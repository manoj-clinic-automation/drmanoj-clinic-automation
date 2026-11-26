#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_s962.py -- S962's live-shape probe: the day check on a database (a copy, or the live one read-only), counts only.
    python3 probe_s962.py <code_dir> <finance.db> <days>
Prints one line per day (counts and money only -- no name, no number, no clinic ID) and a last line
    PROBE days N checked C errors E cards K back B refunds R left_days L
Run it on the FROM code and on the TO code and compare."""
import datetime as dt
import os
import sqlite3
import sys

CODE, DBP, N = os.path.abspath(sys.argv[1]), sys.argv[2], int(sys.argv[3])
os.environ.setdefault("EVCHK_LIVE_DB", "/nonexistent/live.db")    # never the live database: nothing can push
sys.path.insert(0, CODE)
sys.dont_write_bytecode = True
import day_check as DC                                             # noqa: E402

DC.PUSHER = (lambda *a, **k: (0, "probe"))
con = sqlite3.connect("file:%s?mode=ro" % DBP, uri=True, timeout=10)
con.row_factory = sqlite3.Row
DC._done = True                                                    # read-only: never create anything
try:
    import clinic_register as CR                                   # noqa: E402
    CR._schema_done = True
except Exception:                                                  # noqa: BLE001
    pass
today = dt.date.today()
tot = dict(days=0, checked=0, errors=0, cards=0, back=0, refunds=0, left_days=0)
for i in range(1, N + 1):
    d = (today - dt.timedelta(days=i)).isoformat()
    tot["days"] += 1
    try:
        chk = DC.check_day(con, d)
        st = chk.get("state")
        kinds = {}
        for c in chk.get("cards") or []:
            kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
        try:
            for u in ({"user": "shavez", "roles": ["maker"]}, {"user": "manoj", "roles": ["checker"]}):
                DC.cards_html(con, chk, u, "checker" in u["roles"])
            html_ok = "html ok"
        except Exception as ex:                                    # noqa: BLE001
            html_ok = "HTML ERROR %s" % type(ex).__name__
            tot["errors"] += 1
        if st == "checked":
            tot["checked"] += 1
            tot["cards"] += len(chk["cards"])
            tot["back"] += len(chk.get("backdate") or [])
            tot["refunds"] += len(chk.get("refunds") or [])
            left = (chk.get("top") or {}).get("left")
            if left:
                tot["left_days"] += 1
            print("DAY %s %s cards %d %s back %s refunds %s left %s · %s · %s" % (
                d, st, len(chk["cards"]), ",".join("%s:%d" % kv for kv in sorted(kinds.items())),
                len(chk.get("backdate") or []) if "backdate" in chk else "-", len(chk.get("refunds") or []) if "refunds" in chk else "-",
                left if left is not None else "-", DC.summary_en(chk).split(": ", 1)[1], html_ok))
        else:
            print("DAY %s %s" % (d, st))
    except Exception as ex:                                        # noqa: BLE001
        tot["errors"] += 1
        print("DAY %s ERROR %s" % (d, type(ex).__name__))
print("PROBE days %(days)d checked %(checked)d errors %(errors)d cards %(cards)d back %(back)d refunds %(refunds)d left_days %(left_days)d" % tot)
