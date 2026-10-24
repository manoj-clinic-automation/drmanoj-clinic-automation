#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s635_app.py -- S635_PROCROOM_ORDERS (D773 Kit 2) on the REAL scan app: asset_register.py and every part it mounts, copied into a
scratch folder with the given sorting_desk.py, asset_register.py and procroom.py (TO -- or FROM for the control, where procroom.py is
absent), on a COPY of a database (SQLite's backup API) -- or a fresh one the app makes itself. Made-up rows only, dated 2031 (papers
'Z-2031-O*'/'Z-2031-D*' of 'WALK635 ...' suppliers, made-up photo bytes of 2031); made-up owner and manager logins; no reader, no paid call, nothing sent;
Flask's test client, no port. The scratch folder is removed at the end; the database given is only read (copied).

    python3 -B walk_s635_app.py --live <the app folder> --files <folder holding the files to test> [--db <assets.db>] [--expect-red]
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
KIT_FILES = ("sorting_desk.py", "procroom.py")
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs", "procroom")
# the control on the live FROM files (Kit 1's procroom.py and sorting_desk.py): every new check red; Kit 1's flows and the old pages (K*, R*) green
MUST_RED = ("A0", "A1", "O1", "O2", "O3", "O4", "O5", "O6", "O8", "O10", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10", "M12", "M13", "M14", "M15", "M16", "M17")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s635app_")
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
            if "NOT mounted" in l or "S635" in l or "procroom" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S635_WALK_DEBUG"):
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
import io                                                            # noqa: E402

mods = {m: sys.modules.get(m) for m in PARTS}
pr = mods.get("procroom")
sd = mods.get("sorting_desk")
ck("A0 the real app loads with its seven parts mounted; procroom.py is Kit 2's (S635) and the desk carries its mark (%s)" % ", ".join(m for m, x in mods.items() if x is not None),
   lambda: all(mods.values()) and pr.MOUNTED and pr.VERSION == "S635" and getattr(sd, "PROCROOM_S635", "") == "S635" and getattr(sd, "PROCROOM", "") == "S634")
TODAY = datetime.date(2031, 5, 20)
for m in ("sorting_desk", "procroom", "stationery", "asset_machine", "batteries", "xray_costs"):
    if mods.get(m) is not None:
        mods[m].TODAY = TODAY
if pr is not None:
    pr.NO_THREAD = True                                              # the reading runs inline in the walk (the reader is off: nothing sent)
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
for u, role in (("walk_own_s635", "owner"), ("walk_mgr_s635", "manager")):
    if not db.execute("SELECT 1 FROM users WHERE username=?", (u,)).fetchone():
        db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (u, "Walk " + role, role))
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
out0 = []


def setup():
    pr.seed_step(dbp, out=out0.append)                               # Kit 1's list (already there on the live copy)
    had = db.execute("SELECT value FROM settings WHERE key=?", (getattr(pr, "ORDERS_FROM_KEY", "x"),)).fetchone()
    rc1 = pr.floor_step(dbp, out=out0.append)
    v1 = db.execute("SELECT value FROM settings WHERE key=?", (pr.ORDERS_FROM_KEY,)).fetchone()[0]
    rc2 = pr.floor_step(dbp, out=out0.append)
    v2 = db.execute("SELECT value FROM settings WHERE key=?", (pr.ORDERS_FROM_KEY,)).fetchone()[0]
    t = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    return rc1 == 0 and rc2 == 0 and v1 == v2 and "already set" in out0[-1] and (had is not None or "set to" in out0[-2]) and {"proc_paper", "proc_photo"} <= t


ck("A1 the data step sets the floor once (slips scanned from the install on are checked for an order); a second run writes nothing; the two new tables are there", setup, lambda: out0[-3:])


def client(user):
    c = ar.app.test_client()
    uid = db.execute("SELECT id FROM users WHERE username=?", (user,)).fetchone()[0]
    with c.session_transaction() as ss:
        ss["uid"] = uid
        ss["epoch"] = epoch
    return c


own, mgr = client("walk_own_s635"), client("walk_mgr_s635")


def mk(tag, vendor, items=(), created="2031-05-10 05:00:00", **cols):
    vals = dict(kind="Consumable", vendor=vendor, stamp_no="Z-2031-" + tag, status="draft", lane="clinic", created_at=created,
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


def lines_of(j, chg=None):
    chg = chg or {}
    out = []
    for l in (j.get("pr") or {}).get("lines") or []:
        x = {k: l[k] for k in ("no", "name", "qty", "unit", "brand", "place", "item")}
        x.update(chg.get(l["no"], {}))
        out.append(x)
    return out


def txt(h):
    return re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", h)).replace("&#34;", '"').replace("&quot;", '"').replace("&#39;", "'")


def counted_bills():
    try:
        return {d["bill_id"] for d in pr.counted_rows(db) if d.get("src") == "paper"}
    except Exception:                                                # noqa: BLE001
        return set()


F5, R6, ZZ = iid('Fibrecast bandage 5"'), iid('Roller bandage 6"'), iid("Zig-zag cotton 500 g")
# --- his order on the desk ------------------------------------------------------------------------------------------------------
O1 = mk("O1", "WALK635 YUVIKA SURGICALS", items=(('Gloster 5"', 6, 0.0), ("Bandage 13 cm x 4 m", 12, 0.0)), created="2031-05-03 05:00:00", doc_kind="bill")
_c, jo = paper(mgr, O1)
so, ro = post(mgr, "/desk/api/save", {"id": O1, "dest": "procedure", "kind": "bill", "pr_lines": lines_of(jo), "pr_role": "order", "pr_order": "", "pr_book": "24"})
ck("O1 Shavez marks a paper as Dr Manoj's order (book page 24): its two lines are kept and count nothing",
   lambda: so == 200 and "Marked as Dr Manoj's order (book page 24)" in ro.get("message", "") and "an order counts nothing" in ro.get("message", "")
   and len(live_lines(O1)) == 2 and O1 not in counted_bills() and (jo.get("pr") or {}).get("role") == "slip", lambda: (so, ro))
t = own.get("/procroom?ym=2031-05").get_data(as_text=True)
ck("O2 his page: the order is “awaiting — 17 days” (no slip after 3 days), and Worth a look says so; nothing of it is counted as bought",
   lambda: "awaiting — 17 days" in txt(t) and "1 order with no slip after 3 days" in txt(t) and 'data-order="%d"' % O1 in t and "book 24" in txt(t),
   lambda: txt(t)[txt(t).find("Orders and deliveries"):][:400])
D1 = mk("D1", "WALK635 YUVIKA SURGICALS", created="2031-05-06 05:00:00")                       # a slip nothing could be read from
_c1, j1 = paper(mgr, D1)
p1 = j1.get("pr") or {}
L1 = p1.get("lines") or []
ck("O3 the slip of 06-05 on the desk: pre-joined to order Z-2031-O1 and, nothing read, its lines filled from the order (6 Fibrecast 5\", 12 Roller 6\") -- no rate anywhere in the panel",
   lambda: p1.get("order") == str(O1) and p1.get("filled") is True and len(L1) == 2 and L1[0]["item"] == str(F5) and L1[0]["qty"] == "6" and L1[1]["item"] == str(R6)
   and L1[1]["qty"] == "12" and "rate" not in json.dumps(p1) and any(o["id"] == O1 for o in p1.get("orders", [])), lambda: json.dumps(p1)[:500])
s1, r1 = post(mgr, "/desk/api/save", {"id": D1, "dest": "procedure", "kind": "estimate", "pr_lines": lines_of(j1, {2: {"qty": "10"}}),
                                      "pr_role": "slip", "pr_order": str(O1), "pr_book": ""})
ck("O4 Shavez corrects the Roller to 10 and saves: joined to order Z-2031-O1, its lines count",
   lambda: s1 == 200 and "Joined to order Z-2031-O1" in r1.get("message", "") and len(live_lines(D1)) == 2 and D1 in counted_bills(), lambda: (s1, r1))
t = own.get("/procroom?ym=2031-05").get_data(as_text=True)
seg = t[t.find('data-order="%d"' % O1):]
seg = seg[:seg.find("</tr>")]
ck("O5 his page: the order “part came” -- Roller bandage 6\": ordered 12, came 10; the slip Z-2031-D1 against it; no longer awaiting",
   lambda: "part came" in txt(seg) and 'Roller bandage 6": ordered 12, came 10' in txt(seg) and "Z-2031-D1" in seg and "awaiting" not in txt(seg), lambda: txt(seg))
D2 = mk("D2", "WALK635 YUVIKA SURGICALS", items=(('Gloster 4"', 2, 0.0),), created="2031-05-08 05:00:00")
_c2, j2 = paper(mgr, D2)
s2, r2 = post(mgr, "/desk/api/save", {"id": D2, "dest": "procedure", "kind": "estimate", "pr_lines": lines_of(j2), "pr_role": "slip", "pr_order": "", "pr_book": ""})
D3 = mk("D3", "WALK635 YUVIKA SURGICALS", items=(('Gloster 3"', 1, 0.0),), created="2020-05-01 05:00:00", bill_date="2031-05-09")   # scanned before the floor
_c3, j3 = paper(mgr, D3)
post(mgr, "/desk/api/save", {"id": D3, "dest": "procedure", "kind": "estimate", "pr_lines": lines_of(j3), "pr_role": "slip", "pr_order": "", "pr_book": ""})
t = own.get("/procroom?ym=2031-05").get_data(as_text=True)
ck("O6 a slip with no order (08-05) shows “no order” on his page and in Worth a look; a slip scanned before the install (09-05) is never flagged",
   lambda: s2 == 200 and 'data-noorder="%d"' % D2 in t and 'data-noorder="%d"' % D3 not in t and "1 slip with no order of yours" in txt(t), lambda: (s2, r2, txt(t)[txt(t).find("Worth a look"):][:300]))
s8, r8 = post(mgr, "/desk/api/save", {"id": D2, "dest": "procedure", "kind": "estimate", "pr_lines": lines_of(j2), "pr_role": "slip", "pr_order": str(D1), "pr_book": ""})
ck("O8 joining a slip to a paper that is not his order is refused, with the words; nothing changes", lambda: s8 == 400 and "not one of Dr Manoj's orders" in r8.get("error", "")
   and pr.role_of(db, db.execute("SELECT * FROM bills WHERE id=?", (D2,)).fetchone()) is None, lambda: (s8, r8))
_cm, jm1 = paper(mgr, D1)
ck("O9 the manager's whole desk JSON for the slip and the order carries no rate", lambda: '"rate' not in json.dumps(jm1) and '"rate' not in json.dumps(paper(mgr, O1)[1]),
   lambda: [k for k in jm1 if "rate" in json.dumps(jm1.get(k))][:5])
sx, rx = post(own, "/desk/api/save", {"id": O1, "dest": "others", "kind": "bill"})
t = own.get("/procroom?ym=2031-05").get_data(as_text=True)
gone = 'data-order="%d"' % O1 not in t and 'data-noorder="%d"' % D1 in t
sb, rb = post(own, "/desk/api/save", {"id": O1, "dest": "procedure", "kind": "bill", "pr_lines": lines_of(jo), "pr_role": "order", "pr_order": "", "pr_book": "24"})
t = own.get("/procroom?ym=2031-05").get_data(as_text=True)
ck("O10 the order re-sorted out of Procedure room: its role goes with its lines, and the slip against it reads “no order”; sorted back as his order, the join holds again",
   lambda: sx == 200 and gone and sb == 200 and 'data-order="%d"' % O1 in t and 'data-noorder="%d"' % D1 not in t, lambda: (sx, rx, sb, rb))
# --- the month end ------------------------------------------------------------------------------------------------------------------
own.post("/procroom/slip", data={"day": "20-04-2031", "supplier": "WALK635 SURGICALS", "note": "made-up history", "i1": str(F5), "b1": "Gloster", "q1": "4", "p1": "proc", "r1": "123"})
flashes(own)
mp = own.get("/procroom/month?ym=2031-05")
mm = mgr.get("/procroom/month?ym=2031-05")
an = ar.app.test_client().get("/procroom/month?ym=2031-05")
ck("M1 the month end is his alone: 200 for him; the manager refused; logged out to the login; his page links to it",
   lambda: mp.status_code == 200 and "Month end — Yuvika, May 2031" in txt(mp.get_data(as_text=True)) and mm.status_code in (302, 403) and an.status_code == 302
   and "/procroom/month?ym=2031-05" in own.get("/procroom?ym=2031-05").get_data(as_text=True), lambda: (mp.status_code, mm.status_code, an.status_code))
JPG1 = b"\xff\xd8\xff\xe0WALK635-made-up-photo-one" + os.urandom(64)
JPG2 = b"\xff\xd8\xff\xe0WALK635-made-up-photo-two" + os.urandom(64)
up = own.post("/procroom/month/photos", data={"ym": "2031-05", "photos": [(io.BytesIO(JPG1), "wa1.jpg"), (io.BytesIO(JPG2), "wa2.jpg"),
                                                                         (io.BytesIO(b"x"), "notes.txt"), (io.BytesIO(JPG1), "wa1-again.jpg")]},
              content_type="multipart/form-data")
fu = flashes(own)
try:
    ph = [dict(r) for r in db.execute("SELECT * FROM proc_photo WHERE ym='2031-05' ORDER BY id")]
except sqlite3.Error:
    ph = []
updir = os.path.join(os.environ["ASSETS_UPLOADS"], "procroom_month")
ck("M2 two photos added and kept (a text file and the same photo twice are not added, with the words); the reader being off, each says so -- type its lines",
   lambda: up.status_code == 302 and "2 photos added" in fu and "notes.txt is not a photo" in fu and "was added before" in fu and len(ph) == 2
   and all(os.path.isfile(os.path.join(updir, p["stored"])) for p in ph) and all(p["read_state"] == "failed" and "the reader is off" in p["read_error"] for p in ph),
   lambda: (up.status_code, fu, [(p["stored"], p["read_state"], p["read_error"]) for p in ph]))
P1, P2 = (ph[0]["id"], ph[1]["id"]) if len(ph) == 2 else (0, 0)
try:                                                                 # made-up readings (no reader is called); the control has no such table
    db.execute("UPDATE proc_photo SET read_state='read', read_error='', read_json=? WHERE id=?",
               (json.dumps({"bill_date": "2031-05-06", "items": [{"name": 'Gloster 5"', "qty": 6, "rate": 118}, {"name": "Bandage 13 cm x 4 m", "qty": 12, "rate": 21}]}), P1))
    db.execute("UPDATE proc_photo SET read_state='read', read_error='', read_json=? WHERE id=?",
               (json.dumps({"bill_date": "2031-05-11", "items": [{"name": "Zig zag cotton", "qty": 2, "rate": 13}]}), P2))
    db.commit()
except sqlite3.Error:
    pass
t = own.get("/procroom/month?ym=2031-05").get_data(as_text=True)


def prow(h, pid):
    i = h.find('data-photo="%d"' % pid)
    return txt(h[i:h.find("</tr>", i)]) if i >= 0 else ""


ck("M3 the check: the 06-05 photo matched to scan Z-2031-D1 and its order Z-2031-O1 -- Roller bandage 6\": photo 12, scan 10; Fibrecast bandage 5\" down: ₹118 (was ₹123); the 11-05 photo not scanned, from the photo only; to pay ₹986; Z-2031-D2 on the desk, not in the photos",
   lambda: "Z-2031-D1" in prow(t, P1) and "Z-2031-O1" in prow(t, P1) and 'Roller bandage 6": photo 12, scan 10' in prow(t, P1)
   and 'Fibrecast bandage 5" down: ₹118 (was ₹123)' in prow(t, P1) and "not scanned" in prow(t, P2) and "from the photo only" in prow(t, P2)
   and "₹986" in txt(t[t.find('id=s635total'):][:300]) and "Z-2031-D2" in txt(t[t.find("id=s635deskonly"):][:400]), lambda: (prow(t, P1), prow(t, P2), txt(t[t.find('id=s635total'):][:200])))
te = own.get("/procroom/month?ym=2031-05&photo=%d" % P1).get_data(as_text=True)
ed = te[te.find("id=s635edit"):]
ck("M4 the 06-05 photo opened: the scan's own two lines with the photo's rates (118, 21) and “photo 12” beside the Roller",
   lambda: 'name="r1" value="118"' in ed and 'name="r2" value="21"' in ed and "photo 12" in txt(ed) and 'name="q2" value="10"' in ed, lambda: txt(ed)[:600])
d1l = live_lines(D1)
form = {"ym": "2031-05", "photo": str(P1), "scan": str(D1), "day": "06-05-2031"}
for k, l in enumerate(d1l, 1):
    form.update({"l%d" % k: str(l["id"]), "i%d" % k: str(l["item_id"]), "n%d" % k: l["name"], "b%d" % k: l["brand"], "q%d" % k: pr._plain(l["qty"]),
                 "r%d" % k: "118" if l["item_id"] == F5 else "21", "p%d" % k: l["place"]})
c5 = own.post("/procroom/month/check", data=form)
f5 = flashes(own)
t = own.get("/procroom/month?ym=2031-05").get_data(as_text=True)
ck("M5 his Save: the rates go onto the scan's lines (₹118, ₹21), the line ids kept; the row is checked, the quantity that differed kept beside it; to pay now ₹944",
   lambda: c5.status_code == 302 and "Z-2031-D1: rates saved on 2 lines" in f5 and [l["rate"] for l in live_lines(D1)] == [118, 21]
   and [l["id"] for l in live_lines(D1)] == [l["id"] for l in d1l] and "checked" in prow(t, P1) and "photo 12, scan 10" in prow(t, P1) and "₹944" in txt(t[t.find('id=s635total'):][:300]),
   lambda: (c5.status_code, f5, prow(t, P1), txt(t[t.find('id=s635total'):][:200])))
c6 = own.post("/procroom/month/check", data={"ym": "2031-05", "photo": str(P2), "scan": "none", "day": "11-05-2031", "i1": str(ZZ), "q1": "2", "r1": "13", "p1": "proc"})
f6 = flashes(own)
try:
    sl = db.execute("SELECT slip_id FROM proc_photo WHERE id=?", (P2,)).fetchone()
except sqlite3.Error:
    sl = None
ck("M6 the photo that was never scanned: his Save keeps it as a photo slip (11-05, Zig-zag 2 at ₹13) -- it counts on his page",
   lambda: c6.status_code == 302 and "Slip of 11-05-2031 saved — 1 line" in f6 and sl and sl[0] and any(d["item_id"] == ZZ and d.get("src") == "photo" for d in pr.counted_rows(db)),
   lambda: (c6.status_code, f6))
D4 = mk("D4", "WALK635 YUVIKA SURGICALS", items=(("Zig zag cotton", 2, 0.0),), created="2031-05-12 05:00:00", bill_date="2031-05-11")
_c4, j4 = paper(mgr, D4)
post(mgr, "/desk/api/save", {"id": D4, "dest": "procedure", "kind": "estimate", "pr_lines": lines_of(j4), "pr_role": "slip", "pr_order": "", "pr_book": ""})
t = own.get("/procroom/month?ym=2031-05").get_data(as_text=True)
later = "scanned later as Z-2031-D4" in prow(t, P2)
d4l = live_lines(D4)
c7 = own.post("/procroom/month/check", data={"ym": "2031-05", "photo": str(P2), "scan": str(D4), "day": "11-05-2031", "l1": str(d4l[0]["id"]) if d4l else "",
                                            "i1": str(ZZ), "n1": d4l[0]["name"] if d4l else "", "b1": "", "q1": "2", "r1": "13", "p1": "proc"})
f7 = flashes(own)
zz = [d for d in pr.counted_rows(db) if d["item_id"] == ZZ and d["when"] == "2031-05-11"]
ck("M7 the 11-05 slip scanned later: the row says so; his Save on that scan voids the photo slip -- counted once, on the scan",
   lambda: later and c7.status_code == 302 and "counted once, on the scan" in f7 and len(zz) == 1 and zz[0]["src"] == "paper" and zz[0]["eff"] == 13,
   lambda: (later, prow(t, P2), f7, [(d["src"], d["eff"]) for d in zz]))
JPG3 = b"\xff\xd8\xff\xe0WALK635-made-up-photo-three" + os.urandom(64)
JPG4 = b"\xff\xd8\xff\xe0WALK635-made-up-photo-four" + os.urandom(64)
own.post("/procroom/month/photos", data={"ym": "2031-05", "photos": [(io.BytesIO(JPG3), "wa3.jpg"), (io.BytesIO(JPG4), "wa4.jpg")]}, content_type="multipart/form-data")
flashes(own)
try:
    P3, P4 = [r[0] for r in db.execute("SELECT id FROM proc_photo WHERE ym='2031-05' AND orig_name IN ('wa3.jpg','wa4.jpg') ORDER BY id")]
    db.execute("UPDATE proc_photo SET read_state='read', read_error='', read_json=? WHERE id=?",          # the 06-05 slip sent a second time
               (json.dumps({"bill_date": "2031-05-06", "items": [{"name": 'Gloster 5"', "qty": 6, "rate": 118}]}), P3))
    db.commit()
except (sqlite3.Error, ValueError):
    P3, P4 = 0, 0
t = own.get("/procroom/month?ym=2031-05").get_data(as_text=True)
ck("M12 the 06-05 slip sent twice: the second photo says it shows the same scan, counted once -- to pay still ₹944 (the scan is never added twice)",
   lambda: "same scan as the photo of 06-05 — counted once" in prow(t, P3) and "counted above" in prow(t, P3) and "₹944" in txt(t[t.find('id=s635total'):][:300]),
   lambda: (prow(t, P3), txt(t[t.find('id=s635total'):][:200])))
JPG5 = b"\xff\xd8\xff\xe0WALK635-made-up-photo-five" + os.urandom(64)
own.post("/procroom/month/photos", data={"ym": "2031-05", "photos": [(io.BytesIO(JPG5), "wa5.jpg")]}, content_type="multipart/form-data")
flashes(own)
try:
    P5 = db.execute("SELECT id FROM proc_photo WHERE ym='2031-05' AND orig_name='wa5.jpg'").fetchone()[0]
    db.execute("UPDATE proc_photo SET read_state='read', read_error='', read_json=? WHERE id=?",           # a DIFFERENT slip of the same day
               (json.dumps({"bill_date": "2031-05-06", "items": [{"name": "Zig zag cotton", "qty": 3, "rate": 13}]}), P5))
    db.commit()
except (sqlite3.Error, TypeError):
    P5 = 0
t = own.get("/procroom/month?ym=2031-05").get_data(as_text=True)
ck("M16 a different slip of the same day (Zig-zag 3 at ₹13, 06-05) is not folded into the scan another photo was checked onto: not scanned, its ₹39 counted -- to pay ₹983",
   lambda: "not scanned" in prow(t, P5) and "same scan" not in prow(t, P5) and "₹39" in prow(t, P5) and "₹983" in txt(t[t.find('id=s635total'):][:300]),
   lambda: (prow(t, P5), txt(t[t.find('id=s635total'):][:200])))
if P5:
    own.post("/procroom/month/remove", data={"ym": "2031-05", "photo": str(P5)})
    flashes(own)
JPG6 = b"\xff\xd8\xff\xe0WALK635-made-up-photo-six" + os.urandom(64)
own.post("/procroom/month/photos", data={"ym": "2031-05", "photos": [(io.BytesIO(JPG6), "wa6.jpg")]}, content_type="multipart/form-data")
flashes(own)
try:
    P6 = db.execute("SELECT id FROM proc_photo WHERE ym='2031-05' AND orig_name='wa6.jpg'").fetchone()[0]
    db.execute("UPDATE proc_photo SET read_state='read', read_error='', read_json=? WHERE id=?",           # a different slip sharing ONE product
               (json.dumps({"bill_date": "2031-05-06", "items": [{"name": "Bandage 13 cm x 4 m", "qty": 4, "rate": 21}, {"name": "Zig zag cotton", "qty": 3, "rate": 13}]}), P6))
    db.commit()
except (sqlite3.Error, TypeError):
    P6 = 0
t = own.get("/procroom/month?ym=2031-05").get_data(as_text=True)
ck("M17 a different slip of the same day that shares one product (Roller 4, plus Zig-zag 3 not on the scan) is not folded in: not scanned, its ₹123 counted -- to pay ₹1,067",
   lambda: "not scanned" in prow(t, P6) and "same scan" not in prow(t, P6) and "₹123" in prow(t, P6) and "₹1,067" in txt(t[t.find('id=s635total'):][:300]),
   lambda: (prow(t, P6), txt(t[t.find('id=s635total'):][:200])))
if P6:
    own.post("/procroom/month/remove", data={"ym": "2031-05", "photo": str(P6)})
    flashes(own)
e4 = own.get("/procroom/month?ym=2031-05&photo=%d" % P4).get_data(as_text=True)
e4 = e4[e4.find("id=s635edit"):]
e3 = own.get("/procroom/month?ym=2031-05&photo=%d" % P3).get_data(as_text=True)
e3 = e3[e3.find("id=s635edit"):]
ck("M13 a photo nothing could be read from: its scan can still be chosen -- every scan of the month is offered (Z-2031-D1, Z-2031-D2, Z-2031-D4)",
   lambda: all(s in e4 for s in ("Z-2031-D1", "Z-2031-D2", "Z-2031-D4")), lambda: txt(e4)[:400])
ck("M14 “Read again” is offered for the photo that could not be read, and not for one that was read", lambda: "Read again" in e4 and "Read again" not in e3,
   lambda: ("Read again" in e4, "Read again" in e3))
d2l = live_lines(D2)
c15 = own.post("/procroom/month/check", data={"ym": "2031-05", "photo": str(P4), "scan": str(D2), "day": "08-05-2031", "l1": str(d2l[0]["id"]) if d2l else "",
                                             "i1": "ask", "n1": "WALK635 new cream", "q1": "3", "r1": "40", "p1": "proc"})
f15 = flashes(own)
l15 = live_lines(D2)
ck("M15 his line “not on your list yet” onto a scan: saved as such (it waits for his list), with his rate -- not refused",
   lambda: c15.status_code == 302 and "Z-2031-D2: 1 line saved from the photo" in f15 and len(l15) == 1 and l15[0]["ask"] == 1 and l15[0]["item_id"] is None
   and l15[0]["rate"] == 40, lambda: (f15, l15))
cb = own.post("/procroom/month/check", data={"ym": "2031-05", "photo": str(P1), "scan": "none", "day": "31-02-2031", "i1": str(ZZ), "q1": "1", "p1": "proc"})
fb = flashes(own)
ck("M10 a date that is not a date saves nothing, with the words", lambda: "Type the slip's date" in fb and "Nothing was saved" in fb
   and db.execute("SELECT bill_id FROM proc_photo WHERE id=?", (P1,)).fetchone()[0] == D1, lambda: fb)
pf_o = own.get("/procroom/month/photo/%d" % P1)
pf_m = mgr.get("/procroom/month/photo/%d" % P1)
ck("M9 the photo opens for him (image/jpeg, its own bytes); the manager is refused", lambda: pf_o.status_code == 200 and pf_o.mimetype == "image/jpeg" and pf_o.get_data() == JPG1
   and pf_m.status_code in (302, 403), lambda: (pf_o.status_code, pf_o.mimetype, pf_m.status_code))
rm = own.post("/procroom/month/remove", data={"ym": "2031-05", "photo": str(P1)})
fr = flashes(own)
t = own.get("/procroom/month?ym=2031-05").get_data(as_text=True)
ck("M8 a photo taken off the month: kept on the server and listed struck through; its row and amount leave the total; the scan's lines and rates stay",
   lambda: rm.status_code == 302 and "Photo taken off the month" in fr and 'data-photo="%d"' % P1 not in t and "Taken off the month (3)" in txt(t)
   and os.path.isfile(os.path.join(updir, ph[0]["stored"])) and [l["rate"] for l in live_lines(D1)] == [118, 21], lambda: (fr, txt(t)[:300]))
_cm, jm = paper(mgr, D1)
ck("M11 after his rates, the manager's desk JSON for that slip still carries no rate (no ₹118, no ₹21)", lambda: "118" not in json.dumps(jm.get("pr")) and '"rate' not in json.dumps(jm),
   lambda: json.dumps(jm.get("pr"))[:300])
# --- Kit 1 and the old pages keep answering (green on both sides) ---------------------------------------------------------------------
P9 = mk("P9", "WALK635 SURGICALS", items=(('Gloster 5"', 5, 123.0),), created="2031-05-14 05:00:00")
_c9, j9 = paper(mgr, P9)
s9, r9 = post(mgr, "/desk/api/save", {"id": P9, "dest": "procedure", "kind": "estimate", "pr_lines": lines_of(j9)})
ck("K1 Kit 1's Save without the new fields (an older page) still saves its lines; the paper counts", lambda: s9 == 200 and "Procedure room: 1 line saved" in r9.get("message", "")
   and live_lines(P9) and live_lines(P9)[0]["rate_read"] == 123, lambda: (s9, r9))
ck("K2 his Procedure room page, its slips and the FY by month still answer", lambda: own.get("/procroom?fy=2031").status_code == 200 and own.get("/procroom").status_code == 200)
P3 = mk("P3", "WALK635 OTHER SHOP", items=(("A4 sheets", 2, 250.0),), created="2031-05-14 05:00:00", doc_kind="bill")
s7, r7 = post(own, "/desk/api/save", {"id": P3, "dest": "others", "kind": "bill"})
ck("R1 a paper of another group still saves as before", lambda: s7 == 200 and r7.get("ok") and "Procedure room" not in r7.get("message", ""), lambda: (s7, r7))
ck("R2 the desk, The month, Stationery, X-ray and the Machines list still answer for the owner", lambda: all(own.get(u).status_code == 200 for u in ("/desk", "/desk/month", "/stationery", "/xray", "/assets")),
   lambda: [(u, own.get(u).status_code) for u in ("/desk", "/desk/month", "/stationery", "/xray", "/assets")])
_c, j3b = paper(own, P3)
ck("R3 the desk's paper still carries the stationery panel (stk) and its other parts", lambda: _c == 200 and "stk" in j3b and "covers" in j3b, lambda: list(j3b)[:20])
db.close()
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad = [k for k in MUST_RED if RES.get(k, True)] + [k for k in red if k not in MUST_RED and k not in ("O7", "O9", "M11")]
    print("WALK S635 APP CONTROL: %d red; %s" % (len(red), "AS IT MUST BE" if not bad else "NOT AS IT MUST BE: " + ", ".join(bad)))
    sys.exit(0 if not bad else 1)
print("WALK S635 APP: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
