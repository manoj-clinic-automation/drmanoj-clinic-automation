#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s654.py -- kit S654_SLIP_TOOLS's walk on a MADE-UP slip book (D789). Nothing real is read or written.

  python3 walk_s654.py <dir holding the slip_log.py + parchi_desk.py under test> [--old]

Mounts the two files on a throw-away Flask app over a temp database (made-up patients and services), pins the clock to
25-Oct-2026 12:00, and walks: the previous book kept on a book change; a late entry with the old book's number; the desk's
No. and Hatao doors (a reason, the book's ranges, a used number, a skipped number taken over, a slip too old, one's own
same-day entry); the old pages unchanged. --old: the control on the live files -- every S654 check red, every older green."""
import importlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile

OLD = "--old" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]
if len(args) != 1:
    sys.exit(__doc__)
SRC = os.path.abspath(args[0])
TMP = tempfile.mkdtemp(prefix="s654walk.")
for f in ("slip_log.py", "parchi_desk.py"):
    shutil.copy(os.path.join(SRC, f), os.path.join(TMP, f))
DB = os.path.join(TMP, "f.db")
os.environ["SLIP_NOW"] = "2026-10-25 12:00:00"
con0 = sqlite3.connect(DB)
con0.executescript("""
CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT, phone_last4 TEXT, merged_into TEXT);
INSERT INTO patient_ref(clinic_id, name, phone_last4) VALUES ('9001','Asha Test','0001'),('9002','Bina Test','0002'),('9003','Chetan Test','0003');
CREATE TABLE clinic_day_line (business_date TEXT, section TEXT, sn INTEGER, patient TEXT, clinic_id TEXT, amount_p INTEGER, mode TEXT, shift TEXT, gateway_ref TEXT);
CREATE TABLE owner_service (id INTEGER PRIMARY KEY, kind TEXT, name TEXT, price_p INTEGER, active INTEGER DEFAULT 1, note TEXT, created_by TEXT, created_ts TEXT, updated_by TEXT, updated_ts TEXT, code TEXT, status TEXT DEFAULT 'approved', seen INTEGER, grp TEXT, forms TEXT, source TEXT, side TEXT);
INSERT INTO owner_service(id, kind, name, price_p, side) VALUES (1,'xray','Knee AP & Lateral view',50000,'ask'),(2,'xray','Lumbosacral spine AP & Lateral view',50000,''),(61,'proc','ILI KNEE',50000,'');
CREATE TABLE audit_log (id INTEGER PRIMARY KEY, table_name TEXT, row_id INTEGER, action TEXT, before_json TEXT, after_json TEXT, by_whom TEXT, at TEXT);
""")
con0.commit()
con0.close()

sys.path.insert(0, TMP)
from flask import Flask                                                 # noqa: E402

SL = importlib.import_module("slip_log")
USER = {"user": "shavez", "role": "manager", "roles": ["maker", "checker"]}


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def require(*roles, unit="slips"):
    return dict(USER), None


def audit(con, table, row_id, action, before=None, after=None, who=""):
    con.execute("INSERT INTO audit_log(table_name,row_id,action,before_json,after_json,by_whom,at) VALUES(?,?,?,?,?,?,?)",
                (table, row_id, action, json.dumps(before), json.dumps(after), who, "x"))


app = Flask("walk")
app.testing = True
SL.init(app, db, require, audit, unit="slips")
c = app.test_client()
RES = []


def check(tag, name, ok, detail=""):
    RES.append((tag, name, bool(ok)))
    print("%s  [%s] %s%s" % ("GREEN" if ok else "RED  ", tag, name, ("  -- " + str(detail)[:200]) if (detail and not ok) else ""))


def q(sql, *a):
    k = db()
    try:
        return [dict(r) for r in k.execute(sql, a)]
    finally:
        k.close()


def j(path, body):
    r = c.post(path, data=json.dumps(body), content_type="application/json")
    try:
        return r.status_code, json.loads(r.get_data(as_text=True) or "{}")
    except ValueError:
        return r.status_code, {}


T = "S654"
k = db()
SL.ensure(k)
k.close()
# ---- older behaviour
r = c.get("/finance/slips?s=xp")
check("older", "the X-ray page opens", r.status_code == 200, r.status_code)
r = c.get("/finance/slips/desk")
check("older", "the parchi desk opens", r.status_code == 200, r.status_code)
r = c.post("/finance/slips/book", data={"series": "xp", "first_no": "1401", "last_no": "1800", "start_no": "1401"})
check("older", "a new X-ray book 1401-1800 is set", r.status_code in (302, 303) and
      q("SELECT first_no, last_no FROM slip_book WHERE series='xp'")[0] == {"first_no": 1401, "last_no": 1800})
bk = q("SELECT * FROM slip_book WHERE series='xp'")[0]
check(T, "the book remembers the previous range 1001-1400 after the change",
      bk.get("prev_first_no") == 1001 and bk.get("prev_last_no") == 1400, str(bk))
# a saved slip in the current book, a saved slip with the OLD book's number for a late day
r = c.post("/finance/slips/desk/api/save", data=json.dumps({"series": "xp", "slip_no": 1401, "clinic_id": "9001", "day": "2026-10-24",
                                                            "items": [{"k": "xray", "id": 2}]}), content_type="application/json")
d = json.loads(r.get_data(as_text=True))
check("older", "a slip of the current book saves for a late day (1401, 24-Oct)", d.get("ok") is True, d)
st, d = j("/finance/slips/desk/api/save", {"series": "xp", "slip_no": 1397, "clinic_id": "9002", "day": "2026-10-24", "items": [{"k": "xray", "id": 1, "side": "R"}]})
check(T, "a late entry with the PREVIOUS book's number (1397 for 24-Oct) is accepted", d.get("ok") is True, d)
st, d = j("/finance/slips/desk/api/save", {"series": "xp", "slip_no": 999, "clinic_id": "9003", "day": "2026-10-24", "items": [{"k": "xray", "id": 1}]})
check(T, "a number of neither book (999) is refused, and the message names both ranges",
      d.get("ok") is False and "1401–1800" in (d.get("err") or "") and "1001–1400" in (d.get("err") or ""), d)
check("older", "the next number is unchanged by the old-book entry (1402)", q("SELECT 1")[0] and SL.next_no(db(), "xp") == 1402)
# today's slips: 1402 saved; renumber it
st, d = j("/finance/slips/desk/api/save", {"series": "xp", "slip_no": 1402, "clinic_id": "9003", "day": "", "items": [{"k": "proc", "id": 61}]})
sid1402 = d.get("id")
check("older", "today's slip 1402 saves", d.get("ok") is True and sid1402, d)
st, d = j("/finance/slips/desk/api/renumber", {"id": sid1402, "day": "", "no": "1403", "why": ""})
check(T, "No. without a reason is refused", st == 200 and d.get("ok") is False and "wajah" in (d.get("err") or ""), (st, d))
st, d = j("/finance/slips/desk/api/renumber", {"id": sid1402, "day": "", "no": "1401", "why": "galat number"})
check(T, "No. to a number another saved slip holds (1401) is refused", d.get("ok") is False and "pehle se likhi" in (d.get("err") or ""), d)
st, d = j("/finance/slips/desk/api/renumber", {"id": sid1402, "day": "", "no": "2500", "why": "galat number"})
check(T, "No. to a number of neither book (2500) is refused", d.get("ok") is False and "book" in (d.get("err") or ""), d)
st, d = j("/finance/slips/desk/api/renumber", {"id": sid1402, "day": "", "no": "1403", "why": "kagaz par 1403 tha"})
row = q("SELECT slip_no, note FROM slip WHERE id=?", sid1402)[0]
check(T, "No. 1402 -> 1403 with a reason: the slip keeps its items, the old number is noted, Saved words come back",
      d.get("ok") is True and row["slip_no"] == 1403 and "tha 1402" in row["note"] and "1402 ab 1403" in d.get("msg", "")
      and q("SELECT COUNT(*) c FROM slip_item WHERE slip_id=?", sid1402)[0]["c"] == 1, (d, row))
check(T, "the desk's state after it shows 1403, not 1402",
      [x["no"] for x in d.get("state", {}).get("xp", [])] == [1403], str([x["no"] for x in d.get("state", {}).get("xp", [])]))
# a skipped number is taken over
st, d = j("/finance/slips/desk/api/save", {"series": "xp", "slip_no": 1406, "clinic_id": "9001", "day": "", "items": [{"k": "xray", "id": 2}]})
sid1406 = d.get("id")
miss = sorted(x["slip_no"] for x in q("SELECT slip_no FROM slip WHERE series='xp' AND state='missing'"))
check("older", "saving 1406 marks 1404 and 1405 as skipped", d.get("ok") is True and {1404, 1405} <= set(miss), miss)
st, d = j("/finance/slips/desk/api/renumber", {"id": sid1406, "day": "", "no": "1404", "why": "kagaz par 1404"})
miss = sorted(x["slip_no"] for x in q("SELECT slip_no FROM slip WHERE series='xp' AND state='missing'"))
check(T, "No. 1406 -> 1404 takes over the skipped 1404 (only 1405 stays skipped); 1406 is free, so the next number is 1406",
      d.get("ok") is True and miss == [1405] and q("SELECT slip_no FROM slip WHERE id=?", sid1406)[0]["slip_no"] == 1404
      and SL.next_no(db(), "xp") == 1406, (d.get("err"), miss, SL.next_no(db(), "xp")))
# Hatao -- 1397 was typed by someone else yesterday (one's own same-day entry needs no reason; this one does)
k = db()
if not q("SELECT id FROM slip WHERE series='xp' AND slip_no=1397 AND state='ok'"):     # the control refused 1397: plant it
    k.execute("INSERT INTO slip(series, slip_no, day, clinic_id, state, logged_by, logged_at, updated_by, updated_at) "
              "VALUES ('xp', 1397, '2026-10-24', '9002', 'ok', 'alisha', '2026-10-24 19:00:00', 'alisha', '2026-10-24 19:00:00')")
    k.commit()
sid1397 = q("SELECT id FROM slip WHERE series='xp' AND slip_no=1397 AND state='ok'")[0]["id"]
k.execute("UPDATE slip SET logged_by='alisha', logged_at='2026-10-24 19:00:00' WHERE id=?", (sid1397,))
k.commit()
k.close()
st, d = j("/finance/slips/desk/api/void", {"id": sid1397, "day": "2026-10-24", "why": ""})
check(T, "Hatao on a past day's slip without a reason is refused", d.get("ok") is False and "wajah" in (d.get("err") or ""), d)
st, d = j("/finance/slips/desk/api/void", {"id": sid1397, "day": "2026-10-24", "why": "galat mareez"})
check(T, "Hatao with a reason: 24-Oct's 1397 is off, its number free again, the reason kept",
      d.get("ok") is True and q("SELECT state, note FROM slip WHERE id=?", sid1397)[0] == {"state": "void", "note": "galat mareez"}
      and SL._live(db(), "xp", 1397) is None, d)
st, d = j("/finance/slips/desk/api/void", {"id": sid1406, "day": "", "why": ""})
check(T, "Hatao on one's own same-day entry needs no reason", d.get("ok") is True
      and q("SELECT state FROM slip WHERE id=?", sid1406)[0]["state"] == "void", d)
# too old
k = db()
k.execute("INSERT INTO slip(series, slip_no, day, clinic_id, state, logged_by, logged_at, updated_by, updated_at) "
          "VALUES ('xp', 1390, '2026-10-10', '9001', 'ok', 'shavez', '2026-10-10 10:00:00', 'shavez', '2026-10-10 10:00:00')")
k.commit()
old_id = k.execute("SELECT id FROM slip WHERE slip_no=1390").fetchone()[0]
k.close()
st, d = j("/finance/slips/desk/api/void", {"id": old_id, "day": "2026-10-24", "why": "x"})
st2, d2 = j("/finance/slips/desk/api/renumber", {"id": old_id, "day": "2026-10-24", "no": "1391", "why": "x"})
check(T, "a slip older than 7 days (10-Oct) can be neither removed nor renumbered",
      d.get("ok") is False and d2.get("ok") is False and "purani" in (d.get("err") or "") and "purani" in (d2.get("err") or ""), (d, d2))
# a renumber refused on a void slip
st, d = j("/finance/slips/desk/api/renumber", {"id": sid1397, "day": "2026-10-24", "no": "1398", "why": "x"})
check(T, "a removed slip cannot be renumbered", d.get("ok") is False, d)
# audit
acts = [x["action"] for x in q("SELECT action FROM audit_log WHERE action IN ('slip_renumber','slip_void') ORDER BY id")]
check(T, "every change is in the audit: 2 renumbers, 2 removals", acts.count("slip_renumber") == 2 and acts.count("slip_void") == 2, acts)
# the page
r = c.get("/finance/slips/desk")
html = r.get_data(as_text=True)
check(T, "the desk page carries the No. and Hatao buttons and their inline form",
      r.status_code == 200 and "data-fx=\"renum\"" in html and "/finance/slips/desk/api/renumber" in html and "fxf" in html)
r = c.get("/finance/slips?s=xp")
check("older", "the X-ray page still opens after the changes", r.status_code == 200, r.status_code)
r = c.get("/finance/slips/report/2026-10-24")
check("older", "the day report still opens", r.status_code == 200, r.status_code)

shutil.rmtree(TMP, ignore_errors=True)
s = [x for x in RES if x[0] == T]
o = [x for x in RES if x[0] != T]
if OLD:
    print("%d S654 check(s) red · %d older red · %d green" % (sum(1 for x in s if not x[2]), sum(1 for x in o if not x[2]),
                                                                      sum(1 for x in RES if x[2])))
else:
    print("%d of %d green" % (sum(1 for x in RES if x[2]), len(RES)))
