-- ---------------------------------------------------------------------------
-- S243 SNAPSHOT SOURCE -- stock_expected: our own COMPUTED stock, keyed like
-- stock_snapshot, kept apart from it.
--
-- Until S243 push_expected.py (source "push_expected base=.. pur_to=..", as_on =
-- the last sale date) and push_snapshot.py (source "push_snapshot", Marg's real
-- closing stock) both upserted stock_snapshot on (as_on, item). The later one
-- silently became "Marg's figure" for the count page, reconcile() and the pad.
-- From S243 the computed feed lands here. stock_snapshot = Marg only.
--
-- Identical to the EXPECTED_SCHEMA string inside stock_app.py, which creates
-- the table on first computed push anyway; applying this file first is the
-- installer's belt to that brace. Idempotent: safe to run any number of times.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stock_expected (
  as_on     TEXT NOT NULL,
  item      TEXT NOT NULL,
  qty       INTEGER NOT NULL,
  packing   TEXT,
  pack_size INTEGER NOT NULL DEFAULT 1,
  loaded_at TEXT NOT NULL,
  source    TEXT,
  PRIMARY KEY (as_on, item)
);
CREATE INDEX IF NOT EXISTS idx_expected_item ON stock_expected(item, as_on);
