#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s637_app.py -- S637_PROCROOM_MORNING (D773 Kit 3) on the REAL scan app: asset_register.py and every part it mounts, copied into a
scratch folder with the given sorting_desk.py, asset_register.py and procroom.py (TO -- or FROM for the control, where procroom.py is
absent), on a COPY of a database (SQLite's backup API) -- or a fresh one the app makes itself. Made-up rows only, dated 2031 (papers
a MADE-UP slip book and Docterz day in a made-up finance database (never the real one), slips of 2031); made-up owner and manager logins; no reader, no paid call, nothing sent;
Flask's test client, no port. The scratch folder is removed at the end; the database given is only read (copied).

    python3 -B walk_s637_app.py --live <the app folder> --files <folder holding the files to test> [--db <assets.db>] [--expect-red]
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
KIT_FILES = ("procroom.py",)
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs", "procroom")
# the control on the live FROM files (Kit 2's procroom.py): every new check red; Kit 1-2's pages and the old pages (K*, R*) green
MUST_RED = ("A0", "A1", "N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8", "N9", "S1", "S2", "S3", "S4", "N10", "N11", "N12", "N13", "N14")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s637app_")
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
            if "NOT mounted" in l or "S637" in l or "procroom" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S637_WALK_DEBUG"):
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
import asset_register as ar                                          # noqa: E402

mods = {m: sys.modules.get(m) for m in PARTS}
pr = mods.get("procroom")
ck("A0 the real app loads with its seven parts mounted; procroom.py is Kit 3's (S637) (%s)" % ", ".join(m for m, x in mods.items() if x is not None),
   lambda: all(mods.values()) and pr.MOUNTED and pr.VERSION == "S637")
TODAY = datetime.date(2031, 5, 20)
for m in ("sorting_desk", "procroom", "stationery", "asset_machine", "batteries", "xray_costs"):
    if mods.get(m) is not None:
        mods[m].TODAY = TODAY
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
db.execute("DELETE FROM settings WHERE key='proc.morning'")                     # the walk starts with the screen OFF (a copy of the live db)
for k, v in (("proc.gloves_cast", "2"), ("proc.gloves_ili", "1"), ("proc.gloves_box", "")):   # his allowances may be set on the live copy
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (k, v))
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
for u, role in (("walk_own_s637", "owner"), ("walk_mgr_s637", "manager")):
    if not db.execute("SELECT 1 FROM users WHERE username=?", (u,)).fetchone():
        db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (u, "Walk " + role, role))
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
pr.seed_step(dbp, out=lambda *_: None)
# a MADE-UP slip book and Docterz (never the real finance database): his kits as his rate page has them (S637's read, 24-Oct)
FDB = os.environ["FINANCE_DB_FOR_SCANS"]
f = sqlite3.connect(FDB)
f.executescript("""
CREATE TABLE slip(id INTEGER PRIMARY KEY, series TEXT, slip_no INTEGER, day TEXT, clinic_id TEXT DEFAULT '', no_id_name TEXT DEFAULT '', state TEXT DEFAULT 'ok');
CREATE TABLE slip_item(id INTEGER PRIMARY KEY, slip_id INTEGER, kind TEXT, service_id INTEGER, name TEXT DEFAULT '', side TEXT DEFAULT '', price_p INTEGER DEFAULT 0, sort INTEGER DEFAULT 0);
CREATE TABLE clinic_day_line(business_date TEXT, section TEXT, sn INTEGER, patient TEXT DEFAULT '', clinic_id TEXT DEFAULT '', amount_p INTEGER DEFAULT 0, mode TEXT DEFAULT '');
CREATE TABLE clinic_day_revenue(business_date TEXT PRIMARY KEY, taken_at TEXT);
CREATE TABLE owner_service(id INTEGER PRIMARY KEY, kind TEXT, name TEXT, price_p INTEGER DEFAULT 0, active INTEGER DEFAULT 1, grp TEXT DEFAULT '', status TEXT DEFAULT 'approved');
CREATE TABLE owner_service_item(id INTEGER PRIMARY KEY, service_id INTEGER, item TEXT, qty REAL DEFAULT 1, unit TEXT DEFAULT '', ask TEXT DEFAULT '', sizes TEXT DEFAULT '', note TEXT DEFAULT '');
CREATE TABLE patient_ref(id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT, phone_last4 TEXT DEFAULT '', merged_into TEXT);
INSERT INTO owner_service(id, kind, name, grp) VALUES (1,'proc','B/K (Below knee) fibre cast','Cast / slab'), (2,'proc','ILI (heel)','Injection (ILI)'), (3,'proc','Dressing','Dressing'), (4,'xray','KNEE AP/LAT','');
INSERT INTO owner_service_item(service_id, item, ask, sizes) VALUES
 (1,'Cast padding','size_qty','4",6"'), (1,'Fibrecast bandage','size_qty','2",3",4",5"'), (1,'Roller bandage','size_qty','4",6"'), (1,'Stockinette','used_yesno',''),
 (2,'Inj Loftypred 80 mg OR Inj Viracort 40','one_of','Loftypred 80 mg / Viracort 40'), (2,'Surgiwear D600 drape','selectable',''),
 (3,'Roller bandage','size_qty','4",6"');
INSERT INTO slip(id, series, slip_no, day, clinic_id) VALUES (901,'xp',9187,'2031-05-19','W99004821'), (902,'xp',9188,'2031-05-19','W99003307'),
 (903,'xp',9190,'2031-05-19','W99006190'), (904,'xp',9191,'2031-05-19','W99000452'), (905,'opd',9999,'2031-05-19','W99000001'),
 (906,'xp',9175,'2031-05-18','W99007777'), (907,'xp',9160,'2031-05-17','W99008888');
INSERT INTO slip_item(slip_id, kind, service_id, name, side) VALUES (901,'proc',1,'B/K (Below knee) fibre cast','R'), (902,'proc',2,'ILI (heel)','L'),
 (903,'proc',1,'B/K (Below knee) fibre cast','L'), (904,'xray',4,'KNEE AP/LAT',''), (906,'proc',1,'B/K (Below knee) fibre cast','R'), (907,'proc',3,'Dressing','');
INSERT INTO clinic_day_revenue VALUES ('2031-05-19','2031-05-19 23:00'), ('2031-05-18','2031-05-18 23:00');
INSERT INTO clinic_day_line(business_date, section, sn, patient, clinic_id) VALUES ('2031-05-19','proc',1,'WALKPATIENT ONE','W99004821'),
 ('2031-05-19','proc',2,'WALKPATIENT TWO','W99003307'), ('2031-05-19','xray',1,'WALKPATIENT FOUR','W99000452'), ('2031-05-18','proc',1,'WALKPATIENT SEVEN','W99007777');
""")
f.commit()
f.close()


def setup():
    t = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    return {"proc_use_slip", "proc_use", "proc_count"} <= t


ck("A1 the three new tables are there (made by the part at mount)", setup)


def client(user):
    c = ar.app.test_client()
    uid = db.execute("SELECT id FROM users WHERE username=?", (user,)).fetchone()[0]
    with c.session_transaction() as ss:
        ss["uid"] = uid
        ss["epoch"] = epoch
    return c


own, mgr = client("walk_own_s637"), client("walk_mgr_s637")


def flashes(cl):
    with cl.session_transaction() as ss:
        fl = list(ss.get("_flashes") or [])
        ss.pop("_flashes", None)
    return " | ".join(x[1] for x in fl)


def txt(h):
    return re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", h)).replace("&#34;", '"').replace("&quot;", '"').replace("&#39;", "'")


def iid(name):
    try:
        r = db.execute("SELECT id FROM proc_item WHERE name=?", (name,)).fetchone()
    except sqlite3.Error:
        return None
    return r[0] if r else None


def card(h, no):
    i = h.find('data-slip="%d"' % no)
    return h[i:h.find("</details>", i) + 400] if i >= 0 else ""


def uses(no):
    try:
        return [dict(r) for r in db.execute("SELECT u.* FROM proc_use u JOIN proc_use_slip s ON s.id=u.use_slip_id WHERE s.slip_no=? AND s.voided_at='' "
                                            "AND u.voided_at='' ORDER BY u.id", (no,))]
    except sqlite3.Error:
        return []


F4, R6, D600, GL, ZZ = iid('Fibrecast bandage 4"'), iid('Roller bandage 6"'), iid("Surgiwear D600 drape"), iid("Examination gloves"), iid("Zig-zag cotton 500 g")
po = own.get("/procroom/morning")
h = po.get_data(as_text=True)
wd = ("Somvaar", "Mangalvaar", "Budhvaar", "Guruvaar", "Shukravaar", "Shanivaar", "Ravivaar")[datetime.date(2031, 5, 19).weekday()]
ck("N1 the owner sees the screen first (off for the staff): “Kal ke procedures — 19-05-2031, %s”; Docterz has 2 of its 3 procedure slips; no rupee" % wd,
   lambda: po.status_code == 200 and "Off for the staff" in h and "Kal ke procedures — 19-05-2031, %s" % wd in txt(h) and "Slips jo Docterz mein bhi hain: 2" in txt(h)
   and "Slip jo Docterz mein nahi (nahi hua): 1" in txt(h) and "₹" not in h, lambda: (po.status_code, txt(h)[:400]))
pm = mgr.get("/procroom/morning")
sm = mgr.post("/procroom/morning/save", data={"day": "2031-05-19", "u901_bkbelowkneefibrec_k1_s": '4"'})
menu_m = mgr.get("/desk/month").get_data(as_text=True)
ck("N2 switched off: Shavez is told it is closed, it is not in his menu, and his Save writes nothing",
   lambda: pm.status_code == 200 and "abhi band hai" in pm.get_data(as_text=True) and "Kal ke procedures" not in re.sub(r"<h2>.*?</h2>", "", menu_m)
   and "abhi band hai" in sm.get_data(as_text=True) and uses(9187) == [], lambda: (pm.status_code, sm.status_code))
c1, c2 = card(h, 9187), card(h, 9188)
ck("N3 slip 9187 (B/K fibre cast): cast padding, Fibrecast and roller by size and count, stockinette and the D600 drape as ticks, gloves 2 joda, the patient and ID …4821; "
   "slip 9188 (ILI): the injection one of two and the D600 tick, gloves 1; slip 9190 “nahi hua”; the X-ray-only slip is not there",
   lambda: all(x in txt(c1) for x in ("Cast padding", "Fibrecast bandage", "Roller bandage", "Stockinette", "D600 drape", "Gloves: 2 joda", "WALKPATIENT ONE", "ID …4821"))
   and '<option value="5&#34;">' in c1.replace('5"', "5&#34;") and all(x in txt(c2) for x in ("Loftypred 80 mg", "Viracort 40", "Surgiwear D600 drape", "Gloves: 1 joda"))
   and "Slip 9190 · B/K (Below knee) fibre cast — L — Docterz mein nahi hai, isliye nahi hua maana" in txt(h) and "9191" not in h, lambda: (txt(c1)[:500], txt(c2)[:300]))
sw = own.post("/procroom/morning/switch", data={"to": "on"})
flashes(own)
pm2 = mgr.get("/procroom/morning").get_data(as_text=True)
menu_m2 = mgr.get("/desk/month").get_data(as_text=True)
ck("N4 switched on by him: “Kal ke procedures” in Shavez's menu, and the screen opens for him without the owner's note",
   lambda: sw.status_code == 302 and re.search(r'href="[^"]*/procroom/morning"[^>]*>Kal ke procedures<', menu_m2) is not None and "Kal ke procedures — 19-05-2031" in txt(pm2)
   and "Off for the staff" not in pm2, lambda: re.findall(r'href="[^"]*morning[^"]*"', menu_m2)[:3])


def keys(h, no):
    return re.findall(r'name="(u%d_[^"]+)"' % {9187: 901, 9188: 902, 9175: 906}[no], h)


k1, k2 = keys(pm2, 9187), keys(pm2, 9188)
fk = lambda ks, word, end: next((k for k in ks if word in k and k.endswith(end)), "")  # noqa: E731
form = {"day": "2031-05-19", "refs": re.findall(r'name=refs value="([^"]+)"', pm2)}
fib = [k for k in k1 if k.endswith("_s")]
form[fib[1] if len(fib) > 1 else "x"] = '4"'                      # the Fibrecast line (cast padding, fibrecast, roller -- in the kit's order)
form[(fib[1] if len(fib) > 1 else "x")[:-2] + "_q"] = "3"
form[fib[2] if len(fib) > 2 else "y"] = '6"'
form[(fib[2] if len(fib) > 2 else "y")[:-2] + "_q"] = "1"
ticks1 = [k for k in k1 if k.endswith("_c")]
form[ticks1[0] if ticks1 else "z"] = "1"                         # stockinette
o2 = [k for k in k2 if k.endswith("_o")]
form[o2[0] if o2 else "o"] = "Loftypred 80 mg"
t2 = [k for k in k2 if k.endswith("_c")]
form[t2[0] if t2 else "t"] = "1"                                 # the D600 drape on the ILI
s5 = mgr.post("/procroom/morning/save", data=form)
f5 = flashes(mgr)
u1, u2 = uses(9187), uses(9188)
ck("N5 Shavez's one Save: 9187 -- 3 Fibrecast 4\", 1 Roller 6\", stockinette, gloves 2 pairs by themselves; 9188 -- Loftypred (by its name), the D600 drape, gloves 1 pair",
   lambda: s5.status_code == 302 and "Save ho gaya — 2 slip, 7 cheezein" in f5 and sorted((u["item_id"], u["qty"], u["src"]) for u in u1 if u["item_id"]) ==
   sorted([(F4, 3, "kit"), (R6, 1, "kit"), (GL, 2, "gloves")]) and any(u["name"] == "Stockinette" for u in u1)
   and sorted((u["item_id"], u["qty"], u["src"]) for u in u2 if u["item_id"]) == sorted([(D600, 1, "kit"), (GL, 1, "gloves")]) and any(u["name"] == "Loftypred 80 mg" and u["item_id"] is None for u in u2)
   and all(u["unit"] == "pair" for u in u1 + u2 if u["src"] == "gloves"), lambda: (f5, u1, u2))
s6 = mgr.post("/procroom/morning/save", data=form)
f6 = flashes(mgr)
try:
    n_slip = db.execute("SELECT COUNT(*) FROM proc_use_slip").fetchone()[0]
except sqlite3.Error:
    n_slip = -1
ck("N6 the same Save again: nothing written (“kuch nahi badla”)", lambda: "kuch nahi badla" in f6 and n_slip == 2, lambda: (f6, n_slip))
p18 = mgr.get("/procroom/morning?day=2031-05-18").get_data(as_text=True)
c18 = card(p18, 9175)
ck("N7 the next cast (18-05) is pre-filled from the last time: Fibrecast 4\" × 3, Roller 6\" × 1, stockinette ticked -- and 18-05 is offered on 19-05's screen as a day still to fill",
   lambda: re.search(r'<option value="4&#34;" selected>|<option value="4\\" selected>', c18.replace('4"', "4&#34;")) is not None and 'value="3"' in c18 and "checked" in c18
   and "18-05 (1)" in txt(pm2), lambda: (txt(c18)[:300], txt(pm2)[txt(pm2).find("Baaki"):][:120]))
bad = dict(form)
bad[(fib[1] if len(fib) > 1 else "x")] = ""
bad[(fib[1] if len(fib) > 1 else "x")[:-2] + "_q"] = "5"
s8 = mgr.post("/procroom/morning/save", data=bad)
f8 = flashes(mgr)
ck("N8 a count without its size is refused, with the words; nothing saved", lambda: "size chunein" in f8 and "Kuch save nahi hua" in f8 and [u["qty"] for u in uses(9187) if u["item_id"] == F4] == [3],
   lambda: f8)
p17 = mgr.get("/procroom/morning?day=2031-05-17").get_data(as_text=True)
ck("N9 a day Docterz's report has not come for (17-05): every procedure slip is shown, said so", lambda: "Docterz ki report abhi nahi aayi" in p17 and 'data-slip="9160"' in p17, lambda: txt(p17)[:300])
# his page
own.post("/procroom/item", data={"id": F4, "do": "edit", "name": 'Fibrecast bandage 4"', "unit": "roll", "how": "patient", "brands": "Gloster, Duracast, Primecast", "aliases": "", "reorder": "8"})
flashes(own)
own.post("/procroom/count", data={"day": "18-05-2031", "c%d" % F4: "10", "c%d" % GL: "2", "back": "ym=2031-05"})
fc = flashes(own)
t = own.get("/procroom?ym=2031-05").get_data(as_text=True)


def srow(h, i):
    j = h.find('data-stock="%s"' % i)
    return txt(h[j:h.find("</tr>", j)]) if j >= 0 else ""


ck("S1 his page: Fibrecast bandage 4\" used 3 roll; counted 10 on 18-05 -- stock 7 roll, under his reorder level 8: “Order now”, and Worth a look says so",
   lambda: "Counts saved (2 products)" in fc and "3 roll" in srow(t, F4) and "7 roll" in srow(t, F4) and "Order now" in srow(t, F4)
   and 'Order now — 1 under your reorder level: Fibrecast bandage 4"' in txt(t), lambda: (fc, srow(t, F4), txt(t)[txt(t).find("Worth a look"):][:300]))
g1 = srow(t, GL)
own.post("/procroom/allow", data={"cast": "2", "ili": "1", "box": "50", "await": "3", "back": "ym=2031-05"})
flashes(own)
g2 = srow(own.get("/procroom?ym=2031-05").get_data(as_text=True), GL)
ck("S2 gloves are used in pairs and bought in boxes: without his box size the stock says so; with 50 a box it is 1.94 box (2 - 3 pairs)",
   lambda: "set the gloves box size" in g1 and "3 pairs" in g1 and "1.94 box" in g2, lambda: (g1, g2))
zb = db.execute("INSERT INTO bills(kind, vendor, stamp_no, status, lane, created_at, submitted_at, submitted_by, doc_kind, bill_date, subgroup) "
                "VALUES('Consumable','WALK637 YUVIKA SURGICALS','Z-2031-M1','approved','clinic','2031-05-12 05:00:00','2031-05-12 05:00','Walk','estimate','2031-05-12','procedure')").lastrowid
db.execute("INSERT INTO proc_line(bill_id, bill_created_at, line_no, name, qty, unit, item_id, place, rate, day, ts) VALUES(?,?,1,'Zig zag',4,'pack',?,'proc',13,'2031-05-12',0)",
           (zb, "2031-05-12 05:00:00", ZZ))
db.commit()
t = own.get("/procroom?ym=2031-05").get_data(as_text=True)
mseg = txt(t[t.find("id=s637match"):][:1500])
ck("S3 the month-end match for May 2031: casts and slabs 1, injections 1; Zig-zag cotton bought 4 -- 20.0 per 10 procedures",
   lambda: "Casts and slabs: 1 · injections (ILI): 1 · other procedures: 0" in mseg and re.search(r"Zig-zag cotton 500 g 4 pack 20\.0", mseg) is not None, lambda: mseg[:500])
pm3 = mgr.get("/procroom/morning").get_data(as_text=True)
ck("S4 Shavez's screen carries no rupee and no rate, and his page is his alone (the manager is refused)",
   lambda: "₹" not in pm3 and "rate" not in txt(pm3).lower() and mgr.get("/procroom?ym=2031-05").status_code in (302, 403)
   and mgr.post("/procroom/count", data={"c%d" % F4: "1", "day": "19-05-2031"}).status_code in (302, 403), lambda: txt(pm3)[:200])
# K1 round 1: two of one procedure on a slip; a slip that came after the page was opened; Docterz's later "nahi hua"; the clavicle
f = sqlite3.connect(FDB)
f.executescript("""
INSERT INTO owner_service(id, kind, name, grp) VALUES (5,'proc','Clavicle bandage','Cast / slab');
INSERT INTO owner_service_item(service_id, item, ask, sizes) VALUES (5,'Roller bandage','size_qty','4",6"');
INSERT INTO slip(id, series, slip_no, day, clinic_id) VALUES (908,'xp',9150,'2031-05-16','W99001111'), (910,'xp',9140,'2031-05-15','W99002222');
INSERT INTO slip_item(slip_id, kind, service_id, name, side, sort) VALUES (908,'proc',1,'B/K (Below knee) fibre cast','R',1), (908,'proc',1,'B/K (Below knee) fibre cast','L',2),
 (910,'proc',5,'Clavicle bandage','',1);
INSERT INTO clinic_day_revenue VALUES ('2031-05-16','2031-05-16 23:00'), ('2031-05-15','2031-05-15 23:00');
INSERT INTO clinic_day_line(business_date, section, sn, patient, clinic_id) VALUES ('2031-05-16','proc',1,'WALKPATIENT EIGHT','W99001111'), ('2031-05-15','proc',1,'WALKPATIENT TEN','W99002222');
""")
f.commit()
f.close()
p16 = mgr.get("/procroom/morning?day=2031-05-16").get_data(as_text=True)
k16 = re.findall(r'name="(u908_[^"]+_s)"', p16)
f16 = {"day": "2031-05-16", "refs": re.findall(r'name=refs value="([^"]+)"', p16)}
fr = [k for k in k16 if k.startswith("u908_p1_")]
fl_ = [k for k in k16 if k.startswith("u908_p2_")]
if len(fr) > 1 and len(fl_) > 1:
    f16[fr[1]], f16[fr[1][:-2] + "_q"] = '4"', "3"
    f16[fl_[1]], f16[fl_[1][:-2] + "_q"] = '3"', "2"
f = sqlite3.connect(FDB)                                             # a slip written into the book AFTER the page was opened
f.executescript("INSERT INTO slip(id, series, slip_no, day, clinic_id) VALUES (909,'xp',9151,'2031-05-16','W99001112');"
                "INSERT INTO slip_item(slip_id, kind, service_id, name, side) VALUES (909,'proc',1,'B/K (Below knee) fibre cast','R');"
                "INSERT INTO clinic_day_line(business_date, section, sn, patient, clinic_id) VALUES ('2031-05-16','proc',2,'WALKPATIENT NINE','W99001112');")
f.commit()
f.close()
s16 = mgr.post("/procroom/morning/save", data=f16)
fs16 = flashes(mgr)
u16 = uses(9150)
F3 = iid('Fibrecast bandage 3"')
ck('N10 one slip with the same cast on both sides (R and L): each its own lines -- 3 Fibrecast 4" and 2 Fibrecast 3" -- and gloves for two casts (4 pairs)',
   lambda: sorted((u["item_id"], u["qty"]) for u in u16 if u["src"] == "kit") == sorted([(F4, 3), (F3, 2)]) and [u["qty"] for u in u16 if u["src"] == "gloves"] == [4]
   and "B/K (Below knee) fibre cast — L" in txt(card(p16, 9150)), lambda: (fs16, u16))
ck("N11 a slip written into the book after the page was opened is not saved from that page -- said so: “Naya slip 9151 aaya hai — page dobara kholein”",
   lambda: "Naya slip 9151 aaya hai — page dobara kholein" in fs16 and uses(9151) == [], lambda: fs16)


def as_browser(h):
    """The morning form as a browser would send it unchanged: every input's value (a checkbox only when checked), each select's
    selected option (else its first)."""
    import html as _h
    i = h.find('action="'); h = h[h.find("<form", i - 200):]
    h = h[:h.find("</form>")]
    data = []
    for m in re.finditer(r"<input([^>]*)>", h):
        a = m.group(1)
        nm = re.search(r'name="?([^" >]+)"?', a)
        if not nm:
            continue
        ty = (re.search(r'type="?(\w+)', a) or [None, "text"])[1]
        if ty == "checkbox" and " checked" not in a:
            continue
        v = re.search(r'value="([^"]*)"', a)
        data.append((nm.group(1), _h.unescape(v.group(1)) if v else ("1" if ty == "checkbox" else "")))
    for m in re.finditer(r'<select name="([^"]+)"[^>]*>(.*?)</select>', h, flags=re.S):
        opts = re.findall(r'<option value="?([^" >]*)"?([^>]*)>', m.group(2))
        sel = next((o[0] for o in opts if "selected" in o[1]), opts[0][0] if opts else "")
        data.append((m.group(1), _h.unescape(sel)))
    out = {}
    for k, v in data:
        out.setdefault(k, []).append(v)
    return out


p16b = mgr.get("/procroom/morning?day=2031-05-16").get_data(as_text=True)
try:
    rec0 = db.execute("SELECT id FROM proc_use_slip WHERE slip_no=9150 AND voided_at=''").fetchone()[0]
except (sqlite3.Error, TypeError):
    rec0 = -1
s16b = mgr.post("/procroom/morning/save", data=as_browser(p16b))
fs16b = flashes(mgr)
u16b = uses(9150)
ck('N14 the same day reopened and saved as the browser fills it: the slip with R and L is not rewritten -- still 3 Fibrecast 4" and 2 Fibrecast 3"',
   lambda: sorted((u["item_id"], u["qty"]) for u in u16b if u["src"] == "kit") == sorted([(F4, 3), (F3, 2)])
   and db.execute("SELECT id FROM proc_use_slip WHERE slip_no=9150 AND voided_at=''").fetchone()[0] == rec0 != -1,
   lambda: (fs16b, [(u["item_id"], u["size"], u["qty"]) for u in u16b]))
p17b = mgr.get("/procroom/morning?day=2031-05-17").get_data(as_text=True)
k17 = re.findall(r'name="(u907_[^"]+_s)"', p17b)
f17 = {"day": "2031-05-17", "refs": re.findall(r'name=refs value="([^"]+)"', p17b)}
if k17:
    f17[k17[0]], f17[k17[0][:-2] + "_q"] = '4"', "1"
mgr.post("/procroom/morning/save", data=f17)
flashes(mgr)
saved17 = len(uses(9160)) == 1
f = sqlite3.connect(FDB)
f.execute("INSERT INTO clinic_day_revenue VALUES ('2031-05-17','2031-05-17 23:00')")          # Docterz comes: no procedure for that ID
f.commit()
f.close()
t = own.get("/procroom?ym=2031-05").get_data(as_text=True)
R4 = iid('Roller bandage 4"')
ck("N12 a slip saved before Docterz's report, which then does not have it (nahi hua): left out of what was used, and his page says so",
   lambda: saved17 and "1 saved procedure slip Docterz later did not have (nahi hua)" in txt(t) and "—" in srow(t, R4).split("Roller bandage 4\"")[-1][:6], lambda: (saved17, srow(t, R4)))
p15 = mgr.get("/procroom/morning?day=2031-05-15").get_data(as_text=True)
c15 = card(p15, 9140)
ck("N13 the clavicle bandage is neither a cast nor a slab (his ruling): no gloves, no D600 tick", lambda: "Clavicle bandage" in txt(c15) and "Gloves:" not in txt(c15) and "> D600 drape</label>" not in c15 and "> D600 drape</label>" in card(pm2, 9187),
   lambda: txt(c15)[:300])
# Kit 1-2 and the old pages keep answering (green on both sides)
ck("K1 his Procedure room page, the month end and the FY still answer", lambda: all(own.get(u).status_code == 200 for u in ("/procroom", "/procroom?fy=2031", "/procroom/month?ym=2031-05")))
ck("R2 the desk, The month, Stationery, X-ray and the Machines list still answer for the owner", lambda: all(own.get(u).status_code == 200 for u in ("/desk", "/desk/month", "/stationery", "/xray", "/assets")),
   lambda: [(u, own.get(u).status_code) for u in ("/desk", "/desk/month", "/stationery", "/xray", "/assets")])
db.close()
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad_ = [k for k in MUST_RED if RES.get(k, True)] + [k for k in red if k not in MUST_RED]
    print("WALK S637 APP CONTROL: %d red; %s" % (len(red), "AS IT MUST BE" if not bad_ else "NOT AS IT MUST BE: " + ", ".join(bad_)))
    sys.exit(0 if not bad_ else 1)
print("WALK S637 APP: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
