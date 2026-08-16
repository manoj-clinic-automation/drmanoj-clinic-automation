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
