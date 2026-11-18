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
  * S883 (18-Nov-2026): each run also keeps EVERY batch of every item it worked out in stock_batch_now (replaced whole by the next run
    that used a whole-shop Batch Stock) -- read by the item ledger's Batches box; no list above changes.
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

KIT = "S693_STOCK_ON_BATCH"          # S638 built the watch; S693 new stock on its batch; S690: the voucher pair, the Batch Stock every visit, the confirmation
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
    batch_now_ensure(con)
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
        s = sec.get(nkey(name)) or _twin(sec, nkey(name))     # S669: the owner's word survives Marg's report widths
        if s:
            return s == "Orthotics"
        if not words(name):
            return False
        return packing is None or (packing or "").strip() in ("", "1", "1*1")
    return is_o


TWIN_MIN = 12


def _twin(sec, k):
    """S669 (28-Oct-2026): Marg's reports print an item's name at different widths (the closing stock 28 letters, the Batch Stock 30, a
    voucher 26), so the owner's section rulings -- keyed on one width -- must be found from another. The section of the ONE table key that is
    a prefix of k or that k is a prefix of, the shorter at least TWIN_MIN letters; None when none or more than one."""
    if not k or len(k) < TWIN_MIN:
        return None
    hits = [t for t in sec if t != k and len(t) >= TWIN_MIN and (k.startswith(t) or t.startswith(k))]
    return sec[hits[0]] if len(hits) == 1 else None


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
        sales_after = _sales_after(chosen)                    # S668 (D740): the day whose END the Batch Stock stands for
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
        by_k, s693_tied, s693_untied, s693_placed, s693_units = _s693_place(con, bt, order, key, is_o, sales_after)   # S693: new stock on its batch
        sp_bought = {}                                        # the spine's own purchase units since the day: a report that lags the spine is not whole
        for r in sp.execute("SELECT k20, COALESCE(SUM(units),0) FROM sp_move WHERE kind='PURCHASE' AND date > ? GROUP BY k20", (sales_after,)):
            kk0 = alias.get(r[0], r[0])
            sp_bought[kk0] = sp_bought.get(kk0, 0) + (r[1] or 0)
        s693_tied = {k for k in s693_tied if s693_units.get(k, 0) + 0.5 >= sp_bought.get(k, 0)}
        s693_untied = set(s693_untied) | {k for k in s693_units if k not in s693_tied}
        new_wrong = []
        # the spine's sale lines after the export's day; a credit note (sp_sale_bill.credit_note) puts its units BACK on its batch
        for r in sp.execute("SELECT l.date, l.k20, l.batch, l.expiry, l.units, COALESCE(b.credit_note, 0) AS cn FROM sp_sale_line l "
                            "LEFT JOIN sp_sale_bill b ON b.date = l.date AND b.bill = l.bill WHERE l.date > ? ORDER BY l.date", (sales_after,)):
            k = alias.get(r["k20"], r["k20"])
            nb = nbatch(r["batch"])
            u = int(round(r["units"] or 0)) * (-1 if r["cn"] else 1)
            if (k, nb) not in bt and nb:
                kk3 = _s693_sale_tie(bt, by_k, k, nb)     # S693: the batch as the sale text prints it vs the Batch Stock's
                if kk3 is not None:
                    nb = kk3[1]
            if (k, nb) in bt:
                x = bt[(k, nb)]
                x["units"] -= u
                x["sold"] += u
                if x["units"] < 0 and not x.get("_named"):
                    x["_named"] = r["date"]
            elif not nb and not r["cn"]:
                new_wrong.append(dict(k20=k, date=r["date"], units=u))
        bought_since = {r[0] for r in sp.execute("SELECT DISTINCT k20 FROM sp_move WHERE kind='PURCHASE' AND date > ?", (sales_after,))}
        gone = written_off(sp, sales_after)
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
            if k in bought_since and k not in s693_tied:      # S693: a re-supply placed on its batch is judged like any other; untied: Marg's printed minus only
                neg = [b for b in bs if b["printed"] < 0]
            else:
                neg = [b for b in bs if b["units"] < 0]
            pos = [b for b in bs if b["units"] > 0]
            if neg and pos:
                add("wrong", part="batch", k20=k, item=bs[0]["item"], batch=";".join(b["batch"] or "-" for b in neg), expiry="",
                    units=sum(b["units"] for b in neg), pack=bs[0]["pack"], packing=bs[0]["packing"],
                    last_sale=last_sale.get(k), last_buy=last_buy.get(k),
                    info=dict(below=[[b["batch"] or "", qty_txt(b["units"], b["pack"]), b.get("_named") or "", int(b["units"])] for b in neg],
                              has=[[b["batch"] or "", qty_txt(b["units"], b["pack"]), b.get("expiry") or "", int(b["units"])] for b in pos]))
        run["_bt"], run["_sales_after"], run["_bought"] = bt, sales_after, bought_since    # S690: for the fixes (never persisted)
        run["note"] = (run["note"] + (" | " if run["note"] else "") + "S693: %d purchase line(s) since %s placed on %d batch(es), %d new; untied %s"
                       % (s693_placed, sales_after, len({kk for kk in bt if bt[kk].get("bought")}), len([kk for kk in bt if bt[kk].get("new")]),
                          ",".join(sorted(s693_untied))[:200] or "none"))[:900]
        nob = {}
        for w in new_wrong:
            if w["date"] >= this_m + "-01":
                nob.setdefault(w["k20"], []).append(w)
        for k, ws in sorted(nob.items()):
            bs = by_item.get(k) or []
            add("wrong", part="nobatch", k20=k, item=(bs[0]["item"] if bs else k), batch="", expiry="", units=sum(w["units"] for w in ws),
                pack=(bs[0]["pack"] if bs else 1), packing=(bs[0]["packing"] if bs else ""),
                last_sale=max(w["date"] for w in ws), last_buy=None,
                info=dict(lines=len(ws), first=min(w["date"] for w in ws),
                          has=[[b["batch"] or "", qty_txt(b["units"], b["pack"]), b.get("expiry") or "", int(b["units"])] for b in bs if b["units"] > 0]))
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


EFF_LINE_S693 = ("EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL AND e.md5=l.source_md5)")   # purchase_app.EFF_LINE


def _s693_alnum(b):
    return re.sub(r'[^A-Z0-9]', '', nbatch(b))


def _s693_fits(x, a):
    return bool(x) and len(a) >= 4 and len(x) >= 4 and (x == a or x.endswith(a) or a.endswith(x))


def _s693_tie(cands, pb):
    """The ONE batch among cands (bt keys of one medicine) whose letters-and-digits equal, or end with, the printed batch pb
    (the purchase item report prints the last 8 characters of a batch; 4+ characters; either may be the clip of the other, so a sale
    printing a batch in full ties to a new batch made from the report's clip).  -> the key, or None (none, or more than one)."""
    a = _s693_alnum(pb)
    if len(a) < 4:
        return None
    hit = [kk for kk in cands if kk[1] and _s693_fits(_s693_alnum(kk[1]), a)]
    return hit[0] if len(hit) == 1 else None


def _s693_expiry(v):
    """The purchase line's expiry ('5/28', '12/2027', '2027-05') as the watch's YYYY-MM, else ''."""
    s = str(v or "").strip()
    m = re.match(r'^(\d{1,2})/(\d{2}|\d{4})$', s)
    if m:
        y = int(m.group(2))
        return "%04d-%02d" % (y + 2000 if y < 100 else y, int(m.group(1)))
    return s if re.match(r'^\d{4}-\d{2}$', s) else ""


def _s693_place(con, bt, order, key, is_o, sales_after):
    """S693 (plan step 3): new stock placed on its batch from the purchase item report (purchase_line, effective exports, PURCHASE,
    bill date after the report's day, medicines).  Writes into bt: units (+ the purchase), bought (+), and a NEW batch for one the
    Batch Stock does not print (printed 0, new 1).  -> (by_k: medicine -> its bt keys; tied: medicines whose every such line was placed;
    untied: medicines with a line that could not be placed; placed: the count of lines placed; placed_units: units placed per medicine).
    Reads only; fail-soft: nothing placed."""
    by_k = {}
    for kk in order:
        by_k.setdefault(kk[0], []).append(kk)
    tied, untied, placed = set(), set(), 0
    placed_units = {}
    if not _has(con, "purchase_line") or not _has(con, "purchase_export"):
        return by_k, tied, untied, placed, placed_units
    try:
        rows = con.execute("SELECT l.item, l.packing, l.batch, l.expiry, l.qty, l.free, l.loose_qty, l.supplier_norm, l.bill_no, l.bill_date "
                           "FROM purchase_line l WHERE l.bill_date > ? AND l.direction='PURCHASE' AND COALESCE(l.line_type,'ITEMWISE')='ITEMWISE' AND "
                           + EFF_LINE_S693 + " ORDER BY l.bill_date, l.id", (sales_after,)).fetchall()
    except sqlite3.Error:
        return by_k, tied, untied, placed, placed_units
    seen = set()
    for item, packing, batch, expiry, qty, free, loose, sup, bill, bdate in rows:
        if is_o(item, packing or ""):
            continue
        line_key = (sup, bill, bdate, item, nbatch(batch or ""), qty, free, loose)    # S227: the same bill line in two overlapping exports counts once
        if line_key in seen:
            continue
        seen.add(line_key)
        k = key(item)
        pb = nbatch(batch or "")
        pack = pack_of(packing or "")
        # units = Marg's own LOOS figure: the Batch Stock's unit (THIO Q AP 1*10: bought 10 + 2 free, loose 12, printed 12; CCM 1*40: loose 5,
        # printed 5) -- NOT the count's tablet rule (stock_app._purchase_units), which would place 132 and 205 against a print of 12 and 5
        units = int(round(loose)) if loose is not None else int(round(((qty or 0) + (free or 0)) * pack))
        if not pb or units <= 0:
            untied.add(k)
            continue
        cands = by_k.get(k, [])
        kk = (k, pb) if (k, pb) in bt else _s693_tie(cands, pb)
        if kk is None:
            a = _s693_alnum(pb)
            if any(kk2[1] and _s693_fits(_s693_alnum(kk2[1]), a) for kk2 in cands):
                untied.add(k)                             # two batches fit the printed piece
                continue
            kk = (k, pb)                                  # a batch the Batch Stock does not print: new
            base = bt[cands[0]] if cands else {}
            bt[kk] = dict(item=base.get("item", item), k20=k, packing=base.get("packing", packing or ""), pack=base.get("pack", pack),
                          batch=pb, expiry=_s693_expiry(expiry), units=0, printed=0, sold=0, bought=0, new=1)
            order.append(kk)
            by_k.setdefault(k, []).append(kk)
        x = bt[kk]
        x["units"] += units
        x["bought"] = x.get("bought", 0) + units
        if not x.get("expiry") and expiry:
            x["expiry"] = _s693_expiry(expiry)
        tied.add(k)
        placed += 1
        placed_units[k] = placed_units.get(k, 0) + units
    tied -= untied
    return by_k, tied, untied, placed, placed_units


def _s693_sale_tie(bt, by_k, k, nb):
    """A sale line's batch not printed as such on the Batch Stock: the one batch of the medicine it fits (letters and digits), else None."""
    return _s693_tie(by_k.get(k, []), nb)


def _sales_after(R):
    """S668 (D740, the owner 27-Oct-2026): the day whose END a Batch Stock stands for -- the estate's one capture-hour rule,
    stock_figure.end_day, on the file's own stamp (BATCH_STOCK_..__<as_on>__<YYYYMMDD-HHMMSS>__<md5>): a print taken before 09:00 on its own
    day is the START of that day, so that day's sales are taken off; after 22:00, or a print for an earlier day, stands for its own day; a
    same-day print in shop hours (the rule says None) keeps its own day, as before S668. Fail-soft: the printed day."""
    as_on = R.get("as_on")
    m = re.search(r"__(\d{8}-\d{6})__", str(R.get("name") or ""))
    try:
        import stock_figure                                   # noqa: PLC0415
        e = stock_figure.end_day(as_on, stock_figure.stamp_iso(m.group(1))) if m else None
    except Exception:                                         # noqa: BLE001
        e = None
    return e or as_on


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


KIT_S883 = "S883_LEDGER_BATCHES"   # 18-Nov-2026 (the owner, 19:22-19:45 IST): the item ledger shows each item's batches with expiry


def batch_now_ensure(con):
    """S883: stock_batch_now -- the newest run's batches, every item, every batch (the run's own bt: Marg's whole-shop Batch Stock, less the
    sales since on their own batch, plus purchases placed on their batch). One run's rows at a time; nothing else reads or writes it."""
    con.execute("""CREATE TABLE IF NOT EXISTS stock_batch_now (
        id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL, at TEXT, as_on TEXT, sales_after TEXT, sales_to TEXT, k20 TEXT NOT NULL, item TEXT,
        batch TEXT, expiry TEXT, units INTEGER, printed INTEGER, sold INTEGER, bought INTEGER, new INTEGER, pack INTEGER, packing TEXT)""")
    con.execute("CREATE INDEX IF NOT EXISTS ix_stock_batch_now_k20 ON stock_batch_now (k20)")


def batch_now_write(con, rid, r):
    """S883: replace stock_batch_now with this run's batches. -> rows written. A run that used no whole-shop Batch Stock writes nothing and
    leaves the last good rows (they carry their own Batch Stock date)."""
    bt = r.get("_bt")
    if not bt:
        return 0
    batch_now_ensure(con)
    rows = []
    for (k, _b), x in bt.items():
        rows.append((rid, r.get("at"), r.get("export_as_on"), r.get("_sales_after"), r.get("sales_to"), x.get("k20") or k, x.get("item"),
                     x.get("batch") or "", x.get("expiry") or "", int(round(x.get("units") or 0)), int(round(x.get("printed") or 0)),
                     int(round(x.get("sold") or 0)), int(round(x.get("bought") or 0)), 1 if x.get("new") else 0, int(x.get("pack") or 1),
                     x.get("packing") or ""))
    con.execute("DELETE FROM stock_batch_now")
    con.executemany("INSERT INTO stock_batch_now (run_id, at, as_on, sales_after, sales_to, k20, item, batch, expiry, units, printed, sold, "
                    "bought, new, pack, packing) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    return len(rows)


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
        try:                                                  # S883: every batch of every item as this run left it -- the item ledger's Batches box
            with con:
                n_b = batch_now_write(con, rid, r)
            log("expiry_watch %s: %d batch row(s) kept for the item ledger" % (KIT_S883, n_b))
        except Exception as ex:                               # noqa: BLE001 -- the lists stand; the ledger shows the older batch rows with their date
            try:
                con.rollback()
            except sqlite3.Error:
                pass
            log("expiry_watch %s: the batch rows failed and were rolled back (%s: %s); the lists stand" % (KIT_S883, type(ex).__name__, str(ex)[:120]))
        judged, made = [], []
        try:                                                  # S690: the voucher pair -- a new report judges, the run names; never the run's own
            with con:
                fixes_ensure(con)
                judged = fixes_judge(con, sp, alias, rid, r, r["at"])
                made = fixes_create(con, rid, r, lines, r["at"])
        except Exception as ex:                               # noqa: BLE001
            log("expiry_watch %s: the fixes failed and were rolled back (%s: %s); the lists stand" % (KIT, type(ex).__name__, str(ex)[:120]))
        log("expiry_watch %s: run %d · export %s (as on %s) · %s · fixes judged %d, new %d · %s" % (KIT, rid, (r.get("export_name") or "none")[:70],
                                                                         r.get("export_as_on") or "-", r.get("counts"), len(judged), len(made), (r.get("note") or "")[:200]))
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
    rows = []                                                 # S690: the Batch Stock is step 4's third export now (amir_day)
    run_, sec = newest(con)
    sec = now_view(sec, today)
    if run_:
        ex = [x for x in sec.get("expired", []) if x["units"] > 0]
        if ex:
            li = "".join("<li>%s &middot; <span style='font-family:monospace'>%s</span> &middot; %s</li>"
                         % (esc(x["item"]), esc(x["batch"] or "-"), esc(qty_txt(x["units"], x["pack"]))) for x in ex)
            rows.append(("expired", "<div class='line s638exp'><span class=big>Marg mein expiry write-off ya stockist ko return karein:</span>"
                         "<ul>%s</ul></div>" % li, "expired batches to write off or return: %d" % len(ex), False))
    rows.extend(fixes_rows(con, today))                       # S690: the voucher pair, the confirmation, the done list
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
    head = ('<div class="wrap"><h1>Expiry, dump and stock-out watch</h1>') + _hand_section(con, today)   # S706 (D828): on top, collapsed
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
                  (('<p class="note">Sold this month with no batch at all (%d items): %s.</p>'
                   % (len(nb), esc(", ".join("%s (%d)" % (x["item"], (x["info"] or {}).get("lines", 0)) for x in nb)))) if nb else "")
                  + fixes_owner_line(con)))
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


def _hand_section(con, today):
    """S706 (D828, the owner 05-Nov): Marg's stock changed with no sale, bill or voucher -- on top of this page, collapsed, the red count
    when something new was found.  Reads marg_hand_change only (its rows are made by owner_notice's tick); never raises."""
    try:
        return _hand_section_body(con, today)
    except Exception as e:                                        # noqa: BLE001
        return '<p class="sub bad">Stock changed in Marg by hand: not readable (%s).</p>' % esc(e.__class__.__name__)


def _hand_section_body(con, today):
    import marg_hand_change as H                                  # noqa: PLC0415
    rows = H.rows_for_page(con)
    openr = [r for r in rows if r["status"] == "open" and r["kind"] == "hand"]
    ren = [r for r in rows if r["status"] == "open" and r["kind"] == "rename"]
    floor = (today - dt.timedelta(days=30)).isoformat()
    done = [r for r in rows if r["status"] != "open" and (r["status_at"] or "")[:10] >= floor]
    new = [r for r in openr if H.is_new(con, r, today)]
    badge = ('<span class="count red">%d new</span>' % len(new) if new else "") + \
            ' <span class="count %s">%d open</span>' % ("amber" if openr else "", len(openr))

    def card(r, hi):
        return ('<div style="padding:8px 0;border-bottom:1px solid var(--line)%s"><div><b>%s</b> '
                '<span class="m">%s &rarr; %s (%s)</span> <span class="note" style="margin:0">%s &ndash; %s</span>%s</div>'
                '<div style="font-size:.86rem">%s</div><div style="font-size:.86rem;color:var(--accent)">%s</div></div>'
                % (";background:var(--red-soft)" if hi else "", esc(r["item"]), esc(H.num(r["marg_from"])), esc(H.num(r["marg_to"])),
                   esc(H.snum(r["shift"])), esc(dmon(r["day_from"])), esc(dmon(r["day_to"])), ' <span class="tag">new</span>' if hi else "",
                   esc(H.why_of(r)), esc(H.remedy_of(r))))
    body = "".join(card(r, r in new) for r in sorted(openr, key=lambda r: (r in new, r["day_to"], r["item"]), reverse=True))
    parts = ['<p class="what">Marg\'s stock moved and nothing in the system explains it &mdash; no sale, bill or voucher. Marg went '
             '<b>from &rarr; to</b> (the shift) between the two days. You are told the morning after it is found.</p>',
             '<div style="margin-left:20px">%s</div>' % (body or '<p class="note">None.</p>')]
    if ren:
        parts.append('<details class="inner"><summary><h3>Renamed in Marg &mdash; no stock moved</h3><span class="count">%d</span></summary>'
                     '<div style="margin-left:20px">%s</div></details>' % (len(ren), "".join(card(r, False) for r in ren)))
    if done:
        parts.append('<details class="inner"><summary><h3>Put right or explained &mdash; last 30 days</h3><span class="count">%d</span>'
                     '</summary>%s</details>' % (len(done), _tbl(("Item", "Days", "Shift", "Now"), "".join(
                         '<tr><td>%s</td><td class="m">%s &ndash; %s</td><td class="m n">%s</td><td>%s</td></tr>'
                         % (esc(r["item"]), esc(dmon(r["day_from"])), esc(dmon(r["day_to"])), esc(H.snum(r["shift"])),
                            esc("put right in Marg" if r["status"] == "put right" else "explained by a later bill or voucher"))
                         for r in done), (2,))))
    return ('<details class="screen" id="hand" style="margin:10px 0 12px"><summary><h3>Stock changed in Marg without a bill or voucher</h3>'
            '%s</summary>%s</details>' % (badge, "".join(parts)))


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
# ==========================================================================================================================================
# S690_AMIR_BATCH_FIX (01-Nov-2026; the owner's rulings of 30-Oct, his "MOCKUP IS GOOD" of 31-Oct) -- a wrong batch is corrected by a
# voucher pair, never by a sale bill; the Batch Stock at the end of every visit confirms it.
#   * stock_batch_fix: one row per minus batch the watch names (a wrong/batch line's below, or a no-batch sale): the STOCK RECEIVE into the
#     minus batch and the STOCK ISSUE from the batch that has the stock (the earliest expiry with stock; split when short), FROZEN when
#     made (D542: a round is never re-edited; a later difference is a new row after the next report).
#   * fixes_create at every run; fixes_judge at a run whose Batch Stock is a NEW report: the Receive is done when the minus batch's printed
#     figure is no longer below zero; the Issue is done when the issue batch's printed figure has dropped by the voucher beyond its sales
#     between the two reports -> done / receive_only / issue_only / open.  An item bought between the reports is judged on the Receive.
#     Until the spine holds the report day's sales (sales_to >= the report's day) only the Receive is judged; the Issue waits for the
#     next run (the nightly, after the day's sale export) -- a fast mover's Issue is never called done on sales not yet counted.
#     A minus that moved while nothing of its rows was done: the rows are superseded and remade from the new report (one round).
#   * fixes_rows (Amir's card): the confirmation (a report judged in the last 24 h), the done list, the vouchers -- max VOUCHER_LINES a
#     voucher, the Receive set then the Issue set, numbered from 1.  his_line False: monthly work, never a gate (D708 / D712).
#   * batch_stock_state: step 4's third export -- none / wait / ok / bad, from mi_file and the newest run.
#   * new_batch_stock: run --if-new runs the watch only when a Batch Stock newer than the newest run has reached the door.
# ==========================================================================================================================================
FIX_KIT = "S690_AMIR_BATCH_FIX"
VOUCHER_LINES = 6
FIX_OPEN = ("open", "receive_only", "issue_only")


def fixes_ensure(con):
    con.execute("CREATE TABLE IF NOT EXISTS stock_batch_fix (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, k20 TEXT NOT NULL, "
                "item TEXT NOT NULL, pack INTEGER NOT NULL, minus_batch TEXT NOT NULL, units INTEGER NOT NULL, issue_batch TEXT NOT NULL, "
                "issue_printed INTEGER, issue_expiry TEXT, asked_run_id INTEGER NOT NULL, asked_md5 TEXT, asked_day TEXT, "
                "asked_at TEXT NOT NULL, status TEXT NOT NULL, judged_run_id INTEGER, judged_md5 TEXT, judged_at TEXT, done_at TEXT, note TEXT)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_stock_batch_fix_status ON stock_batch_fix (status, k20, minus_batch)")


def _fix_rows(con, where, args=()):
    cols = [d[0] for d in con.execute("SELECT * FROM stock_batch_fix LIMIT 0").description]
    return [dict(zip(cols, tuple(r))) for r in con.execute("SELECT * FROM stock_batch_fix WHERE " + where + " ORDER BY id", args)]


def _fix_same_batch(a, b):
    """The same batch typed differently: equal once upper-cased, stripped of spaces and punctuation and read with I as 1 and O as 0
    (GIF005003 = G1F005003), or the same digits, leading zeros aside, four or more (62607 = SL062607, TSF B1222 = TSF E1222)."""
    def norm(x):
        return re.sub(r"[^A-Z0-9]", "", str(x or "").upper()).replace("I", "1").replace("O", "0")
    def digs(x):
        return re.sub(r"[^0-9]", "", str(x or "")).lstrip("0")
    na, nb = norm(a), norm(b)
    if na and na == nb:
        return True
    da, db = digs(a), digs(b)
    return len(da) >= 4 and da == db


def _fix_issue_order(minus_batch, has):
    """The batches to issue from, in order: the SAME batch typed differently first (the digits agree, 4 or more; the larger stock
    first -- SYSFOL 62607 is SL062607, MEG QCS TSF B1222 is TSF E1222), then the earliest expiry with the larger stock first."""
    same = [h for h in has if _fix_same_batch(minus_batch, h[0])]
    rest = [h for h in has if h not in same]
    return (sorted(same, key=lambda h: (-int(h[3]), h[0]))
            + sorted(rest, key=lambda h: (h[2] or "9999-99", -int(h[3]), h[0])))


def fixes_create(con, rid, r, lines, at):
    """One row per minus batch the run names that no open row covers.  The Issue from the earliest-expiry batch with stock, split when
    that batch is short; what no batch can cover is left (the owner's page says so).  Returns [(item, minus batch, units, issue batch)]."""
    bt = r.get("_bt") or {}
    have = {(x["k20"], x["minus_batch"]) for x in _fix_rows(con, "status IN (?,?,?)", FIX_OPEN)}
    made = []
    for x in lines:
        if x.get("section") != "wrong" or x.get("part") not in ("batch", "nobatch"):
            continue
        info = x.get("info") or {}
        if isinstance(info, str):
            try:
                info = json.loads(info)
            except ValueError:
                info = {}
        pack = int(x.get("pack") or 1)
        has_all = [h for h in info.get("has", []) if len(h) >= 4 and int(h[3] or 0) > 0]
        if x["part"] == "batch":
            below = [(b[0] or "", -int(b[3])) for b in info.get("below", []) if len(b) >= 4 and int(b[3] or 0) < 0]
        else:
            below = [("", int(x.get("units") or 0))]
        left = {h[0]: int(h[3]) for h in has_all}
        for mb, need in below:
            if need <= 0 or (x["k20"], mb) in have:
                continue
            has = _fix_issue_order(mb, has_all)
            for h in has:
                if need <= 0:
                    break
                take = min(left.get(h[0], 0), need)
                if take <= 0:
                    continue
                pr = (bt.get((x["k20"], h[0])) or {}).get("printed")
                con.execute("INSERT INTO stock_batch_fix (kind, k20, item, pack, minus_batch, units, issue_batch, issue_printed, issue_expiry, "
                            "asked_run_id, asked_md5, asked_day, asked_at, status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (x["part"], x["k20"], x["item"], pack, mb, take, h[0], pr, h[2] or "", rid, r.get("export_md5"),
                             r.get("_sales_after") or r.get("export_as_on") or "", at, "open"))
                left[h[0]] -= take
                need -= take
                made.append((x["item"], mb, take, h[0]))
            have.add((x["k20"], mb))
    return made


def fixes_judge(con, sp, alias, rid, r, at):
    """At a run whose Batch Stock is a NEW report (not the one a row was asked on, not one it was judged on): the printed figures decide."""
    md5, bt = r.get("export_md5"), r.get("_bt")
    if not md5 or not bt:
        return []
    new_after = r.get("_sales_after") or r.get("export_as_on") or ""
    caught_up = (r.get("sales_to") or "") >= new_after          # the spine holds the report day's sales: the Issue can be judged
    out = []
    for f in _fix_rows(con, "status IN (?,?,?) AND COALESCE(asked_md5,'')<>? AND COALESCE(judged_md5,'')<>?", FIX_OPEN + (md5, md5)):
        pm = (bt.get((f["k20"], f["minus_batch"])) or {}).get("printed", 0) or 0
        receive_done = pm >= 0
        if not caught_up:                                      # the Receive is read off the print now; the Issue waits for the sales
            st = "receive_only" if receive_done else "open"
            con.execute("UPDATE stock_batch_fix SET status=?, judged_run_id=?, judged_at=?, note=? WHERE id=?",
                        (st, rid, at, "issue pending the day's sales (%s)" % md5[:8], f["id"]))
            out.append((f["item"], f["minus_batch"], st + " (issue pending)"))
            continue
        pi_new = (bt.get((f["k20"], f["issue_batch"])) or {}).get("printed", 0) or 0
        pi_old = f.get("issue_printed")
        sold = 0
        try:
            for l in sp.execute("SELECT l.k20, l.batch, l.units, COALESCE(b.credit_note, 0) AS cn FROM sp_sale_line l "
                                "LEFT JOIN sp_sale_bill b ON b.date = l.date AND b.bill = l.bill WHERE l.date > ? AND l.date <= ?",
                                (f.get("asked_day") or "", new_after)):
                if alias.get(l["k20"], l["k20"]) == f["k20"] and nbatch(l["batch"]) == f["issue_batch"]:
                    sold += int(round(l["units"] or 0)) * (-1 if l["cn"] else 1)
        except sqlite3.Error:
            sold = 0
        try:                                                   # bought between the two reports: the Issue cannot be read off the figure
            bought_between = sp.execute("SELECT 1 FROM sp_move WHERE k20=? AND kind='PURCHASE' AND date > ? AND date <= ? LIMIT 1",
                                        (f["k20"], f.get("asked_day") or "", new_after)).fetchone() is not None
        except sqlite3.Error:
            bought_between = False
        if bought_between or pi_old is None:
            issue_done = receive_done                          # a re-supply moved the figure: the Receive alone is judged
        else:
            issue_done = pi_new <= int(pi_old) - sold - int(f["units"])
        st = "done" if (receive_done and issue_done) else ("receive_only" if receive_done else ("issue_only" if issue_done else "open"))
        units = int(f["units"])
        if st == "issue_only" and pm < 0:
            units = -pm                                        # the Receive still needed is the minus as it stands now, not the asked figure
        con.execute("UPDATE stock_batch_fix SET status=?, units=?, judged_run_id=?, judged_md5=?, judged_at=?, note=NULL, "
                    "done_at=CASE WHEN ?='done' THEN ? ELSE done_at END WHERE id=?", (st, units, rid, md5, at, st, at, f["id"]))
        out.append((f["item"], f["minus_batch"], st))
    # a minus batch whose figure MOVED while nothing of its rows was done: those rows are superseded, and fixes_create (next) makes the
    # current ones from this report -- one round, the figures of today (a row half done is never touched: D542)
    for k20, mb in {(f["k20"], f["minus_batch"]) for f in _fix_rows(con, "status='open' AND judged_run_id=?", (rid,))}:
        rows = _fix_rows(con, "k20=? AND minus_batch=? AND status IN (?,?,?)", (k20, mb) + FIX_OPEN)
        if any(x["status"] != "open" for x in rows):
            continue
        pm = (bt.get((k20, mb)) or {}).get("printed", 0) or 0
        if pm < 0 and -pm != sum(int(x["units"]) for x in rows):
            con.execute("UPDATE stock_batch_fix SET status='superseded', note=? WHERE k20=? AND minus_batch=? AND status='open'",
                        ("the minus moved to %d on %s; remade" % (pm, md5[:8]), k20, mb))
            out.append((rows[0]["item"], mb, "superseded"))
    return out


def _fix_chunks(lines):
    return [lines[i:i + VOUCHER_LINES] for i in range(0, len(lines), VOUCHER_LINES)]


def _fix_bname(b):
    return esc(b) if b else "bina batch"


def fixes_rows(con, today=None):
    """Amir's card rows (amir_day's shape): the confirmation line, the done list, the vouchers.  Nothing when there is nothing."""
    today = today or now_ist().date()
    if not _has(con, "stock_batch_fix"):
        return []
    try:
        opn = _fix_rows(con, "status IN (?,?,?)", FIX_OPEN)
        since = (now_ist() - dt.timedelta(hours=24)).replace(microsecond=0).isoformat()
        done = _fix_rows(con, "status='done' AND COALESCE(done_at,'')>=?", (since,))
        judged = con.execute("SELECT MAX(judged_at), MAX(judged_run_id) FROM stock_batch_fix WHERE COALESCE(judged_at,'')>=?", (since,)).fetchone()
    except sqlite3.Error:
        return []
    html = []
    if judged and judged[0]:
        hhmm = str(judged[0])[11:16]
        jr = con.execute("SELECT export_md5, at FROM stock_expiry_run WHERE id=?", (judged[1],)).fetchone() if judged[1] else None
        if jr:
            try:
                got = con.execute("SELECT received_at FROM mi_file WHERE md5=? LIMIT 1", (jr[0],)).fetchone()
                if got and got[0]:
                    hhmm = str(got[0])[11:16]
            except sqlite3.Error:
                pass
        pend = [x for x in opn if (x.get("judged_at") or "") >= since]
        html.append("<div class='line s690conf'><span class='big good'>Batch Stock mil gayi %s &#10003; &mdash; %d batch theek ho gaye, %d abhi baaki</span>"
                    % (esc(hhmm), len(done), len(pend)))
        if done:
            html.append("<div class=s690done style='background:#f2f9f4;border:1px solid #bfe0c6;border-radius:10px;padding:8px 12px;margin:8px 0 0'>"
                        "<b>Theek ho gaya &#10003;</b> (yeh line kal hat jayegi)<ul style='margin:6px 0 0;padding-left:20px'>%s</ul></div>"
                        % "".join("<li>%s &middot; <span style='font-family:monospace'>%s</span></li>" % (esc(x["item"]), _fix_bname(x["minus_batch"])) for x in done))
        if pend:
            li = []
            for x in pend:
                q = qty_txt(x["units"], x["pack"])
                if x["status"] == "receive_only" and str(x.get("note") or "").startswith("issue pending"):
                    li.append("<li><b>%s</b> &mdash; Receive ho gaya &#10003;; Issue ki jaanch kal subah (aaj ki sale ginne ke baad)</li>" % esc(x["item"]))
                elif x["status"] == "receive_only":
                    li.append("<li><b>%s</b> &mdash; Receive ho gaya &#10003;, Issue baaki: <span style='font-family:monospace'>%s</span> se <b>%s</b> issue karein</li>"
                              % (esc(x["item"]), esc(x["issue_batch"]), esc(q)))
                elif x["status"] == "issue_only":
                    li.append("<li><b>%s</b> &mdash; Issue ho gaya &#10003;, Receive baaki: <span style='font-family:monospace'>%s</span> mein <b>%s</b> receive karein</li>"
                              % (esc(x["item"]), _fix_bname(x["minus_batch"]), esc(q)))
                else:
                    li.append("<li><b>%s</b> &mdash; dono baaki: Receive <span style='font-family:monospace'>%s</span> %s &middot; Issue <span style='font-family:monospace'>%s</span> %s</li>"
                              % (esc(x["item"]), _fix_bname(x["minus_batch"]), esc(q), esc(x["issue_batch"]), esc(q)))
            html.append("<div class=s690open style='background:#fff8e6;border:1px solid #f0c36d;border-radius:10px;padding:8px 12px;margin:8px 0 0'>"
                        "<b>Abhi baaki</b><ul style='margin:6px 0 0;padding-left:20px'>%s</ul></div>" % "".join(li))
        html.append("</div>")
    if opn:
        rec = [(x["item"], x["minus_batch"], qty_txt(x["units"], x["pack"])) for x in opn if x["status"] in ("open", "issue_only")]
        iss = [(x["item"], x["issue_batch"], qty_txt(x["units"], x["pack"])) for x in opn if x["status"] in ("open", "receive_only")]
        chunks = [("STOCK RECEIVE", c) for c in _fix_chunks(rec)] + [("STOCK ISSUE", c) for c in _fix_chunks(iss)]
        vs = []
        for n, (kind, c) in enumerate(chunks, 1):
            body = "".join("<tr><td>%s</td><td><span style='font-family:monospace'>%s</span></td><td style='text-align:right;white-space:nowrap;font-weight:600'>%s</td></tr>"
                           % (esc(it), _fix_bname(b), esc(q)) for it, b, q in c)
            vs.append("<div class=s690v style='border:1px solid #cfe0ef;border-radius:10px;background:#f3f7fb;padding:8px 12px;margin:0 0 10px'>"
                      "<h3 style='margin:0 0 6px;font-size:16px'>Voucher %d &mdash; %s (%d line)</h3>"
                      "<table style='width:100%%;border-collapse:collapse;font-size:15px'>%s</table></div>" % (n, kind, len(c), body))
        new_ones = [x for x in opn if (x.get("asked_at") or "") >= since and not x.get("judged_at")]
        head = ("Kal ki sale se %d naya &mdash; voucher Marg mein daaliye" % len(new_ones)) if (new_ones and len(new_ones) == len(opn) and judged and judged[0]) \
            else ("Batch theek karne ke %d voucher Marg mein daaliye" % len(chunks))
        html.append("<div class='line s690fix'><span class=big>%s</span>"
                    "<p class=sub style='margin:4px 0 10px'>Bill mat kholiye. Voucher jaisa likha hai waisa daaliye &mdash; batch bhi wahi chuniye jo likha hai. "
                    "Daal kar step 4 mein Batch Stock nikaaliye; jo theek ho gaya woh yahan se khud hat jayega. (Matra strip:tab)</p>%s"
                    "<p class=sub style='margin:0'>Dawa ki kul matra nahi badalti &mdash; sirf galat batch se sahi batch par jaati hai.</p></div>"
                    % (head, "".join(vs)))
    if not html:
        return []
    return [("batchfix", "".join(html), "batch vouchers: %d open, %d done in 24 h" % (len(opn), len(done)), False)]


def fixes_owner_line(con):
    """One line for the owner's page: the vouchers asked of Amir and where they stand."""
    if not _has(con, "stock_batch_fix"):
        return ""
    try:
        opn = _fix_rows(con, "status IN (?,?,?)", FIX_OPEN)
        nd = con.execute("SELECT COUNT(*), MAX(done_at) FROM stock_batch_fix WHERE status='done'").fetchone()
    except sqlite3.Error:
        return ""
    if not opn and not (nd and nd[0]):
        return ""
    half = [x for x in opn if x["status"] != "open"]
    bits = ["%d voucher line%s open with Amir" % (len(opn), "" if len(opn) == 1 else "s")]
    if half:
        bits.append("%d half done (%s)" % (len(half), ", ".join("%s: %s" % (x["item"], "Issue pending" if x["status"] == "receive_only" else "Receive pending") for x in half[:4])))
    if nd and nd[0]:
        bits.append("%d done, the last on %s" % (nd[0], dmon(str(nd[1] or "")[:10])))
    return '<p class="note">Batch fixes (S690): %s.</p>' % esc(" · ".join(bits))


def batch_stock_state(con, today=None):
    """Step 4's third export, from the door and the newest run: none | wait | ok | bad (+ at hh:mm, items, reason)."""
    today = today or now_ist().date()
    d = today.isoformat()
    try:
        r = con.execute("SELECT received_at, md5, server_name FROM mi_file WHERE type='BATCH_STOCK' AND verdict='VERIFIED' "
                        "AND (substr(stamp,1,8)=? OR substr(received_at,1,10)=?) ORDER BY received_at DESC LIMIT 1",
                        (d.replace("-", ""), d)).fetchone()
    except sqlite3.Error:
        r = None
    if not r:
        return dict(state="none")
    at = str(r[0])[11:16]
    run_, _sec = newest(con)
    if run_ and run_.get("export_md5") == r[1]:
        return dict(state="ok", at=at, items=run_.get("export_items") or 0, as_on=run_.get("export_as_on") or "")
    if run_ and str(run_.get("at") or "")[:19] > str(r[0])[:19]:
        note = run_.get("note") or ""
        if "filtered" in note and (r[2] or "")[:40] in note:
            return dict(state="bad", at=at, reason="poore store ki nahi thi")
        return dict(state="bad", at=at, reason="padhi nahi ja saki")
    return dict(state="wait", at=at)


def new_batch_stock(db):
    """True when a VERIFIED Batch Stock reached the door after the newest run (run --if-new)."""
    try:
        con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=10)
    except sqlite3.Error:
        return False
    try:
        if not _has(con, "mi_file"):
            return False
        r = con.execute("SELECT received_at, md5 FROM mi_file WHERE type='BATCH_STOCK' AND verdict='VERIFIED' ORDER BY received_at DESC LIMIT 1").fetchone()
        if not r:
            return False
        if not _has(con, "stock_expiry_run"):
            return True
        n = con.execute("SELECT at, export_md5 FROM stock_expiry_run ORDER BY id DESC LIMIT 1").fetchone()
        if not n:
            return True
        return str(r[0])[:19] > str(n[0])[:19] and n[1] != r[1]
    except sqlite3.Error:
        return False
    finally:
        con.close()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("run", "read", "show"))
    ap.add_argument("file", nargs="?")
    ap.add_argument("--db", default=DB_DEFAULT)
    ap.add_argument("--spine", default=SPINE_DEFAULT)
    ap.add_argument("--archive", default=ARCHIVE_DEFAULT)
    ap.add_argument("--date", default="")
    ap.add_argument("--if-new", action="store_true", help="S690: run only when a Batch Stock newer than the newest run has reached the door")
    a = ap.parse_args(argv)
    if a.cmd == "read":
        R = read_batch_stock(a.file)
        print("%s: %d batches, %d items, TOTAL %s, as on %s%s" % ("OK" if R["ok"] else "REFUSED", len(R["batches"]), R["items"], R["total"],
                                                                R["as_on"], ("" if R["ok"] else " -- " + "; ".join(R["failed"]))))
        return 0 if R["ok"] else 1
    if a.cmd == "run":
        if a.if_new and not new_batch_stock(a.db):
            return 0
        return run(a.db, a.spine, a.archive, dt.date.fromisoformat(a.date) if a.date else None)
    con = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
    r, sec = newest(con)
    print(json.dumps(r, indent=1))
    for k, v in sorted(sec.items()):
        print("%-8s %d" % (k, len(v)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
