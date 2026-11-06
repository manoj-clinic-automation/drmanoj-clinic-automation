#!/usr/bin/env python3
"""make_s734.py -- kit S734_PACKS_HEAD_STOP (session 394, the parent, 06-Nov-2026) . F-1148

Builds the new /root/finance/packs.py from the LIVE bytes (fb987b27, S729) by counted edits:
each anchor must occur exactly once, or nothing is written.

    python make_s734.py <live packs.py> <out file> [--expect <md5 of the result>]

WHAT CHANGES -- only where a statement's HEAD ends (packs._header):
  the head also stops at a transaction row that begins with a serial number and a date
  ('1 01/07/2026 ... 50000.00', ICICI), with a d-Mon-yyyy date ('1 Jul 2026 ... 5000.00',
  SBI) or with a dd/mm/yy date (HDFC) -- only when the line ENDS with an amount, carries a
  word besides month names and is not a 'from .. to ..' line.
  Before this, up to 40 lines of such rows counted as the head, and the holder words and
  'the bank by its head' could come from a narration.
"""
import hashlib
import sys

EDITS = [
    ('''def _header(text, n=40):
    """The statement's head: the non-empty lines BEFORE the first transaction row (a dated row, a B/F row or a pipe row) -- where the
    bank, the holder, the account and the period are printed; a narration never reaches it."""
    out = []
    for ln in (text or "").splitlines():
        if not ln.strip():
            continue
        if re.match(r"^\\s*\\d{2}[-\u2013/]\\d{2}[-\u2013/]\\d{4}\\s", ln) or re.search(r"\\bB/F\\b", ln) or re.match(r"^\\s*[Xx*\\d]{6,}\\|", ln):
            break
''',
     '''# S734 (F-1148): three more kinds of transaction row end the head -- a serial number then a date (ICICI: '1 01/07/2026 ...'),
# a d-Mon-yyyy date (SBI: '1 Jul 2026 ...') and a dd/mm/yy date (HDFC) -- each only when the line looks like a row: it ENDS with an
# amount (n.nn, Cr/Dr allowed), it carries a word of three letters or more besides month names, and it is not a 'from .. to ..'
# period line. A period line, a printed time, an address or a summary of dates and figures never ends the head.
_HEAD_STOP_SERIAL = re.compile(r"^\\s*\\d{1,4}\\s+\\d{1,2}[-\u2013/.]\\d{1,2}[-\u2013/.]\\d{2,4}\\s")
_HEAD_STOP_DMON = re.compile(r"(?i)^\\s*\\d{1,2}[\\s\\-/.](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\\s\\-/.,]+\\d{4}\\s")
_HEAD_STOP_DMY2 = re.compile(r"^\\s*\\d{2}[-/]\\d{2}[-/]\\d{2}\\s")
_HEAD_AMT_END = re.compile(r"(?i)\\d[\\d,]*\\.\\d{2}\\s*(?:Cr|Dr)?\\.?\\s*$")
_HEAD_MONTHS = re.compile(r"(?i)\\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\\b")


def _head_stop_row(ln):
    \"\"\"S734 (F-1148): True when the line is a transaction row of the ICICI, SBI or HDFC shape.\"\"\"
    if not (_HEAD_STOP_SERIAL.match(ln) or _HEAD_STOP_DMON.match(ln) or _HEAD_STOP_DMY2.match(ln)):
        return False
    if " to " in ln.lower() or not _HEAD_AMT_END.search(ln):
        return False
    return bool(re.search(r"[A-Za-z]{3,}", _HEAD_MONTHS.sub(" ", ln)))


def _header(text, n=40):
    """The statement's head: the non-empty lines BEFORE the first transaction row (a dated row, a B/F row or a pipe row) -- where the
    bank, the holder, the account and the period are printed; a narration never reaches it."""
    out = []
    for ln in (text or "").splitlines():
        if not ln.strip():
            continue
        if re.match(r"^\\s*\\d{2}[-\u2013/]\\d{2}[-\u2013/]\\d{4}\\s", ln) or re.search(r"\\bB/F\\b", ln) or re.match(r"^\\s*[Xx*\\d]{6,}\\|", ln):
            break
        if _head_stop_row(ln):                                                 # S734 (F-1148)
            break
'''),
]

FROM = "fb987b271f9b99dec2c696590501b19d"


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    src, dst = argv[1], argv[2]
    expect = argv[argv.index("--expect") + 1] if "--expect" in argv else None
    raw = open(src, "rb").read()
    if hashlib.md5(raw).hexdigest() != FROM:
        print("REFUSED: the input is not packs.py %s" % FROM[:8])
        return 1
    text = raw.decode("utf-8")
    for i, (old, new) in enumerate(EDITS, 1):
        n = text.count(old)
        if n != 1:
            print("REFUSED: edit %d's anchor occurs %d times (must be once)" % (i, n))
            return 1
        text = text.replace(old, new, 1)
    out = text.encode("utf-8")
    got = hashlib.md5(out).hexdigest()
    if expect and not got.startswith(expect):
        print("REFUSED: the result is %s, expected %s" % (got, expect))
        return 1
    open(dst, "wb").write(out)
    print("BUILT %s (%d counted edit) md5 %s" % (dst, len(EDITS), got))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
