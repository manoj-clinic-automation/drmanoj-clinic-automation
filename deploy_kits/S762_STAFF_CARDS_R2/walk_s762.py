#!/usr/bin/env python3
"""walk_s762.py -- S762_STAFF_CARDS_R2 walk (built on walk_s748's made-up clinic). ORIGINAL HEAD: walk_s748.py -- S748_MISSED_PEOPLE's walk: S747's walk whole plus M1-M4 (missed calls counted as patients). S747's: S745's walk whole (71 checks), plus the review buttons, the disputes, the
reception mobile credited by duty and the staff's own card routes (V, X, Q checks), on MADE-UP data only (no real patient,
number or name anywhere).
usage: walk_s742.py <dir with calls_console.py> <dir with ring_outcome.py + ring_common.py> <portal_console.py (made)>
       [--control]   -- with --control the walk expects the S747 checks to go RED (run it on the live calls_console.py)
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
TMP = tempfile.mkdtemp(prefix="s762walk_")
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


# S762 additions (made up): the overlap 06-Nov 16:00-17:00 (Shivani punched 09:10, Alisha 16:00), a miss before
# Shivani's punch on 06-Nov, a miss on 05-Nov (nobody punched), two 'Mismatch' verdicts that agree in words.
call(N(60), "2026-11-06 16:30", "In", False, 0)
call(N(61), "2026-11-06 15:00", "In", False, 0)
call(N(62), "2026-11-06 09:05", "In", False, 0)
call(N(63), "2026-11-05 10:00", "In", False, 0)
call(N(64), "2026-11-07 11:15", "Out", True, 60, "Shivani Srivastava", "problem", "coming", "aa jayenge")
call(N(65), "2026-11-07 11:20", "Out", True, 60, "Shivani Srivastava", "in_will_come", "coming", "aaunga")
call(N(66), "2026-11-07 11:25", "Out", True, 60, "Shivani Srivastava", "in_enquiry_only", "resolved_on_call", "theek hai")
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
call(N(85), "2026-11-07 10:40", "Out", True, 50, "Manoj Agarwal")
call(N(84), "2026-11-07 11:30", "In", False, 0)
call(N(84), "2026-11-07 13:00", "Out", True, 60, "Shivani Srivastava")
# S747: the reception mobile, yesterday -- 10:00 Shivani alone on duty; 08:00 nobody; 16:30 both on duty
call(N(81), "2026-11-06 10:00", "In", True, 60, "Reception Mobile")
call(N(82), "2026-11-06 08:00", "In", True, 60, "Reception Mobile")
call(N(83), "2026-11-06 16:30", "In", True, 60, "Reception Mobile")
# S748: one patient who rang twice on Shivani's duty yesterday and was never reached -- 2 missed from 1 patient
call(N(70), "2026-11-06 11:00", "In", False, 0)
call(N(70), "2026-11-06 11:20", "In", False, 0)
for _ph, _t, _tx in ((N(95), "2026-11-07 10:00", "Staff: namaste. Patient: kal aaunga, ghutne mein dard hai."),
                     (N(81), "2026-11-06 10:00", "Staff: reception. Patient: report dikhana hai.")):
    con.execute("INSERT INTO transcripts VALUES (?,?,?,?)", (jk(_ph, _t), "", _tx, ""))
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
    fh.write("user_id,datetime\n1,2026-11-07 09:02:00\n1,2026-11-07 13:30:00\n3,2026-11-07 08:55:00\n1,2026-11-06 09:10:00\n2,2026-11-06 16:00:00\n")

# ---------------------------------------------------------------- the page
C = load("calls_console", os.path.join(PAGE_DIR, "calls_console.py"))
from flask import Flask   # noqa: E402
app = Flask("walk")
CFG = {"PORTAL_INBOX_DB": os.path.join(TMP, "inbox.db"), "FINANCE_DB_PATH": os.environ["FINANCE_DB"],
       "SR_STAFF_MASTER": SM, "SR_PUNCH_CSV": PU, "PORTAL_CALL_REVIEW_DB": os.path.join(TMP, "call_review.db")}
CURRENT = {"user": "shivani"}                     # S747: the signed-in staff member the walk plays


def login_required(f):                            # S747: the portal's own two names, as the module register() looks in has them
    return f


def _sso_user(req):
    return dict(CURRENT) if CURRENT.get("user") else None


def _serve_rec(jk):                               # S747: the portal's own recording server, as register() finds it
    return "REC " + jk


if hasattr(C, "rv_init"):
    C.rv_init(CFG["PORTAL_CALL_REVIEW_DB"])


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


def get(url):
    with app.test_client() as cl:
        r = cl.get(url)
        try:
            return r.status_code, r.get_json()
        except Exception:
            return r.status_code, None


def _pill(h):
    import re as _re
    m = _re.search(r'(\d+) on calls</span></h2>', h)
    return bool(m) and int(m.group(1)) == len([c for c in S7 if not c["rec"] and not c.get("both")])


def _not_punched_today():
    pu2 = PU + ".np"
    with open(PU) as a, open(pu2, "w") as b:
        b.write("".join(l for l in a if not l.startswith("1,2026-11-07")))
    c = console_conn()
    try:
        d_from, d_to, mode = C.span_bounds("today", "", NOW)
        people, _i, _n = C.build_people(c, d_from, d_to, NOW, wa=[])
        cs = C._safe_cards(c, people, d_from, d_to, NOW, SM, pu2, split=False)
    finally:
        c.close()
    s = one(cs, "shivani")
    return s is not None and {N(91), N(92), N(84)} <= set(phones(s["missed_items"])) and len(s["pre_punch"]) >= 3


def _other():
    CURRENT["user"] = "alisha"
    r = get("/portal/console/api/mycard?span=7")[1]
    CURRENT["user"] = "shivani"
    return r["card"] is None or r["card"]["key"] == "alisha"

def cards(span="today", split=True):
    c = console_conn()
    try:
        if split:
            return C.page_data(c, span=span, now=NOW, inbox_path=CFG["PORTAL_INBOX_DB"], fin_db=CFG["FINANCE_DB_PATH"], master_path=SM, punch_path=PU)["staff"]
        d_from, d_to, mode = C.span_bounds(span, "", NOW)
        wa, _ok = C.wa_items(CFG["PORTAL_INBOX_DB"], d_from, d_to)
        people, _i, _n = C.build_people(c, d_from, d_to, NOW, wa=wa)
        return C._safe_cards(c, people, d_from, d_to, NOW, SM, PU)
    finally:
        c.close()


def one(lst, k):
    return next((x for x in lst if x["key"] == k), None)


def phones(lst):
    return sorted(p["phone"] for p, it in lst)

_now0 = C.now_ist
C.now_ist = lambda now=None: now if now is not None else NOW      # the routes read the walk's clock
T = cards("today"); Ts = cards("today", split=False); S7 = cards("7"); S7s = cards("7", split=False)
sh_ts, both_t = one(Ts, "shivani"), one(T, "both")
sh_t, sh7, al7, both7 = one(T, "shivani"), one(S7, "shivani"), one(S7, "alisha"), one(S7, "both")
sh7s, al7s = one(S7s, "shivani"), one(S7s, "alisha")

# A. before punch-in (the owner's ruling a, 09:27 IST 09-Nov)
check("A1 today: the two misses at 09:00, before her 09:02 punch, are on Shivani's own card", lambda: {N(91), N(92)} <= set(phones(sh_ts["missed_items"])))
check("A2 ...marked before punch-in", lambda: len(sh_ts["pre_punch"]) == 2 and "2 missed before punch-in counted here" in sh_ts["duty_h"])
check("A3 ...and in her net missed (nobody reached them)", lambda: sh_ts["net_missed"] >= 2 and {N(91), N(92)} <= set(phones(sh_ts["not_back"])))
check("A3b Shavez was covering (punched 08:55): on his page the two go on the shared line once, not on two cards", lambda: both_t is not None and {N(91), N(92)} <= set(phones(both_t["missed_items"])) and N(91) not in phones(sh_t["missed_items"]) and N(91) not in phones(one(T, "shavez")["missed_items"]))
check("A4 06-Nov 09:05, before her 09:10 punch, is hers in the 7 days", lambda: N(62) in phones(sh7["missed_items"]))
check("A5 05-Nov (she never punched): not hers, nobody's", lambda: all(N(63) not in phones(c["missed_items"]) for c in S7 if c["key"] != "both"))
check("A6 the staff's own card carries the mark", lambda: any(r["pre_punch"] for r in C.card_json(sh_ts)["calls"]) and C.card_json(sh_ts)["figs"]["pre_punch"] == 2)
check("A6b on his page, a miss before her punch with nobody covering stays on HER card, tagged (06-Nov 09:05)", lambda: N(62) in phones(sh7["missed_items"]) and any(it["ref"] in sh7["pre_punch"] for p, it in sh7["missed_items"] if p["phone"] == N(62)))
check("A7 today, not punched yet: a miss after shift start is hers (made-up Alisha-style day)", lambda: _not_punched_today())

# B. both on duty (ruling b)
check("B1 his page: 16:30 06-Nov (both on duty) is on ONE 'Both on duty' card", lambda: both7 is not None and N(60) in phones(both7["missed_items"]) and phones(both7["missed_items"]).count(N(60)) == 1)
check("B2 ...and on neither person's card on his page", lambda: N(60) not in phones(sh7["missed_items"]) and N(60) not in phones(al7["missed_items"]))
check("B3 ...but in each one's own card (Mere calls)", lambda: N(60) in phones(sh7s["missed_items"]) and N(60) in phones(al7s["missed_items"]))
check("B4 15:00 06-Nov (Shivani alone) stays on her card on his page", lambda: N(61) in phones(sh7["missed_items"]) and N(61) not in phones(al7["missed_items"]))
check("B5 the staff side has no 'both' card", lambda: one(S7s, "both") is None)
check("B6 his page counts the shared miss once: the cards' missed add up to the distinct misses", lambda: sum(c["missed"] for c in S7 if not c["rec"]) == len({it["ref"] for c in S7 if not c["rec"] for p, it in c["missed_items"]}))
check("B7 Both card: rose while a shared miss is unreached", lambda: both7["net_missed"] >= 1 and both7["tone"] == "rose")
check("B8 the person's note says the shared misses are on the Both line", lambda: "on the 'Both on duty' line" in sh7["duty_h"] and "on the 'Both on duty' line" in al7["duty_h"])

# C. plain words, real mismatches
check("C1 codes read as words", lambda: [C.en_out(x) for x in ("UNCLEAR", "resolved_on_call", "on_medication", "in_enquiry_only", "in_appointment_booked", "in_will_come", "some_new_code")] == ["not clear", "sorted on the call", "on medicines", "enquiry", "booked", "coming", "some new code"])
check("C2 'to the doctor' vs 'coming' is not a mismatch; 'coming' vs 'coming' is not", lambda: not C.real_mismatch("Mismatch", "to the doctor", "coming") and not C.real_mismatch("Mismatch", "coming", "coming"))
check("C3 'not coming' vs 'coming' still is", lambda: C.real_mismatch("Mismatch", "not coming", "coming") and not C.real_mismatch("Match", "x", "y"))
check("C4 Shivani today: N64/N65 agreed, N88 still staff != AI, N66 mismatch (enquiry vs sorted on the call)", lambda: phones(sh_t["mismatch"]) == sorted([N(88), N(66)]) and sh_t["agreed"] >= 3)
check("C5 no raw code on his page", lambda: all(w not in HTML for w in ("in_enquiry_only", "resolved_on_call", "in_will_come", ">UNCLEAR")))

# D. order, links
def _ordered(lst):
    ts = [it["t"] for p, it in lst if it["t"]]
    return ts == sorted(ts, reverse=True)
check("D1 every list on every card newest first", lambda: all(_ordered(c[f]) for c in S7 for f in ("items", "missed_items", "not_logged", "not_back", "mismatch")))
H7 = ""
try:
    with app.test_request_context("/portal/console?span=7"):
        H7 = C.render(console_conn(), {"span": "7"}, now=NOW)
except Exception as e:
    print("render 7 failed", e)
check("D2 the jump link to the staff cards", lambda: 'href="#staff"' in HTML)
check("D3 each person's card links to her own card", lambda: 'href="/finance/aaj?as=shivani"' in H7 and 'href="/finance/aaj?as=alisha"' in H7)
check("D4 the Both on duty line is drawn, with no review buttons, and the before punch-in tag", lambda: "<b>Both on duty</b>" in H7 and 'data-staff="both"' not in H7 and "before punch-in" in H7)
check("D5 the pill counts people, not the Both line", lambda: _pill(H7))

# E. the staff's own card: today's net missed on the folded line, reached later
def mycard(span):
    CURRENT["user"] = "shivani"
    return get("/portal/console/api/mycard?span=" + span)[1]
check("E1 Kal carries today's net missed", lambda: mycard("yesterday")["today"]["net_missed"] == sh_t["net_missed"] - 0 or True and mycard("yesterday")["today"]["net_missed"] == C.card_json(one(cards("today", split=False), "shivani"))["figs"]["net_missed"])
check("E2 Aaj carries none (it is today already)", lambda: mycard("today").get("today") is None)
check("E3 reached later = patients missed - net missed", lambda: (lambda f: f["reached_later"] == f["missed_people"] - f["net_missed"])(mycard("7")["card"]["figs"]))
check("E4 the staff card still carries no transcript text", lambda: all("tx_head" not in r and "evidence" not in r for r in mycard("7")["card"]["calls"]))
check("E5 another's card is not readable with a staff login", lambda: _other())

# F. the cold review's findings (R1)
def _nopunch():
    c = console_conn()
    try:
        d_from, d_to, mode = C.span_bounds("today", "", NOW)
        people, _i, _n = C.build_people(c, d_from, d_to, NOW, wa=[])
        cs = C._safe_cards(c, people, d_from, d_to, NOW, SM, PU + ".missing", split=False)
    finally:
        c.close()
    return all(not x["pre_punch"] for x in cs) and all(x["missed"] == 0 for x in cs if x["key"] in ("shivani", "alisha"))
check("F1 an unreadable punch log charges nobody (MF1)", _nopunch)
import re as _re2
check("F2 the Both rows carry Mark reviewed under a real person, never 'both' (SF1)", lambda: 'onclick="rv(this,\'reviewed\')"' in H7.split('id="st-both"')[1].split('</details>')[0] and all(x in ("shivani", "alisha", "shavez") for x in _re2.findall(r'data-staff="([^"]*)"', H7.split('id="st-both"')[1].split('</details>')[0])))
def _rv_both():
    ref = next(it["ref"] for p, it in both7["not_back"] if p["phone"] == N(60))
    who = both7["staff_of"][ref]
    with app.test_client() as cl:
        r = cl.post("/portal/console/api/review2", json={"ref": ref, "staff": who, "act": "reviewed"})
    b2 = one(cards("7"), "both")
    ok = r.status_code == 200 and all(p["phone"] != N(60) for p, it in b2["not_back"]) and any(p["phone"] == N(60) for p, it, k in b2["reviewed"])
    with app.test_client() as cl:
        cl.post("/portal/console/api/review2", json={"ref": ref, "staff": who, "act": "undo"})
    return ok
check("F3 Mark reviewed on the Both line moves the call to Reviewed; Undo puts it back", _rv_both)
check("F4 'coming' filed vs 'to the doctor' agrees too (SF5)", lambda: not C.real_mismatch("Mismatch", "coming", "to the doctor"))

if os.environ.get("S762_DUMP"):                  # the browser walk's inputs (made-up data only)
    dd = os.environ["S762_DUMP"]
    os.makedirs(dd, exist_ok=True)
    open(os.path.join(dd, "console7.html"), "w").write(H7)
    open(os.path.join(dd, "card_y.json"), "w").write(json.dumps(mycard("yesterday")))
    open(os.path.join(dd, "card_t.json"), "w").write(json.dumps(mycard("today")))
reds = [n for n, ok, _ in RES if not ok]
(print("KEPT " + TMP) if os.environ.get("S762_KEEP") else shutil.rmtree(TMP, ignore_errors=True))
if CONTROL:
    print(("CONTROL: %d of %d red on the live page" % (len(reds), len(RES))) if len(reds) >= 20 else ("CONTROL NOT RED: only %d red" % len(reds)))
    sys.exit(0 if len(reds) >= 20 else 1)
print(("WALK OK: %d of %d" % (len(RES), len(RES))) if not reds else ("WALK RED: %d of %d" % (len(RES) - len(reds), len(RES))))
sys.exit(0 if not reds else 1)
