"""
revenue.py — Per-patient revenue ledger + financial views.
Dr. Manoj Agarwal Clinic, Bareilly

WHAT THIS DOES
  1. Auto-extracts VISIT revenue (Consultation / X-ray / Procedure) from each
     Docterz consultation report that the follow-up tracker already ingests
     every night — ZERO new data entry (Phase 1 of the revenue-ledger plan).
  2. Accepts MANUAL lab revenue (NK Pathology, billed outside Docterz) via the
     web form: staff type a Docterz Clinic ID or mobile, the name auto-fills
     from the Patient Master, they enter amount + discount, net is computed.
  3. Stores everything in ONE long-format ledger keyed by Patient_UID, which
     yields, with trivial group-bys:
        • visit revenue (one row per visit per source)
        • patient LIFETIME value (sum of net over a UID)
        • day / month / year income totals

CLINIC-SPECIFIC RULE — X-RAY = "LABORATORY AMOUNT" + "RADIOLOGY AMOUNT"
  At this clinic the only imaging is the in-house Fuji DR X-ray. It is billed
  mostly under Docterz's "Laboratory Amount" column, but staff sometimes key it
  into "Radiology Amount" instead (confirmed 19 Jun 2026 over the Apr–Jun data).
  So X-ray revenue = Laboratory + Radiology (both amount AND discount columns).
  NK Pathology (the separate pathology lab) is NOT in Docterz at all — it comes
  in only through the manual lab-entry form, stored with Source = "Lab".

LEDGER IS LONG FORMAT (one row per visit per source). Re-uploading the same
consultation report is safe: rows are de-duplicated on
(Patient_UID, Date, Source, Invoice_No).
"""

from __future__ import annotations

import re
import uuid
import pandas as pd
from pathlib import Path
from datetime import datetime, date, timedelta

# Reuse the tracker's own date/mobile helpers so behaviour is identical.
from processor import (
    DATA_DIR, parse_date, date_to_str, clean_mobile, load_master, load_visits,
)

REVENUE_FILE = DATA_DIR / "revenue_ledger.csv"
# Manual marker for ₹0 / free procedures (e.g. Ayushman cashless) that carry NO
# amount in the Docterz export and therefore cannot be auto-detected. The doctor
# marks these on the web app; they are applied to the visit ledger (so they show
# in staff call-backs) and written to the revenue ledger at ₹0 (so they show in
# the day sheet and patient history).
MANUAL_PROC_FILE = DATA_DIR / "manual_procedures.csv"
MANUAL_PROC_COLS = ["Date", "Patient_UID", "Clinic_Specific_Id", "Patient_Name",
                    "Mobile_Clean", "Note", "Entered_By", "Processed_On"]

# Docterz consultation-report column names that carry money.
# X-ray is read from "Laboratory Amount" per the clinic rule above.
SOURCE_COLS = {
    "Consultation": ("Consultation Amount", "Consultation Discount"),
    "X-ray":        ("Laboratory Amount",  "Laboratory Discount"),
    "Procedure":    ("Procedure Amount",   "Procedure Discount"),
}

DEFAULT_CONSULT_FEE = 600   # standard consultation fee; used only to flag ▲/▼ on the day sheet

# Free-revisit window: a ₹0 consultation counts as a Free Revisit (expected, not a
# concession) when the SAME patient had a PAID consultation within this many days
# before it, counted from the patient's most recent paid consultation. Beyond the
# window a fee is payable, so a ₹0 visit there is a genuine concession.
FREE_REVISIT_WINDOW_DAYS = 5

# Standing concession log — accumulates every ₹0 "Free / Concession Case" visit
# (genuinely complimentary, NOT a free revisit) so concession patients become a
# queryable standing list keyed by Patient_UID. Append-only, de-duped on (UID, Date).
# A new file in data/; existing ledgers are never touched.
CONCESSION_FILE = DATA_DIR / "concession_log.csv"
CONCESSION_COLS = ["Date", "Patient_UID", "Clinic_Specific_Id", "Patient_Name",
                   "Mobile_Clean", "Consultation", "Consultation_Disc",
                   "Xray_Disc", "Procedure_Disc", "Case_Type",
                   "Source_File", "Processed_On"]

REVENUE_COLS = [
    "Revenue_ID", "Date", "Patient_UID", "Clinic_Specific_Id", "Patient_Name",
    "Mobile_Clean", "Source", "Gross", "Discount", "Net",
    "Mode_Of_Payment", "Cash", "Online", "Pending",
    "Shift", "Purpose_Of_Visit", "Invoice_No",
    "Origin", "Entered_By", "Processed_On",
]


# ── tiny numeric helper ───────────────────────────────────────────────────────
def _num(x) -> float:
    """Parse a money cell to float. Handles '1,100', ' 500 ', '#VALUE!', None, ''."""
    if x is None:
        return 0.0
    s = str(x).replace(",", "").strip()
    if s in ("", "nan", "None", "#VALUE!", "-"):
        return 0.0
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


# ── cash / online split parser ────────────────────────────────────────────────
# Docterz records the split inside the "Amount collected" cell, e.g.
#   "900 (Cash: 600, Online Payment: 300)"
#   "1100 (Online Payment: 1100)"
#   "500"            <- no bracket; assign by Mode Of Payment
def split_payment(amount_collected, mode_of_payment) -> tuple[float, float]:
    """Return (cash, online) for a visit's collected amount."""
    raw = "" if amount_collected is None else str(amount_collected)
    cash = online = 0.0
    m_cash = re.search(r"cash\s*:\s*([\d,]+(?:\.\d+)?)", raw, re.I)
    m_onln = re.search(r"online[^:]*:\s*([\d,]+(?:\.\d+)?)", raw, re.I)
    if m_cash or m_onln:
        cash   = _num(m_cash.group(1)) if m_cash else 0.0
        online = _num(m_onln.group(1)) if m_onln else 0.0
        return cash, online
    # No bracketed breakdown: take the leading number and assign by mode.
    lead = re.match(r"\s*([\d,]+(?:\.\d+)?)", raw)
    total = _num(lead.group(1)) if lead else 0.0
    mode = str(mode_of_payment or "").strip().lower()
    if "online" in mode or "upi" in mode or "card" in mode:
        return 0.0, total
    if "cash" in mode:
        return total, 0.0
    # Unknown/blank mode (usually a ₹0 free visit) — nothing collected.
    return 0.0, 0.0


# ── ledger load/save ──────────────────────────────────────────────────────────
def load_revenue() -> pd.DataFrame:
    if REVENUE_FILE.exists():
        df = pd.read_csv(REVENUE_FILE, dtype=str).fillna("")
        for c in REVENUE_COLS:
            if c not in df.columns:
                df[c] = ""
        return df[REVENUE_COLS]
    return pd.DataFrame(columns=REVENUE_COLS)


def save_revenue(df: pd.DataFrame):
    df[REVENUE_COLS].to_csv(REVENUE_FILE, index=False)


# ── 5-day-rule helpers ────────────────────────────────────────────────────────
def _paid_consult_dates_by_uid() -> dict:
    """UID -> list of dates on which that patient had a PAID consultation, read
    from the revenue ledger. ₹0 consultations are never written to the ledger, so
    every Source=="Consultation" row is a paid consult."""
    led = load_revenue()
    out: dict = {}
    if len(led):
        cons = led[led["Source"] == "Consultation"]
        for uid, dstr in zip(cons["Patient_UID"].astype(str).str.strip(), cons["Date"]):
            d = parse_date(dstr)
            if uid and d:
                out.setdefault(uid, []).append(d)
    return out


def _is_free_revisit(uid: str, visit_date, paid_by_uid: dict) -> bool:
    """True if the patient had a paid consultation 0..FREE_REVISIT_WINDOW_DAYS days
    before this ₹0 visit (i.e. the free-revisit window is still open)."""
    if not visit_date:
        return False
    for p in paid_by_uid.get(uid, ()):  # noqa: SIM110
        delta = (visit_date - p).days
        if 0 <= delta <= FREE_REVISIT_WINDOW_DAYS:
            return True
    return False


# ── parse a consultation report into per-visit revenue (rich, for the day tab) ─
def parse_day_revenue(filepath: str) -> tuple[pd.DataFrame, str]:
    """
    Read a Docterz consultation report and return (per_visit_df, report_date).

    per_visit_df has one row per patient-visit with these columns:
        Patient_UID, Clinic_Specific_Id, Patient_Name, Mobile_Clean, Date,
        Consultation, Consultation_Disc, Xray, Xray_Disc, Procedure, Procedure_Disc,
        Bill, Collected, Pending, Cash, Online, Mode, Shift, Purpose, Invoice_No,
        Case_Type   (Paid Consultation | Free Revisit | Free / Concession Case)

    Strips the clinic-name header row (row 0) and the trailing "Total" row.
    """
    try:
        raw = pd.read_csv(filepath, dtype=str)
    except pd.errors.EmptyDataError:
        raw = pd.DataFrame()

    # Report date from the report's CONTENT (latest real visit date), not the
    # filename. Docterz names the export by the download day - one day ahead of the
    # visits - which otherwise breaks manual a0-procedure date-matching. Filename is
    # only a fallback when no visit dates are present.
    if "Consultation Date" in raw.columns:
        _rv = [parse_date(x) for x in raw["Consultation Date"]]
        _rv = [d for d in _rv if d]
    else:
        _rv = []
    if _rv:
        report_date = date_to_str(max(_rv))
    else:
        fname = Path(filepath).stem
        m = re.search(r"(\d{4}-\d{2}-\d{2})", fname)
        report_date = m.group(1) if m else ""

    cols = ["Patient_UID", "Clinic_Specific_Id", "Patient_Name", "Mobile_Clean", "Date",
            "Consultation", "Consultation_Disc", "Xray", "Xray_Disc",
            "Procedure", "Procedure_Disc", "Bill", "Collected", "Pending",
            "Cash", "Online", "Mode", "Shift", "Purpose", "Invoice_No", "Case_Type"]
    if len(raw) == 0:
        return pd.DataFrame(columns=cols), report_date or date_to_str(date.today())

    # Drop clinic-name header (row 0 has the clinic name in 'Sr No').
    first_sr = str(raw.iloc[0].get("Sr No", "")).strip().lower()
    if first_sr in ("dr. manoj agarwal clinic", "dr manoj agarwal clinic", "", "nan"):
        raw = raw.iloc[1:].reset_index(drop=True)

    # Drop trailing "Total" summary row (Patient Name == 'Total', no UID).
    raw = raw[~(
        (raw.get("Patient Name", "").astype(str).str.strip().str.lower() == "total")
        | (raw.get("Patient UID", "").astype(str).str.strip().isin(["", "nan"]))
    )].reset_index(drop=True)

    if report_date == "" and len(raw):
        report_date = date_to_str(parse_date(raw["Consultation Date"].iloc[0])) or date_to_str(date.today())

    # Build the paid-consultation lookup ONCE (prior days, from the revenue ledger);
    # paid consults found in THIS report are merged in after the loop.
    paid_by_uid = _paid_consult_dates_by_uid()
    rd_parsed = parse_date(report_date)
    today_paid: dict = {}

    out_rows = []
    for _, r in raw.iterrows():
        cons   = _num(r.get("Consultation Amount"));  cons_d = _num(r.get("Consultation Discount"))
        # X-ray = Laboratory + Radiology (the clinic's only imaging is the Fuji DR
        # X-ray; staff bill it under either column — both are summed).
        xray   = _num(r.get("Laboratory Amount")) + _num(r.get("Radiology Amount"))
        xray_d = _num(r.get("Laboratory Discount")) + _num(r.get("Radiology Discount"))
        proc   = _num(r.get("Procedure Amount"));     proc_d = _num(r.get("Procedure Discount"))
        bill   = _num(r.get("Bill Amount"))
        coll_raw = r.get("Amount collected")
        pend   = _num(r.get("Bill Amount Pending"))
        mode   = str(r.get("Mode Of Payment") or "").strip()
        cash, online = split_payment(coll_raw, mode)
        purpose = str(r.get("Purpose Of Visit") or "").strip()

        # Case classification — 5-day-from-PAID-consultation rule (replaces the old,
        # unreliable Purpose-field test). ₹0 rows are decided AFTER the loop, once the
        # full paid history (ledger + this report) is known.
        #   Consultation > 0                  → Paid Consultation
        #   ₹0 & paid consult within 5 days   → Free Revisit (window open; expected)
        #   ₹0 & no paid consult within 5 days→ Free / Concession Case (complimentary)
        uid = str(r.get("Patient UID") or "").strip()
        if cons > 0:
            case_type = "Paid Consultation"
            if rd_parsed:
                today_paid.setdefault(uid, []).append(rd_parsed)
        else:
            case_type = ""   # decided after the loop

        out_rows.append({
            "Patient_UID":        str(r.get("Patient UID") or "").strip(),
            "Clinic_Specific_Id": (str(int(_num(r.get("Clinic Specific Id"))))
                                   if _num(r.get("Clinic Specific Id")) else ""),
            "Patient_Name":       str(r.get("Patient Name") or "").strip(),
            "Mobile_Clean":       clean_mobile(r.get("Mobile")),
            "Date":               report_date,
            "Consultation":       cons,  "Consultation_Disc": cons_d,
            "Xray":               xray,  "Xray_Disc":         xray_d,
            "Procedure":          proc,  "Procedure_Disc":    proc_d,
            "Bill":               bill,  "Collected": cash + online, "Pending": pend,
            "Cash":               cash,  "Online":    online,
            "Mode":               mode,
            "Shift":              str(r.get("Schedule") or "").strip(),
            "Purpose":            purpose,
            "Invoice_No":         str(r.get("Invoice No.") or "").strip(),
            "Case_Type":          case_type,
        })
    # Decide the ₹0 rows now that the full paid history is known (prior ledger paid
    # consults + any paid consult in THIS report).
    for _uid, _dts in today_paid.items():
        paid_by_uid.setdefault(_uid, []).extend(_dts)
    for _row in out_rows:
        if _row["Case_Type"] == "":
            _row["Case_Type"] = ("Free Revisit"
                                 if _is_free_revisit(_row["Patient_UID"], rd_parsed, paid_by_uid)
                                 else "Free / Concession Case")
    return pd.DataFrame(out_rows, columns=cols), report_date


# ── fold the day's revenue into the persistent long-format ledger ─────────────
def update_revenue_ledger_from_day(day_df: pd.DataFrame, report_date: str,
                                    origin_file: str, processed_on: str) -> int:
    """Append Consultation / X-ray / Procedure rows (net > 0 only) to the
    revenue ledger, de-duplicated on (UID, Date, Source, Invoice_No).
    Returns number of rows added."""
    ledger = load_revenue()
    existing = set(zip(ledger["Patient_UID"], ledger["Date"],
                       ledger["Source"], ledger["Invoice_No"]))
    src_amt = {"Consultation": ("Consultation", "Consultation_Disc"),
               "X-ray": ("Xray", "Xray_Disc"),
               "Procedure": ("Procedure", "Procedure_Disc")}
    new_rows = []
    # Cash/Online/Pending are VISIT-level (one payment per visit). To avoid
    # triple-counting across a visit's source rows we record them on exactly ONE
    # row per visit — the first source row written for that visit. (Consultation
    # is iterated first, but a free-consultation visit that only paid for X-ray
    # still gets its payment recorded, on the X-ray row.)
    paid_visit = set()
    for _, r in day_df.iterrows():
        visit_key = (r["Patient_UID"], r["Date"], r["Invoice_No"])
        for source, (amt_c, disc_c) in src_amt.items():
            gross = float(r[amt_c]); disc = float(r[disc_c])
            net = gross - disc
            # Procedures are kept even when net is ₹0 (e.g. Ayushman cashless,
            # billed then fully discounted) as long as SOMETHING was recorded
            # (gross or discount). Consultation / X-ray are kept only when net>0.
            if source == "Procedure":
                if gross <= 0 and disc <= 0:
                    continue
            elif net <= 0:
                continue
            key = (r["Patient_UID"], r["Date"], source, r["Invoice_No"])
            if key in existing:
                continue
            attach_payment = visit_key not in paid_visit
            new_rows.append({
                "Revenue_ID": "R" + uuid.uuid4().hex[:10].upper(),
                "Date": r["Date"], "Patient_UID": r["Patient_UID"],
                "Clinic_Specific_Id": r["Clinic_Specific_Id"],
                "Patient_Name": r["Patient_Name"], "Mobile_Clean": r["Mobile_Clean"],
                "Source": source, "Gross": gross, "Discount": disc, "Net": net,
                "Mode_Of_Payment": r["Mode"],
                "Cash":    r["Cash"]    if attach_payment else "",
                "Online":  r["Online"]  if attach_payment else "",
                "Pending": r["Pending"] if attach_payment else "",
                "Shift": r["Shift"], "Purpose_Of_Visit": r["Purpose"],
                "Invoice_No": r["Invoice_No"],
                "Origin": origin_file, "Entered_By": "Docterz (auto)",
                "Processed_On": processed_on,
            })
            existing.add(key)
            paid_visit.add(visit_key)
    if new_rows:
        ledger = pd.concat([ledger, pd.DataFrame(new_rows)], ignore_index=True)
        save_revenue(ledger)
    return len(new_rows)


# ── standing concession log ───────────────────────────────────────────────────
def load_concession_log() -> pd.DataFrame:
    if CONCESSION_FILE.exists():
        df = pd.read_csv(CONCESSION_FILE, dtype=str).fillna("")
        for c in CONCESSION_COLS:
            if c not in df.columns:
                df[c] = ""
        return df[CONCESSION_COLS]
    return pd.DataFrame(columns=CONCESSION_COLS)


def append_concession_log(day_df: pd.DataFrame, source_file: str,
                          processed_on: str) -> int:
    """Append this report's Free / Concession Case visits to the standing concession
    log, de-duplicated on (Patient_UID, Date). Returns the number of rows added.
    Safe to re-run the same report (idempotent)."""
    if day_df is None or not len(day_df) or "Case_Type" not in day_df.columns:
        return 0
    conc = day_df[day_df["Case_Type"] == "Free / Concession Case"]
    if not len(conc):
        return 0
    log = load_concession_log()
    existing = set(zip(log["Patient_UID"].astype(str), log["Date"].astype(str)))
    new_rows = []
    for _, r in conc.iterrows():
        key = (str(r["Patient_UID"]), str(r["Date"]))
        if key in existing:
            continue
        new_rows.append({
            "Date": r["Date"], "Patient_UID": r["Patient_UID"],
            "Clinic_Specific_Id": r["Clinic_Specific_Id"],
            "Patient_Name": r["Patient_Name"], "Mobile_Clean": r["Mobile_Clean"],
            "Consultation": r["Consultation"], "Consultation_Disc": r["Consultation_Disc"],
            "Xray_Disc": r["Xray_Disc"], "Procedure_Disc": r["Procedure_Disc"],
            "Case_Type": r["Case_Type"],
            "Source_File": source_file, "Processed_On": processed_on,
        })
        existing.add(key)
    if new_rows:
        log = pd.concat([log, pd.DataFrame(new_rows)], ignore_index=True)
        log[CONCESSION_COLS].to_csv(CONCESSION_FILE, index=False)
    return len(new_rows)


# ── manual ₹0 / free procedure marker ─────────────────────────────────────────
def load_manual_procedures() -> pd.DataFrame:
    if MANUAL_PROC_FILE.exists():
        df = pd.read_csv(MANUAL_PROC_FILE, dtype=str).fillna("")
        for c in MANUAL_PROC_COLS:
            if c not in df.columns:
                df[c] = ""
        return df[MANUAL_PROC_COLS]
    return pd.DataFrame(columns=MANUAL_PROC_COLS)


def manual_proc_for_date(date_str: str) -> pd.DataFrame:
    """Manual ₹0 procedures recorded for a given date (YYYY-MM-DD)."""
    df = load_manual_procedures()
    if df.empty:
        return df
    return df[df["Date"].astype(str).str.strip() == str(date_str).strip()]


def add_manual_procedure(patient_uid: str, clinic_id: str, name: str, mobile: str,
                         proc_date: str | None = None, entered_by: str = "Staff",
                         note: str = "") -> dict:
    """Mark a ₹0 / free procedure for a patient on a date (default today).
    Writes a manual_procedures row AND a ₹0 Procedure row to the revenue ledger
    (so it shows in history and the day sheet). The visit-ledger Had_Procedure
    flag is applied at the next run by processor (so it shows in staff call-backs).
    De-duplicated on (UID, date) so a double tap won't create two."""
    d = proc_date or date_to_str(date.today())
    uid = str(patient_uid).strip()

    # manual_procedures.csv (dedup on UID+date)
    mdf = load_manual_procedures()
    dup = ((mdf["Patient_UID"].astype(str).str.strip() == uid)
           & (mdf["Date"].astype(str).str.strip() == d)).any() if len(mdf) else False
    if not dup:
        mrow = {
            "Date": d, "Patient_UID": uid, "Clinic_Specific_Id": str(clinic_id).strip(),
            "Patient_Name": str(name).strip(), "Mobile_Clean": clean_mobile(mobile) or str(mobile).strip(),
            "Note": note, "Entered_By": entered_by,
            "Processed_On": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        mdf = pd.concat([mdf, pd.DataFrame([mrow])], ignore_index=True)
        mdf[MANUAL_PROC_COLS].to_csv(MANUAL_PROC_FILE, index=False)

    # ₹0 Procedure row in the revenue ledger (dedup on UID+date+Procedure+MANUAL)
    ledger = load_revenue()
    key_exists = (len(ledger) and ((ledger["Patient_UID"].astype(str).str.strip() == uid)
                  & (ledger["Date"].astype(str).str.strip() == d)
                  & (ledger["Source"] == "Procedure")
                  & (ledger["Invoice_No"].astype(str) == "MANUAL")).any())
    if not key_exists:
        row = {
            "Revenue_ID": "P" + uuid.uuid4().hex[:10].upper(),
            "Date": d, "Patient_UID": uid, "Clinic_Specific_Id": str(clinic_id).strip(),
            "Patient_Name": str(name).strip(),
            "Mobile_Clean": clean_mobile(mobile) or str(mobile).strip(),
            "Source": "Procedure", "Gross": 0.0, "Discount": 0.0, "Net": 0.0,
            "Mode_Of_Payment": "", "Cash": "", "Online": "", "Pending": "",
            "Shift": "", "Purpose_Of_Visit": "Procedure (free/₹0)",
            "Invoice_No": "MANUAL",
            "Origin": ("note:" + note) if note else "Manual ₹0 procedure",
            "Entered_By": entered_by,
            "Processed_On": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        ledger = pd.concat([ledger, pd.DataFrame([row])], ignore_index=True)
        save_revenue(ledger)
    return {"date": d, "uid": uid, "name": name}


# ── manual lab (NK Pathology) entry ───────────────────────────────────────────
def lookup_patient(query: str) -> dict | None:
    """Resolve a Docterz Clinic ID OR mobile (OR a full UID) to a patient for the
    lab / procedure forms. Returns {uid, clinic_id, name, mobile} or None.

    To avoid false matches, digit-based matching (Clinic ID / mobile) fires ONLY
    when the query is purely numeric (after stripping spaces/hyphens/+). A query
    containing letters is treated as a Patient UID. Clinic ID is tried before
    mobile because staff usually have it on the slip."""
    q = str(query or "").strip()
    if not q:
        return None
    master = load_master()
    if master.empty:
        return None

    # Is the query purely numeric (allowing spaces, hyphens, leading +)?
    compact = re.sub(r"[\s\-+]", "", q)
    is_numeric = compact.isdigit()

    if is_numeric:
        # Clinic Specific Id (short numeric, on the slip)
        if len(compact) <= 7:
            hit = master[master["Clinic_Specific_Id"].astype(str).str.strip() == compact]
            if len(hit):
                row = hit.iloc[0]
                return {"uid": row["Patient_UID"], "clinic_id": row["Clinic_Specific_Id"],
                        "name": row["Patient_Name"], "mobile": row["Mobile_Clean"]}
        # Mobile (10 digits / with country code)
        mob = clean_mobile(q)
        if mob:
            hit = master[master["Mobile_Clean"] == mob]
            if len(hit) == 1:
                row = hit.iloc[0]
                return {"uid": row["Patient_UID"], "clinic_id": row["Clinic_Specific_Id"],
                        "name": row["Patient_Name"], "mobile": row["Mobile_Clean"]}
            if len(hit) > 1:                   # shared family mobile — need name/clinic id
                names = ", ".join(hit["Patient_Name"].head(4).tolist())
                return {"uid": "", "clinic_id": "", "name": "", "mobile": mob,
                        "ambiguous": f"{len(hit)} patients share this mobile ({names}). "
                                     f"Use the Docterz Clinic ID instead."}
        return None

    # Non-numeric → treat as a Patient UID (e.g. PCDRP14418)
    hit = master[master["Patient_UID"].astype(str).str.strip().str.upper() == q.upper()]
    if len(hit):
        row = hit.iloc[0]
        return {"uid": row["Patient_UID"], "clinic_id": row["Clinic_Specific_Id"],
                "name": row["Patient_Name"], "mobile": row["Mobile_Clean"]}
    return None


def add_lab_revenue(patient_uid: str, clinic_id: str, name: str, mobile: str,
                    amount, discount, entry_date: str | None = None,
                    entered_by: str = "Staff", note: str = "") -> dict:
    """Append one NK Pathology lab-revenue row. Net = amount − discount.
    Date defaults to today (the entry date)."""
    gross = _num(amount); disc = _num(discount)
    net = gross - disc
    d = entry_date or date_to_str(date.today())
    row = {
        "Revenue_ID": "L" + uuid.uuid4().hex[:10].upper(),
        "Date": d, "Patient_UID": str(patient_uid).strip(),
        "Clinic_Specific_Id": str(clinic_id).strip(), "Patient_Name": str(name).strip(),
        "Mobile_Clean": clean_mobile(mobile) or str(mobile).strip(),
        "Source": "Lab", "Gross": gross, "Discount": disc, "Net": net,
        "Mode_Of_Payment": "", "Cash": "", "Online": "", "Pending": "",
        "Shift": "", "Purpose_Of_Visit": "Pathology", "Invoice_No": "",
        "Origin": ("note:" + note) if note else "Manual lab entry",
        "Entered_By": entered_by,
        "Processed_On": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    ledger = load_revenue()
    ledger = pd.concat([ledger, pd.DataFrame([row])], ignore_index=True)
    save_revenue(ledger)
    return row


# ── financial roll-ups ────────────────────────────────────────────────────────
def _ledger_numeric() -> pd.DataFrame:
    df = load_revenue()
    if df.empty:
        return df
    for c in ("Net", "Gross", "Discount", "Cash", "Online", "Pending"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    df["_d"] = df["Date"].map(parse_date)
    return df


def patient_full_history(query: str) -> dict | None:
    """Complete per-patient view: EVERY visit (from the visit ledger, so free
    ₹0 visits appear too) joined with that day's revenue broken down by source
    (Consultation / X-ray / Procedure / Lab). Also surfaces lab-only days that
    have no Docterz visit. Keyed by Patient_UID.

    Returns:
      {uid, clinic_id, name, mobile, first_date, last_date,
       visit_count, lifetime_net, by_source{...},
       rows: [ {Date, Consultation, Xray, Procedure, Lab, Total, Mode, Shift,
                Pending, Had_Revenue} ... sorted by date ] }
    or None if the patient cannot be resolved in either ledger.
    """
    # ── resolve the patient to a UID using whichever ledger knows them ───────
    rev = _ledger_numeric()
    vis = load_visits()
    q = str(query or "").strip()
    digits = re.sub(r"\D", "", q)
    mob = clean_mobile(q)

    def _match(df, uid_col="Patient_UID", cid_col="Clinic_Specific_Id", mob_col="Mobile_Clean"):
        if df is None or df.empty:
            return df.iloc[0:0] if df is not None else None
        m = df[df[uid_col].astype(str).str.strip() == q]
        if m.empty and digits:
            m = df[df[cid_col].astype(str).str.strip() == digits]
        if m.empty and mob:
            m = df[df[mob_col].astype(str).str.strip() == mob]
        return m

    rsub = _match(rev) if not rev.empty else rev
    vsub = _match(vis) if vis is not None and not vis.empty else (vis.iloc[0:0] if vis is not None else None)

    has_rev = rsub is not None and not rsub.empty
    has_vis = vsub is not None and not vsub.empty
    if not has_rev and not has_vis:
        return None

    # identity / name (prefer revenue ledger, else visit ledger)
    if has_rev:
        uid = rsub["Patient_UID"].iloc[0]; clinic_id = rsub["Clinic_Specific_Id"].iloc[0]
        name = rsub["Patient_Name"].dropna().iloc[-1]
        mobile = rsub["Mobile_Clean"].iloc[0]
    else:
        uid = vsub["Patient_UID"].iloc[0]; clinic_id = vsub["Clinic_Specific_Id"].iloc[0]
        name = vsub["Patient_Name"].dropna().iloc[-1]
        mobile = vsub["Mobile_Clean"].iloc[0]
    # If we matched revenue by UID, also pull the patient's visits by that UID
    if has_vis is False and uid:
        vsub = vis[vis["Patient_UID"].astype(str).str.strip() == str(uid).strip()] if vis is not None else None
        has_vis = vsub is not None and not vsub.empty
    if has_rev and uid:
        rsub = rev[rev["Patient_UID"].astype(str).str.strip() == str(uid).strip()]

    # ── build a per-date row, unioning visit dates and revenue dates ─────────
    dates = set()
    if has_vis:
        dates |= {str(d).strip() for d in vsub["Visit_Date"] if str(d).strip()}
    if has_rev:
        dates |= {str(d).strip() for d in rsub["Date"] if str(d).strip()}

    rows = []
    for d in sorted(dates):
        rrev = rsub[rsub["Date"].astype(str).str.strip() == d] if has_rev else None
        def src_sum(s):
            if rrev is None or rrev.empty:
                return 0.0
            return float(rrev[rrev["Source"] == s]["Net"].sum())
        cons, xray, proc, lab = src_sum("Consultation"), src_sum("X-ray"), src_sum("Procedure"), src_sum("Lab")
        total = cons + xray + proc + lab
        mode = shift = ""
        pending = 0.0
        if rrev is not None and not rrev.empty:
            modes = [m for m in rrev["Mode_Of_Payment"].tolist() if str(m).strip()]
            mode = modes[0] if modes else ""
            shifts = [s for s in rrev["Shift"].tolist() if str(s).strip()]
            shift = shifts[0] if shifts else ""
            pending = float(rrev["Pending"].sum())
        rows.append({
            "Date": d, "Consultation": cons, "Xray": xray, "Procedure": proc,
            "Lab": lab, "Total": total, "Mode": mode, "Shift": shift,
            "Pending": pending, "Had_Revenue": total > 0,
        })

    all_dates = [parse_date(r["Date"]) for r in rows if parse_date(r["Date"])]
    by_source = {}
    if has_rev:
        by_source = {k: float(v) for k, v in rsub.groupby("Source")["Net"].sum().items()}
    return {
        "uid": uid, "clinic_id": clinic_id, "name": name, "mobile": mobile,
        "first_date": min(all_dates) if all_dates else None,
        "last_date": max(all_dates) if all_dates else None,
        "visit_count": len(rows),
        "lifetime_net": float(rsub["Net"].sum()) if has_rev else 0.0,
        "by_source": by_source,
        "rows": rows,
    }


def patient_lifetime(query: str) -> dict | None:
    """Lifetime + per-visit revenue for one patient (by Clinic ID / mobile / UID)."""
    df = _ledger_numeric()
    if df.empty:
        return None
    q = str(query or "").strip()
    sub = df[df["Patient_UID"].str.strip() == q]
    if sub.empty:
        digits = re.sub(r"\D", "", q)
        if digits:
            sub = df[df["Clinic_Specific_Id"].astype(str).str.strip() == digits]
        if sub.empty:
            mob = clean_mobile(q)
            if mob:
                sub = df[df["Mobile_Clean"] == mob]
    if sub.empty:
        return None
    name = sub["Patient_Name"].dropna().iloc[-1] if len(sub) else ""
    by_source = sub.groupby("Source")["Net"].sum().to_dict()
    visits = (sub.groupby("Date")
                 .agg(Net=("Net", "sum"))
                 .reset_index().sort_values("Date"))
    return {
        "uid": sub["Patient_UID"].iloc[0],
        "clinic_id": sub["Clinic_Specific_Id"].iloc[0],
        "name": name,
        "lifetime_net": float(sub["Net"].sum()),
        "by_source": {k: float(v) for k, v in by_source.items()},
        "visit_count": int(sub["Date"].nunique()),
        "visits": visits.to_dict("records"),
        "first_date": sub["_d"].min(),
        "last_date": sub["_d"].max(),
    }


def totals_for_period(start: date, end: date) -> dict:
    """Aggregate net revenue between start and end (inclusive)."""
    df = _ledger_numeric()
    if df.empty:
        return {"net": 0.0, "by_source": {}, "rows": 0}
    sub = df[(df["_d"] >= start) & (df["_d"] <= end)]
    return {
        "net": float(sub["Net"].sum()),
        "by_source": {k: float(v) for k, v in sub.groupby("Source")["Net"].sum().items()},
        "cash": float(sub["Cash"].sum()),
        "online": float(sub["Online"].sum()),
        "rows": int(len(sub)),
        "patients": int(sub["Patient_UID"].nunique()),
    }


def fy_start(d: date) -> date:
    """Indian financial-year start. The FY runs 1 April -> 31 March, so for any
    date in Jan-Mar the FY began on 1 April of the PREVIOUS calendar year."""
    return date(d.year if d.month >= 4 else d.year - 1, 4, 1)


def lines_for_period(source: str, start: date, end: date) -> list[dict]:
    """Individual revenue lines for one source within a period (drill-down)."""
    df = _ledger_numeric()
    if df.empty:
        return []
    sub = df[(df["_d"] >= start) & (df["_d"] <= end) & (df["Source"] == source)]
    sub = sub.sort_values("_d")
    return [{
        "Date": r["Date"], "Name": r["Patient_Name"],
        "Clinic_Id": r["Clinic_Specific_Id"], "UID": r["Patient_UID"],
        "Net": float(r["Net"]), "Mode": r["Mode_Of_Payment"],
    } for _, r in sub.iterrows()]


def dashboard_presets(today: date) -> list[dict]:
    """Quick date-range presets for the finance dashboard."""
    s = date_to_str
    month_start = today.replace(day=1)
    lm_end = month_start - timedelta(days=1)
    lm_start = lm_end.replace(day=1)
    return [
        {"label": "Today",       "from": s(today),               "to": s(today)},
        {"label": "Yesterday",   "from": s(today - timedelta(days=1)), "to": s(today - timedelta(days=1))},
        {"label": "Last 7 days", "from": s(today - timedelta(days=6)), "to": s(today)},
        {"label": "This month",  "from": s(month_start),         "to": s(today)},
        {"label": "Last month",  "from": s(lm_start),            "to": s(lm_end)},
        {"label": "This FY",     "from": s(fy_start(today)),     "to": s(today)},
    ]


def finance_summary(today: date | None = None) -> dict:
    """Day / month-to-date / FINANCIAL-year-to-date roll-up for the dashboard.
    'year' is the Indian financial year (1 Apr -> 31 Mar)."""
    today = today or date.today()
    month_start = today.replace(day=1)
    year_start = fy_start(today)
    return {
        "today": totals_for_period(today, today),
        "month": totals_for_period(month_start, today),
        "year": totals_for_period(year_start, today),
        "as_of": date_to_str(today),
    }
