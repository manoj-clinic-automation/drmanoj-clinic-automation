#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phi_scan.py -- S274 / kit S336_QUARANTINE (Sanjeevni).  "May these bytes rest on this box?"

THE RULE IT SERVES (S186, Book s2.5): no raw Marg export with a patient's number at rest on the server.
The door (marg_take.py) used to delete every refused or unrecognised file for that reason alone --
"contents not established, so treated as patient data".  D567 item 3 asks that refused files be KEPT
in quarantine so a later signature can rescue them without anyone re-exporting.  This module is the
one test that decides which of the two rules wins for a given file:

    clean(path) -> (True, "")            the bytes carry no person's detail: they may be kept
                -> (False, why)          they may not; the door deletes them as before

WHAT COUNTS AS A PERSON'S DETAIL (conservative on purpose -- a wrong "clean" is the failure that matters):
  * any 10-digit run starting 6-9 anywhere in the sheet, in text OR in a numeric cell (a mobile) --
    EXCEPT the two lines that are the report's own furniture and carry the SHOP's or MARG's number, never a
    person's: the shop header line beginning "Phone :" (rows 1-8 of every Marg export) and Marg's
    advertisement footer, a line naming MARG in the last 3 rows ("MARG ERP NANO for Chemist ... Call",
    "Digital Purchase | ERP Ordering | ... | Call MARG ...").  Measured 20-Sep on the whole real archive
    (159 exports): every kept type carries exactly those two lines and nothing else -- see the kit README;
  * any sale-family word in the report's preamble (the first 25 rows): SALE, SALES, PATIENT, MOBILE,
    LEDGER, PRESCRIB, DOCTOR, CUSTOMER, ADDRESS -- the families whose rows name people (PARTY is
    Marg's word for a SUPPLIER on every purchase report, so it is not one of them) (the shop's own
    "Phone :" line is furniture, above);
  * a PDF (whatever was printed, by rule DOCUMENT_PDF is never kept);
  * a sheet that cannot be opened, or is empty (nothing established).

It reads with the router's own opener (marg_router.open_sheet: xlrd for .xls, the stdlib reader for
.xlsx) so it sees exactly the cells the router saw.  It writes nothing.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

MOBILE_RE = re.compile(r"(?<![0-9])[6-9][0-9]{9}(?![0-9])")
PERSON_WORDS = re.compile(r"\b(SALE|SALES|PATIENT|PATIENTS|MOBILE|LEDGER|PRESCRIB\w*|DOCTOR|CUSTOMER|ADDRESS)\b", re.I)
PREAMBLE_ROWS = 25
SHOP_LINE_RE = re.compile(r"^\s*PHONE\s*:", re.I)          # the shop's own header line (rows 1-8)
AD_LINE_RE = re.compile(r"\bMARG\b", re.I)                 # Marg's advertisement footer names Marg ...
AD_LINE_ROWS = 3                                            # ... and sits in the last rows of the sheet
SHOP_LINE_ROWS = 8


def _text(v):
    """A cell as the router would print it; an integral float as its integer digits."""
    if v is None:
        return ""
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return repr(v)
    return str(v)


def clean(path):
    """-> (ok, why).  ok is True only when every test above passed."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return False, "a PDF is never kept (DOCUMENT_PDF rule)"
    if ext not in (".xls", ".xlsx"):
        return False, "not a spreadsheet"
    try:
        import marg_router as R                                  # noqa: PLC0415
        sh = R.open_sheet(path)
    except Exception as e:                                       # noqa: BLE001
        return False, "the sheet could not be opened (%s)" % str(e)[:80]
    try:
        nrows, ncols = int(sh.nrows), int(sh.ncols)
    except Exception:                                            # noqa: BLE001
        return False, "the sheet has no shape"
    if nrows == 0 or ncols == 0:
        return False, "the sheet is empty"
    cells = 0
    preamble = []
    for r in range(nrows):
        for c in range(ncols):
            try:
                t = _text(sh.cell_value(r, c)).strip()
            except Exception:                                    # noqa: BLE001
                return False, "a cell could not be read at row %d" % (r + 1)
            if not t:
                continue
            cells += 1
            if MOBILE_RE.search(t.replace(" ", "")):
                if (r < SHOP_LINE_ROWS and SHOP_LINE_RE.match(t)) or (r >= nrows - AD_LINE_ROWS and AD_LINE_RE.search(t)):
                    continue                                     # the shop's or Marg's own number, not a person's
                return False, "a mobile-shaped number at row %d" % (r + 1)
            if r < PREAMBLE_ROWS:
                preamble.append(t)
    if cells == 0:
        return False, "the sheet has no filled cell"
    m = PERSON_WORDS.search(" ".join(preamble))
    if m:
        return False, "the report's preamble names people (%s)" % m.group(1).upper()
    return True, ""


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 2
    rc = 0
    for p in argv:
        ok, why = clean(p)
        print("%-6s %s%s" % ("CLEAN" if ok else "PHI", os.path.basename(p), ("  -- " + why) if why else ""))
        rc = rc or (0 if ok else 1)
    return rc


if __name__ == "__main__":
    sys.exit(main())
