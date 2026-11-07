#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_s740.py -- S740: the owner's own word for Janta 21965 (D839: "a Rs 1,245 return signed on the bill"; 06:12 IST 07-Nov: Amir entered
only the goods kept) -- recorded as reception's "Haan, wapsi likhi hai", by scan_register.s740_seed, ONLY when the bill is on reception's
question list now (else nothing is written). Idempotent. Then the returns' tracker is filled once (s740_sync).
    python3 -B seed_s740.py <placed finance dir> <shared dir> <finance.db> <assets.db>
The last line: 'SEED S740: seeded' | 'SEED S740: already' | 'SEED S740: not_a_question' | 'SEED S740: ERROR ...'."""
import os
import sqlite3
import sys
import traceback


def main():
    if len(sys.argv) < 5:
        print(__doc__)
        print("SEED S740: ERROR usage")
        return 2
    fin, shared, db, adb = (os.path.abspath(x) for x in sys.argv[1:5])
    sys.path.insert(0, shared)
    sys.path.insert(0, fin)
    os.environ["SHARED_LIB_DIR"] = shared
    import warnings
    warnings.simplefilter("ignore")
    try:
        import purchase_app as PA
        PA._assets_db = adb
        import scan_register as SR
        con = sqlite3.connect(db, timeout=30)
        con.row_factory = sqlite3.Row
        r = SR.s740_seed(con, "JANTA PHARMACEUTICALS", "21965", "2026-10-02", "manoj (D839, S740 seed)", "D839; the owner 06:12 IST 07-Nov")
        n = SR.s740_sync(con)
        con.close()
    except Exception:                                         # noqa: BLE001
        print(traceback.format_exc()[-1500:])
        print("SEED S740: ERROR the seed could not run")
        return 1
    print("tracker filled: %d new, %d resolved, %d gone" % n)
    print("SEED S740: %s" % r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
