#!/usr/bin/env python3
"""delete_test_assets.py -- remove the five stray owner test rows (#51..55)
from the live Asset Register DB, with their dependents (expiries, service
logs, attachments). S177 housekeeping, backlog item 4c.

SAFE BY CONSTRUCTION
--------------------
1. Dry-run is the DEFAULT: prints exactly what would go, changes nothing.
   Deletion happens only with --apply.
2. The target set is HARD-CODED to ids 51..55 -- and each row must ALSO have
   the exact name 'test'. A row that exists but is named anything else is
   REFUSED and the whole run aborts with nothing deleted (all-or-nothing,
   single transaction).
3. Before touching anything, --apply copies assets.db to a timestamped
   backup (assets.db.predelete.<stamp>) and verifies the copy's size.
4. After deleting, it re-counts and prints the verification (expected: the
   5 rows gone, 54 -> 49 assets, zero orphan dependents left behind).

Run on the VPS:
  cd /root/assetapp && python3 delete_test_assets.py           # dry-run
  cd /root/assetapp && python3 delete_test_assets.py --apply   # do it
"""
import os
import shutil
import sqlite3
import sys
import time

TARGET_IDS = (51, 52, 53, 54, 55)
REQUIRED_NAME = "test"
DB = "assets.db"


def main():
    apply = "--apply" in sys.argv[1:]
    if not os.path.exists(DB):
        print("!! %s not found here -- run from /root/assetapp." % DB)
        return 2

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    # ---- identify + verify every target row before anything else ----------
    plan, refused = [], []
    for aid in TARGET_IDS:
        r = db.execute("SELECT id, name, status FROM assets WHERE id=?", (aid,)).fetchone()
        if r is None:
            print("  #%d: already absent -- skipping." % aid)
            continue
        if (r["name"] or "").strip().lower() != REQUIRED_NAME:
            refused.append((aid, r["name"]))
            continue
        dep = {}
        dep["expiries"] = db.execute(
            "SELECT COUNT(*) FROM expiries WHERE entity='asset' AND entity_id=?", (aid,)).fetchone()[0]
        dep["service_logs"] = db.execute(
            "SELECT COUNT(*) FROM service_logs WHERE asset_id=?", (aid,)).fetchone()[0]
        dep["attachments"] = db.execute(
            "SELECT COUNT(*) FROM attachments WHERE entity='asset' AND entity_id=?", (aid,)).fetchone()[0]
        plan.append((aid, r["name"], dep))

    if refused:
        print("!! REFUSING to run -- these target ids are NOT named '%s':" % REQUIRED_NAME)
        for aid, name in refused:
            print("     #%d is named %r" % (aid, name))
        print("   Nothing was deleted. Fix the target list first.")
        return 1

    if not plan:
        print("Nothing to do -- all target rows already gone.")
        return 0

    total_before = db.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
    print("assets before: %d" % total_before)
    print("%s these rows (with dependents):" % ("DELETING" if apply else "Would delete"))
    for aid, name, dep in plan:
        print("  #%-3d %-8r expiries=%d service_logs=%d attachments=%d" % (
            aid, name, dep["expiries"], dep["service_logs"], dep["attachments"]))

    if not apply:
        print("\n(dry-run -- nothing was changed. Re-run with --apply to delete.)")
        return 0

    # ---- backup the DB file first -----------------------------------------
    stamp = time.strftime("%Y-%m-%d_%H%M%S")
    bak = "%s.predelete.%s" % (DB, stamp)
    db.execute("PRAGMA wal_checkpoint(FULL)")   # fold WAL in so the copy is complete
    shutil.copy2(DB, bak)
    if os.path.getsize(bak) != os.path.getsize(DB):
        print("!! backup size mismatch -- ABORTING, nothing deleted.")
        return 1
    print("\nDB backed up -> %s" % bak)

    # ---- delete, all-or-nothing -------------------------------------------
    ids = [aid for aid, _, _ in plan]
    marks = ",".join("?" * len(ids))
    try:
        db.execute("BEGIN")
        # stored attachment files first (none expected, but be thorough)
        for r in db.execute("SELECT stored_name FROM attachments "
                            "WHERE entity='asset' AND entity_id IN (%s)" % marks, ids):
            p = os.path.join("uploads", r["stored_name"])
            if os.path.exists(p):
                os.remove(p)
                print("  removed attachment file %s" % p)
        db.execute("DELETE FROM attachments WHERE entity='asset' AND entity_id IN (%s)" % marks, ids)
        db.execute("DELETE FROM expiries WHERE entity='asset' AND entity_id IN (%s)" % marks, ids)
        db.execute("DELETE FROM service_logs WHERE asset_id IN (%s)" % marks, ids)
        db.execute("DELETE FROM assets WHERE id IN (%s)" % marks, ids)
        db.commit()
    except Exception as ex:
        db.rollback()
        print("!! delete failed (%s) -- ROLLED BACK, nothing changed. Backup kept: %s" % (ex, bak))
        return 1

    # ---- verify -----------------------------------------------------------
    total_after = db.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
    leftover = db.execute("SELECT COUNT(*) FROM assets WHERE id IN (%s)" % marks, ids).fetchone()[0]
    orph_e = db.execute("SELECT COUNT(*) FROM expiries WHERE entity='asset' "
                        "AND entity_id IN (%s)" % marks, ids).fetchone()[0]
    orph_s = db.execute("SELECT COUNT(*) FROM service_logs WHERE asset_id IN (%s)" % marks, ids).fetchone()[0]
    orph_a = db.execute("SELECT COUNT(*) FROM attachments WHERE entity='asset' "
                        "AND entity_id IN (%s)" % marks, ids).fetchone()[0]
    print("\nVERIFY: assets %d -> %d | target rows left=%d | orphan expiries=%d "
          "service_logs=%d attachments=%d" % (
              total_before, total_after, leftover, orph_e, orph_s, orph_a))
    good = (leftover == 0 and orph_e == 0 and orph_s == 0 and orph_a == 0
            and total_after == total_before - len(ids))
    print("RESULT: %s" % ("CLEAN DELETE ✓" if good else "!! CHECK FAILED -- restore from " + bak))
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
