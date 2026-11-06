#!/usr/bin/env python3
"""walk_s733.py -- kit S733_EXIT_CODE_GUARD (session 394, the parent) . F-1147
The joiner/exit register's own Flask routes on a made-up database (no real person, no
real number) -- the file under test, mounted as finance_app mounts it.

    python walk_s733.py <joiner_app.py under test> [<joiner_schema.sql>]

exit 0 and a last line 'WALK OK n/n' = green. The control (the live file) must go RED."""
import datetime as dt
import importlib.util
import os
import shutil
import sqlite3
import sys
import tempfile

path = os.path.abspath(sys.argv[1])
schema = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(
    os.path.dirname(path), "joiner_schema.sql")
t = tempfile.mkdtemp(prefix="s733_")
shutil.copyfile(path, os.path.join(t, "joiner_app.py"))
shutil.copyfile(schema, os.path.join(t, "joiner_schema.sql"))
os.environ["PORTAL_DIR"] = os.path.join(t, "no_portal")      # no user store: never touched
DB = os.path.join(t, "w.db")
oks, fails = [], []


def ck(n, c):
    (oks if c else fails).append(n)
    print(("  ok   " if c else "  FAIL ") + n)


from flask import Flask, g, jsonify  # noqa: E402

app = Flask("walk_s733")


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB, timeout=30)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def _close(_e):
    d = g.pop("db", None)
    if d is not None:
        d.close()


def require(*roles):
    return "walker", None


spec = importlib.util.spec_from_file_location("joiner_app", os.path.join(t, "joiner_app.py"))
J = importlib.util.module_from_spec(spec)
spec.loader.exec_module(J)
J.init(app, db, require, url_prefix="/finance/staff")
C = app.test_client()
A = "/finance/staff/api"
TODAY = dt.date.today().isoformat()


def q(sql, *a):
    con = sqlite3.connect(DB)
    try:
        return con.execute(sql, a).fetchall()
    finally:
        con.close()


def run(sql, *a):
    con = sqlite3.connect(DB)
    con.execute(sql, a)
    con.commit()
    con.close()


def openx(person, **kw):
    body = {"person": person, "kind": "EXIT", "opened_by": "Walker"}
    body.update(kw)
    return C.post(A + "/open", json=body)


def tick(ref, step, **kw):
    body = {"ref": ref, "step": step, "by": "Walker"}
    body.update(kw)
    return C.post(A + "/step", json=body)


def rowcode(ref):
    r = q("SELECT emp_code FROM joiner WHERE ref=?", ref)
    return r[0][0] if r else "?"


def retired(code):
    r = q("SELECT retired_on FROM emp_code WHERE code=?", code)
    return r[0][0] if r else "NOT ON REGISTER"


def done(ref, step):
    return bool(q("SELECT 1 FROM joiner_step s JOIN joiner j ON j.id=s.joiner_id "
                  "WHERE j.ref=? AND s.step=? AND s.done_on IS NOT NULL", ref, step))


# ---- the made-up register
h = C.get(A + "/healthz")
ck("1 healthz answers 200", h.status_code == 200)
ck("2 healthz names kit S733", (h.get_json() or {}).get("kit") == "S733")
seed = {"codes": [{"code": 12, "person": "Asha"}, {"code": 20, "person": "Ravi"},
                  {"code": 17, "person": "Mohan", "retired": True, "retired_on": "2026-08-31"},
                  {"code": 8, "person": "Kiran"}, {"code": 30, "person": "Gopal"},
                  {"code": 31, "person": "gopal "}]}
ck("3 seed of six codes", (C.post(A + "/seed_codes", json=seed).get_json() or {}).get("added") == 6)
# a joiner who got code 24 through the join flow -- 'Ravi Kumar' is NOT 'Ravi'
j = C.post(A + "/open", json={"person": "Ravi Kumar", "kind": "JOIN", "opened_by": "Walker"}).get_json()
JREF = j["ref"]
for s in ("ACCOUNT_CREATED", "CREDENTIALS_SENT", "FIRST_LOGIN"):
    tick(JREF, s)
b = tick(JREF, "BIOMETRIC", emp_code="24")
ck("4 joining unchanged: BIOMETRIC issues code 24", b.status_code == 200 and retired(24) is None)
ZREF = C.post(A + "/open", json={"person": "Zed", "kind": "JOIN", "opened_by": "W"}).get_json()["ref"]
for s in ("ACCOUNT_CREATED", "CREDENTIALS_SENT", "FIRST_LOGIN"):
    tick(ZREF, s)
b = tick(ZREF, "BIOMETRIC", emp_code="12")
ck("5 joining unchanged: a code in use is refused at BIOMETRIC",
   b.status_code == 409 and (b.get_json() or {}).get("error") == "code_in_use")

# ---- an exit finds the code when it is opened
r = openx("asha")
ck("6 exit 'asha' opens and carries code 12 (register, case aside)",
   r.status_code == 200 and rowcode(r.get_json()["ref"]) == "12")
AREF = r.get_json()["ref"]
ck("7 the open says which code it found", r.get_json().get("emp_code") == "12")
r = openx("Ravi Kumar")
RK = r.get_json()["ref"]
ck("8 exit 'Ravi Kumar' carries 24 (from his joining record)", rowcode(RK) == "24")
r = openx("Ravi")
RV = r.get_json()["ref"]
ck("9 exit 'Ravi' carries 20 -- never the first name's 24", rowcode(RV) == "20")
r = openx("Nobody Known")
NB = r.get_json()["ref"]
ck("10 exit of a name with no code carries none", r.status_code == 200 and rowcode(NB) is None)
r = openx("Gopal")
GP = r.get_json()["ref"]
ck("11 two live codes for one name: none taken (ambiguous)", rowcode(GP) is None)
r = openx("Typo Person", emp_code="4x")
ck("12 a typed code that is not digits is refused at the open", r.status_code == 400)

# ---- BIOMETRIC_REMOVED
tick(AREF, "PORTAL_DISABLED")
r = tick(AREF, "BIOMETRIC_REMOVED", last_day="2026-11-05")
ck("13 Asha's tick retires 12 on her last day", r.status_code == 200 and retired(12) == "2026-11-05")
tick(NB, "PORTAL_DISABLED")
r = tick(NB, "BIOMETRIC_REMOVED")
ck("14 no code to be found: REFUSED (409 need_emp_code)",
   r.status_code == 409 and (r.get_json() or {}).get("error") == "need_emp_code")
ck("15 ... and the step is NOT ticked", not done(NB, "BIOMETRIC_REMOVED"))
r = tick(NB, "BIOMETRIC_REMOVED", emp_code="8")
ck("16 a typed code that belongs to another person: REFUSED",
   r.status_code == 409 and (r.get_json() or {}).get("error") == "code_other_person"
   and retired(8) is None and not done(NB, "BIOMETRIC_REMOVED"))
r = tick(NB, "BIOMETRIC_REMOVED", emp_code="77")
ck("17 a typed code from before the register: entered, retired today, on the record",
   r.status_code == 200 and retired(77) == TODAY and rowcode(NB) == "77"
   and q("SELECT person,source FROM emp_code WHERE code=77")[0] == ("Nobody Known", "exit"))
ck("18 ... and the next code is above it (never reissued)",
   C.get(A + "/next_code").get_json()["next_code"] == 78)
tick(RK, "PORTAL_DISABLED")
r = tick(RK, "BIOMETRIC_REMOVED", emp_code="25")
ck("19 a typed code different from the record's: REFUSED",
   r.status_code == 409 and (r.get_json() or {}).get("error") == "code_mismatch" and retired(24) is None)
r = tick(RK, "BIOMETRIC_REMOVED", last_day="2099-01-01")
ck("20 a last day in the future: REFUSED", r.status_code == 400 and retired(24) is None)
r = tick(RK, "BIOMETRIC_REMOVED", last_day="5-11-2026")
ck("21 a last day that is not yyyy-mm-dd: REFUSED", r.status_code == 400 and retired(24) is None)
r = tick(RK, "BIOMETRIC_REMOVED")
ck("22 Ravi Kumar's tick retires 24 and not 20", retired(24) == TODAY and retired(20) is None)
# the S725 case: a code already retired by hand keeps its date
run("UPDATE emp_code SET retired_on='2026-09-30' WHERE code=20")
tick(RV, "PORTAL_DISABLED")
r = tick(RV, "BIOMETRIC_REMOVED")
ck("23 a code already retired keeps its date (2026-09-30)",
   r.status_code == 200 and retired(20) == "2026-09-30")
# an exit opened before this kit, with no code on it
run("INSERT INTO joiner (ref,kind,person,status,opened_on,opened_by,created_at,updated_at) "
    "VALUES ('EXIT-2026-0900','EXIT','Kiran','DECIDED','2026-11-01','old','x','x')")
run("INSERT INTO joiner_step (joiner_id,step,done_on,done_by) SELECT id,'DECIDED','2026-11-01','old' "
    "FROM joiner WHERE ref='EXIT-2026-0900'")
tick("EXIT-2026-0900", "PORTAL_DISABLED")
r = tick("EXIT-2026-0900", "BIOMETRIC_REMOVED")
ck("24 an older exit with no code: the code found at the tick (8), retired, put on the record",
   r.status_code == 200 and retired(8) == TODAY and rowcode("EXIT-2026-0900") == "8")
tick(GP, "PORTAL_DISABLED")
r = tick(GP, "BIOMETRIC_REMOVED")
ck("25 ambiguous name at the tick: REFUSED, neither code retired",
   r.status_code == 409 and retired(30) is None and retired(31) is None)
# the rest of an exit still completes
for s in ("ROSTER_INACTIVE", "DUES_SETTLED", "ITEMS_RETURNED", "STAFF_MASTER"):
    r = tick(AREF, s)
ck("26 Asha's exit completes", (r.get_json() or {}).get("complete") is True)
rec = C.get(A + "/record?ref=" + AREF).get_json()
ck("27 the record page shows the code and the step's words",
   rec.get("emp_code") == "12" and any(
       s["step"] == "BIOMETRIC_REMOVED" and "never given to anybody again" in (s.get("why") or "")
       for s in rec["steps"]))
ck("28 a mohan code retired before stays as it was", retired(17) == "2026-08-31")
# a login is never a name: an exit opened on a bare login finds no code (the tick then asks)
P = C.post(A + "/open", json={"person": "Pooja Rani", "kind": "JOIN", "opened_by": "W",
                               "username": "poojar"}).get_json()["ref"]
for s_ in ("ACCOUNT_CREATED", "CREDENTIALS_SENT", "FIRST_LOGIN"):
    tick(P, s_)
tick(P, "BIOMETRIC", emp_code="40")
r = openx("poojar")
ck("29 an exit opened on a bare login takes no code (a login is not a name)",
   r.status_code == 200 and rowcode(r.get_json()["ref"]) is None)
# REVIEW A: the old 'Hemant' left (code 60 retired); the new 'Hemant Rao' has login 'hemant'
run("INSERT INTO emp_code (code,person,issued_on,retired_on,source) VALUES (60,'Hemant','2026-01-01','2026-05-31','seed')")
HR = C.post(A + "/open", json={"person": "Hemant Rao", "kind": "JOIN", "opened_by": "W",
                                "username": "hemant"}).get_json()["ref"]
for s_ in ("ACCOUNT_CREATED", "CREDENTIALS_SENT", "FIRST_LOGIN"):
    tick(HR, s_)
tick(HR, "BIOMETRIC", emp_code="61")
r = openx("Hemant")
HX = r.get_json()["ref"]
tick(HX, "PORTAL_DISABLED")
r = tick(HX, "BIOMETRIC_REMOVED")
ck("30 a retired namesake: the new joiner's code (login 'hemant') is never taken or retired",
   rowcode(HX) is None and r.status_code == 409 and retired(61) is None)
# REVIEW B: an old joining record carries a retired code; the same name has a live code
run("INSERT INTO emp_code (code,person,issued_on,retired_on,source) VALUES (70,'Sita Ram','2025-01-01','2025-12-31','seed')")
run("INSERT INTO emp_code (code,person,issued_on,retired_on,source) VALUES (71,'Sita Ram','2026-01-01',NULL,'seed')")
run("INSERT INTO joiner (ref,kind,person,status,emp_code,opened_on,opened_by,created_at,updated_at) "
    "VALUES ('JOIN-2025-0070','JOIN','Sita Ram','COMPLETE','70','2025-01-01','old','x','x')")
r = openx("Sita Ram")
SX = r.get_json()["ref"]
tick(SX, "PORTAL_DISABLED")
r = tick(SX, "BIOMETRIC_REMOVED")
ck("31 a retired code on an old joining record is never 'found': the live code 71 is retired",
   rowcode(SX) == "71" and r.status_code == 200 and retired(71) == TODAY and retired(70) == "2025-12-31")
# REVIEW C: a code typed at the open that the register gives to somebody else
r = openx("Stranger", emp_code="12")
ck("32 a typed code of another person at the open: REFUSED", r.status_code == 409)
run("INSERT INTO emp_code (code,person,issued_on,retired_on,source) VALUES (80,'Kamla','2026-01-01',NULL,'seed')")
run("INSERT INTO joiner (ref,kind,person,status,emp_code,opened_on,opened_by,created_at,updated_at) "
    "VALUES ('EXIT-2025-0960','EXIT','Bimla','DECIDED','80','2026-11-06','hand','x','x')")
run("INSERT INTO joiner_step (joiner_id,step,done_on,done_by) SELECT id,'DECIDED','2026-11-06','hand' "
    "FROM joiner WHERE ref='EXIT-2025-0960'")
tick("EXIT-2025-0960", "PORTAL_DISABLED")
r = tick("EXIT-2025-0960", "BIOMETRIC_REMOVED")
ck("33 a code on the record that the register gives to another person: REFUSED, not retired",
   r.status_code == 409 and retired(80) is None)
# should-fix: '008' is stored as 8; a superscript digit is refused, not a crash
r = openx("Leading Zero")
LZ = r.get_json()["ref"]
tick(LZ, "PORTAL_DISABLED")
r = tick(LZ, "BIOMETRIC_REMOVED", emp_code="0090")
ck("34 a typed '0090' retires 90 and the record keeps '90'", r.status_code == 200 and rowcode(LZ) == "90"
   and retired(90) == TODAY)
r = openx("Odd Digit", emp_code="\u00b2")
ck("35 a non-ASCII digit at the open is refused (400), not a crash", r.status_code == 400)
# the live shape of EXIT-2026-0002: the code written on the exit by hand and retired on the
# last day (S725) -- the owner's tick after deleting the finger must not move that date
run("INSERT INTO emp_code (code,person,issued_on,retired_on,source) "
    "VALUES (50,'Hari','2026-08-30','2026-09-30','seed')")
run("INSERT INTO joiner (ref,kind,person,status,emp_code,opened_on,opened_by,created_at,updated_at) "
    "VALUES ('EXIT-2025-0950','EXIT','Hari','DECIDED','50','2026-11-06','hand','x','x')")
run("INSERT INTO joiner_step (joiner_id,step,done_on,done_by) SELECT id,'DECIDED','2026-11-06','hand' "
    "FROM joiner WHERE ref='EXIT-2025-0950'")
tick("EXIT-2025-0950", "PORTAL_DISABLED")
r = tick("EXIT-2025-0950", "BIOMETRIC_REMOVED")
ck("36 an exit carrying a code retired by hand: ticked, the date stays 2026-09-30",
   r.status_code == 200 and retired(50) == "2026-09-30")

shutil.rmtree(t, ignore_errors=True)
n = len(oks) + len(fails)
print("WALK OK %d/%d" % (n, n) if not fails else "WALK RED %d of %d failed" % (len(fails), n))
sys.exit(0 if not fails else 1)
