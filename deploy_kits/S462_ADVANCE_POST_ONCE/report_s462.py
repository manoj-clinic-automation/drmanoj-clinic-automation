#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""report_s462.py -- READ-ONLY. Does the Staff Ledger already hold a pharmacy salary advance twice?

F-706 could have posted one advance two times before this kit. This reads the ledger (and the finance database, read
only) and prints what it finds, in three lines at most per finding. It changes nothing and need not be run by hand:
the installer runs it once after it is green.      usage: report_s462.py <ledger.jsonl> <finance.db>
"""
import json
import sqlite3
import sys


def main():
    led, dbf = sys.argv[1], sys.argv[2]
    rows = []
    try:
        with open(led, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    except OSError as ex:
        print("the Staff Ledger was not read (%s)" % ex)
        return 0
    live = [r for r in rows if r.get("category") == "ADVANCE_ISSUE" and r.get("status") in ("APPROVED", "PENDING")
            and not r.get("contra_of") and "(finance expense #" in (r.get("narration") or "")
            and not any(x.get("contra_of") == r.get("id") and x.get("status") == "APPROVED"
                        and x.get("amount") == -r.get("amount", 0) for x in rows)]
    groups = {}
    for r in live:
        groups.setdefault((r.get("date_from"), r.get("amount")), []).append(r)
    dup = sorted((k, v) for k, v in groups.items() if len(v) > 1)
    print("advances the finance app has posted to the Staff Ledger, still live: %d" % len(live))
    if not dup:
        print("none of them is there twice for the same day and amount")
    for (d, amt), v in dup[:12]:
        print("POSSIBLE DOUBLE POSTING: %s  Rs %s  x%d  (entered %s)"
              % (d, amt, len(v), ", ".join(str(x.get("ts_entry"))[:16] for x in v)))
    if len(dup) > 12:
        print("... and %d more day(s)" % (len(dup) - 12))
    try:
        con = sqlite3.connect("file:%s?mode=ro" % dbf, uri=True)
        n = con.execute("SELECT COUNT(*) FROM day_expense x JOIN day_entry e ON e.id=x.day_entry_id "
                        "WHERE e.unit='medical' AND x.category_fixed='salary_advance' AND x.ledger_posted=0 "
                        "AND e.status IN ('approved','locked')").fetchone()[0]
        m = con.execute("SELECT COUNT(*) FROM day_expense x JOIN day_entry e ON e.id=x.day_entry_id "
                        "WHERE e.unit='medical' AND x.category_fixed='salary_advance' AND x.ledger_posted=1").fetchone()[0]
        print("pharmacy salary advances in the finance book: %d stamped as posted; %d on approved days with no stamp" % (m, n))
    except Exception as ex:                                          # noqa: BLE001
        print("the finance database was not read (%s)" % ex)
    return 0


if __name__ == "__main__":
    sys.exit(main())
