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

S480 (D675, 05-Oct-2026 -- "the system reads every report the shop exports, in text"): Marg's Excel export is its text page cut into
  cells at the column heads (measured: three same-moment pairs, 4,141 cells, none different). So every other report is read by ONE
  cutter (page_to_sheet: a word belongs to the column in which it ends; a line that is one run of words is one cell) and a short
  spec (TEXT_SPECS: title, heads, end, integrity check) -- purchase (four shapes), the salt, category and item lists, the short sale
  statement, sale return (two shapes), the batch-wise valuation, expiry, the stock register. The three readers above are not
  touched: every text they took converts to the same bytes. AN EMPTY REPORT IS AN ANSWER: a sale report with no bill, dated a day
  BEFORE the day it was exported, is a no-sale day (title, heads, its one total row); dated the export day it is refused in the
  staff's words -- today is not over. Other empties are recognised and refused as EMPTY until a real empty sample is verified.

    python marg_txt.py report.txt out.XLS      convert one file
    python marg_txt.py --selftest               prove it
"""
import os, re, struct, sys, hashlib

VERSION = "S490"
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
    """"SALE", "STOCK", "ORDER" (S454) -- the three live kinds answer first -- then the kind word of a TEXT_SPECS entry (S480):
    PURCHASE, SALT, CATEGORY, ITEMS, SALE_SHORT, RETURN, VALUATION, EXPIRY, LEDGER. Or None."""
    if not raw or len(raw) > MAX_BYTES or raw[:4] in (b"\xd0\xcf\x11\xe0", b"PK\x03\x04", b"%PDF"):
        return None
    t = raw.decode("latin-1")
    head = t[:4000]
    if END in t[-400:]:
        # S480: SALE is the statement whose own head line carries CASH -- a short statement's bill rows say .CASH too
        if TITLE in head and any(l.startswith("BILL NO.") and "CASH" in l for l in head.replace("\r", "\n").split("\n")):
            return "SALE"
        if RE_STOCK_TITLE.search(head) and RE_STOCK_HEAD.search(head):
            return "STOCK"
        if ORDER_TITLE in head and RE_ORDER_HEAD.search(head):                 # S454 (D666)
            return "ORDER"
    sp = spec_of(raw)                                                          # S480: the end test is each spec's own
    return sp["kind"] if sp else None


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
# an item line: two spaces, the name, ONE space or more, the packing (a stray full stop allowed), the entry number, the
# S490 (F-756): the packing is whatever stands in its place -- 1*10, 30GM, 200ML, VAIL, 1 -- not only N*M (a sheet with a gel on it
# was refused whole on 06-Oct-2026); it must stand in the same column on every item line of the sheet (order_rows checks).
# date, order qty, receive, pending, rate, value -- and the two trailing heads (due date, party order no.) when Marg fills them.
# A name that fills its column leaves a single space before the packing, so the split is on the packing + entry shape, never on
# "two or more spaces".
RE_ORDER_ITEM = re.compile(r"^  (\S.*?) +(\S+?)\.? +([A-Z]{1,4}-\d+) +(\d\d-\d\d-\d{4}) +(" + _Q + r") +(-|" + _Q + r") +(" + _Q +
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
    pack_col = None                                             # S490: where this sheet's packing column starts

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
            if pack_col is None:
                pack_col = m.start(2)
            elif m.start(2) != pack_col:                        # S490: read by its place; a line that does not fit is refused, never guessed
                raise Refused("line %d: the packing does not stand in its column (col %d, the sheet's is %d)" % (n, m.start(2) + 1, pack_col + 1))
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


# ------------------------------------------------------------------------ S480 (D675): the cutter and the specs
# Marg's Excel export is its text page cut into cells at the column heads (measured 04-Oct-2026: three same-moment pairs, 4,141 cells,
# none different). So every other report is read by ONE cutter and a short spec, and what comes out is the sheet Marg's own Excel export
# would have been. The three readers above (sale, closing stock, order sheet) are not touched and answer first.
RE_RULE = re.compile(r"^\s*[-=]{8,}\s*$")
RE_CELL_NUM = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?$")     # _num's rule; an all-digit run with a leading zero stays text, as in Marg's sheet
RE_RUN = re.compile(r"\S+(?: \S+)*")
RE_SERIAL = re.compile(r"^(\d+)\s{2,}\S")
RE_MONEY_TAIL = re.compile(r"((?:\s+-?\d+\.\d\d){8})\s*$")
TODAY_WORDS = "aaj ki report — kal ki tareekh chun kar dobara banaiye"


class EmptyReport(Refused):
    """The report has its title, heads and end, and no line under them. Kept; verified only where its spec says an empty one is an answer."""


class TodayNotOver(Refused):
    """A sale report with no bill, dated the day it was exported: that day is not over. The same bytes exported on a later day are taken."""


def _runs(line):
    """(start, end) of every run of words: words one space apart are one run, two or more spaces part them."""
    return [(m.start(), m.end()) for m in RE_RUN.finditer(line)]


def _col_starts(head_lines):
    """Rule A: the column starts are where the column heads start. A second head line adds a column only where its head stands clear of
    every head of the first line (the item list's S.RATE and M.R.P.); a head under one of the first line's is that same column."""
    cols = [[a, b] for a, b in _runs(head_lines[0])]
    for hl in head_lines[1:]:
        for a, b in _runs(hl):
            hit = [c for c in cols if a < c[1] and c[0] < b]
            if hit:
                hit[0][0] = min(hit[0][0], a)
            else:
                cols.append([a, b])
    return sorted(c[0] for c in cols)


def _cell(v):
    return float(v) if RE_CELL_NUM.match(v) else v


def _cut(line, starts):
    """Rule A: a word belongs to the column in which it ENDS; words landing in one column keep their own spacing; a cell that is wholly
    a number is a number."""
    cells = [""] * len(starts)
    span = {}
    for m in re.finditer(r"\S+", line):
        e = m.end() - 1
        c = 0
        for i, s in enumerate(starts):
            if s <= e:
                c = i
        a, b = span.get(c, (m.start(), m.end()))
        span[c] = (min(a, m.start()), max(b, m.end()))
    for c, (a, b) in span.items():
        cells[c] = _cell(line[a:b])
    return cells


def _one_run(line):
    """Rule B: a line that is one run of words (single spaces only), flush left, more than one word and not a serial with its name."""
    s = line.strip()
    return (line == line.lstrip() and " " in s and not re.search(r"\S {2,}\S", s) and not re.match(r"^\d+ ", s))


def _heads_of(lines, spec):
    """(index of the first ruled line, the head lines) when the page's heads are this spec's; else None."""
    i0 = next((k for k, l in enumerate(lines[:60]) if RE_RULE.match(l)), None)
    if i0 is None:
        return None
    hl = [l.rstrip() for l in lines[i0 + 1:i0 + 1 + len(spec["heads"])]]
    if [[l[a:b] for a, b in _runs(l)] for l in hl] != spec["heads"]:
        return None
    return i0, hl


def _page(lines, spec):
    """(rows, the text line number of each row) -- the page cut into the cells Marg's own Excel export carries."""
    L = [l.rstrip() for l in lines]
    got = _heads_of(L, spec)
    if got is None:
        raise Refused("the column heads are not the ones expected")
    i0, hl = got
    starts = _col_starts(hl)
    n = len(starts)
    rows, at = [], []
    for k, l in enumerate(L):
        s = l.strip()
        if s == END:
            break
        if RE_RULE.match(l):
            continue                                            # a ruled line, whole or part: dropped
        if not s:
            row = [""] * n
        elif k < i0 or _one_run(l):
            row = [s] + [""] * (n - 1)                          # the letterhead and the title; a supplier heading, a salt name
        else:
            row = _cut(l, starts)
        rows.append(row)
        at.append(k + 1)
    while rows and not any(c != "" for c in rows[-1]):
        rows.pop()
        at.pop()
    return rows, at


def page_to_sheet(lines, spec):
    """A.1 -- the text page as the sheet Marg's Excel export of the same report is (rules A and B)."""
    return _page(lines, spec)[0]


def _f(v):
    """A money cell as a figure: '-' and '' are nothing."""
    if isinstance(v, float):
        return v
    v = str(v).strip()
    if v in ("", "-"):
        return 0.0
    if not RE_NUM.match(v):
        raise ValueError(v)
    return float(v)


def _near(a, b, n):
    """Marg rounds each line: a total re-added from n lines may differ by a rupee a line."""
    return abs(a - b) <= max(1, n) + 0.005


def _has(row, word):
    return any(isinstance(c, str) and c.strip() == word for c in row)


def _chk_purchase_billwise(rows, at, lines):
    cash = credit = 0.0
    n, total = 0, None
    for r, ln in zip(rows[_body(rows):], at[_body(rows):]):
        if r[0] == "TOTAL":
            total = (ln, _f(r[1]), _f(r[2]), _f(r[3]))
            continue
        if r[0] != "" and (isinstance(r[3], float) or isinstance(r[2], float)) and not _is_head(r):
            if total is not None:
                raise Refused("line %d: a bill after the TOTAL" % ln)
            cash, credit, n = cash + _f(r[2]), credit + _f(r[3]), n + 1
    if total is None:
        raise Refused("no TOTAL line")
    if not n:
        raise EmptyReport("no bills")
    if not (_near(total[2], cash, n) and _near(total[3], credit, n) and _near(total[1], cash + credit, n)):
        raise Refused("line %d: the TOTAL printed (%.2f) is not the sum of the bills (%.2f)" % (total[0], total[1], cash + credit))


def _chk_purchase_supplierwise(rows, at, lines):
    sc = sr = gc = gr = 0.0
    sn = gn = 0
    grand = None
    for r, ln in zip(rows[_body(rows):], at[_body(rows):]):
        if _is_head(r):
            continue
        if _words(r).startswith("GRAND TOTAL"):
            grand = (ln, _f(r[2]), _f(r[3]), _f(r[4]))
            continue
        if _has(r, "TOTAL :"):
            if not sn:
                raise Refused("line %d: a supplier TOTAL with no bill above it" % ln)
            if not (_near(_f(r[3]), sc, sn) and _near(_f(r[4]), sr, sn) and _near(_f(r[2]), sc + sr, sn)):
                raise Refused("line %d: a supplier's TOTAL (%.2f) is not the sum of its bills (%.2f)" % (ln, _f(r[2]), sc + sr))
            gc, gr, gn = gc + sc, gr + sr, gn + sn
            sc = sr = 0.0
            sn = 0
            continue
        if (isinstance(r[4], float) or r[4] == "-") and (isinstance(r[3], float) or r[3] == "-"):
            if grand is not None:
                raise Refused("line %d: a bill after the GRAND TOTAL" % ln)
            sc, sr, sn = sc + _f(r[3]), sr + _f(r[4]), sn + 1
    if sn:
        raise Refused("the last supplier's bills have no TOTAL")
    if grand is None:
        raise Refused("no GRAND TOTAL line")
    if not gn:
        raise EmptyReport("no bills")
    if not (_near(grand[2], gc, gn) and _near(grand[3], gr, gn) and _near(grand[1], gc + gr, gn)):
        raise Refused("line %d: the GRAND TOTAL printed (%.2f) is not the sum of the bills (%.2f)" % (grand[0], grand[1], gc + gr))


def _chk_purchase_items(grouped):
    """SUPPLIER/ITEM WISE (grouped: a TOTAL under every supplier, then the GRAND TOTAL) and BILL/ITEM WISE (one TOTAL at the end)."""
    def chk(rows, at, lines):
        sa = sv = ga = gv = 0.0
        sn = gn = 0
        end = None
        for r, ln in zip(rows[_body(rows):], at[_body(rows):]):
            if _is_head(r):
                continue
            if _words(r).startswith("GRAND TOTAL") if grouped else r[0] == "TOTAL":
                end = (ln, _f(r[9]), _f(r[11]))
                continue
            if grouped and _has(r, "TOTAL"):
                if not sn:
                    raise Refused("line %d: a supplier TOTAL with no line above it" % ln)
                if not (_near(_f(r[9]), sa, sn) and _near(_f(r[11]), sv, sn)):
                    raise Refused("line %d: a supplier's TOTAL (%.2f) is not the sum of its lines (%.2f)" % (ln, _f(r[9]), sa))
                ga, gv, gn = ga + sa, gv + sv, gn + sn
                sa = sv = 0.0
                sn = 0
                continue
            if isinstance(r[11], float) and r[9] != "":
                if end is not None:
                    raise Refused("line %d: an item line after the last TOTAL" % ln)
                try:
                    amt = _f(str(r[9]).split()[0]) if isinstance(r[9], str) else r[9]
                except ValueError:
                    raise Refused("line %d: an item line whose amount cannot be read" % ln)
                sa, sv, sn = sa + amt, sv + r[11], sn + 1
        if grouped and sn:
            raise Refused("the last supplier's lines have no TOTAL")
        if not grouped:
            ga, gv, gn = sa, sv, sn
        if end is None:
            raise Refused("no %s line" % ("GRAND TOTAL" if grouped else "TOTAL"))
        if not gn:
            raise EmptyReport("no item lines")
        if not (_near(end[1], ga, gn) and _near(end[2], gv, gn)):
            raise Refused("line %d: the total printed (%.2f) is not the sum of the lines (%.2f)" % (end[0], end[1], ga))
    return chk


def _chk_list(grouped):
    """The lists carry no totals: the serials run unbroken (under each heading, or 1..n), every Continued..N is answered by Page No..N."""
    def chk(rows, at, lines):
        want, owed, items = 1, None, 0
        for r, ln in zip(rows[_body(rows):], at[_body(rows):]):
            cells = [c for c in r if c != ""]
            if not cells or _is_head(r):
                continue
            txt = [c.strip() for c in cells if isinstance(c, str)]
            mc = [RE_CONT.match(c) for c in txt if RE_CONT.match(c)]
            if mc:
                if owed is not None:
                    raise Refused("line %d: a second Continued before the next page began" % ln)
                owed = int(mc[0].group(1))
                continue
            if len(txt) >= 2 and txt[-2] == "Page" and re.match(r"^No\.\.\d+$", txt[-1]):
                page = int(txt[-1][4:])
                if owed != page:
                    raise Refused("line %d: Page No..%d where %s was due" % (ln, page, ("Continued..%d" % owed) if owed else "no new page"))
                owed = None
                continue
            m = RE_SERIAL.match(r[0]) if isinstance(r[0], str) else None
            sno = int(m.group(1)) if m else (int(r[0]) if isinstance(r[0], float) and r[0] == int(r[0]) else None)
            if sno is not None:
                if owed is not None:
                    raise Refused("line %d: an item where Page No..%d was due" % (ln, owed))
                if sno != want:
                    raise Refused("line %d: item %d where %d was due" % (ln, sno, want))
                want, items = want + 1, items + 1
                continue
            if grouped and isinstance(r[0], str) and r[0].strip() and owed is None:
                want = 1                                        # a heading: a salt, a category (it may carry a figure and a code)
        if owed is not None:
            raise Refused("Continued..%d is not answered by a page" % owed)
        if not items:
            raise EmptyReport("no items")
    return chk


def _chk_sale_short(rows, at, lines):
    """The short statement (BILL NO. | DESCRIPTION | BILL VALUE): the footer's bill count is the bills read, its total their sum."""
    n, tot, foot = 0, 0.0, None
    for r, ln in zip(rows[_body(rows):], at[_body(rows):]):
        if isinstance(r[0], str) and r[0].startswith("Total No. of"):
            m = re.search(r"Bills:\s*(\d+)", "%s %s" % (r[0], r[1]))
            if m and "GRAND TOTAL" in str(r[1]):
                foot = (ln, int(m.group(1)), _f(r[2]))
            elif m and "DAY TOTAL" in str(r[1]) and foot is None:
                foot = (ln, int(m.group(1)), _f(r[2]))
            continue
        if isinstance(r[0], str) and RE_BILL.match(r[0]):
            if not isinstance(r[2], float):
                raise Refused("line %d: a bill whose value cannot be read" % ln)
            n, tot = n + 1, tot + r[2]
    if foot is None:
        raise Refused("no 'Total No. of Bills' line")
    if foot[1] != n:
        raise Refused("line %d: the footer says %d bills, %d were read" % (foot[0], foot[1], n))
    if not _near(foot[2], tot, n):
        raise Refused("line %d: the total printed (%.2f) is not the sum of the bills (%.2f)" % (foot[0], foot[2], tot))


def _chk_return_short(rows, at, lines):
    n, tot, total = 0, 0.0, None
    for r, ln in zip(rows[_body(rows):], at[_body(rows):]):
        if _is_head(r):
            continue
        if isinstance(r[0], str) and r[0].replace(" ", "").upper() == "TOTAL":      # printed spaced: T o t a l
            total = (ln, _f(r[3]))
            continue
        if r[0] != "" and isinstance(r[3], float):
            if total is not None:
                raise Refused("line %d: a bill after the total" % ln)
            n, tot = n + 1, tot + r[3]
    if total is None:
        raise Refused("no 'T o t a l' line")
    if not n:
        raise EmptyReport("no bills")
    if not _near(total[1], tot, n):
        raise Refused("line %d: the total printed (%.2f) is not the sum of the bills (%.2f)" % (total[0], total[1], tot))


def _chk_return_detail(rows, at, lines):
    """Eight money columns under six heads: re-added from the printed line itself."""
    sums, n, total = [0.0] * 8, 0, None
    for r, ln in zip(rows[_body(rows):], at[_body(rows):]):
        if _is_head(r) or r[0] == "" or RE_DATE.match(str(r[0]).strip()):
            continue
        m = RE_MONEY_TAIL.search(lines[ln - 1].rstrip())
        if not m:
            continue
        v = [float(x) for x in m.group(1).split()]
        if str(r[0]).strip() == "TOTAL":
            total = (ln, v)
            continue
        if total is not None:
            raise Refused("line %d: a bill after the TOTAL" % ln)
        sums, n = [a + b for a, b in zip(sums, v)], n + 1
    if total is None:
        raise Refused("no TOTAL line")
    if not n:
        raise EmptyReport("no bills")
    if not all(_near(a, b, n) for a, b in zip(total[1], sums)):
        raise Refused("line %d: the TOTAL printed (%.2f) is not the sum of the bills (%.2f)" % (total[0], total[1][-1], sums[-1]))


def _chk_valuation(rows, at, lines):
    """Taken as nothing (the owner, 04-Oct-2026): structural only -- items, and the TOTAL row last."""
    if not any(isinstance(r[0], str) and re.match(r"^\d+ \S", r[0]) for r in rows):
        raise EmptyReport("no items")
    if rows[-1][0] != "TOTAL":
        raise Refused("the TOTAL row is not the last line")


def _chk_expiry(rows, at, lines):
    """The TOTAL row equals the batch stocks in single units: strips x the printed pack + loose. Batch TOTAL rows are furniture."""
    units, n, total = 0, 0, None
    for r, ln in zip(rows[_body(rows):], at[_body(rows):]):
        if r[0] == "TOTAL":
            total = (ln, [c for c in r[1:] if c != ""])
            continue
        m = re.match(r"^(\d+) (\S.*)$", r[0]) if isinstance(r[0], str) else None
        if not m:
            continue
        if total is not None:
            raise Refused("line %d: a batch after the TOTAL" % ln)
        q = str(r[3]).split()[0] if isinstance(r[3], str) and r[3].strip() else ("%d" % r[3] if isinstance(r[3], float) else "")
        if not RE_QTY.match(q):
            raise Refused("line %d: batch %s's stock cannot be read" % (ln, m.group(1)))
        units += _stock_units(q, m.group(2))
        n += 1
    if total is None or len(total[1]) != 1 or not isinstance(total[1][0], float):
        raise Refused("no TOTAL line")
    if not n:
        raise EmptyReport("no batches")
    if int(total[1][0]) != units:
        raise Refused("line %d: the TOTAL printed (%d) is not the sum of the batches (%d)" % (total[0], int(total[1][0]), units))


def _chk_ledger(rows, at, lines):
    """Structural only in S480: the register closes on its Received : / Issued : pair, each once."""
    rec = [i for i, r in enumerate(rows) if _words(r).startswith("Received :")]
    iss = [i for i, r in enumerate(rows) if _words(r).startswith("Issued :")]
    if len(rec) != 1 or len(iss) != 1 or iss[0] != rec[0] + 1 or iss[0] != len(rows) - 1:
        raise Refused("the register does not close on one Received : / Issued : pair")


_FIRST_HEADS = ("BILL NO.", "BILL", "SUPPLIER NAME", "S.No. DESCRIPTION", "S.No. Description", "Bill No. /")


def _is_head(r):
    """A row of column heads (the first head line, at the top of every page)."""
    return isinstance(r[0], str) and r[0] in _FIRST_HEADS and any(c != "" for c in r[1:])


def _words(r):
    """The row's words, in order, whatever cells they fell into ('GRAND' | 'TOTAL' is GRAND TOTAL)."""
    return " ".join(" ".join(str(c).split()) for c in r if isinstance(c, str) and c.strip())


def _body(rows):
    """The first row after the first row of column heads."""
    return next((i + 1 for i, r in enumerate(rows) if _is_head(r)), 0)


_PUR_ITEM_HEADS = [["BILL", "ITEM DESCRIPTION", "PACKING BATCH", "EXP.", "TAX", "QTY.", "FREE", "RATE", "DIS.", "AMOUNT NET RATE",
                    "LOOS PURC. ?", "AMOUNT"]]
_LIST_HEADS = [["S.No. DESCRIPTION", "PACKING", "P.RATE", "S.RATE", "M.R.P."]]
# One entry per report: its title, its column heads as printed (one line or two), the word the refusal note carries, how it ends
# (Marg's end mark, or the register's own closing pair), its integrity check, and whether a page with no body row is an answer.
# empty_ok is False everywhere here: purchase, return, expiry and order empties wait for a real empty sample (D675 a); they are
# RECOGNISED and KEPT by the watcher, never dropped. The one verified empty is the sale day (to_rows above).
TEXT_SPECS = [
    dict(key="PURCHASE_BILLWISE", kind="PURCHASE", title=r"^BILL WISE PURCHASE STATEMENT\b",
         heads=[["BILL NO.", "PARTY NAME", "CASH", "CREDIT"]], end="mark", check=_chk_purchase_billwise, empty_ok=False),
    dict(key="PURCHASE_ITEMWISE", kind="PURCHASE", title=r"^SUPPLIER/ITEM WISE PURCHASE STATEMENT\b",
         heads=_PUR_ITEM_HEADS, end="mark", check=_chk_purchase_items(True), empty_ok=False),
    dict(key="PURCHASE_SUPPLIERWISE", kind="PURCHASE", title=r"^SUPPLIER WISE PURCHASE STATEMENT\b",
         heads=[["SUPPLIER NAME", "DATE", "BILL NO.", "CASH", "CREDIT"]], end="mark", check=_chk_purchase_supplierwise, empty_ok=False),
    dict(key="PURCHASE_BILLITEMWISE", kind="PURCHASE", title=r"^BILL/ITEM WISE PURCHASE STATEMENT\b",
         heads=_PUR_ITEM_HEADS, end="mark", check=_chk_purchase_items(False), empty_ok=False),
    dict(key="SALT_WISE_ITEM_LIST", kind="SALT", title=r"^SALT WISE ITEM LIST$",
         heads=_LIST_HEADS, end="mark", check=_chk_list(True), empty_ok=False),
    dict(key="CATEGORY_WISE_ITEM_LIST", kind="CATEGORY", title=r"^CATEGORY WISE ITEM LIST$",
         heads=_LIST_HEADS, end="mark", check=_chk_list(True), empty_ok=False),
    dict(key="ITEM_MASTER", kind="ITEMS", title=r"^LIST OF ITEMS$",
         heads=[["S.No. DESCRIPTION", "PACKING", "Compnay"], ["P.RATE", "S.RATE", "M.R.P."]], end="mark", check=_chk_list(False),
         empty_ok=False),
    dict(key="SALE_BILLWISE_SUMMARY1", kind="SALE_SHORT", title=r"^BILL WISE SALES STATEMENT\b",
         heads=[["BILL NO.", "DESCRIPTION", "BILL VALUE"]], end="mark", check=_chk_sale_short, empty_ok=False),
    dict(key="SALE_RETURN_SUMMARY", kind="RETURN", title=r"^SALE RETURN\b",
         heads=[["BILL NO.", "DATE", "PARTY", "AMOUNT"]], end="mark", check=_chk_return_short, empty_ok=False),
    dict(key="SALE_RETURN_DETAIL", kind="RETURN", title=r"^SALE RETURN\b",
         heads=[["BILL NO.", "PARTY NAME", "GROSS AMOUNT TRADE DIS. CASH DISCO", "PACKING CASH DISCO", "SALES TAX",
                 "OTHER \xb1 BILL VALUE"]], end="mark", check=_chk_return_detail, empty_ok=False),
    dict(key="STOCK_VALUATION_BATCHWISE", kind="VALUATION", title=r"^WHOLE STORES STOCK VALUATION\b",
         heads=[["S.No. Description", "Batch", "M.R.P.", "Exp.Date", "Stock", "Rate", "Value"]], end="mark", check=_chk_valuation,
         empty_ok=False),
    dict(key="STOCK_EXPIRY", kind="EXPIRY", title=r"^EXP\. BEFORE\b",
         heads=[["S.No. Description", "Batch", "Expiry", "Stock Unit"]], end="mark", check=_chk_expiry, empty_ok=False),
    dict(key="STOCK_ITEM_LEDGER_TEXT", kind="LEDGER", title=r"^STOCK REGISTER WHOLE\b",
         heads=[["Bill No. /", "Type", "Patient Name", "Doctor Name", "Batch", "Quantity", "Value", "Balance"],
                ["Date", "No.", "Quantity"]], end="pair", check=_chk_ledger, empty_ok=False),
]


def _lines_of(raw):
    return raw.decode("latin-1").replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _ends(t, spec):
    """The end-mark test, per spec: Marg's end mark in the tail -- or, for the register, its own closing pair (it prints no end mark)."""
    tail = t[-1200:] if spec["end"] == "pair" else t[-400:]
    if spec["end"] == "pair":
        return bool(re.search(r"Received :.*\n\s*Issued :", tail.replace("\r", "")))
    return END in tail


def spec_of(raw):
    """The TEXT_SPECS entry this text is a complete export of (title, heads and end all present), or None."""
    if not raw or len(raw) > MAX_BYTES or raw[:4] in (b"\xd0\xcf\x11\xe0", b"PK\x03\x04", b"%PDF"):
        return None
    t = raw.decode("latin-1")
    lines = t[:6000].replace("\r\n", "\n").replace("\r", "\n").split("\n")
    i0 = next((k for k, l in enumerate(lines[:60]) if RE_RULE.match(l)), None)
    if i0 is None:
        return None
    title = next((l.strip() for l in reversed(lines[:i0]) if l.strip()), "")
    for sp in TEXT_SPECS:
        if re.search(sp["title"], title) and _heads_of(lines, sp) is not None and _ends(t, sp):
            return sp
    return None


def spec_rows(raw):
    """The sheet of a report read through the cutter; refused, with the line and the reason, when its own figures do not hold."""
    sp = spec_of(raw)
    if sp is None:
        raise NotThisReport("not a complete text export of a report this reader has a spec for")
    lines = _lines_of(raw)
    rows, at = _page(lines, sp)
    try:
        sp["check"](rows, at, lines)
    except EmptyReport as ex:
        if not sp["empty_ok"]:
            raise EmptyReport("an empty report (%s) -- kept; not taken until a real empty sample of this report has been verified" % ex)
    except (ValueError, IndexError) as ex:
        raise Refused("a figure that cannot be read: %s" % str(ex)[:60])
    return rows


def _export_day(x):
    """The day a text was exported: a file time (seconds), a datetime, a date, or a kept copy's own stamp (YYYYmmdd-HHMMSS)."""
    import datetime as _dt
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return _dt.datetime.fromtimestamp(x).date()
    if isinstance(x, _dt.datetime):
        return x.date()
    if isinstance(x, _dt.date):
        return x
    m = re.match(r"^(\d{4})(\d{2})(\d{2})-\d{6}", str(x))
    return _dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def _empty_day(rows, foot, exported_at):
    """D675 a (F-729): a sale report with its title, heads and end mark, no bill and no item line, and the one row
    'Total No. of Bills: 0 ... DAY TOTAL' of zeros is a NO-SALE DAY -- when its AS ON day is before the day it was exported.
    Returns (rows, info), or None when the text is not that shape; raises for the same shape whose day is not over."""
    import datetime as _dt
    if foot is None or len(rows) != 3 or rows[2][2] != "DAY TOTAL :":
        return None
    bills, nums = foot
    mb = re.match(r"^Bills:\s*(\d+)$", bills)
    if not mb or int(mb.group(1)) != 0 or any(v != 0.0 for v in nums):
        return None
    mt = re.search(r"\bAS ON (\d{2})-(\d{2})-(\d{4})\s*$", rows[0][0])
    if not mt:
        return None
    try:
        as_on = _dt.date(int(mt.group(3)), int(mt.group(2)), int(mt.group(1)))
    except ValueError:
        return None
    day = _export_day(exported_at)
    if day is None:
        raise Refused("a sale report with no bill, and the time it was exported is not known -- its day cannot be called over")
    if as_on >= day:
        raise TodayNotOver(TODAY_WORDS)
    sheet = [rows[0], rows[1], ["Total No. of", bills, "DAY TOTAL :"] + nums]
    return sheet, {"empty": True, "as_on": "%s-%s-%s" % (mt.group(1), mt.group(2), mt.group(3))}


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


def to_rows(raw, exported_at=None):
    """The nine-column sheet, as a list of rows of cells (str, or float for a number). S480: exported_at is the file's own time --
    it decides whether a report with no bill is a day that is over (see _empty_day)."""
    return _sale_rows(raw, exported_at)[0]


def _sale_rows(raw, exported_at=None):
    """(rows, extra) -- extra is {} for a report with bills, {"empty": True, "as_on": dd-mm-yyyy} for a no-sale day."""
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
    foot = None                                                          # S480: a DAY TOTAL row that carries the bill count
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
                m0 = re.search(r"Total No\. of\s+(Bills:\s*\d+)", s)             # S480: the zero-bill day prints its count here
                if m0:
                    foot = (m0.group(1), nums)
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
        empty = _empty_day(rows, foot, exported_at)                      # S480 (D675 a, F-729): the no-sale day
        if empty is None:
            raise Refused("no GRAND TOTAL line")
        return empty
    return rows, {}


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


def convert(raw, exported_at=None):
    """(xls_bytes, info) for a text export; raises NotThisReport / Refused. S480: exported_at -- the file's own time, or a kept
    copy's stamp -- is what tells a no-sale day from a report of today; info carries "empty" and "as_on" for a no-sale day."""
    k = kind(raw)
    extra = {}
    if k == "STOCK":
        rows = stock_rows(raw)
    elif k == "ORDER":                                                   # S454
        rows = order_rows(raw)
    elif k in (None, "SALE"):
        rows, extra = _sale_rows(raw, exported_at)
    else:                                                                # S480: a report read through the cutter
        rows = spec_rows(raw)
    info = {"rows": len(rows), "version": VERSION, "kind": k or "SALE"}
    info.update(extra)
    return ole2(workbook_stream(rows)), info


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


# ------------------------------------------------------------------------ S480: made-up texts, one per spec (F-185: no real sample)
def _t(*parts):
    """A printed line: (column, text) -- the text starts at the column; a negative column means the text ENDS at that column."""
    s = ""
    for col, txt in parts:
        a = col if col >= 0 else (-col - len(txt) + 1)
        s = s.ljust(a) + txt
    return s


def _txt(lines, tail=0):
    return ("\r\n".join(lines) + "\r\n" + "\r\n" * tail).encode("latin-1")


_R80, _R132 = "-" * 80, "-" * 132
_LETTER = ["", _t((31, "TEST MEDICOS")), _t((24, "TEST STREET , TESTTOWN")), _t((16, "GSTIN : TESTGST  TIN No. : TESTTIN")), ""]
_PI_HEAD = _t((0, "BILL"), (8, "ITEM DESCRIPTION"), (36, "PACKING BATCH"), (53, "EXP."), (60, "TAX"), (66, "QTY."), (72, "FREE"),
              (80, "RATE"), (86, "DIS."), (93, "AMOUNT NET RATE"), (111, "LOOS PURC. ?"), (126, "AMOUNT"))
_LIST_HEAD = _t((0, "S.No. DESCRIPTION"), (36, "PACKING"), (56, "P.RATE"), (65, "S.RATE"), (74, "M.R.P."))


def _pi_item(bill, name, batch, amt, net):
    return _t((0, bill), (8, name), (36, "1*10"), (44, batch), (-56, "1/31"), (-62, "5.00"), (-69, "10"), (-83, "100.00"), (-89, "0.00"),
              (-98, amt), (-107, "10.00"), (-114, "100"), (-122, "100.00"), (-131, net))


def _pi_total(word_at, word, amt, net):
    return _t((word_at, word), (-98, amt), (-131, net))


def _list_item(sno, name, pack, mrp):
    return _t((0, str(sno)), (6, name), (36, pack), (-61, "10.00"), (-70, "0.00"), (-79, mrp))


def _list_page2(title):
    return [_R80, _t((66, "Continued..2")), "", "", "", "", "TEST MEDICOS", title, _t((68, "Page No..2")), _R80, _LIST_HEAD, _R80]


def _s480_samples():
    """name -> a made-up text export in the layout Marg prints (invented names, invented figures)."""
    S = {}
    S["PURCHASE_BILLWISE"] = _txt([
        _t((11, "BILL WISE PURCHASE STATEMENT FROM 01-01-2030 TO 02-01-2030")), _R80,
        _t((0, "BILL NO."), (13, "PARTY NAME"), (63, "CASH"), (73, "CREDIT")), _R80,
        "01-01-2030",
        _t((0, "101"), (13, "TEST PHARMA ONE"), (-66, "-"), (-78, "1000.00")),
        _t((0, "A00012"), (13, "DEMO AGENCY"), (43, "TESTTOWN"), (-66, "-"), (-78, "500.50")),
        "02-01-2030",
        _t((0, "0077"), (13, "TEST PHARMA ONE"), (-66, "-"), (-78, "250.00")),
        _R80, _t((0, "TOTAL"), (-54, "1750.50"), (-66, "-"), (-78, "1750.50")), _R80, END])
    S["PURCHASE_ITEMWISE"] = _txt([
        _t((7, "SUPPLIER/ITEM WISE PURCHASE STATEMENT FROM 01-01-2030 TO 02-01-2030")), _R132, _PI_HEAD, _R132,
        "TEST PHARMA ONE",
        _pi_item("101", "TESTCILLIN 500", "TB001", "1000.00", "1050.00"),
        _t((80, "-" * 52)), _pi_total(80, "TOTAL", "1000.00", "1050.00"),
        _t((0, "DEMO AGENCY"), (30, "TESTTOWN")),
        _pi_item("0077", "DEMOCIN TAB", "DB07", "200.25", "210.00"),
        _pi_item("0077", "DEMOGEL", "540021", "300.25", "315.50"),
        _t((80, "-" * 52)), _pi_total(80, "TOTAL", "500.50", "525.50"),
        _R132, _pi_total(0, "GRAND TOTAL", "1500.50", "1575.50"), _R132, END])
    S["PURCHASE_SUPPLIERWISE"] = _txt([
        _t((9, "SUPPLIER WISE PURCHASE STATEMENT FROM 01-01-2030 TO 31-01-2030")), _R80,
        _t((0, "SUPPLIER NAME"), (32, "DATE"), (43, "BILL NO."), (63, "CASH"), (73, "CREDIT")), _R80,
        _t((0, "TEST PHARMA ONE"), (32, "02-01-2030"), (43, "101"), (-66, "-"), (-78, "1000.00")),
        _t((32, "09-01-2030"), (43, "0077"), (-66, "-"), (-78, "250.00")),
        _t((36, "-" * 44)), _t((36, "TOTAL :"), (-54, "1250.00"), (-66, "-"), (-78, "1250.00")), "",
        _t((0, "DEMO AGENCY"), (32, "05-01-2030"), (43, "A00012"), (-66, "-"), (-78, "500.50")),
        _t((36, "-" * 44)), _t((36, "TOTAL :"), (-54, "500.50"), (-66, "-"), (-78, "500.50")), "",
        _R80, _t((0, "GRAND TOTAL"), (-54, "1750.50"), (-66, "-"), (-78, "1750.50")), _R80, END])
    S["PURCHASE_BILLITEMWISE"] = _txt([
        _t((9, "BILL/ITEM WISE PURCHASE STATEMENT FROM 01-01-2030 TO 02-01-2030")), _R132, _PI_HEAD, _R132, "",
        "01-01-2030",
        _pi_item("101", "TESTCILLIN 500", "TB001", "1000.00", "1050.00"),
        "02-01-2030",
        _pi_item("0077", "DEMOCIN TAB", "DB07", "200.25", "210.00"),
        _pi_item("0077", "DEMOGEL", "540021", "300.25", "315.50"),
        _R132, _pi_total(0, "TOTAL", "1500.50", "1575.50"), _R132, END])
    for key, title, heading in (("SALT_WISE_ITEM_LIST", "SALT WISE ITEM LIST", "TESTSALT ONE + TWO"),
                                ("CATEGORY_WISE_ITEM_LIST", "CATEGORY WISE ITEM LIST", _t((0, "TESTCAT"), (-46, "0.00"), (57, "D98")))):
        S[key] = _txt([
            _t((32, "TEST MEDICOS")), _t((30, title)), _R80, _LIST_HEAD, _R80, "",
            _t((0, "1"), (-61, "0.00"), (-70, "0.00"), (-79, "0.00")), "",
            heading,
            _list_item(1, "TESTCILLIN 500", "1*10", "15.00"), _list_item(2, "DEMOCIN TAB", "1*10", "25.50"), "",
            "TESTSALT",
            _list_item(1, "DEMOGEL", "30GM", "99.00")]
            + _list_page2(title) + [
            _list_item(2, "DEMOGEL FORTE", "30GM", "120.00"), "",
            " OTHER SALT X",
            _list_item(1, "TEST WRIST SPLINT LF L ELASTI", "1*1", "450.00"), "", _R80, END, ""])
    S["ITEM_MASTER"] = _txt([
        _t((32, "TEST MEDICOS")), "", _t((34, "LIST OF ITEMS")), _R80,
        _t((0, "S.No. DESCRIPTION"), (36, "PACKING"), (54, "Compnay")), _t((54, "P.RATE"), (63, "S.RATE"), (72, "M.R.P.")), _R80,
        _t((0, "1"), (54, "OTHER PRODUCTS")),
        _t((0, "2"), (6, "TESTCILLIN 500"), (36, "1*10"), (54, "TESTCO")),
        _t((0, "3"), (6, "DEMOCIN TAB"), (36, "1*10"), (54, "DEMO LABS")),
        _R80, _t((66, "Continued..2")), "", "", "", "", "TEST MEDICOS", "LIST OF ITEMS", _t((68, "Page No..2")), _R80,
        _t((0, "S.No. DESCRIPTION"), (36, "PACKING"), (54, "Compnay")), _R80,
        _t((0, "4"), (6, "DEMOGEL"), (36, "30GM"), (54, "DEMO LABS")),
        _R80, END, ""])
    S["SALE_BILLWISE_SUMMARY1"] = _txt([
        _t((18, "BILL WISE SALES STATEMENT AS ON 01-01-2030")), "-" * 78,
        _t((0, "BILL NO."), (12, "DESCRIPTION"), (68, "BILL VALUE")), "-" * 78,
        "01-01-2030",
        _t((0, "A000001"), (12, "TEST ONE 1001"), (54, ".CASH"), (-77, "80.00")),
        _t((0, "A000002"), (12, "TEST TWO"), (54, ".UPI"), (65, "#"), (-77, "540.00")),
        "-" * 78, _t((0, "Total No. of Bills: 2"), (56, "DAY TOTAL :"), (-78, "620.00")), "-" * 78, "", END])
    S["SALE_RETURN_SUMMARY"] = _txt(_LETTER[:-1] + [
        _t((19, "SALE RETURN FROM 01-01-2030 TO 31-01-2030")), "", "-" * 78,
        _t((0, "BILL NO."), (12, "DATE"), (18, "PARTY"), (72, "AMOUNT")), "-" * 78,
        _t((0, "CN00001"), (12, "02-01"), (18, "TEST ONE 1001"), (-77, "100.00")),
        _t((0, "CN00002"), (12, "09-01"), (18, "TEST TWO"), (-77, "50.50")),
        "-" * 78, _t((0, "T o t a l"), (-77, "150.50")), "-" * 78, "", END])

    def rd(first, *v):
        return _t(first, *[(-e, x) for e, x in zip((52, 63, 74, 85, 96, 107, 118, 129), v)])
    S["SALE_RETURN_DETAIL"] = _txt([
        _t((20, "SALE RETURN FROM 01-01-2030 TO 31-01-2030")), "-" * 130,
        _t((1, "BILL NO."), (13, "PARTY NAME"), (40, "GROSS AMOUNT TRADE DIS. CASH DISCO"), (78, "PACKING CASH DISCO"),
           (98, "SALES TAX"), (111, "OTHER \xb1 BILL VALUE")), "-" * 130,
        "02-01-2030",
        _t((1, "CN00001"), (13, "TEST ONE 1001"), (-52, "100.00"), (-63, "5.00"), (-74, "0.00"), (-85, "0.00"), (-96, "0.00"),
           (-107, "0.00"), (-118, "0.00"), (-129, "95.00")),
        "09-01-2030",
        _t((1, "CN00002"), (13, "TEST TWO"), (-52, "50.50"), (-63, "0.00"), (-74, "0.00"), (-85, "0.00"), (-96, "0.00"),
           (-107, "0.00"), (-118, "-0.50"), (-129, "50.00")),
        "-" * 130,
        rd((0, "TOTAL"), "150.50", "5.00", "0.00", "0.00", "0.00", "0.00", "-0.50", "145.00"), "-" * 130, "", "", END])
    S["STOCK_VALUATION_BATCHWISE"] = _txt(_LETTER + [
        _t((18, "WHOLE STORES STOCK VALUATION AS ON 01-01-2030")), _R132,
        _t((0, "S.No. Description"), (55, "Batch"), (72, "M.R.P."), (81, "Exp.Date"), (97, "Stock"), (112, "Rate"), (123, "Value")), _R132,
        _t((-4, "1"), (6, "TESTCILLIN 500"), (36, "1*10"), (55, "TB001"), (-77, "61.60"), (81, "Aug.,2031"), (-101, "3:2"),
           (-115, "49.288"), (-127, "152.80")), "",
        _t((-4, "2"), (6, "DEMOGEL"), (36, "30GM"), (-77, "402.19"), (-101, "-0:10"), (-115, "305.664"), (-127, "-203.77")),
        _t((-4, "3"), (6, "DEMOGEL"), (36, "30GM"), (55, "540021"), (-77, "99.00"), (81, "Feb.,2032"), (-101, "6"), (-115, "70.5"),
           (-127, "423.00")),
        _t((88, "-" * 44)), _t((73, "Batch TOTAL"), (-101, "-4"), (-127, "219.23")), "",
        _R132, _t((0, "TOTAL"), (-101, "28"), (-127, "372.03")), _R132, END], tail=12)
    S["STOCK_EXPIRY"] = _txt(_LETTER + [
        _t((30, "EXP. BEFORE *BA.,   0")), _R80,
        _t((0, "S.No. Description"), (44, "Batch"), (57, "Expiry"), (70, "Stock Unit")), _R80,
        _t((-4, "1"), (6, "TESTCILLIN 500"), (37, "1*10"), (44, "TB001"), (-62, "11/2030"), (-75, "3:2"), (77, "STR")), "",
        _t((-4, "2"), (6, "DEMOGEL"), (37, "30GM"), (44, "540021"), (-62, "1/2031"), (-75, "-"), (77, "TUB")),
        _t((-4, "3"), (6, "DEMOGEL"), (37, "30GM"), (44, "540022"), (-62, "1/2031"), (-75, "6"), (77, "TUB")),
        _t((47, "-" * 33)), _t((47, "Batch TOTAL"), (-75, "6")), "",
        _t((-4, "4"), (6, "DEMOCIN TAB"), (37, "1*10."), (44, "DB07"), (-62, "12/2030"), (-75, "-1:3"), (77, "STR")), "",
        _R80, _t((0, "TOTAL"), (-75, "25")), _R80, END], tail=6)
    S["STOCK_ITEM_LEDGER_TEXT"] = _txt(_LETTER + [
        _t((16, "STOCK REGISTER WHOLE FROM 01-01-2030 - 31-01-2030")), _R132,
        _t((0, "Bill No. /"), (13, "Type"), (29, "Patient Name"), (55, "Doctor Name"), (81, "Batch"), (94, "Quantity"), (110, "Value"),
           (123, "Balance")),
        _t((2, "Date"), (82, "No."), (122, "Quantity")), _R132,
        "TESTCILLIN 500 1*10",
        _t((0, "Opening Balance as on 01-01-2030 TAB"), (-131, "43:7")),
        _t((0, "02-01-2030"), (13, "PURCHASE"), (29, "TEST PHARMA ONE"), (81, "TB001"), (-104, "10:0"), (-117, "1000.00"), (-131, "53:7")),
        "101",
        _t((0, "A000001"), (13, "SALE"), (29, "TEST ONE 1001"), (55, "TEST DOCTOR"), (81, "TB001"), (-104, "0:4"), (-117, "80.00"),
           (-131, "53:3")),
        _t((76, "-" * 56)),
        _t((76, "Received :"), (-104, "10:0"), (-117, "1000.00")),
        _t((78, "Issued :"), (-104, "0:4"), (-117, "80.00")),
        _t((76, "-" * 56))])
    return S


EMPTY_DAY_SAMPLE = _txt([
    _t((18, "BILL WISE SALES STATEMENT AS ON 02-01-2030")), _R132,
    "BILL NO.    DESCRIPTION                       D.R.          GROSS AMT.    DISCOUNT         TAX       DR/CR    NET AMT.        CASH",
    _R132, _R132,
    "Total No. of Bills: 0                         DAY TOTAL :         0.00        0.00        0.00        0.00        0.00        0.00",
    _R132, "", END])
# what marg_txt S454 (ed17bb76) made of its own three samples: S480 must make the same bytes of them (the brief's 9.1, in small)
_S454_BYTES = {"SALE": "e5918c7b103f5cbd39342b77ccc01406", "STOCK": "6239dbdc2b5462cabfa08f1f2d8cc1ce", "ORDER": "8845e680d2896c819d27f83d868c3a20"}


def _selftest_s480(ck):
    import datetime as _dt
    T, S_, O_ = SELFTEST_SAMPLE, STOCK_SAMPLE, ORDER_SAMPLE
    for k_, raw_ in (("SALE", T), ("STOCK", S_), ("ORDER", O_)):
        ck("S480: the %s text converts to the same bytes as before S480" % k_,
           hashlib.md5(convert(raw_)[0]).hexdigest() == _S454_BYTES[k_], hashlib.md5(convert(raw_)[0]).hexdigest()[:8])
    M = _s480_samples()
    want = {"PURCHASE_BILLWISE": "PURCHASE", "PURCHASE_ITEMWISE": "PURCHASE", "PURCHASE_SUPPLIERWISE": "PURCHASE",
            "PURCHASE_BILLITEMWISE": "PURCHASE", "SALT_WISE_ITEM_LIST": "SALT", "CATEGORY_WISE_ITEM_LIST": "CATEGORY",
            "ITEM_MASTER": "ITEMS", "SALE_BILLWISE_SUMMARY1": "SALE_SHORT", "SALE_RETURN_SUMMARY": "RETURN",
            "SALE_RETURN_DETAIL": "RETURN", "STOCK_VALUATION_BATCHWISE": "VALUATION", "STOCK_EXPIRY": "EXPIRY",
            "STOCK_ITEM_LEDGER_TEXT": "LEDGER"}
    ck("S480: one spec per report, each with its made-up text", sorted(M) == sorted(sp["key"] for sp in TEXT_SPECS) == sorted(want))
    bad = {"PURCHASE_BILLWISE": (b"250.00", b"350.00"), "PURCHASE_ITEMWISE": (b"300.25", b"900.25"),
           "PURCHASE_SUPPLIERWISE": (b"      250.00", b"      950.00"), "PURCHASE_BILLITEMWISE": (b"300.25", b"900.25"),
           "SALT_WISE_ITEM_LIST": (b"2     DEMOGEL FORTE", b"3     DEMOGEL FORTE"),
           "CATEGORY_WISE_ITEM_LIST": (b"Page No..2", b"Page No..3"), "ITEM_MASTER": (b"4     DEMOGEL", b"5     DEMOGEL"),
           "SALE_BILLWISE_SUMMARY1": (b"Bills: 2", b"Bills: 3"), "SALE_RETURN_SUMMARY": (b" 50.50", b"950.50"),
           "SALE_RETURN_DETAIL": (b"     50.00", b"    950.00"), "STOCK_VALUATION_BATCHWISE": (b"TOTAL" + b" " * 91, b"TOTEL" + b" " * 91),
           "STOCK_EXPIRY": (b"TOTAL" + b" " * 69 + b"25", b"TOTAL" + b" " * 69 + b"26"),
           "STOCK_ITEM_LEDGER_TEXT": (b"Issued :", b"Issue  :")}
    R = {}
    for key in sorted(M):
        raw_ = M[key]
        sp = spec_of(raw_)
        try:
            R[key] = spec_rows(raw_)
            got = True
        except (Refused, NotThisReport) as ex_:
            got = str(ex_)[:60]
        a_, b_ = bad[key]
        try:
            spec_rows(raw_.replace(a_, b_))
            neg = raw_.count(a_) and "taken"
        except (Refused, NotThisReport) as ex_:
            neg = True
        x1_, i1_ = (convert(raw_) if got is True else (b"", {}))
        ck("S480 %s: recognised as %s, its figures hold, one changed figure refuses, the same bytes every time"
           % (key, want[key]), sp is not None and sp["key"] == key and kind(raw_) == want[key] and got is True and neg is True
           and raw_.count(a_) >= 1 and x1_ == convert(raw_)[0] and i1_.get("kind") == want[key] and i1_.get("version") == VERSION,
           (sp and sp["key"], got, neg))
    ck("S480: a number is a number, a bill number with a leading zero stays as printed, '-' stays '-'",
       R["PURCHASE_BILLWISE"][3] == [101.0, "TEST PHARMA ONE", "-", 1000.0] and R["PURCHASE_BILLWISE"][6][0] == "0077"
       and R["PURCHASE_BILLWISE"][-1] == ["TOTAL", 1750.5, "-", 1750.5], R["PURCHASE_BILLWISE"][3])
    ck("S480 rule B: a supplier heading is one cell; rule A: a supplier and its town are cut at the column heads",
       R["PURCHASE_ITEMWISE"][2] == ["TEST PHARMA ONE"] + [""] * 11 and R["PURCHASE_ITEMWISE"][5][:3] == ["DEMO", "AGENCY", "TESTTOWN"]
       and R["PURCHASE_ITEMWISE"][3][9] == "1000.00    10.00" and R["PURCHASE_ITEMWISE"][3][11] == 1050.0, R["PURCHASE_ITEMWISE"][5][:3])
    sl = R["SALT_WISE_ITEM_LIST"]
    ck("S480: the letterhead and the title are one cell each; Continued and Page No as Marg's sheet has them; a heading is one cell",
       sl[0] == ["TEST MEDICOS", "", "", "", ""] and sl[1] == ["SALT WISE ITEM LIST", "", "", "", ""]
       and ["", "", "", "", "Continued..2"] in sl and ["", "", "", "Page", "No..2"] in sl
       and ["TESTSALT ONE + TWO", "", "", "", ""] in sl and ["OTHER SALT X", "", "", "", ""] in sl
       and ["1     TESTCILLIN 500", "1*10", 10.0, 0.0, 15.0] in sl, sl[:2])
    ck("S480: a category heading with its trailing figure and code is cut by column", ["TESTCAT", 0.0, "D98", "", ""] in R["CATEGORY_WISE_ITEM_LIST"])
    im = R["ITEM_MASTER"]
    ck("S480: the item list's two-line heads stay two rows, the columns the union of both lines'",
       ["S.No. DESCRIPTION", "PACKING", "Compnay", "", ""] in im and ["", "", "P.RATE", "S.RATE", "M.R.P."] in im
       and [1.0, "", "OTHER", "PRODUCTS", ""] in im and ["2     TESTCILLIN 500", "1*10", "TESTCO", "", ""] in im, im[3:5])
    lg = R["STOCK_ITEM_LEDGER_TEXT"]
    ck("S480: the register's first head row is its header; it closes on Received : / Issued : and prints no end mark",
       ["Bill No. /", "Type", "Patient Name", "Doctor Name", "Batch", "Quantity", "Value", "Balance"] in lg
       and ["Date", "", "", "", "No.", "", "", "Quantity"] in lg and lg[-1][4] == "Issued :" and END.encode() not in M["STOCK_ITEM_LEDGER_TEXT"],
       lg[-1])
    ck("S480: the short sale statement is SALE_SHORT, the statement with item detail stays SALE",
       kind(M["SALE_BILLWISE_SUMMARY1"]) == "SALE_SHORT" and kind(T) == "SALE"
       and R["SALE_BILLWISE_SUMMARY1"][-1][0] == "Total No. of" and R["SALE_BILLWISE_SUMMARY1"][-1][2] == 620.0)
    ck("S480: a report cut before its end -- Marg's end mark, or the register's closing pair -- is not recognised",
       kind(M["PURCHASE_BILLWISE"][:-30]) is None and kind(M["STOCK_ITEM_LEDGER_TEXT"][:-300]) is None)
    pe_ = M["PURCHASE_BILLWISE"]
    pe_ = pe_[:pe_.index(b"01-01-2030\r\n")] + pe_[pe_.index(b"-" * 80 + b"\r\nTOTAL"):].replace(b"1750.50", b"   0.00")
    try:
        spec_rows(pe_)
        ck("S480: an empty purchase statement is refused as EMPTY", False)
    except EmptyReport:
        ck("S480: an empty purchase statement is refused as EMPTY", kind(pe_) == "PURCHASE")
    # the no-sale day (D675 a, F-729)
    E_ = EMPTY_DAY_SAMPLE
    xe_, ie_ = convert(E_, exported_at=_dt.datetime(2030, 1, 3, 9, 0, 0))
    re_ = to_rows(E_, exported_at=_dt.date(2030, 1, 3))
    ck("S480: a zero-bill sale report of a past day is a NO-SALE DAY: title, heads, its one total row",
       ie_.get("empty") is True and ie_.get("as_on") == "02-01-2030" and ie_["kind"] == "SALE" and len(re_) == 3
       and re_[2] == ["Total No. of", "Bills: 0", "DAY TOTAL :", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] and re_[1] == HEAD
       and xe_ == convert(E_, exported_at="20300105-101500")[0], re_[2][:3])
    for when_, why_ in ((_dt.datetime(2030, 1, 2, 23, 59, 0), "the same day"), (_dt.date(2030, 1, 1), "a day before")):
        try:
            convert(E_, exported_at=when_)
            ck("S480: the same report exported on %s is refused in the staff's words" % why_, False)
        except TodayNotOver as ex_:
            ck("S480: the same report exported on %s is refused in the staff's words" % why_, str(ex_) == TODAY_WORDS)
    try:
        convert(E_)
        ck("S480: with no export time the zero-bill report is refused, never guessed", False)
    except TodayNotOver:
        ck("S480: with no export time the zero-bill report is refused, never guessed", False)
    except Refused:
        ck("S480: with no export time the zero-bill report is refused, never guessed", True)
    for bad_, why_ in ((E_.replace(b"Bills: 0", b"Bills: 1"), "a footer that says one bill"),
                       (E_.replace(b"DAY TOTAL :         0.00", b"DAY TOTAL :         5.00"), "a total that is not zero"),
                       (E_.replace(b"AS ON 02-01-2030", b"FROM 01-01-2030 TO 02-01-2030"), "a period, not a day")):
        try:
            convert(bad_, exported_at=_dt.date(2030, 1, 9))
            ck("S480: not an empty day -- %s" % why_, False)
        except TodayNotOver:
            ck("S480: not an empty day -- %s" % why_, False)
        except Refused as ex_:
            ck("S480: not an empty day -- %s" % why_, "GRAND TOTAL" in str(ex_))
    ck("S480: a sale with bills is read exactly as before whatever the export time",
       to_rows(T, exported_at=_dt.date(2030, 1, 9)) == to_rows(T) and "empty" not in convert(T)[1])


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
    _selftest_s480(ck)                                                   # S480: one check per spec, the three byte-equalities, the empty day
    if sample:
        raw = open(sample, "rb").read()
        xls, info = convert(raw, exported_at=os.path.getmtime(sample))
        ck("the sample converts (%d rows)" % info["rows"], len(xls) > 4096)
    print("SELFTEST " + ("OK" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest(sys.argv[2] if len(sys.argv) > 2 else None))
    if len(sys.argv) == 3:
        x, info = convert(open(sys.argv[1], "rb").read(), exported_at=os.path.getmtime(sys.argv[1]))
        open(sys.argv[2], "wb").write(x)
        print("wrote %s (%d rows, md5 %s)" % (sys.argv[2], info["rows"], hashlib.md5(x).hexdigest()))
        sys.exit(0)
    print(__doc__)
