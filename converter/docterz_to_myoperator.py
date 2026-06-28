#!/usr/bin/env python3
# =============================================================================
# docterz_to_myoperator.py  —  Dr Manoj Agarwal Clinic
# Turn a RAW Docterz EMR export into ready-to-upload MyOperator campaign CSVs.
#
# WHAT IT REPLACES
#   The "CSV_to_MyOperator_WABA_Campaign_Converter" Excel (paste-into-tabs).
#   This does the same job with ONE command and no copy-paste:
#     - Follow-up logs export      -> Export_Followup.csv   (appointment reminder)
#     - Day's consultation export  -> Export_PostVisit.csv  (app / report nudge)
#
# WHY
#   Frictionless daily run. Staff export the two CSVs from Docterz, drop them in
#   a folder, double-click run_converter (or run this script). Out come two clean
#   MyOperator-format CSVs + a rejects file listing any bad/missing mobiles.
#
# WHAT IT DOES TO THE DATA (matches the old Excel rules exactly)
#   - Mobile cleaning: strip everything non-digit, keep the LAST 10 digits,
#     prefix "91". Anything that is not a valid 10-digit Indian mobile
#     (first digit 6-9) is REJECTED (written to the rejects file, not the upload).
#   - Skips junk rows: the "Dr. Manoj Agarwal Clinic" banner row, the "Total"
#     footer row, and any row without a usable name + mobile.
#   - De-dupes within each campaign on the mobile (keeps the first occurrence).
#   - Links / template names / send times come ONLY from the CONFIG block below,
#     so updating a link is a one-line change here, never per-file.
#
# USAGE
#   python3 docterz_to_myoperator.py \
#       --followup "Followup Logs.csv" \
#       --seen     "Consultation Report.csv" \
#       --outdir   "out"
#   Either input may be omitted; only the matching export is produced.
#
# OUTPUT (in --outdir, default: same folder)
#   Export_Followup.csv     mobile,name,followup_date,appointment_link,
#                           clinic_contact,template_name,send_date,send_time,check
#   Export_PostVisit.csv    mobile,name,android_app_link,ios_app_link,
#                           clinic_contact,template_name,send_date,send_time,check
#   Rejected_Rows.csv       source,row_no,mobile_raw,patient_name,date,reason
#
# IMPORTANT (verify once before a real send)
#   * template_name values below are the names the converter writes into the CSV.
#     MyOperator's campaign screen picks the template itself, so these are only a
#     label/record. Make sure the name you USE in the panel campaign is one that
#     is actually APPROVED on your WABA. (Your approved API set is the drmanoj_*
#     family; the FU_Reminder_v2 / PV_Reports_v2 names came from the old template
#     doc — confirm which the panel campaign expects.)
#   * Keep Follow-up and Post-visit as SEPARATE campaigns. Do not merge.
# =============================================================================

import argparse
import csv
import os
import re
import sys

# --------------------------- CONFIG (edit here only) -------------------------
CONFIG = {
    "appointment_link": "https://book.dr-manoj.in",
    "android_app_link": "https://app.dr-manoj.in",
    "ios_app_link":     "https://ios.dr-manoj.in",
    "clinic_contact":   "9358008080",        # swap to IVR number if you want calls routed there
    "followup_template": "FU_Reminder_v2",   # VERIFY this matches an approved panel template
    "postvisit_template": "PV_Reports_v2",   # VERIFY this matches an approved panel template
    "followup_send_time": "10:00",           # suggested 9-11 AM
    "postvisit_send_time": "19:00",          # suggested 6-8 PM
}

COUNTRY = "91"


# ------------------------------- helpers ------------------------------------
def clean_mobile(raw):
    """Return '91'+<10 digits> if valid, else None. Rule: digits only, last 10,
    first of those 10 must be 6-9 (valid Indian mobile)."""
    digits = re.sub(r"\D", "", str(raw or ""))
    if len(digits) < 10:
        return None
    last10 = digits[-10:]
    if last10[0] not in "6789":
        return None
    return COUNTRY + last10


def date_only(s):
    """'15-05-2026 11:05' -> '15-05-2026'; passes plain dates through."""
    s = str(s or "").strip()
    return s.split(" ")[0] if s else ""


def open_csv(path):
    """Open a CSV tolerant of a UTF-8 BOM. Returns (header_list, list_of_rows)."""
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        rows = [r for r in reader]
    if not rows:
        return [], []
    return rows[0], rows[1:]


def col_index(header, *names):
    low = [h.strip().lower() for h in header]
    for n in names:
        if n.lower() in low:
            return low.index(n.lower())
    return -1


def get(row, idx):
    return row[idx].strip() if (0 <= idx < len(row) and row[idx] is not None) else ""


# ----------------------------- follow-up ------------------------------------
def build_followup(path, rejects):
    header, rows = open_csv(path)
    i_mob  = col_index(header, "Mobile No", "Mobile", "Mobile Number", "Phone")
    i_name = col_index(header, "Patient Name", "Name")
    i_date = col_index(header, "Followup Date", "Follow-up Date", "Followup")
    out, seen = [], set()
    for n, row in enumerate(rows, start=2):
        name = get(row, i_name)
        mob_raw = get(row, i_mob)
        fdate = date_only(get(row, i_date))
        if not name and not mob_raw:
            continue                                   # blank line
        if name.lower() in ("total", "dr. manoj agarwal clinic"):
            continue
        mob = clean_mobile(mob_raw)
        if not mob:
            rejects.append(["Followup", n, mob_raw, name, fdate, "bad/blank mobile"])
            continue
        if mob in seen:
            continue                                   # de-dupe
        seen.add(mob)
        out.append({
            "mobile": mob, "name": name, "followup_date": fdate,
            "appointment_link": CONFIG["appointment_link"],
            "clinic_contact": CONFIG["clinic_contact"],
            "template_name": CONFIG["followup_template"],
            "send_date": fdate, "send_time": CONFIG["followup_send_time"],
            "check": "OK",
        })
    return out


def write_followup(rows, outdir):
    path = os.path.join(outdir, "Export_Followup.csv")
    cols = ["mobile", "name", "followup_date", "appointment_link", "clinic_contact",
            "template_name", "send_date", "send_time", "check"]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path


# ----------------------------- post-visit -----------------------------------
def build_postvisit(path, rejects):
    header, rows = open_csv(path)
    i_mob  = col_index(header, "Mobile", "Mobile No", "Mobile Number", "Phone")
    i_name = col_index(header, "Patient Name", "Name")
    i_date = col_index(header, "Consultation Date", "Consult Date", "Date")
    out, seen = [], set()
    for n, row in enumerate(rows, start=2):
        name = get(row, i_name)
        mob_raw = get(row, i_mob)
        cdate = date_only(get(row, i_date))
        if not name and not mob_raw:
            continue
        if name.lower() in ("total", "dr. manoj agarwal clinic"):
            continue                                   # banner / footer
        mob = clean_mobile(mob_raw)
        if not mob:
            rejects.append(["PostVisit", n, mob_raw, name, cdate, "bad/blank mobile"])
            continue
        if mob in seen:
            continue
        seen.add(mob)
        out.append({
            "mobile": mob, "name": name,
            "android_app_link": CONFIG["android_app_link"],
            "ios_app_link": CONFIG["ios_app_link"],
            "clinic_contact": CONFIG["clinic_contact"],
            "template_name": CONFIG["postvisit_template"],
            "send_date": cdate, "send_time": CONFIG["postvisit_send_time"],
            "check": "OK",
        })
    return out


def write_postvisit(rows, outdir):
    path = os.path.join(outdir, "Export_PostVisit.csv")
    cols = ["mobile", "name", "android_app_link", "ios_app_link", "clinic_contact",
            "template_name", "send_date", "send_time", "check"]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path


def write_rejects(rejects, outdir):
    path = os.path.join(outdir, "Rejected_Rows.csv")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["source", "row_no", "mobile_raw", "patient_name", "date", "reason"])
        w.writerows(rejects)
    return path


# --------------------------------- main -------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Docterz EMR CSV -> MyOperator campaign CSVs")
    ap.add_argument("--followup", help="path to the Docterz follow-up logs CSV")
    ap.add_argument("--seen", help="path to the Docterz consultation report CSV")
    ap.add_argument("--outdir", default=".", help="output folder (default: current)")
    args = ap.parse_args()

    if not args.followup and not args.seen:
        ap.error("give --followup and/or --seen")
    os.makedirs(args.outdir, exist_ok=True)
    rejects = []

    if args.followup:
        fu = build_followup(args.followup, rejects)
        p = write_followup(fu, args.outdir)
        print("Follow-up reminder : %3d contacts -> %s" % (len(fu), p))
    if args.seen:
        pv = build_postvisit(args.seen, rejects)
        p = write_postvisit(pv, args.outdir)
        print("Post-visit nudge   : %3d contacts -> %s" % (len(pv), p))

    rp = write_rejects(rejects, args.outdir)
    print("Rejected rows      : %3d           -> %s" % (len(rejects), rp))
    if rejects:
        print("  (fix the mobile/name in Docterz and re-export, or ignore if expected)")


if __name__ == "__main__":
    main()
