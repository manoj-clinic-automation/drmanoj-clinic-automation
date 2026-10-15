#!/usr/bin/env python3
"""run_browser_walk_s560.py -- S560's browser walk: the desk on one screen, in the PC's headless Chrome. A small server on
127.0.0.1 serves the desk's page and its JSON answers as the kit's build gave them on made-up rows (walk_s560.py --save-pages,
made-up rows only), and takes the page's report on /result. The live box is not reached; nothing leaves the PC.

    python -B run_browser_walk_s560.py <chrome.exe> <pages dir> <work dir>

Sizes: 1366 x 768, 1280 x 720, 1920 x 1080 (the window); FIX1 N1: window 1390 x 719 = a viewport of exactly 1366 x 620 (a real
1366 x 768 laptop's browser area, taskbar and Chrome's bars taken off); and for the record 1366 x 740 and 1366 x 625. Scenes: the Bill view (every destination, the kinds, Save, the join / blank row -- no scrolling);
Receipt; Statement (the difference line); the construction tick. Prints the results; exit 1 on any RED."""
import http.server, json, os, re, socket, subprocess, sys, threading, time, urllib.parse

CHROME, PAGES, WORK = sys.argv[1:4]
CONTROL = "--control" in sys.argv                                         # the same measure on the live (S559) desk: must be RED
HERE = os.path.dirname(os.path.abspath(__file__))
IDS = json.load(open(os.path.join(PAGES, "ids.json")))
RES, EV = {}, threading.Event()
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
        q = dict(urllib.parse.parse_qsl(u.query))
        if u.path == "/desk":
            raw = open(os.path.join(PAGES, "desk.html"), encoding="utf-8").read()
            raw = re.sub(r'"open": \d+', '"open": %d' % IDS[q.get("p", "bill")], raw)
            raw = raw.replace(">Walk Owner</a>", ">Dr Xxxxx Xxxxxxxxxxx</a>")
            raw = re.sub(r">Sorting desk \(\d+\)<", ">Sorting desk (123)<", raw)
            raw = re.sub(r">Bills awaited \(\d+\)<", ">Bills awaited (45)<", raw)
            raw = raw.replace("<head>", "<head>" + ERRS, 1).replace("</body>", "<script src=\"/layout.js?sc=%s\"></script></body>" % q.get("sc", "bill"))
            raw = raw.replace("/layout.js?sc=%s\"" % q.get("sc", "bill"), "/layout.js\"")
            raw = raw.replace("<script src=\"/layout.js\">", "<script>history.replaceState(null,'','/desk?sc=%s');</script><script src=\"/layout.js\">" % q.get("sc", "bill"))
            return self.send(raw.encode("utf-8"), "text/html; charset=utf-8")
        if u.path == "/desk/api/list":
            return self.send(open(os.path.join(PAGES, "list.json"), "rb").read(), "application/json")
        m = re.match(r"^/desk/api/paper/(\d+)$", u.path)
        if m and os.path.exists(os.path.join(PAGES, "paper_%s.json" % m.group(1))):
            return self.send(open(os.path.join(PAGES, "paper_%s.json" % m.group(1)), "rb").read(), "application/json")
        if u.path == "/layout.js":
            return self.send(open(os.path.join(HERE, "layout.js"), "rb").read(), "application/javascript")
        if re.match(r"^/bills/\d+/file$", u.path):
            return self.send(b"<!doctype html><body style='background:#fbfaf7'>made-up scan</body>", "text/html")
        return self.send(b"{}", "application/json", 404)

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
PROFILE = os.path.abspath(os.path.join(WORK, "chrome_profile_%d" % int(time.time())))
os.makedirs(PROFILE, exist_ok=True)


def run(p, sc, size, wait=60):
    RES.pop("last", None); EV.clear()
    url = "http://127.0.0.1:%d/desk?p=%s&sc=%s" % (PORT, p, sc)
    pr = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                           "--mute-audio", "--hide-scrollbars", "--user-data-dir=" + PROFILE, "--window-size=" + size, url],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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


TITLES = ["Clinic consumables", "Clinic expense", "My expense — Dr MK / Dr Bhawna", "Handed over", "Documents", "Not here"]
t0 = time.time()
if CONTROL:
    oks = []
    for size in ("1366,768", "1390,719"):                                 # FIX1 N1: and at a real laptop's 1366 x 620
        r = run("bill", "bill", size)
        hid = r.get("hidden") or []
        print("CONTROL the live (S559) desk at window %s (viewport %sx%s): %d of %d destination buttons hidden below the fold: %s" % (
            size.replace(",", " x "), r.get("vw"), r.get("vh"), len([h for h in hid if h not in ("Save", "Blank — discard")]), r.get("nDest"), hid), flush=True)
        oks.append(bool(r.get("nDest") and hid))
    srv.shutdown()
    sys.exit(0 if all(oks) else 1)
for size in ("1366,768", "1280,720", "1920,1080", "1390,719", "1366,740", "1366,625"):
    r = run("bill", "bill", size)
    print("  %s: %s" % (size, json.dumps({k: r.get(k) for k in ("vw", "vh", "nDest", "nKind", "hidden", "below", "minBtn", "fieldsScroll", "cue",
                                                                  "pageScroll", "saveText", "readFolded", "errs")}, ensure_ascii=False)), flush=True)
    base = (r.get("nDest") == 15 and r.get("nKind") == 5 and r.get("titles") == TITLES and (r.get("minBtn") or 0) >= 36 and not r.get("pageScroll")
            and r.get("readFolded") and not r.get("errs"))
    allvis = not r.get("hidden")
    if size in ("1366,768", "1920,1080"):
        line(base and allvis and r.get("fieldsScroll", 1) <= 0,
             "L  %s (viewport %sx%s): every destination (15 buttons, six groups in order), the five kinds, Save and the join / blank row on "
             "screen, nothing scrolls; What was read folded to one line; buttons >= 36 px" % (size.replace(",", " x "), r.get("vw"), r.get("vh")),
             "hidden %s, fields overflow %s px" % (r.get("hidden"), r.get("fieldsScroll")))
    elif size == "1280,720":
        ok = base and (allvis or (set(r.get("below") or []) <= {"Documents", "Not here"} and r.get("cue") and not r.get("hiddenOther")))
        line(ok, "L  1280 x 720 (viewport %sx%s): the same -- or at worst only the Documents / Not here row below the fold, with the "
                 "visible 'more' cue" % (r.get("vw"), r.get("vh")),
             "all visible %s; below %s; cue %s; kinds / Save / join-blank hidden %s" % (allvis, r.get("below"), r.get("cue"), r.get("hiddenOther")))
    elif size == "1390,719":                                              # FIX1 N1: a real 1366 x 768 laptop's browser area, 1366 x 620
        ok = (base and r.get("vw") == 1366 and r.get("vh") == 620
              and (allvis or (set(r.get("below") or []) <= {"Not here"} and r.get("cue") and not r.get("hiddenOther"))))
        line(ok, "L  1366 x 620 (a real 1366 x 768 laptop's browser area; viewport %sx%s): every destination, the five kinds and Save on "
                 "screen without scrolling -- only Not here may fall under the 'more' cue" % (r.get("vw"), r.get("vh")),
             "all visible %s; below %s; cue %s; kinds / Save / join-blank hidden %s; fields overflow %s px" % (
                 allvis, r.get("below"), r.get("cue"), r.get("hiddenOther"), r.get("fieldsScroll")))
    else:
        print("  (for the record, window %s = viewport %sx%s -- a 1366 x 768 laptop with the taskbar and Chrome's bars: all visible %s; below the fold %s; 'more' cue %s)"
              % (size.replace(",", " x "), r.get("vw"), r.get("vh"), allvis, sorted(set(r.get("below") or [])), r.get("cue")), flush=True)
rr = run("receipt", "receipt", "1366,768")
print("  receipt: %s" % json.dumps({k: rr.get(k) for k in ("rcptShown", "radios", "pre", "filed", "groupsHidden", "afterMode", "saveVisible", "saveText", "errs")}, ensure_ascii=False), flush=True)
line(rr.get("rcptShown") and (rr.get("radios") or 0) >= 3 and rr.get("pre") and rr.get("groupsHidden") and "Filed with" in (rr.get("filed") or "")
     and rr.get("saveVisible") and rr.get("saveText") == "Save — next paper" and not rr.get("errs"),
     "R  Receipt (1366 x 768): 'Pays which bill?' with the supplier's unpaid bills, the likely one pre-ticked, 'No bill -- paid directly', "
     "'A statement'; filed with that bill (the destinations give way to 'Filed with ...'); payment boxes pre-filled; Save on screen",
     "radios %s pre %s save '%s'" % (rr.get("radios"), rr.get("pre"), rr.get("saveText")))
rs = run("statement", "statement", "1366,768")
print("  statement: %s" % json.dumps({k: rs.get(k) for k in ("stmtShown", "offered", "ticked", "diff", "grey", "filed", "saveVisible", "saveText", "errs")}, ensure_ascii=False), flush=True)
line(rs.get("stmtShown") and rs.get("ticked") == 3 and rs.get("diff") == "Ticked ₹1,200 of statement ₹1,300 — difference ₹100" and rs.get("grey") is True
     and rs.get("saveVisible") and rs.get("saveText") == "Save — next paper" and not rs.get("errs"),
     "S  Statement (1366 x 768): period typed -> the three invoices inside it pre-ticked; 'Ticked Rs1,200 of statement Rs1,300 -- "
     "difference Rs100' and the grey 'An invoice may not be scanned yet.'; Save on screen",
     "ticked %s diff '%s' grey %s" % (rs.get("ticked"), rs.get("diff"), rs.get("grey")))
rc = run("bill", "construction", "1366,768")
line(rc.get("accShown") and rc.get("accOff") and rc.get("accHiddenForEstimate") and not rc.get("errs"),
     "C  Construction work + Bill: 'Send to accountant' shown, off by default, on screen; hidden for an estimate",
     json.dumps({k: rc.get(k) for k in ("accShown", "accOff", "accHiddenForEstimate", "errs")}))
print("%d browser checks: %d GREEN, %d RED%s  (%.0f s)" % (len(OUT), len(OUT) - len(REDS), len(REDS), (" (" + "; ".join(r_[:3] for r_ in REDS) + ")") if REDS else "", time.time() - t0))
srv.shutdown()
sys.exit(1 if REDS else 0)
