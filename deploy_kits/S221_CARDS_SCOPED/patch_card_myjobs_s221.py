#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_card_myjobs_s221.py -- S221 B6 rev 2: the directory becomes HIS JOBS.

THE OWNER, 03-Sep-2026, on seeing his own S218 B6 directive live:

    "i saw many cards links in darpans card, plan was to keep these separate and
     scoped in the pwa"  ... then, on the choice offered: "b ok"

S218's `S218_CARDS_FINAL_CONTRACT` B6 put a **directory of every staff-facing
card** on Darpan's page -- link, INTENDED USERS and PURPOSE, seven rows,
self-growing. It was the owner's own amendment and it is one day old. Read back
on the real screen it was the wrong shape: a man working the counter does not
need a map of everyone's surfaces, he needs his own work.

WHAT CHANGES. The registry MECHANISM stays exactly as it was -- a card still
ships with its own row and still joins by itself, no hand-edited list, which was
the good half of B6. What changes is the presentation and the audience:

  * the rows are FILTERED to the person whose page this is
  * the page he is already on is dropped from his own list
  * what is left renders as BUTTONS -- his jobs -- not as a directory with
    "who: ... purpose: ..." underneath every line
  * the full directory of everyone's cards moves to the owner's hub, where a
    directory belongs

THIS IS A DISPLAY SCOPE, NOT AN ACCESS CONTROL, and the distinction is written
here so nobody later mistakes it for one. Every page behind these links keeps
its own `require()` and its own `unit_role` rows; hiding a link removes clutter,
never permission. Reception's access to the Vaapsi desk is untouched by this
file.

FAIL-SAFE, deliberately biased toward showing too much rather than too little:
if NO row in the registry carries a `who` key -- an old registry against a new
page -- the page shows every card, exactly as it does today. A man's navigation
must never go blank because a data file lagged a code file.

Target: /root/finance/darpan_card.html (live pin aeb4fd7d..., reproduced offline
from the S218 base fa6f0a86 + the three S220 card patchers, each intermediate
md5 matching its recorded pin, before a line of this was written)

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_card_myjobs_s221.py
Offline:         CARD_PATH=./darpan_card.html python3 -B patch_card_myjobs_s221.py
"""

import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('CARD_PATH', '/root/finance/darpan_card.html')
MARK = "S221 MERE KAAM"

A_OLD = '''/* S218 -- SAB CARDS EK JAGAH: registry se apne aap; naya card khud judta hai. */
(async function(){
 try{
  const r=await fetch("/finance/api/cards?_="+Date.now(),{cache:"no-store"});
  const j=await r.json();
  if(!(j&&j.ok&&j.cards&&j.cards.length))return;
  const sec=document.createElement("div");
  sec.className="sec";
  let h='<div class="row"><span class="k">\U0001f5c2 सारे कार्ड — किसके लिए, किस काम के</span></div>';
  j.cards.forEach(c=>{
    h+='<div style="border-top:1px solid #eee;padding:8px 2px">'
      +'<a href="'+c.url+'" style="font-weight:700;font-size:16px">'+c.name+' →</a>'
      +'<div class="muted">कौन: '+c.users+' · काम: '+c.purpose+'</div></div>';
  });
  sec.innerHTML=h;
  document.body.appendChild(sec);
 }catch(e){}
})();
'''

A_NEW = '''/* S221 MERE KAAM -- the S218 registry, same mechanism, his audience.
   A new card still joins by itself (a card ships with its registry row); it
   now joins HIS list only if he is in its `who`, renders as a button rather
   than a directory line, and the page he is standing on is left out of it.
   The full directory of every card lives on the owner's hub.
   DISPLAY SCOPE ONLY -- every page keeps its own require() and unit_role. */
(async function(){
 try{
  const r=await fetch("/finance/api/cards?_="+Date.now(),{cache:"no-store"});
  const j=await r.json();
  if(!(j&&j.ok&&j.cards&&j.cards.length))return;
  const me=(document.body.getAttribute("data-user")||"darpan").toLowerCase();
  const here=location.pathname.replace(/\\/+$/,"");
  /* An old registry against this new page must not blank his navigation. */
  const scoped=j.cards.some(c=>c.who!==undefined);
  const mine=j.cards.filter(c=>{
    const u=String(c.url||"").replace(/\\/+$/,"");
    if(u&&u===here)return false;                 /* not the page he is on */
    if(!scoped)return true;                      /* pre-B6 registry: show all */
    const w=(c.who||[]).map(x=>String(x).toLowerCase());
    return w.indexOf("all")>=0||w.indexOf(me)>=0;
  });
  if(!mine.length)return;                        /* nothing of his: no section */
  const sec=document.createElement("div");
  sec.className="sec";
  let h='<div class="row"><span class="k">\U0001f9f0 मेरे काम</span></div>'
       +'<div style="display:flex;flex-wrap:wrap;gap:8px;padding:8px 2px">';
  mine.forEach(c=>{
    h+='<a href="'+c.url+'" style="flex:1 1 45%;min-width:150px;text-align:center;'
      +'padding:14px 10px;border:1px solid #d7d7d7;border-radius:10px;'
      +'font-weight:700;font-size:16px;text-decoration:none">'+c.name+'</a>';
  });
  h+='</div>';
  sec.innerHTML=h;
  document.body.appendChild(sec);
 }catch(e){}
})();
'''

PAIRS = [("A", A_OLD, A_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S221_myjobs_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    if out.count("<script") != src.count("<script") or \
            out.count("</script>") != src.count("</script>"):
        raise SystemExit("REFUSED: script tags unbalanced. NOTHING was changed.")
    open(TARGET, "w", encoding="utf-8").write(out)
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("next     copy cards_registry.json, then restart is NOT needed (static file)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
