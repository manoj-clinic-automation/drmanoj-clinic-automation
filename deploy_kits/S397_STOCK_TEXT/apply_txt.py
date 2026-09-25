p = "w/marg_txt.py"
s = open(p, encoding="ascii").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)

rep('VERSION = "S389.2"', 'VERSION = "S397"')

rep('''    python marg_txt.py report.txt out.XLS      convert one file
''', '''THE CLOSING STOCK TOO (S397, 25-Sep-2026, owner's GO)
  "WHOLE STORES CLOSING STOCK AS ON dd-mm-yyyy" (serial | medicine and packing | stock | unit, ended by
  "*** End of Report ***") becomes the four-column sheet Marg's Excel export of it is: the letterhead, the
  title, the column heads, every item, the page furniture, and the TOTAL row. Stock stays as Marg prints
  it ("3:2" = 3 strips and 2 loose, "-" = none); a plain whole number is a number, as in Marg's sheet.
  Marg's TOTAL counts every item in single units (strips x packing + loose); the reader adds every line
  the same way and refuses the file unless the two agree -- a report cut short cannot pass.
  Only the WHOLE STORES report is read; a store- or category-filtered print is left alone.

    python marg_txt.py report.txt out.XLS      convert one file
''')

rep('''def recognise(raw):
    """True for a complete BILL WISE SALES STATEMENT text export with item detail (CASH column)."""
    if not raw or len(raw) > MAX_BYTES or raw[:4] in (b"\\xd0\\xcf\\x11\\xe0", b"PK\\x03\\x04", b"%PDF"):
        return False
    t = raw.decode("latin-1")
    head = t[:4000]
    return (TITLE in head and "BILL NO." in head and "CASH" in head
            and END in t[-400:])
''', '''def recognise(raw):
    """True for a complete text export this reader knows: the BILL WISE SALES STATEMENT with item
    detail (CASH column), or (S397) the WHOLE STORES CLOSING STOCK."""
    return kind(raw) is not None


def kind(raw):
    """"SALE", "STOCK" or None."""
    if not raw or len(raw) > MAX_BYTES or raw[:4] in (b"\\xd0\\xcf\\x11\\xe0", b"PK\\x03\\x04", b"%PDF"):
        return None
    t = raw.decode("latin-1")
    head = t[:4000]
    if END not in t[-400:]:
        return None
    if TITLE in head and "BILL NO." in head and "CASH" in head:
        return "SALE"
    if RE_STOCK_TITLE.search(head) and RE_STOCK_HEAD.search(head):
        return "STOCK"
    return None


# ------------------------------------------------------------------------ closing stock (S397)
RE_STOCK_TITLE = re.compile(r"^\\s*WHOLE STORES CLOSING STOCK AS ON (\\d{2}-\\d{2}-\\d{4})\\s*$", re.M)
RE_STOCK_HEAD = re.compile(r"^S\\.No\\.\\s+Description\\s+Total Stock\\s+Unit\\s*$", re.M)
STOCK_HEAD = ["S.No.", "Description", "Total Stock", "Unit"]
RE_SNO = re.compile(r"^\\s*(\\d+)  ")
RE_QTY = re.compile(r"^(?:-|-?\\d+(?::\\d+)?)$")
RE_CONT = re.compile(r"^Continued\\.\\.(\\d+)$")
RE_PAGE = re.compile(r"^Page No\\.\\.(\\d+)$")


def _stock_units(q, desc):
    """Marg's own count: 'a:b' = a strips of the packing plus b loose; '-' = none; else a number."""
    if q == "-":
        return 0
    m = re.match(r"^(-?)(\\d+):(\\d+)$", q)
    if not m:
        return int(q)
    toks = desc.split()
    pm = re.match(r"^(\\d+)\\*(\\d+)$", (toks[-1] if len(toks) >= 2 else "").rstrip("."))
    pack = int(pm.group(1)) * int(pm.group(2)) if pm else 1
    n = int(m.group(2)) * pack + int(m.group(3))
    return -n if m.group(1) else n


def stock_rows(raw):
    """The four-column closing-stock sheet, as Marg's Excel export lays it out."""
    if kind(raw) != "STOCK":
        raise NotThisReport("not a complete whole-stores closing stock text export")
    lines = raw.decode("latin-1").replace("\\r\\n", "\\n").replace("\\r", "\\n").split("\\n")
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
            if len(s) < q_end or s[q_end:p_unit].strip() or s[q_start - 1] not in " -" and s[q_start - 1:q_start].strip():
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
            if not re.match(r"^-?\\d+$", v):
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
''')

rep('''def to_rows(raw):
    """The nine-column sheet, as a list of rows of cells (str, or float for a number)."""
    if not recognise(raw):''', '''def to_rows(raw):
    """The nine-column sheet, as a list of rows of cells (str, or float for a number)."""
    if kind(raw) != "SALE":''')

rep('''def convert(raw):
    """(xls_bytes, info) for a text export; raises NotThisReport / Refused."""
    rows = to_rows(raw)
    return ole2(workbook_stream(rows)), {"rows": len(rows), "version": VERSION}''',
'''def convert(raw):
    """(xls_bytes, info) for a text export; raises NotThisReport / Refused."""
    k = kind(raw)
    rows = stock_rows(raw) if k == "STOCK" else to_rows(raw)
    return ole2(workbook_stream(rows)), {"rows": len(rows), "version": VERSION, "kind": k or "SALE"}''')

# selftest: a small made-up stock sample (no real names or numbers)
rep('''def selftest(sample=None):''', '''STOCK_SAMPLE = ("\\r\\n" + " " * 31 + "TEST SHOP\\r\\n" + " " * 24 + "TEST STREET\\r\\n"
     + " " * 16 + "GSTIN : TESTGST  TIN No. : TESTTIN\\r\\n\\r\\n"
     + " " * 19 + "WHOLE STORES CLOSING STOCK AS ON 24-09-2026\\r\\n" + "-" * 80 + "\\r\\n"
     "S.No.  Description" + " " * 45 + "Total Stock  Unit\\r\\n" + "-" * 80 + "\\r\\n"
     "    1" + " " * 68 + "-  PCS\\r\\n"
     "    2  TEST TAB 500                  1*10" + " " * 30 + "3:2  STRI\\r\\n"
     "    3  TEST CAST 5                   1*1" + " " * 30 + "-14  ITEM\\r\\n"
     + "-" * 80 + "\\r\\n" + " " * 66 + "Continued..2\\r\\n\\r\\n\\r\\n\\r\\n\\r\\n"
     "TEST SHOP\\r\\n" + " " * 68 + "Page No..2\\r\\nWHOLE STORES CLOSING STOCK AS ON 24-09-2026\\r\\n"
     + "-" * 80 + "\\r\\nS.No.  Description" + " " * 45 + "Total Stock  Unit\\r\\n" + "-" * 80 + "\\r\\n"
     "    4  TEST GEL                      30GM" + " " * 31 + "6  TUBE\\r\\n"
     "    5  TEST WRIST SPLINT LF L ELAST 1*1" + " " * 30 + "-1:3\\r\\n"
     + "-" * 80 + "\\r\\nTOTAL" + " " * 68 + "13\\r\\n" + "-" * 80 + "\\r\\n*** End of Report ***\\r\\n\\r\\n").encode()


def selftest(sample=None):''')

rep('''    if sample:
        raw = open(sample, "rb").read()''', '''    # S397: the closing stock
    S_ = STOCK_SAMPLE
    ck("a complete closing-stock text export is recognised as STOCK; the sale stays SALE",
       kind(S_) == "STOCK" and kind(T) == "SALE" and not recognise(S_[:-30]))
    sr = stock_rows(S_)
    its = [r for r in sr if isinstance(r[0], float)]
    ck("five items, serials 1..5, the TOTAL carried", [r[0] for r in its] == [1.0, 2.0, 3.0, 4.0, 5.0]
       and ["TOTAL", "", 13.0, ""] in sr)
    ck("stock as Marg's sheet has it: '3:2' and '-14' as printed, a plain 6 a number, a missing unit empty",
       its[1][2] == "       3:2" and its[2][2] == "       -14" and its[3][2] == 6.0 and its[4][3] == ""
       and its[0][1] == "" and its[0][2] == "         -", [its[1][2], its[2][2], its[3][2]])
    ck("the page break as Marg's sheet has it", ["", "", "", "Continued..2"] in sr
       and ["", "", "    Page", "No..2"] in sr and sr.count(["", "", "", ""]) == 5)
    ck("a 29-letter name keeps its packing; the GSTIN line is closed up",
       its[4][1] == "TEST WRIST SPLINT LF L ELAST 1*1" and ["GSTIN : TESTGST TIN No. : TESTTIN", "", "", ""] in sr)
    for bad, why in ((S_.replace(b"TOTAL" + b" " * 68 + b"13", b"TOTAL" + b" " * 68 + b"14"), "a TOTAL that does not add up"),
                     (S_.replace(b"    4  TEST GEL", b"    6  TEST GEL"), "a serial out of order"),
                     (S_.replace(b"3:2  STRI", b"3:2 STRI "), "a stock off its column")):
        try:
            stock_rows(bad); ck("refused: " + why, False)
        except Refused:
            ck("refused: " + why, True)
    xs, info = convert(S_)
    ck("the stock .XLS is the same bytes every time", xs == convert(S_)[0] and info["kind"] == "STOCK")
    if sample:
        raw = open(sample, "rb").read()''')
open(p, "w", encoding="ascii", newline="\n").write(s)
print("applied")
