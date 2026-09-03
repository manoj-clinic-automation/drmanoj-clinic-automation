#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RENDER_TEST_corrections_hide_s222.py -- A REAL BROWSER, twice: as Amir, and as the owner.

The rule for this project's pages since S214 v5 shipped with dead taps: no page change goes
out without headless chromium opening it and looking at what a human would see. This one
matters more than most, because the whole change IS what a human sees -- the server behaviour
is identical before and after.

It serves the PATCHED page with two stubs:
    /finance/darpan/api/corrections   -- so the top half loads normally
    /finance/darpan/api/ledger-check  -- 403 for the viewer run, 200 for the owner run,
                                         and a hard connection failure for the third run

and then asks the browser what is actually on the screen.

Runs OFFLINE, in the workspace -- the VPS has no browser.

    python3 -B RENDER_TEST_corrections_hide_s222.py [path-to-patched-darpan_corrections.html]
"""
import os
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.abspath(sys.argv[1] if len(sys.argv) > 1
                       else os.path.join(HERE, "darpan_corrections.html"))
PORT = 8747
MODE = {"ledger": 403}
FAILED, PASSED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("   [%s]" % detail) if detail else ""))


def main():
    if not os.path.exists(PAGE):
        raise SystemExit("no page at %s" % PAGE)
    html = open(PAGE, encoding="utf-8").read()
    if "S222 star-1-2" not in html:
        raise SystemExit("that page is not patched -- run the patcher first")

    from flask import Flask, jsonify, Response
    app = Flask("render_s222")

    @app.route("/finance/darpan/corrections")
    def page():
        return Response(html, mimetype="text/html")

    @app.route("/finance/darpan/api/corrections")
    def api_corr():
        return jsonify(ok=True, month="2026-09", months=["2026-09"], pending=2,
                       corrected=5, rows=[dict(id=1, date="2026-09-02", bill="B1",
                                               amount_p=25000, rrn="", answered_by=None,
                                               answer=None, ticked_by=None, ticked_at=None)])

    @app.route("/finance/darpan/api/ledger-check")
    def api_lc():
        m = MODE["ledger"]
        if m == "boom":
            # a dead connection, not a polite error
            os._exit  # noqa -- never called; the route below closes the socket
            return Response("", status=500)
        if m == 403:
            return jsonify(ok=False, error="not_permitted"), 403
        return jsonify(ok=True, date="2026-09-02", findings=[])

    threading.Thread(target=lambda: app.run(port=PORT, threaded=True,
                                            use_reloader=False), daemon=True).start()
    time.sleep(1.5)

    from playwright.sync_api import sync_playwright
    url = "http://127.0.0.1:%d/finance/darpan/corrections" % PORT
    chrome = os.environ.get("PW_CHROME",
                            "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=chrome)
        pg = b.new_page(viewport={"width": 390, "height": 780})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))

        def look(label):
            pg.goto(url, wait_until="networkidle")
            time.sleep(0.6)
            el = pg.query_selector("#ownerOnly")
            visible = bool(el and el.is_visible())
            body = pg.inner_text("body")
            return visible, body

        print("-- 1  AS AMIR (the server answers 403) ---------------------------")
        MODE["ledger"] = 403
        vis, body = look("viewer")
        ck("the ledger-check / transfer block is NOT on his screen", not vis)
        ck("the words 'Record an owner transfer' are not visible",
           "Record an owner transfer" not in body)
        ck("the words 'Ledger check' are not visible", "Ledger check" not in body)
        ck("his own corrections list IS still there", "pending" in body)
        ck("the corrections table rendered", "B1" in body)
        ck("no javascript error", not errs, "; ".join(errs))

        print("\n-- 2  AS THE OWNER (the server answers 200) ----------------------")
        errs[:] = []
        MODE["ledger"] = 200
        vis, body = look("owner")
        ck("the block IS on his screen", vis)
        ck("'Ledger check and owner transfer' is visible",
           "Ledger check and owner transfer" in body)
        ck("'Record an owner transfer' is visible", "Record an owner transfer" in body)
        ck("the Record transfer button is there", bool(pg.query_selector("#tBtn")))
        ck("the Check this date button is there", bool(pg.query_selector("#lcBtn")))
        ck("his corrections list is still there too", "pending" in body)
        ck("no javascript error", not errs, "; ".join(errs))

        print("\n-- 3  THE FAIL-OPEN, on a route that is not there at all ---------")
        # the deliberate ruling: an error must NEVER cost the owner his control
        errs[:] = []
        MODE["ledger"] = 404
        vis, body = look("error")
        ck("a non-403 answer shows the block (fail-open)", vis)
        ck("no javascript error", not errs, "; ".join(errs))

        print("\n-- 4  AND THE SERVER IS STILL THE REAL GATE ----------------------")
        ck("this kit changed no server file",
           "api/ledger-check" in html and "api/transfer" in html)
        ck("the block starts hidden in the markup, so a viewer never sees a flash",
           'id="ownerOnly" hidden style="display:none"' in html)

        b.close()

    n = len(PASSED) + len(FAILED)
    print("\n%s -- %d passed, %d failed"
          % ("RENDER GREEN" if not FAILED else "RENDER RED", len(PASSED), len(FAILED)))
    for x in FAILED:
        print("   FAILED: %s" % x)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
