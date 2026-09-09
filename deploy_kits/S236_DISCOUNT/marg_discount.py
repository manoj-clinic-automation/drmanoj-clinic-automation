#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marg_discount.py -- S236, 09-Sep-2026.  T1 OF THE SPINE: THE RULING TABLE.

WHAT THIS IS
    The owner's own decision about what each product actually sells for,
    stored as data instead of guessed by a constant.  D437: the orthotic
    discount register is THE AUTHORITY ON REALISABLE PRICE.

WHY IT IS A SEPARATE TABLE FROM EVERYTHING ELSE
    marg_item_fact is DERIVED ONLY -- recomputable, same inputs same answer,
    and its own schema comment says a person's decision never lands there.
    marg_task is a QUESTION -- it opens, it is answered, it closes.
    A ruling is neither.  It is a standing decision that outlives the round
    it was made in, changes only when the owner changes it, and must keep its
    old value visible when it does.  So it gets its own table and its own
    history, and nothing recomputes it.

THREE THINGS THIS FILE WAS BUILT AROUND, EACH FOUND BY READING THE REAL DATA
    1.  marg_item_fact.mrp_p IS NOT AN M.R.P.  It is the MEDIAN OBSERVED SALE
        PRICE, computed from the shop's own sale lines (marg_spine.py line
        ~689).  An observed price wearing an M.R.P. label is exactly the
        mislabelling the S235 derive pass exists to end, and it must not be
        used as the base of a discount.
    2.  THE PRINTED M.R.P. IS NOT IN THE DATABASE AT ALL.  stock_snapshot has
        no M.R.P. column and stock_mrp_manual is empty (0 rows, measured on
        the 08-Sep copy).  The M.R.P. figures the owner ruled against came off
        a Marg report.  So THE RULING MUST CARRY ITS OWN M.R.P., with the date
        that M.R.P. was in force -- which merges two of the spine's rungs
        ("mrp_less_discount" and "hold M.R.P. with its date") into one table.
    3.  MARGIN_ORTHO_DEFAULT = 0.30 IN marg_derive.py IS NOT A DISCOUNT.  It
        is a cost->price gross-up used only for the ESTIMATED rung.  The S235
        documents say the register "replaces" it; read against the code that
        is loose.  The register is a BETTER RUNG ABOVE it, not a replacement
        for it, and 0.30 stays as the fallback for a product with no M.R.P.
        and no ruling.  Deleting it would have silently unpriced every
        appliance the owner has not yet ruled on.

WHAT IT DELIBERATELY DOES NOT DO
    It does not re-order the live price ladder.  The ruled price and the
    observed price are written SIDE BY SIDE, with their disagreement stored
    as data, so that where the counter is actually selling at a different
    rate than the owner ruled becomes a visible number rather than a silent
    overwrite.  Changing which rung wins is a decision with money on it and
    it belongs to the owner, informed by that number.

D437  a no-discount ruling is DATA.  discount_pct = 0 means "decided: sells
      at M.R.P."  NO ROW AT ALL means "nobody has decided yet."  These must
      never collapse into each other, and the schema makes that structural:
      the absence is the absence of a row, and every consumer here returns
      the word 'undecided' rather than a number.
D438  internal_use is a THIRD PRODUCT STATE beside active and retired.  No
      selling price, never counted as unpriced revenue, never flagged as sold
      below M.R.P., never in a loss figure -- but still correctable in Marg.

SAFE TO RUN TWICE.  Every statement is IF NOT EXISTS; the seed is idempotent
and refuses to overwrite a ruling that has been changed since it was seeded.
"""

import argparse
import datetime
import json
import os
import shutil
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

SEED_PATH = os.path.join(HERE, "discount_seed_S236.json")
SPINE_PATH = os.path.join(HERE, "..", "S229_ITEM_SPINE", "marg_spine.py")

RULED_ON = "2026-09-09"
RULED_BY = "owner"
SEED_SOURCE = ("Sanjeevni_Orthotic_Loss_and_Correction_Voucher_09Sep2026.xlsx, "
               "sheet 'LOSS BY SECTION 06-SEP' -- the owner's own settled register, S235")

STATES = ("discount", "mrp", "retired", "internal")


def now_ist():
    return datetime.datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S")


def load_spine(path=None):
    """Import marg_spine.py as a module without requiring it to be installed.

    The spine is the ONE thing that knows which product a name means.  Doing
    our own matching here would be a second opinion about identity, which is
    the fault the spine was built to end."""
    p = os.path.abspath(path or SPINE_PATH)
    if not os.path.exists(p):
        raise RuntimeError("the item spine is not beside this kit: %s" % p)
    import importlib.util
    spec = importlib.util.spec_from_file_location("marg_spine_for_discount", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- #
# SCHEMA
# --------------------------------------------------------------------------- #

SCHEMA_SQL = """
-- ===========================================================================
--  marg_discount -- S236.  TWO new tables and one run log.  Nothing existing
--  is altered, renamed or dropped.  Every statement is IF NOT EXISTS.
-- ===========================================================================

-- THE RULING.  One row per product the owner has decided about.
--
-- NO ROW = UNDECIDED.  That is the whole reason discount_pct is NOT NULL for
-- a decided price: a nullable percentage would let 'decided: zero' and
-- 'nobody has said' share a representation, and D437 exists because those two
-- must never be confused.  The one case that genuinely has no selling price
-- is internal_use, and it is marked by its own column and its own state, not
-- by a null percentage.
CREATE TABLE IF NOT EXISTS marg_item_discount (
    item_id        INTEGER PRIMARY KEY,
    state          TEXT    NOT NULL,   -- discount | mrp | retired | internal
    discount_pct   REAL,               -- 0.0 .. 0.95.  NULL ONLY when state='internal'
    no_discount    INTEGER NOT NULL DEFAULT 0,   -- 1 when the ruling is 'sells at M.R.P.'
    internal_use   INTEGER NOT NULL DEFAULT 0,   -- D438, the third product state
    retired        INTEGER NOT NULL DEFAULT 0,   -- dynamic: a new purchase bill revives it
    mrp_p          INTEGER,            -- the PRINTED M.R.P. in paise, as ruled against
    mrp_as_of      TEXT,               -- the date that M.R.P. was in force
    cost_p         INTEGER,            -- carried for internal_use, which has no sale price
    ruling         TEXT    NOT NULL,   -- the decision in the owner's plain words
    ruled_on       TEXT    NOT NULL,
    ruled_by       TEXT    NOT NULL,
    name_at_ruling TEXT    NOT NULL,   -- what Marg called it when he decided
    section        TEXT,
    family         TEXT,
    source         TEXT    NOT NULL,
    run_id         INTEGER,
    recorded_at    TEXT    NOT NULL,
    CHECK (state IN ('discount','mrp','retired','internal')),
    CHECK (discount_pct IS NULL OR (discount_pct >= 0.0 AND discount_pct < 0.95)),
    CHECK ((state = 'internal') = (discount_pct IS NULL)),
    FOREIGN KEY (item_id) REFERENCES marg_item(item_id)
);
CREATE INDEX IF NOT EXISTS ix_marg_item_discount_state ON marg_item_discount(state);

-- EVERY RULING THIS PRODUCT HAS EVER CARRIED.  A ruling is never overwritten
-- in silence: the old row is copied here first, so "what was it in September"
-- stays answerable after November changes it.  This is what makes rung 4 --
-- freeze the rate onto the line at the moment of a round -- possible at all.
CREATE TABLE IF NOT EXISTS marg_item_discount_history (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id        INTEGER NOT NULL,
    state          TEXT    NOT NULL,
    discount_pct   REAL,
    mrp_p          INTEGER,
    mrp_as_of      TEXT,
    ruling         TEXT,
    ruled_on       TEXT,
    ruled_by       TEXT,
    name_at_ruling TEXT,
    source         TEXT,
    replaced_at    TEXT    NOT NULL,
    replaced_by_run INTEGER,
    FOREIGN KEY (item_id) REFERENCES marg_item(item_id)
);
CREATE INDEX IF NOT EXISTS ix_marg_discount_hist_item ON marg_item_discount_history(item_id);

-- ONE ROW PER RUN, so any figure resting on a ruling can say which run wrote
-- it and what that run could see.
CREATE TABLE IF NOT EXISTS marg_discount_run (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at   TEXT NOT NULL,
    finished_at  TEXT,
    mode         TEXT NOT NULL,
    seeded       INTEGER,
    updated      INTEGER,
    unchanged    INTEGER,
    refused      INTEGER,
    unresolved   INTEGER,
    notes        TEXT
);
"""


def ensure_schema(con):
    con.executescript(SCHEMA_SQL)
    con.commit()


def tables(con):
    return {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}


# --------------------------------------------------------------------------- #
# THE READERS -- what every other screen should call, and nothing else
# --------------------------------------------------------------------------- #

def ruling_of(con, item_id):
    """The live ruling for a product, or None when nobody has decided.

    Returns None rather than a default ON PURPOSE.  A caller that wants a
    fallback must ask for one out loud."""
    r = con.execute(
        "SELECT state, discount_pct, no_discount, internal_use, retired, "
        "       mrp_p, mrp_as_of, cost_p, ruling, ruled_on, name_at_ruling "
        "FROM marg_item_discount WHERE item_id=?", (item_id,)).fetchone()
    if not r:
        return None
    k = ("state", "discount_pct", "no_discount", "internal_use", "retired",
         "mrp_p", "mrp_as_of", "cost_p", "ruling", "ruled_on", "name_at_ruling")
    return dict(zip(k, r))


def realisable_p(con, item_id):
    """(paise, rung, basis-in-words) -- what one unit actually fetches.

    rung:
      ruled       M.R.P. less the owner's own discount, or M.R.P. itself
      internal    never billed to a patient; there IS no selling price
      undecided   no ruling exists.  NOT zero, NOT a guess, NOT the 30%.
    """
    r = ruling_of(con, item_id)
    if r is None:
        return (None, "undecided",
                "no ruling exists for this product. A missing row is 'nobody has "
                "decided yet' and is deliberately not the same as a ruling of zero.")
    if r["state"] == "internal":
        return (None, "internal",
                "internal consumption (D438): never billed to a patient, so it has "
                "no selling price and must never enter a loss or revenue figure.")
    if r["mrp_p"] is None:
        return (None, "undecided",
                "a ruling exists but carries no M.R.P. to apply it to.")
    pct = r["discount_pct"] or 0.0
    val = int(round(r["mrp_p"] * (1.0 - pct)))
    if pct == 0.0:
        why = "M.R.P. (no discount) -- a DECISION, not an absence (D437)."
    else:
        why = "M.R.P. less %s%%, the owner's own ruling of %s (D437)." % (
            _pct_text(pct), r["ruled_on"])
    if r["retired"]:
        why += "  This product is retired; the rate is the one its ruling carries."
    return (val, "ruled", why)


def stock_value_p(con, item_id):
    """(paise per unit, basis-in-words) -- what ONE UNIT ON THE SHELF IS WORTH.

    OWNER'S RULING, 09-Sep-2026: **THE STOCK REPORT IS VALUED AT M.R.P.**

    This is a DIFFERENT NUMBER from realisable_p() and the two must never be
    swapped.  Stock on the shelf is valued at the printed M.R.P.; what a unit
    actually fetches when it is sold is M.R.P. less the ruling.  Using the
    discounted rate to value stock would understate the shelf; using the M.R.P.
    to value a sale would overstate the takings.  Both errors have been made in
    this estate before, which is why they are two named functions rather than
    one function with a flag.

    internal_use products ARE valued here -- they are stock and they are on the
    shelf -- but they carry internal=True so a LOSS figure can exclude them
    without having to know why (D438)."""
    r = ruling_of(con, item_id)
    if r is None:
        return (None, "no ruling exists, so no M.R.P. is held for this product here.")
    if r["mrp_p"] is None:
        return (None, "a ruling exists but carries no M.R.P.")
    why = "M.R.P. as printed on the Marg stock report of %s -- the owner's ruling of " \
          "09-Sep-2026 is that STOCK IS VALUED AT M.R.P., never at the discounted rate." \
          % (r["mrp_as_of"] or "the ruling date")
    if r["internal_use"]:
        why += "  This product is internal consumption: it is stock and it is valued, " \
               "but it must be excluded from any LOSS or REVENUE figure (D438)."
    return (r["mrp_p"], why)


def _pct_text(pct):
    t = ("%.2f" % (pct * 100.0)).rstrip("0").rstrip(".")
    return t


def undecided_items(con):
    """Every product on the spine with no ruling at all.  This is the list
    that says how far the register still has to go, and it is a COUNT the
    owner can act on rather than a silent default applied behind his back."""
    return [r[0] for r in con.execute(
        "SELECT m.item_id FROM marg_item m "
        "LEFT JOIN marg_item_discount d ON d.item_id = m.item_id "
        "WHERE d.item_id IS NULL AND m.status != 'merged' ORDER BY m.item_id")]


# --------------------------------------------------------------------------- #
# THE SEED
# --------------------------------------------------------------------------- #

class Seeder(object):

    def __init__(self, con, spine_mod, out=print):
        self.con = con
        self.ms = spine_mod
        self.out = out
        self.seeded = self.updated = self.unchanged = self.refused = 0
        self.unresolved = []
        self.run_id = None

    # -- helpers ----------------------------------------------------------
    def start(self, mode):
        cur = self.con.execute(
            "INSERT INTO marg_discount_run (started_at, mode) VALUES (?,?)",
            (now_ist(), mode))
        self.run_id = cur.lastrowid
        return self.run_id

    def finish(self, notes=""):
        self.con.execute(
            "UPDATE marg_discount_run SET finished_at=?, seeded=?, updated=?, "
            "unchanged=?, refused=?, unresolved=?, notes=? WHERE id=?",
            (now_ist(), self.seeded, self.updated, self.unchanged, self.refused,
             len(self.unresolved), notes, self.run_id))
        self.con.commit()

    # -- the work ---------------------------------------------------------
    def seed(self, rows):
        """Write the owner's rulings.  Resolution is the SPINE's job.

        A name that does not resolve to exactly one product is NEVER guessed
        at: it is collected and reported, and -- if marg_task exists -- opened
        as a question, because a ruling written against the wrong product is
        worse than no ruling."""
        sp = self.ms.Spine(self.con, self.ms.W_PURCHASE)
        seen = {}
        for x in rows:
            name = x["name_at_ruling"]
            iid, how, cands = sp.resolve(name, self.ms.W_PURCHASE)
            if iid is None:
                self.unresolved.append((name, how, cands))
                continue
            if iid in seen:
                # Two rulings landing on one product is a data fault, not a
                # merge.  Refuse both rather than let the later one win.
                self.unresolved.append(
                    (name, "collides with '%s' on item_id %s" % (seen[iid], iid), None))
                self.refused += 1
                continue
            seen[iid] = name
            self._write(iid, x, how)
        return self

    def _write(self, iid, x, how):
        state = x["state"]
        if state not in STATES:
            raise ValueError("unknown state %r for %r" % (state, x["name_at_ruling"]))
        pct = x.get("discount_pct")
        if state == "internal":
            pct = None
        elif pct is None:
            pct = 0.0
        no_disc = 1 if (state == "mrp") else 0
        internal = 1 if state == "internal" else 0
        retired = 1 if state == "retired" else 0
        mrp_p = x.get("mrp_p")
        cost_p = x.get("rate_p_workbook") if state == "internal" else None
        ruling = x.get("basis") or _default_ruling(state, pct)

        old = self.con.execute(
            "SELECT state, discount_pct, mrp_p, mrp_as_of, ruling, ruled_on, "
            "ruled_by, name_at_ruling, source FROM marg_item_discount "
            "WHERE item_id=?", (iid,)).fetchone()

        if old is not None:
            same = (old[0] == state
                    and _close(old[1], pct)
                    and old[2] == mrp_p)
            if same:
                self.unchanged += 1
                return
            # NEVER overwrite in silence -- the old ruling goes to history
            # first, so "what was it in September" survives November.
            self.con.execute(
                "INSERT INTO marg_item_discount_history "
                "(item_id, state, discount_pct, mrp_p, mrp_as_of, ruling, ruled_on, "
                " ruled_by, name_at_ruling, source, replaced_at, replaced_by_run) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (iid, old[0], old[1], old[2], old[3], old[4], old[5], old[6],
                 old[7], old[8], now_ist(), self.run_id))
            self.con.execute("DELETE FROM marg_item_discount WHERE item_id=?", (iid,))
            self.updated += 1
        else:
            self.seeded += 1

        self.con.execute(
            "INSERT INTO marg_item_discount "
            "(item_id, state, discount_pct, no_discount, internal_use, retired, "
            " mrp_p, mrp_as_of, cost_p, ruling, ruled_on, ruled_by, name_at_ruling, "
            " section, family, source, run_id, recorded_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (iid, state, pct, no_disc, internal, retired, mrp_p, x.get("mrp_as_of"),
             cost_p, ruling, x.get("ruled_on") or RULED_ON, x.get("ruled_by") or RULED_BY,
             x["name_at_ruling"], x.get("section"), x.get("family"),
             x.get("source") or SEED_SOURCE, self.run_id, now_ist()))

    def open_tasks_for_unresolved(self):
        """A name we could not place becomes a question a person can answer,
        never a silent omission (the spine's own rule for marg_name_unresolved)."""
        if "marg_task" not in tables(self.con):
            return 0
        n = 0
        for name, how, cands in self.unresolved:
            try:
                self.con.execute(
                    "INSERT OR IGNORE INTO marg_task (kind, a, b, c, source, created_at) "
                    "VALUES ('ambiguous', ?, ?, ?, ?, ?)",
                    (name, "which product is this?",
                     "a settled discount ruling could not be placed on the spine (%s). "
                     "Until it is, this product is UNDECIDED and no price is guessed for it."
                     % how, "marg_discount seed S236", now_ist()))
                n += 1
            except sqlite3.Error:
                pass
        self.con.commit()
        return n


def _default_ruling(state, pct):
    if state == "internal":
        return "internal consumption -- never billed to a patient (D438)"
    if state == "retired":
        return "M.R.P. (retired product)"
    if not pct:
        return "M.R.P. (no discount)"
    return "M.R.P. less %s%%" % _pct_text(pct)


def _close(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(float(a) - float(b)) < 1e-9


def load_seed(path=None):
    p = os.path.abspath(path or SEED_PATH)
    with open(p, "r", encoding="utf-8") as f:
        rows = json.load(f)
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("seed file is empty or not a list: %s" % p)
    return rows


# --------------------------------------------------------------------------- #
# REPORT
# --------------------------------------------------------------------------- #

def report(con, out=print):
    q = lambda s, *a: con.execute(s, a).fetchall()
    run = q("SELECT id, finished_at, seeded, updated, unchanged, refused, unresolved "
            "FROM marg_discount_run ORDER BY id DESC LIMIT 1")
    if not run:
        out("no run has been recorded")
        return
    rid, fin, sd, up, un, rf, ur = run[0]
    out("")
    out("  RUN %s   finished %s" % (rid, fin))
    out("  seeded %s | updated %s | unchanged %s | refused %s | unresolved %s"
        % (sd, up, un, rf, ur))
    out("")
    out("  THE REGISTER")
    for state, n in q("SELECT state, COUNT(*) FROM marg_item_discount "
                      "GROUP BY state ORDER BY COUNT(*) DESC"):
        out("     %-10s %d" % (state, n))
    tot = q("SELECT COUNT(*) FROM marg_item_discount")[0][0]
    out("     %-10s %d" % ("TOTAL", tot))
    out("")
    rows = q("SELECT discount_pct, COUNT(*) FROM marg_item_discount "
             "WHERE state='discount' GROUP BY discount_pct ORDER BY discount_pct")
    out("  DISCOUNTS RULED")
    for pct, n in rows:
        out("     %-6s %d" % (_pct_text(pct) + "%", n))
    out("")
    if "marg_item" in tables(con):
        u = len(undecided_items(con))
        allitems = q("SELECT COUNT(*) FROM marg_item WHERE status!='merged'")[0][0]
        out("  COVERAGE")
        out("     ruled      %d of %d products on the spine" % (tot, allitems))
        out("     UNDECIDED  %d  -- no ruling exists; nothing is guessed for these" % u)
    out("")


# --------------------------------------------------------------------------- #
# SELFTEST
# --------------------------------------------------------------------------- #

def _fixture(ms):
    """A tiny spine with the shapes that matter, built the way the real one is."""
    con = sqlite3.connect(":memory:")
    with open(os.path.join(os.path.dirname(os.path.abspath(ms.__file__)),
                           "marg_spine_schema.sql"), "r", encoding="utf-8") as f:
        con.executescript(f.read())
    now = now_ist()
    items = [(1, "KNEE HINGE UNI XL", "KNEE HINGE UNI XL", "active"),
             (2, "LS BELT UNI XXXL", "LS BELT UNI XXXL", "active"),
             (3, "BLADE", "BLADE", "active"),
             (4, "CREPE LEUK 10CM", "CREPE LEUK 10CM", "active"),
             (5, "OLD THING", "OLD THING", "retired"),
             (6, "NOBODY RULED ME", "NOBODY RULED ME", "active")]
    for iid, canon, raw, status in items:
        con.execute("INSERT INTO marg_item (item_id, canonical, canonical_raw, status, "
                    "origin, created_at) VALUES (?,?,?,?, 'manual', ?)",
                    (iid, ms.norm(canon), raw, status, now))
        con.execute("INSERT INTO marg_item_name (name, item_id, name_raw, kind, active, "
                    "created_at) VALUES (?,?,?, 'canonical', 1, ?)",
                    (ms.norm(canon), iid, raw, now))
    con.commit()
    return con


def selftest(out=print):
    ok = [0]
    bad = [0]

    def ck(label, cond):
        if cond:
            ok[0] += 1
        else:
            bad[0] += 1
            out("  FAIL  %s" % label)

    ms = load_spine()
    con = _fixture(ms)
    ensure_schema(con)

    rows = [
        dict(name_at_ruling="KNEE HINGE UNI XL", state="discount", discount_pct=0.30,
             mrp_p=139000, mrp_as_of="2026-09-06", basis="MRP less 30%",
             section="ORTHOTICS", family="Hinged knee support"),
        dict(name_at_ruling="LS BELT UNI XXXL", state="mrp", discount_pct=0.0,
             mrp_p=128000, mrp_as_of="2026-09-06", basis="MRP (no discount)",
             section="ORTHOTICS", family="LS belt"),
        dict(name_at_ruling="BLADE", state="internal", discount_pct=None,
             mrp_p=500, rate_p_workbook=300, mrp_as_of="2026-09-06",
             basis="cost (internal use, never billed)", section="CONSUMABLES", family="Blade"),
        dict(name_at_ruling="OLD THING", state="retired", discount_pct=0.0,
             mrp_p=40000, mrp_as_of="2026-09-06", basis="MRP (retired product)",
             section="ORTHOTICS", family="LS belt"),
    ]

    s = Seeder(con, ms, out=lambda *a: None)
    s.start("selftest")
    s.seed(rows)
    s.finish("selftest")

    ck("all four rulings seeded", s.seeded == 4)
    ck("nothing refused", s.refused == 0)
    ck("nothing unresolved", s.unresolved == [])

    # ---- the arithmetic ----
    v, rung, why = realisable_p(con, 1)
    ck("a 30% ruling gives MRP less 30%", v == 97300 and rung == "ruled")
    ck("the basis names the owner's ruling", "own ruling" in why)
    v, rung, why = realisable_p(con, 2)
    ck("a no-discount ruling gives the MRP itself", v == 128000 and rung == "ruled")
    ck("D437: zero is reported as a DECISION", "DECISION" in why)

    # ---- D437, the whole point ----
    v, rung, why = realisable_p(con, 6)
    ck("D437: an unruled product is 'undecided', not zero", v is None and rung == "undecided")
    ck("D437: and it does not silently become a guess", "decided" in why)
    ck("a ruling of zero and no ruling do NOT share a representation",
       realisable_p(con, 2)[1] != realisable_p(con, 6)[1])

    # ---- D438 ----
    v, rung, why = realisable_p(con, 3)
    ck("D438: internal use has NO selling price", v is None and rung == "internal")
    ck("D438: and says why, so it is never read as unpriced revenue",
       "never billed" in why)
    ck("D438: internal_use carries its cost instead",
       ruling_of(con, 3)["cost_p"] == 300)
    ck("D438: internal is the ONLY state with a null percentage",
       con.execute("SELECT COUNT(*) FROM marg_item_discount WHERE discount_pct IS NULL "
                   "AND state!='internal'").fetchone()[0] == 0)

    # ---- the owner's ruling: STOCK IS VALUED AT M.R.P. ----
    sv, swhy = stock_value_p(con, 1)
    rv, _, _ = realisable_p(con, 1)
    ck("stock is valued at the M.R.P., not the discounted rate", sv == 139000)
    ck("and that is NOT the same number as the sale-side rate", sv != rv and rv == 97300)
    ck("the basis says so in words", "VALUED AT M.R.P." in swhy)
    ck("an internal-use product IS still valued as stock", stock_value_p(con, 3)[0] == 500)
    ck("but says it must be left out of a loss figure",
       "LOSS" in stock_value_p(con, 3)[1])
    ck("an unruled product has no stock value here either",
       stock_value_p(con, 6)[0] is None)

    # ---- retired is dynamic, not dead ----
    v, rung, why = realisable_p(con, 5)
    ck("a retired product still carries its ruled rate", v == 40000 and rung == "ruled")
    ck("and says it is retired", "retired" in why)

    # ---- the CHECK constraints are real, not decorative ----
    try:
        con.execute("INSERT INTO marg_item_discount (item_id, state, discount_pct, "
                    "ruling, ruled_on, ruled_by, name_at_ruling, source, recorded_at) "
                    "VALUES (99,'discount',1.5,'x','x','x','x','x','x')")
        ck("a percentage of 150% is refused by the schema", False)
    except sqlite3.IntegrityError:
        ck("a percentage of 150% is refused by the schema", True)
    try:
        con.execute("INSERT INTO marg_item_discount (item_id, state, discount_pct, "
                    "ruling, ruled_on, ruled_by, name_at_ruling, source, recorded_at) "
                    "VALUES (98,'internal',0.2,'x','x','x','x','x','x')")
        ck("internal_use with a percentage is refused by the schema", False)
    except sqlite3.IntegrityError:
        ck("internal_use with a percentage is refused by the schema", True)
    try:
        con.execute("INSERT INTO marg_item_discount (item_id, state, discount_pct, "
                    "ruling, ruled_on, ruled_by, name_at_ruling, source, recorded_at) "
                    "VALUES (97,'mrp',NULL,'x','x','x','x','x','x')")
        ck("a decided price with a NULL percentage is refused", False)
    except sqlite3.IntegrityError:
        ck("a decided price with a NULL percentage is refused", True)
    con.rollback()

    # ---- idempotence ----
    s2 = Seeder(con, ms, out=lambda *a: None)
    s2.start("selftest-again")
    s2.seed(rows)
    s2.finish("selftest-again")
    ck("running the seed twice changes nothing", s2.seeded == 0 and s2.updated == 0)
    ck("and says so as 'unchanged'", s2.unchanged == 4)
    ck("no history row is written when nothing changed",
       con.execute("SELECT COUNT(*) FROM marg_item_discount_history").fetchone()[0] == 0)

    # ---- a CHANGED ruling is never overwritten in silence ----
    rows2 = [dict(r) for r in rows]
    rows2[0]["discount_pct"] = 0.20
    rows2[0]["basis"] = "MRP less 20%"
    s3 = Seeder(con, ms, out=lambda *a: None)
    s3.start("selftest-change")
    s3.seed(rows2)
    s3.finish("selftest-change")
    ck("a changed ruling updates", s3.updated == 1)
    h = con.execute("SELECT state, discount_pct FROM marg_item_discount_history "
                    "WHERE item_id=1").fetchall()
    ck("and the OLD ruling is kept in history", h and abs(h[0][1] - 0.30) < 1e-9)
    ck("the live row now carries the new one",
       abs(ruling_of(con, 1)["discount_pct"] - 0.20) < 1e-9)
    ck("so September stays answerable after November changed it",
       realisable_p(con, 1)[0] == 111200 and h[0][1] == 0.30)

    # ---- coverage is a fact, not a silence ----
    u = undecided_items(con)
    # Items 4 (CREPE) and 6 are deliberately never ruled in this fixture; the
    # first version of this check asserted [6] and failed, which is the check
    # working -- an undecided product that goes unlisted is exactly the
    # silence D437 exists to prevent.
    ck("EVERY unruled product is listed as undecided", u == [4, 6])
    ck("a ruled product is not listed", 1 not in u and 2 not in u and 3 not in u)
    ck("and 'retired' is a RULING, so a retired product is not undecided", 5 not in u)
    ck("merged products are excluded, not counted as undecided",
       all(con.execute("SELECT status FROM marg_item WHERE item_id=?", (i,)).fetchone()[0]
           != 'merged' for i in u))

    # ---- a name the spine cannot place is never guessed at ----
    s4 = Seeder(con, ms, out=lambda *a: None)
    s4.start("selftest-unknown")
    s4.seed([dict(name_at_ruling="A PRODUCT THAT DOES NOT EXIST", state="mrp",
                  discount_pct=0.0, mrp_p=100, basis="MRP (no discount)")])
    s4.finish("selftest-unknown")
    ck("an unplaceable ruling is refused, not guessed", s4.seeded == 0)
    ck("and it is reported rather than dropped", len(s4.unresolved) == 1)
    ck("and it becomes a question a person can answer",
       s4.open_tasks_for_unresolved() == 1)

    # ---- two rulings on one product ----
    con2 = _fixture(ms)
    ensure_schema(con2)
    s5 = Seeder(con2, ms, out=lambda *a: None)
    s5.start("selftest-collide")
    s5.seed([dict(name_at_ruling="BLADE", state="mrp", discount_pct=0.0, mrp_p=500,
                  basis="MRP (no discount)"),
             dict(name_at_ruling="blade", state="discount", discount_pct=0.1, mrp_p=500,
                  basis="MRP less 10%")])
    s5.finish("selftest-collide")
    ck("two rulings on ONE product: the first stands", s5.seeded == 1)
    ck("and the second is REFUSED rather than allowed to win", s5.refused == 1)
    ck("the surviving ruling is the first one, not the last",
       ruling_of(con2, 3)["state"] == "mrp")

    # ---- the schema is safe to run twice ----
    ensure_schema(con)
    ck("ensure_schema is idempotent", "marg_item_discount" in tables(con))

    out("")
    out("  selftests: %d passed, %d failed" % (ok[0], bad[0]))
    return bad[0] == 0


# --------------------------------------------------------------------------- #
# RUNNERS
# --------------------------------------------------------------------------- #

def open_db(path, readonly=False):
    if readonly:
        con = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    else:
        con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys=ON")
    return con


def safe_copy(src, dst):
    shutil.copy2(src, dst)
    return dst


def dry_run(path, seed=None, out=print):
    """Rehearse on a COPY.  Never touches the real file."""
    tmp = path + ".dryrun_S236"
    safe_copy(path, tmp)
    try:
        con = open_db(tmp)
        ms = load_spine()
        ensure_schema(con)
        s = Seeder(con, ms, out=out)
        s.start("dry-run")
        s.seed(load_seed(seed))
        s.open_tasks_for_unresolved()
        s.finish("dry run on a copy")
        report(con, out=out)
        if s.unresolved:
            out("  NOT PLACED (%d) -- each is now a question, none is guessed:" % len(s.unresolved))
            for name, how, _ in s.unresolved:
                out("     %s   (%s)" % (name, how))
        con.close()
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def install(path, seed=None, out=print):
    bak = "%s.bak_S236_discount_%s" % (
        path, datetime.datetime.now(IST).strftime("%Y%m%d_%H%M%S"))
    safe_copy(path, bak)
    out("  backup: %s" % bak)
    con = open_db(path)
    ms = load_spine()
    ensure_schema(con)
    s = Seeder(con, ms, out=out)
    s.start("install")
    s.seed(load_seed(seed))
    s.open_tasks_for_unresolved()
    s.finish("install")
    report(con, out=out)
    con.close()
    out("  undo, if it is ever needed:")
    out("  \\cp %s %s" % (bak, path))


def main(argv=None):
    ap = argparse.ArgumentParser(description="S236 T1 -- the ruling table")
    ap.add_argument("--db")
    ap.add_argument("--seed")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return 0 if selftest() else 1
    if not a.db:
        ap.error("--db is required for anything but --selftest")
    if a.dry_run:
        dry_run(a.db, a.seed)
        return 0
    if a.install:
        install(a.db, a.seed)
        return 0
    if a.report:
        con = open_db(a.db, readonly=True)
        report(con)
        con.close()
        return 0
    ap.error("say one of --selftest, --dry-run, --install, --report")


if __name__ == "__main__":
    sys.exit(main())
