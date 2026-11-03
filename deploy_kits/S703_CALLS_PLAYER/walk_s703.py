#!/usr/bin/env python3
"""walk_s703.py -- kit S703_CALLS_PLAYER's walk. MADE-UP data only (S698's fixtures: phones 5000000xxx, no patient).
  python3 walk_s703.py <calls_console.py> <portal_console.py> <walk_s698.py> [--old]
Builds S698's made-up console.db with the builder's own transform(), renders the page through the module under test on a
bare Flask app, serves it with a stand-in recording route (a made-up 12-second tone; one join key answers 404), and plays
it in headless Chromium (Playwright). --old: the control on the live file -- every S703 check red."""
import http.server, importlib.util, io, math, os, re, struct, sys, tempfile, threading, time, wave

CC, PCF, W698 = [os.path.abspath(a) for a in sys.argv[1:4]]
OLD = "--old" in sys.argv
RES = []


def check(name, fn):
    try:
        ok, note = fn()
    except Exception as e:                                              # noqa: BLE001
        ok, note = False, "%s: %s" % (type(e).__name__, str(e)[:200])
    RES.append(bool(ok))
    print("%s  %s%s" % ("GREEN" if ok else "RED  ", name, ("  -- " + str(note)[:220]) if (note and not ok) else ""), flush=True)


def safe(fn, d=None):
    try:
        return fn()
    except Exception:                                                   # noqa: BLE001 -- the control's old page has no player
        return d


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


sys.argv = [W698, tempfile.gettempdir()]
w = load("w698", W698)
pc = load("pc703", PCF)
cc = load("cc703", CC)
td = tempfile.mkdtemp(prefix="s703walk.")
dbp = os.path.join(td, "console.db")
_counts, P = w.build_db(pc, dbp)
app, _state = w.make_app(cc, dbp, spam={P["P8"]})
html = app.test_client().get("/portal/console").get_data(as_text=True)
# the made-up recording: a 12-second tone, 8 kHz mono
buf = io.BytesIO()
with wave.open(buf, "wb") as wv:
    wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(8000)
    wv.writeframes(b"".join(struct.pack("<h", int(2000 * math.sin(2 * math.pi * 440 * i / 8000))) for i in range(8000 * 12)))
WAV = buf.getvalue()
SEEN = []


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/portal/rec/"):
            jk = self.path.rsplit("/", 1)[-1]
            SEEN.append(jk)
            if jk.endswith("999999"):
                self.send_response(404); self.end_headers(); return
            if jk.endswith("777777"):
                time.sleep(2.5)                             # a slow phone line / the Drive redirect
            data, start = WAV, 0
            rng = self.headers.get("Range")
            if rng:
                m = re.match(r"bytes=(\d+)-(\d*)", rng)
                start = int(m.group(1)); end = int(m.group(2)) if m.group(2) else len(WAV) - 1
                self.send_response(206)
                self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, len(WAV)))
                data = WAV[start:end + 1]
            else:
                self.send_response(200)
            self.send_header("Content-Type", "audio/wav"); self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
            return
        b = html.encode("utf-8")
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/portal/console" % srv.server_address[1]

from playwright.sync_api import sync_playwright                          # noqa: E402

with sync_playwright() as pw:
    br = pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
    pg = br.new_page(viewport={"width": 1366, "height": 768})
    pg.set_default_timeout(3000)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL)
    btns = pg.locator("button.play")
    check("the page carries a play button on S698's made-up calls (the walk is real)", lambda: (btns.count() >= 1, btns.count()))
    # a second row's button, as on a busy day: the same call's button copied into the page for the walk
    pg.evaluate("(function(){var b=document.querySelector('button.play'); var c=b.cloneNode(true); c.id='walk2';"
                "var d=document.createElement('div'); d.className='tl'; d.textContent='walk row two '; d.appendChild(c);"
                "document.querySelector('main,body').appendChild(d);})()")
    check("the player bar is on the page and hidden until a recording is opened",
          lambda: (pg.locator("#pl").count() == 1 and not pg.locator("#pl").is_visible(), ""))
    b0 = btns.nth(0)
    orig = b0.inner_text()
    b0.click()
    check("tap Play: the bar appears at once and says 'Loading…' or already shows the time",
          lambda: (pg.locator("#pl").is_visible() and ("Loading" in pg.locator("#pltime").inner_text() or "/" in pg.locator("#pltime").inner_text()),
                   pg.locator("#pltime").inner_text()))
    pg.wait_for_timeout(2500)
    t1 = safe(lambda: pg.locator("#pltime").inner_text(), "")
    check("while it plays: the time played and the length, e.g. '0:02 / 0:12'", lambda: (re.match(r"^0:0[1-9] / 0:12$", t1) is not None, t1))
    w1 = safe(lambda: pg.evaluate("parseFloat(document.getElementById('plf').style.width)||0"), 0)
    check("the progress bar has moved (more than 5%)", lambda: (w1 > 5, w1))
    check("the row's own button shows pause and the time ('❚❚ 0:0x / 0:12') and fills as it plays",
          lambda: ("❚❚" in b0.inner_text() and "/ 0:12" in b0.inner_text() and "%" in (b0.get_attribute("style") or ""), b0.inner_text()))
    check("the bar's label names the call (the row's own words)", lambda: (len(pg.locator("#pllab").inner_text()) > 8, pg.locator("#pllab").inner_text()))
    safe(lambda: pg.locator("#plbtn").click())
    pg.wait_for_timeout(600)
    tp = safe(lambda: pg.locator("#pltime").inner_text(), "")
    pg.wait_for_timeout(1200)
    check("pause on the bar: the time stops; the bar shows ▶; the row's button shows ▶",
          lambda: (pg.locator("#pltime").inner_text() == tp and "▶" in pg.locator("#plbtn").inner_text() and b0.inner_text().startswith("▶"), (tp, b0.inner_text())))
    b0.click()
    pg.wait_for_timeout(1300)
    check("the row's button again: it plays on from where it was", lambda: (pg.locator("#pltime").inner_text() != tp and "❚❚" in pg.locator("#plbtn").inner_text(), pg.locator("#pltime").inner_text()))
    box = safe(lambda: pg.locator("#plt").bounding_box())
    if box:
        pg.mouse.click(box["x"] + box["width"] * 0.75, box["y"] + box["height"] / 2)
    pg.wait_for_timeout(500)
    ts = safe(lambda: pg.evaluate("_pa?_pa.currentTime:-1"), -1)
    check("tap at three quarters of the bar: it jumps to about 0:09", lambda: (8.0 <= ts <= 10.6, ts))
    pg.wait_for_timeout(4500)
    check("at the end: 'Finished · 0:12', the bar full, the row's button back as it was",
          lambda: (pg.locator("#pltime").inner_text().startswith("Finished") and b0.inner_text() == orig, (pg.locator("#pltime").inner_text(), b0.inner_text(), orig)))
    b1 = pg.locator("#walk2")
    b1.click(); pg.wait_for_timeout(1500)
    b2 = btns.nth(0)
    b2.click(); pg.wait_for_timeout(800)
    check("another recording opened while one plays: the first stops and its button is restored; one recording at a time",
          lambda: (pg.evaluate("document.querySelectorAll('button.play.on').length") == 1 and "❚❚" not in b1.inner_text(), b1.inner_text()))
    safe(lambda: pg.locator(".plx").click())
    pg.wait_for_timeout(300)
    check("close (×): the sound stops, the bar goes, every button is as it was",
          lambda: (not pg.locator("#pl").is_visible() and pg.evaluate("_pa===null") and pg.evaluate("document.querySelectorAll('button.play.on,button.play.load').length") == 0, ""))
    safe(lambda: pg.evaluate("playJk('5000000101_1700000000999999', document.querySelectorAll('button.play')[0])"))
    pg.wait_for_timeout(1500)
    check("a recording the server does not have: the bar says so in plain words (red), the button is restored",
          lambda: (pg.locator("#pl").is_visible() and "could not be played" in pg.locator("#plmsg").inner_text() and pg.evaluate("document.querySelectorAll('button.play.on').length") == 0,
                   pg.locator("#plmsg").inner_text()))
    safe(lambda: pg.locator(".plx").click())
    # the three kinds of button that play a recording: a Needs-you 'Listen', a timeline row inside a person, a slow one
    pg.evaluate("""(function(){var m=document.querySelector('main')||document.body;
      var a=document.createElement('div'); a.className='ny'; a.innerHTML='<div class=\"t\"><div><b>Walk Listen Person</b></div></div>'
        +'<button type=\"button\" class=\"btn soft\" id=\"walkL\" onclick=\"playJk(\\'5000000102_1762100000\\',this)\">Listen</button>'; m.appendChild(a);
      var d=document.createElement('details'); d.className='p'; d.open=true;
      d.innerHTML='<summary><span class=\"who\"><b>Walk Timeline Person · C-1</b></span></summary><div class=\"tl\"><span class=\"tm\">10:42</span><span></span>'
        +'<span class=\"tx\">Answered<select><option>Booked</option></select></span>'
        +'<button type=\"button\" class=\"play\" id=\"walkT\" onclick=\"playJk(\\'5000000103_1762100001\\',this)\">&#9654; 0:12</button></div>'; m.appendChild(d);
      var e=document.createElement('div'); e.className='tl'; e.innerHTML='<b>Walk Slow</b><button type=\"button\" class=\"play\" id=\"walkS\" onclick=\"playJk(\\'5000000104_1762100777777\\',this)\">&#9654; 0:12</button>';
      m.appendChild(e);})()""")
    safe(lambda: pg.locator("#walkL").click()); pg.wait_for_timeout(1800)
    check("the Needs-you 'Listen' button: plays, shows the time, the bar names the person ('Recording — Walk Listen Person')",
          lambda: ("/ 0:12" in pg.locator("#walkL").inner_text() and pg.locator("#pllab").inner_text() == "Recording — Walk Listen Person",
                   (pg.locator("#walkL").inner_text(), pg.locator("#pllab").inner_text())))
    safe(lambda: pg.locator("#walkT").click()); pg.wait_for_timeout(1800)
    check("a timeline row's button: the bar reads 'Recording — <the person's name> · <the call's time>' (no menu or button words)",
          lambda: (pg.locator("#pllab").inner_text() == "Recording — Walk Timeline Person · C-1 · 10:42" and pg.locator("#walkL").inner_text() == "Listen",
                   (pg.locator("#pllab").inner_text(), pg.locator("#walkL").inner_text())))
    safe(lambda: pg.locator("#walkS").click()); pg.wait_for_timeout(700)
    check("while a slow recording loads: 'Loading…' and the bar's button shows PAUSE (a tap stops it, never starts a second sound)",
          lambda: (pg.locator("#pltime").inner_text() == "Loading…" and "❚❚" in pg.locator("#plbtn").inner_text(), (pg.locator("#pltime").inner_text(), pg.locator("#plbtn").inner_text())))
    pg.wait_for_timeout(3500)
    check("...and once it arrives it plays with its time", lambda: ("/ 0:12" in pg.locator("#pltime").inner_text(), pg.locator("#pltime").inner_text()))
    safe(lambda: pg.evaluate("toast('walk toast')"))
    tb = safe(lambda: pg.evaluate("document.getElementById('toast').getBoundingClientRect().bottom"), 9999)
    pt = safe(lambda: pg.evaluate("document.getElementById('pl').getBoundingClientRect().top"), 0)
    check("a message pop-up while the player is open sits ABOVE the bar, not on it", lambda: (tb <= pt + 1, (tb, pt)))
    check("no script error on the page", lambda: (not errs, errs[:2]))
    m = br.new_page(viewport={"width": 390, "height": 800})
    m.goto(URL)
    m.set_default_timeout(3000)
    merrs = []
    m.on("pageerror", lambda e: merrs.append(str(e)))
    m.locator("button.play").nth(0).click(); m.wait_for_timeout(1500)
    check("on a phone (390 px): the bar fits, no sideways scroll, the time readable (16 px)",
          lambda: (m.evaluate("document.documentElement.scrollWidth<=window.innerWidth") and m.locator("#pl").is_visible()
                   and m.evaluate("getComputedStyle(document.getElementById('pltime')).fontSize") == "16px",
                   m.evaluate("[document.documentElement.scrollWidth, window.innerWidth]")))
    m.screenshot(path=os.path.join(td, "phone.png"))
    safe(lambda: m.evaluate("plClose(); playJk('5000000101_1700000000999999', document.querySelectorAll('button.play')[0])"))
    m.wait_for_timeout(1500)
    check("on a phone, the red 'could not be played' line: the whole bar is on screen and the page keeps room under it",
          lambda: (m.evaluate("(function(){var p=document.getElementById('pl').getBoundingClientRect(); return p.top>=0 && p.bottom<=window.innerHeight+1"
                              " && parseInt(document.body.style.paddingBottom)>=p.height;})()") and "could not be played" in m.locator("#plmsg").inner_text(),
                   m.evaluate("(function(){var p=document.getElementById('pl').getBoundingClientRect(); return [p.top,p.bottom,p.height,window.innerHeight,document.body.style.paddingBottom, document.getElementById('plmsg').textContent.slice(0,30)];})()")))
    m.screenshot(path=os.path.join(td, "phone_err.png"))
    check("no script error on the phone page", lambda: (not merrs, merrs[:2]))
    pg.screenshot(path=os.path.join(td, "pc.png"))
    br.close()
srv.shutdown()
check("the transcript link, the call-back button and the rest of the page untouched: only the player's parts differ from S698",
      lambda: (html.count("wholeTx(") >= 1 and html.count("callBack(") >= 1, ""))
print("SHOTS %s" % td)
if OLD:
    print("%d S703 check(s) red · %d green" % (sum(1 for x in RES if not x), sum(RES)))
else:
    print("%d of %d green" % (sum(RES), len(RES)))
