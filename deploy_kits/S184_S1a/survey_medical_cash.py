#!/usr/bin/env python3
# =============================================================================
#  survey_medical_cash.py  ·  Session 184  ·  READ-ONLY
#
#  WHAT THIS IS
#    A survey of the medical (Sanjeevni) cash chain, taken off the live box so
#    the S184 deposit-booking migration is built against the machine and not
#    against the record (D321(d): the box wins).
#
#  IT CANNOT WRITE. The database is opened with SQLite URI mode=ro, so a write
#  is refused by the driver, not by this script's good intentions.
#
#  IT PRINTS NO PHI. Only dates, money, statuses, counts and staff first names.
#  No patient name, no phone, no clinic id.
#
#  RUN (on the VPS):
#      /usr/bin/python3 /root/deploy/survey_medical_cash.py
#
#  Paste the whole output back into the session.
# =============================================================================
import sqlite3, sys, os

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
UNIT = "medical"

DEPOSITS = [  # the 16 Yes Bank cash deposits from S183 (dates only, for lookup)
    "2026-04-09", "2026-04-13", "2026-04-27", "2026-05-02",
    "2026-05-07", "2026-05-12", "2026-05-22", "2026-06-04",
    "2026-06-12", "2026-06-17", "2026-07-01", "2026-07-07",
    "2026-07-14", "2026-07-22", "2026-07-30", "2026-08-13",
]
ADVANCES = ["2026-04-09", "2026-05-30", "2026-06-18"]


def rs(p):
    if p is None:
        return "—"
    neg = p < 0
    p = abs(int(p))
    w, f = divmod(p, 100)
    t = str(w)
    if len(t) > 3:
        head, tail = t[:-3], t[-3:]
        out = ""
        for i, ch in enumerate(reversed(head)):
            if i and i % 2 == 0:
                out = "," + out
            out = ch + out
        out = out + "," + tail
    else:
        out = t
    return ("-" if neg else "") + "Rs " + out + "." + str(f).zfill(2)


def h(title):
    print()
    print("=" * 74)
    print(" " + title)
    print("=" * 74)


def q(c, sql, args=()):
    try:
        return c.execute(sql, args).fetchall()
    except Exception as e:                                   # noqa: BLE001
        print("   !! query failed: %s" % e)
        return []


def main():
    if not os.path.exists(DB):
        print("!! not found: %s" % DB)
        return 1
    c = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    c.row_factory = sqlite3.Row

    print("survey_medical_cash.py  ·  READ-ONLY  ·  unit = %s" % UNIT)
    print("database : %s" % DB)
    print("size     : %s bytes" % os.path.getsize(DB))
    # prove the read-only claim rather than asserting it
    try:
        c.execute("update setting set value=value where key='__never__'")
        print("guard    : !! WARNING — the connection accepted a write. STOP.")
    except sqlite3.OperationalError as e:
        print("guard    : read-only confirmed by the driver (%s)" % e)

    # ---------------------------------------------------------------- 1
    h("1. THE DAY SPINE — how many days, what statuses, what span")
    r = q(c, """select count(*) n, min(business_date) lo, max(business_date) hi
                  from day_entry where unit=?""", (UNIT,))
    if r:
        print("   day_entry rows : %s" % r[0]["n"])
        print("   earliest day   : %s" % r[0]["lo"])
        print("   latest day     : %s" % r[0]["hi"])
    print()
    for row in q(c, """select status, source, count(*) n from day_entry
                        where unit=? group by status, source order by 3 desc""", (UNIT,)):
        print("   %-16s %-14s %5d" % (row["status"], row["source"], row["n"]))

    # ---------------------------------------------------------------- 2
    h("2. THE CASH CHAIN AS IT STANDS — closing balance, last 20 filed days")
    print("   %-12s %12s %12s %10s %10s %10s %12s" %
          ("date", "opening", "cash in", "noncash", "expense", "out/in", "closing"))
    for row in q(c, """select business_date, opening_p, cash_in_p, noncash_p, expense_p,
                              cash_out_p, cash_back_p, adjust_p, closing_p
                         from v_cash_ledger where unit=?
                        order by business_date desc, day_entry_id desc limit 20""", (UNIT,)):
        print("   %-12s %12s %12s %10s %10s %10s %12s" % (
            row["business_date"], rs(row["opening_p"]), rs(row["cash_in_p"]),
            rs(row["noncash_p"]), rs(row["expense_p"]),
            rs(row["cash_out_p"] - row["cash_back_p"]), rs(row["closing_p"])))

    # ---------------------------------------------------------------- 3
    h("3. WHAT MAKES UP THE BALANCE — the whole chain, one line each")
    r = q(c, """select sum(cash_in_p) ci, sum(noncash_p) nc, sum(expense_p) ex,
                       sum(cash_out_p) co, sum(cash_back_p) cb, sum(adjust_p) ad
                  from v_day_cash where unit=?""", (UNIT,))
    if r:
        a = r[0]
        print("   cash collected (day_line mode=cash)   %18s" % rs(a["ci"]))
        print("   less billed-no-cash (noncash bills)   %18s" % rs(-(a["nc"] or 0)))
        print("   less expenses                         %18s" % rs(-(a["ex"] or 0)))
        print("   less cash out (movements)             %18s" % rs(-(a["co"] or 0)))
        print("   plus cash back (movements)            %18s" % rs(a["cb"]))
        print("   plus adjustments (signed)             %18s" % rs(a["ad"]))
        tot = ((a["ci"] or 0) - (a["nc"] or 0) - (a["ex"] or 0)
               - (a["co"] or 0) + (a["cb"] or 0) + (a["ad"] or 0))
        print("   " + "-" * 54)
        print("   COMPUTED CLOSING TODAY                %18s" % rs(tot))
        print()
        print("   >> This is the line that matters. If 'adjustments' or 'cash out'")
        print("      is large, the -Rs 30,056 is NOT simply missing deposits and the")
        print("      S184 migration must be built differently.")

    # ---------------------------------------------------------------- 4
    h("4. CASH MOVEMENTS ALREADY RECORDED — are any deposits already in?")
    r = q(c, """select m.direction, m.party, count(*) n, sum(m.amount_p) s
                  from cash_movement m join day_entry e on e.id=m.day_entry_id
                 where e.unit=? group by 1,2 order by 4 desc""", (UNIT,))
    if not r:
        print("   (none at all — the drawer has never recorded a deposit)")
    for row in r:
        print("   %-5s %-12s  n=%-5d  %18s" %
              (row["direction"], row["party"], row["n"], rs(row["s"])))
    print()
    print("   -- movements on the 16 Yes Bank deposit dates specifically:")
    hit = 0
    for d in DEPOSITS:
        rr = q(c, """select m.direction, m.party, m.amount_p, m.reference
                       from cash_movement m join day_entry e on e.id=m.day_entry_id
                      where e.unit=? and e.business_date=?""", (UNIT, d))
        for row in rr:
            hit += 1
            print("   %s  %-4s %-10s %14s  %s" % (
                d, row["direction"], row["party"], rs(row["amount_p"]),
                row["reference"] or ""))
    if not hit:
        print("   (none — confirms all 16 are unrecorded)")

    # ---------------------------------------------------------------- 5
    h("5. ADJUSTMENTS — the legacy import's own corrections")
    r = q(c, """select a.source, a.status, count(*) n, sum(a.amount_p) s
                  from cash_adjustment a join day_entry e on e.id=a.day_entry_id
                 where e.unit=? group by 1,2""", (UNIT,))
    if not r:
        print("   (none)")
    for row in r:
        print("   %-14s %-10s n=%-5d %18s" %
              (row["source"], row["status"], row["n"], rs(row["s"])))
    print()
    print("   -- the 10 largest, with reasons:")
    for row in q(c, """select e.business_date d, a.amount_p, a.status, a.reason
                         from cash_adjustment a join day_entry e on e.id=a.day_entry_id
                        where e.unit=? order by abs(a.amount_p) desc limit 10""", (UNIT,)):
        print("   %s %14s %-10s %s" % (row["d"], rs(row["amount_p"]), row["status"],
                                       (row["reason"] or "")[:44]))

    # ---------------------------------------------------------------- 6
    h("6. THE 16 DEPOSIT DATES — does a day_entry exist to hang a movement on?")
    print("   %-12s %-10s %-16s %14s" % ("date", "exists", "status", "cash that day"))
    for d in DEPOSITS:
        rr = q(c, """select e.status, v.cash_in_p from day_entry e
                       left join v_day_cash v on v.day_entry_id=e.id
                      where e.unit=? and e.business_date=?""", (UNIT, d))
        if rr:
            print("   %-12s %-10s %-16s %14s" %
                  (d, "yes", rr[0]["status"], rs(rr[0]["cash_in_p"])))
        else:
            print("   %-12s %-10s %-16s %14s   << needs creating" % (d, "NO", "—", "—"))

    # ---------------------------------------------------------------- 7
    h("7. THE 3 SALARY-ADVANCE DATES + what expenses are already on them")
    for d in ADVANCES:
        rr = q(c, """select e.id, e.status from day_entry e
                      where e.unit=? and e.business_date=?""", (UNIT, d))
        if not rr:
            print("   %s  NO day_entry   << needs creating" % d)
            continue
        print("   %s  day_entry #%s (%s)" % (d, rr[0]["id"], rr[0]["status"]))
        for x in q(c, """select amount_p, category_fixed, category_text, staff_id,
                                ledger_posted from day_expense where day_entry_id=?""",
                   (rr[0]["id"],)):
            print("        expense %12s  fixed=%-14s staff=%-5s posted=%s  %s" % (
                rs(x["amount_p"]), x["category_fixed"], x["staff_id"],
                x["ledger_posted"], (x["category_text"] or "")[:30]))

    h("7b. ALL salary_advance expenses ever recorded for this unit")
    r = q(c, """select e.business_date d, x.amount_p, x.staff_id, x.ledger_posted
                  from day_expense x join day_entry e on e.id=x.day_entry_id
                 where e.unit=? and x.category_fixed='salary_advance'
                 order by e.business_date""", (UNIT,))
    if not r:
        print("   (none — so booking the 3 advances cannot double-count inside finance)")
    for row in r:
        print("   %s %14s staff=%-5s ledger_posted=%s" %
              (row["d"], rs(row["amount_p"]), row["staff_id"], row["ledger_posted"]))

    # ---------------------------------------------------------------- 8
    h("8. STAFF — who can a salary advance be attached to")
    for row in q(c, "select id, register_id, name, is_pharmacy from staff_ref order by id"):
        print("   id=%-4s register_id=%-6s pharmacy=%s  %s" %
              (row["id"], row["register_id"], row["is_pharmacy"], row["name"]))

    # ---------------------------------------------------------------- 9
    h("9. OPEN EXCEPTIONS by kind (what the migration should clear)")
    for row in q(c, """select kind, status, count(*) n from recon_exception
                        where unit=? group by 1,2 order by 3 desc""", (UNIT,)):
        print("   %-32s %-10s %5d" % (row["kind"], row["status"], row["n"]))
    print()
    print("   -- every unfiled day (the shout list, uncapped):")
    r = q(c, """select business_date from recon_exception
                 where unit=? and kind='missing_day' and status='open'
                 order by business_date""", (UNIT,))
    print("   count = %d" % len(r))
    print("   " + ", ".join(row["business_date"] for row in r))

    # ---------------------------------------------------------------- 10
    h("10. DAYS WHERE THE COMPUTED DRAWER IS NEGATIVE")
    r = q(c, """select business_date, closing_p from v_cash_ledger
                 where unit=? and closing_p < 0 order by business_date""", (UNIT,))
    print("   count = %d" % len(r))
    if r:
        print("   first : %s  %s" % (r[0]["business_date"], rs(r[0]["closing_p"])))
        print("   worst : %s" % rs(min(x["closing_p"] for x in r)))
        print("   last  : %s  %s" % (r[-1]["business_date"], rs(r[-1]["closing_p"])))

    # ---------------------------------------------------------------- 11
    h("11. AUGUST 2026 IN FULL")
    print("   %-12s %-10s %12s %12s %12s %12s" %
          ("date", "status", "cash", "upi", "noncash", "closing"))
    for row in q(c, """select e.business_date d, e.status,
                              v.cash_in_p, v.upi_in_p, v.noncash_p, l.closing_p
                         from day_entry e
                         left join v_day_cash v on v.day_entry_id=e.id
                         left join v_cash_ledger l on l.day_entry_id=e.id
                        where e.unit=? and e.business_date like '2026-08%'
                        order by e.business_date""", (UNIT,)):
        print("   %-12s %-10s %12s %12s %12s %12s" % (
            row["d"], row["status"], rs(row["cash_in_p"]), rs(row["upi_in_p"]),
            rs(row["noncash_p"]), rs(row["closing_p"])))

    # ---------------------------------------------------------------- 12
    h("12. NONCASH BILLS (home / procedure medicine) already captured")
    r = q(c, """select b.head, count(*) n, sum(b.amount_p) s
                  from day_noncash_bill b where b.unit=? group by 1""", (UNIT,))
    if not r:
        print("   (none recorded yet)")
    for row in r:
        print("   %-22s n=%-5d %18s" % (row["head"], row["n"], rs(row["s"])))

    # ---------------------------------------------------------------- 13
    h("13. CASH COUNTS ever taken (the physical anchor)")
    r = q(c, "select business_date, counted_p, counted_by from cash_count where unit=? order by 1", (UNIT,))
    if not r:
        print("   (never counted — so the opening anchor has to be derived)")
    for row in r:
        print("   %s %16s  by %s" % (row["business_date"], rs(row["counted_p"]), row["counted_by"]))

    # ---------------------------------------------------------------- 14
    h("14. MIGRATION MARKERS already applied")
    for row in q(c, "select key, value from setting where key like 'migration.%' order by 1"):
        print("   %-40s %s" % (row["key"], row["value"]))

    c.close()
    print()
    print("=" * 74)
    print(" END OF SURVEY — nothing was written. Paste all of the above back.")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
