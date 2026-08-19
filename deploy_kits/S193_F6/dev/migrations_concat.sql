-- ===== deploy_kits/S182_C1e/finance_migration_S182_clinic.sql =====
-- =============================================================================
--  finance_migration_S182_clinic.sql   ·  Session 182 · kit S182_C1a
--  Contract: S181_Clinic_Module_Build_Contract_C1 (+ addendum)
--
--  PURPOSE
--    Prepare the shared store for the CLINIC unit's daily entry (C1 slice 1).
--
--  WHAT IT CHANGES
--    (1) day_line gains two nullable columns:
--          line_kind — 'grid' (one of the six clinic cells) or 'stray'
--                      (an out-of-grid addition). NULL on every existing row,
--                      and medical keeps writing NULL. No CHECK, so a later
--                      kind is a value, not a schema change.
--          note      — the stray line's REQUIRED reason.
--        Purely additive; no view, no constraint, no existing row changes.
--    (2) attachment learns two clinic evidence categories, 'opd_register' and
--        'xray_proc_register'. doc_type is guarded by a CHECK that SQLite
--        cannot extend in place, so THIS ONE TABLE IS REBUILT
--        (create → copy → drop → rename → re-index), ids preserved.
--        S180 refused a rebuild for sale_item because a view could carry that
--        change; here no view can add a CHECK value — there is no lighter
--        mechanism, and inventing a parallel evidence table was ruled out by
--        the contract ("reuse the existing attachment mechanism"). Rows are
--        copied verbatim; every referencing table (ocr_extract, archive_item,
--        cash_movement.slip_attachment_id) keys on attachment.id, which the
--        copy preserves. Run with the service STOPPED (install_c1a.sh does).
--    (3) Clinic tile wording as settings (the tile.maker_title pattern,
--        unit-prefixed), plus defensive INSERT OR IGNOREs for the clinic
--        business_unit row and the clinic roster the schema already seeds.
--    (4) A marker row, setting 'migration.S182_clinic' — install_c1a.sh
--        applies this file only when the marker is absent, which is what makes
--        the install idempotent.
--
--  RE-RUN BEHAVIOUR
--    The installer skips this file when the marker exists. Run twice by hand
--    anyway: the two ALTERs fail harmlessly with 'duplicate column name' (the
--    sqlite3 shell reports and continues); everything else is IF NOT EXISTS /
--    INSERT OR IGNORE / copy-idempotent.
--
--  APPLY
--    sqlite3 finance.db < finance_migration_S182_clinic.sql
--    then:  python3 finance_app.py --selftest   (runs on a throwaway copy)
--
--  ROLLBACK — at the foot, commented, per the S180 pattern.
-- =============================================================================

PRAGMA foreign_keys = OFF;

-- (1) stray provenance on day_line — additive, nullable, no defaults
ALTER TABLE day_line ADD COLUMN line_kind TEXT;
ALTER TABLE day_line ADD COLUMN note TEXT;

BEGIN;

-- (2) attachment rebuild: same shape, doc_type CHECK extended by two values
CREATE TABLE IF NOT EXISTS attachment_s182 (
    id            INTEGER PRIMARY KEY,
    day_entry_id  INTEGER REFERENCES day_entry(id) ON DELETE CASCADE,
    doc_type      TEXT NOT NULL
                  CHECK (doc_type IN ('sale_report','manual_copy','orthotics_copy',
                                      'deposit_slip','legacy_medicine_copy','legacy_implant_copy',
                                      'opd_register','xray_proc_register')),
    path          TEXT,
    external_url  TEXT,
    sha256        TEXT,
    bytes         INTEGER,
    uploaded_by   TEXT,
    uploaded_at   TEXT
);
INSERT INTO attachment_s182 (id, day_entry_id, doc_type, path, external_url,
                             sha256, bytes, uploaded_by, uploaded_at)
    SELECT id, day_entry_id, doc_type, path, external_url,
           sha256, bytes, uploaded_by, uploaded_at
    FROM attachment;
DROP TABLE attachment;
ALTER TABLE attachment_s182 RENAME TO attachment;
CREATE INDEX IF NOT EXISTS ix_attachment_entry ON attachment(day_entry_id);

-- (3) clinic seeds — every one a no-op where the schema seed already ran
INSERT OR IGNORE INTO business_unit (code, name, merchant_id, open_sunday) VALUES
    ('clinic', 'Dr Manoj Agarwal Clinic', '100000000306941', 1);
INSERT OR IGNORE INTO unit_role (unit, username, role, note) VALUES
    ('clinic', 'reception', 'maker',   'reception files the clinic day'),
    ('clinic', 'manoj',     'checker', 'doctor approves clinic'),
    ('clinic', 'bhawna',    'checker', 'Dr Bhawna also checks clinic (S179)');
INSERT OR IGNORE INTO setting (key, value, note) VALUES
    ('clinic.tile.maker_title', 'Daily Collection',
     'Portal tile label for the clinic reception. Names the job, not the department (S179).'),
    ('clinic.tile.maker_subtitle', 'आज की OPD / X-Ray / Procedure entry',
     'One line under the clinic maker tile.'),
    ('clinic.tile.checker_title', 'Clinic', 'Portal tile label for the doctors.'),
    ('clinic.tile.checker_subtitle', 'Review and approve the clinic day',
     'One line under the clinic checker tile.');

-- (4) the idempotency marker install_c1a.sh checks before applying this file
INSERT OR REPLACE INTO setting (key, value, note) VALUES
    ('migration.S182_clinic', 'applied',
     'Marker: finance_migration_S182_clinic.sql has been applied. install_c1a.sh skips the file when this row exists.');

COMMIT;

PRAGMA foreign_keys = ON;
PRAGMA foreign_key_check;

-- =============================================================================
--  ROLLBACK — paste and run only if S182_C1a has to be undone.
--  Order matters: clinic evidence rows must go before the CHECK narrows again.
--  (Clinic day_entry/day_line rows, if any were filed, survive harmlessly —
--  they simply have no entry screen once the app binary is rolled back.)
-- =============================================================================
--
-- PRAGMA foreign_keys = OFF;
-- BEGIN;
-- DELETE FROM attachment WHERE doc_type IN ('opd_register','xray_proc_register');
-- CREATE TABLE IF NOT EXISTS attachment_rollback (
--     id            INTEGER PRIMARY KEY,
--     day_entry_id  INTEGER REFERENCES day_entry(id) ON DELETE CASCADE,
--     doc_type      TEXT NOT NULL
--                   CHECK (doc_type IN ('sale_report','manual_copy','orthotics_copy',
--                                       'deposit_slip','legacy_medicine_copy','legacy_implant_copy')),
--     path          TEXT,
--     external_url  TEXT,
--     sha256        TEXT,
--     bytes         INTEGER,
--     uploaded_by   TEXT,
--     uploaded_at   TEXT
-- );
-- INSERT INTO attachment_rollback SELECT id, day_entry_id, doc_type, path,
--     external_url, sha256, bytes, uploaded_by, uploaded_at FROM attachment;
-- DROP TABLE attachment;
-- ALTER TABLE attachment_rollback RENAME TO attachment;
-- CREATE INDEX IF NOT EXISTS ix_attachment_entry ON attachment(day_entry_id);
-- -- day_line: the two added columns are nullable and ignored by medical; they
-- -- may simply stay. To remove them outright (needs SQLite >= 3.35):
-- -- ALTER TABLE day_line DROP COLUMN line_kind;
-- -- ALTER TABLE day_line DROP COLUMN note;
-- DELETE FROM setting WHERE key IN
--     ('clinic.tile.maker_title','clinic.tile.maker_subtitle',
--      'clinic.tile.checker_title','clinic.tile.checker_subtitle',
--      'migration.S182_clinic');
-- COMMIT;
-- PRAGMA foreign_keys = ON;
-- PRAGMA foreign_key_check;

-- (5) S182_C1e: the clinic maker seat pointed at 'reception', a placeholder
-- with no portal login. Seed the REAL people (owner-directed, S182): Shavez
-- (main assistant), Alisha and Shivani as clinic makers. Checkers remain
-- manoj + bhawna alone; none of these three can self-approve by construction.
-- Reversible: UPDATE unit_role SET active=0 WHERE unit='clinic' AND username='<name>';
INSERT OR IGNORE INTO unit_role (unit, username, role, note) VALUES
    ('clinic', 'shavez',  'maker', 'main assistant — files the clinic day (S182)'),
    ('clinic', 'alisha',  'maker', 'reception — files the clinic day (S182)'),
    ('clinic', 'shivani', 'maker', 'reception — files the clinic day (S182)');
;
-- ===== deploy_kits/S182_C2a/finance_migration_S182_c2.sql =====
-- =============================================================================
--  finance_migration_S182_c2.sql   ·  Session 182 · kit S182_C2
--  Owner-directed redesign of the clinic entry (simple English, four tender
--  totals, expenses, two-stage approval, tracker feed).
--
--  EVERYTHING HERE IS ADDITIVE. No table is rebuilt (the C1a attachment
--  rebuild was tolerated once; not again — hard constraint, S182):
--
--    (1) clinic_line_side — a SIDE TABLE for tender rows day_line's CHECK
--        cannot hold. day_line.mode is CHECK-constrained to
--        ('cash','upi','card','credit'); the owner's new 'razorpay' rail is
--        not in that list, and extending a CHECK in SQLite means a rebuild.
--        So razorpay amounts (the day's Razorpay total and any razorpay
--        extra/stray line) live here, keyed to the same day_entry. They never
--        touch the cash drawer (v_day_cash never sees them — correct, they
--        are not cash) and never enter the UPI reconcile (which sums
--        mode='upi' day_line rows only). Clinic read routes join this table
--        so day/month/tile revenue stays whole.
--    (2) clinic_verification — the middle-approval record (owner: "shavez can
--        be a middle approver, me being final checker"). One row per day
--        entry, written when a clinic checker taps VERIFY. Final approval is
--        gated on it in code (or on an explicit skip, which is recorded).
--    (3) tracker_day — the Docterz/tracker day summary pushed by the clinic
--        Gmail account's Apps Script (VPS_Push_TrackerDay.gs). Payload stored
--        verbatim, one row per (unit, business_date), upserted. Attribution
--        context only: the spine READS it, never posts from it (D313).
--        Lines carry clinic ids + amounts — no names, no phones (the feed is
--        privacy-filtered at the sender AND refused at the receiver).
--    (4) Data rows: shavez gains a clinic 'checker' seat (his maker row
--        stays — he still files days; self-verify is barred in code, D272);
--        'clinic.final_checker' names WHO gives final approval as DATA, not
--        code (today: manoj); the maker tile subtitle stops naming the
--        retired six-cell scheme.
--    (5) The marker row, setting 'migration.S182_c2' — the installer applies
--        this file only when the marker is absent.
--
--  RE-RUN BEHAVIOUR
--    Safe to run twice: everything is IF NOT EXISTS / INSERT OR IGNORE /
--    INSERT OR REPLACE. clinic.final_checker is INSERT OR IGNORE so a later
--    hand-change by the owner is never clobbered by a re-run.
--
--  APPLY (the VPS has no sqlite3 CLI — C1b lesson; use the venv python):
--    /root/wa/venv/bin/python3 - <<'PY'
--    import sqlite3
--    con = sqlite3.connect('finance.db')
--    con.executescript(open('finance_migration_S182_c2.sql').read())
--    con.close()
--    PY
--    then:  python3 finance_app.py --selftest   (runs on a throwaway copy)
--
--  ROLLBACK — at the foot, commented, per the S180 pattern.
-- =============================================================================

BEGIN;

-- (1) tenders day_line's CHECK cannot hold (today: razorpay)
CREATE TABLE IF NOT EXISTS clinic_line_side (
    id            INTEGER PRIMARY KEY,
    day_entry_id  INTEGER NOT NULL REFERENCES day_entry(id) ON DELETE CASCADE,
    tender        TEXT NOT NULL,             -- 'razorpay' today; a later rail is a value
    amount_p      INTEGER NOT NULL CHECK (amount_p >= 0),
    line_kind     TEXT,                      -- 'tender' (a day total) | 'stray' (an extra line)
    note          TEXT                       -- the stray line's REQUIRED narration
);
CREATE INDEX IF NOT EXISTS ix_clinic_line_side_entry ON clinic_line_side(day_entry_id);

-- (2) the middle approval (VERIFY) — one per day entry
CREATE TABLE IF NOT EXISTS clinic_verification (
    id            INTEGER PRIMARY KEY,
    day_entry_id  INTEGER NOT NULL UNIQUE REFERENCES day_entry(id) ON DELETE CASCADE,
    verified_by   TEXT NOT NULL,
    verified_at   TEXT NOT NULL,
    note          TEXT
);

-- (3) the Docterz/tracker day feed — payload verbatim, upserted per day
CREATE TABLE IF NOT EXISTS tracker_day (
    id            INTEGER PRIMARY KEY,
    unit          TEXT NOT NULL REFERENCES business_unit(code),
    business_date TEXT NOT NULL,
    payload_json  TEXT NOT NULL,
    received_at   TEXT NOT NULL,
    UNIQUE (unit, business_date)
);

-- (4) data: the middle approver's seat, the final checker AS DATA, tile text
INSERT OR IGNORE INTO unit_role (unit, username, role, note) VALUES
    ('clinic', 'shavez', 'checker',
     'middle approver — VERIFIES the clinic day before the final checker (S182 C2). His maker row stays; self-verify is barred in code (D272).');
INSERT OR IGNORE INTO setting (key, value, note) VALUES
    ('clinic.final_checker', 'manoj',
     'WHO gives the clinic day its final approval. Data, not code (S182 C2): change this row, not the app. Every other clinic checker can only VERIFY.');
INSERT OR REPLACE INTO setting (key, value, note) VALUES
    ('clinic.tile.maker_subtitle', 'Clinic Entry Form — cash, UPI, card, Razorpay',
     'One line under the clinic maker tile. Updated at S182 C2: the six-cell wording was retired with the six cells.');

-- (5) the idempotency marker the installer checks before applying this file
INSERT OR REPLACE INTO setting (key, value, note) VALUES
    ('migration.S182_c2', 'applied',
     'Marker: finance_migration_S182_c2.sql has been applied. The installer skips the file when this row exists.');

COMMIT;

PRAGMA foreign_key_check;

-- =============================================================================
--  ROLLBACK — paste and run only if S182_C2 has to be undone.
--  All three tables are new and nothing else references them, so rollback is
--  plain drops — no rebuild anywhere. Clinic day rows filed through the C2
--  entry survive (their day_line tender rows are ordinary day_line rows);
--  only their razorpay amounts vanish with clinic_line_side, which is the
--  honest consequence of undoing the rail.
-- =============================================================================
--
-- BEGIN;
-- DROP TABLE IF EXISTS clinic_line_side;
-- DROP TABLE IF EXISTS clinic_verification;
-- DROP TABLE IF EXISTS tracker_day;
-- UPDATE unit_role SET active=0 WHERE unit='clinic' AND username='shavez' AND role='checker';
-- DELETE FROM setting WHERE key IN ('clinic.final_checker', 'migration.S182_c2');
-- INSERT OR REPLACE INTO setting (key, value, note) VALUES
--     ('clinic.tile.maker_subtitle', 'आज की OPD / X-Ray / Procedure entry',
--      'One line under the clinic maker tile.');
-- COMMIT;
-- PRAGMA foreign_key_check;
;
-- ===== deploy_kits/S183_M2a/finance_migration_S183_marg_map.sql =====
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
;
-- ===== deploy_kits/S184_C1a/finance_migration_S184_cash_correction.sql =====
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
;
-- ===== deploy_kits/S184_C2a/finance_migration_S184_C2a_exceptions.sql =====
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
;
-- ===== deploy_kits/S186_C1a/finance_migration_S186_cash_close.sql =====
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
;
-- ===== deploy_kits/S186_R1a/finance_migration_S186_reserve_yesbank.sql =====
-- =============================================================================
--  finance_migration_S186_reserve_yesbank.sql   ·  Session 186
--
--  PURPOSE  The data layer for three upgrades, added WITHOUT touching a single
--  existing table, view, row or index. Nothing here is read by the running app
--  until its kit lands, so this migration cannot change what anyone sees today.
--
--    1. bank_statement_line   — every line of a Yes Bank statement, so a booked
--       cash deposit can be matched against the bank the way UPI already is
--       against ICICI. THIS IS THE F-103 GAP, and the absence of it is exactly
--       how F-112 happened: a Rs 75,000 deposit that never occurred sat in the
--       live books for a session because nothing compared it to a statement.
--
--    2. counter_person        — the registry the reserve model needs (D323(d)).
--       Seeded with what S186 established from the owner: Darpan (drawer) and
--       Vinay Saxena (counter person, hands cash DIRECT to Dr Bhawna).
--
--    3. cash_custody_event    — who is holding what, and since when. The sheet
--       that took five sessions to reconcile had three columns and none of them
--       could say "she banked it" or "carried to next month". This can.
--
--  DESIGN NOTE — why a new table and not a wider cash_movement.
--  cash_movement.party is a CHECK constraint ('bank','dr_manoj','dr_bhawna',
--  'other'). Widening it in SQLite means rebuilding the table, and rebuilding a
--  live financial table to add an enum value is a poor trade. cash_custody_event
--  sits ALONGSIDE it and references it, so the money story stays in one place
--  and the custody story is additive.
--
--  MONEY  none moved, none read. day_line, cash_movement, cash_adjustment,
--  day_expense and every view are untouched.
--  IDEMPOTENT  CREATE TABLE IF NOT EXISTS + guarded seeds. REVERSIBLE  the
--  rollback block drops exactly what this created and nothing else.
-- =============================================================================

BEGIN;

-- 1 ------------------------------------------------- the bank's own statement
CREATE TABLE IF NOT EXISTS bank_statement_line (
    id              INTEGER PRIMARY KEY,
    account_ref     TEXT NOT NULL,            -- masked/last-4 account label
    txn_date        TEXT NOT NULL,            -- ISO
    value_date      TEXT,
    description     TEXT NOT NULL,
    reference       TEXT,                     -- bank reference number
    withdrawal_p    INTEGER NOT NULL DEFAULT 0,
    deposit_p       INTEGER NOT NULL DEFAULT 0,
    balance_p       INTEGER,
    is_cash_deposit INTEGER NOT NULL DEFAULT 0,   -- 1 = 'CASH DEP-SELF-...'
    source_file     TEXT,
    sha256          TEXT,
    ingested_at     TEXT,
    UNIQUE (account_ref, txn_date, reference, deposit_p, withdrawal_p)
);
CREATE INDEX IF NOT EXISTS ix_bsl_cash  ON bank_statement_line(is_cash_deposit, txn_date);
CREATE INDEX IF NOT EXISTS ix_bsl_date  ON bank_statement_line(txn_date);

-- Which statement periods we actually hold. A reconciler that does not know
-- what it has NOT seen will call an unevidenced deposit "fine" (F-112's lesson,
-- and F-99's blind-spot rule one domain over).
CREATE TABLE IF NOT EXISTS bank_statement_period (
    id           INTEGER PRIMARY KEY,
    account_ref  TEXT NOT NULL,
    period_from  TEXT NOT NULL,
    period_to    TEXT NOT NULL,
    opening_p    INTEGER,
    closing_p    INTEGER,
    source_file  TEXT,
    sha256       TEXT,
    ingested_at  TEXT,
    UNIQUE (account_ref, period_from, period_to)
);

-- 2 --------------------------------------------------- the counter-person set
CREATE TABLE IF NOT EXISTS counter_person (
    id            INTEGER PRIMARY KEY,
    unit          TEXT NOT NULL REFERENCES business_unit(code),
    name          TEXT NOT NULL,
    hindi_name    TEXT,
    role_kind     TEXT NOT NULL DEFAULT 'counter'
                  CHECK (role_kind IN ('counter','drawer','custodian')),
    hands_cash_to TEXT,                       -- free text: 'dr_bhawna' | 'drawer'
    active        INTEGER NOT NULL DEFAULT 1,
    note          TEXT,
    UNIQUE (unit, name)
);

INSERT INTO counter_person (unit,name,hindi_name,role_kind,hands_cash_to,active,note)
SELECT 'medical','Darpan','दर्पण','drawer','bank',1,
       'S186: keeps the drawer; makes EVERY Sanjeevni bank deposit; his copy resets on the 1st'
 WHERE NOT EXISTS (SELECT 1 FROM counter_person WHERE unit='medical' AND name='Darpan');

INSERT INTO counter_person (unit,name,hindi_name,role_kind,hands_cash_to,active,note)
SELECT 'medical','Vinay Saxena','विनय सक्सेना','counter','dr_bhawna',1,
       'S186: counter person; hands cash DIRECT to Dr Bhawna, bypassing the drawer'
 WHERE NOT EXISTS (SELECT 1 FROM counter_person WHERE unit='medical' AND name='Vinay Saxena');

INSERT INTO counter_person (unit,name,hindi_name,role_kind,hands_cash_to,active,note)
SELECT 'medical','Dr Bhawna','डॉ भावना','custodian','drawer',1,
       'S186: holds the reserve. NEVER banks — every deposit is made by Darpan (owner, 17 Aug 2026)'
 WHERE NOT EXISTS (SELECT 1 FROM counter_person WHERE unit='medical' AND name='Dr Bhawna');

-- 3 ------------------------------------------------------- custody, explicitly
CREATE TABLE IF NOT EXISTS cash_custody_event (
    id                INTEGER PRIMARY KEY,
    unit              TEXT NOT NULL REFERENCES business_unit(code),
    event_date        TEXT NOT NULL,
    from_party        TEXT NOT NULL,          -- 'counter' | 'drawer' | 'dr_bhawna' | 'dr_manoj' | 'bank'
    to_party          TEXT NOT NULL,
    amount_p          INTEGER NOT NULL CHECK (amount_p > 0),
    counter_person_id INTEGER REFERENCES counter_person(id),
    day_entry_id      INTEGER REFERENCES day_entry(id) ON DELETE SET NULL,
    cash_movement_id  INTEGER REFERENCES cash_movement(id) ON DELETE SET NULL,
    -- the marker whose absence hid a float for five months (D323)
    month_end_kind    TEXT CHECK (month_end_kind IS NULL OR month_end_kind IN ('taken','carried')),
    note              TEXT,
    entered_by        TEXT,
    entered_at        TEXT
);
CREATE INDEX IF NOT EXISTS ix_custody_date  ON cash_custody_event(unit, event_date);
CREATE INDEX IF NOT EXISTS ix_custody_party ON cash_custody_event(to_party, event_date);

-- A running "who holds what" without a second source of truth: it is derived.
CREATE VIEW IF NOT EXISTS v_cash_custody_balance AS
SELECT unit, party, SUM(amount_p) AS held_p FROM (
    SELECT unit, to_party   AS party,  amount_p FROM cash_custody_event
    UNION ALL
    SELECT unit, from_party AS party, -amount_p FROM cash_custody_event
) GROUP BY unit, party;

INSERT OR REPLACE INTO setting (key,value,note) VALUES
 ('migration.S186_reserve_yesbank','applied',
  'S186: bank_statement_line + bank_statement_period (F-103 / F-112 detector), counter_person '
  || '(seeded Darpan, Vinay Saxena, Dr Bhawna), cash_custody_event + v_cash_custody_balance '
  || '(D323(d)). Purely additive — no existing table, view or row touched.');

COMMIT;

-- =============================================================================
--  ROLLBACK (drops only what this created):
--  BEGIN;
--  DROP VIEW  IF EXISTS v_cash_custody_balance;
--  DROP TABLE IF EXISTS cash_custody_event;
--  DROP TABLE IF EXISTS counter_person;
--  DROP TABLE IF EXISTS bank_statement_period;
--  DROP TABLE IF EXISTS bank_statement_line;
--  DELETE FROM setting WHERE key='migration.S186_reserve_yesbank';
--  COMMIT;
-- =============================================================================
;
-- ===== deploy_kits/S186_W1a/finance_migration_S186_walkin.sql =====
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

-- A RETURN IS A MAGNITUDE WITH ITS DIRECTION IN THE ROW'S TYPE (D314).
-- sale_item_review stores a credit note as a NEGATIVE amount; sale_item has
-- CHECK (amount_p >= 0) and carries returns as a positive magnitude with the
-- service 'pharmacy_return', which v_day_attribution SUBTRACTS. The first build
-- of this migration guarded on `amount_p > 0` and therefore skipped every credit
-- note in silence -- 116 of 2,072 rows -- while the gate's projection had counted
-- them. The verify caught it and the installer restored. Both sides now agree.
INSERT INTO sale_item (day_entry_id, ingest_batch_id, unit, patient_ref_id, service,
                       description, amount_p, mode, source, source_ref, confidence,
                       verified_by, verified_at)
  SELECT r.day_entry_id, r.ingest_batch_id, 'medical',
         (SELECT id FROM patient_ref WHERE clinic_id='WALK-IN'),
         CASE WHEN COALESCE(r.amount_p,0) < 0 THEN 'pharmacy_return' ELSE 'pharmacy' END,
         COALESCE(NULLIF(TRIM(r.raw_text),''), 'legacy bill, no clinic ID'),
         ABS(COALESCE(r.amount_p,0)), NULL, 'manual',
         'S186-F104-' || r.id, NULL, 'S186_W1a', datetime('now')
    FROM sale_item_review r
    JOIN day_entry e ON e.id = r.day_entry_id
   WHERE e.unit='medical' AND r.status='open'
     AND NOT EXISTS (SELECT 1 FROM sale_item s WHERE s.source_ref = 'S186-F104-' || r.id);

UPDATE sale_item_review
   SET status='resolved', resolved_by='S186_W1a', resolved_at=datetime('now')
 WHERE status='open'
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
;
-- ===== deploy_kits/S189_C1a/finance_migration_S189_custody.sql =====
-- =============================================================================
--  finance_migration_S189_custody.sql  ·  Session 189  ·  F-137
--
--  WHAT THIS RECORDS
--  The physical cash position established by COUNT on 17 Aug 2026 (S186), which
--  until now has existed only as a sentence inside cash_count.explanation:
--
--      "Darpan drawer 0 (cleared) + owner 18,963 + Dr Bhawna 1,56,235"
--
--  S186 created cash_custody_event -- with from_party, to_party and amount_p --
--  in the same session, and then wrote the custody facts into a text column of a
--  different table. No query can reach prose. That is why Darpan's "Where the
--  cash is" card reads zero against roughly 1.75 lakh, and it is the whole of
--  what this migration fixes.
--
--  WHAT IT DELIBERATELY DOES NOT DO -- read this before anything else
--  It does NOT write cash_movement. v_day_cash computes
--      cash_out_p = SUM(cash_movement WHERE direction='out')
--  so EVERY movement row is subtracted from cash in hand, whatever the party.
--  Booking these handovers there would take cash in hand from Rs 2,05,198 to
--  about Rs 30,000 and destroy the agreement the 17 Aug count established.
--  OWNER RULING, S189: cash held by Dr Manoj or Dr Bhawna IS cash in hand,
--  merely located elsewhere. Custody is LOCATION; movement is QUANTITY.
--  No view in the cash ledger reads cash_custody_event, so this migration
--  cannot move a rupee -- and gate_s189.py proves that rather than asserting it.
--
--  THE ARITHMETIC, and where each figure comes from
--    Dr Manoj      18,963   S186 §4, the drawer clearing, itemised to the rupee
--    Dr Bhawna    1,56,235  = 7,309 + 3,926 + 1,45,000
--                    7,309  S186 §4, Vinay -> Dr Bhawna, 6 Aug  (proven by the
--                           drawer arithmetic landing exactly on 48,963)
--                    3,926  S186 §4, Vinay -> Dr Bhawna, 15 Aug (same proof)
--                1,45,000  the balance of her counted position. Its individual
--                           journeys are NOT itemised anywhere in the record, so
--                           it is entered as ONE row that says so. The route is
--                           taken from the documented custody model (S186 §2:
--                           the counter person hands cash direct to Dr Bhawna,
--                           bypassing the drawer), NOT from a per-transaction
--                           record -- and the note on the row states that.
--                           That it comes to a round 1,45,000 is a corroboration,
--                           not the reason: 1,56,235 - 7,309 - 3,926 = 1,45,000.
--    TOTAL        1,75,198  equal, to the paise, to cash_count.counted_p for
--                           2026-08-17. The gate refuses if it is not.
--
--  Darpan's drawer is 0 and therefore has NO row. An empty drawer is the absence
--  of custody, and absence is recorded by writing nothing (F-107's lesson taken
--  the other way: we do not invent a row to say "nothing here").
--
--  ADDITIVE. Four INSERTs into one table, plus one marker. Nothing is read,
--  altered, rebuilt or dropped. Rollback block at the foot; it is lossless.
-- =============================================================================

INSERT INTO cash_custody_event
    (unit, event_date, from_party, to_party, amount_p, counter_person_id,
     day_entry_id, month_end_kind, note, entered_by, entered_at)
VALUES
 ('medical','2026-08-06','counter','dr_bhawna',   730900,
  (SELECT id FROM counter_person WHERE unit='medical' AND name='Vinay Saxena'),
  (SELECT id FROM day_entry WHERE unit='medical' AND business_date='2026-08-06'),
  NULL,
  'S189 (F-137). Vinay handed cash DIRECT to Dr Bhawna, bypassing the drawer. '
  || 'Itemised in S186 section 4 and proven by the drawer clearing landing '
  || 'exactly on Rs 48,963. Location only -- this money never left the books.',
  'manoj','2026-08-18'),

 ('medical','2026-08-15','counter','dr_bhawna',   392600,
  (SELECT id FROM counter_person WHERE unit='medical' AND name='Vinay Saxena'),
  (SELECT id FROM day_entry WHERE unit='medical' AND business_date='2026-08-15'),
  NULL,
  'S189 (F-137). Vinay handed cash DIRECT to Dr Bhawna, bypassing the drawer. '
  || 'Itemised in S186 section 4, same proof. Location only.',
  'manoj','2026-08-18'),

 ('medical','2026-08-17','counter','dr_bhawna', 14500000,
  (SELECT id FROM counter_person WHERE unit='medical' AND name='Vinay Saxena'),
  (SELECT id FROM day_entry WHERE unit='medical' AND business_date='2026-08-17'),
  NULL,
  'S189 (F-137). BALANCING ENTRY to the physical count of 17 Aug 2026. '
  || 'Rs 1,56,235 counted with Dr Bhawna, less the two itemised Vinay '
  || 'handovers (7,309 + 3,926) = Rs 1,45,000. The individual journeys making '
  || 'up this remainder are NOT recorded anywhere; the route shown is the '
  || 'documented custody model (S186 section 2), not a per-transaction record. '
  || 'This row is evidence of POSITION, established by counting notes, and it '
  || 'is deliberately one row rather than an invented history. D323.',
  'manoj','2026-08-18'),

 ('medical','2026-08-17','drawer','dr_manoj',   1896300,
  (SELECT id FROM counter_person WHERE unit='medical' AND name='Darpan'),
  (SELECT id FROM day_entry WHERE unit='medical' AND business_date='2026-08-17'),
  NULL,
  'S189 (F-137). The drawer clearing of 17 Aug 2026, itemised to the rupee in '
  || 'S186 section 4: copy balance 60,198 less the two Vinay handovers = '
  || 'Rs 48,963 physically in the drawer, of which 10,000 settled July salary, '
  || '20,000 was advanced against August salary, and Rs 18,963 was handed to '
  || 'the owner. Drawer left EMPTY, proved to the rupee. Location only.',
  'manoj','2026-08-18');

INSERT OR REPLACE INTO setting (key,value,note) VALUES
 ('migration.S189_custody','applied 2026-08-18',
  'S189 F-137: the 17 Aug 2026 counted custody position written into '
  || 'cash_custody_event, where it had existed only as prose in '
  || 'cash_count.explanation. Dr Manoj 18,963 + Dr Bhawna 1,56,235 = 1,75,198, '
  || 'equal to cash_count.counted_p for that date. Ledger deliberately '
  || 'untouched: custody is location, not quantity.');

-- =============================================================================
--  ROLLBACK -- paste and run only if S189_C1a has to be undone. Lossless:
--  it removes exactly the four rows this file inserted and the marker, and
--  touches no money, because this migration never touched any.
--
--  DELETE FROM cash_custody_event
--   WHERE unit='medical' AND entered_by='manoj' AND entered_at='2026-08-18'
--     AND note LIKE 'S189 (F-137).%';
--  DELETE FROM setting WHERE key='migration.S189_custody';
-- =============================================================================
;
