#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_line_owner_s282.py -- S282: a purchase line whose bill number belongs to two
suppliers on the same day is given to the supplier the ITEMWISE export names.

THE FAULT (F-494, S259). Bill 160 of 1 September exists twice -- DAANSHI PHARMA
and KEDAR PHARMACEUTICAL, same day. BILLITEMWISE prints no supplier, so its lines
are attributed by (bill_no, bill_date). When that names two bills the line cannot
be placed and was stored with NO supplier: 5 lines, Rs 17,777, in September's
month total and on nobody's payment sheet.

THE WITNESS. The ITEMWISE export DOES carry the supplier, and the same five lines
are in it under their owners -- same bill number, same date, same item, same
amount. A line with two possible owners is given to the one owner that ITEMWISE
names for exactly that (bill, date, item, amount). If ITEMWISE names none, or
more than one, or one that is not among the candidates, the line stays as it is.

ONE anchored change and one helper appended. Nothing else is touched:

  A  the end of _redate_lines() gains one call, _line_owner_s282(con, by_no),
     before the month column is refreshed.
  B  the helper is appended at the end of the file.

    python3 -B patch_line_owner_s282.py --file /root/finance/purchase_app.py --from <md5>
"""
import argparse
import hashlib
import io
import os
import shutil
import sys

MARK = "_line_owner_s282"

A_OLD = '''            con.execute("UPDATE purchase_line SET supplier_norm=?, bill_date=? WHERE id=?", (k, d, r[0]))
    con.execute("UPDATE purchase_line SET month=substr(bill_date,1,7) WHERE bill_date IS NOT NULL")


@bp.route("/api/vendors", methods=["POST"])'''

A_NEW = '''            con.execute("UPDATE purchase_line SET supplier_norm=?, bill_date=? WHERE id=?", (k, d, r[0]))
    _line_owner_s282(con, by_no)
    con.execute("UPDATE purchase_line SET month=substr(bill_date,1,7) WHERE bill_date IS NOT NULL")


@bp.route("/api/vendors", methods=["POST"])'''

HELPER = '''

def _line_owner_s282(con, by_no):
    """F-494: a line whose (bill_no, bill_date) names MORE THAN ONE bill.

    Marg numbers bills per vendor, so two suppliers can share a bill number on
    one day; rev 2 above leaves such a line with no supplier. The ITEMWISE export
    carries the supplier, and the same line is in it: same bill number, same
    date, same item, same amount. The line is given to the ONE supplier ITEMWISE
    names for that exact line, provided that supplier is one of the candidates.
    None, two, or a stranger -> the line stays unowned. Returns lines placed."""
    placed = 0
    for r in con.execute("SELECT id, bill_no, bill_date, item, amount_p FROM purchase_line "
                         "WHERE supplier_norm IS NULL AND bill_no IS NOT NULL AND "
                         "bill_date IS NOT NULL").fetchall():
        cands = {c[0] for c in (by_no.get(r[1]) or []) if c[1] == r[2]}
        if len(cands) < 2:
            continue
        w = {x[0] for x in con.execute(
            "SELECT DISTINCT supplier_norm FROM purchase_line WHERE line_type='ITEMWISE' AND "
            "supplier_norm IS NOT NULL AND bill_no=? AND bill_date=? AND item=? AND amount_p IS ?",
            (r[1], r[2], r[3], r[4])).fetchall()}
        if len(w) == 1 and w <= cands:
            con.execute("UPDATE purchase_line SET supplier_norm=? WHERE id=?", (w.pop(), r[0]))
            placed += 1
    return placed
'''


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--from", dest="from_md5", default=None)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)

    if not os.path.exists(a.file):
        sys.exit("REFUSING: %s not found" % a.file)
    raw = io.open(a.file, "rb").read()
    cur = md5(raw)
    src = raw.decode("utf-8")

    if MARK in src:
        print("ALREADY PATCHED (%s present); pin %s -- nothing to do" % (MARK, cur))
        return 0
    if a.from_md5 and cur != a.from_md5.lower():
        sys.exit("REFUSING: %s is %s, you said %s" % (a.file, cur, a.from_md5))
    if "def _redate_lines(con):" not in src:
        sys.exit("REFUSING: _redate_lines is not in this file. S282 has nothing to patch.")
    n = src.count(A_OLD)
    if n != 1:
        sys.exit("REFUSING: the anchor matched %d times, expected exactly 1.\n"
                 "          Nothing was written. The file is at %s." % (n, cur))

    out = src.replace(A_OLD, A_NEW).rstrip("\n") + "\n" + HELPER
    new = out.encode("utf-8")
    if a.check:
        print("would write %s -> %s  (+%d bytes)" % (cur, md5(new), len(new) - len(raw)))
        return 0
    bak = "%s.bak_S282_%s" % (a.file, cur[:8])
    if not os.path.exists(bak):
        shutil.copy2(a.file, bak)
    io.open(a.file, "wb").write(new)
    back = md5(io.open(a.file, "rb").read())
    print("patched %s" % a.file)
    print("   was  %s" % cur)
    print("   now  %s   <-- READ BACK FROM DISK. This is the pin." % back)
    print("   backup %s" % bak)
    return 0 if back == md5(new) else 4


if __name__ == "__main__":
    sys.exit(main())
