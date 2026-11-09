#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proof_s756.py -- S756 on THIS box's databases, READ ONLY: the live finance.db and assets.db are opened mode=ro; the queue is tried on a
COPY of finance.db in the scratch folder (deleted at the end), never on the live one. Never prints a phone number, a body with a number, or
a patient detail.
    python3 -B proof_s756.py <finance code dir> <shared dir> <finance.db> <assets.db> <scratch dir>
The last line:  PROOF S756: ended months N · awaited A (number missing M) · would queue Q today · row 7 '<words>' · snapshot ok
           or   PROOF S756: ended months N · awaited A · (no S756 in these files)        or   PROOF S756: ERROR <why>
Need not be run by hand -- the installer runs it by the live files and by the kit's."""
import datetime as dt
import os
import re
import shutil
import sqlite3
import sys
import traceback

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
TEN = re.compile(r"(?<!\d)\d{10}(?!\d)")
try:
    code, shared, db, adb, scr = [os.path.abspath(x) for x in sys.argv[1:6]]
    sys.path.insert(0, code)
    sys.path.insert(1, shared)
    os.environ["SHARED_LIB_DIR"] = shared
    import purchase_app as PA                                 # noqa: E402
    import scan_register as SR                                # noqa: E402
    import supplier_msg as SM                                 # noqa: E402
    PA._assets_db = adb
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=30)
    con.row_factory = sqlite3.Row
    now = dt.datetime.now(IST).replace(tzinfo=None)
    d0 = now.date()
    os.environ["ORDER_TODAY"] = d0.isoformat()
    has = hasattr(SR, "s756_queue")
    months = SR._s756_ended(con, d0) if has else SR._s755_ended_months(con)
    if SR.s750_summary_scans(con) is None:
        print("PROOF S756: ERROR assets.db could not be read (%s)" % adb)
        sys.exit(1)
    n_aw = n_miss = 0
    words = ""
    for m in months:
        ds = SR.s750_dealers(con, m)
        aw = [d for d in ds if d.get("state") == "awaited" and d.get("key")]
        w = SR._s756_words(ds) if has else (SR.s750_open(con, m).get("words") or "")
        words = words or w
        print("  %s: %d dealers · row 7 '%s'" % (SR.month_name(m), len(ds), w))
        for d in sorted(aw, key=lambda x: x["name"]):
            ok_no = bool(SM._digits(con, d["name"]))
            n_miss += 0 if ok_no else 1
            print("     awaited  %-34s %2d bill(s) %10s  %s" % (" ".join(str(d["name"]).split()).title()[:34], len(d.get("bills") or []),
                                                               SR.rs(d.get("net_p")), "number on file" if ok_no else "NUMBER MISSING"))
        n_aw += len(aw)
    if not has:
        print("PROOF S756: ended months %d · awaited %d · (no S756 in these files)" % (len(months), n_aw))
        sys.exit(0)
    # the queue, on a COPY (never the live file)
    os.makedirs(scr, exist_ok=True)
    cp = os.path.join(scr, "proof_s756_copy.db")
    dst = sqlite3.connect(cp)
    con.backup(dst)
    dst.close()
    try:
        c2 = sqlite3.connect(cp)
        c2.row_factory = sqlite3.Row
        when = max(now.replace(tzinfo=IST), dt.datetime.combine(d0, dt.time(11, 30), IST))
        r = SR.s756_queue(c2, when)
        rows = c2.execute("SELECT month, status, body, last_error FROM supplier_msg WHERE kind='summary'").fetchall()
        bad = [x for x in rows if x["body"] != SR.s756_body(x["month"])]
        park = [x for x in rows if SR.month_class(c2, x["month"]) != "counted"]
        c2.close()
    finally:
        try:
            os.remove(cp)
        except OSError:
            pass
    if r.get("error"):
        print("PROOF S756: ERROR the queue on the copy: %s" % r["error"])
        sys.exit(1)
    if bad or park:
        print("PROOF S756: ERROR %d body(ies) not the owner's words, %d row(s) of a parked month" % (len(bad), len(park)))
        sys.exit(1)
    print("  the queue on a copy at %s: %s" % (when.strftime("%d-%m %H:%M"), {k: v for k, v in r.items() if k != "why" or v}))
    snap = SR.s756_snapshot(con, months[0], "/finance/purchase") if months else ""
    if months and (not snap or TEN.search(snap)):
        print("PROOF S756: ERROR the snapshot of %s is empty or carries a ten-digit number" % months[0])
        sys.exit(1)
    print("PROOF S756: ended months %d · awaited %d (number missing %d) · would queue %d today · row 7 '%s' · snapshot %s"
          % (len(months), n_aw, n_miss, int(r.get("queued") or 0), words, "ok" if snap else "none (no ended month)"))
except SystemExit:
    raise
except Exception:                                             # noqa: BLE001
    print(traceback.format_exc()[-1200:])
    print("PROOF S756: ERROR the proof raised -- see above")
    sys.exit(1)
