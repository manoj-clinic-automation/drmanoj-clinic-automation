#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proof_s827.py -- S827: the purchase lines as one copy of purchase_app re-files them, on a COPY of this box's finance.db (the copy is
made by the caller with sqlite's backup; the live database is never written by this script).
    python3 -B proof_s827.py read <finance code dir> <a COPY of finance.db> <out.json>   (runs _redate_lines on the copy, dumps every line)
    python3 -B proof_s827.py compare <old.json> <new.json>
PROVEN only when the new file re-files every line exactly as the old one does, except the item lines of the bill Marg moved
(Deepam 502, 18-Aug), which go to DEEPAM PHARMA. Last line:  PROOF S827: PROVEN (N lines compared, M differ: the moved bill) | NOT PROVEN <why>"""
import json
import os
import sqlite3
import sys
import traceback


def read(code, db, out):
    sys.path.insert(0, code)
    import warnings
    warnings.simplefilter("ignore")
    try:
        import purchase_app as PA
        con = sqlite3.connect(db, timeout=30)
        PA._redate_lines(con)
        con.commit()
        d = {str(r[0]): [r[1], r[2], r[3], r[4]] for r in con.execute("SELECT id, supplier_norm, bill_date, month, bill_no FROM purchase_line")}
    except Exception:                                         # noqa: BLE001
        print(traceback.format_exc()[-1200:])
        print("PROOF S827: ERROR")
        return 1
    json.dump(d, open(out, "w"))
    print("read: %d lines re-filed by %s" % (len(d), code))
    return 0


def compare(a, b):
    o, n = json.load(open(a)), json.load(open(b))
    diff = [k for k in set(o) | set(n) if o.get(k) != n.get(k)]
    bad = [k for k in diff if not (n.get(k) and n[k][0] == "DEEPAM PHARMA" and o.get(k) and o[k][0] in (None, "MANNAT PHARMA") and n[k][1] == "2026-08-18" and str(n[k][3]) == "502")]
    for k in sorted(diff, key=int)[:10]:
        print("  line %s: %s -> %s" % (k, o.get(k), n.get(k)))
    print("PROOF S827: " + ("PROVEN (%d lines compared, %d differ: the moved bill)" % (len(o), len(diff)) if not bad
                            else "NOT PROVEN -- %d line(s) other than the moved bill re-filed differently" % len(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    if len(sys.argv) >= 5 and sys.argv[1] == "read":
        sys.exit(read(*(os.path.abspath(x) for x in sys.argv[2:5])))
    if len(sys.argv) >= 4 and sys.argv[1] == "compare":
        sys.exit(compare(sys.argv[2], sys.argv[3]))
    print(__doc__)
    sys.exit(2)
