#!/usr/bin/env python3
"""walk_s423.py -- the walk for kit S423_VITALS_VPS. Everything in a scratch folder: fake patient stores, the real
engine and page, a bare Flask app with the module registered exactly as portal.py registers it.
usage: walk_s423.py <app_dir holding vitals_portal.py + clinic_writer.py + the font> <vitals_page.html> [<patched portal.py>]
Prints WALK OK n/n or WALK RED."""
import ast
import csv
import json
import os
import shutil
import sqlite3
import sys
import tempfile

APP, PAGE = sys.argv[1], sys.argv[2]
PORTAL = sys.argv[3] if len(sys.argv) > 3 else ""
T = tempfile.mkdtemp(prefix="s423_")
VD = os.path.join(T, "vitals")
os.makedirs(VD)
shutil.copy(PAGE, os.path.join(VD, "vitals_page.html"))
fin, con_db = os.path.join(T, "finance.db"), os.path.join(T, "console.db")
c = sqlite3.connect(fin)
c.execute("CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT, mobile TEXT, merged_into TEXT)")
c.executemany("INSERT INTO patient_ref (clinic_id,name,mobile,merged_into) VALUES (?,?,?,?)",
              [("4321", "RAM SINGH", "5111111111", None), ("7777", "ONLY MASTER", "5222222222", None),
               ("4321", "OLD MERGED", "5000000000", "x")])
c.commit(); c.close()
c = sqlite3.connect(con_db)
c.execute("CREATE TABLE patients (phone10 TEXT, name TEXT, diagnosis TEXT, age TEXT, gender TEXT, last_visit TEXT, patient_uid TEXT, clinic_id TEXT)")
c.executemany("INSERT INTO patients VALUES (?,?,?,?,?,?,?,?)",
              [("5111111111", "RAM SINGH", "Knee OA", "61", "M", "2026-09-10", "PU-0001", "4321"),
               ("5333333333", "SITA", "Low back pain", "45", "F", "", "PU-0002", "5555"),
               ("5333333333", "GITA", "Frozen shoulder", "52", "F", "", "PU-0003", "5555")])
c.commit(); c.close()
os.environ.update({"PORTAL_VITALS_DIR": VD, "PORTAL_FINANCE_DB": fin, "PORTAL_CONSOLE_DB": con_db})
sys.path.insert(0, APP)
import vitals_portal as vp          # noqa: E402
from flask import Flask             # noqa: E402

N = [0, 0]
def check(name, cond, extra=""):
    N[1] += 1
    if cond:
        N[0] += 1; print("  ok  " + name)
    else:
        print("  RED %s %s" % (name, extra))

app = Flask("walk")
GATE = {"on": True}
def guard(f):
    from functools import wraps
    @wraps(f)
    def w(*a, **k):
        if not GATE["on"]:
            return ("forbidden", 403)
        return f(*a, **k)
    return w
vp.register(app, guard, lambda: "manoj")
web = app.test_client()

print("[1] the page")
h = web.get("/portal/vitals").get_data(as_text=True)
check("served, both calls rewritten to /portal/vitals/*, no bare /lookup or /save left",
      'fetch("/portal/vitals/lookup?' in h and 'fetch("/portal/vitals/save",' in h
      and 'fetch("/lookup?' not in h and 'fetch("/save",' not in h)
raw = open(PAGE, encoding="utf-8").read()
check("otherwise the PC's page byte for byte", h == raw.replace('fetch("/lookup?', 'fetch("/portal/vitals/lookup?').replace('fetch("/save",', 'fetch("/portal/vitals/save",'))
check("the file on disk is left as the PC's", open(os.path.join(VD, "vitals_page.html"), encoding="utf-8").read() == raw)
GATE["on"] = False
check("the gate is applied to every route", all(web.get(u).status_code == 403 for u in ("/portal/vitals", "/portal/vitals/lookup?clinic_id=4321", "/portal/vitals/health"))
      and web.post("/portal/vitals/save", json={}).status_code == 403 and web.post("/portal/vitals/import", json={}).status_code == 403)
GATE["on"] = True

print("[2] the lookup (the Case Pack's two stores, read-only)")
j = web.get("/portal/vitals/lookup?clinic_id=4321").get_json()
m = j["matches"]
check("one match with UID, age, sex, diagnosis, mobile; merged row ignored",
      j["ok"] and len(m) == 1 and m[0]["Patient_UID"] == "PU-0001" and m[0]["Age"] == "61" and m[0]["Sex"] == "M"
      and m[0]["Standardized_Diagnosis"] == "Knee OA" and m[0]["Mobile_Clean"] == "5111111111" and m[0]["Patient_Name"] == "RAM SINGH", m)
check("the page's keys, all present", set(m[0]) == {"Patient_UID", "Clinic_Specific_Id", "Patient_Name", "Mobile_Clean",
      "Mobile_Duplicate_Count", "Age", "Sex", "Standardized_Diagnosis", "Comorbidities"})
m = web.get("/portal/vitals/lookup?clinic_id=5555").get_json()["matches"]
check("two UIDs on one Clinic ID -> two matches (the pick-list, never auto-picked), shared mobile counted",
      len(m) == 2 and {x["Patient_UID"] for x in m} == {"PU-0002", "PU-0003"} and m[0]["Mobile_Duplicate_Count"] == "2", m)
m = web.get("/portal/vitals/lookup?clinic_id=7777").get_json()["matches"]
check("in the master only -> one match with no UID (filed as pending, as on the PC)", len(m) == 1 and m[0]["Patient_UID"] == "" and m[0]["Patient_Name"] == "ONLY MASTER", m)
check("unknown ID -> no match; blank -> no match", web.get("/portal/vitals/lookup?clinic_id=9999").get_json()["matches"] == []
      and web.get("/portal/vitals/lookup?clinic_id=").get_json()["matches"] == [])

print("[3] the one-time import of the PC's ledgers (so the counters continue)")
vh = ",".join(vp.CW.VITALS_COLS); ph = ",".join(vp.CW.PLAN_COLS)
vtext = vh + "\n" + "\n".join("V-2026-%06d,PU-0001,4321,RAM SINGH,2026-07-%02d,60,M,170,70,24.2,Normal,90,0.53,120,80,72,owner,vitals-app,2026-07-%02dT10:00:00+05:30," % (i, i, i) for i in range(1, 15)) + "\n"
ptext = ph + "\n" + "\n".join("P-2026-%06d,PU-0001,4321,RAM SINGH,2026-07-%02d,Knee OA,,Veg,V-2026-%06d,Patient; Physio,,,owner,2026-07-%02dT10:00:00+05:30" % (i, i, i, i) for i in range(1, 15)) + "\n"
r = web.post("/portal/vitals/import", json={"name": "vitals_ledger.csv", "text": "Wrong,Header\n1,2\n"})
check("a wrong header is refused", r.status_code == 409 and "header" in r.get_json()["msg"])
r1 = web.post("/portal/vitals/import", json={"name": "vitals_ledger.csv", "text": vtext}).get_json()
r2 = web.post("/portal/vitals/import", json={"name": "plan_ledger.csv", "text": ptext.replace("\n", "\r\n")}).get_json()
check("both ledgers imported, 14 + 14", r1["ok"] and r2["ok"] and r1["msg"].startswith("14") and r2["msg"].startswith("14"), (r1, r2))
r = web.post("/portal/vitals/import", json={"name": "vitals_ledger.csv", "text": vtext})
check("a second import is refused -- never overwrites a row", r.status_code == 409 and "already" in r.get_json()["msg"])
check("imported ledger is 0600", oct(os.stat(os.path.join(VD, "vitals_ledger.csv")).st_mode & 0o777) == "0o600")
check("unknown file name refused", web.post("/portal/vitals/import", json={"name": "../x.csv", "text": vtext}).status_code == 409)

print("[4] a save, the PC tool's steps on the server's paths")
payload = {"Patient_UID": "PU-0001", "Clinic_Specific_Id": "4321", "Patient_Name": "RAM SINGH", "Mobile": "5111111111",
           "Plan_Date": "2026-09-27", "Age_At_Visit": "61", "Sex": "M", "Height_cm": "170", "Weight_kg": "80",
           "Waist_cm": "100", "BP_Systolic": "130", "BP_Diastolic": "85", "Pulse_bpm": "76", "Note": "",
           "Conditions_Selected": "Knee OA", "Comorbidities_Selected": "Diabetes", "Diet_Type": "Veg",
           "Sheets_Printed": "Patient; Physio",
           "Patient_Sections": [["आहार / Diet", ["दलिया सुबह", "Walk 30 min"]]],
           "Physio_Sections": [["Exercises", ["Quadriceps sets 10 x 3", "सीढ़ी धीरे"]]]}
j = web.post("/portal/vitals/save", json=payload).get_json()
check("saved: the next IDs after the imported ones (V/P-2026-000015)", j.get("ok") and j["vitals_id"] == "V-2026-000015" and j["plan_id"] == "P-2026-000015", j)
check("BMI computed by the engine (27.7, Overweight-class)", str(j.get("bmi")) == "27.7", j)
pat = os.path.join(VD, j["patient_pdf"]); phy = os.path.join(VD, j["physio_pdf"])
check("both PDFs filed under plan_archive/2026/PU-0001/, real PDFs, the paths returned relative (no server path leaks)",
      os.path.isfile(pat) and os.path.isfile(phy) and open(pat, "rb").read(5) == b"%PDF-" and j["patient_pdf"].startswith("plan_archive/2026/PU-0001/") and not j["patient_pdf"].startswith("/"))
rows = list(csv.DictReader(open(os.path.join(VD, "vitals_ledger.csv"), encoding="utf-8")))
check("the ledger row says who and where: Entered_By manoj, Source_Face vitals-vps", rows[-1]["Entered_By"] == "manoj" and rows[-1]["Source_Face"] == "vitals-vps" and len(rows) == 15)
prow = list(csv.DictReader(open(os.path.join(VD, "plan_ledger.csv"), encoding="utf-8")))[-1]
check("the plan row links the vitals row", prow["Vitals_ID_Used"] == "V-2026-000015" and prow["Generated_By"] == "manoj")
p2 = dict(payload, Patient_UID="", Clinic_Specific_Id="7777", Patient_Name="ONLY MASTER", Mobile="5222222222")
j2 = web.post("/portal/vitals/save", json=p2).get_json()
check("a patient with no UID is filed under pending/<id>_<mobile>, flagged new", j2["ok"] and j2["new_patient"] and j2["patient_pdf"].startswith("plan_archive/pending/7777_"), j2)
h = web.get("/portal/vitals/health").get_json()
check("health counts 16 + 16 rows and 4 PDFs", h["vitals_rows"] == 16 and h["plan_rows"] == 16 and h["pdfs"] == 4, h)
check("after rows exist, import is refused", web.post("/portal/vitals/import", json={"name": "plan_ledger.csv", "text": ptext}).status_code == 409)

print("[5] a broken page never takes the portal down")
open(os.path.join(VD, "vitals_page.html"), "w", encoding="utf-8").write("<html>no calls</html>")
r = web.get("/portal/vitals")
check("a page without the two calls -> 500 with the reason, not a half-working page", r.status_code == 500 and "not served" in r.get_data(as_text=True))

if PORTAL:
    print("[6] the patched portal.py")
    src = open(PORTAL, encoding="utf-8").read()
    tree = ast.parse(src)
    check("compiles", True)
    tiles = [n for n in ast.walk(tree) if isinstance(n, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == "name" for k in n.keys)]
    vit = [t for t in tiles if any(isinstance(v, ast.Constant) and v.value == "Vitals & Plan" for v in t.values)]
    d = {k.value: (v.value if isinstance(v, ast.Constant) else None) for k, v in zip(vit[0].keys, vit[0].values)} if vit else {}
    check("the tile: /portal/vitals, not PC-only, doctor", d.get("url") == "/portal/vitals" and "pc_only" not in d, d)
    check("its section is Clinic", '"Vitals & Plan": "Clinic"' in src and '"Vitals & Plan": "Clinic PC tools"' not in src)
    i_cp, i_vp = src.index("import casepack_portal"), src.index("import vitals_portal")
    check("mounted once, after the Case Pack, behind casepack_required", src.count("import vitals_portal") == 1 and i_vp > i_cp
          and "vitals_portal.register(\n        app, casepack_required," in src)

shutil.rmtree(T, ignore_errors=True)
print("WALK %s %d/%d" % ("OK" if N[0] == N[1] else "RED", N[0], N[1]))
sys.exit(0 if N[0] == N[1] else 1)
