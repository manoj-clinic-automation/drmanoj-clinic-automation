#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patches_stepper_back.py - S216: there is no way back from stage 2
=================================================================
Base = the S216 ayushman-names page (LIVE, pin af850a87...).
Two ANCHORED patches, each must match EXACTLY ONCE. CSS + 2 lines of JS.

WHY - read the screen's code first (owner rule 10):
  cpSetStage(1) ALREADY works: it closes the modal and returns to Enquiry.
  The button to call it is simply not reachable. #cpStepper sits in the page
  body, and stage 2 opens #caseModal - `position:fixed; inset:0; z-index:20`
  with a dark backdrop - which covers the whole page including the stepper.
  The only exit is #closeCase, a button at the very BOTTOM of a very long
  modal, past the entire consent form and the fracture grid. From the top of
  stage 2 there is no back at all.

  So this is not a missing button. It is a button that exists and is buried.

FIX: while the modal is open the stepper becomes a fixed bar at the top of the
  viewport, above the modal (z-index 30) on a solid background, and the modal
  gets top padding so nothing is hidden behind it. ONE stepper still, so it
  cannot disagree with itself.

Usage:  python3 patches_stepper_back.py <base_page> <out_page>
"""
import sys, hashlib

BASE_MD5 = "af850a87f9b9984f7dcf52a808b3e269"

A_CSS = "#cpStepper .cpstep.parked{opacity:.55;cursor:default}"

N_CSS = """#cpStepper .cpstep.parked{opacity:.55;cursor:default}
/* ---- S216: a way back from stage 2 ---------------------------------------
   The modal covers the page, so the stepper - and with it the only one-click
   route back to Enquiry - was unreachable; the sole exit was a Close button
   at the bottom of a very long form. While the modal is open the stepper
   floats above it instead of underneath. */
body.cpmodal #cpStepper{position:fixed;top:0;left:0;right:0;z-index:30;
  margin:0;padding:8px 10px;background:var(--bg);
  border-bottom:1px solid var(--line2,#5A706E);
  box-shadow:0 4px 14px rgba(0,0,0,.35)}
body.cpmodal #cpStepper .cpstep{background:var(--card)}
/* the bar wraps to 2-3 rows on a phone, so its height is MEASURED at runtime
   (cpBarFit) and written into --cpbar. A hard-coded value was 74px against a
   real 143px on a 420px-wide screen - it hid the top of the form. */
body.cpmodal .modal{padding-top:var(--cpbar,110px)}"""

A_JS = "   window.cpStage = cm.classList.contains('open') ? 2 : 1; cpPaint();"

N_JS = """   var _open = cm.classList.contains('open');
   window.cpStage = _open ? 2 : 1;
   try{ document.body.classList.toggle('cpmodal', _open); cpBarFit(); }catch(_e){}
   cpPaint();"""

A_FIT = "function cpSetStage(n){"
N_FIT = r'''/* The stepper bar wraps on narrow screens, so the space the modal must leave
   for it is measured, never assumed. */
function cpBarFit(){
 try{
  var s=document.getElementById('cpStepper');
  if(!s || !document.body.classList.contains('cpmodal')){
    document.body.style.removeProperty('--cpbar'); return; }
  document.body.style.setProperty('--cpbar', (s.offsetHeight+10)+'px');
 }catch(_e){}
}
try{ window.addEventListener('resize', cpBarFit); }catch(_e){}
function cpSetStage(n){'''


def main():
    base_fp, out_fp = sys.argv[1], sys.argv[2]
    src = open(base_fp, encoding="utf-8").read()
    got = hashlib.md5(open(base_fp, "rb").read()).hexdigest()
    assert got == BASE_MD5, "BASE MISMATCH: expected %s got %s" % (BASE_MD5, got)
    n = [0]; ref = [src]
    def patch(old, new, label):
        c = ref[0].count(old)
        assert c == 1, "ANCHOR FAIL (%s): found %d, expected 1" % (label, c)
        ref[0] = ref[0].replace(old, new); n[0] += 1
    patch(A_CSS, N_CSS, "B1 stepper floats above the modal")
    patch(A_JS,  N_JS,  "B2 body class follows the modal")
    patch(A_FIT, N_FIT, "B3 bar height measured, not assumed")
    out = ref[0]
    open(out_fp, "w", encoding="utf-8", newline="").write(out)
    print("patches applied: %d" % n[0])
    print("base md5: %s" % got)
    print("out  md5: %s" % hashlib.md5(out.encode("utf-8")).hexdigest())

if __name__ == "__main__":
    main()
