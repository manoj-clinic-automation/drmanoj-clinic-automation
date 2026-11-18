#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s878.py -- kit S878 (the parent, S484, 18-Nov-2026), on a MADE-UP root: a made-up finance db (the tables the page
reads), a made-up Call Console mirror, a made-up clinical data report; invented names, numbers and diagnoses.
    python3 walk_s878.py <dir holding records.py + patient_events.py + not_in_docterz.py> <scratch>     last line 'WALK n/m'
Control: the live files (S834's page, S876's events) go red."""
import io
import os
import random
import re
import sqlite3
import sys

d, scr = sys.argv[1:3]
here = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != here]          # F-1441
sys.path.insert(0, d)
os.makedirs(scr, exist_ok=True)
for f in ("fin.db", "console.db", "clinical_made_up.csv"):
    if os.path.exists(os.path.join(scr, f)):
        os.remove(os.path.join(scr, f))
os.environ["NID_CONSOLE_DB"] = os.path.join(scr, "console.db")
ok, n = 0, 0


def chk(name, cond, info=""):
    global ok, n
    n += 1
    ok += bool(cond)
    print(("ok   " if cond else "FAIL ") + name + (("  [" + str(info)[:220] + "]") if (info and not cond) else ""))


try:
    import records as rc
    import patient_events as pe
except Exception as e:                                   # noqa: BLE001
    print("FAIL import: %s" % e)
    print("WALK 0/28")
    sys.exit(1)

rnd = random.Random()
A = str(rnd.randint(10000, 99999))
MOB = "9%09d" % rnd.randint(0, 999999999)
DB = os.path.join(scr, "fin.db")
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
con.executescript("""
CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT);
CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT, phone_last4 TEXT, merged_into TEXT);
CREATE TABLE day_entry (id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT);
CREATE TABLE sale_item (id INTEGER PRIMARY KEY, day_entry_id INT, unit TEXT, patient_ref_id INT, service TEXT, amount_p INT, mode TEXT, source_ref TEXT, confidence REAL, verified_by TEXT);
CREATE TABLE sale_line_item (id INTEGER PRIMARY KEY, day_entry_id INT, business_date TEXT, bill_no TEXT, is_return INT, seq INT, item_name TEXT, item_key TEXT, pack TEXT, qty_raw TEXT, amount_p INT, expiry_ym TEXT, batch TEXT);
CREATE TABLE identity_dispute (id INTEGER PRIMARY KEY, bill_no TEXT, clinic_id TEXT, status TEXT);
CREATE TABLE clinic_day_line (business_date TEXT, section TEXT, patient TEXT, clinic_id TEXT, amount_p INT, mode TEXT);
CREATE TABLE patient_visit (visit_date TEXT, clinic_id TEXT);
CREATE TABLE slip (id INTEGER PRIMARY KEY, series TEXT, slip_no TEXT, day TEXT, clinic_id TEXT, state TEXT);
CREATE TABLE slip_item (id INTEGER PRIMARY KEY, slip_id INT, kind TEXT, name TEXT, side TEXT, sort INT);
CREATE TABLE blood_order (id INTEGER PRIMARY KEY, day TEXT, clinic_id TEXT, state TEXT, outcome TEXT);
CREATE TABLE lab_report (msg_id TEXT, clinic_id TEXT, received_at TEXT);
CREATE TABLE dx_visit (patient_uid TEXT, visit_date TEXT, clinic_id TEXT, diagnosis_raw TEXT, std_dx TEXT, category TEXT, priority TEXT, dx_status TEXT, follow_up_date TEXT, export_id INT, updated_at TEXT);
CREATE TABLE docterz_export (id INTEGER PRIMARY KEY, drive_id TEXT, drive_name TEXT, drive_mtime TEXT, md5 TEXT, kind TEXT, business_date TEXT, rows INT, stored TEXT, status TEXT, note TEXT, taken_at TEXT);
""")
rc.ensure(con)                                            # record_file, record_event, record_upload, record_open
con.execute("INSERT INTO patient_ref VALUES (1,?,?,?,NULL)", (A, "MADE UP ONE", MOB[-4:]))
days = ["2031-10-%02d" % x for x in (1, 10, 22)] + ["2031-11-%02d" % x for x in (4, 17)]
for i, dd in enumerate(days, 1):
    con.execute("INSERT INTO day_entry VALUES (?,?,?)", (i, "medical", dd))
E = {dd: i for i, dd in enumerate(days, 1)}


def bill(no, day, lines, ret=False, mode="cash", amt=None):
    tot = 0
    for s, (name, pack, qty, amount, batch, exp) in enumerate(lines, 1):
        con.execute("INSERT INTO sale_line_item (day_entry_id,business_date,bill_no,is_return,seq,item_name,item_key,pack,qty_raw,amount_p,expiry_ym,batch) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (E[day], day, no, 1 if ret else 0, s, name, name.upper(), pack, qty, amount, exp, batch))
        tot += amount
    con.execute("INSERT INTO sale_item (day_entry_id,unit,patient_ref_id,service,amount_p,mode,source_ref,confidence,verified_by) VALUES (?,?,?,?,?,?,?,?,?)",
                (E[day], "medical", 1, "pharmacy_return" if ret else "pharmacy", amt if amt is not None else tot, mode, no, 1.0, "x"))


bill("B7731", "2031-11-17", [("FEBUX 40 TAB", "1*10", "3:0", 36500, "FB2411", "2028-10"), ("ACECLO-P TAB", "1*10", "2:0", 18000, "AP7781", "2028-03"),
                             ("PANTOP 40 TAB", "1*10", "1:0", 9500, "PN0921", "2027-08")], mode="upi", amt=60000)        # MRP 640 -> paid 600: a discount
bill("B7540", "2031-10-22", [("CALCIUM D3 TAB", "1*10", "3:0", 36500, "CD3302", "2028-02"), ("DICLO GEL 30G", "30GM", "1.0", 14000, "DG0176", "2027-09")])
bill("CN7558", "2031-10-22", [("CALCIUM D3 TAB", "1*10", "1:0", 12000, "CD3302", "2028-02")], ret=True)
bill("B7102", "2031-10-01", [("ACECLO-P TAB", "1*10", "2:0", 18000, "AP6610", "2027-12")])
for day, sec, amt, mode in (("2031-11-17", "consult", 30000, "cash"), ("2031-11-17", "xray", 60000, "upi"), ("2031-11-04", "revisit", 0, ""),
                            ("2031-11-04", "proc", 80000, "upi"), ("2031-10-22", "consult", 30000, "upi"), ("2031-10-10", "concession", 10000, "cash"),
                            ("2031-10-01", "consult", 30000, "cash"), ("2031-10-01", "xray", 70000, "cash"), ("2031-10-01", "proc", 60000, "cash")):
    con.execute("INSERT INTO clinic_day_line VALUES (?,?,?,?,?,?)", (day, sec, "MADE UP ONE", A, amt, mode))
con.execute("INSERT INTO slip VALUES (1,'xray','X-1187','2031-11-17',?,'ok')", (A,))
con.execute("INSERT INTO slip_item (slip_id,kind,name,side,sort) VALUES (1,'xray','Knee AP/Lat','right',1)")
con.execute("INSERT INTO record_file (clinic_id,kind,day,drive_id,file_name,mime,source,source_ref,state,note,added_at,added_by) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (A, "xray", "2031-11-17", "driveX1", "KNEE R AP.jpg", "image/jpeg", "walk", "x1", "ok", "", "2031-11-17T10:00:00", "walk"))
con.execute("INSERT INTO record_file (clinic_id,kind,day,drive_id,file_name,mime,source,source_ref,state,note,added_at,added_by) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (A, "blood", "2031-10-10", "driveB1", "report.pdf", "application/pdf", "walk", "b1", "ok", "", "2031-10-10T10:00:00", "walk"))
con.execute("INSERT INTO blood_order (day,clinic_id,state,outcome) VALUES ('2031-11-17',?,'ok','')", (A,))
con.execute("INSERT INTO lab_report VALUES ('m1',?,'2031-11-16T09:00:00')", (A,))
rc.up_ensure(con)
con.execute("INSERT INTO record_event (clinic_id,day,hospital,what,note,state,added_at,added_by) VALUES (?,?,?,?,?,?,?,?)",
            (A, "2031-10-15", "Made Up Hospital", "ORIF distal radius left", "volar plate", "ok", "2031-10-15T10:00:00", "walk"))
for day, raw, std, cat, pri, fu in (("2031-11-17", "gout rt knee", "Gouty arthritis", "Rheumatology", "A", "2031-11-24"),
                                    ("2031-10-22", "gout rt knee", "Gouty arthritis", "Rheumatology", "A", "2031-11-04"),
                                    ("2031-10-01", "fracture distal radius lt", "Distal radius fracture", "Trauma", "B", "2031-10-10")):
    con.execute("INSERT INTO dx_visit VALUES ('UID1',?,?,?,?,?,?,'',?,1,'x')", (day, A, raw, std, cat, pri, fu))
# the made-up clinical data report
csvp = os.path.join(scr, "clinical_made_up.csv")
with open(csvp, "w", encoding="utf-8", newline="") as fh:
    fh.write("Patient UID,Patient Name,Consultation Date,Consultation Time,Clinic Specific Id,Purpose Of Visit,Diagnosis,Drugs Prescribed,Dosage,Instructions,Tests,Procedures,Follow Up\n")
    fh.write("UID1,MADE UP ONE,2031-11-17,11:40,%s,Review,gout rt knee,\"FEBUX 40; ACECLO-P; PANTOP 40\",\"1-0-1 x 10 days; 0-0-1 x 30 days; 1-0-0\",no alcohol,\"uric acid, CRP\",,2031-11-24\n" % A)
    fh.write("UID1,MADE UP ONE,2031-10-22,12:05,%s.0,New,gout rt knee,CALCIUM D3,1-0-1,,,,2031-11-04\n" % A)
    fh.write("UID9,SOMEONE ELSE,2031-11-17,11:50,77777,Review,other,OTHERMED,1-0-1,,,,\n")
con.execute("INSERT INTO docterz_export (drive_id,drive_name,drive_mtime,md5,kind,business_date,rows,stored,status,note,taken_at) VALUES ('d','c.csv','m','x','clinical','2031-11-17',3,?,'current','','x')", (csvp,))
con.commit()
# the made-up Call Console mirror
cc = sqlite3.connect(os.environ["NID_CONSOLE_DB"])
cc.execute("CREATE TABLE patients (phone10 TEXT, clinic_id TEXT)")
cc.execute("INSERT INTO patients VALUES (?,?)", (MOB, A))
cc.commit()
cc.close()


def getdb():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


# ---- A. the one reader carries the diagnosis
rec = pe.events(getdb(), A)
dxe = [e for dd in rec["days"] for e in dd["events"] if e["kind"] == "dx"]
chk("A1 patient_events carries a 'dx' event per visit day with a diagnosis", len(dxe) == 3 and dxe[0]["head"] == "Gouty arthritis", [(e["head"], e["sub"]) for e in dxe])
chk("A2 ... with the follow-up advised in its sub, and the raw words when they differ", bool(dxe) and "follow-up advised 24-Nov" in dxe[0]["sub"] and "gout rt knee" in dxe[0]["text"], dxe[:1])
d17 = next(dd for dd in rec["days"] if dd["date"] == "2031-11-17")
chk("A3 the dx line sorts right after the consultation line", [e["kind"] for e in d17["events"]][:2] == ["consult", "dx"], [e["kind"] for e in d17["events"]])

# ---- B. the page
try:
    import flask
    app = flask.Flask("w878")
    rc.init(app, getdb, lambda *a, **kw: ({"user": "manoj"}, None))
    pe.init(app, getdb, lambda *a, **kw: ({"user": "manoj"}, None))
    cl = app.test_client()
    r = cl.get("/finance/records/p/" + A)
    page = r.get_data(as_text=True)
    chk("B1 the page answers 200", r.status_code == 200, r.status_code)
    chk("B2 the banner carries the full mobile from the mirror (not last-4 only)", MOB in page and ("••••" + MOB[-4:]) not in page)
    chk("B3 the banner carries the diagnosis, latest first, with the earlier one under it", "Diagnosis:</b> Gouty arthritis" in page and "Earlier: Distal radius fracture" in page)
    chk("B4 next follow-up advised shown", "next follow-up advised <b>24-Nov-2031</b>" in page)
    chk("B5 the money is a quiet chip, folded, with the heads inside", '<details class="money"><summary title="more">₹ ···</summary>' in page and "consultations ₹1,000 (3 paid · 1 free · 1 concession)" in page, re.findall(r"consultations [^<]{0,60}", page)[:1])
    chk("B6 ... pharmacy net of the return, the bill discount named, the months table", "pharmacy ₹1,165 net (bill discounts ₹40)" in page and "<th>Oct-2031</th>" in page and "<th>Nov-2031</th>" in page, re.findall(r"pharmacy [^<]{0,60}", page)[:1])
    chk("B7 every day is a folded card; none open by default", page.count('<details class="day">') == 7 and '<details class="day" open' not in page, page.count('<details class="day">'))
    chk("B8 a day's folded line says what happened", "— Consulted · X-ray · Blood test · Bought medicines" in page or "— Consulted · X-ray · Bought medicines · Blood test" in page, re.findall(r"— [^<]{0,80}", page)[:3])
    chk("B9 the Docterz line is folded, with the analytical use only on its face", 'Docterz: <b>Gouty arthritis</b> · prescribed 3, bought 3 here ✓ · follow-up advised <b>24-Nov-2031</b>' in page, re.findall(r"Docterz: [^\n]{0,160}", page)[:2])
    chk("B10 ... an earlier follow-up kept: 'came'", "follow-up advised 04-Nov-2031 → <span class=\"ok\">came 04-Nov-2031 ✓</span>" in page)
    chk("B11 ... the drugs, dosage, advice, tests inside the fold", "<b>Prescribed:</b> FEBUX 40; ACECLO-P; PANTOP 40 — 1-0-1 x 10 days" in page and "<b>Advised:</b> no alcohol" in page and "<b>Tests advised:</b> uric acid, CRP" in page)
    chk("B12 the clinical export's '12345.0' ID reads as the ID (only this patient's rows)", "<b>Prescribed:</b> CALCIUM D3 — 1-0-1</div>" in page and "OTHERMED" not in page)
    chk("B13 the Hub's bill-line table, folded: item · qty · pack · rate · line ₹ · batch · exp", "<th>item</th><th>qty</th><th>pack</th><th class=\"num\">rate</th><th class=\"num\">line ₹</th><th>batch</th><th>exp</th>" in page and "<td>FEBUX 40 TAB</td><td>3:0</td><td>1*10</td><td class=\"num\">121.67</td><td class=\"num\">365.00</td><td>FB2411</td><td>2028-10</td>" in page)
    chk("B14 a return is a red line inside the credit note's table", 'class="ret"><td>CALCIUM D3 TAB</td>' in page and "−120.00" in page)
    chk("B15 the day's total at the foot, from the money map", "This day: ₹1,500" in page and "This day: ₹800" in page, re.findall(r"This day: [^<]{0,20}", page))
    chk("B16 On file: a tile per paper, opening in place, with a new-tab link; nothing opens by itself", page.count('class="tile') >= 2 and 'data-src="/finance/records/file/' in page and 'id="rv0"' in page and 'rel="noopener">Open in a new tab ↗</a>' in page and '<iframe src="/finance/records/file' not in page and '<img src="/finance/records/file' not in page)
    chk("B17 the lab e-mail not yet filed shows as a tile", "Lab e-mail · 16-Nov-2031" in page)
    chk("B18 a film on a day's line opens in place", "see here</a>" in page and 'class="vb" data-src="/finance/records/file/' in page)
    chk("B19 the bar: Expand all · Collapse all · Top", "rvAll(true)" in page and "rvAll(false)" in page and "↑ Top" in page)
    chk("B20 no dialog on the page (F-1464)", "confirm(" not in page and "alert(" not in page)
    chk("B21 the add-paper and the hospital-event forms stay", "Add a paper" in page and ("Add a hospital event" in page or "hospital" in page.lower()) and 'class="add"' in page, [x for x in ("Add a paper", "hospital", 'class="add"') if x not in page and x not in page.lower()])
    chk("B22 the old page kept as the fallback", callable(getattr(rc, "_patient_html_s834", None)))
    chk("B23 English only, no Hindi on the owner's page", not re.search(r"[ऀ-ॿ]", page))
    r2 = cl.get("/finance/records/p/" + A + "?msg=hello")
    chk("B24 the msg banner still shows", 'class="okb">hello' in r2.get_data(as_text=True))
    r3 = cl.get("/finance/records/p/99999999")
    chk("B25 an unknown ID still renders (empty record, no crash)", r3.status_code == 200 and "Nothing on record yet" in r3.get_data(as_text=True), r3.status_code)
except Exception as e:                                   # noqa: BLE001
    import traceback
    traceback.print_exc()
    chk("B0 the page could be tried", False, "%s: %s" % (type(e).__name__, e))
print("WALK %d/%d" % (ok, n))
sys.exit(0 if ok == n else 1)
