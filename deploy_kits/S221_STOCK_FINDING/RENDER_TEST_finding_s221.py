#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RENDER_TEST_finding_s221.py -- a REAL BROWSER on the audit document.

This page is a document three different people read and two of them act on, so
it is judged the way a document is judged: by opening it and looking. Headless
chromium loads the real page against the real blueprint on a copy of the live
database, once as the owner and once as the counter, and clicks for real.

Runs OFFLINE. The VPS has no browser.

    FIN_DB=/path/to/finance.db python3 -B RENDER_TEST_finding_s221.py
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import threading
import time

SRC_DB = os.environ.get("FIN_DB", "/tmp/w/finance.db")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FAILED, PASSED = [], []
ROLE = {"role": "checker", "user": "manoj"}


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("   [%s]" % detail) if detail and not cond else ""))


def main():
    tmp = tempfile.mkdtemp(prefix="render_sf_")
    db = os.path.join(tmp, "finance.db")
    shutil.copyfile(SRC_DB, db)

    from flask import Flask, jsonify
    import stock_app as SA
    app = Flask(__name__)

    def _db():
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        return c

    def _require(*roles):
        if ROLE["role"] not in roles:
            return None, (jsonify(ok=False, error="forbidden"), 403)
        return dict(ROLE), None

    SA.init(app, _db, _require, unit="medical", url_prefix="/finance/stock",
            marg_token="t")
    port = 8751
    threading.Thread(target=lambda: app.run(port=port, threaded=True,
                                            use_reloader=False), daemon=True).start()
    time.sleep(1.8)

    cl = app.test_client()
    AS_ON = "02-02-2027"
    cl.post("/finance/stock/api/snapshot", json=dict(
        as_on=AS_ON, source="render",
        items=[dict(item="ZZR ALPHA", qty=100, pack_size=10, rate_p=250),
               dict(item="ZZR NORATE", qty=30, pack_size=10)]))
    j = cl.post("/finance/stock/api/count", json=dict(
        marg_as_on=AS_ON, bill_no="A008888", bill_date="02-02-2027", items_total=2,
        items=[dict(item="ZZR ALPHA", marg_qty=100, counted_qty=92, pack_size=10,
                    counted_by="alisha", entered_by="shivani"),
               dict(item="ZZR NORATE", marg_qty=30, counted_qty=26, pack_size=10,
                    counted_by="alisha", entered_by="shivani")])).get_json()
    cid = j["count_id"]

    from playwright.sync_api import sync_playwright
    chrome = os.environ.get("PW_CHROME",
                            "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    url = "http://127.0.0.1:%d/finance/stock/page/finding?id=%d" % (port, cid)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"])

        # ---------------------------------------------------- as the OWNER
        pg = b.new_page(viewport={"width": 1100, "height": 900})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url)
        pg.wait_for_timeout(1500)
        body = pg.inner_text("body")
        ck("no javascript error on the document", not errs, "; ".join(errs[:2]))
        ck("the finding is titled and numbered", "audit finding" in body and "SF-" in body)
        ck("it names the Marg export it was counted against", AS_ON in body)
        ck("it names the people who counted and wrote",
           "alisha" in body and "shivani" in body, body[:400])
        ck("the seal is shown and reads as unchanged",
           "seal" in body.lower() and "unchanged" in body.lower())
        ck("it states the basis in words, on the document itself",
           "valued at MRP" in body, body[:600])
        ck("it says the cost column is empty on purpose",
           "purchase prices are not in the system" in body)
        ck("the shortage shows at MRP (Rs 20.00 for 8 units at Rs 2.50)",
           "20.00" in body, body[:800])
        ck("the unvalued item has its own block, and says it is not in the totals",
           "No rate" in body and "ZZR NORATE" in body)
        ck("it says in plain words that nothing is deducted",
           "not deducted from anybody" in body)

        ck("the owner is offered the three decisions",
           all(w in body for w in ("write off", "recover", "no loss")))
        od = pg.eval_on_selector_all(
            "button", "es=>es.filter(e=>(e.getAttribute('onclick')||'')"
                      ".indexOf('decide(')>=0).length")
        ck("and they are real buttons, three per valued line", od >= 3, str(od))
        ck("the owner is NOT offered the staff's reason buttons",
           "बिल नहीं बना" not in body)

        # click a real decision
        pg.click("text=write off")
        pg.wait_for_timeout(1200)
        body2 = pg.inner_text("body")
        ck("after the tap the line reads 'written off'", "written off" in body2)
        ck("and the written-off total is no longer zero",
           "Written off" in body2 and "20.00" in body2)
        ck("a Written off list appeared", "ZZR ALPHA" in body2)
        ck("still no javascript error", not errs, "; ".join(errs[:2]))

        # the print stylesheet must exist and hide the controls
        ck("the page carries a print stylesheet", "@media print" in pg.content())
        ck("the buttons are marked not-to-print",
           pg.eval_on_selector_all(".noprint", "e=>e.length") > 3)
        ck("there are signature lines for the hard copy",
           "Counted by" in pg.content() and "Seen by" in pg.content())

        # ---------------------------------------------------- as the COUNTER
        ROLE.update(role="maker", user="darpan")
        pg2 = b.new_page(viewport={"width": 390, "height": 844})
        errs2 = []
        pg2.on("pageerror", lambda e: errs2.append(str(e)))
        pg2.goto(url)
        pg2.wait_for_timeout(1500)
        sbody = pg2.inner_text("body")
        ck("the counter gets the SAME document", "SF-" in sbody and AS_ON in sbody)
        ck("the counter is offered the reasons, in Hindi",
           "बिल नहीं बना" in sbody)
        # asserted on the DOM, not on page text: the words "written off" appear
        # legitimately in the owner's earlier ruling, and a text match would
        # have called that a failure. What must be absent is the BUTTON.
        nd = pg2.eval_on_selector_all(
            "button", "es=>es.filter(e=>(e.getAttribute('onclick')||'')"
                      ".indexOf('decide(')>=0).length")
        ck("the counter is offered NO decision button at all", nd == 0, str(nd))
        nr = pg2.eval_on_selector_all(
            "button", "es=>es.filter(e=>(e.getAttribute('onclick')||'')"
                      ".indexOf('answer(')>=0).length")
        ck("but he is offered the reason buttons", nr > 0, str(nr))
        pg2.click("text=बिल नहीं बना")
        pg2.wait_for_timeout(1200)
        ck("his answer appears on the line with his name",
           "darpan" in pg2.inner_text("body"))
        ck("no javascript error on the phone view", not errs2, "; ".join(errs2[:2]))
        b.close()

    con = sqlite3.connect(db)
    n = con.execute("SELECT COUNT(*) FROM stock_diff_decision").fetchone()[0]
    a = con.execute("SELECT COUNT(*) FROM stock_diff_answer").fetchone()[0]
    ck("the browser's clicks wrote exactly one decision and one answer",
       n == 1 and a == 1, "decisions=%d answers=%d" % (n, a))
    for t in [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND ("
            "name LIKE '%ledger%' OR name LIKE '%advance%' OR name LIKE '%salary%')")]:
        pass
    con.close()

    print("\n%s -- %d passed, %d failed" %
          ("RENDER GREEN" if not FAILED else "RENDER RED", len(PASSED), len(FAILED)))
    for f in FAILED:
        print("   FAILED: %s" % f)
    return 0 if not FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
