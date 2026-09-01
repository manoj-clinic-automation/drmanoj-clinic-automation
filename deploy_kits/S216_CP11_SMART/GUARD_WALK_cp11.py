#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUARD_WALK_cp11.py — CP-1.1 step 1, the LIVE-SHAPE walk (S216)
==============================================================
Reproduces the ACTUAL S215 failure in a real browser and proves the guard
catches it — then proves it does NOT fire on a correct elective consent.

The S215 render test could never have caught this: it calls
    pg.select_option("#cs_proc", "thrneck")
i.e. it hand-picks the right template. 17/17 green, defect untouched.

Exit 0 green · 2 = playwright unavailable (SKIP).
"""
import os, json, sys, threading
BASE = os.path.dirname(os.path.abspath(__file__))
try:
    from playwright.sync_api import sync_playwright
except Exception:
    print("SKIP: playwright not available here"); sys.exit(2)
from http.server import BaseHTTPRequestHandler, HTTPServer

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _j(self, o, c=200):
        b=json.dumps(o).encode(); self.send_response(c)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path.startswith("/portal/casepack/search"): self._j({"ok":True,"matches":[]}); return
        if self.path.startswith("/portal/casepack/consents/"): self._j({"ok":True,"rows":[]}); return
        b=open(os.path.join(BASE,"casepack_page.html"),"rb").read()
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_POST(self): self._j({"ok":True,"case_id":"C-1","version":1,"folder":"x","files":[],
        "consent":{"no":1,"kind":"new","hash8":"d","issue_date":"2026-09-01"}})

N=[0,0]
def check(name, ok):
    N[0]+=1
    if ok: N[1]+=1; print("  ok  "+name)
    else:  print("FAIL  "+name)

srv=HTTPServer(("127.0.0.1",0),H); port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()

with sync_playwright() as pw:
    b=pw.chromium.launch(); pg=b.new_page(); pg.on("dialog", lambda d: d.accept())
    pg.goto("http://127.0.0.1:%d/portal/casepack"%port, wait_until="load"); pg.wait_for_timeout(500)
    pg.click('#cpStepper .cpstep[data-st="2"]'); pg.wait_for_timeout(300)
    pg.click('#caseSub button[data-s="consent"]'); pg.wait_for_timeout(200)
    pg.fill("#c_name","TEST NAAM"); pg.fill("#c_age","62")

    # ---------- 1 · the S215 case, exactly as it happened ----------
    print("\n-- A · the S215 failure reproduced --")
    pg.select_option("#cs_proc","thr")                 # what cpGuessProc() returned
    pg.check("#cs_polio"); pg.wait_for_timeout(150)
    pg.select_option("#cs_polio_proc","thr_fnf")       # fracture neck of femur
    pg.wait_for_timeout(300)
    check("strip is visible", pg.locator("#cp11_strip").is_visible())
    strip = pg.locator("#cp11_strip").inner_text()
    check("strip names the mismatch", "does not match" in strip)
    check("strip names the polio evidence", "polio module" in strip)
    pg.click("#cs_gen"); pg.wait_for_timeout(2500)
    check("GENERATION REFUSED (cs_out stays hidden)", not pg.locator("#cs_out").is_visible())

    # ---------- 2 · one click puts it right ----------
    print("\n-- B · the offered correction --")
    btns = pg.locator("#cp11_strip button")
    check("correct templates offered", btns.count() >= 4)
    pg.locator('#cp11_strip button:has-text("गर्दन फ्रैक्चर")').first.click(); pg.wait_for_timeout(400)
    check("procedure switched to thrneck", pg.locator("#cs_proc").input_value()=="thrneck")
    check("strip turns green", "Fracture case" in pg.locator("#cp11_strip").inner_text())
    pg.click("#cs_gen"); pg.wait_for_timeout(2500)
    out = pg.locator("#cs_out").inner_text()
    check("consent now generates", pg.locator("#cs_out").is_visible() and len(out)>400)
    check("and it says the bone is BROKEN", "टूट गई है" in out)
    check("and it names the neck", "गर्दन" in out)
    check("polio module still printed", "पोलियो-प्रभावित" in out)

    # ---------- 3 · fracture panel, no polio ----------
    print("\n-- C · fracture modules alone must also trip it --")
    pg.uncheck("#cs_polio"); pg.select_option("#cs_proc","thr")
    pg.check("#fm_seg"); pg.wait_for_timeout(300)
    check("segmental fracture trips the guard", "does not match" in pg.locator("#cp11_strip").inner_text())
    pg.uncheck("#fm_seg"); pg.wait_for_timeout(250)

    # ---------- 4 · the override is possible and is RECORDED ----------
    print("\n-- D · override, never silent --")
    pg.check("#fm_seg"); pg.wait_for_timeout(300)
    pg.locator('#cp11_strip button:has-text("generate anyway")').first.click(); pg.wait_for_timeout(2600)
    check("override generates the consent", pg.locator("#cs_out").is_visible())
    note = pg.locator("#cs_change_note").input_value()
    check("override written into the change note", "opening-guard overridden: thr" in note)
    pg.uncheck("#fm_seg"); pg.fill("#cs_change_note",""); pg.wait_for_timeout(250)

    # ---------- 5 · FALSE-POSITIVE CONTROL ----------
    print("\n-- E · it must NOT fire on a correct elective consent --")
    pg.evaluate("window.cp11Ok=null")
    pg.select_option("#cs_proc","thr"); pg.wait_for_timeout(300)
    check("plain elective THR: no block", "does not match" not in pg.locator("#cp11_strip").inner_text())
    pg.check("#fm_osteo"); pg.check("#fm_geri"); pg.wait_for_timeout(300)
    check("osteoporosis + geriatric on a THR: still no block",
          "does not match" not in pg.locator("#cp11_strip").inner_text())
    pg.click("#cs_gen"); pg.wait_for_timeout(2500)
    out2 = pg.locator("#cs_out").inner_text()
    check("elective consent generates normally", pg.locator("#cs_out").is_visible() and len(out2)>400)
    check("and it reads as a worn-out joint", "खराब हो चुका" in out2)
    pg.uncheck("#fm_osteo"); pg.uncheck("#fm_geri")

    # ---------- 6 · a fracture template is never blocked ----------
    print("\n-- F · fracture templates are never blocked --")
    pg.select_option("#cs_proc","itfix")
    pg.check('#fmGrid input[name="fm_comm"][value="c1"]'); pg.wait_for_timeout(300)
    check("PFN + comminution: no block", "does not match" not in pg.locator("#cp11_strip").inner_text())
    pg.check('#fmGrid input[name="fm_comm"][value=""]')
    b.close()

print("\n%d/%d guard-walk checks passed"%(N[1],N[0]))
sys.exit(0 if N[0]==N[1] else 1)
