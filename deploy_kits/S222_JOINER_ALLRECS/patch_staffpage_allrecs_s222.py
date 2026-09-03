#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_staffpage_allrecs_s222.py -- S222 ⭐1-3b, page half: open a CLOSED record.

Adds one button to the home screen -- 📋 sab record — and a search box. Every joiner record,
open and closed, with how many steps are done and a kholo button that opens the same record
page the pending list opens.

Why it matters beyond convenience: the S222 login check lives on the record page. Without this,
that check is unreachable for anybody whose joining is finished -- which is everybody it most
needs to be run on, Amir first.

Target: /root/finance/staff_manage.html   (live pin f9c01552795a6bb350940550ea81a431, i.e.
        AFTER S222_JOINER_LOGIN. This kit refuses against anything else.)

Offline:  SM_PATH=./staff_manage.html python3 -B patch_staffpage_allrecs_s222.py
"""

import datetime as dt
import hashlib
import os
import shutil
import sys

TARGET = os.environ.get('SM_PATH', '/root/finance/staff_manage.html')
MARK = "S222 ALL RECORDS"
EXPECT_FROM = "f9c01552795a6bb350940550ea81a431"


A_OLD = ''' <div id="pending" style="margin-top:10px"></div>
'''

A_NEW = ''' <div id="pending" style="margin-top:10px"></div>
 <!-- S222 ALL RECORDS -- pending shows only what is unfinished; a finished
      record still has to be openable, or the login check on the record page
      can never be run on the people who are already joined. -->
 <div style="margin-top:10px">
  <button class="btn" onclick="loadAll()">📋 Sab record (poore ho chuke bhi)</button>
  <input id="allq" placeholder="naam ya ref" style="max-width:150px"
         onkeyup="if(event.key==='Enter')loadAll()">
 </div>
 <div id="allrecs" style="margin-top:8px"></div>
'''


B_OLD = '''async function loadPending(){
'''

B_NEW = '''/* ---- S222 ALL RECORDS ---------------------------------------------------
   Every record, open and closed. Read only -- it opens the same record page
   the pending list opens. */
async function loadAll(){
 const q=(el("allq").value||"").trim();
 const box=el("allrecs");
 box.innerHTML='<span class="sub">dekh rahe hain…</span>';
 let j=null;
 try{ j=await fetch(API+"/all"+(q?"?q="+encodeURIComponent(q):"")).then(r=>r.json()); }
 catch(e){ j=null; }
 if(!j||!j.ok){ box.innerHTML='<span class="sub">list nahin mili</span>'; return; }
 if(!j.records.length){ box.innerHTML='<span class="sub">koi record nahin mila</span>'; return; }
 box.innerHTML='<table><tr><th>kaun</th><th></th><th>steps</th><th>haalat</th>'+
  '<th></th></tr>'+j.records.map(x=>'<tr><td><b>'+x.person+'</b>'+
  (x.username?' <span class="sub">'+x.username+'</span>':'')+'</td>'+
  '<td><span class="pill '+(x.kind==="EXIT"?"exit":"")+'">'+
  (x.kind==="EXIT"?"vidaai":"jodna")+'</span></td>'+
  '<td>'+x.done+'/'+x.total+'</td>'+
  '<td>'+(x.complete?'<span style="color:#2e6b34">poora ✓</span>':
    '<span style="color:#a8730a">'+x.status+'</span>')+'</td>'+
  '<td><button class="btn" onclick="showRec(\\''+x.ref+'\\')">kholo</button></td>'+
  '</tr>').join("")+'</table>';
}

async function loadPending(){
'''


# --------------------------------------------------------------- anchor C
# A GREEN TICK MUST BE TESTED, NOT ASSERTED.
#
# S222_JOINER_LOGIN made the missing-login case honest. The EXISTING-login case
# was not: it printed the derived password as fact. The owner's own check the
# same afternoon showed why that is not good enough -- his login existed, made
# by his own hand at /portal/users, and nothing here knew whether `amir1234` was
# the password he had actually set. The route now TRIES the password; this shows
# what it found, three ways, and never claims the middle one.

C_OLD = """ if(j.exists&&j.active){
  box.innerHTML='\u2705 login <b>'+j.username+'</b> ban chuka hai'+
   (j.role?' ('+j.role+')':'')+' \u00b7 pehla password <b>'+j.password+
   '</b> \u2014 pehli login par badalna hoga'; return; }
"""

C_NEW = """ if(j.exists&&j.active){
  let t='\u2705 login <b>'+j.username+'</b> ban chuka hai'+
   (j.role?' ('+j.role+')':'');
  if(j.password_works===true)
   t+=' \u00b7 password <b>'+j.password+'</b> abhi chalta hai \u2014 '+
      'pehli login par badalna hoga';
  else if(j.password_works===false)
   t+='<div class="warnbox" style="margin-top:6px">\u26a0\ufe0f <b>'+j.password+
      '</b> se login <b>NAHIN</b> hota \u2014 password badla ja chuka hai. '+
      'Naya password aapko pata ho to theek; warna neeche '+
      '<b>Password reset</b> se default par laaiye.</div>';
  else
   t+=' \u00b7 <span style="color:#999">password jaancha nahin ja saka</span>';
  box.innerHTML=t; return; }
"""


PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW), ("C", C_OLD, C_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    before = hashlib.md5(open(TARGET, "rb").read()).hexdigest()
    print("current pin  %s" % before)
    if before != EXPECT_FROM:
        raise SystemExit("REFUSED: this file is %s, not the %s this kit was built against "
                         "(S222_JOINER_LOGIN must be installed first). NOTHING was changed."
                         % (before, EXPECT_FROM))
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S222_allrecs_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    if out.count("<script") != src.count("<script") or \
            out.count("</script>") != src.count("</script>"):
        raise SystemExit("REFUSED: the script tags came out unbalanced. NOTHING was written.")
    open(TARGET, "w", encoding="utf-8").write(out)
    pin = hashlib.md5(open(TARGET, "rb").read()).hexdigest()
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % pin)
    return 0


if __name__ == "__main__":
    sys.exit(main())
