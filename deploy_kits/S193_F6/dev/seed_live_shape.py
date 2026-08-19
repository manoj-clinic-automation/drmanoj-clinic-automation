"""Seeded finance.db for the F6 smoke — dev_seed_smoke_db.py extended to the
LIVE SHAPE (F-140): plus a Darpan staff_ref row and an APPROVED day carrying a
salary_advance expense at ledger_posted=0. Local SQL paths (no /home/claude/marg)."""
import datetime as dt, os, sqlite3, sys
DB = sys.argv[1] if len(sys.argv) > 1 else "finance_seed.db"
if os.path.exists(DB): os.remove(DB)
con = sqlite3.connect(DB)
con.executescript(open("finance_schema.sql").read())
con.executescript(open("finance_migration_S180_returns.sql").read())
con.executescript(open("finance_returns.sql").read())

end = dt.date(2026, 8, 13); start = end - dt.timedelta(days=134)
d, n = start, 0
while d <= end:
    con.execute("INSERT INTO day_entry (unit,business_date,status,source,entered_by,entered_at) "
                "VALUES ('medical',?,?, 'legacy_sheet','legacy',?)",
                (d.isoformat(), "approved" if n % 17 == 0 else "submitted", d.isoformat()+"T10:00:00"))
    eid = con.execute("SELECT id FROM day_entry WHERE business_date=?", (d.isoformat(),)).fetchone()[0]
    cash = 1500_00 + (n*37 % 900)*100; upi = 600_00 + (n*53 % 700)*100
    con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,'pharmacy_sale','cash',?)", (eid, cash))
    con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,'pharmacy_sale','upi',?)", (eid, upi))
    con.execute("INSERT INTO day_expense (day_entry_id, amount_p, category_text, note) VALUES (?,?, 'purchase', 'stock')", (eid, cash+250_00))
    d += dt.timedelta(days=1); n += 1
con.commit()
row = con.execute("SELECT business_date, closing_p FROM v_cash_ledger WHERE unit='medical' ORDER BY business_date DESC LIMIT 1").fetchone()
print("days seeded      :", n)
print("closing cash     : Rs %.2f  (must be negative)" % (row[1]/100.0))
con.execute("INSERT OR REPLACE INTO recon_exception (unit,business_date,kind,expected_p,actual_p,diff_p,severity,status,detail,opened_at,shout_count) "
            "VALUES ('medical',?, 'line_sum_vs_day_total', 100000, 0, 100000, 'medium','open','seeded',?,0)", (end.isoformat(), end.isoformat()+"T10:00:00"))
last_eid = con.execute("SELECT id FROM day_entry WHERE unit='medical' ORDER BY business_date DESC LIMIT 1").fetchone()[0]
con.execute("INSERT INTO cash_movement (day_entry_id,direction,party,amount_p,reference) VALUES (?, 'out','bank', 5000000, 'seed-deposit')", (last_eid,))
con.execute("INSERT OR IGNORE INTO unit_role (unit,username,role) VALUES ('medical','selftest','checker')")
con.commit()

# ---- LIVE SHAPE (F-140): staff_ref Darpan + an approved day with a
#      salary_advance expense at ledger_posted=0 (the F6 bridge's input) ----
con.execute("INSERT OR IGNORE INTO staff_ref (name, is_pharmacy, active) VALUES ('Darpan',1,1)")
sid = con.execute("SELECT id FROM staff_ref WHERE name='Darpan' AND active=1").fetchone()[0]
adv_date = dt.date(2026, 8, 14).isoformat()   # a fresh APPROVED day, past the legacy tail
con.execute("INSERT INTO day_entry (unit,business_date,status,source,entered_by,entered_at,approved_by,approved_at) "
            "VALUES ('medical',?,'approved','app','darpan',?,?,?)",
            (adv_date, adv_date+"T10:00:00", "manoj", adv_date+"T11:00:00"))
aeid = con.execute("SELECT id FROM day_entry WHERE business_date=?", (adv_date,)).fetchone()[0]
con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,'pharmacy_sale','cash',300000)", (aeid,))
con.execute("INSERT INTO day_expense (day_entry_id, amount_p, category_fixed, staff_id, category_text, note, ledger_posted) "
            "VALUES (?, 200000, 'salary_advance', ?, NULL, 'advance to Darpan', 0)", (aeid, sid))
con.commit()
print("staff_ref Darpan :", sid)
print("approved adv day :", adv_date, "expense_p_p=200000 ledger_posted=0")
print("approved days    :", con.execute("SELECT COUNT(*) FROM day_entry WHERE status='approved'").fetchone()[0])
con.close()
