"""S226 -- THE END OF THE COUNT, DRIVEN.

Darpan and Amir are counting now. The next things they touch are REPORT and
SEND TO LEDGER, and nobody has driven either today. If the end of the flow is
broken, a whole morning's count is lost at the last tap.

Read-only on every live system: this runs against a throwaway database.
"""
import os, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import WALK_readiness_s226 as R
from playwright.sync_api import sync_playwright

OK, BAD, NOTE = [], [], []
def chk(n, c, d=""):
    (OK if c else BAD).append(n + (("  -- " + str(d)) if d and not c else ""))
    print(("  ok   " if c else "  FAIL ") + n + (("   " + str(d)) if d else ""))
def note(n): NOTE.append(n); print("  NOTE " + n)

R.DB = os.path.join(HERE, "_walk226d.db")
con = R.build(); R.fill(con)
ITEMS = (('PRIME CAST 5"', 45, "1*1", 1), ("BIO D3 MAX", 358, "1*15", 15),
         ("LACTOVAX SYP 200ML", 5, "1*1", 1), ("MEG QCS", 684, "1*15", 15),
         ("ALCOXIB 120", 13, "1*10", 10), ("TYRO BR", 700, "1*10", 10))
for item, q, pk, ps in ITEMS:
    con.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,"
                "pack_size,source,loaded_at) VALUES (?,?,?,?,?,?,?)",
                ("06-09-2026", item, q, pk, ps, "push_snapshot.py",
                 "2026-09-06T09:00:59"))
con.commit()
app = R.app_for(con)
threading.Thread(target=lambda: app.run(port=8803, threaded=False), daemon=True).start()
time.sleep(1.5)
URL = "http://127.0.0.1:8803/finance/stock/page/count"

SEED = """() => localStorage.setItem("sanj-stock-live-v1", JSON.stringify({
  cby:"Darpan", eby:"Amir", bill:"A003425", billdate:"2026-09-06",
  started:"2026-09-06T10:15:00",
  e:{ "MEG QCS":{c:684,cby:"Darpan",eby:"Amir",at:"2026-09-06T10:30:00"},
      "TYRO BR":{c:690,cby:"Darpan",eby:"Amir",at:"2026-09-06T10:31:00"},
      "BIO D3 MAX":{c:358,cby:"Darpan",eby:"Amir",at:"2026-09-06T10:32:00"},
      "ALCOXIB 120":{c:11,cby:"Darpan",eby:"Amir",at:"2026-09-06T10:33:00"} }}));"""

print("== S226 -- REPORT AND SEND TO LEDGER, driven ==")
errs, dialogs = [], []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 390, "height": 844})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text)
          if m.type == "error" and "Failed to load resource" not in m.text else None)
    pg.on("dialog", lambda d: (dialogs.append((d.type, d.message)), d.accept()))

    pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate(SEED)
    pg.reload(); pg.wait_for_timeout(600)
    pg.locator("#start").click(); pg.wait_for_timeout(400)
    chk("four of six counted, two of them differing", "4 / 6" in pg.inner_text("#prog"),
        pg.inner_text("#prog"))

    # ---------------------------------------------------------------- REPORT
    pg.locator("#toReport").click(); pg.wait_for_timeout(500)
    rep = pg.inner_text("#out")
    chk("the report renders at all", len(rep) > 50, rep[:80])
    chk("it names both differences",
        "TYRO BR" in rep and "ALCOXIB 120" in rep, rep[:200])
    chk("it does not claim the two that matched are differences",
        rep.count("MEG QCS") <= 1, rep[:300])
    chk("it says how many were not counted", "2" in rep, rep[:200])
    chk("no page error while reporting", not errs, errs[:2])

    # ------------------------------------------------------- SEND TO LEDGER
    pg.locator("#toCount").click(); pg.wait_for_timeout(300)
    pg.locator("#share").click(); pg.wait_for_timeout(1200)
    kinds = [d[0] for d in dialogs]
    chk("a partial count ASKS before sending", "confirm" in kinds, dialogs)
    chk("...and then confirms what it recorded", "alert" in kinds, dialogs)
    msg = " ".join(m for _, m in dialogs)
    chk("the confirmation names the count number", "count #" in msg, msg[:120])
    chk("the send did not throw", not errs, errs[:2])

    row = con.execute("SELECT id, items_counted, items_total, bill_no FROM "
                      "stock_count ORDER BY id DESC LIMIT 1").fetchone()
    chk("the ledger holds the count", row is not None and row[1] == 4, row)
    chk("...pinned to the bill the gate asked for", row and row[3] == "A003425", row)
    cid = row[0]
    diffs = con.execute("SELECT item, marg_qty, counted_qty, diff FROM stock_diff "
                        "WHERE count_id=? ORDER BY item", (cid,)).fetchall()
    chk("exactly two differences raised, and the right two",
        sorted(d[0] for d in diffs) == ["ALCOXIB 120", "TYRO BR"], diffs)
    chk("the differences carry the real numbers",
        {d[0]: (d[1], d[2], d[3]) for d in diffs}["TYRO BR"] == (700, 690, -10), diffs)
    f = con.execute("SELECT finding_no, lines_n FROM stock_finding WHERE count_id=?",
                    (cid,)).fetchone()
    chk("the finding is SEALED in the same breath", f is not None, f)
    rdy = con.execute("SELECT payload FROM stock_check_readiness WHERE count_id=?",
                      (cid,)).fetchone()
    chk("and the data horizon is frozen with it", rdy is not None)

    # -------------------------------------------- what the counter sees after
    chk("the Send button locks itself so it cannot go twice",
        pg.locator("#share").is_disabled())
    chk("...and says so", "Sent" in pg.locator("#share").inner_text(),
        pg.locator("#share").inner_text())

    # ------------------------------- THE ONE THAT MATTERS: a reload after send
    pg.reload(); pg.wait_for_timeout(700)
    left = pg.evaluate("(JSON.parse(localStorage.getItem('sanj-stock-live-v1'))||{}).e")
    sent_txt = ""
    try:
        pg.locator("#start").click(); pg.wait_for_timeout(400)
        sent_txt = pg.locator("#share").inner_text()
    except Exception:
        pass
    print("     after reload: entries=%s  progress=%s  share=%r"
          % (left, pg.inner_text("#prog") if pg.locator("#prog").count() else "?", sent_txt))
    chk("A RELOAD AFTER SENDING still knows the count went",
        "Sent" in sent_txt, sent_txt)
    chk("...the Send button stays locked", pg.locator("#share").is_disabled())
    banner = pg.inner_text("#sentbar") if pg.locator("#sentbar").count() else ""
    chk("...and the screen SAYS so, with the count number",
        "already been sent" in banner and "#1" in banner, banner[:120])
    import re as _re, datetime as _dt
    m = _re.search(r"at (\d{1,2}):(\d{2})( ?[AP]M)?", banner)
    _h = int(m.group(1)) if m else 0
    if m and m.group(3):                                   # the page prints 12-hour time: 01:04 PM
        _h = (_h % 12) + (12 if m.group(3).strip() == "PM" else 0)
    chk("...the time on it is the wall clock, never UTC",
        bool(m) and abs((_dt.datetime.now().hour * 60 + _dt.datetime.now().minute)
                        - (_h * 60 + int(m.group(2)))) < 5,
        (m.group(1) if m else None, _dt.datetime.now().strftime("%H:%M")))
    chk("...it explains why the list looks empty",
        "nothing has been lost" in banner, banner[:200])
    chk("...and warns against counting the same day twice",
        "second, separate count" in banner, banner[:250])

    # the only honest way to count again
    pg.locator("#newcount").click(); pg.wait_for_timeout(500)
    chk("'Start a genuinely new count' asks first",
        any(d[0] == "confirm" and "SEPARATE count" in d[1] for d in dialogs), dialogs[-1:])
    chk("...and then frees the page -- the banner is gone",
        pg.locator("#sentbar").count() == 0)
    chk("...the button no longer says Sent",
        "Sent" not in pg.locator("#share").inner_text(),
        pg.locator("#share").inner_text())
    pg.locator("#find").fill("meg"); pg.wait_for_timeout(200)
    pg.locator("#list .row .yes").first.click(); pg.wait_for_timeout(300)
    chk("...and it can send again once something IS counted",
        not pg.locator("#share").is_disabled(), pg.locator("#share").inner_text())
    chk("...while the count already in the ledger is untouched",
        con.execute("SELECT COUNT(*) FROM stock_count").fetchone()[0] == 1)
    pg.reload(); pg.wait_for_timeout(600); pg.locator("#start").click(); pg.wait_for_timeout(300)
    chk("...and that survives a reload too, without the old banner",
        pg.locator("#sentbar").count() == 0)
    b.close()

print("\n%d ok, %d FAILED, %d note(s)" % (len(OK), len(BAD), len(NOTE)))
for x in BAD: print("   FAILED: " + x)
for x in NOTE: print("   NOTE: " + x)
sys.exit(1 if BAD else 0)
