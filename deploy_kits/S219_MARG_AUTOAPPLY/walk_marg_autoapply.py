#!/usr/bin/env python3
"""
walk_marg_autoapply.py -- S219 M1, THE LIVE-SHAPE WALK.

Runs the shipped helper bytes against the REAL database, on the owner's own
machine, and answers the two questions a selftest cannot:

  1. does the summary agree with what the system already believes about a day?
  2. how much NOISE would the continuity check make on real history?

A check that would flag two hundred old gaps is not a check, it is a new
source of alarm fatigue -- and only real data can say which it is.

READ-ONLY BY CONSTRUCTION: it works on a COPY of the database, taken to a
temp directory OUTSIDE the mounted folders (F-268: sqlite never writes inside
the mount).  The live database is opened only to be copied.

USAGE:
    python3 -B walk_marg_autoapply.py <patched_finance_app.py> <finance.db>
"""
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile


def load_helpers(path):
    src = open(path, encoding="utf-8").read()
    start = src.index("# ============================================================================\n#  S219 M1 -- MARG AUTO-APPLY")
    end = src.index('def _replay_pending_marg_for_day(con, iso, by="auto"):')
    # the sliced functions rely on finance_app's module-level imports
    ns = {"UNIT": "medical", "re": re, "json": json,
          "setting": lambda con, k, d=None: d}
    for frag in ('def marg_net_sql(alias="sale_item"):', "def rupees(p):"):
        blk = src[src.index(frag):]
        exec(compile(blk[:blk.index("\n\n\n")], frag, "exec"), ns)
    exec(compile(src[start:end], "s219_helpers", "exec"), ns)
    return ns


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    app_py, live_db = sys.argv[1], sys.argv[2]
    for p in (app_py, live_db):
        if not os.path.exists(p):
            print("!! not found: %s" % p)
            return 2
    ns = load_helpers(app_py)
    summary, cont = ns["_marg_apply_summary"], ns["_marg_continuity_check"]

    tmpd = tempfile.mkdtemp(prefix="s219_walk_")
    db = os.path.join(tmpd, "walk.db")
    shutil.copyfile(live_db, db)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    try:
        days = [r["business_date"] for r in con.execute(
            "SELECT DISTINCT d.business_date FROM day_entry d "
            "JOIN sale_item s ON s.day_entry_id=d.id "
            "WHERE d.unit='medical' AND s.source_ref IS NOT NULL "
            "ORDER BY d.business_date")]
        print("days carrying Marg bills: %d  (%s .. %s)"
              % (len(days), days[0] if days else "-", days[-1] if days else "-"))

        print("\n--- 1 · THE SUMMARY on the last 10 such days")
        print("    (net is cross-checked against the day's own sale_item sum)")
        agree = disagree = 0
        for iso in days[-10:]:
            s = summary(con, iso)
            if not s:
                print("    %s  NO SUMMARY (day not filed)" % iso)
                continue
            eid = con.execute("SELECT id FROM day_entry WHERE unit='medical' "
                              "AND business_date=?", (iso,)).fetchone()["id"]
            ref = con.execute(
                "SELECT COALESCE(SUM(CASE WHEN COALESCE(service,'') LIKE '%return%' "
                "THEN -amount_p ELSE amount_p END),0) p FROM sale_item "
                "WHERE day_entry_id=?", (eid,)).fetchone()["p"]
            ok = (ref == s["net_p"])
            agree += ok
            disagree += (not ok)
            print("    %s %s" % ("ok " if ok else "!! ", s["line"]))
        print("    net agrees on %d day(s), disagrees on %d" % (agree, disagree))

        print("\n--- 2 · THE CONTINUITY CHECK over ALL history (rolled back)")
        con.execute("BEGIN")
        total, flagged = 0, []
        for iso in days:
            g = cont(con, iso)
            total += len(g)
            for x in g:
                flagged.append((iso, x["series"], x["missing"], x["prev_date"]))
        con.rollback()
        print("    days walked           : %d" % len(days))
        print("    gap flags it WOULD raise: %d" % total)
        if flagged:
            print("    the first 15:")
            for iso, ser, miss, prev in flagged[:15]:
                print("      %s  series %-3s  %4d bill(s) missing since %s"
                      % (iso, ser or "(none)", miss, prev))
            by_series = {}
            for _iso, ser, miss, _p in flagged:
                by_series[ser] = by_series.get(ser, 0) + miss
            print("    total missing bills by series: %s"
                  % ", ".join("%s=%d" % (k or "(none)", v)
                              for k, v in sorted(by_series.items())))
        print("\n    VERDICT: %s"
              % ("quiet on real history -- ships as a flag"
                 if total <= 2 else
                 "TOO NOISY -- raise marg.bill_gap_min before shipping"))

        print("\n--- 3 · nothing was written")
        n = con.execute("SELECT COUNT(*) c FROM data_flag "
                        "WHERE code='MARG_BILL_RANGE_GAP'").fetchone()["c"]
        print("    MARG_BILL_RANGE_GAP rows in the copy after rollback: %d" % n)
        print("    (the live database was only ever read, and only to copy it)")
    finally:
        con.close()
        shutil.rmtree(tmpd, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
