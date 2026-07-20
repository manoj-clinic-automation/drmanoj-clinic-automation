#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
casepack_app.py  —  Dr. Manoj Agarwal Clinic  —  Surgical Case Pack (local front-end)

WHAT THIS IS (plain language)
-----------------------------
A small program that runs ONLY on the clinic PC — the same way as the Vitals tool.
Double-click open_casepack.bat and it opens in your browser at

        http://127.0.0.1:5058/case

On that page you:
   1. search a patient (Clinic ID / name / mobile / UID) -> looked up from the
      tracker's local CSV files (READ-ONLY, never written),
   2. build the estimate, OT medicine list, consent, pre/post-op notes as usual,
   3. press "Save case" -> this program writes:
         * one row to case_ledger.csv                (this app's OWN ledger)
         * case_archive\YYYY\UID\date_caseid_bundle.json   (everything, frozen)
         * case_archive\YYYY\UID\date_caseid_consent.html  (printable consent)

WHAT IT DOES / DOES NOT DO
--------------------------
  * READS ONLY the tracker's patient_master.csv + patient_diagnosis.csv.
    It NEVER writes them.  (one-writer-per-file law — KB D126)
  * WRITES ONLY into D:\surgical_casepack\ (its own ledger + case_archive\).
  * No internet. No Drive calls. No VPS. Bound to 127.0.0.1 (this PC only).
  * The live follow-up tracker and the Vitals tool are NOT touched.
  * The same page still works standalone/offline on the phone (file open):
    there Save downloads a JSON you can drop into case_archive\inbox\.
"""

import os, sys, csv, json, re, webbrowser, threading
from datetime import datetime, timezone, timedelta

# --- where everything lives (edit ONLY these two lines if paths ever change) ---
APP_DIR   = os.path.dirname(os.path.abspath(__file__))            # D:\surgical_casepack
DATA_DIR  = r"C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\data"

MASTER_CSV  = os.path.join(DATA_DIR, "patient_master.csv")
DIAG_CSV    = os.path.join(DATA_DIR, "patient_diagnosis.csv")
CASE_LEDGER = os.path.join(APP_DIR, "case_ledger.csv")
ARCHIVE     = os.path.join(APP_DIR, "case_archive")
PAGE_HTML   = os.path.join(APP_DIR, "casepack_page.html")

PORT = 5058   # tracker=5000, vitals=5057, casepack=5058 — never clash

try:
    from flask import Flask, request, jsonify, Response, redirect
except Exception:
    sys.stderr.write("\nFlask is not installed. On the clinic PC run once:\n    pip install flask\n\n")
    raise

app = Flask(__name__)
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

def _search(q):
    q=(q or "").strip()
    if len(q)<2: return []
    ql=q.lower(); qd=_digits(q)
    master=_read_csv(MASTER_CSV); diag=_read_csv(DIAG_CSV)
    dby={}
    for d in diag:
        u=(d.get("Patient_UID") or "").strip()
        if u: dby[u]=d
    out=[]
    for m in master:
        uid=(m.get("Patient_UID") or "").strip()
        cid=(m.get("Clinic_Specific_Id") or "").strip()
        nm =(m.get("Patient_Name") or "").strip()
        mob=(m.get("Mobile_Clean") or "").strip()
        hit = (ql in nm.lower()) or (q==cid) or (uid.lower()==ql) or (len(qd)>=4 and qd in _digits(mob))
        if not hit: continue
        d=dby.get(uid,{})
        out.append({"Patient_UID":uid,"Clinic_Specific_Id":cid,"Patient_Name":nm,
                    "Mobile_Clean":mob,"Age":(d.get("Age") or "").strip(),"Sex":(d.get("Sex") or "").strip()})
        if len(out)>=20: break
    return out

# --------------------------- writer (own files only) ------------------------ #
def _next_case_id():
    year=datetime.now(IST).strftime("%Y"); mx=0
    for r in _read_csv(CASE_LEDGER):
        cid=(r.get("Case_ID") or "")
        mm=re.match(r"C-(\d{4})-(\d{6})$", cid)
        if mm and mm.group(1)==year: mx=max(mx,int(mm.group(2)))
    return "C-%s-%06d" % (year, mx+1)

def _append_ledger(row):
    new = not os.path.exists(CASE_LEDGER)
    with open(CASE_LEDGER,"a",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=LEDGER_COLS)
        if new: w.writeheader()
        w.writerow({k:row.get(k,"") for k in LEDGER_COLS})

def _safe(s,fallback):
    s=re.sub(r"[^A-Za-z0-9_-]+","_",(s or "").strip())
    return s or fallback

CONSENT_SHELL=u"""<!doctype html><html lang="hi"><head><meta charset="utf-8">
<title>%s — Surgical Consent</title>
<style>body{font-family:'Nirmala UI','Noto Sans Devanagari',serif;max-width:800px;margin:24px auto;padding:0 16px;line-height:1.65;font-size:15px;color:#000}
h2{text-align:center;margin:0 0 4px}.cl{text-align:center;color:#555;font-size:12px;margin:0 0 14px}
.field{border-bottom:1px solid #000;min-height:26px;margin:10px 0;font-size:13px}
.field-label{color:#555;font-size:12px}.place-date{display:flex;justify-content:space-between;margin:14px 0;font-size:13px}
@media print{body{margin:8mm}}</style></head><body>%s</body></html>"""

@app.route("/")
def root(): return redirect("/case")

@app.route("/case")
def page():
    if not os.path.exists(PAGE_HTML):
        return Response("casepack_page.html not found beside casepack_app.py", status=500)
    with open(PAGE_HTML,"r",encoding="utf-8") as f:
        return Response(f.read(), mimetype="text/html; charset=utf-8")

@app.route("/search")
def search():
    try:
        return jsonify({"ok":True,"matches":_search(request.args.get("q",""))})
    except Exception as e:
        return jsonify({"ok":False,"error":str(e)}),500

@app.route("/save", methods=["POST"])
def save():
    try:
        b=request.get_json(force=True) or {}
        p=b.get("patient") or {}
        uid=(p.get("uid") or "").strip(); name=(p.get("name") or "").strip()
        now=datetime.now(IST); date=now.strftime("%Y-%m-%d"); year=now.strftime("%Y")
        case_id=_next_case_id()
        folder=os.path.join(ARCHIVE, year, _safe(uid or name,"NA"))
        os.makedirs(folder, exist_ok=True)
        base="%s_%s" % (date, case_id)
        bundle_fp=os.path.join(folder, base+"_bundle.json")
        with open(bundle_fp,"w",encoding="utf-8") as f:
            json.dump(b,f,ensure_ascii=False,indent=1)
        consent_fp=""
        chtml=((b.get("consent") or {}).get("html") or "").strip()
        if chtml:
            consent_fp=os.path.join(folder, base+"_consent.html")
            with open(consent_fp,"w",encoding="utf-8") as f:
                f.write(CONSENT_SHELL % (name or uid or case_id, chtml))
        est=b.get("estimate_latest") or {}
        _append_ledger({
            "Case_ID":case_id,"Patient_UID":uid,"Clinic_Specific_Id":p.get("clinic_id",""),
            "Patient_Name":name,"Case_Date":date,
            "Consent_Procedure":((b.get("consent") or {}).get("proc") or ""),
            "OT_Tier":((b.get("ot") or {}).get("tier") or ""),
            "OT_Procedure":((b.get("ot") or {}).get("proc") or ""),
            "Estimate_Title":(est.get("title") or ""),"Estimate_Total":(est.get("total") or ""),
            "Bundle_File":os.path.relpath(bundle_fp,APP_DIR),
            "Consent_File":(os.path.relpath(consent_fp,APP_DIR) if consent_fp else ""),
            "Generated_By":"owner","Written_At":now.isoformat(timespec="seconds")})
        return jsonify({"ok":True,"case_id":case_id,
                        "folder":os.path.relpath(folder,APP_DIR)})
    except Exception as e:
        return jsonify({"ok":False,"error":str(e)}),500

def _open():
    try: webbrowser.open("http://127.0.0.1:%d/case" % PORT)
    except Exception: pass

if __name__=="__main__":
    os.makedirs(os.path.join(ARCHIVE,"inbox"), exist_ok=True)  # offline drops land here
    print("\n  Surgical Case Pack  ->  http://127.0.0.1:%d/case\n  (reads tracker CSVs read-only; writes only in %s)\n" % (PORT, APP_DIR))
    threading.Timer(1.2,_open).start()
    app.run(host="127.0.0.1", port=PORT, debug=False)
