#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s650_lists.py -- kit S650_ATTCORR, the finance side (D786). READ-ONLY on the books: the finance database is read
mode=ro through aaj_kaam's own Reader; the console's piece reads a MADE-UP register database in a temp folder.

  python3 walk_s650_lists.py <dir holding the aaj_seed.py, aaj_duties.json and owner_console.py under test>
                             <live finance dir> --db <finance.db> --map <DUTY_MAP.json> --base <dir of the live three> [--old]
  (internal: --dump)

L1 reception's list carries the two new lines, as 'fetch' lines asking /register/attcorr/api/line, in her first section
L2 Shavez's list carries his check line the same way
L3 neither list has an unread line
L4 every other line of every person's list (section, kind, words) is as before
L5 the owner's console says nothing before reception saves, 'October ready -- approve & save' after, 'approved' after
   his approval (on a made-up register)
"""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile

argv = sys.argv[1:]


def opt(name):
    if name in argv:
        k = argv.index(name)
        v = argv[k + 1]
        del argv[k:k + 2]
        return v
    return None


DB, MAP, BASE = opt("--db"), opt("--map"), opt("--base")
OLD, DUMP = "--old" in argv, "--dump" in argv
args = [a for a in argv if not a.startswith("--")]
TEST, FIN = os.path.abspath(args[0]), os.path.abspath(args[1])
os.environ["AAJ_DUTIES_JSON"] = os.path.join(TEST, "aaj_duties.json")
if MAP:
    os.environ["DUTY_MAP_JSON"] = MAP
sys.path[:0] = [TEST, FIN]
import aaj_seed as S                                                    # noqa: E402
import aaj_kaam as A                                                    # noqa: E402
assert os.path.dirname(os.path.abspath(S.__file__)) == TEST, S.__file__
rd = A.Reader(DB)


def rows():
    out = {}
    for k, doc in rd.people.items():
        lst = A.person_list(rd, doc, view_as=True)
        for sec, rs in lst["sections"].items():
            for i, r in enumerate(rs):
                out["%s|%s" % (k, r["id"])] = [sec, r["kind"], r["text"], i, json.dumps(r.get("fetch"), sort_keys=True)]
        out["%s|_unread" % k] = lst["unread"]
    return out


if DUMP:
    print(json.dumps(rows(), sort_keys=True, ensure_ascii=False))
    sys.exit(0)

res = []


def check(name, ok, s650=True, note=""):
    res.append((name, bool(ok), s650, note))


me = rows()
NEW = ("reception|reception.attcorr_print", "reception|reception.attcorr_enter", "shavez|shavez.attcorr_check")


def fetch_ok(key, field):
    r = me.get(key)
    if not r or r[1] != "fetch":
        return False
    f = json.loads(r[4] or "null") or {}
    return f.get("url") == "/register/attcorr/api/line" and f.get("field") == field
p, e = me.get(NEW[0]), me.get(NEW[1])
check("L1 reception's list: 'print' and 'enter' are fetch lines on the register's door, at the top of her first "
      "section", fetch_ok(NEW[0], "print_open") and fetch_ok(NEW[1], "enter_open") and p[0] == e[0] == "first"
      and p[3] == 0 and e[3] == 1, str((p, e)))
check("L2 Shavez's list: 'Attendance correction check' is a fetch line on the register's door, in his first section",
      fetch_ok(NEW[2], "check_open") and me[NEW[2]][0] == "first", str(me.get(NEW[2])))
check("L3 neither reception's nor Shavez's list has an unread line",
      me.get("reception|_unread") == 0 and me.get("shavez|_unread") == 0,
      False, "%s %s" % (me.get("reception|_unread"), me.get("shavez|_unread")))
tmp = tempfile.mkdtemp(prefix="s650o")
for f in ("aaj_seed.py", "aaj_duties.json"):
    open(os.path.join(tmp, f), "wb").write(open(os.path.join(BASE if not OLD else TEST, f), "rb").read())
envd = dict(os.environ, AAJ_DUTIES_JSON=os.path.join(tmp, "aaj_duties.json"))
d = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), tmp, FIN, "--db", DB] + (["--map", MAP] if MAP else [])
                   + ["--dump"], capture_output=True, text=True, env=envd)
try:
    them = json.loads(d.stdout)
    skip = set(NEW)
    diff = []
    for k in set(me) | set(them):
        if k in skip:
            continue
        a, b = me.get(k), them.get(k)
        if k.startswith("reception|") and a and b and a[0] == "first":
            a, b = a[:3] + a[4:], b[:3] + b[4:]           # her first section moved down by the two new lines
        if a != b:
            diff.append(k)
    check("L4 every other line of every person's list (section, kind, words) is as before (%d)" % (len(me) - 3),
          not diff, False, ", ".join(sorted(diff))[:300])
except Exception:                                                       # noqa: BLE001
    check("L4 every other line of every person's list is as before", False, False, d.stderr[-300:])
finally:
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)

# ---- the owner's console, on a made-up register ----
REG = os.path.join(tempfile.mkdtemp(prefix="s650c"), "sr.db")
k = sqlite3.connect(REG)
k.execute("CREATE TABLE locked_run (ym TEXT PRIMARY KEY, total_payout INTEGER, report_html TEXT, locked_by TEXT, "
          "locked_ts TEXT, unlocked_by TEXT, unlocked_ts TEXT, unlock_reason TEXT, status TEXT)")
k.commit()
k.close()
os.environ["CONSOLE_REGISTER_DB"] = REG
sys.modules.pop("owner_console", None)
import owner_console as OC                                              # noqa: E402
OC.REGISTER_DB = REG
assert os.path.dirname(os.path.abspath(OC.__file__)) == TEST, OC.__file__


def console():
    sec = OC.sec_att(None, {"att": None, "today": "2026-11-02", "tile": {}, "att_err": "walk", "now": None})
    return [x for x in sec["lines"] if "Attendance correction" in (x.get("text") or "") or
            "Attendance correction" in json.dumps(x)]


c0 = console()
check("L5a before the staging tables exist the console says nothing about the corrections (and nothing breaks)",
      c0 == [], False, str(c0))
k = sqlite3.connect(REG)
k.executescript("""CREATE TABLE attcorr_day (reg_date TEXT, staff_id INTEGER, ym TEXT, mark TEXT, applied_mark TEXT);
CREATE TABLE attcorr_month (ym TEXT PRIMARY KEY, entered_by TEXT, entered_ts TEXT, checked_by TEXT, checked_ts TEXT,
 approved_by TEXT, approved_ts TEXT, n_applied INTEGER);
INSERT INTO attcorr_day VALUES ('2026-10-07', 1, '2026-10', 'P', NULL);
INSERT INTO attcorr_month(ym) VALUES ('2026-10');""")
k.commit()
c1 = console()
k.execute("UPDATE attcorr_month SET entered_by='alisha', entered_ts='2026-11-01 10:42:00'")
k.commit()
c2 = console()
k.execute("UPDATE attcorr_month SET approved_by='manoj', approved_ts='2026-11-02 08:10:00'")
k.execute("UPDATE attcorr_day SET applied_mark='P'")
k.commit()
c3 = console()
k.close()
check("L5b nothing before reception saves", c1 == [], False, str(c1))
check("L5c after reception saves: 'Attendance correction: October ready — approve & save', opening the owner's page",
      len(c2) == 1 and c2[0].get("dot") == "w" and "October ready" in c2[0].get("text", "")
      and "/register/attcorr?ym=2026-10" in json.dumps(c2[0]), True, str(c2))
check("L5d after his approval: green, 'approved by manoj'", len(c3) == 1 and c3[0].get("dot") == "g"
      and "approved by manoj" in c3[0].get("text", ""), True, str(c3))

for name, ok, s6, note in res:
    print("%s  %s%s" % ("green" if ok else "RED  ", name, ("   [" + note + "]") if (note and not ok) else ""))
g = sum(1 for x in res if x[1])
if OLD:
    print("%d S650 check(s) red · %d older red · %d green" % (sum(1 for x in res if x[2] and not x[1]),
                                                                      sum(1 for x in res if not x[2] and not x[1]), g))
else:
    print("%d of %d green" % (g, len(res)))
