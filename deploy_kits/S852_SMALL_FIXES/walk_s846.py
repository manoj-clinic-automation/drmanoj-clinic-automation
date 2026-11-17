#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s846.py -- kit S846_SLIPS_NOT_IN_DOCTERZ (S474, 17-Nov-2026; v2 with the cold review's cases). A walk on a MADE-UP root: no patient, no real number.

    python walk_s846.py <code_dir> <bundle_finance_dir> <schema_db> <work_dir>

<code_dir>   the files under test (the built five; or the live four for the CONTROL, which must go red)
<bundle_finance_dir>  the newest bundle's /root/finance (every other module the files import)
<schema_db>  an EMPTY database carrying the live schema only (no rows)
<work_dir>   a scratch folder; the made-up database and console mirror are written there
Prints one line per check and a last line "WALK n/m". Exit 0 only when every check passes.
"""
import importlib
import os
import shutil
import sqlite3
import sys

CODE, BUNDLE, SCHEMA, WORK = sys.argv[1:5]
sys.path[:0] = [CODE, BUNDLE]
os.makedirs(WORK, exist_ok=True)
DB = os.path.join(WORK, "walk.db")
CON_DB = os.path.join(WORK, "console_walk.db")
shutil.copyfile(SCHEMA, DB)
os.environ["NID_CONSOLE_DB"] = CON_DB

RES = []


def ok(name, cond, extra=""):
    RES.append(bool(cond))
    print("%s  %s%s" % ("PASS" if cond else "FAIL", name, ("  -- " + str(extra)) if extra else ""))


D1, D2, D3 = "2026-11-10", "2026-11-11", "2026-11-12"
FEE = 50000
ID = {k: str(900000 + k) for k in range(1, 12)}            # made-up clinic IDs, none real


def seed():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    # Docterz for D1 only: two consultations at the usual fee (cash); D2 not exported
    c.execute("INSERT INTO clinic_day_revenue (business_date, source_file, source_id, source_mtime, taken_at, cons_count, cons_amount_p, "
              "xray_count, xray_amount_p, proc_count, proc_amount_p, total_count, total_amount_p, free_revisits, free_concession, "
              "f93_phantom_rows, tender_json) VALUES (?,?,?,?,?,2,?,0,0,0,0,2,?,0,0,0,'{}')",
              (D1, "walk", "walk", D1 + " 22:00", D1 + " 22:00", 2 * FEE, 2 * FEE))
    for sn, k in ((1, 1), (2, 2)):
        c.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode) VALUES (?,?,?,?,?,?,?)",
                  (D1, "consult", sn, "WALK PATIENT %d" % k, ID[k], FEE, "Cash"))
    # the counter: Docterz's 1,000 + 500 (OPD outside) + 250 (X-ray entered back-dated); the proc (free) not collected
    c.execute("INSERT INTO clinic_register_day (business_date, cons_cash_p, cons_upi_p, cons_card_p, xray_cash_p, xray_upi_p, xray_card_p, "
              "proc_cash_p, proc_upi_p, proc_card_p, dress_cash_p, dress_upi_p, dress_card_p, entered_by, entered_at) "
              "VALUES (?,?,0,0,0,?,0,0,0,0,0,0,0,'walk',?)", (D1, 3 * FEE, 25000, D1 + " 21:00"))
    sid = {}

    def slip(key, series, no, day, cid, name="", no_id=""):
        cur = c.execute("INSERT INTO slip (series, slip_no, day, clinic_id, no_id_name, name_seen, state, logged_by, logged_at) "
                        "VALUES (?,?,?,?,?,?,'ok','walk',?)", (series, no, day, cid, no_id, name, day + " 10:00"))
        sid[key] = cur.lastrowid

    def item(key, kind, name, price, disc=0, sort=1):
        c.execute("INSERT INTO slip_item (slip_id, kind, name, side, price_p, sort, discount_p) VALUES (?,?,?,?,?,?,?)",
                  (sid[key], kind, name, "", price, sort, disc))

    slip("S1", "opd", 1, D1, ID[1])                         # in Docterz: never listed
    slip("S2", "opd", 2, D1, ID[3], "WALK PATIENT 3")       # not in Docterz: listed (OPD, the usual fee)
    slip("S3", "xp", 1, D1, ID[2])                          # consult in Docterz, X-ray not: listed (net 250)
    item("S3", "xray", "WALK XRAY", 30000, 5000)
    slip("S4", "xp", 2, D1, ID[4])                          # a free X-ray: never listed
    item("S4", "xray", "WALK XRAY", 30000, 30000)
    slip("S5", "opd", 3, D1, "", no_id="WALK NO ID")        # no clinic ID: the desk's (S844), never listed
    slip("S6", "opd", 4, D1, ID[5])                         # Docterz's clinical report carries the visit: never listed
    c.execute("INSERT INTO dx_visit (patient_uid, visit_date, clinic_id, updated_at) VALUES (?,?,?,?)",
              ("walk-5", D1 + " 11:00", ID[5], D1 + " 23:00"))
    slip("S7", "opd", 5, D1, ID[6])                         # radd (cancel) pending: never listed
    c.execute("INSERT INTO slip_adjust (slip_id, kind, amount_p, clinic_id, day, made_by, made_at, state) VALUES (?,?,?,?,?,?,?,?)",
              (sid["S7"], "cancel", 0, ID[6], D1, "walk", D1 + " 12:00", "pending"))
    slip("S8", "xp", 3, D1, ID[7], "WALK PATIENT 7")        # procedure not in Docterz: listed (1,000)
    item("S8", "proc", "WALK PROC", 100000)
    slip("S9", "opd", 6, D2, ID[8])                         # D2 not exported: not decidable, never listed
    # D3: the register holds NO room (it equals Docterz) and an OPD slip is not in Docterz -- a 'kept outside' answer must not hide it
    c.execute("INSERT INTO clinic_day_revenue (business_date, source_file, source_id, source_mtime, taken_at, cons_count, cons_amount_p, "
              "xray_count, xray_amount_p, proc_count, proc_amount_p, total_count, total_amount_p, free_revisits, free_concession, "
              "f93_phantom_rows, tender_json) VALUES (?,?,?,?,?,1,?,0,0,0,0,1,?,0,0,0,'{}')",
              (D3, "walk", "walk3", D3 + " 22:00", D3 + " 22:00", FEE, FEE))
    c.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode) VALUES (?,?,?,?,?,?,?)",
              (D3, "consult", 1, "WALK PATIENT 9", ID[9], FEE, "Cash"))
    c.execute("INSERT INTO clinic_register_day (business_date, cons_cash_p, cons_upi_p, cons_card_p, xray_cash_p, xray_upi_p, xray_card_p, "
              "proc_cash_p, proc_upi_p, proc_card_p, dress_cash_p, dress_upi_p, dress_card_p, entered_by, entered_at) "
              "VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,'walk',?)", (D3, FEE, D3 + " 21:00"))
    slip("S10", "opd", 7, D3, ID[10], "WALK PATIENT 10")
    c.commit()
    c.close()
    m = sqlite3.connect(CON_DB)
    m.execute("CREATE TABLE patients (phone10 TEXT, clinic_id TEXT)")
    fake = "9" + "0" * 8 + "7"                              # a made-up mobile, built here so no number sits in this file
    m.execute("INSERT INTO patients VALUES (?,?)", (fake, ID[3] + ".0"))
    m.commit()
    m.close()
    return sid, fake


SID, FAKE = seed()
CONN = sqlite3.connect(DB, check_same_thread=False)
CONN.row_factory = sqlite3.Row
AUD = []
USER = {"u": {"user": "manoj", "roles": ["owner"]}, "deny": False}


def getdb():
    return CONN


def req(*a, **k):
    if USER["deny"]:
        return None, "denied"
    return USER["u"], None


def audit(con, table, row_id, action, before=None, after=None, who=None):
    AUD.append((table, row_id, action, who))


from flask import Flask                                     # noqa: E402

app = Flask("walk_s846")
app.secret_key = "walk"
day_check = importlib.import_module("day_check")
clinic_money = importlib.import_module("clinic_money")
owner_console = importlib.import_module("owner_console")
parchi_desk = importlib.import_module("parchi_desk")
day_check.init(app, getdb, req, audit)
parchi_desk.init(app, getdb, req, audit)
try:
    NID = importlib.import_module("not_in_docterz")
except Exception as ex:                                     # noqa: BLE001
    NID = None
    print("not_in_docterz not importable: %s" % ex)
cl = app.test_client()
URL = "/finance/clinic/not-in-docterz"

# ---------------------------------------------------------------- 0 · the readers never create the table (S474 review)
day_check.check_day(CONN, D1)
clinic_money.match_day(CONN, D1)
if NID:
    NID.rows(CONN)
    NID.open_for_patient(CONN, ID[3], "2026-11-12")
ok("the readers (day check, money, list, desk) never create nid_mark",
   CONN.execute("SELECT 1 FROM sqlite_master WHERE name='nid_mark'").fetchone() is None)

# ---------------------------------------------------------------- 1 · the list
ok("the page is mounted by day_check", URL in [r.rule for r in app.url_map.iter_rules()])
rr = NID.rows(CONN) if NID else []
keys = sorted((r["slip_id"], r["kind"]) for r in rr)
want = sorted([(SID["S2"], "opd"), (SID["S3"], "xray"), (SID["S8"], "proc"), (SID["S10"], "opd")])
ok("exactly the four rows (OPD not in Docterz, X-ray not in Docterz, procedure; D3's OPD)", keys == want, keys)
amt = {r["kind"]: r["amount_p"] for r in rr if r["day"] == D1}
ok("OPD at the usual fee; X-ray net of discount; procedure full", amt == {"opd": FEE, "xray": 25000, "proc": 100000}, amt)
ok("a free X-ray, a no-ID slip, a dx_visit, a radd, an unexported day are all left out",
   not any(r["slip_id"] in (SID["S1"], SID["S4"], SID["S5"], SID["S6"], SID["S7"], SID["S9"]) for r in rr))
nm = {r["kind"]: r["name"] for r in rr}
ok("the name: the slip's own, else Docterz's (ID 2 from its consult line)", nm.get("xray") == "WALK PATIENT 2" and nm.get("opd") == "WALK PATIENT 3", nm)

h = cl.get(URL)
body = h.get_data(as_text=True)
ok("the page answers 200 for him", h.status_code == 200, h.status_code)
ok("the page lists 4 to enter", "To enter in Docterz (back-dated) — 4" in body)
ok("single-day reads skip a dx_visit carrying a time (the desk, the next day)", NID.open_for_patient(CONN, ID[5], D2) == [] and
   not any(r["slip_id"] == SID["S6"] for r in NID.rows(CONN, D1, D1)))
ok("the full mobile shown on his page (from the console mirror)", ("tel:%s" % FAKE) in body)
ok("four taps per row", body.count("Entered in Docterz") >= 3 and body.count("Wrong slip") >= 3)
USER["deny"] = True
hd = cl.get(URL)
ok("the page refuses without his gate (no list, no mobile)", FAKE not in hd.get_data(as_text=True) and "To enter" not in hd.get_data(as_text=True))
pd = cl.post(URL + "/act", data={"slip": SID["S2"], "kind": "opd", "act": "outside"})
ok("a tap without his gate is refused and writes nothing", "Noted" not in pd.headers.get("Location", "") and
   CONN.execute("SELECT COUNT(*) FROM nid_mark").fetchone()[0] == 0)
USER["deny"] = False

# ---------------------------------------------------------------- 2 · day_check BEFORE any answer
ck = day_check.check_day(CONN, D1)
ck_keys = {c.get("key"): c.get("kind") for c in ck["cards"]}
ok("before: the day check raises cards for the three (missing / not billed)",
   ck_keys.get("addopd:%d" % SID["S2"]) and any(k.startswith("add:") for k in ck_keys) and len(ck["cards"]) >= 3, ck_keys)

# ---------------------------------------------------------------- 3 · the owner console line BEFORE
nl = owner_console._s846_nid_line(CONN) if hasattr(owner_console, "_s846_nid_line") else None
ok("console: '4 slips not in Docterz' with his link", nl is not None and "4 slips not in Docterz" in str(nl) and URL in str(nl), nl)

# ---------------------------------------------------------------- 4 · the desk's 'old' answer
dc = cl.get("/finance/slips/desk/api/patient?id=%s&day=2026-11-12" % ID[3])
dj = dc.get_json(silent=True) or {}
ok("the desk: typing the patient's ID later shows the earlier slip not in Docterz",
   dj.get("old") == [{"day": D1, "kind": "opd"}], dj.get("old"))
dc2 = cl.get("/finance/slips/desk/api/patient?id=%s&day=2026-11-12" % ID[1])
ok("the desk: a patient Docterz carries has no 'old'", (dc2.get_json(silent=True) or {}).get("old") == [])
dc3 = cl.get("/finance/slips/desk/api/patient?id=%s&day=%s" % (ID[3], D1))
ok("the desk: on the slip's own day it is not 'earlier'", (dc3.get_json(silent=True) or {}).get("old") == [])

# ---------------------------------------------------------------- 5 · the taps
p = cl.post(URL + "/act", data={"slip": SID["S2"], "kind": "opd", "act": "outside"})
ok("tap: Not entering in Docterz (OPD) -> 303 'Noted'", p.status_code == 303 and "Noted" in p.headers.get("Location", ""))
p = cl.post(URL + "/act", data={"slip": SID["S3"], "kind": "xray", "act": "entered"})
ok("tap: Entered in Docterz (X-ray)", p.status_code == 303 and "Noted" in p.headers.get("Location", ""))
p = cl.post(URL + "/act", data={"slip": SID["S8"], "kind": "proc", "act": "free"})
ok("tap: Free / staff / home (procedure)", p.status_code == 303 and "Noted" in p.headers.get("Location", ""))
p = cl.post(URL + "/act", data={"slip": SID["S8"], "kind": "proc", "act": "wrong"})
ok("a second answer on the same row is refused", "err=" in p.headers.get("Location", "") and "Already" in __import__("urllib.parse").parse.unquote(p.headers.get("Location", "")))
p = cl.post(URL + "/act", data={"slip": SID["S1"], "kind": "opd", "act": "entered"})
ok("a tap on a row Docterz carries is refused", "err=" in p.headers.get("Location", ""))
p = cl.post(URL + "/act", data={"slip": SID["S2"], "kind": "opd", "act": "bogus"})
ok("an unknown answer is refused", "err=" in p.headers.get("Location", ""))
n_marks = CONN.execute("SELECT COUNT(*) FROM nid_mark WHERE state='live'").fetchone()[0]
ok("three live marks written, each audited", n_marks == 3 and sum(1 for a in AUD if a[2] == "nid_mark") == 3, (n_marks, len(AUD)))
try:
    CONN.execute("INSERT INTO nid_mark (slip_id, kind, act, amount_p, day, who, at) VALUES (?,?,?,?,?,?,?)",
                 (SID["S2"], "opd", "free", 0, D1, "walk", "x"))
    dup = False
except sqlite3.IntegrityError:
    dup = True
CONN.rollback()
ok("a second LIVE mark on the same row is refused by the table itself (a double tap)", dup)
body = cl.get(URL).get_data(as_text=True)
ok("the page: 1 to enter (D3), 3 answered by you", "To enter in Docterz (back-dated) — 1" in body and "Answered by you — 3" in body)

# ---------------------------------------------------------------- 6 · day_check AFTER the answers
ck = day_check.check_day(CONN, D1)
keys_after = {c.get("key") for c in ck["cards"]}
notes = " | ".join(e for e, _h in ck["notes"])
ok("after: no card for the three answered slips",
   not ({"addopd:%d" % SID["S2"]} & keys_after) and not any(k and k.startswith("add:") for k in keys_after), keys_after)
ok("after: a note for each (outside / entered / free)",
   "kept outside Docterz by Dr Manoj" in notes and "entered in Docterz back-dated" in notes and "free / staff / home" in notes, notes[:300])

# ---------------------------------------------------------------- 7 · clinic_money
_orig_bank = clinic_money._bank
clinic_money._bank = lambda con, d, now=None: ({"state": "applied"}, [dict(txn_time="11:05", amount_p=25000, rrn="WALK0001", mode="UPI")])
try:
    m = clinic_money.match_day(CONN, D1)
finally:
    clinic_money._bank = _orig_bank
codes = [e["code"] for e in m["explained"]]
fl = [f["code"] for f in m["flags"]]
ok("money: counter − Docterz explained by his answered slips (750 = 500 outside + 250 entered)",
   "slips_not_in_docterz" in codes and any(e["amount_p"] == 75000 for e in m["explained"] if e["code"] == "slips_not_in_docterz"), codes)
ok("money: no total difference flagged or handed to the day check", "total_diff" not in fl and not m.get("handed_p"), (fl, m.get("handed_p")))
ok("money: a bank UPI of an answered slip's amount is explained, not a gap",
   "slip_not_in_docterz_upi" in codes and "bank_extra" not in fl, (codes, fl))
clinic_money._bank = lambda con, d, now=None: ({"state": "applied"}, [dict(txn_time="11:05", amount_p=25000, rrn="WALK0001", mode="UPI"),
                                                                       dict(txn_time="12:05", amount_p=25000, rrn="WALK0002", mode="UPI")])
try:
    m2 = clinic_money.match_day(CONN, D1)
finally:
    clinic_money._bank = _orig_bank
ok("money: the same amount twice in the bank -- one explained, the other still flagged",
   [e["code"] for e in m2["explained"]].count("slip_not_in_docterz_upi") == 1 and [f["code"] for f in m2["flags"]].count("bank_extra") == 1)
CONN.execute("UPDATE slip SET paid_mode='cash' WHERE id=?", (SID["S3"],))
CONN.commit()
clinic_money._bank = lambda con, d, now=None: ({"state": "applied"}, [dict(txn_time="11:05", amount_p=25000, rrn="WALK0001", mode="UPI")])
try:
    m3 = clinic_money.match_day(CONN, D1)
finally:
    clinic_money._bank = _orig_bank
ok("money: a slip marked paid in cash never explains a bank UPI", "slip_not_in_docterz_upi" not in [e["code"] for e in m3["explained"]]
   and "bank_extra" in [f["code"] for f in m3["flags"]])
CONN.execute("UPDATE slip SET paid_mode='' WHERE id=?", (SID["S3"],))
CONN.commit()

# ---------------------------------------------------------------- 7b · no room in the register: his 'kept outside' must not hide it
p = cl.post(URL + "/act", data={"slip": SID["S10"], "kind": "opd", "act": "outside"})
c3 = day_check.check_day(CONN, D3)
ok("no room: an 'outside' answer keeps the day check's card (the counter does not hold the money)",
   any(c.get("key") == "addopd:%d" % SID["S10"] for c in c3["cards"]), [c.get("key") for c in c3["cards"]])
mid3 = CONN.execute("SELECT id FROM nid_mark WHERE slip_id=? AND state='live'", (SID["S10"],)).fetchone()[0]
cl.post(URL + "/act", data={"mark": mid3, "act": "undo"})

# ---------------------------------------------------------------- 8 · the console AFTER
nl2 = owner_console._s846_nid_line(CONN) if hasattr(owner_console, "_s846_nid_line") else "x"
ok("console: the count follows the answers (1 left)", nl2 is not None and "1 slip not in Docterz" in str(nl2), nl2)
ok("outside_for_day: [500] for D1", NID.outside_for_day(CONN, D1) == [FEE] if NID else False)
ok("counts: (1 open, 500 outside)", NID.counts(CONN) == (1, FEE) if NID else False)

# ---------------------------------------------------------------- 9 · undo
mid = CONN.execute("SELECT id FROM nid_mark WHERE slip_id=? AND state='live'", (SID["S8"],)).fetchone()[0]
p = cl.post(URL + "/act", data={"mark": mid, "act": "undo"})
ok("undo: the procedure's answer undone", p.status_code == 303 and "Undone" in __import__("urllib.parse").parse.unquote(p.headers.get("Location", "")))
p = cl.post(URL + "/act", data={"mark": mid, "act": "undo"})
ok("undo twice is refused", "err=" in p.headers.get("Location", ""))
ok("the procedure is open again (2 to enter)", "To enter in Docterz (back-dated) — 2" in cl.get(URL).get_data(as_text=True))
CONN.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode) VALUES (?,?,?,?,?,?,?)",
             (D1, "proc", 1, "WALK PATIENT 7", ID[7], 100000, "Cash"))
CONN.commit()
ok("the row leaves by itself when Docterz carries it", not any(r["slip_id"] == SID["S8"] for r in NID.rows(CONN)) if NID else False)

print("WALK %d/%d" % (sum(RES), len(RES)))
CONN.close()
sys.exit(0 if all(RES) else 1)
