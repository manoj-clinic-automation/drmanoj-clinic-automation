#!/usr/bin/env python3
"""walk_s305.py -- on the box, BEFORE anything is placed: the new export_watch.py's selftest, then the old and
the new judge the last ten days against a SCRATCH copy of the live finance.db with the real punch file (read
only). Prints one line a day: punched, old verdict, new verdict, where the new evidence came from. Nothing
is stored. The last line is WALK OK / WALK RED.
    python3 -B walk_s305.py <old export_watch.py> <new export_watch.py> <scratch db>"""
import sys, subprocess, importlib.util, sqlite3, datetime as dt
OLD, NEW, DB = sys.argv[1:4]
def load(p, n):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
try:
    r = subprocess.run([sys.executable, "-B", NEW, "--selftest"], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0 and "0 failures" in r.stdout, "the selftest is not green: %s" % (r.stdout + r.stderr)[-300:]
    O, N = load(OLD, "ew_old"), load(NEW, "ew_new")
    con = sqlite3.connect(DB)
    today = N.ist_now().date()
    worse = 0
    for i in range(10, 0, -1):
        day = today - dt.timedelta(days=i)
        now = dt.datetime.combine(day + dt.timedelta(days=1), dt.time(10, 45))
        a, b = O.check(con, day, now=now), N.check(con, day, now=now)
        via = ",".join("%s:%s" % (k, v.get("via")) for k, v in sorted(b["have"].items()) if v.get("covers")) or "-"
        print("  %s punched=%s  old=%s%s  new=%s%s  (%s)" % (day, {True: "yes", False: "no", None: "?"}[b["punched"]], a["verdict"],
              ("/" + ",".join(a["missing"])) if a["missing"] else "", b["verdict"], ("/" + ",".join(b["missing"])) if b["missing"] else "", via))
        # the new watch may only ever know MORE: never a missing item the old one had as present
        worse += len(set(b["missing"]) - set(a["missing"]))
    assert worse == 0, "the new watch found something missing that the old one had"
    print("WALK OK selftest green; ten days judged, the new watch never less informed than the old")
except Exception as e:                                        # noqa: BLE001
    print("WALK RED %s: %s" % (type(e).__name__, e)); sys.exit(1)
