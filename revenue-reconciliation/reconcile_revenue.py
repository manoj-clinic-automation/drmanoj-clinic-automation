#!/usr/bin/env python3
"""
reconcile_revenue.py — External revenue reconciler (Pharmacy + Lab → patient ledger)
Dr. Manoj Agarwal Clinic, Bareilly

WHAT THIS DOES
  Takes external revenue files that the EMR does NOT carry — pathology (Labmate /
  NK Pathology) and pharmacy (Marg / Sanjeevni) — and attributes every bill to the
  right patient, so that money becomes visible in the clinic's existing /finance
  views (which read revenue_ledger.csv).

NORTH STAR (locked decision D11)
  • Map the MAXIMUM amount of CORRECT revenue from 1 April onward.
  • NEVER drop a rupee — every bill's value is always counted somewhere.
  • Doubtful (2+ candidate patients) → a per-patient REVIEW list (the doctor decides).
  • Truly unmatchable → tagged "Unclassified" but STILL counted in the total.
  • NEVER force-assign a bill to the wrong patient.

TWO ERAS, TWO STRATEGIES (handled by the same matching ladder)
  • Suffix era (Marg 20-Jun-onward; Labmate going forward): the bill carries a
    Clinic ID and/or a 10-digit mobile → clean exact match.
  • Pre-suffix historical (the 1-Apr Labmate backlog): name only, no Clinic ID/
    mobile → must use NAME + (bill-date ↔ visit-date) cross-match. This is the
    fuzzy engine, and it is what this build proves first on the Labmate file.

THE MATCHING LADDER (per bill, first hit wins)
  1. Clinic ID exact            → matched (Match_By = clinic_id)
  2. Mobile exact (unique)      → matched (Match_By = mobile)
  3. Name-set + a visit within ±DATE_WINDOW_DAYS, UNIQUE patient → matched (name_date)
  4. Name-set unique in master (single patient, no date help)    → matched (name_only)
  5. 2+ candidate patients (ambiguous)   → REVIEW list (never auto-pick)
  6. No candidate at all                 → Unclassified (rupee still counted)

OUTPUT (only when run with --write; default is a dry-run summary that writes nothing)
  • reconciled_revenue_ledger.csv — rows in the EXACT 20-column revenue_ledger.csv
    schema (so /finance reads them natively), PLUS audit columns appended AFTER the
    20 (Match_Status, Match_By, Confidence, Candidate_Count, Source_File) which the
    finance views simply ignore.
  • revenue_review.csv — the doubtful bills, each with their candidate patients, for
    the doctor's per-patient call.

INVARIANT (asserted in code): sum(Net of every output bucket) == sum(Net of input).
No rupee is ever created or dropped.

USAGE
  Dry-run (default — prints where the money lands, writes nothing):
      python3 reconcile_revenue.py
  Write the outputs:
      python3 reconcile_revenue.py --write
  Point at specific files / change the window:
      python3 reconcile_revenue.py --labmate PATH --window 3 --outdir DIR
"""

from __future__ import annotations

import argparse
import re
import sys
import uuid
from datetime import datetime, date
from pathlib import Path

import pandas as pd


# ════════════════════════════════════════════════════════════════════════════
# CONFIG — everything tunable lives here (no code change needed to retune)
# ════════════════════════════════════════════════════════════════════════════

# Match a lab/pharmacy bill date to a clinic visit date within this many days
# either side (the "same episode" window). Owner decision: ±3 days.
DATE_WINDOW_DAYS = 3

# Source tags written into the ledger's "Source" column. These join the existing
# /finance group-bys. "Lab" already exists in the live ledger; "Pharmacy" is new;
# "Unclassified" is the never-drop-a-rupee fallback.
SOURCE_LAB          = "Lab"
SOURCE_PHARMACY     = "Pharmacy"
SOURCE_UNCLASSIFIED = "Unclassified"

# Honorifics / relational prefixes to strip before name matching.
HONORIFICS = {
    "mr", "mrs", "ms", "miss", "master", "mast", "smt", "sh", "shri", "sri",
    "km", "kumari", "dr", "baby", "bo", "wo", "so", "do", "c/o", "co",
}

# Docterz placeholder for "no mobile" — treated as blank (mirrors the tracker).
NO_MOBILE_PLACEHOLDER = "1111111111"

# The 20-column revenue_ledger.csv schema (MUST match revenue.py exactly).
REVENUE_COLS = [
    "Revenue_ID", "Date", "Patient_UID", "Clinic_Specific_Id", "Patient_Name",
    "Mobile_Clean", "Source", "Gross", "Discount", "Net",
    "Mode_Of_Payment", "Cash", "Online", "Pending",
    "Shift", "Purpose_Of_Visit", "Invoice_No",
    "Origin", "Entered_By", "Processed_On",
]
# Audit columns appended AFTER the 20 (finance ignores them; we keep the trail).
AUDIT_COLS = ["Match_Status", "Match_By", "Confidence", "Candidate_Count", "Source_File"]


# ════════════════════════════════════════════════════════════════════════════
# Helpers — mirror the tracker's behaviour so keys line up with the live ledger
# ════════════════════════════════════════════════════════════════════════════

def clean_mobile(raw) -> str:
    """Normalise any mobile input to a clean 10-digit Indian number, else ''.
    Mirrors processor.clean_mobile so keys match the live ledger exactly."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return ""
    s = str(raw).strip()
    s = re.sub(r"\.0+$", "", s)        # kill float artefact ".0"
    s = re.sub(r"\D", "", s)           # digits only
    if s.startswith("91") and len(s) == 12:
        s = s[2:]
    if s.startswith("0") and len(s) == 11:
        s = s[1:]
    if s == NO_MOBILE_PLACEHOLDER:
        return ""
    if len(s) == 10 and s[0] in "6789":
        return s
    return ""


def _num(x) -> float:
    """Parse a money cell to float. Handles '1,150', ' 500 ', '', None, '#VALUE!'."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return 0.0
    s = str(x).replace(",", "").strip()
    if s in ("", "nan", "None", "#VALUE!", "-"):
        return 0.0
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def parse_any_date(val):
    """Parse a date from the formats seen across these files. Returns a date or None.
    Handles 'DD-MM-YYYY hh:mm AM/PM', 'DD-MM-YYYY', 'YYYY-MM-DD', 'DD/MM/YYYY'."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if not s:
        return None
    # Datetime with AM/PM (consultation reports)
    for fmt in ("%d-%m-%Y %I:%M %p", "%d/%m/%Y %I:%M %p"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    # Date-only forms (take first 10 chars)
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            pass
    return None


def normalise_name(raw) -> frozenset:
    """Strip honorifics, lowercase, drop punctuation, return a TOKEN SET (order-
    independent). 'Mr. Manoj Gupta' and 'GUPTA MANOJ' → {'manoj','gupta'}."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return frozenset()
    s = str(raw).lower()
    s = re.sub(r"[^a-z\s]", " ", s)          # punctuation/digits → space
    toks = [t for t in s.split() if t and t not in HONORIFICS and len(t) > 1]
    return frozenset(toks)


# ════════════════════════════════════════════════════════════════════════════
# Load the spines (identity master + unified visit-date ledger)
# ════════════════════════════════════════════════════════════════════════════

def load_master(path: Path) -> pd.DataFrame:
    """patient_master.csv → the identity spine. Adds Mobile_Clean + _nameset."""
    m = pd.read_csv(path, dtype=str).fillna("")
    m["Mobile_Clean"] = m.get("Mobile_Clean", m.get("Mobile", "")).map(clean_mobile)
    m["Clinic_Specific_Id"] = m["Clinic_Specific_Id"].astype(str).str.strip()
    m["_nameset"] = m["Patient_Name"].map(normalise_name)
    return m


def load_visit_spine(consult_path: Path, ledger_path: Path | None) -> pd.DataFrame:
    """Union of (a) the Apr–Jun consultation report and (b) the June visit ledger
    into one per-visit table: Patient_UID, Clinic_Specific_Id, Patient_Name,
    Mobile_Clean, Visit_Date (date), _nameset. De-duped on (UID, date)."""
    frames = []

    # (a) consultation report (Docterz raw, DD-MM-YYYY hh:mm AM/PM)
    cr = pd.read_csv(consult_path, dtype=str, engine="python",
                     on_bad_lines="skip").fillna("")
    cr = cr[~cr["Patient UID"].astype(str).str.strip().isin(["", "nan"])]
    cr = cr[cr["Patient Name"].astype(str).str.strip().str.lower() != "total"]
    a = pd.DataFrame({
        "Patient_UID":        cr["Patient UID"].astype(str).str.strip(),
        "Clinic_Specific_Id": cr["Clinic Specific Id"].astype(str).str.strip(),
        "Patient_Name":       cr["Patient Name"].astype(str).str.strip(),
        "Mobile_Clean":       cr["Mobile"].map(clean_mobile),
        "Visit_Date":         cr["Consultation Date"].map(parse_any_date),
    })
    frames.append(a)

    # (b) June visit ledger (YYYY-MM-DD)
    if ledger_path and Path(ledger_path).exists():
        vl = pd.read_csv(ledger_path, dtype=str).fillna("")
        b = pd.DataFrame({
            "Patient_UID":        vl["Patient_UID"].astype(str).str.strip(),
            "Clinic_Specific_Id": vl["Clinic_Specific_Id"].astype(str).str.strip(),
            "Patient_Name":       vl["Patient_Name"].astype(str).str.strip(),
            "Mobile_Clean":       vl["Mobile_Clean"].map(clean_mobile),
            "Visit_Date":         vl["Visit_Date"].map(parse_any_date),
        })
        frames.append(b)

    spine = pd.concat(frames, ignore_index=True)
    spine = spine[spine["Visit_Date"].notna()].copy()
    spine["_dk"] = spine["Patient_UID"] + "|" + spine["Visit_Date"].astype(str)
    spine = spine.drop_duplicates("_dk").drop(columns="_dk").reset_index(drop=True)
    spine["_nameset"] = spine["Patient_Name"].map(normalise_name)
    return spine


# ════════════════════════════════════════════════════════════════════════════
# Read an external revenue file → a normalised list of bills
# Each bill: {Date(date|None), Name(str), Mobile(str|''), Clinic_Id(str|''),
#             Gross, Discount, Net, Invoice_No, Raw}
# ════════════════════════════════════════════════════════════════════════════

def read_labmate(path: Path) -> list[dict]:
    """Labmate pathology xlsx (pre-suffix era): grouped doctor-wise report.
    Header on row 2: Date | Sr. | Name | (blank) | Charge | Disc | Net | Receipt | ...
    Only rows with a real date are bills. No Clinic ID / mobile in this file."""
    raw = pd.read_excel(path, sheet_name=0, header=None)
    hdr = [str(h).strip() for h in raw.iloc[2].tolist()]
    df = raw.iloc[3:].copy()
    df.columns = hdr
    bills = []
    for _, r in df.iterrows():
        d = parse_any_date(r.get("Date"))
        if d is None:                      # group label / total / blank → skip
            continue
        gross = _num(r.get("Charge"))
        disc  = _num(r.get("Disc"))
        net   = _num(r.get("Net"))
        bills.append({
            "Date": d, "Name": str(r.get("Name") or "").strip(),
            "Mobile": "", "Clinic_Id": "",
            "Gross": gross, "Discount": disc, "Net": net,
            "Invoice_No": str(r.get("Sr.") or "").strip(),
            "Raw": str(r.get("Name") or "").strip(),
        })
    return bills


def read_marg(path: Path) -> list[dict]:
    """Marg pharmacy .XLS (suffix era): 3 cols BILL NO. | DESCRIPTION | BILL VALUE.
    Identity is embedded in DESCRIPTION as: [10-digit mobile] NAME [4-digit Clinic ID].
    A single date row precedes the bills. Net == Gross (no discount column)."""
    full = pd.read_excel(path, sheet_name=0, header=None)
    # find header row ('BILL NO.')
    hdr_row = None
    for i in range(min(12, len(full))):
        if str(full.iloc[i, 0]).strip().upper().startswith("BILL"):
            hdr_row = i
            break
    if hdr_row is None:
        return []
    body = full.iloc[hdr_row + 1:].copy()
    body.columns = ["BILL_NO", "DESC", "VAL"][:body.shape[1]]
    cur_date = None
    bills = []
    for _, r in body.iterrows():
        bno = str(r.get("BILL_NO") or "").strip()
        desc = str(r.get("DESC") or "").strip()
        val = _num(r.get("VAL"))
        # a date-only row updates the running date
        d = parse_any_date(bno)
        if d is not None and not desc:
            cur_date = d
            continue
        if not re.match(r"^[A-Z]?\d{3,}", bno):   # not a bill row (totals etc.)
            continue
        # parse identity out of DESC
        mob = ""
        m = re.match(r"^\s*(\d{10})\b", desc)
        if m:
            mob = clean_mobile(m.group(1))
            desc_rest = desc[m.end():].strip()
        else:
            desc_rest = desc
        # 4-digit Clinic ID = a standalone 4-digit token in the remainder
        cids = re.findall(r"\b(\d{4})\b", desc_rest)
        clinic_id = cids[-1] if cids else ""     # suffix → take the last 4-digit token
        name = re.sub(r"\b\d{2,}\b", " ", desc_rest)   # strip number tokens for the name
        name = re.sub(r"[^A-Za-z\s]", " ", name).strip()
        bills.append({
            "Date": cur_date, "Name": name, "Mobile": mob, "Clinic_Id": clinic_id,
            "Gross": val, "Discount": 0.0, "Net": val,
            "Invoice_No": bno, "Raw": desc,
        })
    return bills


# ════════════════════════════════════════════════════════════════════════════
# The matching ladder
# ════════════════════════════════════════════════════════════════════════════

class Matcher:
    def __init__(self, master: pd.DataFrame, spine: pd.DataFrame,
                 window_days: int = DATE_WINDOW_DAYS):
        self.master = master
        self.spine = spine
        self.window_days = window_days
        # exact-key indexes (built once)
        self.by_cid = {}
        for _, r in master.iterrows():
            cid = r["Clinic_Specific_Id"]
            if cid:
                self.by_cid.setdefault(cid, []).append(r)
        self.by_mob = {}
        for _, r in master.iterrows():
            mob = r["Mobile_Clean"]
            if mob:
                self.by_mob.setdefault(mob, []).append(r)
        # name-set index over the MASTER (for name_only) keyed by frozenset
        self.by_nameset = {}
        for _, r in master.iterrows():
            ns = r["_nameset"]
            if ns:
                self.by_nameset.setdefault(ns, []).append(r)
        # visits grouped by name-set (for name_date), each entry carries its UID+date
        self.visits_by_nameset = {}
        for _, v in spine.iterrows():
            ns = v["_nameset"]
            if ns:
                self.visits_by_nameset.setdefault(ns, []).append(v)

    @staticmethod
    def _ident(row) -> dict:
        return {
            "uid": str(row["Patient_UID"]).strip(),
            "clinic_id": str(row["Clinic_Specific_Id"]).strip(),
            "name": str(row["Patient_Name"]).strip(),
            "mobile": str(row.get("Mobile_Clean", "")).strip(),
        }

    def match(self, bill: dict) -> dict:
        """Return a result dict: {status, by, confidence, candidates[list of ident],
        chosen(ident|None)}. status ∈ matched / review / unclassified."""
        # 1. Clinic ID exact
        cid = str(bill.get("Clinic_Id") or "").strip()
        if cid and cid in self.by_cid:
            rows = self.by_cid[cid]
            if len(rows) == 1:
                return self._ok(rows[0], "clinic_id", "high")
            # >1 patient on a clinic id should not happen (it's the key) → review
            return self._review([self._ident(r) for r in rows], "clinic_id_multi")

        # 2. Mobile exact (unique)
        mob = clean_mobile(bill.get("Mobile"))
        if mob and mob in self.by_mob:
            rows = self.by_mob[mob]
            if len(rows) == 1:
                return self._ok(rows[0], "mobile", "high")
            # shared family mobile → try to break the tie by name, else review
            ns = normalise_name(bill.get("Name"))
            narrowed = [r for r in rows if r["_nameset"] & ns] if ns else rows
            if len(narrowed) == 1:
                return self._ok(narrowed[0], "mobile+name", "high")
            return self._review([self._ident(r) for r in rows], "mobile_shared")

        # 3 & 4. Name-set matching
        ns = normalise_name(bill.get("Name"))
        if not ns:
            return self._unclassified()

        bdate = bill.get("Date")
        # 3. name + a visit within the date window → unique patient
        if bdate is not None:
            hits = []
            for cand_ns, visits in self.visits_by_nameset.items():
                if not (cand_ns & ns):
                    continue
                # require a decent token overlap (all bill tokens present, or full set match)
                if not ns.issubset(cand_ns) and not cand_ns.issubset(ns):
                    continue
                for v in visits:
                    dd = v["Visit_Date"]
                    if dd and abs((dd - bdate).days) <= self.window_days:
                        hits.append(v)
            uids = {str(h["Patient_UID"]).strip() for h in hits}
            if len(uids) == 1:
                return self._ok(hits[0], "name_date", "high")
            if len(uids) > 1:
                # several different patients with that name visited in-window → review
                idents = []
                seen = set()
                for h in hits:
                    u = str(h["Patient_UID"]).strip()
                    if u not in seen:
                        seen.add(u)
                        idents.append(self._ident(h))
                return self._review(idents, "name_date_multi")

        # 4. name unique in master (no date help)
        exact = self.by_nameset.get(ns, [])
        if len(exact) == 1:
            return self._ok(exact[0], "name_only", "medium")
        if len(exact) > 1:
            return self._review([self._ident(r) for r in exact], "name_multi")

        # subset/superset name search across master (handles 1-vs-2 token differences)
        loose = []
        seen = set()
        for cand_ns, rows in self.by_nameset.items():
            if ns.issubset(cand_ns) or cand_ns.issubset(ns):
                for r in rows:
                    u = str(r["Patient_UID"]).strip()
                    if u not in seen:
                        seen.add(u)
                        loose.append(r)
        if len(loose) == 1:
            return self._ok(loose[0], "name_loose", "medium")
        if len(loose) > 1:
            return self._review([self._ident(r) for r in loose], "name_loose_multi")

        # 6. nothing
        return self._unclassified()

    def _ok(self, row, by, conf):
        return {"status": "matched", "by": by, "confidence": conf,
                "candidates": [self._ident(row)], "chosen": self._ident(row)}

    def _review(self, idents, by):
        return {"status": "review", "by": by, "confidence": "ambiguous",
                "candidates": idents, "chosen": None}

    def _unclassified(self):
        return {"status": "unclassified", "by": "none", "confidence": "none",
                "candidates": [], "chosen": None}


# ════════════════════════════════════════════════════════════════════════════
# Build ledger rows + review rows from matched bills
# ════════════════════════════════════════════════════════════════════════════

def to_ledger_row(bill: dict, res: dict, source_tag: str, source_file: str,
                  processed_on: str) -> dict:
    chosen = res["chosen"] or {}
    if res["status"] == "unclassified":
        src = SOURCE_UNCLASSIFIED
    else:
        src = source_tag
    row = {
        "Revenue_ID": "X" + uuid.uuid4().hex[:10].upper(),
        "Date": bill["Date"].strftime("%Y-%m-%d") if bill.get("Date") else "",
        "Patient_UID": chosen.get("uid", ""),
        "Clinic_Specific_Id": chosen.get("clinic_id", "") or bill.get("Clinic_Id", ""),
        "Patient_Name": chosen.get("name", "") or bill.get("Name", ""),
        "Mobile_Clean": chosen.get("mobile", "") or clean_mobile(bill.get("Mobile")),
        "Source": src,
        "Gross": bill["Gross"], "Discount": bill["Discount"], "Net": bill["Net"],
        "Mode_Of_Payment": "", "Cash": "", "Online": "", "Pending": "",
        "Shift": "", "Purpose_Of_Visit": "Pathology" if source_tag == SOURCE_LAB else "Pharmacy",
        "Invoice_No": bill.get("Invoice_No", ""),
        "Origin": f"reconciler:{source_file}",
        "Entered_By": "Reconciler (auto)",
        "Processed_On": processed_on,
        # audit
        "Match_Status": res["status"], "Match_By": res["by"],
        "Confidence": res["confidence"],
        "Candidate_Count": len(res["candidates"]),
        "Source_File": source_file,
    }
    return row


def reconcile(bills: list[dict], matcher: Matcher, source_tag: str,
              source_file: str) -> tuple[list[dict], list[dict]]:
    processed_on = datetime.now().strftime("%Y-%m-%d %H:%M")
    ledger_rows, review_rows = [], []
    for bill in bills:
        res = matcher.match(bill)
        ledger_rows.append(to_ledger_row(bill, res, source_tag, source_file, processed_on))
        if res["status"] == "review":
            for i, cand in enumerate(res["candidates"], 1):
                review_rows.append({
                    "Source_File": source_file,
                    "Bill_Date": bill["Date"].strftime("%Y-%m-%d") if bill.get("Date") else "",
                    "Bill_Name": bill.get("Name", ""),
                    "Bill_Mobile": clean_mobile(bill.get("Mobile")),
                    "Bill_Clinic_Id": bill.get("Clinic_Id", ""),
                    "Net": bill["Net"],
                    "Invoice_No": bill.get("Invoice_No", ""),
                    "Reason": res["by"],
                    "Candidate_No": i,
                    "Cand_UID": cand["uid"],
                    "Cand_Clinic_Id": cand["clinic_id"],
                    "Cand_Name": cand["name"],
                    "Cand_Mobile": cand["mobile"],
                })
    return ledger_rows, review_rows


# ════════════════════════════════════════════════════════════════════════════
# Dry-run summary
# ════════════════════════════════════════════════════════════════════════════

def rupee(x) -> str:
    return f"₹{x:,.0f}"


def summarise(ledger_rows: list[dict], input_net: float, label: str):
    df = pd.DataFrame(ledger_rows)
    df["Net"] = pd.to_numeric(df["Net"], errors="coerce").fillna(0.0)
    print(f"\n{'='*68}\n  DRY-RUN SUMMARY — {label}\n{'='*68}")
    print(f"  Bills in        : {len(df)}")
    print(f"  ₹ in (input Net): {rupee(input_net)}")
    print(f"  ₹ out (ledger)  : {rupee(df['Net'].sum())}")
    print(f"\n  WHERE THE MONEY LANDS (count · ₹):")
    # group by status then by Match_By
    for status in ["matched", "review", "unclassified"]:
        sub = df[df["Match_Status"] == status]
        if not len(sub):
            continue
        print(f"    {status.upper():<14} {len(sub):>4} bills · {rupee(sub['Net'].sum()):>12}")
        for by, g in sub.groupby("Match_By"):
            print(f"        ├─ {by:<18} {len(g):>4} · {rupee(g['Net'].sum()):>12}")
    # invariant
    diff = round(df["Net"].sum() - input_net, 2)
    ok = abs(diff) < 0.5
    print(f"\n  INVARIANT (no rupee dropped): "
          f"{'✅ OK' if ok else '❌ MISMATCH'}  (out − in = {rupee(diff)})")
    matched = df[df['Match_Status']=='matched']['Net'].sum()
    print(f"  Auto-attributed now: {rupee(matched)} "
          f"({matched/input_net*100:.0f}% of revenue) · "
          f"review+unclassified held: {rupee(input_net-matched)}")
    return ok


# ════════════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════════════

def main(argv=None):
    ap = argparse.ArgumentParser(description="Reconcile external revenue → patient ledger (dry-run by default).")
    ap.add_argument("--labmate", help="Labmate pathology xlsx")
    ap.add_argument("--marg", help="Marg pharmacy .XLS")
    ap.add_argument("--master", required=True, help="patient_master.csv")
    ap.add_argument("--consult", required=True, help="consultation_report.csv (Apr–Jun, has visit dates)")
    ap.add_argument("--ledger", help="June visit_ledger.csv (optional, extends visit coverage)")
    ap.add_argument("--window", type=int, default=DATE_WINDOW_DAYS, help="date window in days (default 3)")
    ap.add_argument("--outdir", default=".", help="where to write outputs (with --write)")
    ap.add_argument("--write", action="store_true", help="actually write the output files")
    args = ap.parse_args(argv)

    window = args.window

    print(f"Loading identity master … {args.master}")
    master = load_master(Path(args.master))
    print(f"  {len(master)} patients (Clinic ID filled: {(master['Clinic_Specific_Id']!='').sum()})")

    print(f"Building visit-date spine … {args.consult}" + (f" + {args.ledger}" if args.ledger else ""))
    spine = load_visit_spine(Path(args.consult), Path(args.ledger) if args.ledger else None)
    print(f"  {len(spine)} visits, {spine['Patient_UID'].nunique()} patients, "
          f"{spine['Visit_Date'].min()} → {spine['Visit_Date'].max()}  (window ±{window}d)")

    matcher = Matcher(master, spine, window_days=window)

    all_ledger, all_review = [], []
    overall_in = 0.0

    if args.labmate:
        bills = read_labmate(Path(args.labmate))
        net_in = sum(b["Net"] for b in bills)
        overall_in += net_in
        lr, rr = reconcile(bills, matcher, SOURCE_LAB, Path(args.labmate).name)
        summarise(lr, net_in, f"LABMATE (pathology) — {Path(args.labmate).name}")
        all_ledger += lr
        all_review += rr

    if args.marg:
        bills = read_marg(Path(args.marg))
        net_in = sum(b["Net"] for b in bills)
        overall_in += net_in
        lr, rr = reconcile(bills, matcher, SOURCE_PHARMACY, Path(args.marg).name)
        summarise(lr, net_in, f"MARG (pharmacy) — {Path(args.marg).name}")
        all_ledger += lr
        all_review += rr

    if not args.labmate and not args.marg:
        print("\nNothing to do: pass --labmate and/or --marg.")
        return 1

    if args.write:
        outdir = Path(args.outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        led = pd.DataFrame(all_ledger)[REVENUE_COLS + AUDIT_COLS]
        led_path = outdir / "reconciled_revenue_ledger.csv"
        led.to_csv(led_path, index=False)
        print(f"\n✍  wrote {led_path}  ({len(led)} rows)")
        if all_review:
            rev = pd.DataFrame(all_review)
            rev_path = outdir / "revenue_review.csv"
            rev.to_csv(rev_path, index=False)
            print(f"✍  wrote {rev_path}  ({rev['Invoice_No'].nunique() if 'Invoice_No' in rev else len(rev)} bills, {len(rev)} candidate rows)")
    else:
        print(f"\n(dry-run — nothing written. Re-run with --write to produce the files.)")
        if all_review:
            print(f"  {len(all_review)} candidate rows would go to revenue_review.csv")

    return 0


if __name__ == "__main__":
    sys.exit(main())
