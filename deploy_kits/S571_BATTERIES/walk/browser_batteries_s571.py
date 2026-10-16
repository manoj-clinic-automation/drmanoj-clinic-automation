#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""browser_batteries_s571.py -- S571_BATTERIES: the Batteries page in the PC's headless Chrome at 1366 x 768 (and the real laptop's
browser area, 1366 x 620). A small server on 127.0.0.1 serves the pages exactly as the kit's build rendered them on made-up rows
(walk_s571.py --save-pages: batteries_owner.html, batteries_manager.html, batteries_fit_bl.html, batteries_fit_jasoria.html) and takes
each page's report on /result. The live box is not reached; nothing leaves the PC.

    python -B browser_batteries_s571.py <chrome.exe> <pages dir> <work dir> [--control]

Checks: B1 (owner, 1366 x 768 and 1366 x 620) the four totals on the first screen; every group (Online UPS, Small UPS, Generator and
inverters, Vehicles) reachable -- scrolled to, its heading on screen, every row's 'New battery fitted' button inside the screen's
width and the page not wider than the screen; '+ Add a battery place' reachable. B2 (manager, 1366 x 768) the same for the groups he
sees (no Vehicles rows). B3 the two 'New battery fitted' forms (B.L., Jasoria): every field and Save on one 1366 x 768 screen.
--control: the owner's page with its table scroller taken away and the table made 1900 px wide (a made-up broken layout) -- exit 0
only if B1 is RED (the check can fail)."""
import http.server, json, os, re, socket, subprocess, sys, threading, time, urllib.parse

CHROME, PAGES, WORK = sys.argv[1:4]
CONTROL = "--control" in sys.argv
RES, EV = {}, threading.Event()
BREAK = "<style>#s571 .scroll{overflow:visible!important}#s571 table{min-width:1900px!important}</style>"

JS = r"""<script>(function(){
function txt(e){return (e.textContent||'').replace(/\s+/g,' ').trim();}
function inx(r){return r.width>0&&r.height>0&&r.left>=-0.5&&r.right<=window.innerWidth+0.5;}
function iny(r){return r.top>=-0.5&&r.bottom<=window.innerHeight+0.5;}
window.addEventListener('load',function(){setTimeout(function(){
 var out={vw:window.innerWidth,vh:window.innerHeight,errs:window.__errs||[]};
 var tot=document.getElementById('s571tot');if(tot){var r=tot.getBoundingClientRect();out.totals=Array.prototype.map.call(tot.children,function(c){var q=c.getBoundingClientRect();return {t:txt(c),on:inx(q)&&iny(q)};});}
 out.groups=Array.prototype.map.call(document.querySelectorAll('#s571 section'),function(s){
  var h=s.querySelector('h3');h.scrollIntoView({block:'start'});var hr=h.getBoundingClientRect();
  var rows=Array.prototype.map.call(s.querySelectorAll('tr[data-place]'),function(tr){tr.scrollIntoView({block:'center'});var b=tr.querySelector('a.fitb');var q=b?b.getBoundingClientRect():null;var p=tr.querySelector('td a').getBoundingClientRect();
   return {place:txt(tr.querySelector('td a')),btn:!!(q&&inx(q)&&iny(q)),name:inx(p)&&iny(p)};});
  return {name:txt(h),head:inx(hr)&&iny(hr),rows:rows};});
 var add=document.querySelector('#s571add summary');if(add){add.scrollIntoView({block:'center'});var a=add.getBoundingClientRect();out.add=inx(a)&&iny(a);}
 var f=document.getElementById('s571fit');if(f){window.scrollTo(0,0);var fr=f.getBoundingClientRect();
  out.fields=Array.prototype.map.call(f.querySelectorAll('input,select,button'),function(e){var q=e.getBoundingClientRect();return {n:e.name||txt(e),on:inx(q)&&iny(q)};});
  out.formTop=Math.round(fr.top);}
 out.pageWide=document.documentElement.scrollWidth>window.innerWidth+1;
 fetch('/result',{method:'POST',body:JSON.stringify(out)});
},300);});})();</script>"""
ERRS = "<script>window.__errs=[];window.addEventListener('error',function(e){window.__errs.push(String(e.message));});</script>"
PAGESET = ("batteries_owner", "batteries_manager", "batteries_fit_bl", "batteries_fit_jasoria")


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
            extra = BREAK if (CONTROL and m.group(1) == "batteries_owner") else ""
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
PROFILE = os.path.abspath(os.path.join(WORK, "chrome_profile_s571_%d" % int(time.time())))
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


OUT, REDS = [], []


def line(ok, name, detail=""):
    OUT.append(("GREEN " if ok else "RED   ") + name + (("  -- " + detail) if detail else ""))
    print(OUT[-1], flush=True)
    if not ok:
        REDS.append(name)


GROUPS = ["Online UPS", "Small UPS", "Generator and inverters", "Vehicles"]


def groups_ok(r, want_rows=True):
    gs = r.get("groups") or []
    return ([g["name"] for g in gs] == GROUPS and all(g["head"] for g in gs) and all(x["btn"] and x["name"] for g in gs for x in g["rows"])
            and (not want_rows or all(g["rows"] for g in gs)) and r.get("add") is True and not r.get("pageWide") and not r.get("errs"))


def b1_ok(r):
    t = r.get("totals") or []
    return (len(t) == 4 and all(x["on"] for x in t) and [re.sub(r"^\d+", "", x["t"]) for x in t] ==
            ["Due for replacement", "Warranty ends within 30 days", "B.L. bill awaited", "Battery places"] and groups_ok(r))


def brief(r):
    return {"vw": r.get("vw"), "vh": r.get("vh"), "totals": r.get("totals"), "groups": [(g["name"], g["head"], len(g["rows"]), sum(1 for x in g["rows"] if x["btn"]))
                                                                                          for g in r.get("groups") or []], "add": r.get("add"), "pageWide": r.get("pageWide"), "errs": r.get("errs")}


t0 = time.time()
r1 = run("batteries_owner", "1366,768")
print("  owner 1366 x 768: %s" % json.dumps(brief(r1), ensure_ascii=False), flush=True)
if CONTROL:
    ok = not b1_ok(r1)
    print("CONTROL a made-up broken layout (no table scroller, a 1900 px table) at 1366 x 768: B1 %s (must be RED)" % ("RED" if ok else "GREEN"), flush=True)
    srv.shutdown()
    sys.exit(0 if ok else 1)
r1b = run("batteries_owner", "1390,719")
print("  owner 1366 x 620 (the laptop's browser area): %s" % json.dumps(brief(r1b), ensure_ascii=False), flush=True)
line(b1_ok(r1) and b1_ok(r1b), "B1 the owner's Batteries page at 1366 x 768 (viewport %sx%s) and 1366 x 620 (viewport %sx%s): the four totals on the first "
     "screen; every group reachable -- its heading on screen, every row's 'New battery fitted' inside the width; '+ Add a battery place' "
     "reachable; nothing wider than the screen" % (r1.get("vw"), r1.get("vh"), r1b.get("vw"), r1b.get("vh")),
     "rows per group %s" % [(g["name"], len(g["rows"])) for g in r1.get("groups") or []])
r2 = run("batteries_manager", "1366,768")
print("  manager 1366 x 768: %s" % json.dumps(brief(r2), ensure_ascii=False), flush=True)
vg = {g["name"]: len(g["rows"]) for g in r2.get("groups") or []}
line(groups_ok(r2, want_rows=False) and vg.get("Vehicles", 0) == 0 and all(vg.get(k, 0) > 0 for k in GROUPS[:3]),
     "B2 the manager's page (switch ON) at 1366 x 768: the clinic and lab places in reach, no vehicle rows, nothing wider than the screen",
     "rows per group %s" % vg)
okf, det = True, []
for nm in ("batteries_fit_bl", "batteries_fit_jasoria"):
    r = run(nm, "1366,768")
    fl = r.get("fields") or []
    det.append("%s: %d fields, off screen %s, top %s" % (nm[14:], len(fl), [x["n"] for x in fl if not x["on"]], r.get("formTop")))
    okf = okf and len(fl) >= 6 and all(x["on"] for x in fl) and not r.get("pageWide") and not r.get("errs")
line(okf, "B3 'New battery fitted' (B.L. and Jasoria forms) at 1366 x 768: every field and Save on one screen", "; ".join(det))
print("%d browser checks: %d GREEN, %d RED  (%.0f s)" % (len(OUT), len(OUT) - len(REDS), len(REDS), time.time() - t0))
srv.shutdown()
sys.exit(1 if REDS else 0)
