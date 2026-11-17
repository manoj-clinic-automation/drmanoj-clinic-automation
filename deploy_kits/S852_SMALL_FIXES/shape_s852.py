#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""shape_s852.py -- kit S852_SMALL_FIXES (S474, 17-Nov-2026). The LIVE-SHAPE check, on COPIES of the live databases.

    python shape_s852.py <new_dir> <old_dir> <finance_db_copy> <assets_db_copy> <work_dir> <duty_map.json>

1. his console built from the live files and from the new files, each on its own copy (the Scan App left out of both, so
   F-1418's change does not show here): every section the same, but the approve-days line's detail and the timing line.
2. month_read's Scan App groups, live vs new, for this month and the two before, on the copy of the Scan App's database:
   no group and no lane ever gains (the change only takes papers out or takes a credit note off); the differences counted.
Prints no name, no ID, no patient. The last line is "SHAPE OK n/n" or "SHAPE RED ..."."""
import datetime as dt
import json
import os
import shutil
import subprocess
import sys

NEW, OLD, FDB, ADB, WORK, DUTY = sys.argv[1:7]
os.makedirs(WORK, exist_ok=True)
PROBE = r'''
import sys, os, json
code, db, out, what = sys.argv[1:5]
sys.path.insert(0, code)
if what == "console":
    import owner_console as oc
    s = oc.build(db, out)
    sec = s.get("sections") or {}
    print(json.dumps({k: [[l.get("text"), l.get("who") if "to approve" in str(l.get("text")) else None] for l in (v.get("lines") or [])] for k, v in sec.items()}))
else:
    import month_read as MR
    res = {}
    for ym in what.split(","):
        g = MR._scan_groups({"assets": db}, ym)
        res[ym] = dict(groups={k: list(v) for k, v in g["groups"].items()}, lanes={k: list(v) for k, v in g["lanes"].items()}, nph=len(g["ids"]))
    print(json.dumps(res))
'''
open(os.path.join(WORK, "probe.py"), "w").write(PROBE)
RES = []


def run(code, tag, src, what):
    db = os.path.join(WORK, tag + ".db")
    shutil.copyfile(src, db)
    env = dict(os.environ, DUTY_MAP_JSON=DUTY, CONSOLE_ASSETS_DB=os.path.join(WORK, "no_scanapp.db"),
               CONSOLE_SNAPSHOT=os.path.join(WORK, tag + ".snap"), PATIENTS_READING=os.path.join(WORK, tag + ".pat"))
    p = subprocess.run([sys.executable, "-W", "ignore", "-s", "-B", os.path.join(WORK, "probe.py"), code, db, os.path.join(WORK, tag + ".snap"), what],
                       capture_output=True, text=True, timeout=500, cwd="/tmp", env=env)
    if p.returncode != 0:
        print("SHAPE RED %s did not run: %s" % (tag, ((p.stderr or "").strip().splitlines() or ["?"])[-1][:200]))
        sys.exit(1)
    return json.loads(p.stdout.strip().splitlines()[-1])


a, b = run(OLD, "c_old", FDB, "console"), run(NEW, "c_new", FDB, "console")
for k in sorted(set(a) | set(b)):
    sa, sb = a.get(k) or [], b.get(k) or []
    if k == "system":
        RES.append(("system the same but the timing line", [x for x in sa if "took" not in str(x[0])] == [x for x in sb if "took" not in str(x[0])]))
    else:
        RES.append(("console section %s the same but the approve-days detail (%d lines)" % (k, len(sa)), [x[0] for x in sa] == [x[0] for x in sb]))
        appr = [x for x in sb if x[1] is not None]
        if k == "needs" and appr:
            RES.append(("the approve-days line says how long the oldest has waited", "the oldest has waited" in str(appr[0][1])))
t = dt.date.today()
yms = []
for i in range(3):
    y, m = t.year, t.month - i
    while m < 1:
        y, m = y - 1, m + 12
    yms.append("%04d-%02d" % (y, m))
mo, mn = run(OLD, "m_old", ADB, ",".join(yms)), run(NEW, "m_new", ADB, ",".join(yms))
gain, moved, gone = [], 0, 0.0
for ym in yms:
    for part in ("groups", "lanes"):
        for k, (n1, a1) in mn[ym][part].items():
            n0, a0 = mo[ym][part].get(k, (0, 0.0))
            if n1 > n0 or a1 > a0 + 0.005:
                gain.append("%s %s" % (ym, part))
            if part == "lanes":
                moved += n0 - n1
                gone += a0 - a1
        for k, (n0, a0) in mo[ym][part].items():
            if k not in mn[ym][part] and part == "lanes":
                moved += n0
                gone += a0
    RES.append(("%s: the pharmacy count never grows" % ym, mn[ym]["nph"] <= mo[ym]["nph"]))
RES.append(("no group and no lane gains in %s" % ", ".join(yms), not gain))
print("     the three months: %d papers no longer counted as money, Rs %.0f taken off in all" % (moved, gone))
bad = [n for n, c in RES if not c]
for n, c in RES:
    print(("ok   " if c else "RED  ") + n)
print("SHAPE OK %d/%d" % (len(RES), len(RES)) if not bad else "SHAPE RED %d/%d: %s" % (len(RES) - len(bad), len(RES), "; ".join(bad)))
sys.exit(0 if not bad else 1)
