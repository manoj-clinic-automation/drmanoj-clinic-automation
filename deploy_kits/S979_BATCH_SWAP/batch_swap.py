#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch_swap.py -- S979 (Sanjeevni, session 546).  THE BATCH SWAP (D1113; F-1752; mock-up v7, final, 28-Nov-2026).

THE PROBLEM.  The Expiry watch's Near expiry list shows only the expiring batch.  When the same item also holds a NEWER batch, the
expiring batch exists only on paper in nearly all cases (the owner, 15:31): the counter sells the newer batch while Marg keeps the stock
on the old one, and the old batch would expire in Marg as a false loss.

THE FLOW (his rulings 15:28-17:40, D1113).
  * A CASE: a near-expiry batch (expiry_watch's own rule) with stock and NO sale since the last Batch Stock export, while another batch of
    the same item with a LATER expiry has stock (a batch printed two ways -- the same letters and digits -- is never a partner).  Found
    every time the watch runs (the nightly 23:57, and the daytime runs), from the run's own stock_batch_now.  One row a batch, ever:
    expiry_swap_case (k20, old batch).  Every write is audited (audit_log, table expiry_swap_case).
  * DARPAN reconfirms the shelf on his Stock milaan page (/finance/stockmatch), with one push a day from swap.push_at (08:30):
      Nahi hai  -> the swap, the whole paper quantity;
      Hai, N    -> those N are real, NEVER swapped; the batch stays on Near expiry as listed today, marked "Darpan found it"; only a
                   missing part is swapped (N >= the paper quantity: nothing to swap, state 'shelf');
      no answer by swap.answer_by (13:00) on the day he was first asked -> the bills are shown anyway (paper is the norm), amber
                   "not reconfirmed" on the owner's list.
  * THE SWAP is Darpan's, in Marg, at the counter: Bill 1 SALE named STOCK holding every item on its OLD batch, Bill 2 SALE RETURN named
    STOCK, the same items on the NEWER batch at the same rate.  "Dono bill bana diye" records his tap; it closes nothing.
  * CLOSED BY THE SALE REPORT (mi_sale_line, the batch on every line): the sale of exactly the swap quantity on the old batch and the
    return of the same quantity on the newer batch, both on or after the day the case was found.  One half seen and a later day's report
    without the other -> red ("half"), Darpan told the next morning.
  * RED (one push to the owner, once a reason): the last selling day within swap.red_days (2) and the sale not yet seen ("late"); one half
    missing ("half"); the last selling day passed unswapped ("missed" -- Marg blocks the batch; it shows as expired).
  * THE OWNER: a collapsed "Batch swaps" section above Near expiry on /finance/sanjeevni/expiry (owner_section), a Needs-you line
    (needs_you), the near-expiry mark (near_marks).  Amir, vouchers and extra exports are OUT (D1113).

ENTRY POINTS
  after_run(con, rid, today, sp, alias, log)   expiry_watch.run calls it after stock_batch_now is written (judge, find, missed; no push)
  tick(db)                                     the cron (# S979_BATCH_SWAP, every 10 min 08-21 IST): judge, missed, the pushes
  darpan_view(con) / answer(...) / bills_made(...)   Darpan's card (stockmatch.py)
  owner_section(con, today) / near_marks(con) / needs_you(con, today)   the owner's page (expiry_watch.py)
  Nothing here opens the database at import (F-1722).

    /root/wa/venv/bin/python3 -B /root/finance/batch_swap.py tick        (what the cron does)
    /root/wa/venv/bin/python3 -B /root/finance/batch_swap.py find        (judge + find on the newest stock_batch_now, no push)
    /root/wa/venv/bin/python3 -B /root/finance/batch_swap.py show        (read only: the cases, item names and figures)
OFF: /root/finance/_off/ALL_OFF, /root/finance/spine/OFF, /root/finance/_off/S979_OFF, or setting swap.on = 0.
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import sqlite3
import sys
import time

KIT = "S979_BATCH_SWAP"
VERSION = "1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
DB_DEFAULT = os.environ.get("FINANCE_DB", os.path.join(HERE, "finance.db"))
SPINE_DEFAULT = os.path.join(HERE, "spine", "spine.db")
OFF_FLAGS = (os.path.join(HERE, "_off", "ALL_OFF"), os.path.join(HERE, "spine", "OFF"), os.path.join(HERE, "_off", "S979_OFF"))
PAGE_OWNER = "/finance/sanjeevni/expiry"
PAGE_DARPAN = "/finance/stockmatch"
TABLE = "expiry_swap_case"
MON = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
HOURS = (8, 21)                                               # pushes only inside shop hours, IST

SETTINGS = {
    "swap.on": ("1", "S979: the batch swap (1 on, 0 off)"),
    "swap.push_to": ("darpan", "S979: who gets the shelf / STOCK-bill push (logins, comma-separated)"),
    "swap.owner_push_to": ("manoj", "S979: who gets the red push (logins, comma-separated)"),
    "swap.push_at": ("08:30", "S979: the day's push to Darpan from this time (IST)"),
    "swap.answer_by": ("13:00", "S979: no shelf answer by this time on the day he was asked -> the bills are shown anyway"),
    "swap.red_days": ("2", "S979: red when the last selling day is this many days away and the sale bill is not in Marg"),
}

DDL = ("""CREATE TABLE IF NOT EXISTS expiry_swap_case (
    id INTEGER PRIMARY KEY, k20 TEXT NOT NULL, item TEXT, old_batch TEXT NOT NULL, old_key TEXT NOT NULL, old_expiry TEXT, last_sell TEXT,
    paper_units INTEGER, pack INTEGER, packing TEXT, new_batch TEXT, new_key TEXT, new_expiry TEXT, new_units INTEGER,
    found_at TEXT NOT NULL, found_run INTEGER, seen_at TEXT, seen_run INTEGER, asked_at TEXT, pushed_darpan TEXT,
    answer TEXT, answer_n INTEGER, answer_at TEXT, answer_by TEXT, swap_units INTEGER,
    bills_at TEXT, bills_by TEXT, sale_date TEXT, sale_bill TEXT, sale_p INTEGER, ret_date TEXT, ret_bill TEXT, ret_p INTEGER,
    closed_at TEXT, state TEXT NOT NULL DEFAULT 'open', red_reason TEXT, red_pushed TEXT, note TEXT,
    UNIQUE (k20, old_key))""",
       "CREATE INDEX IF NOT EXISTS ix_expiry_swap_case_state ON expiry_swap_case (state)")


# ---------------------------------------------------------------------------------------------------------------- small helpers
def now_ist():
    return dt.datetime.now(IST).replace(tzinfo=None, microsecond=0)


def iso(t):
    return t.replace(microsecond=0).isoformat()


def K(n):
    """The spine's 20-character key (spine_read.K, expiry_watch.K)."""
    return re.sub(r'\s+', ' ', (n or "").strip())[:20].strip()


def nbatch(b):
    s = str(b if b is not None else "").strip().upper()
    if re.match(r'^\d+\.0$', s):
        s = s[:-2]
    return s


def bkey(b):
    """A batch's letters and digits (expiry_watch._s693_alnum): 'C-1255' and 'C1255' are one batch."""
    return re.sub(r'[^A-Z0-9]', '', nbatch(b))


def _same_batch(x, key):
    return bool(x) and bool(key) and (x == key or (len(x) >= 4 and len(key) >= 4 and (x.endswith(key) or key.endswith(x))))


def fits(printed, key, other=""):
    """A sale line's printed batch is the case's batch (`key`), not its partner (`other`): the same letters and digits, or one ends with the
    other (4+ characters) while it does not fit the partner the same way."""
    x = bkey(printed)
    if not x or not key:
        return False
    if x == key:
        return True
    if other and (x == other or _same_batch(x, other)):
        return False
    return _same_batch(x, key)


def pack_of(packing):
    m = re.match(r'^\s*(\d+)\s*\*\s*(\d+)', packing or "")
    return int(m.group(2)) if m and int(m.group(2)) > 0 else 1


def qty_txt(units, pack):
    """Strips:tabs for a strip item, a plain count otherwise (the owner's convention)."""
    units = int(round(units or 0))
    if (pack or 1) <= 1:
        return str(units)
    s = "-" if units < 0 else ""
    u = abs(units)
    return "%s%d:%d" % (s, u // pack, u % pack)


def qty_hi(units, pack):
    """Darpan's words: '8 goli', '2 patte 3 goli', '1 nag'."""
    units = int(round(units or 0))
    if (pack or 1) <= 1:
        return "%d nag" % units
    p, g = divmod(units, pack)
    if not p:
        return "%d goli" % g
    return ("%d patte" % p) + ((" %d goli" % g) if g else "")


def _whole(con, item):
    """S976 (F-1742): a whole-unit item (one bottle, one tube) is counted whole on Darpan's screen; fail-soft False."""
    try:
        import stock_watch as _SW                               # noqa: PLC0415 -- beside this file
        return bool(_SW._s976_whole(con, item))
    except Exception:                                         # noqa: BLE001
        return False


def disp(con, c, units, hindi=False):
    """A case's quantity in words: strips:tabs (owner) / patte-goli (Darpan); a pack-1 item (a whole-unit item is found at pack 1) a count."""
    pack = int(c.get("pack") or 1)
    return qty_hi(units, pack) if hindi else qty_txt(units, pack)


def last_sell_day(exp_ym):
    return dt.date(int(exp_ym[:4]), int(exp_ym[5:7]), 1) - dt.timedelta(days=1)


def mon_yy(exp_ym):
    return "%s-%s" % (MON[int(exp_ym[5:7])], exp_ym[2:4]) if exp_ym else ""


def dm(isoday):
    """'2026-11-30' -> '30-11'."""
    return "%s-%s" % (isoday[8:10], isoday[5:7]) if isoday and len(isoday) >= 10 else ""


def hm(ts):
    return ts[11:16] if ts and len(ts) >= 16 else ""


def dmon(isoday):
    if not isoday:
        return ""
    d = dt.date.fromisoformat(isoday[:10])
    return "%d-%s" % (d.day, MON[d.month])


def esc(v):
    return html.escape(str(v if v is not None else ""), quote=True)


def _has(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?", (name,)).fetchone() is not None


def setting(con, key):
    d = SETTINGS[key][0]
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
    except sqlite3.Error:
        r = None
    return str(r[0]).strip() if r and r[0] not in (None, "") else d


def _int_setting(con, key):
    try:
        return int(float(setting(con, key)))
    except ValueError:
        return int(SETTINGS[key][0])


def _hhmm(con, key):
    m = re.match(r'^\s*(\d{1,2}):(\d{2})\s*$', setting(con, key))
    if not m:
        m = re.match(r'^\s*(\d{1,2}):(\d{2})\s*$', SETTINGS[key][0])
    return int(m.group(1)), int(m.group(2))


def near_days(con):
    try:
        r = con.execute("SELECT value FROM setting WHERE key='expiry.near_days'").fetchone()
        return int(float(r[0])) if r and r[0] not in (None, "") else 90
    except (sqlite3.Error, ValueError):
        return 90


def switched_off(con=None):
    if any(os.path.exists(f) for f in OFF_FLAGS):
        return True
    if con is not None:
        try:
            return setting(con, "swap.on") in ("0", "off", "no")
        except sqlite3.Error:
            return False
    return False


def ensure(con):
    for ddl in DDL:
        con.execute(ddl)
    if _has(con, "setting"):
        for k, (v, note) in SETTINGS.items():
            con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, note))


def _audit(con, action, row_id, after, who):
    try:
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                    (TABLE, int(row_id or 0), action, None, json.dumps(after, sort_keys=True, default=str), who or "system", iso(now_ist())))
    except sqlite3.Error:
        pass


def _rows(con, where="1=1", args=()):
    cur = con.execute("SELECT * FROM %s WHERE %s ORDER BY item, old_expiry, id" % (TABLE, where), args)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, tuple(r))) for r in cur.fetchall()]       # the caller's row_factory is never touched


# ---------------------------------------------------------------------------------------------------------------- the finder
def candidates(con, today):
    """The cases the newest stock_batch_now holds: [dict(k20, item, old*, new*, paper_units, pack, packing, run_id)]."""
    if not _has(con, "stock_batch_now"):
        return []
    cur = con.execute("SELECT * FROM stock_batch_now ORDER BY k20, expiry, batch")
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, tuple(r))) for r in cur.fetchall()]
    this_m = today.strftime("%Y-%m")
    nd = near_days(con)
    by = {}
    for r in rows:
        by.setdefault(r["k20"], []).append(r)
    out = []
    for k, bs in by.items():
        for b in bs:
            e = b.get("expiry") or ""
            if (b.get("units") or 0) <= 0 or not re.match(r'^\d{4}-\d{2}$', e) or e <= this_m:
                continue
            if (last_sell_day(e) - today).days > nd:
                continue
            if int(b.get("sold") or 0) != 0:
                continue                                      # it sold since the export: real stock
            ok_ = bkey(b.get("batch"))
            if not ok_:
                continue
            ps = [o for o in bs if o is not b and (o.get("units") or 0) > 0 and re.match(r'^\d{4}-\d{2}$', o.get("expiry") or "")
                  and (o.get("expiry") or "") > e and bkey(o.get("batch")) and not _same_batch(bkey(o.get("batch")), ok_)]
            if not ps:
                continue
            def _paper(o):                                    # a partner itself near expiry and unsold is likely paper too: last choice
                return int(int(o.get("sold") or 0) == 0 and (last_sell_day(o["expiry"]) - today).days <= nd)
            p = sorted(ps, key=lambda o: (_paper(o), -(o.get("sold") or 0), -(o.get("units") or 0), o.get("expiry") or ""))[0]
            pk = int(b.get("pack") or 1)
            if pk > 1 and _whole(con, b.get("item") or k):
                pk = 1                                        # S976 (F-1742): a whole-unit item's Batch Stock figure is whole pieces (CCM: 2 = 2 bottles)
            out.append(dict(k20=k, item=b.get("item") or k, old_batch=nbatch(b.get("batch")), old_key=ok_, old_expiry=e,
                            last_sell=last_sell_day(e).isoformat(), paper_units=int(b["units"]), pack=pk,
                            packing=b.get("packing") or "", new_batch=nbatch(p.get("batch")), new_key=bkey(p.get("batch")),
                            new_expiry=p.get("expiry") or "", new_units=int(p.get("units") or 0), run_id=b.get("run_id")))
    return out


def _untouched(c):
    return not c.get("bills_at") and not c.get("sale_date") and not c.get("ret_date")


def _swap_of(paper, answer, n):
    if answer == "hai":
        return max(0, int(paper or 0) - int(n or 0))
    return int(paper or 0)


def find(con, today=None, now=None):
    """Insert the new cases, refresh the untouched open ones, mark 'gone' an untouched open case the newest list no longer holds.
    -> dict(new, refreshed, gone, reopened)."""
    now = now or now_ist()
    today = today or now.date()
    ensure(con)
    got = candidates(con, today)
    have = {(c["k20"], c["old_key"]): c for c in _rows(con)}
    st = dict(new=0, refreshed=0, gone=0, reopened=0)
    seen = set()
    at = iso(now)
    for x in got:
        kk = (x["k20"], x["old_key"])
        seen.add(kk)
        c = have.get(kk)
        if c is None:
            cur = con.execute("INSERT INTO %s (k20, item, old_batch, old_key, old_expiry, last_sell, paper_units, pack, packing, new_batch, "
                              "new_key, new_expiry, new_units, found_at, found_run, seen_at, seen_run, swap_units, state) "
                              "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'open')" % TABLE,
                              (x["k20"], x["item"], x["old_batch"], x["old_key"], x["old_expiry"], x["last_sell"], x["paper_units"], x["pack"],
                               x["packing"], x["new_batch"], x["new_key"], x["new_expiry"], x["new_units"], at, x["run_id"], at, x["run_id"],
                               x["paper_units"]))
            _audit(con, "s979_found", cur.lastrowid, dict(x, kit=KIT), "system")
            st["new"] += 1
            continue
        if c["state"] == "gone":
            con.execute("UPDATE %s SET state='open', paper_units=?, swap_units=?, new_batch=?, new_key=?, new_expiry=?, new_units=?, seen_at=?, "
                        "seen_run=?, answer=NULL, answer_n=NULL, answer_at=NULL, answer_by=NULL, asked_at=NULL, pushed_darpan=NULL, "
                        "red_reason=NULL, note=? WHERE id=?" % TABLE,
                        (x["paper_units"], x["paper_units"], x["new_batch"], x["new_key"], x["new_expiry"], x["new_units"], at, x["run_id"],
                         "on paper again " + at[:16], c["id"]))
            _audit(con, "s979_reopened", c["id"], dict(x, kit=KIT), "system")
            st["reopened"] += 1
            continue
        if c["state"] == "open" and _untouched(c):
            ch = {}
            if int(c["paper_units"] or 0) != x["paper_units"]:
                ch["paper_units"] = x["paper_units"]
            if not c.get("answer") and (c["new_key"] != x["new_key"]):
                ch.update(new_batch=x["new_batch"], new_key=x["new_key"], new_expiry=x["new_expiry"])
            ch["new_units"] = x["new_units"]
            paper = ch.get("paper_units", c["paper_units"])
            sw = _swap_of(paper, c.get("answer"), c.get("answer_n"))
            if c.get("answer") == "hai" and sw <= 0:
                ch["state"] = "shelf"
            ch["swap_units"] = sw
            ch.update(seen_at=at, seen_run=x["run_id"])
            con.execute("UPDATE %s SET %s WHERE id=?" % (TABLE, ", ".join("%s=?" % k for k in ch)), tuple(ch.values()) + (c["id"],))
            if "paper_units" in ch or "new_key" in ch:
                _audit(con, "s979_refreshed", c["id"], ch, "system")
                st["refreshed"] += 1
        else:
            con.execute("UPDATE %s SET seen_at=?, seen_run=? WHERE id=?" % TABLE, (at, x["run_id"], c["id"]))
    for kk, c in have.items():
        if kk in seen or c["state"] != "open" or not _untouched(c):
            continue
        if c.get("last_sell") and today.isoformat() > c["last_sell"]:
            continue                                          # its last selling day has passed: missed() decides once that day's report is in
        con.execute("UPDATE %s SET state='gone', note=? WHERE id=?" % TABLE, ("not on paper in the list of " + at[:16], c["id"]))
        _audit(con, "s979_gone", c["id"], dict(item=c["item"], batch=c["old_batch"]), "system")
        st["gone"] += 1
    return st


# ---------------------------------------------------------------------------------------------------------------- the judge
def _alias(spine_path=SPINE_DEFAULT):
    try:
        sp = sqlite3.connect("file:%s?mode=ro" % spine_path, uri=True, timeout=10)
        try:
            return {r[0]: r[1] for r in sp.execute("SELECT alias, k20 FROM sp_alias")}
        finally:
            sp.close()
    except sqlite3.Error:
        return {}


def line_units(qs, ql, raw, pack):
    if qs is not None or ql is not None:
        return int(qs or 0) * int(pack or 1) + int(ql or 0)
    try:
        return int(round(float(str(raw or "0").replace(",", ""))))
    except ValueError:
        return None


def judge(con, alias=None, now=None):
    """Close the open cases whose two halves the sale report shows. -> dict(closed, half, newest_day)."""
    now = now or now_ist()
    ensure(con)
    alias = alias if alias is not None else {}
    out = dict(closed=0, half=0, newest_day=None)
    if not _has(con, "mi_sale_line"):
        return out
    cases = [c for c in _rows(con, "state='open' AND COALESCE(swap_units,0)>0")]
    newest = con.execute("SELECT MAX(bill_date) FROM mi_sale_line").fetchone()[0]
    out["newest_day"] = newest
    if not cases:
        return out
    since = min(c["found_at"][:10] for c in cases)
    lines = con.execute("SELECT DISTINCT bill_date, bill_no, is_return, seq, item_name, pack, qty_raw, qty_strips, qty_loose, amount_p, batch "
                        "FROM mi_sale_line WHERE bill_date >= ? ORDER BY bill_date, bill_no, seq", (since,)).fetchall()
    lines = [tuple(r) for r in lines]
    by_k = {}
    for ln in lines:
        k = K(ln[4])
        k = alias.get(k, k)
        by_k.setdefault(k, []).append(ln)
    used = set()
    at = iso(now)
    for c in cases:
        day0 = c["found_at"][:10]
        sw = int(c["swap_units"] or 0)
        sales, rets = [], []
        for ln in by_k.get(c["k20"], []):
            if ln[0] < day0 or ln in used:
                continue
            if line_units(ln[7], ln[8], ln[6], c["pack"]) != sw:
                continue
            if not ln[2] and fits(ln[10], c["old_key"], c["new_key"]):
                sales.append(ln)
            elif ln[2] and fits(ln[10], c["new_key"], c["old_key"]):
                rets.append(ln)
        sale, ret = None, None
        tap = (c.get("bills_at") or "")[:10]
        if not c.get("sale_date") and not c.get("ret_date"):
            days = sorted({x[0] for x in sales} & {x[0] for x in rets})
            if days:                                          # his two STOCK bills: a sale and a return of the swap, the same day
                sale = [x for x in sales if x[0] == days[0]][0]
                ret = [x for x in rets if x[0] == days[0]][0]
            elif tap:                                         # he said he made them: either bill since the case was found counts
                sale = sales[0] if sales else None
                ret = rets[0] if rets else None
            elif sales and (c.get("answer") or (_cutoff(con, c) and sales[0][0] >= _cutoff(con, c).date().isoformat())):
                # no tap, but he answered the shelf (or the bills were on his card): a sale of exactly the paper quantity on the paper batch is his
                sale = sales[0]                               # STOCK sale (a lone return could be any customer's -- never counted alone)
                ret = rets[0] if rets else None               # with his sale in, a matching return since the found day is his other bill
        elif c.get("sale_date") and not c.get("ret_date"):
            ret = rets[0] if rets else None                   # the other half from the found day on (his return may come first)
        elif c.get("ret_date") and not c.get("sale_date"):
            sale = sales[0] if sales else None
        ch = {}
        if sale is not None:
            used.add(sale)
            ch.update(sale_date=sale[0], sale_bill=str(sale[1]), sale_p=int(sale[9] or 0))
        if ret is not None:
            used.add(ret)
            ch.update(ret_date=ret[0], ret_bill=str(ret[1]), ret_p=int(ret[9] or 0))
        has_sale = bool(ch.get("sale_date") or c.get("sale_date"))
        has_ret = bool(ch.get("ret_date") or c.get("ret_date"))
        if has_sale and has_ret:
            ch.update(closed_at=at, state="closed", red_reason=None)
            out["closed"] += 1
        elif has_sale or has_ret:
            out["half"] += 1
        if not ch and tap and not has_sale and not has_ret and not sales and not rets and newest and newest > tap:
            ch.update(bills_at=None, bills_by=None, note="'bana diye' %s, but that day's sale report holds neither STOCK bill" % tap)
            out["unseen"] = out.get("unseen", 0) + 1
        if ch:
            con.execute("UPDATE %s SET %s WHERE id=?" % (TABLE, ", ".join("%s=?" % k for k in ch)), tuple(ch.values()) + (c["id"],))
            _audit(con, "s979_closed" if ch.get("state") == "closed" else ("s979_bills_unseen" if "bills_at" in ch else "s979_half"), c["id"], ch, "system")
    return out


def missed(con, today=None):
    """An open case whose last selling day has passed without the sale bill, judged only once that day's sale report is in (it comes the
    next morning): Marg blocks the batch now (state 'missed')."""
    today = today or now_ist().date()
    nd = _newest_day(con) or ""
    n = 0
    for c in _rows(con, "state='open'"):
        if c["last_sell"] and today.isoformat() > c["last_sell"] and nd >= c["last_sell"] and not c.get("sale_date"):
            con.execute("UPDATE %s SET state='missed', note=? WHERE id=?" % TABLE, ("last selling day %s passed unswapped" % c["last_sell"], c["id"]))
            _audit(con, "s979_missed", c["id"], dict(item=c["item"], batch=c["old_batch"], last_sell=c["last_sell"]), "system")
            n += 1
    return n


def after_run(con, rid=None, today=None, sp=None, alias=None, log=print):
    """expiry_watch.run, after stock_batch_now: judge, find, missed -- inside the caller's transaction; never a push."""
    if switched_off(con):
        return dict(off=True)
    ensure(con)
    j = judge(con, alias if alias is not None else {})
    m = missed(con, today)                                    # before find: on the 1st the batch leaves the near list -- it is missed, not gone
    f = find(con, today)
    log("batch_swap %s: run %s · found new %d, refreshed %d, gone %d, reopened %d · closed %d, half %d · missed %d"
        % (KIT, rid, f["new"], f["refreshed"], f["gone"], f["reopened"], j["closed"], j["half"], m))
    return dict(j, **f, missed=m)


# ---------------------------------------------------------------------------------------------------------------- the reading
def _cutoff(con, c):
    """The time after which the bills are shown without his answer: swap.answer_by on the day he was first asked (or the next day when
    he was first asked after it)."""
    if not c.get("asked_at"):
        return None
    t = dt.datetime.fromisoformat(c["asked_at"][:19])
    h, m = _hhmm(con, "swap.answer_by")
    cut = t.replace(hour=h, minute=m, second=0)
    return cut if t < cut else cut + dt.timedelta(days=1)


def to_bill(con, c, now=None):
    """The case belongs on Darpan's two bills now."""
    now = now or now_ist()
    if c["state"] != "open" or int(c.get("swap_units") or 0) <= 0 or not _untouched(c):
        return False
    if c.get("answer") in ("nahi", "hai"):
        return True
    cut = _cutoff(con, c)
    return bool(cut and now >= cut)


def half_of(c, newest_day=None):
    """'ret' when the sale is in Marg and the return is not; 'sale' the other way; None otherwise.  The day's sale report comes whole
    the next morning (SALE_BILLWISE, one a day), so a half seen in it is a half made."""
    if c["state"] != "open":
        return None
    if c.get("sale_date") and not c.get("ret_date"):
        return "ret"
    if c.get("ret_date") and not c.get("sale_date"):
        return "sale"
    return None


def red_of(con, c, today, newest_day):
    if c["state"] == "missed":
        return "missed"
    if c["state"] != "open":
        return None
    if half_of(c, newest_day):
        return "half"
    if int(c.get("swap_units") or 0) > 0 and not c.get("sale_date") and not c.get("bills_at") and c.get("last_sell"):
        if (dt.date.fromisoformat(c["last_sell"]) - today).days <= _int_setting(con, "swap.red_days"):
            return "late"
    return None


def _newest_day(con):
    try:
        return con.execute("SELECT MAX(bill_date) FROM mi_sale_line").fetchone()[0] if _has(con, "mi_sale_line") else None
    except sqlite3.Error:
        return None


def darpan_view(con, now=None):
    """Darpan's card: the shelf questions, the two bills, a half-made pair. Read only."""
    now = now or now_ist()
    try:
        if not _has(con, TABLE):
            return dict(ok=True, ask=[], bills=None, half=[], made=[])
        nd = _newest_day(con)
        ask, sale, ret, ids, half, made = [], [], [], [], [], []
        for c in _rows(con, "state='open'"):
            line = dict(id=c["id"], item=c["item"], pack=int(c["pack"] or 1), old_batch=c["old_batch"], old_exp=mon_yy(c["old_expiry"]),
                        new_batch=c["new_batch"], new_exp=mon_yy(c["new_expiry"]), paper_hi=disp(con, c, c["paper_units"], True),
                        swap_hi=disp(con, c, c["swap_units"], True), last_sell=dm(c["last_sell"]))
            h = half_of(c, nd)
            if h:
                half.append(dict(line, missing=h))
                continue
            if not c.get("answer") and _untouched(c):
                ask.append(line)
            if to_bill(con, c, now):
                sale.append(line)
                ret.append(line)
                ids.append(c["id"])
            elif c.get("bills_at") and not c.get("closed_at"):
                made.append(dict(line, at=hm(c["bills_at"])))
        bills = dict(ids=ids, sale=sale, ret=ret) if ids else None
        return dict(ok=True, ask=ask, bills=bills, half=half, made=made, kit=KIT)
    except sqlite3.Error as ex:
        return dict(ok=False, error=type(ex).__name__)


def _qty(q, pack):
    """His boxes -> tablets / pieces: {strips, loose} on a strip item (his patte / goli boxes), {pcs} on a pack-1 item.
    None when nothing was typed or a box is not a number."""
    q = q or {}
    try:
        if q.get("pcs") not in (None, ""):
            return int(float(q.get("pcs")))
        if q.get("strips") in (None, "") and q.get("loose") in (None, ""):
            return None
        return int(float(q.get("strips") or 0)) * pack + int(float(q.get("loose") or 0))
    except (TypeError, ValueError):
        return None


def answer(con, cid, ans, qty, who):
    """Darpan's shelf answer: 'nahi' (not there) or 'hai' with what he counted ({strips, loose} or {pcs}). -> (ok, message, code)."""
    ensure(con)
    rs = _rows(con, "id=?", (int(cid),))
    if not rs:
        return False, "Yeh item nahi mila.", 404
    c = rs[0]
    if c["state"] != "open" or not _untouched(c):
        return False, "Is item ka kaam ho chuka hai.", 409
    if ans not in ("nahi", "hai"):
        return False, "Nahi hai ya Hai chuniye.", 400
    n = 0
    if ans == "hai":
        n = _qty(qty, int(c["pack"] or 1)) or 0
        if n <= 0:
            return False, "Kitni goli / nag shelf par hai, likhiye.", 400
    if c.get("answer") == ans and int(c.get("answer_n") or 0) == n:
        return True, "%s: pehle hi likha hai." % c["item"], 200    # a repeat tap writes nothing (S393)
    sw = _swap_of(c["paper_units"], ans, n)
    state = "shelf" if (ans == "hai" and sw <= 0) else "open"
    at = iso(now_ist())
    con.execute("UPDATE %s SET answer=?, answer_n=?, answer_at=?, answer_by=?, swap_units=?, state=? WHERE id=?" % TABLE,
                (ans, n, at, who or "", sw, state, c["id"]))
    _audit(con, "s979_answer", c["id"], dict(answer=ans, n=n, swap_units=sw, state=state), who)
    con.commit()
    if ans == "nahi":
        return True, "%s: shelf par nahi -- Batch badlo card mein dekhiye." % c["item"], 200
    if state == "shelf":
        return True, "%s: shelf par %s -- batch nahi badlega." % (c["item"], disp(con, c, n, True)), 200
    return True, "%s: shelf par %s -- baaki %s ka batch badlega." % (c["item"], disp(con, c, n, True), disp(con, c, sw, True)), 200


def bills_made(con, ids, who, now=None):
    """'Dono bill bana diye': records his tap on the cases of the card; it closes nothing. -> (ok, message, code)."""
    ensure(con)
    now = now or now_ist()
    want = set()
    for i in ids or []:
        try:
            want.add(int(i))
        except (TypeError, ValueError):
            pass
    done = []
    for c in _rows(con, "state='open'"):
        if c["id"] in want and to_bill(con, c, now):
            con.execute("UPDATE %s SET bills_at=?, bills_by=? WHERE id=?" % TABLE, (iso(now), who or "", c["id"]))
            _audit(con, "s979_bills", c["id"], dict(item=c["item"], swap_units=c["swap_units"]), who)
            done.append(c["item"])
    con.commit()
    if not done:
        return False, "Card badal gaya hai -- page dobara kholiye.", 409
    return True, "Likh liya: %d item. Kal subah ki sale report se band hoga." % len(done), 200


# ---------------------------------------------------------------------------------------------------------------- the pushes
def _push(con, to_key, title, body, url, tag):
    """One Web Push per login (order_rules._push; ORDER_PUSH_STUB for a walk). -> (sent, failed). Fail-soft."""
    to = [x.strip().lower() for x in setting(con, to_key).split(",") if x.strip()]
    sent = failed = 0
    try:
        import order_rules as _OR                              # noqa: PLC0415 -- beside this file
    except Exception:                                         # noqa: BLE001
        return 0, len(to)
    payload = dict(kind="count", title=title, body=body, url=url, tag=tag, ttl=21600, renotify=True, ts=int(time.time() * 1000))
    for u in to:
        try:
            s, f = _OR._push(u, payload)
            sent += int(s or 0)
            failed += int(f or 0)
        except Exception:                                     # noqa: BLE001
            failed += 1
    _audit(con, "s979_push", 0, dict(to=to, title=title, body=body, sent=sent, failed=failed), "system")
    return sent, failed


def tick(db=DB_DEFAULT, spine_path=SPINE_DEFAULT, now=None, log=print):
    """The cron: judge, missed, the pushes (inside shop hours only). Never raises."""
    now = now or now_ist()
    try:
        con = sqlite3.connect(db, timeout=60)
    except sqlite3.Error as ex:
        log("batch_swap %s: no database (%s)" % (KIT, ex))
        return 1
    try:
        if switched_off(con):
            log("batch_swap %s: switched off" % KIT)
            return 0
        with con:
            ensure(con)
            j = judge(con, _alias(spine_path), now)
            m = missed(con, now.date())
        res = dict(closed=j["closed"], half=j["half"], missed=m, darpan=0, owner=0)
        if HOURS[0] <= now.hour < HOURS[1]:
            res["owner"] = _owner_reds(con, now)
            h, mi = _hhmm(con, "swap.push_at")
            if (now.hour, now.minute) >= (h, mi):
                res["darpan"] = _darpan_push(con, now)
        log("batch_swap %s tick %s: closed %d, half %d, missed %d · pushed Darpan %d item(s), owner %d"
            % (KIT, iso(now)[:16], res["closed"], res["half"], res["missed"], res["darpan"], res["owner"]))
        return 0
    except Exception as ex:                                   # noqa: BLE001
        log("batch_swap %s tick failed: %s: %s" % (KIT, type(ex).__name__, str(ex)[:160]))
        return 1
    finally:
        con.close()


def _darpan_push(con, now):
    """Once a day from swap.push_at: one push naming what waits for Darpan (a new case the same day at the next tick)."""
    today = now.date().isoformat()
    nd = _newest_day(con)
    ask, bill, half, ids = [], [], [], []
    for c in _rows(con, "state='open'"):
        if (c.get("pushed_darpan") or "")[:10] == today:
            continue
        h = half_of(c, nd)
        if h:
            half.append(c["item"])
        elif not c.get("answer") and _untouched(c):
            ask.append(c["item"])
        elif to_bill(con, c, now):
            bill.append(c["item"])
        else:
            continue
        ids.append(c["id"])
    if not ids:
        return 0
    bits = []
    if ask:
        bits.append("%d purane batch shelf par dekhiye -- %s" % (len(ask), ", ".join(ask[:5])))
    if bill:
        bits.append("Batch badlo: %d item ke 2 STOCK bill banaiye" % len(bill))
    if half:
        bits.append("STOCK bill adhoora: %s" % ", ".join(half[:4]))
    with con:
        _push(con, "swap.push_to", "Sanjeevni - batch", " · ".join(bits), PAGE_DARPAN, "swap")
        at = iso(now)
        for i in ids:
            con.execute("UPDATE %s SET pushed_darpan=?, asked_at=COALESCE(asked_at, ?) WHERE id=?" % TABLE, (at, at, i))
    return len(ids)


RED_TEXT = {
    "late": "Batch swap late: %s -- last selling day %s, not yet in Marg",
    "half": "Batch swap half made: %s -- one of the two STOCK bills is missing in Marg",
    "missed": "Batch swap missed: %s -- the last selling day %s passed; Marg now blocks the batch",
}


def _owner_reds(con, now):
    """ONE push to the owner when cases turn red (each case once a reason); the newly red named in it."""
    today = now.date()
    nd = _newest_day(con)
    news = []
    with con:
        for c in _rows(con, "state IN ('open','missed')"):
            r = red_of(con, c, today, nd)
            if r != (c.get("red_reason") or None):
                con.execute("UPDATE %s SET red_reason=? WHERE id=?" % TABLE, (r, c["id"]))
            if r and (c.get("red_pushed") or "").split("@")[0] != r:
                news.append((c, r))
    if not news:
        return 0
    txts = [RED_TEXT[r] % ((c["item"], dm(c["last_sell"])) if r != "half" else (c["item"],)) for c, r in news]
    body = txts[0] if len(txts) == 1 else ("%d batch swaps red: " % len(txts)) + "; ".join(t.split(" -- ")[0].split(": ", 1)[-1] for t in txts[:6])
    with con:
        _push(con, "swap.owner_push_to", "Sanjeevni - batch swap", body, PAGE_OWNER, "swap-red")
        at = iso(now)
        for c, r in news:
            con.execute("UPDATE %s SET red_pushed=? WHERE id=?" % TABLE, ("%s@%s" % (r, at), c["id"]))
    return len(news)


# ---------------------------------------------------------------------------------------------------------------- the owner's page
STATE_TAG = {
    "late": ("red", "last selling day %s -- not in Marg"),
    "half": ("red", "one STOCK bill missing in Marg"),
    "missed": ("red", "missed -- Marg blocked the batch on %s"),
}


def _tag(cls, text):
    col = {"red": ("var(--red-soft)", "var(--red)"), "amb": ("var(--amber-soft)", "var(--amber)"), "grn": ("var(--accent-soft)", "var(--accent)"),
           "gry": ("var(--line)", "var(--muted)")}[cls]
    return ('<span style="display:inline-block;font-size:.72rem;padding:1px 7px;border-radius:999px;background:%s;color:%s;white-space:nowrap">%s</span>'
            % (col[0], col[1], esc(text)))


def _row_state(con, c, now, nd):
    r = red_of(con, c, now.date(), nd)
    if r == "late":
        return 0, _tag("red", "last selling day %s -- not in Marg" % dm(c["last_sell"]))
    if r == "half":
        return 0, _tag("red", "one STOCK bill missing in Marg (%s)" % ("the return" if half_of(c, nd) == "ret" else "the sale"))
    if r == "missed":
        return 0, _tag("red", "missed -- last selling day %s passed" % dm(c["last_sell"]))
    if c["state"] == "closed":
        return 4, _tag("grn", "closed %s" % dm((c.get("closed_at") or "")[:10]))
    if c["state"] == "shelf":
        return 3, _tag("gry", "on the shelf -- stays on Near expiry")
    if c["state"] == "gone":
        return 5, _tag("gry", "no longer on paper")
    if c.get("bills_at"):
        return 1, _tag("amb", "bills made -- waits for the next sale report")
    if not c.get("answer"):
        cut = _cutoff(con, c)
        if cut and now >= cut:
            return 1, _tag("amb", "not reconfirmed -- on his card to bill")
        return 2, _tag("amb", "waiting for Darpan's shelf check")
    return 1, _tag("amb", "on his card to bill")


def owner_section(con, today=None, now=None):
    """The collapsed 'Batch swaps' section above Near expiry (mock-up v7). '' when the table does not exist yet."""
    now = now or now_ist()
    today = today or now.date()
    try:
        if not _has(con, TABLE):
            return ""
        nd = _newest_day(con)
        month = today.strftime("%Y-%m")
        cs = [c for c in _rows(con) if c["state"] in ("open", "shelf", "missed")
              or ((c.get("closed_at") or c.get("seen_at") or c.get("found_at") or "")[:7] == month)]
        rows, n_open, n_red, n_closed = [], 0, 0, 0
        for c in cs:
            order, tag = _row_state(con, c, now, nd)
            if c["state"] == "open":
                n_open += 1
            if red_of(con, c, today, nd):
                n_red += 1
            if c["state"] == "closed" and (c.get("closed_at") or "")[:7] == month:
                n_closed += 1
            if c.get("answer") == "nahi":
                shelf = "not there · %s" % hm(c["answer_at"])
            elif c.get("answer") == "hai":
                shelf = "found %s · %s" % (disp(con, c, c["answer_n"]), hm(c["answer_at"]))
            else:
                shelf = "no answer" if c["state"] == "open" else "—"
            if c.get("sale_date") and c.get("ret_date"):
                marg = "both bills in Marg"
            elif c.get("sale_date") or c.get("ret_date"):
                marg = "sale in Marg" if c.get("sale_date") else "return in Marg"
            elif c.get("bills_at"):
                marg = "Bana diye · %s" % hm(c["bills_at"])
            elif c["state"] == "open" and to_bill(con, c, now):
                marg = "on his card"
            else:
                marg = "not yet" if c["state"] == "open" else "—"
            path = ["found %s %s" % (dmon(c["found_at"][:10]), hm(c["found_at"]))]
            if c.get("asked_at"):
                path.append("asked %s %s" % (dmon(c["asked_at"][:10]), hm(c["asked_at"])))
            if c.get("answer"):
                path.append("shelf: %s %s %s" % ("not there" if c["answer"] == "nahi" else "found " + disp(con, c, c["answer_n"]),
                                                 dmon(c["answer_at"][:10]), hm(c["answer_at"])))
            if c.get("bills_at"):
                path.append("bills made %s %s" % (dmon(c["bills_at"][:10]), hm(c["bills_at"])))
            if c.get("sale_date"):
                path.append("sale %s bill %s" % (dmon(c["sale_date"]), c.get("sale_bill") or ""))
            if c.get("ret_date"):
                path.append("return %s bill %s" % (dmon(c["ret_date"]), c.get("ret_bill") or ""))
            if c.get("closed_at"):
                path.append("closed %s" % dmon(c["closed_at"][:10]))
            if c.get("sale_p") and c.get("ret_p") and int(c["sale_p"]) != int(c["ret_p"]):
                path.append("the two bills' amounts differ (Rs %.2f / Rs %.2f)" % (int(c["sale_p"]) / 100.0, int(c["ret_p"]) / 100.0))
            rows.append((order, c["item"], (
                '<tr><td><b>%s</b><div class="note" style="margin:2px 0 0">%s</div></td><td class="m">%s · %s</td><td class="m n">%s</td>'
                '<td class="m">%s · %s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                % (esc(c["item"]), esc(" · ".join(path)), esc(c["old_batch"]), esc(mon_yy(c["old_expiry"])),
                   esc(disp(con, c, c["paper_units"])), esc(c["new_batch"]), esc(mon_yy(c["new_expiry"])), esc(shelf), esc(marg), tag))))
        rows.sort(key=lambda t: (t[0], t[1]))
        made = sum(1 for c in cs if c["state"] == "closed" and (c.get("closed_at") or "")[:7] == month)
        found = sum(1 for c in cs if c.get("answer") == "hai" and (c.get("answer_at") or "")[:7] == month)
        rupees = sum(int(c.get("sale_p") or 0) for c in cs if c["state"] == "closed" and (c.get("closed_at") or "")[:7] == month) / 100.0
        tbl = ('<div class="tbl"><table><thead><tr><th>Item</th><th>Expiring batch</th><th class="n">On paper</th><th>Swap into</th>'
               '<th>Darpan · shelf</th><th>Darpan · Marg</th><th>State</th></tr></thead><tbody>%s</tbody></table></div>'
               % "".join(r[2] for r in rows)) if rows else '<p class="note">None.</p>'
        return ('<details class="s979"><summary><h3>Batch swaps &middot; %d open &middot; %d closed this month &middot; %d red</h3>'
                '<span class="count%s">%d</span></summary>'
                '<p class="what">An expiring batch with no sale since the batch export, beside a newer batch of the same item: nearly always '
                'only on paper. Darpan checks the shelf, then makes two Marg bills named STOCK (a sale of the old batch, a sale return of the '
                'same quantity on the newer batch, same rate). The next sale report closes it. Stock is strips:tabs.</p>%s'
                '<p class="note">%s: %d swapped and closed (Rs %.2f on the STOCK bills) · %d found on the shelf.</p></details>'
                % (n_open, n_closed, n_red, " red" if n_red else (" amber" if n_open else ""), len(rows), tbl, MON[today.month], made, rupees, found))
    except sqlite3.Error:
        return ""


def near_marks(con):
    """{(k20, batch key): N units} -- Darpan's 'Hai, N' on a near batch, for the Near expiry mark."""
    try:
        if not _has(con, TABLE):
            return {}
        return {(c["k20"], c["old_key"]): int(c["answer_n"] or 0) for c in _rows(con, "answer='hai' AND state IN ('open','shelf')")}
    except sqlite3.Error:
        return {}


def needs_you(con, today=None):
    """One Needs-you line when a case is red."""
    today = today or now_ist().date()
    try:
        if not _has(con, TABLE):
            return []
        nd = _newest_day(con)
        red = [c["item"] for c in _rows(con, "state IN ('open','missed')") if red_of(con, c, today, nd)]
        if not red:
            return []
        return [dict(cls="warn", target="expiry", href=PAGE_OWNER,
                     text="Batch swaps: %d red -- %s" % (len(red), ", ".join(red[:4]) + (" ..." if len(red) > 4 else "")))]
    except sqlite3.Error:
        return []


# ---------------------------------------------------------------------------------------------------------------- command line
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("tick", "find", "show"))
    ap.add_argument("--db", default=DB_DEFAULT)
    ap.add_argument("--spine", default=SPINE_DEFAULT)
    a = ap.parse_args(argv)
    if a.cmd == "tick":
        return tick(a.db, a.spine)
    if a.cmd == "find":
        con = sqlite3.connect(a.db, timeout=60)
        try:
            if switched_off(con):
                print("batch_swap %s: switched off" % KIT)
                return 0
            with con:
                r = after_run(con, "by hand", None, None, _alias(a.spine))
            print(json.dumps(r, sort_keys=True))
            return 0
        finally:
            con.close()
    con = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
    try:
        if not _has(con, TABLE):
            print("no cases yet")
            return 0
        nd = _newest_day(con)
        for c in _rows(con):
            print("%-6s %-24s %-14s %s paper %-6s -> %-14s %s · answer %s · bills %s · sale %s · return %s · red %s"
                  % (c["state"], c["item"][:24], c["old_batch"], c["old_expiry"], qty_txt(c["paper_units"], c["pack"]), c["new_batch"],
                     c["new_expiry"], c.get("answer") or "-", "yes" if c.get("bills_at") else "no", c.get("sale_date") or "-",
                     c.get("ret_date") or "-", red_of(con, c, now_ist().date(), nd) or "-"))
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main())
