"""proof_page_s761.py -- kit S761: the whole hub page drawn in Chromium (Playwright), every door answered by made-up fixture JSON (no patient
data, no server). Run where Playwright is (the cloud workspace or manojz), never needed on the box.
  python3 proof_page_s761.py <finance_approvals.html> <needs-you JSON from walk_s761 (needs761.json)>
Prints one line per check and 'PAGE S761: N check(s) failed'."""
import json, sys
from playwright.sync_api import sync_playwright
page_html = open(sys.argv[1], encoding="utf-8").read()
NEEDS = json.load(open(sys.argv[2], encoding="utf-8"))
day = lambda d, ap, cash: dict(date=d, day=d[8:10] + "-" + ["Oct", "Nov"][int(d[5:7]) - 10], weekday="Mon", status="approved" if ap else "submitted", approved=ap,
                               sale="10,000", upi="5,000", without_cash="0", cash=cash, cash_p=100000, elsewhere=None, marg_ok=None, marg=None, marg_bills=None,
                               went="to the pool (approved)" if ap else "in the drawer", logged=False, log=None, banked=[], waiting_approval=not ap, bhati=None)
FIX = {
    "/finance/sanjeevni/api/needs-you": NEEDS,
    "/finance/sanjeevni/api/days": dict(ok=True, anchor="2026-08-17", days=[day("2026-10-30", True, "1,000"), day("2026-10-31", True, "1,000"),
                                        day("2026-11-03", False, "6,522"), day("2026-11-04", False, "20,034")],
                                        position=dict(drawer="24,700", pool="3,50,641", with_doctors="3,50,641", bank="8,00,000")),
    "/finance/api/cash-position": dict(ok=True, basis="sanjeevni_cash", unbanked="3,75,341", drawer="24,700", reserve="3,50,641", bank_deposited="23,70,600",
                                       bank_count=4, last_bank_date="2026-10-09", days=[dict(date="2026-11-04", drawer="24,700", unbanked="24,700")],
                                       bank_deposits=[dict(date="2026-10-09", amount="2,00,000", ref="WALK")], reserve_detail=[], waiting_days=["2026-11-03", "2026-11-04"], as_of="07-Nov"),
    "/finance/sanjeevni/api/bank": dict(ok=True, month="2026-11", upi=[], upi_total="67,104", upi_days=6, banked_total="8,00,000",
                                        icici=dict(holds="3,71,066", anchored=True, base="1,00,000", since="30-Sep", credited="2,71,066", out="0", upto="07-Nov", short="", source="WALK"),
                                        yesbank=dict(holds="0", base="0", as_on="31-Oct", added="0", taken="0", anchored=True),
                                        statement=dict(from_="2026-10-01", to="2026-10-31", from_day="01-Oct", to_day="31-Oct", opening="0", closing="0", loaded_at="2026-11-02 10:00", days_since=9),
                                        deposits=[dict(id=1, date="2026-10-09", day="09-Oct", amount="2,00,000", place="", source="pool", status="ok", text="confirmed in the statement (09-Oct)")],
                                        transfers=[dict(id=2, date="2026-10-20", day="20-Oct", amount="50,000", frm="ICICI Sanjeevni", to="Yes Bank Sanjeevni", frm_key="icici", to_key="yesbank",
                                                        ref="", leaves=False, status="ok", text="confirmed in the Yes Bank statement")], accounts={}),
    "/finance/sanjeevni/api/months": dict(ok=True, months=[]),
    "/finance/sanjeevni/expiry/api/count": dict(ok=True, n=7, expired=1, stops=6, stops_on="1-Dec", title="1 expired · 6 stop selling on 1-Dec"),
}
res = []
def check(n, ok, note=""):
    res.append((n, bool(ok), str(note)[:300]))
with sync_playwright() as p:
    b = p.chromium.launch()
    for width in (1280, 412):
        ctx = b.new_context(viewport=dict(width=width, height=900))
        pg = ctx.new_page()
        errs, cons = [], []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: cons.append(m.text) if m.type == "error" else None)
        def route(r):
            u = r.request.url.split("://", 1)[1].split("/", 1)[1]
            path = "/" + u.split("?")[0].split("#")[0]
            if path == "/finance/approvals":
                return r.fulfill(status=200, content_type="text/html; charset=utf-8", body=page_html)
            if path in FIX:
                return r.fulfill(status=200, content_type="application/json", body=json.dumps(FIX[path], ensure_ascii=False))
            if path.startswith("/finance/") and ("/api/" in path or path.endswith("/state") or path.endswith("/summary")):
                return r.fulfill(status=200, content_type="application/json", body='{"ok": false, "error": "walk"}')
            return r.fulfill(status=404, content_type="text/plain", body="not in the walk")
        pg.route("**/*", route)
        pg.goto("https://hub.test/finance/approvals")
        pg.wait_for_timeout(2500)
        W = "%d px: " % width
        check(W + "no script error on the page", not errs, errs[:3])
        nh = pg.inner_text("#needsHead")
        nt = pg.inner_text("#needs")
        if "groups" not in NEEDS:   # the fail-soft answer (no groups): the old flat list, one line per line, no header count
            check(W + "no groups in the answer: the old flat list (%d lines), no header count" % len(NEEDS["lines"]),
                  nh.strip() == "" and pg.locator("#needs > li").count() == len(NEEDS["lines"]))
        else:
            check(W + "Needs you header '%s'" % nh.strip(), nh.strip() == "— %d items in %d groups" % (NEEDS["n_items"], NEEDS["n_groups"]))
            check(W + "Needs you drawn grouped: Days to approve first with 'Open the days', information last", nt.startswith("2") and "Days to approve" in nt.split("\n")[0]
                  and "Open the days" in nt and "For your information" in nt.strip().split("\n")[-1], nt[:160].replace("\n", " | "))
        if "groups" in NEEDS:
            pg.locator("#needs li.grp summary", has_text="Arrived but not in Marg").click(); pg.wait_for_timeout(200)
            vn = pg.locator("#needs .vnote").first
            check(W + "Arrived: the other-size note is visible text on the line (not a hover)", vn.is_visible() and "carried" in vn.inner_text(), vn.inner_text() if vn.count() else "")
            hp = {}
            for nm, ans in (("empty", dict(ok=True, lines=[], count=0)), ("error", dict(ok=False, error="walk")), ("flat", {k: v for k, v in NEEDS.items() if k not in ("groups", "n_items", "n_groups", "n_info")}),
                            ("groups", NEEDS)):
                FIX["/finance/sanjeevni/api/needs-you"] = ans
                pg.evaluate("document.getElementById('needsHead').textContent='STALE'; loadNeeds()"); pg.wait_for_timeout(400)
                hp[nm] = pg.inner_text("#needsHead").strip()
            check(W + "the header on every path: empty / error / flat -> none, groups -> its count", hp["empty"] == hp["error"] == hp["flat"] == "" and hp["groups"].startswith("— %d items" % NEEDS["n_items"]), hp)
        check(W + "Cash: four figures, no day count of its own", pg.locator("#cashPos .cb-box").count() == 4 and "awaiting" not in pg.inner_text("#cashPos"), pg.inner_text("#cashPos")[:200])
        pg.locator("#cashPos .cb-box").nth(1).click(); pg.wait_for_timeout(200)
        check(W + "Cash: a tap on the drawer opens its detail", pg.is_visible("#cashDet") and "24,700" in pg.inner_text("#cashDet"))
        bt = pg.inner_text("#bank")
        check(W + "Bank: '1 deposit ✓ · 1 transfer ✓ — all confirmed', 'pool deposits recorded here', the deposits fold closed", "1 deposit ✓ · 1 transfer ✓ — all confirmed" in bt
              and "pool deposits recorded here" in pg.content() and not pg.locator("#bank details.mon").first.get_attribute("open") is not None, bt[:200].replace("\n", " | "))
        dk = pg.locator("#days details.mon")
        check(W + "Days: November open (days to approve), October closed 'all approved ✓'; the position line names no bank", dk.count() == 2 and dk.nth(0).get_attribute("open") is not None
              and dk.nth(1).get_attribute("open") is None and "all approved ✓" in dk.nth(1).inner_text() and "banked" not in pg.inner_text("#days"))
        check(W + "the Orders tab and the old strip gone", pg.locator('nav.tabs a[href="#porders"]').count() == 1 and pg.locator("#linksCard").count() == 0)
        pg.click("#gotoBtn"); pg.wait_for_timeout(600)
        vis = pg.is_visible("#gotoPanel")
        n = pg.locator("#gotoPanel a").count()
        ck = pg.get_attribute("#gotoCheck", "href")
        check(W + "Go to opens: %d links, the purchase check at last month (%s), the expiry count 7" % (n, ck), vis and n == 38 and ck.startswith("/finance/purchase/page/check?month=")
              and pg.inner_text("#gotoExp").strip() == "7")
        sw = pg.evaluate("document.scrollingElement.scrollWidth")
        check(W + "the open panel does not push the page sideways (scroll width %d)" % sw, sw <= width + 1)
        pg.keyboard.press("Escape"); pg.wait_for_timeout(200)
        check(W + "Escape closes the panel", not pg.is_visible("#gotoPanel"))
        pg.click("#gotoBtn"); pg.wait_for_timeout(200); pg.mouse.click(5, 880); pg.wait_for_timeout(200)
        check(W + "a tap outside closes it", not pg.is_visible("#gotoPanel"))
        for cid in ("needsCard", "daysCard", "cashPosCard", "bankCard", "returnsCard", "porders", "monthsCard", "checksCard"):
            check(W + "card #%s present and drawn" % cid, pg.locator("#" + cid).count() == 1)
        if width == 1280:
            y1 = pg.locator("#cashPosCard").bounding_box(); y2 = pg.locator("#bankCard").bounding_box()
            check(W + "Cash and Bank side by side", abs(y1["y"] - y2["y"]) < 4 and y2["x"] > y1["x"] + 100, (y1, y2))
        else:
            y1 = pg.locator("#cashPosCard").bounding_box(); y2 = pg.locator("#bankCard").bounding_box()
            check(W + "Cash above Bank on the phone", y2["y"] > y1["y"] + 50, (y1, y2))
        ctx.close()
    b.close()
bad = [r for r in res if not r[1]]
for n_, ok, note in res:
    print("  %s  %s%s" % ("ok " if ok else "RED", n_, "" if ok else "  -- " + note))
print("PAGE S761: %d check(s) failed" % len(bad))
