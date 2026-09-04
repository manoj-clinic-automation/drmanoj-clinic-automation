#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_deskpage_anchor_s224.py -- S224: THE SPOT COUNT GETS ITS BILL ANCHOR (page half).

THE OWNER, 04-Sep-2026, urgent:

    "IN VAAPSI PAGE, THE STOCK CHECK SECTION DOES NOT HAVE ANY LAST SALE BILL
     NUMBER ENTRY BOX, PLEASE FIX IT."

The "stock check section" is the third group of the S221 jaankari card --
heading "ginti karni hai" -- one item a row, a number box, "gin liya". It was
built (S221_JAANKARI, 03-Sep) as a question and so it skipped the one rule
every count on the counting page has obeyed since S207: the LAST SALE BILL
NUMBER is typed BEFORE anything is counted. Without it a difference found later
cannot be attributed -- three strips may have been sold while he was counting.

WHAT THIS DOES -- in returns_desk.html, nothing else:
  1  ONE anchor box under the "ginti karni hai" heading, for the sitting:
       label       आख़िरी सेल बिल नंबर (Marg)     -- Hindi, a staff page (D366)
       placeholder A003195
       the why-line, in his language: the count is pinned to this bill.
     One box, not one per row -- he counts a few shelves in one go after one
     bill; the counting page asks once per count for the same reason.
  2  "gin liya" REFUSES without it: the box gets focus and a Hindi line says
     why. Nothing is posted. (The server refuses too -- the page half is the
     courtesy, the server half is the rule.)
  3  The anchor travels in the POST as anchor_bill. It survives re-renders of
     the list (the list is rebuilt after every answer).

Target: /root/finance/returns_desk.html (live pin 6d98e1b0...)
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_deskpage_anchor_s224.py
Offline:         RDP_PATH=./returns_desk.html python3 -B patch_deskpage_anchor_s224.py
"""

import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('RDP_PATH', '/root/finance/returns_desk.html')
MARK = "S224 anchor"

# --------------------------------------------------------------- anchor A: the box, and jkCount
A_OLD = '''function jkCount(ref){
 var el=$('jkq_'+ref);var v=el?String(el.value).trim():'';
 if(v===''){if(el)el.focus();return;}
 jkPost({kind:'spot',ref:ref,answer:'counted',value:v}).then(function(j){
'''
A_NEW = '''/* S224 anchor -- THE LAST SALE BILL NUMBER. A count without a cut-off in the
   bill stream is not a measurement, it is an impression (the owner, 04-Sep).
   The counting page has asked for it since S207; the spot count now does too.
   One box for the sitting; the server refuses a 'counted' answer without it. */
var JK_ANCHOR='';
function jkAnchorBox(){
 return '<div id="jkAnchorBox" style="border:1px solid var(--teal);border-radius:10px;padding:8px 10px;margin-top:8px">'
  +'<label for="jkAnchor" style="display:block;font-weight:700;margin-bottom:4px">'
  +'\\u0906\\u0916\\u093c\\u093f\\u0930\\u0940 \\u0938\\u0947\\u0932 \\u092c\\u093f\\u0932 \\u0928\\u0902\\u092c\\u0930 (Marg)</label>'
  +'<input id="jkAnchor" type="text" autocapitalize="characters" autocomplete="off" placeholder="A003195" '
  +'style="width:100%;padding:10px" value="'+jkEsc(JK_ANCHOR)+'" oninput="JK_ANCHOR=this.value.trim().toUpperCase()">'
  +'<div class="dim" style="margin-top:6px;line-height:1.5">'
  +'\\u0917\\u093f\\u0928\\u0924\\u0940 \\u0907\\u0938 \\u092c\\u093f\\u0932 \\u092a\\u0930 \\u091f\\u093f\\u0915\\u0940 \\u0939\\u0948 \\u2014 '
  +'\\u0907\\u0938\\u0915\\u0947 \\u092c\\u093e\\u0926 \\u092c\\u093f\\u0915\\u0940 \\u0926\\u0935\\u093e \\u0907\\u0938 \\u0917\\u093f\\u0928\\u0924\\u0940 \\u092e\\u0947\\u0902 \\u0928\\u0939\\u0940\\u0902 \\u092e\\u093e\\u0928\\u0940 \\u091c\\u093e\\u090f\\u0917\\u0940 \\u0964 '
  +'\\u092c\\u093f\\u0928\\u093e \\u092c\\u093f\\u0932 \\u0928\\u0902\\u092c\\u0930 \\u0917\\u093f\\u0928\\u0924\\u0940 \\u0926\\u0930\\u094d\\u091c \\u0928\\u0939\\u0940\\u0902 \\u0939\\u094b\\u0917\\u0940 \\u0964'
  +'</div><div id="jkAnchorMsg" style="color:#f0b429;margin-top:4px"></div></div>';
}
function jkCount(ref){
 var a=$('jkAnchor');if(a)JK_ANCHOR=String(a.value).trim().toUpperCase();
 if(!JK_ANCHOR){
  if(a){a.focus();}
  var m=$('jkAnchorMsg');if(m)m.textContent='\\u092a\\u0939\\u0932\\u0947 \\u0906\\u0916\\u093c\\u093f\\u0930\\u0940 \\u0938\\u0947\\u0932 \\u092c\\u093f\\u0932 \\u0928\\u0902\\u092c\\u0930 \\u0932\\u093f\\u0916\\u093f\\u090f \\u2014 \\u092c\\u093f\\u0928\\u093e \\u092c\\u093f\\u0932 \\u0915\\u0940 \\u0917\\u093f\\u0928\\u0924\\u0940 \\u0926\\u0930\\u094d\\u091c \\u0928\\u0939\\u0940\\u0902 \\u0939\\u094b\\u0924\\u0940 \\u0964';
  return;
 }
 var el=$('jkq_'+ref);var v=el?String(el.value).trim():'';
 if(v===''){if(el)el.focus();return;}
 jkPost({kind:'spot',ref:ref,answer:'counted',value:v,anchor_bill:JK_ANCHOR}).then(function(j){
'''

# --------------------------------------------------------------- anchor B: the box sits under the heading
B_OLD = '''  pend+='<div style="margin-top:12px"><b>'+groups[g][3]+'</b> <span class="dim">('+rows.length+')</span></div>';
  for(var i=0;i<show;i++)pend+=groups[g][2](rows[i]);
'''
B_NEW = '''  pend+='<div style="margin-top:12px"><b>'+groups[g][3]+'</b> <span class="dim">('+rows.length+')</span></div>';
  if(groups[g][0]==='spot')pend+=jkAnchorBox();   /* S224 anchor */
  for(var i=0;i<show;i++)pend+=groups[g][2](rows[i]);
'''


def main():
    with open(TARGET, 'r', encoding='utf-8', newline='') as fh:
        src = fh.read()
    if MARK in src:
        print("already patched: %s" % TARGET)
        return 0
    for name, old in (("A", A_OLD), ("B", B_OLD)):
        n = src.count(old)
        if n != 1:
            print("REFUSED: anchor %s found %d times (need exactly 1) -- file left untouched" % (name, n))
            return 2
    out = src.replace(A_OLD, A_NEW).replace(B_OLD, B_NEW)
    if out.count("<script") != out.count("</script"):
        print("REFUSED: script tags would come out unbalanced -- file left untouched")
        return 3
    stamp = dt.datetime.now().strftime('%Y%m%d-%H%M%S')
    bak = TARGET + '.bak_S224_anchor_' + stamp
    shutil.copy2(TARGET, bak)
    with open(TARGET, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("next     the render test (offline), then the install")
    return 0


if __name__ == '__main__':
    sys.exit(main())
