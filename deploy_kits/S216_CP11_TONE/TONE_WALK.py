#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TONE_WALK.py - CP-1.1 step 4 proof (S216): flow, tone, language switch.
Exit 0 green - 2 = playwright unavailable (SKIP)."""
import os,json,sys,threading
BASE=os.path.dirname(os.path.abspath(__file__))
try: from playwright.sync_api import sync_playwright
except Exception: print("SKIP: playwright not available here"); sys.exit(2)
from http.server import BaseHTTPRequestHandler,HTTPServer
class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def _j(self,o):
        b=json.dumps(o).encode(); self.send_response(200)
        self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(b)))
        self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if "/search" in self.path or "/consents/" in self.path: self._j({"ok":True,"matches":[],"rows":[]}); return
        b=open(os.path.join(BASE,"casepack_page.html"),"rb").read()
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_POST(self): self._j({"ok":True})
N=[0,0]
def check(n_,ok,note=""):
    N[0]+=1
    if ok: N[1]+=1; print("  ok  "+n_+("  "+note if note else ""))
    else:  print("FAIL  "+n_+("  "+note if note else ""))
srv=HTTPServer(("127.0.0.1",0),H); port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()

LATIN = "()=>{const t=document.querySelector('#cs_out').innerText;" \
        "return (t.match(/[A-Za-z]{2,}/g)||[]);}"

with sync_playwright() as pw:
    b=pw.chromium.launch(); pg=b.new_page(); pg.on("dialog",lambda d:d.accept())
    pg.goto("http://127.0.0.1:%d/portal/casepack"%port,wait_until="load"); pg.wait_for_timeout(400)
    pg.click('#cpStepper .cpstep[data-st="2"]'); pg.wait_for_timeout(300)
    pg.click('#caseSub button[data-s="consent"]'); pg.wait_for_timeout(200)
    pg.fill("#c_name","टेस्ट नाम"); pg.fill("#c_age","62")

    print("\n-- A · the switch --")
    check("switch is on screen", pg.locator("#cs_langbar .cslang").count()==2)
    check("it starts on हिंदी every time (owner ruling: no memory)",
          pg.evaluate("()=>window.csLang")=="hi")

    print("\n-- B · Hindi-only print --")
    pg.select_option("#cs_proc","thrneck")
    pg.check("#cs_polio"); pg.wait_for_timeout(150)
    pg.select_option("#cs_polio_proc","thr_fnf"); pg.wait_for_timeout(200)
    pg.click("#cs_gen"); pg.wait_for_timeout(2600)
    out=pg.locator("#cs_out").inner_text()
    latin=pg.evaluate(LATIN)
    # the doctor's own name and qualification are deliberate English chrome
    body=[w for w in latin if w not in ("Ortho","Dr","M","S","Manoj","Agarwal")]
    check("consent generated", pg.locator("#cs_out").is_visible() and len(out)>500)
    check("the bold polio heading is GONE", pg.locator("#cs_out h3.cs-mod").count()==0)
    check("the polio text prints as flowing paragraphs",
          "उसी पैर में पोलियो का असर है" in out and "सब कुछ अच्छी तरह समझकर" in out)
    check("NO English words left in the consent body", body==[], str(body[:8]))
    check("the doctor's own qualification SURVIVES (M.S. Ortho)", "Ortho" in out)
    check("bracketed glosses are gone", "(dislocation)" not in out and "hip precautions" not in out)
    check("implant is Devanagari now", "इम्प्लांट" in out and " implant " not in out)
    # the MRI line lives in the ELECTIVE hip template, not the fracture one
    pg.uncheck("#cs_polio"); pg.select_option("#cs_proc","thr"); pg.wait_for_timeout(200)
    pg.click("#cs_gen"); pg.wait_for_timeout(2600)
    oe=pg.locator("#cs_out").inner_text()
    check("owner's MRI wording is in", "एमआरआई" in oe and "MRI" not in oe)
    eb=[w for w in pg.evaluate(LATIN) if w not in ("Ortho","Dr","M","S","Manoj","Agarwal")]
    check("elective template also prints no English", eb==[], str(eb[:8]))
    pg.select_option("#cs_proc","thrneck"); pg.check("#cs_polio"); pg.wait_for_timeout(200)
    pg.click("#cs_gen"); pg.wait_for_timeout(2600)
    out=pg.locator("#cs_out").inner_text()
    check("no empty brackets or stray spaces left behind",
          "()" not in out and " ।" not in out and "  " not in out)

    print("\n-- C · Hindi + English print --")
    pg.click('#cs_langbar .cslang[data-lang="hien"]'); pg.wait_for_timeout(2800)
    out2=pg.locator("#cs_out").inner_text()
    check("the English comes back", "dislocation" in out2 or "hip precautions" in out2)
    check("and the Hindi is unchanged", "उसी पैर में पोलियो का असर है" in out2)
    check("switching back removes it again",
          (pg.click('#cs_langbar .cslang[data-lang="hi"]'), pg.wait_for_timeout(2800),
           "dislocation" not in pg.locator("#cs_out").inner_text())[2])

    print("\n-- D · the store was never edited --")
    check("the template still holds the English, untouched",
          pg.evaluate("()=>CONSENT_LIB.find(x=>x.k==='thr').r.join(' ')").find("dislocation")>=0)
    b.close()
print("\n%d/%d tone-walk checks passed"%(N[1],N[0]))
sys.exit(0 if N[0]==N[1] else 1)
