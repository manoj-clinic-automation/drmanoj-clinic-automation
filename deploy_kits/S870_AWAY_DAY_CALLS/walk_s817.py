#!/usr/bin/env python3
"""walk_s817.py -- S817_CALLS_FOLLOWUP_LINES's walk, on MADE-UP data only (no real patient, number or name anywhere).
usage: walk_s817.py <dir with calls_console.py> <dir with ring_outcome.py + ring_common.py> <portal_console.py>
                    <finance dir (dx_feed.py, finance_patient_sync.py -- read as TEXT for the two table shapes)>
                    [<dir with the LIVE calls_console.py>] [--control] [--html OUT.html] [--stores DIR]
(--html keeps the rendered page; --stores builds the made-up stores in DIR and leaves them -- both for the bench only)
Builds a made-up console.db (the builder's own SCHEMA + build_fu_all), inbox.db, finance.db (patient_visit and dx_visit in
the shapes the live code creates them) and a ring store; reads the page's data and renders the page.
  normal     every check green on the page given; then TEN MUTATIONS of that page (the rule flipped, the visit filter
             dropped ...) each go red; with the live page's folder given, every OTHER reader's figures (the strip, the
             people, the staff cards as staff read them, Call ke baad, who called today) are compared and must be equal.
  --control  run on the LIVE (unpatched) page: the due-day call case MUST go red.
Prints one line per check; the last line is 'WALK OK: ...' / 'WALK RED: ...' / 'CONTROL: ...'."""
import datetime as dt
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

A = [x for x in sys.argv[1:] if not x.startswith("--")]
CONTROL = "--control" in sys.argv
HTML_OUT = ""
if "--html" in sys.argv:
    HTML_OUT = sys.argv[sys.argv.index("--html") + 1]
    A = [x for x in A if x != HTML_OUT]
STORES = ""
if "--stores" in sys.argv:
    STORES = sys.argv[sys.argv.index("--stores") + 1]
    A = [x for x in A if x != STORES]
    os.makedirs(STORES)
PAGE_DIR, RING_DIR, BUILDER, FIN_DIR = A[0], A[1], A[2], A[3]
LIVE_DIR = A[4] if len(A) > 4 else ""
TMP = STORES or tempfile.mkdtemp(prefix="s817walk_")
os.environ["RING_OUTCOME_DB"] = os.path.join(TMP, "ring.db")
os.environ["FINANCE_DB"] = os.path.join(TMP, "finance.db")
sys.path.insert(0, RING_DIR)
NOW = dt.datetime(2026, 11, 13, 12, 0, 0)          # a Friday, noon
TODAY = NOW.date()


def N(i):
    """a made-up ten-digit test number, built at run time (no number is written in this file -- F-185)"""
    return "5" + "0" * 6 + "%03d" % i


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def ddl_of(path, var):
    """the CREATE TABLE text a live module keeps in `var` -- read as text, the module is never run"""
    m = re.search(r'^%s\s*=\s*"""(.*?)"""' % re.escape(var), open(path, encoding="utf-8").read(), re.S | re.M)
    if not m:
        raise SystemExit("WALK RED: %s has no %s" % (path, var))
    return m.group(1)


B = load("pc_made", BUILDER)


def jk(ph, t):
    return "%s_%d" % (ph, int(dt.datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone(dt.timedelta(hours=5, minutes=30))).timestamp()))


# ---------------------------------------------------------------- the made-up clinic
# (key, name, clinic id, due day, tracker section)
PATS = [
    ("T1", "Test Aone", "T-101", "2026-11-13", "Due Today"),
    ("T2", "Test Atwo", "T-102", "2026-11-13", "Due Today"),
    ("T3", "Test Athree", "T-103", "2026-11-13", "Due Today"),
    ("T4", "Test Dueearly", "T-104", "2026-11-13", "Due Today"),         # due TODAY, 7-day advice, came 2 days ago (D893)
    ("T5", "Test Duemonth", "T-105", "2026-11-13", "Due Today"),         # due TODAY, 30-day advice, came 10 days ago
    ("G1", "Test Dueday", "T-201", "2026-11-12", "Grace Period"),       # called ONLY on the due day (answered)
    ("G2", "Test Reached", "T-202", "2026-11-11", "Grace Period"),      # reached 12-Nov, no answer today
    ("G3", "Test Before", "T-203", "2026-11-10", "Grace Period"),       # called only BEFORE the due day
    ("G4", "Test Today", "T-204", "2026-11-12", "Grace Period"),        # called today, answered
    ("G5", "Test Camelate", "T-205", "2026-11-11", "Grace Period"),     # a visit after the due date
    ("G6", "Test Cameearly", "T-206", "2026-11-12", "Grace Period"),    # 7-day advice, came 2 days early (D893)
    ("G7", "Test Prescribed", "T-207", "2026-11-12", "Grace Period"),   # 7-day advice, only the prescribing visit
    ("G8", "Test Noperiod", "T-208", "2026-11-12", "Grace Period"),     # an early visit, the period cannot be read
    ("G9", "Test Tooearly", "T-209", "2026-11-12", "Grace Period"),     # 30-day advice, a visit 23 days early
    ("G10", "Test Monthearly", "T-210", "2026-11-12", "Grace Period"),  # 30-day advice, a visit 13 days early
    ("G11", "Test Threeday", "T-211", "2026-11-12", "Grace Period"),    # 3-day advice, only the prescribing visit
    ("G12", "Test Threecame", "T-212", "2026-11-12", "Grace Period"),   # 3-day advice, came 1 day early
    ("G13", "Test Family", "T-213", "2026-11-12", "Grace Period"),      # an early visit on the same mobile, another ID
    ("G14", "Test Familylate", "T-214", "2026-11-11", "Grace Period"),  # a visit after the due date, by the mobile
    ("W1", "Test Wrote", "T-215", "2026-11-12", "Grace Period"),        # a WhatsApp on the due day, no reply
    ("G15", "Test Oneday", "T-216", "2026-11-12", "Grace Period"),      # 1-day advice, only the prescribing visit
    ("G16", "Test Rangtoday", "T-217", "2026-11-12", "Grace Period"),   # rang in TODAY and was answered; nobody called out
    ("G17", "Test Quarter", "T-218", "2026-11-12", "Grace Period"),     # 90-day advice, not back (the visits are read far back)
    ("G18", "Test Pointzero", "5512.0", "2026-11-11", "Grace Period"),  # the console's ID reads '5512.0', the visit's '5512'
    ("G19", "Testverylongunbrokenpatientnamewithoutanyspacesatallinit", "T-220", "2026-11-12", "Grace Period"),
    ("O1", "Test Tried", "T-301", "2026-11-05", "Actionable Missed Follow-Up"),
    ("O2", "Test Never", "T-302", "2026-11-03", "Actionable Missed Follow-Up"),
    ("O3", "Test Notcoming", "T-303", "2026-11-08", "Actionable Missed Follow-Up"),   # 'not coming' filed ON the due day
    ("O4", "Test Rangin", "T-304", "2026-11-07", "Actionable Missed Follow-Up"),      # the patient rang in, answered
    ("L1", "Test Lapsed", "T-401", "2026-10-20", "Probable Dropout"),
    ("L2", "Test Longago", "T-402", "2026-10-01", "Probable Dropout"),
    ("L3", "Test Seventy", "T-403", "2026-09-01", "Probable Dropout"),  # due 73 days ago; a visit 4 days later, 69 days ago
]
PH = {k: N(i + 1) for i, (k, _n, _c, _d, _s) in enumerate(PATS)}
CID = {k: c for k, _n, c, _d, _s in PATS}
CIDV = dict(CID, G18="5512")                       # the ID as patient_visit writes it

con = sqlite3.connect(os.path.join(TMP, "console.db"))
con.executescript(B.SCHEMA)
con.execute("CREATE TABLE call_agent (join_key TEXT PRIMARY KEY, agent TEXT, department TEXT, matched_how TEXT)")
for k, n, cid, _d, _s in PATS:
    con.execute("INSERT INTO patients VALUES (?,?,?,?,?,?,?,?)", (PH[k], n, "made-up knee", "50", "F", "", "", cid))


def call(k, t, direction, answered, dur, agent="", claimed="", ai="", ev=""):
    key = jk(PH[k], t)
    end = (dt.datetime.strptime(t, "%Y-%m-%d %H:%M") + dt.timedelta(seconds=dur)).strftime("%Y-%m-%dT%H:%M:%S+05:30")
    con.execute("INSERT INTO calls (direction, answered, total_duration, customer_talk_duration, customer_ring_duration, "
                "recording_filename, ended_at_ist, phone10, join_key, client_ref_id, status) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (direction, 1 if answered else 0, str(dur), str(dur if answered else 0), "12", "r.mp3" if answered else "",
                 end, PH[k], key, "", ""))
    if agent:
        con.execute("INSERT OR REPLACE INTO call_agent VALUES (?,?,?,?)", (key, agent, "", "test"))
    if claimed or ai:
        con.execute("INSERT INTO verdicts (join_key, agent, claimed_outcome, ai_outcome, verdict, evidence) VALUES (?,?,?,?,?,?)",
                    (key, agent, claimed, ai, "Match", ev))
    return key


call("T1", "2026-11-13 10:00", "Out", True, 60, "Shivani Srivastava", "coming", "coming", "aaj aa rahe hain")
call("T2", "2026-11-13 10:05", "Out", False, 0, "Shivani Srivastava")
call("T4", "2026-11-13 10:20", "Out", True, 40, "Shivani Srivastava", "coming", "coming", "aa chuke hain")
call("G16", "2026-11-13 11:40", "In", True, 60, "Shivani Srivastava", "", "coming", "kal aaunga")
call("G1", "2026-11-12 11:00", "Out", True, 50, "Shivani Srivastava", "coming", "coming", "shaam ko aayenge")
JK_G2 = call("G2", "2026-11-12 16:12", "Out", True, 75, "Alisha", "coming", "coming", "Saturday ko aayenge")
call("G2", "2026-11-13 10:42", "Out", False, 0, "Alisha")
call("G3", "2026-11-09 15:00", "Out", True, 40, "Alisha", "coming", "coming", "kal aayenge")
call("G4", "2026-11-13 11:10", "Out", True, 55, "Alisha", "coming", "coming", "kal subah")
call("O1", "2026-10-20 12:00", "Out", True, 45, "Alisha", "coming", "coming", "agle hafte")
call("O1", "2026-11-06 16:30", "Out", False, 0, "Alisha")
call("O1", "2026-11-08 16:40", "Out", False, 0, "Alisha")
call("O3", "2026-11-08 12:00", "Out", True, 45, "Shavez Khan", "not_coming", "not_coming", "nahi aana")
call("O4", "2026-11-09 13:00", "In", True, 60, "Shivani Srivastava", "", "coming", "kal aaunga")
call("L1", "2026-11-13 11:30", "Out", False, 0, "Alisha")
call("L2", "2026-09-04 11:00", "Out", True, 60, "Alisha", "coming", "coming", "aayenge")          # 70 days ago
con.execute("INSERT INTO transcripts VALUES (?,?,?,?)", (JK_G2, "", "Staff: namaste. Patient: Saturday ko aayenge.", ""))
FU_H = ["Key", "Section", "PR", "Patient Name", "Mobile", "Diagnosis", "Due Date", "OD", "Status"]
FU_R = [[k, s, "", n, PH[k], "made-up knee", dt.date.fromisoformat(d).strftime("%d-%b-%Y"), str((TODAY - dt.date.fromisoformat(d)).days), s]
        for k, n, _c, d, s in PATS]
meta = B.build_fu_all(con, FU_H, FU_R)
con.execute("INSERT INTO meta VALUES ('fu_all', ?)", (json.dumps(meta),))
con.execute("INSERT INTO meta VALUES ('built_at', '2026-11-13T11:50:00+05:30')")
con.commit()
con.close()

ib = sqlite3.connect(os.path.join(TMP, "inbox.db"))
ib.execute("CREATE TABLE msgs(rid INTEGER PRIMARY KEY AUTOINCREMENT, mid TEXT UNIQUE, phone TEXT NOT NULL, dir TEXT NOT NULL, "
           "ts TEXT NOT NULL, mtype TEXT, body TEXT, media_url TEXT, mime TEXT, fname TEXT, local_path TEXT, status TEXT, sent_by TEXT, src TEXT)")
ib.execute("INSERT INTO msgs (mid, phone, dir, ts, mtype, body, status, sent_by) VALUES (?,?,?,?,?,?,?,?)",
           ("m1", PH["W1"], "in", "2026-11-12T16:00:00+05:30", "text", "aaj nahi aa paunga, kab aaun", "received", ""))
ib.commit()
ib.close()

# finance.db: the two tables in the shapes the live code creates them (read from the live files' own text)
fd = sqlite3.connect(os.environ["FINANCE_DB"])
fd.executescript(ddl_of(os.path.join(FIN_DIR, "finance_patient_sync.py"), "VISIT_DDL"))
fd.executescript(ddl_of(os.path.join(FIN_DIR, "dx_feed.py"), "DDL"))
VIS = [("G5", "2026-11-12", ""), ("G6", "2026-11-05", ""), ("G6", "2026-11-10", ""), ("G7", "2026-11-05", ""),
       ("G8", "2026-11-05", ""), ("G8", "2026-11-10", ""), ("G9", "2026-10-13", ""), ("G9", "2026-10-20", ""),
       ("G10", "2026-10-13", ""), ("G10", "2026-10-30", ""), ("G11", "2026-11-09", ""), ("G12", "2026-11-09", ""),
       ("G12", "2026-11-11", ""), ("G15", "2026-11-11", ""),
       ("X-G13", "2026-11-10", "fp" + PH["G13"]),        # a family member (another ID) on G13's mobile, in the early window
       ("G13", "2026-11-05", ""),
       ("X-G14", "2026-11-12", "fp" + PH["G14"]),        # a visit after the due date on G14's mobile: closes, as before
       ("T4", "2026-11-06", ""), ("T4", "2026-11-11", ""), ("T5", "2026-10-14", ""), ("T5", "2026-11-03", ""),
       ("G17", "2026-08-14", ""), ("G18", "2026-11-12", ""),
       ("L3", "2026-09-05", "")]                         # after L3's due date, but before the 60 days the page reads
for i, (k, d, fp) in enumerate(VIS):
    fd.execute("INSERT INTO patient_visit (visit_id, visit_date, clinic_id, patient_uid, mobile_fp, had_procedure) VALUES (?,?,?,?,?,?)",
               ("v%d" % i, d, CIDV.get(k, "T-9%02d" % i), "u" + k, fp, ""))
DX = [("G6", "2026-11-05", "2026-11-12"), ("G7", "2026-11-05", "2026-11-12"), ("G9", "2026-10-13", "2026-11-12"),
      ("G10", "2026-10-13", "2026-11-12"), ("G11", "2026-11-09", "2026-11-12"), ("G12", "2026-11-09", "2026-11-12"),
      ("G13", "2026-11-05", "2026-11-12"), ("G1", "2026-11-05", "2026-11-12"), ("G15", "2026-11-11", "2026-11-12"),
      ("T4", "2026-11-06", "2026-11-13"), ("T5", "2026-10-14", "2026-11-13"), ("G17", "2026-08-14", "2026-11-12")]
for k, vd, fu in DX:
    fd.execute("INSERT INTO dx_visit (patient_uid, visit_date, clinic_id, follow_up_date, updated_at) VALUES (?,?,?,?,?)",
               ("u" + k, vd, CID[k], fu, "2026-11-12 21:00:00"))
fd.commit()
fd.close()

import ring_common as RC   # noqa: E402
import ring_outcome as RO   # noqa: E402
RC._fp = lambda m10: ("fp" + m10) if m10 else ""          # made-up fingerprints for the walk (the box's salt never read)
RO.init_db(os.environ["RING_OUTCOME_DB"])
try:
    RO.set_follow_from("2026-10-01", "walk", path=os.environ["RING_OUTCOME_DB"], now=NOW)
except Exception:
    pass

SM = os.path.join(TMP, "staff_master.csv")
with open(SM, "w", encoding="utf-8") as fh:
    fh.write("user_id,name,department,base_salary,allowed_offs,wd_start,wd_end,sun_start,sun_end,active\n")
    fh.write("1,Shivani Srivastava,reception,777777,4,09:00,17:00,,,Y\n2,Alisha,reception,777777,4,10:00,20:00,,,Y\n")
PU = os.path.join(TMP, "punches.csv")
with open(PU, "w", encoding="utf-8") as fh:
    fh.write("user_id,datetime\n1,2026-11-13 09:02:00\n2,2026-11-13 10:00:00\n")
CFG = {"PORTAL_INBOX_DB": os.path.join(TMP, "inbox.db"), "FINANCE_DB_PATH": os.environ["FINANCE_DB"],
       "SR_STAFF_MASTER": SM, "SR_PUNCH_CSV": PU, "PORTAL_CALL_REVIEW_DB": os.path.join(TMP, "call_review.db")}


def console_conn():
    c = sqlite3.connect("file:%s?mode=ro" % os.path.join(TMP, "console.db"), uri=True)
    c.row_factory = sqlite3.Row
    return c


_SEQ = [0]


def facts(page_file):
    """(module, page data, html) of one calls_console.py on the made-up stores"""
    from flask import Flask
    _SEQ[0] += 1
    C = load("cc_%d" % _SEQ[0], page_file)
    app = Flask("walk%d" % _SEQ[0])
    if hasattr(C, "rv_init"):
        C.rv_init(CFG["PORTAL_CALL_REVIEW_DB"])
    C.register(app, lambda f: f, lambda: "manoj", lambda k, d=None: CFG.get(k, d),
               {"console_conn": console_conn, "console_meta": lambda: {"ok": True, "built_at": "2026-11-13T11:50:00+05:30"},
                "spam_phones": lambda: [], "reviews_maps": lambda: ({}, {})})
    conn = console_conn()
    D, H = {}, ""
    try:
        D = C.page_data(conn, now=NOW, inbox_path=CFG["PORTAL_INBOX_DB"], fin_db=CFG["FINANCE_DB_PATH"], master_path=SM, punch_path=PU)
        with app.test_request_context("/portal/console"):
            H = C.render(conn, {}, now=NOW)
    except Exception as e:
        print("the page failed: %s %s" % (type(e).__name__, str(e)[:120]))
    C.walk_nodb = (0, "")
    try:                                              # the page when console.db cannot be opened at all
        keep = C._H["console_conn"]
        C._H["console_conn"] = lambda: None
        resp = app.test_client().get("/portal/console")
        C.walk_nodb = (resp.status_code, resp.get_data(as_text=True))
        C._H["console_conn"] = keep
    except Exception as e:
        C.walk_nodb = (0, type(e).__name__)
    cards = {}
    try:
        for key in ("shivani", "alisha"):
            c, _h, _m, _made = C._card_for(conn, key, "today", NOW)
            cards[key] = C.card_json(c) if c else None
    except Exception as e:
        cards = {"error": type(e).__name__}
    conn.close()
    return C, D, H, cards


def where(D, k):
    """(section, row) of made-up patient k: today | grace | overdue | lapsed | came | None"""
    fu = D.get("fu") or {}
    for b in fu.get("bands", []):
        for r in b[3]:
            if r["phone"] == PH[k]:
                return b[0], r
    for r in fu.get("came", []):
        if r["phone"] == PH[k]:
            return "came", r
    return None, None


def row(D, k):
    return where(D, k)[1] or {}


def fl(D, k):
    return (D["fu"].get("fl") or {})[k]


def band(D, k):
    return next(b for b in D["fu"]["bands"] if b[0] == k)


def sect(H, key):
    """the page's text of one folded section"""
    i = H.index('id="fu-%s"' % key)
    j = H.index("</details>", i)
    return " ".join(re.sub(r"<[^>]+>", " ", H[i:j]).split())


CHECKS = [
    # ---- the rule (b): which calls count
    ("C1 THE FAULT (F-1322): a call made ON the due day does not count for a Grace patient (called is False)",
     lambda C, D, H: where(D, "G1")[0] == "grace" and row(D, "G1")["called"] is False and row(D, "G1")["reached"] is False),
    ("C2 that patient reads 'Not called since the due date', rose",
     lambda C, D, H: row(D, "G1")["call_line"] == "" and row(D, "G1")["tone"] == "rose" and row(D, "G1")["pill"] == "Not called yet"),
    ("C3 a call BEFORE the due day does not count", lambda C, D, H: row(D, "G3")["called"] is False),
    ("C4 a call the day AFTER the due day counts: called and reached on an earlier day",
     lambda C, D, H: row(D, "G2")["called"] and row(D, "G2")["reached"] and row(D, "G2")["called_before"] and row(D, "G2")["reached_before"]),
    ("C5 the same patient called today, no answer: called today, not reached today",
     lambda C, D, H: row(D, "G2")["called_today"] is True and row(D, "G2")["reached_today"] is False),
    ("C6 a Grace patient called and answered today: called today and reached today",
     lambda C, D, H: row(D, "G4")["called_today"] and row(D, "G4")["reached_today"] and not row(D, "G4")["called_before"]),
    ("C7 the Today section counts today's calls (the due day IS today): T1 called and reached, T2 called, T3 not",
     lambda C, D, H: (row(D, "T1")["called"], row(D, "T1")["reached"], row(D, "T2")["called"], row(D, "T2")["reached"], row(D, "T3")["called"]) == (True, True, True, False, False)),
    ("C8 two unanswered calls after the due date: called on earlier days, not reached; pill Not reached x 2",
     lambda C, D, H: row(D, "O1")["called_before"] and not row(D, "O1")["reached_before"] and not row(D, "O1")["called_today"] and row(D, "O1")["pill"] == "Not reached × 2"),
    ("C9 the patient rang in after the due date and was answered: reached, but not 'called'",
     lambda C, D, H: row(D, "O4")["reached_before"] and not row(D, "O4")["called"] and row(D, "O4")["call_line"] == ""),
    ("C10 a 'not coming' filed ON the due day still closes the row (Came / closed)",
     lambda C, D, H: where(D, "O3")[0] == "came" and row(D, "O3")["closed"] == "notcoming"),
    ("C11 a WhatsApp on the due day is read as before: Wrote back, to call",
     lambda C, D, H: where(D, "W1")[0] == "grace" and row(D, "W1")["pill"] == "Wrote back · to call" and row(D, "W1")["note_h"] == "Wrote back · to call"),
    ("C12 the folded line: a patient who rang in and was answered counts as called AND reached that day -- Reached never exceeds Called; the row itself still reads 'not called'",
     lambda C, D, H: row(D, "G16")["called"] is False and row(D, "G16")["reached_today"] and row(D, "G16")["line_today"] and row(D, "O4")["line_before"]
     and all(fl(D, k)["rt"] <= fl(D, k)["ct"] and fl(D, k)["er"] <= fl(D, k)["ec"] for k in ("today", "grace", "overdue", "lapsed"))
     and "Not called since the due date" in sect(H, "grace")[sect(H, "grace").index("Test Rangtoday"):][:150]),
    # ---- the folded lines (a)
    ("L1 Today's line: 3 patients, called today 2, reached 1",
     lambda C, D, H: (fl(D, "today")["n"], fl(D, "today")["ct"], fl(D, "today")["rt"]) == (3, 2, 1)),
    ("L2 Grace: 14 not visited, called today 3 (one of them rang in and was answered), reached today 2; earlier days 1 called, 1 reached",
     lambda C, D, H: (fl(D, "grace")["n"], fl(D, "grace")["ct"], fl(D, "grace")["rt"], fl(D, "grace")["ec"], fl(D, "grace")["er"]) == (14, 3, 2, 1, 1)),
    ("L3 Overdue: 3 not visited, called today 0; earlier days 2 called (one rang in and was answered), 1 reached",
     lambda C, D, H: (fl(D, "overdue")["n"], fl(D, "overdue")["ct"], fl(D, "overdue")["rt"], fl(D, "overdue")["ec"], fl(D, "overdue")["er"]) == (3, 0, 0, 2, 1)),
    ("L4 Lapsed: 3 not visited, called today 1, reached 0; earlier days 0, 0",
     lambda C, D, H: (fl(D, "lapsed")["n"], fl(D, "lapsed")["ct"], fl(D, "lapsed")["rt"], fl(D, "lapsed")["ec"], fl(D, "lapsed")["er"]) == (3, 1, 0, 0, 0)),
    ("L5 the line's colour by today's calls: none called rose, some amber",
     lambda C, D, H: (fl(D, "today")["tone"], fl(D, "grace")["tone"], fl(D, "overdue")["tone"], fl(D, "lapsed")["tone"]) == ("amber", "amber", "rose", "amber")),
    ("L6 the old 8-part section rows still read (outgoing calls / any answered call, by the new rule): grace 14, 2 called, 3 reached",
     lambda C, D, H: band(D, "grace")[4:7] == (14, 2, 3)),
    ("L7 the page: Grace's folded line in the mock-up's words and order",
     lambda C, D, H: "Grace period · 1–3 days late 14 not visited Called today 3 of 14 Reached 2 Earlier days, after the due date: 1 called · 1 reached" in sect(H, "grace")),
    ("L8 the page: Today's line (no 'earlier days'), Overdue's line (no 'Reached' when nobody was called or reached today)",
     lambda C, D, H: "3 patients Called today 2 of 3 Reached 1" in sect(H, "today") and "Earlier days" not in sect(H, "today")
     and "3 not visited Called today 0 of 3 Earlier days, after the due date: 2 called · 1 reached" in sect(H, "overdue")),
    ("L9 the page: the two sentences of the mock-up",
     lambda C, D, H: "Only patients who have not visited are listed." in H
     and "In Grace and older, a call counts only from the day after the due date. A call made on the appointment day does not count." in H),
    ("L10 the page: big line 24 px bold in the mock-up's three colours; the small line 13 px #4A5562",
     lambda C, D, H: ".fu2 .fbig{font-size:24px;font-weight:700" in H and "#1E6B3A" in H and "#8A5A00" in H and "#B3261E" in H
     and ".fu2 .fea{font-size:13px;color:#4A5562}" in H and 'class="fbig rose">Called today 0 of 3' in H),
    # ---- only patients who have not visited (c, D893)
    ("V1 a visit AFTER the due date closes the row, as before (by the clinic ID)",
     lambda C, D, H: where(D, "G5")[0] == "came" and row(D, "G5")["closed"] == "came"),
    ("V2 D893: 7-day advice, a visit 2 days before the due date (not the prescribing one) closes the row",
     lambda C, D, H: where(D, "G6")[0] == "came" and row(D, "G6")["closed_day"] == dt.date(2026, 11, 10) and row(D, "G6")["advised"] == 7),
    ("V3 D893: the visit at which the follow-up was advised never closes it (7-day advice)",
     lambda C, D, H: where(D, "G7")[0] == "grace" and row(D, "G7")["advised"] == 7),
    ("V4 the advised period cannot be read: THE ROW STAYS, though a visit sits 2 days before the due date",
     lambda C, D, H: where(D, "G8")[0] == "grace" and row(D, "G8")["advised"] is None),
    ("V5 D893: 30-day advice, a visit 23 days early is before the half-period window: the row stays",
     lambda C, D, H: where(D, "G9")[0] == "grace" and row(D, "G9")["advised"] == 30),
    ("V6 D893: 30-day advice, a visit 13 days early closes the row (off the list; older than the 7 days of Came / closed)",
     lambda C, D, H: where(D, "G10")[0] is None),
    ("V7 D893: 3-day and 1-day advice -- the window is at least 1 day: the prescribing visit alone leaves the row; a visit 1 day early closes it",
     lambda C, D, H: where(D, "G11")[0] == "grace" and where(D, "G15")[0] == "grace" and row(D, "G15")["advised"] == 1 and where(D, "G12")[0] == "came"),
    ("V8 an EARLY visit matched only on the mobile (a family member's ID) does not close the row",
     lambda C, D, H: where(D, "G13")[0] == "grace"),
    ("V9 a visit after the due date on the same mobile closes the row, as before",
     lambda C, D, H: where(D, "G14")[0] == "came"),
    ("V10 the page knows the advised periods were read, and counts them: 12 read, 5 closed early, 6 rows off the old list in all",
     lambda C, D, H: D["fu"]["advice_ok"] is True and D["fu"]["visits_ok"] is True and D["fu"]["advised"] == 12 and D["fu"]["early"] == 5 and D["fu"]["dropped"] == 6),
    ("V11 the clinic ID is matched as one ID on both sides: the console's '5512.0' meets the visit's '5512' (a visit after the due date closes the row)",
     lambda C, D, H: where(D, "G18")[0] == "came" and row(D, "G18")["closed_day"] == dt.date(2026, 11, 12)),
    ("V12 a row due more than 60 days ago is NOT closed by a visit older than the 60 days the page has always read (though the visits are now read back to Aug for a 90-day advice)",
     lambda C, D, H: where(D, "L3")[0] == "lapsed" and where(D, "G17")[0] == "grace" and row(D, "G17")["advised"] == 90),
    ("V13 due TODAY and came early by D893: off the Today section -- one in Came / closed (2 days ago), one older than its 7 days",
     lambda C, D, H: where(D, "T4")[0] == "came" and where(D, "T5")[0] is None and fl(D, "today")["n"] == 3),
    # ---- last reached (d, D899)
    ("R1 last reached, days ago: 'Thu 12 Nov, 4:12 pm', what was said, the recording and the transcript",
     lambda C, D, H: row(D, "G2")["last_reached"]["when_h"] == "Thu 12 Nov, 4:12 pm" and row(D, "G2")["last_reached"]["jk"] == JK_G2
     and row(D, "G2")["last_reached"]["has_rec"] and "Saturday ko aayenge" in row(D, "G2")["last_reached"]["said"]),
    ("R2 the page: that line with the page's own Play button (playJk) and 'whole transcript' (wholeTx)",
     lambda C, D, H: "Last reached Thu 12 Nov, 4:12 pm — coming · “Saturday ko aayenge”" in H
     and ('onclick="playJk(\'%s\',this)">&#9654; Play 1:15</button>' % JK_G2) in H and ("wholeTx(this,'%s')" % JK_G2) in H),
    ("R3 the page: today's call line in the mock-up's words",
     lambda C, D, H: "Today 10:42 am — called, no answer (Alisha) · 2 calls since the due date" in H),
    ("R4 last reached ON the due day is shown and said to be on the due date (it does not count as a call)",
     lambda C, D, H: row(D, "G1")["last_reached"]["rel"] == "on the due date" and "Last reached Thu 12 Nov, 11:00 am, on the due date" in H),
    ("R5 last reached BEFORE the due date is shown as such (Overdue: 20 Oct)",
     lambda C, D, H: row(D, "O1")["last_reached"]["rel"] == "before the due date" and row(D, "O1")["last_reached"]["when_h"] == "Tue 20 Oct, 12:00 pm"),
    ("R6 never reached in the 60 days read (an answered call 70 days ago is outside): the row says so",
     lambda C, D, H: row(D, "L2")["last_reached"] is None and row(D, "O2")["last_reached"] is None and "No answered call in the last 60 days" in H),
    ("R7 the page: 'Not called since the due date' in red on a patient nobody called; days late; the clinic ID; the due weekday",
     lambda C, D, H: '<span class="no">Not called since the due date</span>' in H and "1 day late" in H and "2 days late" in H
     and "· ID T-202" in H and "due Wed 11 Nov" in H),
    ("R8 every Grace-and-older row keeps its Call button (the click-to-call), and the Today rows their old row",
     lambda C, D, H: H.count("callBack('%s',this)" % PH["G2"]) == 1 and H.count("callBack('%s',this)" % PH["T3"]) == 1),
    # ---- nothing else moved
    ("N1 who called today is unchanged by the rule: Shivani 3, Alisha 3",
     lambda C, D, H: dict(D["fu"]["who"]) == {"Shivani": 3, "Alisha": 3}),
    ("N2 today's line at the top keeps EVERY patient due today -- 5 due, 3 called, 2 reached (as the live page) -- and 2 came (the two early visits)",
     lambda C, D, H: D["fu"]["today"] == {"due": 5, "called": 3, "reached": 2, "came": 2} and "follow-ups called <a href=\"#followups\" class=\"w\">3 of 5</a>" in H),
    ("N3 the page renders; the player, the fold buttons and the Came / closed section are there",
     lambda C, D, H: 'id="pl"' in H and "function playJk(" in H and "function expandAll()" in H and 'id="fu-came"' in H and H.rstrip().endswith("</body></html>")),
    ("N4 open rows 23; Came / closed holds G5, G6, G12, G14, G18, T4 and the 'not coming'",
     lambda C, D, H: D["fu"]["open"] == 23 and sorted(r["name"] for r in D["fu"]["came"]) == ["Test Cameearly", "Test Camelate", "Test Dueearly", "Test Familylate", "Test Notcoming", "Test Pointzero", "Test Threecame"]),
]
CHECKS.append(("N5 with no console.db the page still opens and says the feed is not readable (nothing shown as zero)",
               lambda C, D, H: C.walk_nodb[0] == 200 and "feed not readable" in C.walk_nodb[1] and "Called today" not in C.walk_nodb[1]))
MUST_RED_ON_LIVE = ("C1 ",)          # the control: the unpatched page counts the due-day call


def run(page_file, quiet=False):
    C, D, H, cards = facts(page_file)
    res = []
    for name, fn in CHECKS:
        try:
            ok = bool(fn(C, D, H))
        except Exception as e:
            ok, name = False, name + "  [%s: %s]" % (type(e).__name__, str(e)[:60])
        res.append((name, ok))
        if not quiet:
            print(("ok   " if ok else "RED  ") + name)
    return res, (C, D, H, cards)


# what each mutation of the new page must turn red (old text -> new text, found exactly once)
MUTATIONS = [
    ("M1 '>' flipped to '>=' (the due-day call counts again)", 'if t["day"] > r["due"]] if strict else all_calls', 'if t["day"] >= r["due"]] if strict else all_calls', "C1 "),
    ("M2 the D893 visit filter dropped", "        ds += [d for d in id_days if presc < d and start <= d < dd]\n", "", "V2 "),
    ("M3 the prescribing visit allowed to close the row", "if presc < d and start <= d < dd]", "if presc <= d and start <= d < dd]", "V7 "),
    ("M4 an early visit on the mobile alone allowed", "ds += [d for d in id_days if presc < d", "ds += [d for d in list(id_days) + list(fp_days) if presc < d", "V8 "),
    ("M5 the whole advised period instead of half", "FU_EARLY_SHARE = 0.5 ", "FU_EARLY_SHARE = 1.0 ", "V5 "),
    ("M6 the Today section made strict too", 'strict=(r["age"] > 0)', "strict=True", "C7 "),
    ("M7 today's line taken from the 7-day Came / closed list again (a patient due today drops out of 'due')", "        t_came = t_closed  ", '        t_came = [x for x in out["came"] if x["dd"] == today]  ', "N2 "),
    ("M8 rule 1 given every visit day read (an old Lapsed row closes)", "if d >= dd and (lo is None or d >= lo)]", "if d >= dd]", "V12 "),
    ("M9 the folded line counting outgoing calls only (Reached can exceed Called)", 'r["line_today"] = r["called_today"] or r["reached_today"]', 'r["line_today"] = r["called_today"]', "C12 "),
    ("M10 the clinic ID matched raw on the visit side", 'ds_id = list(ids_n.get(_cid_key(r["cid"]), ())) if r["cid"] else []', 'ds_id = list(visits["by_id"].get(r["cid"], ())) if r["cid"] else []', "V11 "),
]

PAGE = os.path.join(PAGE_DIR, "calls_console.py")
RES, (C0, D0, H0, CARDS0) = run(PAGE)
if HTML_OUT:
    open(HTML_OUT, "w", encoding="utf-8").write(H0)
n_ok = sum(1 for _n, ok in RES if ok)
if CONTROL:
    need = [n for n, ok in RES if n.startswith(MUST_RED_ON_LIVE)]
    hit = bool(need) and all(not ok for n, ok in RES if n.startswith(MUST_RED_ON_LIVE))
    STORES or shutil.rmtree(TMP, ignore_errors=True)
    if hit:
        print("CONTROL: %d of %d red on this page, the due-day call case among them" % (len(RES) - n_ok, len(RES)))
        sys.exit(0)
    print("CONTROL FAILED: the due-day call case is green on this page")
    sys.exit(1)
bad = len(RES) - n_ok
# ---- every other reader: the same figures as the live page gives on the same stores
same_n = same_ok = 0
if LIVE_DIR:
    _c, D1, H1, CARDS1 = facts(os.path.join(LIVE_DIR, "calls_console.py"))

    def people_key(d):
        return [(p["phone"], p["state"], p["state_h"], p["n_calls"], p["n_wa"], p["tail"]) for p in d["people"]]

    def staff_key(d):
        return [(c["key"], c["answered"], c["rung"], c["missed"], c["made"], c.get("net_missed"), len(c["not_logged"]), len(c["mismatch"]), c["tone"])
                for c in (d.get("staff") or [])]
    SAME = [
        ("S1 the strip's figures", lambda: D0["counts"] == D1["counts"]),
        ("S2 the people and their states (the WhatsApp-awaiting rule untouched)", lambda: people_key(D0) == people_key(D1) and D0["chips"] == D1["chips"]),
        ("S3 Needs you", lambda: [(n["tone"], n["who"], n["text"]) for n in D0["needs"]] == [(n["tone"], n["who"], n["text"]) for n in D1["needs"]]),
        ("S4 the staff cards on his page", lambda: staff_key(D0) == staff_key(D1) and len(staff_key(D0)) >= 2),
        ("S5 each person's own card as the staff app reads it (Mere calls): identical", lambda: CARDS0 == CARDS1 and CARDS0.get("alisha") is not None),
        ("S6 Call ke baad, this week's unknown callers, earlier days", lambda: D0["ckb"] == D1["ckb"] and D0["week"] == D1["week"] and D0["earlier"] == D1["earlier"]),
        ("S7 who called today and today's line at the top: due / called / reached exactly the live page's (5, 3, 2); only 'came' may rise (0 -> 2)",
         lambda: D0["fu"]["who"] == D1["fu"]["who"] and all(D0["fu"]["today"][k] == D1["fu"]["today"][k] for k in ("due", "called", "reached"))
         and D1["fu"]["today"]["due"] == 5 and D0["fu"]["today"]["came"] >= D1["fu"]["today"]["came"]),
        ("S9 the list: the rows that left it are exactly the ones this kit closes (live open - new open = dropped = 6); the 73-day Lapsed row open on both",
         lambda: D1["fu"]["open"] - D0["fu"]["open"] == D0["fu"]["dropped"] == 6 and where(D1, "L3")[0] == "lapsed" and where(D0, "L3")[0] == "lapsed"),
        ("S8 the page outside the follow-up section -- the strip with 'follow-ups called 3 of 5' included -- is byte-identical",
         lambda: H0[H0.index('<section id="staff">'):H0.index('<div class="foot">')] == H1[H1.index('<section id="staff">'):H1.index('<div class="foot">')]
         and H0[H0.index("<body>"):H0.index('<section id="followups">')] == H1[H1.index("<body>"):H1.index('<section id="followups">')]),
    ]
    for name, fn in SAME:
        same_n += 1
        try:
            ok = bool(fn())
        except Exception as e:
            ok, name = False, name + "  [%s: %s]" % (type(e).__name__, str(e)[:60])
        same_ok += ok
        print(("ok   " if ok else "RED  ") + name)
# ---- the mutations: each must turn its check red
mut_red = 0
src = open(PAGE, encoding="utf-8").read()
MD = tempfile.mkdtemp(prefix="s817mut_")
if bad == 0:
    for i, (name, old, new, must) in enumerate(MUTATIONS):
        if src.count(old) != 1:
            print("RED  %s  [the text to mutate was found %d times]" % (name, src.count(old)))
            continue
        f = os.path.join(MD, "m%d_calls_console.py" % i)
        open(f, "w", encoding="utf-8").write(src.replace(old, new))
        res, _x = run(f, quiet=True)
        reds = [n for n, ok in res if not ok]
        went = any(n.startswith(must) for n in reds)
        mut_red += went
        print(("ok   " if went else "RED  ") + "%s -> %d check(s) red%s" % (name, len(reds), "" if went else " -- but NOT " + must))
STORES or shutil.rmtree(TMP, ignore_errors=True)
shutil.rmtree(MD, ignore_errors=True)
if bad == 0 and mut_red == len(MUTATIONS) and same_ok == same_n:
    print("WALK OK: %d of %d; %d of %d mutations red; other readers %s" % (n_ok, len(RES), mut_red, len(MUTATIONS),
                                                                         ("%d of %d the same as the live page" % (same_ok, same_n)) if LIVE_DIR else "not compared (no live page given)"))
    sys.exit(0)
print("WALK RED: %d of %d; mutations red %d of %d; other readers %d of %d" % (n_ok, len(RES), mut_red, len(MUTATIONS), same_ok, same_n))
sys.exit(1)
