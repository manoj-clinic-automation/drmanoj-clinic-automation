#!/usr/bin/env python3
"""walk_s721.py -- kit S721 (session 390, the parent). The physio register on a made-up database only.
   python walk_s721.py <physio_book.py under test> <the live physio_book.py>
The home-visit backfill and reception's clinic-only slips; Bhati's clinic and home lists byte-identical to the live module's.
The control (live file as the first argument) must go RED. Exit 0 = WALK OK."""
import importlib.util, os, re, sqlite3, sys, tempfile
from urllib.parse import urlparse, parse_qs

from flask import Flask, g, request

test, live = sys.argv[1], sys.argv[2]
os.environ["PHYSIO_BOOK_NOW"] = "2026-11-06T14:30:00"
ROLES = {"manoj": {"checker"}, "bhati": {"maker"}, "reception": {"maker"}, "alisha": {"maker"}, "shivani": {"maker"}, "amir": set()}
oks, fails = [], []


def ck(n, c):
    (oks if c else fails).append(n)
    print(("  ok   " if c else "  FAIL ") + n)


def load(path, name):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def fixture(dbp):
    c = sqlite3.connect(dbp)
    c.executescript("CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT);"
                    "CREATE TABLE clinic_day_line (clinic_id TEXT, patient TEXT, business_date TEXT);"
                    "CREATE TABLE clinic_physio_day (business_date TEXT PRIMARY KEY, cash_p INTEGER, upi_p INTEGER);"
                    "INSERT INTO setting VALUES ('physio_book.on','1',''),('physio_book.from','2026-10-01','');"
                    "INSERT INTO clinic_day_line VALUES ('C0001','Ram Lal','2026-10-20'),('C0002','Sita Devi','2026-10-21');"
                    "INSERT INTO clinic_physio_day VALUES ('2026-11-05', 50000, 0);")
    c.commit(); c.close()


def build(path, name, dbp):
    m = load(path, name)
    app = Flask(name)
    app.config["TESTING"] = True

    def db():
        if "con" not in g:
            g.con = sqlite3.connect(dbp)
            g.con.row_factory = sqlite3.Row
        return g.con

    @app.teardown_appcontext
    def _c(e):
        x = g.pop("con", None)
        if x:
            x.close()

    def require(*roles, unit=None):
        u = request.headers.get("X-User", "")
        r = ROLES.get(u, set())
        if not (r & set(roles)):
            return None, ("denied", 403)
        return {"user": u, "roles": sorted(r)}, None

    def audit(con, table, row_id, action, before=None, after=None, who=None):
        con.execute("CREATE TABLE IF NOT EXISTS audit (t TEXT, id INT, a TEXT, before TEXT, after TEXT, who TEXT)")
        con.execute("INSERT INTO audit VALUES (?,?,?,?,?,?)", (table, row_id, action, str(before), str(after), who))
    m.init(app, db, require, audit)
    return m, app.test_client()


t = tempfile.mkdtemp(prefix="s721_")
dbn, dbo = os.path.join(t, "n.db"), os.path.join(t, "o.db")
fixture(dbn); fixture(dbo)
M, C = build(test, "pk_new", dbn)
L, CL = build(live, "pk_live", dbo)
H = lambda u: {"X-User": u}
q = lambda sql, *a: sqlite3.connect(dbn).execute(sql, a).fetchall()
loc = lambda r: parse_qs(urlparse(r.headers.get("Location", "")).query)
strip = lambda h: re.sub(r"<style>.*?</style>", "", h, flags=re.S).replace("Register (slips)", "Bhati (slips)")

# the same patients in both databases
for CC in (C, CL):
    CC.post("/finance/physio/book/home/new", data={"name": "Kamla Devi", "mobile": "98" + "765" + "43210", "rate": "500", "started": "2026-10-19"}, headers=H("bhati"))
    CC.post("/finance/physio/book/slip", data={"day": "2026-11-05", "slip_no": "101", "amount": "250", "mode": "cash", "pick": "cC0001"}, headers=H("bhati"))
cid = q("SELECT id FROM physio_course WHERE kind='home'")[0][0]

# 0 Bhati's own pages, before anything new is written: as the live module's
for path in ("/finance/physio/book", "/finance/physio/book?day=2026-11-05", "/finance/physio/book?tab=home"):
    ck("0 bhati: %s is the live module's page (the style sheet and the match card's one label aside)" % path,
       strip(C.get(path, headers=H("bhati")).get_data(as_text=True)) == strip(CL.get(path, headers=H("bhati")).get_data(as_text=True)))

# B the backfill
pg = C.get("/finance/physio/book/home/%d" % cid, headers=H("bhati")).get_data(as_text=True)
ck("B1 the home patient's page carries 'Purane visit ek saath (backfill)'", "Purane visit ek saath (backfill)" in pg)
ck("B2 its tick boxes run from 01-Oct to today (37 days), October and November apart",
   pg.count("name='day' value='2026-") >= 37 and "value='2026-10-01'" in pg and "value='2026-11-06'" in pg and "October 2026" in pg and "November 2026" in pg)
r = C.post("/finance/physio/book/home/visits", data={"course": cid, "day": ["2026-10-03", "2026-10-05", "2026-10-19"], "amount": "500"}, headers=H("bhati"))
ck("B3 three ticked days -> three visits, '3 visit likh diye'", loc(r).get("msg") == ["visits"] and loc(r).get("n") == ["3"]
   and q("SELECT day, amount_p, by_whom FROM physio_session WHERE course_id=? ORDER BY day", cid) ==
   [("2026-10-03", 50000, "bhati"), ("2026-10-05", 50000, "bhati"), ("2026-10-19", 50000, "bhati")])
ck("B4 the start moved back from 19-Oct to 03-Oct, audited", q("SELECT started FROM physio_course WHERE id=?", cid) == [("2026-10-03",)]
   and q("SELECT COUNT(*) FROM audit WHERE t='physio_course' AND a='started'") == [(1,)])
ck("B5 every visit audited as a backfill", q("SELECT COUNT(*) FROM audit WHERE t='physio_session' AND after LIKE '%backfill%'") == [(3,)])
pg2 = C.get("/finance/physio/book/home/%d?msg=visits&n=3" % cid, headers=H("bhati")).get_data(as_text=True)
ck("B6 the page then says '✓ 3 visit likh diye' and shows the three days done", "✓ 3 visit likh diye" in pg2 and pg2.count("bf done") == 3)
r = C.post("/finance/physio/book/home/visits", data={"course": cid, "day": ["2026-10-03", "2026-10-07"], "amount": "500"}, headers=H("bhati"))
ck("B7 a day already written is never written twice (1 new of 2)", loc(r).get("n") == ["1"] and q("SELECT COUNT(*) FROM physio_session WHERE course_id=?", cid) == [(4,)])
for name, days, e in (("before the floor", ["2026-09-30"], "day"), ("in the future", ["2026-11-07"], "day"), ("nothing ticked", [], "noday")):
    n0 = q("SELECT COUNT(*) FROM physio_session")
    r = C.post("/finance/physio/book/home/visits", data={"course": cid, "day": days, "amount": "500"}, headers=H("bhati"))
    ck("B8 refused, nothing written: %s" % name, loc(r).get("err") == [e] and q("SELECT COUNT(*) FROM physio_session") == n0)
r = C.post("/finance/physio/book/home/visits", data={"course": cid, "day": ["2026-10-09"], "amount": "abc"}, headers=H("bhati"))
ck("B9 a bad amount is refused", loc(r).get("err") == ["amount"])
sqlite3.connect(dbn).execute("UPDATE setting SET value='2026-07-01' WHERE key='physio_book.from'").connection.commit()
import datetime as dt
many = [(dt.date(2026, 7, 1) + dt.timedelta(days=i)).isoformat() for i in range(63)]
r = C.post("/finance/physio/book/home/visits", data={"course": cid, "day": many, "amount": "500"}, headers=H("bhati"))
ck("B10 more than 62 days in one press is refused", loc(r).get("err") == ["toomany"])
c2 = sqlite3.connect(dbn); c2.execute("UPDATE setting SET value='2026-10-01' WHERE key='physio_book.from'"); c2.commit()
r = C.post("/finance/physio/book/home/pay", data={"course": cid, "day": "2026-10-03", "amount": "1500", "mode": "cash"}, headers=H("bhati"))
ck("B11 a payment of 03-Oct is now taken (the start moved back)", loc(r).get("msg") == ["paid"])
c2.execute("UPDATE physio_course SET status='paused' WHERE id=?", (cid,)); c2.commit()
r = C.post("/finance/physio/book/home/visits", data={"course": cid, "day": ["2026-10-10"], "amount": "500"}, headers=H("bhati"))
ck("B12 a paused patient: 'Pehle Phir shuru dabaiye'", loc(r).get("err") == ["notactive"])
c2.execute("UPDATE physio_course SET status='active' WHERE id=?", (cid,)); c2.commit()
r = C.post("/finance/physio/book/home/visits", data={"course": cid, "day": ["2026-10-12"], "amount": "500"}, headers=H("manoj"))
ck("B13 the doctor can backfill too", loc(r).get("n") == ["1"])
# a second home course of the same patient (the first closed): a day of the old course is never written again
c2.execute("UPDATE physio_course SET status='closed' WHERE id=?", (cid,)); c2.commit()
c2.execute("INSERT INTO physio_course (patient_id, kind, rate_p, status, started) SELECT patient_id, 'home', 50000, 'active', '2026-11-01' FROM physio_course WHERE id=?", (cid,)); c2.commit()
cid2 = q("SELECT MAX(id) FROM physio_course")[0][0]
r = C.post("/finance/physio/book/home/visits", data={"course": cid2, "day": ["2026-10-03", "2026-10-25"], "amount": "500"}, headers=H("bhati"))
ck("B14 across the patient's courses: 03-Oct (written on the closed course) is not written again; 25-Oct is", loc(r).get("n") == ["1"]
   and q("SELECT COUNT(*) FROM physio_session s JOIN physio_course k ON k.id=s.course_id WHERE k.patient_id=(SELECT patient_id FROM physio_course WHERE id=?) AND s.day='2026-10-03' AND s.voided_at=''", cid) == [(1,)])
c2.execute("DELETE FROM physio_session WHERE course_id=?", (cid2,)); c2.execute("DELETE FROM physio_course WHERE id=?", (cid2,)); c2.execute("UPDATE physio_course SET status='active' WHERE id=?", (cid,)); c2.commit()

# R reception
pr = C.get("/finance/physio/book", headers=H("reception")).get_data(as_text=True)
ck("R1 reception opens the register's Clinic tab", "Physio register" in pr and "Slip" in pr)
ck("R2 reception sees no Ghar (Home visit) tab", "Ghar (Home visit)" not in pr)
ph = C.get("/finance/physio/book?tab=home", headers=H("reception")).get_data(as_text=True)
ck("R3 ?tab=home still shows reception the Clinic tab", "Ghar ke patient" not in ph and "Naya ghar patient" not in ph)
r = C.post("/finance/physio/book/slip", data={"day": "2026-11-05", "slip_no": "102", "amount": "250", "mode": "upi", "pick": "cC0002"}, headers=H("reception"))
ck("R4 reception writes a clinic slip", loc(r).get("msg") == ["saved"] and q("SELECT by_whom FROM physio_session WHERE slip_no=102") == [("reception",)])
r = C.post("/finance/physio/book/slip", data={"day": "2026-11-05", "slip_no": "101", "amount": "250", "mode": "cash", "pick": "cC0002"}, headers=H("reception"))
ck("R5 a slip Bhati already wrote is refused for reception too", loc(r).get("err") == ["dup"])
n0 = q("SELECT COUNT(*) FROM physio_session"), q("SELECT COUNT(*) FROM physio_payment"), q("SELECT COUNT(*) FROM physio_course")
r = C.get("/finance/physio/book/home/%d" % cid, headers=H("reception"))
ck("R6 a home patient's page is refused to reception", loc(r).get("err") == ["clinic_only"])
for path, data in (("/finance/physio/book/home/visit", {"course": cid, "day": "2026-11-01", "amount": "500"}),
                   ("/finance/physio/book/home/visits", {"course": cid, "day": ["2026-11-01"], "amount": "500"}),
                   ("/finance/physio/book/home/pay", {"course": cid, "day": "2026-11-01", "amount": "500", "mode": "cash"}),
                   ("/finance/physio/book/home/new", {"name": "Test Person", "mobile": "9" * 10, "rate": "500"}),
                   ("/finance/physio/book/home/status", {"course": cid, "status": "closed"})):
    r = C.post(path, data=data, headers=H("reception"))
    ck("R7 refused to reception: %s" % path.rsplit("/", 1)[1], loc(r).get("err") == ["clinic_only"])
ck("R8 nothing of the home side was written by those", (q("SELECT COUNT(*) FROM physio_session"), q("SELECT COUNT(*) FROM physio_payment"), q("SELECT COUNT(*) FROM physio_course")) == n0
   and q("SELECT status FROM physio_course WHERE id=?", cid) == [("active",)])
hv = q("SELECT id FROM physio_session WHERE course_id=? LIMIT 1", cid)[0][0]
r = C.post("/finance/physio/book/void", data={"kind": "session", "id": hv, "why": "twice"}, headers=H("reception"))
ck("R9 reception cannot void a home visit", loc(r).get("err") == ["clinic_only"] and q("SELECT voided_at FROM physio_session WHERE id=?", hv) == [("",)])
sid = q("SELECT id FROM physio_session WHERE slip_no=102")[0][0]
r = C.post("/finance/physio/book/void", data={"kind": "session", "id": sid, "why": "amount"}, headers=H("reception"))
ck("R10 reception can void a clinic slip (as Bhati can)", q("SELECT voided_by FROM physio_session WHERE id=?", sid) == [("reception",)])
ck("R11 Bhati still has the Ghar tab", "Ghar (Home visit)" in C.get("/finance/physio/book", headers=H("bhati")).get_data(as_text=True))
c2.execute("INSERT OR REPLACE INTO setting VALUES ('physio_book.home_makers','bhati,reception','')"); c2.commit()
ck("R12 the setting governs it: reception named a home maker sees the Ghar tab", "Ghar (Home visit)" in C.get("/finance/physio/book", headers=H("reception")).get_data(as_text=True))
c2.execute("DELETE FROM setting WHERE key='physio_book.home_makers'"); c2.commit()
ck("R13 the doctor is never limited, even if not named", (c2.execute("INSERT OR REPLACE INTO setting VALUES ('physio_book.home_makers','bhati','')"), c2.commit(), "Ghar (Home visit)" in C.get("/finance/physio/book", headers=H("manoj")).get_data(as_text=True))[2])
ck("R16 a maker nobody named (a new receptionist) is clinic-only by default", (ROLES.__setitem__("newgirl", {"maker"}), "Ghar (Home visit)" not in C.get("/finance/physio/book", headers=H("newgirl")).get_data(as_text=True))[1])
pid_home = q("SELECT patient_id FROM physio_course WHERE id=?", cid)[0][0]
r = C.post("/finance/physio/book/patient/cid", data={"pid": pid_home, "clinic_id": "C0099", "back": "/finance/physio/book"}, headers=H("reception"))
ck("R17 reception cannot set the clinic ID of a home-only patient", loc(r).get("err") == ["clinic_only"] and q("SELECT clinic_id FROM physio_patient WHERE id=?", pid_home) == [("",)])
c2.execute("DELETE FROM setting WHERE key='physio_book.home_makers'"); c2.commit()
for who in ("alisha", "shivani"):
    pa = C.get("/finance/physio/book", headers=H(who)).get_data(as_text=True)
    ck("R15 %s (receptionist) writes clinic slips and has no Ghar tab" % who, "Slip" in pa and "Ghar (Home visit)" not in pa
       and loc(C.get("/finance/physio/book/home/%d" % cid, headers=H(who))).get("err") == ["clinic_only"])
ck("R14 a login with no role is still refused", C.get("/finance/physio/book", headers=H("amir")).status_code == 403)
s_new, s_old = open(test, encoding="utf-8").read(), open(live, encoding="utf-8").read()
ck("S1 the SCHEMA is the live module's (no new table)", M.SCHEMA == L.SCHEMA)
ck("S2 nothing new writes clinic_physio_day or the setting table", s_new.count("INTO clinic_physio_day") == s_old.count("INTO clinic_physio_day")
   and s_new.count("INTO setting") == s_old.count("INTO setting"))
print(("WALK OK %d/%d" % (len(oks), len(oks) + len(fails))) if not fails else ("WALK RED %d of %d failed" % (len(fails), len(oks) + len(fails))))
sys.exit(1 if fails else 0)
