#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""selftest_staff_pages.py — the two guided flows walked through the REAL
register, mounted at the REAL prefix.

joiner_app.py is the untouched S207 file (its own 65 checks run separately).
This walks what the PAGE will drive: Amir's joining end to end, Pravesh's
exit end to end, the refusals in words, the Emp Code rule, the WhatsApp
message, and the owner password reset — all at /finance/staff/*.

    python3 selftest_staff_pages.py     exit 0 = passed
"""
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flask import Flask, jsonify           # noqa: E402
import joiner_app                           # noqa: E402
import staff_pages                          # noqa: E402

_fail, _pass = [], 0


def ck(label, cond, detail=""):
    global _pass
    if cond:
        _pass += 1
        print("  ok   %s" % label)
    else:
        _fail.append(label)
        print("  FAIL %s   %s" % (label, detail))


tmp = tempfile.mkdtemp(prefix="staff_")
CON = sqlite3.connect(os.path.join(tmp, "t.db"), check_same_thread=False)
CON.row_factory = sqlite3.Row
ROLE = {"user": "manoj", "roles": ["checker"]}


def db():
    return CON


def require(*roles):
    have = set(ROLE.get("roles") or [])
    if not have.intersection(roles):
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return dict(ROLE), None


app = Flask(__name__)
# require() here returns a USER DICT -- the LIVE app's signature, on purpose:
# it is what exposed the register's latent crash. The adapter is under test.
joiner_app.init(app, db, staff_pages.joiner_require(require),
                url_prefix="/finance/staff")
staff_pages.init(app, require)
c = app.test_client()

print("[1] mounted where the proxy can reach it")
ck("the guided page is served at /finance/staff",
   c.get("/finance/staff").status_code == 200)
ck("the register answers at /finance/staff/api/healthz",
   c.get("/finance/staff/api/healthz").status_code == 200)

print("\n[2] Amir's joining, end to end")
j = c.post("/finance/staff/api/open",
           json={"person": "Amir Test", "role": "purchase", "kind": "JOIN",
                 "opened_by": "Dr Manoj"}).get_json()
ck("opened", j["ok"], j)
REF = j["ref"]
r = c.post("/finance/staff/api/step",
           json={"ref": REF, "step": "CREDENTIALS_SENT", "by": "Dr Manoj"})
ck("a step out of order is refused BY THE REGISTER, in words",
   r.status_code == 409 and "message" in r.get_json())
# DECIDED is auto-ticked by /open (the register's design); walking it again
# would be refused as Already done.
for step in ("ACCOUNT_CREATED", "CREDENTIALS_SENT", "FIRST_LOGIN"):
    r = c.post("/finance/staff/api/step",
               json={"ref": REF, "step": step, "by": "Dr Manoj"})
    ck("%s ticked" % step, r.status_code == 200, r.get_json())
r = c.post("/finance/staff/api/step",
           json={"ref": REF, "step": "STAFF_MASTER", "by": "Dr Manoj"})
ck("STAFF_MASTER refused while BIOMETRIC pending (the hole this closes)",
   r.status_code == 409)
n = c.get("/finance/staff/api/next_code?seen=11,12,27,19,33").get_json()
ck("next code is one above the highest EVER seen (34, never a gap)",
   n["next_code"] == 34, n)
r = c.post("/finance/staff/api/step",
           json={"ref": REF, "step": "BIOMETRIC", "by": "Dr Manoj",
                 "emp_code": "34"})
ck("BIOMETRIC with the code", r.status_code == 200, r.get_json())
r = c.post("/finance/staff/api/step",
           json={"ref": REF, "step": "STAFF_MASTER", "by": "Dr Manoj"})
ck("now STAFF_MASTER completes the joining", r.status_code == 200)
m = c.get("/finance/staff/api/message?ref=%s" % REF).get_json()
ck("the WhatsApp message is composed with the derived login",
   m["ok"] and "amir" in m["text"])

print("\n[3] Pravesh's exit, end to end")
j = c.post("/finance/staff/api/open",
           json={"person": "Pravesh Test", "kind": "EXIT",
                 "opened_by": "Dr Manoj"}).get_json()
ck("exit opened", j["ok"])
R2 = j["ref"]
for step in ("PORTAL_DISABLED", "BIOMETRIC_REMOVED",
             "ROSTER_INACTIVE", "DUES_SETTLED", "ITEMS_RETURNED",
             "STAFF_MASTER"):
    r = c.post("/finance/staff/api/step",
               json={"ref": R2, "step": step, "by": "Dr Manoj",
                     "detail": "test"})
    ck("%s ticked" % step, r.status_code == 200, r.get_json())
rec = c.get("/finance/staff/api/record?ref=%s" % R2).get_json()
ck("the exit record is COMPLETE with every hand named",
   rec["status"] == "COMPLETE" and all(s["done_by"] for s in rec["steps"]))
ck("pending list is empty again",
   c.get("/finance/staff/api/pending").get_json()["count"] == 0)

print("\n[4] the owner password reset (R10, already inside the register)")
j = c.post("/finance/staff/api/reset_password",
           json={"person": "Amir Test", "by": "Dr Manoj",
                 "reason": "test"}).get_json()
ck("reset returns the default to read out", j["ok"] and j["password"] == "amir1234")
ROLE.update(user="darpan", roles=["maker"])
ck("a maker cannot open or reset", c.post(
    "/finance/staff/api/reset_password",
    json={"person": "X", "by": "d"}).status_code == 403)

print("\n%d passed, %d failed" % (_pass, len(_fail)))
for f in _fail:
    print("  FAILED:", f)
CON.close()
import shutil                                # noqa: E402
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if _fail else 0)
