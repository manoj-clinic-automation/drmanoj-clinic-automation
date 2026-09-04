#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_staff_gate_s225.py -- THE LIVE-SHAPE WALK for the staff order page: the REAL finance_app.py,
its REAL front gate, the REAL purchase_app.py (rev 6) mounted the way gunicorn mounts it -- on a
COPY of finance.db. It writes no order and touches no live file.

On the box (after the copy, BEFORE the restart):
    FIN_DIR=/root/finance /root/wa/venv/bin/python3 -B /root/finance/walk_staff_gate_s225.py
"""
import os
import shutil
import sqlite3
import sys
import tempfile

FIN_DIR = os.environ.get("FIN_DIR", "/root/finance")
SRC_DB = os.environ.get("FIN_DB", os.path.join(FIN_DIR, "finance.db"))
TMP = tempfile.mkdtemp(prefix="walk_s225_")
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
con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('medical','zzwalkstaff','viewer',1)")
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
import purchase_app as PA                                   # noqa: E402
ck("purchase_app beside finance_app is rev 6 (has the staff page)", hasattr(PA, "page_staff") and hasattr(PA, "_staff_send"))
ck("clinic_day_pdf (the PDF writer) is beside it", os.path.exists(os.path.join(FIN_DIR, "clinic_day_pdf.py")))
c = FA.app.test_client()
P = "/finance/purchase"
DOC = {"X-Clinic-User": "zzwalkdoc", "X-Clinic-Role": "doctor"}
STF = {"X-Clinic-User": "zzwalkstaff", "X-Clinic-Role": "staff"}
ck("staff page with nobody signed in -> login redirect", c.get(P + "/page/staff").status_code == 302)
ck("staff page with a login that has no medical role -> refused",
   c.get(P + "/page/staff", headers={"X-Clinic-User": "zzstranger", "X-Clinic-Role": "staff"}).status_code in (302, 403))
r = c.get(P + "/page/staff", headers=STF)
sp = r.get_data(as_text=True)
ck("staff page for a medical VIEWER -> 200 through the real gate", r.status_code == 200, str(r.status_code))
ck("  it shows the three-column page and nothing of the doctor's detail",
   "Order medicines" in sp and "Stock now" in sp and "Per day" not in sp and "Cover after" not in sp and "Save as order" not in sp)
ck("staff page for the checker -> 200", c.get(P + "/page/staff", headers=DOC).status_code == 200)
r = c.post(P + "/api/order", json=dict(action="staff_send", vendor="ZZ WALK NOBODY", lines=[dict(item="ZZ", qty=10)]), headers=STF)
ck("staff_send reaches the route for a viewer: a stockist with no number -> 409, NO order written",
   r.status_code == 409 and (r.get_json() or {}).get("error") == "no_phone", str(r.status_code))
ck("staff_send with nobody signed in -> 302/401",
   c.post(P + "/api/order", json=dict(action="staff_send")).status_code in (302, 401))
ck("a missing order's PDF -> 404 through the real gate (route reached)", c.get(P + "/order/999999/pdf", headers=STF).status_code == 404)
ck("the doctor's Orders page still renders", c.get(P + "/page/orders", headers=DOC).status_code == 200)
ck("the hub still renders", c.get(P + "/page/hub", headers=DOC).status_code == 200)
ck("the finance app's own healthz still answers", c.get("/finance/healthz").status_code == 200)
con = sqlite3.connect(DB)
n = con.execute("SELECT COUNT(*) FROM purchase_order WHERE vendor='ZZ WALK NOBODY'").fetchone()[0]
con.close()
ck("the walk wrote no order into the COPY", n == 0)
shutil.rmtree(TMP, ignore_errors=True)
print("\n%d PASS  %d FAIL" % (len(PASSED), len(FAILED)))
for f in FAILED:
    print("  FAILED: " + f)
sys.exit(1 if FAILED else 0)
