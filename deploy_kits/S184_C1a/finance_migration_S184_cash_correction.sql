-- =============================================================================
--  finance_migration_S184_cash_correction.sql   ·  Session 184
--
--  PURPOSE  Correct the Sanjeevni (medical) historical cash books, which the S179
--  import loaded VERBATIM from the buggy Google Sheet: 31 deposit movements
--  (Rs 16,59,114, the sheet's own Deposit column) and 36 carry-forward
--  'adjustments' (net -Rs 84,533, the sheet papering over its own drift). Those
--  reproduce the impossible -Rs 30,056 closing exactly.
--
--  WHAT IT DOES  (all inside one transaction; every removal is BACKED UP first)
--    1. Copy the 31 medical bank-out cash_movement rows and the 36 medical
--       cash_adjustment rows into s184_removed_* tables (full reversibility).
--    2. Delete them from the live tables.
--    3. Insert the 16 bank-VERIFIED Yes Bank deposits on their real dates.
--    4. Insert Darpan's 3 salary advances (Rs 40,000) as drawer EXPENSES with
--       NO staff_id and NO category_fixed -> they reduce the drawer but do NOT
--       post to the Staff Ledger (owner's choice; salary system reviewed later).
--    5. Insert the 2 mis-keyed procedure-medicine bills (Rs 337) as noncash bills.
--    6. Write the marker row.
--
--  RESULT  Opening stays 0 (computed; nothing precedes 1 Apr). 13 Aug closes at
--  +Rs 27,654. Interim days around the big bank lumps (4 Jun, 7 Jul...) show
--  negative cash: that is the honest footprint of cash parked with Dr Bhawna
--  ahead of a bank trip, to be reconciled later from her copy (owner, option 2).
--
--  MONEY MOVED  none in reality — this makes the RECORD match what already
--  happened at the bank. day_line (the sale money) is never touched.
--
--  IDEMPOTENT  every INSERT is guarded by NOT EXISTS on its S184 marker string;
--  the backup copy is guarded on id. Re-running changes nothing. The installer
--  also refuses if the marker is already 'applied'.
--
--  REVERSIBLE  rollback block at the foot restores the originals byte-for-byte
--  from s184_removed_* and drops the S184 inserts. The installer also backs up
--  the whole finance.db first.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS s184_removed_movements   AS SELECT * FROM cash_movement   WHERE 0;
CREATE TABLE IF NOT EXISTS s184_removed_adjustments AS SELECT * FROM cash_adjustment WHERE 0;

INSERT INTO s184_removed_movements
  SELECT m.* FROM cash_movement m JOIN day_entry e ON e.id = m.day_entry_id
   WHERE e.unit='medical' AND m.party='bank' AND m.direction='out'
     AND NOT EXISTS (SELECT 1 FROM s184_removed_movements b WHERE b.id = m.id);

INSERT INTO s184_removed_adjustments
  SELECT a.* FROM cash_adjustment a JOIN day_entry e ON e.id = a.day_entry_id
   WHERE e.unit='medical'
     AND NOT EXISTS (SELECT 1 FROM s184_removed_adjustments b WHERE b.id = a.id);

DELETE FROM cash_movement   WHERE id IN (SELECT id FROM s184_removed_movements);
DELETE FROM cash_adjustment WHERE id IN (SELECT id FROM s184_removed_adjustments);

-- 3. the 16 bank-verified Yes Bank deposits (amount in paise)
INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference)
  SELECT e.id,'out','bank',11500000,'Yes Bank verified deposit (S184)' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-04-09'
     AND NOT EXISTS (SELECT 1 FROM cash_movement m WHERE m.day_entry_id=e.id AND m.reference='Yes Bank verified deposit (S184)');
INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference)
  SELECT e.id,'out','bank',6000000,'Yes Bank verified deposit (S184)' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-04-13'
     AND NOT EXISTS (SELECT 1 FROM cash_movement m WHERE m.day_entry_id=e.id AND m.reference='Yes Bank verified deposit (S184)');
INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference)
  SELECT e.id,'out','bank',14300000,'Yes Bank verified deposit (S184)' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-04-27'
     AND NOT EXISTS (SELECT 1 FROM cash_movement m WHERE m.day_entry_id=e.id AND m.reference='Yes Bank verified deposit (S184)');
INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference)
  SELECT e.id,'out','bank',5260000,'Yes Bank verified deposit (S184)' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-05-02'
     AND NOT EXISTS (SELECT 1 FROM cash_movement m WHERE m.day_entry_id=e.id AND m.reference='Yes Bank verified deposit (S184)');
INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference)
  SELECT e.id,'out','bank',8000000,'Yes Bank verified deposit (S184)' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-05-07'
     AND NOT EXISTS (SELECT 1 FROM cash_movement m WHERE m.day_entry_id=e.id AND m.reference='Yes Bank verified deposit (S184)');
INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference)
  SELECT e.id,'out','bank',6500000,'Yes Bank verified deposit (S184)' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-05-12'
     AND NOT EXISTS (SELECT 1 FROM cash_movement m WHERE m.day_entry_id=e.id AND m.reference='Yes Bank verified deposit (S184)');
INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference)
  SELECT e.id,'out','bank',12000000,'Yes Bank verified deposit (S184)' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-05-22'
     AND NOT EXISTS (SELECT 1 FROM cash_movement m WHERE m.day_entry_id=e.id AND m.reference='Yes Bank verified deposit (S184)');
INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference)
  SELECT e.id,'out','bank',15000000,'Yes Bank verified deposit (S184)' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-06-04'
     AND NOT EXISTS (SELECT 1 FROM cash_movement m WHERE m.day_entry_id=e.id AND m.reference='Yes Bank verified deposit (S184)');
INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference)
  SELECT e.id,'out','bank',11000000,'Yes Bank verified deposit (S184)' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-06-12'
     AND NOT EXISTS (SELECT 1 FROM cash_movement m WHERE m.day_entry_id=e.id AND m.reference='Yes Bank verified deposit (S184)');
INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference)
  SELECT e.id,'out','bank',8500000,'Yes Bank verified deposit (S184)' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-06-17'
     AND NOT EXISTS (SELECT 1 FROM cash_movement m WHERE m.day_entry_id=e.id AND m.reference='Yes Bank verified deposit (S184)');
INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference)
  SELECT e.id,'out','bank',13500000,'Yes Bank verified deposit (S184)' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-07-01'
     AND NOT EXISTS (SELECT 1 FROM cash_movement m WHERE m.day_entry_id=e.id AND m.reference='Yes Bank verified deposit (S184)');
INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference)
  SELECT e.id,'out','bank',18000000,'Yes Bank verified deposit (S184)' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-07-07'
     AND NOT EXISTS (SELECT 1 FROM cash_movement m WHERE m.day_entry_id=e.id AND m.reference='Yes Bank verified deposit (S184)');
INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference)
  SELECT e.id,'out','bank',10500000,'Yes Bank verified deposit (S184)' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-07-14'
     AND NOT EXISTS (SELECT 1 FROM cash_movement m WHERE m.day_entry_id=e.id AND m.reference='Yes Bank verified deposit (S184)');
INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference)
  SELECT e.id,'out','bank',8500000,'Yes Bank verified deposit (S184)' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-07-22'
     AND NOT EXISTS (SELECT 1 FROM cash_movement m WHERE m.day_entry_id=e.id AND m.reference='Yes Bank verified deposit (S184)');
INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference)
  SELECT e.id,'out','bank',8500000,'Yes Bank verified deposit (S184)' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-07-30'
     AND NOT EXISTS (SELECT 1 FROM cash_movement m WHERE m.day_entry_id=e.id AND m.reference='Yes Bank verified deposit (S184)');
INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference)
  SELECT e.id,'out','bank',7500000,'Yes Bank verified deposit (S184)' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-08-13'
     AND NOT EXISTS (SELECT 1 FROM cash_movement m WHERE m.day_entry_id=e.id AND m.reference='Yes Bank verified deposit (S184)');

-- 4. Darpan's salary advances as drawer expenses (NOT posted to Staff Ledger)
INSERT INTO day_expense (day_entry_id, amount_p, amount_known, category_text, note)
  SELECT e.id,1500000,1,'Salary advance - Darpan','S184: drawer outflow; tracked in salary system, NOT posted to Ledger' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-04-09'
     AND NOT EXISTS (SELECT 1 FROM day_expense x WHERE x.day_entry_id=e.id AND x.note LIKE 'S184:%' AND x.amount_p=1500000);
INSERT INTO day_expense (day_entry_id, amount_p, amount_known, category_text, note)
  SELECT e.id,1500000,1,'Salary advance - Darpan','S184: drawer outflow; tracked in salary system, NOT posted to Ledger' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-05-30'
     AND NOT EXISTS (SELECT 1 FROM day_expense x WHERE x.day_entry_id=e.id AND x.note LIKE 'S184:%' AND x.amount_p=1500000);
INSERT INTO day_expense (day_entry_id, amount_p, amount_known, category_text, note)
  SELECT e.id,1000000,1,'Salary advance - Darpan','S184: drawer outflow; tracked in salary system, NOT posted to Ledger' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-06-18'
     AND NOT EXISTS (SELECT 1 FROM day_expense x WHERE x.day_entry_id=e.id AND x.note LIKE 'S184:%' AND x.amount_p=1000000);

-- 5. the 2 mis-keyed procedure-medicine bills as noncash (billed, no cash)
INSERT INTO day_noncash_bill (day_entry_id, unit, bill_date, head, bill_no, amount_p, note)
  SELECT e.id,'medical','2026-04-20','procedure_medicine','S184-PMB-0420',25200,'S184: mis-keyed into the Deposit column' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-04-20'
     AND NOT EXISTS (SELECT 1 FROM day_noncash_bill n WHERE n.bill_no='S184-PMB-0420');
INSERT INTO day_noncash_bill (day_entry_id, unit, bill_date, head, bill_no, amount_p, note)
  SELECT e.id,'medical','2026-06-19','procedure_medicine','S184-PMB-0619',8500,'S184: mis-keyed into the Deposit column' FROM day_entry e
   WHERE e.unit='medical' AND e.business_date='2026-06-19'
     AND NOT EXISTS (SELECT 1 FROM day_noncash_bill n WHERE n.bill_no='S184-PMB-0619');

INSERT OR REPLACE INTO setting (key,value,note) VALUES
 ('migration.S184_cash_correction','applied',
  'S184: 31 sheet deposits -> 16 Yes Bank verified; 36 legacy adjustments removed (backed up in s184_removed_*); 40k advances as drawer expenses (not Ledger); 337 procedure-med noncash. Reversible.');

COMMIT;

-- =============================================================================
--  ROLLBACK  (run this block to undo; lossless):
--
--  BEGIN;
--  DELETE FROM cash_movement    WHERE reference='Yes Bank verified deposit (S184)';
--  DELETE FROM day_expense      WHERE note LIKE 'S184:%';
--  DELETE FROM day_noncash_bill WHERE bill_no LIKE 'S184-PMB-%';
--  INSERT INTO cash_movement   SELECT * FROM s184_removed_movements;
--  INSERT INTO cash_adjustment SELECT * FROM s184_removed_adjustments;
--  DROP TABLE s184_removed_movements;
--  DROP TABLE s184_removed_adjustments;
--  DELETE FROM setting WHERE key='migration.S184_cash_correction';
--  COMMIT;
-- =============================================================================
