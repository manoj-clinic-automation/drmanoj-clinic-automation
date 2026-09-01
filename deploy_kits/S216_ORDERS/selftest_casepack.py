#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_casepack.py — offline proof of casepack_portal.py v2 (S215 · CP-1)
Runs ANYWHERE: builds throwaway fixture stores in a temp dir, spins the module
on a bare Flask app with a pass-through guard, and exercises every route.
No live file, no live db, no network. Fixture identities are runtime-assembled
(F-185: no ten-digit literal anywhere in this file).
Exit 0 = every check passed. Any FAIL = exit 1.
"""
import os, sys, json, tempfile, shutil, sqlite3, importlib.util

BASE = os.path.dirname(os.path.abspath(__file__))
N = [0, 0]
def check(name, ok, extra=""):
    N[0] += 1
    if ok: N[1] += 1; print("  ok  %-52s" % name)
    else:  print("FAIL  %-52s %s" % (name, extra))
    return ok

def fixture_mobile(seed):
    # runtime-assembled ten digits; never a literal (F-185)
    d = "98" + "".join(str((seed * 7 + i) % 10) for i in range(8))
    return d

def build_console(fp):
    con = sqlite3.connect(fp)
    con.execute("CREATE TABLE patients (phone10 TEXT, name TEXT, diagnosis TEXT,"
                " age TEXT, gender TEXT, last_visit TEXT, patient_uid TEXT, clinic_id TEXT)")
    rows = [
        (fixture_mobile(1), "RAM PRAKASH TEST", "OA knee", "62", "M", "2026-08-20", "UID-A1", "7001"),
        (fixture_mobile(2), "SUNITA TEST",      "# neck femur", "70", "F", "2026-08-28", "UID-B2", "7002"),
    ]
    con.executemany("INSERT INTO patients VALUES (?,?,?,?,?,?,?,?)", rows)
    con.commit(); con.close()

def build_finance(fp, with_mobile=True):
    con = sqlite3.connect(fp)
    con.execute("CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT,"
                " name TEXT, phone_last4 TEXT, first_seen TEXT, merged_into INTEGER, note TEXT)")
    if with_mobile:
        con.execute("ALTER TABLE patient_ref ADD COLUMN mobile TEXT")
        con.execute("INSERT INTO patient_ref (clinic_id,name,phone_last4,mobile) VALUES (?,?,?,?)",
                    ("7002", "SUNITA TEST", fixture_mobile(2)[-4:], fixture_mobile(2)))
        con.execute("INSERT INTO patient_ref (clinic_id,name,phone_last4,mobile) VALUES (?,?,?,?)",
                    ("7003", "MASTER ONLY TEST", fixture_mobile(3)[-4:], fixture_mobile(3)))
        con.execute("INSERT INTO patient_ref (clinic_id,name,phone_last4,mobile,merged_into) VALUES (?,?,?,?,1)",
                    ("7004", "MERGED AWAY TEST", fixture_mobile(4)[-4:], fixture_mobile(4)))
    else:
        con.execute("INSERT INTO patient_ref (clinic_id,name,phone_last4) VALUES (?,?,?)",
                    ("7003", "MASTER ONLY TEST", fixture_mobile(3)[-4:]))
    con.commit(); con.close()

def load_module(tmp, console_fp, finance_fp):
    os.environ["PORTAL_CASEPACK_DIR"] = os.path.join(tmp, "casepack")
    os.environ["PORTAL_CONSOLE_DB"]   = console_fp
    os.environ["PORTAL_FINANCE_DB"]   = finance_fp
    spec = importlib.util.spec_from_file_location("cp2", os.path.join(BASE, "casepack_portal.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def make_client(mod):
    from flask import Flask
    app = Flask(__name__)
    def guard(f): return f            # pass-through: auth stays portal.py's (S172 wiring unchanged)
    mod.register(app, guard, lambda: "selftest")
    return app.test_client()

def main():
    tmp = tempfile.mkdtemp(prefix="cp1_selftest_")
    try:
        console_fp = os.path.join(tmp, "console.db"); build_console(console_fp)
        finance_fp = os.path.join(tmp, "finance.db"); build_finance(finance_fp, True)
        mod = load_module(tmp, console_fp, finance_fp)
        c = make_client(mod)

        # ---- search: master + console merged ----
        j = c.get("/portal/casepack/search?q=SUNITA").get_json()
        check("search ok", j["ok"])
        m = [x for x in j["matches"] if x["Clinic_Specific_Id"] == "7002"]
        check("master row wins for 7002", len(m) == 1 and m[0]["Source"] == "master")
        check("console enriches age/uid", m[0]["Age"] == "70" and m[0]["Patient_UID"] == "UID-B2")
        check("full mobile present (D356)", len(m[0]["Mobile_Clean"]) == 10)
        j2 = c.get("/portal/casepack/search?q=MASTER ONLY").get_json()
        check("master-only patient found", any(x["Clinic_Specific_Id"] == "7003" for x in j2["matches"]))
        check("merged_into rows excluded", not any(x["Clinic_Specific_Id"] == "7004" for x in j2["matches"]))
        j3 = c.get("/portal/casepack/search?q=RAM PRAKASH").get_json()
        r3 = [x for x in j3["matches"] if x["Clinic_Specific_Id"] == "7001"]
        check("console-only patient still found", len(r3) == 1 and r3[0]["Source"] == "console")
        jd = c.get("/portal/casepack/search?q=" + fixture_mobile(3)[2:8]).get_json()
        check("digit search hits master mobile", any(x["Clinic_Specific_Id"] == "7003" for x in jd["matches"]))
        check("sources reported", "master" in j["sources"] and "console" in j["sources"])

        # ---- degradation: master missing → visible, not fatal ----
        os.environ["PORTAL_FINANCE_DB"] = os.path.join(tmp, "absent.db")
        mod2 = load_module(tmp, console_fp, os.path.join(tmp, "absent.db"))
        c2 = make_client(mod2)
        jm = c2.get("/portal/casepack/search?q=SUNITA").get_json()
        check("master-missing degrades visibly", jm["ok"] and "master_error" in jm["sources"]
              and any(x["Source"] == "console" for x in jm["matches"]))
        # both missing → loud error
        mod3 = load_module(tmp, os.path.join(tmp, "absent2.db"), os.path.join(tmp, "absent.db"))
        c3 = make_client(mod3)
        r = c3.get("/portal/casepack/search?q=SUNITA")
        check("both-missing fails loud (500)", r.status_code == 500 and not r.get_json()["ok"])
        # pre-D356 store: fragment shown masked, never as a number
        fin_old = os.path.join(tmp, "finance_old.db"); build_finance(fin_old, False)
        mod4 = load_module(tmp, console_fp, fin_old)
        c4 = make_client(mod4)
        jo = c4.get("/portal/casepack/search?q=MASTER ONLY").get_json()
        ro = [x for x in jo["matches"] if x["Clinic_Specific_Id"] == "7003"][0]
        check("last4 shown masked pre-D356", ro["Mobile_Clean"].startswith("xxxxxx"))

        # ---- save lifecycle + consent versioning (D359) ----
        mod5 = load_module(tmp, console_fp, finance_fp)
        c5 = make_client(mod5)
        html1 = "<p>consent body version one</p>"
        b1 = {"patient": {"uid": "UID-B2", "clinic_id": "7002", "name": "SUNITA TEST"},
              "stage": 2,
              "consent": {"proc": "thrneck", "date": "2026-09-01", "html": html1,
                          "polio": {"on": True, "proc": "thr_fnf"}, "change_note": ""},
              "estimate_latest": {"title": "THR — fracture neck femur", "total": "0"}}
        j = c5.post("/portal/casepack/save", json=b1).get_json()
        check("save v1 ok", j["ok"] and j["version"] == 1)
        cid = j["case_id"]
        check("case id shape", cid.startswith("C-20") and len(cid) == 13)
        check("consent c1 new", j["consent"]["no"] == 1 and j["consent"]["kind"] == "new")
        # same content, later date → RE-ISSUE, same number
        b2 = dict(b1); b2["case_ref"] = cid
        b2["consent"] = dict(b1["consent"], date="2026-09-04")
        j = c5.post("/portal/casepack/save", json=b2).get_json()
        check("save v2 ok", j["ok"] and j["version"] == 2)
        check("unchanged consent = re-issue c1", j["consent"]["no"] == 1 and j["consent"]["kind"] == "reissue"
              and j["consent"]["issue_date"] == "2026-09-04")
        # changed content → REVISION c2 with note
        b3 = dict(b2)
        b3["consent"] = dict(b2["consent"], html="<p>consent body version two — high-risk added</p>",
                             change_note="added high-risk clause", date="2026-09-04")
        j = c5.post("/portal/casepack/save", json=b3).get_json()
        check("changed consent = revision c2", j["consent"]["no"] == 2 and j["consent"]["kind"] == "revision")
        # ledger + files
        jl = c5.get("/portal/casepack/consents/" + cid).get_json()
        check("consent ledger 3 rows", jl["ok"] and len(jl["rows"]) == 3)
        check("kinds new/reissue/revision", [r2["Kind"] for r2 in jl["rows"]] == ["new", "reissue", "revision"])
        check("change note stored", jl["rows"][2]["Change_Note"] == "added high-risk clause")
        check("polio module recorded", jl["rows"][0]["Polio_Module"] == "thr_fnf")
        cpdir = os.environ["PORTAL_CASEPACK_DIR"]
        files = [r2["File"] for r2 in jl["rows"]]
        check("3 distinct consent files, none deleted",
              len(set(files)) == 3 and all(os.path.exists(os.path.join(cpdir, f)) for f in files))
        # consentfile route
        r = c5.get("/portal/casepack/consentfile?case=%s&n=2" % cid)
        check("consentfile serves html", r.status_code == 200 and b"consent body version one" in r.data)
        r = c5.get("/portal/casepack/consentfile?case=%s&n=9" % cid)
        check("consentfile bad n → 404", r.status_code == 404)
        # path traversal refused even if a ledger row were poisoned
        evil = os.path.join(tmp, "evil.html"); open(evil, "w").write("nope")
        mod5._append_consent_ledger({"Case_ID": "C-EVIL", "Consent_No": 1, "Kind": "new",
                                     "Issue_Date": "2026-09-01", "Content_MD5": "x",
                                     "Procedure": "", "Polio_Module": "", "Change_Note": "",
                                     "File": "../evil.html", "Issued_By": "t", "Written_At": "t"})
        r = c5.get("/portal/casepack/consentfile?case=C-EVIL&n=1")
        check("poisoned path refused", r.status_code == 400)
        # recall carries consents + stage
        jr = c5.get("/portal/casepack/case/" + cid).get_json()
        check("recall ok, 3 case versions", jr["ok"] and jr["versions"] == 3)
        check("recall lists consents", len(jr["consents"]) == 3)
        check("bundle carries stage", jr["bundle"].get("stage") == 2)
        check("bundle carries polio", jr["bundle"]["consent"]["polio"]["on"] is True)
        jc = c5.get("/portal/casepack/cases").get_json()
        check("cases list versions=3", jc["ok"] and jc["cases"][0]["Versions"] == 3)
        # clinic-id-only save (master patient, no UID) gets a real folder
        b4 = {"patient": {"uid": "", "clinic_id": "7003", "name": "MASTER ONLY TEST"},
              "consent": {}, "estimate_latest": {}}
        j = c5.post("/portal/casepack/save", json=b4).get_json()
        check("uid-less master save ok", j["ok"] and "Unlinked" not in j["folder"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d/%d checks passed" % (N[1], N[0]))
    sys.exit(0 if N[0] == N[1] else 1)

if __name__ == "__main__":
    main()
