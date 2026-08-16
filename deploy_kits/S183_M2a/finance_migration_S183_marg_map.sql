-- =============================================================================
--  finance_migration_S183_marg_map.sql   ·  Session 183
--
--  PURPOSE
--    Turn ON the Marg pharmacy feed for the medical unit by giving the
--    marg_export adapter the column map it has been missing, and activating
--    the source. Until now (medical, marg_export) was seeded active=0 with
--    ZERO column-map rows, so the adapter would read zero rows and still
--    report success — the silent-zero-rows trap the backfill driver refuses on.
--
--  WHAT IT CHANGES  (all additive · non-destructive · reversible)
--    1. INSERTs 7 rows into ingest_column_map for the (medical, marg_export)
--       source, mapping our fields onto the header marg_report.py actually
--       emits: bill_date · bill_no · clinic_id · patient_name · description ·
--       amount · mode.
--    2. UPDATEs that ingest_source to active=1 and sets its config_json
--       (comma-delimited, utf-8).
--    3. Records a marker row in `setting`.
--
--  WHAT IT DOES NOT CHANGE
--    No table created, altered, rebuilt or dropped. No sale_item, day_line,
--    day_entry or patient row is read, written or deleted. This migration only
--    configures how a future ingest reads a file; it moves no money.
--
--  WHY ONLY 7 FIELDS, NOT 8
--    marg_report.py emits phone_last4 too, but ingest_column_map.our_field
--    carries CHECK (our_field IN ('bill_no','bill_date','clinic_id',
--    'patient_name','description','amount','mode','discount','tax')) — there is
--    no phone field, by design: patient_ref stores phone_last4 elsewhere and
--    the revenue adapter never reads a phone. A 'phone_last4' row would be
--    rejected by the CHECK. adapter_csv reads exactly these 7, so the map is
--    complete for what the code consumes.
--
--  WHY NO TRANSFORMS
--    marg_report.py already emits bill_date as ISO 'YYYY-MM-DD' and amount as a
--    plain signed decimal (a credit note stays negative; finance_ingest turns
--    it into a magnitude + a '_return' service per D314). So transform is NULL
--    on every row — nothing to convert.
--
--  IDEMPOTENT
--    INSERT OR REPLACE on the map (UNIQUE(source_id, our_field)) and a plain
--    UPDATE mean re-running changes nothing after the first apply.
--
--  ROLLBACK  (kept verbatim at the foot of this file)
--    DELETE the 7 map rows, set active back to 0, clear config_json, drop the
--    marker. No data is touched, so rollback is lossless.
--
--  APPLY  (on the box, after a backup)
--    /usr/bin/python3 -c "import sqlite3;c=sqlite3.connect('/root/finance/finance.db');\
--      c.executescript(open('finance_migration_S183_marg_map.sql').read());c.commit()"
-- =============================================================================

BEGIN;

-- 1. the column map — 7 rows the adapter reads, mapped to marg_report's header
INSERT OR REPLACE INTO ingest_column_map (source_id, our_field, their_column, transform, required)
SELECT s.id, m.our_field, m.their_column, NULL, m.required
FROM ingest_source s
JOIN (
    SELECT 'bill_no'      AS our_field, 'bill_no'      AS their_column, 0 AS required
    UNION ALL SELECT 'bill_date',     'bill_date',     1
    UNION ALL SELECT 'clinic_id',     'clinic_id',     0
    UNION ALL SELECT 'patient_name',  'patient_name',  0
    UNION ALL SELECT 'description',   'description',   0
    UNION ALL SELECT 'amount',        'amount',        1
    UNION ALL SELECT 'mode',          'mode',          0
) m
WHERE s.unit = 'medical' AND s.adapter = 'marg_export';

-- 2. activate the source and set how the CSV is read
UPDATE ingest_source
   SET active = 1,
       config_json = '{"delimiter": ",", "encoding": "utf-8", "skip_rows": 0}'
 WHERE unit = 'medical' AND adapter = 'marg_export';

-- 3. marker
INSERT OR REPLACE INTO setting (key, value, note) VALUES
 ('migration.S183_marg_map', 'applied',
  'S183: medical marg_export column map (7 fields) + source activated. Additive, reversible.');

COMMIT;

-- =============================================================================
--  ROLLBACK — run this block instead to undo (lossless; touches no money):
--
--  BEGIN;
--  DELETE FROM ingest_column_map
--   WHERE source_id = (SELECT id FROM ingest_source
--                       WHERE unit='medical' AND adapter='marg_export');
--  UPDATE ingest_source SET active = 0, config_json = NULL
--   WHERE unit='medical' AND adapter='marg_export';
--  DELETE FROM setting WHERE key = 'migration.S183_marg_map';
--  COMMIT;
-- =============================================================================
