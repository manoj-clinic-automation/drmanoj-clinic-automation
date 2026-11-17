#!/usr/bin/env python3
"""shape_s846.py -- kit S846 (S474). The live-shape walk: the built files against the live ones on a COPY of the newest
database, counts only (no name, no ID, no number printed). With no answer marked, the day check and the money match must
come out exactly as the live files' do; the list's count and the console line are printed.
    python shape_s846.py <new_dir> <live_dir> <bundle_finance_dir> <db_copy> <days_back>"""
import datetime as dt
import importlib
import json
import shutil
import sqlite3
import sys

NEW, LIVE, BUNDLE, DBC, BACK = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])


def load(code):
    for m in ("day_check", "clinic_money", "owner_console", "parchi_desk", "not_in_docterz", "slip_log", "clinic_register"):
        sys.modules.pop(m, None)
    sys.path[:] = [code, BUNDLE] + [p for p in sys.path if p not in (NEW, LIVE, BUNDLE)]
    return importlib.import_module("day_check"), importlib.import_module("clinic_money")


def run(code, db):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    dc, cm = load(code)
    out = {}
    today = dt.date.today()
    for i in range(1, BACK + 1):
        d = (today - dt.timedelta(days=i)).isoformat()
        try:
            ck = dc.check_day(con, d)
            a = sorted((c.get("kind"), c.get("key"), c.get("amount")) for c in ck["cards"])
            n = len(ck["notes"])
        except Exception as ex:                    # noqa: BLE001
            a, n = "ERR %s" % type(ex).__name__, -1
        try:
            m = cm.match_day(con, d)
            b = (m["verdict"], sorted(f["code"] for f in m["flags"]), sorted(e["code"] for e in m["explained"]))
        except Exception as ex:                    # noqa: BLE001
            b = "ERR %s" % type(ex).__name__
        out[d] = (json.dumps(a, default=str), n, json.dumps(b))
    extra = None
    if code == NEW:
        nid = importlib.import_module("not_in_docterz")
        rr = nid.rows(con)
        oc = importlib.import_module("owner_console")
        ln = oc._s846_nid_line(con)
        extra = dict(rows=len(rr), by_kind={k: sum(1 for r in rr if r["kind"] == k) for k in ("opd", "xray", "proc")},
                     days=len({r["day"] for r in rr}), oldest=min((r["day"] for r in rr), default=None),
                     console=(ln or {}).get("text"), no_amount=sum(1 for r in rr if not r["amount_p"]))
    con.close()
    return out, extra


a = DBC + ".live"
b = DBC + ".new"
shutil.copyfile(DBC, a)
shutil.copyfile(DBC, b)
lo, _x = run(LIVE, a)
no, ex = run(NEW, b)
same = 0
for d in sorted(lo):
    s = lo[d] == no[d]
    same += s
    print("%s  %s  cards/notes/money %s" % (d, "SAME" if s else "DIFFERENT", "" if s else (lo[d][1], no[d][1])))
print("days the same: %d/%d" % (same, len(lo)))
print("the list on the copy:", json.dumps(ex))
sys.exit(0 if same == len(lo) else 1)
