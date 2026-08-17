-- =============================================================================
--  finance_migration_S186_walkin.sql   ·  Session 186   ·  F-104
--
--  PURPOSE  Legacy Marg bills that carry no clinic ID were parked in
--  sale_item_review by the S183 backfill. They are real sales with a real
--  amount and no patient name -- so the day's money looks unattributed and 118
--  days shout line_sum_vs_day_total, plus ~2,062 rows sit in a review queue
--  nobody can ever resolve, because the name does not exist to be found.
--
--  The owner's ruling (S183): reclassify them to WALK-IN. The schema already
--  reserves that bucket -- patient_ref.clinic_id 'WALK-IN', seeded at S179 with
--  the note "lines land here rather than being dropped or guessed". This uses
--  it for exactly what it was reserved for.
--
--  SURVEYED FIRST, ON THE BOX (the S184_S1a discipline):
--     open review rows          2,062   Rs 17,44,055
--     gap across flagged days     118 days  Rs 17,36,833
--     per flagged day the two match TO THE RUPEE
--  The Rs 7,222 difference is review sitting on days whose gap was under the
--  Rs 100 tolerance and so were never flagged. Named, not hand-waved.
--
--  WHAT IT DOES  (one transaction; everything backed up first)
--    1. Copy every open medical sale_item_review row to s186_f104_reviews.
--    2. Insert one sale_item per row, attributed to WALK-IN, keeping the
--       original ingest_batch_id so lineage survives, source='manual' because
--       this is a HUMAN RULING and not an OCR reading, and source_ref naming
--       the review row it came from.
--    3. Mark those review rows resolved.
--    4. Recompute line_sum_vs_day_total from v_day_attribution -- nothing else
--       recreates it (only the one-shot importer ever did), which is the S184
--       lesson: C1a left the books right and the alarms stale.
--
--  MONEY  none. day_line is never touched. sale_item is ATTRIBUTION and the
--  schema says so in terms: "attribution improving later must never be able to
--  move the books." The day totals and the bank settle the money; this only
--  puts a name against money already counted.
--
--  IDEMPOTENT  guarded on the S186-F104 source_ref. REVERSIBLE  rollback block
--  at the foot; the installer backs up the whole database first.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS s186_f104_reviews AS SELECT * FROM sale_item_review WHERE 0;

INSERT INTO s186_f104_reviews
  SELECT r.* FROM sale_item_review r
    JOIN day_entry e ON e.id = r.day_entry_id
   WHERE e.unit='medical' AND r.status='open'
     AND NOT EXISTS (SELECT 1 FROM s186_f104_reviews b WHERE b.id = r.id);

INSERT INTO sale_item (day_entry_id, ingest_batch_id, unit, patient_ref_id, service,
                       description, amount_p, mode, source, source_ref, confidence,
                       verified_by, verified_at)
  SELECT r.day_entry_id, r.ingest_batch_id, 'medical',
         (SELECT id FROM patient_ref WHERE clinic_id='WALK-IN'),
         'pharmacy',
         COALESCE(NULLIF(TRIM(r.raw_text),''), 'legacy bill, no clinic ID'),
         r.amount_p, NULL, 'manual',
         'S186-F104-' || r.id, NULL, 'S186_W1a', datetime('now')
    FROM sale_item_review r
    JOIN day_entry e ON e.id = r.day_entry_id
   WHERE e.unit='medical' AND r.status='open' AND COALESCE(r.amount_p,0) > 0
     AND NOT EXISTS (SELECT 1 FROM sale_item s WHERE s.source_ref = 'S186-F104-' || r.id);

UPDATE sale_item_review
   SET status='resolved', resolved_by='S186_W1a', resolved_at=datetime('now')
 WHERE status='open' AND COALESCE(amount_p,0) > 0
   AND day_entry_id IN (SELECT id FROM day_entry WHERE unit='medical');

-- ---- recompute the shout from the live view, do not assume it is now clean --
CREATE TABLE IF NOT EXISTS s186_f104_exceptions AS SELECT * FROM recon_exception WHERE 0;
INSERT INTO s186_f104_exceptions
  SELECT * FROM recon_exception r
   WHERE r.unit='medical' AND r.kind='line_sum_vs_day_total'
     AND NOT EXISTS (SELECT 1 FROM s186_f104_exceptions b WHERE b.id = r.id);

UPDATE recon_exception
   SET status='resolved',
       resolution='S186 F-104: legacy no-ID bills reclassified to WALK-IN; recomputed from v_day_attribution.',
       closed_by='S186_W1a', closed_at=datetime('now')
 WHERE unit='medical' AND kind='line_sum_vs_day_total' AND status IN ('open','acknowledged');

INSERT INTO recon_exception
   (unit, business_date, kind, expected_p, actual_p, diff_p, severity, status, detail,
    opened_at, shout_count)
SELECT 'medical', business_date, 'line_sum_vs_day_total', day_total_p, attributed_p,
       day_total_p - attributed_p, 'medium', 'open',
       'still unattributed after the WALK-IN reclass — this one is NOT legacy no-ID; look at it',
       datetime('now'), 0
  FROM v_day_attribution
 WHERE unit='medical'
   AND ABS(day_total_p - attributed_p) >
       CAST(COALESCE((SELECT value FROM setting WHERE key='ingest.attribution_tolerance_p'),
                     '10000') AS INTEGER)
ON CONFLICT(unit, business_date, kind) DO UPDATE SET
   expected_p=excluded.expected_p, actual_p=excluded.actual_p, diff_p=excluded.diff_p,
   severity='medium', status='open', detail=excluded.detail,
   resolution=NULL, closed_by=NULL, closed_at=NULL, opened_at=datetime('now');

INSERT OR REPLACE INTO setting (key,value,note) VALUES
 ('migration.S186_walkin','applied',
  'S186 F-104: open medical sale_item_review rows reclassified to the reserved WALK-IN patient '
  || '(originals in s186_f104_reviews); line_sum_vs_day_total recomputed from v_day_attribution '
  || '(prior rows in s186_f104_exceptions). No money touched — day_line untouched. Reversible.');

COMMIT;

-- =============================================================================
--  ROLLBACK (lossless):
--  BEGIN;
--  DELETE FROM sale_item WHERE source_ref LIKE 'S186-F104-%';
--  DELETE FROM sale_item_review WHERE id IN (SELECT id FROM s186_f104_reviews);
--  INSERT INTO sale_item_review SELECT * FROM s186_f104_reviews;
--  DELETE FROM recon_exception WHERE unit='medical' AND kind='line_sum_vs_day_total';
--  INSERT INTO recon_exception SELECT * FROM s186_f104_exceptions;
--  DROP TABLE s186_f104_reviews;
--  DROP TABLE s186_f104_exceptions;
--  DELETE FROM setting WHERE key='migration.S186_walkin';
--  COMMIT;
-- =============================================================================
