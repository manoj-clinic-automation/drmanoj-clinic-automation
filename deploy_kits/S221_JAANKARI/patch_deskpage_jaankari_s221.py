#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_deskpage_jaankari_s221.py -- S221 star-1-1, part 2 of 2: the Hindi list itself.

One card on the desk's first screen, under the day's slips, so it is the first
thing he sees when he opens the page he already uses. It hides itself completely
when there is nothing to ask -- an empty list must never look like a task.

The owner's own three words are the buttons on the identity rows:
    yah sahi hai . bill dhoondho . pata nahin
A spot count takes a NUMBER instead, because a count is a number.

He never sees a score, a verdict, a ratio or a rupee flag -- the S220 design's
rule, kept. He sees one plain question per row, and the full mobile beside the
name (D363, a counter screen).

The line under the heading is deliberate and it is the whole ruling in one
sentence, in his language: answering changes no money -- it only tells the
doctor. Nothing on this page can act, so nothing on it should imply it can.

Target: /root/finance/returns_desk.html (live pin 32c4b8cc...)
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_deskpage_jaankari_s221.py
Offline:         RDP_PATH=./returns_desk.html python3 -B patch_deskpage_jaankari_s221.py
"""

import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('RDP_PATH', '/root/finance/returns_desk.html')
MARK = "S221 star-1-1"


# --------------------------------------------------------------- anchor A
A_OLD = ''' <div class="card">
  <div class="row"><b>\u0906\u091c \u0915\u0940 \u092a\u0930\u094d\u091a\u093f\u092f\u093e\u0901</b><button class="ghost" onclick="loadSlips()">\u21bb</button></div>
  <div id="todaySlips" class="dim">\u2014</div>
 </div>
</div>
'''

A_NEW = ''' <div class="card">
  <div class="row"><b>\u0906\u091c \u0915\u0940 \u092a\u0930\u094d\u091a\u093f\u092f\u093e\u0901</b><button class="ghost" onclick="loadSlips()">\u21bb</button></div>
  <div id="todaySlips" class="dim">\u2014</div>
 </div>
 <!-- S221 star-1-1 -- jaankari: poochhna hai, hukum nahin -->
 <div class="card hide" id="jkCard">
  <div class="row"><b>\U0001f4cb \u091c\u093e\u0928\u0915\u093e\u0930\u0940 \u091a\u093e\u0939\u093f\u090f</b><button class="ghost" onclick="loadJaankari()">\u21bb</button></div>
  <div class="dim" style="margin:4px 0 10px;line-height:1.5">
   \u0907\u0928\u0915\u093e \u091c\u0935\u093e\u092c \u0926\u0947\u0928\u0947 \u0938\u0947 \u0915\u094b\u0908 \u092a\u0948\u0938\u093e \u0928\u0939\u0940\u0902 \u092c\u0926\u0932\u0924\u093e \u0964
   \u0938\u093f\u0930\u094d\u092b\u093c \u0921\u0949\u0915\u094d\u091f\u0930 \u0938\u093e\u0939\u092c \u0915\u094b \u092a\u0924\u093e \u091a\u0932 \u091c\u093e\u0924\u093e \u0939\u0948 \u0964
   \u092a\u0924\u093e \u0928 \u0939\u094b \u0924\u094b \u0915\u094b\u0908 \u092c\u093e\u0924 \u0928\u0939\u0940\u0902 \u2014 \u091b\u094b\u0921\u093c \u0926\u0940\u091c\u093f\u090f \u0964
  </div>
  <div id="jkList"></div>
  <div id="jkDone" class="dim" style="margin-top:10px"></div>
 </div>
</div>
'''


# --------------------------------------------------------------- anchor B
B_OLD = '''loadSlips();
</script>
'''

B_NEW = '''loadSlips();

/* S221 star-1-1 -- Darpan's list. Read, ask, record. It cannot do anything
   else: the only write behind it is one row in jaankari_answer. */
var JK={disputes:[],identity:[],spot:[]};
var JK_CAP=6, JK_MORE={};
function jkMore(g){JK_MORE[g]=1;jkRender();}
function jkEsc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){
 return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function jkBtns(kind,ref){
 return '<div class="row" style="gap:6px;margin-top:8px;flex-wrap:wrap">'
  +'<button onclick="jkSay(\\''+kind+'\\',\\''+ref+'\\',\\'ok\\')">\\u092f\\u0939 \\u0938\\u0939\\u0940 \\u0939\\u0948</button>'
  +'<button class="ghost" onclick="jkSay(\\''+kind+'\\',\\''+ref+'\\',\\'find_bill\\')">\\u092c\\u093f\\u0932 \\u0922\\u0942\\u0901\\u0922\\u093c\\u094b</button>'
  +'<button class="ghost" onclick="jkSay(\\''+kind+'\\',\\''+ref+'\\',\\'dont_know\\')">\\u092a\\u0924\\u093e \\u0928\\u0939\\u0940\\u0902</button>'
  +'</div>';
}
function jkBox(inner){
 return '<div style="border-top:1px solid #eee;padding:10px 2px;line-height:1.6">'+inner+'</div>';
}
function jkDispute(r){
 var mob=r.mobile?('<div class="dim">\\u0966\\u0966 '+jkEsc(r.mobile)+'</div>'):'';
 return jkBox('<div><b>'+jkEsc(r.bill||'')+'</b> \\u00b7 '+jkEsc(r.date||'')+'</div>'
  +'<div>\\u092a\\u0930\\u094d\\u091a\\u0940 \\u092a\\u0930 \\u0928\\u093e\\u092e <b>'+jkEsc(r.bill_name||'\\u2014')+'</b> \\u0932\\u093f\\u0916\\u093e \\u0939\\u0948, '
  +'\\u092a\\u0930 ID <b>'+jkEsc(r.clinic_id||'')+'</b> \\u0939\\u092e\\u093e\\u0930\\u0947 \\u0930\\u093f\\u0915\\u0949\\u0930\\u094d\\u0921 \\u092e\\u0947\\u0902 '
  +'<b>'+jkEsc(r.master_name||'\\u2014')+'</b> \\u0939\\u0948 \\u0964 \\u0938\\u0939\\u0940 \\u0915\\u094c\\u0928 \\u0939\\u0948 ?</div>'
  +mob+jkBtns('dispute',r.ref));
}
function jkIdentity(r){
 var nm=r.name?('<div>\\u092a\\u0930\\u094d\\u091a\\u0940 \\u092a\\u0930 <b>'+jkEsc(r.name)+'</b> \\u0932\\u093f\\u0916\\u093e \\u0939\\u0948 \\u0964</div>'):'';
 return jkBox('<div><b>'+jkEsc(r.ref)+'</b> \\u00b7 '+jkEsc(r.date||'')+' \\u00b7 '+rupee(r.amount_p)+'</div>'
  +'<div>\\u092f\\u0939 \\u0935\\u093e\\u092a\\u0938\\u0940 \\u0915\\u093f\\u0938\\u0915\\u0940 \\u0925\\u0940 ? \\u0915\\u094b\\u0908 \\u0928\\u093e\\u092e \\u092f\\u093e ID \\u0928\\u0939\\u0940\\u0902 \\u091c\\u0941\\u0921\\u093c\\u093e \\u0964</div>'
  +nm+jkBtns('identity',r.ref));
}
function jkSpot(r){
 var b=r.batch?(' \\u00b7 \\u092c\\u0948\\u091a '+jkEsc(r.batch)):'';
 return jkBox('<div><b>'+jkEsc(r.item||'')+'</b>'+b+'</div>'
  +'<div>\\u0936\\u0947\\u0932\\u094d\\u092b\\u093c \\u092a\\u0930 \\u0917\\u093f\\u0928 \\u0915\\u0930 \\u092c\\u0924\\u093e\\u0907\\u090f \\u2014 \\u0915\\u093f\\u0924\\u0928\\u0940 \\u0939\\u0948 ?</div>'
  +'<div class="row" style="gap:6px;margin-top:8px">'
  +'<input id="jkq_'+jkEsc(r.ref)+'" type="number" inputmode="numeric" style="max-width:120px" placeholder="\\u0917\\u093f\\u0928\\u0924\\u0940">'
  +'<button onclick="jkCount(\\''+r.ref+'\\')">\\u0917\\u093f\\u0928 \\u0932\\u093f\\u092f\\u093e</button>'
  +'<button class="ghost" onclick="jkSay(\\'spot\\',\\''+r.ref+'\\',\\'dont_know\\')">\\u0905\\u092d\\u0940 \\u0928\\u0939\\u0940\\u0902</button>'
  +'</div>');
}
function jkRender(){
 var pend='',done=0;
 var groups=[['disputes',JK.disputes,jkDispute,'\\u0928\\u093e\\u092e \\u092e\\u0947\\u0932 \\u0928\\u0939\\u0940\\u0902 \\u0916\\u093e \\u0930\\u0939\\u093e'],
             ['identity',JK.identity,jkIdentity,'\\u0915\\u093f\\u0938\\u0915\\u0940 \\u0935\\u093e\\u092a\\u0938\\u0940 \\u0925\\u0940'],
             ['spot',JK.spot,jkSpot,'\\u0917\\u093f\\u0928\\u0924\\u0940 \\u0915\\u0930\\u0928\\u0940 \\u0939\\u0948']];
 for(var g=0;g<groups.length;g++){
  var rows=(groups[g][1]||[]).filter(function(r){return !r.answered;});
  done+=(groups[g][1]||[]).length-rows.length;
  if(!rows.length)continue;
  /* JK_CAP -- one sitting, never a wall. The render test showed 22 rows of
     history stacked on a phone; a queue that long is not a question, it is a
     chore, and he will stop opening the page. The rest wait their turn. */
  var show=JK_MORE[groups[g][0]]?rows.length:Math.min(rows.length,JK_CAP);
  pend+='<div style="margin-top:12px"><b>'+groups[g][3]+'</b> <span class="dim">('+rows.length+')</span></div>';
  for(var i=0;i<show;i++)pend+=groups[g][2](rows[i]);
  if(show<rows.length)pend+='<div style="padding:8px 2px"><button class="ghost" onclick="jkMore(\\''+groups[g][0]+'\\')">'
    +'\u0914\u0930 \u0926\u093f\u0916\u093e\u090f\u0901 ('+(rows.length-show)+')</button></div>';
 }
 $('jkList').innerHTML=pend;
 $('jkDone').innerHTML=done?('\\u2713 '+done+' \\u0915\\u093e \\u091c\\u0935\\u093e\\u092c \\u0926\\u0947 \\u0926\\u093f\\u092f\\u093e \\u2014 \\u0927\\u0928\\u094d\\u092f\\u0935\\u093e\\u0926 \\u0964'):'';
 var any=pend||done;
 $('jkCard').className=any?'card':'card hide';
}
function jkPost(body){
 return fetch(API+'/jaankari/answer',{method:'POST',
  headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
  .then(function(r){return r.json();});
}
function jkSay(kind,ref,answer){
 jkPost({kind:kind,ref:ref,answer:answer}).then(function(j){
  if(!j.ok){alert('\\u0930\\u0941\\u0915\\u093e: '+(j.message||j.error));return;}
  loadJaankari();
 }).catch(function(){});
}
function jkCount(ref){
 var el=$('jkq_'+ref);var v=el?String(el.value).trim():'';
 if(v===''){if(el)el.focus();return;}
 jkPost({kind:'spot',ref:ref,answer:'counted',value:v}).then(function(j){
  if(!j.ok){alert('\\u0930\\u0941\\u0915\\u093e: '+(j.message||j.error));return;}
  loadJaankari();
 }).catch(function(){});
}
function loadJaankari(){
 fetch(API+'/jaankari').then(function(r){return r.json();})
 .then(function(j){if(!j||!j.ok)return;JK=j.lists||JK;jkRender();})
 .catch(function(){});
}
loadJaankari();
</script>
'''


PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW)]


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
    bak = TARGET + ".bak_S221_jaankari_" + stamp
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
    print("next     the selftest, then the walk, then: systemctl restart clinic-finance.service")
    return 0


if __name__ == "__main__":
    sys.exit(main())
