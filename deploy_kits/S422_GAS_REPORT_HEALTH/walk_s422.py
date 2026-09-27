#!/usr/bin/env python3
"""walk_s422.py -- the walk for kit S422_GAS_REPORT_HEALTH. Runs on COPIES only.
usage: walk_s422.py <kit_dir> <copy of finance_app.py> <copy of freshness_legs.json> [<dir holding freshness.py>]
Prints WALK OK n/n or WALK RED."""
import datetime as dt
import json
import os
import py_compile
import shutil
import sys
import tempfile

KIT, APP, LEGS = sys.argv[1], sys.argv[2], sys.argv[3]
FRESH_DIR = sys.argv[4] if len(sys.argv) > 4 else ""
sys.path.insert(0, KIT)
import apply_s422 as ap     # noqa: E402

N = [0, 0]
def check(name, cond, extra=""):
    N[1] += 1
    if cond:
        N[0] += 1; print("  ok  " + name)
    else:
        print("  RED " + name + " " + str(extra))

before = open(APP, encoding="utf-8", newline="").read()
legs_before = json.load(open(LEGS, encoding="utf-8"))
tmp = tempfile.mkdtemp(prefix="s422_")
gas = os.path.join(tmp, "gas")
os.makedirs(gas)
r1 = ap.patch_app(APP); r2 = ap.patch_legs(LEGS, gas)
check("first apply patches both", r1 == "patched" and r2 == "added", (r1, r2))
after = open(APP, encoding="utf-8", newline="").read()
check("the ONLY change to finance_app.py is the block, before the B2 marker",
      after.replace(ap.BLOCK, "", 1) == before and after.index(ap.BLOCK) + len(ap.BLOCK) == after.index(ap.MARK))
py_compile.compile(APP, doraise=True)
check("patched finance_app.py compiles", True)
check("second apply changes nothing", ap.patch_app(APP) == "already" and ap.patch_legs(LEGS, gas) == "already"
      and open(APP, encoding="utf-8", newline="").read() == after)
la = json.load(open(LEGS, encoding="utf-8"))
new = [l for l in la["legs"] if l["name"] == ap.LEG["name"]]
check("one new leg, every other leg byte-identical",
      len(new) == 1 and la["legs"][:-1] == legs_before["legs"] and la["_about"] == legs_before["_about"]
      and new[0]["target"] == gas + "/_DRIFT.json" and new[0]["kind"] == "file_mtime" and new[0]["max_age_h"] == 200)
if FRESH_DIR and os.path.isfile(os.path.join(FRESH_DIR, "freshness.py")):
    sys.path.insert(0, FRESH_DIR)
    try:
        import freshness as fr
        legs = fr.load_legs(LEGS, {"STATE_FILE": "/tmp/x"})
        mine = [l for l in legs if l.get("name") == ap.LEG["name"]]
        check("the box's own freshness.py accepts the new leg", len(mine) == 1 and not mine[0].get("bad"), mine)
    except Exception as e:  # noqa: BLE001
        check("the box's own freshness.py accepts the new leg", False, repr(e))

# ---- the block itself, run as _health_state runs it
src = "def _h(add, os, dt, json, CONF):\n" + ap.BLOCK.replace('"/root/state_backup/clinic_state_backup.conf"', "CONF")
ns = {}
exec(compile(src, "s422_block", "exec"), ns)
conf = os.path.join(tmp, "clinic_state_backup.conf")
open(conf, "w").write("GAS_REPO_COPY=/x\nGAS_DIR=%s\n" % gas)
def run():
    rows = []
    ns["_h"](lambda *a, **k: rows.append(a), os, dt, json, conf)
    return rows
r = run()
check("never run: one info row", len(r) == 1 and r[0][0] == "gasdrift" and r[0][2] == "info" and "not written" in r[0][3], r)
dp = os.path.join(gas, "_DRIFT.json")
json.dump({"checked_at_ist": "2026-09-27 02:20:05 IST", "since_last_run": [],
           "against_repository": [{"label": "UPIReconciliation", "kind": "no_copy", "file": ""},
                                  {"label": "X", "kind": "changed_whitespace", "file": "a.gs"}]}, open(dp, "w"))
r = run()
check("clean (no_copy and whitespace-only ignored): ok", r[0][2] == "ok" and "2026-09-27 02:20" in r[0][3], r)
json.dump({"checked_at_ist": "2026-09-27 02:20:05 IST",
           "since_last_run": [{"label": "UPIReconciliation", "kind": "changed", "file": "Code.gs"}],
           "against_repository": [{"label": "UPIReconciliation", "kind": "changed", "file": "Code.gs"},
                                  {"label": "DailyClinicReports", "kind": "changed_shape", "file": "Code.gs"},
                                  {"label": "UPIReconciliation", "kind": "added", "file": "New.gs"}]}, open(dp, "w"))
r = run()
check("findings: info, each file named once, the assistant's job", r[0][2] == "info" and r[0][3].startswith("3 file(s)")
      and "UPIReconciliation/New.gs" in r[0][3] and "Nothing for you" in r[0][4], r)
old = (dt.datetime.now() - dt.timedelta(days=9)).timestamp(); os.utime(dp, (old, old))
r = run()
check("not run for 9 days: warn", r[0][2] == "warn" and "9 days" in r[0][3], r)
open(dp, "w").write("{not json")
r = run()
check("unreadable result: info 'could not be read', never an exception", r[0][2] == "info" and "could not be read" in r[0][3], r)
os.remove(conf)
shutil.rmtree(gas)
r = run()
check("no conf: falls back to /root/state_backup/gas and still answers", len(r) == 1 and r[0][0] == "gasdrift", r)
shutil.rmtree(tmp, ignore_errors=True)
print("WALK %s %d/%d" % ("OK" if N[0] == N[1] else "RED", N[0], N[1]))
sys.exit(0 if N[0] == N[1] else 1)
