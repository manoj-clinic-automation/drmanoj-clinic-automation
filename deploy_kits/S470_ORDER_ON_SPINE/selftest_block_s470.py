# -*- coding: utf-8 -*-
"""selftest_block_s470.py -- kit S470_ORDER_ON_SPINE, A.6: the checks selftest_spine.py gains, one per new read-door method, on a
MADE-UP spine (no real export, no number). make_s470.py copies the lines between the two markers into selftest_spine.py above its
__main__ block, and adds the call. The names below (B, Spine, check, os, shutil, sqlite3, tempfile) are selftest_spine.py's own."""
import os
import shutil
import sqlite3
import tempfile

B = Spine = check = None                                       # the frame only: selftest_spine.py's own names


# >>> S470 selftest
# ======================================================================= S470: the read door's methods for the order engine
def test_s470():
    tmp = tempfile.mkdtemp()
    try:
        p = os.path.join(tmp, "s470.db")
        c = sqlite3.connect(p)
        c.executescript(B.SCHEMA)
        c.executemany("INSERT INTO sp_item VALUES (?,?,?,?,?,?)", [
            ("ALPHA TAB", "ALPHA TAB", "1*10", "LOOSE", "2026-04-01", "2026-04-10"),
            ("GAMMA BELT UNISON XX", "GAMMA BELT UNISON XXL", "1*1", "WHOLE", "2026-04-01", "2026-04-10"),
            ("GAMMA BELT UNISON XX", "GAMMA BELT UNISON XXXL", "1*1", "WHOLE", "2026-04-01", "2026-04-10"),
            ("OLD SYP", "OLD SYP", "1*1", "LOOSE", "2026-04-01", "2026-04-10"),
            ("GONE CAP", "GONE CAP", "1*10", "LOOSE", "2026-04-01", "2026-04-05")])
        c.executemany("INSERT INTO sp_sale_bill VALUES (?,?,?,?,?,?,?,?,?,?)", [
            ("2026-04-02", "A000001", 0, 0, 0, 0, 0, 0, 0, "t"), ("2026-04-02", "A000002", 0, 0, 0, 0, 0, 0, 0, "t"),
            ("2026-04-04", "CN000001", 0, 0, 0, 0, 0, 0, 1, "t"), ("2026-02-01", "A000000", 0, 0, 0, 0, 0, 0, 0, "t")])
        c.executemany("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?,?,?,?,?,?)", [
            ("2026-04-02", "A000001", 1, "ALPHA TAB", "ALPHA TAB", "1*10", "1:0", 10.0, 1000, "", ""),
            ("2026-04-02", "A000002", 1, "ALPHA TAB", "ALPHA TAB", "1*10", "0:5", 5.0, 1000, "", ""),
            ("2026-04-04", "CN000001", 1, "ALPHA TAB", "ALPHA TAB", "1*10", "0:3", 3.0, 1000, "", ""),
            ("2026-02-01", "A000000", 1, "OLD SYP", "OLD SYP", "1*1", "1", 1.0, 1000, "", "")])
        c.executemany("INSERT INTO sp_move VALUES (?,?,?,?,?)", [
            ("ALPHA TAB", "2026-03-31", "OPENING", 40.0, "t"), ("ALPHA TAB", "2026-04-02", "SALE", -15.0, "A000001"),
            ("ALPHA TAB", "2026-04-04", "SALE_RETURN", 3.0, "CN000001")])
        c.executemany("INSERT INTO sp_purchase_bill VALUES (?,?,?,?,?,?,?)", [
            ("SUPPLIER ONE BAREILLY", "SUPPLIER", "11", "2026-04-03", 5000, "PURCHASE", "t"),
            ("SUPPLIER ONE BAREILLY", "SUPPLIER", "12", "2026-04-06", -1000, "RETURN", "t")])
        c.executemany("INSERT INTO sp_purchase_line VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
            ("SUPPLIER", "11", "2026-04-03", 1, "ALPHA TAB", "ALPHA TAB", "1*10", 5.0, 1.0, 60.0, 5000, 5250, "PURCHASE", "t"),
            ("SUPPLIER", "12", "2026-04-06", 1, "ALPHA TAB", "ALPHA TAB", "1*10", 1.0, 0.0, 10.0, 1000, 1050, "RETURN", "t")])
        c.executemany("INSERT INTO sp_close VALUES (?,?,?,?)", [
            ("2026-04-05", "ALPHA TAB", 28.0, "t"), ("2026-04-10", "ALPHA TAB", 27.0, "t"), ("2026-04-10", "GAMMA BELT UNISON XX", 5.0, "t"),
            ("2026-04-10", "OLD SYP", 2.0, "t"), ("2026-04-05", "GONE CAP", 4.0, "t")])
        c.commit()
        c.close()
        sp = Spine(p)
        d = sp.sales_daily("ALPHA TAB", "2026-04-01", "2026-04-10")
        check("S470 sales_daily: a credit-note line counts negative; one row per day with a sale",
              [(r["date"], r["units"], r["bills"]) for r in d] == [("2026-04-02", 15.0, 2), ("2026-04-04", -3.0, 1)])
        s = sp.stock_series("ALPHA TAB", "2026-04-01", "2026-04-05")
        check("S470 stock_series: the figure at the end of every day; a day with no movement repeats the day before",
              [r["units"] for r in s] == [40.0, 25.0, 25.0, 28.0, 28.0] and s[2]["date"] == "2026-04-03")
        pl = sp.purchase_lines("ALPHA TAB")
        check("S470 purchase_lines: a RETURN line is kept as RETURN; the supplier's printed name comes from its bill",
              [l["direction"] for l in pl] == ["PURCHASE", "RETURN"] and pl[0]["supplier"] == "SUPPLIER ONE BAREILLY" and pl[0]["qty"] == 5.0
              and len(sp.purchase_lines("ALPHA TAB", supplier="SUPPLIER ONE", date_from="2026-04-04")) == 1
              and sp.purchase_lines("ALPHA TAB", supplier="ANOTHER FIRM") == [])
        f = sp.family("GAMMA BELT UNISON XXL")
        check("S470 family: two rows under one 20-letter key are a family of two", f["n"] == 2 and f["key"] == "GAMMA BELT UNISON XX"
              and [m["name"] for m in f["members"]] == ["GAMMA BELT UNISON XXL", "GAMMA BELT UNISON XXXL"] and sp.family("ALPHA TAB")["n"] == 1)
        check("S470 last_sale: an item with one old sale answers that day; an item never sold answers None",
              sp.last_sale("OLD SYP") == {"date": "2026-02-01"} and sp.last_sale("GAMMA BELT UNISON XXL") is None)
        check("S470 closing: equal to stock().marg_units, and at or before a date", sp.closing("ALPHA TAB")["units"] == sp.stock("ALPHA TAB")["marg_units"] == 27.0
              and sp.closing("ALPHA TAB", "2026-04-07") == {"as_on": "2026-04-05", "units": 28.0} and sp.closing("NEVER LISTED") is None
              and sp.closing("GONE CAP") == {"as_on": "2026-04-05", "units": 4.0})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
# <<< S470 selftest
