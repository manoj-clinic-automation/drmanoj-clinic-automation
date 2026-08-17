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
