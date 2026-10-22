#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s632_app.py -- S632_BATTERY_CLEAN on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch
folder with the given batteries.py (TO, or FROM for the control), on a COPY of a database (SQLite's backup API) -- or a fresh one the
app makes itself. Made-up rows only, dated 2030-2031 (a machine 'WALK632 machine' with a made-up scan row, battery places 'WALK632 ...',
papers 'B-973x'); made-up owner and manager logins; no reader, no paid call, nothing sent; Flask's test client, no port. The scratch
folder is removed at the end; the database given is only read (copied).

    python3 -B walk_s632_app.py --live <the app folder> --files <folder holding the batteries.py to test> [--db <assets.db>] [--expect-red]
"""
import datetime
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
MUST_RED = ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B11", "B14", "B15", "B16", "B17", "B18")
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s632app_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):                                   # the app's CODE only (top-level .py / .js / .json) -- never a stored scan
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        shutil.copy(os.path.join(FILES, "batteries.py"), os.path.join(app, "batteries.py"))
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
            if "NOT mounted" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1):
            print(r.stderr[-1500:])
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
ck("A0 the real app loads with its six parts mounted (%s)" % ", ".join(m for m, x in mods.items() if x is not None), lambda: all(mods.values()))
bt = mods["batteries"]
bt.TODAY = datetime.date(2031, 6, 1)
db = sqlite3.connect(os.environ["ASSETS_DB"])
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('batteries.on','on')")      # K1 C1: a manager passes the gate -- the door itself must refuse
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):                                     # on the scratch copy only: columns later kits' data steps added on the box
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
for u, role in (("walk_own_s632", "owner"), ("walk_mgr_s632", "manager")):
    if not db.execute("SELECT 1 FROM users WHERE username=?", (u,)).fetchone():
        db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (u, "Walk " + role, role))
loc = db.execute("SELECT id FROM locations ORDER BY id LIMIT 1").fetchone()
if loc is None:
    db.execute("INSERT INTO locations(name, visibility) VALUES('WALK632 room','general')")
    loc = db.execute("SELECT id FROM locations ORDER BY id DESC LIMIT 1").fetchone()
MC = "2030-01-01 10:00:00"
mid = db.execute("INSERT INTO assets(name, location_id, category, created_at) VALUES('WALK632 machine', ?, 'Other', ?)", (loc[0], MC)).lastrowid
db.execute("INSERT INTO attachments(entity, entity_id, stored_name, orig_name) VALUES('asset', ?, 'walk632_made_up.jpg', 'walk632_made_up.jpg')", (mid,))


def mkplace(**kw):
    cols = {r[1]: r for r in db.execute("PRAGMA table_info(battery_place)")}
    pl = dict(kw)
    for k, r in cols.items():
        if r[3] and r[4] is None and not r[5] and k not in pl:
            pl[k] = ""
    return db.execute("INSERT INTO battery_place(%s) VALUES(%s)" % (",".join(pl), ",".join("?" * len(pl))), tuple(pl.values())).lastrowid


def mkfit(**kw):
    cols = {r[1]: r for r in db.execute("PRAGMA table_info(battery_fit)")}
    ft = dict(kw)
    for k, r in cols.items():
        if r[3] and r[4] is None and not r[5] and k not in ft:
            ft[k] = ""
    return db.execute("INSERT INTO battery_fit(%s) VALUES(%s)" % (",".join(ft), ",".join("?" * len(ft))), tuple(ft.values())).lastrowid


P1 = mkplace(grp="small_ups", name="WALK632 UPS", sub="Clinic", payer="clinic", supplier="B.L. Computers", warranty_months=12, life_months=30,
             owner_only=0, active=1, upkeep="backup", upkeep_months=3, asset_id=mid, asset_created_at=MC, sort=9001)
F1 = mkfit(place_id=P1, fitted_on="2030-01-05", removed_on="2030-09-01", supplier="B.L. Computers", warranty_months=12)
F2 = mkfit(place_id=P1, fitted_on="2030-09-01", supplier="B.L. Computers", warranty_months=12, bill_created_at="none:old-battery")
P2 = mkplace(grp="small_ups", name="WALK632 UPS two", sub="Lab", payer="nk", supplier="B.L. Computers", warranty_months=12, life_months=30,
             owner_only=0, active=1, upkeep="backup", upkeep_months=3, sort=9002)
F3 = mkfit(place_id=P2, fitted_on="2031-05-01", supplier="B.L. Computers", warranty_months=12)
P3 = mkplace(grp="small_ups", name="WALK632 home", sub="Home · yours only", payer="owner", supplier="B.L. Computers", warranty_months=12,
             life_months=30, owner_only=1, active=1, upkeep="backup", upkeep_months=3, sort=9003)
P4 = mkplace(grp="gen_inv", name="WALK632 chain", sub="Clinic", payer="clinic", supplier="MADE-UP batteries", life_months=48, owner_only=0, active=1, sort=9004)
G1 = mkfit(place_id=P4, fitted_on="2029-01-01", removed_on="2029-06-01", supplier="MADE-UP batteries", brand="WALK make", ah="7", price=111)
G2 = mkfit(place_id=P4, fitted_on="2029-06-01", removed_on="2030-02-01", supplier="MADE-UP batteries")
G3 = mkfit(place_id=P4, fitted_on="2030-02-01", supplier="MADE-UP batteries")
P5 = mkplace(grp="gen_inv", name="WALK632 same day", sub="Clinic", payer="clinic", supplier="MADE-UP batteries", life_months=48, owner_only=0, active=1, sort=9005)
S1 = mkfit(place_id=P5, fitted_on="2031-02-01", removed_on="2031-02-01", supplier="MADE-UP batteries")
S2 = mkfit(place_id=P5, fitted_on="2031-02-01", supplier="MADE-UP batteries")
B1ID = db.execute("INSERT INTO bills(vendor, created_at, stamp_no, status, lane, doc_kind, subgroup, total_amount) "
                  "VALUES('B.L.Computers','2031-05-30 10:00:00','B-9731','filed','clinic','statement','clinic_equipment', 3200)").lastrowid
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]


def client(user):
    c = ar.app.test_client()
    uid = db.execute("SELECT id FROM users WHERE username=?", (user,)).fetchone()[0]
    with c.session_transaction() as ss:
        ss["uid"] = uid
        ss["epoch"] = epoch
    return c


cl = client("walk_own_s632")
fit = lambda i: dict(db.execute("SELECT * FROM battery_fit WHERE id=?", (i,)).fetchone())
plc = lambda i: dict(db.execute("SELECT * FROM battery_place WHERE id=?", (i,)).fetchone())

r = cl.get("/batteries")
t = r.get_data(as_text=True)
ck("B1 the owner's Batteries page (200) has the group 'Machine batteries'", lambda: r.status_code == 200 and "Machine batteries" in t, lambda: r.status_code)
r = cl.get("/batteries/place/%d" % P1)
t = r.get_data(as_text=True)
ck("B2 a place linked to a machine shows 'Scans on the machine record' with its scan, 'Correct a battery entry' with both fittings, and "
   "the in-use row points to the machine's scan", lambda: r.status_code == 200 and "Scans on the machine record" in t and "/files/" in t
   and "Correct a battery entry" in t and t.count('class=s632f data-fit=') == 2 and "scan on the machine record" in t, lambda: (r.status_code, [k for k in ("Scans on the machine record", "/files/", "Correct a battery entry", "scan on the machine record") if k not in t], t.count('class=s632f data-fit=')))
before = fit(F2)
r = cl.post("/batteries/fitfix", data={"fit": F2, "do": "fix", "fitted_on": "02-09-2030", "supplier": "B.L. Computers", "brand": "UPS battery 12V 9Ah",
                                       "ah": "9", "set_n": "1", "warranty_months": "12", "price": "800", "old_amount": ""})
a2, a1 = fit(F2), fit(F1)
ck("B3 'Correct' saves the fitting (date, make, Ah, price) and moves the previous battery's taken-out date with it",
   lambda: r.status_code == 302 and a2["fitted_on"] == "2030-09-02" and a2["brand"] == "UPS battery 12V 9Ah" and a2["price"] == 800
   and a2["ah"] == "9" and a1["removed_on"] == "2030-09-02" and a2["bill_created_at"] == before["bill_created_at"], lambda: (r.status_code, a2, a1["removed_on"]))
r = cl.post("/batteries/fitfix", data={"fit": F2, "do": "fix", "fitted_on": "01-01-2030", "supplier": "B.L. Computers"}, follow_redirects=True)
ck("B4 a date older than the battery before it is refused in words, nothing saved",
   lambda: "cannot be older" in r.get_data(as_text=True) and fit(F2)["fitted_on"] == "2030-09-02" and fit(F2)["price"] == 800,
   lambda: (r.status_code, fit(F2)["fitted_on"]))
r = cl.post("/batteries/fitfix", data={"fit": F2, "do": "void"})
ck("B5 'Entered by mistake — remove': the entry kept with voided_at, the battery before it in use again",
   lambda: r.status_code == 302 and fit(F2)["voided_at"] != "" and fit(F1)["removed_on"] is None and bt.current_fit(db, P1)["id"] == F1,
   lambda: (r.status_code, fit(F2)["voided_at"], fit(F1)["removed_on"]))
r1 = cl.post("/batteries/link", data={"fit": F1, "paper_stamp": "B-9731", "as": "bill"})
r2 = cl.post("/batteries/link", data={"fit": F3, "paper_stamp": "B-9731", "as": "bill"})
ck("B6 one statement paper is the bill of two batteries (both stored with its fingerprint)",
   lambda: fit(F1)["bill_id"] == B1ID and fit(F3)["bill_id"] == B1ID and fit(F3)["bill_created_at"] == "2031-05-30 10:00:00", lambda: (fit(F1)["bill_id"], fit(F3)["bill_id"]))
ck("B7 a 'B.L.Computers' paper is offered for a B.L. Computers place", lambda: any(c["id"] == B1ID for c in bt.candidates(db, bt.place(db, P2), True)))
r = cl.post("/batteries/place", data={"do": "edit", "id": P2, "name": "WALK632 UPS two", "sub": "Lab", "payer": "nk", "supplier": "B.L. Computers",
                                      "warranty_months": "12", "life_months": "30", "set_n": "", "grp": "machine", "upkeep": "", "upkeep_months": ""})
t = cl.get("/batteries").get_data(as_text=True)
sec = t[t.find('id="s571g_machine"'):] if 's571g_machine' in t else ""
ck("B8 'Change this place' moves it to Machine batteries with no upkeep; the page lists it there",
   lambda: plc(P2)["grp"] == "machine" and plc(P2)["upkeep"] == "" and plc(P2)["upkeep_months"] is None and "WALK632 UPS two" in sec[:4000],
   lambda: (plc(P2)["grp"], plc(P2)["upkeep"]))
mg = client("walk_mgr_s632")
r = mg.post("/batteries/fitfix", data={"fit": F3, "do": "fix", "fitted_on": "02-05-2031", "price": "1"})
ck("B9 anyone but the owner cannot correct a battery (refused; nothing changed)", lambda: (r.status_code == 403 or (EXPECT_RED and r.status_code == 404)) and fit(F3)["fitted_on"] == "2031-05-01" and fit(F3)["price"] is None,
   lambda: r.status_code)
anon = ar.app.test_client().post("/batteries/fitfix", data={"fit": F3, "do": "void"})
ck("B10 logged out, the door sends to the login (302), never writes", lambda: (anon.status_code == 302 or (EXPECT_RED and anon.status_code == 404)) and fit(F3)["voided_at"] == "")
t = cl.get("/batteries/place/%d" % P3).get_data(as_text=True)
hd = t[t.find("WALK632 home — history"):][:600]
hd = hd[:hd.find("</p>")] if "</p>" in hd else hd
ck("B11 an owner-only place whose sub-line already says 'yours only' prints it once in its header", lambda: hd.count("yours only") == 1, lambda: txt(hd))
ck("B12 the pages around still answer (Batteries, a machine, the desk, Renewals)",
   lambda: cl.get("/batteries").status_code == 200 and cl.get("/assets/%d" % mid).status_code == 200 and cl.get("/desk").status_code == 200
   and cl.get("/renewals").status_code == 200)
r = cl.post("/batteries/place", data={"do": "edit", "id": P1, "name": "WALK632 UPS", "sub": "Clinic", "payer": "clinic", "supplier": "B.L. Computers",
                                      "warranty_months": "12", "life_months": "30", "set_n": ""})
ck("B13 a place form without the group / upkeep fields keeps them (backup every 3 months, Small UPS)",
   lambda: plc(P1)["upkeep"] == "backup" and plc(P1)["upkeep_months"] == 3 and plc(P1)["grp"] == "small_ups")
r = cl.post("/batteries/fitfix", data={"fit": G1, "do": "fix", "fitted_on": "01-01-2029", "removed_on": "01-07-2029", "supplier": "MADE-UP batteries",
                                       "brand": "WALK make", "ah": "7", "price": "111"}, follow_redirects=True)
ck("B14 a taken-out date later than the next battery's fitting is refused, nothing saved",
   lambda: "cannot be taken out later" in r.get_data(as_text=True) and fit(G1)["removed_on"] == "2029-06-01", lambda: fit(G1)["removed_on"])
r = cl.post("/batteries/fitfix", data={"fit": G2, "do": "void"})
ck("B15 removing a middle entry: the one before it runs on to the next one's fitting (no gap)",
   lambda: fit(G2)["voided_at"] != "" and fit(G1)["removed_on"] == "2030-02-01" and bt.current_fit(db, P4)["id"] == G3, lambda: (fit(G1)["removed_on"],))
r = cl.post("/batteries/fitfix", data={"fit": G3, "do": "void"})
ck("B16 removing the battery in use: the most recent remaining one is in use again", lambda: (bt.current_fit(db, P4) or {}).get("id") == G1,
   lambda: bt.current_fit(db, P4))
r = cl.post("/batteries/fitfix", data={"fit": G1, "do": "fix", "fitted_on": "02-01-2029"})
ck("B17 a POST carrying only the date keeps every other saved value",
   lambda: fit(G1)["fitted_on"] == "2029-01-02" and fit(G1)["brand"] == "WALK make" and fit(G1)["ah"] == "7" and fit(G1)["price"] == 111, lambda: fit(G1))
r = cl.post("/batteries/fitfix", data={"fit": S1, "do": "void"})
ck("B18 two entries fitted the same day: removing the earlier one leaves the later one in use",
   lambda: fit(S1)["voided_at"] != "" and (bt.current_fit(db, P5) or {}).get("id") == S2, lambda: (fit(S2)["removed_on"],))
db.close()
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad = [k for k in MUST_RED if RES.get(k, True)] + [k for k in red if k not in MUST_RED]
    print("WALK S632 APP CONTROL: %d red; %s" % (len(red), "AS IT MUST BE" if not bad else "NOT AS IT MUST BE: " + ", ".join(bad)))
    sys.exit(0 if not bad else 1)
print("WALK S632 APP: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
