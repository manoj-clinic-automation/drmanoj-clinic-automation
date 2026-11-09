#!/usr/bin/env python3
"""walk_s763.py -- kit S763_F802_AGAIN's walk, on a MADE-UP root (no live data, nothing leaves this machine).

usage: python walk_s763.py <code_dir> <bundle_root> [--control]
  code_dir     holds marg_watch.py, marg_door.py, amir_day.py, reports_tile.py, DUTY_MAP.json (the kit's out/, or the live src/ for the CONTROL)
  bundle_root  the nightly bundle's root/ (marg_ingest, finance) -- the other modules, read only
  --control    the live files: the S763 checks must go RED (exit 0 when every S763 check is red and every old check green)
"""
import importlib
import importlib.util
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
import types

CODE, BROOT = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
CONTROL = "--control" in sys.argv
RES = []          # (name, ok, is_s763)


def ck(name, cond, s763=True):
    RES.append((name, bool(cond), s763))
    print(("  OK   " if cond else "  RED  ") + {True: "[S763] ", False: "[old]  ", None: "[guard]"}[s763] + name)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


TMP = tempfile.mkdtemp(prefix="s763walk_")
DB = os.path.join(TMP, "finance.db")
os.environ["FINANCE_MARG_TOKEN"] = "walk-token-not-real"
os.environ["S722_SEEN_FILE"] = os.path.join(TMP, "medical_seen.json")
sys.path.insert(0, os.path.join(BROOT, "marg_ingest"))
sys.path.insert(1, os.path.join(BROOT, "finance"))
sys.path.insert(0, CODE)                         # the kit's (or live) files win over the bundle's copies

MI = importlib.import_module("marg_ingest")
MT = importlib.import_module("marg_take")
MI.DB_DEFAULT = DB
SALT = "SALT_WISE_ITEM_LIST"
A, B, C, X = "a" * 32, "b" * 32, "c" * 32, "d" * 32

con = MT._connect(DB)
for md5, typ, verdict, stamp, rec in ((A, SALT, "VERIFIED", "20261108-092800", "2026-11-08T09:28:00+05:30"),
                                      (B, SALT, "REFUSED", "20261109-090000", "2026-11-09T09:00:00+05:30"),
                                      (C, "SALE_BILLWISE", "VERIFIED", "20261109-091000", "2026-11-09T09:10:00+05:30")):
    con.execute("INSERT INTO mi_file (md5, type, verdict, stamp, received_at, drive_name, server_name) VALUES (?,?,?,?,?,?,?)",
                (md5, typ, verdict, stamp, rec, "MEDICAL__x.XLS", ""))
con.execute("CREATE TABLE IF NOT EXISTS purchase_salt_task (id INTEGER PRIMARY KEY, done INTEGER, done_at TEXT)")
con.execute("INSERT INTO purchase_salt_task (done, done_at) VALUES (1, '2026-11-09T10:00:00+05:30')")
con.commit()
con.close()

# ======================================================================== D · the door
print("D · the door (marg_door) on a made-up finance.db")
from flask import Flask                                                     # noqa: E402
door = load("marg_door", os.path.join(CODE, "marg_door.py"))
app = Flask("walk")
app.register_blueprint(door.bp)
cl = app.test_client()
H = {"X-Finance-Marg": "walk-token-not-real", "X-Marg-Note": "again"}


def post(body, headers=None, **kw):
    door._hits[:] = [] if hasattr(door, "_hits") else None
    r = cl.post("/finance/api/marg-file", data=json.dumps(body), content_type="application/json", headers=headers or H, **kw)
    try:
        return r.status_code, r.get_json() or {}
    except Exception:                                                        # noqa: BLE001
        return r.status_code, {}


def rows(sql, *a):
    c = sqlite3.connect(DB)
    try:
        return c.execute(sql, a).fetchall()
    except sqlite3.OperationalError:
        return None
    finally:
        c.close()


note = {"name": "MEDICAL__20261108-092800__report_TXT__aaaaaaaa.XLS", "md5": A, "at": "2026-11-01T13:31:00", "from": "report.txt"}
code, js = post(note)
ck("a re-receipt of a held VERIFIED salt list -> 200 AGAIN, 'received again, same as 20261108-092800'",
   code == 200 and js.get("status") == "AGAIN" and "received again, same as 20261108-092800" in str(js.get("message")))
ck("... one mi_receipt row, the PC's export time kept", (rows("SELECT md5, exported_at, source FROM mi_receipt") or []) == [(A, "2026-11-01T13:31:00", "push")])
ck("... the setting mi_again:SALT_WISE_ITEM_LIST = the PC's export time 2026-11-01 13:31:00",
   rows("SELECT value FROM setting WHERE key='mi_again:SALT_WISE_ITEM_LIST'") == [("2026-11-01 13:31:00",)])
ck("... mi_file's received_at NOT moved (the first receipt stays)", rows("SELECT received_at FROM mi_file WHERE md5=?", A) == [("2026-11-08T09:28:00+05:30",)], s763=None)
code, js = post(note)
ck("the same re-receipt within a minute -> AGAIN, recorded false, still one row",
   code == 200 and js.get("status") == "AGAIN" and js.get("recorded") is False and len(rows("SELECT 1 FROM mi_receipt") or []) == 1)
code, js = post(dict(note, at="2026-11-01T11:00:00"))
ck("a delayed re-receipt of an EARLIER export never moves the setting back",
   rows("SELECT value FROM setting WHERE key='mi_again:SALT_WISE_ITEM_LIST'") == [("2026-11-01 13:31:00",)])
code, js = post(dict(note, at="2099-01-01T00:00:00"))
v = (rows("SELECT value FROM setting WHERE key='mi_again:SALT_WISE_ITEM_LIST'") or [("",)])[0][0]
ck("a PC clock more than 10 min ahead of the server's -> recorded, counted false, the setting not moved",
   v == "2026-11-01 13:31:00" and js.get("counted") is False and js.get("status") == "AGAIN")
code, js = post({"name": note["name"], "md5": A, "from": "report.txt"})
v = (rows("SELECT value FROM setting WHERE key='mi_again:SALT_WISE_ITEM_LIST'") or [("",)])[0][0]
ck("a re-receipt with no export time -> recorded only, the setting not moved", v == "2026-11-01 13:31:00" and js.get("counted") is False)
code, js = post(dict(note, md5=X))
ck("an md5 the door does not hold -> UNKNOWN, nothing written",
   code == 200 and js.get("status") == "UNKNOWN" and len(rows("SELECT 1 FROM mi_receipt") or []) == 1)
code, js = post(dict(note, extra="x"))
ck("a re-receipt with another key -> 400 REFUSED", code == 400 and js.get("status") == "REFUSED", s763=None)
code, js = post(dict(note, md5="zz"))
ck("a re-receipt with a bad md5 -> 400 REFUSED", code == 400 and js.get("status") == "REFUSED", s763=None)
code, js = post(note, headers={"X-Finance-Marg": "wrong", "X-Marg-Note": "again"})
ck("the wrong key -> 401, nothing written", code == 401 and len(rows("SELECT 1 FROM mi_receipt") or []) == (0 if CONTROL else 1), s763=False)
door._hits[:] = []
r = cl.post("/finance/api/marg-file", headers=H, data={"f": (__import__("io").BytesIO(b"x" * 10), "a.XLS"), "md5": A},
            content_type="multipart/form-data")
ck("a re-receipt carrying a file -> 400 REFUSED", r.status_code == 400 and (r.get_json() or {}).get("status") == "REFUSED", s763=None)
code, js = post({"name": "report.txt", "md5": "e" * 32, "kind": "SALT", "reason": "walk"},
                headers={"X-Finance-Marg": "walk-token-not-real", "X-Marg-Note": "refused"})
ck("the S454 refusal note still answers NOTED", code == 200 and js.get("status") == "NOTED", s763=False)
r = cl.get("/finance/api/marg-file", headers={"X-Finance-Marg": "walk-token-not-real"})
ck("a GET still answers READY and writes no re-receipt", r.status_code == 200 and (r.get_json() or {}).get("status") == "READY"
   and len(rows("SELECT 1 FROM mi_receipt") or []) == (1 if not CONTROL else 0), s763=False)
code, js = post(dict(note, md5=B))
ck("a re-receipt of a REFUSED list answers its verdict REFUSED, counted false", code == 200 and js.get("verdict") == "REFUSED" and js.get("counted") is False)
code, js = post(dict(note, md5=C))
ck("... and a re-receipt of another type moves only its own key, never the salt key",
   rows("SELECT key FROM setting WHERE key LIKE 'mi_again:%' ORDER BY key") == [("mi_again:SALE_BILLWISE",), ("mi_again:SALT_WISE_ITEM_LIST",)]
   and js.get("counted") is True)

# ======================================================================== A · the salt duty (amir_day) and the duty map
print("A · the salt duty (amir_day) and DUTY_MAP on copies of the made-up db")
amir = load("amir_day", os.path.join(CODE, "amir_day.py"))
dmap = json.load(open(os.path.join(CODE, "DUTY_MAP.json"), encoding="utf-8"))
du = [d for d in dmap["duties"] if d["id"] == "amir.salt_list"][0]
ck("DUTY_MAP amir.salt_list due_sql == amir_day.DUTY_SQL, byte for byte", du["due_sql"] == amir.DUTY_SQL["amir.salt_list"], s763=False)
ck("DUTY_MAP is v21, kit S763_F802_AGAIN", dmap.get("version") == 21 and dmap.get("kit") == "S763_F802_AGAIN")
others = {d["id"]: d["due_sql"] for d in dmap["duties"] if d["id"] != "amir.salt_list"}


def copy_db(tag, receipts=None, drop=False):
    """receipts: [(type, the again-moment)] written as the door writes them; drop: a copy with no setting table at all."""
    p = os.path.join(TMP, "copy_%s.db" % tag)
    shutil.copy(DB, p)
    c = sqlite3.connect(p)
    if drop:
        c.execute("DROP TABLE IF EXISTS setting")
    else:
        c.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
        c.execute("DELETE FROM setting WHERE key LIKE 'mi_again:%'")
        for typ, at in (receipts or []):
            c.execute("INSERT OR REPLACE INTO setting (key, value) VALUES (?, ?)", ("mi_again:" + typ, at))
    c.commit()
    c.row_factory = sqlite3.Row
    return c


def due(c):
    return c.execute(amir.DUTY_SQL["amir.salt_list"]).fetchone()[0]


c0 = copy_db("none")
ck("a tick 10:00 after the list 08-Nov 09:28, no re-receipt -> due (1)", due(c0) == 1 and amir._s444_salt(c0)["pending"] is True, s763=False)
c1 = copy_db("again", [(SALT, "2026-11-09 13:31:05")])
ck("the same list received again 13:31 after the tick -> NOT due (0)", due(c1) == 0)
ck("... _s444_salt says fresh, last list 13:31", amir._s444_salt(c1)["pending"] is False and str(amir._s444_salt(c1)["last_list"]).startswith("2026-11-09 13:31"))
c2 = copy_db("before", [(SALT, "2026-11-09 09:50:00")])
ck("a re-receipt BEFORE the tick -> still due", due(c2) == 1, s763=False)
c3 = copy_db("other", [("SALE_BILLWISE", "2026-11-09 13:32:00")])
ck("a re-receipt of another report -> still due", due(c3) == 1, s763=False)
c4 = copy_db("old", drop=True)
s = amir._s444_salt(c4)
ck("a copy with no setting table (a bare test db) -> read as before: due, no error",
   s["pending"] is True and s["ticks"] == 1, s763=None)
c5 = copy_db("map", [(SALT, "2026-11-09 13:31:05")])
ck("the duty map's own due_sql run on the copy -> 0 (the generic runners: aaj_kaam, owner_console)",
   c5.execute(du["due_sql"]).fetchone()[0] == 0)
bad = []
for k, sql in others.items():
    try:
        c5.execute(sql).fetchall()
    except sqlite3.Error as e:
        if "no such table" not in str(e) and "no such column" not in str(e):
            bad.append((k, str(e)[:60]))
ck("every other duty of the map still prepares on the copy (only missing tables of the made-up db allowed)", not bad, s763=False)

# ======================================================================== R · the reports tile's salt row
print("R · reports_tile._salt_row")
tile = load("reports_tile", os.path.join(CODE, "reports_tile.py"))
r0 = tile._salt_row(copy_db("t0"), "2026-11-09")
ck("no re-receipt -> the salt row is DUE", r0 is not None and r0.get("state") == "due", s763=False)
r1 = tile._salt_row(copy_db("t1", [(SALT, "2026-11-09 13:31:05")]), "2026-11-09")
ck("the same list received again after the tick -> no salt row (not due, nothing new arrived today)", r1 is None)
r2 = tile._salt_row(copy_db("t2", drop=True), "2026-11-09")
ck("no setting table -> the row as before (due)", r2 is not None and r2.get("state") == "due", s763=False)

# ======================================================================== W · the medical PC's watcher
print("W · marg_watch on a made-up medical PC")
mw = load("marg_watch", os.path.join(CODE, "marg_watch.py"))
root = os.path.join(TMP, "pc")
watch = os.path.join(root, "users")
spool = os.path.join(root, "_captured")
os.makedirs(watch)
os.makedirs(spool)
LOG = []
out = LOG.append
mw.SETTLE_MS = 0
mw._marg_txt = lambda: types.SimpleNamespace(recognise=lambda raw: True)
mw._convert = lambda m, raw, when: (b"\xd0\xcf\x11\xe0XLS:" + raw.split(b"|")[0], {"version": "walk"})
mw.txt_live = lambda: True
has = hasattr(mw, "AGAIN_SINK")
if has:
    mw.AGAIN_SINK = []
captured = set()
rpt = os.path.join(watch, "report.txt")
T0 = time.time() - 6 * 3600


def export(body, t):
    with open(rpt, "wb") as fh:
        fh.write(body)
    os.utime(rpt, (t, t))


def sink():
    return list(getattr(mw, "AGAIN_SINK", None) or [])


export(b"SALT WISE ITEM LIST|printed 09:28", T0)
ck("the first export is TAKEN", mw.capture_text(rpt, spool, captured, out) is True, s763=False)
spf = [n for n in os.listdir(spool) if n.endswith(".XLS")]
os.utime(os.path.join(spool, spf[0]), (T0 + 5, T0 + 5))                    # captured 5 s after the export
ck("an unchanged file is not read again (nothing said, nothing sent)", mw.capture_text(rpt, spool, captured, out) is False and not sink(), s763=False)
export(b"SALT WISE ITEM LIST|printed 09:28", T0 + 4 * 3600)                 # 13:31 -- the SAME bytes, exported again
LOG.clear()
mw.capture_text(rpt, spool, captured, out)
v = mw.TXT_VERDICT.get(rpt, (0, ""))[1]
ck("the same bytes exported again -> ONE re-receipt for the server (F-802's case)",
   len(sink()) == 1 and sink()[0].get("md5") and sink()[0]["name"].startswith("MEDICAL__") and sink()[0]["name"].endswith(spf[0])
   and sorted(sink()[0]) == ["at", "from", "md5", "name"] and sink()[0]["at"].startswith(time.strftime("%Y-%m-%dT", time.localtime(T0 + 4 * 3600))))
ck("... the log says AGAIN (where the sender looks)", any("= AGAIN report.txt" in m for m in LOG))
ck("... the census verdict says 'same as an earlier export'", v.startswith("same as an earlier export"))
census = "\n".join(mw.text_census([watch]))
ck("... and text_census prints it", "same as an earlier export" in census)
d = os.path.join(root, "_captured_txt", "again")
ck("... the re-receipt is marked sent, none left waiting",
   os.path.isdir(d) and [n for n in os.listdir(d) if n.endswith(".sent")] and not [n for n in os.listdir(d) if n.endswith(".json")])
export(b"SALT WISE ITEM LIST|printed 15:40", T0 + 6 * 3600 - 60)            # other bytes, the same report
mw.capture_text(rpt, spool, captured, out)
ck("other bytes making the same report, exported later -> a second re-receipt", len(sink()) == 2)
# restart: the run's memory is gone; the spool and the again folder stay
for k in ("TXT_STAT", "TXT_VERDICT"):
    getattr(mw, k).clear()
mw.TXT_SEEN.clear()
if hasattr(mw, "TXT_DIGEST"):
    mw.TXT_DIGEST.clear()
captured2 = set(captured)
mw.capture_text(rpt, spool, captured2, out)
ck("a restart re-reading the file already told -> no new re-receipt", len(sink()) == 2)
export(b"SALT WISE ITEM LIST|printed 09:28", T0)                            # the very file the capture was taken from
for k in ("TXT_STAT", "TXT_VERDICT"):
    getattr(mw, k).clear()
mw.TXT_SEEN.clear()
mw.capture_text(rpt, spool, captured2, out)
v = mw.TXT_VERDICT.get(rpt, (0, ""))[1]
ck("a restart re-reading the file the capture was taken from -> nothing sent, said 'the file it was taken from'",
   len(sink()) == 2 and "the file it was taken from" in v)

# a copy this PC KEPT (a refused text offered again) is never an export
kept = os.path.join(root, "_captured_txt", "refused")
os.makedirs(kept, exist_ok=True)
kp = os.path.join(kept, "20261109-150000__report__x.txt")
with open(kp, "wb") as fh:
    fh.write(b"SALT WISE ITEM LIST|kept copy")
os.utime(kp, (T0 + 7 * 3600, T0 + 7 * 3600))
n0 = len(sink())
mw.capture_text(kp, spool, captured2, out)
ck("a refused copy offered again (in _captured_txt) -> no re-receipt, said 'not an export'",
   len(sink()) == n0 and "not an export" in mw.TXT_VERDICT.get(kp, (0, ""))[1])
ck("... and its refusal note is settled by retry_refused's words (the verdict starts 'same as an earlier export')",
   mw.TXT_VERDICT.get(kp, (0, ""))[1].startswith("same as an earlier export") and
   '"same as an earlier export")' in open(os.path.join(CODE, "marg_watch.py"), encoding="utf-8").read())
# the text reader ON HOLD: nothing told on its strength
was = mw.txt_live
mw.txt_live = lambda: False
export(b"SALT WISE ITEM LIST|printed 09:28", T0 + 8 * 3600)
mw.capture_text(rpt, spool, captured2, out)
ck("the text reader ON HOLD -> no re-receipt, said 'on hold'", len(sink()) == n0 and "on hold" in mw.TXT_VERDICT.get(rpt, (0, ""))[1])
mw.txt_live = was
# the Excel route: a salt list exported as Excel, byte for byte the same, later
xl = os.path.join(watch, "SALTLIST.XLS")
xbody = b"\xd0\xcf\x11\xe0" + b"salt" * 300
with open(xl, "wb") as fh:
    fh.write(xbody)
os.utime(xl, (T0, T0))
mw.looks_complete = lambda p: True
ck("an Excel export is captured as before", mw.capture(xl, spool, captured2, out) is True, s763=False)
mw.capture(xl, spool, captured2, out)
ck("... seen again unchanged (a restart, a poll) -> no re-receipt", len(sink()) == n0, s763=None)
os.utime(xl, (T0 + 9 * 3600, T0 + 9 * 3600))
mw.capture(xl, spool, captured2, out)
ck("the same Excel bytes exported again later -> ONE re-receipt", len(sink()) == n0 + 1 and sink()[-1]["md5"] == __import__("hashlib").md5(xbody).hexdigest())
mw.capture(xl, spool, captured2, out)
ck("... polled again unchanged -> no second", len(sink()) == n0 + 1)

# the sender's answers (no network: _again_send is replaced)
if has:
    mw.AGAIN_SINK = None
    os.makedirs(d, exist_ok=True)

    def queue(stem, age=0):
        p = os.path.join(d, stem + ".json")
        json.dump({"name": "MEDICAL__x.XLS", "md5": A, "at": "2026-11-09T13:31:00", "from": "report.txt"}, open(p, "w"))
        if age:
            os.utime(p, (time.time() - age, time.time() - age))
        return p

    def run(answer):
        mw._again_send = lambda note: answer
        mw._again_run(spool, out)

    p = queue("w1")
    run(("sent", {"status": "UNKNOWN"}))
    ck("UNKNOWN (the capture not on the server yet) -> it waits", os.path.exists(p))
    run(("wait", "sending is OFF (ALL_OFF.txt)"))
    ck("the switch OFF -> it waits", os.path.exists(p))
    run(("sent", {"status": "AGAIN", "message": "received again, same as 20261108-092800"}))
    ck("AGAIN -> marked sent, the log names the stamp", not os.path.exists(p) and os.path.exists(p[:-5] + ".sent")
       and any("the server has it -- received again, same as 20261108-092800" in m for m in LOG))
    p = queue("w2")
    run(("refused", "HTTP 400"))
    ck("400 -> marked gone, not tried again", os.path.exists(p[:-5] + ".gone"))
    pc = os.path.join(d, "w4.json")
    open(pc, "w").write("{not json")
    os.utime(pc, (time.time() - 4 * 86400, time.time() - 4 * 86400))
    run(("sent", {"status": "AGAIN"}))
    ck("an unreadable re-receipt older than 3 days -> marked gone, not tried for ever", os.path.exists(pc[:-5] + ".gone"))
    p = queue("w3", age=4 * 86400)
    run(("wait", "the server could not be reached"))
    ck("a re-receipt older than 3 days that cannot go -> expired, marked gone", os.path.exists(p[:-5] + ".gone"))
    # end to end: the watcher's note through the door's own code
    import urllib.request as _ur                                            # noqa: E402
    sent = []

    class _Resp(object):
        def __init__(self, b):
            self.b = b

        def read(self):
            return self.b

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_open(req, timeout=None, context=None):
        door._hits[:] = []
        hdr = {k: v for k, v in req.header_items()}
        sent.append(hdr)
        r = cl.post("/finance/api/marg-file", data=req.data, content_type="application/json",
                    headers={"X-Finance-Marg": hdr.get("X-finance-marg", ""), "X-Marg-Note": hdr.get("X-marg-note", "")})
        return _Resp(r.data)

    mp = types.SimpleNamespace(off_marker=lambda: None, token=lambda: "walk-token-not-real", URL="https://made-up/finance/api/marg-file",
                               _ctx=lambda: None)
    sys.modules["marg_push"] = mp
    real_open = _ur.urlopen
    _ur.urlopen = fake_open
    try:
        cx = sqlite3.connect(DB); cx.execute("DELETE FROM mi_receipt"); cx.execute("UPDATE setting SET value='' WHERE key LIKE 'mi_again:%'"); cx.commit(); cx.close()
        mw = load("marg_watch", os.path.join(CODE, "marg_watch.py"))         # a fresh _again_send, the stub transport above
        what, ans = mw._again_send({"name": "MEDICAL__x.XLS", "md5": A, "at": "2026-11-02T16:00:00", "from": "report.txt"})
    finally:
        _ur.urlopen = real_open
    ck("END TO END: the watcher's re-receipt through the door -> AGAIN, one mi_receipt row with the PC's export time",
       what == "sent" and ans.get("status") == "AGAIN" and sent and sent[0].get("X-marg-note") == "again"
       and rows("SELECT exported_at FROM mi_receipt WHERE md5=?", A) == [("2026-11-02T16:00:00",)]
       and rows("SELECT value FROM setting WHERE key='mi_again:SALT_WISE_ITEM_LIST'")[0][0] == "2026-11-02 16:00:00")
else:
    ck("UNKNOWN (the capture not on the server yet) -> it waits", False)
    ck("END TO END: the watcher's re-receipt through the door -> AGAIN, one mi_receipt row with the PC's export time", False)

shutil.rmtree(TMP, ignore_errors=True)
new = [r for r in RES if r[2] is True]
old = [r for r in RES if r[2] is not True]                 # old and guard checks: green on both the live and the kit's files
print("\n%d checks: %d S763 (%d green), %d old and guard (%d green)" % (len(RES), len(new), sum(r[1] for r in new), len(old), sum(r[1] for r in old)))
if CONTROL:
    good = all(not r[1] for r in RES if r[2] is True) and all(r[1] for r in RES if r[2] is not True)
    print("CONTROL " + ("RED as it must be (every S763 check red on the live files, every old check green)" if good else
                        "WRONG -- a S763 check is green on the live files or an old one red: " +
                        "; ".join(r[0] for r in RES if (r[2] is True and r[1]) or (r[2] is not True and not r[1]))))
    sys.exit(0 if good else 1)
ok = all(r[1] for r in RES)
print("WALK " + ("GREEN" if ok else "RED"))
sys.exit(0 if ok else 1)
