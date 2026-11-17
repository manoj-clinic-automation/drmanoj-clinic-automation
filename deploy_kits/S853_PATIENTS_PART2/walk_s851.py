#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s851.py -- kit S851_PATIENTS_PAGE (S474, 17-Nov-2026). A walk on a MADE-UP root: made-up patients, no real number.

    python walk_s851.py <code_dir> <bundle_finance_dir> <schema_db> <work_dir>

<code_dir>   the files under test (the built patients_page.py + .html + owner_console.py; or the live files for the CONTROL)
<bundle_finance_dir>  the newest bundle's /root/finance (every other module)
<schema_db>  an EMPTY database carrying the live schema only
Prints one line per check and a last line "WALK n/m". Exit 0 only when every check passes.
"""
import hashlib
import importlib
import json
import os
import shutil
import sqlite3
import stat
import sys

CODE, BUNDLE, SCHEMA, WORK = sys.argv[1:5]
# the kit folder carries the new files too: keep it off the import path, so the CONTROL reads only what it is given
try:
    _ME = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _ME = None
sys.path[:] = [p for p in sys.path if not _ME or os.path.abspath(p or ".") != _ME]
sys.path[:0] = [CODE, BUNDLE]
os.makedirs(WORK, exist_ok=True)
DB = os.path.join(WORK, "walk.db")
shutil.copyfile(SCHEMA, DB)
os.environ["PATIENTS_READING"] = os.path.join(WORK, "patients_reading.dat")
RES = []


def ok(name, cond, extra=""):
    RES.append(bool(cond))
    print("%s  %s%s" % ("PASS" if cond else "FAIL", name, ("  -- " + str(extra)[:300]) if extra else ""))


ID = {k: str(7000 + k) for k in range(0, 12)}            # made-up clinic IDs
UID = {k: "walk-uid-%d" % k for k in range(0, 12)}
UNC = "Other / Unclassified"


def seed():
    c = sqlite3.connect(DB)
    vid = [0]

    def visit(k, day):
        vid[0] += 1
        c.execute("INSERT INTO patient_visit (visit_id, visit_date, clinic_id, patient_uid) VALUES (?,?,?,?)", (vid[0], day, ID[k], UID[k]))

    def dxr(k, day, cat, fu="", std=None):
        c.execute("INSERT INTO dx_visit (patient_uid, visit_date, clinic_id, diagnosis_raw, std_dx, category, follow_up_date, updated_at) "
                  "VALUES (?,?,?,?,?,?,?,?)", (UID[k], day, ID[k], "WALK ODD WORD" if std == UNC else "walk dx", std or cat or "", cat, fu, day))

    def line(day, k, sec, amt, sn):
        c.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode) VALUES (?,?,?,?,?,?,?)",
                  (day, sec, sn, "WALK %d" % k, ID[k], amt, "Cash"))
    # P1: seen in June, back 10-Jul after 38 days (a late return), again 12-Jul (a free revisit) = the review of 25-Jul kept early
    visit(1, "2026-06-02"); visit(1, "2026-07-10"); visit(1, "2026-07-12")
    dxr(1, "2026-07-10", "Rheumatology", "2026-07-25")
    line("2026-07-10", 1, "consult", 50000, 1); line("2026-07-12", 1, "revisit", 0, 2)
    # P2: new 1-Jul (Trauma, back in a week = 8-Jul); came 20-Jul = 12 days late
    visit(2, "2026-07-01"); visit(2, "2026-07-20")
    dxr(2, "2026-07-01", "Trauma", "2026-07-08")
    line("2026-07-01", 2, "consult", 50000, 3); line("2026-07-01", 2, "xray", 30000, 4)
    # P3: new 2-Jul with NO diagnosis typed (carries DJD from 5-Aug); review due 20-Aug not kept, medicines bought 25-Aug -> "on medicines"
    visit(3, "2026-07-02"); visit(3, "2026-08-05")
    dxr(3, "2026-07-02", ""); dxr(3, "2026-08-05", "Degenerative Joint Disease", "2026-08-20")
    line("2026-08-05", 3, "proc", 100000, 5)
    # P4: new 3-Jul, Mechanical Spine, review due 31-Jul, never came; an UNVERIFIED low-confidence bill must not count -> "neither"
    visit(4, "2026-07-03"); dxr(4, "2026-07-03", "Mechanical Spine", "2026-07-31")
    # P5: new 3-Jul, no diagnosis anywhere; a DISPUTED bill must not count
    visit(5, "2026-07-03")
    # P6: 10-Nov, Foot & Ankle, back in 4 days = 14-Nov -> still open
    visit(6, "2026-11-10"); dxr(6, "2026-11-10", "Foot & Ankle", "2026-11-14")
    # P7: 12-Nov, a word the taxonomy does not know -> Other groups and the words list
    visit(7, "2026-11-12"); dxr(7, "2026-11-12", "Unclassified", std=UNC)
    # P8: 12-Nov, no diagnosis -> the last open day's "none"
    visit(8, "2026-11-12")
    # Sanjeevni: patient refs and bills
    pr = {}
    for k in (3, 4, 5):
        cur = c.execute("INSERT INTO patient_ref (clinic_id, name) VALUES (?,?)", (ID[k], "WALK PATIENT %d" % k))
        pr[k] = cur.lastrowid
    for k in (1, 2, 6, 7, 8):
        c.execute("INSERT INTO patient_ref (clinic_id, name) VALUES (?,?)", (ID[k], "WALK PATIENT %d" % k))

    def bill(k, day, amt, conf, ver, no):
        cur = c.execute("INSERT INTO day_entry (unit, business_date) VALUES ('medical',?)", (day,))
        c.execute("INSERT INTO sale_item (day_entry_id, unit, patient_ref_id, service, amount_p, source, source_ref, confidence, verified_by) "
                  "VALUES (?,?,?,?,?,?,?,?,?)", (cur.lastrowid, "medical", pr[k], "pharmacy", amt, "ocr", no, conf, ver))
    bill(3, "2026-08-25", 120000, 0.99, None, "W-1")          # tied (confidence) -> counts
    bill(4, "2026-08-01", 90000, 0.90, None, "W-2")           # not verified, low confidence -> never counted
    bill(5, "2026-07-15", 80000, 1.0, "walk", "W-3")          # verified but DISPUTED -> never counted
    c.execute("INSERT INTO identity_dispute (unit, business_date, bill_no, clinic_id, status, noted_at) VALUES ('medical','2026-07-15','W-3',?, 'open','x')", (ID[5],))
    c.commit()
    c.close()


seed()
md5_before = hashlib.md5(open(DB, "rb").read()).hexdigest()
try:
    PP = importlib.import_module("patients_page")
except Exception as ex:                                       # noqa: BLE001
    PP = None
    print("patients_page not importable: %s" % ex)

con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
try:
    r, L = PP.read(con) if PP else ({}, {})
except Exception as ex:                                       # noqa: BLE001
    r, L = {}, {}
    print("read() failed: %s" % ex)
row = {x["ym"]: x for x in r.get("rows", [])}
fu = {(f["ym"], f["kind"]): f for f in r.get("fu", [])}
J = row.get("2026-07", {})

# ---------------------------------------------------------------- the month
ok("months run Jul..Nov (June left out)", [m["ym"] for m in r.get("months", [])] == ["2026-07", "2026-08", "2026-09", "2026-10", "2026-11"], [m.get("ym") for m in r.get("months", [])])
ok("July: 5 patients, 4 new (new = an ID above every earlier day's)", J.get("patients") == 5 and J.get("new") == 4, (J.get("patients"), J.get("new")))
ok("July: 7 visits, 1 free revisit", J.get("visits") == 7 and J.get("revisits") == 1, (J.get("visits"), J.get("revisits")))
ok("July money: consultation 1,000 + X-ray 300 = 1,300; August procedure 1,000",
   J.get("consult") == 100000 and J.get("xray") == 30000 and J.get("total") == 130000 and row.get("2026-08", {}).get("proc") == 100000)
ok("medicines without a visit: Aug 1 (the tied bill), Jul 0 (the disputed one never counts)",
   row.get("2026-08", {}).get("med") == 1 and J.get("med") == 0, (row.get("2026-08", {}).get("med"), J.get("med")))
ok("an unverified low-confidence bill never counts (no medicines in Aug for that patient)",
   all(x[0] != ID[4] for x in L.get("m:2026-08:med", [])))
ok("November is marked 'so far'", row.get("2026-11", {}).get("partial") is True)

# ---------------------------------------------------------------- follow-ups
fr = fu.get(("2026-07", "review"), {})
ok("July planned reviews: 2 due, 1 kept (an early visit counts), 1 neither", fr.get("due") == 2 and fr.get("kept") == 1 and fr.get("neither") == 1, fr)
ok("a base under 20 shows the count, not a percentage ('1 of 2')", fr.get("kept_pct") == "1 of 2", fr.get("kept_pct"))
fs = fu.get(("2026-07", "short"), {})
ok("July within-a-week: the late one", fs.get("late") == 1 and fs.get("due") == 1, fs)
ok("the late one's note says how late (12 days)", any("12 days" in x[2] for x in L.get("fu:2026-07:short:late", [])), L.get("fu:2026-07:short:late"))
ok("August review: on medicines (bought 5 days after the date, no visit)", fu.get(("2026-08", "review"), {}).get("med") == 1)
ok("November: the open one", fu.get(("2026-11", "short"), {}).get("open") == 1)

# ---------------------------------------------------------------- groups, carried diagnosis, late returners, coverage
gj = {x["name"]: x for x in r.get("groups", {}).get("2026-07", {}).get("rows", [])}
ok("July groups: Rheumatology 1, Trauma 1, DJD 1 (carried from a later visit), Mechanical 1, none 1",
   [gj.get(g, {}).get("p") for g in ("Rheumatology", "Trauma", "Degenerative Joint Disease", "Mechanical Spine", "No diagnosis typed")] == [1, 1, 1, 1, 1])
ok("August pharmacy rupees go to the patient's group (DJD 1,200)", next((x["pp"] for x in r.get("groups", {}).get("2026-08", {}).get("rows", []) if x["name"] == "Degenerative Joint Disease"), None) == 120000)
lj = r.get("late", {}).get("2026-07", {})
ok("July late returner: 1 (Rheumatology, 38 days -> 1-2 months)", lj.get("total", {}).get("t") == 1 and lj.get("total", {}).get("a") == 1, lj.get("total"))
cj = r.get("cov", {}).get("2026-07", {})
ok("July coverage: own 3, carried 3, none 1", (cj.get("own"), cj.get("carried"), cj.get("none")) == (3, 3, 1), cj)
ok("last open day: 1 visit with no diagnosis", r.get("lastday_none") == 1 and r.get("lastday") == "2026-11-12")
ok("the unknown word is listed (1 word, 1 visit)", (r.get("words") or {}).get("n") == 1 and (r.get("words") or {}).get("top", [{}])[0].get("word") == "WALK ODD WORD", r.get("words"))

# ---------------------------------------------------------------- the words: fixed rules
r2, _L2 = PP.read(con) if PP else ({}, {})
ok("readings are the same for the same figures (read twice)", r.get("readings") == r2.get("readings") and bool(r.get("readings", {}).get("2026-08")))
ok("every reading has a head and a text; suggestions never empty where a list exists",
   all(s.get("head") and s.get("text") for v in r.get("readings", {}).values() for s in v))
ok("the reading carries no patient name or clinic ID", not any(ID[k] in json.dumps(r) for k in range(1, 9)) and "WALK PATIENT" not in json.dumps(r))
con.close()

# ---------------------------------------------------------------- build: read-only, the file
rd = PP.build(DB, os.environ["PATIENTS_READING"]) if PP else {}
ok("build leaves finance.db byte-identical (read-only)", hashlib.md5(open(DB, "rb").read()).hexdigest() == md5_before)
st = os.stat(os.environ["PATIENTS_READING"]) if os.path.exists(os.environ["PATIENTS_READING"]) else None
ok("the reading file is written, owner-only (600)", st is not None and stat.S_IMODE(st.st_mode) == 0o600)

# ---------------------------------------------------------------- the pages through Flask
from flask import Flask                                         # noqa: E402

USER = {"deny": False}


def req(*a, **k):
    return (None, ("denied", 403)) if USER["deny"] else ({"user": "manoj"}, None)


CONN = sqlite3.connect(DB, check_same_thread=False)
app = Flask("walk_s851")
try:
    oc = importlib.import_module("owner_console")
    oc.init(app, lambda: CONN, req, "packs")
except Exception as ex:                                       # noqa: BLE001
    print("owner_console.init failed: %s" % ex)
rules = [x.rule for x in app.url_map.iter_rules()]
ok("owner_console mounts the Patients page and its two doors",
   all(u in rules for u in ("/finance/console/patients", "/finance/console/api/patients", "/finance/console/api/patients/list")))
src = open(os.path.join(CODE, "owner_console.py"), encoding="utf-8").read()
ok("the console's month section carries the line to the page", "/finance/console/patients" in src and "S851" in src)
cl = app.test_client()
p = cl.get("/finance/console/patients")
ok("the page answers 200 for him", p.status_code == 200 and "Patients" in p.get_data(as_text=True), p.status_code)
a = cl.get("/finance/console/api/patients").get_json(silent=True) or {}
ok("the reading answers ok with the months", a.get("ok") and len((a.get("reading") or {}).get("months", [])) == 5)
li = cl.get("/finance/console/api/patients/list?key=fu:2026-07:short:late").get_json(silent=True) or {}
ok("a tap lists the patient by name and clinic ID", li.get("ok") and (li.get("rows") or [{}])[0].get("name") == "WALK PATIENT 2" and (li.get("rows") or [{}])[0].get("cid") == ID[2], li)
li2 = cl.get("/finance/console/api/patients/list?key=nonsense").get_json(silent=True) or {}
ok("an unknown list key says so (no crash)", li2.get("ok") is False and "not in the reading" in (li2.get("why") or ""))
USER["deny"] = True
ok("page refused without his gate (403)", cl.get("/finance/console/patients").status_code == 403)
dl = cl.get("/finance/console/api/patients/list?key=fu:2026-07:short:late")
ok("the list refused without his gate (no name)", "WALK PATIENT" not in dl.get_data(as_text=True))
USER["deny"] = False
# a build that fails leaves the older reading standing and says why
if PP:
    old = PP._db_path
    PP._db_path = lambda c: "/nonexistent/finance.db"
    _j = json.load(open(os.environ["PATIENTS_READING"], encoding="utf-8"))
    _j["built_epoch"] = 0                                     # an old reading
    json.dump(_j, open(os.environ["PATIENTS_READING"], "w", encoding="utf-8"))
    s, why = PP.fresh(CONN, True)
    PP._db_path = old
    ok("a failed build keeps the older reading and says why", s is not None and bool(why), why)
    open(PP.LOCK, "w").write("x")
    s, why = PP.fresh(CONN, True)
    ok("a build already running (lock held) returns the stored reading, no second build", s is not None and why == "")
    os.unlink(PP.LOCK)
else:
    ok("a failed build keeps the older reading and says why", False)
    ok("a build already running (lock held) returns the stored reading, no second build", False)
print("WALK %d/%d" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
