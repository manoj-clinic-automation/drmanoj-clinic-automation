-- =============================================================================
--  finance_migration_S202_darpan20k.sql  ·  Session 202  ·  F-187
--
--  WHAT IS WRONG
--  -------------
--  On 17 Aug 2026 Darpan's drawer was cleared. cash_count.explanation and the
--  S186 close both record the itemisation in words:
--
--      48,963 = 10,000 July-salary advance adjustment
--             + 20,000 August-salary advance
--             + 18,963 handed to the owner
--
--  The 18,963 was recorded (cash_custody_event #4). The 10,000 was recorded
--  (day_expense #56, 31-Jul). THE 20,000 WAS NEVER RECORDED ANYWHERE AS MONEY
--  LEAVING THE DRAWER -- it exists only as prose inside an explanation column,
--  which is F-137's exact shape: a custody fact written where no query can
--  reach it.
--
--  PROVEN BY PHYSICAL COUNT, NOT BY ARGUMENT (25 Aug 2026, owner):
--      books say the drawer holds   63,903
--      the drawer physically holds  43,903
--      difference                   20,000   exactly, to the rupee
--
--  WHAT THIS MIGRATION DOES
--  ------------------------
--  ONE INSERT into day_expense, on the 17-Aug day, plus one marker.
--  v_cash_ledger computes closing as
--      cash_in - noncash - EXPENSE - cash_out + cash_back + adjust
--  so this row moves every closing from 17-Aug forward down by exactly 20,000
--  and lands the drawer on the counted figure.
--
--  THE ONE THING THAT MAKES THIS SAFE, AND WHY
--  -------------------------------------------
--  ledger_posted IS SET TO 1 AT INSERT, carrying the Staff Ledger reference
--  0cc0b26b38c5 -- the SPECIAL the owner approved on 17-Aug for this same
--  20,000.
--
--  finance_app.py's approval path selects salary-advance expenses
--  WHERE ledger_posted=0 and posts each one to the Staff Ledger. A row left at
--  0 would post a SECOND 20,000 the next time that day is approved, and Darpan
--  would appear to owe 40,000. Stamping it posted uses the system's own
--  idempotency guard for exactly what it was built for, and links the two books
--  instead of duplicating them.
--
--  WHAT IT DOES NOT TOUCH
--  ----------------------
--  day_line (the money -- D313), cash_movement, cash_adjustment, cash_count,
--  cash_custody_event, sale_item, the Staff Ledger. The gate proves each is
--  byte-identical afterwards and RESTORES the whole database if any moved.
-- =============================================================================

INSERT INTO day_expense
    (day_entry_id, amount_p, amount_known, category_fixed, staff_id,
     category_text, note, ledger_posted, ledger_posted_at, ledger_ref,
     expense_uid, category_kind)
SELECT
    e.id,
    2000000,
    1,
    'salary_advance',
    (SELECT id FROM staff_ref WHERE name='Darpan'),
    'Salary advance - Darpan',
    'S202 (F-187). The August salary advance of Rs 20,000 handed from the '
    || 'drawer on 17-Aug-2026. Recorded in words in cash_count.explanation and '
    || 'in the S186 close since 17-Aug, but never as an entry -- so the drawer '
    || 'carried 20,000 it did not hold, every day from 17-Aug onward. '
    || 'Established by PHYSICAL COUNT on 25-Aug-2026: books 63,903, drawer '
    || '43,903, difference 20,000 exactly. ledger_posted=1 against Staff Ledger '
    || 'SPECIAL 0cc0b26b38c5 (approved 17-Aug, Rs 20,000, against 2026-08) so '
    || 'the approval path CANNOT post it a second time. The ledger side was '
    || 'already correct; only the drawer side was missing.',
    1,
    '2026-08-25',
    '0cc0b26b38c5',
    'exS202darpan20k17aug',
    NULL
FROM day_entry e
WHERE e.unit = 'medical'
  AND e.business_date = '2026-08-17'
  AND NOT EXISTS (SELECT 1 FROM day_expense x
                   WHERE x.day_entry_id = e.id
                     AND x.expense_uid = 'exS202darpan20k17aug');

INSERT OR REPLACE INTO setting (key, value, note) VALUES
 ('migration.S202_darpan20k','applied 2026-08-25',
  'S202/F-187. One day_expense row: Rs 20,000 Darpan salary advance on the '
  || '17-Aug day, stamped ledger_posted=1 against SPECIAL 0cc0b26b38c5. Closes '
  || 'the 20,000 gap between the books (63,903) and the counted drawer (43,903). '
  || 'Reverse with: DELETE FROM day_expense WHERE expense_uid='
  || '''exS202darpan20k17aug''; DELETE FROM setting WHERE key='
  || '''migration.S202_darpan20k'';');
