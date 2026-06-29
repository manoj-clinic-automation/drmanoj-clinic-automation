r"""
undo_followups.py  —  Safely remove a wrongly-loaded follow-up batch
Dr. Manoj Agarwal Clinic, Bareilly

WHAT IT FIXES
  You uploaded a whole month of follow-ups in one go by mistake. Deleting them from
  the audit Excel does nothing (that file is rebuilt from the ledger every run). The
  real rows live in data/followup_ledger.csv. This script removes that batch from the
  ledger — after backing everything up — and leaves your normal daily follow-ups alone.

HOW IT KNOWS WHICH ROWS ARE BAD
  The tracker stamps one Followup_Log_Date per upload. A normal daily upload has all
  its rows on a SINGLE due date. The bad month upload has one log date but MANY due
  dates. So the batch whose log date spans lots of due dates is the accident.

HOW TO RUN  (from inside  C:\followup tracker\ )
  1) Preview only (changes nothing):     python undo_followups.py
  2) Remove a specific batch:            python undo_followups.py --remove 2026-05-31
  It always makes a full backup of data\ before writing anything.
"""
import csv, os, sys, shutil, datetime as dt
from collections import defaultdict

HERE      = os.path.dirname(os.path.abspath(__file__))
DATA      = os.path.join(HERE, "data")
LEDGER    = os.path.join(DATA, "followup_ledger.csv")
BACKUPDIR = os.path.join(DATA, "backups")

LOG_COL, DUE_COL = "Followup_Log_Date", "Due_Date"


def load_rows():
    with open(LEDGER, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return r.fieldnames, list(r)


def summarize(rows):
    """Group by log date -> (count, distinct due dates, min due, max due)."""
    g = defaultdict(list)
    for row in rows:
        g[row.get(LOG_COL, "")].append(row.get(DUE_COL, ""))
    out = []
    for log, dues in g.items():
        dset = sorted(d for d in set(dues) if d)
        out.append({
            "log": log, "rows": len(dues),
            "distinct_due": len(dset),
            "due_min": dset[0] if dset else "",
            "due_max": dset[-1] if dset else "",
        })
    # most-spread batches first (likely the accident)
    out.sort(key=lambda x: x["distinct_due"], reverse=True)
    return out


def print_table(summary):
    print(f"\n{'Followup_Log_Date':18} {'rows':>5} {'distinct due':>13} {'due range':>26}")
    print("-" * 66)
    for s in summary:
        rng = f"{s['due_min']} .. {s['due_max']}" if s["due_min"] else ""
        flag = "  <-- looks like the bad month batch" if s["distinct_due"] >= 5 else ""
        print(f"{s['log']:18} {s['rows']:>5} {s['distinct_due']:>13} {rng:>26}{flag}")
    print()


def backup():
    os.makedirs(BACKUPDIR, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S") + "_undo"
    dest = os.path.join(BACKUPDIR, stamp)
    os.makedirs(dest, exist_ok=True)
    for name in os.listdir(DATA):
        p = os.path.join(DATA, name)
        if os.path.isfile(p) and name.endswith(".csv"):
            shutil.copy2(p, os.path.join(dest, name))
    return dest


def main():
    if not os.path.isfile(LEDGER):
        sys.exit(f"Not found: {LEDGER}\nRun this from inside your followup tracker folder.")

    fields, rows = load_rows()
    if LOG_COL not in fields or DUE_COL not in fields:
        sys.exit(f"Ledger is missing expected columns {LOG_COL}/{DUE_COL}. Aborting (nothing changed).")

    summary = summarize(rows)
    print(f"Ledger: {len(rows)} follow-up rows across {len(summary)} upload batch(es).")
    print_table(summary)

    args = sys.argv[1:]
    if "--remove" not in args:
        print("PREVIEW ONLY — nothing changed.")
        print("To remove a batch, re-run with:  python undo_followups.py --remove <Followup_Log_Date>")
        print("Example:  python undo_followups.py --remove " +
              (summary[0]["log"] if summary else "2026-05-31"))
        return

    target = args[args.index("--remove") + 1] if args.index("--remove") + 1 < len(args) else ""
    if not target:
        sys.exit("Give the log date to remove, e.g.  --remove 2026-05-31")

    doomed = [r for r in rows if r.get(LOG_COL, "") == target]
    keep   = [r for r in rows if r.get(LOG_COL, "") != target]
    if not doomed:
        sys.exit(f"No rows have Followup_Log_Date = {target}. Nothing changed.")

    dues = sorted(set(r.get(DUE_COL, "") for r in doomed))
    print(f"About to remove {len(doomed)} rows with log date {target} "
          f"(due dates {dues[0]} .. {dues[-1]}).")
    print(f"{len(keep)} rows will remain.")
    confirm = input('Type  YES  to proceed (anything else cancels): ').strip()
    if confirm != "YES":
        print("Cancelled. Nothing changed.")
        return

    dest = backup()
    print(f"Backup written: {dest}")

    tmp = LEDGER + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(keep)
    os.replace(tmp, LEDGER)   # atomic swap; never leaves a half-written ledger
    print(f"Done. Removed {len(doomed)} rows; {len(keep)} remain in followup_ledger.csv.")
    print("Re-run the tracker once to rebuild the audit Excel from the cleaned ledger.")


if __name__ == "__main__":
    main()
