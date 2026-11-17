#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s853.py -- kit S853_PATIENTS_PART2 (S477, 17-Nov-2026). A walk on a MADE-UP root: made-up patients, made-up numbers
(90000000xx -- no real number), made-up call record, inbox, Review Assist store, history and Google files.

    python3 walk_s853.py <code_dir> <calls_console.py> <work_dir>

<code_dir>  the files under test (patients_page.py + patients_part2.py; or the live files for the CONTROL)
Prints one line per check and a last line "WALK n/m". Exit 0 only when every check passes."""
import datetime as dt
import hashlib
import json
import os
import shutil
import sqlite3
import sys

CODE, CC, WORK = sys.argv[1:4]
try:
    _ME = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _ME = None
sys.path[:] = [p for p in sys.path if not _ME or os.path.abspath(p or ".") != _ME]     # F-1441
sys.path[:0] = [CODE]
if os.path.isdir(WORK):
    shutil.rmtree(WORK)
os.makedirs(WORK)
RES = []


def ok(name, cond, extra=""):
    RES.append(bool(cond))
    print("%s  %s%s" % ("PASS" if cond else "FAIL", name, ("  -- " + str(extra)[:300]) if extra else ""))


P = lambda n: "90000000%02d" % n                                     # noqa: E731 -- made-up numbers
FIN = os.path.join(WORK, "finance.db")
CON = os.path.join(WORK, "console.db")
INB = os.path.join(WORK, "inbox.db")
GMB = os.path.join(WORK, "gmb_store.db")
HIS = os.path.join(WORK, "patients_history.json")
GOO = os.path.join(WORK, "patients_google.json")
os.environ.update(PATIENTS_READING=os.path.join(WORK, "reading.dat"), PATIENTS_CONSOLE_DB=CON, PATIENTS_INBOX_DB=INB,
                  PATIENTS_AWAIT_DB=os.path.join(WORK, "no_marks.db"), PATIENTS_GMB_DB=GMB, PATIENTS_HISTORY=HIS,
                  PATIENTS_GOOGLE=GOO, PATIENTS_CALLS_CONSOLE=CC)

# ------------------------------------------------------------------ the made-up finance record
f = sqlite3.connect(FIN)
f.executescript("CREATE TABLE patient_visit(visit_id INTEGER, visit_date TEXT, clinic_id TEXT, patient_uid TEXT);"
                "CREATE TABLE dx_visit(patient_uid TEXT, visit_date TEXT, clinic_id TEXT, diagnosis_raw TEXT, std_dx TEXT, category TEXT, follow_up_date TEXT);"
                "CREATE TABLE clinic_day_line(business_date TEXT, section TEXT, clinic_id TEXT, amount_p INTEGER);")
V = [  # uid, cid, day, category, follow-up
    ("uE", "7001", "2026-09-10", "Rheumatology", "2026-09-15"),
    ("uB", "7002", "2026-09-25", "Trauma", "2026-10-05"),
    ("uC", "7003", "2026-09-26", "Trauma", "2026-10-04"),
    ("uD", "7004", "2026-09-27", "Degenerative Joint Disease", "2026-10-07"),
    ("uD", "7004", "2026-10-08", "", ""),
    ("uA", "7005", "2026-10-20", "Rheumatology", "2026-11-03"),
    ("uA", "7005", "2026-11-04", "", ""),
    ("uF", "7006", "2026-11-10", "Trauma", "2026-11-20"),       # review 2: a follow-up still open -> not in the Called split
]
for i, (u, c, d, cat, fu) in enumerate(V):
    f.execute("INSERT INTO patient_visit VALUES (?,?,?,?)", (i + 1, d, c, u))
    if cat:
        f.execute("INSERT INTO dx_visit VALUES (?,?,?,?,?,?,?)", (u, d, c, "walk dx", cat, cat, fu))
    f.execute("INSERT INTO clinic_day_line VALUES (?,?,?,?)", (d, "consult", c, 50000))
f.commit()
f.close()

# ------------------------------------------------------------------ the made-up call record (console.db shape)
c = sqlite3.connect(CON)
c.executescript("""CREATE TABLE calls (id INTEGER PRIMARY KEY AUTOINCREMENT, client_ref_id TEXT, ref_id TEXT, session_id TEXT, category TEXT,
 status TEXT, direction TEXT, answered INTEGER, total_duration TEXT, customer_result TEXT, customer_talk_duration TEXT,
 customer_ring_duration TEXT, recording_filename TEXT, ended_at_ist TEXT, captured_at_ist TEXT, source_event TEXT, phone10 TEXT, join_key TEXT);
CREATE TABLE verdicts (id INTEGER PRIMARY KEY AUTOINCREMENT, join_key TEXT, ai_outcome TEXT);
CREATE TABLE patients (phone10 TEXT, name TEXT, diagnosis TEXT, age TEXT, gender TEXT, last_visit TEXT, patient_uid TEXT, clinic_id TEXT);""")
for ph, cid in ((P(1), "7005"), (P(2), "7002"), (P(3), "7003"), (P(4), "7006")):   # 7004 has no number (review 3)
    c.execute("INSERT INTO patients (phone10, name, clinic_id) VALUES (?,?,?)", (ph, "WALK", cid))


def call(ph, ts, d, ans, ai=""):
    t = dt.datetime.fromisoformat(ts)
    jk = "%s_%d" % (ph, int(t.replace(tzinfo=dt.timezone(dt.timedelta(hours=5, minutes=30))).timestamp()))
    end = t + dt.timedelta(seconds=60)
    c.execute("INSERT INTO calls (direction, answered, total_duration, customer_talk_duration, customer_ring_duration, ended_at_ist, phone10, join_key) "
              "VALUES (?,?,?,?,?,?,?,?)", (d, 1 if ans else 0, "60", "45" if ans else "0", "10", end.strftime("%Y-%m-%d %H:%M:%S"), ph, jk))
    if ai:
        c.execute("INSERT INTO verdicts (join_key, ai_outcome) VALUES (?,?)", (jk, ai))


U1, U2, U3, A, B, C3 = P(11), P(12), P(13), P(1), P(2), P(3)
call(U3, "2026-09-20 10:00:00", "Out", False)                  # the record begins 20-Sep
call(B, "2026-10-06 11:00:00", "Out", False)                   # B's follow-up (due 5-Oct) called
call(A, "2026-11-01 11:00:00", "Out", True)                    # A's follow-up (due 3-Nov) called
call(U1, "2026-11-03 10:00:00", "In", False)
call(U1, "2026-11-03 10:05:00", "In", True, "enquiry_only")    # rang again and got through
call(U2, "2026-11-03 08:30:00", "In", False)
call(U2, "2026-11-03 11:00:00", "Out", True, "coming")         # we called back and spoke
call(U3, "2026-11-03 12:00:00", "In", False)                   # never, no call-back
call(A, "2026-11-03 15:00:00", "In", True, "in_appointment_booked")   # first ring
call(B, "2026-11-03 16:00:00", "In", False)
call(B, "2026-11-05 10:00:00", "Out", True, "on_medication")   # reached on a later day
call(U1, "2026-11-08 11:00:00", "In", False)                   # a Sunday: never, but a call-back was tried
call(U1, "2026-11-08 11:10:00", "Out", False)
call(P(14), "2026-11-14 10:00:00", "In", False)                # review 1: missed 3 days ago -> not reached YET, not "never"
c.commit()
c.close()

# ------------------------------------------------------------------ the made-up WhatsApp inbox
w = sqlite3.connect(INB)
w.execute("CREATE TABLE msgs (rid INTEGER PRIMARY KEY, mid TEXT, phone TEXT, dir TEXT, ts TEXT, mtype TEXT, body TEXT, status TEXT, sent_by TEXT, src TEXT)")
W1, W2 = P(21), P(22)
for ph, d, ts, mt, body, st, by in ((W1, "in", "2026-11-04 10:00:00", "text", "hi", "", ""),
                                    (W1, "out", "2026-11-04 10:30:00", "text", "Please call", "delivered", "alisha"),
                                    (W2, "in", "2026-11-06 09:00:00", "image", "", "", ""),
                                    (A, "in", "2026-11-07 12:00:00", "text", "time kya hai", "", ""),
                                    (A, "out", "2026-11-07 12:10:00", "text", "10 baje", "retrying", "alisha")):
    w.execute("INSERT INTO msgs (mid, phone, dir, ts, mtype, body, status, sent_by, src) VALUES ('',?,?,?,?,?,?,?,'')", (ph, d, ts, mt, body, st, by))
w.commit()
w.close()

# ------------------------------------------------------------------ the made-up Review Assist store
g = sqlite3.connect(GMB)
g.executescript("CREATE TABLE press(id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, who TEXT, lang TEXT, relation TEXT, state TEXT, d0 TEXT, d1 TEXT, d2 TEXT, kit TEXT);"
                "CREATE TABLE share(id INTEGER PRIMARY KEY AUTOINCREMENT, press_id INTEGER, at TEXT, who TEXT, which INTEGER, how TEXT, text TEXT, edited INTEGER);"
                "CREATE TABLE snapshot(id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, who TEXT, taken_on TEXT, data TEXT, kit TEXT);")
g.execute("INSERT INTO snapshot (at, who, taken_on, data, kit) VALUES ('x','d','2026-10-20',?, 'w')", (json.dumps(dict(ours_n=160, ours_low_pct=9, themes=[])),))
g.execute("INSERT INTO snapshot (at, who, taken_on, data, kit) VALUES ('x','d','2026-11-05',?, 'w')", (json.dumps(dict(
    ours_n=167, ours_low_pct=9, themes=[dict(name="Staff tone", ours=6.6, **{"else": 8.2}), dict(name="X-ray and test charges", ours=4.8, **{"else": 2.1})])),))
g.execute("INSERT INTO press (at, who, state, kit) VALUES ('2026-11-06T10:00:00','doctor','{}','w')")
g.execute("INSERT INTO press (at, who, state, kit) VALUES ('2026-11-06T11:00:00','doctor','{}','w')")
g.execute("INSERT INTO share (press_id, at, who, which, how, text, edited) VALUES (1,'x','doctor',0,'shared','t',0)")
g.commit()
g.close()

json.dump(dict(source="walk", months={"2025-10": dict(patients=4, new=2, visits=6, days=3, vpd=2.0, consult=80000, xray=None, proc=None, review_kept_num=None),
                                       "2025-11": dict(patients=5, new=2, visits=9, days=3, vpd=3.0, consult=100000, xray=None, proc=None, review_kept_num=50)},
               range=dict(review_kept=dict(lo=30, hi=60, p25=40, p75=55, n=18)), final={"Rheumatology": dict(n=30, kept=15, within=6, later=3, never=6)},
               late_full={}), open(HIS, "w"))
json.dump(dict(months={"2026-09": dict(searches=100, views=500, calls=20, directions=20, chats=2, website=1, interactions=41, yoy={}),
                       "2026-10": dict(searches=90, views=450, calls=15, directions=10, chats=3, website=2, interactions=27,
                                       yoy=dict(calls=16.4, directions=25.3, actions=19.9, views=1.6, searches=1.1))},
               top_terms="walk", closed_days="walk"), open(GOO, "w"))


class Z(dict):
    """A missing key reads as an empty Z (the CONTROL prints its red count instead of stopping)."""
    def __missing__(self, k):
        return Z()


def z(d):
    return Z({k: (Z(v) if isinstance(v, dict) else v) for k, v in (d or {}).items()})


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


before = {p: md5(p) for p in (FIN, CON, INB, GMB)}

import patients_page as pp                                              # noqa: E402
con = sqlite3.connect("file:%s?mode=ro" % FIN, uri=True)
reading, lists = pp.read(con, today=dt.date(2026, 11, 17))
p2 = reading.get("p2") or {}
ok("Part 1 still reads (months Jul..Nov)", reading.get("ok") and [m["ym"] for m in reading["months"]] == ["2026-07", "2026-08", "2026-09", "2026-10", "2026-11"])
ok("Part 2 present and ok", p2.get("ok") is True and p2.get("version") == "S853 1.0", p2.get("why"))
dk = (p2.get("desk") or {})
ok("front desk read", dk.get("ok") is True and dk.get("wa_ok") is True, dk.get("why"))
N = (dk.get("months") or {}).get("2026-11") or {}
rows = {r["key"]: r for r in N.get("calls", [])}
a = rows.get("all", {})
ok("caller-days all: 7 = first 1, again 1, back 1, later 1, never 2, not yet 1", (a.get("n"), a.get("first"), a.get("again"), a.get("back"), a.get("later"), a.get("never"), a.get("open")) == (7, 1, 1, 1, 1, 2, 1), a)
ok("no call-back on record: 1 (the Sunday caller was rung back, unanswered)", a.get("nocb") == 1, a.get("nocb"))
u, pt = rows.get("unk", {}), rows.get("pat", {})
ok("unknown numbers: 5 caller-days (again 1, back 1, never 2, not yet 1)", (u.get("n"), u.get("again"), u.get("back"), u.get("never"), u.get("open")) == (5, 1, 1, 2, 1), u)
ok("your patients: 2 caller-days (first 1, later 1)", (pt.get("n"), pt.get("first"), pt.get("later")) == (2, 1, 1), pt)
H = z({h["label"]: h for h in N.get("hours", [])})
ok("hours: before 9 = 0 answered / 1 missed", (H.get("Before 9 a.m.", {}).get("ans"), H.get("Before 9 a.m.", {}).get("miss")) == (0, 1))
ok("hours: 9 to 11 = 1 / 2; 2 to 5 = 1 / 1; Sundays 0 / 1", (H["9 to 11"]["ans"], H["9 to 11"]["miss"], H["2 to 5"]["ans"], H["2 to 5"]["miss"],
                                                             H["Sundays (all day)"]["ans"], H["Sundays (all day)"]["miss"]) == (1, 2, 1, 1, 0, 1))
AB = z({r["label"]: r for r in N.get("about", [])})
ok("verdicts: unknown incoming 1 enquiry; patients incoming 1 booked", (AB["Incoming — unknown numbers"]["n"], AB["Incoming — unknown numbers"]["enq"],
                                                                     AB["Incoming — your patients"]["n"], AB["Incoming — your patients"]["booked"]) == (1, 1, 1, 1))
ok("verdicts: outgoing 2 (1 coming, 'on medicines 1' among the others)", AB["Outgoing calls that were answered"]["n"] == 2 and
   AB["Outgoing calls that were answered"]["booked"] == 1 and "on medicines 1" in str(AB["Outgoing calls that were answered"].get("other", "")), AB["Outgoing calls that were answered"])
WA = z({r["key"]: r for r in N.get("wa", [])})
ok("WhatsApp senders: 3 = answered 1, tried 1, nothing 1", (WA["all"]["n"], WA["all"]["ans"], WA["all"]["tried"], WA["all"]["nothing"]) == (3, 1, 1, 1), WA.get("all"))
ok("WhatsApp: unknown 2 (answered 1, nothing 1); patients 1 (tried)", (WA["unk"]["n"], WA["unk"]["ans"], WA["unk"]["nothing"], WA["pat"]["n"], WA["pat"]["tried"]) == (2, 1, 1, 1, 1))
T = z({t["label"]: t for t in N.get("tiles", [])})
ok("tile: 8 people contacted the clinic", T["People who contacted the clinic"]["value"] == "8", T["People who contacted the clinic"])
ok("tile: 6 from numbers not in the list", T["From numbers not in your list"]["value"] == "6")
ok("tile: never reached 2, the not-yet one named apart", T["Callers never reached"]["value"] == "2" and "1 of the last 7 days not reached yet" in str(T["Callers never reached"].get("sub")), T["Callers never reached"])
ok("tile: wrote on WhatsApp, never rang = 2 (1 with nothing)", T["Wrote on WhatsApp, never rang"]["value"] == "2" and str(T["Wrote on WhatsApp, never rang"].get("sub", "")).startswith("1 "))
wm = {r["ym"]: r for r in dk.get("wa_months", [])}
x = wm.get("2026-11", {})
ok("WhatsApp month Nov: 3 people, 2 unknown, 3 conversations, hi 1, photo 1, asked time 1, 1 reply, 0 failed",
   (x.get("people"), x.get("unk"), x.get("convs"), x.get("greet"), x.get("media"), x.get("askt"), x.get("replies"), x.get("failed")) == (3, 2, 3, 1, 1, 1, 1, 0), x)
ok("WhatsApp months from September", sorted(wm) == ["2026-09", "2026-10", "2026-11"])
cl = p2.get("called") or {}
r10 = (cl.get("rows") or {}).get("2026-10:review") or {}
ok("Called, reviews due Oct: 2 = called 1 (B), not 1 (C); D has no number -> left out", (r10.get("n"), r10.get("called"), r10.get("not_"), r10.get("nophone")) == (2, 1, 1, 1), r10)
ok("Called, kept: called 0 of 1, not called 0 of 1", (r10.get("kept_called"), r10.get("kept_not")) == ("0 of 1", "0 of 1"), r10)
r11 = (cl.get("rows") or {}).get("2026-11:review") or {}
ok("Called, reviews due Nov: A called and kept; F still open -> not yet", (r11.get("n"), r11.get("called"), r11.get("notyet")) == (1, 1, 1), r11)
r9 = (cl.get("rows") or {}).get("2026-09:short") or {}
ok("Called: a follow-up before the call record is left out (unknown 1)", (r9.get("n"), r9.get("unknown")) == (0, 1), r9)
gr = (cl.get("groups") or {}).get("2026-10:Trauma") or {}
ok("Of the missed, Trauma Oct: called 1 of 2", (gr.get("missed"), gr.get("called")) == (2, 1), gr)
ok("the called list carries clinic IDs only", [r[0] for r in lists.get("fuc:2026-10:review:called", [])] == ["7002"], lists.get("fuc:2026-10:review:called"))
gg = p2.get("google") or {}
gr2 = z({r["ym"]: r for r in gg.get("rows", [])})
ok("Google: new patients beside, per 10 directions (Sep 4 -> 2.0, Oct 1 -> 1.0)", (gr2["2026-09"]["new"], gr2["2026-09"]["per10"], gr2["2026-10"]["new"], gr2["2026-10"]["per10"]) == (4, 2.0, 1, 1.0), gr2)
ok("Google: Oct new patients vs last year -50% (1 against 2)", (gr2["2026-10"]["new_ly"], gr2["2026-10"]["new_yoy"]) == (2, -50))
hb = p2.get("history") or {}
ok("history: Nov against Nov-2025", (hb.get("ly") or {}).get("2026-11", {}).get("visits") == 9 and "2026-07" not in (hb.get("ly") or {}))
rv = p2.get("reviews") or {}
ok("reviews: 167 reviewers, 7 new since 20-Oct, 2 themes with where to look", rv.get("last", {}).get("ours_n") == 167 and rv.get("new_since") == 7
   and [t.get("look") != "" for t in rv.get("themes", [])] == [True, True], rv)
ok("reviews: Nov 2 drafts, 1 shared, 100 per 100 patients (2 patients)", rv.get("months", {}).get("2026-11") == dict(drafts=2, shared=1, per100=100.0), rv.get("months", {}).get("2026-11"))
heads = [x["head"] for x in reading["readings"]["2026-10"]]
import patients_page as _pp_  # noqa
ok("Oct lines: Google first (both fell -> the season), then Part 1's", heads and heads[0] == "Google and the clinic door" and "Who came" in heads, heads)
gl = z(reading["readings"]["2026-10"][0])
ok("the Google line reads the season", "season" in str(gl.get("sug", "")) and "-50%" in str(gl.get("text", "")).replace("−", "-"), gl)
h11 = [x["head"] for x in reading["readings"]["2026-11"]]
ok("Nov lines: last year + reviews added", "Against the same month last year" in h11 and "Good reviews follow your asks, not the month" in h11, h11)
ly11 = z(next((x for x in reading["readings"]["2026-11"] if x["head"] == "Against the same month last year"), {}))
ok("a part month is compared per open day only (review 6)", "so far" in str(ly11.get("text")) and "new patients a day" in str(ly11.get("text")), ly11.get("text"))
ok("Part 2's own build time is kept", isinstance(p2.get("took"), (int, float)))
ok("nothing written to any store", {p: md5(p) for p in before} == before)
# review 5 / 7: a bad stored row and a null field cost only themselves
g = sqlite3.connect(GMB)
g.execute("INSERT INTO snapshot (at, who, taken_on, data, kit) VALUES ('x','d','2026-11-06','{not json', 'w')")
g.execute("INSERT INTO snapshot (at, who, taken_on, data, kit) VALUES ('x','d','2026-11-07',?, 'w')", (json.dumps(dict(ours_n=None, ours_low_pct=None, themes=[])),))
g.commit()
g.close()
G2 = json.load(open(GOO))
G2["months"]["2026-10"]["yoy"] = dict(calls=None, directions=None)
json.dump(G2, open(GOO, "w"))
reading3, _l3 = pp.read(con, today=dt.date(2026, 11, 17))
q3 = z(reading3.get("p2"))
ok("a bad snapshot row and a null count: the reviews block still reads", q3["reviews"].get("ok") is True, q3["reviews"])
ok("a null year-on-year: the Google line still drawn, without the comparison",
   any(x["head"] == "Google and the clinic door" and "2025" not in x["text"] for x in reading3["readings"]["2026-10"]))
# a store that cannot be read: Part 2 says so, Part 1 stands
os.environ["PATIENTS_CONSOLE_DB"] = os.path.join(WORK, "missing.db")
import importlib                                                        # noqa: E402
try:
    import patients_part2                                               # noqa: E402
    importlib.reload(patients_part2)
except ImportError:
    pass
reading2, _l2 = pp.read(con, today=dt.date(2026, 11, 17))
q2 = z(reading2.get("p2"))
ok("missing call record: desk and called say so, the rest stands", q2["desk"].get("ok") is False and q2["called"].get("ok") is False
   and q2["reviews"].get("ok") is True and reading2["rows"] == reading["rows"])
print("WALK %d/%d" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
