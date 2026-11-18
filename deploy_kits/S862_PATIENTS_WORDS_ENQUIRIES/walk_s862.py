#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s862.py -- kit S862_PATIENTS_WORDS_ENQUIRIES (S480, 18-Nov-2026). A walk on a MADE-UP root: made-up patients, made-up
numbers (90000000xx -- no real number), made-up words, call record and Google file.

    python3 walk_s862.py <code_dir> <calls_console.py> <work_dir> [<node>]

<code_dir>  the finance files under test (the new patients_page.py / .html / patients_part2.py beside the live dx_feed.py and
            diagnosis_normalizer.py; or the live files for the CONTROL). The page is opened through Flask for every role
            (F-1445) and its own script is run under node on the reading (when node is there). Last line "WALK n/m"."""
import datetime as dt
import json
import os
import shutil
import sqlite3
import subprocess
import sys

CODE, CC, WORK = sys.argv[1:4]
NODE = sys.argv[4] if len(sys.argv) > 4 else shutil.which("node") or ""
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
GOO = os.path.join(WORK, "patients_google.json")
os.environ.update(PATIENTS_READING=os.path.join(WORK, "reading.dat"), PATIENTS_CONSOLE_DB=CON,
                  PATIENTS_INBOX_DB=os.path.join(WORK, "no_inbox.db"), PATIENTS_AWAIT_DB=os.path.join(WORK, "no_marks.db"),
                  PATIENTS_GMB_DB=os.path.join(WORK, "no_gmb.db"), PATIENTS_HISTORY=os.path.join(WORK, "no_history.json"),
                  PATIENTS_GOOGLE=GOO, PATIENTS_CALLS_CONSOLE=CC, FINANCE_DB=FIN)

import dx_feed                                                          # noqa: E402 -- the live dx_feed beside the files
UN = dx_feed.UNCLASSIFIED
f = sqlite3.connect(FIN)
f.executescript("CREATE TABLE patient_visit(visit_id INTEGER, visit_date TEXT, clinic_id TEXT, patient_uid TEXT);"
                "CREATE TABLE keep_me(x TEXT); INSERT INTO keep_me VALUES ('walk');")
dx_feed.ensure(f)
V = [  # uid, cid, day, written diagnosis (as Docterz gives it), follow-up
    ("u1", "7001", "2026-09-10", "FRACRURE SHAFT HUMERUS", ""),
    ("u2", "7002", "2026-09-25", "FRACRURE SHAFT HUMERUS (Comminuted right)", ""),
    ("u3", "07003", "2026-10-05", "CELLULITIS RIGHT LEG", ""),   # review 3: an ID written with a leading zero
    ("u4", "7004", "2026-10-06", "CELLULITIS LEFT LEG", ""),
    ("u5", "7005", "2026-10-20", "KNEE OSTEOARTHRITIS", ""),
    ("u6", "7006", "2026-11-10", "WALKWORD ZZQ", ""),
    ("u6", "7006", "2026-11-12", "", ""),
]
dn = dx_feed._normaliser()
for i, (u, c, d, raw, fu) in enumerate(V):
    f.execute("INSERT INTO patient_visit VALUES (?,?,?,?)", (i + 1, d, c, u))
    if raw:
        clean, std, cat, pri, sta = dx_feed.classify(dn, raw, {})
        f.execute("INSERT INTO dx_visit (patient_uid, visit_date, clinic_id, diagnosis_raw, std_dx, category, priority, dx_status, "
                  "follow_up_date, export_id, updated_at) VALUES (?,?,?,?,?,?,?,?,?,1,'walk')", (u, d, c, clean, std, cat, pri, sta, fu))
f.commit()
f.close()
c = sqlite3.connect(CON)
c.executescript("""CREATE TABLE calls (id INTEGER PRIMARY KEY AUTOINCREMENT, client_ref_id TEXT, ref_id TEXT, session_id TEXT, category TEXT,
 status TEXT, direction TEXT, answered INTEGER, total_duration TEXT, customer_result TEXT, customer_talk_duration TEXT,
 customer_ring_duration TEXT, recording_filename TEXT, ended_at_ist TEXT, captured_at_ist TEXT, source_event TEXT, phone10 TEXT, join_key TEXT);
CREATE TABLE verdicts (id INTEGER PRIMARY KEY AUTOINCREMENT, join_key TEXT, ai_outcome TEXT);
CREATE TABLE patients (phone10 TEXT, name TEXT, diagnosis TEXT, age TEXT, gender TEXT, last_visit TEXT, patient_uid TEXT, clinic_id TEXT);""")
for ph, cid in ((P(1), "7001"), (P(3), "7003"), (P(4), "7004"), (P(5), "7005"), (P(6), "7006"), (P(9), "6001")):
    c.execute("INSERT INTO patients (phone10, name, clinic_id) VALUES (?,?,?)", (ph, "WALK", cid))
c.execute("INSERT INTO patients (phone10, name, clinic_id) VALUES (?,?,?)", (P(8), "WALK", ""))      # a number with no clinic ID
c.execute("INSERT INTO patients (phone10, name, clinic_id) VALUES (?,?,?)", (P(12), "WALK", "9999"))  # review 4: an ID the visits have not reached


def call(ph, ts, d, ans):
    t = dt.datetime.fromisoformat(ts)
    jk = "%s_%d" % (ph, int(t.replace(tzinfo=dt.timezone(dt.timedelta(hours=5, minutes=30))).timestamp()))
    end = t + dt.timedelta(seconds=60)
    c.execute("INSERT INTO calls (direction, answered, total_duration, customer_talk_duration, customer_ring_duration, ended_at_ist, phone10, join_key) "
              "VALUES (?,?,?,?,?,?,?,?)", (d, 1 if ans else 0, "60", "45" if ans else "0", "10", end.strftime("%Y-%m-%d %H:%M:%S"), ph, jk))


call(P(20), "2026-08-01 10:00:00", "Out", False)     # the record begins 01-Aug
call(P(3), "2026-09-28 10:00:00", "In", True)        # u3 rang 7 days before his first visit (05-Oct) -> became, Sep
call(P(3), "2026-10-02 10:00:00", "In", False)       # ... and again in Oct, still before 05-Oct -> a caller of Oct too
call(P(4), "2026-10-06 09:00:00", "In", True)        # u4 rang and came the same day
call(P(5), "2026-10-25 10:00:00", "In", True)        # u5 rang AFTER his first visit (20-Oct): already a patient -> not a caller
call(P(9), "2026-10-10 10:00:00", "In", True)        # an old patient (6001, before these months) -> not a caller
call(P(8), "2026-10-11 10:00:00", "In", True)        # a known number with no clinic ID -> not a caller
call(P(11), "2026-10-12 10:00:00", "In", False)      # an unknown number, never came -> a caller who did not become
call(P(12), "2026-10-13 10:00:00", "In", True)       # review 4: registered after finance's last day -> still a caller, not 'old'
call(P(6), "2026-08-20 10:00:00", "In", True)        # u6 rang 82 days before his first visit (10-Nov): Aug caller, not within 60
call(P(1), "2026-11-02 10:00:00", "In", True)        # u1 (first visit 10-Sep) -> not a caller in Nov
c.commit()
c.close()
json.dump(dict(months={"2026-10": dict(searches=90, views=450, calls=15, directions=10, chats=3, website=2, interactions=27, yoy=dict(calls=5.0))},
               top_terms="walk", closed_days="walk"), open(GOO, "w"))
GOOM = os.path.join(WORK, "patients_google_mail.json")
os.environ["PATIENTS_GOOGLE_MAIL"] = GOOM
json.dump(dict(mail_day="2026-11-05", months={"2026-09": dict(searches=100, views=500, calls=20, directions=20, chats=2, website=1, interactions=43),
                                              "2026-10": dict(searches=90, views=450, calls=16, directions=10, chats=3, website=2, interactions=31),
                                              "2026-11": dict(searches=1, views=None, calls=1, directions=1, chats=1, website=1, interactions=4)}),
          open(GOOM, "w"))


def others(path):
    con = sqlite3.connect(path)
    try:
        return [r for t in ("patient_visit", "keep_me") for r in con.execute("SELECT * FROM %s ORDER BY 1" % t)]
    finally:
        con.close()


before = others(FIN)
import patients_page as pp                                              # noqa: E402
TODAY = dt.date(2026, 11, 17)
con = sqlite3.connect("file:%s?mode=ro" % FIN, uri=True)
reading, lists = pp.read(con, today=TODAY)
con.close()
W = reading.get("words") or {}
rows = {r["word"]: r for r in W.get("rows") or []}
ok("Part 1 reads; version S862", reading.get("ok") and getattr(pp, "VERSION", "") == "S862 1.0", getattr(pp, "VERSION", ""))
ok("words: 5 unrecognised words, 5 visits", (W.get("n"), W.get("visits")) == (5, 5), (W.get("n"), W.get("visits")))
fr = rows.get("FRACRURE SHAFT HUMERUS") or {}
ok("the spelling slip and its other side drawn together (2 visits)", fr.get("n") == 2 and [w["word"] for w in fr.get("words", [])] ==
   ["FRACRURE SHAFT HUMERUS", "FRACRURE SHAFT HUMERUS (Comminuted right)"], fr)
ok("FRACRURE suggested as Trauma / Fracture, from the spelling", fr.get("sug") == "Trauma / Fracture" and "FRACRURE = FRACTURE" in fr.get("why", ""), fr.get("why"))
ce = rows.get("CELLULITIS LEFT LEG") or rows.get("CELLULITIS RIGHT LEG") or {}
ok("CELLULITIS LEFT / RIGHT LEG one row, suggested Infection", ce.get("n") == 2 and len(ce.get("words", [])) == 2 and ce.get("sug") == "Infection / Osteomyelitis", ce)
zz = rows.get("WALKWORD ZZQ") or {}
ok("a word with no suggestion says so (sug empty)", zz.get("sug") == "" and zz.get("n") == 1, zz)
ok("the choices are his taxonomy's standard diagnoses with their groups", len(W.get("choices") or []) == len(dn.CATEGORY) and
   all(x["cat"] == dn.CATEGORY[x["std"]] for x in W.get("choices") or []))
ok("nothing placed yet", W.get("placed") == [])
g0 = (reading.get("groups") or {})
# ------------------------------------------------------------------ (c) callers who became patients
B = (reading.get("p2") or {}).get("became") or {}
bm = B.get("months") or {}
ok("became block ok, window 60", B.get("ok") is True and B.get("window") == 60, B.get("why"))
s9, o10, n11, a8 = bm.get("2026-09", {}), bm.get("2026-10", {}), bm.get("2026-11", {}), bm.get("2026-08", {})
ok("Sep: 1 caller, 1 became (u3, 7 days)", (s9.get("callers"), s9.get("became")) == (1, 1), s9)
ok("Oct: callers u3, u4, the unknown, the ID the visits have not reached = 4; became 2 (u3 3 days, u4 same day); old patient, no-ID number and u5 left out",
   (o10.get("callers"), o10.get("became")) == (4, 2), o10)
ok("Aug: u6 a caller, not within 60 days", (a8.get("callers"), a8.get("became")) == (1, 0), a8)
ok("Nov: no caller (u1 already a patient)", n11.get("callers") == 0, n11)
ok("Oct is 'so far' (17-Nov is within 60 days of its end); Aug complete", o10.get("complete") is False and a8.get("complete") is True)
ok("bec:2026-10 lists clinic IDs as written (07003) with their first visit", sorted(r[0] for r in lists.get("bec:2026-10", [])) == ["07003", "7004"] and
   any("same day" in r[2] for r in lists.get("bec:2026-10", [])), lists.get("bec:2026-10"))
ok("rang first, Oct: 3 new patients (7003, 7004, 7005), all covered, 2 rang first", (o10.get("newp"), o10.get("rang_base"), o10.get("rang")) == (3, 3, 2), o10)
ok("rang first, Sep: window before the record -> 7001 left out; 7002 has no number -> base 0 -> none", s9.get("rang") is None and s9.get("rang_base") == 0, s9)
ok("rang first, Nov: u6 rang 82 days before -> 0 of 1", (n11.get("rang"), n11.get("rang_base")) == (0, 1), n11)
ok("the rf list carries clinic IDs only, as written", sorted(r[0] for r in lists.get("rf:2026-10", [])) == ["07003", "7004"], lists.get("rf:2026-10"))
gg = (reading.get("p2") or {}).get("google") or {}
ok("Google block carries read_by / mail_day", (gg.get("read_by"), gg.get("mail_day")) == ("server", "2026-11-05"), gg)
gm = {r["ym"]: r for r in gg.get("rows") or []}
ok("Google: the mail adds September, its count wins in October, the session's year-on-year stays; a month with a missing count is left out",
   sorted(gm) == ["2026-09", "2026-10"] and gm["2026-09"]["calls"] == 20 and gm["2026-10"]["calls"] == 16 and gm["2026-10"]["yoy"] == dict(calls=5.0), gm)
open(GOOM, "w").write("{not json")
import patients_part2 as _p2                                            # noqa: E402
g2 = _p2.google_block(reading, {}) if hasattr(_p2, "google_block") else {}
ok("Google: an unreadable mail file is ignored (the session file alone, no 'read by the server')", g2.get("ok") and g2.get("read_by") == ""
   and [r["ym"] for r in g2["rows"]] == ["2026-10"] and g2["rows"][0]["calls"] == 15, g2)
json.dump(dict(mail_day="2026-11-05", months={"2026-11": dict(searches=1, views=None)}), open(GOOM, "w"))
g3 = _p2.google_block(reading, {})
ok("Google: a mail file with no whole month does not say 'read by the server'", g3.get("read_by") == "" and g3.get("mail_day") == "", g3.get("read_by"))
os.rename(GOO, GOO + ".away")
json.dump(dict(mail_day="2026-11-05", months={"2026-10": dict(searches=90.0, views=450, calls=16, directions=10, chats=3, website=2, interactions=31)}), open(GOOM, "w"))
g4 = _p2.google_block(reading, {})
ok("Google: the session file missing -> the mail alone stands (a whole number written 90.0 read as 90)", g4.get("ok") and g4.get("read_by") == "server"
   and [r["ym"] for r in g4["rows"]] == ["2026-10"] and g4["rows"][0]["searches"] == 90, g4)
os.rename(GOO + ".away", GOO)
ok("the reading wrote no store (read-only)", others(FIN) == before)
# ------------------------------------------------------------------ the page through Flask, every role (F-1445)
from flask import Flask, jsonify                                        # noqa: E402
app = Flask("walk862")


def require(*roles, unit="packs"):
    from flask import request                                           # noqa: PLC0415
    r = request.headers.get("X-Walk-Role", "")
    if r == "owner" and "checker" in roles and unit == "packs":
        return dict(user="walkowner", role="checker"), None
    return None, (jsonify(ok=False, error="not_permitted"), 403)


DBC = {}


def getdb():
    if "c" not in DBC:
        DBC["c"] = sqlite3.connect(FIN, check_same_thread=False)
        DBC["c"].row_factory = sqlite3.Row
    return DBC["c"]


pp.init(app, getdb, require, unit="packs")
cl = app.test_client()
H = lambda r: {"X-Walk-Role": r}                                          # noqa: E731
for role, want in (("owner", 200), ("maker", 403), ("viewer", 403), ("", 403)):
    rp = cl.get("/finance/console/patients", headers=H(role))
    ra = cl.get("/finance/console/api/patients", headers=H(role))
    body = rp.get_data(as_text=True)
    ok("role %-6s: the page %d, its reading %d" % (role or "none", want, want), rp.status_code == want and ra.status_code == want
       and ((want != 200) or ("wordsCard" in body and "becameTable" in body)), (rp.status_code, ra.status_code))
rx = cl.post("/finance/console/api/patients/place", headers=H("viewer"), json=dict(words=["WALKWORD ZZQ"], std="Trauma / Fracture"))
ok("a viewer's Place is refused (403), nothing written", rx.status_code == 403 and getdb().execute("SELECT COUNT(*) FROM dx_term_map").fetchone()[0] == 0)
rx = cl.post("/finance/console/api/patients/place", headers=H("owner"), data="words=WALKWORD+ZZQ&std=Trauma", content_type="application/x-www-form-urlencoded")
ok("a form post (not JSON) is refused (400)", rx.status_code == 400)
rx = cl.post("/finance/console/api/patients/place", headers=H("owner"), json=dict(words=["WALKWORD ZZQ"], std="Not a group"))
ok("a group not in his taxonomy is refused", rx.status_code == 400 and "Choose a group" in (rx.get_json() or {}).get("why", ""))
rx = cl.post("/finance/console/api/patients/place", headers=H("owner"), json=dict(words=["KNEE OSTEOARTHRITIS"], std="Trauma / Fracture"))
ok("a word the taxonomy already knows cannot be placed", rx.status_code == 400 and getdb().execute("SELECT COUNT(*) FROM dx_term_map").fetchone()[0] == 0)
rx = cl.post("/finance/console/api/patients/place", headers=H("owner"),
             json=dict(words=["FRACRURE SHAFT HUMERUS", "FRACRURE SHAFT HUMERUS (Comminuted right)"], std="Trauma / Fracture"))
j = rx.get_json() or {}
ok("Place: 2 words, 2 visits moved, the reading built afresh", rx.status_code == 200 and (j.get("placed"), j.get("moved"), j.get("rebuilt")) == (2, 2, True), j)
dv = getdb().execute("SELECT std_dx, category FROM dx_visit WHERE patient_uid IN ('u1','u2') ORDER BY patient_uid").fetchall()
ok("both visits now Trauma / Fracture, group Trauma", [tuple(r) for r in dv] == [("Trauma / Fracture", "Trauma")] * 2, [tuple(r) for r in dv])
ra = cl.get("/finance/console/api/patients", headers=H("owner")).get_json() or {}
W2 = (ra.get("reading") or {}).get("words") or {}
ok("the new reading: 3 words left, 2 placed, by walkowner's tap", (W2.get("n"), len(W2.get("placed") or [])) == (3, 2), (W2.get("n"), W2.get("placed")))
g1 = ((ra.get("reading") or {}).get("groups") or {})
ok("the groups moved with it", json.dumps(g1, sort_keys=True) != json.dumps(g0, sort_keys=True))
rx = cl.post("/finance/console/api/patients/place", headers=H("owner"), json=dict(words=["FRACRURE SHAFT HUMERUS"], std="Trauma / Fracture"))
ok("the same word again: 'placed already' (400)", rx.status_code == 400 and "already" in (rx.get_json() or {}).get("why", ""))
mp = getdb().execute("SELECT term, set_by FROM dx_term_map ORDER BY term").fetchall()
ok("dx_term_map holds the two words in dx_feed's own key, set_by walkowner", [tuple(r) for r in mp] ==
   [("FRACRURE SHAFT HUMERUS", "walkowner"), ("FRACRURE SHAFT HUMERUS (COMMINUTED RIGHT)", "walkowner")], [tuple(r) for r in mp])
rx = cl.post("/finance/console/api/patients/unplace", headers=H("viewer"), json=dict(term="FRACRURE SHAFT HUMERUS"))
ok("a viewer's Undo is refused", rx.status_code == 403)
rx = cl.post("/finance/console/api/patients/unplace", headers=H("owner"), json=dict(term="FRACRURE SHAFT HUMERUS"))
j = rx.get_json() or {}
ok("Undo: 1 word out, 1 visit back", rx.status_code == 200 and (j.get("removed"), j.get("moved")) == (1, 1), j)
ok("u1 back to Unclassified, u2 stays Trauma", [r[0] for r in getdb().execute("SELECT std_dx FROM dx_visit WHERE patient_uid IN ('u1','u2') ORDER BY patient_uid")] == [UN, "Trauma / Fracture"])
rx = cl.post("/finance/console/api/patients/unplace", headers=H("owner"), json=dict(term="NOT PLACED"))
ok("Undo of a word not placed: 400", rx.status_code == 400)
# review 1: a re-read that fails half way takes the tap back whole
snap = lambda: ([tuple(r) for r in getdb().execute("SELECT * FROM dx_term_map ORDER BY term")],              # noqa: E731
                [tuple(r) for r in getdb().execute("SELECT patient_uid, visit_date, std_dx, category FROM dx_visit ORDER BY 1, 2")])
s0 = snap()
real = dx_feed.reclassify


def half(con):
    con.execute("UPDATE dx_visit SET std_dx='HALF', category='HALF' WHERE patient_uid='u6'")
    raise RuntimeError("walk: fails half way")


dx_feed.reclassify = half
rx = cl.post("/finance/console/api/patients/place", headers=H("owner"), json=dict(words=["CELLULITIS RIGHT LEG", "CELLULITIS LEFT LEG"], std="Infection / Osteomyelitis"))
ok("a re-read failing half way: 400 'Not done', the map and every visit as before", rx.status_code == 400 and "Not done" in (rx.get_json() or {}).get("why", "") and snap() == s0, rx.get_json())
rx = cl.post("/finance/console/api/patients/unplace", headers=H("owner"), json=dict(term="FRACRURE SHAFT HUMERUS (COMMINUTED RIGHT)"))
ok("... and for an Undo: the word stays placed", rx.status_code == 400 and snap() == s0, rx.get_json())
dx_feed.reclassify = real
# review 2: a reading that cannot be built at once is marked old, and the answer says so
realb = pp.build
pp.build = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("walk: no build"))
rx = cl.post("/finance/console/api/patients/place", headers=H("owner"), json=dict(words=["WALKWORD ZZQ"], std="General Musculoskeletal Pain"))
j = rx.get_json() or {}
st = json.load(open(os.environ["PATIENTS_READING"]))
ok("the reading could not be built: placed, rebuilt False, the stored reading marked old (built_epoch 0)", rx.status_code == 200 and j.get("rebuilt") is False
   and st.get("built_epoch") == 0, (j, st.get("built_epoch")))
pp.build = realb
cl.post("/finance/console/api/patients/unplace", headers=H("owner"), json=dict(term="WALKWORD ZZQ"))
ok("no other table touched by the taps", others(FIN) == before)
# ------------------------------------------------------------------ the page's own script under node
if NODE:
    rd = (cl.get("/finance/console/api/patients", headers=H("owner")).get_json() or {}).get("reading") or {"months": []}
    rp = os.path.join(WORK, "reading.json")
    json.dump(rd, open(rp, "w"))
    try:
        jsr = json.loads(subprocess.run([NODE, os.path.join(_ME or ".", "walk_s862_js.js"), os.path.join(CODE, "patients_page.html"), rp],
                                        capture_output=True, text=True, timeout=60).stdout or "{}")
    except Exception as e:                                              # noqa: BLE001
        jsr = dict(errors=[str(e)])
    ok("page script: every month draws without an error", jsr.get("errors") == [] and rd["months"] and all(("page_" + m["ym"]) in jsr for m in rd["months"]), jsr.get("errors"))
    w = jsr.get("words", "")
    ok("words card: rows with a group list, the suggestion selected, Place buttons, the Placed list with Undo",
       'class="words"' in w and 'selected>Infection / Osteomyelitis' in w and w.count('class="place"') == 3 and 'class="unplace"' in w, w[:200])
    ok("words card: the sides drawn ticked under the word", 'type="checkbox" checked' in w)
    ok("words card: a message is escaped", "walk &lt;b&gt;msg&lt;/b&gt;" in jsr.get("words_msg", ""))
    b = jsr.get("became", "")
    ok("became table: months, a tap opens bec:2026-10 and rf:2026-10", "Enquiry callers who became patients" in b and 'data-k="bec:2026-10"' in b and 'data-k="rf:2026-10"' in b, b[:200])
    ok("Google card says it was read by the server from the mail of 05-Nov", "read by the server from Google" in jsr.get("google", "") and "05-Nov" in jsr.get("google", ""))
    ok("'Still to come' gone once Google is read by the server", rd["months"] and all("Still to come" not in jsr.get("page_" + m["ym"], "x Still to come") for m in rd["months"]))
    ok("the desk card carries the became table (Oct)", "Enquiry callers who became patients" in jsr.get("page_2026-10", ""))
else:
    print("SKIP  the page's own script (no node on this machine -- it ran where the kit was built: WALK 55/55 there)")
print("WALK %d/%d" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
