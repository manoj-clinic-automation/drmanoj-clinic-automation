#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_amir_visit_s243.py -- the LIVE-SHAPE walk for S243_AMIR_VISIT.

A real Flask app -- the finance_app.py named by FIN_APP (live pin f002defb), patched IN MEMORY
by the two kits that install before this one (S243_SCREEN_FIXES, S243_DARPAN_KAL) so the walk
runs on the box's predicted state -- over a real sqlite database built from finance_schema.sql
+ finance_returns.sql + purchase_schema.sql + purchase_app's salt tables + marg_ingest's mi_file,
with the real sibling modules beside it and THIS kit's amir_day.py in place of the live one.  The
real hub page, patched by DARPAN_KAL's patcher and then by this kit's, is served from the UI dir.

Seeds one visit day: the pair of purchase reports (arrived), two bills from the bill-wise export,
four open salt tasks, a STALE SALT_WISE_ITEM_LIST in mi_file (yesterday).  Then:
  ticks -> the red prompt (Amir) / amber (owner) / pending (API);  a newer mi_file row -> green;
  the day's OPEN/DONE state never moves on the prompt;  the API is checker-only;  anonymous -> portal;
  the hub carries the collapsed block and DARPAN_KAL's card together.

    FIN_APP=<finance_app.py> FIN_MODS=<folder with the modules> python3 -B walk_amir_visit_s243.py

On the box after install (builds its own db; copies nothing live; patchers say "already"):
    FIN_APP=/root/finance/finance_app.py FIN_MODS=/root/finance SIBLINGS=/root/deploy/repo/deploy_kits \\
        /root/wa/venv/bin/python3 -B /root/deploy/repo/deploy_kits/S243_AMIR_VISIT/walk_amir_visit_s243.py
"""
import datetime as dt
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

KIT = os.path.dirname(os.path.abspath(__file__))
SIBLINGS = os.environ.get("SIBLINGS", os.path.dirname(KIT))
FIN_APP = os.environ.get("FIN_APP", "/root/finance/finance_app.py")
FIN_MODS = os.environ.get("FIN_MODS", os.path.dirname(os.path.abspath(FIN_APP)) or "/root/finance")
MARG_INGEST = os.environ.get("MARG_INGEST", os.path.join(os.path.dirname(FIN_MODS.rstrip("/")), "marg_ingest", "marg_ingest.py"))
TMP = tempfile.mkdtemp(prefix="walk_s243_amir_visit_")
MOD = os.path.join(TMP, "mods")
UI = os.path.join(TMP, "ui")
DB = os.path.join(TMP, "finance.db")
STATE = os.path.join(TMP, "salts_refresh.state.json")
os.makedirs(MOD)
os.makedirs(UI)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---- finance_app: the live bytes, plus the two kits that install first --------
src = open(FIN_APP, encoding="utf-8").read()
FA_ST = []
sf_path = os.path.join(SIBLINGS, "S243_SCREEN_FIXES", "patch_finance_daily_s243.py")
if os.path.exists(sf_path):
    SF = _load("sf_patch", sf_path)
    if SF.MARK in src:
        FA_ST.append("screen_fixes:already")
    elif src.count(SF.OLD) == 1:
        src = src.replace(SF.OLD, SF.NEW, 1)
        FA_ST.append("screen_fixes:patched")
    else:
        FA_ST.append("screen_fixes:REFUSED")
else:
    FA_ST.append("screen_fixes:absent")
kal_path = os.path.join(SIBLINGS, "S243_DARPAN_KAL", "patch_finance_app_darpan_kal_s243.py")
KAL = None
if os.path.exists(kal_path):
    KAL = _load("kal_patch", kal_path)
    src, st = KAL.patch_fa(src)
    FA_ST.append("darpan_kal:" + st)
else:
    FA_ST.append("darpan_kal:absent")
open(os.path.join(MOD, "finance_app.py"), "w", encoding="utf-8", newline="\n").write(src)

for m in ("finance_ingest", "finance_returns", "finance_upi", "marg_report", "finance_identity",
          "darpan_app", "returns_desk", "finance_returns_audit", "finance_money", "finance_returns_escalate",
          "finance_intent", "staff_pages", "joiner_app", "stock_app", "finance_clinic_day", "clinic_register",
          "purchase_app", "bank_mpr_status", "clinic_day_pdf", "marg_door", "marg_take",
          "marg_spine", "sale_bill", "amir_salts", "docterz_ingest", "docterz_day", "padwriter", "padreader",
          "darpan_kal"):
    p = os.path.join(FIN_MODS, m + ".py")
    if os.path.exists(p):
        shutil.copyfile(p, os.path.join(MOD, m + ".py"))
for f in ("darpan_card.html", "darpan_corrections.html", "returns_desk.html", "pipeline_status.html",
          "staff_manage.html", "stock_desk.html", "stock_amir.html", "stock_pad.html", "darpan_kal.html",
          "darpan_kal_schema.sql"):
    p = os.path.join(FIN_MODS, f)
    if os.path.exists(p):
        shutil.copyfile(p, os.path.join(MOD, f))
kal_kit = os.path.join(SIBLINGS, "S243_DARPAN_KAL")
for f in ("darpan_kal.py", "darpan_kal_schema.sql", "darpan_kal.html"):
    p = os.path.join(kal_kit, f)
    if os.path.exists(p) and not os.path.exists(os.path.join(MOD, f)):
        shutil.copyfile(p, os.path.join(MOD, f))
# THIS kit's amir_day.py replaces the live one (the installer's full-file placement)
shutil.copyfile(os.path.join(KIT, "amir_day.py"), os.path.join(MOD, "amir_day.py"))

for f in ("finance_daily.html", "finance_review.html", "finance_approvals.html", "finance_entry.html",
          "finance_workbench.html", "finance_entry_clinic.html"):
    open(os.path.join(UI, f), "w").write("<html><body>walk stub %s</body></html>" % f)
sys.path.insert(0, KIT)
import patch_hub_amir_visit_s243 as HUBP                                 # noqa: E402
HUB_SRC = os.path.join(FIN_MODS, "finance_ui", "finance_approvals.html")
HUB_ST = []
if os.path.exists(HUB_SRC):
    hub = open(HUB_SRC, encoding="utf-8").read()
    if KAL is not None:
        hub, st = KAL.patch_hub(hub)
        HUB_ST.append("darpan_kal:" + st)
    hub, st = HUBP.patch_text(hub)
    HUB_ST.append("amir_visit:" + st)
    open(os.path.join(UI, "finance_approvals.html"), "w", encoding="utf-8", newline="\n").write(hub)
else:
    HUB_ST.append("absent")

# ---- the database ------------------------------------------------------------
con = sqlite3.connect(DB)
con.executescript(open(os.path.join(FIN_MODS, "finance_schema.sql"), encoding="utf-8").read())
con.executescript(open(os.path.join(FIN_MODS, "finance_returns.sql"), encoding="utf-8").read())
con.executescript(open(os.path.join(FIN_MODS, "purchase_schema.sql"), encoding="utf-8").read())
con.execute("""CREATE TABLE IF NOT EXISTS purchase_salt_task (
        id INTEGER PRIMARY KEY, section TEXT NOT NULL, seq INTEGER NOT NULL, a TEXT NOT NULL, b TEXT, c TEXT,
        done INTEGER NOT NULL DEFAULT 0, done_by TEXT, done_at TEXT, answer TEXT, answer_by TEXT, answer_at TEXT,
        source_md5 TEXT, pushed_at TEXT, UNIQUE(section, a))""")
con.execute("CREATE TABLE IF NOT EXISTS purchase_salt_marg (item_norm TEXT PRIMARY KEY, item TEXT NOT NULL, "
            "salt TEXT NOT NULL, as_on TEXT NOT NULL, source_md5 TEXT)")
mi_sql = None
if os.path.exists(MARG_INGEST):
    mtxt = open(MARG_INGEST, encoding="utf-8").read()
    m = re.search(r"CREATE TABLE IF NOT EXISTS mi_file \(.*?\);", mtxt, re.S)
    mi_sql = m.group(0) if m else None
if not mi_sql:                                                            # the live schema, copied at build
    mi_sql = """CREATE TABLE IF NOT EXISTS mi_file (
  md5 TEXT PRIMARY KEY, drive_id TEXT NOT NULL DEFAULT '', drive_name TEXT NOT NULL DEFAULT '',
  drive_folder TEXT NOT NULL DEFAULT '', drive_mtime TEXT NOT NULL DEFAULT '', size INTEGER NOT NULL DEFAULT 0,
  stamp TEXT NOT NULL DEFAULT '', type TEXT NOT NULL DEFAULT '', variant TEXT NOT NULL DEFAULT '',
  date_from TEXT NOT NULL DEFAULT '', date_to TEXT NOT NULL DEFAULT '', verdict TEXT NOT NULL DEFAULT '',
  reason TEXT NOT NULL DEFAULT '', server_name TEXT NOT NULL DEFAULT '', kept INTEGER NOT NULL DEFAULT 0,
  lines INTEGER NOT NULL DEFAULT 0, pc_type TEXT NOT NULL DEFAULT '', pc_verdict TEXT NOT NULL DEFAULT '',
  agree TEXT NOT NULL DEFAULT '', received_at TEXT NOT NULL);"""
con.executescript(mi_sql)
for user, role in (("zzamir", "maker"), ("zzwalkdoc", "checker"), ("zzviewer", "viewer")):
    con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('medical',?,?,1)", (user, role))
con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('clinic','zzclinic','maker',1)")
con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('darpan_kal.recipients', 'zzwalkdoc:dr_manoj')")
con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('returns.act_from', '2026-01-01')")

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
NOW = dt.datetime.now(IST).replace(microsecond=0)
TODAY = NOW.strftime("%Y-%m-%d")
FIRST = TODAY[:8] + "01"
YDAY = (NOW - dt.timedelta(days=1))
if NOW.hour == 0 and NOW.minute < 5:
    print("!! walk started inside the midnight minute -- rerun after 00:05 IST"); sys.exit(2)


def stamp14(t):
    return t.strftime("%Y%m%d-%H%M%S")


# the pair of purchase reports, arrived this morning, 1st of the month to today
T_BW = NOW.replace(hour=max(NOW.hour - 1, 0), minute=5, second=0) if NOW.hour >= 1 else NOW.replace(minute=0, second=0)
con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) "
            "VALUES ('bw0000000000000000000000000000bw','BILLWISE','bw.xls',?,?,?,?,2,1234500)",
            (FIRST, TODAY, stamp14(T_BW), T_BW.isoformat()))
con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) "
            "VALUES ('iw0000000000000000000000000000iw','ITEMWISE','iw.xls',?,?,?,?,9,1234500)",
            (FIRST, TODAY, stamp14(T_BW + dt.timedelta(minutes=2)), (T_BW + dt.timedelta(minutes=2)).isoformat()))
for i, (sup, bno, amt) in enumerate((("WALK SUPPLIER ONE", "B-ONE", 700000), ("WALK SUPPLIER TWO", "B-TWO", 534500))):
    con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, bw_md5, date_src) "
                "VALUES (?,?,?,?,?,?,'bw0000000000000000000000000000bw','BILLWISE')",
                (sup.lower(), sup, bno, TODAY, TODAY[:7], amt))
# four open salt tasks
for seq, (sec, a, b) in enumerate((("rename", "METHYL PREDNISOLONE", "METHYLPREDNISOLONE"),
                                    ("rename", "PARACETAMOLE", "PARACETAMOL"),
                                    ("create", "ACECLOFENAC+PARACETAMOL", "x"),
                                    ("change", "WALKITEM TAB", "OLDSALT"))):
    con.execute("INSERT INTO purchase_salt_task (section, seq, a, b, c) VALUES (?,?,?,?,?)", (sec, seq, a, b, "NEWSALT" if sec == "change" else None))
# a STALE salt list: yesterday's, taken by the door
con.execute("INSERT INTO mi_file (md5, drive_name, stamp, type, verdict, kept, received_at) VALUES "
            "('sw0000000000000000000000000000s1','SALT_WISE_ITEM_LIST.XLS',?,'SALT_WISE_ITEM_LIST','VERIFIED',1,?)",
            (stamp14(YDAY.replace(hour=11, minute=20, second=0)), YDAY.replace(hour=11, minute=21, second=0).isoformat()))
con.commit()
con.close()

os.environ.update(FINANCE_DB=DB, FINANCE_UI_DIR=UI, FINANCE_ALLOW_HEADER_AUTH="1",
                  FINANCE_PORTAL_LOGIN="/portal", FINANCE_SCAN_DIR=os.path.join(TMP, "scans"),
                  FINANCE_MARG_TOKEN="DUMMY-TOKEN-PUT-HERE", FINANCE_UPI_DIR=os.path.join(TMP, "upi"),
                  FINANCE_AUTOAPPLY_OFF=os.path.join(TMP, "AUTOAPPLY_OFF"),
                  SALTS_REFRESH_STATE=STATE)
sys.path.insert(0, MOD)
import finance_app as FA                                                  # noqa: E402
import amir_day as AD                                                     # noqa: E402

print("walking %s (finance_app in memory: %s; hub: %s)" % (FIN_APP, " ".join(FA_ST), " ".join(HUB_ST)))
print("  temp db %s  today %s" % (DB, TODAY))
PASSED, FAILED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label, ("   [%s]" % str(detail)[:300]) if detail and not cond else ""))


c = FA.app.test_client()
AMIR = {"X-Clinic-User": "zzamir", "X-Clinic-Role": "staff"}
DOC = {"X-Clinic-User": "zzwalkdoc", "X-Clinic-Role": "doctor"}
VIEW = {"X-Clinic-User": "zzviewer", "X-Clinic-Role": "staff"}
CLIN = {"X-Clinic-User": "zzclinic", "X-Clinic-Role": "staff"}
API = "/finance/amir/day/api/visit-summary"


def page(u, h=None):
    r = c.get(u, headers=h or {})
    return r.status_code, r.get_data(as_text=True), r


def api(u, h):
    r = c.get(u, headers=h)
    return r.status_code, (r.get_json(silent=True) or {})


def dbx():
    x = sqlite3.connect(DB)
    x.row_factory = sqlite3.Row
    return x


import html as _html                                                      # noqa: E402
RED = "Marg se SALT WISE ITEM LIST nikaalo"
GREEN = "SALT WISE ITEM LIST aa gayi"
AMBER = "Waiting for Marg's SALT WISE ITEM LIST"
AMBER_H = _html.escape(AMBER)                     # the page escapes the apostrophe; the API does not

# ---- 0 mount --------------------------------------------------------------------
ck("amir_day is mounted (and amir_salts rides on it)", "amir_day" in FA.app.blueprints and "amir_salts" in FA.app.blueprints)
ck("darpan_kal is mounted too (the kit before this one)", "darpan_kal" in FA.app.blueprints, list(FA.app.blueprints))
ck("healthz still 200", c.get("/finance/healthz").status_code == 200)
s, j = api("/finance/amir/api/healthz", AMIR)
ck("amir healthz names S243_AMIR_VISIT", s == 200 and j.get("kit") == "S243_AMIR_VISIT", j)
ck("the gate steps are unchanged (2,4,5,6)", AD.GATE_STEPS == (2, 4, 5, 6))

# ---- 1 before any tick: no prompt --------------------------------------------------
s, h, r = page("/finance/amir", AMIR)
ck("Amir: /finance/amir sends him to step 1 (303)", s == 303 and r.headers["Location"].endswith("/finance/amir/step/1"), (s, r.headers.get("Location")))
s, h, _r = page("/finance/amir/step/6", AMIR)
ck("Amir step 6 opens 200, no prompt before any salt tick", s == 200 and RED not in h and GREEN not in h)
s, h, _r = page("/finance/amir/day", DOC)
ck("owner page: 200, 'No salt ticks on this day' with yesterday's list named", s == 200 and "No salt ticks on this day" in h
   and ("Last list from Marg %s 11:20" % YDAY.strftime("%d-%m")) in h, h[h.find("Salt list from Marg"):][:300])
ck("owner page: the collapsed block 'Amir's visit -- what was done' is there, closed",
   "<details class=visit><summary>Amir's visit &mdash; what was done</summary>" in h and "<details class=visit open" not in h)
s, j = api(API + "?date=" + TODAY, DOC)
ck("API (checker): ok, 7 verdicts, salt_list not pending, nothing fresh", s == 200 and j.get("ok") and len(j.get("steps") or []) == 7
   and j["salt_list"]["pending"] is False and j["salt_list"]["fresh"] is False, j.get("salt_list"))
ck("API: step 4 already 'done' from the arrived pair; step 3 'done' by arrival without the tap; step 1 'not yet'",
   [x["state"] for x in j["steps"]][:4] == ["not yet", "not yet", "done", "done"] and "the tap itself was not made" in j["steps"][2]["note"], j["steps"][:4])
ck("API: reports = BILLWISE 2 rows Rs 12,345 + ITEMWISE 9 rows", j["reports"]["bills"] == 2 and j["reports"]["amount_p"] == 1234500
   and j["reports"]["amount"] == "12,345" and [x["type"] for x in j["reports"]["rows"]] == ["BILLWISE", "ITEMWISE"], j["reports"])
ck("EXPORT-STAMP FIX: the pair with Marg's YYYYMMDD-HHMMSS stamps is verified as today's (the live S241 code could not)",
   all(e["have"] for e in AD._work(dbx(), TODAY)["exports"]) and j["reports"]["rows"][0]["at"] == T_BW.strftime("%H:%M"), (j["steps"][3], j["reports"]["rows"]))
ck("EXPORT-STAMP FIX: today's bills are today's, not 'pichhla baaki'",
   len(AD._work(dbx(), TODAY)["today_bills"]) == 2 and len(AD._work(dbx(), TODAY)["carry_bills"]) == 0)
_x = dbx()
_x.execute("UPDATE purchase_export SET export_stamp=? WHERE type='ITEMWISE'", (T_BW.strftime("%Y-%m-%d %H:%M:%S"),))
_x.commit()
ck("EXPORT-STAMP FIX: the S241 fixture shape (yyyy-mm-dd hh:mm:ss) is still read", all(e["have"] for e in AD._work(_x, TODAY)["exports"]))
_x.execute("UPDATE purchase_export SET export_stamp=? WHERE type='ITEMWISE'", (stamp14(T_BW + dt.timedelta(minutes=2)),))
_x.commit(); _x.close()
s, h, _r = page("/finance/amir/step/4", AMIR)
ck("Amir step 4 shows both reports verified with a readable time, not the raw stamp",
   s == 200 and h.count("&#10003;") == 2 and ("%s baje" % T_BW.strftime("%H:%M")) in h and stamp14(T_BW) not in h, h[h.find("Server ne"):][:400])
ck("API: bills step 5 'not yet -- 2 to tap'", j["steps"][4]["state"] == "not yet" and "2 to tap" in j["steps"][4]["note"], j["steps"][4])
ck("API: step 7 open with the plain-words list", j["steps"][6]["state"] == "open" and "bills not confirmed entered" in j["steps"][6]["note"])
ck("API is JSON-safe (round-trips)", json.loads(json.dumps(j))["ok"] is True)

# ---- 2 he ticks salt tasks (his sheet page writes purchase_salt_task) -> RED ------------
x = dbx()
t1 = NOW.strftime("%Y-%m-%d %H:%M:%S")
x.execute("UPDATE purchase_salt_task SET done=1, done_by='zzamir', done_at=? WHERE id IN (1,2)", (t1,))
x.execute("UPDATE purchase_salt_task SET done=1, done_by='zzamir', done_at=? WHERE id=3", (NOW.isoformat(),))   # the old page's ISO 'T' form
x.commit(); x.close()
s, h, _r = page("/finance/amir/step/6", AMIR)
ck("Amir step 6: the RED line, Hinglish, with yesterday's list time", s == 200 and RED in h and "big bad" in h
   and "3 kaam tick hue" in h and ("aakhri list %s 11:20 ki thi" % YDAY.strftime("%d-%m")) in h, h[h.find(RED) - 60:][:400])
ck("Amir step 6: the tick button is still there -- the prompt does not replace the step", "Aaj ke item theek kar diye" in h)
s, h, _r = page("/finance/amir/day", DOC)
ck("owner page: AMBER 'Waiting for Marg's SALT WISE ITEM LIST -- 3 salt tasks ticked since the last list'",
   AMBER_H in h and "3 salt tasks ticked since the last list" in h and "big warn" in h, h[h.find("Salt list from Marg"):][:300])
s, j = api(API + "?date=" + TODAY, DOC)
ck("API: pending true, since_list 3, ticks_day 3, by zzamir; salts.ticked 3 (renames 2, new 1)",
   j["salt_list"]["pending"] is True and j["salt_list"]["since_list"] == 3 and j["salt_list"]["ticks_day"] == 3
   and j["salt_list"]["ticked_by"] == ["zzamir"] and j["salts"]["ticked"] == 3 and j["salts"]["renames"] == 2
   and j["salts"]["by_section"].get("create") == 1, (j["salt_list"], j["salts"]))
ck("API: salt_list.owner_line/css carry the amber", j["salt_list"]["css"] == "warn" and AMBER in j["salt_list"]["owner_line"])
ck("API: step 6 still 'not yet' -- the salt TAP is his, the ticks are the tasks", j["steps"][5]["state"] == "not yet")

# ---- 3 he taps step 6 -> step 7 shows the prompt; the day's state ignores it ------------
r = c.post("/finance/amir/step/6", headers=AMIR, data={"tick": "6", "go": "6"})
ck("POST tick 6 -> 303 onward", r.status_code == 303, r.status_code)
s, h, _r = page("/finance/amir/step/7", AMIR)
ck("Amir step 7 (still baaki): 200", s == 200)
x = dbx()
w = AD._work(x, TODAY)
ck("done[6] is true from the tap alone; the prompt is pending; _left() does not name the list",
   w["done"][6] is True and w["salt_list"]["pending"] is True and not any("SALT" in i for i in AD._left(w)), (w["done"], AD._left(w)))
x.close()
s, j = api(API + "?date=" + TODAY, DOC)
ck("API: step 6 'done HH:MM by zzamir; 3 tasks ticked'", j["steps"][5]["state"] == "done" and "by zzamir" in j["steps"][5]["note"]
   and "3 tasks ticked" in j["steps"][5]["note"], j["steps"][5])

# ---- 4 the rest of his day, then close -- with the prompt STILL pending -------------------
for n in (1, 2, 3):
    c.post("/finance/amir/step/%d" % n, headers=AMIR, data={"tick": str(n), "go": str(n)})
s, h, _r = page("/finance/amir/step/5", AMIR)
ck("step 5 lists the two bills from the bill-wise export", s == 200 and "WALK SUPPLIER ONE" in h and "B-TWO" in h and "name='k_1'" in h)
keys = re.findall(r"name='k_(\d)' value='([^']+)'", h)
form = {"n": "2", "go": "5"}
for i, key in keys:
    form["k_%s" % i] = key
    form["r_%s" % i] = "short" if key.startswith("walk supplier one") else "ok"
r = c.post("/finance/amir/step/5", headers=AMIR, data=form)
ck("POST step 5 with one 'short' and one 'ok' -> onward", r.status_code == 303)
s, h, _r = page("/finance/amir/step/7", AMIR)
ck("step 7 'Din band karein?' with the RED prompt on the close screen", s == 200 and "Din band karein?" in h and RED in h, h[:200])
r = c.post("/finance/amir/step/7", headers=AMIR, data={"go": "7"})
s, h, _r = page("/finance/amir/step/7", AMIR)
ck("the day CLOSES with the list still awaited -- a prompt, not a gate", "DIN BAND" in h and RED in h, h[:300])
s, j = api(API + "?date=" + TODAY, DOC)
ck("API: CLOSED, all seven verdicts 'done', salt list still pending",
   j["state"] == "CLOSED" and all(x["state"] == "done" for x in j["steps"]) and j["salt_list"]["pending"] is True,
   [(x["n"], x["state"]) for x in j["steps"]])
ck("API: bills tapped 2 (Kam maal aaya 1, Theek hai 1); one claim raised worth Rs 7,000",
   j["bills"]["tapped"] == 2 and j["bills"]["by_reason"]["short"]["n"] == 1 and j["bills"]["by_reason"]["ok"]["n"] == 1
   and j["claims"]["n"] == 1 and j["claims"]["amount_p"] == 700000 and j["claims"]["amount"] == "7,000", (j["bills"], j["claims"]))
ck("API: bills line and reports line are readable", "Kam maal aaya 1" in j["bills"]["line"] and "BILLWISE 2 rows Rs 12,345" in j["reports"]["line"])
s, h, _r = page("/finance/amir/day", DOC)
ck("owner page CLOSED: state line, amber list, and the details block lists 'Claims raised for Darpan: <b>1</b>'",
   "CLOSED at" in h and AMBER_H in h and "Claims raised for Darpan: <b>1</b>" in h and "Bills tapped: <b>2</b>" in h, h[-1500:])

# ---- 5 the list arrives (the door rows mi_file) -> GREEN ---------------------------------
T_LIST = NOW + dt.timedelta(minutes=3)
x = dbx()
x.execute("INSERT INTO mi_file (md5, drive_name, stamp, type, verdict, kept, received_at) VALUES "
          "('sw0000000000000000000000000000s2','SALT_WISE_ITEM_LIST.XLS',?,'SALT_WISE_ITEM_LIST','VERIFIED',1,?)",
          (stamp14(T_LIST), T_LIST.isoformat()))
x.commit(); x.close()
s, h, _r = page("/finance/amir/step/7", AMIR)
ck("Amir close screen: GREEN 'SALT WISE ITEM LIST aa gayi' with the arrival time, red gone",
   GREEN in h and T_LIST.strftime("%d-%m %H:%M") in h and RED not in h, h[h.find("Aaj ka kaam"):][:600])
s, h, _r = page("/finance/amir/step/6", AMIR)
ck("Amir step 6: GREEN too", GREEN in h and RED not in h)
s, h, _r = page("/finance/amir/day", DOC)
ck("owner page: green 'Salt list arrived HH:MM, after the day's 3 ticks'", _html.escape("Salt list arrived %s, after the day's 3 ticks" % T_LIST.strftime("%d-%m %H:%M")) in h
   and "big good" in h and AMBER_H not in h, h[h.find("Salt list from Marg"):][:300])
s, j = api(API + "?date=" + TODAY, DOC)
ck("API: fresh true, pending false, last_list = the new stamp", j["salt_list"]["fresh"] is True and j["salt_list"]["pending"] is False
   and j["salt_list"]["last_list"] == T_LIST.strftime("%Y-%m-%d %H:%M:%S") and j["salt_list"]["css"] == "good", j["salt_list"])

# ---- 6 a later tick makes it pending again; the ISO-with-zone received_at is read when stamp is blank ---
x = dbx()
x.execute("UPDATE purchase_salt_task SET done=1, done_by='zzamir', done_at=? WHERE id=4", ((T_LIST + dt.timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S"),))
x.commit(); x.close()
s, j = api(API + "?date=" + TODAY, DOC)
ck("a tick AFTER the list -> pending again, since_list 1", j["salt_list"]["pending"] is True and j["salt_list"]["since_list"] == 1, j["salt_list"])
x = dbx()
x.execute("INSERT INTO mi_file (md5, drive_name, stamp, type, verdict, kept, received_at) VALUES "
          "('sw0000000000000000000000000000s3','SALT_WISE_ITEM_LIST.XLS','','SALT_WISE_ITEM_LIST','VERIFIED',1,?)",
          ((T_LIST + dt.timedelta(minutes=9)).isoformat(),))
x.commit(); x.close()
s, j = api(API + "?date=" + TODAY, DOC)
ck("a row with a blank stamp is read by its received_at (ISO with zone) -> fresh", j["salt_list"]["fresh"] is True
   and j["salt_list"]["last_list"] == (T_LIST + dt.timedelta(minutes=9)).strftime("%Y-%m-%d %H:%M:%S"), j["salt_list"])

# ---- 7 salts_refresh's state file adds the 'applied' detail --------------------------------
json.dump({"ok": True, "applied_at": (T_LIST + dt.timedelta(minutes=10)).replace(tzinfo=None).isoformat(),
           "file": "SALT_WISE_ITEM_LIST_DEFAULT__%s__%s__deadbeef.XLS" % (TODAY, stamp14(T_LIST)), "as_on": TODAY, "rows": 812},
          open(STATE, "w"))
s, j = api(API + "?date=" + TODAY, DOC)
ck("state file read: applied_at, applied_as_on, applied_stamp from the archived name", j["salt_list"]["applied_at"] == (T_LIST + dt.timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
   and j["salt_list"]["applied_as_on"] == TODAY and j["salt_list"]["applied_stamp"] == T_LIST.strftime("%Y-%m-%d %H:%M:%S"), j["salt_list"])
s, h, _r = page("/finance/amir/day", DOC)
ck("owner page: 'Salts page refreshed HH:MM from the list of <today>'", "Salts page refreshed %s from the list of %s" % ((T_LIST + dt.timedelta(minutes=10)).strftime("%d-%m %H:%M"), TODAY) in h)
open(STATE, "w").write("{not json")
s, j = api(API + "?date=" + TODAY, DOC)
ck("a broken state file is ignored, the API still answers", s == 200 and j["ok"] and j["salt_list"]["applied_at"] is None)
os.remove(STATE)

# ---- 8 who may read what ---------------------------------------------------------------
s, j = api(API, AMIR)
ck("API refused to Amir (maker) -- 403 JSON", s == 403 and j.get("error") == "not_permitted", (s, j))
s, j = api(API, VIEW)
ck("API refused to a viewer -- 403", s == 403)
r = c.get(API)
ck("API anonymous -> the portal (302)", r.status_code == 302 and "/portal" in (r.headers.get("Location") or ""), (r.status_code, r.headers.get("Location")))
r = c.get(API, headers=CLIN)
ck("API for a login with no medical role -> the portal (302)", r.status_code == 302)
s, j = api(API + "?date=13-09-2026", DOC)
ck("a malformed date is refused 400", s == 400 and j.get("error") == "bad_date")
r = c.get("/finance/amir/day")
ck("anonymous /finance/amir/day -> the portal", r.status_code == 302 and "/portal" in (r.headers.get("Location") or ""))
r = c.get("/finance/amir/step/6")
ck("anonymous step 6 -> the portal", r.status_code == 302)
s, h, _r = page("/finance/amir/day", AMIR)
ck("Amir may still open the English day page (as before S243)", s == 200)
s, h, _r = page("/finance/amir/salts", AMIR)
ck("his salts sheet page still opens 200 (amir_salts untouched)", s == 200 and "Salt ka kaam" in h)

# ---- 9 a past day with nothing -----------------------------------------------------------
OLD = "2026-01-05"
s, j = api(API + "?date=" + OLD, DOC)
ck("an empty past day: ok, OPEN, bills 'not needed', check 'not done', no exception", s == 200 and j["ok"] and j["state"] == "OPEN"
   and j["steps"][4]["state"] == "not needed" and j["steps"][3]["state"] == "not done" and j["bills"]["tapped"] == 0
   and j["reports"]["line"] == "none received" and j["salt_list"]["pending"] is False, j.get("steps"))
s, h, _r = page("/finance/amir/day?d=" + OLD, DOC)
ck("owner page for that day: 200 with the details block", s == 200 and "Amir's visit &mdash; what was done" in h)
ck("a past day is judged by its own ticks: today's ticks do not make 05-Jan pending", j["salt_list"]["ticks_day"] == 0 and j["salt_list"]["last_tick"] is None)

# ---- 10 without the tables (a box before marg_ingest / purchase_app ran) ------------------
bare = sqlite3.connect(":memory:")
bare.row_factory = sqlite3.Row
AD._ensure(bare)
st = AD._salt_list_state(bare, TODAY)
ck("no purchase_salt_task, no mi_file: quiet state, nothing pending", st["pending"] is False and st["fresh"] is False and st["last_list"] is None)
bare.execute("CREATE TABLE purchase_salt_task (id INTEGER PRIMARY KEY, section TEXT, seq INTEGER, a TEXT, b TEXT, c TEXT, done INTEGER, done_by TEXT, done_at TEXT)")
bare.execute("INSERT INTO purchase_salt_task VALUES (1,'rename',1,'A','B',NULL,1,'zzamir',?)", (t1,))
st = AD._salt_list_state(bare, TODAY)
ck("ticks but no mi_file table at all: pending, 'no list seen yet'", st["pending"] is True and st["last_list"] is None
   and "no list seen yet" in AD._salt_owner_line(st)[1])
ck("_norm_ts reads all three writers' shapes", AD._norm_ts("20260913-081200") == "2026-09-13 08:12:00"
   and AD._norm_ts("2026-09-13T08:12:00+05:30") == "2026-09-13 08:12:00" and AD._norm_ts("2026-09-13 08:12:00") == "2026-09-13 08:12:00"
   and AD._norm_ts("") is None)
bare.close()

# ---- 11 the hub ---------------------------------------------------------------------------
s, h, _r = page("/finance/approvals", DOC)
ck("hub /finance/approvals: 200 (real page; hub patch state %s)" % " ".join(HUB_ST), s == 200 and all(x.endswith(("patched", "already")) for x in HUB_ST))
ck("hub: the collapsed block sits in the Marg card, with its loader and its call",
   'id="amirVisitBox"' in h and "Amir's visit — what was done" in h and "function loadAmirVisit()" in h and "loadAmirVisit(); loadHomeMed();" in h)
ck("hub: the block is a closed <details> (collapsed by default)", '<details class="help" id="amirVisitBox"><summary' in h and 'id="amirVisitBox" open' not in h)
ck("hub: the loader fetches THIS kit's API", 'fetch("/finance/amir/day/api/visit-summary?_="' in h)
ck("hub: DARPAN_KAL's card and the S243 auto-apply wording are both still there",
   ('id="kalCard"' in h and "function loadKal()" in h) and '"applied automatically "' in h)
ck("hub: the Marg card's own help survives once", h.count("Export from Marg as <b>Bill wise sales statement</b>") == 1)
r = c.get("/finance/approvals", headers=AMIR)
ck("hub refused to Amir (302 to the portal, as before)", r.status_code == 302)

# ---- 12 no numbers, no secrets in what this kit renders -------------------------------------
s, h, _r = page("/finance/amir/day", DOC)
ck("owner page carries no 10-digit number", not re.search(r"(?<!\d)\d{10}(?!\d)", h))
s, h, _r = page("/finance/amir/step/7", AMIR)
ck("Amir's close screen carries no 10-digit number", not re.search(r"(?<!\d)\d{10}(?!\d)", h))

print("")
print("walk: %d passed, %d failed" % (len(PASSED), len(FAILED)))
for f in FAILED:
    print("  FAILED: %s" % f)
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(0 if not FAILED else 1)
