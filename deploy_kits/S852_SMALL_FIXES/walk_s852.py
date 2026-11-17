#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s852.py -- kit S852_SMALL_FIXES (the parent, S474, 17-Nov-2026). A walk on a MADE-UP root: made-up days, slips and
papers, no real number.

    python walk_s852.py <code_dir> <schema_db> <work_dir> <duty_map.json>

<code_dir>  every /root/finance module, with the files under test (the built three; or the live files for the CONTROL)
<schema_db> an EMPTY database carrying the live schema only
Prints one line per check and a last line "WALK n/m". Exit 0 only when every check passes."""
import datetime as dt
import json
import os
import shutil
import sqlite3
import sys

CODE, SCHEMA, WORK, DUTY = sys.argv[1:5]
try:
    _ME = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _ME = None
sys.path[:] = [p for p in sys.path if not _ME or os.path.abspath(p or ".") != _ME]
sys.path.insert(0, CODE)
os.makedirs(WORK, exist_ok=True)
RES = []


def ok(name, cond, extra=""):
    RES.append((name, bool(cond)))
    print(("ok   " if cond else "RED  ") + name + (("   [%s]" % str(extra)[:160]) if not cond and extra != "" else ""))


TODAY = dt.date.today()


def day(n):
    return (TODAY - dt.timedelta(days=n)).isoformat()


# ================================================================ 1 · the console: approve-days (AF-41)
DB = os.path.join(WORK, "con.db")
shutil.copyfile(SCHEMA, DB)
c = sqlite3.connect(DB)
for code in ("medical",):
    try:
        c.execute("INSERT OR IGNORE INTO business_unit(code, name) VALUES (?,?)", (code, "Sanjeevni Medicos"))
    except sqlite3.Error:
        pass
for n, st in ((14, "submitted"), (12, "approved"), (10, "locked"), (9, "submitted"), (8, "draft")):
    c.execute("INSERT INTO day_entry(unit, business_date, status, source, entered_by, entered_at) VALUES ('medical',?,?,'app','walk',?)",
              (day(n), st, day(n) + "T21:00:00"))
c.commit()
c.close()
os.environ["DUTY_MAP_JSON"] = DUTY
os.environ["CONSOLE_SNAPSHOT"] = os.path.join(WORK, "snap.json")
os.environ["PATIENTS_READING"] = os.path.join(WORK, "patients.dat")
line = None
try:
    import owner_console as oc
    snap = oc.build(DB, os.path.join(WORK, "snap.json"))
    for ln in ((snap.get("sections") or {}).get("needs") or {}).get("lines") or []:      # his Needs-you section
        if "to approve" in str(ln.get("text") or ""):
            line = ln
except Exception as ex:                                       # noqa: BLE001
    print("console build failed: %s: %s" % (type(ex).__name__, ex))
who = str((line or {}).get("who") or "")
dm = lambda d: oc.dmy(d) if line else d                       # noqa: E731
ok("c1 the approve-days line is on his console with 3 days", line is not None and "3 day" in str(line.get("text")), line)
ok("c2 it says how long the oldest has waited (14 days)", "the oldest has waited 14 days" in who, who)
ok("c3 it names the day passed over while later days were approved", "passed over while later days were approved: %s" % dm(day(14)) in who, who)
ok("c4 a day after the last approved one is not called passed over", line is not None and who.count(dm(day(9))) == 1, who)
ok("c5 every waiting day is still listed", line is not None and all(dm(day(n)) in who for n in (14, 9, 8)), who)

# ================================================================ 2 · the radd door (F-1430)
DB2 = os.path.join(WORK, "slips.db")
shutil.copyfile(SCHEMA, DB2)
os.environ["FINANCE_DB"] = DB2
try:
    from flask import Flask
    import slip_log
    con = sqlite3.connect(DB2, timeout=10, check_same_thread=False)
    con.row_factory = sqlite3.Row
    slip_log.ensure(con)

    def require(*roles, unit=None):
        return {"user": "shavez", "roles": ["maker"]}, None

    def audit(*a, **k):
        return None
    app = Flask("s852walk")
    app.secret_key = "x"
    slip_log.init(app, lambda: con, require, audit, unit="slips")
    import parchi_desk                                       # noqa: F401 -- its guard, as the live app mounts it
    try:
        import slip_adjust
        slip_adjust.ensure(con)
    except Exception:                                        # noqa: BLE001
        pass
    cl = app.test_client()
    tday = slip_log._today()

    def mk(no):
        cur = con.execute("INSERT INTO slip(series, slip_no, day, clinic_id, state, logged_by, logged_at, updated_by, updated_at) "
                          "VALUES ('opd',?,?,'','ok','walk',?,'walk',?)", (no, tday, tday + " 10:00:00", tday + " 10:00:00"))
        con.commit()
        return cur.lastrowid
    a, b = mk(880001), mk(880002)
    r = cl.post("/finance/slips/radd", data=dict(slip_id=a, clinic_id="Zqxwalkname", how="returned", back="late"))
    n_adj = con.execute("SELECT COUNT(*) FROM slip_adjust WHERE slip_id=?", (a,)).fetchone()[0]
    cid = con.execute("SELECT clinic_id FROM slip WHERE id=?", (a,)).fetchone()[0]
    loc = r.headers.get("Location", "")
    ok("r1 a name typed as the clinic ID on the radd door is refused (no radd row)", n_adj == 0, n_adj)
    ok("r2 the slip keeps no name as its clinic ID", cid == "", cid)
    ok("r3 he is sent back to the list he came from, the reason said", r.status_code == 303 and "s=late" in loc and "err=" in loc, (r.status_code, loc[:80]))
    r2 = cl.post("/finance/slips/radd", data=dict(slip_id=b, clinic_id="7001", how="returned", back="list"))
    n2 = con.execute("SELECT COUNT(*) FROM slip_adjust WHERE slip_id=?", (b,)).fetchone()[0]
    cid2 = con.execute("SELECT clinic_id FROM slip WHERE id=?", (b,)).fetchone()[0]
    ok("r4 a number on the radd door goes through as before (radd written, the slip takes the ID)", n2 == 1 and cid2 == "7001", (n2, cid2))
    cc = con.execute("INSERT INTO slip(series, slip_no, day, clinic_id, state, logged_by, logged_at, updated_by, updated_at) "
                     "VALUES ('opd',880003,?,'Zqxoldname','cancelled','walk',?,'walk',?)", (tday, tday + " 10:00:00", tday + " 10:00:00")).lastrowid
    con.commit()
    cl.post("/finance/slips/radd", data=dict(slip_id=cc, clinic_id="Zqxoldname", how="never_taken", back="list"))
    n3 = con.execute("SELECT COUNT(*) FROM slip_adjust WHERE slip_id=?", (cc,)).fetchone()[0]
    ok("r6 a cancelled slip that already carries an old name as its ID can still be marked radd (as before)", n3 == 1, n3)
    r3 = cl.post("/finance/slips/save", data=dict(series="opd", clinic_id="Zqxwalkname"))
    ok("r5 the other doors' guard is unchanged (a name on save refused)", "clinic ID" in r3.get_data(as_text=True) or r3.status_code in (200, 303), r3.status_code)
except Exception as ex:                                       # noqa: BLE001
    import traceback
    traceback.print_exc()
    ok("r0 the slips walk ran", False, "%s: %s" % (type(ex).__name__, ex))

# ================================================================ 3 · month_read's Scan App groups (F-1418)
A = os.path.join(WORK, "assets.db")
if os.path.exists(A):
    os.remove(A)
s = sqlite3.connect(A)
s.execute("CREATE TABLE bills(id INTEGER PRIMARY KEY, kind TEXT, lane TEXT, subgroup TEXT, status TEXT, dup_of INTEGER, page_of INTEGER, "
          "doc_kind TEXT, challan_state TEXT, total_amount REAL, bill_date TEXT, bill_month TEXT, created_at TEXT)")
s.execute("CREATE TABLE credit_note(id INTEGER PRIMARY KEY, cn_bill_id INTEGER NOT NULL, cn_created_at TEXT NOT NULL DEFAULT '', against_bill_id INTEGER, "
          "against_created_at TEXT NOT NULL DEFAULT '', on_account INTEGER NOT NULL DEFAULT 0, amount REAL, by_whom TEXT, at TEXT, "
          "voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '')")
YM = "2026-10"
rows = [  # id, kind, lane, subgroup, status, dup_of, page_of, doc_kind, challan_state, amount
    (1, "Consumable", "clinic", "plaster", "approved", None, None, "bill", "", 1000),
    (2, "Consumable", "clinic", "plaster", "approved", None, None, "receipt", "", 500),
    (3, "Consumable", "clinic", "plaster", "approved", None, None, "statement", "", 300),
    (4, "Consumable", "clinic", "plaster", "approved", None, None, "summary", "", 200),
    (5, "Consumable", "clinic", "plaster", "approved", None, None, "challan", "open", 400),
    (6, "Consumable", "clinic", "plaster", "approved", None, None, "challan", "final", 250),
    (7, "Consumable", "clinic", "plaster", "approved", None, 1, "bill", "", 700),
    (8, "Consumable", "clinic", "plaster", "approved", 1, None, "bill", "", 1000),
    (9, "Consumable", "clinic", "plaster", "rejected", None, None, "bill", "", 900),
    (10, "Consumable", "clinic", "", "approved", None, None, "credit_note", "", 100),
    (11, "Consumable", "clinic", "", "draft", None, None, None, "", 60),
    (12, "Pharmacy", "pharmacy", "", "approved", None, None, "bill", "", 900),
    (13, "Pharmacy", "pharmacy", "", "approved", None, None, "credit_note", "", 90),
    (14, "Pharmacy", "pharmacy", "", "approved", None, None, "summary", "", 5000),
    (15, "Lab", "lab_purchase", "", "approved", None, None, "bill", "", 300),
    (16, "Lab", "lab_purchase", "", "approved", None, None, "credit_note", "", 30),
]
for r in rows:
    s.execute("INSERT INTO bills(id, kind, lane, subgroup, status, dup_of, page_of, doc_kind, challan_state, total_amount, bill_date, bill_month, created_at) "
              "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", r + (YM + "-15", "", YM + "-15 10:00:00"))
s.execute("INSERT INTO credit_note(cn_bill_id, against_bill_id) VALUES (10, 1)")
s.execute("INSERT INTO credit_note(cn_bill_id, against_bill_id, voided_at) VALUES (16, 1, '2026-10-20')")   # voided: stays on its own lane
s.commit()
s.close()
try:
    import month_read as MR
    g = MR._scan_groups({"assets": A}, YM)
    pl = g["groups"].get("plaster")
    ok("m1 plaster: the bill and the final challan count (2 papers)", pl and pl[0] == 2, pl)
    ok("m2 plaster: 1000 + 250 less the credit note 100 against its bill = 1150", pl and abs(pl[1] - 1150) < 0.01, pl)
    un = g["groups"].get("")
    ok("m3 the unsorted clinic paper counts; the credit note is not counted there", un and un[0] == 1 and abs(un[1] - 60) < 0.01, un)
    ok("m4 the pharmacy: one bill scanned (no credit note, no summary)", g["pharmacy"][0] == 1 and g["ids"] == [12], (g["pharmacy"], g["ids"]))
    lab = g["lanes"].get("lab_purchase")
    ok("m5 a credit note with only a voided link is less on its own lane (300 - 30)", lab and lab[0] == 1 and abs(lab[1] - 270) < 0.01, lab)
    cl_ = g["lanes"].get("clinic")
    ok("m6 the clinic lane = the groups added up (3 papers, 1210)", cl_ and cl_[0] == 3 and abs(cl_[1] - 1210) < 0.01, cl_)
    A2 = os.path.join(WORK, "assets_old.db")
    shutil.copyfile(A, A2)
    s2 = sqlite3.connect(A2)
    s2.execute("DROP TABLE credit_note")
    s2.execute("CREATE TABLE credit_note(id INTEGER PRIMARY KEY, cn_bill_id INTEGER, against_bill_id INTEGER)")   # an older shape
    s2.execute("INSERT INTO credit_note(cn_bill_id, against_bill_id) VALUES (10, 1)")
    s2.commit()
    s2.close()
    g2 = MR._scan_groups({"assets": A2}, YM)
    ok("m7 an older credit-note table (no voided_at) is read without a fault: the note less on its own group",
       abs(g2["groups"]["plaster"][1] - 1250) < 0.01 and abs(g2["groups"][""][1] - (60 - 100)) < 0.01, g2["groups"])
except Exception as ex:                                       # noqa: BLE001
    ok("m0 month_read read the Scan App", False, "%s: %s" % (type(ex).__name__, ex))

bad = [n for n, cnd in RES if not cnd]
print("WALK %d/%d" % (len(RES) - len(bad), len(RES)))
sys.exit(0 if not bad else 1)
