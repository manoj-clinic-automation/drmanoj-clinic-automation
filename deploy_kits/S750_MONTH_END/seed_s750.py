#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_s750.py -- S750: the two tables the owner's answers are kept in (s750_answer, s750_dealer_of), made once at the install so every read
finds them (a GET never creates a table). Nothing else is written; no row is seeded.
    python3 -B seed_s750.py <finance code dir> <shared dir> <finance.db> [--dry]
The last line: 'SEED S750: tables present: s750_answer, s750_dealer_of' or 'SEED S750: DRY -- would create: ...'."""
import os
import sqlite3
import sys


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    code, shared, db = (os.path.abspath(x) for x in sys.argv[1:4])
    dry = "--dry" in sys.argv
    sys.path.insert(0, shared)
    sys.path.insert(0, code)
    os.environ["SHARED_LIB_DIR"] = shared
    import warnings
    warnings.simplefilter("ignore")
    import scan_register as SR
    con = sqlite3.connect("file:%s?mode=%s" % (db, "ro" if dry else "rw"), uri=True, timeout=30)
    have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('s750_answer','s750_dealer_of')")}
    want = {"s750_answer", "s750_dealer_of"}
    if dry:
        print("SEED S750: DRY -- would create: %s" % (", ".join(sorted(want - have)) or "nothing (both present)"))
        return 0
    SR.s750_ensure(con)
    con.commit()
    have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('s750_answer','s750_dealer_of')")}
    con.close()
    if have != want:
        print("SEED S750: ERROR tables missing: %s" % ", ".join(sorted(want - have)))
        return 1
    print("SEED S750: tables present: s750_answer, s750_dealer_of")
    return 0


if __name__ == "__main__":
    sys.exit(main())
