#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""browser_batteries_s575.py -- S575_BATTERY_SETUP: the Batteries page with the First setup fold, and the New battery fitted forms, in
the PC's headless Chrome at 1366 x 768 (and the real laptop's browser area, 1366 x 620). A small server on 127.0.0.1 serves the pages
exactly as the kit's build rendered them on made-up rows (walk_s575.py --save-pages: s575_owner_first.html, s575_fit_online.html,
s575_fit_small.html, s575_fit_jasoria.html, s575_place_links.html) and takes each page's report on /result. The live box is not
reached; nothing leaves the PC.

    python -B browser_batteries_s575.py <chrome.exe> <pages dir> <work dir> [--control]

Checks: F1 (owner, 1366 x 768 and 1366 x 620) the four totals on the first screen; every group's rows reachable with 'New battery
fitted' inside the width; every 'How many batteries? — set' inside the width; the First setup fold open, each of its lines -- the
place, 'Fitted on', the bill, 'or find by stamp' and Save -- on screen when scrolled to, inside the width; nothing wider than the
screen. F2 the three New battery fitted forms (online UPS, small UPS, Jasoria) at 1366 x 768: every field outside the closed fold and
Save on one screen (the online UPS's first field is 'Batteries in the set'); 'Show older / other papers' opened: its fields inside
the width and reachable, Save still reachable. F3 a place's 'The battery now — its papers' with the fold opened: the wider list,
'Find by stamp' and Link inside the width. --control: the owner's page with the First setup lines forced to one 1900 px row (a
made-up broken layout) -- exit 0 only if F1 is RED (the check can fail)."""
import http.server, json, os, re, socket, subprocess, sys, threading, time, urllib.parse

CHROME, PAGES, WORK = sys.argv[1:4]
CONTROL = "--control" in sys.argv
RES, EV = {}, threading.Event()
BREAK = "<style>#s571first form.s575line{flex-wrap:nowrap!important;width:1900px!important}</style>"

JS = r"""<script>(function(){
function txt(e){return (e.textContent||'').replace(/\s+/g,' ').trim();}
function inx(r){return r.width>0&&r.height>0&&r.left>=-0.5&&r.right<=window.innerWidth+0.5;}
function iny(r){return r.top>=-0.5&&r.bottom<=window.innerHeight+0.5;}
function vis(e){return !(e.closest&&e.closest('details:not([open])'))&&e.type!=='hidden';}
function seen(e){e.scrollIntoView({block:'center'});var q=e.getBoundingClientRect();return inx(q)&&iny(q);}
window.addEventListener('load',function(){setTimeout(function(){
 var out={vw:window.innerWidth,vh:window.innerHeight,errs:window.__errs||[]};
 var tot=document.getElementById('s571tot');if(tot){out.totals=Array.prototype.map.call(tot.children,function(c){var q=c.getBoundingClientRect();return {t:txt(c),on:inx(q)&&iny(q)};});}
 out.groups=Array.prototype.map.call(document.querySelectorAll('#s571 section'),function(s){
  return {name:txt(s.querySelector('h3')),rows:Array.prototype.map.call(s.querySelectorAll('tr[data-place]'),function(tr){var b=tr.querySelector('a.fitb');return !!(b&&seen(b));})};});
 out.asks=Array.prototype.map.call(document.querySelectorAll('a.s575ask'),function(a){return seen(a);});
 var fd=document.getElementById('s571first');
 if(fd){out.foldOpen=fd.open;out.foldHead=seen(fd.querySelector('summary'));
  out.lines=Array.prototype.map.call(fd.querySelectorAll('form.s575line'),function(f){var parts=[f.querySelector('.s575nm'),f.querySelector('[name=fitted_on]'),f.querySelector('[name=bill]'),f.querySelector('[name=bill_stamp]'),f.querySelector('button')];
   f.scrollIntoView({block:'center'});return {place:txt(f.querySelector('.s575nm')),ok:parts.every(function(e){if(!e){return false;}var q=e.getBoundingClientRect();return inx(q)&&iny(q);}),req:f.querySelector('[name=fitted_on]').required};});}
 var f=document.getElementById('s571fit');
 if(f){window.scrollTo(0,0);var els=Array.prototype.filter.call(f.querySelectorAll('input,select,button'),vis);
  out.first=(els[0]||{}).name||'';
  out.fields=els.map(function(e){var q=e.getBoundingClientRect();return {n:e.name||txt(e),on:inx(q)&&iny(q)};});
  var ds=f.querySelectorAll('details.s575more');out.folds=ds.length;Array.prototype.forEach.call(ds,function(d){d.open=true;});
  out.inner=Array.prototype.map.call(f.querySelectorAll('details.s575more select,details.s575more input'),function(e){return {n:e.name,on:seen(e)};});
  var sv=f.querySelector('button');out.saveAfter=!!(sv&&seen(sv));}
 var lk=document.getElementById('s571links');
 if(lk){var d=lk.querySelector('details.s575more');if(d){d.open=true;}
  out.links=Array.prototype.map.call(lk.querySelectorAll('select,input:not([type=hidden]),button'),function(e){return {n:e.name||txt(e),on:seen(e)};});}
 out.pageWide=document.documentElement.scrollWidth>window.innerWidth+1;
 fetch('/result',{method:'POST',body:JSON.stringify(out)});
},300);});})();</script>"""
ERRS = "<script>window.__errs=[];window.addEventListener('error',function(e){window.__errs.push(String(e.message));});</script>"
PAGESET = ("s575_owner_first", "s575_fit_online", "s575_fit_small", "s575_fit_jasoria", "s575_place_links")


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
            extra = BREAK if (CONTROL and m.group(1) == "s575_owner_first") else ""
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
PROFILE = os.path.abspath(os.path.join(WORK, "chrome_profile_s575_%d" % int(time.time())))
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


def f1_ok(r):
    t = r.get("totals") or []
    gs = r.get("groups") or []
    ln = r.get("lines") or []
    return (len(t) == 4 and all(x["on"] for x in t) and len(gs) == 4 and all(all(g["rows"]) for g in gs) and all(r.get("asks") or [False])
            and r.get("foldOpen") is True and r.get("foldHead") is True and len(ln) >= 3 and all(x["ok"] and x["req"] for x in ln)
            and not r.get("pageWide") and not r.get("errs"))


def brief(r):
    return {"vw": r.get("vw"), "vh": r.get("vh"), "totals_on": [x["on"] for x in r.get("totals") or []],
            "groups": [(g["name"], len(g["rows"]), sum(1 for x in g["rows"] if x)) for g in r.get("groups") or []],
            "asks": "%d/%d" % (sum(1 for x in r.get("asks") or [] if x), len(r.get("asks") or [])), "foldOpen": r.get("foldOpen"),
            "lines": "%d/%d" % (sum(1 for x in r.get("lines") or [] if x["ok"]), len(r.get("lines") or [])),
            "pageWide": r.get("pageWide"), "errs": r.get("errs")}


t0 = time.time()
r1 = run("s575_owner_first", "1366,768")
print("  owner 1366 x 768 (First setup open): %s" % json.dumps(brief(r1), ensure_ascii=False), flush=True)
if CONTROL:
    ok = not f1_ok(r1)
    print("CONTROL a made-up broken layout (the First setup lines one 1900 px row) at 1366 x 768: F1 %s (must be RED)" % ("RED" if ok else "GREEN"), flush=True)
    srv.shutdown()
    sys.exit(0 if ok else 1)
r1b = run("s575_owner_first", "1390,719")
print("  owner 1366 x 620 (the laptop's browser area): %s" % json.dumps(brief(r1b), ensure_ascii=False), flush=True)
line(f1_ok(r1) and f1_ok(r1b), "F1 the owner's Batteries page with First setup open at 1366 x 768 (viewport %sx%s) and 1366 x 620 (viewport %sx%s): the "
     "four totals on the first screen; every row's 'New battery fitted' and every 'How many batteries? — set' inside the width; each First "
     "setup line (place, Fitted on -- required --, bill, find by stamp, Save) on screen when scrolled to; nothing wider than the screen"
     % (r1.get("vw"), r1.get("vh"), r1b.get("vw"), r1b.get("vh")),
     "First setup lines %s, asks %s" % (brief(r1)["lines"], brief(r1)["asks"]))
okf, det = True, []
for nm in ("s575_fit_online", "s575_fit_small", "s575_fit_jasoria"):
    r = run(nm, "1366,768")
    fl, inner = r.get("fields") or [], r.get("inner") or []
    det.append("%s: first '%s', %d fields, off screen %s, fold %d with %d fields (off %s), Save after opening %s"
               % (nm[9:], r.get("first"), len(fl), [x["n"] for x in fl if not x["on"]], r.get("folds") or 0, len(inner),
                  [x["n"] for x in inner if not x["on"]], r.get("saveAfter")))
    want_first = "set_n" if nm == "s575_fit_online" else "fitted_on"
    want_inner = 4 if nm == "s575_fit_jasoria" else 2
    okf = okf and (len(fl) >= 6 and all(x["on"] for x in fl) and r.get("first") == want_first and r.get("folds") == 1
                   and len(inner) == want_inner and all(x["on"] for x in inner) and r.get("saveAfter") is True
                   and not r.get("pageWide") and not r.get("errs"))
line(okf, "F2 New battery fitted (online UPS, small UPS, Jasoria) at 1366 x 768: every field outside the closed fold and Save on one screen "
     "(the online UPS's first field 'Batteries in the set'); 'Show older / other papers' opened: its fields inside the width and "
     "reachable, Save still reachable", "; ".join(det))
r3 = run("s575_place_links", "1366,768")
lk = r3.get("links") or []
line(len(lk) >= 5 and all(x["on"] for x in lk) and {"paper", "paper_any", "paper_stamp", "as"} <= {x["n"] for x in lk}
     and not r3.get("pageWide") and not r3.get("errs"),
     "F3 a place's 'The battery now — its papers' with 'Show older / other papers' opened at 1366 x 768: the usual list, the wider list, "
     "Find by stamp, 'as' and Link inside the width", "fields %s, off %s" % ([x["n"] for x in lk], [x["n"] for x in lk if not x["on"]]))
print("%d browser checks: %d GREEN, %d RED  (%.0f s)" % (len(OUT), len(OUT) - len(REDS), len(REDS), time.time() - t0))
srv.shutdown()
sys.exit(1 if REDS else 0)
