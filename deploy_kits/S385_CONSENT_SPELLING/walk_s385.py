#!/usr/bin/env python3
"""walk_s385.py -- kit S385_CONSENT_SPELLING. The kit's casepack_page.html in headless Chromium against a stub server
that answers /portal/casepack/trdict through the kit's own casepack_portal.py routes (a scratch CASEPACK_DIR).
The owner's case, shaped: a name and an address the machine spells wrongly; corrected ONCE in the new box; every
occurrence in the consent and the header of the printed page change; the spelling is remembered, so a fresh page's
next consent spells it right by itself; a hand-edit in one place only is caught before printing.
The live page (S216) is the negative control. Usage: python3 walk_s385.py <kit dir> <live casepack_page.html>"""
import importlib.util, json, os, sys, tempfile, threading
kit, live = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
tmp = tempfile.mkdtemp(prefix="s385walk_")
os.environ["PORTAL_CASEPACK_DIR"] = tmp
os.environ["PORTAL_CONSOLE_DB"] = os.path.join(tmp, "none.db"); os.environ["PORTAL_FINANCE_DB"] = os.path.join(tmp, "none2.db")
N = [0]
def ok(c, label, got=None):
    N[0] += 1
    if not c:
        print("WALK RED %d: %s %s" % (N[0], label, "" if got is None else got)); sys.exit(1)
from flask import Flask, Response
s = importlib.util.spec_from_file_location("cp", os.path.join(kit, "casepack_portal.py")); cp = importlib.util.module_from_spec(s); s.loader.exec_module(cp)
app = Flask("w")
cp.register(app, lambda f: f, lambda: "manoj")
PAGE = {"html": ""}
@app.route("/walkpage")
def walkpage():
    return Response(PAGE["html"], mimetype="text/html; charset=utf-8")
th = threading.Thread(target=lambda: app.run(port=65071, use_reloader=False), daemon=True); th.start()
import time; time.sleep(1.2)
from playwright.sync_api import sync_playwright
NAME, RES = "Tulsi Chaurasia", "Khurramgautiya"
GOOD_NAME, GOOD_RES = "तुलसी चौरसिया", "खुर्रम गौटिया"
def run(page_file):
    PAGE["html"] = open(page_file, encoding="utf-8").read()
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("CHROME") or None)
        pg = b.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.route("https://inputtools.google.com/**", lambda r: r.abort())
        pg.goto("http://127.0.0.1:65071/walkpage"); pg.wait_for_timeout(800)
        def gen():
            pg.evaluate("""([n,r])=>{ const s=(id,v)=>{const e=document.getElementById(id); if(e){e.value=v; e.dispatchEvent(new Event('input')); e.dispatchEvent(new Event('change'));}};
              s('c_name',n); s('c_age','60'); s('cs_res',r); window.cp11Check=function(){return null;}; }""", [NAME, RES])
            pg.evaluate("async()=>{ await csGenerate(); }"); pg.wait_for_timeout(300)
        gen()
        res = {"errs": errs, "hasbox": pg.evaluate("!!document.getElementById('cs_fix') && document.getElementById('cs_fix').style.display!=='none'"),
               "meta": pg.evaluate("csLastMeta")}
        if res["hasbox"]:
            pg.evaluate("""([a,b])=>{ const f=CS_FIX; f.forEach((x,i)=>{ const e=document.getElementById('csfix_'+i); if(x.key==='name') e.value=a; if(x.key==='res') e.value=b; }); }""", [GOOD_NAME, GOOD_RES])
            res["wrong_before"] = pg.evaluate("[CS_FIX.find(f=>f.key==='name').cur, CS_FIX.find(f=>f.key==='name').n]")
            pg.evaluate("csFixApply()"); pg.wait_for_timeout(500)
            res["body"] = pg.evaluate("document.getElementById('cs_out').innerText")
            res["print"] = pg.evaluate("csPrintHTML()")
            res["msg"] = pg.evaluate("document.getElementById('csfix_msg').textContent")
            # a hand-edit in ONE place only is caught before printing
            pg.evaluate("""(a)=>{ const out=document.getElementById('cs_out'); const w=document.createTreeWalker(out,NodeFilter.SHOW_TEXT); let t; while((t=w.nextNode())){ if(t.nodeValue.indexOf(a)>=0){ t.nodeValue=t.nodeValue.replace(a,'XYZ'); break; } } }""", GOOD_NAME)
            asked = []
            pg.on("dialog", lambda d: (asked.append(d.message), d.dismiss()))
            pg.evaluate("document.getElementById('cs_pr').onclick()"); pg.wait_for_timeout(300)
            res["asked"] = asked
            # a fresh page: the spelling is remembered
            pg.goto("http://127.0.0.1:65071/walkpage"); pg.wait_for_timeout(900)
            gen()
            res["body2"] = pg.evaluate("document.getElementById('cs_out').innerText")
            res["meta2"] = pg.evaluate("csLastMeta")
        b.close()
    return res
r = run(os.path.join(kit, "casepack_page.html"))
ok(not r["errs"], "no script error on the page", r["errs"][:2])
ok(r["hasbox"], "after Generate the Hindi-spelling box shows")
ok(r["wrong_before"][0] != GOOD_NAME and r["wrong_before"][1] >= 1, "the machine spelling is in the consent (and the header) before the correction", r["wrong_before"][1])
ok(r["body"].count(GOOD_NAME) >= 1 and r["wrong_before"][0] not in r["body"], "Apply everywhere: every occurrence in the consent carries the corrected name, none the old")
ok(GOOD_RES in r["body"], "the address is corrected in the consent")
ok(GOOD_NAME in r["print"] and GOOD_RES in r["print"] and r["wrong_before"][0] not in r["print"].split("cs-rhead")[1][:600],
   "the header printed on every page carries the corrected name and address")
ok(os.path.exists(os.path.join(tmp, "tr_dict.json")) and json.load(open(os.path.join(tmp, "tr_dict.json"), encoding="utf-8")).get("tulsi chaurasia") == GOOD_NAME,
   "the spelling is remembered on the server (name, and each word)")
ok(r["asked"] and "not everywhere" in r["asked"][0], "a hand-edit in one place only is caught before printing", r["asked"])
ok(r["body2"].count(GOOD_NAME) >= 1 and r["meta2"]["name"] == GOOD_NAME and r["meta2"]["res"] == GOOD_RES,
   "a fresh page: the next consent spells the name and the address right by itself")
r0 = run(live)
ok(not r0["hasbox"], "negative control: the live page has no spelling box (an edit stays in one place)")
print("WALK OK %d/%d checks" % (N[0], N[0]))
