#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Proves the S215 defect IS present in the live page — so the guard is not
   guarding against nothing. Run against casepack_page.html in this folder."""
import os,json,sys,threading
BASE=os.path.dirname(os.path.abspath(__file__))
from playwright.sync_api import sync_playwright
from http.server import BaseHTTPRequestHandler,HTTPServer
class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def _j(self,o):
        b=json.dumps(o).encode(); self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if "/search" in self.path or "/consents/" in self.path: self._j({"ok":True,"matches":[],"rows":[]}); return
        b=open(os.path.join(BASE,"casepack_page.html"),"rb").read()
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_POST(self): self._j({"ok":True})
srv=HTTPServer(("127.0.0.1",0),H); port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
with sync_playwright() as pw:
    b=pw.chromium.launch(); pg=b.new_page(); pg.on("dialog",lambda d:d.accept())
    pg.goto("http://127.0.0.1:%d/portal/casepack"%port,wait_until="load"); pg.wait_for_timeout(500)
    pg.click('#cpStepper .cpstep[data-st="2"]'); pg.wait_for_timeout(300)
    pg.click('#caseSub button[data-s="consent"]'); pg.wait_for_timeout(200)
    pg.fill("#c_name","TEST NAAM"); pg.fill("#c_age","62")
    pg.select_option("#cs_proc","thr")
    pg.check("#cs_polio"); pg.wait_for_timeout(150)
    pg.select_option("#cs_polio_proc","thr_fnf"); pg.wait_for_timeout(200)
    pg.click("#cs_gen"); pg.wait_for_timeout(2500)
    vis=pg.locator("#cs_out").is_visible(); out=pg.locator("#cs_out").inner_text() if vis else ""
    print("consent GENERATED with no objection :", vis)
    print("opening says 'worn out joint'       :", "खराब हो चुका" in out)
    print("opening says 'broken bone'          :", "टूट गई है" in out)
    print("polio module says fracture neck     :", "पोलियो-प्रभावित" in out)
    print()
    i=out.find("हमारे मरीज"); print("--- opening paragraph as printed ---"); print(out[i:i+300] if i>=0 else out[:300])
    b.close()
