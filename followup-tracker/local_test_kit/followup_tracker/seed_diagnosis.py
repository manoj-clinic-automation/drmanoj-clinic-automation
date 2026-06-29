"""
seed_diagnosis.py
Dr. Manoj Agarwal Clinic — Diagnosis Layer Ingestion & Enrichment

PURPOSE
-------
Take a patient export (raw Docterz `patients_detail.csv`, or the cleaned
MyOperator contacts CSV), normalise every diagnosis through the taxonomy
engine, pull out the administrative codes (CC/PD/BID/VIP), and build /update
the enriched master:

        data/patient_diagnosis.csv

This is the PERIODIC-INGESTION ROUTE. Each time a fresh Docterz file is
downloaded (from the beginning is fine and preferred), run this script /
upload the file — patients are de-duplicated by 10-digit mobile, and a
patient's diagnosis row is only overwritten when the new file carries a
non-blank diagnosis for them (so older diagnoses are never wiped by a blank).

FORMATS AUTO-DETECTED
---------------------
1. Docterz raw  (`patients_detail.csv`)
     - mobile lives in the 'Parent Name' column (known column-shift)
     - diagnosis is long-form inside 'Patient Medical History'
       ("... He was diagnosed with <DIAGNOSIS>. He was treated with ...")
2. MyOperator contacts (cleaned)
     - mobile in 'Phone Number', diagnosis already short-form in 'Diagnosis'

USAGE
-----
    python seed_diagnosis.py <source_file.csv> [<source_file2.csv> ...]
    python seed_diagnosis.py --insight        # rebuild insight workbook only
"""

import sys, re, json, datetime as dt
from pathlib import Path
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

from diagnosis_normalizer import (
    normalise_diagnosis, extract_diagnosis_from_history,
    extract_comorbidities, CATEGORY, _priority,
)

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
DIAG_FILE = DATA_DIR / "patient_diagnosis.csv"
# Freshness metadata: records WHEN the diagnosis layer was last refreshed and from
# WHICH raw export, so the app can display "Diagnosis data as of <date>" and the
# doctor knows when a fresh full Docterz export should be absorbed.
META_FILE = DATA_DIR / "diagnosis_source_meta.json"

_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def parse_asof_from_filename(name: str) -> str:
    """Parse a data cutoff date from a filename such as
    'DOCTERZ_PATIENT_LIST_UPTO_31_MAY_2026.csv' -> '2026-05-31'.
    Accepts space / underscore / hyphen separators. Returns '' if not found."""
    m = re.search(r"(\d{1,2})[ _\-]+([A-Za-z]{3,9})[ _\-]+(\d{4})", str(name))
    if m:
        day = int(m.group(1)); mon = m.group(2)[:3].lower(); yr = int(m.group(3))
        if mon in _MONTHS:
            try:
                return dt.date(yr, _MONTHS[mon], day).isoformat()
            except ValueError:
                pass
    return ""


def load_diagnosis_meta() -> dict:
    if META_FILE.exists():
        try:
            return json.loads(META_FILE.read_text())
        except Exception:
            return {}
    return {}


def write_diagnosis_meta(source_files, master, stats, asof_date="") -> dict:
    meta = load_diagnosis_meta()
    history = meta.get("history", [])
    if len(master):
        std = master["Standardized_Diagnosis"].astype(str)
        with_diag = int((~std.isin(["", "No Diagnosis Recorded", "Other / Unclassified"])).sum())
    else:
        with_diag = 0
    entry = {
        "ingested_on": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source_files": list(source_files),
        "as_of_date": asof_date or "",
        "patient_count": int(len(master)),
        "with_diagnosis": with_diag,
        "no_diagnosis": int(len(master)) - with_diag,
        "rows_with_diag_this_run": stats.get("with_diag", 0),
        "new_or_seeded_this_run": stats.get("new", 0) + stats.get("seeded", 0),
        "updated_this_run": stats.get("updated", 0),
    }
    history.append(entry)
    meta = {**entry, "history": history[-20:]}
    META_FILE.write_text(json.dumps(meta, indent=2))
    return meta

DIAG_COLS = [
    "Patient_UID", "Clinic_Specific_Id", "Patient_Name", "Age", "Sex",
    "Mobile_Clean",
    "Diagnosis_Raw", "Standardized_Diagnosis", "Diagnosis_Category",
    "Diagnosis_Priority", "Diagnosis_Status",
    "Comorbidities",
    "Concession_Scheme",
    "Admin_CC", "Admin_PD", "Admin_BID", "Is_VIP",
    "Source_File", "Last_Updated",
]

# ─────────────────────────────────────────────────────────────────────────────
def clean_mobile(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = re.sub(r"\D", "", str(v))
    if s.startswith("91") and len(s) == 12:
        s = s[2:]
    if s.startswith("0") and len(s) == 11:
        s = s[1:]
    return s[-10:] if len(s) >= 10 else ""


def _s(v):
    """NaN/None -> '' ; otherwise stripped string (avoids the literal 'nan')."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = str(v).strip()
    return "" if s.lower() == "nan" else s


def detect_format(df):
    cols = set(df.columns)
    if "Phone Number" in cols and "Diagnosis" in cols:
        return "myoperator"
    if "Patient Medical History" in cols and "Parent Name" in cols:
        # Both the shifted raw export and the clean patient list share headers.
        # Distinguish by what the 'Age' column actually holds:
        #   clean patient list -> "NN years ..."   |   shifted raw -> "male/female"
        age_sample = df["Age"].dropna().astype(str).head(50) if "Age" in cols else []
        if len(age_sample) and age_sample.str.contains(r"\d+\s*year", case=False).any():
            return "docterz_patient_list"
        return "docterz_raw"
    return "unknown"


def _read_csv(path):
    """Robust reader for Docterz exports.

    The free-text LAST column ('Patient Medical History') contains unescaped
    commas, so a patient's narrative spills into extra trailing fields. The old
    reader marked such rows 'bad' and DROPPED them — silently losing the
    diagnosis AND the CC/PD/BID/VIP codes for ~2 of every 3 patients. Here we
    read with the quote-aware csv module and, for every data row, keep the first
    N-1 fields positionally and rejoin ALL overflow back into the final column,
    so no patient row is ever dropped or misaligned. A short row (a stray line
    break inside a narrative) is appended to the previous record's last column.
    """
    import csv as _csv
    try:
        with open(path, newline="", encoding="utf-8", errors="replace") as fh:
            rows = list(_csv.reader(fh))
    except Exception:
        # last-resort fallback to the old tolerant read
        return pd.read_csv(path, engine="python", on_bad_lines="skip", dtype=str)
    if not rows:
        return pd.DataFrame()
    header = [h.strip() for h in rows[0]]
    ncol = len(header)
    last = ncol - 1
    recs = []
    for r in rows[1:]:
        if not any(str(c).strip() for c in r):
            continue                                  # blank line
        if len(r) >= ncol:
            fixed = list(r[:last]) + [",".join(r[last:])]
        elif recs:                                    # short fragment -> continuation of prev narrative
            recs[-1][last] = (str(recs[-1][last]) + " " + " ".join(r)).strip()
            continue
        else:
            fixed = list(r) + [""] * (ncol - len(r))
        recs.append(fixed)
    return pd.DataFrame(recs, columns=header).astype(object)


# ─────────────────────────────────────────────────────────────────────────────
def _parse_age(age_text, dob_text, ref=dt.date(2026, 5, 15)):
    """Pull age in years. Order of preference:
       1. 'NN years ...'  in the age text  -> NN
       2. infant 'N mons / N days' (no year) -> 0
       3. compute from DOB (DD/MM/YYYY) relative to the 15-May-2026 export date
    Returns an int-as-string, or '' if nothing usable."""
    t = _s(age_text)
    m = re.match(r"\s*(\d+)\s*year", t, re.IGNORECASE)
    if m:
        return str(int(m.group(1)))
    if re.search(r"\bmon|\bday", t, re.IGNORECASE):   # infant: months/days only
        return "0"
    # fallback: DOB
    d = _s(dob_text)
    md = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", d)
    if md:
        dd, mm, yy = int(md.group(1)), int(md.group(2)), int(md.group(3))
        if yy < 100:
            yy += 1900 if yy > 30 else 2000
        try:
            born = dt.date(yy, mm, dd)
            yrs = ref.year - born.year - ((ref.month, ref.day) < (born.month, born.day))
            if 0 <= yrs <= 120:
                return str(yrs)
        except ValueError:
            pass
    return ""


def rows_from_docterz_raw(df):
    """Docterz raw `patients_detail.csv` — column-shifted; mobile in
    'Parent Name', diagnosis long-form in 'Patient Medical History'.
    Foot Notes holds 'Name, age, gender.' which we use for the display name.
    After the shift: 'Name' col = age text, 'Age' col = sex, 'Sex' col = DOB."""
    out = []
    for _, r in df.iterrows():
        mob = clean_mobile(r.get("Parent Name"))
        history = _s(r.get("Patient Medical History"))
        raw_diag = extract_diagnosis_from_history(history)
        # name from Foot Notes ("Deepak Kapoor, 72 years, male.")
        foot = _s(r.get("Foot Notes"))
        name = foot.split(",")[0].strip() if foot else ""
        # Patient UID sits in 'Address' column after the shift
        uid = _s(r.get("Address"))
        if not re.match(r"^[A-Z]{3,}\d", uid):
            uid = ""  # not a UID-looking token
        # age: 'Name' col holds age text; 'Sex' col holds DOB (fallback)
        age = _parse_age(r.get("Name"), r.get("Sex"))
        sex = _s(r.get("Age")).lower()
        sex = {"male": "M", "female": "F"}.get(sex, "")
        out.append({
            "mobile": mob, "raw_diag": raw_diag, "name": name,
            "uid": uid, "csid": "", "age": age, "sex": sex,
        })
    return out


def rows_from_myoperator(df):
    out = []
    for _, r in df.iterrows():
        out.append({
            "mobile": clean_mobile(r.get("Phone Number")),
            "raw_diag": _s(r.get("Diagnosis")),
            "name": _s(r.get("Name")),
            "uid": "", "csid": "", "age": "", "sex": "",
        })
    return out


def rows_demographic_from_patient_list(df):
    """Clean Docterz patient-list export (NOT column-shifted): standard
    Name / Age / Sex / DOB / Mobile / Patient UID columns."""
    out = []
    for _, r in df.iterrows():
        out.append({
            "mobile": clean_mobile(r.get("Mobile")),
            "age":    _parse_age(r.get("Age"), r.get("DOB")),
            "sex":    {"male": "M", "female": "F"}.get(_s(r.get("Sex")).lower(), ""),
            "name":   _s(r.get("Name")),
            "uid":    _s(r.get("Patient UID")),
        })
    return out


def build_demographic_lookup(paths):
    """Scan every Docterz file (shifted raw OR clean patient list) fully and
    return {mobile -> {age, sex, name, uid}} from ALL rows. The Docterz exports
    carry age for ~99% of patients, so this lets us attach accurate age/sex to
    every patient in the structured data by mobile — including MyOperator ones."""
    demo = {}
    for path in paths:
        path = Path(path)
        if not path.exists():
            continue
        df = _read_csv(path)
        fmt = detect_format(df)
        if fmt == "docterz_raw":
            rows = rows_from_docterz_raw(df)
        elif fmt == "docterz_patient_list":
            rows = rows_demographic_from_patient_list(df)
        else:
            continue
        for row in rows:
            mob = row["mobile"]
            if not mob:
                continue
            cur = demo.get(mob, {"age": "", "sex": "", "name": "", "uid": ""})
            for k in ("age", "sex", "name", "uid"):
                if not cur[k] and row.get(k):
                    cur[k] = row[k]
            demo[mob] = cur
    return demo


NO_DIAGNOSIS = "No Diagnosis Recorded"

def _name_tokens(name):
    toks = set(re.findall(r"[a-z]+", str(name).lower()))
    return toks - {"mr", "mrs", "ms", "dr", "baby", "smt", "master", "the", "of"}

def comorbidities_from_significant_history(text):
    """31 May patient list 'Significant History' uses '|' as separator,
    e.g. 'HYPERTENSION | DIABETES MELLITUS'. Return canonical comorbidity list."""
    found = []
    for piece in re.split(r"[|;,]", _s(text)):
        _, cs = extract_comorbidities(piece)
        for c in cs:
            if c not in found:
                found.append(c)
    return found


def rows_from_patient_list_full(df):
    """Full patient records from the clean 31-May Docterz roster (identity base).
    Keyed by Patient UID. Carries demographics + comorbidities (Significant History)."""
    out = []
    for _, r in df.iterrows():
        out.append({
            "uid":   _s(r.get("Patient UID")),
            "csid":  _s(r.get("Clinic Specific Id")),
            "name":  _s(r.get("Name")),
            "age":   _parse_age(r.get("Age"), r.get("DOB")),
            "sex":   {"male": "M", "female": "F"}.get(_s(r.get("Sex")).lower(), ""),
            "mobile": clean_mobile(r.get("Mobile")),
            "comorbidities": comorbidities_from_significant_history(r.get("Significant History")),
        })
    return out


def rows_from_patient_list_diag(df):
    """Mine the CLEAN patient-list export as a DIAGNOSIS source.

    The long-form narrative
        '... was diagnosed with <DIAGNOSIS> and CC 0 PD 20 BID 50. She was
         treated with ...'
    lives in 'Patient Medical History' on the clean list too — not only on the
    column-shifted raw export. Returns rows in the SAME shape Phase 2 expects,
    so the existing UID-first attach + sticky admin/VIP logic is reused
    unchanged. raw_diag falls back to the full narrative when there is no
    'diagnosed with' phrase, so a CC/PD/BID/VIP written without a formal
    diagnosis is still captured."""
    out = []
    for _, r in df.iterrows():
        history  = _s(r.get("Patient Medical History"))
        raw_diag = extract_diagnosis_from_history(history) or history
        out.append({
            "mobile":   clean_mobile(r.get("Mobile")),
            "raw_diag": raw_diag,
            "name":     _s(r.get("Name")),
            "uid":      _s(r.get("Patient UID")),
            "csid":     _s(r.get("Clinic Specific Id")),
            "age":      _parse_age(r.get("Age"), r.get("DOB")),
            "sex":      {"male": "M", "female": "F"}.get(_s(r.get("Sex")).lower(), ""),
        })
    return out


def _blank_record(now):
    return {
        "Patient_UID": "", "Clinic_Specific_Id": "", "Patient_Name": "",
        "Age": "", "Sex": "", "Mobile_Clean": "",
        "Diagnosis_Raw": "", "Standardized_Diagnosis": NO_DIAGNOSIS,
        "Diagnosis_Category": NO_DIAGNOSIS, "Diagnosis_Priority": "",
        "Diagnosis_Status": "", "Comorbidities": "", "Concession_Scheme": "",
        "Admin_CC": "", "Admin_PD": "", "Admin_BID": "", "Is_VIP": False,
        "Source_File": "", "Last_Updated": now,
    }


# ─────────────────────────────────────────────────────────────────────────────
def ingest(paths, asof_date=""):
    """Two-phase build:
       Phase 1 — seed the full patient roster from the 31-May Docterz list,
                 keyed by Patient UID (every patient gets age/sex/comorbidities).
       Phase 2 — attach diagnoses from the detail export (by UID) and the
                 MyOperator-derived file (by mobile, with name disambiguation).
    Existing demographics are never blanked; VIP / admin codes / comorbidities
    are sticky and accumulate."""
    now = dt.date.today().isoformat()
    if DIAG_FILE.exists():
        master = pd.read_csv(DIAG_FILE, dtype=str).fillna("")
    else:
        master = pd.DataFrame(columns=DIAG_COLS)
    # pandas 3 makes read_csv(dtype=str) a strict StringDtype that rejects int/bool
    # on .at/.loc assignment (e.g. Is_VIP=True, an admin code, Admin_CC=0). Use plain
    # object dtype so every assignment below is accepted; CSV output is unchanged.
    master = master.astype(object)

    by_uid    = {r["Patient_UID"]: i for i, r in master.iterrows() if r.get("Patient_UID")}
    by_mobile = {}
    for i, r in master.iterrows():
        if r.get("Mobile_Clean"):
            by_mobile.setdefault(r["Mobile_Clean"], []).append(i)

    stats = {"files": 0, "rows": 0, "with_diag": 0, "new": 0, "updated": 0,
             "vip": 0, "admin": 0, "comorbid": 0, "discarded": 0, "seeded": 0}

    # classify the input files
    list_files, diag_files = [], []
    for path in paths:
        path = Path(path)
        if not path.exists():
            print(f"  ! file not found: {path}")
            continue
        fmt = detect_format(_read_csv(path))
        if fmt == "docterz_patient_list":
            list_files.append(path)
            # also mine its 'Patient Medical History' narrative for diagnosis +
            # CC/PD/BID/VIP (Phase 2). Previously the clean list was treated as a
            # roster only, so its concession codes were never extracted.
            diag_files.append((path, "docterz_patient_list"))
        elif fmt in ("docterz_raw", "myoperator"):
            diag_files.append((path, fmt))
        else:
            print(f"  ! unrecognised format: {path.name}")

    # ── PHASE 1: seed identity base from the patient roster (keyed by UID) ────
    for path in list_files:
        df = _read_csv(path)
        rows = rows_from_patient_list_full(df)
        stats["files"] += 1
        print(f"  • {path.name}: format=docterz_patient_list (roster), {len(rows)} rows")
        for row in rows:
            stats["rows"] += 1
            uid, mob = row["uid"], row["mobile"]
            # roster rows always carry a UID — match by UID ONLY here, so family
            # members who share one mobile are never collapsed into each other.
            idx = by_uid.get(uid) if uid else None
            if idx is None and not uid and mob and len(by_mobile.get(mob, [])) == 1:
                idx = by_mobile[mob][0]
            if idx is None:
                rec = _blank_record(now)
                rec.update({
                    "Patient_UID": uid, "Clinic_Specific_Id": row["csid"],
                    "Patient_Name": row["name"], "Age": row["age"], "Sex": row["sex"],
                    "Mobile_Clean": mob, "Source_File": path.name,
                    "Comorbidities": "; ".join(row["comorbidities"]),
                })
                master = pd.concat([master, pd.DataFrame([rec])], ignore_index=True)
                ni = len(master) - 1
                if uid: by_uid[uid] = ni
                if mob: by_mobile.setdefault(mob, []).append(ni)
                stats["seeded"] += 1
            else:
                for k, v in (("Patient_Name", row["name"]), ("Age", row["age"]),
                             ("Sex", row["sex"]), ("Clinic_Specific_Id", row["csid"]),
                             ("Patient_UID", uid), ("Mobile_Clean", mob)):
                    if v and not str(master.at[idx, k]).strip():
                        master.at[idx, k] = v
                if row["comorbidities"]:
                    merged = set(str(master.at[idx, "Comorbidities"]).split("; ")) | set(row["comorbidities"])
                    merged.discard("")
                    master.at[idx, "Comorbidities"] = "; ".join(sorted(merged))

    # ── PHASE 2: attach diagnoses from detail + MyOperator files ─────────────
    for path, fmt in diag_files:
        df = _read_csv(path)
        if fmt == "docterz_raw":
            rows = rows_from_docterz_raw(df)
        elif fmt == "docterz_patient_list":
            rows = rows_from_patient_list_diag(df)
        else:
            rows = rows_from_myoperator(df)
        stats["files"] += 1
        print(f"  • {path.name}: format={fmt}, {len(rows)} rows")
        for row in rows:
            stats["rows"] += 1
            mob, uid = row["mobile"], row.get("uid", "")
            norm = normalise_diagnosis(row["raw_diag"])

            has_clinical = norm["Standardized_Diagnosis"] != "Other / Unclassified"
            has_admin    = any([norm["Admin_CC"] != "", norm["Admin_PD"] != "",
                                norm["Admin_BID"] != "", norm["Is_VIP"]])
            has_comorbid = bool(norm["Comorbidities"])
            has_text     = bool(norm["Diagnosis_Raw"].strip())
            if norm["Is_Discard"] and not has_comorbid and not has_admin:
                stats["discarded"] += 1
                continue
            if not has_clinical and not has_admin and not has_text and not has_comorbid:
                continue

            # resolve to a master row: by UID first, else by mobile (+ name match)
            idx = by_uid.get(uid) if uid else None
            if idx is None and mob:
                cands = by_mobile.get(mob, [])
                if len(cands) == 1:
                    idx = cands[0]
                elif len(cands) > 1:
                    nt = _name_tokens(row["name"])
                    best, bscore = None, 0.0
                    for c in cands:
                        ot = _name_tokens(master.at[c, "Patient_Name"])
                        if nt and ot:
                            sc = len(nt & ot) / len(nt | ot)
                            if sc > bscore:
                                best, bscore = c, sc
                    idx = best if bscore >= 0.34 else None   # ambiguous family -> treat as new

            if idx is None:
                # patient not in roster (or unresolved family member) -> add new
                rec = _blank_record(now)
                rec.update({
                    "Patient_UID": uid, "Clinic_Specific_Id": row.get("csid", ""),
                    "Patient_Name": row["name"], "Age": row["age"], "Sex": row["sex"],
                    "Mobile_Clean": mob, "Source_File": path.name,
                    "Diagnosis_Raw": norm["Diagnosis_Raw"],
                    "Standardized_Diagnosis": norm["Standardized_Diagnosis"],
                    "Diagnosis_Category": norm["Diagnosis_Category"],
                    "Diagnosis_Priority": norm["Diagnosis_Priority"],
                    "Diagnosis_Status": norm["Diagnosis_Status"],
                    "Comorbidities": norm["Comorbidities"],
                    "Concession_Scheme": norm["Concession_Scheme"],
                    "Admin_CC": norm["Admin_CC"], "Admin_PD": norm["Admin_PD"],
                    "Admin_BID": norm["Admin_BID"], "Is_VIP": norm["Is_VIP"],
                })
                master = pd.concat([master, pd.DataFrame([rec])], ignore_index=True)
                ni = len(master) - 1
                if uid: by_uid[uid] = ni
                if mob: by_mobile.setdefault(mob, []).append(ni)
                stats["new"] += 1
            else:
                cur = master.loc[idx]
                if has_clinical:
                    stats["updated"] += 1
                # attach clinical fields when this file has a real diagnosis (or current is empty)
                cur_std = cur["Standardized_Diagnosis"]
                if has_clinical or cur_std in ("", NO_DIAGNOSIS, "Other / Unclassified"):
                    for k, v in (("Diagnosis_Raw", norm["Diagnosis_Raw"]),
                                 ("Standardized_Diagnosis", norm["Standardized_Diagnosis"]),
                                 ("Diagnosis_Category", norm["Diagnosis_Category"]),
                                 ("Diagnosis_Priority", norm["Diagnosis_Priority"]),
                                 ("Diagnosis_Status", norm["Diagnosis_Status"]),
                                 ("Source_File", path.name)):
                        if k.startswith("Diagnosis") and not has_clinical and v in ("", "Other / Unclassified"):
                            continue
                        master.at[idx, k] = v
                # fill any missing demographics from this file too
                for k, v in (("Patient_Name", row["name"]), ("Age", row["age"]),
                             ("Sex", row["sex"]), ("Patient_UID", uid)):
                    if v and not str(master.at[idx, k]).strip():
                        master.at[idx, k] = v
                # sticky VIP / admin / comorbidities
                if norm["Is_VIP"] or str(cur["Is_VIP"]) == "True":
                    master.at[idx, "Is_VIP"] = True
                for k, v in (("Admin_CC", norm["Admin_CC"]), ("Admin_PD", norm["Admin_PD"]),
                             ("Admin_BID", norm["Admin_BID"])):
                    if v not in ("", False) and str(cur[k]) in ("", "False"):
                        master.at[idx, k] = v
                if norm["Comorbidities"]:
                    merged = set(str(cur["Comorbidities"]).split("; ")) | set(norm["Comorbidities"].split("; "))
                    merged.discard("")
                    master.at[idx, "Comorbidities"] = "; ".join(sorted(merged))
                if norm["Concession_Scheme"]:
                    merged = set(str(cur["Concession_Scheme"]).split("; ")) | set(norm["Concession_Scheme"].split("; "))
                    merged.discard("")
                    master.at[idx, "Concession_Scheme"] = "; ".join(sorted(merged))
                master.at[idx, "Last_Updated"] = now

            if has_clinical:  stats["with_diag"] += 1
            if norm["Is_VIP"]: stats["vip"] += 1
            if has_admin:      stats["admin"] += 1
            if has_comorbid:   stats["comorbid"] += 1

    # VIP implies complimentary consultation (CC 0) wherever a VIP has no explicit CC
    master = master.astype(object)   # guard against StringDtype re-inference from concat
    vip_mask = master["Is_VIP"].astype(str) == "True"
    master.loc[vip_mask & (master["Admin_CC"].astype(str).str.strip() == ""), "Admin_CC"] = "0"

    # ── Demographic enrichment ───────────────────────────────────────────────
    # Fill age / sex / name / UID for every patient by mobile, using the Docterz
    # exports as the demographic source (they carry age for ~99% of patients).
    # In addition to the files passed in, auto-discover any Docterz demographic
    # export kept alongside the app (so periodic uploads still enrich age).
    demo_paths = list(paths)
    for d in (Path(__file__).resolve().parent, UPLOAD_DIR, DATA_DIR):
        if d.exists():
            for f in d.glob("*.csv"):
                nm = f.name.upper()
                if ("PATIENT_LIST" in nm or "PATIENTS_DETAIL" in nm) and str(f) not in demo_paths:
                    demo_paths.append(str(f))
    demo = build_demographic_lookup(demo_paths)
    if demo:
        for idx in master.index:
            mob = str(master.at[idx, "Mobile_Clean"]).strip()
            d = demo.get(mob)
            if not d:
                continue
            if not str(master.at[idx, "Age"]).strip() and d["age"]:
                master.at[idx, "Age"] = d["age"]
            if not str(master.at[idx, "Sex"]).strip() and d["sex"]:
                master.at[idx, "Sex"] = d["sex"]
            if not str(master.at[idx, "Patient_Name"]).strip() and d["name"]:
                master.at[idx, "Patient_Name"] = d["name"]
            if not str(master.at[idx, "Patient_UID"]).strip() and d["uid"]:
                master.at[idx, "Patient_UID"] = d["uid"]
        stats["age_enriched"] = int((master["Age"].astype(str).str.strip() != "").sum())

    master = master[DIAG_COLS]
    master.to_csv(DIAG_FILE, index=False)

    # record source freshness metadata (as-of date: prefer explicit, else parse
    # the latest 'UPTO DD MMM YYYY' cutoff from the input filenames)
    src_names = [Path(p).name for p in paths]
    if not asof_date:
        for p in paths:
            a = parse_asof_from_filename(Path(p).name)
            if a and a > asof_date:
                asof_date = a
    try:
        write_diagnosis_meta(src_names, master, stats, asof_date)
    except Exception as _e:
        print(f"  ! could not write diagnosis meta: {_e}")
    return master, stats


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    print("Ingesting diagnosis sources ...")
    master, stats = ingest(args)
    print("\n── INGESTION SUMMARY ──────────────────────────────")
    print(f"  Files processed:        {stats['files']}")
    print(f"  Rows scanned:           {stats['rows']}")
    print(f"  Patients seeded (roster): {stats['seeded']}")
    print(f"  Rows with diagnosis:    {stats['with_diag']}")
    print(f"  New patients added:     {stats['new']}")
    print(f"  VIP flags captured:     {stats['vip']}")
    print(f"  Comorbidity rows:       {stats.get('comorbid', 0)}")
    print(f"  Age populated:          {stats.get('age_enriched', 0)}")
    print(f"  Discarded (junk):       {stats.get('discarded', 0)}")
    print(f"  Admin-code rows:        {stats['admin']}")
    print(f"  Master size now:        {len(master)}")
    print(f"  Saved -> {DIAG_FILE}")
