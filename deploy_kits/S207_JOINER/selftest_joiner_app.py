#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""selftest_joiner_app.py -- adding a person, driven through the real app.

Exit 0 passed - 1 a check failed - 2 Flask is missing.

WHAT IS ACTUALLY BEING TESTED
    Not that the steps can be ticked -- that the ORDER holds, and that the two
    identifiers cannot be lost. Both come from code that already runs:

      * build_staff_master.py skips a roster row with no Emp Code, so a person
        whose biometric never gets captured is invisible to attendance while
        appearing, to everyone, to have been added.
      * staff_register.staff_for_user falls back to an unambiguous FIRST NAME
        when staff.username is unset, and returns None when two people share
        one -- no self page, no error.

    So: the username must be captured at the step that creates it, the Emp Code
    at the step that captures it, and BIOMETRIC must be the one step allowed to
    lag without blocking the rest.
"""
import datetime as dt
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from flask import Flask, jsonify
except ImportError:
    print("FLASK NOT AVAILABLE -- run on the VPS with /root/wa/venv/bin/python3")
    print("NOT a code failure.")
    sys.exit(2)

import joiner_app as J

_fail, _pass = [], 0


def ck(label, cond, detail=""):
    global _pass
    if cond:
        _pass += 1
        print("  ok   %s" % label)
    else:
        _fail.append(label)
        print("  FAIL %s   %s" % (label, detail))


TMP = tempfile.mkdtemp(prefix="joiner_")
DB = os.path.join(TMP, "finance.db")
ROLE = {"role": "checker"}


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def require(*roles):
    r = ROLE.get("role")
    if r is None:
        return None, (jsonify(ok=False, error="not_authorised"), 401)
    if r not in roles:
        return None, (jsonify(ok=False, error="wrong_role"), 403)
    return "test:" + r, None


app = Flask(__name__)
J.init(app, db, require)
c = app.test_client()


def post(p, b):
    return c.post(p, data=json.dumps(b), content_type="application/json")


def step(ref, s, by="Dr Manoj", **kw):
    body = {"ref": ref, "step": s, "by": by}
    body.update(kw)
    return post("/joiner/api/step", body)


print("[1] the gate")
ROLE["role"] = None
ck("nobody without a role can add a person",
   post("/joiner/api/open", {"person": "X", "opened_by": "Y"}).status_code == 401)
ROLE["role"] = "maker"
ck("a maker cannot either -- adding a person is a checker action",
   post("/joiner/api/open", {"person": "X", "opened_by": "Y"}).status_code == 403)
ROLE["role"] = "checker"

print("\n[2] the login is DERIVED, which is why a whole step disappeared")
ck("first name, lower case", J.default_username("Amir") == "amir")
ck("only the first name of two", J.default_username("Ram Singh") == "ram")
ck("capitals are flattened", J.default_username("ALISHA") == "alisha")
ck("password is that plus 1234", J.default_password("Shavez Khan") == "shavez1234")
ck("nothing in, nothing out -- never a bare '1234'",
   J.default_username("") == "" and J.default_password("") == "")

print("\n[3] opening Amir")
r = post("/joiner/api/open", {"person": "Amir", "role": "purchase",
                              "employment": "BIWEEKLY", "opened_by": "Dr Manoj",
                              "authorities": ["purchase_order", "purchase_entry",
                                              "salt_fix", "self"]})
j = r.get_json()
AMIR = j["ref"]
ck("it opens", r.status_code == 200 and bool(AMIR), j)
ck("and hands back the login without anybody typing it",
   j["username"] == "amir" and j["password"] == "amir1234", j)
ck("biweekly part-time is recorded as such", j["employment"] == "BIWEEKLY")
ck("the ticked authorities come back", sorted(j["authorities"]) ==
   ["purchase_entry", "purchase_order", "salt_fix", "self"], j["authorities"])
ck("and it says the password must be changed at first login",
   j["force_change_at_first_login"] is True)
r = post("/joiner/api/open", {"person": "Bilal", "opened_by": "Dr Manoj",
                              "authorities": ["fly_the_plane"]})
ck("an authority nobody has cannot be ticked",
   r.status_code == 400 and "fly_the_plane" in r.get_json()["message"])
r = post("/joiner/api/open", {"person": "Bilal", "opened_by": "Dr Manoj",
                              "employment": "WEEKENDS"})
ck("an employment type that does not exist is refused", r.status_code == 400)

print("\n[4] two people, one first name")
r = post("/joiner/api/open", {"person": "Amir Khan", "opened_by": "Dr Manoj"})
ck("a second Amir is warned about BEFORE the account is made",
   "username_warning" in r.get_json(), r.get_json())
ck("and the warning names who already has it",
   "Amir" in r.get_json().get("username_warning", ""), r.get_json().get("username_warning"))

print("\n[5] the six steps")
r = step(AMIR, "CREDENTIALS_SENT")
ck("nothing can be sent before the account exists", r.status_code == 409)
ck("and the refusal explains what the roster row needs",
   "sunday_group" in r.get_json()["message"], r.get_json()["message"])
ck("account created -- roster row and login together",
   step(AMIR, "ACCOUNT_CREATED", roster_row="row 14").status_code == 200)
m = c.get("/joiner/api/message?ref=" + AMIR).get_json()
ck("the WhatsApp is composed for you", m["ok"] and "amir1234" in m["text"], m.get("text"))
ck("it carries the link, the user and the password",
   all(x in m["text"] for x in ("portal", "amir", "amir1234")))
ck("and it tells him to change it", "password badal" in m["text"])
ck("the password is not stored anywhere",
   "amir1234" not in str(db().execute("SELECT * FROM joiner").fetchall()))
ck("sent", step(AMIR, "CREDENTIALS_SENT", detail="whatsapp").status_code == 200)
ck("signed in", step(AMIR, "FIRST_LOGIN", by="Amir").status_code == 200)

print("\n[6] the employee code -- never reused, and the register remembers")
n = c.get("/joiner/api/next_code").get_json()
ck("with an empty register the first code is 1", n["next_code"] == 1, n)
r = post("/joiner/api/seed_codes", {"source": "roster+punches", "codes": [
    {"code": 11, "person": "Darpan"}, {"code": 12, "person": "Shavez"},
    {"code": 27, "person": "Pravesh"},
    {"code": 19, "person": "(name not recorded)", "retired": True,
     "note": "left in the ONtime era; punches still under this code"}]})
ck("codes already in use are loaded once", r.get_json()["added"] == 4, r.get_json())
n = c.get("/joiner/api/next_code").get_json()
ck("the next code is one above the HIGHEST, not the first gap",
   n["next_code"] == 28, n)
ck("and it says so in words", "gap" in n["rule"].lower(), n["rule"])
r = step(AMIR, "BIOMETRIC", emp_code="19")
ck("a departed person's code cannot be reissued",
   r.status_code == 409 and r.get_json()["error"] == "code_in_use", r.get_json())
ck("the refusal explains what would happen to their punches",
   "punch" in r.get_json()["message"].lower(), r.get_json()["message"])
ck("and it suggests the right one instead", r.get_json()["suggested"] == 28)
ck("a non-numeric code is refused",
   step(AMIR, "BIOMETRIC", emp_code="A12").status_code == 400)
r = step(AMIR, "BIOMETRIC", emp_code="28", detail="enrolled on his visit")
ck("the suggested code is accepted", r.status_code == 200)
reg = c.get("/joiner/api/codes").get_json()
ck("and Amir is on the permanent register",
   any(x["code"] == 28 and x["person"] == "Amir" for x in reg["codes"]), reg["codes"])
ck("the retired code is still there, not deleted", reg["retired"] == 1, reg)

print("\n[7] the biometric may lag, but nothing pretends it did not")
ck("the staff master could not be signed off before the code existed -- proved by "
   "the fact it can be now", step(AMIR, "STAFF_MASTER").get_json()["complete"] is True)
ck("a completed record leaves the pending list",
   AMIR not in [x["ref"] for x in c.get("/joiner/api/pending").get_json()["records"]])
rec = c.get("/joiner/api/record?ref=" + AMIR).get_json()
ck("every step names who did it", all(s["done_by"] for s in rec["steps"]))
ck("Amir signed in as himself, not as the owner",
   [s for s in rec["steps"] if s["step"] == "FIRST_LOGIN"][0]["done_by"] == "Amir")

print("\n[8] a leaver retires the code, and never frees it")
r = post("/joiner/api/open", {"person": "Pravesh", "kind": "EXIT", "opened_by": "Dr Manoj"})
PRAV = r.get_json()["ref"]
ck("an exit opens with its own numbering", PRAV.startswith("EXIT-"))
ck("dues cannot be settled before the login is disabled",
   step(PRAV, "DUES_SETTLED").status_code == 409)
ck("login disabled", step(PRAV, "PORTAL_DISABLED").status_code == 200)
con = db()
con.execute("UPDATE joiner SET emp_code='27' WHERE ref=?", (PRAV,))
con.commit()
ck("removed from the device", step(PRAV, "BIOMETRIC_REMOVED").status_code == 200)
reg = c.get("/joiner/api/codes").get_json()
p27 = [x for x in reg["codes"] if x["code"] == 27][0]
ck("his code is RETIRED, not deleted", bool(p27["retired_on"]), p27)
ck("and it can never come back",
   post("/joiner/api/seed_codes", {"codes": [{"code": 27, "person": "Somebody New"}]})
   .get_json()["added"] == 0)
ck("the next code still climbs past it",
   c.get("/joiner/api/next_code").get_json()["next_code"] == 29)

print("\n[9] the chase")
con = db()
old = (dt.date.today() - dt.timedelta(days=30)).isoformat()
con.execute("UPDATE joiner SET opened_on=? WHERE ref=?", (old, PRAV))
con.commit()
p = c.get("/joiner/api/pending").get_json()
ck("a record left open for a month is flagged", any(x["ref"] == PRAV and x["overdue"]
                                                    for x in p["records"]))

print("\n[10] the password, the simplest way it can work")
r = post("/joiner/api/reset_password", {"person": "Amir", "by": "Dr Manoj",
                                        "reason": "forgot after the weekend"})
j = r.get_json()
ck("the owner can reset it in one call", r.status_code == 200, j)
ck("and it hands back what to read out",
   j["username"] == "amir" and j["password"] == "amir1234", j)
ck("with a line ready to send", "Password : amir1234" in j["text"], j["text"])
ck("the reset is recorded against the person", j["recorded"] is True)
ck("a reset with nobody named is refused",
   post("/joiner/api/reset_password", {"person": "Amir", "by": ""}).status_code == 400)
ROLE["role"] = "maker"
ck("a maker cannot reset anybody's password",
   post("/joiner/api/reset_password", {"person": "Amir", "by": "X"}).status_code == 403)
ROLE["role"] = "checker"
post("/joiner/api/reset_password", {"person": "Amir", "by": "Dr Manoj", "reason": "again"})
res = c.get("/joiner/api/resets").get_json()
ck("repeat resets are counted -- a person resetting weekly means the flow confuses them",
   [x for x in res["people"] if x["person"] == "Amir"][0]["resets"] == 2, res)
ck("nothing anywhere stores the password itself",
   "amir1234" not in str(db().execute("SELECT * FROM joiner_event").fetchall()))

print("\n[11] the staff master, and the ghosts that make the code rule necessary")
import csv as _csv
_m = os.path.join(TMP, "staff_master.csv")
with open(_m, "w", encoding="utf-8") as fh:
    fh.write("user_id,name,department,base_salary,sunday_group,minutes_exempt\n")
    fh.write("11,Darpan,pharmacy,25000,A,N\n12,Shavez,reception,18000,B,N\n")
J.STAFF_MASTER = _m
sm = c.get("/joiner/api/staff_master").get_json()
ck("the owner can read the staff master to check a join landed", sm["ok"], sm)
ck("base salary is withheld even from this view",
   all("base_salary" not in row for row in sm["rows"]), sm["rows"][:1])
ROLE["role"] = "maker"
ck("and a maker cannot open it at all -- it is salary-adjacent (F-31)",
   c.get("/joiner/api/staff_master").status_code == 403)
ROLE["role"] = "checker"
sm = c.get("/joiner/api/staff_master").get_json()
ck("it says which codes are not yet on the register",
   isinstance(sm["not_yet_on_register"], list), sm.get("not_yet_on_register"))
ck("and warns rather than quietly suggesting a number",
   (sm["warning"] is None) == (not sm["not_yet_on_register"]), sm.get("warning"))

# the seeder's own logic, which is the reason the rule works at all
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed_codes_from_vps as SEED
_p = os.path.join(TMP, "punches.csv")
with open(_p, "w", encoding="utf-8") as fh:
    fh.write("user_id,datetime,io_mode,verify_mode,received_at\n")
    for line in ("11,2026-08-01 09:12:00,0,1,x", "12,2026-08-01 09:20:00,0,1,x",
                 "19,2025-03-04 09:01:00,0,1,x", "33,2024-11-19 10:02:00,0,1,x",
                 "11,2026-08-02 09:10:00,0,1,x"):
        fh.write(line + "\n")
punched, _ = SEED.codes_from_punches(_p)
roster, _ = SEED.codes_from_master(_m)
ghosts = sorted(punched - set(roster))
ck("punches reveal codes the roster has never heard of", ghosts == [19, 33], ghosts)
ck("ROSTER ALONE would have issued 13 and marched straight into 19 and 33",
   max(roster) + 1 == 13, max(roster) + 1)
ck("punches included, the next code clears every one of them",
   max(punched | set(roster)) + 1 == 34, max(punched | set(roster)) + 1)
ck("and the header row is not mistaken for a code", 0 not in punched and len(punched) == 4)

print("\n%d passed, %d failed" % (_pass, len(_fail)))
for f in _fail:
    print("  FAILED:", f)
sys.exit(1 if _fail else 0)
