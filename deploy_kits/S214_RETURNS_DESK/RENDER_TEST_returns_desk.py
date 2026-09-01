#!/usr/bin/env python3
"""RENDER_TEST -- v6: the page opened in a REAL browser (headless chromium),
APIs mocked, and the counter flow driven by actual clicks.

WHY THIS FILE EXISTS: v5 shipped with node-syntax-clean JavaScript and 45
green server-side checks -- and the owner found taps dead on his phone. The
S209 lesson, re-learned at the desk: a page is not proven until a browser
has clicked it. This test now gates every desk page change.

Runs in the build sandbox (needs playwright + chromium); NOT part of the VPS
install. Asserts: patient search -> pick -> items render (A00 prefix
stripped, strip-rate with pack word, bill qty + discount inline) -> tap
opens a BLANK qty box -> confirm adds with the medicine's own counting word
-> bottom bar shows the live net total -> step 3 conversion line -> cart
number boxes blank on focus -> zero page errors.
"""
import sys

from playwright.sync_api import sync_playwright

HTML = open(__file__.replace("RENDER_TEST_returns_desk.py",
                             "returns_desk.html")).read() \
    .replace("__DESK_USER__", '"alisha"')
ITEMS = [dict(item_key="k1", item_name="GEMCAL XT TABLETS", bought_units=20,
              last_date="2026-08-12", last_expiry="2027-05", pack_n=10,
              unit_p=1701, unit_net_p=1531, discounted=True, n_bills=2,
              bills=[dict(bill_no="A003238", date="2026-08-12", units=20,
                          disc_pct=10)],
              last_expired=False, unreadable_qty=False)]


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        base = "http://desk.test/finance/returns/desk"
        pg.route(base, lambda r: r.fulfill(content_type="text/html", body=HTML))
        pg.route("**/api/slips*", lambda r: r.fulfill(json=dict(ok=True, slips=[])))
        pg.route("**/api/search*", lambda r: r.fulfill(json=dict(ok=True,
                 patients=[dict(id=16, name="RAM TEST", clinic_id="C7591",
                                last4="1234")])))
        pg.route("**/api/items*", lambda r: r.fulfill(json=dict(ok=True,
                 items=ITEMS)))
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(base)
        pg.fill("#q", "RAM"); pg.wait_for_selector("#plist .item")
        pg.click("#plist .item"); pg.wait_for_selector("#ilist .item")
        body = pg.inner_text("#ilist")
        assert "3238" in body and "A003238" not in body
        assert "10%" in body and "पत्ता" in body and "गोली" in body
        pg.click("#ilist .item"); pg.wait_for_selector("input[id^=qb_]")
        assert pg.input_value("input[id^=qb_]") == ""
        pg.fill("input[id^=qb_]", "15"); pg.click(".okb")
        pg.wait_for_selector(".tag.sel")
        assert "15 गोली" in pg.inner_text("#ilist")
        assert "net" in pg.inner_text("#barTxt")
        # v8: qty cap -- billed item bought 20, typing 50 is refused with guidance
        pg.click("#ilist .item")            # remove (was selected)
        pg.wait_for_timeout(100)
        pg.click("#ilist .item")            # re-open qty box
        pg.wait_for_selector("input[id^=qb_]")
        pg.fill("input[id^=qb_]", "50")
        pg.click(".okb")
        assert pg.input_value("input[id^=qb_]") == "", "cap did not clear the box"
        ph = pg.get_attribute("input[id^=qb_]", "placeholder")
        assert "20" in ph, "cap guidance missing: " + str(ph)
        pg.fill("input[id^=qb_]", "15"); pg.click(".okb")
        pg.wait_for_selector(".tag.sel")
        # selections panel edit (v7) still present
        assert "15 गोली" in pg.inner_text("#sellist")
        pg.click("#barBtn")
        assert "1 पत्ता + 5 गोली" in pg.inner_text("#cart")
        assert "medical sales counter" in pg.inner_text("#p3"), "counter note missing"
        assert pg.locator("#mCash").count() == 0, "money buttons should be gone"
        pg.focus("#cart input[type=number]")
        assert pg.input_value("#cart input[type=number]") == ""
        # v7 panel edit
        pg.click("#st2")
        pg.click("#sellist .qty button")            # minus
        assert "14 गोली" in pg.inner_text("#sellist"), pg.inner_text("#sellist")
        # qty in the bill line is visually distinct (bold ink, not dim)
        assert pg.locator("#ilist .sub b").count() >= 1, "inline qty not distinct"
        assert errs == [], errs
        print("RENDER TEST PASS -- browser-driven, zero page errors")
        b.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
