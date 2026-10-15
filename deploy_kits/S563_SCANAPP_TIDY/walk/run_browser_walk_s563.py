#!/usr/bin/env python3
"""run_browser_walk_s563.py -- S563's browser walk in the PC's headless Chrome (S559's shape). A small server on 127.0.0.1
serves the widget (OLD = the live 1128ac97, NEW = the kit's build), OpenCV.js (the live copy, ff1e10e7) and harness_s563.js,
answers every upload with a made-up stamp, and takes the page's report on /result. Made-up photos only; nothing leaves the PC.
With --desk: the desk's page and JSON answers as the kit's build gave them on made-up rows (walk_s563.py --save-pages), the
F-902 line measured on a set-aside paper.

    python -B run_browser_walk_s563.py <chrome.exe> <old widget> <new widget> <opencv.js> <work dir> [--desk <pages dir>]

Item 10: scene G (a page deleted while an Adjust picture is still loading) and scene H (the stage button's page number after
the shift), each on NEW and on OLD (the control: OLD must show the fault). The seven surfaces (the finance app's five, the scan
app's asset page and intake), each with its own SCANNER_CONFIG, OLD and NEW: the same screen and the same upload byte for
byte. Prints the results; exit 1 on any RED."""
import http.server, json, os, re, socket, subprocess, sys, threading, time, urllib.parse

_A = sys.argv[1:]
DESK = None
if "--desk" in _A:
    DESK = _A[_A.index("--desk") + 1]
    del _A[_A.index("--desk"):_A.index("--desk") + 2]
CHROME, OLD, NEW, OCV, WORK = _A[0:5]
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = {"fileField": "file", "allowIdCard": False, "allowBatch": False, "backUrl": "#saved"}
SURF = [
    ("finance day scan", dict(BASE, title="Day — 2099-01-01", uploadUrl="/finance/api/day/2099-01-01/scan/z", uploadFields={"unit": "U", "business_date": "2099-01-01", "doc_type": "z"}, nameBase="S_z")),
    ("finance non-cash", dict(BASE, title="NC -- 2099-01-01", uploadUrl="/finance/api/day/2099-01-01/noncash-scan/u", uploadFields={"unit": "U", "business_date": "2099-01-01", "noncash_uid": "u"}, nameBase="S_b")),
    ("finance expense", dict(BASE, title="Ex — 2099-01-01", uploadUrl="/finance/api/day/2099-01-01/expense-scan/u", uploadFields={"unit": "U", "business_date": "2099-01-01", "expense_uid": "u"}, nameBase="S_e")),
    ("finance clinic day", dict(BASE, title="C — 2099-01-01", uploadUrl="/finance/clinic/api/day/2099-01-01/scan/z", uploadFields={"unit": "C", "business_date": "2099-01-01", "doc_type": "z"}, nameBase="C_z")),
    ("finance clinic expense", dict(BASE, title="CE — 2099-01-01", uploadUrl="/finance/clinic/api/day/2099-01-01/expense-scan/u", uploadFields={"unit": "C", "business_date": "2099-01-01", "expense_uid": "u"}, nameBase="C_e")),
    ("scan app asset page", dict(BASE, title="Asset 1", uploadUrl="/scanapp/files/upload", uploadFields={"entity": "asset", "entity_id": "1"}, nameBase="asset_1", allowIdCard=True)),
    ("scan app intake (smart)", dict(BASE, title="Scan the bill", uploadUrl="/scanapp/intake/scan_submit", fileField="bill_scan", uploadFields={"lane": "clinic", "bill_month": "2099-01"},
                                     nameBase="bill", autoPage=True, inlineStamp=True, retryUpload=True, directFile=True, slipJsonUrl="/x/{id}", cvScan=True, cvUrl="/opencv.js")),
]
CFG = dict(SURF)
RES = {}
EV = threading.Event()
ERRS = "<script>window.__errs=[];window.addEventListener('error',function(e){window.__errs.push(String(e.message));});</script>"
IDS = json.load(open(os.path.join(DESK, "ids.json"))) if DESK else {}


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
        if u.path == "/page":
            cfg = CFG[q["s"]]
            body = ("<!doctype html><html><head><meta charset=utf-8></head><body><div id=scanroot></div>"
                    "<script>window.SCANNER_CONFIG = %s;</script><script src=\"/harness_s563.js\"></script>"
                    "<script src=\"/widget_%s.js\"></script></body></html>") % (json.dumps(cfg), q["w"])
            return self.send(body.encode("utf-8"), "text/html; charset=utf-8")
        if u.path == "/syntax":                                           # node --check's equivalent in V8 (no node here)
            body = ("<!doctype html><html><head><meta charset=utf-8></head><body><script>"
                    "fetch('/widget_%s.js').then(function(r){return r.text();}).then(function(t){var o={len:t.length};"
                    "try{new Function(t);o.ok=true;}catch(e){o.ok=false;o.err=String(e);}"
                    "return fetch('/result',{method:'POST',body:JSON.stringify(o)});});</script></body></html>") % q["w"]
            return self.send(body.encode("utf-8"), "text/html; charset=utf-8")
        if u.path == "/desk" and DESK:
            raw = open(os.path.join(DESK, "desk.html"), encoding="utf-8").read()
            raw = re.sub(r'"open": \d+', '"open": %d' % IDS[q.get("p", "aside")], raw)
            raw = raw.replace("<head>", "<head>" + ERRS, 1).replace("</body>", "<script src=\"/aside.js\"></script></body>")
            return self.send(raw.encode("utf-8"), "text/html; charset=utf-8")
        if u.path == "/desk/api/list" and DESK:
            return self.send(open(os.path.join(DESK, "list.json"), "rb").read(), "application/json")
        mm = re.match(r"^/desk/api/paper/(\d+)$", u.path)
        if mm and DESK and os.path.exists(os.path.join(DESK, "paper_%s.json" % mm.group(1))):
            return self.send(open(os.path.join(DESK, "paper_%s.json" % mm.group(1)), "rb").read(), "application/json")
        if re.match(r"^/bills/\d+/file$", u.path):
            return self.send(b"<!doctype html><body style='background:#fbfaf7'>made-up scan</body>", "text/html")
        files = {"/harness_s563.js": os.path.join(HERE, "harness_s563.js"), "/aside.js": os.path.join(HERE, "aside.js"),
                 "/widget_old.js": OLD, "/widget_new.js": NEW, "/opencv.js": OCV}
        if u.path in files:
            return self.send(open(files[u.path], "rb").read(), "application/javascript")
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


def run(url, size="1366,900", wait=180):
    RES.pop("last", None); EV.clear()
    p = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                          "--mute-audio", "--hide-scrollbars", "--user-data-dir=" + PROFILE, "--window-size=" + size, url],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    EV.wait(wait)
    p.terminate()
    try:
        p.wait(15)
    except Exception:                                                     # noqa: BLE001
        p.kill()
    return RES.get("last") or {"errs": ["no report from the page within %d s" % wait]}


def page(w, s, sc):
    return run("http://127.0.0.1:%d/page?w=%s&s=%s&sc=%s" % (PORT, w, urllib.parse.quote(s), sc))


OUT, REDS = [], []


def line(ok, name, detail=""):
    OUT.append(("GREEN " if ok else "RED   ") + name + (("  -- " + detail) if detail else ""))
    print(OUT[-1], flush=True)
    if not ok:
        REDS.append(name)


t0 = time.time()
SY = run("http://127.0.0.1:%d/syntax?w=new" % PORT, wait=60)
line(SY.get("ok") is True and SY.get("len") == sum(2 if ord(c) > 0xFFFF else 1 for c in open(NEW, encoding="utf-8").read()),
     "V  the new widget compiles in V8 (Chrome's JavaScript engine): parsed whole, not run -- node --check's equivalent",
     "%s %s" % (SY.get("len"), SY.get("err") or SY.get("errs")))
# --------------------------------------------------------------- item 10 on the intake: NEW and OLD (the control)
RG = {(w, sc): page(w, "scan app intake (smart)", sc) for w in ("new", "old") for sc in ("G", "H")}
for k, v in sorted(RG.items()):
    print("  %s %s: %s" % (k[0], k[1], json.dumps({x: v.get(x) for x in ("ready", "adjBefore", "adjAfter", "adj", "left", "stage", "label0", "label",
                                                                        "u1", "errs")}, ensure_ascii=False)), flush=True)


def pdf_words(v):
    nm = {v.get("p1"): "page1", v.get("p2"): "page2", v.get("p3"): "page3"}
    return "[" + ", ".join(nm.get(h, "an adjusted page" if h else "?") for h in (v.get("pdf") or [])) + "]"


nG, oG, nH, oH = RG[("new", "G")], RG[("old", "G")], RG[("new", "H")], RG[("old", "H")]
line(nG.get("ready") and nG.get("adjBefore") == -1 and nG.get("adjAfter") == -1 and nG.get("stage") == "none" and nG.get("left") == 2
     and nG.get("u1") == 1 and (nG.get("pdf") or []) == [nG.get("p2"), nG.get("p3")] and not nG.get("errs"),
     "G  (S559-K2-N7) page 1 deleted while page 2's Adjust picture is still loading (700 ms late): the late picture is IGNORED -- no "
     "stage opens, no page is adjusted; Save makes ONE paper of the two pages left, each as it was (page 2, page 3)",
     "adjust after %s stage %s saved %s" % (nG.get("adjAfter"), nG.get("stage"), pdf_words(nG)))
line(oG.get("adjAfter") == 1 and oG.get("stage") == "block" and nG.get("p3") and oG.get("p3") not in (oG.get("pdf") or []),
     "G' CONTROL (the live widget 1128ac97): the late picture of page 2 opens on the slot now holding page 3 ('%s') -- the WRONG page "
     "is adjusted: Theek hai puts page 2's picture there and page 3 is lost from the saved paper" % (oG.get("label") or ""),
     "adjust after %s stage %s saved %s" % (oG.get("adjAfter"), oG.get("stage"), pdf_words(oG)))
line(nH.get("label0", "").endswith("page 3") and nH.get("adj") == 1 and nH.get("label", "").endswith("page 2") and nH.get("stage") == "block"
     and nH.get("u1") == 1 and len(nH.get("pdf") or []) == 2 and (nH.get("pdf") or [None])[0] == nH.get("p2") and not nH.get("errs"),
     "H  page 3 under adjustment, page 1 deleted: the stage button now names the page under adjustment ('%s', was '%s'); Theek hai -> "
     "Save: one paper, page 2 and the adjusted page" % (nH.get("label"), nH.get("label0")),
     "adj %s saved %s" % (nH.get("adj"), pdf_words(nH)))
line(oH.get("adj") == 1 and oH.get("label", "").endswith("page 3"),
     "H' CONTROL (the live widget): after the same delete the stage button still says '%s' while page 2 is under adjustment" % (oH.get("label") or ""),
     "adj %s" % oH.get("adj"))
# --------------------------------------------------------------- the seven surfaces, OLD and NEW
for name, cfg in SURF:
    do, dn = page("old", name, "dom"), page("new", name, "dom")
    same = do.get("dom") == dn.get("dom") and do.get("dom")
    if cfg.get("cvScan"):
        line(same and dn.get("ready") and not dn.get("errs") and dn.get("s559") == "S559.1" and do.get("s559") == "S559.1",
             "S  %-24s loads: the same screen as the live widget (DOM identical), OpenCV ready, no error, the S559 mark as before" % name)
        continue
    so, sn = page("old", name, "save"), page("new", name, "save")
    line(same and not dn.get("errs") and not do.get("errs") and dn.get("on") is False and dn.get("s559") is None
         and so.get("upsSummary") and so.get("upsSummary") == sn.get("upsSummary") and sn.get("hash") == so.get("hash") == "#saved"
         and so.get("pageh") == sn.get("pageh"),
         "S  %-24s loads and saves exactly as with the live widget: DOM identical, no error, smart path off; the same page, the same "
         "upload (fields, file name, type, size, bytes), the same way back" % name,
         "dom %s ups %s" % (bool(same), so.get("upsSummary") == sn.get("upsSummary")))
# --------------------------------------------------------------- the desk: F-902's line on a set-aside paper
if DESK:
    for size, label in (("1366,768", "1366 x 768"), ("1390,719", "1366 x 620 (a real laptop's browser area)"), ("1920,1080", "1920 x 1080")):
        r = run("http://127.0.0.1:%d/desk?p=aside" % PORT, size, wait=60)
        print("  aside %s: %s" % (size, json.dumps({k: r.get(k) for k in ("vw", "vh", "nDest", "below", "hiddenOther", "cue", "asideText", "asideCount",
                                                                          "restoreCount", "asideVis", "restoreVis", "saveText1", "saveOn1", "errs")}, ensure_ascii=False)), flush=True)
        okb = (r.get("nDest") == 15 and r.get("asideCount") == 1 and r.get("restoreCount") == 1 and r.get("asideVis") and r.get("restoreVis")
               and re.fullmatch(r"Already set aside on \d\d-\d\d-\d{4} — Restore\?", r.get("asideText") or "") is not None
               and not r.get("pageScroll") and not r.get("hiddenOther") and r.get("pageboxShown") is False and r.get("saveOn1") is False
               and r.get("saveText1") == "Restore it first (above)" and not r.get("errs"))
        fits = (not r.get("below")) or (set(r.get("below") or []) <= {"Documents", "Not here", "Handed over"} and r.get("cue"))
        line(okb and fits, "A  the desk at %s with F-902's line: ONE 'Already set aside on dd-mm-yyyy — Restore?' and ONE Restore button on "
             "screen; the kinds and Save on screen (the join / blank row not offered on a set-aside paper, as today); the destinations on screen (at worst the last rows under the "
             "visible 'more' cue); a destination chosen -> Save held: 'Restore it first (above)'" % label,
             "below %s cue %s hidden %s save '%s'" % (r.get("below"), r.get("cue"), r.get("hiddenOther"), r.get("saveText1")))
print("%d browser checks: %d GREEN, %d RED%s  (%.0f s)" % (len(OUT), len(OUT) - len(REDS), len(REDS), (" (" + "; ".join(r_[:3] for r_ in REDS) + ")") if REDS else "", time.time() - t0))
srv.shutdown()
sys.exit(1 if REDS else 0)
