#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""synth_s928.py -- kit S928_STOCK_ONE_RULE (22-Nov-2026, Sanjeevni session 503). MADE-UP data only, in a scratch folder.
    python3 -B synth_s928.py <dir with the files under test (a copy of /root/finance)> <schema-from: a COPY of finance.db> [--control]
Builds in TMPDIR: a finance.db with the copy's schema and NO rows of its own, a made-up spine (spine_build.SCHEMA), a made-up assets.db
(two pharmacy scans with Claude readings), four orders of dealer 'W928 PHARMA', two spot counts. Then: the bill over the tap (T1-T6),
a count by its time (T7-T10), the day's one line on the owner's Needs-you (T11-T15), the settings (T16-T18). --control runs the SAME
checks on the OLD files and must go red on the S928 checks. No patient data anywhere; no number longer than 7 digits is printed.
Prints 'RESULT: ALL PASS' or 'RESULT: n FAIL'."""
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

RUN, FAILS = [0], []


def say(s):
    print(re.sub(r"\d{8,}", lambda m: "#" * len(m.group(0)), str(s)), flush=True)


def check(label, cond, got=None):
    RUN[0] += 1
    say(("ok   " if cond else "FAIL ") + label + (("  [%s]" % str(got)[:300]) if (got is not None and not cond) else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def schema_from(copy, path):
    src = sqlite3.connect("file:%s?mode=ro" % copy, uri=True)
    dst = sqlite3.connect(path)
    for (sql,) in src.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END, name"):
        try:
            dst.execute(sql)
        except sqlite3.Error:
            pass
    dst.commit()
    src.close()
    return dst


def make_spine(fin, path):
    sys.path.insert(0, os.path.join(fin, "spine"))
    import spine_build as SB                                  # noqa: E402
    sys.path.pop(0)
    sys.modules.pop("spine_build", None)
    sp = sqlite3.connect(path)
    sp.executescript(SB.SCHEMA)
    D = "2026-11-20"
    CAP = "W928CAP00000000000000000000000001"
    sp.execute("INSERT INTO sp_export VALUES (?,?,?,?,?,?,?,?,?,?,?)", (CAP, "closing", "STOCK_CLOSING", "20261121-093700", None, None, D, 1, None, "closing", "walk"))
    sp.execute("INSERT INTO sp_export VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("W928SALE", "sale", "SALE_BILLWISE", "20261122-053000", "2026-11-01", "2026-11-21", None, 1, None, "sale", "walk"))
    sp.execute("INSERT INTO sp_export VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("W928PB", "pur", "PURCHASE_BILLWISE", "20261120-180000", "2026-11-01", "2026-11-19", None, 1, None, "pur", "walk"))
    sp.execute("INSERT INTO sp_export VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("W928PI", "pur", "PURCHASE_ITEMWISE", "20261120-180100", "2026-11-01", "2026-11-19", None, 1, None, "pur", "walk"))
    items = [("W928 ALFA 10", "1*10", 300.0), ("W928 BETA 10", "1*10", 100.0), ("W928 GAMA 10", "1*10", 50.0), ("W928 DELTA 10", "1*10", 20.0),
             ("W928 EPS 10", "1*10", 100.0), ("W928 MOR 10", "1*10", 100.0), ("W928 ZETA 10", "1*10", 10.0), ("W928 KAPPA 10", "1*10", 10.0),
             ("W928 KAPPA 20", "1*10", 10.0), ("W928 FULL 10", "1*10", 100.0)]
    for name, packing, units in items:
        k = name[:20]
        sp.execute("INSERT INTO sp_item VALUES (?,?,?,?,?,?)", (k, name, packing, "strip", "2026-09-01", D))
        sp.execute("INSERT INTO sp_close_name VALUES (?,?,?,?,?)", (CAP, name, packing, k, units))
        sp.execute("INSERT INTO sp_close VALUES (?,?,?,?)", (D, k, units, CAP))
    for name in ("W928 EPS 10", "W928 MOR 10", "W928 FULL 10"):   # sales on the count day (21-11) and the day after
        sp.execute("INSERT INTO sp_move VALUES (?,?,?,?,?)", (name[:20], "2026-11-21", "SALE", -10.0, "S1"))
        sp.execute("INSERT INTO sp_move VALUES (?,?,?,?,?)", (name[:20], "2026-11-22", "SALE", -5.0, "S2"))
    sp.commit()
    sp.close()


def make_assets(path):
    a = sqlite3.connect(path)
    a.executescript("""
CREATE TABLE bills(id INTEGER PRIMARY KEY, kind TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL, notes TEXT, source_stored TEXT,
  created_at TEXT, submitted_at TEXT, stamp_no TEXT, lane TEXT, status TEXT, dup_of INTEGER, page_of INTEGER, rescan_of INTEGER, ocr_status TEXT);
CREATE TABLE claude_reading(bill_id INTEGER PRIMARY KEY, at TEXT NOT NULL, model TEXT, ok INTEGER NOT NULL DEFAULT 0, doc_kind TEXT, data TEXT, error TEXT);
CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT);
""")
    a.execute("INSERT INTO bills VALUES (501,'Pharmacy','W928 PHARMA','W-1','2026-11-21',550.0,NULL,'w928_1.jpg','2026-11-21T05:00:00','2026-11-21T10:30:00','B-9501','pharmacy','ok',NULL,NULL,NULL,'done')")
    a.execute("INSERT INTO bills VALUES (502,'Pharmacy','W928 PHARMA','W-2','2026-11-21',90.0,NULL,'w928_2.jpg','2026-11-21T05:00:00','2026-11-21T10:30:00','B-9502','pharmacy','ok',NULL,NULL,NULL,'done')")
    r1 = dict(doc="bill", doc_kind="bill", dealer="W928 PHARMA", bill_no="W-1", date="2026-11-20", total=550.0, total_amount=550.0,   # the lines add up: scan_quality (the box's /root/shared) must not call it a scan to redo
              items=[dict(name="W928 ALFA 10", qty=15, unit="1*10", rate=10, amount=150, batch="B1"), dict(name="W928 ALFA 10", qty=5, unit="1*10", rate=10, amount=50, batch="B2"),
                     dict(name="W928 DELTA 10", qty=12, unit="1*10", rate=10, amount=120), dict(name="W928 OMEGA 10", qty=5, unit="1*10", rate=10, amount=50),
                     dict(name="W928 ZETA 10", qty=8, free=2, unit="1*10", rate=10, amount=80), dict(name="W928 KAPPA 10", qty=7, unit="1*10", rate=10, amount=70),
                     dict(name="W928 KAPPA 20", qty=3, unit="1*10", rate=10, amount=30)])
    a.execute("INSERT INTO claude_reading VALUES (501,'2026-11-20T11:00:00','walk',1,'bill',?,NULL)", (json.dumps(r1),))
    a.execute("INSERT INTO claude_reading VALUES (502,'2026-11-21T11:00:00','walk',1,'bill',?,NULL)", (json.dumps(dict(doc="bill", doc_kind="bill", dealer="W928 PHARMA", bill_no="W-2", total_amount=90.0, items=[dict(name="W928 GAMA 10", qty=None, amount=90)])),))
    a.commit()
    a.close()


def main():
    fin, copy = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    control = "--control" in sys.argv
    scratch = tempfile.mkdtemp(prefix="s928_", dir=os.environ.get("TMPDIR") or "/tmp")
    try:
        run(fin, copy, control, scratch)
    finally:
        if "--keep" in sys.argv:
            say("KEPT %s" % scratch)
        else:
            shutil.rmtree(scratch, ignore_errors=True)
    say("RESULT: %s" % ("ALL PASS" if not FAILS else "%d FAIL" % len(FAILS)))
    sys.exit(0 if not FAILS else 1)


def run(fin, copy, control, scratch):
    dbp, spp, adb = os.path.join(scratch, "fin.db"), os.path.join(scratch, "spine.db"), os.path.join(scratch, "assets.db")
    con = schema_from(copy, dbp)
    make_spine(fin, spp)
    make_assets(adb)
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=adb, SPINE_DB=spp, PYTHONDONTWRITEBYTECODE="1")
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [x for x in sys.path if os.path.abspath(x or ".") != here]
    sys.path.insert(0, fin)
    os.chdir(fin)
    import stock_watch as SW                                  # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    import purchase_app as PA                                 # noqa: E402
    assert SW.__file__.startswith(fin) and SF.__file__.startswith(fin), (SW.__file__, SF.__file__)
    PA._assets_db = adb
    say("-- S928 synth on the %s files: %s (stock_figure KIT %s)" % ("OLD (control)" if control else "new", fin, getattr(SF, "KIT", "?")))
    SW.ensure(con)
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('order.track_since','2026-10-12')")
    # the orders of W928 PHARMA: order 1 (scan 501 tied, arrived), order 2 (no scan), order 3 (scan 502 tied: a reading with no quantity)
    con.execute("INSERT INTO purchase_order (id, created_at, created_by, vendor, status, supplier_norm) VALUES (1,'2026-11-19T09:00:00','walk','W928 PHARMA','sent','W928 PHARMA')")
    con.execute("INSERT INTO purchase_order (id, created_at, created_by, vendor, status, supplier_norm) VALUES (2,'2026-11-19T09:00:00','walk','W928 PHARMA','sent','W928 PHARMA')")
    con.execute("INSERT INTO purchase_order (id, created_at, created_by, vendor, status, supplier_norm) VALUES (3,'2026-11-20T09:00:00','walk','W928 PHARMA','sent','W928 PHARMA')")
    L = "INSERT INTO purchase_order_line (id, order_id, item, packs, pack_size, units, supplied, arrived_at, arrived_by) VALUES (?,?,?,?,?,?,?,?,?)"
    con.execute(L, (11, 1, "W928 ALFA 10", 30, 10, 300, 30, "2026-11-21T11:00:00", "reception"))     # tapped 30, the bill says 20 -> 10 short
    con.execute(L, (12, 1, "W928 BETA 10", 10, 10, 100, 10, "2026-11-21T11:00:00", "reception"))     # tapped 10, not on the bill -> counts nothing
    con.execute(L, (13, 1, "W928 DELTA 10", 10, 10, 100, None, None, None))                          # not tapped, the scan says 12 -> counts 120
    con.execute(L, (14, 1, "W928 ZETA 10", 10, 10, 100, 10, "2026-11-21T11:00:00", "reception"))     # tapped 10, bill 8 + 2 free = 10 -> equal, no short
    con.execute(L, (15, 1, "W928 KAPPA 10", 7, 10, 70, 7, "2026-11-21T11:00:00", "reception"))       # two sizes of one name on one order: each its own read line
    con.execute(L, (16, 1, "W928 KAPPA 20", 5, 10, 50, 5, "2026-11-21T11:00:00", "reception"))       # tapped 5, the bill says 3 -> 2 short (never KAPPA 10's 7)
    con.execute(L, (21, 2, "W928 GAMA 10", 5, 10, 50, 5, "2026-11-20T11:00:00", "reception"))        # no scan: the tap stands (50)
    con.execute(L, (31, 3, "W928 GAMA 10", 4, 10, 40, 4, "2026-11-21T11:00:00", "reception"))        # the scan read it with NO quantity: the tap stands (40)
    con.execute("INSERT INTO order_scan_tie (order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived) VALUES (1,501,'B-9501','2026-11-21T10:30:00','2026-11-21T10:31:00','walk',1)")
    con.execute("INSERT INTO order_scan_tie (order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived) VALUES (3,502,'B-9502','2026-11-21T10:30:00','2026-11-21T10:31:00','walk',1)")
    con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, status) VALUES ('W928 EPS 10','W928 EPS 10','2026-11-21T19:49:00',90,'spot','darpan','settled')")
    con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, status) VALUES ('W928 MOR 10','W928 MOR 10','2026-11-21T10:40:00',90,'spot','darpan','settled')")
    con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, status) VALUES ('W928 ALFA 10','W928 ALFA 10','2026-11-20T10:00:00',100,'spot','darpan','settled')")   # counted BEFORE the tap: the shelf = 100 + what counts
    con.execute("INSERT INTO stock_count (id, unit, marg_as_on, bill_no, bill_date, started_at, submitted_at, submitted_by, items_total, items_counted, status) VALUES (7,'medical','2026-11-21','W','21-11-2026','2026-11-21T19:00:00','2026-11-21T19:00:00','walk',1,1,'submitted')")
    con.execute("INSERT INTO stock_count_item (count_id, item, pack_size, marg_qty, counted_qty, at) VALUES (7,'W928 FULL 10',10,100,90,'2026-11-21T19:00:00')")   # a FULL count keyed in at 19:00: never an evening count
    con.commit()
    sp = SW.Spine(spp)
    check("the made-up spine reads (ready)", sp.ok and SF.ready(sp))
    ctx = SF.Ctx(con, sp)
    cap = SF.capture_at(sp, None, ctx)
    check("the made-up closing stands for the end of 20-11", bool(cap) and cap["end_day"] == "2026-11-20", cap)

    # ---- WHY lines (made-up data only): what the scan half sees here -- printed so a red on another machine explains itself (S503, 22-Nov)
    try:
        import order_track as OT                              # noqa: E402
        say("INFO sqlite %s . assets store %s exists=%s . spine %s" % (sqlite3.sqlite_version, os.path.basename(PA._assets_db or ""), os.path.exists(PA._assets_db or ""), os.path.basename(spp)))
        acon = PA._assets_con()
        say("INFO _assets_con: %s" % ("open, %d bills" % acon.execute("SELECT COUNT(*) FROM bills").fetchone()[0] if acon is not None else "NONE"))
        if acon is not None:
            acon.close()
        rf = con.row_factory
        con.row_factory = sqlite3.Row
        try:
            o = OT.Ctx(con)
        finally:
            con.row_factory = rf
        try:
            import porders_s454 as _P4                        # noqa: E402
            say("INFO scan_quality (the scans-to-redo judge): %s" % ("loaded from %s" % os.path.dirname(_P4._sq_before_s736().__file__) if _P4._sq_before_s736() is not None else "NOT loaded here (the box has it in /root/shared)"))
        except Exception as e:                                # noqa: BLE001
            say("INFO scan_quality: unknown (%s)" % type(e).__name__)
        say("INFO order_track.Ctx: ok=%s scans=%d readings=%d bad=%s since=%s" % (getattr(o, "ok", None), len(getattr(o, "scans", {}) or {}), len(getattr(o, "read", {}) or {}), sorted(getattr(o, "bad", ()) or ()), OT.since(con)))
        if getattr(o, "ok", False):
            for sid in (501, 502):
                say("INFO scan %d: in scans=%s head=%s usable=%s names=%s" % (sid, sid in o.scans, o.head(sid), o.usable(sid), o.names(sid)))
            if hasattr(SF, "_s928_order_match"):
                M = SF._s928_order_match(ctx, o, OT, 1)
                say("INFO match order 1: %s" % ("NONE" if M is None else "hit=%s heads=%s reads=%d" % (sorted(M["hit"]), M["heads"], len(M["reads"]))))
        if hasattr(SF, "_s928_settings"):
            say("INFO settings: bill_over_tap=%s evening_hour=%s" % SF._s928_settings(ctx))
    except Exception as e:                                    # noqa: BLE001
        say("INFO why-lines failed: %s: %s" % (type(e).__name__, str(e)[:160]))
    # ---- the bill over the tap
    has = hasattr(SF, "bill_units")
    def bu(lid):
        a = [x for x in SW._arrivals(con, con.execute("SELECT item FROM purchase_order_line WHERE id=?", (lid,)).fetchone()[0], "", sp, ctx=ctx) if x["line_id"] == lid]
        return (SF.bill_units(con, sp, a[0], ctx) if (has and a) else None), (a[0] if a else None)
    b11, a11 = bu(11)
    check("T1 ALFA: tapped 30 strips, the scanned bill says 15 + 5 (two batch lines, summed) -> bill_units 200 (on the bill)", bool(b11) and b11.get("units") == 200.0 and b11.get("on_bill") and b11.get("qty") == 20.0, b11)
    b14, _ = bu(14)
    check("T1d ZETA: tapped 10, the bill says 8 + 2 free -> 100 units, equal, no short", bool(b14) and b14.get("units") == 100.0 and b14.get("free") == 2.0, b14)
    b15, _ = bu(15)
    b16, _ = bu(16)
    check("T1e two sizes of one name on one order are matched one-to-one: KAPPA 10 -> 70 (bill 7), KAPPA 20 -> 30 (bill 3), never each other's",
          bool(b15) and b15.get("units") == 70.0 and bool(b16) and b16.get("units") == 30.0, (b15, b16))
    check("T1b ALFA: taps() counts the BILL's 200, not the tap's 300", SF.taps(con, sp, "W928 ALFA 10", "", ctx) == 200.0, SF.taps(con, sp, "W928 ALFA 10", "", ctx))
    SA = SF.shelf(con, sp, "W928 ALFA 10", "2026-11-22", ctx)
    check("T1c ALFA counted 100 on 20-11, tapped 21-11 11:00 after the closing: the shelf = 100 + the bill's 200 = 300 (arrived 200)", SA.get("shelf") == 300 and SA.get("arrived") == 200.0, SA)
    b12, _ = bu(12)
    check("T2 BETA: tapped, not on the bill -> counts nothing (0)", bool(b12) and b12.get("units") == 0.0 and b12.get("on_bill") is False, b12)
    check("T2b BETA: taps() 0", SF.taps(con, sp, "W928 BETA 10", "", ctx) == 0.0, SF.taps(con, sp, "W928 BETA 10", "", ctx))
    b21, _ = bu(21)
    check("T3 GAMA (order 2): no scan tied -> the rule cannot speak (None), the tap stands", (b21 is None) if has else False, b21)
    b31, _ = bu(31)
    check("T3b GAMA (order 3): read with no quantity -> units None, the tap stands", bool(b31) and b31.get("units") is None and b31.get("on_bill"), b31)
    check("T3c GAMA taps() = 50 + 40 (both taps stand)", SF.taps(con, sp, "W928 GAMA 10", "", ctx) == 90.0, SF.taps(con, sp, "W928 GAMA 10", "", ctx))
    j825 = SF.s825_bill_judged(con, ctx)
    check("T3d s825_bill_judged and bill_units share ONE scan context per Ctx (one load) and agree on DELTA (on the bill)", j825 is not None and j825.get(13) is True and ("s928_octx",) in ctx.c, (j825, [k for k in ctx.c if k and k[0] == "s928_octx"]))
    # T3e (the second look's SHOULD 1): s825's verdict on every judged line IS the one match's -- never a second, line-subset match
    agree = []
    try:
        for lid, v in (j825 or {}).items():
            row = con.execute("SELECT order_id, item FROM purchase_order_line WHERE id=?", (lid,)).fetchone()
            M = SF._s928_order_match(ctx, ctx.c.get(("s928_octx",)), __import__("order_track"), row[0])
            agree.append(v == (M is not None and row[1] in M["hit"]))
    except Exception as e:                                    # noqa: BLE001 -- the control (old files) has no such function
        agree = [False, str(e)[:80]]
    check("T3e s825's verdict = the ONE match per order on every judged line (%d lines)" % len(agree), bool(agree) and all(agree), (j825, agree))
    check("T4 DELTA (not tapped, scan-tied): scan_arrivals counts the bill's 12 strips = 120", SF.scan_arrivals(con, sp, "W928 DELTA 10", "", ctx) == 120.0, SF.scan_arrivals(con, sp, "W928 DELTA 10", "", ctx))
    EX = SF.expect_for_point(con, sp, "W928 DELTA 10", ctx)
    check("T4b an UNCOUNTED item's spot count is judged against Marg + the scan-tied delivery (20 + 120 = 140, basis marg)", EX.get("basis") == "marg" and EX.get("expected") == 140.0, EX)
    ss = SF.short_supplies(con, sp, ctx) if hasattr(SF, "short_supplies") else None
    check("T5 short_supplies: ALFA 10 strips short (-100 units), BETA whole tap short (-100), DELTA +20 over; GAMA absent",
          ss is not None and sorted((x["item"], x["diff_units"]) for x in ss) == [("W928 ALFA 10", -100.0), ("W928 BETA 10", -100.0), ("W928 DELTA 10", 20.0), ("W928 KAPPA 20", -20.0)], ss)
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('arrival.bill_over_tap','0')")
    con.commit()
    ctx2 = SF.Ctx(con, sp)
    check("T6 the switch off: the tap stands again (ALFA 300, BETA 100), short_supplies empty",
          SF.taps(con, sp, "W928 ALFA 10", "", ctx2) == 300.0 and SF.taps(con, sp, "W928 BETA 10", "", ctx2) == 100.0 and (not has or SF.short_supplies(con, sp, ctx2) == []),
          (SF.taps(con, sp, "W928 ALFA 10", "", ctx2), SF.taps(con, sp, "W928 BETA 10", "", ctx2)))
    con.execute("DELETE FROM setting WHERE key='arrival.bill_over_tap'")
    con.commit()

    # ---- a count by its time
    ctx3 = SF.Ctx(con, sp)
    E = SF.shelf(con, sp, "W928 EPS 10", "2026-11-22", ctx3)
    M = SF.shelf(con, sp, "W928 MOR 10", "2026-11-22", ctx3)
    check("T7 the evening count (19:49) is the END of its day: 90 - 5 (next day's sale only) = 85", E.get("shelf") == 85 and E.get("base_evening") is True, E)
    check("T8 the morning count (10:40) is the start of its day: 90 - 10 - 5 = 75", M.get("shelf") == 75 and not M.get("base_evening"), M)
    FU = SF.shelf(con, sp, "W928 FULL 10", "2026-11-22", ctx3)
    check("T8b a FULL count keyed in at 19:00 is never an evening count: 90 - 10 - 5 = 75, as before", FU.get("shelf") == 75 and not FU.get("base_evening") and FU.get("base_kind") == "count", FU)
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('count.evening_hour','21')")
    con.commit()
    ctx4 = SF.Ctx(con, sp)
    E2 = SF.shelf(con, sp, "W928 EPS 10", "2026-11-22", ctx4)
    check("T9 the setting moved to 21: 19:49 is a day-start count again (75)", E2.get("shelf") == 75 and not E2.get("base_evening"), E2)
    con.execute("DELETE FROM setting WHERE key='count.evening_hour'")
    con.commit()
    check("T10 evening_count(): on its own day at/after the hour only",
          hasattr(SF, "evening_count") and SF.evening_count("2026-11-21T19:49:00", 17, "2026-11-21") and not SF.evening_count("2026-11-21T19:49:00", 17, "2026-11-20")
          and not SF.evening_count("2026-11-21T09:00:00", 17) and not SF.evening_count("", 17) and SF.evening_count("2026-11-21 17:00", 17))

    # ---- the day's one line on the owner's Needs-you
    today = dt.date.today().isoformat()
    ok1, msg1, code1, P1 = SW.darpan_point(con, "W928 MOR 10", 70.0, "darpan", sp=SW.Spine(spp))
    check("T11 Darpan's count of MOR is written (a point)", ok1 and code1 == 200 and P1 and P1.get("id"), (ok1, msg1, code1))
    n1 = con.execute("SELECT text FROM stock_watch_notice WHERE kind='count_day' AND once_key=?", ("counted:" + today,)).fetchall()
    check("T12 ONE count_day line for today: 'Darpan counted 1 item on dd-mm-yyyy: W928 MOR 10 ...'", len(n1) == 1 and n1[0][0].startswith("Darpan counted 1 item on %s: W928 MOR 10" % SW.dmy(today)), n1)
    id1 = con.execute("SELECT MAX(id) FROM stock_watch_notice WHERE kind='count_day'").fetchone()[0]
    ok2, msg2, code2, P2 = SW.darpan_point(con, "W928 DELTA 10", 140.0, "darpan", sp=SW.Spine(spp))   # Marg 20 + the bill's 120 (a scan-tied delivery counts for an uncounted item: A6)
    n2 = con.execute("SELECT text FROM stock_watch_notice WHERE kind='count_day' AND once_key=?", ("counted:" + today,)).fetchall()
    id2 = con.execute("SELECT MAX(id) FROM stock_watch_notice WHERE kind='count_day'").fetchone()[0]
    check("T13 the second count REWRITES the day's line as the newest notice: 'counted 2 items on ...', both named, DELTA matches the records (Marg + the bill's 120)",
          len(n2) == 1 and "counted 2 items on" in n2[0][0] and "W928 DELTA 10 matches the records" in n2[0][0] and "W928 MOR 10" in n2[0][0] and id2 >= id1
          and SW.notices(con, "owner")[0]["kind"] == "count_day", (n2, id1, id2, [x["kind"] for x in SW.notices(con, "owner")][:3]))
    pD = con.execute("SELECT status, provisional_units FROM stock_point WHERE item='W928 DELTA 10' ORDER BY id DESC LIMIT 1").fetchone()
    check("T13b DELTA's point is PROVISIONAL (judged against a scan-tied delivery Marg has not got yet; re-judged when it does)", pD and pD[0] == "provisional" and pD[1] == 120.0, pD)
    lines = SW.needs_you_lines(con)
    cd = [l for l in lines if "counted 2 items on" in (l.get("text") or "")]
    check("T14 needs_you_lines carries the count_day line, class warn (MOR is below the records)", len(cd) == 1 and cd[0].get("cls") == "warn", cd)
    cls_fn = getattr(SW, "_s928_cls", None)
    check("T15 _s928_cls: a day with nothing below is information; a close line is information; a loss line is a warning",
          cls_fn is not None and cls_fn(dict(kind="count_day", text="Darpan counted 1 item on 22-11-2026: X matches the records")) == "info"
          and cls_fn(dict(kind="close_watch", text="x")) == "info" and cls_fn(dict(kind="trace_unexplained", text="x")) == "warn"
          and cls_fn(dict(kind="count_day", text="Darpan counted 1 item on 22-11-2026: X 1:2 below the records")) == "warn")

    # ---- the settings
    S = SW.settings(con)
    check("T16 settings(): bill_over_tap True, evening_hour 17 by default", S.get("bill_over_tap") is True and S.get("evening_hour") == 17, (S.get("bill_over_tap"), S.get("evening_hour")))
    keys = [s["key"] for s in SW.SETTINGS]
    check("T17 SETTINGS carries arrival.bill_over_tap and count.evening_hour (his page can alter them)", "arrival.bill_over_tap" in keys and "count.evening_hour" in keys)
    try:
        sv = SW.settings_view(con)
        txt = json.dumps(sv, default=str)
        check("T18 settings_view renders with the two new rows", "arrival.bill_over_tap" in txt and "count.evening_hour" in txt)
    except Exception as e:                                    # noqa: BLE001
        check("T18 settings_view renders", False, str(e)[:200])
    say("INFO %d checks, %d fail" % (RUN[0], len(FAILS)))


if __name__ == "__main__":
    main()
