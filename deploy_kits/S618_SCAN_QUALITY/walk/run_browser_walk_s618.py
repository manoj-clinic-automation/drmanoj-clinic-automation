#!/usr/bin/env python3
"""run_browser_walk_s618.py -- S618's phone walk (brief 4.3): headless Chrome on the PC (the box has no browser). A small server on
127.0.0.1 serves the widget (OLD = the live 10a8bb29, NEW = the kit's build), OpenCV.js (the box's copy, ff1e10e7), jsPDF (the box's copy,
4b16d1b6) and harness_s618.js, answers every upload with a made-up stamp (it keeps the form fields, never the file), and takes the page's
report on /result. The stored bill pages (pdfimages of the stored scans) stay in the PC's _scratch folder; nothing leaves the PC.

    python -B run_browser_walk_s618.py <chrome.exe> <old widget> <new widget> <opencv.js> <jspdf.js> <pages dir> <work dir> <blur_min>
                                       [--intake-old <html> --intake-new <html>]    (the intake pages the box walk rendered, OLD / NEW)

Scenes: V (the new widget compiles in V8), CAL (the sharpness of every stored page at the widget's 600-px scale, direct and through the
widget's own outline-straighten-upright path), A/A' (B-0181 on a desk margin refused with the words; the live widget keeps it), B (B-0198
kept), C (two refusals then kept, the upload carries blur_kept=1), D (a gallery import of three photos, one refused, does not stall),
E/E' (the half-A4 prior on a pharmacy link from the start; read at call time), F/F' (the intake page: rescan_of on the first Save only).
Prints the results; exit 1 on any RED."""
import email.parser
import http.server
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.parse

A = sys.argv[1:]
INTAKE = {}
for k in ("--intake-old", "--intake-new"):
    if k in A:
        INTAKE[k[9:]] = A[A.index(k) + 1]
        del A[A.index(k):A.index(k) + 2]
CHROME, OLD, NEW, OCV, JSPDF, PAGES, WORK, BLUR = A[0:8]
BLUR = float(BLUR)
HERE = os.path.dirname(os.path.abspath(__file__))
RES, UPS, EV = {}, [], threading.Event()
NAMES = sorted(f for f in os.listdir(PAGES) if f.lower().endswith(".jpg"))


def cfg(blur=True, aspect=True):
    c = {"title": "Scan the bill", "uploadUrl": "/upload", "fileField": "bill_scan", "uploadFields": {"lane": "pharmacy", "bill_month": "2026-10"},
         "nameBase": "bill", "backUrl": "#", "allowIdCard": False, "allowBatch": False, "autoPage": True, "inlineStamp": True, "retryUpload": True,
         "directFile": True, "slipJsonUrl": "/slip/{id}", "cvScan": True, "cvUrl": "/opencv.js"}
    if blur:
        c["blurMin"] = BLUR
    if aspect:
        c["expectAspect"], c["expectLabel"] = 0.7048, "half-A4 bill"
    return c


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
            c = cfg(blur=q.get("blur", "1") == "1", aspect=q.get("aspect", "1") == "1")
            body = ("<!doctype html><html><head><meta charset=utf-8></head><body><div id=scanroot></div>"
                    "<script>window.SCANNER_CONFIG = %s;</script><script src=\"/jspdf.js\"></script>"
                    "<script src=\"/widget_%s.js\"></script><script src=\"/harness_s618.js\"></script></body></html>") % (json.dumps(c), q["w"])
            return self.send(body.encode("utf-8"), "text/html; charset=utf-8")
        if u.path == "/intake":
            raw = open(INTAKE[q["w"]], "rb").read().decode("utf-8")
            raw = re.sub(r'<script src="https://cdnjs\.cloudflare\.com/ajax/libs/jspdf/[^"]+"></script>', '<script src="/jspdf.js"></script>', raw)
            raw = re.sub(r'src="[^"]*widget\.js[^"]*"', 'src="/widget_%s.js"' % q["w"], raw)
            raw = re.sub(r'"cvUrl": "[^"]*"', '"cvUrl": "/opencv.js"', raw)
            raw = re.sub(r'"uploadUrl": "[^"]*"', '"uploadUrl": "/upload"', raw)
            raw = raw.replace("</body>", '<script src="/harness_s618.js"></script></body>', 1)
            return self.send(raw.encode("utf-8"), "text/html; charset=utf-8")
        if u.path == "/syntax":
            body = ("<!doctype html><html><head><meta charset=utf-8></head><body><script>"
                    "fetch('/widget_new.js').then(function(r){return r.text();}).then(function(t){var o={len:t.length};"
                    "try{new Function(t);o.ok=true;}catch(e){o.ok=false;o.err=String(e);}"
                    "return fetch('/result',{method:'POST',body:JSON.stringify(o)});});</script></body></html>")
            return self.send(body.encode("utf-8"), "text/html; charset=utf-8")
        if u.path == "/pages.json":
            return self.send(json.dumps(NAMES).encode(), "application/json")
        if u.path.startswith("/page/"):
            n = os.path.basename(urllib.parse.unquote(u.path[6:]))
            return self.send(open(os.path.join(PAGES, n), "rb").read(), "image/jpeg")
        if u.path == "/uploads":
            return self.send(json.dumps(UPS).encode(), "application/json")
        if u.path.startswith("/slip/"):
            return self.send(b'{"ocr_status":"read"}', "application/json")
        files = {"/harness_s618.js": os.path.join(HERE, "harness_s618.js"), "/widget_old.js": OLD, "/widget_new.js": NEW, "/opencv.js": OCV, "/jspdf.js": JSPDF}
        if u.path in files:
            return self.send(open(files[u.path], "rb").read(), "application/javascript")
        return self.send(b"{}", "application/json", 404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        data = self.rfile.read(n)
        if self.path.startswith("/result"):
            RES["last"] = json.loads(data.decode("utf-8"))
            EV.set()
            return self.send(b"{}", "application/json")
        if self.path.startswith("/upload"):
            msg = email.parser.BytesParser().parsebytes(b"Content-Type: " + self.headers["Content-Type"].encode() + b"\r\n\r\n" + data)
            f = {p.get_param("name", header="content-disposition"): p.get_payload(decode=True).decode("utf-8", "replace") for p in msg.get_payload()
                 if p.get_param("name", header="content-disposition") != "bill_scan"}
            f.pop("client_token", None)
            UPS.append(f)
            return self.send(json.dumps({"ok": True, "id": 9000 + len(UPS), "stamp": "B-9%03d" % len(UPS)}).encode(), "application/json")
        return self.send(b"{}", "application/json")


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


PORT = free_port()
srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
PROFILE = os.path.abspath(os.path.join(WORK, "chrome_profile_%d" % int(time.time())))
os.makedirs(PROFILE, exist_ok=True)


def run(path, wait=300):
    RES.pop("last", None)
    EV.clear()
    del UPS[:]
    p = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                          "--mute-audio", "--user-data-dir=" + PROFILE, "--window-size=420,900", "http://127.0.0.1:%d%s" % (PORT, path)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    EV.wait(wait)
    p.terminate()
    try:
        p.wait(15)
    except Exception:                                                     # noqa: BLE001
        p.kill()
    return RES.get("last") or {"errs": ["no report from the page within %d s" % wait]}


OUT, REDS = [], []


def line(ok, name, detail=""):
    OUT.append(("GREEN " if ok else "RED   ") + name + (("  -- " + detail) if detail else ""))
    print(OUT[-1], flush=True)
    if not ok:
        REDS.append(name)


t0 = time.time()
SY = run("/syntax", 60)
line(SY.get("ok") is True, "V  the new widget compiles in V8 (Chrome's JavaScript engine, the one node uses): parsed whole, not run -- node --check's equivalent",
     "%s %s" % (SY.get("len"), SY.get("err") or SY.get("errs") or ""))
# ---------------------------------------------------------------- CAL: the calibration table
CAL = run("/page?w=new&sc=cal", 900)
cal = CAL.get("cal") or {}
print("  the sharpness of every stored page (3x3 Laplacian variance at 600 px): direct = the stored page; through = laid on a desk and "
      "taken through the widget's own outline, straighten (B&W) and upright", flush=True)
for n in NAMES:
    v = cal.get(n) or {}
    print("    %-10s %5sx%-5s direct %7s   through %7s   outline %s" % (n[:-4], v.get("w"), v.get("h"), "%.0f" % v["direct"] if v.get("direct") is not None else "-",
                                                                         "%.0f" % v["pipe"] if v.get("pipe") is not None else "-", v.get("found")), flush=True)
json.dump(cal, open(os.path.join(WORK, "calibration_s618.json"), "w"), indent=1)
line(bool(cal) and len(cal) == len(NAMES) and not CAL.get("errs"), "CAL  the sharpness of all %d stored pages measured by the widget's own function" % len(NAMES),
     str(CAL.get("errs") or ""))
# ---------------------------------------------------------------- A, A', B, C, D
rA, rAo = run("/page?w=new&sc=refuse&p=B-0181.jpg"), run("/page?w=old&sc=refuse&p=B-0181.jpg")
line(rA.get("pages") == 0 and "Photo saaf nahi" in (rA.get("box") or "") and "phir se lijiye" in (rA.get("box") or "") and "Retake" in (rA.get("box") or "") and not rA.get("errs"),
     "A  B-0181's stored page on a desk margin: REFUSED -- not added, the phone says 'Photo saaf nahi — phir se lijiye' with Retake",
     "pages %s box '%s' errs %s" % (rA.get("pages"), rA.get("box"), rA.get("errs")))
line(rAo.get("pages") == 1 and not rAo.get("box"), "A' CONTROL (the live widget 10a8bb29): the same photo is KEPT as page 1 -- no refusal (red on the old file)",
     "pages %s box '%s'" % (rAo.get("pages"), rAo.get("box")))
rB = run("/page?w=new&sc=keep&p=B-0198.jpg")
line(rB.get("pages") == 1 and not rB.get("box") and not rB.get("errs"), "B  B-0198's stored page (the lowest readable) on a desk margin: KEPT as page 1",
     "pages %s box '%s'" % (rB.get("pages"), rB.get("box")))
rC = run("/page?w=new&sc=three&p=B-0181.jpg", 400)
seq = rC.get("seq") or []
ups = rC.get("ups") or []
line(len(seq) == 3 and seq[0]["pages"] == 0 and seq[0]["box"] and seq[1]["pages"] == 0 and seq[1]["box"] and seq[2]["pages"] == 1 and not seq[2]["box"]
     and len(ups) == 1 and ups[0].get("blur_kept") == "1" and ups[0].get("lane") == "pharmacy",
     "C  two refusals of the same page, then the third photo KEPT (never a dead end); Save: the upload carries blur_kept=1",
     "pages after each %s; upload fields %s" % ([s.get("pages") for s in seq], ups))
rCo = run("/page?w=old&sc=three&p=B-0181.jpg", 400)
print("  (the live widget, for the record: pages after each %s; upload blur_kept %s)" % ([s.get("pages") for s in (rCo.get("seq") or [])],
                                                                                    [u.get("blur_kept") for u in (rCo.get("ups") or [])]), flush=True)
rD = run("/page?w=new&sc=gallery&ps=B-0198.jpg,B-0181.jpg,B-0201.jpg", 400)
line(rD.get("pages") == 2 and rD.get("sawBoxAt") is not None and not rD.get("errs"),
     "D  a gallery import of three photos, the middle one blurred: it is refused and the import goes on -- 2 pages, no stall",
     "pages %s, the refusal seen at page count %s" % (rD.get("pages"), rD.get("sawBoxAt")))
# ---------------------------------------------------------------- E: the half-A4 prior
rE = run("/page?w=new&sc=aspect&aspect=1")
rEo = run("/page?w=old&sc=aspect&aspect=0")
line(rE.get("guidehint") is True and rE.get("cfgAR") == 0.7048 and rE.get("arSquare") is False and rE.get("arHalfA4") is True and rE.get("arSquareAfterClinic") is True,
     "E  a pharmacy link (the server puts expectAspect in SCANNER_CONFIG): the half-A4 prior in effect from the start (the guide line shown, a square "
     "outline refused by arOK) and read at call time (a lane change to clinic lifts it)",
     json.dumps({k: rE.get(k) for k in ("guidehint", "cfgAR", "arSquare", "arHalfA4", "arSquareAfterClinic")}))
line(rEo.get("guidehint") is False and rEo.get("cfgAR") is None, "E' CONTROL (the live intake's SCANNER_CONFIG, set by the lane select after the widget read it): no prior at load "
     "-- no guide line (red on the old files)", json.dumps({k: rEo.get(k) for k in ("guidehint", "cfgAR")}))
# ---------------------------------------------------------------- F: the intake page's rescan_of on the first Save only
if INTAKE:
    rF = run("/intake?w=new&sc=intake&p=B-0198.jpg&p2=B-0201.jpg", 400)
    rFo = run("/intake?w=old&sc=intake&p=B-0198.jpg&p2=B-0201.jpg", 400)
    u1 = rF.get("ups") or []
    uo = rFo.get("ups") or []
    line(len(u1) == 2 and u1[0].get("rescan_of") == "199" and "rescan_of" not in u1[1] and not rF.get("errs"),
         "F  the intake page opened from 'Scan karo' (rescan_of=199): the first Save carries rescan_of, the next bill does NOT",
         "uploads %s errs %s" % ([sorted(x) for x in u1], rF.get("errs")))
    line(len(uo) == 2 and all("rescan_of" not in x for x in uo), "F' CONTROL (the live intake page): rescan_of is not even carried (INTAKE_PREFILL has no rescan_of) -- red on the old files",
         "uploads %s" % [sorted(x) for x in uo])
print("%d browser checks: %d GREEN, %d RED%s  (%.0f s)" % (len(OUT), len(OUT) - len(REDS), len(REDS), (" (" + "; ".join(r[:3] for r in REDS) + ")") if REDS else "", time.time() - t0))
srv.shutdown()
sys.exit(1 if REDS else 0)
