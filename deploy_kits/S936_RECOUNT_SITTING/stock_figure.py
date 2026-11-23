#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  stock_figure.py  ·  v1.1  ·  kit S583_ARRIVALS_ONE_RULE  ·  Session 324 (Sanjeevni)  ·  rung 4b of the spine plan (Book 4A, 15F.1)
#  (v1.0 was S577_STOCK_ON_SPINE)
#
#  THE ONE STOCK FUNCTION (charter 1, 2, 3, 11, 12). For an item it gives two answers, each carrying the closing it stands on:
#    marg()   -- Marg's figure: the newest USABLE closing capture, by the item's printed name (sp_close_name), carried forward by the
#                spine's own movements (sp_move) to the day asked;
#    shelf()  -- the shelf figure: the newest physical count (the count family with the desk's corrections laid over, or a stock point
#                that is not the full count's own copy and not superseded) carried forward the same way, plus what has arrived and is
#                not yet in Marg. An item with no count has NO shelf figure (named 'no_count'), never Marg's.
#  The two are never mixed in one judgment. Five checks read them: the voucher guard (stock_app), Darpan's spot counts and traces
#  (stock_watch), the shelf-gap flags (shelf_figure), 'bill entry baaki' and the arrivals (stock_watch, through carried() here -- S583),
#  the owner's stock-now and drift pages (stock_app).
#
#  THE CAPTURE RULE (charter 11, unchanged -- moved here verbatim from stock_app._s524_end_day / _s524_stamp_iso): a closing is placed by
#  its capture moment, never by its printed day alone. Captured before 09:00 on its printed day = the end of the previous day; 22:00 or
#  later = the end of its own day; captured on a later day = the end of the printed day; between 09:00 and 22:00 on its own day = unusable.
#  THE ONE CHOICE RULE: for any purpose, the capture standing for a given end_day is the NEWEST usable one by stamp.
#  IDENTITY (charter 12): key_of() -- sp_item's k20 for the printed name (spacing and case ignored), else through the ticked renames
#  (item_alias.done_rows: the partner name and the owner's accepted seen_names), else the spine's alias key. Never a bare clip.
#  READ ONLY. No table of its own. No Flask: it runs inside the order_rules tick process too (record_gaps). Every reader of a finance
#  table opens nothing itself: the caller's connection (con) and the spine door (stock_watch.Spine: ok-safe) are passed in. One
#  per-request context (Ctx) is built by the caller and passed down -- never module-global.
#  stock_watch.expected_units, the PC's push_expected and marg_shadow run beside it for one witness week: `python3 stock_figure.py witness`.
#  THE ONE ARRIVAL RULE (S583, charter 2): carried() names the purchase of Marg's that carries a tapped or scan-tied order line -- (a) the
#  line's own Marg bill (billed_bill_no, S537); (b) a bill that answered ANOTHER line of the key never carries this one; (c) the order's own
#  vendor's bill dated up to arrival.back_days BEFORE the order day; (d) the own vendor's bill dated on or after the order day; (e) another
#  supplier's bill dated on or after the order day; the first eligible wins. expired() says the spine's purchase reach (reach(), read once per
#  Ctx) has passed the arrival moment by arrival.bill_grace_days -- ISO against ISO, never a raw 'YYYYMMDD-HHMMSS' compare (charter 11).
#  taps() and scan_arrivals() count a line while it is neither carried nor expired (a line with a billed_bill_no never counts);
#  arrivals_open() lists the expired ones -- the owner's Needs-you line (stock_watch.arrival_needs_you) for the scan-tied orders.
#  stock_watch._arrivals marks in_spine = carried() is not None and nothing else: a trace's finding 2 still sees a tap Marg never carried.
# =============================================================================
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import sys

VERSION = "1.5"
KIT = "S936_RECOUNT_SITTING"                                   # v1.9 S936 (a count held for a recount is never a base), v1.8 S934 (a Count now placed to its last sale bill), v1.7 S933 (the scan tie is the fact for bill_units), v1.6 S928 (the bill over the tap; a count by its time), v1.5 S628 (the one name list: Marg partners read by printed_forms / _carried), v1.4 S613 (after S602), v1.3 S598_ARRIVALS_BY_LINE, v1.2 S587_MORNING_FLOW, v1.1 S583_ARRIVALS_ONE_RULE, v1.0 S577_STOCK_ON_SPINE
#  S613 (22-Oct-2026, F-951 -- the readers' half of S605): THE SPLIT OF A SHARED KEY IS READ ONLY WHERE A READER SPANS DATES. S605's spine
#  gives each of the 22 renamed orthotic sizes its own key from its family's split day (sp_alias kind 'rename_family'); lines dated on or
#  before it stay under the old key. key_of() is NOT changed (stock_app's count-voucher proof judges keys between captures before the split).
#  split_of() -- the one place the split is known -- reads the spine's own alias note '(split YYYY-MM-DD from <old clip>)' by a strict
#  pattern, the old key through sp_item (cross-checked with the rename memory and the old key's RENAME_SPLIT date); a missing, unparsable
#  or disagreeing row = no split (today's figure) and one stderr line. split_moves() is the one helper for a split size's movements: the old
#  key's up to the split day times the size's counted share (shelf()'s rule over split_members: the old key's members in the newest usable
#  capture on or before the split day that prints it), plus the new key's after it. shelf(), marg() (and spine_move()) read it; old and
#  new name give the same figure. carried(): a split size's bill lines are its new key's (matched as today) plus its old key's matched by
#  printed name only (sib True: a sibling size's line never matches, R1-B3) -- rules (a)-(e) otherwise unchanged; the family-bill words
#  span the old family (the old key's lines to the split day, each sibling size's new key after it).
#  S602 (19-Oct-2026, F-943): the witness's read-only run never judges. A read-only caller says so on its Ctx (read_only=True), read by
#  _may_write alone: the judge stays out, the capture stays as recorded, and verify_start's work is not done for nothing on a connection
#  that cannot take the write (seen at S594's rehearsal: 'attempt to write a readonly database', one stderr line a night).
#  v1.3 (S598, 19-Oct-2026, F-942): THE BILL LINE IS THE UNIT OF THE ARRIVALS RULE. Sizes of one orthotic share a 20-letter spine key, so
#  the by-bill rule credited one size's order line with the whole family's bill (KNEE SUPPORT HINGED XL ordered 2, 'billed 6' by a bill that
#  carried M and L). Now an order line is matched to a bill LINE of its own printed name (_line_forms: every spelling Marg or the count has
#  printed for the item, clipped to 27 as Marg's bill clips; _matches), the key alone deciding only for an item with no sibling under its key
#  (_siblings). Rule (b) is per bill line, keyed on the match (_taken_lines): one bill line is never credited to two order lines of one item.
#  carried() returns the LINE's units / qty / free (two batches of one bill summed), its seq and printed name; when nothing matches, the family's bill
#  that carried OTHER sizes is kept for the owner's words (_family_bill -> arrivals_open()['family_bill']). _purchases_of and _taken_bills are
#  retired. Sizes that still agree in their first 27 letters stay one lump (Marg's report cannot tell them apart) -- named, not fixed.
#  v1.2 (S587, 18-Oct-2026, D740 / R2-B2..B5): THE START-OF-DAY CLOSING. A closing printed day D and taken on D between 09:00 and 22:00 (a
#  START capture) may stand for the END of D-1 plus the morning's Marg work -- once verified item by item (verify_start) against the previous
#  verified capture and the spine: the change in the Marg-minus-spine offset per key, the known non-spine Marg work excluded by cause
#  (count vouchers, Amir's 'fix:' taps, the consumption list, purchases dated D, bills first seen after the previous capture); an unexcluded
#  drop no bigger than the day's sales = a sale came before it (set aside); more than count.start_unexplained_max other changes = set aside;
#  else accepted. The verdict is a RECORD (finance.db stock_start_capture, one row per md5, pending -> final once), written lazily by
#  captures() when the context carries a writable connection outside a transaction (the witness's read-only run never judges, F-943), and
#  by `python3 stock_figure.py verify-start`. A capture
#  is verified only when the day's sale report is in and the purchase side covers it (purchase_cover) -- never set aside for a short reach.
#  end_day() itself is unchanged (the clock rule). The owner's switch count.start_capture (stock_watch) off = the old rule, nothing written.
#  R2-B3: marg() on a start / early-morning capture never adds the printed day's purchases again (they are inside the capture); such a key is
#  approx (reason purchase_on_start), as is a verification-excluded key with a sale dated D (start_excluded) and an unexplained key
#  (start_unexplained). The S577 early-morning helper is folded into this. R2-B4: purchase_cover() -- the spine's purchase reach (a), the newest purchase
#  exports after the closing (b), or VISIT COVER (c): the last purchase export after Amir's last bill-entry tap of the visit covers every
#  closing until his next visit's bill entry. tryable() takes it for its purchase half (both callers pass con / ctx).
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
FULL = "full_count"
MOVE_KINDS = ("SALE", "SALE_RETURN", "PURCHASE", "PURCHASE_RETURN", "RECONCILIATION")      # never OPENING (stock_app.S524_MOVE_KINDS)
LATE_DAYS = 21                                                 # a bill keyed after the closing: dated within this many days on or before its end_day
WITNESS_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


# ------------------------------------------------------------------ the lazy doors (no import cycle at module level)
def _sw():
    import stock_watch                                        # noqa: PLC0415 -- beside this file; it imports this module lazily too
    return stock_watch


def _sf_shelf():
    import shelf_figure                                       # noqa: PLC0415
    return shelf_figure


def _qw():
    import qty_words                                          # noqa: PLC0415
    return qty_words


def _ia():
    import item_alias                                         # noqa: PLC0415
    return item_alias


# ------------------------------------------------------------------ small helpers
def today():
    v = os.environ.get("ORDER_TODAY", "")
    try:
        return dt.date.fromisoformat(v) if v else dt.date.today()
    except ValueError:
        return dt.date.today()


def _iso(d):
    if d is None:
        return today().isoformat()
    return d.isoformat() if isinstance(d, (dt.date, dt.datetime)) else str(d)[:10]


def norm(n):
    """The printed name with spacing and case folded -- the key sp_close_name and sp_item are matched by (charter 12: never a clip)."""
    return re.sub(r"\s+", " ", str(n or "").strip()).upper()


def norm_name(s):
    """stock_watch.norm_name, verbatim (stock_point.item_norm)."""
    t = re.sub(r"[^A-Z0-9 ]+", " ", str(s or "").upper())
    return re.sub(r"\s+", " ", t).strip()


def dmy_iso(s):
    s = str(s or "").strip()
    m = re.match(r"^(\d\d)-(\d\d)-(\d{4})$", s)
    return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else s[:10]


class Ctx(object):
    """ONE per-request context: the connection, the spine door and the caches of one pass. Built by the caller, passed down, never
    module-global (R3-C7). Every public function takes ctx=None and builds one when it is None."""

    def __init__(self, con=None, sp=None, read_only=False):
        self.con, self.sp, self.c = con, sp, {}
        self.read_only = bool(read_only)                      # S602 (F-943): a read-only caller says so; _may_write alone reads it


def _ctx(con, sp, ctx):
    if ctx is None:
        return Ctx(con, sp)
    if ctx.con is None:
        ctx.con = con
    if ctx.sp is None:
        ctx.sp = sp
    return ctx


def _has(con, t):
    try:
        return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone() is not None
    except sqlite3.Error:
        return False


# ------------------------------------------------------------------ the capture rule (charter 11) -- verbatim from stock_app (S524)
def stamp_iso(stamp):
    """'YYYYMMDD-HHMMSS' -> 'YYYY-MM-DDTHH:MM:SS' (exactly as marg_take.py reads a capture); '' when it is not a stamp."""
    s = str(stamp or "")
    if not re.match(r"^\d{8}-\d{6}$", s):
        return ""
    return "%s-%s-%sT%s:%s:%s" % (s[0:4], s[4:6], s[6:8], s[9:11], s[11:13], s[13:15])


def end_day(as_on, stamp_iso_):
    """push_expected._gap_side as the one capture-hour rule: the day whose END the closing's figure stands for, or None when the capture
    fell inside that day's shop hours (a same-day print between 09:00 and 22:00; a print dated after its capture) -- then it is skipped."""
    sd, hm = str(stamp_iso_)[:10], str(stamp_iso_)[11:16]
    if len(sd) != 10 or len(str(as_on)) != 10:
        return None
    if as_on < sd:                                             # printed for an earlier day: the whole day was before the capture
        return as_on
    if as_on > sd:
        return None
    if hm >= "22:00":
        return as_on
    if hm < "09:00":
        try:
            return (dt.date.fromisoformat(as_on) - dt.timedelta(days=1)).isoformat()
        except ValueError:
            return None
    return None


# ------------------------------------------------------------------ the spine's reach (verbatim from stock_app S524 / S570)
def reach(sp):
    """{last_sale, sale_stamp, last_pur, pur_stamp}: last_sale = MAX(date_to) over ok=1 SALE_BILLWISE; last_pur = MIN of MAX(date_to) over ok=1
    PURCHASE_BILLWISE and over ok=1 PURCHASE_ITEMWISE|PURCHASE_BILLITEMWISE (spine_build.py 377-378); the stamps are those newest exports'."""
    def last(fam_sql):
        return str(sp.q("SELECT MAX(date_to) AS d FROM sp_export WHERE ok=1 AND " + fam_sql)[0]["d"] or "")

    def stamp_of(fam_sql, d):
        return str(sp.q("SELECT MAX(stamp) AS s FROM sp_export WHERE ok=1 AND date_to=? AND " + fam_sql, d)[0]["s"] or "") if d else ""
    S, B, I = "family='SALE_BILLWISE'", "family='PURCHASE_BILLWISE'", "family IN ('PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE')"
    ls, lb, li = last(S), last(B), last(I)
    lp = min(lb, li) if (lb and li) else ""

    def newest(fam_sql):                                      # S587 (purchase_cover b): the newest export of a family, whatever day it reaches
        return str(sp.q("SELECT MAX(stamp) AS s FROM sp_export WHERE ok=1 AND " + fam_sql)[0]["s"] or "")
    nb, ni = newest(B), newest(I)
    return dict(last_sale=ls, sale_stamp=stamp_of(S, ls), last_pur=lp, pur_stamp=(min(stamp_of(B, lb), stamp_of(I, li)) if lp else ""),
                pur_newest=(min(nb, ni) if (nb and ni) else ""))


def covers(day, stamp, c, d):
    """S570 (F-905): the newest export of a family (reaching `day`, captured at `stamp`) covers the closing `c` (end_day `d`) when it was
    captured after the closing, OR when its own capture, read by the estate's one capture rule (end_day, charter 11), stands for the
    end of a day at or after d. The morning order -- the sale report ~05:10, the closing ~05:17, both the end of yesterday -- is covered;
    a same-day capture inside shop hours gives None, and None never covers."""
    if stamp > c["stamp"]:
        return True
    e = end_day(str(day or ""), stamp_iso(stamp))
    return e is not None and e >= d


def tryable(c, reach_, con=None, ctx=None):
    """(ok, short) -- a closing is tried only when the spine's reach covers it (R1-B2): the SALE half as before (last_sale at or past its
    end_day and the newest sale export covering it -- S570, F-905); the PURCHASE half is purchase_cover() (S587, R2-B4: the reach, the newest
    exports after the closing, or Amir's visit cover -- the last needs `con`; with con None only the first two run). `c` is read with .get
    (stock_app passes a bare dict). short names what is missing: 'sale' | 'pur' | ''."""
    d = c.get("end_day") or ""
    if not d or not reach_:
        return False, "sale"
    if reach_["last_sale"] < d or not covers(reach_["last_sale"], reach_["sale_stamp"], c, d):
        return False, "sale"
    sp = ctx.sp if (ctx is not None and ctx.sp is not None) else None
    if not purchase_cover(con, sp, c, reach_, ctx):
        return False, "pur"
    return True, ""


def _ts(s):
    """Any stored moment -> 'YYYY-MM-DD HH:MM:SS' so stamps of different writers compare as text (charter 11; amir_day._norm_ts's rule):
    Marg's YYYYMMDD-HHMMSS, ISO with a 'T' and a zone, or a space. None when it is not a moment."""
    if not s:
        return None
    s = str(s).strip()
    if re.match(r"^\d{8}-\d{6}$", s):
        return "%s-%s-%s %s:%s:%s" % (s[0:4], s[4:6], s[6:8], s[9:11], s[11:13], s[13:15])
    s = s.replace("T", " ")
    if len(s) >= 19:
        return s[:19]
    if len(s) == 16:
        return s + ":00"
    if len(s) == 10:
        return s + " 00:00:00"
    return None


def purchase_cover(con, sp, c, reach_, ctx=None):
    """S587 (R2-B4): True when the PURCHASE side covers closing `c` (end_day d) by any of
      (a) the spine's purchase reach: last_pur at or past d and its newest exports covering the closing (covers: as before);
      (b) the newest purchase export of EACH family (sp_export ok=1) is stamped after the closing;
      (c) visit cover (visit_cover): the last purchase export after Amir's last bill-entry tap of the visit, with no 'self' answer and no
          open self-wait after it, covers every closing after it until his next visit's bill entry (needs `con`; None -> not by this clause).
    `c` is read with .get (stock_app's bare dict). purchase_cover_how() names the clause."""
    return purchase_cover_how(con, sp, c, reach_, ctx) is not None


def purchase_cover_how(con, sp, c, reach_, ctx=None):
    """'a' | 'b' | dict(clause='c', ...) | None -- which clause of purchase_cover covers the closing (the walk and the report print it)."""
    d = str((c or {}).get("end_day") or "")[:10]
    if not d:
        return None
    if reach_:
        lp = str(reach_.get("last_pur") or "")
        if lp and lp >= d and covers(lp, str(reach_.get("pur_stamp") or ""), c, d):
            return "a"
    newest = str((reach_ or {}).get("pur_newest") or "")      # reach() carries it; a bare reach dict without it: read the spine
    if not newest and sp is not None and getattr(sp, "ok", False):
        try:
            b = str((sp.q("SELECT MAX(stamp) AS s FROM sp_export WHERE ok=1 AND family='PURCHASE_BILLWISE'") or [{"s": ""}])[0]["s"] or "")
            i = str((sp.q("SELECT MAX(stamp) AS s FROM sp_export WHERE ok=1 AND family IN ('PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE')") or [{"s": ""}])[0]["s"] or "")
            newest = min(b, i) if (b and i) else ""
        except sqlite3.Error:
            newest = ""
    if newest and newest > str(c.get("stamp") or ""):
        return "b"
    if con is None and (ctx is None or ctx.con is None):
        return None
    v = visit_cover(con if con is not None else ctx.con, c, ctx)
    return v if v else None


def _visit_facts(con, ctx):
    """Read once per Ctx (finance.db, small tables): Amir's visit days (amir_day) with their opened_at, his step-2 ('Sab bill daal diye') taps by
    day (amir_step_log), every purchase export (purchase_export: family, Marg's stamp, rows, amount), his 'self' answers' moments and the
    open self-waits. Every moment through _ts."""
    if "visit" in ctx.c:
        return ctx.c["visit"]
    F = dict(days=[], opened={}, t2={}, exports=[], selfs=[], waits=[])
    if con is not None:
        try:
            if _has(con, "amir_day"):
                for day, opened in con.execute("SELECT day, opened_at FROM amir_day ORDER BY day"):
                    F["days"].append(str(day)[:10])
                    F["opened"][str(day)[:10]] = _ts(opened)
            if _has(con, "amir_step_log"):
                for day, at in con.execute("SELECT day, done_at FROM amir_step_log WHERE step=2 ORDER BY done_at"):
                    t = _ts(at)
                    if t:
                        F["t2"].setdefault(str(day)[:10], []).append(t)
            if _has(con, "purchase_export"):
                for typ, es, rec, n, amt in con.execute("SELECT type, export_stamp, received_at, n_rows, grand_amount_p FROM purchase_export "
                                                        "WHERE type IN ('BILLWISE','ITEMWISE','BILLITEMWISE')"):
                    at = _ts(es) or _ts(rec)
                    if at:
                        F["exports"].append(dict(fam=("B" if typ == "BILLWISE" else "I"), at=at, n=n, amt=amt, type=typ))
            if _has(con, "amir_bill_answer"):
                F["selfs"] = [t for t in (_ts(r[0]) for r in con.execute("SELECT at FROM amir_bill_answer WHERE reason='self'")) if t]
            if _has(con, "amir_self_wait"):
                F["waits"] = [t for t in (_ts(r[0]) for r in con.execute("SELECT marked_at FROM amir_self_wait WHERE cleared_at IS NULL")) if t]
        except sqlite3.Error:
            pass
    ctx.c["visit"] = F
    return F


def visit_cover(con, c, ctx=None):
    """S587 (R2-B4, restated after R1-B2 / R1-B3): clause (c). V = Amir's visit day (amir_day.day) on or before the closing's calendar day.
    T2 = his LAST step-2 tap on V before the closing (re-taps after the close included). E = the newest purchase export of EACH family (anyone's
    -- purchase_export rows; an export identical in rows and amount to the visit's own continues it) stamped at or after T2 and before the
    closing; E covers the closing when no 'self' answer and no open self-wait fall between E and the closing. On V itself the same clause runs
    on the taps made so far (R1-B3). A closing on V BEFORE he opened his day or tapped bill entry is judged by the previous visit's cover (the
    bound: the next visit's first step-2 tap, or its opened_at -- bills he keys before his first tap are never covered falsely). A visit day
    with no step-2 tap gives no cover. Returns dict(clause='c', visit, t2, at, identical) or None."""
    ctx = _ctx(con, None, ctx)
    cs = _ts(c.get("stamp_iso") or stamp_iso(c.get("stamp")))
    if not cs:
        return None
    F = _visit_facts(ctx.con, ctx)
    days = [d for d in F["days"] if d <= cs[:10]]
    if not days:
        return None
    V = days[-1]
    if V == cs[:10]:
        taps = [t for t in F["t2"].get(V, []) if t < cs]
        if not taps:
            first = min([t for t in F["t2"].get(V, [])] + ([F["opened"][V]] if F["opened"].get(V) else [])) if (F["t2"].get(V) or F["opened"].get(V)) else V + " 00:00:00"
            if cs >= first or len(days) < 2:
                return None
            V = days[-2]
            taps = list(F["t2"].get(V, []))
    else:
        taps = list(F["t2"].get(V, []))
    if not taps:
        return None
    t2 = max(taps)
    E = {}
    for fam in ("B", "I"):
        cand = [e for e in F["exports"] if e["fam"] == fam and t2 <= e["at"] < cs]
        if not cand:
            return None
        E[fam] = max(cand, key=lambda e: e["at"])
    at = max(E["B"]["at"], E["I"]["at"])
    if any(at < s <= cs for s in F["selfs"]) or any(at < w <= cs for w in F["waits"]):
        return None
    own = {fam: [e for e in F["exports"] if e["fam"] == fam and e["at"][:10] == V and e["at"] < t2] for fam in ("B", "I")}
    ident = all(own[fam] and (E[fam]["n"], E[fam]["amt"]) == (max(own[fam], key=lambda e: e["at"])["n"], max(own[fam], key=lambda e: e["at"])["amt"]) for fam in ("B", "I"))
    return dict(clause="c", visit=V, t2=t2, at=at, identical=bool(ident and at[:10] != V))


def sale_landed(sp, day):
    """The day (ISO) the sale report reaching `day` was taken -- the earliest ok=1 SALE_BILLWISE export with date_to >= day; '' when none."""
    try:
        r = sp.q("SELECT MIN(stamp) AS s FROM sp_export WHERE ok=1 AND family='SALE_BILLWISE' AND date_to>=?", str(day)[:10])
        return stamp_iso((r[0]["s"] if r else "") or "")[:10]
    except sqlite3.Error:
        return ""


# ------------------------------------------------------------------ the captures (sp_close_name)
def ready(sp):
    """False when the spine cannot be read or sp_close_name is missing or empty: every judgment then answers 'not yet' and the voucher
    guard HOLDS (an owner line) -- never offers (R2-B7)."""
    try:
        if sp is None or not getattr(sp, "ok", False):
            return False
        if not sp.q("SELECT 1 AS x FROM sqlite_master WHERE type='table' AND name='sp_close_name'"):
            return False
        return bool(sp.q("SELECT 1 AS x FROM sp_close_name LIMIT 1"))
    except sqlite3.Error:
        return False


def captures(sp, ctx=None):
    """Every closing capture held by name (sp_close_name's md5s) with its export's printed day and stamp (sp_export.as_on / stamp -- the
    one copy, R2-C17), stamp_iso and end_day. Oldest stamp first. usable = end_day is not None.
    S587 (D740): a same-day print between 09:00 and 22:00 is a START capture (start=True, start_day=D-1): usable, with end_day=D-1, only
    once its verdict is 'accepted' (stock_start_capture, finance.db -- read through ctx.con; judged here lazily when that connection may
    write, see _start_apply); otherwise unusable as before. A same-day print before 09:00 is marked early=True (end_day D-1 as before).
    verdict: None (not a start capture) | 'pending' | 'accepted' | 'set_aside' | 'off' (the owner's switch count.start_capture is off)."""
    ctx = _ctx(None, sp, ctx)
    if "caps" in ctx.c:
        return ctx.c["caps"]
    out = []
    if ready(sp):
        for r in sp.q("SELECT e.md5 AS md5, e.as_on AS as_on, e.stamp AS stamp FROM sp_export e WHERE e.md5 IN (SELECT DISTINCT md5 FROM sp_close_name) "
                      "ORDER BY e.stamp, e.md5"):
            si = stamp_iso(r["stamp"])
            as_on = str(r["as_on"] or "")
            e = end_day(as_on, si) if si else None
            c = dict(md5=str(r["md5"]), as_on=as_on, stamp=str(r["stamp"] or ""), stamp_iso=si, end_day=e, usable=e is not None,
                     start=False, early=False, start_day=None, verdict=None)
            if si and len(as_on) == 10 and as_on == si[:10]:
                hm = si[11:16]
                if hm < "09:00":
                    c["early"] = True
                elif hm < "22:00":
                    c["start"], c["start_day"] = True, _day_before(as_on)
            out.append(c)
        try:
            _start_apply(out, ctx)
        except Exception as ex:                                # noqa: BLE001 -- fail-soft: every start capture stays unusable, one line
            print("stock_figure: start captures not judged: %s" % str(ex)[:160], file=sys.stderr)
    ctx.c["caps"] = out
    return out


def _day_before(d):
    try:
        return (dt.date.fromisoformat(str(d)[:10]) - dt.timedelta(days=1)).isoformat()
    except ValueError:
        return None


def capture_of(sp, md5, ctx=None):
    """The capture dict of one md5 (captures()), or None."""
    ctx = _ctx(None, sp, ctx)
    if "capmap" not in ctx.c:
        ctx.c["capmap"] = {c["md5"]: c for c in captures(sp, ctx)}
    return ctx.c["capmap"].get(str(md5 or ""))


def usable_captures(sp, ctx=None):
    return [c for c in captures(sp, ctx) if c["usable"]]


def capture_for(sp, end_day_, ctx=None):
    """The capture standing for an end_day: the NEWEST usable one by stamp (the one choice rule); None when none stands for it."""
    cs = [c for c in usable_captures(sp, ctx) if c["end_day"] == str(end_day_ or "")[:10]]
    return max(cs, key=lambda c: c["stamp"]) if cs else None


def capture_at(sp, at=None, ctx=None):
    """The newest usable capture whose end_day is at or before `at` (today when None); within that end_day the newest by stamp."""
    a = _iso(at)
    cs = [c for c in usable_captures(sp, ctx) if c["end_day"] <= a]
    return max(cs, key=lambda c: (c["end_day"], c["stamp"])) if cs else None


def _cn_rows(sp, md5, ctx):
    """One capture's rows: {norm(name): [(name, packing, units, k20), ...]} and {k20: [(name, packing, units), ...]} -- cached per md5."""
    key = ("cn", md5)
    if key not in ctx.c:
        by_n, by_k = {}, {}
        for r in sp.q("SELECT name, packing, k20, units FROM sp_close_name WHERE md5=?", md5):
            by_n.setdefault(norm(r["name"]), []).append((str(r["name"]), str(r["packing"] or ""), float(r["units"] or 0), str(r["k20"] or "")))
            by_k.setdefault(str(r["k20"] or ""), []).append((str(r["name"]), str(r["packing"] or ""), float(r["units"] or 0)))
        ctx.c[key] = (by_n, by_k)
    return ctx.c[key]


# ------------------------------------------------------------------ the start-of-day closing (S587, D740; R2-B2) -- the verdict record
START_DDL = ("CREATE TABLE IF NOT EXISTS stock_start_capture (md5 TEXT PRIMARY KEY, as_on TEXT, stamp_iso TEXT, end_day TEXT, "
             "verdict TEXT NOT NULL, reason TEXT, checked_at TEXT, built TEXT, prev_md5 TEXT, n_keys INTEGER, n_excluded INTEGER, "
             "n_unexplained INTEGER, detail TEXT)")              # one row per capture md5; pending -> a final verdict once (a record, never re-judged)
START_FINAL = ("accepted", "set_aside")


def _ensure_start(con):
    con.execute(START_DDL)


def _start_settings(con, ctx):
    """(count.start_capture on?, count.start_unexplained_max) through stock_watch.settings -- the one settings reader -- read once per Ctx;
    the defaults (on, 3) when it cannot be read."""
    if "startset" not in ctx.c:
        on, mx = True, 3
        try:
            S = _sw().settings(con)
            on = bool(S.get("start_capture", True))
            mx = int(S.get("start_unexplained_max", 3))
        except Exception:                                     # noqa: BLE001
            pass
        ctx.c["startset"] = (on, max(0, mx))
    return ctx.c["startset"]


def _start_rows(con, ctx):
    """{md5: row dict} -- every stock_start_capture row (read once per Ctx; {} with no connection or no table)."""
    if "startrows" not in ctx.c:
        rows = {}
        if con is not None and _has(con, "stock_start_capture"):
            try:
                for r in con.execute("SELECT md5, as_on, stamp_iso, end_day, verdict, reason, checked_at, built, prev_md5, n_keys, n_excluded, n_unexplained, detail "
                                     "FROM stock_start_capture"):
                    rows[str(r[0])] = dict(md5=str(r[0]), as_on=r[1], stamp_iso=r[2], end_day=r[3], verdict=str(r[4] or "pending"), reason=r[5] or "",
                                           checked_at=r[6], built=r[7], prev_md5=r[8], n_keys=r[9], n_excluded=r[10], n_unexplained=r[11], detail=r[12])
            except sqlite3.Error:
                rows = {}
        ctx.c["startrows"] = rows
    return ctx.c["startrows"]


def _may_write(con, ctx=None):
    """A connection that may take the verdict's write: present and not inside the caller's own transaction (its pending writes are never
    committed by this module). A read-only caller says so on its Ctx (read_only=True) and the judge stays out -- the capture stays as
    recorded (F-943)."""
    if ctx is not None and getattr(ctx, "read_only", False):
        return False
    try:
        return con is not None and not con.in_transaction
    except Exception:                                         # noqa: BLE001
        return False


def _start_apply(caps, ctx):
    """For every START capture, in stamp order: the switch; the recorded verdict (or, when the context's connection may write and the capture
    is within LATE_DAYS with no final verdict yet, the verdict judged now and written); accepted -> usable with end_day = D-1."""
    starts = [c for c in caps if c["start"]]
    if not starts:
        return
    con = ctx.con
    on, mx = _start_settings(con, ctx)
    if not on:
        for c in starts:
            c["verdict"] = "off"
        return
    rows = _start_rows(con, ctx)
    recent = (today() - dt.timedelta(days=LATE_DAYS)).isoformat()
    for c in starts:
        v = rows.get(c["md5"])
        if (v is None or v["verdict"] not in START_FINAL) and c["as_on"] >= recent and _may_write(con, ctx):
            nv = _judge_start(con, ctx.sp, c, caps, ctx, mx, v)
            if nv is not None:
                v = nv
                rows[c["md5"]] = v
        c["verdict"] = (v or {}).get("verdict") or "pending"
        if c["verdict"] == "accepted":
            c["end_day"], c["usable"] = c["start_day"], True


def _judge_start(con, sp, S, caps, ctx, mx, old):
    """start_ready -> verify_start -> the row written (INSERT when none; UPDATE while pending). Returns the row, or None when it could not be
    judged or written (the capture stays as it was)."""
    try:
        _ensure_start(con)
        ready_, why = start_ready(con, sp, S, ctx)
        if ready_:
            row = verify_start(con, sp, S, caps, ctx, mx)
        else:
            row = dict(verdict="pending", reason=why, prev_md5=None, n_keys=None, n_excluded=None, n_unexplained=None, detail={})
        row.update(md5=S["md5"], as_on=S["as_on"], stamp_iso=S["stamp_iso"], end_day=S["start_day"], checked_at=dt.datetime.now().replace(microsecond=0).isoformat(),
                   built=_built(sp))
        det = json.dumps(row.get("detail") or {}, ensure_ascii=False, sort_keys=True, default=str)
        if old is None:
            con.execute("INSERT OR IGNORE INTO stock_start_capture (md5, as_on, stamp_iso, end_day, verdict, reason, checked_at, built, prev_md5, n_keys, n_excluded, "
                        "n_unexplained, detail) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (row["md5"], row["as_on"], row["stamp_iso"], row["end_day"], row["verdict"], row["reason"], row["checked_at"], row["built"], row["prev_md5"],
                         row["n_keys"], row["n_excluded"], row["n_unexplained"], det))
        else:
            con.execute("UPDATE stock_start_capture SET verdict=?, reason=?, checked_at=?, built=?, prev_md5=?, n_keys=?, n_excluded=?, n_unexplained=?, detail=? "
                        "WHERE md5=? AND verdict NOT IN ('accepted','set_aside')",
                        (row["verdict"], row["reason"], row["checked_at"], row["built"], row["prev_md5"], row["n_keys"], row["n_excluded"], row["n_unexplained"], det, row["md5"]))
        con.commit()
        row["detail"] = det
        return row
    except Exception as ex:                                   # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        print("stock_figure: start capture %s (%s) stays pending: %s" % (S["md5"][:8], S["stamp_iso"], str(ex)[:160]), file=sys.stderr)
        return None


def _built(sp):
    try:
        return str((sp.q("SELECT value FROM sp_meta WHERE key='built'") or [{"value": ""}])[0]["value"] or "")
    except Exception:                                         # noqa: BLE001
        return ""


def start_ready(con, sp, S, ctx=None):
    """(ready, why) -- a start capture printed D can be judged once the spine's sale reach has D (the day's sale report is in: the next
    morning at the earliest -- a start capture is never used on its own day) AND the purchase side covers it (purchase_cover on the closing
    as it would stand, end_day D-1). why: 'sale_short' | 'pur_short' | ''. Never set aside for a short reach (R2-B2)."""
    ctx = _ctx(con, sp, ctx)
    R = _reach_once(sp, ctx)
    if not R or str(R.get("last_sale") or "") < str(S["as_on"]):
        return False, "sale_short"
    c = dict(S, end_day=S["start_day"])
    if not purchase_cover(ctx.con, sp, c, R, ctx):
        return False, "pur_short"
    return True, ""


def _bal(sp, d, ctx):
    """{k20: the spine's own stock at the end of day d} = SUM(sp_move.units) with date <= d, OPENING included. Once per (Ctx, d)."""
    ck = ("bal", str(d)[:10])
    if ck not in ctx.c:
        ctx.c[ck] = {str(r["k"]): float(r["u"] or 0) for r in sp.q("SELECT k20 AS k, SUM(units) AS u FROM sp_move WHERE date<=? GROUP BY k20", str(d)[:10]) if r["k"]}
    return ctx.c[ck]


def _sales_on(sp, d, ctx):
    """{k20: |units sold| on day d} (SALE units are negative in sp_move -- the absolute sum). Once per (Ctx, d)."""
    ck = ("salesD", str(d)[:10])
    if ck not in ctx.c:
        ctx.c[ck] = {str(r["k"]): abs(float(r["u"] or 0)) for r in sp.q("SELECT k20 AS k, SUM(units) AS u FROM sp_move WHERE kind='SALE' AND date=? GROUP BY k20", str(d)[:10]) if r["k"]}
    return ctx.c[ck]


def _purchases_on(sp, d, ctx):
    """{k20: (rows, signed units)} of PURCHASE / PURCHASE_RETURN dated d. Once per (Ctx, d)."""
    ck = ("purD", str(d)[:10])
    if ck not in ctx.c:
        ctx.c[ck] = {str(r["k"]): (int(r["n"] or 0), float(r["u"] or 0)) for r in
                     sp.q("SELECT k20 AS k, COUNT(*) AS n, SUM(units) AS u FROM sp_move WHERE kind IN ('PURCHASE','PURCHASE_RETURN') AND date=? GROUP BY k20", str(d)[:10]) if r["k"]}
    return ctx.c[ck]


def _units_by_key(sp, md5, ctx):
    """{k20: units} of one capture (the '' key dropped) and {k20: its first printed name}."""
    by_k = _cn_rows(sp, md5, ctx)[1]
    return ({k: float(sum(u for (_n, _p, u) in rows)) for k, rows in by_k.items() if k},
            {k: rows[0][0] for k, rows in by_k.items() if k and rows})


def _start_excluded(con, sp, S, P, ctx):
    """{cause: set(k20)} -- the keys with KNOWN non-spine Marg work between the previous verified capture P and the start capture S:
      vouchers  count-voucher batches first entered in (P.stamp, S.stamp] (stock_voucher_entered's first non-empty row of a batch entered now,
                the rule of stock_app._s446_window; its lines, not voided, through key_of);
      fix       amir_job 'fix:%' rows with done_at in the window (his 'Aaj ke item theek kar diye' tap, or seen in Marg);
      consume   the owner's consumption list (loss_piles.settings: stock.consume_items), through key_of;
      purchase  keys with a PURCHASE / PURCHASE_RETURN dated the printed day D in sp_move (inside the capture when entered before it);
      bill_new  keys of a purchase bill first seen (purchase_bill.first_seen_day) on or after P's own day (a bill first seen on P's day is
                undecidable: excluded too), its lines found in sp_purchase_line by supplier key, bill number and date."""
    lo, hi = _ts(P["stamp_iso"]), _ts(S["stamp_iso"])
    D = S["as_on"]
    out = dict(vouchers=set(), fix=set(), consume=set(), purchase=set(), bill_new=set())
    con = ctx.con if ctx.con is not None else con
    if con is None:
        out["purchase"] = set(_purchases_on(sp, D, ctx))
        return out
    try:
        if _has(con, "stock_voucher_entered") and _has(con, "stock_voucher_line"):
            ent, first = {}, {}
            for cid, rno, kind, bno, vno, at in con.execute("SELECT count_id, round_no, kind, batch_no, marg_voucher_no, at FROM stock_voucher_entered ORDER BY id"):
                k = (cid, rno, kind, bno)
                if str(vno or "").strip():
                    ent[k] = True
                    first.setdefault(k, _ts(at))
                else:
                    ent.pop(k, None)
            win = {k for k in ent if first.get(k) and lo < first[k] <= hi}
            if win:
                vf = (" AND NOT EXISTS (SELECT 1 FROM stock_voucher_void v WHERE v.count_id=l.count_id AND v.round_no=l.round_no AND v.kind=l.kind AND v.batch_no=l.batch_no)"
                      if _has(con, "stock_voucher_void") else "")
                for cid, rno, kind, bno, item in con.execute("SELECT count_id, round_no, kind, batch_no, item FROM stock_voucher_line l WHERE 1=1" + vf):
                    if (cid, rno, kind, bno) in win:
                        out["vouchers"].add(key_of(sp, item, ctx))
    except sqlite3.Error:
        pass
    try:
        if _has(con, "amir_job"):
            for subj, at in con.execute("SELECT subject, done_at FROM amir_job WHERE key LIKE 'fix:%' AND done_at IS NOT NULL"):
                t = _ts(at)
                if t and lo < t <= hi:
                    out["fix"].add(key_of(sp, subj, ctx))
    except sqlite3.Error:
        pass
    try:
        import loss_piles                                     # noqa: PLC0415 -- beside this file; stdlib only at module level
        for nm in loss_piles.settings(con).get("consume_items") or []:
            out["consume"].add(key_of(sp, nm, ctx))
    except Exception:                                         # noqa: BLE001
        pass
    out["purchase"] = set(_purchases_on(sp, D, ctx))
    try:
        if _has(con, "purchase_bill"):
            pl = {}
            for r in sp.q("SELECT supkey, bill, date, k20 FROM sp_purchase_line"):
                pl.setdefault((str(r["supkey"] or ""), _bill(r["bill"]), str(r["date"] or "")[:10]), set()).add(str(r["k20"] or ""))
            sk = _sw().supkey
            for sn, sup, bno, bdt in con.execute("SELECT supplier_norm, supplier, bill_no, bill_date FROM purchase_bill WHERE first_seen_day >= ?", (lo[:10],)):
                for key in {(sk(sn), _bill(bno), str(bdt or "")[:10]), (sk(sup), _bill(bno), str(bdt or "")[:10])}:
                    out["bill_new"] |= {k for k in pl.get(key, set()) if k}
    except sqlite3.Error:
        pass
    return out


def verify_start(con, sp, S, caps, ctx=None, mx=3):
    """R2-B2, the one test: P = the newest usable capture (accepted or clean) with end_day <= D-1 and stamp < S.stamp (none -> pending,
    no_prev). For every key of S or P: change = (units_S - bal(D-1)) - (units_P - bal(P.end_day)) -- the change in the Marg-minus-spine
    offset, never an absolute compare. The excluded keys (_start_excluded) are set apart by cause. An unexcluded key with change < 0 and
    |change| <= its sales dated D -> set_aside 'sale_before'; more than `mx` other unexcluded keys with |change| >= 0.5 -> set_aside
    'unexplained'; else accepted (those keys listed: approx on this capture). Returns the row (verdict, reason, prev_md5, n_*, detail)."""
    ctx = _ctx(con, sp, ctx)
    D, d1 = S["as_on"], S["start_day"]
    prev = [c for c in caps if c["usable"] and c["end_day"] and c["end_day"] <= d1 and c["stamp"] < S["stamp"] and c["md5"] != S["md5"]]
    if not prev:
        return dict(verdict="pending", reason="no_prev", prev_md5=None, n_keys=None, n_excluded=None, n_unexplained=None, detail={})
    P = max(prev, key=lambda c: c["stamp"])
    uS, nS = _units_by_key(sp, S["md5"], ctx)
    uP, nP = _units_by_key(sp, P["md5"], ctx)
    names = dict(nP)
    names.update(nS)
    bS, bP = _bal(sp, d1, ctx), _bal(sp, P["end_day"], ctx)
    salesD = _sales_on(sp, D, ctx)
    keys = sorted(set(uS) | set(uP))
    change = {k: (uS.get(k, 0.0) - bS.get(k, 0.0)) - (uP.get(k, 0.0) - bP.get(k, 0.0)) for k in keys}
    exc = _start_excluded(con, sp, S, P, ctx)
    excl = set().union(*exc.values()) if exc else set()
    sale_before, unexpl = [], []
    for k in keys:
        if k in excl:
            continue
        ch = change[k]
        if abs(ch) < 0.5:
            continue
        if ch < 0 and salesD.get(k, 0.0) > 0 and abs(ch) <= salesD[k] + 1e-9:
            sale_before.append((k, names.get(k, k), round(ch, 2), salesD[k]))
        else:
            unexpl.append((k, names.get(k, k), round(ch, 2)))
    if sale_before:
        verdict, reason = "set_aside", "sale_before"
    elif len(unexpl) > int(mx):
        verdict, reason = "set_aside", "unexplained"
    else:
        verdict, reason = "accepted", ""
    detail = dict(prev=dict(md5=P["md5"], as_on=P["as_on"], stamp_iso=P["stamp_iso"], end_day=P["end_day"], start=bool(P.get("start"))),
                  max_unexplained=int(mx), sale_before=sale_before, unexplained=unexpl,
                  excluded={cause: sorted((k, names.get(k, k)) for k in ks if k in change) for cause, ks in exc.items()},
                  changed_excluded=sorted((k, names.get(k, k), round(change[k], 2)) for k in excl if k in change and abs(change[k]) >= 0.5))
    return dict(verdict=verdict, reason=reason, prev_md5=P["md5"], n_keys=len(keys), n_excluded=len(excl & set(keys)), n_unexplained=len(unexpl), detail=detail)


def start_marks(con, sp, cap, ctx=None):
    """{k20: reason} -- the keys of a START / EARLY capture whose figure is approximate (R2-B3, §3.1): 'purchase_on_start' for a key with a
    PURCHASE / PURCHASE_RETURN dated the printed day (inside the capture when entered before it; never added again by marg()); on an accepted
    start capture also 'start_unexplained' (the verdict's unexplained keys) and 'start_excluded' (a verification-excluded key with a sale dated
    D -- its D-sale cannot be told from the capture's). {} for an ordinary capture. Once per (Ctx, md5)."""
    ctx = _ctx(con, sp, ctx)
    if not cap or not (cap.get("start") or cap.get("early")):
        return {}
    ck = ("smarks", cap["md5"])
    if ck in ctx.c:
        return ctx.c[ck]
    out = {k: "purchase_on_start" for k in _purchases_on(sp, cap["as_on"], ctx)}
    if cap.get("start"):
        row = _start_rows(ctx.con, ctx).get(cap["md5"])
        try:
            d = json.loads((row or {}).get("detail") or "{}") if row else {}
        except ValueError:
            d = {}
        for x in d.get("unexplained") or []:
            out.setdefault(str(x[0]), "start_unexplained")
        salesD = _sales_on(sp, cap["as_on"], ctx)
        for _cause, ks in (d.get("excluded") or {}).items():
            for x in ks:
                if str(x[0]) in salesD:
                    out.setdefault(str(x[0]), "start_excluded")
    ctx.c[ck] = out
    return out


def morning_skip_keys(sp, cap, ctx=None):
    """start_marks for the proof table (stock_app._s524_table): {k20: reason} of a capture dict, {} for None."""
    ctx = _ctx(None, sp, ctx)
    return start_marks(ctx.con, sp, cap, ctx) if cap else {}


def _prev_capture(sp, c, ctx):
    """The usable capture standing for the newest end_day BEFORE c's (record_gaps' P -- the base of a between-two-closings judgment)."""
    earlier = [x["end_day"] for x in usable_captures(sp, ctx) if x["end_day"] and c.get("end_day") and x["end_day"] < c["end_day"]]
    return capture_for(sp, max(earlier), ctx) if earlier else None


def start_report(con, sp, ctx=None, days=7):
    """[dict] -- every start capture of the last `days` days with its verdict, reason, the deciding keys and the excluded keys by cause
    (`python3 stock_figure.py verify-start`, the installer's state step, the walk)."""
    ctx = _ctx(con, sp, ctx)
    lo = (today() - dt.timedelta(days=days)).isoformat()
    out = []
    rows = _start_rows(ctx.con, ctx)
    for c in captures(sp, ctx):
        if not c["start"] or c["as_on"] < lo:
            continue
        r = rows.get(c["md5"]) or {}
        try:
            d = json.loads(r.get("detail") or "{}") if r else {}
        except ValueError:
            d = {}
        out.append(dict(md5=c["md5"][:8], as_on=c["as_on"], stamp_iso=c["stamp_iso"], start_day=c["start_day"], verdict=c["verdict"], reason=r.get("reason") or "",
                        usable=c["usable"], n_keys=r.get("n_keys"), n_excluded=r.get("n_excluded"), n_unexplained=r.get("n_unexplained"),
                        prev=(d.get("prev") or {}), sale_before=d.get("sale_before") or [], unexplained=d.get("unexplained") or [],
                        excluded={k: len(v) for k, v in (d.get("excluded") or {}).items()}, changed_excluded=d.get("changed_excluded") or []))
    return out


# ------------------------------------------------------------------ identity (charter 12)
def _k_by_name(sp, ctx):
    if "kbn" not in ctx.c:
        m = {}
        if sp is not None and getattr(sp, "ok", False):
            for r in sp.q("SELECT name, k20 FROM sp_item"):
                m.setdefault(norm(r["name"]), str(r["k20"] or ""))
        ctx.c["kbn"] = m
    return ctx.c["kbn"]


def _accepted_seen(con, rids):
    """{rename_id: [seen_name...]} -- the owner's ACCEPTED sightings (marg_item_rename_event, event 'accepted') for these rename ids only.
    item_alias has no reader for an accepted seen_name (its questions() lists the OPEN ones); this read is item_alias's to own at its next
    kit (README)."""
    out = {}
    if not rids or not _has(con, "marg_item_rename_event"):
        return out
    try:
        q = ",".join("?" * len(rids))
        for r in con.execute("SELECT rename_id, seen_name FROM marg_item_rename_event WHERE event='accepted' AND seen_name IS NOT NULL AND rename_id IN (%s) ORDER BY id" % q, list(rids)):
            if str(r[1] or "").strip():
                out.setdefault(int(r[0]), []).append(str(r[1]))
    except sqlite3.Error:
        pass
    return out


def _rename_groups(con, ctx):
    """[set of printed forms of ONE renamed item] from the ticked, not-taken-back renames (item_alias.done_rows): old name, new name, the
    accepted seen_names. {norm(form): group index} beside it. Cached in the ctx."""
    if "ren" in ctx.c:
        return ctx.c["ren"]
    groups, index = [], {}
    if con is not None:
        try:
            rows = _ia().done_rows(con)
        except Exception:                                     # noqa: BLE001 -- no rename memory: a name is its own only form
            rows = []
        acc = _accepted_seen(con, [int(r["id"]) for r in rows]) if rows else {}
        for r in rows:
            g = [str(r["old_name"]), str(r["new_name"])] + [s for s in acc.get(int(r["id"]), []) if s]
            seen, forms = set(), []
            for f in g:
                if norm(f) not in seen:
                    seen.add(norm(f))
                    forms.append(f)
            gi = len(groups)
            groups.append(forms)
            for f in forms:
                index.setdefault(norm(f), gi)
    ctx.c["ren"] = (groups, index)
    return ctx.c["ren"]


def printed_forms(con, name, ctx=None):
    """The name, its rename partner and the accepted seen_names (one item, every spelling Marg or the count has printed for it)."""
    ctx = _ctx(con, None, ctx)
    groups, index = _rename_groups(ctx.con, ctx)
    gi = index.get(norm(name))
    out = [str(name)]
    if gi is not None:
        for f in groups[gi]:
            if norm(f) != norm(name):
                out.append(f)
    return out


def arrival_forms(con, name, ctx=None):
    """S628 (D761): printed_forms PLUS the name's Marg partners from the one name list (med_names: THIO Q AP TAB for THIO Q AP) -- read ONLY
    where a bill line is matched to an order line (_line_forms: carried, rule b, the family's bill). printed_forms itself is unchanged, so a
    stock figure, a count, a closing and a split are per Marg item exactly as before."""
    ctx = _ctx(con, None, ctx)
    out = list(printed_forms(ctx.con, name, ctx))
    for f in _same(ctx, name):
        if norm(f) not in {norm(x) for x in out}:
            out.append(f)
    return out


def _same(ctx, name):
    """S628: med_names.same_items(name) read once per name and Ctx -- the other Marg items that are this medicine; [] when the list is absent
    or unreadable (fail-soft: the estate reads as before S628). Plain SQL -- it never calls key_of (no recursion)."""
    ck = ("same", norm(name))
    if ck not in ctx.c:
        try:
            import med_names                                  # noqa: PLC0415 -- beside this file (S628); it never imports stock_figure at import
            ctx.c[ck] = list(med_names.same_items(ctx.con, name)) if ctx.con is not None else []
        except Exception:                                     # noqa: BLE001
            ctx.c[ck] = []
    return ctx.c[ck]


def _same_keys(sp, name, k, ctx):
    """S628: the spine keys of the name's Marg partners other than its own key k (each read by key_of: the partner's own sp_item key)."""
    out = []
    for f in _same(ctx, name):
        try:
            k2 = key_of(sp, f, ctx)
        except Exception:                                     # noqa: BLE001
            continue
        if k2 and k2 != k and k2 not in out:
            out.append(k2)
    return out


def key_of(sp, name, ctx=None):
    """The one identity (charter 12): 1. sp_item.k20 for the printed name, spacing and case ignored; 2. else through the ticked renames --
    the partner name and the accepted seen_names, each tried through step 1; 3. else sp.key(name) (the spine's alias key)."""
    ctx = _ctx(None, sp, ctx)
    ck = ("key", norm(name))
    if ck in ctx.c:
        return ctx.c[ck]
    m = _k_by_name(sp, ctx)
    k = m.get(norm(name))
    if not k and ctx.con is not None:
        for f in printed_forms(ctx.con, name, ctx)[1:]:
            k = m.get(norm(f))
            if k:
                break
    if not k:
        try:
            k = sp.key(name)
        except Exception:                                     # noqa: BLE001
            k = re.sub(r"\s+", " ", str(name or "").strip())[:20].strip()
    ctx.c[ck] = k
    return k


# ------------------------------------------------------------------ S613 (F-951): a size of a split shared key -- read only where a reader spans dates
SPLIT_RE = re.compile(r"\(split (\d{4}-\d{2}-\d{2}) from (.+)\)\s*$")     # the strict pattern of spine_build's rename_family note (R1-B2)


def _clip20(n):
    """spine_build.K, verbatim: the first 20 characters, spaces collapsed -- the clip a rename_family note names its old key by."""
    return re.sub(r"\s+", " ", str(n or "").strip())[:20].strip()


def _split_warn(ctx, what):
    """One stderr line per row and Ctx: a split that cannot be read is no split (today's figure), never a typed date."""
    ck = ("split_warn", what)
    if ck not in ctx.c:
        ctx.c[ck] = True
        print("stock_figure: S613 split not read -- %s (today's figure kept)" % str(what)[:200], file=sys.stderr)


def _split_rows(sp, ctx):
    """{new_k: dict(new_k, old_k, day, old_clip, new_name)} from the spine alone (ctx.con only cross-checks): every sp_alias row of kind
    'rename_family' whose note parses by SPLIT_RE; new_k = the alias (= _k_by_name of its printed name in sp_item); old_k = the one sp_item key
    (not a rename_family key) whose printed names clip to the note's old clip -- for KNEE IMMOBILIZER the rules family 'KNEE IMMOBILI?ER UNI
    (family)' -- and, with a connection, the key _k_by_name gives the rename memory's old name; day cross-checked against the old key's
    RENAME_SPLIT move date where that row exists. Cached in the Ctx."""
    if "splits" in ctx.c:
        return ctx.c["splits"]
    out = {}
    try:
        rows = (sp.q("SELECT alias, k20, source FROM sp_alias WHERE kind='rename_family' ORDER BY alias")
                if (sp is not None and getattr(sp, "ok", False)) else [])
    except Exception:                                         # noqa: BLE001 -- no alias table: no split
        rows = []
    if rows:
        aliases = {str(r["alias"] or "") for r in rows}
        names = {}
        try:
            for r in sp.q("SELECT name, k20 FROM sp_item"):
                names.setdefault(str(r["k20"] or ""), []).append(str(r["name"] or ""))
        except Exception:                                     # noqa: BLE001
            names = {}
        by_clip = {}
        for k, ns in names.items():
            if k and k not in aliases:
                for n in ns:
                    by_clip.setdefault(_clip20(n), set()).add(k)
        kbn = _k_by_name(sp, ctx)
        for r in rows:
            new_k = str(r["alias"] or "")
            m = SPLIT_RE.search(str(r["source"] or ""))
            if not m or str(r["k20"] or "") != new_k:
                _split_warn(ctx, "%s: its rename_family note does not read '(split YYYY-MM-DD from <old>)'" % new_k)
                continue
            day, clip = m.group(1), m.group(2).strip()
            try:
                dt.date.fromisoformat(day)
            except ValueError:
                _split_warn(ctx, "%s: the split day '%s' is not a date" % (new_k, day))
                continue
            nn = sorted(n for n in names.get(new_k, []) if kbn.get(norm(n)) == new_k)
            if not nn:
                _split_warn(ctx, "%s: no printed name of sp_item stands under it" % new_k)
                continue
            olds = by_clip.get(clip, set())
            if len(olds) != 1:
                _split_warn(ctx, "%s: the old clip '%s' is %d keys, not one" % (new_k, clip, len(olds)))
                continue
            old_k = next(iter(olds))
            if ctx.con is not None:
                cand = {kbn.get(norm(f)) for f in printed_forms(ctx.con, nn[0], ctx)[1:]} - {None, "", new_k} - aliases
                if cand and old_k not in cand:
                    _split_warn(ctx, "%s: the rename memory's old name is under %s, not %s" % (new_k, sorted(cand), old_k))
                    continue
            try:
                mv = {str(x["d"]) for x in sp.q("SELECT DISTINCT date AS d FROM sp_move WHERE k20=? AND kind='RENAME_SPLIT'", old_k)}
            except Exception:                                 # noqa: BLE001
                mv = set()
            if mv and mv != {day}:
                _split_warn(ctx, "%s: the note says %s, the old key's RENAME_SPLIT says %s" % (new_k, day, sorted(mv)))
                continue
            out[new_k] = dict(new_k=new_k, old_k=old_k, day=day, old_clip=clip, new_name=nn[0])
    ctx.c["splits"] = out
    return out


def split_of(sp, name, ctx=None):
    """S613 (F-951): THE ONE PLACE THE SPLIT IS KNOWN. None, or dict(old_k, new_k, day, old_clip, new_name) for a printed name (old or new,
    or an accepted seen_name) of one of the sizes S605's spine split off a shared key. Derived from the spine (_split_rows); the connection
    only widens the name to its printed forms (an OLD name reaches its size only through the rename memory). Cached in the Ctx."""
    ctx = _ctx(None, sp, ctx)
    ck = ("split", norm(name))
    if ck in ctx.c:
        return ctx.c[ck]
    out = None
    rows = _split_rows(sp, ctx)
    if rows:
        kbn = _k_by_name(sp, ctx)
        for f in printed_forms(ctx.con, name, ctx):
            s = rows.get(kbn.get(norm(f)) or "")
            if s is not None:
                out = s
                break
    ctx.c[ck] = out
    return out


def split_members(sp, s, ctx=None):
    """S613 (R1-C3): the old key's members at the split -- family() within the NEWEST usable capture standing for a day on or before the split
    day that prints the old key, folded by printed_forms as family() does. A split-day capture printing only the new names does not print the
    old key; one printing spellings no count holds (11-10 09:52: 'SHOULDER IMMOBILISE L UNISON', not in the rename memory) cannot apportion
    the count, so the newest capture whose every member reaches a counted item (base()) is taken -- else the newest printing the old key."""
    ctx = _ctx(None, sp, ctx)
    ck = ("split_mem", s["old_k"])
    if ck not in ctx.c:
        have = {str(r["md5"]) for r in sp.q("SELECT DISTINCT md5 FROM sp_close_name WHERE k20=?", s["old_k"])}
        cs = sorted([c for c in usable_captures(sp, ctx) if c["end_day"] <= s["day"] and c["md5"] in have],
                    key=lambda c: (c["end_day"], c["stamp"]), reverse=True)
        pick = None
        if ctx.con is not None:
            for c in cs:
                fam = family(sp, s["old_k"], c["md5"], ctx)
                if fam and all(base(ctx.con, m[0], ctx) is not None for m in fam):
                    pick = fam
                    break
        if pick is None:
            pick = family(sp, s["old_k"], cs[0]["md5"] if cs else None, ctx)
        ctx.c[ck] = pick
    return ctx.c[ck]


def split_share(con, sp, name, s, ctx=None, exclude_id=None):
    """S613: (share, n) -- shelf()'s share rule over split_members: the size's counted base over the members' (below zero as 0); 1/n when
    nothing is counted. marg() reads it for a capture on or before the split day; shelf() computes the same inline over the same members."""
    ctx = _ctx(con, sp, ctx)
    mine = base(con, name, ctx, exclude_id)
    bases = [b for b in (base(con, m[0], ctx, exclude_id) for m in split_members(sp, s, ctx)) if b is not None]
    if mine is not None and not any(norm(b["item"]) == norm(mine["item"]) for b in bases):
        bases.append(mine)
    tot = sum(max(0.0, b["qty"]) for b in bases)
    n = len(bases)
    if mine is not None and tot > 0:
        return max(0.0, mine["qty"]) / tot, n
    return 1.0 / max(1, n), n


def split_moves(sp, s, share, d_from, d_to, incl_from=False, net=False):
    """S613 (F-951): THE ONE HELPER for a split size's movements over (d_from, d_to] (the count day's sales in with incl_from, as moves()): the
    OLD key's over (d_from, min(d_to, split day)] times the size's share, plus the NEW key's over (max(d_from, split day), d_to]. Returns
    (sold, returned, bought) -- or, net=True, the net of MOVE_KINDS (spine_move's figure). shelf(), marg() and spine_move() read it."""
    day, d_from, d_to = s["day"], str(d_from)[:10], str(d_to)[:10]
    if net:
        v = 0.0
        if d_from < day:
            v += share * spine_move(sp, s["old_k"], d_from, min(d_to, day))
        return v + spine_move(sp, s["new_k"], max(d_from, day), d_to)
    so = rt = bo = 0.0
    if d_from <= day:
        a, b, c = moves(sp, s["old_k"], d_from, min(d_to, day), incl_from)
        so, rt, bo = share * a, share * b, share * c
    a, b, c = moves(sp, s["new_k"], max(d_from, day), d_to, incl_from if d_from > day else False)
    return so + a, rt + b, bo + c


def family(sp, k20, md5, ctx=None):
    """The printed names under the key WITHIN that capture (sp_close_name), two forms of one renamed item folded into one member
    (printed_forms). When the key is absent from the capture: the members of the newest capture that prints the key -- never sp_item,
    whose last_seen the salt list moves for every item Marg holds (R3-C4). Returns [[form, ...], ...]; more than one member = a family."""
    ctx = _ctx(None, sp, ctx)
    ck = ("fam", k20, md5)
    if ck in ctx.c:
        return ctx.c[ck]
    names = []
    if md5:
        names = [n for (n, _p, _u) in _cn_rows(sp, md5, ctx)[1].get(k20, [])]
    if not names and ready(sp):
        r = sp.q("SELECT n.md5 AS md5 FROM sp_close_name n JOIN sp_export e ON e.md5=n.md5 WHERE n.k20=? ORDER BY e.stamp DESC LIMIT 1", k20)
        if r:
            names = [n for (n, _p, _u) in _cn_rows(sp, str(r[0]["md5"]), ctx)[1].get(k20, [])]
    groups, index = _rename_groups(ctx.con, ctx)
    members, seen = [], set()
    for n in sorted(set(names)):
        gi = index.get(norm(n))
        tag = ("g", gi) if gi is not None else ("n", norm(n))
        if tag in seen:
            for mbr in members:
                if mbr[0] == tag:
                    mbr[1].append(n)
            continue
        seen.add(tag)
        members.append((tag, [n]))
    out = [m[1] for m in members]
    ctx.c[ck] = out
    return out


# ------------------------------------------------------------------ Marg's figure
def closing(con, sp, name, at=None, ctx=None):
    """Marg's closing of the item at the newest usable capture with end_day <= at (today): BY NAME over every printed form of it, summed
    across packings (packings = the count; approx when more than 1); else the SUM over the same capture of the key (by='key', approx);
    else, when the key is known to sp_item with first_seen <= the capture's as_on (Marg prints only items with stock), units=0 by='absent';
    else None. Never sp_close."""
    ctx = _ctx(con, sp, ctx)
    cap = capture_at(sp, at, ctx)
    if cap is None:
        return None
    ck = ("cl", cap["md5"], norm(name))
    if ck in ctx.c:
        return ctx.c[ck]
    by_n, by_k = _cn_rows(sp, cap["md5"], ctx)
    hits = []
    for f in printed_forms(ctx.con, name, ctx):
        hits.extend(by_n.get(norm(f), []))
    out = None
    base = dict(as_on=cap["as_on"], end_day=cap["end_day"], stamp=cap["stamp"], stamp_iso=cap["stamp_iso"], md5=cap["md5"])
    if hits:
        packs = sorted({p for (_n, p, _u, _k) in hits})
        out = dict(base, units=float(sum(u for (_n, _p, u, _k) in hits)), by="name", approx=len(packs) > 1, packings=len(packs),
                   packing=hits[0][1], names=[n for (n, _p, _u, _k) in hits], key=hits[0][3])
    else:
        k = key_of(sp, name, ctx)
        krows = by_k.get(k, [])
        if krows:
            out = dict(base, units=float(sum(u for (_n, _p, u) in krows)), by="key", approx=True, packings=len({p for (_n, p, _u) in krows}),
                       packing=krows[0][1], names=[n for (n, _p, _u) in krows], key=k)
        else:
            fs = sp.q("SELECT MIN(first_seen) AS f, MIN(packing) AS p FROM sp_item WHERE k20=?", k)
            f = str((fs[0]["f"] if fs else "") or "")
            if f and f <= cap["as_on"]:
                out = dict(base, units=0.0, by="absent", approx=False, packings=0, packing=str((fs[0]["p"] if fs else "") or ""), names=[], key=k)
    ctx.c[ck] = out
    return out


def moves(sp, k20, d_from, d_to, incl_from=False):
    """(sold, returned, bought) units of the key between two days from the spine's own ledger (sp_move: SALE negative, SALE_RETURN positive,
    PURCHASE / PURCHASE_RETURN signed). The count day's sales in (incl_from=True), its purchases out (purchases always date > d_from)."""
    op = ">=" if incl_from else ">"
    r = sp.q("SELECT COALESCE(SUM(CASE WHEN kind='SALE' THEN -units ELSE 0 END),0) AS s, COALESCE(SUM(CASE WHEN kind='SALE_RETURN' THEN units ELSE 0 END),0) AS r "
             "FROM sp_move WHERE k20=? AND date %s ? AND date<=?" % op, k20, d_from, d_to)
    b = sp.q("SELECT COALESCE(SUM(CASE WHEN kind IN ('PURCHASE','PURCHASE_RETURN') THEN units ELSE 0 END),0) AS b FROM sp_move WHERE k20=? AND date>? AND date<=?",
             k20, d_from, d_to)
    return (float(r[0]["s"] or 0) if r else 0.0), (float(r[0]["r"] or 0) if r else 0.0), (float(b[0]["b"] or 0) if b else 0.0)


def spine_move(sp, k20, d_from, d_to, split=None, share=1.0):
    """The net of every movement kind the proof carries (MOVE_KINDS, never OPENING) over (d_from, d_to] -- what Marg's figure moved by.
    S613 (F-951): split = split_of()'s dict -> the split size's net through split_moves (the one helper), its share given."""
    if split is not None:
        return split_moves(sp, split, share, d_from, d_to, net=True)
    r = sp.q("SELECT COALESCE(SUM(units),0) AS u FROM sp_move WHERE k20=? AND date>? AND date<=? AND kind IN (%s)" % ",".join("?" * len(MOVE_KINDS)),
             k20, d_from, d_to, *MOVE_KINDS)
    return float(r[0]["u"] or 0) if r else 0.0


# ------------------------------------------------------------------ the arrivals: ONE rule for "Marg carries this arrival" (S583, charter 2)
def _arr_settings(con, ctx):
    """(arrival.bill_grace_days, arrival.back_days) through stock_watch.settings -- the one settings reader -- read once per Ctx."""
    if "arrset" not in ctx.c:
        g, b = 3, 2
        try:
            S = _sw().settings(con)
            g = int(S.get("bill_grace_days") or 3)
            b = int(S["back_days"]) if S.get("back_days") is not None else 2
        except Exception:                                     # noqa: BLE001
            pass
        ctx.c["arrset"] = (max(1, g), max(0, b))
    return ctx.c["arrset"]


def _reach_once(sp, ctx):
    """reach(sp) read once per Ctx (expired() reads the spine's purchase reach, never twice in one pass)."""
    if "reach" not in ctx.c:
        try:
            ctx.c["reach"] = reach(sp) if (sp is not None and getattr(sp, "ok", False)) else {}
        except Exception:                                     # noqa: BLE001
            ctx.c["reach"] = {}
    return ctx.c["reach"]


def _bill(b):
    """A bill number as a key: spacing and case folded, leading zeros dropped (the spine prints A.A.'s 467 as '0000467'; Marg's own line says '467')."""
    return re.sub(r"^0+(?=\d)", "", re.sub(r"\s+", "", str(b or "")).upper())


def arrival_moment(line):
    """The arrival moment as a datetime (finance.db's clock, IST): a tapped line's arrived_at, a scan-tied line's scan_at. None when unreadable."""
    s = str(line.get("arrived_at") or line.get("scan_at") or "").strip().replace(" ", "T")[:19]
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _line_forms(ctx, name):
    """S598: the set of spellings a bill line of THIS item may print, as the estate clips them -- {pad_norm(f[:27]), pad_norm(f)} over
    printed_forms (the name, its ticked rename partner, the accepted seen_names). A CLIPPED order spelling (27 letters or more: Marg's
    order report clips too) also takes every rename group that holds a form starting with it, so the clip still reaches its partner
    (R1-C2). pad_norm is stock_watch's (the clip _arrivals / scan_lines match an order line by). Cached per name and Ctx."""
    sw = _sw()
    name = str(name or "")
    ck = ("forms", norm(name))
    if ck in ctx.c:
        return ctx.c[ck]
    fs = list(arrival_forms(ctx.con, name, ctx))             # S628: the Marg partners too (arrival matching only)
    if len(name.strip()) >= 27:
        nn = norm(name)
        groups, _index = _rename_groups(ctx.con, ctx)
        for g in groups:
            if any(norm(f).startswith(nn) for f in g):
                fs.extend(g)
    out = set()
    for f in fs:
        out.add(sw.pad_norm(str(f)[:27]))
        out.add(sw.pad_norm(str(f)))
    out.discard("")
    ctx.c[ck] = out
    return out


def _siblings(sp, k20, ctx):
    """S598: True when more than one ITEM lives under the key -- sp_item's names under k20, two spellings of one renamed item folded into one
    member (the fold family() does). A key with one item is matched by the key alone, whatever Marg's clip printed. Cached per key and Ctx."""
    ck = ("sib", k20)
    if ck in ctx.c:
        return ctx.c[ck]
    names = []
    try:
        if sp is not None and getattr(sp, "ok", False):
            names = [str(r["name"] or "") for r in sp.q("SELECT DISTINCT name FROM sp_item WHERE k20=?", k20)]
    except Exception:                                         # noqa: BLE001
        names = []
    _groups, index = _rename_groups(ctx.con, ctx)
    tags = set()
    for n in names:
        if not n.strip():
            continue
        gi = index.get(norm(n))
        tags.add(("g", gi) if gi is not None else ("n", norm(n)))
    ctx.c[ck] = len(tags) > 1
    return ctx.c[ck]


def _matches(ctx, sp, k20, forms, sib, name27):
    """S598: THE one match of a bill line to an order line -- its printed name (name27, as Marg's BILL/ITEM WISE report clips it) in the
    line's forms; or the key alone when the key has no sibling (sib False). The only place a name27 is compared with forms."""
    sw = _sw()
    s = str(name27 or "")
    if sw.pad_norm(s) in forms or sw.pad_norm(s[:27]) in forms:
        return True
    return not sib


def _taken_lines(sp, k20, line_id, ctx):
    """S598 (rule b, per bill LINE; R1-B1): for every OTHER order line of the key that carries a billed_bill_no, one entry
    (its order's vendor key, _bill(its bill), ITS forms by _line_forms, sib of its key) -- a bill line is TAKEN when (supkey, bill) equals an
    entry's and _matches(entry.forms, entry.sib, its printed name) is True: the same match the other line itself used, so one bill line is never
    credited to two order lines of one item, whatever the two spellings. Read once per key and Ctx (a fresh Ctx per row keeps it honest)."""
    ck = ("taken", k20)
    if ck not in ctx.c:
        out = []
        try:
            if ctx.con is not None:
                for lid, item, bno, vendor in ctx.con.execute("SELECT l.id, l.item, l.billed_bill_no, o.vendor FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                                                               "WHERE COALESCE(l.billed_bill_no,'')<>''").fetchall() + _other_taken(ctx):
                    if key_of(sp, item, ctx) == k20:
                        out.append((int(lid), _sw().supkey(vendor), _bill(bno), _line_forms(ctx, item), _siblings(sp, k20, ctx)))
        except sqlite3.Error:
            out = []
        ctx.c[ck] = out
    me = int(line_id) if line_id is not None else None
    return [t for t in ctx.c[ck] if t[0] != me]


def _other_taken(ctx):
    """S628 (F-991): the order lines credited with ANOTHER dealer's bill line (other_bill_no) as rule (b) entries (id, item, bill, that dealer) --
    so one bill line is never credited twice. [] before S628's columns exist."""
    if "othtaken" not in ctx.c:
        try:
            ctx.c["othtaken"] = [tuple(r) for r in ctx.con.execute("SELECT id, item, other_bill_no, other_supplier FROM purchase_order_line "
                                                                    "WHERE COALESCE(other_bill_no,'')<>''")] if ctx.con is not None else []
        except sqlite3.Error:
            ctx.c["othtaken"] = []
    return list(ctx.c["othtaken"])


def _taken_split(sp, sx, line_id, ctx):
    """S613 (R1-B3): rule (b) for a split size -- _taken_lines' entries for every OTHER billed order line whose key is the size's old key or its
    new key (each entry's sib its own key's); the caller matches a bill line of the OLD key with sib True (by printed name only)."""
    ck = ("taken_split", sx["new_k"])
    if ck not in ctx.c:
        out = []
        try:
            if ctx.con is not None:
                for lid, item, bno, vendor in ctx.con.execute("SELECT l.id, l.item, l.billed_bill_no, o.vendor FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                                                               "WHERE COALESCE(l.billed_bill_no,'')<>''").fetchall() + _other_taken(ctx):
                    kk = key_of(sp, item, ctx)
                    if kk in (sx["old_k"], sx["new_k"]):
                        out.append((int(lid), _sw().supkey(vendor), _bill(bno), _line_forms(ctx, item), _siblings(sp, kk, ctx)))
        except sqlite3.Error:
            out = []
        ctx.c[ck] = out
    me = int(line_id) if line_id is not None else None
    return [t for t in ctx.c[ck] if t[0] != me]


def _split_lines(sp, sx, since_day, ctx):
    """S613 (F-951, R1-B3): a split size's bill lines dated on or after since_day -- its NEW key's lines (matched as today, the new key's sib)
    and its OLD key's lines (sib True: matched by printed name only, a sibling size's line never matches) in one list, ordered as
    _purchase_lines_of orders it (date, bill, seq): [(line, k20, sib)]."""
    ck = ("splines", sx["new_k"], since_day)
    if ck not in ctx.c:
        rows = [(p, sx["new_k"], _siblings(sp, sx["new_k"], ctx)) for p in _purchase_lines_of(sp, sx["new_k"], since_day, ctx)]
        rows += [(p, sx["old_k"], True) for p in _purchase_lines_of(sp, sx["old_k"], since_day, ctx)]
        rows.sort(key=lambda t: (str(t[0]["date"] or ""), str(t[0]["bill"] or ""), _seqkey(t[0]["seq"])))
        ctx.c[ck] = rows
    return ctx.c[ck]


def _seqkey(v):
    s = str(v if v is not None else "")
    return (0, int(s), "") if re.match(r"^-?\d+$", s) else (1, 0, s)


def _purchase_lines_of(sp, k20, since_day, ctx):
    """S598: the spine's PURCHASE LINES of the key dated on or after since_day (since_day '' = every line of the key), oldest first, the
    lines of one bill together in Marg's order: dict(supkey, bill, date, seq, name27, qty, free, units, supplier) -- ONE ROW PER BILL LINE
    (never summed by bill), the supplier's name from sp_purchase_bill when the spine has it."""
    ck = ("plines", k20, since_day)
    if ck not in ctx.c:
        try:
            rows = sp.q("SELECT l.supkey AS supkey, l.bill AS bill, l.date AS date, l.seq AS seq, l.name27 AS name27, l.qty AS qty, l.free AS free, l.units AS units, "
                        "l.packing AS packing, MAX(b.supplier) AS supplier FROM sp_purchase_line l LEFT JOIN sp_purchase_bill b ON b.supkey=l.supkey AND b.bill=l.bill AND b.date=l.date "
                        "WHERE l.k20=? AND l.direction='PURCHASE' AND l.date>=? GROUP BY l.supkey, l.bill, l.date, l.seq ORDER BY l.date, l.bill, l.seq", k20, since_day)
        except sqlite3.Error:
            rows = sp.q("SELECT supkey, bill, date, seq, name27, qty, free, units, packing, supkey AS supplier FROM sp_purchase_line WHERE k20=? AND direction='PURCHASE' "
                        "AND date>=? ORDER BY date, bill, seq", k20, since_day)
        ctx.c[ck] = rows
    return ctx.c[ck]


def carried(con, sp, line, ctx=None):
    """THE ONE RULE: the purchase LINE of Marg's that carries an arrival line, or None. `line` is the dict stock_watch._arrivals yields (line_id,
    item, vendor, order_at, arrived_at, billed_bill_no; scan_at for a scan-tied line). Returns dict(supplier, supkey, bill, date, units, qty,
    free, seq, the bill line's printed name, how) -- `how` the rule's letter; units / qty / free are THE MATCHED BILL LINE's (two batches of
    one item on one bill summed), never the family's. None while sp.ok is False (the spine unread: nothing is dropped). In order:
      (a) the line's own billed_bill_no (Marg's answer, S537) -> carried, whatever the spine shows (units None when no line of that bill
          matches: the figure unknown, the answer trusted);
      (b) a bill LINE that answered ANOTHER order line of the same item (by the same match) never carries this line -- S598, per line;
      (c) a purchase dated BEFORE the order day carries only from the order's own vendor key, dated within arrival.back_days before the order day;
      (d) a purchase from the order's own vendor key dated on or after the order day carries (the rule before S583);
      (e) a purchase from another supplier carries only when dated on or after the order day.
    S598 (F-942): a bill line is eligible only when it MATCHES the order line -- its printed name among the item's spellings (_line_forms /
    _matches), the key alone only for an item with no sibling under its key (_siblings): a sibling size never takes it. The first eligible
    matching line, oldest date first, wins. No matching line -> None, and the family's bill that carried OTHER sizes is kept for the owner's
    words (ctx ('fam_bill', line_id) -> arrivals_open). A carrying bill dated on or before the item's count day still drops the arrival: the
    goods are inside the count (the brief's named edge)."""
    ctx = _ctx(con, sp, ctx)
    if sp is None or not getattr(sp, "ok", False) or not isinstance(line, dict):
        return None
    ck = ("carried", line.get("line_id"), norm(line.get("item")), _sw().supkey(line.get("vendor")), str(line.get("order_at") or "")[:10], _bill(line.get("billed_bill_no")),
          bool(line.get("own_only")))                         # S628: own_only -- only the order's own dealer's bills (porders.detect_supplies)
    if ck in ctx.c:
        return ctx.c[ck]
    try:
        out = _carried(ctx, sp, line)
    except sqlite3.Error:
        out = None
    ctx.c[ck] = out
    return out


def _carried(ctx, sp, line):
    sw = _sw()
    k = key_of(sp, line.get("item"), ctx)
    own = sw.supkey(line.get("vendor"))
    forms = _line_forms(ctx, line.get("item"))
    sib = _siblings(sp, k, ctx)
    sx = split_of(sp, line.get("item"), ctx)                  # S613 (F-951): a split size reads its new key's lines and its old key's by name (R1-B3)
    same_k = _same_keys(sp, line.get("item"), k, ctx)         # S628 (D761): the keys of the Marg items that are this medicine (med_names)

    def lines_of(since):
        if sx is not None:
            rows = list(_split_lines(sp, sx, since, ctx))
        else:
            rows = [(p, k, sib) for p in _purchase_lines_of(sp, k, since, ctx)]
        if same_k:                                            # S628: a partner's lines join, each matched under its own key's sib, one order
            rows += [(p, k2, _siblings(sp, k2, ctx)) for k2 in same_k for p in _purchase_lines_of(sp, k2, since, ctx)]
            rows.sort(key=lambda t: (str(t[0]["date"] or ""), str(t[0]["bill"] or ""), _seqkey(t[0]["seq"])))
        return rows
    bno = _bill(line.get("billed_bill_no"))
    if bno:                                                   # (a): the lines of that bill that MATCH, summed; the newest bill of the number
        hit = [p for (p, pk, ps) in lines_of("") if _bill(p["bill"]) == bno and _matches(ctx, sp, pk, forms, ps, p["name27"])]
        if hit:
            top = max((str(p["date"] or "")[:10], str(p["supkey"] or "")) for p in hit)
            hit = [p for p in hit if (str(p["date"] or "")[:10], str(p["supkey"] or "")) == top]
        p = hit[0] if hit else {}
        return dict(supplier=str(line.get("vendor") or ""), supkey=str(p.get("supkey") or own), bill=str(line.get("billed_bill_no") or ""),
                    date=str(p.get("date") or line.get("billed_date") or "")[:10], units=(sum(float(x["units"] or 0) for x in hit) if hit else None),
                    qty=(sum(float(x["qty"] or 0) for x in hit) if hit else None), free=(sum(float(x["free"] or 0) for x in hit) if hit else None),
                    seq=(p.get("seq") if hit else None), name27=(str(p.get("name27") or "") if hit else ""), how="a",
                    packing=(str(p.get("packing") or "") if hit else ""))
    od = str(line.get("order_at") or "")[:10]
    try:
        lo = (dt.date.fromisoformat(od) - dt.timedelta(days=_arr_settings(ctx.con, ctx)[1])).isoformat()
    except ValueError:
        return None
    lid = line.get("line_id")
    taken = _taken_split(sp, sx, lid, ctx) if sx is not None else _taken_lines(sp, k, lid, ctx)
    for k2 in same_k:                                         # S628: rule (b) over every key of the medicine -- one bill line, one order line
        taken = list(taken) + [t for t in _taken_lines(sp, k2, lid, ctx) if t not in taken]
    hit, hkey = None, None
    for p, pk, ps in lines_of(lo):
        sk, d, b = str(p["supkey"] or ""), str(p["date"] or "")[:10], _bill(p["bill"])
        if hit is not None and (sk, b, d) != hkey:
            break                                             # the first matching bill's lines are summed (two batches); a later bill never joins
        if line.get("own_only") and not (own and sk == own):
            continue                                          # S628: the own dealer's bill first -- an older other-dealer line never hides it
        old_line = sx is not None and pk == sx["old_k"]       # S613: an old-key line is matched by printed name only, whoever matches it
        if any(t[1] == sk and t[2] == b and _matches(ctx, sp, pk, t[3], t[4] or old_line, p["name27"]) for t in taken):   # (b) per line
            continue
        if not _matches(ctx, sp, pk, forms, ps, p["name27"]):
            continue
        if d < od:
            how = "c" if (own and sk == own) else None        # (c)
        else:
            how = "d" if (own and sk == own) else "e"         # (d) / (e)
        if not how:
            continue
        if hit is None:
            hit = dict(supplier=str(p.get("supplier") or sk), supkey=sk, bill=str(p["bill"] or ""), date=d, units=float(p["units"] or 0),
                       qty=float(p["qty"] or 0), free=float(p["free"] or 0), seq=p["seq"], name27=str(p["name27"] or ""), how=how,
                       packing=str(p.get("packing") or ""))
            hkey = (sk, b, d)
        else:
            hit["units"] += float(p["units"] or 0)
            hit["qty"] += float(p["qty"] or 0)
            hit["free"] += float(p["free"] or 0)
    if hit is not None:
        return hit
    if lid is not None:
        ctx.c[("fam_bill", lid)] = _family_bill(ctx, sp, k, lo, od, own, forms, sib, sx)
    return None


def _family_bill(ctx, sp, k20, lo, od, own, forms, sib, split=None):
    """S598 (R1-C9): when no bill line matches the order line -- the family's bill that carried OTHER sizes: among the lines of the key
    since lo that pass the loop's own vendor-and-date test (c: the own vendor before the order day; d / e: any supplier on or after it) and
    do NOT match the line's forms (so only when sib is True), the newest bill -> dict(supplier, supkey, bill, date, sizes=[name27 as Marg
    printed it, deduped by pad_norm, that bill's lines of the key only]); None when there is none. A line already credited to the sibling
    order line still counts here: the clause says what the bill carried. Read by arrivals_open for the owner's words (stock_watch).
    S613 (F-951, R1-C4): for a split size (split = split_of's dict) the family spans the OLD family -- the old key's lines up to the split day
    plus each sibling size's new key lines after it, every one matched by printed name only (sib True)."""
    sw = _sw()
    best, lines = None, {}
    if split is None:
        src = [(p, sib) for p in _purchase_lines_of(sp, k20, lo, ctx)]
    else:
        src = [(p, True) for p in _purchase_lines_of(sp, split["old_k"], lo, ctx) if str(p["date"] or "")[:10] <= split["day"]]
        for s2 in sorted(_split_rows(sp, ctx).values(), key=lambda x: x["new_k"]):
            if s2["old_k"] == split["old_k"] and s2["new_k"] != split["new_k"]:
                src += [(p, True) for p in _purchase_lines_of(sp, s2["new_k"], lo, ctx) if str(p["date"] or "")[:10] > split["day"]]
        src.sort(key=lambda t: (str(t[0]["date"] or ""), str(t[0]["bill"] or ""), _seqkey(t[0]["seq"])))
    for p, psib in src:
        sk, d = str(p["supkey"] or ""), str(p["date"] or "")[:10]
        if d < od and not (own and sk == own):
            continue
        if _matches(ctx, sp, k20, forms, psib, p["name27"]):
            continue
        key = (d, sk, _bill(p["bill"]))
        lines.setdefault(key, []).append(p)
        if best is None or key > best:
            best = key
    if best is None:
        return None
    seen, sizes = set(), []
    for p in lines[best]:
        pn = sw.pad_norm(str(p["name27"] or ""))
        if pn and pn not in seen:
            seen.add(pn)
            sizes.append(str(p["name27"] or "").strip())
    p0 = lines[best][0]
    return dict(supplier=str(p0.get("supplier") or p0["supkey"] or ""), supkey=str(p0["supkey"] or ""), bill=str(p0["bill"] or ""), date=best[0], sizes=sizes)


def expired(con, sp, line, ctx=None):
    """True when carried() is None AND the spine's purchase reach has passed the arrival with its grace (arrival.bill_grace_days): last_pur is at
    or past the arrival day + grace AND stamp_iso(pur_stamp) is after the arrival moment + grace -- two ISO shapes; never a raw compare of the
    'YYYYMMDD-HHMMSS' stamp against an ISO moment (charter 11). covers() is not used. False while sp.ok is False, the reach is empty or the
    moment is unreadable: the arrival keeps counting (charter 1b)."""
    ctx = _ctx(con, sp, ctx)
    if sp is None or not getattr(sp, "ok", False) or not isinstance(line, dict):
        return False
    if carried(con, sp, line, ctx) is not None:
        return False
    R = _reach_once(sp, ctx)
    if not R or not R.get("last_pur") or not stamp_iso(R.get("pur_stamp")):
        return False
    m = arrival_moment(line)
    if m is None:
        return False
    due = m + dt.timedelta(days=_arr_settings(ctx.con, ctx)[0])
    return str(R["last_pur"])[:10] >= due.date().isoformat() and stamp_iso(R["pur_stamp"]) > due.replace(microsecond=0).isoformat()


def taps(con, sp, name, since_iso, ctx=None):
    """Units of the item's tapped arrivals after a moment that COUNT: no billed_bill_no (rule a: Marg answered), carried() None (in_spine False)
    and expired() False. stock_watch._arrivals lists the lines. Reported beside Marg's figure, added to the shelf figure."""
    ctx = _ctx(con, sp, ctx)
    try:
        return sum(_count_units(con, sp, a, ctx) for a in _sw()._arrivals(ctx.con, name, since_iso, sp, ctx=ctx)   # S928: the scanned bill's units when it speaks
                   if not str(a.get("billed_bill_no") or "").strip() and not a["in_spine"] and not expired(con, sp, a, ctx))
    except Exception:                                         # noqa: BLE001
        return 0.0


def s825_bill_judged(con, ctx=None):
    """S825 (F-1220, D883): {order line id: True | False} -- for each scan-tied open order line, whether the bill TIED to its order carries
    it: the tied scan's clearer copy (order_track.Ctx.head), usable as the tracker counts usable (not set aside, no rescan asked), as Claude
    read it, matched by THE TRACKER'S OWN MATCHER (order_track.match_lines: the item's printed forms and its learnt scan spellings, numbers
    and sizes agreeing). A line is judged only when one of its order's tied scans is usable and has its items read; otherwise -- a scan not
    read yet, a scan to redo, a scan before order.track_since, the scan store unreachable -- it is not judged and the old reading stands for
    it. {} when none is judged; None on any failure. READ ONLY (it calls nothing that writes; the connection's row factory is put back as it
    was). Once per Ctx."""
    ctx = _ctx(con, None, ctx)
    key = ("s825_judged",)
    if key in ctx.c:
        return ctx.c[key]
    con = ctx.con
    out = None
    rf = con.row_factory if con is not None else None
    try:
        con.row_factory = sqlite3.Row                         # as the tracker's own readers expect (its rescan list)
        rows = con.execute("SELECT l.id, l.item, l.order_id, o.vendor, o.supplier_norm, t.asset_bill_id FROM purchase_order_line l "
                           "JOIN purchase_order o ON o.id=l.order_id JOIN order_scan_tie t ON t.order_id=o.id WHERE t.arrived=1 "
                           "AND l.supplied IS NULL AND l.billed_qty IS NULL AND COALESCE(l.missing,0)=0 AND t.asset_bill_id IS NOT NULL").fetchall()
        out = {}
        if rows:
            import order_track as OT                          # noqa: PLC0415 -- beside this file
            octx = _s928_octx(ctx)                            # S928: the one scan context per Ctx (s825 and bill_units share it)
            if octx is None:
                out = None
            else:
                pa = OT._pa()
                by = {}
                for r in rows:
                    e = by.setdefault(int(r["order_id"]), dict(sn=r["supplier_norm"] or pa.supplier_key(r["vendor"] or ""), items={}, sids=set()))
                    e["items"][int(r["id"])] = r["item"]
                    e["sids"].add(int(r["asset_bill_id"]))
                for oid, e in by.items():
                    M = _s928_order_match(ctx, octx, OT, oid)   # S928: ONE match per order -- s825 and bill_units read the same hit
                    if M is None:
                        continue                              # no tied scan usable and read: not judged
                    for lid, it in e["items"].items():
                        out[lid] = it in M["hit"]
    except Exception:                                         # noqa: BLE001 -- fail-soft: the old reading
        out = None
    finally:
        if con is not None:
            con.row_factory = rf
    ctx.c[key] = out
    return out


def scan_lines(con, sp, item=None, since_iso="", ctx=None):
    """The scan-tied, unanswered order lines (S454 4.4: order_scan_tie.arrived=1; supplied and billed_qty NULL, missing 0) whose scan moment is
    after since_iso -- of one item (matched as _arrivals matches an order line: pad_norm(name[:27]) / pad_norm(name); seen, not touched, charter
    12) or of every item (None). In _arrivals' shape: arrived_at = scan_at, arrived_by 'scan', units = packs x pack_size, kind 'scan'.
    S825 (F-1220, D883): a line the dealer's scanned bill does NOT carry (s825_bill_judged False) has not arrived and is left out -- it stays
    on order (order_rules); a line not judged keeps the old reading."""
    ctx = _ctx(con, sp, ctx)
    con = ctx.con
    if con is None or not _has(con, "order_scan_tie"):
        return []
    sw = _sw()
    keys = {sw.pad_norm(str(item)[:27]), sw.pad_norm(str(item))} if item else None
    out = []
    try:
        rows = con.execute("SELECT l.id, l.item, l.packs, l.pack_size, o.vendor, o.created_at, o.id, MAX(t.scan_at) FROM purchase_order_line l "
                           "JOIN purchase_order o ON o.id=l.order_id JOIN order_scan_tie t ON t.order_id=o.id "
                           "WHERE t.arrived=1 AND l.supplied IS NULL AND l.billed_qty IS NULL AND COALESCE(l.missing,0)=0 "
                           "GROUP BY l.id HAVING MAX(t.scan_at)>? ORDER BY MAX(t.scan_at), l.id", (str(since_iso or ""),)).fetchall()
    except sqlite3.Error:
        return []
    judged = s825_bill_judged(con, ctx) if rows else None
    for lid, nm, packs, size, vendor, created, oid, scan_at in rows:
        if keys is not None and sw.pad_norm(str(nm)[:27]) not in keys and sw.pad_norm(str(nm)) not in keys:
            continue
        if judged and judged.get(int(lid)) is False:          # S825: not on the bill -- not arrived (on the way, order_rules)
            continue
        out.append(dict(line_id=lid, item=nm, packs=int(packs or 0), pack_size=int(size or 1), supplied=0, units=float(packs or 0) * float(size or 1),
                        arrived_at=str(scan_at or ""), arrived_by="scan", billed_qty=None, billed_bill_no="", billed_date="", vendor=vendor or "",
                        supkey=sw.supkey(vendor), order_id=oid, order_at=created, scan_at=str(scan_at or ""), kind="scan"))
    return out


def scan_arrivals(con, sp, item, since_iso, ctx=None):
    """Units of the item's scan-tied, unanswered lines (scan_lines) that COUNT: carried() None and expired() False, the arrival moment being
    scan_at. Moved here from shelf_figure (S583): the one rule. Fail-soft 0.0."""
    ctx = _ctx(con, sp, ctx)
    try:
        return sum(_count_units(con, sp, a, ctx) for a in scan_lines(con, sp, item, since_iso, ctx) if carried(con, sp, a, ctx) is None and not expired(con, sp, a, ctx))   # S928
    except Exception:                                         # noqa: BLE001
        return 0.0


def arrivals_open(con, sp, ctx=None):
    """Every tapped or scan-tied line that is EXPIRED and not carried, without a billed_bill_no: dict(line_id, item, units, at (the arrival
    moment), who ('scan' for a scan-tied line, else who tapped), vendor, order_id, kind 'tap' | 'scan', scan_tied (its order has a scan tie),
    family_bill (S598: the family's bill that carried OTHER sizes of the item -- dict(bill, date, sizes) -- or None)).
    Sorted by item, then moment. The owner's Needs-you (stock_watch.arrival_needs_you) names the scan-tied ones; an untied tap stays with D712."""
    ctx = _ctx(con, sp, ctx)
    con = ctx.con
    out = []
    if con is None or sp is None or not getattr(sp, "ok", False):
        return out
    try:
        tied = {int(r[0]) for r in con.execute("SELECT DISTINCT order_id FROM order_scan_tie WHERE arrived=1")} if _has(con, "order_scan_tie") else set()
        items = [r[0] for r in con.execute("SELECT DISTINCT item FROM purchase_order_line WHERE arrived_at IS NOT NULL AND supplied>0 AND COALESCE(billed_bill_no,'')=''")]
    except sqlite3.Error:
        return out
    lines = []
    for it in items:
        lines.extend(a for a in _sw()._arrivals(con, it, "", sp, ctx=ctx) if not str(a.get("billed_bill_no") or "").strip())
    lines.extend(scan_lines(con, sp, None, "", ctx))
    seen = set()
    for a in lines:
        if a.get("line_id") in seen:                          # one line reached under two spellings of its name
            continue
        seen.add(a.get("line_id"))
        if carried(con, sp, a, ctx) is None and expired(con, sp, a, ctx):
            out.append(dict(line_id=a["line_id"], item=a["item"], units=float(a["units"] or 0), at=str(a.get("arrived_at") or ""),
                            who=("scan" if a.get("kind") == "scan" else (a.get("arrived_by") or "")), vendor=a.get("vendor") or "", order_id=a.get("order_id"),
                            kind=a.get("kind") or "tap", scan_tied=(int(a.get("order_id") or 0) in tied), family_bill=ctx.c.get(("fam_bill", a["line_id"]))))
    out.sort(key=lambda x: (str(x["item"]), x["at"]))
    return out


def marg(con, sp, name, at=None, ctx=None):
    """Marg's figure at `at` (today): closing().units + sp_move of key_of(name) over (end_day, at] (MOVE_KINDS). approx=True whenever
    family() has more than one member, whatever `by` is. taps = tapped arrivals the spine does not carry, beside the figure.
    S587 (R2-B3): on a START or EARLY-morning capture (printed D, standing for the end of D-1) the purchases dated D are already inside the
    capture -- they are never added again (only D's sales, returns and reconciliations, and every kind after D), and such a key is approx with
    approx_reason 'purchase_on_start' (also at `at` == end_day); an accepted start capture's unexplained keys ('start_unexplained') and its
    verification-excluded keys with a sale dated D ('start_excluded') are approx too (start_marks). When the figure is asked exactly at the
    capture's end day (a judgment between two closings: shelf_figure.record_gaps) and the PREVIOUS end day's capture is a morning one holding
    a purchase of its printed day for this key, the key is approx as well -- the base side of R2-B3."""
    ctx = _ctx(con, sp, ctx)
    c = closing(con, sp, name, at, ctx)
    if c is None:
        return None
    a = _iso(at)
    k = key_of(sp, name, ctx)
    sx = split_of(sp, name, ctx)                              # S613 (F-951): a split size is figured on its own key, by old name or new
    if sx is not None:
        k = sx["new_k"]
    fam = family(sp, k, c["md5"], ctx)
    if sx is not None and c["end_day"] <= sx["day"]:          # a capture on or before the split day: the helper (the share, then its own key)
        share = split_share(con, sp, name, sx, ctx)[0]
        sold, ret, bought = split_moves(sp, sx, share, c["end_day"], a)
        net = spine_move(sp, k, c["end_day"], a, split=sx, share=share)
        if c["end_day"] < sx["day"]:
            fam = split_members(sp, sx, ctx)
    else:
        sold, ret, bought = moves(sp, k, c["end_day"], a, incl_from=False)
        net = spine_move(sp, k, c["end_day"], a)
    cap = capture_of(sp, c["md5"], ctx)
    reason = None
    if cap and (cap["start"] or cap["early"]):
        reason = start_marks(ctx.con, sp, cap, ctx).get(k)
        pD = _purchases_on(sp, cap["as_on"], ctx).get(k)
        if pD and a >= cap["as_on"]:
            net -= pD[1]
            bought -= pD[1]
    if reason is None and a == c["end_day"]:
        pv = _prev_capture(sp, c, ctx)
        if pv and (pv["start"] or pv["early"]) and k in _purchases_on(sp, pv["as_on"], ctx):
            reason = "purchase_on_start"
    return dict(figure=float(c["units"]) + net, closing=c, sold=sold, returned=ret, bought=bought, upto=a, key=k,
                approx=bool(c["approx"] or len(fam) > 1 or reason), approx_reason=reason, family=fam, taps=taps(con, sp, name, c["stamp_iso"], ctx))


def late_match(res, pl, tol=0.5):
    """The residual match _s524_table uses (moved here, called by both): the units of ONE purchase, or the sum of TWO, within `tol` of
    `res`; None when none matches. A purchase keyed after a closing's capture but dated at or before its day is the spine's own TIMING
    reading."""
    for u in pl:
        if abs(res - u) < tol:
            return u
    for i in range(len(pl)):
        for j in range(i + 1, len(pl)):
            if abs(res - pl[i] - pl[j]) < tol:
                return pl[i] + pl[j]
    return None


def late_purchases(sp, k20, end_day_):
    """The purchase movements (signed) of the key dated within LATE_DAYS days on or before a closing's end_day."""
    try:
        d21 = (dt.date.fromisoformat(str(end_day_)[:10]) - dt.timedelta(days=LATE_DAYS)).isoformat()
    except ValueError:
        return []
    return [float(r["units"] or 0) for r in sp.q("SELECT units FROM sp_move WHERE k20=? AND kind IN ('PURCHASE','PURCHASE_RETURN') AND date>=? AND date<=?", k20, d21, str(end_day_)[:10])]


def late_purchase(con, sp, name, cap, after, shelf_, tol, ctx=None):
    """True when |after - shelf| equals, within tol, the units of a purchase (or two) of the key dated within LATE_DAYS on or before the
    capture's end_day -- a bill that may have been keyed after the closing (sp_purchase_line.source_md5 cannot say when a line first
    appeared, R3-C6). Such an item is not judged against the shelf."""
    ctx = _ctx(con, sp, ctx)
    if cap is None or after is None or shelf_ is None:
        return False
    k = key_of(sp, name, ctx)
    return late_match(float(after) - float(shelf_), late_purchases(sp, k, cap["end_day"]), max(0.5, float(tol or 0))) is not None


# S587: the early-morning rule (a capture printed D taken before 09:00 holding a bill dated D) is start_marks / marg() -- one rule for the
# early and the start capture; its one caller, the voucher guard, reads marg()['approx_reason'].


# ------------------------------------------------------------------ the shelf figure (the three count tables, read once per pass)
def count_family(con, ctx=None):
    """{item: dict(qty, day iso, at, count_id, fixed, marg0)} -- the newest full count's row of every item: the count's own figure, its
    parts', and the desk's corrections (stock_shelf_fix) laid over, the latest winning. A fix with count_id < 0 is a RETIRED row (S502's
    marking) and is never read. (shelf_figure.count_family's shape, kept.)"""
    ctx = _ctx(con, None, ctx)
    if "cf" in ctx.c:
        return ctx.c["cf"]
    con = ctx.con
    out = {}
    if con is None or not _has(con, "stock_count_item"):
        ctx.c["cf"] = out
        return out
    try:
        parts = {}
        if _has(con, "stock_count_part"):
            parts = {int(r[0]): int(r[1]) for r in con.execute("SELECT count_id, part_of FROM stock_count_part")}
        counts = [dict(id=int(r[0]), day=dmy_iso(r[1]), at=str(r[2] or "")) for r in
                  con.execute("SELECT id, marg_as_on, COALESCE(submitted_at, started_at) FROM stock_count WHERE status='submitted' ORDER BY id")]
        for c in counts:
            for item, qty, at, mq in con.execute("SELECT item, counted_qty, at, marg_qty FROM stock_count_item WHERE count_id=? AND counted_qty IS NOT NULL", (c["id"],)):
                prev = out.get(item)
                st = (c["day"], str(at or c["at"]))
                if prev is None or st >= (prev["day"], prev["at"]):
                    out[item] = dict(qty=float(qty), day=c["day"], at=str(at or c["at"]), count_id=parts.get(c["id"], c["id"]), fixed=False,
                                     marg0=(float(mq) if mq is not None else None))
        if _has(con, "stock_shelf_fix"):
            for item, qty, at, cid in con.execute("SELECT item, qty, at, count_id FROM stock_shelf_fix WHERE COALESCE(count_id,0) >= 0 ORDER BY at, id"):
                e = out.get(item)
                if e is not None and qty is not None and int(cid or 0) in (e["count_id"], 0):
                    e.update(qty=float(qty), fixed=True, fixed_at=str(at))
    except sqlite3.Error:
        out = {}
    ctx.c["cf"] = out
    return out


def points(con, ctx=None, exclude_id=None):
    """{item_norm: dict(qty, at, source, item, basis)} -- the newest stock point that is not the full count's own copy and NOT superseded
    (S502: a replaced count is never picked). exclude_id: a point left out (the point being judged itself -- settle_provisional re-judges a
    provisional point against the base BEFORE it). (shelf_figure.points' shape, kept; superseded rows excluded -- the one change.)"""
    ctx = _ctx(con, None, ctx)
    ck = ("pts", exclude_id)
    if ck in ctx.c:
        return ctx.c[ck]
    con = ctx.con
    out = {}
    if con is not None and _has(con, "stock_point"):
        try:
            cols = {r[1] for r in con.execute("PRAGMA table_info(stock_point)")}
            bcol = "basis" if "basis" in cols else "NULL"
            lcol = "last_bill" if "last_bill" in cols else "NULL"      # S934: a Count now's last sale bill
            for nm, item, at, qty, src, bs, pid, lb in con.execute("SELECT item_norm, item, at, qty_units, source, %s, id, %s FROM stock_point WHERE source<>? "
                                                                   "AND COALESCE(status,'') NOT IN ('superseded','recount','recounted') "   # S936 (D1046): a count held for a recount is never a base
                                                                   "ORDER BY at, id" % (bcol, lcol), (FULL,)):
                if exclude_id is not None and int(pid) == int(exclude_id):
                    continue
                out[nm] = dict(qty=float(qty or 0), at=str(at), source=src, item=item, basis=bs, last_bill=(str(lb) if lb not in (None, "") else None))
        except sqlite3.Error:
            out = {}
    ctx.c[ck] = out
    return out


def base(con, name, ctx=None, exclude_id=None):
    """The one view of the three count tables for the name AND every printed form of it (the count holds old names): the newest of the
    count family (stock_count_item with stock_shelf_fix laid over) and a stock point that is not full_count and not superseded.
    dict(qty, kind, day, at, count_id, fixed, marg0, item) or None."""
    ctx = _ctx(con, None, ctx)
    cf, pts = count_family(con, ctx), points(con, ctx, exclude_id)
    best = None
    for f in printed_forms(ctx.con, name, ctx):
        c = cf.get(f)
        if c and (best is None or (c["day"], c["at"]) > (best["day"], best["at"])):
            best = dict(qty=c["qty"], kind="count", day=c["day"], at=c["at"], count_id=c["count_id"], fixed=c["fixed"], marg0=c.get("marg0"), item=f)
        p = pts.get(norm_name(f))
        if p and (best is None or (p["at"][:10], p["at"]) > (best["day"], best["at"])):
            best = dict(qty=p["qty"], kind=p["source"], day=p["at"][:10], at=p["at"], count_id=None, fixed=False, marg0=None, item=p["item"],
                        last_bill=p.get("last_bill"))                   # S934
    return best


def pack_of(con, sp, name, ctx=None):
    """(pack size, packing, source) -- sp_close_name's packing of the newest capture through qty_words.pack_of, else sp_item's; 1 otherwise."""
    ctx = _ctx(con, sp, ctx)
    c = closing(con, sp, name, None, ctx)
    if c and c.get("packing"):
        return _qw().pack_of(c["packing"]), c["packing"], "sp_close_name"
    try:
        it = sp.item(name) if (sp is not None and sp.ok) else None
    except Exception:                                         # noqa: BLE001
        it = None
    if it and it.get("packing"):
        return _qw().pack_of(it["packing"]), it["packing"], "sp_item"
    return 1, "", "none"


def shelf(con, sp, name, at=None, ctx=None, exclude_id=None):
    """The shelf figure at `at` (today): base + the spine's movements after the base (the count day's sales in, its purchases out), split
    by counted share among the FAMILY's members (family(), never the names passed in), + boundary purchases (a bill dated before the count,
    entered after it) + the arrivals Marg does not carry yet (taps + scan_arrivals: ONE rule, carried / expired -- S583). No count ->
    shelf=None, named='no_count' (never Marg's: charter 3).
    Below zero -> 0, named='below_zero'. arrived is returned apart. exclude_id: a stock point left out of the base (the point being judged)."""
    ctx = _ctx(con, sp, ctx)
    a = _iso(at)
    k = key_of(sp, name, ctx)
    cap = capture_at(sp, a, ctx)
    fam = family(sp, k, cap["md5"] if cap else None, ctx)
    mine = base(con, name, ctx, exclude_id)
    out = dict(shelf=None, named=None, base=None, base_kind=None, base_day=None, base_at=None, sold=0.0, returned=0.0, bought=0.0,
               boundary=0.0, arrived=0.0, approx=len(fam) > 1, key=k, marg0=None, members=fam, share=None)
    if mine is None:
        out["named"] = "no_count"
        return out
    out.update(base=mine["qty"], base_kind=mine["kind"], base_day=mine["day"], base_at=mine["at"], marg0=mine.get("marg0"))
    sx = split_of(sp, name, ctx)                              # S613 (F-951): a size of a split shared key
    bname = name
    if sx is not None and mine["day"] > sx["day"]:            # a base after the split day: the size alone, on its own key (as any item)
        k, bname = sx["new_k"], sx["new_name"]
        fam = family(sp, k, cap["md5"] if cap else None, ctx)
        out.update(key=k, members=fam)
        sx = None
    elif sx is not None:                                      # a base on or before it: the family's members at the split share its history
        fam = split_members(sp, sx, ctx)
        out["members"] = fam
    bases = []
    for mbr in fam:
        b = base(con, mbr[0], ctx, exclude_id)
        if b is not None:
            bases.append(b)
    if not any(norm(b["item"]) == norm(mine["item"]) for b in bases):
        bases.append(mine)
    tot = sum(max(0.0, b["qty"]) for b in bases)
    n = len(bases)
    share = (max(0.0, mine["qty"]) / tot) if tot > 0 else (1.0 / max(1, n))
    out["share"] = round(share, 4)
    if sp is None or not getattr(sp, "ok", False):
        out["named"] = "no_spine"
        return out
    ev = mine["kind"] != "count" and not mine.get("last_bill") and evening_count(mine.get("at"), _s928_settings(ctx)[1], mine["day"])   # S934: a count placed to its bill is never 'the end of its day'   # S928 (F-1564): a spot count at or after the evening hour is the END of its day (never the full count: its at is the entry moment)
    out["base_evening"] = ev
    if sx is not None:                                        # S613: the one helper -- the old key's share to the split day, its own key after
        sold, ret, bought = split_moves(sp, sx, share, mine["day"], a, incl_from=not ev)
        out.update(sold=round(sold, 2), returned=round(ret, 2), bought=round(bought, 2))
    else:
        sold, ret, bought = moves(sp, k, mine["day"], a, incl_from=not ev)   # S928: the count day's sales in only for a count before the evening hour
        if mine.get("last_bill"):                             # S934: the count day's sales billed up to its last bill left before he counted
            cut = day_sales_cut(sp, k, mine["day"], _bill_n(mine.get("last_bill")), after=False)
            sold -= cut
            ret -= day_returns(sp, k, mine["day"])          # the count day's sale returns are taken as made BEFORE the count (credit notes carry no A number)
            out["bill_cut"] = round(cut, 2)
        out.update(sold=round(share * sold, 2), returned=round(share * ret, 2), bought=round(share * bought, 2))
    arr = taps(con, sp, name, mine["at"], ctx) + scan_arrivals(con, sp, name, (mine["day"] if mine["kind"] == "count" else mine["at"]), ctx)   # S583: both under the one rule; S928: a spot count by its moment
    out["arrived"] = arr
    if n == 1 and sx is None and mine["kind"] == "count" and cap is not None and not (   # S454 9.1 (S613: never across a split)
            (cap.get("start") or cap.get("early")) and k in _purchases_on(sp, cap["as_on"], ctx)):   # S587 (R2-B3): never on a morning capture holding this key's purchase
        c = closing(con, sp, name, a, ctx)
        pk = pack_of(con, sp, name, ctx)[0]
        try:
            out["boundary"] = float(_sf_shelf().boundary_purchases(con, sp, bname, mine["day"], mine.get("marg0"), (c["units"] if c else None),
                                                                   (c["as_on"] if c else None), pk, ctx=ctx) or 0)
        except Exception:                                     # noqa: BLE001
            out["boundary"] = 0.0
    v = mine["qty"] - out["sold"] + out["returned"] + out["bought"] + out["boundary"] + arr
    if v < 0:
        out["named"], v = "below_zero", 0.0
    out["shelf"] = int(round(v))
    out["approx"] = n > 1 or sx is not None                   # S613: a split size is approx while its base is on or before the split day
    return out


def _bill_n(text):
    """S934: a sale bill number's digits as an int ('A004951' -> 4951); None when it carries none."""
    d = "".join(re.findall(r"\d+", str(text or "")))
    return int(d) if d else None


def day_sales_cut(sp, k20, day, bill_no, after=True):
    """S934: units SOLD of the key on `day` billed AFTER (after=True) or UP TO (after=False) the sale bill number -- the spine's SALE rows
    carry their bill in ref. A row whose ref carries no number counts as after (never taken off as before). 0 when the number is None."""
    if sp is None or not getattr(sp, "ok", False) or bill_no is None or not k20:
        return 0.0
    tot = 0.0
    for r in (sp.q("SELECT ref, units FROM sp_move WHERE k20=? AND date=? AND kind='SALE'", k20, day) or []):
        n = _bill_n(r["ref"])
        is_after = (n is None) or (n > int(bill_no))
        if is_after == bool(after):
            tot += -float(r["units"] or 0)
    return tot


def day_returns(sp, k20, day):
    """S934: units RETURNED by patients (SALE_RETURN) of the key on `day` -- taken as before a bill-placed count of that day."""
    if sp is None or not getattr(sp, "ok", False) or not k20:
        return 0.0
    r = sp.q("SELECT COALESCE(SUM(units),0) AS u FROM sp_move WHERE k20=? AND date=? AND kind='SALE_RETURN'", k20, day)
    return float(r[0]["u"] or 0) if r else 0.0


def figures(con, sp, names, at=None, ctx=None):
    """{name: dict(marg=marg(), shelf=shelf())} -- both kept apart, one pass, one context."""
    ctx = _ctx(con, sp, ctx)
    return {n: dict(marg=marg(con, sp, n, at, ctx), shelf=shelf(con, sp, n, at, ctx)) for n in names}


def expect_for_point(con, sp, name, ctx=None, basis=None, exclude_id=None):
    """What a spot count is judged against: dict(expected, basis, provisional, as_on, approx, close, sold, bought, records).
    approx (a family member) -> basis='approx', expected=None; counted -> basis='shelf' (provisional = its arrived); uncounted ->
    basis='marg' (expected = marg.figure + taps, provisional = taps). `basis` given forces that branch (settle_provisional re-judges a
    point on its STORED basis; NULL -> 'marg'); exclude_id leaves the point being judged out of the base."""
    ctx = _ctx(con, sp, ctx)
    S = shelf(con, sp, name, None, ctx, exclude_id)
    M = marg(con, sp, name, None, ctx)
    s928_sa = scan_arrivals(con, sp, name, M["closing"]["stamp_iso"], ctx) if M else 0.0   # S928: a scan-tied delivery counts for an uncounted item too (once)
    records = (float(M["figure"]) + float(M["taps"] or 0) + s928_sa) if M else None
    if basis is None:
        basis = "approx" if (S.get("approx") or (M and M.get("approx"))) else ("shelf" if S.get("shelf") is not None else "marg")
    if basis == "approx":
        return dict(expected=None, basis="approx", provisional=0.0, as_on=(S.get("base_day") or (M["closing"]["as_on"] if M else None)), approx=True,
                    close=None, sold=0.0, bought=0.0, records=records, terms=[])
    if basis == "shelf" and S.get("shelf") is not None:
        return dict(expected=float(S["shelf"]), basis="shelf", provisional=float(S.get("arrived") or 0), as_on=S.get("base_day"), approx=False,
                    close=S.get("base"), sold=float(S.get("sold") or 0), bought=float(S.get("bought") or 0), records=records, terms=[])
    if M is None:
        return dict(expected=None, basis="marg", provisional=0.0, as_on=None, approx=False, close=None, sold=0.0, bought=0.0, records=None, terms=[])
    return dict(expected=records, basis="marg", provisional=float(M["taps"] or 0) + s928_sa, as_on=M["closing"]["as_on"], approx=False,   # S928: a scan-tied delivery is provisional too
                close=float(M["closing"]["units"]), sold=float(M["sold"] or 0), bought=float(M["bought"] or 0), records=records, terms=[])


# ------------------------------------------------------------------ S928 (D1036 / D1037, 22-Nov-2026): the bill over the tap; a count by its time
#  THE OWNER'S WORD (22-Nov 07:01): "the scanned bill's quantity is relied on over reception's arrival taps, and the same rule must apply
#  everywhere in the system". So an arrival line (a tap, or a scan-tied order line) COUNTS by the quantity the dealer's scanned bill carries
#  for that medicine -- read by the tracker's own matcher (order_track.match_lines, as S825 judges "on the bill") -- whenever the order has a
#  usable, read scan tied to it: a tap above the bill is a SHORT SUPPLY (short_supplies(), the Stock check page; it rides the dealer's next
#  order through the purchase flow), a tapped medicine the bill does not carry counts NOTHING, a bill above the tap counts the bill. With no
#  usable read scan the tap stands as before (nothing is dropped, charter 1b). The switch: arrival.bill_over_tap (stock_watch.settings).
#  A COUNT BY ITS TIME (F-1564): a count saved on its own day at or after count.evening_hour (the setting, 17:00 to start) stands for the END
#  of that day -- its day's sales are not taken off again (TYRO BR, Darpan 12-10 19:49: ~18:5 strips were). A count saved before the hour, or
#  keyed in on a later day, is the start of its day as before.
def _s928_settings(ctx):
    """(arrival.bill_over_tap, count.evening_hour) through stock_watch.settings -- once per Ctx; (True, 17) when unread."""
    if "s928" not in ctx.c:
        bot, ev = True, 17
        try:
            S = _sw().settings(ctx.con)
            bot = bool(S.get("bill_over_tap", True))
            ev = int(S.get("evening_hour", 17))
        except Exception:                                     # noqa: BLE001
            pass
        ctx.c["s928"] = (bot, max(0, min(23, ev)))
    return ctx.c["s928"]


def evening_count(at, hour, day=None):
    """True when the count moment `at` (ISO) falls on `day` (its own day; at's day when None) at or after `hour` -- the count then stands
    for the END of its day. False for an unreadable moment."""
    s = str(at or "").strip().replace(" ", "T")
    if len(s) < 13 or not s[11:13].isdigit():
        return False
    if day is not None and s[:10] != str(day)[:10]:
        return False
    return int(s[11:13]) >= int(hour)


def _s928_octx(ctx):
    """order_track.Ctx (the scans and their readings) once per Ctx; None when the scan store cannot be read. The connection's row factory is
    put back as it was (as s825_bill_judged does)."""
    key = ("s928_octx",)
    if key in ctx.c:
        return ctx.c[key]
    o = None
    con = ctx.con
    if con is not None:
        rf = con.row_factory
        try:
            con.row_factory = sqlite3.Row
            import order_track as OT                          # noqa: PLC0415 -- beside this file
            o = OT.Ctx(con)
            if not getattr(o, "ok", False):
                o = None
            else:
                o._s928_OT = OT
        except Exception:                                     # noqa: BLE001
            o = None
        finally:
            con.row_factory = rf
    ctx.c[key] = o
    return o


def bill_units(con, sp, line, ctx=None):
    """S928: what the dealer's SCANNED BILL says this arrival line brought -- dict(units, qty, on_bill, read_name, scan_id) -- or None when the
    rule cannot speak (the switch off; no order; no usable, read scan tied to the order; the store unreadable): the line's own units then
    stand. on_bill False -> units 0.0 (the bill does not carry the medicine: it did not come, whatever was tapped); a matched line whose
    quantity was not read -> units None (read, but no figure: the line's own units stand). units = the read quantity x the order line's
    pack size (the unit the tap itself is counted in). Once per line per Ctx. READ ONLY."""
    ctx = _ctx(con, sp, ctx)
    if not isinstance(line, dict) or not line.get("order_id"):
        return None
    if not _s928_settings(ctx)[0]:
        return None
    ck = ("s928_bill", line.get("line_id"), int(line.get("order_id") or 0), norm(line.get("item")))
    if ck in ctx.c:
        return ctx.c[ck]
    try:
        out = _bill_units(ctx, line)
    except Exception:                                         # noqa: BLE001 -- fail-soft: the line's own units
        out = None
    ctx.c[ck] = out
    return out


def _s928_order_match(ctx, o, OT, order_id):
    """ONE match per order, as s825_bill_judged matches: every order line's item against every read line of the order's usable, read scans,
    one-to-one (order_track.match_lines) -- {item: (read name, stamp)}, plus the reads [(name, stamp, qty, free, head)] and the heads.
    Cached per order per Ctx. None when the order has no usable, read scan."""
    key = ("s928_match", int(order_id))
    if key in ctx.c:
        return ctx.c[key]
    con = ctx.con
    out = None
    sids = sorted({int(r[0]) for r in con.execute("SELECT asset_bill_id FROM order_scan_tie WHERE order_id=? AND asset_bill_id IS NOT NULL", (int(order_id),))})   # S933: the tie is the fact -- arrived=0 when reception tapped before the scan (41 of 99 live ties); the bill still speaks
    heads = []
    for sid in sids:
        h = o.head(sid)
        if h in o.scans and h not in heads and o.usable(h) and o.names(h):
            heads.append(h)
    if heads:
        reads = []
        for h in heads:
            stp = o.scans[h].get("stamp_no") or "#%d" % h
            for it in ((o.read.get(int(h)) or {}).get("items") or []):
                if isinstance(it, dict) and it.get("name"):
                    fr = it.get("free")
                    if fr is None:
                        fr = it.get("free_qty")
                    reads.append((str(it.get("name")), stp, it.get("qty"), fr, h))
        if reads:
            orow = con.execute("SELECT vendor, supplier_norm FROM purchase_order WHERE id=?", (int(order_id),)).fetchone()
            sn = (orow[1] if (orow and orow[1]) else OT._pa().supplier_key((orow[0] if orow else "") or ""))
            items = list(dict.fromkeys(str(r[0]) for r in con.execute("SELECT item FROM purchase_order_line WHERE order_id=? ORDER BY id", (int(order_id),))))
            hit = OT.match_lines(con, sn, items, [(n, s) for (n, s, _q, _f, _h) in reads], o.sf)
            out = dict(hit=hit, reads=reads, heads=heads)
    ctx.c[key] = out
    return out


def _bill_units(ctx, line):
    con = ctx.con
    if con is None or not _has(con, "order_scan_tie"):
        return None
    o = _s928_octx(ctx)
    if o is None:
        return None
    OT = o._s928_OT
    M = _s928_order_match(ctx, o, OT, int(line["order_id"]))
    if M is None:
        return None
    item = str(line.get("item") or "")
    if item not in M["hit"]:
        return dict(units=0.0, qty=None, on_bill=False, read_name="", scan_id=M["heads"][0], scans=list(M["heads"]))
    rn, stp = M["hit"][item]
    nm = OT._nm(rn)
    qs, fs, sid = [], [], M["heads"][0]
    for n, s, qq, fr, h in M["reads"]:                        # every batch line of the medicine on that bill, summed (as carried() sums them)
        if s == stp and OT._nm(n) == nm:
            qs.append(qq)
            fs.append(fr)
            sid = h
    try:
        qf = sum(float(q) for q in qs)
        ff = sum(float(f) for f in fs if f not in (None, ""))
    except (TypeError, ValueError):
        return dict(units=None, qty=None, on_bill=True, read_name=rn, scan_id=sid, scans=list(M["heads"]))
    ps = int(line.get("pack_size") or 1) or 1
    return dict(units=(qf + ff) * ps, qty=qf, free=ff, on_bill=True, read_name=rn, scan_id=sid, scans=list(M["heads"]))


def _count_units(con, sp, a, ctx):
    """The units an arrival line COUNTS for: the scanned bill's (bill_units) when it speaks, else the line's own."""
    b = bill_units(con, sp, a, ctx)
    if b is not None and b.get("units") is not None:
        return float(b["units"])
    return float(a.get("units") or 0)


def short_supplies(con, sp, ctx=None, since_iso=""):
    """S928: every open arrival line (tapped or scan-tied; not carried by Marg's purchases, no billed_bill_no) whose tap or order quantity and
    the scanned bill's quantity DIFFER: dict(line_id, item, vendor, supkey, order_id, kind, at, tap_units, bill_units, diff_units (bill - tap:
    negative = short, the dealer sent less than was tapped / ordered; positive = over), on_bill, read_name, scan_id, pack_size). Sorted by
    item, then moment. The Stock check page's words; the purchase flow reads it for the dealer's next order. READ ONLY, fail-soft []."""
    ctx = _ctx(con, sp, ctx)
    con = ctx.con
    out = []
    if con is None or sp is None or not getattr(sp, "ok", False) or not _s928_settings(ctx)[0]:
        return out
    try:
        items = [r[0] for r in con.execute("SELECT DISTINCT item FROM purchase_order_line WHERE arrived_at IS NOT NULL AND supplied>0 AND COALESCE(billed_bill_no,'')=''")]
    except sqlite3.Error:
        return out
    lines = []
    for it in items:
        lines.extend(a for a in _sw()._arrivals(con, it, since_iso or "", sp, ctx=ctx) if not str(a.get("billed_bill_no") or "").strip())
    lines.extend(scan_lines(con, sp, None, since_iso or "", ctx))
    seen = set()
    for a in lines:
        if a.get("line_id") in seen:
            continue
        seen.add(a.get("line_id"))
        if carried(con, sp, a, ctx) is not None:
            continue
        b = bill_units(con, sp, a, ctx)
        if b is None or b.get("units") is None:
            continue
        tap = float(a.get("units") or 0)
        if abs(float(b["units"]) - tap) < 0.5:
            continue
        out.append(dict(line_id=a.get("line_id"), item=a.get("item"), vendor=a.get("vendor") or "", supkey=a.get("supkey") or _sw().supkey(a.get("vendor")),
                        order_id=a.get("order_id"), kind=a.get("kind") or "tap", at=str(a.get("arrived_at") or a.get("scan_at") or ""),
                        tap_units=tap, bill_units=float(b["units"]), diff_units=round(float(b["units"]) - tap, 3), on_bill=bool(b.get("on_bill")),
                        read_name=b.get("read_name") or "", scan_id=b.get("scan_id"), pack_size=int(a.get("pack_size") or 1)))
    out.sort(key=lambda x: (str(x["item"]), x["at"]))
    return out


# ------------------------------------------------------------------ the side-by-side week (witness only; 4b-2 retires the old ways)
def witness(con, sp, out_dir=None, when=None):
    """For every item of the newest usable capture: stock_figure.marg against stock_watch.expected_units against the PC's newest
    push_expected row (stock_feed), each with its day; marg_shadow's line where sh_diff has one; per pair the items a pack or more apart,
    with the named reason. Written to <spine dir>/stock_figure_witness_<Mon..Sun>.txt (overwritten a week later; nothing deleted)."""
    ctx = Ctx(con, sp, read_only=True)                        # S602 (F-943): read-only -- the judge stays out
    now = when or dt.datetime.now()
    d = out_dir or os.path.dirname(os.path.abspath(getattr(_sw(), "SPINE_DB", os.path.join(HERE, "spine", "spine.db"))))
    path = os.path.join(d, "stock_figure_witness_%s.txt" % WITNESS_DAYS[now.weekday()])
    L = ["stock_figure witness  %s IST  (kit %s; the old ways run beside the new for one week -- 4b-2 retires them)" % (now.replace(microsecond=0).isoformat(), KIT)]
    if not ready(sp):
        L.append("the spine's closing table (sp_close_name) is not ready: nothing to compare")
        _write(path, L)
        return path
    cap = capture_at(sp, None, ctx)
    L.append("newest usable capture: printed %s, taken %s, stands for the end of %s (%s)" % (cap["as_on"], cap["stamp_iso"], cap["end_day"], cap["md5"][:8]))
    by_n, _by_k = _cn_rows(sp, cap["md5"], ctx)
    names = sorted({rows[0][0] for rows in by_n.values()})
    pc_day, pc_at, pc = None, None, {}
    try:
        r = con.execute("SELECT as_on, received_at FROM stock_feed WHERE LOWER(source) LIKE 'push_expected%' ORDER BY received_at DESC LIMIT 1").fetchone()
        if r:
            pc_day, pc_at = str(r[0]), str(r[1])
            pc = {str(x[0]): float(x[1] or 0) for x in con.execute("SELECT item, qty FROM stock_feed WHERE as_on=? AND received_at=? AND LOWER(source) LIKE 'push_expected%'", (r[0], r[1]))}
    except sqlite3.Error:
        pass
    sh_day, sh = None, {}
    try:
        r = con.execute("SELECT id, as_on FROM sh_run ORDER BY id DESC LIMIT 1").fetchone()
        if r:
            sh_day = str(r[1])
            sh = {str(x[0]): (x[1], x[2], x[3]) for x in con.execute("SELECT item, server_qty, pc_qty, diff FROM sh_diff WHERE run_id=?", (r[0],))}
    except sqlite3.Error:
        pass
    L.append("PC's newest push_expected: day %s, received %s, %d items · marg_shadow's newest run: as on %s, %d lines" % (pc_day, pc_at, len(pc), sh_day, len(sh)))
    L.append("")
    L.append("%-30s %10s %10s %10s %10s   %s" % ("item", "marg()", "expected", "PC push", "shadow", "closing / reason"))
    diff_e, diff_p, diff_s = [], [], []
    for n in names:
        M = marg(con, sp, n, None, ctx)
        E = _sw().expected_units(con, sp, n)
        pk = pack_of(con, sp, n, ctx)[0]
        mf = M["figure"] if M else None
        ef = E.get("expected")
        pf = pc.get(n)
        sf = sh.get(n)
        reason = []
        if M and M["approx"]:
            reason.append("family figure (%d members)" % len(M["family"]))
        if M and E.get("as_on") and E["as_on"] != M["closing"]["as_on"]:
            reason.append("closing days differ: %s by name vs %s by sp_close" % (M["closing"]["as_on"], E["as_on"]))
        if M and M["taps"]:
            reason.append("tapped arrivals %g beside the figure" % M["taps"])
        if M and M["closing"]["by"] != "name":
            reason.append("closing read by %s" % M["closing"]["by"])
        if mf is not None and ef is not None and abs(mf - ef) >= max(1, pk):
            diff_e.append((n, mf, ef, "; ".join(reason) or "unexplained"))
        if mf is not None and pf is not None and abs(mf - pf) >= max(1, pk):
            diff_p.append((n, mf, pf, "; ".join(reason) or "the PC's own base and reach"))
        if sf is not None and sf[2] not in (None, 0) and abs(float(sf[2])) >= max(1, pk):
            diff_s.append((n, sf[0], sf[1], "shadow run as on %s" % sh_day))
        L.append("%-30s %10s %10s %10s %10s   %s" % (n[:30], _f(mf), _f(ef), _f(pf), _f(sf[2] if sf else None),
                                                      ("closing %s %s" % (M["closing"]["as_on"], M["closing"]["by"]) if M else "no closing") + ((" · " + "; ".join(reason)) if reason else "")))
    L.append("")
    L.append("marg() vs expected_units, a pack or more apart: %d" % len(diff_e))
    L.extend("   %-30s %10s %10s   %s" % (n[:30], _f(a), _f(b), w) for n, a, b, w in diff_e)
    L.append("marg() vs the PC's push, a pack or more apart: %d" % len(diff_p))
    L.extend("   %-30s %10s %10s   %s" % (n[:30], _f(a), _f(b), w) for n, a, b, w in diff_p)
    L.append("marg_shadow lines a pack or more apart (server vs PC): %d" % len(diff_s))
    L.extend("   %-30s %10s %10s   %s" % (n[:30], _f(a), _f(b), w) for n, a, b, w in diff_s)
    _write(path, L)
    return path


def _f(v):
    return "-" if v is None else ("%g" % v)


def _write(path, lines):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(re.sub(r"\d{10,}", "##########", l) for l in lines) + "\n")
    os.replace(tmp, path)


def verify_start_cli(con, sp, days=21):
    """`python3 stock_figure.py verify-start`: judge every start capture of the last `days` days that has no final verdict (captures() with a
    writable connection writes the record), then print each with its verdict, reason, the deciding keys and the excluded keys by cause.
    The installer runs it once after placing; the walk and the report quote it."""
    ctx = Ctx(con, sp)
    lines = []
    for r in start_report(con, sp, ctx, days=days):
        lines.append("start capture %s printed %s taken %s -> stands for the end of %s: %s%s (usable %s; keys %s, excluded %s, unexplained %s; prev %s %s)"
                     % (r["md5"], r["as_on"], r["stamp_iso"], r["start_day"], r["verdict"], (" / " + r["reason"]) if r["reason"] else "", r["usable"],
                        r["n_keys"], r["n_excluded"], r["n_unexplained"], str((r["prev"] or {}).get("md5") or "")[:8], (r["prev"] or {}).get("stamp_iso") or "-"))
        if r["sale_before"]:
            lines.append("   a sale came before it: %s" % ", ".join("%s %+g (sold %g)" % (x[1], x[2], x[3]) for x in r["sale_before"][:12]))
        if r["unexplained"]:
            lines.append("   unexplained: %s" % ", ".join("%s %+g" % (x[1], x[2]) for x in r["unexplained"][:12]))
        if r["excluded"]:
            lines.append("   excluded by cause: %s" % ", ".join("%s %d" % (k, v) for k, v in sorted(r["excluded"].items())))
        if r["changed_excluded"]:
            lines.append("   excluded keys that changed: %s" % ", ".join("%s %+g" % (x[1], x[2]) for x in r["changed_excluded"][:12]))
    return lines


def main(argv):
    if not argv or argv[0] not in ("witness", "verify-start"):
        print("usage: stock_figure.py witness   (the nightly side-by-side file; read only)")
        print("       stock_figure.py verify-start   (S587: judge the start-of-day closings of the last 21 days; writes stock_start_capture)")
        return 2
    for flag in ("/root/finance/_off/ALL_OFF", os.path.join(HERE, "_off", "ALL_OFF")):
        if os.path.exists(flag):
            print("stock_figure: switched off (%s)" % flag)
            return 0
    db = os.environ.get("FINANCE_DB") or os.path.join(HERE, "finance.db")
    if argv[0] == "verify-start":
        con = sqlite3.connect(db, timeout=60)
        sp = _sw().Spine()
        try:
            for line in verify_start_cli(con, sp):
                print(line)
        finally:
            con.close()
        return 0
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=60)
    sp = _sw().Spine()
    p = witness(con, sp)
    con.close()
    print("stock_figure witness written: %s" % p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
