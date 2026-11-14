#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s838_app.py -- S838_SCANAPP_GOTO on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch folder
with the given sorting_desk.py, clinic_papers.py, claude_reader.py and xray_costs.py (TO -- or the live files for the control), on a
fresh database the app makes itself. Made-up users only (an owner and a manager); nothing leaves the process (the made-up finance
and spine databases of S835's harness are made and never read). The scratch folder is removed at the end.

    python3 -B walk_s838_app.py --live <the app folder> --shared <the shared folder> --files <folder holding the files to test> [--expect-red] [--box]
    --box: run by the installer on the server -- where node is absent, D6 (the page script) stands as checked when the kit was built.
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


LIVE, FILES = opt("--live", "/root/assetapp"), opt("--files")
EXPECT_RED = "--expect-red" in ARGS
KIT_FILES = ("sorting_desk.py",)
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs", "procroom")
GREEN_BOTH = ("A0", "Z1")                                            # the app loads; an ordinary page is unchanged

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s838app_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        for f in KIT_FILES:
            p = os.path.join(FILES, f)
            if os.path.isfile(p):
                shutil.copy(p, os.path.join(app, f))
        SHARED = opt("--shared")                                     # the live /root/shared (scan_checks_s441 adds page_of, dup_flag ...)
        if SHARED:
            shutil.copytree(SHARED, os.path.join(work, "shared"), ignore=shutil.ignore_patterns("*.pyc", "__pycache__"))
        os.makedirs(os.path.join(work, "uploads"))
        os.makedirs(os.path.join(work, "key"))
        open(os.path.join(work, "key", "anthropic.key"), "w").write("made-up-walk-key\n")
        fin, spn = os.path.join(work, "finance.db"), os.path.join(work, "spine.db")
        f = sqlite3.connect(fin)
        f.executescript("""
CREATE TABLE purchase_scan_link(bill_id INTEGER, asset_bill_id INTEGER, grade TEXT, matched_on TEXT, linked_at TEXT);
CREATE TABLE purchase_bill(id INTEGER PRIMARY KEY, supplier_norm TEXT, supplier TEXT, bill_no TEXT, bill_date TEXT, month TEXT, amount_p INTEGER, first_seen_day TEXT);
CREATE TABLE purchase_line(id INTEGER PRIMARY KEY, supplier_norm TEXT, bill_no TEXT, bill_date TEXT, month TEXT, item TEXT, packing TEXT, batch TEXT,
  expiry TEXT, tax REAL, qty REAL, free REAL, rate_p INTEGER, discount_pct REAL, amount_p INTEGER, net_rate_p INTEGER, net_amount_p INTEGER,
  loose_qty REAL, purchase_rate_p INTEGER, direction TEXT, source_md5 TEXT, line_type TEXT);
CREATE TABLE purchase_export(md5 TEXT PRIMARY KEY, type TEXT, received_at TEXT, superseded_by TEXT);
INSERT INTO purchase_export VALUES('OLDWALK','ITEMWISE','2031-03-06 10:00','NEWWALK'),('NEWWALK','ITEMWISE','2031-03-07 10:00',NULL);
INSERT INTO purchase_bill VALUES(9001,'WALK DEALER835','WALK DEALER835 BAREILLY','WD803','2031-03-05','2031-03',141000,'2031-03-06');
INSERT INTO purchase_line(supplier_norm,bill_no,bill_date,item,batch,qty,free,rate_p,amount_p,net_amount_p,direction,source_md5,line_type) VALUES
 ('WALK DEALER835','WD803','2031-03-05','WALKITEM OLD','B0',1,0,1000,1000,1000,'PURCHASE','OLDWALK','ITEMWISE'),
 ('WALK DEALER835','WD803','2031-03-05','WALKITEM ONE','B1',2,0,50000,100000,100000,'PURCHASE','NEWWALK','ITEMWISE'),
 ('WALK DEALER835','WD803','2031-03-05','WALKITEM TWO','B2',1,1,41000,41000,41000,'PURCHASE','NEWWALK','ITEMWISE');
""")
        f.commit()
        f.close()
        s = sqlite3.connect(spn)
        s.execute("CREATE TABLE sp_purchase_bill (supplier TEXT, supkey TEXT, bill TEXT, date TEXT, amount_p INTEGER, direction TEXT, source_md5 TEXT)")
        s.commit()
        s.close()
        env = dict(os.environ, ASSETS_DB=os.path.join(work, "assets.db"), ASSETS_UPLOADS=os.path.join(work, "uploads"),
                   SHARED_LIB_DIR=os.path.join(work, "shared" if opt("--shared") else "noshared"), SCANAPP_ANTHROPIC_KEY_FILE=os.path.join(work, "key", "anthropic.key"),
                   SCANAPP_ANTHROPIC_URL="https://made-up.invalid/v1", CLINIC_PORTAL_DIR=os.path.join(work, "noportal"),
                   FINANCE_LOCAL_URL="http://127.0.0.1:9", FINANCE_DB_FOR_SCANS=fin, SPINE_DB_FOR_SCANS=spn,
                   READER_WATCH_STATE=os.path.join(work, "rw_state.json"), READER_WATCH_STUB=os.path.join(work, "rw_sent.jsonl"),
                   READER_WATCH_ALL_OFF=os.path.join(work, "_off", "ALL_OFF"))
        for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
            env.pop(k, None)
        r = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--inner", app, work] + ARGS, env=env, cwd=work,
                           capture_output=True, text=True, timeout=600)
        sys.stdout.write(r.stdout)
        for l in r.stderr.splitlines():
            if "NOT mounted" in l or "S838" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S838_WALK_DEBUG"):
            print(r.stderr[-3000:])
        sys.exit(r.returncode)
    finally:
        shutil.rmtree(work, ignore_errors=True)

# ------------------------------------------------------------------------------------------------ inside the scratch process
APPD = ARGS[ARGS.index("--inner") + 1]
WORK = ARGS[ARGS.index("--inner") + 2]
_me = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") not in (_me, os.path.abspath("."))]   # never the kit's own copies (F-1415)
sys.path.insert(0, APPD)
RES = {}


def ck(name, fn, detail=None):
    try:
        ok = bool(fn())
        d = "" if ok or detail is None else detail()
    except Exception as e:                                           # noqa: BLE001
        ok, d = False, repr(e)
    RES[name.split(" ")[0]] = ok
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:500]) if (d and not ok) else ""))


def txt(h):
    return re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", h)).replace("&#34;", '"').replace("&#39;", "'").replace("&amp;", "&")


import asset_register as ar                                          # noqa: E402

mods = {m: sys.modules.get(m) for m in PARTS}
ck("A0 the real app loads with its seven parts mounted (%s)" % ", ".join(m for m, x in mods.items() if x is not None), lambda: all(mods.values()))
sd = mods["sorting_desk"]
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
for u_, r_ in (("walk_own_s838", "owner"), ("walk_mgr_s838", "manager")):
    db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (u_, u_, r_))
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
db.execute("DELETE FROM settings WHERE key='bar.goto'")
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]


def client(name):
    c = ar.app.test_client()
    with c.session_transaction() as ss:
        ss["uid"] = db.execute("SELECT id FROM users WHERE username=?", (name,)).fetchone()[0]
        ss["epoch"] = epoch
    return c


own, mgr = client("walk_own_s838"), client("walk_mgr_s838")


def page(c, path):
    r = c.get(path)
    return r.status_code, r.get_data(as_text=True)


def hrefs(h):
    return set(re.findall(r'href="([^"]+)"', h))


def bar_of(h):
    i = h.find("id=s559bar")
    j = h.find("</script>", i) if "s838panel" in h[i:i + 20000] else h.find("</div>", i)
    return h[max(0, i - 3000):j + 9] if i >= 0 else ""


c1, d1 = page(own, "/desk")
c2, d2 = page(own, "/")
c3, d3 = page(own, "/desk/month")
G = ("1 · Papers coming in", "2 · Clinic purchases &amp; stock", "3 · Dealers", "4 · Machines &amp; renewals", "5 · Yours only")
ck("B1 the owner's desk: the bar keeps Sorting desk, The month, Bills awaited and the Go to ▾ button; the panel holds the five groups, "
   "Add a paper from a file and the Sanjeevni Hub", lambda: c1 == 200 and "id=s838go" in d1 and "id=s838panel" in d1 and all(g in d1 for g in G)
   and "Add a paper from a file" in d1 and 'href="/finance/approvals"' in d1 and "Implant stock ledger" in d1 and "X-ray films" in d1,
   lambda: (c1, [g for g in G if g not in d1]))
ck("B2 the same bar on the scan app's home page (the portal tile lands here) and on The month; the switch card lists “Go to menu for Shavez”",
   lambda: c2 == 200 and "id=s838go" in d2 and c3 == 200 and "id=s838go" in d3 and "Go to menu for Shavez" in d3, lambda: (c2, c3))
old = (sd.S838_OLD[0] if getattr(sd, "S838_OLD", None) else None)
with ar.app.test_request_context("/desk"):
    from flask import g as _g
    _g.user = db.execute("SELECT * FROM users WHERE username='walk_own_s838'").fetchone()
    old_bar = str(old(_g.user)) if old else ""
lost = [h for h in hrefs(old_bar) if h not in hrefs(d1)]
ck("B3 nothing is lost: every link of the old bar is on the new one (bar or panel)", lambda: old_bar and not lost, lambda: lost)
c4, m4 = page(mgr, "/desk")
c5, m5 = page(mgr, "/")
ck("B4 installed switched OFF for Shavez: his desk and home keep the old bar exactly (no Go to) while the owner's has it",
   lambda: c4 == 200 and c5 == 200 and "id=s559bar" in m4 and "id=s838go" not in m4 and "id=s838go" not in m5 and "id=s838go" in d1, lambda: (c4, c5))
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('bar.goto','on')")
db.commit()
c6, m6 = page(mgr, "/desk")
ck("B5 switched on: Shavez gets Go to -- without “Yours only”, Admin, the switches or the Sanjeevni Hub",
   lambda: c6 == 200 and "id=s838go" in m6 and "5 · Yours only" not in m6 and "/finance/approvals" not in m6 and ">Admin<" not in m6
   and "1 · Papers coming in" in m6, lambda: c6)
js = re.findall(r"<script>(\(function\(\)\{var b=document.getElementById\('s838go'\).*?)</script>", d1, re.S)
jsok, jsmsg = False, "no script"
if js:
    jp = os.path.join(WORK, "bar838.js")
    open(jp, "w", encoding="utf-8").write(js[0])
    try:
        rr = subprocess.run(["node", "--check", jp], capture_output=True, text=True, timeout=60)
        jsok, jsmsg = rr.returncode == 0, rr.stderr[-300:]
    except FileNotFoundError:
        jsok, jsmsg = ("--box" in ARGS), "node is not here"
ck("B6 the bar's script is valid JavaScript (node --check)", lambda: jsok, lambda: jsmsg)
orig = getattr(sd, "_s838_parts", None)
if orig:
    sd._s838_parts = lambda u: 1 / 0
c7, d7 = page(own, "/desk")
if orig:
    sd._s838_parts = orig
ck("B7 any error in Go to draws the OLD bar (never a broken page)", lambda: orig and c7 == 200 and "id=s559bar" in d7 and "id=s838go" not in d7, lambda: c7)
DUMP = os.environ.get("S838_DUMP")
if DUMP:
    open(os.path.join(DUMP, "month.html"), "w", encoding="utf-8").write(d3)
cz, dz = page(own, "/assets")
ck("Z1 an ordinary page of the app still answers (Machines)", lambda: cz == 200, lambda: cz)
db.close()
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad_ = [k for k in GREEN_BOTH if not RES.get(k)] + [k for k, v in RES.items() if v and k not in GREEN_BOTH]
    print("WALK S838 APP CONTROL: %d red; %s" % (len(red), "AS IT MUST BE (every new check red; the app and an ordinary page green)" if not bad_
                                                   else "NOT AS IT MUST BE: " + ", ".join(bad_)))
    sys.exit(0 if not bad_ else 1)
print("WALK S838 APP: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
