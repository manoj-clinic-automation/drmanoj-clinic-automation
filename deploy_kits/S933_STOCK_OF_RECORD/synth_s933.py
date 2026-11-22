#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""synth_s933.py -- kit S933_STOCK_OF_RECORD (22-Nov-2026, Sanjeevni session 504). MADE-UP data only, in a scratch folder.
    python3 -B synth_s933.py <dir with the files under test (a copy of /root/finance)> <schema-from: a COPY of finance.db> [--control] [--keep]
Builds in TMPDIR: a finance.db with the copy's schema and NO rows of its own, a made-up spine (spine_build.SCHEMA) with TWO closing reports
(Sat 09:37 as on Fri; Sun 09:20 as on Sun -- a morning print, the end of Sat), Amir's bills (one first seen on the print day, one after), a
made-up assets.db with two scans, four orders of dealer 'W933 PHARMA', the taps (tie arrived=0: the tap came before the scan), two counts,
the consumption list. Then the stock of record (R1-R12), its readers (R13-R16), the fingerprint (R17-R18). --control runs the SAME checks on
the OLD files and must go red. No patient data anywhere; no number longer than 7 digits is printed. Prints 'RESULT: ALL PASS' or 'RESULT: n FAIL'."""
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


SAT, SUN = "2026-11-21", "2026-11-22"                          # the walk's days: Fri 20-11 (bills), Sat (sales, the yesterday-print), Sun (the morning print)
CAP_SAT = "W933CAPSAT0000000000000000000001"                   # printed Sat 09:37 as on Fri 20-11 -> the end of 20-11 ('yesterday')
CAP_SUN = "W933CAPSUN0000000000000000000002"                   # printed Sun 09:20 as on Sun 22-11 -> the end of Sat 21-11 ('morning')
K = "WPHARMA"                                                  # supkey of 'W933 PHARMA' (letters only, as the spine's supnorm and stock_watch.supkey fold it)


def make_spine(fin, path):
    sys.path.insert(0, os.path.join(fin, "spine"))
    import spine_build as SB                                  # noqa: E402
    sys.path.pop(0)
    sys.modules.pop("spine_build", None)
    sp = sqlite3.connect(path)
    sp.executescript(SB.SCHEMA)
    sp.execute("INSERT INTO sp_meta VALUES ('built', '2026-11-22T18:50:00+05:30')")
    E = "INSERT INTO sp_export VALUES (?,?,?,?,?,?,?,?,?,?,?)"
    sp.execute(E, (CAP_SAT, "closing_sat", "STOCK_CLOSING", "20261121-093700", None, None, "2026-11-20", 1, None, "closing", "walk"))
    sp.execute(E, (CAP_SUN, "closing_sun", "STOCK_CLOSING", "20261122-092000", None, None, SUN, 1, None, "closing", "walk"))
    sp.execute(E, ("W933SALE", "sale", "SALE_BILLWISE", "20261122-053000", "2026-11-01", SAT, None, 1, None, "sale", "walk"))
    sp.execute(E, ("W933PB", "pur", "PURCHASE_BILLWISE", "20261122-100000", "2026-11-01", SUN, None, 1, None, "pur", "walk"))
    sp.execute(E, ("W933PI", "pur", "PURCHASE_ITEMWISE", "20261122-100100", "2026-11-01", SUN, None, 1, None, "pur", "walk"))
    # (name, Sat closing units, Sun closing units)
    items = [("W933 ALFA 10", 300.0, 205.0), ("W933 BETA 10", 100.0, 40.0), ("W933 GAMA 10", 80.0, 60.0), ("W933 DELTA 10", 25.0, 25.0),
             ("W933 EPS 10", 10.0, 10.0), ("W933 ZETA 10", 100.0, 100.0), ("W933 KAPPA 10", 50.0, 150.0), ("W933 PLAIN 10", 70.0, 70.0),
             ("W933 RET 10", 100.0, 90.0), ("W933 NEG 10", 70.0, 40.0), ("W933 SUR 10", 20.0, 70.0)]
    sp.execute("INSERT INTO sp_item VALUES (?,?,?,?,?,?)", ("W933 ZERO 10", "W933 ZERO 10", "1*10", "strip", "2026-09-01", "2026-11-10"))   # at zero in Marg: printed in no closing
    for name, sat, sun in items:
        k = name[:20]
        sp.execute("INSERT INTO sp_item VALUES (?,?,?,?,?,?)", (k, name, "1*10", "strip", "2026-09-01", SUN))
        sp.execute("INSERT INTO sp_close_name VALUES (?,?,?,?,?)", (CAP_SAT, name, "1*10", k, sat))
        sp.execute("INSERT INTO sp_close_name VALUES (?,?,?,?,?)", (CAP_SUN, name, "1*10", k, sun))
        sp.execute("INSERT INTO sp_close VALUES (?,?,?,?)", ("2026-11-20", k, sat, CAP_SAT))
        sp.execute("INSERT INTO sp_close VALUES (?,?,?,?)", (SUN, k, sun, CAP_SUN))
    M = "INSERT INTO sp_move VALUES (?,?,?,?,?)"
    # ALFA: opening 300, sold 95 on Sat -> 205 = Sun's closing (no bill): agrees with itself
    sp.execute(M, ("W933 ALFA 10", "2026-11-01", "OPENING", 300.0, "OPEN"))
    sp.execute(M, ("W933 ALFA 10", SAT, "SALE", -95.0, "S1"))
    # BETA: opening 100, sold 60 Sat, bill K251 of Fri +300 keyed AFTER Sat's print (first seen Sun = the print day -> the shortfall decides): record 340, Sun's print 40
    sp.execute(M, ("W933 BETA 10", "2026-11-01", "OPENING", 100.0, "OPEN"))
    sp.execute(M, ("W933 BETA 10", SAT, "SALE", -60.0, "S2"))
    sp.execute(M, ("W933 BETA 10", "2026-11-20", "PURCHASE", 300.0, "K251"))
    # GAMA: opening 80, sold 20 Sat, bill K252 of 19-11 +120 first seen 23-11 (AFTER the print day: certain), Sun's print 60 (without it)
    sp.execute(M, ("W933 GAMA 10", "2026-11-01", "OPENING", 80.0, "OPEN"))
    sp.execute(M, ("W933 GAMA 10", SAT, "SALE", -20.0, "S3"))
    sp.execute(M, ("W933 GAMA 10", "2026-11-19", "PURCHASE", 120.0, "K252"))
    # DELTA: a consumable (the consumption list), Marg 25, counted 0
    sp.execute(M, ("W933 DELTA 10", "2026-11-01", "OPENING", 25.0, "OPEN"))
    # EPS: Marg 10 at Sun's print, a sale of 30 dated Sun (after the end day) -> the figure would be -20: Marg behind a bill
    sp.execute(M, ("W933 EPS 10", "2026-11-01", "OPENING", 10.0, "OPEN"))
    sp.execute(M, ("W933 EPS 10", SUN, "SALE", -30.0, "S4"))
    # ZETA: Marg 100; a delivery tapped Fri (25 strips), scanned (the bill says 20), NOT in Marg yet
    sp.execute(M, ("W933 ZETA 10", "2026-11-01", "OPENING", 100.0, "OPEN"))
    # KAPPA: Marg 150 = opening 50 + bill K253 of Fri +100 (printed 'W933 KAPPA-10' on the bill); the tap is carried by the scan's Marg bill
    sp.execute(M, ("W933 KAPPA 10", "2026-11-01", "OPENING", 50.0, "OPEN"))
    sp.execute(M, ("W933 KAPPA 10", "2026-11-20", "PURCHASE", 100.0, "K253"))
    # PLAIN: nothing moves, no count -> no shelf figure
    sp.execute(M, ("W933 PLAIN 10", "2026-11-01", "OPENING", 70.0, "OPEN"))
    # RET: opening 100, sold 10 Sat, a purchase RETURN R1 of Fri (-20) keyed after Sat's print (first seen Sun = the print day): record 70, Sun's print 90
    sp.execute(M, ("W933 RET 10", "2026-11-01", "OPENING", 100.0, "OPEN"))
    sp.execute(M, ("W933 RET 10", SAT, "SALE", -10.0, "S5"))
    sp.execute(M, ("W933 RET 10", "2026-11-20", "PURCHASE_RETURN", -20.0, "R1"))
    # NEG: opening 70, sold 30 Sat -> Marg 40; counted 5 units on 19-11: the count carried forward goes below zero
    sp.execute(M, ("W933 NEG 10", "2026-11-01", "OPENING", 70.0, "OPEN"))
    sp.execute(M, ("W933 NEG 10", SAT, "SALE", -30.0, "S6"))
    # SUR: opening 20, bill K254 of Fri +50 first seen 23-11 (after the print day) yet INSIDE Sun's print (70): the surplus names it -> not added
    sp.execute(M, ("W933 SUR 10", "2026-11-01", "OPENING", 20.0, "OPEN"))
    sp.execute(M, ("W933 SUR 10", "2026-11-20", "PURCHASE", 50.0, "K254"))
    PB = "INSERT INTO sp_purchase_bill VALUES (?,?,?,?,?,?,?)"
    PL = "INSERT INTO sp_purchase_line VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
    for bill, day, name, units, direction in (("K251", "2026-11-20", "W933 BETA 10", 300.0, "PURCHASE"), ("K252", "2026-11-19", "W933 GAMA 10", 120.0, "PURCHASE"),
                                              ("K253", "2026-11-20", "W933 KAPPA-10", 100.0, "PURCHASE"), ("R1", "2026-11-20", "W933 RET 10", 20.0, "RETURN"),
                                              ("K254", "2026-11-20", "W933 SUR 10", 50.0, "PURCHASE")):
        sp.execute(PB, ("W933 PHARMA", K, bill, day, int(units * 1000), direction, "W933PB"))
        sp.execute(PL, (K, bill, day, 1, name, name[:20] if "KAPPA" not in name else "W933 KAPPA 10", "1*10", units / 10, 0, units, int(units * 1000), int(units * 1000), direction, "W933PI"))   # a RETURN line carries POSITIVE units (the spine's shape)
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
    a.execute("INSERT INTO bills VALUES (601,'Pharmacy','W933 PHARMA','Z-1','2026-11-20',200.0,NULL,'w933_1.jpg','2026-11-20T05:00:00','2026-11-20T12:26:00','B-9601','pharmacy','ok',NULL,NULL,NULL,'done')")
    a.execute("INSERT INTO bills VALUES (602,'Pharmacy','W933 PHARMA','K253','2026-11-20',100.0,NULL,'w933_2.jpg','2026-11-20T05:00:00','2026-11-20T12:27:00','B-9602','pharmacy','ok',NULL,NULL,NULL,'done')")
    r1 = dict(doc="bill", doc_kind="bill", dealer="W933 PHARMA", bill_no="Z-1", date="2026-11-20", total=200.0, total_amount=200.0,
              items=[dict(name="W933 ZETA 10", qty=20, unit="1*10", rate=10, amount=200, batch="Z1")])
    r2 = dict(doc="bill", doc_kind="bill", dealer="W933 PHARMA", bill_no="K253", date="2026-11-20", total=100.0, total_amount=100.0,
              items=[dict(name="W933 KAPPA-10", qty=10, unit="1*10", rate=10, amount=100, batch="K1")])
    a.execute("INSERT INTO claude_reading VALUES (601,'2026-11-20T12:30:00','walk',1,'bill',?,NULL)", (json.dumps(r1),))
    a.execute("INSERT INTO claude_reading VALUES (602,'2026-11-20T12:31:00','walk',1,'bill',?,NULL)", (json.dumps(r2),))
    a.commit()
    a.close()


def main():
    fin, copy = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    control = "--control" in sys.argv
    scratch = tempfile.mkdtemp(prefix="s933_", dir=os.environ.get("TMPDIR") or "/tmp")
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
    say("-- S933 synth on the %s files: %s (stock_figure KIT %s)" % ("OLD (control)" if control else "new", fin, getattr(SF, "KIT", "?")))
    SW.ensure(con)
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('order.track_since','2026-10-12')")
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('stock.consume_items', ?)", (json.dumps(["W933 DELTA 10"]),))
    # the orders of W933 PHARMA (all 'received' by reception's tap BEFORE the scan: the tie's arrived=0 -- the live shape, 41 of 99 ties)
    O = "INSERT INTO purchase_order (id, created_at, created_by, vendor, status, supplier_norm, received_at) VALUES (?,?,?,?,?,?,?)"
    con.execute(O, (1, "2026-11-20T09:00:00", "walk", "W933 PHARMA", "received", "W933 PHARMA", "2026-11-20T12:25:00"))   # ZETA: scanned (Z-1), not in Marg
    con.execute(O, (2, "2026-11-20T09:00:00", "walk", "W933 PHARMA", "received", "W933 PHARMA", "2026-11-20T12:25:00"))   # KAPPA: scanned (K253), linked to Marg's bill
    con.execute(O, (3, "2026-11-20T09:00:00", "walk", "W933 PHARMA", "received", "W933 PHARMA", "2026-11-20T12:25:00"))   # PLAIN: tapped, no scan at all
    L = "INSERT INTO purchase_order_line (id, order_id, item, packs, pack_size, units, supplied, arrived_at, arrived_by) VALUES (?,?,?,?,?,?,?,?,?)"
    con.execute(L, (11, 1, "W933 ZETA 10", 25, 10, 250, 25, "2026-11-20T12:25:00", "reception"))    # tapped 25, the bill says 20 -> waiting 200, 5 short
    con.execute(L, (21, 2, "W933 KAPPA 10", 10, 10, 100, 10, "2026-11-20T12:25:00", "reception"))   # tapped 10, bill K253 (printed KAPPA-10) keyed in Marg -> carried
    con.execute(L, (31, 3, "W933 PLAIN 10", 3, 10, 30, 3, "2026-11-21T12:00:00", "reception"))      # tapped 3 strips Sat, no scan, not in Marg -> waiting 30 (tap_no_scan)
    T = "INSERT INTO order_scan_tie (order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived) VALUES (?,?,?,?,?,?,?)"
    con.execute(T, (1, 601, "B-9601", "2026-11-20T12:26:00", "2026-11-20T12:28:00", "scan", 0))
    con.execute(T, (2, 602, "B-9602", "2026-11-20T12:27:00", "2026-11-20T12:28:00", "scan", 0))
    # Amir's bills in the purchase register: K251 first seen Sun (the print day), K252 first seen 23-11 (after), K253 first seen Sat (before)
    B = "INSERT INTO purchase_bill (id, supplier_norm, supplier, bill_no, bill_date, month, amount_p, first_seen_day) VALUES (?,?,?,?,?,?,?,?)"
    con.execute(B, (901, "W933 PHARMA", "W933 PHARMA", "K251", "2026-11-20", "2026-11", 300000, SUN))
    con.execute(B, (902, "W933 PHARMA", "W933 PHARMA", "K252", "2026-11-19", "2026-11", 120000, "2026-11-23"))
    con.execute(B, (903, "W933 PHARMA", "W933 PHARMA", "K253", "2026-11-20", "2026-11", 100000, SAT))
    con.execute(B, (904, "W933 PHARMA", "W933 PHARMA", "R1", "2026-11-20", "2026-11", 20000, SUN))
    con.execute(B, (905, "W933 PHARMA", "W933 PHARMA", "K254", "2026-11-20", "2026-11", 50000, "2026-11-23"))
    con.execute("INSERT INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (903, 602, 'EXACT', 'walk', '2026-11-22T10:05:00')")
    # the counts: BETA counted 100 on 19-11 (morning); ZETA 100 on 19-11; KAPPA 50 on 19-11; DELTA 0 on 19-11; ALFA 300 on 20-11 (morning, before Sat's sale)
    P = "INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, status) VALUES (?,?,?,?,?,?,?)"
    for name, at, q in (("W933 BETA 10", "2026-11-19T10:00:00", 100), ("W933 ZETA 10", "2026-11-19T10:00:00", 100), ("W933 KAPPA 10", "2026-11-19T10:00:00", 50),
                        ("W933 DELTA 10", "2026-11-19T10:00:00", 0), ("W933 ALFA 10", "2026-11-20T10:00:00", 300), ("W933 GAMA 10", "2026-11-17T10:00:00", 80),
                        ("W933 RET 10", "2026-11-19T10:00:00", 100), ("W933 NEG 10", "2026-11-19T10:00:00", 5), ("W933 ZERO 10", "2026-11-19T10:00:00", 30)):
        con.execute(P, (name, name, at, q, "spot", "darpan", "settled"))
    con.commit()
    sp = SW.Spine(spp)
    check("the made-up spine reads (ready)", sp.ok and SF.ready(sp))

    # ---- the record
    try:
        import stock_record as SR                             # noqa: E402
    except ImportError:
        SR = None
    check("R0 stock_record is beside the files under test", SR is not None and SR.__file__.startswith(fin), getattr(SR, "__file__", None))
    if SR is None:
        say("INFO the control has no stock_record: R1-R16 are red by construction")
        for i in range(1, 17):
            check("R%d (no record)" % i, False)
        return
    cap = SR.capture(sp, SF)
    check("R1 the newest report wins: Sun's morning print (as on 22-11) stands for the END of Sat 21-11 ('morning'); no hold", bool(cap) and cap["md5"] == CAP_SUN and cap["end_day"] == SAT and cap["kind"] == "morning", cap)
    old = SF.capture_at(sp, None, SF.Ctx(con, sp))
    check("R1b (information) the old rule would still stand on Sat's print of Fri 20-11 (a same-day print held)", bool(old) and old["end_day"] == "2026-11-20", old)
    r = SR.build(con, sp, log=say)
    check("R2 build() writes the record: ok, 12 rows (11 printed + ZERO, counted but at zero in Marg), no item skipped", r.get("ok") and r.get("n") == 12 and r.get("errors") == 0, r)
    rows, M = SR.rows(con, sp, "never")
    R = {d["item"]: d for d in rows}
    say("INFO rows: " + "; ".join("%s m=%s s=%s w=%s g=%s %s" % (k[5:], d["marg_units"], d["shelf_units"], d["waiting_units"], d["gap_units"], d["state"]) for k, d in sorted(R.items())))
    A = R.get("W933 ALFA 10") or {}
    check("R3 ALFA: Marg 205 (Sun's print, no bill), shelf 205 (300 counted Fri morning - Sat's 95), gap 0 -> agree", A.get("marg_units") == 205 and A.get("shelf_units") == 205 and A.get("gap_units") == 0 and A.get("state") == "agree", A)
    Bt = R.get("W933 BETA 10") or {}
    check("R4 BETA: bill K251 (Fri, first seen ON the print day) closes the print's shortfall of 300 -> added: Marg 340 = shelf 340, gap 0, the words name the bill",
          Bt.get("marg_units") == 340 and Bt.get("marg_late") == 300 and Bt.get("shelf_units") == 340 and Bt.get("gap_units") == 0 and "K251" in (Bt.get("words") or "") and "keyed after the print" in (Bt.get("words") or ""), Bt)
    G = R.get("W933 GAMA 10") or {}
    check("R5 GAMA: bill K252 first seen AFTER the print day is added whole (certain): Marg 60 + 120 = 180; shelf 80 (counted 17-11) - 20 + 120 = 180; gap 0", G.get("marg_units") == 180 and G.get("marg_late") == 120 and G.get("shelf_units") == 180 and G.get("gap_units") == 0, G)
    D = R.get("W933 DELTA 10") or {}
    check("R6 DELTA: on the consumption list -> state consumable (Marg 25, counted 0: never a shop difference)", D.get("state") == "consumable" and D.get("consumable") == 1 and D.get("gap_units") == -25, D)
    E = R.get("W933 EPS 10") or {}
    check("R7 EPS: a sale after the end day takes Marg's figure to -20 -> marg_behind, no gap judged, the words say so", E.get("state") == "marg_behind" and E.get("marg_units") == -20 and E.get("gap_units") is None and "below" in (E.get("words") or "").lower() or "would be" in (E.get("words") or ""), E)
    Z = R.get("W933 ZETA 10") or {}
    W = Z.get("waiting") or []
    check("R8 ZETA: the tap (25) came BEFORE the scan (tie arrived=0) and the bill is not in Marg: waiting 200 by the BILL's quantity, 5 strips short, state scan_not_in_marg; shelf 100 (the count alone), gap 0",
          Z.get("waiting_units") == 200 and len(W) == 1 and W[0].get("state") == "scan_not_in_marg" and W[0].get("short") == -50 and "5:0 short" in (W[0].get("word") or "") and Z.get("shelf_units") == 100 and Z.get("gap_units") == 0 and Z.get("state") == "waiting", (Z, W))
    Kp = R.get("W933 KAPPA 10") or {}
    check("R9 KAPPA: the scan is linked to Marg's bill K253 (printed 'KAPPA-10') -> the tap is CARRIED, nothing waits; Marg 150, shelf 150 (50 + the bill's 100), gap 0",
          Kp.get("waiting_units") == 0 and Kp.get("marg_units") == 150 and Kp.get("shelf_units") == 150 and Kp.get("gap_units") == 0 and Kp.get("state") == "agree", Kp)
    Pl = R.get("W933 PLAIN 10") or {}
    PW = Pl.get("waiting") or []
    check("R10 PLAIN: no count -> no shelf figure (state no_shelf), Marg 70; its untied Sat tap waits as tap_no_scan (30)", Pl.get("state") == "no_shelf" and Pl.get("marg_units") == 70 and Pl.get("shelf_units") is None and Pl.get("waiting_units") == 30 and PW and PW[0].get("state") == "tap_no_scan", Pl)
    check("R11 the meta names the closing (as on 22-11, the end of 21-11, 'morning'), the reaches and the build", M.get("cap_as_on") == SUN and M.get("cap_end_day") == SAT and M.get("cap_kind") == "morning" and M.get("sale_to") == SAT and M.get("n_rows") == "12" and bool(M.get("built_at")), M)
    Rt = R.get("W933 RET 10") or {}
    check("R20 RET: a purchase RETURN keyed after the print (first seen on the print day) is SUBTRACTED: Marg 90 - 20 = 70 = shelf 70 (100 - 10 - 20), gap 0", Rt.get("marg_units") == 70 and Rt.get("marg_late") == -20 and Rt.get("shelf_units") == 70 and Rt.get("gap_units") == 0, Rt)
    Ng = R.get("W933 NEG 10") or {}
    check("R21 NEG: the count carried forward below zero stands at 0 and IS judged: gap 0 - 40 = -40, state look, the note says so", Ng.get("shelf_units") == 0 and Ng.get("shelf_named") == "below_zero" and Ng.get("gap_units") == -40 and Ng.get("state") == "look" and "below zero" in (Ng.get("words") or ""), Ng)
    Zr = R.get("W933 ZERO 10") or {}
    check("R22 ZERO: counted 30, printed in no closing (at zero in Marg) -> a row judged against zero: Marg 0, shelf 30, gap +30, look, the words say Marg prints no stock", Zr.get("marg_units") == 0 and Zr.get("shelf_units") == 30 and Zr.get("gap_units") == 30 and Zr.get("state") == "look" and "no stock" in (Zr.get("words") or ""), Zr)
    Su = R.get("W933 SUR 10") or {}
    check("R23 SUR: bill K254 first seen AFTER the print day but the print's surplus of 50 names it as inside -> NOT added: Marg 70, no late bill, no flag", Su.get("marg_units") == 70 and Su.get("marg_late") == 0 and not Su.get("marg_flag") and Su.get("state") == "no_shelf", Su)
    rw = SR.row(con, "W933 BETA 10", sp, "never")
    rk = SR.row(con, "W933 KAPPA 10", sp, "never")
    check("R12 row(): by name and by key; words_for() reads", rw is not None and rw["item"] == "W933 BETA 10" and rk is not None and "K251" in SR.words_for(rw), (rw and rw["item"], rk and rk["item"]))

    # ---- the readers
    import stock_check as SC                                  # noqa: E402
    SC._db = lambda: con
    rec = SC.record(con)
    rr = {x["item"]: x for x in rec.get("rows", [])}
    T = rec.get("totals") or {}
    check("R13 stock_check.record() reads the record: 12 rows, look 2 (NEG, ZERO; the consumable and the behind row are not 'look'), waiting 2, no_shelf 2 (PLAIN, SUR), behind 1, consumable 1, late 3 (BETA, GAMA, RET); the page did not rebuild (rebuilding False: the record is fresh)",
          rec.get("ok") and len(rr) == 12 and T.get("look") == 2 and T.get("arrived") == 2 and T.get("noshelf") == 2 and T.get("behind") == 1 and T.get("consumable") == 1 and T.get("late") == 3 and rec.get("record", {}).get("n_rows") == "12" and rec.get("record", {}).get("rebuilding") is False, (T, rec.get("reason"), rec.get("record")))
    check("R13e the count-only list no longer carries ZERO (it is a row now)", not any(c["item"] == "W933 ZERO 10" for c in rec.get("count_only") or []), rec.get("count_only"))
    zb = rr.get("W933 ZETA 10") or {}
    check("R13b the page's ZETA row: Marg 10:0, shelf 10:0, waiting +20:0, one line with the bill's word and the short in bold (short<0)", zb.get("marg_t") == "10:0" and zb.get("core_t") == "10:0" and zb.get("arrived_t") == "+20:0" and zb.get("lines") and zb["lines"][0].get("short") == -50 and "short" in zb["lines"][0].get("word", ""), zb)
    bb = rr.get("W933 BETA 10") or {}
    check("R13c the page's BETA row carries the words (bill K251 keyed after the print) and state agree", "K251" in (bb.get("words") or "") and bb.get("state") == "agree" and bb.get("gap") == 0, bb)
    rep = rec.get("reports") or {}
    check("R13d the reports line: closing as on 21-11 (the end day), printed 22-11, a morning print, the record's build time", rep.get("closing_as_on") == "21-11-2026" and rep.get("closing_printed") == "22-11-2026" and rep.get("start") is True and "morning" in (rep.get("kind_word") or "") and bool(rep.get("built_at")), rep)
    html = open(os.path.join(fin, "stock_check.html"), encoding="utf-8").read()
    check("R14 the page's HTML reads the new states: marg_behind and consumable sections, the words in rowNote, the record's build line, never a negative Marg in the column", "marg_behind" in html and "consumable" in html and "r.words" in html and "stock of record" in html and "behind a bill" in html and "rebuilding" in html)
    # the ledger's head figures from the record
    import item_ledger as IL                                  # noqa: E402
    sp2 = IL.spine_con(spp) if hasattr(IL, "spine_con") else None
    try:
        it = IL.item(sp2, "W933 BETA 10")
        body = IL._item_body(con, sp2, it, {})
    except Exception as e:                                    # noqa: BLE001
        body = "ERR %s: %s" % (type(e).__name__, str(e)[:160])
    check("R15 the ledger's head for BETA: Marg stock 34:0 from the record (not 4:0 from sp_close), 'keyed after the print' in its sub-line", "34:0" in body and "keyed after the print" in body and "K251" in body, body[:400] if body.startswith("ERR") else [x for x in re.findall(r'<div class="val">([^<]*)</div>', body)][:3])
    # S928's bill over the tap now speaks on a tie with arrived=0 (the live shape)
    a11 = [x for x in SW._arrivals(con, "W933 ZETA 10", "", sp, ctx=SF.Ctx(con, sp)) if x["line_id"] == 11]
    bu = SF.bill_units(con, sp, a11[0], SF.Ctx(con, sp)) if a11 else None
    check("R16 stock_figure.bill_units speaks on a tie whose arrived=0 (the tap came first): ZETA's bill says 200 (tapped 250)", bool(bu) and bu.get("units") == 200.0 and bu.get("on_bill"), bu)
    # the fingerprint
    check("R17 the record is fresh after its build (not stale)", not SR.is_stale(con, sp))
    con.execute(P, ("W933 PLAIN 10", "W933 PLAIN 10", "2026-11-21T19:30:00", 60, "spot", "darpan", "settled"))
    con.commit()
    check("R18 a new count makes it stale; rows('auto') rebuilds: PLAIN now has a shelf (60 counted Sat evening = the end of Sat; + nothing) and is no longer no_shelf", SR.is_stale(con, sp) and (lambda rs: rs[0].get("state") != "no_shelf" and rs[0].get("shelf_units") == 60)([d for d in SR.rows(con, sp, "auto")[0] if d["item"] == "W933 PLAIN 10"]), [d for d in SR.rows(con, sp, "never")[0] if d["item"] == "W933 PLAIN 10"])
    # capture() kinds on a tiny spine of its own
    tp = os.path.join(scratch, "caps.db")
    import spine_build as SB                                  # noqa: E402
    t = sqlite3.connect(tp)
    t.executescript(SB.SCHEMA)
    t.execute("INSERT INTO sp_export VALUES ('N1','n','STOCK_CLOSING','20261121-223000',NULL,NULL,'2026-11-21',1,NULL,'closing','walk')")
    t.execute("INSERT INTO sp_close_name VALUES ('N1','X','1*10','X',1)")
    t.commit()
    t.close()
    c2 = SR.capture(SW.Spine(tp), SF)
    check("R19 capture(): a print on its own day from 22:00 is 'night', the end of that day", bool(c2) and c2["kind"] == "night" and c2["end_day"] == "2026-11-21", c2)
    say("INFO %d checks, %d fail" % (RUN[0], len(FAILS)))


if __name__ == "__main__":
    main()
