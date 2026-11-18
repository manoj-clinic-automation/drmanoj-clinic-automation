/* ==== KIT_S876 (D1007, Session 483): a clinic ID on the Hub opens the patient's record inline -- events newest first,
   in words, the paper one tap under each, "Open the full record" for the rest. One reader (patient_events.py);
   no dialog anywhere (F-1464); every click inside stays inside (the rows around it toggle on click). ==== */
function s876Chip(cid,mode,label){
  if(!s876Is(cid)) return '#'+esc(cid);
  var c=esc(cid);
  return '<span class="s876cid" data-cid="'+c+'" data-mode="'+(mode==='here'?'here':'row')+'" onclick="event.stopPropagation();s876Rec(this)" '+
    'style="color:var(--accent);font-weight:600;cursor:pointer;border-bottom:1px dotted currentColor;white-space:nowrap" title="open the patient\'s record here">'+
    (label?esc(label)+' ':'')+'#'+c+' <span class="s876t">▸</span></span>';
}
function s876Who(who,cid){ return s876Is(cid)?who.split(' · #'+esc(cid)).join('')+' '+s876Chip(cid,'row'):who; }
function s876Is(cid){ var c=String(cid||'').trim().toUpperCase(); return c!==''&&c!=='WALK-IN'&&c.indexOf('WA')!==0&&/\d/.test(c); }   /* a walk-in (WALK-IN, WA...) has no record */
function s876Rec(el){
  var cid=el.getAttribute('data-cid'), host=null;
  var hd=null;
  if(el.getAttribute('data-mode')==='row'){ hd=el.closest('div[onclick]'); host=hd?hd.parentElement:null; }
  if(!host) host=el.closest('div,td');
  if(!host) return;
  var t=el.querySelector('.s876t'), ex=null;
  for(var i=0;i<host.children.length;i++){ var c=host.children[i]; if(c.classList.contains('s876rec')&&c.getAttribute('data-cid')===cid){ ex=c; break; } }
  if(ex){ host.removeChild(ex); if(t)t.textContent='▸'; return; }
  var box=document.createElement('div'); box.className='s876rec'; box.setAttribute('data-cid',cid);
  box.addEventListener('click',function(e){ e.stopPropagation(); });
  box.innerHTML='<div class="mut" style="padding:4px 0">opening the record of #'+esc(cid)+'…</div>';
  if(hd&&!hd.nextElementSibling){ var sp=document.createElement('div'); sp.style.display='none'; host.appendChild(sp); }   /* the row's own toggle keeps its own target */
  host.appendChild(box); if(t)t.textContent='▾';
  fetch('/finance/sanjeevni/api/patient/'+encodeURIComponent(cid)+'/record?_='+Date.now(),{cache:'no-store',credentials:'same-origin'})
    .then(function(r){ return r.json(); })
    .then(function(j){ box.innerHTML=(j&&j.ok)?s876Html(j):'<div class="mut">'+esc((j&&j.message)||'the record could not be opened')+'</div>'; })
    .catch(function(){ box.innerHTML='<div class="mut">the record could not be opened — tap the ID again</div>'; });
}
function s876Html(j){
  var days=j.days||[], n=Math.max(1,parseInt(j.recent_days,10)||5);
  var h='<div style="border:1px solid #c7d7fe;background:#f8faff;border-radius:10px;padding:8px 12px;margin:6px 0 8px;max-width:780px;cursor:default">';
  h+='<div style="display:flex;gap:10px;flex-wrap:wrap;align-items:baseline;border-bottom:1px solid #dbe4ff;padding-bottom:5px;margin-bottom:2px">'+
     '<b>'+esc(j.name||'name not known yet')+'</b><span class="mut">#'+esc(j.cid)+'</span>'+
     ((j.mobiles||[]).length&&typeof s874Mob==='function'?s874Mob({mobiles:j.mobiles}):'')+
     (j.first_seen?'<span class="badge">first seen '+esc(j.first_seen)+' · '+(j.visit_days||0)+' visit day'+(j.visit_days===1?'':'s')+'</span>':'')+
     '<a href="'+esc(j.full_url)+'" target="_blank" rel="noopener" style="margin-left:auto">Open the full record ↗</a></div>';
  if(j.merged) h+='<div class="mut">This ID is marked as merged into '+esc(j.merged)+'.</div>';
  if(!days.length) h+='<div class="mut" style="padding:6px 0">Nothing on record for this ID yet.</div>';
  for(var i=0;i<days.length;i++){
    if(i===n) h+='<details><summary class="mut" style="cursor:pointer;padding:6px 0">▸ '+(days.length-n)+' earlier day'+(days.length-n===1?'':'s')+
      ' · '+esc(days[days.length-1].dmy)+' to '+esc(days[n].dmy)+'</summary>';
    h+=s876Day(days[i]);
  }
  if(days.length>n) h+='</details>';
  return h+'</div>';
}
function s876Day(d){
  var h='<div style="display:grid;grid-template-columns:78px 1fr;gap:10px;padding:6px 0;border-top:1px solid #e6ecfb">'+
        '<div style="font-weight:600;font-size:13.5px">'+esc(d.dmy)+'<div class="mut" style="font-weight:400;font-size:12px">'+esc(d.dow)+'</div></div><div>';
  (d.events||[]).forEach(function(e){
    h+='<div style="display:flex;gap:8px;align-items:baseline;padding:2px 0"><span style="width:18px;text-align:center">'+esc(e.icon)+'</span>'+
       '<span style="flex:1"><b>'+esc(e.head)+'</b>'+esc(e.text||'')+(e.sub?' <span class="mut">· '+esc(e.sub)+'</span>':'')+'</span>'+
       '<span class="num" style="white-space:nowrap">'+(e.money?esc(e.sign||'')+'₹'+esc(e.money):'')+'</span></div>';
    if(e.flag) h+='<div style="margin:2px 0 2px 26px;padding:3px 9px;border-radius:8px;font-size:13px;'+
       (e.flag.tone==='warn'?'background:#fffaeb;border:1px solid #fedf89;color:#b54708':'background:#f2f4f7;color:#667085')+'">⚑ '+esc(e.flag.text)+'</div>';
    (e.opens||[]).forEach(function(o){
      h+='<details style="margin:0 0 2px 26px"><summary style="cursor:pointer;color:var(--accent);font-size:12.5px">'+esc(o.label)+'</summary>'+s876Open(o)+'</details>';
    });
  });
  return h+'</div></div>';
}
function s876Open(o){
  if(o.lines) return '<table style="margin:2px 0 6px;background:#fff;max-width:620px"><thead><tr><th>medicine</th><th class="num">quantity</th><th class="num">value</th></tr></thead><tbody>'+
    o.lines.map(function(l){ return '<tr><td>'+esc(l.item)+(l.note?' <span class="mut">('+esc(l.note)+')</span>':'')+'</td><td class="num">'+esc(l.qty)+'</td>'+
      '<td class="num">'+(l.value!=null?'₹'+esc(l.value):'—')+'</td></tr>'; }).join('')+'</tbody></table>';
  if(o.files) return '<div style="padding:3px 0 6px">'+(o.files.length?o.files.map(function(f){
      return f.url?'<a href="'+esc(f.url)+'" target="_blank" rel="noopener">'+esc(f.name)+'</a>':'<span class="mut">'+esc(f.name)+' (not on Drive yet)</span>'; }).join(' · ')
    :'<span class="mut">no file yet</span>')+'</div>';
  return '<div style="padding:3px 0 6px;font-size:13.5px">'+esc(o.text||'')+'</div>';
}
/* ==== end KIT_S876 ==== */
