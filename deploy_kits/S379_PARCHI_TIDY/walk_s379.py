#!/usr/bin/env python3
"""walk_s379.py -- kit S379_PARCHI_TIDY.
PART A -- the day statement: a synthetic finance.db (S372's shape) whose Docterz order is NOT the slip order, a
cancelled number, a number never written, a gap back to the day before; the page and the PDF through the real modules.
PART B -- the Parchi tile on a SCRATCH COPY of the real finance.db, on the walk's own day (SLIP_NOW 2001-01-05) and
IDs (9091xx): the Docterz upload screen gone, the blood questions on Blood test, a procedure discount saved and used
by the match, a new patient's name filled from the Docterz lines, the six X-rays on the list.
The LIVE modules are the negative control. Prints IDs and counts only.
Usage: FINANCE_DB=<scratch copy> python3 walk_s379.py <dir with the kit's 4 modules + add_xrays_s379.py> <dir with the LIVE 4>"""
import importlib.util, os, re, sqlite3, subprocess, sys, tempfile
new_dir, live_dir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
N = [0]
def ok(c, label, got=None):
    N[0] += 1
    if not c:
        print("WALK RED %d: %s %s" % (N[0], label, "" if got is None else got)); sys.exit(1)
def load(path, name):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
from flask import Flask

# ================================================================ PART A -- the day statement
tmp = tempfile.mkdtemp(prefix="s379walk_"); dbp = os.path.join(tmp, "f.db")
con = sqlite3.connect(dbp)
con.executescript("""
CREATE TABLE clinic_day_revenue(business_date TEXT PRIMARY KEY, source_file TEXT, source_id TEXT, source_mtime TEXT, taken_at TEXT,
 cons_count INT, cons_amount_p INT, xray_count INT, xray_amount_p INT, proc_count INT, proc_amount_p INT, total_count INT, total_amount_p INT,
 morning INT, evening INT, free_revisits INT, free_concession INT, f93_phantom_rows INT, tender_json TEXT, sheet_total_p INT, sheet_cash_p INT, sheet_online_p INT, variance_note TEXT);
CREATE TABLE clinic_day_line(business_date TEXT, section TEXT, sn INT, patient TEXT, clinic_id TEXT, amount_p INT, mode TEXT, shift TEXT, gateway_ref TEXT);
CREATE TABLE clinic_day_tender(business_date TEXT, clinic_id TEXT, invoice_no TEXT, tender TEXT, amount_p INT, source_file TEXT);
CREATE TABLE slip(id INTEGER PRIMARY KEY, series TEXT, slip_no INT, day TEXT, clinic_id TEXT, no_id_name TEXT, is_new INT, name_seen TEXT, state TEXT, note TEXT,
 paid_mode TEXT, paid_by TEXT, paid_at TEXT, done_by TEXT, done_at TEXT, logged_by TEXT, logged_at TEXT, updated_by TEXT, updated_at TEXT);
""")
D = "2026-09-21"
con.execute("INSERT INTO clinic_day_revenue(business_date,cons_count,cons_amount_p,xray_count,xray_amount_p,proc_count,proc_amount_p,total_count,total_amount_p,morning,evening,free_revisits,free_concession,tender_json) VALUES(?,4,120000,2,80000,0,0,6,200000,4,2,0,0,'{}')", (D,))
con.executemany("INSERT INTO clinic_day_line VALUES(?,?,?,?,?,?,?,?,?)", [          # Docterz order != slip order
    (D, "consult", 1, "PERSON C", "1203", 30000, "Cash", "Morning", ""), (D, "consult", 2, "PERSON A", "1201", 30000, "Cash", "Morning", ""),
    (D, "consult", 3, "NO SLIP", "1299", 30000, "Cash", "Morning", ""), (D, "consult", 4, "PERSON B", "1202", 30000, "Cash", "Evening", ""),
    (D, "xray", 1, "PERSON B", "1202", 40000, "Cash", "Evening", ""), (D, "xray", 2, "PERSON A", "1201", 40000, "Cash", "Morning", "")])
con.executemany("INSERT INTO slip(series,slip_no,day,clinic_id,state) VALUES(?,?,?,?,?)", [
    ("opd", 19297, "2026-09-19", "1100", "ok"),                          # the day before ends at 19297 -> 19298 never written
    ("opd", 19299, D, "1201", "ok"), ("opd", 19300, D, "", "cancelled"), ("opd", 19301, D, "1202", "ok"),
    ("opd", 19303, D, "1203", "ok"),                                     # 19302 never written
    ("xp", 1501, D, "1201", "ok"), ("xp", 1502, D, "1202", "ok")])
con.commit(); con.close()

def build(d, tag):
    sys.path.insert(0, d)
    for m in ("slip_lookup",):
        sys.modules.pop(m, None)
    app = Flask("walk" + tag)
    def dbg():
        c = sqlite3.connect(dbp); c.row_factory = sqlite3.Row; return c
    def req(*roles, **kw):
        return ({"user": "manoj", "roles": ["checker"]}, None)
    day = load(os.path.join(d, "finance_clinic_day.py"), "fcd" + tag); day.init(app, dbg, req)
    pdf = load(os.path.join(d, "clinic_day_pdf.py"), "cdp" + tag); pdf.init(app, dbg, req)
    sys.path.remove(d)
    return app, day, pdf
app, day, pdf = build(new_dir, "new")
h = app.test_client().get("/finance/clinic/day/" + D).get_data(as_text=True)
cons = re.findall(r"<td class='n slip'>(\d*)</td><td class='n sn'>\d+</td><td class='p'>([^<]*)</td>", h)
ok([x[0] for x in cons[:4]] == ["19299", "19301", "19303", ""], "page: consultations in slip order, the one with no slip last", cons[:4])
ok([x[0] for x in cons[4:6]] == ["1501", "1502"], "page: X-rays in slip order", cons[4:6])
ok("Slip books" in h and "19298 (not written)" in h and "19300 (cancelled)" in h and "19302 (not written)" in h,
   "page: every skipped OPD number named with its reason, back to the day before's last")
ok("X-ray &amp; Proc book: slips 1501–1502 · 2 written · no number skipped" in h, "page: a book with no gap says so")
cc = sqlite3.connect(dbp); cc.row_factory = sqlite3.Row
d = pdf.day_data(cc, D)
body = pdf.render_pdf(d, who="manoj")
ok(body[:4] == b"%PDF" and b"19298 \\(not written\\)" in body and b"19300 \\(cancelled\\)" in body, "pdf: the skipped line is on the PDF")
ok([r["clinic_id"] for r in d["sections"][0][1]] == ["1201", "1202", "1203", "1299"], "pdf: the same slip order",
   [r["clinic_id"] for r in d["sections"][0][1]])
ok(app.test_client().get("/finance/clinic/day/2026-09-20").status_code == 200, "page: a day with no slips still renders")
app0, day0, pdf0 = build(live_dir, "old")
h0 = app0.test_client().get("/finance/clinic/day/" + D).get_data(as_text=True)
ok("Slip books" not in h0 and re.findall(r"<td class='n slip'>(\d*)</td>", h0)[0] == "19303", "negative control: the live page runs in Docterz order")
ok({r.rule for r in app0.url_map.iter_rules()} == {r.rule for r in app.url_map.iter_rules()}, "day pages: routes identical")

# ================================================================ PART B -- the Parchi tile, on a scratch copy of the real db
dbr = os.environ["FINANCE_DB"]
assert "walk" in dbr or "scratch" in dbr or dbr.startswith("/tmp"), "refusing a non-scratch database"
WD = "2001-01-05"
os.environ["SLIP_NOW"] = WD + "T11:00:00"
out = subprocess.run([sys.executable, "-B", os.path.join(new_dir, "add_xrays_s379.py"), dbr], stdout=subprocess.PIPE, text=True).stdout
ok("XRAYS_S379 OK: 6 added" in out or "XRAYS_S379 OK: 0 added" in out, "six X-rays onto the rate page (or already there)", out[-200:])
out2 = subprocess.run([sys.executable, "-B", os.path.join(new_dir, "add_xrays_s379.py"), dbr], stdout=subprocess.PIPE, text=True).stdout
ok("XRAYS_S379 OK: 0 added" in out2, "run twice: nothing doubled")
USER = {"u": {"user": "shavez", "roles": ["maker"]}}
def app_for(d, tag):
    m = load(os.path.join(d, "slip_log.py"), "slip_log_" + tag)
    a = Flask("slip" + tag)
    def dbg():
        c = sqlite3.connect(dbr); c.row_factory = sqlite3.Row; return c
    def req(*roles, **kw):
        return (USER["u"], None)
    m.init(a, dbg, req)
    return a, m
A, S = app_for(new_dir, "new")
c = A.test_client()
menu = c.get("/finance/slips").get_data(as_text=True)
ok("Docterz upload" not in menu and "/finance/slips/emr" not in menu and "Blood test" in menu, "menu: the Docterz upload screen is gone, Blood test stays")
r = c.get("/finance/slips/emr")
ok(r.status_code == 303 and r.headers["Location"].endswith("/finance/slips/blood"), "the old address sends staff to Blood test")
ok(c.get("/finance/slips/blood").status_code == 200, "Blood test page renders")
xpf = c.get("/finance/slips?s=xp").get_data(as_text=True)
ok("Humerus (arm) AP &amp; Lateral view" in xpf and "Foot AP &amp; Oblique view" in xpf and "Both knees AP standing view · ₹300" in xpf,
   "X-ray list: the new studies are there with his prices")
ok('name="proc0_disc"' in xpf and 'name="xray0_disc"' not in xpf, "a discount box beside each procedure, none beside X-rays")
con = sqlite3.connect(dbr); con.row_factory = sqlite3.Row
S.ensure(con)
proc = con.execute("SELECT id, price_p FROM owner_service WHERE kind='proc' AND active=1 AND status<>'rejected' AND price_p>0 ORDER BY id LIMIT 1").fetchone()
xr = con.execute("SELECT id, price_p FROM owner_service WHERE kind='xray' AND name='Humerus (arm) AP & Lateral view'").fetchone()
nxp, nop = S.next_no(con, "xp"), S.next_no(con, "opd")
ok(nxp and nop, "both books prompt a number")
def save(**f):
    return c.post("/finance/slips/save", data=f)
r = save(series="xp", sec="xp", slip_no=str(nxp), clinic_id="909101", id_ok="1", xray0=str(xr["id"]), xray0_side="R",
         proc0=str(proc["id"]), proc0_disc=str(proc["price_p"] // 100 + 50))
ok("zyada nahi" in (r.headers.get("Location") or "") or "zyada%20nahi" in (r.headers.get("Location") or ""), "a discount above the rate is refused")
r = save(series="xp", sec="xp", slip_no=str(nxp), clinic_id="909101", id_ok="1", xray0=str(xr["id"]), xray0_side="R",
         proc0=str(proc["id"]), proc0_disc="abc")
ok("rupaye" in (r.headers.get("Location") or ""), "a discount that is not a number is refused")
r = save(series="xp", sec="xp", slip_no=str(nxp), clinic_id="909101", id_ok="1", xray0=str(xr["id"]), xray0_side="R",
         proc0=str(proc["id"]), proc0_disc="100")
ok(r.status_code == 303 and "save%20ho%20gayi" in r.headers["Location"], "the slip with a Rs 100 discount is saved", r.headers.get("Location"))
sid = con.execute("SELECT id FROM slip WHERE series='xp' AND slip_no=?", (nxp,)).fetchone()["id"]
its = {i["kind"]: dict(i) for i in con.execute("SELECT * FROM slip_item WHERE slip_id=?", (sid,))}
ok(its["proc"]["discount_p"] == 10000 and its["xray"]["discount_p"] == 0 and its["xray"]["price_p"] == 50000, "stored: Rs 100 off the procedure, the X-ray at Rs 500")
room = c.get("/finance/slips?s=room").get_data(as_text=True)
ok("chhoot ₹100" in room and S._rs(50000 + proc["price_p"] - 10000) in room, "the room sees the discount and the amount after it")
r = save(series="opd", sec="opd", slip_no=str(nop), clinic_id="909102", id_ok="1")
ok(r.status_code == 303, "an OPD slip for a new patient")
lst = c.get("/finance/slips?s=list").get_data(as_text=True)
ok("909102 · naya" in lst, "before the Docterz report: the ID and 'naya' only")
con.executemany("INSERT INTO clinic_day_line(business_date, section, sn, patient, clinic_id, amount_p, mode, shift) VALUES (?,?,?,?,?,?,?,?)", [
    (WD, "consult", 1, "WALK NEWNAME", "909102", 50000, "Cash", "Morning"),
    (WD, "xray", 1, "WALK XRAYNAME", "909101", 50000, "Cash", "Morning"),
    (WD, "proc", 1, "WALK XRAYNAME", "909101", proc["price_p"] - 10000, "Cash", "Morning")])
con.execute("INSERT OR REPLACE INTO clinic_day_revenue(business_date, source_file, source_id, source_mtime, taken_at, cons_count, "
            "cons_amount_p, xray_count, xray_amount_p, proc_count, proc_amount_p, total_count, total_amount_p, free_revisits, "
            "free_concession, f93_phantom_rows, tender_json) VALUES (?,'walk','walk','',?,1,50000,1,50000,1,0,3,0,0,0,0,'{}')",
            (WD, WD + " 22:00"))
con.commit()
lst = c.get("/finance/slips?s=list").get_data(as_text=True)
ok("909102 · WALK NEWNAME · naya" in lst and "909101 · WALK XRAYNAME · naya" in lst, "after the Docterz report: the new patients carry their names")
ok(con.execute("SELECT name_seen FROM slip WHERE series='opd' AND slip_no=?", (nop,)).fetchone()[0] == "WALK NEWNAME", "the name is written into the slip once")
m = S.match_day(con, WD)
ok(not [f for f in m["flags"] if "procedure:" in f], "the match: Docterz billed the rate less the discount -> no procedure flag", m["flags"])
con.execute("UPDATE clinic_day_line SET amount_p=? WHERE business_date=? AND section='proc'", (proc["price_p"], WD)); con.commit()
m = S.match_day(con, WD)
ok([f for f in m["flags"] if "after ₹100 discount" in f], "the match: Docterz billed the full rate -> flagged, the discount named", m["flags"])
USER["u"] = {"user": "manoj", "roles": ["checker"]}
rep = c.get("/finance/slips/report/" + WD).get_data(as_text=True)
ok("not yet uploaded to Docterz" not in rep and "WALK NEWNAME" in rep, "report: no upload section; the new name shows")
# negative control
USER["u"] = {"user": "shavez", "roles": ["maker"]}
A0, S0 = app_for(live_dir, "old")
m0 = A0.test_client().get("/finance/slips").get_data(as_text=True)
ok("Docterz upload" in m0, "negative control: the live tile still offers Docterz upload")
ok({r.rule for r in A0.url_map.iter_rules()} == {r.rule for r in A.url_map.iter_rules()}, "slip tile: routes identical (%d)" % len(list(A.url_map.iter_rules())))
print("WALK OK %d/%d checks" % (N[0], N[0]))
