-- =============================================================================
--  finance_migration_S180_returns.sql   ·  Session 180
--
--  PURPOSE
--    Let sale returns (Marg credit notes) count in patient attribution.
--
--  WHAT IT CHANGES
--    ONE VIEW.  v_day_attribution is redefined so that a sale_item whose
--    service ends in "_return" subtracts from attributed_p instead of adding
--    to it.
--
--  WHAT IT DOES NOT CHANGE
--    No table is created, altered, rebuilt or dropped.  No row is written,
--    updated or deleted.  sale_item.amount_p keeps its CHECK (amount_p >= 0)
--    constraint, so no data migration is needed and there is nothing to
--    roll back but the view itself.
--
--  WHY NOT SIMPLY ALLOW NEGATIVE AMOUNTS
--    Because sale_item.amount_p is declared CHECK (amount_p >= 0) and SQLite
--    cannot drop a CHECK constraint with ALTER TABLE.  Removing it would mean
--    create-copy-drop-rename on a live table holding 121 days of real patient
--    data — a data migration, with everything that implies — in order to
--    change a reporting behaviour.  Storing the magnitude and marking the
--    direction in "service" honours the invariant the schema author chose
--    (amounts are magnitudes; direction is the row's type) and touches no data.
--
--  ROLLBACK
--    Re-run the ORIGINAL view definition, kept verbatim at the foot of this
--    file.  Views hold no data; swapping back is instant and lossless.
--
--  APPLY
--    sqlite3 finance.db < finance_migration_S180_returns.sql
--    then:  finance_ingest.py finance.db      (selftest, on a throwaway copy)
-- =============================================================================

BEGIN;

DROP VIEW IF EXISTS v_day_attribution;

CREATE VIEW v_day_attribution AS
-- How much of a day's money is attributed to a named patient yet, and how much
-- is still sitting in the review queue. Attribution NEVER moves the books —
-- the day total is settled by day_line and the bank. This view only reports
-- how far the naming has got.
--
-- S180: a sale return is stored with a positive amount_p and a service of
-- "<base>_return" (pharmacy_return / lab_test_return). It must SUBTRACT here,
-- or a day with a refund would look over-attributed by twice the refund.
SELECT
    e.id                                   AS day_entry_id,
    e.unit                                 AS unit,
    e.business_date                        AS business_date,
    COALESCE((SELECT SUM(amount_p) FROM day_line  l WHERE l.day_entry_id = e.id), 0) AS day_total_p,
    COALESCE((SELECT SUM(CASE WHEN s.service GLOB '*_return'
                              THEN -s.amount_p ELSE s.amount_p END)
                FROM sale_item s WHERE s.day_entry_id = e.id), 0)                    AS attributed_p,
    COALESCE((SELECT SUM(amount_p) FROM sale_item_review r
               WHERE r.day_entry_id = e.id AND r.status = 'open'), 0)                AS in_review_p,
    COALESCE((SELECT COUNT(*) FROM sale_item_review r
               WHERE r.day_entry_id = e.id AND r.status = 'open'), 0)                AS in_review_count
FROM day_entry e;

COMMIT;

-- =============================================================================
--  ROLLBACK — the definition exactly as it stood before S180.
--  Paste and run only if the change has to be undone.
-- =============================================================================
--
-- BEGIN;
-- DROP VIEW IF EXISTS v_day_attribution;
-- CREATE VIEW v_day_attribution AS
-- SELECT
--     e.id                                   AS day_entry_id,
--     e.unit                                 AS unit,
--     e.business_date                        AS business_date,
--     COALESCE((SELECT SUM(amount_p) FROM day_line  l WHERE l.day_entry_id = e.id), 0) AS day_total_p,
--     COALESCE((SELECT SUM(amount_p) FROM sale_item s WHERE s.day_entry_id = e.id), 0) AS attributed_p,
--     COALESCE((SELECT SUM(amount_p) FROM sale_item_review r
--                WHERE r.day_entry_id = e.id AND r.status = 'open'), 0)                AS in_review_p,
--     COALESCE((SELECT COUNT(*) FROM sale_item_review r
--                WHERE r.day_entry_id = e.id AND r.status = 'open'), 0)                AS in_review_count
-- FROM day_entry e;
-- COMMIT;
