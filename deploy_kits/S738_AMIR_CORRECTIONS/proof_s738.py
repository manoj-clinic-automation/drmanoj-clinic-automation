#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proof_s738.py -- S738: Amir's correction list as it stands now, on this box's own databases, READ ONLY (both opened mode=ro; only
scan_register.s738_fixes, which reads).
    python3 -B proof_s738.py <new finance dir> <shared dir> <finance.db> <assets.db>
Prints each correction (supplier, bill, bill date, scan, kind, Marg, paper, the lines named) and one last line:
    PROOF S738: N correction(s) for Amir (less a, more b, twice c) -- or "PROOF S738: ERROR ...".
Supplier names, bill numbers, scan stamps and amounts only -- no phone number, no patient detail."""
import os
import sqlite3
import sys
import traceback


def rs(p):
    if p is None:
        return "-"
    p = int(p)
    return "Rs %s%s" % ("{:,}".format(abs(p) // 100), (".%02d" % (abs(p) % 100)) if p % 100 else "")


def main():
    if len(sys.argv) < 5:
        print(__doc__)
        print("PROOF S738: ERROR usage")
        return 2
    new, shared, db, adb = (os.path.abspath(x) for x in sys.argv[1:5])
    sys.path.insert(0, shared)
    sys.path.insert(0, new)
    os.environ["SHARED_LIB_DIR"] = shared
    import warnings
    warnings.simplefilter("ignore")
    try:
        import purchase_app as PA
        PA._assets_db = adb
        import scan_register as SR
        con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=30)
        con.row_factory = sqlite3.Row
        fx = SR.s738_fixes(con)
    except Exception:                                         # noqa: BLE001
        print(traceback.format_exc()[-1500:])
        print("PROOF S738: ERROR the list could not be read")
        return 1
    k = {"less": 0, "more": 0, "double": 0}
    print("S738 proof · read only · Amir's corrections:")
    for f in fx:
        k[f["kind"]] = k.get(f["kind"], 0) + 1
        print("  %-30s %-12s %s  %-8s %-6s Marg %s · paper %s" % ((f["supplier"] or "")[:30], (f["bill_no"] or "")[:12], f["date"], f.get("stamp") or "-",
                                                             f["kind"], rs(f["marg_p"]), rs(f.get("paper_p"))))
        for i in f.get("items") or []:
            print("      not in Marg: %s · %s · %s" % (str(i.get("name"))[:40], i.get("qty"), rs(i.get("amount_p"))))
    print("PROOF S738: %d correction(s) for Amir (less %d, more %d, twice %d)" % (len(fx), k["less"], k["more"], k["double"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
