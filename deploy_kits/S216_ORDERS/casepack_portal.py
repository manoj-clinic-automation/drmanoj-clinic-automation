#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
casepack_portal.py — Surgical Case Pack, VPS edition · v2 (S215, CP-1 · D359)
=============================================================================
Base: the S172 module (live pin 341404d7e6d054b4c49fae09d59ea13b), evolved in
place for contract D359 CP-1. Everything the S172 module did, it still does,
byte-compatible for the page's existing calls.

WHAT v2 ADDS (CP-1 scope only)
------------------------------
1. PATIENT LOOKUP now reads the Docterz patient master on this box —
   finance.db `patient_ref` (D355/D356: full names, full mobiles) — MERGED
   with the S172 console.db mirror (which contributes age/sex/diagnosis/
   last-visit). Each result carries Source. One source failing degrades
   VISIBLY in the payload; only BOTH failing is an error (D236 fail-loud).
2. CONSENT VERSIONING (D359): every saved consent is hashed (md5 of the
   html). Same content as the case's previous consent = a RE-ISSUE (same
   consent number, new issue date, recorded). Changed content = the next
   consent number, with an optional change note. Nothing is ever deleted;
   every issue writes its own dated file and one ledger row.
     consent_ledger.csv  (CASEPACK_DIR, append-only, this module sole writer)
3. Two read-only routes: /portal/casepack/consents/<case_id> (the ledger)
   and /portal/casepack/consentfile?case=..&n=.. (an archived consent html,
   path-validated to stay inside the archive).
4. The saved bundle records `stage` (the CP-1 stepper position).

UNCHANGED: guard wiring (owner-only, portal-owned), the case ledger columns,
bundle/versioned-save lifecycle, archive layout, sole-writer rule (D235),
PHI stays out of git (F-31/F-49).
"""

import os, csv, json, re, sqlite3, hashlib
import shutil
from datetime import datetime, timezone, timedelta

# --- where everything lives (env-overridable, defaults match /root/wa) ------
CASEPACK_DIR = os.environ.get("PORTAL_CASEPACK_DIR",
                              "/root/wa/casepack")
CONSOLE_DB   = os.environ.get("PORTAL_CONSOLE_DB",
                              "/root/wa/console.db")
FINANCE_DB   = os.environ.get("PORTAL_FINANCE_DB",
                              "/root/finance/finance.db")

CASE_LEDGER    = os.path.join(CASEPACK_DIR, "case_ledger.csv")
CONSENT_LEDGER = os.path.join(CASEPACK_DIR, "consent_ledger.csv")
ARCHIVE        = os.path.join(CASEPACK_DIR, "case_archive")
PAGE_HTML      = os.path.join(CASEPACK_DIR, "casepack_page.html")
MED_LIST       = os.path.join(CASEPACK_DIR, "med_list.csv")

IST = timezone(timedelta(hours=5, minutes=30))

LEDGER_COLS = ["Case_ID","Patient_UID","Clinic_Specific_Id","Patient_Name","Case_Date",
               "Consent_Procedure","OT_Tier","OT_Procedure","Estimate_Title","Estimate_Total",
               "Bundle_File","Consent_File","Generated_By","Written_At"]

CONSENT_COLS = ["Case_ID","Consent_No","Kind","Issue_Date","Content_MD5","Procedure",
                "Polio_Module","Change_Note","File","Issued_By","Written_At"]

MED_COLS = ["Item","Route","Freq","Ayushman","Package","Active","Sort"]

# The owner's own post-op medicines, from MY_TEMPLATES_S216.txt. Seeded ONCE if
# the list does not exist; after that the file is his and is never re-seeded.
MED_SEED = [
    ("5% DNS",              "IV",  "",    "", "", "1", "10"),
    ("NS",                  "IV",  "",    "", "", "1", "11"),
    ("Ringer Lactate",      "IV",  "",    "", "", "1", "12"),
    ("Inj Pantawin 40",     "IV",  "OD",  "", "", "1", "20"),
    ("Inj Aciloc",          "IV",  "BD",  "", "", "1", "21"),
    ("Inj Vinbactum DS",    "IV",  "BD",  "", "", "1", "30"),
    ("Inj Q Bact 1.5",      "IV",  "BD",  "", "", "1", "31"),
    ("Inj Tazar 4.5",       "IV",  "TDS", "", "", "1", "32"),
    ("Inj Vintaz P 4.5",    "IV",  "TDS", "", "", "1", "33"),
    ("Inj Dynapar",         "IV",  "TDS", "", "", "1", "40"),
    ("Inj Lonac",           "IV",  "TDS", "", "", "1", "41"),
    ("Inj Butrum 2 Mg",     "IM",  "SOS", "", "", "1", "50"),
    ("Inj Pcm 100 Ml",      "IV",  "SOS", "", "", "1", "51"),
]

def _med_rows():
    """The medicine list. Seeded from the owner's template the first time only."""
    if not os.path.exists(MED_LIST):
        _med_write([dict(zip(MED_COLS, r)) for r in MED_SEED])
    return _read_csv(MED_LIST)

def _med_write(rows):
    """Replace the list. The previous file is kept, dated, never deleted."""
    if os.path.exists(MED_LIST):
        stamp = datetime.now(IST).strftime("%Y%m%d_%H%M%S")
        try:
            shutil.copy2(MED_LIST, MED_LIST + ".bak_" + stamp)
        except Exception:
            pass
    with open(MED_LIST, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MED_COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: str(r.get(k, "") or "") for k in MED_COLS})

# --------------------------- read-only helpers ------------------------------ #
def _read_csv(path):
    if not os.path.exists(path): return []
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def _digits(s): return "".join(ch for ch in str(s or "") if ch.isdigit())

def _patients():
    """S172 source: the console.db patients mirror, READ-ONLY. Raises with a
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

def _console_rows(q):
    """The S172 search, verbatim behaviour, plus Source tag."""
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
                    "Last_Visit": (m["last_visit"] or "").strip(),
                    "Source": "console"})
        if len(out) >= 20: break
    return out

def _master_rows(q):
    """D355/D356: the Docterz patient master — finance.db patient_ref,
    READ-ONLY. Full mobile when the D356 column exists; the pre-D356
    phone_last4 shown masked otherwise (a fragment must never read as a
    number). Fail loud with a plain message if the db is missing."""
    if not os.path.exists(FINANCE_DB):
        raise RuntimeError("patient master unavailable — finance.db not found")
    ql = q.lower(); qd = _digits(q)
    conn = sqlite3.connect("file:%s?mode=ro" % FINANCE_DB, uri=True)
    try:
        conn.row_factory = sqlite3.Row
        cols = {r[1] for r in conn.execute("PRAGMA table_info(patient_ref)")}
        has_mobile = "mobile" in cols
        mobcol = "mobile" if has_mobile else "phone_last4"
        rows = conn.execute(
            "SELECT id, clinic_id, name, COALESCE(%s,'') AS mob "
            "FROM patient_ref WHERE merged_into IS NULL "
            "AND clinic_id <> 'WALK-IN'" % mobcol).fetchall()
    finally:
        conn.close()
    out = []
    for m in rows:
        cid = (m["clinic_id"] or "").strip()
        nm  = (m["name"] or "").strip()
        mob = (m["mob"] or "").strip()
        hit = (ql in nm.lower()) or (q == cid) \
              or (has_mobile and len(qd) >= 4 and qd in _digits(mob))
        if not hit: continue
        shown = mob if has_mobile else ("xxxxxx" + mob if mob else "")
        out.append({"Patient_UID": "", "Clinic_Specific_Id": cid,
                    "Patient_Name": nm, "Mobile_Clean": shown,
                    "Age": "", "Sex": "", "Diagnosis": "", "Last_Visit": "",
                    "Source": "master"})
        if len(out) >= 20: break
    return out

def _search2(q):
    """CP-1 lookup: master first (D359 ruling 5), console enriches and fills.
    Returns (matches, sources) — sources says what each store contributed or
    why it could not."""
    q = (q or "").strip()
    if len(q) < 2: return [], {"master": 0, "console": 0}
    sources = {}
    try:
        master = _master_rows(q); sources["master"] = len(master)
    except Exception as e:
        master = []; sources["master_error"] = str(e)
    try:
        console = _console_rows(q); sources["console"] = len(console)
    except Exception as e:
        console = []; sources["console_error"] = str(e)
    if "master_error" in sources and "console_error" in sources:
        raise RuntimeError("both patient sources failed — master: %s · console: %s"
                           % (sources["master_error"], sources["console_error"]))
    by_cid = {}
    for r in console:
        c = r["Clinic_Specific_Id"]
        if c and c not in by_cid: by_cid[c] = r
    out = []
    seen = set()
    for r in master:
        c = r["Clinic_Specific_Id"]
        enr = by_cid.get(c)
        if enr:
            for k in ("Patient_UID", "Age", "Sex", "Diagnosis", "Last_Visit"):
                if not r[k]: r[k] = enr[k]
            if not r["Mobile_Clean"]: r["Mobile_Clean"] = enr["Mobile_Clean"]
        out.append(r); seen.add(c)
    for r in console:
        if r["Clinic_Specific_Id"] in seen: continue
        out.append(r)
        if len(out) >= 20: break
    return out[:20], sources

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

def _append_consent_ledger(row):
    new = not os.path.exists(CONSENT_LEDGER)
    with open(CONSENT_LEDGER, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CONSENT_COLS)
        if new: w.writeheader()
        w.writerow({k: row.get(k, "") for k in CONSENT_COLS})

def _consent_rows(case_id):
    return [r for r in _read_csv(CONSENT_LEDGER)
            if (r.get("Case_ID") or "").strip() == case_id]

def _safe(s, fallback):
    s = re.sub(r"[^A-Za-z0-9_-]+", "_", (s or "").strip())
    return s or fallback

CONSENT_SHELL = u"""<!doctype html><html lang="hi"><head><meta charset="utf-8">
<title>%s — Surgical Consent</title>
<style>body{font-family:'Nirmala UI','Noto Sans Devanagari',serif;max-width:800px;margin:24px auto;padding:0 16px;line-height:1.65;font-size:15px;color:#000}
h2{text-align:center;margin:0 0 4px}.cl{text-align:center;color:#555;font-size:12px;margin:0 0 14px}
h3.cs-mod{margin:14px 0 4px;font-size:16px}
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
            matches, sources = _search2(request.args.get("q", ""))
            return jsonify({"ok": True, "matches": matches, "sources": sources})
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
                            "opened_version": ver, "bundle": bundle,
                            "consents": _consent_rows(case_id)})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/meds")
    @guard
    def casepack_meds():
        """The owner's medicine list — read."""
        try:
            return jsonify({"ok": True, "rows": _med_rows()})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/meds", methods=["POST"])
    @guard
    def casepack_meds_save():
        """Replace the medicine list. Refuses an empty list — that is far more
        likely to be a bug in the page than an intention, and the previous file
        would already have been backed up for nothing."""
        try:
            b = request.get_json(force=True) or {}
            rows = b.get("rows")
            if not isinstance(rows, list) or not rows:
                return jsonify({"ok": False, "error": "refused: empty list"}), 400
            if len(rows) > 400:
                return jsonify({"ok": False, "error": "refused: too many rows"}), 400
            clean = []
            for r in rows:
                item = str((r or {}).get("Item", "")).strip()
                if not item:
                    continue
                clean.append({
                    "Item":     item[:120],
                    "Route":    str(r.get("Route", "")).strip()[:12],
                    "Freq":     str(r.get("Freq", "")).strip()[:12],
                    "Ayushman": "1" if str(r.get("Ayushman", "")).strip() in ("1", "true", "True") else "",
                    "Package":  "1" if str(r.get("Package", "")).strip() in ("1", "true", "True") else "",
                    "Active":   "" if str(r.get("Active", "1")).strip() in ("", "0", "false", "False") else "1",
                    "Sort":     str(r.get("Sort", "")).strip()[:8],
                })
            if not clean:
                return jsonify({"ok": False, "error": "refused: no usable rows"}), 400
            _med_write(clean)
            return jsonify({"ok": True, "count": len(clean)})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/consents/<case_id>")
    @guard
    def casepack_consents(case_id):
        """Read-only: the consent ledger for one case — v1, v2, re-issues,
        who, when (D359: the consent history is a first-class record)."""
        try:
            return jsonify({"ok": True, "rows": _consent_rows(case_id)})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/consentfile")
    @guard
    def casepack_consentfile():
        """Read-only: one archived consent html, by case + ledger row index.
        The path comes from our own ledger and is still validated to stay
        inside CASEPACK_DIR — never from the query string directly."""
        try:
            case_id = (request.args.get("case") or "").strip()
            n = int(request.args.get("n") or 0)
            rows = _consent_rows(case_id)
            if not (1 <= n <= len(rows)):
                return jsonify({"ok": False, "error": "no such consent row"}), 404
            rel = (rows[n-1].get("File") or "").strip()
            fp = os.path.realpath(os.path.join(CASEPACK_DIR, rel))
            root = os.path.realpath(CASEPACK_DIR)
            if not fp.startswith(root + os.sep):
                return jsonify({"ok": False, "error": "path refused"}), 400
            if not os.path.exists(fp):
                return jsonify({"ok": False, "error": "file missing: " + rel}), 404
            with open(fp, "r", encoding="utf-8") as f:
                return Response(f.read(), mimetype="text/html; charset=utf-8")
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
                elif clin:
                    folder_name = _safe((name or "Patient") + "_" + clin, "Patient")
                else:
                    folder_name = _safe("Unlinked_" + (name or "Unknown"), "Unlinked")
                folder = os.path.join(ARCHIVE, year, folder_name)
                base = "%s_%s" % (case_id, _safe(name or "Patient", "Patient"))
            os.makedirs(folder, exist_ok=True)
            bundle_fp = os.path.join(folder, base + "_bundle%s.json" % vsuf)
            with open(bundle_fp, "w", encoding="utf-8") as f:
                json.dump(b, f, ensure_ascii=False, indent=1)
            # ---- consent: versioned per D359, never deleted, hash-decided ----
            consent_fp = ""; consent_info = None
            cobj  = (b.get("consent") or {})
            chtml = (cobj.get("html") or "").strip()
            if chtml:
                chash = hashlib.md5(chtml.encode("utf-8")).hexdigest()
                issue_date = (cobj.get("date") or "").strip() or date
                crows = _consent_rows(case_id)
                last = crows[-1] if crows else None
                if last and (last.get("Content_MD5") or "") == chash:
                    kind = "reissue"; cno = int(last.get("Consent_No") or 1)
                elif crows:
                    kind = "revision"; cno = int(last.get("Consent_No") or len(crows)) + 1
                else:
                    kind = "new"; cno = 1
                consent_fp = os.path.join(folder, base + "_consent_c%d%s.html" % (cno, vsuf))
                with open(consent_fp, "w", encoding="utf-8") as f:
                    f.write(CONSENT_SHELL % (name or uid or case_id, chtml))
                polio = (cobj.get("polio") or {})
                _append_consent_ledger({
                    "Case_ID": case_id, "Consent_No": cno, "Kind": kind,
                    "Issue_Date": issue_date, "Content_MD5": chash,
                    "Procedure": (cobj.get("proc") or ""),
                    "Polio_Module": (polio.get("proc") or "") if polio.get("on") else "",
                    "Change_Note": (cobj.get("change_note") or ""),
                    "File": os.path.relpath(consent_fp, CASEPACK_DIR),
                    "Issued_By": (get_user() or "doctor"),
                    "Written_At": now.isoformat(timespec="seconds")})
                consent_info = {"no": cno, "kind": kind, "hash8": chash[:8],
                                "issue_date": issue_date}
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
            out = {"ok": True, "case_id": case_id, "version": ver,
                   "files": [os.path.basename(bundle_fp)] +
                            ([os.path.basename(consent_fp)] if consent_fp else []),
                   "folder": os.path.relpath(folder, CASEPACK_DIR)}
            if consent_info: out["consent"] = consent_info
            return jsonify(out)
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    return True
