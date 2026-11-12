#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""marg_billwatch.py -- kit S803_MARG_WATCH_BILLS (12-Nov-2026, Sanjeevni session 438): the Marg watch, Kit 1 -- section B,
"Changed after the day". Plan S434_MARG_WATCH_PLAN_v3 section 0A row 1, section 6, with the owner's rulings D923-D928, D935, D936.

WHAT IT DOES. The same bill, seen in two Marg reports of the same period taken on different days: removed, added late, re-dated, or
its lines changed. It READS the server's own name-free line tables only -- purchase_line (every item-wise purchase export, superseded
or not) and mi_sale_line (every certified sale export) -- never a raw Marg file, never a patient's name.
The five noise rules (plan 6.4): 1 a part export is set aside whole (and a filtered first print is no baseline for "added late") ·
2 "added late" needs the bill dated 3+ days before the earlier export was taken · 3 paise -- under one rupee -- are for the record ·
4 a renamed item is for the record unless both names still hold stock · 5 letter case and spaces in a bill number never make two bills.
A bill is one supplier's number within one financial year (a number used again next April is another bill).  Found here on the live tables (not in the plan): Marg's own purchase rate is
re-set on old bills and moves Marg's "amount" column while the bill's money (the net amount) stays -- kind 'value', for the record.
D935: a purchase bill agrees with its scanned paper TO THE RUPEE or it stays open; nothing about a bill's money is "small".
D926: a changed purchase bill that now agrees with its paper is "Settled by the scanned bill" -- by the Purchase bills page's own
judgement (scan_register.agree / verified and provisional_s781.differences), read, never copied; and only when the paper can tell
the old entry from the new (the money or the date moved).
D936 / D927: View opens, IN THE ROW, the Purchase bills page's own panel -- the scan, the paper's lines beside Marg's, its verdict and
its own taps -- under one strip: what the bill was. No second viewer is built: the panel is made by provisional_s781's functions.
D923 / D924: he closes a row himself, on the row, with a reason; a removed sale bill carries its two choices.

THE PAGE: /finance/sanjeevni/marg-watch -- the doctor only (checker).  Section A (stock moved with no record) is Kit 2.

READ ONLY on everything that exists. It writes ONLY its own two tables -- billwatch_seen (when a finding was first found, whether that
was before the page began, and whether it is to be told) and billwatch_act (his closes, re-opens and Not-OK marks) -- its setting rows
(billchange.*) and audit lines. The taps inside an opened panel are the Purchase bills page's own (its /api/s781/mark), unchanged.
THE PHONE NOTICE IS OFF UNTIL HE TURNS IT ON, on the page (billchange.on; owner_notice's own switches stop it too). Turned on, it tells
only a finding found AFTER that moment, once, and one bill at most once a week. The page itself only reads.

    /root/wa/venv/bin/python3 -B marg_billwatch.py <finance.db> --fill      (the install's history fill: everything found so far is
                                                                             'Before this page' and is never announced)
    /root/wa/venv/bin/python3 -B marg_billwatch.py <finance.db> --show      (counts only; writes nothing)
"""
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import sys

KIT = "S803_MARG_WATCH_BILLS"
VERSION = "1"
PAGE = "/finance/sanjeevni/marg-watch"
PURCHASE_PREFIX = "/finance/purchase"                         # the Purchase bills page's own address: its scan route and its taps
HERE = os.path.dirname(os.path.abspath(__file__))
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
DDL = (
    "CREATE TABLE IF NOT EXISTS billwatch_seen (fkey TEXT PRIMARY KEY, side TEXT NOT NULL, kind TEXT NOT NULL, sup TEXT, bill_no TEXT, "
    "bill_date TEXT, found_at TEXT NOT NULL, before INTEGER NOT NULL DEFAULT 0, counted INTEGER NOT NULL DEFAULT 1, words TEXT, tell INTEGER, line TEXT, judged_at TEXT)",
    "CREATE TABLE IF NOT EXISTS billwatch_act (id INTEGER PRIMARY KEY AUTOINCREMENT, fkey TEXT NOT NULL, action TEXT NOT NULL, "
    "decision TEXT, reason TEXT, by_user TEXT, at TEXT NOT NULL)",
    "CREATE INDEX IF NOT EXISTS billwatch_act_fkey ON billwatch_act (fkey, id)",
)
DECISIONS = {"stands": "The sale stands", "cancelled": "The sale was cancelled", "ok": "OK", "notok": "Not OK", "lot": "OK — with the lot"}

_db = _require = None


# ====================================================================== the engine (reads only; name-free tables)
PART_SHARE = 0.90        # noise rule 1: an export holding under 90% of the previous export's bills for the shared dates ...
PART_MIN_GONE = 3        # ... and at least three bills short of it, is a part print: set aside whole (one or two bills gone are findings)
PART_FWD_SHARE = 1.0 / 3  # rule 1 looking forward: a list that held under a THIRD of the bills it should have is no baseline for "added late"
LATE_DAYS = 3            # noise rule 2: "added late" only when the bill is dated 3 or more days before the earlier export was taken
PAISE_ABS = 100          # noise rule 3: the amount differs by less than one rupee (D935: a rupee is never "for the record")
RECORD_KINDS = ("paise", "rename", "value")                   # line changes that are for the record: never counted, never told


def _d(s):
    try:
        return dt.date.fromisoformat(str(s or "")[:10])
    except ValueError:
        return None


def _taken(stamp):
    """Marg's export stamp YYYYMMDD-HHMMSS -> datetime (IST, naive); None when malformed."""
    try:
        return dt.datetime.strptime(str(stamp or "")[:15], "%Y%m%d-%H%M%S")
    except ValueError:
        return None


def _fy(d):
    """The financial year a bill's date falls in (April to March), as its starting year; '' when undated."""
    x = _d(d)
    return "" if x is None else str(x.year if x.month >= 4 else x.year - 1)


def billno_norm(s):
    """Noise rule 5: letter case and spaces in a bill number never make two bills."""
    return re.sub(r"\s+", "", str(s or "").upper())


def _num(v):
    try:
        return float(v) if v is not None and str(v).strip() != "" else 0.0
    except (TypeError, ValueError):
        return 0.0


def _g(v):
    return ("%g" % v) if v is not None else ""


def _table(con, name):
    return bool(con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone())


def purchase_exports(con):
    """Every item-wise purchase export the server holds, superseded or not, oldest first: [dict(md5, type, f, t, stamp, taken, bills)].
    bills: {(supplier_norm, bill no. normalised, financial year): dict(sup, no, date, lines)}; a line: dict(item, pack, qty, free, rate_p,
    amt_p, val_p, disc, tax). The date is not part of a bill's identity (a re-dated bill is one finding) -- its financial year is.
    amt_p is the line's NET amount -- what the bill charges (after discount, with tax): the money the vendor's total is made of (D935).
    val_p is Marg's own "amount" column, (quantity + free) x Marg's purchase rate: the value Marg puts on the stock. It moves when the
    purchase rate is re-set in Marg and the bill's money does not -- such a change is kind 'value', for the record, never a bill change."""
    by = {}
    for r in con.execute("SELECT source_md5, supplier_norm, bill_no, bill_date, item, packing, qty, free, rate_p, amount_p, net_amount_p, discount_pct, tax "
                         "FROM purchase_line WHERE COALESCE(direction,'PURCHASE')='PURCHASE' ORDER BY id"):
        if not str(r[2] or "").strip() or not str(r[1] or "").strip():
            continue                                           # a line that could not be put on a bill is not judged
        key = (str(r[1]).strip().upper(), billno_norm(r[2]), _fy(r[3]))
        b = by.setdefault(r[0], {}).setdefault(key, dict(sup=str(r[1]).strip().upper(), no=str(r[2]).strip(), date=str(r[3] or "")[:10], lines=[]))
        amt = r[10] if r[10] is not None else r[9]
        b["lines"].append(dict(item=re.sub(r"\s+", " ", str(r[4] or "")).strip().upper(), pack=str(r[5] or "").strip(), qty=_num(r[6]), free=_num(r[7]),
                               rate_p=int(r[8] or 0), amt_p=int(amt or 0), val_p=int(r[9] or 0), disc=_num(r[11]), tax=_num(r[12])))
    out = []
    for r in con.execute("SELECT md5, type, period_from, period_to, export_stamp, n_rows FROM purchase_export WHERE type IN ('ITEMWISE','BILLITEMWISE') "
                         "ORDER BY export_stamp, n_rows, md5"):
        tk = _taken(r[4])
        f, t = _d(r[2]), _d(r[3])
        if tk is None or f is None or t is None or r[0] not in by:
            continue
        out.append(dict(md5=r[0], type=r[1], f=f, t=t, stamp=r[4], taken=tk, bills=by[r[0]]))
    return out


def sale_exports(con):
    """Every certified sale export (bill-wise, with items) the server holds, oldest first; the same shape. A sale bill's identity is its
    number and its day. A line: dict(item, pack, qty, free, rate_p, amt_p) with qty = Marg's quantity text."""
    if not (_table(con, "mi_sale_line") and _table(con, "mi_file")):
        return []
    files = {}
    for r in con.execute("SELECT md5, date_from, date_to, stamp FROM mi_file WHERE type='SALE_BILLWISE' AND verdict='VERIFIED'"):
        tk, f, t = _taken(r[3]), _d(r[1]), _d(r[2])
        if tk and f and t:
            files[r[0]] = dict(md5=r[0], type="SALE", f=f, t=t, stamp=r[3], taken=tk, bills={})
    for r in con.execute("SELECT md5, bill_date, bill_no, is_return, item_name, pack, qty_raw, amount_p FROM mi_sale_line ORDER BY rowid"):
        e = files.get(r[0])
        if e is None or not str(r[2] or "").strip():
            continue
        key = ("SALE", billno_norm(r[2]) + "|" + str(r[1] or "")[:10])
        b = e["bills"].setdefault(key, dict(sup="SALE", no=str(r[2]).strip(), date=str(r[1] or "")[:10], ret=int(r[3] or 0), lines=[]))
        b["lines"].append(dict(item=re.sub(r"\s+", " ", str(r[4] or "")).strip().upper(), pack=str(r[5] or "").strip(), qty=str(r[6] or "").strip(),
                               free=0.0, rate_p=0, amt_p=int(r[7] or 0), val_p=0, disc=0.0, tax=0.0))
    return sorted((e for e in files.values() if e["bills"]), key=lambda e: (e["stamp"], e["md5"]))


def _lkey(l):
    return (l["item"], l["qty"], l["free"], l["rate_p"], l["amt_p"])


def _paise(a_amt, b_amt):
    return abs(int(b_amt) - int(a_amt)) < PAISE_ABS


def _qf(lines):
    """(quantity, free) summed; a sale line's quantity is text, so the texts joined in order."""
    if lines and isinstance(lines[0]["qty"], str):
        return " + ".join(l["qty"] for l in lines), 0.0
    return sum(l["qty"] for l in lines), sum(l["free"] for l in lines)


def diff_lines(was, now, stock_names=None):
    """The line changes between two readings of one bill: [dict(kind, item, was, now, d_amt_p, d_qty)].
    kind: paise (rule 3) | value (Marg's purchase rate only) | amount | qty | rename (rule 4) | item | added | removed.  stock_names: the item names Marg holds stock of now."""
    A, B = list(was), list(now)
    same = []                                                  # unchanged in the bill's money; Marg's own valuation of the line moved
    for l in list(A):                                          # 1 the lines that did not change
        k = _lkey(l)
        m = next((x for x in B if _lkey(x) == k), None)
        if m is not None:
            A.remove(l)
            B.remove(m)
            if abs(int(m.get("val_p") or 0) - int(l.get("val_p") or 0)) >= max(PAISE_ABS, 1):
                same.append((l, m))
    out = [dict(kind="value", item=a["item"], was=[a], now=[b], d_amt_p=0, d_qty=0) for a, b in same]
    for item in sorted({l["item"] for l in A} & {l["item"] for l in B}):      # 2 the same item on both sides
        a = [l for l in A if l["item"] == item]
        b = [l for l in B if l["item"] == item]
        A = [l for l in A if l["item"] != item]
        B = [l for l in B if l["item"] != item]
        (qa, fa), (qb, fb) = _qf(a), _qf(b)
        d_amt = sum(l["amt_p"] for l in b) - sum(l["amt_p"] for l in a)
        if qa != qb or fa != fb:
            kind = "qty"
        elif len(a) == len(b) == 1 and a[0]["rate_p"] == b[0]["rate_p"] and _paise(a[0]["amt_p"], b[0]["amt_p"]):
            kind = "paise"
        elif abs(d_amt) < PAISE_ABS:
            kind = "paise"
        else:
            kind = "amount"
        d_qty = None if isinstance(qa, str) else (qb + fb) - (qa + fa)
        out.append(dict(kind=kind, item=item, was=a, now=b, d_amt_p=d_amt, d_qty=d_qty))
    for a in list(A):                                          # 3 rule 4: a line gone and a line come with the same quantity, free, rate and amount
        m = next((x for x in B if (x["qty"], x["free"], x["rate_p"], x["amt_p"]) == (a["qty"], a["free"], a["rate_p"], a["amt_p"])), None)
        if m is None:
            continue
        A.remove(a)
        B.remove(m)
        both = stock_names is not None and a["item"] in stock_names and m["item"] in stock_names
        out.append(dict(kind="item" if both else "rename", item=m["item"], was=[a], now=[m], d_amt_p=0, d_qty=0 if both else None))
    for a in A:                                                # 4 what is left
        out.append(dict(kind="removed", item=a["item"], was=[a], now=[], d_amt_p=-a["amt_p"], d_qty=None if isinstance(a["qty"], str) else -(a["qty"] + a["free"])))
    for b in B:
        out.append(dict(kind="added", item=b["item"], was=[], now=[b], d_amt_p=b["amt_p"], d_qty=None if isinstance(b["qty"], str) else (b["qty"] + b["free"])))
    return out


def _is_part(x, prev):
    """Noise rule 1. (part?, bills of x on the shared dates, bills of prev on them)."""
    f, t = max(x["f"], prev["f"]), min(x["t"], prev["t"])
    if f > t:
        return False, 0, 0
    def n(e):
        return sum(1 for b in e["bills"].values() if (_d(b["date"]) and f <= _d(b["date"]) <= t))
    nx, np_ = n(x), n(prev)
    return (np_ > 0 and nx < PART_SHARE * np_ and (np_ - nx) >= PART_MIN_GONE), nx, np_


def compare(exports, side, stock_names=None, part_rule=True, record_kinds=RECORD_KINDS):
    """Walk the exports of one kind, oldest first, and say what changed in a bill between two of them.
    -> (findings, parts). A finding: dict(side, sup, no, date, kind, was_md5, now_md5, was_stamp, now_stamp, was, now, changes, rupee_p,
    redated, record) -- kind: gone | late | changed | redated; record=True when every line change is of record_kinds (paise, a rename,
    Marg's own purchase rate -- and, for a sale bill, its money: D917) and the date did not move: listed for the record, never counted.
    parts: the exports rule 1 names: [dict(md5, stamp, f, t, n, of[, fwd])] -- a part print set aside whole; with fwd=True a filtered
    print that is only refused as a baseline for "added late" (it is still read for removed and changed bills)."""
    findings, parts = [], []
    last = {}                                                  # (type, key) -> dict(bill, e) : the newest reading of the bill
    gone = {}                                                  # (type, key) -> the 'gone' finding, should the bill come back
    done = []                                                  # the exports walked (not parts), in order
    for x in exports:
        prev = next((p for p in reversed(done) if p["type"] == x["type"] and max(p["f"], x["f"]) <= min(p["t"], x["t"])), None)
        if part_rule and prev is not None:
            part, nx, np_ = _is_part(x, prev)
            if part:
                parts.append(dict(md5=x["md5"], stamp=x["stamp"], f=x["f"], t=x["t"], n=nx, of=np_))
                continue
        late_c = {}                                            # baseline md5 -> the 'added late' findings this export makes against it
        for key, b in x["bills"].items():
            bd = _d(b["date"])
            tk = (x["type"], key)
            old = last.get(tk)
            if old is not None and tk in gone:                 # it was gone, and is back
                g = gone.pop(tk)
                ch = diff_lines(old["bill"]["lines"], b["lines"], stock_names)
                red = old["bill"]["date"] != b["date"]
                if not ch and not red:
                    findings[:] = [z for z in findings if z is not g]      # gone in one report, back unchanged in the next: no finding
                else:
                    g.update(kind="redated" if (red and not ch) else "changed", now=b, date=b["date"], now_md5=x["md5"], now_stamp=x["stamp"], changes=ch,
                             rupee_p=sum(c["d_amt_p"] for c in ch), redated=red, record=(not red) and all(c["kind"] in record_kinds for c in ch))
            elif old is not None:
                ch = diff_lines(old["bill"]["lines"], b["lines"], stock_names)
                red = old["bill"]["date"] != b["date"]
                if ch or red:
                    findings.append(dict(side=side, sup=b["sup"], no=b["no"], date=b["date"], kind="redated" if (red and not ch) else "changed",
                                         was_md5=old["e"]["md5"], now_md5=x["md5"], was_stamp=old["e"]["stamp"], now_stamp=x["stamp"],
                                         was=old["bill"], now=b, changes=ch, rupee_p=sum(c["d_amt_p"] for c in ch), redated=red,
                                         record=(not red) and all(c["kind"] in record_kinds for c in ch)))
            else:                                              # never seen: was there an earlier report that should have held it?
                e0 = None
                if bd is not None:
                    for p in reversed(done):
                        if p["type"] != x["type"] or not (p["f"] <= bd <= p["t"]):
                            continue
                        if side == "purchase" and (p["taken"].date() - bd).days < LATE_DAYS:
                            continue                           # rule 2: keyed after that export was taken
                        if side == "sale" and p["taken"].date() <= bd:
                            continue                           # the day's own report, taken before the day ended
                        e0 = p
                        break
                if e0 is not None:
                    lf = dict(side=side, sup=b["sup"], no=b["no"], date=b["date"], kind="late", was_md5=e0["md5"], now_md5=x["md5"],
                              was_stamp=e0["stamp"], now_stamp=x["stamp"], was=None, now=b, changes=[],
                              rupee_p=sum(l["amt_p"] for l in b["lines"]), redated=False, record=False)
                    findings.append(lf)
                    late_c.setdefault(e0["md5"], (e0, []))[1].append(lf)
            last[tk] = dict(bill=b, e=x)
        if part_rule and side == "purchase":                   # rule 1, looking forward: a filtered first print is no baseline
            for p, lfs in late_c.values():
                elig = sum(1 for b in x["bills"].values() if _d(b["date"]) and p["f"] <= _d(b["date"]) <= p["t"] and (p["taken"].date() - _d(b["date"])).days >= LATE_DAYS)
                held = elig - len(lfs)
                if len(lfs) >= PART_MIN_GONE and held < PART_FWD_SHARE * elig:
                    drop = {id(z) for z in lfs}
                    findings[:] = [z for z in findings if id(z) not in drop]
                    parts.append(dict(md5=p["md5"], stamp=p["stamp"], f=p["f"], t=p["t"], n=held, of=elig, fwd=True))
        for (tp, key), old in list(last.items()):              # a bill the report should hold, and does not
            if tp != x["type"] or key in x["bills"] or (tp, key) in gone:
                continue
            bd = _d(old["bill"]["date"])
            if bd is None or not (x["f"] <= bd <= x["t"]) or old["e"] is x:
                continue
            g = dict(side=side, sup=old["bill"]["sup"], no=old["bill"]["no"], date=old["bill"]["date"], kind="gone", was_md5=old["e"]["md5"],
                     now_md5=x["md5"], was_stamp=old["e"]["stamp"], now_stamp=x["stamp"], was=old["bill"], now=None, changes=[],
                     rupee_p=-sum(l["amt_p"] for l in old["bill"]["lines"]), redated=False, record=False)
            findings.append(g)
            gone[(tp, key)] = g
        done.append(x)
    return findings, parts


# ====================================================================== the store, the settings, the neighbours
def now_ist():
    return dt.datetime.now(IST).replace(tzinfo=None, microsecond=0)


def now_iso():
    return now_ist().isoformat(sep=" ")


def ensure(con):
    for q in DDL:
        con.execute(q)


def setting(con, key, default=""):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return str(r[0]) if r and r[0] is not None else default
    except sqlite3.Error:
        return default


def is_on(con):
    """The phone notice: OFF until he turns it on, on the page."""
    return setting(con, "billchange.on", "off").strip().lower() == "on"


def _shared_path():
    shared = os.environ.get("SHARED_LIB_DIR") or os.path.join(os.path.dirname(HERE), "shared")
    if os.path.isdir(shared) and shared not in sys.path:
        sys.path.append(shared)                                # cron runs from /root/finance with no SHARED_LIB_DIR (as owner_notice does)
    if HERE not in sys.path:
        sys.path.insert(0, HERE)


def SR():
    _shared_path()
    import scan_register                                      # noqa: PLC0415 -- the Purchase bills page's register; called, never changed
    return scan_register


def PV():
    _shared_path()
    import provisional_s781                                   # noqa: PLC0415 -- the Purchase bills page's comparison panel; called, never changed
    return provisional_s781


def esc(s):
    return (str("" if s is None else s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;"))


def rs(p, sign=False):
    """Paise -> rupees in his reading: Indian grouping, the paise shown only when there are any; sign: +/- in front."""
    p = int(p or 0)
    a = abs(p)
    whole, pa = divmod(a, 100)
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    out = "₹" + s + ((".%02d" % pa) if pa else "")
    if sign:
        return ("−" if p < 0 else "+") + out if p else out
    return ("−" + out) if p < 0 else out


def dmon(iso, year=False):
    d = _d(iso)
    if not d:
        return str(iso or "")
    return "%d-%s%s" % (d.day, d.strftime("%b"), ("-%d" % d.year) if (year or d.year != now_ist().year) else "")


def stamp_day(stamp):
    t = _taken(stamp)
    return dmon(t.date().isoformat()) if t else str(stamp or "")


def month_name(ym):
    try:
        return dt.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%B %Y")
    except (ValueError, TypeError):
        return str(ym or "undated")


def stock_names(con):
    """The item names Marg holds stock of in its newest closing report (noise rule 4); None when no closing is on the server."""
    try:
        r = con.execute("SELECT MAX(as_on) FROM stock_snapshot").fetchone()
        if not r or not r[0]:
            return None
        return {re.sub(r"\s+", " ", str(x[0] or "")).strip().upper() for x in con.execute("SELECT item FROM stock_snapshot WHERE as_on=? AND qty>0", (r[0],))}
    except sqlite3.Error:
        return None


def fkey(f):
    """A finding's own key: the bill, what happened to it, and the report that first showed it. The same finding keeps its key for ever."""
    raw = "|".join([f["side"], f["sup"], billno_norm(f["no"]), f["date"] if f["side"] == "sale" else _fy(f["date"]),
                    "late" if f["kind"] == "late" else "gone" if f["kind"] == "gone" else "changed", str(f.get("now_md5") or "")])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


# ====================================================================== words for a finding
def _sale_qty(q):
    """Marg's sale quantity text 'packs:loose' -> his words."""
    m = re.match(r"^\s*(\d+)\s*:\s*(\d+)\s*$", str(q or ""))
    if not m:
        try:
            return _g(float(str(q or "").strip()))
        except ValueError:
            return str(q or "")
    a, b = int(m.group(1)), int(m.group(2))
    return " + ".join(x for x in (("%d" % a) if a else "", ("%d loose" % b) if b else "") if x) or "0"


def qf(l):
    if isinstance(l["qty"], str):
        return _sale_qty(l["qty"])
    return _g(l["qty"]) + ((" + %s free" % _g(l["free"])) if l["free"] else "")


def qfs(lines):
    return " and ".join(qf(l) for l in lines)


def change_words(c):
    """One line change in his words (plain text; escaped where it is shown)."""
    k, a, b = c["kind"], c["was"], c["now"]
    if k == "qty" or (k == "amount" and len(a) != len(b)):
        if len(a) == 1 and len(b) > 1:
            return "%s — %s split into %s" % (c["item"], qfs(a), qfs(b))
        return "%s — quantity %s → %s" % (c["item"], qfs(a), qfs(b))
    if k == "amount" and a and isinstance(a[0]["qty"], str):   # a sale line carries Marg's rate per pack, not an amount
        return "%s — rate per pack %s → %s, the same quantity" % (c["item"], rs(sum(l["amt_p"] for l in a)), rs(sum(l["amt_p"] for l in b)))
    if k == "amount":
        bits = []
        if len(a) == len(b) == 1:                              # say WHAT moved the money: the rate, the GST or the discount
            if a[0]["rate_p"] != b[0]["rate_p"]:
                bits.append("rate %s → %s" % (rs(a[0]["rate_p"]), rs(b[0]["rate_p"])))
            if a[0].get("tax", 0) != b[0].get("tax", 0):
                bits.append("GST %s%% → %s%%" % (_g(a[0].get("tax", 0)), _g(b[0].get("tax", 0))))
            if a[0].get("disc", 0) != b[0].get("disc", 0):
                bits.append("discount %s%% → %s%%" % (_g(a[0].get("disc", 0)), _g(b[0].get("disc", 0))))
        return "%s — %samount %s → %s, the same quantity" % (c["item"], (", ".join(bits) + "; ") if bits else "", rs(sum(l["amt_p"] for l in a)),
                                                             rs(sum(l["amt_p"] for l in b)))
    if k == "item":
        return "Item changed on the bill — %s → %s (%s)" % (a[0]["item"], b[0]["item"], qf(b[0]))
    if k == "rename":
        return "renamed in Marg — %s → %s" % (a[0]["item"], b[0]["item"])
    if k == "added":
        return "Line added — %s, %s" % (c["item"], qf(b[0]))
    if k == "removed":
        return "Line removed — %s, %s" % (c["item"], qf(a[0]))
    if k == "value":
        return "%s — Marg's own value of the line %s → %s; the bill's money is unchanged" % (c["item"], rs(a[0].get("val_p")), rs(b[0].get("val_p")))
    return "%s — differs by paise" % c["item"]


def what_words(f):
    side_sale = f["side"] == "sale"
    if f["kind"] == "gone":
        return "Bill removed from Marg"
    if f["kind"] == "late":
        return "Sale bill added after the day's report" if side_sale else "Bill added late"
    parts = []
    if f.get("redated") and f.get("was"):
        parts.append("Bill date changed — %s → %s" % (dmon(f["was"]["date"]), dmon(f["now"]["date"])))
    rk = RECORD_KINDS + (("amount",) if side_sale else ())
    ch = sorted(f["changes"], key=lambda c: c["kind"] in rk)      # the changes that count come first
    parts += [change_words(c) for c in ch[:3]]
    if len(ch) > 3:
        parts.append("and %d more line%s" % (len(ch) - 3, "" if len(ch) - 3 == 1 else "s"))
    return "; ".join(parts) or "changed"


def effect_words(f):
    """What the change means for the quantity on the bill (packs as Marg bills them). Marg's own stock moves are section A's (Kit 2)."""
    if f["side"] == "sale":
        n = len((f["was"] or f["now"])["lines"])
        if f["kind"] == "gone":
            return "%d item%s back in Marg's stock" % (n, "" if n == 1 else "s")
        if f["kind"] == "late":
            return "%d item%s sold on a bill made after the report" % (n, "" if n == 1 else "s")
        return "the bill's items or quantities changed"
    if f["kind"] == "late":
        return "the bill's goods entered Marg's stock late"
    if f["kind"] == "gone":
        return "the bill's goods left Marg's stock"
    mv = []
    for c in f["changes"]:
        if c["kind"] == "item":
            n = c["now"][0]["qty"] + c["now"][0]["free"]
            mv.append("%s −%s, %s +%s" % (c["was"][0]["item"], _g(n), c["now"][0]["item"], _g(n)))
        elif c["kind"] in ("qty", "added", "removed") and c.get("d_qty"):
            mv.append("%s %s%s" % (c["item"], "+" if c["d_qty"] > 0 else "−", _g(abs(c["d_qty"]))))
    return ("Quantity on the bill (free goods included): " + "; ".join(mv[:4]) + (" …" if len(mv) > 4 else "")) if mv else ""


def seen_words(f):
    a, b = stamp_day(f["was_stamp"]), stamp_day(f["now_stamp"])
    if f["kind"] == "gone":
        return "In the report taken %s · gone in the one taken %s" % (a, b)
    if f["kind"] == "late":
        return "Not in the report taken %s · in the one taken %s" % (a, b)
    return "As before in the report taken %s · changed in the one taken %s" % (a, b)


def notice_line(f):
    """The one line told to him for a new finding that counts (plan 6.5)."""
    who = "Sale bill %s" % f["no"] if f["side"] == "sale" else "%s bill %s" % (" ".join(f["sup"].split()).title(), f["no"])
    amt = f.get("bill_p") if f.get("bill_p") is not None else abs(int(f.get("rupee_p") or 0))
    if f["kind"] == "gone":
        return "%s (%s, %s) is gone from Marg; %s." % (who, dmon(f["date"]), rs(abs(amt)), effect_words(f))
    if f["kind"] == "late":
        return "%s (%s, %s) was added after its day's report." % (who, dmon(f["date"]), rs(abs(amt)))
    return "%s (%s): %s." % (who, dmon(f["date"]), what_words(f))


# ====================================================================== the paper: the Purchase bills page's own judgement, read
class Paper(object):
    """One read of what the Purchase bills page knows, for one request: the scans, the pairs, its context; its differences by month."""

    def __init__(self, con):
        self.con, self.ok, self.why = con, False, ""
        self.scans, self.links, self.cx, self._diff = {}, {}, None, {}
        try:
            S = SR()
            sc = S.asset_scans(con)
            if sc is None:
                self.why = "the scanned bills could not be read just now"
                return
            self.scans, self.links, self.cx, self.ok = sc, S.links(con), S.Ctx(con), True
        except Exception as e:                                # noqa: BLE001 -- the page never falls with the paper side
            self.why = "the scanned bills could not be read just now (%s)" % e.__class__.__name__

    def bill(self, f):
        """The bill as the server holds it now (purchase_bill, effective), or None."""
        try:
            pa = SR()._pa()
            rows = [dict(r) for r in self.con.execute("SELECT b.* FROM purchase_bill b WHERE b.supplier_norm=? AND " + pa.EFF_BILL, (f["sup"],))]
        except Exception:                                     # noqa: BLE001
            return None
        rows = [b for b in rows if billno_norm(b["bill_no"]) == billno_norm(f["no"])]
        if not rows:
            return None
        want = (f.get("now") or f.get("was") or {}).get("date")
        same = [b for b in rows if str(b.get("bill_date") or "")[:10] == want]
        return (same or sorted(rows, key=lambda b: b["id"]))[-1]

    def differs(self, b):
        """provisional_s781's own row for this bill when Marg differs from its scan (and is not cleared by him), else None."""
        month = str(b.get("month") or str(b.get("bill_date") or "")[:7])
        if month not in self._diff:
            try:
                self._diff[month] = {int(x["bill"]["id"]): x for x in PV().differences(self.con, month, self.scans)}
            except Exception:                                 # noqa: BLE001
                self._diff[month] = None
        d = self._diff[month]
        if d is None:
            return "unread"
        x = d.get(int(b["id"]))
        return x if (x is not None and not x.get("cleared")) else None

    def state(self, f):
        """dict(state, bill, sid, paper_p, marg_p, words). state: settled | differs | agrees | no_paper | no_bill | unread.
        settled = that page's verdict agrees, to the rupee (D935), AND the paper can tell the old entry from the new (D926)."""
        if f["side"] != "purchase":
            return dict(state="sale", bill=None, sid=None, words="A sale bill has no paper.")
        if not self.ok:
            return dict(state="unread", bill=None, sid=None, words="Not judged against the paper: %s." % self.why)
        b = self.bill(f)
        if b is None:
            return dict(state="no_bill", bill=None, sid=None, words=("The bill is no longer in Marg, so there is no paper to check it against." if f["kind"] == "gone" else
                                                                     "The server's current list of bills does not hold this bill yet, so its paper cannot be shown here."))
        lk = self.links.get(int(b["id"]))
        if not lk or int(lk["scan"]) not in self.scans:
            return dict(state="no_paper", bill=b, sid=None, marg_p=int(b["amount_p"] or 0), words="No scanned bill on file.")
        S = SR()
        s = self.scans[int(lk["scan"])]
        out = dict(bill=b, sid=int(lk["scan"]), stamp=s.get("stamp_no") or "#%d" % int(lk["scan"]), marg_p=int(b["amount_p"] or 0))
        try:
            a = S.agree(self.cx, s, b)
            sp = a.get("scan_p")
            out["paper_p"] = sp
            rupee = sp not in (None, 0) and abs(abs(int(sp)) - abs(int(b["amount_p"] or 0))) < 100       # D935: to the rupee, in every month
            ver = bool(S.verified(a)) and rupee
            dx = self.differs(b)
        except Exception as e:                                # noqa: BLE001
            out.update(state="unread", words="Not judged against the paper (%s)." % e.__class__.__name__)
            return out
        if dx == "unread":
            out.update(state="unread", words="Not judged against the paper: its lines could not be compared just now.")
            return out
        if dx is not None or not ver:
            why = ""
            try:
                why = PV().chip(dx) if dx is not None else ("the paper's total is not read" if sp in (None, 0) else
                                                           "Marg differs by %s" % rs(abs(abs(int(sp)) - abs(int(b["amount_p"] or 0)))) if not rupee
                                                           else "the bill number or the supplier does not agree with the scan")
            except Exception:                                 # noqa: BLE001
                why = "Marg differs"
            out.update(state="differs", words="Marg differs from the paper — %s." % why, dx=dx)
            return out
        tells = (f["kind"] == "late" or abs(int(f.get("rupee_p") or 0)) >= 100
                 or (f.get("redated") and a.get("date") == "agree"))
        out.update(state="settled" if tells else "agrees",
                   words=("Paper matches ✓ — paper %s, Marg %s." % (rs(abs(int(sp))), rs(abs(int(b["amount_p"] or 0))))) if tells else
                   ("The paper's total agrees (%s) — but the money did not change, so the total cannot say which entry is right. "
                    "The name and quantity printed on the paper decide." % rs(abs(int(sp)))))
        return out


# ====================================================================== the findings, whole
def _bill_total(con, f):
    """A sale bill's own total and how it was paid, from the day's first reading (sale_bill keeps it: plan R9)."""
    try:
        r = con.execute("SELECT net_p, cash_p, noncash_p FROM sale_bill WHERE bill_no=? AND business_date=?", (f["no"], f["date"])).fetchone()
    except sqlite3.Error:
        r = None
    if not r:
        return None, ""
    net, cash, non = int(r[0] or 0), int(r[1] or 0), int(r[2] or 0)
    return net, ("cash" if cash and not non else "UPI or credit" if non and not cash else "cash and UPI" if cash and non else "")


def acts(con):
    """{fkey: the last act dict(action, decision, reason, by_user, at)}."""
    out = {}
    try:
        for r in con.execute("SELECT fkey, action, decision, reason, by_user, at FROM billwatch_act ORDER BY id"):
            out[r[0]] = dict(action=r[1], decision=r[2], reason=r[3] or "", by=r[4] or "", at=r[5])
    except sqlite3.Error:
        pass
    return out


def seen(con):
    out = {}
    try:
        for r in con.execute("SELECT fkey, found_at, before FROM billwatch_seen"):
            out[r[0]] = dict(found_at=r[1], before=int(r[2] or 0))
    except sqlite3.Error:
        pass
    return out


def build(con, paper=True):
    """Everything the page shows: dict(findings, record, parts, paper_ok, paper_why, since). Reads only.
    A finding gains: fkey, month, what, effect, seen, bill_p, pay, paper (Paper.state), status, act, found_at, before."""
    names = stock_names(con)
    pur, parts = compare(purchase_exports(con), "purchase", names)
    sal, _p = compare(sale_exports(con), "sale", None, part_rule=False, record_kinds=RECORD_KINDS + ("amount",))
    P = Paper(con) if paper else None
    A, SN = acts(con), seen(con)
    since = setting(con, "billchange.since", "")
    out, record = [], []
    for f in pur + sal:
        f["fkey"] = fkey(f)
        f["month"] = str((f.get("now") or f.get("was") or {}).get("date") or f["date"])[:7]
        f["what"], f["effect"], f["seen"] = what_words(f), effect_words(f), seen_words(f)
        f["bill_p"], f["pay"] = (None, "")
        if f["side"] == "sale":                               # a sale line carries Marg's RATE per pack: its money is rate x quantity
            f["bill_p"], f["pay"] = _bill_total(con, f)
            was_p = sum(_sale_amount_p(l) for l in f["was"]["lines"]) if f.get("was") else 0
            now_p = sum(_sale_amount_p(l) for l in f["now"]["lines"]) if f.get("now") else 0
            if f["kind"] == "gone":
                f["rupee_p"] = -(f["bill_p"] if f["bill_p"] is not None else was_p)
            elif f["kind"] == "late":
                f["rupee_p"] = f["bill_p"] if f["bill_p"] is not None else now_p
            else:
                f["rupee_p"] = now_p - was_p
        sn = SN.get(f["fkey"])
        f["found_at"], f["before"] = (sn["found_at"], sn["before"]) if sn else ("", 0 if _after_began(f, since) else 1)
        f["act"] = A.get(f["fkey"])
        if f["record"]:
            f["paper"], f["status"] = None, "record"
            record.append(f)
            continue
        f["paper"] = P.state(f) if P is not None else dict(state="unread", bill=None, sid=None, words="")
        act = f["act"] or {}
        if act.get("action") == "close":
            f["status"] = "closed"
        elif act.get("action") in ("reopen", "notok"):
            f["status"] = "open"
        elif f["paper"]["state"] == "settled":
            f["status"] = "settled"
        else:
            f["status"] = "open"
        out.append(f)
    key = lambda f: (f["month"], f["date"], f["sup"], f["no"])     # noqa: E731
    out.sort(key=key, reverse=True)
    record.sort(key=key, reverse=True)
    return dict(findings=out, record=record, parts=parts, paper_ok=bool(P and P.ok), paper_why=(P.why if P else ""), since=since)


def _after_began(f, since):
    """Is this finding of the page's own time? Only when the report that first showed it was TAKEN after the page began: a report of an
    older day that arrives late brings history, and history is never new (and never told)."""
    if not since:
        return False
    t = _taken(f.get("now_stamp"))
    try:
        return t is not None and t >= dt.datetime.fromisoformat(since.replace(" ", "T")[:19])
    except ValueError:
        return False


def refresh(con, fill=False):
    """Note every finding not seen before, with the time it was found. fill=True (the install): everything found now is 'Before this
    page' and the page begins now. Until the page has begun (billchange.since) nothing is noted -- and so nothing can be announced.
    -> (new rows, total findings). Writes billwatch_seen and, at the fill, the billchange.* settings; nothing else."""
    ensure(con)
    since = setting(con, "billchange.since", "")
    if not since and not fill:
        return 0, 0
    sig = _signature(con)
    if not fill and sig and sig == setting(con, "billchange.sig", ""):
        return 0, 0                                            # no new report since the last look: nothing can be new
    B = build(con, paper=False)
    have = seen(con)
    ts = now_iso()
    n = 0
    for f in B["findings"] + B["record"]:
        if f["fkey"] in have:
            continue
        con.execute("INSERT OR IGNORE INTO billwatch_seen (fkey, side, kind, sup, bill_no, bill_date, found_at, before, counted, words) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (f["fkey"], f["side"], f["kind"], f["sup"], f["no"], f["date"], ts, 1 if (fill or not _after_began(f, since)) else 0,
                     0 if f["record"] else 1, f["what"][:300]))
        n += 1
    if fill and not since:
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES ('billchange.since', ?, 'S803: the Marg watch began; what was found before this is never announced')", (ts,))
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES ('billchange.on', 'off', 'S803: the phone notice of a changed bill -- off until he turns it on, on the page')")
    con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('billchange.sig', ?, 'S803: the reports the Marg watch last compared')", (sig,))
    con.commit()
    return n, len(B["findings"]) + len(B["record"])


def _signature(con):
    """What the compare reads, in one line: it changes when a purchase or sale report arrives (or is retired)."""
    try:
        a = con.execute("SELECT COUNT(*), COALESCE(MAX(export_stamp),''), COALESCE(SUM(n_rows),0) FROM purchase_export WHERE type IN ('ITEMWISE','BILLITEMWISE')").fetchone()
        b = con.execute("SELECT COUNT(*), COALESCE(MAX(stamp),'') FROM mi_file WHERE type='SALE_BILLWISE' AND verdict='VERIFIED'").fetchone() if _table(con, "mi_file") else (0, "")
        c = con.execute("SELECT COALESCE(MAX(as_on),'') FROM stock_snapshot").fetchone() if _table(con, "stock_snapshot") else ("",)
        return "%s:%s:%s|%s:%s|%s" % (a[0], a[1], a[2], b[0], b[1], c[0])
    except sqlite3.Error:
        return ""


TELL_DAYS = 2            # a finding is told within two days of being found, or not at all
ONCE_DAYS = 7            # one bill is told at most once in seven days (a change re-read from another report is the same news)
UNREAD_WAIT_MIN = 30     # while the scans cannot be read, the judging is tried again only every half hour


def _floor(con, now=None):
    """(the page began, the earliest moment a finding may have been found to be told now, the moment the notice was turned on) -- a
    finding is told only when it was found AFTER the notice was turned on ('9' = never turned on: nothing qualifies)."""
    since = setting(con, "billchange.since", "")
    now = now or now_ist()
    return since, max(since, (now - dt.timedelta(days=TELL_DAYS)).isoformat(sep=" ")), (setting(con, "billchange.tell_from", "") or "9")


def judge(con, now=None):
    """The tick's second step (after refresh): decide ONCE, for each finding noted since the notice was turned on, whether it is to be
    told -- it counts, it is open, he has not touched it, its paper does not settle it, and the same bill was not told in the last seven
    days -- and keep the one line to say. A finding whose paper could not be read just now waits (tried again every half hour). A finding
    judged quiet stays quiet; it shows on the page as NEW all the same.
    -> rows judged. Writes billwatch_seen.tell / .line / .judged_at (and one setting while the scans are unread); builds nothing when
    nothing waits."""
    now = now or now_ist()
    since, floor, on_at = _floor(con, now)
    if not since or not is_on(con) or not _table(con, "billwatch_seen"):
        return 0
    wait = [tuple(r) for r in con.execute("SELECT fkey, side, sup, bill_no FROM billwatch_seen WHERE before=0 AND counted=1 AND tell IS NULL AND found_at>=? "
                                          "AND found_at>?", (floor, on_at))]
    if not wait:
        return 0
    held = setting(con, "billchange.unread_at", "")
    if held and held > (now - dt.timedelta(minutes=UNREAD_WAIT_MIN)).isoformat(sep=" "):
        return 0
    by = {f["fkey"]: f for f in build(con, paper=True)["findings"]}
    week = (now - dt.timedelta(days=ONCE_DAYS)).isoformat(sep=" ")
    ts = now.isoformat(sep=" ")
    n = unread = 0
    for fk, side, sup, no in wait:
        f = by.get(fk)
        if f is not None and (f["paper"] or {}).get("state") == "unread":
            unread += 1
            continue
        say = f is not None and f["status"] == "open" and not f.get("act")
        if say and con.execute("SELECT 1 FROM billwatch_seen WHERE tell=1 AND fkey<>? AND side=? AND sup=? AND REPLACE(UPPER(bill_no),' ','')=? AND judged_at>=?",
                               (fk, side, sup, billno_norm(no), week)).fetchone():
            say = False                                        # this bill was told within the week
        con.execute("UPDATE billwatch_seen SET tell=?, line=?, judged_at=? WHERE fkey=?", (1 if say else 0, notice_line(f) if say else None, ts, fk))
        n += 1
    if unread:
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('billchange.unread_at', ?, 'S803: the scans could not be read when a new finding was judged')", (ts,))
    elif held:
        con.execute("DELETE FROM setting WHERE key='billchange.unread_at'")
    con.commit()
    return n


def tellable(con, now=None):
    """For owner_notice's part: [dict(fkey, kind, found_at, judged_at, line)] -- judged 'to tell' in the last two days, and not touched by
    him since (a row he closed overnight is not pushed in the morning). One cheap read."""
    since, floor, on_at = _floor(con, now)
    if not since or not is_on(con) or not _table(con, "billwatch_seen"):
        return []
    return [dict(fkey=r[0], kind=r[1], found_at=r[2], judged_at=r[3] or "", line=r[4] or "") for r in con.execute(
        "SELECT fkey, kind, found_at, judged_at, line FROM billwatch_seen WHERE before=0 AND counted=1 AND tell=1 AND judged_at IS NOT NULL AND found_at>=? "
        "AND found_at>? AND fkey NOT IN (SELECT fkey FROM billwatch_act) ORDER BY judged_at, fkey", (floor, on_at))]


# ====================================================================== the page (the owner's; English; the approved mock's look)
CSS = """
:root{--ink:#1d2430;--mute:#5b6676;--line:#dfe3ea;--bg:#f6f7f9;--card:#ffffff;--head:#fafbfc;--hover:#eef3fb;--inner:#fbfcfe;
 --up:#0b6b3a;--dn:#a3231b;--new:#b45309;--btn:#ffffff;--btnline:#b9c1cd;--accent:#1f4e8c;--accentbg:#e8f0fb;--amberbg:#fdf0d9;--okbg:#e7f5ec;
 --font:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 var(--font)}
.wrap{max-width:1180px;margin:0 auto;padding:16px}
.back{display:inline-flex;align-items:center;min-height:44px;padding:0 16px;border:1px solid var(--btnline);border-radius:9px;background:var(--btn);color:var(--accent);font-weight:700;text-decoration:none}
h1{font-size:22px;margin:10px 0 2px}
.sub{color:var(--mute);margin:0 0 14px;max-width:860px}
h2{font-size:17px;margin:0 0 4px}
h2 small{font-weight:400;color:var(--mute);font-size:13px;margin-left:6px}
.lead{color:var(--mute);font-size:13.5px;margin:0 0 10px;max-width:860px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin-bottom:16px}
.scroll{overflow-x:auto}
.tiles{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}
.tile{flex:1 1 170px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px;min-width:0}
.tile b{display:block;font-size:20px}
.tile span{color:var(--mute);font-size:13px}
.jump{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 14px}
.jump a{font-size:13.5px;text-decoration:none;color:var(--accent);background:var(--accentbg);border-radius:999px;padding:0 14px;min-height:44px;display:inline-flex;align-items:center}
table{border-collapse:collapse;width:100%}
th,td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font-size:12px;text-transform:uppercase;letter-spacing:.03em;color:var(--mute);background:var(--head)}
td.n,th.n,.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.up{color:var(--up);font-weight:600}.dn{color:var(--dn);font-weight:600}
.note{color:var(--mute);font-size:13px}
.badge{font-size:11px;font-weight:700;color:var(--new);border:1px solid var(--new);border-radius:4px;padding:0 4px;margin-left:6px;white-space:nowrap}
.st{display:inline-block;font-size:12px;border-radius:999px;padding:1px 9px;border:1px solid var(--line);color:var(--mute)}
.st.late{background:var(--amberbg);color:var(--new);border-color:transparent}
.st.ans{background:var(--okbg);color:var(--up);border-color:transparent}
button{font:14px var(--font);border:1px solid var(--btnline);background:var(--btn);color:var(--ink);border-radius:8px;padding:8px 12px;cursor:pointer;min-height:40px}
button:focus-visible,a:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
button.pri{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
details>summary{cursor:pointer}
.pgrid{display:grid;grid-template-columns:minmax(150px,2fr) repeat(4,minmax(70px,1fr));gap:8px;padding:10px 8px;border-bottom:1px solid var(--line);align-items:center;min-width:520px}
.phead{font-size:12px;text-transform:uppercase;letter-spacing:.03em;color:var(--mute);background:var(--head)}
.ptot{font-weight:700;border-top:2px solid var(--ink)}
details.pd>summary{list-style:none}
details.pd>summary::-webkit-details-marker{display:none}
details.pd>summary:hover{background:var(--hover)}
details.pd[open]>summary{background:var(--hover)}
details.pd[open]>summary .per{font-weight:700}
.per::before{content:"\\25B8 "}
details.pd[open]>summary .per::before{content:"\\25BE "}
.inner{padding:6px 8px 12px 24px;background:var(--inner);border-bottom:1px solid var(--line)}
table.btab{table-layout:fixed;min-width:760px}
table.btab>tbody>tr>td{overflow-wrap:anywhere}
details.fold>summary{font-weight:600;font-size:16px;padding:11px 0;min-height:44px}
details.fold[open]>summary{margin-bottom:10px}
.eff{font-size:13px;color:var(--mute);margin-top:3px}
.was{white-space:nowrap}
.dt>td{background:var(--inner);padding:12px}
.dh{font-weight:600;margin:0 0 6px}
table.bill{min-width:560px;table-layout:auto;background:var(--card);border:1px solid var(--line);margin-bottom:6px}
table.bill tr.tot td{font-weight:700;border-top:2px solid var(--ink)}
table.bill td:first-child,table.bill th{white-space:nowrap}
table.bill tr.nowr td{background:var(--okbg)}
input[type="radio"]{accent-color:var(--accent);width:18px;height:18px;vertical-align:-3px}
input[type="text"]{font:14px var(--font);padding:9px;border:1px solid var(--btnline);border-radius:8px;background:var(--btn);color:var(--ink);min-width:0;flex:1 1 220px;min-height:40px}
.closep{border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin-top:12px;background:var(--card)}
.closep label{display:block;margin:8px 0;cursor:pointer}
.askrow{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.msg{font-weight:700;color:var(--dn)}
.inp{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px}
.inp>div{border:1px solid var(--line);border-radius:8px;padding:8px 10px;min-width:0}
.inp span{display:block;color:var(--mute);font-size:13px}.inp b{display:block;font-size:15px}
.mwp{margin-top:12px;border:1px dashed var(--btnline);border-radius:8px;padding:10px;background:var(--card)}
.mwp .ph{font-weight:600;margin:0 0 2px}
ul.rec{margin:6px 0 0;padding-left:20px}ul.rec li{margin:3px 0;font-size:13.5px}
@media (max-width:820px){.inner{padding-left:8px}table.btab{min-width:0;table-layout:auto;display:block}.btab>colgroup{display:none}.btab>tbody{display:block}
 .btab>tbody>tr{display:block;padding:8px 0;border-bottom:1px solid var(--line)}.btab>tbody>tr.hd{display:none}.btab>tbody>tr[hidden]{display:none}
 .btab>tbody>tr>td{display:block;border:0;padding:3px 4px;text-align:left;white-space:normal}.btab>tbody>tr.dt>td{padding:10px 4px}
 .btab>tbody>tr>td[data-k]::before{content:attr(data-k) " · ";color:var(--mute);font-size:12px;font-weight:600}
 .pgrid{min-width:0;grid-template-columns:minmax(84px,1.6fr) repeat(4,minmax(36px,1fr));gap:4px;padding:10px 4px}.phead{font-size:10.5px;letter-spacing:0}
 .pgrid>span{overflow-wrap:anywhere}}
@media (max-width:640px){table.bill{min-width:0;display:block;border:0;background:none}table.bill>tbody{display:block}
 table.bill tr{display:block;border:1px solid var(--line);border-radius:8px;background:var(--card);padding:6px 8px;margin:0 0 6px}table.bill tr.hdr{display:none}
 table.bill td{display:inline-block;border:0;padding:1px 10px 1px 0;white-space:normal!important;text-align:left}
 table.bill td:empty{display:none}table.bill td[data-k]::before{content:attr(data-k) " ";color:var(--mute);font-size:12px}
 table.bill td:first-child{display:block;font-weight:600}table.bill tr.tot td{border:0}}
"""

JS = """
var MW=%(page)s;
function mwView(b){var id=b.getAttribute('data-f');var r=document.getElementById('d'+id);if(!r)return;r.hidden=!r.hidden;
 b.textContent=r.hidden?'View':'Hide';b.setAttribute('aria-expanded',r.hidden?'false':'true');if(r.hidden)return;
 var p=r.querySelector('.mwp[data-src]');if(!p||p.getAttribute('data-done'))return;p.setAttribute('data-done','1');
 var body=p.querySelector('.mwb');body.textContent='Opening the paper…';
 fetch(p.getAttribute('data-src'),{credentials:'same-origin'}).then(function(x){if(!x.ok)throw new Error('http');return x.text();}).then(function(h){
  var bill=p.getAttribute('data-bill');
  if(bill){[].forEach.call(document.querySelectorAll('.mwp[data-bill="'+bill+'"]'),function(o){if(o!==p&&o.getAttribute('data-done')){
    o.querySelector('.mwb').textContent='Open on the other row of this bill.';o.removeAttribute('data-done');}});}
  body.innerHTML=h;var d=body.querySelector('details.s738v');if(d&&!d.open){d.open=true;}
 }).catch(function(){body.textContent='The paper could not be opened just now. Tap View again.';p.removeAttribute('data-done');});}
function mwPost(path,data,m){if(m)m.textContent='Saving…';
 fetch(MW+path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})
 .then(function(r){return r.json();}).then(function(j){if(!j.ok){if(m)m.textContent=j.message||'Not saved.';return;}location.reload();})
 .catch(function(){if(m)m.textContent='Not saved — the network did not answer. Try again.';});}
function mwClose(b){var box=b.closest('.closep');var m=box.querySelector('.msg');var c=box.querySelector('input[type=radio]:checked');
 if(!c){m.textContent='Pick one of the choices first.';return;}
 mwPost('/api/close',{f:b.getAttribute('data-f'),decision:c.value,reason:box.querySelector('input[type=text]').value},m);}
function mwReopen(b){mwPost('/api/reopen',{f:b.getAttribute('data-f')},b.parentNode.querySelector('.msg'));}
function mwNotice(b){mwPost('/api/notice',{on:b.getAttribute('data-on')==='1'},b.parentNode.querySelector('.msg'));}
function mwLot(b){var m=b.parentNode.querySelector('.msg');if(b.getAttribute('data-sure')!=='1'){b.setAttribute('data-sure','1');
 b.textContent='Tap again to close all '+b.getAttribute('data-n')+' bills';return;}mwPost('/api/oklot',{n:parseInt(b.getAttribute('data-n'),10)},m);}
[].forEach.call(document.querySelectorAll('.jump a'),function(a){a.addEventListener('click',function(){var t=document.querySelector(a.getAttribute('href'));
 while(t){if(t.tagName==='DETAILS')t.open=true;t=t.parentElement;}});});
"""


def _pack_n(pack):
    """How many loose units make a pack: '1*10' -> 10, '10 TAB' / '15T' -> the number; 1 when the text names none."""
    m = re.search(r"(\d+)\s*[*xX]\s*(\d+)", str(pack or ""))
    if m and int(m.group(2)) > 0:
        return int(m.group(2))
    m = re.match(r"^\s*(\d+)", str(pack or ""))
    return int(m.group(1)) if m and int(m.group(1)) > 1 else 1


def _sale_amount_p(l):
    """A sale line's amount: Marg's rate per pack x (packs + loose / pack size)."""
    m = re.match(r"^\s*(\d+)\s*:\s*(\d+)\s*$", str(l["qty"] or ""))
    try:
        q = (int(m.group(1)) + int(m.group(2)) / float(_pack_n(l["pack"]))) if m else float(str(l["qty"] or "0"))
    except ValueError:
        q = 0.0
    return int(round(l["amt_p"] * q))


def _tbl(head, rows):
    h = ["<div class='scroll'><table class='bill'><tr class='hdr'>"]
    h += ["<th%s>%s</th>" % (" class='n'" if i > 1 else "", esc(c)) for i, c in enumerate(head)]
    h.append("</tr>")
    for r in rows:
        h.append("<tr%s>" % (" class='%s'" % r["cls"] if r.get("cls") else ""))
        h += ["<td%s%s>%s</td>" % (" class='n'" if i > 1 else "", (' data-k="%s"' % esc(head[i])) if (i > 1 and head[i] and str(c) != "") else "", esc(c))
              for i, c in enumerate(r["c"])]
        h.append("</tr>")
    h.append("</table></div>")
    return "".join(h)


def _pline(label, l, extra=()):
    return dict(c=[label, l["item"], _g(l["qty"]), _g(l["free"]) if l["free"] else "—", rs(l["rate_p"])]
                + [("%s%%" % _g(l.get(k, 0))) for k in extra] + [rs(l["amt_p"])])


def _pcols(lines):
    """The strip's columns: discount and GST show only when a line carries one (so a change of either is seen where it happened)."""
    extra = tuple(k for k in ("disc", "tax") if any(l.get(k) for l in lines))
    return ["", "Item", "Qty", "Free", "Rate"] + [{"disc": "Disc", "tax": "GST"}[k] for k in extra] + ["Net amount"], extra


def strip_html(f):
    """What the bill was -- the one strip the Marg watch adds (D924, D936)."""
    was_d, now_d = stamp_day(f["was_stamp"]), stamp_day(f["now_stamp"])
    if f["side"] == "sale":
        b = f["was"] if f["kind"] == "gone" else f["now"]
        rows, tot = [], 0
        for l in b["lines"]:
            a = _sale_amount_p(l)
            tot += a
            rows.append(dict(c=[l["item"], l["pack"], _sale_qty(l["qty"]), rs(l["amt_p"]), rs(a)]))
        if f.get("bill_p") is not None and int(f["bill_p"]) != tot:
            rows.append(dict(c=["Round-off / discount on the bill", "", "", "", rs(int(f["bill_p"]) - tot)]))
        bill = ("%s%s" % (rs(f["bill_p"]), (" · " + f["pay"]) if f["pay"] else "")) if f.get("bill_p") is not None else rs(tot)
        rows.append(dict(cls="tot", c=["Bill total", "", "", "", bill]))
        head = ("The bill as Marg reported it — report taken %s" % was_d) if f["kind"] == "gone" else ("The bill as Marg reports it — report taken %s" % now_d)
        note = ("<p class='note'>A sale bill has no paper. In the report taken %s it is not there.</p>" % esc(now_d)) if f["kind"] == "gone" else \
            "<p class='note'>A sale bill has no paper.</p>"
        return "<p class='dh'>%s</p>%s%s" % (esc(head), _tbl(["Item", "Pack", "Qty", "Rate per pack", "Amount"], rows), note)
    if f["kind"] in ("late", "gone"):
        b = f["now"] if f["kind"] == "late" else f["was"]
        cols, extra = _pcols(b["lines"])
        rows = [_pline("", l, extra) for l in b["lines"]]
        rows.append(dict(cls="tot", c=["Lines total", "", "", "", ""] + [""] * len(extra) + [rs(sum(l["amt_p"] for l in b["lines"]))]))
        head = ("The bill in Marg — first seen in the report taken %s" % now_d) if f["kind"] == "late" else \
            ("The bill as Marg listed it — report taken %s; gone in the one taken %s" % (was_d, now_d))
        return "<p class='dh'>%s</p>%s" % (esc(head), _tbl(cols, rows))
    rows = []
    shown = [c for c in sorted(f["changes"], key=lambda c: c["kind"] in RECORD_KINDS) if f["record"] or c["kind"] not in ("paise", "value", "rename")]
    cols, extra = _pcols([l for c in shown for l in c["was"] + c["now"]])    # a counted bill's strip shows the lines that count
    pad = [""] * (3 + len(extra))
    for c in shown:
        for l in c["was"]:
            rows.append(_pline("Was · %s" % was_d, l, extra))
        if not c["was"]:
            rows.append(dict(c=["Was · %s" % was_d, "— no such line —"] + pad + [""]))
        for l in c["now"]:
            r = _pline("Now · %s" % now_d, l, extra)
            r["cls"] = "nowr"
            rows.append(r)
        if not c["now"]:
            rows.append(dict(cls="nowr", c=["Now · %s" % now_d, "— line removed —"] + pad + [""]))
    wt, nt = sum(l["amt_p"] for l in f["was"]["lines"]), sum(l["amt_p"] for l in f["now"]["lines"])
    rows.append(dict(cls="tot", c=["All lines of the bill", ""] + pad + [("was %s → now %s" % (rs(wt), rs(nt))) if wt != nt else ("%s — unchanged" % rs(nt))]))
    dates = ("<p class='note'>Bill date: was %s, now %s.</p>" % (esc(dmon(f["was"]["date"])), esc(dmon(f["now"]["date"])))) if f.get("redated") else ""
    return "<p class='dh'>What the bill was — and what it is now</p>%s%s" % (_tbl(cols, rows), dates)


def decision_html(f):
    """D923: he closes the row himself, on the row, with a reason. A removed sale bill carries its two choices."""
    fk = f["fkey"]
    act = f.get("act") or {}
    if f["status"] in ("closed", "settled"):
        if f["status"] == "closed":
            line = "Closed by you — %s%s · %s." % (DECISIONS.get(act.get("decision"), "OK"), (": " + act["reason"]) if act.get("reason") else "", dmon(str(act.get("at"))[:10]))
        else:
            line = "Settled by the scanned bill — nothing is asked of you."
        return ('<div class="closep"><div class="askrow"><span>%s</span><button type="button" data-f="%s" onclick="mwReopen(this)">Reopen</button>'
                '<span class="msg"></span></div></div>' % (esc(line), fk))
    if f["side"] == "sale" and f["kind"] == "gone":
        ch = (("stands", "<b>The sale stands</b> — the goods left; the bill is to go back into Marg"),
              ("cancelled", "<b>The sale was cancelled</b> — the goods came back and the cash was returned"))
        tail = ("<p class='note' style='margin:8px 0 0'>This row is yours: removing a sale bill is your own act, so it never goes to the counter. A sale "
                "return (credit note) in Marg keeps the bill on record — then nothing is flagged here. Your answer is kept with the row; the stock "
                "side acts on it when section A (stock moved with no record) is added.</p>")
    elif f["kind"] == "late":
        ch = (("ok", "<b>OK</b> — a genuine bill, entered late"), ("notok", "<b>Not OK</b> — to be looked into; the row stays open, marked"))
        tail = ""
    else:
        ch = (("ok", "<b>OK</b> — correct as it is now"), ("notok", "<b>Not OK</b> — to be put right in Marg; the row stays open, marked"))
        tail = ""
    was = ""
    if act.get("action") == "notok":
        was = "<p class='note' style='margin:0 0 6px'>Marked Not OK by you on %s%s.</p>" % (esc(dmon(str(act.get("at"))[:10])), esc((": " + act["reason"]) if act.get("reason") else ""))
    h = ['<div class="closep">%s<b>Your decision</b>' % was]
    for v, words in ch:
        h.append('<label><input type="radio" name="c%s" value="%s"> %s</label>' % (fk, v, words))
    h.append('<div class="askrow" style="margin:8px 0 0"><input type="text" maxlength="300" placeholder="Reason (optional)" aria-label="Reason (optional)">'
             '<button type="button" class="pri" data-f="%s" onclick="mwClose(this)">Save my decision</button><span class="msg"></span></div>%s</div>' % (fk, tail))
    return "".join(h)


def status_html(f):
    act = f.get("act") or {}
    if f["status"] == "closed":
        return '<span class="st ans">Closed by you — %s</span>' % esc(DECISIONS.get(act.get("decision"), "OK"))
    if f["status"] == "settled":
        return '<span class="st ans">Settled — matches the paper ✓</span>'
    if act.get("action") == "notok":
        return '<span class="st late">Marked Not OK by you</span>'
    if act.get("action") == "reopen":
        return '<span class="st">Open — reopened by you</span>'
    if f["side"] == "sale" and f["kind"] == "gone":
        return '<span class="st late">Yours to close</span>'
    ps = (f.get("paper") or {}).get("state")
    if ps == "no_paper":
        return '<span class="st late">No paper on file</span>'
    if ps == "differs":
        return '<span class="st late">Marg differs from the paper</span>'
    if ps == "unread":
        return '<span class="st">Open · paper not read just now</span>'
    return '<span class="st">Open</span>'


def row_html(f):
    fk = f["fkey"]
    who = ("Sale" + ((" · " + f["pay"]) if f["pay"] else "")) if f["side"] == "sale" else " ".join(f["sup"].split()).title()
    new = "" if f["before"] else '<span class="badge">NEW</span>'
    rup = int(f.get("rupee_p") or 0)
    money = ('<span class="%s">%s</span>' % ("dn" if rup < 0 else "up", esc(rs(rup, sign=True)))) if rup else "₹0"
    eff = ('<div class="eff">%s</div>' % esc(f["effect"])) if f["effect"] else ""
    main = ('<tr data-f="%s"><td class="was" data-k="Bill date">%s</td><td><b>%s</b>%s<br><span class="note">%s</span></td><td>%s%s<div class="eff">%s</div></td>'
            '<td class="n" data-k="Effect">%s</td><td>%s</td><td><button type="button" class="pri" data-f="%s" aria-expanded="false" aria-controls="d%s" onclick="mwView(this)">View</button></td></tr>'
            % (fk, esc(dmon(f["date"])), esc(f["no"]), new, esc(who), esc(f["what"]), eff, esc(f["seen"]), money, status_html(f), fk, fk))
    panel = ""
    if f["side"] == "purchase":
        b = (f.get("paper") or {}).get("bill")
        panel = ('<div class="mwp" data-src="%s/api/panel?f=%s"%s><p class="ph">The scanned bill — from the Purchase bills page</p><div class="mwb note">'
                 '</div></div>' % (PAGE, fk, (' data-bill="%d"' % int(b["id"])) if b else ""))
    det = '<tr class="dt" id="d%s" hidden><td colspan="6">%s%s%s</td></tr>' % (fk, strip_html(f), panel, decision_html(f))
    return main + det


BTAB_HEAD = ('<table class="btab"><colgroup><col style="width:8%"><col style="width:16%"><col style="width:38%"><col style="width:10%"><col style="width:17%">'
             '<col style="width:11%"></colgroup><tbody><tr class="hd"><th>Bill date</th><th>Bill</th><th>What changed</th><th class="n">₹ effect</th><th>Status</th><th></th></tr>')


def table_html(fs):
    return '<div class="scroll">%s%s</tbody></table></div>' % (BTAB_HEAD, "".join(row_html(f) for f in fs))


def months_html(fs):
    """The findings by the month of the bill: a grid that opens (the approved shape)."""
    by = {}
    for f in fs:
        by.setdefault(f["month"], []).append(f)
    h = ['<div class="scroll"><div class="pgrid phead"><span>Month of the bill</span><span class="n">Bills</span><span class="n">Removed</span>'
         '<span class="n">Added late</span><span class="n">Changed</span></div>']
    tot = [0, 0, 0, 0]
    for i, m in enumerate(sorted(by, reverse=True)):
        g = by[m]
        c = [len(g), sum(1 for f in g if f["kind"] == "gone"), sum(1 for f in g if f["kind"] == "late"), sum(1 for f in g if f["kind"] in ("changed", "redated"))]
        tot = [a + b for a, b in zip(tot, c)]
        h.append('<details class="pd"%s><summary class="pgrid"><span class="per">%s</span>%s</summary><div class="inner">%s</div></details>'
                 % (" open" if i == 0 else "", esc(month_name(m)), "".join('<span class="n">%s</span>' % (v or "—") for v in c), table_html(g)))
    h.append('<div class="pgrid ptot"><span>Total</span>%s</div></div>' % "".join('<span class="n">%s</span>' % (v or "—") for v in tot))
    return "".join(h)


def inputs_html(con, B):
    """Today's inputs: the page checks what it reads before it judges (the owner's 12-Nov ruling, folded into plan v3 0A)."""
    cells = []
    try:
        r = con.execute("SELECT date_to, stamp FROM mi_file WHERE type='SALE_BILLWISE' AND verdict='VERIFIED' ORDER BY date_to DESC, stamp DESC LIMIT 1").fetchone()
    except sqlite3.Error:
        r = None
    if r:
        t = _taken(r[1])
        cells.append(("Sale report", '<b class="up">In ✓</b>', "up to %s · taken %s" % (dmon(r[0]), (dmon(t.date().isoformat()) + t.strftime(" %H:%M")) if t else "")))
    else:
        cells.append(("Sale report", '<b class="dn">None on the server</b>', "sale bills are not judged"))
    ex = purchase_exports(con)
    part_md5 = {p["md5"] for p in B["parts"] if not p.get("fwd")}   # a list only refused as a baseline is still a list
    full = [e for e in ex if e["md5"] not in part_md5]
    note = ""
    if full:
        e = full[-1]
        later = [p for p in B["parts"] if p["stamp"] > e["stamp"] and not p.get("fwd")]
        cells.append(("Purchase list", '<b class="up">Complete ✓</b>' if not later else '<b style="color:var(--new)">A part list came last</b>',
                      "%s to %s · %d bills · taken %s" % (dmon(e["f"].isoformat()), dmon(e["t"].isoformat()), len(e["bills"]), stamp_day(e["stamp"]))))
        if later:
            p = later[-1]
            note = ('<p class="note" style="margin:10px 0 0"><span class="st late">Purchase list — part, %d of %d bills</span> The list taken %s holds only a part of '
                    'its period, so it is set aside: bills changed since the full list of %s are <b>not judged</b> until a full list arrives. No flag is raised '
                    'from a part list.</p>' % (p["n"], p["of"], esc(stamp_day(p["stamp"])), esc(stamp_day(e["stamp"]))))
    else:
        cells.append(("Purchase list", '<b class="dn">None on the server</b>', "purchase bills are not judged"))
    if B["paper_ok"]:
        try:
            pa = SR()._pa()
            m = con.execute("SELECT MAX(b.month) FROM purchase_bill b WHERE " + pa.EFF_BILL).fetchone()[0]
            n = con.execute("SELECT COUNT(*) FROM purchase_bill b WHERE b.month=? AND " + pa.EFF_BILL, (m,)).fetchone()[0]
            k = con.execute("SELECT COUNT(*) FROM purchase_bill b JOIN purchase_scan_link l ON l.bill_id=b.id WHERE b.month=? AND " + pa.EFF_BILL, (m,)).fetchone()[0]
            cells.append(("Scanned bills", '<b class="up">Read ✓</b>', "%d of %d %s bills have their paper" % (k, n, month_name(m).split()[0])))
        except Exception:                                     # noqa: BLE001
            cells.append(("Scanned bills", '<b class="up">Read ✓</b>', ""))
    else:
        cells.append(("Scanned bills", '<b class="dn">Not read</b>', "purchase bills are not judged against their paper now — %s" % B["paper_why"]))
    return ('<div class="card" id="inputs"><h2>Today\'s inputs <small>checked before anything is judged</small></h2><div class="inp">%s</div>%s</div>'
            % ("".join("<div><span>%s</span>%s<span>%s</span></div>" % (esc(a), b, esc(c)) for a, b, c in cells), note))


def notice_html(con):
    """The phone notice, in his hands: off until he turns it on here."""
    on = is_on(con)
    a, b = setting(con, "owner_notice.hand_from", "08:00") or "08:00", setting(con, "owner_notice.hand_to", "21:00") or "21:00"
    if on:
        frm = setting(con, "billchange.tell_from", "")
        return ('<div class="askrow" style="margin:0 0 10px"><span>Phone notice of a newly changed bill: <b class="up">On</b>%s</span>'
                '<button type="button" data-on="0" onclick="mwNotice(this)">Turn off</button><span class="msg"></span></div>'
                '<p class="note" style="margin:0 0 10px">You are told once about a bill found from then on that needs you, between %s and %s — never about one its '
                'scanned paper settles, and the same bill at most once a week.</p>' % ((" since %s" % esc(dmon(frm[:10]))) if frm else "", esc(a), esc(b)))
    return ('<div class="askrow" style="margin:0 0 10px"><span>Phone notice of a newly changed bill: <b>Off</b></span>'
            '<button type="button" data-on="1" onclick="mwNotice(this)">Turn on</button><span class="msg"></span></div>'
            '<p class="note" style="margin:0 0 10px">Off to begin with, so you can watch this page first. Turned on, you are told once about a bill found from then on '
            'that needs you, between %s and %s. Nothing found earlier is ever sent.</p>' % (esc(a), esc(b)))


def record_html(B):
    """For the record: never counted, never told."""
    rec = B["record"]
    groups = (("Marg's own purchase rate was re-set on an old bill — the value Marg puts on the stock moved; the bill's money did not", lambda f: any(c["kind"] == "value" for c in f["changes"])),
              ("An item was renamed in Marg — the same line under a new name", lambda f: any(c["kind"] == "rename" for c in f["changes"])),
              ("A line differs only by paise", lambda f: any(c["kind"] == "paise" for c in f["changes"])),
              ("A sale bill's money changed with the same items — not watched: your daily cash and UPI checks lock each day", lambda f: f["side"] == "sale"))
    h, used = [], set()
    for title, test in groups:
        g = [f for f in rec if f["fkey"] not in used and test(f)]
        used |= {f["fkey"] for f in g}
        if not g:
            continue
        h.append("<p class='dh' style='margin-top:10px'>%s (%d)</p><ul class='rec'>%s</ul>" % (esc(title), len(g), "".join(
            "<li><b>%s %s</b> · %s — %s <span class='note'>(report taken %s)</span></li>"
            % (esc("Sale" if f["side"] == "sale" else " ".join(f["sup"].split()).title()), esc(f["no"]), esc(dmon(f["date"])), esc(f["what"]), esc(stamp_day(f["now_stamp"])))
            for f in g)))
    if B["parts"]:
        h.append("<p class='dh' style='margin-top:10px'>Part lists (%d)</p><ul class='rec'>%s</ul>" % (len(B["parts"]), "".join(
            ("<li>The purchase list taken %s (%s to %s) held only %d of the %d bills it should have — a filtered print. No bill is called "
             "\u201cadded late\u201d against it; it is still read for removed and changed bills.</li>" if p.get("fwd") else
             "<li>The purchase list taken %s (%s to %s) held %d of %d bills — a part print; nothing is judged from it.</li>")
            % (esc(stamp_day(p["stamp"])), esc(dmon(p["f"].isoformat())), esc(dmon(p["t"].isoformat())), p["n"], p["of"]) for p in B["parts"])))
    return "".join(h) or "<p class='note'>Nothing.</p>"


def page_html(con):
    B = build(con, paper=True)
    fs = B["findings"]
    new = [f for f in fs if not f["before"] and f["status"] == "open"]
    old = [f for f in fs if f["before"] and f["status"] == "open"]
    settled = [f for f in fs if f["status"] == "settled"]
    closed = [f for f in fs if f["status"] == "closed"]
    lot = [f for f in old if not (f["side"] == "sale" and f["kind"] == "gone")]
    nopaper = sum(1 for f in new + old if (f.get("paper") or {}).get("state") == "no_paper")
    since = B["since"]
    began = ("the page began %s" % dmon(since[:10])) if since else "the page has not begun yet — everything below is history"
    h = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
         '<title>Marg watch</title><style>%s</style><style>%s</style></head><body><div class="wrap">' % (CSS, _panel_css())]
    h.append('<a class="back" href="/finance/console">← Back</a><h1>Marg watch</h1><p class="sub"><b>Bills changed after their day</b> — a bill that was removed, '
             'added late or altered in Marg after the day\'s report was taken. Found from the reports the staff already make; nothing new is asked of them. '
             'Stock that moved in Marg with no record is the next part to be built.</p>')
    h.append(inputs_html(con, B))
    h.append('<div class="tiles"><div class="tile"><span>New since the page began</span><b>%d</b><span>shown here first</span></div>'
             '<div class="tile"><span>Before this page · to look at</span><b>%d</b><span>%s</span></div>'
             '<div class="tile"><span>Settled by the scanned bill</span><b>%d</b><span>closed automatically</span></div>'
             '<div class="tile"><span>Closed by you</span><b>%d</b><span>each can be reopened</span></div></div>'
             % (len(new), len(old), ("%d have no paper on file" % nopaper) if nopaper else "found in the reports so far", len(settled), len(closed)))
    h.append('<div class="jump"><a href="#inputs">Today\'s inputs</a><a href="#since">Since the page began</a><a href="#before">Before this page</a>'
             '<a href="#settled">Settled by the scanned bill</a><a href="#closed">Closed by you</a><a href="#record">For the record</a></div>')
    h.append('<div class="card" id="since"><h2>Since the page began <small>%s · %s</small></h2>' % (("%d new" % len(new)) if new else "nothing new", esc(began)))
    h.append('<p class="lead">A bill changed after its day shows here first.</p>')
    h.append(notice_html(con))
    if new:
        h.append(table_html(new))
    h.append("</div>")
    h.append('<div class="card" id="before"><h2>Before this page <small>%d bill%s</small></h2>' % (len(old), "" if len(old) == 1 else "s"))
    if old:
        h.append('<p class="lead">Everything found before the page began. It is listed and you were never notified of it. Close them all with one OK — or open a '
                 'month and close row by row. Each stays on record and can be reopened.</p>')
        if lot:
            h.append('<div class="askrow" style="margin:0 0 12px"><button type="button" class="pri" data-n="%d" onclick="mwLot(this)">OK all %d — close them together</button>'
                     '<span class="msg"></span>%s</div>' % (len(lot), len(lot),
                                                            '<span class="note">A removed sale bill is left out — it keeps its own two choices.</span>' if len(lot) != len(old) else ""))
        h.append(months_html(old))
    else:
        h.append('<p class="lead" style="margin:0">Nothing waits from before the page began.</p>')
    h.append("</div>")
    h.append('<div class="card" id="settled"><details class="fold"><summary>Settled by the scanned bill — closed automatically (%d)</summary>'
             '<p class="lead">A purchase bill was changed or added in Marg, and it now agrees with its scanned paper to the rupee. That is an entry put right, so '
             'nothing is asked of you. Each stays here to look at; <b>Reopen</b> (inside View) sends it back to the list. A change that does not agree with the '
             'paper, or a bill with no paper, is never settled this way.</p>%s</details></div>' % (len(settled), table_html(settled) if settled else "<p class='note'>None yet.</p>"))
    h.append('<div class="card" id="closed"><details class="fold"><summary>Closed by you (%d)</summary>%s</details></div>'
             % (len(closed), table_html(closed) if closed else "<p class='note'>None yet.</p>"))
    h.append('<div class="card" id="record"><details class="fold"><summary>For the record — no action needed (%d bill%s%s)</summary>%s</details></div>'
             % (len(B["record"]), "" if len(B["record"]) == 1 else "s", (" · %d part list%s" % (len(B["parts"]), "" if len(B["parts"]) == 1 else "s")) if B["parts"] else "",
                record_html(B)))
    h.append('</div><script>%s</script>%s</body></html>' % (JS % dict(page=json.dumps(PAGE)), _panel_js()))
    return "".join(h)


def _panel_css():
    """The Purchase bills page's own styles for its panel (provisional_s781.CSS, under #s781) -- read from it, not copied."""
    try:
        return (PV().CSS + "#s781{margin:0}#s781 .pv .s738f iframe{height:560px}#s781 .pv .s738f img{max-width:100%}"
                "#s781 .pv summary{list-style:none}#s781 .pv summary::-webkit-details-marker{display:none}")
    except Exception:                                         # noqa: BLE001
        return ""


def _panel_js():
    """Its scripts: the scan's lazy opener (scan_register.S738_JS, without the page's up-arrow) and its taps (provisional_s781.JS)."""
    try:
        s738 = SR().S738_JS.split("<button", 1)[0]
        return s738 + PV().JS % dict(P=PURCHASE_PREFIX)
    except Exception:                                         # noqa: BLE001
        return ""


def panel_html(con, fk):
    """The opened part of a purchase row: the Purchase bills page's own panel for that bill (D936) -- (html, http code)."""
    B = build(con, paper=True)
    f = next((x for x in B["findings"] if x["fkey"] == fk), None)
    if f is None or f["side"] != "purchase":
        return "<p class='note'>This row is no longer on the list. Reload the page.</p>", 404
    ps = f["paper"]
    st = ps["state"]
    if st in ("no_paper", "no_bill", "unread", "sale"):
        extra = " Every changed bill with a scan shows its paper here; this one has none to check against." if st == "no_paper" else ""
        return "<p style='margin:4px 0'><b>%s</b>%s</p>" % (esc(ps["words"]), esc(extra)), 200
    P = PV()
    try:
        if st == "differs" and ps.get("dx") is not None:
            body = P._panel(con, ps["dx"], PURCHASE_PREFIX)        # that page's panel, whole: the difference, the lines, its taps, the scan
            verdict = "<p style='margin:4px 0 8px'><b class='dn'>%s</b> <span class='note'>The taps below are the Purchase bills page's own.</span></p>" % esc(ps["words"])
        else:
            body = _agree_panel(con, P, ps)
            verdict = "<p style='margin:4px 0 8px'><b class='%s'>%s</b> <span class='note'>— the Purchase bills page's verdict.</span></p>" % (
                "up" if st == "settled" else "", esc(ps["words"]))
    except Exception as e:                                    # noqa: BLE001
        return "<p class='note'>The paper could not be shown just now (%s). Tap View again.</p>" % esc(e.__class__.__name__), 200
    return verdict + '<div id="s781">' + body + "</div>", 200


def _agree_panel(con, P, ps):
    """A bill that agrees with its scan has no open panel on the Purchase bills page (it opens one only where Marg differs). The same
    parts, made by that page's own functions: the paper's lines beside Marg's (Assets, marg_lines, pair_lines) and its scan viewer."""
    S = SR()
    b, sid = ps["bill"], int(ps["sid"])
    slines = P.Assets([sid]).lines.get(sid, [])
    mlines = P.marg_lines(con, b)
    pairs = P.pair_lines(slines, mlines) if slines else []
    rows = []
    for a, m in pairs:
        miss = a is None or m is None
        rows.append('<tr class="%s"><td>%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td><td>%s</td></tr>'
                    % ("miss" if miss else "", S.esc((a or m)["name"]) + ((' <span class="sub">(Marg: %s)</span>' % S.esc(m["name"]))
                                                                         if a and m and P._norm(a["name"]) != P._norm(m["name"]) else ""),
                       S.esc("%g" % a["qty"]) if a and a.get("qty") is not None else "—", S.esc(S.rs2(P._p(a["amount"]))) if a and a.get("amount") is not None else "—",
                       S.esc("%g" % m["qty"]) if m and m.get("qty") is not None else "—", S.esc(S.rs2(P._p(m["amount"]))) if m and m.get("amount") is not None else "—",
                       "<b>not in Marg</b>" if m is None else ("<b>not on the paper</b>" if a is None else "both")))
    table = ('<div class="tw"><table class="items"><tr><th>Item</th><th class="n">Scan qty</th><th class="n">Scan ₹</th><th class="n">Marg qty</th>'
             '<th class="n">Marg ₹</th><th></th></tr>%s</table></div>' % "".join(rows)) if rows else '<div class="sub">No item lines were read on this scan.</div>'
    src = "%s/api/s738/scan/%d" % (PURCHASE_PREFIX, sid)
    viewer = ('<details class="s738v" ontoggle="s738open(this)"><summary>The scanned paper ▾</summary><div class="s738vb"><div class="s738f" data-src="%s">'
              '</div></div></details><a class="lnk" href="%s" target="_blank" rel="noopener">Open the scan in a new tab</a>' % (S.esc(src), S.esc(src)))
    head = '<div class="dw">Scan %s · paper %s · Marg %s</div>' % (S.esc(ps.get("stamp") or ""), S.esc(rs(abs(int(ps.get("paper_p") or 0)))), S.esc(rs(abs(int(ps.get("marg_p") or 0)))))
    return '<div class="pnl"><div class="pw">%s%s</div><div class="pv">%s</div></div>' % (head, table, viewer)


# ====================================================================== the routes (the doctor only)
def _mount():
    from flask import Blueprint, jsonify, request            # noqa: PLC0415 -- the web side only; the cron side never needs Flask here

    bp = Blueprint("marg_billwatch", __name__)

    def _doc():
        u, err = _require("checker")                           # the medical unit's checker: Dr Manoj alone (the owner's S179 rule)
        return u, err

    def _html(body, code=200):
        return body, code, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}

    @bp.route(PAGE)
    def page():
        u, err = _doc()
        if err:
            return err
        con = _db()
        try:
            refresh(con)                                       # note what is new (its own table only); never holds the page
        except Exception as e:                                # noqa: BLE001
            print("marg_billwatch refresh failed: %r" % (e,), file=sys.stderr)
            try:
                con.rollback()
            except sqlite3.Error:
                pass
        return _html(page_html(con))

    @bp.route(PAGE + "/api/panel")
    def api_panel():
        u, err = _doc()
        if err:
            return err
        fk = str(request.args.get("f") or "")
        if not re.match(r"^[0-9a-f]{16}$", fk):
            return _html("<p class='note'>Which row?</p>", 400)
        body, code = panel_html(_db(), fk)
        return _html(body, code)

    @bp.route(PAGE + "/api/healthz")
    def api_healthz():
        u, err = _doc()
        if err:
            return err
        con = _db()
        return jsonify(ok=True, module="marg_billwatch", kit=KIT, version=VERSION, since=setting(con, "billchange.since", ""), on=is_on(con))

    def _post():
        u, err = _doc()
        if err:
            return None, None, None, err
        return u, _db(), (request.get_json(silent=True) or {}), None

    @bp.route(PAGE + "/api/close", methods=["POST"])
    def api_close():
        u, con, b, err = _post()
        if err:
            return err
        ok, msg, code = close(con, str(u.get("user") or "owner"), str(b.get("f") or ""), str(b.get("decision") or ""), str(b.get("reason") or ""))
        return jsonify(ok=ok, message=msg), code

    @bp.route(PAGE + "/api/reopen", methods=["POST"])
    def api_reopen():
        u, con, b, err = _post()
        if err:
            return err
        ok, msg, code = reopen(con, str(u.get("user") or "owner"), str(b.get("f") or ""))
        return jsonify(ok=ok, message=msg), code

    @bp.route(PAGE + "/api/notice", methods=["POST"])
    def api_notice():
        u, con, b, err = _post()
        if err:
            return err
        if not isinstance(b.get("on"), bool):
            return jsonify(ok=False, message="On or off?"), 400
        ok, msg, code = set_notice(con, str(u.get("user") or "owner"), b["on"])
        return jsonify(ok=ok, message=msg), code

    @bp.route(PAGE + "/api/oklot", methods=["POST"])
    def api_oklot():
        u, con, b, err = _post()
        if err:
            return err
        ok, msg, code = ok_lot(con, str(u.get("user") or "owner"), b.get("n"))
        return jsonify(ok=ok, message=msg), code

    return bp


def init(app, db_getter, require_fn):
    """Mount only (called by sanjeevni_approvals.init, fail-soft). Opens no connection."""
    global _db, _require
    _db, _require = db_getter, require_fn
    bp = _mount()
    app.register_blueprint(bp)
    return bp


# ====================================================================== his acts (the only writes besides the first-seen stamps)
def _audit(con, who, action, ref, detail):
    try:
        SR()._pa()._audit(con, who, action, str(ref), detail)
    except Exception:                                         # noqa: BLE001 -- the act row itself is the record
        pass


def _find(con, fk):
    if not re.match(r"^[0-9a-f]{16}$", str(fk or "")):
        return None
    return next((f for f in build(con, paper=True)["findings"] if f["fkey"] == fk), None)


def _write(fn):
    def run(con, *a):
        try:
            ensure(con)
            return fn(con, *a)
        except sqlite3.Error as e:
            try:
                con.rollback()
            except sqlite3.Error:
                pass
            return False, "Not saved — the database was busy (%s). Try again." % str(e)[:60], 503
    return run


@_write
def close(con, who, fk, decision, reason):
    """(ok, message, http). His decision on a row: closes it -- or, for Not OK, keeps it open and marked."""
    f = _find(con, fk)
    if f is None:
        return False, "This row is no longer on the list — the page was out of date. Reload it.", 409
    if f["status"] == "closed":
        return False, "This row is already closed. Reopen it first.", 409
    gone_sale = f["side"] == "sale" and f["kind"] == "gone"
    allowed = ("stands", "cancelled") if gone_sale else ("ok", "notok")
    if decision not in allowed:
        return False, "Pick one of the choices.", 400
    reason = re.sub(r"\s+", " ", str(reason or "")).strip()[:300]
    action = "notok" if decision == "notok" else "close"
    con.execute("INSERT INTO billwatch_act (fkey, action, decision, reason, by_user, at) VALUES (?,?,?,?,?,?)", (fk, action, decision, reason or None, who, now_iso()))
    _audit(con, who, "billwatch_" + action, fk, dict(decision=decision, reason=reason or None, bill=f["no"], sup=f["sup"], date=f["date"], kind=f["kind"]))
    con.commit()
    return True, "Saved.", 200


@_write
def reopen(con, who, fk):
    f = _find(con, fk)
    if f is None:
        return False, "This row is no longer on the list — the page was out of date. Reload it.", 409
    if f["status"] not in ("closed", "settled") and (f.get("act") or {}).get("action") != "notok":
        return False, "This row is open already.", 409
    con.execute("INSERT INTO billwatch_act (fkey, action, decision, reason, by_user, at) VALUES (?,?,?,?,?,?)", (fk, "reopen", None, None, who, now_iso()))
    _audit(con, who, "billwatch_reopen", fk, dict(bill=f["no"], sup=f["sup"], date=f["date"], was=f["status"]))
    con.commit()
    return True, "Reopened.", 200


@_write
def ok_lot(con, who, n_shown):
    """One OK for every bill open from before the page began -- except a removed sale bill, which keeps its own two choices. The count
    he saw must be the count now, or nothing is closed (the list moved under him)."""
    lot = [f for f in build(con, paper=True)["findings"]
           if f["before"] and f["status"] == "open" and not (f["side"] == "sale" and f["kind"] == "gone")]
    try:
        n_shown = int(n_shown)
    except (TypeError, ValueError):
        n_shown = -1
    if not lot:
        return False, "Nothing is waiting from before the page began.", 409
    if n_shown != len(lot):
        return False, "The list changed while the page was open (%d now). Reload it and look again." % len(lot), 409
    ts = now_iso()
    for f in lot:
        con.execute("INSERT INTO billwatch_act (fkey, action, decision, reason, by_user, at) VALUES (?,?,?,?,?,?)", (f["fkey"], "close", "lot", None, who, ts))
    _audit(con, who, "billwatch_ok_lot", "", dict(n=len(lot), fkeys=[f["fkey"] for f in lot]))
    con.commit()
    return True, "Closed %d." % len(lot), 200


@_write
def set_notice(con, who, on):
    """The phone notice on or off -- his tap on the page. Turned on, only what is FOUND from this moment is told."""
    ts = now_iso()
    con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('billchange.on', ?, 'S803: the phone notice of a changed bill -- his switch on the Marg watch')",
                ("on" if on else "off",))
    if on:
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('billchange.tell_from', ?, 'S803: the notice was turned on; nothing found before this is told')", (ts,))
    _audit(con, who, "billwatch_notice", "", dict(on=bool(on)))
    con.commit()
    return True, "The phone notice is %s." % ("on" if on else "off"), 200


# ====================================================================== the command line
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2 or argv[1] not in ("--fill", "--show"):
        print(__doc__)
        return 2
    ro = argv[1] == "--show"
    con = sqlite3.connect(("file:%s?mode=ro" % argv[0]) if ro else argv[0], uri=ro, timeout=30)
    con.row_factory = sqlite3.Row
    try:
        if not ro:
            n, tot = refresh(con, fill=True)
            print("FILL S803: %d finding(s) noted as 'before this page' (%d in all); the page began %s" % (n, tot, setting(con, "billchange.since", "?")))
        B = build(con, paper=True)
        fs = B["findings"]
        kinds = {}
        for f in fs:
            kinds[f["kind"]] = kinds.get(f["kind"], 0) + 1
        print("SHOW S803: counted %d (%s) · settled by the paper %d · no paper %d · for the record %d · part lists set aside %d · paper side %s"
              % (len(fs), ", ".join("%s %d" % kv for kv in sorted(kinds.items())) or "none", sum(1 for f in fs if f["status"] == "settled"),
                 sum(1 for f in fs if (f.get("paper") or {}).get("state") == "no_paper"), len(B["record"]), len(B["parts"]),
                 "read" if B["paper_ok"] else "NOT read (%s)" % B["paper_why"]))
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
