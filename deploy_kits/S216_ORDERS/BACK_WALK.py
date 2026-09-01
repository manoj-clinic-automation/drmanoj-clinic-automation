#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BACK_WALK.py - S216: prove there is a way back from stage 2.
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

TOPMOST = """()=>{const el=document.querySelector('#cpStepper .cpstep[data-st="1"]');
 if(!el) return 'no-stepper';
 const r=el.getBoundingClientRect();
 const hit=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2);
 return (hit && (hit===el || el.contains(hit))) ? 'clickable' : ('covered-by:'+(hit?hit.id||hit.className:'null'));}"""

with sync_playwright() as pw:
    b=pw.chromium.launch(); pg=b.new_page(); pg.set_viewport_size({"width":900,"height":900})
    pg.on("dialog",lambda d:d.accept())
    pg.goto("http://127.0.0.1:%d/portal/casepack"%port,wait_until="load"); pg.wait_for_timeout(400)

    check("stage 1: stepper is clickable", pg.evaluate(TOPMOST)=="clickable")
    pg.click('#cpStepper .cpstep[data-st="2"]'); pg.wait_for_timeout(500)
    check("stage 2 opened", "open" in (pg.locator("#caseModal").get_attribute("class") or ""))
    check("body carries the modal class", "cpmodal" in (pg.locator("body").get_attribute("class") or ""))

    st=pg.evaluate(TOPMOST)
    check("stage 2: the way back is REACHABLE, not buried", st=="clickable", st)
    check("and it is pinned to the top of the screen",
          pg.evaluate("()=>Math.round(document.querySelector('#cpStepper').getBoundingClientRect().top)")==0)
    # measured at three widths - the bar wraps on a phone
    for w in (900,560,420):
        pg.set_viewport_size({"width":w,"height":900}); pg.wait_for_timeout(350)
        r=pg.evaluate("""()=>{const s=document.querySelector('#cpStepper').getBoundingClientRect();
            const m=document.querySelector('#caseModal .mbox').getBoundingClientRect();
            return {gap:Math.round(m.top-s.bottom), barH:Math.round(s.height)};}""")
        check("nothing hidden behind the bar at %dpx"%w, r["gap"]>=0,
              "bar %dpx, clear by %dpx"%(r["barH"],r["gap"]))
    pg.set_viewport_size({"width":900,"height":900}); pg.wait_for_timeout(300)

    pg.click('#cpStepper .cpstep[data-st="1"]'); pg.wait_for_timeout(400)
    check("one click returns to stage 1", "open" not in (pg.locator("#caseModal").get_attribute("class") or ""))
    check("and the bar releases", "cpmodal" not in (pg.locator("body").get_attribute("class") or ""))
    check("stage 1 is marked active again",
          "on" in (pg.locator('#cpStepper .cpstep[data-st="1"]').get_attribute("class") or ""))

    # the old exit must still work
    pg.click('#cpStepper .cpstep[data-st="2"]'); pg.wait_for_timeout(400)
    pg.click("#closeCase"); pg.wait_for_timeout(400)
    check("the original Close button still works",
          "open" not in (pg.locator("#caseModal").get_attribute("class") or "")
          and "cpmodal" not in (pg.locator("body").get_attribute("class") or ""))
    b.close()
print("\n%d/%d back-navigation checks passed"%(N[1],N[0]))
sys.exit(0 if N[0]==N[1] else 1)
