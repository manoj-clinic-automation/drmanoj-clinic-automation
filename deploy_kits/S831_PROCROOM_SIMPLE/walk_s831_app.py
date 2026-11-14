#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s831_app.py -- S831_PROCROOM_SIMPLE on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch
folder with the given procroom.py (TO -- or FROM for the control), on a COPY of a database (SQLite's backup API) -- or a fresh one the
app makes itself. Made-up rows only, dated 2031 (papers "Z-2031-..."); a MADE-UP slip book and Docterz day in a made-up finance
database with the LIVE table shapes (slip, slip_item with discount_p, slip_adjust, owner_service, owner_service_item, clinic_day_*,
patient_ref) -- never the real one; made-up owner and manager logins; no reader, no paid call, nothing sent; Flask's test client, no
port. The scratch folder is removed at the end; the database given is only read (copied).

    python3 -B walk_s831_app.py --live <the app folder> --files <folder holding procroom.py to test> [--db <assets.db>] [--expect-red]
"""
import ast
import datetime
import hashlib
import io
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
GREEN_BOTH = ("S2", "G1", "G2", "G3")                                   # the control (S656's file): the staff screens, the slip book, the other pages green on both

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s831app_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):                                   # the app's CODE only (top-level .py / .js / .json) -- never a stored scan
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        for f in KIT_FILES:
            shutil.copy(os.path.join(FILES, f), os.path.join(app, f))
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
                   FINANCE_DB_FOR_SCANS=os.path.join(work, "madeup_finance.db"))
        for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
            env.pop(k, None)
        r = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--inner", app] + ARGS, env=env, cwd=work,
                           capture_output=True, text=True, timeout=300)
        sys.stdout.write(r.stdout)
        for l in r.stderr.splitlines():
            if "NOT mounted" in l or "S831" in l or "procroom" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S831_WALK_DEBUG"):
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
    return re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", h)).replace("&#34;", '"').replace("&quot;", '"').replace("&#39;", "'").replace("&amp;", "&")


import asset_register as ar                                          # noqa: E402

mods = {m: sys.modules.get(m) for m in PARTS}
pr = mods.get("procroom")
ck("S0 the real app loads with its seven parts mounted; procroom.py is S831's, with its month Save's door (%s)" % ", ".join(m for m, x in mods.items() if x is not None),
   lambda: all(mods.values()) and pr.MOUNTED and pr.VERSION == "S831" and "s831_used" in ar.app.view_functions)
TODAY = datetime.date(2031, 5, 20)
for m in ("sorting_desk", "procroom", "stationery", "asset_machine", "batteries", "xray_costs"):
    if mods.get(m) is not None:
        mods[m].TODAY = TODAY
pr.NO_THREAD = True
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
for k, v in (("read.claude", "off"), ("desk.on", "on"), ("proc.morning", "on"), ("proc.morning_from", "2031-05-01"), ("proc.gloves_cast", "2"),
             ("proc.gloves_ili", "0"), ("proc.gloves_box", "50")):
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (k, v))
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col, spec in (("page_of", "INTEGER"), ("mixed", "INTEGER"), ("subgroup", "TEXT")):
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s %s" % (col, spec))
for u, role in (("walk_own_s831", "owner"), ("walk_mgr_s831", "manager")):
    if not db.execute("SELECT 1 FROM users WHERE username=?", (u,)).fetchone():
        db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (u, "Walk " + role, role))
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
# a COPY of the live database: its own procedure-room records are set aside IN THE COPY ONLY (voided, the papers moved out of the group,
# the product list re-made from the owner's S342 list), so the walk counts its made-up rows alone; the live database is only read
aside = 0
for t_ in ("proc_line", "proc_slip", "proc_paper", "proc_photo", "proc_use_slip", "proc_use", "proc_count"):
    try:
        aside += db.execute("UPDATE %s SET voided_at='walk831 copy' WHERE voided_at=''" % t_).rowcount
    except sqlite3.Error:
        pass
aside += db.execute("DELETE FROM proc_item").rowcount
db.execute("DELETE FROM settings WHERE key=?", (pr.SEED_KEY,))
aside += db.execute("UPDATE bills SET subgroup='walk831_aside' WHERE COALESCE(subgroup,'')='procedure'").rowcount
db.commit()
print("      (the copy's own procedure-room rows set aside in the copy: %d)" % aside)
pr.seed_step(dbp, out=lambda *_: None)
# the MADE-UP slip book, in the live shapes (read 14-Nov-2026 from the nightly copy: schema only)
FDB = os.environ["FINANCE_DB_FOR_SCANS"]
f = sqlite3.connect(FDB)
f.executescript("""
CREATE TABLE slip (id INTEGER PRIMARY KEY AUTOINCREMENT, series TEXT NOT NULL CHECK (series IN ('opd','xp')), slip_no INTEGER NOT NULL, day TEXT NOT NULL,
  clinic_id TEXT NOT NULL DEFAULT '', no_id_name TEXT NOT NULL DEFAULT '', is_new INTEGER NOT NULL DEFAULT 0, name_seen TEXT NOT NULL DEFAULT '',
  state TEXT NOT NULL DEFAULT 'ok' CHECK (state IN ('ok','missing','cancelled','spoilt','void')), note TEXT NOT NULL DEFAULT '', paid_mode TEXT NOT NULL DEFAULT '',
  paid_by TEXT NOT NULL DEFAULT '', paid_at TEXT NOT NULL DEFAULT '', done_by TEXT NOT NULL DEFAULT '', done_at TEXT NOT NULL DEFAULT '',
  logged_by TEXT NOT NULL DEFAULT '', logged_at TEXT NOT NULL DEFAULT '', updated_by TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT '');
CREATE TABLE slip_item (id INTEGER PRIMARY KEY AUTOINCREMENT, slip_id INTEGER NOT NULL REFERENCES slip(id), kind TEXT NOT NULL CHECK (kind IN ('xray','proc')),
  service_id INTEGER, name TEXT NOT NULL DEFAULT '', side TEXT NOT NULL DEFAULT '', price_p INTEGER NOT NULL DEFAULT 0, sort INTEGER NOT NULL DEFAULT 0,
  discount_p INTEGER NOT NULL DEFAULT 0);
CREATE TABLE slip_adjust (id INTEGER PRIMARY KEY AUTOINCREMENT, slip_id INTEGER NOT NULL, item_id INTEGER, kind TEXT NOT NULL CHECK (kind IN ('discount','free','cancel')),
  amount_p INTEGER NOT NULL DEFAULT 0, reason TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '', cancel_how TEXT NOT NULL DEFAULT '', clinic_id TEXT NOT NULL DEFAULT '',
  day TEXT NOT NULL, made_by TEXT NOT NULL, made_at TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','approved','rejected','replaced')),
  checked_by TEXT NOT NULL DEFAULT '', checked_at TEXT NOT NULL DEFAULT '', check_note TEXT NOT NULL DEFAULT '');
CREATE TABLE owner_service (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, name TEXT NOT NULL, price_p INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1,
  note TEXT NOT NULL DEFAULT '', created_by TEXT NOT NULL DEFAULT '', created_ts TEXT NOT NULL DEFAULT '', updated_by TEXT NOT NULL DEFAULT '', updated_ts TEXT NOT NULL DEFAULT '',
  code TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'pending', seen INTEGER NOT NULL DEFAULT 0, grp TEXT NOT NULL DEFAULT '', forms TEXT NOT NULL DEFAULT '',
  source TEXT NOT NULL DEFAULT '', side TEXT NOT NULL DEFAULT '');
CREATE TABLE owner_service_item (id INTEGER PRIMARY KEY AUTOINCREMENT, service_id INTEGER NOT NULL REFERENCES owner_service(id), item TEXT NOT NULL,
  qty REAL NOT NULL DEFAULT 1, unit TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '', added_by TEXT NOT NULL DEFAULT '', added_ts TEXT NOT NULL DEFAULT '',
  ask TEXT NOT NULL DEFAULT '', sizes TEXT NOT NULL DEFAULT '');
CREATE TABLE clinic_day_line (business_date TEXT NOT NULL, section TEXT NOT NULL, sn INTEGER NOT NULL, patient TEXT NOT NULL DEFAULT '', clinic_id TEXT NOT NULL DEFAULT '',
  amount_p INTEGER NOT NULL DEFAULT 0, mode TEXT NOT NULL DEFAULT '', shift TEXT NOT NULL DEFAULT '', gateway_ref TEXT NOT NULL DEFAULT '', PRIMARY KEY (business_date, section, sn));
CREATE TABLE clinic_day_revenue (business_date TEXT PRIMARY KEY, source_file TEXT NOT NULL DEFAULT '', source_id TEXT NOT NULL DEFAULT '', source_mtime TEXT NOT NULL DEFAULT '',
  taken_at TEXT NOT NULL DEFAULT '', cons_count INTEGER NOT NULL DEFAULT 0, cons_amount_p INTEGER NOT NULL DEFAULT 0, xray_count INTEGER NOT NULL DEFAULT 0,
  xray_amount_p INTEGER NOT NULL DEFAULT 0, proc_count INTEGER NOT NULL DEFAULT 0, proc_amount_p INTEGER NOT NULL DEFAULT 0, total_count INTEGER NOT NULL DEFAULT 0,
  total_amount_p INTEGER NOT NULL DEFAULT 0, morning INTEGER, evening INTEGER, free_revisits INTEGER NOT NULL DEFAULT 0, free_concession INTEGER NOT NULL DEFAULT 0,
  f93_phantom_rows INTEGER NOT NULL DEFAULT 0, tender_json TEXT NOT NULL DEFAULT '', sheet_total_p INTEGER, sheet_cash_p INTEGER, sheet_online_p INTEGER,
  variance_note TEXT NOT NULL DEFAULT '');
CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT NOT NULL UNIQUE, name TEXT, phone_last4 TEXT, first_seen TEXT, merged_into INTEGER, note TEXT);
INSERT INTO owner_service(id, kind, name, grp, status) VALUES (1,'proc','B/K (Below knee) fibre cast','Cast / slab','approved'), (2,'proc','ILI (heel)','Injection (ILI)','approved'),
  (3,'proc','Dressing','Dressing','approved'), (4,'xray','KNEE AP/LAT','','approved');
INSERT INTO owner_service_item(id, service_id, item, ask, sizes) VALUES
  (1,1,'Cast padding','size_qty','4",6"'), (2,1,'Fibrecast bandage','size_qty','2",3",4",5"'), (3,1,'Roller bandage','size_qty','4",6"'), (4,1,'Stockinette','used_yesno',''),
  (5,2,'Inj Loftypred 80 mg OR Inj Viracort 40','one_of','Loftypred 80 mg / Viracort 40'), (6,2,'Surgiwear D600 drape','selectable',''), (7,3,'Roller bandage','size_qty','4",6"');
INSERT INTO slip(id, series, slip_no, day, clinic_id) VALUES (901,'xp',9187,'2031-05-19','W99004821'), (902,'xp',9188,'2031-05-19','W99003307'),
  (903,'xp',9190,'2031-05-19','W99006190'), (904,'xp',9191,'2031-05-19','W99000452'), (905,'opd',9999,'2031-05-19','W99000001'),
  (906,'xp',9175,'2031-05-18','W99007777'), (907,'xp',9160,'2031-05-17','W99008888'), (908,'xp',9161,'2031-05-17','W99008889'),
  (909,'xp',9150,'2031-04-20','W99001111'), (910,'xp',9192,'2031-05-20','W99001234');
INSERT INTO slip_item(id, slip_id, kind, service_id, name, side, price_p, discount_p) VALUES
  (1,901,'proc',1,'B/K (Below knee) fibre cast','R',150000,0), (2,902,'proc',2,'ILI (heel)','L',80000,10000), (3,903,'proc',1,'B/K (Below knee) fibre cast','L',150000,0),
  (4,904,'xray',4,'KNEE AP/LAT','',40000,0), (5,906,'proc',1,'B/K (Below knee) fibre cast','R',150000,50000), (6,907,'proc',3,'Dressing','',30000,0),
  (7,908,'proc',2,'ILI (heel)','R',80000,0), (8,909,'proc',1,'B/K (Below knee) fibre cast','R',150000,0), (9,910,'proc',2,'ILI (heel)','L',80000,0);
INSERT INTO slip_adjust(slip_id, item_id, kind, amount_p, day, made_by, made_at, state) VALUES
  (902,2,'discount',10000,'2031-05-19','walk','2031-05-19 10:00','approved'), (906,5,'discount',50000,'2031-05-18','walk','2031-05-18 10:00','rejected'),
  (908,NULL,'cancel',0,'2031-05-17','walk','2031-05-17 11:00','approved');
INSERT INTO clinic_day_revenue(business_date, taken_at) VALUES ('2031-05-19','2031-05-19 23:00'), ('2031-05-18','2031-05-18 23:00');
INSERT INTO clinic_day_line(business_date, section, sn, patient, clinic_id) VALUES ('2031-05-19','proc',1,'WALKPATIENT ONE','W99004821'),
  ('2031-05-19','proc',2,'WALKPATIENT TWO','W99003307'), ('2031-05-19','xray',1,'WALKPATIENT FOUR','W99000452'), ('2031-05-18','proc',1,'WALKPATIENT SEVEN','W99007777');
""")
f.commit()
f.close()


def fmd5():
    return hashlib.md5(open(FDB, "rb").read()).hexdigest()


F0 = fmd5()


def client(user):
    c = ar.app.test_client()
    uid = db.execute("SELECT id FROM users WHERE username=?", (user,)).fetchone()[0]
    with c.session_transaction() as ss:
        ss["uid"] = uid
        ss["epoch"] = epoch
    return c


own, mgr = client("walk_own_s831"), client("walk_mgr_s831")


def flashes(cl):
    with cl.session_transaction() as ss:
        fl = list(ss.get("_flashes") or [])
        ss.pop("_flashes", None)
    return " | ".join(x[1] for x in fl)


def iid(name):
    r = db.execute("SELECT id FROM proc_item WHERE name=?", (name,)).fetchone()
    return r[0] if r else None


def mk(tag, vendor, created, **cols):
    vals = dict(kind="Consumable", vendor=vendor, stamp_no="Z-2031-" + tag, status="draft", lane="clinic", created_at=created,
                submitted_at=created[:16], submitted_by="Walk", doc_kind="challan", bill_date=created[:10], subgroup="procedure")
    vals.update(cols)
    bid = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
    db.commit()
    return bid


def page(ym=None, cl=None, **kw):
    r = (cl or own).get("/procroom", query_string=dict(({"ym": ym} if ym else {}), **kw))
    return r.status_code, r.get_data(as_text=True)


def block(h, start, end):
    i = h.find(start)
    return h[i:h.find(end, i + len(start))] if i >= 0 else ""


def row(h, attr):
    i = h.find(attr)
    return h[i:h.find("</tr>", i)] if i >= 0 else ""


def uses(ref):
    return [dict(r) for r in db.execute("SELECT u.*, s.by_whom AS who, s.id AS sid FROM proc_use u JOIN proc_use_slip s ON s.id=u.use_slip_id "
                                        "WHERE s.slip_ref=? AND s.voided_at='' AND u.voided_at='' ORDER BY u.id", (ref,))]


def recs(ref):
    return [dict(r) for r in db.execute("SELECT * FROM proc_use_slip WHERE slip_ref=? ORDER BY id", (ref,))]


F4, F5, GL = iid('Fibrecast bandage 4"'), iid('Fibrecast bandage 5"'), iid("Examination gloves")
D1 = mk("D1", "WALK831 YUVIKA SURGICALS", "2031-05-12 05:00:00")
D2 = mk("D2", "WALK831 YUVIKA SURGICALS", "2031-05-15 05:00:00")
own.post("/procroom/slip", data={"day": "12-05-2031", "supplier": "WALK831 YUVIKA SURGICALS", "paper": "Z-2031-D1",
                                 "i1": str(F4), "q1": "10", "p1": "proc", "r1": "200", "i2": str(GL), "q2": "2", "p2": "proc", "r2": "300",
                                 "n3": "WALK831 kettle", "q3": "1", "p3": "home", "r3": "500"})
fl_d1 = flashes(own)
own.post("/procroom/slip", data={"day": "20-04-2031", "supplier": "WALK831 YUVIKA SURGICALS", "note": "made-up April", "i1": str(F5), "q1": "4", "p1": "proc", "r1": "250"})
fl_apr = flashes(own)
up = own.post("/procroom/month/photos", data={"ym": "2031-05", "photos": [(io.BytesIO(b"\xff\xd8\xff\xe0WALK831-" + os.urandom(64)), "walk831_may.jpg")]},
              content_type="multipart/form-data")
flashes(own)

st, h = page()
ck("S1 his page answers (200) with the new shape: the title, the month picker, six tiles each a link, Start here, the financial year, Stock now, a fixed Top",
   lambda: st == 200 and 'id=s831' in h and len(re.findall(r'<a class=tile href="#', h)) == 6 and "Start here — three steps keep the stock correct" in h
   and "Expenses and revenue — financial year 2031-32" in h and "id=s637stock" in h and 'class=s831top' in h and "↑ Top" in h and 'type=month name=ym' in h,
   lambda: (st, fl_d1, txt(h)[:300]))
pm, hm = page(cl=mgr)
pm2 = mgr.post("/procroom/used", data={"ym": "2031-05", "refs": "xp:901", "u901_p1_k2_s": '4"', "u901_p1_k2_q": "3"})
ck("S2 his only: Shavez is refused the page and its month Save (nothing written)",
   lambda: pm != 200 and "id=s831" not in hm and pm2.status_code != 302 and recs("xp:901") == [], lambda: (pm, pm2.status_code))
tl = {t: txt(block(h, 'data-t=%s' % t, "</a>")) for t in ("spent", "rev", "done", "fib", "wait", "morning")}
ck("S3 the tiles of May 2031: spent ₹2,600 (1 dealer challan counted; the kettle kept at home apart); revenue ₹4,800 — ILI ₹1,500 · others ₹3,300 "
   "(a rejected discount not taken off, an approved one taken off; 'nahi hua' and the cancelled slip left out); procedures 5 — 2 casts / slabs · 2 ILI · 1 other",
   lambda: "₹2,600" in tl["spent"] and "1 dealer challan counted" in tl["spent"] and "₹4,800" in tl["rev"] and "ILI ₹1,500 · others ₹3,300" in tl["rev"]
   and re.search(r"\b5 2 casts / slabs · 2 ILI · 1 other", tl["done"]) is not None, lambda: tl)
ck("S4 waiting for you: 2 — 1 dealer challan · 1 photo; Start here step 2 names Z-2031-D2 (on the desk, lines not saved) and Yuvika's May photo",
   lambda: re.search(r"\b2 1 dealer challan · 1 photo", tl["wait"]) is not None and "Z-2031-D2</a> dealer challan 15-05 — on the desk, lines not saved" in h
   and "Yuvika's May 2031 photo" in txt(h) and "STEP 2 · 2 WAITING" in h, lambda: (tl["wait"], txt(block(h, 'data-step=2', "</ul>"))))
may, apr = block(h, 'id="m2031-05"', 'id="m2031-04"'), block(h, 'id="m2031-04"', 'id=s831year')
yr = txt(block(h, 'id=s831year', "</div>"))
ck("S5 the year, X-ray page style: May open — bought 2,600 · 5 procedures · ILI 1,500 · others 3,300 · revenue less bought 2,200; April (before the floor) "
   "bought 1,000 and “—”; Year so far 3,600 · 5 · 1,500 · 3,300 · 2,200; NO per-procedure column",
   lambda: 'id="m2031-05" data-ym="2031-05" open' in h and re.search(r"May( [^<]*)? 2,600 5 1,500 3,300 2,200", txt(may[:900])) is not None
   and re.search(r"April 1,000 — — — —", txt(apr[:600])) is not None and "Year so far 3,600 5 1,500 3,300 2,200" in yr
   and "per procedure" not in h.lower(), lambda: (txt(may[:700]), txt(apr[:400]), yr))
bt = txt(block(may, "What was bought", "</details>"))
ck("S6 May's “What was bought”: Z-2031-D1 Fibrecast 4\" 10 roll at 200 = 2,000 and the gloves 2 box at 300 = 600; Z-2031-D2 “not saved on the desk yet”; "
   "the kettle said apart (kept elsewhere: 1 line, ₹500)",
   lambda: re.search(r'Z-2031-D1 WALK831 YUVIKA SURGICALS 12-05 Fibrecast bandage 4" 10 roll 200 2,000', bt) is not None
   and "Examination gloves 2 box 300 600" in bt and "Z-2031-D2 WALK831 YUVIKA SURGICALS 15-05 not saved on the desk yet" in bt
   and "Kept elsewhere on these dealer challans: 1 line, ₹500" in bt, lambda: bt[:600])
pd_ = block(may, "Procedures done", "</form>")
ck("S7 May's procedures, one row per PATIENT SLIP, newest first: 9192 (today), 9188, 9187, 9175, 9160 with their fees 800 · 700 · 1,500 · 1,500 · 300 and "
   "the patient's name; 9190 (nahi hua), 9161 (cancelled), 9191 (X-ray only) and April's 9150 not there; each “not filled yet” with its own tick",
   lambda: re.findall(r'data-pslip="(\d+)"', pd_) == ["9192", "9188", "9187", "9175", "9160"]
   and [txt(row(pd_, 'data-pslip="%s"' % n)).split(" ")[6 if n != "9160" else 5] for n in ()] == []
   and all(x in txt(row(pd_, 'data-pslip="%s"' % n)) for n, x in (("9188", " 700 "), ("9187", " 1,500 "), ("9175", " 1,500 "), ("9160", " 300 "), ("9192", " 800 ")))
   and "WALKPATIENT ONE" in txt(row(pd_, 'data-pslip="9187"')) and pd_.count("class=fillref") == 5 and pd_.count('class="nf"') == 5
   and "1 patient slip Docterz did not have (not done) left out" in txt(pd_), lambda: (re.findall(r'data-pslip="(\d+)"', pd_), txt(pd_)[:900]))
r = own.post("/procroom/used", data={"ym": "2031-05", "refs": ["xp:901"], "u901_p1_k2_s": '4"', "u901_p1_k2_q": "3", "u901_p1_k4_c": "1",
                                       "u902_p1_k6_c": "1"})
fl1 = flashes(own)
u901 = uses("xp:901")
ck("S8 he fills 9187 here (its tick): saved THROUGH THE MORNING SCREEN'S OWN SAVE — Fibrecast 4\" ×3, the stockinette, gloves 2 pairs by his allowance, "
   "in his name; 9188 (not ticked) not written though a field was changed; his words in English",
   lambda: r.status_code == 302 and "#m2031-05" in r.headers.get("Location", "") and sorted((u["item_id"] or 0, u["qty"], u["src"], u["name"]) for u in u901) ==
   sorted([(F4, 3.0, "kit", "Fibrecast bandage"), (0, 1.0, "kit", "Stockinette"), (GL, 2.0, "gloves", "Examination gloves")])
   and u901[0]["who"] == "Walk owner" and recs("xp:902") == [] and fl1.startswith("Saved — 1 patient slip changed"), lambda: (fl1, u901))
st2, h2 = page("2031-05")
r9187 = row(h2, 'data-pslip="9187"')
ck("S9 the page again: 9187 saved (no longer “not filled”) with Fibrecast 4\" × 3 shown for him to correct", lambda: 'class=""' in r9187[:60] and 'name=refs value="xp:901"' in r9187
   and re.search(r'name="u901_p1_k2_q" value="3"', r9187) is not None and "not filled yet" not in r9187, lambda: r9187[:500])
r = own.post("/procroom/used", data={"ym": "2031-05", "refs": ["xp:901"], "u901_p1_k2_s": '4"', "u901_p1_k2_q": "2", "u901_p1_k4_c": "1"})
fl2 = flashes(own)
rr = recs("xp:901")
own.post("/procroom/used", data={"ym": "2031-05", "refs": ["xp:901"], "u901_p1_k2_s": '4"', "u901_p1_k2_q": "2", "u901_p1_k4_c": "1"})
fl3 = flashes(own)
ck("S10 his correction replaces the entry (Fibrecast 4\" now 2): the earlier record voided and KEPT, a new one live; the same Save again writes nothing",
   lambda: len(rr) == 2 and rr[0]["voided_at"] != "" and rr[1]["voided_at"] == "" and [u["qty"] for u in uses("xp:901") if u["item_id"] == F4] == [2.0]
   and fl2.startswith("Saved — 1 patient slip changed") and fl3 == "Nothing changed." and len(recs("xp:901")) == 2, lambda: (rr, fl2, fl3))
r = own.post("/procroom/used", data={"ym": "2031-05", "refs": ["xp:901"], "u901_p1_k2_s": "", "u901_p1_k2_q": "4"})
fl4 = flashes(own)
ck("S11 a mistake is told in English and nothing is saved: “Patient slip 9187: choose a size. Nothing was saved.”",
   lambda: fl4 == "Patient slip 9187: choose a size. Nothing was saved." and len(recs("xp:901")) == 2, lambda: fl4)
fib0 = txt(block(h, 'data-t=fib', "</a>"))
ck("S12 Fibrecast in stock today before any count: 5\" 4\" 3\" 2\" each “—”, “after your first count”; step 1 NOT DONE",
   lambda: re.search(r'5" — 4" — 3" — 2" — after your first count', fib0) is not None and "STEP 1 · NOT DONE" in h, lambda: fib0)
r = own.post("/procroom/count", data={"back": "ym=2031-05", "day": "11-05-2031", "c%d" % F4: "5", "c%d" % GL: "114", "o%d" % F4: "20", "o%d" % GL: "40"})
fl5 = flashes(own)
cnt = {x["item_id"]: x["qty"] for x in db.execute("SELECT item_id, qty FROM proc_count WHERE voided_at=''")}
reo = {x["id"]: x["reorder"] for x in db.execute("SELECT id, reorder FROM proc_item")}
ck("S13 one Save of the counts and the reorder levels: Fibrecast 4\" 5 rolls (order below 20); gloves 114 PAIRS kept as 2.28 boxes of 50 pairs, "
   "order below 40 pairs kept as 0.8 box",
   lambda: cnt.get(F4) == 5 and abs(cnt.get(GL, 0) - 2.28) < 1e-9 and reo.get(F4) == 20 and abs((reo.get(GL) or 0) - 0.8) < 1e-9
   and fl5 == "Counts saved (2 products). Reorder levels saved (2).", lambda: (fl5, cnt, reo.get(F4), reo.get(GL)))
st3, h3 = page("2031-05")
g = txt(row(h3, 'data-stock="%d"' % GL))
f4 = txt(row(h3, 'data-stock="%d"' % F4))
fib1 = txt(block(h3, 'data-t=fib', "</a>"))
ck("S14 Stock now, GLOVES IN PAIRS, never a decimal: bought since 2 boxes, used since 2 pairs, stock 4 boxes + 12 pairs, order below 40 (pairs); "
   "Fibrecast 4\": 5 + 10 − 2 = 13 rolls, under 20 — red, and red on the tile; step 1 DONE",
   lambda: "(box of 100 gloves (50 pairs))" in g and " 2 boxes 2 pairs 4 boxes + 12 pairs " in g + " " and 'name="o%d" value="40"' % GL in row(h3, 'data-stock="%d"' % GL)
   and "11-05-2031 · 114 pairs" in g and "." not in re.sub(r"\d{2}-\d{2}-\d{4}", "", g.split("pairs)")[-1])
   and " 10 roll 2 roll 13 roll " in f4 + " " and 'class="r red"' in row(h3, 'data-stock="%d"' % F4)
   and re.search(r'4" 13 rolls', fib1) is not None and 'class="red" data-fib="4&#34;"' in h3.replace('4"', "4&#34;") and "STEP 1 · DONE" in h3,
   lambda: (g, f4, fib1))
own.post("/procroom/count", data={"back": "", "day": "12-05-2031", "c%d" % GL: "7.5"})
fl6 = flashes(own)
ck("S15 a count of 7.5 pairs is refused: gloves are counted in whole pairs; nothing saved",
   lambda: fl6 == "Gloves are counted in whole pairs — “7.5” is not a whole number. Nothing was saved." and
   db.execute("SELECT COUNT(*) FROM proc_count WHERE item_id=? AND day='2031-05-12'", (GL,)).fetchone()[0] == 0, lambda: fl6)
low = h3.lower()
ck("S16 Yuvika's papers are “dealer challans” on his page: the folded five are there and closed (Month-end match · Dealer challans and their rates · "
   "Your orders and deliveries · + Add a dealer challan from a photo by hand · Your product list and allowances); the old words and sections gone",
   lambda: all(re.search(r"<details id=%s>" % i, h3) for i in ("s637match", "s634slips", "s635orders", "s634add", "s634list"))
   and all(x in h3 for x in ("Month-end match — what was bought per 10 procedures", "Dealer challans and their rates", "Your orders and deliveries",
                             "+ Add a dealer challan from a photo by hand", "Your product list and allowances", "Save the dealer challan"))
   and not any(x in h3 for x in ("Slips and their rates", "+ A slip from a photo", "Slips against it", "By product", "Worth a look", "By month")),
   lambda: [x for x in ("Slips and their rates", "+ A slip from a photo", "Slips against it", "By product", "Worth a look", "By month") if x in h3])
ck("S17 the gloves line under Stock now: 2 pairs a cast or slab · 0 an ILI · box of 100 gloves (50 pairs) · change",
   lambda: "Gloves: 2 pairs a cast or slab · 0 an ILI · box of 100 gloves (50 pairs) change" in txt(block(h3, "id=s831gloves", "</div>")),
   lambda: txt(block(h3, "id=s831gloves", "</div>")))
ck("S18 before the floor: April says procedures are counted from 01-05-2031; a link of the older kind (?fy=2031) opens this year at May",
   lambda: "Procedures are counted from 01-05-2031, when the morning screen began" in txt(apr) and 'id="m2031-05" data-ym="2031-05" open' in page(fy="2031")[1],
   lambda: txt(apr)[:300])
db.execute("UPDATE proc_item SET reorder=1.25 WHERE id=?", (GL,))
db.commit()
h4 = page("2031-05")[1]
own.post("/procroom/count", data={"back": "", "day": "13-05-2031", "o%d" % GL: "62", "w%d" % GL: "62", "o%d" % F4: "20", "w%d" % F4: "20"})
fl7 = flashes(own)
own.post("/procroom/used", data={"ym": "2031-05"})
fl8 = flashes(own)
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('proc.gloves_cast','3')")
db.commit()
h5 = page("2031-05")[1]
ck("S20 untouched things are never rewritten: a gloves level set on the list as 1.25 boxes shows 62 pairs and a Save leaves it 1.25; a saved patient slip "
   "posts itself only when he changes it (its tick hidden, set by the page) -- a month Save with nothing changed writes nothing even after his allowance moved",
   lambda: 'name="o%d" value="62"' % GL in h4 and abs(db.execute("SELECT reorder FROM proc_item WHERE id=?", (GL,)).fetchone()[0] - 1.25) < 1e-9
   and fl7 == "No count typed and no reorder level changed." and "type=hidden name=refs" not in h5 and "type=hidden name=refs" not in h4
   and 'class=chg><input type=checkbox name=refs value="xp:901" class=fillref hidden' in h5 and fl8.startswith("Nothing to save") and len(recs("xp:901")) == 2,
   lambda: (fl7, fl8, re.findall(r'name="o%d" value="[^"]*"' % GL, h4)))
ck("S19 the add-an-item lists are filled in the browser from one list (the page stays light); every product in use is in it",
   lambda: h3.count("class=s831add") == 15 and all(s.count("<option") <= 1 for s in re.findall(r"<select class=s831add.*?</select>", h3))
   and '"Examination gloves"' in h3, lambda: (h3.count("class=s831add"), [s.count("<option") for s in re.findall(r"<select class=s831add.*?</select>", h3)]))
# ------------------------------------------------------------------------------------------------ green on both sides
srcp = open(pr.__file__, encoding="utf-8").read()
tree = ast.parse(srcp)
PIN = {'kit_lines': 'df091d9d555e67e5ddef8b58cd6fa163', 'fin_day': '1c06a3ced81698a62b7fc9e77f3b5b81', 'open_days': '0cbc2413b84f48d207376ac226be0a5f',
       'morning_view': 'cd2bcb7d8ecc6cd8e14e9e352379aeee', 'save_morning': '8f00a79a520347fb4339f7032066b3f2', 'MORNING_TPL': 'ffc33c10fd46aff1e730cadcd51050c9',
       '_staff_gate': '95dff2c9a1fa052a2b7d9c9287f4951e', 'morning_page': '74da52a21c3940bc644432b87ec1369b', 'morning_save': 'eb28b88d2ad80c171b6a87a81cd1bc20',
       'open_door': '8e9e47567623cf20dc8c0dc86758e767'}
got = {}
for n in tree.body:
    if isinstance(n, ast.FunctionDef) and n.name in PIN:
        got[n.name] = hashlib.md5(ast.get_source_segment(srcp, n).encode()).hexdigest()
    if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "MORNING_TPL":
        got["MORNING_TPL"] = hashlib.md5(n.value.value.encode()).hexdigest()
ck("G1 the staff's screen is untouched: Kal ke procedures' template and its code (the screen, its Save, the slip-book read, the door) are byte for byte S656's",
   lambda: got == PIN, lambda: [k for k in PIN if got.get(k) != PIN[k]])
ck("G2 the slip book is only read: the made-up finance database's bytes are unchanged by every page and every Save", lambda: fmd5() == F0)
codes = {u: own.get(u).status_code for u in ("/procroom/month?ym=2031-05", "/procroom/morning", "/desk/month", "/procroom/morning/api/open")}
codes["mgr /procroom/morning"] = mgr.get("/procroom/morning").status_code
ck("G3 the month end, the morning screen (his and Shavez's), the desk's month and the count door still answer", lambda: set(codes.values()) == {200}, lambda: codes)
db.close()
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad_ = [k for k in GREEN_BOTH if not RES.get(k)] + [k for k, v in RES.items() if v and k not in GREEN_BOTH]
    print("WALK S831 APP CONTROL: %d red; %s" % (len(red), "AS IT MUST BE (every new check red, the staff screen, the slip book and the other pages green)"
                                                   if not bad_ else "NOT AS IT MUST BE: " + ", ".join(bad_)))
    sys.exit(0 if not bad_ else 1)
print("WALK S831 APP: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
