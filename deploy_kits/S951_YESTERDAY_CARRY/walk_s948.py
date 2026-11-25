#!/usr/bin/env python3
"""walk_s948.py -- S948_STAFF_CONSOLE: the walk on a MADE-UP console.db + inbox.db (every number 500000xxxx).

  python walk_s948.py dump <code dir> <out file>      the owner's page + his ?as= card, as HTML/JSON, for the byte compare
  python walk_s948.py walk <code dir>                 every check per role; exit 0 only when all pass

<code dir> holds calls_console.py (+ calls_staff.py for the TO side), ring_outcome.py and ring_common.py from the bundle.
Nothing here reads a real store: every path is a temp file made below.
"""
import datetime as _dt
import json
import os
import sqlite3
import sys
import tempfile
import types
from functools import wraps

NOW = _dt.datetime(2026, 11, 24, 11, 30, 0)
TODAY = NOW.date().isoformat()
IST = _dt.timezone(_dt.timedelta(hours=5, minutes=30))


def ph(n):
    return "500000%04d" % n


def unix(hm, day=TODAY):
    t = _dt.datetime.strptime(day + " " + hm, "%Y-%m-%d %H:%M").replace(tzinfo=IST)
    return int(t.timestamp())


def make_fixture(root):
    con_p, inbox_p = os.path.join(root, "console.db"), os.path.join(root, "inbox.db")
    sys.path.insert(0, CODE)
    c = sqlite3.connect(con_p)
    c.executescript(SCHEMA)
    pats = [(1, "Ram Alpha", "Knee pain", "2026-11-09", "101"), (2, "Kamla Beta", "Fracture wrist", "", "102"),
            (3, "Arif Gamma", "Back pain", "", "103"), (4, "Sunil <script>alert(1)</script>", "", "", "104"), (5, "Pooja Eps", "Ankle", "", "105"),
            (6, "Geeta Zeta", "", "", "106"), (7, "Rakesh Eta", "Knee", "", "107"), (8, "Sunita Theta", "Back pain", "", "108"),
            (9, "Reached Iota", "Shoulder", "", "109"), (10, "Wrote Kappa", "Hip", "", "110"), (11, "Both Lambda", "Neck", "", "111")]
    for n, name, dx, lv, cid in pats:
        c.execute("INSERT INTO patients (phone10,name,diagnosis,age,gender,last_visit,patient_uid,clinic_id) VALUES (?,?,?,?,?,?,?,?)",
                  (ph(n), name, dx, "40", "M", lv, "", cid))
    d = _dt.date.fromisoformat(TODAY)

    def dd(k):
        return (d - _dt.timedelta(days=k)).isoformat()
    fu = [(1, "Due Today", 0), (2, "Due Today", 0), (3, "Grace Period", 2), (4, "Actionable Missed Follow-Up", 6),
          (5, "Probable Dropout", 20), (6, "Due Today", 0), (9, "Due Today", 0), (10, "Due Today", 0), (11, "Due Today", 0)]
    c.execute("CREATE TABLE fu_all (key TEXT, section TEXT, name TEXT, phone10 TEXT, dx TEXT, due_date TEXT, od TEXT, status_raw TEXT)")
    for n, sec, k in fu:
        c.execute("INSERT INTO fu_all VALUES (?,?,?,?,?,?,?,?)", ("k%d" % n, sec, "", ph(n), "", dd(k), "", ""))
    c.execute("INSERT INTO meta VALUES ('fu_all', ?)", (json.dumps({"found": True}),))
    c.execute("CREATE TABLE call_agent (join_key TEXT PRIMARY KEY, agent TEXT)")
    calls = [  # (phone n, direction, answered, hm, ring, dur, agent, ai)
        (2, "Out", 0, "10:05", 20, 25, "Shivani Test", ""),
        (5, "Out", 0, "09:20", 0, 3, "Shivani Test", ""),
        (5, "Out", 0, "10:20", 15, 20, "Alisha Test", ""),
        (6, "Out", 0, "09:00", 10, 12, "Shivani Test", ""), (6, "Out", 0, "10:00", 10, 12, "Shivani Test", ""),
        (6, "Out", 0, "11:00", 10, 12, "Shivani Test", ""),
        (9, "Out", 1, "10:30", 5, 192, "Shivani Test", "coming"),
        (7, "In", 0, "10:55", 9, 9, "", ""), (7, "In", 0, "11:01", 9, 9, "", ""),
        (11, "In", 0, "09:00", 7, 7, "", ""),
        (2001, "In", 0, "10:42", 8, 8, "", ""),
        (2002, "In", 0, "09:40", 8, 8, "", ""), (2002, "Out", 0, "10:12", 0, 2, "Shivani Test", ""),
        (8, "In", 1, "08:30", 5, 65, "Alisha Test", "enquiry_only"),
        (2003, "In", 0, "10:00", 6, 6, "", ""),
        (2004, "Out", 1, "09:10", 4, 50, "Shivani Test", "call_again"),
        (2005, "In", 0, "10:45", 6, 6, "", ""),
    ]
    for i, (n, dr, a, hm, ring, dur, agent, ai) in enumerate(calls):
        jk = "%s_%d" % (ph(n), unix(hm))
        end = (_dt.datetime.strptime(TODAY + " " + hm, "%Y-%m-%d %H:%M") + _dt.timedelta(seconds=dur)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO calls (status,direction,answered,total_duration,customer_talk_duration,customer_ring_duration,"
                  "recording_filename,ended_at_ist,phone10,join_key,client_ref_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  ("bridged" if a else "missed", dr, a, str(dur), str(max(0, dur - ring)) if a else "0", str(ring), "",
                   end, ph(n), jk, ""))
        if agent:
            c.execute("INSERT INTO call_agent VALUES (?,?)", (jk, agent))
        if ai:
            c.execute("INSERT INTO verdicts (join_key,agent,patient_name,clinic_id,claimed_outcome,ai_outcome,verdict) "
                      "VALUES (?,?,?,?,?,?,?)", (jk, agent, "", "", "", ai, "No claim logged"))
            c.execute("INSERT INTO recordings VALUES (?,?,?,?)", ("f.mp3", jk, "https://example.invalid/x", ""))
    c.commit()
    c.close()
    i = sqlite3.connect(inbox_p)
    i.executescript("CREATE TABLE msgs(rid INTEGER PRIMARY KEY AUTOINCREMENT, mid TEXT UNIQUE, phone TEXT NOT NULL, dir TEXT NOT NULL,"
                    " ts TEXT NOT NULL, mtype TEXT, body TEXT, media_url TEXT, mime TEXT, fname TEXT, local_path TEXT,"
                    " status TEXT, sent_by TEXT, src TEXT);")
    i.execute("INSERT INTO msgs (mid,phone,dir,ts,mtype,body,status,sent_by,src) VALUES (?,?,?,?,?,?,?,?,?)",
              ("m10a", ph(10), "in", TODAY + " 11:00:00", "text", "Kal aa sakte hain kya? Dard kam nahi hua", "", "", ""))
    i.execute("INSERT INTO msgs (mid,phone,dir,ts,mtype,body,status,sent_by,src) VALUES (?,?,?,?,?,?,?,?,?)",
              ("m2003", ph(2003), "in", TODAY + " 10:30:00", "text", "Missed call kiya tha", "", "", ""))
    i.execute("INSERT INTO msgs (mid,phone,dir,ts,mtype,body,status,sent_by,src) VALUES (?,?,?,?,?,?,?,?,?)",
              ("m2005a", ph(2005), "in", TODAY + " 09:00:00", "text", "Report kab milegi", "", "", ""))
    i.execute("INSERT INTO msgs (mid,phone,dir,ts,mtype,body,status,sent_by,src) VALUES (?,?,?,?,?,?,?,?,?)",
              ("m2005b", ph(2005), "out", TODAY + " 09:20:00", "text", "Kal tak", "delivered", "shivani", ""))
    i.execute("INSERT INTO msgs (mid,phone,dir,ts,mtype,body,status,sent_by,src) VALUES (?,?,?,?,?,?,?,?,?)",
              ("m1a", ph(1), "in", (d - _dt.timedelta(days=2)).isoformat() + " 09:00:00", "text", "Report bhej diya", "", "", ""))
    i.execute("INSERT INTO msgs (mid,phone,dir,ts,mtype,body,status,sent_by,src) VALUES (?,?,?,?,?,?,?,?,?)",
              ("m1b", ph(1), "out", (d - _dt.timedelta(days=2)).isoformat() + " 09:30:00", "text", "Mil gaya", "delivered", "shivani", ""))
    i.commit()
    i.close()
    with open(os.path.join(root, "staff_master.csv"), "w") as fh:
        fh.write("user_id,name,wd_start,wd_end,sun_start,sun_end,active\n1,Shivani Test,08:00,20:00,,,Y\n2,Alisha Test,08:00,20:00,,,Y\n")
    with open(os.path.join(root, "punches.csv"), "w") as fh:
        fh.write("user_id,datetime\n1,%s 08:00:00\n2,%s 08:05:00\n" % (TODAY, TODAY))
    return con_p, inbox_p


SCHEMA = """
CREATE TABLE calls (id INTEGER PRIMARY KEY AUTOINCREMENT, client_ref_id TEXT, ref_id TEXT, session_id TEXT, category TEXT,
  status TEXT, direction TEXT, answered INTEGER, total_duration TEXT, customer_result TEXT, customer_talk_duration TEXT,
  customer_ring_duration TEXT, recording_filename TEXT, ended_at_ist TEXT, captured_at_ist TEXT, source_event TEXT,
  phone10 TEXT, join_key TEXT);
CREATE TABLE verdicts (id INTEGER PRIMARY KEY AUTOINCREMENT, join_key TEXT, date TEXT, time TEXT, direction TEXT,
  patient_number TEXT, agent TEXT, patient_name TEXT, clinic_id TEXT, duration TEXT, claimed_outcome TEXT, not_filed INTEGER,
  ai_outcome TEXT, verdict TEXT, ai_reason TEXT, evidence TEXT, match_confidence TEXT, outcome_tf TEXT, spoke_with TEXT,
  flag_postop TEXT, flag_complaint TEXT, flag_urgent TEXT, flag_surgery TEXT, flag_clinical TEXT, flag_conduct TEXT,
  conduct_note TEXT, recording_link TEXT, transcript_link TEXT, status TEXT, error TEXT, judged_at TEXT, prompt_ver TEXT,
  model TEXT, doctor_flag TEXT, doctor_note TEXT, final_outcome TEXT);
CREATE TABLE recordings (myoperator_filename TEXT, join_key TEXT, recording_link TEXT, drive_file_id TEXT);
CREATE TABLE transcripts (join_key TEXT, transcribed_at TEXT, text TEXT, drive_file_id TEXT);
CREATE TABLE patients (phone10 TEXT, name TEXT, diagnosis TEXT, age TEXT, gender TEXT, last_visit TEXT, patient_uid TEXT, clinic_id TEXT);
CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT);
"""


def build_app(root, con_p, inbox_p, now):
    from flask import Flask, request, redirect, abort
    pm = types.ModuleType("fakeportal_s948")
    sys.modules["fakeportal_s948"] = pm

    def _sso_user(req):
        u = req.headers.get("X-Test-User")
        return {"user": u, "role": req.headers.get("X-Test-Role", "staff")} if u else None

    def login_required(view):
        @wraps(view)
        def w(*a, **k):
            if _sso_user(request) is None:
                return redirect("/portal/login")
            return view(*a, **k)
        return w

    def _is_doctor(req):
        return (_sso_user(req) or {}).get("role") == "doctor"

    def doctor_required(view):
        @wraps(view)
        def w(*a, **k):
            if _sso_user(request) is None:
                return redirect("/portal/login")
            if not _is_doctor(request):
                abort(403)
            return view(*a, **k)
        return w

    def _is_wa_user(req):
        return (_sso_user(req) or {}).get("user") in ("manoj", "shivani")

    def _serve_rec(jk):
        return "REC " + jk
    login_required.__module__ = doctor_required.__module__ = "fakeportal_s948"
    pm.login_required, pm.doctor_required, pm._sso_user, pm._is_doctor = login_required, doctor_required, _sso_user, _is_doctor
    pm._is_wa_user, pm._serve_rec = _is_wa_user, _serve_rec
    pm.TILES = [{"name": "System Board", "group": "System", "roles": ["doctor"]},
                {"icon": "X", "name": "Call Console", "group": "Calls & WhatsApp", "roles": ["doctor"], "url": "/portal/console"},
                {"name": "Call Tracker", "group": "Calls & WhatsApp", "roles": ["doctor"]}]
    pm._TILE_GROUP = {t["name"]: t["group"] for t in pm.TILES}
    import calls_console as cc
    real_now = cc.now_ist
    cc.now_ist = lambda n=None: n if n is not None else now
    cfg = {"PORTAL_INBOX_DB": inbox_p, "PORTAL_CALL_REVIEW_DB": os.path.join(root, "call_review.db"),
           "PORTAL_WA_AWAITING_DB": os.path.join(root, "wa_awaiting.db"), "SR_STAFF_MASTER": os.path.join(root, "staff_master.csv"),
           "SR_PUNCH_CSV": os.path.join(root, "punches.csv"), "FINANCE_DB_PATH": os.path.join(root, "no_finance.db"),
           "PORTAL_PHONE_STAFF": "shivani,alisha", "PORTAL_WA_ENV": os.path.join(root, "no.env")}

    def cfg_get(k, default=""):
        return cfg.get(k, default)

    def conn():
        x = sqlite3.connect("file:%s?mode=ro" % con_p, uri=True)
        x.row_factory = sqlite3.Row
        return x
    app = Flask("walk_s948")
    built = now - _dt.timedelta(minutes=5)
    cc.register(app, doctor_required, lambda: ((_sso_user(request) or {}).get("user") or "manoj"), cfg_get,
                {"console_conn": conn, "console_meta": lambda: {"ok": True, "built_at": built.strftime("%Y-%m-%d %H:%M:%S")},
                 "reviews_maps": lambda: ({}, {}), "spam_phones": lambda: []})
    cc._CARD_CACHE.clear()
    return app, cc, pm, real_now


def H(user, role="staff", post=False):
    h = {"X-Test-User": user, "X-Test-Role": role} if user else {}
    if post:
        h["X-Staff-Console"] = "1"
    return h


def do_dump(out):
    root = tempfile.mkdtemp(prefix="s948d_")
    con_p, inbox_p = make_fixture(root)
    res = []
    for hm in ("11:30", "16:30"):
        now = _dt.datetime.strptime(TODAY + " " + hm, "%Y-%m-%d %H:%M")
        app, cc, pm, _ = build_app(root, con_p, inbox_p, now)
        cl = app.test_client()
        r = cl.get("/portal/console", headers=H("manoj", "doctor"))
        res.append(("page " + hm, r.status_code, r.get_data()))
        for who in ("shivani", "alisha"):
            r = cl.get("/portal/console/api/card/%s?span=today" % who, headers=H("manoj", "doctor"))
            res.append(("card " + who + " " + hm, r.status_code, r.get_data()))
        for m in [m for m in list(sys.modules) if m in ("calls_console", "calls_staff", "ring_outcome", "ring_common")]:
            del sys.modules[m]
    with open(out, "wb") as fh:
        for name, st, b in res:
            fh.write(("== %s %s %d\n" % (name, st, len(b))).encode())
            fh.write(b + b"\n")
    print("dumped", len(res), "parts")


FAILS = []
N = [0]


def ok(cond, what):
    N[0] += 1
    print(("  ok   " if cond else "  FAIL ") + what)
    if not cond:
        FAILS.append(what)


def phones(lst):
    return [r["phone"] for r in lst]


def do_walk():
    root = tempfile.mkdtemp(prefix="s948w_")
    con_p, inbox_p = make_fixture(root)
    app, cc, pm, _ = build_app(root, con_p, inbox_p, NOW)
    global CC_FMT
    CC_FMT = cc.fmt_num
    cl = app.test_client()
    called = []
    cc.ivr_call = lambda p, login, **k: (called.append((p, login)) or (True, "Your phone is ringing", 200))
    print("[1] gates")
    ok(cl.get("/portal/console/staff").status_code == 302, "signed out -> sent to the login")
    ok(cl.get("/portal/console/staff", headers=H("bhawna")).status_code == 403, "a login not on the list -> 403")
    ok(cl.get("/portal/console/staff/api/lists", headers=H("bhawna")).status_code == 403, "its data route too -> 403")
    r = cl.get("/portal/console/staff", headers=H("manoj", "doctor"))
    t = r.get_data(as_text=True)
    ok(r.status_code == 200 and all(("?as=" + k) in t for k in ("shivani", "alisha", "shavez")), "the doctor: a picker of the three")
    ok(cl.get("/portal/console/staff?as=bhawna", headers=H("manoj", "doctor")).status_code == 404, "the doctor ?as= a login not on the list -> 404")
    r = cl.get("/portal/console/staff?as=shivani", headers=H("manoj", "doctor"))
    t = r.get_data(as_text=True)
    ok(r.status_code == 200 and "seeing Shivani" in t and "Wrong?" not in t and ">Recording<" not in t,
       "the doctor ?as=shivani: her page, no Wrong? and no Recording")
    ok(cl.get("/portal/console/staff", headers=H("shavez")).status_code == 200, "Shavez (the extra login) -> 200")
    print("[2] the lists at 11:30 (shivani)")
    r = cl.get("/portal/console/staff/api/lists", headers=H("shivani"))
    d = r.get_json()
    T = d["tabs"]
    ok(r.status_code == 200 and r.headers.get("Cache-Control") == "no-store", "lists 200, no-store")
    ok(phones(T["due"]) == [ph(1), ph(3), ph(4)], "Follow-ups due = Due Today, Grace, Actionable, in that order: %s" % [p[-4:] for p in phones(T["due"])])
    ok("Due Today" in T["due"][0]["sub"] and "last visit 09-Nov" in T["due"][0]["sub"], "row line: section + last visit")
    ok("Grace Period" in T["due"][1]["sub"] and "2 days" in T["due"][1]["sub"], "grace row: '2 days'")
    ok(sorted(phones(T["again"])) == sorted([ph(2), ph(2002)]), "Call again = one attempt (follow-up + missed caller)")
    a2 = next(x for x in T["again"] if x["phone"] == ph(2))
    ok(a2["sub"] == "1 attempt · 10:05 No answer · follow-up" and not a2["hi"], "call-again line, not yet due at 11:30")
    a3 = next(x for x in T["again"] if x["phone"] == ph(2002))
    ok("Incoming missed (09:40)" in a3["sub"] and "call back 10:12 Switched off" in a3["sub"], "missed caller tried once, rang 0 s -> Switched off")
    ok(phones(T["eve"]) == [ph(5)] and "2 attempts (09:20, 10:20)" in T["eve"][0]["sub"], "Evening = two attempts")
    ok(phones(T["missed"]) == [ph(11), ph(2001), ph(2005), ph(7)], "Incoming missed, earliest first: %s" % [p[-4:] for p in phones(T["missed"])])
    m7 = next(x for x in T["missed"] if x["phone"] == ph(7))
    ok(m7["sub"].startswith("Incoming missed 2 (10:55, 11:01)"), "two misses: 'Incoming missed 2 (10:55, 11:01)'")
    u1 = next(x for x in T["missed"] if x["phone"] == ph(2001))
    ok(u1["name"] == "New number" and "not an existing patient" in u1["sub"], "unknown number: New number, not an existing patient")
    every = [p for k in ("due", "again", "eve", "missed") for p in phones(T[k])]
    ok(ph(9) not in every, "reached today -> on no call list")
    ok(ph(6) not in every, "three unanswered attempts -> done for the day")
    ok(ph(10) not in every and phones(T["wa"]) == [ph(2003), ph(10)], "wrote on WhatsApp today -> WhatsApp tab only (longest wait first)")
    ok(ph(2003) not in every, "a missed caller who then wrote on WhatsApp -> WhatsApp tab only")
    ok(ph(2005) in phones(T["missed"]) and ph(2005) not in phones(T["wa"]), "a WhatsApp answered BEFORE the missed call -> still Incoming missed")
    ok(every.count(ph(11)) == 1 and ph(11) in phones(T["missed"]), "follow-up AND missed caller -> once, on the missed path")
    ok(len(every) == len(set(every)), "no number twice across the call tabs")
    ok(phones(T["mine"]) == [ph(9), ph(2004)] and T["mine"][0]["verdict"] == "Coming" and T["mine"][1]["can_dispute"] and T["mine"][0]["can_dispute"]
       and T["mine"][0]["jk"], "Handled today = her own answered call, Call verdict 'Coming', recording")
    ok("3 min 12 s" in T["mine"][0]["sub"] and "follow-up" in T["mine"][0]["sub"], "her call line: length + follow-up")
    ok(not d["evening"] and d["built_h"] == "11:25" and not d["old"], "the bar: updated 11:25, not old")
    da = cl.get("/portal/console/staff/api/lists", headers=H("alisha")).get_json()
    ok(phones(da["tabs"]["mine"]) == [ph(8)], "Alisha's Handled today is hers alone")
    ok(da["tabs"]["due"] == T["due"], "the work lists are the same for both")
    print("[3] the page")
    t = cl.get("/portal/console/staff", headers=H("shivani")).get_data(as_text=True)
    ok(CC_FMT(ph(1)) in t and CC_FMT(ph(1)) == "50000 00001", "FULL mobile numbers on the page (D1060)")
    ok("Follow-ups due 3<" in t and "Call again 2<" in t and "Incoming missed 4<" in t and "WhatsApp 2<" in t and "Handled today 2<" in t,
       "tab counts")
    ok("Evening calls 1" not in t and "These are called from 4pm to 6pm" in t, "before 16:00 the Evening count is not shown")
    ok("Call verdict: Coming" in t and "Wrong?" in t and ">Recording<" in t, "Call verdict, Wrong?, Recording")
    ok("/portal/inbox?m=m10a" in t and "/portal/inbox?m=m1b" in t, "Reply / Chat open the inbox chat (a WhatsApp user)")
    ok("AI reading" not in t and "transcript" not in t.lower().replace("no transcripts", ""), "no 'AI reading', no transcript text")
    ok("&lt;script&gt;alert(1)" in t and "<script>alert(1)" not in t, "a name holding <script> is shown as text")
    t4 = cl.get("/portal/console/staff?as=alisha", headers=H("shivani")).get_data(as_text=True)
    ok("Call Console · Shivani" in t4 and "seeing" not in t4, "a staff ?as= is ignored: her own page")
    t2 = cl.get("/portal/console/staff", headers=H("alisha")).get_data(as_text=True)
    ok("/portal/inbox?m=" not in t2, "no Chat / Reply for a login that is not a WhatsApp user")
    print("[4] Call")
    ok(cl.post("/portal/console/staff/api/call", json={"phone10": ph(1)}, headers=H("shivani")).status_code == 400, "no header -> 400")
    r = cl.post("/portal/console/staff/api/call", json={"phone10": ph(1)}, headers=H("shivani", post=True))
    ok(r.status_code == 200 and called[-1] == (ph(1), "shivani"), "Call -> ivr_call(her number, HER login)")
    r = cl.post("/portal/console/staff/api/call", data="phone10=" + ph(1), headers=H("shivani", post=True))
    ok(r.status_code == 409 and len(called) == 1, "a body that is not JSON -> 409, nothing dialled")
    r = cl.post("/portal/console/staff/api/call", json={"phone10": ph(9999)}, headers=H("shivani", post=True))
    ok(r.status_code == 409 and len(called) == 1, "a number no list showed -> 409, nothing dialled")
    ok(cl.post("/portal/console/staff/api/call", json={"phone10": ph(1)}, headers=H("bhawna", post=True)).status_code == 403, "bhawna -> 403")
    cs_ = sys.modules["calls_staff"]
    t_r = cs_._REBUILT[0]
    r = cl.post("/portal/console/staff/api/call", json={"phone10": ph(9998)}, headers=H("shivani", post=True))
    ok(r.status_code == 409 and cs_._REBUILT[0] == t_r and t_r > 0, "a second unknown number within the minute re-reads nothing")
    cs_._OFFERED.clear()
    cs_._REBUILT[0] = 0.0                                # a minute later, on a worker that never drew the page
    r = cl.post("/portal/console/staff/api/call", json={"phone10": ph(4)}, headers=H("alisha", post=True))
    ok(r.status_code == 200 and called[-1] == (ph(4), "alisha"), "a worker that never drew the page reads the lists and dials")
    r = cl.post("/portal/console/staff/api/call", json={"phone10": ph(3)}, headers=H("manoj", "doctor", post=True))
    ok(r.status_code == 200 and called[-1] == (ph(3), "manoj"), "the doctor's Call rings his own phone")
    print("[5] Wrong?")
    ref = T["mine"][0]["ref"]
    ok(cl.post("/portal/console/staff/api/dispute", json={"ref": ref, "text": "x"}, headers=H("shivani")).status_code == 400, "no header -> 400")
    ok(cl.post("/portal/console/staff/api/dispute", json={"ref": ref, "text": ""}, headers=H("shivani", post=True)).status_code == 400, "empty text -> 400")
    ok(cl.post("/portal/console/staff/api/dispute", json={"ref": ref, "text": "He said he will not come"}, headers=H("alisha", post=True)).status_code == 409,
       "someone else's call -> 409")
    ok(cl.post("/portal/console/staff/api/dispute", json={"ref": ref, "text": "x"}, headers=H("manoj", "doctor", post=True)).status_code == 403,
       "the doctor cannot send one -> 403")
    r = cl.post("/portal/console/staff/api/dispute", json={"ref": ref, "text": "He said he will not come"}, headers=H("shivani", post=True))
    ok(r.status_code == 200, "her own call -> sent (%s %s)" % (r.status_code, (r.get_json() or {}).get("msg")))
    ok(cl.post("/portal/console/staff/api/dispute", json={"ref": ref, "text": "again"}, headers=H("shivani", post=True)).status_code == 409, "twice -> 409")
    con = sqlite3.connect(os.path.join(root, "call_review.db"))
    rows = con.execute("SELECT ref, staff, fig, text, by_whom FROM dispute").fetchall()
    con.close()
    ok(rows == [(ref, "shivani", "verdict", "He said he will not come", "shivani")], "one row in the owner's review store, fig 'verdict'")
    cc._CARD_CACHE.clear()
    dj = cl.get("/portal/console/api/card/shivani?span=today", headers=H("manoj", "doctor")).get_json()
    ok(any(x["fig"] == "verdict" for x in dj["card"]["disputes"]), "it is on his ?as= card as a dispute")
    t = cl.get("/portal/console", headers=H("manoj", "doctor")).get_data(as_text=True)
    ok("says the Call verdict is wrong" in t and "He said he will not come" in t and "Accept" in t, "his page: Disputed, with Accept / It stands")
    d2 = cl.get("/portal/console/staff/api/lists", headers=H("shivani")).get_json()
    ok(not d2["tabs"]["mine"][0]["can_dispute"] and d2["tabs"]["mine"][0]["disputed"] == "Sent to the doctor", "her row: Sent to the doctor")
    ok("Accept — the verdict was wrong" in t, "his button on a verdict dispute: 'Accept — the verdict was wrong'")
    nl0 = dj["card"]["figs"]["not_logged"]
    con = sqlite3.connect(os.path.join(root, "call_review.db"))
    did = con.execute("SELECT id FROM dispute").fetchone()[0]
    con.close()
    r = cl.post("/portal/console/api/dispute-answer", json={"id": did, "answer": "accept"}, headers=H("manoj", "doctor"))
    cc._CARD_CACHE.clear()
    dj2 = cl.get("/portal/console/api/card/shivani?span=today", headers=H("manoj", "doctor")).get_json()
    ok("verdict is marked wrong" in (r.get_json() or {}).get("msg", ""), "his Accept's words: the verdict is marked wrong")
    r2 = cl.post("/portal/console/staff/api/dispute", json={"ref": ref, "text": "once more"}, headers=H("shivani", post=True))
    ok(r2.status_code == 409, "after his answer, no second Wrong? on the same call")
    ok(r.status_code == 200 and nl0 == 2 and dj2["card"]["figs"]["not_logged"] == 2,
       "his Accept on a verdict dispute leaves her other figures alone (not logged %s -> %s)" % (nl0, dj2["card"]["figs"]["not_logged"]))
    d5 = cl.get("/portal/console/staff/api/lists", headers=H("shivani")).get_json()
    ok(d5["tabs"]["mine"][0]["disputed"] == "Doctor agreed: the verdict was wrong", "her row then reads 'Doctor agreed'")
    ref2 = d5["tabs"]["mine"][1]["ref"]
    con = sqlite3.connect(os.path.join(root, "call_review.db"))
    con.execute("INSERT INTO dispute (ref, staff, fig, text, call_h, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                (ref2, "shivani", "not_logged", "I did log it", "", "shivani", TODAY + " 11:20:00"))
    con.commit()
    con.close()
    cc._CARD_CACHE.clear()
    d6 = cl.get("/portal/console/staff/api/lists", headers=H("shivani")).get_json()
    ok(not d6["tabs"]["mine"][1]["can_dispute"], "an open dispute of another figure on her call -> no Wrong? (one open dispute per call)")
    print("[6] the tile")
    names = [x["name"] for x in pm.TILES]
    ok(names == ["System Board", "Call Console", "My Call Console", "Call Tracker"], "'My Call Console' right after 'Call Console'")
    tile = pm.TILES[2]
    ok(tile["roles"] == [] and tile["group"] == "Calls & WhatsApp" and pm._TILE_GROUP.get("My Call Console") == "Calls & WhatsApp"
       and tile["url"] == "/portal/console/staff", "no role (granted by name only), its group, its address")
    print("[7] evening, 16:30")
    app2, cc2, pm2, _ = build_app(root, con_p, inbox_p, _dt.datetime(2026, 11, 24, 16, 30))
    cc2._CARD_CACHE.clear()
    d3 = app2.test_client().get("/portal/console/staff/api/lists", headers=H("shivani")).get_json()
    T3 = d3["tabs"]
    ok(d3["evening"] and phones(T3["due"]) == [ph(1), ph(4)], "from 16:00 untried Grace leaves Follow-ups due")
    ok(phones(T3["eve"]) == [ph(5), ph(3)], "Evening = two-attempt rows first, then Grace untried")
    ok(next(x for x in T3["again"] if x["phone"] == ph(2))["hi"], "Call again lit once due (10:05 + 2 h)")
    t3 = app2.test_client().get("/portal/console/staff", headers=H("shivani")).get_data(as_text=True)
    ok("Evening calls 2" in t3, "the Evening count shows from 16:00")
    ok([x["name"] for x in pm2.TILES].count("My Call Console") == 1, "the tile is added once")
    print("\n%d checks, %d failed" % (N[0], len(FAILS)))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    CODE = os.path.abspath(sys.argv[2])
    sys.path.insert(0, CODE)
    if sys.argv[1] == "dump":
        do_dump(sys.argv[3])
        sys.exit(0)
    sys.exit(do_walk())
