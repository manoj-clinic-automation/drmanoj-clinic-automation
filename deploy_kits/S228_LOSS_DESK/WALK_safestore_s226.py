"""S226 SAFE STORE -- the two ways a morning's counting could vanish in silence.

A count lives in one browser. These are the failure modes that used to be quiet:
a browser that refuses to store, and a stored record that cannot be read back.
"""
import os, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import WALK_readiness_s226 as R
from playwright.sync_api import sync_playwright
OK, BAD = [], []
def chk(n, c, d=""):
    (OK if c else BAD).append(n + (("  -- " + str(d)) if d and not c else ""))
    print(("  ok   " if c else "  FAIL ") + n + (("   " + str(d)) if d else ""))

R.DB = os.path.join(HERE, "_walk_ss.db"); con = R.build(); R.fill(con)
for item, q, pk, ps in (("BIO D3 MAX", 358, "1*15", 15), ("TYRO BR", 700, "1*10", 10)):
    con.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,"
                "source,loaded_at) VALUES (?,?,?,?,?,?,?)",
                ("06-09-2026", item, q, pk, ps, "p", "2026-09-06T09:00:59"))
con.commit(); app = R.app_for(con)
threading.Thread(target=lambda: app.run(port=8809, threaded=False), daemon=True).start()
time.sleep(1.5)
URL = "http://127.0.0.1:8809/finance/stock/page/count"
SEED = ("()=>localStorage.setItem('sanj-stock-live-v1',JSON.stringify("
        "{cby:'Darpan',eby:'Amir',bill:'A1',billdate:'2026-09-06',"
        "e:{'BIO D3 MAX':{c:350,st:23,lo:5,at:'2026-09-06T11:00:00'}}}))")

print("== S226 SAFE STORE ==")
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")

    # ---------------------------------------- 1 a browser that refuses to save
    pg = b.new_page(viewport={"width": 390, "height": 844}); pg.on("dialog", lambda d: d.accept())
    pg.goto(URL); pg.wait_for_timeout(300); pg.evaluate(SEED)
    pg.reload(); pg.wait_for_timeout(500); pg.locator("#start").click(); pg.wait_for_timeout(300)
    chk("normal working: no alarm on screen", pg.locator("#storebar").count() == 0)
    pg.evaluate("""()=>{ const o=localStorage.setItem.bind(localStorage);
        localStorage.setItem=function(k,v){ if(k==='sanj-stock-live-v1') throw new Error('QuotaExceeded');
                                            return o(k,v); }; }""")
    pg.locator("#find").fill("tyro"); pg.wait_for_timeout(250)
    pg.locator("#list .row .yes").first.click(); pg.wait_for_timeout(500)
    bar = pg.inner_text("#storebar") if pg.locator("#storebar").count() else ""
    chk("A BROWSER THAT WILL NOT SAVE SAYS SO, LOUDLY", "NOT SAVING" in bar.upper(), bar[:90])
    chk("...and tells them not to reload", "not reload" in bar.lower(), bar[:140])
    chk("...and to stop and tell the doctor", "doctor" in bar.lower(), bar[:140])
    pg.close()

    # ---------------------------------------- 2 a record that cannot be read
    pg = b.new_page(viewport={"width": 390, "height": 844}); pg.on("dialog", lambda d: d.accept())
    pg.goto(URL); pg.wait_for_timeout(300); pg.evaluate(SEED)
    pg.reload(); pg.wait_for_timeout(500); pg.locator("#start").click(); pg.wait_for_timeout(300)
    chk("a good copy is kept beside the live one",
        pg.evaluate("!!localStorage.getItem('sanj-stock-live-v1.bak')"))
    pg.evaluate("""()=>localStorage.setItem('sanj-stock-live-v1', '{"e":{"BIO D3 M')""")  # truncated
    pg.reload(); pg.wait_for_timeout(600); pg.locator("#start").click(); pg.wait_for_timeout(400)
    bar = pg.inner_text("#storebar") if pg.locator("#storebar").count() else ""
    chk("A DAMAGED RECORD IS RECOVERED FROM THE BACKUP", "RECOVERED" in bar.upper(), bar[:100])
    # (the counted item is not in the "To do" list, by design -- look at the record)
    chk("...and the counted figure is back, intact",
        pg.evaluate("(JSON.parse(localStorage.getItem('sanj-stock-live-v1')).e['BIO D3 MAX']||{}).c") == 350,
        pg.evaluate("JSON.stringify(JSON.parse(localStorage.getItem('sanj-stock-live-v1')).e)"))
    chk("...and the progress counter proves it", "1 / 2" in pg.inner_text("#prog"),
        pg.inner_text("#prog"))
    pg.locator("#find").fill("bio"); pg.wait_for_timeout(300)
    chk("...and it is there when searched for",
        "you counted 350" in pg.inner_text("#list"), pg.inner_text("#list")[:80])
    chk("...and the unreadable bytes were set aside, not thrown away",
        pg.evaluate("Object.keys(localStorage).some(k=>k.indexOf('.rescue.')>0)"))
    pg.close()

    # ---------------------------------------- 3 both gone: never start blank quietly
    pg = b.new_page(viewport={"width": 390, "height": 844}); pg.on("dialog", lambda d: d.accept())
    pg.goto(URL); pg.wait_for_timeout(300)
    pg.evaluate("""()=>{ localStorage.clear();
        localStorage.setItem('sanj-stock-live-v1','{not json at all'); }""")
    pg.reload(); pg.wait_for_timeout(600)
    bar = pg.inner_text("#storebar") if pg.locator("#storebar").count() else ""
    chk("the warning is on the GATE, before anyone can count over the top",
        bar != "" and pg.locator("#gate").is_visible(), (bar[:60], "gate visible"))
    chk("NOTHING READABLE ANYWHERE: it says so instead of starting blank",
        "COULD NOT BE READ" in bar.upper() or "set aside" in bar.lower(), bar[:120] or "(no banner)")
    chk("...and those bytes were set aside too",
        pg.evaluate("Object.keys(localStorage).some(k=>k.indexOf('.rescue.')>0)"))
    b.close()

print("\n%d ok, %d FAILED" % (len(OK), len(BAD)))
for x in BAD: print("   FAILED: " + x)
sys.exit(1 if BAD else 0)
