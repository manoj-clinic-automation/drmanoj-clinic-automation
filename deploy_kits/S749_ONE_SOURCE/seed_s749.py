#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_s749.py -- S749: the one setting the kit needs (D866: Ravi Medical Agency is an owner-confirmed supplier), written once, audited.
    python3 -B seed_s749.py <finance dir> <shared dir> <finance.db> [--dry]
Writes setting purchase.owner_confirm_suppliers = 'RAVI MEDICAL AGENCY' when the key is absent or empty; leaves any value the owner has set.
Creates the kit's two tables (s749_confirm, s749_act) so the first tap never meets a missing table. --dry prints and writes nothing.
Last line: SEED S749: written | already | dry (would write) | dry (already)."""
import os
import sqlite3
import sys

KEY, VALUE = "purchase.owner_confirm_suppliers", "RAVI MEDICAL AGENCY"


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        print("SEED S749: ERROR usage")
        return 2
    code, shared, db = (os.path.abspath(x) for x in sys.argv[1:4])
    dry = "--dry" in sys.argv
    sys.path.insert(0, shared)
    sys.path.insert(0, code)
    import warnings
    warnings.simplefilter("ignore")
    import purchase_app as PA
    import scan_register as SR
    con = sqlite3.connect(("file:%s?mode=ro" % db) if dry else db, uri=dry, timeout=30)
    con.row_factory = sqlite3.Row
    r = con.execute("SELECT value FROM setting WHERE key=?", (KEY,)).fetchone()
    have = str(r[0]).strip() if r and r[0] else ""
    key = PA.supplier_key(VALUE)
    n = sum(1 for r in con.execute("SELECT DISTINCT supplier FROM purchase_bill") if PA.supplier_key(r[0]) == key)
    nb = sum(1 for r in con.execute("SELECT supplier FROM purchase_bill") if PA.supplier_key(r[0]) == key)
    print("S749 seed · %s = %r now · the key %r names %d supplier spelling(s), %d bill(s) in Marg" % (KEY, have, key, n, nb))
    if not have and nb == 0:
        print("SEED S749: ERROR the key names no bill in Marg -- the setting would be inert (the spelling differs); nothing written")
        return 1
    if have:
        print("SEED S749: %s" % ("dry (already)" if dry else "already"))
        return 0
    if dry:
        print("SEED S749: dry (would write %s = %r and create s749_confirm, s749_act)" % (KEY, VALUE))
        return 0
    SR.s749_ensure(con)
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES (?,?)", (KEY, VALUE))
    try:
        PA._audit(con, "S749 install", "setting", KEY, dict(value=VALUE, kit="S749_ONE_SOURCE", why="D866: an owner-confirmed supplier"))
    except Exception as e:                                    # noqa: BLE001
        print("  (audit row not written: %s)" % str(e)[:120])
    con.commit()
    r = con.execute("SELECT value FROM setting WHERE key=?", (KEY,)).fetchone()
    print("SEED S749: %s" % ("written" if r and str(r[0]).strip() == VALUE else "ERROR not written"))
    return 0 if r and str(r[0]).strip() == VALUE else 1


if __name__ == "__main__":
    sys.exit(main())
