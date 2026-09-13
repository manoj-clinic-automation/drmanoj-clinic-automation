#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_finance_daily_s243.py -- the REAL finance_app.py (its real front gate, real
require, real unit_role table) imported as gunicorn imports it, on a COPY of the
database, never the live one. Proves the S243 /finance/daily behaviour:

  anonymous            -> 302 to the portal login (unchanged)
  login with no role   -> 302 to the portal login (unchanged; the front gate)
  medical MAKER        -> 200, the Daily Sale form (unchanged)
  medical CHECKER      -> 302 to /finance/review   (S243: was 302 to the portal)
  /finance/review, /finance/, /finance/approvals still answer the checker as before

    FIN_DIR=/root/finance /root/wa/venv/bin/python3 -B walk_finance_daily_s243.py
Offline: FIN_DIR=<folder with finance_app.py + its modules> python3 -B walk_finance_daily_s243.py
Set FIN_DB to point at a database copy; without one, a fresh db is built from finance_schema.sql.
"""
import os
import shutil
import sqlite3
import sys
import tempfile

FIN_DIR = os.environ.get("FIN_DIR", "/root/finance")
SRC_DB = os.environ.get("FIN_DB", os.path.join(FIN_DIR, "finance.db"))
SCHEMA = os.environ.get("FIN_SCHEMA", os.path.join(FIN_DIR, "finance_schema.sql"))
UI_SRC = os.environ.get("FIN_UI", os.path.join(FIN_DIR, "finance_ui"))
TMP = tempfile.mkdtemp(prefix="walk_s243_fa_")
DB = os.path.join(TMP, "finance.db")
UI = os.path.join(TMP, "ui")
os.makedirs(UI)
if os.path.isdir(UI_SRC):
    for f in os.listdir(UI_SRC):
        if f.endswith(".html"):
            shutil.copyfile(os.path.join(UI_SRC, f), os.path.join(UI, f))
for f in ("finance_daily.html", "finance_review.html", "finance_approvals.html"):
    p = os.path.join(UI, f)
    if not os.path.exists(p):
        open(p, "w").write("<html><body>walk stub %s</body></html>" % f)
if os.path.exists(SRC_DB):
    shutil.copyfile(SRC_DB, DB)
else:
    con = sqlite3.connect(DB)
    con.executescript(open(SCHEMA, encoding="utf-8").read())
    con.commit()
    con.close()
con = sqlite3.connect(DB)
con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('medical','zzwalkmaker','maker',1)")
con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('medical','zzwalkdoc','checker',1)")
con.commit()
con.close()
os.environ.update(FINANCE_DB=DB, FINANCE_UI_DIR=UI, FINANCE_ALLOW_HEADER_AUTH="1",
                  FINANCE_PORTAL_LOGIN="/portal", FINANCE_SCAN_DIR=os.path.join(TMP, "scans"))
sys.path.insert(0, FIN_DIR)
print("walking %s on a COPY of the db at %s" % (os.path.join(FIN_DIR, "finance_app.py"), DB))
PASSED, FAILED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label, ("   [%s]" % detail) if detail and not cond else ""))


import finance_app as FA                                    # noqa: E402
src = open(FA.__file__, encoding="utf-8").read()
patched = "S243: a checker (the doctor) lands on his Review console" in src
print("  file carries the S243 mark: %s" % patched)
c = FA.app.test_client()
DOC = {"X-Clinic-User": "zzwalkdoc", "X-Clinic-Role": "doctor"}
MAK = {"X-Clinic-User": "zzwalkmaker", "X-Clinic-Role": "staff"}
STR = {"X-Clinic-User": "zzstranger", "X-Clinic-Role": "staff"}
r = c.get("/finance/daily")
ck("anonymous /finance/daily -> 302 to the portal", r.status_code == 302 and r.headers.get("Location", "").endswith("/portal"),
   "%s %s" % (r.status_code, r.headers.get("Location")))
r = c.get("/finance/daily", headers=STR)
ck("login with NO medical role -> 302 to the portal (front gate, unchanged)",
   r.status_code == 302 and r.headers.get("Location", "").endswith("/portal"), "%s %s" % (r.status_code, r.headers.get("Location")))
r = c.get("/finance/daily", headers=MAK)
ck("medical MAKER -> 200, the Daily Sale form", r.status_code == 200, str(r.status_code))
r = c.get("/finance/daily", headers=DOC)
if patched:
    ck("medical CHECKER -> 302 to /finance/review (S243)",
       r.status_code == 302 and r.headers.get("Location", "").endswith("/finance/review"), "%s %s" % (r.status_code, r.headers.get("Location")))
else:
    ck("UNPATCHED: medical CHECKER -> 302 to the portal (the symptom)",
       r.status_code == 302 and r.headers.get("Location", "").endswith("/portal"), "%s %s" % (r.status_code, r.headers.get("Location")))
ck("checker: /finance/review -> 200", c.get("/finance/review", headers=DOC).status_code == 200)
ck("checker: /finance/approvals -> 200", c.get("/finance/approvals", headers=DOC).status_code == 200)
ck("checker: /finance/ answers (200 or a redirect within /finance)",
   c.get("/finance/", headers=DOC).status_code in (200, 302))
ck("maker: /finance/approvals still refused (302 to the portal) -- no gate widened",
   c.get("/finance/approvals", headers=MAK).status_code == 302)
print("RESULT: %d passed, %d failed" % (len(PASSED), len(FAILED)))
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAILED else 0)
