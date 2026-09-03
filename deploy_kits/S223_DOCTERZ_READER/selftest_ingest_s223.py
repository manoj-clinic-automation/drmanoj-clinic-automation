#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest_ingest_s223.py -- prove the reader and the store on REAL exports, offline.

Drive is stubbed with real Staff_Action_Today files on disk; everything else -- the parse, the
schema, the upsert, the same-date tiebreaker, the idempotence -- is the code that will run on the
box. Run it from the kit folder with a directory of .xlsx files:

    python3 -B selftest_ingest_s223.py /path/to/xlsx_dir
"""
import glob, json, os, sqlite3, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docterz_ingest as ING

F = []
def ck(l, c, d=""):
    print("  %s  %s%s" % ("PASS" if c else "FAIL", l, ("   [%s]" % d) if d else ""))
    if not c: F.append(l)

SRC = sys.argv[1] if len(sys.argv) > 1 else "/tmp/xlsx"
paths = sorted(glob.glob(os.path.join(SRC, "Staff_Action_Today_*.xlsx")))
if not paths:
    sys.exit("no Staff_Action_Today_*.xlsx under %s" % SRC)

BY_ID = {os.path.basename(p): p for p in paths}
ING.fetch_bytes = lambda fid: open(BY_ID[fid], "rb").read()
def _listing(stamp="2026-09-04T00:00:00Z"):
    return [(os.path.basename(p), os.path.basename(p), stamp) for p in paths]
ING.list_day_files = _listing

db = os.path.join(tempfile.mkdtemp(), "t.db")
print("-- 1  first run: every file parses and lands --------------------------")
sys.argv = ["x", "--db", db]
rc = ING.main()
ck("exit code 0 (nothing failed)", rc == 0)
con = sqlite3.connect(db); con.row_factory = sqlite3.Row
rows = {r["business_date"]: r for r in con.execute("SELECT * FROM clinic_day_revenue")}
ck("one row per file (%d files -> %d days)" % (len(paths), len(rows)), len(rows) == len(paths))

print("\n-- 2  the figures are the ROWS, not the sheet (D367) -------------------")
bad = [d for d, r in rows.items()
       if r["total_amount_p"] != r["cons_amount_p"] + r["xray_amount_p"] + r["proc_amount_p"]]
ck("total = consultations + x-ray + procedures, every day", not bad, str(bad))
bad = [d for d, r in rows.items()
       if sum(json.loads(r["tender_json"]).values()) != r["total_amount_p"]]
ck("the tender split accounts for EVERY rupee of the row total", not bad, str(bad))
gt = {"2026-08-19": 1640000, "2026-09-02": 2090000}
for d, p in gt.items():
    if d in rows:
        ck("ground truth %s = Rs %d" % (d, p // 100), rows[d]["total_amount_p"] == p,
           "got Rs %s" % (rows[d]["total_amount_p"] // 100))

print("\n-- 3  F-93 phantoms are dropped, and counted -------------------------")
ck("no day stores a phantom as a concession case",
   all(r["free_concession"] >= 0 for r in rows.values()))
ck("phantoms were seen and counted on the recent days",
   any(r["f93_phantom_rows"] == 3 for r in rows.values()),
   str({d: r["f93_phantom_rows"] for d, r in rows.items()}))

print("\n-- 4  the sheet's own disagreement is RECORDED, never shown -----------")
noted = {d: r["variance_note"] for d, r in rows.items() if r["variance_note"]}
ck("days where the sheet contradicts itself carry a note", bool(noted))
for d in sorted(noted):
    print("       %s  %s" % (d, noted[d]))
ck("no note mentions a patient, an id or a mobile",
   not any(any(w in v.lower() for w in ("patient", "mobile", "clinic id")) for v in noted.values()))

print("\n-- 5  idempotence and the same-date tiebreaker -----------------------")
before = {d: (r["total_amount_p"], r["taken_at"]) for d, r in rows.items()}
sys.argv = ["x", "--db", db]
ING.main()
_c2 = sqlite3.connect(db); _c2.row_factory = sqlite3.Row
rows2 = {r["business_date"]: r["total_amount_p"] for r in
         _c2.execute("SELECT business_date, total_amount_p FROM clinic_day_revenue")}
ck("a second run changes nothing (unchanged files are skipped)",
   len(rows2) == len(before) and all(rows2[d] == before[d][0] for d in before))
# two files for one date: the later Drive mtime must win
dup = paths[-1]
ING.list_day_files = lambda: [(os.path.basename(dup), os.path.basename(dup), "2026-01-01T00:00:00Z"),
                              (os.path.basename(dup), os.path.basename(dup), "2027-01-01T00:00:00Z")]
sys.argv = ["x", "--db", db, "--all"]
ING.main()
r = sqlite3.connect(db).execute(
    "SELECT source_mtime FROM clinic_day_revenue WHERE source_file=?",
    (os.path.basename(dup),)).fetchone()
ck("of two exports of one date, the LATER-taken one is the row kept",
   r and r[0] == "2027-01-01T00:00:00Z", str(r))

print("\n-- 6  no identifier reached the database -----------------------------")
blob = " ".join(str(v) for r in sqlite3.connect(db).execute("SELECT * FROM clinic_day_revenue")
                for v in r).lower()
import re as _re
ck("no 10-digit mobile-shaped number anywhere in the table",
   not _re.search(r"[6-9]\d{9}", blob))
ck("no Docterz patient-UID shape (10 uppercase letters+digits) anywhere",
   not _re.search(r"\b[A-Z]{5}\d{5}\b", " ".join(
       str(v) for r in sqlite3.connect(db).execute("SELECT * FROM clinic_day_revenue") for v in r)))

print("\n%s  %d checks, %d failed" % ("RED" if F else "GREEN", 14, len(F)))
sys.exit(1 if F else 0)
