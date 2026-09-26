#!/usr/bin/env python3
"""walk_s413.py -- kit S413_SLIP_PICKER. The kit's slip_log.py over a SCRATCH COPY of the live finance.db, on the walk's
own books (OPD from 90001, X-ray/Proc from 90501), clock pinned, served on a local port and driven in a real phone-sized
browser (Chromium via Playwright when it is there; otherwise the test client alone, and the browser part is reported
as skipped, never as passed). Checks the owner's asks of 26-Sep-2026: one search box over X-rays and procedures;
"SBK" and "BK" find the right lines; full names with prices; side and chhoot on a chosen line; the running total;
the posted form saves the same rows as before; the room lists each line with its price. The live S401 file is the
negative control (it has no search box). Prints counts and walk slip numbers only.
Usage: python3 walk_s413.py <kit slip_log.py> <live slip_log.py> <scratch db A> <scratch db B>"""
import datetime as dt, importlib.util, os, sqlite3, sys, threading, time
new_p, live_p, dba, dbb = [os.path.abspath(x) for x in sys.argv[1:5]]
for d in (dba, dbb):
    assert "walk" in d or "scratch" in d or d.startswith("/tmp"), "refusing a non-scratch database"
NOW = dt.datetime.now().replace(microsecond=0, hour=11, minute=0, second=0)
os.environ["SLIP_NOW"] = NOW.isoformat()
os.environ.setdefault("FINANCE_CRON_TOKEN", "walk-s413-token")
N = [0]


def ok(c, label, got=None):
    N[0] += 1
    if not c:
        print("WALK RED %d: %s %s" % (N[0], label, "" if got is None else str(got)[:300])); sys.exit(1)


from flask import Flask
USER = {"u": {"user": "bhati", "roles": ["maker"]}}


def build(path, tag, dbp):
    sp = importlib.util.spec_from_file_location("slip_log_" + tag, path); m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    a = Flask("w" + tag)

    def dbg():
        c = sqlite3.connect(dbp); c.row_factory = sqlite3.Row; return c

    def req(*roles, **kw):
        u = USER["u"]
        if not set(u["roles"]) & set(roles):
            from flask import jsonify
            return None, (jsonify(ok=False, error="not_permitted"), 403)
        return u, None
    m.init(a, dbg, req, None, unit="slips")
    return a, m


def prep(dbp, mod):
    c = sqlite3.connect(dbp); c.row_factory = sqlite3.Row
    mod.ensure(c)
    c.execute("DELETE FROM slip WHERE slip_no BETWEEN 90001 AND 90600")
    c.execute("UPDATE slip_book SET first_no=90001, last_no=90100, start_no=90001 WHERE series='opd'")
    c.execute("UPDATE slip_book SET first_no=90501, last_no=90600, start_no=90501 WHERE series='xp'")
    c.commit()
    return c


A, S = build(new_p, "new", dba)
B, L = build(live_p, "live", dbb)
ca, cb = A.test_client(), B.test_client()
con = prep(dba, S); conb = prep(dbb, L)
cid = con.execute("SELECT clinic_id FROM patient_ref WHERE clinic_id GLOB '[0-9]*' ORDER BY id DESC LIMIT 1").fetchone()[0]
xr, pr = S.services(con)
ok(len(xr) > 5 and len(pr) > 5, "the rate page has X-rays and procedures (%d / %d)" % (len(xr), len(pr)))
sbk = [p for p in pr if p["name"].upper().startswith("SBK")]
ok(len(sbk) >= 1, "an SBK line exists on the rate page")
bk_names = [p["name"] for p in pr if "B/K" in p["name"].upper() or "BK" in p["name"].upper().replace("/", "")]
ok(len(bk_names) >= 3, "B/K, SBK and HBK lines exist", bk_names)
knee = [x for x in xr if "knee" in x["name"].lower()]
ok(knee, "a knee X-ray exists")

# --- the server side
ok({r.rule for r in A.url_map.iter_rules()} == {r.rule for r in B.url_map.iter_rules()}, "the same doors as S401")
h = ca.get("/finance/slips?s=xp").get_data(as_text=True)
ok('class="pks"' in h and 'class="pkdata"' in h, "the form carries the picker and its data")
ok('class="svc"' not in h and "+ aur X-ray" not in h, "the old drop-downs are gone")
hb = cb.get("/finance/slips?s=xp").get_data(as_text=True)
ok('class="pks"' not in hb and 'class="svc"' in hb, "control: S401 still has the drop-downs")
import json
data = json.loads(h.split('class="pkdata">')[1].split("</script>")[0])
ok(len(data) == len(xr) + len(pr), "every rate line is in the picker's data (%d)" % len(data))
ok(all(d["n"] and "a" in d for d in data), "each line carries its full name and its search words")
# the same fields as before still save
r = ca.post("/finance/slips/save", data={"series": "xp", "slip_no": "90501", "clinic_id": cid, "xray0": str(knee[0]["id"]),
                                         "xray0_side": "L", "proc0": str(sbk[0]["id"]), "proc0_disc": "100"})
ok(r.status_code == 303 and "ok=" in r.headers["Location"], "posting the same fields saves", r.headers.get("Location"))
sid = con.execute("SELECT id FROM slip WHERE series='xp' AND slip_no=90501").fetchone()[0]
its = [dict(x) for x in con.execute("SELECT * FROM slip_item WHERE slip_id=? ORDER BY sort", (sid,))]
ok(len(its) == 2 and its[0]["side"] == "L" and its[1]["discount_p"] == 10000, "two lines, side L, chhoot 100", its)
h = ca.get("/finance/slips?s=room").get_data(as_text=True)
ok('class="il"' in h and S._esc(knee[0]["name"]) in h and S._esc(sbk[0]["name"]) in h and "chhoot" in h, "the room lists each line whole with its price")
ok(h.count('class="il"') >= 2, "one line per item in the room")

# --- the browser: the picker as the staff see it
browser_done = False
try:
    from playwright.sync_api import sync_playwright
    from werkzeug.serving import make_server
    srv = make_server("127.0.0.1", 0, A); port = srv.socket.getsockname()[1]
    th = threading.Thread(target=srv.serve_forever, daemon=True); th.start(); time.sleep(0.5)
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 390, "height": 780})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("http://127.0.0.1:%d/finance/slips?s=xp" % port)
        pg.wait_for_selector(".pks")
        ok(pg.locator(".pkc button").count() >= 4, "most-used lines are on screen before typing (%d)" % pg.locator(".pkc button").count())
        ok(pg.locator(".pkc button em").first.inner_text().startswith("₹") or "rate" in pg.locator(".pkc button em").first.inner_text(),
           "each button shows its price")
        pg.fill(".pks", "SBK"); pg.wait_for_timeout(300)
        names = [t for t in pg.locator(".pkr button > span").all_inner_texts()]
        ok(names and all("SBK" in n.upper() for n in names), "SBK finds only the SBK lines", names)
        pg.fill(".pks", "BK"); pg.wait_for_timeout(300)
        names = " | ".join(pg.locator(".pkr button").all_inner_texts()).upper()
        ok("B/K" in names and "SBK" in names and "HBK" in names, "BK finds B/K, SBK and HBK", names[:200])
        pg.fill(".pks", "knee"); pg.wait_for_timeout(300)
        names = pg.locator(".pkr button").all_inner_texts()
        ok(names and all("KNEE" in n.upper() for n in names) and any("X-RAY" in n.upper() for n in names), "knee finds knee X-rays", names)
        pg.fill(".pks", "bk slab"); pg.wait_for_timeout(300)
        names = " | ".join(pg.locator(".pkr button").all_inner_texts()).upper()
        ok("SLAB" in names and "CAST" not in names.split("|")[0], "two words narrow it: bk slab", names[:200])
        pg.fill(".pks", "ili"); pg.wait_for_timeout(300)
        ok(all("ILI" in n.upper() for n in pg.locator(".pkr button").all_inner_texts()), "ili finds the injections")
        pg.fill(".pks", "zzzz"); pg.wait_for_timeout(300)
        ok(pg.locator(".pkr .none").count() == 1, "nothing found is said in words")
        # choose: knee X-ray (side L) + SBK slab (chhoot 100) via the search
        pg.fill(".pks", "knee ap"); pg.wait_for_timeout(300); pg.locator(".pkr button").first.click()
        ok(pg.locator(".pkl .it").count() == 1, "a tapped line lands in the chosen list")
        full = pg.locator(".pkl .it .nm").first.inner_text()
        ok("Knee" in full and "₹" in full, "the chosen line shows its full name and price", full)
        ok(pg.locator(".pks").input_value() == "", "the search box clears after a tap")
        pg.locator(".pkl .it select.side").first.select_option("L")
        pg.fill(".pks", "sbk slab"); pg.wait_for_timeout(300); pg.locator(".pkr button").first.click()
        ok(pg.locator(".pkl .it").count() == 2, "second line chosen")
        pg.locator(".pkl .it input.disc").first.fill("100"); pg.wait_for_timeout(100)
        tot = pg.locator(".pktot").inner_text()
        ok(tot.startswith("Kul:") and "₹" in tot, "the running total shows", tot)
        hid = {e.get_attribute("name"): e.get_attribute("value") for e in pg.locator(".pkh input").all()}
        ok(hid.get("xray0") == str(knee[0]["id"]) or hid.get("xray0") in {str(x["id"]) for x in knee}, "hidden xray0 carries the id", hid)
        ok(hid.get("xray0_side") == "L" and hid.get("proc0_disc") == "100" and "proc0" in hid, "side and chhoot are posted", hid)
        # remove one, add via a chip, then save
        pg.locator(".pkl .it .x").first.click()
        ok(pg.locator(".pkl .it").count() == 1, "the cross removes a line")
        pg.locator(".pkc button").first.click()
        ok(pg.locator(".pkl .it").count() == 2, "a most-used button adds a line")
        pg.fill('input[name="clinic_id"]', cid); pg.wait_for_timeout(500)
        pg.locator("form.slipf button.go").click(); pg.wait_for_load_state()
        ok("save ho gayi" in pg.content(), "saved from the browser")
        row = con.execute("SELECT id FROM slip WHERE series='xp' AND slip_no=90502").fetchone()
        ok(row is not None, "the browser's parchi is in the table")
        its = [dict(x) for x in con.execute("SELECT * FROM slip_item WHERE slip_id=? ORDER BY sort", (row[0],))]
        ok(len(its) == 2 and any(i["discount_p"] == 10000 for i in its), "its two lines and the chhoot are saved", its)
        # an empty form is stopped on the phone
        pg.goto("http://127.0.0.1:%d/finance/slips?s=xp" % port); pg.wait_for_selector(".pks")
        pg.on("dialog", lambda d: d.dismiss())
        pg.fill('input[name="clinic_id"]', cid); pg.locator("form.slipf button.go").click(); pg.wait_for_timeout(300)
        ok(con.execute("SELECT COUNT(*) FROM slip WHERE series='xp' AND slip_no=90503").fetchone()[0] == 0, "an empty parchi is not posted")
        # "other" with a typed name
        pg.fill(".pks", "other"); pg.wait_for_timeout(300); pg.locator(".pkr button").first.click()
        ok(pg.locator(".pkl .it input.oth").count() == 1, "Other asks for a name")
        ok(not errs, "no script error on the page", errs)
        br.close()
    srv.shutdown()
    browser_done = True
except ImportError:
    pass

# --- every screen, every role
for who, rl in (("bhati", "maker"), ("alisha", "maker"), ("awdhesh", "maker"), ("shavez", "maker"), ("manoj", "checker"), ("sukhveer", "viewer")):
    USER["u"] = {"user": who, "roles": [rl]}
    for pth in ("/finance/slips", "/finance/slips?s=xp", "/finance/slips?s=room", "/finance/slips?s=list", "/finance/slips?s=late",
                "/finance/slips?s=all", "/finance/slips/pending", "/finance/slips/report"):
        ok(ca.get(pth).status_code in (200, 302, 303, 403), "GET %s as %s" % (pth.split("?")[0], who))

for c in (con, conb):
    c.execute("DELETE FROM slip WHERE slip_no BETWEEN 90001 AND 90600"); c.commit()
print("WALK OK %d/%d checks%s" % (N[0], N[0], "" if browser_done else " (browser part SKIPPED: no Playwright here)"))
