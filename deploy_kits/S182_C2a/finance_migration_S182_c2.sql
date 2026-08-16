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
