#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""render_s521.py -- kit S521_AMIR_BOARD_STAGE_PROOF: the render check's harness (the brief's walk step 3), run on the PC at build time.

    python -B render_s521.py --html stock_amir.html --json board_amir.json --out page.html

Takes the live stock_amir.html (unchanged by this kit) and the NEW board JSON the walk saved as amir (--json-out), and writes ONE page
that boots as amir and renders that JSON instead of fetching it -- nothing else in the page's script is touched.  The page is then opened
in a browser at phone width and the rendered text is asserted (section 2 reads "Orthotic: sab sahi" with the green chip; section 3 (c)
lists the renames with "Marg mein badal diya" buttons; no voucher card).  The assertions are in ASSERT_JS below, run in the page; the
result line is what the report records.  Writes only --out.  Never import this file.
"""
import argparse
import io
import json
import sys

FETCH = 'fetch(BASE+"/api/pad/amir/"+B.count_id,{cache:"no-store"}).then(r=>r.json())'
BOOT = "/*__BOOT__*/"
ASSERT_JS = r"""
(function(){
  const body=document.getElementById("body"); const cards=[...body.querySelectorAll(":scope>.card")];
  const sec2=cards[1], sec3=cards[2];
  const row=sec2.querySelector(".row"); const q=row.querySelector(".q").textContent; const chip=row.querySelector(".chip");
  const h3=[...sec3.querySelectorAll("h3")].find(x=>x.id==="renames");
  const btns=[...sec3.querySelectorAll("button[data-rtick]")];
  const out={
    sec2_line:q, chip:chip.textContent, chip_ok:chip.classList.contains("ok"),
    renames_h3:h3?h3.textContent:null, rename_buttons:btns.length, button_text:btns.length?btns[0].textContent:null,
    voucher_cards:cards[0].querySelectorAll(".vc,details.vd").length, voucher_empty:(cards[0].querySelector(".empty")||{}).textContent||null,
    wait_line:(sec3.querySelector("h3#renames+div.lead")||{}).textContent||null, width:window.innerWidth};
  out.PASS = q.indexOf("Orthotic: sab sahi")===0 && out.chip_ok && out.chip==="Mil gaye ✓" && !/ANKLE BINDER|TYNOR/.test(q)
    && btns.length>0 && out.button_text==="Marg mein badal diya" && out.voucher_cards===0;
  return JSON.stringify(out);
})()
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with io.open(a.html, "r", encoding="utf-8") as fh:
        h = fh.read()
    with io.open(a.json, "r", encoding="utf-8") as fh:
        j = json.load(fh)
    if h.count(FETCH) != 1 or h.count(BOOT) != 1:
        print("STOP: the page does not carry the one fetch and the one boot marker this harness was written on")
        return 2
    boot = "window.BOOT=%s;window.W521=%s;" % (json.dumps(dict(count_id=int(j.get("count_id") or 0), user="amir", checker=False)), json.dumps(j, ensure_ascii=False))
    h = h.replace(BOOT, boot, 1).replace(FETCH, "Promise.resolve(window.W521)", 1)
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(h)
    print("wrote %s (count %s; proof_state %r; renames_ready %r)" % (a.out, j.get("count_id"), j.get("proof_state"), j.get("renames_ready")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
