#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""browser_xray_s582.py -- S582_XRAY_COSTS: the owner's X-ray expenses page in the PC's headless Chrome at 1366 x 768 (and the real
laptop's browser area, 1366 x 620). A small server on 127.0.0.1 serves the page exactly as the kit's build rendered it on made-up rows
(walk_s582.py --save-pages: s582_owner_xray.html, the made-up month June 2031) and takes the page's report on /result. The live box is
not reached; nothing leaves the PC.

    python -B browser_xray_s582.py <chrome.exe> <pages dir> <work dir> [--control]

Check V1 (1366 x 768 and 1366 x 620): with EVERY fold opened (the four money folds and the two tick folds), nothing is wider than the
screen (no sideways scroll); the header, the month buttons and the one total line are on the first screen; every fold's heading, every
table row's amount cell and paper link, the "+ Mark a paper" box and its button, and every tick box with its "Save the ticks" button lie
inside the width. --control: the same page with one table forced to 1900 px (a made-up broken layout) -- exit 0 only if V1 is RED."""
import http.server, json, os, re, socket, subprocess, sys, threading, time, urllib.parse

CHROME, PAGES, WORK = sys.argv[1:4]
CONTROL = "--control" in sys.argv
RES, EV = {}, threading.Event()
BREAK = "<style>#s582films table{width:1900px!important;table-layout:auto!important}</style>"

JS = r"""<script>(function(){
function inx(r){return r.width>0&&r.height>0&&r.left>=-0.5&&r.right<=window.innerWidth+0.5;}
function iny(r){return r.top>=-0.5&&r.bottom<=window.innerHeight+0.5;}
function inside(e){var q=e.getBoundingClientRect();return inx(q);}
window.addEventListener('load',function(){setTimeout(function(){
 var out={vw:window.innerWidth,vh:window.innerHeight,errs:window.__errs||[]};
 window.scrollTo(0,0);
 var top=['s582head','s582tot'].map(function(i){var e=document.getElementById(i);if(!e){return false;}var q=e.getBoundingClientRect();return inx(q)&&iny(q);});
 var nav=document.querySelector('#s582 .nav');out.first=top.concat([!!nav&&inx(nav.getBoundingClientRect())&&iny(nav.getBoundingClientRect())]);
 var ds=document.querySelectorAll('#s582 details');out.folds=ds.length;Array.prototype.forEach.call(ds,function(d){d.open=true;});
 out.heads=Array.prototype.map.call(document.querySelectorAll('#s582 details>summary'),inside);
 out.cells=Array.prototype.map.call(document.querySelectorAll('#s582 tr td:nth-child(4), #s582 tr td:nth-child(5)'),inside);
 var mf=document.getElementById('s582markform');out.mark=!!mf&&Array.prototype.every.call(mf.querySelectorAll('input:not([type=hidden]),button'),inside);
 out.ticks=Array.prototype.map.call(document.querySelectorAll('#s582 .ticks input[type=checkbox]'),inside);
 out.saves=Array.prototype.map.call(document.querySelectorAll('#s582mmarks button, #s582pmarks button'),inside);
 out.pageWide=document.documentElement.scrollWidth>window.innerWidth+1;
 out.rows=document.querySelectorAll('#s582 tr[data-paper], #s582 tr[data-row]').length;
 fetch('/result',{method:'POST',body:JSON.stringify(out)});
},300);});})();</script>"""
ERRS = "<script>window.__errs=[];window.addEventListener('error',function(e){window.__errs.push(String(e.message));});</script>"
PAGESET = ("s582_owner_xray",)


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, body, ctype, code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        m = re.match(r"^/page/(\w+)$", u.path)
        if m and m.group(1) in PAGESET:
            raw = open(os.path.join(PAGES, m.group(1) + ".html"), encoding="utf-8").read()
            extra = BREAK if CONTROL else ""
            raw = raw.replace("<head>", "<head>" + ERRS, 1).replace("</body>", extra + JS + "</body>", 1)
            return self.send(raw.encode("utf-8"), "text/html; charset=utf-8")
        return self.send(b"", "text/plain", 404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        data = self.rfile.read(n)
        if self.path.startswith("/result"):
            RES["last"] = json.loads(data.decode("utf-8"))
            EV.set()
        self.send(b"{}", "application/json")


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


PORT = free_port()
srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
PROFILE = os.path.abspath(os.path.join(WORK, "chrome_profile_s582_%d" % int(time.time())))
os.makedirs(PROFILE, exist_ok=True)


def run(name, size, wait=60):
    RES.pop("last", None); EV.clear()
    pr = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                           "--mute-audio", "--hide-scrollbars", "--user-data-dir=" + PROFILE, "--window-size=" + size,
                           "http://127.0.0.1:%d/page/%s" % (PORT, name)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    EV.wait(wait)
    pr.terminate()
    try:
        pr.wait(15)
    except Exception:                                                     # noqa: BLE001
        pr.kill()
    return RES.get("last") or {"errs": ["no report from the page within %d s" % wait]}


def ok(r):
    return (all(r.get("first") or [False]) and r.get("folds") == 6 and all(r.get("heads") or [False]) and len(r.get("heads") or []) == 6
            and all(r.get("cells") or [False]) and r.get("mark") is True and all(r.get("ticks") or [False]) and len(r.get("saves") or []) == 2
            and all(r.get("saves")) and not r.get("pageWide") and not r.get("errs") and (r.get("rows") or 0) >= 8)


def brief(r):
    return {"vw": r.get("vw"), "vh": r.get("vh"), "first": r.get("first"), "folds": r.get("folds"),
            "heads": "%d/%d" % (sum(1 for x in r.get("heads") or [] if x), len(r.get("heads") or [])),
            "cells": "%d/%d" % (sum(1 for x in r.get("cells") or [] if x), len(r.get("cells") or [])), "mark": r.get("mark"),
            "ticks": "%d/%d" % (sum(1 for x in r.get("ticks") or [] if x), len(r.get("ticks") or [])), "saves": r.get("saves"),
            "rows": r.get("rows"), "pageWide": r.get("pageWide"), "errs": r.get("errs")}


t0 = time.time()
r1 = run("s582_owner_xray", "1366,768")
print("  owner 1366 x 768 (every fold open): %s" % json.dumps(brief(r1), ensure_ascii=False), flush=True)
if CONTROL:
    red = not ok(r1)
    print("CONTROL a made-up broken layout (the films table forced to 1900 px) at 1366 x 768: V1 %s (must be RED)" % ("RED" if red else "GREEN"), flush=True)
    srv.shutdown()
    sys.exit(0 if red else 1)
r2 = run("s582_owner_xray", "1390,719")
print("  owner 1366 x 620 (the laptop's browser area): %s" % json.dumps(brief(r2), ensure_ascii=False), flush=True)
good = ok(r1) and ok(r2)
print(("GREEN " if good else "RED   ") + "V1 the owner's X-ray expenses page at 1366 x 768 (viewport %sx%s) and 1366 x 620 (viewport %sx%s), every fold open: "
      "no sideways scroll; the header, the month buttons and the total line on the first screen; every fold heading, amount and paper link, "
      "the '+ Mark a paper' box and every tick box with its Save inside the width" % (r1.get("vw"), r1.get("vh"), r2.get("vw"), r2.get("vh")))
print("1 browser check: %d GREEN, %d RED  (%.0f s)" % (1 if good else 0, 0 if good else 1, time.time() - t0))
srv.shutdown()
sys.exit(0 if good else 1)
