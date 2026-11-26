#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s960.py -- S960_EVENING_CHECK's walk, on a made-up database and made-up exports (no real name, number or clinic ID).
    python3 walk_s960.py <code_dir>      code_dir holds the finance modules (the live set with the kit's TO files laid over them)
The last line is ALL PASS or N FAIL. CONTROL: the same walk on the FROM files (no evening_check.py) must go red at T1."""
import csv
import datetime as dt
import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time

CODE = os.path.abspath(sys.argv[1])
TMP = tempfile.mkdtemp(prefix="w960_")
DB = os.path.join(TMP, "finance.db")
PORTAL = os.path.join(TMP, "portal")
PUSHLOG = os.path.join(TMP, "pushes.jsonl")
D = "2026-11-26"                                              # a Thursday
os.makedirs(PORTAL)
with open(os.path.join(PORTAL, "callback_clock.py"), "w") as fh:  # the clock's send road, as a stub that writes what it was given
    fh.write('''import json, os
def cfg(name, default=""):
    v = os.environ.get(name, "").strip()
    return v or default
def get_pusher(p=None):
    return p or (lambda w, payload: (1, 0))
def send(pusher, who, title, body, url, tag):
    with open(os.environ["W960_PUSHLOG"], "a") as fh:
        fh.write(json.dumps(dict(who=list(who), title=title, body=body, urls=[url(w) for w in who], tag=tag)) + "\\n")
    return (len(who), 0, 0)
''')
os.environ.update(EVCHK_NOW=D + "T19:30:00", SLIP_NOW=D + "T19:30:00", EVCHK_LIVE_DB=DB, RING_PORTAL_DIR=PORTAL, W960_PUSHLOG=PUSHLOG,
                  EVCHK_PY=sys.executable, DOCTERZ_EXPORT_STORE=os.path.join(TMP, "store"), FINANCE_DB=DB)
for k in ("EVCHK_ON", "EVCHK_TO", "EVCHK_FROM", "EVCHK_SUN_FROM", "EVCHK_SPAWN"):
    os.environ.pop(k, None)
sys.path.insert(0, CODE)
sys.dont_write_bytecode = True

RES = []


def ok(key, cond, note=""):
    RES.append((key, bool(cond)))
    print("%s  %s%s" % ("PASS" if cond else "FAIL", key, ("  -- " + note) if (note and not cond) else ""))


import docterz_pickup as DP                                    # noqa: E402
import slip_log as SL                                          # noqa: E402
import slip_adjust as SA                                       # noqa: E402
import docterz_ingest as DI                                    # noqa: E402
import dx_feed as DX                                           # noqa: E402
import not_in_docterz as NID                                   # noqa: E402
try:
    import evening_check as EC                                 # noqa: E402
except Exception as ex:                                        # noqa: BLE001 -- the control has none
    EC = None
    print("INFO evening_check not importable: %s" % ex)

HEAD = ["Sr No", "Patient UID", "Patient Name", "Clinic Specific Id", "Mobile", "Consultation Date", "Consultation Amount",
        "Consultation Discount", "Laboratory Amount", "Laboratory Discount", "Radiology Amount", "Radiology Discount",
        "Procedure Amount", "Procedure Discount", "Amount collected", "Mode Of Payment"]


def export_bytes(rows, salt=""):
    b = io.StringIO()
    w = csv.writer(b)
    w.writerow(HEAD)
    w.writerow(["Dr. Manoj Agarwal Clinic"] + [""] * (len(HEAD) - 1))
    for i, r in enumerate(rows, 1):
        dd = dt.date.fromisoformat(r.get("day", D)).strftime("%d-%m-%Y")
        w.writerow([i, "TESTUID%04d" % i, r.get("name", "Test Person"), r["cid"], "x", dd, r.get("cons", 0), 0, r.get("lab", 0), 0,
                    r.get("rad", 0), 0, r.get("proc", 0), r.get("procd", 0), r.get("cons", 0), "Cash"])
    if salt:
        w.writerow(["", "", salt] + [""] * (len(HEAD) - 3))
    return b.getvalue().encode("utf-8")


def fresh():
    for p in (DB, PUSHLOG):
        if os.path.exists(p):
            os.remove(p)
    shutil.rmtree(os.path.join(TMP, "store"), ignore_errors=True)
    SL._schema_done = False
    NID._done = False
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    SL.ensure(con)
    con.executescript(SA.SCHEMA)
    DP.ensure(con)
    con.executescript(DI.SCHEMA)
    con.executescript(DX.DDL)
    con.execute("CREATE TABLE IF NOT EXISTS patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT, phone_last4 TEXT, merged_into TEXT)")
    for i in range(5):                                         # the usual fee: Rs 600 most days
        con.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode, shift) VALUES (?,?,?,?,?,?,?,?)",
                    ("2026-11-2%d" % i, "consult", 1, "x", "1", 60000, "Cash", ""))
    con.commit()
    return con


SN = {"opd": 100, "xp": 200}


def slip(con, series, cid, day=D, state="ok", noid="", name="", items=()):
    SN[series] += 1
    cur = con.execute("INSERT INTO slip (series, slip_no, day, clinic_id, no_id_name, name_seen, state, logged_by, logged_at) "
                      "VALUES (?,?,?,?,?,?,?,?,?)", (series, SN[series], day, cid, noid, name, state, "shavez", day + " 10:00:00"))
    sid = cur.lastrowid
    for j, (kind, nm, price, disc) in enumerate(items):
        con.execute("INSERT INTO slip_item (slip_id, kind, name, price_p, discount_p, sort) VALUES (?,?,?,?,?,?)", (sid, kind, nm, price, disc, j))
    con.commit()
    return sid


def scenario(con):
    s = {}
    s["in_opd"] = slip(con, "opd", "501", name="Test Person A")
    s["miss_opd"] = slip(con, "opd", "502", name="Test Person B")
    s["in_xr"] = slip(con, "xp", "501", items=[("xray", "Knee AP", 50000, 0)])
    s["miss_xr"] = slip(con, "xp", "503", name="Test Person C", items=[("xray", "Spine", 70000, 0)])
    s["in_proc"] = slip(con, "xp", "504", items=[("proc", "Dressing", 30000, 0)])
    s["radd"] = slip(con, "opd", "505")
    con.execute("INSERT INTO slip_adjust (slip_id, kind, day, made_by, made_at, state, cancel_how) VALUES (?,?,?,?,?,?,?)",
                (s["radd"], "cancel", D, "shavez", D + " 11:00:00", "pending", "returned"))
    s["noid"] = slip(con, "opd", "", noid="Walk In")
    s["letters"] = slip(con, "opd", "AB12")
    s["marked"] = slip(con, "opd", "506")
    s["undone"] = slip(con, "opd", "507", name="Test Person D")
    NID.ensure(con)
    con.execute("INSERT INTO nid_mark (slip_id, kind, act, amount_p, day, who, at) VALUES (?,?,?,?,?,?,?)", (s["marked"], "opd", "free", 60000, D, "manoj", D + " 12:00:00"))
    con.execute("INSERT INTO nid_mark (slip_id, kind, act, amount_p, day, who, at, state) VALUES (?,?,?,?,?,?,?,?)",
                (s["undone"], "opd", "free", 60000, D, "manoj", D + " 12:00:00", "undone"))
    s["free_line"] = slip(con, "xp", "508", items=[("xray", "Hand", 40000, 40000)])
    s["rejected"] = slip(con, "xp", "509", name="Test Person E", items=[("xray", "Wrist", 40000, 40000)])
    iid = con.execute("SELECT id FROM slip_item WHERE slip_id=?", (s["rejected"],)).fetchone()[0]
    con.execute("INSERT INTO slip_adjust (slip_id, item_id, kind, amount_p, day, made_by, made_at, state) VALUES (?,?,?,?,?,?,?,?)",
                (s["rejected"], iid, "free", 40000, D, "shavez", D + " 11:00:00", "rejected"))
    s["dx"] = slip(con, "opd", "510")
    con.execute("INSERT INTO dx_visit (patient_uid, visit_date, clinic_id, updated_at) VALUES (?,?,?,?)", ("TESTUIDDX", D + " 10:00", "510", D))
    s["cancelled"] = slip(con, "opd", "511", state="cancelled")
    s["yesterday"] = slip(con, "opd", "512", day="2026-11-25")
    s["rad"] = slip(con, "xp", "513", items=[("xray", "Chest", 40000, 0)])
    con.commit()
    return s


BASE = [dict(cid="501.0", cons=600, lab=500), dict(cid="503", cons=0), dict(cid="504", cons=600, procd=300), dict(cid="513", rad=400),
        dict(cid="502", day="2026-11-25", cons=600), dict(cid="506", cons=600)]
FULL = BASE + [dict(cid="502", cons=600), dict(cid="503", lab=700), dict(cid="507", cons=600), dict(cid="509", rad=400)]
EXPECT = None


def take(con, raw, ist_hhmm, fid=None):
    """Take an export through docterz_pickup.take (no spawn), then set its taken time (the walk's clock)."""
    os.environ["EVCHK_SPAWN"] = "0"
    f = {"id": fid or ("reception:%d" % (len(raw) * 7 + int(ist_hhmm.replace(":", "")))), "name": "x.csv",
         "modifiedTime": (dt.datetime.fromisoformat(D + "T" + ist_hhmm) - dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S.000Z")}
    kind, day, n, st, note = DP.take(con, f, raw)
    os.environ.pop("EVCHK_SPAWN", None)
    r = con.execute("SELECT id FROM docterz_export WHERE drive_id=? AND drive_mtime=?", (f["id"], f["modifiedTime"])).fetchone()
    con.execute("UPDATE docterz_export SET taken_at=? WHERE id=?", (D + " " + ist_hhmm + ":05", r[0]))
    con.commit()
    return r[0], st


def pushes():
    if not os.path.exists(PUSHLOG):
        return []
    return [json.loads(x) for x in open(PUSHLOG) if x.strip()]


def run():
    global EXPECT
    # ---------------------------------------------------------------- T: the take starts the check (the spawn, a real process)
    con = fresh()
    s = scenario(con)
    real_now = DP.now
    DP.now = lambda: dt.datetime(2026, 11, 26, 19, 30, 5)
    f = {"id": "reception:spawn1", "name": "x.csv", "modifiedTime": "2026-11-26T14:00:00.000Z"}
    t0 = time.time()
    kind, day, n, st, note = DP.take(con, f, export_bytes(BASE))
    took = time.time() - t0
    got = []
    for _ in range(60):
        got = pushes()
        if got:
            break
        time.sleep(0.25)
    ok("T1 the take starts the evening check: a push comes from its own process", len(got) == 1 and got[0]["title"].startswith("4 parchi"),
       "pushes %s" % [g.get("title") for g in got])
    ok("T2 the take does not wait for it (under 3 s) and stays 'current'", took < 3 and st == "current", "%.2fs %s" % (took, st))
    logf = os.path.join(CODE, "logs", "evening_check.log")
    ok("T3 the process wrote its line to logs/evening_check.log", os.path.exists(logf) and "missing 4" in open(logf).read())
    os.environ["EVCHK_SPAWN"] = "0"
    DP.take(con, {"id": "reception:spawn2", "name": "x.csv", "modifiedTime": "2026-11-26T14:05:00.000Z"}, export_bytes(FULL))
    os.environ.pop("EVCHK_SPAWN", None)
    time.sleep(2)
    ok("T4 EVCHK_SPAWN=0: nothing started", len(pushes()) == 1)
    DP.take(con, {"id": "reception:spawn3", "name": "x.csv", "modifiedTime": "2026-11-26T14:06:00.000Z"}, export_bytes(FULL, "a"), dry=True)
    time.sleep(1.5)
    ok("T5 a dry take starts nothing", len(pushes()) == 1)
    src = os.path.join(CODE, "evening_check.py")
    if os.path.exists(src):
        os.rename(src, src + ".away")
    try:
        k2, d2, n2, st2, _ = DP.take(con, {"id": "reception:spawn4", "name": "x.csv", "modifiedTime": "2026-11-26T14:07:00.000Z"}, export_bytes(FULL, "b"))
    finally:
        if os.path.exists(src + ".away"):
            os.rename(src + ".away", src)
    time.sleep(1.5)
    ok("T6 evening_check.py absent: the take still succeeds, nothing pushed", st2 == "current" and len(pushes()) == 1)
    DP.take(con, {"id": "drive:fu1", "name": "f.csv", "modifiedTime": "2026-11-26T14:08:00.000Z"},
            b"Appointment ID,Mobile No,Due Date\n1,x,27-11-2026\n")
    time.sleep(1.5)
    ok("T7 a follow-up log starts nothing", len(pushes()) == 1)
    DP.now = real_now
    if EC is None:
        return
    # ---------------------------------------------------------------- R: the reader and the rules
    con = fresh()
    s = scenario(con)
    carried = EC.read_export(export_bytes(BASE), D)
    ok("R1 the reader: today's rows only, the clinic ID as digits, X-ray by lab or radiology, procedure by its discount",
       carried == {"501": {"opd", "xray"}, "503": {"opd"}, "504": {"opd", "proc"}, "513": {"opd", "xray"}, "506": {"opd"}}, str(carried))
    rawj = export_bytes([dict(cid="530", lab=0, cons=600)])
    assert rawj.count(b"TESTUID0001") == 1
    junk = EC.read_export(rawj.replace(b"TESTUID0001", b"Credit Card"), D)
    ok("R1b a row whose Patient UID is not UID-shaped (the report's footer) is no patient", junk == {}, str(junk))
    rawz = export_bytes([dict(cid="531", cons=600)])
    assert rawz.count(b",600,0,0,0,0,0,0,0,600") == 1           # the walk's own edit must land (a discount-only X-ray)
    dz = EC.read_export(rawz.replace(b",600,0,0,0,0,0,0,0,600", b",600,0,0,500,0,0,0,0,600"), D)
    ok("R1c an X-ray with only a discount is not an X-ray line (revenue.py: Xray > 0)", dz == {"531": {"opd"}}, str(dz))
    ok("R2 a file that is not a consultation report reads as None", EC.read_export(b"a,b\n1,2\n", D) is None and EC.read_export(b"", D) is None)
    rows = EC.missing_slips(con, D, carried)
    got = sorted((r["slip_id"], r["kind"]) for r in rows)
    EXPECT = sorted([(s["miss_opd"], "opd"), (s["miss_xr"], "xray"), (s["undone"], "opd"), (s["rejected"], "xray")])
    ok("R3 exactly the four missing: OPD not carried, X-ray row with no X-ray, an undone answer, a rejected chhoot", got == EXPECT, str(got))
    amt = {(r["slip_id"], r["kind"]): r["amount_p"] for r in rows}
    ok("R4 the amounts: the usual fee for OPD, the net for X-ray (rejected chhoot = full rate)",
       amt.get((s["miss_opd"], "opd")) == 60000 and amt.get((s["miss_xr"], "xray")) == 70000 and amt.get((s["rejected"], "xray")) == 40000, str(amt))
    ok("R5 the name: the slip's own", any(r["name"] == "Test Person B" for r in rows))
    con.execute("UPDATE slip SET name_seen='' WHERE id=?", (s["miss_opd"],))
    con.execute("INSERT INTO patient_ref (clinic_id, name, phone_last4) VALUES ('502', 'Master Name', '0000')")
    con.commit()
    ok("R6 the name: else the master's", any(r["name"] == "Master Name" for r in EC.missing_slips(con, D, carried)))
    ok("R7 everything carried: nothing missing", EC.missing_slips(con, D, EC.read_export(export_bytes(FULL), D)) == [])
    # the same answer as the owner's own list, when the tracker's lines carry the same export
    con.execute("INSERT INTO clinic_day_revenue (business_date, source_file, source_id, source_mtime, taken_at, cons_count, cons_amount_p, xray_count, "
                "xray_amount_p, proc_count, proc_amount_p, total_count, total_amount_p, morning, evening, free_revisits, free_concession, "
                "f93_phantom_rows, tender_json, sheet_total_p, sheet_cash_p, sheet_online_p, variance_note) "
                "VALUES (?, 'w', 'w', 'w', 'w', 0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',0,0,0,'')", (D,))
    lines = [("consult", "501"), ("xray", "501"), ("revisit", "503"), ("consult", "504"), ("proc", "504"), ("revisit", "513"),
             ("xray", "513"), ("consult", "506")]          # the Day Revenue sheet of BASE, written out by hand (not from the reader)
    for sn, (sec, c) in enumerate(lines, 1):
        con.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode, shift) VALUES (?,?,?,?,?,?,?,?)",
                    (D, sec, sn, "x", c, 0 if sec == "revisit" else 100, "Cash", ""))
    con.commit()
    theirs = sorted((r["slip_id"], r["kind"], r["amount_p"]) for r in NID.rows(con, D, D) if not r["mark"])
    mine = sorted((r["slip_id"], r["kind"], r["amount_p"]) for r in EC.missing_slips(con, D, carried))
    ok("R8 the same slips and amounts as his 'Slips not in Docterz' list (not_in_docterz.rows) on the same export", theirs == mine,
       "his %s mine %s" % (theirs, mine))
    # ---------------------------------------------------------------- P: the pushes, once per export
    con = fresh()
    s = scenario(con)
    e0, _ = take(con, export_bytes(BASE, "early"), "16:30")
    os.environ["EVCHK_NOW"] = D + "T16:40:00"
    ok("P1 an export before 17:00 is left alone", EC.on_export(con, e0).startswith("skip") and not pushes())
    os.environ["EVCHK_NOW"] = D + "T19:31:00"
    ok("P1b ... and stays alone later too (taken before the evening)", EC.on_export(con, e0).startswith("skip") and not pushes())
    e1, _ = take(con, export_bytes(BASE), "19:30")
    r1 = EC.on_export(con, e1)
    p = pushes()
    ok("P2 slips missing: ONE push '4 parchi Docterz mein nahi' with the names", r1.startswith("missing 4") and len(p) == 1
       and p[0]["title"] == "4 parchi Docterz mein nahi" and "Test Person B" in p[0]["body"] and "Test Person C" in p[0]["body"], "%s %s" % (r1, p))
    ok("P3 to Shavez (the desk) and reception (the portal), one tag for the day",
       p and p[0]["who"] == ["shavez", "reception"] and p[0]["urls"] == ["/finance/slips/desk", "/portal"] and p[0]["tag"] == "evening-" + D)
    ok("P4 the same export again: nothing more", EC.on_export(con, e1).startswith("skip: already") and len(pushes()) == 1)
    row = con.execute("SELECT * FROM evening_check_push WHERE export_id=?", (e1,)).fetchone()
    ok("P5 its record: missing 4, the slip ids and kinds, no name", row["missing"] == 4 and row["outcome"] == "missing"
       and "Test" not in row["slips"] and row["slips"].count(":") == 4 and "sent 2" in row["sent"])
    e2, _ = take(con, export_bytes(FULL), "19:40")
    os.environ["EVCHK_NOW"] = D + "T19:41:00"
    r2 = EC.on_export(con, e2)
    p = pushes()
    ok("P6 a corrected export: '✓ Sab parchi Docterz mein' -- kaam poora, with its time", r2.startswith("cleared 0") and len(p) == 2
       and p[1]["title"] == "✓ Sab parchi Docterz mein" and "19:40" in p[1]["body"] and "kaam poora" in p[1]["body"], "%s %s" % (r2, p[-1:]))
    e3, _ = take(con, export_bytes(FULL, "again"), "19:50")
    ok("P7 another clean export after the all-clear: nothing", EC.on_export(con, e3).startswith("quiet") and len(pushes()) == 2)
    ok("P8 an export no longer current: left alone", EC.on_export(con, e1).startswith("skip"))
    con = fresh()
    s = scenario(con)
    e1, _ = take(con, export_bytes(FULL), "20:10")
    os.environ["EVCHK_NOW"] = D + "T20:11:00"
    r = EC.on_export(con, e1)
    p = pushes()
    ok("P9 the first export clean before the closing: '✓ 26-Nov: sab parchi Docterz mein' -- kuch nahi karna (no 'PC band')", r.startswith("clean 0")
       and len(p) == 1 and p[0]["title"] == "✓ 26-Nov: sab parchi Docterz mein" and p[0]["body"] == "Kuch nahi karna", "%s %s" % (r, p))
    con = fresh()
    s = scenario(con)
    e1, _ = take(con, export_bytes(FULL), "21:10")
    os.environ["EVCHK_NOW"] = D + "T21:11:00"
    r = EC.on_export(con, e1)
    p = pushes()
    ok("P9b ... after the closing (20:30): 'PC band kar sakte hain'", p and "PC band kar sakte hain" in p[0]["body"], "%s %s" % (r, p))
    # a newer export taken while the check was working: the stale answer never goes out
    con = fresh()
    s = scenario(con)
    os.environ["EVCHK_NOW"] = D + "T19:31:00"
    e1, _ = take(con, export_bytes(BASE), "19:30")
    real_ms = EC.missing_slips
    hold = {}

    def racing(con_, day_, car_):
        if not hold:
            hold["e2"] = take(con_, export_bytes(FULL), "19:31")[0]
        return real_ms(con_, day_, car_)
    EC.missing_slips = racing
    r = EC.on_export(con, e1)
    EC.missing_slips = real_ms
    ok("X1 a newer export lands during the check: 'superseded', nothing pushed", r.startswith("superseded") and not pushes(), r)
    r = EC.on_export(con, hold["e2"])
    ok("X2 ... and the newer one is judged as the day's first (all in)", r.startswith("clean 0") and len(pushes()) == 1, r)
    import fcntl                                               # noqa: PLC0415
    lf = os.path.join(TMP, ".evening_check.lock")
    with open(lf, "a") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        okl = True
        fcntl.flock(fh, fcntl.LOCK_UN)
    ok("X3 the check's lock sits beside the database and is let go", os.path.exists(lf) and okl)
    # the sweep: the every-minute safety net
    con = fresh()
    s = scenario(con)
    os.environ["EVCHK_NOW"] = D + "T19:00:00"
    ok("W1 no evening export: the sweep does nothing", EC.sweep(con) == "")
    e1, _ = take(con, export_bytes(BASE), "19:30")
    os.environ["EVCHK_NOW"] = D + "T19:32:00"
    r = EC.sweep(con)
    ok("W2 an export no check judged: the sweep judges it (one push)", r.startswith("swept: missing 4") and len(pushes()) == 1, r)
    ok("W3 the sweep again: nothing", EC.sweep(con) == "" and len(pushes()) == 1)
    e2, _ = take(con, export_bytes(FULL), "19:40")
    con.execute("INSERT INTO evening_check_push (export_id, day, at) VALUES (?,?,?)", (e2, D, D + " 19:40:10"))
    con.commit()
    os.environ["EVCHK_NOW"] = D + "T19:41:00"
    import fcntl                                               # noqa: PLC0415
    import threading                                           # noqa: PLC0415
    hold_fh = open(os.path.join(TMP, ".evening_check.lock"), "a")
    fcntl.flock(hold_fh, fcntl.LOCK_EX)                        # a check at work holds the lock
    out = {}
    con2 = sqlite3.connect(DB, timeout=10, check_same_thread=False)
    con2.row_factory = sqlite3.Row
    th = threading.Thread(target=lambda: out.setdefault("r", EC.sweep(con2)))
    th.start()
    th.join(1.5)
    waited = th.is_alive() and not pushes()[1:]
    con.execute("UPDATE evening_check_push SET outcome='cleared' WHERE export_id=?", (e2,))   # ... and gives its answer
    con.commit()
    fcntl.flock(hold_fh, fcntl.LOCK_UN)
    hold_fh.close()
    th.join(10)
    ok("W4 a check at work holds the lock: the sweep waits, then sees its answer and does nothing", waited and out.get("r") == ""
       and len(pushes()) == 1, str(out))
    con.execute("UPDATE evening_check_push SET outcome='claimed' WHERE export_id=?", (e2,))   # a check that died after its claim
    con.commit()
    r = EC.sweep(con)
    ok("W5 a check that died (its claim left, no lock held): judged again -- the all-clear, once", r.startswith("swept: cleared 0")
       and len(pushes()) == 2 and EC.sweep(con) == "", r)
    # ---------------------------------------------------------------- C: the clock's REAL send road (the live callback_clock.py)
    real_cc = os.environ.get("W960_REAL_CC", "")
    if real_cc:
        import importlib.util                                  # noqa: PLC0415
        spec = importlib.util.spec_from_file_location("cc_real_w960", real_cc)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        seen = []
        EC.CC_MOD, EC.PUSHER = mod, (lambda w, payload: (seen.append((w, payload)) or (1, 0)))
        saved = os.environ.pop("PORTAL_STAFF_NTFY_URL", None)
        try:
            res, why = EC._send(["shavez", "reception"], "3 parchi Docterz mein nahi", "Test Person B", "evening-" + D)
        finally:
            EC.CC_MOD, EC.PUSHER = None, None
            if saved is not None:
                os.environ["PORTAL_STAFF_NTFY_URL"] = saved
        ok("C1 the live clock's send(): both logins pushed, desk and portal landings, the day's tag",
           res == (2, 0, 0) and [w for w, _p in seen] == ["shavez", "reception"] and seen[0][1]["url"] == "/finance/slips/desk"
           and seen[1][1]["url"] == "/portal" and seen[0][1]["tag"] == "evening-" + D and seen[0][1]["title"].startswith("3 parchi"),
           "%s %s %s" % (res, why, seen[:1]))
    else:
        print("INFO C1 skipped (no W960_REAL_CC)")
    # ---------------------------------------------------------------- K: the desk
    con = fresh()
    s = scenario(con)
    os.environ["EVCHK_NOW"] = D + "T18:00:00"
    ok("K1 no evening export yet: the desk shows no box", EC.panel_html(con) == "")
    e1, _ = take(con, export_bytes(BASE), "19:30")
    os.environ["EVCHK_NOW"] = D + "T19:31:00"
    ph = EC.panel_html(con)
    ok("K2 the box: 'Aaj ki parchi jo Docterz mein nahi: 4', four 'Paise nahi liye', the export time and road",
       "Aaj ki parchi jo Docterz mein nahi: 4" in ph and ph.count("Paise nahi liye") == 4 and "19:30" in ph and "seedha server par" in ph, ph[:300])
    ok("K3 his English view", "Slips of today not in Docterz: 4" in EC.panel_html(con, eng=True) and "Money not taken" in EC.panel_html(con, eng=True))
    from flask import Flask                                    # noqa: PLC0415
    import parchi_desk as PD                                   # noqa: PLC0415
    app = Flask("w960")
    who = {"u": {"user": "shavez", "roles": ["maker"]}}
    audits = []

    def req(*roles, unit=None):
        if who["u"] is None:
            return None, ("no", 403)
        return who["u"], None

    def aud(con_, table, rid, action, before=None, after=None, who=None):
        audits.append((table, action, who))

    PD.init(app, lambda: con, req, aud, unit="slips")
    rules = {r.rule for r in app.url_map.iter_rules()}
    ok("K4 the desk mounts the two doors", EC.API in rules and EC.API + "/free" in rules)
    c = app.test_client()
    j = c.get(EC.API).get_json()
    ok("K5 GET the box: ok, the same box", j and j["ok"] and "Docterz mein nahi: 4" in j["html"])
    j = c.post(EC.API + "/free", json={"slip_id": s["miss_opd"], "kind": "opd"}).get_json()
    m = con.execute("SELECT * FROM nid_mark WHERE slip_id=? AND state='live'", (s["miss_opd"],)).fetchone()
    ok("K6 'Paise nahi liye': ok; nid_mark 'free' by shavez; audited", j and j["ok"] and m and m["act"] == "free" and m["who"] == "shavez"
       and m["amount_p"] == 60000 and audits and audits[-1][2] == "shavez", str(j))
    ok("K7 the slip leaves the box (3 left)", "Docterz mein nahi: 3" in c.get(EC.API).get_json()["html"])
    ok("K8 his list sees the same answer", (s["miss_opd"], "opd") in NID.marks_for_day(con, D) and NID.marks_for_day(con, D)[(s["miss_opd"], "opd")] == "free")
    j = c.post(EC.API + "/free", json={"slip_id": s["miss_opd"], "kind": "opd"}).get_json()
    ok("K9 the same tap again: refused, nothing written", j and not j["ok"] and con.execute("SELECT COUNT(*) FROM nid_mark WHERE slip_id=?", (s["miss_opd"],)).fetchone()[0] == 1)
    j = c.post(EC.API + "/free", json={"slip_id": s["in_opd"], "kind": "opd"}).get_json()
    ok("K10 a slip not on the list: refused", j and not j["ok"])
    j = c.post(EC.API + "/free", json={"slip_id": "x", "kind": "zzz"}).get_json()
    ok("K11 nonsense: refused", j and not j["ok"])
    who["u"] = None
    ok("K12 no desk login: 403 on both doors", c.get(EC.API).status_code == 403 and c.post(EC.API + "/free", json={}).status_code == 403)
    who["u"] = {"user": "shavez", "roles": ["maker"]}
    with app.test_request_context("/finance/slips/desk"):
        pg = PD.page()
    ok("K13 the desk page carries the box at the top, today", isinstance(pg, str) and '<div id="missing"></div><div id="s960w" data-today="%s">' % D in pg
       and "Docterz mein nahi: 3" in pg, str(pg)[:200])
    with app.test_request_context("/finance/slips/desk?day=2026-11-25"):
        pg2 = PD.page()
    ok("K14 an earlier day on the desk: the box is today's, and the page's day picker hides it (data-today, the picker's change)",
       isinstance(pg2, str) and 'data-today="%s"' % D in pg2 and 'getElementById("day")' in pg2 and 'addEventListener("change",vis)' in pg2)
    ok("K14b the box is not hidden before the page fills its day picker (an empty picker hides nothing)", "s&&s.value&&T&&" in pg2
       and 'addEventListener("DOMContentLoaded",vis)' in pg2)
    e2, _ = take(con, export_bytes(FULL), "19:45")
    os.environ["EVCHK_NOW"] = D + "T19:46:00"
    ok("K15 after the corrected export the box says all is in", "✓ Aaj ki sab parchi Docterz mein" in c.get(EC.API).get_json()["html"])
    real = EC.check
    EC.check = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    with app.test_request_context("/finance/slips/desk"):
        pg3 = PD.page()
    EC.check = real
    ok("K16 a fault in the box: the desk as it was", isinstance(pg3, str) and '<div id="missing"></div>' in pg3 and "s960w" not in pg3)


try:
    run()
except Exception as ex:                                       # noqa: BLE001
    import traceback
    traceback.print_exc()
    ok("Z the walk ran to its end", False, str(ex))
finally:
    shutil.rmtree(TMP, ignore_errors=True)
    shutil.rmtree(os.path.join(CODE, "logs"), ignore_errors=True)
bad = sum(1 for _k, c in RES if not c)
print("ALL PASS" if bad == 0 and RES else "%d FAIL" % bad)
sys.exit(0 if bad == 0 and RES else 1)
