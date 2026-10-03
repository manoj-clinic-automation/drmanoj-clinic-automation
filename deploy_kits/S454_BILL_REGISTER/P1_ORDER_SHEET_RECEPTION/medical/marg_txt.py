# -*- coding: utf-8 -*-
r"""marg_txt.py -- Marg's one-click TEXT export, read into the same sheet Marg's Excel export is.  (S389)

WHY (the owner, 24-Sep-2026): Microsoft Office on the medical PC stopped working, so Marg's Excel
export stopped. Marg's text export does not need Office: one click writes the printed page to
C:\Users\Public\MARG\<id>\report.txt. Every reader on the clinic server and on Dr Manoj's PC reads
Marg's .XLS; none reads text. So this turns the text into that .XLS -- the SAME nine columns, the
SAME cells Marg's own export carries -- and nothing downstream has to change.

WHAT IT READS, AND ONLY THAT
  The BILL WISE SALES STATEMENT with item detail (header ending in CASH), ended by
  "*** End of Report ***". Anything else -- another report, a half-written file, a layout that is
  not where it is expected -- is refused with a reason, never guessed at.

HOW (fixed columns, never spaces -- a medicine name is cut at 20 letters and can run into its
packing, S281 analysis): the columns are measured from the report's own header line, and every
bill row is checked to sit on them. Page furniture (the C/F carry-forward, "Continued..", the
repeated firm line, page number, title and column heads) is dropped. The day total and the grand
total are carried exactly as printed, so the server's own reader checks the bills against them.

THE .XLS (BIFF8 in an OLE2 container) is written with the standard library alone -- nothing to
install on the medical PC -- and byte-for-byte the same for the same text, so the same report
exported twice is taken once. Numbers are numbers where Marg's export has numbers (a bill's money,
a whole-number quantity, an all-digit batch), text where it has text.

THE CLOSING STOCK TOO (S397, 25-Sep-2026, owner's GO)
  "WHOLE STORES CLOSING STOCK AS ON dd-mm-yyyy" (serial | medicine and packing | stock | unit, ended by
  "*** End of Report ***") becomes the four-column sheet Marg's Excel export of it is: the letterhead, the
  title, the column heads, every item, the page furniture, and the TOTAL row. Stock stays as Marg prints
  it ("3:2" = 3 strips and 2 loose, "-" = none); a plain whole number is a number, as in Marg's sheet.
  Marg's TOTAL counts every item in single units (strips x packing + loose); the reader adds every line
  the same way and refuses the file unless the two agree -- a report cut short cannot pass.
  Only the WHOLE STORES report is read; a store- or category-filtered print is left alone.

S446 (F-674, 02-Oct-2026): Marg prints *** in an item line's second number column (the three-character
  column between the bill's line number and the medicine name) when its figure does not fit. That line
  is read with the column empty: its cells are what Marg prints, as Marg's own Excel export has them
  ("4 *** FINGER EXTENSION SPL 1*1"). The stars must fill that column exactly; *** anywhere else, and
  every other check, refuses as before.

S454 (D666, 03-Oct-2026): Marg's PENDING ORDERS (PURCHASE) -- Darpan's order sheet, saved as text the default way -- is a third kind,
  ORDER: recognised by its title and column heads with *** End of Report *** at the end (the file's name is never looked at). It
  becomes an eleven-column sheet: supplier, phones, item, packing, entry number, date, order qty, receive, pending, rate, value -- a
  title row, the heads, one row per item line, the TOTAL row last; the date is not the first column. An item line is split on the
  packing's own shape followed by the entry number (a name that fills its column leaves one space). Refused, with the reason: a
  line of a kind not known here; a supplier's lines not coming to its subtotal in units; the lines not coming to the TOTAL; no
  TOTAL; the file cut short. Values are checked within a rupee a line (Marg rounds each line's value).

    python marg_txt.py report.txt out.XLS      convert one file
    python marg_txt.py --selftest               prove it
"""
import os, re, struct, sys, hashlib

VERSION = "S454"
TITLE = "BILL WISE SALES STATEMENT"
HEAD = ["BILL NO.", "DESCRIPTION", "D.R.", "GROSS AMT.", "DISCOUNT", "TAX", "DR/CR", "NET AMT.", "CASH"]
END = "*** End of Report ***"
RE_DATE = re.compile(r"^\d{2}-\d{2}-\d{4}$")
RE_BILL = re.compile(r"^(?:A|CN)\d+$")
RE_ITEM = re.compile(r"^\s{6,}\d+\s+\d+\s")
RE_ITEM_STARS = re.compile(r"^\s{6,}\d+ \*\*\* \S")    # S446: *** fills the second column, nothing else
RE_NUM = re.compile(r"^-?\d+(?:\.\d+)?$")
MAX_BYTES = 5 * 1024 * 1024


class NotThisReport(Exception):
    """Not a report this reader knows -- left alone, not an error."""


class Refused(Exception):
    """It IS a bill-wise text report, but something in it is not where it must be."""


def recognise(raw):
    """True for a complete text export this reader knows: the BILL WISE SALES STATEMENT with item
    detail (CASH column), or (S397) the WHOLE STORES CLOSING STOCK."""
    return kind(raw) is not None


def kind(raw):
    """"SALE", "STOCK", "ORDER" (S454) or None."""
    if not raw or len(raw) > MAX_BYTES or raw[:4] in (b"\xd0\xcf\x11\xe0", b"PK\x03\x04", b"%PDF"):
        return None
    t = raw.decode("latin-1")
    head = t[:4000]
    if END not in t[-400:]:
        return None
    if TITLE in head and "BILL NO." in head and "CASH" in head:
        return "SALE"
    if RE_STOCK_TITLE.search(head) and RE_STOCK_HEAD.search(head):
        return "STOCK"
    if ORDER_TITLE in head and RE_ORDER_HEAD.search(head):                 # S454 (D666)
        return "ORDER"
    return None


# ------------------------------------------------------------------------ closing stock (S397)
RE_STOCK_TITLE = re.compile(r"^\s*WHOLE STORES CLOSING STOCK AS ON (\d{2}-\d{2}-\d{4})\s*$", re.M)
RE_STOCK_HEAD = re.compile(r"^S\.No\.\s+Description\s+Total Stock\s+Unit\s*$", re.M)
STOCK_HEAD = ["S.No.", "Description", "Total Stock", "Unit"]
RE_SNO = re.compile(r"^\s*(\d+)  ")
RE_QTY = re.compile(r"^(?:-|-?\d+(?::\d+)?)$")
RE_CONT = re.compile(r"^Continued\.\.(\d+)$")
RE_PAGE = re.compile(r"^Page No\.\.(\d+)$")


def _stock_units(q, desc):
    """Marg's own count: 'a:b' = a strips of the packing plus b loose; '-' = none; else a number."""
    if q == "-":
        return 0
    m = re.match(r"^(-?)(\d+):(\d+)$", q)
    if not m:
        return int(q)
    toks = desc.split()
    pm = re.match(r"^(\d+)\*(\d+)$", (toks[-1] if len(toks) >= 2 else "").rstrip("."))
    pack = int(pm.group(1)) * int(pm.group(2)) if pm else 1
    n = int(m.group(2)) * pack + int(m.group(3))
    return -n if m.group(1) else n


def stock_rows(raw):
    """The four-column closing-stock sheet, as Marg's Excel export lays it out."""
    if kind(raw) != "STOCK":
        raise NotThisReport("not a complete whole-stores closing stock text export")
    lines = raw.decode("latin-1").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    hi = next(i for i, l in enumerate(lines) if RE_STOCK_HEAD.match(l))
    h = lines[hi]
    p_desc, p_tot, p_unit = h.find("Description"), h.find("Total Stock"), h.find("Unit")
    if not (p_desc > 0 and p_tot > p_desc and p_unit > p_tot):
        raise Refused("the column heads are not the ones expected")
    q_end = p_tot + len("Total Stock")                   # the stock sits right-aligned under its head
    q_start = q_end - 10
    rows = []
    started = False
    for l in lines[:hi]:                                 # the letterhead and the title, as printed
        s = l.rstrip()
        if not s.strip():
            if started:
                rows.append([""])
            continue
        if set(s.strip()) <= set("-="):
            continue                                     # a ruled line
        started = True
        rows.append([" ".join(s.split())] if s.strip().startswith("GSTIN") else [s])
    if not rows or not RE_STOCK_TITLE.match(rows[-1][0]):
        raise Refused("the title is not the line above the column heads")
    rows.append(list(STOCK_HEAD))
    want, units, total, seen_end, pending = 1, 0, None, False, 0
    for n, l in enumerate(lines[hi + 1:], hi + 2):
        s = l.rstrip()
        st = s.strip()
        if st == END:
            seen_end = True
            break
        if not st:
            pending += 1
            continue
        blanks, pending = pending, 0
        if set(st) <= set("-="):
            continue                                     # a ruled line
        rows.extend([[""]] * blanks)
        m = RE_SNO.match(s)
        if m and not st.startswith("TOTAL"):
            sno = int(m.group(1))
            if sno != want:
                raise Refused("line %d: item %d where %d was due" % (n, sno, want))
            want += 1
            if len(s) < q_end or s[q_end:p_unit].strip() or s[q_start - 1] != " ":
                raise Refused("line %d: item %d is not on the stock column" % (n, sno))
            desc = s[p_desc:q_start].rstrip()
            if desc and desc[:1] == " ":
                raise Refused("line %d: item %d's name is not where the header says" % (n, sno))
            q = s[q_start:q_end]
            if not RE_QTY.match(q.strip()) or q[-1] == " ":
                raise Refused("line %d: item %d's stock cannot be read: %r" % (n, sno, q.strip()))
            unit = s[p_unit:].strip()
            units += _stock_units(q.strip(), desc)
            cell = float(q.strip()) if q.strip().isdigit() else q
            rows.append([float(sno), desc, cell, unit])
            continue
        if st.startswith("TOTAL") and st[5:6] == " ":
            v = st[5:].strip()
            if not re.match(r"^-?\d+$", v):
                raise Refused("line %d: a TOTAL that is not a number" % n)
            total = int(v)
            rows.append(["TOTAL", "", float(total), ""])
            continue
        mc, mp = RE_CONT.match(st), RE_PAGE.match(st)
        if mc:
            rows.append(["", "", "", st])
        elif mp:
            rows.append(["", "", "    Page", "No..%s" % mp.group(1)])
        elif RE_STOCK_HEAD.match(s):
            rows.append(list(STOCK_HEAD))
        elif RE_STOCK_TITLE.match(s) or st == rows[0][0].strip():
            rows.append([st])                            # the title and the shop's name, at each page top
        else:
            raise Refused("line %d: a line of a kind this reader does not know: %r" % (n, st[:60]))
    if not seen_end:
        raise Refused("no End of Report -- the file is incomplete")
    if want == 1:
        raise Refused("no items")
    if total is None:
        raise Refused("no TOTAL line")
    if total != units:
        raise Refused("the TOTAL printed (%d) is not the sum of the lines (%d)" % (total, units))
    return [r + [""] * (4 - len(r)) for r in rows]


# ------------------------------------------------------------------------ the pending-orders sheet (S454)
ORDER_TITLE = "PENDING ORDERS (PURCHASE)"
RE_ORDER_HEAD = re.compile(r"^\s*ITEM NAME\s+ENTRY NO\.\s+DATED\s+ORDER QTY\s+RECEIVE\s+PENDING\s+RATE\s+VALUE\b", re.M)
ORDER_HEAD = ["SUPPLIER", "PHONES", "ITEM NAME", "PACKING", "ENTRY NO.", "DATED", "ORDER QTY", "RECEIVE", "PENDING", "RATE", "VALUE"]
_Q = r"\d+(?::\d+)?"
# an item line: two spaces, the name, ONE space or more, the packing's own shape (a stray full stop allowed), the entry number, the
# date, order qty, receive, pending, rate, value -- and the two trailing heads (due date, party order no.) when Marg fills them.
# A name that fills its column leaves a single space before the packing, so the split is on the packing + entry shape, never on
# "two or more spaces".
RE_ORDER_ITEM = re.compile(r"^  (\S.*?) +(\d+\*\d+)\.? +([A-Z]{1,4}-\d+) +(\d\d-\d\d-\d{4}) +(" + _Q + r") +(-|" + _Q + r") +(" + _Q +
                           r") +(\d+(?:\.\d+)?) +(\d+)(?: +(\d\d-\d\d-\d{4}))?(?: +(\S{1,30}))?\s*$")
RE_ORDER_SUP = re.compile(r"^(\S.*?)\s*Ph\.(.*)$")
RE_ORDER_PHONE = re.compile(r"^[0-9X+\-]{5,16}$")
RE_ORDER_SUB = re.compile(r"^\s{20,}(\d+)\s+(\d+)\s+(\d+)\s*$")
RE_ORDER_TOTAL = re.compile(r"^TOTAL\s+(\d+)\s+(\d+)\s+(\d+)\s*$")


def _order_units(q, packing):
    """Marg's units: 'a:b' = a packs of the packing (1*10 -> 10) plus b loose; a plain number stands as it is."""
    if q == "-":
        return 0
    m = re.match(r"^(\d+):(\d+)$", q)
    if not m:
        return int(q)
    pm = re.match(r"^(\d+)\*(\d+)$", packing)
    pack = int(pm.group(1)) * int(pm.group(2)) if pm else 1
    return int(m.group(1)) * pack + int(m.group(2))


def _order_cell(q):
    """A quantity as Marg's sheet would carry it: '20:0' as printed, a plain whole number a number."""
    return float(q) if q.isdigit() else q


def order_rows(raw):
    """The eleven-column pending-orders sheet: a title row, the heads, one row per item line, the TOTAL row.
    Refused, with the reason, when a line is of a kind not known here, a supplier's lines do not come to its
    subtotal in units, the lines do not come to the TOTAL in units, there is no TOTAL, or the file is cut short.
    The value is checked with a tolerance of one rupee a line (Marg rounds each line's value)."""
    t = raw.decode("latin-1").replace("\r\n", "\n").replace("\r", "\n")
    if ORDER_TITLE not in t[:4000] or not RE_ORDER_HEAD.search(t[:4000]):
        raise NotThisReport("not a pending-orders text export")
    if END not in t[-400:]:
        raise Refused("no End of Report -- the file is incomplete")
    lines = t.split("\n")
    hi = next(i for i, l in enumerate(lines) if RE_ORDER_HEAD.match(l))
    shop = next((l.strip() for l in lines[:hi] if l.strip()), "")
    rows = [[ORDER_TITLE] + [""] * 10, list(ORDER_HEAD)]
    sups, cur, total, seen_end, furniture = [], None, None, False, False
    tu = tp = tv = 0

    def close(s, n):
        if s is None:
            return
        if not s["items"]:
            raise Refused("line %d: %s has no item line" % (n, s["name"]))
        if s["sub"] is None and len(s["items"]) > 1:
            raise Refused("line %d: %s has %d lines and no subtotal" % (n, s["name"], len(s["items"])))
    for n, l in enumerate(lines[hi + 1:], hi + 2):
        s = l.rstrip()
        st = s.strip()
        if not st:
            continue
        if st == END:
            seen_end = True
            break
        if set(st.replace(" ", "")) <= set("-="):
            continue                                            # a ruled line
        if furniture:                                           # the next page's shop name, title, page number and heads
            if RE_ORDER_HEAD.match(s):
                furniture = False
            elif st == shop or (ORDER_TITLE in st and re.search(r"Page No\.\.\d+$", st)):
                pass
            else:
                raise Refused("line %d: a line of a kind this reader does not know: %r" % (n, st[:60]))
            continue
        if re.match(r"^Continued\.\.\d+$", st):
            furniture = True
            continue
        m = RE_ORDER_TOTAL.match(s)
        if m:
            close(cur, n)
            cur = None
            total = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            continue
        m = RE_ORDER_ITEM.match(s)
        if m:
            if cur is None:
                raise Refused("line %d: an item line with no supplier above it" % n)
            name, pack, entry, date, oq, rec, pend, rate, val = m.groups()[:9]
            u, pu = _order_units(oq, pack), _order_units(pend, pack)
            cur["items"].append((u, pu, int(val)))
            rows.append([cur["name"], cur["phones"], name.strip(), pack, entry, date, _order_cell(oq), _order_cell(rec),
                         _order_cell(pend), float(rate), float(val)])
            continue
        m = RE_ORDER_SUB.match(s)
        if m:
            if cur is None or not cur["items"] or cur["sub"] is not None:
                raise Refused("line %d: a subtotal where none belongs" % n)
            cur["sub"] = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            k = len(cur["items"])
            su, sp, sv = (sum(x[i] for x in cur["items"]) for i in range(3))
            if cur["sub"][0] != su or cur["sub"][1] != sp:
                raise Refused("line %d: %s's lines come to %d units, its subtotal says %d" % (n, cur["name"], su, cur["sub"][0]))
            if abs(cur["sub"][2] - sv) > k:
                raise Refused("line %d: %s's line values come to %d, its subtotal says %d" % (n, cur["name"], sv, cur["sub"][2]))
            continue
        m = RE_ORDER_SUP.match(s)
        if m and not s.startswith(" "):
            close(cur, n)
            nm = re.sub(r"\s{2,}.*$", "", m.group(1)).strip()
            ph = []
            for p in m.group(2).split():
                if not RE_ORDER_PHONE.match(p):
                    raise Refused("line %d: %s's phone cannot be read" % (n, nm))
                if p not in ph:
                    ph.append(p)
            cur = dict(name=nm, phones=", ".join(ph), items=[], sub=None)
            sups.append(cur)
            continue
        raise Refused("line %d: a line of a kind this reader does not know: %r" % (n, st[:60]))
    if not seen_end:
        raise Refused("no End of Report -- the file is incomplete")
    if total is None:
        raise Refused("no TOTAL line")
    close(cur, len(lines))
    nl = 0
    for sp_ in sups:
        for u, pu, v in sp_["items"]:
            tu, tp, tv, nl = tu + u, tp + pu, tv + v, nl + 1
    if not nl:
        raise Refused("no items")
    if total[0] != tu or total[1] != tp:
        raise Refused("the TOTAL printed (%d units) is not the sum of the lines (%d)" % (total[0], tu))
    if abs(total[2] - tv) > nl:
        raise Refused("the TOTAL value printed (%d) is not the sum of the line values (%d) within a rupee a line" % (total[2], tv))
    rows.append(["TOTAL", "", "", "", "", "", float(total[0]), "", float(total[1]), "", float(total[2])])
    return rows


def _cols(header_line):
    """Start offset of every column, measured from the report's own header line."""
    pos = []
    at = 0
    for h in HEAD:
        i = header_line.find(h, at)
        if i < 0:
            raise Refused("the column heads are not the ones expected (%s missing)" % h)
        pos.append(i)
        at = i + len(h)
    return pos


def _num(s):
    s = s.strip()
    if not RE_NUM.match(s):
        raise Refused("not a number where one must be: %r" % s)
    return s


def to_rows(raw):
    """The nine-column sheet, as a list of rows of cells (str, or float for a number)."""
    if kind(raw) != "SALE":
        raise NotThisReport("not a complete bill-wise sales text export")
    lines = raw.decode("latin-1").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    title = None
    hi = None
    for i, l in enumerate(lines):
        if title is None and TITLE in l:
            title = l.rstrip()
        if l.startswith("BILL NO.") and "CASH" in l:
            hi = i
            break
    if title is None or hi is None:
        raise Refused("no title or no column heads at the top")
    pos = _cols(lines[hi])
    p_dr, p_gross = pos[2], pos[3]
    rows = [[title, "", "", "", "", "", "", "", ""], list(HEAD)]
    seen_end = False
    for n, l in enumerate(lines[hi + 1:], hi + 2):
        s = l.rstrip()
        st = s.strip()
        if not st:
            continue
        if st == END:
            seen_end = True
            break
        if set(st.replace(" ", "")) <= set("-="):                     # a ruled line
            continue
        if (st.startswith("C/F :") or st.startswith("Continued..") or st.startswith("Page No..")
                or TITLE in st or s.startswith("BILL NO.") or st == "SANJEEVNI MEDICOS"):
            continue                                                     # page furniture
        if RE_DATE.match(st):
            rows.append([st, "", "", "", "", "", "", "", ""])
            continue
        c0 = s[:pos[1]].strip()
        if RE_BILL.match(c0):
            if len(s) < p_gross or s[p_dr] != ".":
                raise Refused("line %d: a bill row whose payment head is not where the header says" % n)
            desc = s[pos[1]:p_dr].strip()
            mode = s[p_dr:p_gross].rstrip()
            nums = s[p_gross:].split()
            if len(nums) != 6:
                raise Refused("line %d: bill %s does not carry six amounts" % (n, c0))
            nums = [_num(x) for x in nums]
            gross = nums[0] if nums[0].startswith("-") else float(nums[0])   # Marg: a negative gross is text
            rows.append([c0, desc, mode, gross] + [float(x) for x in nums[1:]])
            continue
        if "DAY TOTAL :" in st or "GRAND TOTAL :" in st:
            k = s.find("DAY TOTAL :") if "DAY TOTAL :" in s else s.find("GRAND TOTAL :")
            label = s[k:].split(":")[0].strip() + " :"
            nums = [float(_num(x)) for x in s[k + len(label):].split()]
            if len(nums) != 6:
                raise Refused("line %d: a total that does not carry six amounts" % n)
            if label.startswith("GRAND"):
                m = re.search(r"Total No\. of\s+(Bills:\s*\d+)", s)
                rows.append(["Total No. of", m.group(1) if m else "", label] + nums)
            else:
                rows.append(["", "", label] + nums)
            continue
        if RE_ITEM.match(s) or RE_ITEM_STARS.match(s):          # S446 (F-674)
            body = s.lstrip()       # S389.2: a line number of two digits starts a column early (10, 11 ...)
            # the item line: "seq code NAME<20> PACK" | qty | "amount  m/yy" | batch -- by position
            mm = re.search(r"\s(\d+(?::\d+)?)\s+(-?\d+\.\d\d)(?:\s+(\d{1,2}/\d{2}))?(?:\s+(\S+))?\s*$", body)
            if not mm:
                raise Refused("line %d: an item line that cannot be read" % n)
            left = body[:mm.start(1)].rstrip()
            qty = mm.group(1)
            amt = mm.group(2)
            exp = mm.group(3)
            batch = mm.group(4) or ""
            if exp is None and batch and re.match(r"^\d{1,2}/\d{2}$", batch):
                exp, batch = batch, ""
            q = float(qty) if ":" not in qty else ("      " + qty)[-9:]
            ae = (" %7s %5s" % (amt, exp)) if exp else (" %7s" % amt)
            b = float(batch) if (batch.isdigit() and not batch.startswith("0")) else batch
            rows.append(["", left.strip(), q, ae, b, "", "", "", ""])
            continue
        raise Refused("line %d: a line of a kind this reader does not know: %r" % (n, st[:60]))
    if not seen_end:
        raise Refused("no End of Report -- the file is incomplete")
    if not any(r[2] == "GRAND TOTAL :" for r in rows):
        raise Refused("no GRAND TOTAL line")
    return rows


# --------------------------------------------------------------------- BIFF8 / OLE2 writer
def _rec(rt, data):
    return struct.pack("<HH", rt, len(data)) + data


def _label(r, c, s):
    try:
        b = s.encode("latin-1"); flag = 0
    except UnicodeEncodeError:
        b = s.encode("utf-16-le"); flag = 1
    return _rec(0x0204, struct.pack("<HHHHB", r, c, 0x0F, len(s), flag) + b)


def _number(r, c, v):
    return _rec(0x0203, struct.pack("<HHHd", r, c, 0x0F, float(v)))


def _bof(dt):
    return _rec(0x0809, struct.pack("<HHHHII", 0x0600, dt, 0x0DBB, 0x07CC, 0, 0x06))


def workbook_stream(rows):
    ncols = max(len(r) for r in rows)
    cells = []
    for r, row in enumerate(rows):
        for c, v in enumerate(row):
            if isinstance(v, float):
                cells.append(_number(r, c, v))
            elif v != "":
                cells.append(_label(r, c, v))
    sheet = (_bof(0x0010) + _rec(0x0200, struct.pack("<IIHHH", 0, len(rows), 0, ncols, 0))
             + b"".join(cells) + _rec(0x000A, b""))
    name = b"Sheet1"
    fname = b"Arial"
    font = _rec(0x0031, struct.pack("<HHHHHBBBB", 200, 0, 0x7FFF, 400, 0, 0, 0, 0, 0)
                + struct.pack("<BB", len(fname), 0) + fname)
    # the sixteen standard XF records: fifteen style XFs, then the one cell XF (index 15) every
    # cell points at -- readers such as xlrd map each cell's type through them
    style_xf = _rec(0x00E0, struct.pack("<HHHBBBBIIH", 0, 0, 0xFFF5, 0x20, 0, 0, 0xF4, 0, 0, 0x20C0))
    cell_xf = _rec(0x00E0, struct.pack("<HHHBBBBIIH", 0, 0, 0x0001, 0x20, 0, 0, 0x00, 0, 0, 0x20C0))
    def globals_(off):
        return (_bof(0x0005) + _rec(0x0042, struct.pack("<H", 0x04B0))
                + font * 4 + style_xf * 15 + cell_xf
                + _rec(0x0085, struct.pack("<IBBBB", off, 0, 0, len(name), 0) + name)
                + _rec(0x000A, b""))
    g = globals_(0)
    g = globals_(len(g))
    return g + sheet


def ole2(stream, name="Workbook"):
    """A minimal compound file: one stream, no mini-stream (the stream is padded to >= 4096)."""
    SS = 512
    if len(stream) < 4096:
        stream = stream + b"\x00" * (4096 - len(stream))
    size = len(stream)
    nstream = (size + SS - 1) // SS
    stream_p = stream + b"\x00" * (nstream * SS - size)
    ndir = 1
    nfat = 1
    while (nstream + ndir + nfat) > nfat * 128:
        nfat += 1
    if nfat > 109:
        raise Refused("report too large for this writer")
    FREE, END_, FATS = 0xFFFFFFFF, 0xFFFFFFFE, 0xFFFFFFFD
    fat = []
    for i in range(nstream):
        fat.append(i + 1 if i < nstream - 1 else END_)
    dir_start = nstream
    fat.append(END_)                                        # the one directory sector
    fat_start = nstream + ndir
    fat += [FATS] * nfat
    fat += [FREE] * (nfat * 128 - len(fat))
    def dent(nm, typ, child, start, sz):
        n = nm.encode("utf-16-le") + b"\x00\x00"
        e = n + b"\x00" * (64 - len(n))
        e += struct.pack("<HBB", len(n), typ, 1)            # name length, type, colour black
        e += struct.pack("<III", 0xFFFFFFFF, 0xFFFFFFFF, child)
        e += b"\x00" * 16 + struct.pack("<I", 0) + b"\x00" * 16
        e += struct.pack("<IQ", start, sz)
        return e
    d = dent("Root Entry", 5, 1, END_, 0) + dent(name, 2, 0xFFFFFFFF, 0, size)
    d += (dent("", 0, 0xFFFFFFFF, FREE, 0)) * 2
    difat = list(range(fat_start, fat_start + nfat)) + [FREE] * (109 - nfat)
    hdr = (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 16
           + struct.pack("<HHHHH", 0x003E, 0x0003, 0xFFFE, 9, 6) + b"\x00" * 6
           + struct.pack("<IIIIIIIII", 0, nfat, dir_start, 0, 4096, END_, 0, END_, 0)
           + struct.pack("<109I", *difat))
    assert len(hdr) == 512
    return hdr + stream_p + d + struct.pack("<%dI" % len(fat), *fat)


def convert(raw):
    """(xls_bytes, info) for a text export; raises NotThisReport / Refused."""
    k = kind(raw)
    rows = stock_rows(raw) if k == "STOCK" else (order_rows(raw) if k == "ORDER" else to_rows(raw))     # S454: ORDER
    return ole2(workbook_stream(rows)), {"rows": len(rows), "version": VERSION, "kind": k or "SALE"}


# ------------------------------------------------------------------------------- selftest
SELFTEST_SAMPLE = ("                  BILL WISE SALES STATEMENT AS ON 23-09-2026\r\n" + "-" * 132 + "\r\n"
     "BILL NO.    DESCRIPTION                       D.R.          GROSS AMT.    DISCOUNT         TAX"
     "       DR/CR    NET AMT.        CASH\r\n" + "-" * 132 + "\r\n23-09-2026\r\n"
     "A000001                TEST ONE               .CASH      #       90.00       10.00        0.00"
     "        0.00       80.00       80.00\r\n"
     "            1  92 XEPOD 200            1*10          0:4      225.00  2/28 UCT26111C\r\n\r\n"
     "A000002                TEST TWO               .UPI              539.99        0.00        0.00"
     "        0.00      540.00        0.00\r\n"
     "            1   5 HARD COLLAR ADJ L HO 1*1             1      375.00       1\r\n"
     "            2  16 DISPO SYRINGE NIPRO  1*1             1        7.00\r\n"
     "            3   5 TOLTRIS PLUS         1*10          0:9      157.99  6/28 260500\r\n\r\n"
     + " " * 46 + "-" * 86 + "\r\n" + " " * 46 + "DAY TOTAL :       629.99       10.00        0.00"
     "        0.00      620.00       80.00\r\n" + "-" * 132 + "\r\n"
     "Total No. of Bills: 2                        GRAND TOTAL :       629.99       10.00        0.00"
     "        0.00      620.00       80.00\r\n" + "-" * 132 + "\r\n\r\n*** End of Report ***\r\n").encode()


def _stock_line(sno, desc, q, unit):
    return ("%5d  %-57s%10s  %s" % (sno, desc, q, unit)).rstrip() + "\r\n"


STOCK_SAMPLE = ("\r\n" + " " * 31 + "TEST SHOP\r\n" + " " * 24 + "TEST STREET\r\n"
     + " " * 16 + "GSTIN : TESTGST  TIN No. : TESTTIN\r\n\r\n"
     + " " * 19 + "WHOLE STORES CLOSING STOCK AS ON 24-09-2026\r\n" + "-" * 80 + "\r\n"
     "S.No.  Description" + " " * 45 + "Total Stock  Unit\r\n" + "-" * 80 + "\r\n"
     + _stock_line(1, "", "-", "PCS")
     + _stock_line(2, "TEST TAB 500                  1*10", "3:2", "STRI")
     + _stock_line(3, "TEST CAST 5                   1*1", "-14", "ITEM")
     + "-" * 80 + "\r\n" + " " * 66 + "Continued..2\r\n\r\n\r\n\r\n\r\n"
     "TEST SHOP\r\n" + " " * 68 + "Page No..2\r\nWHOLE STORES CLOSING STOCK AS ON 24-09-2026\r\n"
     + "-" * 80 + "\r\nS.No.  Description" + " " * 45 + "Total Stock  Unit\r\n" + "-" * 80 + "\r\n"
     + _stock_line(4, "TEST GEL                      30GM", "6", "TUBE")
     + _stock_line(5, "TEST WRIST SPLINT LF L ELAST 1*1", "-1:3", "")
     + "-" * 80 + "\r\nTOTAL" + " " * 68 + "20\r\n" + "-" * 80 + "\r\n*** End of Report ***\r\n\r\n").encode()


ORDER_SAMPLE = (
    '\n'
    '                               SANJEEVNI MEDICOS\n'
    '                        XXXXXXXX , XXXXXX XXXX XXXXXXXX\n'
    '                              Phone : XXXXXXXXXX\n'
    '                D.L.No. : XXXXXXXX\n'
    '                GSTIN : XXXXXXXXXXXXXXX  TIN No. : XXXXXXXXXXX\n'
    '\n'
    '                            PENDING ORDERS (PURCHASE)\n'
    '------------------------------------------------------------------------------------------------------------------------------------\n'
    '  ITEM NAME                      ENTRY NO.    DATED   ORDER QTY   RECEIVE   PENDING     RATE   VALUE  DUEDT  PARTY ORDER NO.\n'
    '------------------------------------------------------------------------------------------------------------------------------------\n'
    '\n'
    'DEEPAM PHARMA Ph.XXXXXXXXXX\n'
    '  TENDOZAC TAB          1*10     OP-0329   02-10-2026      20:0         -      20:0   190.50    3810\n'
    '  VERC 16               1*10     OP-0329   02-10-2026      10:0         -      10:0    95.25     953\n'
    '                                                   ------------------------------------------------------------------\n'
    '                                                            300       300             4763\n'
    '                                                   ------------------------------------------------------------------\n'
    '\n'
    'DRUG DEAL                     BAREILLY Ph.XXXXXXXXXX XXXXXXXXXX\n'
    '  CHYMORAL AP           1*10     OP-0325   02-10-2026      10:0         -      10:0   142.71    1427\n'
    '  XGESIC LA             1*15     OP-0300   17-09-2026      20:0         -      20:0    85.34    1707\n'
    '                                                   ------------------------------------------------------------------\n'
    '                                                            400       400             3134\n'
    '                                                   ------------------------------------------------------------------\n'
    '\n'
    'GUNINA PHARMACEUTICALS PVT LTD Ph.XXXXXXXXXX XXXXXXXXXX\n'
    '  CCM                   1*40     OP-0323   02-10-2026         5         -         5   427.86    2139\n'
    '  DFO MR                1*10     OP-0323   02-10-2026      10:0         -      10:0   103.52    1035\n'
    '                                                   ------------------------------------------------------------------\n'
    '                                                            105       105             3175\n'
    '                                                   ------------------------------------------------------------------\n'
    '\n'
    'JANTA PHARMACEUTICALS         BAREILLY Ph.XXXXXXXXXX XXXXXXXXXX\n'
    '  NUPTACH 200           1*1      OP-0319   25-09-2026        10         -        10   148.61    1486\n'
    '  POWERGESIC 100 PATCH  1*1      OP-0319   25-09-2026        10         -        10   122.15    1222\n'
    '  VOLITRA APS SPRAY     1*1      OP-0330   02-10-2026        10         -        10   267.86    2679\n'
    '                                                   ------------------------------------------------------------------\n'
    '                                                             30        30             5386\n'
    '                                                   ------------------------------------------------------------------\n'
    '\n'
    'KEDAR PHARMACEUTICAL Ph.XXXXXXXXXX XXXXXXXXXX\n'
    '  KT ROS DT             1*15     OP-0326   02-10-2026      20:0         -      20:0    56.00    1120\n'
    '  LONAC AQ INJ          1*1      OP-0326   02-10-2026        20         -        20    23.00     460\n'
    '  MEG QCS               1*15     OP-0326   02-10-2026      20:0         -      20:0    80.00    1600\n'
    '  PRETOL-4              1*10     OP-0326   02-10-2026      10:0         -      10:0    48.00     480\n'
    '  RANIMIG 150           1*30     OP-0326   02-10-2026      10:0         -      10:0    33.60     336\n'
    '                                                   ------------------------------------------------------------------\n'
    '                                                           1020      1020             3996\n'
    '                                                   ------------------------------------------------------------------\n'
    '\n'
    'KRISHNA MEDICOS               BAREILLY Ph.XXXXXXXXXX XXXXXXXXXXX XXXXXXXXXX\n'
    '  NARCOGEN FORTE        1*10     OP-0327   02-10-2026      10:0         -      10:0   179.37    1794\n'
    '\n'
    'RADHA MEDICAL & SCIENTIFIC Ph.XXXXXXXXXX XXXXXXXXXX\n'
    '  PANTOCID DSR          1*15     OP-0328   02-10-2026      10:0         -      10:0   192.14    1921\n'
    '  UPRISE 6L INJ         1*1      OP-0293   09-09-2026        18         -        18    59.28    1067\n'
    '                                                   ------------------------------------------------------------------\n'
    '                                                            168       168             2988\n'
    '                                                   ------------------------------------------------------------------\n'
    '\n'
    'RAVI MEDICAL AGENCY Ph.\n'
    '------------------------------------------------------------------------------------------------------------------------------------\n'
    '                                                                  Continued..2\n'
    '\n'
    '\n'
    'SANJEEVNI MEDICOS\n'
    ' PENDING ORDERS (PURCHASE)                                          Page No..2\n'
    '------------------------------------------------------------------------------------------------------------------------------------\n'
    '  ITEM NAME                      ENTRY NO.    DATED   ORDER QTY   RECEIVE   PENDING     RATE   VALUE  DUEDT  PARTY ORDER NO.\n'
    '------------------------------------------------------------------------------------------------------------------------------------\n'
    '  DECA INSTABOLIN 50    1*1      OP-0331   02-10-2026        10         -        10    17.00     170\n'
    '  ETOBONE P             1*10     OP-0235   10-08-2026      40:0         -      40:0    24.00     960\n'
    '  MET4MIN GL 1          1*10     OP-0317   25-09-2026      20:0         -      20:0    16.00     320\n'
    '  OPTIFENAC TBR         1*10     OP-0307   17-09-2026      10:0         -      10:0    35.00     350\n'
    '                                                   ------------------------------------------------------------------\n'
    '                                                            710       710             1800\n'
    '                                                   ------------------------------------------------------------------\n'
    '\n'
    'SHIVAAZ FORMULATIONS          BAREILLY Ph.XXXXXXXXXX\n'
    '  CEECIT MZ             1*10     OP-0324   02-10-2026      10:0         -      10:0    66.96     670\n'
    '  CROCAL                1*10     OP-0324   02-10-2026      30:0         -      30:0    44.45    1334\n'
    '  OSTOVAXL DM           1*10     OP-0324   02-10-2026      20:0         -      20:0   163.58    3272\n'
    '  PREGHYPE NT TAB       1*10     OP-0324   02-10-2026      20:0         -      20:0   143.28    2866\n'
    '  PRETOL 8              1*10.    OP-0324   02-10-2026      10:0         -      10:0    56.00     560\n'
    '  VINDAC 25             1*1      OP-0191   23-07-2026        10         -        10    83.34     833\n'
    '  VOM L                 1*10     OP-0246   19-08-2026      10:0         -      10:0   115.32    1153\n'
    '                                                   ------------------------------------------------------------------\n'
    '                                                           1010      1010            10687\n'
    '                                                   ------------------------------------------------------------------\n'
    '\n'
    'SHRADDHA MEDICOSE Ph.XXXXXXXXXX\n'
    '  AURAB L CAP           1*10     OP-0322   02-10-2026      10:0         -      10:0   127.98    1280\n'
    '  FENARIC T4 TAB        1*10     OP-0322   02-10-2026      10:0         -      10:0   117.98    1180\n'
    '                                                   ------------------------------------------------------------------\n'
    '                                                            200       200             2460\n'
    '                                                   ------------------------------------------------------------------\n'
    '\n'
    'YUVIKA SURGICALS Ph.XXXXXXXXXX\n'
    '  ARM SLING XL HOPE     1*1      OP-0267   01-09-2026         2         -         2   215.00     430\n'
    '  KNEE IMMOBILISER UNIS 1*1      OP-0288   09-09-2026         1         -         1   614.28     614\n'
    '                                                   ------------------------------------------------------------------\n'
    '                                                              3         3             1044\n'
    '                                                   ------------------------------------------------------------------\n'
    '------------------------------------------------------------------------------------------------------------------------------------\n'
    'TOTAL                                                      4046      4046            41226\n'
    '------------------------------------------------------------------------------------------------------------------------------------\n'
    '*** End of Report ***\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
    '\n'
).encode("latin-1")


def selftest(sample=None):
    ok = True
    def ck(name, cond, got=None):
        nonlocal ok
        print(("  OK   " if cond else "  FAIL ") + name + ("" if got is None else "   [%s]" % (got,)))
        ok = ok and bool(cond)
    T = SELFTEST_SAMPLE
    ck("a complete bill-wise text export is recognised", recognise(T))
    ck("an Excel file, a PDF and a cut-off text are not", not recognise(b"\xd0\xcf\x11\xe0xx")
       and not recognise(b"%PDF-1.4") and not recognise(T[:-40]))
    rows = to_rows(T)
    bills = [r for r in rows if RE_BILL.match(str(r[0]))]
    ck("two bills, each carrying its six amounts", len(bills) == 2 and all(isinstance(b[4], float) for b in bills))
    items = [r for r in rows if r[0] == "" and r[1][:1].isdigit()]
    ck("four item lines, a name cut at 20 letters kept whole with its packing",
       len(items) == 4 and items[1][1].endswith("HARD COLLAR ADJ L HO 1*1"), [i[1] for i in items][1:2])
    ck("a two-digit line number keeps both digits (S389.2)",
       to_rows(T.replace(b"            3   5 TOLTRIS PLUS", b"           13   5 TOLTRIS PLUS"))[-3][1].startswith("13 "),
       to_rows(T.replace(b"            3   5 TOLTRIS PLUS", b"           13   5 TOLTRIS PLUS"))[-3][1][:12])
    ck("an item with no expiry keeps its batch; one with neither keeps its amount",
       items[1][4] == 1.0 and items[2][3].strip() == "7.00")
    ST = T.replace(b"            2  16 DISPO SYRINGE NIPRO", b"            2 *** DISPO SYRINGE NIPRO")
    sr_ = to_rows(ST)
    ck("S446: *** in an item's second column is read with that column empty, the line as Marg prints it",
       [r for r in sr_ if r[0] == "" and r[1][:1].isdigit()][2][1] == "2 *** DISPO SYRINGE NIPRO  1*1"
       and len(sr_) == len(rows))
    for bad_, why_ in ((ST.replace(b"NIPRO  1*1             1        7.00", b"NIPRO  1*1           ***        7.00"),
                        "*** in the quantity"),
                       (ST.replace(b"             1        7.00", b"             1         ***"), "*** in the amount"),
                       (T.replace(b"            2  16 DISPO", b"          ***  16 DISPO"), "*** in the line number"),
                       (T.replace(b"            2  16 DISPO", b"            2 **  DISPO"), "** not filling the column")):
        try:
            to_rows(bad_); ck("S446 refused: " + why_, False)
        except Refused:
            ck("S446 refused: " + why_, True)
    x1, _ = convert(T); x2, _ = convert(T)
    ck("the same text gives the same bytes every time", x1 == x2, hashlib.md5(x1).hexdigest()[:8])
    try:
        import xlrd
        sh = xlrd.open_workbook(file_contents=x1).sheet_by_index(0)
        ck("the .XLS opens in xlrd, nine columns", sh.ncols == 9 and sh.nrows == len(rows), (sh.nrows, sh.ncols))
        ck("cells read back as written", sh.cell_value(1, 0) == "BILL NO." and sh.cell_value(3, 7) == 80.0 and sh.cell_value(2, 0) == "23-09-2026")
    except ImportError:
        print("  (xlrd not on this machine -- the read-back is proved at build time)")
    bad = T.replace(b"                TEST ONE               .CASH", b"                TEST ONE                .CASH")
    try:
        to_rows(bad); ck("a bill row off its columns is refused", False)
    except Refused:
        ck("a bill row off its columns is refused", True)
    # S397: the closing stock
    S_ = STOCK_SAMPLE
    ck("a complete closing-stock text export is recognised as STOCK; the sale stays SALE",
       kind(S_) == "STOCK" and kind(T) == "SALE" and not recognise(S_[:-30]))
    sr = stock_rows(S_)
    its = [r for r in sr if isinstance(r[0], float)]
    ck("five items, serials 1..5, the TOTAL carried", [r[0] for r in its] == [1.0, 2.0, 3.0, 4.0, 5.0]
       and ["TOTAL", "", 20.0, ""] in sr)
    ck("stock as Marg's sheet has it: '3:2' and '-14' as printed, a plain 6 a number, a missing unit empty",
       its[1][2] == "       3:2" and its[2][2] == "       -14" and its[3][2] == 6.0 and its[4][3] == ""
       and its[0][1] == "" and its[0][2] == "         -", [its[1][2], its[2][2], its[3][2]])
    ck("the page break as Marg's sheet has it", ["", "", "", "Continued..2"] in sr
       and ["", "", "    Page", "No..2"] in sr and sr.count(["", "", "", ""]) == 5)
    ck("a 29-letter name keeps its packing; the GSTIN line is closed up",
       its[4][1] == "TEST WRIST SPLINT LF L ELAST 1*1" and ["GSTIN : TESTGST TIN No. : TESTTIN", "", "", ""] in sr)
    for bad, why in ((S_.replace(b"TOTAL" + b" " * 68 + b"20", b"TOTAL" + b" " * 68 + b"21"), "a TOTAL that does not add up"),
                     (S_.replace(b"    4  TEST GEL", b"    6  TEST GEL"), "a serial out of order"),
                     (S_.replace(b"   3:2  STRI", b"  3:2   STRI"), "a stock off its column")):
        try:
            stock_rows(bad); ck("refused: " + why, False)
        except Refused:
            ck("refused: " + why, True)
    xs, info = convert(S_)
    ck("the stock .XLS is the same bytes every time", xs == convert(S_)[0] and info["kind"] == "STOCK")
    # S454 (D666): the pending-orders sheet -- the repository's sample of 02-Oct (phone numbers blanked)
    O_ = ORDER_SAMPLE
    ck("S454: the pending-orders sheet is recognised as ORDER; the sale and the stock stay themselves",
       kind(O_) == "ORDER" and kind(T) == "SALE" and kind(S_) == "STOCK" and kind(T) != "ORDER")
    orr = order_rows(O_)
    it_ = orr[2:-1]
    ck("S454: 11 suppliers, 32 lines, 4,046 units; the TOTAL row last", len({r[0] for r in it_}) == 11 and len(it_) == 32
       and orr[-1][0] == "TOTAL" and orr[-1][6] == 4046.0 and orr[-1][10] == 41226.0, (len({r[0] for r in it_}), len(it_), orr[-1][6]))
    ck("S454: the heads, eleven, the date not the first column", orr[1] == ORDER_HEAD and orr[1][0] == "SUPPLIER" and orr[1][5] == "DATED"
       and all(len(r) == 11 for r in orr))
    ck("S454: the supplier whose block breaks across the page keeps its four lines",
       [r[2] for r in it_ if r[0] == "RAVI MEDICAL AGENCY"] == ["DECA INSTABOLIN 50", "ETOBONE P", "MET4MIN GL 1", "OPTIFENAC TBR"])
    ck("S454: a name that fills its column is read whole, the packing apart (one space)",
       any(r[2] == "KNEE IMMOBILISER UNIS" and r[3] == "1*1" and r[4] == "OP-0288" for r in it_))
    ck("S454: the supplier with one line and no subtotal is read; the town is not part of a supplier",
       [r[2] for r in it_ if r[0] == "KRISHNA MEDICOS"] == ["NARCOGEN FORTE"] and "DRUG DEAL" in {r[0] for r in it_})
    ck("S454: '20:0' as printed, a plain number a number, the stray full stop dropped from a packing",
       any(r[2] == "TENDOZAC TAB" and r[6] == "20:0" for r in it_) and any(r[2] == "CCM" and r[6] == 5.0 for r in it_)
       and any(r[2] == "PRETOL 8" and r[3] == "1*10" for r in it_))
    _cut = O_[:O_.index(b"*** End of Report ***")]
    for bad_, why_ in ((O_.replace(b"  VERC 16               1*10     OP-0329   02-10-2026      10:0         -      10:0    95.25     953\n", b""),
                        "a line removed (the subtotal fails)"),
                       (O_.replace(b"TOTAL                                                      4046      4046", b"TOTAL                                                      4047      4047"),
                        "the TOTAL altered"),
                       (_cut, "the last line cut off (no End of Report)"),
                       (O_.replace(b"KRISHNA MEDICOS", b"  SOMETHING ODD HERE\nKRISHNA MEDICOS"), "a line of a kind not known"),
                       (O_.replace(b"TOTAL                                                      4046      4046            41226\n", b""), "no TOTAL")):
        try:
            order_rows(bad_)
            ck("S454 refused: " + why_, False)
        except Refused as ex_:
            ck("S454 refused: %s -- %s" % (why_, str(ex_)[:70]), True)
    ck("S454: a cut-off sheet is not recognised as ORDER (no End line); a sale with the order title elsewhere is not either",
       kind(_cut) is None and kind(T + b"PENDING ORDERS (PURCHASE)") != "ORDER")
    xo, io_ = convert(O_)
    ck("S454: the order sheet gives the same bytes every time", xo == convert(O_)[0] and io_["kind"] == "ORDER" and io_["rows"] == 35,
       hashlib.md5(xo).hexdigest()[:8])
    if sample:
        raw = open(sample, "rb").read()
        xls, info = convert(raw)
        ck("the sample converts (%d rows)" % info["rows"], len(xls) > 4096)
    print("SELFTEST " + ("OK" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest(sys.argv[2] if len(sys.argv) > 2 else None))
    if len(sys.argv) == 3:
        x, info = convert(open(sys.argv[1], "rb").read())
        open(sys.argv[2], "wb").write(x)
        print("wrote %s (%d rows, md5 %s)" % (sys.argv[2], info["rows"], hashlib.md5(x).hexdigest()))
        sys.exit(0)
    print(__doc__)
