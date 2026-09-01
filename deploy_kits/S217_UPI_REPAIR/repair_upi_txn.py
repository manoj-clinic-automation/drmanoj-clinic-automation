#!/usr/bin/env python3
"""
repair_upi_txn.py -- S217: restore the real bank transactions after the
30-Aug 00:25 fixture write.

WHAT HAPPENED (measured from the 01-Sep nightly backup): at 2026-08-30T00:25:16
nine synthetic statements (rrn='RRN1', Rs 999, txn_time 20:00:00) were written
into the LIVE upi_txn store. store_txns() deletes per (merchant, day) before
inserting, so the real bank detail for those nine days was wiped:
medical 14,16,19,20,21,23,25,26,28 Aug 2026. upi_statement (the day totals)
was untouched and is the reference for verifying this repair.

WHAT THIS DOES, in order:
  1. backs up finance.db (sqlite3 backup API, timestamped, verified size > 0)
  2. re-runs finance_upi.backfill_txns() over the raw statement store --
     every real MPR file is re-parsed and its upi_txn rows rewritten
  3. deletes any surviving fixture rows (rrn='RRN1')
  4. re-runs finance_upi.reconcile_upi() for every (unit, day) that has a
     statement since 2026-08-01 -- so a day filed AFTER its statement arrived
     (the 28-Aug hole) finally gets its mismatch flag
  5. prints a per-day verdict table: statement count/total vs upi_txn
     count/total, OK or STILL SHORT

DRY-RUN BY DEFAULT. Nothing is written without --apply.
With --apply, steps 2-4 run inside the live database; step 1 always runs first.

USAGE (on the VPS):
  /root/wa/venv/bin/python3 /root/finance/repair_upi_txn.py            # dry-run
  /root/wa/venv/bin/python3 /root/finance/repair_upi_txn.py --apply   # repair
"""
import datetime as dt
import os
import sqlite3
import sys

FIN_DIR = os.environ.get("FIN_DIR", "/root/finance")
DB_PATH = os.environ.get("FINANCE_DB", os.path.join(FIN_DIR, "finance.db"))
BACKUP_DIR = os.environ.get("FIN_BACKUP_DIR", "/root/backups/finance")
SINCE = os.environ.get("REPAIR_SINCE", "2026-08-01")

sys.path.insert(0, FIN_DIR)


def find_store_dir():
    """The raw-MPR store. finance_app passes it to ingest_statement; the
    canonical location is <FIN_DIR>/upi_statements. Refuse rather than guess
    an empty directory -- a backfill over nothing would 'succeed' silently."""
    cand = [os.path.join(FIN_DIR, "upi_statements"),
            os.path.join(FIN_DIR, "statements")]
    for c in cand:
        if os.path.isdir(c) and os.listdir(c):
            return c
    raise SystemExit("REFUSED: no non-empty statement store found in %s -- "
                     "checked %s. Name it with FIN_STORE_DIR." % (FIN_DIR, cand))


def table(con, sql, *args):
    return [dict(r) for r in con.execute(sql, args)]


def verdicts(con):
    rows = table(con, """
        SELECT s.unit, s.statement_date d, s.txn_count st_n,
               s.parsed_total_p st_p,
               (SELECT COUNT(*) FROM upi_txn t
                 WHERE t.unit=s.unit AND t.txn_date=s.statement_date) tx_n,
               (SELECT COALESCE(SUM(amount_p),0) FROM upi_txn t
                 WHERE t.unit=s.unit AND t.txn_date=s.statement_date) tx_p
        FROM upi_statement s WHERE s.statement_date >= ? ORDER BY 1,2""", SINCE)
    bad = 0
    print("%-8s %-11s %13s %13s  %s" % ("unit", "day", "statement", "txn-store", "verdict"))
    for r in rows:
        ok = (r["st_n"] == r["tx_n"]) and (r["st_p"] == r["tx_p"])
        bad += (not ok)
        print("%-8s %-11s %5d /%7.2f %5d /%7.2f  %s"
              % (r["unit"], r["d"], r["st_n"], r["st_p"] / 100.0,
                 r["tx_n"], r["tx_p"] / 100.0, "ok" if ok else "STILL SHORT"))
    return bad


def main():
    apply_ = "--apply" in sys.argv
    if not os.path.exists(DB_PATH):
        raise SystemExit("REFUSED: %s not found" % DB_PATH)
    store = os.environ.get("FIN_STORE_DIR") or find_store_dir()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    fx = table(con, "SELECT unit, txn_date, COUNT(*) n FROM upi_txn "
                    "WHERE rrn='RRN1' GROUP BY 1,2 ORDER BY 2")
    print("== fixture rows now: %d day(s) ==" % len(fx))
    for r in fx:
        print("   %(unit)s %(txn_date)s x%(n)d" % r)
    print("== store dir: %s (%d files) ==" % (store, len(os.listdir(store))))
    print("== BEFORE ==")
    verdicts(con)

    if not apply_:
        print("\nDRY-RUN ONLY. Re-run with --apply to repair.")
        return 0

    # 1 -- backup, verified
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bpath = os.path.join(BACKUP_DIR, "finance_pre_S217_repair_%s.db" % stamp)
    bdst = sqlite3.connect(bpath)
    con.backup(bdst)
    bdst.close()
    if os.path.getsize(bpath) <= 0:
        raise SystemExit("REFUSED: backup came out empty at %s" % bpath)
    print("backup written: %s (%d bytes)" % (bpath, os.path.getsize(bpath)))

    # 2a -- QUARANTINE fixture files first. The smoke suite's test statements
    #        were stored into the LIVE store by the upi-statement route; a
    #        backfill replays the store, which is exactly how the 30-Aug 00:25
    #        wipe happened. Real MPR files carry the 15-digit MID in their
    #        stored name (<sha10>_<MID>_...); a stored name without one is a
    #        fixture (the smoke posts them as plain 'mpr.xlsx').
    qdir = os.path.join(store, "_quarantine_S217")
    moved = []
    for f in sorted(os.listdir(store)):
        p = os.path.join(store, f)
        if not os.path.isfile(p):
            continue
        if not __import__("re").search(r"_\d{15}_", "_" + f):
            os.makedirs(qdir, exist_ok=True)
            os.replace(p, os.path.join(qdir, f))
            moved.append(f)
    print("fixture files quarantined to %s: %d" % (qdir, len(moved)))
    for f in moved:
        print("   " + f)

    # 2b -- backfill from the real files
    import finance_upi
    res = finance_upi.backfill_txns(con, store)
    print("backfill: %s" % (res,))

    # 3 -- any fixture row that survived (its fake file is not in the store,
    #      so the per-day delete may not have covered its day)
    n = con.execute("DELETE FROM upi_txn WHERE rrn='RRN1'").rowcount
    con.commit()
    print("fixture rows deleted after backfill: %d" % n)

    # 4 -- re-run the arbiter for every statement day since SINCE
    opened = 0
    for r in table(con, "SELECT DISTINCT unit, statement_date d FROM upi_statement "
                        "WHERE statement_date >= ? ORDER BY 2", SINCE):
        out = finance_upi.reconcile_upi(con, r["unit"], r["d"])
        if out and not out["match"]:
            opened += 1
            print("MISMATCH now flagged: %s %s bank %.2f entered %.2f"
                  % (r["unit"], r["d"], out["bank_p"] / 100.0, out["entered_p"] / 100.0))
    print("open mismatches after re-run: %d" % opened)

    print("== AFTER ==")
    bad = verdicts(con)
    print("\nRESULT: %s" % ("ALL DAYS AGREE with their statements" if bad == 0
                            else "%d day(s) STILL SHORT -- read the table above" % bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
