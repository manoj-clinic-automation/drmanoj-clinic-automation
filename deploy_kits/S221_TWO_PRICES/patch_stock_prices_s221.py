#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_stock_prices_s221.py -- S221: THE TWO PRICES, HONESTLY LABELLED, AND THE DRIFT LOG.

WHY THIS EXISTS: I MISLABELLED A MONEY COLUMN.

`S221_STOCK_FINDING`, installed this morning, shows a column headed "at MRP".
It is NOT MRP. `stock_rate.rate_p` is built by `push_snapshot.py` from the
PURCHASE_ITEMWISE exports and its own docstring says what it is --

    "the last purchase rate in paise so a shortage can be priced"

-- so the figure on the live document is the owner's COST. I read where the
number sat instead of what produced it (the F-135 / F-284 family), and told the
owner the opposite: that cost was not computable and MRP was. Both wrong, and
the wrong way round. No count exists yet, so nothing has printed; this corrects
it before the first one.

AND MRP TURNS OUT TO BE REAL. Found by reading raw rows after a first
derivation produced one item priced from Rs 2 to Rs 61 a unit:

    2026-08-31  0:15 units  amount 61.60
    2026-08-18  0:1  unit   amount 61.60      <- the same figure, any quantity

`sale_line_item.amount_p` is NOT an amount. It is the printed RATE of a full
strip, repeated on every line. `returns_desk._per_unit_p()` already says so --
"a strip-form line's printed rate is the strip's" -- and divides by the pack.
The live module knew before I did.

    MRP per unit = the strip rate / the pack size

Measured over 147 items that have both: MRP/cost p10 1.25, median 1.40, p75
1.62, and only 2 below cost. A coherent pharmacy margin. The broken derivation
had put 34 of 147 below cost, which is how it announced itself.

WHAT CHANGES ON THE DOCUMENT
  * the existing figure is relabelled **at cost (last purchase rate)** and says
    where it came from
  * a real **at MRP** column arrives, from the item's own strip rate
  * a RECOVERY defaults to the MRP value (the owner's D-a, now executable),
    falling back to cost only when the item has never sold -- and saying which
  * a coverage line: how many lines could be priced at all, and by which route

THE DRIFT LOG, and why it is now urgent (the owner's "yes to both")
`push_expected.py` (what SHOULD be on the shelf, computed) and
`push_snapshot.py` (what Marg says) POST TO THE SAME ENDPOINT, and
`stock_snapshot` is keyed (as_on, item) with last-write-wins. Two different
numbers for the same shelf, and if both carry the same as_on **the second
silently overwrites the first** -- after which `reconcile()` closes differences
against whichever landed last. It has never bitten because the computed push
has never run. It goes live the first morning both run.

`stock_feed` is append-only: every pushed figure, with its source and the time
it arrived, is kept. Nothing can overwrite anything. That makes the owner's
month-or-two cross-check possible at all, and separates a BUG (an item out by
the same amount every run) from an EVENT (right for three weeks, then out).

Target: /root/finance/stock_app.py (pin ed2f76ef... == S213 base + this morning's
S221_STOCK_FINDING patcher, reproduced offline and md5-proven before building)
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_stock_prices_s221.py
Offline:         SA_PATH=./stock_app.py python3 -B patch_stock_prices_s221.py
"""

import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('SA_PATH', '/root/finance/stock_app.py')
MARK = "S221 TWO PRICES"


# --------------------------------------------------------------- anchor A
A_OLD = '''RECOVERY_BASIS = "MRP"          # the owner's ruling D-a, printed on the document
'''

A_NEW = '''RECOVERY_BASIS = "MRP"          # the owner's ruling D-a, printed on the document

# ---- S221 TWO PRICES --------------------------------------------------------
PAGE_DRIFT = os.path.join(HERE, "stock_drift.html")

import re as _re221          # noqa: E402  -- this module does not import re itself

_PACK_RE = _re221.compile(r"(\\d+)\\s*\\*\\s*(\\d+)")


def _pack_units(pack):
    """'1*10' -> 10 units in a strip; None when it cannot be read. Same rule as
    returns_desk._pack_n, which is the live-proven one."""
    m = _PACK_RE.search(str(pack or ""))
    if m:
        n = int(m.group(2))
        return n if 0 < n <= 1000 else None
    return None


def _mrp_p(con, item):
    """MRP for ONE unit, from the item's own sale lines.

    sale_line_item.amount_p is NOT an amount -- it is the printed rate of a
    full strip, repeated on every line whatever the quantity was. Divide by the
    pack and you have the unit price the shop actually charges. This is exactly
    what returns_desk._per_unit_p() already does; the rule is not new here.

    The MEDIAN across the item's lines, because a rate can change with a batch
    and one revision should not become the price. None when the item has never
    sold -- and none is returned honestly rather than falling back to cost,
    because a cost wearing an MRP label is the fault this whole kit corrects.
    """
    try:
        rows = con.execute(
            "SELECT amount_p, pack FROM sale_line_item WHERE item_key=? "
            "AND is_return=0 AND amount_p>0 ORDER BY business_date DESC LIMIT 200",
            (item,)).fetchall()
    except Exception:
        return None
    vals = []
    for r in rows:
        amt = r[0] if not hasattr(r, "keys") else r["amount_p"]
        pk = r[1] if not hasattr(r, "keys") else r["pack"]
        n = _pack_units(pk)
        if amt and n:
            vals.append(amt / float(n))
        elif amt and pk in (None, ""):
            vals.append(float(amt))
    if not vals:
        return None
    vals.sort()
    mid = len(vals) // 2
    med = vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2.0
    return int(round(med))


def _mrp_value_p(con, item, diff):
    rp = _mrp_p(con, item)
    return None if rp is None else int(round(rp * diff))


FEED_SCHEMA = """
CREATE TABLE IF NOT EXISTS stock_feed (
  id INTEGER PRIMARY KEY,
  as_on TEXT NOT NULL,
  source TEXT NOT NULL,
  item TEXT NOT NULL,
  qty INTEGER NOT NULL,
  received_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_feed_item ON stock_feed(item, as_on);
CREATE INDEX IF NOT EXISTS idx_feed_ason ON stock_feed(as_on);
"""


def _feed_ensure(con):
    con.executescript(FEED_SCHEMA)


def _feed_kind(source):
    """Which of the two feeds this is. Anything else is kept and labelled, not
    guessed at -- an unrecognised sender must not silently become one of them."""
    s = (source or "").lower()
    if s.startswith("push_expected"):
        return "expected"
    if s.startswith("push_snapshot"):
        return "marg"
    return "other"
# ---- end S221 TWO PRICES helpers --------------------------------------------
'''


# --------------------------------------------------------------- anchor B
# every pushed figure is kept, append-only.

B_OLD = '''    con.commit()
    # S221 D-b -- "recalculate at export". Items with no rate should be rare;
'''

B_NEW = '''    # S221 TWO PRICES -- keep EVERY pushed figure, append-only, with its source.
    # stock_snapshot is keyed (as_on,item) and last-write-wins, so Marg's export
    # and the computed expected figure overwrite each other whenever they share
    # an as_on. This log is what makes them comparable instead of destructive.
    _feed_ensure(con)
    _now = now_iso()
    for it in items:
        _n = (it.get("item") or "").strip()
        if _n:
            con.execute("INSERT INTO stock_feed (as_on, source, item, qty, received_at)"
                        " VALUES (?,?,?,?,?)",
                        (as_on, b.get("source") or "", _n, int(it.get("qty") or 0), _now))
    con.commit()
    # S221 D-b -- "recalculate at export". Items with no rate should be rare;
'''


# --------------------------------------------------------------- anchor C
# the document: two prices, and what could not be priced at all.

C_OLD = '''        line = dict(id=r[0], item=r[1], marg_qty=r[2], counted_qty=r[3], diff=r[4],
                    pack_size=r[5], value_p=r[6], cause=r[7],
                    cause_label=CAUSE_LABEL.get(r[7], r[7]), cause_note=r[8],
                    status=r[9], counted_by=r[10], answer=a, decision=d,
                    cost_p=None,                 # M3 backfills this; never invented
                    line_state=("closed" if d else "open"))
'''

C_NEW = '''        # S221 TWO PRICES. value_p has always been the LAST PURCHASE RATE times
        # the difference -- the owner's cost -- and until this kit the document
        # called it MRP. It is now named for what it is, and a real MRP figure
        # sits beside it, from the item's own strip rate.
        _mrp = _mrp_value_p(con, r[1], r[4])
        line = dict(id=r[0], item=r[1], marg_qty=r[2], counted_qty=r[3], diff=r[4],
                    pack_size=r[5], value_p=r[6], cause=r[7],
                    cause_label=CAUSE_LABEL.get(r[7], r[7]), cause_note=r[8],
                    status=r[9], counted_by=r[10], answer=a, decision=d,
                    cost_p=r[6],                 # the purchase-rate value
                    mrp_p=_mrp,                  # the selling-rate value
                    priced_by=("both" if (r[6] is not None and _mrp is not None)
                               else "cost only" if r[6] is not None
                               else "mrp only" if _mrp is not None else "neither"),
                    line_state=("closed" if d else "open"))
'''


# --------------------------------------------------------------- anchor D
# a recovery is valued at MRP (D-a), and says so when it cannot be.

D_OLD = '''        if val is None and b.get("recover_p") in (None, ""):
            return jsonify(ok=False, error="no_value",
                           message="This line has no rate yet, so there is no amount "
                                   "to recover. Set a rate first, or type the amount."), 400
        rec_p = int(b["recover_p"]) if b.get("recover_p") not in (None, "") \\
            else (-int(val) if val < 0 else 0)
'''

D_NEW = '''        # D-a: A RECOVERY IS VALUED AT MRP. Cost is the fallback ONLY when the
        # item has never sold, and the answer says which was used so the figure
        # on a person's name is never a mystery.
        _item = con.execute("SELECT item, diff FROM stock_diff WHERE id=?",
                            (did,)).fetchone()
        _mrpv = _mrp_value_p(con, _item[0], _item[1]) if _item else None
        _basis = "MRP"
        if _mrpv is None:
            _mrpv, _basis = val, ("cost (this item has never sold)"
                                  if val is not None else None)
        if _mrpv is None and b.get("recover_p") in (None, ""):
            return jsonify(ok=False, error="no_value",
                           message="This line has neither a selling price nor a purchase "
                                   "rate, so there is no amount to recover. Set a rate "
                                   "first, or type the amount."), 400
        if b.get("recover_p") not in (None, ""):
            rec_p, _basis = int(b["recover_p"]), "typed in by hand"
        else:
            rec_p = (-int(_mrpv) if _mrpv < 0 else 0)
'''


# --------------------------------------------------------------- anchor E
D2_OLD = '''    con.commit()
    return jsonify(ok=True, decision=d, label=DECISION_LABEL[d],
                   recover_p=rec_p, recovery_state=state)
'''

D2_NEW = '''    con.commit()
    return jsonify(ok=True, decision=d, label=DECISION_LABEL[d],
                   recover_p=rec_p, recovery_state=state,
                   basis=(_basis if d == "RECOVER" else None))
'''


# --------------------------------------------------------------- anchor F
# the coverage line, and the drift surface.

F_OLD = '''@bp.route("/api/losses")
'''

F_NEW = '''@bp.route("/page/drift")
def page_drift():
    """Expected vs Marg, run after run. The evidence the spot-count bridge will
    need before it can be armed (the owner, 03-Sep)."""
    u, err = _require("checker", "maker")
    if err:
        return err
    try:
        with io.open(PAGE_DRIFT, "r", encoding="utf-8") as fh:
            t = fh.read()
    except OSError:
        return jsonify(ok=False, error="template_missing",
                       message="stock_drift.html is not beside stock_app.py"), 503
    return t, 200, {"Content-Type": "text/html; charset=utf-8",
                    "Cache-Control": "no-store"}


@bp.route("/api/drift")
def api_drift():
    """For each item and each as-on date that has BOTH feeds: what we computed,
    what Marg says, and the gap.

    A BUG is an item out by the same amount on every run. An EVENT is an item
    that agreed for weeks and then did not. Nothing here decides which; it
    keeps the series so a person can see the difference at a glance -- which a
    printed comparison, thrown away each morning, never could.
    """
    u, err = _require("checker", "maker")
    if err:
        return err
    con = _db()
    _feed_ensure(con)
    rows = con.execute(
        "SELECT as_on, source, item, qty, MAX(received_at) at FROM stock_feed "
        "GROUP BY as_on, source, item ORDER BY as_on").fetchall()
    byday = {}
    for r in rows:
        k = (r[0], r[2])
        byday.setdefault(k, {})[_feed_kind(r[1])] = r[3]
    per = {}
    for (as_on, item), v in byday.items():
        if "expected" not in v or "marg" not in v:
            continue
        d = int(v["expected"]) - int(v["marg"])
        e = per.setdefault(item, dict(item=item, runs=0, deltas=[], days=[]))
        e["runs"] += 1
        e["deltas"].append(d)
        e["days"].append(as_on)
    out = []
    for item, e in per.items():
        ds = e["deltas"]
        nz = [x for x in ds if x != 0]
        same = len(set(nz)) == 1 and len(nz) == len(ds) and len(ds) > 1
        out.append(dict(item=item, runs=e["runs"], last=ds[-1],
                        agreed=len(ds) - len(nz), disagreed=len(nz),
                        verdict=("agrees every run" if not nz else
                                 "SAME gap every run -- look at the arithmetic"
                                 if same else "gap on some runs -- look at the shelf"),
                        cost_p=_rate_p(con, item), mrp_p=_mrp_p(con, item),
                        days=e["days"][-8:], deltas=ds[-8:]))
    out.sort(key=lambda x: (-x["disagreed"], -abs(x["last"] or 0)))
    feeds = [dict(as_on=r[0], source=r[1], items=r[2], first=r[3], last=r[4])
             for r in con.execute(
                 "SELECT as_on, source, COUNT(*), MIN(received_at), MAX(received_at) "
                 "FROM stock_feed GROUP BY as_on, source ORDER BY as_on DESC, source"
                 " LIMIT 40")]
    return jsonify(ok=True, items=out, feeds=feeds,
                   comparable=len(out),
                   note=("A day is comparable only when BOTH feeds arrived for it. "
                         "push_expected.py has to be running for this page to fill."))


@bp.route("/api/losses")
'''


# --------------------------------------------------------------- anchor G
# coverage on the finding itself.

G_OLD = '''    live = _f_seal_md5(con, cid)
'''

G_NEW = '''    # S221 TWO PRICES -- how many lines could be priced at all, and by which
    # route. A total is only honest beside the count of what it could not reach.
    t["priced_both"] = sum(1 for l in valued if l["priced_by"] == "both")
    t["priced_cost_only"] = sum(1 for l in valued if l["priced_by"] == "cost only")
    t["priced_mrp_only"] = sum(1 for l in valued if l["priced_by"] == "mrp only")
    t["priced_none"] = len(unvalued)
    t["mrp_short_p"] = sum(-int(l["mrp_p"]) for l in valued
                           if l["mrp_p"] is not None and l["mrp_p"] < 0)
    live = _f_seal_md5(con, cid)
'''


PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW), ("C", C_OLD, C_NEW),
         ("D", D_OLD, D_NEW), ("E", D2_OLD, D2_NEW), ("F", F_OLD, F_NEW),
         ("G", G_OLD, G_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S221_prices_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: the result does not compile (%s). "
                         "RESTORED from %s -- the live file is unchanged." % (ex, bak))
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("next     copy stock_finding.html and stock_drift.html, then the walk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
