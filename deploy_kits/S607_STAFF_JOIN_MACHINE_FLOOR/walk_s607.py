#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s607.py -- the Add-staff walk (S606 + S607), on SCRATCH COPIES only (kit S606, S331).

    python3 walk_s606.py --code DIR --scratch DIR [--portal-dir DIR]

--code     the folder holding joiner_app.py, joiner_schema.sql, staff_pages.py
           (and, for the new kit, staff_easy.py + staff_easy.html)
--scratch  a folder holding COPIES of finance.db, staff_register.db,
           staff_master.csv, punches.csv, clinic_users.json -- never the live ones.

Made-up people only ("Walk Testone", "Walk Testtwo"), made-up punches dated 2099,
a made-up mobile built at run time. Exit 0 = GREEN, 1 = RED. Run against the OLD
staff_pages.py it must go RED (the negative control): the page does not exist.
"""
import argparse
import datetime as dt
import csv
import io
import os
import sqlite3
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--code", required=True)
ap.add_argument("--scratch", required=True)
ap.add_argument("--portal-dir", default="/root/portal")
a = ap.parse_args()
S = os.path.abspath(a.scratch)
for f in ("finance.db", "staff_register.db", "staff_master.csv", "punches.csv", "clinic_users.json"):
    if not os.path.exists(os.path.join(S, f)):
        print("RED: scratch copy missing: %s" % f)
        sys.exit(1)
    if os.path.realpath(os.path.join(S, f)).startswith(("/root/finance/", "/root/staff_register/", "/root/portal/")) \
            or os.path.realpath(os.path.join(S, f)) in ("/root/staff_master.csv", "/root/punches.csv"):
        print("RED: refusing to walk on a live file: %s" % f)
        sys.exit(1)
os.environ["STAFF_EASY_SR_DB"] = os.path.join(S, "staff_register.db")
os.environ["ATT_STAFF_MASTER"] = os.path.join(S, "staff_master.csv")
os.environ["ATT_PUNCH_CSV"] = os.path.join(S, "punches.csv")
os.environ["CLINIC_USERS_FILE"] = os.path.join(S, "clinic_users.json")
os.environ["PORTAL_DIR"] = a.portal_dir
sys.path.insert(0, os.path.abspath(a.code))
sys.dont_write_bytecode = True

from flask import Flask, g, jsonify  # noqa: E402

import joiner_app  # noqa: E402
import staff_pages  # noqa: E402

FIN = os.path.join(S, "finance.db")
app = Flask("walk")
WHO = {"user": "manoj", "role": "doctor"}


def db():
    if "con" not in g:
        g.con = sqlite3.connect(FIN, timeout=15)
        g.con.row_factory = sqlite3.Row
    return g.con


@app.teardown_appcontext
def _close(_e):
    c = g.pop("con", None)
    if c:
        c.close()


def require(*roles):
    if WHO.get("user") in ("manoj", "shavez"):
        return dict(WHO, roles=["checker"]), None
    return None, (jsonify(ok=False, error="not_permitted"), 403)


joiner_app.init(app, db, staff_pages.joiner_require(require), url_prefix="/finance/staff/api")
staff_pages.init(app, require)
C = app.test_client()

passed, failed = [], []


def check(cond, label):
    (passed if cond else failed).append(label)
    print(("  ok   " if cond else "  FAIL ") + label)
    return cond


def J(r):
    try:
        return r.get_json() or {}
    except Exception:
        return {}


def fin(sql, *args):
    c = sqlite3.connect(FIN)
    c.row_factory = sqlite3.Row
    try:
        return c.execute(sql, args).fetchall()
    finally:
        c.close()


def srq(sql, *args):
    c = sqlite3.connect(os.environ["STAFF_EASY_SR_DB"])
    c.row_factory = sqlite3.Row
    try:
        return c.execute(sql, args).fetchall()
    finally:
        c.close()


def master_codes():
    with io.open(os.environ["ATT_STAFF_MASTER"], encoding="utf-8-sig") as fh:
        return {r["user_id"]: r for r in csv.DictReader(fh)}


def punch(code, when):
    with io.open(os.environ["ATT_PUNCH_CSV"], "a", encoding="utf-8") as fh:
        fh.write("%s,%s,0,1,%s\n" % (code, when, when))


MOB = "".join(["9"] * 10)        # made up, built at run time (F-185)

print("[a] the page and the gate")
r = C.get("/finance/staff/new")
if not check(r.status_code == 200 and b"Add staff" in r.data, "GET /finance/staff/new is the new page"):
    print("RED: the new page is not there (%s)" % r.status_code)
    sys.exit(1)
WHO = {"user": "shavez", "role": "manager"}
check(C.get("/finance/staff/easy/api/list").status_code == 403, "a manager is refused (salary is the doctor's)")
WHO = {"user": "manoj", "role": "doctor"}
L = J(C.get("/finance/staff/easy/api/list"))
check(L.get("ok") and "A" in L.get("sunday", {}), "the list answers, with the Sunday choices")
check(C.get("/finance/staff").status_code == 200, "the old ladder still answers at /finance/staff")

print("[b] refusals in words")
base = dict(person="Walk Testone", handover="whatsapp", mobile="", job="Cleaner",
            employment="PARTTIME", join_date="2099-01-05", wd_start="09:00", wd_end="10:30",
            sunday_group="C", sun_start="09:00", sun_end="10:30", base_salary="1234",
            allowed_offs="4", minutes_exempt="1")
r = C.post("/finance/staff/easy/api/save", json=base)
check(r.status_code == 400 and "10-digit" in J(r).get("message", ""), "WhatsApp without a mobile is refused")
r = C.post("/finance/staff/easy/api/save", json=dict(base, mobile=MOB, sunday_group="Z"))
check(r.status_code == 400, "an unknown Sunday duty is refused")

print("[c] a WhatsApp joiner, start to finish")
r = C.post("/finance/staff/easy/api/save", json=dict(base, mobile="+91 " + MOB))
j = J(r)
check(r.status_code == 200 and j.get("ok"), "saved: %s" % j.get("message"))
ref1 = j.get("ref")
row = fin("SELECT * FROM joiner WHERE ref=?", ref1)[0]
check(row["username"] == "walk", "clean username from the first name: %s" % row["username"])
pend = srq("SELECT * FROM joiner_pending WHERE ref=?", ref1)[0]
check(pend["mobile"] == MOB, "the mobile kept as 10 digits, in the staff register's own table")
check("mobile" not in [c[1] for c in sqlite3.connect(FIN).execute("PRAGMA table_info(joiner)")],
      "no phone number in finance.db")
P = J(C.get("/finance/staff/easy/api/person?ref=%s" % ref1))
check(P.get("stage") == "login" and P["login"]["exists"] is True, "his login exists in the portal store")
check("wa.me" not in P.get("message", "") and "walk1234" in P.get("message", ""), "the message carries user and password")
r = C.post("/finance/staff/easy/api/given", json={"ref": ref1, "how": "whatsapp"})
check(J(r).get("ok"), "login given by WhatsApp")
st = {x["step"]: x["detail"] for x in fin("SELECT s.step,s.detail FROM joiner_step s JOIN joiner j "
                                           "ON j.id=s.joiner_id WHERE j.ref=?", ref1)}
check("CREDENTIALS_SENT" in st and "not tracked" in (st.get("FIRST_LOGIN") or ""),
      "CREDENTIALS_SENT ticked; FIRST_LOGIN says honestly it is not tracked")
# S607: an unknown finger pressed BEFORE this joining was opened is not his -- never offered
_old = (dt.date.today() - dt.timedelta(days=5)).isoformat() + " 06:51:58"
punch(9990, _old)
M = J(C.get("/finance/staff/easy/api/machine?ref=%s" % ref1))
check(9990 not in [x["code"] for x in M["new"]], "an old unknown finger (from before the joining) is not offered")
r = C.post("/finance/staff/easy/api/link", json={"ref": ref1, "code": 9990})
check(r.status_code == 409, "and linking it is refused")
code1 = M["next_code"]
check(isinstance(code1, int) and code1 > 0, "the next unused number is offered: %s" % code1)
r = C.post("/finance/staff/easy/api/link", json={"ref": ref1, "code": code1})
check(r.status_code == 409, "a number the machine has not sent is refused")
punch(code1, "2099-01-05 09:01:00")
M = J(C.get("/finance/staff/easy/api/machine?ref=%s" % ref1))
check(code1 in [x["code"] for x in M["new"]], "his first punch shows as a new finger")
r = C.post("/finance/staff/easy/api/link", json={"ref": ref1, "code": code1})
check(J(r).get("ok"), "linked: %s" % J(r).get("message"))
mc = master_codes()
check(str(code1) in mc and mc[str(code1)]["name"] == "Walk Testone"
      and mc[str(code1)]["sunday_group"] == "C" and mc[str(code1)]["minutes_exempt"] == "Y",
      "in staff_master.csv with his hours and Sunday duty")
s1 = srq("SELECT * FROM staff WHERE staff_id=?", code1)
check(len(s1) == 1 and s1[0]["username"] == "walk" and s1[0]["base_salary"] == 1234,
      "in the staff register, with his login name")
check(len(srq("SELECT * FROM staff_shift WHERE staff_id=?", code1)) == 1, "his shift is recorded")
check(fin("SELECT person FROM emp_code WHERE code=?", code1)[0]["person"] == "Walk Testone",
      "the number is on the never-reuse register")
row = fin("SELECT status FROM joiner WHERE ref=?", ref1)[0]
check(row["status"] == "COMPLETE", "the joining closed by itself: %s" % row["status"])
r = C.post("/finance/staff/easy/api/link", json={"ref": ref1, "code": code1})
check(J(r).get("already"), "a second Yes changes nothing")

punch(17, "2099-01-06 09:00:00")
M = J(C.get("/finance/staff/easy/api/machine"))
check(17 in [x["code"] for x in M["reused"]] and 17 not in [x["code"] for x in M["new"]],
      "a leaver's old number punching again is flagged, never offered")

print("[d] a joiner with no phone")
r = C.post("/finance/staff/easy/api/save",
           json=dict(base, person="Walk Testtwo", handover="none", sunday_group="A"))
ref2 = J(r).get("ref")
row = fin("SELECT * FROM joiner WHERE ref=?", ref2)[0]
check(row["username"] is None, "no login made")
st = {x["step"]: x["detail"] for x in fin("SELECT s.step,s.detail FROM joiner_step s JOIN joiner j "
                                           "ON j.id=s.joiner_id WHERE j.ref=?", ref2)}
check(all(k in st for k in ("ACCOUNT_CREATED", "CREDENTIALS_SENT", "FIRST_LOGIN")),
      "login steps closed as 'no phone'")
P = J(C.get("/finance/staff/easy/api/person?ref=%s" % ref2))
check(P.get("stage") == "machine", "he goes straight to the machine")
code2 = J(C.get("/finance/staff/easy/api/machine"))["next_code"]
check(code2 == code1 + 1, "numbers only go up: %s" % code2)
punch(code2, "2099-01-05 09:05:00")
r = C.post("/finance/staff/easy/api/link", json={"ref": ref2, "code": code2})
check(J(r).get("ok"), "linked")
check(fin("SELECT status FROM joiner WHERE ref=?", ref2)[0]["status"] == "COMPLETE", "complete")
check(srq("SELECT username FROM staff WHERE staff_id=?", code2)[0]["username"] is None,
      "no login name on his register row")

print("[e] a login typed with a space is healed")
c = sqlite3.connect(FIN)
c.execute("INSERT INTO joiner (ref,kind,person,role,status,username,employment,opened_on,opened_by,"
          "created_at,updated_at) VALUES ('JOIN-2099-9001','JOIN','Walk Three','x','ACCOUNT_CREATED',"
          "'walk three','FULLTIME','2099-01-01','walk','2099-01-01T00:00:00','2099-01-01T00:00:00')")
jid = c.execute("SELECT id FROM joiner WHERE ref='JOIN-2099-9001'").fetchone()[0]
for s in ("DECIDED", "ACCOUNT_CREATED"):
    c.execute("INSERT INTO joiner_step (joiner_id,step,done_on,done_by) VALUES (?,?,?,?)",
              (jid, s, "2099-01-01", "walk"))
c.commit()
c.close()
sys.path.insert(0, a.portal_dir)
import clinic_users as CU  # noqa: E402
CU.add_user(os.environ["CLINIC_USERS_FILE"], "walk three", "staff", joiner_app.default_password("Walk Three"))
L = J(C.get("/finance/staff/easy/api/list"))
u3 = fin("SELECT username FROM joiner WHERE ref='JOIN-2099-9001'")[0]["username"]
check(u3 == "walkthree", "renamed to a clean login: %s ('walk' is taken)" % u3)
users = {x["user"] for x in CU.list_users(os.environ["CLINIC_USERS_FILE"])}
check("walk three" not in users and "walkthree" in users, "the old login is gone, the new one signs in")
check(bool(CU.verify_password(os.environ["CLINIC_USERS_FILE"], "walkthree",
                              joiner_app.default_password("Walk Three"))), "and its password works")
r = C.get("/finance/staff/slip?ref=JOIN-2099-9001")
check(r.status_code == 200 and b"walkthree" in r.data, "the printed slip shows it")

print("")
print("WALK S607: %d passed, %d failed" % (len(passed), len(failed)))
print("GREEN" if not failed else "RED")
sys.exit(0 if not failed else 1)
