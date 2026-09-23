#!/usr/bin/env python3
"""walk_s372.py -- the S372 walk: a scratch finance.db with a real-shaped day (revenue row, lines in every section, a
few slips of both books incl. a void one and a person with no slip), the day page and the PDF rendered through the two
modules with a stub gate; the LIVE modules are the negative control.
Usage: python walk_s372.py <dir: finance_clinic_day.py clinic_day_pdf.py slip_lookup.py> [<dir with the LIVE two>]"""
import importlib.util, os, sqlite3, sys, tempfile
app_dir = os.path.abspath(sys.argv[1]); neg = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else ""
tmp = tempfile.mkdtemp(prefix="s372walk_"); dbp = os.path.join(tmp, "f.db")
n = 0
def ok(c, l):
    global n
    if not c: print("WALK RED: " + l); sys.exit(1)
    n += 1
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
con.execute("INSERT INTO clinic_day_revenue(business_date,cons_count,cons_amount_p,xray_count,xray_amount_p,proc_count,proc_amount_p,total_count,total_amount_p,morning,evening,free_revisits,free_concession,tender_json) VALUES(?,3,90000,2,80000,1,50000,6,220000,4,2,1,1,'{}')", (D,))
con.executemany("INSERT INTO clinic_day_line VALUES(?,?,?,?,?,?,?,?,?)", [
    (D, "consult", 1, "RAM KUMAR", "1201", 30000, "Cash", "Morning", ""), (D, "consult", 2, "SITA DEVI", "1202", 30000, "Online Payment", "Morning", ""),
    (D, "consult", 3, "NO SLIP YET", "1300", 30000, "Cash", "Evening", ""),
    (D, "xray", 1, "RAM KUMAR", "1201", 40000, "Cash", "Morning", ""), (D, "xray", 2, "MOHAN LAL", "1305", 40000, "Cash", "Evening", ""),
    (D, "proc", 1, "MOHAN LAL", "1305", 50000, "Cash", "Evening", ""),
    (D, "revisit", 1, "GITA", "1150", 0, "", "Morning", ""), (D, "concession", 1, "ANON", "", 0, "", "Morning", "")])
con.executemany("INSERT INTO slip(series,slip_no,day,clinic_id,state) VALUES(?,?,?,?,?)", [
    ("opd", 19301, D, "1201", "ok"), ("opd", 19302, D, "1202", "ok"), ("opd", 19303, D, "1150", "ok"),
    ("xp", 1201, D, "1201", "ok"), ("xp", 1202, D, "1305", "ok"), ("xp", 1203, D, "1305", "ok"),
    ("opd", 19304, D, "1300", "void"), ("opd", 19290, "2026-09-19", "1300", "ok")])
con.commit(); con.close()
sys.path.insert(0, app_dir)
import slip_lookup
ro = sqlite3.connect(dbp); ro.row_factory = sqlite3.Row
S = slip_lookup.slips_for_day(ro, D)
ok(slip_lookup.slip_no(S, "consult", "1201") == "19301" and slip_lookup.slip_no(S, "xray", "1201") == "1201", "one person, two books, two numbers")
ok(slip_lookup.slip_no(S, "proc", "1305") == "1202", "two X/P slips for one person -> the lower live number")
ok(slip_lookup.slip_no(S, "consult", "1300") == "", "void slip -> blank; another day's slip -> blank")
ok(slip_lookup.slip_no(S, "concession", "") == "" and slip_lookup.slip_no(S, "nonsense", "1201") == "", "no id / unknown section -> blank")
ok(slip_lookup.slips_for_day(sqlite3.connect(":memory:"), D) == {}, "no slip table -> blanks, never an error")

from flask import Flask
def load(path, name):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def build(d, tag):
    app = Flask("walk" + tag)
    def dbg():
        c = sqlite3.connect(dbp); c.row_factory = sqlite3.Row; return c
    def req(*roles, **kw):
        return ({"user": "manoj", "roles": ["checker"]}, None)
    day = load(os.path.join(d, "finance_clinic_day.py"), "fcd" + tag); day.init(app, dbg, req)
    pdf = load(os.path.join(d, "clinic_day_pdf.py"), "cdp" + tag); pdf.init(app, dbg, req)
    return app, day, pdf
app, day, pdf = build(app_dir, "new")
c = app.test_client()
h = c.get("/finance/clinic/day/" + D).get_data(as_text=True)
ok("<th class=\"n slip\">Slip</th><th class=\"n sn\">#</th>" in h, "page: Slip is the FIRST column")
ok("<td class='n slip'>19301</td><td class='n sn'>1</td><td class='p'>RAM KUMAR</td>" in h and "<td class='n slip'>1201</td><td class='n sn'>1</td><td class='p'>RAM KUMAR</td>" in h, "page: RAM KUMAR 19301 in consult, 1201 in X-ray")
ok("<td class='n slip'></td><td class='n sn'>3</td><td class='p'>NO SLIP YET</td>" in h, "page: no live slip -> blank")
ok("<td class='n slip'>19303</td><td class='n sn'>1</td><td class='p'>GITA</td>" in h and "<td class='n slip'></td><td class='n sn'>1</td><td class='p'>ANON</td>" in h, "page: revisit gets its OPD slip; no-id line blank")
ok(h.count("<td></td><td></td><td>Subtotal</td>") == 5, "page: every subtotal row shifted one cell")
ok(c.get("/finance/clinic/day/2026-09-20").status_code == 200 and c.get("/finance/clinic/day?m=2026-09").status_code == 200, "page: empty day + month view still render")
d = pdf.day_data(sqlite3.connect(dbp) if False else (lambda: (lambda cc: (setattr(cc, "row_factory", sqlite3.Row), cc)[1])(sqlite3.connect(dbp)))(), D)
ok(d["slips"] and len(d["sections"]) == 5 and all(len(s) == 3 for s in d["sections"]), "pdf: day_data carries slips and (title, rows, key)")
body = pdf.render_pdf(d, who="manoj")
ok(body[:4] == b"%PDF" and b"Slip" in body and b"19301" in body and b"1202" in body and b"NO SLIP YET" in body, "pdf: renders with the Slip column and real numbers")
r = c.get("/finance/clinic/day/%s.pdf" % D) if any(x.rule.endswith(".pdf") for x in app.url_map.iter_rules()) else None
routes_new = {x.rule for x in app.url_map.iter_rules()}
if neg:
    app0, day0, pdf0 = build(neg, "old")
    h0 = app0.test_client().get("/finance/clinic/day/" + D).get_data(as_text=True)
    ok("Slip</th>" not in h0 and "RAM KUMAR" in h0, "negative control: live page has no Slip column")
    ok({x.rule for x in app0.url_map.iter_rules()} == routes_new, "routes identical (%d)" % len(routes_new))
    b0 = pdf0.render_pdf(pdf0.day_data((lambda cc: (setattr(cc, "row_factory", sqlite3.Row), cc)[1])(sqlite3.connect(dbp)), D), who="manoj")
    ok(b0[:4] == b"%PDF" and b"19301" not in b0, "negative control: live PDF carries no slip numbers")
print("WALK OK %d/%d checks" % (n, n))
