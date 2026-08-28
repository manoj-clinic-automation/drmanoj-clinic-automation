-- returns_schema.sql -- the purchase-return lifecycle, inside finance.db.
--
-- WHY A CUSTODY TRAIL AND NOT JUST A STATUS COLUMN
--     A purchase return is the one transaction where the goods leave the
--     building BEFORE the paperwork exists.  Between "set aside" and "credit
--     note entered" the stock is off our shelf, off Marg's books in nobody's
--     account, and in the hands of a person whose name nobody wrote down.
--     Five months of history: five returns, Rs 6,919, one of them Rs 4,042.
--     An uncredited return is a straight loss and there is currently no record
--     that would let anyone chase one.
--
--     So every hand-off is a row, not an edit.  pret_event is append-only:
--     who did what, when, and what they said.  The status on the header is a
--     cache of the newest event and is always rebuildable from the trail.
--
-- Idempotent.  Safe on every boot.  sqlite3 only.

CREATE TABLE IF NOT EXISTS pret (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  ref           TEXT    NOT NULL UNIQUE,   -- PR-2026-0001, printed on the slip
  vendor        TEXT,                      -- may be blank: an unrecorded return
  status        TEXT    NOT NULL DEFAULT 'BOOKED',
  booked_on     TEXT    NOT NULL,          -- yyyy-mm-dd IST
  booked_by     TEXT    NOT NULL,
  notified_on   TEXT,
  notified_by   TEXT,
  reception_on  TEXT,
  reception_by  TEXT,                      -- the named person who took custody
  handed_on     TEXT,
  handed_by     TEXT,                      -- our person who handed it over
  collector     TEXT,                      -- their person who took it away
  collector_ph  TEXT,
  note_no       TEXT,                      -- vendor credit note, when it lands
  note_on       TEXT,
  closed_on     TEXT,
  closed_by     TEXT,
  value_p       INTEGER,                   -- paise, our own estimate at booking
  chase_muted   INTEGER NOT NULL DEFAULT 0,
  created_at    TEXT    NOT NULL,
  updated_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS pret_line (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  pret_id       INTEGER NOT NULL REFERENCES pret(id),
  item          TEXT    NOT NULL,
  batch         TEXT,
  expiry        TEXT,                      -- mm/yyyy as Marg prints it
  qty           INTEGER NOT NULL,          -- base units, never strips
  pack_size     INTEGER NOT NULL DEFAULT 1,
  packing       TEXT,
  reason        TEXT    NOT NULL DEFAULT 'NEAR_EXPIRY',
  rate_p        INTEGER,
  purchase_bill TEXT,                      -- optional, as ruled
  matched_qty   INTEGER NOT NULL DEFAULT 0,
  created_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS pret_event (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  pret_id       INTEGER NOT NULL REFERENCES pret(id),
  at            TEXT    NOT NULL,
  actor         TEXT    NOT NULL,          -- the login that recorded it
  person        TEXT,                      -- the person it is ABOUT, if different
  kind          TEXT    NOT NULL,
  detail        TEXT
);

-- What Marg's credit notes said, so a match is evidence and not a memory.
CREATE TABLE IF NOT EXISTS pret_credit (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  vendor        TEXT,
  item          TEXT    NOT NULL,
  batch         TEXT,
  qty           INTEGER NOT NULL,
  note_no       TEXT,
  note_on       TEXT,
  value_p       INTEGER,
  source        TEXT,
  loaded_at     TEXT    NOT NULL,
  used_by       INTEGER REFERENCES pret_line(id)
);

CREATE INDEX IF NOT EXISTS ix_pret_status  ON pret(status);
CREATE INDEX IF NOT EXISTS ix_pret_vendor  ON pret(vendor);
CREATE INDEX IF NOT EXISTS ix_pline_pret   ON pret_line(pret_id);
CREATE INDEX IF NOT EXISTS ix_pline_item   ON pret_line(item, batch);
CREATE INDEX IF NOT EXISTS ix_pevent_pret  ON pret_event(pret_id, at);
CREATE INDEX IF NOT EXISTS ix_pcred_match  ON pret_credit(item, batch, used_by);
