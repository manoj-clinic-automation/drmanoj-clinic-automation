#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marg_derive.py -- S235, 08-Sep-2026.  THE DERIVATION PASS.  v2.

WHAT THIS IS
    Step 2+3 of the consolidation the owner approved.  One job works the
    numbers out ONCE, into a table, each figure carrying HOW COMPLETE IT IS
    as data -- instead of every screen recomputing its own answer when
    somebody opens it and then apologising for itself in a sentence.

    Measured before writing this, on the 08-Sep 01:05 database:
      * every number on every stock, purchase and sale screen is recomputed
        at request time.  Nothing is stored.  So no two screens can be
        guaranteed to agree, and nobody can ask what coverage looked like
        last month.
      * completeness is PROSE in twenty separate hand-written phrases across
        the stock screens alone ("no MRP on record", "at cost, for
        reference", "N unpriced", "no price").  Exactly one place in the
        whole estate stores a completeness count as data.
      * pricing by raw item name reaches 221 of 373 shelf items.  Pricing
        through the item spine reaches 227 -- and moves 8 items off an
        ESTIMATED price onto a real observed one.

WHAT IT IS NOT
    It holds DERIVED facts only.  Every row may be recomputed at any moment
    and must give the same answer.  A person's decision -- a write-off, a
    cause, a count, a typed salt -- NEVER lands here.  Those live in
    marg_task and the stock tables and are not touched by this file.

    IT CHANGES NO SCREEN.  Nothing reads these tables yet.  Two new tables
    are added; nothing existing is altered, renamed or dropped.

THE ONE RULE IT ENFORCES
    A figure that cannot see everything says so IN A FIELD, not in a
    footnote a person has to remember.  A figure that CAN see everything
    leaves the coverage columns empty rather than inventing a denominator --
    a breakdown is not a coverage gap, and printing "337 uncovered" beside a
    count of 36 would be a new kind of lie.

WHAT v1 GOT WRONG  (adversarial review against the real database, 08-Sep)
    v1 passed 33 self-tests and was wrong in six ways that mattered:
      1  CRITICAL -- figures were upserted and never swept, so when a month's
         data was deleted its figures SURVIVED and the report printed them
         under the new run's header.  A shelf that no longer existed still
         showed 373 items and Rs 5.12 lakh.  Every pass now deletes what it
         did not write, in the same transaction, and the report reads only
         the newest run.
      2  the sale figure counted RETURN lines in its readability denominator
         while excluding their money -- so it disclosed unreachable money it
         had never included.
      3  the return figure always claimed perfect coverage.
      4  a breakdown count carried the whole shelf as its denominator, so a
         count of 12 faults rendered as "361 uncovered".
      5  the estate keyed on the raw snapshot string, not the spine item, so
         two spellings of one product would have double-counted -- the exact
         fault the spine exists to prevent.
      6  a merged or retired product still fed the estate total but got no
         row of its own, so the per-item table and the estate could not be
         reconciled.
    A green self-test suite proves the cases its author thought of.

  python marg_derive.py --selftest
  python marg_derive.py --db <file> --dry-run      (works on a copy, never writes)
  python marg_derive.py --db <file> --build
  python marg_derive.py --db <file> --report
  python marg_derive.py --db <file> --install      (self-gating: tests, rehearse, backup, build)
"""

import argparse
import os
import shutil
import sqlite3
import sys
import tempfile
import importlib.util
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
HERE = os.path.dirname(os.path.abspath(__file__))

# The spine is the authority on names, widths and pack arithmetic.  It is
# imported rather than copied, so there is exactly one implementation of
# "how many packs did this line move" in the estate.
SPINE_PATH = os.path.join(HERE, "..", "S229_ITEM_SPINE", "marg_spine.py")


def load_spine(path=None):
    p = os.path.abspath(path or SPINE_PATH)
    if not os.path.exists(p):
        raise SystemExit(
            "REFUSING: the item spine was not found at\n  %s\n"
            "marg_derive.py must sit beside S229_ITEM_SPINE in the same deploy\n"
            "clone.  Nothing was touched." % p)
    spec = importlib.util.spec_from_file_location("marg_spine", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def now_ist():
    return datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S")


# --------------------------------------------------------------------------- #
# THE PRICE LADDER
#
# The same four rungs stock_app._price_p climbs today, in the same order, so
# no figure here can disagree with a live screen about which price is right:
#     sale         the item's own observed sale price -- the real thing
#     manual       a price a PERSON typed into stock_mrp_manual
#     provisional  last purchase rate grossed up by the margin -- an ESTIMATE
#     none         nothing, and the figure says so rather than guessing
#
# The one difference, and it is the whole point of this pass: the rungs are
# climbed THROUGH THE SPINE, so a product is priced from every name it has
# ever worn, not only from the exact string one table happens to spell.
#
# AND THAT DIFFERENCE IS REAL, so it is stated rather than glossed: this pass
# CAN price a product the live screens call unpriced, because they look a
# typed or observed price up by exact string and this follows every name.
# That is the improvement, not an accident -- but it means the two can
# disagree, and any consumer must prefer this table rather than assume they
# agree.
#
# NOTE on the 'manual' rung: a typed MRP is a person's entry, and this file
# holds derived facts.  It is read anyway, deliberately, because a screen
# showing the owner's own typed price while this table called the product
# "unpriced" would be worse than the impurity.  It is labelled 'manual' so no
# consumer can mistake it for an observation, a typed price of zero or less is
# REFUSED rather than multiplied into a total, and how many typed prices were
# read, used, discarded and collided is reported as data.

# Widths for tables the spine's own SOURCE_WIDTH does not name.  Marg clips at
# 27 on every purchase/stock-shaped report and 20 on the sale report; guessing
# the sale width for a stock-side table is how a name gets called unknown and
# priced from in the same minute (the spine's own defect 4).
EXTRA_WIDTH = {"stock_mrp_manual": "purchase"}
# --------------------------------------------------------------------------- #

MARGIN_MED_DEFAULT = 0.20
MARGIN_ORTHO_DEFAULT = 0.30

_ORTHO_WORDS = ("BELT", "BINDER", "BRACE", "COLLAR", "CAST", "PAD ", "SPLINT", "SUPPORT",
                "KNEE", "WRIST", "GLOVE", "SYRINGE", "COTTON", "BLADE", "CREPE", "BANDAGE",
                "TYNOR", "UNISON", "HOSPIK", "IMMOBIL", "SLING", "SHOE", "WALKER",
                "FINGER COT", "DRESS", "GAUZE", "ELBOW", "ANKLE", "CERVICAL", "LUMBAR",
                "STICK", "CRUTCH", "BODY AID", "FLAMINGO", "REMEDE", "LEUKO", "NIPRO")


def is_ortho(item):
    return any(w in " " + (item or "").upper() + " " for w in _ORTHO_WORDS)


def _setting(con, key, default):
    """The RAW stored value, stripped -- never parsed here.

    v3 called float() here inside a try that caught only sqlite3.Error, so
    one settings row reading 'twenty percent' killed the whole pass with a
    traceback before a single figure was written, while every live screen
    carried on. Parsing belongs to the caller, which knows what a good value
    looks like and has a fallback."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
    except sqlite3.Error:
        return default
    if not r or r[0] is None:
        return default
    v = str(r[0]).strip()
    return default if v == "" else v


def _fraction(m, default):
    """0.30 and 30 mean the same thing to a person and very different things
    to arithmetic: 1-30 is -29, and max(0.05, -29) turns a 20% margin into a
    20x multiplier on every estimated price.  A setting above 1 is read as a
    percentage; anything that cannot be a margin at all falls back."""
    try:
        m = float(str(m).strip().rstrip("%"))
    except (TypeError, ValueError):
        return default
    if m != m or m in (float("inf"), float("-inf")):   # NaN and infinities
        return default
    if m > 1.0:
        m = m / 100.0
    if not (0.0 <= m < 0.95):
        return default
    return m


def margins(con):
    return (_fraction(_setting(con, "stock.margin_med", MARGIN_MED_DEFAULT), MARGIN_MED_DEFAULT),
            _fraction(_setting(con, "stock.margin_ortho", MARGIN_ORTHO_DEFAULT), MARGIN_ORTHO_DEFAULT))


def date_key(a):
    """Marg writes dd-mm-yyyy and text order lies about that -- '27-08-2026'
    sorts ABOVE '06-09-2026'.  That fault has a number already (F-236); this
    is the same guard, kept here so no figure in this file can inherit it."""
    t = (a or "").strip().replace("/", "-").split("-")
    if len(t) == 3:
        try:
            dd, mm, yy = (int(x) for x in t)
            if yy > 1900 and 1 <= mm <= 12 and 1 <= dd <= 31:
                return (yy, mm, dd)
        except ValueError:
            pass
    return (0, 0, 0)


def month_of(business_date):
    """'2026-08-14' -> '2026-08'.  None for anything that is not a real ISO
    date, INCLUDING Marg's day-first shape, which must never be sliced:
    substr('07-09-2026',1,7) is '07-09-2' and would sort above every real
    month.  These tables are ISO today; that is luck, not a guard."""
    s = str(business_date or "").strip()
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        try:
            y, m, d = int(s[0:4]), int(s[5:7]), int(s[8:10])
            if y > 1900 and 1 <= m <= 12 and 1 <= d <= 31:
                return "%04d-%02d" % (y, m)
        except ValueError:
            pass
    return None


def newest_snapshot(con):
    dates = [r[0] for r in con.execute("SELECT DISTINCT as_on FROM stock_snapshot")]
    dates = [d for d in dates if date_key(d) != (0, 0, 0)]
    if not dates:
        return None
    return max(dates, key=date_key)


def iso_of(ddmmyyyy):
    y, m, d = date_key(ddmmyyyy)
    return None if not y else "%04d-%02d-%02d" % (y, m, d)


# --------------------------------------------------------------------------- #
# SCHEMA
# --------------------------------------------------------------------------- #

SCHEMA_SQL = """
-- ===========================================================================
--  marg_derive -- S235.  TWO new tables.  Nothing existing is altered,
--  renamed or dropped.  Every statement is IF NOT EXISTS.
-- ===========================================================================

-- One row per derived figure.  DERIVED ONLY: recomputable, and the same
-- inputs must always give the same answer.  A person's decision never lands
-- here.
--
-- The coverage columns are NULLABLE ON PURPOSE.  A figure that can see
-- everything it is meant to see leaves them empty; inventing a denominator
-- for a breakdown count would report a gap that does not exist.
CREATE TABLE IF NOT EXISTS marg_figure (
    scope       TEXT    NOT NULL,   -- estate | month | item
    scope_key   TEXT    NOT NULL,   -- '' | '2026-08' | item_id
    figure      TEXT    NOT NULL,   -- the name of the number
    value_p     INTEGER,            -- money, in paise, when it is money
    value_n     REAL,               -- a count or a quantity, when it is not
    value_t     TEXT,               -- a word, when it is a word ('sale'...)
    denom_n     INTEGER,            -- how many units it SHOULD have covered
    covered_n   INTEGER,            -- how many it actually covered
    uncovered_n INTEGER,            -- denom_n - covered_n, stored not implied
    uncovered_p INTEGER,            -- the money it could not reach, when knowable
    unit        TEXT,               -- paise | items | lines
    basis       TEXT    NOT NULL,   -- how it was computed, in plain words
    source      TEXT    NOT NULL,   -- the tables it rests on
    as_of       TEXT,               -- the date the VALUE is true for
    run_id      INTEGER NOT NULL,
    computed_at TEXT    NOT NULL,
    PRIMARY KEY (scope, scope_key, figure)
);
CREATE INDEX IF NOT EXISTS ix_marg_figure_fig ON marg_figure(figure);
CREATE INDEX IF NOT EXISTS ix_marg_figure_run ON marg_figure(run_id);

-- One row per pass, so any figure on a screen can say which run produced it
-- and what that run could see.
CREATE TABLE IF NOT EXISTS marg_derive_run (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at   TEXT NOT NULL,
    finished_at  TEXT,
    mode         TEXT NOT NULL,
    figures      INTEGER,
    swept        INTEGER,
    spine_run_id INTEGER,
    spine_built  TEXT,
    snapshot     TEXT,
    notes        TEXT
);
"""


def ensure_schema(con):
    con.executescript(SCHEMA_SQL)
    con.commit()


def tables(con):
    return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}


# --------------------------------------------------------------------------- #
# THE PASS
# --------------------------------------------------------------------------- #

class Deriver(object):
    def __init__(self, con, ms, out=print):
        self.con = con
        self.ms = ms
        self.out = out
        self.T = tables(con)
        self.run_id = None
        self.n = 0
        self.swept = 0
        self.margin_med, self.margin_ortho = margins(con)
        self.spine = None
        self._fact = {}
        self._manual = {}
        self._price = {}
        self._canon = {}        # item_id -> canonical_raw
        self._merged = {}       # item_id -> the id it was merged into
        self._cov = {}          # item_id -> sale lines the observed price rests on
        self._typed = dict(read=0, used=0, unresolved=0, collided=0, refused=0)
        self._merge_faults = 0

    # -- plumbing ----------------------------------------------------------
    def put(self, scope, key, figure, basis, source,
            value_p=None, value_n=None, value_t=None,
            denom_n=None, covered_n=None, uncovered_p=None,
            unit=None, as_of=None):
        unc = None if (denom_n is None or covered_n is None) else int(denom_n) - int(covered_n)
        self.con.execute(
            "INSERT INTO marg_figure(scope,scope_key,figure,value_p,value_n,value_t,"
            "denom_n,covered_n,uncovered_n,uncovered_p,unit,basis,source,as_of,run_id,computed_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(scope,scope_key,figure) DO UPDATE SET "
            "value_p=excluded.value_p, value_n=excluded.value_n, value_t=excluded.value_t, "
            "denom_n=excluded.denom_n, covered_n=excluded.covered_n, "
            "uncovered_n=excluded.uncovered_n, uncovered_p=excluded.uncovered_p, "
            "unit=excluded.unit, basis=excluded.basis, source=excluded.source, "
            "as_of=excluded.as_of, run_id=excluded.run_id, computed_at=excluded.computed_at",
            (scope, str(key), figure, value_p, value_n, value_t,
             denom_n, covered_n, unc, uncovered_p, unit, basis, source, as_of,
             self.run_id, now_ist()))
        self.n += 1

    def sweep(self):
        """Delete every figure this pass did not write.

        Without this a figure OUTLIVES the data it was derived from: delete a
        month's sale lines and its money stays on the table under the next
        run's header.  A stale derived figure is worse than a missing one,
        because nothing about it looks wrong."""
        cur = self.con.execute("DELETE FROM marg_figure WHERE run_id <> ?", (self.run_id,))
        self.swept = cur.rowcount or 0
        return self.swept

    # -- the spine ---------------------------------------------------------
    def load_spine(self):
        need = {"marg_item", "marg_item_name", "marg_item_fact"}
        missing = need - self.T
        if missing:
            raise SystemExit(
                "REFUSING: the item spine is not built in this database "
                "(missing: %s).\nRun marg_spine.py --install first. Nothing was touched."
                % ", ".join(sorted(missing)))
        self.spine = self.ms.Spine(self.con)
        self.spine.load()
        for iid, f, v, cov in self.con.execute(
                "SELECT item_id, fact, value, coverage_n FROM marg_item_fact "
                "WHERE fact IN ('mrp_p','cost_p')"):
            try:
                self._fact.setdefault(iid, {})[f] = int(v)
                if f == "mrp_p":
                    self._cov[iid] = cov
            except (TypeError, ValueError):
                pass
        rows = self.con.execute(
            "SELECT item_id, canonical_raw, status, merged_into FROM marg_item").fetchall()
        for iid, raw, status, into in rows:
            self._canon[iid] = raw
        for iid, raw, status, into in rows:
            if status != "merged" or not into:
                continue
            # A merge pointing at a product that does not exist would silently
            # vaporise a real price, and the item row would then say "cannot be
            # priced at all" -- which is not why.  Refuse it and count it.
            if into not in self._canon:
                self._merge_faults += 1
                continue
            self._merged[iid] = into
        # and refuse every merge that cannot reach a real, unmerged product.
        # TWO passes, and the order matters: remove every member of every
        # cycle FIRST, then the chains that lead into one. Removing them as
        # they are met leaves whichever arm was walked second looking valid,
        # so two identically-placed products resolve differently -- which is
        # worse than either answer, because it is not reproducible.
        colour = {}                      # 0 = walking, 1 = settled
        on_cycle = set()
        for start in list(self._merged):
            if colour.get(start):
                continue
            path, cur = [], start
            while cur in self._merged and colour.get(cur) is None:
                colour[cur] = 0
                path.append(cur)
                cur = self._merged[cur]
            if colour.get(cur) == 0:     # walked into the path we are on
                on_cycle.update(path[path.index(cur):])
            for nid in path:
                colour[nid] = 1
        for nid in on_cycle:
            self._merged.pop(nid, None)
            self._merge_faults += 1
        for iid in list(self._merged):
            cur, ok, guard = iid, False, 0
            while guard <= len(self._merged) + 1:
                guard += 1
                if cur not in self._merged:
                    ok = cur in self._canon
                    break
                cur = self._merged[cur]
            if not ok:
                self._merged.pop(iid, None)
                self._merge_faults += 1
        if "stock_mrp_manual" in self.T:
            try:
                for it, p in self.con.execute("SELECT item, mrp_p FROM stock_mrp_manual"):
                    self._typed["read"] += 1
                    try:
                        p = int(p)
                    except (TypeError, ValueError):
                        self._typed["refused"] += 1
                        continue
                    # A typed price of zero or less is a keying slip, and one
                    # minus sign would take its whole shelf line off the total
                    # while the coverage count went UP.  Refused, and counted.
                    if p <= 0:
                        self._typed["refused"] += 1
                        continue
                    iid = self.resolve(it, "stock_mrp_manual")
                    if iid is None:
                        self._typed["unresolved"] += 1
                        continue
                    cid = self.canonical_id(iid)
                    if cid in self._manual:
                        self._typed["collided"] += 1
                        continue          # first writer wins, and it is reported
                    self._manual[cid] = p
                    self._typed["used"] += 1
            except sqlite3.Error:
                pass

    def canonical_id(self, iid):
        """Follow a merge to the product that survived, so two names of one
        product can never be counted as two."""
        seen = set()
        while iid in self._merged and iid not in seen:
            seen.add(iid)
            iid = self._merged[iid]
        return iid

    def resolve(self, raw, table):
        w = self.ms.SOURCE_WIDTH.get(table)
        if w is None and EXTRA_WIDTH.get(table) == "purchase":
            w = getattr(self.ms, "W_PURCHASE", None)
        iid, _, _ = self.spine.resolve(raw, w)
        return iid

    def price_of(self, item_id):
        """(paise per unit, rung) for a product.

        A cost wearing an MRP label is the fault this whole layer corrects,
        so the estimate is LABELLED as one and never silently promoted."""
        if item_id is None:
            return (None, "none")
        item_id = self.canonical_id(item_id)
        if item_id in self._price:
            return self._price[item_id]
        f = self._fact.get(item_id, {})
        raw = self._canon.get(item_id, "")
        if "mrp_p" in f:
            out = (f["mrp_p"], "sale")
        elif item_id in self._manual:
            out = (self._manual[item_id], "manual")
        elif "cost_p" in f:
            m = self.margin_ortho if is_ortho(raw) else self.margin_med
            out = (int(round(f["cost_p"] / max(0.05, 1.0 - m))), "provisional")
        else:
            out = (None, "none")
        self._price[item_id] = out
        return out

    # -- figure families ---------------------------------------------------
    def item_prices(self):
        """One row per product -- EVERY product, whatever its status, so the
        per-item rows and the estate totals can always be reconciled."""
        rows = self.con.execute(
            "SELECT item_id, canonical_raw, status FROM marg_item").fetchall()
        basis = {
            "sale": "MEDIAN of amount/pack over this product's own non-return sale lines, "
                    "across every name it has worn. The covered count is how many lines "
                    "that median rests on.",
            "manual": "a price a PERSON typed into stock_mrp_manual. Not an observation -- "
                      "carried so that no screen can disagree with it.",
            "provisional": "ESTIMATE -- last purchase rate grossed up by the margin. Not an "
                           "observed price, and it reads low for appliances.",
            "none": "no observed sale price, no typed price and no purchase rate: this "
                    "product cannot be priced at all.",
        }
        for iid, raw, status in rows:
            cid = self.canonical_id(iid)
            p, rung = self.price_of(cid)
            note = "" if status == "active" else \
                "  This product is %s; the price is the one its surviving record carries." % status
            self.put("item", iid, "price_p",
                     basis=basis[rung] + note,
                     source="marg_item_fact (mrp_p, cost_p) + stock_mrp_manual, via marg_item_name",
                     value_p=p, value_t=rung,
                     covered_n=(self._cov.get(cid) if rung == "sale" else 0),
                     unit="paise")
        return len(rows)

    def estate(self, as_on):
        """The shelf, and how much of it can be priced at all.

        Quantities are aggregated BY PRODUCT, not by spelling.  Two names of
        one product on one snapshot are one product holding the sum -- which
        is the entire reason the spine exists."""
        if "stock_snapshot" not in self.T or not as_on:
            return
        pos = {}          # product -> stock it actually holds
        neg = {}          # product -> stock recorded BELOW ZERO, positive
        collided_qty = {}
        rows = 0
        unresolved = 0
        collisions = 0
        for it, qn in self.con.execute(
                "SELECT item, qty FROM stock_snapshot WHERE as_on=?", (as_on,)):
            rows += 1
            iid = self.resolve(it, "stock_snapshot")
            if iid is None:
                # A name the spine cannot place is NOT a product. Counting it
                # as one and again as the gap would report 376 products and 3
                # missing out of 379, when the truth is 376 rows, 373 products.
                unresolved += 1
                continue
            key = self.canonical_id(iid)
            if key in pos or key in neg:
                collisions += 1
                # only the POSITIVE part of a colliding row reaches the shelf
                # total; its negative part goes to the below-zero figures, and
                # reporting it here as shelf money would misattribute it
                collided_qty[key] = (collided_qty.get(key) or 0) + max(0, qn or 0)
            # THE SIGN IS A PROPERTY OF THE ROW, not of the sum. Adding a -40
            # row to a +761 row before testing would net the fault away one
            # level up -- which is the very thing below_zero_items exists to
            # stop, moved from the row to the product.
            qn = qn or 0
            if qn < 0:
                neg[key] = (neg.get(key) or 0) + (-qn)
            else:
                pos[key] = (pos.get(key) or 0) + qn
        qty = dict(pos)
        for k in neg:
            qty.setdefault(k, 0)
        iso = iso_of(as_on)
        observed = estimated = manual = 0
        val_mrp = 0
        unreach = 0
        bz_items = bz_val = bz_unpriced = 0
        collided_p = 0
        for key in qty:
            p, rung = self.price_of(key)
            if rung == "sale":
                observed += 1
            elif rung == "manual":
                manual += 1
            elif rung == "provisional":
                estimated += 1
            if p is None:
                unreach += 1
            else:
                val_mrp += int(round(p * pos.get(key, 0)))
                collided_p += int(round(p * collided_qty.get(key, 0)))
            # Stock recorded below zero is a DATA FAULT (D398 -- a purchase
            # that never arrived, or a return keyed against nothing), not
            # negative value. It is never subtracted from the shelf: on the
            # 08-Sep data twelve products worth Rs 98,503.63 would have come
            # off the total, invisibly.
            if neg.get(key):
                bz_items += 1
                if p is None:
                    bz_unpriced += 1
                else:
                    bz_val += int(round(p * neg[key]))
        n = len(qty)
        self.put("estate", "", "items_on_shelf",
                 basis="distinct PRODUCTS in the newest stock snapshot -- resolved through "
                       "the spine, so two spellings of one product are one product. The "
                       "denominator is snapshot ROWS; the uncovered count is rows whose "
                       "name resolves to no product and which are therefore in no figure "
                       "on this page.",
                 source="stock_snapshot + marg_item_name",
                 value_n=n, unit="items", as_of=iso,
                 denom_n=rows, covered_n=rows - unresolved)
        self.put("estate", "", "shelf_name_collisions",
                 basis="snapshot rows that resolved onto a product another row had already "
                       "claimed. Zero is the expected answer. Anything else is two spellings "
                       "of one product on one day: their quantities are SUMMED, which is "
                       "right if Marg really holds the stock split across two records and "
                       "wrong if the same stock was exported twice -- and this file cannot "
                       "tell those apart. The uncovered money is what the second and later "
                       "rows put INTO THE SHELF TOTAL -- their positive stock only -- so "
                       "the size of that doubt is stated. A negative colliding row moves no "
                       "shelf money and is in the below-zero figures instead.",
                 source="stock_snapshot + marg_item_name",
                 value_n=collisions, unit="items", as_of=iso,
                 uncovered_p=collided_p)
        self.put("estate", "", "items_priced",
                 basis="products with a price on any rung of the ladder, through the spine. "
                       "The uncovered count is products no price can reach at all.",
                 source="stock_snapshot + marg_item_fact",
                 value_n=observed + manual + estimated, unit="items", as_of=iso,
                 denom_n=n, covered_n=observed + manual + estimated)
        self.put("estate", "", "items_priced_observed",
                 basis="of the priced products, how many carry a REAL price from their own "
                       "sale lines. A breakdown, not a coverage: it has no denominator.",
                 source="stock_snapshot + marg_item_fact(mrp_p)",
                 value_n=observed, unit="items", as_of=iso)
        self.put("estate", "", "items_priced_manual",
                 basis="of the priced products, how many stand on a price a person typed. "
                       "A breakdown, not a coverage.",
                 source="stock_snapshot + stock_mrp_manual",
                 value_n=manual, unit="items", as_of=iso)
        self.put("estate", "", "items_priced_estimated",
                 basis="of the priced products, how many stand only on an ESTIMATE grossed "
                       "up from the purchase rate. A breakdown, not a coverage.",
                 source="stock_snapshot + marg_item_fact(cost_p)",
                 value_n=estimated, unit="items", as_of=iso)
        self.put("estate", "", "shelf_value_mrp_p",
                 basis="price per unit x the stock a product actually holds, summed. Rows "
                       "recorded below zero contribute NOTHING here -- they are a fault, "
                       "counted separately, never a deduction. The uncovered count is "
                       "products no price can reach, whose value is not in this total and "
                       "cannot be; it is counted ONCE, so a product that is both unpriced "
                       "and below zero is one gap, not two. Below-zero stock is not a "
                       "coverage gap here at all -- there is no positive value missing -- "
                       "and it has its own two figures.",
                 source="stock_snapshot + marg_item_fact",
                 value_p=val_mrp, unit="paise", as_of=iso,
                 denom_n=n, covered_n=n - unreach)
        self.put("estate", "", "below_zero_items",
                 basis="products whose recorded stock is less than zero -- a purchase that "
                       "never arrived, or a return keyed against nothing (D398). Never a "
                       "negative value: a fault with a count.",
                 source="stock_snapshot",
                 value_n=bz_items, unit="items", as_of=iso)
        self.put("estate", "", "below_zero_value_p",
                 basis="what the below-zero quantities would be worth at their own price, "
                       "stated POSITIVE as the size of the fault. It is not stock and it is "
                       "not in the shelf total. The uncovered count is those with no price, "
                       "so the fault is larger than this figure by an unknown amount.",
                 source="stock_snapshot + marg_item_fact",
                 value_p=bz_val, unit="paise", as_of=iso,
                 denom_n=bz_items, covered_n=bz_items - bz_unpriced)

    def inputs(self):
        """What the pass had to work with, and what it refused.

        These describe marg_item and stock_mrp_manual, so they are written
        whether or not a stock snapshot exists -- in v3 they lived inside the
        shelf family and vanished the moment the snapshot did, taking the
        record of a refused typed price with them."""
        self.put("estate", "", "merge_faults",
                 basis="merges the spine records that this pass REFUSED to follow -- a "
                       "target that does not exist, or a chain that never reaches a real "
                       "product. Following one would have vaporised a real price and then "
                       "said the product could not be priced at all. Zero is expected.",
                 source="marg_item(status, merged_into)",
                 value_n=self._merge_faults, unit="items")
        if "stock_mrp_manual" not in self.T:
            return
        t = self._typed
        self.put("estate", "", "typed_prices",
                 basis="prices a person typed into stock_mrp_manual: how many were read, "
                       "and how many actually reached a product. The uncovered count is "
                       "those refused (zero, less, or unreadable), those whose name matches "
                       "no product, and those landing on a product another typed row had "
                       "already claimed. With none typed at all there is nothing to cover, "
                       "so no denominator is stated.",
                 source="stock_mrp_manual + marg_item_name",
                 value_n=t["used"], unit="items",
                 denom_n=(t["read"] or None),
                 covered_n=(t["used"] if t["read"] else None))

    def months(self):
        """The sale lane, month by month, weighted properly.

        amount_p is the price of ONE PACK, not the line total.  Summing it
        unweighted answers no question -- and one live screen does exactly
        that today (F-379), which is why these figures exist."""
        if "sale_line_item" not in self.T:
            return
        vocab = []
        try:
            r = self.con.execute(
                "SELECT value FROM setting WHERE key='orthotics.vocab'").fetchone()
            if not r:
                r = self.con.execute(
                    "SELECT value FROM setting WHERE key LIKE '%orthotic%' "
                    "ORDER BY key LIMIT 1").fetchone()
            if r and r[0]:
                vocab = [t.strip().upper() for t in str(r[0]).split(",") if t.strip()]
        except sqlite3.Error:
            pass
        buckets = {}
        undated = 0
        undated_p = 0
        for bd, nm, key, qty, pack, amt, isret in self.con.execute(
                "SELECT business_date, item_name, item_key, qty_raw, pack, amount_p, is_return "
                "FROM sale_line_item"):
            ym = month_of(bd)
            v = self.ms.mrp_value_p(amt, qty, pack)
            if ym is None:
                undated += 1
                undated_p += v or 0
                continue
            b = buckets.setdefault(ym, dict(
                lines=0, ret_lines=0, val=0, ret_val=0, tied_val=0, tied=0,
                readable=0, unread=0, unread_p=0, ret_readable=0, ret_unread_p=0,
                orth_lines=0, orth_val=0, untied_p=0, packbad=0, ret_packbad=0))
            # "readable" means the weighting was real: a quantity we can read
            # AND a price to weight.  A NULL price is not zero money, it is
            # money we cannot see, and it is disclosed rather than absorbed.
            readable = (self.ms.packs_sold(qty, pack) is not None) and (amt is not None)
            # an unreadable pack string is counted on ITS OWN lane: charging a
            # return line against the non-return figure is the exact fault v1
            # had elsewhere, and it silently cost 42 lines across six months
            badpack = bool(str(pack or "").strip()) and self.ms.pack_units(pack) is None
            if isret:
                b["ret_lines"] += 1
                b["ret_val"] += v
                if badpack:
                    b["ret_packbad"] += 1
                if readable:
                    b["ret_readable"] += 1
                else:
                    b["ret_unread_p"] += v or 0
                continue
            if badpack:
                b["packbad"] += 1
            b["lines"] += 1
            b["val"] += v
            if readable:
                b["readable"] += 1
            else:
                b["unread"] += 1
                b["unread_p"] += v or 0
            iid = self.resolve(key or nm, "sale_line_item")
            if iid:
                b["tied"] += 1
                b["tied_val"] += v
            else:
                b["untied_p"] += v
            if vocab and any(w in (nm or "").upper() for w in vocab):
                b["orth_lines"] += 1
                b["orth_val"] += v
        src = "sale_line_item"
        for ym in sorted(buckets):
            b = buckets[ym]
            if not b["lines"] and not b["ret_lines"]:
                continue
            if b["lines"]:
                self.put("month", ym, "sale_value_mrp_p",
                         basis="sum of (pack price x packs sold) over NON-RETURN lines. A "
                               "line whose quantity cannot be read is counted ONCE, never "
                               "guessed at, and a line with no price at all is money we "
                               "cannot see; the uncovered count and money are both.",
                         source=src, value_p=b["val"], unit="paise", as_of=ym,
                         denom_n=b["lines"], covered_n=b["readable"],
                         uncovered_p=b["unread_p"])
                self.put("month", ym, "sale_value_tied_p",
                         basis="the part of the month's sale value that resolves to a known "
                               "product. The uncovered money is real sales the shelf cannot "
                               "account for -- clipped or renamed names awaiting a task.",
                         source=src + " + marg_item_name",
                         value_p=b["tied_val"], unit="paise", as_of=ym,
                         denom_n=b["lines"], covered_n=b["tied"], uncovered_p=b["untied_p"])
                self.put("month", ym, "sale_lines",
                         basis="non-return sale lines in the month. The uncovered count is "
                               "those whose pack string cannot be read, so a part-pack "
                               "quantity on one of them would be lost silently.",
                         source=src, value_n=b["lines"], unit="lines", as_of=ym,
                         denom_n=b["lines"], covered_n=b["lines"] - b["packbad"])
            if b["ret_lines"]:
                self.put("month", ym, "sale_return_lines",
                         basis="return lines in the month. The uncovered count is those "
                               "whose pack string cannot be read -- the same disclosure the "
                               "sale lane carries, so neither lane is quietly the tidier one.",
                         source=src, value_n=b["ret_lines"], unit="lines", as_of=ym,
                         denom_n=b["ret_lines"], covered_n=b["ret_lines"] - b["ret_packbad"])
                self.put("month", ym, "sale_return_value_p",
                         basis="the same arithmetic over RETURN lines, kept separate rather "
                               "than netted, so neither hides the other. Coverage is measured "
                               "the same way and is never assumed perfect.",
                         source=src, value_p=b["ret_val"], unit="paise", as_of=ym,
                         denom_n=b["ret_lines"], covered_n=b["ret_readable"],
                         uncovered_p=b["ret_unread_p"])
            if vocab and b["orth_lines"]:
                self.put("month", ym, "orthotics_value_p",
                         basis="orthotic sales, WEIGHTED by packs sold. The live approvals "
                               "page sums the pack price once per line and labels it "
                               "'Amount' (F-379), so it reads low.",
                         source=src + " + setting(orthotics.vocab)",
                         value_p=b["orth_val"], unit="paise", as_of=ym,
                         denom_n=b["orth_lines"], covered_n=b["orth_lines"])
        self.put("estate", "", "sale_lines_undated",
                 basis="sale lines whose business_date is not a real ISO date and which "
                       "therefore belong to no month. They are in NO month figure. Zero is "
                       "the expected answer.",
                 source=src, value_n=undated, unit="lines", uncovered_p=undated_p)

    # -- the run -----------------------------------------------------------
    def run(self, mode="build"):
        ensure_schema(self.con)
        cur = self.con.execute(
            "INSERT INTO marg_derive_run(started_at,mode) VALUES(?,?)", (now_ist(), mode))
        self.run_id = cur.lastrowid
        self.load_spine()
        sr = self.con.execute(
            "SELECT id, finished_at FROM marg_spine_run ORDER BY id DESC LIMIT 1").fetchone()
        as_on = newest_snapshot(self.con)
        self.out("  spine build #%s of %s" % (sr[0] if sr else "-", sr[1] if sr else "-"))
        self.out("  newest snapshot: %s" % (as_on or "none"))
        n_items = self.item_prices()
        self.out("  item prices: %d" % n_items)
        self.estate(as_on)
        self.inputs()
        self.months()
        self.sweep()
        # put() upserts, so two families writing one key would overwrite in
        # silence and the run row would claim more figures than exist. The
        # count is stored as MEASURED, and a mismatch is recorded as a note
        # rather than left for a reader to notice.
        held = self.con.execute("SELECT COUNT(*) FROM marg_figure WHERE run_id=?",
                                (self.run_id,)).fetchone()[0]
        note = None
        if held != self.n:
            note = ("%d put() calls produced %d rows: two figure families wrote the same "
                    "key and one overwrote the other." % (self.n, held))
            self.out("  !! " + note)
        self.con.execute(
            "UPDATE marg_derive_run SET finished_at=?, figures=?, swept=?, spine_run_id=?, "
            "spine_built=?, snapshot=?, notes=? WHERE id=?",
            (now_ist(), held, self.swept, sr[0] if sr else None,
             sr[1] if sr else None, as_on, note, self.run_id))
        self.con.commit()
        self.out("  figures written: %d   stale figures swept: %d" % (held, self.swept))
        return held


# --------------------------------------------------------------------------- #
# REPORT
# --------------------------------------------------------------------------- #

def rs(p):
    return "-" if p is None else "Rs %s" % format(round(p / 100.0, 2), ",.2f")


def report(con, out=print):
    if "marg_figure" not in tables(con):
        out("No derivation has been run on this database.")
        return
    r = con.execute("SELECT id,finished_at,figures,swept,spine_run_id,snapshot "
                    "FROM marg_derive_run WHERE finished_at IS NOT NULL "
                    "ORDER BY id DESC LIMIT 1").fetchone()
    if not r:
        out("No completed derivation run recorded.")
        return
    run_id = r[0]
    out("run #%s  %s  figures=%s  swept=%s  spine build #%s  snapshot %s"
        % (r[0], r[1], r[2], r[3], r[4], r[5]))
    strays = con.execute("SELECT COUNT(*) FROM marg_figure WHERE run_id <> ?",
                         (run_id,)).fetchone()[0]
    if strays:
        out("  !! %d figure(s) are not from this run and are NOT shown. That should be "
            "impossible; the sweep did not happen." % strays)
    out("")
    out("THE SHELF")
    for f in ("items_on_shelf", "shelf_name_collisions", "items_priced",
              "items_priced_observed", "items_priced_manual", "items_priced_estimated",
              "shelf_value_mrp_p", "below_zero_items", "below_zero_value_p",
              "typed_prices", "merge_faults", "sale_lines_undated"):
        row = con.execute("SELECT value_p,value_n,denom_n,covered_n,uncovered_n "
                          "FROM marg_figure WHERE scope='estate' AND figure=? AND run_id=?",
                          (f, run_id)).fetchone()
        if not row:
            continue
        v = rs(row[0]) if row[0] is not None else ("%g" % row[1])
        what = "rows" if f == "items_on_shelf" else "" 
        cov = "" if row[2] is None else \
            "   covers %s of %s %s  (%s uncovered)" % (row[3], row[2], what, row[4])
        out("  %-24s %14s%s" % (f, v, cov))
    out("")
    out("THE SALE LANE, BY MONTH")
    out("  %-9s %14s %14s %8s %12s" % ("month", "sale value", "tied to shelf", "lines", "untied"))
    for ym, in con.execute("SELECT DISTINCT scope_key FROM marg_figure "
                           "WHERE scope='month' AND run_id=? ORDER BY scope_key", (run_id,)):
        g = {f: (vp, vn, dn, cn, up) for f, vp, vn, dn, cn, up in con.execute(
            "SELECT figure,value_p,value_n,denom_n,covered_n,uncovered_p "
            "FROM marg_figure WHERE scope='month' AND scope_key=? AND run_id=?", (ym, run_id))}
        sv, tv, sl = g.get("sale_value_mrp_p"), g.get("sale_value_tied_p"), g.get("sale_lines")
        out("  %-9s %14s %14s %8s %12s"
            % (ym, rs(sv[0]) if sv else "-", rs(tv[0]) if tv else "-",
               int(sl[1]) if sl else "-", rs(tv[4]) if tv and tv[4] else "-"))
    out("")
    out("PRICE RUNGS")
    for t, n in con.execute("SELECT value_t, COUNT(*) FROM marg_figure "
                            "WHERE scope='item' AND figure='price_p' AND run_id=? "
                            "GROUP BY value_t ORDER BY 2 DESC", (run_id,)):
        out("  %-14s %4d" % (t, n))


# --------------------------------------------------------------------------- #
# SELFTEST
# --------------------------------------------------------------------------- #

def _fixture(ms):
    """A small database with the shapes that matter.

    A green fixture proves the kit, not the join -- and every fixture here was
    written by this file's own author, which is exactly how a defect survived
    24 of them at S234.  So these prove the RULES; the proof that matters is
    --dry-run against the real database, and an adversarial reader."""
    con = sqlite3.connect(":memory:")
    con.executescript(open(os.path.join(HERE, "..", "S229_ITEM_SPINE",
                                        "marg_spine_schema.sql")).read())
    con.executescript("""
    CREATE TABLE stock_snapshot(as_on TEXT,item TEXT,qty INTEGER,packing TEXT,pack_size INTEGER,source TEXT);
    CREATE TABLE stock_rate(item TEXT,rate_p INTEGER,pack_size INTEGER,as_of TEXT,source TEXT);
    CREATE TABLE stock_count_item(item TEXT,pack_size INTEGER);
    CREATE TABLE stock_mrp_manual(item TEXT PRIMARY KEY, mrp_p INTEGER);
    CREATE TABLE sale_line_item(business_date TEXT,item_name TEXT,item_key TEXT,pack TEXT,
                                qty_raw TEXT,amount_p INTEGER,is_return INTEGER);
    CREATE TABLE setting(key TEXT PRIMARY KEY,value TEXT);
    """)
    con.execute("INSERT INTO setting VALUES('orthotics.vocab','KNEE SUPPORT')")
    for it, q, pk in (("ACILOC 300", 100, "1*20"), ("KNEE SUPPORT HINGED L", 4, "1*1"),
                      ("ESTONLY ITEM", 5, "1*1"), ("MANUAL ITEM", 2, "1*1"),
                      ("NOPRICE ITEM", 7, "1*1"), ("BELOWZERO ITEM", -3, "1*1")):
        con.execute("INSERT INTO stock_snapshot VALUES('06-09-2026',?,?,?,?,'x')",
                    (it, q, pk, ms.pack_units(pk)))
        con.execute("INSERT INTO stock_count_item VALUES(?,?)", (it, ms.pack_units(pk)))
    # an OLDER snapshot, day-first, which naive text order would rank ABOVE 06-09
    con.execute("INSERT INTO stock_snapshot VALUES('27-08-2026','ACILOC 300',999,'1*20',20,'x')")
    con.execute("INSERT INTO stock_rate VALUES('KNEE SUPPORT HINGED L',100000,1,'05-09-2026','x')")
    con.execute("INSERT INTO stock_rate VALUES('ESTONLY ITEM',80000,1,'05-09-2026','x')")
    con.execute("INSERT INTO stock_rate VALUES('MANUAL ITEM',50000,1,'05-09-2026','x')")
    con.execute("INSERT INTO stock_rate VALUES('BELOWZERO ITEM',100000,1,'05-09-2026','x')")
    con.execute("INSERT INTO stock_mrp_manual VALUES('MANUAL ITEM',123456)")
    S = "INSERT INTO sale_line_item VALUES(?,?,?,?,?,?,?)"
    con.execute(S, ('2026-08-01', 'ACILOC 300', 'ACILOC 300', '1*20', '3:0', 6160, 0))
    con.execute(S, ('2026-08-02', 'ACILOC 300', 'ACILOC 300', '1*20', '1:0', 6160, 0))
    con.execute(S, ('2026-08-03', 'ACILOC 300', 'ACILOC 300', '1*20', '1:0', 6160, 1))
    # unreadable quantity -- counted once, never guessed
    con.execute(S, ('2026-08-04', 'ACILOC 300', 'ACILOC 300', '1*20', '?', 6160, 0))
    # NULL price -- money we cannot see, disclosed rather than absorbed as zero
    con.execute(S, ('2026-08-06', 'ACILOC 300', 'ACILOC 300', '1*20', '2:0', None, 0))
    # an unreadable RETURN, which must not flatter the return figure
    con.execute(S, ('2026-08-07', 'ACILOC 300', 'ACILOC 300', '1*20', '?', 5000, 1))
    # a REAL 20-character clip of 'KNEE SUPPORT HINGED L'
    con.execute(S, ('2026-08-05', 'KNEE SUPPORT HINGED', 'KNEE SUPPORT HINGED', '1*1', '2', 150000, 0))
    # a day-first date, which must NOT become a month called '07-09-2'
    con.execute(S, ('07-09-2026', 'ACILOC 300', 'ACILOC 300', '1*20', '1:0', 6160, 0))
    con.commit()
    return con


def selftest(out=print):
    ms = load_spine()
    fails = []
    n = [0]

    def ck(label, cond):
        n[0] += 1
        if not cond:
            fails.append(label)
        out("  %s %s" % ("ok  " if cond else "FAIL", label))

    # ---- arithmetic ------------------------------------------------------
    ck("3 packs of 20 at 6160p is 18480p", ms.mrp_value_p(6160, "3:0", "1*20") == 18480)
    ck("an unreadable quantity counts ONCE, not zero and not a guess",
       ms.mrp_value_p(6160, "?", "1*20") == 6160)
    ck("7 loose out of 20 is 0.35 of a pack", abs(ms.packs_sold("0:7", "1*20") - 0.35) < 1e-9)

    # ---- the date traps --------------------------------------------------
    ck("27-08-2026 sorts BELOW 06-09-2026 when keyed properly",
       date_key("27-08-2026") < date_key("06-09-2026"))
    ck("and the naive text order would have got it wrong", "27-08-2026" > "06-09-2026")
    ck("iso_of turns Marg's day-first into a real date", iso_of("06-09-2026") == "2026-09-06")
    ck("month_of reads an ISO date", month_of("2026-08-14") == "2026-08")
    ck("month_of REFUSES a day-first date rather than slicing it", month_of("07-09-2026") is None)
    ck("month_of refuses a 13th month", month_of("2026-13-01") is None)
    ck("month_of refuses rubbish", month_of("x") is None and month_of(None) is None)

    # ---- the ladder ------------------------------------------------------
    ck("an orthotic is recognised as one", is_ortho("KNEE SUPPORT HINGED L"))
    ck("a tablet is not", not is_ortho("ACILOC 300"))

    # ---- a whole pass ----------------------------------------------------
    con = _fixture(ms)
    ms.build(con, out=lambda *a: None)
    Deriver(con, ms, out=lambda *a: None).run("selftest")

    def g(s, k, f, c="value_p"):
        return con.execute("SELECT %s FROM marg_figure WHERE scope=? AND scope_key=? "
                           "AND figure=?" % c, (s, str(k), f)).fetchone()

    ck("the newest snapshot is used, not the one text order would pick",
       g("estate", "", "items_on_shelf", "value_n")[0] == 6)
    ck("no two spellings collided onto one product",
       g("estate", "", "shelf_name_collisions", "value_n")[0] == 0)
    # ACILOC + KNEE (both sale) + MANUAL (typed) + ESTONLY and BELOWZERO (estimates)
    ck("five products can be priced", g("estate", "", "items_priced", "value_n")[0] == 5)
    ck("two from their own sales -- one only because a clipped name tied back",
       g("estate", "", "items_priced_observed", "value_n")[0] == 2)
    ck("one from a price a person typed",
       g("estate", "", "items_priced_manual", "value_n")[0] == 1)
    mid = con.execute("SELECT item_id FROM marg_item WHERE canonical='MANUAL ITEM'").fetchone()[0]
    ck("a typed price BEATS the estimate, as it does on every live screen",
       g("item", mid, "price_p")[0] == 123456)
    ck("two are only an ESTIMATE", g("estate", "", "items_priced_estimated", "value_n")[0] == 2)
    ck("a breakdown carries NO denominator, so it cannot print a false gap",
       g("estate", "", "items_priced_observed", "denom_n")[0] is None)
    ck("but a real coverage does", g("estate", "", "items_priced", "denom_n")[0] == 6)

    # 100 ACILOC at 308p + 4 knee supports at 150000p + 5 ESTONLY at 80000/0.8
    #   + 2 MANUAL at 123456p ; NOPRICE unpriced ; BELOWZERO excluded
    ck("a below-zero quantity is NOT subtracted from the shelf total",
       g("estate", "", "shelf_value_mrp_p")[0] == 308 * 100 + 150000 * 4 + 100000 * 5 + 123456 * 2)
    ck("it is counted as a fault instead", g("estate", "", "below_zero_items", "value_n")[0] == 1)
    ck("and its size is stated POSITIVE, never as negative value",
       g("estate", "", "below_zero_value_p")[0] == 125000 * 3)
    ck("the fault count has no denominator either",
       g("estate", "", "below_zero_items", "denom_n")[0] is None)

    ck("the month's sale value weights by packs sold",
       g("month", "2026-08", "sale_value_mrp_p")[0] == 24640 + 6160 + 0 + 300000)
    ck("the return is NOT netted into the sale figure",
       g("month", "2026-08", "sale_return_value_p")[0] == 6160 + 5000)
    ck("the sale denominator counts SALE lines only, never returns",
       g("month", "2026-08", "sale_value_mrp_p", "denom_n")[0] == 5)
    ck("two sale lines could not be weighted: the unreadable one and the priceless one",
       g("month", "2026-08", "sale_value_mrp_p", "uncovered_n")[0] == 2)
    ck("the return figure does NOT claim perfect coverage",
       g("month", "2026-08", "sale_return_value_p", "uncovered_n")[0] == 1)
    ck("and the unreachable return money is stated",
       g("month", "2026-08", "sale_return_value_p", "uncovered_p")[0] == 5000)
    ck("the clipped orthotic name still ties to the shelf through the spine",
       g("month", "2026-08", "sale_value_tied_p", "uncovered_n")[0] == 0)
    ck("orthotics are weighted: 2 packs at 1500 is 3000, not 1500",
       g("month", "2026-08", "orthotics_value_p")[0] == 300000)
    ck("a day-first sale date creates NO phantom month",
       con.execute("SELECT COUNT(*) FROM marg_figure WHERE scope='month' AND "
                   "scope_key NOT LIKE '____-__'").fetchone()[0] == 0)
    ck("it is reported as undated instead",
       g("estate", "", "sale_lines_undated", "value_n")[0] == 1)

    # ---- the rules this file exists to enforce ---------------------------
    for label, sql in (
        ("uncovered_n is always denom_n minus covered_n",
         "SELECT COUNT(*) FROM marg_figure WHERE denom_n IS NOT NULL AND covered_n IS NOT NULL "
         "AND uncovered_n <> denom_n-covered_n"),
        ("every figure says in words how it was computed",
         "SELECT COUNT(*) FROM marg_figure WHERE basis IS NULL OR basis=''"),
        ("every figure names the tables it rests on",
         "SELECT COUNT(*) FROM marg_figure WHERE source IS NULL OR source=''"),
        ("no figure claims to cover more than exists",
         "SELECT COUNT(*) FROM marg_figure WHERE covered_n > denom_n"),
        ("no figure carries a coverage half-stated",
         "SELECT COUNT(*) FROM marg_figure WHERE (denom_n IS NULL) <> (uncovered_n IS NULL)"),
    ):
        ck(label, con.execute(sql).fetchone()[0] == 0)

    # ---- the CRITICAL one: a figure must never outlive its data ----------
    before = con.execute("SELECT COUNT(*) FROM marg_figure WHERE scope='month'").fetchone()[0]
    con.execute("DELETE FROM sale_line_item WHERE business_date LIKE '2026-08%'")
    con.commit()
    Deriver(con, ms, out=lambda *a: None).run("selftest")
    ck("when a month's data is deleted, its figures are SWEPT, not left standing",
       before > 0 and con.execute("SELECT COUNT(*) FROM marg_figure WHERE scope='month' "
                                  "AND scope_key='2026-08'").fetchone()[0] == 0)
    rid = con.execute("SELECT MAX(id) FROM marg_derive_run").fetchone()[0]
    ck("and nothing from an older run survives at all",
       con.execute("SELECT COUNT(*) FROM marg_figure WHERE run_id <> ?", (rid,)).fetchone()[0] == 0)

    con2 = _fixture(ms)
    ms.build(con2, out=lambda *a: None)
    Deriver(con2, ms, out=lambda *a: None).run("selftest")
    con2.execute("DELETE FROM stock_snapshot")
    con2.commit()
    Deriver(con2, ms, out=lambda *a: None).run("selftest")
    ck("when the shelf disappears, the shelf figures disappear with it",
       con2.execute("SELECT COUNT(*) FROM marg_figure WHERE figure='shelf_value_mrp_p'"
                    ).fetchone()[0] == 0)

    # ---- a merged product is ONE product ---------------------------------
    con3 = _fixture(ms)
    ms.build(con3, out=lambda *a: None)
    a = con3.execute("SELECT item_id FROM marg_item WHERE canonical='ESTONLY ITEM'").fetchone()[0]
    b = con3.execute("SELECT item_id FROM marg_item WHERE canonical='NOPRICE ITEM'").fetchone()[0]
    con3.execute("UPDATE marg_item SET status='merged', merged_into=? WHERE item_id=?", (a, b))
    con3.commit()
    Deriver(con3, ms, out=lambda *a: None).run("selftest")
    ck("a merged product still gets a row, so per-item and estate reconcile",
       con3.execute("SELECT COUNT(*) FROM marg_figure WHERE scope='item' AND scope_key=?",
                    (str(b),)).fetchone()[0] == 1)
    ck("and it takes the price of the product it merged INTO",
       con3.execute("SELECT value_p FROM marg_figure WHERE scope='item' AND scope_key=? "
                    "AND figure='price_p'", (str(b),)).fetchone()[0] == 100000)
    ck("the two of them count as ONE product on the shelf",
       con3.execute("SELECT value_n FROM marg_figure WHERE scope='estate' AND "
                    "figure='items_on_shelf'").fetchone()[0] == 5)

    # ---- idempotence -----------------------------------------------------
    cols = ("scope,scope_key,figure,value_p,value_n,value_t,denom_n,covered_n,"
            "uncovered_n,uncovered_p,basis,source,as_of")
    con4 = _fixture(ms)
    ms.build(con4, out=lambda *a: None)
    Deriver(con4, ms, out=lambda *a: None).run("selftest")
    s1 = con4.execute("SELECT %s FROM marg_figure ORDER BY 1,2,3" % cols).fetchall()
    Deriver(con4, ms, out=lambda *a: None).run("selftest")
    s2 = con4.execute("SELECT %s FROM marg_figure ORDER BY 1,2,3" % cols).fetchall()
    ck("running it twice changes nothing but the timestamp and the run id", s1 == s2)

    # ---- it must never write to anything that existed before -------------
    ck("no existing table was touched: snapshot unchanged",
       con4.execute("SELECT COUNT(*) FROM stock_snapshot").fetchone()[0] == 7)
    ck("no existing table was touched: sale lines unchanged",
       con4.execute("SELECT COUNT(*) FROM sale_line_item").fetchone()[0] == 8)

    # ---- v2's own faults, each found by an adversarial reader ------------
    ck("a margin typed as 30 means 30 per cent, not minus twenty-nine",
       abs(_fraction(30, 0.20) - 0.30) < 1e-9 and abs(_fraction(0.30, 0.20) - 0.30) < 1e-9)
    ck("and a margin that cannot be one at all falls back",
       _fraction(0.99, 0.20) == 0.20 and _fraction("x", 0.20) == 0.20)

    con5 = _fixture(ms)
    ms.build(con5, out=lambda *a: None)
    # an unreadable pack on BOTH lanes: the return one must not be charged to
    # the sale figure's coverage
    S5 = "INSERT INTO sale_line_item VALUES(?,?,?,?,?,?,?)"
    con5.execute(S5, ('2026-08-08', 'ACILOC 300', 'ACILOC 300', 'VAIL', '1', 100, 0))
    con5.execute(S5, ('2026-08-09', 'ACILOC 300', 'ACILOC 300', 'VAIL', '1', 100, 1))
    con5.commit()
    Deriver(con5, ms, out=lambda *a: None).run("selftest")
    q5 = lambda f, c: con5.execute("SELECT %s FROM marg_figure WHERE scope='month' AND "
                                   "scope_key='2026-08' AND figure=?" % c, (f,)).fetchone()[0]
    ck("one unreadable pack on a SALE line costs the sale figure one line",
       q5("sale_lines", "uncovered_n") == 1)
    ck("and the unreadable pack on a RETURN line costs it nothing",
       q5("sale_lines", "denom_n") == 6 and q5("sale_lines", "covered_n") == 5)

    # a snapshot row the spine cannot place: NOT a product, and not silently lost
    con5.execute("INSERT INTO stock_snapshot VALUES('06-09-2026','ZZ NOT A THING',5,'1*1',1,'x')")
    con5.commit()
    Deriver(con5, ms, out=lambda *a: None).run("selftest")
    e5 = lambda f, c: con5.execute("SELECT %s FROM marg_figure WHERE scope='estate' AND "
                                   "figure=?" % c, (f,)).fetchone()[0]
    ck("an unplaceable snapshot row is NOT counted as a product",
       e5("items_on_shelf", "value_n") == 6)
    ck("it is the denominator's gap instead, so nothing is lost quietly",
       e5("items_on_shelf", "denom_n") == 7 and e5("items_on_shelf", "uncovered_n") == 1)

    # a typed price that is negative, one that matches nothing, two on one product
    con6 = _fixture(ms)
    ms.build(con6, out=lambda *a: None)
    con6.execute("INSERT INTO stock_mrp_manual VALUES('ACILOC 300',-500000)")
    con6.execute("INSERT INTO stock_mrp_manual VALUES('TOTALLY UNKNOWN THING',9999)")
    con6.commit()
    Deriver(con6, ms, out=lambda *a: None).run("selftest")
    e6 = lambda f, c: con6.execute("SELECT %s FROM marg_figure WHERE scope='estate' AND "
                                   "figure=?" % c, (f,)).fetchone()[0]
    ck("a NEGATIVE typed price is refused, not multiplied into the shelf total",
       con6.execute("SELECT value_p FROM marg_figure WHERE scope='item' AND figure='price_p' "
                    "AND value_t='sale' AND scope_key=?",
                    (str(con6.execute("SELECT item_id FROM marg_item WHERE canonical="
                                      "'ACILOC 300'").fetchone()[0]),)).fetchone()[0] == 308)
    ck("three typed prices were read and only one reached a product",
       e6("typed_prices", "denom_n") == 3 and e6("typed_prices", "covered_n") == 1)
    ck("so the two that did not are stated, not discarded in silence",
       e6("typed_prices", "uncovered_n") == 2)

    # a merge pointing at nothing, and a cycle
    con7 = _fixture(ms)
    ms.build(con7, out=lambda *a: None)
    aa = con7.execute("SELECT item_id FROM marg_item WHERE canonical='ACILOC 300'").fetchone()[0]
    bb = con7.execute("SELECT item_id FROM marg_item WHERE canonical='ESTONLY ITEM'").fetchone()[0]
    cc = con7.execute("SELECT item_id FROM marg_item WHERE canonical='MANUAL ITEM'").fetchone()[0]
    con7.execute("UPDATE marg_item SET status='merged', merged_into=99999 WHERE item_id=?", (bb,))
    con7.execute("UPDATE marg_item SET status='merged', merged_into=? WHERE item_id=?", (cc, aa))
    con7.execute("UPDATE marg_item SET status='merged', merged_into=? WHERE item_id=?", (aa, cc))
    con7.commit()
    Deriver(con7, ms, out=lambda *a: None).run("selftest")
    ck("a merge pointing at a product that does not exist is REFUSED and counted",
       con7.execute("SELECT value_n FROM marg_figure WHERE scope='estate' AND "
                    "figure='merge_faults'").fetchone()[0] >= 1)
    ck("and the product keeps its own price instead of vanishing",
       con7.execute("SELECT value_p FROM marg_figure WHERE scope='item' AND scope_key=? "
                    "AND figure='price_p'", (str(bb),)).fetchone()[0] == 100000)
    ck("a merge cycle terminates and is refused, not followed to itself",
       con7.execute("SELECT value_n FROM marg_figure WHERE scope='estate' AND "
                    "figure='merge_faults'").fetchone()[0] >= 3)

    # the run row must not be able to claim more figures than exist
    for c in (con5, con6, con7):
        rid2 = c.execute("SELECT MAX(id) FROM marg_derive_run").fetchone()[0]
        ck("the run's figure count is measured, not counted on trust (run %d)" % rid2,
           c.execute("SELECT figures FROM marg_derive_run WHERE id=?", (rid2,)).fetchone()[0]
           == c.execute("SELECT COUNT(*) FROM marg_figure").fetchone()[0])

    # ---- v3's own faults, each found by the same adversarial reader ------
    con8 = _fixture(ms)
    ms.build(con8, out=lambda *a: None)
    con8.execute("INSERT INTO setting VALUES('stock.margin_med','twenty percent')")
    con8.execute("INSERT INTO setting VALUES('stock.margin_ortho','30%')")
    con8.commit()
    crashed = False
    try:
        Deriver(con8, ms, out=lambda *a: None).run("selftest")
    except Exception:                                            # noqa: BLE001
        crashed = True
    ck("a settings row a person mistyped does NOT kill the whole pass", not crashed)
    ck("and '30%' is still read as thirty per cent",
       abs(Deriver(con8, ms, out=lambda *a: None).margin_ortho - 0.30) < 1e-9)
    ck("while unreadable text falls back to the default",
       abs(Deriver(con8, ms, out=lambda *a: None).margin_med - MARGIN_MED_DEFAULT) < 1e-9)

    # a below-zero ROW hiding behind a positive one for the same product
    con9 = _fixture(ms)
    ms.build(con9, out=lambda *a: None)
    con9.execute("INSERT INTO stock_snapshot VALUES('06-09-2026','ACILOC 300',-40,'1*20',20,'x')")
    con9.commit()
    Deriver(con9, ms, out=lambda *a: None).run("selftest")
    e9 = lambda f, c="value_p": con9.execute(
        "SELECT %s FROM marg_figure WHERE scope='estate' AND figure=?" % c, (f,)).fetchone()[0]
    ck("a below-zero row is a fault even when a positive row for the same "
       "product would have netted it away",
       e9("below_zero_items", "value_n") == 2)
    ck("its money is counted at the product's own price", e9("below_zero_value_p") == 125000 * 3 + 308 * 40)
    ck("and the shelf still holds the stock it really has, undiminished",
       e9("shelf_value_mrp_p") == 308 * 100 + 150000 * 4 + 100000 * 5 + 123456 * 2)
    ck("the second row for one product is reported as a collision",
       e9("shelf_name_collisions", "value_n") == 1)
    ck("and since that second row was NEGATIVE it moved no shelf money, so none "
       "is attributed to it -- its money is in the below-zero figures",
       e9("shelf_name_collisions", "uncovered_p") == 0)

    # the input figures must survive the shelf disappearing
    con10 = _fixture(ms)
    ms.build(con10, out=lambda *a: None)
    con10.execute("INSERT INTO stock_mrp_manual VALUES('NOPRICE ITEM',-5)")
    con10.execute("DELETE FROM stock_snapshot")
    con10.commit()
    Deriver(con10, ms, out=lambda *a: None).run("selftest")
    ck("with no snapshot at all, the refused typed price is STILL on the record",
       con10.execute("SELECT denom_n,covered_n,uncovered_n FROM marg_figure WHERE "
                     "figure='typed_prices'").fetchone() == (2, 1, 1))
    ck("and so is the merge check", con10.execute(
        "SELECT COUNT(*) FROM marg_figure WHERE figure='merge_faults'").fetchone()[0] == 1)

    # two tails into one cycle: both must be refused, and the answer must not
    # depend on which was walked first
    def _cyc(order):
        c = _fixture(ms)
        ms.build(c, out=lambda *a: None)
        ids = [c.execute("SELECT item_id FROM marg_item WHERE canonical=?", (nm,)).fetchone()[0]
               for nm in ("ACILOC 300", "ESTONLY ITEM", "MANUAL ITEM", "NOPRICE ITEM")]
        one, two, three, four = ids
        pairs = [(one, three), (two, three), (three, four), (four, three)]
        for a_, b_ in (pairs if order else list(reversed(pairs))):
            c.execute("UPDATE marg_item SET status='merged', merged_into=? WHERE item_id=?", (b_, a_))
        c.commit()
        d = Deriver(c, ms, out=lambda *a: None)
        d.run("selftest")
        return d._merged, d._merge_faults
    m1, f1 = _cyc(True)
    m2, f2 = _cyc(False)
    ck("no member of a merge cycle stays merged",
       not any(v in m1 for v in m1.values()) and not any(v in m2 for v in m2.values()))
    ck("and the answer does not depend on the order the rows are read in",
       m1 == m2 and f1 == f2)
    ck("the two tails leading into that cycle resolve to the SAME product, "
       "so two identically-placed products can never come out different",
       len(set(m1.values())) == 1)

    # the return lane discloses an unreadable pack the way the sale lane does
    con11 = _fixture(ms)
    ms.build(con11, out=lambda *a: None)
    con11.execute("INSERT INTO sale_line_item VALUES('2026-08-09','ACILOC 300','ACILOC 300',"
                  "'VAIL','1',100,1)")
    con11.commit()
    Deriver(con11, ms, out=lambda *a: None).run("selftest")
    ck("an unreadable pack on a return line is disclosed on the return lane",
       con11.execute("SELECT uncovered_n FROM marg_figure WHERE scope='month' AND "
                     "scope_key='2026-08' AND figure='sale_return_lines'").fetchone()[0] == 1)

    # nothing typed is not the same as nothing to cover
    con12 = _fixture(ms)
    con12.execute("DELETE FROM stock_mrp_manual")
    con12.commit()
    ms.build(con12, out=lambda *a: None)
    Deriver(con12, ms, out=lambda *a: None).run("selftest")
    ck("with no typed prices at all, no denominator is invented to divide by",
       con12.execute("SELECT denom_n FROM marg_figure WHERE figure='typed_prices'"
                     ).fetchone()[0] is None)

    # ---- v4's own faults ---------------------------------------------------
    con13 = _fixture(ms)
    ms.build(con13, out=lambda *a: None)
    # NOPRICE ITEM is unpriced AND now below zero: it is ONE gap, not two
    con13.execute("INSERT INTO stock_snapshot VALUES('06-09-2026','NOPRICE ITEM',-2,'1*1',1,'x')")
    con13.commit()
    Deriver(con13, ms, out=lambda *a: None).run("selftest")
    e13 = lambda f, c: con13.execute("SELECT %s FROM marg_figure WHERE scope='estate' AND "
                                     "figure=?" % c, (f,)).fetchone()[0]
    ck("a product that is BOTH unpriced and below zero is one coverage gap, not two",
       e13("shelf_value_mrp_p", "denom_n") - e13("shelf_value_mrp_p", "covered_n") == 1)
    ck("and the shelf's covered count equals the number of products with a price",
       e13("shelf_value_mrp_p", "covered_n") == e13("items_priced", "value_n"))
    ck("it is still counted as a below-zero fault",
       e13("below_zero_items", "value_n") == 2)
    ck("with no money attached, because no price can reach it",
       e13("below_zero_value_p", "uncovered_n") == 1)

    con14 = _fixture(ms)
    ms.build(con14, out=lambda *a: None)
    # a colliding row that is NEGATIVE moves no shelf money
    con14.execute("INSERT INTO stock_snapshot VALUES('06-09-2026','ACILOC 300',-40,'1*20',20,'x')")
    con14.commit()
    Deriver(con14, ms, out=lambda *a: None).run("selftest")
    ck("a NEGATIVE colliding row is not reported as shelf money it never moved",
       con14.execute("SELECT uncovered_p FROM marg_figure WHERE figure="
                     "'shelf_name_collisions'").fetchone()[0] == 0)
    con15 = _fixture(ms)
    ms.build(con15, out=lambda *a: None)
    con15.execute("INSERT INTO stock_snapshot VALUES('06-09-2026','ACILOC 300',40,'1*20',20,'x')")
    con15.commit()
    Deriver(con15, ms, out=lambda *a: None).run("selftest")
    ck("a POSITIVE one is, to the paise",
       con15.execute("SELECT uncovered_p FROM marg_figure WHERE figure="
                     "'shelf_name_collisions'").fetchone()[0] == 308 * 40)

    # ---- a judgement must never be storable here -------------------------
    ccols = {r[1] for r in con4.execute("pragma table_info(marg_figure)")}
    ck("marg_figure has no column a person's decision could land in",
       not (ccols & {"decided_by", "decision", "verdict", "approved_by", "status"}))

    out("")
    out("%d checks, %d failures" % (n[0], len(fails)))
    for f in fails:
        out("  FAILED: %s" % f)
    return len(fails)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def open_db(path, readonly=False):
    if not os.path.exists(path):
        raise SystemExit("REFUSING: no such database: %s\nNothing was touched." % path)
    if readonly:
        return sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    return sqlite3.connect(path)


def safe_copy(src, dst):
    """A consistent copy even while the server is writing.

    shutil.copyfile can take a torn image of a live sqlite file; the backup
    API takes a consistent one, and that is the whole point of a backup."""
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    with d:
        s.backup(d)
    d.close()
    s.close()


def dry_run(path, out=print):
    """Rehearse the whole pass on a COPY.  The real database is opened
    read-only, and only to copy it."""
    tmp = tempfile.mkdtemp(prefix="marg_derive_dry_")
    dst = os.path.join(tmp, "copy.db")
    try:
        safe_copy(path, dst)
        con = sqlite3.connect(dst)
        out("DRY RUN on a copy -- the real database is not opened for writing.")
        Deriver(con, load_spine(), out=out).run("dry-run")
        out("")
        report(con, out=out)
        con.close()
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def install(path, out=print):
    out("1/4  self-tests")
    if selftest(out=out):
        raise SystemExit("REFUSING: self-tests failed. Nothing was touched.")
    out("2/4  rehearsal on a copy")
    dry_run(path, out=lambda *a: None)
    out("     rehearsal clean")
    out("3/4  backup")
    # dated, so a second install can never overwrite the pre-install backup
    # and quietly turn the undo line into a lie
    bak = "%s.bak_S235_derive_%s" % (path, datetime.now(IST).strftime("%Y%m%d_%H%M%S"))
    safe_copy(path, bak)
    out("     %s" % bak)
    out("4/4  build")
    con = open_db(path)
    Deriver(con, load_spine(), out=out).run("build")
    con.close()
    out("")
    out("DONE.  Nothing reads these tables yet; no screen has changed.")
    out("To undo entirely:")
    out("  \\cp %s %s" % (bak, path))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="The derivation pass -- S235.")
    ap.add_argument("--db")
    ap.add_argument("--spine", help="path to marg_spine.py, if not beside this kit")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry-run", dest="dry", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--install", action="store_true")
    a = ap.parse_args(argv)
    global SPINE_PATH
    if a.spine:
        SPINE_PATH = a.spine
    if a.selftest:
        return 1 if selftest() else 0
    if not a.db:
        ap.error("--db is required for anything but --selftest")
    if a.dry:
        return dry_run(a.db)
    if a.report:
        con = open_db(a.db, readonly=True)
        report(con)
        con.close()
        return 0
    if a.install:
        return install(a.db)
    if a.build:
        con = open_db(a.db)
        Deriver(con, load_spine()).run("build")
        con.close()
        return 0
    ap.error("say what to do: --selftest, --dry-run, --build, --report or --install")


if __name__ == "__main__":
    sys.exit(main() or 0)
