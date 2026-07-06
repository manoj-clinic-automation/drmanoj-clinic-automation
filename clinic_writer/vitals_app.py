#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
vitals_app.py  —  Dr. Manoj Agarwal Clinic  —  Track 1, Step 5 (the local front-end)

WHAT THIS IS (plain language)
-----------------------------
A small program that runs ONLY on the clinic PC. When you double-click
open_vitals.bat it starts quietly and opens a page in your browser at

        http://127.0.0.1:5057/vitals

On that page you:
   1. type a patient's Clinic ID  ->  it looks up the real patient from the
      tracker's local CSV files (shared-mobile pick-list if the number is shared),
   2. enter today's vitals + tick the plan choices (all pre-filled and editable),
   3. print the two sheets (patient + physio) as you already do,
   4. press "Save to records" -> this program calls the three PROVEN writer
      functions inside clinic_writer.py to:
         * append one row to vitals_ledger.csv   (write_vitals)
         * append one row to plan_ledger.csv     (write_plan)
         * file both printed sheets as PDFs       (archive_pdf)

WHAT IT DOES / DOES NOT DO
--------------------------
  * READS ONLY the tracker's two CSVs (patient_master.csv, patient_diagnosis.csv).
    It NEVER writes them.  (one-writer-per-file law — KB D126)
  * WRITES ONLY into D:\clinic_writer\ (the two ledgers + plan_archive\).
  * No internet. No Drive calls. No VPS. Purely local. Bound to 127.0.0.1 so it
    can only be reached from THIS PC (not the clinic Wi-Fi, not the internet).
  * The live follow-up tracker is NOT touched. It keeps running exactly as before.
  * Manual fallback (print from the browser, no save) always still works.

The heavy lifting (BMI maths, ID assignment, schemas, PDF) all lives in the
already-verified clinic_writer.py — this file only collects the form and calls it.
"""

import os
import sys
import csv
import json
import webbrowser
import threading

# --- where everything lives (edit ONLY these three lines if paths ever change) ---
# The tool + engine + outputs live on D: (survives a Windows reformat).
APP_DIR      = os.path.dirname(os.path.abspath(__file__))          # D:\clinic_writer
# The tracker's read-only source CSVs (on C:, where the tracker writes them).
DATA_DIR     = r"C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\data"
# Our own output home (on D:, beside this app).
OUT_DIR      = APP_DIR

MASTER_CSV   = os.path.join(DATA_DIR, "patient_master.csv")
DIAG_CSV     = os.path.join(DATA_DIR, "patient_diagnosis.csv")
VITALS_LEDGER= os.path.join(OUT_DIR, "vitals_ledger.csv")
PLAN_LEDGER  = os.path.join(OUT_DIR, "plan_ledger.csv")
ARCHIVE_ROOT = os.path.join(OUT_DIR, "plan_archive")
PAGE_HTML    = os.path.join(APP_DIR, "vitals_page.html")

PORT = 5057   # its own port (the tracker uses 5000; these never clash)

# --- import Flask (installed with: pip install flask) ---
try:
    from flask import Flask, request, jsonify, Response
except Exception:
    sys.stderr.write(
        "\nFlask is not installed. On the clinic PC run this once:\n"
        "    pip install flask\n\n")
    raise

# --- import the PROVEN engine sitting beside this file ---
try:
    import clinic_writer as CW
except Exception:
    sys.stderr.write(
        "\nCould not import clinic_writer.py. It must sit in the SAME folder as\n"
        "this file (D:\\clinic_writer\\clinic_writer.py).\n\n")
    raise

app = Flask(__name__)


# ----------------------------------------------------------------------------- #
#  READ-ONLY CSV helpers (never write the source files)
# ----------------------------------------------------------------------------- #

def _read_csv(path):
    """Read a CSV into a list of dicts. Returns [] if the file is missing."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _digits(s):
    return "".join(ch for ch in str(s or "") if ch.isdigit())


def _find_matches(clinic_id):
    """
    Resolve a Clinic ID to one-or-more patients (D123 shared-mobile pick-list).
    Joins patient_master (identity) + patient_diagnosis (age/sex/diagnosis) on
    Patient_UID. Returns a list of candidate dicts (usually 1; several if the same
    Clinic ID maps to several UIDs, which can happen with shared numbers).
    """
    cid = (clinic_id or "").strip()
    if not cid:
        return []
    master = _read_csv(MASTER_CSV)
    diag   = _read_csv(DIAG_CSV)

    # index diagnosis rows by UID (last one wins if duplicated)
    dbyuid = {}
    for d in diag:
        u = (d.get("Patient_UID") or "").strip()
        if u:
            dbyuid[u] = d

    out = []
    for m in master:
        if (m.get("Clinic_Specific_Id") or "").strip() != cid:
            continue
        uid = (m.get("Patient_UID") or "").strip()
        d = dbyuid.get(uid, {})
        out.append({
            "Patient_UID": uid,
            "Clinic_Specific_Id": cid,
            "Patient_Name": (m.get("Patient_Name") or d.get("Patient_Name") or "").strip(),
            "Mobile_Clean": (m.get("Mobile_Clean") or d.get("Mobile_Clean") or "").strip(),
            "Mobile_Duplicate_Count": (m.get("Mobile_Duplicate_Count") or "").strip(),
            "Age": (d.get("Age") or "").strip(),
            "Sex": (d.get("Sex") or "").strip(),
            "Standardized_Diagnosis": (d.get("Standardized_Diagnosis") or "").strip(),
            "Comorbidities": (d.get("Comorbidities") or "").strip(),
        })
    return out


# ----------------------------------------------------------------------------- #
#  ROUTES
# ----------------------------------------------------------------------------- #

@app.route("/vitals")
def page():
    """Serve the front-end page (the v25 plan-tool HTML + a Save bridge)."""
    if not os.path.exists(PAGE_HTML):
        return Response("vitals_page.html not found beside vitals_app.py", status=500)
    with open(PAGE_HTML, "r", encoding="utf-8") as f:
        return Response(f.read(), mimetype="text/html; charset=utf-8")


@app.route("/lookup")
def lookup():
    """Clinic ID -> candidate patient(s). Read-only. Returns JSON."""
    cid = request.args.get("clinic_id", "")
    try:
        return jsonify({"ok": True, "matches": _find_matches(cid)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/save", methods=["POST"])
def save():
    """
    Write one visit to records: vitals row + plan row + two archived PDFs.
    Body is JSON collected by the page. Calls the proven engine functions only.
    Returns the IDs assigned + the PDF paths, so the page can confirm on screen.
    """
    try:
        data = request.get_json(force=True) or {}

        # ---- 1) vitals row (engine computes BMI/category/ratio + assigns V-id) ----
        vrow = CW.write_vitals(VITALS_LEDGER, {
            "Patient_UID":        data.get("Patient_UID", ""),
            "Clinic_Specific_Id": data.get("Clinic_Specific_Id", ""),
            "Patient_Name":       data.get("Patient_Name", ""),
            "Measured_On":        data.get("Plan_Date", ""),
            "Age_At_Visit":       data.get("Age_At_Visit", ""),
            "Sex":                data.get("Sex", ""),
            "Height_cm":          data.get("Height_cm", ""),
            "Weight_kg":          data.get("Weight_kg", ""),
            "Waist_cm":           data.get("Waist_cm", ""),
            "BP_Systolic":        data.get("BP_Systolic", ""),
            "BP_Diastolic":       data.get("BP_Diastolic", ""),
            "Pulse_bpm":          data.get("Pulse_bpm", ""),
            "Note":               data.get("Note", ""),
        }, entered_by="owner", source_face="vitals-app")

        plan_date = vrow["Measured_On"]

        # ---- 2) plan row (engine assigns P-id, links the vitals id) ----
        prow = CW.write_plan(PLAN_LEDGER, {
            "Patient_UID":            data.get("Patient_UID", ""),
            "Clinic_Specific_Id":     data.get("Clinic_Specific_Id", ""),
            "Patient_Name":           data.get("Patient_Name", ""),
            "Plan_Date":              plan_date,
            "Conditions_Selected":    data.get("Conditions_Selected", ""),
            "Comorbidities_Selected": data.get("Comorbidities_Selected", ""),
            "Diet_Type":              data.get("Diet_Type", ""),
            "Sheets_Printed":         data.get("Sheets_Printed", "Patient; Physio"),
        }, vitals_id_used=vrow["Vitals_ID"], generated_by="owner")

        plan_id = prow["Plan_ID"]
        uid     = data.get("Patient_UID", "")
        cid     = data.get("Clinic_Specific_Id", "")
        mobile  = _digits(data.get("Mobile", ""))

        # ---- 3) archive both PDFs on the real UID folder + real Plan_ID ----
        pat_line = "%s  |  %s  |  %s" % (
            data.get("Patient_Name", ""), cid, plan_date)

        patient_sections = data.get("Patient_Sections") or []
        physio_sections  = data.get("Physio_Sections") or []

        pat_path = CW.plan_pdf_path(ARCHIVE_ROOT, "patient", uid, cid, mobile, plan_date, plan_id)
        phy_path = CW.plan_pdf_path(ARCHIVE_ROOT, "physio",  uid, cid, mobile, plan_date, plan_id)

        CW.archive_pdf(pat_path,
                       "Dr. Manoj Agarwal Clinic - Patient Plan",
                       pat_line,
                       [(h, l) for (h, l) in patient_sections])
        CW.archive_pdf(phy_path,
                       "Dr. Manoj Agarwal Clinic - Physio Sheet",
                       pat_line,
                       [(h, l) for (h, l) in physio_sections])

        # ---- 4) stamp the PDF paths back onto the plan row is NOT needed:
        #         write_plan already ran; we return paths for on-screen confirm.
        return jsonify({
            "ok": True,
            "vitals_id": vrow["Vitals_ID"],
            "plan_id": plan_id,
            "bmi": vrow["BMI"],
            "bmi_category": vrow["BMI_Category"],
            "patient_pdf": pat_path,
            "physio_pdf": phy_path,
            "new_patient": not bool((uid or "").strip()),
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/health")
def health():
    """Tiny liveness check used by the menu page."""
    return jsonify({
        "ok": True,
        "data_dir_found": os.path.isdir(DATA_DIR),
        "master_found": os.path.exists(MASTER_CSV),
        "diag_found": os.path.exists(DIAG_CSV),
        "out_dir": OUT_DIR,
    })


# ----------------------------------------------------------------------------- #
#  START
# ----------------------------------------------------------------------------- #

def _open_browser():
    try:
        webbrowser.open("http://127.0.0.1:%d/vitals" % PORT)
    except Exception:
        pass


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        # Offline check: engine imports, routes registered, paths resolve.
        print("vitals_app self-test")
        print("  engine imported     :", hasattr(CW, "write_vitals")
              and hasattr(CW, "write_plan") and hasattr(CW, "archive_pdf"))
        print("  DATA_DIR            :", DATA_DIR)
        print("  OUT_DIR             :", OUT_DIR)
        print("  page html present   :", os.path.exists(PAGE_HTML))
        routes = sorted(r.rule for r in app.url_map.iter_rules())
        print("  routes              :", ", ".join(routes))
        sys.exit(0)

    os.makedirs(OUT_DIR, exist_ok=True)
    # open the browser a moment after the server starts
    threading.Timer(1.2, _open_browser).start()
    # 127.0.0.1 only = reachable from THIS PC alone (safe)
    app.run(host="127.0.0.1", port=PORT, debug=False)
