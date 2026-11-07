#!/usr/bin/env python3
"""walk_s744.py -- S744_STAFF_CARDS's walk (S742's walk whole, plus the staff cards), on MADE-UP data only (no real patient, number or name anywhere).
usage: walk_s742.py <dir with calls_console.py> <dir with ring_outcome.py + ring_common.py> <portal_console.py (made)>
       [--control]   -- with --control the walk expects the S742 checks to go RED (run it on the live calls_console.py)
Builds a made-up console.db (the builder's own SCHEMA + build_fu_all), inbox.db, finance.db (patient_visit) and a
ring store, then reads the page's data and renders the page. Prints one line per check; exit 0 only when all pass."""
import datetime as dt
import importlib.util
import json
import os
import shutil
import sqlite3
import sys
import tempfile

A = [x for x in sys.argv[1:] if not x.startswith("--")]
CONTROL = "--control" in sys.argv
PAGE_DIR, RING_DIR, BUILDER = A[0], A[1], A[2]
TMP = tempfile.mkdtemp(prefix="s744walk_")
os.environ["RING_OUTCOME_DB"] = os.path.join(TMP, "ring.db")
os.environ["FINANCE_DB"] = os.path.join(TMP, "finance.db")
sys.path.insert(0, RING_DIR)
sys.path.insert(0, PAGE_DIR)
NOW = dt.datetime(2026, 11, 7, 12, 0, 0)


def N(i):
    """a made-up ten-digit test number, built at run time (no number is written in this file -- F-185)"""
    return "9" + "0" * 6 + "%03d" % i

RES = []


def check(name, fn, s742=True):
    try:
        ok = bool(fn())
    except Exception as e:
        ok, name = False, name + "  [%s: %s]" % (type(e).__name__, str(e)[:80])
    RES.append((name, ok, s742))
    print(("ok   " if ok else "RED  ") + name)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


B = load("pc_made", BUILDER)
DAY = "2026-11-07"


def jk(ph, t):
    return "%s_%d" % (ph, int(dt.datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone(dt.timedelta(hours=5, minutes=30))).timestamp()))


# ---------------------------------------------------------------- console.db, made up
con = sqlite3.connect(os.path.join(TMP, "console.db"))
con.executescript(B.SCHEMA)
con.execute("CREATE TABLE call_agent (join_key TEXT PRIMARY KEY, agent TEXT, department TEXT, matched_how TEXT)")
P = {N(1): ("Asha Test", "C-1001", "knee pain"), N(2): ("Bina Test", "C-1002", "back pain"),
     N(3): ("Chand Test", "C-1003", "shoulder"), N(4): ("Dev Test", "C-1004", "wrist"),
     N(5): ("Esha Test", "C-1005", "ankle"), N(6): ("Faiz Test", "C-1006", "hip"),
     N(7): ("Gita Test", "C-1007", "knee")}
for ph, (n, cid, dx) in P.items():
    con.execute("INSERT INTO patients VALUES (?,?,?,?,?,?,?,?)", (ph, n, dx, "50", "F", "", "", cid))
CALLS = []


def call(ph, t, direction, answered, dur, agent="", claimed="", ai="", ev="", ring=12, talk=None):
    k = jk(ph, t)
    end = (dt.datetime.strptime(t, "%Y-%m-%d %H:%M") + dt.timedelta(seconds=dur)).strftime("%Y-%m-%dT%H:%M:%S+05:30")
    con.execute("INSERT INTO calls (direction, answered, total_duration, customer_talk_duration, customer_ring_duration, "
                "recording_filename, ended_at_ist, phone10, join_key, client_ref_id, status) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (direction, 1 if answered else 0, str(dur), str((dur if talk is None else talk) if answered else 0), str(ring), "r.mp3" if answered else "",
                 end, ph, k, "", ""))
    if agent:
        con.execute("INSERT OR REPLACE INTO call_agent VALUES (?,?,?,?)", (k, agent, "", "test"))
    if claimed or ai:
        con.execute("INSERT INTO verdicts (join_key, agent, claimed_outcome, ai_outcome, verdict, evidence) VALUES (?,?,?,?,?,?)",
                    (k, agent, claimed, ai, "Mismatch" if (claimed and ai and claimed != ai) else "Match", ev))


# follow-up patients
call(N(1), "2026-11-07 10:00", "Out", True, 60, "Shivani Srivastava", "coming", "coming", "kal aa jayenge")
call(N(3), "2026-11-06 11:00", "Out", False, 0, "Alisha")
call(N(3), "2026-11-07 09:00", "Out", False, 0, "Alisha")
call(N(4), "2026-11-06 12:00", "Out", True, 45, "Shavez Khan", "not_coming", "not_coming")
call(N(6), "2026-11-05 12:00", "Out", True, 50, "Shivani Srivastava", "", "not_coming", "nahi aana")
# people today (unknown numbers)
call(N(99), "2026-11-07 09:58", "In", False, 0)
call(N(99), "2026-11-07 10:12", "In", True, 80, "Shivani Srivastava")
call(N(96), "2026-11-07 08:00", "In", False, 0)
call(N(96), "2026-11-07 08:30", "Out", True, 40, "Shivani Srivastava")
call(N(95), "2026-11-07 10:00", "Out", True, 40, "Shivani Srivastava")
call(N(94), "2026-11-07 10:00", "Out", True, 40, "Shivani Srivastava")
call(N(92), "2026-11-07 09:00", "In", False, 0)
call(N(91), "2026-11-07 09:00", "In", False, 0)
call(N(90), "2026-11-07 08:00", "In", False, 0)
call(N(89), "2026-11-07 09:30", "Out", True, 40, "Shivani Srivastava", ring=25, talk=15)
call(N(20), "2026-11-03 10:00", "Out", False, 0, "Alisha")
call(N(88), "2026-11-07 11:00", "Out", True, 70, "Shivani Srivastava", "not_coming", "coming", "haan aaunga")
call(N(87), "2026-11-07 10:30", "Out", True, 50, "Dr Manoj Agarwal")
FU_H = ["Key", "Section", "PR", "Patient Name", "Mobile", "Diagnosis", "Due Date", "OD", "Status"]
FU_R = [["k1", "Due Today", "", "Asha Test", N(1), "knee pain", "07-Nov-2026", "0", "Due Today"],
        ["k1b", "Probable Dropout", "", "Asha Test", N(1), "knee pain", "20-Oct-2026", "18", "Probable Dropout"],
        ["k2", "Grace Period", "", "Bina Test", N(2), "back pain", "05-Nov-2026", "2", "Grace Period"],
        ["k3", "Actionable Missed Follow-Up", "", "Chand Test", N(3), "shoulder", "01-Nov-2026", "6", "Actionable"],
        ["k4", "Probable Dropout", "", "Dev Test", N(4), "wrist", "10-Oct-2026", "28", "Probable Dropout"],
        ["k5", "Grace Period", "", "Esha Test", N(5), "ankle", "06-Nov-2026", "1", "Grace Period"],
        ["k6", "Probable Dropout", "", "Faiz Test", N(6), "hip", "01-Oct-2026", "37", "Probable Dropout"],
        ["k7", "Due Today", "", "Gita Test", N(7), "knee", "07-Nov-2026", "0", "Due Today"],
        ["k8", "Invalid Mobile / No Contact", "", "Hari NoPhone", "", "", "04-Nov-2026", "3", "Invalid Mobile"],
        ["k9", "Due Today", "", "Ira Future", N(9), "", "09-Nov-2026", "-2", "upcoming"],
        ["k10", "Due Today", "", "Bad Date", N(10), "", "not a date", "", ""],
        ["k11", "Actionable Missed Follow-Up", "", "Jai Rebooked", N(20), "", "01-Nov-2026", "6", "Actionable"],
        ["k12", "Due Today", "", "Jai Rebooked", N(20), "", "12-Nov-2026", "-5", "upcoming"]]
meta = B.build_fu_all(con, FU_H, FU_R)
con.execute("INSERT INTO meta VALUES ('fu_all', ?)", (json.dumps(meta),))
con.execute("INSERT INTO meta VALUES ('built_at', '2026-11-07T11:50:00+05:30')")
con.commit()
con.close()

# ---------------------------------------------------------------- inbox.db, made up
ib = sqlite3.connect(os.path.join(TMP, "inbox.db"))
ib.execute("CREATE TABLE msgs(rid INTEGER PRIMARY KEY AUTOINCREMENT, mid TEXT UNIQUE, phone TEXT NOT NULL, dir TEXT NOT NULL, "
           "ts TEXT NOT NULL, mtype TEXT, body TEXT, media_url TEXT, mime TEXT, fname TEXT, local_path TEXT, status TEXT, sent_by TEXT, src TEXT)")
W = [(N(5), "in", "2026-11-06T16:00:00+05:30", "text", "dard kam hai, kab aaun", "received", ""),
     (N(98), "in", "2026-11-07T10:07:00+05:30", "text", "appointment chahiye", "received", ""),
     (N(97), "in", "2026-11-07T09:00:00+05:30", "text", "report bhej diya", "received", ""),
     (N(97), "out", "2026-11-07T09:30:00+05:30", "text", "ji mil gaya", "delivered", "shivani"),
     (N(96), "in", "2026-11-07T09:00:00+05:30", "text", "hello", "received", ""),
     (N(96), "out", "2026-11-07T09:10:00+05:30", "template", "Template: hours", "delivered", "shivani"),
     (N(95), "in", "2026-11-07T09:00:00+05:30", "text", "call me", "received", ""),
     (N(94), "in", "2026-11-07T07:00:00+05:30", "text", "call me early", "received", ""),
     (N(93), "in", "2026-11-07T09:00:00+05:30", "text", "x", "received", ""),
     (N(93), "out", "2026-11-07T09:05:00+05:30", "text", "reply", "failed", "alisha"),
     (N(92), "out", "2026-11-07T09:05:00+05:30", "template", "Template: hours", "delivered", "shivani"),
     (N(91), "out", "2026-11-07T09:05:00+05:30", "text", "call karein", "failed", "shivani"),
     (N(90), "in", "2026-11-07T08:10:00+05:30", "text", "missed call kiya tha", "received", ""),
     (N(90), "out", "2026-11-07T08:20:00+05:30", "text", "ji batayein", "delivered", "shivani"),
     (N(89), "in", "2026-11-07T09:00:00+05:30", "text", "please call", "received", "")]
for i, (ph, d, ts, mt, body, st, by) in enumerate(W):
    ib.execute("INSERT INTO msgs (mid, phone, dir, ts, mtype, body, status, sent_by) VALUES (?,?,?,?,?,?,?,?)",
               ("m%d" % i, ph, d, ts, mt, body, st, by))
ib.commit()
ib.close()

# ---------------------------------------------------------------- finance.db (patient_visit only), made up
fd = sqlite3.connect(os.environ["FINANCE_DB"])
fd.execute("CREATE TABLE patient_visit (visit_id TEXT, visit_date TEXT, clinic_id TEXT, patient_uid TEXT, mobile_fp TEXT, had_procedure INTEGER)")
for i, (d, cid) in enumerate([("2026-11-07", "C-1007"), ("2026-11-05", "C-2001"), ("2026-10-15", "C-1001")]):
    fd.execute("INSERT INTO patient_visit VALUES (?,?,?,?,?,?)", ("v%d" % i, d, cid, "", "", 0))
fd.commit()
fd.close()

# ---------------------------------------------------------------- the ring store, made up
import ring_common as RC   # noqa: E402
import ring_outcome as RO   # noqa: E402
RC._fp = lambda m10: ("fp" + m10) if m10 else ""          # made-up fingerprints for the walk (the box's salt never read)
RO.init_db(os.environ["RING_OUTCOME_DB"])
rs = sqlite3.connect(os.environ["RING_OUTCOME_DB"])
cols = {r[1] for r in rs.execute("PRAGMA table_info(outcome)")}
for sid, when, mob, pat, cid, appt in (("s1", "2026-11-03 11:00", N(11), "Kamal Test", "C-2001", "2026-11-05"),
                                       ("s2", "2026-11-04 11:00", N(12), "Lata Test", "C-2002", "2026-11-10"),
                                       ("s3", "2026-11-02 11:00", N(13), "Mohan Test", "C-2003", "2026-11-04"),
                                       ("s4", "2026-10-20 11:00", N(14), "Old Test", "C-2004", "2026-10-22")):
    rs.execute("INSERT INTO outcome (sid, mobile, patient, clinic_id, login, handler, code, when_ist, created_at%s) "
               "VALUES (?,?,?,?,?,?,?,?,?%s)" % ((", appt_day", ", ?") if "appt_day" in cols else ("", "")),
               ((sid, mob, pat, cid, "shivani", "Shivani", "appointment_booked", when, 0) + ((appt,) if "appt_day" in cols else ())))
rs.commit()
rs.close()
RO.set_follow_from("2026-10-01", "walk", path=os.environ["RING_OUTCOME_DB"], now=NOW)

# ---------------------------------------------------------------- staff list and punches, made up (S744)
SM = os.path.join(TMP, "staff_master.csv")
with open(SM, "w", encoding="utf-8") as fh:
    fh.write("user_id,name,department,base_salary,allowed_offs,wd_start,wd_end,sun_start,sun_end,active\n")
    fh.write("1,Shivani Srivastava,reception,777777,4,09:00,17:00,,,Y\n")
    fh.write("2,Alisha,reception,777777,4,16:00,20:00,,,Y\n")
    fh.write("3,Shavez Khan,office,777777,4,09:00,18:00,,,Y\n")
    fh.write("4,Ravi One,x,777777,4,09:00,18:00,,,Y\n5,Ravi Two,x,777777,4,09:00,18:00,,,Y\n6,Gone Staff,x,777777,4,09:00,18:00,,,N\n")
PU = os.path.join(TMP, "punches.csv")
with open(PU, "w", encoding="utf-8") as fh:
    fh.write("user_id,datetime\n1,2026-11-07 09:02:00\n1,2026-11-07 13:30:00\n3,2026-11-07 08:55:00\n1,2026-11-06 09:10:00\n")

# ---------------------------------------------------------------- the page
C = load("calls_console", os.path.join(PAGE_DIR, "calls_console.py"))
from flask import Flask   # noqa: E402
app = Flask("walk")
CFG = {"PORTAL_INBOX_DB": os.path.join(TMP, "inbox.db"), "FINANCE_DB_PATH": os.environ["FINANCE_DB"],
       "SR_STAFF_MASTER": SM, "SR_PUNCH_CSV": PU}


def console_conn():
    c = sqlite3.connect("file:%s?mode=ro" % os.path.join(TMP, "console.db"), uri=True)
    c.row_factory = sqlite3.Row
    return c


C.register(app, lambda f: f, lambda: "manoj", lambda k, d=None: CFG.get(k, d),
           {"console_conn": console_conn, "console_meta": lambda: {"ok": True, "built_at": "2026-11-07T11:50:00+05:30"},
            "spam_phones": lambda: [], "reviews_maps": lambda: ({}, {})})
conn = console_conn()
D = {}
try:
    D = C.page_data(conn, now=NOW, inbox_path=CFG["PORTAL_INBOX_DB"], fin_db=CFG["FINANCE_DB_PATH"], master_path=SM, punch_path=PU)
except Exception as e:
    print("page_data failed: %s %s" % (type(e).__name__, e))
_fp_keep = RC._fp
RC._fp = lambda m10: ""
try:
    BLIND = C.followup_list(console_conn(), NOW, fin_db=CFG["FINANCE_DB_PATH"], inbox_path=CFG["PORTAL_INBOX_DB"])
except Exception:
    BLIND = {}
RC._fp = _fp_keep
HTML = ""
try:
    with app.test_request_context("/portal/console"):
        HTML = C.render(conn, {}, now=NOW)
except Exception as e:
    print("render failed: %s %s" % (type(e).__name__, e))


def person(ph):
    return next(p for p in D["people"] if p["phone"] == ph)


def fu_row(ph):
    for k, t, s, rows, *_ in D["fu"]["bands"]:
        for r in rows:
            if r["phone"] == ph:
                return k, r
    for r in D["fu"]["came"]:
        if r["phone"] == ph:
            return "came", r
    return None, None


def band(k):
    return next(b for b in D["fu"]["bands"] if b[0] == k)


# builder
check("B1 build_fu_all keeps every row with a readable date (12 of 13) and counts the bad one", lambda: meta["rows"] == 12 and meta["bad_due"] == 1 and meta["no_phone"] == 1, False)
# whatsapp + people
check("W1 a WhatsApp with no reply is rose, 'WhatsApp awaiting'", lambda: person(N(98))["state"] == "rose" and person(N(98))["state_h"].startswith("WhatsApp awaiting"))
check("W2 a delivered reply answers a WhatsApp", lambda: person(N(97))["state"] == "green" and "WhatsApp" in person(N(97))["state_h"])
check("W3 a template never answers, nor counts as a try: rose", lambda: person(N(96))["state"] == "rose")
check("W4 an answered call of 40 s within 2 h answers a WhatsApp", lambda: person(N(95))["state"] == "green" and "call" in person(N(95))["state_h"])
check("W5 an answered call 3 h later does NOT answer it", lambda: person(N(94))["state"] == "amber")
check("W6 a failed reply never counts, nor as a try: rose", lambda: person(N(93))["state"] == "rose")
check("W7 the strip counts WhatsApps received and replies delivered", lambda: D["counts"]["wa_in"] == 8 and D["counts"]["wa_replied"] == 2 and D["counts"]["wa_people"] == 8)
check("W10 a missed call then only a template: still rose (R1 blocker 1)", lambda: person(N(92))["state"] == "rose")
check("W11 a missed call then a failed reply: still rose", lambda: person(N(91))["state"] == "rose")
check("W12 a missed call is not answered by a WhatsApp reply (R1 blocker 2)", lambda: person(N(90))["state"] == "rose")
check("W13 a call of 40 s with 15 s spoken does not answer a WhatsApp", lambda: person(N(89))["state"] != "green")
check("F16 a patient given a later date is not chased on the old one", lambda: fu_row(N(20))[0] is None)
check("F18 a fingerprint that cannot be made is said on the page (visits_ok false)", lambda: BLIND.get("visits_ok") is False and BLIND.get("found") is True)
check("F17 visits read and the fingerprint made: visits_ok", lambda: D["fu"]["visits_ok"] is True)
check("W8 call counts count calls only (n_calls excludes WhatsApps)", lambda: person(N(97))["n_calls"] == 0 and person(N(97))["n_wa"] == 2)
check("W9 Needs you says 'WhatsApp not answered' for the waiting one", lambda: any(n["phone"] == N(98) and n["text"] == "WhatsApp not answered" for n in D["needs"]))
check("A1 missed then they rang again and got through is told apart", lambda: D["counts"]["miss_then_again"] == 1 and D["counts"]["miss_then_back"] == 1)
# follow-ups
check("F1 repeats folded: Asha once, at her latest due (today)", lambda: fu_row(N(1))[0] == "today" and D["fu"]["removed"] == 2)
check("F2 today's due shown (F-1106): Asha reached, coming", lambda: fu_row(N(1))[1]["pill"].startswith("Reached") and fu_row(N(1))[1]["tone"] == "green")
check("F3 grace, no contact: Not called yet, rose", lambda: fu_row(N(2))[0] == "grace" and fu_row(N(2))[1]["pill"] == "Not called yet")
check("F4 overdue, two unanswered calls: Not reached x 2", lambda: fu_row(N(3))[0] == "overdue" and fu_row(N(3))[1]["pill"] == "Not reached × 2")
check("F5 a filed 'not coming' closes the row (Came / closed)", lambda: fu_row(N(4))[0] == "came" and fu_row(N(4))[1]["closed"] == "notcoming")
check("F6 a WhatsApp from the patient with no reply: Wrote back, to call", lambda: fu_row(N(5))[1]["pill"] == "Wrote back · to call")
check("F7 the AI heard 'not coming' but nobody filed it: stays open, amber", lambda: fu_row(N(6))[0] == "lapsed" and "not filed" in fu_row(N(6))[1]["pill"])
check("F8 a Docterz visit on the due day closes it as came", lambda: fu_row(N(7))[0] == "came" and fu_row(N(7))[1]["closed"] == "came")
check("F9 a visit BEFORE the due date does not close (Asha's 15 Oct)", lambda: not fu_row(N(1))[1]["closed"])
check("F10 no mobile: kept, no Call button", lambda: any(r["name"] == "Hari NoPhone" and not r["phone"] for r in band("grace")[3]))
check("F11 a due date after today is left out", lambda: fu_row(N(9))[0] is None)
check("F12 today's line: 2 due, 1 called, 1 reached, 1 came", lambda: D["fu"]["today"] == {"due": 2, "called": 1, "reached": 1, "came": 1})
check("F13 who called today: Shivani 1, Alisha 1", lambda: dict(D["fu"]["who"]) == {"Shivani": 1, "Alisha": 1})
check("F14 called-of per section (grace: 0 of 3)", lambda: band("grace")[4] == 3 and band("grace")[5] == 0 and band("grace")[7] == "amber")
check("F15 lapsed with an uncalled row is rose; all called is green", lambda: band("lapsed")[7] == "green" and band("overdue")[7] == "green")
# call ke baad
check("K1 Call ke baad, the week: 3 booked, 1 came, 1 awaited, 1 never came", lambda: (D["ckb"]["booked"], D["ckb"]["came"], D["ckb"]["due"], D["ckb"]["noshow"]) == (3, 1, 1, 1))
check("K2 per staff: Shivani 3", lambda: D["ckb"]["staff"][0][0] == "Shivani" and D["ckb"]["staff"][0][1]["booked"] == 3)
check("K3 the never-came row carries name, ID and a number to call", lambda: D["ckb"]["never"][0]["cid"] == "C-2003" and D["ckb"]["never"][0]["phone"] == N(13))
# the page
check("P1 the page renders", lambda: "<html" in HTML and "Follow-ups" in HTML)
check("P2 the key is one line, short labels", lambda: 'class="key"' in HTML and ">No answer</span>" in HTML and "Incoming call — connected" not in HTML)
check("P3 no section opens by itself (every <details> folded)", lambda: HTML.count("<details") > 5 and not __import__("re").search(r"<details[^>]*\sopen[\s>=]", HTML))
check("P4 the sections carry their colour on the top line", lambda: 'details class="s amber"' in HTML and 'details class="s green"' in HTML)
check("P5 the follow-up rows show the quote and the clinic ID", lambda: "kal aa jayenge" in HTML and "C-1003" in HTML)
check("P6 Call ke baad and the never-came row on the page", lambda: 'id="ckb"' in HTML and "Mohan Test" in HTML)
check("P7 the WhatsApp text in the timeline", lambda: "appointment chahiye" in HTML)
check("P8 the two-column layout", lambda: HTML.count('class="col"') == 2)
check("P9 the as-of carries the day", lambda: "as of 11:50, Sat 7 Nov" in HTML)
check("P10 the old routes kept: the player, transcripts, review form", lambda: 'id="pl"' in HTML and "wholeTx" in HTML and "/portal/console/review" in HTML, False)
def card(k):
    return next((c for c in D["staff"] if c["key"] == k), None)


check("S1 one card per call handler today: Shivani, Alisha, and Shavez (on duty, no call of his own); never you", lambda: sorted(c["key"] for c in D["staff"]) == ["alisha", "shavez", "shivani"] and card("shavez")["made"] == 0)
check("S2 Shivani: answered 1 of 2 rung on duty", lambda: (card("shivani")["answered"], card("shivani")["rung"]) == (1, 2))
check("S3 missed on duty 1, called back within the hour 1, none left", lambda: (card("shivani")["missed"], card("shivani")["cb_in_h"], len(card("shivani")["not_back"])) == (1, 1, 0))
check("S4 a missed call before her punch is not hers", lambda: card("shivani")["missed"] == 1)
check("S5 calls made 6", lambda: card("shivani")["made"] == 6)
check("S6 not logged 5, staff vs AI 1, agreed 1: rose, 6 to check", lambda: (len(card("shivani")["not_logged"]), len(card("shivani")["mismatch"]), card("shivani")["agreed"], card("shivani")["tone"], card("shivani")["check"]) == (5, 1, 1, "rose", 6))
check("S7 WhatsApps on her duty: 1 in, 0 answered", lambda: (card("shivani")["wa_in"], card("shivani")["wa_ans"]) == (1, 0))
check("S8 her duty and punch", lambda: card("shivani")["duty_h"] == "on duty 09:00–17:00" and card("shivani")["punch_h"] == "punched 09:02")
check("S9 Alisha: not punched yet, nothing missed counted to her, clear", lambda: card("alisha")["punch_h"] == "not punched yet" and card("alisha")["missed"] == 0 and card("alisha")["tone"] == "green" and card("alisha")["made"] == 1)
check("S10 two staff sharing a first name are never matched; an inactive one is left out", lambda: "ravi" not in C.load_duty(SM, PU, ["2026-11-07"])[0] and "gone" not in C.load_duty(SM, PU, ["2026-11-07"])[0])
check("S11 an unreadable staff list is said on the card", lambda: C.staff_cards(D["people"], "2026-11-07", "2026-11-07", NOW, master_path=os.path.join(TMP, "nope.csv"), punch_path=PU)[0]["duty_h"].startswith("the duty list could not be read"))
PB = os.path.join(TMP, "punches_bom.csv")
open(PB, "w", encoding="utf-8-sig").write("user_id,datetime\n01,2026-11-07 09:02:00\n")
check("S15 a missing punch log is said on a matched card, and the card is not 'all clear'", lambda: [c for c in C.staff_cards(D["people"], "2026-11-07", "2026-11-07", NOW, master_path=SM, punch_path=os.path.join(TMP, "nope.csv"), agents={"shivani": {"x"}, "alisha": {"y"}}) if c["key"] == "alisha"][0]["tone"] == "amber" and "punch log could not be read" in [c for c in C.staff_cards(D["people"], "2026-11-07", "2026-11-07", NOW, master_path=SM, punch_path=os.path.join(TMP, "nope.csv")) if c["key"] == "alisha"][0]["duty_h"])
check("S16 a punch log written with a BOM and a '01' id is read", lambda: [c for c in C.staff_cards(D["people"], "2026-11-07", "2026-11-07", NOW, master_path=SM, punch_path=PB) if c["key"] == "shivani"][0]["punch_h"] == "punched 09:02")
check("S17 two agents sharing a first name: no duty is matched to them", lambda: [c for c in C.staff_cards(D["people"], "2026-11-07", "2026-11-07", NOW, master_path=SM, punch_path=PU, agents={"alisha": {"Alisha", "Alisha Khan"}}) if c["key"] == "alisha"][0]["duty_h"].startswith("two agents"))
check("S12 the staff section on the page: folded, rose top line, the lists", lambda: 'details class="s rose" id="st-shivani"' in HTML and "Not logged — answered" in HTML and "Staff ≠ AI — to check" in HTML)
check("S13 the pay column never reaches the page", lambda: "777777" not in HTML)
check("S14 the 7-day view counts duty days", lambda: [c for c in C.page_data(console_conn(), span="7", now=NOW, inbox_path=CFG["PORTAL_INBOX_DB"], fin_db=CFG["FINANCE_DB_PATH"], master_path=SM, punch_path=PU)["staff"] if c["key"] == "shivani"][0]["duty_h"] == "on duty 2 of 7 days")
if os.environ.get("WALK_DUMP"):
    open(os.environ["WALK_DUMP"], "w", encoding="utf-8").write(HTML)
conn.close()
if not os.environ.get("WALK_KEEP"):
    shutil.rmtree(TMP, ignore_errors=True)
else:
    print("KEPT", TMP)
s742 = [r for r in RES if r[2]]
red = [r for r in RES if not r[1]]
if CONTROL:
    s744 = [r for r in RES if __import__("re").match(r"S\d", r[0])]
    red744 = [r for r in s744 if not r[1]]
    kept = [r for r in RES if not __import__("re").match(r"S\d", r[0]) and r[1]]
    print("CONTROL: %d of %d S744 checks red, %d of the S742 checks kept green" % (len(red744), len(s744), len(kept)))
    sys.exit(0 if len(red744) >= len(s744) - 1 else 1)
print("WALK %s: %d of %d" % ("OK" if not red else "RED", len(RES) - len(red), len(RES)))
sys.exit(0 if not red else 1)
