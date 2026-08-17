-- =============================================================================
--  finance_migration_S184_C2a_exceptions.sql   ·  Session 184
--
--  PURPOSE  After S184_C1a corrected the medical cash books, the recon_exception
--  table still held the ORIGINAL import-time shouts, now stale:
--    * 36 carry_forward_break — the sheet's Old-Balance drift; the adjustments
--      that caused it were removed by C1a, and the opening is now computed, so
--      these breaks no longer exist. There is NO live detector that recreates
--      them (only the one-shot importer did), so they must be closed here.
--    * 7 negative_cash — computed on the OLD buggy chain (e.g. 13 Aug -30,056,
--      now +27,654). Stale. The days that are genuinely negative now are the
--      cash-PARKING windows, which the owner chose to keep as honest exceptions.
--
--  WHAT IT DOES  (one transaction; touched rows backed up first)
--    1. Back up every medical carry_forward_break + negative_cash row.
--    2. Resolve all open carry_forward_break (obsolete after C1a).
--    3. Resolve all stale negative_cash.
--    4. Recompute negative_cash straight from v_cash_ledger (the live corrected
--       ledger — D321, the box computes it, not us), UPSERTing one row per day
--       whose closing is still < 0, with a detail that names the cause: cash
--       parked with Dr Bhawna ahead of a bank trip, to verify from her copy.
--    5. line_sum_vs_day_total (F-104) and missing_day are left UNTOUCHED.
--
--  IDEMPOTENT  re-running resolves-then-recomputes the same set; UPSERT on the
--  UNIQUE(unit,business_date,kind) key. REVERSIBLE  rollback block at the foot,
--  plus the installer's whole-db backup.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS s184c2_removed_exceptions AS SELECT * FROM recon_exception WHERE 0;
INSERT INTO s184c2_removed_exceptions
  SELECT * FROM recon_exception r
   WHERE r.unit='medical' AND r.kind IN ('carry_forward_break','negative_cash')
     AND NOT EXISTS (SELECT 1 FROM s184c2_removed_exceptions b WHERE b.id=r.id);

UPDATE recon_exception
   SET status='resolved',
       resolution='Resolved by S184: sheet deposits replaced with 16 Yes Bank verified, legacy carry-forward adjustments removed; opening is now computed, so this break no longer exists.',
       closed_by='S184_C2a', closed_at=datetime('now')
 WHERE unit='medical' AND kind='carry_forward_break' AND status IN ('open','acknowledged');

UPDATE recon_exception
   SET status='resolved',
       resolution='Superseded by S184: recomputed on the corrected ledger.',
       closed_by='S184_C2a', closed_at=datetime('now')
 WHERE unit='medical' AND kind='negative_cash' AND status IN ('open','acknowledged');

INSERT INTO recon_exception
   (unit, business_date, kind, expected_p, actual_p, diff_p, severity, status, detail, opened_at, shout_count)
SELECT 'medical', business_date, 'negative_cash', NULL, closing_p, closing_p, 'high', 'open',
       'cash in hand negative — cash parked with Dr Bhawna ahead of a bank trip (S184; verify from her copy)',
       datetime('now'), 0
  FROM v_cash_ledger WHERE unit='medical' AND closing_p < 0
ON CONFLICT(unit, business_date, kind) DO UPDATE SET
   status='open', expected_p=excluded.expected_p, actual_p=excluded.actual_p, diff_p=excluded.diff_p,
   severity='high', detail=excluded.detail, resolution=NULL, closed_by=NULL, closed_at=NULL,
   opened_at=datetime('now');

INSERT OR REPLACE INTO setting (key,value,note) VALUES
 ('migration.S184_C2a_exceptions','applied',
  'S184: carry_forward_break + stale negative_cash resolved; negative_cash recomputed from v_cash_ledger (parking windows). Reversible via s184c2_removed_exceptions.');

COMMIT;

-- =============================================================================
--  ROLLBACK (lossless):
--  BEGIN;
--  DELETE FROM recon_exception WHERE unit='medical' AND kind IN ('carry_forward_break','negative_cash');
--  INSERT INTO recon_exception SELECT * FROM s184c2_removed_exceptions;
--  DROP TABLE s184c2_removed_exceptions;
--  DELETE FROM setting WHERE key='migration.S184_C2a_exceptions';
--  COMMIT;
-- =============================================================================
