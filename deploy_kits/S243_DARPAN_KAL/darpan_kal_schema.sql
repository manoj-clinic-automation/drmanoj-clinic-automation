-- darpan_kal_schema.sql -- S243_DARPAN_KAL. Additive, idempotent, safe on every boot.
-- Darpan's morning page: yesterday's expected cash, what he handed over and to whom,
-- the reason when they differ, the server's verdict, the returns he was asked about.
-- No patient field is stored here (F-185): bills are named by bill number only.

CREATE TABLE IF NOT EXISTS darpan_kal_day (
    unit              TEXT NOT NULL,
    business_date     TEXT NOT NULL,
    net_sale_p        INTEGER, home_p INTEGER, proc_p INTEGER, online_p INTEGER,
    online_provisional INTEGER NOT NULL DEFAULT 0,   -- 1 = bank statement not in; Marg modes used
    expected_p        INTEGER,
    handed_p          INTEGER,
    handed_to         TEXT CHECK (handed_to IS NULL OR handed_to IN ('dr_manoj','dr_bhawna')),
    diff_p            INTEGER,
    reason            TEXT CHECK (reason IS NULL OR reason IN
                        ('none','home_not_in_print','online_not_on_pos','return_cash','carried','other')),
    reason_note       TEXT,
    state             TEXT NOT NULL DEFAULT 'open' CHECK (state IN
                        ('waiting_report','open','complete','explained','needs_owner')),
    verdict           TEXT CHECK (verdict IS NULL OR verdict IN ('confirmed','not_confirmable','contradicted')),
    decided_by        TEXT, decided_at TEXT,
    landed_movement_id INTEGER,                     -- cash_movement.id once the day exists
    received_by       TEXT, received_at TEXT,       -- the recipient's tap (amber until then)
    owner_decision    TEXT CHECK (owner_decision IS NULL OR owner_decision IN ('accept','reject','ask')),
    owner_note        TEXT, owner_by TEXT, owner_at TEXT,
    created_by        TEXT, created_at TEXT, updated_at TEXT,
    PRIMARY KEY (unit, business_date)
);

CREATE TABLE IF NOT EXISTS darpan_kal_check (
    id            INTEGER PRIMARY KEY,
    unit          TEXT NOT NULL,
    business_date TEXT NOT NULL,
    reason        TEXT NOT NULL,
    verdict       TEXT NOT NULL CHECK (verdict IN ('confirmed','not_confirmable','contradicted')),
    evidence_json TEXT,
    checked_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_kal_check_day ON darpan_kal_check(unit, business_date);

CREATE TABLE IF NOT EXISTS darpan_kal_return_answer (
    id            INTEGER PRIMARY KEY,
    unit          TEXT NOT NULL,
    business_date TEXT NOT NULL,
    cn_bill       TEXT NOT NULL,
    flag          TEXT,
    answer        TEXT NOT NULL CHECK (answer IN ('slip_checked','wrong_bill','exchange','doctor_said','other')),
    note          TEXT,
    answered_by   TEXT NOT NULL,
    answered_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_kal_ra_bill ON darpan_kal_return_answer(unit, cn_bill);

-- Cash MORE than expected = Darpan paid extra from his own pocket (owner, 13-Sep).
-- Recorded as owed back to him; stays on his screen and the owner's card until returned.
CREATE TABLE IF NOT EXISTS darpan_kal_owed (
    id            INTEGER PRIMARY KEY,
    unit          TEXT NOT NULL,
    business_date TEXT NOT NULL,
    amount_p      INTEGER NOT NULL CHECK (amount_p > 0),
    provisional   INTEGER NOT NULL DEFAULT 0,
    status        TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','returned','withdrawn')),
    returned_by   TEXT, returned_at TEXT, note TEXT,
    created_at    TEXT NOT NULL,
    UNIQUE (unit, business_date)
);

CREATE TABLE IF NOT EXISTS darpan_kal_audit (
    id     INTEGER PRIMARY KEY,
    at     TEXT NOT NULL, who TEXT NOT NULL,
    action TEXT NOT NULL, detail TEXT
);

INSERT OR IGNORE INTO setting (key, value) VALUES ('darpan_kal.tolerance_p', '5000');
INSERT OR IGNORE INTO setting (key, value) VALUES ('darpan_kal.month_cap_p', '200000');
INSERT OR IGNORE INTO setting (key, value) VALUES ('darpan_kal.recipients', 'manoj:dr_manoj,bhawna:dr_bhawna');
INSERT OR IGNORE INTO setting (key, value) VALUES ('procedure_customer_name', '');
