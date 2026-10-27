#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s667.py -- kit S667_DESK_TODAY's walk on a MADE-UP slip book. Nothing real is read or written.

  python3 walk_s667.py <dir holding the parchi_desk.py under test> <dir holding the live slip_log.py> [--old] [--page <file>]

Mounts slip_log + parchi_desk on a throw-away Flask app over a temp database, opens the desk on 26-Oct, moves the clock to
27-Oct 11:26 (the page left open overnight) and saves from the stale "Aaj"; then a deliberate late entry and an old page's
save; then the data step on made-up rows. --old: the control on the live file -- every S667 check red, every older green.
--page <file>: also writes the rendered desk page (made-up data) for the browser walk."""
import importlib, json, os, shutil, sqlite3, subprocess, sys, tempfile

OLD = "--old" in sys.argv
PAGE = sys.argv[sys.argv.index("--page") + 1] if "--page" in sys.argv else ""
args = [a for a in sys.argv[1:] if not a.startswith("--") and a != PAGE]
if len(args) != 2:
    sys.exit(__doc__)
SRC, LIB = os.path.abspath(args[0]), os.path.abspath(args[1])
KDIR = os.path.dirname(os.path.abspath(__file__))
TMP = tempfile.mkdtemp(prefix="s667walk.")
shutil.copy(os.path.join(SRC, "parchi_desk.py"), os.path.join(TMP, "parchi_desk.py"))
shutil.copy(os.path.join(LIB, "slip_log.py"), os.path.join(TMP, "slip_log.py"))
if os.path.exists(os.path.join(LIB, "slip_adjust.py")):
    shutil.copy(os.path.join(LIB, "slip_adjust.py"), os.path.join(TMP, "slip_adjust.py"))
DB = os.path.join(TMP, "f.db")
os.environ["SLIP_NOW"] = "2026-10-26 12:00:00"
k0 = sqlite3.connect(DB)
k0.executescript("""
CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT, phone_last4 TEXT, merged_into TEXT);
INSERT INTO patient_ref(clinic_id, name, phone_last4) VALUES ('9001','Asha Test','0001'),('9002','Bina Test','0002'),('9003','Chetan Test','0003');
CREATE TABLE clinic_day_line (business_date TEXT, section TEXT, sn INTEGER, patient TEXT, clinic_id TEXT, amount_p INTEGER, mode TEXT, shift TEXT, gateway_ref TEXT);
CREATE TABLE owner_service (id INTEGER PRIMARY KEY, kind TEXT, name TEXT, price_p INTEGER, active INTEGER DEFAULT 1, note TEXT, created_by TEXT, created_ts TEXT, updated_by TEXT, updated_ts TEXT, code TEXT, status TEXT DEFAULT 'approved', seen INTEGER, grp TEXT, forms TEXT, source TEXT, side TEXT);
INSERT INTO owner_service(id, kind, name, price_p, side) VALUES (1,'xray','Knee AP & Lateral view',50000,'ask'),(2,'xray','Lumbosacral spine AP & Lateral view',50000,''),(61,'proc','ILI KNEE',50000,'');
CREATE TABLE audit_log (id INTEGER PRIMARY KEY, table_name TEXT, row_id INTEGER, action TEXT, before_json TEXT, after_json TEXT, by_whom TEXT, at TEXT);
""")
k0.commit()
k0.close()
sys.path.insert(0, TMP)
from flask import Flask                                                 # noqa: E402

SL = importlib.import_module("slip_log")
USER = {"user": "shavez", "role": "manager", "roles": ["maker", "checker"]}


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def require(*roles, unit="slips"):
    return dict(USER), None


def audit(con, table, row_id, action, before=None, after=None, who=""):
    con.execute("INSERT INTO audit_log(table_name,row_id,action,before_json,after_json,by_whom,at) VALUES(?,?,?,?,?,?,?)",
                (table, row_id, action, json.dumps(before), json.dumps(after), who, "x"))


app = Flask("walk")
app.testing = True
SL.init(app, db, require, audit, unit="slips")
c = app.test_client()
RES = []


def check(tag, name, ok, detail=""):
    RES.append((tag, name, bool(ok)))
    print("%s  [%s] %s%s" % ("GREEN" if ok else "RED  ", tag, name, ("  -- " + str(detail)[:200]) if (detail and not ok) else ""))


def q(sql, *a):
    k = db()
    try:
        return [dict(r) for r in k.execute(sql, a)]
    finally:
        k.close()


def j(path, body):
    r = c.post(path, data=json.dumps(body), content_type="application/json")
    try:
        return r.status_code, json.loads(r.get_data(as_text=True) or "{}")
    except ValueError:
        return r.status_code, {}


T = "S667"
k = db(); SL.ensure(k); k.close()
c.post("/finance/slips/book", data={"series": "xp", "first_no": "1401", "last_no": "1800", "start_no": "1418"})
c.post("/finance/slips/book", data={"series": "opd", "first_no": "19601", "last_no": "20000", "start_no": "19855"})
r = c.get("/finance/slips/desk")
check("older", "the desk opens on 26-Oct", r.status_code == 200 and b'"day": "2026-10-26"' in r.data, r.status_code)
st, d = j("/finance/slips/desk/api/save", {"series": "opd", "slip_no": 19855, "clinic_id": "9001", "day": "2026-10-26", "today_pick": True})
check("older", "on 26-Oct an 'Aaj' OPD save files under 26-Oct", d.get("ok") is True and q("SELECT day FROM slip WHERE slip_no=19855")[0]["day"] == "2026-10-26", d)
# ---- the night passes; the page still says 26-Oct
os.environ["SLIP_NOW"] = "2026-10-27 11:26:14"
st, d = j("/finance/slips/desk/api/save", {"series": "opd", "slip_no": 19856, "clinic_id": "9002", "day": "2026-10-26", "today_pick": True})
check(T, "27-Oct: an OPD save from the stale 'Aaj' (day 26-Oct) is refused, nothing saved", d.get("ok") is False and not q("SELECT 1 FROM slip WHERE slip_no=19856"), d)
check(T, "...the refusal names the old day (26-Oct) and Aaj, and carries today's state (day 27-Oct)",
      "26-Oct par" in (d.get("err") or "") and "Aaj" in (d.get("err") or "") and (d.get("state") or {}).get("day") == "2026-10-27" and (d.get("state") or {}).get("today") == "2026-10-27", d)
st, d = j("/finance/slips/desk/api/save", {"series": "xp", "slip_no": 1418, "clinic_id": "9002", "day": "2026-10-26", "today_pick": True,
                                           "items": [{"k": "xray", "id": 1, "side": "R"}]})
check(T, "27-Oct: an X-ray save from the stale 'Aaj' is refused, nothing saved", d.get("ok") is False and not q("SELECT 1 FROM slip WHERE series='xp'"), d)
st, d = j("/finance/slips/desk/api/save", {"series": "xp", "slip_no": 1419, "clinic_id": "9002", "day": "2026-10-27", "today_pick": True,
                                           "items": [{"k": "xray", "id": 1, "side": "R"}]})
check("older", "an X-ray save on today's 'Aaj' (1419) saves under 27-Oct",
      d.get("ok") is True and q("SELECT day FROM slip WHERE series='xp' AND slip_no=1419")[0]["day"] == "2026-10-27", d)
st, d = j("/finance/slips/desk/api/save", {"series": "opd", "slip_no": 19860, "clinic_id": "9002", "day": "2026-10-26", "today_pick": False})
check("older", "a DELIBERATE late entry (Kal chosen) still files under 26-Oct", d.get("ok") is True and
      q("SELECT day FROM slip WHERE slip_no=19860")[0]["day"] == "2026-10-26", d)
st, d = j("/finance/slips/desk/api/save", {"series": "opd", "slip_no": 19861, "clinic_id": "9003", "day": "2026-10-26"})
check(T, "a desk opened before the kit (no today_pick) saving for 26-Oct is refused: press F5", d.get("ok") is False and
      "F5" in (d.get("err") or "") and not q("SELECT 1 FROM slip WHERE slip_no=19861"), d)
st, d = j("/finance/slips/desk/api/save", {"series": "opd", "slip_no": 19862, "clinic_id": "9003", "day": "2026-10-27"})
check("older", "...the same old page saving for today still saves", d.get("ok") is True and
      q("SELECT day FROM slip WHERE slip_no=19862")[0]["day"] == "2026-10-27", d)
st, d = j("/finance/slips/desk/api/state", {})
r = c.get("/finance/slips/desk/api/state?day=2026-10-26")
sd = json.loads(r.get_data(as_text=True))["state"]
check("older", "the state door answers for 26-Oct with today = 27-Oct", sd["day"] == "2026-10-26" and sd["today"] == "2026-10-27", sd.get("today"))
page = c.get("/finance/slips/desk").get_data(as_text=True)
check(T, "the page: both saves send today_pick; fillDays and the draw() move are in",
      page.count("today_pick:onToday") == 2 and "function fillDays(" in page and "if(onToday&&st.today&&st.today>day)" in page)
check(T, "the page: a refused save draws the state it carries (both sections)", page.count("msg(false,r.err);if(r.state)draw(r.state);") == 2)
if PAGE:
    os.environ["SLIP_NOW"] = "2026-10-26 12:00:00"
    open(PAGE, "w", encoding="utf-8").write(c.get("/finance/slips/desk").get_data(as_text=True))
# ---- the data step, on made-up rows shaped as this morning's
k = db()
k.execute("INSERT INTO slip(series, slip_no, day, clinic_id, state, logged_by, logged_at, updated_by, updated_at) VALUES ('opd',19858,'2026-10-26','9001','ok','shavez','2026-10-27 11:26:14','shavez','2026-10-27 11:26:14')")
k.execute("INSERT INTO slip(series, slip_no, day, clinic_id, state, logged_by, logged_at, updated_by, updated_at) VALUES ('xp',1420,'2026-10-26','9001','ok','shavez','2026-10-27 11:26:28','shavez','2026-10-27 11:26:28')")
k.commit(); k.close()
fx = os.path.join(KDIR, "fix_s667_day.py")
k = db(); k.execute("INSERT INTO slip(series, slip_no, day, clinic_id, state, logged_by, logged_at, updated_by, updated_at) VALUES ('opd',19870,'2026-10-26','9002','ok','shavez','2026-10-27 11:40:00','shavez','2026-10-27 11:40:00')"); k.commit(); k.close()
p0 = subprocess.run([sys.executable, "-I", fx, DB, "--dry", "--lib", TMP], capture_output=True, text=True); o = p0.stdout
check("data", "the data step DRY says both would move (rc 0), names the other row typed today (not moved), moves nothing", p0.returncode == 0 and "moved 2 (DRY" in o and "opd 19870" in o and
      q("SELECT COUNT(*) n FROM slip WHERE slip_no IN (19858,1420) AND day='2026-10-26'")[0]["n"] == 2, o)
o = subprocess.run([sys.executable, "-I", fx, DB, "--lib", TMP], capture_output=True, text=True).stdout
check("data", "the data step moves OPD 19858 and X-ray 1420 to 27-Oct, one audit row each", "moved 2" in o and
      q("SELECT COUNT(*) n FROM slip WHERE slip_no IN (19858,1420) AND day='2026-10-27'")[0]["n"] == 2 and
      q("SELECT COUNT(*) n FROM audit_log WHERE action='slip_day_move'")[0]["n"] == 2, o)
p2 = subprocess.run([sys.executable, "-I", fx, DB, "--lib", TMP], capture_output=True, text=True); o = p2.stdout
check("data", "run again: nothing to move (rc 0); the near-miss row typed 11:40 is left on 26-Oct", p2.returncode == 0 and "moved 0" in o and "already on 2026-10-27" in o and
      q("SELECT day FROM slip WHERE slip_no=19870")[0]["day"] == "2026-10-26", o)
check("data", "the deliberate late entry stays on 26-Oct", q("SELECT COUNT(*) n FROM slip WHERE slip_no=19860 AND day='2026-10-26'")[0]["n"] == 1)
s6 = sum(1 for t, _n, ok in RES if t == T and not ok)
older = sum(1 for t, _n, ok in RES if t != T and not ok)
g = sum(1 for _t, _n, ok in RES if ok)
shutil.rmtree(TMP, ignore_errors=True)
print("%d S667 check(s) red · %d older red · %d green" % (s6, older, g) if OLD else "%d of %d green" % (g, len(RES)))
