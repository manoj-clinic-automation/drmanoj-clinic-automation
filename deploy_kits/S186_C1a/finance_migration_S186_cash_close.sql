-- =============================================================================
--  finance_migration_S186_cash_close.sql   ·  Session 186
--
--  PURPOSE  Two corrections the app cannot make itself, and one evidence record.
--
--  (A) F-112 — REMOVE A BANK DEPOSIT THAT NEVER HAPPENED.
--      S184_C1a booked "16 verified Yes Bank credits". The Yes Bank statement for
--      1 Jul - 17 Aug (supplied by the owner at S186) has its LAST transaction of
--      any kind on 30 July -- there are no August entries at all. The 13 Aug
--      Rs 75,000 deposit does not exist. Truth: 15 deposits, Rs 15,70,600.
--      S183 had flagged this exact row as unevidenced and it was booked anyway.
--
--  (B) D323 — PARK THE PRE-APRIL CASH-IN-HAND, ONCE, BY COUNT.
--      Owner's characterisation: cash never made to the bank, kept separate as
--      cash-in-hand carried from the previous financial year. Established by
--      physically clearing Darpan's drawer on 17 Aug 2026 -- which landed on
--      Rs 48,963 to the rupee (10,000 + 20,000 + 18,963) and thereby proved two
--      counter-person handovers no record had connected.
--
--        physical cash 17 Aug   = 0 (drawer) + 18,963 (owner) + 1,56,235 (Dr Bhawna)
--                               = 1,75,198
--        books once corrected   = 42,993 + 75,000 (A) - 30,000 (advances, entered
--                                 through the APP, not here)        =    87,993
--        PARKED                 = 1,75,198 - 87,993                 =    87,205
--
--      Booked as ONE cash_adjustment on the earliest medical day -- the schema's
--      own stated "ONLY way the running balance can ever move without a real
--      transaction. Visible, dated, reasoned, and it must be approved." It is NOT
--      spread across invented dates to make a chart look right (D323(a)).
--
--  (C) The 17 Aug physical count is recorded in cash_count, which the schema
--      keeps OUT of the computed ledger forever, on purpose. Evidence, not input.
--
--  (D) negative_cash exceptions are recomputed from v_cash_ledger, because
--      nothing else recreates them -- only the one-shot importer ever did. This
--      is the S184 lesson (C1a left the books right and the alarms stale).
--
--  NOT IN THIS MIGRATION, DELIBERATELY
--      * Darpan's 17 Aug advances (Rs 10,000 + Rs 20,000) -> ordinary drawer
--        expenses, entered through the app. A migration is for what the app
--        cannot do; using one for ordinary transactions hides them from the
--        maker-checker path.
--      * The Rs 18,963 handed to the owner is NOT booked as cash_out. Cash held
--        by Dr Bhawna has never been booked out either, so "cash in hand" in
--        these books means the WHOLE chain. Booking only this one handover out
--        would make the figure mean two different things on two dates.
--      * Nothing about the Staff Ledger. The Rs 70,000 of Darpan advances riding
--        on an unverified claim stays an open check, named in the Register.
--
--  MONEY MOVED  none in reality. This makes the RECORD match a bank statement
--  and a physical count. day_line (the sale money) is never touched.
--
--  IDEMPOTENT   every write is guarded on its S186 marker. Re-running is a no-op.
--  REVERSIBLE   rollback block at the foot; installer backs up the whole db too.
-- =============================================================================

BEGIN;

-- (A) -------------------------------------------------------- phantom deposit
CREATE TABLE IF NOT EXISTS s186_removed_movements AS SELECT * FROM cash_movement WHERE 0;

INSERT INTO s186_removed_movements
  SELECT m.* FROM cash_movement m JOIN day_entry e ON e.id = m.day_entry_id
   WHERE e.unit='medical' AND e.business_date='2026-08-13'
     AND m.direction='out' AND m.party='bank' AND m.amount_p=7500000
     AND NOT EXISTS (SELECT 1 FROM s186_removed_movements b WHERE b.id=m.id);

DELETE FROM cash_movement WHERE id IN (SELECT id FROM s186_removed_movements);

-- (B) ------------------------------------------------------------- the parked
INSERT INTO cash_adjustment
      (day_entry_id, amount_p, reason, source, status, explanation, approved_by, approved_at)
SELECT (SELECT id FROM day_entry WHERE unit='medical' ORDER BY business_date, id LIMIT 1),
       8720500,
       'S186: pre-April cash-in-hand carried from the previous financial year',
       'manual', 'approved',
       'Cash never made to the bank and kept separate as cash-in-hand of the previous '
       || 'financial year (owner, 17 Aug 2026). Established by PHYSICAL COUNT, not derived: '
       || 'Darpan drawer cleared to zero on 17 Aug (48,963 = 10,000 July-salary advance '
       || 'adjustment + 20,000 August-salary advance + 18,963 handed to the owner); cash with '
       || 'Dr Bhawna 1,56,235 (every handover since the last real bank deposit of 30 Jul, '
       || 'nothing banked, no returns); total counted 1,75,198 against corrected books 87,993. '
       || 'D323. Not spread across invented dates.',
       'manoj', '2026-08-17'
 WHERE NOT EXISTS (SELECT 1 FROM cash_adjustment WHERE reason LIKE 'S186:%');

-- (C) ------------------------------------------------- the count, as evidence
INSERT INTO cash_count (unit, business_date, counted_p, counted_by, counted_at, explanation)
VALUES ('medical','2026-08-17',17519800,'manoj','2026-08-17',
        'S186 physical position: Darpan drawer 0 (cleared) + owner 18,963 + Dr Bhawna 1,56,235. '
        || 'Dr Bhawna never banks; every Sanjeevni deposit is made by Darpan; the counter person '
        || 'hands cash direct to Dr Bhawna. D323.')
ON CONFLICT(unit, business_date) DO UPDATE SET
   counted_p=excluded.counted_p, counted_by=excluded.counted_by,
   counted_at=excluded.counted_at, explanation=excluded.explanation;

-- (D) --------------------------------------- recompute the negative_cash shout
CREATE TABLE IF NOT EXISTS s186_removed_exceptions AS SELECT * FROM recon_exception WHERE 0;
INSERT INTO s186_removed_exceptions
  SELECT * FROM recon_exception r
   WHERE r.unit='medical' AND r.kind='negative_cash'
     AND NOT EXISTS (SELECT 1 FROM s186_removed_exceptions b WHERE b.id=r.id);

UPDATE recon_exception
   SET status='resolved',
       resolution='Resolved by S186: the phantom 13 Aug deposit removed (F-112) and the pre-April '
                  || 'cash-in-hand parked by count (D323). Recomputed from the corrected ledger.',
       closed_by='S186_C1a', closed_at=datetime('now')
 WHERE unit='medical' AND kind='negative_cash' AND status IN ('open','acknowledged');

INSERT INTO recon_exception
   (unit, business_date, kind, expected_p, actual_p, diff_p, severity, status, detail, opened_at, shout_count)
SELECT 'medical', business_date, 'negative_cash', NULL, closing_p, closing_p, 'high', 'open',
       'cash in hand still negative after the S186 close — investigate; do not assume parking',
       datetime('now'), 0
  FROM v_cash_ledger WHERE unit='medical' AND closing_p < 0
ON CONFLICT(unit, business_date, kind) DO UPDATE SET
   status='open', expected_p=excluded.expected_p, actual_p=excluded.actual_p, diff_p=excluded.diff_p,
   severity='high', detail=excluded.detail, resolution=NULL, closed_by=NULL, closed_at=NULL,
   opened_at=datetime('now');

INSERT OR REPLACE INTO setting (key,value,note) VALUES
 ('migration.S186_cash_close','applied',
  'S186: phantom 13 Aug Rs 75,000 bank deposit removed (F-112, backed up in s186_removed_movements); '
  || 'Rs 87,205 pre-April cash-in-hand parked as one approved cash_adjustment (D323); 17 Aug physical '
  || 'count Rs 1,75,198 recorded in cash_count; negative_cash recomputed. Reversible.');

COMMIT;

-- =============================================================================
--  ROLLBACK (lossless):
--
--  BEGIN;
--  DELETE FROM cash_adjustment  WHERE reason LIKE 'S186:%';
--  DELETE FROM cash_count       WHERE unit='medical' AND business_date='2026-08-17';
--  INSERT INTO cash_movement    SELECT * FROM s186_removed_movements;
--  DELETE FROM recon_exception  WHERE unit='medical' AND kind='negative_cash';
--  INSERT INTO recon_exception  SELECT * FROM s186_removed_exceptions;
--  DROP TABLE s186_removed_movements;
--  DROP TABLE s186_removed_exceptions;
--  DELETE FROM setting WHERE key='migration.S186_cash_close';
--  COMMIT;
-- =============================================================================
