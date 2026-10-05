#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s487.py -- S487_AAJ_KA_KAAM: the walk. LIVE-SHAPE and WRITES NOTHING LIVE.

It works in a private scratch folder: the box's own finance modules are COPIED there (never imported from /root/finance,
never written), the two edited files are made by apply_s487.py on copies, and finance.db is copied with SQLite's backup
through a read-only door. Everything below runs on those copies and on made-up files (punches, a staff master, an asset
database, a register lock, a freshness file, a heartbeat) the walk writes itself.

  A  the files: the edits apply, compile, and say what the kit says; the portal's tile renders for the doctor only
  B  the builder on the copy: exit 0, one file, mode 600, nothing left behind, AND THE DATABASE IT READ IS BYTE-IDENTICAL
  C  every figure against its owner: the walk asks the owning module itself (a second process, a second copy) and compares
  D  made-up rows are put in the copy and the reading must move by exactly that: a slip discount to approve, a pharmacy day
     to approve, the follow-up export, the counter sheet, a petty entry; a made-up patient name is put where the owners keep
     names and must NOT appear in any reading
  E  the service's part through Flask's own test client: the owner only, the first reading made in the background, one
     builder at a time, a dead lock replaced, a failed build said plainly while the older reading stands
  F  THE STAFF'S LISTS (S487): the floor (nothing before 01-Sep counted) proven against a copy with the old rows DELETED; who
     sees which queue; off for staff until the owner's tap; a tap is the person's own, once, and the first stands; a weekly or
     monthly line begins with the first week / month after the switch; the console's staff lines are the list's own lines
Last line: WALK_S487 GREEN|RED <n> checks, <f> fail
   usage: walk_s487.py --kit <dir> --finance <dir> --portal <portal.py> --db <finance.db> --attcore <att_core.py>
                       [--dutymap <DUTY_MAP.json>] [--allow-unread N] [--full-app] [--keep]
"""
import ast
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
CHECKS, FAILS, NOTES = [], [], []
SENT = "ZZQQPATIENT"
NB = "‑"


def check(name, cond, detail=""):
    CHECKS.append(name)
    if cond and os.environ.get("WALK_VERBOSE"):
        print("  ok   %s" % name[:150])
    if not cond:
        FAILS.append(name)
        print("  FAIL %s%s" % (name, (" -- " + str(detail)[:300]) if detail else ""))
    return bool(cond)


def note(text):
    NOTES.append(text)
    print("  note %s" % text)


def arg(name, default=None):
    a = sys.argv
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default


def md5f(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def listing(d):
    out = {}
    for root, _dirs, files in os.walk(d):
        for f in files:
            p = os.path.join(root, f)
            st = os.stat(p)
            out[os.path.relpath(p, d)] = (st.st_size, st.st_mtime_ns)
    return out


def copy_code(src, dst):
    """The finance app's code and small data files, two levels deep -- no database, no backup, no upload."""
    keep = (".py", ".html", ".json", ".sql", ".js", ".css", ".txt", ".md", ".csv")
    os.makedirs(dst, exist_ok=True)
    n = 0
    for name in sorted(os.listdir(src)):
        p = os.path.join(src, name)
        if os.path.isfile(p):
            if name.endswith(keep) and ".bak" not in name and not name.startswith(".") and not name.startswith("console_") \
                    and os.path.getsize(p) < 6_000_000:
                shutil.copy2(p, os.path.join(dst, name))
                n += 1
        elif os.path.isdir(p) and not name.startswith((".", "__")):
            try:
                inner = [f for f in os.listdir(p) if f.endswith(".py")]
            except OSError:
                inner = []
            if inner:
                os.makedirs(os.path.join(dst, name), exist_ok=True)
                for f in os.listdir(p):
                    q = os.path.join(p, f)
                    if os.path.isfile(q) and f.endswith(keep) and ".bak" not in f and os.path.getsize(q) < 6_000_000:
                        shutil.copy2(q, os.path.join(dst, name, f))
                        n += 1
    return n


def backup(src, dst):
    a = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    try:
        b = sqlite3.connect(dst)
        try:
            a.backup(b)
        finally:
            b.close()
    finally:
        a.close()


def clone_row(con, table, where, args, changes, drop=("id",)):
    """Insert a made-up row shaped exactly like a real one: one real row is read, the named columns are changed."""
    con.row_factory = sqlite3.Row
    r = con.execute("SELECT * FROM %s WHERE %s LIMIT 1" % (table, where), args).fetchone()
    if r is None:
        r = con.execute("SELECT * FROM %s LIMIT 1" % table).fetchone()
    info = con.execute("PRAGMA table_info(%s)" % table).fetchall()
    if r is None:                                                      # an empty table: the row is shaped on the table itself
        d = {x[1]: (None if not x[3] else (0 if "INT" in str(x[2]).upper() else "")) for x in info}
    else:
        d = dict(r)
    pk = [x[1] for x in info if x[5] and str(x[2]).upper() == "INTEGER"]
    for k in drop:
        if k in d and k in pk:
            d.pop(k)
    d.update(changes)
    cols = list(d)
    cur = con.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ",".join(cols), ",".join("?" * len(cols))), [d[c] for c in cols])
    return cur.lastrowid


def lines_of(snap, key):
    return (snap.get("sections") or {}).get(key, {}).get("lines") or []


def find(snap, key, needle):
    return [l for l in lines_of(snap, key) if needle in (l.get("b", "") + l.get("text", ""))]


def flat(snap):
    return json.dumps(snap, ensure_ascii=False)


# ------------------------------------------------------------------ the oracle: the owners, asked directly, in their own process
ORACLE = r'''
import datetime as dt, json, os, re, sqlite3, sys
sys.dont_write_bytecode = True
fin, db, dutymap = sys.argv[1], sys.argv[2], sys.argv[3]
os.environ["FINANCE_DB"] = db
os.environ["DUTY_MAP_JSON"] = dutymap
sys.path.insert(0, fin); os.chdir(fin)
con = sqlite3.connect(db, timeout=30); con.row_factory = sqlite3.Row
today = dt.date.today(); yday = today - dt.timedelta(days=1); lwd = yday
while lwd.weekday() == 6: lwd -= dt.timedelta(days=1)
def has(sql, d): return con.execute(sql, (d.isoformat(),)).fetchone() is not None
D = yday if (yday.weekday() != 6 or has("SELECT 1 FROM clinic_day_revenue WHERE business_date=?", yday)) else lwd
S = yday if (yday.weekday() != 6 or has("SELECT 1 FROM day_entry WHERE unit='medical' AND business_date=?", yday)) else lwd
D, S, L = D.isoformat(), S.isoformat(), lwd.isoformat()
out = dict(D=D, S=S, lwd=L, today=today.isoformat())
import clinic_money, clinic_register, sanjeevni_cash, darpan_kal, slip_log, slip_adjust, records, packs
m = clinic_money.match_day(con, D)
out["match"] = dict(verdict=m.get("verdict"), flags=[[f.get("code"), f.get("amount_p"), bool(f.get("owner"))] for f in m.get("flags") or []],
                    p1=m.get("p1"), doc_known=bool(m.get("doc_known")), filled=bool(m.get("filled")))
rows = (sanjeevni_cash.days(con, S, S, "medical") or {}).get("rows") or []
out["sanj"] = dict(sale_p=rows[0].get("sale_p"), status=rows[0].get("status"), upi_p=rows[0].get("upi_p"), cash_p=rows[0].get("cash_p")) if rows else None
k = darpan_kal._row(con, S)
out["kal"] = dict(handed_p=k.get("handed_p"), handed_to=k.get("handed_to"), created_by=k.get("created_by"), received=bool(k.get("received_at"))) if k else None
p = clinic_register.physio_row(con, D)
out["physio"] = (int(p["cash_p"] or 0) + int(p["upi_p"] or 0)) if p else None
r = clinic_register.register_row(con, D)
out["register"] = dict(entered_by=r["entered_by"], entered_at=r["entered_at"]) if r else None
ym = today.isoformat()[:7]
out["month_clinic"] = list(con.execute("SELECT COALESCE(SUM(total_amount_p),0), COUNT(*) FROM clinic_day_revenue WHERE substr(business_date,1,7)=?", (ym,)).fetchone())
out["month_sanj"] = sum(int(x.get("sale_p") or 0) for x in (sanjeevni_cash.days(con, ym + "-01", today.isoformat(), "medical") or {}).get("rows") or [])
out["exports"] = {kk: [dict(x) for x in con.execute("SELECT rows, taken_at, drive_id FROM docterz_export WHERE kind=? AND business_date=? AND status='current' ORDER BY id DESC LIMIT 1", (kk, L))] for kk in ("consultation", "followup")}
out["slips_pending"] = [[a.get("kind"), a.get("series"), a.get("slip_no"), a.get("amount_p"), a.get("made_by")] for a in slip_adjust.pending(con)]
out["owner_queue"] = [[dict(q)["business_date"], dict(q)["code"], dict(q)["amount_p"]] for q in clinic_money.owner_queue(con)]
out["unreceived"] = con.execute("SELECT COUNT(*) FROM darpan_kal_day WHERE unit='medical' AND handed_p IS NOT NULL AND received_at IS NULL").fetchone()[0]
t, n, old = records.check_line(con)
out["records"] = [t, n]
out["baaki"] = dict(slip_log.pending_counts(con))
sm = slip_log.match_day(con, D)
def nl(v): return len(v) if isinstance(v, (list, tuple, dict)) else int(v or 0)
out["slipday"] = dict(opd=nl(sm.get("opd")), xp=nl(sm.get("xp")), flags=nl(sm.get("flags")), orphans=nl(sm.get("orphans")))
out["road"] = packs.statement_road(con).get("text")
first = dt.date.fromisoformat(today.isoformat()[:8] + "01"); pm = (first - dt.timedelta(days=1)).isoformat()[:7]
cells = packs.cells(con, pm); out["shelf"] = [sum(1 for c in cells if c.get("state") != "empty"), len(cells)]
out["petty_wait"] = con.execute("SELECT COUNT(*) FROM petty_entry WHERE void_at='' AND confirm_at='' AND kind IN ('receive','loan_out')").fetchone()[0]
pl = con.execute("SELECT by_whom FROM petty_entry WHERE void_at='' ORDER BY at DESC LIMIT 1").fetchone()
out["petty_last"] = pl[0] if pl else None
import flask, sanjeevni_approvals
darpan_kal._db = lambda: con
darpan_kal._require = lambda *a, **k: ({"user": "manoj", "role": "doctor", "roles": ["checker"]}, None)
with flask.Flask("oracle").test_request_context("/finance/darpan/kal/api/owner"):
    ny = sanjeevni_approvals.needs_you(con)
out["needs_you"] = [[x.get("cls"), x.get("text")] for x in ny.get("lines") or []]
con.commit()
mp = json.load(open(dutymap, encoding="utf-8"))
xf = json.load(open(os.path.join(fin, "aaj_duties.json"), encoding="utf-8"))
# THE FLOOR, LAID THE OTHER WAY: the module lays views under the SQL; the walk makes a copy and DELETES the old rows.
import shutil, tempfile
fdir = tempfile.mkdtemp(prefix="oracle_floor_"); fdb = os.path.join(fdir, "floored.db")
a_ = sqlite3.connect(db); b_ = sqlite3.connect(fdb); a_.backup(b_); a_.close()
fl = str(xf.get("from") or "2026-09-01")[:10]
r_ = b_.execute("SELECT value FROM setting WHERE key='duties.from'").fetchone()
if r_ and r_[0]: fl = str(r_[0])[:10]
cutd = {}
for t_, f_ in sorted((xf.get("floor") or {}).items()):
    d_ = fl
    fo = f_.get("first_of")
    if fo:
        m_ = b_.execute("SELECT MIN(%s) FROM %s" % (fo[1], fo[0])).fetchone()[0]
        if m_ and str(m_)[:10] > d_: d_ = str(m_)[:10]
    cutd[t_] = d_
for t_, f_ in sorted((xf.get("floor") or {}).items()):
    b_.execute("DELETE FROM %s WHERE %s < ?" % (t_, f_["col"]), (cutd[t_],))
b_.commit(); b_.close()
def run_all(path):
    ro = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=5); res = {}; ex = {}
    for d_ in (mp.get("duties") or []):
        try:
            r_ = ro.execute(str(d_.get("due_sql") or "").strip().rstrip(";")).fetchone()
            res[d_["id"]] = [int((r_[0] if r_ else 0) or 0), (r_[1] if (r_ is not None and len(r_) > 1) else None), d_.get("person"), int(d_.get("allowed_days") or 0)]
        except Exception as e:
            res[d_["id"]] = ["ERR", str(e)[:80], d_.get("person"), 0]
    for d_ in (xf.get("extra") or []):
        if d_.get("kind") != "sql": continue
        try:
            r_ = ro.execute(d_["sql"]).fetchone()
            ex[d_["id"]] = [int((r_[0] if r_ else 0) or 0), (r_[1] if len(r_) > 1 else None), d_.get("person"), int(d_.get("allowed_days") or 0), bool(d_.get("soft"))]
        except Exception as e:
            ex[d_["id"]] = ["ERR", str(e)[:80], d_.get("person"), 0, False]
    ro.close(); return res, ex
out["duties"], out["extras"] = run_all(fdb)
out["duties_all"], _x = run_all(db)
out["floor"] = fl; out["cut"] = cutd
shutil.rmtree(fdir, ignore_errors=True)
out["people"] = mp.get("people") or {}
if len(sys.argv) > 4:                                    # where does the made-up patient's name travel in the owners' own answers?
    sent = sys.argv[4]
    def has_(v): return sent in json.dumps(v, ensure_ascii=False, default=str)
    with flask.Flask("oracle2").test_request_context("/finance/darpan/kal/api/owner"):
        ao = darpan_kal.api_owner(); ao = ao.get_json() if not isinstance(ao, tuple) else {}
    out["carriers"] = dict(slip_match=has_(sm), slip_pending=has_(slip_adjust.pending(con)), owner_queue=has_([dict(q) for q in clinic_money.owner_queue(con)]),
                           clinic_match=has_(m), darpan_card=has_(ao))
print("ORACLE " + json.dumps(out, ensure_ascii=False, default=str))
'''

# ------------------------------------------------------------------ the service's part, in its own process
SERVICE = r'''
import json, os, sqlite3, sys, time
sys.dont_write_bytecode = True
fin, db, full = sys.argv[1], sys.argv[2], sys.argv[3] == "1"
os.environ["FINANCE_DB"] = db
sys.path.insert(0, fin); os.chdir(fin)
out = {}
OWN = {"X-Clinic-User": "manoj", "X-Clinic-Role": "doctor"}; STF = {"X-Clinic-User": "shavez", "X-Clinic-Role": "manager"}
if full:
    os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
    import finance_app as fa
    import owner_console as oc
    app = fa.app
    out["mount_failed"] = [n for n, _w in fa._MOUNT_FAILED]
    out["mounted"] = "owner_console" in sys.modules
else:
    import flask
    import owner_console as oc
    app = flask.Flask("walk487")
    def getdb():
        c = sqlite3.connect(db, timeout=30); c.row_factory = sqlite3.Row; return c
    def require(*roles, unit=None):
        u = flask.request.headers.get("X-Clinic-User") or ""
        if u == "manoj" and unit == "packs" and "checker" in roles:
            return {"user": u, "role": "doctor", "roles": ["checker"]}, None
        return None, (flask.jsonify(ok=False, error="not_permitted"), 403)
    oc.init(app, getdb, require, unit="packs")
c = app.test_client()
URLS = ("/finance/console", "/finance/console/api/state", "/finance/console/api/tile")
out["owner"] = [c.get(u, headers=OWN).status_code for u in URLS]
out["staff"] = [c.get(u, headers=STF).status_code for u in URLS]
def state(q=""):
    return c.get("/finance/console/api/state" + q, headers=OWN).get_json()
def wait(pred, secs=90):
    t = time.time()
    while time.time() - t < secs:
        r = state()
        if pred(r):
            return r
        time.sleep(0.5)
    return state()
# the first three GETs above already asked for a reading
r1 = wait(lambda r: r["snapshot"] and not r["building"])
out["first"] = dict(snapshot=bool(r1["snapshot"]), building=r1["building"], stale=r1["stale"], label=r1.get("as_of_label"), err=r1.get("build_error"),
                    failed=(r1["snapshot"] or {}).get("failed"), keys=sorted((r1["snapshot"] or {}).get("sections", {}).keys()))
out["snap_mode"] = oct(os.stat(oc.SNAP).st_mode & 0o777)
out["lock_gone"] = not os.path.exists(oc.LOCK)
t = c.get("/finance/console/api/tile", headers=OWN).get_json()
out["tile"] = dict(ok=t.get("ok"), keys=sorted((t.get("tile") or {}).keys()), label=t.get("as_of_label"), day=t.get("day_words"))
pg = c.get("/finance/console", headers=OWN)
out["page"] = dict(code=pg.status_code, cache=pg.headers.get("Cache-Control"), title=b"<title>Command console</title>" in pg.data, n=len(pg.data))
# a fresh reading is not made again: nothing is stale
e0 = r1["snapshot"]["built_epoch"]; time.sleep(1.2); r2 = state()
out["fresh_not_rebuilt"] = (r2["snapshot"]["built_epoch"] == e0 and not r2["building"])
# one builder at a time: a living lock stops a second
open(oc.LOCK, "w").write("walk"); lm = os.stat(oc.LOG).st_mtime_ns
r3 = state("?refresh=1"); time.sleep(1.5)
out["one_at_a_time"] = dict(building=r3["building"], log_untouched=os.stat(oc.LOG).st_mtime_ns == lm, same=state()["snapshot"]["built_epoch"] == e0)
# two workers asking in the same instant: the second finds the first's lock and starts nothing
t0 = time.time()
while os.path.exists(oc.LOCK) and os.stat(oc.LOCK).st_size != 4 and time.time() - t0 < 30: time.sleep(0.2)
os.unlink(oc.LOCK); oc._reap(); n0 = len(oc._CHILDREN)
ka = oc._kick(db); kb = oc._kick(db)
out["two_kicks"] = dict(a=ka, b=kb, started=len(oc._CHILDREN) - n0)
t0 = time.time()
while os.path.exists(oc.LOCK) and time.time() - t0 < 60: time.sleep(0.3)
e0 = state()["snapshot"]["built_epoch"]
open(oc.LOCK, "w").write("walk")
# a dead lock (its build died) is replaced and a new reading is made on request
old = time.time() - 1000; os.utime(oc.LOCK, (old, old)); time.sleep(16)
r4 = state("?refresh=1")
r5 = wait(lambda r: r["snapshot"] and r["snapshot"]["built_epoch"] != e0 and not r["building"])
out["dead_lock"] = dict(kicked=r4["building"], said=r4.get("build_error"), rebuilt=r5["snapshot"]["built_epoch"] != e0, lock_gone=not os.path.exists(oc.LOCK),
                        cleared=r5.get("build_error"))
# a stale reading is replaced without being asked
e1 = r5["snapshot"]["built_epoch"]
s = json.load(open(oc.SNAP, encoding="utf-8")); s["built_epoch"] = time.time() - 4000; s["as_of"] = "2020-01-01T10:00:00"; s["as_of_hm"] = "10:00"
json.dump(s, open(oc.SNAP, "w", encoding="utf-8"), ensure_ascii=False)
t2 = c.get("/finance/console/api/tile", headers=OWN).get_json()
out["stale"] = dict(stale=t2["stale"], building=t2["building"], label=t2.get("as_of_label"))
r6 = wait(lambda r: r["snapshot"] and r["snapshot"]["built_epoch"] > e1 and not r["building"])
out["stale_rebuilt"] = r6["snapshot"]["built_epoch"] > e1 and r6.get("as_of_label", "").startswith("as of ") and "Jan" not in r6.get("as_of_label", "")
# a build that fails says so, and the older reading stands
e2 = r6["snapshot"]["built_epoch"]
os.environ["WALK_BREAK"] = "1"
oc_kick = oc._kick
ok = oc._kick(os.path.join(os.path.dirname(db), "no_such_database.db"))
t0 = time.time()
while os.path.exists(oc.LOCK) and time.time() - t0 < 60: time.sleep(0.3)
r7 = state()
out["failed_build"] = dict(kicked=ok, err=r7.get("build_error"), stands=bool(r7["snapshot"]) and r7["snapshot"]["built_epoch"] == e2, lock_gone=not os.path.exists(oc.LOCK))
# ... and a failure never becomes a loop: for a minute after it, asking again starts nothing
s = json.load(open(oc.SNAP, encoding="utf-8")); s["built_epoch"] = time.time() - 4000
json.dump(s, open(oc.SNAP, "w", encoding="utf-8"), ensure_ascii=False)
oc._reap(); n0 = len(oc._CHILDREN)
r8 = state("?refresh=1")
out["no_loop"] = dict(building=r8["building"], started=len(oc._CHILDREN) - n0, lock=os.path.exists(oc.LOCK), err=bool(r8.get("build_error")), stale=r8["stale"])
out["snap_name"] = os.path.basename(oc.SNAP)
print("SERVICE " + json.dumps(out, ensure_ascii=False, default=str))
'''


LISTS = r"""
import datetime as dt, hashlib, json, os, sqlite3, sys
sys.dont_write_bytecode = True
fin, db, full = sys.argv[1], sys.argv[2], sys.argv[3] == "1"
os.environ["FINANCE_DB"] = db
sys.path.insert(0, fin); os.chdir(fin)
out = {}
def H(u, r="staff"): return {"X-Clinic-User": u, "X-Clinic-Role": r}
OWN = H("manoj", "doctor")
if full:
    os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
    import finance_app as fa
    app = fa.app
    out["mount_failed"] = [n for n, _w in fa._MOUNT_FAILED]
else:
    import flask, aaj_kaam
    app = flask.Flask("walk487")
    def getdb():
        c_ = sqlite3.connect(db, timeout=30); c_.row_factory = sqlite3.Row; return c_
    def require(*roles, unit=None):
        u = flask.request.headers.get("X-Clinic-User") or ""
        if u == "manoj" and unit == "packs" and "checker" in roles:
            return {"user": u, "role": "doctor", "roles": ["checker"]}, None
        return None, (flask.jsonify(ok=False, error="not_permitted"), 403)
    def cu():
        return {"user": flask.request.headers.get("X-Clinic-User") or "", "role": flask.request.headers.get("X-Clinic-Role") or ""}
    aaj_kaam.init(app, getdb, require, cu)
c = app.test_client()
def J(r):
    try: return r.get_json() or {}
    except Exception: return {}
def md5(): return hashlib.md5(open(db, "rb").read()).hexdigest()
def rows(u, q=""):
    j = J(c.get("/finance/aaj/api/list" + q, headers=H(u) if u != "manoj" else OWN))
    return j, {s_["key"]: [r_["id"] for r_ in s_["rows"]] for s_ in j.get("sections") or []}
URLS = ("/finance/aaj", "/finance/aaj/api/list", "/finance/aaj/api/line", "/finance/aaj/api/switch")
m0 = md5()
out["nobody"] = [c.get(u).status_code for u in URLS]
off = {}
for u in ("shivani", "bhati", "sukhveer", "shavez", "darpan", "stranger"):
    a = c.get("/finance/aaj", headers=H(u)); b = c.get("/finance/aaj/api/list", headers=H(u)); l = c.get("/finance/aaj/api/line", headers=H(u)); w = c.get("/finance/aaj/api/switch", headers=H(u))
    off[u] = [a.status_code, b.status_code, J(b).get("error"), J(l).get("show"), w.status_code, c.get("/finance/aaj/api/list?as=alisha", headers=H(u)).status_code]
out["off"] = off
out["off_tick"] = c.post("/finance/aaj/api/tick", json={"id": "reception.week_float"}, headers=H("shivani")).status_code
out["staff_switch"] = c.post("/finance/aaj/api/switch", json={"on": 1}, headers=H("shivani")).status_code
# a form post (what a page of another site could send with the owner's cookie) and an empty post change nothing
out["form_switch"] = [c.post("/finance/aaj/api/switch", data={"on": "1"}, headers=OWN).status_code, c.post("/finance/aaj/api/switch", json={}, headers=OWN).status_code,
                      c.post("/finance/aaj/api/switch", data="[1]", headers=dict(OWN, **{"Content-Type": "application/json"})).status_code,
                      J(c.get("/finance/aaj/api/switch", headers=OWN)).get("on")]
jv, rv = rows("manoj", "?as=shivani")
out["view_as"] = dict(ok=jv.get("ok"), view_as=jv.get("view_as"), on=jv.get("on"), name=jv.get("name"), can_tick=[r_["can_tick"] for s_ in jv.get("sections") or [] for r_ in s_["rows"] if r_["kind"] == "tick"],
                      secs=sorted(rv), month=rv.get("month"))
out["owner_page"] = c.get("/finance/aaj", headers=OWN).status_code
out["owner_line_show"] = J(c.get("/finance/aaj/api/line", headers=OWN)).get("show")
out["bad_as"] = c.get("/finance/aaj/api/list?as=DROP%20TABLE", headers=OWN).status_code
out["reads_wrote_nothing"] = md5() == m0
con = sqlite3.connect(db)
out["tick_table_before"] = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='duty_tick'").fetchone()[0]
con.close()
s1 = J(c.post("/finance/aaj/api/switch", json={"on": 1}, headers=OWN))
out["on"] = dict(ok=s1.get("ok"), on=s1.get("on"), by=s1.get("by"), since=bool(s1.get("since")))
con = sqlite3.connect(db); out["setting"] = con.execute("SELECT value FROM setting WHERE key='aaj.staff_on'").fetchone()[0]
out["first_on"] = con.execute("SELECT value FROM setting WHERE key='aaj.staff_first_on'").fetchone()[0]; con.close()
lists = {}
for u in ("shivani", "alisha", "reception", "shavez", "bhati", "sukhveer", "darpan", "amir", "stranger"):
    j, r = rows(u)
    lists[u] = dict(ok=j.get("ok"), has=j.get("has"), open=j.get("open"), late=j.get("late"), line=j.get("line"), secs=r, clear=[x["id"] for x in j.get("clear") or []],
                    show=J(c.get("/finance/aaj/api/line", headers=H(u))).get("show"), page=c.get("/finance/aaj", headers=H(u)).status_code)
out["lists"] = lists
out["owner_line_show_on"] = J(c.get("/finance/aaj/api/line", headers=OWN)).get("show")          # the owner has no staff tile, on or off
jt, _r = rows("shivani")
out["texts"] = [r_["text"] for s_ in jt.get("sections") or [] for r_ in s_["rows"]] + [x["text"] for x in jt.get("clear") or []]
# from here the lists stand switched on since the first of THIS month, so this week's and this month's lines are live on any weekday
MS = dt.date.today().replace(day=1).isoformat() + "T00:00:00"
con = sqlite3.connect(db); con.execute("UPDATE setting SET value=? WHERE key='aaj.staff_on'", (MS + "|manoj",)); con.execute("UPDATE setting SET value=? WHERE key='aaj.staff_first_on'", (MS,)); con.commit(); con.close()
j2_, r2_ = rows("shivani"); out["month_on"] = dict(secs=r2_, can=[r_["can_tick"] for s_ in j2_.get("sections") or [] for r_ in s_["rows"] if r_["kind"] == "tick"])
tf = c.post("/finance/aaj/api/tick", data={"id": "bhati.petty_today"}, headers=H("bhati"))          # a form post is not a tap
con = sqlite3.connect(db); out["form_tick"] = [tf.status_code, con.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='duty_tick'").fetchone()[0]]; con.close()
t1 = c.post("/finance/aaj/api/tick", json={"id": "bhati.petty_today"}, headers=H("bhati")); j1 = J(t1)
t2 = c.post("/finance/aaj/api/tick", json={"id": "bhati.petty_today"}, headers=H("bhati")); j2 = J(t2)
t3 = c.post("/finance/aaj/api/tick", json={"id": "bhati.petty_today"}, headers=H("shivani"))
sqlid = ([r_["id"] for s_ in jt.get("sections") or [] for r_ in s_["rows"] if r_["kind"] == "sql"] + ["alisha.counter_sheet"])[0]   # a COUNTED line that is open on her list
out["sql_tried"] = sqlid
t4 = c.post("/finance/aaj/api/tick", json={"id": sqlid}, headers=H("shivani"))
t5 = c.post("/finance/aaj/api/tick", json={"id": "reception.week_float"}, headers=H("shivani")); j5 = J(t5)
t6 = c.post("/finance/aaj/api/tick", json={"id": "reception.week_float"}, headers=H("alisha")); j6 = J(t6)
t7 = c.post("/finance/aaj/api/tick", json={"id": "reception.week_float"}, headers=OWN)
t8 = c.post("/finance/aaj/api/tick", json={"id": "reception.week_float"}, headers=H("reception"))
out["ticks"] = dict(first=[t1.status_code, j1.get("by"), j1.get("yours")], again=[t2.status_code, j2.get("by"), j2.get("at") == j1.get("at")], other=t3.status_code, sql=t4.status_code,
                    shared=[t5.status_code, j5.get("by")], shared_second=[t6.status_code, j6.get("by"), j6.get("yours")], owner=t7.status_code, not_in_queue=t8.status_code)
con = sqlite3.connect(db); out["tick_rows"] = [list(r_) for r_ in con.execute("SELECT duty_id, period_key, by_whom FROM duty_tick ORDER BY id")]; con.close()
jb, _r = rows("bhati"); out["bhati_after"] = {r_["id"]: [bool(r_["done"]), r_["can_tick"]] for s_ in jb.get("sections") or [] for r_ in s_["rows"] if r_["kind"] == "tick"}
out["done_name"] = [(r_["done"] or {}).get("by_name") for s_ in jb.get("sections") or [] for r_ in s_["rows"] if r_["id"] == "bhati.petty_today"]
out["bhati_open_after"] = [lists["bhati"]["open"], jb.get("open")]
s0 = J(c.post("/finance/aaj/api/switch", json={"on": 0}, headers=OWN))
out["off_again"] = [s0.get("on"), J(c.get("/finance/aaj/api/list", headers=H("shivani"))).get("error")]
# off and on again: the first-on day does not move, so this week's and this month's lines do not start over
c.post("/finance/aaj/api/switch", json={"on": 1}, headers=OWN)
con = sqlite3.connect(db); f2 = con.execute("SELECT value FROM setting WHERE key='aaj.staff_first_on'").fetchone()[0]; con.close()
j3_, r3_ = rows("shivani")
out["on_again"] = [f2 == MS, r3_.get("month"), "reception.week_float" in (r3_.get("week") or [])]
# the periods, on fixed days (the engine asked directly): switched on a Wednesday
import aaj_kaam as A
con = sqlite3.connect(db); con.execute("UPDATE setting SET value='2026-10-07T10:00:00|manoj' WHERE key='aaj.staff_on'")
con.execute("UPDATE setting SET value='2026-10-07T10:00:00' WHERE key='aaj.staff_first_on'"); con.execute("DELETE FROM duty_tick"); con.commit(); con.close()
def tk(day):
    allp = A.build_all(db, dt.datetime.fromisoformat(day + "T12:00:00"))
    return {i["id"]: [bool(i["live"]), bool(i["late"])] for i in allp["items"] if i["kind"] == "tick"}
out["periods"] = {d_: tk(d_) for d_ in ("2026-10-07", "2026-10-08", "2026-10-12", "2026-10-13", "2026-11-01", "2026-11-03", "2026-11-04")}
# the duty map unreadable (a bad pull): the list says it is not whole, and never says all done
con = sqlite3.connect(db); con.execute("UPDATE setting SET value=? WHERE key='aaj.staff_on'", (dt.date.today().isoformat() + "T00:00:00|manoj",)); con.commit(); con.close()
keep_ = A.DUTY_MAP
# (a) one line of the map cannot be read; (b) one line reaches behind the floor through a table the floor is not under
mp_ = json.load(open(keep_, encoding="utf-8"))
for d_ in mp_["duties"]:
    if d_["id"] == "sukhveer.blood_mail": d_["due_sql"] = "SELECT COUNT(*) AS n, MIN(day) AS since FROM no_such_table_walk"
    if d_["id"] == "amir.own_correction": d_["due_sql"] = "SELECT 3 AS n, '2026-08-20' AS since"
    if d_["id"] == "amir.salt_list": d_["due_sql"] = "SELECT 1 AS n, date('now','localtime','-%d day') AS since" % int(d_["allowed_days"])          # its allowed days are used up TODAY
    if d_["id"] == "amir.rate_entry": d_["due_sql"] = "SELECT 1 AS n, date('now','localtime','-%d day') AS since" % (int(d_["allowed_days"]) - 1)   # one day still in hand
tmpm = os.path.join(os.environ.get("TMPDIR") or "/tmp", "walk_map_%d.json" % os.getpid()); json.dump(mp_, open(tmpm, "w", encoding="utf-8"))
A.DUTY_MAP = tmpm
ju = J(c.get("/finance/aaj/api/list", headers=H("sukhveer"))); lu = J(c.get("/finance/aaj/api/line", headers=H("sukhveer")))
ja = J(c.get("/finance/aaj/api/list", headers=H("amir")))
ra = [r_ for s_ in ja.get("sections") or [] for r_ in s_["rows"] if r_["id"] == "amir.own_correction"]
ea = [i for i in A.build_all(db)["items"] if i["id"] == "amir.own_correction"]
out["edge"] = {r_["id"]: r_["late"] for s_ in ja.get("sections") or [] for r_ in s_["rows"] if r_["id"] in ("amir.salt_list", "amir.rate_entry")}
out["unread"] = [ju.get("ok"), ju.get("has"), ju.get("partial"), ju.get("open"), lu.get("partial"), lu.get("text_hi"), lu.get("show")]
out["behind"] = dict(row=[(r_["text"], r_["late"]) for r_ in ra], hi=[d_["duty_hi"] for d_ in mp_["duties"] if d_["id"] == "amir.own_correction"],
                     en=[i["en"] for i in ea], flag=[i["behind"] for i in ea], late=[i["late"] for i in ea])
os.remove(tmpm)
A.DUTY_MAP = keep_
# (c) the duties file cannot be read (the map CAN): no floor -> no line of the map is shown at all
keepx = A.EXTRA; A.EXTRA = os.path.join(fin, "no_such_duties.json")
jx = J(c.get("/finance/aaj/api/list", headers=H("darpan"))); lx = J(c.get("/finance/aaj/api/line", headers=H("darpan")))
out["no_extra"] = [jx.get("ok"), jx.get("has"), jx.get("partial"), len(jx.get("sections") or []), len(jx.get("clear") or []), lx.get("show")]
A.EXTRA = keepx
A.DUTY_MAP = os.path.join(fin, "no_such_map.json")
jp = J(c.get("/finance/aaj/api/list", headers=H("sukhveer"))); lp = J(c.get("/finance/aaj/api/line", headers=H("sukhveer")))
jq = J(c.get("/finance/aaj/api/list", headers=H("shivani")))
A.DUTY_MAP = keep_
jr = J(c.get("/finance/aaj/api/list", headers=H("sukhveer"))); lr = J(c.get("/finance/aaj/api/line", headers=H("sukhveer")))
out["partial"] = dict(bad=[jp.get("ok"), jp.get("partial"), jp.get("has"), lp.get("partial"), lp.get("text_hi"), jq.get("partial"), jq.get("has")],
                      good=[jr.get("ok"), jr.get("partial"), jr.get("has"), lr.get("partial"), lr.get("text_hi")])
print("LISTS " + json.dumps(out, ensure_ascii=False, default=str))
"""


def run(cmd, env=None, timeout=300, cwd=None):
    e = dict(os.environ)
    e.update(env or {})
    p = subprocess.run(cmd, env=e, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def main():
    kit, finance, portal, db = arg("--kit"), arg("--finance"), arg("--portal"), arg("--db")
    attcore, dutymap = arg("--attcore"), arg("--dutymap", "/root/deploy/repo/claude_code_briefs/DUTY_MAP.json")
    allow_unread, full = int(arg("--allow-unread", "0")), "--full-app" in sys.argv
    if not all((kit, finance, portal, db, attcore)):
        raise SystemExit(__doc__)
    py = sys.executable
    live_before = {k: v for k, v in listing(finance).items() if k.endswith((".py", ".html")) and os.sep not in k}
    portal_before = md5f(portal)
    scr = tempfile.mkdtemp(prefix="s487_walk_")
    os.chmod(scr, 0o700)
    try:
        fin = os.path.join(scr, "fin")
        n = copy_code(finance, fin)
        shutil.copy2(portal, os.path.join(scr, "portal.py"))
        for f in ("owner_console.py", "owner_console.html", "aaj_kaam.py", "aaj_kaam.html", "aaj_duties.json"):
            shutil.copy2(os.path.join(kit, f), os.path.join(fin, f))
        play = os.path.join(scr, "play.db")
        backup(db, play)
        os.chmod(play, 0o600)

        # ============================================================ A  the files
        rc, out = run([py, "-B", os.path.join(kit, "apply_s487.py"), os.path.join(fin, "finance_app.py"), os.path.join(scr, "portal.py")])
        check("A1 the six edits apply to copies of the box's two files", rc == 0, out[-300:])
        fa = open(os.path.join(fin, "finance_app.py"), encoding="utf-8").read()
        po = open(os.path.join(scr, "portal.py"), encoding="utf-8").read()
        check("A2 finance_app.py: one guarded mount of the list, the row knows the part and counts 29; the console's mount is untouched",
              fa.count("aaj_kaam.init(app, db, require, current_user)") == 1 and fa.count("_MOUNT_FAILED.append(('aaj_kaam'") == 1
              and "'owner_console', 'aaj_kaam') if m not in sys.modules" in fa and fa.count("_all = 29") == 1 and "_all = 28" not in fa
              and fa.count("owner_console.init(app, db, require, unit=\"packs\")") == 1)
        doors = ("/finance/aaj", "/finance/aaj/api/list", "/finance/aaj/api/line", "/finance/aaj/api/tick", "/finance/aaj/api/switch")
        m_ = re.search(r"IDENTITY_ONLY_PATHS = \(([^)]*)\)\n", fa)
        got_ = sorted(re.findall(r'"(/[^"]+)"', m_.group(1))) if m_ else []
        check("A2b the list's five doors, and only they, join the two paths a signed-in login reaches without a unit row",
              got_ == sorted(doors + ("/finance/api/whoami", "/finance/clinic/api/whoami")), str(got_))
        try:
            compile(fa, "finance_app.py", "exec")
            compile(po, "portal.py", "exec")
            for f_ in ("owner_console.py", "aaj_kaam.py", "apply_s487.py"):
                compile(open(os.path.join(kit, f_), encoding="utf-8").read(), f_, "exec")
            XF = json.load(open(os.path.join(kit, "aaj_duties.json"), encoding="utf-8"))
            ok = True
        except Exception as e:                                         # noqa: BLE001
            ok, XF = "%s: %s" % (type(e).__name__, e), {}
        check("A3 the two edited files, the console 1.1 and the list engine compile; the duties file is sound JSON", ok is True, ok)
        MAP0 = json.load(open(dutymap, encoding="utf-8"))
        known = set(MAP0.get("people") or {}) | set(XF.get("names") or {})
        ids = [d_.get("id") for d_ in XF.get("extra") or []]
        bad = [d_.get("id") for d_ in XF.get("extra") or [] if
               (d_.get("kind") == "sql" and (not re.match(r"(?is)^(select|with)\b", str(d_.get("sql") or "")) or ";" in d_["sql"]))
               or (d_.get("kind") == "tick" and d_.get("period") not in ("day", "week", "month"))
               or (d_.get("kind") == "fetch" and not str((d_.get("fetch") or {}).get("url") or "").startswith("/"))
               or d_.get("kind") not in ("sql", "tick", "fetch") or not d_.get("hi") or not d_.get("en")
               or d_.get("person") not in known or any(a_ not in known for a_ in d_.get("also") or [])
               or (d_.get("door") is not None and not re.match(r"^/[a-z]", str(d_.get("door"))))
               or (d_.get("kind") == "fetch" and not re.match(r"^/[a-z]", str((d_.get("fetch") or {}).get("url"))))]
        ftab = sorted(XF.get("floor") or {})
        trap = [d_["id"] for d_ in MAP0.get("duties") or [] if any(re.search(r"\bmain\s*\.\s*%s\b" % t_, d_.get("due_sql") or "", re.I) for t_ in ftab)
                or (re.search(r"\browid\b", d_.get("due_sql") or "", re.I) and any(re.search(r"\b%s\b" % t_, d_.get("due_sql") or "") for t_ in ftab))]
        check("A3c no SQL of the map steps around the floor (no 'main.<table>' and no rowid on a floored table)", not trap, str(trap))
        check("A3b the duties file: every line is one read-only SELECT, a tap with a period, or another door's own count; every id is new "
              "to the map and its own; every person is a login the map knows",
              not bad and len(ids) == len(set(ids)) and not (set(ids) & {d_["id"] for d_ in MAP0.get("duties") or []})
              and re.match(r"^\d{4}-\d{2}-\d{2}$", str(XF.get("from") or "")) is not None, str(bad))
        check("A4 portal.py: the staff's tile once, its script once; the owner's tile, the strip and the older scripts still there",
              po.count('id="kaamTile"') == 1 and po.count("getElementById('kaamTile')") == 1 and po.count("/finance/aaj/api/line") == 1
              and po.count('id="todayTile"') == 1 and po.count("getElementById('todayTile')") == 1 and po.count('<div class="strip">') == 1
              and po.count("/* S472: Shavez's 'Mahine ka kaam' tile -- ") == 1 and po.count("/finance/console/api/tile") == 1)
        try:
            import jinja2                                              # the portal's own template engine
            vals = {}
            for node in ast.parse(po).body:
                if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                        and node.targets[0].id in ("HOME_HEAD", "PORTAL_HTML"):
                    vals[node.targets[0].id] = eval(compile(ast.Expression(node.value), "portal", "eval"), dict(vals))  # noqa: S307 -- two string literals
            tpl = jinja2.Environment().from_string(vals["PORTAL_HTML"])
            doc = tpl.render(role="doctor", who=dict(user="manoj", role="doctor"), sections=[], pc=False, sso=True, s444_nowork=False)
            stf = tpl.render(role="staff", who=dict(user="shivani", role="staff"), sections=[], pc=False, sso=True, s444_nowork=False)
            mgr = tpl.render(role="manager", who=dict(user="shavez", role="manager"), sections=[], pc=False, sso=True, s444_nowork=False)
            check("A5 the home page renders: staff and manager get the 'Aaj ka kaam' tile (hidden until its door says show) and no owner's "
                  "tile; the doctor gets the owner's tile and no staff tile",
                  all(x.count('id="kaamTile"') == 1 and ' hidden>' in x[x.index('id="kaamTile"'):x.index('id="kaamTile"') + 110]
                      and 'id="todayTile"' not in x and 'href="/finance/aaj"' in x for x in (stf, mgr))
                  and doc.count('id="todayTile"') == 1 and 'id="kaamTile"' not in doc and "kaamtile{" not in doc
                  and all(x.count("getElementById('kaamTile')") == 1 and x.count("/finance/aaj/api/line") == 1 for x in (stf, mgr)))
            check("A6 the staff's tile sits at the top of the home, above the tiles; the owner's tile still above the strip",
                  stf.index('id="kaamTile"') < stf.index('class="foot"') and doc.index('id="todayTile"') < doc.index('<div class="strip">')
                  and "\\u00b7" not in doc)
        except Exception as e:                                         # noqa: BLE001
            check("A5 the home page renders with the tiles", False, "%s: %s" % (type(e).__name__, e))
        for nm_, need_ in (("owner_console.html", ("/finance/console/api/state", "/finance/api/tile-summary", "/portal/review-counts", "/finance/aaj/api/switch")),
                           ("aaj_kaam.html", ("/finance/aaj/api/list", "/finance/aaj/api/tick"))):
            html = open(os.path.join(kit, nm_), encoding="utf-8").read()
            js = html[html.index("<script>") + 8:html.index("</script>")]
            check("A7 %s: its doors, nothing fetched from outside, the script whole" % nm_, all(x in js for x in need_)
                  and "http://" not in html and "https://" not in html and js.count("{") == js.count("}") and js.count("(") == js.count(")"))
            check("A8 %s draws with textContent only (nothing read is ever put in as HTML)" % nm_, "innerHTML" not in js
                  and "document.write" not in js and "eval(" not in js)

        # ============================================================ fixtures the walk writes itself
        now = dt.datetime.now()
        today = now.date()
        att = os.path.join(scr, "att")
        os.makedirs(att)
        shutil.copy2(attcore, os.path.join(att, "att_core.py"))
        with open(os.path.join(att, "att_config.py"), "w") as fh:
            fh.write("import os\nHERE = os.path.dirname(os.path.abspath(__file__))\nPUNCH_CSV = os.path.join(HERE, 'punches.csv')\n"
                     "STAFF_MASTER = os.path.join(HERE, 'staff_master.csv')\nEXCLUDE_IDS = {99}\nGRACE_MIN = 10\nEARLY_THRESHOLD_MIN = 30\n"
                     "FLAG_LATE_ON_SUNDAY = True\n")
        nowm = now.hour * 60 + now.minute
        early = max(1, nowm - 180)                                     # a shift that began three hours ago
        late_usual = min(23 * 60 + 58, nowm + 180)                     # someone whose usual punch is three hours from now

        def hhmm(m):
            return "%02d:%02d" % divmod(m, 60)
        staff = [(1, "Shivani Walktest", hhmm(early), "Y"), (2, "Shavez Walktest", hhmm(early), "Y"), (3, "Vikki Walktest", hhmm(early), "Y"),
                 (4, "Later Walktest", hhmm(late_usual), "Y"), (5, "Gone Walktest", hhmm(early), "N"), (99, "Excluded Walktest", hhmm(early), "Y")]
        with open(os.path.join(att, "staff_master.csv"), "w") as fh:
            fh.write("user_id,name,department,base_salary,allowed_offs,wd_start,wd_end,sun_start,sun_end,active,timing_note\n")
            for uid, name, st, act in staff:
                fh.write("%d,%s,Walk,,,%s,23:59,%s,23:59,%s,\n" % (uid, name, st, st, act))
        with open(os.path.join(att, "punches.csv"), "w") as fh:
            fh.write("user_id,datetime,io_mode,verify_mode,received_at\n")
            for back in range(1, 8):                                   # seven earlier days: everyone's usual first punch
                d = today - dt.timedelta(days=back)
                for uid, usual in ((1, early), (2, early), (3, early), (4, late_usual), (5, early), (99, early)):
                    fh.write("%d,%s %s:00,0,1,\n" % (uid, d.isoformat(), hhmm(usual)))
            fh.write("1,%s %s:00,0,1,\n" % (today.isoformat(), hhmm(early + 2)))              # Shivani: two minutes after her start
            p2 = min(nowm, early + 75)
            fh.write("2,%s %s:00,0,1,\n" % (today.isoformat(), hhmm(p2)))                     # Shavez: 75 minutes after his
            fh.write("99,%s %s:00,0,1,\n" % (today.isoformat(), hhmm(early)))                 # an excluded id never counts
        assets = os.path.join(scr, "assets.db")
        ac = sqlite3.connect(assets)
        ac.execute("CREATE TABLE bills (id INTEGER PRIMARY KEY, lane TEXT, status TEXT, dup_of INTEGER, page_of INTEGER, subgroup TEXT)")
        ac.executemany("INSERT INTO bills (lane,status,dup_of,page_of,subgroup) VALUES (?,?,?,?,?)",
                       [(None, "draft", None, None, None)] * 4 + [("clinic", "approved", None, None, "")] * 3            # 7 to sort
                       + [("clinic", "draft", None, None, "xray")] * 2 + [("pharmacy", "draft", None, None, None)] * 5
                       + [("clinic", "draft", 1, None, None), ("clinic", "draft", None, 1, None), ("clinic", "void", None, None, None)])
        ac.commit()
        ac.close()
        regdb = os.path.join(scr, "register.db")
        pm = (dt.date.fromisoformat(today.isoformat()[:8] + "01") - dt.timedelta(days=1)).isoformat()[:7]
        rc_ = sqlite3.connect(regdb)
        rc_.execute("CREATE TABLE locked_run (ym TEXT PRIMARY KEY, total_payout INTEGER NOT NULL, report_html TEXT NOT NULL, locked_by TEXT NOT NULL, "
                    "locked_ts TEXT NOT NULL, unlocked_by TEXT, unlocked_ts TEXT, unlock_reason TEXT, status TEXT NOT NULL DEFAULT 'locked')")
        rc_.execute("INSERT INTO locked_run (ym,total_payout,report_html,locked_by,locked_ts,status) VALUES (?,?,?,?,?,?)",
                    (pm, 1, "x", "walktest", today.isoformat() + " 09:00:00", "locked"))
        rc_.commit()
        rc_.close()
        fresh = os.path.join(scr, "fresh.json")
        json.dump(dict(generated_iso=now.replace(microsecond=0).isoformat(), counts=dict(total=5, ok=4, stale=1, never=0, error=0, parked=0),
                       legs=[dict(name="walk leg %d" % i, verdict="OK", age_words="1 hour ago") for i in range(4)]
                       + [dict(name="walk leg that went quiet", verdict="STALE", age_words="3 days ago")]), open(fresh, "w"))
        beat = os.path.join(scr, "beat.json")
        json.dump(dict(received_ts=int(time.time()) - 120, received_ist="x", beat=dict(agent_version="WALK", pc_uptime_hours=2.5,
                       attention=["one thing"], xray=dict(inbox_waiting=2, check_waiting=3))), open(beat, "w"))
        env = dict(DUTY_MAP_JSON=dutymap, CONSOLE_ATT_DIR=att, CONSOLE_ASSETS_DB=assets, CONSOLE_REGISTER_DB=regdb, CONSOLE_FRESHNESS=fresh,
                   CONSOLE_BEAT=beat, TMPDIR=os.path.join(scr, "tmp"), PYTHONDONTWRITEBYTECODE="1")
        os.makedirs(env["TMPDIR"])
        env_nofix = dict(env)

        def build(dbp, outp):
            return run([py, "-B", os.path.join(fin, "owner_console.py"), "--build", "--db", dbp, "--out", outp], env=env, cwd=fin)

        # ============================================================ B  the builder on the copy
        m0, l0 = md5f(play), listing(fin)
        s0p = os.path.join(scr, "snap0.json")
        rc, out = build(play, s0p)
        check("B1 the builder ends 0 and says what it wrote", rc == 0 and "console reading written" in out, out[-400:])
        check("B2 THE DATABASE IT READ IS BYTE-IDENTICAL, and no journal was left beside it",
              md5f(play) == m0 and not any(os.path.exists(play + x) for x in ("-journal", "-wal", "-shm")))
        check("B3 nothing was written beside the code it ran (no cache, no state file)", listing(fin) == l0,
              str(sorted(set(listing(fin)) ^ set(l0))[:6]))
        check("B4 its private copy is gone", not [x for x in os.listdir(env["TMPDIR"]) if x.startswith("console_build_")])
        check("B5 the reading is one file, readable by its owner only", os.path.exists(s0p) and (os.stat(s0p).st_mode & 0o777) == 0o600
              and not os.path.exists(s0p + ".err"))
        snap0 = json.load(open(s0p, encoding="utf-8"))
        want = ["needs", "money", "work", "att", "sanj", "papers", "system"]
        check("B6 seven sections, in the order the mock-up has them, none failed", snap0.get("order") == want and snap0.get("failed") == []
              and all(snap0["sections"][k].get("ok") for k in want), str(snap0.get("failed")))
        unread = [l for k in want for l in lines_of(snap0, k) if "could not be" in l.get("text", "")]
        mapsql = [l for l in unread if "could not be checked just now" in l["text"]]      # a duty whose own due_sql errors: the map's
        unread = [l for l in unread if l not in mapsql]
        check("B7 no piece of the reading says it could not be read%s" % ((" (%d allowed here)" % allow_unread) if allow_unread else ""),
              len(unread) <= allow_unread, "; ".join("%s [%s]" % (l["text"][:70], l.get("why", "")[:80]) for l in unread)[:600])
        for l in unread + mapsql:
            note("not read here: %s [%s]" % (l["text"][:80], l.get("why", "")[:160]))
        g = snap0.get("guard") or {}
        check("B7b the app's own modules were pointed at the COPY before any was loaded (the reading says which database they saw)",
              g.get("env_is_copy") is True and g.get("app_db_is_copy") is not False, str(g))
        T = snap0["tile"]
        check("B8 the tile carries its figures", all(k in T for k in ("clinic", "clinic_word", "sanj", "sanj_word", "needs_n", "work_late",
                                                                    "work_not_done", "att_in", "att_total", "sys_word", "as_of_hm")), str(sorted(T)))
        check("B9 no technical word is drawn: reasons travel in 'why', never in the line",
              not re.search(r"Error\b|Traceback|no such table|\(s\)| -- |_days\b", " ".join(l.get("text", "") + " " + l.get("who", "") for k in want
                                                                                         for l in lines_of(snap0, k))))

        # from the 10th of a month packs.needs_you_lines takes its long road (the checklist, the pack rows, the whole finance app loaded):
        mid = today.replace(day=15).isoformat()
        s15 = os.path.join(scr, "snap15.json")
        rc, out = run([py, "-B", os.path.join(fin, "owner_console.py"), "--build", "--db", play, "--out", s15], env=dict(env, PACKS_TODAY=mid), cwd=fin)
        sn15 = json.load(open(s15, encoding="utf-8")) if rc == 0 and os.path.exists(s15) else {}
        g15 = sn15.get("guard") or {}
        check("B10 the long road of the 15th of a month: a whole reading, the finance app loaded ON THE COPY, the database byte-identical",
              rc == 0 and sn15.get("failed") == [] and g15.get("env_is_copy") is True and g15.get("app_db_is_copy") is not False and md5f(play) == m0
              and listing(fin) == l0, "%s %s %s" % (rc, g15, out[-200:]))
        check("B11 ... and it takes far less than the two minutes a reading is allowed", float(sn15.get("took_s") or 999) < 60, str(sn15.get("took_s")))
        note("a reading takes %s s today and %s s on the 15th (finance app loaded: %s)" % (snap0.get("took_s"), sn15.get("took_s"), g15.get("app_loaded")))

        # ============================================================ C  every figure against its owner
        play2 = os.path.join(scr, "play2.db")
        shutil.copy2(play, play2)
        rc, out = run([py, "-B", "-c", ORACLE, fin, play2, dutymap], env=env, cwd=fin)
        om = [x for x in out.splitlines() if x.startswith("ORACLE ")]
        if not check("C0 the owners answer when asked directly", rc == 0 and len(om) == 1, out[-600:]):
            raise RuntimeError("no oracle")
        O = json.loads(om[0][7:])
        sys.path.insert(0, kit)
        os.environ["AAJ_DUTIES_JSON"] = os.path.join(kit, "aaj_duties.json")
        import owner_console as OC                                     # only its formatters (inr, dmy, tidy) are used here
        inr, dmy, tidy = OC.inr, OC.dmy, OC.tidy
        check("C1 the days: the clinic's, Sanjeevni's and the last counter day", snap0["clinic_day"] == O["D"] and snap0["sanj_day"] == O["S"]
              and snap0["lwd"] == O["lwd"] and snap0["day"] == O["today"], "%s %s %s" % (snap0["clinic_day"], snap0["sanj_day"], snap0["lwd"]))
        mt = O["match"]
        amt = (mt["p1"] or {}).get("docterz_p") if mt["doc_known"] else ((mt["p1"] or {}).get("counter_p") if mt["filled"] else None)
        check("C2 the clinic's figure is clinic_money.match_day's own", T["clinic"] == (inr(amt) if amt is not None else "–"), "%s vs %s" % (T["clinic"], amt))
        cl = find(snap0, "money", "Clinic ")
        vw = {"nothing_to_do": "matched", "not_filled": "counter sheet not filled", "waiting_docterz": "waiting for the Docterz export"}.get(mt["verdict"])
        check("C3 ... and its word is that verdict", bool(cl) and ((vw in cl[0]["text"]) if vw else ("%d flag" % len(mt["flags"])) in cl[0]["text"]),
              "%s / %s" % (mt["verdict"], cl[0]["text"] if cl else ""))
        fl = [l for l in lines_of(snap0, "money") if l.get("sub") and ("reached you" in l["text"] or "with the staff" in l["text"])]
        check("C4 one line per flag of the match: its code in plain words, its amount, whose it is -- and NOTHING of the flag's own sentence",
              len(fl) == len(mt["flags"]) and all(l["text"] == tidy(OC.flag_word(c_, a) + (" — reached you" if o else " — with the staff"))
                                                  for l, (c_, a, o) in zip(fl, mt["flags"])), str([l["text"] for l in fl]))
        if O["sanj"]:
            check("C5 Sanjeevni's sale is sanjeevni_cash.days' own", T["sanj"] == inr(O["sanj"]["sale_p"]) and bool(find(snap0, "money", "Sanjeevni " + inr(O["sanj"]["sale_p"]))))
        else:
            check("C5 Sanjeevni: no day filed is said so", T["sanj"] == "–" and bool(find(snap0, "money", "no day filed yet")))
        if O["kal"] and O["kal"]["handed_p"] is not None:
            sl = find(snap0, "money", "Sanjeevni ")
            check("C6 Darpan's hand-over: the amount, to whom, by whom, received or not", bool(sl) and inr(O["kal"]["handed_p"]) in sl[0].get("who", "")
                  and ("received ✓" in sl[0]["who"]) == O["kal"]["received"] and str(O["kal"]["created_by"]) in sl[0]["who"], sl[0].get("who", "") if sl else "")
        if O["physio"] is not None:
            check("C7 the physiotherapy day is clinic_register's own row", bool(find(snap0, "money", "Physiotherapy " + inr(O["physio"]))))
        mo = [l for l in lines_of(snap0, "money") if " so far: " in l["text"]]
        check("C8 the month so far: the clinic's and Sanjeevni's sums", bool(mo) and inr(O["month_clinic"][0]) in mo[0]["text"]
              and inr(O["month_sanj"]) in mo[0]["text"], mo[0]["text"] if mo else "")
        check("C9 the statement road in packs' own words; last month's shelf count", bool(find(snap0, "money", tidy(O["road"])))
              and bool(find(snap0, "money", "%d of %d on the shelf" % tuple(O["shelf"]))))
        du = O["duties"]
        ex = O["extras"]
        XD = {d_["id"]: d_ for d_ in XF.get("extra") or []}
        NAMES = dict(O["people"]); NAMES.update(XF.get("names") or {})
        mine = {k: v for k, v in du.items() if v[2] == "manoj" and v[0] != "ERR" and v[0] > 0}
        check("C10 'Needs you' is the duty map's own count for the owner", T["needs_n"] == len(mine) and snap0["sections"]["needs"]["chip"] == str(len(mine)),
              "%s vs %s" % (T["needs_n"], sorted(mine)))
        nl = [l for l in lines_of(snap0, "needs") if l["dot"] in ("b", "w")]
        MAP = json.load(open(dutymap, encoding="utf-8"))
        MAPD = {d_["id"]: d_ for d_ in MAP.get("duties") or []}

        def expect_line(did, v):
            """The line the MAP writes for a duty: its own owner_line filled with the count and the date the owner's SQL gave when the
            walk asked it directly. None where the map gives the duty no such line (the page then shows the duty's description)."""
            d_ = MAPD.get(did) or {}
            if not d_.get("owner_line"):
                return None
            days = None
            if v[1]:
                try:
                    days = (today - dt.date.fromisoformat(str(v[1])[:10])).days
                except ValueError:
                    days = None
            try:
                return tidy(str(d_["owner_line"]).format(n=v[0], days=(days if days is not None else "?"), since=OC.dm(v[1]) if v[1] else "-",
                                                         person=(MAP.get("people") or {}).get(d_.get("person"), d_.get("person") or "")))
            except Exception:                                          # noqa: BLE001 -- a line the map cannot fill
                return None
        # (S481.1: until 05-Oct 18:1x this asked only that each count appear in SOME line -- a duty whose line carries no count
        #  (the month's purchases to finalise) then passed or failed by what the other lines happened to hold. On the server it failed.)
        want_n = sorted(x for x in (expect_line(k, v) for k, v in mine.items()) if x)
        check("C11 ... one line each, and each line is the map's own owner's line filled with the count the owner's SQL gives",
              len(nl) == len(mine) and sorted(l["text"].strip() for l in nl if l["text"].strip() in want_n) == want_n
              and len(want_n) >= len(mine) - 1, "%s / %s" % ([l["text"][:70] for l in nl if l["text"].strip() not in want_n][:3],
                                                              [x[:70] for x in want_n if x not in [l["text"].strip() for l in nl]][:3]))
        hid0 = sum(max(0, O["duties_all"][k][0] - v[0]) for k, v in du.items() if v[2] == "manoj" and v[0] != "ERR" and O["duties_all"][k][0] != "ERR")
        old0 = [l for l in lines_of(snap0, "needs") if "older item" in l["text"]]
        check("C11b what the floor hides from the owner's own lines is said, with its number -- and nothing is said when nothing is hidden",
              (len(old0) == 1 and re.match(r"^%d older item" % hid0, old0[0]["text"]) is not None) if hid0 else not old0,
              "%s hidden / %s" % (hid0, [l["text"][:60] for l in old0]))
        check("C11c the reading says it was cut from the list engine, on the floor", (snap0.get("lists") or {}).get("engine") is True
              and (snap0.get("lists") or {}).get("floor") == O["floor"] and (snap0.get("lists") or {}).get("views") == O["cut"], str(snap0.get("lists")))

        def expect_extra(did, v):
            d_ = XD.get(did) or {}
            days = None
            if v[1]:
                try:
                    days = (today - dt.date.fromisoformat(str(v[1])[:10])).days
                except ValueError:
                    days = None
            try:
                return tidy(str(d_["en"]).format(n=v[0], days=(days if days is not None else "?"), since=OC.dm(v[1]) if v[1] else "-",
                                                 person=NAMES.get(d_.get("person"), d_.get("person") or "")))
            except Exception:                                          # noqa: BLE001
                return None

        def is_late(v):
            if not v[1]:
                return True
            try:
                return (today - dt.date.fromisoformat(str(v[1])[:10])).days >= v[3]
            except ValueError:
                return True
        staff_due = {k: v for k, v in du.items() if v[2] != "manoj" and v[0] != "ERR" and v[0] > 0}
        ex_due = {k: v for k, v in ex.items() if v[0] != "ERR" and v[0] > 0 and not v[4] and XD[k].get("console") != "fact"}
        check("C12 the staff's open lines: the map's own count ON THE FLOOR plus the parent's extra lines (no tap exists while the lists are off)",
              T["work_open"] == len(staff_due) + len(ex_due), "%s vs %s + %s" % (T["work_open"], len(staff_due), len(ex_due)))
        nlate = sum(1 for v in staff_due.values() if is_late(v)) + sum(1 for v in ex_due.values() if is_late(v))
        check("C13 ... and how many are late, by each line's own allowed days", T["work_late"] == nlate, "%s vs %s" % (T["work_late"], nlate))
        want_s = [x for x in (expect_line(k, v) for k, v in staff_due.items()) if x] + [x for x in (expect_extra(k, v) for k, v in ex_due.items()) if x]
        got_s = [l["text"].strip() for l in lines_of(snap0, "work") if l.get("sub")]
        check("C13b ... and every open staff line is written in its owner's own words, with its own count and date", bool(want_s) is bool(staff_due or ex_due)
              and all(x in got_s for x in want_s) and len(want_s) >= len(staff_due) + len(ex_due) - 3, str([x[:70] for x in want_s if x not in got_s][:3]))
        fall = {k: v for k, v in O["duties_all"].items() if v[2] != "manoj" and v[0] != "ERR" and k in du and du[k][0] != "ERR" and v[0] > du[k][0]}
        check("C13c NOTHING BEFORE THE FLOOR is counted in a staff line: where the unfloored count is larger, the line carries the floored one",
              all((expect_line(k, du[k]) in got_s) if du[k][0] > 0 else (expect_line(k, v) not in got_s) for k, v in fall.items()),
              str({k: (du[k][0], v[0]) for k, v in fall.items()}))
        note("the floor (%s; %s) takes %d staff line(s) down: %s" % (O["floor"], O["cut"], len(fall), {k: "%s of %s" % (du[k][0], v[0]) for k, v in fall.items()}))
        ppl = []
        for p_ in [v[2] for v in du.values()] + [d_.get("person") for d_ in XF.get("extra") or [] if d_.get("kind") in ("sql", "tick")]:
            if p_ != "manoj" and p_ not in ppl:
                ppl.append(p_)
        WK = {}
        for a_, b_ in (MAP0.get("shared") or {}).items():
            WK[a_] = [a_, b_]
        WK.update({k: list(v) for k, v in (XF.get("works") or {}).items()})
        allq = {lg: frozenset(WK.get(lg) or [lg]) for lg in set(ppl) | set(NAMES) | set(WK) if lg != "manoj"}
        want_blocks = {q_ for q_ in allq.values() if (q_ & set(ppl)) and not any(q_ < o_ for o_ in allq.values())}
        heads = [l for l in lines_of(snap0, "work") if str(l.get("href") or "").startswith("/finance/aaj?as=") and not l.get("sub")]
        got_blocks = {allq.get(l["href"].split("=", 1)[1]) for l in heads}
        check("C14 one head line per LIST (the desk's two people share one; the shared login, which sees part of it, has none), each "
              "opening that list as its people see it", len(heads) == len(want_blocks) and got_blocks == want_blocks
              and all(set(ppl) & q_ for q_ in got_blocks) and set().union(*want_blocks) >= set(ppl),
              "%s vs %s" % ([l.get("b") for l in heads], sorted(sorted(q_) for q_ in want_blocks)))
        ny = [l["text"] for l in lines_of(snap0, "sanj") if l.get("href")]
        check("C15 the Sanjeevni section IS the approvals page's own list, line for line", ny == [tidy(t) for _c, t in O["needs_you"]],
              "%d vs %d" % (len(ny), len(O["needs_you"])))
        check("C16 patient records: records.check_line's own sentence", bool(find(snap0, "papers", tidy(O["records"][0]))))
        b = O["baaki"]
        check("C17 Report baaki: slip_log.pending_counts' own numbers", bool(find(snap0, "papers", tidy("Report baaki: X-ray %d (%d late) · blood %d (%d late)" % (
            int(b.get("xray") or 0), int(b.get("xray_red") or 0), int(b.get("blood") or 0), int(b.get("blood_red") or 0))))))
        sd = O["slipday"]
        check("C18 the day's slips: slip_log.match_day's own counts", bool(find(snap0, "papers", tidy("%d OPD, %d X-ray / procedure" % (sd["opd"], sd["xp"])))))
        for kk, label in (("consultation", "Consultation report"), ("followup", "Follow-up log")):
            have = bool(O["exports"][kk])
            got = find(snap0, "work", "Docterz %s of" % label)
            check("C19 the Docterz %s: %s" % (label, "reached, with its rows" if have else "said NOT reached"), bool(got) and (
                ("reached the server" in got[0]["text"] and "(%d rows" % int(O["exports"][kk][0]["rows"] or 0) in got[0]["text"]) if have
                else "has NOT reached the server" in got[0]["text"]), got[0]["text"] if got else "")
        reg = find(snap0, "work", "Docterz daily collection of")
        check("C20 the counter sheet: who entered it, or that nobody has", bool(reg) and (("entered by %s" % O["register"]["entered_by"]) in reg[0]["text"]
              if O["register"] else "is NOT entered" in reg[0]["text"]), reg[0]["text"] if reg else "")
        pt = find(snap0, "work", "Petty book")
        check("C21 the petty book: its last writer and what waits for a confirmation", bool(pt) and (O["petty_last"] is None or (
            "last entry by %s" % O["petty_last"]) in pt[0]["text"]) and (("%d waiting" % O["petty_wait"]) in pt[0]["text"]) == bool(O["petty_wait"]),
            pt[0]["text"] if pt else "")
        if "manoj.slip_adjust" in mine:
            sl = [l for l in nl if l.get("table") and l["table"]["head"][:2] == ["Kind", "Slip"]]
            check("C22 the slips to approve: slip_adjust.pending's own rows", bool(sl) and len(sl[0]["table"]["rows"]) == len(O["slips_pending"])
                  and all(str(a[4]) in r for a, r in zip(O["slips_pending"], sl[0]["table"]["rows"])))
        if "manoj.clinic_flags" in mine:
            ql = [l for l in nl if l.get("table") and l["table"]["head"] == ["Day", "What"]]
            check("C22b the clinic's flags for the owner: clinic_money.owner_queue's own rows FROM THE FLOOR ON -- day, code in plain words, amount",
                  bool(ql) and ql[0]["table"]["rows"] == [[tidy(dmy(d_)), tidy(OC.flag_word(c_, a_))] for d_, c_, a_ in O["owner_queue"]
                                                         if str(d_) >= O["cut"]["clinic_money_flag"]][:40]
                  and (hid0 == 0 or any(str(d_) < O["cut"]["clinic_money_flag"] for d_, c_, a_ in O["owner_queue"])
                       or O["duties_all"]["manoj.clinic_flags"][0] == mine["manoj.clinic_flags"][0]),
                  str(ql[0]["table"]["rows"][:2] if ql else "no table on the line"))
        if "manoj.cash_received" in mine:
            ul = [l for l in nl if l.get("table") and l["table"]["head"] == ["Day", "Cash", "Handed to"]]
            check("C22c Darpan's cash not yet marked received: one row a day", bool(ul) and len(ul[0]["table"]["rows"]) == min(40, O["unreceived"]),
                  str(len(ul[0]["table"]["rows"]) if ul else "no table on the line"))
        # the made-up files
        A = snap0["sections"]["att"]
        check("C23 attendance, on the walk's own punches: 2 of 4 in (an inactive and an excluded id never count)",
              T["att_in"] == 2 and T["att_total"] == 4 and A["chip"] == "2 of 4 in", "%s %s %s" % (T.get("att_in"), T.get("att_total"), A["chip"]))
        if nowm >= 200 and nowm <= 23 * 60:
            lt = [l for l in A["lines"] if l["text"].startswith("Late: ")]
            check("C24 ... Shavez late by his own shift, Shivani not", bool(lt) and "Shavez Walktest" in lt[0]["text"] and "Shivani" not in lt[0]["text"]
                  and T["att_late"] == 1, lt[0]["text"] if lt else str(A["lines"])[:300])
            np_ = [l for l in A["lines"] if l["text"].startswith("No punch: ")]
            nd = [l for l in A["lines"] if l["text"].startswith("Not due yet: ")]
            check("C25 ... no punch: the one whose usual hour has passed; not due yet: the one whose usual hour is to come",
                  bool(np_) and "Vikki Walktest (usual %s)" % hhmm(early) in np_[0]["text"] and "Later" not in np_[0]["text"]
                  and (nowm + 180 > 23 * 60 + 58 or (bool(nd) and "Later Walktest (usual %s)" % hhmm(late_usual) in nd[0]["text"])),
                  str([l["text"] for l in A["lines"]])[:400])
            sh = [l for l in lines_of(snap0, "work") if l.get("b") == str(O["people"].get("shavez", "")) and not l.get("sub")]
            check("C26 ... and the punch reaches the right person's line (a name matched to a login only when it is the only one)",
                  bool(sh) and "Shavez in %s" % hhmm(min(nowm, early + 75)) in sh[0].get("who", ""), sh[0].get("who", "") if sh else "")
        else:
            note("the attendance clock checks C24-C26 are skipped within three hours of midnight (the made-up shifts cross the date)")
        check("C27 the salary month's lock from the register's own table", bool(find(snap0, "att", "salary month: locked by walktest")))
        check("C28 the scanned papers to sort: 7 of the 18 made-up bills", bool(find(snap0, "papers", "7 clinic papers to sort into lanes")))
        check("C29 the freshness file: 4 of 5, and the quiet leg named", T["sys_word"] == "4 of 5 feeds fresh"
              and bool(find(snap0, "system", "walk leg that went quiet")))
        check("C30 the reception PC's heartbeat: heard two minutes ago, one thing needs attention; its X-ray folder 2 and 3",
              bool(find(snap0, "system", "1 thing needs attention")) and bool(find(snap0, "papers", "2 waiting to be filed · 3 to check")))
        check("C31 the lines the page fills itself are marked for it (the register twice, the health line, the staff switch)",
              sum(1 for k in want for l in lines_of(snap0, k) if l.get("fill") == "reg") == 2
              and sum(1 for l in lines_of(snap0, "system") if l.get("fill") == "health") == 1
              and sum(1 for l in lines_of(snap0, "work") if l.get("fill") == "aaj") == 1)

        # ============================================================ D  made-up rows: the reading moves by exactly that
        con = sqlite3.connect(play)
        con.row_factory = sqlite3.Row
        nowiso = now.strftime("%Y-%m-%d %H:%M:%S")
        D_, L_ = O["D"], O["lwd"]
        slip = con.execute("SELECT id, day, clinic_id FROM slip ORDER BY id DESC LIMIT 1").fetchone()
        clone_row(con, "slip_adjust", "1=1", (), dict(slip_id=slip["id"], item_id=None, kind="discount", amount_p=15000, reason="walk", note=SENT + " note",
                                                      cancel_how="", clinic_id=slip["clinic_id"], day=slip["day"], made_by="walktest", made_at=nowiso,
                                                      state="pending", checked_by="", checked_at="", check_note=""))
        clone_row(con, "day_entry", "unit='medical'", (), dict(unit="medical", business_date="2019-01-01", status="submitted", entered_by="walktest",
                                                              entered_at=nowiso, approved_by=None, approved_at=None))
        had_fu = bool(O["exports"]["followup"])
        if had_fu:
            con.execute("UPDATE docterz_export SET status='duplicate' WHERE kind='followup' AND business_date=?", (L_,))
        else:
            clone_row(con, "docterz_export", "kind='followup'", (), dict(drive_id="reception:walk", drive_name="walk.xlsx", md5="walk" + nowiso, kind="followup",
                                                                      business_date=L_, rows=77, status="current", taken_at=nowiso))
        had_reg = bool(O["register"])
        if had_reg:
            con.execute("UPDATE clinic_register_day SET entered_by='walktest', entered_at=? WHERE business_date=?", (nowiso, D_))
        else:
            clone_row(con, "clinic_register_day", "1=1", (), dict(business_date=D_, entered_by="walktest", entered_at=nowiso), drop=())
        clone_row(con, "petty_entry", "1=1", (), dict(entry_date=today.isoformat(), kind="receive", party="walk", other_name="", amount_p=100, photo="",
                                                      by_whom="walktest", at=nowiso, confirm_by="", confirm_at="", void_by="", void_at=""))
        # a made-up patient, put wherever the owners keep a patient's name for the days the reading looks at
        con.execute("UPDATE slip SET name_seen=?, no_id_name=?", (SENT, SENT))
        con.execute("UPDATE clinic_day_line SET patient=?", (SENT,))
        con.execute("UPDATE clinic_money_flag SET text=? || ' ' || text", (SENT,))
        # a WRONG figure left in the cache one of the owner's duties reads (returns.pending_ok): the reading must not carry it
        con.execute("DELETE FROM setting WHERE key='returns.pending_ok'")
        con.execute("INSERT INTO setting (key, value) VALUES ('returns.pending_ok', '987|2019-01-01')")
        clone_row(con, "clinic_money_flag", "1=1", (), dict(business_date="2019-01-01", key="walk:1", code="total_diff", amount_p=-12300,
                                                            text=SENT + " made-up flag", owner=1, status="open", created_at=nowiso))
        # ... and on THIS side of the floor: a pharmacy day of September and a flag ON THE FLOOR'S OWN DAY (the first day that counts);
        # the 2019 ones above are before it
        recent = [d_ for d_ in ("2026-09-06", "2026-09-13", "2026-09-20", "2026-09-27", "2026-09-05", "2026-09-12")
                  if not con.execute("SELECT 1 FROM day_entry WHERE unit='medical' AND business_date=?", (d_,)).fetchone()][0]
        clone_row(con, "day_entry", "unit='medical'", (), dict(unit="medical", business_date=recent, status="submitted", entered_by="walktest",
                                                              entered_at=nowiso, approved_by=None, approved_at=None))
        clone_row(con, "clinic_money_flag", "1=1", (), dict(business_date=O["cut"]["clinic_money_flag"], key="walk:2", code="bank_extra", amount_p=45600,
                                                            text=SENT + " made-up flag two", owner=1, status="open", created_at=nowiso))
        con.execute("UPDATE darpan_kal_day SET reason_note=?, owner_note=?", (SENT, SENT))
        try:
            con.execute("UPDATE clinic_other_upi SET note=?", (SENT,))
        except sqlite3.Error:
            pass
        con.commit()
        con.close()
        s1p = os.path.join(scr, "snap1.json")
        m1 = md5f(play)
        rc, out = build(play, s1p)
        check("D0 the builder reads the changed copy, and again leaves it byte-identical", rc == 0 and md5f(play) == m1, out[-300:])
        snap1 = json.load(open(s1p, encoding="utf-8"))
        n_slip0 = mine.get("manoj.slip_adjust", [0])[0]
        sl = [l for l in lines_of(snap1, "needs") if l.get("table") and l["table"]["head"][:2] == ["Kind", "Slip"]]
        check("D1 a made-up discount to approve: the count goes up by one and the row shows who made it and how much",
              bool(sl) and len(sl[0]["table"]["rows"]) == n_slip0 + 1 and re.search(r"(?<!\d)%d(?!\d)" % (n_slip0 + 1), sl[0]["text"]) is not None
              and any("walktest" in r and "₹150" in r and "discount" in r for r in sl[0]["table"]["rows"]), str(sl[0] if sl else "")[:300])
        n_day0 = mine.get("manoj.approve_days", [0])[0]
        n_day_all0 = O["duties_all"]["manoj.approve_days"][0]
        dl = [l for l in lines_of(snap1, "needs") if "to approve" in l["text"] and l.get("who") and tidy(dmy(recent)) in l.get("who", "")]
        check("D2 a made-up pharmacy day of September is counted and named among the days; the one of 2019 is neither (the floor)",
              bool(dl) and re.search(r"(?<!\d)%d(?!\d)" % (n_day0 + 1), dl[0]["text"]) is not None and ("01" + NB + "Jan") not in dl[0].get("who", ""),
              str([(l["text"], l.get("who")) for l in lines_of(snap1, "needs") if "to approve" in l["text"]])[:300])
        s1 = [l["text"] for l in lines_of(snap1, "sanj") if l.get("href")]
        check("D3 ... while the approvals page's own first line, which knows no floor, counts both", bool(s1)
              and re.search(r"(?<!\d)%d days? to approve" % (n_day_all0 + 2), s1[0]) is not None, s1[0] if s1 else "")
        ql1 = [l for l in lines_of(snap1, "needs") if l.get("table") and l["table"]["head"] == ["Day", "What"]]
        check("D3b the made-up flag dated ON the floor's own day is listed by day, code and amount (never by its sentence); the one of 2019 is not",
              bool(ql1) and any(r[0] == tidy(dmy(O["cut"]["clinic_money_flag"])) and inr(45600) in r[1] for r in ql1[0]["table"]["rows"])
              and not any(r[0] == tidy(dmy("2019-01-01")) for r in ql1[0]["table"]["rows"]), str(ql1[0]["table"]["rows"][-2:] if ql1 else ""))
        old1 = [l for l in lines_of(snap1, "needs") if "older item" in l["text"]]
        check("D3c ... and the two of 2019 are in the count of older items not shown (%d before, two more now)" % hid0,
              len(old1) == 1 and re.match(r"^%d older items" % (hid0 + 2), old1[0]["text"]) is not None, str([l["text"][:70] for l in old1]))
        check("D4 'Needs you' never falls: the count is the lines", snap1["tile"]["needs_n"] == len([l for l in lines_of(snap1, "needs") if l["dot"] in ("b", "w")])
              and snap1["tile"]["needs_n"] >= T["needs_n"])
        fu = find(snap1, "work", "Docterz Follow-up log of")
        sheet_red0 = sum(1 for l in lines_of(snap0, "work") if "Docterz daily collection of" in l["text"] and l.get("dot") == "b")
        if had_fu:
            check("D5 the follow-up export taken away: the line turns red and one more thing is not done", bool(fu) and fu[0]["dot"] == "b"
                  and "has NOT reached" in fu[0]["text"] and snap1["tile"]["work_not_done"] == T["work_not_done"] + 1 - sheet_red0, fu[0]["text"] if fu else "")
        else:
            check("D5 a made-up follow-up export: the red line turns green, says the road, and one thing less is not done", bool(fu) and fu[0]["dot"] == "g"
                  and "(77 rows, straight from the reception PC)" in fu[0]["text"] and snap1["tile"]["work_not_done"] == T["work_not_done"] - 1 - sheet_red0,
                  "%s (not done %s -> %s, the sheet's line was red: %s)" % (fu[0]["text"] if fu else "", T["work_not_done"], snap1["tile"]["work_not_done"], sheet_red0))
        rg = find(snap1, "work", "Docterz daily collection of")
        check("D6 the counter sheet entered by a made-up person: the line names him", bool(rg) and "entered by walktest" in rg[0]["text"] and rg[0]["dot"] == "g",
              rg[0]["text"] if rg else "")
        cs = find(snap1, "money", "Clinic ")
        check("D7 ... and the money line names him too", bool(cs) and "counter sheet by walktest" in cs[0].get("who", ""), cs[0].get("who", "") if cs else "")
        pt = find(snap1, "work", "Petty book")
        check("D8 a made-up petty entry waiting for a confirmation: its writer and one more waiting", bool(pt) and "last entry by walktest" in pt[0]["text"]
              and ("%d waiting for a confirmation" % (O["petty_wait"] + 1)) in pt[0]["text"], pt[0]["text"] if pt else "")
        play3 = os.path.join(scr, "play3.db")
        shutil.copy2(play, play3)
        rc, out = run([py, "-B", "-c", ORACLE, fin, play3, dutymap, SENT], env=env, cwd=fin)
        om = [x for x in out.splitlines() if x.startswith("ORACLE ")]
        O2 = json.loads(om[0][7:]) if (rc == 0 and om) else {}
        car = O2.get("carriers") or {}
        mine2 = {k: v for k, v in (O2.get("duties") or {}).items() if v[2] == "manoj" and v[0] != "ERR" and v[0] > 0}
        nl2 = [l for l in lines_of(snap1, "needs") if l["dot"] in ("b", "w")]
        want2 = sorted(x for x in (expect_line(k, v) for k, v in mine2.items()) if x)
        check("D8b a stale figure left in a cache is never shown: the owner's lines are the map's lines filled with the counts made NOW",
              bool(O2) and snap1["tile"]["needs_n"] == len(mine2) and not any("987" in l["text"] for l in nl2)
              and sorted(l["text"].strip() for l in nl2 if l["text"].strip() in want2) == want2 and len(want2) >= len(mine2) - 1,
              "%s vs %s / stale: %s / not the map's: %s" % (snap1["tile"]["needs_n"], len(mine2), [l["text"][:50] for l in nl2 if "987" in l["text"]],
                                                            [x[:70] for x in want2 if x not in [l["text"].strip() for l in nl2]][:3]))
        check("D9a the made-up patient's name really travels in the owners' own answers (the slips to approve and the clinic's flags for the "
              "owner -- both made by this walk)", car.get("slip_pending") and car.get("owner_queue"), str(car))
        note("the made-up name is carried by: %s" % ", ".join(k for k, v in sorted(car.items()) if v))
        check("D9 NO PATIENT IN ANY READING: that name is in no reading", SENT not in flat(snap1) and SENT not in flat(snap0))
        # every phone number and bank reference the database itself holds: none may be in a reading
        secret = set()
        sc = sqlite3.connect("file:%s?mode=ro" % play, uri=True)
        for (tname,) in sc.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
            for col in [x[1] for x in sc.execute("PRAGMA table_info(%s)" % tname)]:
                if re.search(r"(?i)phone|mobile|rrn|utr|gateway_ref|bank_ref|upi_ref|account_no|acct", col):
                    try:
                        for (v,) in sc.execute("SELECT DISTINCT %s FROM %s WHERE %s IS NOT NULL LIMIT 200000" % (col, tname, col)):
                            secret.update(re.findall(r"\d{9,}", str(v)))
                    except sqlite3.Error:
                        pass
        sc.close()
        for nm, sn in (("before", snap0), ("after", snap1)):
            body = re.sub(r'"(built_epoch|took_s)": [0-9.]+', "", flat(sn))
            hit = sorted(set(re.findall(r"\d{9,}", body)) & secret)
            check("D10 none of the %d phone numbers and bank references the database holds is in the reading %s" % (len(secret), nm), not hit,
                  "%d found" % len(hit))
        check("D10b ... and that list is not empty (the check has something to look for)", len(secret) > 50, str(len(secret)))

        # the fixtures taken away: each piece says so in plain words and the rest stands
        env2 = dict(env, CONSOLE_ATT_DIR=os.path.join(scr, "nowhere"), CONSOLE_ASSETS_DB=os.path.join(scr, "nowhere.db"),
                    CONSOLE_REGISTER_DB=os.path.join(scr, "nowhere2.db"), CONSOLE_FRESHNESS=os.path.join(scr, "nowhere.json"),
                    CONSOLE_BEAT=os.path.join(scr, "nowhere3.json"), DUTY_MAP_JSON=os.path.join(scr, "nowhere4.json"))
        s2p = os.path.join(scr, "snap2.json")
        rc, out = run([py, "-B", os.path.join(fin, "owner_console.py"), "--build", "--db", play, "--out", s2p], env=env2, cwd=fin)
        snap2 = json.load(open(s2p, encoding="utf-8")) if rc == 0 else {}
        gone = [l for k in want for l in lines_of(snap2, k) if "could not be read just now" in l.get("text", "")]
        check("D11 with the punches, the asset database, the register, the freshness file, the heartbeat and the duty map all missing: still one "
              "reading, seven sections, each missing piece said in plain words with its reason out of sight",
              rc == 0 and snap2.get("failed") == [] and len(gone) >= 6 and all(l.get("why") for l in gone)
              and not any("Error" in l["text"] for l in gone), "%s %s" % (rc, [l["text"][:50] for l in gone]))
        check("D12 ... and without the duty map 'Needs you' falls back to the approvals page's own lines, never to an empty list",
              any("approvals page's own lines" in l["text"] for l in lines_of(snap2, "needs")) and len(lines_of(snap2, "needs")) >= 2
              and bool(find(snap2, "money", "Clinic ")), str([l["text"][:60] for l in lines_of(snap2, "needs")]))

        # ============================================================ E  the service's part
        senv = dict(env, CONSOLE_SNAPSHOT=os.path.join(scr, "svc", "console_reading.dat"), CONSOLE_BUILD_LOG=os.path.join(scr, "svc", "build.log"))
        os.makedirs(os.path.join(scr, "svc"))
        rc, out = run([py, "-B", "-c", SERVICE, fin, play, "1" if full else "0"], env=senv, cwd=fin, timeout=420)
        sm = [x for x in out.splitlines() if x.startswith("SERVICE ")]
        if check("E0 the service's part runs through Flask's own test client%s" % (" inside the whole edited finance app" if full else ""),
                 rc == 0 and len(sm) == 1, out[-900:]):
            V = json.loads(sm[0][8:])
            if full:
                check("E1 the whole edited finance app loads: every part mounted, the console among them", V["mount_failed"] == [] and V["mounted"], str(V.get("mount_failed")))
            check("E2 the owner: the page and both doors answer 200", V["owner"] == [200, 200, 200], str(V["owner"]))
            check("E3 a staff login: all three refused (403)", V["staff"] == [403, 403, 403], str(V["staff"]))
            f = V["first"]
            check("E4 the first reading is made in the background and arrives whole", f["snapshot"] and not f["building"] and not f["stale"] and not f["err"]
                  and f["failed"] == [] and f["keys"] == sorted(want) and str(f["label"]).startswith("as of "), str(f))
            check("E5 it is written 600 and its lock is gone", V["snap_mode"] == "0o600" and V["lock_gone"], "%s %s" % (V["snap_mode"], V["lock_gone"]))
            check("E6 the tile door gives the tile's figures, the day and 'as of'", V["tile"]["ok"] and "needs_n" in V["tile"]["keys"]
                  and "clinic" in V["tile"]["keys"] and str(V["tile"]["label"]).startswith("as of ") and bool(V["tile"]["day"]), str(V["tile"]))
            check("E7 the page is served whole and never cached", V["page"]["code"] == 200 and V["page"]["cache"] == "no-store" and V["page"]["title"], str(V["page"]))
            check("E8 a fresh reading is not made again", V["fresh_not_rebuilt"])
            o = V["one_at_a_time"]
            check("E9 one builder at a time: while a lock lives, a second is not started", o["building"] and o["log_untouched"] and o["same"], str(o))
            tk = V["two_kicks"]
            check("E9b two askers in the same instant start ONE builder", tk["a"] and tk["b"] and tk["started"] == 1, str(tk))
            d = V["dead_lock"]
            check("E10 a dead lock is taken over, the page is told the reading before was stopped, the asked-for reading is made and the note "
                  "is gone", d["kicked"] and "stopped before it finished" in str(d["said"]) and d["rebuilt"] and d["lock_gone"] and not d["cleared"], str(d))
            st = V["stale"]
            check("E11 an old reading is shown with its DATE, never as today's, while a new one is made", st["stale"] and st["building"]
                  and "Jan" in str(st["label"]), str(st))
            check("E12 ... and the new one replaces it by itself", V["stale_rebuilt"])
            fb = V["failed_build"]
            check("E13 a build that cannot read the database says so in the page's warning, and the older reading stands", fb["kicked"] and bool(fb["err"])
                  and fb["stands"] and fb["lock_gone"], str(fb))
            nlp = V["no_loop"]
            check("E13b a failure never becomes a loop: asked again within the minute, nothing is started and the page still says why",
                  nlp["stale"] and not nlp["building"] and nlp["started"] == 0 and not nlp["lock"] and nlp["err"], str(nlp))
        names = [os.path.basename(x) for x in (OC.SNAP, OC.LOCK, OC.ERRF, OC.LOG)]
        check("E15 by default nothing the console writes is named *.json, *.py, *.html, *.sql or *.sh (the nightly code bundle takes those "
              "from the finance folder to Drive; a reading holds the day's revenue)", "CONSOLE_SNAPSHOT" not in os.environ
              and names[0] == "console_reading.dat" and not any(n.endswith((".json", ".py", ".html", ".sql", ".sh")) for n in names)
              and all(os.path.dirname(x) == kit for x in (OC.SNAP, OC.LOCK, OC.ERRF, OC.LOG)), str(names))
        check("E14 the made-up database is as the walk left it: the service's part wrote nothing to it", md5f(play) == m1)

        # ============================================================ F  the staff's lists
        os.environ["DUTY_MAP_JSON"] = dutymap
        os.environ["AAJ_DUTIES_JSON"] = os.path.join(kit, "aaj_duties.json")
        import aaj_kaam as AK                                          # the engine itself, asked directly (read-only by construction)
        mp2 = md5f(play2)
        allp = AK.build_all(play2)
        check("F1 the list engine reads through a read-only door: the database it read is byte-identical, no journal beside it",
              md5f(play2) == mp2 and not any(os.path.exists(play2 + x) for x in ("-journal", "-wal", "-shm")))
        check("F2 the floor is the owner's (01-Sep-2026 unless the setting says otherwise) and each floored table's own start is what the "
              "walk found by deleting", allp["floor"] == O["floor"] and allp["views"] == O["cut"], "%s %s vs %s %s" % (allp["floor"], allp["views"], O["floor"], O["cut"]))
        em = {i["id"]: i for i in allp["items"] if i["kind"] == "sql" and i["from_map"]}
        ee = {i["id"]: i for i in allp["items"] if i["kind"] == "sql" and not i["from_map"]}
        diff = [k for k, v in du.items() if (v[0] == "ERR") != bool(em[k]["err"]) or (v[0] != "ERR" and (em[k]["n"] != v[0] or (v[0] > 0 and str(em[k]["since"] or "") != str(v[1] or "")[:10])))]
        check("F3 EVERY duty of the map, counted under the module's views, equals the same SQL run on a copy with the old rows deleted "
              "(%d duties)" % len(du), not diff and len(em) == len(du), str([(k, em[k]["n"], em[k]["since"], du[k][:2]) for k in diff][:4]))
        diff2 = [k for k, v in ex.items() if v[0] != "ERR" and (ee[k]["n"] != v[0])]
        check("F3b ... and so does every extra line of the parent's file", not diff2 and len(ee) == len(ex), str(diff2))
        check("F3c the unfloored count the engine keeps beside each line is the plain SQL's own", all(
            em[k]["n_all"] == max(em[k]["n"], v[0]) for k, v in O["duties_all"].items() if v[0] != "ERR" and not em[k]["err"]))
        stale = [(i["id"], i["since"]) for i in allp["items"] if i["kind"] == "sql" and i["n"] > 0 and i["since"] and str(i["since"]) < allp["floor"]]
        for s_ in stale:
            note("a line still reaches behind the floor (its table is not one the floor is laid under): %s since %s" % s_)
        shv, rcp, bht = AK.list_for(allp, "shivani"), AK.list_for(allp, "reception"), AK.list_for(allp, "bhati")
        ids = lambda l_: {i["id"] for k_ in ("first", "open", "night", "week", "month", "clear") for i in l_["sections"][k_]}     # noqa: E731
        check("F4 who sees which queue: Shivani works Alisha's and the reception's; the shared login its own; Bhati his own; a login "
              "nobody named has no list", {"alisha.counter_sheet", "reception.bill_scan", "reception.docterz_followup", "reception.staff_register"} <= ids(shv)
              and "alisha.counter_sheet" not in ids(rcp) and "reception.bill_scan" in ids(rcp) and "reception.docterz_followup" in ids(rcp)
              and "bhati.petty_today" in ids(bht) and not (ids(bht) & ids(rcp)) and not AK.list_for(allp, "stranger")["has"]
              and not any(i["person"] == "manoj" for l_ in (shv, rcp, bht) for k_ in l_["sections"] for i in l_["sections"][k_]))
        check("F5 the list's Hinglish line is the map's own duty_hi, with its count and its day", all(
            AK.item_hi(i).startswith(AK.tidy(MAPD[i["id"]]["duty_hi"])) for i in allp["items"] if i["kind"] == "sql" and i["from_map"])
            and all(("%d baaki" % i["n"]) in AK.item_hi(i) for i in allp["items"] if i["kind"] == "sql" and i["from_map"] and i["n"] > 0))
        lenv = dict(env, PYTHONDONTWRITEBYTECODE="1")
        play5 = os.path.join(scr, "play5.db")
        shutil.copy2(play, play5)
        rc, out = run([py, "-B", "-c", LISTS, fin, play5, "1" if full else "0"], env=lenv, cwd=fin, timeout=300)
        lm = [x for x in out.splitlines() if x.startswith("LISTS ")]
        if check("F6 the list's doors run through Flask's own test client%s" % (" inside the whole edited finance app" if full else ""),
                 rc == 0 and len(lm) == 1, out[-900:]):
            W = json.loads(lm[0][6:])
            if full:
                check("F7 the whole edited finance app loads with the list mounted; a visitor who is not signed in is sent to the login",
                      W["mount_failed"] == [] and all(x in (302, 401) for x in W["nobody"]), "%s %s" % (W.get("mount_failed"), W["nobody"]))
            o_ = W["off"]
            check("F8 OFF (as installed): a staff login gets the page but no list, no tile, and cannot see another's list or the switch -- "
                  "Bhati too, who holds no row in the pharmacy's unit, and Shavez, who is the maker of the owner's own unit", all(v == [200, 200, "off", False, 403, 403] for v in o_.values()), str(o_))
            check("F9 ... a tap is refused while off, and a staff login cannot turn the lists on", W["off_tick"] == 403 and W["staff_switch"] == 403,
                  "%s %s" % (W["off_tick"], W["staff_switch"]))
            check("F9b a form post with the owner's own login (what another site's page could send), an empty post and a post that is not "
                  "an object change nothing: the lists stay off", W["form_switch"] == [400, 400, 400, False], str(W["form_switch"]))
            v_ = W["view_as"]
            check("F10 the owner sees a person's list as they will see it, taps off, every weekly and monthly line shown for his eye; his own "
                  "page sends him to the console and he gets no staff tile", v_["ok"] and v_["view_as"] and v_["on"] is False and v_["name"] == "Shivani"
                  and v_["can_tick"] and not any(v_["can_tick"]) and "week" in v_["secs"] and v_["month"] == ["reception.month_new_register"]
                  and W["owner_page"] == 200 and W["owner_line_show"] is False and W["owner_line_show_on"] is False and W["bad_as"] == 404, str(v_)[:300])
            check("F11 reading wrote nothing: the database is byte-identical after every page and door, and no tap table exists yet",
                  W["reads_wrote_nothing"] and W["tick_table_before"] == 0)
            check("F12 the owner's tap turns the lists on: one setting, when and by whom -- and the day they were FIRST turned on is kept",
                  W["on"] == dict(ok=True, on=True, by="manoj", since=True)
                  and re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\|manoj$", str(W["setting"])) is not None
                  and str(W["setting"]).split("|")[0] == W["first_on"], "%s %s %s" % (W["on"], W["setting"], W["first_on"]))
            L_ = W["lists"]
            check("F13 ON: each login has its own list and its tile shows; Alisha's and Shivani's are the same list; a login nobody named "
                  "has none and no tile", all(L_[u]["ok"] and L_[u]["has"] and L_[u]["show"] and L_[u]["page"] == 200 for u in ("shivani", "alisha", "reception", "shavez", "bhati", "sukhveer", "darpan", "amir"))
                  and L_["shivani"]["secs"] == L_["alisha"]["secs"] and L_["stranger"]["has"] is False and L_["stranger"]["show"] is False, str({u: (v["has"], v["show"]) for u, v in L_.items()}))
            want_first = sorted(k for k, v in ex.items() if k.startswith("reception.docterz_") and v[0] != "ERR")
            check("F14 the Docterz export lines head the reception's list AND Shavez's AND the shared login's when a report is missing",
                  all(sorted(x for x in (L_[u]["secs"].get("first") or []) + L_[u]["clear"] if x.startswith("reception.docterz_")) == want_first
                      for u in ("shivani", "reception", "shavez")), str({u: L_[u]["secs"].get("first") for u in ("shivani", "reception", "shavez")}))
            mth = dt.date.today().replace(day=1)
            wk = dt.date.today() - dt.timedelta(days=dt.date.today().weekday())
            check("F15 nothing stale: switched on today, a weekly tap line is on the list only if this week began today, a monthly one only "
                  "if this month did", (("week" in L_["shivani"]["secs"]) == (wk == dt.date.today())) and (("month" in L_["shivani"]["secs"]) == (mth == dt.date.today()))
                  and "bhati.petty_today" in (L_["bhati"]["secs"].get("open") or []), str(L_["shivani"]["secs"].keys()))
            t_ = W["ticks"]
            check("F16a a form post is not a tap: refused, and no tap table is made", W["form_tick"] == [400, 0], str(W["form_tick"]))
            check("F16 a tap: the person's own line, once -- a second tap changes nothing; another person's line, a counted line, the "
                  "owner and a login outside the queue are refused", t_["first"] == [200, "bhati", True] and t_["again"] == [200, "bhati", True]
                  and t_["other"] == 404 and t_["sql"] == 404 and t_["owner"] == 403 and t_["not_in_queue"] == 404
                  and W["sql_tried"] in [x for v_ in L_["shivani"]["secs"].values() for x in v_], "%s (counted line tried: %s)" % (t_, W["sql_tried"]))
            mo_ = W["month_on"]
            check("F16b switched on since the first of this month: this week's and this month's tap lines are on the list and can be tapped",
                  "reception.week_float" in (mo_["secs"].get("week") or []) and mo_["secs"].get("month") == ["reception.month_new_register"]
                  and mo_["can"] and all(mo_["can"]), str(mo_))
            check("F17 a shared line: whoever taps first stands; the desk-mate's tap is answered with the first one's name",
                  t_["shared"] == [200, "shivani"] and t_["shared_second"] == [200, "shivani", False], str(t_))
            check("F18 the tap table is made on the first tap; one row per line and period, the first tapper's name on it",
                  [[r_[0], r_[2]] for r_ in W["tick_rows"]] == [["bhati.petty_today", "bhati"], ["reception.week_float", "shivani"]]
                  and W["tick_rows"][0][1] == "D" + dt.date.today().isoformat() and W["tick_rows"][1][1] == "W%04d-%02d" % dt.date.today().isocalendar()[:2], str(W["tick_rows"]))
            check("F19b the done line carries the person's name as the clinic writes it", W["done_name"] == ["Bhati"], str(W["done_name"]))
            check("F19 after his tap Bhati's line reads done and cannot be tapped again; his open count falls by one",
                  W["bhati_after"].get("bhati.petty_today") == [True, False] and W["bhati_after"].get("bhati.petty_cash_match") == [False, True]
                  and W["bhati_open_after"][1] == W["bhati_open_after"][0] - 1, "%s %s" % (W["bhati_after"], W["bhati_open_after"]))
            check("F20 the owner's second tap turns the lists off again and the staff's list closes", W["off_again"] == [False, "off"], str(W["off_again"]))
            check("F20b off and on again: the first-on day does not move, and this week's and this month's lines are still on the list",
                  W["on_again"] == [True, ["reception.month_new_register"], True], str(W["on_again"]))
            P_ = W["periods"]
            wkl, mol, dyl = "reception.week_float", "reception.month_new_register", "bhati.petty_today"
            check("F21 NOTHING STALE, on fixed days (switched on Wed 07-Oct): the daily line lives from that day; the weekly line is not on the "
                  "list that week, begins Mon 12-Oct and is late from Tue 13-Oct; the monthly line begins 01-Nov and is late from 04-Nov",
                  P_["2026-10-07"][dyl] == [True, False] and P_["2026-10-08"][wkl] == [False, False] and P_["2026-10-12"][wkl] == [True, False]
                  and P_["2026-10-13"][wkl] == [True, True] and P_["2026-10-12"][mol] == [False, False] and P_["2026-11-01"][mol] == [True, False]
                  and P_["2026-11-03"][mol] == [True, False] and P_["2026-11-04"][mol] == [True, True], str({k: (v[wkl], v[mol]) for k, v in P_.items()}))
            body = lm[0]
            check("F22 no patient in any list: the made-up name is in none, and none of the phone numbers and bank references the database holds",
                  SENT not in body and not (set(re.findall(r"\d{9,}", body)) & secret))
            check("F23 the list's lines are plain words: no SQL, no table name, no error text reaches the staff", not re.search(
                r"SELECT|Error|no such|_sql|sqlite|\{n\}\s*$", " ".join(x for x in W["texts"] if "{n}" not in x and "{text}" not in x)), str(W["texts"])[:300])
            u_ = W["unread"]
            check("F25a ONE line of a list cannot be read: the list says it is NOT whole, and neither it nor the tile says all done",
                  u_[:4] == [True, True, True, 0] and u_[4] is True and "adhoori" in str(u_[5]) and "Sab ho gaya" not in str(u_[5]) and u_[6] is True, str(u_))
            b_ = W["behind"]
            check("F25b a line whose oldest item is older than the floor (its table is not one the floor is laid under) is said WITHOUT a count, "
                  "a day or a 'late'; the owner's line says older items are in it", b_["flag"] == [True] and b_["late"] == [False]
                  and len(b_["row"]) == 1 and b_["row"][0][1] is False and b_["row"][0][0] == AK.tidy(b_["hi"][0]) and "baaki" not in b_["row"][0][0]
                  and b_["en"][0].endswith("(includes items from before %s)" % AK.dm(O["floor"])), str(b_))
            check("F25d 'late' is the duty map's own rule: late on the day its allowed days are used up, not a day before",
                  W["edge"] == {"amir.salt_list": True, "amir.rate_entry": False}, str(W["edge"]))
            check("F25c the duties file unreadable = NO FLOOR: then no line of the map is shown at all (never an unfloored count), the list "
                  "says it is not whole, the tile stays hidden", W["no_extra"] == [True, False, True, 0, 0, False], str(W["no_extra"]))
            pb_, pg_ = W["partial"]["bad"], W["partial"]["good"]
            check("F25 the duty map unreadable (a bad pull): every list says it is NOT whole and the tile never says all done; with the map "
                  "back, the same login's list is whole again", pb_[0] is True and pb_[1] is True and pb_[3] is True and "adhoori" in str(pb_[4])
                  and pb_[5] is True and pg_[:4] == [True, False, True, False] and "adhoori" not in str(pg_[4]), str(W["partial"]))
        # the console's staff lines ARE the list's lines
        allp2 = AK.build_all(play2)
        blk, cur_ = {}, None
        for l in lines_of(snap0, "work"):
            if not l.get("sub") and str(l.get("href") or "").startswith("/finance/aaj?as="):
                cur_ = l["href"].split("=", 1)[1]
                blk[cur_] = []
            elif l.get("sub") and cur_:
                blk[cur_].append(l["text"].strip())
            elif not l.get("sub"):
                cur_ = None
        notes_ = ("To be tapped", "Tapped done")
        bad24 = []
        for lg_, got_ in blk.items():
            lst_ = AK.list_for(allp2, lg_)
            want_ = sorted(i["en"] for k_ in ("first", "open", "night", "week", "month") for i in lst_["sections"][k_]
                           if i["kind"] == "sql" and i["person"] in lst_["queues"] and not i.get("fact"))
            if sorted(x for x in got_ if not x.startswith(notes_) and "could not be checked" not in x and "older item" not in x) != want_:
                bad24.append((lg_, len(got_), len(want_)))
        check("F24 the console's staff lines ARE the list's lines: list by list, the same open lines in the owner's English (the two "
              "Docterz exports, which the console says as facts of its own, are not said twice)", blk and not bad24, str(bad24))
        hid_ = {}
        for i in allp2["items"]:
            if i["kind"] == "sql" and not i["err"] and i["person"] != "manoj" and i["n_all"] > i["n"]:
                for lg_ in blk:
                    if i["person"] in AK.list_for(allp2, lg_)["queues"]:
                        hid_[lg_] = hid_.get(lg_, 0) + i["n_all"] - i["n"]
        check("F26 what the floor keeps off a person's list is SAID under that person on the console, with its number (%s)" % (hid_ or "nothing hidden on this box"),
              all(any(re.match(r"^%d older items? (is|are) kept off this list" % n_, x) for x in blk[lg_]) for lg_, n_ in hid_.items())
              and all(not any("older item" in x for x in v_) for lg_, v_ in blk.items() if lg_ not in hid_), str({k: [x for x in v if "older" in x] for k, v in blk.items()}))
        fu0 = [l for l in lines_of(snap0, "work") if "Follow-up log of" in l["text"]]
        check("F27 a missing Docterz export is said ONCE on the console (the fact line), and carries its weight on the tile as before",
              len(fu0) == 1 and not fu0[0].get("sub") and T["work_not_done"] == sum(1 for l in lines_of(snap0, "work") if l.get("dot") == "b" and not l.get("sub")
                                                                                   and not str(l.get("href") or "").startswith("/finance/aaj?as=")), str([l["text"] for l in fu0]))

        if full:
            penv = dict(env, PYTHONDONTWRITEBYTECODE="1", TMPDIR=env["TMPDIR"])
            rc1, o1 = run([py, "-B", os.path.join(kit, "reading_s487.py"), "mounted", fin, play2], env=penv, cwd=scr, timeout=200)
            before = arg("--finance")
            rc2, o2 = run([py, "-B", os.path.join(kit, "reading_s487.py"), "mounted", before, play2], env=penv, cwd=scr, timeout=200)
            check("F28 the installer's mount proof says YES for the edited app and NO for the app as it is before the install (so its "
                  "yes after placing means something)", rc1 == 0 and o1.strip().splitlines()[-1].startswith("MOUNT OK")
                  and rc2 == 1 and o2.strip().splitlines()[-1].startswith("MOUNT RED"), "%s || %s" % (o1.strip()[-200:], o2.strip()[-200:]))
            check("F28b ... and it left the database it read, and the code it loaded, as they were", md5f(play2) == mp2
                  and not [x for x in os.listdir(env["TMPDIR"]) if x.startswith("s487_mount_")])

        # ============================================================ nothing live moved
        live_after = {k: v for k, v in listing(finance).items() if k.endswith((".py", ".html")) and os.sep not in k}
        check("Z1 no file of the box's own finance code changed during the walk (%d files copied, none written)" % n, live_after == live_before,
              str(sorted(k for k in set(live_after) | set(live_before) if live_after.get(k) != live_before.get(k))[:5]))
        check("Z2 the box's portal.py did not change during the walk", md5f(portal) == portal_before)
    except Exception as e:                                             # noqa: BLE001
        import traceback
        traceback.print_exc()
        check("the walk ran to its end", False, "%s: %s" % (type(e).__name__, e))
    finally:
        if "--keep" in sys.argv:
            print("  note scratch kept: %s" % scr)
        else:
            shutil.rmtree(scr, ignore_errors=True)
    print("WALK_S487 %s %d checks, %d fail" % ("GREEN" if not FAILS else "RED", len(CHECKS), len(FAILS)))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
