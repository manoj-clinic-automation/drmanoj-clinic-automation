-- joiner_schema.sql -- adding a person to the clinic's systems, and removing one.
--
-- WHY A REGISTER AND NOT A CHECKLIST ON PAPER
--     Adding a person touches four separate places: the roster sheet, the
--     portal, the person's own scope, and the biometric device. They are done
--     by different people on different days, and the biometric is routinely
--     last because it needs the person to be physically present.
--
--     A paper checklist handles that badly. It gets to "biometric pending",
--     the person starts working, and the last line is never ticked -- so the
--     roster row keeps no Emp Code, build_staff_master.py skips it forever,
--     and attendance quietly does not cover somebody who has been at the
--     counter for a month. Nothing breaks; a person is simply not there.
--
--     So: an open record per person, one row per step, and the step that lags
--     stays visible until it is done.
--
-- The same register does LEAVERS. An exit is the same four places in reverse,
-- and the failure is identical -- a login that still works after somebody has
-- gone is the same missed tick as a biometric never captured.
--
-- Idempotent. Safe on every boot. sqlite3 only. No personal number is stored
-- here: contact details live in the config store (F-185).

CREATE TABLE IF NOT EXISTS joiner (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  ref           TEXT    NOT NULL UNIQUE,     -- JOIN-2026-0001 / EXIT-2026-0001
  kind          TEXT    NOT NULL DEFAULT 'JOIN',   -- JOIN | EXIT
  person        TEXT    NOT NULL,            -- the name as the roster spells it
  role          TEXT,                        -- counter / purchase / reception ...
  status        TEXT    NOT NULL DEFAULT 'DECIDED',
  username      TEXT,                        -- DERIVED from the first name (S207.2)
  employment    TEXT,                        -- FULLTIME | PARTTIME | BIWEEKLY
  authorities   TEXT,                        -- comma-separated, ticked at DECIDED
  emp_code      TEXT,                        -- biometric user_id, once captured
  roster_row    TEXT,                        -- where the anchor row sits
  opened_on     TEXT    NOT NULL,
  opened_by     TEXT    NOT NULL,
  closed_on     TEXT,
  closed_by     TEXT,
  created_at    TEXT    NOT NULL,
  updated_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS joiner_step (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  joiner_id     INTEGER NOT NULL REFERENCES joiner(id),
  step          TEXT    NOT NULL,
  done_on       TEXT,
  done_by       TEXT,
  detail        TEXT,
  UNIQUE(joiner_id, step)
);

CREATE TABLE IF NOT EXISTS joiner_event (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  joiner_id     INTEGER NOT NULL REFERENCES joiner(id),
  at            TEXT    NOT NULL,
  actor         TEXT    NOT NULL,
  kind          TEXT    NOT NULL,
  detail        TEXT
);

CREATE INDEX IF NOT EXISTS ix_joiner_status ON joiner(status);
CREATE INDEX IF NOT EXISTS ix_jstep_joiner  ON joiner_step(joiner_id);
CREATE INDEX IF NOT EXISTS ix_jevent_joiner ON joiner_event(joiner_id, at);

-- ---------------------------------------------------------------------------
-- EMPLOYEE CODES. A code is PERMANENT and is NEVER reissued.
--
-- WHY THIS TABLE HAD TO EXIST
--     punches.csv is append-only and keyed on (user_id, datetime). It holds
--     every punch ever taken, including those of people who left years ago.
--     The NAME behind a user_id lives only in staff_master.csv, which is
--     rebuilt from the roster sheet and contains only rows that still have an
--     Emp Code -- every one written active="Y". There is no inactive state.
--
--     So when somebody leaves and their roster row goes, their punches stay in
--     punches.csv under a code that no longer has a name. Reissue that code to
--     a new joiner and EVERY HISTORICAL PUNCH UNDER IT BECOMES THEIRS -- in
--     attendance, in the month report, in salary -- with no error and no trace.
--
--     Nothing in the system currently remembers that a code was ever used. The
--     roster sheet is the only memory, and a deleted leaver row destroys it.
--     This table is that memory, and it never deletes a row.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS emp_code (
  code          INTEGER PRIMARY KEY,       -- the biometric device's user_id
  person        TEXT    NOT NULL,
  issued_on     TEXT,
  retired_on    TEXT,                      -- set when they leave; NEVER deleted
  source        TEXT,                      -- roster | punches | manual
  note          TEXT
);
