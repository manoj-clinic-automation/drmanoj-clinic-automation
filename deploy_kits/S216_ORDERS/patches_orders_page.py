#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patches_orders_page.py - S216 orders build, PAGE side
======================================================
Base = the S216 tone page (LIVE, pin 63b2cba4...).
Three ANCHORED patches.

THE OWNER'S RULINGS (MY_TEMPLATES_S216.txt + his answers, 01-Sep-2026):
  * He enters the SURGERY TIME once; every time on all three sheets is
    computed from it and stays editable before he forwards it.
      pre-op  nil orally FROM  = surgery - 6 h      (his own figure)
      post-op nil orally TILL  = that time + 13 h   (his own figure)
  * Slashes become DROPDOWNS fed from a list he maintains himself, with route
    and frequency, marked for Ayushman and package cases. Marked ones sort to
    the TOP; nothing is hidden - at a bedside he must still reach anything.
  * Renumbered; IV fluid is item 1.
  * Monitoring is tick-boxes, plus RBS by glucometer 8-hourly / SOS.
  * OT note header is two editable fields only: Diagnosis, Surgery done.
  * English, Title Case.
  * No per-operation variants - the payer marking does that job.

The composed sheet lands in the SAME textarea as before, so Copy, WhatsApp,
Print and Reset keep working untouched, and he can still type over anything.
"""
import sys, hashlib

BASE_MD5 = "63b2cba422464a35f6d50db8bd9c0eb3"

A_PANES_START = '<div class="casepane" id="pane_preop">'
A_PANES_END   = '<div class="casepane" id="pane_cases">'

NEW_PANES = r'''<div class="casepane" id="pane_preop">
    <div class="casehint">Set the surgery date and time once — every time on all three sheets is worked out from it, and stays editable.</div>
    <div class="opbar">
      <label>Surgery date <input type="date" id="op_date"></label>
      <label>Time <input type="time" id="op_time"></label>
      <span id="op_derived" class="opderived"></span>
    </div>
    <div style="margin:8px 0"><button class="cbtn" id="preop_build">Build pre-op sheet</button></div>
    <textarea class="docbox" id="preop_tx"></textarea>
    <div style="margin-top:8px"><button class="cbtn" id="preop_wa">WhatsApp</button><button class="cbtn" id="preop_cp">Copy</button><button class="cbtn ghost" id="preop_pr">Print</button><button class="cbtn ghost" id="preop_reset">Reset template</button></div>
  </div>

  <div class="casepane" id="pane_postop">
    <div class="casehint">Pick what applies, then build. The medicine list is yours — add, remove and mark items with “Edit list”.</div>
    <div class="opbar">
      <span id="op_derived2" class="opderived"></span>
      <button class="cbtn ghost" id="med_edit" style="margin-left:auto">Edit list</button>
    </div>
    <div class="ordgrid">
      <div class="ordcol"><h5>1 · IV fluid</h5><div id="med_fluid"></div></div>
      <div class="ordcol"><h5>2 · Medicines</h5><div id="med_pick"></div></div>
      <div class="ordcol"><h5>3 · Monitoring</h5><div id="mon_pick"></div></div>
    </div>
    <div style="margin:8px 0"><button class="cbtn" id="postop_build">Build post-op sheet</button>
      <span id="med_msg" style="font-size:12px;color:var(--muted);margin-left:8px"></span></div>
    <textarea class="docbox" id="postop_tx"></textarea>
    <div style="margin-top:8px"><button class="cbtn" id="postop_wa">WhatsApp</button><button class="cbtn" id="postop_cp">Copy</button><button class="cbtn ghost" id="postop_pr">Print</button><button class="cbtn ghost" id="postop_reset">Reset template</button></div>
    <div id="med_editor" style="display:none;margin-top:10px;border:1px solid var(--line2,#5A706E);border-radius:10px;padding:10px">
      <div style="font-weight:700;margin-bottom:6px">Your medicine list</div>
      <div id="med_rows" style="max-height:40vh;overflow:auto"></div>
      <div class="medadd">
        <input id="med_new" placeholder="Medicine / fluid name">
        <select id="med_new_route"><option value="">route</option><option>IV</option><option>Oral</option><option>IM</option><option>SC</option><option>Local</option></select>
        <select id="med_new_freq"><option value="">frequency</option><option>OD</option><option>BD</option><option>TDS</option><option>QID</option><option>SOS</option><option>STAT</option></select>
        <button class="cbtn ghost" id="med_add">Add</button>
      </div>
      <div style="margin-top:8px"><button class="cbtn" id="med_save">Save list</button>
        <span style="font-size:11.5px;color:var(--muted);margin-left:8px">Saved on the server — the same list on every device. The previous version is always kept.</span></div>
    </div>
  </div>

  <div class="casepane" id="pane_opnote">
    <div class="casehint">Diagnosis and surgery are filled in from the case — change either, then build.</div>
    <div class="opbar">
      <label style="flex:1">Diagnosis <input id="ot_dx" style="width:100%"></label>
      <label style="flex:1">Surgery done <input id="ot_sx" style="width:100%"></label>
    </div>
    <div style="margin:8px 0"><button class="cbtn" id="opnote_build">Build OT note</button></div>
    <textarea class="docbox" id="opnote_tx"></textarea>
    <div style="margin-top:8px"><button class="cbtn" id="opnote_wa">WhatsApp</button><button class="cbtn" id="opnote_cp">Copy</button><button class="cbtn ghost" id="opnote_pr">Print</button><button class="cbtn ghost" id="opnote_reset">Reset template</button></div>
  </div>

  '''

A_STYLE = ".docbox{width:100%;min-height:230px"
N_STYLE = (".opbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:6px 0;"
           "background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 10px}\n"
           ".opbar label{font-size:13px;color:var(--muted);display:flex;align-items:center;gap:6px}\n"
           ".opbar input,.opbar select{padding:6px 9px;border:1px solid var(--blue);border-radius:8px;"
           "background:var(--bg);color:var(--ink);font-family:inherit;font-size:13.5px}\n"
           ".opderived{font-size:12.5px;color:var(--green);font-weight:600}\n"
           ".ordgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin:8px 0}\n"
           ".ordcol{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 10px}\n"
           ".ordcol h5{margin:0 0 6px;font-size:12px;text-transform:uppercase;letter-spacing:.3px;color:var(--muted)}\n"
           ".ordcol label{display:flex;gap:7px;align-items:flex-start;font-size:13px;margin:3px 0;cursor:pointer}\n"
           ".ordcol .mk{font-size:10px;font-weight:700;border-radius:4px;padding:0 4px;margin-left:3px}\n"
           ".ordcol .mk.a{background:rgba(116,194,149,.22);color:var(--green)}\n"
           ".ordcol .mk.p{background:rgba(224,179,106,.22);color:var(--warn)}\n"
           ".medadd{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}\n"
           ".medadd input,.medadd select{padding:6px 9px;border:1px solid var(--line2,#5A706E);"
           "border-radius:8px;background:var(--bg);color:var(--ink);font-family:inherit;font-size:13px}\n"
           ".medrow{display:flex;gap:6px;align-items:center;font-size:13px;padding:3px 0;"
           "border-bottom:1px solid var(--line)}\n"
           ".medrow .nm{flex:1;min-width:0}\n"
           ".docbox{width:100%;min-height:230px")


A_OPEN = """   otRebuild();
   cm.classList.add('open'); try{updateEstPreview();}catch(_e){}"""

N_OPEN = r"""   otRebuild();
   try{ ordSync(); otPrefill(); medLoad(); }catch(_e){}
   cm.classList.add('open'); try{updateEstPreview();}catch(_e){}"""

A_WIRE = """ document.getElementById('closeCase').onclick=function(){"""

N_WIRE = r""" /* ---- S216 orders wiring ---- */
 (function(){
  function on(id,fn){ var e=document.getElementById(id); if(e) e.onclick=fn; }
  ['op_date','op_time'].forEach(function(id){
    var e=document.getElementById(id); if(e) e.addEventListener('change',ordSync); });
  on('preop_build', buildPreop);
  on('postop_build', buildPostop);
  on('opnote_build', function(){ otPrefill(); buildOpnote(); });
  on('med_edit', function(){
    var b=document.getElementById('med_editor');
    if(!b) return;
    var show=(b.style.display==='none');
    b.style.display=show?'block':'none';
    if(show) medEditorRender();
  });
  on('med_add', function(){
    var nm=document.getElementById('med_new');
    var it=(nm.value||'').trim(); if(!it) return;
    MEDS.push({Item:ordTitle(it),
      Route:(document.getElementById('med_new_route')||{}).value||'',
      Freq:(document.getElementById('med_new_freq')||{}).value||'',
      Ayushman:'',Package:'',Active:'1',
      Sort:String(900+MEDS.length)});
    nm.value=''; medEditorRender(); medRender();
  });
  var rowsBox=document.getElementById('med_rows');
  if(rowsBox) rowsBox.addEventListener('click',function(e){
    var b=e.target.closest('.mDel'); if(!b) return;
    var d=b.closest('.medrow'); var i=parseInt(d.getAttribute('data-i'),10);
    if(!isNaN(i)) MEDS.splice(i,1);
    medEditorRender(); medRender();
  });
  on('med_save', function(){
    var msg=document.getElementById('med_msg');
    var rows=medCollect();
    if(!rows.length){ if(msg) msg.textContent='Refused: the list would be empty.'; return; }
    if(msg) msg.textContent='Saving…';
    fetch('/portal/casepack/meds',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({rows:rows})}).then(function(r){return r.json();}).then(function(j){
        if(j&&j.ok){ if(msg) msg.textContent='Saved — '+j.count+' items, on every device.'; medLoad(); }
        else { if(msg) msg.textContent='Not saved: '+((j&&j.error)||'unknown'); }
      }).catch(function(){ if(msg) msg.textContent='Not saved — no answer from the server.'; });
  });
  var seg=document.getElementById('seg');
  if(seg) seg.addEventListener('click',function(){ setTimeout(medRender,0); },true);
 })();
 document.getElementById('closeCase').onclick=function(){"""

A_TPL = "const TPL_PREOP="

N_TPL = r'''/* ===== S216 orders build ==================================================
   His templates, his times, his list. Nothing here invents clinical content. */
function ordTitle(s){ return String(s||'').replace(/\w\S*/g,function(w){
  if(/^(IV|IM|SC|OD|BD|TDS|QID|SOS|STAT|OT|NBM|RBS|DNS|NS|PCM|MRI)$/i.test(w)) return w.toUpperCase();
  return w.charAt(0).toUpperCase()+w.slice(1).toLowerCase(); }); }
function ordPad(n){ return (n<10?'0':'')+n; }
function ordClock(mins){ mins=((mins%1440)+1440)%1440; return ordPad(Math.floor(mins/60))+':'+ordPad(mins%60); }
function ordDayShift(mins){ return mins<0?' (previous day)':(mins>=1440?' (next day)':''); }
/* THE OWNER'S OWN FIGURES: nil orally from surgery -6h; till that +13h. */
var ORD_PREOP_BEFORE_H = 6, ORD_POSTOP_AFTER_NIL_H = 13;
function ordTimes(){
 var d=(document.getElementById('op_date')||{}).value||'';
 var t=(document.getElementById('op_time')||{}).value||'';
 if(!t) return null;
 var p=t.split(':'), m=parseInt(p[0],10)*60+parseInt(p[1],10);
 var from=m-ORD_PREOP_BEFORE_H*60, till=from+ORD_POSTOP_AFTER_NIL_H*60;
 return {date:d, surgery:t, fromRaw:from, tillRaw:till,
         from:ordClock(from)+ordDayShift(from), till:ordClock(till)+ordDayShift(till)};
}
function ordDateStr(d){ return d? d.split('-').reverse().join('/') : '____'; }
function ordSync(){
 var x=ordTimes();
 var s = x ? ('Nil orally from '+x.from+'  ·  surgery '+x.surgery+'  ·  nil orally till '+x.till)
           : 'Enter the surgery time and all three sheets fill themselves.';
 ['op_derived','op_derived2'].forEach(function(id){
   var e=document.getElementById(id); if(e) e.textContent=s; });
}
/* ---- the owner's medicine list, from the server ---- */
var MEDS=[];
function medLoad(){
 return fetch('/portal/casepack/meds').then(function(r){return r.json();}).then(function(j){
   MEDS=(j&&j.ok&&j.rows)?j.rows:[]; medRender(); return MEDS;
 }).catch(function(){ MEDS=[]; medRender(); });
}
function medMark(r){
 return (r.Ayushman?'<span class="mk a">AY</span>':'')+(r.Package?'<span class="mk p">PKG</span>':'');
}
function medSorted(){
 var payer=window.cpPayer||'cash';
 var want = payer==='ayush' ? 'Ayushman' : (payer==='tpa' ? 'Package' : null);
 var rows=MEDS.filter(function(r){ return String(r.Active||'')==='1'; });
 return rows.slice().sort(function(a,b){
   /* marked for THIS payer float to the top - nothing is ever hidden */
   var am=want?(a[want]?0:1):0, bm=want?(b[want]?0:1):0;
   if(am!==bm) return am-bm;
   return (parseInt(a.Sort||'999',10)||999)-(parseInt(b.Sort||'999',10)||999);
 });
}
function medRender(){
 var fl=document.getElementById('med_fluid'), pk=document.getElementById('med_pick');
 if(!fl||!pk) return;
 var rows=medSorted();
 function line(r,i,grp){
   var lbl=r.Item+(r.Route?' '+r.Route:'')+(r.Freq?' '+r.Freq:'');
   return '<label><input type="checkbox" data-grp="'+grp+'" data-i="'+i+'"><span>'
     +lbl.replace(/&/g,'&amp;').replace(/</g,'&lt;')+medMark(r)+'</span></label>';
 }
 var f='',p='';
 rows.forEach(function(r,i){
   if(!r.Freq && String(r.Route||'').toUpperCase()==='IV') f+=line(r,i,'f');
   else p+=line(r,i,'p');
 });
 fl.innerHTML=f||'<span style="font-size:12px;color:var(--muted)">none in the list</span>';
 pk.innerHTML=p||'<span style="font-size:12px;color:var(--muted)">none in the list</span>';
 var mon=document.getElementById('mon_pick');
 if(mon && !mon.innerHTML){
   mon.innerHTML=ORD_MON.map(function(m,i){
     return '<label><input type="checkbox" data-mon="'+i+'"'+(m[1]?' checked':'')+'><span>'+m[0]+'</span></label>';
   }).join('');
 }
}
/* Monitoring lines - his list, plus the RBS line he asked for. */
var ORD_MON=[
 ['Vitals 2 Hourly',1],['Check Dressing And Drain',1],['Limb Elevation',1],
 ['Check Distal Circulation',1],['RBS By Glucometer 8 Hourly',0],['RBS By Glucometer SOS',0],
 ['Watch Pain, Bleeding, Urine Output',1],['Sips To Soft Diet Once Fully Awake',1],
 ['Physiotherapy / Mobilisation As Advised',0]
];
function medChecked(grp){
 var rows=medSorted(), out=[];
 [].forEach.call(document.querySelectorAll('#pane_postop input[data-grp="'+grp+'"]:checked'),
   function(c){ var r=rows[parseInt(c.getAttribute('data-i'),10)]; if(r) out.push(r); });
 return out;
}
/* ---- the three sheets ---- */
function buildPreop(){
 var x=ordTimes();
 var L=[];
 L.push('PRE-OP ORDERS — Dr. Manoj Agarwal');
 L.push('Surgery At '+(x?x.surgery:'____')+' On '+(x?ordDateStr(x.date):'( Date )'));
 L.push('');
 L.push('1. Nil Orally From '+(x?x.from:'____')+' ('+ORD_PREOP_BEFORE_H+' Hours Before Surgery)');
 L.push('2. Consent To Be Taken');
 L.push('3. Patient To Be Shifted To OT With All Investigations And Records, In Proper OT Dress');
 document.getElementById('preop_tx').value=L.join('\n');
}
function buildPostop(){
 var x=ordTimes(), n=1, L=[];
 L.push('POST-OP ORDERS — Dr. Manoj Agarwal');
 if(x) L.push('Surgery At '+x.surgery+' On '+ordDateStr(x.date));
 L.push('');
 var fl=medChecked('f');
 L.push((n++)+'. IV Fluid — '+(fl.length?fl.map(function(r){return r.Item;}).join(' / '):'____'));
 L.push((n++)+'. Nil Orally Till '+(x?x.till:'____'));
 medChecked('p').forEach(function(r){
   L.push((n++)+'. '+r.Item+(r.Route?' '+r.Route:'')+(r.Freq?' '+r.Freq:''));
 });
 var mon=[];
 [].forEach.call(document.querySelectorAll('#mon_pick input[data-mon]:checked'),function(c){
   mon.push(ORD_MON[parseInt(c.getAttribute('data-mon'),10)][0]); });
 if(mon.length){ L.push(''); L.push('Monitoring:'); mon.forEach(function(m){ L.push('  - '+m); }); }
 document.getElementById('postop_tx').value=L.join('\n');
}
function buildOpnote(){
 var x=ordTimes(), L=[];
 L.push('OPERATIVE NOTES — Dr. Manoj Agarwal');
 L.push('Diagnosis: '+((document.getElementById('ot_dx')||{}).value||'____'));
 L.push('Surgery Done: '+((document.getElementById('ot_sx')||{}).value||'____'));
 if(x) L.push('Date: '+ordDateStr(x.date)+'   Time: '+x.surgery);
 L.push('');
 L.push('Patient Laid Supine / Lateral / On Fracture Table');
 L.push('Painting And Draping Done');
 L.push('Closed / Open Reduction And Fracture Fixation Done');
 L.push('For Replacement Patients — Hip / Knee Replacement Done');
 L.push('Closure Done In Layers');
 L.push('');
 L.push('Surgeon: Dr. Manoj Agarwal (M.S. Ortho)');
 document.getElementById('opnote_tx').value=L.join('\n');
}
/* Diagnosis and surgery prefill from the case, and stay editable. */
function otPrefill(){
 var dx=document.getElementById('ot_dx'), sx=document.getElementById('ot_sx');
 if(!dx||!sx) return;
 try{
  var c=caseHeader();
  if(!dx.value){
    var p=CONSENT_LIB.find(function(z){return z.k===(document.getElementById('cs_proc')||{}).value;});
    dx.value=ordTitle([(c.side||''),(c.part||''),(c.bone||'')].filter(Boolean).join(' '))||'';
  }
  if(!sx.value){
    var q=CONSENT_LIB.find(function(z){return z.k===(document.getElementById('cs_proc')||{}).value;});
    if(q) sx.value=q.en||'';
  }
 }catch(_e){}
}
/* ---- the list editor ---- */
function medEditorRender(){
 var box=document.getElementById('med_rows'); if(!box) return;
 box.innerHTML=MEDS.map(function(r,i){
  return '<div class="medrow" data-i="'+i+'">'
   +'<span class="nm">'+String(r.Item).replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</span>'
   +'<span style="color:var(--muted);font-size:12px">'+(r.Route||'')+' '+(r.Freq||'')+'</span>'
   +'<label style="font-size:12px"><input type="checkbox" class="mAy"'+(r.Ayushman?' checked':'')+'> AY</label>'
   +'<label style="font-size:12px"><input type="checkbox" class="mPk"'+(r.Package?' checked':'')+'> PKG</label>'
   +'<button class="cbtn ghost mDel" style="padding:2px 8px;font-size:12px">remove</button></div>';
 }).join('')||'<div style="color:var(--muted);font-size:12.5px">empty</div>';
}
function medCollect(){
 var out=[];
 [].forEach.call(document.querySelectorAll('#med_rows .medrow'),function(d){
   var i=parseInt(d.getAttribute('data-i'),10), r=MEDS[i]; if(!r) return;
   out.push({Item:r.Item,Route:r.Route,Freq:r.Freq,
     Ayushman:d.querySelector('.mAy').checked?'1':'',
     Package:d.querySelector('.mPk').checked?'1':'',
     Active:'1', Sort:r.Sort||''});
 });
 return out;
}
const TPL_PREOP='''


def main():
    base_fp, out_fp = sys.argv[1], sys.argv[2]
    src = open(base_fp, encoding="utf-8").read()
    got = hashlib.md5(open(base_fp, "rb").read()).hexdigest()
    assert got == BASE_MD5, "BASE MISMATCH: expected %s got %s" % (BASE_MD5, got)
    n = [0]; ref = [src]

    i = ref[0].index(A_PANES_START); j = ref[0].index(A_PANES_END)
    old = ref[0][i:j]
    assert old.count('id="preop_tx"') == 1 and old.count('id="opnote_tx"') == 1, "panes not as expected"
    ref[0] = ref[0][:i] + NEW_PANES + ref[0][j:]; n[0] += 1
    print("  P1 three order panes rebuilt: %d chars -> %d" % (len(old), len(NEW_PANES)))

    def patch(o, w, label):
        c = ref[0].count(o)
        assert c == 1, "ANCHOR FAIL (%s): found %d" % (label, c)
        ref[0] = ref[0].replace(o, w); n[0] += 1
    patch(A_STYLE, N_STYLE, "P2 styles")
    patch(A_TPL,   N_TPL,   "P3 the builders")
    patch(A_OPEN,  N_OPEN,  "P4 load the list when the case opens")
    patch(A_WIRE,  N_WIRE,  "P5 wire the buttons")

    out = ref[0]
    open(out_fp, "w", encoding="utf-8", newline="").write(out)
    print("patches applied: %d" % n[0])
    print("base md5: %s" % got)
    print("out  md5: %s" % hashlib.md5(out.encode("utf-8")).hexdigest())

if __name__ == "__main__":
    main()
