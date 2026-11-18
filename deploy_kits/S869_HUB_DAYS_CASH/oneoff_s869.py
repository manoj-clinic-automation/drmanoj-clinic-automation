#!/usr/bin/env python3
"""oneoff_s869.py --db PATH [--apply]  --  kit S869_HUB_DAYS_CASH: the ONE-TIME clean-up of Darpan's drawer (D1005, the owner's
rulings of 18-Nov-2026, S481_HUB_BUILD_SPEC.md).  Without --apply it SAYS what it would do and writes nothing.  Idempotent:
every step reads its own state first and is skipped once done.  Every change is audited (audit_log before/after; darpan_kal_audit).
Runs AFTER day_resync.py has set 9-Oct and 14-Oct to the bank's UPI (it refuses otherwise).  The finance dir is beside this
script's --fin (default /root/finance); the one calculation is read back at the end and the drawer printed.

  A. 9-Oct: the 23,421 handover typed by the owner on 10-Oct was a typo ("make the necessary changes one time") -> 13,258 =
     the day's cash once the bank's UPI 10,163 is taken: darpan_kal_day handed_p / diff_p, cash_movement (the landed row),
     cash_handover_cover, and the 'owed back to Darpan' row that typo opened (status returned -> withdrawn).
  B. 14-Nov: two owner entries -- Rs 1,580 paid into the NK Pathology UPI by a patient (never reached the drawer);
     Rs 4,000 given to Darpan by Dr Bhawna for personal expenses (cash taken out, with Dr Bhawna).
  C. 4-Nov: one owner entry -- Rs 954, a UPI done into another account.
  D. 3-Nov: sale bill A004591 (Rs 1,760) was deleted in Marg ("a backup person was holding the sales counter"); Marg's
     later export (05-Nov 14:42, 13 bills) no longer carries it, the server still did (the ingest only adds).  The bill
     row and its lines go (kept whole in the audit row), its review-queue line is resolved as gone, and the day --
     still unapproved -- follows Marg's 13 bills (day_resync pass 0: cash 6,522 -> 4,762).
  28-Sep (Rs 680, accepted) and 17-Oct (Rs 504, his tap) need no write here: the accepted-short rule reads the decision.
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import sys

KIT = "S869_HUB_DAYS_CASH"
WHO = "manoj (the owner's word of 18-Nov-2026, recorded by %s)" % KIT
UNIT = "medical"


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def rs(p):
    return "{:,}".format(int(round(p / 100.0)))


def audit(con, table, row_id, action, before, after):
    con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                (table, row_id, action, json.dumps(before) if before is not None else None,
                 json.dumps(after) if after is not None else None, WHO, now_iso()))


def kal_audit(con, action, detail):
    con.execute("INSERT INTO darpan_kal_audit (at, who, action, detail) VALUES (?,?,?,?)",
                (now_iso(), "manoj", action, json.dumps(detail)[:600]))


def lines(con, iso):
    r = con.execute("SELECT l.mode, l.amount_p FROM day_line l JOIN day_entry e ON e.id=l.day_entry_id WHERE e.unit=? "
                    "AND e.business_date=? AND l.service='pharmacy_sale'", (UNIT, iso)).fetchall()
    return {m: int(a) for m, a in r}


def step_a(con, apply, say):
    iso, old, new = "2026-10-09", 2342100, 1325800
    ln = lines(con, iso)
    if ln.get("cash") != new or ln.get("upi") != 1016300:
        return "REFUSED: 9-Oct's lines are cash %s / upi %s -- run day_resync.py first (expected 13,258 / 10,163)" % (
            rs(ln.get("cash", 0)), rs(ln.get("upi", 0)))
    row = con.execute("SELECT handed_p, diff_p, expected_p, landed_movement_id, state FROM darpan_kal_day WHERE unit=? AND business_date=?",
                      (UNIT, iso)).fetchone()
    if not row:
        return "REFUSED: no handover row for 9-Oct"
    handed, diff, expected, mid, state = int(row[0]), int(row[1] or 0), int(row[2] or 0), row[3], row[4]
    if handed == new:
        return "A  9-Oct handover already 13,258 -- done"
    if handed != old:
        return "REFUSED: 9-Oct's handover is %s, not the 23,421 the ruling names" % rs(handed)
    mv = con.execute("SELECT id, amount_p, party FROM cash_movement WHERE id=?", (mid,)).fetchone() if mid else None
    if not mv or int(mv[1]) != old or mv[2] != "dr_bhawna":
        return "REFUSED: the landed movement %s is not the 23,421 to Dr Bhawna" % mid
    cov = con.execute("SELECT id, amount_p FROM cash_handover_cover WHERE handover_src='movement' AND handover_id=? AND covers_date=?",
                      (mid, iso)).fetchone()
    owed = con.execute("SELECT id, amount_p, status FROM darpan_kal_owed WHERE unit=? AND business_date=?", (UNIT, iso)).fetchone()
    say("A  9-Oct: handover %s -> %s (diff %s -> 0); cash_movement %d %s -> %s; cover row %s; owed row %s (%s) -> withdrawn" % (
        rs(handed), rs(new), rs(diff), mid, rs(int(mv[1])), rs(new), (("%d -> %s" % (cov[0], rs(new))) if cov else "none"),
        (owed[0] if owed else "none"), (owed[2] if owed else "-")))
    if not apply:
        return "A  would correct 9-Oct"
    before = dict(handed_p=handed, diff_p=diff, expected_p=expected, state=state, movement_p=int(mv[1]),
                  cover_p=(int(cov[1]) if cov else None), owed=(dict(id=owed[0], amount_p=int(owed[1]), status=owed[2]) if owed else None))
    con.execute("UPDATE darpan_kal_day SET handed_p=?, diff_p=?, updated_at=? WHERE unit=? AND business_date=?",
                (new, new - expected, now_iso(), UNIT, iso))
    con.execute("UPDATE cash_movement SET amount_p=? WHERE id=?", (new, mid))
    audit(con, "cash_movement", mid, "owner_correction", dict(amount_p=int(mv[1]), date=iso, party="dr_bhawna"),
          dict(amount_p=new, date=iso, party="dr_bhawna", why="the 23,421 was a typo of the handover; 13,258 = the day's cash once the bank's UPI 10,163 is taken", kit=KIT))
    if cov:
        con.execute("UPDATE cash_handover_cover SET amount_p=?, note=? WHERE id=?",
                    (new, "darpan_kal: the day this handover paid for (corrected by %s, the owner's word 18-Nov)" % KIT, cov[0]))
    if owed and owed[2] != "withdrawn":
        con.execute("UPDATE darpan_kal_owed SET status='withdrawn', note=? WHERE id=?",
                    ("withdrawn by %s: the 23,421 handover was a typo (the owner, 18-Nov-2026); nothing was owed back" % KIT, owed[0]))
    kal_audit(con, "owner_correction_s869", dict(date=iso, before=before, after=dict(handed_p=new, diff_p=new - expected),
                                                 why="the 23,421 handover typed 10-Oct was a typo; corrected once to 13,258 (the owner, 18-Nov-2026)"))
    audit(con, "darpan_kal_day", 0, "owner_correction", before, dict(date=iso, handed_p=new, diff_p=new - expected, kit=KIT))
    return "A  9-Oct corrected"


ENTRIES = [
    ("2026-11-14", "other_account", 158000, "NK Pathology UPI", None, "a patient paid into the NK Pathology UPI -- never reached the drawer (the owner, 18-Nov)"),
    ("2026-11-14", "taken_out", 400000, "dr_bhawna", "personal", "given to Darpan by Dr Bhawna for personal expenses (the owner, 18-Nov)"),
    ("2026-11-04", "other_account", 95400, "another account (UPI)", None, "a UPI done into another account (the owner, 18-Nov)"),
]


def step_bc(con, apply, say):
    import hub_cash
    hub_cash.ensure_schema(con)
    out = []
    for iso, kind, amt, party, purpose, note in ENTRIES:
        ex = con.execute("SELECT id FROM owner_day_entry WHERE unit=? AND business_date=? AND kind=? AND amount_p=? AND removed_at IS NULL",
                         (UNIT, iso, kind, amt)).fetchone()
        if ex:
            out.append("B/C %s %s %s already entered (#%d)" % (iso, kind, rs(amt), ex[0]))
            continue
        if not con.execute("SELECT 1 FROM day_entry WHERE unit=? AND business_date=?", (UNIT, iso)).fetchone():
            out.append("REFUSED: %s is not filed" % iso)
            continue
        say("B/C %s: %s %s %s -- %s" % (iso, kind, rs(amt), party, note))
        if not apply:
            out.append("B/C would enter %s %s" % (iso, rs(amt)))
            continue
        now = now_iso()
        cur = con.execute("INSERT INTO owner_day_entry (unit, business_date, kind, amount_p, party, purpose, note, entered_by, entered_at) "
                          "VALUES (?,?,?,?,?,?,?,?,?)", (UNIT, iso, kind, amt, party, purpose, note, "manoj", now))
        audit(con, "owner_day_entry", cur.lastrowid, "create",
              None, dict(date=iso, kind=kind, amount_p=amt, party=party, purpose=purpose, note=note, kit=KIT, by="the one-off"))
        out.append("B/C %s %s %s entered (#%d)" % (iso, kind, rs(amt), cur.lastrowid))
    return "\n".join(out)


def step_d(con, apply, say, fin):
    iso, bill = "2026-11-03", "A004591"
    b = con.execute("SELECT * FROM sale_bill WHERE unit=? AND business_date=? AND bill_no=?", (UNIT, iso, bill)).fetchone()
    cols = [c[0] for c in con.execute("SELECT * FROM sale_bill LIMIT 0").description]
    if not b:
        return "D  3-Nov: %s already gone from sale_bill -- done" % bill
    brow = dict(zip(cols, b))
    if int(brow["net_p"]) != 176000:
        return "REFUSED: %s nets %s, not the 1,760 the ruling names" % (bill, rs(int(brow["net_p"])))
    newest = con.execute("SELECT MAX(source_stamp) FROM sale_bill WHERE unit=? AND business_date=?", (UNIT, iso)).fetchone()[0]
    if brow["source_stamp"] >= newest:
        return "REFUSED: %s is in Marg's newest export of 3-Nov (%s) -- not a deleted bill" % (bill, newest)
    st = con.execute("SELECT status FROM day_entry WHERE unit=? AND business_date=?", (UNIT, iso)).fetchone()
    if not st or st[0] not in ("submitted", "draft"):
        return "REFUSED: 3-Nov is %s -- the day must be unapproved for pass 0 to follow Marg" % (st[0] if st else "not filed")
    li = con.execute("SELECT id, seq, item_name, qty_raw, amount_p FROM sale_line_item WHERE unit=? AND business_date=? AND bill_no=?",
                     (UNIT, iso, bill)).fetchall()
    rv = con.execute("SELECT id, status FROM sale_item_review WHERE raw_text LIKE ? AND status='open'", ('%"' + bill + '"%',)).fetchall()
    say("D  3-Nov: %s (%s, export %s; the newest is %s) -> removed with %d line(s); review line(s) %s resolved as gone; then pass 0 on the day" % (
        bill, rs(int(brow["net_p"])), brow["source_stamp"], newest, len(li), [r[0] for r in rv]))
    if not apply:
        return "D  would remove %s and re-read 3-Nov from Marg" % bill
    audit(con, "sale_bill", 0, "remove_gone_bill", dict(bill=brow, lines=[dict(id=l[0], seq=l[1], item=l[2], qty=l[3], amount_p=l[4]) for l in li]),
          dict(why="deleted in Marg (the owner, 18-Nov: a backup person was holding the sales counter); gone from the %s export" % newest, kit=KIT))
    con.execute("DELETE FROM sale_line_item WHERE unit=? AND business_date=? AND bill_no=?", (UNIT, iso, bill))
    con.execute("DELETE FROM sale_bill WHERE unit=? AND business_date=? AND bill_no=?", (UNIT, iso, bill))
    for rid, _s in rv:
        con.execute("UPDATE sale_item_review SET status='resolved', resolved_by=?, resolved_at=?, reason=? WHERE id=?",
                    ("manoj", now_iso(), "gone from Marg: the bill was deleted (the owner, 18-Nov; %s)" % KIT, rid))
        audit(con, "sale_item_review", rid, "resolve", dict(status="open"), dict(status="resolved", why="bill deleted in Marg", kit=KIT))
    con.commit()
    sys.path.insert(0, fin)
    import day_resync
    con.row_factory = sqlite3.Row
    e = con.execute("SELECT id, business_date, status FROM day_entry WHERE unit=? AND business_date=?", (UNIT, iso)).fetchone()
    v, line = day_resync.resync_marg(con, e, apply=True)
    con.row_factory = None
    stale = con.execute("SELECT COUNT(*) FROM sale_item WHERE source_ref=? AND day_entry_id=?", (bill, e["id"])).fetchone()[0]
    note = (" (note: %d sale_item row(s) still name %s -- read only, the Returns and counter cards may show it)" % (stale, bill)) if stale else ""
    if v not in ("FIXED", "SAME"):
        return "REFUSED at the end of D: %s removed but pass 0 answered %s (%s) -- the day's cash is NOT yet Marg's; tell Claude%s" % (bill, v, line, note)
    return "D  %s removed; pass 0: %s %s%s" % (bill, v, line, note)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--fin", default="/root/finance")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.path.insert(0, a.fin)
    con = sqlite3.connect(a.db, timeout=30)
    con.execute("PRAGMA busy_timeout = 30000")
    mode = "APPLY" if a.apply else "DRY"
    print("%s one-off %s on %s" % (KIT, mode, a.db))
    say = lambda t: print("   " + t)
    res = []
    try:
        con.execute("BEGIN IMMEDIATE")
        res.append(step_a(con, a.apply, say))
        res.append(step_bc(con, a.apply, say))
        if a.apply:
            con.commit()
            con.execute("BEGIN IMMEDIATE")
        res.append(step_d(con, a.apply, say, a.fin))
        if a.apply:
            con.commit()
        else:
            con.rollback()
    except Exception as ex:                                     # noqa: BLE001
        con.rollback()
        print("!! %s -- rolled back, nothing of this step kept: %r" % (KIT, ex))
        return 2
    for r in res:
        print(r)
    refused = [r for r in res if "REFUSED" in r]
    try:
        import sanjeevni_cash as sc
        con.row_factory = None
        d = sc.days(con, "2026-09-01", "9999-12-31", UNIT)
        if d.get("ok") and d["rows"]:
            cl = d["rows"][-1]["close"]
            print(("drawer now %s · with the doctors %s" if a.apply else "drawer before this one-off (after day_resync) %s · with the doctors %s")
                  % (rs(cl["drawer"]), rs(cl["with_doctors"])))
    except Exception as ex:                                     # noqa: BLE001
        print("(the one calculation could not be read back: %r)" % (ex,))
    print("%s one-off %s: %s" % (KIT, mode, "REFUSED %d step(s)" % len(refused) if refused else "OK"))
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main())
