#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patches_cp11_guard.py - CP-1.1 step 1: the wrong-opening guard (S216)
=====================================================================
Base = the LIVE casepack_page.html (S215 pin 903b915e837c6e06b5b19a833af79c09).
Three ANCHORED patches, each must match EXACTLY ONCE or the build aborts.
Nothing else in the page is touched. No consent wording is changed.

WHY (recorded in the code, F-97 discipline):
  S215 printed the ELECTIVE hip opening for a month-old fracture neck of femur.
  cpGuessProc() reads only the estimate TITLE ("Total Hip Replacement" carries
  neither 'fracture' nor 'neck') and returns 'thr'. fmApplyOpening() inserts
  fracture wording by rewriting the phrase 'TOOT GAI HAI.' which NO elective
  opening contains - so the fracture panel had nothing to attach to. The polio
  module was keyed thr_fnf (fracture neck of femur) the whole time. Nothing
  cross-checked the two. 32 selftests + 17 render checks all passed.

Usage:  python3 patches_cp11_guard.py <base_page> <out_page>
"""
import sys, hashlib

BASE_MD5 = "903b915e837c6e06b5b19a833af79c09"

A1 = '<div style="margin-top:8px"><button class="cbtn" id="cs_gen">Generate consent</button></div>'

A2 = ("async function csGenerate(){\n var c=caseHeader();\n"
      " var proc=CONSENT_LIB.find(function(x){return x.k==="
      "document.getElementById('cs_proc').value;})||CONSENT_LIB[0];")

A3 = "/* ---- polio module UI ---- */"

STRIP = r'''<div id="cp11_strip" style="display:none"></div>
<div style="margin-top:8px"><button class="cbtn" id="cs_gen">Generate consent</button></div>'''

GUARD_IN_GEN = r'''async function csGenerate(){
 var c=caseHeader();
 var proc=CONSENT_LIB.find(function(x){return x.k===document.getElementById('cs_proc').value;})||CONSENT_LIB[0];
 /* CP-1.1 S216 - the wrong-opening guard. Refuses to print a degenerative
    narrative over a fracture case. Overridable, never silently. */
 var _g11=(typeof cp11Check==='function')?cp11Check():null;
 if(_g11 && window.cp11Ok!==_g11.proc.k){
   try{ cp11Status(); document.getElementById('cp11_strip').scrollIntoView({block:'center'}); }catch(_e){}
   return;
 }'''

GUARD_JS = r'''/* ===== CP-1.1 - S216 - the wrong-opening guard =============================
   An elective opening narrates a worn-out joint or an old problem. A fracture
   case narrates an injury. Printing the first over the second is a false
   clinical statement in a signed legal document. This refuses to generate
   when the two disagree; the owner may override, and the override is written
   into the consent change note so it is never silent.                        */

var CP11_ELECTIVE={thr:1,tkr:1,acl:1,cubitus:1,implrem:1,osteo:1};
var CP11_SUGGEST={thr:['thrneck','hemi','noffix','itfix'],tkr:['dfemur','ptibia','patella']};
var CP11_BAD='border:2px solid #b91c1c;background:rgba(185,28,28,.10);color:var(--ink);border-radius:12px;padding:10px 13px;margin:10px 0;font-size:13.5px;line-height:1.55;display:block';
var CP11_OK ='border:1px solid var(--line);background:rgba(116,194,149,.08);color:var(--ink);border-radius:10px;padding:8px 12px;margin:10px 0;font-size:12.5px;line-height:1.5;display:block';

function cp11Esc(s){ return String(s==null?'':s)
 .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

function cp11Proc(){
 try{ var s=document.getElementById('cs_proc'); if(!s) return null;
      return CONSENT_LIB.find(function(x){return x.k===s.value;})||CONSENT_LIB[0]; }
 catch(_e){ return null; }
}

/* Signals that ONLY make sense when a bone is broken. Deliberately NOT
   fmActive(): osteoporosis / geriatric / DVT-risk are true of many planned
   replacements and would fire the guard on a correct elective consent. */
function cp11FxSignals(){
 var s=[], v=null;
 try{ v=fmVals(); }catch(_e){ v=null; }
 if(v){
  if(v.compound)    s.push('open (compound) fracture ticked');
  if(v.comm)        s.push('comminution ticked');
  if(v.seg)         s.push('segmental fracture ticked');
  if(v.art)         s.push('articular (into joint) ticked');
  if(v.multi)       s.push(v.fx.length+' additional fracture(s) added');
  if(v.path)        s.push('a fracture pathway is chosen');
  if(v.anyBoneloss) s.push('bone-loss possibility ticked');
  if(v.poly)        s.push('polytrauma injury ticked');
 }
 try{ var pcb=document.getElementById('cs_polio');
      if(pcb&&pcb.checked){
        var pk=(document.getElementById('cs_polio_proc')||{}).value||'';
        var pm=POLIO_MODULES.find(function(x){return x.k===pk;})||POLIO_MODULES[0];
        if(pm && /fnf|fracture|neck/i.test(String(pm.k)+' '+String(pm.en||'')))
          s.push('the polio module is "'+pm.en+'"');
      } }catch(_e){}
 try{ var b=((typeof pickSel==='function'?pickSel('c_bone'):'')||'')+' '
          +(((document.getElementById('c_bone_x')||{}).value)||'');
      if(/गर्दन/.test(b)) s.push('the bone chosen is the neck (गर्दन)');
 }catch(_e){}
 return s;
}

function cp11Check(){
 var p=cp11Proc(); if(!p) return null;
 var sig=cp11FxSignals(); if(!sig.length) return null;
 if(!CP11_ELECTIVE[p.k]) return null;
 return {proc:p,signals:sig,suggest:(CP11_SUGGEST[p.k]||[])};
}

function cp11Use(k){
 var s=document.getElementById('cs_proc'); if(!s) return;
 s.value=k; window.cpProcTouched=true; window.cp11Ok=null;
 try{ s.dispatchEvent(new Event('change')); }catch(_e){}
 cp11Status();
}

function cp11Override(){
 var p=cp11Proc(); if(!p) return;
 window.cp11Ok=p.k;
 var n=document.getElementById('cs_change_note');
 var mark='[opening-guard overridden: '+p.k+']';
 if(n && String(n.value||'').indexOf(mark)<0) n.value=(n.value?n.value+' ':'')+mark;
 cp11Status();
 try{ csGenerate(); }catch(_e){}
}

function cp11Status(){
 var box=document.getElementById('cp11_strip'); if(!box) return;
 var p=cp11Proc(), sig=cp11FxSignals(), bad=cp11Check();
 var pn=p?(p.hi+' — '+p.en):'—';
 if(bad){
  var btns=bad.suggest.map(function(k){
    var q=CONSENT_LIB.find(function(x){return x.k===k;});
    return q?('<button type="button" class="cbtn" style="padding:4px 10px;font-size:12.5px;margin:3px 5px 0 0" onclick="cp11Use(\'' + k + '\')">'+cp11Esc(q.hi)+'</button>'):'';
  }).join('');
  box.style.cssText=CP11_BAD;
  box.innerHTML='<b>⛔ यह मेल नहीं खा रहा — the opening does not match the case</b>'
   +'<div style="margin-top:5px">Chosen opening: <b>'+cp11Esc(pn)+'</b> — this template narrates a <b>long-standing / worn-out</b> problem, not an injury.</div>'
   +'<div style="margin-top:4px">The case says fracture: <b>'+sig.map(cp11Esc).join(' · ')+'</b></div>'
   +(btns?('<div style="margin-top:6px">Use instead: '+btns+'</div>'):'')
   +'<div style="margin-top:7px"><button type="button" class="cbtn ghost" style="padding:3px 9px;font-size:12px" onclick="cp11Override()">My choice is right — generate anyway</button> <span style="color:var(--muted);font-size:11.5px">(written into the change note)</span></div>';
 } else if(sig.length){
  box.style.cssText=CP11_OK;
  box.innerHTML='<b>✓ Fracture case.</b> Opening: <b>'+cp11Esc(pn)+'</b>. Reading: '+sig.map(cp11Esc).join(' · ');
 } else {
  box.style.cssText=CP11_OK;
  box.innerHTML='Opening: <b>'+cp11Esc(pn)+'</b> — no fracture module is ticked, so this prints as a planned (non-injury) case.';
 }
}

(function(){
 var cm=document.getElementById('caseModal'); if(!cm) return;
 var t=null;
 function ping(e){
  try{ if(e&&e.target&&e.target.id==='cs_proc') window.cp11Ok=null; }catch(_e){}
  if(t) clearTimeout(t);
  t=setTimeout(function(){ try{ cp11Status(); }catch(_e){} },120);
 }
 cm.addEventListener('change',ping,true);
 cm.addEventListener('input',ping,true);
 cm.addEventListener('click',ping,true);
 try{ cp11Status(); }catch(_e){}
})();

/* ---- polio module UI ---- */'''


def main():
    base_fp, out_fp = sys.argv[1], sys.argv[2]
    src = open(base_fp, encoding="utf-8").read()
    got = hashlib.md5(open(base_fp, "rb").read()).hexdigest()
    assert got == BASE_MD5, "BASE MISMATCH: expected %s got %s" % (BASE_MD5, got)

    n = [0]
    def patch(old, new, label):
        c = src_ref[0].count(old)
        assert c == 1, "ANCHOR FAIL (%s): found %d, expected 1" % (label, c)
        src_ref[0] = src_ref[0].replace(old, new)
        n[0] += 1
    src_ref = [src]

    patch(A1, STRIP,        "G1 status strip above Generate")
    patch(A2, GUARD_IN_GEN, "G2 refusal inside csGenerate")
    patch(A3, GUARD_JS,     "G3 guard functions + wiring")

    out = src_ref[0]
    open(out_fp, "w", encoding="utf-8", newline="").write(out)
    print("patches applied: %d" % n[0])
    print("base  md5: %s" % got)
    print("out   md5: %s" % hashlib.md5(out.encode("utf-8")).hexdigest())
    print("bytes: %d -> %d (+%d)" % (len(src.encode('utf-8')), len(out.encode('utf-8')),
                                     len(out.encode('utf-8'))-len(src.encode('utf-8'))))

if __name__ == "__main__":
    main()
