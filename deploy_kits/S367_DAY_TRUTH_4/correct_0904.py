#!/usr/bin/env python3
"""correct_0904.py -- kit S367_DAY_TRUTH_4 · the owner's ruling D602 (22-Sep-2026).

04-Sep-2026 (pharmacy) was filed automatically at 09:03 on 05-Sep from Marg's 08:53 export: 17 bills,
23,675 (cash 11,066 + UPI 12,609). Marg's 06-Sep export carries an 18th bill for that day, A003396,
200 in cash. The owner ruled: Marg's bills are the day -- the sale is 23,875, the 200 cash belongs to
04-Sep, it is not a shortage, and the approved day is corrected VISIBLY.

This moves the day's cash line 11,066 -> 11,266, once, only if every figure is exactly as read on
22-Sep; writes one audit_log row 'correct' with before / after and the ruling. UPI, the approval, the
bills, Marg are not touched. The one calculation then sends the 200 with the day's cash to the pool.
Idempotent: a second run says ALREADY and changes nothing.
    python3 correct_0904.py [--db PATH] [--dry-run]
"""
import argparse, datetime as dt, json, os, sqlite3, sys

KIT, ISO, BILL = "S367_DAY_TRUTH_4", "2026-09-04", "A003396"
CASH_FROM, CASH_TO, UPI, MARG = 1106600, 1126600, 1260900, 2387500
ap = argparse.ArgumentParser()
ap.add_argument("--db", default=os.environ.get("FINANCE_DB", "/root/finance/finance.db"))
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
con = sqlite3.connect(a.db, timeout=30)
e = con.execute("SELECT id, status FROM day_entry WHERE unit='medical' AND business_date=?", (ISO,)).fetchone()
if not e:
    sys.exit("RED: no 04-Sep pharmacy day")
eid = e[0]
lines = con.execute("SELECT id, mode, amount_p FROM day_line WHERE day_entry_id=? AND service='pharmacy_sale' "
                    "ORDER BY mode", (eid,)).fetchall()
cash = [l for l in lines if l[1] == "cash"]; upi = [l for l in lines if l[1] == "upi"]
marg = con.execute("SELECT COALESCE(SUM(net_p),0) FROM sale_bill WHERE unit='medical' AND business_date=?", (ISO,)).fetchone()[0]
bill = con.execute("SELECT net_p, cash_p FROM sale_bill WHERE unit='medical' AND business_date=? AND bill_no=?", (ISO, BILL)).fetchone()
if len(cash) == 1 and cash[0][2] == CASH_TO and con.execute(
        "SELECT 1 FROM audit_log WHERE table_name='day_entry' AND row_id=? AND action='correct' AND after_json LIKE '%D602%'",
        (eid,)).fetchone():
    print("ALREADY: 04-Sep cash is 11,266 under D602 -- nothing changed"); sys.exit(0)
ok = (len(cash) == 1 and cash[0][2] == CASH_FROM and len(upi) == 1 and upi[0][2] == UPI
      and marg == MARG and bill == (20000, 20000))
if not ok:
    sys.exit("RED: 04-Sep is not as read on 22-Sep (cash %s, upi %s, marg %s, bill %s) -- nothing changed"
             % ([c[2] for c in cash], [u[2] for u in upi], marg, bill))
now = dt.datetime.now().replace(microsecond=0).isoformat()
before = dict(date=ISO, status=e[1], cash_p=CASH_FROM, upi_p=UPI, net_p=CASH_FROM + UPI)
after = dict(date=ISO, status=e[1], cash_p=CASH_TO, upi_p=UPI, net_p=MARG, bill=BILL, bill_p=20000,
             ruling="D602, the owner, 22-Sep-2026: Marg's bills are the day; bill A003396 (200 cash, "
                    "Marg's 06-Sep export) belongs to 04-Sep; not a shortage", kit=KIT)
if a.dry_run:
    print("WOULD: 04-Sep cash 11,066 -> 11,266 (sale 23,675 -> 23,875), audit 'correct' under D602"); sys.exit(0)
con.execute("UPDATE day_line SET amount_p=? WHERE id=?", (CASH_TO, cash[0][0]))
con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) "
            "VALUES ('day_entry', ?, 'correct', ?, ?, 'manoj (ruling D602)', ?)",
            (eid, json.dumps(before), json.dumps(after), now))
con.commit()
print("DONE: 04-Sep cash 11,066 -> 11,266 (sale 23,875 = Marg's 18 bills), audit 'correct' under D602")
