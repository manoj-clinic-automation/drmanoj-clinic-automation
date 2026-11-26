#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s960.py -- S960_EVENING_CHECK: remakes the two changed files from their LIVE bytes (F-472).
    python3 make_s960.py <docterz_pickup.py> <parchi_desk.py> <out_dir>
Each input must be its FROM (md5); every anchor must occur exactly once; the output is written to out_dir under the same name.
evening_check.py is NEW and is not made here (the kit carries it)."""
import hashlib
import os
import sys

def md5(b):
    return hashlib.md5(b).hexdigest()


def rep(s, old, new, what):
    n = s.count(old)
    if n != 1:
        raise SystemExit("ANCHOR %s found %d times -- refused" % (what, n))
    return s.replace(old, new)


DP_DOC_OLD = "THE ALARM: no consultation export for the last working day"
DP_DOC_NEW = ("S960 (S527, 26-Nov-2026, D1080 -- the Morning Match's evening check): a consultation report taken as the CURRENT one starts\n"
              "evening_check.py in its own process (_s960_evening): it reads the stored export at once and tells Shavez and reception which of\n"
              "the day's slips Docterz does not carry -- or that all are in. The take never waits for it and nothing there can fail the take;\n"
              "EVCHK_SPAWN=0 turns the start off. A second cron line picks up from Drive every minute 19:00-22:59 Mon-Sat and then runs\n"
              "evening_check.py --sweep, which judges an evening export no check judged (# S960_EVENING_PICKUP).\n"
              "THE ALARM: no consultation export for the last working day")
DP_IMP_OLD = "import sqlite3\nimport sys\n"
DP_IMP_NEW = "import sqlite3\nimport subprocess\nimport sys\n"
DP_FN_OLD = "def take(con, f, raw, dry=False):\n"
DP_FN_NEW = '''def _s960_evening(con, f):
    """S960 (D1080): start evening_check.py for this export in its own, fully detached process -- never waited for, never a
    reason for the take to fail. EVCHK_SPAWN=0 turns it off; EVCHK_PY names the python (the box's venv by default)."""
    if os.environ.get("EVCHK_SPAWN", "1") == "0":
        return False
    try:
        r = con.execute("SELECT id FROM docterz_export WHERE drive_id=? AND drive_mtime=?", (f["id"], f.get("modifiedTime") or "")).fetchone()
        path = con.execute("PRAGMA database_list").fetchone()[2]
        script = os.path.join(HERE, "evening_check.py")
        if r is None or not path or not os.path.isfile(script):
            return False
        py = os.environ.get("EVCHK_PY", "/root/wa/venv/bin/python3")
        if not os.path.isfile(py):
            py = sys.executable
        logd = os.path.join(HERE, "logs")
        os.makedirs(logd, exist_ok=True)
        env = dict(os.environ, EVCHK_LOGF=os.path.join(logd, "evening_check.log"))
        p = subprocess.Popen(["/bin/sh", "-c", '"$@" </dev/null >>"$EVCHK_LOGF" 2>&1 &', "s960", py, "-B", script,
                              "--export", str(int(r[0])), "--db", path], env=env, cwd=HERE, close_fds=True,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p.wait(timeout=10)
        return True
    except Exception:                                        # noqa: BLE001 -- the take never fails for this
        return False


def take(con, f, raw, dry=False):
'''
DP_CALL_OLD = '        if kind == "clinical" and st == "current":'
DP_CALL_NEW = ('        if kind == "consultation" and st == "current":       # S960 (D1080): the evening check, at once, in its own process\n'
               '            _s960_evening(con, f)\n'
               '        if kind == "clinical" and st == "current":')

PD_DOC_OLD = "No patient name, no number, no secret in this file (F-185).\n\"\"\""
PD_DOC_NEW = ("S960 (S527, 26-Nov-2026, D1080 -- the Morning Match's evening check): at the top of today's desk, once an evening Docterz\n"
              "export of today is here, evening_check.desk_box() -- the day's slips Docterz does not carry, each with \"Paise nahi liye\", the\n"
              "box re-reading itself every 30 seconds and showing only while the desk is on today; its two doors are mounted by init() below\n"
              "(a failure there is printed: 'evening_check NOT mounted'). Any fault in the box: the desk as it was.\n"
              "No patient name, no number, no secret in this file (F-185).\n\"\"\"")
PD_INIT_OLD = "    _db, _require, _audit, UNIT = db_getter, require_fn, audit_fn, unit\n    app.register_blueprint(bp)\n    return bp\n"
PD_INIT_NEW = ("    _db, _require, _audit, UNIT = db_getter, require_fn, audit_fn, unit\n    app.register_blueprint(bp)\n"
               "    try:                                                 # S960 (D1080): the evening check's two doors on the desk\n"
               "        import evening_check                             # noqa: PLC0415\n"
               "        evening_check.init(app, db_getter, require_fn, audit_fn, unit)\n"
               "    except Exception as _ex_s960:                        # noqa: BLE001 -- the desk as it was, and said\n"
               "        import sys as _sys                               # noqa: PLC0415\n"
               "        print(\"evening_check NOT mounted: %s\" % _ex_s960, file=_sys.stderr)\n"
               "    return bp\n")
PD_PAGE_OLD = ("    try:                                                 # S844 (F-1424): old slips with a name as the clinic ID, one tap to fix\n"
               "        html = html.replace('<div id=\"missing\"></div>', '<div id=\"missing\"></div>' + _s844_box(_s844_items(con), eng), 1)\n"
               "    except Exception:                                    # noqa: BLE001 -- the desk as it was\n"
               "        pass\n")
PD_PAGE_NEW = PD_PAGE_OLD + (
    "    try:                                                 # S960 (D1080): the evening check at the very top (shown on today only)\n"
    "        import evening_check                             # noqa: PLC0415\n"
    "        html = html.replace('<div id=\"missing\"></div>', '<div id=\"missing\"></div>' + evening_check.desk_box(con, eng), 1)\n"
    "    except Exception:                                    # noqa: BLE001 -- the desk as it was\n"
    "        pass\n")


def make(dp_path, pd_path, out, pins):
    dp, pd = open(dp_path, "rb").read(), open(pd_path, "rb").read()
    if md5(dp) != pins["docterz_pickup.py"]:
        raise SystemExit("docterz_pickup.py is %s, not its FROM %s -- refused" % (md5(dp)[:8], pins["docterz_pickup.py"][:8]))
    if md5(pd) != pins["parchi_desk.py"]:
        raise SystemExit("parchi_desk.py is %s, not its FROM %s -- refused" % (md5(pd)[:8], pins["parchi_desk.py"][:8]))
    s = dp.decode("utf-8")
    s = rep(s, DP_DOC_OLD, DP_DOC_NEW, "dp doc")
    s = rep(s, DP_IMP_OLD, DP_IMP_NEW, "dp import")
    s = rep(s, DP_FN_OLD, DP_FN_NEW, "dp fn")
    s = rep(s, DP_CALL_OLD, DP_CALL_NEW, "dp call")
    t = pd.decode("utf-8")
    t = rep(t, PD_DOC_OLD, PD_DOC_NEW, "pd doc")
    t = rep(t, PD_INIT_OLD, PD_INIT_NEW, "pd init")
    t = rep(t, PD_PAGE_OLD, PD_PAGE_NEW, "pd page")
    os.makedirs(out, exist_ok=True)
    for n, b in (("docterz_pickup.py", s), ("parchi_desk.py", t)):
        with open(os.path.join(out, n), "w", encoding="utf-8", newline="") as fh:
            fh.write(b)
        print("MADE %s %s" % (n, md5(b.encode("utf-8"))[:8]))


PINS = {"docterz_pickup.py": "a6cbdb8ba255c5f640aa402a653e401a",   # FROM, read from the 26-Nov bundle
        "parchi_desk.py": "1053255360f821e0007759edd9cf685b"}

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    make(sys.argv[1], sys.argv[2], sys.argv[3], PINS)
