#!/usr/bin/env python3
# push_patient_mirror.py
# -----------------------------------------------------------------------------
# One-way, replace-only mirror of the local patient_master.csv into the
# "Patient_Master" tab of the Clinic Callback Tracker Google Sheet.
#
# SAFETY (by design):
#   - Reads the local CSV READ-ONLY. It never writes to your local file.
#   - Pushes UP only (local -> cloud). It never reads the sheet back.
#   - Replace-only: rewrites the tab fresh each run.
#   - Refuses to push if the CSV is missing or has zero valid rows,
#     so a bad/empty file can never wipe the mirror with nothing.
#   - Only the needed columns travel up: phone, name, diagnosis, age,
#     gender, last visit, UID, and the numeric Clinic ID. (Less PHI, faster.)
#
# SESSION 30 CHANGE:
#   - Added a dedicated "Clinic_Specific_Id" output column so the numeric
#     Clinic ID travels up as its own column (the dashboard reads it by that
#     exact name). Previously the clinic id was only a low-priority alias for
#     the Patient UID, so it was being dropped whenever a real UID existed.
#   - Cleaned up: "clinicspecificid" removed from the Patient UID alias list
#     so the two IDs can never be confused.
#
# HOW TO RUN:
#   python push_patient_mirror.py            <-- PREVIEW (writes nothing)
#   python push_patient_mirror.py --push     <-- LIVE push to the sheet
# -----------------------------------------------------------------------------

import os
import sys
import csv
import json
import glob

# =============================== CONFIG ======================================
# Normally you do NOT need to change anything here.
# The script looks for the patient file and the JSON key in its OWN folder.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Your real patient master (read-only). It lives in the "data" subfolder.
LOCAL_CSV = os.path.join(BASE_DIR, "data", "patient_master.csv")

# Folder holding the service-account .json key you downloaded in Step 1.
# Default = same folder as this script. The script auto-finds the key.
KEY_DIR = BASE_DIR

# The Clinic Callback Tracker sheet + the tab the dashboard reads.
SHEET_ID = "1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0"
TAB_NAME = "Patient_Master"
# =============================================================================

# Output column order (these names are what the dashboard recognises).
OUT_HEADERS = ["Mobile", "Patient Name", "Diagnosis", "Age", "Gender", "Last Visit", "Patient UID", "Clinic_Specific_Id"]

# For each output field, the possible header names in your local CSV.
# Matching ignores case, spaces and underscores. First match wins.
FIELD_ALIASES = {
    "Mobile":             ["mobileclean", "mobile", "phone", "phonenumber", "mobileno", "mobilenumber", "mobileraw", "contact", "contactno"],
    "Patient Name":       ["patientname", "name", "fullname"],
    "Diagnosis":          ["diagnosis", "dx", "purposeofvisit", "purpose"],
    "Age":                ["age"],
    "Gender":             ["gender", "sex"],
    "Last Visit":         ["lastseendate", "lastvisit", "consultationdate", "lastvisited", "lastseen", "visitdate"],
    "Patient UID":        ["patientuid", "uid", "patientid", "id"],
    "Clinic_Specific_Id": ["clinicspecificid", "clinicid", "clinicspecific"],
}


def norm(s):
    return "".join(ch for ch in str(s).lower() if ch.isalnum())


def mask_phone(p):
    p = str(p)
    if len(p) >= 4:
        return p[:2] + "x" * (len(p) - 4) + p[-2:]
    return "xxxx"


def normalize_phone(raw):
    """Return a clean 10-digit Indian mobile, or '' if not valid."""
    digits = "".join(ch for ch in str(raw) if ch.isdigit())
    if len(digits) > 10:
        digits = digits[-10:]          # strip leading country code / zero
    if len(digits) == 10 and digits[0] in "6789":
        return digits
    return ""


def build_mapping(headers):
    """Map each output field to a column index in the CSV, by alias."""
    norm_headers = [norm(h) for h in headers]
    mapping = {}
    for field, aliases in FIELD_ALIASES.items():
        idx = None
        for alias in aliases:
            if alias in norm_headers:
                idx = norm_headers.index(alias)
                break
        mapping[field] = idx
    return mapping


def load_rows():
    if not os.path.exists(LOCAL_CSV):
        print("STOP: could not find the patient file at:")
        print("   " + LOCAL_CSV)
        print("Fix the LOCAL_CSV path near the top of this script, then rerun.")
        sys.exit(1)

    with open(LOCAL_CSV, "r", encoding="utf-8-sig", newline="") as f:
        all_rows = list(csv.reader(f))

    if not all_rows:
        print("STOP: the patient file is completely empty. Nothing pushed.")
        sys.exit(1)

    headers = all_rows[0]
    data = all_rows[1:]
    mapping = build_mapping(headers)

    print("\nColumn detection (output field  <-  your CSV column):")
    for field in OUT_HEADERS:
        idx = mapping[field]
        shown = "(NOT FOUND - will be blank)" if idx is None else '"' + str(headers[idx]) + '"'
        print(f"   {field:<18} <- {shown}")

    if mapping["Mobile"] is None:
        print("\nSTOP: no phone column found - cannot build the mirror.")
        print("Tell me your CSV's phone column header and I'll add it.")
        sys.exit(1)

    seen = {}
    bad_phone = 0
    for r in data:
        def cell(field):
            i = mapping[field]
            if i is None or i >= len(r):
                return ""
            return str(r[i]).strip()

        phone = normalize_phone(cell("Mobile"))
        if not phone:
            bad_phone += 1
            continue

        seen[phone] = [
            phone,
            cell("Patient Name"),
            cell("Diagnosis"),
            cell("Age"),
            cell("Gender"),
            cell("Last Visit"),
            cell("Patient UID"),
            cell("Clinic_Specific_Id"),
        ]  # keep last occurrence per phone

    return list(seen.values()), bad_phone


def main():
    push = "--push" in sys.argv

    print("=" * 60)
    print("PATIENT MIRROR  -  " + ("LIVE PUSH" if push else "PREVIEW (no write)"))
    print("=" * 60)
    print("Local file : " + LOCAL_CSV)
    print("Sheet tab  : " + TAB_NAME)

    rows, bad_phone = load_rows()

    print(f"\nValid patients to mirror : {len(rows)}")
    print(f"Rows skipped (bad phone) : {bad_phone}")

    if not rows:
        print("\nSTOP: zero valid rows. Refusing to push (mirror left untouched).")
        sys.exit(1)

    print("\nSample of what will be written (phone masked):")
    print("   " + " | ".join(OUT_HEADERS))
    for row in rows[:3]:
        shown = [mask_phone(row[0])] + row[1:]
        print("   " + " | ".join(str(x) for x in shown))

    if not push:
        print("\nThis was a PREVIEW - nothing was written to the sheet.")
        print("If the columns above look right, run again with:  --push")
        return

    # ----------------------------- live push ---------------------------------
    try:
        import gspread
    except ImportError:
        print("\nSTOP: the 'gspread' library isn't installed.")
        print("Run this once:  pip install --upgrade gspread")
        sys.exit(1)

    keys = []
    for path in glob.glob(os.path.join(KEY_DIR, "*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            if obj.get("type") == "service_account" and obj.get("client_email"):
                keys.append(path)
        except Exception:
            pass

    if len(keys) == 0:
        print("\nSTOP: no service-account .json key found in:")
        print("   " + KEY_DIR)
        sys.exit(1)
    if len(keys) > 1:
        print("\nSTOP: more than one service-account .json found:")
        for k in keys:
            print("   " + k)
        print("Keep only the correct one in this folder, then rerun.")
        sys.exit(1)

    key_path = keys[0]
    print("\nUsing key file: " + os.path.basename(key_path))

    gc = gspread.service_account(filename=key_path)
    sh = gc.open_by_key(SHEET_ID)

    try:
        ws = sh.worksheet(TAB_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=TAB_NAME, rows=len(rows) + 10, cols=len(OUT_HEADERS))
        print(f"Created new tab: {TAB_NAME}")

    values = [OUT_HEADERS] + rows
    ws.resize(rows=len(values), cols=len(OUT_HEADERS))   # remove any stale rows
    ws.update(values=values, range_name="A1", value_input_option="RAW")

    print(f"\nDONE. Wrote {len(rows)} patients to '{TAB_NAME}'. (Replace-only.)")
    print("The dashboard will show fresh patient details on its next refresh.")


if __name__ == "__main__":
    main()
