#!/usr/bin/env python3
"""selftest_s288.py -- proves S288_DESK_PARKED offline, twice over.

Part A (bytes): the patcher's anchors hit exactly once on the live page; refusal on
a wrong --from; idempotence; the page's script still parses (node --check).
Part B (behaviour, headless Chromium): the patched page is served with a mocked
report API and driven as a person would -- the real-loss card shows the fourth
button, tapping it POSTs action PARKED, a lane row carries "Kept elsewhere", the
find box shows the word already given and "Change this word" reopens the line
(POST action OPEN) and lands on its card. The untouched page is driven the same
way as the control: no PARKED button on the loss card, no way to change a word.

    python3 -B selftest_s288.py --live stock_desk.html.live
"""
from __future__ import print_function
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import patch_desk_parked_s288 as P  # noqa: E402

LIVE_MD5 = "54aeda96ba022b30b21bdb9f77616a18"
FAILS = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else "  -- " + str(detail)))
    if not ok:
        FAILS.append(name)


def md5(p):
    return hashlib.md5(io.open(p, "rb").read()).hexdigest()


def fixture():
    diff = lambda item, lane, d, word=None, kind=None: dict(  # noqa: E731
        item=item, packing="1x10", pack=10, marg=50, counted=50 + d, diff=d, mrp_p=-2500 if d < 0 else 2500,
        cost_p=-2000 if d < 0 else 2000, mrp_source="sale", lane=lane, kind=kind, word=word, why="test line",
        sold_fy=120, loose_fy=0, last_sale="2026-09-10", last_purchase="2026-08-30", answer=None,
        needs_owner=False, lookups=[])
    return dict(ok=True, count_id=1, day="06-09-2026", totals=dict(written_off=0, pursue=0, parked=0, explained=0,
                recount=0, bill=0, marg_fix=0, open=3), mismatch=dict(mrp_short_p=5000, mrp_over_p=0),
                differences=[diff("ETOZOX 90", "loss", -10), diff("HYORTH INJ", "loss", -1, word=dict(action="WRITE_OFF")),
                             diff("PARA 650", "allowance", -2)],
                dead_matched=[], pairs=[], links=dict(amir="/finance/stock/page/amir", loss_page="/finance/stock/page/loss",
                                                       amir_page="/finance/stock/page/amir"))


def drive(page_path, label):
    """Serve the page with a mocked API through Playwright; return what happened."""
    from playwright.sync_api import sync_playwright
    html = io.open(page_path, "r", encoding="utf-8").read()
    html = html.replace("/*__BOOT__*/", 'window.BOOT={count_id:1,user:"manoj",checker:true};')
    posts = []
    fx = fixture()
    out = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()
        pg.on("console", lambda m: out.setdefault("console", []).append(m.text) if m.type == "error" else None)

        def route(r):
            u = r.request.url
            if u.endswith("/finance/stock/page/desk"):
                r.fulfill(status=200, content_type="text/html", body=html)
            elif "/api/pad/report/" in u:
                r.fulfill(status=200, content_type="application/json", body=json.dumps(fx))
            elif "/api/pad/decide" in u:
                body = json.loads(r.request.post_data or "{}")
                posts.append(body)
                for d in fx["differences"]:
                    if d["item"] in body.get("items", []):
                        d["word"] = None if body["action"] == "OPEN" else dict(action=body["action"])
                r.fulfill(status=200, content_type="application/json",
                          body=json.dumps(dict(ok=True, count_id=1, action=body.get("action"), label="x", items=1)))
            else:
                r.fulfill(status=204, body="")
        pg.route("**/*", route)
        pg.goto("http://desk.test/finance/stock/page/desk")
        pg.wait_for_function("document.querySelector('#card .card') !== null")
        # lane cards come first; skip to the first item card (the largest real loss: ETOZOX 90)
        for _ in range(8):
            if pg.query_selector("#card .card .btns button.b[data-item]"):
                break
            pg.click("#card button[data-skip]")
            pg.wait_for_timeout(100)
        out["first_title"] = pg.inner_text("#card .card h2")
        out["loss_buttons"] = pg.eval_on_selector_all("#card .card .btns button.b[data-item]", "els=>els.map(e=>e.dataset.act)")
        if "PARKED" in out["loss_buttons"]:
            pg.click("#card .card .btns button[data-act='PARKED']")
            pg.wait_for_timeout(300)
        out["posts_after_park"] = list(posts)
        # the find box on an item that already carries a word
        pg.fill("#q", "HYORTH")
        pg.wait_for_selector("#qr .hit")
        pg.click("#qr .hit")
        pg.wait_for_timeout(200)
        out["hit_text"] = pg.inner_text("#qr .hit")
        out["has_reopen"] = pg.query_selector("#qr button[data-reopen]") is not None
        if out["has_reopen"]:
            pg.click("#qr button[data-reopen]")
            pg.wait_for_timeout(500)
            out["after_reopen_title"] = pg.inner_text("#card .card h2")
        out["posts"] = list(posts)
        # the lane list rows (allowance lane) carry the word
        pg.goto("http://desk.test/finance/stock/page/desk")
        pg.wait_for_function("document.querySelector('#card .card') !== null")
        # skip item cards until the lane card
        for _ in range(6):
            if pg.query_selector("#card button[data-list]"):
                break
            pg.click("#card button[data-skip]")
            pg.wait_for_timeout(100)
        if pg.query_selector("#card button[data-list]"):
            pg.click("#card button[data-list]")
            out["row_acts"] = pg.eval_on_selector_all("#list .li .acts button", "els=>els.map(e=>e.dataset.act)")
        b.close()
    print("   [%s] first=%s loss_buttons=%s reopen=%s rows=%s errors=%s" % (
        label, out.get("first_title"), out.get("loss_buttons"), out.get("has_reopen"), out.get("row_acts"),
        out.get("console")))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", required=True, help="the live stock_desk.html bytes (54aeda96)")
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args(argv)
    check("live page is the S228 pin", md5(a.live) == LIVE_MD5, md5(a.live))
    tmp = tempfile.mkdtemp(prefix="s288_")
    work = os.path.join(tmp, "stock_desk.html")
    shutil.copy2(a.live, work)
    text = io.open(work, "r", encoding="utf-8").read()
    for old, _ in P.EDITS:
        check("anchor once: " + old[:40], text.count(old) == 1, text.count(old))
    check("handler anchor once", text.count(P.HANDLER_ANCHOR) == 1)
    r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "patch_desk_parked_s288.py"), "--file", work,
                        "--from", "0" * 32], capture_output=True, text=True)
    check("refuses a wrong --from", r.returncode != 0 and "REFUSING" in (r.stdout + r.stderr))
    r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "patch_desk_parked_s288.py"), "--file", work,
                        "--from", LIVE_MD5], capture_output=True, text=True)
    check("patches from the live pin", r.returncode == 0, r.stdout + r.stderr)
    new_md5 = md5(work)
    r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "patch_desk_parked_s288.py"), "--file", work],
                       capture_output=True, text=True)
    check("idempotent (second run changes nothing)", r.returncode == 0 and md5(work) == new_md5 and "ALREADY" in r.stdout)
    check("backup beside the file", os.path.exists(work + ".bak_S288_" + LIVE_MD5[:8]))
    check("backup is the live bytes", md5(work + ".bak_S288_" + LIVE_MD5[:8]) == LIVE_MD5)
    patched = io.open(work, "r", encoding="utf-8").read()
    sc = re.findall(r"<script[^>]*>(.*?)</script>", patched, re.S)
    check("one script block", len(sc) == 1, len(sc))
    js = os.path.join(tmp, "s.js")
    io.open(js, "w", encoding="utf-8").write(sc[0])
    r = subprocess.run(["node", "--check", js], capture_output=True, text=True)
    check("script parses (node --check)", r.returncode == 0, r.stderr[:300])
    check("PARKED on the loss card (bytes)", '"PARKED","Kept elsewhere' in patched)
    check("PARKED on lane rows (bytes)", 'data-act="PARKED" data-item=' in patched)
    check("find box offers Change (bytes)", "data-reopen" in patched)
    print("predicted md5 of the patched page: %s" % new_md5)
    if not a.no_browser:
        try:
            ctl = drive(a.live, "untouched")
            check("control: no PARKED on the loss card", "PARKED" not in (ctl.get("loss_buttons") or []))
            check("control: no way to change a word", not ctl.get("has_reopen"))
            check("control: no console errors", not ctl.get("console"))
            new = drive(work, "patched")
            check("the first item card is the largest real loss", new.get("first_title", "").startswith("ETOZOX 90"), new.get("first_title"))
            check("loss card shows PARKED as the 4th button",
                  new.get("loss_buttons") == ["RECOVER", "WRITE_OFF", "RECOUNT", "PARKED"], new.get("loss_buttons"))
            pk = [p for p in new.get("posts_after_park", []) if p.get("action") == "PARKED"]
            check("tapping it POSTs PARKED for that item", len(pk) == 1 and pk[0]["items"] == ["ETOZOX 90"], pk)
            check("find box names the word already given", "written off" in (new.get("hit_text") or ""), new.get("hit_text"))
            check("find box offers Change this word", new.get("has_reopen"))
            op = [p for p in new.get("posts", []) if p.get("action") == "OPEN"]
            check("Change POSTs OPEN for that item", len(op) == 1 and op[0]["items"] == ["HYORTH INJ"], op)
            check("and lands on its card", (new.get("after_reopen_title") or "").startswith("HYORTH INJ"),
                  new.get("after_reopen_title"))
            check("lane rows carry Kept elsewhere", "PARKED" in (new.get("row_acts") or []), new.get("row_acts"))
            check("patched: no console errors", not new.get("console"), new.get("console"))
        except ImportError:
            check("playwright present for Part B", False, "playwright not importable")
    n = 0
    for _ in FAILS:
        n += 1
    print("\n%d failed" % n)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
