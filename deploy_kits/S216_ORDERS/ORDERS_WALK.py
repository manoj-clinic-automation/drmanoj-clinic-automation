#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ORDERS_WALK.py - S216 orders build, page side, in a real browser.
Exit 0 green - 2 = playwright unavailable (SKIP)."""
import os,json,sys,threading
BASE=os.path.dirname(os.path.abspath(__file__))
try: from playwright.sync_api import sync_playwright
except Exception: print("SKIP: playwright not available here"); sys.exit(2)
from http.server import BaseHTTPRequestHandler,HTTPServer
MEDS=[
 {"Item":"5% DNS","Route":"IV","Freq":"","Ayushman":"","Package":"","Active":"1","Sort":"10"},
 {"Item":"NS","Route":"IV","Freq":"","Ayushman":"","Package":"","Active":"1","Sort":"11"},
 {"Item":"Inj Pantawin 40","Route":"IV","Freq":"OD","Ayushman":"","Package":"","Active":"1","Sort":"20"},
 {"Item":"Inj Vinbactum DS","Route":"IV","Freq":"BD","Ayushman":"","Package":"","Active":"1","Sort":"30"},
 {"Item":"Inj Q Bact 1.5","Route":"IV","Freq":"BD","Ayushman":"1","Package":"","Active":"1","Sort":"31"},
 {"Item":"Inj Butrum 2 Mg","Route":"IM","Freq":"SOS","Ayushman":"","Package":"","Active":"1","Sort":"50"},
]
SAVED=[]
class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def _j(self,o):
        b=json.dumps(o).encode(); self.send_response(200)
        self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(b)))
        self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if "/meds" in self.path: self._j({"ok":True,"rows":MEDS}); return
        if "/search" in self.path or "/consents/" in self.path: self._j({"ok":True,"matches":[],"rows":[]}); return
        b=open(os.path.join(BASE,"casepack_page.html"),"rb").read()
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        n=int(self.headers.get("Content-Length") or 0)
        body=json.loads(self.rfile.read(n) or b"{}")
        if "/meds" in self.path:
            SAVED.append(body); self._j({"ok":True,"count":len(body.get("rows",[]))}); return
        self._j({"ok":True})
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
    pg.click('#cpStepper .cpstep[data-st="2"]'); pg.wait_for_timeout(600)

    print("\n-- A · one time in, every time out --")
    pg.click('#caseSub button[data-s="preop"]'); pg.wait_for_timeout(200)
    pg.fill("#op_date","2026-09-03"); pg.fill("#op_time","09:00"); pg.wait_for_timeout(300)
    d=pg.locator("#op_derived").inner_text()
    check("nil orally FROM is surgery minus 6 hours", "from 03:00" in d, d)
    check("nil orally TILL is that time plus 13 hours", "till 16:00" in d, d)
    pg.click("#preop_build"); pg.wait_for_timeout(250)
    pre=pg.locator("#preop_tx").input_value()
    check("pre-op sheet carries the computed time", "Nil Orally From 03:00" in pre)
    check("and says why", "(6 Hours Before Surgery)" in pre)
    check("and the surgery date reads dd/mm/yyyy", "03/09/2026" in pre)
    check("his three lines, in his order",
          pre.index("Nil Orally")<pre.index("Consent To Be Taken")<pre.index("Shifted To OT"))

    print("\n-- B · a midnight case must not print a wrong day --")
    pg.fill("#op_time","04:00"); pg.wait_for_timeout(300)
    d2=pg.locator("#op_derived").inner_text()
    check("a pre-dawn surgery says 'previous day' for the nil-orally time",
          "22:00 (previous day)" in d2, d2)
    pg.fill("#op_time","09:00"); pg.wait_for_timeout(300)

    print("\n-- C · post-op: his numbering, his medicines --")
    pg.click('#caseSub button[data-s="postop"]'); pg.wait_for_timeout(400)
    check("the medicine list loaded from the server", pg.locator("#med_pick label").count()>0)
    check("IV fluids sit in their own group", pg.locator("#med_fluid label").count()==2)
    pg.locator("#med_fluid input").first.check()
    for i in range(pg.locator("#med_pick input").count()):
        pg.locator("#med_pick input").nth(i).check()
    pg.locator('#mon_pick input[data-mon="4"]').check()      # RBS 8 hourly
    pg.click("#postop_build"); pg.wait_for_timeout(300)
    po=pg.locator("#postop_tx").input_value()
    check("IV FLUID IS ITEM 1 (his ruling)", "1. IV Fluid" in po, po.split("\n")[3] if len(po.split("\n"))>3 else po[:60])
    check("nil orally till is item 2 and uses the computed time", "2. Nil Orally Till 16:00" in po)
    check("medicines are numbered on from there, no duplicate numbers",
          "3. " in po and po.count("\n5. ")<=1)
    check("route and frequency print with the medicine", "IV BD" in po or "IM SOS" in po)
    check("the RBS line he asked for is there", "RBS By Glucometer 8 Hourly" in po)
    check("monitoring is its own block", "Monitoring:" in po)

    print("\n-- D · Ayushman marking floats to the top, hides nothing --")
    before=pg.locator("#med_pick label").count()
    pg.evaluate("()=>{window.cpPayer='ayush'; medRender();}"); pg.wait_for_timeout(250)
    first=pg.locator("#med_pick label").first.inner_text()
    check("the marked medicine is now first", "Q Bact" in first, first)
    check("and NOTHING was hidden", pg.locator("#med_pick label").count()==before)
    check("the mark is visible on the row", pg.locator("#med_pick .mk.a").count()>0)
    pg.evaluate("()=>{window.cpPayer='cash'; medRender();}"); pg.wait_for_timeout(200)

    print("\n-- E · the list is his to edit, and saving is guarded --")
    pg.click("#med_edit"); pg.wait_for_timeout(250)
    check("the editor opens", pg.locator("#med_editor").is_visible())
    pg.fill("#med_new","inj new test"); pg.select_option("#med_new_route","IV")
    pg.select_option("#med_new_freq","TDS"); pg.click("#med_add"); pg.wait_for_timeout(250)
    check("a new medicine is added in Title Case",
          "Inj New Test" in pg.locator("#med_rows").inner_text())
    pg.click("#med_save"); pg.wait_for_timeout(600)
    check("it posted to the server", len(SAVED)==1 and len(SAVED[0]["rows"])==7, str(len(SAVED)))
    check("and the server was told about the mark",
          any(r.get("Ayushman")=="1" for r in SAVED[0]["rows"]))

    print("\n-- F · OT note --")
    pg.click('#caseSub button[data-s="opnote"]'); pg.wait_for_timeout(300)
    pg.fill("#ot_dx","Fracture Neck Of Femur Right")
    pg.fill("#ot_sx","Total Hip Replacement")
    pg.click("#opnote_build"); pg.wait_for_timeout(250)
    ot=pg.locator("#opnote_tx").input_value()
    check("only the two header fields he asked for", "Diagnosis:" in ot and "Surgery Done:" in ot)
    check("and nothing he removed", "Anaesthesia:" not in ot and "Tourniquet" not in ot and "Blood Loss" not in ot)
    check("his own five lines are the body",
          "Painting And Draping Done" in ot and "Closure Done In Layers" in ot)
    check("his qualification signs it", "(M.S. Ortho)" in ot)
    b.close()
print("\n%d/%d orders-walk checks passed"%(N[1],N[0]))
sys.exit(0 if N[0]==N[1] else 1)
