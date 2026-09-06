"""S226_DRIFT_TRUTH -- THE SCREENS. Both pages in a real browser at phone
width, reading what a person reads and measuring what he said was wrong:
the two headers that lacked clarity, and the column that did not line up."""
import os, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
# The readiness walk (and its schema finder) lives in the S226_READINESS kit.
# APPENDED, never inserted: that folder also holds the PREVIOUS stock_app.py,
# and putting it first silently tests the old file. It did, once.
_sib = os.path.join(os.path.dirname(HERE), "S226_READINESS")
if os.path.isdir(_sib) and _sib not in sys.path:
    sys.path.append(_sib)
import WALK_drift_truth_s226 as D
from playwright.sync_api import sync_playwright

OK, BAD = [], []
def chk(n, c, d=""):
    (OK if c else BAD).append(n + (("  -- " + str(d)) if d and not c else ""))
    print(("  ok   " if c else "  FAIL ") + n + (("   " + str(d)) if d else ""))

con, app = D.setup("_walk226b_screen.db")
threading.Thread(target=lambda: app.run(port=8795, threaded=False),
                 daemon=True).start()
time.sleep(1.5)
B = "http://127.0.0.1:8795/finance/stock/page/"

print("== S226_DRIFT_TRUTH -- the screens ==")
errs = []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 390, "height": 844})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text)
          if m.type == "error" and "Failed to load resource" not in m.text else None)

    # ------------------------------------------------------------ the drift page
    pg.goto(B + "drift"); pg.wait_for_timeout(900)
    head = " ".join(pg.inner_text("table:has(#rows) thead").split()).upper()
    chk("the headers now say what they mean",
        "GAP ON THE LAST DAY" in head and "DAY BY DAY (OLDEST → NEWEST)" in head,
        head[:140])
    chk("'Runs' and 'Recent' are gone",
        "RUNS" not in head and "RECENT" not in head, head[:140])
    chk("the gap is explained before the table",
        "our figure minus Marg" in pg.inner_text("body"))
    # the alignment he complained about: the day-by-day cell must sit inside
    # the right edge of its own header, not spill left of it.
    th = pg.locator("th", has_text="Day by day").first.bounding_box()
    td = pg.locator("#rows tr >> nth=0 >> td >> nth=5").bounding_box()
    chk("the day-by-day column sits under its header",
        abs((td["x"] + td["width"]) - (th["x"] + th["width"])) < 12,
        (round(td["x"] + td["width"]), round(th["x"] + th["width"])))
    chk("its right edges line up with the numeric columns too",
        td["x"] >= th["x"] - 2, (round(td["x"]), round(th["x"])))
    chk("a differing day is marked, an agreeing one is not",
        pg.locator("#rows .chipbad").count() >= 1,
        pg.locator("#rows .chipbad").count())
    chk("the merged item reads as agreeing",
        "agrees every day" in pg.inner_text("#rows"))
    chk("no sideways scroll at phone width",
        pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2"))

    # -------------------------------------------------------------- the new page
    pg.goto(B + "now"); pg.wait_for_timeout(900)
    body = pg.inner_text("body")
    chk("the stock page paints", "Stock as we hold it" in body)
    chk("it names the day it is for", "05-09-2026" in body, body[:200])
    chk("the readiness header is on it too", "A003412" in pg.inner_text("#rdy"))
    chk("ours and Marg's are both on the row",
        "65" in pg.inner_text("#rows") and "58" in pg.inner_text("#rows"))
    chk("the tiles count the shop", "items" in pg.inner_text("#tiles")
        and "agree with Marg" in pg.inner_text("#tiles"))
    pg.locator('#tabs button[data-f="differ"]').click(); pg.wait_for_timeout(250)
    only = pg.inner_text("#rows")
    chk("'only where we differ' really filters",
        "BIO D3 MAX" in only and "ACILOC 300" not in only, only[:120])
    pg.locator('#tabs button[data-f="below"]').click(); pg.wait_for_timeout(250)
    chk("'below zero' explains itself rather than alarming",
        "purchase bill has not been entered" in pg.inner_text("#filternote"))
    chk("no sideways scroll at phone width",
        pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2"))
    b.close()

chk("no javascript error on either page", not errs, errs[:3])
print("\n%d ok, %d FAILED" % (len(OK), len(BAD)))
for x in BAD:
    print("   FAILED: " + x)
sys.exit(1 if BAD else 0)
