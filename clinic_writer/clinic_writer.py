#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
clinic_writer.py  —  Dr. Manoj Agarwal Clinic  —  PC-LOCAL single writer (Track 1, Step 4)

WHAT THIS IS (plain language)
-----------------------------
One small program that runs on the CLINIC PC. It does three jobs, and nothing else:

  1. VITALS WRITER  — appends one row to vitals_ledger.csv. It computes BMI, BMI
     category (Indian cut-offs) and waist:height for EVERY row itself, and assigns
     the next Vitals_ID. (KB D127 / D131)

  2. PLAN WRITER    — appends one row to plan_ledger.csv. It assigns the next
     Plan_ID and links the same-visit Vitals_ID_Used. (KB D126 / D134)

  3. PDF ARCHIVE    — saves a frozen PDF of a printed sheet into plan_archive/,
     filed on the patient (KB D132). Text-faithful PDF via reportlab.

DESIGN RULES IT OBEYS
---------------------
  * ONE WRITER PER FILE. This module is the only thing that writes the two ledgers
    and the PDF archive. It NEVER writes patient_master.csv / patient_diagnosis.csv
    (those are read-only, tracker-owned). (KB D126 / one-writer-per-file)
  * Patient_UID is the join key; Clinic_Specific_Id is the human handle. (KB D128)
  * Locked schemas: vitals_ledger = 20 cols, plan_ledger = 14 cols. Column order is
    frozen and matches the plan-tool (v26) byte-for-byte. (KB §67.3 / D134)
  * BMI maths mirrors the plan-tool's compute(): BMI = W / (H/100)^2, rounded to 1dp;
    Indian categories <18.5 / <23 / <27.5 / else; waist:height = round(waist/H,2). (v26)
  * IST timestamps stamped explicitly (TZ-independent), same format as the tool.
  * Append-only. Never rewrites or deletes existing rows.

WHAT IT DOES NOT DO
-------------------
  * No network. No Drive calls. No VPS. Purely local files. (Drive sync is Google
    Drive's own job on the folders; this writer just writes to disk.)
  * No staff BP page (retired this session — only the doctor enters vitals).
  * Does not host a web server. This is the WRITE-PATH library + a CLI for testing.
    The hosting front-end (Step 5) will import these functions.

USAGE
-----
    python clinic_writer.py --selftest
        Runs the built-in behaviour test against synthetic data in ./test_data
        (real headers, no real patient data). Proves the whole path end to end.

    (imported)  from clinic_writer import write_vitals, write_plan, archive_pdf
"""

import os
import csv
import io
import re
import sys
import json
import datetime

# ----------------------------------------------------------------------------- #
#  LOCKED SCHEMAS  (must match plan-tool v26 exactly — KB §67.3 / D134)
# ----------------------------------------------------------------------------- #

VITALS_COLS = [
    "Vitals_ID", "Patient_UID", "Clinic_Specific_Id", "Patient_Name", "Measured_On",
    "Age_At_Visit", "Sex", "Height_cm", "Weight_kg", "BMI", "BMI_Category", "Waist_cm",
    "Waist_Height_Ratio", "BP_Systolic", "BP_Diastolic", "Pulse_bpm", "Entered_By",
    "Source_Face", "Written_At", "Note",
]

PLAN_COLS = [
    "Plan_ID", "Patient_UID", "Clinic_Specific_Id", "Patient_Name", "Plan_Date",
    "Conditions_Selected", "Comorbidities_Selected", "Diet_Type", "Vitals_ID_Used",
    "Sheets_Printed", "Plan_PDF_Patient", "Plan_PDF_Physio", "Generated_By", "Written_At",
]

# ID formats:  V-YYYY-NNNNNN  and  P-YYYY-NNNNNN  (per-year running counter, zero-padded)
VITALS_ID_PREFIX = "V"
PLAN_ID_PREFIX = "P"
ID_PAD = 6


# ----------------------------------------------------------------------------- #
#  TIME  (IST, stamped explicitly — matches the tool's vitNowIST / vitDateOnly)
# ----------------------------------------------------------------------------- #

_IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def now_ist_iso():
    """2026-07-05T14:09:33+05:30 — same shape the plan-tool writes."""
    return datetime.datetime.now(_IST).strftime("%Y-%m-%dT%H:%M:%S+05:30")


def today_ist_date():
    """YYYY-MM-DD in IST."""
    return datetime.datetime.now(_IST).strftime("%Y-%m-%d")


def _year_of(date_str):
    """Year prefix from a YYYY-MM-DD string; falls back to current IST year."""
    s = (date_str or "").strip()
    if len(s) >= 4 and s[:4].isdigit():
        return s[:4]
    return datetime.datetime.now(_IST).strftime("%Y")


# ----------------------------------------------------------------------------- #
#  NUMBERS  (BMI / category / ratio — mirrors the tool's compute() exactly)
# ----------------------------------------------------------------------------- #

def _to_num(v):
    """Best-effort number from a cell; returns None if not a clean positive number."""
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    try:
        n = float(s)
    except (ValueError, TypeError):
        return None
    return n


def _round1(n):
    """Round to 1 decimal, matching JS r1 (round to 1dp)."""
    return round(n + 1e-9, 1)


def compute_bmi(height_cm, weight_kg):
    """BMI = W / (H/100)^2, 1dp. Returns None if either missing/invalid."""
    h = _to_num(height_cm)
    w = _to_num(weight_kg)
    if not h or not w or h <= 0:
        return None
    return _round1(w / ((h / 100.0) ** 2))


def bmi_category(bmi):
    """Indian cut-offs — identical to the tool: <18.5 / <23 / <27.5 / else."""
    if bmi is None:
        return ""
    if bmi < 18.5:
        return "Underweight"
    if bmi < 23:
        return "Normal"
    if bmi < 27.5:
        return "Overweight"
    return "Obese"


def waist_height_ratio(waist_cm, height_cm):
    """round(waist/height, 2) — matches the tool. None if either missing."""
    waist = _to_num(waist_cm)
    h = _to_num(height_cm)
    if not waist or not h or h <= 0:
        return None
    return round((waist / h) + 1e-9, 2)


# ----------------------------------------------------------------------------- #
#  CSV LEDGER HELPERS  (append-only; header written once; ID assignment)
# ----------------------------------------------------------------------------- #

def _read_existing_ids(path, id_col):
    """Return the set of existing IDs in an existing ledger (empty if no file)."""
    ids = set()
    if not os.path.exists(path):
        return ids
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                v = (row.get(id_col) or "").strip()
                if v:
                    ids.add(v)
    except Exception:
        # A readable ledger is required to assign the next ID safely; re-raise so
        # the caller (and the doctor) sees the real problem rather than silently
        # duplicating an ID.
        raise
    return ids


def _next_id(existing_ids, prefix, year):
    """Next running ID for this year: PREFIX-YEAR-000001, skipping any used ones."""
    pat = re.compile(r"^%s-%s-(\d+)$" % (re.escape(prefix), re.escape(year)))
    max_n = 0
    for v in existing_ids:
        m = pat.match(v)
        if m:
            n = int(m.group(1))
            if n > max_n:
                max_n = n
    return "%s-%s-%0*d" % (prefix, year, ID_PAD, max_n + 1)


def _append_row(path, cols, row_dict):
    """Append one dict as a CSV row in locked column order; write header if new."""
    new_file = not os.path.exists(path) or os.path.getsize(path) == 0
    # Ensure the target directory exists (local disk only).
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        if new_file:
            w.writeheader()
        # Normalise: every column present, everything stringified, None -> "".
        clean = {}
        for c in cols:
            val = row_dict.get(c, "")
            clean[c] = "" if val is None else str(val)
        w.writerow(clean)


# ----------------------------------------------------------------------------- #
#  READ-ONLY LOOKUP  (resolve Clinic_Specific_Id -> Patient_UID from the two CSVs)
#  NEVER writes these files. Newest-by-date rule is applied by the caller passing
#  the resolved paths; here we just read what we're given. (KB D122 / D128)
# ----------------------------------------------------------------------------- #

def lookup_uid_by_clinic_id(master_csv_path, clinic_id):
    """
    Resolve a Clinic_Specific_Id to a Patient_UID using patient_master.csv (read-only).
    Returns (uid, name) or (None, None) if not found. Shared-mobile disambiguation
    lives in the front-end (D123); this is the plain ID->UID resolve.
    """
    cid = (clinic_id or "").strip()
    if not cid or not os.path.exists(master_csv_path):
        return (None, None)
    with open(master_csv_path, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            if (row.get("Clinic_Specific_Id") or "").strip() == cid:
                return ((row.get("Patient_UID") or "").strip(),
                        (row.get("Patient_Name") or "").strip())
    return (None, None)


# ----------------------------------------------------------------------------- #
#  1) VITALS WRITER
# ----------------------------------------------------------------------------- #

def write_vitals(vitals_ledger_path, data, entered_by="owner", source_face="plan-tool"):
    """
    Append one vitals row. Computes BMI / category / ratio HERE (never trusts caller),
    assigns the next Vitals_ID, stamps IST. Returns the full row dict actually written.

    `data` keys accepted (all optional except a patient handle):
      Patient_UID, Clinic_Specific_Id, Patient_Name, Measured_On, Age_At_Visit, Sex,
      Height_cm, Weight_kg, Waist_cm, BP_Systolic, BP_Diastolic, Pulse_bpm, Note
    """
    measured_on = (data.get("Measured_On") or "").strip() or today_ist_date()
    year = _year_of(measured_on)

    existing = _read_existing_ids(vitals_ledger_path, "Vitals_ID")
    vid = _next_id(existing, VITALS_ID_PREFIX, year)

    height = data.get("Height_cm", "")
    weight = data.get("Weight_kg", "")
    waist = data.get("Waist_cm", "")

    bmi = compute_bmi(height, weight)
    cat = bmi_category(bmi)
    whr = waist_height_ratio(waist, height)

    # Sex normalised to M/F like the tool (Male->M, Female->F, else through/blank).
    sex_raw = (str(data.get("Sex", "")) or "").strip()
    if sex_raw in ("Male", "M", "m"):
        sex = "M"
    elif sex_raw in ("Female", "F", "f"):
        sex = "F"
    else:
        sex = ""

    row = {
        "Vitals_ID": vid,
        "Patient_UID": (data.get("Patient_UID") or "").strip(),
        "Clinic_Specific_Id": (data.get("Clinic_Specific_Id") or "").strip(),
        "Patient_Name": (data.get("Patient_Name") or "").strip(),
        "Measured_On": measured_on,
        "Age_At_Visit": (str(data.get("Age_At_Visit", "")) or "").strip(),
        "Sex": sex,
        "Height_cm": (str(height) or "").strip(),
        "Weight_kg": (str(weight) or "").strip(),
        "BMI": ("" if bmi is None else bmi),
        "BMI_Category": cat,
        "Waist_cm": (str(waist) or "").strip(),
        "Waist_Height_Ratio": ("" if whr is None else whr),
        "BP_Systolic": (str(data.get("BP_Systolic", "")) or "").strip(),
        "BP_Diastolic": (str(data.get("BP_Diastolic", "")) or "").strip(),
        "Pulse_bpm": (str(data.get("Pulse_bpm", "")) or "").strip(),
        "Entered_By": entered_by,
        "Source_Face": source_face,
        "Written_At": now_ist_iso(),
        "Note": (data.get("Note") or "").strip(),
    }
    _append_row(vitals_ledger_path, VITALS_COLS, row)
    return row


# ----------------------------------------------------------------------------- #
#  2) PLAN WRITER
# ----------------------------------------------------------------------------- #

def write_plan(plan_ledger_path, data, vitals_id_used="", generated_by="owner"):
    """
    Append one plan_ledger row. Assigns the next Plan_ID, links Vitals_ID_Used,
    stamps IST. Returns the full row dict actually written.

    `data` keys accepted:
      Patient_UID, Clinic_Specific_Id, Patient_Name, Plan_Date, Conditions_Selected,
      Comorbidities_Selected, Diet_Type, Sheets_Printed, Plan_PDF_Patient,
      Plan_PDF_Physio
    """
    plan_date = (data.get("Plan_Date") or "").strip() or today_ist_date()
    year = _year_of(plan_date)

    existing = _read_existing_ids(plan_ledger_path, "Plan_ID")
    pid = _next_id(existing, PLAN_ID_PREFIX, year)

    row = {
        "Plan_ID": pid,
        "Patient_UID": (data.get("Patient_UID") or "").strip(),
        "Clinic_Specific_Id": (data.get("Clinic_Specific_Id") or "").strip(),
        "Patient_Name": (data.get("Patient_Name") or "").strip(),
        "Plan_Date": plan_date,
        "Conditions_Selected": (data.get("Conditions_Selected") or "").strip(),
        "Comorbidities_Selected": (data.get("Comorbidities_Selected") or "").strip(),
        "Diet_Type": (data.get("Diet_Type") or "").strip(),
        "Vitals_ID_Used": (vitals_id_used or "").strip(),
        "Sheets_Printed": (data.get("Sheets_Printed") or "").strip(),
        "Plan_PDF_Patient": (data.get("Plan_PDF_Patient") or "").strip(),
        "Plan_PDF_Physio": (data.get("Plan_PDF_Physio") or "").strip(),
        "Generated_By": generated_by,
        "Written_At": now_ist_iso(),
    }
    _append_row(plan_ledger_path, PLAN_COLS, row)
    return row


# ----------------------------------------------------------------------------- #
#  3) PDF ARCHIVE  (reportlab; text-faithful; filed on the patient — KB D132)
# ----------------------------------------------------------------------------- #

def plan_pdf_path(archive_root, which, patient_uid, clinic_id, mobile, plan_date, plan_id):
    """
    Build the D132 archive path for one sheet ('patient' or 'physio').
      real UID:  plan_archive/<year>/<Patient_UID>/<Plan_Date>_<Plan_ID>_<which>.pdf
      new pt:    plan_archive/pending/<Clinic_Id>_<mobile>/<Plan_Date>_<Plan_ID>_<which>.pdf
    """
    year = _year_of(plan_date)
    if (patient_uid or "").strip():
        folder = os.path.join(archive_root, year, patient_uid.strip())
    else:
        stub = "%s_%s" % ((clinic_id or "NA").strip() or "NA",
                          (mobile or "NA").strip() or "NA")
        folder = os.path.join(archive_root, "pending", stub)
    fname = "%s_%s_%s.pdf" % ((plan_date or "").strip(), (plan_id or "").strip(), which)
    return os.path.join(folder, fname)


def archive_pdf(out_path, title, patient_line, sections):
    """
    Render a text-faithful archive PDF with reportlab and save it to out_path.
    Creates parent folders as needed. Returns out_path.

      title         : top heading (e.g. clinic name / sheet type)
      patient_line  : one line of patient identity (name / id / date)
      sections      : list of (heading, [lines...]) tuples — the sheet content

    reportlab is a pure-Python dependency (pip install reportlab). No system
    libraries, so it is durable on Windows. (Chosen this session.)
    """
    # Imported here so the ledger writers work even on a machine without reportlab
    # (e.g. if only the CSV path is being exercised). PDF archiving needs it.
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, HRFlowable)
    from reportlab.lib.enums import TA_LEFT

    d = os.path.dirname(os.path.abspath(out_path))
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

    # --- Hindi (Devanagari) support -------------------------------------------
    # The patient/physio sheets are Hindi-first. reportlab's built-in fonts cannot
    # draw Devanagari, so we register NotoSansDevanagari-Regular.ttf if it sits
    # beside this module. If the font file is missing we fall back to Helvetica
    # (English still renders; Hindi would show as boxes) so archiving never fails.
    # English text uses Helvetica (built in). Hindi (Devanagari) RUNS inside a line
    # are wrapped in <font name="NotoDev"> by _mixed() below, drawn with the Noto
    # Devanagari TTF if it sits beside this module. This renders BOTH scripts in the
    # same line. If the font file is missing, Hindi shows as boxes but English (and
    # the whole archive) still works — archiving never fails on a font issue.
    base_font = "Helvetica"
    hindi_ok = False
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        _here = os.path.dirname(os.path.abspath(__file__))
        _font_path = os.path.join(_here, "NotoSansDevanagari-Regular.ttf")
        if os.path.exists(_font_path):
            if "NotoDev" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("NotoDev", _font_path))
            hindi_ok = True
    except Exception:
        hindi_ok = False

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=15, spaceAfter=4,
                        fontName=base_font)
    sub = ParagraphStyle("sub", parent=styles["Normal"], fontSize=9,
                         textColor="#555555", spaceAfter=8, fontName=base_font)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=11.5,
                        spaceBefore=8, spaceAfter=3, fontName=base_font)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=9.5,
                          leading=13, alignment=TA_LEFT, fontName=base_font)

    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=16 * mm, rightMargin=16 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm,
        title=title,
    )
    flow = []
    flow.append(Paragraph(_mixed(title, hindi_ok), h1))
    if patient_line:
        flow.append(Paragraph(_mixed(patient_line, hindi_ok), sub))
    flow.append(HRFlowable(width="100%", thickness=0.6, color="#cccccc"))
    flow.append(Spacer(1, 4))
    for heading, lines in (sections or []):
        if heading:
            flow.append(Paragraph(_mixed(heading, hindi_ok), h2))
        for ln in (lines or []):
            flow.append(Paragraph(_mixed(ln, hindi_ok), body))
    doc.build(flow)
    return out_path


def _esc(s):
    """Escape the few characters reportlab's mini-markup treats specially."""
    s = "" if s is None else str(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


_DEV_RE = re.compile(r'([\u0900-\u097F][\u0900-\u097F\u0020\u200d\u0964\u0965]*)')

def _mixed(s, hindi_ok=True):
    """
    Build a reportlab mini-markup string that renders BOTH English and Hindi in one
    line: Devanagari runs are wrapped in <font name="NotoDev">, everything else stays
    in the base (Helvetica) font. Each piece is escaped. If hindi_ok is False (no
    font file) the text is still returned escaped (Hindi would show as boxes, English
    fine). This is why numbers-only worked before but English words did not: the
    Devanagari-only font lacked Latin letters. (Session 91 fix.)
    """
    s = "" if s is None else str(s)
    parts = re.split(r'([\u0900-\u097F][\u0900-\u097F\u0020\u200d\u0964\u0965]*)', s)
    out = []
    for part in parts:
        if not part:
            continue
        is_dev = any('\u0900' <= c <= '\u097F' for c in part)
        esc = part.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if is_dev and hindi_ok:
            out.append('<font name="NotoDev">' + esc + '</font>')
        else:
            out.append(esc)
    return "".join(out)


# ----------------------------------------------------------------------------- #
#  BUILT-IN BEHAVIOUR TEST  (synthetic data only — real headers, no real patients)
# ----------------------------------------------------------------------------- #

def _selftest():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")
    os.makedirs(base, exist_ok=True)
    master = os.path.join(base, "patient_master.csv")
    vled = os.path.join(base, "vitals_ledger.csv")
    pled = os.path.join(base, "plan_ledger.csv")
    arch = os.path.join(base, "plan_archive")

    # Fresh run each time so results are deterministic.
    for p in (vled, pled):
        if os.path.exists(p):
            os.remove(p)

    # Synthetic master (real headers from KB §66.1; fake identities).
    with open(master, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Patient_UID", "Clinic_Specific_Id", "Patient_Name", "Mobile_Raw",
                    "Mobile_Clean", "Mobile_Status", "First_Seen_Date", "Last_Seen_Date",
                    "Mobile_Duplicate_Count", "Identity_Status", "Added_From", "Last_Updated"])
        w.writerow(["TESTA10001", "CID-9001", "Test Patient One", "", "9990000001", "ok",
                    "2026-01-01", "2026-07-01", "1", "active", "synthetic", "2026-07-01"])

    results = []

    def check(label, cond):
        results.append((label, bool(cond)))

    # --- 1. lookup resolves clinic id -> uid ---
    uid, name = lookup_uid_by_clinic_id(master, "CID-9001")
    check("lookup: CID-9001 -> TESTA10001", uid == "TESTA10001" and name == "Test Patient One")
    uid_miss, _ = lookup_uid_by_clinic_id(master, "CID-DOES-NOT-EXIST")
    check("lookup: missing id -> None", uid_miss is None)

    # --- 2. vitals write (established patient) computes BMI/cat/ratio + assigns V-id ---
    v1 = write_vitals(vled, {
        "Patient_UID": uid, "Clinic_Specific_Id": "CID-9001",
        "Patient_Name": name, "Measured_On": "2026-07-05",
        "Age_At_Visit": "61", "Sex": "Male",
        "Height_cm": "170", "Weight_kg": "82", "Waist_cm": "102",
        "BP_Systolic": "138", "BP_Diastolic": "86", "Pulse_bpm": "78",
    })
    # BMI = 82 / (1.70^2) = 28.37... -> 28.4 ; category Obese ; whr = 102/170 = 0.6
    check("vitals: BMI computed 28.4", v1["BMI"] == 28.4)
    check("vitals: category Obese", v1["BMI_Category"] == "Obese")
    check("vitals: waist:height 0.6", v1["Waist_Height_Ratio"] == 0.6)
    check("vitals: sex normalised M", v1["Sex"] == "M")
    check("vitals: Vitals_ID V-2026-000001", v1["Vitals_ID"] == "V-2026-000001")
    check("vitals: 20 columns", set(v1.keys()) == set(VITALS_COLS))

    # --- 3. second vitals row increments the ID ---
    v2 = write_vitals(vled, {
        "Patient_UID": uid, "Clinic_Specific_Id": "CID-9001",
        "Patient_Name": name, "Measured_On": "2026-07-05",
        "Height_cm": "170", "Weight_kg": "80",
    })
    check("vitals: 2nd id V-2026-000002", v2["Vitals_ID"] == "V-2026-000002")

    # --- 4. missing height/weight -> blank BMI, still a valid row ---
    v3 = write_vitals(vled, {
        "Clinic_Specific_Id": "CID-9001", "Patient_Name": name,
        "Measured_On": "2026-07-05", "Weight_kg": "80",  # no height
    })
    check("vitals: missing height -> blank BMI", v3["BMI"] == "" and v3["BMI_Category"] == "")

    # --- 5. plan write assigns P-id, links vitals id ---
    p1 = write_plan(pled, {
        "Patient_UID": uid, "Clinic_Specific_Id": "CID-9001", "Patient_Name": name,
        "Plan_Date": "2026-07-05",
        "Conditions_Selected": "Knee OA [Standard/Moderate]",
        "Comorbidities_Selected": "Diabetes; Hypertension",
        "Diet_Type": "Egg+Veg", "Sheets_Printed": "Patient; Physio",
    }, vitals_id_used=v1["Vitals_ID"])
    check("plan: Plan_ID P-2026-000001", p1["Plan_ID"] == "P-2026-000001")
    check("plan: Vitals_ID_Used linked", p1["Vitals_ID_Used"] == "V-2026-000001")
    check("plan: 14 columns", set(p1.keys()) == set(PLAN_COLS))

    # --- 6. PDF path building: established patient vs new patient ---
    established = plan_pdf_path(arch, "patient", "TESTA10001", "CID-9001",
                               "9990000001", "2026-07-05", "P-2026-000001")
    check("pdf path: real UID folder",
          established.endswith(os.path.join("2026", "TESTA10001",
                                            "2026-07-05_P-2026-000001_patient.pdf")))
    newpt = plan_pdf_path(arch, "physio", "", "CID-NEW", "9995550000",
                          "2026-07-05", "P-2026-000002")
    check("pdf path: pending bucket for new patient",
          os.path.join("pending", "CID-NEW_9995550000") in newpt)

    # --- 7. actually generate a PDF and confirm it exists + is non-trivial ---
    made = archive_pdf(
        established,
        title="Advanced Orthopedic Surgery Centre — Patient Sheet",
        patient_line="Test Patient One  |  CID-9001  |  2026-07-05",
        sections=[
            ("Conditions", ["Knee OA [Standard/Moderate]"]),
            ("Home Exercises", ["Quadriceps Set — 10 reps x 2 sets",
                                "Straight Leg Raise — 10 reps x 2 sets"]),
            ("Nutrition", ["Protein target as advised.", "Weight loss is the key lever."]),
        ],
    )
    check("pdf: file created", os.path.exists(made))
    check("pdf: non-trivial size", os.path.exists(made) and os.path.getsize(made) > 1200)
    # confirm it's a real PDF (magic header)
    ok_magic = False
    if os.path.exists(made):
        with open(made, "rb") as fh:
            ok_magic = fh.read(5) == b"%PDF-"
    check("pdf: valid %PDF- header", ok_magic)

    # --- 8. ledgers are readable back with locked headers in order ---
    with open(vled, "r", encoding="utf-8", newline="") as f:
        vhead = next(csv.reader(f))
    check("ledger: vitals header == locked order", vhead == VITALS_COLS)
    with open(pled, "r", encoding="utf-8", newline="") as f:
        phead = next(csv.reader(f))
    check("ledger: plan header == locked order", phead == PLAN_COLS)

    # --- report ---
    print("\n=== clinic_writer.py self-test ===")
    passed = 0
    for label, ok in results:
        print(("  PASS  " if ok else "  FAIL  ") + label)
        if ok:
            passed += 1
    print("----------------------------------")
    print("  %d / %d checks passed" % (passed, len(results)))
    print("  test artifacts in: %s" % base)
    return passed == len(results)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = _selftest()
        sys.exit(0 if ok else 1)
    print(__doc__)
    print("Run:  python clinic_writer.py --selftest")
