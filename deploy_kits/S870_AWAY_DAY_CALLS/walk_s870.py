#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s870.py -- kit S870_AWAY_DAY_CALLS (the parent, S480, 18-Nov-2026). MADE-UP data only (no real patient, number or name):
  A  wa_ladder.plan(): a follow-up due on a not-sitting day is HELD ("Dr Manoj was away"), the others as before;
  B  portal_followups.parse(): the batch page never offers a WhatsApp for such a row, and says why;
  C  calls_console: the Call Console page (on S817's own made-up stores) shows "Dr Manoj was away" on that row only;
  D  docterz_missing_alert: a not-sitting mark is not a sign the clinic worked (S868 review SHOULD 2).
usage: walk_s870.py <portal dir to test> <portal dir with ring_outcome/ring_common> <portal_console.py> <finance dir>
                    <walk_s817.py> <scratch>                       last line "WALK n/m"."""
import datetime as dt
import importlib.util
import os
import shutil
import sqlite3
import subprocess
import sys

P, RING, BUILDER, FIN, W817, SCR = sys.argv[1:7]
try:
    _ME = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _ME = None
sys.path[:] = [p for p in sys.path if not _ME or os.path.abspath(p or ".") != _ME]     # F-1441
if os.path.isdir(SCR):
    shutil.rmtree(SCR)
os.makedirs(SCR)
RES = []


def ok(name, cond, extra=""):
    RES.append(bool(cond))
    print("%s  %s%s" % ("PASS" if cond else "FAIL", name, ("  -- " + str(extra)[:240]) if extra else ""))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
D = dt.datetime.now(IST).date()
day = lambda n: (D + dt.timedelta(days=n)).strftime("%Y-%m-%d")      # noqa: E731
M = lambda n: "9" + "%09d" % (87000 + n)                             # noqa: E731 -- made-up mobiles, built at run time (F-185)

# ---------------------------------------------------------------- A. the WhatsApp ladder
FDB = os.path.join(SCR, "f.db")
os.environ.update({"FINANCE_DB": FDB, "WA_LADDER_DB": os.path.join(SCR, "wl.db"), "WA_LADDER_INBOX_DB": os.path.join(SCR, "inbox.db"),
                   "WA_LADDER_OLD_OPTOUT": os.path.join(SCR, "old.csv"), "WA_LADDER_INGEST": "0",
                   "WA_LADDER_CONSOLE_DB": os.path.join(SCR, "console_none.db")})
c = sqlite3.connect(FDB)
c.executescript("""
CREATE TABLE dx_visit (patient_uid TEXT NOT NULL, visit_date TEXT NOT NULL, clinic_id TEXT NOT NULL DEFAULT '', diagnosis_raw TEXT NOT NULL DEFAULT '',
  std_dx TEXT NOT NULL DEFAULT '', category TEXT NOT NULL DEFAULT '', priority TEXT NOT NULL DEFAULT '', dx_status TEXT NOT NULL DEFAULT '',
  follow_up_date TEXT NOT NULL DEFAULT '', export_id INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL, PRIMARY KEY (patient_uid, visit_date));
CREATE TABLE patient_visit (visit_id TEXT PRIMARY KEY, visit_date TEXT NOT NULL, clinic_id TEXT, patient_uid TEXT, mobile_fp TEXT, had_procedure TEXT);
CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT NOT NULL UNIQUE, name TEXT, phone_last4 TEXT, first_seen TEXT, merged_into INTEGER,
  note TEXT, mobile_fp TEXT, patient_uid TEXT, last_seen TEXT, mobile TEXT);
""")


def pat(n, name, mob, vd, fu):
    c.execute("INSERT INTO patient_ref (clinic_id, name, phone_last4, mobile, patient_uid) VALUES (?,?,?,?,?)", ("W%d" % n, name, mob[-4:], mob, "u%d" % n))
    c.execute("INSERT INTO patient_visit VALUES (?,?,?,?,?,?)", ("v%d" % n, vd, "W%d" % n, "u%d" % n, "", ""))
    c.execute("INSERT INTO dx_visit (patient_uid, visit_date, clinic_id, follow_up_date, updated_at) VALUES (?,?,?,?,?)", ("u%d" % n, vd, "W%d" % n, fu, "x"))


pat(1, "Walk Amar", M(1), day(-7), day(1))       # tomorrow -- a day he will not sit
pat(2, "Walk Bina", M(2), day(-8), day(1))       # tomorrow too, the same day -- also held
pat(3, "Walk Charu", M(3), day(-9), day(-1))     # passed yesterday -- he was away yesterday
pat(4, "Walk Dev", M(4), day(-12), day(-5))      # 5 days ago -- he sat that day: goes
c.commit()
try:
    WL = load("wa_ladder_t", os.path.join(P, "wa_ladder.py"))
    p0 = WL.plan()
    rows0 = {r["cid"]: r for x in p0["lists"] for r in x["rows"]}
    ok("A1 no not-sitting table at all: nothing held for it (as before)", not any("away" in (r["hold"] or "") for r in rows0.values()), [(k, r["hold"]) for k, r in rows0.items()])
    c.execute("CREATE TABLE clinic_off_day (day TEXT PRIMARY KEY, how TEXT NOT NULL, by TEXT NOT NULL DEFAULT '', at TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '')")
    c.execute("INSERT INTO clinic_off_day (day, how) VALUES (?, 'owner')", (day(1),))
    c.execute("INSERT INTO clinic_off_day (day, how) VALUES (?, 'auto')", (day(-1),))
    c.commit()
    p1 = WL.plan()
    rows1 = {r["cid"]: r for x in p1["lists"] for r in x["rows"]}
    ok("A2 'tomorrow' for a day he will not sit: held, the reason said", "Dr Manoj was away" in rows1["W1"]["hold"] and "Dr Manoj was away" in rows1["W2"]["hold"], (rows1["W1"]["hold"], rows1["W2"]["hold"]))
    ok("A3 'date passed yesterday' when he was away yesterday: held", "Dr Manoj was away" in rows1["W3"]["hold"], rows1["W3"]["hold"])
    ok("A4 a follow-up of a day he sat still goes", rows1["W4"]["hold"] == "" and rows0["W4"]["hold"] == "", rows1["W4"]["hold"])
    c.execute("CREATE TABLE IF NOT EXISTS online_booking (id INTEGER PRIMARY KEY, payment_id TEXT NOT NULL UNIQUE, name TEXT, mobile TEXT, appt_at TEXT)")
    c.execute("INSERT INTO online_booking (payment_id, name, mobile, appt_at) VALUES (?,?,?,?)", ("pay_S870walk", "Walk Esha", M(5), day(1) + " 11:30"))
    c.commit()
    p2 = WL.plan()
    ap = [r for x in p2["lists"] if x["key"] == "appt" for r in x["rows"]]
    ok("A6 an online booking for a day he will not sit: its reminder held (review)", ap and all("Dr Manoj was away" in r["hold"] for r in ap), [r["hold"] for r in ap])
    c.execute("DELETE FROM online_booking")
    c.commit()
    ok("A5 the held rows are counted held, never 'go'", all(x["go"] + x["tick"] + x["held"] == len(x["rows"]) for x in p1["lists"])
       and sum(x["go"] for x in p1["lists"]) == sum(x["go"] for x in p0["lists"]) - 3)
except Exception as ex:                                                  # noqa: BLE001
    ok("A wa_ladder: %s: %s" % (type(ex).__name__, ex), False)

# ---------------------------------------------------------------- B. the batch page's list
try:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Call Sheet"
    ws.append(["Staff action list %s" % D.year])
    ws.append(["1. FOLLOW-UP - due"])
    ws.append(["S.N", "", "Name", "Mobile", "Diagnosis", "Date", "OD", "Status"])
    yday, tom = D - dt.timedelta(days=1), D + dt.timedelta(days=1)
    ws.append(["1", "", "Walk Charu", M(3), "made-up", yday.strftime("%d-%b"), 1, "Not called"])
    ws.append(["2", "", "Walk Amar", M(1), "made-up", tom.strftime("%d-%b"), -1, "Not called"])
    ws.append(["3", "", "Walk Dev", M(4), "made-up", (D - dt.timedelta(days=5)).strftime("%d-%b"), 5, "Not called"])
    xl = os.path.join(SCR, "Staff_Action_Today_%s.xlsx" % D.isoformat())
    wb.save(xl)
    PF = load("portal_followups_t", os.path.join(P, "portal_followups.py"))
    rr = {r["name"]: r for s in PF.parse(xl)["sections"] for r in s["rows"]}
    ok("B1 the batch page: a row due on a not-sitting day is not sendable, no template", not rr["Walk Charu"]["sendable"] and rr["Walk Charu"]["template"] == ""
       and not rr["Walk Amar"]["sendable"], (rr["Walk Charu"]["sendable"], rr["Walk Charu"]["template"]))
    ok("B2 ... and says why", "Dr Manoj was away" in rr["Walk Charu"]["status"] and rr["Walk Charu"].get("away") is True)
    ok("B3 a row of a day he sat is sent as before", rr["Walk Dev"]["sendable"] and rr["Walk Dev"]["template"] == "drmanoj_followup_missed", rr["Walk Dev"])
    ok("B4 the sheet's date reads to its day", PF.s870_iso(yday.strftime("%d-%b"), str(D.year)) == yday.isoformat() and PF.s870_iso("junk", "2026") == "")
    ok("B5 across the year end the nearest year is taken; a year in the cell wins (review)",
       PF.s870_iso("28-Dec", "2027", dt.date(2027, 1, 3)) == "2026-12-28" and PF.s870_iso("01-Jan", "2026", dt.date(2026, 12, 31)) == "2027-01-01"
       and PF.s870_iso("16-Nov-2025", "2026", dt.date(2026, 11, 18)) == "2025-11-16")
except Exception as ex:                                                  # noqa: BLE001
    ok("B portal_followups: %s: %s" % (type(ex).__name__, ex), False)

# ---------------------------------------------------------------- C. the Call Console (S817's own made-up stores)
ST = os.path.join(SCR, "st817")
r = subprocess.run([sys.executable, "-B", W817, P, RING, BUILDER, FIN, "--stores", ST], capture_output=True, text=True, timeout=600)
ok("C0 S817's walk on this page, on its made-up stores, as on the live page", "WALK" in (r.stdout or "") and "of 48" in r.stdout, (r.stdout or r.stderr)[-200:])
try:
    from flask import Flask
    os.environ["RING_OUTCOME_DB"] = os.path.join(ST, "ring.db")
    os.environ["FINANCE_DB"] = os.path.join(ST, "finance.db")
    sys.path.insert(0, RING)
    NOW = dt.datetime(2026, 11, 13, 12, 0, 0)
    CFG = {"PORTAL_INBOX_DB": os.path.join(ST, "inbox.db"), "FINANCE_DB_PATH": os.environ["FINANCE_DB"], "SR_STAFF_MASTER": os.path.join(ST, "staff_master.csv"),
           "SR_PUNCH_CSV": os.path.join(ST, "punches.csv"), "PORTAL_CALL_REVIEW_DB": os.path.join(ST, "call_review.db")}

    def conn():
        k = sqlite3.connect("file:%s?mode=ro" % os.path.join(ST, "console.db"), uri=True)
        k.row_factory = sqlite3.Row
        return k

    def page(tag):
        C = load("cc_" + tag, os.path.join(P, "calls_console.py"))
        app = Flask("w870" + tag)
        if hasattr(C, "rv_init"):
            C.rv_init(CFG["PORTAL_CALL_REVIEW_DB"])
        C.register(app, lambda f: f, lambda: "manoj", lambda k, d=None: CFG.get(k, d),
                   {"console_conn": conn, "console_meta": lambda: {"ok": True, "built_at": "2026-11-13T11:50:00+05:30"},
                    "spam_phones": lambda: [], "reviews_maps": lambda: ({}, {})})
        Dd = C.page_data(conn(), now=NOW, inbox_path=CFG["PORTAL_INBOX_DB"], fin_db=CFG["FINANCE_DB_PATH"], master_path=CFG["SR_STAFF_MASTER"], punch_path=CFG["SR_PUNCH_CSV"])
        with app.test_request_context("/portal/console"):
            H = C.render(conn(), {}, now=NOW)
        return Dd, H

    D0, H0 = page("a")
    open_rows = [r for b in D0["fu"]["bands"] for r in b[3]]
    ok("C1 the made-up follow-up list has open rows, none marked away (no table yet)", open_rows and not any(r.get("away") for r in open_rows)
       and "Dr Manoj was away" not in H0, len(open_rows))
    pick = open_rows[0]["dd"].isoformat() if open_rows else ""
    f = sqlite3.connect(os.environ["FINANCE_DB"])
    f.execute("CREATE TABLE IF NOT EXISTS clinic_off_day (day TEXT PRIMARY KEY, how TEXT NOT NULL, by TEXT NOT NULL DEFAULT '', at TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '')")
    f.execute("INSERT OR REPLACE INTO clinic_off_day (day, how) VALUES (?, 'owner')", (pick,))
    f.commit()
    f.close()
    D1, H1 = page("b")
    rows1 = [r for b in D1["fu"]["bands"] for r in b[3]]
    away = [r for r in rows1 if r.get("away")]
    ok("C2 a row due on that day is marked away; every other row not", away and all(r["dd"].isoformat() == pick for r in away)
       and len(away) == sum(1 for r in rows1 if r["dd"].isoformat() == pick), (pick, len(away)))
    ok("C3 the page says it on the row", "Dr Manoj was away that day" in H1 and H1.count("Dr Manoj was away that day") >= len(away))
    ok("C4 nothing else on the list moves (the same rows, the same bands)", [(b[0], b[4]) for b in D0["fu"]["bands"]] == [(b[0], b[4]) for b in D1["fu"]["bands"]])
except Exception as ex:                                                  # noqa: BLE001
    ok("C calls_console: %s: %s" % (type(ex).__name__, ex), False)
# ---------------------------------------------------------------- D. the 21:45 / 08:15 push (S868 review SHOULD 2)
try:
    DMA = load("dma_t", os.path.join(P, "docterz_missing_alert.py"))
    ddb = os.path.join(SCR, "dma.db")
    k = sqlite3.connect(ddb)
    k.execute("CREATE TABLE docterz_export (id INTEGER PRIMARY KEY, drive_id TEXT, drive_mtime TEXT, md5 TEXT, kind TEXT, business_date TEXT, "
              "rows INTEGER, stored TEXT, status TEXT, note TEXT, taken_at TEXT, due_from TEXT, due_to TEXT)")
    k.execute("CREATE TABLE slip (id INTEGER PRIMARY KEY, series TEXT, day TEXT, state TEXT)")
    k.execute("INSERT INTO docterz_export (drive_id, drive_mtime, md5, kind, business_date, rows, stored, status) VALUES "
              "('offday:walk','0000-offday-2031-04-01','offday-2031-04-01','consultation','2031-04-01',0,'','current')")
    k.execute("INSERT INTO docterz_export (drive_id, drive_mtime, md5, kind, business_date, rows, stored, status) VALUES "
              "('offday:walk','0000-offday-2031-04-02','offday-2031-04-02','consultation','2031-04-02',0,'','current')")
    k.execute("INSERT INTO docterz_export (drive_id, drive_mtime, md5, kind, business_date, rows, stored, status, due_to) VALUES "
              "('walk-f','t','m2','followup','2031-04-02',9,'x','current','2031-05-02')")
    k.execute("INSERT INTO docterz_export (drive_id, drive_mtime, md5, kind, business_date, rows, stored, status) VALUES "
              "('walk-c','t','m3','consultation','2031-04-03',12,'x','current')")
    k.commit()
    s1 = DMA.read_day(ddb, dt.date(2031, 4, 1))
    m1, w1, _ = DMA.judge(s1)
    ok("D1 a marked day with nothing else (a leave day, clinic shut): nothing is said", s1["cons"] and not w1, (s1, m1, w1))
    s2 = DMA.read_day(ddb, dt.date(2031, 4, 2))
    m2, w2, _ = DMA.judge(s2)
    ok("D2 a marked day with the follow-up log in: worked, nothing missing", w2 and m2 == [], (m2, w2))
    s3 = DMA.read_day(ddb, dt.date(2031, 4, 3))
    m3, w3, sg3 = DMA.judge(s3)
    ok("D3 a real report still counts as the sign of work", w3 and "consultation report came" in sg3 and "followup" in m3, (m3, sg3))
    k.execute("INSERT INTO docterz_export (drive_id, drive_mtime, md5, kind, business_date, rows, stored, status) VALUES "
              "('walk-c4','t','m4','consultation','2031-04-01',7,'x','current')")
    k.commit()
    s4 = DMA.read_day(ddb, dt.date(2031, 4, 1))
    m4, w4, sg4 = DMA.judge(s4)
    ok("D4 a mark AND a real report the same day: the report still counts (review)", w4 and "consultation report came" in sg4, (m4, sg4))
except Exception as ex:                                                  # noqa: BLE001
    ok("D docterz_missing_alert: %s: %s" % (type(ex).__name__, ex), False)
print("WALK %d/%d" % (sum(RES), len(RES)))
