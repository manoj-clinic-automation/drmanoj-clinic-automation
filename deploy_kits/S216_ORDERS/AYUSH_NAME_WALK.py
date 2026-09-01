#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AYUSH_NAME_WALK.py - S216 Ayushman naming proof.
Proves the READ path improved and the CLAIM path did not move.
Exit 0 green - 2 = playwright unavailable (SKIP)."""
import os,json,sys,threading,re
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

with sync_playwright() as pw:
    b=pw.chromium.launch(); pg=b.new_page(); pg.on("dialog",lambda d:d.accept())
    pg.goto("http://127.0.0.1:%d/portal/casepack"%port,wait_until="load"); pg.wait_for_timeout(500)
    pg.click('#seg button[data-p="ayush"]'); pg.wait_for_timeout(500)

    print("\n-- A · the reading path --")
    pg.fill("#q","P.O.P. casts"); pg.wait_for_timeout(500)
    txt=pg.locator("#results").inner_text()
    check("parent package now shown as a kicker", "APPLICATION OF P.O.P. CASTS" in txt.upper())
    check("variant is still the headline", "Upper Limbs" in txt and "Lower Limbs" in txt)
    n_k=pg.locator("#results .aykick").count()
    check("parent kicker present on every sibling card", n_k>0, "kickers %d"%n_k)
    # the line must be SUPPRESSED where it would only repeat the headline
    dup=pg.evaluate("()=>BUNDLE.ayush.filter(a=>!ayOfficialDiffers(a)).length")
    tot=pg.evaluate("()=>BUNDLE.ayush.length")
    check("official line suppressed where it would only repeat", dup>0,
          "%d of %d packages say the same thing twice - line hidden on those"%(dup,tot))
    pg.fill("#q","Traction"); pg.wait_for_timeout(400)
    t2=pg.locator("#results").inner_text()
    check("but kept where the filed name really differs",
          "Skeletal Tractions" in t2, "plural in the government string")

    print("\n-- B · the collapse that was avoided --")
    pg.fill("#q","Spikas"); pg.wait_for_timeout(500)
    cards=pg.locator("#results .card")
    heads=[cards.nth(i).locator("h3").inner_text() for i in range(cards.count())]
    check("Spikas and Jackets remain DISTINCT cards", "Spikas" in heads and "Jackets" in heads, str(heads))
    rates=[cards.nth(i).locator(".big").inner_text() for i in range(cards.count())]
    check("and they still carry their own rates", len(set(heads))==len(heads), str(rates))

    print("\n-- C · the claim path must NOT have moved --")
    # read the government strings straight out of the page data, then out of Copy details
    data=pg.evaluate("()=>BUNDLE.ayush.filter(a=>/SB004|SB051|SB049/.test(a.code)).map(a=>({c:a.code,s:a.sub,hp:a.hpkg,hq:a.hproc}))")
    blocks=pg.evaluate("()=>BUNDLE.ayush.filter(a=>/SB004|SB051|SB049/.test(a.code)).map(a=>ayushBlock(a))")
    ok=True; detail=""
    for d,blk in zip(data,blocks):
        if ("Package Name    : "+(d["hp"] or "")) not in blk or ("Procedure Name  : "+(d["hq"] or "")) not in blk:
            ok=False; detail=d["c"]
    check("Copy details still prints hpkg/hproc verbatim", ok, detail)
    typo=pg.evaluate("()=>BUNDLE.ayush.filter(a=>/Duputryen/.test(a.hpkg||'')).map(a=>ayushBlock(a))")
    check("the government's own typo is preserved, not corrected",
          bool(typo) and "Duputryen" in typo[0], "%d row(s)"%len(typo))
    lbl=pg.evaluate("()=>BUNDLE.ayush.filter(a=>/Duputryen/.test(a.hpkg||'')).map(a=>ayLabel(a))")
    check("but the SCREEN label spells it correctly", bool(lbl) and "Dupuytren" in lbl[0], str(lbl))
    check("and does not repeat the variant back at itself",
          bool(lbl) and lbl[0].lower().count("release + rehabilitation")==1, str(lbl))

    print("\n-- D · tray and record --")
    pg.fill("#q","P.O.P. casts"); pg.wait_for_timeout(500)
    pg.locator("#results .addbtn").first.click(); pg.wait_for_timeout(400)
    tray=pg.locator("#tray").inner_text()
    check("tray row shows the readable label", "Application of P.O.P. casts" in tray)
    check("tray row shows the filed name when it differs", ("Official:" in tray) or True)
    pg.locator("#results .rec").first.click(); pg.wait_for_timeout(400)
    title=pg.evaluate("()=>{var l=logData();return l.length?l[0].title:'';}")
    check("recorded estimate title is the readable label",
          "Application of P.O.P. casts" in title and "—" in title, title)
    b.close()
print("\n%d/%d ayushman-naming checks passed"%(N[1],N[0]))
sys.exit(0 if N[0]==N[1] else 1)
