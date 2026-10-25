#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""liveread_s650.py -- kit S650_ATTCORR: the LIVE-SHAPE read after placing (D786). Imports the placed register the way the
service does (module, no server), and reads the running month through the new module. No name is printed; the only
write is the staging tables' CREATE TABLE IF NOT EXISTS, which the first page view would make anyway.
Last line: 'attcorr live: routes 8 . lock wrapped yes . ...'"""
import datetime
import os
import sys

APPDIR = sys.argv[1] if len(sys.argv) > 1 else "/root/staff_register"
os.chdir(APPDIR)
sys.path.insert(0, APPDIR)
import staff_register as SR                                             # noqa: E402
import att_correction as AC                                             # noqa: E402

rules = sorted({r.rule for r in SR.app.url_map.iter_rules() if "/attcorr" in r.rule})
nrules = sum(1 for r in SR.app.url_map.iter_rules() if "/attcorr" in r.rule)
wrapped = bool(getattr(SR.app.view_functions.get("salary_lock"), "_attcorr_wrapped", False))
ym = SR._today()[:7]
con = AC._db()
try:
    blocks, ok = AC.day_list(con, ym)
    st = AC.summary(con, ym, blocks, ok)
finally:
    con.close()
waits = bool(AC.lock_blocker(ym)) if ym >= AC.FROM_YM else False
line = AC.line_payload(AC._prev_ym(SR._today()))
print("paths: " + ", ".join(rules))
print("previous month's line door: %s %s days, print_open %s" % (line["month"], line["days"], line["print_open"]))
print("attcorr live: routes %d · lock wrapped %s · punch feed %s · %s to date: %d staff, %d day(s) with no "
      "punch · the lock would wait: %s" % (nrules, "yes" if wrapped else "NO", "read" if ok else "UNREADABLE",
                                              datetime.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%B"),
                                              st["n_staff"], st["n_days"], "yes" if waits else "no"))
