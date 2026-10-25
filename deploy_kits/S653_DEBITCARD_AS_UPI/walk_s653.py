#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s653.py -- kit S653_DEBITCARD_AS_UPI (D788, F-1022). Runs the day check of EVERY day from 1-Oct-2026 to yesterday twice
-- the day_check.py under test and the live one -- on a THROW-AWAY COPY of the finance database (the check's own tick table is
created on first read, so the live database is never opened for writing). No patient name is printed.

  python3 walk_s653.py <dir with the day_check.py under test> <live finance dir> --db <finance.db> [--base <dir of the live
                       day_check.py, default the finance dir>] [--old]
D1 every 'Payment mode wrong' line the new file drops is a Docterz Debit Card -> UPI line (and there is at least one)
D2 every other line of every day is exactly as before (kind, key, amount, words)
D3 each day that dropped one carries the note, with the same count of bills
D4 no Debit Card the register holds as card is touched: no day gains or loses any other line, and the totals are unchanged
--old: the control on the live file -- D1 and D3 red, D2 and D4 green."""
import datetime as dt
import importlib.util
import os
import shutil
import sqlite3
import sys
import tempfile

argv = sys.argv[1:]
DB = None
if "--db" in argv:
    k = argv.index("--db")
    DB = argv[k + 1]
    del argv[k:k + 2]
BASE = None
if "--base" in argv:
    k = argv.index("--base")
    BASE = argv[k + 1]
    del argv[k:k + 2]
OLD = "--old" in argv
args = [a for a in argv if not a.startswith("--")]
TEST, FIN = os.path.abspath(args[0]), os.path.abspath(args[1])
DB = DB or os.path.join(FIN, "finance.db")
tmp = tempfile.mkdtemp(prefix="s653w")
copy = os.path.join(tmp, "f.db")
src = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
dst = sqlite3.connect(copy)
src.backup(dst)
src.close()
dst.close()
os.environ["FINANCE_DB"] = copy
sys.path.insert(0, FIN)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


NEWM = load(os.path.join(TEST, "day_check.py"), "dc_new")
OLDM = load(os.path.join(os.path.abspath(BASE) if BASE else FIN, "day_check.py"), "dc_old")
con = sqlite3.connect(copy)
con.row_factory = sqlite3.Row
d0, yday = dt.date(2026, 10, 1), dt.date.today() - dt.timedelta(days=1)
dropped, other_diff, note_bad, tot_diff, days = [], [], [], [], 0
while d0 <= yday:
    d = d0.isoformat()
    d0 += dt.timedelta(days=1)
    a, b = OLDM.check_day(con, d), NEWM.check_day(con, d)
    days += 1
    ka = {c["key"]: (c["kind"], c["amount"], c.get("en")) for c in a["cards"]}
    kb = {c["key"]: (c["kind"], c["amount"], c.get("en")) for c in b["cards"]}
    gone = [k for k in ka if k not in kb]
    new = [k for k in kb if k not in ka]
    changed = [k for k in ka if k in kb and ka[k] != kb[k]]
    for k in gone:
        if ka[k][0] == "mode" and k.endswith(":card:upi") and "Docterz Debit Card" in (ka[k][2] or ""):
            dropped.append((d, k))
        else:
            other_diff.append((d, k, "gone"))
    other_diff += [(d, k, "new") for k in new] + [(d, k, "changed") for k in changed]
    n_drop = sum(1 for x in dropped if x[0] == d)
    notes = [en for en, hi in b.get("notes", []) if "written as Debit Card" in en]
    if n_drop and not (len(notes) == 1 and ("(%d bill" % n_drop) in notes[0]):
        note_bad.append(d)
    if not n_drop and notes:
        note_bad.append(d)
    if a.get("totals") != b.get("totals") or a.get("state") != b.get("state"):
        tot_diff.append(d)
con.close()
shutil.rmtree(tmp, ignore_errors=True)
res = [("D1 every dropped 'Payment mode wrong' line is a Docterz Debit Card paid by UPI (%d line(s) over %d days)" % (len(dropped), days),
        bool(dropped), True),
       ("D2 every other line of every day is exactly as before", not other_diff, False),
       ("D3 each day that dropped one carries the note with its count of bills", bool(dropped) and not note_bad, True),
       ("D4 the day's totals and states are unchanged (Docterz is shown as recorded)", not tot_diff, False)]
for name, ok, _s in res:
    print("%s  %s" % ("green" if ok else "RED  ", name))
if other_diff:
    print("   other differences: %s" % ", ".join("%s %s %s" % (x[0], x[2], x[1].split(":")[0]) for x in other_diff[:10]))
if OLD:
    print("%d S653 check(s) red · %d older red · %d green" % (sum(1 for x in res if x[2] and not x[1]),
                                                                      sum(1 for x in res if not x[2] and not x[1]),
                                                                      sum(1 for x in res if x[1])))
else:
    print("%d of %d green" % (sum(1 for x in res if x[1]), len(res)))
