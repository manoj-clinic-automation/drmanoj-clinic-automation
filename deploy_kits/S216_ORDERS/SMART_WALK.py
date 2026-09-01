#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SMART_WALK.py - CP-1.1 steps 3 and 5 proof (S216).
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

with sync_playwright() as pw:
    b=pw.chromium.launch(); pg=b.new_page(); pg.on("dialog",lambda d:d.accept())
    pg.goto("http://127.0.0.1:%d/portal/casepack"%port,wait_until="load"); pg.wait_for_timeout(400)
    pg.click('#cpStepper .cpstep[data-st="2"]'); pg.wait_for_timeout(300)
    pg.click('#caseSub button[data-s="consent"]'); pg.wait_for_timeout(200)
    pg.fill("#c_name","TEST NAAM"); pg.fill("#c_age","62")

    print("\n-- STEP 3 · the guess reads the case --")
    check("clean elective THR still guesses thr",
          pg.evaluate("()=>cpGuessProc('Total Hip Replacement')")=="thr")
    pg.check("#cs_polio"); pg.wait_for_timeout(150)
    pg.select_option("#cs_polio_proc","thr_fnf"); pg.wait_for_timeout(250)
    check("same title + polio fracture module now guesses thrneck",
          pg.evaluate("()=>cpGuessProc('Total Hip Replacement')")=="thrneck")
    check("the evidence is named, not silent",
          len(pg.evaluate("()=>cpNeckEvidence()"))>0, str(pg.evaluate("()=>cpNeckEvidence()")))
    pg.uncheck("#cs_polio"); pg.wait_for_timeout(200)
    check("evidence clears when the module is unticked",
          pg.evaluate("()=>cpGuessProc('Total Hip Replacement')")=="thr")
    pg.check('#fmGrid input[name="fm_comm"][value="c1"]'); pg.wait_for_timeout(250)
    check("fracture panel alone also flips it",
          pg.evaluate("()=>cpGuessProc('Total Hip Replacement')")=="thrneck")
    check("A KNEE replacement is NEVER auto-changed (clinical choice stays his)",
          pg.evaluate("()=>cpGuessProc('Total Knee Replacement')")=="tkr")
    check("nor is a PFN or a fixation guess disturbed",
          pg.evaluate("()=>cpGuessProc('PFN intertrochanteric')")=="itfix")
    pg.check('#fmGrid input[name="fm_comm"][value=""]'); pg.wait_for_timeout(200)

    print("\n-- STEP 5 · transliteration --")
    r=pg.evaluate("()=>{TR_GUESSED=[];return csHindi('Bareilly').then(h=>({h:h,g:TR_GUESSED.slice()}));}")
    check("Bareilly comes from the dictionary, spelled right", r["h"]=="बरेली", r["h"])
    check("and is NOT flagged as a guess", r["g"]==[], str(r["g"]))
    r=pg.evaluate("()=>{TR_GUESSED=[];return csHindi('Nawabganj').then(h=>({h:h,g:TR_GUESSED.slice()}));}")
    check("Nawabganj too", r["h"]=="नवाबगंज", r["h"])
    r=pg.evaluate("()=>{TR_GUESSED=[];return csHindi('Shahjahanpur').then(h=>({h:h,g:TR_GUESSED.slice()}));}")
    check("Shahjahanpur too", r["h"]=="शाहजहाँपुर", r["h"])
    sfx=pg.evaluate("()=>trLocalWord('Bareillyganj')")
    check("a KNOWN stem + suffix is exact, not a guess",
          sfx[0]=="बरेलीगंज" and sfx[1] is False, str(sfx))
    sfx2=pg.evaluate("()=>trLocalWord('Qwertyxyzganj')")
    check("an UNKNOWN stem still gets its suffix right", sfx2[0].endswith("गंज"), str(sfx2))
    check("and is marked as a guess", sfx2[1] is True)
    warn=pg.evaluate("()=>{TR_GUESSED=[];trLocal('Qwertypatti',true);return trWarnHTML();}")
    check("a guessed word produces the amber warning", "Qwertypatti" in warn and "जाँच" in warn)
    check("no guess produces NO warning",
          pg.evaluate("()=>{TR_GUESSED=[];return trWarnHTML();}")=="")

    print("\n-- STEP 5 · the warning on the real screen --")
    # the NAME is transliterated too, so it is set in Hindi here to isolate the address
    pg.fill("#c_name","टेस्ट नाम")
    pg.fill("#cs_res","Bareilly"); pg.select_option("#cs_proc","thrneck")
    pg.click("#cs_gen"); pg.wait_for_timeout(2600)
    check("dictionary address: consent generated, no amber warning",
          pg.locator("#cs_out").is_visible() and pg.locator("#cp11_trwarn").inner_text().strip()=="")
    check("and the address is spelled correctly in the consent",
          "बरेली" in pg.locator("#cs_out").inner_text())
    pg.fill("#cs_res","Qwertypatti"); pg.wait_for_timeout(150)
    pg.click("#cs_gen"); pg.wait_for_timeout(3200)
    wtxt=pg.locator("#cp11_trwarn").inner_text()
    check("guessed address: the amber warning APPEARS", "Qwertypatti" in wtxt, wtxt[:70])
    pg.fill("#cs_res","Bareilly"); pg.wait_for_timeout(150)
    pg.click("#cs_gen"); pg.wait_for_timeout(2600)
    check("and it CLEARS on the next clean generate",
          pg.locator("#cp11_trwarn").inner_text().strip()=="")
    # a Latin patient NAME can never be in a place dictionary - it must warn
    pg.fill("#c_name","TEST NAAM"); pg.wait_for_timeout(150)
    pg.click("#cs_gen"); pg.wait_for_timeout(3200)
    check("a Latin-typed PATIENT NAME also raises the warning",
          "TEST" in pg.locator("#cp11_trwarn").inner_text())
    b.close()
print("\n%d/%d smart-walk checks passed"%(N[1],N[0]))
sys.exit(0 if N[0]==N[1] else 1)
