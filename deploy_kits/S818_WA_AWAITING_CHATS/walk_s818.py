#!/usr/bin/env python3
"""walk_s818.py -- S818_WA_AWAITING_CHATS's walk, on MADE-UP data only (no real patient, number or name anywhere).
usage: walk_s818.py <dir with calls_console.py> <portal dir: ring_outcome.py, ring_common.py, and portal_inbox.py (read as
                    TEXT for the Inbox's msgs table)> <portal_console.py> <finance dir (dx_feed.py, finance_patient_sync.py
                    -- read as TEXT for the two table shapes)> [<dir with the BASE calls_console.py (S817's)>]
                    [--control] [--html OUT.html] [--stores DIR]
(--html keeps the rendered page; --stores builds the made-up stores in DIR and leaves them -- both for the bench only)
Builds a made-up console.db (the builder's own SCHEMA + build_fu_all), inbox.db (the msgs table as portal_inbox.py creates
it), finance.db, a ring store and the owner's marks (written by the page's own wz_write); reads the page's data, renders
the page and knocks on the door.
  normal     every check green on the page given; then the MUTATIONS of that page (the rule flipped, the look-back cut,
             the gate taken off the door ...) each go red; with the base page's folder given, every OTHER reader's figures
             (calls, people, follow-up sections, strip call counts, staff-card call figures, Call ke baad) are compared and
             must be equal, and the awaiting figures must differ exactly as the kit says.
  --control  run on the BASE (S817) page: the reported case -- a chat answered, then "ok" -- MUST go red.
Prints one line per check; the last line is 'WALK OK: ...' / 'WALK RED: ...' / 'CONTROL: ...'."""
import datetime as dt
import html as _html
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from functools import wraps

A = [x for x in sys.argv[1:] if not x.startswith("--")]
CONTROL = "--control" in sys.argv


def opt(name):
    global A
    if name not in sys.argv:
        return ""
    v = sys.argv[sys.argv.index(name) + 1]
    A = [x for x in A if x != v]
    return v


HTML_OUT, STORES = opt("--html"), opt("--stores")
if STORES:
    os.makedirs(STORES)
PAGE_DIR, PORTAL_DIR, BUILDER, FIN_DIR = A[0], A[1], A[2], A[3]
BASE_DIR = A[4] if len(A) > 4 else ""
TMP = STORES or tempfile.mkdtemp(prefix="s818walk_")
os.environ["RING_OUTCOME_DB"] = os.path.join(TMP, "ring.db")
os.environ["FINANCE_DB"] = os.path.join(TMP, "finance.db")
sys.path.insert(0, PORTAL_DIR)
NOW = dt.datetime(2026, 11, 13, 12, 0, 0)          # a Friday, noon
TODAY = NOW.date()
D0, D1, D2 = "2026-11-13", "2026-11-12", "2026-11-11"     # today, yesterday, two days ago


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


def msgs_ddl(path):
    """the Inbox's msgs table exactly as portal_inbox.py creates it -- read as text, the module is never run"""
    m = re.search(r"CREATE TABLE IF NOT EXISTS msgs\((.*?)\);", open(path, encoding="utf-8").read(), re.S)
    if not m:
        raise SystemExit("WALK RED: %s does not create the msgs table" % path)
    return "CREATE TABLE msgs(%s)" % " ".join(m.group(1).split())


B = load("pc_made", BUILDER)


def jk(ph, t):
    return "%s_%d" % (ph, int(dt.datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone(dt.timedelta(hours=5, minutes=30))).timestamp()))


# ---------------------------------------------------------------- the made-up clinic
# (key, name or '' for a number the clinic does not know, clinic id)
CAST = [
    ("OK", "Test Okafter", "T-501"),          # THE FAULT: asked, answered (delivered), then wrote "ok"
    ("QUE", "Test Question", "T-502"),        # answered, then a real question
    ("SENT", "Test Sent", "T-503"),           # the reply's status is 'sent' (the delivery ping never came)
    ("DELV", "Test Delivered", "T-504"),      # the reply's status is 'delivered'
    ("FAIL", "Test Failed", "T-505"),         # the reply failed
    ("MID", "Test Midnight", "T-506"),        # wrote last night 22:30, answered this morning 08:10
    ("OLD", "Test Twodays", "T-507"),         # wrote two days ago, never answered
    ("CALL", "Test Called", "T-508"),         # answered by a call of 60 s, 40 minutes later
    ("SHORT", "Test Shortcall", "T-509"),     # a call of 40 s with 15 s spoken: does not answer
    ("LATE", "Test Latecall", "T-510"),       # a call 3 clinic hours later: does not answer
    ("LAST", "Test Lastword", "T-511"),       # wrote 08:10 and 11:20; a call at 11:40 -- within 2 h of the LAST word
    ("THREE", "Test Three", "T-512"),         # three messages (one a photo), no reply: ONE chat
    ("DONE", "Test Done", "T-513"),           # the owner's Done, then silence
    ("DNEW", "Test Donenew", "T-514"),        # Done last evening, a new real message this morning
    ("DTHX", "Test Donethanks", "T-515"),     # Done, then "thanks" with an emoji
    ("DUNS", "Test Doneunseen", "T-516"),     # Done reached the 08:20 message; one of 08:26 he had not seen
    ("NP", "", ""),                           # an unknown number: WhatsApps, an answered call, a missed call -- marked Not a patient
    ("TPL", "Test Template", "T-518"),        # only a template went back
    ("EMO", "Test Emoji", "T-519"),           # answered, then two folded-hands emoji
    ("HIN", "Test Hindi", "T-520"),           # answered, then thanks in Hindi with "doctor sahab"
    ("LTHX", "Test Latethanks", "T-521"),     # answered two days ago; "thank you" today (later than 24 hours)
    ("ACK1", "Test Ackfirst", "T-522"),       # a bare "hello" with nothing before it
    ("RETRY", "Test Retry", "T-523"),         # the reply is still 'retrying'
    ("YES", "Test Yes", "T-524"),             # answered, then "haan" (an answer, not an acknowledgement)
    ("XSS", "Test Script", "T-525"),          # the message is a script tag
    ("FRESH", "Test Fresh", "T-526"),         # wrote 30 minutes ago
    ("TOK", "Test Tplok", "T-527"),           # a template went out; the patient wrote "ok"
    ("TQ", "Test Tplquestion", "T-528"),      # a template went out; the patient asked a real question
    ("QTT", "Test Tplthanks", "T-529"),       # a real question, then only a template, then "thanks": never answered
    ("TLATE", "Test Tpllate", "T-530"),       # a template 30 hours ago; "ok" today
    ("QM1", "Test Okquestion", "T-534"),      # answered, then "ok?" -- a question mark makes it a question
    ("QM2", "Test Helloquestion", "T-535"),   # a template went out, then "Hello?"
    ("AUTO", "Test Autogreeting", "T-536"),   # an automatic greeting 20 s after the message: plain text, 'sent', NO sender recorded
    ("HSM", "Test Hsm", "T-537"),             # the only thing that went back is an 'hsm' row (a structured / automatic type)
    ("TPLTXT", "Test Templatetext", "T-538"), # a template echoed back as plain text: its text begins "Template:"
    ("PANEL", "Test Panelreply", "T-539"),    # a reply typed in the panel: plain text, no sender recorded, 5 minutes later
    ("MC", "Test Missedtext", "T-540"),       # a MISSED CALL, then a free-text WhatsApp at 'sent' (no WhatsApp from the patient)
    ("FU1", "Test Fuwrote", "T-531"),         # follow-up due yesterday; wrote yesterday, no reply
    ("FU2", "Test Fureplied", "T-532"),       # follow-up due yesterday; wrote yesterday, the reply's status 'sent'
    ("FU3", "Test Futoday", "T-533"),         # follow-up due today, called and reached
    ("Q1", "Test Callin", "T-541"),           # calls only: an incoming call answered and logged
    ("Q2", "Test Missed", "T-542"),           # calls only: a missed call nobody called back
    ("Q3", "Test Missedback", "T-543"),       # calls only: missed, then called back
    ("Q4", "Test Notlogged", "T-544"),        # calls only: answered, nothing filed
]
PH = {k: N(i + 1) for i, (k, _n, _c) in enumerate(CAST)}
NAME = {k: n for k, n, _c in CAST}
KEY_OF = {v: k for k, v in PH.items()}

con = sqlite3.connect(os.path.join(TMP, "console.db"))
con.executescript(B.SCHEMA)
con.execute("CREATE TABLE call_agent (join_key TEXT PRIMARY KEY, agent TEXT, department TEXT, matched_how TEXT)")
for k, n, cid in CAST:
    if n:
        con.execute("INSERT INTO patients VALUES (?,?,?,?,?,?,?,?)", (PH[k], n, "made-up knee", "50", "F", "", "", cid))


def call(k, t, direction, answered, dur, agent="", claimed="", ai="", talk=None):
    key = jk(PH[k], t)
    end = (dt.datetime.strptime(t, "%Y-%m-%d %H:%M") + dt.timedelta(seconds=dur)).strftime("%Y-%m-%dT%H:%M:%S+05:30")
    spoken = (dur if answered else 0) if talk is None else talk
    con.execute("INSERT INTO calls (direction, answered, total_duration, customer_talk_duration, customer_ring_duration, "
                "recording_filename, ended_at_ist, phone10, join_key, client_ref_id, status) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (direction, 1 if answered else 0, str(dur), str(spoken), str(max(0, dur - spoken) if answered else 12),
                 "r.mp3" if answered else "", end, PH[k], key, "", ""))
    if agent:
        con.execute("INSERT OR REPLACE INTO call_agent VALUES (?,?,?,?)", (key, agent, "", "test"))
    if claimed or ai:
        con.execute("INSERT INTO verdicts (join_key, agent, claimed_outcome, ai_outcome, verdict, evidence) VALUES (?,?,?,?,?,?)",
                    (key, agent, claimed, ai, "Match", ""))
    return key


SHIV, ALI = "Shivani Srivastava", "Alisha"
call("CALL", D0 + " 09:40", "Out", True, 60, SHIV, "coming", "coming")
call("SHORT", D0 + " 09:30", "Out", True, 40, SHIV, "call_again", "call_again", talk=15)
call("LATE", D0 + " 11:05", "Out", True, 60, SHIV, "coming", "coming")
call("LAST", D0 + " 11:40", "Out", True, 60, SHIV, "coming", "coming")
call("NP", D0 + " 08:50", "In", True, 50, SHIV)                               # the unknown number: a call answered (nothing filed) ...
call("NP", D0 + " 09:20", "In", False, 0)                                     # ... and a missed call nobody called back
call("FU3", D0 + " 10:40", "Out", True, 50, SHIV, "coming", "coming")
call("MC", D0 + " 09:35", "In", False, 0)
call("Q1", D0 + " 10:00", "In", True, 60, SHIV, "coming", "coming")
call("Q2", D0 + " 10:15", "In", False, 0)
call("Q3", D0 + " 10:30", "In", False, 0)
call("Q3", D0 + " 10:50", "Out", True, 45, SHIV, "coming", "coming")
call("Q4", D0 + " 11:00", "In", True, 70, SHIV)
call("Q1", D1 + " 15:00", "In", True, 60, ALI, "coming", "coming")            # yesterday: Alisha has a card
FU_H = ["Key", "Section", "PR", "Patient Name", "Mobile", "Diagnosis", "Due Date", "OD", "Status"]
FU_R = [[k, s, "", NAME[k], PH[k], "made-up knee", dt.date.fromisoformat(d).strftime("%d-%b-%Y"), str((TODAY - dt.date.fromisoformat(d)).days), s]
        for k, d, s in (("FU1", D1, "Grace Period"), ("FU2", D1, "Grace Period"), ("FU3", D0, "Due Today"))]
meta = B.build_fu_all(con, FU_H, FU_R)
con.execute("INSERT INTO meta VALUES ('fu_all', ?)", (json.dumps(meta),))
con.execute("INSERT INTO meta VALUES ('built_at', '2026-11-13T11:50:00+05:30')")
con.commit()
con.close()

# (key, in/out, day, time, type, text, status, sent by)
XSS_TEXT = "<script>alert(1)</script>"
MSGS = [
    ("OK", "in", D0, "09:00", "text", "kal aa sakte hain kya", "received", ""),
    ("OK", "out", D0, "09:20", "text", "ji, kal 11 baje aaiye", "delivered", "manoj"),
    ("OK", "in", D0, "09:25", "text", "ok", "received", ""),
    ("QUE", "in", D0, "09:00", "text", "report dekh lijiye", "received", ""),
    ("QUE", "out", D0, "09:10", "text", "report theek hai", "delivered", "shivani"),
    ("QUE", "in", D0, "09:30", "text", "aur dawai kab tak leni hai", "received", ""),
    ("SENT", "in", D0, "09:05", "text", "fees kitni hai", "received", ""),
    ("SENT", "out", D0, "09:15", "text", "fees counter par bata denge", "sent", "shivani"),
    ("DELV", "in", D0, "09:06", "text", "clinic kab khulta hai", "received", ""),
    ("DELV", "out", D0, "09:16", "text", "subah 10 baje", "delivered", "shivani"),
    ("FAIL", "in", D0, "09:10", "text", "plaster kab katega", "received", ""),
    ("FAIL", "out", D0, "09:12", "text", "do hafte baad", "failed", "shivani"),
    ("MID", "in", D1, "22:30", "text", "kal subah aa jaun", "received", ""),
    ("MID", "out", D0, "08:10", "text", "ji aa jaiye", "sent", "manoj"),
    ("OLD", "in", D2, "10:00", "text", "x-ray report bhejni hai", "received", ""),
    ("CALL", "in", D0, "09:00", "text", "call kijiye", "received", ""),
    ("SHORT", "in", D0, "09:00", "text", "phone kijiye please", "received", ""),
    ("LATE", "in", D0, "08:05", "text", "subah se dard hai", "received", ""),
    ("LAST", "in", D0, "08:10", "text", "report ke baare mein", "received", ""),
    ("LAST", "in", D0, "11:20", "text", "please call kijiye", "received", ""),
    ("THREE", "in", D0, "09:00", "text", "doctor sahab", "received", ""),
    ("THREE", "in", D0, "09:01", "image", "", "received", ""),
    ("THREE", "in", D0, "09:02", "text", "yeh sujan theek hai kya", "received", ""),
    ("DONE", "in", D0, "08:30", "text", "theek hai, report kal dikhaunga", "received", ""),
    ("DNEW", "in", D1, "18:00", "text", "kal aaunga", "received", ""),
    ("DNEW", "in", D0, "09:30", "text", "dard badh gaya hai", "received", ""),
    ("DTHX", "in", D0, "08:40", "text", "dawai le li hai", "received", ""),
    ("DTHX", "in", D0, "09:50", "text", "Thanks \U0001f64f", "received", ""),
    ("DUNS", "in", D0, "08:20", "text", "parso aaunga", "received", ""),
    ("DUNS", "in", D0, "08:26", "text", "ya kal aa jaun", "received", ""),
    ("NP", "in", D0, "09:13", "image", "", "received", ""),
    ("NP", "in", D0, "09:14", "image", "", "received", ""),
    ("NP", "in", D0, "09:15", "text", "New implant set rates", "received", ""),
    ("TPL", "in", D0, "09:00", "text", "kab aana hai", "received", ""),
    ("TPL", "out", D0, "09:05", "template", "Template: hours", "delivered", "shivani"),
    ("EMO", "in", D0, "09:00", "text", "exercise kab se karni hai", "received", ""),
    ("EMO", "out", D0, "09:10", "text", "kal se shuru kijiye", "delivered", "shivani"),
    ("EMO", "in", D0, "09:12", "text", "\U0001f64f\U0001f64f", "received", ""),
    ("HIN", "in", D0, "09:00", "text", "patti kab badalni hai", "received", ""),
    ("HIN", "out", D0, "09:10", "text", "teen din baad", "delivered", "shivani"),
    ("HIN", "in", D0, "09:14", "text", "धन्यवाद डॉक्टर साहब", "received", ""),
    ("LTHX", "in", D2, "10:00", "text", "report mil gayi kya", "received", ""),
    ("LTHX", "out", D2, "10:10", "text", "ji mil gayi", "delivered", "shivani"),
    ("LTHX", "in", D0, "09:00", "text", "thank you", "received", ""),
    ("ACK1", "in", D0, "09:00", "text", "hello", "received", ""),
    ("RETRY", "in", D0, "09:00", "text", "appointment chahiye", "received", ""),
    ("RETRY", "out", D0, "09:05", "text", "kal 12 baje", "retrying", "shivani"),
    ("YES", "in", D0, "09:00", "text", "sujan hai", "received", ""),
    ("YES", "out", D0, "09:10", "text", "kya bukhar bhi hai", "delivered", "manoj"),
    ("YES", "in", D0, "09:12", "text", "haan", "received", ""),
    ("XSS", "in", D0, "09:00", "text", XSS_TEXT, "received", ""),
    ("FRESH", "in", D0, "11:30", "text", "abhi aa sakta hoon kya", "received", ""),
    ("TOK", "out", D0, "08:30", "template", "Template: visit", "sent", "portal"),
    ("TOK", "in", D0, "09:00", "text", "ok", "received", ""),
    ("TQ", "out", D0, "08:30", "template", "Template: visit", "sent", "portal"),
    ("TQ", "in", D0, "09:00", "text", "kitne baje aana hai", "received", ""),
    ("QTT", "in", D0, "08:45", "text", "dawai khatam ho gayi", "received", ""),
    ("QTT", "out", D0, "08:50", "template", "Template: visit", "sent", "portal"),
    ("QTT", "in", D0, "09:00", "text", "thanks", "received", ""),
    ("TLATE", "out", D1, "03:00", "template", "Template: visit", "sent", "portal"),
    ("TLATE", "in", D0, "09:00", "text", "ok", "received", ""),
    ("QM1", "in", D0, "09:00", "text", "kal subah ya shaam", "received", ""),
    ("QM1", "out", D0, "09:10", "text", "shaam ko aaiye", "delivered", "shivani"),
    ("QM1", "in", D0, "09:20", "text", "ok?", "received", ""),
    ("QM2", "out", D0, "08:30", "template", "Template: visit", "sent", "portal"),
    ("QM2", "in", D0, "09:00", "text", "Hello?", "received", ""),
    ("AUTO", "in", D0, "09:00:00", "text", "appointment lena hai", "received", ""),
    ("AUTO", "out", D0, "09:00:20", "text", "Thank you for contacting the clinic", "sent", ""),
    ("HSM", "in", D0, "09:00", "text", "mera number kab aayega", "received", ""),
    ("HSM", "out", D0, "09:10", "hsm", "Aapka appointment darj hai", "sent", "shivani"),
    ("TPLTXT", "in", D0, "09:00", "text", "kya dawai badalni hai", "received", ""),
    ("TPLTXT", "out", D0, "09:10", "text", "Template: hours", "sent", ""),
    ("PANEL", "in", D0, "09:00", "text", "parchi kho gayi hai", "received", ""),
    ("PANEL", "out", D0, "09:05", "text", "nayi parchi bana denge", "sent", ""),
    ("MC", "out", D0, "09:45", "text", "aapka call aaya tha", "sent", "shivani"),
    ("NP", "in", D0, "11:10", "text", "rates bhej diye hain", "received", ""),
    ("FU1", "in", D1, "16:00", "text", "aaj nahi aa paunga", "received", ""),
    ("FU2", "in", D1, "16:05", "text", "kal aaunga", "received", ""),
    ("FU2", "out", D1, "16:20", "text", "ji theek hai", "sent", "alisha"),
]
BODIES = sorted({m[5] for m in MSGS if m[1] == "in" and len(m[5]) > 5})
ib = sqlite3.connect(os.path.join(TMP, "inbox.db"))
ib.execute(msgs_ddl(os.path.join(PORTAL_DIR, "portal_inbox.py")))
for i, (k, d, day, hm, mt, body, st, by) in enumerate(MSGS):
    ib.execute("INSERT INTO msgs (mid, phone, dir, ts, mtype, body, status, sent_by, src) VALUES (?,?,?,?,?,?,?,?,?)",
               ("wamid.T%03d" % i, PH[k], d, "%sT%s+05:30" % (day, hm if len(hm) == 8 else hm + ":00"), mt, body, st, by,
                "log" if (d == "in" or not by) else "inbox"))
ib.commit()
ib.close()

fd = sqlite3.connect(os.environ["FINANCE_DB"])
fd.executescript(ddl_of(os.path.join(FIN_DIR, "finance_patient_sync.py"), "VISIT_DDL"))
fd.executescript(ddl_of(os.path.join(FIN_DIR, "dx_feed.py"), "DDL"))
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
    fh.write("1,Shivani Srivastava,reception,777777,4,08:00,14:00,,,Y\n2,Alisha,reception,777777,4,14:00,20:00,,,Y\n")
PU = os.path.join(TMP, "punches.csv")
with open(PU, "w", encoding="utf-8") as fh:
    fh.write("user_id,datetime\n")
    for day in (D2, D1, D0):
        fh.write("1,%s 08:00:00\n2,%s 14:00:00\n" % (day, day))
MARKS = os.path.join(TMP, "wa_awaiting.db")           # the owner's marks, written by the page's own wz_write
NOSTORE = os.path.join(TMP, "not_there", "wa_awaiting.db")
CFG = {"PORTAL_INBOX_DB": os.path.join(TMP, "inbox.db"), "FINANCE_DB_PATH": os.environ["FINANCE_DB"],
       "SR_STAFF_MASTER": SM, "SR_PUNCH_CSV": PU, "PORTAL_CALL_REVIEW_DB": os.path.join(TMP, "call_review.db"),
       "PORTAL_WA_AWAITING_DB": MARKS}
# (key, act, the message it reached, when he pressed)
THE_MARKS = [("DONE", "done", D0 + " 08:30:00", D0 + " 08:45:00"), ("DNEW", "done", D1 + " 18:00:00", D1 + " 18:30:00"),
             ("DTHX", "done", D0 + " 08:40:00", D0 + " 08:50:00"), ("DUNS", "done", D0 + " 08:20:00", D0 + " 08:30:00"),
             ("NP", "not_patient", "", D0 + " 10:00:00")]


def ts(s):
    return dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def console_conn():
    c = sqlite3.connect("file:%s?mode=ro" % os.path.join(TMP, "console.db"), uri=True)
    c.row_factory = sqlite3.Row
    return c


def gate(view):
    """the portal's doctor_required, in shape: no login -> the login page; any other role -> 403 (the role is a made-up header)"""
    @wraps(view)
    def w(*a, **k):
        from flask import abort, redirect, request
        role = request.headers.get("X-Walk-Role", "")
        if not role:
            return redirect("/portal/login")
        if role != "doctor":
            abort(403)
        return view(*a, **k)
    return w


def rows_of(path):
    if not os.path.exists(path):
        return []
    c = sqlite3.connect(path)
    try:
        return c.execute("SELECT id, phone, act, upto, by_whom, at FROM mark ORDER BY id").fetchall()
    except sqlite3.Error:
        return []
    finally:
        c.close()


def clone(rows, path, wal):
    """a store holding `rows`, made by hand (WAL or not)"""
    c = sqlite3.connect(path)
    if wal:
        c.execute("PRAGMA journal_mode=WAL")
    c.execute("CREATE TABLE mark (id INTEGER PRIMARY KEY, phone TEXT NOT NULL, act TEXT NOT NULL, upto TEXT NOT NULL DEFAULT '', "
              "by_whom TEXT NOT NULL, at TEXT NOT NULL)")
    c.executemany("INSERT INTO mark (id, phone, act, upto, by_whom, at) VALUES (?,?,?,?,?,?)", rows)
    c.commit()
    c.close()


_SEQ = [0]


def facts(page_file, light=False):
    """everything the checks read of one calls_console.py on the made-up stores (light: the base page -- no marks, no door)"""
    from flask import Flask
    _SEQ[0] += 1
    n = _SEQ[0]
    C = load("cc_%d" % n, page_file)
    C.now_ist = lambda now=None: now if now is not None else NOW          # the walk's clock: Friday 13-Nov, noon
    for k, v in (("WZ_READ_WAIT_S", 0.2), ("WZ_WRITE_WAIT_S", 0.3)):
        if hasattr(C, k):
            setattr(C, k, v)
    app = Flask("walk%d" % n)
    if hasattr(C, "rv_init"):
        C.rv_init(CFG["PORTAL_CALL_REVIEW_DB"])
    C.register(app, gate, lambda: "manoj", lambda k, d=None: CFG.get(k, d),
               {"console_conn": console_conn, "console_meta": lambda: {"ok": True, "built_at": "2026-11-13T11:50:00+05:30"},
                "spam_phones": lambda: [], "reviews_maps": lambda: ({}, {})})
    F = {"C": C, "app": app, "err": []}
    if hasattr(C, "wz_write") and not os.path.exists(MARKS) and not light:
        for k, act, upto, at in THE_MARKS:
            C.wz_write(MARKS, PH[k], act, upto, "manoj", now=ts(at))

    def view(store, span="today", html=True, inbox=None):
        CFG["PORTAL_WA_AWAITING_DB"] = store
        conn = console_conn()
        D, H = {}, ""
        try:
            D = C.page_data(conn, span=span, now=NOW, inbox_path=inbox or CFG["PORTAL_INBOX_DB"], fin_db=CFG["FINANCE_DB_PATH"], master_path=SM, punch_path=PU)
            if html:
                with app.test_request_context("/portal/console"):
                    H = C.render(conn, {} if span == "today" else {"span": span}, now=NOW)
        except Exception as e:
            F["err"].append("%s: %s %s" % (store[-14:], type(e).__name__, str(e)[:100]))
        finally:
            conn.close()
            CFG["PORTAL_WA_AWAITING_DB"] = MARKS
        return D, H

    def mycard(key, span, store=MARKS):
        CFG["PORTAL_WA_AWAITING_DB"] = store
        conn = console_conn()
        try:
            c, _h, _m, _made = C._card_for(conn, key, span, NOW)
            return C.card_json(c) if c else None
        except Exception as e:
            return {"error": "%s %s" % (type(e).__name__, str(e)[:80])}
        finally:
            conn.close()
            CFG["PORTAL_WA_AWAITING_DB"] = MARKS

    F["view"], F["mycard"] = view, mycard
    F["T"] = view(MARKS)                                     # today, the owner's marks standing
    F["Y"] = view(MARKS, span="yesterday", html=False)       # yesterday's page
    F["E"] = view(NOSTORE, html=not light)                   # today, no store at all (no marks)
    F["W"] = view(MARKS, span="7", html=False)               # the 7-day page
    keep = CFG["PORTAL_INBOX_DB"]
    CFG["PORTAL_INBOX_DB"] = os.path.join(TMP, "not_there", "inbox.db")
    F["noinbox"] = view(MARKS, inbox=CFG["PORTAL_INBOX_DB"])  # the Inbox store cannot be read
    CFG["PORTAL_INBOX_DB"] = keep
    if hasattr(C, "_aw_text"):                                # the block's maker made to fail: the page must SAY so
        keep_fn = C._aw_text

        def boom(_msgs):
            raise RuntimeError("made to fail by the walk")
        C._aw_text = boom
        F["broken"] = view(MARKS)
        C._aw_text = keep_fn
    F["mine"] = {"shivani": mycard("shivani", "today"), "alisha_y": mycard("alisha", "yesterday")}
    F["mine_e"] = {"shivani": mycard("shivani", "today", NOSTORE), "alisha_y": mycard("alisha", "yesterday", NOSTORE)}
    if light:
        return F
    V = os.path.join(TMP, "v%d" % n)
    os.makedirs(V)
    good = rows_of(MARKS)
    # -- the store empty, corrupt, locked whole, locked for writing, and with the Not-a-patient mark undone
    open(os.path.join(V, "empty.db"), "w").close()
    F["empty"] = view(os.path.join(V, "empty.db"))
    with open(os.path.join(V, "corrupt.db"), "wb") as fh:
        fh.write(b"this is not a database " * 64)
    F["corrupt"] = view(os.path.join(V, "corrupt.db"))
    clone(good, os.path.join(V, "locked.db"), wal=False)
    lk = sqlite3.connect(os.path.join(V, "locked.db"), isolation_level=None)
    lk.execute("BEGIN EXCLUSIVE")
    F["locked"] = view(os.path.join(V, "locked.db"))
    lk.execute("ROLLBACK")
    lk.close()
    clone(good, os.path.join(V, "wlocked.db"), wal=True)
    wl = sqlite3.connect(os.path.join(V, "wlocked.db"), isolation_level=None)
    wl.execute("BEGIN IMMEDIATE")
    F["wlocked"] = view(os.path.join(V, "wlocked.db"))
    cl = app.test_client()
    DOC = {"X-Walk-Role": "doctor", "X-Call-Console": "1"}

    def post(body, headers, store):
        CFG["PORTAL_WA_AWAITING_DB"] = store
        try:
            r = cl.post("/portal/console/api/wa-mark", json=body, headers=headers)
            return r.status_code, (r.get_json(silent=True) or {}), r.headers.get("Location", "")
        except Exception as e:
            return 0, {"error": type(e).__name__}, ""
        finally:
            CFG["PORTAL_WA_AWAITING_DB"] = MARKS
    F["post_wlocked"] = post({"phone": PH["QUE"], "act": "done", "upto": D0 + " 09:30:00"}, DOC, os.path.join(V, "wlocked.db"))
    wl.execute("ROLLBACK")
    wl.close()
    F["rows_wlocked"] = rows_of(os.path.join(V, "wlocked.db"))
    before = open(os.path.join(V, "corrupt.db"), "rb").read()
    F["post_corrupt"] = post({"phone": PH["QUE"], "act": "done", "upto": D0 + " 09:30:00"}, DOC, os.path.join(V, "corrupt.db"))
    F["corrupt_kept"] = open(os.path.join(V, "corrupt.db"), "rb").read() == before
    undone = os.path.join(V, "undone.db")
    clone(good, undone, wal=True)
    if hasattr(C, "wz_write"):
        C.wz_write(undone, PH["NP"], "undo_not_patient", "", "manoj", now=ts(D0 + " 11:00:00"))
    F["undone"] = view(undone)
    F["rows_undone"], F["rows_good"] = rows_of(undone), good
    # -- the door (its own store, made by the door itself)
    door = os.path.join(V, "door", "wa_awaiting.db")
    os.makedirs(os.path.dirname(door))
    Q = {"phone": PH["QUE"], "act": "done", "upto": D0 + " 09:30:00"}
    R = {}
    try:
        CFG["PORTAL_WA_AWAITING_DB"] = door
        g = cl.get("/portal/console/api/wa-mark", headers=DOC)
        R["get"] = g.status_code
        CFG["PORTAL_WA_AWAITING_DB"] = MARKS
    except Exception as e:
        R["get"] = type(e).__name__
    R["nologin"] = post(Q, {"X-Call-Console": "1"}, door)
    R["staff"] = post(Q, {"X-Walk-Role": "staff", "X-Call-Console": "1"}, door)
    R["nohdr"] = post(Q, {"X-Walk-Role": "doctor"}, door)
    R["closed_rows"] = len(rows_of(door))
    R["bad"] = [post(b, DOC, door)[0] for b in ({"phone": "12345", "act": "done", "upto": Q["upto"]},
                                               {"phone": PH["QUE"], "act": "erase", "upto": Q["upto"]},
                                               {"phone": PH["QUE"], "act": "done", "upto": ""},
                                               {"phone": PH["QUE"], "act": "done", "upto": "yesterday"})]
    R["unknown"] = [post(b, DOC, door)[0] for b in ({"phone": N(900), "act": "not_patient"},
                                                   {"phone": N(900), "act": "done", "upto": Q["upto"]},
                                                   {"phone": PH["QUE"], "act": "done", "upto": D0 + " 09:31:00"})]
    R["unknown_rows"] = len(rows_of(door))
    R["done"] = post(Q, DOC, door)
    R["rows1"] = rows_of(door)
    R["after_done"] = view(door, html=False)[0]
    R["again"] = post(Q, DOC, door)
    R["rows2"] = rows_of(door)
    R["undo"] = post(dict(Q, act="undo_done"), DOC, door)
    R["rows3"] = rows_of(door)
    R["after_undo"] = view(door, html=False)[0]
    R["undo2"] = post(dict(Q, act="undo_done"), DOC, door)
    R["np"] = post({"phone": PH["QUE"], "act": "not_patient"}, DOC, door)
    R["np_undo"] = post({"phone": PH["QUE"], "act": "undo_not_patient"}, DOC, door)
    R["rows5"] = rows_of(door)
    try:
        c = sqlite3.connect(door)
        R["wal"] = c.execute("PRAGMA journal_mode").fetchone()[0]
        c.close()
    except Exception:
        R["wal"] = ""
    F["door"] = R
    try:
        F["route"] = cl.get("/portal/console", headers=DOC).status_code, cl.get("/portal/console").status_code
    except Exception as e:
        F["route"] = (type(e).__name__, 0)
    return F


# ---------------------------------------------------------------- reading the facts
def person(D, k):
    return next((p for p in D.get("people", []) if p["phone"] == PH[k]), None) or {}


def st(D, k):
    p = person(D, k)
    return (p.get("state"), p.get("state_h", ""))


def aw(D):
    return D.get("wa_aw") or {}


def chat(D, k):
    return next((c for c in aw(D).get("chats", []) if c["phone"] == PH[k]), None)


def waiting(D):
    return sorted(KEY_OF[c["phone"]] for c in aw(D).get("chats", []))


def listed(D, name):
    return sorted(KEY_OF[c["phone"]] for c in aw(D).get(name, []))


def card(D, key):
    return next((c for c in (D.get("staff") or []) if c["key"] == key), None) or {}


def wa_fig(c):
    return (c.get("wa_in"), c.get("wa_ans"), len(c.get("wa_open", [])))


def open_keys(c):
    return sorted(KEY_OF[p["phone"]] for p, _w in c.get("wa_open", []))


def fu_row(D, k):
    fu = D.get("fu") or {}
    for b in fu.get("bands", []):
        for r in b[3]:
            if r["phone"] == PH[k]:
                return r
    return {}


def sect(H, sid):
    i = H.index('<section id="%s">' % sid)
    return H[i:H.index("</section>", i)]


def text_of(html):
    return " ".join(_html.unescape(re.sub(r"<[^>]+>", " ", html)).split())


def awc(H, k):
    """the awaiting card of one made-up person, as text"""
    s = sect(H, "wa-await")
    i = s.index('data-ph="%s"' % PH[k])
    return text_of(s[s.rindex("<div", 0, i):s.index('<div class="awg">', i)])


def opens(F, rows):
    """one made-up number's chat through wa_chat(): True when it ends awaiting. rows: (in/out, HH:MM:SS, text, type, status, sender)"""
    its = [F["C"].wa_item({"rid": 9000 + i, "mid": "u%d" % i, "phone": N(950), "dir": d, "ts": "%sT%s+05:30" % (D0, hms), "mtype": mt, "body": body,
                           "status": st_, "sent_by": by, "src": "log"}) for i, (d, hms, body, mt, st_, by) in enumerate(rows)]
    return F["C"].wa_chat(its)["open"] is not None


Q_IN = ("in", "09:00:00", "kab aana hai", "text", "received", "")


def after_reply(F, x):
    return opens(F, [Q_IN, ("out", "09:10:00", "kal aaiye", "text", "delivered", "shivani"), ("in", "09:20:00", x, "text", "received", "")])


def after_tpl(F, x):
    return opens(F, [("out", "08:30:00", "Template: visit", "template", "sent", "portal"), ("in", "09:00:00", x, "text", "received", "")])


def went_back(F, hms, body, mt="text", status="sent", by="shivani"):
    """does this ONE outgoing row answer a question asked at 09:00:00?"""
    return not opens(F, [Q_IN, ("out", hms, body, mt, status, by)])


AWAIT_T = sorted(["QUE", "FAIL", "OLD", "SHORT", "LATE", "THREE", "DNEW", "DUNS", "TPL", "LTHX", "ACK1", "RETRY", "YES", "XSS", "FRESH", "FU1", "TQ", "QTT", "TLATE", "QM1", "QM2", "AUTO", "HSM", "TPLTXT"])
AWAIT_E = sorted(AWAIT_T + ["DONE", "DTHX", "NP"])          # with no marks: the Done chats and the unknown number are back
OPEN_SHIV = sorted(set(AWAIT_T) - {"OLD", "FU1"})          # the chats awaiting that began on her duty today
ACKS = ["ok", "OK.", "Okay", "okk", "k", "thanks", "Thank you", "thank you doctor", "Thank you so much sir", "thanku ji", "ok thanks",
        "theek hai", "thik hai ji", "accha", "hello", "Hi", "namaste", "Good morning", "good night doctor sahab", "ram ram",
        "\U0001f64f", "\U0001f44d\U0001f44d", "ok \U0001f44d", "thanks \U0001f64f\U0001f64f", "ठीक है",
        "धन्यवाद", "नमस्ते डॉक्टर साहब", "ओके"]
QMARKS = ["ok?", "ok ?", "Hello?", "theek hai?", "\u0920\u0940\u0915 \u0939\u0948?"]
NOT_ACKS = QMARKS + ["ok\u061f", "thanks\uff1f", "", "haan", "yes", "no", "nahi", "ji", "doctor sahab", "ok kal aata hoon", "ok 5 baje", "thanks, report bhej dijiye", "hello?? koi hai",
            "ok but dard hai", "kab aana hai", "?", "\U0001f62d", "ok \U0001f62d", "sir \U0001f64f", "theek nahi hai", "good", "call me",
            "ok ok ok ok", "thank you doctor sahab, aapne bahut achha ilaaj kiya, bhagwan aapka bhala kare"]

CHECKS = [
    # ---- a. per chat; what went back
    ("A1 THE FAULT (F-1323): a chat answered, then \"ok\" from the sender -- the chat is NOT awaiting (green, answered on WhatsApp)",
     lambda F: st(F["T"][0], "OK") == ("green", "answered on WhatsApp") and "OK" not in waiting(F["T"][0])),
    ("A2 answered, then a real question: the chat IS awaiting again, from the question (09:30), one message",
     lambda F: st(F["T"][0], "QUE")[0] == "rose" and st(F["T"][0], "QUE")[1].startswith("WhatsApp awaiting") and chat(F["T"][0], "QUE")["n"] == 1
     and chat(F["T"][0], "QUE")["upto"] == D0 + " 09:30:00"),
    ("A3 a reply whose status is 'sent' (MyOperator accepted it; the delivery ping never came) answers the chat",
     lambda F: st(F["T"][0], "SENT") == ("green", "answered on WhatsApp") and "SENT" not in waiting(F["T"][0])),
    ("A4 a reply 'delivered' answers the chat", lambda F: st(F["T"][0], "DELV") == ("green", "answered on WhatsApp")),
    ("A5 a FAILED reply does not: awaiting, and the block says a reply was tried and NOT delivered",
     lambda F: st(F["T"][0], "FAIL")[0] == "rose" and "FAIL" in waiting(F["T"][0]) and "NOT delivered" in chat(F["T"][0], "FAIL")["tried"]),
    ("A6 a reply still 'retrying' (queued, not accepted) does not: the person is amber 'tried', the chat is on the awaiting list",
     lambda F: st(F["T"][0], "RETRY") == ("amber", "tried · not answered yet") and "RETRY" in waiting(F["T"][0]) and "retrying" in chat(F["T"][0], "RETRY")["tried"]),
    ("A7 a template never answers: awaiting", lambda F: st(F["T"][0], "TPL")[0] == "rose" and "TPL" in waiting(F["T"][0])),
    ("A8 an answered call of 60 s, 40 minutes after the message, answers the chat (answered by a call)",
     lambda F: st(F["T"][0], "CALL") == ("green", "answered by a call") and "CALL" not in waiting(F["T"][0])),
    ("A9 a call of 40 s with 15 s spoken does not; a call 3 clinic hours later does not",
     lambda F: st(F["T"][0], "SHORT")[0] == "amber" and st(F["T"][0], "LATE")[0] == "amber" and {"SHORT", "LATE"} <= set(waiting(F["T"][0]))),
    ("A10 the call rule runs from the sender's LAST word: wrote 08:10 and 11:20, called 11:40 -- answered",
     lambda F: st(F["T"][0], "LAST") == ("green", "answered by a call") and "LAST" not in waiting(F["T"][0])),
    ("A11 three unanswered messages are ONE chat: one line in the block (3 messages, 1 photo and the last text), one row on the staff card",
     lambda F: chat(F["T"][0], "THREE")["n"] == 3 and chat(F["T"][0], "THREE")["media"] == "1 photo" and chat(F["T"][0], "THREE")["text"] == "yeh sujan theek hai kya"
     and open_keys(card(F["T"][0], "shivani")).count("THREE") == 1),
    # ---- b. a bare acknowledgement
    ("B1 two folded-hands emoji after the reply do not reopen; thanks in Hindi with 'doctor sahab' does not",
     lambda F: st(F["T"][0], "EMO") == ("green", "answered on WhatsApp") and st(F["T"][0], "HIN") == ("green", "answered on WhatsApp")
     and not {"EMO", "HIN"} & set(waiting(F["T"][0]))),
    ("B2 \"haan\" after our question is an ANSWER, not an acknowledgement: it reopens the chat",
     lambda F: st(F["T"][0], "YES")[0] == "rose" and "YES" in waiting(F["T"][0])),
    ("B3 a bare \"hello\" with nothing before it opens the chat (there was no reply for it to follow)",
     lambda F: st(F["T"][0], "ACK1")[0] == "rose" and "ACK1" in waiting(F["T"][0])),
    ("B4 \"thank you\" two days after the reply (later than 24 hours) reopens -- when in doubt it reopens",
     lambda F: st(F["T"][0], "LTHX")[0] == "rose" and "LTHX" in waiting(F["T"][0]) and chat(F["T"][0], "LTHX")["n"] == 1),
    ("B5 the list itself: %d acknowledgements in English, Hindi and Hinglish are bare; %d other messages are not (a yes, a digit, a question, a crying face, 'doctor sahab' alone, a long thank-you)" % (len(ACKS), len(NOT_ACKS)),
     lambda F: all(F["C"].wa_is_ack("text", x) for x in ACKS) and not any(F["C"].wa_is_ack("text", x) for x in NOT_ACKS)
     and not F["C"].wa_is_ack("image", "ok") and not F["C"].wa_is_ack("audio", "") and F["C"].wa_is_ack("reaction", "\U0001f44d")),
    # ---- the owner's ruling of 13-Nov: a bare acknowledgement after a TEMPLATE
    ("T1 a template went out, the patient wrote \"ok\": NOT awaiting (no chat is opened; the person reads 'no reply needed'; it is on no staff card)",
     lambda F: "TOK" not in waiting(F["T"][0]) and st(F["T"][0], "TOK") == ("green", "no reply needed") and "TOK" not in listed(F["T"][0], "answered")
     and all(p["phone"] != PH["TOK"] for p, _w, _a in card(F["T"][0], "shivani")["wa"])),
    ("T2 a template went out, the patient asked a real question: awaiting",
     lambda F: "TQ" in waiting(F["T"][0]) and st(F["T"][0], "TQ")[0] == "rose" and chat(F["T"][0], "TQ")["n"] == 1),
    ("T3 a real question, then ONLY a template, then \"thanks\": STILL awaiting -- the question was never answered (one chat, 2 messages, from the question)",
     lambda F: "QTT" in waiting(F["T"][0]) and st(F["T"][0], "QTT")[0] == "rose" and chat(F["T"][0], "QTT")["n"] == 2
     and chat(F["T"][0], "QTT")["first_h"] == "8:45 am" and open_keys(card(F["T"][0], "shivani")).count("QTT") == 1),
    ("T4 a template, then \"ok\" 30 hours later: awaiting (later than 24 hours it opens the chat)",
     lambda F: "TLATE" in waiting(F["T"][0]) and st(F["T"][0], "TLATE")[0] == "rose"),
    # ---- build 3, must-fix 1: a question mark makes it a question
    ("Q1 \"ok?\", \"ok ?\", \"Hello?\", \"theek hai?\" and the Hindi \"theek hai?\" each OPEN the chat -- after a reply and after a template (the same words without the mark do not)",
     lambda F: all(after_reply(F, x) and after_tpl(F, x) for x in QMARKS) and not any(after_reply(F, x) or after_tpl(F, x) for x in ("ok", "Hello", "theek hai"))),
    ("Q2 on the page: answered, then \"ok?\" -- awaiting from the question mark; a template, then \"Hello?\" -- awaiting",
     lambda F: {"QM1", "QM2"} <= set(waiting(F["T"][0])) and chat(F["T"][0], "QM1")["upto"] == D0 + " 09:20:00" and chat(F["T"][0], "QM1")["n"] == 1
     and st(F["T"][0], "QM2")[0] == "rose"),
    # ---- build 3, must-fix 2: an automatic outgoing message never answers
    ("R1 an automatic greeting -- plain text, 'sent', NO sender recorded, 20 s after the message -- does NOT answer: awaiting, rose (it is not even a 'try')",
     lambda F: "AUTO" in waiting(F["T"][0]) and st(F["T"][0], "AUTO")[0] == "rose" and chat(F["T"][0], "AUTO")["tried"] == ""),
    ("R2 an 'hsm' row (a structured type) does NOT answer, though a staff name is on it: awaiting",
     lambda F: "HSM" in waiting(F["T"][0]) and st(F["T"][0], "HSM")[0] == "rose"),
    ("R3 a row whose text begins \"Template:\" under the type 'text' does NOT answer: awaiting",
     lambda F: "TPLTXT" in waiting(F["T"][0]) and st(F["T"][0], "TPLTXT")[0] == "rose"),
    ("R4 a reply typed in the panel -- plain text, no sender recorded, 5 minutes later -- DOES answer",
     lambda F: "PANEL" not in waiting(F["T"][0]) and st(F["T"][0], "PANEL") == ("green", "answered on WhatsApp") and "PANEL" in listed(F["T"][0], "answered")),
    ("R5 each branch alone: the Inbox's own types answer (text, image, document, audio, and video) with a sender, even 20 s later; "
     "hsm / interactive / button / sticker / an unknown type never; \"template: ...\" in small letters never; no sender at 60 s no, at 61 s yes",
     lambda F: all(went_back(F, "09:00:20", "ji", mt) for mt in ("text", "image", "document", "audio", "video"))
     and not any(went_back(F, "09:10:00", "ji", mt) for mt in ("hsm", "interactive", "button", "sticker", "location", "template"))
     and not went_back(F, "09:10:00", "template: hours") and not went_back(F, "09:10:00", "  Template: hours")
     and not went_back(F, "09:01:00", "ji", by="") and went_back(F, "09:01:01", "ji", by="") and not went_back(F, "09:10:00", "ji", status="failed")),
    ("R6 an automatic message opens no chat for a bare \"ok\" after it (any accepted outgoing message, the ruling) -- and a real question after it opens one",
     lambda F: not opens(F, [("out", "08:30:00", "Thank you for contacting", "text", "sent", ""), ("in", "09:00:00", "ok", "text", "received", "")])
     and opens(F, [("out", "08:30:00", "Thank you for contacting", "text", "sent", ""), ("in", "09:00:00", "fees kitni hai", "text", "received", "")])),
    # ---- build 3, must-fix 3: the call-side figure
    ("G1 a MISSED CALL followed by a free-text WhatsApp at 'sent' is amber 'tried · not reached', exactly as before this kit -- no Needs-you line",
     lambda F: st(F["T"][0], "MC") == ("amber", "tried · not reached") and not any(n.get("phone") == PH["MC"] for n in F["T"][0]["needs"])),
    # ---- c. midnight does not cut a chat
    ("C1 wrote last night 22:30, answered this morning 08:10: YESTERDAY's page reads answered; today's block lists it under Answered today",
     lambda F: st(F["Y"][0], "MID") == ("green", "answered on WhatsApp") and "MID" not in waiting(F["T"][0]) and "MID" in listed(F["T"][0], "answered")),
    ("C2 a message of two days ago nobody answered is STILL awaiting today: on the block, marked as from an earlier day, waiting '2 days'",
     lambda F: "OLD" in waiting(F["T"][0]) and chat(F["T"][0], "OLD")["old"] is True and chat(F["T"][0], "OLD")["wait_h"] == "2 days"
     and chat(F["T"][0], "OLD")["last_h"] == "Wed 11 Nov, 10:00 am" and aw(F["T"][0])["old"] == 2),
    ("C3 the people list stays the window's own: a chat of an earlier day is on the block, not among today's people or today's WhatsApp count",
     lambda F: person(F["T"][0], "OLD") == {} and F["T"][0]["counts"]["wa_in"] == sum(1 for m in MSGS if m[1] == "in" and m[2] == D0)),
    # ---- d. the owner's two buttons
    ("D1 Done, then silence: off the awaiting list, on the Done list; the person reads 'no reply needed'",
     lambda F: "DONE" not in waiting(F["T"][0]) and "DONE" in listed(F["T"][0], "done") and st(F["T"][0], "DONE") == ("green", "no reply needed")),
    ("D2 Done last evening, then a NEW real message this morning: awaiting again, and no longer on the Done list",
     lambda F: "DNEW" in waiting(F["T"][0]) and "DNEW" not in listed(F["T"][0], "done") and chat(F["T"][0], "DNEW")["upto"] == D0 + " 09:30:00"),
    ("D3 Done, then \"Thanks\" with an emoji: stays closed",
     lambda F: "DTHX" not in waiting(F["T"][0]) and "DTHX" in listed(F["T"][0], "done") and st(F["T"][0], "DTHX")[0] == "green"),
    ("D4 Done reaches only the message he saw: one that arrived before he pressed, after the one shown, keeps the chat awaiting",
     lambda F: "DUNS" in waiting(F["T"][0]) and chat(F["T"][0], "DUNS")["n"] == 1 and chat(F["T"][0], "DUNS")["upto"] == D0 + " 08:26:00"),
    ("D5 Not a patient: the number is off the awaiting list, grey among the people, in no Needs-you line, on the Not-a-patient list",
     lambda F: "NP" not in waiting(F["T"][0]) and st(F["T"][0], "NP") == ("grey", "not a patient") and listed(F["T"][0], "np") == ["NP"]
     and not any(n.get("phone") == PH["NP"] for n in F["T"][0]["needs"])),
    ("D9 a marked number is never hidden silently: it wrote once after the mark -- its row on the Not-a-patient list says 'wrote again · 1 since', and so does the folded line",
     lambda F: [x["again"] for x in aw(F["T"][0])["np"]] == [1] and "wrote again · 1 since" in text_of(sect(F["T"][1], "wa-await"))
     and "Not a patient 1 number · 1 wrote again · undo" in text_of(sect(F["T"][1], "wa-await"))),
    ("D6 Not a patient on the staff card: its WhatsApps are in no figure and its missed call is no missed call-back (4 missed to 3); "
     "the call she ANSWERED from that number stays on her card, counted and 'not logged' as before",
     lambda F: "NP" not in open_keys(card(F["T"][0], "shivani")) and all(p["phone"] != PH["NP"] for p, _i in card(F["T"][0], "shivani")["missed_items"])
     and all(p["phone"] != PH["NP"] for p, _i in card(F["T"][0], "shivani")["not_back"])
     and card(F["T"][0], "shivani")["missed"] == 3 and card(F["E"][0], "shivani")["missed"] == 4
     and any(p["phone"] == PH["NP"] for p, _i in card(F["T"][0], "shivani")["items"]) and any(p["phone"] == PH["NP"] for p, _i in card(F["T"][0], "shivani")["not_logged"])
     and card(F["T"][0], "shivani")["answered"] == card(F["E"][0], "shivani")["answered"] == 3),
    ("D7 Undo of Not a patient: the number is back -- awaiting, rose, on her card (the WhatsApp and the missed call) -- and the store holds BOTH rows",
     lambda F: "NP" in waiting(F["undone"][0]) and st(F["undone"][0], "NP")[0] == "rose" and "NP" in open_keys(card(F["undone"][0], "shivani"))
     and card(F["undone"][0], "shivani")["missed"] == 4 and listed(F["undone"][0], "np") == []
     and len(F["rows_undone"]) == len(F["rows_good"]) + 1 and F["rows_undone"][:len(F["rows_good"])] == F["rows_good"]),
    ("D8 the lists: %d chats awaiting (2 from an earlier day), 9 answered today, 2 Done, 1 Not a patient" % len(AWAIT_T),
     lambda F: waiting(F["T"][0]) == AWAIT_T and aw(F["T"][0])["n"] == len(AWAIT_T) and listed(F["T"][0], "answered") == sorted(["OK", "SENT", "DELV", "MID", "CALL", "LAST", "EMO", "HIN", "PANEL"])
     and listed(F["T"][0], "done") == ["DONE", "DTHX"]),
    # ---- e. the same rule wherever the figure is shown
    ("E1 her staff card counts CHATS: 33 on duty, 11 answered, 22 awaiting -- exactly the block's chats that began today",
     lambda F: wa_fig(card(F["T"][0], "shivani")) == (33, 11, 22) and open_keys(card(F["T"][0], "shivani")) == OPEN_SHIV),
    ("E2 her own card as the staff app reads it (Mere calls) carries the same WhatsApp figures, and 22 rows behind 'WhatsApp'",
     lambda F: (F["mine"]["shivani"]["figs"]["wa_in"], F["mine"]["shivani"]["figs"]["wa_ans"]) == (33, 11)
     and sum(1 for r in F["mine"]["shivani"]["calls"] if "wa" in r["figs"]) == 22),
    ("E3 yesterday's card (Alisha, Mere calls): 2 chats on duty, 1 answered -- a reply 'sent' counts; the chat he marked Done is not hers to answer",
     lambda F: (F["mine"]["alisha_y"]["figs"]["wa_in"], F["mine"]["alisha_y"]["figs"]["wa_ans"]) == (2, 1)),
    ("E7 the 7-day page: her card 35 chats on duty, 12 answered (a chat answered two days ago and reopened today is two); Alisha's 2, 1 answered",
     lambda F: wa_fig(card(F["W"][0], "shivani")) == (35, 12, 23) and wa_fig(card(F["W"][0], "alisha")) == (2, 1, 1)),
    ("E4 the strip: people nobody has answered = the rose people; WhatsApp replies counted when accepted (a 'sent' one included)",
     lambda F: F["T"][0]["counts"]["awaiting"] == sum(1 for p in F["T"][0]["people"] if p["state"] == "rose")
     and F["T"][0]["counts"]["wa_replied"] == sum(1 for m in MSGS if m[1] == "out" and m[2] == D0 and m[4] != "template" and m[6] in ("sent", "delivered"))),
    ("E5 every person rose by WhatsApp today is on the block; every block chat that began today is a rose or amber person",
     lambda F: {KEY_OF[p["phone"]] for p in F["T"][0]["people"] if p.get("wa_wait")} <= set(AWAIT_T)
     and all(st(F["T"][0], k)[0] in ("rose", "amber") for k in OPEN_SHIV)),
    ("E6 the follow-up pill: wrote yesterday and nobody replied -- 'Wrote back · to call'; wrote and the reply was 'sent' -- no longer 'wrote back'",
     lambda F: fu_row(F["T"][0], "FU1")["pill"] == "Wrote back · to call" and fu_row(F["T"][0], "FU2")["pill"] == "Not called yet"),
    # ---- the store: missing, empty, locked, corrupt
    ("K1 no store at all: the page opens, no marks -- the two Done chats and the unknown number are awaiting again (%d chats), nothing said to be wrong" % len(AWAIT_E),
     lambda F: waiting(F["E"][0]) == AWAIT_E and aw(F["E"][0])["marks_ok"] is True and F["E"][1].rstrip().endswith("</body></html>")
     and "could not be read just now — every chat" not in F["E"][1]),
    ("K2 an EMPTY store file: the same -- no marks, the page whole",
     lambda F: waiting(F["empty"][0]) == AWAIT_E and aw(F["empty"][0])["marks_ok"] is True and F["empty"][1].rstrip().endswith("</body></html>")),
    ("K3 a CORRUPT store: the page opens whole, every chat shows (none hidden), and the block says the marks could not be read",
     lambda F: waiting(F["corrupt"][0]) == AWAIT_E and aw(F["corrupt"][0])["marks_ok"] is False and F["corrupt"][1].rstrip().endswith("</body></html>")
     and "Your Done and Not-a-patient marks could not be read just now" in F["corrupt"][1]),
    ("K4 a store LOCKED whole by another writer: the same -- every chat shows, the page says so, no error",
     lambda F: waiting(F["locked"][0]) == AWAIT_E and aw(F["locked"][0])["marks_ok"] is False and F["locked"][1].rstrip().endswith("</body></html>")),
    ("K5 the store (WAL) while another writer holds the write lock: the marks are still READ (the page as usual); a tap is told to try again (503), nothing written",
     lambda F: waiting(F["wlocked"][0]) == AWAIT_T and aw(F["wlocked"][0])["marks_ok"] is True and F["post_wlocked"][0] == 503
     and F["post_wlocked"][1].get("ok") is False and F["rows_wlocked"] == F["rows_good"]),
    ("K6 a tap on a corrupt store: 503 in words, never a crash, and the file is left exactly as it was",
     lambda F: F["post_corrupt"][0] == 503 and F["post_corrupt"][1].get("ok") is False and F["corrupt_kept"] is True),
    ("K9 the INBOX unreadable: the page opens whole and says so; the block shows no figure (never 'none awaiting'); the calls are as usual",
     lambda F: F["noinbox"][1].rstrip().endswith("</body></html>") and aw(F["noinbox"][0])["ok"] is False
     and "The WhatsApp messages could not be read just now — nothing is shown as zero." in sect(F["noinbox"][1], "wa-await")
     and "Awaiting a reply" not in sect(F["noinbox"][1], "wa-await") and F["noinbox"][0]["counts"]["calls"] == F["T"][0]["counts"]["calls"]),
    ("X1 the block's maker made to FAIL: the page is whole and the block says 'The WhatsApp awaiting list could not be made — open WhatsApp Inbox' "
     "(a link to the Inbox) instead of vanishing; the people and the staff cards are as usual",
     lambda F: F["broken"][1].rstrip().endswith("</body></html>") and aw(F["broken"][0]) == {"failed": True}
     and "The WhatsApp awaiting list could not be made — open WhatsApp Inbox" in text_of(sect(F["broken"][1], "wa-await"))
     and '<a href="/portal/inbox">WhatsApp Inbox</a>' in sect(F["broken"][1], "wa-await") and "Awaiting a reply" not in sect(F["broken"][1], "wa-await")
     and [st(F["broken"][0], k) for k in PH] == [st(F["T"][0], k) for k in PH] and wa_fig(card(F["broken"][0], "shivani")) == wa_fig(card(F["T"][0], "shivani"))),
    ("K7 no view raised an error; the staff cards and the follow-up list were made on every store",
     lambda F: F["err"] == [] and all(F[k][0].get("staff") is not None and F[k][0]["fu"]["found"] for k in ("T", "E", "empty", "corrupt", "locked", "wlocked", "undone", "broken"))),
    ("K8 with the marks unreadable the other figures are those of 'no marks' exactly (people, strip, her card)",
     lambda F: [st(F["corrupt"][0], k) for k in PH] == [st(F["E"][0], k) for k in PH] and F["corrupt"][0]["counts"] == F["E"][0]["counts"]
     and wa_fig(card(F["corrupt"][0], "shivani")) == wa_fig(card(F["E"][0], "shivani")) == (36, 11, 25)),
    # ---- the door
    ("P1 the door by GET: 405 (never a link)", lambda F: F["door"]["get"] == 405),
    ("P2 the door without a login: sent to the login page, nothing written",
     lambda F: F["door"]["nologin"][0] == 302 and F["door"]["nologin"][2].endswith("/portal/login")),
    ("P3 the door for a staff login: 403", lambda F: F["door"]["staff"][0] == 403),
    ("P4 the door for the doctor WITHOUT the page's own header: 400; after all three the store is still not even made",
     lambda F: F["door"]["nohdr"][0] == 400 and F["door"]["closed_rows"] == 0),
    ("P5 a bad number, an unknown act, a Done with no message or a wrong one: 400 each",
     lambda F: F["door"]["bad"] == [400, 400, 400, 400]),
    ("P6 a number the Inbox holds no WhatsApp from, or a Done for a message that is not there: 409, nothing written",
     lambda F: F["door"]["unknown"] == [409, 409, 409] and F["door"]["unknown_rows"] == 0),
    ("P7 Done by the doctor: 200, ONE row with the number, the message reached, who (manoj) and when; the chat leaves the awaiting list",
     lambda F: F["door"]["done"][0] == 200 and F["door"]["done"][1]["ok"] is True
     and [r[1:] for r in F["door"]["rows1"]] == [(PH["QUE"], "done", D0 + " 09:30:00", "manoj", D0 + " 12:00:00")]
     and "QUE" not in waiting(F["door"]["after_done"]) and "QUE" in listed(F["door"]["after_done"], "done")),
    ("P8 the same Done again: 200, no second row", lambda F: F["door"]["again"][0] == 200 and F["door"]["rows2"] == F["door"]["rows1"]),
    ("P9 Undo: 200, a NEW row (the Done row untouched); the chat is back on the awaiting list; a second undo: 409",
     lambda F: F["door"]["undo"][0] == 200 and len(F["door"]["rows3"]) == 2 and F["door"]["rows3"][0] == F["door"]["rows1"][0]
     and F["door"]["rows3"][1][2] == "undo_done" and "QUE" in waiting(F["door"]["after_undo"]) and F["door"]["undo2"][0] == 409),
    ("P10 Not a patient and its undo: 200 each; four rows in all, every one with who and when; the store is in WAL mode",
     lambda F: F["door"]["np"][0] == 200 and F["door"]["np_undo"][0] == 200 and [r[2] for r in F["door"]["rows5"]] == ["done", "undo_done", "not_patient", "undo_not_patient"]
     and all(r[4] == "manoj" and r[5] == D0 + " 12:00:00" for r in F["door"]["rows5"]) and F["door"]["wal"] == "wal"),
    ("P11 the page itself: 200 for the doctor, the login page without a login", lambda F: F["route"] == (200, 302)),
    # ---- the page
    ("H1 the block in the mock-up's words: 'Awaiting a reply · %d chats', 'One line per chat, not per message.'" % len(AWAIT_T),
     lambda F: ("Awaiting a reply · %d chats" % len(AWAIT_T)) in text_of(sect(F["T"][1], "wa-await")) and "One line per chat, not per message. 2 from an earlier day." in text_of(sect(F["T"][1], "wa-await"))
     and "Call Console · WhatsApp" in sect(F["T"][1], "wa-await")),
    ("H2 one chat's card: name · ID, the wait, the number · last message, the words; Reply (into the Inbox), Call, and the two buttons",
     lambda F: awc(F["T"][1], "QUE") == "Test Question · ID T-502 2 h 30 min %s · last message 9:30 am “aur dawai kab tak leni hai”" % F["C"].fmt_num(PH["QUE"])
     and sect(F["T"][1], "wa-await").count(">Done — no reply needed</button>") == len(AWAIT_T)
     and sect(F["T"][1], "wa-await").count(">Not a patient</button>") == len(AWAIT_T)
     and sect(F["T"][1], "wa-await").count('class="awb pri" href="/portal/inbox?m=wamid.T') == len(AWAIT_T)
     and sect(F["T"][1], "wa-await").count(">Call</button>") == len(AWAIT_T)),
    ("H3 an unknown number reads 'Unknown number' with its photos counted (no marks: 2 photos and the last text); a 30-minute wait is amber, a long one red",
     lambda F: "Unknown number" in awc(F["E"][1], "NP") and "2 photos · “rates bhej diye hain”" in awc(F["E"][1], "NP")
     and chat(F["T"][0], "FRESH")["wait_h"] == "30 min" and chat(F["T"][0], "FRESH")["tone"] == "amber" and chat(F["T"][0], "QUE")["tone"] == "rose"),
    ("H4 the three folded lines: Answered today 9 chats; Done — no reply needed 2 chats · undo; Not a patient 1 number · undo; each with its Undo",
     lambda F: all(x in text_of(sect(F["T"][1], "wa-await")) for x in ("Answered today 9 chats", "Done — no reply needed 2 chats · undo", "Not a patient 1 number · 1 wrote again · undo"))
     and sect(F["T"][1], "wa-await").count("waMark(this,'undo_done')") == 2 and sect(F["T"][1], "wa-await").count("waMark(this,'undo_not_patient')") == 1),
    ("H5 the five sentences of the mock-up, word for word",
     lambda F: all(x in text_of(sect(F["T"][1], "wa-await")) for x in (
         "When a chat leaves this list", "A reply went out and MyOperator accepted it — yours, staff’s, or one typed in the MyOperator panel.",
         "Or a call to that number was answered.", "“Ok”, “thanks” or a greeting after your reply does not bring it back.",
         "Midnight does not cut a chat: last night’s reply clears this morning’s line.",
         "A number marked Not a patient never shows as a missed call-back on a staff card."))),
    ("H6 a message that is a script tag is shown as text, escaped, everywhere on the page",
     lambda F: XSS_TEXT not in F["T"][1] and F["T"][1].count("&lt;script&gt;alert(1)&lt;/script&gt;") >= 2),
    ("H7 no message text is inside any script or any onclick; every waMark call carries only its act",
     lambda F: not any(b in s for b in BODIES + ["alert(1)"] for s in re.findall(r"<script>(.*?)</script>", F["T"][1], re.S))
     and not any(b in a for b in BODIES + ["alert(1)"] for a in re.findall(r'onclick="([^"]*)"', F["T"][1]))
     and set(re.findall(r"waMark\(this,'([a-z_]+)'\)", F["T"][1])) == {"done", "not_patient", "undo_done", "undo_not_patient"}),
    ("H8 the staff section says chats: 'WhatsApp chats on duty · 33 → 11 answered'; the page says a chat is answered by a reply MyOperator accepted, and what a template does",
     lambda F: "WhatsApp chats on duty · 33 → 11 answered" in text_of(sect(F["T"][1], "staff")) and "a reply MyOperator accepted (sent, delivered or read)" in F["T"][1]
     and "delivered reply" not in F["T"][1] and "a template, an automatic message or a failed reply never answers a chat, and a bare “ok” or thanks within 24 hours after one opens none; “ok?” is a question." in F["T"][1]),
    ("H9 the page whole: the player, the people, the follow-up sections and the block are all there",
     lambda F: all(x in F["T"][1] for x in ('id="pl"', 'id="people"', 'id="fu-grace"', 'id="wa-await"', "function waMark(", "function playJk(")) and F["T"][1].rstrip().endswith("</body></html>")),
]
MUST_RED_ON_BASE = ("A1 ",)          # the control: on S817's page the chat answered-then-"ok" still reads awaiting


def run(page_file, quiet=False, light=False):
    try:
        F = facts(page_file, light=light)
    except Exception as e:
        F = {"err": ["facts: %s %s" % (type(e).__name__, str(e)[:120])]}
        if not quiet:
            print("the page could not be read: %s" % F["err"][0])
    res = []
    for name, fn in CHECKS:
        try:
            ok = bool(fn(F))
        except Exception as e:
            ok, name = False, name + "  [%s: %s]" % (type(e).__name__, str(e)[:60])
        res.append((name, ok))
        if not quiet:
            print(("ok   " if ok else "RED  ") + name)
    return res, F


# what each mutation of the new page must turn red (old text -> new text, found exactly once)
MUTATIONS = [
    ("M1 only a delivered or read reply counts again (a 'sent' one does not)", 'WA_ACCEPTED = ("sent", "delivered", "read") ', 'WA_ACCEPTED = ("delivered", "read") ', "A3 "),
    ("M2 no acknowledgement is ever bare (\"ok\" reopens the chat -- the fault)", 'is_ack = it["ack"] if "ack" in it else wa_is_ack(it.get("mtype"), it.get("txt", it.get("body")))', "is_ack = False", "A1 "),
    ("M3 every message after a reply is taken for an acknowledgement (a real question hidden)", "                if (ep is None and back is not None and is_ack\n", "                if (ep is None and back is not None\n", "A2 "),
    ("M4 the look-back cut to nothing (midnight cuts the chat again)", "WA_BACK_DAYS = 7 ", "WA_BACK_DAYS = 0 ", "C2 "),
    ("M5 the days after the window not read (a reply across midnight does not answer)", '    hi = max(str(d_to), today.isoformat())\n', '    hi = str(d_to)\n', "C1 "),
    ("M6 the owner's Done not read", 'it["wa_dones"] = dz["done_t"].get(it["phone"], ())', 'it["wa_dones"] = ()', "D1 "),
    ("M7 a Done reaching every message up to the moment he pressed (one he had not seen is hidden)", '(it is None or it["t"] > dones[di][0])', '(it is None or it["t"] > dones[di][1])', "D4 "),
    ("M8 a Not-a-patient number's missed call kept on the staff cards", 'if it.get("ch") == "wa" or (it["kind"] == "in_miss" and p.get("not_patient")):', 'if it.get("ch") == "wa":', "D6 "),
    ("M22 a Not-a-patient number taken off the staff cards whole (its answered calls too -- more than was asked)", 'if it.get("ch") == "wa" or (it["kind"] == "in_miss" and p.get("not_patient")):', 'if it.get("ch") == "wa" or p.get("not_patient"):', "D6 "),
    ("M9 an undo not honoured", "        elif act == \"undo_not_patient\":\n            np_.pop(ph, None)\n", "        elif act == \"undo_not_patient\":\n            pass\n", "D7 "),
    ("M10 the 24 hours taken off (a thank-you days later stays hidden)", "<= WA_ACK_WITHIN_H * 3600):", "<= WA_ACK_WITHIN_H * 3600000):", "B4 "),
    ("M11 a failed reply taken as one that went back", '    if it.get("kind") != "wa_out" or (it.get("status") or "") not in WA_ACCEPTED:\n        return False\n', '    if it.get("kind") not in ("wa_out", "wa_fail"):\n        return False\n', "A5 "),
    ("M12 the type not looked at (an hsm / interactive / button row answers)", '    if (it.get("mtype") or "text") not in WA_REPLY_TYPES:\n        return False\n', "", "R2 "),
    ("M25 a question mark not looked at (\"ok?\" a bare acknowledgement again)", " or any(q in str(text) + s for q in WA_QUESTION_MARKS):", ":", "Q1 "),
    ("M26 the text \"Template:\" not looked at (a template echoed as text answers)", '    if str(it.get("txt", it.get("body") or "")).lstrip().lower().startswith("template:"):\n        return False\n', "", "R3 "),
    ("M27 the 60 seconds not looked at (an automatic greeting answers)", "            and 0 <= (it[\"t\"] - last_in[\"t\"]).total_seconds() <= WA_AUTO_WITHIN_S):", "            and False):", "R1 "),
    ("M28 'sent' taken out of 'tried' for a missed call too (the call-side figure moves)", '("retrying", "unsure") if first.get("ch") == "wa" else ("sent", "retrying", "unsure"))', '("retrying", "unsure"))', "G1 "),
    ("M29 the block vanishing when it cannot be made", '        return {"failed": True} ', "        return None ", "X1 "),
    ("M30 what a marked number wrote since the mark not counted", "                        again[w[\"phone\"]] = again.get(w[\"phone\"], 0) + 1", "                        pass", "D9 "),
    ("M23 a bare \"ok\" after a template opening a chat again (the flood the ruling stops)", '                back = (it["t"], WA_TPL)', "                pass", "T1 "),
    ("M24 a template made to close an open chat (a question never answered would be hidden)", '            elif it["kind"] in ("wa_out", "wa_tpl") and (it.get("status") or "") in WA_ACCEPTED:\n                back = (it["t"], WA_TPL)', '            elif it["kind"] in ("wa_out", "wa_tpl") and (it.get("status") or "") in WA_ACCEPTED:\n                back, ep = (it["t"], WA_TPL), None', "T3 "),
    ("M13 the call rule from the FIRST message again", 'if wait_h(ep["msgs"][-1]["t"], it["t"]) <= WA_CALL_WITHIN_H:', 'if wait_h(ep["msgs"][0]["t"], it["t"]) <= WA_CALL_WITHIN_H:', "A10 "),
    ("M14 the staff card counting messages again", "                mine = [w for w in ep[\"msgs\"] if not w.get(\"ctx\") and on_duty(w[\"t\"])]\n                if not mine or any((w[\"ref\"], key) in accepted for w in mine):\n                    continue\n                w = next((x for x in mine if reviewed(x)), mine[0])\n",
     "                mine = [w for w in ep[\"msgs\"] if not w.get(\"ctx\") and on_duty(w[\"t\"])]\n                if not mine or any((w[\"ref\"], key) in accepted for w in mine):\n                    continue\n                w = next((x for x in mine if reviewed(x)), mine[0])\n                c[\"wa_in\"] += len(mine) - 1\n", "E1 "),
    ("M15 the gate taken off the door", "    @gate\n    def _wa_mark():", "    def _wa_mark():", "P2 "),
    ("M16 the door not asking for the page's own header", 'if request.headers.get("X-Call-Console") != "1":', "if False:", "P4 "),
    ("M17 the door open to GET", 'methods=["POST"], endpoint="s818_wa_mark"', 'methods=["GET", "POST"], endpoint="s818_wa_mark"', "P1 "),
    ("M18 the door writing a number the Inbox does not hold", '        if act in ("done", "not_patient"):\n            try:\n                ok, msg, code = wa_mark_check(', '        if act in ("nothing",):\n            try:\n                ok, msg, code = wa_mark_check(', "P6 "),
    ("M19 a corrupt store taken for an empty one (the page would not say the marks are unreadable)", '        if "no such table" not in str(e).lower():     # a store with no table yet is an empty store\n            out["ok"] = False\n', '        if False:\n            out["ok"] = False\n', "K3 "),
    ("M20 the message drawn unescaped", "{% if a.text %}“{{ a.text }}”{% endif %}", "{% if a.text %}“{{ a.text|safe }}”{% endif %}", "H6 "),
    ("M21 a yes taken for an acknowledgement", '    "ok", "okay", "okk", "okey", "oky", "k", "kk",', '    "ok", "okay", "okk", "okey", "oky", "k", "kk", "haan",', "B2 "),
]

PAGE = os.path.join(PAGE_DIR, "calls_console.py")
if CONTROL:
    RES, F0 = run(PAGE, light=True)
    n_ok = sum(1 for _n, ok in RES if ok)
    hit = all(not ok for n, ok in RES if n.startswith(MUST_RED_ON_BASE))
    STORES or shutil.rmtree(TMP, ignore_errors=True)
    if hit:
        print("CONTROL: %d of %d red on this page, the answered-then-\"ok\" chat among them" % (len(RES) - n_ok, len(RES)))
        sys.exit(0)
    print("CONTROL FAILED: the answered-then-\"ok\" chat reads answered on this page")
    sys.exit(1)
RES, F0 = run(PAGE)
if HTML_OUT:
    open(HTML_OUT, "w", encoding="utf-8").write(F0["T"][1])
n_ok = sum(1 for _n, ok in RES if ok)
bad = len(RES) - n_ok
# ---- every other reader: the same figures as the base page gives on the same stores
same_n = same_ok = 0
if BASE_DIR and bad == 0:
    F1 = facts(os.path.join(BASE_DIR, "calls_console.py"), light=True)
    NT, NE, OT = F0["T"][0], F0["E"][0], F1["T"][0]           # new with the marks . new with no marks . the base page
    NY, OY = F0["Y"][0], F1["Y"][0]
    WA_KEYS = ("awaiting", "tried", "answered", "bar", "wa_replied")

    def calls_of(d):
        """each person's calls and contact counts (nothing of the awaiting rule)"""
        return [(p["phone"], p["name"], p["cid"], p["unknown"], p["n_calls"], p["n_wa"], p["n_in"], p["n_out"], p["n_missed"], p["tail"], p["flagged"],
                 p["mismatch"], p["any_answered"], p["booked"], [(x["id"], x["kind"], x["t"]) for x in p["calls"]]) for p in sorted(d["people"], key=lambda p: p["phone"])]

    def states(d):
        return {KEY_OF[p["phone"]]: p["state"] for p in d["people"]}

    def moved(new, old):
        return {k: (old[k], new[k]) for k in new if new[k] != old.get(k)}

    def strip(d):
        return {k: v for k, v in d["counts"].items() if k not in WA_KEYS}

    def call_figs(d, drop=()):
        out = []
        for c in (d.get("staff") or []):
            out.append((c["key"], c["answered"], c["rung"], c["missed"], c["made"], c["cb_in_h"], c["cb_later"], c.get("net_missed"), c.get("missed_people"),
                        len(c["not_logged"]), len(c["not_back"]), len(c["mismatch"]), c["agreed"], c["credited"], c["duty_h"], c["punch_h"],
                        sorted(it["ref"] for _p, it in c["items"]), sorted(it["ref"] for _p, it in c["missed_items"])))
        return out

    def fu_key(d, skip=()):
        fu = d["fu"]
        return (fu["found"], fu["open"], fu["removed"], fu["today"], fu["who"], fu["fl"], [(b[0], b[4], b[5], b[6], b[7]) for b in fu["bands"]],
                sorted((r["phone"], r["pill"], r["tone"], r["called"], r["reached"], r["closed"]) for b in fu["bands"] for r in b[3] if KEY_OF[r["phone"]] not in skip),
                [(r["phone"], r["closed"]) for r in fu["came"]])

    def mine_calls(m):
        return ({k: v for k, v in m["figs"].items() if k not in ("wa_in", "wa_ans")}, m["tone"], [r for r in m["calls"] if r["kind"] != "wa_in"], m["asks"], m["notes"], m["disputes"])

    A_C = {"OK": ("rose", "green"), "SENT": ("amber", "green"), "LAST": ("amber", "green"), "EMO": ("rose", "green"), "HIN": ("rose", "green"), "TOK": ("rose", "green"),
           "PANEL": ("amber", "green"), "AUTO": ("amber", "rose"), "HSM": ("amber", "rose"), "TPLTXT": ("amber", "rose")}
    D_C = dict(A_C, DONE=("rose", "green"), DTHX=("rose", "green"), NP=("rose", "grey"))
    SAME = [
        ("S1 the strip's call figures (calls, callers, answered in and out, the three missed chains, flagged, staff ≠ AI, WhatsApps received) -- with and without the marks",
         lambda: strip(NT) == strip(OT) == strip(NE) and NT["chips"]["all"] == OT["chips"]["all"] and NT["chips"]["calls"] == OT["chips"]["calls"]
         and NT["chips"]["wa"] == OT["chips"]["wa"] and NT["chips"]["unknown"] == OT["chips"]["unknown"]),
        ("S2 the people: the same people, the same calls and WhatsApps on each timeline, the same counts and outcome words -- today and on yesterday's page",
         lambda: calls_of(NT) == calls_of(OT) == calls_of(NE) and calls_of(NY) == calls_of(OY) and len(calls_of(NT)) >= 30),
        ("S3 every person with NO WhatsApp keeps their state (calls judged as before); with no marks, exactly ten people change and each as the kit says: "
         "\"ok\" after the reply, a reply 'sent', the call after the last word, the emoji, the Hindi thanks, \"ok\" after a template, the panel reply (amber to green); "
         "and three whose only 'reply' was automatic -- the greeting, the hsm row, the \"Template:\" text -- were amber 'tried' and are rose awaiting",
         lambda: all(states(NE)[k] == states(OT)[k] for k in states(OT) if not person(OT, k)["n_wa"]) and moved(states(NE), states(OT)) == A_C),
        ("S4 with the owner's marks, three more change and only those: the two Done chats (rose to green) and the Not-a-patient number (rose to grey)",
         lambda: moved(states(NT), states(OT)) == D_C),
        ("S5 yesterday's page: three people change and only those -- the chat answered across midnight (rose to green), the reply 'sent' (amber to green), the chat he marked Done last evening (rose to green)",
         lambda: moved(states(NY), states(OY)) == {"MID": ("rose", "green"), "FU2": ("amber", "green"), "DNEW": ("rose", "green")}),
        ("S6 Needs you: the same lines but for the people who changed (no marks: the four who were rose and are not awaiting, the three now rose)",
         lambda: sorted((n["tone"], n["who"], n["text"]) for n in OT["needs"] if KEY_OF.get(n.get("phone")) not in ("OK", "EMO", "HIN", "TOK")) == sorted((n["tone"], n["who"], n["text"]) for n in NE["needs"] if KEY_OF.get(n.get("phone")) not in ("AUTO", "HSM", "TPLTXT"))),
        ("S14 the call-side figure (must-fix 3): the person whose MISSED CALL was followed by a WhatsApp at 'sent' is identical on both pages -- amber, "
         "'tried · not reached', no Needs-you line -- with and without the marks",
         lambda: st(OT, "MC") == st(NE, "MC") == st(NT, "MC") == ("amber", "tried · not reached")
         and not any(n.get("phone") == PH["MC"] for d in (OT, NE, NT) for n in d["needs"])),
        ("S7 the staff cards' CALL figures (answered, rung, missed, made, called back, net missed, not logged, staff ≠ AI, agreed, the duty line, every call on the card): identical with no marks",
         lambda: call_figs(NE) == call_figs(OT) and len(call_figs(NE)) >= 1 and call_figs(NY) == call_figs(OY)),
        ("S8 ... and with the marks they differ by ONE thing: the Not-a-patient number's missed call is off her card (rung 7 to 6, missed 4 to 3, "
         "net missed 3 to 2, missed patients 4 to 3, not called back 3 to 2); every other call figure and every call on the card is the same -- "
         "the call she answered from that number included",
         lambda: [x[:2] + x[4:7] + x[9:10] + x[11:17] for x in call_figs(NT)] == [x[:2] + x[4:7] + x[9:10] + x[11:17] for x in call_figs(OT)]
         and [(x[2], x[3], x[7], x[8], x[10]) for x in call_figs(OT) if x[0] == "shivani"] == [(7, 4, 3, 4, 3)]
         and [(x[2], x[3], x[7], x[8], x[10]) for x in call_figs(NT) if x[0] == "shivani"] == [(6, 3, 2, 3, 2)]
         and [x for x in call_figs(NT) if x[0] != "shivani"] == [x for x in call_figs(OT) if x[0] != "shivani"]),
        ("S9 the staff cards' WhatsApp figures: the base counted MESSAGES (49 on duty, 9 answered, 40 not); the kit counts CHATS (no marks 36 → 11, 25 awaiting; with the marks 33 → 11, 22)",
         lambda: wa_fig(card(OT, "shivani")) == (49, 9, 40) and wa_fig(card(NE, "shivani")) == (36, 11, 25) and wa_fig(card(NT, "shivani")) == (33, 11, 22)),
        ("S10 each person's own card as the staff app reads it: the call figures, every call row, the asks and notes identical (no marks); only 'WhatsApp aaye → jawab diye' changes",
         lambda: mine_calls(F0["mine_e"]["shivani"]) == mine_calls(F1["mine"]["shivani"]) and mine_calls(F0["mine_e"]["alisha_y"]) == mine_calls(F1["mine"]["alisha_y"])
         and set(F0["mine_e"]["shivani"]) == set(F1["mine"]["shivani"]) and set(F0["mine_e"]["shivani"]["figs"]) == set(F1["mine"]["shivani"]["figs"])),
        ("S11 the follow-up sections: every figure and every row identical, but for the ONE pill the kit means to change (the reply 'sent': 'Wrote back' no more)",
         lambda: fu_key(NT, skip=("FU2",)) == fu_key(OT, skip=("FU2",)) == fu_key(NE, skip=("FU2",)) and fu_row(OT, "FU2")["pill"] == "Wrote back · to call" and fu_row(OT, "FU1")["pill"] == "Wrote back · to call"),
        ("S12 Call ke baad, this week's unknown callers, earlier days: identical",
         lambda: NT["ckb"] == OT["ckb"] and NT["week"] == OT["week"] and NT["earlier"] == OT["earlier"]),
        ("S13 the page's HTML outside what the kit means to change: the follow-up, Call-ke-baad, unknown-callers and earlier-days sections byte-identical (no marks), bar the one pill's row",
         lambda: all(sect(F0["E"][1], s) == sect(F1["T"][1], s) for s in ("ckb", "unknown", "earlier"))
         and re.sub(r'<li class="fp">(?:(?!</li>).)*Test Fureplied.*?</li>', "", sect(F0["E"][1], "followups"), flags=re.S) == re.sub(r'<li class="fp">(?:(?!</li>).)*Test Fureplied.*?</li>', "", sect(F1["T"][1], "followups"), flags=re.S)),
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
MD = tempfile.mkdtemp(prefix="s818mut_")
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
shutil.rmtree(MD, ignore_errors=True)
STORES or shutil.rmtree(TMP, ignore_errors=True)
if bad == 0 and mut_red == len(MUTATIONS) and same_ok == same_n:
    print("WALK OK: %d of %d; %d of %d mutations red; other readers %s" % (n_ok, len(RES), mut_red, len(MUTATIONS),
                                                                         ("%d of %d as they must be against the base page" % (same_ok, same_n)) if BASE_DIR else "not compared (no base page given)"))
    sys.exit(0)
print("WALK RED: %d of %d; mutations red %d of %d; other readers %d of %d" % (n_ok, len(RES), mut_red, len(MUTATIONS), same_ok, same_n))
sys.exit(1)
