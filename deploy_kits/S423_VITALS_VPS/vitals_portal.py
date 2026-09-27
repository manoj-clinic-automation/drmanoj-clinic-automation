#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vitals_portal.py -- kit S423_VITALS_VPS (session 284, 27-Sep-2026) -- F-598 / D589: Vitals & Plan on the server.

WHAT THIS IS
  The clinic PC's Vitals & Plan tool (D:\\clinic_writer: vitals_app.py + clinic_writer.py + vitals_page.html),
  moved onto the portal the way the Surgical Case Pack was (S172): the SAME page, byte for byte, the SAME
  proven engine (clinic_writer.py, unchanged), the SAME two ledgers and the SAME PDF archive layout -- now on
  the server's disk, reachable from the phone. The PC copy stays exactly where it is as the fallback.

  The only two differences, both forced by where it now lives:
    * the page asks /portal/vitals/lookup and /portal/vitals/save instead of /lookup and /save
      (rewritten as the page is served, so the page file itself is the PC's own bytes);
    * the patient lookup reads the server's own two patient stores, exactly as the Case Pack does:
      finance.db patient_ref (the Docterz patient master) and console.db patients (UID, age, sex,
      diagnosis) -- READ-ONLY, instead of the tracker CSVs on the clinic PC's C: drive.

WHERE THINGS LIVE
  /root/portal/vitals_portal.py        this file (code)
  /root/portal/clinic_writer.py        the engine, unchanged from the PC (0ad6d9f4)
  /root/portal/NotoSansDevanagari-Regular.ttf   the Hindi font the engine's PDFs use (beside the engine)
  /root/wa/vitals/                     PHI store, 0700 -- never in the repository:
      vitals_page.html                 the PC's page (fcedae30), served with two URLs rewritten
      vitals_ledger.csv  plan_ledger.csv   the two ledgers (the PC's 14 + 14 rows imported once)
      plan_archive/<year>/<UID>/...pdf     the archived sheets

ACCESS  Owner-only: the portal passes the Case Pack's own gate (doctor, in PORTAL_CASEPACK_USERS).
"""
import csv
import json
import os
import sqlite3

import clinic_writer as CW

VITALS_DIR = os.environ.get("PORTAL_VITALS_DIR", "/root/wa/vitals")
CONSOLE_DB = os.environ.get("PORTAL_CONSOLE_DB", "/root/wa/console.db")
FINANCE_DB = os.environ.get("PORTAL_FINANCE_DB", "/root/finance/finance.db")
PAGE_HTML = os.path.join(VITALS_DIR, "vitals_page.html")
VITALS_LEDGER = os.path.join(VITALS_DIR, "vitals_ledger.csv")
PLAN_LEDGER = os.path.join(VITALS_DIR, "plan_ledger.csv")
ARCHIVE_ROOT = os.path.join(VITALS_DIR, "plan_archive")
SOURCE_FACE = "vitals-vps"

# the two calls the PC page makes, and where they go on the server
URL_REWRITES = (('fetch("/lookup?', 'fetch("/portal/vitals/lookup?'),
                ('fetch("/save",', 'fetch("/portal/vitals/save",'))


def _digits(s):
    return "".join(ch for ch in str(s or "") if ch.isdigit())


def _ro(path):
    if not os.path.exists(path):
        raise RuntimeError("%s not found" % os.path.basename(path))
    con = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    return con


def find_matches(clinic_id, finance_db=None, console_db=None):
    """Clinic ID -> the candidate patients, in the shape the page's pick-list expects.
    Console rows carry the UID, age, sex and diagnosis; master rows carry the name and (when the column exists)
    the mobile. Several UIDs on one Clinic ID -> several matches, never an automatic pick (D123)."""
    cid = (clinic_id or "").strip()
    if not cid:
        return []
    console, master, errors = [], [], []
    try:
        con = _ro(console_db or CONSOLE_DB)
        try:
            console = [dict(r) for r in con.execute(
                "SELECT patient_uid, name, phone10, age, gender, diagnosis FROM patients WHERE clinic_id=?", (cid,))]
            for r in console:
                p = _digits(r.get("phone10"))
                r["_dup"] = con.execute("SELECT COUNT(*) FROM patients WHERE phone10=?", (r.get("phone10"),)).fetchone()[0] if p else 0
        finally:
            con.close()
    except Exception as e:  # noqa: BLE001
        errors.append("console: %s" % e)
    try:
        con = _ro(finance_db or FINANCE_DB)
        try:
            cols = {r[1] for r in con.execute("PRAGMA table_info(patient_ref)")}
            mob = "mobile" if "mobile" in cols else "''"
            master = [dict(r) for r in con.execute(
                "SELECT name, COALESCE(%s,'') AS mob FROM patient_ref WHERE clinic_id=? AND merged_into IS NULL" % mob, (cid,))]
        finally:
            con.close()
    except Exception as e:  # noqa: BLE001
        errors.append("master: %s" % e)
    if len(errors) == 2:
        raise RuntimeError("both patient stores failed -- " + " · ".join(errors))
    out = []
    mname = (master[0]["name"] or "").strip() if master else ""
    mmob = _digits(master[0]["mob"]) if master else ""
    for r in console:
        out.append({"Patient_UID": (r.get("patient_uid") or "").strip(),
                    "Clinic_Specific_Id": cid,
                    "Patient_Name": (r.get("name") or mname or "").strip(),
                    "Mobile_Clean": _digits(r.get("phone10")) or mmob,
                    "Mobile_Duplicate_Count": str(r.get("_dup") or ""),
                    "Age": str(r.get("age") or "").strip(),
                    "Sex": str(r.get("gender") or "").strip(),
                    "Standardized_Diagnosis": str(r.get("diagnosis") or "").strip(),
                    "Comorbidities": ""})
    if not out:
        for m in master:
            out.append({"Patient_UID": "", "Clinic_Specific_Id": cid,
                        "Patient_Name": (m.get("name") or "").strip(), "Mobile_Clean": _digits(m.get("mob")),
                        "Mobile_Duplicate_Count": "", "Age": "", "Sex": "", "Standardized_Diagnosis": "",
                        "Comorbidities": ""})
    return out


def save_visit(data, entered_by):
    """The PC tool's /save, step for step, on the server's paths. Returns the same JSON the page reads."""
    os.makedirs(VITALS_DIR, mode=0o700, exist_ok=True)
    vrow = CW.write_vitals(VITALS_LEDGER, {
        "Patient_UID": data.get("Patient_UID", ""), "Clinic_Specific_Id": data.get("Clinic_Specific_Id", ""),
        "Patient_Name": data.get("Patient_Name", ""), "Measured_On": data.get("Plan_Date", ""),
        "Age_At_Visit": data.get("Age_At_Visit", ""), "Sex": data.get("Sex", ""),
        "Height_cm": data.get("Height_cm", ""), "Weight_kg": data.get("Weight_kg", ""),
        "Waist_cm": data.get("Waist_cm", ""), "BP_Systolic": data.get("BP_Systolic", ""),
        "BP_Diastolic": data.get("BP_Diastolic", ""), "Pulse_bpm": data.get("Pulse_bpm", ""),
        "Note": data.get("Note", ""),
    }, entered_by=entered_by, source_face=SOURCE_FACE)
    plan_date = vrow["Measured_On"]
    prow = CW.write_plan(PLAN_LEDGER, {
        "Patient_UID": data.get("Patient_UID", ""), "Clinic_Specific_Id": data.get("Clinic_Specific_Id", ""),
        "Patient_Name": data.get("Patient_Name", ""), "Plan_Date": plan_date,
        "Conditions_Selected": data.get("Conditions_Selected", ""),
        "Comorbidities_Selected": data.get("Comorbidities_Selected", ""),
        "Diet_Type": data.get("Diet_Type", ""), "Sheets_Printed": data.get("Sheets_Printed", "Patient; Physio"),
    }, vitals_id_used=vrow["Vitals_ID"], generated_by=entered_by)
    plan_id = prow["Plan_ID"]
    uid, cid = data.get("Patient_UID", ""), data.get("Clinic_Specific_Id", "")
    mobile = _digits(data.get("Mobile", ""))
    pat_line = "%s  |  %s  |  %s" % (data.get("Patient_Name", ""), cid, plan_date)
    pat_path = CW.plan_pdf_path(ARCHIVE_ROOT, "patient", uid, cid, mobile, plan_date, plan_id)
    phy_path = CW.plan_pdf_path(ARCHIVE_ROOT, "physio", uid, cid, mobile, plan_date, plan_id)
    CW.archive_pdf(pat_path, "Dr. Manoj Agarwal Clinic - Patient Plan", pat_line,
                   [(h, l) for (h, l) in (data.get("Patient_Sections") or [])])
    CW.archive_pdf(phy_path, "Dr. Manoj Agarwal Clinic - Physio Sheet", pat_line,
                   [(h, l) for (h, l) in (data.get("Physio_Sections") or [])])
    return {"ok": True, "vitals_id": vrow["Vitals_ID"], "plan_id": plan_id, "bmi": vrow["BMI"],
            "bmi_category": vrow["BMI_Category"],
            "patient_pdf": os.path.relpath(pat_path, VITALS_DIR), "physio_pdf": os.path.relpath(phy_path, VITALS_DIR),
            "new_patient": not bool((uid or "").strip())}


def served_page():
    with open(PAGE_HTML, "r", encoding="utf-8") as fh:
        html = fh.read()
    for old, new in URL_REWRITES:
        if html.count(old) != 1:
            raise RuntimeError("the page does not carry the call %r exactly once -- not served" % old)
        html = html.replace(old, new)
    return html


def _rows(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def import_ledger(name, text):
    """ONE-TIME carry of the PC's ledger into the server's (so the ID counters continue). Refused unless the
    header is the engine's own and the server's ledger is still empty. Never overwrites a single row."""
    cols = {"vitals_ledger.csv": CW.VITALS_COLS, "plan_ledger.csv": CW.PLAN_COLS}.get(name)
    if not cols:
        return False, "unknown ledger"
    text = (text or "").replace("\r\n", "\n")
    lines = [l for l in text.split("\n") if l.strip()]
    if not lines or next(csv.reader([lines[0]])) != cols:
        return False, "the header is not the engine's own"
    target = os.path.join(VITALS_DIR, name)
    if _rows(target):
        return False, "the server's %s already has rows -- nothing imported" % name
    rows = list(csv.DictReader(lines))
    os.makedirs(VITALS_DIR, mode=0o700, exist_ok=True)
    tmp = target + ".tmp_import"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    os.chmod(tmp, 0o600)
    os.replace(tmp, target)
    return True, "%d row(s) imported" % len(rows)


def register(app, guard, get_user):
    from flask import request, jsonify, Response

    @app.route("/portal/vitals")
    @guard
    def vitals_page():
        try:
            return Response(served_page(), mimetype="text/html; charset=utf-8",
                            headers={"Cache-Control": "no-store"})
        except Exception as e:  # noqa: BLE001
            return Response("Vitals & Plan could not load its page: %s" % e, status=500)

    @app.route("/portal/vitals/lookup")
    @guard
    def vitals_lookup():
        try:
            return jsonify({"ok": True, "matches": find_matches(request.args.get("clinic_id", ""))})
        except Exception as e:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/vitals/save", methods=["POST"])
    @guard
    def vitals_save():
        try:
            return jsonify(save_visit(request.get_json(force=True) or {}, get_user() or "owner"))
        except Exception as e:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/vitals/import", methods=["POST"])
    @guard
    def vitals_import():
        b = request.get_json(force=True) or {}
        ok, msg = import_ledger(str(b.get("name") or ""), str(b.get("text") or ""))
        return jsonify({"ok": ok, "msg": msg}), (200 if ok else 409)

    @app.route("/portal/vitals/health")
    @guard
    def vitals_health():
        return jsonify({"ok": True, "page": os.path.exists(PAGE_HTML), "vitals_rows": len(_rows(VITALS_LEDGER)),
                        "plan_rows": len(_rows(PLAN_LEDGER)),
                        "pdfs": sum(len(f) for _, _, f in os.walk(ARCHIVE_ROOT)) if os.path.isdir(ARCHIVE_ROOT) else 0})
