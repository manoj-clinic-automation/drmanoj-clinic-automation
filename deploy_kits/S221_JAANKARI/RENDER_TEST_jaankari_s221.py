#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RENDER_TEST_jaankari_s221.py -- a REAL BROWSER actually clicking this page.

The standing rule for returns_desk.html since S214 v6: no change to this page
ships without headless chromium opening it and clicking the flow. S214 v5 went
out with node-clean syntax, 45 green server checks and DEAD TAPS, because no
browser had ever touched it. This is that gate for the S221 jaankari card.

It serves the patched desk on localhost, opens it in chromium, reads what a
human would actually see, clicks the buttons, and checks the rows leave the
list. Run OFFLINE, in the workspace -- it is the kit's evidence, not a step on
the box (the VPS has no browser).

    FIN_DB=/path/to/finance.db python3 -B RENDER_TEST_jaankari_s221.py
"""

import datetime as dt
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


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("   [%s]" % detail) if detail and not cond else ""))


def main():
    tmp = tempfile.mkdtemp(prefix="render_jk_")
    db = os.path.join(tmp, "finance.db")
    shutil.copyfile(SRC_DB, db)
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    today = dt.date.today().isoformat()

    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    con.execute(
        "CREATE TABLE IF NOT EXISTS identity_dispute ("
        " id INTEGER PRIMARY KEY, unit TEXT NOT NULL, business_date TEXT NOT NULL,"
        " bill_no TEXT, clinic_id TEXT NOT NULL, bill_name TEXT, master_name TEXT,"
        " patient_ref_id INTEGER, kind TEXT NOT NULL DEFAULT 'sale',"
        " status TEXT NOT NULL DEFAULT 'open', noted_at TEXT NOT NULL,"
        " resolved_by TEXT, resolved_at TEXT, resolution TEXT,"
        " UNIQUE(unit, business_date, bill_no, clinic_id))")
    con.execute(
        "CREATE TABLE IF NOT EXISTS stock_spot_check ("
        " id INTEGER PRIMARY KEY, unit TEXT NOT NULL, business_date TEXT NOT NULL,"
        " bill_no TEXT NOT NULL, item_key TEXT NOT NULL, item_name TEXT, batch TEXT,"
        " reason TEXT NOT NULL, requested_at TEXT NOT NULL,"
        " status TEXT NOT NULL DEFAULT 'due' CHECK (status IN ('due','done','skipped')),"
        " counted_qty TEXT, counted_by TEXT, counted_at TEXT, note TEXT,"
        " UNIQUE(unit, bill_no, item_key))")
    pat = con.execute("SELECT clinic_id, name FROM patient_ref WHERE clinic_id!='WALK-IN' "
                      "AND name IS NOT NULL AND name!='' LIMIT 1").fetchone()
    mob = "9" + "5" * 4 + "4" * 5                              # assembled: F-185
    try:
        con.execute("UPDATE patient_ref SET mobile=? WHERE clinic_id=?",
                    (mob, pat["clinic_id"]))
    except Exception:
        pass
    con.execute("INSERT INTO identity_dispute (unit, business_date, bill_no, clinic_id,"
                " bill_name, master_name, kind, status, noted_at)"
                " VALUES ('medical',?,?,?,?,?,'return','open',?)",
                (today, "RCN9001", pat["clinic_id"], "ZZQX TESTNAME", pat["name"], now))
    con.execute("INSERT INTO stock_spot_check (unit, business_date, bill_no, item_key,"
                " item_name, batch, reason, requested_at, status)"
                " VALUES ('medical',?,?,?,?,?,?,?, 'due')",
                (today, "RCN9002", "ZZ_KEY", "ZZQX TEST ITEM", "B-9", "large return", now))
    # AND an "identity needed" row, dated today, so the browser exercises THAT
    # group too. Without it the group renders zero rows and its taps would go
    # out untested -- which is precisely how S214 v5 shipped dead taps.
    walk = con.execute("SELECT id FROM patient_ref WHERE clinic_id='WALK-IN'").fetchone()
    con.execute("INSERT OR IGNORE INTO day_entry (unit, business_date, status, source,"
                " entered_by, entered_at) VALUES ('medical',?,'draft','app','render',?)",
                (today, now))
    eid = con.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?",
                      (today,)).fetchone()[0]
    con.execute("INSERT INTO sale_item (day_entry_id, unit, patient_ref_id, service,"
                " description, amount_p, source, source_ref, confidence)"
                " VALUES (?,'medical',?,'pharmacy_return',?,?, 'manual','RCN9003',0.5)",
                (eid, walk[0] if walk else None,
                 '{"patient_name": "ZZQX WALKIN TEST"}', 25000))
    con.commit()
    con.close()

    from flask import Flask
    import returns_desk as RD
    app = Flask(__name__)

    def _db():
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        return c

    RD.init(app, _db, lambda *r: ({"user": "darpan", "role": "maker"}, None),
            unit="medical")
    port = 8731
    t = threading.Thread(target=lambda: app.run(port=port, threaded=True,
                                                use_reloader=False), daemon=True)
    t.start()
    time.sleep(2.0)

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("PW_CHROME", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"),
                              args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 390, "height": 844})   # a phone, as he uses it
        errs = []
        bad = []
        # /favicon.ico 404s on this bare test server and on nothing else -- the
        # real portal serves one. Named and excluded, not silently swallowed:
        # every OTHER non-2xx is collected and asserted on below.
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text)
              if (m.type == "error" and "favicon" not in m.text
                  and "status of 404" not in m.text) else None)
        pg.on("requestfailed", lambda r: bad.append("REQFAIL " + r.url))
        pg.on("response", lambda r: bad.append("HTTP%d %s" % (r.status, r.url))
              if (r.status >= 400 and "favicon" not in r.url) else None)
        pg.goto("http://127.0.0.1:%d/finance/returns/desk/" % port)
        pg.wait_for_timeout(1200)

        ck("no javascript error on load", not errs, "; ".join(errs[:3]))
        ck("every request the page made returned 2xx (favicon aside)", not bad,
           "; ".join(bad[:3]))
        ck("the jaankari card is VISIBLE (not just present in the html)",
           pg.is_visible("#jkCard"))
        txt = pg.inner_text("#jkCard")
        ck("it says answering changes no money",
           "पैसा नहीं बदलता" in txt, txt[:120])
        ck("the dispute question is on screen", "RCN9001" in txt, txt[:200])
        ck("the FULL mobile is on screen (D363)", mob in txt, txt[:200])
        ck("the spot-count question is on screen", "ZZQX TEST ITEM" in txt)
        ck("the identity-needed question is on screen too", "RCN9003" in txt, txt[:300])
        ck("its rupee value is shown the way he reads money",
           "250" in txt, txt[:300])
        ck("no score, verdict, ratio or percentage is shown to him",
           not any(w in txt.lower() for w in ("score", "verdict", "%", "flag", "intent")),
           txt[:200])
        for w in ("यह सही है",
                  "बिल ढूँढ़ो",
                  "पता नहीं"):
            ck("the button %r is rendered" % w, w in txt)

        # CLICK the owner's first word, for real
        pg.click("text=यह सही है")
        pg.wait_for_timeout(1200)
        txt2 = pg.inner_text("#jkCard")
        ck("after the tap the dispute row LEAVES his list", "RCN9001" not in txt2, txt2[:200])
        ck("and he is thanked", "✓" in txt2, txt2[:120])
        ck("still no javascript error after the tap", not errs, "; ".join(errs[:3]))

        # the identity row's own tap -- a DIFFERENT button, on a DIFFERENT group
        pg.click("text=बिल ढूँढ़ो")
        pg.wait_for_timeout(1200)
        ck("tapping 'bill dhoondho' on an identity row clears it too",
           "RCN9003" not in pg.inner_text("#jkCard"))

        # the count: type a number and tap
        ref = None
        con = sqlite3.connect(db)
        ref = str(con.execute("SELECT id FROM stock_spot_check WHERE bill_no='RCN9002'")
                  .fetchone()[0])
        con.close()
        pg.fill("#jkq_" + ref, "7")
        pg.click("text=गिन लिया")
        pg.wait_for_timeout(1200)
        txt3 = pg.inner_text("#jkCard")
        ck("after the count the spot row LEAVES his list too", "ZZQX TEST ITEM" not in txt3)
        ck("no javascript error at any point", not errs, "; ".join(errs[:3]))
        ck("no failed request at any point (favicon aside)", not bad, "; ".join(bad[:3]))

        pg.screenshot(path=os.path.join(HERE, "EVIDENCE_render_s221.png"), full_page=True)
        b.close()

    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT kind, answer, value, answered_by FROM jaankari_answer "
                       "ORDER BY id").fetchall()
    ck("the browser's three taps wrote exactly three evidence rows", len(rows) == 3,
       str([dict(r) for r in rows]))
    ck("the identity tap recorded 'find_bill'",
       any(r["kind"] == "identity" and r["answer"] == "find_bill" for r in rows))
    ck("the tap recorded 'ok' for the dispute",
       bool(rows) and rows[0]["kind"] == "dispute" and rows[0]["answer"] == "ok")
    ck("the typed count reached the record as 7",
       any(r["answer"] == "counted" and r["value"] == "7" for r in rows))
    st = con.execute("SELECT status FROM identity_dispute WHERE bill_no='RCN9001'").fetchone()
    ck("the dispute is STILL OPEN after a real human tap", st["status"] == "open")
    sp = con.execute("SELECT status FROM stock_spot_check WHERE bill_no='RCN9002'").fetchone()
    ck("the spot check is STILL DUE after a real typed count", sp["status"] == "due")
    con.close()

    print("\n%s -- %d passed, %d failed" %
          ("RENDER GREEN" if not FAILED else "RENDER RED", len(PASSED), len(FAILED)))
    for f in FAILED:
        print("   FAILED: %s" % f)
    return 0 if not FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
