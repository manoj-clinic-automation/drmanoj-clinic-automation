#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s634_app.py -- S634_PROCROOM_LIST (D773 Kit 1) on the REAL scan app: asset_register.py and every part it mounts, copied into a
scratch folder with the given sorting_desk.py, asset_register.py and procroom.py (TO -- or FROM for the control, where procroom.py is
absent), on a COPY of a database (SQLite's backup API) -- or a fresh one the app makes itself. Made-up rows only, dated 2031 (papers
'Z-2031-P*' of 'WALK634 ...' suppliers, a photo slip of 2031); made-up owner and manager logins; no reader, no paid call, nothing sent;
Flask's test client, no port. The scratch folder is removed at the end; the database given is only read (copied).

    python3 -B walk_s634_app.py --live <the app folder> --files <folder holding the files to test> [--db <assets.db>] [--expect-red]
"""
import datetime
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

ARGS = sys.argv[1:]


def opt(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d


LIVE, FILES, SRC = opt("--live", "/root/assetapp"), opt("--files"), opt("--db")
EXPECT_RED = "--expect-red" in ARGS
KIT_FILES = ("sorting_desk.py", "asset_register.py", "procroom.py")
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs", "procroom")
# the control on the live FROM files (no procroom.py): every new check red; the old pages (R*) green
MUST_RED = ("A0", "A1", "B1", "B2", "B3", "C1", "C2", "C3", "C4", "C5", "C6", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "E1", "E2", "F1", "F2", "F3", "G1")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s634app_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):                                   # the app's CODE only (top-level .py / .js / .json) -- never a stored scan
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        for f in KIT_FILES:
            p = os.path.join(FILES, f)
            if os.path.isfile(p):
                shutil.copy(p, os.path.join(app, f))
            elif os.path.exists(os.path.join(app, f)):
                os.remove(os.path.join(app, f))                      # the control: a file the FROM side does not have is absent
        db = os.path.join(work, "assets.db")
        if SRC:
            s = sqlite3.connect("file:%s?mode=ro" % SRC, uri=True)
            d = sqlite3.connect(db)
            s.backup(d)
            d.close()
            s.close()
        os.makedirs(os.path.join(work, "uploads"))
        os.makedirs(os.path.join(work, "key"))
        open(os.path.join(work, "key", "anthropic.key"), "w").write("made-up-walk-key\n")
        env = dict(os.environ, ASSETS_DB=db, ASSETS_UPLOADS=os.path.join(work, "uploads"), SHARED_LIB_DIR=os.path.join(work, "noshared"),
                   SCANAPP_ANTHROPIC_KEY_FILE=os.path.join(work, "key", "anthropic.key"), SCANAPP_ANTHROPIC_URL="https://made-up.invalid/v1",
                   CLINIC_PORTAL_DIR=os.path.join(work, "noportal"), FINANCE_LOCAL_URL="http://127.0.0.1:9",
                   FINANCE_DB_FOR_SCANS=os.path.join(work, "nofinance.db"))
        for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
            env.pop(k, None)
        r = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--inner", app] + ARGS, env=env, cwd=work,
                           capture_output=True, text=True, timeout=300)
        sys.stdout.write(r.stdout)
        for l in r.stderr.splitlines():
            if "NOT mounted" in l or "S634" in l or "procroom" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S634_WALK_DEBUG"):
            print(r.stderr[-3000:])
        sys.exit(r.returncode)
    finally:
        shutil.rmtree(work, ignore_errors=True)

# ------------------------------------------------------------------------------------------------ inside the scratch process
APPD = ARGS[ARGS.index("--inner") + 1]
sys.path.insert(0, APPD)
RES = {}


def ck(name, fn, detail=None):
    try:
        ok = bool(fn())
        d = "" if ok or detail is None else detail()
    except Exception as e:                                           # noqa: BLE001
        ok, d = False, repr(e)
    RES[name.split(" ")[0]] = ok
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:400]) if (d and not ok) else ""))


def txt(h):
    return re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", h))


import asset_register as ar                                          # noqa: E402

mods = {m: sys.modules.get(m) for m in PARTS}
pr = mods.get("procroom")
sd = mods.get("sorting_desk")
ck("A0 the real app loads with its seven parts mounted, procroom.py among them (%s)" % ", ".join(m for m, x in mods.items() if x is not None),
   lambda: all(mods.values()) and pr.MOUNTED and pr.VERSION == "S634" and getattr(sd, "PROCROOM", "") == "S634" and getattr(ar, "PROCROOM_S634", "") == "S634")
TODAY = datetime.date(2031, 5, 20)
for m in ("sorting_desk", "procroom", "stationery", "asset_machine", "batteries", "xray_costs"):
    if mods.get(m) is not None:
        mods[m].TODAY = TODAY
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):                                    # a fresh database (the rehearsal) lacks the columns the live one has
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
for u, role in (("walk_own_s634", "owner"), ("walk_mgr_s634", "manager")):
    if not db.execute("SELECT 1 FROM users WHERE username=?", (u,)).fetchone():
        db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (u, "Walk " + role, role))
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
lines0 = []


def seeded():
    out = []
    rc1 = pr.seed_step(dbp, out=out.append)
    rc2 = pr.seed_step(dbp, out=out.append)
    n = db.execute("SELECT COUNT(*) FROM proc_item").fetchone()[0]
    lines0.extend(out)
    return rc1 == 0 and rc2 == 0 and n >= 30 and any("already done" in x for x in out) and \
        db.execute("SELECT COUNT(*) FROM proc_item WHERE name='Fibrecast bandage 5\"' AND state='active'").fetchone()[0] == 1 and \
        db.execute("SELECT state FROM proc_item WHERE name='POP powder'").fetchone()[0] == "rare"


ck("A1 the data step writes the owner's list once (30 products; POP powder rarely used); a second run writes nothing", seeded, lambda: lines0[-3:])


def client(user):
    c = ar.app.test_client()
    uid = db.execute("SELECT id FROM users WHERE username=?", (user,)).fetchone()[0]
    with c.session_transaction() as ss:
        ss["uid"] = uid
        ss["epoch"] = epoch
    return c


own, mgr = client("walk_own_s634"), client("walk_mgr_s634")


def mk(tag, vendor, items=(), created="2031-05-10 05:00:00", **cols):
    vals = dict(kind="Consumable", vendor=vendor, stamp_no="Z-2031-P" + tag, status="draft", lane="clinic", created_at=created,
                submitted_at=created[:16], submitted_by="Walk", doc_kind="estimate", bill_date=created[:10])
    vals.update(cols)
    bid = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
    for it in items:
        db.execute("INSERT INTO bill_items(bill_id, item_name, quantity, rate, amount) VALUES(?,?,?,?,?)", (bid, it[0], it[1], it[2], (it[1] or 0) * it[2]))
    db.commit()
    return bid


def paper(cl, bid):
    r = cl.get("/desk/api/paper/%d" % bid)
    return r.status_code, (r.get_json(silent=True) or {})


def post(cl, url, j):
    r = cl.post(url, json=j)
    return r.status_code, (r.get_json(silent=True) or {})


def flashes(cl):
    with cl.session_transaction() as ss:
        f = list(ss.get("_flashes") or [])
        ss.pop("_flashes", None)
    return " | ".join(x[1] for x in f)


def iid(name):
    try:
        r = db.execute("SELECT id FROM proc_item WHERE name=?", (name,)).fetchone()
    except sqlite3.Error:
        return None
    return r[0] if r else None


def live_lines(bid):
    try:
        return [dict(r) for r in db.execute("SELECT * FROM proc_line WHERE bill_id=? AND voided_at='' ORDER BY line_no", (bid,))]
    except sqlite3.Error:
        return []


P1 = mk("1", "WALK634 SURGICALS", items=(('Gloster 5"', 5, 123.0), ("Bandage 13 cm x 4 m", 5, 21.0), ("Thumb spica Urban", 2, 37.0)))      # made-up rates
F5, R6 = iid('Fibrecast bandage 5"'), iid('Roller bandage 6"')
c, jo = paper(own, P1)
prj = jo.get("pr") or {}
L = prj.get("lines") or []
ck("B1 the desk offers the three lines: Gloster 5\" pre-chosen as Fibrecast bandage 5\" (brand Gloster), the 13 cm × 4 m bandage as Roller bandage 6\", the thumb spica placed at Sanjeevni and flagged",
   lambda: c == 200 and len(L) == 3 and L[0]["item"] == str(F5) and L[0]["brand"] == "Gloster" and L[1]["item"] == str(R6) and L[2]["place"] == "sanj" and L[2]["orth"] and L[2]["item"] == "free",
   lambda: (c, L))
cm, jm = paper(mgr, P1)
ck("B2 no rate anywhere in the desk's Procedure room panel (owner and manager): the reading's ₹123 is not sent", lambda: "pr" in jo and "rate" not in json.dumps(jo.get("pr")) and "123" not in json.dumps(jo.get("pr"))
   and cm == 200 and "rate" not in json.dumps(jm.get("pr")), lambda: json.dumps(jo.get("pr"))[:300])
ck("B3 the manager's panel has no “+ Add to the list” (owner false); the owner's has it", lambda: (jm.get("pr") or {}).get("owner") is False and prj.get("owner") is True)


def lines_of(j, chg=None):
    chg = chg or {}
    out = []
    for l in (j.get("pr") or {}).get("lines") or []:
        x = {k: l[k] for k in ("no", "name", "qty", "unit", "brand", "place", "item")}
        x.update(chg.get(l["no"], {}))
        out.append(x)
    return out


s1, r1 = post(mgr, "/desk/api/save", {"id": P1, "dest": "procedure", "kind": "estimate", "pr_lines": lines_of(jm)})
ll = live_lines(P1)
ck("C1 Shavez's Save (a manager): three lines stored with their places -- 5 Fibrecast 5\" (Gloster) and 5 Roller 6\" in the Procedure room, 2 thumb spica at Sanjeevni; the paper's read rate kept unseen",
   lambda: s1 == 200 and r1.get("ok") and "Procedure room: 3 lines saved" in r1.get("message", "") and len(ll) == 3 and ll[0]["item_id"] == F5 and ll[0]["qty"] == 5
   and ll[0]["brand"] == "Gloster" and ll[0]["rate_read"] == 123 and ll[0]["rate"] is None and ll[2]["place"] == "sanj" and ll[2]["item_id"] is None,
   lambda: (s1, r1, ll))
s2, r2 = post(mgr, "/desk/api/save", {"id": P1, "dest": "procedure", "kind": "estimate", "pr_lines": lines_of(jm)})
ck("C2 the same Save again: unchanged -- still three live lines, never twice", lambda: s2 == 200 and "Procedure room: unchanged" in r2.get("message", "") and len(live_lines(P1)) == 3, lambda: (s2, r2))
s3, r3 = post(mgr, "/desk/api/save", {"id": P1, "dest": "procedure", "kind": "estimate", "pr_lines": lines_of(jm, {3: {"item": "new", "place": "proc"}})})
ck("C3 a manager cannot add to the list (“only Dr Manoj adds”) -- nothing saved, nothing added", lambda: s3 == 400 and "only Dr Manoj adds" in r3.get("error", "") and len(live_lines(P1)) == 3
   and iid("Thumb spica Urban") is None, lambda: (s3, r3))
s4, r4 = post(mgr, "/desk/api/save", {"id": P1, "dest": "procedure", "kind": "estimate", "pr_lines": lines_of(jm, {3: {"place": "proc"}})})
ck("C4 a Procedure room line with no product (kept by its name) is refused, with the words", lambda: s4 == 400 and "needs a product from the list" in r4.get("error", ""), lambda: (s4, r4))
s5, r5 = post(mgr, "/desk/api/save", {"id": P1, "dest": "procedure", "kind": "estimate", "pr_lines": lines_of(jm, {3: {"item": "ask", "place": "proc"}})})
ll5 = live_lines(P1)
ck("C5 “Not on the list — for Dr Manoj” is saved and waits for his list; the earlier lines are replaced, never added", lambda: s5 == 200 and "waiting for Dr Manoj" in r5.get("message", "")
   and len(ll5) == 3 and ll5[2]["ask"] == 1 and db.execute("SELECT COUNT(*) FROM proc_line WHERE bill_id=?", (P1,)).fetchone()[0] == 6, lambda: (s5, r5))
post(mgr, "/desk/api/save", {"id": P1, "dest": "procedure", "kind": "estimate", "pr_lines": lines_of(jm)})       # back to Sanjeevni
pg = own.get("/procroom?ym=2031-05")
t = pg.get_data(as_text=True)
seg = t[t.find('data-item="%s"' % F5):] if F5 else ""
seg = seg[:seg.find("</tr>")]
ck("D1 his page for May 2031: Fibrecast bandage 5\" bought 5 roll, ₹615 (the read rate ₹123 × 5); Worth a look names the orthotics moved to Sanjeevni; the thumb spica under Kept elsewhere",
   lambda: pg.status_code == 200 and "5 roll" in txt(seg) and "₹615" in seg and "Orthotics on clinic slips — 1 line moved to Sanjeevni" in txt(t) and "Thumb spica Urban" in t,
   lambda: (pg.status_code, txt(seg)[:200]))
mp = mgr.get("/procroom?ym=2031-05")
anon = ar.app.test_client().get("/procroom")
ck("D2 his page is his alone: the manager is refused, logged out goes to the login", lambda: mp.status_code in (302, 403) and "Fibrecast" not in mp.get_data(as_text=True) and anon.status_code == 302,
   lambda: (mp.status_code, anon.status_code))
rs_ = own.post("/procroom/slip", data={"day": "20-04-2031", "supplier": "WALK634 SURGICALS", "note": "made-up photo", "back": "ym=2031-05",
                                       "i1": str(F5), "b1": "Gloster", "q1": "4", "p1": "proc", "r1": "123",
                                       "n2": "WALK634 weighing scale", "q2": "1", "p2": "equip", "r2": "555"})
fl = flashes(own)
ck("D3 a slip from a photo (20-04-2031): one Procedure room line and one line kept elsewhere by its name -- saved as one slip", lambda: rs_.status_code == 302 and "Slip of 20-04-2031 saved — 2 lines" in fl
   and db.execute("SELECT COUNT(*) FROM proc_slip WHERE supplier='WALK634 SURGICALS' AND voided_at=''").fetchone()[0] == 1, lambda: fl)
l1 = live_lines(P1)[0]["id"] if live_lines(P1) else 0
rr = own.post("/procroom/rates", data={"r%d" % l1: "101", "back": "ym=2031-05"})
fl2 = flashes(own)
t = own.get("/procroom?ym=2031-05").get_data(as_text=True)
ck("D4 his rate on the May line (₹101): May's Fibrecast 5\" is ₹505, and Worth a look says the rate changed from ₹123 (20-04-2031)",
   lambda: rr.status_code == 302 and "Rates saved (1 line)" in fl2 and 'Fibrecast bandage 5" (Gloster) on 10-05-2031 — ₹101, was ₹123 (20-04-2031)' in txt(t).replace("&#34;", '"').replace("&quot;", '"'),
   lambda: (fl2, txt(t)[txt(t).find("Worth a look"):][:300]))
tf = own.get("/procroom?fy=2031").get_data(as_text=True)


def mrow(h, ym):
    i = h.find('data-ym="%s"' % ym)
    return txt(h[i:h.find("</tr>", i)]) if i >= 0 else ""


ck("D5 the financial year 2031-32 by month: April -- 1 slip, only a photo, Procedure room ₹492, all places ₹1,047; May -- 1 slip, scanned, ₹610 (₹505 + 5 × ₹21)",
   lambda: re.search(r"1 0 1 ₹492 ₹1,047", mrow(tf, "2031-04")) is not None and re.search(r"1 1 0 ₹610", mrow(tf, "2031-05")) is not None,
   lambda: (mrow(tf, "2031-04"), mrow(tf, "2031-05")))
own.post("/procroom/rates", data={"r%d" % l1: "abc"})
ck("D6 a rate that is not a number saves nothing, with the words", lambda: "is not a number. Nothing was saved" in flashes(own) and live_lines(P1)[0]["rate"] == 101)
P5 = mk("5", "WALK634 YUVIKA SURGICALS", items=(('Gloster 4"', 3, 777.0),), created="2031-05-18 05:00:00")       # a printed rate, made up
_c5, j5 = paper(mgr, P5)
_c5o, j5o = paper(own, P5)
ck("D9 a Yuvika paper on its first open, before it is sorted: the manager's desk JSON carries no rate (no stationery panel); the owner's still has it",
   lambda: _c5 == 200 and "777" not in json.dumps(j5) and j5.get("stk") is None and "777" in json.dumps(j5o), lambda: [k for k in j5 if "777" in json.dumps(j5.get(k))])
lid1 = live_lines(P1)[0]["id"] if live_lines(P1) else 0
own.post("/procroom/rates", data={"r%d" % lid1: "", "back": "ym=2031-05"})
flashes(own)
post(mgr, "/desk/api/save", {"id": P1, "dest": "procedure", "kind": "estimate", "pr_lines": lines_of(jm, {1: {"brand": "WALK634 other"}})})
post(mgr, "/desk/api/save", {"id": P1, "dest": "procedure", "kind": "estimate", "pr_lines": lines_of(jm)})
ck("D10 a rate he cleared stays clear through later desk Saves", lambda: live_lines(P1)[0]["rate"] is None, lambda: live_lines(P1)[:1])
own.post("/procroom/rates", data={"r%d" % (live_lines(P1)[0]["id"] if live_lines(P1) else 0): "101", "back": "ym=2031-05"})
flashes(own)
bad_m = own.get("/procroom?ym=2031-13")
ck("D7 a month that is not a month shows this month, never an error", lambda: bad_m.status_code == 200, lambda: bad_m.status_code)
_cm2, jm2 = paper(mgr, P1)
ck("D8 the manager's whole desk JSON for this Procedure room paper carries no rate -- not the read ₹123, not his ₹101",
   lambda: _cm2 == 200 and '"rate"' not in json.dumps(jm2) and (jm2.get("stk") is None), lambda: [k for k in jm2 if "rate" in json.dumps(jm2.get(k))][:5])
so, ro = post(own, "/desk/api/save", {"id": P1, "dest": "others", "kind": "estimate"})
t = own.get("/procroom?fy=2031").get_data(as_text=True)
ck("E1 the paper re-sorted to Others: its Procedure room lines are taken off (kept, voided) and May counts nothing", lambda: so == 200 and "Procedure room lines are taken off" in ro.get("message", "")
   and live_lines(P1) == [] and re.search(r"0 0 0 ₹0", mrow(t, "2031-05")) is not None, lambda: (so, ro, mrow(t, "2031-05")))
sb, rb = post(own, "/desk/api/save", {"id": P1, "dest": "procedure", "kind": "estimate", "pr_lines": lines_of(jm)})
ck("E2 sorted back to Procedure room with its lines: they count again (three lines), and his rate ₹101 is still on the first", lambda: sb == 200 and len(live_lines(P1)) == 3
   and live_lines(P1)[0]["rate"] == 101, lambda: (sb, rb, live_lines(P1)[:1]))
try:
    sid = db.execute("SELECT id FROM proc_slip WHERE supplier='WALK634 SURGICALS'").fetchone()
except sqlite3.Error:
    sid = None
rv = own.post("/procroom/void", data={"slip": sid[0] if sid else 0, "back": "fy=2031"})
t = own.get("/procroom?fy=2031").get_data(as_text=True)
ck("F1 the photo slip voided (kept): April counts nothing", lambda: rv.status_code == 302 and re.search(r"0 0 0 ₹0 ₹0", mrow(t, "2031-04")) is not None, lambda: mrow(t, "2031-04"))
R4 = iid('Roller bandage 4"')
own.post("/procroom/item", data={"id": R4, "do": "retire"})
fl3 = flashes(own)
P2 = mk("2", "WALK634 SURGICALS", items=(("Roller bandage 4", 2, 60.0),), created="2031-05-12 05:00:00")
_c, j2 = paper(mgr, P2)
s6, r6 = post(mgr, "/desk/api/save", {"id": P2, "dest": "procedure", "kind": "estimate", "pr_lines": [dict(no=1, name="Roller bandage 4", qty="2", unit="", brand="", place="proc", item=str(R4))]})
ck("F2 a retired product: off the desk's list, and a new line on it is refused until he brings it back", lambda: "retired" in fl3 and not any(i["id"] == R4 for i in (j2.get("pr") or {}).get("items", []))
   and s6 == 400 and "is retired" in r6.get("error", ""), lambda: (fl3, s6, r6))
P4 = mk("4", "WALK634 SURGICALS", items=(("Zig zag cotton", None, 13.0),), created="2031-05-16 05:00:00")
_c4, j4 = paper(mgr, P4)
L4 = (j4.get("pr") or {}).get("lines") or []
s8, r8 = post(mgr, "/desk/api/save", {"id": P4, "dest": "procedure", "kind": "estimate",
                                      "pr_lines": [dict(no=l["no"], name=l["name"], qty=l["qty"], unit=l["unit"], brand=l["brand"], place=l["place"], item=l["item"], sug=True) for l in L4]})
ck("C6 a suggested line with no quantity read never blocks the Save: the paper is sorted, the line left out and said so",
   lambda: s8 == 200 and len(L4) == 1 and L4[0]["item"] == str(iid("Zig-zag cotton 500 g")) and "left out — no quantity read" in r8.get("message", "") and live_lines(P4) == [],
   lambda: (s8, r8, L4))
ZZ = iid("Zig-zag cotton 500 g")
rsa = own.post("/procroom/slip", data={"day": "16-05-2031", "paper": "z-2031-p4", "back": "ym=2031-05", "i1": str(ZZ), "q1": "2", "p1": "proc", "r1": "13"})
fsa = flashes(own)
rsb = own.post("/procroom/slip", data={"day": "16-05-2031", "paper": "B-99999", "back": "ym=2031-05", "i1": str(ZZ), "q1": "2", "p1": "proc", "r1": "13"})
fsb = flashes(own)
ck("F3 “Scanned as”: the photo's lines go onto that scanned paper (with his rate); an unknown number is refused, nothing saved",
   lambda: "Z-2031-P4: 1 line saved from the photo" in fsa and len(live_lines(P4)) == 1 and live_lines(P4)[0]["rate"] == 13 and "There is no paper numbered" in fsb,
   lambda: (fsa, fsb))
oh = own.get("/desk/month?ym=2031-05").get_data(as_text=True)
mh = mgr.get("/desk/month?ym=2031-05").get_data(as_text=True)
ck("G1 the one menu: “Procedure room” for the owner, not for the manager", lambda: re.search(r'href="[^"]*/procroom"[^>]*>Procedure room<', oh) is not None
   and re.search(r'href="[^"]*/procroom"', mh) is None, lambda: re.findall(r'href="[^"]*procroom[^"]*"', oh)[:3])
# the old pages keep answering (green on both sides)
P3 = mk("3", "WALK634 OTHER SHOP", items=(("A4 sheets", 2, 250.0),), created="2031-05-14 05:00:00", doc_kind="bill")
s7, r7 = post(own, "/desk/api/save", {"id": P3, "dest": "others", "kind": "bill"})
ck("R1 a paper of another group still saves as before", lambda: s7 == 200 and r7.get("ok") and "Procedure room" not in r7.get("message", ""), lambda: (s7, r7))
ck("R2 the desk, The month, Stationery, X-ray and the Machines list still answer for the owner", lambda: all(own.get(u).status_code == 200 for u in ("/desk", "/desk/month", "/stationery", "/xray", "/assets")),
   lambda: [(u, own.get(u).status_code) for u in ("/desk", "/desk/month", "/stationery", "/xray", "/assets")])
_c, j3 = paper(own, P3)
ck("R3 the desk's paper still carries the stationery panel (stk) and its other parts", lambda: _c == 200 and "stk" in j3 and "covers" in j3, lambda: list(j3)[:20])
db.close()
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad = [k for k in MUST_RED if RES.get(k, True)] + [k for k in red if k not in MUST_RED]
    print("WALK S634 APP CONTROL: %d red; %s" % (len(red), "AS IT MUST BE" if not bad else "NOT AS IT MUST BE: " + ", ".join(bad)))
    sys.exit(0 if not bad else 1)
print("WALK S634 APP: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
