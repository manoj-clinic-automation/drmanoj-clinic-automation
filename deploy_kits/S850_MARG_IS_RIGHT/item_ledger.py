#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
item_ledger.py -- S845_ITEM_LEDGER (16-Nov-2026, Sanjeevni session 470; D992).

THE OWNER, 16-Nov-2026 07:54-09:46 IST: "I also need to know latest stock of items, so a search box somewhere, and it opens the item ledger ...
it flags any unwarranted stock discrepancies, so I don't need to open marg item ledger everytime"; "each sale purchase etc to be listed in
ledger against the bill or voucher with their numbers, can purchase listing open the scanned purchase bill inline, also any new purchase that's
scanned but not entered in marg be shown there, along with its scanned bills and its read lines and expected stock"; "should be able to view
full ledger also, and run a date range query"; "ok" (09:46) on mock-up v2 (https://claude.ai/artifact/Sp2SJZtrNrX6P5RzNHZXLi).

THE PAGE: /finance/sanjeevni/ledger -- the doctor only (checker), as the Marg watch. READ ONLY: it writes no table, no setting, no file.
  * a search box (any 2 letters of a name, the stock record's items) -> the item's page;
  * Marg stock (the latest closing) · expected stock (Marg + what arrived and is not in Marg yet) · the days that need a look;
  * "Arrived -- not yet in Marg": the Purchase bills page's own list of scans waiting for their Marg bill (provisional_s781.provisional --
    one list, never a second), each scan inline with its read lines; a line counts into the expected stock only when it is this item by the
    order tracker's own matcher (order_track.match_lines) AND its units are proven (marg_hand_change's own factor) -- else shown, not added;
  * the ledger, newest day first: each sale, sale return, purchase, purchase return against its bill number; Amir's stock vouchers against
    their Marg voucher number (the spine's own rule for a filed voucher); each day's opening, expected closing and Marg's closing;
  * a red day is the Marg watch's own counted move (marg_hand_change, the ONE rule) -- with the Marg watch's own "Ask Marg's Stock
    Register" (its existing door; this page posts to it and nothing else); a move explained (a record, or Marg's own register) is green;
  * Last 30 days · Full ledger (from the stock record's opening) · a date range; one totals line for the period; "only days that need a look".
Quantities are the stock record's own units: a strip item as strips:tabs, any other in its own word (qty_words).
OFF: /root/finance/_off/ALL_OFF or /root/finance/spine/OFF -- the page then says so.
"""
import datetime as dt
import html
import json
import os
import re
import sqlite3
import sys

KIT = "S845_ITEM_LEDGER"
KIT2 = "S847_LEDGER_ARRIVED"   # 16-Nov-2026: a stale scan or a misread quantity is shown, never added to the expected stock
VERSION = "S847-ITEM-LEDGER-1.3"
HERE = os.path.dirname(os.path.abspath(__file__))
SPINE_DIR = os.path.join(HERE, "spine")
SPINE_DB = os.environ.get("SPINE_DB") or os.path.join(SPINE_DIR, "spine.db")
OFF_FLAGS = (os.path.join(HERE, "_off", "ALL_OFF"), os.path.join(SPINE_DIR, "OFF"))
PAGE = "/finance/sanjeevni/ledger"
WATCH = "/finance/sanjeevni/marg-watch"
PURCHASE_PREFIX = "/finance/purchase"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
TOL = 0.5
FIND_MAX = 15
LAST_DAYS = 30

_db = None
_require = None


# ====================================================================== small helpers
def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def now_ist():
    return dt.datetime.now(IST)


def today():
    return now_ist().date()


def K(n):
    return re.sub(r"\s+", " ", (n or "").strip())[:20].strip()


def dmon(iso):
    s = str(iso or "")[:10]
    return "%s-%s" % (s[8:10], s[5:7]) if len(s) == 10 else s


def dday(iso):
    try:
        d = dt.date.fromisoformat(str(iso)[:10])
        return "%s %s" % (d.strftime("%a"), d.strftime("%d-%m"))
    except ValueError:
        return str(iso or "")


def _iso(s):
    try:
        return dt.date.fromisoformat(str(s or "")[:10]).isoformat()
    except ValueError:
        return None


def is_off():
    return next((f for f in OFF_FLAGS if os.path.exists(f)), None)


def _table(con, name):
    try:
        return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None
    except sqlite3.Error:
        return False


def _H():
    import marg_hand_change                                   # noqa: PLC0415 -- the Marg watch's engine; read only here
    return marg_hand_change


def _BW():
    import marg_billwatch                                     # noqa: PLC0415 -- the Marg watch; its readers only
    return marg_billwatch


def _PV():
    import provisional_s781                                   # noqa: PLC0415 -- the Purchase bills page's own list and panel parts
    return provisional_s781


def _SB():
    if SPINE_DIR not in sys.path:
        sys.path.insert(0, SPINE_DIR)
    import spine_build                                        # noqa: PLC0415 -- its voucher-day rule only
    return spine_build


def spine_con(path=None):
    """The stock record, read only. None when it is not there."""
    p = path or SPINE_DB
    if not os.path.exists(p):
        return None
    try:
        c = sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=10)
        c.execute("SELECT 1 FROM sp_item LIMIT 1")
        return c
    except sqlite3.Error:
        return None


# ====================================================================== quantities
class Unit(object):
    """The item's own unit: strip items in strips:tabs (the owner's count convention, 29-Sep); others in their own word."""

    def __init__(self, packing, unit_kind, name=""):
        self.packing, self.unit_kind, self.name = packing or "", unit_kind or "", name or ""
        m = re.match(r"^(\d+)\*(\d+)$", self.packing.rstrip("."))
        self.n = int(m.group(1)) * int(m.group(2)) if m else 1
        self.strip = self.unit_kind != "WHOLE" and self.n > 1 and not self._whole_word()

    def _whole_word(self):
        try:
            import qty_words                                  # noqa: PLC0415
            return bool(qty_words.whole_unit_of(self.name))
        except Exception:                                     # noqa: BLE001
            return False

    def fmt(self, u, sign=False):
        if u is None:
            return "—"
        v = float(u)
        neg = v < -1e-9
        a = abs(v)
        if self.strip:
            s, t = int(a // self.n), a - (a // self.n) * self.n
            t = int(round(t)) if abs(t - round(t)) < 1e-6 else round(t, 1)
            body = "%d:%s" % (s, t)
        else:
            try:
                import qty_words                              # noqa: PLC0415
                body = qty_words.words(a, self.packing, self.unit_kind, name=self.name)
            except Exception:                                 # noqa: BLE001
                body = ("%g" % round(a, 2))
        return ("−" if neg else ("+" if sign and v > 1e-9 else "")) + body

    def word(self):
        return "strips:tabs" if self.strip else "its own unit"


class Plain(Unit):
    """The stock record's own count, plain -- for a key whose members differ in pack size (no one strip size is right for all)."""

    def __init__(self):
        Unit.__init__(self, "", "PLAIN", "")
        self.strip = False

    def fmt(self, u, sign=False):
        if u is None:
            return "—"
        v = float(u)
        body = ("%g" % round(abs(v), 2))
        return ("−" if v < -1e-9 else ("+" if sign and v > 1e-9 else "")) + body

    def word(self):
        return "the stock record's count (its sizes differ in pack)"


# ====================================================================== the stock record's items
def find(sp, q, limit=FIND_MAX):
    """[dict(key, name, marg, as_on, n)] -- items whose name holds q (2 letters or more), those starting with it first. The figure in the
    item page's own unit (item())."""
    q = re.sub(r"\s+", " ", str(q or "").upper()).strip()[:60]
    if len(q) < 2 or sp is None:
        return []
    rows = sp.execute("SELECT k20, name FROM sp_item WHERE UPPER(name) LIKE ? ORDER BY name", ("%" + q + "%",)).fetchall()
    by = {}
    for k, nm in rows:
        by.setdefault(k, nm)
    top = sorted(by.items(), key=lambda kv: (0 if kv[1].upper().startswith(q) else 1, kv[1].upper().find(q), kv[1]))[:limit]
    out = []
    for k, nm in top:                                         # the unit and figure only for the rows shown (review: 2-letter keystrokes)
        it = item(sp, k)
        c = sp.execute("SELECT as_on, units FROM sp_close WHERE k20=? ORDER BY as_on DESC LIMIT 1", (k,)).fetchone()
        out.append(dict(key=k, name=nm, marg=(it["unit"].fmt(c[1]) if (c and it) else "not in Marg's closing"), as_on=c[0] if c else ""))
    return out


def item(sp, key):
    """dict(key, names, packing, unit_kind, unit) for a stock-record key; None when unknown."""
    rows = sp.execute("SELECT name, packing, unit_kind, last_seen FROM sp_item WHERE k20=? ORDER BY last_seen DESC, name", (key,)).fetchall()
    if not rows:
        return None
    nm, pk, uk, _ls = rows[0]
    sizes = {Unit(r[1], r[2], r[0]).n if Unit(r[1], r[2], r[0]).strip else 0 for r in rows}
    unit = Unit(pk, uk, nm) if len(sizes) == 1 else Plain()   # members of one key in different strip sizes: plain units, never a wrong strip
    return dict(key=key, names=sorted({r[0] for r in rows}), name=nm, packing=pk, unit_kind=uk, unit=unit,
                family=len({r[0] for r in rows}) > 1)


def first_day(sp):
    r = sp.execute("SELECT MIN(date) FROM sp_move WHERE kind='OPENING'").fetchone()
    return (r[0] if r and r[0] else "2026-04-01")


# ====================================================================== Amir's filed vouchers (the spine's own rule, with the number)
def vouchers(con, sp, key):
    """[dict(day, units, no, kind)] of this key -- every line of a voucher batch that is in Marg (the newest stock_voucher_entered row of the
    batch carries a voucher number; no stock_voucher_void row voids it), read only."""
    if con is None or not (_table(con, "stock_voucher_entered") and _table(con, "stock_voucher_line")):
        return []
    SB = _SB()
    alias = {r[0]: r[1] for r in sp.execute("SELECT alias, k20 FROM sp_alias")}
    state = {}
    for cid, rno, kind, bno, vno, eon, at in con.execute("SELECT count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, at "
                                                         "FROM stock_voucher_entered ORDER BY id"):
        state[(cid, rno, kind, bno)] = (vno, eon, at, kind)
    void = set()
    if _table(con, "stock_voucher_void"):
        void = {tuple(r) for r in con.execute("SELECT count_id, round_no, kind, batch_no FROM stock_voucher_void")}
    out = []
    for cid, rno, kind, bno, it, ch in con.execute("SELECT count_id, round_no, kind, batch_no, item, change FROM stock_voucher_line"):
        st = state.get((cid, rno, kind, bno))
        if not st or not str(st[0] or "").strip() or (cid, rno, kind, bno) in void or not it:
            continue
        k = K(it)
        if alias.get(k, k) != key:
            continue
        d = SB._voucher_day(st[1], st[2])
        if d:
            out.append(dict(day=d, units=float(ch or 0), no=str(st[0]).strip(), kind=str(st[3] or "")))
    return out


# ====================================================================== the Marg watch's own moves (read only)
def hand_rows(con, key):
    """[dict] of marg_hand_change for this key, each with `state`: bad (counted -- red) · expl (a record or Marg's register explains it) ·
    closed (he closed it on the Marg watch) · rename · cleared; and `why` in the Marg watch's own words."""
    if con is None or not _table(con, "marg_hand_change"):
        return []
    H = _H()
    rows = [r for r in H.rows_for_page(con, all_rows=True) if r.get("k20") == key]
    if not rows:
        return []
    try:
        BW = _BW()
        acts = BW.hand_acts(con)
        regs = BW._reg_all(con) if _table(con, "mi_register") else []
    except Exception:                                         # noqa: BLE001
        BW, acts, regs = None, {}, []
    for r in rows:
        r["why"] = H.why_of(r)
        reg = None
        if BW is not None and regs:
            try:
                reg = BW.reg_verdict(con, r, regs)
            except Exception:                                 # noqa: BLE001
                reg = None
        r["reg"] = reg
        act = (acts or {}).get(r["id"]) or {}
        if r.get("rec_kind"):
            r["state"] = "expl"
        elif reg and reg.get("kind") == "marg_only":
            r["state"], r["why"] = "expl", reg.get("note") or r["why"]
        elif r["kind"] == "rename":
            r["state"] = "rename"
        elif r["status"] != "open":
            r["state"] = "cleared"
        elif act.get("action") == "close":
            r["state"] = "closed"
        else:
            r["state"] = "bad"
            if reg and reg.get("note"):
                r["why"] = r["why"] + " " + reg["note"]
        r["asked"] = False
    try:                                                      # an open Stock Register ask on the row (S837): the button says so
        if BW is not None:
            for a in BW._reg_rows(con, "AND closed_at IS NULL"):
                for kk in str(a.get("row_keys") or "").split(","):
                    for r in rows:
                        if kk == "hand:%d" % int(r["id"]):
                            r["asked"] = True
    except Exception:                                         # noqa: BLE001
        pass
    return rows


# ====================================================================== the ledger
def _sup_names(sp):
    return {(s, b, d): n for s, b, d, n in sp.execute("SELECT supkey, bill, date, supplier FROM sp_purchase_bill")}


def ledger(con, sp, key, d1, d2, hands=None):
    """The item's ledger d1..d2: dict(days=[...] newest first, totals, opening, closing). Every figure from the stock record (sales, bills,
    Marg's closings), Amir's filed vouchers and the Marg watch's rows; nothing written."""
    it = item(sp, key)
    U = it["unit"]
    closes = {d: u for d, u in sp.execute("SELECT as_on, units FROM sp_close WHERE k20=? ORDER BY as_on", (key,))}
    moves = sp.execute("SELECT date, kind, units, ref FROM sp_move WHERE k20=? AND date<=? ORDER BY date", (key, d2)).fetchall()
    vs = [v for v in vouchers(con, sp, key) if v["day"] <= d2]
    hands = hand_rows(con, key) if hands is None else hands
    sup = _sup_names(sp)
    # the opening: Marg's own closing before d1; else the record's own balance before d1
    before = [d for d in closes if d < d1]
    if before:
        o_day = max(before)                                   # Marg's closing holds everything up to its own day; what came after it, before d1, is added
        bal = float(closes[o_day]) + sum(float(m[2]) for m in moves if o_day < m[0] < d1) + sum(v["units"] for v in vs if o_day < v["day"] < d1)
        o_src = "Marg's closing of %s" % dmon(o_day) + (" + the days after it" if any(o_day < m[0] < d1 for m in moves) else "")
    else:
        bal = sum(float(m[2]) for m in moves if m[0] < d1) + sum(v["units"] for v in vs if v["day"] < d1)
        o_src = "the stock record's own balance"
    opening = bal
    by = {}
    for d, kind, u, ref in moves:
        if d < d1:
            continue
        by.setdefault(d, []).append(_entry(kind, u, ref, d, sup))
    for v in vs:
        if v["day"] >= d1:
            by.setdefault(v["day"], []).append(dict(order=4, kind="voucher", label="Stock %s · Amir's voucher" % ("receive" if v["units"] > 0 else "issue"),
                                                    ref="Marg voucher %s" % v["no"], u=v["units"]))
    hand_by = {}
    for h in hands:
        if d1 <= str(h["day_to"])[:10] <= d2:
            hand_by.setdefault(str(h["day_to"])[:10], []).append(h)
    try:
        from_day = _H().setting(con, "hand.from_day") or "2026-10-16"
    except Exception:                                         # noqa: BLE001
        from_day = "2026-10-16"
    days = sorted(set(by) | {d for d in closes if d1 <= d <= d2} | set(hand_by))
    out = []
    pend, owed = [], []                                         # purchases of the last week; bills Marg's closing had not taken in yet
    T = dict(pur=0.0, pur_bills=set(), sale=0.0, sale_bills=set(), sret=0.0, pret=0.0, vin=0.0, vout=0.0, other=0.0, nonrec=0.0, n_bad=0)
    for d in days:
        if d < d1 or d > d2:
            continue
        ents = sorted(by.get(d, []), key=lambda e: (e["order"], e.get("ref") or ""))
        op = bal
        run = op
        for e in ents:
            run += e["u"]
            e["bal"] = run
            k = e["kind"]
            if k == "PURCHASE":
                T["pur"] += e["u"]; T["pur_bills"].add(e["ref"])
                pend.append(dict(u=e["u"], ref=e["ref"], label=e["label"], day=d))
            elif k == "SALE":
                T["sale"] += e["u"]; T["sale_bills"].add(e["ref"])
            elif k == "SALE_RETURN":
                T["sret"] += e["u"]
            elif k == "PURCHASE_RETURN":
                T["pret"] += e["u"]
            elif k == "voucher":
                T["vin" if e["u"] > 0 else "vout"] += e["u"]
            else:
                T["other"] += e["u"]
        day = dict(day=d, opening=op, expected=run, entries=ents, marg=closes.get(d), diff=None, state="", hands=hand_by.get(d, []))
        hs = day["hands"]
        if any(h["state"] == "bad" for h in hs):               # the Marg watch's counted move: red, whatever this key's closings hold (review M1)
            day["state"] = "bad"
            T["n_bad"] += 1
            T["nonrec"] += sum(float(h["shift"] or 0) for h in hs if h["state"] == "bad")
        if d in closes:
            m = float(closes[d])
            diff = m - run
            day["diff"] = diff
            if day["state"] == "bad":
                pass
            elif hs:
                day["state"] = "expl" if any(h["state"] == "expl" for h in hs) else hs[0]["state"]
            elif abs(diff) < TOL:
                day["state"] = "ok"
            else:
                got = _late(diff, d, pend, owed)
                if got:
                    day["state"], day["late"] = got
                else:
                    day["state"] = "old" if d < from_day else "differs"
            bal = m
            cut = (dt.date.fromisoformat(d) - dt.timedelta(days=7)).isoformat()
            pend[:] = [p for p in pend if p["day"] > cut]
            owed[:] = [p for p in owed if p["day"] > (dt.date.fromisoformat(d) - dt.timedelta(days=21)).isoformat()]
        else:
            bal = run
        out.append(day)
    closing_day = max([d for d in closes if d <= d2] or [""]) or None
    totals = dict(opening=opening, opening_src=o_src, purchased=T["pur"], pur_bills=len(T["pur_bills"]), sold=T["sale"],
                  sale_bills=len(T["sale_bills"]), sret=T["sret"], pret=T["pret"], vin=T["vin"], vout=T["vout"], other=T["other"],
                  nonrec=T["nonrec"], n_bad=T["n_bad"], closing=closes.get(closing_day) if closing_day else None, closing_day=closing_day,
                  end=bal)
    out.reverse()
    return dict(item=it, days=out, totals=totals, d1=d1, d2=d2)


def _late(diff, d, pend, owed):
    """A bill Marg's closing had not taken in yet, or took in late -- the Marg watch's own OWED reading, shown in words (never counted red):
    Marg below by exactly one, two or three purchase lines of the last week -> ('late', words); Marg above by exactly bills owed -> ('late_in',
    words). None otherwise."""
    import itertools                                          # noqa: PLC0415
    if diff < 0:
        taken = {id(p) for p in owed}                         # by identity: two equal lines of one bill (two batches) stay two
        cand = [p for p in pend if id(p) not in taken]
        for n in (1, 2, 3):
            for c in itertools.combinations(cand, n):
                if abs(sum(p["u"] for p in c) + diff) < TOL:
                    owed.extend(c)
                    return "late", "Marg's closing had not taken in %s yet." % "; ".join(dict.fromkeys("bill %s (%s, %s)" % (p["ref"], p["label"].split(" · ", 1)[-1], dmon(p["day"])) for p in c))
    elif owed:
        for n in (1, 2, 3):
            for c in itertools.combinations(list(owed), n):
                if abs(sum(p["u"] for p in c) - diff) < TOL:
                    gone = {id(p) for p in c}
                    owed[:] = [p for p in owed if id(p) not in gone]
                    return "late_in", "Marg took in %s at this closing — keyed late, nothing missing." % "; ".join(dict.fromkeys("bill %s of %s" % (p["ref"], dmon(p["day"])) for p in c))
    return None


def _entry(kind, u, ref, d, sup):
    u = float(u or 0)
    if kind == "SALE":
        return dict(order=3, kind=kind, label="Sale", ref=str(ref or ""), u=u)
    if kind == "SALE_RETURN":
        return dict(order=2, kind=kind, label="Sale return", ref=str(ref or ""), u=u)
    if kind in ("PURCHASE", "PURCHASE_RETURN"):
        sk, _, bill = str(ref or "").partition("/")
        name = sup.get((sk, bill, d)) or sk
        return dict(order=1 if kind == "PURCHASE" else 5, kind=kind, label=("Purchase · " if kind == "PURCHASE" else "Purchase return · ") + name,
                    ref=bill, supkey=sk, u=u)
    if kind == "OPENING":
        return dict(order=0, kind=kind, label="Opening of the stock record", ref="", u=u)
    if kind == "RENAME_SPLIT":
        return dict(order=6, kind=kind, label="Name split in Marg (sizes)", ref=str(ref or ""), u=u)
    return dict(order=7, kind=kind, label="Reconciliation in the stock record", ref=str(ref or ""), u=u)


# ====================================================================== arrived -- not yet in Marg
def arrived(con, sp, key, months=None):
    """The Purchase bills page's own list of scans waiting for their Marg bill (this month and last), with the lines that are this item.
    [dict(scan, lines=[dict(name, qty, units|None, why)], units_ok, units)] -- only scans with at least one line of this item."""
    if con is None:
        return []
    try:
        PV = _PV()
    except Exception:                                         # noqa: BLE001
        return []
    it = item(sp, key)
    if months is None:
        t = today()
        prev = (t.replace(day=1) - dt.timedelta(days=1))
        months = [prev.strftime("%Y-%m"), t.strftime("%Y-%m")]
    try:
        import order_track as OT                              # noqa: PLC0415 -- the tracker's own matcher (S825's)
        octx = OT.Ctx(con)
        sf = octx.sf if getattr(octx, "ok", False) else None
    except Exception:                                         # noqa: BLE001
        OT, sf = None, None
    factor = _factor(sp, key)
    reach, grace = _reach(sp), _grace(con)
    big = _plausible_max(sp, key)
    out = []
    rf = con.row_factory
    for ym in months:
        try:
            con.row_factory = sqlite3.Row
            rows = PV.provisional(con, ym)
        except Exception:                                     # noqa: BLE001
            rows = []
        finally:
            con.row_factory = rf
        for x in rows:
            mine = []
            sday = str(x.get("day") or x.get("date") or "")[:10]
            stale = _stale(sday, reach, grace)
            for ln in x.get("lines") or []:
                if not _is_item(con, OT, sf, x, ln, it):
                    continue
                q = ln.get("qty")
                units = (float(q) * factor) if (q is not None and factor) else None
                why = "" if units is not None else ("the quantity was not read" if q is None else
                                                    "its units cannot be proven from Marg's own bills, so it is not added")
                if units is not None and stale:               # S847: Marg's purchases have moved past this scan -- not arriving any more
                    units, why = None, stale
                elif units is not None and big is not None and units > big:   # S847: a quantity far beyond the item's own -- a misread
                    units, why = None, ("the quantity read (%g) is far beyond this item's own purchases, so it looks misread and is not added "
                                        "— the paper decides" % float(q))
                mine.append(dict(name=ln.get("name"), batch=ln.get("batch"), expiry=ln.get("expiry"), qty=q, units=units, why=why))
            if mine:
                twin = next((w for w in (x.get("why") or []) if str(w).startswith("probably already in Marg")), "")
                ok = [m["units"] for m in mine if m["units"] is not None]
                out.append(dict(scan=x, lines=mine, units=(sum(ok) if not twin else 0.0), twin=twin, all_lines=x.get("lines") or []))
    return out


def _reach(sp):
    """The newest purchase-bill day Marg's purchases hold (never past today) -- the stock record's own (spine_read.purchases_upto's rule)."""
    try:
        r = sp.execute("SELECT MAX(date) FROM sp_purchase_bill WHERE direction='PURCHASE' AND date<=?", (today().isoformat(),)).fetchone()
        return r[0] if r and r[0] else None
    except sqlite3.Error:
        return None


def _grace(con):
    """arrival.bill_grace_days -- the arrivals' own grace (stock_watch.settings, the one settings reader), 3 when unread."""
    try:
        import stock_watch                                    # noqa: PLC0415
        return max(1, int(stock_watch.settings(con).get("bill_grace_days") or 3))
    except Exception:                                         # noqa: BLE001
        return 3


def _stale(sday, reach, grace):
    """S847: a scan whose day is more than the grace before Marg's newest purchase bill is not 'arriving' any more: Marg's purchases have moved
    past it, so it is either in Marg under another number or was never entered -- shown, never added. '' when it still counts."""
    try:
        d = dt.date.fromisoformat(str(sday)[:10])
        r = dt.date.fromisoformat(str(reach)[:10])
    except (TypeError, ValueError):
        return ""
    if (r - d).days > grace:
        return ("scanned %s, and Marg's purchases already run to %s — not added: it is in Marg under another number or was never entered "
                "(the Purchase bills page settles it)" % (dmon(d.isoformat()), dmon(r.isoformat())))
    return ""


def _plausible_max(sp, key):
    """S847: the most one waiting line may add -- five times the item's largest purchase line or its highest Marg closing, whichever is
    larger. None when the item has neither (then nothing is judged a misread)."""
    try:
        a = sp.execute("SELECT MAX(units) FROM sp_purchase_line WHERE k20=? AND direction='PURCHASE'", (key,)).fetchone()[0] or 0
        b = sp.execute("SELECT MAX(units) FROM sp_close WHERE k20=?", (key,)).fetchone()[0] or 0
    except sqlite3.Error:
        return None
    m = max(float(a), float(b))
    return 5.0 * m if m > 0 else None


def _is_item(con, OT, sf, x, ln, it):
    nm = str(ln.get("name") or "")
    if not nm:
        return False
    if OT is not None and sf is not None:
        try:
            pa = OT._pa()
            sn = pa.supplier_key(x.get("dealer") or "")
            for name in it["names"]:
                if name in OT.match_lines(con, sn, [name], [(nm, x.get("stamp") or "")], sf):
                    return True
            return False
        except Exception:                                     # noqa: BLE001
            pass
    a = re.sub(r"[^A-Z0-9]", "", nm.upper())
    return any(re.sub(r"[^A-Z0-9]", "", n.upper()) == a for n in it["names"])


def _factor(sp, key):
    """Units per Marg quantity for this key: the stock record's own purchase lines (units / (qty + free)), when they all agree; else None.
    The Marg watch's M1 rule: an unproven factor is never taken as 1."""
    fs = set()
    for q, f, u in sp.execute("SELECT qty, free, units FROM sp_purchase_line WHERE k20=? AND direction='PURCHASE'", (key,)):
        n = (q or 0) + (f or 0)
        if n and u:
            fs.add(round(float(u) / float(n), 3))
    return fs.pop() if len(fs) == 1 else None


# ====================================================================== a purchase row's paper (lazy)
def bill_panel(con, supkey, bill_no, day):
    """The Marg purchase bill's scan inline, and its lines beside Marg's -- made by the Purchase bills page's own parts (as the Marg watch's
    _agree_panel). (html, code). The connection's row factory is put back as it was."""
    rf = con.row_factory
    try:
        con.row_factory = sqlite3.Row
        return _bill_panel(con, supkey, bill_no, day)
    finally:
        con.row_factory = rf


def _bill_panel(con, supkey, bill_no, day):
    if not _table(con, "purchase_bill"):
        return "<p class='note'>This bill is not in the purchase register yet.</p>", 200
    PV, S = _PV(), _BW().SR()
    pa = PV.PA()
    rows = [dict(r) for r in con.execute("SELECT b.id, b.supplier, b.supplier_norm, b.bill_no, b.bill_date, b.amount_p FROM purchase_bill b "
                                         "WHERE b.bill_no=? AND b.bill_date=?", (str(bill_no), str(day)[:10]))]
    rows = [r for r in rows if re.sub(r"[^A-Z]", "", str(r["supplier"] or "").upper())[:8] == supkey] or rows
    if not rows:
        return "<p class='note'>This bill is not in the purchase register yet.</p>", 200
    link, b = None, rows[0]
    if _table(con, "purchase_scan_link"):
        for r in rows:                                        # the row that has its scan paired, when two rows share the number
            got = con.execute("SELECT asset_bill_id FROM purchase_scan_link WHERE bill_id=?", (r["id"],)).fetchone()
            if got:
                link, b = got, r
                break
    if not link:
        return "<p class='note'>No scan is paired with bill %s of %s yet.</p>" % (esc(b["bill_no"]), esc(b["supplier"])), 200
    sid = int(link[0])
    try:
        mlines = PV.marg_lines(con, b)
    except Exception:                                         # noqa: BLE001
        mlines = []
    slines = PV.Assets([sid]).lines.get(sid, [])
    return _paper(sid, slines, mlines, PV, S), 200


def _paper(sid, slines, mlines, PV, S):
    src = "%s/api/s738/scan/%d" % (PURCHASE_PREFIX, sid)
    viewer = ('<details class="s738v" ontoggle="window.s845open&&s845open(this)"><summary>The scanned paper ▾</summary><div class="s738vb"><div class="s738f" data-src="%s">'
              '</div></div></details><a class="lnk" href="%s" target="_blank" rel="noopener">Open the scan in a new tab</a>' % (esc(src), esc(src)))
    if not slines:                                            # the scan's lines not read (or the scan store not reachable): Marg's lines alone, no verdict
        rows = "".join('<tr><td>%s</td><td class="n">—</td><td class="n">%s</td><td></td></tr>' % (
            esc(m["name"]), esc("%g" % m["qty"]) if m.get("qty") is not None else "—") for m in mlines)
        table = ('<table class="items"><tr><th>Item</th><th class="n">Paper qty</th><th class="n">Marg qty</th><th></th></tr>%s</table>' % rows) if rows else ""
        return ('<div class="paper2"><div class="pv">%s</div><div class="pw">%s<p class="sub">The scan\'s item lines are not read, so Marg\'s lines are shown '
                'alone — compare them with the paper beside them.</p></div></div>') % (viewer, table)
    rows, same = [], bool(mlines)
    pairs = PV.pair_lines(slines, mlines)
    for a, m in pairs:
        miss = a is None or m is None
        qa = a.get("qty") if a else None
        qm = m.get("qty") if m else None
        if miss or (qa is not None and qm is not None and abs(float(qa) - float(qm)) > 1e-6):
            same = False
        rows.append('<tr class="%s"><td>%s</td><td class="n">%s</td><td class="n">%s</td><td>%s</td></tr>' % (
            "miss" if miss else "", esc((a or m)["name"]) + ((' <span class="sub">(Marg: %s)</span>' % esc(m["name"])) if a and m and PV._norm(a["name"]) != PV._norm(m["name"]) else ""),
            esc("%g" % qa) if qa is not None else "—", esc("%g" % qm) if qm is not None else "—",
            "<b>not in Marg</b>" if m is None else ("<b>not on the paper</b>" if a is None else "both")))
    table = ('<table class="items"><tr><th>Item</th><th class="n">Paper qty</th><th class="n">Marg qty</th><th></th></tr>%s</table>' % "".join(rows)
             if rows else '<p class="sub">No item lines were read on this scan.</p>')
    verdict = ('<p class="okw">Paper matches Marg.</p>' if same else
               ('<p class="sub">Where the paper and Marg differ, the Purchase bills page settles it: <a href="%s/page/scans">open it</a>.</p>' % PURCHASE_PREFIX))
    return '<div class="paper2"><div class="pv">%s</div><div class="pw">%s%s</div></div>' % (viewer, table, verdict)


# ====================================================================== the page
CSS = """
:root{--ink:#1d2430;--mute:#6b7380;--line:#e3e6ea;--bg:#f6f7f9;--green:#1d7a46;--greenbg:#e9f6ee;--red:#b42318;--redbg:#fdecea;--amber:#9a5b00;--amberbg:#fff4e0;--bluebg:#eaf1fc}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:var(--bg)}
.wrap{max-width:1180px;margin:0 auto;padding:14px 20px 60px}.crumb{color:var(--mute);font-size:13px;margin-bottom:6px}.crumb a{color:inherit}
h1{font-size:22px;margin:0 0 12px}.search{position:relative;max-width:560px;margin-bottom:14px}
.search input{width:100%;padding:11px 14px;font-size:15px;border:1px solid #c9ced6;border-radius:8px;background:#fff}
.sugg{position:absolute;left:0;right:0;top:46px;background:#fff;border:1px solid var(--line);border-radius:8px;box-shadow:0 6px 18px rgba(0,0,0,.08);z-index:5}
.sugg a{padding:8px 14px;display:flex;justify-content:space-between;gap:12px;color:var(--ink);text-decoration:none}.sugg a:hover,.sugg a.on{background:var(--bluebg)}
.sugg small{color:var(--mute)}.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin-bottom:14px}
.head{display:flex;gap:18px;flex-wrap:wrap}.head .name{flex:1 1 260px}.head .name b{font-size:19px}.head .name div{color:var(--mute);font-size:13px;margin-top:4px}
.fig{border:1px solid var(--line);border-radius:8px;padding:10px 16px;min-width:190px}.fig .lab{font-size:12px;color:var(--mute);text-transform:uppercase;letter-spacing:.03em}
.fig .val{font-size:26px;font-weight:650;margin:2px 0}.fig .sub{font-size:12.5px;color:var(--mute)}.fig.exp{background:var(--bluebg);border-color:#c9daf5}
.fig.flag{background:var(--redbg);border-color:#f3c3bd}.fig.flag .val{color:var(--red)}.fig.calm .val{color:var(--green)}
h2{font-size:15px;margin:0 0 10px}.pill{font-size:11.5px;padding:2px 8px;border-radius:20px;font-weight:600}.p-amber{background:var(--amberbg);color:var(--amber)}
table{width:100%;border-collapse:collapse}th{font-size:12px;color:var(--mute);text-align:left;font-weight:600;padding:6px 8px;border-bottom:1px solid var(--line)}
td{padding:6px 8px;border-bottom:1px solid #f0f1f3;vertical-align:top}td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.in{color:var(--green);font-weight:600}.btn{border:1px solid #c9ced6;background:#fff;border-radius:6px;padding:4px 10px;font-size:12.5px;cursor:pointer}
.btn.red{border-color:#e6a49c;color:var(--red)}.btn[disabled]{color:var(--mute);cursor:default;background:#f6f7f9}
.amberbox{border-left:4px solid #e3a33b}.day td{background:#fafbfc;font-weight:600;border-top:1px solid var(--line)}.day.bad td{background:var(--redbg)}
.day.differs td{background:var(--amberbg)}.why{background:var(--redbg);color:var(--red);font-size:13px}.expl{background:var(--greenbg);color:var(--green);font-size:13px}
.amb{background:var(--amberbg);color:var(--amber);font-size:13px}.grey{color:var(--mute);font-size:13px}.ok{color:var(--green);font-weight:700}.bad{color:var(--red);font-weight:700}
.drop td{background:#fbfcfd;padding:12px 10px}.num{font-family:ui-monospace,Consolas,monospace;font-size:12.5px}
.tools{display:flex;gap:10px;align-items:center;margin-bottom:10px;flex-wrap:wrap}.seg a{border:1px solid #c9ced6;background:#fff;padding:5px 12px;font-size:13px;color:var(--ink);text-decoration:none;display:inline-block}
.seg a:first-child{border-radius:6px 0 0 6px}.seg a:last-child{border-radius:0 6px 6px 0}.seg a+a{border-left:0}.seg a.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.sum{display:flex;gap:18px;flex-wrap:wrap;background:#f6f7f9;border:1px solid var(--line);border-radius:8px;padding:8px 14px;margin-bottom:10px;font-size:13px}
.foot,.note,.sub{color:var(--mute);font-size:12.5px}.okw{color:var(--green);font-weight:600}.paper2{display:flex;gap:16px;flex-wrap:wrap}.paper2 .pv{flex:1 1 420px}
.paper2 .pw{flex:1 1 360px}.s738f iframe{width:100%;height:560px;border:1px solid var(--line)}.s738f img{max-width:100%}.items td,.items th{font-size:12.5px}tr.miss td{background:var(--amberbg)}
label.tg{font-size:13px;display:flex;gap:6px;align-items:center;cursor:pointer}form.rng{display:inline-flex;gap:6px;align-items:center;font-size:13px}
"""

JS = """
<script>
(function(){
var q=document.getElementById('q'),s=document.getElementById('sugg'),t=null,pick=-1,seq=0;
function so(d){ if(typeof s738open==='function'){ s738open(d); } }
window.s845open=so;
function draw(rows){ if(!rows.length){s.hidden=true;s.innerHTML='';return;}
 s.innerHTML=rows.map(function(r){return '<a href="'+PAGE+'?k='+encodeURIComponent(r.key)+'"><span>'+esc(r.name)+'</span><small>Marg '+esc(r.marg)+(r.as_on?' · '+esc(r.as_on.slice(8,10)+'-'+r.as_on.slice(5,7)):'')+'</small></a>';}).join('');
 s.hidden=false;pick=-1;}
function esc(x){return String(x==null?'':x).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
if(q){q.addEventListener('input',function(){clearTimeout(t);var v=q.value.trim();if(v.length<2){seq++;draw([]);return;}
 t=setTimeout(function(){var my=++seq;fetch(PAGE+'/api/find?q='+encodeURIComponent(v),{credentials:'same-origin'}).then(function(r){return r.json();}).then(function(j){if(my===seq)draw((j&&j.items)||[]);}).catch(function(){});},180);});
 q.addEventListener('keydown',function(e){var a=s.querySelectorAll('a');if(!a.length)return;
  if(e.key==='Enter'&&(s.hidden||pick<0))return;               // nothing picked: the form searches what he typed
  if(e.key==='ArrowDown'){pick=Math.min(pick+1,a.length-1);}else if(e.key==='ArrowUp'){pick=Math.max(pick-1,0);}else if(e.key==='Enter'){e.preventDefault();location.href=a[pick].href;return;}else return;
  e.preventDefault();a.forEach(function(x,i){x.className=i===pick?'on':'';});});
 document.addEventListener('click',function(e){if(!e.target.closest('.search'))s.hidden=true;});}
document.querySelectorAll('[data-open]').forEach(function(b){b.addEventListener('click',function(){
 var r=document.getElementById(b.getAttribute('data-open'));if(!r)return;var on=r.style.display==='table-row';r.style.display=on?'none':'table-row';
 b.textContent=on?b.getAttribute('data-l1'):b.getAttribute('data-l2');
 var c=r.querySelector('[data-src2]');if(!on&&c&&!c.getAttribute('data-done')){c.setAttribute('data-done','1');
  fetch(c.getAttribute('data-src2'),{credentials:'same-origin'}).then(function(x){return x.text();}).then(function(h){c.innerHTML=h;var d=c.querySelector('details.s738v');if(d){d.open=true;so(d);}}).catch(function(){c.textContent='The paper could not be shown just now. Tap again.';c.removeAttribute('data-done');});}
 var d2=r.querySelector('details.s738v');if(!on&&d2){d2.open=true;so(d2);}});});
var ob=document.getElementById('onlybad');if(ob){ob.addEventListener('change',function(){document.querySelectorAll('#led tr.okd').forEach(function(x){x.style.display=ob.checked?'none':'';});
 document.querySelectorAll('#led tr.drop').forEach(function(x){x.style.display='none';});
 document.querySelectorAll('#led button[data-open]').forEach(function(b){b.textContent=b.getAttribute('data-l1');});});}
document.querySelectorAll('button[data-ask]').forEach(function(b){b.addEventListener('click',function(){b.disabled=true;b.textContent='Asking…';
 fetch(WATCH+'/api/register/ask',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({row:parseInt(b.getAttribute('data-ask'),10)})})
 .then(function(r){return r.json().then(function(j){return [r.ok,j];});}).then(function(a){b.textContent=(a[1]&&a[1].message)||(a[0]?'Asked':'Could not ask');if(!a[0])b.disabled=false;})
 .catch(function(){b.textContent='Could not ask — try again';b.disabled=false;});});});
})();
</script>
"""


def page_html(con, args):
    """The whole page for the request's arguments (k, q, r, from, to). Read only."""
    head = ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Item ledger</title><style>%s</style></head><body><div class="wrap">'
            '<div class="crumb"><a href="/finance/approvals">Sanjeevni Hub</a> › Go to › <b>Item ledger</b></div><h1>Item ledger</h1>') % CSS
    tail = ('<script>var PAGE=%s,WATCH=%s;</script>' % (json.dumps(PAGE), json.dumps(WATCH))) + _s738_js() + JS + "</div></body></html>"
    key, q = str(args.get("k") or "").strip(), str(args.get("q") or "").strip()
    off = is_off()
    sp = None if off else spine_con()
    q = q[:60]
    srch = ('<form class="search" method="get" action="%s"><input id="q" name="q" value="%s" placeholder="Type 2 or more letters of a medicine or orthotic…" autocomplete="off" %s>'
            '<div class="sugg" id="sugg" hidden></div></form>') % (PAGE, esc(q if not key else ""), "" if key else "autofocus")
    if off:
        return head + srch + '<div class="card"><p>The stock record is switched off (%s), so the ledger cannot be shown.</p></div>' % esc(os.path.basename(off)) + tail
    if sp is None:
        return head + srch + '<div class="card"><p>The stock record could not be opened just now. Reload in a minute.</p></div>' + tail
    try:
        if not key and len(q) >= 2:
            one = find(sp, q, 2)
            if len(one) == 1:                                 # one item holds what he typed (the Hub's Go to box): straight to it
                key = one[0]["key"]
        if not key:
            body = _search_body(sp, q)
            return head + srch + body + tail
        it = item(sp, key)
        if it is None:
            return head + srch + '<div class="card"><p>No item "%s" in the stock record. Search again above.</p></div>' % esc(key) + tail
        return head + srch + _item_body(con, sp, it, args) + tail
    finally:
        sp.close()


def _s738_js():
    try:
        return _BW().SR().S738_JS.split("<button", 1)[0]
    except Exception:                                         # noqa: BLE001
        return ""


def _search_body(sp, q):
    if len(q) < 2:
        return '<p class="note">Search any medicine or orthotic by 2 or more letters of its name — its stock, its ledger by bill and voucher, and what arrived but is not in Marg yet.</p>'
    rows = find(sp, q, 50)
    if not rows:
        return '<div class="card"><p>Nothing in the stock record holds "%s".</p></div>' % esc(q)
    li = "".join('<tr><td><a href="%s?k=%s">%s</a></td><td class="n">%s</td><td class="grey">%s</td></tr>' % (
        PAGE, esc(_u(r["key"])), esc(r["name"]), esc(r["marg"]), esc(("Marg's closing of " + dmon(r["as_on"])) if r["as_on"] else "")) for r in rows)
    return '<div class="card"><h2>%d item%s holding "%s"</h2><table><tr><th>Item</th><th class="n">Marg stock</th><th></th></tr>%s</table></div>' % (
        len(rows), "" if len(rows) == 1 else "s", esc(q), li)


def _u(s):
    from urllib.parse import quote                            # noqa: PLC0415
    return quote(str(s), safe="")


def _range(sp, args):
    r = str(args.get("r") or "30")
    t = today().isoformat()
    if r == "full":
        return "full", first_day(sp), t
    if r == "range":
        a, b = _iso(args.get("from")), _iso(args.get("to"))
        if a and b and a <= b:
            return "range", a, min(b, t)
        return "range", (today() - dt.timedelta(days=LAST_DAYS - 1)).isoformat(), t
    return "30", (today() - dt.timedelta(days=LAST_DAYS - 1)).isoformat(), t


def _item_body(con, sp, it, args):
    U = it["unit"]
    key = it["key"]
    rk, d1, d2 = _range(sp, args)
    HR = hand_rows(con, key)
    L = ledger(con, sp, key, d1, d2, HR)
    try:                                                      # S850 (D993 d): each purchase line carries its scan line's verdict
        import marg_right as _s850                           # noqa: PLC0415 -- beside this file
        _s850.annotate_ledger(con, it, L)
    except Exception as _e850:                                # noqa: BLE001 -- the ledger as before
        print("S850 ledger verdicts failed: %r" % (_e850,), file=sys.stderr)
    last = sp.execute("SELECT as_on, units FROM sp_close WHERE k20=? ORDER BY as_on DESC LIMIT 1", (key,)).fetchone()
    A = arrived(con, sp, key)
    add = sum(a["units"] for a in A)
    hands_all = [h for h in HR if h["state"] == "bad"]
    bad_days = sorted({str(h["day_to"])[:10] for h in hands_all}, reverse=True)
    marg_txt = U.fmt(last[1]) if last else "—"
    exp_txt = U.fmt((float(last[1]) if last else 0.0) + add) if last else "—"
    built = ""
    try:
        m = dict(sp.execute("SELECT key, value FROM sp_meta").fetchall())
        built = m.get("built", "")[:16].replace("T", " ")
    except sqlite3.Error:
        pass
    fam = (" · one figure for: %s" % ", ".join(it["names"])) if it["family"] else ""
    h = ['<div class="card head"><div class="name"><b>%s</b><div>Pack %s · quantities in %s%s</div></div>' % (esc(it["name"]), esc(it["packing"] or "—"), esc(U.word()), esc(fam)),
         '<div class="fig"><div class="lab">Marg stock</div><div class="val">%s</div><div class="sub">%s</div></div>' % (
             esc(marg_txt), esc(("Marg's closing of %s" % dmon(last[0])) if last else "not in Marg's closings")),
         '<div class="fig exp"><div class="lab">Expected stock</div><div class="val">%s</div><div class="sub">%s</div></div>' % (
             esc(exp_txt), esc(("Marg %s %s arrived, not yet in Marg" % (marg_txt, U.fmt(add, sign=True))) if add else
                 ("a waiting scan carries it but adds nothing — see below" if A else "nothing arrived waits for Marg"))),
         '<div class="fig %s"><div class="lab">Needs a look</div><div class="val">%d day%s</div><div class="sub">%s</div></div></div>' % (
             "flag" if bad_days else "calm", len(bad_days), "" if len(bad_days) == 1 else "s",
             esc(", ".join(dmon(x) for x in bad_days[:4]) + " · stock moved with no record") if bad_days else "nothing moved without a record")]
    h.append(_arrived_html(A, U))
    h.append(_ledger_html(L, U, key, rk, d1, d2))
    h.append('<p class="foot">From the stock record built %s (Marg\'s reports), Amir\'s filed vouchers and the Marg watch\'s own moves. '
             'Today\'s sales show after tomorrow morning\'s closing report. Batches and expiry: the Expiry watch.</p>' % esc(built or "—"))
    return "".join(h)


def _arrived_html(A, U):
    if not A:
        return ('<div class="card"><h2>Arrived — not yet in Marg</h2><p class="note">No scanned bill waiting for Marg carries this item '
                '(this month and last, as the Purchase bills page lists them).</p></div>')
    rows = []
    for i, a in enumerate(A):
        x = a["scan"]
        q = " + ".join(("%g" % m["qty"]) if m["qty"] is not None else "?" for m in a["lines"])
        tot = U.fmt(sum(m["units"] for m in a["lines"] if m["units"] is not None), sign=True) if any(m["units"] is not None for m in a["lines"]) else "—"
        note = a["twin"] or "; ".join(m["why"] for m in a["lines"] if m["why"]) or ""
        rows.append('<tr><td>%s</td><td>%s</td><td class="num">%s</td><td class="num">%s</td><td class="n in">%s</td><td class="grey">%s</td>'
                    '<td><button class="btn" data-open="ar%d" data-l1="Show scan ▾" data-l2="Hide scan ▴">Show scan ▾</button></td></tr>' % (
                        esc(dday(x.get("day") or x.get("date"))), esc(x.get("dealer") or "dealer not read"), esc(x.get("bill_no") or "—"),
                        esc(x.get("stamp")), esc(tot) + ('<div class="grey">paper qty %s</div>' % esc(q)), esc(note), i))
        PV = _PV()
        lines = "".join('<tr%s><td>%s</td><td class="num">%s</td><td>%s</td><td class="n">%s</td></tr>' % (
            ' style="background:#fffbe6"' if any(ln is m0 or (ln.get("name") == m0["name"]) for m0 in a["lines"]) else "",
            esc(ln.get("name")), esc(ln.get("batch") or ""), esc(ln.get("expiry") or ""), esc("%g" % ln["qty"] if ln.get("qty") is not None else "—"))
            for ln in a["all_lines"])
        src = "%s/api/s738/scan/%d" % (PURCHASE_PREFIX, int(x["id"]))
        rows.append('<tr class="drop" id="ar%d" style="display:none"><td colspan="7"><div class="paper2"><div class="pv"><details class="s738v" ontoggle="window.s845open&&s845open(this)">'
                    '<summary>The scanned paper ▾</summary><div class="s738vb"><div class="s738f" data-src="%s"></div></div></details>'
                    '<a class="lnk" href="%s" target="_blank" rel="noopener">Open the scan in a new tab</a></div><div class="pw"><b>Lines read from the scan</b>'
                    '<table class="items"><tr><th>Item (as printed)</th><th>Batch</th><th>Exp</th><th class="n">Qty</th></tr>%s</table>'
                    '<p class="sub">This item\'s line%s marked. When Amir enters this bill in Marg it leaves this list and its lines enter the ledger below by themselves.</p>'
                    '</div></div></td></tr>' % (i, esc(src), esc(src), lines, "" if len(a["lines"]) == 1 else "s"))
    return ('<div class="card amberbox"><h2>Arrived — not yet in Marg <span class="pill p-amber">%d bill%s</span></h2><table><tr><th>Scanned</th><th>Dealer</th>'
            '<th>Bill no.</th><th>Scan</th><th class="n">This item</th><th></th><th></th></tr>%s</table></div>') % (len(A), "" if len(A) == 1 else "s", "".join(rows))


def _ledger_html(L, U, key, rk, d1, d2):
    T = L["totals"]
    base = "%s?k=%s" % (PAGE, _u(key))
    seg = ('<div class="seg"><a class="%s" href="%s&r=30">Last 30 days</a><a class="%s" href="%s&r=full">Full ledger</a><a class="%s" href="%s&r=range&from=%s&to=%s">Date range</a></div>'
           % ("on" if rk == "30" else "", base, "on" if rk == "full" else "", base, "on" if rk == "range" else "", base, d1, d2))
    rng = ('<form class="rng" method="get" action="%s"><input type="hidden" name="k" value="%s"><input type="hidden" name="r" value="range">From '
           '<input type="date" name="from" value="%s"> to <input type="date" name="to" value="%s"> <button class="btn">Show</button></form>' % (PAGE, esc(key), d1, d2)) if rk == "range" else ""
    lab = {"30": "Last 30 days", "full": "Full ledger", "range": "Date range"}[rk]
    sold = -T["sold"]
    sm = ['<span><b>%s · %s to %s</b></span>' % (lab, dmon(d1), dmon(d2)),
          '<span>Opening <b>%s</b> <span class="grey">(%s)</span></span>' % (esc(U.fmt(T["opening"])), esc(T["opening_src"])),
          '<span>Purchased <b class="in">%s</b> (%d bill%s)</span>' % (esc(U.fmt(T["purchased"], sign=True)), T["pur_bills"], "" if T["pur_bills"] == 1 else "s"),
          '<span>Sold <b>%s</b> (%d bill%s)</span>' % (esc(U.fmt(-sold)), T["sale_bills"], "" if T["sale_bills"] == 1 else "s")]
    if abs(T["sret"]) > 1e-9 or abs(T["pret"]) > 1e-9:
        sm.append('<span>Returns <b>%s</b></span>' % esc(U.fmt(T["sret"] + T["pret"], sign=True)))
    if abs(T["vin"]) > 1e-9 or abs(T["vout"]) > 1e-9:
        sm.append('<span>Vouchers <b>%s / %s</b></span>' % (esc(U.fmt(T["vout"])), esc(U.fmt(T["vin"], sign=True))))
    if abs(T["other"]) > 1e-9:
        sm.append('<span>Stock record entries <b>%s</b></span>' % esc(U.fmt(T["other"], sign=True)))
    if T["n_bad"]:
        sm.append('<span style="color:var(--red)">Moved with no record <b>%s</b> (%d day%s)</span>' % (esc(U.fmt(T["nonrec"], sign=True)), T["n_bad"], "" if T["n_bad"] == 1 else "s"))
    if T["closing"] is not None:
        sm.append('<span>Closing <b>%s</b> <span class="grey">(Marg, %s)</span></span>' % (esc(U.fmt(T["closing"])), dmon(T["closing_day"])))
    rows = []
    for i, day in enumerate(L["days"]):
        st = day["state"]
        cls = {"bad": "day bad", "differs": "day differs"}.get(st, "day")
        okd = "" if st in ("bad",) else " okd"
        if day["marg"] is None and st == "bad":
            mk = '<span class="bad">✗</span> no Marg closing of this item this day — the Marg watch counted a move'
        elif day["marg"] is not None:
            mk = ('<span class="ok">✓</span> Marg %s' % esc(U.fmt(day["marg"])) if st in ("ok",) else
                  '<span class="bad">✗</span> Marg %s · <b>%s</b>' % (esc(U.fmt(day["marg"])), esc(U.fmt(day["diff"], sign=True))) if st == "bad" else
                  '<span class="ok">✓</span> Marg %s · <span style="color:var(--green)">explained</span>' % esc(U.fmt(day["marg"])) if st == "expl" else
                  'Marg %s · %s' % (esc(U.fmt(day["marg"])), esc(U.fmt(day["diff"], sign=True))))
        else:
            mk = '<span class="grey">no Marg closing this day</span>'
        rows.append('<tr class="%s%s"><td>%s</td><td colspan="4">Opening %s · expected closing %s</td><td class="n">%s</td><td class="chk">%s</td></tr>' % (
            cls, okd, esc(dday(day["day"])), esc(U.fmt(day["opening"])), esc(U.fmt(day["expected"])), esc(U.fmt(day["marg"] if day["marg"] is not None else day["expected"])), mk))
        for j, e in enumerate(day["entries"]):
            pid = "p%d_%d" % (i, j)
            btn = ""
            if e["kind"] in ("PURCHASE", "PURCHASE_RETURN") and e.get("ref"):
                btn = '<button class="btn" data-open="%s" data-l1="Scan ▾" data-l2="Scan ▴">Scan ▾</button>' % pid
            rows.append('<tr class="%s"><td></td><td>%s</td><td class="num">%s</td><td class="n in">%s</td><td class="n">%s</td><td class="n">%s</td><td>%s</td></tr>' % (
                "okd" if st != "bad" else "", esc(e["label"]), esc(e.get("ref") or ""), esc(U.fmt(e["u"], sign=True)) if e["u"] > 0 else "",
                esc(U.fmt(-e["u"])) if e["u"] < 0 else "", esc(U.fmt(e["bal"])), btn + (e.get("s850_html") or "")))
            if btn:
                src = "%s/api/bill?s=%s&b=%s&d=%s" % (PAGE, _u(e.get("supkey") or ""), _u(e["ref"]), day["day"])
                rows.append('<tr class="drop" id="%s" style="display:none"><td colspan="7"><div data-src2="%s">Opening the paper…</div></td></tr>' % (pid, esc(src)))
        for hrow in day["hands"]:
            if hrow["state"] == "bad":
                b = ('<button class="btn" disabled>Register asked — waiting</button>' if hrow["asked"] else
                     '<button class="btn red" data-ask="%d">Ask Marg\'s Stock Register</button>' % int(hrow["id"]))
                rows.append('<tr><td></td><td colspan="5" class="why">%s</td><td class="why">%s</td></tr>' % (esc(hrow["why"]), b))
            elif hrow["state"] == "expl":
                rows.append('<tr class="okd"><td></td><td colspan="6" class="expl">Explained: %s</td></tr>' % esc(hrow["why"]))
            elif hrow["state"] == "closed":
                rows.append('<tr class="okd"><td></td><td colspan="6" class="grey">You closed this on the Marg watch: %s</td></tr>' % esc(hrow["why"]))
            else:
                rows.append('<tr class="okd"><td></td><td colspan="6" class="grey">%s</td></tr>' % esc(hrow["why"]))
        if st == "differs":
            rows.append('<tr class="okd"><td></td><td colspan="6" class="amb">Marg differs by %s — not counted by the Marg watch (a bill Marg took in at another '
                        'closing, or a step put right within three closings).</td></tr>' % esc(U.fmt(day["diff"], sign=True)))
        elif st in ("late", "late_in"):
            rows.append('<tr class="okd"><td></td><td colspan="6" class="grey">%s</td></tr>' % esc(day.get("late") or ""))
        elif st == "old":
            rows.append('<tr class="okd"><td></td><td colspan="6" class="grey">Marg differs by %s — before the Marg watch began judging (%s).</td></tr>' % (
                esc(U.fmt(day["diff"], sign=True)), "16-10"))
    table = ('<table id="led"><tr><th style="width:96px">Date</th><th>Entry</th><th>Bill / voucher no.</th><th class="n">In</th><th class="n">Out</th>'
             '<th class="n">Balance</th><th></th></tr>%s</table>' % "".join(rows)) if rows else '<p class="note">No sale, bill, voucher or closing in these days.</p>'
    return ('<div class="card"><div class="tools"><h2 style="margin:0">Ledger</h2>%s%s<label class="tg"><input type="checkbox" id="onlybad"> Only days that need a look</label></div>'
            '<div class="sum">%s</div>%s<p class="foot">Each day opens on Marg\'s closing of the day before; the balance runs through the day\'s bills and vouchers '
            'to the expected closing, beside Marg\'s own.</p></div>') % (seg, rng, "".join(sm), table)


# ====================================================================== the routes (the doctor only)
def _mount():
    from flask import Blueprint, jsonify, request            # noqa: PLC0415

    bp = Blueprint("item_ledger", __name__)

    def _doc():
        return _require("checker")

    @bp.route(PAGE)
    def page():
        u, err = _doc()
        if err:
            return err
        return page_html(_db(), request.args), 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}

    @bp.route(PAGE + "/api/find")
    def api_find():
        u, err = _doc()
        if err:
            return err
        if is_off():
            return jsonify(ok=False, items=[])
        sp = spine_con()
        if sp is None:
            return jsonify(ok=False, items=[])
        try:
            return jsonify(ok=True, items=find(sp, str(request.args.get("q") or "")[:60]))
        finally:
            sp.close()

    @bp.route(PAGE + "/api/bill")
    def api_bill():
        u, err = _doc()
        if err:
            return err
        try:
            body, code = bill_panel(_db(), str(request.args.get("s") or "")[:8], str(request.args.get("b") or "")[:40], _iso(request.args.get("d")) or "")
        except Exception as e:                                # noqa: BLE001
            body, code = "<p class='note'>The paper could not be shown just now (%s).</p>" % esc(e.__class__.__name__), 200
        return body, code, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}

    @bp.route(PAGE + "/api/healthz")
    def api_healthz():
        u, err = _doc()
        if err:
            return err
        sp = spine_con()
        ok = sp is not None
        if sp is not None:
            sp.close()
        return jsonify(ok=ok, kit=KIT, version=VERSION, off=bool(is_off()))

    return bp


def init(app, db_getter, require_fn):
    """Mount only (called by sanjeevni_approvals.init, fail-soft). Opens no connection."""
    global _db, _require
    _db, _require = db_getter, require_fn
    bp = _mount()
    app.register_blueprint(bp)
    return bp


if __name__ == "__main__":
    # python3 item_ledger.py <finance.db> NAME [r]  -- the page's figures as text (read only), for the walk and the box
    con = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
    sp = spine_con()
    rows = find(sp, sys.argv[2])
    print(json.dumps(rows[:5], ensure_ascii=False))
    if rows:
        k = rows[0]["key"]
        L = ledger(con, sp, k, (today() - dt.timedelta(days=LAST_DAYS - 1)).isoformat(), today().isoformat())
        print(json.dumps(dict(totals=L["totals"], days=len(L["days"])), default=str))
