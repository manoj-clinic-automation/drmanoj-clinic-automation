#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""shape_s854.py -- kit S854 (S477): the LIVE SHAPE on a COPY of finance.db (the installer runs it on the box).
   shape_s854.py <new dir> <old dir> <lib dir> <finance.db copy>
Counts only (no name, no ID). Last line "SHAPE OK n/m"."""
import importlib.util, os, sqlite3, sys
from collections import Counter
NEW, OLD, LIB, DB = sys.argv[1:5]
try:
    _ME = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _ME = None
BASE = [p for p in sys.path if not _ME or os.path.abspath(p or ".") != _ME]
res = []


def ok(nm, c, x=""):
    res.append(bool(c))
    print(("PASS " if c else "FAIL ") + nm + ("  -- " + str(x)[:160] if x else ""))


def load(d):
    sys.path[:] = [d, LIB] + BASE
    for m in ("slip_log", "check_screens", "records"):
        sys.modules.pop(m, None)
    import slip_log, records, check_screens                              # noqa: E401
    if check_screens.R is None:
        check_screens.attach(records)
    return slip_log, check_screens


con = sqlite3.connect(DB)                                   # a scratch COPY: the modules create their own tables on it
con.row_factory = sqlite3.Row
SLo, CSo = load(OLD)
old_pend = [r["msg_id"] for r in SLo.noid_pending(con)]
old_auto = {r["msg_id"]: SLo.noid_match(con, r["name"], r["received_at"]) for r in con.execute("SELECT * FROM lab_noid")}
old_filed = [i["key"] for i in CSo.filed_items(con)]
SLn, CSn = load(NEW)
new_pend = SLn.noid_pending(con)
ok("S391's automatic rule gives the same answer for every past report", all(SLn.noid_match(con, r["name"], r["received_at"]) == old_auto[r["msg_id"]]
                                                                           for r in con.execute("SELECT * FROM lab_noid")))
ok("every report the old list showed is still shown", set(old_pend) <= {r["msg_id"] for r in new_pend})
tiers = Counter()
for r in new_pend:
    c = SLn.noid_candidates(con, r["name"], r["received_at"])
    tiers["none" if not c else ("strong first" if c[0]["strong"] else "tier %d first" % c[0]["tier"])] += 1
    tiers["suggestions"] += len(c)
print("  unplaced reports listed: %d (the old list: %d) -- %s" % (len(new_pend), len(old_pend), dict(tiers)))
nf = CSn.filed_items(con)
ok("the X-ray part of 'Filed by themselves' is unchanged", [i["key"] for i in nf if not i.get("lab")] == [i for i in old_filed])
print("  lab reports on 'Filed by themselves' since 8-Nov: %d" % sum(1 for i in nf if i.get("lab")))
html = SLn._pend_blood_html(con, {"user": "shape", "roles": ["maker"]}, [], [], [])
ok("the reception card draws", "Report aayi, ID nahi likha" in html or not new_pend)
print(("SHAPE OK %d/%d" if all(res) else "SHAPE RED %d/%d") % (sum(res), len(res)))
sys.exit(0 if all(res) else 1)
