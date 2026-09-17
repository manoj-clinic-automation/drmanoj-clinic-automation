#!/usr/bin/env python3
"""selftest_s292.py -- proves S292_DESK_PAIRS offline: bytes (anchors, refusal,
idempotence, node --check) and behaviour (headless Chromium over a mocked report
with real-shaped same-salt pairs): the over card no longer dumps every pair into its
sentence; it lists each of ITS items with its own partner; the toggle reveals all
pairs one per line; a real-loss item card names its partner; nothing else moved and
no console error. The untouched page (post-S288) is the control.
    python3 -B selftest_s292.py --live stock_desk.html.live
"""
import argparse, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import patch_desk_pairs_s292 as P  # noqa: E402
LIVE_MD5 = "16b9a234b71150b19c8d2ef883eb5f08"; FAILS = []
def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else "  -- " + str(detail)))
    if not ok: FAILS.append(name)
def md5(p): return hashlib.md5(io.open(p, "rb").read()).hexdigest()
def fixture():
    def d(item, lane, diff, word=None):
        return dict(item=item, packing="1x10", pack=10, marg=50, counted=50 + diff, diff=diff,
                    mrp_p=diff * 250, cost_p=diff * 200, mrp_source="sale", lane=lane, kind=None, word=word,
                    why="test", sold_fy=120, loose_fy=0, last_sale="2026-09-10", last_purchase="2026-08-30",
                    answer=None, needs_owner=False, lookups=[])
    pairs = [dict(salt="ETORICOXIB 90", over=[dict(item="PARI CR 12.5", diff=183, pack=10)], short=[dict(item="ETOZOX 90", diff=-469, pack=10)]),
             dict(salt="ETORICOXIB 60", over=[dict(item="INTACOXIA-60", diff=484, pack=10)], short=[dict(item="ETOBONE 60", diff=-8, pack=10)]),
             dict(salt="CALCIUM + CALCITRIOL", over=[dict(item="ZIBON EXTRA", diff=177, pack=10)], short=[dict(item="GEMCAL XT TABLETS", diff=-106, pack=10)])]
    return dict(ok=True, count_id=1, day="06-09-2026", totals=dict(written_off=0, pursue=0, parked=0, explained=0, recount=0, bill=0, marg_fix=0, open=5),
                mismatch=dict(mrp_short_p=9025324, mrp_over_p=2576057),
                differences=[d("PARI CR 12.5", "over", 183), d("INTACOXIA-60", "over", 484), d("LONELY OVER", "over", 3),
                             d("ETOZOX 90", "loss", -469), d("PLAIN LOSS", "loss", -5)],
                dead_matched=[], pairs=pairs, links=dict(amir="/a", loss_page="/l", amir_page="/a"))
def drive(path, label, shot=None):
    from playwright.sync_api import sync_playwright
    html = io.open(path, "r", encoding="utf-8").read().replace("/*__BOOT__*/", 'window.BOOT={count_id:1,user:"manoj",checker:true};')
    fx = fixture(); out = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport=dict(width=640, height=1100), color_scheme="dark")
        pg.on("console", lambda m: out.setdefault("console", []).append(m.text) if m.type == "error" else None)
        def route(r):
            u = r.request.url
            if u.endswith("/page/desk"): r.fulfill(status=200, content_type="text/html", body=html)
            elif "/api/pad/report/" in u: r.fulfill(status=200, content_type="application/json", body=json.dumps(fx))
            else: r.fulfill(status=204, body="")
        pg.route("**/*", route); pg.goto("http://desk.test/finance/stock/page/desk")
        pg.wait_for_function("document.querySelector('#card .card') !== null")
        out["over_why"] = pg.inner_text("#card .card .why")
        out["over_rows"] = pg.eval_on_selector_all("#card .card .pairs .pr", "els=>els.map(e=>e.innerText)")
        out["has_more"] = pg.query_selector("#card .pairs button[data-more]") is not None
        if out["has_more"]:
            out["all_hidden_before"] = pg.eval_on_selector("#card .pairs .all", "e=>e.hidden")
            pg.click("#card .pairs button[data-more]"); pg.wait_for_timeout(100)
            out["all_hidden_after"] = pg.eval_on_selector("#card .pairs .all", "e=>e.hidden")
            out["all_rows"] = pg.eval_on_selector_all("#card .pairs .all .pr", "els=>els.length")
        if shot: pg.screenshot(path=shot, full_page=True)
        for _ in range(8):
            if pg.query_selector("#card .card .btns button.b[data-item]"): break
            pg.click("#card button[data-skip]"); pg.wait_for_timeout(100)
        out["loss_title"] = pg.inner_text("#card .card h2")
        out["loss_pair"] = pg.eval_on_selector_all("#card .card .pairs .pr", "els=>els.map(e=>e.innerText)")
        out["loss_buttons"] = pg.eval_on_selector_all("#card .card .btns button.b[data-item]", "els=>els.map(e=>e.dataset.act)")
        if shot: pg.screenshot(path=shot.replace(".png", "_loss.png"), full_page=True)
        b.close()
    print("   [%s] why=%d chars rows=%s more=%s all=%s loss=%s pair=%s errors=%s" % (label, len(out.get("over_why", "")), out.get("over_rows"), out.get("has_more"), out.get("all_rows"), out.get("loss_title"), out.get("loss_pair"), out.get("console")))
    return out
def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--live", required=True); ap.add_argument("--shot", default=None); a = ap.parse_args(argv)
    check("live page is the S288 pin", md5(a.live) == LIVE_MD5, md5(a.live))
    tmp = tempfile.mkdtemp(prefix="s292_"); work = os.path.join(tmp, "stock_desk.html"); shutil.copy2(a.live, work)
    text = io.open(work, "r", encoding="utf-8").read()
    for old, _ in P.EDITS: check("anchor once: " + old[:40].replace("\n", " "), text.count(old) == 1, text.count(old))
    check("helper anchor once", text.count(P.HELPERS_ANCHOR) == 1)
    r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "patch_desk_pairs_s292.py"), "--file", work, "--from", "0" * 32], capture_output=True, text=True)
    check("refuses a wrong --from", r.returncode != 0 and "REFUSING" in (r.stdout + r.stderr))
    r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "patch_desk_pairs_s292.py"), "--file", work, "--from", LIVE_MD5], capture_output=True, text=True)
    check("patches from the live pin", r.returncode == 0, r.stdout + r.stderr); new_md5 = md5(work)
    r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "patch_desk_pairs_s292.py"), "--file", work], capture_output=True, text=True)
    check("idempotent", r.returncode == 0 and md5(work) == new_md5 and "ALREADY" in r.stdout)
    check("backup is the live bytes", md5(work + ".bak_S292_" + LIVE_MD5[:8]) == LIVE_MD5)
    sc = re.findall(r"<script[^>]*>(.*?)</script>", io.open(work, "r", encoding="utf-8").read(), re.S); js = os.path.join(tmp, "s.js"); io.open(js, "w", encoding="utf-8").write(sc[0])
    r = subprocess.run(["node", "--check", js], capture_output=True, text=True); check("script parses (node --check)", r.returncode == 0, r.stderr[:300])
    print("predicted md5 of the patched page: %s" % new_md5)
    ctl = drive(a.live, "untouched")
    check("control: the over sentence carries the pair dump", "Same-salt pairs found" in ctl.get("over_why", ""))
    check("control: no pairs block", not ctl.get("over_rows"))
    new = drive(work, "patched", shot=a.shot)
    check("over sentence no longer dumps the pairs", "Same-salt pairs found" not in new.get("over_why", "") and len(new.get("over_why", "")) < 400, len(new.get("over_why", "")))
    rows = new.get("over_rows") or []
    check("one line per item on the card (3)", len([x for x in rows if not x.startswith("Same salt")]) >= 3, rows)
    check("PARI CR 12.5 names ETOZOX 90 as its partner", any("PARI CR 12.5" in x and "ETOZOX 90" in x for x in rows), rows)
    check("an unpaired item says so", any("LONELY OVER" in x and "no same-salt pair" in x for x in rows), rows)
    check("the toggle exists and is closed", new.get("has_more") and new.get("all_hidden_before") is True)
    check("the toggle opens all 3 pairs, one per line", new.get("all_hidden_after") is False and new.get("all_rows") == 3, new.get("all_rows"))
    check("the loss card is ETOZOX 90", (new.get("loss_title") or "").startswith("ETOZOX 90"), new.get("loss_title"))
    check("the loss card names its partner", any("PARI CR 12.5" in x and "billing swap" in x for x in (new.get("loss_pair") or [])), new.get("loss_pair"))
    check("S288's four buttons still there", new.get("loss_buttons") == ["RECOVER", "WRITE_OFF", "RECOUNT", "PARKED"], new.get("loss_buttons"))
    check("no console errors", not new.get("console") and not ctl.get("console"), new.get("console"))
    print("\n%d failed" % len(FAILS)); return 1 if FAILS else 0
if __name__ == "__main__": sys.exit(main())
