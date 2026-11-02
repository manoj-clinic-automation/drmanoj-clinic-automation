#!/usr/bin/env python3
"""
walk_s698.py -- S698_CALLS_R1: the walk on MADE-UP data (no patient, no real number; phones 5000000xxx).
  python3 walk_s698.py <folder>            the folder holds calls_console.py, portal_console.py, call_hook_capture.py,
                                           portal.py (the kit's TO files or a copy of the live folder)
  python3 walk_s698.py <folder> --control  the same checks on the LIVE files: they must go red
  python3 walk_s698.py <folder> --mutants  the kit's files with one rule broken at a time: every mutant must be caught
Builds a console.db through the builder's own transform() from fixtures, renders the page through the module registered
on a bare Flask app with a pass-through gate, and checks the HTML and the pure rules. Prints one verdict line last.
"""
import datetime as _dt
import importlib.util
import json
import os
import re
import sqlite3
import sys
import tempfile

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else ".")
MODE = "control" if "--control" in sys.argv else ("mutants" if "--mutants" in sys.argv else "walk")
TOTAL_WALK = 82
TOTAL_MUT = 9
D = "2026-11-02"            # the made-up "today"
D1 = "2026-11-01"
D2 = "2026-10-31"
D10 = "2026-10-23"
NOW = _dt.datetime(2026, 11, 2, 18, 0, 0)
RED, GREEN_N = [], [0]


def check(name, cond):
    if cond:
        GREEN_N[0] += 1
    else:
        RED.append(name)
        print("  RED  " + name)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def jk(ph, unix):
    return "%s_%d" % (ph, unix)


def ist_unix(day, hhmm):
    t = _dt.datetime.strptime(day + " " + hhmm, "%Y-%m-%d %H:%M").replace(tzinfo=_dt.timezone(_dt.timedelta(hours=5, minutes=30)))
    return int(t.timestamp())


def fixtures():
    """The tab data the builder reads, shaped for the page's cases. Returns (tabdata, followups)."""
    P1, P2, P3, P4, P5, P6, P7, P8, P9, P10 = ["50000001%02d" % i for i in range(1, 11)]
    def cd(ph, cat, status, rec, day, hhmm, dur="0", ring="0", key=None, ref="", ses="", ev="call.summary"):
        end = _dt.datetime.strptime(day + " " + hhmm, "%Y-%m-%d %H:%M") + _dt.timedelta(seconds=int(dur))
        return [key or ("IN-" + (ses or ("s" + hhmm.replace(":", "") + ph[-2:]))), ref, ses or ("s" + hhmm.replace(":", "") + ph[-2:]),
                cat, status, dur, "", dur, ring, rec, end.strftime("%Y-%m-%dT%H:%M:%S") + "+05:30",
                end.strftime("%Y-%m-%dT%H:%M:%S") + "+05:30", ev, ph if cat == "incoming" else ""]
    hdr = ["client_ref_id", "ref_id", "session_id", "category", "status", "total_duration", "customer_result",
           "customer_talk_duration", "customer_ring_duration", "recording_filename", "ended_at_ist", "captured_at_ist",
           "source_event", "phone10"]
    rows = [
        cd(P1, "incoming", "missed", "", D, "09:58", ring="31"),
        cd(P1, "incoming", "missed", "", D, "10:05", ring="28"),
        cd(P2, "incoming", "missed", "", D, "14:51", ring="25"),
        cd(P2, "obd", "bridged", "R2", D, "15:02", dur="72", key=P2 + "-1700000002aa"),   # starts 15:02 (its join key), ends 15:03:12
        # P3: the doubled pair -- the same IN- key twice (call.end without the recording, call.summary with it)
        cd(P3, "incoming", "bridged", "", D, "12:14", dur="161", ses="s3", ref="uuid3", ev="call.end"),
        cd(P3, "incoming", "bridged", "R3", D, "12:14", dur="161", ses="s3", ref="uuid3", ev="call.summary"),
        # P4 Anjali: the owner's own OBD call (phone10 blank; the join key carries the number), flagged post-op; Shivani's later call
        cd(P4, "obd", "bridged", "R4", D, "09:40", dur="91", key=P4 + "-1700000004aa"),
        cd(P4, "obd", "bridged", "R4b", D, "13:42", dur="125", key=P4 + "-1700000004bb"),
        # P5 Rakesh: Shavez's follow-up call, filed 'not coming', the AI heard 'coming' -> Mismatch
        cd(P5, "obd", "bridged", "R5", D, "11:20", dur="134", key=P5 + "-1700000005aa"),
        # P6 unknown: WhatsApp-less; missed then an outgoing not answered -> tried
        cd(P6, "incoming", "missed", "", D, "16:31", ring="30"),
        cd(P6, "obd", "missed", "", D, "16:40", ring="40", key=P6 + "-1700000006aa"),
        # P7 Sunita: two misses then Shivani reaches her
        cd(P7, "incoming", "missed", "", D, "17:20", ring="30"),
        cd(P7, "incoming", "missed", "", D, "17:31", ring="22"),
        cd(P7, "obd", "bridged", "R7", D, "17:42", dur="53", key=P7 + "-1700000007aa"),
        # P8: a number the owner marked spam
        cd(P8, "incoming", "missed", "", D, "08:30", ring="12"),
        # yesterday: one unknown never reached, one patient answered
        cd(P9, "incoming", "missed", "", D1, "10:00", ring="20"),
        cd(P10, "incoming", "bridged", "R10", D1, "11:00", dur="60"),
        # a probe row (excluded by the builder)
        ["IN-probe", "", "probe", "incoming", "probe", "", "", "", "", "", D + "T07:00:00+05:30", D + "T07:00:00+05:30", "call.end", "0000000000"],
    ]
    recs = [["R2", jk(P2, ist_unix(D, "15:02")), "https://drive/x2", "f2"],
            ["R3", jk(P3, ist_unix(D, "12:14")), "https://drive/x3", "f3"],
            ["R4", jk(P4, ist_unix(D, "09:40")), "https://drive/x4", "f4"],
            ["R4b", jk(P4, ist_unix(D, "13:42")), "https://drive/x4b", "f4b"],
            ["R5", jk(P5, ist_unix(D, "11:20")), "https://drive/x5", "f5"],
            ["R7", jk(P7, ist_unix(D, "17:42")), "https://drive/x7", "f7"],
            ["R10", jk(P10, ist_unix(D1, "11:00")), "https://drive/x10", "f10"]]
    vh = ["Join Key", "Agent", "Claimed Outcome", "AI Outcome", "Verdict", "Status", "Judged At", "Patient Name", "Clinic ID",
          "AI Reason", "Evidence", "Flag Postop", "Flag Urgent"]
    verd = [[jk(P2, ist_unix(D, "15:02")), "Shavez Khan", "appointment_booked", "appointment_booked", "Match", "done", D + " 15:20:00", "", "", "fee and timings", "Monday aa jaunga", "", ""],
            [jk(P3, ist_unix(D, "12:14")), "Shivani Srivastava", "appointment_booked", "appointment_booked", "Match", "done", D + " 12:30:00", "", "", "knee pain, two months", "Tuesday 10:30 ka time", "", ""],
            [jk(P4, ist_unix(D, "09:40")), "Dr Manoj Agarwal", "", "problem", "No claim logged", "done", D + " 10:00:00", "Anjali Mishra", "C-2268", "post-op concern", "swelling has come back", "TRUE", ""],
            [jk(P4, ist_unix(D, "13:42")), "Shivani Srivastava", "coming", "coming", "Match", "done", D + " 14:00:00", "Anjali Mishra", "C-2268", "", "kal subah aa jaiye", "", ""],
            [jk(P5, ist_unix(D, "11:20")), "Shavez Khan", "not_coming", "coming", "Mismatch", "done", D + " 11:40:00", "Rakesh Gupta", "C-1890", "patient said Thursday", "Thursday ko aa jaunga", "", ""],
            [jk(P7, ist_unix(D, "17:42")), "Shivani Srivastava", "coming", "coming", "Match", "done", D + " 18:00:00", "Sunita Verma", "C-2211", "", "review Tuesday", "", ""]]
    tr = [[jk(P3, ist_unix(D, "12:14")), D + " 12:25:00", "Ghutne mein do mahine se dard hai. Tuesday 10:30 ka time de deti hoon. " * 4, "f3t"],
          [jk(P5, ist_unix(D, "11:20")), D + " 11:35:00", "Haan Thursday ko aa jaunga, abhi thoda dard kam hai.", "f5t"]]
    pats = [["Mobile", "Patient Name", "Diagnosis", "Age", "Gender", "Clinic_Specific_Id", "Last Visit"],
            [[P4, "Anjali Mishra", "ACL right, post-op day 12", "34", "F", "C-2268", "2026-10-21"],
             [P5, "Rakesh Gupta", "frozen shoulder", "64", "M", "C-1890", "2026-10-25"],
             [P7, "Sunita Verma", "OA knee, both", "52", "F", "C-2211", "2026-10-10"],
             [P10, "Vinod Kumar", "lumbar disc", "45", "M", "C-2189", "2026-10-30"],
             ["5000000111", "Mohan Lal", "TKR right, post-op review", "66", "M", "C-1876", "2026-10-15"],
             ["5000000112", "Suresh Babu", "TKR both, 3-month review", "70", "M", "C-1712", "2026-07-20"]]]
    agents = [["Ext", "Name", "UserId", "Active"], [["10", "Dr Manoj Agarwal", "u10", "TRUE"], ["11", "Shivani Srivastava", "u11", "TRUE"], ["12", "Shavez Khan", "u12", "TRUE"]]]
    tab = {"Call_Durations": (hdr, rows), "Call_Recordings": (["MyOperator Filename", "Join Key", "Recording Link", "Drive File Id"], recs),
           "Call_Verdicts": (vh, verd), "Call_Transcripts": (["Join Key", "Transcribed At", "Transcript Text", "Transcript Drive File ID"], tr),
           "Patient_Master": pats, "Outbound_Log": (["Date", "Time", "Phone10", "Agent", "Duration_s", "Status", "Start_Unix"], []),
           "Agents": agents, "Daily_Summary": (["Date", "Total Calls", "Incoming", "Net-Missed", "Resolved", "Net-Missed %"], [])}
    fu_h = ["Mobile Number", "Patient Name", "Due Date", "Status"]
    fu_r = [["5000000111", "Mohan Lal", D2, "booked"],                 # due 2 days ago, no call -> grace, no call made
            [P5, "Rakesh Gupta", D2, "booked"],                       # due 2 days ago, Shavez called today -> grace, reached
            ["5000000112", "Suresh Babu", D10, "booked"]]             # due 10 days ago, no call -> overdue
    return tab, (fu_h, fu_r), {"P%d" % i: p for i, p in enumerate([P1, P2, P3, P4, P5, P6, P7, P8, P9, P10], 1)}


def build_db(pc, path):
    tab, (fu_h, fu_r), P = fixtures()
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    counts, headers = pc.transform(conn, tab)
    # the agent table the Stage-2a layer builds: the handler per join key
    conn.execute("CREATE TABLE IF NOT EXISTS call_agent (join_key TEXT PRIMARY KEY, agent TEXT, department TEXT, matched_how TEXT)")
    for jk_, ag in conn.execute("SELECT join_key, agent FROM verdicts WHERE join_key<>''").fetchall():
        conn.execute("INSERT OR REPLACE INTO call_agent VALUES (?,?,?,?)", (jk_, ag, "", "exact"))
    fm = pc.build_no_shows(conn, fu_h, fu_r, D)
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('followups_feed', ?)", (json.dumps(fm),))
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('built_at', ?)", (NOW.strftime("%Y-%m-%dT%H:%M:%S"),))
    conn.commit()
    conn.close()
    return counts, P


def make_app(cc, dbpath, spam):
    from flask import Flask
    app = Flask("walk")
    app.secret_key = "walk"
    state = {"authed": True}

    def gate(view):
        from functools import wraps
        from flask import redirect as _redir
        @wraps(view)
        def w(*a, **k):
            if not state["authed"]:
                return _redir("/portal/login")
            return view(*a, **k)
        return w

    def conn():
        c = sqlite3.connect("file:%s?mode=ro" % dbpath, uri=True)
        c.row_factory = sqlite3.Row
        return c

    def meta():
        c = conn()
        try:
            b = c.execute("SELECT v FROM meta WHERE k='built_at'").fetchone()[0]
        finally:
            c.close()
        return {"ok": True, "built_at": b, "stale": False, "age_min": 3, "counts": {}}

    cc.register(app, gate, lambda: "manoj", lambda n, d="": d, {"console_conn": conn, "console_meta": meta,
                                                               "reviews_maps": lambda: ({}, {}), "spam_phones": lambda: set(spam)})
    return app, state


def walk(root, tag=""):
    """Every check on the folder's files. Returns the number of reds added."""
    before = len(RED)
    paths = {n: os.path.join(root, n) for n in ("calls_console.py", "portal_console.py", "call_hook_capture.py", "portal.py")}
    # --- the files exist and carry the kit's marks ---
    check("calls_console.py is there", os.path.exists(paths["calls_console.py"]))
    ptxt = open(paths["portal.py"], encoding="utf-8").read() if os.path.exists(paths["portal.py"]) else ""
    check("portal.py: the old page moved to /portal/console/old", '@app.route("/portal/console/old")' in ptxt)
    check("portal.py: the new module registered behind the doctor gate", "calls_console.register(" in ptxt and "doctor_required" in ptxt.split("calls_console.register(")[-1][:120] if "calls_console.register(" in ptxt else False)
    check("portal.py (F-1084): the digest's last build filled", 'm["built"] = m.get("built_at")' in ptxt)
    check("portal.py: exactly one route serves /portal/console besides the fallback", ptxt.count('@app.route("/portal/console")') == 1 and "_calls_broken" in ptxt)
    btxt = open(paths["portal_console.py"], encoding="utf-8").read() if os.path.exists(paths["portal_console.py"]) else ""
    check("builder: the fold is in load_calls", "rows, fold = fold_calls(rows)" in btxt)
    htxt = open(paths["call_hook_capture.py"], encoding="utf-8").read() if os.path.exists(paths["call_hook_capture.py"]) else ""
    check("hook: v3.2 -- the real row from the append answer", "_row_from_append(resp)" in htxt)
    check("hook: v3.2 -- the row verified before an update", "_row_holds(ws, r, key, ref)" in htxt)
    check("hook: v3.2 -- the uuid as the second key", '"refs": {}' in htxt and "_store[\"refs\"]" in htxt)
    if not (os.path.exists(paths["calls_console.py"]) and "fold_calls" in btxt):
        print("  (the folder has no S698 module or no fold -- the rest of the walk cannot run; every remaining check is red)")
        for i in range(TOTAL_WALK - (len(RED) - before) - GREEN_N[0]):
            RED.append("not run %d" % i)
        return len(RED) - before
    pc = load("pc_walk" + tag, paths["portal_console.py"])
    cc = load("cc_walk" + tag, paths["calls_console.py"])
    td = tempfile.mkdtemp(prefix="s698walk_", dir=os.environ.get("WALK_TMPDIR") or None)
    dbp = os.path.join(td, "console.db")
    counts, P = build_db(pc, dbp)
    # --- the builder's fold on the fixtures ---
    check("builder: the doubled P3 pair folded -- 16 calls kept of 18 rows (probe out, one pair folded)", counts["calls"] == 16)
    check("builder: the fold stats ride in the call stats", counts["_call_stats"]["fold"]["folded"] == 1 and counts["_call_stats"]["fold"]["same_key_pairs"] == 1)
    conn = sqlite3.connect(dbp)
    r3 = conn.execute("SELECT recording_filename, source_event FROM calls WHERE phone10=?", (P["P3"],)).fetchall()
    check("builder: the folded row keeps the recording (the summary won)", len(r3) == 1 and r3[0][0] == "R3")
    conn.close()
    # --- the pure rules ---
    check("fmt_num groups the full number", cc.fmt_num("5000000101") == "50000 00101" and cc.fmt_num("") == "")
    check("first_name: the owner's calls read 'you'", cc.first_name("Dr Manoj Agarwal") == "you" and cc.first_name("Shivani Srivastava") == "Shivani")
    check("call_start: the join key's unix is the start", cc.call_start(D + "T12:16:41+05:30", jk(P["P3"], ist_unix(D, "12:14")), "161").strftime("%H:%M") == "12:14")
    check("call_start: no join key -> the end minus the duration", cc.call_start(D + "T15:03:12+05:30", "", "72").strftime("%H:%M:%S") == "15:02:00")
    check("wait_h counts the reading window only (22:50 -> 08:00 next day = 1 h 10 min, not 9 h)",
          abs(cc.wait_h(_dt.datetime(2026, 11, 1, 22, 50), _dt.datetime(2026, 11, 2, 8, 0)) - (10 / 60.0 + 1.0)) < 0.05)
    check("wait_words", cc.wait_words(0.4) == "24 min" and cc.wait_words(11.2) == "11 h" and cc.wait_words(60) == "2 days")
    check("en_out maps the staff's codes to English", cc.en_out("k_not_coming") == "not coming" and cc.en_out("appointment_booked") == "booked" and cc.en_out("") == "")
    mk = lambda kind, hhmm, ans: {"direction": "In" if kind.startswith("in") else "Out", "answered": ans, "kind": kind, "t": _dt.datetime.strptime(D + " " + hhmm, "%Y-%m-%d %H:%M"), "ai_h": "", "claimed_h": ""}
    st, w, _ = cc.person_state([mk("in_miss", "09:58", False), mk("in_miss", "10:05", False)], NOW)
    check("state: two misses, nothing after -> rose 'awaiting · 7 h' (18:00 - 10:05 inside the window)", st == "rose" and w == "awaiting · 7 h")
    st, w, _ = cc.person_state([mk("in_miss", "14:51", False), mk("out_ok", "15:02", True)], NOW)
    check("state: a miss then a connected call -> green 'answered · 11 min'", st == "green" and w == "answered · 11 min")
    st, w, _ = cc.person_state([mk("in_miss", "16:31", False), mk("out_miss", "16:40", False)], NOW)
    check("state: a miss then a call not answered -> amber 'tried · not reached'", st == "amber" and w == "tried · not reached")
    st, w, _ = cc.person_state([mk("out_ok", "09:40", True)], NOW)
    check("state: staff-initiated and answered -> green", st == "green")
    st, w, _ = cc.person_state([mk("in_ok", "12:14", True)], NOW)
    check("state: an answered incoming call -> green 'answered'", st == "green" and w == "answered")
    st, w, _ = cc.person_state([mk("out_ok", "09:00", True), mk("in_miss", "10:00", False)], NOW)
    check("state: a connect BEFORE the miss does not answer it (the latest thing the patient did)", st == "rose")
    # --- the page ---
    app, state = make_app(cc, dbp, spam={P["P8"]})
    with app.test_request_context("/portal/console"):
        c = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True); c.row_factory = sqlite3.Row
        html = cc.render(c, {"span": "today"}, now=NOW)
        html7 = cc.render(c, {"span": "7"}, now=NOW)
        htmlq = cc.render(c, {"span": "7", "q": "Tuesday"}, now=NOW)
        htmly = cc.render(c, {"span": "yesterday"}, now=NOW)
        d = cc.page_data(c, span="today", now=NOW)
        c.close()
    check("page: the legend's eight icons", html.count('class="lg"') == 1 and all(s in html for s in ("Incoming call — connected", "Outgoing call — not answered (dashed)", "WhatsApp — template (not a reply)")))
    check("page: the strip -- 14 calls from 8 callers today (calls only; the probe out; the pair folded)", "<b>14 calls</b> from <b>8 callers</b>" in html)
    check("page: the strip names the one person nobody has answered", "1 person nobody has answered" in html)
    check("page: the strip's icon counts (in answered 1, out answered 5, missed then reached 3, missed open 4 -- the spam call counted as a call)",
          d["counts"]["in_ok"] == 1 and d["counts"]["out_ok"] == 5 and d["counts"]["miss_then_ok"] == 3 and d["counts"]["miss_open"] == 4)
    check("page: the spam number is in no people count (awaiting 1, tried 1, answered 5)",
          d["counts"]["awaiting"] == 1 and d["counts"]["tried"] == 1 and d["counts"]["answered"] == 5)
    check("page: flagged for you 1, to check 1", "1 call flagged for you" in html and "1 to check (staff ≠ AI)" in html)
    ny = d["needs"]
    check("needs you: three lines, the unknown caller first (rose), then the flagged call and the mismatch (amber)",
          len(ny) == 3 and [n["tone"] for n in ny] == ["rose", "amber", "amber"] and ny[0]["act"] == "call" and ny[1]["act"] == "listen" and ny[2]["act"] == "review")
    check("needs you: the unknown caller's line -- the full number, the wait, a Call back button", "50000 00101" in html and "nobody has answered" in html and "waiting 7 h" in html and "callBack('5000000101'" in html)
    check("needs you: the flagged call -- 'AI heard' with the evidence, 'your own call', a Listen button", "AI heard “swelling has come back”" in html and "your own call · ▶ 1:31" in html and ">Listen<" in html)
    check("needs you: staff ≠ AI -- what was logged and what the recording says", "Shavez logged “not coming”; the recording says “coming”" in html and "staff ≠ AI — to check" in html)
    check("needs you: the spam number is left out", P["P8"] not in "".join(n["phone"] or "" for n in ny if n.get("phone")))
    people = d["people"]
    check("people: 8 rows, the four unknown numbers first (awaiting, tried, then answered), then the patients",
          len(people) == 8 and people[0]["phone"] == P["P1"] and people[0]["state"] == "rose" and people[1]["phone"] == P["P6"]
          and all(p["unknown"] for p in people[:4]) and not any(p["unknown"] for p in people[4:7]))
    check("people: the spam row last, grey, marked", people[-1]["phone"] == P["P8"] and people[-1]["state"] == "grey" and "marked spam" in html)
    check("people: the chips -- All 8, Awaiting 1, Calls 8, Unknown numbers 5", "All 8<" in html and "Awaiting 1<" in html and "Calls 8<" in html and "Unknown numbers 5<" in html)
    p2 = next(p for p in people if p["phone"] == P["P2"])
    check("people: P2 -- missed then reached in 11 min, the chain ends 'booked'", p2["state_h"] == "answered · 11 min" and p2["tail"] == "booked")
    check("people: the owner's OBD call with a blank phone10 is placed by its join key (Anjali's row holds 2 calls)", next(p for p in people if p["phone"] == P["P4"])["n_calls"] == 2)
    p4 = next(p for p in people if p["phone"] == P["P4"])
    check("people: the patient's row carries name, clinic ID, number, age/sex, diagnosis", "Anjali Mishra · C-2268" in html and "50000 00104 · 34/F · ACL right, post-op day 12" in html)
    check("people: the timeline line and sub-line (answered by Shivani · AI · filed)", "Incoming call — answered by Shivani" in html and "AI: booked · filed: booked" in html)
    check("people: a missed call reads its ring seconds and 'no one picked up'", "Missed call — rang 31 s" in html and "no one picked up" in html)
    check("people: the transcript's head (220 chars) is shown with 'whole transcript' on tap, never the whole text inline", "whole transcript" in html and 0 < html.count("Ghutne mein do mahine se dard hai") < 4)
    check("people: the recording plays in place (the player pill with the length)", 'onclick="playJk(' in html and "&#9654; 2:41" in html)
    check("people: the awaiting row is open with the rose foot line and its Call back", 'class="tl rose"' in html and "Nobody has called back" in html)
    check("people: the review select on answered calls posts to the old route with a return to this page", 'action="/portal/console/review"' in html and 'name="ret" value="span=today"' in html)
    check("people: the mismatch row shows the owner's verdict select", "your verdict…" in html)
    check("people: the P3 row holds ONE call (the pair folded), its chain one icon", next(p for p in people if p["phone"] == P["P3"])["n_calls"] == 1)
    ns = d["noshows"]
    check("follow-up: the feed found; 3 rows -- 1 of 3 called; grace 2 (one reached, one no call), overdue 1", ns["found"] and len(ns["rows"]) == 3 and ns["called"] == 1 and len(ns["bands"][0][2]) == 2 and len(ns["bands"][1][2]) == 1)
    check("follow-up: the called row's chain (an OBD call found by its join key: Shavez · reached) and the uncalled row's line", "Shavez · reached" in html and "due 31 Oct · no call made" in html)
    wk = d["week"]
    check("week: unknown numbers that rang 5, reached 2 (one by an OBD call), booked 2, never reached 3 (the spam number out)", (wk["rang"], wk["reached"], wk["booked"], wk["never"]) == (5, 2, 2, 3))
    check("week: the note names what comes with the next kit", "come with the next kit" in html)
    e = d["earlier"]
    check("earlier days: yesterday's line -- 2 calls · 2 callers · unknown 1 (1 never reached)", len(e) == 1 and e[0]["calls"] == 2 and e[0]["callers"] == 2 and e[0]["unknown"] == 1 and e[0]["never"] == 1)
    check("earlier days: the line links to that day", "/portal/console?day=" + D1 in html)
    check("page: the day tabs, the search box, expand all, as of", "Today</a>" in html and 'name="q"' in html and "expand all" in html and "as of 18:00" in html)
    check("page: the footer names the old console's address", "/portal/console/old" in html)
    check("page: no 10-digit number as a bare run of digits except in the buttons' data", not re.search(r"(?<![\d'\"=/_])\d{10}(?![\d'\"_])", re.sub(r"callBack\('\d{10}'", "", re.sub(r"id=\"p\d{10}\"", "", html))))
    check("7 days: yesterday's people grouped under their day, today's people too", html7.count('class="note" style="border-top:0') == 2 and "Yesterday · Sun 1 Nov" in html7)
    check("search: 'Tuesday' (words said) finds the one caller whose transcript says it", "<b>50000 00103</b>" in htmlq and "<b>50000 00101</b>" not in htmlq)
    check("yesterday: no Needs-you section, the strip says Yesterday", 'id="needs"' not in htmly and "Yesterday: <b>2 calls</b>" in htmly)
    # --- the routes through the test client ---
    cl = app.test_client()
    r = cl.get("/portal/console?view=log&q=x")
    check("route: an old view redirects to /portal/console/old with its query", r.status_code == 302 and r.headers["Location"].endswith("/portal/console/old?view=log&q=x"))
    r = cl.get("/portal/console/api/tx/" + jk(P["P3"], ist_unix(D, "12:14")))
    check("route: the transcript api answers the text", r.status_code == 200 and "Tuesday" in r.get_json()["text"])
    r = cl.get("/portal/console/api/tx/not-a-key")
    check("route: a malformed key is 404", r.status_code == 404)
    state["authed"] = False
    r = cl.get("/portal/console")
    check("route: the gate holds (no login -> redirect)", r.status_code == 302 and "/portal/login" in r.headers["Location"])
    r = cl.post("/portal/console/api/call", json={"phone10": P["P1"]})
    check("route: the call api sits behind the gate too", r.status_code == 302)
    state["authed"] = True
    r = cl.get("/portal/console")
    check("route: the page answers 200 with no-store", r.status_code == 200 and r.headers.get("Cache-Control") == "no-store")
    # --- the click-to-call, with a fake call_api and a fake ring_agents ---
    calls = []
    def fake_post(url, body, key, timeout):
        calls.append((url, body, key))
        return 200, {"accepted": True}
    import types
    ro = types.ModuleType("ring_outcome"); ro.ivr_agent = lambda login: "Dr Manoj" if login == "manoj" else ""
    sys.modules["ring_outcome"] = ro
    envf = os.path.join(td, "wa.env"); open(envf, "w").write("CALL_API_SECRET=walkkey\n")
    cc._LAST_CALL.clear()
    ok, msg, code = cc.ivr_call(P["P1"], "manoj", env_path=envf, call_url="http://x/call", now=1000, post=fake_post)
    check("call: the owner's agent, the number from the row, the key in the header; accepted", ok and code == 200 and calls[0][1]["agent"] == "Dr Manoj" and calls[0][1]["patient_number"] == P["P1"] and calls[0][2] == "walkkey")
    ok2, msg2, code2 = cc.ivr_call(P["P1"], "manoj", env_path=envf, call_url="http://x/call", now=1030, post=fake_post)
    check("call: the same number within a minute is refused (429)", not ok2 and code2 == 429 and len(calls) == 1)
    ok3, msg3, code3 = cc.ivr_call("12345", "manoj", env_path=envf, call_url="http://x/call", now=2000, post=fake_post)
    check("call: a number that is not 10 digits is refused (400)", not ok3 and code3 == 400)
    ok4, msg4, code4 = cc.ivr_call(P["P2"], "nobody", env_path=envf, call_url="http://x/call", now=3000, post=fake_post)
    check("call: a login with no MyOperator agent is refused (400)", not ok4 and code4 == 400)
    ok5, msg5, code5 = cc.ivr_call(P["P2"], "manoj", env_path=envf, call_url="http://x/call", now=4000, post=lambda u, b, k, t: (400, {"reason": "number 5000000102 blocked"}))
    check("call: a refusal's reason comes back with any long number cut to its last 4", not ok5 and "…0102" in msg5 and "5000000102" not in msg5)
    ok6, msg6, code6 = cc.ivr_call(P["P2"], "manoj", env_path=envf, call_url="http://x/call", now=4010, post=fake_post)
    check("call: a refused call does not lock the number for a minute (the next try goes through)", ok6 and code6 == 200)
    del sys.modules["ring_outcome"]
    # --- the cold review's cases (R1) ---
    check("hook: the 'no longer holds' journal line prints no number (key head and tail only)",
          '(r, key[:3], key[-4:])' in htxt and "key[:40]" not in htxt)
    check("hook: a read error in the cell check raises (never read as a mismatch)", "a read\n" in htxt or "error RAISES" in htxt)
    cc2 = sqlite3.connect(dbp)
    cc2.execute("INSERT INTO calls (category,status,direction,answered,ended_at_ist,captured_at_ist,phone10,client_ref_id,join_key) VALUES "
                "('incoming','missed','In',0,?, ?, '5000000199','IN-odd','')", (D, D))      # a date-only end stamp (the hook's raw fallback)
    cc2.commit(); cc2.close()
    with app.test_request_context("/portal/console"):
        c = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True); c.row_factory = sqlite3.Row
        try:
            htmlx = cc.render(c, {"span": "today"}, now=NOW); ok_x = True
            html30 = cc.render(c, {"span": "30"}, now=NOW)
        except Exception as e:
            htmlx, ok_x, html30 = str(e), False, ""
        c.close()
    check("page: a call whose end stamp has no readable time does not crash today / 30 days (R1 blocker 1)", ok_x and "50000 00199" in htmlx and "50000 00199" in html30)
    cc2 = sqlite3.connect(dbp); cc2.execute("DELETE FROM calls WHERE client_ref_id='IN-odd'"); cc2.commit(); cc2.close()
    st, w, _ = cc.person_state([{"direction": "In", "answered": False, "kind": "in_miss", "t": None, "ai_h": "", "claimed_h": ""},
                                {"direction": "Out", "answered": True, "kind": "out_ok", "t": None, "ai_h": "", "claimed_h": ""}], NOW)
    check("state: no readable times -> the list's order decides (a later connect answers)", st == "green")
    check("wait_h is capped at a month (a 1973 start walks 31 days, not 53 years)", 0 < cc.wait_h(_dt.datetime(1973, 1, 1), NOW) < 31 * 24)
    cc2 = sqlite3.connect(dbp); cc2.execute("INSERT INTO no_shows VALUES ('5000000113','Bad Due','2026-13-45','booked',0,'','',0)"); cc2.commit(); cc2.close()
    with app.test_request_context("/portal/console"):
        c = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True); c.row_factory = sqlite3.Row
        nsx = cc.noshow_rows(c, NOW); c.close()
    check("follow-up: a row with an unreadable due date is kept as it is, the section not emptied", len(nsx["rows"]) == 4 and any(x["due_h"] == "2026-13-45" for x in nsx["rows"]))
    cc2 = sqlite3.connect(dbp); cc2.execute("DELETE FROM no_shows WHERE phone10='5000000113'"); cc2.commit(); cc2.close()
    # --- the hook's selftest and the builder's selftest, in this folder ---
    import subprocess
    r1 = subprocess.run([sys.executable, "-B", paths["portal_console.py"], "--selftest"], capture_output=True, text=True, timeout=120)
    check("builder --selftest passes (the fold's five checks among them)", r1.returncode == 0 and "SELFTEST PASSED" in r1.stdout and "S698 fold" in r1.stdout)
    r2 = subprocess.run([sys.executable, "-B", paths["call_hook_capture.py"], "--selftest"], capture_output=True, text=True, timeout=120, cwd=td)
    check("hook --selftest passes (v3.2's fake sheet among them)", r2.returncode == 0 and "selftest:" in r2.stdout and "0 failed" not in r2.stdout and r2.stdout.strip().split("\n")[-1].split()[-2].split("/")[0] == r2.stdout.strip().split("\n")[-1].split()[-2].split("/")[1])
    try:
        import shutil; shutil.rmtree(td)
    except Exception:
        pass
    return len(RED) - before


MUTANTS = [
    ("calls_console.py", "if any(it[\"direction\"] == \"Out\" for it in after):", "if False:", "a tried-not-reached never amber"),
    ("calls_console.py", "conn = [it for it in after if it[\"answered\"]]", "conn = [it for it in its if it[\"answered\"]]", "a connect before the miss counted as an answer"),
    ("calls_console.py", "people.sort(key=lambda r: (r[\"spam\"], not r[\"unknown\"],", "people.sort(key=lambda r: (r[\"spam\"], r[\"unknown\"],", "patients before unknown numbers"),
    ("calls_console.py", "if ph in spam:                                   # a number the owner marked spam", "if False:  # mutant", "the spam number counted and in Needs you"),
    ("calls_console.py", "if READ_FROM_H <= t.hour < READ_TO_H:", "if True:", "the wait counted through the night"),
    ("calls_console.py", "if last is not None and t - last < CALL_GAP:", "if False:", "no minute gap between calls to one number"),
    ("portal_console.py", "rows, fold = fold_calls(rows)", "fold = {\"folded\": 0, \"same_key_pairs\": 0}", "the fold removed from the builder"),
    ("call_hook_capture.py", "r = _row_from_append(resp) or (len(_store[\"index\"]) + 2)", "r = len(_store[\"index\"]) + 2", "the old row arithmetic back in the hook"),
    ("call_hook_capture.py", "    if r is not None and not _row_holds(ws, r, key, ref):\n        _reload_index(ws)", "    if False:\n        _reload_index(ws)", "the cell check removed from the hook"),
]


def mutants(root):
    import shutil
    caught = 0
    for i, (fn, old, new, why) in enumerate(MUTANTS, 1):
        td = tempfile.mkdtemp(prefix="s698mut_", dir=os.environ.get("WALK_TMPDIR") or None)
        for n in ("calls_console.py", "portal_console.py", "call_hook_capture.py", "portal.py"):
            shutil.copy(os.path.join(root, n), os.path.join(td, n))
        p = os.path.join(td, fn)
        t = open(p, encoding="utf-8").read()
        if t.count(old) != 1:
            print("  MUTANT %d: anchor not found once in %s (%s)" % (i, fn, why))
            continue
        open(p, "w", encoding="utf-8").write(t.replace(old, new, 1))
        n0 = len(RED)
        g0 = GREEN_N[0]
        walk(td, tag="m%d" % i)
        reds = RED[n0:]
        del RED[n0:]
        GREEN_N[0] = g0
        if reds:
            caught += 1
        else:
            print("  MISSED mutant %d: %s" % (i, why))
        shutil.rmtree(td, ignore_errors=True)
    return caught


if __name__ == "__main__":
    if MODE == "control":
        n = walk(ROOT, tag="c")
        print("CONTROL: %d red" % n)
    elif MODE == "mutants":
        c = mutants(ROOT)
        print("MUTANTS S698: caught %d of %d" % (c, len(MUTANTS)))
    else:
        walk(ROOT)
        total = GREEN_N[0] + len(RED)
        c = mutants(ROOT) if "--no-mutants" not in sys.argv else TOTAL_MUT
        print("WALK S698: %d of %d green · mutants caught %d of %d · " % (GREEN_N[0], total, c, len(MUTANTS)))
