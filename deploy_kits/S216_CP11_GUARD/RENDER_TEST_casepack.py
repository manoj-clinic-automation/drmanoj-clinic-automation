#!/usr/bin/env python3
# RENDER_TEST_casepack.py — the S214 rule: a page is proven only when a browser
# has CLICKED it. Serves the kit page + stub endpoints, drives headless
# chromium (playwright). Exit 0 green · 2 = playwright unavailable (SKIP).
import os, json, sys, threading
BASE = os.path.dirname(os.path.abspath(__file__))
try:
    from playwright.sync_api import sync_playwright
except Exception:
    print("SKIP: playwright not available here"); sys.exit(2)
from http.server import BaseHTTPRequestHandler, HTTPServer
SAVED = []
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _j(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path.startswith("/portal/casepack/search"):
            self._j({"ok": True, "sources": {"master": 1, "console": 1}, "matches": [
                {"Patient_UID": "UID-B2", "Clinic_Specific_Id": "7002", "Patient_Name": "SUNITA TEST",
                 "Mobile_Clean": "98" + "0" * 8, "Age": "70", "Sex": "F", "Diagnosis": "", "Last_Visit": "",
                 "Source": "master"}]}); return
        if self.path.startswith("/portal/casepack/consents/"):
            self._j({"ok": True, "rows": [{"Consent_No": "1", "Kind": "new", "Issue_Date": "2026-09-01",
                     "Procedure": "thrneck", "Polio_Module": "thr_fnf", "Change_Note": "", "File": "x"}]}); return
        b = open(os.path.join(BASE, "casepack_page.html"), "rb").read()
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        SAVED.append(json.loads(self.rfile.read(n) or b"{}"))
        self._j({"ok": True, "case_id": "C-2026-000099", "version": len(SAVED),
                 "folder": "case_archive/2026/T", "files": ["f.json"],
                 "consent": {"no": 1, "kind": "new", "hash8": "deadbeef", "issue_date": "2026-09-01"}})
N=[0,0]
def check(name, ok):
    N[0]+=1
    if ok: N[1]+=1; print("  ok  "+name)
    else: print("FAIL  "+name)
srv = HTTPServer(("127.0.0.1", 0), H); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
with sync_playwright() as pw:
    b = pw.chromium.launch(); pg = b.new_page()
    pg.goto("http://127.0.0.1:%d/portal/casepack" % port, wait_until="load")
    pg.wait_for_timeout(600)
    check("stepper visible", pg.locator("#cpStepper .cpstep").count() == 4)
    check("stage1 active", "on" in (pg.locator('#cpStepper .cpstep[data-st="1"]').get_attribute("class") or ""))
    pg.click('#cpStepper .cpstep[data-st="2"]'); pg.wait_for_timeout(400)
    check("stage2 opens build modal", "open" in (pg.locator("#caseModal").get_attribute("class") or ""))
    check("stepper follows", "on" in (pg.locator('#cpStepper .cpstep[data-st="2"]').get_attribute("class") or ""))
    pg.click('#caseSub button[data-s="consent"]'); pg.wait_for_timeout(200)
    check("polio toggle present", pg.locator("#cs_polio").count() == 1)
    pg.check("#cs_polio"); pg.wait_for_timeout(150)
    check("polio sub-selector reveals", pg.locator("#polioSub").is_visible())
    check("THR entry listed", "Total Hip Replacement" in (pg.locator("#cs_polio_proc").inner_text() or ""))
    pg.select_option("#cs_proc", "thrneck")
    pg.fill("#c_name", "TEST NAAM"); pg.fill("#c_age", "65")
    pg.on("dialog", lambda d: d.accept())
    pg.fill("#pb_q", "SUNITA"); pg.wait_for_timeout(700)
    check("lookup renders with source tag", "Docterz" in (pg.locator("#pb_res").inner_text() or ""))
    pg.locator("#pb_res div").first.click(); pg.wait_for_timeout(300)
    check("patient linked", pg.locator("#pb_sel").is_visible())
    pg.click("#cs_gen"); pg.wait_for_timeout(2500)  # transliteration falls back offline
    out = pg.locator("#cs_out").inner_text()
    check("consent generated", len(out) > 400)
    check("polio heading in consent", "विशेष स्थिति" in out and "पोलियो" in out)
    check("polio paragraphs in consent", "पोलियो-प्रभावित" in out)
    pg.click("#caseSave"); pg.wait_for_timeout(600)
    check("save posted", len(SAVED) == 1)
    bnd = SAVED[0] if SAVED else {}
    check("bundle has stage", bnd.get("stage") in (1, 2))
    check("bundle has polio", (bnd.get("consent") or {}).get("polio", {}).get("on") is True)
    check("save msg shows consent verdict", "c1 issued" in (pg.locator("#caseSaveMsg").inner_text() or ""))
    pg.click("#cs_hist"); pg.wait_for_timeout(500)
    check("consent history renders", "Consent history" in (pg.locator("#cs_hist_panel").inner_text() or ""))
    b.close()
print("%d/%d render checks passed" % (N[1], N[0]))
sys.exit(0 if N[0] == N[1] else 1)
