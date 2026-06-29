#!/usr/bin/env python3
"""
backfill_revenue.py  —  ONE-TIME rebuild of the revenue ledger.

WHY
  The daily flow stamps every row in a file with ONE date, so a wide (date-range)
  Docterz consultation report cannot be fed through it. This script reads a wide
  report and writes each Consultation / X-ray / Procedure row on its OWN
  Consultation Date — so it both BACKFILLS missing history (e.g. 1 Apr onward) and
  CORRECTS the old +1 filename mis-dating in one clean pass.

WHAT IT TOUCHES
  Only data/revenue_ledger.csv. It backs up all of data/ first, PRESERVES any
  manual rows (Lab entries, manual ₹0 procedures — anything not "Docterz (auto)"),
  and rebuilds the auto portion from the report. The three follow-up ledgers
  (master / visits / follow-ups) are NOT touched.

X-RAY RULE
  X-ray = Laboratory + Radiology (both amount and discount columns) — the clinic's
  only imaging is the Fuji DR X-ray, billed under either column.

USAGE
  python backfill_revenue.py  "C:\\path\\to\\consultation_report_full.csv"
  (or drag the CSV onto RUN_BACKFILL.bat)
"""
import sys
import uuid
import pandas as pd
from pathlib import Path
from datetime import date

import processor
import revenue
from processor import parse_date, date_to_str, backup_data
from revenue import (_num, split_payment, clean_mobile, load_revenue, save_revenue,
                     REVENUE_COLS, REVENUE_FILE)


def _strip(raw: pd.DataFrame) -> pd.DataFrame:
    """Drop the clinic-name header row and the trailing Total row."""
    if len(raw):
        first = str(raw.iloc[0].get("Sr No", "")).strip().lower()
        if "manoj agarwal clinic" in first or first in ("", "nan"):
            raw = raw.iloc[1:].reset_index(drop=True)
    raw = raw[~(
        (raw.get("Patient Name", "").astype(str).str.strip().str.lower() == "total")
        | (raw.get("Patient UID", "").astype(str).str.strip().isin(["", "nan"]))
    )].reset_index(drop=True)
    return raw


def rebuild(report_path: str) -> None:
    rp = Path(report_path)
    if not rp.exists():
        print(f"ERROR: file not found: {rp}")
        sys.exit(1)

    print(f"Rebuilding revenue ledger from: {rp.name}")
    backup_data("pre_backfill")                      # safety net first

    # ── split existing ledger: preserve manual, discard old auto ──────────────
    led = load_revenue()
    before_total = len(led)
    if before_total:
        manual = led[led["Entered_By"].astype(str).str.strip() != "Docterz (auto)"].copy()
    else:
        manual = led.iloc[0:0].copy()
    print(f"  existing ledger rows: {before_total}  (manual kept: {len(manual)}, "
          f"auto rebuilt: {before_total - len(manual)})")

    # ── read + clean the wide report ──────────────────────────────────────────
    raw = pd.read_csv(rp, dtype=str).fillna("")
    raw = _strip(raw)
    processed_on = date_to_str(date.today())
    origin = rp.name

    new_rows = []
    seen = set()          # (uid, date_str, source, invoice) within this rebuild
    paid_visit = set()    # (uid, date_str, invoice) — attach payment once per visit
    skipped_nodate = 0
    src_amt = {"Consultation": ("cons", "cons_d"),
               "X-ray": ("xray", "xray_d"),
               "Procedure": ("proc", "proc_d")}

    for _, r in raw.iterrows():
        d = parse_date(r.get("Consultation Date"))
        if not d:
            skipped_nodate += 1
            continue
        date_str = date_to_str(d)
        vals = {
            "cons": _num(r.get("Consultation Amount")), "cons_d": _num(r.get("Consultation Discount")),
            # X-ray = Laboratory + Radiology (both columns)
            "xray": _num(r.get("Laboratory Amount")) + _num(r.get("Radiology Amount")),
            "xray_d": _num(r.get("Laboratory Discount")) + _num(r.get("Radiology Discount")),
            "proc": _num(r.get("Procedure Amount")), "proc_d": _num(r.get("Procedure Discount")),
        }
        uid = str(r.get("Patient UID") or "").strip()
        clinic_id = (str(int(_num(r.get("Clinic Specific Id"))))
                     if _num(r.get("Clinic Specific Id")) else "")
        name = str(r.get("Patient Name") or "").strip()
        mobile = clean_mobile(r.get("Mobile"))
        invoice = str(r.get("Invoice No.") or "").strip()
        mode = str(r.get("Mode Of Payment") or "").strip()
        cash, online = split_payment(r.get("Amount collected"), mode)
        pend = _num(r.get("Bill Amount Pending"))
        shift = str(r.get("Schedule") or "").strip()
        purpose = str(r.get("Purpose Of Visit") or "").strip()
        visit_key = (uid, date_str, invoice)

        for source, (amt_k, disc_k) in src_amt.items():
            gross = vals[amt_k]; disc = vals[disc_k]
            net = gross - disc
            if source == "Procedure":
                if gross <= 0 and disc <= 0:
                    continue
            elif net <= 0:
                continue
            key = (uid, date_str, source, invoice)
            if key in seen:
                continue
            attach = visit_key not in paid_visit
            new_rows.append({
                "Revenue_ID": "R" + uuid.uuid4().hex[:10].upper(),
                "Date": date_str, "Patient_UID": uid, "Clinic_Specific_Id": clinic_id,
                "Patient_Name": name, "Mobile_Clean": mobile,
                "Source": source, "Gross": gross, "Discount": disc, "Net": net,
                "Mode_Of_Payment": mode,
                "Cash": cash if attach else "", "Online": online if attach else "",
                "Pending": pend if attach else "",
                "Shift": shift, "Purpose_Of_Visit": purpose, "Invoice_No": invoice,
                "Origin": origin, "Entered_By": "Docterz (auto)", "Processed_On": processed_on,
            })
            seen.add(key); paid_visit.add(visit_key)

    rebuilt = pd.DataFrame(new_rows, columns=REVENUE_COLS)
    final = pd.concat([manual[REVENUE_COLS], rebuilt], ignore_index=True) if len(manual) else rebuilt
    final[REVENUE_COLS].to_csv(REVENUE_FILE, index=False)

    # ── summary ───────────────────────────────────────────────────────────────
    def _f(x): return f"{float(x):,.0f}"
    by_src = rebuilt.groupby("Source")["Net"].sum().to_dict() if len(rebuilt) else {}
    dmin = rebuilt["Date"].min() if len(rebuilt) else "-"
    dmax = rebuilt["Date"].max() if len(rebuilt) else "-"
    print()
    print("  ── REBUILD SUMMARY ─────────────────────────────────────────")
    print(f"  report rows read (dated): {len(raw) - skipped_nodate}"
          + (f"   (skipped, no date: {skipped_nodate})" if skipped_nodate else ""))
    print(f"  auto revenue rows written: {len(rebuilt)}   manual rows preserved: {len(manual)}")
    print(f"  ledger rows: {before_total}  ->  {len(final)}")
    print(f"  date span now: {dmin}  ->  {dmax}")
    for s in ("Consultation", "X-ray", "Procedure", "Lab"):
        v = by_src.get(s, 0.0)
        if v:
            print(f"    {s:13} ₹{_f(v)}")
    print(f"    {'TOTAL net':13} ₹{_f(rebuilt['Net'].sum() if len(rebuilt) else 0)}")
    print("  ────────────────────────────────────────────────────────────")
    print("  Done. Open the Finance Dashboard to verify the period totals.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # fall back to a default filename in this folder
        default = Path(__file__).with_name("consultation_report_full.csv")
        if default.exists():
            rebuild(str(default))
        else:
            print("Usage: python backfill_revenue.py <path-to-wide-consultation-report.csv>")
            print("  (or place the file here named 'consultation_report_full.csv' and re-run,")
            print("   or drag the CSV onto RUN_BACKFILL.bat)")
            sys.exit(1)
    else:
        rebuild(sys.argv[1])
