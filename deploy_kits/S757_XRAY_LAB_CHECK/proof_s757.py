#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proof_s757.py -- what kit S757's screens would show today, read from a READ-ONLY copy of a finance database.
COUNTS ONLY: no name, no clinic ID, no file name is printed.

  python3 proof_s757.py <dir with the kit's records.py and check_screens.py> <finance.db>

The database is copied with SQLite's own backup into a private temp folder first and the copy is deleted at the end."""
import os
import shutil
import sqlite3
import sys
import tempfile
import time
from collections import Counter

KIT, SRC = sys.argv[1], sys.argv[2]
TMP = tempfile.mkdtemp(prefix="p757.")
os.chmod(TMP, 0o700)
DB = os.path.join(TMP, "proof.db")
s = sqlite3.connect("file:%s?mode=ro" % SRC, uri=True)
d = sqlite3.connect(DB)
s.backup(d)
d.close()
s.close()
sys.path.insert(0, os.path.abspath(KIT))
os.environ["RECORDS_DRIVE_STUB"] = TMP                   # nothing is fetched from Drive
try:
    import records                                       # noqa: E402
    import check_screens as cs                           # noqa: E402
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    t0 = time.time()
    xq = cs.xray_queue(con)
    t1 = time.time()
    lab = cs.lab_items(con)
    t2 = time.time()
    nox, filed, xb = cs.nox_items(con), cs.filed_items(con), cs.xbill_items(con)
    t3 = time.time()
    print("X-ray pictures waiting for staff: %d  (by month, newest first: %s)  [%.2f s]" % (
        len(xq), " · ".join("%s %d" % (m, n) for m, n in sorted(Counter(i["day"][:7] for i in xq).items(), reverse=True)), t1 - t0))
    tops, tags, sizes = 0, Counter(), []
    cache = {}
    rows = {r["src_id"]: r for r in cs._parked(con)}
    for i in xq:
        ps = cs.pick_list(con, rows[i["sid"]], cache)
        sizes.append(len([p for p in ps if not p["near"]]))
        if ps and ps[0]["tag"]:
            tops += 1
            tags[ps[0]["tag_en"]] += 1
    print("  a likely patient on top: %d of %d (%s); patients on that day's list: median %s" % (
        tops, len(xq), ", ".join("%s %d" % kv for kv in tags.most_common()), sorted(sizes)[len(sizes) // 2] if sizes else 0))
    print("Lab report came, no blood slip: %d  [%.2f s]" % (len(lab), t2 - t1))
    print("  came the same day %d · the day before %d · earlier that week %d · likely wrong ID %d · no visit, no suggestion %d" % (
        sum(1 for i in lab if i["note"].startswith("Isi din")), sum(1 for i in lab if i["note"].startswith("Ek din pehle")),
        sum(1 for i in lab if " ko clinic aaye" in i["note"]), sum(1 for i in lab if i["wrong"]),
        sum(1 for i in lab if i["note"].startswith("Is ID par is hafte"))))
    print("  by month: %s" % " · ".join("%s %d" % (m, n) for m, n in sorted(Counter(i["day"][:7] for i in lab).items(), reverse=True)))
    print("X-ray taken, no X-ray slip: %d · filed by themselves since 8-Nov: %d · X-rays with Shavez to bill: %d  [%.2f s]" % (
        len(nox), len(filed), len(xb), t3 - t2))
    print("  filed, how: %s" % ", ".join("%s %d" % kv for kv in Counter(i["detail"].split(" · ")[-1] for i in filed).most_common()))
    print("PROOF DONE")
finally:
    shutil.rmtree(TMP, ignore_errors=True)
