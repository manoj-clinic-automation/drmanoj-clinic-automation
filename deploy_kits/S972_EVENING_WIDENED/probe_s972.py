#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_s972.py -- S972: the evening check's four money shapes on the LIVE shape, read-only, counts only (never a name or number).
    python3 probe_s972.py <code_dir> <finance.db> [days]
For each of the last `days` days with a current stored consultation export: the export read as the evening reads it, the shapes
the evening WOULD name on the slips as they stand now (later corrections have already cleared some -- the counts are a floor of
what an evening sees, and a ceiling check on noise). Beside it, the reader's money against the tracker's own lines
(clinic_day_line, the same export read the long way) for every (patient, X-ray / procedure) pair both hold: how many agree.
Read-only (the database opened read-only). One line:
  PROBE972 days N unread U errors E lines L chhoot a kam b tdoc c tslip d more e head h reader_same S reader_diff X maxday M
(maxday: the most lines on any one day -- the installer gates on the worst day, not the average; cold review 6)"""
import sqlite3
import sys

code, db = sys.argv[1], sys.argv[2]
days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
sys.path.insert(0, code)
sys.dont_write_bytecode = True
import evening_check as EC                                     # noqa: E402

con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=30)
con.row_factory = sqlite3.Row
try:
    ds = [r[0] for r in con.execute("SELECT DISTINCT business_date FROM docterz_export WHERE kind='consultation' AND status='current' "
                                    "AND rows>0 ORDER BY business_date DESC LIMIT ?", (days,))]
except sqlite3.Error:                                          # a database without the Docterz tables (a made-up root)
    ds = []
n = dict(unread=0, errors=0, lines=0, same=0, diff=0, maxday=0)
by = dict.fromkeys(EC.SHAPES, 0)
for d in ds:
    e = EC.current_export(con, d)
    try:
        raw = open(e["stored"], "rb").read()
    except (OSError, TypeError):
        n["unread"] += 1
        continue
    try:
        car = EC.read_export(raw, d)
        am = EC.read_amounts(raw, d)
        if car is None or am is None:
            n["unread"] += 1
            continue
        day_lines = 0
        _rows, shapes = EC.merge_lines(EC.missing_slips(con, d, car), EC.shape_lines(con, d, car, am))   # as check() names them
        for ln in shapes:
            day_lines += 1
            n["lines"] += 1
            by[ln["shape"]] = by.get(ln["shape"], 0) + 1
            EC.shape_text(ln)
            EC.shape_text(ln, True)
        n["maxday"] = max(n["maxday"], day_lines)
        try:
            tl = {}
            for r in con.execute("SELECT clinic_id, section, amount_p FROM clinic_day_line WHERE business_date=? AND section IN ('xray','proc')", (d,)):
                k = (EC._cid(r["clinic_id"]), r["section"])
                tl[k] = tl.get(k, 0) + int(r["amount_p"] or 0)
        except sqlite3.Error:
            tl = {}
        for (c, kind), v in tl.items():
            mine = am.get(c, {}).get(kind)
            if mine is None:
                continue
            if mine[0] == v:
                n["same"] += 1
            else:
                n["diff"] += 1
    except Exception:                                          # noqa: BLE001 -- counted, never shown (a value could carry a name)
        n["errors"] += 1
print("PROBE972 days %d unread %d errors %d lines %d chhoot %d kam %d tdoc %d tslip %d more %d head %d reader_same %d reader_diff %d maxday %d" % (
    len(ds), n["unread"], n["errors"], n["lines"], by["chhoot"], by["kam"], by["tdoc"], by["tslip"], by["more"], by["head"], n["same"], n["diff"], n["maxday"]))
