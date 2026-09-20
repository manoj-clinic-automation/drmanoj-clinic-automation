"""marg_read.py -- S272 / kit S331 (Sanjeevni). The certified Marg readers.

One reader per Marg report family the spine uses. Every reader:
  * classifies EVERY row positively (page furniture is named, never guessed at);
  * runs the report's OWN witness (its printed totals, serial runs, footer counts);
  * returns a plain, JSON-safe READING: the facts the spine needs and nothing else.

Promoted from the S270 contract harness (MARG_REPORT_CONTRACT_v1, evidence\\contract_harness.py)
with three S272 changes, each tested in selftest_marg_read.py:
  1. Marg's advertising footer is recognised whatever its capitals ('Marg ERP' / 'MARG ERP').
  2. The purchase BILL-WISE report has a reader (it carries the supplier, the date and the SIGN
     of every bill -- a minus bill is a purchase RETURN, F-527).
  3. The sale DETAIL reading carries the bill money columns and NEVER the patient columns:
     a sale reading holds date, bill number, money, and item lines -- no name, no mobile.

Reads only. Writes nothing. Imports nothing from the live estate. Python 3.8+, xlrd + openpyxl.
"""
import collections
import datetime as dt
import hashlib
import os
import re

READER_VERSION = "S331.1"
SHOP = "SANJEEVNI MEDICOS"
RE_CONT = re.compile(r'^Continued\.+\s*\d*$', re.I)
RE_PAGENO = re.compile(r'^No\.+\s*\d+$', re.I)
RE_DATE = re.compile(r'^(\d{2})-(\d{2})-(\d{4})$')
RE_BILL_SALE = re.compile(r'^[A-Z]{1,3}\d{4,}$')


# ------------------------------------------------------------------ cells
def S(c):
    return (c or "").replace("\xa0", " ").strip()


def num(x):
    x = S(x).replace(",", "")
    try:
        return float(x)
    except ValueError:
        return None


def paise(x):
    v = num(x)
    return int(round(v * 100)) if v is not None else 0


def packn(p):
    m = re.match(r'^(\d+)\*(\d+)$', (p or "").rstrip('.'))
    return int(m.group(1)) * int(m.group(2)) if m else None


def iso(d):
    m = RE_DATE.match(d)
    return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else ""


def textno(v):
    """A document number as TEXT: Marg's grid stores '160' as 160.0 -- the '.0' is the grid's, not Marg's."""
    v = S(v)
    return v[:-2] if re.match(r'^\d+\.0$', v) else v


def rows_of(path):
    """Every cell as text, the way the S270 harness read them (xlrd for .xls, openpyxl for .xlsx)."""
    if path.lower().endswith(".xlsx"):
        try:
            import openpyxl
        except ImportError:                     # the box reads .xlsx with the collector's stdlib reader (S201)
            import sys
            sys.path.insert(0, "/root/marg_ingest")
            import xlsx_stdlib
            sh = xlsx_stdlib.open_workbook(path).sheet_by_index(0)
            return [[_cell(sh.cell_value(r, c)) for c in range(sh.ncols)] for r in range(sh.nrows)]
        ws = openpyxl.load_workbook(path, data_only=True, read_only=True).active
        return [[_cell(v) for v in r] for r in ws.iter_rows(values_only=True)]
    try:
        import xlrd
    except ImportError:                         # the box keeps xlrd vendored beside the collector (salts_refresh does the same)
        import sys
        sys.path.insert(0, "/root/marg_ingest")
        import xlrd
    sh = xlrd.open_workbook(path).sheet_by_index(0)
    out = []
    for r in range(sh.nrows):
        row = []
        for c in range(sh.ncols):
            v = sh.cell_value(r, c)
            row.append(repr(v) if sh.cell_type(r, c) == 3 else str(v))
        out.append(row)
    return out


def _cell(v):
    """An .xlsx cell as the text the readers expect: a whole number without '.0', exactly as openpyxl hands it."""
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def pad(r, n):
    return list(r) + [""] * (n - len(r))


def furniture(r, titles=()):
    """Page furniture, each named by what it is. Returns a class name or None."""
    cells = [S(c) for c in r]
    filled = [c for c in cells if c]
    j = " | ".join(cells)
    if not filled:
        return "BLANK"
    if "call marg" in j.lower() or "qrcode" in j.lower() or "marg erp" in j.lower():   # S272: any capitals
        return "ADVERT"
    if len(filled) == 1 and RE_CONT.match(filled[0]):
        return "CONTINUED"
    if len(filled) == 2 and filled[0].lower() == "page" and RE_PAGENO.match(filled[1]):
        return "PAGENO"
    if len(filled) == 1 and re.match(r'^Page\s*No\.+\s*\d+$', filled[0], re.I):
        return "PAGENO"
    if len(filled) == 1 and filled[0].upper() in (SHOP, "SANJEEVNI"):
        return "SHOPNAME"
    if len(filled) == 1 and (filled[0].startswith("35G/15B") or filled[0].startswith("Phone :")
                             or filled[0].startswith("D.L.No.") or filled[0].startswith("GSTIN")
                             or filled[0] == "BAREILLY" or filled[0].startswith("Mfg.Lic.No.")):
        return "LETTERHEAD"
    for t in titles:
        if len(filled) == 1 and re.search(t, filled[0], re.I):
            return "TITLE"
    return None


class Reading:
    """What a reader returns. .ok is True only when every witness check held and no row was unclassified."""

    def __init__(self, family):
        self.family = family
        self.classes = collections.Counter()
        self.checks = []          # (name, ok, detail)
        self.anomalies = []       # (row, kind, detail) -- never a patient cell
        self.data = {}

    def cls(self, k):
        self.classes[k] += 1

    def check(self, name, ok, detail=""):
        self.checks.append((name, bool(ok), str(detail)[:300]))

    @property
    def ok(self):
        return all(c[1] for c in self.checks) and not self.anomalies

    def failed(self):
        return [c[0] for c in self.checks if not c[1]] + ["%s at row %d" % (a[1], a[0]) for a in self.anomalies[:5]]


def qty_units(v, pack):
    """Marg stock quantity: '-'=0, 'a:b' = a packs + b loose, else a plain number."""
    v = S(v)
    if v in ("-", ""):
        return 0.0
    m = re.match(r'^(-?)(\d+):(\d+)$', v)
    if m:
        sg = -1 if m.group(1) else 1
        return float(sg * (int(m.group(2)) * (packn(pack) or 1) + int(m.group(3))))
    return float(v)


# ================================================================== ITEM LISTS (salt / category)
RE_ITEM = re.compile(r'^(\d+)\s{2,}(\S.*)$')


def read_grouped_list(rows, family, title_re):
    R = Reading(family)
    group = None
    want = None
    empty = []
    items = []
    for i, r in enumerate(rows):
        r = pad(r, 5)
        f = furniture(r, (title_re,))
        c0 = S(r[0])
        rest = [S(c) for c in r[1:]]
        if f is None and c0.upper().startswith("S.NO"):
            f = "COLHDR"
        if f:
            R.cls(f)
            continue
        m = RE_ITEM.match(c0)
        if re.match(r'^\d+(\.\d+)?$', c0):
            R.cls("ITEM_NO_NAME")
            if group is not None:
                R.anomalies.append((i, "STRAY", "a nameless serial inside a group"))
            continue
        if m:
            R.cls("ITEM")
            n = int(m.group(1))
            if group is None:
                R.anomalies.append((i, "ORPHAN", m.group(2)[:30]))
                continue
            if n != want:
                R.anomalies.append((i, "SERIAL", "serial %d under %r, expected %d" % (n, group, want)))
            want = n + 1
            items.append(dict(group=group, name=m.group(2).strip(), packing=rest[0], p_rate=num(rest[1]),
                              s_rate=num(rest[2]), mrp=num(rest[3])))
            continue
        if c0 and all((not x) or num(x) == 0 for x in rest):
            R.cls("HEADING")
            if group is not None and want == 1:
                empty.append(group)
            group, want = c0, 1
            continue
        R.cls("ANOMALY")
        R.anomalies.append((i, "UNCLASSIFIED", c0[:40]))
    if group is not None and want == 1:
        empty.append(group)
    R.check("serial restarts at 1 under every heading and never skips",
            not [a for a in R.anomalies if a[2].startswith("serial")])
    R.check("every heading carries at least one item", not empty, "%d empty: %s" % (len(empty), empty[:3]))
    R.check("no heading is the shop name or a title",
            not [d for d in items if d["group"].upper() in (SHOP, "SALT WISE ITEM LIST", "CATEGORY WISE ITEM LIST")])
    R.check("at least one item read", bool(items))
    R.data = dict(items=items)
    return R


# ================================================================== ITEM MASTER
def read_item_master(rows):
    R = Reading("ITEM_MASTER")
    want = 1
    items = []
    for i, r in enumerate(rows):
        r = pad(r, 6)
        f = furniture(r, (r'LIST\s+OF\s+ITEMS',))
        c0 = S(r[0])
        rest = [S(c) for c in r[1:]]
        if f is None and c0.upper().startswith("S.NO"):
            f = "COLHDR"
        if f is None and not c0 and rest[1:4] == ["P.RATE", "S.RATE", "M.R.P."]:
            f = "COLHDR2"
        if f:
            R.cls(f)
            continue
        m = RE_ITEM.match(c0)
        mb = re.match(r'^(\d+)(\.0)?$', c0)
        if m or mb:
            n = int((m or mb).group(1))
            name = m.group(2).strip() if m else ""
            R.cls("ITEM" if name else "ITEM_NO_NAME")
            if n != want:
                R.anomalies.append((i, "SERIAL", "serial %d, expected %d" % (n, want)))
            want = n + 1
            items.append(dict(name=name, packing=rest[0],
                              company=" ".join(x for x in rest[1:3] if x and num(x) is None).strip()))
            continue
        R.cls("ANOMALY")
        R.anomalies.append((i, "UNCLASSIFIED", c0[:40]))
    R.check("last serial equals the number of item rows", want - 1 == len(items), "%d vs %d" % (want - 1, len(items)))
    R.check("at least one item read", bool(items))
    R.data = dict(items=items)
    return R


# ================================================================== CLOSING STOCK (whole stores, totals)
def read_closing(rows):
    """Marg 'WHOLE STORES CLOSING STOCK AS ON dd-mm-yyyy' -- serial | description+packing | stock | unit."""
    R = Reading("STOCK_CLOSING")
    want = 1
    total = None
    tunits = 0.0
    as_on = ""
    items = []
    for i, r in enumerate(rows):
        r = pad(r, 4)
        c = [S(x) for x in r]
        t = re.search(r'CLOSING\s+STOCK\s+AS\s+ON\s+(\d{2}-\d{2}-\d{4})', c[0], re.I)
        if t and not any(c[1:]):
            R.cls("TITLE")
            as_on = iso(t.group(1))
            continue
        f = furniture(r, (r'CLOSING\s+STOCK',))
        if f is None and c[0].upper().startswith("S.NO"):
            f = "COLHDR"
        if f:
            R.cls(f)
            continue
        if c[0] == "TOTAL":
            R.cls("TOTAL")
            total = num(c[2])
            continue
        m = re.match(r'^(\d+)(\.0)?$', c[0])
        if not m:
            R.cls("ANOMALY")
            R.anomalies.append((i, "UNCLASSIFIED", c[0][:40]))
            continue
        n = int(m.group(1))
        R.cls("ITEM")
        if n != want:
            R.anomalies.append((i, "SERIAL", "serial %d, expected %d" % (n, want)))
        want = n + 1
        d = S(r[1])
        mm = re.match(r'^(.*?\S)\s{2,}(\S+)$', d)
        if mm:
            name, pack = mm.group(1), mm.group(2)
        else:                                   # a 29-character name leaves ONE space before the packing
            toks = d.split()
            name, pack = (" ".join(toks[:-1]), toks[-1]) if len(toks) >= 2 else (d, "")
        u = qty_units(c[2], pack)
        tunits += u
        items.append(dict(serial=n, name=name, packing=pack, qty_raw=c[2], units=u, unit=c[3],
                          plain=(":" not in c[2] and c[2] not in ("-", ""))))
    R.check("serial run 1..N unbroken", not [a for a in R.anomalies if a[1] == "SERIAL"])
    R.check("every row classified", not [a for a in R.anomalies if a[1] == "UNCLASSIFIED"])
    R.check("the report names its date", bool(as_on))
    R.check("TOTAL row present", total is not None)
    if total is not None:
        R.check("TOTAL units = sum of every line", abs(total - tunits) < 0.5, "printed %.1f, lines %.1f" % (total, tunits))
    R.data = dict(as_on=as_on, items=items, printed_total=total, lines_total=tunits)
    return R


# ================================================================== PURCHASE, BILL-WISE
def read_purchase_billwise(rows):
    """'BILL WISE PURCHASE STATEMENT FROM d TO d' -- date rows, then bill | party | cash | credit; TOTAL."""
    R = Reading("PURCHASE_BILLWISE")
    date = ""
    bills = []
    total = None
    period = ("", "")
    for i, r in enumerate(rows):
        r = pad(r, 4)
        c = [S(x) for x in r]
        t = re.search(r'BILL\s+WISE\s+PURCHASE\s+STATEMENT\s+FROM\s+(\S+)\s+TO\s+(\S+)', c[0], re.I)
        if t and not any(c[1:]):
            R.cls("TITLE")
            period = (iso(t.group(1)), iso(t.group(2)))
            continue
        f = furniture(r, (r'BILL\s+WISE\s+PURCHASE',))
        if f is None and c[0] == "BILL NO.":
            f = "COLHDR"
        if f:
            R.cls(f)
            continue
        if RE_DATE.match(c[0]) and not any(c[1:]):
            R.cls("DATE")
            date = iso(c[0])
            continue
        if c[0] == "TOTAL":
            R.cls("TOTAL")
            total = (num(c[1]) or 0) if num(c[1]) is not None else (num(c[3]) or 0)
            continue
        if c[0] and c[1] and (num(c[2]) is not None or num(c[3]) is not None) and date:
            R.cls("BILL")
            cash, credit = num(c[2]) or 0.0, num(c[3]) or 0.0
            amt = cash + credit
            bills.append(dict(date=date, bill=textno(c[0]), supplier=re.sub(r'\s+', ' ', c[1]).strip(),
                              cash_p=int(round(cash * 100)), credit_p=int(round(credit * 100)),
                              amount_p=int(round(amt * 100)), direction="RETURN" if amt < 0 else "PURCHASE"))
            continue
        R.cls("ANOMALY")
        R.anomalies.append((i, "UNCLASSIFIED", c[0][:30]))
    s = sum(b["amount_p"] for b in bills) / 100.0
    R.check("the report names its period", all(period))
    R.check("TOTAL row present", total is not None)
    if total is not None:
        R.check("TOTAL = sum of every bill", abs(total - s) < 0.5, "printed %.2f, bills %.2f" % (total, s))
    R.check("every row classified", not R.anomalies)
    R.data = dict(date_from=period[0], date_to=period[1], bills=bills)
    return R


# ================================================================== PURCHASE, ITEM-WISE (supplier/item and bill/item)
def split2(s):
    t = S(s).split()
    return (t[0] if t else ""), (" ".join(t[1:]) if len(t) > 1 else "")


def read_purchase_lines(rows):
    """SUPPLIER/ITEM WISE (grouped by supplier, no dates) or BILL/ITEM WISE (grouped by date, no supplier)."""
    grouping = None
    period = ("", "")
    for r in rows[:8]:
        c0 = S(pad(r, 1)[0])
        t = re.search(r'(SUPPLIER|BILL)/ITEM\s+WISE\s+PURCHASE\s+STATEMENT\s+FROM\s+(\S+)\s+TO\s+(\S+)', c0, re.I)
        if t:
            grouping = t.group(1).upper()
            period = (iso(t.group(2)), iso(t.group(3)))
    R = Reading("PURCHASE_ITEMWISE" if grouping == "SUPPLIER" else "PURCHASE_BILLITEMWISE")
    grp = [0.0, 0.0]
    allsum = [0.0, 0.0]
    grand = None
    bad_grp = []
    supplier = ""
    date = ""
    lines = []
    for i, r in enumerate(rows):
        r = pad(r, 12)
        f = furniture(r, (r'ITEM\s+WISE\s+PURCHASE',))
        c = [S(x) for x in r]
        if f is None and c[0] == "BILL" and c[1] == "ITEM DESCRIPTION":
            f = "COLHDR"
        if f:
            R.cls(f)
            continue
        if (c[0], c[1]) == ("GRAND", "TOTAL") or (c[0] == "TOTAL" and grouping == "BILL"):
            R.cls("GRAND_TOTAL")
            grand = (num(split2(c[9])[0]), num(c[11]))
            continue
        if c[7] == "TOTAL" and not c[0]:
            R.cls("GROUP_TOTAL")
            t = (num(split2(c[9])[0]), num(c[11]))
            if abs((t[0] or 0) - grp[0]) > 0.05 or abs((t[1] or 0) - grp[1]) > 0.05:
                bad_grp.append((supplier, t, tuple(round(x, 2) for x in grp)))
            grp = [0.0, 0.0]
            continue
        if RE_DATE.match(c[0]) and not any(c[1:]):
            R.cls("DATE")
            date = iso(c[0])
            continue
        money = [num(c[7]), num(c[11])]
        if all(x is None for x in money) and not any(c[4:12]) and any(c[:4]):
            R.cls("SUPPLIER_HEADING")
            supplier = re.sub(r'\s+', ' ', " ".join(x for x in c[:4] if x)).strip()
            grp = [0.0, 0.0]
            continue
        glued = None
        if not c[0] and c[1] and money[0] is not None and money[1] is not None:
            gm = re.match(r'^([A-Z]{1,3}-?\d{3,})([A-Z].*)$', c[1])
            if gm:
                glued = gm
        if (re.match(r'^[A-Za-z]{0,3}-?\d+(\.0)?$', c[0]) and c[1] and money[1] is not None) or glued:
            R.cls("ITEM_GLUED" if glued else "ITEM")
            bill, name = (glued.group(1), glued.group(2).strip()) if glued else (textno(c[0]), c[1])
            net_amt, net_rate = split2(c[9])
            loose, purc = split2(c[10])
            pk, batch = split2(c[2])
            qty, free, amt = num(c[5]), num(c[6]) or 0.0, num(c[11])
            lines.append(dict(seq=len(lines) + 1, bill=bill, supplier=supplier if grouping == "SUPPLIER" else "",
                              date=date if grouping == "BILL" else "", name=name, packing=pk,
                              batch=(batch + " " + c[3]).strip(), qty=qty, free=free, loose=num(loose),
                              rate=num(c[7]), purc=num(purc), net_amount_p=paise(net_amt), amount_p=paise(c[11]),
                              glued=bool(glued)))
            grp[0] += num(net_amt) or 0
            grp[1] += amt or 0
            allsum[0] += num(net_amt) or 0
            allsum[1] += amt or 0
            continue
        R.cls("ANOMALY")
        R.anomalies.append((i, "UNCLASSIFIED", c[0][:20] + "|" + c[1][:20]))
    R.check("the report names its grouping and period", grouping is not None and all(period))
    R.check("every row classified", not R.anomalies)
    R.check("closing total row present", grand is not None)
    if grand:
        R.check("closing total AMOUNT = sum of every line's AMOUNT", abs((grand[1] or 0) - allsum[1]) < 0.5,
                "%.2f vs %.2f" % (grand[1] or 0, allsum[1]))
        R.check("closing total NET = sum of every line's net amount", abs((grand[0] or 0) - allsum[0]) < 0.5,
                "%.2f vs %.2f" % (grand[0] or 0, allsum[0]))
    if grouping == "SUPPLIER":
        R.check("every supplier TOTAL re-adds its own lines", not bad_grp, str(bad_grp[:2]))
    R.data = dict(grouping=grouping, date_from=period[0], date_to=period[1], lines=lines)
    return R


# ================================================================== SALE, BILL-WISE DETAIL
def read_sale_detail(rows):
    """'BILL WISE SALES STATEMENT' DETAIL. Bill rows carry a patient's name and mobile in columns 2-3:
    those cells are NEVER read into the reading. Kept: date, bill no, the six money columns, and lines."""
    R = Reading("SALE_BILLWISE")
    bills = []
    cur = None
    date = ""
    grand = None
    nfoot = None
    days = []
    day_sum = 0.0
    for i, r in enumerate(rows):
        r = pad(r, 9)
        f = furniture(r, (r'BILL\s+WISE\s+SALES\s+STATEMENT',))
        c = [S(x) for x in r]
        if f is None and c[0] == "BILL NO.":
            f = "COLHDR"
        if f:
            R.cls(f)
            continue
        if RE_DATE.match(c[0]) and not any(c[1:]):
            R.cls("DATE")
            date = iso(c[0])
            day_sum = 0.0
            continue
        if c[2].startswith("DAY TOTAL"):
            R.cls("DAY_TOTAL")
            days.append((date, num(c[3]), round(day_sum, 2)))
            continue
        if c[0].startswith("Total No. of"):
            R.cls("GRAND_TOTAL")
            grand = num(c[3])
            nfoot = int(re.sub(r'\D', '', c[1]) or 0)
            continue
        if c[0].startswith("C/F") or c[1].startswith("C/F") or c[2].startswith("C/F") or c[2].startswith("B/F"):
            R.cls("CARRY")
            continue
        if RE_BILL_SALE.match(c[0]):
            R.cls("BILL")
            cur = dict(date=date, bill=c[0], gross_p=paise(c[3]), disc_p=paise(c[4]), tax_p=paise(c[5]),
                       drcr_p=paise(c[6]), net_p=paise(c[7]), cash_p=paise(c[8]),
                       credit_note=c[0].startswith("CN"), lines=[])
            bills.append(cur)
            day_sum += num(c[3]) or 0
            continue
        raw = S(r[1]) and r[1].replace("\xa0", " ")
        fm = re.match(r'^\s*(\d+)\s+(\d+|\*+)\s(.{1,20})(.*)$', raw or "") if not c[0] else None
        if fm and cur is not None:
            R.cls("ITEM")
            am = re.match(r'^(-?[\d.]+)(?:\s+(\d+/\d+))?$', c[3])
            cur["lines"].append(dict(seq=int(fm.group(1)), name=fm.group(3).strip(), pack=fm.group(4).strip(),
                                     qty=c[2], rate_p=int(round(float(am.group(1)) * 100)) if am else None,
                                     expiry=am.group(2) if am and am.group(2) else "", batch=textno(c[4])))
            continue
        R.cls("ANOMALY")
        R.anomalies.append((i, "UNCLASSIFIED", "(row not quoted)"))
    R.check("GRAND TOTAL = sum of bill GROSS", grand is not None and abs(grand - sum(b["gross_p"] for b in bills) / 100.0) < 0.5,
            "%s vs %.2f" % (grand, sum(b["gross_p"] for b in bills) / 100.0))
    R.check("footer bill count = bills read", nfoot == len(bills), "%s vs %d" % (nfoot, len(bills)))
    R.check("every DAY TOTAL = its bills", all(d[1] is not None and abs(d[1] - d[2]) < 0.5 for d in days),
            str([d for d in days if d[1] is None or abs(d[1] - d[2]) >= 0.5][:3]))
    R.check("line numbers run 1..n inside every bill",
            all([l["seq"] for l in b["lines"]] == list(range(1, len(b["lines"]) + 1)) for b in bills))
    R.check("every bill has a date", all(b["date"] for b in bills))
    R.check("every row classified", not R.anomalies)
    ds = sorted({b["date"] for b in bills})
    R.data = dict(date_from=ds[0] if ds else "", date_to=ds[-1] if ds else "", days=ds, bills=bills)
    return R


# ================================================================== identify + read one file
TITLES = [
    ("SALT_WISE_ITEM_LIST", r'SALT\s+WISE\s+ITEM\s+LIST'),
    ("CATEGORY_WISE_ITEM_LIST", r'CATEGORY\s+WISE\s+ITEM\s+LIST'),
    ("ITEM_MASTER", r'LIST\s+OF\s+ITEMS'),
    ("STOCK_CLOSING", r'WHOLE\s+STORES\s+CLOSING\s+STOCK'),
    ("PURCHASE_BILLWISE", r'^BILL\s+WISE\s+PURCHASE\s+STATEMENT'),
    ("PURCHASE_LINES", r'(SUPPLIER|BILL)/ITEM\s+WISE\s+PURCHASE\s+STATEMENT'),
    ("SALE_BILLWISE", r'^BILL\s+WISE\s+SALES\s+STATEMENT(\s+AS\s+ON\s+\S+|\s+FROM\s+\S+\s+TO\s+\S+)?$'),
]


def identify(rows):
    """By the report's own title and column header -- never by the file name."""
    head = [S(pad(r, 1)[0]) for r in rows[:10]]
    cols = [" | ".join(S(x) for x in r) for r in rows[:10]]
    for fam, t in TITLES:
        if any(re.search(t, h, re.I) for h in head):
            if fam == "SALE_BILLWISE" and not any(c.startswith("BILL NO. | DESCRIPTION | D.R.") for c in cols):
                return None          # summary layouts are not the DETAIL report
            if fam == "STOCK_CLOSING" and not any(c.startswith("S.No. | Description | Total Stock") for c in cols):
                return None          # batch-wise / category-filtered layouts are not used by the spine
            return fam
    return None


def read_file(path):
    """-> (family or None, Reading or None, md5). A family the spine does not use returns (None, None, md5)."""
    raw = open(path, "rb").read()
    md5 = hashlib.md5(raw).hexdigest()
    rows = rows_of(path)
    fam = identify(rows)
    if fam is None:
        return None, None, md5
    if fam == "SALT_WISE_ITEM_LIST":
        R = read_grouped_list(rows, fam, r'SALT\s+WISE\s+ITEM\s+LIST')
    elif fam == "CATEGORY_WISE_ITEM_LIST":
        R = read_grouped_list(rows, fam, r'CATEGORY\s+WISE\s+ITEM\s+LIST')
    elif fam == "ITEM_MASTER":
        R = read_item_master(rows)
    elif fam == "STOCK_CLOSING":
        R = read_closing(rows)
    elif fam == "PURCHASE_BILLWISE":
        R = read_purchase_billwise(rows)
    elif fam == "PURCHASE_LINES":
        R = read_purchase_lines(rows)
    else:
        R = read_sale_detail(rows)
    return R.family, R, md5


STAMP_RE = re.compile(r'__(\d{8}-\d{6})__')
DAY_RE = re.compile(r'__(\d{4}-\d{2}-\d{2})__')


def reading_record(path, source_name=None):
    """The JSON-safe record the evidence store keeps for one file."""
    fam, R, md5 = read_file(path)
    name = source_name or os.path.basename(path)
    m = STAMP_RE.search(name)
    stamp = m.group(1) if m else dt.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y%m%d-%H%M%S")
    rec = dict(md5=md5, name=name, stamp=stamp, reader=READER_VERSION, family=fam)
    if R is None:
        rec.update(ok=None, checks=[], failed=[], data={})
        return rec
    d = dict(R.data)
    if fam in ("SALT_WISE_ITEM_LIST", "CATEGORY_WISE_ITEM_LIST", "ITEM_MASTER"):
        dm = DAY_RE.search(name)
        d["as_on"] = dm.group(1) if dm else "%s-%s-%s" % (stamp[:4], stamp[4:6], stamp[6:8])
    rec.update(ok=R.ok, checks=R.checks, failed=R.failed(), classes=dict(R.classes), data=d)
    return rec
