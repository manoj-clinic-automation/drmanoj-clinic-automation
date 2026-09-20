-- S359: the cash_movement table and the three cash views exactly as the 20-Sep nightly finance.db defines them (the selftest's scratch shape)
CREATE TABLE cash_movement (
    id                 INTEGER PRIMARY KEY,
    day_entry_id       INTEGER NOT NULL REFERENCES day_entry(id) ON DELETE CASCADE,
    direction          TEXT NOT NULL CHECK (direction IN ('out','in')),
    party              TEXT NOT NULL CHECK (party IN ('bank','dr_manoj','dr_bhawna','other')),
    amount_p           INTEGER NOT NULL CHECK (amount_p > 0),
    reference          TEXT,
    slip_attachment_id INTEGER REFERENCES attachment(id)
, clears_ym TEXT, clears_amount_p INTEGER, cleared_by TEXT, cleared_at TEXT);
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
