#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s827.py -- S827_LINES_TO_THE_LIVE_BILL (F-1243): makes the new /root/finance/purchase_app.py from the LIVE bytes by exact,
counted replacements; refuses any other starting file.
    python3 -B make_s827.py <live purchase_app.py> <out file>
The change: an item line Marg prints without a supplier (BILLITEMWISE) is given its supplier only from the bills of the EFFECTIVE
bill-wise exports (EFF_BILL) -- never from a bill an older, superseded export still holds. A bill Amir moved from one dealer to another
in Marg (Deepam 502, 18-Aug: Mannat in the 02-Sep list, Deepam in the 17-Sep list) gets its lines under the dealer Marg says now.
Two lines: _store_lines' one-bill test and _redate_lines' bill list (which _line_owner_s282 also reads). Nothing else changes."""
import hashlib
import sys

FROM = "98ae8f76cf7ad2311e1152a005e8f1f4"

R = [
('''            k2 = con.execute("SELECT DISTINCT supplier_norm FROM purchase_bill WHERE bill_no=? "
                             "AND bill_date=?", (bno, d)).fetchall()''',
 '''            k2 = con.execute("SELECT DISTINCT b.supplier_norm FROM purchase_bill b WHERE b.bill_no=? "     # S827: live bills only
                             "AND b.bill_date=? AND " + EFF_BILL, (bno, d)).fetchall()'''),
('''    for r in con.execute("SELECT supplier_norm, bill_no, bill_date FROM purchase_bill "
                         "WHERE bill_date IS NOT NULL ORDER BY bill_date"):''',
 '''    for r in con.execute("SELECT b.supplier_norm, b.bill_no, b.bill_date FROM purchase_bill b "     # S827 (F-1243): the bills of the
                         "WHERE b.bill_date IS NOT NULL AND " + EFF_BILL + " ORDER BY b.bill_date"):   # live exports only'''),
]


def main():
    src, out = sys.argv[1], sys.argv[2]
    b = open(src, "rb").read()
    h = hashlib.md5(b).hexdigest()
    if h != FROM:
        print("make_s827: the live file is %s, not %s -- STOP" % (h[:8], FROM[:8]))
        return 2
    t = b.decode("utf-8")
    for i, (old, new) in enumerate(R, 1):
        n = t.count(old)
        if n != 1:
            print("make_s827: replacement %d found %d times -- STOP" % (i, n))
            return 2
        t = t.replace(old, new, 1)
    nb = t.encode("utf-8")
    open(out, "wb").write(nb)
    print("make_s827: %s -> %s" % (FROM[:8], hashlib.md5(nb).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
