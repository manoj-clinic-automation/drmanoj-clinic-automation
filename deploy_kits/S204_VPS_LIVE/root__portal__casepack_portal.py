#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
casepack_portal.py — Surgical Case Pack, VPS edition (S172)
============================================================
The clinic-PC casepack tool (casepack_app_NEW_lifecycle.py, pinned
478fd1493d019b684b70a0af70021ee4) ported to live INSIDE the doctor portal.

WHAT CHANGED vs the PC tool (plain language)
--------------------------------------------
1. Lives at /portal/casepack behind the portal's own login (owner-only
   guard supplied by portal.py). No new password, no new service.
2. Patient search now reads the VPS `console.db` `patients` table
   (READ-ONLY, mode=ro) — the nightly Patient_Master mirror that the
   console cron refreshes every 10 minutes. No more PC CSVs.
3. Everything it WRITES stays under /root/wa/casepack/ :
        case_ledger.csv                        (append-only ledger)
        case_archive/YYYY/<folder>/..._bundle_vN_date.json
        case_archive/YYYY/<folder>/..._consent_vN_date.html
   This module is the SOLE writer of that store (D235). PHI — the
   folder is gitignored, never in a repo or kit (F-31/F-49).
4. The lifecycle logic (versioned saves onto a case_ref, /cases list,
   /case/<id> recall) is ported VERBATIM from the PC app.

WIRING
------
portal.py calls  register(app, guard, get_user)  where
  guard    = the portal's owner-only decorator (auth stays in portal.py),
  get_user = zero-arg callable returning the logged-in username for the
             ledger's Generated_By column.
If console.db is absent/unreadable the search FAILS LOUD (ok:False +
plain-language error) — never a silent empty list (D236).
"""

import os, csv, json, re, sqlite3
from datetime import datetime, timezone, timedelta

# --- where everything lives (env-overridable, defaults match /root/wa) ------
CASEPACK_DIR = os.environ.get("PORTAL_CASEPACK_DIR",
                              "/root/wa/casepack")
CONSOLE_DB   = os.environ.get("PORTAL_CONSOLE_DB",
                              "/root/wa/console.db")

CASE_LEDGER = os.path.join(CASEPACK_DIR, "case_ledger.csv")
ARCHIVE     = os.path.join(CASEPACK_DIR, "case_archive")
PAGE_HTML   = os.path.join(CASEPACK_DIR, "casepack_page.html")

IST = timezone(timedelta(hours=5, minutes=30))

LEDGER_COLS = ["Case_ID","Patient_UID","Clinic_Specific_Id","Patient_Name","Case_Date",
               "Consent_Procedure","OT_Tier","OT_Procedure","Estimate_Title","Estimate_Total",
               "Bundle_File","Consent_File","Generated_By","Written_At"]

# --------------------------- read-only helpers ------------------------------ #
def _read_csv(path):
    if not os.path.exists(path): return []
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def _digits(s): return "".join(ch for ch in str(s or "") if ch.isdigit())

def _patients():
    """Load the patients table from console.db, READ-ONLY. Raises with a
    plain-language message if the db or table is not there (fail loud, D236)."""
    if not os.path.exists(CONSOLE_DB):
        raise RuntimeError("patient list unavailable — console.db not found "
                           "(the console cron builds it every 10 minutes)")
    conn = sqlite3.connect("file:%s?mode=ro" % CONSOLE_DB, uri=True)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT phone10, name, diagnosis, age, gender, last_visit, "
            "patient_uid, clinic_id FROM patients").fetchall()
    finally:
        conn.close()
    return rows

def _search(q):
    q = (q or "").strip()
    if len(q) < 2: return []
    ql = q.lower(); qd = _digits(q)
    out = []
    for m in _patients():
        uid = (m["patient_uid"] or "").strip()
        cid = (m["clinic_id"] or "").strip()
        nm  = (m["name"] or "").strip()
        mob = (m["phone10"] or "").strip()
        hit = (ql in nm.lower()) or (q == cid) or (uid.lower() == ql) \
              or (len(qd) >= 4 and qd in _digits(mob))
        if not hit: continue
        out.append({"Patient_UID": uid, "Clinic_Specific_Id": cid,
                    "Patient_Name": nm, "Mobile_Clean": mob,
                    "Age": (m["age"] or "").strip(),
                    "Sex": (m["gender"] or "").strip(),
                    "Diagnosis": (m["diagnosis"] or "").strip(),
                    "Last_Visit": (m["last_visit"] or "").strip()})
        if len(out) >= 20: break
    return out

# --------------------------- writer (own files only) ------------------------ #
def _next_case_id():
    year = datetime.now(IST).strftime("%Y"); mx = 0
    for r in _read_csv(CASE_LEDGER):
        cid = (r.get("Case_ID") or "")
        mm = re.match(r"C-(\d{4})-(\d{6})$", cid)
        if mm and mm.group(1) == year: mx = max(mx, int(mm.group(2)))
    return "C-%s-%06d" % (year, mx + 1)

def _append_ledger(row):
    new = not os.path.exists(CASE_LEDGER)
    with open(CASE_LEDGER, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_COLS)
        if new: w.writeheader()
        w.writerow({k: row.get(k, "") for k in LEDGER_COLS})

def _safe(s, fallback):
    s = re.sub(r"[^A-Za-z0-9_-]+", "_", (s or "").strip())
    return s or fallback

CONSENT_SHELL = u"""<!doctype html><html lang="hi"><head><meta charset="utf-8">
<title>%s — Surgical Consent</title>
<style>body{font-family:'Nirmala UI','Noto Sans Devanagari',serif;max-width:800px;margin:24px auto;padding:0 16px;line-height:1.65;font-size:15px;color:#000}
h2{text-align:center;margin:0 0 4px}.cl{text-align:center;color:#555;font-size:12px;margin:0 0 14px}
.field{border-bottom:1px solid #000;min-height:26px;margin:10px 0;font-size:13px}
.field-label{color:#555;font-size:12px}.place-date{display:flex;justify-content:space-between;margin:14px 0;font-size:13px}
@media print{body{margin:8mm}}</style></head><body>%s</body></html>"""

# --------------------------- registration ----------------------------------- #
def register(app, guard, get_user):
    """Attach the casepack routes to the portal's Flask app.
    guard: decorator enforcing the owner-only gate (portal-owned).
    get_user: () -> username string for Generated_By."""
    from flask import request, jsonify, Response

    os.makedirs(os.path.join(ARCHIVE, "inbox"), exist_ok=True)

    @app.route("/portal/casepack")
    @guard
    def casepack_page():
        if not os.path.exists(PAGE_HTML):
            return Response("casepack_page.html not found at " + PAGE_HTML,
                            status=500, mimetype="text/plain")
        with open(PAGE_HTML, "r", encoding="utf-8") as f:
            return Response(f.read(), mimetype="text/html; charset=utf-8")

    @app.route("/portal/casepack/search")
    @guard
    def casepack_search():
        try:
            return jsonify({"ok": True,
                            "matches": _search(request.args.get("q", ""))})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/cases")
    @guard
    def casepack_cases():
        """Read-only: one item per Case_ID (latest row), newest first, version count."""
        try:
            rows = _read_csv(CASE_LEDGER)
            by = {}; order = []
            for r in rows:
                cid = (r.get("Case_ID") or "").strip()
                if not cid: continue
                if cid not in by: order.append(cid)
                by.setdefault(cid, []).append(r)
            out = []
            for cid in order:
                rs = by[cid]; latest = rs[-1]
                item = {k: (latest.get(k) or "") for k in LEDGER_COLS}
                item["Versions"] = len(rs)
                out.append(item)
            out.sort(key=lambda x: (x.get("Written_At") or ""), reverse=True)
            return jsonify({"ok": True, "cases": out})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/case/<case_id>")
    @guard
    def casepack_case_one(case_id):
        """Read-only: a Case_ID's ledger row + saved bundle.json (recall);
        ?ver=N opens an older version."""
        try:
            rows = [r for r in _read_csv(CASE_LEDGER)
                    if (r.get("Case_ID") or "").strip() == case_id]
            if not rows:
                return jsonify({"ok": False,
                                "error": "Case not found: " + case_id}), 404
            try:
                ver = int(request.args.get("ver") or 0)
            except Exception:
                ver = 0
            if 1 <= ver <= len(rows):
                latest = rows[ver - 1]
            else:
                latest = rows[-1]; ver = len(rows)
            rel = (latest.get("Bundle_File") or "").strip()
            bundle = None
            if rel:
                fp = os.path.join(CASEPACK_DIR, rel)
                if os.path.exists(fp):
                    with open(fp, "r", encoding="utf-8") as f:
                        bundle = json.load(f)
            return jsonify({"ok": True, "row": latest, "versions": len(rows),
                            "opened_version": ver, "bundle": bundle})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/save", methods=["POST"])
    @guard
    def casepack_save():
        try:
            b = request.get_json(force=True) or {}
            p = b.get("patient") or {}
            uid = (p.get("uid") or "").strip(); name = (p.get("name") or "").strip()
            now = datetime.now(IST); date = now.strftime("%Y-%m-%d"); year = now.strftime("%Y")
            # --- versioned save (lifecycle): case_ref = existing Case_ID to version onto ---
            ref = (b.get("case_ref") or "").strip()
            prev_rows = [r for r in _read_csv(CASE_LEDGER)
                         if (r.get("Case_ID") or "").strip() == ref] if ref else []
            if prev_rows:
                case_id = ref; ver = len(prev_rows) + 1
                prev = prev_rows[-1]
                case_date = (prev.get("Case_Date") or date)
                pb = (prev.get("Bundle_File") or "").strip()
                if pb:
                    folder = os.path.join(CASEPACK_DIR, os.path.dirname(pb))
                else:
                    folder = os.path.join(ARCHIVE, year, _safe(uid or name, "NA"))
                base = "%s_%s" % (case_id, _safe(name or prev.get("Patient_Name") or "Patient", "Patient"))
                vsuf = "_v%d_%s" % (ver, date)
            else:
                case_id = _next_case_id(); ver = 1; case_date = date
                vsuf = "_v1_%s" % date
                clin = (p.get("clinic_id") or "").strip()
                if uid:
                    folder_name = _safe((name or "Patient") + "_" + (clin or uid), "Patient")
                else:
                    folder_name = _safe("Unlinked_" + (name or "Unknown"), "Unlinked")
                folder = os.path.join(ARCHIVE, year, folder_name)
                base = "%s_%s" % (case_id, _safe(name or "Patient", "Patient"))
            os.makedirs(folder, exist_ok=True)
            bundle_fp = os.path.join(folder, base + "_bundle%s.json" % vsuf)
            with open(bundle_fp, "w", encoding="utf-8") as f:
                json.dump(b, f, ensure_ascii=False, indent=1)
            consent_fp = ""
            chtml = ((b.get("consent") or {}).get("html") or "").strip()
            if chtml:
                consent_fp = os.path.join(folder, base + "_consent%s.html" % vsuf)
                with open(consent_fp, "w", encoding="utf-8") as f:
                    f.write(CONSENT_SHELL % (name or uid or case_id, chtml))
            est = b.get("estimate_latest") or {}
            _append_ledger({
                "Case_ID": case_id, "Patient_UID": uid,
                "Clinic_Specific_Id": p.get("clinic_id", ""),
                "Patient_Name": name, "Case_Date": case_date,
                "Consent_Procedure": ((b.get("consent") or {}).get("proc") or ""),
                "OT_Tier": ((b.get("ot") or {}).get("tier") or ""),
                "OT_Procedure": ((b.get("ot") or {}).get("proc") or ""),
                "Estimate_Title": (est.get("title") or ""),
                "Estimate_Total": (est.get("total") or ""),
                "Bundle_File": os.path.relpath(bundle_fp, CASEPACK_DIR),
                "Consent_File": (os.path.relpath(consent_fp, CASEPACK_DIR) if consent_fp else ""),
                "Generated_By": (get_user() or "doctor"),
                "Written_At": now.isoformat(timespec="seconds")})
            return jsonify({"ok": True, "case_id": case_id, "version": ver,
                            "files": [os.path.basename(bundle_fp)] +
                                     ([os.path.basename(consent_fp)] if consent_fp else []),
                            "folder": os.path.relpath(folder, CASEPACK_DIR)})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    return True
