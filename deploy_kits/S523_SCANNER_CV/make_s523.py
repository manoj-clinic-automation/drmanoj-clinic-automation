#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s523.py -- S523_SCANNER_CV: exact, counted edits on md5-pinned live bytes (BUILD_NORM_v1 s3).

    python3 make_s523.py <live_dir> <out_dir>

Reads  <live_dir>/scanner_widget.js  (must be e2bca60222f043c225dfa57bce565522)
       <live_dir>/asset_register.py  (must be e774be89193472dfa4b142d85bdcc46c)
       s523_block.js beside this script
Writes <out_dir>/scanner_widget.js, <out_dir>/asset_register.py and prints each file's md5.
Every anchor must occur EXACTLY once in the live file, or the build refuses (nothing is written).
"""
import hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = {"scanner_widget.js": "e2bca60222f043c225dfa57bce565522",
        "asset_register.py": "e774be89193472dfa4b142d85bdcc46c"}


def md5(b):
    return hashlib.md5(b).hexdigest()


def edit(text, anchor, new, name, where="replace"):
    n = text.count(anchor)
    if n != 1:
        raise SystemExit("REFUSED: anchor for %s found %d times (need 1)" % (name, n))
    if where == "after":
        return text.replace(anchor, anchor + new)
    if where == "before":
        return text.replace(anchor, new + anchor)
    return text.replace(anchor, new)


def build_widget(src, block):
    t = src
    # W1 the flag, beside S441's four (line 70)
    t = edit(t, '  var retryUp = CFG.retryUpload === true, directFile = CFG.directFile === true;      // S441\n',
             '  var cvScanOn = (CFG.cvScan === true) && !!CFG.cvUrl;                                  // S523: the smart outline (set below)\n',
             "W1 flag", "after")
    # W2 the camera asks for 8 MP when the smart outline is on (openCam)
    t = edit(t, '    var want = {video:{facingMode:{ideal:"environment"}, width:{ideal:1920}, height:{ideal:1440}}, audio:false};',
             '    var want = {video:{facingMode:{ideal:"environment"}, width:{ideal: cvScanOn ? 3264 : 1920}, height:{ideal: cvScanOn ? 2448 : 1440}}, audio:false};   // S523: 8 MP with the smart outline',
             "W2 camera")
    # W3 the live outline follows the stream
    t = edit(t, '    camChrome(false);\n    say(""); listCams();\n  }',
             '    camChrome(false);\n    say(""); listCams();\n    if (cvScanOn) liveStart();                                                        // S523\n  }',
             "W3 liveStart")
    t = edit(t, '  function stopStream(){ if (stream){ stream.getTracks().forEach(function(t){ t.stop(); }); stream = null; } }',
             '  function stopStream(){ if (cvScanOn) liveStop();                                                            // S523\n'
             '    if (stream){ stream.getTracks().forEach(function(t){ t.stop(); }); stream = null; } }',
             "W4 liveStop")
    # W5 a capture goes to the smart path (a canvas, no re-encode)
    t = edit(t, '    if (autoPage) { autoAdd(c.toDataURL("image/jpeg", 0.92)); return; }               // S441: the camera stays open',
             '    if (autoPage && cvScanOn) { autoAddCV(c); return; }                                 // S523: the camera stays open, the smart outline\n'
             '    if (autoPage) { autoAdd(c.toDataURL("image/jpeg", 0.92)); return; }               // S441: the camera stays open',
             "W5 shoot")
    # W6 a chosen photo too
    t = edit(t, '    (autoPage ? autoAdd : loadImage)(URL.createObjectURL(importQueue.shift()));        // S441',
             '    (autoPage ? (cvScanOn ? autoAddCV : autoAdd) : loadImage)(URL.createObjectURL(importQueue.shift()));        // S441; S523',
             "W6 import")
    # W7 the stage's two buttons finish an Adjust
    t = edit(t, '  function addPage(){ addCaptured(warp()); }\n  function addWhole(){ addCaptured(wholeImage()); }',
             '  function addPage(){ if (cvScanOn && adjustIdx >= 0) { adjustDone(); return; } addCaptured(warp()); }                       // S523\n'
             '  function addWhole(){ if (cvScanOn && adjustIdx >= 0) { corners = [[0,0],[ov.width,0],[ov.width,ov.height],[0,ov.height]]; adjustDone(); return; }\n'
             '    addCaptured(wholeImage()); }',
             "W7 addPage")
    # W8 deleting a page drops its kept original
    t = edit(t, '      x.onclick = function(){ pages.splice(i,1); retakeIdx = -1;',
             '      x.onclick = function(){ pages.splice(i,1); retakeIdx = -1; if (cvScanOn) dropSrc(i);                           // S523',
             "W8 delete")
    # W9 the Adjust button beside Retake
    t = edit(t, '        wrap.appendChild(rt);\n      }\n      box.appendChild(wrap);',
             '        wrap.appendChild(rt);\n'
             '        if (cvScanOn && cvReady && pageSrc[i]) {                                                              // S523: Adjust\n'
             '          var aj = document.createElement("button"); aj.type = "button"; aj.textContent = (adjustIdx === i) ? "\\u270E adjust ho raha" : "Adjust";\n'
             '          aj.style.cssText = rt.style.cssText.replace(/background:[^;]*/, "background:" + (adjustIdx === i ? "#ffe08a" : "#eef2f8"));\n'
             '          aj.onclick = function(){ if (adjustIdx === i) { adjustIdx = -1; $("stage").style.display = "none"; $("addpage").textContent = "\\u2714 Add this page"; renderPages(); say(""); } else { adjustOpen(i); } };\n'
             '          wrap.appendChild(aj);\n'
             '        }\n'
             '      }\n      box.appendChild(wrap);',
             "W9 adjust button")
    # W10 the stage's Retake cancels an Adjust
    t = edit(t, '  function resetShot(){ $("stage").style.display = "none"; $("cam").value = "";',
             '  function resetShot(){ $("stage").style.display = "none"; $("cam").value = "";\n'
             '    if (cvScanOn && adjustIdx >= 0) { adjustIdx = -1; adjustImg = null; $("addpage").textContent = "\\u2714 Add this page"; renderPages(); }   // S523',
             "W10 resetShot")
    # W11 Save hands the pages on and lets the originals go
    t = edit(t, '    if (inlineStamp && mode === "doc") { enqueue(pages.slice()); pages = []; retakeIdx = -1; renderPages(); updateSaveBar(); return; }   // S441',
             '    if (inlineStamp && mode === "doc") { enqueue(pages.slice()); pages = []; retakeIdx = -1; if (cvScanOn) clearSrc(); renderPages(); updateSaveBar(); return; }   // S441; S523',
             "W11 save")
    # W12 the block itself, before the buttons are wired
    t = edit(t, '  /* ======================= end S441 ======================================= */\n',
             block, "W12 block", "after")
    assert t.count("S523") >= 14
    return t


def build_app(src):
    t = src
    # A1 the intake's config: one key pair, behind the owner's switch
    t = edit(t, '        "slipJsonUrl": url_for("intake_slip", bid=987654321).replace("987654321", "{id}") + "?json=1",\n    }\n',
             '        "slipJsonUrl": url_for("intake_slip", bid=987654321).replace("987654321", "{id}") + "?json=1",\n    }\n'
             '    if _scan_cv_on():                                                                  # S523: the smart outline, the owner\'s switch on /admin\n'
             '        scan_cfg["cvScan"] = True\n'
             '        scan_cfg["cvUrl"] = url_for("scanner_opencv_js") + "?v=" + str(_opencv_version())\n',
             "A1 intake cfg")
    # A2 the library's route, beside the widget's
    t = edit(t, '@app.route("/scan/widget.js")\ndef scanner_widget_js():',
             'OPENCV_JS_PATH = os.environ.get("SCANNER_OPENCV_JS", os.path.join(os.path.dirname(__file__), "static", "opencv.js"))   # S523\n'
             '\n'
             'def _scan_cv_on():\n'
             '    """S523: the smart outline is on only when the owner has switched it on and the library is on disk."""\n'
             '    try:\n'
             '        return (setting_or("scan.cv", "off") or "").strip().lower() == "on" and os.path.exists(OPENCV_JS_PATH)\n'
             '    except Exception:                                                # noqa: BLE001\n'
             '        return False\n'
             '\n'
             'def _opencv_version():\n'
             '    try:\n'
             '        return int(os.path.getmtime(OPENCV_JS_PATH))\n'
             '    except OSError:\n'
             '        return 0\n'
             '\n'
             '@app.route("/scan/opencv.js")\n'
             'def scanner_opencv_js():\n'
             '    """S523: OpenCV.js served by our own app -- the gzip copy when the browser takes it (3.4 MB instead of 10),\n'
             '    cached for a year under its ?v= stamp, so each phone downloads it once."""\n'
             '    if not os.path.exists(OPENCV_JS_PATH):\n'
             '        abort(404)\n'
             '    gz = OPENCV_JS_PATH + ".gz"\n'
             '    if "gzip" in (request.headers.get("Accept-Encoding") or "") and os.path.exists(gz):\n'
             '        resp = send_file(gz, mimetype="application/javascript")\n'
             '        resp.headers["Content-Encoding"] = "gzip"\n'
             '        resp.headers["Vary"] = "Accept-Encoding"\n'
             '    else:\n'
             '        resp = send_file(OPENCV_JS_PATH, mimetype="application/javascript")\n'
             '    resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"\n'
             '    return resp\n'
             '\n'
             '@app.route("/scan/widget.js")\ndef scanner_widget_js():',
             "A2 route")
    # A3 the switch on /admin: the action
    t = edit(t, '        elif act == "set_palette":\n',
             '        elif act == "set_scan_cv":                                                     # S523\n'
             '            db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(\'scan.cv\',?)",\n'
             '                       ("on" if request.form.get("on") == "1" else "off",))\n'
             '            flash("Smart outline (OpenCV) is now %s for the bill intake." % ("ON" if request.form.get("on") == "1" else "OFF"))\n'
             '        elif act == "set_palette":\n',
             "A3 admin action")
    # A4 the switch on /admin: the card, before Locations
    t = edit(t, '<div class=card><h4>Locations</h4>\n',
             '<div class=card><h4>Scanner \\u2014 smart outline (OpenCV)</h4>\n'
             '<p class=muted>On the bill intake only. When ON, a phone that can carry it downloads the library once (3.4 MB), shows the paper\\u2019s outline live on the camera, keeps the full camera resolution and offers <b>Adjust</b> on every page. A phone that cannot keeps today\\u2019s scanner by itself. The other scan screens are untouched.</p>\n'
             '<p>Now: <b>{{\'ON\' if scan_cv else \'OFF\'}}</b>{% if not opencv_present %} <span class=muted>(library file not on the server \\u2014 stays off)</span>{% endif %}</p>\n'
             '<form method=post><input type=hidden name=action value=set_scan_cv><input type=hidden name=on value="{{\'0\' if scan_cv else \'1\'}}">\n'
             '<button class="btn small">{{\'Switch OFF\' if scan_cv else \'Switch ON\'}}</button></form></div>\n'
             '<div class=card><h4>Locations</h4>\n',
             "A4 admin card")
    t = edit(t, '        palettes=PALETTES, cur_palette=setting_or("palette", DEFAULT_PALETTE),\n        ocr_key=bool(SARVAM_API_KEY))',
             '        palettes=PALETTES, cur_palette=setting_or("palette", DEFAULT_PALETTE),\n'
             '        scan_cv=_scan_cv_on(), opencv_present=os.path.exists(OPENCV_JS_PATH),                     # S523\n'
             '        ocr_key=bool(SARVAM_API_KEY))',
             "A5 admin ctx")
    # A6 the reception login may fetch the library (the route is open like the widget's; named here on purpose, A-D21)
    t = edit(t, 'RECEPTION_OK = {"intake", "intake_submit", "intake_scan_submit", "intake_slip_last",\n                "intake_slip", "scanner_widget_js", "login", "logout"}', 'RECEPTION_OK = {"intake", "intake_submit", "intake_scan_submit", "intake_slip_last",\n                "intake_slip", "scanner_widget_js", "scanner_opencv_js", "login", "logout"}      # S523: + the library', "A6 reception ok")
    assert t.count("S523") >= 6
    return t


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    live, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    srcs = {}
    for name, want in FROM.items():
        b = open(os.path.join(live, name), "rb").read()
        got = md5(b)
        if got != want:
            raise SystemExit("REFUSED: %s is %s, not the pinned %s" % (name, got[:8], want[:8]))
        srcs[name] = b.decode("utf-8")
    block = open(os.path.join(HERE, "s523_block.js"), encoding="utf-8").read()
    w = build_widget(srcs["scanner_widget.js"], block)
    a = build_app(srcs["asset_register.py"])
    for name, text in (("scanner_widget.js", w), ("asset_register.py", a)):
        b = text.encode("utf-8")
        open(os.path.join(out, name), "wb").write(b)
        print("%s  %s  %d bytes" % (md5(b), name, len(b)))
    print("BUILT")


if __name__ == "__main__":
    main()
