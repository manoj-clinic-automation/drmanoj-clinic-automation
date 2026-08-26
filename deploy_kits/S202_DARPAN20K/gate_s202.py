#!/usr/bin/env python3
"""
gate_s202.py  ·  S202_DARPAN20K  ·  F-187

Proves the migration did EXACTLY one thing and nothing else.

  before  -> snapshot the whole money surface to JSON
  after   -> compare, and FAIL LOUD on any drift the migration did not intend

The installer restores the database on any red, so a failure here leaves the
books exactly as they were found.

WHAT IT ASSERTS
  1. exactly ONE new day_expense row, carrying our uid
  2. it sits on the medical 2026-08-17 day
  3. it is Rs 20,000, salary_advance, staff Darpan
  4. ledger_posted = 1 and ledger_ref = 0cc0b26b38c5
     ^ THE CRITICAL ONE. At 0 the approval path would post a SECOND Rs 20,000
       into the Staff Ledger and Darpan would appear to owe 40,000.
  5. the count of ledger-eligible rows (salary_advance AND ledger_posted=0) is
     UNCHANGED -- we added nothing the bridge can fire on
  6. the latest closing cash falls by EXACTLY 20,000 -- not 19,999, not 20,001
  7. day_line, cash_movement, cash_adjustment, cash_count, cash_custody_event,
     sale_item, sale_item_review, day_noncash_bill are byte-identical
     (row count AND sum), because this migration must not touch money or
     attribution -- D313
"""
import json, os, sqlite3, sys

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
SNAP = os.environ.get("S202_SNAP", "/tmp/s202_before.json")
UID = "exS202darpan20k17aug"
LEDGER_REF = "0cc0b26b38c5"
AMOUNT_P = 2000000
UNTOUCHED = ("day_line", "cash_movement", "cash_adjustment", "cash_count",
             "cash_custody_event", "sale_item", "sale_item_review",
             "day_noncash_bill", "day_entry")

def con():
    c = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    c.row_factory = sqlite3.Row
    return c

def one(c, sql, p=()):
    r = c.execute(sql, p).fetchone()
    return r[0] if r else None

def latest_closing_p(c):
    r = c.execute("SELECT closing_p FROM v_cash_ledger WHERE unit='medical' "
                  "ORDER BY business_date DESC, day_entry_id DESC LIMIT 1").fetchone()
    return int(r[0]) if r else None

def snapshot():
    c = con()
    s = {"closing_p": latest_closing_p(c),
         "expense_rows": one(c, "SELECT COUNT(*) FROM day_expense"),
         "expense_sum": one(c, "SELECT COALESCE(SUM(amount_p),0) FROM day_expense WHERE amount_known=1"),
         "ours": one(c, "SELECT COUNT(*) FROM day_expense WHERE expense_uid=?", (UID,)),
         "eligible": one(c, "SELECT COUNT(*) FROM day_expense WHERE category_fixed='salary_advance' AND ledger_posted=0"),
         "tables": {}}
    for t in UNTOUCHED:
        s["tables"][t] = [one(c, "SELECT COUNT(*) FROM %s" % t), 0]
        for col in ("amount_p", "counted_p"):
            try:
                s["tables"][t][1] = one(c, "SELECT COALESCE(SUM(%s),0) FROM %s" % (col, t)) or 0
                break
            except sqlite3.OperationalError:
                continue
    c.close()
    return s

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "before"
    if mode == "before":
        s = snapshot()
        json.dump(s, open(SNAP, "w"))
        print("  snapshot taken: closing Rs %s · %s expense rows · %s ledger-eligible"
              % (format(s["closing_p"]/100, ",.2f"), s["expense_rows"], s["eligible"]))
        if s["ours"]:
            print("  !! REFUSING: this migration is ALREADY applied (uid %s present)" % UID)
            return 1
        return 0

    b = json.load(open(SNAP))
    a = snapshot()
    c = con()
    fails, checks = [], 0
    def ck(label, cond):
        nonlocal checks
        checks += 1
        print("   %s  %s" % ("ok  " if cond else "FAIL", label))
        if not cond:
            fails.append(label)

    ck("exactly one new day_expense row", a["expense_rows"] == b["expense_rows"] + 1)
    ck("it carries our uid, exactly once", a["ours"] == 1)
    r = c.execute("SELECT x.*, e.business_date, e.unit, s.name AS staff_name "
                  "FROM day_expense x JOIN day_entry e ON e.id=x.day_entry_id "
                  "LEFT JOIN staff_ref s ON s.id=x.staff_id "
                  "WHERE x.expense_uid=?", (UID,)).fetchone()
    ck("the row exists and is readable", r is not None)
    if r:
        ck("on the medical 2026-08-17 day", r["business_date"] == "2026-08-17" and r["unit"] == "medical")
        ck("amount is exactly Rs 20,000", r["amount_p"] == AMOUNT_P)
        ck("amount_known = 1 (so the cash ledger counts it)", r["amount_known"] == 1)
        ck("category_fixed = salary_advance", r["category_fixed"] == "salary_advance")
        ck("staff is Darpan", (r["staff_name"] or "") == "Darpan")
        ck("LEDGER GUARD: ledger_posted = 1", r["ledger_posted"] == 1)
        ck("LEDGER GUARD: ledger_ref = %s" % LEDGER_REF, (r["ledger_ref"] or "") == LEDGER_REF)
    ck("no NEW ledger-eligible row was created (bridge cannot fire)",
       a["eligible"] == b["eligible"])
    ck("expense total rose by exactly Rs 20,000",
       a["expense_sum"] == b["expense_sum"] + AMOUNT_P)
    ck("latest closing cash FELL by exactly Rs 20,000",
       a["closing_p"] == b["closing_p"] - AMOUNT_P)
    for t in UNTOUCHED:
        ck("%s untouched (rows and sum)" % t, a["tables"][t] == b["tables"][t])
    ck("the migration marker is recorded",
       one(c, "SELECT COUNT(*) FROM setting WHERE key='migration.S202_darpan20k'") == 1)
    c.close()

    print("\n  %d checks, %d failed" % (checks, len(fails)))
    if fails:
        print("  RED — the installer will restore the database untouched.")
        for f in fails:
            print("     · %s" % f)
        return 1
    print("  GREEN — the drawer now reads Rs %s, and nothing else moved."
          % format(a["closing_p"]/100, ",.2f"))
    return 0

if __name__ == "__main__":
    sys.exit(main())
