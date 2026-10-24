#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
expiry_watch.py -- S638 (Sanjeevni, session 348).  THE EXPIRY WATCH: expired, near expiry, dump, wrong batch, new products,
out of stock.  D771 (the plan of 23-Oct), D777 (the owner's additions), D780 (his "yes" to the mock-up, rev 3, 24-Oct 21:47 IST).

ONE MONTHLY INPUT, ONE NIGHTLY LIST, READ-ONLY.
  * The input is Marg's Batch Stock (Stocks -> Batch Stock, WHOLE store, saved as text) -- the only report that holds stock BY BATCH.
    The medical PC's reader converts it (marg_txt S638); the server's door files it by its own signature as BATCH_STOCK (never a
    closing stock, F-1008).  It is taken as the shop's batches only when it lists at least `expiry.whole_fraction` of the items the
    newest closing holds in stock (a filtered batch print -- Marg's batch-wise dump -- is kept, never used).
  * Between two exports the spine's own sale lines (batch and expiry on every line) lower each batch's figure; a sale against a
    batch beyond its stock, or against no batch, is a wrong-batch sale and is named the next morning.
  * Every night (spine/near_expiry.py, the cron line of S343, unchanged) the list is made again and written, whole, to two tables
    of finance.db: stock_expiry_run (one row a run) and stock_expiry_line (the newest run's lines; the older runs' lines are
    replaced -- a run is a fact of its night, the lines are its list).  Nothing else is written; no stock figure anywhere reads them.
  * The screens read the newest good run: the owner's page /finance/sanjeevni/expiry (English, six sections), Darpan's order tab
    (one block: the batches to sell first), Amir's Marg sudhar card (the expired batches to write off or return, the batches to
    correct, the monthly export card), the owner's Needs-you lines.

SECTIONS (each line carries item, batch, expiry, stock in strips:tabs):
  expired   a batch with stock whose expiry month has begun -- Marg will not sell it (Amir: write-off or return)
  near      a batch with stock whose last selling day (the day before its expiry month) is within expiry.near_days
  dump      an item with stock (expired batches left out) and no sale and no purchase in expiry.dump_days -- orthotics apart
  wrong     a medicine with a batch below zero beside a batch that has the stock; plus the month's sales with no batch
  new       a name Marg had never carried: first bought, or first in a closing (Amir's orthotic renames left out), or first in the
            monthly item list; the month open, earlier months folded
  oos       ordered, did not come, and the newest closing has none: waiting; and the first purchase after it: arrived again

SETTINGS (table setting, the owner changes them on his page): see SETTINGS below.

    /root/wa/venv/bin/python3 -B /root/finance/expiry_watch.py run [--date YYYY-MM-DD]     (what the nightly does)
    /root/wa/venv/bin/python3 -B /root/finance/expiry_watch.py read FILE.xls                (read one Batch Stock and print its witness)
    /root/wa/venv/bin/python3 -B /root/finance/expiry_watch.py show                         (the newest run, as text)
OFF: /root/finance/_off/ALL_OFF and /root/finance/spine/OFF (the spine's own switches) stop the nightly; the screens then show the
last run with its date.
"""
import argparse
import datetime as dt
import glob
import hashlib
import html
import json
import os
import re
import sqlite3
import sys

KIT = "S638_EXPIRY_WATCH"
VERSION = "1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
SPINE_DIR = os.path.join(HERE, "spine")
DB_DEFAULT = os.environ.get("FINANCE_DB", os.path.join(HERE, "finance.db"))
SPINE_DEFAULT = os.path.join(SPINE_DIR, "spine.db")
ARCHIVE_DEFAULT = os.path.join(os.environ.get("MARG_INGEST", "/root/marg_ingest"), "archive")
OFF_FLAGS = (os.path.join(SPINE_DIR, "OFF"), os.path.join(HERE, "_off", "ALL_OFF"))
PAGE = "/finance/sanjeevni/expiry"
MON = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# key: (default, what it is) -- the owner's rule of 26-Sep: every threshold is a setting he can alter on the screen
SETTINGS = {
    "expiry.near_days": ("90", "near expiry: the batch's last selling day falls within this many days"),
    "expiry.dump_days": ("60", "dump: no sale and no purchase for this many days"),
    "expiry.bold_strips": ("5", "dump, expiring soon: bold when this many strips or more are left"),
    "expiry.grey_strips": ("1", "dump, expiring soon: grey when fewer than this many strips are left"),
    "expiry.darpan_months": ("2", "Darpan's tab: the batches Marg stops selling within this many months"),
    "expiry.arrived_days": ("7", "out of stock: 'arrived again' stays this many days"),
    "expiry.whole_fraction": ("0.9", "a Batch Stock is the whole shop when it lists this share of the items the newest closing holds"),
    "expiry.export_due_day": ("7", "your line when the month's Batch Stock has not come by this day of the month"),
}


# ---------------------------------------------------------------------------------------------------------------- small helpers
def K(n):
    """The spine's 20-character key (spine_read.K)."""
    return re.sub(r'\s+', ' ', (n or "").strip())[:20].strip()


def norm(n):
    return re.sub(r'\s+', ' ', (n or "").upper()).strip()


def nbatch(b):
    """A batch as Marg prints it: an all-digit batch read as a number ('260117.0') is the same batch '260117'."""
    s = str(b if b is not None else "").strip().upper()
    if re.match(r'^\d+\.0$', s):
        s = s[:-2]
    return s


def pack_of(packing):
    m = re.match(r'^\s*(\d+)\s*\*\s*(\d+)', packing or "")
    return int(m.group(2)) if m and int(m.group(2)) > 0 else 1


def units_of(q, pack):
    """'20:5' -> 20*pack+5; '-1:3' -> -(pack+3); '12' -> 12; '-' or '' -> 0.  Marg's own sign rule (S268)."""
    q = (q or "").strip()
    if q in ("", "-"):
        return 0
    m = re.match(r'^(-?)(\d+):(\d+)$', q)
    if m:
        v = int(m.group(2)) * pack + int(m.group(3))
        return -v if m.group(1) else v
    try:
        return int(round(float(q)))
    except ValueError:
        raise ValueError("stock %r cannot be read" % q[:12])


def qty_txt(units, pack):
    """Strips:tabs for a strip item, a plain count otherwise (the owner's convention, 29-Sep)."""
    units = int(round(units or 0))
    if pack <= 1:
        return str(units)
    s = "-" if units < 0 else ""
    u = abs(units)
    return "%s%d:%d" % (s, u // pack, u % pack)


def ym(y, m):
    return "%04d-%02d" % (y, m)


def ym_add(s, n):
    y, m = int(s[:4]), int(s[5:7]) + n
    while m > 12:
        y, m = y + 1, m - 12
    while m < 1:
        y, m = y - 1, m + 12
    return ym(y, m)


def last_sell_day(exp_ym):
    """Marg blocks a batch from the first day of its expiry month: the last day it sells is the day before."""
    return dt.date(int(exp_ym[:4]), int(exp_ym[5:7]), 1) - dt.timedelta(days=1)


def mmyy(exp_ym):
    return "%s/%s" % (exp_ym[5:7], exp_ym[2:4]) if exp_ym else ""


def mon_year(exp_ym):
    return "%s %s" % (MON[int(exp_ym[5:7])], exp_ym[:4]) if exp_ym else ""


def dmon(iso):
    if not iso:
        return ""
    d = dt.date.fromisoformat(iso[:10])
    return "%d-%s" % (d.day, MON[d.month])


def esc(v):
    return html.escape(str(v if v is not None else ""), quote=True)


IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def now_ist():
    return dt.datetime.now(IST).replace(tzinfo=None)


def _has(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def setting(con, key):
    d = SETTINGS[key][0]
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
    except sqlite3.Error:
        r = None
    v = (r[0] if r and r[0] not in (None, "") else d)
    try:
        return float(v) if "." in str(v) else int(v)
    except ValueError:
        return float(d) if "." in d else int(d)


def ensure(con):
    con.execute("""CREATE TABLE IF NOT EXISTS stock_expiry_run (
        id INTEGER PRIMARY KEY, at TEXT NOT NULL, today TEXT NOT NULL, ok INTEGER NOT NULL, kit TEXT,
        export_md5 TEXT, export_name TEXT, export_as_on TEXT, export_items INTEGER, export_total INTEGER, whole INTEGER,
        closing_items INTEGER, sales_to TEXT, counts TEXT, note TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS stock_expiry_line (
        id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL, section TEXT NOT NULL, part TEXT, k20 TEXT, item TEXT, batch TEXT,
        expiry TEXT, units INTEGER, pack INTEGER, packing TEXT, last_sale TEXT, last_buy TEXT, info TEXT, seq INTEGER)""")
    con.execute("CREATE INDEX IF NOT EXISTS ix_stock_expiry_line_run ON stock_expiry_line (run_id, section, seq)")
    for k, (v, note) in SETTINGS.items():
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, "S638: " + note))


# ---------------------------------------------------------------------------------------------------------------- the reader
TITLE_RE = re.compile(r'^\s*WHOLE\s+STORES\s+CLOSING\s+STOCK\s+AS\s+ON\s+(\d{2})-(\d{2})-(\d{4})\s*$', re.I)
SER_RE = re.compile(r'^(\d+) (\S.*)$')
EXP_RE = re.compile(r'^(\d{1,2})/(\d{4})$')


def _rows(path):
    if SPINE_DIR not in sys.path:
        sys.path.insert(0, SPINE_DIR)
    import marg_read                                          # noqa: PLC0415  (the spine's certified opener)
    return marg_read.rows_of(path)


def split_merged(cell):
    """'LGP11/244/0710/2027' -> ('LGP11/244/07', '10/2027').  Marg prints the batch from column 44 and the expiry right-aligned to
    column 62, so the two touch only when the batch fills its 12 places: the split leaves at least 12 for the batch, a two-digit
    month (10-12) before a one-digit one.  None when no split leaves a whole batch."""
    for n in (2, 1):
        m = re.match(r'^(.+)(\d{%d})/(\d{4})$' % n, cell)
        if m and len(m.group(1)) >= 12 and 1 <= int(m.group(2)) <= 12 and (n == 1 or int(m.group(2)) >= 10):
            return m.group(1), "%s/%s" % (m.group(2), m.group(3))
    return None


def read_batch_stock(path=None, rows=None):
    """-> dict(ok, failed, as_on (ISO), batches=[...], items, total, md5).  Every row classified; the serials run 1..N unbroken;
    Marg's TOTAL re-adds from the batches (strips x pack + loose).  Made to fail: any row it cannot place refuses the file."""
    rows = rows if rows is not None else _rows(path)
    md5 = hashlib.md5(open(path, "rb").read()).hexdigest() if path else ""
    failed, batches = [], []
    as_on, head, total, furn = None, False, None, False
    for i, r in enumerate(rows):
        c = [str(x if x is not None else "").strip() for x in (list(r) + ["", "", "", ""])[:4]]
        if not any(c):
            continue
        m = TITLE_RE.match(c[0])
        if m:
            as_on = "%s-%s-%s" % (m.group(3), m.group(2), m.group(1))
            continue
        if c[0].startswith("S.No. Description") and c[1] == "Batch":
            head, furn = True, False
            continue
        if not head or furn:
            continue                                          # the letterhead, on the first page and after every page break
        if c[0] == "" and c[1] == "Batch" and c[2] == "TOTAL":
            continue                                          # an item's Batch TOTAL: furniture
        if c[0] == "" and c[1] == "" and c[2] == "" and re.match(r'^(Continued|Page No)\.\.\d+$', c[3]):
            furn = True                                       # a page break: the next page's head follows
            continue
        if c[0] == "TOTAL":
            try:
                total = int(round(float(c[3])))
            except ValueError:
                failed.append("row %d: a TOTAL that cannot be read" % (i + 1))
            continue
        if c[0].startswith("*** End of Report"):
            continue
        sm = SER_RE.match(c[0])
        if not sm:
            failed.append("row %d: unclassified" % (i + 1))
            continue
        ser = sm.group(1)
        body = c[0][len(ser) + 1:]
        name, packing = body[:30].strip(), body[31:].strip()
        if not packing:                                       # a name that ran into its packing
            mm = re.match(r'^(.*\S)\s+(\S+)$', body)
            name, packing = (mm.group(1).strip(), mm.group(2)) if mm else (body.strip(), "")
        pack = pack_of(packing)
        q = c[3].split()
        unit = q[1] if len(q) > 1 else ""
        try:
            u = units_of(q[0] if q else "", pack)
        except ValueError as ex:
            failed.append("row %d: %s" % (i + 1, ex))
            continue
        e = ""
        if not c[1] and c[2] and not EXP_RE.match(c[2]):
            sp_ = split_merged(c[2])                          # a batch that fills its column runs into the expiry (Marg's own print)
            if sp_:
                c[1], c[2] = sp_
        elif c[1] and not c[2] and not isinstance(r[1], float) and split_merged(c[1]):
            c[1], c[2] = split_merged(c[1])                   # the same run-together, cut into the batch's column
        em = EXP_RE.match(c[2])
        if em:
            e = ym(int(em.group(2)), int(em.group(1)))
        elif c[2]:
            failed.append("row %d: an expiry that cannot be read" % (i + 1))
            continue
        batches.append(dict(serial=int(ser), item=name, k20=K(name), packing=packing, pack=pack, batch=nbatch(c[1]), expiry=e,
                            units=u, stock=q[0] if q else "", unit=unit))
    if as_on is None:
        failed.append("no title 'WHOLE STORES CLOSING STOCK AS ON dd-mm-yyyy'")
    if not head:
        failed.append("no column heads 'S.No. Description | Batch | Expiry | Stock Unit'")
    if [b["serial"] for b in batches] != list(range(1, len(batches) + 1)):
        failed.append("the serial numbers do not run 1..N unbroken")
    s = sum(b["units"] for b in batches)
    if total is None:
        failed.append("no TOTAL row")
    elif total != s:
        failed.append("Marg's TOTAL %d is not the sum of the batches %d" % (total, s))
    return dict(ok=not failed, failed=failed, as_on=as_on, batches=batches, items=len({b["k20"] for b in batches}), total=total,
                md5=md5, name=os.path.basename(path) if path else "")


def batch_exports(archive):
    """Every Batch Stock the door has filed, newest capture first."""
    fs = [p for p in glob.glob(os.path.join(archive, "BATCH_STOCK", "*", "*")) if p.lower().endswith((".xls", ".xlsx"))]

    def stamp(p):
        parts = os.path.basename(p).split("__")
        return parts[2] if len(parts) > 2 else ""
    return sorted(fs, key=stamp, reverse=True)


# ---------------------------------------------------------------------------------------------------------------- the inputs
def _spine(spine_path):
    sp = sqlite3.connect("file:%s?mode=ro" % spine_path, uri=True)
    sp.row_factory = sqlite3.Row
    alias = {r["alias"]: r["k20"] for r in sp.execute("SELECT alias, k20 FROM sp_alias")}
    return sp, alias


def closing_items_on(sp, as_on):
    """How many items Marg's newest closing at or before the day holds in stock (>0): the yardstick of a whole-shop Batch Stock."""
    r = sp.execute("SELECT MAX(as_on) FROM sp_close WHERE as_on<=?", (as_on,)).fetchone()
    if not r or not r[0]:
        return 0, None
    n = sp.execute("SELECT COUNT(*) FROM sp_close WHERE as_on=? AND units>0", (r[0],)).fetchone()[0]
    return int(n), r[0]


def ortho_of(con):
    """The owner's own sections (stock_item_section) first, then the shared word list (section_map.is_orthotic, the order screens')."""
    sec = {}
    if _has(con, "stock_item_section"):
        for k, it, s in con.execute("SELECT item_key, item, section FROM stock_item_section"):
            sec[nkey(k or it)] = s                            # item_key is section_map.norm_key (punctuation out), never K()
    try:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import section_map                                    # noqa: PLC0415
        words = section_map.is_orthotic
    except Exception:                                         # noqa: BLE001
        words = lambda n: False                               # noqa: E731

    def is_o(name, packing=None):  # noqa: C901
        """packing given: the shared word list counts only for a single piece ('1*1', '1') -- 'DYNA' alone would take DYNAPAR QPS
        PLUS (15ML), a medicine (named in the report, not changed here: section_map is read only)."""
        s = sec.get(nkey(name))
        if s:
            return s == "Orthotics"
        if not words(name):
            return False
        return packing is None or (packing or "").strip() in ("", "1", "1*1")
    return is_o


def nkey(name):
    """section_map.norm_key, verbatim: upper case, every character but A-Z 0-9 and space made a space, spaces folded."""
    s = re.sub(r"[^A-Z0-9 ]+", " ", str(name or "").upper())
    return re.sub(r"\s+", " ", s).strip()


SIZE_RE = re.compile(r'\b(XXXL|XXL|XL|L|M|S|\d{2})\b')


def size_of(name):
    m = SIZE_RE.findall(name or "")
    return m[-1] if m else ""


# ---------------------------------------------------------------------------------------------------------------- the run
def compute(con, sp, alias, archive, today):
    """-> (run dict, lines list).  Reads only."""
    key = lambda n: alias.get(K(n), K(n))                    # noqa: E731
    run = dict(at=now_ist().replace(microsecond=0).isoformat(), today=today.isoformat(), ok=0, kit=KIT, note="")
    lines = []
    is_o = ortho_of(con)
    # 1 · the newest whole-shop Batch Stock
    chosen, tried = None, []
    for p in batch_exports(archive)[:12]:
        try:
            R = read_batch_stock(p)
        except Exception as ex:                               # noqa: BLE001
            tried.append("%s: unreadable (%s)" % (os.path.basename(p)[:60], str(ex)[:60]))
            continue
        if not R["ok"]:
            tried.append("%s: refused (%s)" % (os.path.basename(p)[:60], "; ".join(R["failed"])[:120]))
            continue
        n_close, on = closing_items_on(sp, R["as_on"])
        whole = n_close > 0 and R["items"] >= setting(con, "expiry.whole_fraction") * n_close
        if not whole:
            tried.append("%s: a filtered batch list (%d items; the closing of %s holds %d in stock)"
                         % (os.path.basename(p)[:60], R["items"], on or "-", n_close))
            continue
        chosen = R
        run.update(export_md5=R["md5"], export_name=R["name"], export_as_on=R["as_on"], export_items=R["items"],
                   export_total=R["total"], whole=1, closing_items=n_close)
        break
    run["note"] = " | ".join(tried)[:900]
    sales_to = sp.execute("SELECT MAX(date) FROM sp_sale_line").fetchone()[0] or ""
    run["sales_to"] = sales_to
    seq = [0]

    def add(section, **kw):
        seq[0] += 1
        kw.setdefault("info", None)
        if isinstance(kw.get("info"), (dict, list)):
            kw["info"] = json.dumps(kw["info"], sort_keys=True)
        lines.append(dict(section=section, seq=seq[0], **kw))

    last_sale = {r[0]: r[1] for r in sp.execute("SELECT k20, MAX(date) FROM sp_move WHERE kind='SALE' GROUP BY k20")}
    last_buy = {r[0]: r[1] for r in sp.execute("SELECT k20, MAX(date) FROM sp_move WHERE kind='PURCHASE' GROUP BY k20")}
    this_m = today.strftime("%Y-%m")
    if chosen:
        # 2 · the batches, lowered by the spine's sale lines after the export's day
        bt = {}
        order = []
        for b in chosen["batches"]:
            k = key(b["item"])
            kk = (k, b["batch"])
            if kk not in bt:
                bt[kk] = dict(b, k20=k, sold=0, printed=b["units"])
                order.append(kk)
            else:
                bt[kk]["units"] += b["units"]
                bt[kk]["printed"] += b["units"]
        new_wrong = []
        # the spine's sale lines after the export's day; a credit note (sp_sale_bill.credit_note) puts its units BACK on its batch
        for r in sp.execute("SELECT l.date, l.k20, l.batch, l.expiry, l.units, COALESCE(b.credit_note, 0) AS cn FROM sp_sale_line l "
                            "LEFT JOIN sp_sale_bill b ON b.date = l.date AND b.bill = l.bill WHERE l.date > ? ORDER BY l.date", (chosen["as_on"],)):
            k = alias.get(r["k20"], r["k20"])
            nb = nbatch(r["batch"])
            u = int(round(r["units"] or 0)) * (-1 if r["cn"] else 1)
            if (k, nb) in bt:
                x = bt[(k, nb)]
                x["units"] -= u
                x["sold"] += u
                if x["units"] < 0 and not x.get("_named"):
                    x["_named"] = r["date"]
            elif not nb and not r["cn"]:
                new_wrong.append(dict(k20=k, date=r["date"], units=u))
        bought_since = {r[0] for r in sp.execute("SELECT DISTINCT k20 FROM sp_move WHERE kind='PURCHASE' AND date > ?", (chosen["as_on"],))}
        gone = written_off(sp, chosen["as_on"])
        by_item = {}
        for kk in order:
            by_item.setdefault(kk[0], []).append(bt[kk])
        near_days = setting(con, "expiry.near_days")
        for kk in order:
            x = bt[kk]
            if x["units"] <= 0 or not x["expiry"]:
                continue
            info = dict(stock=qty_txt(x["units"], x["pack"]), sold_since=x["sold"])
            if x["expiry"] <= this_m:
                if gone(x["k20"], x["units"]):
                    continue                                  # Marg's closing has dropped by this batch beyond the sales: written off or returned
                add("expired", part="", k20=x["k20"], item=x["item"], batch=x["batch"], expiry=x["expiry"], units=x["units"],
                    pack=x["pack"], packing=x["packing"], last_sale=last_sale.get(x["k20"]), last_buy=last_buy.get(x["k20"]), info=info)
            elif (last_sell_day(x["expiry"]) - today).days <= near_days:
                info["stops"] = x["expiry"] + "-01"
                add("near", part=x["expiry"], k20=x["k20"], item=x["item"], batch=x["batch"], expiry=x["expiry"], units=x["units"],
                    pack=x["pack"], packing=x["packing"], last_sale=last_sale.get(x["k20"]), last_buy=last_buy.get(x["k20"]), info=info)
        # 3 · dump: stock (expired batches out), no sale and no purchase in expiry.dump_days -- the system's own sales
        cut = (today - dt.timedelta(days=setting(con, "expiry.dump_days"))).isoformat()
        for k, bs in by_item.items():
            good = [b for b in bs if b["units"] > 0 and not (b["expiry"] and b["expiry"] <= this_m)]
            u = sum(b["units"] for b in good)
            if u <= 0:
                continue
            ls, lb = last_sale.get(k), last_buy.get(k)
            if (ls and ls >= cut) or (lb and lb >= cut):
                continue
            exps = sorted(b["expiry"] for b in good if b["expiry"])
            o = is_o(bs[0]["item"], bs[0]["packing"])
            soon = bool(exps) and (last_sell_day(exps[0]) - today).days <= near_days
            add("dump", part="ortho" if o else "med", k20=k, item=bs[0]["item"], batch="", expiry=exps[0] if exps else "",
                units=u, pack=bs[0]["pack"], packing=bs[0]["packing"], last_sale=ls, last_buy=lb,
                info=dict(stock=qty_txt(u, bs[0]["pack"]), size=size_of(bs[0]["item"]) if o else "", soon=soon))
        # 4 · wrong batch: a batch below zero beside one with the stock (Marg's own print, then the sales since)
        for k, bs in sorted(by_item.items(), key=lambda kv: kv[1][0]["item"]):
            if k in bought_since:                             # a re-supply carries no batch on the spine: only Marg's own printed minus counts
                neg = [b for b in bs if b["printed"] < 0]
            else:
                neg = [b for b in bs if b["units"] < 0]
            pos = [b for b in bs if b["units"] > 0]
            if neg and pos:
                add("wrong", part="batch", k20=k, item=bs[0]["item"], batch=";".join(b["batch"] or "-" for b in neg), expiry="",
                    units=sum(b["units"] for b in neg), pack=bs[0]["pack"], packing=bs[0]["packing"],
                    last_sale=last_sale.get(k), last_buy=last_buy.get(k),
                    info=dict(below=[[b["batch"] or "", qty_txt(b["units"], b["pack"]), b.get("_named") or ""] for b in neg],
                              has=[[b["batch"] or "", qty_txt(b["units"], b["pack"])] for b in pos]))
        nob = {}
        for w in new_wrong:
            if w["date"] >= this_m + "-01":
                nob.setdefault(w["k20"], []).append(w)
        for k, ws in sorted(nob.items()):
            add("wrong", part="nobatch", k20=k, item=k, batch="", expiry="", units=sum(w["units"] for w in ws), pack=1, packing="",
                last_sale=max(w["date"] for w in ws), last_buy=None, info=dict(lines=len(ws), first=min(w["date"] for w in ws)))
    # 5 · new products: the month and the months before (purchase_new_item; the orthotic renames out; the item list)
    renamed = set()
    if _has(con, "marg_item_rename"):
        for nn, n20 in con.execute("SELECT new_name, new20 FROM marg_item_rename WHERE undone_at IS NULL"):
            renamed.add(K(nn or n20 or ""))
    known = set()
    if _has(con, "purchase_new_item"):
        for item, first, seen, sup, packing in con.execute(
                "SELECT item, first_seen, seen_in, supplier, packing FROM purchase_new_item ORDER BY first_seen, item"):
            known.add(K(item))
            if seen != "purchase" and (K(item) in renamed or is_o(item, packing or "")):
                continue                                      # D780: Amir's orthotic renames are not new products
            add("new", part=(first or "")[:7], k20=K(item), item=item, batch="", expiry="", units=0, pack=1, packing=packing or "",
                last_sale=None, last_buy=first, info=dict(seen="purchase" if seen == "purchase" else "marg",
                                                         supplier=re.sub(r'\s+', ' ', sup or "").strip()))
    for item, first in item_list_new(archive, known | renamed | {k for k in last_sale} | {k for k in last_buy}):
        if is_o(item, ""):
            continue
        add("new", part=first[:7], k20=K(item), item=item, batch="", expiry="", units=0, pack=1, packing="", last_sale=None,
            last_buy=first, info=dict(seen="list", supplier=""))
    # 6 · out of stock: waiting / arrived again
    for row in out_of_stock(con, sp, alias, today):
        add("oos", **row)
    run["ok"] = 1
    counts = {}
    for ln in lines:
        counts[ln["section"]] = counts.get(ln["section"], 0) + 1
    run["counts"] = json.dumps(counts, sort_keys=True)
    if not chosen:
        run["note"] = ("no whole-shop Batch Stock received yet" + (" | " + run["note"] if run["note"] else ""))[:900]
    return run, lines


def written_off(sp, as_on):
    """-> gone(k20, units): True when Marg's newest closing has fallen below what the export's day's closing and the spine's own moves
    since then say it should be, by at least the batch (a write-off voucher), or a purchase return since covers it.  Keeps Amir from being
    asked twice for a batch he has already written off (between two Batch Stocks only the item's closing can show it)."""
    newest = sp.execute("SELECT MAX(as_on) FROM sp_close").fetchone()[0]
    if not newest or newest <= as_on:
        return lambda k, u: False

    def gone(k, units):
        c0 = sp.execute("SELECT units FROM sp_close WHERE k20=? AND as_on<=? ORDER BY as_on DESC LIMIT 1", (k, as_on)).fetchone()
        c1 = sp.execute("SELECT units FROM sp_close WHERE k20=? AND as_on=?", (k, newest)).fetchone()
        if c0 is None:
            return False
        if c1 is None:
            return False                                      # the newest closing does not list the item: nothing can be judged
        c1v = c1[0] or 0
        mv = sp.execute("SELECT COALESCE(SUM(units),0) FROM sp_move WHERE k20=? AND date>? AND date<=?", (k, as_on, newest)).fetchone()[0] or 0
        pr = sp.execute("SELECT COALESCE(SUM(ABS(units)),0) FROM sp_move WHERE k20=? AND kind='PURCHASE_RETURN' AND date>? AND date<=?",
                        (k, as_on, newest)).fetchone()[0] or 0
        drop = (c0[0] or 0) + mv - c1v
        return drop >= 0.9 * units or pr >= 0.9 * units
    return gone


def now_view(sec, today):
    """The list as of TODAY: a near batch whose month has begun since the night it was made is expired now (the 23:57 run of the 31st
    is read all day on the 1st)."""
    m = today.strftime("%Y-%m")
    out = dict(sec)
    moved = [x for x in sec.get("near", []) if x["expiry"] and x["expiry"] <= m]
    if moved:
        out["near"] = [x for x in sec.get("near", []) if x not in moved]
        out["expired"] = list(sec.get("expired", [])) + moved
    return out


def item_list_new(archive, known):
    """Names in the newest monthly item list (ITEM_MASTER) that the one before it did not carry and nothing else has seen: a medicine
    created in Marg and not yet bought or counted.  -> [(name, first-seen ISO day)].  Fail-soft: [] when two lists are not held."""
    fs = [p for p in glob.glob(os.path.join(archive, "ITEM_MASTER", "*", "*")) if p.lower().endswith((".xls", ".xlsx"))]
    fs.sort(key=lambda p: (os.path.basename(p).split("__") + ["", "", ""])[2])
    if len(fs) < 2:
        return []
    try:
        if SPINE_DIR not in sys.path:
            sys.path.insert(0, SPINE_DIR)
        import marg_read                                      # noqa: PLC0415
        a = marg_read.read_item_master(marg_read.rows_of(fs[-2]))
        b = marg_read.read_item_master(marg_read.rows_of(fs[-1]))
        if not (a.ok and b.ok):
            return []
        old = {K(i["name"]) for i in a.data["items"]}
        day = (os.path.basename(fs[-1]).split("__") + ["", ""])[1][:10]
        return [(i["name"], day) for i in b.data["items"] if K(i["name"]) not in old and K(i["name"]) not in known]
    except Exception:                                         # noqa: BLE001
        return []


def out_of_stock(con, sp, alias, today):
    """Waiting: an order line short or missing (purchase_order_line), or a carry still open (order_carry), for an item whose newest
    closing (the spine's sp_close) holds none.  Arrived again: the first purchase after such a short, when the closing before it held
    none, kept expiry.arrived_days days."""
    out = []
    if not _has(con, "purchase_order_line") or not _has(con, "purchase_order"):
        return out
    key = lambda n: alias.get(K(n), K(n))                    # noqa: E731
    newest = sp.execute("SELECT MAX(as_on) FROM sp_close").fetchone()[0]
    if not newest:
        return out
    held = {r[0]: r[1] for r in sp.execute("SELECT k20, units FROM sp_close WHERE as_on=?", (newest,))}
    shorts = {}
    for r in con.execute("SELECT l.item, o.vendor, substr(o.created_at,1,10) FROM purchase_order_line l JOIN purchase_order o "
                         "ON o.id=l.order_id WHERE COALESCE(l.short,0)>0 OR COALESCE(l.missing,0)>0 ORDER BY o.created_at"):
        k = key(r[0])
        s = shorts.setdefault(k, dict(item=r[0], vendor=r[1], first=r[2], last=r[2]))
        s["last"], s["vendor"] = r[2], r[1]
    if _has(con, "order_carry"):
        for item, vendor, at in con.execute("SELECT c.item, c.vendor, COALESCE(substr(o.created_at,1,10), substr(c.at,1,10)) FROM order_carry c "
                                            "LEFT JOIN purchase_order o ON o.id=c.from_order_id WHERE c.done_order_id IS NULL "
                                            "AND c.dropped_at IS NULL ORDER BY c.at"):
            k = key(item)
            shorts.setdefault(k, dict(item=item, vendor=vendor, first=at, last=at))
    keep = setting(con, "expiry.arrived_days")
    marg_items = {r[0] for r in sp.execute("SELECT k20 FROM sp_item")}
    for k, s in sorted(shorts.items(), key=lambda kv: kv[1]["first"]):
        if k not in marg_items:
            continue                                          # a name Marg does not carry: its stock cannot be judged here
        bought = sp.execute("SELECT MIN(date) FROM sp_move WHERE kind='PURCHASE' AND k20=? AND date>=?", (k, s["last"])).fetchone()[0]
        times = con.execute("SELECT COUNT(*) FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                            "WHERE substr(o.created_at,1,10)>=? AND l.item=?", (s["first"], s["item"])).fetchone()[0]
        ls = sp.execute("SELECT MAX(date) FROM sp_move WHERE kind='SALE' AND k20=?", (k,)).fetchone()[0]
        if (held.get(k) or 0) <= 0 and not bought:
            out.append(dict(part="waiting", k20=k, item=s["item"], batch="", expiry="", units=0, pack=1, packing="", last_sale=ls,
                            last_buy=None, info=dict(vendor=s["vendor"], since=s["first"], times=max(int(times), 1))))
            continue
        buys = sp.execute("SELECT date, units FROM sp_move WHERE kind='PURCHASE' AND k20=? AND date>=? ORDER BY date LIMIT 1",
                          (k, s["last"])).fetchone()
        if not buys or (today - dt.date.fromisoformat(buys[0])).days > keep:
            continue
        before = sp.execute("SELECT units FROM sp_close WHERE k20=? AND as_on<? ORDER BY as_on DESC LIMIT 1", (k, buys[0])).fetchone()
        if before is not None and (before[0] or 0) > 0:
            continue
        pl = sp.execute("SELECT supkey, packing FROM sp_purchase_line WHERE k20=? AND date=? LIMIT 1", (k, buys[0])).fetchone()
        pk = pack_of(pl["packing"] if pl else "")
        out.append(dict(part="arrived", k20=k, item=s["item"], batch="", expiry="", units=int(round(buys[1] or 0)), pack=pk,
                        packing=pl["packing"] if pl else "", last_sale=ls, last_buy=buys[0],
                        info=dict(vendor=(pl["supkey"] if pl else s["vendor"]), since=s["first"])))
    return out


def run(db=DB_DEFAULT, spine_path=SPINE_DEFAULT, archive=ARCHIVE_DEFAULT, today=None, log=print):
    for f in OFF_FLAGS:
        if os.path.exists(f):
            log("expiry_watch: switched off (%s)" % f)
            return 0
    today = today or now_ist().date()
    sp, alias = _spine(spine_path)
    con = sqlite3.connect(db, timeout=60)
    try:
        ensure(con)
        con.commit()                                          # the settings seeded; no write is held open while the files are read
        r, lines = compute(con, sp, alias, archive, today)
        with con:
            cur = con.execute("INSERT INTO stock_expiry_run (at, today, ok, kit, export_md5, export_name, export_as_on, export_items, "
                              "export_total, whole, closing_items, sales_to, counts, note) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                              (r["at"], r["today"], r["ok"], r["kit"], r.get("export_md5"), r.get("export_name"), r.get("export_as_on"),
                               r.get("export_items"), r.get("export_total"), r.get("whole"), r.get("closing_items"), r.get("sales_to"),
                               r.get("counts"), r.get("note")))
            rid = cur.lastrowid
            con.execute("DELETE FROM stock_expiry_line WHERE run_id<>?", (rid,))
            con.executemany("INSERT INTO stock_expiry_line (run_id, section, part, k20, item, batch, expiry, units, pack, packing, "
                            "last_sale, last_buy, info, seq) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            [(rid, x["section"], x.get("part"), x.get("k20"), x.get("item"), x.get("batch"), x.get("expiry"),
                              int(x.get("units") or 0), int(x.get("pack") or 1), x.get("packing"), x.get("last_sale"), x.get("last_buy"),
                              x.get("info"), x["seq"]) for x in lines])
        log("expiry_watch %s: run %d · export %s (as on %s) · %s · %s" % (KIT, rid, (r.get("export_name") or "none")[:70],
                                                                         r.get("export_as_on") or "-", r.get("counts"), (r.get("note") or "")[:200]))
        return 0
    finally:
        con.close()
        sp.close()


# ---------------------------------------------------------------------------------------------------------------- reading a run
def newest(con):
    """(run row as dict, {section: [line dicts]}) of the newest run, or (None, {})."""
    try:
        if not _has(con, "stock_expiry_run"):
            return None, {}
        r = con.execute("SELECT * FROM stock_expiry_run WHERE ok=1 ORDER BY id DESC LIMIT 1").fetchone()
        if not r:
            return None, {}
        cols = [d[0] for d in con.execute("SELECT * FROM stock_expiry_run LIMIT 0").description]
        run_ = dict(zip(cols, tuple(r)))
        lc = [d[0] for d in con.execute("SELECT * FROM stock_expiry_line LIMIT 0").description]
        sec = {}
        for x in con.execute("SELECT * FROM stock_expiry_line WHERE run_id=? ORDER BY section, seq", (run_["id"],)):
            d = dict(zip(lc, tuple(x)))
            try:
                d["info"] = json.loads(d["info"]) if d["info"] else {}
            except ValueError:
                d["info"] = {}
            sec.setdefault(d["section"], []).append(d)
        return run_, sec
    except sqlite3.Error:
        return None, {}


def batch_stock_in(con, today):
    """The month's Batch Stock is IN when the newest run used a whole-shop export dated this month, or a Batch Stock reached the door
    this month after that run (the nightly has not judged it yet).  A filtered print judged by the nightly does not count: the card
    comes back on Amir's page (a do-this line) and the owner's line says why.  -> received_at of the newest such file, or None."""
    m = today.strftime("%Y-%m")
    got = batch_stock_received(con, m)
    if not got:
        return None
    run_, _sec = newest(con)
    if run_ and (run_.get("export_as_on") or "")[:7] == m and run_.get("whole") == 1:
        return got[0]
    if not run_ or str(got[0]).replace("T", " ")[:19] > str(run_.get("at") or "").replace("T", " ")[:19]:
        return got[0]
    return None


def batch_stock_received(con, month):
    """The month's Batch Stock as the door filed it: (received_at, md5) of the newest, or None."""
    try:
        r = con.execute("SELECT received_at, md5 FROM mi_file WHERE type='BATCH_STOCK' AND verdict='VERIFIED' AND substr(received_at,1,7)=? "
                        "ORDER BY received_at DESC LIMIT 1", (month,)).fetchone()
    except sqlite3.Error:
        return None
    return tuple(r) if r else None


# ---------------------------------------------------------------------------------------------------------------- Darpan
def darpan_sell_first(con, today=None):
    """[{stops: 'YYYY-MM-01', item, batch, stock}] -- the batches Marg stops selling within expiry.darpan_months months, by the
    day Marg stops them, the biggest stock first.  Empty when there is no run.  D708: a do-this line, nothing to tap."""
    today = today or now_ist().date()
    run_, sec = newest(con)
    sec = now_view(sec, today)
    if not run_:
        return []
    upto = ym_add(today.strftime("%Y-%m"), int(setting(con, "expiry.darpan_months")))
    out = []
    for x in sec.get("near", []):
        if x["expiry"] <= upto and x["units"] > 0:
            out.append(dict(stops=x["expiry"] + "-01", item=x["item"], batch=x["batch"], stock=qty_txt(x["units"], x["pack"]), units=x["units"]))
    out.sort(key=lambda d: (d["stops"], -d["units"], d["item"]))
    return out


def darpan_groups(con, today=None):
    """The same, grouped for the tab: [{label: '1 Nov se band', rows: [...]}]."""
    g = {}
    for d in darpan_sell_first(con, today):
        g.setdefault(d["stops"], []).append(d)
    return [dict(label="%d %s se band" % (1, MON[int(k[5:7])]), stops=k, rows=v) for k, v in sorted(g.items())]


# ---------------------------------------------------------------------------------------------------------------- Amir
def amir_rows(con, today=None):
    """Rows for Amir's Marg sudhar card, in amir_day's shape (kind, hi_html, en_text, his_line).  his_line is False on every row:
    the expired batches and the batch corrections are monthly work proved only by the next month's Batch Stock, so they never hold
    his day open (D708 / D712: no line rests on a tap; no gate he cannot clear)."""
    today = today or now_ist().date()
    rows = []
    if not batch_stock_in(con, today):
        rows.append(("batchstock", EXPORT_CARD_HI % dict(mon=MON[today.month]),
                     "the month's Batch Stock (whole store) to export as text", False))
    run_, sec = newest(con)
    sec = now_view(sec, today)
    if run_:
        ex = [x for x in sec.get("expired", []) if x["units"] > 0]
        if ex:
            li = "".join("<li>%s &middot; <span style='font-family:monospace'>%s</span> &middot; %s</li>"
                         % (esc(x["item"]), esc(x["batch"] or "-"), esc(qty_txt(x["units"], x["pack"]))) for x in ex)
            rows.append(("expired", "<div class='line s638exp'><span class=big>Marg mein expiry write-off ya stockist ko return karein:</span>"
                         "<ul>%s</ul></div>" % li, "expired batches to write off or return: %d" % len(ex), False))
        wr = [x for x in sec.get("wrong", []) if x["part"] == "batch"]
        if wr:
            li = "".join("<li>%s &mdash; minus: %s &middot; stock wala: %s</li>"
                         % (esc(x["item"]), esc(", ".join("%s %s" % (b[0] or "bina batch", b[1]) for b in x["info"].get("below", []))),
                            esc(", ".join("%s %s" % (b[0], b[1]) for b in x["info"].get("has", [])))) for x in wr)
            rows.append(("batchfix", "<div class='line s638fix'><details><summary class=big>Marg mein in %d dawaon ka batch theek karein"
                         "</summary><ul>%s</ul></details></div>" % (len(wr), li), "batches to correct in Marg: %d" % len(wr), False))
    return rows


EXPORT_CARD_HI = ("<div class='line s638card' style='border:1px solid var(--accent);border-radius:8px;padding:8px 10px'>"
                  "<span class=big>Mahine ki report: Batch Stock (poora store) text mein save karein</span>"
                  "<ol style='margin:6px 0 0;padding-left:20px'>"
                  "<li>Marg main screen &rarr; <b>Stocks</b> &rarr; <b>Batch Stock</b></li>"
                  "<li>Select Store &rarr; <b>WHOLE</b> &rarr; Enter</li>"
                  "<li>Selected Company <b>No</b> &middot; Stock as on: jo date Marg dikhaye &middot; Stock Status <b>Available</b> &middot; "
                  "Selected Salt <b>No</b> &middot; More Options <b>No</b> &rarr; <b>Accept</b></li>"
                  "<li>Report menu kholein &rarr; <b>A Stock Statement</b></li>"
                  "<li>Index On &rarr; <b>B Alphabatic</b></li>"
                  "<li>Separate Printing <b>1 No</b>, dono Chr box khaali &rarr; Enter</li>"
                  "<li><b>View</b></li>"
                  "<li>View screen mein <b>Save</b> (F3) dabayein. File apne aap chali jayegi.</li></ol></div>")


# ---------------------------------------------------------------------------------------------------------------- the owner
def needs_you_lines(con, today=None):
    """The owner's Needs-you lines (sanjeevni_approvals.needs_you, fail-soft): what is expired or stops next month, and a month's
    Batch Stock not received by expiry.export_due_day (or received only as a filtered list)."""
    today = today or now_ist().date()
    out = []
    run_, sec = newest(con)
    sec = now_view(sec, today)
    if run_:
        ex = [x for x in sec.get("expired", []) if x["units"] > 0]
        nxt = ym_add(today.strftime("%Y-%m"), 1)
        soon = [x for x in sec.get("near", []) if x["expiry"] <= nxt]
        if ex or soon:
            bits = []
            if ex:
                bits.append("%d expired batch%s" % (len(ex), "" if len(ex) == 1 else "es"))
            if soon:
                bits.append("%d stop%s selling on 1-%s" % (len(soon), "s" if len(soon) == 1 else "", MON[int(nxt[5:7])]))
            out.append(dict(cls="warn", target="expiry", href=PAGE, text="Expiry watch: " + " · ".join(bits)))
    month = today.strftime("%Y-%m")
    if today.day >= int(setting(con, "expiry.export_due_day")):
        got = batch_stock_received(con, month)
        whole = bool(batch_stock_in(con, today))
        if not got:
            out.append(dict(cls="warn", target="expiry", href=PAGE,
                            text="%s's Batch Stock not received yet (Amir, monthly; his card shows the steps)" % MON[today.month]))
        elif not whole:
            out.append(dict(cls="warn", target="expiry", href=PAGE,
                            text="%s's Batch Stock came as a filtered list, not the whole store -- it is not used" % MON[today.month]))
    return out


def save_settings(con, form, who):
    """The owner's form: each known key, a number; anything else ignored.  -> (changed keys)."""
    changed = []
    for k in SETTINGS:
        v = (form.get(k) or "").strip()
        if not v:
            continue
        try:
            f = float(v)
        except ValueError:
            continue
        if f < 0 or f > 10000 or (k == "expiry.whole_fraction" and not 0.3 <= f <= 1):
            continue
        v = ("%g" % f) if "." in SETTINGS[k][0] else str(int(round(f)))
        old = con.execute("SELECT value FROM setting WHERE key=?", (k,)).fetchone()
        if old and old[0] == v:
            continue
        con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (k, v, "S638: " + SETTINGS[k][1]))
        changed.append(k)
    if changed:
        try:
            con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                        ("setting", None, "expiry_settings", None, json.dumps(changed), who, now_ist().replace(microsecond=0).isoformat()))
        except sqlite3.Error:
            pass
    con.commit()
    return changed


CSS = """
:root{--bg:#f3f5f4;--paper:#fff;--ink:#1d2a27;--muted:#5b6b67;--line:#d9e1de;--accent:#1f6f62;--accent-soft:#e3f0ec;--red:#a8322b;
--red-soft:#f8e6e4;--amber:#8a5a00;--amber-soft:#fbf0d9;--blue:#2f5fa8}
@media (prefers-color-scheme:dark){:root{--bg:#121816;--paper:#1a2220;--ink:#e4ebe8;--muted:#9aaba6;--line:#2e3a37;--accent:#6cc4b2;
--accent-soft:#1d3430;--red:#ef8a80;--red-soft:#3a1f1d;--amber:#e6b85c;--amber-soft:#3a2e15;--blue:#8fb1ec;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:760px;margin:0 auto;padding:16px}h1{font-size:1.45rem;margin:0}.sub{color:var(--muted);font-size:.86rem;margin:4px 0 12px}
.screen{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:6px 16px 14px}
details{border-bottom:1px solid var(--line);padding:10px 0}details:last-of-type{border-bottom:0}
summary{cursor:pointer;display:flex;gap:10px;align-items:baseline;list-style:none}summary::-webkit-details-marker{display:none}
summary::before{content:"\\25B8";color:var(--muted)}details[open]>summary::before{content:"\\25BE"}
summary h3{font-size:1rem;margin:0;font-weight:600;flex:1;min-width:0}
.count{font-family:ui-monospace,Menlo,monospace;font-size:.85rem;padding:1px 8px;border-radius:999px;background:var(--accent-soft);color:var(--accent)}
.count.red{background:var(--red-soft);color:var(--red)}.count.amber{background:var(--amber-soft);color:var(--amber)}
.what{color:var(--muted);font-size:.86rem;margin:6px 0 8px 20px}.tbl{overflow-x:auto;margin-left:20px}
table{border-collapse:collapse;width:100%;font-size:.88rem}th{text-align:left;font-weight:500;color:var(--muted);font-size:.74rem;
text-transform:uppercase;letter-spacing:.04em;padding:4px 8px 4px 0;border-bottom:1px solid var(--line)}
td{padding:5px 8px 5px 0;border-bottom:1px solid var(--line);vertical-align:top}
.m{font-family:ui-monospace,Menlo,monospace;font-size:.82rem;white-space:nowrap}.n{text-align:right}
tr.grp td{background:var(--amber-soft);color:var(--amber);font-size:.82rem;padding:5px 8px}.sub2{font-weight:600;margin:10px 0 4px 20px;font-size:.92rem}
details.inner{margin-left:20px;padding:8px 0;border-bottom:0}.note{font-size:.84rem;color:var(--muted);margin:4px 0 0 20px}
.xs{color:var(--amber);font-family:ui-monospace,Menlo,monospace;font-size:.8rem;font-weight:600}.xr{color:var(--blue);font-family:ui-monospace,Menlo,monospace;font-size:.8rem}
tr.hi td{font-weight:600;background:var(--amber-soft)}tr.lo td{color:var(--muted);opacity:.65}tr.sep td{border-bottom:2px solid var(--line);padding:2px}
.tag{font-size:.72rem;padding:0 6px;border-radius:999px;background:var(--red-soft);color:var(--red)}
form.set{display:grid;grid-template-columns:1fr auto;gap:6px 10px;margin:8px 0 0 20px;font-size:.86rem;align-items:center}
form.set input{width:90px;padding:4px 6px}form.set button{grid-column:1/3;justify-self:start;padding:6px 14px}
.ok{color:var(--accent)}.bad{color:var(--red)}a{color:var(--accent)}
"""


def _tbl(heads, body, right=()):
    th = "".join('<th%s>%s</th>' % (' class="n"' if i in right else "", esc(h)) for i, h in enumerate(heads))
    return '<div class="tbl"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (th, body)


def owner_page(con, today=None, saved=None):
    """The owner's page (English), the six sections of the approved mock-up (D780)."""
    today = today or now_ist().date()
    run_, sec = newest(con)
    sec = now_view(sec, today)
    head = ('<div class="wrap"><h1>Expiry, dump and stock-out watch</h1>')
    if not run_:
        return _shell(head + '<p class="sub">No list yet: it is made every night at 23:57 from Marg\'s Batch Stock and the system\'s own '
                      'sales. %s</p>%s</div>' % (_export_line(con, today, None), _settings_html(con, saved)))
    sub = ('<p class="sub">Made %s IST from Marg\'s Batch Stock as on %s (%s items) and the system\'s sales to %s. '
           'Stock is strips:tabs. %s</p>' % (esc(run_["at"][:16].replace("T", " ")), esc(dmon(run_.get("export_as_on")) or "-"),
                                           esc(run_.get("export_items") or 0), esc(dmon(run_.get("sales_to"))),
                                           _export_line(con, today, run_)))
    if not run_.get("export_as_on"):
        sub += '<p class="sub bad">%s</p>' % esc(run_.get("note") or "")
    out = [head, sub, '<div class="screen">']
    # 1 expired
    ex = sorted(sec.get("expired", []), key=lambda x: x["expiry"])
    body = "".join('<tr><td>%s</td><td class="m">%s</td><td class="m">%s</td><td class="m n">%s</td></tr>'
                   % (esc(x["item"]), esc(x["batch"]), esc(mon_year(x["expiry"])), esc(qty_txt(x["units"], x["pack"]))) for x in ex)
    out.append('<details open><summary><h3>1 &middot; Expired medicines</h3><span class="count red">%d</span></summary>'
               '<p class="what">Past their month; Marg will not sell them. Amir writes them off in Marg (Breakage / Expiry) or returns '
               'them to the stockist. He sees them on his page.</p>%s</details>'
               % (len(ex), _tbl(("Item", "Batch", "Expiry", "Stock"), body, (3,)) if ex else '<p class="note">None.</p>'))
    # 2 near
    nr = sorted(sec.get("near", []), key=lambda x: (x["expiry"], -x["units"]))
    body, cur = [], None
    for x in nr:
        if x["expiry"] != cur:
            cur = x["expiry"]
            body.append('<tr class="grp"><td colspan="4">Marg stops selling from <b>1-%s-%s</b></td></tr>' % (MON[int(cur[5:7])], cur[:4]))
        body.append('<tr><td>%s</td><td class="m">%s</td><td class="m">%s</td><td class="m n">%s</td></tr>'
                    % (esc(x["item"]), esc(x["batch"]), esc(mon_year(x["expiry"])), esc(qty_txt(x["units"], x["pack"]))))
    out.append('<details open><summary><h3>2 &middot; Near expiry</h3><span class="count amber">%d</span></summary>'
               '<p class="what">Counted to the day Marg stops selling the batch, %d days ahead. Darpan\'s tab tells him to sell these '
               'batches first.</p>%s</details>' % (len(nr), setting(con, "expiry.near_days"),
                                                   _tbl(("Item", "Batch", "Expiry", "Stock"), "".join(body), (3,)) if nr else '<p class="note">None.</p>'))
    # 3 dump
    dp = sec.get("dump", [])
    do = sorted([x for x in dp if x["part"] == "ortho"], key=lambda x: x["item"])
    dm = [x for x in dp if x["part"] != "ortho"]
    soon = sorted([x for x in dm if (x["info"] or {}).get("soon")], key=lambda x: (x["expiry"], x["item"]))
    rest = sorted([x for x in dm if not (x["info"] or {}).get("soon")], key=lambda x: (-x["units"], x["item"]))
    bold, grey = setting(con, "expiry.bold_strips"), setting(con, "expiry.grey_strips")
    obody = "".join('<tr><td>%s</td><td class="m">%s</td><td class="m n">%s</td><td class="m">%s</td></tr>'
                    % (esc(x["item"]), esc((x["info"] or {}).get("size") or "—"), esc(qty_txt(x["units"], x["pack"])),
                       esc(dmon(x["last_sale"]) or "none since 1-Apr")) for x in do)

    def mrow(x, s):
        strips = x["units"] / float(max(x["pack"], 1))
        cls = (' class="hi"' if strips >= bold else (' class="lo"' if strips < grey else "")) if s else ""
        e = (' <span class="%s">(%s)</span>' % ("xs" if s else "xr", esc(mmyy(x["expiry"])))) if x["expiry"] else ""
        return ('<tr%s><td>%s%s</td><td class="m">%s</td><td class="m n">%s</td><td class="m">%s</td></tr>'
                % (cls, esc(x["item"]), e, esc(x["packing"]), esc(qty_txt(x["units"], x["pack"])), esc(dmon(x["last_sale"]) or "none since 1-Apr")))
    mbody = "".join(mrow(x, True) for x in soon) + ('<tr class="sep"><td colspan="4"></td></tr>' if soon and rest else "") + \
        "".join(mrow(x, False) for x in rest)
    out.append('<details open><summary><h3>3 &middot; Dump &mdash; no sale and no purchase in %d days</h3><span class="count">%d + %d</span>'
               '</summary><p class="what">Your decision: keep, return, or move. By the system\'s own sales, not Marg\'s "not sold" list.</p>'
               '<details class="inner"><summary><h3>Orthotics</h3><span class="count">%d</span></summary>%s</details>'
               '<details class="inner"><summary><h3>Medicines and others</h3><span class="count">%d</span></summary>'
               '<p class="note"><span class="xs">Expiring soon</span> first (%d), earliest first: <b>bold</b> = %d strips or more left, '
               'grey = under %d strip%s. The rest show their earliest expiry <span class="xr">(mm/yy)</span>. Expired batches are only in '
               'section 1.</p>%s</details></details>'
               % (setting(con, "expiry.dump_days"), len(do), len(dm), len(do),
                  _tbl(("Item", "Size", "Stock", "Last sale"), obody, (2,)) if do else '<p class="note">None.</p>',
                  len(dm), len(soon), bold, grey, "" if grey == 1 else "s",
                  _tbl(("Item", "Packing", "Stock", "Last sale"), mbody, (2,)) if dm else '<p class="note">None.</p>'))
    # 4 wrong
    wr = [x for x in sec.get("wrong", []) if x["part"] == "batch"]
    nb = [x for x in sec.get("wrong", []) if x["part"] == "nobatch"]
    body = "".join('<tr><td>%s</td><td class="m">%s</td><td class="m">%s</td></tr>'
                   % (esc(x["item"]), "<br>".join(esc("%s  %s" % (b[0] or "no batch", b[1])) for b in x["info"].get("below", [])),
                      "<br>".join(esc("%s  %s" % (b[0], b[1])) for b in x["info"].get("has", []))) for x in wr)
    nneg = sum(len(x["info"].get("below", [])) for x in wr)
    out.append('<details><summary><h3>4 &middot; Wrong batch &mdash; Marg\'s batches below zero</h3><span class="count">%d</span></summary>'
               '<p class="what">A batch sold below zero while another batch of the same medicine has stock (%d batches in %d medicines). '
               'Amir corrects them in Marg on his monthly visit; a new one is named here the next day.</p>%s%s</details>'
               % (len(wr), nneg, len(wr), _tbl(("Item", "Below zero", "Has the stock"), body) if wr else '<p class="note">None.</p>',
                  ('<p class="note">Sold this month with no batch at all (%d items): %s.</p>'
                   % (len(nb), esc(", ".join("%s (%d)" % (x["item"], (x["info"] or {}).get("lines", 0)) for x in nb)))) if nb else ""))
    # 5 new products
    nw = sec.get("new", [])
    month = today.strftime("%Y-%m")
    cur = [x for x in nw if (x["part"] or "") == month]
    old = [x for x in nw if (x["part"] or "") < month]
    bought = [x for x in cur if (x["info"] or {}).get("seen") == "purchase"]
    made = [x for x in cur if (x["info"] or {}).get("seen") != "purchase"]
    bb = "".join('<tr><td>%s</td><td class="m">%s</td><td>%s</td><td class="m">%s</td></tr>'
                 % (esc(x["item"]), esc(dmon(x["last_buy"])), esc(((x["info"] or {}).get("supplier") or "").title()), esc(x["packing"]))
                 for x in bought)
    mb = "".join('<tr><td>%s</td><td class="m">%s</td><td class="m">%s</td></tr>'
                 % (esc(x["item"]) + (' <span class="note">(item list)</span>' if (x["info"] or {}).get("seen") == "list" else ""),
                    esc(dmon(x["last_buy"])), esc(x["packing"])) for x in made)
    ob = "".join('<tr><td>%s</td><td class="m">%s</td><td>%s</td><td class="m">%s</td></tr>'
                 % (esc(x["item"]), esc(dmon(x["last_buy"])), esc(((x["info"] or {}).get("supplier") or "").title()), esc(x["packing"]))
                 for x in sorted(old, key=lambda x: x["last_buy"] or "", reverse=True))
    out.append('<details open><summary><h3>5 &middot; New products &mdash; %s</h3><span class="count">%d</span></summary>'
               '<p class="what">A name Marg had never carried before, the day it first appeared. Nothing goes to staff. Amir\'s orthotic '
               'renames are left out.</p><div class="sub2">First bought &mdash; %d</div>%s<div class="sub2">Created in Marg without a purchase '
               '&mdash; %d</div>%s<details class="inner"><summary><h3>Earlier months</h3><span class="count">%d</span></summary>%s</details></details>'
               % (MON[today.month], len(cur), len(bought), _tbl(("Item", "First seen", "Stockist", "Packing"), bb) if bought else '<p class="note">None.</p>',
                  len(made), _tbl(("Item", "First seen", "Packing"), mb) if made else '<p class="note">None.</p>', len(old),
                  _tbl(("Item", "First seen", "Stockist", "Packing"), ob) if old else '<p class="note">None.</p>'))
    # 6 out of stock
    os_ = sec.get("oos", [])
    wt = [x for x in os_ if x["part"] == "waiting"]
    ar = [x for x in os_ if x["part"] == "arrived"]
    wb = "".join('<tr><td>%s</td><td>%s</td><td class="m">%s</td><td class="m n">%s</td><td class="m">%s</td></tr>'
                 % (esc(x["item"]), esc(((x["info"] or {}).get("vendor") or "").title()), esc(dmon((x["info"] or {}).get("since"))),
                    esc((x["info"] or {}).get("times") or 1), esc(dmon(x["last_sale"]) or "—")) for x in wt)
    ab = "".join('<tr><td>%s</td><td>%s</td><td class="m">%s</td><td class="m n">%s</td></tr>'
                 % (esc(x["item"]), esc(((x["info"] or {}).get("vendor") or "").title()), esc(dmon(x["last_buy"])),
                    esc(qty_txt(x["units"], x["pack"]))) for x in ar)
    out.append('<details open><summary><h3>6 &middot; Out of stock &mdash; the stockist could not supply</h3><span class="count amber">%d</span>'
               '</summary><p class="what">Ordered, did not come, and Marg\'s stock is now zero. It goes back on that dealer\'s next order by '
               'itself (your rule).</p><div class="sub2">Waiting</div>%s<div class="sub2">Arrived again &mdash; shown for %d days</div>%s</details>'
               % (len(wt), _tbl(("Item", "Stockist", "Ordered", "Times ordered", "Last sale"), wb, (3,)) if wt else '<p class="note">None.</p>',
                  setting(con, "expiry.arrived_days"), _tbl(("Item", "Stockist", "Arrived", "Qty"), ab, (3,)) if ar else '<p class="note">None.</p>'))
    out.append("</div>")
    out.append(_settings_html(con, saved))
    out.append("</div>")
    return _shell("".join(out))


def _export_line(con, today, run_):
    got = batch_stock_in(con, today)
    if got:
        return "This month's Batch Stock received %s." % esc(dmon(got))
    return "This month's Batch Stock not received yet (Amir's card shows the steps)."


def _settings_html(con, saved):
    rows = "".join('<label for="%s">%s</label><input id="%s" name="%s" inputmode="decimal" value="%s">'
                   % (esc(k), esc(v[1]), esc(k), esc(k), esc(setting(con, k))) for k, v in SETTINGS.items())
    msg = ""
    if saved is not None:
        msg = '<p class="note ok">Saved: %s. The list is made again tonight.</p>' % esc(", ".join(saved)) if saved else \
              '<p class="note">Nothing changed.</p>'
    return ('<details class="screen" style="margin-top:14px"><summary><h3>Settings</h3></summary>%s'
            '<form class="set" method="post" action="%s/settings">%s<button type="submit">Save</button></form></details>' % (msg, PAGE, rows))


def _shell(body):
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Expiry watch</title><style>%s</style></head><body>%s</body></html>' % (CSS, body))


# ---------------------------------------------------------------------------------------------------------------- command line
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("run", "read", "show"))
    ap.add_argument("file", nargs="?")
    ap.add_argument("--db", default=DB_DEFAULT)
    ap.add_argument("--spine", default=SPINE_DEFAULT)
    ap.add_argument("--archive", default=ARCHIVE_DEFAULT)
    ap.add_argument("--date", default="")
    a = ap.parse_args(argv)
    if a.cmd == "read":
        R = read_batch_stock(a.file)
        print("%s: %d batches, %d items, TOTAL %s, as on %s%s" % ("OK" if R["ok"] else "REFUSED", len(R["batches"]), R["items"], R["total"],
                                                                R["as_on"], ("" if R["ok"] else " -- " + "; ".join(R["failed"]))))
        return 0 if R["ok"] else 1
    if a.cmd == "run":
        return run(a.db, a.spine, a.archive, dt.date.fromisoformat(a.date) if a.date else None)
    con = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
    r, sec = newest(con)
    print(json.dumps(r, indent=1))
    for k, v in sorted(sec.items()):
        print("%-8s %d" % (k, len(v)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
