#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_stock_finding_s221.py -- S221: THE STOCK DIFFERENCE BECOMES AN AUDIT FINDING.

THE OWNER, 03-Sep-2026:

    "stock diff is a audit finding, its reporting shd be in proper way to me --
     date time, stck checkers involved, results, loss at mrp (loss at purchse to
     me), write off column where I decide these, and the total write offs list
     value, and the list which goes in for recovery from darpan. A hard copy of
     the stock diff is generated and printed, shared with darpan and amir, open
     the same in their mobiles or pc, and work in it."

    ... and on recovery: "its more than that - a blind sight is worse, when the
    system is in place its main purpose is DETERRENCE."

That last sentence is the design. **NOTHING IS EVER DEDUCTED BY THIS CODE.** A
recovery is LOGGED against a named person and shown to him; no staff ledger is
touched, here or anywhere downstream of here. The deterrent is that the shelf is
countable and the count is attributable -- not that money is taken.

THE PRINCIPLE: A FINDING IS FROZEN; EVERYTHING AFTER IT IS A LAYER.
At submit the count is SEALED -- a finding number, the time, the Marg snapshot
it was counted against, both counters' names, and an md5 over the difference
rows themselves. Nothing afterwards edits a quantity or a value, and
/api/finding/<id> recomputes that md5 on every read and says so if it differs.
A recount is a NEW finding; the old one stays saying what it said.

Three layers sit on top, none of which rewrite the finding:
  * the STAFF ANSWER  -- one plain reason per line from Darpan or Amir
  * the OWNER DECISION -- WRITE_OFF | RECOVER | EXPLAINED, append-only, latest wins
  * the VOUCHER RECORD -- the Marg stock-adjustment voucher, by number and date
                          (S207 R6: a write-off is not finished until Marg agrees)

THE OWNER'S RULINGS, EXECUTED HERE:
  D-a  recovery is valued AT MRP, and the document says so in words.
  D-b  an item with no rate is NEVER folded into a total. It is listed in its
       own block, and a rate can be typed in (POST /api/rate) or arrive with the
       next export -- either way every open unvalued difference is re-valued.
  D-c  LOG ONLY. There is no ledger call in this file and there must never be.
  D-d  a decision CLOSES the line; a RECOVER keeps its own amount OPEN until it
       is settled, which is a separate, deliberate act.
  cost the column exists, empty, and is backfilled when the M3 purchase tables
       land. Nothing here invents a cost figure.

Target: /root/finance/stock_app.py (live pin 83b0a1b0... == the repo copy, verified)
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_stock_finding_s221.py
Offline:         SA_PATH=./stock_app.py python3 -B patch_stock_finding_s221.py
"""

import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('SA_PATH', '/root/finance/stock_app.py')
MARK = "S221 FINDING"


# --------------------------------------------------------------- anchor A
# constants, the page path, the lazy schema and every helper.

A_OLD = '''    "THEFT":       "taken",
}
'''

A_NEW = '''    "THEFT":       "taken",
}

# ---- S221 FINDING: the difference as an audit document ----------------------
PAGE_FINDING = os.path.join(HERE, "stock_finding.html")

# What the owner may rule on a line. WRITE_OFF and RECOVER are both his loss;
# they differ only in whether he intends to put it to a person. EXPLAINED is
# the honest third answer -- a counting error or a late arrival is not a loss,
# and forcing it into one of the other two would make the totals lie.
DECISIONS = ("WRITE_OFF", "RECOVER", "EXPLAINED")
DECISION_LABEL = {
    "WRITE_OFF": "written off",
    "RECOVER":   "marked for recovery",
    "EXPLAINED": "explained -- no loss",
}
# The staff's own words, in their own language. "pata nahin" is a real answer
# and is offered deliberately: a forced reason is a false reason.
STAFF_REASONS = {
    "count_error": "\\u0917\\u093f\\u0928\\u0924\\u0940 \\u092e\\u0947\\u0902 \\u0917\\u0932\\u0924\\u0940",
    "not_billed":  "\\u092c\\u093f\\u0932 \\u0928\\u0939\\u0940\\u0902 \\u092c\\u0928\\u093e",
    "breakage":    "\\u091f\\u0942\\u091f / \\u0916\\u0930\\u093e\\u092c",
    "expiry":      "\\u090f\\u0915\\u094d\\u0938\\u092a\\u093e\\u092f\\u0930\\u0940 \\u092e\\u0947\\u0902 \\u0917\\u092f\\u093e",
    "sample":      "\\u0938\\u0948\\u0902\\u092a\\u0932 / \\u0921\\u0949\\u0915\\u094d\\u091f\\u0930 \\u0915\\u094b \\u0926\\u093f\\u092f\\u093e",
    "return":      "\\u0935\\u093e\\u092a\\u0938\\u0940 \\u0915\\u093e \\u092e\\u093e\\u0932",
    "dont_know":   "\\u092a\\u0924\\u093e \\u0928\\u0939\\u0940\\u0902",
}
RECOVERY_BASIS = "MRP"          # the owner's ruling D-a, printed on the document

FINDING_SCHEMA = """
CREATE TABLE IF NOT EXISTS stock_finding (
  count_id   INTEGER PRIMARY KEY REFERENCES stock_count(id),
  finding_no TEXT NOT NULL UNIQUE,
  sealed_at  TEXT NOT NULL,
  seal_md5   TEXT NOT NULL,
  basis      TEXT NOT NULL DEFAULT 'MRP',
  lines_n    INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS stock_diff_answer (
  id INTEGER PRIMARY KEY, diff_id INTEGER NOT NULL REFERENCES stock_diff(id),
  reason TEXT NOT NULL, note TEXT,
  answered_by TEXT NOT NULL, answered_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stock_diff_decision (
  id INTEGER PRIMARY KEY, diff_id INTEGER NOT NULL REFERENCES stock_diff(id),
  decision TEXT NOT NULL, recover_from TEXT, recover_p INTEGER,
  recovery_state TEXT NOT NULL DEFAULT 'none', note TEXT,
  decided_by TEXT NOT NULL, decided_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stock_voucher (
  id INTEGER PRIMARY KEY, count_id INTEGER NOT NULL REFERENCES stock_count(id),
  voucher_no TEXT NOT NULL, voucher_date TEXT NOT NULL, note TEXT,
  scan_ref TEXT, recorded_by TEXT NOT NULL, recorded_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sda_diff ON stock_diff_answer(diff_id);
CREATE INDEX IF NOT EXISTS idx_sdd_diff ON stock_diff_decision(diff_id);
"""


def _f_ensure(con):
    con.executescript(FINDING_SCHEMA)


def _f_seal_md5(con, cid):
    """The finding's own fingerprint, over THE QUANTITIES ONLY.

    Deliberately NOT over value_p, and the walk is what settled it. A rate that
    arrives late legitimately fills in a blank value (the owner's D-b), and a
    seal that covered the value would then shout "these rows have changed" at
    every finding that ever waited for a rate -- a warning that fires on
    correct behaviour is a warning nobody reads.

    So the seal covers what a person could be judged by and what must never
    move: the item, what Marg expected, what was actually counted, and the
    difference. A price is an attribute that may be corrected; a count is not.
    """
    import hashlib                                            # noqa: PLC0415
    h = hashlib.md5()
    for r in con.execute(
            "SELECT item, marg_qty, counted_qty, diff "
            "FROM stock_diff WHERE count_id=? ORDER BY item", (cid,)):
        h.update(("%s|%s|%s|%s;" % (r[0], r[1], r[2], r[3])).encode("utf-8"))
    return h.hexdigest()


def _f_seal(con, cid, as_on):
    """Seal a submitted count. Idempotent: a second call never re-seals."""
    _f_ensure(con)
    if con.execute("SELECT 1 FROM stock_finding WHERE count_id=?", (cid,)).fetchone():
        return None
    n = con.execute("SELECT COUNT(*) FROM stock_diff WHERE count_id=?", (cid,)).fetchone()[0]
    no = "SF-%s-%03d" % ((as_on or "")[-4:] or "0000", cid)
    con.execute(
        "INSERT INTO stock_finding (count_id, finding_no, sealed_at, seal_md5, basis, lines_n)"
        " VALUES (?,?,?,?,?,?)",
        (cid, no, now_iso(), _f_seal_md5(con, cid), RECOVERY_BASIS, n))
    return no


def _f_latest(con, table, diff_ids, cols):
    """The newest row per diff_id. Both layers are append-only -- a change of
    mind is a new row, never an overwrite -- so 'latest' is what is shown and
    the earlier ones stay on the record."""
    out = {}
    if not diff_ids:
        return out
    q = ("SELECT %s FROM %s WHERE diff_id IN (%s) ORDER BY id"
         % (", ".join(("diff_id",) + cols), table, ",".join("?" * len(diff_ids))))
    for r in con.execute(q, tuple(diff_ids)):
        out[r[0]] = dict(zip(cols, tuple(r)[1:]))
    return out


def _f_revalue(con):
    """Give a rupee value to every OPEN difference that had none, now that a
    rate exists. Nothing already valued is touched, so a sealed number never
    moves; only a blank becomes a figure. Returns how many filled in."""
    n = 0
    for r in con.execute("SELECT id, item, diff FROM stock_diff "
                         "WHERE value_p IS NULL AND status='open'").fetchall():
        v = _value_p(con, r[1] if not hasattr(r, "keys") else r["item"],
                     r[2] if not hasattr(r, "keys") else r["diff"])
        if v is not None:
            con.execute("UPDATE stock_diff SET value_p=? WHERE id=?",
                        (v, r[0] if not hasattr(r, "keys") else r["id"]))
            n += 1
    return n
# ---- end S221 FINDING helpers ------------------------------------------------
'''


# --------------------------------------------------------------- anchor B
# seal the finding the moment the count is submitted.

B_OLD = '''    con.commit()
    return jsonify(ok=True, count_id=cid, items=len(items), differences=raised,
'''

B_NEW = '''    # S221 FINDING -- seal it here, in the same transaction that raised the
    # differences. A finding that is sealed later is a finding that could have
    # been edited in between.
    finding_no = _f_seal(con, cid, b["marg_as_on"].strip())
    con.commit()
    return jsonify(ok=True, count_id=cid, items=len(items), differences=raised,
                   finding_no=finding_no,
'''


# --------------------------------------------------------------- anchor C
# re-value on every export: the owner's D-b.

C_OLD = '''    con.commit()
    closed = reconcile(con, as_on)
    return jsonify(ok=True, as_on=as_on, items=n, reconciled=closed)
'''

C_NEW = '''    con.commit()
    # S221 D-b -- "recalculate at export". Items with no rate should be rare;
    # when a rate finally arrives, every open difference that had no value
    # gets one. A value already recorded is never moved by this.
    _f_ensure(con)
    revalued = _f_revalue(con)
    con.commit()
    closed = reconcile(con, as_on)
    return jsonify(ok=True, as_on=as_on, items=n, reconciled=closed,
                   revalued=revalued)
'''


# --------------------------------------------------------------- anchor D
# the document, the two layers, the rate, the voucher, the page.

D_OLD = '''@bp.route("/api/losses")
'''

D_NEW = '''# ---- S221 FINDING: the document and its layers -------------------------------

@bp.route("/page/finding")
def page_finding():
    """The audit document. One page, three readers: the owner adjudicates, the
    staff answer, and the print button makes the hard copy. Which of those a
    viewer gets is decided by the server on /api/finding, never by the page."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    try:
        with io.open(PAGE_FINDING, "r", encoding="utf-8") as fh:
            t = fh.read()
    except OSError:
        return jsonify(ok=False, error="template_missing",
                       message="stock_finding.html is not beside stock_app.py"), 503
    return t, 200, {"Content-Type": "text/html; charset=utf-8",
                    "Cache-Control": "no-store"}


@bp.route("/api/findings")
def api_findings():
    """Every sealed finding, newest first -- the way in to the document."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _f_ensure(con)
    out = []
    for r in con.execute(
            "SELECT f.count_id, f.finding_no, f.sealed_at, f.lines_n, "
            " c.marg_as_on, c.submitted_by, c.items_counted "
            "FROM stock_finding f JOIN stock_count c ON c.id=f.count_id "
            "ORDER BY f.count_id DESC LIMIT 50"):
        out.append(dict(count_id=r[0], finding_no=r[1], sealed_at=r[2],
                        lines=r[3], marg_as_on=r[4], submitted_by=r[5],
                        items_counted=r[6]))
    return jsonify(ok=True, findings=out)


@bp.route("/api/finding/<int:cid>")
def api_finding(cid):
    """THE DOCUMENT, composed here and nowhere else (D349). The owner's screen,
    the staff's phone and the printed sheet all render this one payload, so no
    number can differ between them."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _f_ensure(con)
    f = con.execute("SELECT finding_no, sealed_at, seal_md5, basis, lines_n "
                    "FROM stock_finding WHERE count_id=?", (cid,)).fetchone()
    if not f:
        return jsonify(ok=False, error="not_found",
                       message="No sealed finding for count %d." % cid), 404
    c = con.execute("SELECT marg_as_on, bill_no, bill_date, started_at, submitted_at,"
                    " submitted_by, items_total, items_counted FROM stock_count "
                    "WHERE id=?", (cid,)).fetchone()
    who_c, who_e = [], []
    for r in con.execute("SELECT DISTINCT counted_by, entered_by FROM stock_count_item "
                         "WHERE count_id=?", (cid,)):
        if r[0] and r[0] not in who_c:
            who_c.append(r[0])
        if r[1] and r[1] not in who_e:
            who_e.append(r[1])

    rows = con.execute(
        "SELECT id, item, marg_qty, counted_qty, diff, pack_size, value_p, cause, "
        " cause_note, status, counted_by FROM stock_diff WHERE count_id=? "
        "ORDER BY (value_p IS NULL), ABS(COALESCE(value_p,0)) DESC, item", (cid,)).fetchall()
    ids = [r[0] for r in rows]
    ans = _f_latest(con, "stock_diff_answer", ids,
                    ("reason", "note", "answered_by", "answered_at"))
    dec = _f_latest(con, "stock_diff_decision", ids,
                    ("decision", "recover_from", "recover_p", "recovery_state",
                     "note", "decided_by", "decided_at"))

    valued, unvalued = [], []
    t = dict(written_off_p=0, to_recover_p=0, explained_p=0, undecided_p=0,
             short_p=0, over_p=0, undecided_lines=0, recover_lines=0,
             writeoff_lines=0, explained_lines=0, settled_p=0)
    for r in rows:
        d = dec.get(r[0])
        a = ans.get(r[0])
        if a:
            a = dict(a, label=STAFF_REASONS.get(a["reason"], a["reason"]))
        line = dict(id=r[0], item=r[1], marg_qty=r[2], counted_qty=r[3], diff=r[4],
                    pack_size=r[5], value_p=r[6], cause=r[7],
                    cause_label=CAUSE_LABEL.get(r[7], r[7]), cause_note=r[8],
                    status=r[9], counted_by=r[10], answer=a, decision=d,
                    cost_p=None,                 # M3 backfills this; never invented
                    line_state=("closed" if d else "open"))
        if r[6] is None:
            unvalued.append(line)
            if not d:
                t["undecided_lines"] += 1
            continue
        valued.append(line)
        v = int(r[6])
        if v < 0:
            t["short_p"] += -v
        else:
            t["over_p"] += v
        loss = -v if v < 0 else 0
        if not d:
            t["undecided_p"] += loss
            t["undecided_lines"] += 1
        elif d["decision"] == "WRITE_OFF":
            t["written_off_p"] += loss
            t["writeoff_lines"] += 1
        elif d["decision"] == "RECOVER":
            amt = int(d["recover_p"] or loss)
            if (d["recovery_state"] or "open") == "settled":
                t["settled_p"] += amt
            else:
                t["to_recover_p"] += amt
            t["recover_lines"] += 1
        elif d["decision"] == "EXPLAINED":
            t["explained_p"] += loss
            t["explained_lines"] += 1

    recovery = [dict(item=l["item"], person=(l["decision"] or {}).get("recover_from"),
                     amount_p=int((l["decision"] or {}).get("recover_p") or
                                  (-l["value_p"] if l["value_p"] and l["value_p"] < 0 else 0)),
                     state=(l["decision"] or {}).get("recovery_state") or "open")
                for l in valued
                if l["decision"] and l["decision"]["decision"] == "RECOVER"]
    writeoffs = [dict(item=l["item"], value_p=l["value_p"]) for l in valued
                 if l["decision"] and l["decision"]["decision"] == "WRITE_OFF"]

    vouchers = [dict(voucher_no=r[0], voucher_date=r[1], note=r[2], scan_ref=r[3],
                     recorded_by=r[4], recorded_at=r[5])
                for r in con.execute(
                    "SELECT voucher_no, voucher_date, note, scan_ref, recorded_by,"
                    " recorded_at FROM stock_voucher WHERE count_id=? ORDER BY id", (cid,))]

    live = _f_seal_md5(con, cid)
    return jsonify(
        ok=True,
        you=dict(user=(u or {}).get("user") or "", may_decide=_may_decide(u)),
        finding=dict(no=f[0], count_id=cid, sealed_at=f[1], seal=f[2],
                     seal_ok=(live == f[2]), seal_now=live, basis=f[3],
                     lines_sealed=f[4], marg_as_on=c[0], bill_no=c[1],
                     bill_date=c[2], started_at=c[3], submitted_at=c[4],
                     submitted_by=c[5], items_total=c[6], items_counted=c[7],
                     counted_by=who_c, entered_by=who_e),
        lines=valued, unvalued=unvalued, totals=t,
        recovery=recovery, writeoffs=writeoffs, vouchers=vouchers,
        reasons=STAFF_REASONS, decisions=list(DECISIONS),
        decision_labels=DECISION_LABEL)


def _may_decide(u):
    """Only the checker rules on a line. The server decides this, not the page."""
    return (u or {}).get("role") in ("checker",) or bool((u or {}).get("is_checker"))


@bp.route("/api/diff/<int:did>/answer", methods=["POST"])
def api_diff_answer(did):
    """The staff layer. Evidence, never state: it cannot change a quantity, a
    value, a cause or a decision, and the row it writes is append-only."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    reason = (b.get("reason") or "").strip()
    if reason not in STAFF_REASONS:
        return jsonify(ok=False, error="bad_reason",
                       message="reason must be one of: %s"
                               % ", ".join(sorted(STAFF_REASONS))), 400
    con = _db()
    _f_ensure(con)
    if not con.execute("SELECT 1 FROM stock_diff WHERE id=?", (did,)).fetchone():
        return jsonify(ok=False, error="not_found"), 404
    con.execute("INSERT INTO stock_diff_answer (diff_id, reason, note, answered_by,"
                " answered_at) VALUES (?,?,?,?,?)",
                (did, reason, (b.get("note") or "").strip() or None,
                 (u or {}).get("user") or "", now_iso()))
    con.commit()
    return jsonify(ok=True)


@bp.route("/api/diff/<int:did>/decision", methods=["POST"])
def api_diff_decision(did):
    """The owner's ruling on one line. Append-only; the latest is shown and
    every earlier one stays on the record.

    LOG ONLY (the owner's ruling D-c). A RECOVER writes a name and an amount
    and NOTHING ELSE HAPPENS -- no staff ledger, no advance, no deduction, not
    here and not by anything this calls. Deterrence is the purpose; the money
    is not taken by software.
    """
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    d = (b.get("decision") or "").strip().upper()
    if d not in DECISIONS:
        return jsonify(ok=False, error="bad_decision",
                       message="decision must be one of: %s" % ", ".join(DECISIONS)), 400
    con = _db()
    _f_ensure(con)
    row = con.execute("SELECT value_p FROM stock_diff WHERE id=?", (did,)).fetchone()
    if not row:
        return jsonify(ok=False, error="not_found"), 404
    val = row[0]
    rec_from, rec_p, state = None, None, "none"
    if d == "RECOVER":
        rec_from = (b.get("recover_from") or "").strip()
        if not rec_from:
            return jsonify(ok=False, error="bad_request",
                           message="A recovery has to name a person."), 400
        if val is None and b.get("recover_p") in (None, ""):
            return jsonify(ok=False, error="no_value",
                           message="This line has no rate yet, so there is no amount "
                                   "to recover. Set a rate first, or type the amount."), 400
        rec_p = int(b["recover_p"]) if b.get("recover_p") not in (None, "") \\
            else (-int(val) if val < 0 else 0)
        state = "settled" if b.get("settled") else "open"
    con.execute(
        "INSERT INTO stock_diff_decision (diff_id, decision, recover_from, recover_p,"
        " recovery_state, note, decided_by, decided_at) VALUES (?,?,?,?,?,?,?,?)",
        (did, d, rec_from, rec_p, state, (b.get("note") or "").strip() or None,
         (u or {}).get("user") or "", now_iso()))
    # D-d: the LINE closes on a decision; a recovery AMOUNT stays open on its own.
    con.execute("UPDATE stock_diff SET status='closed', closed_at=? WHERE id=?",
                (now_iso(), did))
    con.commit()
    return jsonify(ok=True, decision=d, label=DECISION_LABEL[d],
                   recover_p=rec_p, recovery_state=state)


@bp.route("/api/rate", methods=["POST"])
def api_rate():
    """Type in a rate for an item Marg's export did not carry (D-b), then
    re-value every open difference that was waiting on one."""
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    item = (b.get("item") or "").strip()
    try:
        rate_p = int(round(float(b.get("rate_p"))))
    except (TypeError, ValueError):
        rate_p = -1
    if not item or rate_p < 0:
        return jsonify(ok=False, error="bad_request",
                       message="item and a rate in paise are required."), 400
    con = _db()
    ensure_schema(con)
    _f_ensure(con)
    con.execute("INSERT INTO stock_rate (item,rate_p,pack_size,as_of,source) "
                "VALUES (?,?,?,?, 'manual') ON CONFLICT(item) DO UPDATE SET "
                "rate_p=excluded.rate_p, as_of=excluded.as_of, source='manual'",
                (item, rate_p, int(b.get("pack_size") or 1), now_iso()[:10]))
    n = _f_revalue(con)
    con.commit()
    return jsonify(ok=True, item=item, rate_p=rate_p, revalued=n)


@bp.route("/api/voucher", methods=["POST"])
def api_voucher():
    """Record the Marg stock-adjustment voucher for this finding, by number and
    date (S207 R6: a write-off is not finished until Marg agrees). `scan_ref`
    holds wherever the scanned copy was kept -- the scan itself is preserved
    outside this table until Marg's own vouchers can be exported."""
    u, err = _require("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    cid = b.get("count_id")
    no = (b.get("voucher_no") or "").strip()
    date = (b.get("voucher_date") or "").strip()
    if not (cid and no and date):
        return jsonify(ok=False, error="bad_request",
                       message="count_id, voucher_no and voucher_date are required."), 400
    con = _db()
    _f_ensure(con)
    con.execute("INSERT INTO stock_voucher (count_id, voucher_no, voucher_date, note,"
                " scan_ref, recorded_by, recorded_at) VALUES (?,?,?,?,?,?,?)",
                (int(cid), no, date, (b.get("note") or "").strip() or None,
                 (b.get("scan_ref") or "").strip() or None,
                 (u or {}).get("user") or "", now_iso()))
    con.commit()
    return jsonify(ok=True)
# ---- end S221 FINDING --------------------------------------------------------


@bp.route("/api/losses")
'''


PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW), ("C", C_OLD, C_NEW),
         ("D", D_OLD, D_NEW)]


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
    bak = TARGET + ".bak_S221_finding_" + stamp
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
    if "ledger" in out.lower().split("S221 FINDING")[-1][:20000]:
        pass          # (a reminder, not a gate: no ledger call belongs in this file)
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("next     copy stock_finding.html beside it, then the walk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
