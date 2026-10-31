#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s684.py -- kit S684_CONSENT_ANKLE_STAGED (the parent, session S371, 31-Oct-2026).

Builds the new Case Pack page from the LIVE bytes (/root/wa/casepack/casepack_page.html 26cba6b1, S680's TO) by nine
anchored edits, each anchor required exactly once (F-472: no patcher from an inferred anchor). Prints the TO md5.

  python3 make_s684.py FROM.html TO.html

The owner, 31-Oct-2026 08:20-08:47 IST: a proximal humerus fracture with a medial and a posterior malleolus fracture and
ankle subluxation; an external fixator on the ankle now, definitive fixation later; "for ankle fractures how about a
selector for the malleoli and subluxation, so can tick the ones patients has"; "definitive fixation can be screws and
wires also, plates are not used always"; "proceed with this feature build now".
"""
import hashlib
import sys

FROM_MD5 = "26cba6b11a21f1bf6a5062f6084314a6"

E1_ANCHOR = '    <div id="polioWrap" style='
E1_NEW = (
    '    <div id="s684_ank" style="display:none;border:2px solid #2bb3a3;border-radius:12px;padding:10px 14px;margin:8px 0;background:rgba(43,179,163,.08)">\n'
    '      <div style="font-weight:800;color:#5fd3c4;font-size:14px;margin-bottom:6px">Ankle — the bones, the joint, the plan</div>\n'
    '      <div class="s684g">\n'
    '        <div><h5>Bones broken</h5>\n'
    '          <label class="fmo"><input type="checkbox" id="ank_med" onchange="s684Sync()"><span>Inner — medial malleolus</span></label>\n'
    '          <label class="fmo"><input type="checkbox" id="ank_lat" onchange="s684Sync()"><span>Outer — lateral malleolus / fibula</span></label>\n'
    '          <label class="fmo"><input type="checkbox" id="ank_post" onchange="s684Sync()"><span>Back — posterior malleolus</span></label></div>\n'
    '        <div><h5>The joint</h5>\n'
    '          <label class="fmo"><input type="radio" name="ank_jt" value="" checked onchange="s684Sync()"><span>In place</span></label>\n'
    '          <label class="fmo"><input type="radio" name="ank_jt" value="sub" onchange="s684Sync()"><span>Subluxation — partly out of place</span></label>\n'
    '          <label class="fmo"><input type="radio" name="ank_jt" value="dis" onchange="s684Sync()"><span>Dislocation — fully out of place</span></label></div>\n'
    '        <div id="s684_stage_slot"></div>\n'
    '        <div><h5>Fixed with</h5>\n'
    '          <label class="fmo"><input type="checkbox" id="ank_fw_plate" onchange="s684Sync()"><span>Plate-screws</span></label>\n'
    '          <label class="fmo"><input type="checkbox" id="ank_fw_screw" onchange="s684Sync()"><span>Screws only</span></label>\n'
    '          <label class="fmo"><input type="checkbox" id="ank_fw_wire" onchange="s684Sync()"><span>Wires (K-wire / tension band)</span></label>\n'
    '          <div style="font-size:11px;color:var(--muted)">None ticked = “screws, wires or plate, as suitable”</div></div>\n'
    '      </div>\n'
    '      <div id="s684_sum" style="margin-top:6px;font-size:12.5px;font-weight:700;color:#5fd3c4"></div>\n'
    '    </div>\n'
)

E2_ANCHOR = '    <div>\n      <h5>Comminuted</h5>'
E2_NEW = (
    '    <div id="s684_stagebox">\n'
    '      <h5>Plan now</h5>\n'
    '      <label class="fmo"><input type="radio" name="fm_stage" value="" checked onchange="s684Sync()"><span>Fix now (one operation)</span></label>\n'
    '      <label class="fmo"><input type="radio" name="fm_stage" value="exfix" onchange="s684Sync()"><span>External fixator now, fix later</span></label>\n'
    '      <div id="s684_stage_note" class="fmsub" style="display:none;font-size:11.5px;color:var(--muted)">Open fracture: the plan is the pathway chosen in the open-fracture box.</div>\n'
    '    </div>\n'
)

E3_OLD = ("{k:'ankle',en:'Ankle — bimalleolar',hi:'गट्टे (टखने) की हड्डियाँ',\n"
          " o:'{P} {NAME}, उम्र लगभग {AGE} वर्ष, {RELM} {RELN}{RES}, के {SIDE} पैर के गट्टे (टखने) की हड्डियाँ {DUR} टूट गई हैं, "
          "जिन्हें ऑपरेशन द्वारा प्लेट-पेंच से जोड़ा जाएगा। '+CS_CONSULT,")
E3_NEW = ("{k:'ankle',en:'Ankle fracture — tick the bones, joint and plan',hi:'गट्टे (टखने) की हड्डियाँ',\n"
          " o:'{P} {NAME}, उम्र लगभग {AGE} वर्ष, {RELM} {RELN}{RES}, के {SIDE} पैर के गट्टे (टखने) की हड्डियाँ {DUR} टूट गई हैं। '+CS_CONSULT,")

E4_OLD = " if(/हड्डियाँ/.test(v.LIMB||'')) paras[paras.length-1]=paras[paras.length-1].replace('टूट गई है','टूट गई हैं');"
E4_NEW = " if(/हड्डियाँ/.test(v.LIMB||'') && !(proc.k==='ankle' && typeof s684Ank==='function' && s684Ank().bones.length)) paras[paras.length-1]=paras[paras.length-1].replace(/टूट गई है(?!ं)/,'टूट गई हैं');  /* S684: an opening already plural is left alone; the ankle's ticks decide its own number */"

E5_OLD = "    if(q) sx.value=q.en||'';"
E5_NEW = "    if(q) sx.value=((typeof s684ProcEn==='function')?s684ProcEn(q):q.en)||'';"

E6_OLD = '"गट्टे (टखने)": ["टखने की हड्डी", "टखने की दोनों हड्डियाँ", "एड़ी की हड्डी"]'
E6_NEW = ('"गट्टे (टखने)": ["टखने की हड्डी", "टखने की दोनों हड्डियाँ", "टखने की तीनों हड्डियाँ", '
          '"टखने की अंदर की हड्डी (medial malleolus)", "टखने की बाहर की हड्डी (lateral malleolus)", '
          '"टखने की पीछे की हड्डी (posterior malleolus)", "एड़ी की हड्डी"]')

E7_OLD = "    +cb('fx_o','<b>open</b>',d.o)+cb('fx_n','op now',d.n)"
E7_NEW = "    +cb('fx_o','<b>open</b>',d.o)+cb('fx_n','op now',d.n)+cb('fx_pl','plan later',d.pl)"

E8_OLD = "o:ck('fx_o')?1:0,g:g('fx_g'),pth:g('fx_pth'),n:ck('fx_n')?1:0,"
E8_NEW = "o:ck('fx_o')?1:0,g:g('fx_g'),pth:g('fx_pth'),n:ck('fx_n')?1:0,pl:ck('fx_pl')?1:0,"

E9_ANCHOR = "@media print{.csfix{display:none!important}}</style>\n</body>"
E9_SCRIPT = r"""<style>
/* S684 -- the ankle box and the plan-now box */
#s684_ank .s684g{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:3px 14px;align-items:start}
#s684_ank h5,#s684_stagebox h5{margin:4px 0 3px;font-size:12.5px;color:#5fd3c4;font-weight:800}
#fmGrid #s684_stagebox h5{color:#7c3f06}
</style>
<script>
/* ===== S684 (31-Oct-2026) -- the ankle's own selector, and the staged plan on a CLOSED fracture ======================
   THE OWNER: a proximal humerus fracture with a medial and a posterior malleolus fracture and ankle subluxation; an
   external fixator on the ankle now, definitive fixation later. "for ankle fractures how about a selector for the malleoli
   and subluxation, so can tick the ones patients has" -- "definitive fixation can be screws and wires also, plates are not
   used always". Until now the ankle opening promised plate-screws, and the external fixator printed only as an open-
   fracture pathway.
   (1) Ankle: which malleoli, the joint, fixed-with -- the opening is built from the ticks.
   (2) Plan now: fix now / external fixator now, fix later -- for any closed fracture (not on the planned operations:
       replacements, ACL, implant removal and the like); the two-stage paragraph, its risks and the scope ("this consent
       is for the first stage") print from it. An open fracture keeps its own pathway and this box stands aside.
       (Plaster/slab now was left out at the cold review: the rest of the consent speaks of an operation.)
   (3) An additional fracture can be marked "plan later" -- with or without an operation, decided later.
   Every function here wraps a base one; nothing in the base is rewritten by this block. */
var S684_BONE={med:'अंदर की ओर की हड्डी (medial malleolus)', lat:'बाहर की ओर की हड्डी (lateral malleolus / fibula)',
               post:'पीछे की ओर की हड्डी (posterior malleolus)'};
var S684_FW1={plate:'प्लेट-पेंच', screw:'पेंच (screws)', wire:'तार (K-wire / tension band)'};
var S684_FWN={plate:'प्लेट', screw:'पेंच', wire:'तार'};
var S684_FW0='पेंच, तार या प्लेट (जो ऑपरेशन के समय उचित हो)';
var S684_ELECT={thr:1,thrneck:1,tkr:1,hemi:1,thr_fnf:1,acl:1,cubitus:1,implrem:1,osteo:1,hallux:1,amput:1};   /* no 'plan now' on these */
var S684_PLANHEAD='इलाज की योजना:';
var S684_WHY='डॉक्टर साहब ने हमें समझाया है कि अभी सूजन और चोट की स्थिति के कारण सीधे हड्डी जोड़ने का पक्का ऑपरेशन करना सुरक्षित नहीं है। इसलिए इलाज दो चरणों में किया जाएगा — ';
var S684_LATER='दूसरे चरण का समय सूजन, खाल की स्थिति और मरीज की हालत देखकर तय किया जाएगा।';
var S684_RISK={
 exfix:{h:'शिकंजे (बाहरी फिक्सेटर) से जुड़े जोखिम',
  t:'शिकंजे की पिनों की जगह इन्फेक्शन (मैल पड़ना) हो सकता है या पिन ढीली हो सकती है, इसलिए पिनों की नियमित सफाई और देखभाल जरूरी है — यह मरीज और परिवार की भी जिम्मेदारी है। सूजन के कारण चोट की जगह पर फफोले पड़ सकते हैं, और दूसरा ऑपरेशन खाल ठीक होने तक टल सकता है। दूसरे ऑपरेशन के अपने अलग जोखिम और खर्च होते हैं।'},
 joint:{h:'जोड़ तक पहुँची चोट से जुड़े जोखिम',
  t:'टखने के जोड़ तक पहुँची इस चोट में आगे चलकर टखने में अकड़न, दर्द या जोड़ घिसने (arthritis) की संभावना रहती है।'},
 jointout:' जोड़ खिसका होने पर उसे जल्दी अपनी जगह बैठाना जरूरी होता है; देर होने पर खाल और नसों पर दबाव का खतरा रहता है।'
};
var S684_PLATERHEAD='शेष हड्डियों की योजना:';
var S684_PLATER=' का इलाज ऑपरेशन द्वारा होगा या बिना ऑपरेशन, यह मरीज की स्थिति और चोट देखकर उचित समय पर तय किया जाएगा, और ऑपरेशन की आवश्यकता होने पर उसके लिए अलग से सहमति ली जाएगी।';
var S684_SCOPEALL='इस सहमति-पत्र में मरीज की सभी टूटी हड्डियों तथा चोटों की जानकारी और उनके इलाज की योजना दर्ज है। ';

function s684Proc(){ return ((document.getElementById('cs_proc')||{}).value||''); }
function s684Ck(id){ var e=document.getElementById(id); return !!(e&&e.checked); }
function s684Rad(n){ var r=document.querySelector('input[name='+n+']:checked'); return r?r.value:''; }
function s684Ank(){
 var b=[]; ['med','lat','post'].forEach(function(k){ if(s684Ck('ank_'+k)) b.push(k); });
 var fw=[]; ['plate','screw','wire'].forEach(function(k){ if(s684Ck('ank_fw_'+k)) fw.push(k); });
 return {bones:b, jt:s684Rad('ank_jt'), fw:fw};
}
function s684Open(){ try{ return !!(fmVals().compound); }catch(_e){ return false; } }
function s684Stage(){
 if(s684Open() || S684_ELECT[s684Proc()]) return '';
 return s684Rad('fm_stage')==='exfix' ? 'exfix' : '';
}
function s684FW(a){
 if(!a||!a.fw.length) return S684_FW0;
 if(a.fw.length===1) return S684_FW1[a.fw[0]];
 var n=a.fw.map(function(k){return S684_FWN[k];});
 return n.slice(0,-1).join(', ')+' या '+n[n.length-1];
}
function s684Join(list){
 if(list.length<2) return list.join('');
 return list.slice(0,-1).join(', ')+' और '+list[list.length-1];
}
/* the opening for the ankle -- the bones sentence always ends in "टूट गई है(ं)।" so the open-fracture rewrite still finds it */
function s684AnkleOpening(){
 var a=s684Ank(), st=s684Stage(), n=a.bones.length;
 var t='{P} {NAME}, उम्र लगभग {AGE} वर्ष, {RELM} {RELN}{RES}, के {SIDE} पैर के गट्टे (टखने) की ';
 t+= n ? (s684Join(a.bones.map(function(k){return S684_BONE[k];}))+' {DUR} '+(n===1?'टूट गई है।':'टूट गई हैं।'))
       : 'हड्डियाँ {DUR} टूट गई हैं।';
 if(a.jt==='sub') t+=' टखने का जोड़ भी अपनी जगह से आंशिक रूप से खिसक गया है (subluxation)।';
 if(a.jt==='dis') t+=' टखने का जोड़ भी अपनी जगह से पूरी तरह खिसक गया है (dislocation)।';
 var pth=''; try{ pth=s684Open()?(fmVals().path||''):''; }catch(_e){}
 if(!st && pth!=='A' && pth!=='C') t+=' '+(n===1?'इसे':'इन्हें')+' ऑपरेशन करके '+s684FW(a)+' द्वारा जोड़ा जाएगा।';   /* an open fracture with plaster-first or a fixator first never promises fixation now */
 return t+' '+CS_CONSULT;
}
function s684ProcEn(q){
 if(!q||q.k!=='ankle') return q?q.en:'';
 var a=s684Ank(), st=s684Stage(), n=a.bones.length;
 var nm={med:'medial',lat:'lateral',post:'posterior'};
 var kind= n===3?'Trimalleolar':(n===2?'Bimalleolar':(n===1?('Isolated '+nm[a.bones[0]]+' malleolus'):'Ankle'));
 var s='Ankle fracture — '+kind+(n===2?(' ('+a.bones.map(function(k){return nm[k];}).join(' + ')+')'):'');
 if(a.jt==='sub') s+=', subluxation'; if(a.jt==='dis') s+=', dislocation';
 s+= st==='exfix'?' — external fixator now, fixation later':
     (' — fixation ('+(a.fw.length?a.fw.map(function(k){return {plate:'plate-screws',screw:'screws',wire:'wires'}[k];}).join(' / '):'screws, wires or plate')+')');
 return s;
}
function s684Sync(){
 var ank=(s684Proc()==='ankle'), box=document.getElementById('s684_ank'), sb=document.getElementById('s684_stagebox');
 if(box) box.style.display=ank?'block':'none';
 if(sb){
   var want=ank?document.getElementById('s684_stage_slot'):document.getElementById('fmGrid');
   if(want && sb.parentNode!==want){
     if(ank) want.appendChild(sb);
     else { var ref=null; try{ ref=document.querySelector('#fmGrid > div:nth-child(3)'); }catch(_e){} want.insertBefore(sb, ref); }
   }
   var open=s684Open();
   sb.style.display=S684_ELECT[s684Proc()]?'none':'';
   [].forEach.call(sb.querySelectorAll('input[name=fm_stage]'),function(r){ r.disabled=open; r.parentElement.style.opacity=open?'0.45':''; });
   var nt=document.getElementById('s684_stage_note'); if(nt) nt.style.display=open?'block':'none';
 }
 var sm=document.getElementById('s684_sum');
 if(sm) sm.textContent=ank?('Reads as: '+s684ProcEn({k:'ankle'})):'';
}
/* ---- wrappers ---- */
(function(){
 /* the ankle's opening: the library entry's template is READ from the ticks at the moment the generator reads it -- nothing
    is swapped or put back, so overlapping runs (a double tap, the language button) can never leave a wrong template; the
    base fills and transliterates its tokens exactly as before. If the builder ever fails, the entry's own text is used. */
 var ANK=CONSENT_LIB.find(function(x){return x.k==='ankle';});
 if(ANK){ var ANK_O=ANK.o;
   try{ Object.defineProperty(ANK,'o',{configurable:true, enumerable:true,
          get:function(){ try{ return s684AnkleOpening(); }catch(_e){ return ANK_O; } }, set:function(_v){} }); }catch(_e){} }
 var _mid=fmMidBlocks;
 fmMidBlocks=function(){
  var out=_mid(), st=s684Stage();
  var v=null; try{ v=fmVals(); }catch(_e){}
  if(st){
    var ank=(s684Proc()==='ankle'), a=s684Ank(), n=a.bones.length;
    var what= ank ? (a.jt ? 'टखने के जोड़ और हड्डियों' : (n===1?'टखने की हड्डी':'टखने की हड्डियों')) : 'हड्डी';
    var obj= ank ? (n===1?'हड्डी':'हड्डियों') : 'हड्डी';
    var first=what+' को अपनी जगह बैठाकर बाहरी फिक्सेटर (external fixator / शिकंजा) लगाया जाएगा, और सूजन व खाल की स्थिति ठीक होने पर दूसरे चरण में शिकंजा निकालकर ';
    var second= ank ? (obj+' को '+s684FW(a)+' द्वारा जोड़ा जाएगा।') : 'हड्डी जोड़ने का पक्का ऑपरेशन किया जाएगा।';   /* another procedure's own opening already names its fixation */
    var plan='<b>'+S684_PLANHEAD+'</b> '+S684_WHY+'अभी पहले चरण में '+first+second+' '+S684_LATER;
    /* the scope: the base's multi-fracture scope is replaced by the staged one (never two scopes) */
    out=out.filter(function(b){ return String(b).indexOf('<b>'+FM_SCOPEHEAD+'</b>')!==0; });
    var where= ank ? 'टखने' : ((v&&v.plimb)?v.plimb:'हड्डी');
    var step=where+' में बाहरी फिक्सेटर (शिकंजा) लगाने';
    var also=[]; if(v&&v.multi) (v.fx||[]).forEach(function(f){ if(f.n) also.push(fxPhrase(f)); });
    var scope='<b>'+FM_SCOPEHEAD+'</b> '+((v&&v.multi)?S684_SCOPEALL:'')+'यह सहमति अभी किए जा रहे पहले चरण — '+step+' — के लिए दी जा रही है।'
      +(also.length?(' इसी बार '+also.join(' तथा ')+' का ऑपरेशन भी किया जा रहा है।'):'')
      +' दूसरे चरण के ऑपरेशन'+((v&&v.multi)?' तथा शेष हड्डियों के इलाज':'')+' के लिए अलग से सहमति ली जाएगी।';
    out.unshift(plan);
    out.push(scope);
  }
  if(v&&v.multi){
    var pl=(v.fx||[]).filter(function(f){ return f.pl && !f.n; }).map(fxPhrase);
    if(pl.length) out.push('<b>'+S684_PLATERHEAD+'</b> '+pl.join(' तथा ')+S684_PLATER);
  }
  return out;
 };
 var _risk=fmRiskPara;
 fmRiskPara=function(){
  var t=_risk(), st=s684Stage(), add=[];
  if(st&&S684_RISK[st]) add.push(S684_RISK[st]);
  if(s684Proc()==='ankle'){
    var a=s684Ank(), art=false; try{ art=!!fmVals().art; }catch(_e){}
    if(!art && (a.jt || a.bones.indexOf('post')>=0)) add.push({h:S684_RISK.joint.h, t:S684_RISK.joint.t+(a.jt?S684_RISK.jointout:'')});
  }
  if(!add.length) return t;
  var b=add.map(function(x){return '• <b>'+x.h+':</b> '+x.t;}).join('<br>');
  if(!t) return '<b>'+FM_RISKHEAD+'</b> '+FM_RISK_INTRO+'<br>'+b;
  var gi=t.indexOf('<br><br><b>'+GERI.h);
  if(t.indexOf(FM_RISK_INTRO)<0) return t.replace('<b>'+FM_RISKHEAD+'</b> ','<b>'+FM_RISKHEAD+'</b> '+FM_RISK_INTRO+'<br>'+b+'<br><br>');
  return gi>=0 ? (t.slice(0,gi)+'<br>'+b+t.slice(gi)) : (t+'<br>'+b);
 };
 var _sync=fmSync;
 fmSync=function(){ var r=_sync.apply(this,arguments); try{ s684Sync(); }catch(_e){} return r; };
 var _snap=csFieldsSnap;
 csFieldsSnap=function(){ var f=_snap();
  try{ var a=s684Ank(); f.s684={stage:s684Rad('fm_stage'), bones:a.bones, jt:a.jt, fw:a.fw}; }catch(_e){}
  return f; };
 var _rest=csFieldsRestore;
 csFieldsRestore=function(f){ var r=_rest(f);
  try{
   var s=(f&&f.s684)||{};
   ['med','lat','post'].forEach(function(k){ var e=document.getElementById('ank_'+k); if(e) e.checked=(s.bones||[]).indexOf(k)>=0; });
   ['plate','screw','wire'].forEach(function(k){ var e=document.getElementById('ank_fw_'+k); if(e) e.checked=(s.fw||[]).indexOf(k)>=0; });
   var j=document.querySelector('input[name=ank_jt][value="'+(s.jt||'')+'"]'); if(j) j.checked=true;
   var g=document.querySelector('input[name=fm_stage][value="'+(s.stage||'')+'"]'); if(g) g.checked=true;
   s684Sync();
  }catch(_e){}
  return r; };
 try{ var ps=document.getElementById('cs_proc'); if(ps) ps.addEventListener('change',function(){ try{ s684Sync(); }catch(_e){} }); }catch(_e){}
 /* 'external fixator now' means the primary fracture is treated now; un-ticking 'operated now' takes the plan back to fix now */
 try{ document.addEventListener('change',function(e){ var t=e.target; if(!t) return;
   if(t.name==='fm_stage' && t.value==='exfix' && t.checked){ var op=document.getElementById('fm_opnow'); if(op && !op.checked){ op.checked=true; try{ fmSync(); }catch(_e){} } }
   if(t.id==='fm_opnow' && !t.checked){ var z=document.querySelector('input[name=fm_stage][value=""]'); if(z && !z.checked){ z.checked=true; try{ s684Sync(); }catch(_e){} } }
   if(t.classList && (t.classList.contains('fx_n')||t.classList.contains('fx_pl')) && t.checked){   /* 'op now' and 'plan later' exclude each other */
     var row=t.closest('.fxrow'), other=row&&row.querySelector(t.classList.contains('fx_n')?'.fx_pl':'.fx_n'); if(other) other.checked=false; }
 }, true); }catch(_e){}
 try{ s684Sync(); }catch(_e){}
})();
/* S684 end */
</script>
"""


def edit(s, old, new, label):
    n = s.count(old)
    if n != 1:
        sys.exit("!! %s: the anchor occurs %d times (exactly 1 needed) -- nothing written" % (label, n))
    return s.replace(old, new, 1)


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: make_s684.py FROM.html TO.html")
    raw = open(sys.argv[1], "rb").read()
    if hashlib.md5(raw).hexdigest() != FROM_MD5:
        sys.exit("!! the FROM file is %s, not the pinned %s -- nothing written" % (hashlib.md5(raw).hexdigest(), FROM_MD5))
    s = raw.decode("utf-8")
    s = edit(s, E1_ANCHOR, E1_NEW + E1_ANCHOR, "E1 the ankle box")
    s = edit(s, E2_ANCHOR, E2_NEW + E2_ANCHOR, "E2 the plan-now box")
    s = edit(s, E3_OLD, E3_NEW, "E3 the ankle opening no longer promises plates")
    s = edit(s, E4_OLD, E4_NEW, "E4 the plural guard")
    s = edit(s, E5_OLD, E5_NEW, "E5 the OT note's procedure name")
    s = edit(s, E6_OLD, E6_NEW, "E6 the ankle's bone list")
    s = edit(s, E7_OLD, E7_NEW, "E7 plan later on an additional fracture")
    s = edit(s, E8_OLD, E8_NEW, "E8 plan later collected")
    s = edit(s, E9_ANCHOR, E9_ANCHOR.replace("</body>", E9_SCRIPT + "</body>"), "E9 the S684 block")
    out = s.encode("utf-8")
    open(sys.argv[2], "wb").write(out)
    print("S684 TO %s (%d bytes, 9 counted edits)" % (hashlib.md5(out).hexdigest(), len(out)))


if __name__ == "__main__":
    main()
