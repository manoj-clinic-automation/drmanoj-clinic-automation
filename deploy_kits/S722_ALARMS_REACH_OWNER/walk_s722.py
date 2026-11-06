#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_s722.py -- S722_ALARMS_REACH_OWNER: the walk, on made-up rows in a scratch folder of its own (year 2099 never needed: the times are
given), with stubs instead of a phone.  No network, no live database, no file outside its own temp folder.

    python3 -B walk_s722.py <dir holding owner_notice.py, reports_watch.py, marg_door.py>

Run on the TO files: every check green.  Run on the FROM (live) files: the S722 checks go red (the CONTROL) -- a walk that stays green
on the old files proves nothing.
"""
import datetime as dt
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import types

SRC = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
TMP = tempfile.mkdtemp(prefix="walk_s722_")
SEEN = os.path.join(TMP, "medical_seen.json")
STUB = os.path.join(TMP, "notice_stub.jsonl")
os.environ["S722_SEEN_FILE"] = SEEN
os.environ["OWNER_NOTICE_STUB"] = STUB
os.environ["OWNER_NOTICE_LOCK"] = os.path.join(TMP, "lock")
os.environ["FINANCE_OFF_DIR"] = os.path.join(TMP, "_off")
os.environ["REPORTS_WATCH_OFF_DIR"] = os.path.join(TMP, "_off")
os.environ.pop("REPORTS_NTFY_STUB", None)
os.environ.pop("ORDER_PUSH_STUB", None)
os.environ.pop("ORDER_PUSH_NONE", None)
for n in ("owner_notice.py", "reports_watch.py", "marg_door.py"):
    shutil.copy(os.path.join(SRC, n), os.path.join(TMP, n))
sys.path.insert(0, TMP)

# stand-ins the real modules import (the page's judgement, the hand-change watch, the Marg reader) -- never the live ones
rt = types.ModuleType("reports_tile")
rt.STATUS = {"day": "2099-01-01", "due_day": "2099-01-01", "rows": []}
rt.status = lambda con, day=None, now=None: rt.STATUS
rt.owner_lists = lambda con, today: []
sys.modules["reports_tile"] = rt
mh = types.ModuleType("marg_hand_change")
mh.refresh = lambda con: None
mh.message_groups = lambda con, since, now: {}
sys.modules["marg_hand_change"] = mh
mt = types.ModuleType("marg_take")
mt.MAX_BYTES = 1000000
mt.counts = lambda: {"total": 1, "verified": 1, "today": 0}
mt.take = lambda raw, name="", source="manual": dict(status="TAKEN", md5="a" * 32, type="SALE_BILLWISE", variant="", verdict="VERIFIED",
                                                    lines=1, kept=0, stamp="", date_from="", date_to="", name=name, reason="")
sys.modules["marg_take"] = mt

import owner_notice as ON   # noqa: E402
import reports_watch as RW  # noqa: E402
RW.CONF = os.path.join(TMP, "no_ntfy.conf")                 # never the box's freshness.conf: no walk can reach the ntfy topic

FAILS = []
S722 = []


def ck(name, cond, s722=True):
    print(("  ok   " if cond else "  FAIL ") + ("[S722] " if s722 else "") + name)
    if not cond:
        FAILS.append(name)
        if s722:
            S722.append(name)


IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def at(d, h, m):
    return dt.datetime(2026, 11, d, h, m, tzinfo=IST)     # 01-Nov-2026 is a Sunday; 06-Nov a Friday


def db():
    con = sqlite3.connect(os.path.join(TMP, "scratch.db"))
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS mi_file (md5 TEXT PRIMARY KEY, type TEXT, verdict TEXT, reason TEXT, received_at TEXT, "
                "server_name TEXT, source TEXT)")
    con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('owner_notice.since', '2026-11-01 00:00:00', 'walk')")
    con.commit()
    return con


def seen(stamp, waiting=None, first=None):
    with open(SEEN, "w", encoding="utf-8") as fh:
        json.dump({"at": stamp, "first_at": first or stamp, "how": "beat", "waiting": waiting}, fh)


def medical(con, now):
    if not hasattr(ON, "_part_medical"):
        return []
    return ON._part_medical(con, now)


def stub_lines():
    try:
        with open(STUB, encoding="utf-8") as fh:
            return [json.loads(x) for x in fh if x.strip()]
    except OSError:
        return []


con = db()
ON.ensure(con)

# ---- 1. the medical PC's silence -------------------------------------------------------------------------------------------------------
ck("no beat ever: nothing is said (the medical half not yet installed)", medical(con, at(6, 12, 0)) == [] and not os.path.exists(SEEN), False)
seen("2026-11-06T10:00:00+05:30", 0)
ck("silent 19 minutes: nothing", medical(con, at(6, 10, 19)) == [], False)
m = medical(con, at(6, 10, 20))
ck("silent 20 minutes inside the window: Medical PC offline, once per silence (its key is the last sign of life)",
   len(m) == 1 and m[0]["key"] == "medical_off:2026-11-06 10:00:00" and m[0]["title"] == "Medical PC offline")
ck("its words", bool(m) and m[0]["body"] == "Nothing from the medical PC since 10:00. Reports made on it now wait there until it is back. "
                                           "Check that it is switched on and its internet works.")
seen("2026-11-05T20:29:00+05:30", 0)
ck("not heard today: nothing at 09:30 or 10:59 (the PC is usually switched on 09:15-10:50)",
   medical(con, at(6, 9, 30)) == [] and medical(con, at(6, 10, 59)) == [], False)
m = medical(con, at(6, 11, 0))
ck("not heard today by 11:00: offline, the day named", len(m) == 1 and "since 05-11 20:29." in m[0]["body"])
seen("2026-11-06T00:10:00+05:30", 0)
ck("left on past midnight (a beat at 00:10): not 'heard today' -- nothing at 09:30, said at 11:00 (the review)",
   medical(con, at(6, 9, 30)) == [] and len(medical(con, at(6, 11, 0))) == 1)
seen("2026-11-06T08:30:00+05:30", 0)
ck("heard at 08:30, then silent: nothing at 09:00, said at 11:00", medical(con, at(6, 9, 0)) == [] and len(medical(con, at(6, 11, 0))) == 1)
seen("2026-11-06T19:50:00+05:30", 0)
ck("19:50 + 20 min falls after 20:00: nothing (the window has closed)", medical(con, at(6, 20, 10)) == [], False)
ck("... and nothing at night", medical(con, at(6, 23, 30)) == [], False)
seen("2026-11-01T12:30:00+05:30", 0)
ck("a Sunday inside its half day (13:00): offline", len(medical(con, at(1, 13, 0))) == 1)
seen("2026-11-01T13:50:00+05:30", 0)
ck("a Sunday after 14:00: nothing", medical(con, at(1, 14, 30)) == [], False)

# ---- 2. the tick: the offline row once, then back with the reports delivered ---------------------------------------------------------
open(STUB, "w").close()
seen("2026-11-05T20:29:00+05:30", 0)
r = ON.tick(con, at(6, 11, 0))
ck("the tick makes and sends it (the walk's stub stands for the phone)", r.get("ok") and any(x["title"] == "Medical PC offline" for x in stub_lines()))
ON.tick(con, at(6, 11, 5))
ck("said once: the next tick sends nothing new", sum(1 for x in stub_lines() if x["title"] == "Medical PC offline") == 1)
seen("2026-11-06T11:49:00+05:30", 2)
con.execute("INSERT INTO mi_file VALUES ('m1', 'SALE_BILLWISE', 'VERIFIED', '', '2026-11-06T11:49:30+05:30', 'x', 'push')")
con.execute("INSERT INTO mi_file VALUES ('m2', 'STOCK_CLOSING', 'VERIFIED', '', '2026-11-06T11:50:10+05:30', 'y', 'push')")
con.execute("INSERT INTO mi_file VALUES ('m0', 'STOCK_CLOSING', 'VERIFIED', '', '2026-11-05T19:00:00+05:30', 'z', 'push')")
con.execute("INSERT INTO mi_file VALUES ('m9', 'SALE_BILLWISE', 'VERIFIED', '', '2026-11-06T11:51:00+05:30', 'w', 'drive')")
con.execute("INSERT INTO mi_file VALUES ('m8', '', 'REFUSED', 'the medical PC refused it', '2026-11-06T11:51:30+05:30', '', 'push')")
con.commit()
ck("heard again but 2 still waiting, 5 minutes after its first beat back: not yet",
   not [x for x in medical(con, at(6, 11, 54)) if x["kind"] == "medical_back"])
mb = [x for x in medical(con, at(6, 12, 5)) if x["kind"] == "medical_back"]
ck("15 minutes after its first beat back: back, with what is still waiting",
   len(mb) == 1 and mb[0]["body"] == "Back at 11:49 after 15 h 20 min. 2 reports delivered since: Sale report, Closing stock. "
                                      "2 reports still waiting to be sent.")
seen("2026-11-06T11:52:00+05:30", 0, "2026-11-06T11:49:00+05:30")
mb = [x for x in medical(con, at(6, 11, 53)) if x["kind"] == "medical_back"]
ck("nothing waiting: back at once -- its first beat back, the gap, the reports pushed since (not the drive copy, not yesterday's, not a refusal note)",
   len(mb) == 1 and mb[0]["key"] == "medical_back:2026-11-05 20:29:00" and mb[0]["title"] == "Medical PC back ✓"
   and mb[0]["body"] == "Back at 11:49 after 15 h 20 min. 2 reports delivered since: Sale report, Closing stock.")
ON.tick(con, at(6, 11, 55))
ON.tick(con, at(6, 12, 0))
ck("the tick sends it once", sum(1 for x in stub_lines() if x["title"] == "Medical PC back ✓") == 1)
seen("2026-11-06T15:00:00+05:30", 0)
m = medical(con, at(6, 15, 25))
ck("a new silence later: a new offline message", [x["key"] for x in m] == ["medical_off:2026-11-06 15:00:00"])
ON.tick(con, at(6, 15, 25))
seen("2026-11-06T15:40:00+05:30", 0)
mb = [x for x in medical(con, at(6, 15, 45)) if x["kind"] == "medical_back"]
ck("back with nothing waiting and nothing pushed: said plainly", len(mb) == 1 and mb[0]["body"] == "Back at 15:40 after 40 min. No report was waiting on it.")
ON.tick(con, at(6, 15, 45))
seen("2026-11-06T15:50:00+05:30", 0)
ON.tick(con, at(6, 16, 10))
seen("2026-11-06T16:30:00+05:30", 3, "2026-11-06T16:12:00+05:30")
mb = [x for x in medical(con, at(6, 16, 30)) if x["kind"] == "medical_back"]
ck("a count stuck above 0 and nothing pushed: back 15 minutes after its first beat back, saying what still waits",
   len(mb) == 1 and mb[0]["body"] == "Back at 16:12 after 22 min. No report delivered yet. 3 reports still waiting to be sent.")
ck("the tap opens the command console", ON._payload("medical_off:x", "t", "b")["url"] == "/finance/console", False)
with open(SEEN, "w") as fh:
    fh.write("{not json")
ck("a spoiled note: nothing said, nothing raised", medical(con, at(6, 16, 30)) == [], False)
os.makedirs(os.path.join(TMP, "_off"), exist_ok=True)
open(os.path.join(TMP, "_off", "OWNER_NOTICE_OFF"), "w").close()
ck("the switch file stops it", ON.tick(con, at(6, 16, 30)).get("off") == "OWNER_NOTICE_OFF", False)
os.remove(os.path.join(TMP, "_off", "OWNER_NOTICE_OFF"))

# ---- 3. the morning-report alarm goes by owner_notice's road --------------------------------------------------------------------------
open(STUB, "w").close()
RW._is_live = lambda c: True                                   # the walk's connection stands for the live one; the stub stands for the phone
ok, how = RW._send(con, "Morning reports 05-11", "Closing stock of 05-11 has not come by 10:00.")
ck("reports_watch's message goes the clinic-app road (owner_notice.deliver; here its stub)",
   ok and how == "stub" and stub_lines() and stub_lines()[-1]["title"] == "Morning reports 05-11")
rt.STATUS = {"day": "2026-11-06", "due_day": "2026-11-05",
             "rows": [{"key": "SALE_BILLWISE", "pair": True, "state": "ok", "s500": {}},
                      {"key": "STOCK_CLOSING", "pair": True, "state": "due", "s500": {"wrong": 0}}]}
open(STUB, "w").close()
r = RW.tick(con, at(6, 10, 0))
ln = stub_lines()
ck("the 10:00 alarm: one message, titled without a second 'Sanjeevni' (owner_notice adds it), the old words",
   r.get("sent") == 1 and len(ln) == 1 and ln[0]["title"] == "Morning reports 05-11"
   and ln[0]["body"] == "Closing stock of 05-11 has not come by 10:00. The sale report is right.")
ck("stamped sent, so the page says 'khabar chali gayi hai'", bool(RW.told(con, "2026-11-06").get("STOCK_CLOSING")), False)
saved = sys.modules.pop("owner_notice")
sys.modules["owner_notice"] = None                            # owner_notice cannot be imported: the old road is the fallback
ok, how = RW._send(con, "t", "b")
ck("owner_notice unimportable: the ntfy road stays the fallback (here: no NTFY_URL on this machine)", (not ok) and "NTFY_URL" in how, False)
sys.modules["owner_notice"] = saved
os.environ["ORDER_PUSH_NONE"] = "1"
ck("a walk's push stub still sends nothing", RW._send(con, "t", "b")[0] is False, False)
del os.environ["ORDER_PUSH_NONE"]
ON_STUB = os.environ.pop("OWNER_NOTICE_STUB")
ok, how = ON.deliver(sqlite3.connect(":memory:"), "reports:x", "t", "b")
ck("no message leaves a database that is not the live one", ok is False and "not the live database" in how, False)
os.environ["OWNER_NOTICE_STUB"] = ON_STUB

# ---- 4. the Marg door records the medical PC's beat ------------------------------------------------------------------------------------
try:
    import flask                                               # noqa: E402
    os.environ["FINANCE_MARG_TOKEN"] = "walk-token-not-a-secret"
    import marg_door as MD                                     # noqa: E402
    app = flask.Flask("walk")
    MD.init(app, lambda: None, lambda *a, **k: None)
    cl = app.test_client()
    if os.path.exists(SEEN):
        os.remove(SEEN)
    cl.get("/finance/api/marg-file", headers={"X-Finance-Marg": "wrong", "X-Marg-Beat": "MEDICAL waiting=1"})
    ck("a wrong key: no note written", not os.path.exists(SEEN))
    cl.get("/finance/api/marg-file", headers={"X-Finance-Marg": "walk-token-not-a-secret"})
    ck("a plain 'are you there?' with no beat (any other caller): no note", not os.path.exists(SEEN))
    r = cl.get("/finance/api/marg-file", headers={"X-Finance-Marg": "walk-token-not-a-secret", "X-Marg-Beat": "MEDICAL waiting=3"})
    d = json.load(open(SEEN)) if os.path.exists(SEEN) else {}
    ck("the medical PC's beat: noted with its waiting count, the answer unchanged (READY)",
       r.status_code == 200 and r.get_json().get("status") == "READY" and d.get("how") == "beat" and d.get("waiting") == 3
       and d.get("at", "").endswith("+05:30"))
    if os.path.exists(SEEN):
        r = cl.get("/finance/api/marg-file", headers={"X-Finance-Marg": "walk-token-not-a-secret", "X-Marg-Beat": "MEDICAL waiting=0"})
    d2 = json.load(open(SEEN)) if os.path.exists(SEEN) else {}
    ck("a beat soon after another keeps the first beat after the gap", d2.get("first_at") == d.get("first_at") and d2.get("waiting") == 0)
    r = cl.get("/finance/api/marg-file", headers={"X-Finance-Marg": "walk-token-not-a-secret", "X-Marg-Beat": "MEDICAL waiting=\u00b2"})
    d3 = json.load(open(SEEN)) if os.path.exists(SEEN) else {}
    ck("a beat whose count is not plain digits: answered 200, noted with no count", r.status_code == 200 and d3.get("waiting", "x") is None)
    if os.path.exists(SEEN):
        os.remove(SEEN)
    r = cl.post("/finance/api/marg-file", headers={"X-Finance-Marg": "walk-token-not-a-secret"},
                data={"name": "report.XLS", "source": "pc", "f": (open(__file__, "rb"), "report.XLS")}, content_type="multipart/form-data")
    ck("a file from another sender: no note", r.status_code == 200 and not os.path.exists(SEEN), False)
    r = cl.post("/finance/api/marg-file", headers={"X-Finance-Marg": "walk-token-not-a-secret"},
                data={"name": "MEDICAL__20261106-114900__REPORT_1__abcd1234.XLS", "source": "push",
                      "f": (open(__file__, "rb"), "x.XLS")}, content_type="multipart/form-data")
    ck("a file the medical PC pushed writes no note -- only a beat does, so the old pusher cannot start the messages (the review's blocker)",
       r.status_code == 200 and not os.path.exists(SEEN), False)
    cl.get("/finance/api/marg-file", headers={"X-Finance-Marg": "walk-token-not-a-secret", "X-Marg-Beat": "MEDICAL waiting=1"})
    ck("a beat's count is read only as digits", hasattr(MD, "_s722_beat") and MD._s722_beat("MEDICAL waiting=x") is None
       and MD._s722_beat("MEDICAL") is None and MD._s722_beat("MEDICAL waiting=12") == 12)
    ON2 = ON._s722_seen() if hasattr(ON, "_s722_seen") else None
    ck("owner_notice reads the door's note", ON2 is not None and ON2[1] == 1)
except ImportError as e:
    ck("flask is here for the door's part of the walk (%s)" % e, False, False)

shutil.rmtree(TMP, ignore_errors=True)
print("walk_s722: %d check(s) failed (%d of them S722 checks)" % (len(FAILS), len(S722)))
sys.exit(1 if FAILS else 0)
