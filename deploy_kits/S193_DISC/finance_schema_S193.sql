-- ============================================================================
--  finance_schema.sql  ·  Clinic Finance / Daily Revenue system
--  Dr. Manoj Agarwal · Advanced Orthopaedic Surgery Centre, Bareilly
--  Session 179 · step B1 · contract: S179_Sanjeevni_Medical_Module_Build_Contract_v1
--
--  DESIGN RULES (load-bearing — do not relax without a decision):
--   1. All money is stored as INTEGER PAISE. No floats anywhere. Ever.
--   2. Nothing derivable is stored as typed input. Opening balance, closing
--      balance, day totals and variances are VIEWS, never columns.
--      -> this is what makes the 36 carry-forward breaks structurally impossible.
--   3. One row per (unit, business_date). Enforced by the database, not by habit.
--   4. Corrections supersede; they never overwrite. Old submissions live on in
--      day_revision, verbatim.
--   5. A reconciliation exception stays OPEN and keeps shouting until a human
--      closes it with a reason. It cannot be silently aged out.
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- reference

CREATE TABLE IF NOT EXISTS business_unit (
    code        TEXT PRIMARY KEY,          -- 'medical' | 'clinic' | 'lab'
    name        TEXT NOT NULL,
    merchant_id TEXT,                      -- ICICI Merchant Solutions MID
    open_sunday INTEGER NOT NULL DEFAULT 1,
    active      INTEGER NOT NULL DEFAULT 1
);

-- Lightweight mirror only. The staff MASTER is staff_register (D274) — this
-- table never becomes a second source of truth for staff.
CREATE TABLE IF NOT EXISTS staff_ref (
    id            INTEGER PRIMARY KEY,
    register_id   INTEGER UNIQUE,          -- id in staff_register
    name          TEXT NOT NULL,
    is_pharmacy   INTEGER NOT NULL DEFAULT 0,
    active        INTEGER NOT NULL DEFAULT 1
);

-- ---------------------------------------------------------------- the day

CREATE TABLE IF NOT EXISTS day_entry (
    id             INTEGER PRIMARY KEY,
    unit           TEXT NOT NULL REFERENCES business_unit(code),
    business_date  TEXT NOT NULL,          -- ISO 'YYYY-MM-DD' — never a slice of a string (F-78)
    status         TEXT NOT NULL DEFAULT 'draft'
                   CHECK (status IN ('draft','submitted','approved','locked','closed_holiday')),
    manned_by      INTEGER REFERENCES staff_ref(id),
    manned_source  TEXT CHECK (manned_source IN ('biometric','manual','legacy_unknown')),
    source         TEXT NOT NULL DEFAULT 'app'
                   CHECK (source IN ('app','legacy_sheet')),
    entered_by     TEXT,
    entered_at     TEXT,
    approved_by    TEXT,
    approved_at    TEXT,
    legacy_ref     TEXT,                   -- original sheet timestamp, for traceability
    UNIQUE (unit, business_date)           -- kills FIN-8 permanently
);
CREATE INDEX IF NOT EXISTS ix_day_entry_unit_date ON day_entry(unit, business_date);

-- Superseded submissions, kept verbatim. A correction never destroys evidence.
CREATE TABLE IF NOT EXISTS day_revision (
    id            INTEGER PRIMARY KEY,
    day_entry_id  INTEGER NOT NULL REFERENCES day_entry(id) ON DELETE CASCADE,
    revision      INTEGER NOT NULL,
    submitted_at  TEXT,
    payload_json  TEXT NOT NULL,
    superseded_at TEXT
);

-- ---------------------------------------------------------------- the money
-- NARROW by design. A new revenue head or payment mode is a ROW, not a schema
-- change and not a broken history. (The old sheet needed a new column.)

CREATE TABLE IF NOT EXISTS day_line (
    id            INTEGER PRIMARY KEY,
    day_entry_id  INTEGER NOT NULL REFERENCES day_entry(id) ON DELETE CASCADE,
    service       TEXT NOT NULL,           -- 'pharmacy_sale' | 'opd' | 'xray' | 'procedure' | 'lab'
    mode          TEXT NOT NULL CHECK (mode IN ('cash','upi','card','credit')),
    amount_p      INTEGER NOT NULL CHECK (amount_p >= 0)
);
CREATE INDEX IF NOT EXISTS ix_day_line_entry ON day_line(day_entry_id);

CREATE TABLE IF NOT EXISTS day_expense (
    id              INTEGER PRIMARY KEY,
    day_entry_id    INTEGER NOT NULL REFERENCES day_entry(id) ON DELETE CASCADE,
    amount_p        INTEGER NOT NULL DEFAULT 0 CHECK (amount_p >= 0),
    amount_known    INTEGER NOT NULL DEFAULT 1,   -- 0 = blank/unreadable in source; NOT the same as zero
    category_fixed  TEXT CHECK (category_fixed IS NULL OR category_fixed IN ('salary_advance')),
    staff_id        INTEGER REFERENCES staff_ref(id),
    category_text   TEXT,
    note            TEXT,
    -- salary advance is maker-checker: pharmacy makes, doctor approves, and ONLY
    -- on approval does it post to the Staff Ledger (D258 stays the single home).
    ledger_posted   INTEGER NOT NULL DEFAULT 0,
    ledger_posted_at TEXT,
    ledger_ref      TEXT,
    CHECK (category_fixed IS NULL OR staff_id IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS ix_day_expense_entry ON day_expense(day_entry_id);

-- Deposits, hand-overs and returns. Direction + party covers
-- "to bank / to Dr Manoj / to Dr Bhawna / and back" in one model.
CREATE TABLE IF NOT EXISTS cash_movement (
    id                 INTEGER PRIMARY KEY,
    day_entry_id       INTEGER NOT NULL REFERENCES day_entry(id) ON DELETE CASCADE,
    direction          TEXT NOT NULL CHECK (direction IN ('out','in')),
    party              TEXT NOT NULL CHECK (party IN ('bank','dr_manoj','dr_bhawna','other')),
    amount_p           INTEGER NOT NULL CHECK (amount_p > 0),
    reference          TEXT,
    slip_attachment_id INTEGER REFERENCES attachment(id)
);
CREATE INDEX IF NOT EXISTS ix_cash_movement_entry ON cash_movement(day_entry_id);

-- The ONLY way the running balance can ever move without a real transaction.
-- Visible, dated, reasoned, and it must be approved.
CREATE TABLE IF NOT EXISTS cash_adjustment (
    id            INTEGER PRIMARY KEY,
    day_entry_id  INTEGER NOT NULL REFERENCES day_entry(id) ON DELETE CASCADE,
    amount_p      INTEGER NOT NULL,        -- signed
    reason        TEXT NOT NULL,
    source        TEXT NOT NULL CHECK (source IN ('legacy_import','manual')),
    status        TEXT NOT NULL DEFAULT 'open'
                  CHECK (status IN ('open','explained','approved')),
    explanation   TEXT,
    approved_by   TEXT,
    approved_at   TEXT
);
CREATE INDEX IF NOT EXISTS ix_cash_adj_entry ON cash_adjustment(day_entry_id);

-- Physical count. Kept separate from the computed ledger FOREVER — this is the
-- one distinction the spreadsheet never made, and every drift came from that.
CREATE TABLE IF NOT EXISTS cash_count (
    id            INTEGER PRIMARY KEY,
    unit          TEXT NOT NULL REFERENCES business_unit(code),
    business_date TEXT NOT NULL,
    counted_p     INTEGER NOT NULL,
    counted_by    TEXT,
    counted_at    TEXT,
    explanation   TEXT,
    UNIQUE (unit, business_date)
);

-- ---------------------------------------------------------------- evidence

CREATE TABLE IF NOT EXISTS attachment (
    id            INTEGER PRIMARY KEY,
    day_entry_id  INTEGER REFERENCES day_entry(id) ON DELETE CASCADE,
    doc_type      TEXT NOT NULL
                  CHECK (doc_type IN ('sale_report','manual_copy','orthotics_copy',
                                      'deposit_slip','legacy_medicine_copy','legacy_implant_copy')),
    path          TEXT,
    external_url  TEXT,                    -- legacy Drive links preserved on import
    sha256        TEXT,
    bytes         INTEGER,
    uploaded_by   TEXT,
    uploaded_at   TEXT
);
CREATE INDEX IF NOT EXISTS ix_attachment_entry ON attachment(day_entry_id);

CREATE TABLE IF NOT EXISTS ocr_extract (
    id             INTEGER PRIMARY KEY,
    attachment_id  INTEGER NOT NULL REFERENCES attachment(id) ON DELETE CASCADE,
    engine         TEXT NOT NULL DEFAULT 'sarvam',
    raw_text       TEXT,
    extracted_p    INTEGER,
    confidence     REAL,
    match_status   TEXT CHECK (match_status IN ('match','mismatch','unreadable','not_run')),
    run_at         TEXT
);

-- Daily ICICI Merchant Solutions MPR (.xlsx), one file per merchant per day.
-- Deduplicated on (merchant_id, statement_date) so a forward or a re-send can
-- never double-count.
CREATE TABLE IF NOT EXISTS upi_statement (
    id             INTEGER PRIMARY KEY,
    merchant_id    TEXT NOT NULL,
    unit           TEXT REFERENCES business_unit(code),
    statement_date TEXT NOT NULL,
    source_msg_id  TEXT,
    filename       TEXT,
    sha256         TEXT,
    parsed_total_p INTEGER,
    txn_count      INTEGER,
    ingested_at    TEXT,
    UNIQUE (merchant_id, statement_date)
);

-- ---------------------------------------------------------------- shouting

-- Owner's rule (S179): "any diff flags and shouts until reconciled."
-- An exception is OPEN until a human closes it with a resolution. Every shout
-- is counted, so escalation is possible and silence is impossible.
CREATE TABLE IF NOT EXISTS recon_exception (
    id             INTEGER PRIMARY KEY,
    unit           TEXT NOT NULL REFERENCES business_unit(code),
    business_date  TEXT NOT NULL,
    kind           TEXT NOT NULL,          -- 'upi_vs_statement' | 'total_vs_ocr' |
                                           -- 'missing_day' | 'negative_cash' |
                                           -- 'carry_forward_break' | 'count_variance'
    expected_p     INTEGER,
    actual_p       INTEGER,
    diff_p         INTEGER,
    severity       TEXT NOT NULL DEFAULT 'high'
                   CHECK (severity IN ('low','medium','high')),
    status         TEXT NOT NULL DEFAULT 'open'
                   CHECK (status IN ('open','acknowledged','resolved')),
    detail         TEXT,
    opened_at      TEXT,
    shout_count    INTEGER NOT NULL DEFAULT 0,
    last_shout_at  TEXT,
    resolution     TEXT,
    closed_by      TEXT,
    closed_at      TEXT,
    UNIQUE (unit, business_date, kind)
);
CREATE INDEX IF NOT EXISTS ix_recon_open ON recon_exception(status, unit, business_date);

-- Import / entry quality flags (not necessarily money exceptions).
CREATE TABLE IF NOT EXISTS data_flag (
    id            INTEGER PRIMARY KEY,
    unit          TEXT,
    business_date TEXT,
    day_entry_id  INTEGER REFERENCES day_entry(id) ON DELETE CASCADE,
    code          TEXT NOT NULL,
    severity      TEXT NOT NULL DEFAULT 'info',
    detail        TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id         INTEGER PRIMARY KEY,
    table_name TEXT NOT NULL,
    row_id     INTEGER,
    action     TEXT NOT NULL,
    before_json TEXT,
    after_json  TEXT,
    by_whom    TEXT,
    at         TEXT NOT NULL
);

-- ---------------------------------------------------------------- the ledger
-- DERIVED. There is no table anywhere that stores opening or closing cash, so
-- there is no cell for anyone to overwrite. This is the whole fix.

DROP VIEW IF EXISTS v_day_cash;
CREATE VIEW v_day_cash AS
SELECT
    e.id                AS day_entry_id,
    e.unit              AS unit,
    e.business_date     AS business_date,
    COALESCE((SELECT SUM(l.amount_p) FROM day_line l
               WHERE l.day_entry_id = e.id AND l.mode = 'cash'), 0)          AS cash_in_p,
    COALESCE((SELECT SUM(l.amount_p) FROM day_line l
               WHERE l.day_entry_id = e.id AND l.mode = 'upi'), 0)           AS upi_in_p,
    COALESCE((SELECT SUM(l.amount_p) FROM day_line l
               WHERE l.day_entry_id = e.id), 0)                              AS revenue_p,
    COALESCE((SELECT SUM(x.amount_p) FROM day_expense x
               WHERE x.day_entry_id = e.id AND x.amount_known = 1), 0)       AS expense_p,
    COALESCE((SELECT SUM(m.amount_p) FROM cash_movement m
               WHERE m.day_entry_id = e.id AND m.direction = 'out'), 0)      AS cash_out_p,
    COALESCE((SELECT SUM(m.amount_p) FROM cash_movement m
               WHERE m.day_entry_id = e.id AND m.direction = 'in'), 0)       AS cash_back_p,
    COALESCE((SELECT SUM(a.amount_p) FROM cash_adjustment a
               WHERE a.day_entry_id = e.id), 0)                              AS adjust_p
FROM day_entry e;

DROP VIEW IF EXISTS v_cash_ledger;
CREATE VIEW v_cash_ledger AS
SELECT
    unit, business_date, day_entry_id,
    cash_in_p, upi_in_p, revenue_p, expense_p, cash_out_p, cash_back_p, adjust_p,
    (cash_in_p - expense_p - cash_out_p + cash_back_p + adjust_p) AS net_p,
    COALESCE(SUM(cash_in_p - expense_p - cash_out_p + cash_back_p + adjust_p)
             OVER (PARTITION BY unit ORDER BY business_date, day_entry_id
                   ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING), 0)     AS opening_p,
    SUM(cash_in_p - expense_p - cash_out_p + cash_back_p + adjust_p)
             OVER (PARTITION BY unit ORDER BY business_date, day_entry_id
                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)         AS closing_p
FROM v_day_cash;

DROP VIEW IF EXISTS v_month_summary;
CREATE VIEW v_month_summary AS
SELECT
    unit,
    substr(business_date, 1, 7)                AS ym,
    COUNT(*)                                   AS days_recorded,
    SUM(revenue_p)                             AS revenue_p,
    SUM(cash_in_p)                             AS cash_p,
    SUM(upi_in_p)                              AS upi_p,
    SUM(expense_p)                             AS expense_p,
    SUM(cash_out_p)                            AS deposited_p,
    SUM(adjust_p)                              AS adjust_p
FROM v_day_cash
GROUP BY unit, ym;

-- ---------------------------------------------------------------- seed

INSERT OR IGNORE INTO business_unit (code, name, merchant_id, open_sunday) VALUES
    ('medical', 'Sanjeevni Medicos',            '100000000312505', 1),
    ('clinic',  'Dr Manoj Agarwal Clinic',      '100000000306941', 1),
    ('lab',     'Lab',                          NULL,              1);

-- END OF finance_schema.sql

-- ============================================================================
--  SCHEMA v2 ADDITIONS  ·  Session 179 · step B1b
--  Contract: S179_Clinic_Finance_System_Build_Contract_v2
--
--  Adds: three separate accounting entities · the patient revenue spine ·
--        export/accountant-pack plumbing · settings.
--  Everything below is ADDITIVE. v1 tables and views are untouched.
-- ============================================================================

-- ---------------------------------------------------------------- entities
-- HARD RULE (D-candidate): medical, clinic and pathology are three separate
-- books. There is no default consolidation anywhere in accounting output.

CREATE TABLE IF NOT EXISTS entity (
    code             TEXT PRIMARY KEY,     -- 'medical' | 'clinic' | 'lab'
    legal_name       TEXT NOT NULL,
    gstin            TEXT,
    merchant_id      TEXT,                 -- ICICI Merchant Solutions MID
    accountant_email TEXT,
    fy_start_month   INTEGER NOT NULL DEFAULT 4,
    active           INTEGER NOT NULL DEFAULT 1
);

-- Each unit belongs to exactly one entity. Kept as a separate column (rather
-- than assuming unit==entity) so a future unit can join an existing book
-- without a migration.
ALTER TABLE business_unit ADD COLUMN entity_code TEXT REFERENCES entity(code);

-- ---------------------------------------------------------- patient spine
-- Crosses entities for CLINICAL / MANAGEMENT questions only.
-- It is never an accounting document. See v_patient_revenue.

CREATE TABLE IF NOT EXISTS patient_ref (
    id           INTEGER PRIMARY KEY,
    clinic_id    TEXT NOT NULL UNIQUE,     -- the clinic's own patient ID; 'WALK-IN' is reserved
    name         TEXT,
    phone_last4  TEXT,                     -- last 4 only, always (masking rule)
    first_seen   TEXT,
    merged_into  INTEGER REFERENCES patient_ref(id),   -- de-dup without rewriting history
    note         TEXT
);
CREATE INDEX IF NOT EXISTS ix_patient_clinic_id ON patient_ref(clinic_id);

-- One line per billed item. The day's TOTAL is settled by day_line + the bank
-- statement; sale_item is attribution, and attribution improving later must
-- never be able to move the books. (Enforced by reconciling, not by summing.)
CREATE TABLE IF NOT EXISTS sale_item (
    id             INTEGER PRIMARY KEY,
    day_entry_id   INTEGER NOT NULL REFERENCES day_entry(id) ON DELETE CASCADE,
    unit           TEXT NOT NULL REFERENCES business_unit(code),
    patient_ref_id INTEGER REFERENCES patient_ref(id),
    service        TEXT NOT NULL,          -- pharmacy | implant_orthotic | lab_test
                                           -- | consultation | xray | procedure
    description    TEXT,
    amount_p       INTEGER NOT NULL CHECK (amount_p >= 0),   -- NET (after discount)
    gross_p        INTEGER,                -- MRP/gross before discount (Marg); NULL if unknown
    disc_p         INTEGER,                -- discount amount (Marg); NULL if unknown
    mode           TEXT CHECK (mode IN ('cash','upi','card','credit')),
    source         TEXT NOT NULL CHECK (source IN ('ocr','manual','tracker')),
    source_ref     TEXT,                   -- bill no / tracker row id
    confidence     REAL,
    verified_by    TEXT,
    verified_at    TEXT
);
CREATE INDEX IF NOT EXISTS ix_sale_item_entry   ON sale_item(day_entry_id);
CREATE INDEX IF NOT EXISTS ix_sale_item_patient ON sale_item(patient_ref_id);

-- Low-confidence or unmatched OCR lines wait here. Visible, small, never blocking.
CREATE TABLE IF NOT EXISTS sale_item_review (
    id            INTEGER PRIMARY KEY,
    day_entry_id  INTEGER NOT NULL REFERENCES day_entry(id) ON DELETE CASCADE,
    raw_text      TEXT,
    guess_clinic_id TEXT,
    guess_name    TEXT,
    amount_p      INTEGER,
    confidence    REAL,
    status        TEXT NOT NULL DEFAULT 'open'
                  CHECK (status IN ('open','resolved','discarded')),
    resolved_by   TEXT,
    resolved_at   TEXT
);

-- ------------------------------------------------- exports / accountant pack
-- Every regeneration is versioned, so an accountant can never be quietly handed
-- different numbers than last time.

CREATE TABLE IF NOT EXISTS export_run (
    id           INTEGER PRIMARY KEY,
    entity_code  TEXT NOT NULL REFERENCES entity(code),
    ym           TEXT NOT NULL,            -- 'YYYY-MM'
    kind         TEXT NOT NULL CHECK (kind IN ('accountant_pack','tally_csv','revenue_csv')),
    version      INTEGER NOT NULL,
    include_patient_names INTEGER NOT NULL DEFAULT 0,   -- the owner's toggle (S179)
    path         TEXT,
    sha256       TEXT,
    row_count    INTEGER,
    total_p      INTEGER,
    generated_by TEXT,
    generated_at TEXT,
    UNIQUE (entity_code, ym, kind, version)
);

-- Placeholder for the CA-decided Tally column mapping. Deliberately empty:
-- the schema is the chartered accountant's to specify, not ours to invent.
CREATE TABLE IF NOT EXISTS tally_map (
    id           INTEGER PRIMARY KEY,
    entity_code  TEXT NOT NULL REFERENCES entity(code),
    source_field TEXT NOT NULL,
    tally_field  TEXT NOT NULL,
    ledger_name  TEXT,
    note         TEXT,
    UNIQUE (entity_code, source_field)
);

CREATE TABLE IF NOT EXISTS setting (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    note  TEXT
);

-- ---------------------------------------------------------------- views

DROP VIEW IF EXISTS v_patient_revenue;
CREATE VIEW v_patient_revenue AS
-- MANAGEMENT VIEW, NOT AN ACCOUNT. Crosses entities on purpose.
SELECT
    p.id                       AS patient_ref_id,
    p.clinic_id                AS clinic_id,
    p.name                     AS name,
    s.unit                     AS unit,
    COUNT(*)                   AS line_count,
    MIN(e.business_date)       AS first_date,
    MAX(e.business_date)       AS last_date,
    SUM(s.amount_p)            AS revenue_p
FROM sale_item s
JOIN patient_ref p ON p.id = s.patient_ref_id
JOIN day_entry  e ON e.id = s.day_entry_id
GROUP BY p.id, s.unit;

DROP VIEW IF EXISTS v_day_attribution;
CREATE VIEW v_day_attribution AS
-- How much of each day's money is attributed to a named patient yet.
SELECT
    e.id                                   AS day_entry_id,
    e.unit                                 AS unit,
    e.business_date                        AS business_date,
    COALESCE((SELECT SUM(amount_p) FROM day_line  l WHERE l.day_entry_id = e.id), 0) AS day_total_p,
    COALESCE((SELECT SUM(amount_p) FROM sale_item s WHERE s.day_entry_id = e.id), 0) AS attributed_p
FROM day_entry e;

-- ---------------------------------------------------------------- seed

INSERT OR IGNORE INTO entity (code, legal_name, merchant_id, fy_start_month) VALUES
    ('medical', 'Sanjeevni Medicos',       '100000000312505', 4),
    ('clinic',  'Dr Manoj Agarwal Clinic', '100000000306941', 4),
    ('lab',     'Pathology',               NULL,              4);

UPDATE business_unit SET entity_code = code WHERE entity_code IS NULL;

INSERT OR IGNORE INTO patient_ref (clinic_id, name, note) VALUES
    ('WALK-IN', 'Walk-in / no clinic ID', 'reserved bucket — lines land here rather than being dropped or guessed');

INSERT OR IGNORE INTO setting (key, value, note) VALUES
    ('export.include_patient_names', '0',
     'Owner toggle (S179). 0 = accountant packs carry revenue lines only. 1 = include patient name + clinic ID.'),
    ('medical.entry_role', 'maker',   'pharmacy files the day'),
    ('medical.approve_role', 'checker', 'doctor approves; approval posts salary advances to the Staff Ledger'),
    ('missing_day.never_silent', '1',
     'S179 ruling: a missing day is NEVER suppressed — not for Sunday, not for absence. It stays pinned on the tile until filed.');

-- END OF SCHEMA v2 ADDITIONS

-- ============================================================================
--  SCHEMA v2.1 ADDITIONS  ·  Session 179 · step B2.1
--
--  Adds: per-unit maker/checker roles (Dr Bhawna checks lab + clinic) ·
--        monthly soft-copy reconciliation · month finalisation with an explicit
--        no-carry settlement · scan retirement to Google Drive after a month is
--        verified · deposit threshold · cash-with-whom.
--  Additive only. Nothing above is altered.
-- ============================================================================

-- ---------------------------------------------------------- who does what
-- Roles are PER UNIT. The doctor checks everything; Dr Bhawna checks lab and
-- clinic; each unit has its own maker. A role in one unit grants nothing in
-- another — cash books stay separate all the way down to permissions.

CREATE TABLE IF NOT EXISTS unit_role (
    id        INTEGER PRIMARY KEY,
    unit      TEXT NOT NULL REFERENCES business_unit(code),
    username  TEXT NOT NULL,                 -- SSO username
    role      TEXT NOT NULL CHECK (role IN ('maker','checker','viewer')),
    active    INTEGER NOT NULL DEFAULT 1,
    note      TEXT,
    UNIQUE (unit, username, role)
);
CREATE INDEX IF NOT EXISTS ix_unit_role_lookup ON unit_role(unit, username, active);

-- ------------------------------------------------- monthly reconciliation
-- The month's own soft copy — Sanjeevni's sale register export, the lab's
-- revenue statement. A month-level total from the source system is a far
-- stronger check than any per-day OCR, so this is the one that decides.

CREATE TABLE IF NOT EXISTS monthly_statement (
    id            INTEGER PRIMARY KEY,
    unit          TEXT NOT NULL REFERENCES business_unit(code),
    ym            TEXT NOT NULL,             -- 'YYYY-MM'
    kind          TEXT NOT NULL
                  CHECK (kind IN ('sale_register','lab_revenue','other')),
    filename      TEXT,
    path          TEXT,
    sha256        TEXT,
    stated_total_p INTEGER,                  -- the figure the soft copy asserts
    parsed_by     TEXT,                      -- 'manual' | 'sarvam' | 'xlsx'
    uploaded_by   TEXT,
    uploaded_at   TEXT,
    UNIQUE (unit, ym, kind)
);

-- ------------------------------------------------------ month finalisation
-- Finalising is the act that (a) freezes the month, (b) settles the drawer,
-- and (c) retires that month's scans. All three, or none — a half-closed month
-- is how evidence goes missing.

CREATE TABLE IF NOT EXISTS month_close (
    id                 INTEGER PRIMARY KEY,
    unit               TEXT NOT NULL REFERENCES business_unit(code),
    ym                 TEXT NOT NULL,
    status             TEXT NOT NULL DEFAULT 'open'
                       CHECK (status IN ('open','verified','finalised')),
    system_total_p     INTEGER,              -- what this system says the month earned
    statement_total_p  INTEGER,              -- what the soft copy says
    variance_p         INTEGER,
    residual_cash_p    INTEGER,              -- drawer at month end BEFORE settlement
    carry_policy       TEXT NOT NULL DEFAULT 'settle_to_zero'
                       CHECK (carry_policy IN ('settle_to_zero','carry')),
    settlement_note    TEXT,
    closed_by          TEXT,
    closed_at          TEXT,
    archive_status     TEXT NOT NULL DEFAULT 'pending'
                       CHECK (archive_status IN ('pending','moving','archived','failed','n/a')),
    archived_at        TEXT,
    UNIQUE (unit, ym)
);

-- Scans stop earning their keep once the month is verified. They move to the
-- connected Google Drive and the local copy goes. The ROW never goes — the
-- Drive file id lives here forever, so evidence is relocated, never lost.
CREATE TABLE IF NOT EXISTS archive_item (
    id             INTEGER PRIMARY KEY,
    attachment_id  INTEGER NOT NULL REFERENCES attachment(id) ON DELETE CASCADE,
    unit           TEXT NOT NULL,
    ym             TEXT NOT NULL,
    drive_folder   TEXT,
    drive_file_id  TEXT,
    sha256_before  TEXT,
    status         TEXT NOT NULL DEFAULT 'queued'
                   CHECK (status IN ('queued','moved','verified','failed')),
    local_deleted  INTEGER NOT NULL DEFAULT 0,
    error          TEXT,
    queued_at      TEXT,
    moved_at       TEXT,
    UNIQUE (attachment_id)
);
CREATE INDEX IF NOT EXISTS ix_archive_status ON archive_item(status, unit, ym);

-- ---------------------------------------------------------------- views

DROP VIEW IF EXISTS v_cash_custody;
CREATE VIEW v_cash_custody AS
-- "How much cash is sitting with Darpan right now." Attribution follows whoever
-- last manned the counter, which is exactly who the drawer is with.
SELECT
    l.unit                                   AS unit,
    l.business_date                          AS as_of,
    l.closing_p                              AS cash_p,
    e.manned_by                              AS custodian_staff_id,
    COALESCE(s.name, 'not recorded')         AS custodian_name
FROM v_cash_ledger l
JOIN day_entry e ON e.unit = l.unit AND e.business_date = l.business_date
LEFT JOIN staff_ref s ON s.id = e.manned_by
WHERE l.business_date = (SELECT MAX(business_date) FROM day_entry d WHERE d.unit = l.unit);

-- ---------------------------------------------------------------- seed

INSERT OR IGNORE INTO setting (key, value, note) VALUES
    ('medical.deposit_threshold_p', '5000000',
     'Prompt to deposit once cash in hand crosses this (paise). 50,00,000p = ₹50,000.'),
    ('clinic.deposit_threshold_p',  '3000000', 'Prompt threshold, clinic.'),
    ('lab.deposit_threshold_p',     '3000000', 'Prompt threshold, pathology.'),
    ('medical.carry_month_balance', '0',
     'S179 owner ruling: Sanjeevni month balances are NOT carried over; month close must settle the drawer or record an explicit reason. Set to 1 to restore carrying.'),
    ('retire_scans_on_finalise', '1',
     'On month finalisation the scans for that month move to the connected Google Drive and the local copy is deleted. The attachment row and the Drive file id are kept forever.'),
    ('archive.drive_root', 'ClinicFinanceArchive',
     'Google Drive folder; per-month subfolders <unit>/<YYYY-MM>/.');

-- Placeholder roster. REPLACE the usernames with real SSO usernames at install —
-- a role row keyed to a wrong username silently grants nothing, which fails quiet.
INSERT OR IGNORE INTO unit_role (unit, username, role, note) VALUES
    ('medical', 'darpan',    'maker',   'pharmacy files the day'),
    ('medical', 'manoj',     'checker', 'doctor approves medical'),
    ('clinic',  'reception', 'maker',   'reception files the clinic day'),
    ('clinic',  'manoj',     'checker', 'doctor approves clinic'),
    ('clinic',  'bhawna',    'checker', 'Dr Bhawna also checks clinic (S179)'),
    ('lab',     'labstaff',  'maker',   'lab staff file the pathology day'),
    ('lab',     'manoj',     'checker', 'doctor approves pathology'),
    ('lab',     'bhawna',    'checker', 'Dr Bhawna also checks pathology (S179)');

-- END OF SCHEMA v2.1 ADDITIONS

-- ============================================================================
--  SCHEMA v2.2 ADDITIONS  ·  Session 179 · step B2.2
--
--  Two owner corrections (S179):
--   (a) Cash is NOT swept at month end. It goes to the bank on the next trip,
--       which may be days later. So the drawer CARRIES across months, and the
--       deposit threshold + trip reminder are what actually drive banking.
--   (b) Some bills are raised at FULL VALUE with no cash across the counter —
--       home medicines, and medicines consumed in procedures. The sale is real
--       (revenue is booked) but the cash is not. Recording these is what makes
--       the drawer reconcile on those days.
--
--  Additive. Only the two ledger views are replaced, and only to subtract (b).
-- ============================================================================

-- Bills raised at full value against which no cash was collected.
-- REVENUE still counts (the sale happened); CASH does not (it did not arrive).
-- Conflating those two is exactly the kind of gap that ate ₹84,533 in the sheet.
CREATE TABLE IF NOT EXISTS day_noncash_bill (
    id             INTEGER PRIMARY KEY,
    day_entry_id   INTEGER NOT NULL REFERENCES day_entry(id) ON DELETE CASCADE,
    unit           TEXT NOT NULL REFERENCES business_unit(code),
    bill_date      TEXT NOT NULL,            -- ISO; usually the business date, not always
    head           TEXT NOT NULL
                   CHECK (head IN ('home_medicine','procedure_medicine','other')),
    head_text      TEXT,                     -- required when head='other'
    bill_no        TEXT NOT NULL,
    amount_p       INTEGER NOT NULL CHECK (amount_p > 0),
    patient_ref_id INTEGER REFERENCES patient_ref(id),
    status         TEXT NOT NULL DEFAULT 'open'
                   CHECK (status IN ('open','settled','written_off')),
    settled_ref    TEXT,
    settled_at     TEXT,
    note           TEXT,
    entered_by     TEXT,
    entered_at     TEXT,
    UNIQUE (unit, bill_no, bill_date)        -- one bill number cannot be claimed twice
);
CREATE INDEX IF NOT EXISTS ix_noncash_entry ON day_noncash_bill(day_entry_id);
CREATE INDEX IF NOT EXISTS ix_noncash_head  ON day_noncash_bill(unit, head, status);

-- ---------------------------------------------------------------- views

DROP VIEW IF EXISTS v_day_cash;
CREATE VIEW v_day_cash AS
SELECT
    e.id                AS day_entry_id,
    e.unit              AS unit,
    e.business_date     AS business_date,
    COALESCE((SELECT SUM(l.amount_p) FROM day_line l
               WHERE l.day_entry_id = e.id AND l.mode = 'cash'), 0)          AS cash_in_p,
    COALESCE((SELECT SUM(l.amount_p) FROM day_line l
               WHERE l.day_entry_id = e.id AND l.mode = 'upi'), 0)           AS upi_in_p,
    COALESCE((SELECT SUM(l.amount_p) FROM day_line l
               WHERE l.day_entry_id = e.id), 0)                              AS revenue_p,
    COALESCE((SELECT SUM(b.amount_p) FROM day_noncash_bill b
               WHERE b.day_entry_id = e.id), 0)                              AS noncash_p,
    COALESCE((SELECT SUM(x.amount_p) FROM day_expense x
               WHERE x.day_entry_id = e.id AND x.amount_known = 1), 0)       AS expense_p,
    COALESCE((SELECT SUM(m.amount_p) FROM cash_movement m
               WHERE m.day_entry_id = e.id AND m.direction = 'out'), 0)      AS cash_out_p,
    COALESCE((SELECT SUM(m.amount_p) FROM cash_movement m
               WHERE m.day_entry_id = e.id AND m.direction = 'in'), 0)       AS cash_back_p,
    COALESCE((SELECT SUM(a.amount_p) FROM cash_adjustment a
               WHERE a.day_entry_id = e.id), 0)                              AS adjust_p
FROM day_entry e;

DROP VIEW IF EXISTS v_cash_ledger;
CREATE VIEW v_cash_ledger AS
-- closing = opening + cash sale − bills raised without cash − expenses
--                   − cash taken out + cash brought back ± adjustment
SELECT
    unit, business_date, day_entry_id,
    cash_in_p, upi_in_p, revenue_p, noncash_p, expense_p, cash_out_p, cash_back_p, adjust_p,
    (cash_in_p - noncash_p - expense_p - cash_out_p + cash_back_p + adjust_p) AS net_p,
    COALESCE(SUM(cash_in_p - noncash_p - expense_p - cash_out_p + cash_back_p + adjust_p)
             OVER (PARTITION BY unit ORDER BY business_date, day_entry_id
                   ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING), 0)     AS opening_p,
    SUM(cash_in_p - noncash_p - expense_p - cash_out_p + cash_back_p + adjust_p)
             OVER (PARTITION BY unit ORDER BY business_date, day_entry_id
                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)         AS closing_p
FROM v_day_cash;

DROP VIEW IF EXISTS v_month_summary;
CREATE VIEW v_month_summary AS
SELECT
    unit,
    substr(business_date, 1, 7)                AS ym,
    COUNT(*)                                   AS days_recorded,
    SUM(revenue_p)                             AS revenue_p,
    SUM(cash_in_p)                             AS cash_p,
    SUM(upi_in_p)                              AS upi_p,
    SUM(noncash_p)                             AS noncash_p,
    SUM(expense_p)                             AS expense_p,
    SUM(cash_out_p)                            AS deposited_p,
    SUM(adjust_p)                              AS adjust_p
FROM v_day_cash
GROUP BY unit, ym;

DROP VIEW IF EXISTS v_noncash_by_head;
CREATE VIEW v_noncash_by_head AS
-- What the practice consumed rather than sold. Home medicines are effectively
-- drawings; procedure medicines are a clinic cost sitting inside pharmacy revenue.
-- Both are worth a number, and neither had one before.
SELECT
    b.unit                          AS unit,
    substr(e.business_date, 1, 7)   AS ym,
    b.head                          AS head,
    COUNT(*)                        AS bill_count,
    SUM(b.amount_p)                 AS amount_p
FROM day_noncash_bill b
JOIN day_entry e ON e.id = b.day_entry_id
GROUP BY b.unit, ym, b.head;

-- ---------------------------------------------------------------- settings

-- CORRECTED (S179): the drawer carries. Cash reaches the bank on the next trip,
-- which may be days later, so month end is not a sweep. What drives banking is
-- the threshold plus the trip reminder below.
UPDATE setting SET value = '1',
    note = 'CORRECTED S179: cash goes to the bank on the next trip, possibly days later, so the drawer carries across months. Month close records the carried balance; it does not demand a sweep.'
  WHERE key = 'medical.carry_month_balance';

INSERT OR IGNORE INTO setting (key, value, note) VALUES
    ('medical.deposit_trip_days', '7',
     'Remind about a bank trip when this many days have passed since the last deposit.'),
    ('clinic.carry_month_balance', '1', 'Drawer carries across months.'),
    ('lab.carry_month_balance',    '1', 'Drawer carries across months.');

-- END OF SCHEMA v2.2 ADDITIONS

-- ============================================================================
--  SCHEMA v3.0 ADDITIONS  ·  Session 179 · step B3a
--
--  Patient-wise sale lines, from a SWAPPABLE source.
--
--  Owner ruling (S179): "if sarvam isn't up to the mark we will export or pull
--  the sale report from Marg pharmacy software on the connected PC — same for
--  pathology, Labmate."
--
--  So the source is a CONFIGURED ADAPTER, never a hard-coded assumption:
--     sarvam_ocr  — OCR the scanned day report
--     marg_export — a file exported/pulled from Marg (pharmacy)
--     labmate_export — a file exported/pulled from Labmate (pathology)
--     tracker     — the follow-up tracker (clinic)
--     manual      — typed by hand
--  Switching source is a settings row plus a column map. It is not a rewrite,
--  and history from an old adapter stays valid and attributed to it.
-- ============================================================================

CREATE TABLE IF NOT EXISTS ingest_source (
    id            INTEGER PRIMARY KEY,
    unit          TEXT NOT NULL REFERENCES business_unit(code),
    adapter       TEXT NOT NULL
                  CHECK (adapter IN ('sarvam_ocr','marg_export','labmate_export',
                                     'tracker','manual','csv_generic')),
    label         TEXT,
    is_primary    INTEGER NOT NULL DEFAULT 0,
    active        INTEGER NOT NULL DEFAULT 1,
    config_json   TEXT,                    -- delimiter, sheet name, header row, date format…
    note          TEXT,
    UNIQUE (unit, adapter)
);

-- How a vendor file's columns map onto our fields. Filled in once the real Marg
-- and Labmate exports are in hand — a mapping row, not a code change.
CREATE TABLE IF NOT EXISTS ingest_column_map (
    id             INTEGER PRIMARY KEY,
    source_id      INTEGER NOT NULL REFERENCES ingest_source(id) ON DELETE CASCADE,
    our_field      TEXT NOT NULL
                   CHECK (our_field IN ('bill_no','bill_date','clinic_id','patient_name',
                                        'description','amount','mode','discount','tax')),
    their_column   TEXT NOT NULL,
    transform      TEXT,                   -- 'strip_rs' | 'ddmmyyyy' | 'negate' | NULL
    required       INTEGER NOT NULL DEFAULT 0,
    UNIQUE (source_id, our_field)
);

-- One run of one adapter over one day. Every line traces back to a batch, and
-- every batch records what it was fed and what came out.
CREATE TABLE IF NOT EXISTS ingest_batch (
    id             INTEGER PRIMARY KEY,
    day_entry_id   INTEGER NOT NULL REFERENCES day_entry(id) ON DELETE CASCADE,
    unit           TEXT NOT NULL,
    adapter        TEXT NOT NULL,
    source_ref     TEXT,                   -- filename / attachment id / tracker query
    sha256         TEXT,
    rows_read      INTEGER NOT NULL DEFAULT 0,
    rows_accepted  INTEGER NOT NULL DEFAULT 0,
    rows_review    INTEGER NOT NULL DEFAULT 0,
    total_p        INTEGER NOT NULL DEFAULT 0,
    status         TEXT NOT NULL DEFAULT 'ok'
                   CHECK (status IN ('ok','partial','failed','superseded')),
    error          TEXT,
    run_by         TEXT,
    run_at         TEXT
);
CREATE INDEX IF NOT EXISTS ix_ingest_batch_day ON ingest_batch(day_entry_id, status);

ALTER TABLE sale_item ADD COLUMN ingest_batch_id INTEGER REFERENCES ingest_batch(id);
ALTER TABLE sale_item_review ADD COLUMN ingest_batch_id INTEGER REFERENCES ingest_batch(id);
ALTER TABLE sale_item_review ADD COLUMN reason TEXT;

-- ---------------------------------------------------------------- views

DROP VIEW IF EXISTS v_day_attribution;
CREATE VIEW v_day_attribution AS
-- How much of a day's money is attributed to a named patient yet, and how much
-- is still sitting in the review queue. Attribution NEVER moves the books —
-- the day total is settled by day_line and the bank. This view only reports
-- how far the naming has got.
SELECT
    e.id                                   AS day_entry_id,
    e.unit                                 AS unit,
    e.business_date                        AS business_date,
    COALESCE((SELECT SUM(amount_p) FROM day_line  l WHERE l.day_entry_id = e.id), 0) AS day_total_p,
    COALESCE((SELECT SUM(amount_p) FROM sale_item s WHERE s.day_entry_id = e.id), 0) AS attributed_p,
    COALESCE((SELECT SUM(amount_p) FROM sale_item_review r
               WHERE r.day_entry_id = e.id AND r.status = 'open'), 0)                AS in_review_p,
    COALESCE((SELECT COUNT(*) FROM sale_item_review r
               WHERE r.day_entry_id = e.id AND r.status = 'open'), 0)                AS in_review_count
FROM day_entry e;

-- ---------------------------------------------------------------- seed

INSERT OR IGNORE INTO ingest_source (unit, adapter, label, is_primary, active, note) VALUES
    ('medical', 'sarvam_ocr',     'Sarvam OCR of the scanned day sale report', 1, 1,
     'Primary until proven on real bills. Demote if accuracy is poor.'),
    ('medical', 'marg_export',    'Marg pharmacy software export (connected PC)', 0, 0,
     'Preferred fallback per owner. Column map to be filled from a real Marg file.'),
    ('lab',     'sarvam_ocr',     'Sarvam OCR of the lab statement', 1, 1, NULL),
    ('lab',     'labmate_export', 'Labmate export (connected PC)', 0, 0,
     'Preferred fallback per owner. Column map to be filled from a real Labmate file.'),
    ('clinic',  'tracker',        'Follow-up tracker, already patient-wise', 1, 1,
     'Clinic revenue is read, not typed.');

INSERT OR IGNORE INTO setting (key, value, note) VALUES
    ('ingest.attribution_tolerance_p', '10000',
     'Open a line_sum_vs_day_total exception when attributed lines differ from the day total by more than this (paise). 10000p = Rs 100.'),
    ('ingest.min_confidence', '0.70',
     'Below this confidence a line goes to the review queue instead of straight into sale_item.');

-- END OF SCHEMA v3.0 ADDITIONS

-- ============================================================================
--  SCHEMA v3.1  ·  Session 179 · step B3b — scanner mount + tile naming
--  The clinic's existing refined scanner widget is REUSED, never re-implemented.
--  Its URL and global are settings so the exact path is confirmed at install
--  rather than guessed here (F-66: a path is not provenance).
-- ============================================================================

INSERT OR IGNORE INTO setting (key, value, note) VALUES
    ('scanner.widget_url', '',
     'URL of the existing clinic scanner widget JS, served same-origin. Set at install after confirming the live path. Empty = the scan buttons say so instead of pretending.'),
    ('scanner.global', 'ClinicScanner',
     'Global object the widget exposes; .open({docType, uploadUrl, onDone}) is called.'),
    ('tile.maker_title', 'Daily Sale',
     'Portal tile label for the pharmacy. Deliberately NOT "Finance" — it names the job, not the department (S179).'),
    ('tile.maker_subtitle', 'Enter today''s shop sale', 'One line under the maker tile.'),
    ('tile.checker_title', 'Sanjeevni', 'Portal tile label for the doctor.'),
    ('tile.checker_subtitle', 'Review, approve, month close', 'One line under the checker tile.');

-- END OF SCHEMA v3.1

-- ============================================================================
--  SCHEMA v3.2  ·  Session 179 · parked cash and how a deposit clears it
--
--  Owner's rule (S179): a bank trip happens days after month end, so ONE deposit
--  carries the old month's parked cash plus the new month's takings. Record only
--  the OLD month's share; the rest is by definition the current month's.
--
--  The movement stays WHOLE — one row, one slip, one date, matching the bank
--  statement exactly. Splitting it would make the ledger disagree with the bank,
--  and that agreement is the whole basis of trusting this system.
-- ============================================================================

ALTER TABLE cash_movement ADD COLUMN clears_ym TEXT;            -- 'YYYY-MM' being settled
ALTER TABLE cash_movement ADD COLUMN clears_amount_p INTEGER;   -- how much of this deposit is that month's
ALTER TABLE cash_movement ADD COLUMN cleared_by TEXT;
ALTER TABLE cash_movement ADD COLUMN cleared_at TEXT;
CREATE INDEX IF NOT EXISTS ix_cash_movement_clears ON cash_movement(clears_ym);

DROP VIEW IF EXISTS v_month_parked;
CREATE VIEW v_month_parked AS
-- For every finalised month: what stayed in the drawer, how much of it has since
-- reached the bank, and what is still sitting there. A month can honestly be
-- "closed but not yet banked" — a state the spreadsheet could never express.
SELECT
    mc.unit                                        AS unit,
    mc.ym                                          AS ym,
    mc.status                                      AS status,
    mc.closed_at                                   AS closed_at,
    COALESCE(mc.residual_cash_p, 0)                AS parked_p,
    COALESCE((SELECT SUM(m.clears_amount_p) FROM cash_movement m
               WHERE m.clears_ym = mc.ym
                 AND m.day_entry_id IN (SELECT id FROM day_entry WHERE unit = mc.unit)), 0)
                                                   AS cleared_p,
    COALESCE(mc.residual_cash_p, 0) -
    COALESCE((SELECT SUM(m.clears_amount_p) FROM cash_movement m
               WHERE m.clears_ym = mc.ym
                 AND m.day_entry_id IN (SELECT id FROM day_entry WHERE unit = mc.unit)), 0)
                                                   AS outstanding_p
FROM month_close mc
WHERE mc.status = 'finalised';

INSERT OR IGNORE INTO setting (key, value, note) VALUES
    ('parked_cash.nag_days', '21',
     'Shout when a finalised month still has cash parked in the drawer after this many days. Ageing cash deserves a nudge whether or not it crosses the deposit threshold.');

-- END OF SCHEMA v3.2
