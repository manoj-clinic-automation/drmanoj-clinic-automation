"""
One-time migration: add a Patient_UID column to data/patient_diagnosis.csv
so the diagnosis layer is keyed by clinical identity (Patient UID) instead
of mobile number (P0-03 fix).

How it works
------------
For each diagnosis row, the patient's Mobile_Clean is looked up in
data/patient_master.csv:

  * mobile maps to exactly ONE patient  -> Patient_UID written
  * mobile is shared by several patients -> Patient_UID left blank and the
    row is listed at the end for manual assignment (do it once; usually a
    handful of family-shared numbers)
  * mobile not found in master           -> left blank, listed

Safe to re-run: it only fills blank Patient_UID cells and never overwrites
an existing UID. A timestamped backup of the original file is written to
data/backups/ before any change.

Run from the tracker folder:   python migrate_diagnosis_add_uid.py
"""

import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
DIAG = BASE / "data" / "patient_diagnosis.csv"
MASTER = BASE / "data" / "patient_master.csv"
BACKUPS = BASE / "data" / "backups"


def main():
    if not DIAG.exists():
        print(f"Nothing to do — {DIAG} does not exist yet.")
        return
    if not MASTER.exists():
        print(f"Cannot migrate — {MASTER} not found. Initialise the patient "
              "master first.")
        return

    d = pd.read_csv(DIAG, dtype=str).fillna("")
    m = pd.read_csv(MASTER, dtype=str).fillna("")

    if "Patient_UID" not in d.columns:
        d["Patient_UID"] = ""

    # mobile -> list of UIDs in master
    mob_to_uids = {}
    for _, r in m.iterrows():
        mob = str(r.get("Mobile_Clean", "")).strip()
        uid = str(r.get("Patient_UID", "")).strip()
        if mob and uid:
            mob_to_uids.setdefault(mob, [])
            if uid not in mob_to_uids[mob]:
                mob_to_uids[mob].append(uid)

    filled, shared, missing = 0, [], []
    for idx, r in d.iterrows():
        if str(r.get("Patient_UID", "")).strip():
            continue  # already assigned — never overwrite
        mob = str(r.get("Mobile_Clean", "")).strip()
        uids = mob_to_uids.get(mob, [])
        if len(uids) == 1:
            d.at[idx, "Patient_UID"] = uids[0]
            filled += 1
        elif len(uids) > 1:
            shared.append((idx, mob, r.get("Standardized_Diagnosis", ""), uids))
        else:
            missing.append((idx, mob, r.get("Standardized_Diagnosis", "")))

    # backup, then write
    BACKUPS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(DIAG, BACKUPS / f"{stamp}_pre_uid_migration_patient_diagnosis.csv")
    d.to_csv(DIAG, index=False)

    print(f"Done. UID filled for {filled} rows.")
    if shared:
        print(f"\n{len(shared)} row(s) use a SHARED mobile — assign Patient_UID "
              "manually in patient_diagnosis.csv (pick the correct family member):")
        for idx, mob, diag, uids in shared:
            print(f"  row {idx + 2}: mobile {mob} | diagnosis '{diag}' | "
                  f"candidates: {', '.join(uids)}")
    if missing:
        print(f"\n{len(missing)} row(s) have a mobile not found in the master "
              "(left blank — these rows will simply not enrich until fixed):")
        for idx, mob, diag in missing:
            print(f"  row {idx + 2}: mobile {mob} | diagnosis '{diag}'")
    if not shared and not missing:
        print("All diagnosis rows now carry a Patient_UID. Migration complete.")


if __name__ == "__main__":
    main()
