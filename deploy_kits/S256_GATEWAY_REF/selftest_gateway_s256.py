#!/usr/bin/env python3
"""S256_GATEWAY_REF selftest -- offline, no network, no VPS.
Rebuilds the 29-Aug-2026 sheet shape (the day we hold a Razorpay receipt for) and proves the
reference is kept, that nothing else moves, and that an old database migrates."""
import importlib.util, os, sqlite3, sys
from openpyxl import Workbook

HERE = os.path.dirname(os.path.abspath(__file__))
ok = fail = 0
def chk(c, label):
    global ok, fail
    if c: ok += 1;  print("PASS ", label)
    else: fail += 1; print("FAIL ", label)

def load(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sys.modules[name] = m; sp.loader.exec_module(m); return m

REF = "pay_TVSzKeESCXc04L"          # the id in the 29-Aug Docterz mail AND the 29-Aug sheet

def sheet():
    wb = Workbook(); ws = wb.active
    ws.append(["DR. MANOJ AGARWAL CLINIC — DAY REVENUE · 29-Aug-2026"])
    ws.append(["", "Shift split — Morning: 2  Evening: 1"])
    ws.append([])
    ws.append(["PAID CONSULTATIONS (default ₹600 — ▲ above / ▼ below flagged)"])
    ws.append(["S.N", "Patient", "Clinic ID", "Consult ₹", "vs ₹600", "Mode", "Shift", "Notes"])
    ws.append([1, "Shashi", "7958", 600, 600, "Cash", "Evening", ""])
    ws.append([2, "Bindu Malhotra", "7961", 600, 600, "Online Payment " + REF, "Morning", ""])
    ws.append(["", "Subtotal", 2, 1200])
    ws.append([])
    ws.append(["X-RAY (billed under Docterz 'Laboratory' column)"])
    ws.append(["S.N", "Patient", "Clinic ID", "X-ray ₹", "Mode", "Shift"])
    ws.append([1, "Sushma", "7962", 500, "Cash", "Morning"])
    ws.append(["", "Subtotal", 1, 500])
    ws.append([])
    ws.append(["PROCEDURES (incl. ₹0 / free — e.g. Ayushman cashless)"])
    ws.append(["S.N", "Patient", "Clinic ID", "Procedure ₹ (net)", "Note", "Shift"])
    ws.append([1, "Bindu Malhotra", "7961", 800, "Online Payment " + REF, "Morning"])
    ws.append(["", "Subtotal (net)", 1, 800])
    return ws

day = load("docterz_day", os.path.join(HERE, "docterz_day.py"))
d = day.parse_day_revenue(sheet())
lines = d["lines"]
by = {(l["section"], l["patient"]): l for l in lines}

b_con = by[("consult", "Bindu Malhotra")]
b_pro = by[("proc", "Bindu Malhotra")]
chk(b_con["gateway_ref"] == REF, "the consultation keeps the Razorpay id")
chk(b_pro["gateway_ref"] == REF, "the procedure keeps the same id")
chk(b_con["mode"] == "Online Payment", "the mode is still normalised to 'Online Payment'")
chk(by[("consult", "Shashi")]["gateway_ref"] == "", "a cash line carries no reference")
chk(by[("xray", "Sushma")]["gateway_ref"] == "", "an x-ray cash line carries no reference")
chk(all("gateway_ref" in l for l in lines), "every line has the field")

chk(d["business_date"] == "2026-08-29", "the date still reads 2026-08-29")
chk(d["cons_amount_p"] == 120000, "consultations still ₹1,200")
chk(d["proc_amount_p"] == 80000, "procedures still ₹800")
chk(d["total_amount_p"] == 250000, "the day still totals ₹2,500")
chk(d["tender"].get("Online Payment") == 140000, "the online tender is still ₹1,400, under the plain name")
chk(d["tender"].get("Cash") == 110000, "cash still ₹1,100")

ing = load("docterz_ingest", os.path.join(HERE, "docterz_ingest.py"))
con = sqlite3.connect(":memory:"); con.row_factory = sqlite3.Row
con.executescript(ing.SCHEMA)
ing.upsert_lines(con, d)
rows = list(con.execute("SELECT patient, mode, gateway_ref FROM clinic_day_line ORDER BY section, sn"))
chk(sum(1 for r in rows if r["gateway_ref"] == REF) == 2, "both of Bindu's lines are stored with the id")
chk(sum(1 for r in rows if r["gateway_ref"] == "") == len(rows) - 2, "no other line gained one")
chk([r["mode"] for r in rows].count("Online Payment") == 2, "the stored mode is unchanged")

# a database made before this kit: no column, must migrate silently
old = sqlite3.connect(":memory:"); old.row_factory = sqlite3.Row
old.executescript("""CREATE TABLE clinic_day_line (business_date TEXT NOT NULL, section TEXT NOT NULL,
 sn INTEGER NOT NULL, patient TEXT NOT NULL DEFAULT '', clinic_id TEXT NOT NULL DEFAULT '',
 amount_p INTEGER NOT NULL DEFAULT 0, mode TEXT NOT NULL DEFAULT '', shift TEXT NOT NULL DEFAULT '',
 PRIMARY KEY (business_date, section, sn));""")
old.execute("INSERT INTO clinic_day_line VALUES ('2026-08-01','consult',1,'Old','1',60000,'Cash','Morning')")
ing.upsert_lines(old, d)
cols = [r[1] for r in old.execute("PRAGMA table_info(clinic_day_line)")]
chk("gateway_ref" in cols, "an old database gains the column on first write")
kept = old.execute("SELECT COUNT(*) c FROM clinic_day_line WHERE business_date='2026-08-01'").fetchone()["c"]
chk(kept == 1, "the old day's row survives the migration untouched")
chk(old.execute("SELECT COUNT(*) c FROM clinic_day_line WHERE gateway_ref=?", (REF,)).fetchone()["c"] == 2,
    "and the new day's two references land in it")
ing.upsert_lines(old, d)
chk(old.execute("SELECT COUNT(*) c FROM clinic_day_line WHERE business_date='2026-08-29'").fetchone()["c"]
    == len(rows), "re-running the same day leaves no duplicate (migration is idempotent)")

print("\n%d passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
