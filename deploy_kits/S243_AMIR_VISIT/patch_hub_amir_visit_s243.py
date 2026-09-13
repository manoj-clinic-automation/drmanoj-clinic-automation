#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_hub_amir_visit_s243.py -- S243_AMIR_VISIT: a collapsed "Amir's visit -- what was done"
block on the owner's hub, inside the Marg card, fed by /finance/amir/day/api/visit-summary.

THREE anchored additions to /root/finance/finance_ui/finance_approvals.html, patched ON THE BOX
(the live page is not in the repository), each anchor asserted to occur EXACTLY ONCE, else
REFUSED and nothing is written.  Never writes the live file: writes <file>.new.

  B  the Marg card: a <details> block after the identity box, before "How this works"
  F  loadAmirVisit() defined before loadReclass()
  L  loadAmirVisit() called on the same line that starts the other loaders

Built to sit beside S243_AUTOAPPLY (already in the live page cc349dd0) and S243_DARPAN_KAL
(installs before this kit).  None of the three anchors is touched by either: DARPAN_KAL edits
the tab strip, the home-medicine card comment, the loadHomeMed() header and APPENDS to the
loader line; this kit PREPENDS to that line and its anchor omits the newline, so it matches once
in both orders.  Verified at build on the live page and on the DARPAN_KAL-patched page.

    HUB_PATH=/root/finance/finance_ui/finance_approvals.html /root/wa/venv/bin/python3 -B patch_hub_amir_visit_s243.py
    --selftest <finance_approvals.html> [more pages]
"""
import hashlib
import io
import os
import sys

TARGET = os.environ.get("HUB_PATH", "/root/finance/finance_ui/finance_approvals.html")
MARK = "S243 amir visit"

B_OLD = ('  <div id="idBox" class="note"></div>\n'
         '  <details class="help"><summary>How this works</summary><div>\n'
         '  Export from Marg as <b>Bill wise sales statement</b>')
B_NEW = ('  <div id="idBox" class="note"></div>\n'
         '  <!-- ' + MARK + ' -- the owner\'s collapsed summary of Amir\'s visit-day work (13-Sep ruling) -->\n'
         '  <details class="help" id="amirVisitBox"><summary id="amirVisitSum">Amir\'s visit — what was done</summary>\n'
         '  <div id="amirVisit">loading&hellip;</div></details>\n'
         '  <details class="help"><summary>How this works</summary><div>\n'
         '  Export from Marg as <b>Bill wise sales statement</b>')

F_OLD = 'function loadReclass(){\n'
F_NEW = ('/* ' + MARK + ' -- today\'s visit from amir_day.py: one verdict per step, the counts, the salt-list prompt */\n'
         'function loadAmirVisit(){\n'
         '  fetch("/finance/amir/day/api/visit-summary?_="+Date.now(),{cache:"no-store"}).then(function(r){return r.json()}).then(function(j){\n'
         '    if(!j||!j.ok){$("amirVisit").innerHTML=\'<span class="mut">\'+esc((j&&(j.message||j.error))||"—")+\'</span>\';return}\n'
         '    var sl=j.salt_list||{},b=j.bills||{},rp=j.reports||{},sa=j.salts||{},cl=j.claims||{};\n'
         '    var h=\'<div><b>\'+esc(j.day)+\'</b> · \'+esc(j.state)+(j.closed_at?\' at \'+esc(String(j.closed_at).slice(11,16)):\'\')+\'</div>\';\n'
         '    h+=\'<div class="tblwrap" style="margin-top:6px"><table><tbody>\';\n'
         '    (j.steps||[]).forEach(function(s){h+=\'<tr><td>\'+s.n+\'</td><td>\'+esc(s.label)+\'</td><td class="\'+(s.state==="done"?"ok":(s.state==="not needed"?"mut":"warn"))+\'">\'+esc(s.state)+\'</td><td class="mut">\'+esc(s.note||"")+\'</td></tr>\'});\n'
         '    h+=\'</tbody></table></div>\';\n'
         '    h+=\'<div class="note">Bills tapped: <b>\'+(b.tapped||0)+\'</b> (\'+esc(b.line||"")+\') · Purchase reports: \'+esc(rp.line||"")+\' · Salt tasks ticked: <b>\'+(sa.ticked||0)+\'</b> (\'+esc(sa.line||"")+\') · Claims raised: <b>\'+(cl.n||0)+\'</b> worth ₹\'+esc(cl.amount||"0")+\'</div>\';\n'
         '    h+=\'<div class="\'+(sl.pending?"warn":(sl.fresh?"ok":"mut"))+\'">\'+esc(sl.owner_line||"")+\'</div>\';\n'
         '    h+=\'<div class="mut" style="margin-top:6px"><a href="/finance/amir/day">Amir\\\'s day (English) ↗</a></div>\';\n'
         '    $("amirVisit").innerHTML=h;\n'
         '    var sm=$("amirVisitSum");if(sm){sm.textContent="Amir\'s visit — what was done · "+j.day+" · "+j.state+(sl.pending?" · salt list awaited":"")}\n'
         '  }).catch(function(){$("amirVisit").innerHTML=\'<span class="mut">could not load</span>\'});\n'
         '}\n'
         'function loadReclass(){\n')

L_OLD = 'loadHomeMed(); loadReclass(); loadMPR(); loadReview(); loadStaffCards();'
L_NEW = 'loadAmirVisit(); loadHomeMed(); loadReclass(); loadMPR(); loadReview(); loadStaffCards();'


def md5(b):
    return hashlib.md5(b).hexdigest()


def patch_text(src):
    if MARK in src:
        return src, "already"
    for nm, old in (("B", B_OLD), ("F", F_OLD), ("L", L_OLD)):
        n = src.count(old)
        if n != 1:
            return src, "refused: anchor %s occurs %d times (need exactly 1)" % (nm, n)
    out = src.replace(B_OLD, B_NEW, 1).replace(F_OLD, F_NEW, 1).replace(L_OLD, L_NEW, 1)
    return out, "patched"


def selftest(paths):
    ok = bad = 0

    def check(name, cond):
        nonlocal ok, bad
        if cond:
            ok += 1
            print("  PASS ", name)
        else:
            bad += 1
            print("  FAIL ", name)

    for p in paths:
        s = io.open(p, encoding="utf-8").read()
        out, st = patch_text(s)
        check("%s (%s): patches (%s)" % (os.path.basename(p), md5(s.encode("utf-8"))[:8], st), st == "patched")
        if st != "patched":
            continue
        check("  block, loader and call each once",
              out.count('id="amirVisitBox"') == 1 and out.count('id="amirVisit"') == 1
              and out.count("function loadAmirVisit()") == 1 and out.count("loadAmirVisit(); loadHomeMed();") == 1)
        check("  the block sits inside the Marg card, before its help",
              out.find('id="margCard"') < out.find('id="amirVisitBox"') < out.find('id="homeMedCard"'))
        check("  the Marg card's own help, the home-medicine loader and the reclass loader survive",
              out.count("function loadHomeMed()") == 1 and out.count("function loadReclass()") == 1
              and out.count("Export from Marg as <b>Bill wise sales statement</b>") == 1)
        check("  only additions: every original line still present",
              all(ln in out for ln in s.splitlines() if ln.strip()))
        check("  the S243_AUTOAPPLY wording is still there", '"applied automatically "' in out)
        if "S243 darpan kal" in s:
            check("  DARPAN_KAL's card, loader and call are untouched",
                  out.count('id="kalCard"') == 1 and out.count("function loadKal()") == 1
                  and out.count("loadStaffCards(); loadKal();") == 1)
        check("  second run is a no-op", patch_text(out)[1] == "already")
    check("a stranger page is refused", patch_text("<html></html>\n")[1].startswith("refused"))
    print("selftest: %d passed, %d failed" % (ok, bad))
    return 0 if bad == 0 else 1


def main(argv):
    if argv and argv[0] == "--selftest":
        return selftest(argv[1:])
    out_path = TARGET + ".new"
    if "--out" in argv:
        out_path = argv[argv.index("--out") + 1]
    raw = io.open(TARGET, "rb").read()
    src = raw.decode("utf-8")
    print("source %s md5 %s" % (TARGET, md5(raw)))
    new, st = patch_text(src)
    if st == "already":
        print("ALREADY PATCHED -- nothing to do")
        return 0
    if st != "patched":
        print("REFUSED: %s -- nothing written" % st[len("refused: "):])
        return 2
    io.open(out_path, "w", encoding="utf-8", newline="\n").write(new)
    print("wrote %s md5 %s" % (out_path, md5(new.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
