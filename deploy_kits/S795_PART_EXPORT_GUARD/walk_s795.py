#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s795.py BUILT_purchase_app.py [--control] -- the guard's rule run on made-up exports, and the repair on a made-up database.
Last line 'WALK S795 GREEN' -- or, with --control on the LIVE (unbuilt) file, 'CONTROL S795 RED as it must be'."""
import os
import re
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import repair_s795                                                # noqa: E402

DDL = ("CREATE TABLE purchase_export (md5 TEXT PRIMARY KEY, type TEXT, file TEXT, period_from TEXT, period_to TEXT, export_stamp TEXT, "
       "received_at TEXT, n_rows INTEGER, grand_amount_p INTEGER, superseded_by TEXT);"
       "CREATE TABLE purchase_bill (id INTEGER PRIMARY KEY, month TEXT, bw_md5 TEXT, sw_md5 TEXT);"
       "CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT);")


def guard(path):
    s = open(path, encoding="utf-8").read()
    m = re.search(r"# ---- S795_PART_EXPORT_GUARD[\s\S]*?\n(S795_HALF[\s\S]*?)# ---- end S795_PART_EXPORT_GUARD", s)
    if not m or 'reason="part_export"' not in s:
        return None
    ns = {}
    exec(m.group(1), ns)                                          # the function as built, nothing else of the module
    return ns["_s795_fuller"]


def ex(con, md5, typ, pf, pt, stamp, n, sup=None):
    con.execute("INSERT INTO purchase_export VALUES (?,?,?,?,?,?,?,?,?,?)", (md5, typ, "", pf, pt, stamp, "", n, 0, sup))


def main():
    path, control = sys.argv[1], "--control" in sys.argv
    f = guard(path)
    bad = []
    if f is None:
        bad.append("the guard is not in this file")
    else:
        con = sqlite3.connect(":memory:")
        con.executescript(DDL)
        ex(con, "full29", "BILLWISE", "2026-11-01", "2026-11-11", "20261111-110400", 29)
        ex(con, "item5", "ITEMWISE", "2026-11-01", "2026-11-11", "20261111-110503", 5)
        ex(con, "old25", "BILLWISE", "2026-10-01", "2026-10-08", "20261008-090000", 25)
        cases = [
            ("4 bills after 29, the same period: a part", ("BILLWISE", "2026-11-01", "2026-11-11", "20261111-110415", 4), "full29"),
            ("28 after 29, the same period: a correction, not a part", ("BILLWISE", "2026-11-01", "2026-11-11", "20261111-120000", 28), None),
            ("31 after 29, a wider period: the normal month-to-date", ("BILLWISE", "2026-11-01", "2026-11-12", "20261112-100000", 31), None),
            ("3 after 29, a wider period: a part", ("BILLWISE", "2026-11-01", "2026-11-12", "20261112-100000", 3), "full29"),
            ("71 lines after 5: the full one follows the part", ("ITEMWISE", "2026-11-01", "2026-11-11", "20261111-110517", 71), None),
            ("a new month, nothing older inside it", ("BILLWISE", "2026-12-01", "2026-12-02", "20261202-100000", 3), None),
            ("2 after 4: too small to call", ("SUPPLIERWISE", "2026-11-01", "2026-11-11", "20261111-110415", 2), None),
            ("12 after 25, the same period: a part", ("BILLWISE", "2026-10-01", "2026-10-08", "20261009-090000", 12), "old25"),
        ]
        ex(con, "sup4", "SUPPLIERWISE", "2026-11-01", "2026-11-11", "20261111-110400", 4)
        for name, a, want in cases:
            got = f(con, *a)
            if got != want:
                bad.append("%s: got %r, want %r" % (name, got, want))
    # the repair, on the shape of 11-Nov: 25 bills on the full list (retired), 4 on the part list (live)
    d = tempfile.mkdtemp(prefix="s795w_")
    db = os.path.join(d, "f.db")
    con = sqlite3.connect(db)
    con.executescript(DDL)
    ex(con, "prev25", "BILLWISE", "2026-11-01", "2026-11-08", "20261108-094340", 25, "full29")
    ex(con, "full29", "BILLWISE", "2026-11-01", "2026-11-11", "20261111-110400", 29, "part4")
    ex(con, "part4", "BILLWISE", "2026-11-01", "2026-11-11", "20261111-110415", 4)
    ex(con, "item5", "ITEMWISE", "2026-11-01", "2026-11-11", "20261111-110503", 5, "item71")
    ex(con, "item71", "ITEMWISE", "2026-11-01", "2026-11-11", "20261111-110517", 71)
    ex(con, "sepfull", "ITEMWISE", "2026-09-01", "2026-10-03", "20261005-075900", 186, "seppart")   # an old pair that another live
    ex(con, "seppart", "ITEMWISE", "2026-09-01", "2026-10-03", "20261005-075956", 5)                # report covers: LEFT ALONE
    ex(con, "sepmonth", "ITEMWISE", "2026-09-01", "2026-09-30", "20261020-090000", 180)
    for i in range(25):
        con.execute("INSERT INTO purchase_bill (month, bw_md5) VALUES ('2026-11','full29')")
    for i in range(4):
        con.execute("INSERT INTO purchase_bill (month, bw_md5) VALUES ('2026-11','part4')")
    con.execute("INSERT INTO setting VALUES ('purchase.rematch_seen','x','')")
    con.commit()
    b0 = repair_s795.effective(con, "2026-11")
    con.close()
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        r0 = repair_s795.main(["--db", db])                       # listing only: must change nothing
        con = sqlite3.connect(db); b1 = repair_s795.effective(con, "2026-11"); con.close()
        r1 = repair_s795.main(["--db", db, "--apply"])
        r2 = repair_s795.main(["--db", db, "--apply"])            # again: nothing more
    con = sqlite3.connect(db)
    b2 = repair_s795.effective(con, "2026-11")
    st = dict(con.execute("SELECT md5, superseded_by FROM purchase_export").fetchall())
    seen = con.execute("SELECT COUNT(*) FROM setting WHERE key='purchase.rematch_seen'").fetchone()[0]
    con.close()
    if not (b0 == 4 and b1 == 4 and r0 == 0):
        bad.append("before the repair: %s/%s effective (want 4/4)" % (b0, b1))
    if not (r1 == 0 and r2 == 0 and b2 == 29):
        bad.append("after the repair: %s effective (want 29)" % b2)
    if not (st.get("full29") is None and st.get("part4") == "full29" and st.get("prev25") == "full29" and st.get("item5") == "item71" and st.get("item71") is None
            and st.get("sepfull") == "seppart" and st.get("seppart") is None):
        bad.append("export marks after the repair: %r" % st)
    if seen:
        bad.append("the pairing's seen mark was not cleared")
    for f_ in os.listdir(d):
        os.remove(os.path.join(d, f_))
    os.rmdir(d)
    if control:
        print("CONTROL S795 RED as it must be" if bad and "the guard is not in this file" in bad else "CONTROL S795 NOT RED -- %s" % (bad or "the unbuilt file passed"))
        return 0
    for x in bad:
        print("RED: " + x)
    print("WALK S795 GREEN" if not bad else "WALK S795 RED (%d)" % len(bad))
    return 0


if __name__ == "__main__":
    sys.exit(main())
