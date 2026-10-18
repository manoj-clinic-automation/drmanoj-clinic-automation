#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  stock_figure.py  ·  v1.0  ·  kit S577_STOCK_ON_SPINE  ·  Session 324 (Sanjeevni)  ·  rung 4b of the spine plan (Book 4A, 15F.1)
#
#  THE ONE STOCK FUNCTION (charter 1, 2, 3, 11, 12). For an item it gives two answers, each carrying the closing it stands on:
#    marg()   -- Marg's figure: the newest USABLE closing capture, by the item's printed name (sp_close_name), carried forward by the
#                spine's own movements (sp_move) to the day asked;
#    shelf()  -- the shelf figure: the newest physical count (the count family with the desk's corrections laid over, or a stock point
#                that is not the full count's own copy and not superseded) carried forward the same way, plus what has arrived and is
#                not yet in Marg. An item with no count has NO shelf figure (named 'no_count'), never Marg's.
#  The two are never mixed in one judgment. Five checks read them: the voucher guard (stock_app), Darpan's spot counts and traces
#  (stock_watch), the shelf-gap flags (shelf_figure), 'bill entry baaki' and the arrivals (stock_watch / shelf_figure, through key_of),
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
# =============================================================================
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import sys

VERSION = "1.0"
KIT = "S577_STOCK_ON_SPINE"
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

    def __init__(self, con=None, sp=None):
        self.con, self.sp, self.c = con, sp, {}


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
    return dict(last_sale=ls, sale_stamp=stamp_of(S, ls), last_pur=lp, pur_stamp=(min(stamp_of(B, lb), stamp_of(I, li)) if lp else ""))


def covers(day, stamp, c, d):
    """S570 (F-905): the newest export of a family (reaching `day`, captured at `stamp`) covers the closing `c` (end_day `d`) when it was
    captured after the closing, OR when its own capture, read by the estate's one capture rule (end_day, charter 11), stands for the
    end of a day at or after d. The morning order -- the sale report ~05:10, the closing ~05:17, both the end of yesterday -- is covered;
    a same-day capture inside shop hours gives None, and None never covers."""
    if stamp > c["stamp"]:
        return True
    e = end_day(str(day or ""), stamp_iso(stamp))
    return e is not None and e >= d


def tryable(c, reach_):
    """(ok, short) -- a closing is tried only when the spine's reach covers it (R1-B2): last_sale and last_pur at or past its end_day, and
    both newest exports cover it (covers: captured after it, or standing by their own capture for the end of a day at or after its
    end_day -- S570, F-905). short names what is missing: 'sale' | 'pur' | ''."""
    d = c.get("end_day") or ""
    if not d or not reach_:
        return False, "sale"
    if reach_["last_sale"] < d or not covers(reach_["last_sale"], reach_["sale_stamp"], c, d):
        return False, "sale"
    if not reach_["last_pur"] or reach_["last_pur"] < d or not covers(reach_["last_pur"], reach_["pur_stamp"], c, d):
        return False, "pur"
    return True, ""


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
    one copy, R2-C17), stamp_iso and end_day. Oldest stamp first. usable = end_day is not None."""
    ctx = _ctx(None, sp, ctx)
    if "caps" in ctx.c:
        return ctx.c["caps"]
    out = []
    if ready(sp):
        for r in sp.q("SELECT e.md5 AS md5, e.as_on AS as_on, e.stamp AS stamp FROM sp_export e WHERE e.md5 IN (SELECT DISTINCT md5 FROM sp_close_name) "
                      "ORDER BY e.stamp, e.md5"):
            si = stamp_iso(r["stamp"])
            e = end_day(str(r["as_on"] or ""), si) if si else None
            out.append(dict(md5=str(r["md5"]), as_on=str(r["as_on"] or ""), stamp=str(r["stamp"] or ""), stamp_iso=si, end_day=e, usable=e is not None))
    ctx.c["caps"] = out
    return out


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


def spine_move(sp, k20, d_from, d_to):
    """The net of every movement kind the proof carries (MOVE_KINDS, never OPENING) over (d_from, d_to] -- what Marg's figure moved by."""
    r = sp.q("SELECT COALESCE(SUM(units),0) AS u FROM sp_move WHERE k20=? AND date>? AND date<=? AND kind IN (%s)" % ",".join("?" * len(MOVE_KINDS)),
             k20, d_from, d_to, *MOVE_KINDS)
    return float(r[0]["u"] or 0) if r else 0.0


def taps(con, sp, name, since_iso, ctx=None):
    """Tapped arrivals the spine does not carry (stock_watch._arrivals, in_spine by key_of) after a moment -- reported beside a figure,
    never added to Marg's."""
    ctx = _ctx(con, sp, ctx)
    try:
        return sum(float(a["units"] or 0) for a in _sw()._arrivals(ctx.con, name, since_iso, sp, ctx=ctx) if not a["in_spine"])
    except Exception:                                         # noqa: BLE001
        return 0.0


def marg(con, sp, name, at=None, ctx=None):
    """Marg's figure at `at` (today): closing().units + sp_move of key_of(name) over (end_day, at] (MOVE_KINDS). approx=True whenever
    family() has more than one member, whatever `by` is. taps = tapped arrivals the spine does not carry, beside the figure."""
    ctx = _ctx(con, sp, ctx)
    c = closing(con, sp, name, at, ctx)
    if c is None:
        return None
    a = _iso(at)
    k = key_of(sp, name, ctx)
    fam = family(sp, k, c["md5"], ctx)
    sold, ret, bought = moves(sp, k, c["end_day"], a, incl_from=False)
    net = spine_move(sp, k, c["end_day"], a)
    return dict(figure=float(c["units"]) + net, closing=c, sold=sold, returned=ret, bought=bought, upto=a, key=k,
                approx=bool(c["approx"] or len(fam) > 1), family=fam, taps=taps(con, sp, name, c["stamp_iso"], ctx))


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


def early_bill(sp, k20, cap):
    """The early-morning capture (R3, R2-B3): a capture printed day D and taken before 09:00 on D stands for the end of D-1, but it can
    hold a bill dated D keyed before it. True when the key has a PURCHASE dated D in such a capture -- 'not judged on this closing'."""
    if cap is None:
        return False
    si = str(cap.get("stamp_iso") or "")
    if si[:10] != str(cap.get("as_on") or "") or si[11:16] >= "09:00":
        return False
    r = sp.q("SELECT 1 AS x FROM sp_move WHERE k20=? AND kind='PURCHASE' AND date=? LIMIT 1", k20, cap["as_on"])
    return bool(r)


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
            for nm, item, at, qty, src, bs, pid in con.execute("SELECT item_norm, item, at, qty_units, source, %s, id FROM stock_point WHERE source<>? AND COALESCE(status,'')<>'superseded' "
                                                               "ORDER BY at, id" % bcol, (FULL,)):
                if exclude_id is not None and int(pid) == int(exclude_id):
                    continue
                out[nm] = dict(qty=float(qty or 0), at=str(at), source=src, item=item, basis=bs)
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
            best = dict(qty=p["qty"], kind=p["source"], day=p["at"][:10], at=p["at"], count_id=None, fixed=False, marg0=None, item=p["item"])
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
    entered after it) + tapped arrivals not in Marg + scan arrivals. No count -> shelf=None, named='no_count' (never Marg's: charter 3).
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
    sold, ret, bought = moves(sp, k, mine["day"], a, incl_from=True)
    out.update(sold=round(share * sold, 2), returned=round(share * ret, 2), bought=round(share * bought, 2))
    arr = taps(con, sp, name, mine["at"], ctx)
    try:
        arr += float(_sf_shelf().scan_arrivals(con, sp, name, mine["day"], ctx=ctx) or 0)
    except Exception:                                         # noqa: BLE001
        pass
    out["arrived"] = arr
    if n == 1 and mine["kind"] == "count" and cap is not None:   # S454 9.1: a bill dated before the count, entered after it
        c = closing(con, sp, name, a, ctx)
        pk = pack_of(con, sp, name, ctx)[0]
        try:
            out["boundary"] = float(_sf_shelf().boundary_purchases(con, sp, name, mine["day"], mine.get("marg0"), (c["units"] if c else None),
                                                                   (c["as_on"] if c else None), pk, ctx=ctx) or 0)
        except Exception:                                     # noqa: BLE001
            out["boundary"] = 0.0
    v = mine["qty"] - out["sold"] + out["returned"] + out["bought"] + out["boundary"] + arr
    if v < 0:
        out["named"], v = "below_zero", 0.0
    out["shelf"] = int(round(v))
    out["approx"] = n > 1
    return out


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
    records = (float(M["figure"]) + float(M["taps"] or 0)) if M else None
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
    return dict(expected=records, basis="marg", provisional=float(M["taps"] or 0), as_on=M["closing"]["as_on"], approx=False,
                close=float(M["closing"]["units"]), sold=float(M["sold"] or 0), bought=float(M["bought"] or 0), records=records, terms=[])


# ------------------------------------------------------------------ the side-by-side week (witness only; 4b-2 retires the old ways)
def witness(con, sp, out_dir=None, when=None):
    """For every item of the newest usable capture: stock_figure.marg against stock_watch.expected_units against the PC's newest
    push_expected row (stock_feed), each with its day; marg_shadow's line where sh_diff has one; per pair the items a pack or more apart,
    with the named reason. Written to <spine dir>/stock_figure_witness_<Mon..Sun>.txt (overwritten a week later; nothing deleted)."""
    ctx = Ctx(con, sp)
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


def main(argv):
    if not argv or argv[0] != "witness":
        print("usage: stock_figure.py witness   (the nightly side-by-side file; read only)")
        return 2
    for flag in ("/root/finance/_off/ALL_OFF", os.path.join(HERE, "_off", "ALL_OFF")):
        if os.path.exists(flag):
            print("stock_figure: switched off (%s)" % flag)
            return 0
    db = os.environ.get("FINANCE_DB") or os.path.join(HERE, "finance.db")
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=60)
    sp = _sw().Spine()
    p = witness(con, sp)
    con.close()
    print("stock_figure witness written: %s" % p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
