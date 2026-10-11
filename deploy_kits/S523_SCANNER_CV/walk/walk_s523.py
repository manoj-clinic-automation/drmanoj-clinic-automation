#!/usr/bin/env python3
"""WALK for S523_SCANNER_CV (BUILD_NORM_v1 s3): the widget on made-up bill photos in headless Chromium, the app's
three doors on a throw-away database. Usage:

    python3 walk_s523.py <widget.js> <asset_register.py> <opencv.js> <images_dir> <report_dir> [--expect-red]

Every check prints GREEN/RED; the exit code is 1 on any RED. With --expect-red the run is the NEGATIVE CONTROL: it
must end with at least one RED on the file under test (the live bytes), and then exits 0."""
import asyncio, base64, glob, io, json, os, shutil, sqlite3, subprocess, sys, tempfile, time
from PIL import Image

W_JS, A_PY, CV_JS, IMG, REP = [os.path.abspath(a) for a in sys.argv[1:6]]
EXPECT_RED = "--expect-red" in sys.argv
os.makedirs(REP, exist_ok=True)
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(detail)) if detail else ""))


HOST = """<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<style>.card{border:1px solid #ccc;padding:8px;margin:8px}.muted{color:#666}.btn{padding:6px}</style></head><body>
<div id=scanroot></div>
<script>window.SCANNER_CONFIG = %s;</script>
<script src="%s"></script>
<script>
window.__loadCanvas = function(url){ return new Promise(function(res, rej){ var im = new Image(); im.onload = function(){
  var c = document.createElement('canvas'); c.width = im.width; c.height = im.height; c.getContext('2d').drawImage(im, 0, 0);
  window.__lastCanvas = c; res([c.width, c.height]); }; im.onerror = rej; im.src = url; }); };
window.__dims = function(du){ return new Promise(function(res){ var im = new Image(); im.onload = function(){ res([im.width, im.height]); }; im.src = du; }); };
</script></body></html>"""


def host(path, cfg, widget):
    open(path, "w").write(HOST % (json.dumps(cfg), widget))


def quad_err(q, t):
    import math
    return max(math.hypot(q[i][0] - t[i][0], q[i][1] - t[i][1]) for i in range(4))


async def browser_walk():
    from playwright.async_api import async_playwright
    wd = tempfile.mkdtemp(prefix="s523walk_")
    shutil.copy(W_JS, os.path.join(wd, "widget.js")); shutil.copy(CV_JS, os.path.join(wd, "opencv.js"))
    truth = json.load(open(os.path.join(IMG, "truth.json")))
    base = dict(title="Scan the bill", uploadUrl="/nowhere", fileField="bill_scan", uploadFields={"lane": "clinic"}, nameBase="bill",
                backUrl="/", allowIdCard=False, allowBatch=False, autoPage=True, inlineStamp=True, retryUpload=True, directFile=True)
    cfg_cv = dict(base, cvScan=True, cvUrl="opencv.js")
    cfg_nocv = dict(base)
    cfg_stage = dict(title="Scan", uploadUrl="/nowhere", fileField="file", uploadFields={}, nameBase="x", backUrl="/", allowIdCard=False, allowBatch=False)
    host(os.path.join(wd, "cv.html"), cfg_cv, "widget.js"); host(os.path.join(wd, "nocv.html"), cfg_nocv, "widget.js"); host(os.path.join(wd, "stage.html"), cfg_stage, "widget.js")
    import http.server, socketserver, threading
    shutil.copytree(IMG, os.path.join(wd, "images"))
    class Q(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k): super().__init__(*a, directory=wd, **k)
        def log_message(self, *a): pass
    srv = socketserver.TCPServer(("127.0.0.1", 0), Q); port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    U = "http://127.0.0.1:%d/" % port
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                                          "--use-file-for-fake-video-capture=" + os.path.join(IMG, "cam.y4m")])
        pg = await b.new_page(viewport={"width": 390, "height": 800})
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(U + "cv.html")
        # A1 the switch is seen and the library arrives
        on = await pg.evaluate("!!(window.__scannerS523 && window.__scannerS523.on)")
        check("A1 cvScan switch seen by the widget", on)
        ready = False
        for _ in range(120):
            ready = await pg.evaluate("!!(window.__scannerS523 && window.__scannerS523.ready())")
            if ready: break
            await pg.wait_for_timeout(250)
        check("A2 OpenCV.js loaded and ready", ready, "why=" + str(await pg.evaluate("window.__scannerS523 ? window.__scannerS523.why() : 'absent'")))
        if not ready:
            await b.close(); return
        # A3..A8 the made-up photos: corners found within 2.5% of the long side
        found = 0
        for name, t in truth.items():
            dims = await pg.evaluate("window.__loadCanvas(%s)" % json.dumps(U + "images/" + name + ".jpg"))
            q = await pg.evaluate("window.__scannerCV.find(window.__lastCanvas)")
            tol = 0.025 * max(t["w"], t["h"])
            ok = bool(q) and quad_err(q, t["quad"]) <= tol
            if ok: found += 1
            check("A3 outline on %s" % name, ok, ("max corner error %.0f px (tol %.0f)" % (quad_err(q, t["quad"]), tol)) if q else "not found")
        check("A4 outline found on all made-up photos", found == len(truth), "%d of %d" % (found, len(truth)))
        # B the chosen-photo path: full resolution kept, paper aspect kept
        await pg.set_input_files("#cam", [os.path.join(IMG, "tilted12_wood.jpg"), os.path.join(IMG, "perspective_grey.jpg")])
        for _ in range(80):
            n = await pg.evaluate("window.__scannerCV.pages().length")
            if n >= 2: break
            await pg.wait_for_timeout(250)
        check("B1 two chosen photos became two pages", n == 2, n)
        pages = await pg.evaluate("window.__scannerCV.pages()")
        okd = True
        for i, du in enumerate(pages):
            w, h = await pg.evaluate("window.__dims(%s)" % json.dumps(du))
            ar = w / h
            good = 1500 <= max(w, h) <= 2400 and 0.64 <= ar <= 0.78
            okd = okd and good
            check("B2 page %d is %dx%d (the paper's own size, 1500-2400 long side; half-A4 shape; was 536x759 under the 1400 cap)" % (i + 1, w, h), good)
            open(os.path.join(REP, "page%d.jpg" % (i + 1)), "wb").write(base64.b64decode(du.split(",")[1]))
        thumbs = await pg.evaluate("document.querySelectorAll('#pages button').length")
        check("B3 each page carries Retake and Adjust (4 buttons for 2 pages + 2 delete)", thumbs == 6, thumbs)
        adj = await pg.evaluate("Array.from(document.querySelectorAll('#pages button')).map(function(b){return b.textContent}).join('|')")
        check("B4 the Adjust button is on the page", "Adjust" in adj, adj)
        # C Adjust: open, the stage shows the handles; 'Theek hai' re-cuts; 'Add whole image' takes the whole photo
        await pg.evaluate("window.__scannerCV.adjustOpen(0)")
        await pg.wait_for_timeout(600)
        st = await pg.evaluate("document.getElementById('stage').style.display + '|' + document.getElementById('addpage').textContent")
        check("C1 Adjust opens the stage with 'Theek hai'", st.startswith("block|") and "Theek hai" in st, st)
        await pg.click("#addpage"); await pg.wait_for_timeout(800)
        p0 = await pg.evaluate("window.__scannerCV.pages()[0]")
        w, h = await pg.evaluate("window.__dims(%s)" % json.dumps(p0))
        check("C2 'Theek hai' re-cuts the page at full size", 1500 <= max(w, h) <= 2400 and 0.64 <= w / h <= 0.78, "%dx%d" % (w, h))
        closed = await pg.evaluate("document.getElementById('stage').style.display + '|' + window.__scannerCV.state().adjust")
        check("C3 the stage closes and the adjust ends", closed == "none|-1", closed)
        await pg.evaluate("window.__scannerCV.adjustOpen(1)"); await pg.wait_for_timeout(600)
        await pg.click("#addwhole"); await pg.wait_for_timeout(800)
        p1 = await pg.evaluate("window.__scannerCV.pages()[1]")
        w, h = await pg.evaluate("window.__dims(%s)" % json.dumps(p1))
        check("C4 'Add whole image' in Adjust keeps the whole photo (4:3)", abs(w / h - 4 / 3) < 0.02 and max(w, h) <= 2400, "%dx%d" % (w, h))
        # D delete a page drops its original
        await pg.evaluate("document.querySelector('#pages button[title=\"Delete this page\"]').click()"); await pg.wait_for_timeout(300)
        n1, n2 = await pg.evaluate("[window.__scannerCV.pages().length, window.__scannerCV.corners().length]")
        check("D1 deleting a page drops its kept original too", n1 == 1 and n2 == 1, "%d pages, %d originals" % (n1, n2))
        # E the live camera: the outline overlay appears, a capture is a full-size page
        await pg.click("#opencam"); await pg.wait_for_timeout(1500)
        ov = await pg.evaluate("(function(){var c=document.getElementById('livov'); return c ? (c.style.display||'block') : 'absent'})()")
        check("E1 the live outline canvas is on the camera", ov == "block", ov)
        vw = await pg.evaluate("document.getElementById('vid').videoWidth")
        await pg.click("#shootbtn"); await pg.wait_for_timeout(1500)
        n = await pg.evaluate("window.__scannerCV.pages().length")
        check("E2 Capture adds a page through the smart path", n == 2, "pages=%d video=%s" % (n, vw))
        cam_on = await pg.evaluate("document.getElementById('camwrap').style.display")
        check("E3 the camera stays open after Capture (S441 kept)", cam_on == "block", cam_on)
        await pg.click("#cancelcam"); await pg.wait_for_timeout(300)
        ov2 = await pg.evaluate("document.getElementById('livov').style.display")
        check("E4 Cancel stops the live outline", ov2 == "none", ov2)
        # F Save hands on and clears the originals (the upload goes nowhere here)
        await pg.evaluate("document.getElementById('savebtn').click()"); await pg.wait_for_timeout(500)
        n1, n2 = await pg.evaluate("[window.__scannerCV.pages().length, window.__scannerCV.corners().length]")
        check("F1 Save empties the pages and the kept originals", n1 == 0 and n2 == 0, "%d, %d" % (n1, n2))
        check("F2 no page error in the smart path", not errs, errs[:2])
        # G the other six surfaces: without cvScan nothing changes
        errs2 = []; pg2 = await b.new_page(viewport={"width": 390, "height": 800}); pg2.on("pageerror", lambda e: errs2.append(str(e)))
        await pg2.goto(U + "nocv.html"); await pg2.wait_for_timeout(500)
        g1 = await pg2.evaluate("[!!(window.__scannerS523 && window.__scannerS523.on), !!document.querySelector('script[src*=\"opencv\"]')]")
        check("G1 without cvScan: switch off, no library requested", g1 == [False, False], g1)
        await pg2.set_input_files("#cam", [os.path.join(IMG, "tilted12_wood.jpg")]); await pg2.wait_for_timeout(2500)
        du = await pg2.evaluate("(document.querySelector('#pages img')||{}).src || ''")
        w, h = await pg2.evaluate("window.__dims(%s)" % json.dumps(du)) if du else (0, 0)
        check("G2 without cvScan a page is the S441 page (1400 px cap, as today)", max(w, h) == 1400, "%dx%d" % (w, h))
        g3 = await pg2.evaluate("Array.from(document.querySelectorAll('#pages button')).map(function(b){return b.textContent}).join('|')")
        check("G3 without cvScan no Adjust button", "Adjust" not in g3 and "Retake" in g3, g3)
        check("G4 no page error without cvScan", not errs2, errs2[:2])
        pg3 = await b.new_page(viewport={"width": 390, "height": 800}); errs3 = []; pg3.on("pageerror", lambda e: errs3.append(str(e)))
        await pg3.goto(U + "stage.html"); await pg3.wait_for_timeout(300)
        await pg3.set_input_files("#cam", [os.path.join(IMG, "straight_wood.jpg")]); await pg3.wait_for_timeout(2500)
        g5 = await pg3.evaluate("document.getElementById('stage').style.display + '|' + document.getElementById('addpage').textContent")
        check("G5 a finance-shaped caller (no autoPage): the review stage as before", g5.startswith("block|") and "Add this page" in g5, g5)
        await pg3.click("#addpage"); await pg3.wait_for_timeout(500)
        g6 = await pg3.evaluate("document.querySelectorAll('#pages img').length")
        check("G6 'Add this page' adds the page as before", g6 == 1, g6)
        check("G7 no page error on the finance-shaped caller", not errs3, errs3[:2])
        # H the real whole-photo scans of the backup (reads only; made from bills, no patient paper)
        real = sorted(glob.glob(os.path.join(IMG, "real", "*.jpg")))
        if real:
            hit = 0; sheet = []; hug = 0
            for f in real:
                dims = await pg.evaluate("window.__loadCanvas(%s)" % json.dumps(U + "images/real/" + os.path.basename(f)))
                q = await pg.evaluate("window.__scannerCV.find(window.__lastCanvas)")
                if q:
                    hit += 1
                    w0, h0 = dims; m = 0.015 * min(w0, h0)
                    if sum(1 for p_ in q if p_[0] < m or p_[1] < m or p_[0] > w0 - m or p_[1] > h0 - m) >= 3: hug += 1
                    du = await pg.evaluate("window.__scannerCV.warp(window.__lastCanvas, %s, true).toDataURL('image/jpeg', 0.8)" % json.dumps(q))
                    sheet.append(Image.open(io.BytesIO(base64.b64decode(du.split(",")[1]))))
            check("H1 the old whole-photo scans (already flattened B&W, 1050 px -- the worst case): never a frame-hugging box; the rest refused, not guessed",
                  hug == 0, "%d of %d outlined, %d frame-hugging" % (hit, len(real), hug))
            if sheet:
                for im in sheet: im.thumbnail((180, 240))
                cols = 8; rows = (len(sheet) + cols - 1) // cols
                S = Image.new("RGB", (cols * 190, rows * 250), "white")
                for i, im in enumerate(sheet): S.paste(im, (10 + (i % cols) * 190, 5 + (i // cols) * 250))
                S.save(os.path.join(REP, "real_outlined_sheet.jpg"), quality=80)
        await b.close()
    srv.shutdown()


def app_walk():
    """The app's doors on a throw-away database: the library route, the intake's config, the admin switch."""
    import importlib.util
    wd = tempfile.mkdtemp(prefix="s523app_")
    static = os.path.join(wd, "static"); os.makedirs(static)
    shutil.copy(CV_JS, os.path.join(static, "opencv.js"))
    subprocess.run(["gzip", "-k", "-9", os.path.join(static, "opencv.js")], check=True)
    shutil.copy(A_PY, os.path.join(wd, "asset_register.py")); shutil.copy(W_JS, os.path.join(wd, "scanner_widget.js"))
    os.environ["ASSETS_DB"] = os.path.join(wd, "assets.db"); os.environ["ASSETS_UPLOADS"] = os.path.join(wd, "uploads")
    os.environ["SCANNER_OPENCV_JS"] = os.path.join(static, "opencv.js")
    sys.path.insert(0, wd)
    spec = importlib.util.spec_from_file_location("asset_register", os.path.join(wd, "asset_register.py"))
    try:
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    except Exception as e:                                                        # noqa: BLE001
        check("P0 the app imports", False, repr(e)[:200]); return
    check("P0 the app imports", True)
    c = m.app.test_client()
    r = c.get("/scan/opencv.js", headers={"Accept-Encoding": "gzip"})
    check("P1 /scan/opencv.js serves the gzip copy with a one-year cache", r.status_code == 200 and r.headers.get("Content-Encoding") == "gzip"
          and "immutable" in r.headers.get("Cache-Control", ""), "%s %s %s" % (r.status_code, r.headers.get("Content-Encoding"), r.headers.get("Cache-Control")))
    r2 = c.get("/scan/opencv.js")
    check("P2 /scan/opencv.js serves the plain copy without gzip", r2.status_code == 200 and r2.headers.get("Content-Encoding") is None and len(r2.data) > 9000000, "%s %d" % (r2.status_code, len(r2.data)))
    r3 = c.post("/login", data={"username": "manoj", "password": "change-me-manoj"}, follow_redirects=False)
    check("P3 the seeded owner can log in on the throw-away database", r3.status_code in (302, 303), r3.status_code)
    r4 = c.get("/intake")
    check("P4 intake OFF by default: no cvScan in the scanner config", r4.status_code == 200 and '"cvScan"' not in r4.get_data(as_text=True), r4.status_code)
    r5 = c.get("/admin"); t5 = r5.get_data(as_text=True)
    check("P5 /admin shows the switch card, OFF", "smart outline" in t5 and "<b>OFF</b>" in t5 and "set_scan_cv" in t5, r5.status_code)
    r6 = c.post("/admin", data={"action": "set_scan_cv", "on": "1"}, follow_redirects=True); t6 = r6.get_data(as_text=True)
    check("P6 the owner's tap switches it ON", "<b>ON</b>" in t6 and "is now ON" in t6, r6.status_code)
    r7 = c.get("/intake"); t7 = r7.get_data(as_text=True)
    check("P7 intake ON: cvScan true and the library's versioned URL in the config", '"cvScan": true' in t7 and "/scan/opencv.js?v=" in t7, r7.status_code)
    r8 = c.post("/admin", data={"action": "set_scan_cv", "on": "0"}, follow_redirects=True)
    r9 = c.get("/intake")
    check("P8 switched OFF again: the intake is as today", "<b>OFF</b>" in r8.get_data(as_text=True) and '"cvScan"' not in r9.get_data(as_text=True))
    # the switch on, the library missing: stays off by itself
    c.post("/admin", data={"action": "set_scan_cv", "on": "1"})
    os.rename(os.path.join(static, "opencv.js"), os.path.join(static, "opencv.js.away"))
    r10 = c.get("/intake"); r11 = c.get("/admin")
    check("P9 ON but no library file on disk: the intake stays as today and /admin says so", '"cvScan"' not in r10.get_data(as_text=True) and "library file not on the server" in r11.get_data(as_text=True))
    os.rename(os.path.join(static, "opencv.js.away"), os.path.join(static, "opencv.js"))
    r12 = c.get("/healthz")
    check("P10 /healthz answers", r12.status_code == 200, r12.status_code)
    r13 = c.get("/scan/widget.js")
    check("P11 the widget route serves the built widget", r13.status_code == 200 and b"S523" in r13.data)


def main():
    t0 = time.time()
    asyncio.run(browser_walk())
    app_walk()
    red = [r for r in RESULTS if not r[1]]
    json.dump([dict(name=n, ok=o, detail=str(d)) for n, o, d in RESULTS], open(os.path.join(REP, "walk_results.json"), "w"), indent=1)
    print("\n%d checks: %d green, %d red (%.0fs)" % (len(RESULTS), len(RESULTS) - len(red), len(red), time.time() - t0))
    if EXPECT_RED:
        if red:
            print("NEGATIVE CONTROL: red as it must be -- %s" % ", ".join(r[0] for r in red[:4])); sys.exit(0)
        print("NEGATIVE CONTROL FAILED: the walk could not tell old from new"); sys.exit(1)
    sys.exit(1 if red else 0)


if __name__ == "__main__":
    main()
