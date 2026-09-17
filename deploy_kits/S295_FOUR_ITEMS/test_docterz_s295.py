#!/usr/bin/env python3
"""test_docterz_s295.py -- the no-sheet memory of docterz_ingest.py (S295), offline.
A workbook with a Day Revenue sheet is built from the parser's own expectations is NOT needed: the test
feeds one workbook WITHOUT the sheet and checks it is fetched once, remembered, skipped after, and read
again when its Drive mtime changes; a --dry-run never writes the memory; a genuine parse failure still
counts as failed. No real file, no network.
Usage: python3 test_docterz_s295.py <dir holding docterz_ingest.py + docterz_day.py>
"""
import io
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, sys.argv[1])
import openpyxl                                   # noqa: E402
import docterz_ingest as di                       # noqa: E402

N = [0]


def check(name, cond):
    N[0] += 1
    if not cond:
        print("FAIL %d: %s" % (N[0], name))
        sys.exit(1)


def book(sheet):
    wb = openpyxl.Workbook()
    wb.active.title = sheet
    b = io.BytesIO()
    wb.save(b)
    return b.getvalue()


tmp = tempfile.mkdtemp()
di.NOSHEET_FILE = os.path.join(tmp, "nosheet.json")
db = os.path.join(tmp, "f.db")
fetched = []
FILES = [["Staff_Action_Today_2026-06-11.xlsx", "idA", "2026-06-11T18:23:32.593Z"],
         ["Staff_Action_Today_2026-06-12.xlsx", "idB", "2026-06-12T18:00:00.000Z"]]
BYTES = {"idA": book("Follow-up"), "idB": b"not a workbook at all"}
di.list_day_files = lambda: [tuple(f) for f in FILES]
di.fetch_bytes = lambda fid: (fetched.append(fid), BYTES[fid])[1]
di.ingest_tenders = lambda con, dry: None


def run(*extra):
    sys.argv = ["docterz_ingest.py", "--db", db] + list(extra)
    del fetched[:]
    out = io.StringIO()
    old, sys.stdout = sys.stdout, out
    try:
        code = di.main()
    finally:
        sys.stdout = old
    return code, out.getvalue(), list(fetched)


code, out, f = run("--dry-run")
check("dry run: no-sheet reported, not failed", "NO SHEET" in out and "1 with no Day Revenue sheet" in out)
check("dry run: the corrupt one still fails", "failed 1" in out and code == 1)
check("dry run writes no memory", not os.path.exists(di.NOSHEET_FILE))
code, out, f = run()
check("live run remembers the no-sheet file", os.path.exists(di.NOSHEET_FILE) and "idA" in open(di.NOSHEET_FILE).read())
code, out, f = run()
check("next run does not fetch it again", "idA" not in f and "1 with no Day Revenue sheet" in out)
check("a genuine failure is still retried and counted", "idB" in f and "failed 1" in out)
FILES[0][2] = "2026-06-11T19:00:00.000Z"
code, out, f = run()
check("a changed Drive mtime is read again", "idA" in f)
code, out, f = run("--all")
check("--all ignores the memory", "idA" in f)
print("TEST OK -- %d checks (docterz_ingest no-sheet memory)" % N[0])
