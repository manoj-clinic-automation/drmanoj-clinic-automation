#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s652.py -- kit S652_SHAVEZ_PROCROOM_LINE. READ-ONLY: the finance database is read mode=ro through aaj_kaam's Reader.

  python3 walk_s652.py <dir holding the aaj_seed.py + aaj_duties.json under test> <live finance dir> --db <finance.db>
                       --map <DUTY_MAP.json> --base <dir of the live two> [--old]      (internal: --dump)
P1 Shavez's list carries 'Kal ke procedures' as a fetch line on the Scan App's door (/scanapp/procroom/morning/api/open,
   field open, words from its text), opening /scanapp/procroom/morning, in his first section
P2 his list has no unread line
P3 every other line of every person's list (section, kind, words, order) is as before"""
import json
import os
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
KEY = "shavez|shavez.procroom_morning"


def rows():
    out = {}
    for k, doc in rd.people.items():
        lst = A.person_list(rd, doc, view_as=True)
        for sec, rs in lst["sections"].items():
            for i, r in enumerate(rs):
                out["%s|%s" % (k, r["id"])] = [sec, r["kind"], r["text"], i, json.dumps(r.get("fetch"), sort_keys=True),
                                              r.get("door")]
        out["%s|_unread" % k] = lst["unread"]
    return out


if DUMP:
    print(json.dumps(rows(), sort_keys=True, ensure_ascii=False))
    sys.exit(0)
res = []


def check(name, ok, s652=True, note=""):
    res.append((name, bool(ok), s652, note))


me = rows()
r = me.get(KEY)
f = json.loads(r[4]) if r and r[4] else {}
check("P1 Shavez's list: 'Kal ke procedures' is a fetch line on the Scan App's door, opening his morning page, in his first "
      "section", bool(r) and r[0] == "first" and r[1] == "fetch" and f.get("url") == "/scanapp/procroom/morning/api/open"
      and f.get("field") == "open" and f.get("text_field") == "text" and r[5] == "/scanapp/procroom/morning", True, str(r))
check("P2 his list has no unread line", me.get("shavez|_unread") == 0, False, str(me.get("shavez|_unread")))
tmp = tempfile.mkdtemp(prefix="s652o")
for fn in ("aaj_seed.py", "aaj_duties.json"):
    open(os.path.join(tmp, fn), "wb").write(open(os.path.join(BASE if not OLD else TEST, fn), "rb").read())
d = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), tmp, FIN, "--db", DB] + (["--map", MAP] if MAP else [])
                   + ["--dump"], capture_output=True, text=True, env=dict(os.environ, AAJ_DUTIES_JSON=os.path.join(tmp, "aaj_duties.json")))
try:
    them = json.loads(d.stdout)
    diff = [k for k in set(me) | set(them) if k != KEY and me.get(k) != them.get(k)]
    check("P3 every other line of every person's list (section, kind, words, order) is as before (%d)" % (len(me) - 1),
          not diff, False, ", ".join(sorted(diff))[:300])
except Exception:                                                       # noqa: BLE001
    check("P3 every other line of every person's list is as before", False, False, d.stderr[-300:])
finally:
    for fn in os.listdir(tmp):
        os.remove(os.path.join(tmp, fn))
    os.rmdir(tmp)
for name, ok, s6, note in res:
    print("%s  %s%s" % ("green" if ok else "RED  ", name, ("   [" + note + "]") if (note and not ok) else ""))
g = sum(1 for x in res if x[1])
if OLD:
    print("%d S652 check(s) red · %d older red · %d green" % (sum(1 for x in res if x[2] and not x[1]),
                                                                      sum(1 for x in res if not x[2] and not x[1]), g))
else:
    print("%d of %d green" % (g, len(res)))
