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

    python marg_txt.py report.txt out.XLS      convert one file
    python marg_txt.py --selftest               prove it
"""
import os, re, struct, sys, hashlib

VERSION = "S389.2"
TITLE = "BILL WISE SALES STATEMENT"
HEAD = ["BILL NO.", "DESCRIPTION", "D.R.", "GROSS AMT.", "DISCOUNT", "TAX", "DR/CR", "NET AMT.", "CASH"]
END = "*** End of Report ***"
RE_DATE = re.compile(r"^\d{2}-\d{2}-\d{4}$")
RE_BILL = re.compile(r"^(?:A|CN)\d+$")
RE_ITEM = re.compile(r"^\s{6,}\d+\s+\d+\s")
RE_NUM = re.compile(r"^-?\d+(?:\.\d+)?$")
MAX_BYTES = 5 * 1024 * 1024


class NotThisReport(Exception):
    """Not a report this reader knows -- left alone, not an error."""


class Refused(Exception):
    """It IS a bill-wise text report, but something in it is not where it must be."""


def recognise(raw):
    """True for a complete BILL WISE SALES STATEMENT text export with item detail (CASH column)."""
    if not raw or len(raw) > MAX_BYTES or raw[:4] in (b"\xd0\xcf\x11\xe0", b"PK\x03\x04", b"%PDF"):
        return False
    t = raw.decode("latin-1")
    head = t[:4000]
    return (TITLE in head and "BILL NO." in head and "CASH" in head
            and END in t[-400:])


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
    if not recognise(raw):
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
        if RE_ITEM.match(s):
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
    rows = to_rows(raw)
    return ole2(workbook_stream(rows)), {"rows": len(rows), "version": VERSION}


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
