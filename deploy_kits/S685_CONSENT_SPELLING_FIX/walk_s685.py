#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s685.py -- kit S685_CONSENT_SPELLING_FIX: the Hindi-spelling box driven in Chromium with MADE-UP names and
addresses. For each typed form: generate, correct the spelling in the box, Apply everywhere -- the consent text must carry
the correction, and a correction that finds nothing must say so (never a tick for 0 places, never a changed header alone).

  python3 walk_s685.py PAGE.html [--control]     (needs walk_s684.py beside it for the page helpers)
Last line: 'walk_s685: N of N green' or, with --control, 'control: R red · G green'.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import walk_s684 as w                                      # noqa: E402
from playwright.sync_api import sync_playwright            # noqa: E402

NEW = "नया पता बरेली"
CASES = [  # (label, field, typed, kind)  kind: 'fix' = the tidied ones (red before), 'old' = held before and after
    ("plain address", "cs_res", "Civil Lines Bareilly", "old"),
    ("address with a comma", "cs_res", "Civil Lines, Bareilly", "old"),
    ("address with a space before the comma", "cs_res", "Civil Lines , Bareilly", "fix"),
    ("address with a double space", "cs_res", "Gaon  Rampur Bareilly", "fix"),
    ("address typed in Hindi with a space before the comma", "cs_res", "गाँव रामपुर , बरेली", "fix"),
    ("relative's name with a double space", "cs_relname", "Suresh  Kumar Test", "fix"),
    ("Hindi + English print: an address with ' .' and ' ,'", "cs_res", "म. नं . 12 , सिविल लाइंस", "fix|hien"),
    ("Hindi + English print: an address with ' ;' and a double space", "cs_res", "गली 4 ; रामपुर  बाग", "fix|hien"),
]


def main():
    page = sys.argv[1]
    control = "--control" in sys.argv
    res = []
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg, errs = w.open_page(br, page)
        for label, field, typed, kind in CASES:
            w.reset(pg, "generic", part="जांघ", bone="जांघ की हड्डी")
            pg.evaluate("(m)=>{ window.csLang=m; }", "hien" if kind.endswith("|hien") else "hi")
            kind = kind.split("|")[0]
            pg.evaluate("([f,v])=>{ document.getElementById(f).value=v; }", [field, typed])
            w.gen(pg)
            key = {"cs_res": "res", "cs_relname": "reln"}[field]
            r = pg.evaluate("""([key,nv])=>{ var i=CS_FIX.findIndex(function(f){return f.key===key;}); if(i<0) return {nofix:true};
                var inp=document.getElementById('csfix_'+i); inp.value=nv; csFixApply();
                var t=document.getElementById('cs_out').innerText;
                return {found:t.split(nv).length-1, msg:document.getElementById('csfix_msg').textContent, meta:(csLastMeta||{})[key]}; }""", [key, NEW])
            good = (not r.get("nofix")) and r["found"] >= 1 and r["msg"].startswith("✔")
            res.append((label + ": the correction reaches the consent", kind, good, str(r)[:160]))
        # a correction that can find nothing: the consent edited by hand first, then the box
        pg.evaluate("()=>{ window.csLang='hi'; }")
        w.reset(pg, "generic", part="जांघ", bone="जांघ की हड्डी")
        pg.evaluate("()=>{ document.getElementById('cs_res').value='Civil Lines Bareilly'; }")
        w.gen(pg)
        r = pg.evaluate("""(nv)=>{ var i=CS_FIX.findIndex(function(f){return f.key==='res';}); var f=CS_FIX[i];
            var out=document.getElementById('cs_out'); csFixReplace(out,f.cur,'हाथ से बदला');   /* the owner had edited it by hand */
            var before=(csLastMeta||{}).res; var inp=document.getElementById('csfix_'+i); inp.value=nv; csFixApply();
            return {msg:document.getElementById('csfix_msg').textContent, meta_kept:(csLastMeta||{}).res===before}; }""", "दूसरा पता बरेली")   # a spelling the page has not learnt above
        res.append(("nothing found: no tick, the words say so, the header is not changed alone", "fix",
                    (not r["msg"].startswith("✔")) and ("not found" in r["msg"]) and r["meta_kept"], str(r)[:200]))
        res.append(("no script error on the page", "old", not errs, "; ".join(errs[:2])))
        br.close()
    for label, kind, good, note in res:
        print("%s %s%s" % ("GREEN" if good else "RED  ", label, ("" if good else " -- " + note)))
    g = sum(1 for x in res if x[2])
    if control:
        print("control: %d S685 red · %d older red · %d green" % (sum(1 for x in res if x[1] == "fix" and not x[2]),
                                                                   sum(1 for x in res if x[1] == "old" and not x[2]), g))
    else:
        print("walk_s685: %d of %d green" % (g, len(res)))


if __name__ == "__main__":
    main()
