#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s827.py -- S827_LINES_TO_THE_LIVE_BILL (F-1243) on a MADE-UP root: the finance code to test copied to a temp folder of the walk's
own; a made-up finance.db from purchase_schema.sql. No real data, no network.
    python3 -B walk_s827.py <finance code dir to test> <purchase_schema.sql>
Green on the new file; the CONTROL (the live file) red on the moved-bill checks. Last line:  walk_s827: N check(s) failed"""
import os
import shutil
import sqlite3
import sys
import tempfile

CODE, SCHEMA = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
TMP = tempfile.mkdtemp(prefix="s827walk_")
_c = os.path.join(TMP, "code")
os.makedirs(_c)
for n in os.listdir(CODE):
    if n.endswith(".py") and os.path.isfile(os.path.join(CODE, n)):
        shutil.copy(os.path.join(CODE, n), os.path.join(_c, n))
shutil.copy(SCHEMA, os.path.join(_c, "purchase_schema.sql"))
for k in ("ASSETS_DB", "FINANCE_DB", "ASSETS_UPLOADS"):
    os.environ.pop(k, None)
sys.path.insert(0, _c)
import warnings                                               # noqa: E402
warnings.simplefilter("ignore")
import purchase_app as PA                                     # noqa: E402

FAILS = []


def ck(name, cond):
    print(("  ok   " if cond else "  FAIL ") + "[S827] " + name)
    if not cond:
        FAILS.append(name)


con = sqlite3.connect(os.path.join(TMP, "finance.db"))
con.row_factory = sqlite3.Row
con.executescript(open(SCHEMA).read())
PA._schema_done = False
PA._ensure(con)
for md5, typ, rec, sup in (("bw_old", "BILLWISE", "2026-09-02T15:10:05", "bw_new"), ("bw_new", "BILLWISE", "2026-09-17T09:24:06", None),
                           ("iw", "ITEMWISE", "2026-08-27T03:57:51", None), ("biw", "BILLITEMWISE", "2026-09-22T18:25:57", None)):
    con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, superseded_by) "
                "VALUES (?,?,?,?,?,?,?,?,?)", (md5, typ, md5 + ".xls", "2026-08-01", "2026-08-31", rec.replace("-", "")[:8] + "-000000", rec, 3, sup))


def bill(sup, no, day, md5, rs):
    con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, bw_md5, first_seen_day) VALUES (?,?,?,?,?,?,?,?)",
                (sup, sup, no, day, day[:7], rs * 100, md5, day))


bill("MANNAT PHARMA", "502", "2026-08-18", "bw_old", 10641)            # Marg's 02-Sep list: the bill under Mannat
bill("DEEPAM PHARMA", "502", "2026-08-18", "bw_new", 10641)            # Marg's 17-Sep list: Amir moved it to Deepam
bill("ALPHA DRUGS", "77", "2026-08-20", "bw_new", 500)                 # F-494: two live bills of one number on one day
bill("BETA PHARMA", "77", "2026-08-20", "bw_new", 700)
bill("GAMMA MEDICOS", "88", "2026-08-21", "bw_new", 300)               # an ordinary bill
con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, qty, amount_p, direction, source_md5, line_type) VALUES "
            "('MANNAT PHARMA','502','2026-08-18','2026-08','ROSIKA FORTE',50,1064134,'PURCHASE','iw','ITEMWISE')")   # the item list of 27-Aug (Mannat)
con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, qty, amount_p, direction, source_md5, line_type) VALUES "
            "('BETA PHARMA','77','2026-08-20','2026-08','XETA TAB',7,70000,'PURCHASE','iw','ITEMWISE')")
con.commit()
rows = [dict(item="ROSIKA FORTE", bill_no="502", bill_date="2026-08-18", qty=50, amount_p=1064134),
        dict(item="XETA TAB", bill_no="77", bill_date="2026-08-20", qty=7, amount_p=70000),
        dict(item="ZOLA SYP", bill_no="88", bill_date="2026-08-21", qty=3, amount_p=30000)]
try:
    PA._store_lines(con, "BILLITEMWISE", "biw", "2026-08-01", "2026-08-31", rows)
    PA._redate_lines(con)
    con.commit()
except Exception as e:                                        # noqa: BLE001
    print("    (raised: %s)" % e)


def owner(item):
    r = con.execute("SELECT supplier_norm FROM purchase_line WHERE source_md5='biw' AND item=?", (item,)).fetchone()
    return r[0] if r else "?"


print("1 · a bill moved between dealers in Marg")
ck("Deepam's 502 of 18-Aug: the printed item line goes to DEEPAM PHARMA (the live list), never MANNAT (the replaced one)", owner("ROSIKA FORTE") == "DEEPAM PHARMA")
ck("... so Deepam's live bill shows its line", con.execute("SELECT COUNT(*) FROM purchase_line WHERE supplier_norm='DEEPAM PHARMA' AND bill_no='502' "
                                                           "AND source_md5='biw'").fetchone()[0] == 1)
print("2 · as before")
ck("two live bills of one number on one day: the item list names the dealer (F-494) -> BETA PHARMA", owner("XETA TAB") == "BETA PHARMA")
ck("an ordinary bill: its one live dealer -> GAMMA MEDICOS", owner("ZOLA SYP") == "GAMMA MEDICOS")
ck("the item list's own line stays as Marg printed it (MANNAT on 27-Aug)", con.execute("SELECT supplier_norm FROM purchase_line WHERE source_md5='iw' "
                                                                                       "AND item='ROSIKA FORTE'").fetchone()[0] == "MANNAT PHARMA")
print("walk_s827: %d check(s) failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
