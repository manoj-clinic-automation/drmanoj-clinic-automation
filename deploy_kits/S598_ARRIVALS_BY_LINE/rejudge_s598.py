#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rejudge_s598.py -- kit S598_ARRIVALS_BY_LINE, the ONE data step (the brief's section 3.5): the order lines S593's detect_supplies marked on
19-Oct-2026 (detected_at >= 2026-10-19T08:03:00) are re-judged under the NEW rule (stock_figure.carried on bill LINES) and the rows the rule
disagrees with are cleared -- the system's own write undone, never a person's entry (charter 5).

    python3 -B rejudge_s598.py --fin <finance folder whose stock_figure is the NEW one> --db <finance.db or a COPY> --json <save the rows here>
                               [--since 2026-10-19T08:03:00] [--dry]

For every such row: printed first; saved WHOLE to --json before any write; then line = dict(line_id, item, vendor, order_at,
billed_bill_no=None), a fresh Ctx, hit = carried(). AGREE (R1-C5) = hit is a (c)/(d) hit AND _bill(hit.bill) == _bill(row.billed_bill_no) AND
int(round(hit.qty + hit.free)) == int(row.billed_qty) -> untouched. DISAGREE -> billed_qty, billed_bill_no, billed_date, detected_at set NULL
and, ONLY IF arrived_by = 'marg' (the system's write) and purchase_audit holds S593's line_detected row for this id (19-Oct), supplied,
arrived_by, arrived_at set NULL and short 0 (the column is NOT NULL; 0 is what an open line holds) too; audit line_rejudged_s598 with before / after. A line that now matches a DIFFERENT bill line is not
re-marked here (printed: the next detect_supplies tick does that under the one rule). _close_complete_orders is not called;
purchase_order.status of orders 1, 10, 13, 20 is asserted equal before and after. Idempotent: a second run finds no row (detected_at NULL)
or agrees. Prints 'REJUDGE OK S598 ...' with the ids cleared; exit 1 on any fault (nothing committed).
No phone number is printed (a run of ten digits is masked)."""
import argparse
import json
import os
import re
import sqlite3
import sys

SINCE = "2026-10-19T08:03:00"
ORDERS = (1, 10, 13, 20)


def mask(s):
    return re.sub(r"\d{10,}", lambda m: "#" * len(m.group(0)), str(s))


def say(s=""):
    print(mask(s), flush=True)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    ap.add_argument("--fin", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--since", default=SINCE)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    fin = os.path.abspath(a.fin)
    sys.path.insert(0, fin)
    os.chdir(fin)
    os.environ["FINANCE_DB"] = os.path.abspath(a.db)
    import stock_figure as SF                                 # noqa: E402
    import stock_watch as SW                                  # noqa: E402
    import porders as PO                                      # noqa: E402
    for m in (SF, SW, PO):
        assert m.__file__.startswith(fin), m.__file__
    if not hasattr(SF, "_purchase_lines_of"):
        say("REJUDGE RED S598: stock_figure at %s is not the S598 one (no _purchase_lines_of) -- nothing done" % fin)
        return 1
    con = sqlite3.connect(os.path.abspath(a.db), timeout=60)
    con.row_factory = sqlite3.Row
    cols = [r[1] for r in con.execute("PRAGMA table_info(purchase_order_line)")]
    rows = [dict(r) for r in con.execute("SELECT l.*, o.vendor AS _vendor, o.created_at AS _order_at, o.status AS _status FROM purchase_order_line l "
                                         "JOIN purchase_order o ON o.id=l.order_id WHERE l.detected_at >= ? ORDER BY l.id", (a.since,))]
    say("REJUDGE S598: %d row(s) with detected_at >= %s (ids %s) on %s%s" % (len(rows), a.since, ",".join(str(r["id"]) for r in rows), os.path.basename(a.db), " [DRY]" if a.dry else ""))
    for r in rows:
        say("   line %-4s order %-3s %-30s %-24s packs %3s billed %4s by %-14s of %s supplied %-4s short %s arrived_by %-6s detected %s"
            % (r["id"], r["order_id"], r["item"][:30], r["_vendor"][:24], r["packs"], r["billed_qty"], r["billed_bill_no"], r["billed_date"], r["supplied"], r["short"], r["arrived_by"], r["detected_at"]))
    st0 = {o: con.execute("SELECT status FROM purchase_order WHERE id=?", (o,)).fetchone() for o in ORDERS}
    st0 = {o: (v[0] if v else None) for o, v in st0.items()}
    saved = [{c: r[c] for c in cols} for r in rows]
    if not a.dry:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(dict(kit="S598_ARRIVALS_BY_LINE", since=a.since, db=os.path.abspath(a.db), saved_at=PO.now_iso(), columns=cols, rows=saved), fh, indent=1, default=str)
        say("   the %d row(s) saved whole to %s" % (len(saved), a.json))
    sw = SW.Spine()
    if not getattr(sw, "ok", False):
        say("REJUDGE RED S598: the spine could not be read -- nothing done")
        return 1
    cleared, agreed, would = [], [], []
    try:
        for r in rows:
            line = dict(line_id=r["id"], item=r["item"], vendor=r["_vendor"], order_at=r["_order_at"], billed_bill_no=None)
            ctx = SF.Ctx(con, sw)
            hit = SF.carried(con, sw, line, ctx)
            q = int(round(float((hit or {}).get("qty") or 0) + float((hit or {}).get("free") or 0))) if hit else None
            agree = bool(hit) and hit.get("how") in ("c", "d") and SF._bill(hit["bill"]) == SF._bill(r["billed_bill_no"]) and q == int(r["billed_qty"] or -1)
            if hit and hit.get("how") in ("c", "d"):
                htxt = "(%s) bill %s of %s line %s %r qty %s" % (hit["how"], hit["bill"], hit["date"], hit.get("seq"), hit.get("name27"), q)
            elif hit:
                htxt = "(%s) another supplier's bill %s -- never this line" % (hit["how"], hit["bill"])
            else:
                fb = ctx.c.get(("fam_bill", r["id"]))
                htxt = "no matching bill line" + ((" -- the family's bill %s of %s carried %s" % (fb["bill"], fb["date"], ", ".join(fb["sizes"]))) if fb else "")
            say("   line %-4s %-30s %s -> %s" % (r["id"], r["item"][:30], "AGREE   " if agree else "DISAGREE", htxt))
            if agree:
                agreed.append(r["id"])
                continue
            sysw = (r["arrived_by"] == "marg") and bool(con.execute("SELECT 1 FROM purchase_audit WHERE action='line_detected' AND who='marg' AND ref=? AND at>=? AND at<'2026-10-20'",
                                                                        (str(r["id"]), a.since[:10])).fetchone())
            before = {c: r[c] for c in cols}
            after = dict(before, billed_qty=None, billed_bill_no=None, billed_date=None, detected_at=None)
            if sysw:
                after.update(supplied=None, short=0, arrived_by=None, arrived_at=None)   # short is NOT NULL: an open line holds 0
            say("      -> cleared: billed_qty, billed_bill_no, billed_date, detected_at%s" % (", supplied, arrived_by, arrived_at NULL and short 0 (the system's own write, S593's audit row found)" if sysw else " (arrived_by %r is a person's entry: supplied / short / arrived_at kept)" % r["arrived_by"]))
            if hit and hit.get("how") in ("c", "d"):
                would.append((r["id"], hit["bill"], hit["date"], q))
                say("      -> the next detect_supplies tick would mark it: bill %s of %s, %s packs (not done here)" % (hit["bill"], hit["date"], q))
            if not a.dry:
                con.execute("UPDATE purchase_order_line SET billed_qty=NULL, billed_bill_no=NULL, billed_date=NULL, detected_at=NULL WHERE id=?", (r["id"],))
                if sysw:
                    con.execute("UPDATE purchase_order_line SET supplied=NULL, short=0, arrived_by=NULL, arrived_at=NULL WHERE id=?", (r["id"],))
                PO._audit(con, "s598", "line_rejudged_s598", str(r["id"]), dict(item=r["item"], before=before, after=after, system_write=sysw,
                                                                               hit=({k: hit[k] for k in ("how", "bill", "date", "seq", "name27")} if hit else None)))
            cleared.append(r["id"])
    finally:
        try:
            sw.con.close()
        except Exception:                                     # noqa: BLE001
            pass
    st1 = {o: con.execute("SELECT status FROM purchase_order WHERE id=?", (o,)).fetchone() for o in ORDERS}
    st1 = {o: (v[0] if v else None) for o, v in st1.items()}
    if st0 != st1:
        con.rollback()
        say("REJUDGE RED S598: purchase_order.status moved %s -> %s -- rolled back" % (st0, st1))
        return 1
    if a.dry:
        con.rollback()
    else:
        con.commit()
    con.close()
    say("   purchase_order.status of %s: %s (equal before and after)" % (ORDERS, st1))
    say("REJUDGE OK S598: %d row(s) re-judged, %d agree (%s), %d cleared (%s)%s" % (len(rows), len(agreed), ",".join(map(str, agreed)) or "-", len(cleared), ",".join(map(str, cleared)) or "-", " [DRY: nothing written]" if a.dry else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
