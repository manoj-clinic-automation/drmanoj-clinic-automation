#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""backfill_s618.py -- kit S618_SCAN_QUALITY (brief 3.5): the last two weeks' pharmacy scans checked and turned upright. A KEYED, IDEMPOTENT
step: every pharmacy-lane scan since scan.redo_since (default 2026-10-08), not set aside, not a joined page, with no check of its CURRENT file
in scan_lie, goes through claude_reader.lie_pass -- the very function the Scan App calls after a reading. A second run finds nothing to do.
Run under the venv python (it has pypdf); bounded by the reader's own daily cap (cap(con)): it stops when the day's calls reach it.

    /root/wa/venv/bin/python3 -B backfill_s618.py --assetapp <folder holding the NEW claude_reader.py> --adb <assets.db> --uploads <uploads dir>
                                                  [--stub <json: {"<stored file>": {check answer}}>]   (the walk's synthetic scenes only)
Prints each scan (stamp, the word lie_pass gave), then 'BACKFILL S618: n scans -- checked c, turned t, failed f, skipped s; calls used u of
the cap k (before b)'. Never prints a key; never a bill image."""
import argparse
import datetime as dt
import json
import os
import sqlite3
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assetapp", required=True)
    ap.add_argument("--adb", required=True)
    ap.add_argument("--uploads", required=True)
    ap.add_argument("--stub", default="")
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]     # never import from the kit folder
    sys.path.insert(0, os.path.abspath(a.assetapp))
    import claude_reader as C                                 # noqa: E402
    if not hasattr(C, "lie_pass"):
        print("BACKFILL S618: claude_reader in %s has no lie_pass (the OLD file) -- nothing done" % a.assetapp)
        return 3
    if a.stub:
        stub = json.load(open(a.stub))

        def check_scan(path, db_path=None):
            v = stub.get(os.path.basename(path))
            return dict(v, model="stub") if v else None
        C.check_scan = check_scan
    con = sqlite3.connect(a.adb, timeout=60)
    con.row_factory = sqlite3.Row
    con.execute(C.LIE_DDL)
    con.commit()
    since = "2026-10-08"
    r = con.execute("SELECT value FROM settings WHERE key='scan.redo_since'").fetchone()
    if r and str(r[0] or "").strip():
        since = str(r[0]).strip()[:10]
    day = dt.datetime.now().strftime("%Y-%m-%d")
    cap, before = C.cap(con), C.calls_today(con)
    rows = con.execute("SELECT b.id, b.stamp_no, b.source_stored FROM bills b WHERE b.lane='pharmacy' AND substr(b.created_at,1,10)>=? "
                       "AND COALESCE(b.status,'')<>'rejected' AND b.page_of IS NULL AND COALESCE(b.subgroup,'') NOT IN ('personal','resume','patient_paper') "
                       "AND NOT EXISTS (SELECT 1 FROM scan_lie l WHERE l.bill_id=b.id AND l.file=b.source_stored AND l.model IS NOT NULL) ORDER BY b.id",
                       (since,)).fetchall()
    con.close()
    n = {"checked": 0, "turned": 0, "failed": 0, "skipped": 0}
    print("BACKFILL S618: since %s, %d pharmacy-lane scan(s) not set aside with no check of their file; the day's calls %d of the cap %d" % (since, len(rows), before, cap))
    for r in rows:
        c2 = sqlite3.connect(a.adb, timeout=60)
        used = C.calls_today(c2)
        c2.close()
        if used >= cap:
            print("   the day's cap reached (%d of %d) -- stopped; the rest is checked by the next run" % (used, cap))
            break
        w = C.lie_pass(a.adb, a.uploads, r["id"], who="server (S618 backfill)")
        k = w.split(":")[0]
        n[k if k in n else "failed"] += 1
        print("   %-8s %s" % (r["stamp_no"], w))
    c3 = sqlite3.connect(a.adb, timeout=60)
    after = C.calls_today(c3) if dt.datetime.now().strftime("%Y-%m-%d") == day else None
    c3.close()
    print("BACKFILL S618: %d scans -- checked %d, turned %d, failed %d, skipped %d; calls used %s of the cap %d (before %d)"
          % (len(rows), n["checked"] + n["turned"], n["turned"], n["failed"], n["skipped"], "?" if after is None else after - before, cap, before))
    return 0 if not n["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
