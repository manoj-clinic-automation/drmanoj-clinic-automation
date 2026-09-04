-- =============================================================================
--  purchase_schema.sql  ·  S224_MARG_PURCHASES
--
--  Marg's purchase exports, pushed from manojz, kept on the box: the bills, the
--  item lines, a month's status, the owner's verdicts, the scan links, the
--  order book and the feed's own health. ADDITIVE ONLY -- every statement is
--  CREATE ... IF NOT EXISTS, run lazily on first request (F-303), never at
--  import. Nothing here touches any other table in finance.db.
--
--  Money is integer PAISE throughout. Dates are ISO yyyy-mm-dd. month is yyyy-mm.
-- =============================================================================

CREATE TABLE IF NOT EXISTS purchase_export (
  md5            TEXT PRIMARY KEY,          -- of the archived Marg file
  type           TEXT NOT NULL,             -- ITEMWISE | BILLWISE | SUPPLIERWISE | BILLITEMWISE
  file           TEXT NOT NULL,
  period_from    TEXT NOT NULL,
  period_to      TEXT NOT NULL,
  export_stamp   TEXT NOT NULL,             -- YYYYMMDD-HHMMSS as Marg named it
  received_at    TEXT NOT NULL,
  n_rows         INTEGER NOT NULL DEFAULT 0,
  grand_amount_p INTEGER,
  superseded_by  TEXT                       -- md5 of the later export of the SAME type+period
);

-- One row per Marg purchase bill. Identity is (supplier_norm, bill_no); the date
-- comes from BILLWISE first, SUPPLIERWISE second (date_src records which).
-- bw_md5 / sw_md5 remember which export of each type last carried the bill, so
-- a bill stays EFFECTIVE while either of them is un-superseded.
CREATE TABLE IF NOT EXISTS purchase_bill (
  id             INTEGER PRIMARY KEY,
  supplier_norm  TEXT NOT NULL,
  supplier       TEXT NOT NULL,
  bill_no        TEXT NOT NULL,
  bill_date      TEXT,
  month          TEXT,
  cash_p         INTEGER NOT NULL DEFAULT 0,
  credit_p       INTEGER NOT NULL DEFAULT 0,
  amount_p       INTEGER NOT NULL DEFAULT 0,
  source_md5     TEXT,
  bw_md5         TEXT,
  sw_md5         TEXT,
  date_src       TEXT,                      -- BILLWISE | SUPPLIERWISE
  verdict        TEXT,                      -- NULL | CORRECT | WRONG
  verdict_by     TEXT,
  verdict_at     TEXT,
  wrong_amount_p INTEGER,
  reason         TEXT,
  scan_bill_id   INTEGER,
  UNIQUE (supplier_norm, bill_no, bill_date)
);
CREATE INDEX IF NOT EXISTS ix_pb_month ON purchase_bill(month);
CREATE INDEX IF NOT EXISTS ix_pb_key   ON purchase_bill(supplier_norm, bill_no);

-- One row per ITEMWISE / BILLITEMWISE line, owned by its export (source_md5).
CREATE TABLE IF NOT EXISTS purchase_line (
  id              INTEGER PRIMARY KEY,
  supplier_norm   TEXT,
  bill_no         TEXT,
  bill_date       TEXT,                     -- NULL = could not be dated
  month           TEXT,
  item            TEXT NOT NULL,
  packing         TEXT,
  batch           TEXT,
  expiry          TEXT,
  tax             REAL,
  qty             REAL,
  free            REAL,
  rate_p          INTEGER,
  discount_pct    REAL,
  amount_p        INTEGER,
  net_rate_p      INTEGER,
  net_amount_p    INTEGER,
  loose_qty       REAL,
  purchase_rate_p INTEGER,
  direction       TEXT,
  source_md5      TEXT NOT NULL,
  line_type       TEXT NOT NULL DEFAULT 'ITEMWISE'
);
CREATE INDEX IF NOT EXISTS ix_pl_src   ON purchase_line(source_md5);
CREATE INDEX IF NOT EXISTS ix_pl_bill  ON purchase_line(supplier_norm, bill_no, bill_date);
CREATE INDEX IF NOT EXISTS ix_pl_month ON purchase_line(month);
CREATE INDEX IF NOT EXISTS ix_pl_item  ON purchase_line(item);

CREATE TABLE IF NOT EXISTS purchase_month (
  month            TEXT PRIMARY KEY,
  status           TEXT NOT NULL DEFAULT 'provisional',   -- provisional | final
  finalised_by     TEXT,
  finalised_at     TEXT,
  billwise_total_p INTEGER,
  itemwise_total_p INTEGER,
  note             TEXT
);

CREATE TABLE IF NOT EXISTS purchase_order (
  id         INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL,
  created_by TEXT NOT NULL,
  vendor     TEXT NOT NULL,
  status     TEXT NOT NULL DEFAULT 'draft',   -- draft | sent | received | cancelled
  note       TEXT,
  total_p    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS purchase_order_line (
  id          INTEGER PRIMARY KEY,
  order_id    INTEGER NOT NULL REFERENCES purchase_order(id),
  item        TEXT NOT NULL,
  packs       INTEGER NOT NULL DEFAULT 0,
  pack_size   INTEGER NOT NULL DEFAULT 1,
  units       INTEGER NOT NULL DEFAULT 0,
  rate_p      INTEGER,
  value_p     INTEGER,
  on_hand     INTEGER,
  per_day     REAL,
  cover_after REAL
);

-- Vendor phones, pushed from manojz's own config. Lives HERE only (F-185).
CREATE TABLE IF NOT EXISTS purchase_vendor_contact (
  vendor_norm TEXT PRIMARY KEY,
  vendor      TEXT NOT NULL,
  phone       TEXT,
  updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS purchase_scan_link (
  bill_id       INTEGER PRIMARY KEY,        -- purchase_bill.id
  asset_bill_id INTEGER NOT NULL,           -- assets.db bills.id
  grade         TEXT NOT NULL,              -- EXACT | PROBABLE | NONE
  matched_on    TEXT,
  linked_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS purchase_feed (
  id           INTEGER PRIMARY KEY,
  at           TEXT NOT NULL,
  host         TEXT,
  pull_last    TEXT,
  pull_age_min INTEGER,
  state        TEXT
);

CREATE TABLE IF NOT EXISTS purchase_audit (
  id     INTEGER PRIMARY KEY,
  at     TEXT NOT NULL,
  who    TEXT NOT NULL,
  action TEXT NOT NULL,
  ref    TEXT,
  detail TEXT
);
