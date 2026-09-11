#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marg_spine.py  --  S229, 07-Sep-2026.  THE ITEM SPINE.  v2.

WHAT THIS IS
    One row per real product, and every name that product has ever worn.
    Seven new tables; nothing existing is altered, renamed or dropped.

THE PROBLEM IT SOLVES, MEASURED 07-09-2026
    407 distinct product names for a shelf of 373, and 515 sale lines carrying
    Rs 95,611.93 of MRP value that tied to no shelf item at all.  The cause is
    that Marg clips a description to a fixed width -- AND THE WIDTH DIFFERS BY
    REPORT: 20 characters in the sale report, 27 in the purchase reports.

THE CARDINAL RULE
    A name is resolved or it is recorded.  IT IS NEVER GUESSED.
    A clip fitting two items is written to marg_name_unresolved and raised as a
    task.  It is never assigned to the first, the biggest or the newest.

WHAT v2 FIXED, AND WHY IT MATTERS
    v1 passed 44 self-tests and was still wrong in the one case the whole file
    exists to serve.  An adversarial review against real data found that the
    FIRST TIME the owner applied one of the 24 agreed renames, _add_item would
    mint a SECOND item -- because it asked marg_item.canonical whether it knew
    the product, and a pending rename lives in marg_item_name.  373 items would
    have become 397, twenty-four of them nameless, and nothing would have said
    so.  Every fix below is from that review:
      1  _add_item now resolves through EVERY known name, and a name that
         already belongs to another item raises a task instead of being lost.
      2  the clip test compares against the clip INDEX KEY, not the length of
         the incoming string, which had blocked real clips whose 20th character
         was a space and admitted short names that were not clips at all.
      3  _facts resolves at each source's OWN width; it was using 20 for tables
         declared at 27, so one build could call a name unknown and write a
         cost from it in the same minute.
      4  first_seen / last_seen are MIN and MAX over normalised dates; they were
         last-writer-wins over mixed date formats, and stock_diff -- which
         carries no date and runs last -- was wiping 230 of 423 of them.
      5  a task's money and wording are UPDATED, not frozen at first sight.
      6  money from sale lines is quantity-weighted.  amount_p is a PACK PRICE,
         not a line total (159 of 224 items have exactly one distinct value),
         so summing it unweighted answers no question anyone asked.

ONE JUDGEMENT, NOT TWO
    norm() is character-for-character the live server's sale_key(), and MRP is
    the median of amount_p / pack_units(pack) over the item's own non-return
    sale lines -- the rule build_table.py already uses.

USAGE
    python marg_spine.py --selftest
    python marg_spine.py --db <finance.db> --dry-run
    python marg_spine.py --db <finance.db> --build
    python marg_spine.py --db <finance.db> --report
    On the VPS: /root/wa/venv/bin/python3
"""
import argparse, datetime, json, os, re, sqlite3, statistics, sys

HERE   = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(HERE, "marg_spine_schema.sql")
IST    = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# Marg clips a description to a fixed width, AND THE WIDTH IS NOT THE SAME IN
# EVERY REPORT.  Both figures are OBSERVED on real exports across Apr-Sep 2026.
# The purchase width was found only by running this against real data: four
# purchase names came back unknown at 27 characters, which no amount of reading
# the sale side could have revealed.
W_SALE, W_PURCHASE = 20, 27
SOURCE_WIDTH = {
    "sale_line_item":     W_SALE,
    "purchase_line":      W_PURCHASE,
    "stock_snapshot":     W_PURCHASE,   # push_expected writes purchase-shaped names here
    "stock_feed":         W_PURCHASE,
    "stock_rate":         W_PURCHASE,
    "stock_diff":         W_PURCHASE,
    "purchase_salt_marg": W_PURCHASE,
    "stock_count_item":   W_PURCHASE,
}
ALL_WIDTHS = sorted(set(SOURCE_WIDTH.values()))

def now_ist():
    return datetime.datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S")

# --------------------------------------------------------------------------- #
# NORMALISATION -- identical to the live server's sale_key()
# --------------------------------------------------------------------------- #
def norm(s):
    """The live server's sale_key(), character for character.  Deliberately not
    'improved': if this and the server disagree about what a name means, two
    systems hold two opinions and the join changes without anyone deciding."""
    return re.sub(r"[^A-Z0-9]+", " ", (s or "").upper()).strip()

RE_QTY_PREFIX = re.compile(r"^\d+\s*\*{2,}\s*")          # '1 *** PRIME CAST 4"'
RE_PACK_TAIL  = re.compile(r"\s+\d+\s*\*\s*\d+\s*$")     # 'LINTIDE 145 MCG 1*1'
RE_ZZ_PREFIX  = re.compile(r"^Z{2,}(?=[A-Z0-9])", re.I)  # Marg's deactivation mark

def clean_raw(raw):
    """Undo the three deformations we can reverse with certainty, on the RAW
    string, before normalising.  Returns (cleaned, marks).

    Order matters: the quantity prefix comes off first, or the pack-tail test
    would see '1 *** X 1*1' and strip the wrong end.  Case is preserved."""
    s = re.sub(r"\s+", " ", str(raw or "")).strip()
    marks = []
    t = RE_QTY_PREFIX.sub("", s)
    if t != s: s, _ = t, marks.append("qty_prefix")
    t = RE_PACK_TAIL.sub("", s)
    if t != s: s, _ = t, marks.append("pack_tail")
    t = RE_ZZ_PREFIX.sub("", s)
    if t != s: s, _ = t, marks.append("zz_prefix")
    return s.strip(), marks

def truncation_of(raw, width):
    """What a Marg report of this width would print.  Computed on the RAW
    string because Marg counts characters, then normalised so it compares."""
    return norm(str(raw or "")[:width])

def pack_units(pk):
    """'1*10' -> 10.  The server's rule."""
    s = str(pk or "").strip()
    m = re.search(r"(\d+)\s*\*\s*(\d+)", s)
    if m: return int(m.group(1)) * int(m.group(2))
    if s.isdigit(): return int(s)
    return None

def packs_sold(qty_raw, pack):
    """How many PACKS a sale line moved.  '3:0' is 3 strips; '0:7' is 7 loose
    out of a pack.  Returns None when the shape is unreadable -- and None is
    never quietly treated as 1."""
    s = str(qty_raw or "").strip()
    pu = pack_units(pack)
    m = re.match(r"^(-?\d+)\s*:\s*(\d+)$", s)
    if m:
        strips, loose = int(m.group(1)), int(m.group(2))
        return strips + (loose / float(pu) if pu else 0.0)
    try:
        return float(s)
    except (TypeError, ValueError):
        return None

def mrp_value_p(amount_p, qty_raw, pack):
    """The MRP value a sale line represents.

    amount_p is the price of ONE PACK, not the line total -- proven on real
    data: 159 of 224 items carry exactly one distinct amount_p across every
    line, whatever the quantity.  Summing it unweighted answers no question."""
    n = packs_sold(qty_raw, pack)
    if amount_p is None: return 0
    if n is None: return int(amount_p)          # unreadable quantity: count once, honestly
    return int(round(amount_p * n))

def iso_date(v):
    """One date shape, so MIN and MAX mean something.  The tables mix ISO
    (2026-09-05) with Marg's DD-MM-YYYY (05-09-2026); comparing them as text
    put three names on the real database with first_seen AFTER last_seen."""
    s = str(v or "").strip()
    if not s: return None
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m: return "%s-%s-%s" % m.groups()
    m = re.match(r"^(\d{2})-(\d{2})-(\d{4})", s)
    if m: return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1))
    return None

# --------------------------------------------------------------------------- #
# THE RENAMES AGREED WITH THE OWNER, 07-Sep-2026 -- registered BEFORE they happen
#
# The day a rename is made in Marg, the next export carries a name this system
# has never seen.  Registered ahead, each one joins itself when it lands, in any
# order, over any number of days.  The rule: the size moves to sit immediately
# after the product noun, inside the first 20 characters.  Verified 07-09-2026:
# after all 24, no two of the 373 items share a 20-character prefix and no two
# end up with the same full name.
# --------------------------------------------------------------------------- #
PENDING_RENAMES = [
    ("L S BELT CONT GRAY UNISON L",   "L S BELT L CONT GRAY UNISON"),
    ("L S BELT CONT GRAY UNISON M",   "L S BELT M CONT GRAY UNISON"),
    ("L S BELT CONT GRAY UNISON XL",  "L S BELT XL CONT GRAY UNISON"),
    ("L S BELT CONT GRAY UNISON XXL", "L S BELT XXL CONT GRAY UNISON"),
    ("L S BELT CONT GRAY UNISON XXX", "L S BELT XXX CONT GRAY UNISON"),
    ("KNEE SUPPORT HINGED L",         "KNEE SUPPORT L HINGED"),
    ("KNEE SUPPORT HINGED M",         "KNEE SUPPORT M HINGED"),
    ("KNEE SUPPORT HINGED XL",        "KNEE SUPPORT XL HINGED"),
    ("KNEE SUPPORT HINGED XXL UNISO", "KNEE SUPPORT XXL HINGED UNISON"),
    ("SHOULDER IMMOBILISE UNISON L",  "SHOULDER IMMOB L UNISON"),
    ("SHOULDER IMMOBILISE UNISON M",  "SHOULDER IMMOB M UNISON"),
    ("SHOULDER IMMOBILISE UNISON XL", "SHOULDER IMMOB XL UNISON"),
    ("ANKLE BINDER BAMBOO L",         "ANKLE BINDER L BAMBOO"),
    ("ANKLE BINDER BAMBOO M",         "ANKLE BINDER M BAMBOO"),
    ("BLING PELVIC TRACTION BELT L",  "BLING PELVIC TRACT L BELT"),
    ("BLING PELVIC TRACTION BELT XL", "BLING PELVIC TRACT XL BELT"),
    ("KNEE IMMOBILIZER UNISON L",     "KNEE IMMOBILIZER L UNISON"),
    ("KNEE IMMOBILIZER UNISON XL",    "KNEE IMMOBILIZER XL UNISON"),
    ("KNEE IMMOBILISER UNISON M",     "KNEE IMMOBILIZER M UNISON"),
    ("TYNOR WRIST SPLINT LF L ELAST", "TYNOR WRIST SPL LF L ELAST"),
    ("TYNOR WRIST SPLINT LF M ELAS",  "TYNOR WRIST SPL LF M ELAST"),
    ("TYNOR WRIST SPLINT RT L ELAST", "TYNOR WRIST SPL RT L ELAST"),
    ("TYNOR WRIST SPLINT RT M ELAST", "TYNOR WRIST SPL RT M ELAST"),
    ("LINTIDE 145 MCG 1*1",           "LINTIDE 145 MCG"),
]

# Renames Marg has ALREADY made -- old name stops, new one starts, no overlap.
HISTORICAL_RENAMES = [
    ("LEUKOCREPE 10 CM", "LEUKOCREPE 10CM*4IN", "clean handover 19-Aug -> 25-Aug-2026"),
    ("LEUKOCREPE 15 CM", "LEUKOCREPE 15CM*6INC", "clean handover 11-Aug -> 27-Aug-2026"),
]

# Records merged away in Marg.  The old spellings stay resolvable so history
# survives.  'done' = already merged; 'optional' = his call, no stock moves.
MERGED_RECORDS = [
    ("NIPRO 3 ML DISPO SYRINGE", "DISPO SYRINGE NIPRO 3ML", "done",
     "merged by the owner; last billed 12-Aug-2026. The full spelling, as Marg's "
     "own stock export still carried it on 27-Aug and 02-Sep-2026."),
    ("NIPRO 3 ML DISPO SYR", "DISPO SYRINGE NIPRO 3ML", "done",
     "the 20-character clip of the same merged-away record, as the sale report printed it"),
    ("VINTAZ P 4500", "VINTAZ P 4500 INJ", "done",
     "merged by the owner between Marg's 02-09 and 03-09 exports, and the arithmetic proves it: "
     "VINTAZ P 4500 held 25 and VINTAZ P 4500 INJ held -1 on 02-09; on 03-09 there is one row at 24. "
     "25 + (-1) = 24. Registered so the spine stops asking whether they are the same item."),
    ("PARI 12.5", "PARI CR 12.5", "optional",
     "out of use since 15-Jul-2026, not on the 06-Sep shelf; 12 old bills"),
    ("PARI 25", "PARI CR 25", "optional",
     "out of use since 27-Jun-2026, not on the 06-Sep shelf; 1 old bill"),
]

# --------------------------------------------------------------------------- #
# RESOLUTION
# --------------------------------------------------------------------------- #
# Only these kinds may compete for a clipped prefix.  A superseded, merged or
# historical spelling stays resolvable EXACTLY -- its history matters -- but must
# not compete, or a rename could never clear the ambiguity it was made to remove.
TRUNC_KINDS = ("canonical", "pending_rename")

class Spine(object):
    def __init__(self, con, width=W_SALE):
        self.con = con
        self.width = width
        self.load()

    def load(self):
        self.by_name = {}
        self._raws = []                 # (item_id, raw) for names Marg can print TODAY
        self._raws_hist = []            # (item_id, raw) for every name it has EVER worn
        self._cache = {}
        self._cache_hist = {}
        retired = {r[0] for r in self.con.execute(
            "SELECT item_id FROM marg_item WHERE status='retired'")}
        for name, iid, kind, raw in self.con.execute(
                "SELECT name, item_id, kind, name_raw FROM marg_item_name WHERE active=1"):
            self.by_name[name] = iid
            # A retired item's name must not stand in front of a live one in the
            # clip index; it can still be found exactly.
            if iid not in retired:
                self._raws_hist.append((iid, raw))
                if kind in TRUNC_KINDS:
                    self._raws.append((iid, raw))

    def index(self, width, historic=False):
        """clip key -> {(item_id, raw_length)}.  Cached: a build asks for the
        same two widths thousands of times.

        historic=True also includes superseded, merged and historical spellings.
        Used ONLY after the live index has failed, and only to explain an old
        line: once the 24 renames are made, 'KNEE SUPPORT HINGED' stops being
        any live item's clip, and without this the 28 sale lines already billed
        under it would go from 'ambiguous between these four' -- which is the
        truth -- to 'matches nothing', which is not."""
        cache = self._cache_hist if historic else self._cache
        if width not in cache:
            ix = {}
            for iid, raw in (self._raws_hist if historic else self._raws):
                ix.setdefault(truncation_of(raw, width), set()).add((iid, len(str(raw))))
            cache[width] = ix
        return cache[width]

    def resolve(self, raw, width=None):
        """(item_id, how, candidates).
        how: exact | cleaned:<marks> | truncation | ambiguous | unknown.
        On 'ambiguous' item_id is None and every candidate is listed.  NOTHING
        IS EVER PICKED FROM THAT LIST HERE."""
        n = norm(raw)
        if n in self.by_name:
            return self.by_name[n], "exact", None
        cleaned, marks = clean_raw(raw)
        cn = norm(cleaned)
        if cn and cn != n and cn in self.by_name:
            return self.by_name[cn], "cleaned:" + "+".join(marks), None
        # A clip is recognised by MATCHING THE INDEX KEY, not by the length of
        # the incoming string.  v1 gated on len(raw) >= width-1, which blocked a
        # real clip whose 20th character was a space (it arrives trimmed and
        # short) and admitted short names that were never clipped at all.
        w = self.width if width is None else width
        raw_len = len(re.sub(r"\s+", " ", str(raw or "")).strip())
        # Each candidate is measured against ITS OWN length.  Measuring the
        # cleaned candidate against the raw length hid two real sale lines --
        # '4 *** SOFT COLLAR NEOLIFE 1*1' is 29 characters of decoration around
        # a 19-character name, and no shelf item is longer than 29.
        pairs = [(n, raw_len)] if cn == n else [(n, raw_len), (cn, len(cleaned))]
        for cand, cand_len in pairs:
            if not cand:
                continue
            # only names LONGER than the candidate can have been clipped down to
            # it; an equal-length match would have been found exactly.
            hits = {i for (i, ln) in self.index(w).get(cand, set()) if ln > cand_len}
            if len(hits) == 1:
                return sorted(hits)[0], "truncation", None
            if len(hits) > 1:
                return None, "ambiguous", sorted(hits)
        for cand, cand_len in pairs:
            if not cand:
                continue
            hits = {i for (i, ln) in self.index(w, historic=True).get(cand, set()) if ln > cand_len}
            if len(hits) == 1:
                return sorted(hits)[0], "truncation", None
            if len(hits) > 1:
                return None, "ambiguous", sorted(hits)
        return None, "unknown", None


# --------------------------------------------------------------------------- #
# WRITES -- every one idempotent, and none of them silent
# --------------------------------------------------------------------------- #
def _tables(con):
    return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}

def ensure_schema(con, schema_path=SCHEMA):
    with open(schema_path, "r", encoding="utf-8") as fh:
        con.executescript(fh.read())

def _set(con, key, value, note):
    con.execute("INSERT INTO marg_spine_setting(key,value,note,updated_at) VALUES(?,?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, note=excluded.note, "
                "updated_at=excluded.updated_at", (key, str(value), note, now_ist()))

def _task(con, kind, a, b, c, item_id=None, section=None, seq=None,
          detail=None, money_p=None, source=None):
    """Upsert.  v1 used INSERT OR IGNORE, so a task's money and wording froze at
    the first sight of the problem while the report moved on -- the worklist and
    the report then disagreed permanently.  Sources accumulate rather than the
    second one being dropped."""
    row = con.execute("SELECT id, money_p, source FROM marg_task WHERE kind=? AND a=? AND b=?",
                      (kind, a, b or "")).fetchone()
    if row:
        srcs = sorted(set(filter(None, (row[2] or "").split(","))) | ({source} if source else set()))
        con.execute("UPDATE marg_task SET c=?, detail=COALESCE(?,detail), money_p=?, source=? "
                    "WHERE id=?", (c, detail, money_p, ",".join(srcs), row[0]))
        return row[0]
    cur = con.execute("INSERT INTO marg_task"
                      "(kind,item_id,section,seq,a,b,c,detail,money_p,status,source,created_at) "
                      "VALUES(?,?,?,?,?,?,?,?,?,'open',?,?)",
                      (kind, item_id, section, seq, a, b or "", c, detail, money_p, source, now_ist()))
    return cur.lastrowid

def _add_name(con, item_id, raw, kind, note=None, source=None, active=1):
    """Idempotent, and NEVER silent about a clash.  A name already owned by
    another item is left where it is and reported -- silently re-pointing a name
    is how one product's history ends up split across two."""
    n = norm(raw)
    if not n:
        return "empty"
    row = con.execute("SELECT item_id, kind FROM marg_item_name WHERE name=?", (n,)).fetchone()
    if row:
        if row[0] != item_id:
            other = con.execute("SELECT canonical_raw FROM marg_item WHERE item_id=?", (row[0],)).fetchone()
            mine  = con.execute("SELECT canonical_raw FROM marg_item WHERE item_id=?", (item_id,)).fetchone()
            _task(con, "name_clash", str(raw).strip(),
                  "%s  |  %s" % (other[0] if other else row[0], mine[0] if mine else item_id),
                  "This spelling is already recorded against a different item. Nothing was "
                  "changed. Two products cannot share one name -- say which it belongs to.",
                  item_id=row[0], section="name_clash", source=source)
            return "conflict:%d" % row[0]
        if row[1] != kind:
            con.execute("UPDATE marg_item_name SET kind=?, note=COALESCE(?,note) WHERE name=? AND item_id=?",
                        (kind, note, n, item_id))
            return "kind_changed"
        return "exists"
    con.execute("INSERT INTO marg_item_name(name,item_id,name_raw,kind,active,note,source,created_at) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (n, item_id, str(raw).strip(), kind, active, note, source, now_ist()))
    return "added"

def _add_item(con, raw, origin, first_seen=None):
    """Create an item ONLY if no existing item already answers to this name.

    THE CRITICAL FIX.  v1 asked marg_item.canonical alone.  A pending rename
    lives in marg_item_name, so the first shelf export after Amir renamed an
    item would have minted a SECOND item: 373 would have become 397, twenty-four
    of them nameless, every later sale credited to the pre-rename item, and
    nothing anywhere would have said so."""
    n = norm(raw)
    row = con.execute("SELECT item_id FROM marg_item_name WHERE name=?", (n,)).fetchone()
    if row:
        return row[0]
    row = con.execute("SELECT item_id FROM marg_item WHERE canonical=?", (n,)).fetchone()
    if row:
        return row[0]
    cur = con.execute("INSERT INTO marg_item(canonical,canonical_raw,status,origin,first_seen,created_at) "
                      "VALUES(?,?,'active',?,?,?)",
                      (n, str(raw).strip(), origin, iso_date(first_seen), now_ist()))
    return cur.lastrowid

def _seen(con, name, item_id, dmin, dmax):
    """first_seen = MIN, last_seen = MAX, over normalised dates, ignoring
    absences.  v1 wrote last-writer-wins over mixed date formats and the last
    source (stock_diff, which carries no date) wiped 230 of 423 of them."""
    a, b = iso_date(dmin), iso_date(dmax)
    if not a and not b:
        return
    cur = con.execute("SELECT first_seen, last_seen FROM marg_item_name WHERE name=? AND item_id=?",
                      (name, item_id)).fetchone()
    if not cur:
        return
    f = min([x for x in (cur[0], a) if x]) if (cur[0] or a) else None
    l = max([x for x in (cur[1], b) if x]) if (cur[1] or b) else None
    con.execute("UPDATE marg_item_name SET first_seen=?, last_seen=? WHERE name=? AND item_id=?",
                (f, l, name, item_id))

# --------------------------------------------------------------------------- #
# BUILD
# --------------------------------------------------------------------------- #
SOURCES = [("sale_line_item",     "item_name", "business_date"),
           ("purchase_line",      "item",      "bill_date"),
           ("stock_feed",         "item",      "as_on"),
           ("stock_rate",         "item",      "as_of"),
           ("purchase_salt_marg", "item",      "as_on"),
           ("stock_diff",         "item",      None)]

def build(con, out=print):
    """Create the spine and fill it.  Re-runnable; every write is idempotent."""
    started = now_ist()
    ensure_schema(con)
    _set(con, "trunc_width_sale", W_SALE,
         "Characters Marg's SALE BILL WISE report prints. OBSERVED Apr-Sep 2026.")
    _set(con, "trunc_width_purchase", W_PURCHASE,
         "Characters Marg's PURCHASE reports print. OBSERVED - found only by running the "
         "spine against real data; reading the sale side alone could not reveal it.")
    _set(con, "norm", "sale_key",
         "Normalisation is the live server's sale_key(): upper, non-alphanumeric to space, collapsed.")
    _set(con, "money", "mrp_value_p",
         "Sale money is amount_p (a PACK price) multiplied by packs sold. amount_p alone is "
         "not a line total: 159 of 224 items carry one distinct value whatever the quantity.")
    T = _tables(con)

    # ---- 1. seed from the shelf -------------------------------------------
    seeded = promoted = 0
    if "stock_count_item" in T:
        for (raw,) in con.execute("SELECT DISTINCT item FROM stock_count_item WHERE item IS NOT NULL"):
            iid = _add_item(con, raw, "shelf_seed")
            # MARG'S OWN SHELF EXPORT IS AUTHORITATIVE FOR WHAT AN ITEM IS CALLED
            # TODAY.  If it now carries a spelling we hold as a pending rename,
            # the rename has been made: promote it, and demote the name it
            # replaced so it stops competing for a clipped prefix.  Without this
            # the ambiguity the rename was made to remove would never clear.
            cur = con.execute("SELECT canonical, canonical_raw FROM marg_item WHERE item_id=?",
                              (iid,)).fetchone()
            if cur and cur[0] != norm(raw):
                con.execute("UPDATE marg_item SET canonical=?, canonical_raw=? WHERE item_id=?",
                            (norm(raw), str(raw).strip(), iid))
                _add_name(con, iid, cur[1], "superseded",
                          note="Marg's shelf export carries '%s' instead" % str(raw).strip(),
                          source="stock_count_item")
                promoted += 1
            _add_name(con, iid, raw, "canonical", source="stock_count_item")
            seeded += 1
    out("  seeded %d items from the shelf%s" % (
        seeded, (" (%d renamed in Marg since the last build)" % promoted) if promoted else ""))
    sp = Spine(con)

    # ---- 2. the agreed renames, registered BEFORE they are made ------------
    pend = applied = 0
    for old, new in PENDING_RENAMES:
        oid, how, _ = sp.resolve(old, W_PURCHASE)
        nid, hown, _ = sp.resolve(new, W_PURCHASE)
        if oid and nid and oid != nid:
            _task(con, "name_clash", new, old,
                  "The old and the new spelling are recorded against two different items. "
                  "This rename cannot be applied until that is settled.", source="S229 rename list")
            continue
        iid = oid or nid
        if iid is None:
            continue
        canon = con.execute("SELECT canonical FROM marg_item WHERE item_id=?", (iid,)).fetchone()[0]
        if canon == norm(new):
            # the rename has been made in Marg: the shelf now carries the new name
            _add_name(con, iid, old, "superseded", note="renamed in Marg (S229 list)")
            con.execute("UPDATE marg_task SET status='done', done_by='marg', done_at=? "
                        "WHERE kind='rename' AND a=? AND status='open'", (now_ist(), old))
            applied += 1
        else:
            _add_name(con, iid, new, "pending_rename",
                      note="agreed 07-Sep-2026; registered before the rename so it joins itself",
                      source="S229 rename list")
            _task(con, "rename", old, new,
                  "Marg's sale report prints %d characters and these items are identical for "
                  "those %d. Moving the size earlier makes each one unique." % (W_SALE, W_SALE),
                  item_id=iid, section="rename", source="S229 rename list")
            pend += 1
    out("  renames: %d pending, %d already made in Marg" % (pend, applied))

    # ---- 3. renames already made, and records merged away ------------------
    for old, live, why in HISTORICAL_RENAMES:
        iid, _, _ = sp.resolve(live, W_PURCHASE)
        if iid: _add_name(con, iid, old, "historical", note=why, source="S229")
    for old, live, state, why in MERGED_RECORDS:
        iid, _, _ = sp.resolve(live, W_PURCHASE)
        if iid:
            _add_name(con, iid, old, "merged", note=why, source="S229")
            if state == "optional":
                _task(con, "merge", old, live,
                      "Optional. Out of use and not on the shelf; merging only joins its old "
                      "bills. No stock moves either way.", item_id=iid, section="merge",
                      detail=why, source="S229")
    sp.load()

    # ---- 4. what Marg's OWN export knows that the count did not ------------
    # ONLY MARG'S OWN EXPORT MAY CREATE AN ITEM.  A name written by one of our
    # own computations is a derived string: 'SHOULDER IMMOBILISE UNISON' is a
    # 27-character clip that would otherwise have become a 380th phantom item
    # standing in front of three real ones.
    made = 0
    if "stock_snapshot" in T:
        cols = {r[1] for r in con.execute("PRAGMA table_info(stock_snapshot)")}
        sel = ("SELECT DISTINCT item, source FROM stock_snapshot WHERE item IS NOT NULL"
               if "source" in cols else "SELECT DISTINCT item, NULL FROM stock_snapshot WHERE item IS NOT NULL")
        for raw, src in con.execute(sel):
            iid, how, cands = sp.resolve(raw, SOURCE_WIDTH["stock_snapshot"])
            if iid is not None:
                if how == "truncation" or how.startswith("cleaned"):
                    _add_name(con, iid, raw, "truncation" if how == "truncation" else "parsed",
                              note="resolved by %s" % how, source="stock_snapshot")
                continue
            if str(src or "").startswith("push_expected"):
                _task(con, "ambiguous" if how == "ambiguous" else "question", str(raw).strip(), "",
                      "This name reached the stock table from our own expected-stock computation, "
                      "not from a Marg export, and it matches %s on the spine. Nothing was created "
                      "from it." % ("more than one item" if how == "ambiguous" else "nothing"),
                      section="derived_name", source="stock_snapshot/push_expected")
                continue
            iid = _add_item(con, raw, "snapshot")
            _add_name(con, iid, raw, "canonical", source="stock_snapshot")
            made += 1
        sp.load()
    out("  from Marg's own stock export: %d further items" % made)

    # ---- 5. a short name that is a strict prefix of a longer one -----------
    # Very likely a rename Marg made.  "Very likely" is not "known": ASK.
    # v1 asked only when there was exactly one candidate, so the cases with more
    # than one -- where the doubt is greatest -- passed in silence.
    asked = 0
    canon = [(r[0], r[1]) for r in con.execute(
        "SELECT item_id, canonical_raw FROM marg_item WHERE status='active'")]
    for iid, raw in canon:
        if con.execute("SELECT COUNT(*) FROM marg_item_name WHERE item_id=?", (iid,)).fetchone()[0] > 1:
            continue
        pre = norm(raw) + " "
        hits = [r2 for i2, r2 in canon if i2 != iid and norm(r2).startswith(pre)]
        if hits:
            _task(con, "question", raw, " | ".join(sorted(hits)),
                  "Marg's export carried the shorter name and the shelf carries the longer "
                  "one%s. Same product, renamed? Nothing is joined until you say."
                  % ("" if len(hits) == 1 else " (%d of them)" % len(hits)),
                  item_id=iid, section="same_item", source="spine")
            asked += 1
    out("  short-name questions raised (never joined on our own authority): %d" % asked)

    # ---- 6. every other name, resolved or recorded -------------------------
    stats = {}
    con.execute("DELETE FROM marg_name_unresolved")
    for tbl, col, datecol in SOURCES:
        if tbl not in T: continue
        cols = {r[1] for r in con.execute("PRAGMA table_info(%s)" % tbl)}
        if col not in cols: continue
        w = SOURCE_WIDTH.get(tbl, W_PURCHASE)
        c = stats.setdefault(tbl, dict(exact=0, cleaned=0, truncation=0, ambiguous=0, unknown=0))
        agg = {}
        if tbl == "sale_line_item":
            for raw, amt, qty, pk, bd in con.execute(
                    "SELECT item_name, amount_p, qty_raw, pack, business_date FROM sale_line_item "
                    "WHERE item_name IS NOT NULL"):
                a = agg.setdefault(raw, [0, 0, None, None])
                a[0] += 1; a[1] += mrp_value_p(amt, qty, pk)
                d = iso_date(bd)
                if d: a[2] = min(a[2] or d, d); a[3] = max(a[3] or d, d)
        else:
            money = "amount_p" if "amount_p" in cols else ("value_p" if "value_p" in cols else None)
            sel = ("SELECT %s, COUNT(*), %s, %s, %s FROM %s WHERE %s IS NOT NULL GROUP BY %s" % (
                col, ("SUM(COALESCE(%s,0))" % money) if money else "0",
                ("MIN(%s)" % datecol) if (datecol and datecol in cols) else "NULL",
                ("MAX(%s)" % datecol) if (datecol and datecol in cols) else "NULL",
                tbl, col, col))
            for raw, n, m, dmin, dmax in con.execute(sel):
                agg[raw] = [n, m or 0, iso_date(dmin), iso_date(dmax)]
        for raw, (lines, money, dmin, dmax) in agg.items():
            iid, how, cands = sp.resolve(raw, w)
            key = how.split(":")[0]
            c[key] = c.get(key, 0) + 1
            if iid is not None:
                if key in ("truncation", "cleaned"):
                    _add_name(con, iid, raw, "truncation" if key == "truncation" else "parsed",
                              note="resolved by %s at width %d" % (how, w), source=tbl)
                _seen(con, norm(raw), iid, dmin, dmax)
            else:
                con.execute("INSERT OR REPLACE INTO marg_name_unresolved"
                            "(name,name_raw,seen_in,verdict,candidates,lines,money_p,"
                            " first_seen,last_seen,computed_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                            (norm(raw), str(raw).strip(), tbl, key,
                             json.dumps(cands) if cands else None, lines, money, dmin, dmax, now_ist()))
                names = [con.execute("SELECT canonical_raw FROM marg_item WHERE item_id=?", (i,)).fetchone()[0]
                         for i in (cands or [])]
                _task(con, "ambiguous" if key == "ambiguous" else "question",
                      str(raw).strip(), " | ".join(names),
                      ("Marg clipped this name at %d characters and it fits %d different items. "
                       "It cannot be settled from the report -- only from the bill."
                       % (w, len(cands or []))) if key == "ambiguous"
                      else "Seen in %s and matching nothing on the spine." % tbl,
                      section=key, money_p=money, source=tbl)
        sp.load()
    for tbl, c in sorted(stats.items()):
        out("  %-20s exact %-4d cleaned %-3d clipped %-3d | ambiguous %-3d unknown %-3d"
            % (tbl, c["exact"], c["cleaned"], c["truncation"], c["ambiguous"], c["unknown"]))

    nfacts = _facts(con, sp, T, out)
    counts = dict(
        items=con.execute("SELECT COUNT(*) FROM marg_item").fetchone()[0],
        names=con.execute("SELECT COUNT(*) FROM marg_item_name").fetchone()[0],
        facts=nfacts,
        tasks_open=con.execute("SELECT COUNT(*) FROM marg_task WHERE status='open'").fetchone()[0],
        unresolved=con.execute("SELECT COUNT(*) FROM marg_name_unresolved").fetchone()[0])
    con.execute("INSERT INTO marg_spine_run"
                "(started_at,finished_at,mode,items,names,facts,tasks_open,unresolved,notes) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (started, now_ist(), "build", counts["items"], counts["names"], counts["facts"],
                 counts["tasks_open"], counts["unresolved"],
                 json.dumps({"per_source": stats,
                             "note": "counts describe THIS run's starting state; on a second run "
                                     "names resolved by the first are already exact"})))
    con.commit()
    return counts


def _facts(con, sp, T, out=print):
    """Derived facts only.  Recomputed from scratch, each carrying its source,
    the date it is true for, and how many rows it rests on.  A person's decision
    never lands here -- that goes to marg_task."""
    n = 0
    def put(iid, fact, value, as_of, source, basis, cov):
        con.execute("INSERT INTO marg_item_fact"
                    "(item_id,fact,value,as_of,source,basis,coverage_n,computed_at) "
                    "VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(item_id,fact) DO UPDATE SET "
                    "value=excluded.value, as_of=excluded.as_of, source=excluded.source, "
                    "basis=excluded.basis, coverage_n=excluded.coverage_n, computed_at=excluded.computed_at",
                    (iid, fact, None if value is None else str(value), as_of, source, basis, cov, now_ist()))
    # each source resolved at ITS OWN width -- v1 used 20 everywhere, so a build
    # could call a name unknown and write a cost from it in the same minute.
    if "purchase_salt_marg" in T:
        for raw, salt, as_on in con.execute("SELECT item, salt, as_on FROM purchase_salt_marg "
                                            "WHERE salt IS NOT NULL AND TRIM(salt)<>''"):
            iid, _, _ = sp.resolve(raw, SOURCE_WIDTH["purchase_salt_marg"])
            if iid: put(iid, "salt", salt, iso_date(as_on), "purchase_salt_marg",
                        "as Marg's salt-wise list gives it", 1); n += 1
    if "stock_count_item" in T:
        for raw, ps in con.execute("SELECT item, pack_size FROM stock_count_item"):
            iid, _, _ = sp.resolve(raw, SOURCE_WIDTH["stock_count_item"])
            if iid and ps is not None:
                put(iid, "pack_size", ps, None, "stock_count_item",
                    "the pack size the count carried", 1); n += 1
    if "stock_rate" in T:
        for raw, rate, as_of, src in con.execute("SELECT item, rate_p, as_of, source FROM stock_rate"):
            iid, _, _ = sp.resolve(raw, SOURCE_WIDTH["stock_rate"])
            if iid and rate is not None:
                put(iid, "cost_p", rate, iso_date(as_of), "stock_rate",
                    "last purchase rate, as the server computed it (%s)" % (src or "-"), 1); n += 1
    if "sale_line_item" in T:
        for (iid,) in con.execute("SELECT item_id FROM marg_item"):
            names = [r[0] for r in con.execute(
                "SELECT name FROM marg_item_name WHERE item_id=? AND active=1", (iid,))]
            if not names: continue
            qs = ",".join("?" * len(names))
            rows = con.execute("SELECT amount_p, pack, business_date FROM sale_line_item "
                               "WHERE item_key IN (%s) AND is_return=0 AND amount_p>0 "
                               "ORDER BY business_date DESC LIMIT 200" % qs, names).fetchall()
            vals, newest = [], None
            for amt, pk, bd in rows:
                u = pack_units(pk)
                if amt and u: vals.append(amt / float(u))
                elif amt and pk in (None, ""): vals.append(float(amt))
                d = iso_date(bd)
                if d: newest = max(newest or d, d)
            if vals:
                put(iid, "mrp_p", int(round(statistics.median(vals))), newest, "sale_line_item",
                    "MEDIAN of amount / pack over the item's own non-return sale lines (the "
                    "server's rule), across %d name(s). The date is the NEWEST line seen, not "
                    "the date of the median value." % len(names), len(vals)); n += 1
    con.commit()
    out("  facts written: %d" % n)
    return n

# --------------------------------------------------------------------------- #
# REPORT
# --------------------------------------------------------------------------- #
def report(con, out=print):
    q = lambda s, *a: con.execute(s, a).fetchall()
    run = q("SELECT id,finished_at,items,names,facts,tasks_open,unresolved FROM marg_spine_run "
            "ORDER BY id DESC LIMIT 1")
    if not run:
        out("no build has been run"); return
    r = run[0]
    out("SPINE  build #%s at %s IST" % (r[0], r[1]))
    out("  items %d | names %d | facts %d | open tasks %d | unresolved names %d" % r[2:])
    out("")
    out("  names by kind:")
    for k, n in q("SELECT kind, COUNT(*) FROM marg_item_name GROUP BY kind ORDER BY 2 DESC"):
        out("    %-16s %d" % (k, n))
    out("")
    out("  facts held, of %d items:" % r[2])
    for f, n in q("SELECT fact, COUNT(*) FROM marg_item_fact WHERE value IS NOT NULL "
                  "GROUP BY fact ORDER BY 2 DESC"):
        out("    %-12s %-4d  (missing %d)" % (f, n, r[2] - n))
    out("")
    out("  the one worklist:")
    for k, n in q("SELECT kind, COUNT(*) FROM marg_task WHERE status='open' GROUP BY kind ORDER BY 2 DESC"):
        out("    %-12s %d" % (k, n))
    out("")
    out("  JOINED BY CLIP -- Marg printed a shortened name and it fitted exactly one item.")
    out("  Read these: a wrong one here would be a wrong number everywhere.")
    for nm, canon, note in q("SELECT n.name_raw, i.canonical_raw, n.note FROM marg_item_name n "
                             "JOIN marg_item i ON i.item_id=n.item_id WHERE n.kind='truncation' "
                             "ORDER BY n.name_raw"):
        out("    %-28s -> %s" % (nm[:28], canon))
    out("")
    amb = q("SELECT COUNT(*), COALESCE(SUM(money_p),0) FROM marg_name_unresolved WHERE verdict='ambiguous'")[0]
    unk = q("SELECT COUNT(*), COALESCE(SUM(money_p),0) FROM marg_name_unresolved WHERE verdict='unknown'")[0]
    out("  STILL NOT RESOLVED -- recorded, never guessed:")
    out("    ambiguous  %-3d names   MRP value Rs %12.2f   (a clip fitting more than one item)"
        % (amb[0], amb[1] / 100.0))
    out("    unknown    %-3d names   MRP value Rs %12.2f   (matches nothing on the spine)"
        % (unk[0], unk[1] / 100.0))
    for nm, tbl, v, ln, mp in q("SELECT name_raw, seen_in, verdict, lines, money_p "
                                "FROM marg_name_unresolved ORDER BY COALESCE(money_p,0) DESC LIMIT 12"):
        out("      %-28s %-16s %-9s %5s rows  Rs %10.2f" % (nm[:28], tbl, v, ln, (mp or 0) / 100.0))


# --------------------------------------------------------------------------- #
# SELFTEST -- offline, needs no real database
# --------------------------------------------------------------------------- #
def _fixture(shelf):
    con = sqlite3.connect(":memory:")
    con.executescript("CREATE TABLE stock_count_item(item TEXT, pack_size INT, packing TEXT);")
    con.executemany("INSERT INTO stock_count_item VALUES(?,?,?)", [(s, 1, None) for s in shelf])
    return con

def selftest(out=print):
    ok = [0]; bad = [0]
    def ck(label, cond):
        if cond: ok[0] += 1; out("  OK   " + label)
        else:    bad[0] += 1; out("  FAIL " + label)
    def sale_key(s): return re.sub(r"[^A-Z0-9]+", " ", (s or "").upper()).strip()

    # -- normalisation is the server's, character for character ---------------
    for s in ['PRIME CAST 4"', "L S BELT CONT GRAY UNISON XL", "LINTIDE 145 MCG 1*1",
              "  double  space ", "", None, "a-b_c/d", "LEUKOCREPE 10CM*4IN"]:
        ck("norm == server sale_key %r" % (s,), norm(s) == sale_key(s))

    # -- cleaners -------------------------------------------------------------
    ck("qty prefix stripped",   clean_raw('1 *** PRIME CAST 4" 1*1')[0] == 'PRIME CAST 4"')
    ck("pack tail stripped",    clean_raw("LINTIDE 145 MCG 1*1")[0] == "LINTIDE 145 MCG")
    ck("ZZ stripped",           clean_raw("ZZLINTIDE 145 MCG")[0] == "LINTIDE 145 MCG")
    ck("ZZZ stripped too",      clean_raw("ZZZLINVIZ 600")[0] == "LINVIZ 600")
    ck("both marks reported",   set(clean_raw('2 *** FINGER EXTENSION SPL 1*1')[1]) == {"qty_prefix", "pack_tail"})
    ck("a real name untouched", clean_raw("KNEE SUPPORT HINGED XL")[0] == "KNEE SUPPORT HINGED XL")
    ck("cleaning preserves case", clean_raw("ZZLintide 145 MCG")[0] == "Lintide 145 MCG")
    ck("an inner 1*1 is kept",  clean_raw("LEUKOCREPE 10CM*4IN")[0] == "LEUKOCREPE 10CM*4IN")

    # -- widths, dates, money -------------------------------------------------
    ck("clip counts characters", truncation_of("DISPO SYRINGE NIPRO 3ML", 20) == "DISPO SYRINGE NIPRO")
    ck("pack_units 1*10",  pack_units("1*10") == 10)
    ck("pack_units 30GM is unknown", pack_units("30GM") is None)
    ck("packs_sold 3 strips", packs_sold("3:0", "1*10") == 3.0)
    ck("packs_sold 7 loose of 10", abs(packs_sold("0:7", "1*10") - 0.7) < 1e-9)
    ck("packs_sold unreadable is None", packs_sold("", None) is None)
    ck("MRP value weights by quantity", mrp_value_p(16700, "3:0", "1*10") == 50100)
    ck("...and counts an unreadable quantity once, not zero", mrp_value_p(16700, "?", None) == 16700)
    ck("iso_date reads Marg's DD-MM-YYYY", iso_date("05-09-2026") == "2026-09-05")
    ck("iso_date passes ISO through",     iso_date("2026-09-05") == "2026-09-05")
    ck("iso_date refuses nonsense",       iso_date("later") is None)

    # -- the rename list is internally sound ----------------------------------
    olds = [o for o, _ in PENDING_RENAMES]; news = [n for _, n in PENDING_RENAMES]
    ck("24 renames", len(PENDING_RENAMES) == 24)
    ck("no old name repeats", len(set(olds)) == len(olds))
    ck("no new name repeats", len(set(news)) == len(news))
    ck("every new name fits Marg's field (<=30)", all(len(n) <= 30 for n in news))
    ck("no two new names collide at 20", len({truncation_of(n, 20) for n in news}) == len(news))
    ck("no new name is also an old name", not (set(news) & set(olds)))

    # -- the resolver ---------------------------------------------------------
    con = _fixture(["KNEE SUPPORT HINGED L", "KNEE SUPPORT HINGED M", "DISPO SYRINGE NIPRO 3ML",
                    "ACILOC 300", "LINTIDE 145 MCG"])
    build(con, out=lambda *a: None)
    sp = Spine(con)
    gid = lambda nm: con.execute("SELECT item_id FROM marg_item WHERE canonical=?", (norm(nm),)).fetchone()[0]
    ck("exact resolves",            sp.resolve("ACILOC 300", 20)[1] == "exact")
    ck("case/spacing irrelevant",   sp.resolve("  aciloc   300 ", 20)[0] == gid("ACILOC 300"))
    ck("a clip fitting ONE item resolves",
       sp.resolve("DISPO SYRINGE NIPRO", 20)[:2] == (gid("DISPO SYRINGE NIPRO 3ML"), "truncation"))
    i, how, cand = sp.resolve("KNEE SUPPORT HINGED", 20)
    ck("a clip fitting TWO is ambiguous", i is None and how == "ambiguous")
    ck("...and names both, picking neither", len(cand) == 2)
    ck("an unknown name is unknown", sp.resolve("SOMETHING NEW ENTIRELY", 20)[1] == "unknown")
    ck("a pack glued into a name resolves", sp.resolve("LINTIDE 145 MCG 1*1", 20)[0] == gid("LINTIDE 145 MCG"))
    ck("a ZZ-marked name resolves",         sp.resolve("ZZLINTIDE 145 MCG", 20)[0] == gid("LINTIDE 145 MCG"))
    ck("an EQUAL-length name is never a clip of itself",
       sp.resolve("ACILOC 300", 20)[1] == "exact")

    # -- THE CASE v1 GOT WRONG: applying a rename must not mint a second item --
    con2 = _fixture(["KNEE SUPPORT HINGED L", "KNEE SUPPORT HINGED M",
                     "KNEE SUPPORT HINGED XL", "KNEE SUPPORT HINGED XXL UNISO", "ACILOC 300"])
    n1 = build(con2, out=lambda *a: None)
    # Amir renames all four in Marg; the next shelf export carries the new names
    con2.execute("DELETE FROM stock_count_item")
    con2.executemany("INSERT INTO stock_count_item VALUES(?,?,?)",
                     [(n, 1, None) for o, n in PENDING_RENAMES
                      if o in ("KNEE SUPPORT HINGED L", "KNEE SUPPORT HINGED M",
                               "KNEE SUPPORT HINGED XL", "KNEE SUPPORT HINGED XXL UNISO")]
                     + [("ACILOC 300", 1, None)])
    n2 = build(con2, out=lambda *a: None)
    ck("applying a rename creates NO new item", n1["items"] == n2["items"] == 5)
    ck("...no item is left nameless",
       con2.execute("SELECT COUNT(*) FROM marg_item i WHERE NOT EXISTS"
                    "(SELECT 1 FROM marg_item_name n WHERE n.item_id=i.item_id)").fetchone()[0] == 0)
    ck("...the old spelling still resolves to the same item",
       Spine(con2).resolve("KNEE SUPPORT HINGED L", 20)[0] ==
       Spine(con2).resolve("KNEE SUPPORT L HINGED", 20)[0])
    ck("...the rename tasks close themselves",
       con2.execute("SELECT COUNT(*) FROM marg_task WHERE kind='rename' AND status='open'").fetchone()[0] == 0)
    sp2 = Spine(con2)
    ck("...and every NEW clipped name is now unique",
       all(sp2.resolve(truncation_of(n, 20), 20)[1] in ("exact", "truncation")
           for o, n in PENDING_RENAMES
           if o in ("KNEE SUPPORT HINGED L", "KNEE SUPPORT HINGED M",
                    "KNEE SUPPORT HINGED XL", "KNEE SUPPORT HINGED XXL UNISO")))
    # The lines ALREADY billed under the old clip stay ambiguous, and must.
    # Renaming cannot reach back into a bill that was printed months ago; the
    # honest answer is 'it was one of these four', not 'it matches nothing'.
    i, how, cand = sp2.resolve("KNEE SUPPORT HINGED", 20)
    ck("...while lines already billed under the old clip stay ambiguous",
       how == "ambiguous" and len(cand) == 4)

    # -- a clash is raised, never silently re-pointed -------------------------
    con3 = _fixture(["ACILOC 300", "PANTAVIN 40"])
    build(con3, out=lambda *a: None)
    a = con3.execute("SELECT item_id FROM marg_item WHERE canonical='ACILOC 300'").fetchone()[0]
    b = con3.execute("SELECT item_id FROM marg_item WHERE canonical='PANTAVIN 40'").fetchone()[0]
    ck("re-pointing a name is refused", str(_add_name(con3, b, "ACILOC 300", "canonical")).startswith("conflict"))
    ck("...and the refusal becomes a task",
       con3.execute("SELECT COUNT(*) FROM marg_task WHERE kind='name_clash'").fetchone()[0] == 1)

    # -- idempotency and order ------------------------------------------------
    con4 = _fixture(["KNEE SUPPORT HINGED L", "KNEE SUPPORT HINGED M", "ACILOC 300"])
    x1 = build(con4, out=lambda *a: None); x2 = build(con4, out=lambda *a: None)
    ck("building twice changes nothing", x1["items"] == x2["items"] and x1["names"] == x2["names"])
    ck("a run is recorded each time",
       con4.execute("SELECT COUNT(*) FROM marg_spine_run").fetchone()[0] == 2)
    ck("a task's money is updated, not frozen",
       _task(con4, "t", "a", "b", "c", money_p=100) and
       _task(con4, "t", "a", "b", "c", money_p=200) and
       con4.execute("SELECT money_p FROM marg_task WHERE kind='t'").fetchone()[0] == 200)

    # -- retired items stay out of the clip index -----------------------------
    con5 = _fixture(["DISPO SYRINGE NIPRO 3ML"])
    build(con5, out=lambda *a: None)
    con5.execute("UPDATE marg_item SET status='retired'")
    ck("a retired item does not answer a clip", Spine(con5).resolve("DISPO SYRINGE NIPRO", 20)[1] == "unknown")

    out("")
    out("SELFTEST: %d passed, %d failed" % (ok[0], bad[0]))
    return bad[0] == 0


def install(db, out=print):
    """ONE LINE that does the whole safe thing, in order, and stops at the first
    doubt.  Written because a four-step install is four chances to run step 3
    without step 2 -- and the two skipped steps are the proof.

      1  the 54 self-tests            -> refuse on a single failure
      2  a build on a COPY            -> refuse if it raises
      3  a backup of the database     -> refuse if it cannot be written
      4  the real build
    """
    import shutil, tempfile, traceback
    out("=" * 66)
    out("  1/4  SELF-TESTS")
    if not selftest(out):
        out("\n  REFUSING: a self-test failed. Nothing was touched."); return 2
    out("\n" + "=" * 66)
    out("  2/4  REHEARSAL on a copy -- the real database is not opened for writing")
    tmp = os.path.join(tempfile.mkdtemp(), "rehearsal.db")
    try:
        shutil.copy2(db, tmp)
        con = sqlite3.connect(tmp); build(con, out); con.close()
    except Exception:
        out(traceback.format_exc())
        out("  REFUSING: the rehearsal failed. Nothing was touched."); return 3
    out("\n" + "=" * 66)
    out("  3/4  BACKUP")
    bak = db + ".bak_S229_spine"
    try:
        shutil.copy2(db, bak)
        out("  written: %s  (%.1f MB)" % (bak, os.path.getsize(bak) / 1048576.0))
    except Exception:
        out(traceback.format_exc())
        out("  REFUSING: no backup could be written. Nothing was touched."); return 4
    out("\n" + "=" * 66)
    out("  4/4  BUILD  -- adds seven new tables; alters nothing that exists")
    con = sqlite3.connect(db); build(con, out); report(con, out); con.close()
    out("\n" + "=" * 66)
    out("  DONE. Nothing reads the spine yet -- no screen has changed.")
    out("  To undo entirely:  \\cp %s %s" % (bak, db))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="The Marg item spine.")
    ap.add_argument("--db")
    ap.add_argument("--install", action="store_true",
                    help="selftest, rehearse on a copy, back up, then build. One line, self-gating.")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="build on a scratch copy; change nothing")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.install:
        if not a.db:
            ap.error("--install needs --db")
        return install(a.db)
    if a.selftest:
        return 0 if selftest() else 1
    if not a.db:
        ap.error("--db is required unless --selftest")
    if a.dry_run:
        import shutil, tempfile
        tmp = os.path.join(tempfile.mkdtemp(), "scratch.db")
        shutil.copy2(a.db, tmp)
        print("DRY RUN on a copy: %s" % tmp)
        print("(the real database is never opened for writing)")
        con = sqlite3.connect(tmp); build(con); report(con); return 0
    con = sqlite3.connect(a.db)
    if a.build: build(con)
    if a.report or a.build: report(con)
    return 0

if __name__ == "__main__":
    sys.exit(main())
