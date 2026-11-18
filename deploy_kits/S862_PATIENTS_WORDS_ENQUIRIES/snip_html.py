# -*- coding: utf-8 -*-
# Snippets for patients_page.html (S862). Read by make_s862.py.
CSS_OLD = '''</style>'''
CSS_NEW = '''/* S862: the one-tap words; callers who became patients */
table.words select{font-size:13px;padding:4px 6px;border:1px solid var(--line);border-radius:6px;background:var(--paper);color:var(--fg);max-width:260px}
table.words .also{margin-top:4px;font-size:12px;color:var(--fg)}
table.words .also label{display:inline-block;margin:2px 10px 2px 0;white-space:nowrap}
table.words .why{margin-top:3px;font-size:12px;opacity:.7}
button.place,button.unplace{font-weight:600;font-size:13px;padding:5px 12px;border-radius:999px;border:1px solid var(--line);background:var(--paper);color:var(--fg);cursor:pointer}
button.place{border-color:currentColor}
button.place:disabled,button.unplace:disabled{opacity:.5;cursor:default}
.okmsg{border:1px solid var(--line);border-radius:8px;padding:9px 12px;margin:0 0 12px}
</style>'''

WORDS_OLD = '''    '<div class="card"><h2>Diagnosis words to place</h2>'+(R.words?('<p class="sub">'+R.words.n+' words · '+R.words.visits+' visits — words your taxonomy did not recognise. The largest:</p><div class="tw"><table><tbody>'+R.words.top.map(function(w){return '<tr><td class="l">'+esc(w.word)+'</td><td>'+w.n+' visit'+(w.n===1?'':'s')+'</td></tr>';}).join("")+'</tbody></table></div><p class="note">The one-tap placing (the page suggests a group; one tap places the word, its spelling slips and its other sides) comes next.</p>'):'<p class="sub">could not be read just now</p>')+'</div></div>');}'''
WORDS_NEW = '''    wordsCard()+'</div>');}'''

NEXT_OLD = '''  h.push('<div class="card next"><h2>Still to come</h2><ul><li>The one-tap placing of diagnosis words.</li><li>Google\\'s monthly figures read by the server by itself each month (today they are read from Google\\'s mail at each session).</li><li>Which enquiry callers became patients.</li></ul></div>');
  document.getElementById("page").innerHTML=h.join("");
  Array.prototype.forEach.call(document.querySelectorAll("[data-k]"),function(e){e.onclick=function(ev){ev.preventDefault();openList(e.getAttribute("data-k"),e.textContent);};});
}'''
NEXT_NEW = '''  var G0=p2().google||{};
  if(G0.read_by!=="server")h.push('<div class="card next"><h2>Still to come</h2><ul><li>Google\\'s monthly figures read by the server by itself each month (today they are read from Google\\'s mail at each session).</li></ul></div>');
  document.getElementById("page").innerHTML=h.join("");
  Array.prototype.forEach.call(document.querySelectorAll("[data-k]"),function(e){e.onclick=function(ev){ev.preventDefault();openList(e.getAttribute("data-k"),e.textContent);};});
  wireWords();
}
// ---------------------------------------------------------------- S862: the diagnosis words, one tap
var WMSG=null;
function wordsCard(){
  var W=R.words;
  if(!W)return '<div class="card"><h2>Diagnosis words to place</h2><p class="sub">could not be read just now</p></div>';
  var rows=W.rows||[],ch=W.choices||[];
  function opts(sel){var o='<option value="">— choose a group —</option>',cat=null;ch.forEach(function(c){if(c.cat!==cat){if(cat!==null)o+='</optgroup>';cat=c.cat;o+='<optgroup label="'+esc(cat)+'">';}o+='<option value="'+esc(c.std)+'"'+(c.std===sel?' selected':'')+'>'+esc(c.std)+'</option>';});if(cat!==null)o+='</optgroup>';return o;}
  var h='<div class="card"><h2>Diagnosis words to place</h2><div id="wmsg">'+(WMSG?'<div class="'+(WMSG.bad?'err':'okmsg')+'">'+esc(WMSG.t)+'</div>':'')+'</div>';
  if(!W.n)h+='<p class="sub">Every diagnosis word written so far is recognised — nothing to place.</p>';
  else if(!rows.length||!ch.length)h+='<p class="sub">'+W.n+' words · '+W.visits+' visits — words your taxonomy did not recognise (the placing could not be read just now):</p><div class="tw"><table><tbody>'+(W.top||[]).map(function(w){return '<tr><td class="l">'+esc(w.word)+'</td><td>'+w.n+' visit'+(w.n===1?'':'s')+'</td></tr>';}).join("")+'</tbody></table></div>';
  else h+='<p class="sub">'+W.n+' words · '+W.visits+' visits — words your taxonomy did not recognise. Each shows the group the page suggests; <b>Place</b> puts the word there, with the spellings and sides ticked under it. Every figure on this page moves with it.</p><div class="tw"><table class="words"><thead><tr><th>Word</th><th>Visits</th><th>Group</th><th></th></tr></thead><tbody>'+
    rows.map(function(r,i){return '<tr><td class="l"><b>'+esc(r.word)+'</b>'+(r.words.length>1?'<div class="also">'+r.words.slice(1).map(function(w){return '<label><input type="checkbox" checked data-w="'+esc(w.word)+'"> '+esc(w.word)+' ('+w.n+')</label>';}).join("")+'</div>':'')+(r.why?'<div class="why">suggested from '+esc(r.why)+'</div>':'<div class="why">no suggestion — choose a group</div>')+'</td><td>'+r.n+'</td><td><select aria-label="Group for '+esc(r.word)+'">'+opts(r.sug)+'</select></td><td><button class="place" data-i="'+i+'">Place</button></td></tr>';}).join("")+'</tbody></table></div>';
  if(W.placed&&W.placed.length)h+='<p class="sub" style="margin-top:12px"><b>Placed by you</b> — Undo puts a word back among the words to place</p><div class="tw"><table><tbody>'+
    W.placed.map(function(p){return '<tr><td class="l">'+esc(p.term)+'</td><td class="l">'+esc(p.std)+'</td><td>'+esc(dmy(String(p.at||"").slice(0,10)))+'</td><td><button class="unplace" data-t="'+esc(p.term)+'">Undo</button></td></tr>';}).join("")+'</tbody></table></div>';
  return h+'</div>';
}
function wireWords(){
  var W=R&&R.words;if(!W)return;
  Array.prototype.forEach.call(document.querySelectorAll("button.place"),function(b){b.onclick=function(){
    var r=(W.rows||[])[+b.getAttribute("data-i")],tr=b.closest("tr");if(!r||!tr)return;
    var std=tr.querySelector("select").value;if(!std){WMSG={t:"Choose a group for "+r.word+" first.",bad:1};draw();return;}
    var ws=[r.word];Array.prototype.forEach.call(tr.querySelectorAll("input[type=checkbox]"),function(c){if(c.checked)ws.push(c.getAttribute("data-w"));});
    wpost("/finance/console/api/patients/place",{words:ws,std:std},b,"Place",function(j){return "Placed "+j.placed+" word"+(j.placed===1?"":"s")+" in "+j.std+" — "+j.moved+" visit"+(j.moved===1?"":"s")+" moved.";});};});
  Array.prototype.forEach.call(document.querySelectorAll("button.unplace"),function(b){b.onclick=function(){
    wpost("/finance/console/api/patients/unplace",{term:b.getAttribute("data-t")},b,"Undo",function(j){return "Undone — "+j.moved+" visit"+(j.moved===1?"":"s")+" back among the words to place.";});};});
}
function wpost(url,body,btn,label,say){
  btn.disabled=true;btn.textContent="…";
  fetch(url,{method:"POST",credentials:"same-origin",cache:"no-store",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}).then(function(r){return r.json().catch(function(){return {ok:false,why:"the server answered "+r.status};});}).then(function(j){
    if(!j.ok){WMSG={t:j.why||j.message||"Not done.",bad:1};btn.disabled=false;btn.textContent=label;load(false);return;}
    WMSG={t:say(j)+(j.rebuilt===false?" The page shows it at its next reading (in a minute).":""),bad:0};load(false);
  }).catch(function(e){WMSG={t:"Could not reach the server ("+e+"). Nothing changed on this page.",bad:1};btn.disabled=false;btn.textContent=label;draw();});
}
// ---------------------------------------------------------------- S862: enquiry callers who became patients
function becameTable(){
  var B=p2().became;
  if(!B||!B.ok)return '<p class="note">Which callers became patients could not be read just now'+(B&&B.why?' ('+esc(B.why)+')':'')+'.</p>';
  var ms=R.months.map(function(m){return m.ym;}).filter(function(ym){return B.months&&B.months[ym];});
  if(!ms.length)return '';
  return '<p class="sub" style="margin-top:12px"><b>Enquiry callers who became patients</b></p><div class="tw"><table><thead><tr><th>Month</th><th>Callers not yet your patients</th><th class="hl">Came as new patients within '+B.window+' days</th><th>New patients of the month</th><th>… who rang the clinic before their first visit</th></tr></thead><tbody>'+
    ms.map(function(ym){var b=B.months[ym];return '<tr class="'+(ym===M?'shade':'')+'"><td>'+esc(mlab(ym))+(b.complete?'':' <span class="grey">(so far)</span>')+'</td><td>'+b.callers+'</td>'+cell(b.became+' ('+b.became_p+')',b.became?'bec:'+ym:'','hl')+'<td>'+b.newp+'</td>'+(b.rang==null?'<td><span class="grey">before the call record</span></td>':cell(b.rang+' of '+b.rang_base+' ('+b.rang_p+')',b.rang?'rf:'+ym:''))+'</tr>';}).join("")+'</tbody></table></div><p class="note">'+esc(B.note)+'</p>';
}'''

DESK_OLD = '''    d.calls.map(function(r){return '<tr><td>'+esc(r.label)+'</td><td>'+r.n+'</td><td>'+r.first+' ('+esc(r.first_p)+')</td><td>'+r.again+' ('+esc(r.again_p)+')</td><td>'+r.back+' ('+esc(r.back_p)+')</td><td>'+r.later+' ('+esc(r.later_p)+')</td><td>'+(r.open||0)+'</td><td class="hl"><b>'+r.never+' ('+esc(r.never_p)+')</b></td><td class="hl">'+r.nocb+'</td></tr>';}).join("")+'</tbody></table></div><p class="note">'+esc(d.note)+'</p>');'''
DESK_NEW = DESK_OLD + '''
  h.push(becameTable());'''

CHIPS_OLD = '''b.onclick=function(){M=b.getAttribute("data-m");'''
CHIPS_NEW = '''b.onclick=function(){WMSG=null;M=b.getAttribute("data-m");'''

GSUB_OLD = '''beside the clinic\\'s own new patients · latest: '+esc(last)+'</p>'+'''
GSUB_NEW = '''beside the clinic\\'s own new patients · latest: '+esc(last)+(G.read_by==="server"&&G.mail_day?' · read by the server from Google\\'s mail of '+esc(dmy(G.mail_day)):'')+'</p>'+'''
