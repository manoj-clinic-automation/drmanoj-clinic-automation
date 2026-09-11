-- ===========================================================================
--  marg_spine_schema.sql  --  S229, 07-Sep-2026
--
--  THE ITEM SPINE.  One row per real product, and everything else references
--  it rather than defining its own idea of what an item is.
--
--  WHY THIS EXISTS
--      Before this, item identity lived in at least six places -- the shelf,
--      the snapshot, the sale lines, the purchase lines, the salt table and
--      the rate table -- and each answered "which product is this?" privately.
--      Measured on 07-Sep-2026: 407 distinct product names for a shelf of 373,
--      and 515 sale lines worth Rs 95,611.93 that tied to no shelf item at all.
--
--  EVERY TABLE HERE IS NEW.  Nothing existing is altered, renamed or dropped.
--  Every statement is IF NOT EXISTS, so the file is safe to run twice.
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- 1 - THE SPINE.  One row per product.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marg_item (
    item_id        INTEGER PRIMARY KEY,
    canonical      TEXT    NOT NULL,          -- normalised; the name we call it
    canonical_raw  TEXT    NOT NULL,          -- exactly as Marg spells it today
    status         TEXT    NOT NULL DEFAULT 'active',   -- active|merged|retired
    merged_into    INTEGER,                   -- set only when status='merged'
    origin         TEXT    NOT NULL,          -- shelf_seed|purchase_first|snapshot|manual
    first_seen     TEXT,
    created_at     TEXT    NOT NULL,
    FOREIGN KEY (merged_into) REFERENCES marg_item(item_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_marg_item_canonical ON marg_item(canonical);
CREATE INDEX IF NOT EXISTS ix_marg_item_status ON marg_item(status);

-- ---------------------------------------------------------------------------
-- 2 - EVERY NAME THE PRODUCT HAS EVER WORN.
--     This is the column that repays the whole exercise: the moment a clipped
--     or renamed spelling is recorded here, its history reattaches itself.
--     kind:
--       canonical       the current Marg name
--       truncation      the 20-character clip Marg's sale report prints
--       pending_rename  a rename agreed but not yet done in Marg (S229: 24)
--       historical      a name Marg used before a rename that has been done
--       merged          the name of a record merged away
--       parsed          a form our own parser produced (the 'N ***' fault)
--       zz              Marg's deactivation prefix
--     A name row NEVER moves between items.  If a name turns out to belong to
--     another item, the old row is retired (active=0) and a new one written,
--     so the record of what we once believed survives.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marg_item_name (
    name       TEXT    NOT NULL,              -- normalised, the lookup key
    item_id    INTEGER NOT NULL,
    name_raw   TEXT    NOT NULL,
    kind       TEXT    NOT NULL,
    active     INTEGER NOT NULL DEFAULT 1,
    note       TEXT,
    source     TEXT,
    first_seen TEXT,
    last_seen  TEXT,
    created_at TEXT    NOT NULL,
    PRIMARY KEY (name, item_id),
    FOREIGN KEY (item_id) REFERENCES marg_item(item_id)
);
CREATE INDEX IF NOT EXISTS ix_marg_item_name_item ON marg_item_name(item_id);
CREATE INDEX IF NOT EXISTS ix_marg_item_name_kind ON marg_item_name(kind);

-- ---------------------------------------------------------------------------
-- 3 - DERIVED FACTS, each carrying where it came from and how complete it is.
--     Derivation and judgement are kept apart on purpose (see the architecture
--     take).  THIS TABLE IS DERIVED ONLY: every row may be recomputed at any
--     time and must give the same answer.  A person's decision never lands
--     here -- it goes to marg_task.
--     fact: salt | pack_size | packing | mrp_p | cost_p | company | expiry
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marg_item_fact (
    item_id     INTEGER NOT NULL,
    fact        TEXT    NOT NULL,
    value       TEXT,
    as_of       TEXT,                          -- the date the VALUE is true for
    source      TEXT    NOT NULL,              -- the table/report it came from
    basis       TEXT,                          -- how it was computed, in words
    coverage_n  INTEGER,                       -- rows the value rests on
    computed_at TEXT    NOT NULL,
    PRIMARY KEY (item_id, fact),
    FOREIGN KEY (item_id) REFERENCES marg_item(item_id)
);

-- ---------------------------------------------------------------------------
-- 4 - THE ONE HOME FOR EVERY MARG CORRECTION  (D411).
--     A salt name, an item rename, a merge, a pack fix, a new item's details:
--     one list, one place, worked by the same people.  Deliberately the same
--     a/b/c shape as purchase_salt_task, which Amir already reads, so the
--     existing 125 salt questions can move in without changing how they look.
--     kind:   salt|rename|merge|pack|new_item|ambiguous|question
--     status: open|done|declined
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marg_task (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT    NOT NULL,
    item_id     INTEGER,
    section     TEXT,
    seq         INTEGER,
    a           TEXT,                           -- "from" / the item
    b           TEXT,                           -- "to"   / the answer wanted
    c           TEXT,                           -- why, in plain words
    detail      TEXT,                           -- longer note, optional
    money_p     INTEGER,                        -- what it is worth, when known
    status      TEXT    NOT NULL DEFAULT 'open',
    done_by     TEXT,
    done_at     TEXT,
    answer      TEXT,
    answer_by   TEXT,
    answer_at   TEXT,
    source      TEXT,
    created_at  TEXT    NOT NULL,
    UNIQUE (kind, a, b),
    FOREIGN KEY (item_id) REFERENCES marg_item(item_id)
);
CREATE INDEX IF NOT EXISTS ix_marg_task_status ON marg_task(status, kind);
CREATE INDEX IF NOT EXISTS ix_marg_task_item ON marg_task(item_id);

-- ---------------------------------------------------------------------------
-- 5 - WHAT COULD NOT BE RESOLVED, kept rather than dropped.
--     A name that matched nothing, or matched more than one item.  Never
--     guessed at: recorded, counted, and answerable by a person.
--     verdict: unknown | ambiguous
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marg_name_unresolved (
    name        TEXT    NOT NULL,
    name_raw    TEXT    NOT NULL,
    seen_in     TEXT    NOT NULL,               -- which table it was read from
    verdict     TEXT    NOT NULL,
    candidates  TEXT,                           -- the item_ids it could be
    lines       INTEGER,                        -- how many rows carry it
    money_p     INTEGER,
    first_seen  TEXT,
    last_seen   TEXT,
    computed_at TEXT    NOT NULL,
    PRIMARY KEY (name, seen_in)
);

-- ---------------------------------------------------------------------------
-- 6 - THE BUILD'S OWN RECORD.  Every run writes one row, so a figure on a
--     screen can always say which build it came from and what that build
--     could see.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marg_spine_run (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    mode        TEXT NOT NULL,                  -- build|refresh
    items       INTEGER,
    names       INTEGER,
    facts       INTEGER,
    tasks_open  INTEGER,
    unresolved  INTEGER,
    notes       TEXT
);

-- ---------------------------------------------------------------------------
-- 7 - SETTINGS this spine depends on, as data rather than as constants buried
--     in code.  The truncation width is an OBSERVED FACT about Marg, not a law.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marg_spine_setting (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    note        TEXT,
    updated_at  TEXT NOT NULL
);
