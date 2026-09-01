#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CONTRAST_TEST_cp11.py - CP-1.1 step 2 proof (S216).
Measures real computed colours in a real browser. Contrast is exactly the thing
a pass/fail check cannot see, so this MEASURES ratios rather than asserting a
string is present. Exit 0 green - 2 = playwright unavailable (SKIP)."""
import os,json,sys,threading
BASE=os.path.dirname(os.path.abspath(__file__))
try: from playwright.sync_api import sync_playwright
except Exception: print("SKIP: playwright not available here"); sys.exit(2)
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
N=[0,0]
def check(n_,ok,note=""):
    N[0]+=1
    if ok: N[1]+=1; print("  ok  "+n_+("  "+note if note else ""))
    else:  print("FAIL  "+n_+("  "+note if note else ""))
srv=HTTPServer(("127.0.0.1",0),H); port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()

RATIO = r"""(sel)=>{
  function rgb(s){const m=s.match(/\d+(\.\d+)?/g)||[0,0,0];return [+m[0],+m[1],+m[2],m[3]===undefined?1:+m[3]];}
  function lum(c){const f=c.slice(0,3).map(v=>{v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);});
    return 0.2126*f[0]+0.7152*f[1]+0.0722*f[2];}
  const el=document.querySelector(sel); if(!el) return null;
  const cs=getComputedStyle(el);
  let bg=rgb(cs.backgroundColor), fg=rgb(cs.color);
  let p=el.parentElement;
  while(bg[3]===0 && p){ const pb=rgb(getComputedStyle(p).backgroundColor); if(pb[3]!==0){bg=pb;break;} p=p.parentElement; }
  if(bg[3]===0) bg=[255,255,255,1];              // what the browser falls back to
  const L1=lum(fg),L2=lum(bg);
  const r=(Math.max(L1,L2)+0.05)/(Math.min(L1,L2)+0.05);
  return {fg:cs.color,bg:cs.backgroundColor,effBg:'rgb('+bg.slice(0,3).join(',')+')',
          ratio:Math.round(r*100)/100, scheme:cs.colorScheme};
}"""

with sync_playwright() as pw:
    b=pw.chromium.launch(); pg=b.new_page(); pg.on("dialog",lambda d:d.accept())
    pg.goto("http://127.0.0.1:%d/portal/casepack"%port,wait_until="load"); pg.wait_for_timeout(500)

    html_scheme=pg.evaluate("getComputedStyle(document.documentElement).colorScheme")
    check("html color-scheme is dark", html_scheme=="dark", "("+str(html_scheme)+")")

    pg.click('#cpStepper .cpstep[data-st="2"]'); pg.wait_for_timeout(300)
    pg.click('#caseSub button[data-s="consent"]'); pg.wait_for_timeout(250)

    for label,sel in [("body-part dropdown","#c_part option:nth-child(2)"),
                      ("bone dropdown","#c_bone option"),
                      ("procedure dropdown","#cs_proc option"),
                      ("duration dropdown","#cs_dur option:nth-child(2)"),
                      ("polio procedure dropdown","#cs_polio_proc option")]:
        r=pg.evaluate(RATIO,sel)
        ok = r is not None and r["ratio"]>=4.5
        check("readable: "+label, ok, "" if r is None else "ratio %.2f  text %s on %s"%(r["ratio"],r["fg"],r["effBg"]))

    pg.click('#caseSub button[data-s="preop"]'); pg.wait_for_timeout(250)
    r=pg.evaluate(RATIO,"#preop_tx")
    check("readable: pre-op template box", r and r["ratio"]>=4.5, "" if not r else "ratio %.2f"%r["ratio"])

    # the consent paper must stay a light document
    pg.click('#caseSub button[data-s="consent"]'); pg.wait_for_timeout(200)
    pg.fill("#c_name","TEST NAAM"); pg.fill("#c_age","62")
    pg.select_option("#cs_proc","thrneck"); pg.wait_for_timeout(200)
    pg.click("#cs_gen"); pg.wait_for_timeout(2500)
    r=pg.evaluate(RATIO,"#cs_out")
    check("consent paper still black on white", r and r["ratio"]>=15,
          "" if not r else "ratio %.2f  %s on %s  scheme=%s"%(r["ratio"],r["fg"],r["effBg"],r["scheme"]))

    # printing must revert to light
    pg.emulate_media(media="print"); pg.wait_for_timeout(200)
    pr=pg.evaluate("()=>({root:getComputedStyle(document.documentElement).colorScheme,"
                   "body:getComputedStyle(document.body).backgroundColor})")
    check("print media reverts to light", pr["root"].find("light")>=0, str(pr))
    pg.emulate_media(media="screen")

    pg.screenshot(path="shot_consent_pane.png", full_page=False)
    pg.click('#caseSub button[data-s="preop"]'); pg.wait_for_timeout(300)
    pg.screenshot(path="shot_preop_pane.png", full_page=False)
    b.close()
print("\n%d/%d contrast checks passed"%(N[1],N[0]))
sys.exit(0 if N[0]==N[1] else 1)
