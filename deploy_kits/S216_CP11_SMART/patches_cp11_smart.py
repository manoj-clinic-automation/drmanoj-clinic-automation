#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patches_cp11_smart.py - CP-1.1 steps 3 and 5 (S216)
====================================================
Base = the S216 back-nav page (LIVE, pin 7de1f5c3...).
Five ANCHORED patches, each must match EXACTLY ONCE.

STEP 3 - the auto-select reads the CASE, not just the estimate title.
  cpGuessProc() matched only the estimate name. "Total Hip Replacement" carries
  neither 'fracture' nor 'neck', so a fracture neck of femur got the elective
  opening (S215). It now also reads the bone dropdown, the fracture panel and
  the polio module.

  DELIBERATELY NARROW - it only ever swaps thr -> thrneck. That is the SAME
  operation with the correct narrative, so it is not a clinical decision.
  Where the real choice is clinical (fix the bone vs replace the head vs
  hemi), it does NOT choose: the guard's buttons offer, and the owner picks.
  An assistant must not pick an operation.

STEP 5 - transliteration stops failing silently.
  trOnline() times out at 1.5s and falls back to trLocal(), a letter-by-letter
  mapper with no place-name knowledge, WITH NO SIGNAL. Garbled place names
  reached a signed document. Now: a Bareilly-catchment dictionary and suffix
  rules are tried FIRST (no network, always right for the common names), and
  whenever the crude fallback actually ran, an amber warning names the words it
  guessed, on screen, above the consent.

Usage:  python3 patches_cp11_smart.py <base_page> <out_page>
"""
import sys, hashlib

BASE_MD5 = "7de1f5c359bb4c3e5a5994252227b309"

# ---------------------------------------------------------------- step 3 ----
A_GUESS = ("function cpGuessProc(t){ t=(t||'').toLowerCase();\n"
           " if(/thr|total hip|hip replace/.test(t)) return "
           "(/neck|fracture/.test(t)?'thrneck':'thr');")

N_GUESS = r'''/* S216 CP-1.1 step 3: the guess reads the CASE, not only the estimate title.
   Scope is deliberately narrow - see cpNeckEvidence(). */
function cpNeckEvidence(){
 var why=[];
 try{ var pcb=document.getElementById('cs_polio');
      if(pcb&&pcb.checked){
        var pk=(document.getElementById('cs_polio_proc')||{}).value||'';
        var pm=POLIO_MODULES.find(function(x){return x.k===pk;})||POLIO_MODULES[0];
        if(pm && /fnf|fracture neck/i.test(String(pm.k)+' '+String(pm.en||'')))
          why.push('the polio module names a fracture neck of femur');
      } }catch(_e){}
 try{ var b=((typeof pickSel==='function'?pickSel('c_bone'):'')||'')+' '
          +(((document.getElementById('c_bone_x')||{}).value)||'');
      if(/गर्दन/.test(b)) why.push('the bone chosen is the neck (गर्दन)');
 }catch(_e){}
 try{ var v=fmVals();
      if(v && (v.compound||v.comm||v.seg||v.art||v.multi||v.path||v.anyBoneloss))
        why.push('the fracture panel is in use');
 }catch(_e){}
 return why;
}
function cpGuessProc(t){ t=(t||'').toLowerCase();
 var neck=cpNeckEvidence().length>0;
 /* thr -> thrneck is the SAME operation with the correct opening, so this is
    safe to do automatically. Anything else stays the owner's choice. */
 if(/thr|total hip|hip replace/.test(t)) return ((/neck|fracture/.test(t)||neck)?'thrneck':'thr');'''

A_FF = ("    var est=null; try{ est=chooseEstimate(); }catch(_e2){}\n"
        "    var guess=cpGuessProc(est&&est.title);")

N_FF = ("    var est=null; try{ est=chooseEstimate(); }catch(_e2){}\n"
        "    var guess=cpGuessProc(est&&est.title);\n"
        "    /* no estimate yet, but the case already says fracture neck */\n"
        "    try{ if(!guess && cpNeckEvidence().length) guess='thrneck'; }catch(_e4){}")

# ---------------------------------------------------------------- step 5 ----
A_TRLOCAL = ("function trLocal(s){ return (s||'').split(/(\\s+)/).map(function(w){ "
             "return /[A-Za-z]/.test(w)?trWord(w):w; }).join(''); }")

N_TRLOCAL = r'''/* S216 CP-1.1 step 5: the Bareilly catchment, spelled correctly, offline.
   Tried BEFORE any network call and before the crude letter mapper. Add names here
   as they come up - one line each, no code change needed. */
var TR_PLACES={
 "bareilly":"बरेली","baheri":"बहेड़ी","aonla":"आँवला","anola":"आँवला",
 "faridpur":"फरीदपुर","nawabganj":"नवाबगंज","bhojipura":"भोजीपुरा",
 "meerganj":"मीरगंज","mirganj":"मीरगंज","shahi":"शाही","fatehganj":"फतेहगंज",
 "bithri":"बिथरी","chainpur":"चैनपुर","richha":"रिछा","sirauli":"सिरौली",
 "deorania":"देवरनियां","kyara":"क्यारा","majhgawan":"मझगवां","shergarh":"शेरगढ़",
 "izzatnagar":"इज्जतनगर","ramnagar":"रामनगर","dhaura":"धौरा","tanda":"टांडा",
 "rampur":"रामपुर","pilibhit":"पीलीभीत","shahjahanpur":"शाहजहाँपुर",
 "budaun":"बदायूँ","badaun":"बदायूँ","bisalpur":"बिसलपुर","puranpur":"पूरनपुर",
 "bilsanda":"बिलसंडा","tilhar":"तिलहर","jalalabad":"जलालाबाद","nigohi":"निगोही",
 "dataganj":"दातागंज","bilsi":"बिल्सी","sahaswan":"सहसवान","ujhani":"उझानी",
 "gunnaur":"गुन्नौर","chandausi":"चंदौसी","sambhal":"संभल","amroha":"अमरोहा",
 "milak":"मिलक","bilaspur":"बिलासपुर","suar":"स्वार","swar":"स्वार",
 "kashipur":"काशीपुर","rudrapur":"रुद्रपुर","haldwani":"हल्द्वानी",
 "moradabad":"मुरादाबाद","lakhimpur":"लखीमपुर","sitapur":"सीतापुर",
 "katra":"कटरा","khera":"खेड़ा","nagar":"नगर","ganj":"गंज","pur":"पुर"
};
var TR_SUFFIX=[["ganj","गंज"],["abad","ाबाद"],["nagar","नगर"],["garh","गढ़"],
               ["khera","खेड़ा"],["kheda","खेड़ा"],["pura","पुरा"],["patti","पट्टी"],
               ["wala","वाला"],["kot","कोट"],["pur","पुर"]];
/* trLocalWord returns [text, guessed?] so a guess can never travel silently. */
function trLocalWord(w){
 var k=w.toLowerCase().replace(/[^a-z]/g,'');
 if(!k) return [w,false];
 if(TR_PLACES[k]) return [TR_PLACES[k],false];
 for(var i=0;i<TR_SUFFIX.length;i++){
   var suf=TR_SUFFIX[i][0];
   if(k.length>suf.length+1 && k.slice(-suf.length)===suf){
     var stem=k.slice(0,-suf.length);
     if(TR_PLACES[stem]) return [TR_PLACES[stem]+TR_SUFFIX[i][1],false];
     return [trWord(stem)+TR_SUFFIX[i][1],true];
   }
 }
 return [trWord(w),true];
}
var TR_GUESSED=[];
/* record=false is a PROBE. Recording on the probe would raise the amber warning
   even when the online engine then answered correctly - a warning that cries
   wolf is worse than none. */
function trLocal(s,record){
 return (s||'').split(/(\s+)/).map(function(w){
   if(!/[A-Za-z]/.test(w)) return w;
   var r=trLocalWord(w);
   if(r[1] && record && TR_GUESSED.indexOf(w)<0) TR_GUESSED.push(w);
   return r[0];
 }).join('');
}
function trLocalProbeGuessed(s){
 return (s||'').split(/(\s+)/).some(function(w){
   return /[A-Za-z]/.test(w) && trLocalWord(w)[1]; });
}'''

A_HINDI = """function csHindi(s){
 if(!csLatin(s)) return Promise.resolve(s);
 if(TR_CACHE[s]) return Promise.resolve(TR_CACHE[s]);
 return trOnline(s).then(function(h){ TR_CACHE[s]=h; return h; })
  .catch(function(){ var h=trLocal(s); TR_CACHE[s]=h; return h; });
}"""

N_HINDI = r'''function csHindi(s){
 if(!csLatin(s)) return Promise.resolve(s);
 if(TR_CACHE[s]) return Promise.resolve(TR_CACHE[s]);
 /* the dictionary wins outright - no network, and right every time it hits */
 var dict=trLocal(s,false);
 if(!/[A-Za-z]/.test(dict) && !trLocalProbeGuessed(s)){ TR_CACHE[s]=dict; return Promise.resolve(dict); }
 return trOnline(s).then(function(h){ TR_CACHE[s]=h; return h; })
  .catch(function(){ var h=trLocal(s,true); TR_CACHE[s]=h; return h; });
}
/* An amber line, above the consent, naming every word the crude mapper guessed.
   S215 printed garbled place names on a signed document and said nothing. */
function trWarnHTML(){
 if(!TR_GUESSED.length) return '';
 var w=TR_GUESSED.map(function(x){ return '<b>'+String(x)
   .replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</b>'; }).join(', ');
 return '<div class="trwarn">⚠ हिंदी वर्तनी अपने आप बनाई गई — कृपया जाँच लें।'
  +'<br><span>Spelled by guesswork, not from the dictionary: '+w
  +' — check the spelling in the consent before printing, and tell me the correct'
  +' spelling so it goes into the dictionary.</span></div>';
}'''

A_OUT = " document.getElementById('cs_out').innerHTML=html;"
N_OUT = (" try{ var _tw=document.getElementById('cp11_trwarn');\n"
         "      if(_tw) _tw.innerHTML=trWarnHTML(); }catch(_e){}\n"
         " document.getElementById('cs_out').innerHTML=html;")

A_SLOT = '<div id="cp11_strip" style="display:none"></div>'
N_SLOT = ('<div id="cp11_strip" style="display:none"></div>\n'
          '<div id="cp11_trwarn"></div>\n'
          '<style>.trwarn{border:2px solid #b45309;background:rgba(224,179,106,.14);'
          'color:var(--ink);border-radius:10px;padding:9px 12px;margin:10px 0;'
          'font-size:13.5px;line-height:1.5}'
          '.trwarn span{font-size:12px;color:var(--muted)}</style>')


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
    patch(A_GUESS,   N_GUESS,   "S1 guess reads the case")
    patch(A_FF,      N_FF,      "S2 feed-forward with no estimate")
    patch(A_TRLOCAL, N_TRLOCAL, "S3 catchment dictionary + suffix rules")
    patch(A_HINDI,   N_HINDI,   "S4 dictionary first + the warning builder")
    patch(A_SLOT,    N_SLOT,    "S5 warning slot + style")
    patch("async function csGenerate(){\n var c=caseHeader();",
          "async function csGenerate(){\n TR_GUESSED=[];  /* a stale warning is a lie */\n var c=caseHeader();",
          "S7 warning list resets each generate")
    patch(A_OUT,     N_OUT,     "S6 warning painted on every generate")
    out = ref[0]
    open(out_fp, "w", encoding="utf-8", newline="").write(out)
    print("patches applied: %d" % n[0])
    print("base md5: %s" % got)
    print("out  md5: %s" % hashlib.md5(out.encode("utf-8")).hexdigest())

if __name__ == "__main__":
    main()
