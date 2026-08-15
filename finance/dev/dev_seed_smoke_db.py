"""Build a finance.db that satisfies the smoke suite's preconditions.

The suite is written against the real store: >100 filed days, some approved or
locked, open exceptions, and a legacy tail that leaves cash NEGATIVE. Without a
database like that it cannot run at all — which is exactly why a change to it
was shipped blind. This makes it runnable here.
"""
import datetime as dt, os, sqlite3, sys

DB = sys.argv[1] if len(sys.argv) > 1 else "finance.db"
if os.path.exists(DB): os.remove(DB)
con = sqlite3.connect(DB)
con.executescript(open("finance_schema.sql").read())
con.executescript(open("/home/claude/marg/u1/finance_migration_S180_returns.sql").read())
con.executescript(open("finance_returns.sql").read())

end = dt.date(2026, 8, 13)                      # the legacy import ends here
start = end - dt.timedelta(days=134)
d, n = start, 0
while d <= end:
    con.execute("INSERT INTO day_entry (unit,business_date,status,source,entered_by,entered_at) "
                "VALUES ('medical',?,?, 'legacy_sheet','legacy',?)",
                (d.isoformat(),
                 "approved" if n % 17 == 0 else "submitted",
                 d.isoformat() + "T10:00:00"))
    eid = con.execute("SELECT id FROM day_entry WHERE business_date=?", (d.isoformat(),)).fetchone()[0]
    cash = 1500_00 + (n * 37 % 900) * 100
    upi  =  600_00 + (n * 53 % 700) * 100
    con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,'pharmacy_sale','cash',?)", (eid, cash))
    con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,'pharmacy_sale','upi',?)", (eid, upi))
    # expenses slightly exceed cash on average -> the legacy tail ends negative
    con.execute("INSERT INTO day_expense (day_entry_id, amount_p, category_text, note) "
                "VALUES (?,?, 'purchase', 'stock')", (eid, cash + 250_00))
    d += dt.timedelta(days=1); n += 1
con.commit()

row = con.execute("SELECT business_date, closing_p FROM v_cash_ledger WHERE unit='medical' "
                  "ORDER BY business_date DESC LIMIT 1").fetchone()
print("days seeded      :", n)
print("last legacy day  :", row[0])
print("closing cash     : Rs %.2f  (must be negative)" % (row[1] / 100.0))

con.execute("INSERT OR REPLACE INTO recon_exception (unit,business_date,kind,expected_p,actual_p,"
            "diff_p,severity,status,detail,opened_at,shout_count) VALUES "
            "('medical',?, 'line_sum_vs_day_total', 100000, 0, 100000, 'medium','open','seeded',?,0)",
            (end.isoformat(), end.isoformat() + "T10:00:00"))
# a bank deposit the suite can allocate against a parked month
last_eid = con.execute("SELECT id FROM day_entry WHERE unit='medical' ORDER BY business_date DESC LIMIT 1").fetchone()[0]
con.execute("INSERT INTO cash_movement (day_entry_id,direction,party,amount_p,reference) "
            "VALUES (?, 'out','bank', 5000000, 'seed-deposit')", (last_eid,))
con.execute("INSERT OR IGNORE INTO unit_role (unit,username,role) VALUES ('medical','selftest','checker')")
con.commit()
print("open exceptions  :", con.execute("SELECT COUNT(*) FROM recon_exception WHERE status='open'").fetchone()[0])
print("approved days    :", con.execute("SELECT COUNT(*) FROM day_entry WHERE status='approved'").fetchone()[0])
con.close()
