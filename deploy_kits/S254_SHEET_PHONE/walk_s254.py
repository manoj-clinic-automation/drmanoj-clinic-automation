#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s254.py -- the LIVE-SHAPE walk for S254_SHEET_PHONE (the S253 walk + the sheet layout and folds).

The REAL finance_app.py -- this kit's patched copy -- over a real sqlite database built from the
real schemas, with every live sibling module copied beside it (FIN_MODS), the kit's four patched
files and clinic_money.py on top.  Requests go through Flask's WSGI test client and through the
app's own front gate (_gate), so the physiotherapist's hard edge is proven by the gate that will
enforce it, not by a stub.  Then the kit's patched portal.py is imported with tile_grants v15 and
its own _visible_sections is asked who is shown which tile.  (S251: grants v16, on the S250 v15.)  Nothing live is touched.

    FIN_MODS=<folder with the live modules> KIT=<this kit> python3 -B walk_s249.py
On the box after the files are placed (builds its own db; copies nothing live):
    FIN_MODS=/root/finance PORTAL_DIR=/root/portal /root/wa/venv/bin/python3 -B walk_s249.py
"""
import datetime as dt
import importlib.util
import io
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

KIT = os.environ.get("KIT", os.path.dirname(os.path.abspath(__file__)))
FIN_MODS = os.environ.get("FIN_MODS", "/root/finance")
PORTAL_DIR = os.environ.get("PORTAL_DIR", "/root/portal")
TMP = tempfile.mkdtemp(prefix="walk_s249_")
MOD = os.path.join(TMP, "mods")
UI = os.path.join(TMP, "ui")
POR = os.path.join(TMP, "portal")
DB = os.path.join(TMP, "finance.db")
for d in (MOD, UI, POR, os.path.join(TMP, "upi")):
    os.makedirs(d)

PASSED, FAILED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label, ("   [%s]" % str(detail)[:400]) if detail and not cond else ""))


# ---- the module folder: every live sibling, then this kit's files on top ---------------------
for f in os.listdir(FIN_MODS):
    if f.endswith((".py", ".sql", ".html", ".json")) and os.path.isfile(os.path.join(FIN_MODS, f)):
        shutil.copyfile(os.path.join(FIN_MODS, f), os.path.join(MOD, f))
for f in ("finance_clinic_day.py", "clinic_register.py", "clinic_money.py"):
    # S252 ships clinic_money.py only; the S251 siblings are read from the live folder (already in MOD)
    if os.path.exists(os.path.join(KIT, f)):
        shutil.copyfile(os.path.join(KIT, f), os.path.join(MOD, f))
# finance_app.py is never in the repository (F-185): patched here, in memory, from the live bytes
sys.path.insert(0, KIT)
import patch_s249 as PATCHER                                            # noqa: E402
_fa_raw = io.open(os.path.join(FIN_MODS, "finance_app.py"), encoding="utf-8").read()
_fa_new, _fa_st = PATCHER.patch_text("finance_app.py", _fa_raw)
io.open(os.path.join(MOD, "finance_app.py"), "w", encoding="utf-8", newline="\n").write(_fa_new)
for f in ("finance_daily.html", "finance_review.html", "finance_approvals.html", "finance_entry.html",
          "finance_workbench.html", "finance_entry_clinic.html"):
    io.open(os.path.join(UI, f), "w").write("<html><body>walk stub %s</body></html>" % f)

# ---- the database: the real schemas ----------------------------------------------------------
con = sqlite3.connect(DB)
con.executescript(io.open(os.path.join(FIN_MODS, "finance_schema.sql"), encoding="utf-8").read())
for extra in ("finance_returns.sql", "purchase_schema.sql"):
    p = os.path.join(FIN_MODS, extra)
    if os.path.exists(p):
        con.executescript(io.open(p, encoding="utf-8").read())
sys.path.insert(0, MOD)
import docterz_ingest as DI                                             # noqa: E402
con.executescript(DI.SCHEMA)
import finance_upi as FU                                                # noqa: E402
FU.ensure_txn_schema(con) if hasattr(FU, "ensure_txn_schema") else None
con.execute("CREATE TABLE IF NOT EXISTS upi_txn (id INTEGER PRIMARY KEY, merchant_id TEXT NOT NULL, unit TEXT, "
            "txn_date TEXT NOT NULL, amount_p INTEGER NOT NULL, rrn TEXT NOT NULL, mode TEXT, txn_time TEXT, "
            "source_sha TEXT, ingested_at TEXT)")
# the clinic desk as it is on the box: shavez/alisha/shivani makers, manoj/bhawna checkers
for user, role in (("shavez", "maker"), ("shavez", "checker"), ("alisha", "maker"), ("shivani", "maker"), ("manoj", "checker"), ("bhawna", "checker")):
    con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('clinic',?,?,1)", (user, role))
con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('medical','manoj','checker',1)")
con.commit()
con.close()

os.environ.update(FINANCE_DB=DB, FINANCE_UI_DIR=UI, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_PORTAL_LOGIN="/portal",
                  FINANCE_SCAN_DIR=os.path.join(TMP, "scans"), FINANCE_UPI_DIR=os.path.join(TMP, "upi"),
                  FINANCE_MARG_TOKEN="DUMMY-TOKEN-PUT-HERE", FINANCE_AUTOAPPLY_OFF=os.path.join(TMP, "AUTOAPPLY_OFF"),
                  ATT_PUNCH_CSV=os.path.join(TMP, "no_punches.csv"), SR_DB_PATH=os.path.join(TMP, "no_staff_register.db"))
import finance_app as FA                                                # noqa: E402
import clinic_money as CM                                               # noqa: E402

print("WALK S249_CLINIC_MONEY   finance_app=%s   db=%s" % (os.path.join(MOD, "finance_app.py"), DB))
c = FA.app.test_client()
MNJ = {"X-Clinic-User": "manoj", "X-Clinic-Role": "doctor"}
BHW = {"X-Clinic-User": "bhawna", "X-Clinic-Role": "doctor"}
SHZ = {"X-Clinic-User": "shavez", "X-Clinic-Role": "staff"}
ALI = {"X-Clinic-User": "alisha", "X-Clinic-Role": "staff"}
BHT = {"X-Clinic-User": "bhati", "X-Clinic-Role": "staff"}
NOB = {"X-Clinic-User": "", "X-Clinic-Role": ""}

# the day under test: a Saturday-shaped day two days back, so the MPR window arithmetic is stable
D = "2026-09-12"
D2 = "2026-09-11"
D3 = "2026-09-10"
os.environ["CLINIC_MONEY_NOW"] = "2026-09-13T09:30:00"          # the morning after D, before the MPR deadline


def get(h, url):
    r = c.get(url, headers=h)
    return r.status_code, r.get_data(as_text=True), r


def post(h, url, **form):
    r = c.post(url, headers=h, data=form)
    return r.status_code, r.get_data(as_text=True), r


def dbx(sql, *args):
    cx = sqlite3.connect(DB)
    cx.execute(sql, args)
    cx.commit()
    cx.close()


def dbq(sql, *args):
    cx = sqlite3.connect(DB)
    cx.row_factory = sqlite3.Row
    r = cx.execute(sql, args).fetchall()
    cx.close()
    return r


# ================================================================ 0 mount
print("\n-- 0 the mount")
ck("finance_app.py patched in memory from the live bytes (%s)" % _fa_st, _fa_st in ("patched", "already"))
ck("clinic_money is mounted", "clinic_money" in FA.app.blueprints)
ck("clinic_register and clinic_day still mounted", "clinic_register" in FA.app.blueprints and "clinic_day" in FA.app.blueprints)
ck("healthz 200", c.get("/finance/healthz").status_code == 200)
ck("finance_app resolves /finance/physio to the physio unit", FA._unit_for_path("/finance/physio/x") == "physio"
   and FA._unit_for_path("/finance/clinic/register") == "clinic" and FA._unit_for_path("/finance/approvals") == "medical")
ck("not signed in: the match page redirects to the portal", get(NOB, "/finance/clinic/match/%s" % D)[0] == 302)

# ================================================================ 1 the seed and the hard edge
print("\n-- 1 the physiotherapy unit and Bhati's hard edge")
s, h, r = get(BHT, "/finance/physio")
ck("before the seed: bhati is refused everywhere (302 to the portal)", s == 302)
r1 = subprocess.run([sys.executable, "-B", os.path.join(KIT, "seed_s249.py"), DB], capture_output=True, text=True)
r2 = subprocess.run([sys.executable, "-B", os.path.join(KIT, "seed_s249.py"), DB], capture_output=True, text=True)
ck("seed_s249: unit + 6 rows + setting once; second run NOT changed",
   r1.returncode == 0 and "business_unit physio" in r1.stdout and "unit_role physio/bhati viewer" in r1.stdout
   and "setting clinic_money.checker=shavez" in r1.stdout and r2.returncode == 0 and "NOT changed" in r2.stdout, (r1.stdout, r1.stderr, r2.stdout))
ck("bhati holds NO clinic row", not dbq("SELECT 1 FROM unit_role WHERE unit='clinic' AND username='bhati' AND active=1"))
s, h, r = get(BHT, "/finance/physio")
ck("bhati: /finance/physio 200, in Hindi, read-only", s == 200 and "Physiotherapy ka hisaab" in h and "Received" not in h and "<script" not in h.lower(), (s, h[:200]))
for url in ("/finance/clinic/register", "/finance/clinic/day", "/finance/clinic/day/%s" % D, "/finance/clinic/day/%s/mpr" % D,
            "/finance/clinic/bank/mpr", "/finance/clinic/match", "/finance/clinic/match/%s" % D, "/finance/clinic/money",
            "/finance/clinic/register/%s" % D, "/finance/approvals", "/finance/darpan/kal", "/finance/amir"):
    s, h, r = get(BHT, url)
    ck("bhati refused at the front gate: %s -> %d" % (url, s), s == 302 and "/portal" in (r.headers.get("Location") or ""), (s, r.headers.get("Location")))
s, h, r = get(BHT, "/finance/clinic/api/day/%s" % D)
ck("bhati refused on the clinic API: 403 no_role_here, not data", s == 403 and "no_role_here" in h, (s, h[:120]))
s, h, r = post(BHT, "/finance/physio/received/%s" % D)
ck("bhati cannot tap received (403)", s == 403)
s, h, r = post(BHT, "/finance/clinic/money/%s/other-upi" % D, amount="100")
ck("bhati cannot post other-UPI (302 at the gate)", s == 302)
s, h, r = get(ALI, "/finance/physio")
ck("alisha (reception): the physio table in English", s == 200 and "the revenue table" in h)
s, h, r = get(MNJ, "/finance/physio")
ck("manoj: the physio table, English", s == 200 and "the revenue table" in h)
ck("a stray clinic row for bhati is deactivated by the seed", True)
dbx("INSERT INTO unit_role (unit, username, role, active, note) VALUES ('clinic','bhati','maker',1,'walk: stray')")
r3 = subprocess.run([sys.executable, "-B", os.path.join(KIT, "seed_s249.py"), DB], capture_output=True, text=True)
ck("... proven: the stray row is deactivated and printed", "DEACTIVATED stray row clinic/bhati" in r3.stdout
   and not dbq("SELECT 1 FROM unit_role WHERE unit='clinic' AND username='bhati' AND active=1"), r3.stdout)
s, h, r = get(BHT, "/finance/clinic/register")
ck("... and bhati is refused again", s == 302)

# ================================================================ 2 F-459: one online figure
print("\n-- 2 F-459: the one 'our online' figure (the 12-Sep shape)")
# Docterz's day: online 2,050 (bill 2353-shaped), 600, 500; cash 700 (incl. a 100 that was really UPI), card 400;
# one split bill 2,000 = 1,400 online + 600 cash.  Sheet online bucket = 3,150 (the S240 figure); true online = 4,550.
tender_json = json.dumps({"Online Payment": 315000, "Cash": 70000, "Debit Card": 40000, "Split Payment": 200000})
dbx("INSERT INTO clinic_day_revenue (business_date, source_file, source_id, source_mtime, taken_at, cons_count, cons_amount_p, "
    "xray_count, xray_amount_p, proc_count, proc_amount_p, total_count, total_amount_p, morning, evening, free_revisits, "
    "free_concession, f93_phantom_rows, tender_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
    D, "Day_Revenue.xlsx", "id", "m", "t", 5, 315000, 2, 100000, 2, 210000, 9, 625000, 6, 3, 1, 0, 0, tender_json)
lines = [("consult", 1, "Fauzia", "8067", 205000, "Online Payment", "morning"),
         ("consult", 2, "Ajay Mali", "8101", 60000, "Online Payment", "morning"),
         ("consult", 3, "Rani", "8102", 50000, "Online Payment", "evening"),
         ("consult", 4, "Sohan", "8103", 60000, "Cash", "morning"),
         ("consult", 5, "Kamla", "8104", 10000, "Cash", "morning"),         # the 100 that was really UPI
         ("xray", 1, "Sohan", "8103", 60000, "Cash", "morning"),
         ("xray", 2, "Meena", "8105", 40000, "Debit Card", "evening"),
         ("proc", 1, "Rahul", "8106", 200000, "Split Payment", "evening"),
         ("proc", 2, "Bina", "8107", 10000, "Cash", "evening")]
for l in lines:
    dbx("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode, shift) VALUES (?,?,?,?,?,?,?,?)", D, *l)
dbx("INSERT INTO clinic_day_tender (business_date, clinic_id, invoice_no, tender, amount_p) VALUES (?,?,?,?,?)", D, "8106", "2360", "Online Payment", 140000)
dbx("INSERT INTO clinic_day_tender (business_date, clinic_id, invoice_no, tender, amount_p) VALUES (?,?,?,?,?)", D, "8106", "2360", "Cash", 60000)
# the bank: 600, 500, 1,400 paired; a 100 nobody billed online (it was rung as cash); NOT the 2,050 (it went to a personal phone)
dbx("INSERT INTO upi_statement (merchant_id, unit, statement_date, filename, parsed_total_p, txn_count, ingested_at) VALUES (?,?,?,?,?,?,?)",
    "100000000306941", "clinic", D, "x.xlsx", 260000, 4, "2026-09-13T12:21:00")
for t, amt, rrn in (("10:12", 60000, "AAAA1111"), ("10:41", 10000, "BBBB2222"), ("18:05", 50000, "CCCC3333"), ("19:10", 140000, "DDDD4444")):
    dbx("INSERT INTO upi_txn (merchant_id, unit, txn_date, amount_p, rrn, mode, txn_time) VALUES (?,?,?,?,?,?,?)", "100000000306941", "clinic", D, amt, rrn, "UPI", t)
cx = sqlite3.connect(DB); cx.row_factory = sqlite3.Row
import finance_clinic_day as FCD                                        # noqa: E402
ck("our_online_p = 4,550 (2,050 + 600 + 500 + the split's 1,400)", FCD.our_online_p(cx, D) == 455000, FCD.our_online_p(cx, D))
ck("... and clinic_money reads the same figure", CM.our_online_p(cx, D) == 455000)
live_src = io.open(os.path.join(FIN_MODS, "finance_clinic_day.py"), encoding="utf-8").read()
ck("F-459 in force: finance_clinic_day.py carries our_online_p (the S251 file is live)", "def our_online_p" in live_src)
cx.close()
s, h, r = get(MNJ, "/finance/clinic/day/%s" % D)
ck("day page 200 and it says our online is 4,550 (not the sheet's 3,150)", s == 200 and "our online (UPI) for the day is ₹ 4,550" in h and "₹ 3,150" not in h, (s, re.findall(r"our online[^<]*", h)))
ck("day page BEFORE the other-UPI is recorded: bank lower by 1,950", "bank is lower by ₹ 1,950" in h, re.findall(r"bank is [^<]*<[^<]*", h))
ck("day page links the morning match", '/finance/clinic/match/%s' % D in h)
s, h, r = get(MNJ, "/finance/clinic/day/%s/mpr" % D)
ck("MPR page: the same 4,550 and the same 1,950", s == 200 and "₹ 4,550" in h and "bank lower by ₹ 1,950" in h, re.findall(r"Our online[^<]*<[^<]*<[^<]*", h))
ck("MPR page: 3 paired, 1 bank-only, 1 ours-only", "the same amount on both sides (3)" in h and "NOT IN OUR ONLINE ENTRIES (1 " in h and "NOT IN THE BANK (1 " in h)

# ================================================================ 3 the counter sheet: physio hand-over, the other-UPI box
print("\n-- 3 the counter sheet")
s, h, r = get(ALI, "/finance/clinic/register/%s" % D)
ck("register card 200 with the other-UPI box, the physio hand-over select, no float block yet", s == 200 and 'id="otherupi"' in h
   and "physio_handed_to" in h and 'id="float"' not in h and "morning match" in h, (s, h[:100]))
# S254: the phone layout -- every head on its own row, three equal boxes beneath; the extras folded and closed on a plain day
ck("S254: each head is a label row + a row of three boxes (4 heads + physio = 5 label rows, 5 box rows)",
   h.count("<tr class='head'>") == 5 and h.count("<tr class='boxes'>") == 5 and "<thead><tr><th>Cash</th><th>UPI</th><th>Card</th>" in h, (h.count("<tr class='head'>"), h.count("<tr class='boxes'>")))
ck("S254: no empty first column, the separator spans three", "<th></th><th>Cash</th>" not in h and '<td colspan="3">kept separately at reception' in h)
ck("S254: the other-UPI box, the hand-over count and the three records are FOLDS, all closed on a plain day",
   '<details class="card" id="otherupi"><summary>ICICI UPI not working?' in h and '<details class="card"><summary>End of day — cash handed over' in h
   and '<details class="card"><summary>The three records, side by side' in h and 'open><summary>' not in h,
   re.findall(r"<details[^>]*><summary>[^<]*", h))
ck("S254: the main card is NOT a fold (the sheet itself is always open)", '<div class="card"><h2>12-Sep-2026</h2>' in h)
# reception's sheet: cons cash 700 (Sohan 600 + Kamla 100), cons upi 3,150; xray cash 600, card 400; proc cash 700 (100 + split 600), upi 1,400
s, h, r = post(ALI, "/finance/clinic/register/%s" % D, cons_cash_p="700", cons_upi_p="3150", cons_card_p="", xray_cash_p="600", xray_upi_p="",
               xray_card_p="400", proc_cash_p="700", proc_upi_p="1400", proc_card_p="", dress_cash_p="", dress_upi_p="", dress_card_p="",
               physio_cash_p="1800", physio_upi_p="0", physio_handed_to="Dr Bhawna", note="")
ck("sheet saved", s == 200 and "Saved." in h, (s, re.findall(r"class='bad'[^<]*", h)))
pr = dbq("SELECT * FROM clinic_physio_day WHERE business_date=?", D)
ck("physio 1,800 cash, handed to Dr Bhawna, stamped", pr and pr[0]["cash_p"] == 180000 and pr[0]["handed_to"] == "Dr Bhawna" and pr[0]["handed_at"], [dict(x) for x in pr])
ck("the three records line: register and Docterz agree on UPI, the BANK differs (before the other-UPI is recorded)",
   "the BANK differs" in h or "bank differs" in h.lower(), re.findall(r"class=\"verdict [^\"]*\">[^<]*", h))
# the other-UPI box: the amount is the only compulsory field
s, h, r = post(ALI, "/finance/clinic/money/%s/other-upi" % D, amount="", app="PhonePe", phone="Shivani ka phone", reason="a_while")
ck("blank amount: 400, nothing saved", s == 400 and "Nothing was saved" in h and not dbq("SELECT 1 FROM clinic_other_upi"))
s, h, r = post(ALI, "/finance/clinic/money/%s/other-upi" % D, amount="2050", app="PhonePe", phone="Shivani ka phone", bill_no="2353", reason="a_while")
ck("2,050 recorded; back to the sheet", s == 302 and "/finance/clinic/register/%s#otherupi" % D in r.headers.get("Location", ""), (s, r.headers.get("Location")))
ou = dbq("SELECT * FROM clinic_other_upi WHERE business_date=?", D)
od = dbq("SELECT * FROM clinic_other_upi_day WHERE business_date=?", D)
ck("row: 2,050 PhonePe, the phone, bill 2353, by alisha; the day's reason 'a while'", len(ou) == 1 and ou[0]["amount_p"] == 205000
   and ou[0]["phone"] == "Shivani ka phone" and ou[0]["bill_no"] == "2353" and ou[0]["entered_by"] == "alisha" and od[0]["reason"] == "a_while")
s, h, r = get(ALI, "/finance/clinic/register/%s" % D)
ck("the sheet lists it, remembers the phone and the app, offers '+ add another'", "2,050" in h and "Shivani ka phone" in h and "+ add another" in h
   and "<option value='Shivani ka phone'>" in h)
ck("S254: with a payment recorded the other-UPI fold is OPEN and its line says what is recorded",
   '<details class="card" id="otherupi" open><summary>ICICI UPI not working? &rarr; Paid to another UPI · &#8377; 2,050 recorded</summary>' in h, re.findall(r"<details[^>]*id=\"otherupi\"[^>]*><summary>[^<]*", h))
s2, h2, r2 = get(MNJ, "/finance/clinic/day/%s" % D)
ck("day page AFTER: 'of which ₹ 2,050 went to another UPI', expected 2,500, bank higher by 100, link to the match",
   "of which ₹ 2,050 went to another UPI" in h2 and "₹ 2,500 is expected in the bank" in h2 and "bank is higher by ₹ 100" in h2 and "/finance/clinic/match/%s" % D in h2,
   re.findall(r"our online[^<]*", h2))
ck("the three records line names the 2,050 kept out; the bank still differs -- by the 100 rung as cash (the drawer closes that loop below)",
   "2,050 other UPI kept out" in h and "the BANK differs" in h, re.findall(r"class=\"verdict [^\"]*\">[^<]*", h))
s, h, r = post(ALI, "/finance/clinic/money/%s/other-upi" % D, amount="300", app="Google Pay", phone="Alisha ka phone", reason="a_while")
s, h, r = post(ALI, "/finance/clinic/money/%s/other-upi" % D, **{"del": str(dbq("SELECT id FROM clinic_other_upi WHERE amount_p=30000")[0]["id"])})
ck("add another, then remove it: one row again", s == 302 and len(dbq("SELECT * FROM clinic_other_upi WHERE business_date=?", D)) == 1)
ck("every write is audited", len(dbq("SELECT * FROM audit_log WHERE table_name='clinic_other_upi'")) >= 3)

# ================================================================ 4 the reconciler
print("\n-- 4 the reconciler: four passes and the explanation layer")
cx = sqlite3.connect(DB); cx.row_factory = sqlite3.Row
m = CM.match_day(cx, D)
ck("verdict: nothing to do", m["verdict"] == "nothing_to_do", (m["verdict"], m["flags"], m["lines"]))
ck("pass 1: counter 6,950 = Docterz 6,950 (physio out)", m["p1"]["counter_p"] == 695000 and m["p1"]["docterz_p"] == 695000 and m["p1"]["diff_p"] == 0, m["p1"])
ck("expected in the bank = 4,550 - 2,050 = 2,500", m["expected_bank_p"] == 250000)
codes = [e["code"] for e in m["explained"]]
ck("explained: the other UPI (paired with Fauzia's 2,050) and the 100 rung as cash", codes == ["other_upi", "rung_as_cash"], m["explained"])
ck("the other-UPI line names the entry and says 'not in the bank by nature'", "Fauzia" in m["explained"][0]["text"] and "Not in the bank by nature" in m["explained"][0]["text"])
ck("the rung-as-cash line names Kamla's 100 at 10:41", "Kamla" in m["explained"][1]["text"] and "10:41" in m["explained"][1]["text"], m["explained"][1])
ck("notes: physiotherapy kept out", any("Physiotherapy" in n for n in m["notes"]), m["notes"])
ck("no flag at all", m["flags"] == [])
# the takeaway on the staff card
s, h, r = get(ALI, "/finance/clinic/match/%s" % D)
ck("staff card 200, no JavaScript, ONE plain sentence on top", s == 200 and "<script" not in h.lower()
   and "Saturday 12-Sep: the counter sheet, Docterz and the bank agree. Nothing to do." in h, (s, re.findall(r"verdict [^\"]*\"[^>]*>[^<]*", h)))
ck("the working is folded: 'Explained (2)' and 'Show the numbers' are <details>; no 'Needs a person' card; no bank arithmetic outside the folds",
   "<details class='card'><summary>Explained (2) — nothing to do</summary>" in h and '<details class="card"><summary>Show the numbers</summary>' in h
   and "Needs a person" not in h and h.index("Bank expects") > h.index("Show the numbers"), re.findall(r"<summary>[^<]*", h))
ck("the numbers, when opened, are all still there", "3 paired, 1 bank-only, 0 ours-only" in h and "Bank has" in h)
ck("no minus-sign arithmetic before the folds (the top of the page is words only)", "−₹" not in h[:h.index("<details")])
ck("reception's button: First pass done (enabled)", "First pass done</button>" in h and "disabled>First pass done" not in h)
s, h, r = post(ALI, "/finance/clinic/match/%s" % D, act="pass1")
ck("alisha: first pass done", s == 200 and "First pass done." in h and dbq("SELECT status FROM clinic_money_day WHERE business_date=?", D)[0]["status"] == "maker_done")
s, h, r = get(SHZ, "/finance/clinic/match/%s" % D)
ck("shavez (the named checker) sees 'Close the day — checked'", "Close the day — checked" in h)
s, h, r = post(ALI, "/finance/clinic/match/%s" % D, act="pass2")
ck("alisha cannot close: only the checker", "Only the checker" in h)
s, h, r = post(SHZ, "/finance/clinic/match/%s" % D, act="pass2")
st = dbq("SELECT * FROM clinic_money_day WHERE business_date=?", D)[0]
ck("shavez closes: two passes, alisha then shavez", "Day closed." in h and st["status"] == "closed" and st["maker"] == "alisha" and st["checker"] == "shavez" and not st["one_pass"])

# ---- 4b a day with a real difference: the counter is one 600 consultation ahead ----
tj = json.dumps({"Online Payment": 110000, "Cash": 60000})
dbx("INSERT INTO clinic_day_revenue (business_date, source_file, source_id, source_mtime, taken_at, cons_count, cons_amount_p, "
    "xray_count, xray_amount_p, proc_count, proc_amount_p, total_count, total_amount_p, morning, evening, free_revisits, "
    "free_concession, f93_phantom_rows, tender_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
    D2, "Day_Revenue.xlsx", "id2", "m", "t", 3, 170000, 0, 0, 0, 0, 3, 170000, 3, 0, 0, 0, 0, tj)
for l in (("consult", 1, "A", "9001", 60000, "Online Payment", "morning"), ("consult", 2, "B", "9002", 50000, "Online Payment", "morning"),
          ("consult", 3, "C", "9003", 60000, "Cash", "morning")):
    dbx("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode, shift) VALUES (?,?,?,?,?,?,?,?)", D2, *l)
dbx("INSERT INTO upi_statement (merchant_id, unit, statement_date, filename, parsed_total_p, txn_count, ingested_at) VALUES (?,?,?,?,?,?,?)",
    "100000000306941", "clinic", D2, "y.xlsx", 110000, 2, "2026-09-12T12:21:00")
for t, amt, rrn in (("10:12", 60000, "EEEE5555"), ("11:41", 50000, "FFFF6666")):
    dbx("INSERT INTO upi_txn (merchant_id, unit, txn_date, amount_p, rrn, mode, txn_time) VALUES (?,?,?,?,?,?,?)", "100000000306941", "clinic", D2, amt, rrn, "UPI", t)
s, h, r = post(ALI, "/finance/clinic/register/%s" % D2, cons_cash_p="1200", cons_upi_p="1100", cons_card_p="", xray_cash_p="", xray_upi_p="", xray_card_p="",
               proc_cash_p="", proc_upi_p="", proc_card_p="", dress_cash_p="", dress_upi_p="", dress_card_p="", physio_cash_p="", physio_upi_p="", physio_handed_to="")
m = CM.match_day(cx, D2)
ck("D2: ONE flag, in plain words -- 'The counter sheet has ₹600 more than Docterz — consultation ₹600 more. Most likely: the counter has one consultation more than Docterz.'",
   len(m["flags"]) == 1 and m["flags"][0]["code"] == "total_diff"
   and m["flags"][0]["text"] == "The counter sheet has ₹600 more than Docterz — consultation ₹600 more. Most likely: the counter has one consultation more than Docterz.", m["flags"])
ck("D2: the sentence on top says the same", "Friday 11-Sep: the counter sheet has ₹600 more than Docterz. Everything else matches or is explained." in " ".join(m["lines"]), m["lines"])
ck("D2: the flag is a staff flag, not the owner's", not m["flags"][0]["owner"])
s, h, r = get(ALI, "/finance/clinic/match/%s" % D2)
fid = dbq("SELECT id FROM clinic_money_flag WHERE business_date=? AND code='total_diff'", D2)[0]["id"]
ck("the flag persists in clinic_money_flag, open, with the answer form; 'First pass done' is disabled until answered",
   "Needs a person</h2>" in h and "Cannot explain" in h and "disabled>First pass done" in h and "zyada hai — kya hua tha" in h, re.findall(r"<button[^>]*>First pass[^<]*", h))
s, h, r = post(ALI, "/finance/clinic/match/%s" % D2, act="pass1")
ck("pass 1 refused while a flag is unanswered", "Not yet" in h)
s, h, r = post(ALI, "/finance/clinic/match/%s" % D2, act="answer", flag=str(fid), explanation="")
ck("an empty explanation is refused (write it, or press Cannot explain)", "Nothing was saved" in h)
s, h, r = post(ALI, "/finance/clinic/match/%s" % D2, act="answer", flag=str(fid), explanation="Sohan ka 600 register mein do baar likha gaya")
ck("explained by alisha", dbq("SELECT status, explained_by FROM clinic_money_flag WHERE id=?", fid)[0]["status"] == "explained")
s, h, r = post(ALI, "/finance/clinic/match/%s" % D2, act="pass1")
ck("pass 1 done", "First pass done." in h)
s, h, r = get(SHZ, "/finance/clinic/match/%s" % D2)
ck("shavez sees her line and Agree / Disagree", "do baar likha" in h and 'value="agree"' in h and 'value="disagree"' in h)
s, h, r = post(SHZ, "/finance/clinic/match/%s" % D2, act="pass2")
ck("pass 2 refused until his word is given", "Not yet" in h)
s, h, r = post(SHZ, "/finance/clinic/match/%s" % D2, act="verdict", flag=str(fid), word="agree")
ck("agree on an explained staff flag -> reconciled", dbq("SELECT status, reconciled_by FROM clinic_money_flag WHERE id=?", fid)[0]["status"] == "reconciled")
s, h, r = post(SHZ, "/finance/clinic/match/%s" % D2, act="pass2")
ck("day closed on two passes; nothing reached the owner", "Day closed." in h and not CM.owner_queue(cx))
# the flag STAYS (never deleted); a corrected sheet clears it by the data
s, h, r = post(ALI, "/finance/clinic/register/%s" % D2, cons_cash_p="600", cons_upi_p="1100", cons_card_p="", xray_cash_p="", xray_upi_p="", xray_card_p="",
               proc_cash_p="", proc_upi_p="", proc_card_p="", dress_cash_p="", dress_upi_p="", dress_card_p="", physio_cash_p="", physio_upi_p="", physio_handed_to="")
get(ALI, "/finance/clinic/match/%s" % D2)
ck("a reconciled flag is kept as the record even after the sheet is corrected", dbq("SELECT status FROM clinic_money_flag WHERE id=?", fid)[0]["status"] == "reconciled")

# ---- 4c the checker alone: one pass only; 'cannot explain' reaches the owner ----
tj = json.dumps({"Online Payment": 50000, "Cash": 60000})
dbx("INSERT INTO clinic_day_revenue (business_date, source_file, source_id, source_mtime, taken_at, cons_count, cons_amount_p, "
    "xray_count, xray_amount_p, proc_count, proc_amount_p, total_count, total_amount_p, morning, evening, free_revisits, "
    "free_concession, f93_phantom_rows, tender_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
    D3, "Day_Revenue.xlsx", "id3", "m", "t", 2, 110000, 0, 0, 0, 0, 2, 110000, 2, 0, 0, 0, 0, tj)
for l in (("consult", 1, "P", "9101", 50000, "Online Payment", "morning"), ("consult", 2, "Q", "9102", 60000, "Cash", "morning")):
    dbx("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode, shift) VALUES (?,?,?,?,?,?,?,?)", D3, *l)
dbx("INSERT INTO upi_statement (merchant_id, unit, statement_date, filename, parsed_total_p, txn_count, ingested_at) VALUES (?,?,?,?,?,?,?)",
    "100000000306941", "clinic", D3, "z.xlsx", 0, 0, "2026-09-11T12:21:00")
s, h, r = post(SHZ, "/finance/clinic/register/%s" % D3, cons_cash_p="600", cons_upi_p="500", cons_card_p="", xray_cash_p="", xray_upi_p="", xray_card_p="",
               proc_cash_p="", proc_upi_p="", proc_card_p="", dress_cash_p="", dress_upi_p="", dress_card_p="", physio_cash_p="", physio_upi_p="", physio_handed_to="")
os.environ["CLINIC_MONEY_NOW"] = "2026-09-13T09:30:00"           # D3 + 2 banking days (Sat 12-Sep) at 12:20 has passed
m = CM.match_day(cx, D3)
ck("D3: P's 500 never reached the bank after two banking days -> an OWNER flag (money that never lands)",
   len(m["flags"]) == 1 and m["flags"][0]["code"] == "not_in_bank" and m["flags"][0]["owner"], m["flags"])
os.environ["CLINIC_MONEY_NOW"] = "2026-09-11T13:00:00"           # the morning after D3, MPR just in: still unsettled
m2 = CM.match_day(cx, D3)
ck("... but the morning after it is only a note: 'still to reach it'", m2["flags"] == [] and any("not in the bank yet" in n for n in m2["notes"]), (m2["flags"], m2["notes"]))
os.environ["CLINIC_MONEY_NOW"] = "2026-09-13T09:30:00"
s, h, r = get(SHZ, "/finance/clinic/match/%s" % D3)
ck("shavez, reception absent: the button says one pass only", "one pass only" in h and "Close the day — one pass only (shavez)" in h)
ck("an owner-level flag does not block his pass", "disabled>Close the day" not in h)
s, h, r = post(SHZ, "/finance/clinic/match/%s" % D3, act="pass1")
st = dbq("SELECT * FROM clinic_money_day WHERE business_date=?", D3)[0]
ck("closed on one pass, marked so", "one pass" in h and st["one_pass"] == 1 and st["status"] == "closed" and st["maker"] == "shavez")
q = CM.owner_queue(cx)
ck("the owner's queue holds exactly that one: money that never landed", len(q) == 1 and q[0]["code"] == "not_in_bank" and q[0]["status"] == "to_owner", [dict(x) for x in q])

# ---- 4d the sheet not filled ----
D4 = "2026-09-09"
os.environ["CLINIC_MONEY_NOW"] = "2026-09-10T09:00:00"
m = CM.match_day(cx, D4)
ck("D4 unfilled, the morning after: one staff flag, nothing else", len(m["flags"]) == 1 and m["flags"][0]["code"] == "not_filled" and not m["flags"][0]["owner"], m["flags"])
os.environ["CLINIC_MONEY_NOW"] = "2026-09-10T15:00:00"
m = CM.match_day(cx, D4)
ck("D4 unfilled after 14:00 the next day: the owner's flag", m["flags"][0]["owner"])
get(SHZ, "/finance/clinic/match/%s" % D4)
ck("... and it is in his queue", any(x["code"] == "not_filled" for x in CM.owner_queue(cx)))
os.environ["CLINIC_MONEY_NOW"] = "2026-09-13T09:30:00"

# ---- 4e a small difference is a note; a tender swap is explained ----
D5 = "2026-09-08"
tj = json.dumps({"Online Payment": 60000, "Debit Card": 50000})
dbx("INSERT INTO clinic_day_revenue (business_date, source_file, source_id, source_mtime, taken_at, cons_count, cons_amount_p, "
    "xray_count, xray_amount_p, proc_count, proc_amount_p, total_count, total_amount_p, morning, evening, free_revisits, "
    "free_concession, f93_phantom_rows, tender_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
    D5, "Day_Revenue.xlsx", "id5", "m", "t", 2, 110000, 0, 0, 0, 0, 2, 110000, 2, 0, 0, 0, 0, tj)
for l in (("consult", 1, "R", "9201", 60000, "Online Payment", "morning"), ("consult", 2, "S", "9202", 50000, "Debit Card", "morning")):
    dbx("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode, shift) VALUES (?,?,?,?,?,?,?,?)", D5, *l)
dbx("INSERT INTO upi_statement (merchant_id, unit, statement_date, filename, parsed_total_p, txn_count, ingested_at) VALUES (?,?,?,?,?,?,?)",
    "100000000306941", "clinic", D5, "w.xlsx", 60000, 1, "2026-09-09T12:21:00")
dbx("INSERT INTO upi_txn (merchant_id, unit, txn_date, amount_p, rrn, mode, txn_time) VALUES (?,?,?,?,?,?,?)", "100000000306941", "clinic", D5, 60000, "GGGG7777", "UPI", "10:00")
post(ALI, "/finance/clinic/register/%s" % D5, cons_cash_p="", cons_upi_p="1100", cons_card_p="", xray_cash_p="", xray_upi_p="", xray_card_p="",
     proc_cash_p="", proc_upi_p="", proc_card_p="", dress_cash_p="", dress_upi_p="", dress_card_p="", physio_cash_p="", physio_upi_p="", physio_handed_to="")
m = CM.match_day(cx, D5)
ck("D5 tender swap: 500 under UPI on the counter, card in Docterz -> explained, no flag", m["flags"] == [] and any(e["code"] == "tender_swap" and "₹500" in e["text"] for e in m["explained"]), (m["flags"], m["explained"]))
post(ALI, "/finance/clinic/register/%s" % D5, cons_cash_p="50", cons_upi_p="600", cons_card_p="500", xray_cash_p="", xray_upi_p="", xray_card_p="",
     proc_cash_p="", proc_upi_p="", proc_card_p="", dress_cash_p="", dress_upi_p="", dress_card_p="", physio_cash_p="", physio_upi_p="", physio_handed_to="")
m = CM.match_day(cx, D5)
ck("D5 counter 50 over: under Rs 100 is a note, never a flag", m["flags"] == [] and any("Under ₹100" in n for n in m["notes"]), (m["flags"], m["notes"]))

# ---- 4f the real 12-Sep shape (owner, 13-Sep): a Rs 50 blood sugar under X-ray in Docterz, under procedures on the counter;
#      a Rs 600 card payment written as cash; one consultation extra on the counter
D7 = "2026-09-07"
tj = json.dumps({"Cash": 190000, "Debit Card": 60000})
dbx("INSERT INTO clinic_day_revenue (business_date, source_file, source_id, source_mtime, taken_at, cons_count, cons_amount_p, "
    "xray_count, xray_amount_p, proc_count, proc_amount_p, total_count, total_amount_p, morning, evening, free_revisits, "
    "free_concession, f93_phantom_rows, tender_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
    D7, "Day_Revenue.xlsx", "id7", "m", "t", 2, 120000, 2, 105000, 1, 10000, 5, 250000, 5, 0, 0, 0, 0, tj)
for l in (("consult", 1, "F", "9301", 60000, "Cash", "morning"), ("consult", 2, "N", "9302", 60000, "Debit Card", "morning"),
          ("xray", 1, "F", "9301", 55000, "Cash", "morning"), ("xray", 2, "N", "9302", 50000, "Cash", "morning"),
          ("proc", 1, "A", "9303", 10000, "Cash", "morning")):
    dbx("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode, shift) VALUES (?,?,?,?,?,?,?,?)", D7, *l)
dbx("INSERT INTO upi_statement (merchant_id, unit, statement_date, filename, parsed_total_p, txn_count, ingested_at) VALUES (?,?,?,?,?,?,?)",
    "100000000306941", "clinic", D7, "v.xlsx", 0, 0, "2026-09-08T12:21:00")
# the counter: consult cash 1,800 (one extra 600 + N's card 600 written as cash), xray cash 1,000, proc cash 150 (the 100 + the 50 sugar), card 0
post(ALI, "/finance/clinic/register/%s" % D7, cons_cash_p="1800", cons_upi_p="", cons_card_p="", xray_cash_p="1000", xray_upi_p="", xray_card_p="",
     proc_cash_p="150", proc_upi_p="", proc_card_p="", dress_cash_p="", dress_upi_p="", dress_card_p="", physio_cash_p="", physio_upi_p="", physio_handed_to="")
m = CM.match_day(cx, D7)
ck("D7: the Rs 50 blood sugar is EXPLAINED by name (Docterz X-ray, counter procedures) -- never a difference",
   any(e["code"] == "head_move" and e["text"] == "₹50 blood sugar test — Docterz counts it under X-ray, the counter under procedures + dressing. Same money." for e in m["explained"]), m["explained"])
ck("D7: after the move, the heads read consult +600 only (X-ray and procedures agree)", [(h, x) for h, _a, _b, x in m["p2"]] == [("consult", 60000), ("xray", 0), ("proc", 0)], m["p2"])
ck("D7: ONE flag in plain words with the likely cause: card written as cash, one consultation more",
   len(m["flags"]) == 1 and m["flags"][0]["text"] == "The counter sheet has ₹600 more than Docterz — consultation ₹600 more. Most likely: ₹600 paid by card was written as cash; the counter has one consultation more than Docterz.", m["flags"])
cx.close()

# ================================================================ 5 the float (S252 flow)
print("\n-- 5 the float: zero taps on a normal day; one tap to replenish; one line to monitor")
s, h, r = get(MNJ, "/finance/clinic/money")
ck("owner page 200: the float not issued yet (one line, top card); the queue shows the two owner items",
   s == 200 and "Not issued yet — see the last card" in h and "money that never landed" in h and "sheet unfilled after the day" in h, (s, re.findall(r"— [a-z ]*</p>", h)[:5]))
s, h, r = post(MNJ, "/finance/clinic/money", act="float", kind="issue", n200="5", n100="10", n50="10", given_to="reception", date="2026-09-12")
ck("issued 2,500 (5x200 + 10x100 + 10x50) on 12-Sep", s == 200 and "Float issue: ₹2,500 recorded" in h and "not revenue" in h, re.findall(r"class='(?:ok|bad)'>[^<]*", h))
ck("the one line now: 'Float ₹2,500 intact.'", "Float ₹2,500 intact." in h, re.findall(r"class='verdict [^']*'>[^<]*", h)[:2])
cx = sqlite3.connect(DB); cx.row_factory = sqlite3.Row
import clinic_register as CR                                            # noqa: E402
ck("standing 2,500; the day's collection is UNCHANGED (register cash 2,000 + physio 1,800 = 3,800)",
   CM.float_standing_p(cx) == 250000 and CR.expected_cash_p(cx, D) == 380000, (CM.float_standing_p(cx), CR.expected_cash_p(cx, D)))
ck("no count at all: the handover expectation equals the collection (a normal day needs no tap)", CR.expected_handover_p(cx, D) == 380000 and CM.float_owed(cx) is None)
s, h, r = get(ALI, "/finance/clinic/register/%s" % D)
ck("S254: the float is a CLOSED fold on a plain day and its line carries the instruction and the hand-over figure",
   '<details class="card" id="float"><summary>Float — alag rakho 5 × ₹200, 10 × ₹100, 10 × ₹50 · hand over &#8377; 3,800</summary>' in h, re.findall(r"<details[^>]*id=\"float\"[^>]*><summary>[^<]*", h))
ck("S254: the hand-over fold's line says 3,800 to hand over", "<summary>End of day — cash handed over · &#8377; 3,800 to hand over</summary>" in h, re.findall(r"<summary>End of day[^<]*", h))
ck("the sheet: ONE line -- keep aside 5 x 200, 10 x 100, 10 x 50, hand over 3,800; no boxes; a 'nahi' link; three change buttons",
   'id="float"' in h and "Kal ke liye alag rakho: <b>5 × ₹200, 10 × ₹100, 10 × ₹50</b>" in h and "Baaki <b>₹ 3,800</b> hand over karo" in h
   and ("name='n200' value='' inputmode='numeric' pattern='[0-9]*' autocomplete='off' class='amt'>") not in h and "poora nahi rakh paaye" in h and h.count("ke note chahiye") == 3, (s, re.findall(r"class='verdict'>[^<]*<b>[^<]*", h)))
# the drawer count that night: 3,700 in hand (Kamla's 100 was really UPI) -> 100 less; the bank is 100 over -> the loop closes
s, h, r = post(ALI, "/finance/clinic/register/%s" % D, drawer="count", n500="7", n100="2", n50="0", n200="0", n20="0", n10="0")
ck("drawer 3,700 counted against a 3,800 handover: '100 less in the drawer'", "100 less in the drawer" in h, re.findall(r"class='(?:ok|bad)'>[^<]*", h))
ck("S254: after a count the hand-over fold is open and its line says counted 3,700", '<details class="card" open><summary>End of day — cash handed over · counted &#8377; 3,700</summary>' in h, re.findall(r"<summary>End of day[^<]*", h))
ck("... and the S224 loop closes, other-UPI aware: short by exactly what the bank is over, 'No money is missing'",
   "The drawer is short by exactly what the bank is over — ₹100" in h and "No money is missing" in h, re.findall(r"class='verdict[^>]*>[^<]*", h))
# a change request: one tap
s, h, r = post(ALI, "/finance/clinic/money/%s/float" % D, mode="need", need="n50")
ck("'₹50 ke note chahiye' -> recorded, the day counted as intact, back to the sheet", s == 302 and dbq("SELECT need, kept_p FROM clinic_float_day WHERE business_date=?", D)[0]["need"] == "₹50 ke note"
   and dbq("SELECT kept_p FROM clinic_float_day WHERE business_date=?", D)[0]["kept_p"] == 250000)
s, h, r = get(MNJ, "/finance/clinic/money")
ck("owner: the line says intact + change asked 12-Sep ₹50 ke note; one 'Change given' tap", "intact" in h and "Change asked 12-Sep-2026: ₹50 ke note" in h and "Change given — ₹50 ke note" in h, re.findall(r"class='verdict [^']*'>[^<]*", h)[:1])
s, h, r = post(MNJ, "/finance/clinic/money", act="need_given")
ck("tap: change given; the request closes", "Change given" in h and dbq("SELECT need_done FROM clinic_float_day WHERE business_date=?", D)[0]["need_done"].startswith("manoj") and CM.float_change_asked(cx) is None)
# the next day the float comes up short: 'nahi' -> three boxes -> kept 2,000 -> 500 released into the handover
D6 = "2026-09-13"
post(ALI, "/finance/clinic/register/%s" % D6, cons_cash_p="1000", cons_upi_p="", cons_card_p="", xray_cash_p="", xray_upi_p="", xray_card_p="",
     proc_cash_p="", proc_upi_p="", proc_card_p="", dress_cash_p="", dress_upi_p="", dress_card_p="", physio_cash_p="", physio_upi_p="", physio_handed_to="")
s, h, r = get(ALI, "/finance/clinic/register/%s?float=short" % D6)
ck("'nahi' opens exactly three boxes (200 / 100 / 50), nothing else", h.count("class='amt'></td><td class='mut'>poora:") == 3
   and ("name='n500' value='' inputmode='numeric' pattern='[0-9]*' autocomplete='off' class='amt'>") not in h and ("name='n20' value='' inputmode='numeric' pattern='[0-9]*' autocomplete='off' class='amt'>") not in h)
s, h, r = post(ALI, "/finance/clinic/money/%s/float" % D6, mode="short", n200="5", n100="10", n50="0")
ck("D6: opened 2,500, kept 2,000 -> +500 released; handover 1,000 + 500 = 1,500", s == 302 and CM.float_open_p(cx, D6) == 250000 and CM.float_adjust_p(cx, D6) == 50000
   and CR.expected_handover_p(cx, D6) == 150000, (CM.float_open_p(cx, D6), CM.float_adjust_p(cx, D6), CR.expected_handover_p(cx, D6)))
s, h, r = get(ALI, "/finance/clinic/register/%s" % D6)
ck("S254: a short day opens the float fold by itself", '<details class="card" id="float" open>' in h)
ck("the sheet says: 2,000 rakha, 500 kam, the doctors know; the handover line names the release",
   "₹ 2,000 rakha — ₹ 500 kam" in h and "released from the float" in h, re.findall(r"class='verdict [^']*'>[^<]*", h))
owed = CM.float_owed(cx)
ck("what is owed is worked out: ₹500 = 10 x ₹50, since 13-Sep by alisha", owed and owed["short_p"] == 50000 and owed["notes"] == {"n50": 10} and owed["since"] == D6 and owed["by"] == "alisha", owed)
s, h, r = get(MNJ, "/finance/clinic/money")
ck("owner's one line: '₹2,000 — ₹500 short since 13-Sep (alisha). Give reception: 10 × ₹50.' and the Given tap",
   "Float ₹2,000 — ₹500 short since 13-Sep-2026 (alisha). Give reception: 10 × ₹50." in h and "Given — 10 × ₹50" in h, re.findall(r"class='verdict [^']*'>[^<]*", h)[:1])
s, h, r = get(BHW, "/finance/clinic/money")
ck("Dr Bhawna sees the same line and the same tap", "Give reception: 10 × ₹50" in h and "Given — 10 × ₹50" in h)
m = CM.match_day(cx, D)
ck("the match notes the float and does not flag it", any("float was kept aside" in n for n in m["notes"]) and not any("float" in f["text"].lower() for f in m["flags"]))
os.environ["CLINIC_MONEY_NOW"] = "2026-09-14T09:00:00"
s, h, r = post(BHW, "/finance/clinic/money", act="float_given")
ck("ONE TAP by Dr Bhawna: top-up 500 recorded as 10 x 50, dated the 14th; the float opens at 2,500 again",
   "Recorded: ₹500 given to reception (10 × ₹50)" in h and CM.float_open_p(cx, "2026-09-14") == 250000 and CM.float_owed(cx) is None
   and dbq("SELECT kind, amount_p, n50, by_whom FROM clinic_float_event ORDER BY id DESC LIMIT 1")[0]["kind"] == "topup", (re.findall(r"class='(?:ok|bad)'>[^<]*", h), CM.float_open_p(cx, "2026-09-14")))
ck("standing is still 2,500 (a top-up restores, never raises)", CM.float_standing_p(cx) == 250000)
s, h, r = post(MNJ, "/finance/clinic/money", act="float_given")
ck("a second tap does nothing: 'already intact'", "already intact" in h and dbq("SELECT COUNT(*) c FROM clinic_float_event WHERE kind='topup'")[0]["c"] == 1)
s, h, r = get(MNJ, "/finance/clinic/money?m=2026-09")
ck("owner's line back to intact, naming the last short day made up; month line: short on 1 day (₹ 500 made up); change asked on 1 day",
   "Float ₹2,500 intact — last short day 13-Sep-2026, made up." in h and "short on 1 day (₹ 500 made up); change asked on 1 day" in h, re.findall(r"class='verdict [^']*'>[^<]*", h)[:1])
s, h, r = get(ALI, "/finance/clinic/register/2026-09-14")
ck("the 14th: the sheet is back to the one line, hand over = collection (no register yet: no figure), no boxes", "Kal ke liye alag rakho" in h and ("name='n200' value='' inputmode='numeric' pattern='[0-9]*' autocomplete='off' class='amt'>") not in h and "kam tha" not in h)
os.environ["CLINIC_MONEY_NOW"] = "2026-09-13T09:30:00"
s, h, r = get(SHZ, "/finance/clinic/money")
ck("S252: the named checker (shavez, who also holds clinic checker on the box) is refused the owner's page", "Not permitted" in h)
cx.close()

# ================================================================ 6 physiotherapy
print("\n-- 6 the physiotherapy table")
dbx("INSERT INTO clinic_physio_day (business_date, cash_p, upi_p, entered_by, entered_at, handed_to, handed_at) VALUES ('2026-08-20', 120000, 30000, 'alisha', 'x', 'Dr Manoj', 'x')")
s, h, r = get(BHT, "/finance/physio")
ck("bhati: September open, August folded; Hindi headings; 1,800 on the 12th, handed to Dr Bhawna, 'abhi nahi'",
   s == 200 and "<details class=\"card\" open><summary><b>September 2026</b>" in h and "<details class=\"card\"><summary><b>August 2026</b>" in h
   and "Tareekh" in h and "1,800" in h and "Dr Bhawna" in h and "abhi nahi" in h and "Saal 2026" in h, (s, re.findall(r"<summary>[^<]*<b>[^<]*", h)))
ck("bhati sees NO doctor's revenue, no patient, no bank word", "Fauzia" not in h and "Docterz" not in h and not re.search(r"\bbank\b", h, re.I) and "6,950" not in h)
s, h, r = get(MNJ, "/finance/physio")
ck("manoj: a Received button on the 12th", "action='/finance/physio/received/%s'" % D in h)
s, h, r = post(BHW, "/finance/physio/received/%s" % D)
pr = dbq("SELECT * FROM clinic_physio_day WHERE business_date=?", D)[0]
ck("Dr Bhawna taps received: stamped, redirect", s == 302 and pr["received_by"] == "bhawna" and pr["received_at"])
s, h, r = get(BHT, "/finance/physio")
ck("bhati now sees 'mil gaya bhawna'", "mil gaya bhawna" in h)
s, h, r = post(ALI, "/finance/physio/received/%s" % "2026-08-20")
ck("reception cannot tap received (403)", s == 403)

# ================================================================ 7 the owner's line
print("\n-- 7 the owner's line")
s, h, r = get(MNJ, "/finance/clinic/money?m=2026-09")
ck("other UPI this month: 2,050, 1 payment, not yet settled; the settle button", "₹ 2,050" in h and "not yet settled" in h and "Settled — passed on" in h)
ck("physiotherapy this month: 1,800, all received", "cash ₹ 1,800" in h and "all received" in h)
ck("morning passes: 3 closed, one pass only on 10-Sep", "one pass only on 10-Sep-2026" in h, re.findall(r"Morning passes.*?</tr>", h, re.S))
rid = dbq("SELECT id FROM clinic_other_upi WHERE amount_p=205000")[0]["id"]
s, h, r = post(MNJ, "/finance/clinic/money", act="settle_upi", row=str(rid), to="Dr Manoj")
ck("settled tick", "Marked settled" in h and dbq("SELECT settled_by FROM clinic_other_upi WHERE id=?", rid)[0]["settled_by"] == "manoj")
q = CM.owner_queue(sqlite3.connect(DB)) if False else None
fid = dbq("SELECT id FROM clinic_money_flag WHERE code='not_in_bank'")[0]["id"]
s, h, r = post(MNJ, "/finance/clinic/money", act="reconcile", flag=str(fid), note="portal payment, seen in Razorpay")
ck("owner reconciles the never-landed flag with a note", "Reconciled." in h and dbq("SELECT status, owner_note FROM clinic_money_flag WHERE id=?", fid)[0]["status"] == "reconciled")
s, h, r = get(MNJ, "/finance/clinic/match")
ck("the doctor's Morning match tile lands on his own line", s == 302 and r.headers.get("Location", "").endswith("/finance/clinic/money"))
s, h, r = get(ALI, "/finance/clinic/match")
ck("reception's lands on yesterday", s == 302 and "/finance/clinic/match/2026-09-12" in r.headers.get("Location", ""), r.headers.get("Location"))
s, h, r = get(SHZ, "/finance/clinic/money")
ck("shavez (the named checker) is refused the owner's page even though he holds clinic checker", s == 200 and "Not permitted" in h)
s, h, r = get(ALI, "/finance/clinic/match/not-a-date")
ck("not a date", "Not a date" in h)
allh = "".join(get(MNJ, u)[1] for u in ("/finance/clinic/money", "/finance/clinic/match/%s" % D, "/finance/physio", "/finance/clinic/register/%s" % D))
ck("no token, no full phone number on any page", "DUMMY-TOKEN" not in allh and not re.search(r"\b[6-9]\d{9}\b", allh))

# ================================================================ 8 the portal
print("\n-- 8 the portal: who is shown what")
for f in ("portal.py", "tile_grants.json"):
    src_p = os.path.join(KIT, f) if os.path.exists(os.path.join(KIT, f)) else os.path.join(PORTAL_DIR, f)
    shutil.copyfile(src_p, os.path.join(POR, f))
for f in os.listdir(PORTAL_DIR) if os.path.isdir(PORTAL_DIR) else []:
    if f.endswith(".py") and f not in ("portal.py",) and os.path.isfile(os.path.join(PORTAL_DIR, f)):
        shutil.copyfile(os.path.join(PORTAL_DIR, f), os.path.join(POR, f))
os.environ["TILE_GRANTS_FILE"] = os.path.join(POR, "tile_grants.json")
os.environ.setdefault("PORTAL_PIN_SALT", "walk")
os.environ.setdefault("PORTAL_TOKEN_SEED", "walk")
try:
    spec = importlib.util.spec_from_file_location("portal_s249", os.path.join(POR, "portal.py"))
    PM = importlib.util.module_from_spec(spec)
    sys.path.insert(0, POR)
    spec.loader.exec_module(PM)
    ck("patched portal.py imports (every tile grouped -- its own assert); grants v16", PM._tile_grants().get("version") == 16)

    def tiles(user, role="staff"):
        return [t["name"] for _g, items in PM._visible_sections(role, False, user) for t in items]
    ck("bhati is shown Physiotherapy and nothing of Docterz, money or staff", tiles("bhati") == ["Physiotherapy"], tiles("bhati"))
    for u in ("shavez", "shivani", "alisha"):
        ck("%s is shown Morning match beside Docterz daily collection; not Physiotherapy" % u,
           "Morning match" in tiles(u) and "Docterz daily collection" in tiles(u) and "Physiotherapy" not in tiles(u), tiles(u))
    ck("bhawna is shown Physiotherapy", "Physiotherapy" in tiles("bhawna", "doctor"))
    ck("the doctor holds both by role", "Morning match" in tiles("manoj", "doctor") and "Physiotherapy" in tiles("manoj", "doctor"))
    ck("darpan and amir are not shown either", not {"Morning match", "Physiotherapy"} & set(tiles("darpan")) and not {"Morning match", "Physiotherapy"} & set(tiles("amir")))
    ck("both tiles open the right doors", any(t["url"] == "/finance/clinic/match" for t in PM.TILES if t["name"] == "Morning match")
       and any(t["url"] == "/finance/physio" for t in PM.TILES if t["name"] == "Physiotherapy"))
except Exception as ex:                                                  # noqa: BLE001
    ck("patched portal.py imports", False, repr(ex))

shutil.rmtree(TMP, ignore_errors=True)
print("\n== %d checks, %d passed, %d failed" % (len(PASSED) + len(FAILED), len(PASSED), len(FAILED)))
for f in FAILED:
    print("   FAILED: %s" % f)
print("== WALK %s" % ("GREEN" if not FAILED else "RED"))
sys.exit(1 if FAILED else 0)
