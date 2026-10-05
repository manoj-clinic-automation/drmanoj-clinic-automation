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


