#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_staffpage_login_s222.py -- S222 star-1-3, page half: stop printing a login that does not exist.

BEFORE, on every JOIN record, unconditionally:

    login: amir · pehla password: amir1234 (pehli login par badalna hoga)

Both halves invented in the browser from the first name. Nothing had created that account. The
owner read it out to Amir and the portal refused him -- F-295.

AFTER, the same line asks the server what is actually true, and says it:

    ✅ login amir ban chuka hai (manager) · pehla password amir1234 -- pehli login par badalna hoga
    ⚠️ login amir hai lekin BAND hai -- portal se chaalu kijiye
    ⚠️ Yeh login abhi bana NAHIN hai. amir se koi login nahin kar sakta.   [🔑 login banao]

The button asks for a role FROM THE PORTAL STORE'S OWN LIST -- never a guessed word -- and the
route behind it creates the login and then signs in as him to prove it before reporting success.

AND THE WHATSAPP MESSAGE GETS SOMEWHERE TO GO. It was composed and displayed with no way to
send it. Now there is a send button: `https://wa.me/?text=...` with NO number in it. WhatsApp
opens with the message already typed and the owner picks the person from his own contacts.
The owner's ruling at S222, and it is the F-185-safe shape: no number is written into this
page, into the database, into the repository, or onto the box.

Target: /root/finance/staff_manage.html   (live pin 9ff9fc48919f76cd86a35135c10b554b)
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_staffpage_login_s222.py
Offline:         SM_PATH=./staff_manage.html python3 -B patch_staffpage_login_s222.py
"""

import datetime as dt
import hashlib
import os
import shutil
import sys

TARGET = os.environ.get('SM_PATH', '/root/finance/staff_manage.html')
MARK = "S222 star-1-3"
EXPECT_FROM = "9ff9fc48919f76cd86a35135c10b554b"


A_OLD = r''' if(j.kind==="JOIN"&&j.username)
  h+='<div class="sub">login: <b>'+j.username+'</b> · pehla password: <b>'+
   j.username+'1234</b> (pehli login par badalna hoga)</div>';
'''

A_NEW = r''' /* S222 star-1-3 -- this line used to STATE a login and a password that
    nothing had created. It now says only what the server confirms. */
 if(j.kind==="JOIN"&&j.username)
  h+='<div class="sub" id="loginState">login: <b>'+j.username+
   '</b> · <span style="color:#999">jaanch rahe hain…</span></div>';
'''


B_OLD = r'''   '\')">📱 WhatsApp message dikhao</button><div id="wa"></div>';
 F.innerHTML=h;
}
'''

B_NEW = r'''   '\')">📱 WhatsApp message dikhao</button><div id="wa"></div>';
 F.innerHTML=h;
 if(j.kind==="JOIN"&&j.username) checkLogin(ref);          /* S222 star-1-3 */
}
'''


C_OLD = r'''async function waMsg(ref){
 const r=await fetch(API+"/message?ref="+encodeURIComponent(ref));
 const j=await r.json();
 el("wa").innerHTML=j.ok?'<div class="msgbox">'+j.text+'</div>':"";
}
'''

C_NEW = r'''async function waMsg(ref){
 const r=await fetch(API+"/message?ref="+encodeURIComponent(ref));
 const j=await r.json();
 if(!j.ok){ el("wa").innerHTML=""; return; }
 /* S222 star-1-3 -- the message was composed and shown with NO WAY TO SEND IT.
    wa.me with no number: WhatsApp opens with the text already typed and you
    choose the person from your own contacts. No number is written into this
    page, the database, the repository or the box (F-185). */
 el("wa").innerHTML='<div class="msgbox">'+j.text+'</div>'+
  '<a class="btn primary" style="margin-top:8px" target="_blank" rel="noopener" '+
  'href="https://wa.me/?text='+encodeURIComponent(j.text)+
  '">📤 WhatsApp par bhejo</a>';
}

/* ---- S222 star-1-3: F-295, the login that was never created ---------------
   The page no longer asserts a login. It asks. */
async function checkLogin(ref){
 const box=el("loginState"); if(!box) return;
 let j=null;
 try{ j=await fetch(API+"/portal_user?ref="+encodeURIComponent(ref))
        .then(r=>r.json()); }catch(e){ j=null; }
 if(!j||!j.ok){
  box.innerHTML='login: <span style="color:#999">jaanch nahin ho payi</span>'; return; }
 if(!j.store_readable){
  box.innerHTML='login: <b>'+j.username+'</b> · <span style="color:#999">'+
   'portal ka user store padha nahin ja saka</span>'; return; }
 if(j.exists&&j.active){
  box.innerHTML='✅ login <b>'+j.username+'</b> ban chuka hai'+
   (j.role?' ('+j.role+')':'')+' · pehla password <b>'+j.password+
   '</b> — pehli login par badalna hoga'; return; }
 if(j.exists&&!j.active){
  box.innerHTML='⚠️ login <b>'+j.username+'</b> hai lekin <b>BAND</b> hai — '+
   'portal se chaalu kijiye'; return; }
 box.innerHTML='<div class="warnbox">⚠️ <b>Yeh login abhi bana NAHIN hai.</b> '+
  '<b>'+j.username+'</b> se koi login nahin kar sakta. Password batane se '+
  'pehle ise banaiye.</div>'+
  '<button class="btn warn" style="margin-top:8px" onclick="makeLogin(\''+ref+
  '\')">🔑 login banao</button>';
}

/* The role is CHOSEN FROM THE STORE'S OWN LIST, shown as buttons -- not typed
   into a prompt() and not hard-coded here. Two reasons: a role this page
   invented would be refused by the store anyway, and on a phone a native
   prompt is a bad way to pick one of three fixed words. */
async function makeLogin(ref){
 const box=el("loginState"); if(!box) return;
 let j=null;
 try{ j=await fetch(API+"/portal_user?ref="+encodeURIComponent(ref))
        .then(r=>r.json()); }catch(e){ j=null; }
 const roles=(j&&j.roles)||[];
 if(!roles.length){ toast("Portal store me koi role nahin mila — banaya nahin gaya"); return; }
 let h='<div class="warnbox">Role chuniye — <b>'+j.username+'</b> ka login isi role '+
  'se banega:</div><div id="rolePick" style="margin-top:8px">';
 for(const r of roles)
  h+='<button class="btn" style="margin-right:6px" onclick="doMakeLogin(\''+ref+
   '\',\''+r+'\')">'+r+'</button>';
 h+='</div>';
 box.innerHTML=h;
}

async function doMakeLogin(ref,role){
 const by=whoAmI(); if(!by) return;
 const pick=el("rolePick");
 if(pick) pick.innerHTML='<span style="color:#999">bana rahe hain…</span>';
 try{
  const k=await post(API+"/portal_user/create",{ref,role,by});
  toast(k.message||"Login ban gaya");
 }catch(e){ toast(""+e); }
 checkLogin(ref);
}
'''


PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW), ("C", C_OLD, C_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    before = hashlib.md5(open(TARGET, "rb").read()).hexdigest()
    print("current pin  %s" % before)
    if before != EXPECT_FROM:
        raise SystemExit("REFUSED: this file is %s, not the %s this kit was built against. "
                         "NOTHING was changed." % (before, EXPECT_FROM))
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S222_login_" + stamp
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
