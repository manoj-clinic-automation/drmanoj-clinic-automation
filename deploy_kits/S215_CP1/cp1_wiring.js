/* ==================== CP-1 wiring (S215 · D359) ====================
   Added as the LAST script block so every base function it touches
   already exists. Nothing here rewrites base behaviour except by
   documented wrapper. */

/* ---- stage state ---- */
window.cpStage=1; window.cpPayer='cash';
window.cpTierTouched=false; window.cpProcTouched=false;

function cpPaint(){
 [].forEach.call(document.querySelectorAll('#cpStepper .cpstep'),function(b){
   b.classList.toggle('on', parseInt(b.getAttribute('data-st'),10)===window.cpStage);
 });
}
function cpSetStage(n){
 var cm=document.getElementById('caseModal');
 if(n===1){ window.cpStage=1; if(cm) cm.classList.remove('open'); cpPaint(); return; }
 if(n===2){ window.cpStage=2;
   if(cm && !cm.classList.contains('open')){ var b=document.getElementById('caseBtn'); if(b&&b.onclick) b.onclick(); }
   cpFeedForward(); cpPaint(); return; }
 /* 3 & 4 are parked by the owner's word (CP-3 / CP-4) */
 try{ toast('Parked — arrives with CP-'+(n===3?'3':'3/CP-4')); }catch(_e){ alert('Parked — arrives with CP-3/CP-4'); }
}
(function(){
 var s=document.getElementById('cpStepper'); if(!s) return;
 s.addEventListener('click',function(e){ var b=e.target.closest('.cpstep'); if(!b) return;
   cpSetStage(parseInt(b.getAttribute('data-st'),10)); });
})();
/* the old Case pack button and modal close keep the stepper honest */
(function(){
 var cm=document.getElementById('caseModal'); if(!cm||!window.MutationObserver) return;
 new MutationObserver(function(){
   window.cpStage = cm.classList.contains('open') ? 2 : 1; cpPaint();
 }).observe(cm,{attributes:true,attributeFilter:['class']});
})();

/* ---- payer + touched-state tracking ---- */
(function(){
 var seg=document.getElementById('seg');
 if(seg) seg.addEventListener('click',function(e){ var b=e.target.closest('button'); if(b&&b.getAttribute('data-p')) window.cpPayer=b.getAttribute('data-p'); },true);
 var ot=document.getElementById('otTier');
 if(ot) ot.addEventListener('click',function(){ window.cpTierTouched=true; },true);
 var cp=document.getElementById('cs_proc');
 if(cp) cp.addEventListener('change',function(){ window.cpProcTouched=true; });
})();

/* ---- stage-1 → stage-2 feed-forward (D359: chosen upstream, editable downstream) ---- */
function cpGuessProc(t){ t=(t||'').toLowerCase();
 if(/thr|total hip|hip replace/.test(t)) return (/neck|fracture/.test(t)?'thrneck':'thr');
 if(/tkr|total knee|knee replace/.test(t)) return 'tkr';
 if(/hemi|bipolar|austin|moore/.test(t)) return 'hemi';
 if(/pfn|intertroch|trochanter/.test(t)) return 'itfix';
 if(/femoral neck|neck femur|cc screw|cannulated/.test(t)) return 'noffix';
 if(/acl/.test(t)) return 'acl';
 if(/implant removal|rod removal|plate removal/.test(t)) return 'implrem';
 if(/patella/.test(t)) return 'patella';
 if(/ankle|bimalleolar/.test(t)) return 'ankle';
 return '';
}
function cpFeedForward(){
 /* OT tier from the payer path — only until the owner touches the tier himself */
 try{
  if(!window.cpTierTouched){
    var map={ayush:'ayush',tpa:'tpa',cash:'pay'};
    var want=map[window.cpPayer]||'pay';
    var btn=document.querySelector('#otTier button[data-t="'+want+'"]');
    if(btn && !btn.classList.contains('on')) btn.click();
  }
 }catch(_e){}
 /* consent procedure guess from the chosen estimate — only until he picks one himself */
 try{
  if(!window.cpProcTouched){
    var est=null; try{ est=chooseEstimate(); }catch(_e2){}
    var guess=cpGuessProc(est&&est.title);
    var sel=document.getElementById('cs_proc');
    if(guess && sel && sel.value!==guess){
      sel.value=guess;
      try{ sel.dispatchEvent(new Event('change')); }catch(_e3){}
      window.cpProcTouched=false; /* a guess is not a touch */
    }
  }
 }catch(_e){}
}

/* ---- polio module UI ---- */
function polioSync(){
 var cb=document.getElementById('cs_polio'), sub=document.getElementById('polioSub');
 if(sub&&cb) sub.style.display=cb.checked?'block':'none';
}
(function(){
 var sel=document.getElementById('cs_polio_proc'); if(!sel) return;
 sel.innerHTML='';
 POLIO_MODULES.forEach(function(m){ var o=document.createElement('option'); o.value=m.k; o.textContent=m.en; sel.appendChild(o); });
})();

/* ---- snapshot wrappers: the polio choice survives save/recall ---- */
(function(){
 var _snap=csFieldsSnap;
 csFieldsSnap=function(){ var f=_snap();
  try{ f.polio=!!(document.getElementById('cs_polio')||{}).checked;
       f.v.cs_polio_proc=(document.getElementById('cs_polio_proc')||{}).value||'';
       f.v.cs_change_note=(document.getElementById('cs_change_note')||{}).value||''; }catch(_e){}
  return f; };
 var _rest=csFieldsRestore;
 csFieldsRestore=function(f){ var r=_rest(f);
  try{ var cb=document.getElementById('cs_polio');
       if(cb){ cb.checked=!!(f&&f.polio); polioSync(); }
       if(f&&f.v&&f.v.cs_polio_proc){ var s=document.getElementById('cs_polio_proc'); if(s) s.value=f.v.cs_polio_proc; }
  }catch(_e){}
  return r; };
})();

/* ---- bundle wrapper: stage + polio + change-note travel with the case ---- */
(function(){
 var _cb0=caseBundle;
 caseBundle=function(){ var b=_cb0();
  try{
   b.stage=window.cpStage||2;
   b.consent=b.consent||{};
   b.consent.polio={on:!!(document.getElementById('cs_polio')||{}).checked,
                    proc:(document.getElementById('cs_polio_proc')||{}).value||''};
   b.consent.change_note=(document.getElementById('cs_change_note')||{}).value||'';
  }catch(_e){}
  return b; };
})();

/* ---- after a save, the saved case IS the open case (one case travels) ---- */
(function(){
 var _f=window.fetch;
 window.fetch=function(u,o){
  var p=_f.apply(this,arguments);
  if(String(u).indexOf('/portal/casepack/save')>=0){
    p=p.then(function(r){
      try{ r.clone().json().then(function(j){
        if(j&&j.ok&&j.case_id){
          window.cpLastCase=j.case_id;
          window.loadedCase={case_id:j.case_id,versions:j.version||1};
          try{paintLoaded();}catch(_e){}
        } }).catch(function(){}); }catch(_e){}
      return r; });
  }
  return p; };
})();

/* ---- consent history (the D359 consent ledger, read-only) ---- */
(function(){
 var btn=document.getElementById('cs_hist'), panel=document.getElementById('cs_hist_panel');
 if(!btn||!panel) return;
 btn.onclick=function(){
  var cid=(window.loadedCase&&window.loadedCase.case_id)||window.cpLastCase||'';
  if(!cid){ cid=prompt('Case ID (e.g. C-2026-000012):')||''; }
  cid=cid.trim(); if(!cid) return;
  panel.style.display='block'; panel.innerHTML='Loading…';
  fetch('/portal/casepack/consents/'+encodeURIComponent(cid))
   .then(function(r){return r.json();})
   .then(function(j){
     if(!j.ok){ panel.innerHTML='Error: '+(j.error||'?'); return; }
     if(!j.rows.length){ panel.innerHTML='<b>'+cid+'</b> — no consent issued yet.'; return; }
     var h='<b>Consent history — '+cid+'</b><table style="width:100%;border-collapse:collapse;margin-top:6px;font-size:12px">'
          +'<tr><th style="text-align:left">c#</th><th style="text-align:left">kind</th><th style="text-align:left">issued</th><th style="text-align:left">procedure</th><th style="text-align:left">note</th><th></th></tr>';
     j.rows.forEach(function(r2,i){
       h+='<tr style="border-top:1px solid var(--line)"><td>c'+r2.Consent_No+'</td><td>'+r2.Kind+(r2.Polio_Module?' · polio':'')+'</td><td>'+r2.Issue_Date+'</td><td>'+(r2.Procedure||'')+'</td><td>'+(r2.Change_Note||'')+'</td>'
         +'<td><a href="/portal/casepack/consentfile?case='+encodeURIComponent(cid)+'&n='+(i+1)+'" target="_blank">open</a></td></tr>';
     });
     panel.innerHTML=h+'</table><div style="color:var(--muted);margin-top:4px">Old versions are never deleted — a date-only re-issue keeps its number; changed content becomes the next number.</div>';
   })
   .catch(function(e){ panel.innerHTML='Error: '+e; });
 };
})();

cpPaint();
