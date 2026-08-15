-- =============================================================================
--  finance_returns.sql   ·  Session 180 · item U3
--
--  PURPOSE
--    Give drug-level lines a home, so a sale return can be traced back to the
--    sale it came from.
--
--  WHY A NEW TABLE
--    sale_item is BILL-level: one row per bill, being one patient-attribution
--    line. There is nowhere in the current schema to put "which medicines were
--    on this bill". Without that, a return can be matched to a PATIENT but the
--    match cannot be corroborated — and on the real six-day sample, medicine
--    overlap was the difference between a probable match and a conclusive one
--    (CN00158 returned six items and all six were on that patient's earlier
--    sale).
--
--  WHAT IT CHANGES
--    ADDITIVE ONLY. One new table and its indexes, all CREATE ... IF NOT
--    EXISTS. No existing table is altered. No existing row is read, written or
--    deleted. No view changes. Re-running this file is a no-op.
--
--  ROLLBACK
--    DROP TABLE IF EXISTS sale_line_item;
--    Nothing else in the schema references it, so dropping it cannot cascade.
--
--  APPLY
--    python3 -c "import sqlite3;c=sqlite3.connect('finance.db');
--                c.executescript(open('finance_returns.sql').read());c.commit()"
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS sale_line_item (
    id              INTEGER PRIMARY KEY,
    day_entry_id    INTEGER NOT NULL REFERENCES day_entry(id) ON DELETE CASCADE,
    ingest_batch_id INTEGER REFERENCES ingest_batch(id),
    unit            TEXT NOT NULL REFERENCES business_unit(code),

    business_date   TEXT NOT NULL,          -- ISO; denormalised so the lookup
                                            -- never has to join to find a date
    bill_no         TEXT NOT NULL,          -- links to sale_item.source_ref
    is_return       INTEGER NOT NULL DEFAULT 0 CHECK (is_return IN (0, 1)),

    seq             INTEGER,                -- line number within the bill
    item_name       TEXT NOT NULL,          -- as printed
    item_key        TEXT NOT NULL,          -- normalised, for matching only
    pack            TEXT,
    qty_raw         TEXT,                   -- 'strips:loose' as Marg prints it
    amount_p        INTEGER CHECK (amount_p IS NULL OR amount_p >= 0),
    expiry_ym       TEXT,                   -- 'YYYY-MM'
    batch           TEXT,

    UNIQUE (unit, bill_no, seq)             -- a re-run replaces, never duplicates
);

CREATE INDEX IF NOT EXISTS ix_sli_bill  ON sale_line_item (unit, bill_no);
CREATE INDEX IF NOT EXISTS ix_sli_key   ON sale_line_item (unit, item_key);
CREATE INDEX IF NOT EXISTS ix_sli_day   ON sale_line_item (day_entry_id);
CREATE INDEX IF NOT EXISTS ix_sli_date  ON sale_line_item (unit, business_date);

-- Settings, inserted only if absent so an owner's later change is never undone.
INSERT OR IGNORE INTO setting (key, value, note) VALUES
 ('returns.window_days', '30', 'A sale return is expected within this many days of the original sale. Outside it the return is FLAGGED for review — never refused by the system.'),
 ('returns.expiry_grace_months', '0', 'A returned item is flagged if its expiry month is this many months away or closer. 0 = flag only at or past expiry.'),
 ('returns.large_p', '100000', 'A return at or above this value (in paise) that could not be matched to an earlier sale is flagged. Default Rs 1,000.');

COMMIT;
