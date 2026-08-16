#!/usr/bin/env python3
"""marg_backfill.py — one-shot Marg fortnight backfill for the medical unit.

DRY RUN BY DEFAULT. Nothing is written without --apply.

Why this exists
---------------
`marg_report.py` reads a Marg BILL WISE export; `finance_ingest.ingest_day()`
attaches the resulting bill rows to a day that ALREADY EXISTS. The designed feed
is one day at a time. A fortnight export needs a driver that walks the days and,
crucially, TELLS YOU WHAT IT WOULD DESTROY before it destroys it.

Two behaviours of the live code make that mandatory:

  1. ingest_day() raises "no day entry for ... — file the day first" for any day
     the maker has not filed. The patient-revenue spine reads, never posts
     (D313). So this script can only reach days that already exist.

  2. Re-running ingest for a day SUPERSEDES its previous batch and DELETEs the
     sale_item / sale_item_review rows that batch produced. On a day already fed
     from another adapter, those lines go. That is correct behaviour and it is
     also exactly why a dry run and a backup come first.

PHI: bill rows carry a patient name and phone_last4 (F-86 — never a full
number). This script prints COUNTS AND AMOUNTS ONLY, never a row.
"""
import argparse
import datetime as dt
import io
import os
import shutil
import sqlite3
import sys

# Overridable so the script can be REHEARSED offline against a throwaway db.
# F-87: if a thing cannot be run before it ships, making it runnable is the
# first task, not an optional one. Defaults to the live path.
LIVE = os.environ.get("FINANCE_DIR", "/root/finance")
DB = os.path.join(LIVE, "finance.db")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Backfill a Marg fortnight export into clinic-finance")
    ap.add_argument("xls", help="path to the Marg BILL WISE .xls")
    ap.add_argument("--unit", default="medical")
    ap.add_argument("--db", default=DB)
    ap.add_argument("--apply", action="store_true",
                    help="actually write. Without this, nothing is changed.")
    a = ap.parse_args(argv)

    if LIVE not in sys.path:
        sys.path.insert(0, LIVE)
    try:
        import marg_report
        import finance_ingest
    except ImportError as ex:
        print("!! cannot import from %s (%s) — run this on the VPS" % (LIVE, ex))
        return 2

    if not os.path.exists(a.db):
        print("!! no database at %s" % a.db)
        return 2

    # ---- parse first. A file that fails its own checks never reaches the db.
    try:
        rep = marg_report.read_report(a.xls)
    except Exception as ex:
        print("REFUSED: %s" % ex)
        return 2
    if not rep.get("ok"):
        print("REFUSED — the export did not pass its own checks:")
        for e in rep.get("errors", []):
            print("   %s" % e)
        return 3
    print("%s  [%s]" % (rep["title"], rep["variant"]))
    for w in rep.get("warnings", []):
        print("WARNING: %s" % w)

    days = marg_report.day_totals(rep)
    con = sqlite3.connect(a.db)
    con.row_factory = sqlite3.Row

    # ---- PRE-FLIGHT: the adapter must actually be able to read this CSV -----
    # _colmap() returns ({}, {}) when no ingest_source row exists, and adapter_csv
    # then reads ZERO rows and ingest_day still reports ok. A silent success on
    # live patient data is the worst outcome available here, so both the source
    # and the column map are checked against the REAL header marg_report emits.
    probe = io.StringIO()
    marg_report.write_lines_csv(rep, probe, days[0]["business_date"])
    header = probe.getvalue().splitlines()[0].split(",")
    src = con.execute("SELECT id, active FROM ingest_source WHERE unit=? AND adapter='marg_export'",
                      (a.unit,)).fetchone()
    if not src:
        print("\n!! REFUSING — no ingest_source row for (%s, marg_export)." % a.unit)
        print("   The adapter would read ZERO rows and still report success.")
        print("   Register the source and its column map first.")
        return 4
    if not src["active"]:
        print("\n!! REFUSING — the (%s, marg_export) source is marked INACTIVE." % a.unit)
        return 4
    cmap = {r["our_field"]: r["their_column"] for r in con.execute(
        "SELECT our_field, their_column FROM ingest_column_map WHERE source_id=?", (src["id"],))}
    if not cmap:
        print("\n!! REFUSING — (%s, marg_export) has no column map." % a.unit)
        print("   Adapter would read ZERO rows and report success.")
        return 4
    missing = {f: c for f, c in cmap.items() if c not in header}
    print("\ncolumn map: %d field(s) mapped; CSV header = %s" % (len(cmap), ",".join(header)))
    if missing:
        print("!! REFUSING — the column map does not match what marg_report.py emits.")
        for f, c in sorted(missing.items()):
            print("     our_field %-14s -> %-18s NOT in the CSV header" % (f, repr(c)))
        print("   This is the silent-zero-rows trap: every day would ingest 0 lines")
        print("   and report ok. Fix the map (or the parser) before ingesting.")
        return 4
    print("column map matches the parser output — safe to proceed.")

    # ---- survey BEFORE touching anything ---------------------------------
    print("\n%-12s %-11s %6s %12s %10s" %
          ("DATE", "DAY", "BILLS", "NET", "EXISTING"))
    plan, reachable, blocked, would_delete = [], 0, 0, 0
    for t in days:
        iso = t["business_date"]
        e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                        (a.unit, iso)).fetchone()
        if not e:
            print("%-12s %-11s %6d %12.2f %10s" %
                  (iso, "NOT FILED", t["bills"], t["net_p"] / 100.0, "-"))
            blocked += 1
            continue
        n = con.execute(
            "SELECT COUNT(*) c FROM sale_item WHERE ingest_batch_id IN "
            "(SELECT id FROM ingest_batch WHERE day_entry_id=? AND status!='superseded')",
            (e["id"],)).fetchone()["c"]
        print("%-12s %-11s %6d %12.2f %10d" %
              (iso, "filed", t["bills"], t["net_p"] / 100.0, n))
        plan.append((iso, t["bills"]))
        reachable += 1
        would_delete += n

    print("\n%d of %d day(s) reachable · %d not filed (refused, harmlessly)"
          % (reachable, len(days), blocked))
    if would_delete:
        print("!! %d existing line(s) on those days would be SUPERSEDED and deleted."
              % would_delete)
    else:
        print("No existing lines on the reachable days — nothing would be replaced.")

    if not a.apply:
        print("\nDRY RUN — nothing was written. Re-run with --apply to ingest.")
        return 0
    if not plan:
        print("\nNothing reachable to ingest. Nothing written.")
        return 0

    # ---- backup, then write ----------------------------------------------
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = "%s.bak_S182M1_%s" % (a.db, stamp)
    shutil.copy2(a.db, bak)
    print("\nbackup: %s" % bak)

    ok = fail = 0
    for iso, _bills in plan:
        buf = io.StringIO()
        marg_report.write_lines_csv(rep, buf, iso)
        try:
            expect = len(buf.getvalue().splitlines()) - 1     # minus the header
            res = finance_ingest.ingest_day(
                con, a.unit, iso, "marg_export", buf.getvalue(),
                run_by="marg_backfill_S182",
                source_ref=os.path.basename(a.xls))
            got = res.get("rows_read") or 0
            if got != expect:
                # A zero-row or short read that still says ok is the failure this
                # whole script is shaped around. Stop the RUN, not just the day.
                con.rollback()
                print("  %s  ABORT  adapter read %d of %d rows — refusing to continue."
                      % (iso, got, expect))
                print("\n%d day(s) ingested before the abort. Database restored point: %s" % (ok, bak))
                return 5
            con.commit()
            print("  %s  ok   read %d/%d · attributed %s · review %s" %
                  (iso, got, expect, res.get("attributed", "?"), res.get("in_review", "?")))
            ok += 1
        except Exception as ex:
            print("  %s  FAIL %s" % (iso, ex))
            fail += 1

    print("\n%d day(s) ingested, %d failed." % (ok, fail))
    if fail:
        print("Restore if needed:  systemctl stop clinic-finance && "
              "cp %s %s && systemctl start clinic-finance" % (bak, a.db))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
