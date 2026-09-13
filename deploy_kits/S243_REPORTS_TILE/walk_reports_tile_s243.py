#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_reports_tile_s243.py -- the LIVE-SHAPE walk for S243_REPORTS_TILE.

A real Flask app -- the finance_app.py named by FIN_APP, patched IN MEMORY by this kit's own
patcher (and, when the sibling kits are found, by S243_SCREEN_FIXES and S243_DARPAN_KAL first,
exactly the order the box will see) -- over a real sqlite database built from finance_schema.sql
+ finance_returns.sql + the marg_ingest schema (mi_file, read from marg_ingest.py itself) +
purchase_schema.sql + the amir tables (amir_day._ensure), with the real sibling modules copied
beside it.  The rendered PAGE is walked as the report generator (`shavez`-shaped viewer), the
owner's hub line is walked as the checker, the portal's own _visible_sections is asked who is
shown the tile.  Nothing live is touched.

    FIN_APP=<finance_app.py> FIN_MODS=<folder with the modules> MI_DIR=<marg_ingest folder> \
    PORTAL_PY=<portal.py> python3 -B walk_reports_tile_s243.py

On the box after install (builds its own db; copies nothing live):
    FIN_APP=/root/finance/finance_app.py FIN_MODS=/root/finance MI_DIR=/root/marg_ingest PORTAL_PY=/root/portal/portal.py \
        /root/wa/venv/bin/python3 -B /root/deploy/repo/deploy_kits/S243_REPORTS_TILE/walk_reports_tile_s243.py
"""
import datetime as dt
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

KIT = os.path.dirname(os.path.abspath(__file__))
FIN_APP = os.environ.get("FIN_APP", "/root/finance/finance_app.py")
FIN_MODS = os.environ.get("FIN_MODS", os.path.dirname(os.path.abspath(FIN_APP)) or "/root/finance")
MI_DIR = os.environ.get("MI_DIR", "/root/marg_ingest")
PORTAL_PY = os.environ.get("PORTAL_PY", "/root/portal/portal.py")
SF_PATCHER = os.environ.get("SF_PATCHER", os.path.join(os.path.dirname(KIT), "S243_SCREEN_FIXES", "patch_finance_daily_s243.py"))
KAL_KIT = os.environ.get("KAL_KIT", os.path.join(os.path.dirname(KIT), "S243_DARPAN_KAL"))
TMP = tempfile.mkdtemp(prefix="walk_s243_rpt_")
MOD = os.path.join(TMP, "mods")
UI = os.path.join(TMP, "ui")
POR = os.path.join(TMP, "portal")
DB = os.path.join(TMP, "finance.db")
PUNCH = os.path.join(TMP, "punches.csv")
os.makedirs(MOD)
os.makedirs(UI)
os.makedirs(POR)

sys.path.insert(0, KIT)
import patch_finance_app_reports_s243 as PATCHER                        # noqa: E402
import patch_portal_reports_tile_s243 as PPATCH                         # noqa: E402

PASSED, FAILED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label, ("   [%s]" % str(detail)[:300]) if detail and not cond else ""))


# ---- the app, patched in memory in the box's order: SCREEN_FIXES -> DARPAN_KAL -> this kit ----
src = io.open(FIN_APP, encoding="utf-8").read()
lineage = ["live"]
if os.path.exists(SF_PATCHER) and "S243: a checker (the doctor) lands on his Review console" not in src:
    p0 = os.path.join(TMP, "fa0.py")
    io.open(p0, "w", encoding="utf-8", newline="\n").write(src)
    r = subprocess.run([sys.executable, "-B", SF_PATCHER, "--out", p0 + ".sf"], env=dict(os.environ, FA_PATH=p0, FA_FROM_PIN8=""),
                       capture_output=True, text=True)
    if r.returncode == 0 and os.path.exists(p0 + ".sf"):
        src = io.open(p0 + ".sf", encoding="utf-8").read()
        lineage.append("SCREEN_FIXES")
kal_ok = False
if os.path.isdir(KAL_KIT) and os.path.exists(os.path.join(KAL_KIT, "patch_finance_app_darpan_kal_s243.py")):
    sys.path.insert(0, KAL_KIT)
    import patch_finance_app_darpan_kal_s243 as KALP                     # noqa: E402
    src, kst = KALP.patch_fa(src)
    if kst in ("patched", "already"):
        lineage.append("DARPAN_KAL")
        kal_ok = True
        for f in ("darpan_kal.py", "darpan_kal_schema.sql", "darpan_kal.html"):
            if os.path.exists(os.path.join(KAL_KIT, f)):
                shutil.copyfile(os.path.join(KAL_KIT, f), os.path.join(MOD, f))
patched, st = PATCHER.patch_fa(src)
io.open(os.path.join(MOD, "finance_app.py"), "w", encoding="utf-8", newline="\n").write(patched)
for m in ("finance_ingest", "finance_returns", "finance_upi", "marg_report", "finance_identity",
          "darpan_app", "returns_desk", "finance_returns_audit", "finance_money", "finance_returns_escalate",
          "finance_intent", "staff_pages", "joiner_app", "stock_app", "finance_clinic_day", "clinic_register",
          "purchase_app", "bank_mpr_status", "clinic_day_pdf", "marg_door", "amir_day", "marg_take",
          "marg_spine", "sale_bill", "amir_salts", "docterz_ingest", "docterz_day", "export_watch"):
    p = os.path.join(FIN_MODS, m + ".py")
    if os.path.exists(p):
        shutil.copyfile(p, os.path.join(MOD, m + ".py"))
for f in ("darpan_card.html", "darpan_corrections.html", "returns_desk.html", "pipeline_status.html",
          "staff_manage.html", "stock_desk.html", "stock_amir.html", "stock_pad.html"):
    p = os.path.join(FIN_MODS, f)
    if os.path.exists(p):
        shutil.copyfile(p, os.path.join(MOD, f))
shutil.copyfile(os.path.join(KIT, "reports_tile.py"), os.path.join(MOD, "reports_tile.py"))
for f in ("finance_daily.html", "finance_review.html", "finance_approvals.html", "finance_entry.html",
          "finance_workbench.html", "finance_entry_clinic.html"):
    io.open(os.path.join(UI, f), "w").write("<html><body>walk stub %s</body></html>" % f)
HUB_SRC = os.path.join(FIN_MODS, "finance_ui", "finance_approvals.html")
HUB_ST = "absent"
if os.path.exists(HUB_SRC):
    _hub = io.open(HUB_SRC, encoding="utf-8").read()
    if kal_ok:
        _hub, _ = KALP.patch_hub(_hub)
    _hub, HUB_ST = PATCHER.patch_hub(_hub)
    io.open(os.path.join(UI, "finance_approvals.html"), "w", encoding="utf-8", newline="\n").write(_hub)

TODAY = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).date()
T = TODAY.isoformat()
Y = (TODAY - dt.timedelta(days=1)).isoformat()
FIRST = TODAY.replace(day=1).isoformat()
NEED_TO = Y if TODAY.day != 1 else T
if TODAY.day == 1:
    FIRST = T
YMD = TODAY.strftime("%Y%m%d")

# ---- the database: every real schema this page reads --------------------------
con = sqlite3.connect(DB)
con.executescript(io.open(os.path.join(FIN_MODS, "finance_schema.sql"), encoding="utf-8").read())
if os.path.exists(os.path.join(FIN_MODS, "finance_returns.sql")):
    con.executescript(io.open(os.path.join(FIN_MODS, "finance_returns.sql"), encoding="utf-8").read())
con.executescript(io.open(os.path.join(FIN_MODS, "purchase_schema.sql"), encoding="utf-8").read())
MI_SCHEMA = None
if os.path.exists(os.path.join(MI_DIR, "marg_ingest.py")):
    sys.path.insert(0, MI_DIR)
    import marg_ingest as MI                                            # noqa: E402
    MI_SCHEMA = MI.SCHEMA
    con.executescript(MI.SCHEMA)
    con.execute("ALTER TABLE mi_file ADD COLUMN source TEXT NOT NULL DEFAULT ''")   # marg_take adds this column
sys.path.insert(0, MOD)
import amir_day as AD                                                   # noqa: E402
AD._ensure(con)
con.execute("CREATE TABLE IF NOT EXISTS stock_feed (id INTEGER PRIMARY KEY, as_on TEXT NOT NULL, source TEXT NOT NULL, "
            "item TEXT NOT NULL, qty INTEGER NOT NULL, received_at TEXT NOT NULL)")
con.execute("""CREATE TABLE IF NOT EXISTS purchase_salt_task (id INTEGER PRIMARY KEY, section TEXT NOT NULL, seq INTEGER NOT NULL,
        a TEXT NOT NULL, b TEXT, c TEXT, done INTEGER NOT NULL DEFAULT 0, done_by TEXT, done_at TEXT, answer TEXT, answer_by TEXT,
        answer_at TEXT, source_md5 TEXT, pushed_at TEXT, UNIQUE(section, a))""")
con.execute("CREATE TABLE IF NOT EXISTS upi_txn (id INTEGER PRIMARY KEY, merchant_id TEXT NOT NULL, unit TEXT, "
            "txn_date TEXT NOT NULL, amount_p INTEGER NOT NULL, rrn TEXT NOT NULL, mode TEXT, txn_time TEXT, "
            "source_sha TEXT, ingested_at TEXT)")
for user, role in (("zzwalkdoc", "checker"), ("zzwalkmaker", "maker"), ("amir", "viewer")):
    con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('medical',?,?,1)", (user, role))
# `shavez` deliberately NOT seeded here: the kit's own seed script must admit him (checked below)
# `alisha` holds a CLINIC role only -- a signed-in login with no medical role
con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('clinic','alisha','maker',1)")
con.commit()
con.close()

io.open(PUNCH, "w").write("user_id,datetime,io_mode,verify_mode,received_at\n7,%s 09:00:00,0,1,x\n" % T)   # Alisha punched, Amir did not

os.environ.update(FINANCE_DB=DB, FINANCE_UI_DIR=UI, FINANCE_ALLOW_HEADER_AUTH="1",
                  FINANCE_PORTAL_LOGIN="/portal", FINANCE_SCAN_DIR=os.path.join(TMP, "scans"),
                  FINANCE_MARG_TOKEN="DUMMY-TOKEN-PUT-HERE", FINANCE_UPI_DIR=os.path.join(TMP, "upi"),
                  FINANCE_AUTOAPPLY_OFF=os.path.join(TMP, "AUTOAPPLY_OFF"),
                  ATT_PUNCH_CSV=PUNCH, SR_DB_PATH=os.path.join(TMP, "no_such_staff_register.db"))
import finance_app as FA                                                # noqa: E402

print("walking %s (patched in memory: %s; lineage %s)" % (FIN_APP, st, " -> ".join(lineage)))
print("  temp db %s   mi_file schema %s" % (DB, "from marg_ingest.py" if MI_SCHEMA else "ABSENT (MI_DIR not found)"))

c = FA.app.test_client()
DOC = {"X-Clinic-User": "zzwalkdoc", "X-Clinic-Role": "doctor"}
SHZ = {"X-Clinic-User": "shavez", "X-Clinic-Role": "manager"}
AMR = {"X-Clinic-User": "amir", "X-Clinic-Role": "staff"}
ALI = {"X-Clinic-User": "alisha", "X-Clinic-Role": "staff"}
PAGE = "/finance/reports/aaj"
API = "/finance/reports/aaj/api/status"


def page(h, url=PAGE):
    r = c.get(url, headers=h)
    return r.status_code, r.get_data(as_text=True), r


def api(h, url=API):
    r = c.get(url, headers=h)
    return r.status_code, (r.get_json(silent=True) or {})


def dbx(sql, *args):
    cx = sqlite3.connect(DB)
    cx.execute(sql, args)
    cx.commit()
    cx.close()


def rows_by_key(j):
    return {r["key"]: r for r in j.get("rows", [])}


# ---- 0 mount --------------------------------------------------------------------
ck("reports_tile is mounted (blueprint registered)", "reports_tile" in FA.app.blueprints)
ck("healthz still 200", c.get("/finance/healthz").status_code == 200)
ck("/finance/amir still opens for amir (nothing else moved)", c.get("/finance/amir", headers=AMR).status_code in (200, 302, 303))
if kal_ok:
    ck("darpan_kal is still mounted beside it", "darpan_kal" in FA.app.blueprints)

# ---- 1 the gate: before the seed, shavez (portal role manager, no medical row) is NOT admitted
s, h, r = page(SHZ)
ck("before the seed: shavez has no medical role -> sent to the portal (302), not a 500", s == 302 and "/portal" in (r.headers.get("Location") or ""), (s, r.headers.get("Location")))
r1 = subprocess.run([sys.executable, "-B", os.path.join(KIT, "seed_reports_role_s243.py"), DB], capture_output=True, text=True)
r2 = subprocess.run([sys.executable, "-B", os.path.join(KIT, "seed_reports_role_s243.py"), DB], capture_output=True, text=True)
cx = sqlite3.connect(DB)
n_shz = cx.execute("SELECT COUNT(*) FROM unit_role WHERE unit='medical' AND username='shavez' AND role='viewer' AND active=1").fetchone()[0]
cx.close()
ck("seed_reports_role: adds shavez a medical viewer row once; second run NOT changed",
   r1.returncode == 0 and r2.returncode == 0 and n_shz == 1 and "added unit_role medical/shavez" in r1.stdout and "NOT changed" in r2.stdout,
   (r1.stdout, r2.stdout, r1.stderr, r2.stderr))

# ---- 2 the empty morning: both rows due --------------------------------------
s, h, r = page(SHZ)
ck("PAGE shavez: 200 text/html", s == 200 and "text/html" in (r.content_type or ""), (s, r.content_type))
ck("PAGE: the one instruction line", "Marg me report banao, yahan khud tick ho jayegi" in h)
ck("PAGE: 30-s auto refresh present", "http-equiv=refresh content='30'" in h)
ck("PAGE: no JavaScript at all", "<script" not in h.lower())
ck("PAGE: the sale row and the stock row, both baaki", h.count("baaki") >= 2 and "Bill-wise sale report" in h and "Stock closing report" in h)
ck("PAGE: yesterday's date named on the sale row", "kal ki, %s" % dt.date.fromisoformat(Y).strftime("%d-%m-%Y") in h)
ck("PAGE: no Amir rows on a day he did not punch and has no amir_day", "Purchase item-wise report" not in h and "Amir ka din" not in h)
ck("PAGE: no salt row when no tick is newer than the last list", "Salt-wise item list" not in h)
ck("PAGE: 0 / 2 aa gayi", "0 / 2 aa gayi" in h)
s, j = api(DOC)
ck("API checker: ok, 2 rows due, the owner's line", s == 200 and j.get("ok") and j.get("total") == 2 and j.get("line") == "Today's reports: 0 of 2 arrived", j)
ck("API: no phone number, no token in the payload", "DUMMY-TOKEN" not in json.dumps(j))

# ---- 3 a refused sale report, then a verified one -----------------------------
if MI_SCHEMA:
    dbx("INSERT INTO mi_file (md5,drive_name,type,date_from,date_to,verdict,reason,received_at,source) VALUES "
        "('aaaa1','SALE_BILLWISE_x.xls','SALE_BILLWISE',?,?,'REFUSED','deep parse failed: title/data truncated',?, 'push')", Y, Y, T + "T09:01:12+05:30")
    s, h, r = page(SHZ)
    ck("PAGE: a refused sale report reads 'manzoor nahi' with the time", "manzoor nahi" in h and "09:01 baje" in h)
    ck("PAGE: the refusal reason in plain Hindi, the router's words beneath", "dobara export kijiye" in h and "deep parse failed" in h)
    s, j = api(DOC)
    ck("API: sale row state refused, reason_hi present", rows_by_key(j)["SALE_BILLWISE"]["state"] == "refused" and rows_by_key(j)["SALE_BILLWISE"].get("reason_hi"), j)
    ck("API: the owner's line counts the refusal", j.get("line") == "Today's reports: 0 of 2 arrived, 1 refused", j.get("line"))
    dbx("INSERT INTO mi_file (md5,drive_name,type,date_from,date_to,verdict,reason,received_at,source,lines) VALUES "
        "('aaaa2','SALE_BILLWISE_y.xls','SALE_BILLWISE',?,?,'VERIFIED','',?, 'push', 40)", Y, Y, T + "T09:06:40+05:30")
    s, h, r = page(SHZ)
    ck("PAGE: the later verified copy wins: 'aa gayi 09:06'", "aa gayi" in h and "09:06 baje" in h and "manzoor nahi" not in h)
    # a month-to-date sale export that only covers up to the day before yesterday does NOT count for yesterday
    dbx("DELETE FROM mi_file WHERE md5='aaaa2'")
    D2 = (TODAY - dt.timedelta(days=2)).isoformat()
    dbx("INSERT INTO mi_file (md5,type,date_from,date_to,verdict,received_at) VALUES ('aaaa3','SALE_BILLWISE',?,?,'VERIFIED',?)", FIRST if FIRST <= D2 else D2, D2, T + "T09:07:00+05:30")
    s, j = api(DOC)
    ck("a verified sale export that stops before yesterday does not tick yesterday", rows_by_key(j)["SALE_BILLWISE"]["state"] == "refused", rows_by_key(j)["SALE_BILLWISE"])
    dbx("INSERT INTO mi_file (md5,type,date_from,date_to,verdict,received_at) VALUES ('aaaa2','SALE_BILLWISE',?,?,'VERIFIED',?)", Y, Y, T + "T09:06:40+05:30")
else:
    print("  SKIP  mi_file scenarios (MI_DIR not found)")

# the pushed-report door alone (older route) also counts
cx = sqlite3.connect(DB)
FA_ = None
cx.execute("CREATE TABLE IF NOT EXISTS marg_push_staging (id INTEGER PRIMARY KEY AUTOINCREMENT, unit TEXT NOT NULL DEFAULT 'medical', "
           "received_at TEXT NOT NULL DEFAULT (datetime('now','localtime')), file_md5 TEXT NOT NULL, filename_hint TEXT, status TEXT NOT NULL DEFAULT 'pending', "
           "survey_json TEXT, parsed_json TEXT, applied_at TEXT, applied_by TEXT, apply_result_json TEXT)")
cx.commit()
cx.close()

# ---- 4 the stock closing ----------------------------------------------------------
dbx("INSERT INTO stock_feed (as_on, source, item, qty, received_at) VALUES (?, 'push_snapshot', 'X', 1, ?)",
    TODAY.strftime("%d-%m-%Y"), T + "T09:12:00")
s, h, r = page(SHZ)
s2, j = api(DOC)
ck("PAGE: a morning push_snapshot as on today ticks the stock closing (yesterday's close)", rows_by_key(j)["STOCK_CLOSING"]["state"] == "ok" and "09:12 baje" in h)
ck("PAGE: everything in -> the green 'sab reports aa gayi' card", "Aaj ki sab reports aa gayi" in h)
ck("API: the owner's line 2 of 2", j.get("line") == "Today's reports: 2 of 2 arrived", j.get("line"))

# ---- 5 Amir's day, by punch and by amir_day ---------------------------------------
io.open(PUNCH, "w").write("user_id,datetime,io_mode,verify_mode,received_at\n7,%s 09:00:00,0,1,x\n101,%s 09:02:11,0,1,x\n" % (T, T))
s, h, r = page(SHZ)
s2, j = api(DOC)
ck("Amir punched today (machine id 101 in the punch file) -> the purchase pair appears, both due",
   j.get("amir_day") and j.get("amir_why") == "punch" and j.get("total") == 4 and rows_by_key(j)["PURCHASE_ITEMWISE"]["state"] == "due"
   and rows_by_key(j)["PURCHASE_BILLWISE"]["state"] == "due" and "Amir ka din" in h, (j.get("amir_day"), j.get("amir_why"), j.get("total")))
io.open(PUNCH, "w").write("user_id,datetime,io_mode,verify_mode,received_at\n7,%s 09:00:00,0,1,x\n" % T)
s2, j = api(DOC)
ck("punch removed -> the pair is gone again", not j.get("amir_day") and j.get("total") == 2, j.get("total"))
dbx("INSERT OR IGNORE INTO amir_day (day, opened_at) VALUES (?, ?)", T, T + " 09:00:00")
s2, j = api(DOC)
ck("an amir_day row for today alone -> Amir day (his page opened)", j.get("amir_day") and j.get("amir_why") == "amir_day" and j.get("total") == 4, (j.get("amir_why"), j.get("total")))
dbx("INSERT INTO purchase_export VALUES ('pe1','BILLWISE','f.xls',?,?,?,?,5,0,NULL)", FIRST, NEED_TO, YMD + "-093010", T + "T09:30:12")
s2, j = api(DOC)
ck("purchase BILLWISE received today, 1st..yesterday -> aa gayi; item-wise still due",
   rows_by_key(j)["PURCHASE_BILLWISE"]["state"] == "ok" and rows_by_key(j)["PURCHASE_ITEMWISE"]["state"] == "due", rows_by_key(j))
dbx("INSERT INTO purchase_export VALUES ('pe2','ITEMWISE','f.xls',?,?,?,?,9,0,NULL)", FIRST, NEED_TO, YMD + "-093110", T + "T09:31:12")
s, h, r = page(SHZ)
s2, j = api(DOC)
ck("purchase ITEMWISE received today -> aa gayi; 4 of 4", rows_by_key(j)["PURCHASE_ITEMWISE"]["state"] == "ok" and j.get("line") == "Today's reports: 4 of 4 arrived", j.get("line"))
ck("PAGE: the two purchase rows read '1 tareekh se aaj tak (Amir ke din)'", h.count("1 tareekh se aaj tak (Amir ke din)") == 2)

# ---- 6 the salt list: only when ticks are newer than the last list ----------------
if MI_SCHEMA:
    dbx("INSERT INTO mi_file (md5,type,date_from,date_to,verdict,received_at) VALUES ('ssss0','SALT_WISE_ITEM_LIST',?,?,'VERIFIED',?)",
        (TODAY - dt.timedelta(days=3)).isoformat(), (TODAY - dt.timedelta(days=3)).isoformat(), (TODAY - dt.timedelta(days=3)).isoformat() + "T10:00:00+05:30")
    dbx("INSERT INTO purchase_salt_task (section,seq,a,b,done,done_at) VALUES ('rename',1,'OLD','NEW',1,?)", (TODAY - dt.timedelta(days=4)).isoformat() + " 12:00:00")
    s2, j = api(DOC)
    ck("a tick OLDER than the last list -> no salt row", "SALT_WISE_ITEM_LIST" not in rows_by_key(j) and j.get("total") == 4, list(rows_by_key(j)))
    dbx("INSERT INTO purchase_salt_task (section,seq,a,b,done,done_at) VALUES ('create',2,'NEW ITEM','SALT',1,?)", Y + " 18:30:00")
    s, h, r = page(SHZ)
    s2, j = api(DOC)
    ck("a tick NEWER than the last list -> the salt row appears, due", rows_by_key(j).get("SALT_WISE_ITEM_LIST", {}).get("state") == "due" and "Salt-wise item list" in h and "nayi list chahiye" in h, rows_by_key(j).get("SALT_WISE_ITEM_LIST"))
    ck("API: 4 of 5 now", j.get("line") == "Today's reports: 4 of 5 arrived", j.get("line"))
    dbx("INSERT INTO mi_file (md5,type,date_from,date_to,verdict,reason,received_at) VALUES ('ssss1','SALT_WISE_ITEM_LIST',?,?,'REFUSED','title match + wrong layout',?)", T, T, T + "T09:40:00+05:30")
    s2, j = api(DOC)
    ck("a refused salt list today -> manzoor nahi with the layout reason", rows_by_key(j)["SALT_WISE_ITEM_LIST"]["state"] == "refused" and "format" in rows_by_key(j)["SALT_WISE_ITEM_LIST"]["reason_hi"], rows_by_key(j)["SALT_WISE_ITEM_LIST"])
    dbx("INSERT INTO mi_file (md5,type,date_from,date_to,verdict,received_at,kept) VALUES ('ssss2','SALT_WISE_ITEM_LIST',?,?,'VERIFIED',?,1)", T, T, T + "T09:45:00+05:30")
    s, h, r = page(SHZ)
    s2, j = api(DOC)
    ck("the fresh list arrives -> aa gayi 09:45; 5 of 5", rows_by_key(j)["SALT_WISE_ITEM_LIST"]["state"] == "ok" and "09:45 baje" in h and j.get("line") == "Today's reports: 5 of 5 arrived", j.get("line"))

# ---- 7 an unrecognised file today is said once, at the end ------------------------
if MI_SCHEMA:
    dbx("INSERT INTO mi_file (md5,type,verdict,reason,received_at) VALUES ('uuuu1','','UNKNOWN','no signature matches this title: \"Ledger Summary\"',?)", T + "T09:50:00+05:30")
    s, h, r = page(SHZ)
    ck("PAGE: 'Ek file pehchan nahi aayi' line with the Hindi reason", "Ek file pehchan nahi aayi" in h and "wahi report chuniye" in h)

# ---- 8 who may open it ------------------------------------------------------------
s, h, r = page(AMR)
ck("PAGE amir (viewer): 200", s == 200)
s, h, r = page(ALI)
ck("alisha (clinic role only, no medical role): sent to the portal, nothing shown", s == 302 and "/portal" in (r.headers.get("Location") or ""), (s, r.headers.get("Location")))
r = c.get(PAGE)
ck("anonymous -> 302 to the portal", r.status_code == 302 and "/portal" in (r.headers.get("Location") or ""), (r.status_code, r.headers.get("Location")))
r = c.get(API)
ck("anonymous API -> not 200", r.status_code in (302, 401, 403), r.status_code)
s, h, r = page(SHZ, PAGE + "/" + Y)
ck("PAGE /finance/reports/aaj/<yesterday>: 200, no auto-refresh on a picked day, a way back", s == 200 and "http-equiv=refresh" not in h and "Aaj par wapas" in h)
r = c.get(PAGE + "/not-a-date", headers=SHZ)
ck("a malformed date -> back to today (302)", r.status_code == 302 and r.headers.get("Location", "").endswith(PAGE), (r.status_code, r.headers.get("Location")))
ck("the page's own healthz", c.get("/finance/reports/aaj/api/healthz", headers=SHZ).status_code == 200)

# ---- 9 the owner's hub line -------------------------------------------------------
r = c.get("/finance/approvals", headers=DOC)
hub_html = r.get_data(as_text=True)
ck("PAGE owner hub /finance/approvals: 200 (real page, patched %s)" % HUB_ST, r.status_code == 200 and HUB_ST in ("patched", "already"))
ck("PAGE owner hub: the line 'Today's reports' with its loader and its call, on the Marg card",
   'id="rptToday"' in hub_html and "function loadReports()" in hub_html and "loadPushes(); loadReports();" in hub_html
   and hub_html.find('id="margCard"') < hub_html.find('id="rptToday"') < hub_html.find('id="homeMedCard"'))
if kal_ok:
    ck("PAGE owner hub: the DARPAN_KAL card is still there beside it", 'id="kalCard"' in hub_html and "loadStaffCards(); loadKal();" in hub_html)

# ---- 10 nothing was written by the page ------------------------------------------
cx = sqlite3.connect(DB)
ck("the page wrote nothing: no audit_log rows, no data_flag rows from this walk",
   cx.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] == 0 and cx.execute("SELECT COUNT(*) FROM data_flag").fetchone()[0] == 0)
cx.close()

# ---- 11 the portal: who is shown the tile ---------------------------------------
if os.path.exists(PORTAL_PY):
    psrc = io.open(PORTAL_PY, encoding="utf-8").read()
    pnew, pst = PPATCH.patch_text(psrc)
    io.open(os.path.join(POR, "portal.py"), "w", encoding="utf-8", newline="\n").write(pnew)
    shutil.copyfile(os.path.join(KIT, "tile_grants.json"), os.path.join(POR, "tile_grants.json"))
    os.environ["TILE_GRANTS_FILE"] = os.path.join(POR, "tile_grants.json")
    os.environ.setdefault("PORTAL_PIN_SALT", "walk")
    os.environ.setdefault("PORTAL_TOKEN_SEED", "walk")
    sys.path.insert(0, POR)
    try:
        import portal                                                    # noqa: E402
        ck("portal.py patched in memory (%s) imports: every tile is grouped (its own assert)" % pst, pst in ("patched", "already"))
        ck("grants file in use is v13", portal._tile_grants().get("version") == 13)

        def tiles(user, role="staff", pc=False):
            out = []
            for _g, items in portal._visible_sections(role, pc, user):
                out += [t["name"] for t in items]
            return out
        ck("shavez (portal role manager) is shown 'Aaj ki reports'", "Aaj ki reports" in tiles("shavez", role="manager"))
        ck("amir is shown 'Aaj ki reports' beside 'Amir ka kaam'", tiles("amir") == ["Amir ka kaam", "Aaj ki reports"], tiles("amir"))
        ck("alisha is NOT shown it", "Aaj ki reports" not in tiles("alisha"))
        ck("darpan / shivani / a bare staff login are NOT shown it",
           all("Aaj ki reports" not in tiles(u) for u in ("darpan", "shivani", "nobody")))
        ck("the doctor has it by role", "Aaj ki reports" in tiles("manoj", role="doctor"))
        ck("where it goes", [t["url"] for t in portal.TILES if t["name"] == "Aaj ki reports"] == ["/finance/reports/aaj"])
        ck("shavez's other tiles are unchanged (the S242 walk's list, plus the new one)",
           [t for t in tiles("shavez") if t != "Aaj ki reports"] == ["Call Tracker", "Forms & Downloads", "Asset Register", "Scan Purchase",
                                                                       "Vaapsi Desk", "Docterz Revenue", "Docterz daily collection"], tiles("shavez"))
        portal.TILE_GRANTS_FILE = os.path.join(POR, "no_such_grants.json")
        portal._GRANTS_CACHE["mtime"] = None
        portal._GRANTS_CACHE["data"] = None
        ck("FAIL CLOSED: no grants file -> shavez and amir lose the tile, the doctor keeps it",
           "Aaj ki reports" not in tiles("shavez", role="manager") and "Aaj ki reports" not in tiles("amir")
           and "Aaj ki reports" in tiles("manoj", role="doctor"))
    except Exception as ex:                                              # noqa: BLE001
        ck("portal.py imports after the patch", False, ex)
else:
    print("  SKIP  portal checks (PORTAL_PY not found: %s)" % PORTAL_PY)

# ---- 12 the module's own selftest -----------------------------------------------
r = subprocess.run([sys.executable, "-B", os.path.join(KIT, "reports_tile.py")], capture_output=True, text=True)
ck("reports_tile.py --selftest: 0 failures", r.returncode == 0 and "0 failures" in r.stdout, r.stdout[-300:])

print()
print("WALK: %d passed, %d failed" % (len(PASSED), len(FAILED)))
for f in FAILED:
    print("  FAILED:", f)
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(0 if not FAILED else 1)
