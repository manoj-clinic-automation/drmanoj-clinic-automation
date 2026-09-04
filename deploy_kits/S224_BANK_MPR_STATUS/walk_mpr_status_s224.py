#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_mpr_status_s224.py -- THE LIVE-SHAPE WALK: the REAL patched finance_app.py, its REAL front
gate, and bank_mpr_status mounted by the REAL patch -- on a COPY of finance.db.

Why: S208's push was refused by the front gate for weeks while every unit test was green (F-286);
S209 found a page that killed a console behind four green gates. This walk supplies nothing of
its own: it imports finance_app from FIN_DIR exactly as gunicorn does and knocks on the doors.

On the box (after the patch, BEFORE the restart if you like -- it touches no live file):
    FIN_DIR=/root/finance /root/wa/venv/bin/python3 -B /root/finance/walk_mpr_status_s224.py
Offline: FIN_DIR=<folder holding the patched finance_app.py and its modules> python3 -B walk_mpr_status_s224.py

It never touches the live database: the first thing it does is copy it.  It never touches the
live statement store: FINANCE_UPI_DIR is pointed at a temp folder.
"""
import datetime as dt
import os
import shutil
import sqlite3
import sys
import tempfile

FIN_DIR = os.environ.get("FIN_DIR", "/root/finance")
SRC_DB = os.environ.get("FIN_DB", os.path.join(FIN_DIR, "finance.db"))
TMP = tempfile.mkdtemp(prefix="walk_mpr_s224_")
DB = os.path.join(TMP, "finance.db")
STORE = os.path.join(TMP, "upi_statements")
os.makedirs(STORE)
if os.path.exists(SRC_DB):
    shutil.copyfile(SRC_DB, DB)
else:
    con = sqlite3.connect(DB)
    con.executescript(open(os.path.join(FIN_DIR, "finance_schema.sql"), encoding="utf-8").read())
    con.execute("INSERT OR IGNORE INTO business_unit (code, name) VALUES ('medical','Sanjeevni Medicos')")
    con.execute("INSERT OR IGNORE INTO business_unit (code, name) VALUES ('clinic','Clinic')")
    con.commit()
    con.close()
con = sqlite3.connect(DB)
con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('clinic','zzwalkdoc','checker',1)")
con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('medical','zzwalkpharm','checker',1)")
# a synthetic APPLIED day on the copy only (no real merchant id)
con.execute("CREATE TABLE IF NOT EXISTS upi_statement (id INTEGER PRIMARY KEY, merchant_id TEXT NOT NULL, "
            "unit TEXT, statement_date TEXT NOT NULL, source_msg_id TEXT, filename TEXT, sha256 TEXT, "
            "parsed_total_p INTEGER, txn_count INTEGER, ingested_at TEXT, UNIQUE (merchant_id, statement_date))")
con.execute("INSERT OR REPLACE INTO upi_statement (merchant_id, unit, statement_date, filename, parsed_total_p, "
            "txn_count, ingested_at) VALUES ('999999999999999','clinic','2001-01-01','walk.xlsx',100000,2,"
            "'2001-01-02T09:00:00')")
con.commit()
con.close()
os.environ.update(FINANCE_DB=DB, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_UPI_DIR=STORE,
                  ASSETS_DB=os.path.join(TMP, "absent.db"))
sys.path.insert(0, FIN_DIR)
print("walking %s on a COPY of the db at %s" % (os.path.join(FIN_DIR, "finance_app.py"), DB))

PASSED, FAILED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label, ("   [%s]" % detail) if detail and not cond else ""))


import finance_app as FA                                    # noqa: E402
src = open(FA.__file__, encoding="utf-8").read()
ck("finance_app imported with the S224 MPR mount (no import-time db call, F-303)",
   "S224_BANK_MPR_STATUS begin" in src)
ck("the mount sits AFTER the S224_MARG_PURCHASES end marker (chained, not interleaved)",
   src.index("S224_MARG_PURCHASES end") < src.index("S224_BANK_MPR_STATUS begin"))
import bank_mpr_status as M                                 # noqa: E402
ck("the mounted module knows the app's UPI_DIR", M._upi_dir == FA.UPI_DIR and FA.UPI_DIR == STORE)
ck("the mounted module is on the clinic unit", M._unit == FA.CLINIC_UNIT == "clinic")

c = FA.app.test_client()
DOC = {"X-Clinic-User": "zzwalkdoc", "X-Clinic-Role": "doctor"}
PH = {"X-Clinic-User": "zzwalkpharm", "X-Clinic-Role": "doctor"}
yday = (dt.date.today() - dt.timedelta(days=1)).isoformat()

rv = c.get("/finance/clinic/bank/mpr/" + yday)
ck("anonymous -> not 200 through the REAL gate (login redirect or 401/403)", rv.status_code in (301, 302, 401, 403),
   str(rv.status_code))
rv = c.get("/finance/clinic/bank/mpr/" + yday, headers=DOC)
ck("clinic checker -> 200 html line for yesterday", rv.status_code == 200 and b"Bank MPR for" in rv.data,
   "%s %s" % (rv.status_code, rv.data[:120]))
ck("yesterday's line names one of the states in English",
   any(w in rv.data for w in (b"APPLIED", b"LATE", b"WAITING", b"NOT RECEIVED", b"RECEIVED")))
rv = c.get("/finance/clinic/bank/mpr/" + yday + ".json", headers=DOC)
ck("json for yesterday", rv.status_code == 200 and rv.get_json()["date"] == yday
   and rv.get_json()["expected_by"].endswith("T12:20:00"))
rv = c.get("/finance/clinic/bank/mpr/2001-01-01?json=1", headers=DOC)
ck("the seeded APPLIED day reads applied through the real app db()", rv.get_json()["state"] == "applied"
   and rv.get_json()["rows"] == 2, str(rv.get_json()))
rv = c.get("/finance/clinic/bank/mpr/2026-09-03?json=1", headers=DOC)
ck("03-Sep answers from the store (never a 500)", rv.status_code == 200 and rv.get_json()["ok"], str(rv.status_code))
print("      03-Sep on this copy: %s" % rv.get_json()["line"])
rv = c.get("/finance/clinic/bank/mpr?days=8", headers=DOC)
ck("the 8-day page renders", rv.status_code == 200 and rv.data.count(b'class="mpr-status"') == 8)
ck("the 8-day page has no <script>", b"<script" not in rv.data)
rv = c.get("/finance/clinic/bank/mpr/" + yday, headers=PH)
ck("a medical-only login is refused on the clinic route by the REAL gate (302 to portal, or 403)",
   rv.status_code in (302, 403), str(rv.status_code))
ck("nothing was written to the copied db by the walk (no audit row from these routes)",
   sqlite3.connect(DB).execute("SELECT COUNT(*) FROM audit_log WHERE table_name='bank_mpr_status'").fetchone()[0] == 0)
ck("the temp statement store is still empty (the routes never write files)", os.listdir(STORE) == [])

# the other mounts still answer (nothing broken by the chain)
rv = c.get("/finance/purchase/api/healthz")
ck("S224_MARG_PURCHASES healthz still public and 200", rv.status_code == 200, str(rv.status_code))
rv = c.get("/finance/healthz")
ck("/finance/healthz still 200", rv.status_code == 200, str(rv.status_code))

shutil.rmtree(TMP, ignore_errors=True)
print("\n%d passed, %d failed" % (len(PASSED), len(FAILED)))
if FAILED:
    print("FAILED: " + "; ".join(FAILED))
sys.exit(1 if FAILED else 0)
