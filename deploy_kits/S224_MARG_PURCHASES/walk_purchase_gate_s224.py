#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_purchase_gate_s224.py -- THE LIVE-SHAPE WALK: the REAL patched finance_app.py, its REAL
front gate, and this blueprint mounted by the REAL patch -- on a COPY of finance.db.

Why it exists: S208's push was refused 401 by the front gate for weeks while every unit test
was green, because the tests supplied their own gate (F-286). This walk supplies nothing:
it imports finance_app from FIN_DIR exactly as gunicorn does and knocks on every door.

On the box (after the patch, BEFORE the restart if you like -- it touches no live file):
    FIN_DIR=/root/finance /root/wa/venv/bin/python3 -B /root/finance/walk_purchase_gate_s224.py
Offline: FIN_DIR=<a folder holding the patched finance_app.py and its modules> python3 -B walk_purchase_gate_s224.py

It never touches the live database: the first thing it does is copy it.
"""
import os
import shutil
import sqlite3
import sys
import tempfile

FIN_DIR = os.environ.get("FIN_DIR", "/root/finance")
SRC_DB = os.environ.get("FIN_DB", os.path.join(FIN_DIR, "finance.db"))
TMP = tempfile.mkdtemp(prefix="walk_s224_")
DB = os.path.join(TMP, "finance.db")
if os.path.exists(SRC_DB):
    shutil.copyfile(SRC_DB, DB)
else:
    con = sqlite3.connect(DB)
    con.executescript(open(os.path.join(FIN_DIR, "finance_schema.sql"), encoding="utf-8").read())
    con.execute("INSERT OR IGNORE INTO business_unit (code, name) VALUES ('medical','Sanjeevni Medicos')")
    con.commit()
    con.close()
con = sqlite3.connect(DB)
con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('medical','zzwalkdoc','checker',1)")
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
ck("finance_app imported with the S224 mount (no import-time db call, F-303)",
   "S224_MARG_PURCHASES begin" in open(FA.__file__, encoding="utf-8").read())
c = FA.app.test_client()
P = "/finance/purchase"
DOC = {"X-Clinic-User": "zzwalkdoc", "X-Clinic-Role": "doctor"}
ck("healthz is PUBLIC through the real gate", c.get(P + "/api/healthz").status_code == 200)
ck("push with the WRONG token -> 401 from the real gate",
   c.post(P + "/api/push", json={}, headers={"X-Finance-Marg": "bad"}).status_code == 401)
ck("push with the wrong header name (X-Finance-Cron) is NOT let in",
   c.post(P + "/api/push", json={}, headers={"X-Finance-Cron": "walk-tok"}).status_code in (401, 302))
r = c.post(P + "/api/push", json={"type": "BILLWISE"}, headers={"X-Finance-Marg": "walk-tok"})
ck("push with the right token REACHES the route (400 malformed, not 302/401)",
   r.status_code == 400 and (r.get_json() or {}).get("error") == "malformed")
ck("feed with the right token reaches the route",
   c.post(P + "/api/feed", json={"state": "ok", "host": "walk"}, headers={"X-Finance-Marg": "walk-tok"}).status_code == 200)
ck("vendors with the right token reaches the route",
   c.post(P + "/api/vendors", json={"pairs": {}}, headers={"X-Finance-Marg": "walk-tok"}).status_code == 200)
ck("the token opens NOTHING else (stock losses stays shut)",
   c.get("/finance/stock/api/losses", headers={"X-Finance-Marg": "walk-tok"}).status_code in (302, 401, 403))
ck("hub with nobody signed in -> login redirect", c.get(P + "/page/hub").status_code == 302)
ck("hub with a login that has no medical role -> refused",
   c.get(P + "/page/hub", headers={"X-Clinic-User": "zzstranger", "X-Clinic-Role": "staff"}).status_code in (302, 403))
r = c.get(P + "/page/hub", headers=DOC)
ck("hub for the medical checker -> 200 and marked (doctor)", r.status_code == 200 and "(doctor)" in r.get_data(as_text=True))
for page in ("orders", "scans"):
    ck("%s page renders for the checker" % page, c.get(P + "/page/" + page, headers=DOC).status_code == 200)
ck("scans page says the asset app is not reachable and nothing else breaks",
   "asset app not reachable" in c.get(P + "/page/scans", headers=DOC).get_data(as_text=True))
ck("the finance app's own healthz still answers", c.get("/finance/healthz").status_code == 200)
ck("the stock count page still answers for the checker", c.get("/finance/stock/page/count", headers=DOC).status_code in (200, 503))
con = sqlite3.connect(DB)
tabs = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
con.close()
ck("the purchase tables now exist in the COPY (created on first request)", "purchase_export" in tabs and "purchase_bill" in tabs)
print("\n%d PASS  %d FAIL" % (len(PASSED), len(FAILED)))
for f in FAILED:
    print("  FAILED: " + f)
sys.exit(1 if FAILED else 0)
