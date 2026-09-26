#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s414.py -- kit S414_RULES_PAGE_UX (F-635). Builds the two patched files FROM THE LIVE BYTES with anchored edits (every
anchor exactly once, else it refuses) after checking each file's FROM pin:

  finance_ui/finance_approvals.html   the buying-rules block (S410) rewritten: nothing redraws on a tap -- ticks, supplier edits, pause,
                                      freeze and approve patch the DOM in place from the API's answer; a full draw remembers every open
                                      <details> and the scroll (poKeepOpen); the two candidate lists are check-lists that stay put
                                      (count, tick/untick all shown, filter, sort, ticked-only; a ticked row stays, greyed, with its
                                      rule); the per-supplier editor is an inline form with a hint on every field; Freeze / Approve are
                                      inline confirmations; "Your item rules" grouped by rule with a cross and inline numbers, the add
                                      box autocompletes; Approve rules (with the one-line summary) at the top and the bottom.
                                      No prompt(), no confirm() in the block. Owner-facing, English.
  order_rules.py                      two small additions: GET /finance/porders/api/rules/items?q= (<= 20 names from the stock
                                      master, every typed word must appear) and the item-rule answer carries the updated counts + row.

Usage: make_s414.py --finance /root/finance --out DIR   (writes DIR/finance_approvals.html and DIR/order_rules.py)
"""
import hashlib
import io
import os
import sys

FROM = {"finance_approvals.html": "7de583154b87bd4d3ba13ce6de1c53a9", "order_rules.py": "df6196fcb750f3dd5401695bd254a7aa"}
SRC = {"finance_approvals.html": os.path.join("finance_ui", "finance_approvals.html"), "order_rules.py": "order_rules.py"}


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(path, name):
    with io.open(path, "rb") as fh:
        raw = fh.read()
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not its FROM pin %s" % (path, md5(raw), FROM[name]))
    return raw.decode("utf-8")


def rep(s, old, new, what):
    n = s.count(old)
    if n != 1:
        sys.exit("REFUSED: anchor for %s found %d times (need exactly 1): %r" % (what, n, old[:80]))
    return s.replace(old, new)


def rep_between(s, start, end, new, what):
    """Replace everything from the start marker up to (not including) the end marker; each marker exactly once, start before end."""
    if s.count(start) != 1 or s.count(end) != 1:
        sys.exit("REFUSED: markers for %s: start x%d, end x%d (need exactly 1 each)" % (what, s.count(start), s.count(end)))
    i, j = s.index(start), s.index(end)
    if j <= i:
        sys.exit("REFUSED: markers for %s out of order" % what)
    return s[:i] + new + s[j:]


# ============================================================================ the page: the rules block, rewritten
CSS = r'''
/* S414 (F-635): the buying-rules block -- ticked rows stay (greyed, with the rule), the saved tick fades, the inline editor, the tools row */
#poRules tr.ticked td{color:var(--text-3)}#poRules .po-rule{display:none;margin-left:6px;font-size:12px;color:var(--text-2);border:1px solid var(--line);border-radius:6px;padding:0 6px}#poRules tr.ticked .po-rule{display:inline-block}
#poRules .po-saved{display:none;color:var(--good);font-weight:600;margin-left:6px;font-size:13px}#poRules .po-saved.on{display:inline;animation:poFade 2.4s forwards}@keyframes poFade{0%{opacity:0}15%{opacity:1}70%{opacity:1}100%{opacity:0}}
#poRules .po-form{display:grid;grid-template-columns:1fr;gap:8px;padding:10px;border:1px solid var(--line);border-radius:10px;background:var(--surface-1);max-width:720px}#poRules .po-form label{display:block}#poRules .po-form small{display:block;color:var(--text-2);font-size:12.5px}
#poRules .po-form input[type=number]{width:90px}#poRules .po-form input[type=text],#poRules .po-form input[type=date],#poRules .po-tools input[type=text],#poRules input.po-txt{border:1px solid var(--line);border-radius:8px;padding:5px 8px;font-size:14px}
#poRules .po-tools{margin:6px 0;font-size:14px}#poRules .po-tools input[type=text]{min-width:170px}#poRules .po-grp{margin-top:8px}#poRules .po-approve{margin:8px 0;padding:10px 12px;border:1px solid var(--line);border-radius:10px}
#poRules .po-days label{display:inline-block;margin-right:8px}#poRules td.po-act{white-space:nowrap}#poRules .po-x{padding:2px 8px}
'''

JS = r'''/* ---- S410 (D626) -> S414 (F-635): the buying rules block. NOTHING REDRAWS ON A TAP: a tick, a supplier edit, a pause, the freeze,
   the approval patch the DOM in place from the API's answer. A full draw (loadPORules) remembers every open <details> and the scroll
   and restores them (poKeepOpen). Candidates are check-lists that stay put; the supplier editor is an inline form; Freeze / Approve
   are inline confirmations; no browser prompt or confirm dialog anywhere in this block. ---- */
var PO_R=null, PO_UI={open:null, timers:{}, sugT:null};
var PO_RULE_WORD={never:"never re-order", on_demand:"on demand", keep:"keep-in-stock", max_shelf:"max on shelf", internal:"internal use"};
var PO_RULE_ORDER=["never","on_demand","keep","max_shelf","internal"];
function poKeepOpen(fn){
  var o=$("poRules"), open={}, y=window.pageYOffset||document.documentElement.scrollTop||0, first=(PO_UI.open===null);
  if(first) open={poD_never:1,poD_od:1,poD_items:1};
  else if(o){ var ds=o.querySelectorAll("details[id]"); for(var i=0;i<ds.length;i++){ if(ds[i].open) open[ds[i].id]=1 } }
  fn();
  for(var k in open){ var d=document.getElementById(k); if(d) d.open=true }
  PO_UI.open=open; if(!first) window.scrollTo(0,y);
}
function poFlash(el){ if(!el) return; var s=el.querySelector(".po-saved"); if(!s) return; s.classList.remove("on"); void s.offsetWidth; s.classList.add("on"); }
function poFetch(u,b){ return fetch(u,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b||{})}).then(srvJSON).then(function(x){ var j=x.j||{}; if(!j.ok){ throw new Error(j.message||j.error||"not saved") } return j; }); }
function poWhy(e){ return (e&&e.message)?e.message:"the server could not be reached"; }
function poSummaryText(){
  var j=PO_R||{}, c=(j.counts&&j.counts.by_rule)||{}, ir=j.item_rules||[];
  var nn=(c.never!=null)?c.never:ir.filter(function(x){return x.rule==="never"}).length, od=(c.on_demand!=null)?c.on_demand:ir.filter(function(x){return x.rule==="on_demand"}).length;
  return (j.rules||[]).length+" suppliers · "+nn+" never re-order · "+od+" on demand · frozen: "+(j.frozen?"YES":"no")+(j.rules_ok?" · approved":" · not yet approved");
}
function poSummaryFill(){ var els=document.querySelectorAll("#poRules .po-sum"); for(var i=0;i<els.length;i++) els[i].textContent=poSummaryText(); }
/* ---- Approve rules: at the top and the bottom; a second button "Yes, approve" for 10 s, never a browser dialog ---- */
function poApproveHTML(where){
  var j=PO_R||{};
  return '<div class="po-approve" id="poApprove'+where+'"><div class="mut po-sum">'+esc(poSummaryText())+'</div>'+
    (j.rules_ok?'<div class="ok" style="margin-top:6px">✓ Rules approved — the staff screen sends medicine orders (the day\'s proposals at 09:00).</div>'
              :'<div style="margin-top:6px"><span class="po-appbtn"><button onclick="poApproveAsk(\''+where+'\')">Approve rules</button></span> <span class="mut">one tap: the standing approval (D626) — the paper purchase-order sheet is retired; the system\'s record replaces it. Until then the staff screen says "Doctor sahab ke rules ka intezaar".</span></div>')+'</div>';
}
function poApproveAsk(where){
  var s=document.querySelector("#poApprove"+where+" .po-appbtn"); if(!s) return;
  s.innerHTML='<b>Approve the medicine buying rules as they stand?</b> <button onclick="poApproveGo()">Yes, approve</button> <button class="ghost" onclick="poApproveReset()">cancel</button> <span class="mut">(10 s)</span>';
  clearTimeout(PO_UI.timers.approve); PO_UI.timers.approve=setTimeout(poApproveReset,10000);
}
function poApproveReset(){ clearTimeout(PO_UI.timers.approve); ["Top","Bottom"].forEach(function(w){ var s=document.querySelector("#poApprove"+w+" .po-appbtn"); if(s) s.innerHTML='<button onclick="poApproveAsk(\''+w+'\')">Approve rules</button>'; }); }
function poApproveGo(){
  clearTimeout(PO_UI.timers.approve);
  poFetch("/finance/porders/api/rules/approve",{}).then(function(j){ PO_R.rules_ok=true; PO_R.approved=j.approved||null; ["Top","Bottom"].forEach(function(w){ var d=$("poApprove"+w); if(d) d.outerHTML=poApproveHTML(w); }); loadNeeds(); })
    .catch(function(e){ alert(poWhy(e)); poApproveReset(); });
}
/* ---- Freeze / Unfreeze: the reason box and "Yes, freeze" appear inline for 10 s ---- */
function poFreezeHTML(){
  var fr=(PO_R||{}).frozen;
  if(fr) return '<div class="alert bad" style="margin:6px 0">⛔ Medicine ordering is FROZEN since '+esc((fr.at||"").slice(0,16).replace("T"," "))+' — '+esc(fr.reason||"")+' <span class="po-frz"><button class="ghost" onclick="poFreezeAsk(false)">Unfreeze</button></span></div>';
  return '<div class="row" style="margin:6px 0"><span class="po-frz"><button class="ghost" onclick="poFreezeAsk(true)">Freeze all medicine ordering</button></span> <span class="mut">one tap, a reason staff will see; unfreeze the same way</span></div>';
}
function poFreezeAsk(on){
  var s=document.querySelector("#poFreezeLine .po-frz"); if(!s) return;
  s.innerHTML=(on?'<input type="text" class="po-txt" id="poFrzWhy" placeholder="the reason staff will see" style="min-width:220px"> ':'')+'<button onclick="poFreezeGo('+(on?'true':'false')+')">'+(on?'Yes, freeze':'Yes, unfreeze')+'</button> <button class="ghost" onclick="poFreezeReset()">cancel</button> <span class="mut">(10 s)</span>';
  if(on){ var i=$("poFrzWhy"); if(i) i.focus(); }
  clearTimeout(PO_UI.timers.freeze); PO_UI.timers.freeze=setTimeout(poFreezeReset,10000);
}
function poFreezeReset(){ clearTimeout(PO_UI.timers.freeze); var d=$("poFreezeLine"); if(d) d.innerHTML=poFreezeHTML(); }
function poFreezeGo(on){
  clearTimeout(PO_UI.timers.freeze); var why=on?(($("poFrzWhy")||{}).value||""):"";
  poFetch("/finance/porders/api/rules/freeze",{on:on,reason:why}).then(function(j){ PO_R.frozen=j.frozen||null; var d=$("poFreezeLine"); if(d) d.innerHTML=poFreezeHTML(); poSummaryFill(); loadNeeds(); })
    .catch(function(e){ alert(poWhy(e)); poFreezeReset(); });
}
/* ---- the suppliers: one plain line each; "edit" opens the line into a form; pause asks its reason inline ---- */
function poSupIdx(sn){ var R=(PO_R&&PO_R.rules)||[]; for(var i=0;i<R.length;i++){ if(R[i].supplier_norm===sn) return i } return -1; }
function poSupRowHTML(i){
  var r=PO_R.rules[i];
  return '<td>'+esc(r.words)+'<span class="po-saved">✓ saved</span><div class="mut" style="font-size:12.5px">'+esc(r.cadence_how||"")+(r.owner_set&&r.owner_set.length?' · yours: '+esc(r.owner_set.join(", ")):'')+(r.note?' · '+esc(r.note):'')+'</div></td>'+
    '<td class="num po-act"><span class="po-btns"><button class="ghost" onclick="poEditOpen('+i+')">edit</button> '+(r.paused?'<button class="ghost" onclick="poSetRow('+i+',[[\'paused\',0]],this)">resume</button>':'<button class="ghost" onclick="poPauseAsk('+i+')">pause</button>')+
    (r.review_on?' <button class="ghost" onclick="poSetRow('+i+',[[\'move_to\',\''+esc(r.review_target||"weekly")+'\']],this)">move to '+esc(r.review_target||"weekly")+'</button>':'')+'</span></td>';
}
function poSupRowFill(i){ var tr=$("poSup_"+i); if(tr){ tr.innerHTML=poSupRowHTML(i); poFlash(tr); } }
function poSetRow(i,pairs,btn){
  /* pairs: [[field,value],...] posted one after another (the API takes one field a call); the row re-renders from the last answer's words */
  var sn=PO_R.rules[i].supplier_norm, k=0; if(btn) btn.disabled=true;
  function next(){
    if(k>=pairs.length){ poSupRowFill(i); poSummaryFill(); loadNeeds(); return Promise.resolve(); }
    var p=pairs[k++];
    return poFetch("/finance/porders/api/rules/set",{supplier:sn,field:p[0],value:p[1]}).then(function(j){ var ch=j.changed||{}; for(var f in ch) PO_R.rules[i][f]=ch[f]; if(j.words) PO_R.rules[i].words=j.words; if(!PO_R.rules[i].owner_set) PO_R.rules[i].owner_set=[]; for(var g in ch){ if(PO_R.rules[i].owner_set.indexOf(g)<0) PO_R.rules[i].owner_set.push(g) } return next(); });
  }
  return next().catch(function(e){ if(btn) btn.disabled=false; throw e; });
}
function poPauseAsk(i){
  var s=document.querySelector("#poSup_"+i+" .po-btns"); if(!s) return;
  s.innerHTML='<input type="text" class="po-txt" id="poPz_'+i+'" placeholder="the reason staff will see" style="min-width:200px"> <button onclick="poPauseGo('+i+')">Pause</button> <button class="ghost" onclick="poSupRowFill('+i+')">cancel</button>';
  var e=$("poPz_"+i); if(e) e.focus();
}
function poPauseGo(i){ var why=(($("poPz_"+i)||{}).value||"").trim()||"paused by the owner"; poSetRow(i,[["pause_reason",why],["paused",1]]).catch(function(e){ alert(poWhy(e)); poSupRowFill(i); }); }
var PO_DAYS=["MON","TUE","WED","THU","FRI","SAT"], PO_DAY_WORD={MON:"Mon",TUE:"Tue",WED:"Wed",THU:"Thu",FRI:"Fri",SAT:"Sat"};
function poEditOpen(i){
  var old=document.querySelector("#poRules tr.po-editor"); if(old){ var was=old.id; old.parentNode.removeChild(old); if(was==="poEd_"+i) return; }
  var r=PO_R.rules[i], tr=$("poSup_"+i); if(!tr) return;
  var days=String(r.order_days||"MON").split(","), blocked=String(r.blocked_days||"").split(",");
  var p="poF_"+i+"_";
  function sel(id,cur,opts){ return '<select id="'+p+id+'">'+opts.map(function(o){return '<option value="'+o[0]+'"'+(String(cur)===o[0]?' selected':'')+'>'+o[1]+'</option>'}).join("")+'</select>'; }
  function num(id,cur,hint){ return '<label>'+hint[0]+' <input type="number" id="'+p+id+'" min="0" max="60" value="'+esc(cur==null?"":cur)+'"><small>'+hint[1]+'</small></label>'; }
  function chk(id,on,label,hint){ return '<label><input type="checkbox" id="'+p+id+'"'+(on?' checked':'')+'> '+label+'<small>'+hint+'</small></label>'; }
  var h='<tr class="po-editor" id="poEd_'+i+'"><td colspan="2"><div class="po-form"><div><b>'+esc(r.short||r.supplier)+'</b> <span class="mut">— change what you need, then Save; every field says what it does</span></div>'+
    '<label>Cadence '+sel("cadence",r.cadence,[["weekly","weekly"],["fortnightly","fortnightly"],["monthly","monthly"],["custom","custom (the days ticked below)"]])+'<small>weekly = one order day a week · fortnightly = alternate weeks · monthly = the first such day of the month · custom = every day you tick (Kedar: Mon + Fri)</small></label>'+
    '<div class="po-days">Order days: '+PO_DAYS.map(function(d){return '<label><input type="checkbox" id="'+p+'d_'+d+'"'+(days.indexOf(d)>=0?' checked':'')+' onchange="poEditDay('+i+',this)"> '+PO_DAY_WORD[d]+'</label>'}).join("")+'<small>the day(s) the order goes out to this supplier; for weekly / fortnightly / monthly only one day counts</small></div>'+
    chk("thu",blocked.indexOf("THU")<0,"Thursday ok","on = an order may go out on a Thursday (Kedar) · off = the shop-wide rule, no Thursday orders to this supplier")+
    chk("sun",blocked.indexOf("SUN")>=0,"Sunday blocked","on = never an order on a Sunday (the default) · off = Sundays allowed")+
    num("lead",r.lead_days,["Lead days","days from the order to the goods on the shelf: 1 = same evening, 2 = next day"])+
    num("safety",r.safety_days,["Safety days","days of stock kept as a cushion on top of the lead time"])+
    num("cap",r.cover_cap_days,["Cover cap (days)","never order more than this many days of cover in one go (weekly 14 · fortnightly 21 · monthly 45 by default)"])+
    chk("sse",!!Number(r.single_source_extra),"Single-source extra","extra cover days for an item only this supplier sells · waive it for a supplier who delivers the same evening")+
    '<label>Review on <input type="date" id="'+p+'review_on" value="'+esc(r.review_on||"")+'"> → target '+sel("review_target",r.review_target||"",[["","(none)"],["weekly","weekly"],["fortnightly","fortnightly"],["monthly","monthly"],["custom","custom"]])+'<small>a date to look at this supplier\'s cadence again; from that day the line offers "move to &lt;target&gt;" with one tap · clear the date to drop the review</small></label>'+
    chk("paused",!!Number(r.paused),"Paused","on = no orders to this supplier until you resume; the reason below shows to staff")+
    '<label>Pause reason <input type="text" id="'+p+'pause_reason" value="'+esc(r.pause_reason||"")+'" placeholder="the reason staff will see" style="min-width:220px"><small>only read while Paused is on</small></label>'+
    '<label>Note <input type="text" id="'+p+'note" value="'+esc(r.note||"")+'" style="min-width:280px"><small>a word for yourself; it shows under the supplier\'s line</small></label>'+
    '<div class="row"><button onclick="poEditSave('+i+')">Save</button> <button class="ghost" onclick="poEditClose('+i+')">Cancel</button> <span class="mut" id="'+p+'msg"></span></div></div></td></tr>';
  tr.insertAdjacentHTML("afterend",h);
}
function poEditDay(i,cb){ var c=$("poF_"+i+"_cadence"); if(c&&c.value!=="custom"&&cb.checked){ PO_DAYS.forEach(function(d){ var e=$("poF_"+i+"_d_"+d); if(e&&e!==cb) e.checked=false; }); } }
function poEditClose(i){ var e=$("poEd_"+i); if(e) e.parentNode.removeChild(e); }
function poEditSave(i){
  var r=PO_R.rules[i], p="poF_"+i+"_", v=function(id){ var e=$(p+id); return e?e.value:"" }, on=function(id){ var e=$(p+id); return !!(e&&e.checked) }, msg=$(p+"msg");
  var cad=v("cadence"), days=PO_DAYS.filter(function(d){return on("d_"+d)});
  if(!days.length){ if(msg) msg.textContent="tick at least one order day"; return; }
  if(cad!=="custom") days=days.slice(0,1);
  var blocked=String(r.blocked_days||"").split(",").filter(function(x){return x&&x!=="THU"&&x!=="SUN"}); if(!on("thu")) blocked.push("THU"); if(on("sun")) blocked.push("SUN");
  var want=[["cadence",cad],["order_days",days.join(",")],["blocked_days",blocked.join(",")],["lead_days",v("lead")],["safety_days",v("safety")],["cover_cap_days",v("cap")],["single_source_extra",on("sse")?1:0],
            ["review_on",v("review_on")],["review_target",v("review_target")],["note",v("note")]];
  var cur={cadence:r.cadence,order_days:r.order_days,blocked_days:r.blocked_days,lead_days:r.lead_days,safety_days:r.safety_days,cover_cap_days:r.cover_cap_days,single_source_extra:Number(r.single_source_extra)?1:0,review_on:r.review_on||"",review_target:r.review_target||"",note:r.note||""};
  var pairs=[], cadChanged=(cad!==r.cadence);
  want.forEach(function(w){ var f=w[0], val=w[1]; if(String(val)!==String(cur[f]==null?"":cur[f]) || (cadChanged&&(f==="order_days"||f==="cover_cap_days"))) pairs.push([f,val]); });
  var pz=on("paused"), was=!!Number(r.paused), why=v("pause_reason");
  if(pz&&(!was||why!==(r.pause_reason||""))){ pairs.push(["pause_reason",why||"paused by the owner"]); if(!was) pairs.push(["paused",1]); }
  if(!pz&&was) pairs.push(["paused",0]);
  if(!pairs.length){ poEditClose(i); return; }
  if(msg) msg.textContent="saving "+pairs.length+" change"+(pairs.length===1?"":"s")+"…";
  poSetRow(i,pairs).then(function(){ poEditClose(i); }).catch(function(e){ if(msg) msg.textContent="not saved: "+poWhy(e)+" — the fields above are as you left them"; });
}
/* ---- the two candidate lists: check-lists that stay put ---- */
function poCandRows(key,c,ir){
  var rule=(key==="never")?"never":"on_demand", rows=[];
  (c||[]).forEach(function(x){ rows.push({item:x.item, qty:x.qty, a:(key==="never")?x.last_sale_text:x.sales, b:(key==="never")?"":x.unit_rs, val:(key==="never")?Number(x.qty||0):Number(x.unit_p||0), ticked:false}); });
  (ir||[]).forEach(function(x){ if(x.rule===rule) rows.push({item:x.item, qty:null, a:"", b:"", val:-1, ticked:true}); });
  return rows;
}
function poCandRowHTML(key,x){
  return '<tr'+(x.ticked?' class="ticked"':'')+' data-item="'+esc(x.item)+'" data-name="'+esc(String(x.item).toLowerCase())+'" data-val="'+x.val+'"><td><input type="checkbox" onchange="poTick(this,\''+key+'\')"'+(x.ticked?' checked':'')+'></td>'+
    '<td>'+esc(x.item)+'<span class="po-rule">'+(key==="never"?"never re-order":"on demand")+'</span><span class="po-saved">✓ saved</span></td><td class="num">'+(x.qty==null?"—":x.qty)+'</td><td'+(key==="never"?'':' class="num"')+'>'+esc(x.a==null?"":x.a)+'</td>'+(key==="never"?'':'<td class="num">'+esc(x.b||"")+'</td>')+'</tr>';
}
function poCandList(key,title,sub,c,ir){
  var rows=poCandRows(key,c,ir), n=rows.filter(function(x){return x.ticked}).length;
  return '<details class="fold" id="poD_'+key+'"><summary><b>'+title+' — candidates (<span class="po-tot">'+rows.length+'</span>)</b> <span class="sub">'+sub+'</span></summary>'+
    '<div class="row po-tools"><span class="mut po-cnt">'+n+' of '+rows.length+' ticked</span> <button class="ghost" onclick="poTickAll(\''+key+'\',true)">Tick all shown</button> <button class="ghost" onclick="poTickAll(\''+key+'\',false)">Untick all shown</button> '+
    '<input type="text" placeholder="type part of a name" oninput="poApply(\''+key+'\')" class="po-filt"> <label class="mut">sort <select class="po-sort" onchange="poApply(\''+key+'\')"><option value="value">by '+(key==="never"?"stock":"unit value")+'</option><option value="name">by name</option></select></label> <label class="mut"><input type="checkbox" class="po-only" onchange="poApply(\''+key+'\')"> show ticked only</label></div>'+
    '<div class="tblwrap"><table><thead><tr><th></th><th>Item</th><th class="num">Stock</th>'+(key==="never"?'<th>Last sale</th>':'<th class="num">Sales</th><th class="num">Unit</th>')+'</tr></thead><tbody>'+rows.map(function(x){return poCandRowHTML(key,x)}).join("")+'</tbody></table></div></details>';
}
function poBody(key){ var d=$("poD_"+key); return d?d.querySelector("tbody"):null; }
function poCounts(key){
  var d=$("poD_"+key), tb=poBody(key); if(!d||!tb) return; var all=tb.children, n=0, m=all.length;
  for(var i=0;i<m;i++){ if(all[i].classList.contains("ticked")) n++ }
  var c=d.querySelector(".po-cnt"); if(c) c.textContent=n+" of "+m+" ticked"; var t=d.querySelector(".po-tot"); if(t) t.textContent=m;
}
function poApply(key){
  var d=$("poD_"+key), tb=poBody(key); if(!d||!tb) return;
  var f=((d.querySelector(".po-filt")||{}).value||"").toLowerCase().split(" ").filter(function(w){return w}), by=(d.querySelector(".po-sort")||{}).value||"value", only=!!((d.querySelector(".po-only")||{}).checked);
  var rows=Array.prototype.slice.call(tb.children);
  rows.sort(function(a,b){ if(by==="name") return a.getAttribute("data-name")<b.getAttribute("data-name")?-1:1; var va=Number(a.getAttribute("data-val")), vb=Number(b.getAttribute("data-val")); return vb!==va?vb-va:(a.getAttribute("data-name")<b.getAttribute("data-name")?-1:1); });
  rows.forEach(function(tr){ tb.appendChild(tr); var nm=tr.getAttribute("data-name"), show=true; for(var i=0;i<f.length;i++){ if(nm.indexOf(f[i])<0){show=false;break} } if(only&&!tr.classList.contains("ticked")) show=false; tr.style.display=show?"":"none"; });
}
function poTickRow(tr,key,on){
  var rule=(key==="never")?"never":"on_demand", item=tr.getAttribute("data-item"), cb=tr.querySelector("input[type=checkbox]"); if(cb) cb.disabled=true;
  return poFetch("/finance/porders/api/rules/item",{item:item,rule:rule,on:on}).then(function(j){
    if(cb){ cb.disabled=false; cb.checked=on; } tr.classList.toggle("ticked",on); poFlash(tr); poCounts(key);
    PO_R.counts=j.counts||PO_R.counts; poItemRowSet(item,rule,on,j.row); poItemsCount(); poSummaryFill(); loadNeeds();
  }).catch(function(e){ if(cb){ cb.disabled=false; cb.checked=!on; } throw e; });
}
function poTick(cb,key){ var tr=cb.closest("tr"); if(!tr) return; poTickRow(tr,key,cb.checked).catch(function(e){ alert(poWhy(e)) }); }
function poTickAll(key,on){
  var tb=poBody(key); if(!tb) return; var d=$("poD_"+key), c=d?d.querySelector(".po-cnt"):null;
  var rows=Array.prototype.slice.call(tb.children).filter(function(tr){ return tr.style.display!=="none" && tr.classList.contains("ticked")!==on }), k=0;
  if(!rows.length) return;
  function next(){ if(k>=rows.length){ poCounts(key); return; } if(c) c.textContent="saving "+(k+1)+" of "+rows.length+"…"; poTickRow(rows[k++],key,on).then(next).catch(function(e){ alert(poWhy(e)); poCounts(key); }); }
  next();
}
/* ---- Your item rules: grouped by rule, a cross to remove, inline numbers for keep / max, the add box with autocomplete ---- */
function poItemRowHTML(x){
  var v=(x.rule==="keep"||x.rule==="max_shelf")?'<input type="number" min="0" value="'+esc(x.value==null?"":x.value)+'" style="width:80px"> <button class="ghost po-x" onclick="poItemVal(this,\''+esc(x.rule)+'\')">save</button>':'';
  return '<tr data-item="'+esc(x.item)+'"><td>'+esc(x.item)+'<span class="po-saved">✓ saved</span></td><td>'+v+'</td><td class="mut">'+esc(x.set_by||"")+' '+esc((x.set_at||"").slice(0,10))+'</td><td><button class="ghost po-x" title="remove this rule" onclick="poItemOff(this,\''+esc(x.rule)+'\')">✕</button></td></tr>';
}
function poItemRulesHTML(ir,L){
  var h='<details class="fold" id="poD_items"><summary><b>Your item rules (<span id="poIrN">'+ir.length+'</span>)</b> <span class="sub">never re-order · on demand · keep-in-stock · max on shelf · internal use — the lists as the spine reads them</span></summary>';
  PO_RULE_ORDER.forEach(function(rule){ var rows=ir.filter(function(x){return x.rule===rule}); h+='<div class="po-grp" id="poG_'+rule+'"><b>'+PO_RULE_WORD[rule]+'</b> <span class="mut">(<span class="po-gn">'+rows.length+'</span>)</span><table><tbody>'+rows.map(poItemRowHTML).join("")+'</tbody></table></div>'; });
  h+='<div class="row" style="margin-top:8px"><input id="poItemName" class="po-txt" list="poItemList" placeholder="item as Marg prints it — start typing" style="min-width:240px" autocomplete="off" oninput="poItemSuggest(this.value)"><datalist id="poItemList"></datalist> <select id="poItemRule">'+PO_RULE_ORDER.map(function(r){return '<option value="'+r+'">'+PO_RULE_WORD[r]+((r==="keep"||r==="max_shelf")?" (units)":"")+'</option>'}).join("")+'</select> <input id="poItemVal" type="number" placeholder="units" style="width:90px"> <button class="ghost" onclick="poItemAdd()">add</button> <span class="mut" id="poItemMsg"></span></div>'+
    '<div class="mut" style="margin-top:6px">the spine\'s lists: internal use '+(L.internal_use||[]).length+' · never re-order '+(L.never_reorder||[]).length+' · on demand '+(L.on_demand||[]).length+' (orthotics cycle retired)</div></details>';
  return h;
}
function poItemFind(rule,item){ var g=$("poG_"+rule); if(!g) return null; var trs=g.querySelectorAll("tbody tr"); for(var i=0;i<trs.length;i++){ if(String(trs[i].getAttribute("data-item")).toUpperCase()===String(item).toUpperCase()) return trs[i] } return null; }
function poItemRowSet(item,rule,on,row){
  PO_RULE_ORDER.forEach(function(r){ var tr=poItemFind(r,item); if(tr&&(!on||r!==rule)) tr.parentNode.removeChild(tr); });
  if(on){ var g=$("poG_"+rule); if(g){ var tb=g.querySelector("tbody"); var x=row||{item:item,rule:rule,value:null,set_by:"",set_at:""}; tb.insertAdjacentHTML("beforeend",poItemRowHTML(x)); poFlash(tb.lastElementChild); } }
  PO_RULE_ORDER.forEach(function(r){ var g=$("poG_"+r); if(g){ var n=g.querySelector(".po-gn"); if(n) n.textContent=g.querySelectorAll("tbody tr").length } });
  if(PO_R&&PO_R.item_rules){ PO_R.item_rules=PO_R.item_rules.filter(function(x){return String(x.item).toUpperCase()!==String(item).toUpperCase()}); if(on) PO_R.item_rules.push(row||{item:item,rule:rule}); }
}
function poItemsCount(){ var n=$("poIrN"); if(!n) return; var tot=0; PO_RULE_ORDER.forEach(function(r){ var g=$("poG_"+r); if(g) tot+=g.querySelectorAll("tbody tr").length }); n.textContent=tot; }
function poCandMark(item,rule,on){
  var key=(rule==="never")?"never":(rule==="on_demand"?"od":null); if(!key) return; var tb=poBody(key); if(!tb) return;
  for(var i=0;i<tb.children.length;i++){ var tr=tb.children[i]; if(String(tr.getAttribute("data-item")).toUpperCase()===String(item).toUpperCase()){ tr.classList.toggle("ticked",on); var cb=tr.querySelector("input[type=checkbox]"); if(cb) cb.checked=on; poFlash(tr); poCounts(key); return; } }
  if(on){ tb.insertAdjacentHTML("beforeend",poCandRowHTML(key,{item:item,qty:null,a:"",b:"",val:-1,ticked:true})); poCounts(key); }
}
function poItemOff(btn,rule){
  var tr=btn.closest("tr"), item=tr.getAttribute("data-item"); btn.disabled=true;
  poFetch("/finance/porders/api/rules/item",{item:item,rule:rule,on:false}).then(function(j){ PO_R.counts=j.counts||PO_R.counts; poItemRowSet(item,rule,false,null); poCandMark(item,rule,false); poItemsCount(); poSummaryFill(); loadNeeds(); })
    .catch(function(e){ btn.disabled=false; alert(poWhy(e)); });
}
function poItemVal(btn,rule){
  var tr=btn.closest("tr"), item=tr.getAttribute("data-item"), inp=tr.querySelector("input[type=number]"), val=inp?inp.value:""; btn.disabled=true;
  poFetch("/finance/porders/api/rules/item",{item:item,rule:rule,on:true,value:(val===""?null:val)}).then(function(j){ btn.disabled=false; poFlash(tr); PO_R.counts=j.counts||PO_R.counts; }).catch(function(e){ btn.disabled=false; alert(poWhy(e)); });
}
function poItemSuggest(q){
  clearTimeout(PO_UI.sugT); if(!q||q.trim().length<2) return;
  PO_UI.sugT=setTimeout(function(){ fetch("/finance/porders/api/rules/items?q="+encodeURIComponent(q.trim()),{cache:"no-store"}).then(srvJSON).then(function(x){ var j=x.j||{}; var dl=$("poItemList"); if(!dl||!j.ok) return; dl.innerHTML=(j.items||[]).map(function(it){return '<option value="'+esc(it.item)+'">'+esc(it.packing||"")+(it.qty!=null?' · stock '+it.qty:'')+'</option>'}).join(""); }).catch(function(){}); },250);
}
function poItemAdd(){
  var n=(($("poItemName")||{}).value||"").trim(), r=($("poItemRule")||{}).value||"keep", v=($("poItemVal")||{}).value||"", msg=$("poItemMsg");
  if(!n){ if(msg) msg.textContent="type the item's name first"; return; }
  if(msg) msg.textContent="saving…";
  poFetch("/finance/porders/api/rules/item",{item:n,rule:r,on:true,value:(v===""?null:v)}).then(function(j){ PO_R.counts=j.counts||PO_R.counts; poItemRowSet(j.item||n,r,true,j.row); poCandMark(j.item||n,r,true); poItemsCount(); poSummaryFill(); if(msg) msg.textContent="saved ✓"; $("poItemName").value=""; $("poItemVal").value=""; loadNeeds(); })
    .catch(function(e){ if(msg) msg.textContent="not saved: "+poWhy(e); });
}
/* ---- the block: drawn once per load, in the brief's order; every later change patches in place ---- */
function poHTML(j){
  var st=j.settings||{}, R=j.rules||[], c=j.candidates||{}, ir=j.item_rules||[], L=j.lists||{};
  var h=poApproveHTML("Top");
  h+='<div id="poFreezeLine">'+poFreezeHTML()+'</div>';
  h+='<div class="mut" style="margin:6px 0">Shop-wide: lead '+esc(st["order.lead_days"])+' day · safety '+esc(st["order.safety_days"])+' · single-source extra '+esc(st["order.single_source_extra_days"])+' · caps weekly '+esc(st["order.cap_weekly"])+' / fortnightly '+esc(st["order.cap_fortnightly"])+' / monthly '+esc(st["order.cap_monthly"])+' days · min line ₹'+Math.round((st["order.min_line_p"]||0)/100)+' · min order ₹'+Math.round((st["order.min_order_p"]||0)/100)+' · blocked '+esc(st["order.blocked_days"])+' · interim orders '+(st["order.interim"]==="1"?'ON from '+esc(st["order.interim_from"]):'off')+' · notices to '+esc(j.notice_to)+' at 09:00, 12:00, 15:00, 17:00 · go-live '+esc(st["order.go_live"])+'.</div>';
  h+='<details class="fold" id="poD_sup"><summary><b>Suppliers ('+R.length+')</b> <span class="sub">· one plain line each, Kedar first · "edit" opens the line into a form · your edits are kept for ever</span></summary><div class="tblwrap"><table><tbody>';
  R.forEach(function(r,i){ h+='<tr id="poSup_'+i+'">'+poSupRowHTML(i)+'</tr>'; });
  h+='</tbody></table></div></details>';
  h+=poCandList("never","Never re-order","· in stock, no sale in "+esc(c.never_days)+" days · tick = never proposed; untick = back in the running",c.never,ir);
  h+=poCandList("od","On demand","· at most "+esc(c.on_demand_max_sales)+" sales in "+esc(c.on_demand_days)+" days and unit value ≥ "+esc(c.on_demand_min_rs)+" · tick = ordered only when asked",c.on_demand,ir);
  h+=poItemRulesHTML(ir,L);
  if(j.kedar_review){ var ki=poSupIdx("KEDAR PHARMACEUTICAL"); h+='<div class="alert info" style="margin-top:8px">'+esc(j.kedar_review.text)+(ki>=0?' <button class="ghost" onclick="poSetRow('+ki+',[[\'move_to\',\''+esc(j.kedar_review.target)+'\']],this)">Move Kedar to '+esc(j.kedar_review.target)+'</button>':'')+'</div>'; }
  if((j.holidays||[]).length) h+='<div class="mut" style="margin-top:6px">Holidays (Shavez keeps the list): '+(j.holidays||[]).map(function(x){return esc(x.day)+(x.note?' ('+esc(x.note)+')':'')}).join(", ")+'</div>';
  h+='<details class="fold" id="poD_audit" style="margin-top:6px"><summary class="mut">last changes ('+(j.audit||[]).length+')</summary><div class="tblwrap"><table><tbody>'+(j.audit||[]).map(function(a){return '<tr><td class="mut">'+esc((a.at||"").slice(0,16).replace("T"," "))+'</td><td>'+esc(a.who)+'</td><td>'+esc(a.supplier_norm||"")+'</td><td>'+esc(a.field)+'</td><td class="mut">'+esc(a.old==null?"":a.old)+' → '+esc(a.new==null?"":a.new)+'</td></tr>'}).join("")+'</tbody></table></div><div class="mut">refreshed on the next open of this block</div></details>';
  h+=poApproveHTML("Bottom");
  return h;
}
function loadPORules(){
  fetch("/finance/porders/api/rules/state?_="+Date.now(),{cache:"no-store"}).then(srvJSON).then(function(x){
    var j=x.j||{}; var o=$("poRules"); if(!o)return; if(!j.ok){o.textContent=j.message||j.error||"could not load";return}
    PO_R=j; PO_R.counts=null;
    poKeepOpen(function(){ o.innerHTML=poHTML(j); });
    poApply("never"); poApply("od");
    var e=$("poNewN"); if(e) e.textContent=j.new_items_n;
  }).catch(function(){var o=$("poRules"); if(o) o.textContent="could not reach the server"});
}
'''


def build_html(s):
    s = rep(s, '''<details class="fold" id="pordersRulesCard" data-load="loadPORules"><summary>Buying rules for medicines <span class="sub">· one line per supplier, tap to edit · the lists · the freeze · Approve rules (S410, D626)</span></summary><div>''',
            '''<details class="fold" id="pordersRulesCard" data-load="loadPORules"><summary>Buying rules for medicines <span class="sub">· Approve rules · the freeze · one line per supplier, edit in place · the two check-lists · your item rules (S410 D626 · S414)</span></summary><div>''', "card summary")
    s = rep(s, '''details.fold>summary::-webkit-details-marker{display:none}details.fold>summary:before{content:"\\25B8";color:var(--text-3);font-weight:400}\n''',
            '''details.fold>summary::-webkit-details-marker{display:none}details.fold>summary:before{content:"\\25B8";color:var(--text-3);font-weight:400}\n''' + CSS.lstrip("\n"), "css")
    s = rep_between(s, "/* ---- S410 (D626): the rules as settings -- one plain line per supplier, tap to edit; the lists; the freeze; Approve rules ---- */\n",
                    "function loadPOOos(){", JS, "the rules block")
    return s


# ============================================================================ order_rules.py: the two small additions
def build_rules(s):
    s = rep(s, '''#        POST /finance/porders/api/rules/item          {item, rule, on, value}   per-item override + the lists (owner)
''', '''#        POST /finance/porders/api/rules/item          {item, rule, on, value}   per-item override + the lists (owner)
#                                                      S414: the answer carries counts {item_rules, by_rule, lists} and the row
#        GET  /finance/porders/api/rules/items?q=      S414: <= 20 item names from the stock master for the add box (owner)
''', "doc")
    s = rep(s, '''    con.commit()
    return dict(ok=True, item=item, rule=rule, on=bool(on), value=value, lists=load_lists()), 200


def candidates(con, today=None):''', '''    con.commit()
    row = con.execute("SELECT item, rule, value, set_by, set_at FROM order_item_rule WHERE item_norm=?", (k,)).fetchone() if on else None
    return dict(ok=True, item=item, rule=rule, on=bool(on), value=value, lists=load_lists(), counts=rule_counts(con), row=(dict(row) if row else None)), 200


def rule_counts(con):
    """S414 (F-635): what the owner's page shows after a tick WITHOUT a re-fetch -- the per-item rules by rule and the lists' sizes."""
    ensure(con)
    by = {r: 0 for r in ITEM_RULES}
    for rule, n in con.execute("SELECT rule, COUNT(*) FROM order_item_rule GROUP BY rule"):
        if rule in by:
            by[rule] = int(n or 0)
    j = load_lists()
    return dict(item_rules=sum(by.values()), by_rule=by, lists={k: len(j.get(k) or []) for k in ("never_reorder", "on_demand", "internal_use")})


def item_names(con, q, limit=20):
    """S414: item names from the newest stock snapshot (the stock master) for the add box's autocomplete -- every typed word must
    appear in the name; at most `limit` names, in name order."""
    words = [w for w in re.split(r"\\s+", str(q or "").strip().upper()) if w]
    _as_on, snap = _pa()._latest_snapshot(con)
    out = []
    for k in sorted(snap, key=lambda x: str(snap[x]["item"]).upper()):
        s = snap[k]
        up = str(s["item"]).upper()
        if all(w in up for w in words):
            out.append(dict(item=s["item"], qty=s["qty"], packing=s.get("packing") or ""))
            if len(out) >= limit:
                break
    return out


def candidates(con, today=None):''', "counts + item names")
    s = rep(s, '''@bp.route("/finance/porders/api/rules/freeze", methods=["POST"])
def api_rules_freeze():''', '''@bp.route("/finance/porders/api/rules/items")
def api_rules_items():
    """S414: the add box's autocomplete -- names only, from the stock master; owner."""
    u, con, kind, err = _auth()
    if err:
        return err
    if kind != "owner":
        return jsonify(ok=False, error="owner_only"), 403
    return jsonify(ok=True, items=item_names(con, request.args.get("q", "")))


@bp.route("/finance/porders/api/rules/freeze", methods=["POST"])
def api_rules_freeze():''', "items route")
    return s


BUILDERS = {"finance_approvals.html": build_html, "order_rules.py": build_rules}


def main():
    args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
    fin, out = args.get("--finance", "/root/finance"), args.get("--out")
    if not out:
        sys.exit(__doc__)
    os.makedirs(out, exist_ok=True)
    for name, fn in BUILDERS.items():
        built = fn(load(os.path.join(fin, SRC[name]), name))
        b = built.encode("utf-8")
        with io.open(os.path.join(out, name), "wb") as fh:
            fh.write(b)
        print("built %s  %s -> %s  (%d bytes)" % (name, FROM[name][:8], md5(b), len(b)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
