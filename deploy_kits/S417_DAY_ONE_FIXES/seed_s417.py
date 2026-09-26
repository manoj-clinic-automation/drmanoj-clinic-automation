#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_s417.py -- kit S417_DAY_ONE_FIXES (F-636). The one data step of the kit, run by the installer ON THE LIVE DATABASE after the
files are placed (the database is backed up first with the backup API), and by the walk on a scratch copy:

  every card file on the shelf (the locked originals and the decrypted copies) is looked at again by the new reader -- statement date,
  period and card number read from the decrypted PDF, the locked original marked 'duplicate of decrypted' (or its month 'decrypted
  copy not yet made'), each card slot learns its card number(s); the All_Transactions.xlsx row in the Credit Card Statements root
  becomes the running Excel (all_txn). Bank statements are not touched (packs.process_inbox re-reads only what is unplaced or unread,
  as every night at 05:40). Idempotent.

  seed_s417.py --app /root/finance --db /root/finance/finance.db
Prints counts and last-four tails only.
"""
import argparse
import os
import sqlite3
import sys


def seed(app, db_path):
    sys.path.insert(0, app)
    os.environ["FINANCE_DB"] = db_path
    import packs                                                # noqa: PLC0415 -- the placed (S417) packs.py
    con = sqlite3.connect(db_path, timeout=60)
    con.row_factory = sqlite3.Row
    packs.ensure(con)
    n = con.execute("UPDATE stmt_file SET read_status=NULL WHERE folder IN ('cards','decrypted')").rowcount
    con.commit()
    res = packs.process_inbox(con)
    print("  card files re-read: %d -> %s" % (n, res))
    q = lambda s, *a: con.execute(s, a).fetchall()             # noqa: E731
    dec = q("SELECT COUNT(*), SUM(CASE WHEN read_status='read' AND period_to IS NOT NULL THEN 1 ELSE 0 END) FROM stmt_file WHERE folder='decrypted'")[0]
    orig = q("SELECT COUNT(*), SUM(CASE WHEN read_status=? THEN 1 ELSE 0 END), SUM(CASE WHEN matched_status=? THEN 1 ELSE 0 END) FROM stmt_file WHERE folder='cards'",
             packs.DUP_OF_DECRYPTED, packs.NO_TWIN)[0]
    print("  decrypted card statements: %d, read with their statement date: %d" % (dec[0], dec[1] or 0))
    print("  locked originals: %d -- duplicate of decrypted %d, decrypted copy not yet made %d" % (orig[0], orig[1] or 0, orig[2] or 0))
    for r in q("SELECT key, ident_tail, owner_set FROM stmt_slot WHERE kind='card' ORDER BY sort"):
        print("  %-20s tails %s  (%s)" % (r["key"], " / ".join("…" + t for t in (r["ident_tail"] or "").split(",") if t) or "none", (r["owner_set"] or "")[:70]))
    for m in ("2026-07", "2026-08", "2026-09"):
        cl = [c for c in packs.cells(con, m) if c["kind"] == "card"]
        print("  %s cards: %s" % (m, " · ".join("%s=%s%s" % (c["slot"], c["state"], (" (%s)" % c["file"]["period_to"]) if c["file"] else "") for c in cl)))
    print("  all_txn rows: %d · unplaced now: %d (%s)" % (q("SELECT COUNT(*) FROM stmt_file WHERE folder='all_txn'")[0][0], len(packs.unplaced(con)),
                                                      ", ".join(sorted({"locked" if u["locked"] else (u["folder"] or "?") for u in packs.unplaced(con)}))))
    con.close()
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--db", required=True)
    a = ap.parse_args()
    sys.exit(seed(a.app, a.db))
