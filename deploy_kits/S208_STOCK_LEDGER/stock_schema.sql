-- ---------------------------------------------------------------------------
-- S207 · the stock loop: expected -> counted -> difference -> cause -> closed
--
-- Lives in the SAME finance.db as everything else. One database, one backup,
-- one auth table. A second store would mean a second backup nobody takes.
--
-- THE IDEA THIS SCHEMA EXISTS FOR
--   Stock leaves the shop by several doors: it is sold, returned to a vendor,
--   issued for clinic use, thrown away expired, broken, or it simply goes.
--   Marg records the first two well. The rest leave no trace until a physical
--   count finds the hole, and by then nobody remembers which door.
--   So: capture the difference the DAY it is found, name the door while the
--   memory is fresh, and keep it open until Marg agrees again.
-- ---------------------------------------------------------------------------

-- A counting session. Pinned to a sale bill so a mid-day count still
-- reconciles: everything sold after that bill is not the counter's problem.
CREATE TABLE IF NOT EXISTS stock_count (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  unit          TEXT NOT NULL DEFAULT 'medical',
  marg_as_on    TEXT NOT NULL,           -- date of the Marg export counted against
  bill_no       TEXT NOT NULL,           -- last sale bill at the moment of counting
  bill_date     TEXT NOT NULL,
  started_at    TEXT NOT NULL,
  submitted_at  TEXT,
  submitted_by  TEXT,
  items_total   INTEGER NOT NULL DEFAULT 0,
  items_counted INTEGER NOT NULL DEFAULT 0,
  status        TEXT NOT NULL DEFAULT 'open'   -- open | submitted
);

-- One row per item actually counted. marg_qty is copied in, not looked up
-- later: the expected figure must be the one the counter was shown, or the
-- difference is measured against a number nobody saw.
CREATE TABLE IF NOT EXISTS stock_count_item (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  count_id    INTEGER NOT NULL REFERENCES stock_count(id),
  item        TEXT NOT NULL,
  packing     TEXT,
  pack_size   INTEGER NOT NULL DEFAULT 1,
  marg_qty    INTEGER NOT NULL,
  counted_qty INTEGER NOT NULL,
  strips      INTEGER,
  loose       INTEGER,
  counted_by  TEXT,
  entered_by  TEXT,
  at          TEXT NOT NULL,
  batches     TEXT,                       -- JSON {batch: qty}, or NULL
  UNIQUE(count_id, item)
);
CREATE INDEX IF NOT EXISTS ix_sci_item ON stock_count_item(item);

-- THE LEDGER THIS IS ALL FOR. One row per difference found, and it stays open
-- until Marg's own numbers agree again. `cause` is the door it went out of.
CREATE TABLE IF NOT EXISTS stock_diff (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  count_id       INTEGER NOT NULL REFERENCES stock_count(id),
  item           TEXT NOT NULL,
  found_on       TEXT NOT NULL,           -- the count's marg_as_on
  marg_qty       INTEGER NOT NULL,
  counted_qty    INTEGER NOT NULL,
  diff           INTEGER NOT NULL,        -- counted - marg; negative = short
  pack_size      INTEGER NOT NULL DEFAULT 1,
  value_p        INTEGER,                 -- paise, at last known purchase rate
  cause          TEXT NOT NULL DEFAULT 'UNEXPLAINED',
  cause_note     TEXT,
  cause_by       TEXT,
  cause_at       TEXT,
  status         TEXT NOT NULL DEFAULT 'open',   -- open | reconciled
  closed_as_on   TEXT,                    -- the export that agreed
  closed_at      TEXT,
  counted_by     TEXT
);
CREATE INDEX IF NOT EXISTS ix_sd_status ON stock_diff(status);
CREATE INDEX IF NOT EXISTS ix_sd_item   ON stock_diff(item);
CREATE INDEX IF NOT EXISTS ix_sd_found  ON stock_diff(found_on);

-- Every Marg closing-stock export we have seen, item by item. This is what
-- closes a difference automatically: when a later export shows the quantity
-- the counter reported, the hole was fixed in Marg and nobody has to remember
-- to tick it off.
CREATE TABLE IF NOT EXISTS stock_snapshot (
  as_on     TEXT NOT NULL,
  item      TEXT NOT NULL,
  qty       INTEGER NOT NULL,
  packing   TEXT,
  pack_size INTEGER NOT NULL DEFAULT 1,
  loaded_at TEXT NOT NULL,
  source    TEXT,
  PRIMARY KEY (as_on, item)
);

-- Last known purchase rate per item, so a loss can be priced. Kept separate
-- from the count so a missing rate never blocks a count being recorded.
CREATE TABLE IF NOT EXISTS stock_rate (
  item      TEXT PRIMARY KEY,
  rate_p    INTEGER NOT NULL,             -- paise per unit
  pack_size INTEGER NOT NULL DEFAULT 1,
  as_of     TEXT,
  source    TEXT
);
