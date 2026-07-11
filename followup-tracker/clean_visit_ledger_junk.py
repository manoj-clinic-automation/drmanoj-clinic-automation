#!/usr/bin/env python3
"""
clean_visit_ledger_junk.py — S135 one-time cleanup (F-34 family)

Removes non-patient footer rows that the OLD consultation-report format leaked
into data/visit_ledger.csv (seen 09-Jul-2026: payment-mode summary rows such as
"Credit Card" / "Cash" ingested as patients). A real Docterz Patient UID is
8-14 uppercase letters/digits; any row whose Patient_UID is not UID-shaped is
export furniture, never a patient.

SAFE BY DEFAULT:
  python clean_visit_ledger_junk.py            -> PREVIEW only (shows rows, writes nothing)
  python clean_visit_ledger_junk.py --apply    -> backs up the ledger, then removes the rows

The backup is written next to the ledger as visit_ledger_BACKUP_<timestamp>.csv
(this backup is the manual rollback: copy it back over visit_ledger.csv).
"""
import re
import sys
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

LEDGER = Path(__file__).resolve().parent / "data" / "visit_ledger.csv"
UID_RE = re.compile(r"^[A-Z0-9]{8,14}$")

def main() -> int:
    apply = "--apply" in sys.argv
    if not LEDGER.exists():
        print(f"ERROR: ledger not found at {LEDGER}")
        return 1
    df = pd.read_csv(LEDGER, dtype=str).fillna("")
    if "Patient_UID" not in df.columns:
        print("ERROR: no Patient_UID column — wrong file? Nothing done.")
        return 1
    bad = ~df["Patient_UID"].apply(lambda u: bool(UID_RE.fullmatch(str(u).strip())))
    n = int(bad.sum())
    print(f"Ledger rows: {len(df)}   junk (non-UID-shaped) rows found: {n}")
    for _, row in df[bad].iterrows():
        print("  JUNK:", " | ".join(str(row.get(c, "")) for c in
              ("Visit_ID", "Patient_UID", "Clinic_Specific_Id",
               "Patient_Name", "Visit_Date", "Source_File")))
    if n == 0:
        print("Nothing to clean.")
        return 0
    if not apply:
        print("\nPREVIEW ONLY — nothing written. Re-run with --apply to remove these rows.")
        return 0
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = LEDGER.with_name(f"visit_ledger_BACKUP_{stamp}.csv")
    shutil.copy2(LEDGER, backup)
    df[~bad].to_csv(LEDGER, index=False)
    print(f"\nRemoved {n} row(s). Backup saved: {backup.name}")
    print("Rollback if ever needed: copy the backup back over visit_ledger.csv")
    return 0

if __name__ == "__main__":
    sys.exit(main())
