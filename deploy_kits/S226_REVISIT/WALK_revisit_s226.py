"""S226_COUNT_SEARCH -- THE COUNTER'S SCREEN, DRIVEN.

Darpan is on the shelf, Amir is at the keyboard, and the count is HALF DONE.
This walk therefore does the one thing that matters: it seeds localStorage with
entries already made, reloads the new page over them, and checks nothing was
lost -- then drives the search the way a counter would use it.
"""
import os, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import WALK_readiness_s226 as R
from playwright.sync_api import sync_playwright

OK, BAD = [], []
def chk(n, c, d=""):
    (OK if c else BAD).append(n + (("  -- " + str(d)) if d and not c else ""))
    print(("  ok   " if c else "  FAIL ") + n + (("   " + str(d)) if d else ""))

R.DB = os.path.join(HERE, "_walk226c.db")
con = R.build()
R.fill(con)
# a shop-shaped item list, including the names that are typed five ways
for item, q, pk, ps in (("PRIME CAST 5\"", 45, "1*1", 1), ("BIO D3 MAX", 358, "1*15", 15),
                        ("LACTOVAX SYP 200ML", 5, "1*1", 1), ("MEG QCS", 684, "1*15", 15),
                        ("ALCOXIB 120", 13, "1*10", 10), ("TYRO BR", 700, "1*10", 10)):
    con.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,"
                "source,loaded_at) VALUES (?,?,?,?,?,?,?)",
                ("06-09-2026", item, q, pk, ps, "push_snapshot.py", "2026-09-06T09:00:59"))
con.commit()
app = R.app_for(con)
threading.Thread(target=lambda: app.run(port=8797, threaded=False), daemon=True).start()
time.sleep(1.5)
URL = "http://127.0.0.1:8797/finance/stock/page/count"

print("== S226_COUNT_SEARCH -- the counter's screen ==")
errs = []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 390, "height": 844})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text)
          if m.type == "error" and "Failed to load resource" not in m.text else None)

    # ---- a count already in progress, saved by the OLD page ----
    pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""() => localStorage.setItem("sanj-stock-live-v1", JSON.stringify({
        cby:"Darpan", eby:"Amir", bill:"A003425", billdate:"2026-09-06",
        e:{ "MEG QCS":{c:684,cby:"Darpan",eby:"Amir",at:"2026-09-06T10:30:00"},
            "TYRO BR":{c:690,cby:"Darpan",eby:"Amir",at:"2026-09-06T10:31:00"} }}));""")
    pg.reload(); pg.wait_for_timeout(700)
    pg.locator("#start").click(); pg.wait_for_timeout(500)
    chk("THE HALF-DONE COUNT SURVIVES the new page",
        pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('sanj-stock-live-v1')).e).length") == 2)
    txt = pg.inner_text("body")
    chk("it reopens on the counting screen, not the gate",
        not pg.locator("#count").evaluate("el => el.classList.contains('hide')"))
    chk("progress shows the two already counted", "2 / 6" in pg.inner_text("#prog"),
        pg.inner_text("#prog"))

    # ---- the search itself ----
    f = pg.locator("#find")
    chk("there is a search box, on the sticky bar", f.count() == 1)
    f.fill("d3")
    pg.wait_for_timeout(200)
    chk("three letters find the item", "BIO D3 MAX" in pg.inner_text("#list"),
        pg.inner_text("#list")[:60])
    chk("and only that item", pg.locator("#list .row").count() == 1,
        pg.locator("#list .row").count())
    chk("it says what it is showing", "1" in pg.inner_text("#findnote"),
        pg.inner_text("#findnote"))

    f.fill("primecast5")
    pg.wait_for_timeout(200)
    chk('SPACES AND THE INCH MARK DO NOT MATTER (primecast5 finds PRIME CAST 5")',
        'PRIME CAST 5"' in pg.inner_text("#list"), pg.inner_text("#list")[:60])

    f.fill("meg")
    pg.wait_for_timeout(200)
    chk("AN ALREADY-COUNTED ITEM IS STILL FINDABLE -- the whole point of a correction",
        "MEG QCS" in pg.inner_text("#list"), pg.inner_text("#list")[:60])

    # ---- OK, while searching ----
    f.fill("alcoxib"); pg.wait_for_timeout(200)
    pg.locator("#list .row .yes").first.click(); pg.wait_for_timeout(300)
    chk("OK saves the expected figure",
        pg.evaluate("JSON.parse(localStorage.getItem('sanj-stock-live-v1')).e['ALCOXIB 120'].c") == 13)
    chk("...and the box CLEARS ITSELF, ready for the next name Darpan calls",
        pg.locator("#find").input_value() == "", pg.locator("#find").input_value())
    chk("...and progress moved", "3 / 6" in pg.inner_text("#prog"), pg.inner_text("#prog"))

    # ---- Not OK, while searching ----
    f.fill("lacto"); pg.wait_for_timeout(200)
    pg.locator("#list .row .no").first.click(); pg.wait_for_timeout(300)
    chk("Not OK opens the entry box", pg.locator("#list .entry input").count() >= 1)
    pg.locator("#list .entry input").first.fill("3"); pg.wait_for_timeout(400)
    chk("the physical count is saved against the right item",
        pg.evaluate("(JSON.parse(localStorage.getItem('sanj-stock-live-v1')).e['LACTOVAX SYP 200ML']||{}).c") == 3,
        pg.evaluate("JSON.stringify(JSON.parse(localStorage.getItem('sanj-stock-live-v1')).e['LACTOVAX SYP 200ML'])"))

    # ---- S226: COMING BACK TO AN ITEM. The counter's own complaint:
    #      "they enter a quantity, more stock turns up, and when they revisit
    #      the item they do not see what they first entered."
    f.fill("bio"); pg.wait_for_timeout(250)
    pg.locator("#list .row .no").first.click(); pg.wait_for_timeout(300)
    pg.locator("#list .entry .qs").fill("20"); pg.locator("#list .entry .ql").fill("5")
    pg.wait_for_timeout(400)
    f.fill("meg"); pg.wait_for_timeout(250)
    f.fill("bio"); pg.wait_for_timeout(300)
    vals = pg.locator("#list .entry input").evaluate_all("e=>e.map(x=>x.value)")
    chk("REVISITING A COUNTED ITEM SHOWS WHAT WAS ENTERED", vals[:2] == ["20", "5"], vals)
    chk("...and the row says it without opening anything",
        "you counted 305" in pg.inner_text("#list .row"),
        pg.inner_text("#list .row").replace("\n", " | ")[:100])
    chk("...in strips and tablets, the convention",
        "20 strips 5 tablets" in pg.inner_text("#list .row"),
        pg.inner_text("#list .row").replace("\n", " | ")[:100])
    # more stock turns up: adjust, do not retype from nothing
    pg.locator("#list .entry .qs").fill("23"); pg.wait_for_timeout(400)
    chk("...and it can simply be adjusted when more stock turns up",
        pg.evaluate("JSON.parse(localStorage.getItem('sanj-stock-live-v1')).e['BIO D3 MAX'].c") == 350,
        pg.evaluate("JSON.stringify(JSON.parse(localStorage.getItem('sanj-stock-live-v1')).e['BIO D3 MAX'])"))
    # an item counted to EXACTLY Marg's figure must not go silent
    f.fill("alcoxib"); pg.wait_for_timeout(250)
    pg.locator("#list .row .yes").first.click(); pg.wait_for_timeout(300)
    f.fill("alcoxib"); pg.wait_for_timeout(300)
    chk("AN ITEM COUNTED AS 'OK' ALSO SHOWS ITS FIGURE ON RETURN",
        "you counted 13" in pg.inner_text("#list .row"),
        pg.inner_text("#list .row").replace("\n", " | ")[:100])
    chk("...with its boxes filled, not blank",
        pg.locator("#list .entry input").evaluate_all("e=>e.map(x=>x.value)")[:1] == ["1"],
        pg.locator("#list .entry input").evaluate_all("e=>e.map(x=>x.value)"))
    pg.locator("#findclear").click(); pg.wait_for_timeout(250)

    # ---- the chips still work when the box is empty ----
    pg.locator("#findclear").click(); pg.wait_for_timeout(250)
    chk("clearing brings the list back", pg.locator("#list .row").count() >= 1,
        pg.locator("#list .row").count())
    # THE CRASH. Every chip that can show a differing item used to blow the
    # stack and blank the list -- live, one tap from a counter who had just
    # marked his first item Not OK.
    for f_ in ("diff", "all", "stock", "nil"):
        pg.locator('#chips button[data-f="%s"]' % f_).click(); pg.wait_for_timeout(250)
        chk("chip '%s' renders instead of blanking" % f_,
            pg.locator("#list .row").count() >= 1 or "Nothing here" in pg.inner_text("#list"),
            pg.inner_text("#list")[:50])
    pg.locator('#chips button[data-f="diff"]').click(); pg.wait_for_timeout(300)
    dtxt = pg.inner_text("#list")
    chk("Differences shows BOTH mismatched items",
        "TYRO BR" in dtxt and "LACTOVAX" in dtxt, dtxt[:90])
    chk("a differing row opens its entry box already filled",
        pg.locator("#list .entry input").count() >= 1)
    chk("a search overrides the chip rather than fighting it",
        (f.fill("bio"), pg.wait_for_timeout(200), "BIO D3 MAX" in pg.inner_text("#list"))[2])

    chk("no sideways scroll at phone width",
        pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2"))
    b.close()

chk("no javascript error anywhere in that", not errs, errs[:3])
print("\n%d ok, %d FAILED" % (len(OK), len(BAD)))
for x in BAD: print("   FAILED: " + x)
sys.exit(1 if BAD else 0)
