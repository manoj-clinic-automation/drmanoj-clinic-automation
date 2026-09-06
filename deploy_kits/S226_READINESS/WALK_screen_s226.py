"""S226 -- THE SCREEN ITSELF.

The first walk proves the payload and the markup. This one opens the two live
pages in a real browser and reads what a person would read. S209's lesson: a
page can pass every server gate and still be dead in the browser.
"""
import os, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import WALK_readiness_s226 as W
from playwright.sync_api import sync_playwright

OK, BAD = [], []
def chk(n, c, d=""):
    (OK if c else BAD).append(n + (("  -- " + str(d)) if d and not c else ""))
    print(("  ok   " if c else "  FAIL ") + n + (("   " + str(d)) if d else ""))

W.DB = os.path.join(HERE, "_walk226_screen.db")
con = W.build(); W.fill(con)
app = W.app_for(con)
srv = threading.Thread(target=lambda: app.run(port=8791, threaded=False),
                       daemon=True)
srv.start(); time.sleep(1.5)

print("== S226 READINESS -- the screen ==")
errs = []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 390, "height": 844})   # a phone, as counted on
    pg.on("pageerror", lambda e: errs.append(str(e)))
    # Benign here and only here: the container has no egress to Google Fonts
    # (the count page has loaded them since S213, unchanged by this kit) and a
    # test server serves no favicon. Anything else is a real page error.
    def _con(m):
        t = m.text
        if m.type != "error":
            return
        if "Failed to load resource" in t:
            return
        errs.append(t)
    pg.on("console", _con)

    pg.goto("http://127.0.0.1:8791/finance/stock/page/drift")
    pg.wait_for_timeout(900)
    t = pg.inner_text("#rdy")
    chk("drift: the header PAINTED", len(t) > 40, t[:70])
    chk("drift: last bill number on the screen", "A003412" in t)
    chk("drift: purchases horizon on the screen", "03-09-2026" in t)
    chk("drift: the stock export's date AND time", "06-09-2026 03:10" in t)
    chk("drift: the credit-note sentence", "CN00161" in t)
    chk("drift: the last day's bills are listed by supplier",
        "PRIME ORTHO" in t and "PO/2210" in t)
    chk("drift: the money reads as rupees", "Rs 54,119.00" in t, t)
    chk("drift: the warning is visible", "Count after the purchase export" in t)
    box = pg.locator("#rdy-card").bounding_box()
    items = pg.locator("h2", has_text="Items").first.bounding_box()
    chk("drift: the header is ABOVE the results", box["y"] < items["y"],
        (box["y"], items["y"]))
    chk("drift: the page's own rows still render",
        "BIO D3 MAX" in pg.inner_text("#rows"))
    chk("drift: no horizontal scroll at phone width",
        pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2"))

    pg.goto("http://127.0.0.1:8791/finance/stock/page/count")
    pg.wait_for_timeout(900)
    t2 = pg.inner_text("#rdy")
    chk("count: the header PAINTED", len(t2) > 40, t2[:70])
    chk("count: last bill number on the screen", "A003412" in t2)
    chk("count: the gate still works below it",
        "Stock check" in pg.inner_text("#gate"))
    chk("count: no horizontal scroll at phone width",
        pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2"))
    b.close()

chk("no javascript error on either page", not errs, errs[:3])
print("\n%d ok, %d FAILED" % (len(OK), len(BAD)))
for x in BAD:
    print("   FAILED: " + x)
sys.exit(1 if BAD else 0)
