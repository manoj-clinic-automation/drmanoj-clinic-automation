#!/usr/bin/env python3
"""run_browser_walk.py -- S559's browser walk (item 10, and the bar's fit at 1366 px). Headless Chrome; a small server on
127.0.0.1 serves the widget (OLD = the live 1143c77b, NEW = the kit's build), OpenCV.js (the live copy, ff1e10e7) and harness.js,
answers every upload with a made-up stamp, and takes the page's report on /result. Made-up photos only; nothing leaves the PC.

    python -B run_browser_walk.py <chrome.exe> <old widget> <new widget> <opencv.js> <work dir> [<pages dir for the fit>]
                                  [--prev <the first S559 build's widget, 552effcd>]

The seven surfaces (the finance app's five, the scan app's asset page and intake) are each loaded with their own
SCANNER_CONFIG shape (as S545's walk7.js did), OLD and NEW. S559_FIX1: scenes E (C1) and F (C2) run on NEW, on PREV (the
first S559 build -- each must be red there) and on OLD. Prints the results; exit 1 on any RED."""
import http.server, json, os, re, socket, subprocess, sys, threading, time, urllib.parse

_A = sys.argv[1:]
PREV = None
if "--prev" in _A:                                                        # S559_FIX1
    PREV = _A[_A.index("--prev") + 1]
    del _A[_A.index("--prev"):_A.index("--prev") + 2]
CHROME, OLD, NEW, OCV, WORK = _A[0:5]
FIT = _A[5] if len(_A) > 5 else None
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
                    "<script>window.SCANNER_CONFIG = %s;</script><script src=\"/harness.js\"></script>"
                    "<script src=\"/widget_%s.js\"></script></body></html>") % (json.dumps(cfg), q["w"])
            return self.send(body.encode("utf-8"), "text/html; charset=utf-8")
        if u.path == "/syntax":                                           # S559_FIX1: node --check's equivalent in V8 (no node here)
            body = ("<!doctype html><html><head><meta charset=utf-8></head><body><script>"
                    "fetch('/widget_%s.js').then(function(r){return r.text();}).then(function(t){var o={len:t.length};"
                    "try{new Function(t);o.ok=true;}catch(e){o.ok=false;o.err=String(e);}"
                    "return fetch('/result',{method:'POST',body:JSON.stringify(o)});});</script></body></html>") % q["w"]
            return self.send(body.encode("utf-8"), "text/html; charset=utf-8")
        if u.path == "/fit":
            raw = open(os.path.join(FIT, q["p"] + ".html"), "rb").read().decode("utf-8")
            raw = raw.replace(">Walk Owner</a>", ">Dr Xxxxx Xxxxxxxxxxx</a>")                     # a long real-length name
            raw = re.sub(r">Sorting desk \(\d+\)<", ">Sorting desk (123)<", raw)
            raw = re.sub(r">Bills awaited \(\d+\)<", ">Bills awaited (45)<", raw)
            raw = raw.replace("</body>", "<script src=\"/fit.js\"></script></body>")
            return self.send(raw.encode("utf-8"), "text/html; charset=utf-8")
        files = {"/harness.js": os.path.join(HERE, "harness.js"), "/fit.js": os.path.join(HERE, "fit.js"),
                 "/widget_old.js": OLD, "/widget_new.js": NEW, "/widget_prev.js": PREV or NEW, "/opencv.js": OCV}
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
PROFILE = os.path.abspath(os.path.join(WORK, "chrome_profile_%d" % int(time.time())))      # Chrome needs an absolute profile path
os.makedirs(PROFILE, exist_ok=True)


def run(url, size="1366,900", wait=180):
    RES.pop("last", None); EV.clear()
    p = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                          "--mute-audio", "--user-data-dir=" + PROFILE, "--window-size=" + size, url],
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
# --------------------------------------------------------------- 0. S559_FIX1: the new widget compiles (V8 parses it, nothing runs)
SY = run("http://127.0.0.1:%d/syntax?w=new" % PORT, wait=60)
line(SY.get("ok") is True and SY.get("len") == sum(2 if ord(c) > 0xFFFF else 1 for c in open(NEW, encoding="utf-8").read()),
     "V  the new widget compiles in V8 (Chrome's JavaScript engine, the one node uses): parsed whole, not run -- node --check's equivalent",
     "%s %s" % (SY.get("len"), SY.get("err") or SY.get("errs")))
# --------------------------------------------------------------- 1. item 10 on the intake: OLD (the control) and NEW
R = {(w, sc): page(w, "scan app intake (smart)", sc) for w in ("old", "new") for sc in ("A", "B", "C", "D")}
for k, v in sorted(R.items()):
    print("  %s %s: %s" % (k[0], k[1], json.dumps({x: v.get(x) for x in ("ready", "label0", "u1", "u2", "stage", "label", "pagesAfterTap", "stageLeft", "uSame", "uDiff", "errs")})), flush=True)
nA, oA, nB, oB = R[("new", "A")], R[("old", "A")], R[("new", "B")], R[("old", "B")]
nC, oC, nD, oD = R[("new", "C")], R[("old", "C")], R[("new", "D")], R[("old", "D")]
padj = nB.get("padj")
line(nA.get("ready") and nA.get("u1") == 1 and nA.get("u2") == 1 and (nA.get("thumbs") or [None])[0] == padj and padj != nA.get("p0")
     and nA.get("stage") == "none" and nA.get("label", "").endswith("Add this page") and nA.get("pagesAfterTap") == 0 and not nA.get("errs"),
     "A  capture -> Adjust -> Save tapped WHILE adjusting: exactly ONE paper queued, holding the ADJUSTED page; the stage closed; "
     "her next tap on the old stage button adds nothing; a second Save queues nothing",
     "u1 %s u2 %s adjusted %s stage %s tap %s errs %s" % (nA.get("u1"), nA.get("u2"), (nA.get("thumbs") or [None])[0] == padj, nA.get("stage"), nA.get("pagesAfterTap"), nA.get("errs")))
line(oA.get("u2") == 2 and (oA.get("thumbs") or [None])[0] == oA.get("p0") and oA.get("stage") == "block" and oA.get("pagesAfterTap") == 1,
     "A' CONTROL (the live widget 1143c77b): the same taps give the reported fault -- the UN-adjusted page queued, the stage left "
     "open ('%s'), her next tap makes a new page from it, and Save queues it: TWO papers, two stamps" % (oA.get("label") or ""),
     "u1 %s u2 %s unadjusted %s stage %s tap %s" % (oA.get("u1"), oA.get("u2"), (oA.get("thumbs") or [None])[0] == oA.get("p0"), oA.get("stage"), oA.get("pagesAfterTap")))
line(nB.get("u1") == 1 and (nB.get("thumbs") or [None])[0] == padj and padj and padj != nB.get("p0") and nB.get("stage") == "none"
     and oB.get("u1") == 1 and oB.get("padj") == padj and not nB.get("errs"),
     "B  Adjust -> Theek hai -> Save: one paper, the adjusted page -- the same as the live widget gives (the adjusted page identical)")
line(nC.get("stageLeft") == "block" and nC.get("pagesAfterTap") == 0 and nC.get("stage") == "none" and oC.get("pagesAfterTap") == 1,
     "C  the page under adjustment deleted, the stage left on screen: a tap on its button adds NOTHING (the live widget: a new page "
     "from the leftover canvas) and the leftover stage is closed",
     "new %s / old %s" % (nC.get("pagesAfterTap"), oC.get("pagesAfterTap")))
line(nD.get("uSame") == 1 and nD.get("uDiff") == 2 and nD.get("p0again") == nD.get("p0") and oD.get("uSame") == 2 and oD.get("uDiff") == 3,
     "D  the same pages queued twice within 10 s: queued ONCE (the live widget: twice); a different paper right after: queued",
     "new %s,%s / old %s,%s" % (nD.get("uSame"), nD.get("uDiff"), oD.get("uSame"), oD.get("uDiff")))
# --------------------------------------------------------------- 1b. S559_FIX1: C1 (scene E) and C2 (scene F) -- NEW, PREV, OLD
if PREV:
    RF = {(w, sc): page(w, "scan app intake (smart)", sc) for w in ("new", "prev", "old") for sc in ("E", "F")}
    for k, v in sorted(RF.items()):
        print("  %s %s: %s" % (k[0], k[1], json.dumps({x: v.get(x) for x in ("ready", "adjBefore", "u1", "u2", "stage", "label", "pagesAfterTap",
                                                                          "adjAfterDel", "left", "errs")})), flush=True)

    def e_ok(v):
        return (v.get("ready") and v.get("adjBefore") == -1 and v.get("u1") == 1 and (v.get("thumbs") or [None])[0] == v.get("p0")
                and v.get("stage") == "none" and v.get("pagesAfterTap") == 0 and v.get("u2") == 1 and not v.get("errs"))

    def f_ok(v):
        pdf = v.get("pdf") or []
        return (v.get("ready") and v.get("adjAfterDel") == 0 and v.get("left") == 2 and v.get("u1") == 1 and len(pdf) == 2
                and pdf[1] == v.get("p3") and pdf[0] not in (v.get("p1"), v.get("p2"), v.get("p3")) and pdf[0] != pdf[1]
                and v.get("stage") == "none" and not v.get("errs"))

    def pdf_words(v):
        nm = {v.get("p1"): "page1", v.get("p2"): "page2", v.get("p3"): "page3"}
        return "[" + ", ".join(nm.get(h, "page2-adjusted" if h else "?") for h in (v.get("pdf") or [])) + "]"
    nE, pE, oE, nF, pF, oF = RF[("new", "E")], RF[("prev", "E")], RF[("old", "E")], RF[("new", "F")], RF[("prev", "F")], RF[("old", "F")]
    line(e_ok(nE), "E  (C1) Save tapped while the Adjust image is still loading (700 ms late): ONE paper queued (the page as it was); "
         "the late image does NOT reopen the stage; her next tap adds nothing; a second Save queues nothing",
         "u1 %s stage %s tap %s u2 %s errs %s" % (nE.get("u1"), nE.get("stage"), nE.get("pagesAfterTap"), nE.get("u2"), nE.get("errs")))
    line(not e_ok(pE) and pE.get("stage") == "block" and pE.get("u2") == 2,
         "E' CONTROL (the first S559 build 552effcd): the late image reopens the stage ('%s'), her tap makes a page from it, Save "
         "queues it -- TWO papers, two stamps" % (pE.get("label") or ""),
         "u1 %s stage %s tap %s u2 %s" % (pE.get("u1"), pE.get("stage"), pE.get("pagesAfterTap"), pE.get("u2")))
    line(f_ok(nF), "F  (C2) 3 pages, adjusting page 2, page 1 deleted, Save: ONE paper with two different pages, once each "
         "(page 2 adjusted, page 3)", "adjustIdx after delete %s . saved %s" % (nF.get("adjAfterDel"), pdf_words(nF)))
    line(not f_ok(pF) and len(pF.get("pdf") or []) == 2 and (pF.get("pdf") or [None])[0] == pF.get("p2") and pF.get("p3") not in (pF.get("pdf") or []),
         "F' CONTROL (the first S559 build 552effcd): the same taps save page 2 TWICE (as it was and adjusted) and lose page 3",
         "adjustIdx after delete %s . saved %s" % (pF.get("adjAfterDel"), pdf_words(pF)))
    print("  (the live widget 1143c77b, for the record: E %s, u2 %s . F saved %s, stage %s)" % (
        "green" if e_ok(oE) else "red", oE.get("u2"), pdf_words(oF), oF.get("stage")), flush=True)
# --------------------------------------------------------------- 2. the seven surfaces, OLD and NEW
for name, cfg in SURF:
    do, dn = page("old", name, "dom"), page("new", name, "dom")
    same = do.get("dom") == dn.get("dom") and do.get("dom")
    if cfg.get("cvScan"):
        line(same and dn.get("ready") and not dn.get("errs") and dn.get("s559") == "S559.1" and do.get("s559") is None,
             "S  %-24s loads: the same screen (DOM identical), OpenCV ready, no error; the S559 mark present (intake only)" % name)
        continue
    so, sn = page("old", name, "save"), page("new", name, "save")
    line(same and not dn.get("errs") and not do.get("errs") and dn.get("on") is False and dn.get("s559") is None
         and so.get("upsSummary") and so.get("upsSummary") == sn.get("upsSummary") and sn.get("hash") == so.get("hash") == "#saved"
         and so.get("pageh") == sn.get("pageh"),
         "S  %-24s loads and saves exactly as before: DOM identical, no error, smart path off, no S559 mark; the same page, the "
         "same upload (fields, file name, type, size, bytes), the same way back" % name,
         "dom %s ups %s" % (bool(same), so.get("upsSummary") == sn.get("upsSummary")))
# --------------------------------------------------------------- 3. the bar: one line at 1366 px, wraps at a phone's width
if FIT:
    for pg in sorted(f[:-5] for f in os.listdir(FIT) if f.endswith(".html")):
        wide = run("http://127.0.0.1:%d/fit?p=%s" % (PORT, pg), "1366,900")
        narrow = run("http://127.0.0.1:%d/fit?p=%s" % (PORT, pg), "390,844")
        line(wide.get("navLines") == 1 and wide.get("barLines") == 1 and wide.get("items") == 11 and narrow.get("navLines", 0) > 1
             and not narrow.get("overflow"),
             "W  the bar on the %-8s page: one line at 1366 px (11 items, a long name and 3-digit counts); at 390 px it wraps, no sideways scroll" % pg,
             "1366: nav %s lines, bar %s, %s items, %s px wide . 390: nav %s lines, overflow %s" % (
                 wide.get("navLines"), wide.get("barLines"), wide.get("items"), wide.get("barWidth"), narrow.get("navLines"), narrow.get("overflow")))
print("%d browser checks: %d GREEN, %d RED%s  (%.0f s)" % (len(OUT), len(OUT) - len(REDS), len(REDS), (" (" + "; ".join(r[:3] for r in REDS) + ")") if REDS else "", time.time() - t0))
srv.shutdown()
sys.exit(1 if REDS else 0)
