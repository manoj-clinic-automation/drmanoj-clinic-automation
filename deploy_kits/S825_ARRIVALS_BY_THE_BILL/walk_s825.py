#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s825.py -- S825_ARRIVALS_BY_THE_BILL (F-1220, D883): the walk, on a COPY of a finance.db with made-up orders and a made-up scan store.
    python3 -B walk_s825.py <finance code dir> <shared dir> <finance.db to copy>
Nothing outside its own temporary folder is opened for writing (the copy and the made-up assets.db are its own). Made-up dealers and items
only (WALKTEST ...). Its last line:  walk_s825: N check(s) failed"""
import datetime as dt
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import traceback

FAILS = []
N = [0]


def ok(cond, label):
    N[0] += 1
    if not cond:
        FAILS.append(label)
        print("FAIL  " + label)
    else:
        print("ok    " + label)


def main(code, shared, src_db):
    tmp = tempfile.mkdtemp(prefix="walk_s825_")
    try:
        return _main(code, shared, src_db, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _main(code, shared, src_db, tmp):
    db = os.path.join(tmp, "finance.db")
    adb = os.path.join(tmp, "assets.db")
    s = sqlite3.connect("file:%s?mode=ro" % src_db, uri=True)
    d = sqlite3.connect(db)
    s.backup(d)
    s.close()
    now = dt.datetime.now().replace(microsecond=0)
    od = (now - dt.timedelta(days=1)).replace(hour=10, minute=0, second=0)
    sat = od + dt.timedelta(hours=5)
    iso = lambda x: x.isoformat()                            # noqa: E731
    d.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('order.track_since', ?)", ((od - dt.timedelta(days=2)).date().isoformat(),))
    oid = {}
    for k, vend in (("A", "WALKTEST SURGICALS"), ("B", "WALKTWO PHARMA"), ("C", "WALKTHREE ORTHO")):
        cur = d.execute("INSERT INTO purchase_order (created_at, created_by, vendor, status, total_p, supplier_norm) VALUES (?,?,?,?,0,?)",
                        (iso(od), "walk", vend, "received", vend))
        oid[k] = cur.lastrowid
    L = {}
    for key, k, item, packs in (("a1", "A", "WALKCAP KNEE L", 2), ("a2", "A", "WALKCAP KNEE XL", 1), ("a3", "A", "WALKTAB 40", 3),
                                ("a4", "A", "WALKSYP 100", 2), ("b1", "B", "WALKDROP 5", 4), ("c1", "C", "WALKBELT M", 1), ("c2", "C", "WALKGEL 30", 2)):
        cur = d.execute("INSERT INTO purchase_order_line (order_id, item, packs, pack_size, units) VALUES (?,?,?,1,?)", (oid[k], item, packs, packs))
        L[key] = cur.lastrowid
    d.execute("INSERT OR REPLACE INTO stock_item_section (item_key, item, section, source, seeded_as, by_user, at) VALUES (?,?,?,?,?,?,?)",
              ("WALKBELT M", "WALKBELT M", "Orthotics", "walk", "Orthotics", "walk", iso(now)))
    # S459 (F-1400): the made-up scan ids sit above every id the copy already holds -- a database that already carries ties (the box's own,
    # a bench copy with made-up ties) never collides with them (the rehearsal's red was a UNIQUE failure on 9901).
    _b = max(9900, int(d.execute("SELECT COALESCE(MAX(asset_bill_id), 0) FROM order_scan_tie").fetchone()[0] or 0)) + 1
    S1, S2, S3 = _b, _b + 1, _b + 2
    for k, sid in (("A", S1), ("B", S2), ("C", S3)):
        d.execute("INSERT INTO order_scan_tie (order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived) VALUES (?,?,?,?,?,?,1)",
                  (oid[k], sid, "B-%d" % sid, iso(sat), iso(sat), "scan"))
    # a sent, untied order of a fourth dealer: on order on both bases, before and after
    cur = d.execute("INSERT INTO purchase_order (created_at, created_by, vendor, status, total_p, supplier_norm) VALUES (?,?,?,?,0,?)",
                    (iso(now - dt.timedelta(hours=3)), "walk", "WALKFOUR AGENCY", "sent", "WALKFOUR AGENCY"))
    d.execute("INSERT INTO purchase_order_line (order_id, item, packs, pack_size, units) VALUES (?,?,?,1,?)", (cur.lastrowid, "WALKSENT 10", 5, 5))
    d.commit()
    d.close()
    a = sqlite3.connect(adb)
    a.execute("CREATE TABLE bills (id INTEGER PRIMARY KEY, stamp_no TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL, submitted_at TEXT, "
              "created_at TEXT, ocr_status TEXT, dup_of INTEGER, lane TEXT, status TEXT, kind TEXT, page_of INTEGER, rescan_of INTEGER, source_stored TEXT)")
    a.execute("CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT)")      # the redo list (scan quality) is not this walk's subject
    a.execute("INSERT INTO settings (key, value) VALUES ('scan.redo_since', '2099-01-01')")
    a.execute("CREATE TABLE bill_items (id INTEGER PRIMARY KEY, bill_id INTEGER, item_name TEXT, quantity REAL)")
    a.execute("CREATE TABLE claude_reading (bill_id INTEGER PRIMARY KEY, at TEXT NOT NULL, model TEXT, ok INTEGER NOT NULL DEFAULT 0, doc_kind TEXT, data TEXT, error TEXT)")
    for sid, vend in ((S1, "WALKTEST SURGICALS"), (S2, "WALKTWO PHARMA"), (S3, "WALKTHREE ORTHO")):
        a.execute("INSERT INTO bills (id, stamp_no, vendor, bill_no, bill_date, total_amount, submitted_at, created_at, ocr_status, lane, status, kind) "
                  "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (sid, "B-%d" % sid, vend, "W%d" % sid, od.date().isoformat(), 100.0, iso(sat),
                                                       iso(sat - dt.timedelta(hours=5, minutes=30)), "read", "pharmacy", "captured", "Pharmacy"))
    reads = {S1: ["WALKCAP KNEE LARGE", "WALKCAP KNEE M", "WALKSYP 100ML"], S3: ["WALKBELT", "WALKGEL 30 GM"]}
    for sid, names in reads.items():
        a.execute("INSERT INTO claude_reading (bill_id, at, ok, data) VALUES (?,?,1,?)",
                  (sid, iso(sat), json.dumps(dict(vendor="", items=[dict(name=n, qty=1) for n in names]))))
    a.commit()
    a.close()

    sys.path.insert(0, shared)
    sys.path.insert(0, code)
    os.environ["SHARED_LIB_DIR"] = shared
    os.environ["ASSETS_DB"] = adb
    if not os.environ.get("SPINE_DB"):                       # the engine's rhythm opens the spine read-only: an empty one is enough here
        sqlite3.connect(os.path.join(tmp, "spine.db")).close()
        os.environ["SPINE_DB"] = os.path.join(tmp, "spine.db")
    import warnings
    warnings.simplefilter("ignore")
    import purchase_app as PA
    PA._assets_db = adb
    import order_track as OT
    import stock_figure as SF
    import order_rules as ORR
    new = hasattr(SF, "s825_bill_judged")
    con = sqlite3.connect(db)
    con.row_factory = None

    def judged():
        return SF.s825_bill_judged(con, SF.Ctx(con, None, read_only=True)) if new else None

    def lines_now():
        return {int(x["line_id"]) for x in SF.scan_lines(con, None, None, "", SF.Ctx(con, None, read_only=True))}

    def onord(basis):
        con.row_factory = sqlite3.Row                         # as order_rules' own connection
        try:
            return ORR._on_order_units(con, now.date(), basis)
        finally:
            con.row_factory = None

    j = judged() or {}
    ok(j.get(L["a1"]) is True, "1 judged: WALKCAP KNEE L carried by 'WALKCAP KNEE LARGE' (LARGE = L)")
    ok(j.get(L["a2"]) is False, "2 judged: WALKCAP KNEE XL NOT carried -- the bill's 'WALKCAP KNEE M' is a sibling size")
    ok(j.get(L["a3"]) is False, "3 judged: WALKTAB 40 NOT carried (not on the bill)")
    ok(j.get(L["a4"]) is True, "4 judged: WALKSYP 100 carried by 'WALKSYP 100ML'")
    ok(L["b1"] not in j, "5 a scan with no reading: its order's line not judged (the old reading stands)")
    ok(j.get(L["c1"]) is False, "6 judged: WALKBELT M (Orthotics) NOT carried by a bill line printing no size")
    ok(j.get(L["c2"]) is True, "7 judged: WALKGEL 30 carried by 'WALKGEL 30 GM'")
    ok(con.row_factory is None, "8 the connection's row factory put back as it was")
    sl = lines_now()
    ok({L["a1"], L["a4"], L["b1"], L["c2"]} <= sl, "9 scan_lines keeps the carried lines and the unjudged one")
    ok(not ({L["a2"], L["a3"], L["c1"]} & sl), "10 scan_lines leaves out the three lines the bill does not carry")
    oc = onord("count")
    ok(all(k in oc for k in ("WALKCAP KNEE XL", "WALKTAB 40", "WALKBELT M")), "11 on order (count): the three lines not on the bill stay on the way")
    ok(not any(k in oc for k in ("WALKCAP KNEE L", "WALKSYP 100", "WALKDROP 5", "WALKGEL 30")), "12 on order (count): carried / unjudged scan lines are not")
    ok(oc.get("WALKTAB 40", {}).get("units") == 3, "13 on order (count): WALKTAB 40 counts its 3 ordered units, once")
    ok("WALKSENT 10" in oc, "14 on order (count): a sent untied order still counts")
    om = onord(None)
    ok(all(k in om for k in ("WALKCAP KNEE L", "WALKCAP KNEE XL", "WALKTAB 40", "WALKDROP 5", "WALKSENT 10")), "15 on order (marg basis): unchanged -- every tied line and the sent one")
    ok(SF.scan_arrivals(con, None, "WALKTAB 40", "") == 0.0, "16 scan_arrivals: WALKTAB 40 has not arrived (0 units)")
    ok(SF.scan_arrivals(con, None, "WALKCAP KNEE L", "") == 2.0, "17 scan_arrivals: WALKCAP KNEE L arrived, its 2 ordered packs")
    ok(OT.name_score("KNEE CAP L", "KNEE CAP XL") == 0.0, "18 the tracker's matcher: KNEE CAP L never answers KNEE CAP XL")
    ok(OT.name_score("CAST SHOE L", "CAST SHOE M TYNOR") == 0.0 and OT.name_score("LS BELT M", "LS BELT L") == 0.0, "19 real sibling sizes never pair")
    ok(OT.name_score("FINGER COT M", "FINGER COT MEDIUM") > 0 and OT.name_score("KNEE CAP L", "KNEE CAP LARGE") > 0
       and OT.name_score("ZIVOPREG M", "ZIVOPREG-M TAB") > 0 and OT.name_score("AURAB L CAP", "AURAB-L") > 0, "20 real same-item spellings still pair")
    ok(OT.name_score("PAN 40", "PAN 20 TAB") == 0.0 and OT.name_score("XYZ 10'S", "XYZ 10 S") == 1.0, "21 numbers still decide; 10'S is a count")
    try:
        sz = OT.size_of("L.S. BELT M")
    except Exception:                                         # noqa: BLE001
        sz = None
    ok(sz == frozenset(["M"]), "22 size_of: an initial (L.S.) is no size; the last M is")
    soft = {}
    try:
        octx = OT.Ctx(con)
        rows = [r for r in OT.light_all(con, now) if r["id"] == oid["A"]]
        soft = OT.soft_notes(con, rows[0], octx, True, None) if rows else {}
    except Exception:                                         # noqa: BLE001
        soft = {}
    ok((soft.get(L["a2"]) or ("",))[0] == "no" and (soft.get(L["a1"]) or ("",))[0] == "on", "23 the tracker's own note agrees: L on the bill, XL not seen")
    con.row_factory = None
    try:
        ro = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
        jro = SF.s825_bill_judged(ro, SF.Ctx(ro, None, read_only=True)) if new else None
        ro.close()
    except Exception:                                         # noqa: BLE001
        jro = None
    ok(jro is not None and jro == judged(), "27 judged on a read-only connection, the same (nothing it calls writes)")
    # the scan store unreachable: the old reading everywhere
    PA._assets_db = os.path.join(tmp, "absent.db")
    os.environ["ASSETS_DB"] = PA._assets_db
    ok(judged() is None, "24 the scan store unreachable: nothing judged")
    ok({L["a2"], L["a3"], L["c1"]} <= lines_now(), "25 the scan store unreachable: scan_lines keeps every tied line (the old reading)")
    ok(not any(k in onord("count") for k in ("WALKCAP KNEE XL", "WALKTAB 40")), "26 the scan store unreachable: on order (count) as before")
    con.close()
    if os.environ.get("WALK_KEEP"):                          # the bench only: keep the made-up databases for the proof
        for f in ("finance.db", "assets.db"):
            shutil.copy(os.path.join(tmp, f), os.path.join(os.environ["WALK_KEEP"], f))
    print("walk_s825: %d check(s) failed" % len(FAILS))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(2)
    try:
        sys.exit(main(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])))
    except Exception:                                         # noqa: BLE001
        print(traceback.format_exc()[-2000:])
        print("walk_s825: raised -- 99 check(s) failed")
        sys.exit(1)
