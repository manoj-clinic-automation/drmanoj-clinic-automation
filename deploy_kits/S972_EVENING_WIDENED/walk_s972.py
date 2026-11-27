#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s972.py -- S972_EVENING_WIDENED's walk, on a made-up database and made-up exports (no real name, number or clinic ID).
    python3 walk_s972.py <code_dir>      code_dir holds the finance modules (the live set with the kit's TO laid over them)
The last line is ALL PASS or N FAIL. CONTROL: the same walk on the FROM evening_check.py (S960 1) must go red at S1."""
import csv
import datetime as dt
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

CODE = os.path.abspath(sys.argv[1])
TMP = tempfile.mkdtemp(prefix="w972_")
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
    with open(os.environ["W972_PUSHLOG"], "a") as fh:
        fh.write(json.dumps(dict(who=list(who), title=title, body=body, tag=tag)) + "\\n")
    return (len(who), 0, 0)
''')
os.environ.update(EVCHK_NOW=D + "T19:30:00", SLIP_NOW=D + "T19:30:00", EVCHK_LIVE_DB=DB, RING_PORTAL_DIR=PORTAL, W972_PUSHLOG=PUSHLOG,
                  EVCHK_PY=sys.executable, DOCTERZ_EXPORT_STORE=os.path.join(TMP, "store"), FINANCE_DB=DB, EVCHK_SPAWN="0")
for k in ("EVCHK_ON", "EVCHK_TO", "EVCHK_FROM", "EVCHK_SUN_FROM", "EVCHK_SHAPES"):
    os.environ.pop(k, None)
sys.path.insert(0, CODE)
sys.dont_write_bytecode = True

RES = []


def ok(key, cond, note=""):
    RES.append((key, bool(cond)))
    print("%s  %s%s" % ("PASS" if cond else "FAIL", key, ("  -- " + str(note)[:300]) if (note and not cond) else ""))


import docterz_pickup as DP                                    # noqa: E402
import slip_log as SL                                          # noqa: E402
import slip_adjust as SA                                       # noqa: E402
import docterz_ingest as DI                                    # noqa: E402
import dx_feed as DX                                           # noqa: E402
import not_in_docterz as NID                                   # noqa: E402
import evening_check as EC                                     # noqa: E402

HEAD = ["Sr No", "Patient UID", "Patient Name", "Clinic Specific Id", "Mobile", "Consultation Date", "Consultation Amount",
        "Consultation Discount", "Laboratory Amount", "Laboratory Discount", "Radiology Amount", "Radiology Discount",
        "Procedure Amount", "Procedure Discount", "Amount collected", "Mode Of Payment"]
SALT = [0]


def export_bytes(rows):
    SALT[0] += 1
    b = io.StringIO()
    w = csv.writer(b)
    w.writerow(HEAD)
    w.writerow(["Dr. Manoj Agarwal Clinic"] + [""] * (len(HEAD) - 1))
    for i, r in enumerate(rows, 1):
        dd = dt.date.fromisoformat(r.get("day", D)).strftime("%d-%m-%Y")
        w.writerow([i, r.get("uid", "TESTUID%04d" % i), r.get("name", "Test Person"), r["cid"], "x", dd, r.get("cons", 0), 0,
                    r.get("lab", 0), r.get("labd", 0), r.get("rad", 0), r.get("radd", 0), r.get("proc", 0), r.get("procd", 0),
                    r.get("cons", 0), "Cash"])
    w.writerow(["", "", "salt %d" % SALT[0]] + [""] * (len(HEAD) - 3))
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
    for i in range(5):
        con.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode, shift) VALUES (?,?,?,?,?,?,?,?)",
                    ("2026-11-2%d" % i, "consult", 1, "x", "1", 60000, "Cash", ""))
    con.commit()
    return con


SN = {"opd": 100, "xp": 200}


def slip(con, series, cid, day=D, state="ok", noid="", name="", items=()):
    SN[series] += 1
    cur = con.execute("INSERT INTO slip (series, slip_no, day, clinic_id, no_id_name, name_seen, state, logged_by, logged_at) "
                      "VALUES (?,?,?,?,?,?,?,?,?)", (series, SN[series], day, cid, noid, name or ("Test " + cid), state, "shavez", day + " 10:00:00"))
    sid = cur.lastrowid
    for j, x in enumerate(items):
        kind, nm, price, disc = x[:4]
        con.execute("INSERT INTO slip_item (slip_id, kind, name, side, price_p, discount_p, sort) VALUES (?,?,?,?,?,?,?)",
                    (sid, kind, nm, x[4] if len(x) > 4 else "", price, disc, j))
    con.commit()
    return sid


def items_of(con, sid):
    return [dict(r) for r in con.execute("SELECT * FROM slip_item WHERE slip_id=? ORDER BY sort, id", (sid,))]


def scenario(con):
    s = {}
    s[601] = slip(con, "xp", "601", items=[("xray", "Knee AP", 50000, 10000)])                       # chhoot
    s[602] = slip(con, "xp", "602", items=[("xray", "Hand AP", 50000, 0), ("xray", "Hand Lat", 30000, 0)])   # kam
    s[603] = slip(con, "xp", "603", items=[("proc", "Dressing", 30000, 0)])                          # kam, Docterz chhoot
    s[604] = slip(con, "xp", "604", items=[("xray", "Ankle AP", 40000, 0, "R")])                     # tdoc, offered (a side: the copy is the other)
    s[605] = slip(con, "xp", "605", items=[("xray", "Wrist", 40000, 10000)])                         # tdoc, not offered (chhoot)
    s[606] = slip(con, "xp", "606", items=[("proc", "ILI knee", 100000, 0), ("proc", "ILI knee", 100000, 0)])  # tslip
    s[607] = slip(con, "xp", "607", items=[("proc", "ILI knee", 100000, 0), ("proc", "ILI knee", 100000, 0)])  # both knees, agrees
    s[608] = slip(con, "xp", "608", items=[("xray", "Chest", 50000, 0)])                             # more
    s["609o"] = slip(con, "opd", "609")                                                              # more, no X-ray slip
    s[610] = slip(con, "xp", "610", items=[("xray", "Spine", 50000, 0)])                             # radd today
    con.execute("INSERT INTO slip_adjust (slip_id, kind, day, made_by, made_at, state, cancel_how) VALUES (?,?,?,?,?,?,?)",
                (s[610], "cancel", D, "shavez", D + " 11:00:00", "pending", "returned"))
    s[611] = slip(con, "xp", "611", items=[("xray", "Pelvis", 50000, 0)])                            # answered on his list
    NID.ensure(con)
    con.execute("INSERT INTO nid_mark (slip_id, kind, act, amount_p, day, who, at) VALUES (?,?,?,?,?,?,?)", (s[611], "xray", "outside", 50000, D, "manoj", D + " 12:00:00"))
    s[612] = slip(con, "xp", "612", items=[("xray", "Elbow", 50000, 0)])                             # the S960 missing line
    s[613] = slip(con, "xp", "613", items=[("xray", "Finger", 40000, 40000)])                        # a free line, nothing billed
    s[614] = slip(con, "xp", "614", items=[("xray", "Toe", 40000, 40000)])                           # rejected chhoot, full rate billed
    s[615] = slip(con, "xp", "615", items=[("xray", "Heel", 40000, 40000)])                          # rejected chhoot, Docterz 0
    for k in (614, 615):
        iid = con.execute("SELECT id FROM slip_item WHERE slip_id=?", (s[k],)).fetchone()[0]
        con.execute("INSERT INTO slip_adjust (slip_id, item_id, kind, amount_p, day, made_by, made_at, state) VALUES (?,?,?,?,?,?,?,?)",
                    (s[k], iid, "free", 40000, D, "shavez", D + " 11:00:00", "rejected"))
    s[616] = slip(con, "xp", "616", items=[("xray", "Shoulder", 50000, 0)])                          # radiology column, agrees
    s[617] = slip(con, "xp", "", noid="Walk In", items=[("xray", "Leg", 50000, 0)])                  # no clinic ID
    s[619] = slip(con, "xp", "619", items=[("xray", "Foot", 50000, 0)])                              # two Docterz rows, agrees
    s[620] = slip(con, "xp", "620", items=[("proc", "ILI shoulder", 100000, 0), ("proc", "ILI shoulder", 100000, 0)])  # tslip, a chhoot waits
    iid = con.execute("SELECT id FROM slip_item WHERE slip_id=? ORDER BY id DESC LIMIT 1", (s[620],)).fetchone()[0]
    con.execute("INSERT INTO slip_adjust (slip_id, item_id, kind, amount_p, day, made_by, made_at, state) VALUES (?,?,?,?,?,?,?,?)",
                (s[620], iid, "discount", 10000, D, "shavez", D + " 11:00:00", "pending"))
    con.execute("UPDATE slip_item SET discount_p=10000 WHERE id=?", (iid,))
    s[621] = slip(con, "xp", "621", day="2026-11-25", items=[("xray", "Knee AP", 50000, 0)])          # yesterday's slip
    s[623] = slip(con, "xp", "623", items=[("xray", "Knee AP", 30000, 0), ("xray", "LS spine", 30000, 0)])   # same price: which twice? -> more
    s["624a"] = slip(con, "xp", "624", items=[("proc", "ILI knee", 100000, 0), ("proc", "ILI shoulder", 100000, 0)])
    s["624b"] = slip(con, "xp", "624", items=[("proc", "ILI knee", 100000, 0)])                     # the repeats on two other slips:
    s["624c"] = slip(con, "xp", "624", items=[("proc", "ILI shoulder", 100000, 0)])                 # tslip, no write offered
    s["625o"] = slip(con, "opd", "625")
    s[625] = slip(con, "xp", "625", items=[("xray", "Arm", 50000, 0)])                               # X-ray billed under procedure
    s[626] = slip(con, "xp", "626", items=[("xray", "Ankle Lat", 40000, 0)])                         # tdoc, no side: no tap
    s[627] = slip(con, "xp", "627", items=[("xray", "Knee AP", 50000, 0), ("proc", "Plaster", 50000, 0)])     # all billed as X-ray
    s[628] = slip(con, "xp", "628", items=[("xray", "Wrist AP", 30000, 0), ("xray", "Wrist Lat", 30000, 0)])  # one view billed as proc
    s[629] = slip(con, "xp", "629", items=[("xray", "Hip AP", 50000, 0), ("xray", "Hip AP", 50000, 0)])     # a repeat + a stray proc:
    con.commit()
    return s


EXP = [dict(cid="601", cons=600, lab=500), dict(cid="602", lab=500), dict(cid="603", proc=300, procd=300), dict(cid="604", lab=800),
       dict(cid="605", lab=600), dict(cid="606", proc=1000), dict(cid="607", proc=2000), dict(cid="608", lab=1200),
       dict(cid="609", cons=600, lab=500), dict(cid="610", lab=800), dict(cid="611", lab=800), dict(cid="612", cons=600),
       dict(cid="614", lab=400), dict(cid="615", lab=400, labd=400), dict(cid="616", rad=500), dict(cid="618", lab=500),
       dict(cid="619", lab=300), dict(cid="619", lab=200), dict(cid="620", proc=1000), dict(cid="621", lab=900),
       dict(cid="601", lab=999, day="2026-11-25"), dict(cid="622", lab=500, uid="bad uid"), dict(cid="623", lab=900),
       dict(cid="624", proc=2000), dict(cid="625", cons=600, proc=500), dict(cid="626", lab=800), dict(cid="627", lab=1000),
       dict(cid="628", lab=300, proc=300), dict(cid="629", lab=500, proc=500)]
WANT = {("601", "chhoot"), ("602", "kam"), ("603", "kam"), ("604", "tdoc"), ("605", "tdoc"), ("606", "tslip"), ("608", "more"),
        ("609", "more"), ("615", "kam"), ("620", "tslip"), ("623", "more"), ("624", "tslip"), ("625", "head"), ("626", "tdoc"),
        ("627", "head"), ("628", "head"), ("629", "tslip"), ("629", "more")}
FIXED = [dict(cid="601", cons=600, lab=500, labd=100), dict(cid="602", lab=800), dict(cid="603", proc=300), dict(cid="604", lab=800),
         dict(cid="605", lab=300), dict(cid="606", proc=1000), dict(cid="607", proc=2000), dict(cid="608", lab=500),
         dict(cid="609", cons=600), dict(cid="610", lab=800), dict(cid="611", lab=800), dict(cid="612", cons=600, lab=500),
         dict(cid="614", lab=400), dict(cid="615", lab=400), dict(cid="616", rad=500), dict(cid="619", lab=500), dict(cid="620", proc=1900),
         dict(cid="623", lab=600), dict(cid="624", proc=4000), dict(cid="625", cons=600, lab=500),
         dict(cid="626", lab=400), dict(cid="627", lab=500, proc=500), dict(cid="628", lab=600),
         dict(cid="629", lab=1000)] + [dict(cid=str(630 + i), cons=600) for i in range(8)]   # a corrected export never has fewer rows (docterz_pickup quarantines it)
FRESH = [dict(x, lab=400) if x["cid"] == "604" else (dict(x, proc=2000) if x["cid"] == "606" else x) for x in FIXED]   # before any answer


def take(con, raw, ist_hhmm, day=D):
    f = {"id": "reception:%d" % (SALT[0] * 1000 + int(ist_hhmm.replace(":", ""))), "name": "x.csv",
         "modifiedTime": (dt.datetime.fromisoformat(day + "T" + ist_hhmm) - dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S.000Z")}
    DP.take(con, f, raw)
    r = con.execute("SELECT id FROM docterz_export WHERE drive_id=? AND drive_mtime=?", (f["id"], f["modifiedTime"])).fetchone()
    con.execute("UPDATE docterz_export SET taken_at=? WHERE id=?", (day + " " + ist_hhmm + ":05", r[0]))
    con.commit()
    return r[0]


def pushes():
    if not os.path.exists(PUSHLOG):
        return []
    return [json.loads(x) for x in open(PUSHLOG) if x.strip()]


def shp(con):
    c = EC.check(con, D)
    return (c or {}).get("shapes") or []


def run():
    # ---------------------------------------------------------------- S: the four shapes on one export
    con = fresh()
    s = scenario(con)
    xid = take(con, export_bytes(EXP), "19:30")
    got = shp(con)
    have = {(x["cid"], x["shape"]) for x in got}
    ok("S1 the shapes on the export: exactly the sixteen made-up lines", have == WANT, "extra %s missing %s" % (sorted(have - WANT), sorted(WANT - have)))
    by = {x["cid"]: x for x in got}
    ok("S2 chhoot: parchi 400, Docterz 500, the discount 100", by.get("601", {}).get("extra") == 10000 and by["601"]["p"] == 40000 and by["601"]["d"] == 50000)
    ok("S3 kam: parchi 800, Docterz 500, add 300", by.get("602", {}).get("extra") == 30000)
    ok("S4 kam with a Docterz chhoot (proc 300, discount 300): the words say the discount", "chhoot ₹300" in EC.shape_text(by["603"])[0]
       and "hataiye" in EC.shape_text(by["603"])[0], EC.shape_text(by.get("603", {"name": "", "cid": "", "kind": "proc", "what": "", "p": 0, "d": 0, "extra": 0, "shape": "x"})) if "603" in by else "")
    ok("S5 tdoc offered (no chhoot); tdoc with a chhoot not offered", by.get("604", {}).get("can") is True and by.get("605", {}).get("can") is False)
    ok("S6 tslip offered; tslip whose repeat carries a chhoot entry not offered", by.get("606", {}).get("can") is True and by.get("620", {}).get("can") is False
       and len(by.get("606", {}).get("items") or []) == 1)
    ok("S7 both knees billed as two: nothing", "607" not in by)
    ok("S8 more: Docterz 1200, parchi 500; more with no X-ray slip (OPD slip only)", by.get("608", {}).get("extra") == 70000 and by.get("609", {}).get("p") == 0)
    ok("S9 left out: a radd today, an answer on his list, a free line, a rejected chhoot billed in full, radiology, two rows, no ID, "
       "no slip, yesterday's slip, another day's row, a non-UID row", not any(c in by for c in ("610", "611", "613", "614", "616", "617", "618", "619", "621", "622")))
    ok("S13 two lines at the same price: 'more', never a tap that could copy the wrong one (cold review M1)", by.get("623", {}).get("shape") == "more")
    ok("S14 repeats spread over two other slips: tslip, no write offered (cold review 4)", by.get("624", {}).get("shape") == "tslip" and by["624"]["can"] is False)
    rows = EC.check(con, D)["rows"]
    ok("S10 the S960 missing line stays its own (612), not a shape", any(r["cid"] == "612" and r["kind"] == "xray" for r in rows) and "612" not in by)
    ok("S15 the total agrees, the head does not (X-ray billed as procedure, and back): ONE 'head' line, no tap, off the missing list "
       "(second look 1)", all(by.get(c, {}).get("shape") == "head" and by[c]["can"] is False for c in ("625", "627", "628"))
       and not any(r["cid"] in ("625", "627", "628") for r in rows) and "head galat" in EC.shape_text(by["627"])[0])
    ok("S17 a repeated slip line beside a stray procedure: no 'head' -- named as it is (re-look)", {x["shape"] for x in got if x["cid"] == "629"} == {"tslip", "more"})
    ok("S16 Docterz one more of a line with no side: no tap (another view, or twice?)", by.get("626", {}).get("shape") == "tdoc"
       and by["626"]["can"] is False and "doosra view" in EC.shape_text(by["626"])[0])
    words = [EC.shape_text(x, e) for x in got for e in (False, True)]
    ok("S11 every line has words in both languages, no 'None', the money in rupees", all(w[0] and "None" not in w[0] and "₹" in w[0] for w in words))
    ok("S12 the shape keys hold no name", all(re.fullmatch(r"ev:(chhoot|kam|tdoc|tslip|more|head):\d+:(xray|proc|both)", x["key"]) for x in got))
    # ---------------------------------------------------------------- R: the money reader
    if hasattr(EC, "read_amounts"):
        am = EC.read_amounts(export_bytes(EXP), D)
        ok("R1 the reader: Laboratory + Radiology, net = amount - discount, rows summed, other days and non-UID rows out",
           am.get("616", {}).get("xray") == [50000, 50000, 0] and am.get("619", {}).get("xray") == [50000, 50000, 0]
           and am.get("615", {}).get("xray") == [0, 40000, 40000] and am.get("601", {}).get("xray") == [50000, 50000, 0] and "622" not in am)
        ok("R2 an unreadable export: None", EC.read_amounts(b"\xff\xfe\x00junk", D) is None and EC.read_amounts(b"a,b\n1,2\n", D) is None)
    else:
        ok("R1 the reader exists", False)
    # ---------------------------------------------------------------- P: one push per export
    r = EC.on_export(con, xid, push=True)
    pu = pushes()
    row = con.execute("SELECT * FROM evening_check_push WHERE export_id=?", (xid,)).fetchone()
    ok("P1 missing + shapes: one push '1 parchi Docterz mein nahi · 18 farq', outcome missing", len(pu) == 1 and pu[0]["title"] == "1 parchi Docterz mein nahi · 18 farq"
       and row["outcome"] == "missing", "%s %s" % (r, pu[-1:] if pu else ""))
    ok("P2 the push names the lines, Docterz first", pu and "farq:" in pu[0]["body"] and "Docterz mein daalein" in pu[0]["body"], pu[0]["body"] if pu else "")
    ok("P3 the shapes column: keys only (shape:slip:kind)", row["shapes"] and all(re.fullmatch(r"(chhoot|kam|tdoc|tslip|more|head):\d+:(xray|proc|both)", k) for k in row["shapes"].split(",")))
    ok("P4 the same export again: nothing", EC.on_export(con, xid).startswith("skip") and len(pushes()) == 1)
    st = os.popen("cd %s && EVCHK_NOW=%sT19:31:00 %s -B %s --status --db %s" % (TMP, D, sys.executable, os.path.join(CODE, "evening_check.py"), DB)).read()
    ok("P5 --status counts the shapes", "missing 1; shapes 18" in st and "S972 1" in st, st)
    # ---------------------------------------------------------------- A: the slip-side answers
    audits = []
    EC._U["audit"] = lambda con_, table, rid, action, before=None, after=None, who=None: audits.append((table, action, who))
    os.environ["EVCHK_NOW"] = D + "T19:40:00"
    k604 = by["604"]["key"]
    msg = EC.answer(con, "shavez", k604, "addline")
    it = items_of(con, s[604])
    ok("A1 'Haan, parchi theek karo': the other side (L) of Ankle AP, no chhoot, audited; the line goes", len(it) == 2 and it[1]["name"] == "Ankle AP"
       and it[0]["side"] == "R" and it[1]["side"] == "L"
       and it[1]["price_p"] == 40000 and it[1]["discount_p"] == 0 and audits[-1][1] == "slip_item_added_evening_s972" and "604" not in {x["cid"] for x in shp(con)}, msg)
    try:
        EC.answer(con, "shavez", k604, "addline")
        ok("A2 the same tap again: refused", False)
    except EC.FreeError:
        ok("A2 the same tap again: refused, nothing written", len(items_of(con, s[604])) == 2)
    for key, act, nm in ((by["605"]["key"], "addline", "A3 tdoc with a chhoot"), (by["606"]["key"], "addline", "A4 the wrong answer for tslip"),
                         (by["620"]["key"], "dropdup", "A5 tslip with a chhoot entry"), (by["602"]["key"], "dropdup", "A6 kam has no slip answer"),
                         ("ev:tdoc:999:xray", "addline", "A7 a key not on the list")):
        n0 = con.execute("SELECT COUNT(*) FROM slip_item").fetchone()[0]
        try:
            EC.answer(con, "shavez", key, act)
            ok(nm + ": refused", False)
        except EC.FreeError:
            ok(nm + ": refused, nothing written", con.execute("SELECT COUNT(*) FROM slip_item").fetchone()[0] == n0)
    n0 = con.execute("SELECT COUNT(*) FROM slip_item").fetchone()[0]
    try:
        EC.answer(con, "shavez", by["606"]["key"], "dropdup", items="99999")
        ok("A9 a tap whose items are not the line's now: refused", False)
    except EC.FreeError:
        ok("A9 a tap whose items are not the line's now: refused, nothing written (cold review 2)", con.execute("SELECT COUNT(*) FROM slip_item").fetchone()[0] == n0
           and not con.in_transaction)
    msg = EC.answer(con, "shavez", by["606"]["key"], "dropdup", items=",".join(str(i) for i in by["606"]["items"]))
    ok("A8 'Nahi, parchi se ek hataiye': exactly the repeat removed, audited; the line goes", len(items_of(con, s[606])) == 1
       and audits[-1][1] == "slip_item_removed_duplicate_s972" and "606" not in {x["cid"] for x in shp(con)}, msg)
    # ---------------------------------------------------------------- K: the desk
    ph = EC.panel_html(con)
    n_can = sum(1 for x in shp(con) if x["can"])
    ok("K1 the box: the missing list, then 'Docterz aur parchi mein farq: 8', one tap per offered line", "Aaj ki parchi jo Docterz mein nahi: 1" in ph
       and "Docterz aur parchi mein farq: 16" in ph and ph.count('class="s972a"') == n_can, "can %d taps %d" % (n_can, ph.count('class="s972a"')))
    pe = EC.panel_html(con, eng=True)
    ok("K2 his English view", "Docterz and the slips differ: 16" in pe and "apply the discount" in pe and "which is right?" in pe)
    db_ = EC.desk_box(con)
    ok("K3 the desk box carries the S960 script and the S972 script once each", db_.count("/answer") == 1 and db_.count("setInterval") == 1
       and "window.s960load=load" in db_ and "window.s960load()" in db_)
    try:
        from flask import Flask                                # noqa: PLC0415
        import parchi_desk as PD                               # noqa: PLC0415
        app = Flask("w972")
        who = {"u": {"user": "shavez", "roles": ["maker"]}}

        def req(*roles, unit=None):
            return (who["u"], None) if who["u"] is not None else (None, ("no", 403))

        PD.init(app, lambda: con, req, lambda *a, **k: audits.append(("door", a[3] if len(a) > 3 else "", k.get("who"))), unit="slips")
        c = app.test_client()
        ok("K4 the desk mounts three doors (S960's two + S972's answer)", EC.API + "/answer" in {r.rule for r in app.url_map.iter_rules()})
        j = c.post(EC.API + "/answer", json={"key": by["601"]["key"], "act": "addline"}).get_json()
        ok("K5 the door refuses an answer the line does not take", j and not j["ok"] and j.get("err"))
        j = c.post(EC.API + "/answer", json={"key": "x", "act": "drop"}).get_json()
        ok("K6 nonsense: refused", j and not j["ok"])
        who["u"] = None
        ok("K7 no desk login: 403", c.post(EC.API + "/answer", json={}).status_code == 403)
        who["u"] = {"user": "shavez", "roles": ["maker"]}
    except ImportError:
        ok("K4 flask present for the door walk", False)
    # ---------------------------------------------------------------- P: corrected, clean, mixed, off
    os.environ["EVCHK_NOW"] = D + "T20:40:00"
    x2 = take(con, export_bytes(FIXED), "20:40")
    r = EC.on_export(con, x2)
    pu = pushes()
    left = shp(con)
    ok("P6 a corrected export clears every line: 'cleared', '✓ Docterz aur parchi sab mile'", pu[-1]["title"] == "✓ Docterz aur parchi sab mile" and not left
       and "PC band" in pu[-1]["body"], "%s left %s" % (r, [(x["cid"], x["shape"]) for x in left]))
    con.close()
    con = fresh()
    scenario(con)
    os.environ["EVCHK_NOW"] = D + "T19:30:00"
    only = [x for x in EXP if x["cid"] not in ("612", "625")] + [dict(cid="612", lab=500), dict(cid="625", cons=600, lab=500)]
    x3 = take(con, export_bytes(only), "19:30")
    EC.on_export(con, x3)
    ok("P7 shapes only: '17 farq — Docterz aur parchi'", pushes()[-1]["title"] == "17 farq — Docterz aur parchi", pushes()[-1]["title"])
    con.close()
    con = fresh()
    scenario(con)
    x4 = take(con, export_bytes(FRESH), "19:30")
    EC.on_export(con, x4)
    ok("P8 the first export clean: '✓ 26-Nov: Docterz aur parchi sab mile'", pushes()[-1]["title"] == "✓ 26-Nov: Docterz aur parchi sab mile", pushes()[-1]["title"])
    con.close()
    con = fresh()
    scenario(con)
    os.environ["EVCHK_SHAPES"] = "0"
    x5 = take(con, export_bytes([x for x in only if x["cid"] != "627"] + [dict(cid="627", lab=500, proc=500)]), "19:30")   # 627 in full: shapes only
    EC.on_export(con, x5)
    ok("P9 EVCHK_SHAPES=0: the S960 check as it was (no shapes, its own clean words)", pushes()[-1]["title"] == "✓ 26-Nov: sab parchi Docterz mein"
       and not shp(con), pushes()[-1]["title"])
    os.environ.pop("EVCHK_SHAPES", None)
    con.close()
    con = fresh()
    slip(con, "opd", "701")
    slip(con, "xp", "702", items=[("xray", "Knee AP", 50000, 0)])
    x6 = take(con, export_bytes([dict(cid="702", lab=500)]), "19:30")
    EC.on_export(con, x6)
    ok("P10 missing only: the S960 words exactly", pushes()[-1]["title"] == "1 parchi Docterz mein nahi" and pushes()[-1]["body"].endswith("abhi Docterz mein daalein, phir dobara export"))
    x7 = take(con, export_bytes([dict(cid="702", lab=500), dict(cid="701", cons=600, lab=300)]), "16:30")
    ok("P11 an afternoon export is left alone", EC.on_export(con, x7).startswith("skip"))
    con.close()
    # ---------------------------------------------------------------- an earlier day: no box, no answer
    con = fresh()
    s = scenario(con)
    take(con, export_bytes(EXP), "19:30")
    os.environ["EVCHK_NOW"] = "2026-11-27T19:30:00"
    try:
        EC.answer(con, "shavez", "ev:tdoc:604:xray", "addline")
        ok("Y1 yesterday's line cannot be answered today", False)
    except EC.FreeError:
        ok("Y1 yesterday's line cannot be answered today; the box is empty", EC.panel_html(con) == "" and len(items_of(con, s[604])) == 1)
    os.environ["EVCHK_NOW"] = D + "T19:30:00"
    con.close()


try:
    run()
except Exception as ex:                                        # noqa: BLE001
    import traceback
    traceback.print_exc()
    ok("RUN the walk finished", False, ex)
finally:
    shutil.rmtree(TMP, ignore_errors=True)
bad = [k for k, v in RES if not v]
print("ALL PASS" if not bad else "%d FAIL" % len(bad))
sys.exit(0 if not bad else 1)
