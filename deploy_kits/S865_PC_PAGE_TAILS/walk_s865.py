#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s865.py -- kit S865_PC_PAGE_TAILS (S480, 18-Nov-2026). A walk on a MADE-UP root: the owner's Clinic PCs page opened
through Flask for every role (F-1445), the lab PC's card from made-up heartbeat and snapshot files, the biometric card's
new lines.    python3 walk_s865.py <code_dir> <work_dir>        last line "WALK n/m"."""
import datetime as dt
import json
import os
import shutil
import sys

CODE, WORK = sys.argv[1:3]
try:
    _ME = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _ME = None
sys.path[:] = [p for p in sys.path if not _ME or os.path.abspath(p or ".") != _ME]     # F-1441
sys.path[:0] = [CODE]
if os.path.isdir(WORK):
    shutil.rmtree(WORK)
os.makedirs(os.path.join(WORK, "kits"))
RES = []


def ok(name, cond, extra=""):
    RES.append(bool(cond))
    print("%s  %s%s" % ("PASS" if cond else "FAIL", name, ("  -- " + str(extra)[:240]) if extra else ""))


BEAT, IDX = os.path.join(WORK, "lab_heartbeat.json"), os.path.join(WORK, "snapshots.json")
os.environ.update(LAB_BEAT=BEAT, LAB_SNAP_INDEX=IDX, PC_KITS_ROOT=os.path.join(WORK, "kits"), PC_KIT_CODES=os.path.join(WORK, "codes.json"),
                  PC_KIT_LOG=os.path.join(WORK, "log.txt"), ATT_PUNCH_CSV=os.path.join(WORK, "punches.csv"),
                  ATT_STAFF_MASTER=os.path.join(WORK, "staff.csv"))
from flask import Flask, jsonify, request                                # noqa: E402
import pc_kits as pk                                                     # noqa: E402
app = Flask("walk865")


def require(*roles, unit=None):
    r = request.headers.get("X-Walk-Role", "")
    if r == "owner" and "checker" in roles:
        return dict(user="walkowner", role="checker"), None
    return None, (jsonify(ok=False, error="not_permitted"), 403)


HEALTH = {"checks": [dict(key="reception", label="Reception PC", state="ok", detail="walk reception"),
                     dict(key="watcher", label="Medical PC capture", state="ok", detail="walk medical"),
                     dict(key="pipeline", label="Pipeline heartbeat", state="ok", detail="walk pipeline")]}
pk.init(app, lambda: None, require, lambda con: HEALTH)
cl = app.test_client()
OPEN = dt.datetime(2026, 11, 18, 11, 0)          # a Wednesday, the lab open
SHUT = dt.datetime(2026, 11, 18, 23, 0)          # the same day, the lab shut
CLOCK = {"now": OPEN}
pk._ist_now = lambda: CLOCK["now"]


def beat(minutes_ago, attention=None):
    b = {"n": 1}
    if attention is not None:
        b["attention"] = attention
    json.dump({"received_ts": 0, "received_ist": (CLOCK["now"] - dt.timedelta(minutes=minutes_ago)).isoformat(timespec="seconds"),
               "from": "labpc", "beat": b}, open(BEAT, "w"))


def snaps(hours_ago, bad=False):
    d = {"labpc_x.zip": {"bytes": 12 * 1048576, "received_ist": (CLOCK["now"] - dt.timedelta(hours=hours_ago)).isoformat(timespec="seconds"),
                         "sha256": "x", "parts": 3, "from": "labpc"},
         "labpc_y.zip": {"bytes": 11 * 1048576, "received_ist": (CLOCK["now"] - dt.timedelta(hours=hours_ago + 3)).isoformat(timespec="seconds")}}
    if bad:
        d["zz_bad"] = {"bytes": "lots", "received_ist": "9999-garbage"}
    json.dump(d, open(IDX, "w"))


def card(html_text, label="Pathology lab PC"):
    i = html_text.find("<div class=pcn>%s</div>" % label)
    if i < 0:
        return ""
    j = html_text.find("<div class=pc>", i)
    return html_text[i:j if j > 0 else len(html_text)]


def lab():
    return card(cl.get("/finance/pcs", headers={"X-Walk-Role": "owner"}).get_data(as_text=True))


for role, want in (("owner", 200), ("maker", 403), ("viewer", 403), ("", 403)):
    r = cl.get("/finance/pcs", headers={"X-Walk-Role": role})
    ok("role %-6s: the Clinic PCs page %d" % (role or "none", want), r.status_code == want, r.status_code)
beat(4)
snaps(1)
page = cl.get("/finance/pcs", headers={"X-Walk-Role": "owner"}).get_data(as_text=True)
c = card(page)
ok("the lab PC has a card of its own (no longer 'Not set up yet')", c and "Not set up yet" not in c and "Labmate" in c, c[:200])
ok("open, heard 4 min ago, data 1 h ago: Working, with the heard time and 12.0 MB", "st ok" in c and "Working" in c and "12.0 MB" in c and "heard" in c, c[:300])
ok("its kit line names the lab agent kit", "INSTALL_LAB_AGENT.bat" in c)
ok("Shavez's PC still 'Not set up yet'", "Shavez" in page and "Not set up yet" in page)
ok("the other cards still read their health rows", "walk reception" in page and "walk medical" in page and "walk pipeline" in page)
snaps(10)
ok("heard, data 10 h ago (the overnight gap): still Working -- no morning false alarm (review 4)", "st ok" in lab())
snaps(30)
ok("heard, no data for 30 hours: Needs a look", "st warn" in lab())
snaps(1)
beat(4, attention=["walk text that must not show", "two"])
c = lab()
ok("heard, the PC reports 2 things: Needs a look, a count only, none of its text (review 3)", "st warn" in c and "reports 2 things" in c and "must not show" not in c, c[:250])
beat(90)
c = lab()
ok("open, silent 90 min: Needs a look, 'silent ... while the lab is open' (review 1)", "st warn" in c and "while the lab is open" in c, c[:200])
beat(240)
ok("open, silent 4 hours: Not working", "st bad" in lab())
CLOCK["now"] = SHUT
beat(180)
snaps(4)
c = lab()
ok("shut, not heard for 3 hours: 'switched off' (No report), not a fault", "st info" in c and "switched off" in c, c[:200])
beat(30 * 60)
ok("not heard for 30 hours: Needs a look", "st warn" in lab() and "not heard since" in lab())
CLOCK["now"] = OPEN
os.remove(BEAT)
c = lab()
ok("no heartbeat file: says so (No report)", "st info" in c and "no heartbeat" in c, c[:200])
open(BEAT, "w").write("{broken")
r = cl.get("/finance/pcs", headers={"X-Walk-Role": "owner"})
ok("a broken heartbeat file: the page still 200, the card says so", r.status_code == 200 and "no heartbeat" in card(r.get_data(as_text=True)))
beat(2)
snaps(2, bad=True)
c = lab()
ok("a bad entry in the snapshot index is skipped, the good one shown (review 5)", "st ok" in c and "12.0 MB" in c, c[:250])
os.remove(IDX)
c = lab()
ok("heard, no snapshot index: Needs a look, 'no Labmate data ... yet'", "st warn" in c and "no Labmate data" in c, c[:200])
HEALTH["checks"].append(dict(key="labpc", label="Lab PC", state="bad", detail="walk health lab"))
ok("lab_door's own health row (key labpc), once wired, wins (review 2)", "walk health lab" in lab())
HEALTH["checks"].pop()
pg = cl.get("/finance/pcs", headers={"X-Walk-Role": "owner"}).get_data(as_text=True)
ok("the biometric card: the 5-minute watch on the machine, the 13/14-Nov record, notes checked 18-Nov-2026",
   "attendance machine contact" in pg and "13/14-Nov-2026" in pg and "18-Nov-2026" in pg, "")
ok("no patient, number or key in the lab card", all(x not in card(pg) for x in ("sha256", "labpc_x", "token")))
print("WALK %d/%d" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
