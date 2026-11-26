#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_s960.py -- S960: the evening check's reader against his own list, on the LIVE shape, counts only (never a name or number).
    python3 probe_s960.py <code_dir> <finance.db> [days]
For each of the last `days` days that has BOTH a current stored consultation export and the tracker's lines (clinic_day_revenue):
evening_check.missing_slips(read_export(the stored file)) beside not_in_docterz.rows() unanswered -- how many agree, how many only
one of them names. Read-only: the database is opened read-only. Prints one line: PROBE days N same S mine_only M his_only H unread U"""
import os
import sqlite3
import sys

code, db = sys.argv[1], sys.argv[2]
days = int(sys.argv[3]) if len(sys.argv) > 3 else 6
sys.path.insert(0, code)
sys.dont_write_bytecode = True
import evening_check as EC                                     # noqa: E402
import not_in_docterz as NID                                   # noqa: E402

con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=30)
con.row_factory = sqlite3.Row
try:
    ds = [r[0] for r in con.execute("SELECT DISTINCT e.business_date FROM docterz_export e JOIN clinic_day_revenue r "
                                    "ON r.business_date=e.business_date WHERE e.kind='consultation' AND e.status='current' AND e.rows>0 ORDER BY e.business_date DESC LIMIT ?", (days,))]
except sqlite3.Error:                                          # a database without the Docterz tables (a made-up root)
    ds = []
same = mine_only = his_only = unread = 0
for d in ds:
    e = EC.current_export(con, d)
    try:
        raw = open(e["stored"], "rb").read()
    except (OSError, TypeError):
        unread += 1
        continue
    car = EC.read_export(raw, d)
    if car is None:
        unread += 1
        continue
    mine = {(r["slip_id"], r["kind"]) for r in EC.missing_slips(con, d, car)}
    his = {(r["slip_id"], r["kind"]) for r in NID.rows(con, d, d) if not r["mark"]}
    same += len(mine & his)
    mine_only += len(mine - his)
    his_only += len(his - mine)
print("PROBE days %d same %d mine_only %d his_only %d unread %d" % (len(ds), same, mine_only, his_only, unread))
