#!/usr/bin/env python3
"""marg_backfill.py — v2 — Marg fortnight/month backfill for the medical unit.

DRY RUN BY DEFAULT. Nothing is written without --apply.

WHAT v2 ADDS OVER v1 (S182)
---------------------------
v1 wrote only the bill level (sale_item). v2 writes BOTH halves per day:

    bills → finance_ingest.ingest_day()        → sale_item        (revenue spine)
    items → finance_returns.load_lines()        → sale_line_item   (drug lines)

The drug lines are what the sale-return pipeline (D314/D315) matches against, so
without them a return can never be corroborated by the medicines returned. v1
left sale_line_item empty; v2 fills it, tying every line to the SAME
ingest_batch as its bills so a re-ingest supersedes both halves together.

Why read_report(keep_items=True): v1 called it with the default keep_items=False,
so day["items"] was empty and a naive "write lines too" bolt-on would have
written ZERO lines while reporting success — the silent-zero trap. v2 requires
item detail and refuses a file exported without it (unless --allow-no-items).

WHAT MAKES A RE-INGEST SAFE (the "once entered will not duplicate" guarantee)
-----------------------------------------------------------------------------
  * ingest_day supersedes the day's previous batch and deletes the sale_item it
    produced. v2 additionally clears sale_line_item for the day BY day_entry_id
    before loading, because ingest_day does NOT touch sale_line_item and
    load_lines only replaces bill-by-bill — so a day re-ingested with fewer
    bills would otherwise orphan lines. Clearing by day_entry_id makes both
    halves supersede identically.
  * sale_item / sale_line_item are the ATTRIBUTION spine. They reconcile to the
    day total and CANNOT move it (v_day_attribution: day_total_p comes from
    day_line, attributed_p from sale_item — separate). So re-ingesting a day
    that is already filed and APPROVED re-computes attribution only and cannot
    disturb Darpan's declared cash/UPI or the approved total. That is what makes
    a multi-day catch-up export safe to run over already-entered days.

PHI: bill rows carry a patient name and phone_last4 (F-86 — never a full
number). This script prints COUNTS AND AMOUNTS ONLY, never a row. The item CSV
carries no patient identity at all (only a bill number links back).

APPLY (on the box, after the migration and a backup):
    /root/wa/venv/bin/python3 is NOT used here — the finance app is system
    python3 (F-53):
        /usr/bin/python3 marg_backfill.py <export.xls|.xlsx>            # dry run
        /usr/bin/python3 marg_backfill.py <export.xls|.xlsx> --apply    # write
"""
import argparse
import csv
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
    ap = argparse.ArgumentParser(description="Backfill a Marg export into clinic-finance (v2: bills + drug lines)")
    ap.add_argument("xls", help="path to the Marg BILL WISE export (.xls or .xlsx)")
    ap.add_argument("--unit", default="medical")
    ap.add_argument("--db", default=DB)
    ap.add_argument("--apply", action="store_true",
                    help="actually write. Without this, nothing is changed.")
    ap.add_argument("--allow-no-items", action="store_true",
                    help="permit a file exported WITHOUT item detail (bills only, "
                         "sale_line_item left empty for those days). Off by default so "
                         "a mis-exported file is refused, not silently half-loaded.")
    a = ap.parse_args(argv)

    if LIVE not in sys.path:
        sys.path.insert(0, LIVE)
    # When rehearsing offline, the modules live beside this script.
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        import marg_report
        import finance_ingest
        import finance_returns
    except ImportError as ex:
        print("!! cannot import finance modules (%s) — run this on the VPS or beside the modules" % ex)
        return 2

    if not os.path.exists(a.db):
        print("!! no database at %s" % a.db)
        return 2

    # ---- parse first, WITH item detail. A file that fails its own checks
    #      never reaches the db.
    try:
        rep = marg_report.read_report(a.xls, keep_items=True)
    except Exception as ex:                                     # noqa: BLE001
        print("REFUSED: %s" % ex)
        return 2

    total_items = sum(len(d.get("items", [])) for d in rep["days"])
    print("%s  [%s]  bills=%d  item lines=%d"
          % (rep.get("title", "?"), rep.get("variant", "?"),
             sum(len(d["bills"]) for d in rep["days"]), total_items))
    for w in rep.get("warnings", []):
        print("WARNING: %s" % w)

    if total_items == 0 and not a.allow_no_items:
        print("\n!! REFUSING — this export carries NO item detail (0 drug lines).")
        print("   v2 writes both the bills AND the drug lines the return pipeline needs.")
        print("   Re-export from Marg with 'With Item Deta. = Yes', or pass")
        print("   --allow-no-items to load bills only (sale_line_item stays empty).")
        return 3

    days = marg_report.day_totals(rep)

    # The adapter drops a bill whose NET is exactly zero — a procedure-type
    # write-off (gross cancelled by an equal DR/CR) that Marg zeroes itself.
    # So the number of rows the adapter will accept for a day is the count of
    # NON-ZERO bills, not every CSV line. Using all lines as the expectation
    # false-aborts on any day carrying such a bill (caught in offline test,
    # F-87). Negatives (credit notes) are kept as returns, so they count here.
    nonzero_by_day = {}
    for day in rep["days"]:
        nonzero_by_day[day["date"]] = sum(1 for b in day["bills"] if b["net_p"] != 0)

    con = sqlite3.connect(a.db)
    con.row_factory = sqlite3.Row

    # sale_line_item must exist (finance_returns.sql, S180). Fail clearly if not.
    has_lines = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='sale_line_item'").fetchone()
    if not has_lines:
        print("\n!! sale_line_item table is missing — apply finance_returns.sql first.")
        return 2

    # ---- PRE-FLIGHT: the adapter must actually be able to read this CSV ------
    # _colmap() returns ({}, {}) when no source row exists, and adapter_csv then
    # reads ZERO rows while ingest_day still reports ok. Both the source and the
    # column map are checked against the REAL header marg_report emits.
    probe = io.StringIO()
    marg_report.write_lines_csv(rep, probe, days[0]["business_date"])
    header = probe.getvalue().splitlines()[0].split(",")
    src = con.execute("SELECT id, active FROM ingest_source WHERE unit=? AND adapter='marg_export'",
                      (a.unit,)).fetchone()
    if not src:
        print("\n!! REFUSING — no ingest_source row for (%s, marg_export)." % a.unit)
        print("   Apply finance_migration_S183_marg_map.sql first.")
        return 4
    if not src["active"]:
        print("\n!! REFUSING — the (%s, marg_export) source is marked INACTIVE." % a.unit)
        print("   Apply finance_migration_S183_marg_map.sql (it sets active=1).")
        return 4
    cmap = {r["our_field"]: r["their_column"] for r in con.execute(
        "SELECT our_field, their_column FROM ingest_column_map WHERE source_id=?", (src["id"],))}
    if not cmap:
        print("\n!! REFUSING — (%s, marg_export) has no column map." % a.unit)
        print("   Apply finance_migration_S183_marg_map.sql first.")
        return 4
    missing = {f: c for f, c in cmap.items() if c not in header}
    print("\ncolumn map: %d field(s) mapped; CSV header = %s" % (len(cmap), ",".join(header)))
    if missing:
        print("!! REFUSING — the column map does not match what marg_report.py emits.")
        for f, c in sorted(missing.items()):
            print("     our_field %-14s -> %-18s NOT in the CSV header" % (f, repr(c)))
        print("   This is the silent-zero-rows trap. Fix the map (or the parser).")
        return 4
    print("column map matches the parser output — safe to proceed.")

    # ---- survey BEFORE touching anything ------------------------------------
    print("\n%-12s %-11s %6s %12s %10s %8s" %
          ("DATE", "DAY", "BILLS", "NET", "EXIST BILL", "EXIST LN"))
    plan, reachable, blocked, would_del_bill, would_del_line = [], 0, 0, 0, 0
    for t in days:
        iso = t["business_date"]
        e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                        (a.unit, iso)).fetchone()
        if not e:
            print("%-12s %-11s %6d %12.2f %10s %8s" %
                  (iso, "NOT FILED", t["bills"], t["net_p"] / 100.0, "-", "-"))
            blocked += 1
            continue
        eid = e["id"]
        nb = con.execute(
            "SELECT COUNT(*) c FROM sale_item WHERE ingest_batch_id IN "
            "(SELECT id FROM ingest_batch WHERE day_entry_id=? AND status!='superseded')",
            (eid,)).fetchone()["c"]
        nl = con.execute("SELECT COUNT(*) c FROM sale_line_item WHERE day_entry_id=?",
                         (eid,)).fetchone()["c"]
        print("%-12s %-11s %6d %12.2f %10d %8d" %
              (iso, "filed", t["bills"], t["net_p"] / 100.0, nb, nl))
        plan.append((iso, eid))
        reachable += 1
        would_del_bill += nb
        would_del_line += nl

    print("\n%d of %d day(s) reachable · %d not filed (refused, harmlessly)"
          % (reachable, len(days), blocked))
    if would_del_bill or would_del_line:
        print("!! re-ingest would SUPERSEDE %d existing bill line(s) and clear %d drug line(s) on those days."
              % (would_del_bill, would_del_line))
    else:
        print("No existing lines on the reachable days — nothing would be replaced.")

    if not a.apply:
        print("\nDRY RUN — nothing was written. Re-run with --apply to ingest.")
        return 0
    if not plan:
        print("\nNothing reachable to ingest. Nothing written.")
        return 0

    # ---- backup, then write -------------------------------------------------
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = "%s.bak_S183M_%s" % (a.db, stamp)
    shutil.copy2(a.db, bak)
    print("\nbackup: %s" % bak)

    ok = fail = 0
    tot_bills = tot_lines = 0
    for iso, eid in plan:
        # 1. bills -> sale_item (no commit yet; the driver owns the transaction)
        lbuf = io.StringIO()
        marg_report.write_lines_csv(rep, lbuf, iso)
        # expect the NON-ZERO bills (the adapter drops zero-net procedure
        # write-offs as junk). A column-map failure still shows as got=0 here,
        # so the silent-zero trap stays guarded.
        expect_bills = nonzero_by_day.get(iso, 0)
        try:
            res = finance_ingest.ingest_day(
                con, a.unit, iso, "marg_export", lbuf.getvalue(),
                run_by="marg_backfill_S183",
                source_ref=os.path.basename(a.xls))
            got = res.get("rows_read") or 0
            if got != expect_bills:
                con.rollback()
                print("  %s  ABORT  bill adapter read %d of %d rows — refusing to continue."
                      % (iso, got, expect_bills))
                print("\n%d day(s) ingested before the abort. Restore point: %s" % (ok, bak))
                return 5
            batch_id = res.get("batch_id")

            # 2. items -> sale_line_item, tied to the SAME batch
            ibuf = io.StringIO()
            marg_report.write_items_csv(rep, ibuf, iso)
            irows = list(csv.DictReader(io.StringIO(ibuf.getvalue())))
            # clear the day's lines first so both halves supersede identically
            con.execute("DELETE FROM sale_line_item WHERE day_entry_id=?", (eid,))
            n_lines = finance_returns.load_lines(con, a.unit, iso, irows, batch_id=batch_id)
            # load_lines commits; if it read zero from a non-empty item set, that
            # is the silent-zero trap on the LINE side — undo the whole day.
            if irows and n_lines == 0:
                con.rollback()
                print("  %s  ABORT  %d item rows but 0 lines stored — line mapping is wrong."
                      % (iso, len(irows)))
                print("\n%d day(s) ingested before the abort. Restore point: %s" % (ok, bak))
                return 5
            if not irows:
                con.commit()     # bills-only day; load_lines never ran to commit

            print("  %s  ok   bills %d/%d · lines %d · attributed %s · review %s" %
                  (iso, got, expect_bills, n_lines,
                   res.get("attributed", "?"), res.get("in_review", "?")))
            ok += 1
            tot_bills += got
            tot_lines += n_lines
        except Exception as ex:                                   # noqa: BLE001
            con.rollback()
            print("  %s  FAIL %s" % (iso, ex))
            fail += 1

    print("\n%d day(s) ingested (%d bills, %d drug lines), %d failed."
          % (ok, tot_bills, tot_lines, fail))
    if fail:
        print("Restore if needed:  systemctl stop clinic-finance && "
              "cp %s %s && systemctl start clinic-finance" % (bak, a.db))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
