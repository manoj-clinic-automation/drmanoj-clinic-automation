#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_daypdf_gate_s224.py -- THE LIVE-SHAPE WALK: the REAL patched finance_app.py, its REAL front
gate, the REAL S223 day page beside it, and this blueprint mounted by the REAL patch -- on a COPY
of finance.db with one invented day written into the copy.

    FIN_DIR=/root/finance /root/wa/venv/bin/python3 -B /root/finance/walk_daypdf_gate_s224.py
Offline: FIN_DIR=<a folder holding the patched finance_app.py and its modules> python3 -B walk_daypdf_gate_s224.py

It never touches the live database: the first thing it does is copy it. The invented day is
dated 2001-01-01 so it can never be mistaken for, or collide with, a real one.
"""
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

FIN_DIR = os.environ.get("FIN_DIR", "/root/finance")
SRC_DB = os.environ.get("FIN_DB", os.path.join(FIN_DIR, "finance.db"))
TMP = tempfile.mkdtemp(prefix="walk_s224pdf_")
DB = os.path.join(TMP, "finance.db")
if os.path.exists(SRC_DB):
    shutil.copyfile(SRC_DB, DB)
else:
    con = sqlite3.connect(DB)
    con.executescript(open(os.path.join(FIN_DIR, "finance_schema.sql"), encoding="utf-8").read())
    con.commit()
    con.close()
DAY = "2001-01-01"
con = sqlite3.connect(DB)
con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('clinic','zzwalkdoc','checker',1)")
con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('clinic','zzwalkdesk','maker',1)")
con.executescript("""
CREATE TABLE IF NOT EXISTS clinic_day_revenue (
  business_date TEXT PRIMARY KEY, source_file TEXT NOT NULL, source_id TEXT NOT NULL,
  source_mtime TEXT NOT NULL, taken_at TEXT NOT NULL,
  cons_count INTEGER NOT NULL, cons_amount_p INTEGER NOT NULL, xray_count INTEGER NOT NULL,
  xray_amount_p INTEGER NOT NULL, proc_count INTEGER NOT NULL, proc_amount_p INTEGER NOT NULL,
  total_count INTEGER NOT NULL, total_amount_p INTEGER NOT NULL, morning INTEGER, evening INTEGER,
  free_revisits INTEGER NOT NULL, free_concession INTEGER NOT NULL, f93_phantom_rows INTEGER NOT NULL,
  tender_json TEXT NOT NULL, sheet_total_p INTEGER, sheet_cash_p INTEGER, sheet_online_p INTEGER,
  variance_note TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS clinic_day_line (
  business_date TEXT NOT NULL, section TEXT NOT NULL, sn INTEGER NOT NULL,
  patient TEXT NOT NULL DEFAULT '', clinic_id TEXT NOT NULL DEFAULT '', amount_p INTEGER NOT NULL DEFAULT 0,
  mode TEXT NOT NULL DEFAULT '', shift TEXT NOT NULL DEFAULT '', PRIMARY KEY (business_date, section, sn));
""")
con.execute("INSERT OR REPLACE INTO clinic_day_revenue VALUES (?,?,?,?,?, ?,?, ?,?, ?,?, ?,?, ?,?, ?,?, ?, ?, ?,?,?, ?)",
            (DAY, "walk.xlsx", "walk", "x", "x", 2, 100000, 1, 30000, 0, 0, 3, 130000, 2, 1, 0, 0, 0,
             json.dumps({"Cash": 130000}), None, None, None, ""))
con.executemany("INSERT OR REPLACE INTO clinic_day_line VALUES (?,?,?,?,?,?,?,?)", [
    (DAY, "consult", 1, "Walk Test One", "W-001", 50000, "Cash", "morning"),
    (DAY, "consult", 2, "Walk Test Two", "W-002", 50000, "Cash", "morning"),
    (DAY, "xray", 1, "Walk Test One", "W-001", 30000, "Cash", "evening")])
con.commit()
con.close()
os.environ.update(FINANCE_DB=DB, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_MARG_TOKEN="walk-tok",
                  ASSETS_DB=os.path.join(TMP, "absent.db"))
sys.path.insert(0, FIN_DIR)
print("walking %s on a COPY of the db at %s" % (os.path.join(FIN_DIR, "finance_app.py"), DB))

PASSED, FAILED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label, ("   [%s]" % detail) if detail and not cond else ""))


import finance_app as FA                                    # noqa: E402
src = open(FA.__file__, encoding="utf-8").read()
ck("finance_app imported with the S224_DAY_REVENUE_PDF mount", "S224_DAY_REVENUE_PDF begin" in src)
ck("the S223 day page is mounted beside it (the neighbour the routes must not collide with)",
   "S223_CLINIC_DAY begin" in src)
c = FA.app.test_client()
DOC = {"X-Clinic-User": "zzwalkdoc", "X-Clinic-Role": "doctor"}
DESK = {"X-Clinic-User": "zzwalkdesk", "X-Clinic-Role": "staff"}
NOBODY = {"X-Clinic-User": "zzstranger", "X-Clinic-Role": "staff"}
P = "/finance/clinic/day/%s" % DAY

ck("share bookmark with nobody signed in -> 302 (the login redirect; curl's expected answer)",
   c.get("/finance/clinic/share").status_code == 302)
r = c.get("/finance/clinic/share", headers=DOC)
ck("share bookmark for the checker -> 302 to yesterday's share page",
   r.status_code == 302 and re.search(r"/finance/clinic/day/\d{4}-\d{2}-\d{2}/share$", r.headers["Location"]) is not None)
ck("PDF with nobody signed in -> 302, never the file", c.get(P + "/pdf").status_code == 302)
ck("PDF for a login with NO clinic role -> refused by the front gate",
   c.get(P + "/pdf", headers=NOBODY).status_code in (302, 403))
r = c.get(P + "/pdf", headers=DESK)
ck("PDF for the clinic MAKER -> 403 from require (checker only)", r.status_code == 403 and not r.data.startswith(b"%PDF"))
r = c.get(P + "/pdf", headers=DOC)
ck("PDF for the clinic checker -> 200 application/pdf", r.status_code == 200 and r.mimetype == "application/pdf")
ck("it is a PDF that names the invented day and its total",
   r.data.startswith(b"%PDF-1.4") and b"01-Jan-2001" in r.data and b"Rs 1,300" in r.data)
ck("the invented names are in the PDF, so the lines really came through the real db()",
   b"Walk Test One" in r.data and b"W-002" in r.data)
ck("?dl=1 -> attachment named Docterz_Revenue_<date>.pdf",
   c.get(P + "/pdf?dl=1", headers=DOC).headers.get("Content-Disposition") == 'attachment; filename="Docterz_Revenue_%s.pdf"' % DAY)
r2 = c.get(P + ".pdf", headers=DOC)
ck("/day/<date>.pdf reaches THIS module, not the S223 day page (no route collision)",
   r2.status_code == 200 and r2.mimetype == "application/pdf")
r3 = c.get(P, headers=DOC)
ck("/day/<date> still reaches the S223 A4 page, unchanged", r3.status_code == 200 and b"<!doctype html" in r3.data
   and b"PAID CONSULTATIONS" in r3.data)
ck("/day (the month) still answers", c.get("/finance/clinic/day?m=2001-01", headers=DOC).status_code == 200)
r = c.get(P + "/share", headers=DOC)
h = r.get_data(as_text=True)
ck("share page for the checker -> 200 with both buttons and navigator.share",
   r.status_code == 200 and "Share PDF on WhatsApp" in h and "Download PDF" in h and "navigator.share(" in h)
ck("share page names no patient (only the PDF carries them)", "Walk Test" not in h)
ck("share page for the maker -> 403 in words", c.get(P + "/share", headers=DESK).status_code == 403)
ck("the finance app's own healthz still answers", c.get("/finance/healthz").status_code == 200)
ck("the purchase healthz still answers (the neighbouring S224 mount)", c.get("/finance/purchase/api/healthz").status_code == 200)
print("\n%d PASS  %d FAIL" % (len(PASSED), len(FAILED)))
for f in FAILED:
    print("  FAILED: " + f)
sys.exit(1 if FAILED else 0)
