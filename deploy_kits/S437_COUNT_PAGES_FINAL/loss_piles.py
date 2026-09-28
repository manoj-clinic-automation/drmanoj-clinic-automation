#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  loss_piles.py  ·  v2.0  ·  kit S427_LOSS_DESK_RULINGS  ·  Session 283 (Sanjeevni)  ·  D632 / F-642
#  (v1.0 was kit S418_LOSS_DESK_PILES, D631 / F-641 -- its tables, its taps and its routes stay)
#
#  THE OWNER'S LOSS DESK UNDER HIS RULINGS OF 27-Sep-2026, on the live S418 desk:
#    "The recount pile says 50 or more units -- we agreed ONE nomenclature, strips and tablets, everywhere."
#    "Recount should be Darpan's option, not pushed on him."  "The Rs 1,000 rule puts slow items like VFER and
#    G Dress in write-off; big fast sellers land in Recount instead of the loss pile."  "Leukocrepe, Leukoband,
#    G Dress are sold on bills -- they are not clinic consumption."  "It is a loss -- carelessness or theft. Boldly:
#    these are the major losses in this count, this much has been written off. That keeps the staff alert."
#
#  FOUR PILES, every open shortage line in exactly one, the sales-after-count test first:
#     with_me   With me / back in store   ONE tap Accept back -> EXPLAINED, cause FOUND, shelf corrected to Marg's
#     writeoff  Write off                 (a) within the allowance = stock.allowance_pct % of the item's OWN sales
#                                         since the previous closed count (first count: since its first sale, at most
#                                         180 days), floor stock.allowance_min_strips; (b) small real gap -- beyond
#                                         the allowance, under stock.small_gap_ceiling_p at MRP and not a slow item
#     bigloss   Big losses                beyond the allowance AND (value >= stock.big_loss_floor_p, or a gap of
#                                         stock.slow_months months of the item's own sales worth >= stock.slow_floor_p,
#                                         or never sold in 180 days with stock on record and worth >= slow_floor).
#                                         Nothing here is "pursued": it is a loss, recorded by name.
#     consume   Consumption               the owner's list only (stock.consume_items -- BLADE, ZIG ZAG cotton, GLOVES),
#                                         never name-words; written off AS clinic consumption by the same close
#  Surpluses are never a loss (the "Over on shelf" note; the close corrects the shelf figure).  THERE IS NO RECOUNT
#  PILE: Darpan keeps his own "Dobara ginna hai" on Stock milaan for any item of the round; his figure, stamped,
#  replaces the shelf figure (the S418 layer) and the line re-piles itself.
#
#  THE SALES-AFTER-COUNT TEST (automatic, before piling): a line whose sales since the count day exceed counted +
#  bought since (the spine's sp_sale_line / sp_purchase_line after as_on) is closed by the system -- EXPLAINED, cause
#  FOUND, shelf = Marg, audited "system: sold after count" -- and listed in the record under its own heading.
#
#  ONE TAP CLOSES THE COUNT (armed, 10-s confirm): every line in piles 2, 3 and 4 -> WRITE_OFF + closed, Amir's
#  vouchers in rounds of <= stock.voucher_batch in the same call, ONE frozen stock_writeoff_run with the four groups
#  (allowance / small / consume / big) item by item, and THE STAFF BLOCK frozen from it -- Hindi, pinned on Darpan's
#  Stock milaan until the next count closes: total loss, the small part written off, the big part BY NAME.  No
#  reasons, no percentages, no questions; one optional line "Kuchh batana hai?" under it.  With-me lines stay open.
#
#  QUANTITIES: every quantity a person reads goes through qty_words.words() -- strips + tabs, pcs / bottles / tubes /
#  vials, Hindi patte / goli / nag.  The word "unit(s)" reaches no screen, hint, notice, PDF or message.
#
#  EVERY THRESHOLD IS A SETTING (the `setting` table, audited, printed in the record).  The piles re-compute from the
#  settings on every read; changing a setting never decides a line by itself.
#
#  No stock_app import at module level: stock_app imports this file while it is itself being imported.
# =============================================================================
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3

VERSION = "2.4"
KIT = "S437_COUNT_PAGES_FINAL"                                 # v2.3 was S436_STAFF_PAGES_CLEAN, v2.2 S432_DESK_GROUP_FLOW
# v2.4 (S437, F-659, 28-Sep-2026) -- THE COUNT PAGES FINISHED:
#   * THE STOCK RECEIVE ROUND BY RULE (receive_close): every line where the shelf holds MORE than Marg after the swaps -- the
#     over-on-shelf lines and the Marg-negative book corrections -- gets its STOCK RECEIVE voucher line (Marg brought UP to the
#     shelf) as part of every close, in ONE run of kind 'receive_close' (group 'receive'; never a loss, never leakage, never in a
#     block). At install the rule ran once for count #1 and, in the same round, carried the 15 short lines the owner wrote off on
#     06-Sep that were on no voucher (group 'issue_earlier', STOCK ISSUE) -- the hub's "not yet on a voucher" reads 0.
#   * THE STAFF BLOCK AS TABLES (block_tables): kul; Badi kami rows (item · Marg on the count day · counted · short · Rs at MRP,
#     a total row); Chhoti kami rows the same (collapsed on the pages); the orthotic loss rows apart -- frozen at the close as
#     before (the rows are read from the frozen runs behind the block), rendered by Darpan's page, the owner's desk and the record
#     PDF. The three text lines (+ the orthotic foot line) stay for the pages that still print them.
#   * WHOLE-UNIT ITEMS (stock.whole_unit_items, an owner list "ITEM = word"; seeded "CCM = bottle"): qty_words v1.2 reads such an
#     item in whole units of its word, never strips / tabs; settings() loads the map into qty_words on every read;
#     whole_unit_candidates() lists the items the owner may add with one tap (1*N packing sold only in whole multiples, or ML / GM /
#     POW / SYP / SACH in the packing or the name).
# v2.3 (S436, D638, 28-Sep-2026): the ORTHOTIC LOSS (stockmatch.close_by_rule writes a run of kind 'ortho_close', groups ortho_loss /
# ortho_fix) is shown, never merged: the staff block gains ONE line at its foot -- "Orthotics -- Rs X (N lines, bina bill)" -- while
# its first three lines (total / small / big) keep reading allowance + small + big only; the record names the run's kind; the union
# of runs behind a medicine block never takes the orthotic run in. Nothing else of the desk changes.
# v2.1 (S430, D637 / F-650, 27-Sep-2026): a fifth destination 'Owner's use' (group owner_use inside the Consumption pile, moved
# line by line, vouchered in its own round, never leakage); the group 'Old stock' (no sale, no purchase since the opening, no
# price -- written off, not a loss, never a Big loss); a consumption-list item keeps its tag even when the owner moved it.
# v2.2 (S432, F-651, 28-Sep-2026) -- THE DESK MADE FAST, AND CLOSED GROUP BY GROUP THE OWNER'S WAY:
#   * measured on the box (28-Sep): a desk read took 6.5 s -- the S227 report composer (_pad_report_data, ~2.8 s: one item-life
#     walk per line) ran TWICE per read (once inside the sales-after-count test, once for the desk) and the watch scoring took
#     0.9 s more; classify() itself takes 10 ms. Every tap paid the same again and then the page re-fetched everything.
#   * stock_pile_cache: the classified lines of a count, computed ONCE and stored (count_id, item, diff_id) with a STAMP of their
#     inputs (the settings, the spine build, the count's rows, the prices, the moves, the shelf fixes, the words, the sales tests,
#     the runs). A read serves the cache. A stale stamp recomputes ONLY the lines whose inputs changed (a move, an accept-back,
#     a recount, a word, a sales-test hit) from their stored count-day inputs; a changed setting, spine build, price or count row
#     rebuilds everything, once, in one transaction (the spine's sales fetched in ONE query for all items). The sales-after-count
#     test runs when the spine was rebuilt, not on every read.
#   * the traces and the watch scoring leave the read path (stock_watch v1.2 keeps the stored view; the 06:30 job and 'Refresh
#     watch' refresh it); a Big-loss trace is opened by the close / the clear, once.
#   * THE GROUP FLOW: 'Clear this group (N ticked)' -- arm_clear / clear: the ticked lines written off NOW as that group, one
#     stock_writeoff_run per clear (kind 'clear:<group>'), Amir's vouchers in rounds, audited; the unticked stay open. The LAST
#     clear closes the count by itself: when no open line remains outside With me, ONE staff block is frozen from the union of
#     the clears (how 'auto'), the S428 full-count points are written once (stock_app), the leakage period line follows.
#     'Close the count' stays: the same code path, all groups at once (its block too unions the clears before it).
#   * move / accept return a PATCH (the changed line + the totals) so the page updates in place.
HERE = os.path.dirname(os.path.abspath(__file__))
SPINE_DB = os.environ.get("SPINE_DB") or os.path.join(HERE, "spine", "spine.db")
FIRST_COUNT_DAYS = 180

PILES = (("with_me", "With me / back in store"),
         ("writeoff", "Write off"),
         ("bigloss", "Big losses"),
         ("consume", "Consumption & owner's use"))
PILE_TITLE = dict(PILES)
PILE_HI = {"with_me": "Mere paas", "writeoff": "Chhoti kami", "bigloss": "Badi kami", "consume": "Clinic mein laga"}
# S430: the -> pile menu's fifth destination -- 'Owner's use' lands in the Consumption pile as its own group, moved line by line
MOVE_TARGETS = (("with_me", "With me / back in store"), ("writeoff", "Write off"), ("bigloss", "Big losses"),
                ("consume", "Consumption (clinic)"), ("owner_use", "Owner's use -- taken for home, unbilled"))
MOVE_PILE = {"with_me": "with_me", "writeoff": "writeoff", "bigloss": "bigloss", "consume": "consume", "owner_use": "consume"}
GROUPS = (("allowance", "Within the allowance",
           "short by no more than the allowance -- a share of what the item itself sold since the previous count"),
          ("small", "Small real gap",
           "beyond the allowance, under the small-gap ceiling at MRP and not a slow item -- a real loss, written off and recorded"),
          ("old", "Old stock",
           "no sale and no purchase since the opening, no price on record -- written off, not a loss (never a Big loss)"),
          ("consume", "Clinic consumption",
           "the items on your consumption list (blades, cotton, gloves) -- used in the clinic, never billed"),
          ("owner_use", "Owner's use",
           "taken for home, unbilled -- moved here by you, line by line; a recorded non-loss, never leakage"),
          ("big", "Big loss",
           "beyond the allowance and large -- by value, or a slow item short by months of its own sales -- recorded by name"),
          ("earlier", "Written off before the piles",
           "decided line by line on the earlier desk"))
GROUP_TITLE = {k: t for k, t, _b in GROUPS}
GROUP_BLURB = {k: b for k, _t, b in GROUPS}
# S436: the orthotic section's own groups (stockmatch.close_by_rule) -- named here for the record, never piles of this desk
ORTHO_GROUP_TITLE = {"ortho_loss": "Orthotic loss -- sold without bill", "ortho_fix": "Orthotic book correction -- billed, not handed over"}
ORTHO_RUN_KIND = "ortho_close"
# S437 (F-659): the STOCK RECEIVE round by rule -- Marg brought up to the shelf; a book correction, never a loss, never in a block
RECEIVE_RUN_KIND = "receive_close"
RECEIVE_GROUP_TITLE = {"receive": "Marg corrected -- the shelf held more than Marg (STOCK RECEIVE)",
                       "issue_earlier": "Written off before the piles, on no voucher until now (STOCK ISSUE)"}
NON_BLOCK_KINDS = (ORTHO_RUN_KIND, RECEIVE_RUN_KIND)         # runs that never enter a medicine block, the leakage or the union of clears
GROUP_OF_PILE = {"writeoff": None, "bigloss": "big", "consume": "consume", "owner_use": "owner_use"}
LOSS_GROUPS = ("allowance", "small", "big")                   # what counts as a loss (the staff block, leakage); old / consume / owner_use never
OPENING_DAY = "2026-04-01"                                     # the spine's opening (sp_move OPENING at 31-03-2026)

# ---- the settings (3.6). kind: choice | rupees | pct | num | int | list. `seed` is what the kit writes when the key is absent.
CONSUME_SEED = ["BLADE", "ZIG ZAG COTTON 500GM", "ZIG ZAG COTTON 500 GM", "GLOVES SURGICAL 7", "DISPO GLOVES NO 7",
                "EXAMINATION GLOVES", "LATEX EXAM GLOVES", "LATEX GLOVES"]
SETTINGS = (
    dict(key="stock.allowance_pct", label="Allowance (% of the item's own sales)", kind="pct", default="1.0", seed="1.0", lo=0.0, hi=100.0,
         hint="A shortage within this share of what the item itself sold since the previous closed count is normal shop loss, "
              "written off with the pile. First count: its sales since its first sale, at most 180 days."),
    dict(key="stock.allowance_min_strips", label="Allowance floor (strips, or pcs)", kind="int", default="1", seed="1", lo=0, hi=50,
         hint="Whatever it sells, at least this many strips (pcs for a bottle, a tube, a belt) are within the allowance."),
    dict(key="stock.small_gap_ceiling_p", label="Small gap ceiling (at MRP)", kind="rupees", default="100000", seed="100000",
         hint="A real gap under this, on an item that is not slow, is a small loss -- written off with the pile and recorded."),
    dict(key="stock.big_loss_floor_p", label="Big loss floor (at MRP)", kind="rupees", default="100000", seed="100000",
         hint="A real gap of this value or more is a big loss -- recorded by name, shown to the staff by name."),
    dict(key="stock.slow_months", label="Slow item: months of its own sales", kind="num", default="1", seed="1", lo=0.1, hi=24,
         hint="An item short by this many months of what it sells is a big loss even when the value is small (VFER, G Dress)."),
    dict(key="stock.slow_floor_p", label="Slow item floor (at MRP)", kind="rupees", default="20000", seed="20000",
         hint="A slow item's gap, or an item never sold in 180 days with stock on record, counts as a big loss from this value."),
    dict(key="stock.old_stock_days", label="Old stock: days without a sale or a purchase", kind="int", default="180", seed="180", lo=30, hi=730,
         hint="A shortage on an item with no sale and no purchase since the opening is old stock -- written off, not a loss -- when it has no "
              "price on record, or when this many days have passed without either. Never a Big loss."),
    dict(key="stock.consume_items", label="Consumption list", kind="list", default="[]", seed=json.dumps(CONSUME_SEED),
         hint="Only these items are clinic consumption -- matched by name, never by a word in the name. Bandages and "
              "dressings sold on bills are stock, not consumption. Search an item to add it; tap a name to take it off."),
    dict(key="stock.voucher_batch", label="Lines per Marg voucher", kind="int", default="6", seed="6", lo=1, hi=8,
         hint="How many lines Amir enters on one Marg voucher (Marg prints six to eight)."),
    dict(key="stock.accept_back_by", label="Who may tap Accept back", kind="choice", default="owner", seed="owner",
         choices=(("owner", "only you"), ("owner,darpan", "you and Darpan")),
         hint="Accept back closes a line as 'it is here, not lost'."),
    dict(key="stock.staff_block_items", label="Staff block: big losses named", kind="int", default="20", seed="20", lo=1, hi=100,
         hint="How many of the big losses the staff block names, largest first; the rest are 'aur N'."),
    dict(key="stock.whole_unit_items", label="Whole-piece items (bottle / jar / pc / tube / vial / sachet)", kind="list", default="[]",
         seed=json.dumps(["CCM = bottle"]),                   # S437 (F-659): the CCM bug -- Marg's packing 1*40 is the tablets in the bottle; the shop counts bottles
         hint="Items Marg counts by the whole piece although the packing reads 1*N -- a bottle of 40 tablets, a jar. Every quantity of such an "
              "item reads in that word (8 bottles), never strips and tabs. Pick the word when you add one; tap a name to take it off."),
)
SETTING_BY_KEY = {s["key"]: s for s in SETTINGS}
# S418 keys that left the card (their rows may stay in the table; S428 defines the counts):
RETIRED_KEYS = ("stock.allowance_scale", "stock.recount_trigger", "stock.consume_auto", "stock.rolling_section_items",
                "stock.rolling_day", "stock.pursue_floor_p")

SCHEMA = """
CREATE TABLE IF NOT EXISTS stock_pile_move (
  id        INTEGER PRIMARY KEY,          -- S418: the owner moved a line to a pile; append-only, the newest wins
  count_id  INTEGER NOT NULL,             -- the ROOT count
  item      TEXT NOT NULL,
  pile      TEXT NOT NULL,                -- with_me | writeoff | bigloss | consume | auto (S418 also wrote pursue | recount)
  by_user   TEXT, at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pile_move ON stock_pile_move(count_id, item);
CREATE TABLE IF NOT EXISTS stock_shelf_fix (
  id        INTEGER PRIMARY KEY,          -- S418: a corrected shelf figure for one item of a count; append-only, the newest wins
  count_id  INTEGER NOT NULL,
  item      TEXT NOT NULL,
  qty       INTEGER NOT NULL,             -- what is on the shelf now (tablets, or pieces)
  source    TEXT NOT NULL,                -- accept_back (= Marg's figure) | recount (Darpan's figure) | sales_test (S427: = Marg's figure)
  note      TEXT, by_user TEXT, at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_shelf_fix ON stock_shelf_fix(count_id, item);
CREATE TABLE IF NOT EXISTS stock_recount_ask (
  id        INTEGER PRIMARY KEY,          -- S418: the owner asked Darpan to count one item again (no new rows since S427)
  count_id  INTEGER NOT NULL,
  item      TEXT NOT NULL,
  asked_by  TEXT, asked_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_recount_ask ON stock_recount_ask(count_id, item);
CREATE TABLE IF NOT EXISTS stock_pile_arm (
  id        INTEGER PRIMARY KEY,          -- S418: a write-off pressed once -- the 10-second confirm (S427: 'Close the count' too)
  count_id  INTEGER NOT NULL,
  token     TEXT NOT NULL,
  items     TEXT NOT NULL,                -- JSON: the lines as they stood when armed
  by_user   TEXT, at TEXT NOT NULL, used_at TEXT
);
CREATE TABLE IF NOT EXISTS stock_writeoff_run (
  id        INTEGER PRIMARY KEY,          -- S418: one write-off tap -- FROZEN, the documented groups (S427: one close = one run)
  count_id  INTEGER NOT NULL,
  at        TEXT NOT NULL, by_user TEXT,
  lines_n   INTEGER NOT NULL, mrp_p INTEGER NOT NULL, cost_p INTEGER NOT NULL, unpriced INTEGER NOT NULL,
  groups    TEXT NOT NULL,                -- JSON {group: [ {item, short_units, short_text, mrp_p, cost_p, why}, ... ]}
  settings  TEXT NOT NULL,                -- JSON: the rules in force when it was written off
  round_no  INTEGER,                      -- the Marg voucher round made in the same call
  md5       TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stock_sales_test (
  id        INTEGER PRIMARY KEY,          -- S427: the system closed a line -- sold after the count more than counted + bought
  count_id  INTEGER NOT NULL,
  item      TEXT NOT NULL,
  at        TEXT NOT NULL,
  counted   INTEGER, marg INTEGER, sold_after REAL, bought_after REAL, as_on TEXT, upto TEXT, diff_id INTEGER
);
CREATE INDEX IF NOT EXISTS idx_sales_test ON stock_sales_test(count_id, item);
CREATE TABLE IF NOT EXISTS stock_staff_block (
  id        INTEGER PRIMARY KEY,          -- S427: THE STAFF BLOCK, frozen at the close (one per close)
  count_id  INTEGER NOT NULL,
  run_id    INTEGER,
  at        TEXT NOT NULL, day TEXT,
  total_p   INTEGER NOT NULL,             -- allowance + small + big at MRP (consumption is clinic use, not a loss)
  small_p   INTEGER NOT NULL,             -- allowance + small
  big_p     INTEGER NOT NULL,             -- the big losses
  consume_p INTEGER NOT NULL,
  big_lines TEXT NOT NULL,                -- JSON [ {item, short_units, pack, packing, mrp_p}, ... ] by value
  top_n     INTEGER NOT NULL,
  by_user   TEXT
);
CREATE TABLE IF NOT EXISTS stock_staff_note (
  id        INTEGER PRIMARY KEY,          -- S427: 'Kuchh batana hai?' -- the staff's free text under the block
  block_id  INTEGER NOT NULL,
  count_id  INTEGER NOT NULL,
  text      TEXT NOT NULL,
  by_user   TEXT, at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stock_pile_cache (
  count_id  INTEGER NOT NULL,             -- S432 (F-651): the classified lines of a count, computed once and stored
  item      TEXT NOT NULL,
  diff_id   INTEGER,                      -- the newest stock_diff row of the item in the family (the brief's key)
  bucket    TEXT NOT NULL,                -- with_me | writeoff | bigloss | consume | back | written_off | over
  pile      TEXT, grp TEXT,
  allow_units INTEGER, mrp_p INTEGER,
  why       TEXT,
  x_json    TEXT NOT NULL,                -- the report's line as built (count-day inputs), for a one-line recompute
  line_json TEXT NOT NULL,                -- the classified line as the desk shows it
  built_at  TEXT NOT NULL,
  PRIMARY KEY (count_id, item)
);
CREATE INDEX IF NOT EXISTS idx_pile_cache_diff ON stock_pile_cache(count_id, diff_id);
CREATE TABLE IF NOT EXISTS stock_pile_cache_meta (
  count_id  INTEGER PRIMARY KEY,          -- S432: the stamp the cached lines were built from
  stamp     TEXT NOT NULL,                -- JSON: every input's version
  built_at  TEXT NOT NULL, full_ms INTEGER, lines_n INTEGER, over_n INTEGER, skipped INTEGER,
  last_partial_at TEXT, last_partial_n INTEGER, last_partial_ms INTEGER
);
"""
ARM_SECONDS = 10
AUDIT_TABLE = "stock_pile"
_TABLES = ("stock_pile_move", "stock_shelf_fix", "stock_recount_ask", "stock_pile_arm", "stock_writeoff_run",
           "stock_sales_test", "stock_staff_block", "stock_staff_note", "stock_pile_cache", "stock_pile_cache_meta")
# S432: two columns on the frozen tables, added once where missing -- a run's KIND (close | clear:<group> | pile) and a block's HOW (tap | auto)
_COLUMNS = (("stock_writeoff_run", "kind", "TEXT"), ("stock_staff_block", "how", "TEXT"))


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _sa():
    import stock_app                                          # noqa: PLC0415 -- beside this file, already loaded
    return stock_app


def _qwm():
    import qty_words                                          # noqa: PLC0415 -- beside this file
    return qty_words


def qw(units, pack=1, packing="", name="", lang="en"):
    """Every quantity a person reads -- through the one function (S427)."""
    return _qwm().words(units, packing=packing, pack=pack, name=name, lang=lang)


def norm_name(s):
    """The name key of the consumption list: case, punctuation and spacing folded (item_alias.sale_key, verbatim)."""
    t = re.sub(r"[^A-Z0-9 ]+", " ", str(s or "").upper())
    return re.sub(r"\s+", " ", t).strip()


def ensure(con):
    """Create the desk's tables -- only when one is missing. executescript COMMITs whatever the caller has open, and
    this is reached from the report's read path (apply_fixes), so it must be a no-op once the tables exist."""
    have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN (%s)"
                                      % ",".join("?" * len(_TABLES)), _TABLES)}
    if len(have) < len(_TABLES):
        con.executescript(SCHEMA)
    for table, col, typ in _COLUMNS:                           # S432: guarded ALTERs (a no-op once the column is there)
        try:
            cols = {r[1] for r in con.execute("PRAGMA table_info(%s)" % table)}
            if col not in cols:
                con.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, col, typ))
                con.commit()
        except sqlite3.Error:
            pass


def _audit(con, root, action, after, who, before=None):
    try:
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                    (AUDIT_TABLE, int(root), action, json.dumps(before) if before is not None else None,
                     json.dumps(after, sort_keys=True), who or "", now_iso()))
    except Exception:                                         # noqa: BLE001 -- the row it describes is the record that counts
        pass


# ------------------------------------------------------------------ settings
def setting_raw(con, key):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        if r is not None and str(r[0]).strip() != "":
            return str(r[0]).strip()
    except Exception:                                         # noqa: BLE001
        pass
    return None


def _list_of(raw):
    try:
        v = json.loads(raw) if raw else []
        return [str(x) for x in v if str(x).strip()] if isinstance(v, list) else []
    except ValueError:
        return [x.strip() for x in str(raw or "").split(",") if x.strip()]


def settings(con):
    """The rules in force, typed."""
    out = {}
    for s in SETTINGS:
        raw = setting_raw(con, s["key"])
        out[s["key"]] = raw if raw is not None else s["default"]

    def num(k, dflt, f=int):
        try:
            return f(float(out[k]))
        except (TypeError, ValueError):
            return dflt
    who = [w.strip() for w in str(out["stock.accept_back_by"] or "owner").split(",") if w.strip()]
    items = _list_of(out["stock.consume_items"])
    whole = _list_of(out.get("stock.whole_unit_items") or "[]")   # S437: the whole-unit items, handed to qty_words on every read
    try:
        whole_map = _qwm().set_whole_units(whole)
    except Exception:                                         # noqa: BLE001 -- an older qty_words: the words read as before
        whole_map = {}
    return dict(raw=out, whole_unit_items=whole, whole_units=whole_map, allowance_pct=max(0.0, num("stock.allowance_pct", 1.0, float)),
                allowance_min_strips=max(0, num("stock.allowance_min_strips", 1)),
                small_gap_ceiling_p=max(0, num("stock.small_gap_ceiling_p", 100000)),
                big_loss_floor_p=max(0, num("stock.big_loss_floor_p", 100000)),
                slow_months=max(0.1, num("stock.slow_months", 1.0, float)), slow_floor_p=max(0, num("stock.slow_floor_p", 20000)),
                consume_items=items, consume_keys={norm_name(i) for i in items}, old_stock_days=max(30, num("stock.old_stock_days", 180)),
                voucher_batch=max(1, min(8, num("stock.voucher_batch", 6))), accept_back_by=who,
                staff_block_items=max(1, num("stock.staff_block_items", 20)))


def _rs(p_):
    return _sa()._loss_rs(p_) if p_ is not None else "-"


def _shown(s, v):
    if v is None:
        return "not set"
    if s["kind"] == "rupees":
        try:
            return _rs(int(float(v)))
        except (TypeError, ValueError):
            return str(v)
    if s["kind"] == "choice":
        return dict(s["choices"]).get(str(v), str(v))
    if s["kind"] == "pct":
        try:
            return ("%g" % float(v)) + "%"
        except (TypeError, ValueError):
            return str(v)
    if s["kind"] == "list":
        ls = _list_of(v)
        return ("%d item%s: " % (len(ls), "" if len(ls) == 1 else "s")) + ", ".join(ls) if ls else "empty"
    return str(v)


def settings_view(con):
    rows = []
    for s in SETTINGS:
        raw = setting_raw(con, s["key"])
        v = raw if raw is not None else s["default"]
        row = dict(key=s["key"], label=s["label"], kind=s["kind"], value=v, shown=_shown(s, v), hint=s["hint"],
                   choices=[dict(v=a, t=b) for a, b in s.get("choices", ())], set=(raw is not None),
                   rupees=(None if s["kind"] != "rupees" else int(float(v)) // 100))
        if s["kind"] == "list":
            row["items"] = _list_of(v)
        if s["key"] == "stock.whole_unit_items":              # S437: the words to choose from, and the candidates the owner may add with one tap
            row["words"] = list(WHOLE_WORDS)
            try:
                row["candidates"] = whole_unit_candidates(con)
            except Exception:                                 # noqa: BLE001
                row["candidates"] = []
        rows.append(row)
    return rows


WHOLE_WORDS = ("bottle", "jar", "pc", "tube", "vial", "sachet")


def whole_unit_candidates(con, since="2026-04-01", limit=60):
    """S437: the items that look like whole-unit items and are not on the list yet -- a 1*N packing (N > 1) whose every sale in the
    spine since `since` is a whole multiple of N (no loose part), or a packing / name that says ML / GM / POW / SYP / SACH.
    [{item, packing, n, sales, why, word}] with a guessed word; the owner adds each with one tap."""
    sa = _sa()
    on = set()
    try:
        on = set(_qwm().parse_whole_units(_list_of(setting_raw(con, "stock.whole_unit_items") or "[]")).keys())
    except Exception:                                         # noqa: BLE001
        pass
    root = con.execute("SELECT MAX(id) FROM stock_count WHERE id NOT IN (SELECT count_id FROM stock_count_part)").fetchone()[0]
    if not root:
        return []
    fam = [int(root)] + [r[0] for r in con.execute("SELECT count_id FROM stock_count_part WHERE part_of=?", (int(root),))]
    out = []
    for it, packing, ps in con.execute("SELECT DISTINCT item, packing, pack_size FROM stock_count_item WHERE count_id IN (%s) ORDER BY item" % ",".join("?" * len(fam)), tuple(fam)):
        ps = int(ps or 1)
        packing = packing or ""
        if norm_name(it) in on or ps <= 1:
            continue
        up = (" " + packing + " " + it + " ").upper().replace("ML", " ML ")
        wordy = bool(re.search(r"\b(ML|GM|POW|POWDER|SYP|SYRUP|SACH|SACHET)\b", up))
        sales = [r[0] for r in con.execute("SELECT qty_raw FROM sale_line_item WHERE unit='medical' AND item_key=? AND business_date>=?", (sa._sale_key(it), since))]
        def whole(q):
            q = str(q or "").strip()
            if ":" in q:
                return q.split(":", 1)[1].strip() in ("", "0")
            return q not in ("", "0")
        all_whole = bool(sales) and all(whole(q) for q in sales)
        if not (all_whole or wordy):
            continue
        word = "bottle"
        if re.search(r"\bGM\b", up) or " OINT" in up or " GEL " in up:
            word = "tube"
        elif re.search(r"\b(SACH|SACHET)\b", up):
            word = "sachet"
        elif re.search(r"\b(POW|POWDER)\b", up):
            word = "jar"
        out.append(dict(item=it, packing=packing, n=ps, sales=len(sales), word=word,
                        why=("every sale since %s a whole multiple of %d (%d sale%s)" % (since[8:10] + "-" + since[5:7], ps, len(sales), "" if len(sales) == 1 else "s")) if all_whole
                        else "the packing or the name says ML / GM / POW / SYP / SACH"))
        if len(out) >= limit:
            break
    return out


def set_setting(con, key, value, who, root=0):
    """Validate, store, audit. Returns (ok, message)."""
    s = SETTING_BY_KEY.get(key)
    if not s:
        return False, "Not a setting of this desk."
    v = "" if value is None else (json.dumps(value) if isinstance(value, list) else str(value).strip())
    if s["kind"] == "choice":
        if v not in [a for a, _b in s["choices"]]:
            return False, "Choose one of: %s." % ", ".join(b for _a, b in s["choices"])
    elif s["kind"] == "rupees":
        try:
            r = float(v.replace(",", "").replace("Rs", "").strip())
        except ValueError:
            return False, "Type an amount in rupees."
        if r < 0 or r > 1000000:
            return False, "Type an amount in rupees."
        v = str(int(round(r * 100)))
    elif s["kind"] in ("pct", "num"):
        try:
            f = float(v.replace("%", "").strip())
        except ValueError:
            return False, "Type a number."
        if f < s.get("lo", 0) or f > s.get("hi", 100):
            return False, "Between %g and %g." % (s.get("lo", 0), s.get("hi", 100))
        v = ("%g" % f)
    elif s["kind"] == "int":
        try:
            n = int(float(v))
        except ValueError:
            return False, "Type a whole number."
        lo, hi = s.get("lo", 1), s.get("hi", 100000)
        if n < lo or n > hi:
            return False, "Between %d and %d." % (lo, hi)
        v = str(n)
    elif s["kind"] == "list":
        ls = _list_of(v)
        seen, clean = set(), []
        for x in ls:
            x = re.sub(r"\s+", " ", str(x)).strip()
            if x and norm_name(x) not in seen:
                seen.add(norm_name(x)); clean.append(x)
        v = json.dumps(clean)
    old = setting_raw(con, key)
    if (old or "") == v:
        return True, "No change."
    con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, note=excluded.note",
                (key, v, "S427 loss desk setting: %s" % s["label"]))
    try:
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                    ("setting", int(root or 0), "stock_setting", json.dumps(dict(key=key, value=old)),
                     json.dumps(dict(key=key, value=v, label=s["label"])), who or "", now_iso()))
    except Exception:                                         # noqa: BLE001
        pass
    con.commit()
    return True, "%s set." % s["label"]


def set_setting_req(con, key, body, who, root=0):
    """The /pile/setting door: {key, value} -- or, for the consumption list, {key, add: name} / {key, remove: name}."""
    s = SETTING_BY_KEY.get(key)
    whole = key == "stock.whole_unit_items"                   # S437: "ITEM = word" entries; add carries {add: name, word: bottle|jar|pc|tube|vial|sachet}
    lname = "whole-unit" if whole else "consumption"
    entry_name = (lambda x: x.split("=", 1)[0].strip()) if whole else (lambda x: x)
    if s and s["kind"] == "list" and (body.get("add") or body.get("remove")):
        cur = _list_of(setting_raw(con, key) if setting_raw(con, key) is not None else s["default"])
        if body.get("add"):
            name = re.sub(r"\s+", " ", str(body.get("add"))).strip()
            if not name:
                return False, "Name the item."
            if whole:
                name = entry_name(name)
                word = str(body.get("word") or "").strip().lower()
                if word not in WHOLE_WORDS:
                    return False, "Pick the word: %s." % " / ".join(WHOLE_WORDS)
                entry = "%s = %s" % (name, word)
            else:
                entry = name
            if norm_name(name) in {norm_name(entry_name(x)) for x in cur}:
                return True, "%s is already on the list." % name
            cur.append(entry)
            ok, msg = set_setting(con, key, cur, who, root)
            return ok, ("%s added to the %s list%s." % (name, lname, (" as %s" % word) if whole else "")) if ok else msg
        name = entry_name(str(body.get("remove")))
        new = [x for x in cur if norm_name(entry_name(x)) != norm_name(name)]
        if len(new) == len(cur):
            return True, "%s was not on the list." % name
        ok, msg = set_setting(con, key, new, who, root)
        return ok, ("%s taken off the %s list." % (name, lname)) if ok else msg
    return set_setting(con, key, body.get("value"), who, root)


def seed(con, who="S427"):
    """INSERT the kit's defaults for every key that is not there yet; never overwrite. The big-loss floor inherits
    the S418 pursue floor's value; a blank S418 small-gap ceiling becomes Rs 1,000. Returns the keys written."""
    wrote = []
    for s in SETTINGS:
        cur = setting_raw(con, s["key"])
        if s["seed"] is None or cur is not None:
            continue
        val = s["seed"]
        if s["key"] == "stock.big_loss_floor_p" and setting_raw(con, "stock.pursue_floor_p") is not None:
            val = setting_raw(con, "stock.pursue_floor_p")
        con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, note=excluded.note",
                    (s["key"], val, "S427 loss desk setting: %s (seeded)" % s["label"]))
        try:
            con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                        ("setting", 0, "stock_setting", json.dumps(dict(key=s["key"], value=None)),
                         json.dumps(dict(key=s["key"], value=val, label=s["label"], seeded=True)), who, now_iso()))
        except Exception:                                     # noqa: BLE001
            pass
        wrote.append(s["key"])
    con.commit()
    return wrote


def settings_log(con):
    out = []
    try:
        for r in con.execute("SELECT before_json, after_json, by_whom, at FROM audit_log WHERE table_name='setting' AND action='stock_setting' ORDER BY id"):
            b, a = json.loads(r[0] or "{}"), json.loads(r[1] or "{}")
            s = SETTING_BY_KEY.get(a.get("key"))
            if not s:
                continue
            out.append(dict(key=a.get("key"), label=s["label"], old=b.get("value"), new=a.get("value"),
                            old_text=_shown(s, b.get("value")), new_text=_shown(s, a.get("value")),
                            by=r[2] or "", at=r[3], at_text=_sa()._r_stamp(r[3]) + " IST", seeded=bool(a.get("seeded"))))
    except Exception:                                         # noqa: BLE001
        pass
    return out


# ------------------------------------------------------------------ the spine (sales and purchases, read-only)
def _k20(name):
    return re.sub(r"\s+", " ", str(name or "").strip())[:20].strip()


class Spine(object):
    """The one read door onto the spine for this desk: net sales and purchases of an item between two dates.
    SPINE_DB names the file (the walk points it at a scratch copy); missing spine = every figure None."""

    def __init__(self, path=None):
        self.ok, self.con, self._alias, self._cache = False, None, {}, {}
        p = path or SPINE_DB
        try:
            if os.path.exists(p):
                self.con = sqlite3.connect("file:%s?mode=ro" % p, uri=True)
                self._alias = {r[0]: r[1] for r in self.con.execute("SELECT alias, k20 FROM sp_alias")}
                self.ok = True
        except sqlite3.Error:
            self.ok, self.con = False, None

    def key(self, name):
        k = _k20(name)
        return self._alias.get(k, k)

    def sales(self, item, d_from, d_to, incl_from=True):
        """(net tablets/pieces sold, first sale date in the window, lines) -- None when the spine is not there."""
        if not self.ok:
            return None
        ck = ("s", item, d_from, d_to, incl_from)
        if ck not in self._cache:
            op = ">=" if incl_from else ">"
            r = self.con.execute("SELECT COALESCE(SUM(units),0), MIN(date), COUNT(*) FROM sp_sale_line WHERE k20=? AND date %s ? AND date<=?" % op,
                                 (self.key(item), d_from, d_to)).fetchone()
            self._cache[ck] = (float(r[0] or 0), r[1], int(r[2] or 0))
        return self._cache[ck]

    def first_sale(self, item):
        if not self.ok:
            return None
        ck = ("f", item)
        if ck not in self._cache:
            self._cache[ck] = self.con.execute("SELECT MIN(date) FROM sp_sale_line WHERE k20=?", (self.key(item),)).fetchone()[0]
        return self._cache[ck]

    def first_purchase(self, item):
        """The first purchase of the item since the opening (returns aside), or None -- S430's old-stock test."""
        if not self.ok:
            return None
        ck = ("fp", item)
        if ck not in self._cache:
            self._cache[ck] = self.con.execute("SELECT MIN(date) FROM sp_purchase_line WHERE k20=? AND direction<>'RETURN'", (self.key(item),)).fetchone()[0]
        return self._cache[ck]

    def prefetch(self, items, as_on, prev):
        """S432: the sales the allowance needs, for EVERY item in ONE query (and every first sale / first purchase in one each),
        laid into the same cache allowance_for() reads -- the per-line queries then never run. Mirrors allowance_for's window."""
        if not self.ok or not items:
            return 0
        try:
            to_d = dt.date.fromisoformat(as_on)
        except (TypeError, ValueError):
            to_d = dt.date.today()
        keys = {}
        for it in items:
            keys.setdefault(self.key(it), []).append(it)
        ks = list(keys)
        q = ",".join("?" * len(ks))
        first = {r[0]: r[1] for r in self.con.execute("SELECT k20, MIN(date) FROM sp_sale_line WHERE k20 IN (%s) GROUP BY k20" % q, ks)}
        firstp = {r[0]: r[1] for r in self.con.execute("SELECT k20, MIN(date) FROM sp_purchase_line WHERE k20 IN (%s) AND direction<>'RETURN' GROUP BY k20" % q, ks)}
        if prev:
            lo, op = prev, ">"
        else:
            lo, op = (to_d - dt.timedelta(days=FIRST_COUNT_DAYS)).isoformat(), ">="
        sold = {r[0]: (float(r[1] or 0), r[2], int(r[3] or 0)) for r in self.con.execute(
            "SELECT k20, COALESCE(SUM(units),0), MIN(date), COUNT(*) FROM sp_sale_line WHERE k20 IN (%s) AND date %s ? AND date<=? GROUP BY k20" % (q, op), ks + [lo, as_on])}
        n = 0
        for k, its in keys.items():
            for it in its:
                self._cache[("f", it)] = first.get(k)
                self._cache[("fp", it)] = firstp.get(k)
                if prev:
                    frm, incl = prev, False
                else:
                    frm, incl = lo, True
                    f = first.get(k)
                    if f and f > frm:
                        frm = f                                # no sale before the first sale: the same sum
                self._cache[("s", it, frm, as_on, incl)] = sold.get(k, (0.0, None, 0))
                n += 1
        return n

    def purchases(self, item, d_from, d_to):
        """Net tablets/pieces bought (returns off) after d_from up to d_to -- None when the spine is not there."""
        if not self.ok:
            return None
        ck = ("p", item, d_from, d_to)
        if ck not in self._cache:
            r = self.con.execute("SELECT COALESCE(SUM(CASE WHEN direction='RETURN' THEN -units ELSE units END),0) FROM sp_purchase_line "
                                 "WHERE k20=? AND date>? AND date<=?", (self.key(item), d_from, d_to)).fetchone()
            self._cache[ck] = float(r[0] or 0)
        return self._cache[ck]

    def item(self, name):
        if not self.ok:
            return None
        r = self.con.execute("SELECT name, packing, unit_kind FROM sp_item WHERE k20=? ORDER BY last_seen DESC LIMIT 1", (self.key(name),)).fetchone()
        return dict(name=r[0], packing=r[1], unit_kind=r[2]) if r else None

    def search(self, q, limit=12):
        if not self.ok or not q:
            return []
        like = "%" + re.sub(r"\s+", "%", q.strip().upper()) + "%"
        return [r[0] for r in self.con.execute("SELECT DISTINCT name FROM sp_item WHERE UPPER(name) LIKE ? ORDER BY name LIMIT ?", (like, int(limit)))]


def _as_on_iso(con, root, d=None):
    sa = _sa()
    s = (d or {}).get("as_on")
    if not s:
        r = con.execute("SELECT marg_as_on FROM stock_count WHERE id=?", (int(root),)).fetchone()
        s = r[0] if r else ""
    return sa._dmy_to_iso(s) or str(s or "")[:10]


def prev_count_iso(con, root):
    """The Marg date of the previous CLOSED whole-shop count of this unit -- None for the first count."""
    try:
        r = con.execute("SELECT c.marg_as_on FROM stock_count c JOIN stock_count_close k ON k.count_id=c.id "
                        "WHERE c.id<? AND c.unit=(SELECT unit FROM stock_count WHERE id=?) AND c.status='submitted' "
                        "AND c.id NOT IN (SELECT count_id FROM stock_count_part) ORDER BY c.id DESC LIMIT 1", (int(root), int(root))).fetchone()
        return _sa()._dmy_to_iso(r[0]) if r else None
    except sqlite3.Error:
        return None


def allowance_for(con, x, S, as_on, prev, sp):
    """THE ALLOWANCE OF ONE ITEM (3.2): stock.allowance_pct % of what the item itself sold since the previous closed
    count (first count: since its first sale, at most 180 days before the count), never below the floor of
    stock.allowance_min_strips whole strips (pcs). The spine's sales; stock_app's FY figure when the spine is away."""
    pack = int(x.get("pack") or 1)
    floor = S["allowance_min_strips"] * (pack if pack > 1 else 1)
    try:
        to_d = dt.date.fromisoformat(as_on)
    except (TypeError, ValueError):
        to_d = dt.date.today()
    if prev:
        frm = prev
        incl = False
    else:
        frm = (to_d - dt.timedelta(days=FIRST_COUNT_DAYS)).isoformat()
        f = sp.first_sale(x["item"]) if sp.ok else None
        if f and f > frm:
            frm = f
        incl = True
    got = sp.sales(x["item"], frm, as_on, incl) if sp.ok else None
    if got is not None:
        sold, src = got[0], "spine"
    else:
        sold, src = float(x.get("sold_fy") or 0), "sales table"
    try:
        days = max(1, (to_d - dt.date.fromisoformat(frm)).days)
    except (TypeError, ValueError):
        days = FIRST_COUNT_DAYS
    monthly = sold * 30.0 / days
    allow = max(int(S["allowance_pct"] / 100.0 * sold), floor)
    return dict(allow=allow, sold=sold, monthly=monthly, days=days, frm=frm, to=as_on, source=src, floor=floor)


# ------------------------------------------------------------------ the shelf layer (read time)
FIX_LABEL = {"accept_back": "back in store -- shelf = Marg",
             "recount": "recounted -- the shelf agrees with Marg",
             "sales_test": "sold after the count -- the stock existed, the count was short"}


def fixes(con, root):
    """item -> the newest shelf fix of this count."""
    out = {}
    try:
        ensure(con)
        for r in con.execute("SELECT item, qty, source, note, by_user, at FROM stock_shelf_fix WHERE count_id=? ORDER BY id", (int(root),)):
            out[r[0]] = dict(qty=int(r[1]), source=r[2], note=r[3] or "", by=r[4] or "", at=r[5])
    except Exception:                                         # noqa: BLE001
        return {}
    return out


def _fix_one(con, sa, st, x, f):
    """S432: ONE line under its newest shelf fix (the arithmetic apply_fixes always did, factored out so a cached line can be
    recomputed alone). The count-day figures stay on the line."""
    x.setdefault("diff_count_day", x["diff"])
    x.setdefault("mrp_p_count_day", x.get("mrp_p"))
    x.setdefault("cost_p_count_day", x.get("cost_p"))
    x["counted_count_day"] = x["counted"]
    base = int(f["qty"]) - int(x["marg"])
    d0 = int(x["diff_count_day"] or 0)
    sw = int(x.get("swapped") or 0)
    rem = base
    if sw and base and ((base < 0) == (d0 < 0)):
        k = min(abs(base), sw)
        rem = base + k if base < 0 else base - k
    x["counted"] = int(f["qty"])
    x["diff"] = rem
    if rem:
        mv, src = sa._price_value_p(con, x["item"], rem, st)
        x["mrp_p"], x["mrp_source"] = mv, src
        x["cost_p"] = sa._value_p(con, x["item"], rem)
    else:
        x["mrp_p"] = 0 if x.get("mrp_p_count_day") is not None else None
        x["cost_p"] = 0 if x.get("cost_p_count_day") is not None else None
    x["shelf_fix"] = dict(f, at_text=sa._r_stamp(f["at"]) + " IST")
    if rem == 0 and not x.get("word"):
        x["word"] = dict(action="EXPLAINED", swap=True, by=f["by"], at=f["at"], at_text=sa._r_stamp(f["at"]) + " IST",
                         label=FIX_LABEL.get(f["source"], "shelf corrected"), note=f["note"])


def apply_fixes(con, root, diffs):
    """Lay the corrected shelf figures over the report's lines (in place). The count-day figures stay on the
    line (counted_count_day, diff_count_day, mrp_p_count_day, cost_p_count_day). Never raises."""
    try:
        fx = fixes(con, root)
        if not fx:
            return 0
        sa = _sa()
        st = sa._stock_settings(con)
        n = 0
        for x in diffs:
            f = fx.get(x["item"])
            if not f:
                continue
            _fix_one(con, sa, st, x, f)
            n += 1
        return n
    except Exception:                                         # noqa: BLE001 -- a layer is never worth a broken report
        return 0


# ------------------------------------------------------------------ the piles
def _moves(con, root):
    out = {}
    for r in con.execute("SELECT item, pile, by_user, at FROM stock_pile_move WHERE count_id=? ORDER BY id", (int(root),)):
        if r[1] not in MOVE_PILE:                               # 'auto', and S418's pursue / recount: back to the system's choice
            out.pop(r[0], None)
        else:
            out[r[0]] = dict(pile=MOVE_PILE[r[1]], target=r[1], by=r[2] or "", at=r[3])
    return out


def is_old_stock(con, x, S, sp, value):
    """S430 (2.3): no sale and no purchase in the spine since the opening, AND (no price on record, or stock.old_stock_days
    passed without either). Never a Big loss; written off, not a loss."""
    if not sp.ok:
        return False
    if sp.first_sale(x["item"]) or sp.first_purchase(x["item"]):
        return False
    if value is None:
        return True
    try:
        days = (dt.date.today() - dt.date.fromisoformat(OPENING_DAY)).days
    except ValueError:
        days = 0
    return days >= S["old_stock_days"]


def _runs_by_item(con, root):
    out = {}
    for r in con.execute("SELECT id, at, groups FROM stock_writeoff_run WHERE count_id=? ORDER BY id", (int(root),)):
        try:
            g = json.loads(r[2])
        except ValueError:
            continue
        for grp, rows in g.items():
            for l in rows:
                out[l["item"]] = dict(group=grp, run=int(r[0]), at=r[1])
    return out


def _tests_by_item(con, root):
    out = {}
    try:
        for r in con.execute("SELECT item, at, counted, marg, sold_after, bought_after, as_on, upto FROM stock_sales_test WHERE count_id=? ORDER BY id", (int(root),)):
            out[r[0]] = dict(at=r[1], counted=r[2], marg=r[3], sold_after=r[4], bought_after=r[5], as_on=r[6], upto=r[7])
    except sqlite3.Error:
        pass
    return out


def _shares_by_item(con, root):
    out = {}
    try:
        for r in con.execute("SELECT id, no, lines, made_at FROM stock_loss_share WHERE count_id=? ORDER BY no", (int(root),)):
            for l in json.loads(r[2]):
                out.setdefault(l["item"], dict(no=int(r[1]), id=int(r[0]), at=r[3]))
    except Exception:                                         # noqa: BLE001
        pass
    return out


def _claims_by_item(con, root):
    sa = _sa()
    out = {}
    if not getattr(sa, "CLAIM_QUEUE_OK", False):
        return out
    try:
        for c in sa._cq.lines(con, int(root), limit=500):
            out[c["item"]] = c
    except Exception:                                         # noqa: BLE001
        pass
    return out


def is_ortho(con, x):
    sa = _sa()
    return x.get("lane") == "ortho" or sa._item_section(con, x) == "Orthotics"


def is_consume(con, x, S, amap=None):
    """On the owner's list -- by name, after normalisation; a ticked rename (item_alias) counts too. Never a word rule."""
    keys = S["consume_keys"]
    if not keys:
        return False
    item = x["item"]
    if norm_name(item) in keys:
        return True
    try:
        amap = amap if amap is not None else _sa()._alias_map(con)
        for f, old in amap.items():
            if norm_name(old) == norm_name(item) and norm_name(f) in keys:
                return True
            if norm_name(f) == norm_name(item) and norm_name(old) in keys:
                return True
    except Exception:                                         # noqa: BLE001
        pass
    return False


def _loss(x, key="mrp_p"):
    v = x.get(key)
    return (-int(v)) if (v is not None and int(v) < 0) else (0 if v is not None else None)


def _rule(con, x, S, A):
    """(pile, group, why) for one OPEN shortage with no move of the owner's on it and not on the consumption list."""
    short = -int(x["diff"])
    pack, packing, name = int(x.get("pack") or 1), x.get("packing") or "", x["item"]
    sold_t = qw(A["sold"], pack, packing, name)
    frm_t = _sa()._r_dmy(A["frm"])
    if short <= A["allow"]:
        return "writeoff", "allowance", "short %s -- within the allowance of %s (%g%% of the %s it sold since %s%s)" % (
            qw(short, pack, packing, name), qw(A["allow"], pack, packing, name), S["allowance_pct"], sold_t, frm_t,
            "; the floor" if A["allow"] == A["floor"] and A["floor"] > int(S["allowance_pct"] / 100.0 * A["sold"]) else "")
    v = _loss(x)
    if v is None:
        v = _loss(x, "cost_p")
    pct = (100.0 * short / A["sold"]) if A["sold"] else None
    beyond = "short %s%s against %s sold since %s" % (qw(short, pack, packing, name), (" (%.1f%%)" % pct) if pct is not None else "", sold_t, frm_t)
    if v is None:
        return "bigloss", "big", beyond + " -- no price on record, so the loss cannot be called small"
    if v >= S["big_loss_floor_p"]:
        return "bigloss", "big", "%s at MRP -- %s or more is a big loss; %s" % (_rs(v), _rs(S["big_loss_floor_p"]), beyond)
    if A["sold"] > 0 and short >= S["slow_months"] * A["monthly"] and v >= S["slow_floor_p"]:
        months = short / A["monthly"] if A["monthly"] else 0
        return "bigloss", "big", "a slow item: the gap is %.1f months of its own sales (%s a month) -- %s at MRP" % (
            months, qw(A["monthly"], pack, packing, name), _rs(v))
    if A["sold"] <= 0 and int(x["marg"]) > 0 and v >= S["slow_floor_p"]:
        return "bigloss", "big", "never sold in %d days, yet Marg held %s -- %s at MRP" % (FIRST_COUNT_DAYS if not A.get("prev") else A["days"], qw(x["marg"], pack, packing, name), _rs(v))
    if v < S["small_gap_ceiling_p"]:
        return "writeoff", "small", "a real gap of %s, under %s; %s" % (_rs(v), _rs(S["small_gap_ceiling_p"]), beyond)
    return "bigloss", "big", "%s at MRP -- above the small-gap ceiling of %s; %s" % (_rs(v), _rs(S["small_gap_ceiling_p"]), beyond)


def _ctx(con, root, d=None, S=None, sp=None):
    """S432: everything classify() reads besides the line itself, read ONCE for a pass (or for a one-line recompute)."""
    sa = _sa()
    ensure(con)
    S = S or settings(con)
    sp = sp or Spine()
    try:
        amap = sa._alias_map(con)
    except Exception:                                         # noqa: BLE001
        amap = {}
    return dict(sa=sa, S=S, sp=sp, root=root, as_on=_as_on_iso(con, root, d), prev=prev_count_iso(con, root),
                moves=_moves(con, root), fx=fixes(con, root), runs=_runs_by_item(con, root), shares=_shares_by_item(con, root),
                tests=_tests_by_item(con, root), amap=amap)


def _classify_one(con, x, C):
    """ONE line of the round -> (kind, line): kind 'line' (a desk line with its bucket), 'over' (the Over note),
    'ortho' (not on this desk) or 'skip' (a surplus written down / explained: no loss line). The whole rule of the piles."""
    sa, S, sp = C["sa"], C["S"], C["sp"]
    if is_ortho(con, x):
        return "ortho", None
    item = x["item"]
    w = x.get("word") or {}
    act = w.get("action")
    rem = int(x["diff"] or 0)
    d0 = int(x.get("diff_count_day", rem) or 0)
    f = C["fx"].get(item)
    pack, packing = int(x.get("pack") or 1), x.get("packing") or ""
    mv = C["moves"].get(item)
    if mv and f and f["source"] == "recount" and str(f["at"]) >= str(mv["at"]):
        mv = None                                               # Darpan's figure came after the move: the line re-piles itself
    base = dict(item=item, packing=packing, pack=pack, marg=int(x["marg"]), counted=int(x["counted"]),
                diff=rem, diff_count_day=d0, short_units=(-rem if rem < 0 else 0),
                short_text=(qw(-rem, pack, packing, item) if rem < 0 else ""),
                short_hi=(qw(-rem, pack, packing, item, "hi") if rem < 0 else ""),
                mrp_p=_loss(x), cost_p=_loss(x, "cost_p"),
                mrp_day_p=_loss(dict(mrp_p=x.get("mrp_p_count_day", x.get("mrp_p")))),
                cost_day_p=_loss(dict(cost_p=x.get("cost_p_count_day", x.get("cost_p"))), "cost_p"),
                short_day_text=(qw(-d0, pack, packing, item) if d0 < 0 else ""),
                consumable=is_consume(con, x, S, C["amap"]), moved=None, sent=None, recount=None, test=None,
                word=act or "", word_by=w.get("by") or "", word_at=w.get("at") or "", life=x.get("life"),
                swapped=int(x.get("swapped") or 0), marg_text=qw(x["marg"], pack, packing, item),
                counted_text=qw(x["counted"], pack, packing, item))
    if f:
        base["recount"] = dict(qty=f["qty"], source=f["source"], by=f["by"], at=f["at"],
                               at_text=sa._r_stamp(f["at"]) + " IST", qty_text=qw(f["qty"], pack, packing, item),
                               counted_day=int(x.get("counted_count_day", x["counted"])))
    if item in C["tests"]:
        t = C["tests"][item]
        base["test"] = dict(t, at_text=sa._r_stamp(t["at"]) + " IST", sold_text=qw(t["sold_after"], pack, packing, item),
                            bought_text=qw(t["bought_after"], pack, packing, item), counted_text=qw(t["counted"], pack, packing, item))
    if act == "WRITE_OFF":
        if d0 >= 0 and rem >= 0:
            return "skip", None                                 # a surplus written down: not a loss line
        r = C["runs"].get(item)
        base.update(bucket="written_off", pile=None, group=(r or {}).get("group") or "earlier",
                    why="written off " + (sa._r_stamp(w.get("at")) + " IST" if w.get("at") else ""))
        return "line", base
    if act in ("EXPLAINED", "MARG_FIX") or rem == 0:
        if d0 >= 0:
            return "skip", None                                 # a surplus explained: never a loss line
        base.update(bucket="back", pile=None, group=None, why=(w.get("label") or "explained -- no loss"))
        return "line", base
    if rem > 0:
        return "over", dict(base, bucket="over", pile=None, group=None, over_text=qw(rem, pack, packing, item),
                            why=("recounted by %s: %s more than Marg -- never a loss" % (f["by"] or "Darpan", qw(rem, pack, packing, item))) if (f and f["source"] == "recount")
                            else "more on the shelf than Marg -- never a loss; the close corrects the shelf figure")
    # an OPEN shortage -- the owner's move first, then his PARKED word, then the list, then the rules
    A = allowance_for(con, x, S, C["as_on"], C["prev"], sp)
    A["prev"] = C["prev"]
    base.update(allow_units=A["allow"], allow_text=qw(A["allow"], pack, packing, item), sold_units=A["sold"],
                sold_text=qw(A["sold"], pack, packing, item), sold_from=sa._r_dmy(A["frm"]), sold_source=A["source"],
                pct=((round(100.0 * -rem / A["sold"], 1)) if A["sold"] else None))
    if mv:
        pile, why = mv["pile"], "moved here by you"
        base["moved"] = mv
        if pile == "writeoff":
            group = "allowance" if -rem <= A["allow"] else "small"
        else:
            group = GROUP_OF_PILE.get(mv.get("target") or pile)
        if group == "owner_use":
            why = "owner's use -- taken for home, unbilled (moved here by you); a recorded non-loss"
        elif group == "consume" and base["consumable"]:
            why = "on your consumption list -- used in the clinic, never billed"
    elif act == "PARKED":
        pile, group, why = "with_me", None, "you had it set aside -- kept elsewhere, not counted"
    elif base["consumable"]:
        pile, group, why = "consume", "consume", "on your consumption list -- used in the clinic, never billed"
    elif is_old_stock(con, x, S, sp, (_loss(x) if _loss(x) is not None else _loss(x, "cost_p"))):
        pile, group = "writeoff", "old"
        why = "old stock -- no sale and no purchase since %s%s; written off, not a loss" % (
            sa._r_dmy(OPENING_DAY), "" if (_loss(x) is not None or _loss(x, "cost_p") is not None) else ", no price on record")
    else:
        pile, group, why = _rule(con, x, S, A)
    if f and f["source"] == "recount":
        why = "recounted by %s: %s on the shelf -- %s" % (f["by"] or "Darpan", qw(f["qty"], pack, packing, item), why)
    base.update(bucket=pile, pile=pile, group=group, why=why, sent=C["shares"].get(item))
    return "line", base


def classify(con, d, S=None, sp=None):
    """Every line of the round that belongs on the desk, with its bucket. One pass; the hub, the record, the statement
    and the cache's full build all call this. Returns (lines, over, skipped_ortho). S432: the spine's sales for every
    item are fetched in ONE query before the pass (Spine.prefetch)."""
    C = _ctx(con, d["count_id"], d, S, sp)
    if C["sp"].ok:
        try:
            C["sp"].prefetch([x["item"] for x in d["differences"] if int(x["diff"] or 0) < 0], C["as_on"], C["prev"])
        except sqlite3.Error:
            pass
    lines, over, skipped = [], [], 0
    for x in d["differences"]:
        kind, l = _classify_one(con, x, C)
        if kind == "ortho":
            skipped += 1
        elif kind == "line":
            lines.append(l)
        elif kind == "over":
            over.append(l)
    return lines, over, skipped


# ------------------------------------------------------------------ S432 (F-651): THE CACHE -- the piles computed once, stored
STAMP_VERSION = "S432.1"
FULL_PARTS = ("v", "settings", "spine", "items", "matches", "prices", "alias", "sections", "snapshot", "close")   # any change -> everything
PART_TABLES = {"moves": "stock_pile_move", "fixes": "stock_shelf_fix", "words": "stock_diff_lane", "tests": "stock_sales_test",
               "runs": "stock_writeoff_run", "shares": "stock_loss_share"}                                             # a change -> the touched lines


def _maxid(con, table, where="", args=()):
    try:
        r = con.execute("SELECT COALESCE(MAX(id),0), COUNT(*) FROM %s %s" % (table, where), args).fetchone()
        return "%d/%d" % (int(r[0] or 0), int(r[1] or 0))
    except sqlite3.Error:
        return "-"


def _spine_stamp():
    p = SPINE_DB
    try:
        st = os.stat(p)
        return "%d:%d" % (int(st.st_mtime * 1000), st.st_size)
    except OSError:
        return "none"


def stamp(con, root):
    """Every input of the piles, versioned -- cheap queries, no report. FULL_PARTS rebuild everything; the rest name the lines."""
    try:
        fam = [int(root)] + [int(r[0]) for r in con.execute("SELECT count_id FROM stock_count_part WHERE part_of=? ORDER BY count_id", (int(root),))]
    except sqlite3.Error:
        fam = [int(root)]
    q = ",".join("?" * len(fam))
    fam = tuple(fam)
    try:
        sv = hashlib.md5("|".join("%s=%s" % (r[0], r[1]) for r in con.execute("SELECT key, value FROM setting WHERE key LIKE 'stock.%' ORDER BY key")).encode("utf-8")).hexdigest()[:12]
    except sqlite3.Error:
        sv = "-"
    try:
        as_on = con.execute("SELECT marg_as_on FROM stock_count WHERE id=?", (int(root),)).fetchone()[0]
        snap = con.execute("SELECT COUNT(*), COALESCE(MAX(loaded_at),'') FROM stock_snapshot WHERE as_on=?", (as_on,)).fetchone()
        snap = "%d/%s" % (snap[0], snap[1])
    except (sqlite3.Error, TypeError):
        snap = "-"

    def cnt(sql, args=()):
        try:
            r = con.execute(sql, args).fetchone()
            return "/".join(str(v if v is not None else "") for v in r)
        except sqlite3.Error:
            return "-"
    out = dict(v=STAMP_VERSION, settings=sv, spine=_spine_stamp(),
               items=cnt("SELECT COUNT(*), COALESCE(MAX(id),0), COALESCE(SUM(marg_qty),0), COALESCE(SUM(counted_qty),0) FROM stock_count_item WHERE count_id IN (%s)" % q, fam)
               + "|" + cnt("SELECT COUNT(*), COALESCE(MAX(id),0) FROM stock_diff WHERE count_id IN (%s)" % q, fam),
               matches=_maxid(con, "stock_match", "WHERE count_id=?", (int(root),)),
               prices=cnt("SELECT COUNT(*), COALESCE(MAX(set_at),'') FROM stock_mrp_manual") + "|" + cnt("SELECT COUNT(*), COALESCE(SUM(rate_p),0) FROM stock_rate"),
               alias=_maxid(con, "marg_item_rename"), sections=cnt("SELECT COUNT(*), COALESCE(MAX(at),'') FROM stock_item_section"), snapshot=snap,
               close=cnt("SELECT COUNT(*) FROM stock_count_close WHERE count_id IN (%s)" % q, fam) + "|" + cnt("SELECT COUNT(*) FROM stock_count_part WHERE part_of=?", (int(root),)))
    for part, table in PART_TABLES.items():
        out[part] = _maxid(con, table, "WHERE count_id=?", (int(root),))
    return out


def _x_store(x):
    """The report's line as it stood AFTER the swap layer and BEFORE the shelf-fix layer, its count-day figures kept -- what a
    one-line recompute starts from (the swap layer's inputs are FULL parts of the stamp, so it never changes under a partial
    refresh; the fix and the word are laid on again at recompute). The matcher's own word on a wholly-swapped line is kept."""
    y = {k: v for k, v in x.items() if k not in ("word", "shelf_fix", "answer", "cause", "decision", "ours", "ours_gap", "lookups", "residue", "family_verdict",
                                                  "counted_count_day", "diff_count_day", "mrp_p_count_day", "cost_p_count_day")}
    d0 = int(x.get("diff_count_day", x["diff"]) or 0)
    mrp0, cost0 = x.get("mrp_p_count_day", x.get("mrp_p")), x.get("cost_p_count_day", x.get("cost_p"))
    y["counted"] = int(x.get("counted_count_day", x["counted"]))
    sw = int(x.get("swapped") or 0)
    if sw:
        n = min(abs(d0), sw)
        rem = d0 + n if d0 < 0 else d0 - n
        f = (abs(rem) / float(abs(d0))) if d0 else 0.0
        y.update(diff=rem, mrp_p=(None if mrp0 is None else int(round(mrp0 * f))), cost_p=(None if cost0 is None else int(round(cost0 * f))),
                 diff_count_day=d0, mrp_p_count_day=mrp0, cost_p_count_day=cost0)
    else:
        y.update(diff=d0, mrp_p=mrp0, cost_p=cost0)
    w = x.get("word") or {}
    if w.get("swap") and not w.get("by") and "swapped with" in (w.get("note") or ""):
        y["swap_word"] = w
    return y


def _x_load(con, C, y, words):
    """The stored line back under today's word and shelf fix (the swap layer is already on it)."""
    x = dict(y)
    sw = x.pop("swap_word", None)
    x["word"] = words.get(x["item"]) or sw
    f = C["fx"].get(x["item"])
    if f:
        _fix_one(con, C["sa"], C["sa"]._stock_settings(con), x, f)
    return x


def _light_d(con, root):
    """What desk(), record() and block_preview() need of the report besides the lines -- one row of stock_count."""
    sa = _sa()
    r = con.execute("SELECT marg_as_on, submitted_at FROM stock_count WHERE id=?", (int(root),)).fetchone()
    when = (r[1] if r else "") or ""
    return dict(count_id=int(root), as_on=(r[0] if r else ""), day=sa._r_dmy(when[:10]) if when else "", when=(sa._r_stamp(when) + " IST") if when else "",
                links=dict(amir_page="/finance/stock/page/amir?count=%d" % int(root)))


def _cache_rows(con, root):
    lines, over, skipped = [], [], 0
    for r in con.execute("SELECT bucket, line_json FROM stock_pile_cache WHERE count_id=? ORDER BY item", (int(root),)):
        l = json.loads(r[1])
        (over if r[0] == "over" else lines).append(l)
    m = con.execute("SELECT skipped FROM stock_pile_cache_meta WHERE count_id=?", (int(root),)).fetchone()
    return lines, over, int((m[0] if m else 0) or 0)


def rebuild(con, root, who="system", d=None, sp=None):
    """THE FULL BUILD: the report once, the sales-after-count test on it (a hit -> the report once more), classify with the
    spine prefetched, every row written in ONE transaction with the stamp. Returns (lines, over, skipped, info)."""
    sa = _sa()
    t0 = dt.datetime.now()
    sp = sp or Spine()
    d = d or sa._pad_report_data(con, root)
    if d is None:
        return None
    hits = sales_test(con, root, d=d, sp=sp, who="system")
    if hits:
        d = sa._pad_report_data(con, root)
    S = settings(con)
    lines, over, skipped = classify(con, d, S, sp)
    diffs = {x["item"]: x for x in d["differences"]}
    did = {}
    try:
        _r, fam, _R = sa._pad_family(con, root)
        q = ",".join("?" * len(fam))
        for r in con.execute("SELECT item, id FROM stock_diff WHERE count_id IN (%s) ORDER BY count_id, id" % q, tuple(fam)):
            did[r[0]] = int(r[1])
    except Exception:                                         # noqa: BLE001
        pass
    st = stamp(con, root)
    ts = now_iso()
    con.execute("DELETE FROM stock_pile_cache WHERE count_id=?", (int(root),))
    for l in lines + over:
        con.execute("INSERT OR REPLACE INTO stock_pile_cache (count_id, item, diff_id, bucket, pile, grp, allow_units, mrp_p, why, x_json, line_json, built_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (int(root), l["item"], did.get(l["item"]), l["bucket"], l.get("pile"), l.get("group"), l.get("allow_units"), l.get("mrp_p"), l.get("why") or "",
                     json.dumps(_x_store(diffs[l["item"]]), default=str, separators=(",", ":")), json.dumps(l, default=str, separators=(",", ":")), ts))
    ms = int((dt.datetime.now() - t0).total_seconds() * 1000)
    con.execute("INSERT OR REPLACE INTO stock_pile_cache_meta (count_id, stamp, built_at, full_ms, lines_n, over_n, skipped, last_partial_at, last_partial_n, last_partial_ms) VALUES (?,?,?,?,?,?,?,NULL,NULL,NULL)",
                (int(root), json.dumps(st, sort_keys=True), ts, ms, len(lines), len(over), skipped))
    con.commit()
    return lines, over, skipped, dict(built="full", ms=ms, built_at=ts, sales_hits=hits, lines_n=len(lines))


def _touched_items(con, root, old, new):
    """The items behind the changed non-full parts: rows written since the stamp (id > the old max)."""
    items = set()
    for part, table in PART_TABLES.items():
        if old.get(part) == new.get(part):
            continue
        try:
            omax = int(str(old.get(part, "0/0")).split("/")[0] or 0)
        except ValueError:
            omax = 0
        try:
            if table == "stock_writeoff_run":
                for r in con.execute("SELECT groups FROM stock_writeoff_run WHERE count_id=? AND id>?", (int(root), omax)):
                    for rows in json.loads(r[0]).values():
                        items.update(x["item"] for x in rows)
            elif table == "stock_loss_share":
                for r in con.execute("SELECT lines FROM stock_loss_share WHERE count_id=? AND id>?", (int(root), omax)):
                    items.update(x["item"] for x in json.loads(r[0]))
            else:
                items.update(r[0] for r in con.execute("SELECT DISTINCT item FROM %s WHERE count_id=? AND id>?" % table, (int(root), omax)))
        except (sqlite3.Error, ValueError, KeyError, TypeError):
            return None                                        # cannot name them: the caller rebuilds everything
    return items


def refresh_items(con, root, items, C=None):
    """Recompute the named lines only, from their stored count-day inputs under today's word / fix / move / test / run.
    Returns the recomputed lines by item (a line that left the desk maps to None)."""
    sa = _sa()
    C = C or _ctx(con, root)
    words = sa._lane_actions(con, root)
    out = {}
    if not items:
        return out
    q = ",".join("?" * len(items))
    rows = {r[0]: (r[1], r[2]) for r in con.execute("SELECT item, x_json, diff_id FROM stock_pile_cache WHERE count_id=? AND item IN (%s)" % q, (int(root),) + tuple(items))}
    ts = now_iso()
    for item in items:
        if item not in rows:
            continue                                           # not a line of this round's cache (a name the desk never saw): nothing to recompute
        y = json.loads(rows[item][0])
        x = _x_load(con, C, y, words)
        kind, l = _classify_one(con, x, C)
        if kind in ("line", "over"):
            con.execute("UPDATE stock_pile_cache SET bucket=?, pile=?, grp=?, allow_units=?, mrp_p=?, why=?, line_json=?, built_at=? WHERE count_id=? AND item=?",
                        (l["bucket"], l.get("pile"), l.get("group"), l.get("allow_units"), l.get("mrp_p"), l.get("why") or "", json.dumps(l, default=str, separators=(",", ":")), ts, int(root), item))
            out[item] = l
        else:
            con.execute("DELETE FROM stock_pile_cache WHERE count_id=? AND item=?", (int(root), item))
            out[item] = None
    return out


def cached(con, root, force=False, who="system"):
    """THE READ: the cached lines, refreshed as their stamp demands -- nothing (equal), the touched lines (moves / fixes /
    words / tests / runs), or everything (a setting, the spine build, a price, a count row). Returns (lines, over, skipped, info)."""
    ensure(con)
    m = con.execute("SELECT stamp, built_at, full_ms, last_partial_at FROM stock_pile_cache_meta WHERE count_id=?", (int(root),)).fetchone()
    new = stamp(con, root)
    if force or not m:
        r = rebuild(con, root, who)
        if r is None:
            return None
        return r
    old = json.loads(m[0])
    if any(old.get(k) != new.get(k) for k in FULL_PARTS):
        return rebuild(con, root, who)
    changed = [k for k in PART_TABLES if old.get(k) != new.get(k)]
    info = dict(built="cache", built_at=m[1], full_ms=m[2], last_partial_at=m[3])
    if changed:
        t0 = dt.datetime.now()
        items = _touched_items(con, root, old, new)
        if items is None:
            return rebuild(con, root, who)
        done = refresh_items(con, root, sorted(items))
        ms = int((dt.datetime.now() - t0).total_seconds() * 1000)
        ts = now_iso()
        con.execute("UPDATE stock_pile_cache_meta SET stamp=?, last_partial_at=?, last_partial_n=?, last_partial_ms=? WHERE count_id=?",
                    (json.dumps(new, sort_keys=True), ts, len(done), ms, int(root)))
        con.commit()
        info.update(built="partial", partial_n=len(done), partial_ms=ms, partial_items=sorted(done)[:40], last_partial_at=ts)
    lines, over, skipped = _cache_rows(con, root)
    return lines, over, skipped, info


def cache_info(con, root):
    m = con.execute("SELECT stamp, built_at, full_ms, lines_n, over_n, skipped, last_partial_at, last_partial_n, last_partial_ms FROM stock_pile_cache_meta WHERE count_id=?", (int(root),)).fetchone()
    if not m:
        return None
    return dict(built_at=m[1], built_text=_sa()._r_stamp(m[1]) + " IST", full_ms=m[2], lines_n=m[3], over_n=m[4], skipped=m[5],
                last_partial_at=m[6], last_partial_n=m[7], last_partial_ms=m[8], stamp=json.loads(m[0]))


def _sum(ls, day=False):
    k1, k2 = ("mrp_day_p", "cost_day_p") if day else ("mrp_p", "cost_p")
    return dict(n=len(ls), mrp_p=sum(l[k1] or 0 for l in ls), cost_p=sum(l[k2] or 0 for l in ls),
                unpriced=sum(1 for l in ls if l[k1] is None))


def totals_of(lines):
    """THE TOTALS -- defined here, once. Every desk line is in exactly one bucket:
         back        back in store / explained -- valued at the count day (what did not go missing)
         written_off written off -- by group (allowance / small / consume / big / earlier)
         with_me, writeoff, bigloss, consume -- the four piles still open
       open  = with_me + writeoff + bigloss + consume
       short = open + back + written_off   (every desk shortage of the round)"""
    by = {}
    for l in lines:
        by.setdefault(l["bucket"], []).append(l)
    back = _sum(by.get("back", []), day=True)
    wo = _sum(by.get("written_off", []))
    wo["groups"] = {g: _sum([l for l in by.get("written_off", []) if l["group"] == g]) for g, _t, _b in GROUPS}
    piles = {}
    for k, _t in PILES:
        piles[k] = _sum(by.get(k, []))
    piles["writeoff"]["groups"] = {g: _sum([l for l in by.get("writeoff", []) if l["group"] == g]) for g, _t, _b in GROUPS}
    open_ = dict(n=sum(piles[k]["n"] for k, _t in PILES), mrp_p=sum(piles[k]["mrp_p"] for k, _t in PILES),
                 cost_p=sum(piles[k]["cost_p"] for k, _t in PILES), unpriced=sum(piles[k]["unpriced"] for k, _t in PILES))
    short = dict(n=open_["n"] + back["n"] + wo["n"], mrp_p=open_["mrp_p"] + back["mrp_p"] + wo["mrp_p"],
                 cost_p=open_["cost_p"] + back["cost_p"] + wo["cost_p"], unpriced=open_["unpriced"] + back["unpriced"] + wo["unpriced"])
    return dict(open=open_, back=back, written_off=wo, with_me=piles["with_me"], writeoff=piles["writeoff"],
                bigloss=piles["bigloss"], consume=piles["consume"], short=short)


def totals(con, d):
    """The one figure the desk, the hub's status card and the record PDF all print."""
    lines, _o, _s = classify(con, d)
    return totals_of(lines)


def _sortkey(l):
    return (-(l["mrp_p"] if l["mrp_p"] is not None else -1), l["item"])


def rules_view(S):
    return dict(allowance_pct=("%g" % S["allowance_pct"]), allowance_min=S["allowance_min_strips"], ceiling=_rs(S["small_gap_ceiling_p"]),
                big_floor=_rs(S["big_loss_floor_p"]), slow_months=("%g" % S["slow_months"]), slow_floor=_rs(S["slow_floor_p"]),
                batch=S["voucher_batch"], consume_items=S["consume_items"], staff_items=S["staff_block_items"])


def desk(con, d, who=""):
    """Everything the Loss desk page shows -- the S427 door (classify on a report); the desk itself reads desk_cached()."""
    S = settings(con)
    lines, over, skipped = classify(con, d, S)
    return _desk_from(con, d, lines, over, skipped, who, S)


def desk_cached(con, root, who="", lite=False, pile=None, force=False):
    """S432: the desk from the cache -- no report, no sales test, no trace, no watch scoring on the read path.
    lite=True: the totals, the piles' headers, the close and the block only (the page draws these first);
    pile=<key>: that pile's lines only (the page fetches a pile's list when it is opened)."""
    S = settings(con)
    got = cached(con, root, force=force, who=who)
    if got is None:
        return None
    lines, over, skipped, info = got
    out = _desk_from(con, _light_d(con, root), lines, over, skipped, who, S, lite=lite, pile=pile)
    out["cache"] = dict(info, meta=cache_info(con, root))
    return out


def _desk_from(con, d, lines, over, skipped, who, S, lite=False, pile=None):
    sa = _sa()
    claims = _claims_by_item(con, d["count_id"])
    for l in lines:
        c = claims.get(l["item"])
        if c:
            l["claim"] = dict(state=c["state"], answer=c.get("answer_label") or "", note=c.get("answer_note") or "",
                              outcome=c.get("outcome_label") or "")
    T = totals_of(lines)
    piles = []
    for k, title in PILES:
        ls = sorted([l for l in lines if l["bucket"] == k], key=_sortkey)
        if k == "with_me":
            ls.sort(key=lambda l: (l["word"] != "PARKED", -(l["mrp_p"] or 0), l["item"]))
        if k == "writeoff":
            order = {g: i for i, (g, _t, _b) in enumerate(GROUPS)}
            ls.sort(key=lambda l: (order.get(l["group"], 9), -(l["mrp_p"] or 0), l["item"]))
        piles.append(dict(key=k, title=title, title_hi=PILE_HI[k], lines=(ls if (not lite and (pile is None or pile == k)) else []), lines_n=len(ls), **T[k]))
    over.sort(key=lambda l: (-l["diff"], l["item"]))
    close_items = sorted(l["item"] for l in lines if l["bucket"] in CLOSE_PILES)
    # S432: the group list -- every open line outside With me, by its group (the owner clears a group at a time)
    grp_n = {}
    for l in lines:
        if l["bucket"] in CLOSE_PILES:
            g = l["group"] or ("consume" if l["bucket"] == "consume" else ("big" if l["bucket"] == "bigloss" else "small"))
            grp_n[g] = grp_n.get(g, 0) + 1
    out = dict(kit=KIT, version=VERSION, count_id=d["count_id"], day=d.get("day") or "", as_on=d.get("as_on") or "", when=d.get("when") or "",
               totals=T, piles=piles, orthotics_elsewhere=skipped,
               groups=[dict(key=g, title=t, blurb=b, open_n=grp_n.get(g, 0)) for g, t, b in GROUPS],
               rules=rules_view(S), block=block_view(con, d["count_id"]), block_preview=block_preview(con, d, S, lines=lines),
               close=dict(n=len(close_items), items=close_items, mrp_p=sum((l["mrp_p"] or 0) for l in lines if l["bucket"] in CLOSE_PILES)),
               may_accept=True, arm_seconds=ARM_SECONDS, lite=bool(lite),
               links=dict(hub="/finance/stock/page/hub?count=%d" % d["count_id"], amir=d["links"]["amir_page"],
                          record_pdf="/finance/stock/api/loss/%d/record.pdf" % d["count_id"],
                          report="/finance/stock/page/report?count=%d" % d["count_id"], stockmatch="/finance/stockmatch"))
    if lite:
        out.update(done=dict(back=[], written_off=[]), over=[], sold_after=[], settings=[], record=None)
        return out
    out.update(done=dict(back=sorted([l for l in lines if l["bucket"] == "back"], key=_sortkey),
                         written_off=sorted([l for l in lines if l["bucket"] == "written_off"], key=lambda l: (l["group"], -(l["mrp_p"] or 0), l["item"]))),
               over=over, sold_after=sorted([l for l in lines if l.get("test")], key=_sortkey),
               settings=settings_view(con), record=record(con, d, lines=lines))
    return out


def patch_of(con, root, lines_by_item, items):
    """S432: what a tap returns so the page updates in place -- the changed lines (None = left the desk) and the totals."""
    lines, over, skipped = _cache_rows(con, root)
    T = totals_of(lines)
    close_items = sorted(l["item"] for l in lines if l["bucket"] in CLOSE_PILES)
    grp_n = {}
    for l in lines:
        if l["bucket"] in CLOSE_PILES:
            g = l["group"] or ("consume" if l["bucket"] == "consume" else ("big" if l["bucket"] == "bigloss" else "small"))
            grp_n[g] = grp_n.get(g, 0) + 1
    return dict(lines={i: lines_by_item.get(i) for i in items}, totals=T,
                close=dict(n=len(close_items), items=close_items, mrp_p=sum((l["mrp_p"] or 0) for l in lines if l["bucket"] in CLOSE_PILES)),
                groups_n=grp_n, block_preview=block_preview(con, _light_d(con, root), None, lines=lines), block=block_view(con, root))


# ------------------------------------------------------------------ the record (the audit trail at the desk's foot)
def _kind_text(kind, groups_n):
    """S432: a run's kind in words -- 'Close the count' / 'Clear this group -- Big losses' / 'Write off this pile'."""
    k = str(kind or "")
    if k.startswith("clear:"):
        g = k[6:]
        return "Clear this group -- %s" % ("All groups" if g == "all" else GROUP_TITLE.get(g, g))
    if k == "pile":
        return "Write off this pile"
    if k == "close":
        return "Close the count"
    if k == ORTHO_RUN_KIND:
        return "Orthotics closed by rule -- the orthotic loss at selling price"
    if k == RECEIVE_RUN_KIND:
        return "Marg corrected -- the STOCK RECEIVE vouchers by rule (never a loss)"
    return "Close the count" if len(groups_n) != 1 else "Write off"


def runs(con, root):
    out = []
    for r in con.execute("SELECT id, at, by_user, lines_n, mrp_p, cost_p, unpriced, groups, settings, round_no, md5, kind "
                         "FROM stock_writeoff_run WHERE count_id=? ORDER BY id", (int(root),)):
        g = json.loads(r[7])
        out.append(dict(id=r[0], at=r[1], at_text=_sa()._r_stamp(r[1]) + " IST", by=r[2] or "", lines=r[3], mrp_p=r[4],
                        cost_p=r[5], unpriced=r[6], round_no=r[9], md5=(r[10] or "")[:8], kind=r[11] or "", kind_text=_kind_text(r[11], g),
                        orthotic=((r[11] or "") == ORTHO_RUN_KIND), corrective=((r[11] or "") == RECEIVE_RUN_KIND),
                        groups=[dict(key=k, title=GROUP_TITLE.get(k) or ORTHO_GROUP_TITLE.get(k) or RECEIVE_GROUP_TITLE.get(k, k), lines=v, n=len(v), mrp_p=sum(l["mrp_p"] or 0 for l in v),
                                     cost_p=sum(l["cost_p"] or 0 for l in v)) for k, v in g.items() if v],
                        settings=json.loads(r[8])))
    return out


def closes(con, root):
    """S432: every frozen staff block of the count -- a tap close, or the count closing by itself after the last clear."""
    out = []
    try:
        for r in con.execute("SELECT id, run_id, at, by_user, total_p, small_p, big_p, how FROM stock_staff_block WHERE count_id=? ORDER BY id", (int(root),)):
            out.append(dict(id=r[0], run_id=r[1], at=r[2], at_text=_sa()._r_stamp(r[2]) + " IST", by=r[3] or "", total_p=r[4], small_p=r[5], big_p=r[6],
                            how=r[7] or "tap", how_text=("closed by itself after the last clear" if (r[7] or "") == "auto" else "Close the count -- one tap")))
    except sqlite3.Error:
        pass
    return out


def trail(con, root, limit=200):
    out = []
    try:
        for r in con.execute("SELECT action, after_json, by_whom, at FROM audit_log WHERE table_name=? AND row_id=? ORDER BY id DESC LIMIT ?",
                             (AUDIT_TABLE, int(root), int(limit))):
            a = json.loads(r[1] or "{}")
            out.append(dict(action=r[0], what=a.get("text") or "", by=r[2] or "", at=r[3], at_text=_sa()._r_stamp(r[3]) + " IST"))
    except Exception:                                         # noqa: BLE001
        pass
    return out


def record(con, d, lines=None):
    if lines is None:
        lines, _o, _s = classify(con, d)
    T = totals_of(lines)
    wo = [l for l in lines if l["bucket"] == "written_off"]
    groups = []
    for g, t, b in GROUPS:
        ls = sorted([l for l in wo if l["group"] == g], key=_sortkey)
        if ls:
            groups.append(dict(key=g, title=t, blurb=b, lines=ls, **T["written_off"]["groups"][g]))
    return dict(groups=groups, runs=runs(con, d["count_id"]), closes=closes(con, d["count_id"]), settings_log=settings_log(con),
                trail=trail(con, d["count_id"]), back=sorted([l for l in lines if l["bucket"] == "back"], key=_sortkey),
                sold_after=sorted([l for l in lines if l.get("test")], key=_sortkey))


# ------------------------------------------------------------------ the sales-after-count test (3.4) -- the system's own closing
def _newest_diff_id(con, root, item):
    sa = _sa()
    _r, fam, _R = sa._pad_family(con, root)
    q = ",".join("?" * len(fam))
    r = con.execute("SELECT id FROM stock_diff WHERE item=? AND count_id IN (%s) ORDER BY count_id DESC, id DESC LIMIT 1" % q,
                    (item,) + tuple(fam)).fetchone()
    return int(r[0]) if r else None


def _word(con, root, item, action, note, who, ts, close=False, recovery_state=None):
    """The same two rows /api/pad/decide writes (lane word + the S221 decision), and -- for a closing word --
    the line's status, the way /api/diff/<id>/decision closes it."""
    sa = _sa()
    con.execute("INSERT INTO stock_diff_lane (count_id, item, action, note, by_user, at) VALUES (?,?,?,?,?,?)",
                (root, item, action, note, who, ts))
    did = _newest_diff_id(con, root, item)
    if did and action in sa.DECISIONS:
        con.execute("INSERT INTO stock_diff_decision (diff_id, decision, recover_from, recover_p, recovery_state, note, decided_by, decided_at) "
                    "VALUES (?,?,?,?,?,?,?,?)", (did, action, None, None, recovery_state or ("open" if action == "RECOVER" else "none"), note, who, ts))
        if close:
            con.execute("UPDATE stock_diff SET status='closed', closed_at=? WHERE id=?", (ts, did))
    return did


def sales_test(con, root, d=None, sp=None, who="system"):
    """A line whose sales since the count day exceed counted + bought since: the stock existed, the count was short.
    Closed by the system -- EXPLAINED, cause FOUND, shelf = Marg, audited 'system: sold after count' -- before piling.
    Idempotent: a closed line has a word and is skipped. Returns the items closed on this call; never raises.
    S432: runs inside the cache's full build (a spine rebuild changes the stamp), not on every read."""
    try:
        sa = _sa()
        ensure(con)
        d = d or sa._pad_report_data(con, root)
        if d is None:
            return []
        sp = sp or Spine()
        if not sp.ok:
            return []
        as_on = _as_on_iso(con, root, d)
        upto = dt.date.today().isoformat()
        if not as_on or as_on >= upto:
            return []
        ts, done = now_iso(), []
        for x in d["differences"]:
            rem = int(x["diff"] or 0)
            if rem >= 0 or is_ortho(con, x):
                continue
            act = (x.get("word") or {}).get("action")
            if act in ("WRITE_OFF", "EXPLAINED", "MARG_FIX"):
                continue
            sold = sp.sales(x["item"], as_on, upto, incl_from=False)
            bought = sp.purchases(x["item"], as_on, upto)
            if sold is None:
                continue
            sold_n = sold[0]
            bought_n = max(0.0, bought or 0.0)
            counted = int(x["counted"])
            if sold_n <= counted + bought_n:
                continue
            item, pack, packing = x["item"], int(x.get("pack") or 1), x.get("packing") or ""
            note = "system: sold after count -- %s sold since %s against %s counted + %s bought (S427)" % (
                qw(sold_n, pack, packing, item), sa._r_dmy(as_on), qw(counted, pack, packing, item), qw(bought_n, pack, packing, item))
            did = _word(con, root, item, "EXPLAINED", note, who, ts, close=True)
            if did:
                con.execute("UPDATE stock_diff SET cause='FOUND', cause_note=?, cause_by=?, cause_at=? WHERE id=?", (note, who, ts, did))
            con.execute("INSERT INTO stock_shelf_fix (count_id, item, qty, source, note, by_user, at) VALUES (?,?,?,?,?,?,?)",
                        (root, item, int(x["marg"]), "sales_test", note, who, ts))
            con.execute("INSERT INTO stock_sales_test (count_id, item, at, counted, marg, sold_after, bought_after, as_on, upto, diff_id) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?)", (root, item, ts, counted, int(x["marg"]), sold_n, bought_n, as_on, upto, did))
            _audit(con, root, "sales_test", dict(item=item, diff_id=did, counted=counted, sold_after=sold_n, bought_after=bought_n, marg=x["marg"],
                                                 text="%s closed by the system: %s" % (item, note[8:])), who)
            done.append(item)
        con.commit()
        return done
    except Exception:                                         # noqa: BLE001 -- the test is never worth a broken desk
        try:
            con.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        return []


# ------------------------------------------------------------------ the owner's taps
def _lines_now(con, root):
    """S432: the desk's lines as the CACHE holds them (refreshed as its stamp demands) -- no report, no sales test on a tap."""
    got = cached(con, root)
    if got is None:
        return None, None
    ls, over, _s, _i = got
    return _light_d(con, root), {l["item"]: l for l in ls + over}


def _group_key(l):
    return l["group"] or ("consume" if l["bucket"] == "consume" else ("big" if l["bucket"] == "bigloss" else "small"))


def move(con, root, item, pile, who):
    ok, msg, code, _patch = move_patch(con, root, item, pile, who)
    return ok, msg, code


def move_patch(con, root, item, pile, who):
    """The -> pile menu (and the group list's untick menu): the move recorded, that ONE line recomputed, the patch returned."""
    d, L = _lines_now(con, root)
    if d is None:
        return False, "No such count.", 404, None
    l = L.get(item)
    if not l:
        return False, "That line is not on the desk (orthotics stay on their own section).", 400, None
    if pile not in MOVE_PILE and pile != "auto":
        return False, "Choose one of the piles (or owner's use).", 400, None
    if l["bucket"] in ("back", "written_off"):
        return False, "That line is already closed.", 409, None
    if l["bucket"] == "over":
        return False, "A line with more on the shelf is never a loss -- Darpan may count it again on his Stock milaan.", 400, None
    target_title = dict(MOVE_TARGETS)
    if l.get("moved") and (l["moved"].get("target") or l["moved"]["pile"]) == pile:
        return True, "Already in %s." % target_title[pile], 200, patch_of(con, root, {item: l}, [item])
    ts = now_iso()
    con.execute("INSERT INTO stock_pile_move (count_id, item, pile, by_user, at) VALUES (?,?,?,?,?)", (root, item, pile, who, ts))
    _audit(con, root, "move", dict(item=item, pile=pile, was=l.get("pile") or l["bucket"],
                                   text="%s moved %s -> %s" % (item, PILE_TITLE.get(l.get("pile") or "", l["bucket"]),
                                                               target_title.get(pile, "the system's suggestion"))), who)
    con.commit()
    new = _refresh_after_write(con, root, [item])
    return True, "%s moved to %s." % (item, target_title.get(pile, "the system's suggestion")), 200, patch_of(con, root, new, [item])


def _refresh_after_write(con, root, items):
    """After a tap wrote its rows: the named lines recomputed and the stamp brought up to date (so the next read is a plain read)."""
    new = refresh_items(con, root, list(items))
    con.execute("UPDATE stock_pile_cache_meta SET stamp=?, last_partial_at=?, last_partial_n=?, last_partial_ms=? WHERE count_id=?",
                (json.dumps(stamp(con, root), sort_keys=True), now_iso(), len(new), 0, int(root)))
    con.commit()
    return new


def accept(con, root, items, who):
    ok, msg, code, n, _patch = accept_patch(con, root, items, who)
    return ok, msg, code, n


def accept_patch(con, root, items, who):
    """Accept back: EXPLAINED, cause FOUND, status closed, shelf corrected to Marg's, audited. Only a line that is in
    the With-me pile now; a repeat finds it closed and writes nothing. Returns the patch too (S432)."""
    d, L = _lines_now(con, root)
    if d is None:
        return False, "No such count.", 404, 0, None
    ts, done, skipped = now_iso(), [], []
    for item in items:
        l = L.get(item)
        if not l or l["bucket"] != "with_me":
            skipped.append(item)
            continue
        did = _word(con, root, item, "EXPLAINED", "owner: back in store", who, ts, close=True)
        if did:
            con.execute("UPDATE stock_diff SET cause='FOUND', cause_note=?, cause_by=?, cause_at=? WHERE id=?",
                        ("owner: back in store -- kept elsewhere, turned up (S418)", who, ts, did))
        con.execute("INSERT INTO stock_shelf_fix (count_id, item, qty, source, note, by_user, at) VALUES (?,?,?,?,?,?,?)",
                    (root, item, int(l["marg"]), "accept_back", "owner: back in store", who, ts))
        _audit(con, root, "accept_back", dict(item=item, diff_id=did, marg=l["marg"], counted=l["counted"], mrp_p=l["mrp_p"],
                                              text="%s accepted back -- %s short at the count, shelf corrected to Marg's %s" % (item, l["short_day_text"] or l["short_text"], l["marg_text"])), who)
        done.append(item)
    con.commit()
    if not done:
        return True, ("Already closed -- nothing written." if skipped else "Nothing to accept."), 200, 0, patch_of(con, root, {i: L.get(i) for i in items}, list(items))
    new = _refresh_after_write(con, root, done)
    return True, "Accepted back: %s." % ", ".join(done), 200, len(done), patch_of(con, root, new, done)


def _pile_items(con, root, key):
    d, L = _lines_now(con, root)
    if d is None:
        return None, None, []
    keys = (key,) if isinstance(key, str) else tuple(key)
    return d, L, sorted(i for i, l in L.items() if l.get("bucket") in keys)


CLOSE_PILES = ("writeoff", "bigloss", "consume")
CLEAR_GROUPS = ("allowance", "small", "old", "big", "consume", "owner_use", "all")


def _arm(con, root, who, keys, what, items=None, group=None):
    d, L, all_items = _pile_items(con, root, keys)
    if d is None:
        return False, "No such count.", 404, None
    if items is None:
        items = all_items
    if not items:
        return False, "Nothing to %s -- the piles are empty." % what, 400, None
    # S432: the token is unique per tap (a random salt) -- two arms of the same lines within one second used to share a token, and
    # the confirm then found the OLDER row (seen in the walk: 'More than 10 seconds passed' on a fresh arm)
    token = hashlib.md5(("%s|%s|%s|%s|%s|%s" % (root, now_iso(), what, group or "", json.dumps(items), os.urandom(8).hex())).encode("utf-8")).hexdigest()[:16]
    con.execute("INSERT INTO stock_pile_arm (count_id, token, items, by_user, at) VALUES (?,?,?,?,?)",
                (root, token, json.dumps(dict(items=items, group=group) if group else items), who, now_iso()))
    con.commit()
    mrp = sum((L[i]["mrp_p"] or 0) for i in items)
    return True, "Tap again within %d seconds: %s %d lines, %s at MRP." % (ARM_SECONDS, what, len(items), _rs(mrp)), 200, \
        dict(token=token, n=len(items), mrp_p=mrp, seconds=ARM_SECONDS, group=group)


def arm(con, root, who):
    """S418's door: the write-off pile alone."""
    return _arm(con, root, who, ("writeoff",), "write off")


def arm_close(con, root, who):
    """S427: 'Close the count' -- piles 2, 3 and 4 together."""
    return _arm(con, root, who, CLOSE_PILES, "close the count and write off")


def arm_clear(con, root, who, group, items):
    """S432 (3.2): 'Clear this group (N ticked)' -- the ticked lines of ONE group, armed for the 10-second confirm. Every ticked
    line must be open in that group now (With-me lines are never in a group list); nothing ticked is refused."""
    if group not in CLEAR_GROUPS:
        return False, "Choose a group (within allowance, small real gap, old stock, big losses, clinic consumption, owner's use) or all.", 400, None
    d, L, all_items = _pile_items(con, root, CLOSE_PILES)
    if d is None:
        return False, "No such count.", 404, None
    want = sorted({str(i).strip() for i in (items or []) if str(i or "").strip()})
    if not want:
        return False, "Nothing ticked -- tick the lines to clear first.", 400, None
    bad = [i for i in want if i not in all_items or (group != "all" and _group_key(L[i]) != group)]
    if bad:
        return False, "%s %s not open in this group any more -- look again." % (", ".join(bad[:4]), "is" if len(bad) == 1 else "are"), 409, None
    title = "All groups" if group == "all" else GROUP_TITLE.get(group, group)
    return _arm(con, root, who, CLOSE_PILES, "clear %s and write off" % title.lower(), items=want, group=group)


def _armed(raw):
    v = json.loads(raw)
    if isinstance(v, dict):
        return sorted(v.get("items") or []), v.get("group")
    return v, None


def _run(con, root, token, who, keys, what, clear=False):
    """The second tap. The lines must be what they were when armed, within ARM_SECONDS. Every line -> WRITE_OFF
    (closed), ONE documented run frozen with its groups (kind: close | clear:<group> | pile), the Marg voucher round for
    exactly those lines in the same call (rounds of <= stock.voucher_batch), and -- for a close, or for the LAST clear --
    THE STAFF BLOCK frozen from the union of the runs since the previous block."""
    sa = _sa()
    r = con.execute("SELECT id, items, at, used_at FROM stock_pile_arm WHERE count_id=? AND token=? ORDER BY id DESC LIMIT 1", (root, str(token or ""))).fetchone()   # S432: the newest arm of this token
    if not r:
        return False, "Tap '%s' first." % what, 400, None
    if r[3]:
        return True, "Already done -- nothing written twice.", 200, dict(lines=0, round_no=None)
    try:
        age = (dt.datetime.now() - dt.datetime.fromisoformat(str(r[2])[:19])).total_seconds()
    except ValueError:
        age = 999
    if age > ARM_SECONDS:
        return False, "More than %d seconds passed -- tap '%s' again." % (ARM_SECONDS, what), 409, None
    armed, group = _armed(r[1])
    d, L, all_items = _pile_items(con, root, keys)
    if clear:
        if group not in CLEAR_GROUPS or any(i not in all_items or (group != "all" and _group_key(L[i]) != group) for i in armed):
            return False, "The lines changed since you tapped -- look again and tap once more.", 409, None
        items = armed
        kind = "clear:%s" % group
    else:
        items = all_items
        if items != armed:
            return False, "The lines changed since you tapped -- look again and tap once more.", 409, None
        kind = "close" if len(keys) > 1 else "pile"
    S = settings(con)
    RC = None
    if len(keys) > 1 and not clear:                           # S437 (F-659): a tap close puts the shelf-more lines on STOCK RECEIVE vouchers FIRST, so the
        try:                                                  # close's own run stays the newest row (the record, the walks and the hub read it so)
            RC = receive_close(con, root, who, d)
        except Exception:                                     # noqa: BLE001 -- the close stands; the rule runs again at the next close
            RC = None
    ts = now_iso()
    con.execute("UPDATE stock_pile_arm SET used_at=? WHERE id=?", (ts, r[0]))
    groups, big_lines = {}, []
    for item in items:
        l = L[item]
        g = _group_key(l)
        note = "owner: %s -- %s" % (("cleared as a group" if clear else ("the count closed" if len(keys) > 1 else "written off with the pile")), GROUP_TITLE.get(g, g)) \
            + (" (clinic consumption)" if g == "consume" else "")
        _word(con, root, item, "WRITE_OFF", note, who, ts, close=True)
        groups.setdefault(g, []).append(dict(item=item, short_units=l["short_units"], short_text=l["short_text"], short_hi=l["short_hi"],
                                             pack=l["pack"], packing=l["packing"], mrp_p=l["mrp_p"], cost_p=l["cost_p"], why=l["why"]))
        if l["bucket"] == "bigloss":
            big_lines.append(l)
    lines_n = len(items)
    mrp = sum(x["mrp_p"] or 0 for v in groups.values() for x in v)
    cost = sum(x["cost_p"] or 0 for v in groups.values() for x in v)
    unpriced = sum(1 for v in groups.values() for x in v if x["mrp_p"] is None)
    frozen = json.dumps(groups, sort_keys=True, separators=(",", ":"))
    rules = dict(allowance_pct=S["allowance_pct"], allowance_min_strips=S["allowance_min_strips"], small_gap_ceiling_p=S["small_gap_ceiling_p"],
                 big_loss_floor_p=S["big_loss_floor_p"], slow_months=S["slow_months"], slow_floor_p=S["slow_floor_p"],
                 consume_items=S["consume_items"], voucher_batch=S["voucher_batch"], kit=KIT)
    cur = con.execute("INSERT INTO stock_writeoff_run (count_id, at, by_user, lines_n, mrp_p, cost_p, unpriced, groups, settings, md5, kind) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (root, ts, who, lines_n, mrp, cost, unpriced, frozen, json.dumps(rules, sort_keys=True),
                                                           hashlib.md5(frozen.encode("utf-8")).hexdigest(), kind))
    run_id = int(cur.lastrowid)
    title = ("All groups" if group == "all" else GROUP_TITLE.get(group, group)) if clear else ""
    _audit(con, root, "clear" if clear else ("close" if len(keys) > 1 else "writeoff_pile"),
           dict(run=run_id, lines=lines_n, mrp_p=mrp, groups={k: len(v) for k, v in groups.items()}, kind=kind,
                text="%s: %d lines, %s at MRP (%s)" % (("cleared the group %s" % title) if clear else ("closed the count" if len(keys) > 1 else "wrote off the pile"), lines_n, _rs(mrp),
                                                       ", ".join("%s %d" % (GROUP_TITLE.get(k, k), len(v)) for k, v in sorted(groups.items())))), who)
    con.commit()
    new = _refresh_after_write(con, root, items)
    block_id, auto_closed = None, False
    if len(keys) > 1 and not clear:
        block_id = _freeze_block(con, root, run_id, d, _union_groups(con, root, groups, run_id), S, who, ts, how="tap")
    elif clear:
        left = [i for i, l in _cache_rows_by_item(con, root).items() if l["bucket"] in CLOSE_PILES]
        if not left:                                          # THE LAST CLEAR closes the count by itself
            block_id = _freeze_block(con, root, run_id, d, _union_groups(con, root, groups, run_id), S, who, ts, how="auto")
            auto_closed = True
            _audit(con, root, "auto_close", dict(run=run_id, block=block_id, text="the count closed by itself after the last clear -- one staff block frozen from every clear since the previous block"), who)
    con.commit()
    d2 = sa._pad_report_data(con, root)
    if con.in_transaction:
        con.commit()
    # S430: the owner's-use lines get their own Marg round ("Owner's use" on Amir's board), then the rest
    ou = set(x["item"] for x in groups.get("owner_use", []))
    rno_ou, nv_ou = (sa._voucher_make(con, d2, dict(user=who), items=ou) if ou else (None, 0))
    if rno_ou:
        _audit(con, root, "vouchers", dict(round_no=rno_ou, lines=nv_ou, owner_use=True, text="Marg voucher round %d made for the owner's use: %d lines" % (rno_ou, nv_ou)), who)
        con.commit()
    rno, nv = sa._voucher_make(con, d2, dict(user=who), items=set(items) - ou)
    if rno:
        con.execute("UPDATE stock_writeoff_run SET round_no=? WHERE id=?", (rno, run_id))
        _audit(con, root, "vouchers", dict(round_no=rno, lines=nv, text="Marg voucher round %d made: %d lines, at most %d a voucher" % (rno, nv, S["voucher_batch"])), who)
        con.commit()
    elif rno_ou:
        con.execute("UPDATE stock_writeoff_run SET round_no=? WHERE id=?", (rno_ou, run_id))
        con.commit()
    if auto_closed and RC is None:                            # S437 (F-659): the last clear closed the count -- the shelf-more lines go on STOCK RECEIVE vouchers now
        try:
            RC = receive_close(con, root, who, d2)
        except Exception:                                     # noqa: BLE001 -- the close stands; the rule runs again at the next close
            RC = None
    head = ("Cleared -- %s" % title) if clear else ("The count is closed" if len(keys) > 1 else "Written off")
    if auto_closed:
        head += ". Nothing open is left outside With me: the count is closed"
    return True, "%s: %d lines, %s at MRP. %s%s%s" % (head, lines_n, _rs(mrp),
                                                      ("Amir's vouchers: round %d, %d lines." % (rno, nv)) if rno else "No Marg voucher was needed.",
                                                      (" Owner's use: round %d, %d lines." % (rno_ou, nv_ou)) if rno_ou else "",
                                                      (" STOCK RECEIVE by rule: round %d, %d lines where the shelf held more than Marg." % (RC["round_no"], RC["lines"])) if RC and RC.get("round_no") else ""), 200, \
        dict(lines=lines_n, mrp_p=mrp, round_no=rno, voucher_lines=nv, run=run_id, block=block_id, owner_use_round=rno_ou, owner_use_lines=nv_ou,
             receive_round=(RC or {}).get("round_no"), receive_lines=(RC or {}).get("lines", 0),
             kind=kind, group=group, items=items, auto_closed=auto_closed, big_lines=big_lines, patch=patch_of(con, root, new, items))


def _cache_rows_by_item(con, root):
    ls, over, _s = _cache_rows(con, root)
    return {l["item"]: l for l in ls + over}


def _union_groups(con, root, groups_now, run_id):
    """S432: the block is frozen from the UNION of the runs since the previous block -- every clear before this one, and this
    run's own groups (one block, the S427 wording)."""
    last = con.execute("SELECT COALESCE(MAX(run_id),0) FROM stock_staff_block WHERE count_id=?", (int(root),)).fetchone()[0] or 0
    out = {k: list(v) for k, v in groups_now.items()}
    for r in con.execute("SELECT id, groups FROM stock_writeoff_run WHERE count_id=? AND id>? AND id<>? AND COALESCE(kind,'') NOT IN (?,?) ORDER BY id",
                         (int(root), int(last), int(run_id)) + NON_BLOCK_KINDS):                 # S436 / S437: the orthotic and the receive runs are never in a medicine block
        try:
            g = json.loads(r[1])
        except ValueError:
            continue
        for k, v in g.items():
            out.setdefault(k, []).extend(v)
    return out


def writeoff(con, root, token, who):
    """S418's second tap (the write-off pile alone)."""
    return _run(con, root, token, who, ("writeoff",), "Write off this pile")


def close(con, root, token, who):
    """S427: the second tap of 'Close the count'."""
    return _run(con, root, token, who, CLOSE_PILES, "Close the count")


def clear(con, root, token, who):
    """S432: the second tap of 'Clear this group (N ticked)'."""
    return _run(con, root, token, who, CLOSE_PILES, "Clear this group", clear=True)


# ------------------------------------------------------------------ THE STAFF BLOCK (3.5)
def _block_numbers(groups, S, day):
    big = sorted(groups.get("big", []), key=lambda x: (-(x["mrp_p"] or 0), x["item"]))
    small_p = sum((x["mrp_p"] or 0) for g in ("allowance", "small") for x in groups.get(g, []))
    big_p = sum((x["mrp_p"] or 0) for x in big)
    cons_p = sum((x["mrp_p"] or 0) for x in groups.get("consume", []))
    return dict(day=day, total_p=small_p + big_p, small_p=small_p, big_p=big_p, consume_p=cons_p,
                big_lines=[dict(item=x["item"], short_units=x["short_units"], pack=x["pack"], packing=x.get("packing") or "", mrp_p=x["mrp_p"]) for x in big],
                top_n=S["staff_block_items"])


def _freeze_block(con, root, run_id, d, groups, S, who, ts, how="tap"):
    B = _block_numbers(groups, S, d.get("day") or "")
    cur = con.execute("INSERT INTO stock_staff_block (count_id, run_id, at, day, total_p, small_p, big_p, consume_p, big_lines, top_n, by_user, how) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (root, run_id, ts, B["day"], B["total_p"], B["small_p"], B["big_p"], B["consume_p"],
                                                            json.dumps(B["big_lines"], separators=(",", ":")), B["top_n"], who, how))
    bid = int(cur.lastrowid)
    _audit(con, root, "staff_block", dict(block=bid, run=run_id, how=how, total_p=B["total_p"], small_p=B["small_p"], big_p=B["big_p"], big_n=len(B["big_lines"]),
                                          text="staff block frozen%s: total %s, small %s, big %s (%d named)" % (" (the count closed by itself after the last clear)" if how == "auto" else "",
                                                                                                                _rs(B["total_p"]), _rs(B["small_p"]), _rs(B["big_p"]), len(B["big_lines"]))), who)
    return bid


def ortho_loss_of(con, root):
    """S436: the orthotic section's close-by-rule run of this count (stockmatch), for the block's foot line -- None before it."""
    try:
        r = con.execute("SELECT id, at, mrp_p, unpriced, groups, round_no FROM stock_writeoff_run WHERE count_id=? AND kind=? ORDER BY id DESC LIMIT 1",
                        (int(root), ORTHO_RUN_KIND)).fetchone()
    except sqlite3.Error:
        return None
    if not r:
        return None
    try:
        g = json.loads(r[4])
    except ValueError:
        return None
    n = len(g.get("ortho_loss", []))
    return dict(run_id=r[0], at=r[1], mrp_p=int(r[2] or 0), unpriced=int(r[3] or 0), n=n, round_no=r[5],
                items=[x["item"] for x in g.get("ortho_loss", [])])


def _block_lines(B, lang):
    """The three lines of the block from its frozen numbers -- Hindi for Darpan, English for the owner.
    S436: a FOURTH line at the foot when the orthotic section is closed -- the orthotic loss, separate, never in the first three."""
    top = B["big_lines"][:B["top_n"]]
    rest = len(B["big_lines"]) - len(top)
    names = " · ".join("%s %s" % (x["item"], qw(x["short_units"], x["pack"], x.get("packing") or "", x["item"], lang)) for x in top)
    if lang == "hi":
        l1 = "Ginti %s · kul kami %s" % (B["day"], _rs(B["total_p"]))
        l2 = "Chhoti kami, likh di gayi: %s" % _rs(B["small_p"])
        l3 = ("Badi kami — %s: %s%s" % (_rs(B["big_p"]), names, (" · aur %d" % rest) if rest > 0 else "")) if B["big_lines"] else "Badi kami: koi nahi"
    else:
        l1 = "Count of %s · total loss %s" % (B["day"], _rs(B["total_p"]))
        l2 = "Small losses, written off: %s" % _rs(B["small_p"])
        l3 = ("Big losses — %s: %s%s" % (_rs(B["big_p"]), names, (" · and %d more" % rest) if rest > 0 else "")) if B["big_lines"] else "Big losses: none"
    out = [l1, l2, l3]
    O = B.get("ortho")
    if O and O.get("n"):
        if lang == "hi":
            out.append("Orthotics — %s (%d line, bina bill)%s" % (_rs(O["mrp_p"]), O["n"], (" · %d bina daam" % O["unpriced"]) if O.get("unpriced") else ""))
        else:
            out.append("Orthotics — %s (%d line%s, bina bill)%s" % (_rs(O["mrp_p"]), O["n"], "" if O["n"] == 1 else "s", (" · %d without a price" % O["unpriced"]) if O.get("unpriced") else ""))
    return out


def block_view(con, root, lang="en"):
    """The frozen block of this count (the newest close), with its notes -- None before the close."""
    try:
        ensure(con)
        r = con.execute("SELECT id, run_id, at, day, total_p, small_p, big_p, consume_p, big_lines, top_n, by_user, how FROM stock_staff_block "
                        "WHERE count_id=? ORDER BY id DESC LIMIT 1", (int(root),)).fetchone()
    except sqlite3.Error:
        return None
    if not r:
        return None
    B = dict(id=r[0], run_id=r[1], at=r[2], at_text=_sa()._r_stamp(r[2]) + " IST", day=r[3], total_p=r[4], small_p=r[5], big_p=r[6], consume_p=r[7],
             big_lines=json.loads(r[8]), top_n=int(r[9] or 20), by=r[10] or "", count_id=int(root), how=r[11] or "tap",
             how_text=("closed by itself after the last clear" if (r[11] or "") == "auto" else "Close the count -- one tap"))
    for x in B["big_lines"]:
        x["qty_text"] = qw(x["short_units"], x["pack"], x.get("packing") or "", x["item"])
        x["qty_hi"] = qw(x["short_units"], x["pack"], x.get("packing") or "", x["item"], "hi")
    B["ortho"] = ortho_loss_of(con, root)                      # S436: the orthotic foot line, read live (the section closes after the block)
    B["lines_hi"] = _block_lines(B, "hi")
    B["lines_en"] = _block_lines(B, "en")
    B["notes"] = [dict(id=n[0], text=n[1], by=n[2], at=n[3], at_text=_sa()._r_stamp(n[3]) + " IST")
                  for n in con.execute("SELECT id, text, by_user, at FROM stock_staff_note WHERE block_id=? ORDER BY id", (B["id"],))]
    try:
        B["tables"] = block_tables(con, root, B)              # S437: the block as tables (from the frozen runs behind it)
    except Exception:                                         # noqa: BLE001
        B["tables"] = None
    return B


def block_preview(con, d, S=None, lines=None):
    """What the block WOULD say if the count were closed now -- the desk shows it above the button."""
    S = S or settings(con)
    if lines is None:
        lines, _o, _s = classify(con, d, S)
    groups = {}
    for l in lines:
        if l["bucket"] in CLOSE_PILES:
            groups.setdefault(_group_key(l), []).append(l)
    try:                                                      # S432: the groups already cleared since the last block are in the block too
        groups = _union_groups(con, d["count_id"], groups, 0)
        cleared = sum(1 for r in con.execute("SELECT id FROM stock_writeoff_run WHERE count_id=? AND id>(SELECT COALESCE(MAX(run_id),0) FROM stock_staff_block WHERE count_id=?) AND COALESCE(kind,'') NOT IN (?,?)",
                                             (int(d["count_id"]), int(d["count_id"])) + NON_BLOCK_KINDS))
    except sqlite3.Error:
        cleared = 0
    B = _block_numbers(groups, S, d.get("day") or "")
    B["ortho"] = ortho_loss_of(con, d["count_id"])            # S436
    B["lines_hi"], B["lines_en"] = _block_lines(B, "hi"), _block_lines(B, "en")
    B["big_n"] = len(B["big_lines"])
    B["cleared_runs"] = cleared
    B["tables"] = block_tables(con, d["count_id"], B, groups)   # S437: the same rows the frozen block will show
    return B


# ------------------------------------------------------------------ S437 (F-659): THE BLOCK AS TABLES, THE RECEIVE ROUND BY RULE
def _count_figures(con, root):
    """item -> (Marg on the count day, counted) for the block's rows: the classified lines first (the cache), else the count sheet."""
    out = {}
    try:
        for it, l in _cache_rows_by_item(con, root).items():
            if l.get("marg") is not None and l.get("counted") is not None:
                out[it] = (int(l["marg"]), int(l["counted"]))
    except Exception:                                         # noqa: BLE001
        pass
    fam = [int(root)] + [r[0] for r in con.execute("SELECT count_id FROM stock_count_part WHERE part_of=?", (int(root),))]
    for r in con.execute("SELECT item, marg_qty, counted_qty FROM stock_count_item WHERE count_id IN (%s) ORDER BY count_id, id" % ",".join("?" * len(fam)), tuple(fam)):
        out.setdefault(r[0], (int(r[1] or 0), int(r[2] or 0)))
    return out


def _table_row(x, fig, lang_pack=None):
    item, units, pack, packing, mrp = x["item"], int(x.get("short_units") or 0), int(x.get("pack") or 1), x.get("packing") or "", x.get("mrp_p")
    marg, counted = fig.get(item, (None, None))
    return dict(item=item, pack=pack, packing=packing, marg=marg, counted=counted, short_units=units,
                marg_text=(qw(marg, pack, packing, item) if marg is not None else "-"), marg_hi=(qw(marg, pack, packing, item, "hi") if marg is not None else "-"),
                counted_text=(qw(counted, pack, packing, item) if counted is not None else "-"), counted_hi=(qw(counted, pack, packing, item, "hi") if counted is not None else "-"),
                short_text=qw(units, pack, packing, item), short_hi=qw(units, pack, packing, item, "hi"),
                mrp_p=mrp, rs=(_rs(mrp) if mrp is not None else "-"), price_src=x.get("price_src"))


def block_tables(con, root, B, groups=None):
    """The block's rows (S437): kul; badi (the big losses, largest first); chhoti (allowance + small, collapsed on the pages);
    ortho (the orthotic loss rows, apart). From the frozen runs behind the block when `groups` is not given (block_view), from
    the groups at hand for a preview. Every quantity through qty_words; the totals at MRP equal the block's figures."""
    root = int(root)
    if groups is None:
        groups = {}
        try:
            prev = con.execute("SELECT COALESCE(MAX(run_id),0) FROM stock_staff_block WHERE count_id=? AND id<?", (root, int(B.get("id") or 0))).fetchone()[0] or 0
            for r in con.execute("SELECT id, groups FROM stock_writeoff_run WHERE count_id=? AND id>? AND id<=? AND COALESCE(kind,'') NOT IN (?,?) ORDER BY id",
                                 (root, int(prev), int(B.get("run_id") or 0)) + NON_BLOCK_KINDS):
                try:
                    g = json.loads(r[1])
                except ValueError:
                    continue
                for k, v in g.items():
                    groups.setdefault(k, []).extend(v)
        except sqlite3.Error:
            groups = {}
    fig = _count_figures(con, root)
    big = sorted(groups.get("big", []), key=lambda x: (-(x.get("mrp_p") or 0), x["item"]))
    small = sorted([x for g in ("allowance", "small") for x in groups.get(g, [])], key=lambda x: (-(x.get("mrp_p") or 0), x["item"]))
    badi = [_table_row(x, fig) for x in big]
    chhoti = [_table_row(x, fig) for x in small]
    ortho_rows, O = [], (B.get("ortho") or ortho_loss_of(con, root) or {})
    try:
        r = con.execute("SELECT groups FROM stock_writeoff_run WHERE id=?", (int(O.get("run_id") or 0),)).fetchone() if O.get("run_id") else None
        if r:
            og = json.loads(r[0]).get("ortho_loss", [])
            ortho_rows = [_table_row(x, fig) for x in sorted(og, key=lambda x: (-(x.get("mrp_p") or 0), x["item"]))]
    except (sqlite3.Error, ValueError):
        ortho_rows = []
    T = dict(day=B.get("day") or "",
             kul=dict(p=B.get("total_p") or 0, rs=_rs(B.get("total_p") or 0),
                      hi="Ginti %s · kul kami %s" % (B.get("day") or "", _rs(B.get("total_p") or 0)),
                      en="Count of %s · total loss %s" % (B.get("day") or "", _rs(B.get("total_p") or 0))),
             badi=dict(rows=badi, n=len(badi), total_p=sum(r_["mrp_p"] or 0 for r_ in badi), rs=_rs(sum(r_["mrp_p"] or 0 for r_ in badi)),
                       hi="Badi kami — %s" % _rs(B.get("big_p") or 0), en="Big losses — %s" % _rs(B.get("big_p") or 0)),
             chhoti=dict(rows=chhoti, n=len(chhoti), total_p=sum(r_["mrp_p"] or 0 for r_ in chhoti), rs=_rs(sum(r_["mrp_p"] or 0 for r_ in chhoti)),
                         hi="Chhoti kami, likh di gayi — %s" % _rs(B.get("small_p") or 0), en="Small losses, written off — %s" % _rs(B.get("small_p") or 0)),
             ortho=dict(rows=ortho_rows, n=int(O.get("n") or 0), total_p=int(O.get("mrp_p") or 0), rs=_rs(int(O.get("mrp_p") or 0)), unpriced=int(O.get("unpriced") or 0),
                        round_no=O.get("round_no"),
                        hi=("Orthotics band ho gaya — kami %s (%d line, bina bill)%s" % (_rs(O["mrp_p"]), O["n"], (" · %d bina daam" % O["unpriced"]) if O.get("unpriced") else "")) if O.get("n") else "",
                        en=("Orthotics closed — loss %s (%d line%s, bina bill)%s" % (_rs(O["mrp_p"]), O["n"], "" if O["n"] == 1 else "s", (" · %d without a price" % O["unpriced"]) if O.get("unpriced") else "")) if O.get("n") else ""),
             headers=dict(hi=["Item", "Marg (ginti ke din)", "Gina", "Kami", "Rs"], en=["Item", "Marg (count day)", "Counted", "Short", "Rs"]))
    return T


def receive_close(con, root, who, d=None, all_pending=False):
    """S437 (F-659): the STOCK RECEIVE round by rule. Every pending line where the shelf holds MORE than Marg after the swaps -- the
    over-on-shelf lines and the Marg-negative book corrections (kind RECEIVE in _voucher_pending) -- goes on Amir's vouchers now, in
    ONE run of kind 'receive_close' (group 'receive'; never a loss, never leakage, never in a block). With all_pending=True (the
    install for count #1) the pending ISSUE lines ride the same round (group 'issue_earlier': the lines written off before the
    piles that were on no voucher). Idempotent: nothing pending -> None. Returns dict(run, round_no, lines, receive, issue)."""
    sa = _sa()
    root = int(root)
    ensure(con)
    d = d or sa._pad_report_data(con, root)
    if d is None:
        return None
    ts = now_iso()
    # a shelf-more line the maker does not carry (no word at all, or a word that makes no voucher -- the owner's PARKED of 06-Sep) is still
    # Marg to be corrected up to the shelf -- the rule gives it its word (EXPLAINED: no loss) so the maker carries it; the orthotic section
    # keeps its own words (stockmatch)
    worded = []
    carried = {p["item"] for p in sa._voucher_pending(con, d)} | set(sa._voucher_frozen(con, root).keys())
    for x in d["differences"]:
        try:
            if sa._item_section(con, x) == "Orthotics" or x["item"] in carried:
                continue
            diff, marg, sw = int(x.get("diff") or 0), int(x.get("marg") or 0), int(x.get("swapped") or 0)
            after = (diff - sw) if diff > 0 else diff
            if after > 0 or marg < 0:
                _word(con, root, x["item"], "EXPLAINED", "%s: the shelf held more than Marg -- Marg corrected up to the shelf, never a loss" % who, who, ts)
                worded.append(x["item"])
        except Exception:                                     # noqa: BLE001 -- a line the report cannot read stays as it is
            continue
    if worded:
        con.commit()
        d = sa._pad_report_data(con, root)
    pend = sa._voucher_pending(con, d)
    recv = [p for p in pend if p["kind"] == "RECEIVE"]
    iss = [p for p in pend if p["kind"] == "ISSUE"] if all_pending else []
    if not recv and not iss:
        return None

    def row(p):
        units = abs(int(p["change"]))
        return dict(item=p["item"], short_units=0, over_units=units, pack=int(p.get("pack") or 1), packing=p.get("packing") or "",
                    short_text="", short_hi="", over_text=qw(units, p.get("pack") or 1, p.get("packing") or "", p["item"]),
                    over_hi=qw(units, p.get("pack") or 1, p.get("packing") or "", p["item"], "hi"),
                    marg_from=p["marg_from"], marg_to=p["marg_to"], change=int(p["change"]), mrp_p=0, cost_p=0,
                    why=("Marg corrected up to the shelf -- " + (p.get("reason") or "")) if p["kind"] == "RECEIVE" else ("written off earlier, on no voucher -- " + (p.get("reason") or "")))
    groups = {}
    if recv:
        groups["receive"] = [row(p) for p in recv]
    if iss:
        groups["issue_earlier"] = [dict(row(p), short_units=abs(int(p["change"])), over_units=0,
                                        short_text=qw(abs(int(p["change"])), p.get("pack") or 1, p.get("packing") or "", p["item"]),
                                        short_hi=qw(abs(int(p["change"])), p.get("pack") or 1, p.get("packing") or "", p["item"], "hi"), over_text="", over_hi="") for p in iss]
    frozen = json.dumps(groups, sort_keys=True, separators=(",", ":"))
    cur = con.execute("INSERT INTO stock_writeoff_run (count_id, at, by_user, lines_n, mrp_p, cost_p, unpriced, groups, settings, md5, kind) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (root, ts, who, len(recv) + len(iss), 0, 0, 0, frozen, json.dumps(dict(kit=KIT, rule="F-659", voucher_batch=settings(con)["voucher_batch"]), sort_keys=True),
                       hashlib.md5(frozen.encode("utf-8")).hexdigest(), RECEIVE_RUN_KIND))
    run_id = int(cur.lastrowid)
    con.commit()
    items = {p["item"] for p in recv + iss}
    rno, n = sa._voucher_make(con, d, dict(user=who), items=items)
    if rno:
        con.execute("UPDATE stock_writeoff_run SET round_no=? WHERE id=?", (rno, run_id))
    _audit(con, root, "receive_close", dict(run=run_id, round_no=rno, lines=n, receive=len(recv), issue_earlier=len(iss), worded_by_rule=worded,
                                            text="STOCK RECEIVE by rule: %d line%s where the shelf held more than Marg (%d of them worded by the rule)%s -- Marg voucher round %s (%d lines); never a loss" % (
                                                len(recv), "" if len(recv) == 1 else "s", len(worded), (", and %d earlier write-off%s on no voucher (STOCK ISSUE)" % (len(iss), "" if len(iss) == 1 else "s")) if iss else "",
                                                rno or "-", n)), who)
    con.commit()
    return dict(run=run_id, round_no=rno, lines=n, receive=len(recv), issue=len(iss), worded=worded)


def add_note(con, root, text, who):
    """'Kuchh batana hai?' -- free text under the pinned block, stored, shown on the owner's record card."""
    B = block_view(con, root)
    if not B:
        return False, "Abhi koi ginti band nahi hui.", 404
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    if not t:
        return False, "Kuchh likhiye.", 400
    if len(t) > 500:
        t = t[:500]
    ts = now_iso()
    con.execute("INSERT INTO stock_staff_note (block_id, count_id, text, by_user, at) VALUES (?,?,?,?,?)", (B["id"], root, t, who, ts))
    _audit(con, root, "staff_note", dict(block=B["id"], by=who, text="%s wrote under the staff block: %s" % (who, t[:120])), who)
    con.commit()
    return True, "Likh liya. Doctor sahab dekh lenge.", 200


# ------------------------------------------------------------------ Darpan's side (Stock milaan): Dobara ginna hai
def round_items(con, root):
    """{item: (pack, packing)} -- every item of the round's differences (the desk's lines and the over note)."""
    sa = _sa()
    out = {}
    try:
        _r, fam, _R = sa._pad_family(con, root)
        q = ",".join("?" * len(fam))
        as_on = con.execute("SELECT marg_as_on FROM stock_count WHERE id=?", (int(root),)).fetchone()[0]
        packs = {r[0]: (int(r[1] or 1), r[2] or "") for r in con.execute("SELECT item, pack_size, packing FROM stock_snapshot WHERE as_on=?", (as_on,))}
        for r in con.execute("SELECT DISTINCT item, pack_size FROM stock_diff WHERE count_id IN (%s)" % q, tuple(fam)):
            p = packs.get(r[0]) or (int(r[1] or 1), "")
            out[r[0]] = p
    except Exception:                                         # noqa: BLE001
        pass
    return out


def round_item(con, root, item):
    """dict(item, pack, packing) when the item is a line of this round, else None."""
    p = round_items(con, root).get(item)
    return dict(item=item, pack=p[0], packing=p[1]) if p else None


def items_search(con, root, q, limit=12):
    """Darpan's search box: the round's items whose name carries every word typed."""
    words = [w for w in re.sub(r"[^A-Z0-9 ]+", " ", str(q or "").upper()).split() if w]
    if not words:
        return []
    out = []
    for item, (pack, packing) in sorted(round_items(con, root).items()):
        u = re.sub(r"[^A-Z0-9 ]+", " ", item.upper())
        if all(w in u for w in words):
            out.append(dict(item=item, pack=pack, packing=packing, whole=_qwm().whole_word(packing, None, item, pack, "hi")))
            if len(out) >= limit:
                break
    return out


def recounts_by(con, root):
    """Every recount Darpan gave on this round (the newest per item) -- 'Aapne gina', with his figure in his words."""
    ensure(con)
    sa = _sa()
    packs = round_items(con, root)
    out = {}
    for r in con.execute("SELECT item, qty, by_user, at FROM stock_shelf_fix WHERE count_id=? AND source='recount' ORDER BY id", (int(root),)):
        pack, packing = packs.get(r[0], (1, ""))
        out[r[0]] = dict(item=r[0], pack=pack, packing=packing, qty=int(r[1]), qty_text=qw(r[1], pack, packing, r[0], "hi"),
                         by=r[2] or "", at=r[3], at_text=sa._r_stamp(r[3]) + " IST", done=True)
    return sorted(out.values(), key=lambda x: x["at"], reverse=True)


def recount_any(con, root, item, qty, who, may_change_minutes=10):
    """Dobara ginna hai: Darpan's own figure for ANY item of the round. A shelf fix (source recount), stamped; his own
    figure may be corrected within ten minutes; the same figure twice writes nothing. The owner's desk re-piles the line."""
    info = round_item(con, root, item)
    if not info:
        return False, "Yeh item is ginti mein nahi hai.", 404
    try:
        q = int(qty)
    except (TypeError, ValueError):
        return False, "Ginti likhiye.", 400
    if q < 0 or q > 100000:
        return False, "Ginti sahi likhiye.", 400
    prev = con.execute("SELECT qty, by_user, at FROM stock_shelf_fix WHERE count_id=? AND item=? AND source='recount' ORDER BY id DESC LIMIT 1",
                       (int(root), item)).fetchone()
    if prev:
        try:
            recent = (dt.datetime.now() - dt.datetime.fromisoformat(str(prev[2])[:19])) <= dt.timedelta(minutes=may_change_minutes)
        except ValueError:
            recent = False
        if int(prev[0]) == q:
            return True, "Pehle hi likha hai — dobara nahi likha.", 200
        if not (recent and prev[1] == who):
            return False, "Ginti darj ho chuki hai — badalna ho to doctor sahab se kahiye.", 409
    ts = now_iso()
    con.execute("INSERT INTO stock_shelf_fix (count_id, item, qty, source, note, by_user, at) VALUES (?,?,?,?,?,?,?)",
                (root, item, q, "recount", "Dobara ginna hai (Stock milaan)", who, ts))
    _audit(con, root, "recount", dict(item=item, qty=q, text="%s recounted by %s: %s" % (item, who, qw(q, info["pack"], info["packing"], item))), who)
    con.commit()
    return True, "Likh liya: %s — %s." % (item, qw(q, info["pack"], info["packing"], item, "hi")), 200


# ------------------------------------------------------------------ S418's doors, kept (their routes stay)
def recount_list(con, root):
    """S418: what the owner asked Darpan to count again (no new asks since S427), with his answer if any."""
    ensure(con)
    sa = _sa()
    fx = fixes(con, root)
    packs = round_items(con, root)
    out = []
    for r in con.execute("SELECT item, asked_by, asked_at FROM stock_recount_ask WHERE count_id=? ORDER BY id", (int(root),)):
        item, a_at = r[0], r[2]
        f = fx.get(item)
        done = bool(f and f["source"] == "recount" and str(f["at"]) >= str(a_at))
        pack, packing = packs.get(item, (1, ""))
        out.append(dict(item=item, packing=packing, pack=pack, asked_at=a_at, asked_text=sa._r_stamp(a_at) + " IST",
                        done=done, qty=(f["qty"] if done else None), qty_text=(qw(f["qty"], pack, packing, item, "hi") if done else ""),
                        by=(f["by"] if done else ""), at=(f["at"] if done else ""), at_text=((sa._r_stamp(f["at"]) + " IST") if done else "")))
    return out


def recount_answer(con, root, item, qty, who, may_change_minutes=10):
    """S418's door -- now the same as Darpan's own recount."""
    return recount_any(con, root, item, qty, who, may_change_minutes)


def recount_ask(con, root, who):
    """S418's 'Ask Darpan to recount' -- gone (the route answers 410). Kept so nothing imports a missing name."""
    return False, "Recount is Darpan's own option now -- 'Dobara ginna hai' on his Stock milaan.", 410, 0


def pursue_prepare(con, root, who):
    """S418's 'Make the sheet for Darpan' -- there is no Pursue pile any more; nothing is readied (the route says so)."""
    d, L, items = _pile_items(con, root, ("pursue",))
    if d is None:
        return None
    return 0


# ------------------------------------------------------------------ the record as a PDF
def record_pdf(con, d):
    import pad_receipt as PR                                  # noqa: PLC0415 -- the estate's own stdlib PDF writer, read-only use
    sa = _sa()
    lines, over, _s = classify(con, d)
    T = totals_of(lines)
    R = record(con, d, lines=lines)
    S = settings(con)
    B = block_view(con, d["count_id"])
    cid = d["count_id"]
    doc = PR._Doc("Stock count #%d - loss desk record" % cid, "%s - %s" % (PR.CLINIC, PR.STORE), "COUNT #%d - LOSS DESK RECORD" % cid)
    p = doc.pdf
    p.text(PR._L, doc.y - 15, "%s - %s" % (PR.CLINIC, PR.STORE), 14, bold=True)
    doc.y -= 21
    p.text(PR._L, doc.y - 13, "STOCK COUNT #%d OF %s - THE LOSS DESK RECORD" % (cid, d.get("day") or ""), 12, bold=True)
    doc.y -= 19
    p.line(PR._L, doc.y, PR._R, doc.y, 0.8)
    doc.y -= 6
    doc.line_text("Printed %s IST. Marg stock as on %s. Medicines and consumables; the orthotics are closed on their own section."
                  % (sa._r_stamp(now_iso()), d.get("as_on") or "-"), 8.5, gray=0.3)
    cols = [("", PR._L, "l", 200), ("Lines", PR._L + 260, "r", 0), ("At MRP", PR._L + 350, "r", 0), ("At cost", PR._L + 440, "r", 0),
            ("Unpriced", PR._R, "r", 0)]
    doc.thead("THE TOTALS (the same figures as the desk and the hub)", cols)
    for label, t in (("Short at the count (all lines below)", T["short"]), ("Open -- still to settle", T["open"]),
                     ("   with you / back in store (to accept)", T["with_me"]), ("   write off", T["writeoff"]),
                     ("   big losses", T["bigloss"]), ("   consumption", T["consume"]),
                     ("Back in store / explained", T["back"]), ("Written off", T["written_off"])):
        doc.trow("THE TOTALS", cols, [label, str(t["n"]), PR._rs(t["mrp_p"]), PR._rs(t["cost_p"]), str(t["unpriced"] or "")],
                 bold=not label.startswith("   "))
    doc.heading("THE RULES IN FORCE NOW")
    for s in settings_view(con):
        doc.kv(s["label"], str(s["shown"]), kw=200)
    icols = [("#", PR._L + 16, "r", 0), ("Item", PR._L + 22, "l", 230), ("Short", PR._L + 330, "r", 0),
             ("At MRP", PR._L + 410, "r", 0), ("At cost", PR._R, "r", 0)]
    if B:
        doc.heading("THE STAFF BLOCK (as Darpan's Stock milaan shows it, frozen at the close of %s)" % B["at_text"])
        TB = B.get("tables")
        if TB:                                                # S437: the block as tables -- kul, Badi kami, Chhoti kami, the orthotic rows apart
            bcols = [("#", PR._L + 16, "r", 0), ("Item", PR._L + 22, "l", 190), ("Marg (count day)", PR._L + 290, "r", 0), ("Counted", PR._L + 360, "r", 0),
                     ("Short", PR._L + 440, "r", 0), ("Rs", PR._R, "r", 0)]
            doc.para(TB["kul"]["en"] + "  ·  " + TB["kul"]["hi"], 9.5, 0.1)
            for key, T2 in (("badi", TB["badi"]), ("chhoti", TB["chhoti"]), ("ortho", TB["ortho"])):
                if key == "ortho" and not T2["n"]:
                    continue
                doc.para(T2["en"] + ("" if key != "ortho" else "") + "   (" + T2["hi"] + ")", 9, 0.15)
                if T2["rows"]:
                    doc.thead(T2["en"], bcols)
                    for i, r_ in enumerate(T2["rows"], 1):
                        doc.trow(T2["en"], bcols, [str(i), r_["item"], r_["marg_text"], r_["counted_text"], r_["short_text"], r_["rs"]])
                    doc.trow(T2["en"], bcols, ["", "TOTAL", "", "", "%d line%s" % (len(T2["rows"]), "" if len(T2["rows"]) == 1 else "s"), _rs(T2["total_p"])], bold=True)
        else:
            for ln in B["lines_en"]:
                doc.para(ln, 9, 0.1)
            for ln in B["lines_hi"]:
                doc.para(ln, 8.5, 0.35)
        if B["notes"]:
            doc.para("Kuchh batana hai? -- " + " | ".join("%s (%s): %s" % (n["by"], n["at_text"], n["text"]) for n in B["notes"]), 8.5, 0.2)
    for g in R["groups"]:
        doc.heading("WRITTEN OFF -- %s: %d line%s, %s at MRP, %s at cost" % (g["title"].upper(), g["n"], "" if g["n"] == 1 else "s", PR._rs(g["mrp_p"]), PR._rs(g["cost_p"])))
        doc.para(g["blurb"])
        doc.thead(g["title"], icols)
        for i, l in enumerate(g["lines"], 1):
            doc.trow(g["title"], icols, [str(i), l["item"], l["short_text"] or l["short_day_text"], PR._rs(l["mrp_p"]), PR._rs(l["cost_p"])])
    if R["sold_after"]:
        tcols = [("#", PR._L + 16, "r", 0), ("Item", PR._L + 22, "l", 200), ("Counted", PR._L + 300, "r", 0), ("Sold since", PR._L + 390, "r", 0),
                 ("Bought since", PR._L + 470, "r", 0), ("Shelf now", PR._R, "r", 0)]
        doc.heading("SOLD AFTER THE COUNT -- THE STOCK EXISTED, THE COUNT WAS SHORT (closed by the system): %d line%s" % (len(R["sold_after"]), "" if len(R["sold_after"]) == 1 else "s"))
        doc.para("More was sold after the count day than had been counted plus bought since: the stock was there. The line is closed as explained and the shelf figure is Marg's.")
        doc.thead("Sold after the count", tcols)
        for i, l in enumerate(R["sold_after"], 1):
            t = l["test"]
            doc.trow("Sold after the count", tcols, [str(i), l["item"], t["counted_text"], t["sold_text"], t["bought_text"], l["marg_text"]])
    if R.get("closes"):
        doc.heading("EACH CLOSE OF THE COUNT")
        for k in R["closes"]:
            doc.para("%s by %s: %s -- total %s, small %s, big %s." % (k["at_text"], k["by"] or "-", k["how_text"], PR._rs(k["total_p"]), PR._rs(k["small_p"]), PR._rs(k["big_p"])), 8.5, 0.2)
    if R["runs"]:
        doc.heading("EACH CLOSE / CLEAR / WRITE-OFF TAP")
        for r in R["runs"]:
            st = r["settings"]
            rule_txt = ("allowance %s%% (floor %s strips), small-gap ceiling %s, big-loss floor %s, slow %s months from %s, %s lines a voucher"
                        % (st.get("allowance_pct"), st.get("allowance_min_strips"), PR._rs(st.get("small_gap_ceiling_p")), PR._rs(st.get("big_loss_floor_p")),
                           st.get("slow_months"), PR._rs(st.get("slow_floor_p")), st.get("voucher_batch"))) if "allowance_pct" in st else \
                ("S418 rules: allowance x%s, pursue floor %s, small-gap ceiling %s, %s lines a voucher" % (st.get("allowance_scale"), PR._rs(st.get("pursue_floor_p")),
                                                                                                          PR._rs(st.get("small_gap_ceiling_p")), st.get("voucher_batch")))
            doc.para("%s by %s -- %s: %d lines, %s at MRP, %s at cost; %s; Marg voucher round %s; fingerprint %s. Rules: %s."
                     % (r["at_text"], r["by"] or "-", r["kind_text"], r["lines"], PR._rs(r["mrp_p"]), PR._rs(r["cost_p"]),
                        "; ".join("%s %d" % (g["title"], g["n"]) for g in r["groups"]), r["round_no"] or "-", r["md5"], rule_txt), 8.5, 0.2)
    for key, title in (("back", "BACK IN STORE / EXPLAINED -- valued at the count day"), ("bigloss", "BIG LOSSES -- OPEN"), ("consume", "CONSUMPTION -- OPEN"),
                       ("with_me", "WITH YOU -- TO ACCEPT BACK"), ("writeoff", "IN THE WRITE-OFF PILE -- NOT YET WRITTEN OFF")):
        ls = sorted([l for l in lines if l["bucket"] == key], key=_sortkey)
        if not ls:
            continue
        doc.heading("%s: %d line%s" % (title, len(ls), "" if len(ls) == 1 else "s"))
        doc.thead(title, icols)
        for i, l in enumerate(ls, 1):
            day = key == "back"
            doc.trow(title, icols, [str(i), l["item"], (l["short_day_text"] if day else (l["short_text"] or l.get("over_text") or "")),
                                    PR._rs(l["mrp_day_p"] if day else l["mrp_p"]), PR._rs(l["cost_day_p"] if day else l["cost_p"])])
    if over:
        ocols = [("#", PR._L + 16, "r", 0), ("Item", PR._L + 22, "l", 260), ("Over", PR._L + 400, "r", 0), ("Marg", PR._R, "r", 0)]
        doc.heading("OVER ON THE SHELF -- NEVER A LOSS: %d line%s" % (len(over), "" if len(over) == 1 else "s"))
        doc.thead("Over on the shelf", ocols)
        for i, l in enumerate(over, 1):
            doc.trow("Over on the shelf", ocols, [str(i), l["item"], l["over_text"], l["marg_text"]])
    if R["settings_log"]:
        doc.heading("EVERY CHANGE OF A RULE")
        for c in R["settings_log"]:
            doc.para("%s  %s: %s -> %s  (%s)" % (c["at_text"], c["label"], c["old_text"], c["new_text"], "seeded by the kit" if c["seeded"] else c["by"]), 8.5, 0.2)
    return doc.finish("Stock count #%d - the loss desk record - %s" % (cid, KIT))
