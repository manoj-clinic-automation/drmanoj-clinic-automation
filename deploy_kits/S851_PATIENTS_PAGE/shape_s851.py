#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""shape_s851.py -- kit S851_PATIENTS_PAGE (S474, 17-Nov-2026). The LIVE-SHAPE check, on a COPY of the live database.

    python shape_s851.py <new_dir> <old_dir> <db_copy> <work_dir>

1. builds his console from the live files and from the new files, each on its own copy of the database;
   every section must read the same, except the month section, which must gain exactly the one Patients line,
   and the system section's timing line.
2. builds the Patients reading from the copy: months from Jul 2026 to this month, the follow-up states adding
   up to the follow-ups given, and the reading must take under 30 seconds.
Prints nothing about any patient. The last line is "SHAPE OK n/n" or "SHAPE RED ...".
"""
import json, os, shutil, subprocess, sys, time

NEW, OLD, DB, WORK = sys.argv[1:5]
# the kit folder carries the new files too: keep it off the import path, so the CONTROL reads only what it is given
try:
    _ME = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _ME = None
sys.path[:] = [p for p in sys.path if not _ME or os.path.abspath(p or ".") != _ME]
os.makedirs(WORK, exist_ok=True)
PROBE = r'''
import sys, os, json
code, db, out = sys.argv[1:4]
sys.path.insert(0, code)
os.environ["CONSOLE_SNAPSHOT"] = out
os.environ["PATIENTS_READING"] = out + ".patients"
import owner_console as oc
s = oc.build(db, out)
sec = s.get("sections") or {}
print(json.dumps({k: [l.get("text") for l in (v.get("lines") or [])] for k, v in sec.items()}))
'''
open(os.path.join(WORK, "probe.py"), "w").write(PROBE)


def console(code, tag):
    db = os.path.join(WORK, tag + ".db")
    shutil.copyfile(DB, db)
    p = subprocess.run([sys.executable, "-W", "ignore", "-s", "-B", os.path.join(WORK, "probe.py"), code, db,
                        os.path.join(WORK, tag + ".snap")], capture_output=True, text=True, timeout=500, cwd="/tmp")
    if p.returncode != 0:
        print("SHAPE RED the console (%s) did not build: %s" % (tag, (p.stderr or "").strip().splitlines()[-1:]))
        sys.exit(1)
    return json.loads(p.stdout.strip().splitlines()[-1])


RES = []
a, b = console(OLD, "old"), console(NEW, "new")
for k in sorted(set(a) | set(b)):
    sa, sb = a.get(k) or [], b.get(k) or []
    if k == "month":
        add = [x for x in sb if x not in sa]
        RES.append(("month section gains only the Patients line", add == [x for x in add if x.startswith("Patients")]
                    and len(add) == 1 and [x for x in sa if x not in sb] == []))
        if len(add) != 1:
            print("     month lines: old %d, new %d, added %d" % (len(sa), len(sb), len(add)))
    elif k == "system":
        RES.append(("system section same but the timing line",
                    [x for x in sa if "took" not in x] == [x for x in sb if "took" not in x]))
    else:
        RES.append(("section %s the same (%d lines)" % (k, len(sa)), sa == sb))

sys.path.insert(0, NEW)
os.environ["PATIENTS_READING"] = os.path.join(WORK, "reading.dat")
import patients_page as P
db = os.path.join(WORK, "pp.db")
shutil.copyfile(DB, db)
t = time.time()
rd = P.build(db, os.path.join(WORK, "reading.dat"))
took = time.time() - t
months = [m.get("ym") for m in (rd.get("months") or [])]
RES.append(("reading months start Jul 2026 and reach this month (or last, early in a month)",
            bool(months) and months[0] == "2026-07" and months[-1] in (time.strftime("%Y-%m"),
                                                                       time.strftime("%Y-%m", time.localtime(time.time() - 5 * 86400)))))
fu_ok = bool(rd.get("fu"))
for f in rd.get("fu") or []:
    if sum(int(f.get(k) or 0) for k in ("kept", "med", "late", "neither", "open")) != int(f.get("due") or 0):
        fu_ok = False
RES.append(("follow-up states add up to the follow-ups given, every month", fu_ok))
RES.append(("reading took under 30 seconds (%.1f s)" % took, took < 30))
RES.append(("reading file is private (600)", oct(os.stat(os.path.join(WORK, "reading.dat")).st_mode & 0o777) == "0o600"))
bad = [n for n, c in RES if not c]
for n, c in RES:
    print(("ok   " if c else "RED  ") + n)
print("SHAPE OK %d/%d" % (len(RES), len(RES)) if not bad else "SHAPE RED %d/%d: %s" % (len(RES) - len(bad), len(RES), "; ".join(bad)))
sys.exit(0 if not bad else 1)
