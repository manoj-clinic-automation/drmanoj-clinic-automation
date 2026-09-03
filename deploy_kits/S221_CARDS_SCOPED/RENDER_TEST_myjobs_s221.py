#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RENDER_TEST_myjobs_s221.py -- a REAL BROWSER on Darpan's card.

The S218 directory was approved on paper and was wrong on the screen. This
change is therefore judged the same way it was found: by opening the page.

It serves the patched darpan_card.html with a stub `/finance/api/cards` fed from
the kit's own registry, opens it in headless chromium at phone width, and reads
what is actually on the glass -- which buttons appear, which do not, and that
the old directory language is gone. It then re-serves the SAME page against an
old registry with no `who` at all and proves the fail-safe: his navigation shows
everything rather than going blank.

Runs OFFLINE. The VPS has no browser.

    CARD=./darpan_card.html REG=./cards_registry.json python3 -B RENDER_TEST_myjobs_s221.py
"""

import json
import os
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CARD = os.environ.get("CARD", os.path.join(HERE, "darpan_card.html"))
REG = os.environ.get("REG", os.path.join(HERE, "cards_registry.json"))
BASE = os.environ.get("CARD_BASE", "")     # the UNPATCHED live card, for the differential

FAILED, PASSED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("   [%s]" % detail) if detail and not cond else ""))


def serve(port, cards, card_file=None):
    from flask import Flask, jsonify
    app = Flask(__name__)
    html = open(card_file or CARD, encoding="utf-8").read()

    @app.route("/finance/darpan")
    @app.route("/finance/darpan/")
    def page():
        return html, 200, {"Content-Type": "text/html; charset=utf-8"}

    @app.route("/finance/api/cards")
    def api():
        return jsonify(ok=True, cards=cards)

    # The card's OWN endpoints, stubbed with the SHAPE it reads rather than an
    # empty ok. A stub that answers {"ok":true} and nothing else makes the page
    # throw on its own fields, and then the harness reports a page error that
    # belongs to the harness -- F-142's family. Give it the shape.
    @app.route("/finance/darpan/api/card")
    def card_api():
        return jsonify(ok=True, date="2026-09-03",
                       sale=dict(day_sale_p=0, upi_p=0, net_cash_p=0, cn_p=0,
                                 cn_bills=[], parked=[], home_p=0, proc_p=0,
                                 ortho_p=0),
                       drawer=dict(counted_p=0, expected_p=0, diff_p=0),
                       exceptions=[], bank=dict())

    @app.route("/finance/darpan/api/<path:_p>")
    @app.route("/finance/api/<path:_p>")
    def rest(_p):
        return jsonify(ok=True, days=[], attention=[], cards=[], rows=[],
                       positions=[], units={}, totals={})

    threading.Thread(target=lambda: app.run(port=port, threaded=True,
                                            use_reloader=False), daemon=True).start()
    time.sleep(1.8)


def main():
    cards = json.load(open(REG, encoding="utf-8"))["cards"]
    serve(8741, cards)
    # A DIFFERENTIAL, not an absolute (the F-87 pattern). This harness cannot
    # stub every field the card's other sections read, and chasing them one by
    # one would only prove the stub complete. What must be proved is that MY
    # change adds no error: the UNPATCHED live card is run through the same
    # harness first, and only errors it did not already produce count.
    if BASE:
        serve(8744, cards, card_file=BASE)

    from playwright.sync_api import sync_playwright
    chrome = os.environ.get("PW_CHROME", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"])
        base_errs = set()
        if BASE:
            pb = b.new_page(viewport={"width": 390, "height": 844})
            pb.on("pageerror", lambda e: base_errs.add(str(e)))
            pb.goto("http://127.0.0.1:8744/finance/darpan")
            pb.wait_for_timeout(1500)
            base_body = pb.inner_text("body")
            ck("the BASELINE card really is the unpatched one (it still shows the directory)",
               "सारे कार्ड" in base_body)
            pb.close()
        pg = b.new_page(viewport={"width": 390, "height": 844})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("http://127.0.0.1:8741/finance/darpan")
        pg.wait_for_timeout(1500)
        body = pg.inner_text("body")

        new_errs = [e for e in errs if e not in base_errs]
        ck("this change introduces NO javascript error the live card did not "
           "already have (%d pre-existing, stub-caused)" % len(base_errs),
           not new_errs, "; ".join(new_errs[:2]))
        ck("the section is headed as HIS WORK, not as a directory",
           "मेरे काम" in body, body[-400:])
        ck("the old directory heading is GONE",
           "सारे कार्ड" not in body)
        ck("the old 'kaun: ... kaam: ...' line is gone",
           "कौन:" not in body and "काम:" not in body)

        # what he should see
        for want in ("Din ka card", "Vaapsi desk", "Stock count", "Staff register"):
            ck("his own card is offered: %s" % want, want in body, body[-500:])
        # what he should NOT see
        ck("Amir's corrections desk is NOT on his page", "Corrections desk" not in body)
        ck("Stock COUNT is on his page (owner, 03-Sep: 'might need 2 persons')",
           "Stock count" in body, body[-500:])
        ck("but stock DIFFERENCES is not -- that list is the others plus you",
           "Stock differences" not in body)
        ck("the page he is standing on is not offered back to him",
           "Drawer card" not in body)

        # they must be real, working links
        hrefs = pg.eval_on_selector_all("a", "els=>els.map(e=>e.getAttribute('href'))")
        ck("the buttons are real links to the real routes",
           "/finance/returns/desk" in hrefs and "/finance/daily" in hrefs and
           "/finance/stock/page/count" in hrefs and "/register" in hrefs,
           str([h for h in hrefs if h]))
        ck("no link to a page that is not his",
           "/finance/darpan/corrections" not in hrefs and
           "/finance/stock/page/diffs" not in hrefs)

        # THE FAIL-SAFE: an old registry with no `who` must not blank him
        old = [dict((k, v) for k, v in c.items() if k != "who") for c in cards]
        serve(8742, old)
        pg2 = b.new_page(viewport={"width": 390, "height": 844})
        errs2 = []
        pg2.on("pageerror", lambda e: errs2.append(str(e)))
        pg2.goto("http://127.0.0.1:8742/finance/darpan")
        pg2.wait_for_timeout(1500)
        body2 = pg2.inner_text("body")
        ck("fail-safe: a registry with no `who` shows him everything, not nothing",
           "Corrections desk" in body2 and "Stock count" in body2, body2[-300:])
        ck("even then, the page he is on is still left out", "Drawer card" not in body2)
        ck("no NEW javascript error in the fail-safe path",
           not [e for e in errs2 if e not in base_errs], "; ".join(errs2[:2]))

        # and an EMPTY registry must simply render no section at all
        serve(8743, [])
        pg3 = b.new_page(viewport={"width": 390, "height": 844})
        pg3.goto("http://127.0.0.1:8743/finance/darpan")
        pg3.wait_for_timeout(1200)
        ck("an empty registry renders no section at all",
           "मेरे काम" not in pg3.inner_text("body"))
        b.close()

    print("\n%s -- %d passed, %d failed" %
          ("RENDER GREEN" if not FAILED else "RENDER RED", len(PASSED), len(FAILED)))
    for f in FAILED:
        print("   FAILED: %s" % f)
    return 0 if not FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
