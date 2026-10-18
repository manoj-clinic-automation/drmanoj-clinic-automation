#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""browser_many_s585.py -- S585: the many-items screen in the PC's headless Chrome at a phone's width (390 x 844, the owner's mock-up
artboard Main.dc.html) and at 1366 x 768, and the owner's Stationery page at 1366 x 768. A small server on 127.0.0.1 serves the pages
exactly as the kit's build rendered them on made-up rows (walk_s585.py --save-pages: many.html, many_after.html, stock.html) and takes
each page's report on /result. The live box is not reached; nothing leaves the PC; no Save reaches any server (the test stops the
form's submit after counting it).

    python -B browser_many_s585.py <chrome.exe> <pages dir> <work dir> [--control]

Checks: V1 at 390 x 844 -- five place buttons (3 + 2 rows), each >= 44 px tall and on screen; every item row's − and + >= 44 px and on
screen, its number box on screen; Save grey ('Save karo') at first; one tap on X-ray picks it; + + on a row -> 2, the row green, Save
'Save karo (1)' and the line naming it '→ X-ray'; − -> 1; a word typed in a number box greys Save, cleared -> back; the first tap on
Save sends once and greys it, a second tap sends nothing; nothing wider than the phone. V2 the same screen at 1366 x 768: nothing
wider than the window, every row's controls on screen. V3 after a Save at 390: 'Save ho gaya ✓ — …' at the top, nothing wider.
V4 the owner's Stationery page at 1366 x 768 with every fold open: nothing wider than the window. --control: a 1900 px element
is put into the screen -- exit 0 only if V1 is RED."""
import http.server, json, os, re, socket, subprocess, sys, threading, time, urllib.parse

CHROME, PAGES, WORK = sys.argv[1:4]
CONTROL = "--control" in sys.argv
RES, EV = {}, threading.Event()

JS = r"""<script>(function(){
function txt(e){return (e.textContent||'').replace(/\s+/g,' ').trim();}
function onx(r){return r.width>0&&r.height>0&&r.left>=-0.5&&r.right<=window.innerWidth+0.5;}
function tap(el){var r=el.getBoundingClientRect();var t=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);(t||el).click();}
window.addEventListener('load',function(){setTimeout(function(){
 var out={vw:window.innerWidth,vh:window.innerHeight,errs:window.__errs||[]};
 var fl=document.querySelector('main .flash');out.flash=fl?txt(fl):'';
 Array.prototype.forEach.call(document.querySelectorAll('details'),function(d){d.open=true;});
 var f=document.getElementById('s585form');out.form=!!f;
 if(f){
  var sv=document.getElementById('s585save'),sm=document.getElementById('s585sum');
  var labs=Array.prototype.slice.call(f.querySelectorAll('label.s585place'));
  out.places=labs.map(function(l){var s=l.querySelector('span');var r=s.getBoundingClientRect();return {t:txt(l),top:Math.round(r.top),h:Math.round(r.height),on:onx(r)};});
  var rows=Array.prototype.slice.call(f.querySelectorAll('.s585row'));
  out.nrows=rows.length;
  out.rowsOk=rows.every(function(r){var bs=r.querySelectorAll('button');var i=r.querySelector('input');
    return bs.length===2&&Array.prototype.every.call(bs,function(b){var q=b.getBoundingClientRect();return q.height>=44&&q.width>=44&&onx(q);})&&onx(i.getBoundingClientRect());});
  out.save0={dis:sv.disabled,t:txt(sv),on:onx(sv.getBoundingClientRect())};
  var sends=0;f.addEventListener('submit',function(e){sends++;e.preventDefault();});
  var xr=labs.filter(function(l){return txt(l)==='X-ray';})[0];if(xr){tap(xr.querySelector('span'));}
  out.xrPicked=!!f.querySelector('input[name=place][value=xray]:checked');
  var r0=rows[0],plus=r0.querySelector('.s585plus'),minus=r0.querySelector('.s585minus'),q0=r0.querySelector('input');
  tap(plus);tap(plus);
  out.after2={q:q0.value,green:r0.classList.contains('on'),dis:sv.disabled,t:txt(sv),sum:txt(sm),name:r0.getAttribute('data-name')};
  tap(minus);out.after1={q:q0.value,t:txt(sv)};
  var q1=rows[1].querySelector('input');q1.value='abc';q1.dispatchEvent(new Event('input',{bubbles:true}));
  out.bad={dis:sv.disabled,sum:txt(sm)};
  q1.value='';q1.dispatchEvent(new Event('input',{bubbles:true}));
  out.cleared={dis:sv.disabled,t:txt(sv)};
  tap(sv);var s1=sends;var d1=sv.disabled;tap(sv);
  out.sends={first:s1,dis:d1,second:sends,t:txt(sv)};
 }
 out.pageWide=document.documentElement.scrollWidth>window.innerWidth+1;
 fetch('/result',{method:'POST',body:JSON.stringify(out)});
},300);});})();</script>"""
ERRS = "<script>window.__errs=[];window.addEventListener('error',function(e){window.__errs.push(String(e.message));});</script>"
WIDE = "<div style='width:1900px;height:4px;background:#c00'></div>"


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
        m = re.match(r"^/page/(many|many_after|stock)$", u.path)
        if m:
            raw = open(os.path.join(PAGES, m.group(1) + ".html"), encoding="utf-8").read()
            raw = raw.replace("<head>", "<head>" + ERRS, 1).replace("</body>", JS + "</body>", 1)
            if CONTROL and m.group(1) == "many":
                raw = raw.replace("<div class=card id=s585many>", WIDE + "<div class=card id=s585many>", 1)
            return self.send(raw.encode("utf-8"), "text/html; charset=utf-8")
        m = re.match(r"^/frame/(many|many_after)$", u.path)
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
PROFILE = os.path.abspath(os.path.join(WORK, "chrome_profile_many_%d" % int(time.time())))
os.makedirs(PROFILE, exist_ok=True)


def run(path, size, wait=60):
    RES.pop("last", None); EV.clear()
    pr = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                           "--mute-audio", "--hide-scrollbars", "--user-data-dir=" + PROFILE, "--window-size=" + size,
                           "http://127.0.0.1:%d%s" % (PORT, path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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


def screen_ok(r, vw):
    pl = r.get("places") or []
    tops = sorted(set(p["top"] for p in pl))
    a2, a1, bad, cl, sd = r.get("after2") or {}, r.get("after1") or {}, r.get("bad") or {}, r.get("cleared") or {}, r.get("sends") or {}
    return (r.get("vw") == vw and r.get("form") and [p["t"] for p in pl] == ["Lab", "Reception", "Sanjeevni", "Clinic", "X-ray"]
            and (len(tops) == 2 if vw <= 420 else len(tops) >= 1) and all(p["h"] >= 44 and p["on"] for p in pl)
            and (r.get("nrows") or 0) >= 3 and r.get("rowsOk") is True
            and (r.get("save0") or {}).get("dis") is True and (r.get("save0") or {}).get("t") == "Save karo" and (r.get("save0") or {}).get("on")
            and r.get("xrPicked") is True and a2.get("q") == "2" and a2.get("green") is True and a2.get("dis") is False and a2.get("t") == "Save karo (1)"
            and (a2.get("name") or "~") in (a2.get("sum") or "") and (a2.get("sum") or "").endswith("→ X-ray")
            and a1.get("q") == "1" and bad.get("dis") is True and "number nahi hai" in (bad.get("sum") or "") and cl.get("dis") is False
            and sd.get("first") == 1 and sd.get("dis") is True and sd.get("second") == 1
            and not r.get("pageWide") and not r.get("errs"))


t0 = time.time()
r1 = run("/frame/many", "640,1000")
print("  many 390 x 844: %s" % json.dumps({k: r1.get(k) for k in ("vw", "vh", "places", "nrows", "rowsOk", "save0", "xrPicked", "after2", "after1",
                                                                  "bad", "cleared", "sends", "pageWide", "errs")}, ensure_ascii=False), flush=True)
if CONTROL:
    ok = not screen_ok(r1, 390)
    print("CONTROL a 1900 px element in the many-items screen at 390 x 844: V1 %s (must be RED)" % ("RED" if ok else "GREEN"), flush=True)
    srv.shutdown()
    sys.exit(0 if ok else 1)
line(screen_ok(r1, 390), "V1 the many-items screen at a phone's width (390 x 844): five place buttons in 3 + 2, >= 44 px, on screen; every "
                         "row's − / + >= 44 px and its number box on screen; Save grey at first; X-ray picked by a tap; + + -> 2 (row green, "
                         "'Save karo (1)', the line naming it '→ X-ray'); − -> 1; a word greys Save; the first Save tap sends once and greys "
                         "it, a second sends nothing; nothing wider than the phone")
r2 = run("/page/many", "1366,768")
print("  many 1366 x 768: %s" % json.dumps({k: r2.get(k) for k in ("vw", "vh", "nrows", "rowsOk", "sends", "pageWide", "errs")}, ensure_ascii=False), flush=True)
line(screen_ok(r2, r2.get("vw") or 0) and (r2.get("vw") or 0) >= 1300,
     "V2 the same screen at 1366 x 768 (viewport %sx%s): the same taps, every row's controls on screen, nothing wider than the window" % (r2.get("vw"), r2.get("vh")))
r3 = run("/frame/many_after", "640,1000")
print("  many_after 390 x 844: %s" % json.dumps({k: r3.get(k) for k in ("vw", "flash", "pageWide", "errs")}, ensure_ascii=False), flush=True)
line(bool(re.match(r"^Save ho gaya ✓ — .+ → (Lab|Reception|Sanjeevni|Clinic|X-ray)$", r3.get("flash") or "")) and r3.get("vw") == 390
     and not r3.get("pageWide") and not r3.get("errs"), "V3 after a Save at 390: 'Save ho gaya ✓ — <what was saved> → <place>' at the top, "
     "nothing wider than the phone", repr(r3.get("flash")))
r4 = run("/page/stock", "1366,768")
print("  stock 1366 x 768: %s" % json.dumps({k: r4.get(k) for k in ("vw", "vh", "pageWide", "errs")}, ensure_ascii=False), flush=True)
line((r4.get("vw") or 0) >= 1300 and r4.get("pageWide") is False and not r4.get("errs"),
     "V4 the owner's Stationery page at 1366 x 768 with every fold open (Show all issues, Shavez's sheet): nothing wider than the window")
print("%d browser checks: %d GREEN, %d RED  (%.0f s)" % (len(OUT), len(OUT) - len(REDS), len(REDS), time.time() - t0))
srv.shutdown()
sys.exit(1 if REDS else 0)
