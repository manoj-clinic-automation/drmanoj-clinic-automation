#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""browser_diya_s568.py -- S568 FIX1 (the kit review K1's CORRECTION 2): "Stationery diya" in the PC's headless Chrome at a phone's
width (390 x 844, the owner's mock-up artboard Issue.dc.html). A small server on 127.0.0.1 serves the page exactly as the kit's
build rendered it on made-up rows (walk_s568.py --save-pages: diya.html, diya_after.html) and takes the page's report on /result.
The live box is not reached; nothing leaves the PC.

    python -B browser_diya_s568.py <chrome.exe> <pages dir> <work dir> [--control]

Checks: D1 the screen -- the title 'Stationery diya'; the labels 'Kya diya', 'Kitne', 'Kisko' on screen; four place buttons Lab ·
Reception · Sanjeevni · Clinic in a 2 x 2 grid, each at least 52 px tall and inside the screen's width; one tap on a button picks
that place; one Save, on the page; nothing wider than the phone. D2 after a Save -- the line 'Ho gaya — <item> <qty> <unit>,
<place> ko. Stock mein ab <N>.' at the top. --control: the same on the round-0 kit's page -- exit 0 only if D1 is RED."""
import http.server, json, os, re, socket, subprocess, sys, threading, time, urllib.parse

CHROME, PAGES, WORK = sys.argv[1:4]
CONTROL = "--control" in sys.argv
RES, EV = {}, threading.Event()

JS = r"""<script>(function(){
function txt(e){return (e.textContent||'').replace(/\s+/g,' ').trim();}
function onx(r){return r.width>0&&r.height>0&&r.left>=-0.5&&r.right<=window.innerWidth+0.5;}
window.addEventListener('load',function(){setTimeout(function(){
 var out={vw:window.innerWidth,vh:window.innerHeight,errs:window.__errs||[]};
 var h2=document.querySelector('main h2');out.title=h2?txt(h2):'';
 var form=document.querySelector('#s568diya form');out.form=!!form;
 var fl=document.querySelector('main .flash');out.flash=fl?txt(fl):'';
 if(form){
  out.labels=Array.prototype.filter.call(form.querySelectorAll('label'),function(l){return !l.querySelector('input[type=radio]');}).map(function(l){var r=l.getBoundingClientRect();return {t:txt(l),on:onx(r)};});
  var radios=Array.prototype.slice.call(form.querySelectorAll('input[type=radio][name=place]'));
  out.places=radios.map(function(i){var b=i.closest('label')||i;var r=b.getBoundingClientRect();return {v:i.value,t:txt(b),top:Math.round(r.top),left:Math.round(r.left),h:Math.round(r.height),w:Math.round(r.width),on:onx(r)};});
  var pick=radios.filter(function(i){return i.value==='sanjeevni';})[0];
  if(pick){var lb=pick.closest('label');var tgt=lb&&lb.querySelector('span')?lb.querySelector('span'):lb;var r=tgt.getBoundingClientRect();
   var el=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);if(el){el.click();}
   out.tapPicks=pick.checked&&radios.filter(function(i){return i.checked;}).length===1;}
  out.buttons=Array.prototype.map.call(form.querySelectorAll('button,input[type=submit]'),function(b){var r=b.getBoundingClientRect();return {t:txt(b)||b.value,h:Math.round(r.height),on:onx(r)};});
 }
 out.pageWide=document.documentElement.scrollWidth>window.innerWidth+1;
 fetch('/result',{method:'POST',body:JSON.stringify(out)});
},300);});})();</script>"""
ERRS = "<script>window.__errs=[];window.addEventListener('error',function(e){window.__errs.push(String(e.message));});</script>"


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
        m = re.match(r"^/page/(diya|diya_after)$", u.path)
        if m:
            raw = open(os.path.join(PAGES, m.group(1) + ".html"), encoding="utf-8").read()
            raw = raw.replace("<head>", "<head>" + ERRS, 1).replace("</body>", JS + "</body>", 1)
            return self.send(raw.encode("utf-8"), "text/html; charset=utf-8")
        m = re.match(r"^/frame/(diya|diya_after)$", u.path)
        if m:                                       # headless Chrome keeps a window >= 500 px wide: the phone is a 390 x 844 frame
            body = ("<!doctype html><html><body style='margin:0'><iframe src='/page/%s' style='width:390px;height:844px;border:0;display:block'>"
                    "</iframe></body></html>" % m.group(1))
            return self.send(body.encode("utf-8"), "text/html; charset=utf-8")
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
PROFILE = os.path.abspath(os.path.join(WORK, "chrome_profile_diya_%d" % int(time.time())))
os.makedirs(PROFILE, exist_ok=True)


def run(name, size="640,1000", wait=60):
    RES.pop("last", None); EV.clear()
    pr = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                           "--mute-audio", "--hide-scrollbars", "--user-data-dir=" + PROFILE, "--window-size=" + size,
                           "http://127.0.0.1:%d/frame/%s" % (PORT, name)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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


def d1_ok(r):
    pl = r.get("places") or []
    labels = [x.get("t") for x in (r.get("labels") or [])]
    tops = sorted(set(p["top"] for p in pl))
    lefts = sorted(set(p["left"] for p in pl))
    grid = (len(pl) == 4 and len(tops) == 2 and len(lefts) == 2
            and [p["v"] for p in pl if p["top"] == tops[0]] == ["lab", "reception"] and [p["v"] for p in pl if p["top"] == tops[1]] == ["sanjeevni", "clinic"])
    btns = r.get("buttons") or []
    return (r.get("vw") == 390 and r.get("title") == "Stationery diya" and labels == ["Kya diya", "Kitne", "Kisko"] and all(x.get("on") for x in r.get("labels") or [])
            and [p["v"] for p in pl] == ["lab", "reception", "sanjeevni", "clinic"] and [p["t"] for p in pl] == ["Lab", "Reception", "Sanjeevni", "Clinic"]
            and grid and all(p["h"] >= 52 and p["on"] for p in pl) and r.get("tapPicks") is True
            and len(btns) == 1 and btns[0]["t"] == "Save" and btns[0]["on"] and not r.get("pageWide") and not r.get("errs"))


t0 = time.time()
r1 = run("diya")
print("  diya 390 x 844: %s" % json.dumps({k: r1.get(k) for k in ("vw", "vh", "title", "labels", "places", "tapPicks", "buttons", "pageWide", "errs")},
                                         ensure_ascii=False), flush=True)
if CONTROL:
    ok = not d1_ok(r1)
    print("CONTROL the round-0 kit's Stationery diya at 390 x 844: D1 %s (must be RED)" % ("RED" if ok else "GREEN"), flush=True)
    srv.shutdown()
    sys.exit(0 if ok else 1)
line(d1_ok(r1), "D1 Stationery diya at a phone's width (viewport %sx%s): the title; 'Kya diya', 'Kitne', 'Kisko' on screen; four place "
                "buttons Lab · Reception · Sanjeevni · Clinic in a 2 x 2 grid, each >= 52 px tall and on screen; one tap picks; one Save; "
                "nothing wider than the phone" % (r1.get("vw"), r1.get("vh")),
     "labels %s; buttons h %s; Save %s; page wider %s" % ([x.get("t") for x in r1.get("labels") or []], [p.get("h") for p in r1.get("places") or []],
                                                        r1.get("buttons"), r1.get("pageWide")))
r2 = run("diya_after")
print("  diya_after 390 x 844: %s" % json.dumps({k: r2.get(k) for k in ("vw", "vh", "flash", "pageWide", "errs")}, ensure_ascii=False), flush=True)
line(bool(re.match(r"^Ho gaya — .+ \S+ \S*, (Lab|Reception|Sanjeevni|Clinic) ko\. Stock mein ab -?[\d.]+\.$", r2.get("flash") or ""))
     and r2.get("vw") == 390 and not r2.get("pageWide") and not r2.get("errs"),
     "D2 after a Save: 'Ho gaya — <item> <qty> <unit>, <place> ko. Stock mein ab <N>.' at the top, nothing wider than the phone",
     repr(r2.get("flash")))
print("%d browser checks: %d GREEN, %d RED  (%.0f s)" % (len(OUT), len(OUT) - len(REDS), len(REDS), time.time() - t0))
srv.shutdown()
sys.exit(1 if REDS else 0)
