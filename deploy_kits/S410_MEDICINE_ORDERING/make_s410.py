#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s410.py -- kit S410_MEDICINE_ORDERING (D626). Builds the six patched files FROM THE LIVE BYTES with anchored edits
(every anchor must occur exactly once, else it refuses) after checking each file's FROM pin:

  porders.py                the module mounts order_rules (fail-soft); state() carries 'today' (the day's proposals) and the
                            freeze; send_med refuses while frozen (423)
  porders.html              section 4 becomes "Aaj ke order (N)": the day's proposals with ± / remove / bhejo (the S403 wa.me
                            flow), "Beech ka order" cards, the contextual text, the freeze / paused reason; section 5 the
                            holiday list (senders); the engine's full plan folded away
  sanjeevni_approvals.py    v1.10: Needs you gains order_rules' lines (NEEDS_YOU_WITHOUT_S410=1 for S400's frozen walk only)
  finance_approvals.html    the red "Out of stock both ends" bar at the top; the rules fold rewritten (one plain line per
                            supplier, tap to edit; candidates; item overrides; freeze; Approve rules); "New items this month";
                            the Needs-you review button
  darpan_kal.py / .html     the count line 'Aaj ke order — N (M bheja)' on Darpan's card

Usage: make_s410.py --finance /root/finance --out DIR
"""
import hashlib
import io
import os
import sys

FROM = {
    "porders.py": "d08f59e2fb4e42e173f135f06da28787",
    "porders.html": "76a173af5faee643fa0d0139731b10e8",
    "sanjeevni_approvals.py": "3cde91fbfead8e698ca1e3981362a6d3",
    "finance_approvals.html": "77c79211845f3416a3211d22ced3d7db",
    "darpan_kal.py": "401ee01c7cbd49cea1c34665c99bab60",
    "darpan_kal.html": "1bedb46991bc5b531e809519c50ee990",
}


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


# ---------------------------------------------------------------- porders.py
def build_porders(s):
    s = rep(s, '''#  porders.py  ·  v1.0  ·  kit S403_PURCHASE_ORDERS_LIVE  ·  Session 283 (Sanjeevni)  ·  D618
#
''', '''#  porders.py  ·  v1.1  ·  kit S410_MEDICINE_ORDERING  ·  Session 283 (Sanjeevni)  ·  D626
#
#  v1.1 (S410, D626, 26-Sep-2026): mounts order_rules (the medicine buying rules as settings, fixed order days, the ordering
#  team's day); state() carries 'today' (the day's proposals, the freeze, the contextual text); send_med refuses while frozen.
#
''', "header")
    s = rep(s, '''VERSION = "1.0"
KIT = "S403_PURCHASE_ORDERS_LIVE"
''', '''VERSION = "1.1"
KIT = "S410_MEDICINE_ORDERING"
''', "version")
    s = rep(s, '''    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp)
    return bp
''', '''    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp)
    # S410 (D626): the medicine buying rules as settings ride on this screen's unit; fail-soft -- the screen never waits for them
    try:
        import order_rules                                    # noqa: PLC0415
        order_rules.init(app, db_getter, require_fn, unit=ACCESS_UNIT)
    except Exception as _ex_or:                               # noqa: BLE001
        print("order_rules NOT mounted: %s" % _ex_or, file=sys.stderr)
    return bp
''', "mount")
    s = rep(s, '''def state(con, u=None, kind="viewer"):
    ensure_schema(con)
''', '''def _day_s410(con):
    """S410 (D626): the day's proposals (fixed + interim), the freeze, the contextual text -- read from order_rules, fail-soft."""
    try:
        import order_rules                                    # noqa: PLC0415
        return order_rules.day_state(con)
    except Exception as e:                                    # noqa: BLE001
        return dict(ok=False, n=0, sent=0, unsent=0, text="", proposals=[], frozen=None, error=str(e)[:80])


def _frozen_s410(con):
    try:
        import order_rules                                    # noqa: PLC0415
        return order_rules._frozen(con)
    except Exception:                                         # noqa: BLE001
        return None


def state(con, u=None, kind="viewer"):
    ensure_schema(con)
''', "day helper")
    s = rep(s, '''                meds=dict(rules_ok=bool(rules), rules=rules, plan=meds),
                all=allrows, keep_total=sum(int(it["keep"]) for it in items))
''', '''                meds=dict(rules_ok=bool(rules), rules=rules, plan=meds),
                today=_day_s410(con),                                   # S410 (D626)
                all=allrows, keep_total=sum(int(it["keep"]) for it in items))
''', "state today")
    s = rep(s, '''    if not _rules_ok(con):
        return jsonify(ok=False, error="rules_pending", message="Doctor sahab ke rules ka intezaar."), 403
    pa = _pa()
    b = request.get_json(silent=True) or {}
    vendor = str(b.get("vendor") or "").strip()
''', '''    if not _rules_ok(con):
        return jsonify(ok=False, error="rules_pending", message="Doctor sahab ke rules ka intezaar."), 403
    fr = _frozen_s410(con)                                    # S410 (D626): the owner's freeze
    if fr:
        return jsonify(ok=False, error="frozen", message="Medicine ordering band hai: %s" % (fr.get("reason") or "")), 423
    pa = _pa()
    b = request.get_json(silent=True) or {}
    vendor = str(b.get("vendor") or "").strip()
''', "send_med freeze gate")
    return s


# ---------------------------------------------------------------- porders.html
def build_porders_html(s):
    s = rep(s, '''<!-- S403_PURCHASE_ORDERS_LIVE (26-Sep-2026, D618): ONE screen''', '''<!-- S410_MEDICINE_ORDERING (26-Sep-2026, D626): section 4 is the ordering team's day -- "Aaj ke order (N)": the day's proposals
     per supplier (item · shelf · order qty, ± allowed, a line removable), bhejo -> the S403 wa.me flow, SENT marked; "Beech ka order"
     cards; the contextual text at the top; the freeze / paused reason; section 5 the holiday list (senders). The engine's full plan
     stays one tap away. Nothing else on the screen moves.
  -- kit S403 header below --
<!-- S403_PURCHASE_ORDERS_LIVE (26-Sep-2026, D618): ONE screen''', "header")
    s = rep(s, ''' s3:["Bill scan karo (%d)","Bill scans pending (%d)"], s4:["Medicines (rules ka intezaar)","Medicines (awaiting the buying rules)"],''',
            ''' s3:["Bill scan karo (%d)","Bill scans pending (%d)"], s4:["Aaj ke order (%d)","Today's orders (%d)"], s5:["Chhutti ke din (%d)","Holidays (%d)"],
 bhejo:["%s ko order bhejo","Send the order to %s"], remove:["hatao","remove"], frozen:["Medicine ordering band hai","Medicine ordering is frozen"],
 held:["Rukaa hua","Held"], interim:["Beech ka order","Interim order"], sentby:["bheja — %s, %s","sent — %s, %s"], nonetoday:["Aaj koi order nahi.","No order due today."],
 plan:["Engine ka poora plan (dekhne ke liye)","The engine's full plan (for reference)"], addhol:["Chhutti jodo","Add a holiday"], holnote:["kyun","why"],''',
            "labels")
    s = rep(s, '''let S=null, MSG=null, BUSY=false, EN=false, QTY={}, PICK={}, OPEN={1:true}, SHORTQ={};''',
            '''let S=null, MSG=null, BUSY=false, EN=false, QTY={}, PICK={}, OPEN={1:true,4:true}, SHORTQ={}, DQ={};''', "state vars")
    s = rep(s, ''' // 4 -- medicines
 let m="";
 if(!s.meds.rules_ok) m+='<div class="muted">'+L("rules")+'</div>';
 (s.meds.plan.vendors||[]).forEach((v,i)=>{
  m+='<div class="line"><div class="nm">'+esc(v.vendor)+'</div><table>'+v.lines.map(l=>'<tr><td>'+esc(l.item)+'</td><td class="n">'+l.on_hand+'</td><td class="n"><b>'+l.qty+'</b> '+esc(l.unit)+'</td></tr>').join("")+'</table>'+
     (s.meds.rules_ok&&canWrite()&&v.has_phone?'<span class="btn ok sm" onclick="sendMed(\\''+esc(v.vendor).replace(/'/g,"\\\\'")+'\\')">'+L("sendm")+'</span>':'')+'</div>';
 });
 if(!(s.meds.plan.vendors||[]).length) m+='<div class="muted">'+(EN?'Nothing to order on today\\'s stock.':'Aaj ke stock par kuch order nahi.')+'</div>';
 h+=sec(4,L("s4"),(s.meds.plan.vendors||[]).length,'',m);
 el("body").innerHTML=h;
}''', ''' // 4 -- the ordering team's day (S410, D626): the proposals prepared at 09:00, ± / remove / bhejo; the engine's plan folded away
 const d=s.today||{proposals:[],n:0,sent:0,unsent:0,text:""};
 let m="";
 if(d.frozen) m+='<div class="saved err"><div class="t">'+L("frozen")+'</div><div class="l">'+esc(d.frozen.reason||"")+' · '+esc((d.frozen.at||"").slice(0,16))+'</div></div>';
 if(!s.meds.rules_ok) m+='<div class="muted">'+L("rules")+'</div>';
 if(d.text) m+='<div class="sent">'+esc(d.text)+'</div>';
 (d.merged_ahead||[]).forEach(x=>{m+='<div class="muted">'+esc(x.vendor)+': '+esc(x.day)+' ka order nahi gaya — '+esc(x.into)+' ke order mein judega</div>';});
 (d.proposals||[]).forEach(p=>{
  if(!DQ[p.id]){DQ[p.id]={}; p.lines.forEach(l=>{DQ[p.id][l.item]=l.qty;});}
  const q=DQ[p.id];
  m+='<div class="line'+(p.status==="sent"?' done':'')+'"><div class="nm">'+esc(p.vendor)+(p.kind==="interim"?'<span class="tag approx">'+L("interim")+'</span>':'')+(p.status==="held"?'<span class="tag">'+L("held")+'</span>':'')+'</div>';
  if(p.reason) m+='<div class="muted">'+esc(p.reason)+'</div>';
  if(p.carried_from) m+='<div class="muted">'+esc(p.carried_from)+' ka order bhi isme</div>';
  if(p.status==="sent"){ m+='<div class="sent">'+L("sentby",esc(p.sent_text),esc(p.sent_by||""))+' · order #'+p.sent_order_id+'</div><table>'+p.lines.map(l=>'<tr><td>'+esc(l.item)+'</td><td class="n"><b>'+l.qty+'</b> '+esc(l.unit)+'</td></tr>').join("")+'</table>'; }
  else {
   m+='<table>'+p.lines.map(l=>'<tr><td>'+esc(l.item)+'</td><td class="n">'+l.on_hand+'</td><td class="n">'+(canWrite()&&p.status!=="held"?'<span class="qty"><span class="btn pm" onclick="pq('+p.id+',\\''+esc(l.item).replace(/'/g,"\\\\'")+'\\',-1)">−</span><b>'+(q[l.item]||0)+'</b><span class="btn pm" onclick="pq('+p.id+',\\''+esc(l.item).replace(/'/g,"\\\\'")+'\\',1)">+</span></span> '+esc(l.unit)+' <span class="btn chip" onclick="pq('+p.id+',\\''+esc(l.item).replace(/'/g,"\\\\'")+'\\',-9999)">'+L("remove")+'</span>':'<b>'+l.qty+'</b> '+esc(l.unit))+'</td></tr>').join("")+'</table>';
   if(canWrite()&&p.status!=="held"&&s.meds.rules_ok&&!d.frozen) m+='<span class="btn ok big" onclick="sendDay('+p.id+')">'+L("bhejo",esc(p.short||p.vendor))+'</span>';
  }
  m+='</div>';
 });
 if(!(d.proposals||[]).length) m+='<div class="muted">'+L("nonetoday")+'</div>';
 m+='<details style="margin-top:8px"><summary class="muted">'+L("plan")+'</summary>';
 (s.meds.plan.vendors||[]).forEach((v,i)=>{
  m+='<div class="line"><div class="nm">'+esc(v.vendor)+'</div><table>'+v.lines.map(l=>'<tr><td>'+esc(l.item)+'</td><td class="n">'+l.on_hand+'</td><td class="n"><b>'+l.qty+'</b> '+esc(l.unit)+'</td></tr>').join("")+'</table></div>';
 });
 if(!(s.meds.plan.vendors||[]).length) m+='<div class="muted">'+(EN?'Nothing to order on today\\'s stock.':'Aaj ke stock par kuch order nahi.')+'</div>';
 m+='</details>';
 h+=sec(4,L("s4",d.n||0),(d.unsent||0),(d.unsent?'red':(d.n?'ok':'')),m);
 // 5 -- the holiday list (S410): an order day on a holiday moves to the previous working day; senders keep it
 let hl="";
 (d.holidays||[]).forEach(x=>{hl+='<div class="line"><b>'+esc(x.day)+'</b> <span class="muted">'+esc(x.note||"")+' · '+esc(x.set_by||"")+'</span>'+(canWrite()?' <span class="btn chip" onclick="holiday(\\''+esc(x.day)+'\\',true)">'+L("remove")+'</span>':'')+'</div>';});
 if(canWrite()) hl+='<div class="line"><input type="date" id="holDay"> <input class="q" style="width:140px;font-size:15px;text-align:left" id="holNote" placeholder="'+L("holnote")+'"> <span class="btn ok sm" onclick="holiday(null,false)">'+L("addhol")+'</span></div>';
 h+=sec(5,L("s5",(d.holidays||[]).length),(d.holidays||[]).length,'',hl);
 el("body").innerHTML=h;
}
function pq(pid,item,dl){const q=DQ[pid]||(DQ[pid]={}); q[item]=dl<=-9999?0:Math.max(0,(q[item]||0)+dl); render();}
async function sendDay(pid){
 if(BUSY)return;BUSY=true;
 const p=(S.today.proposals||[]).find(x=>x.id===pid); const q=DQ[pid]||{};
 const lines=(p?p.lines:[]).map(l=>({item:l.item,qty:q[l.item]!=null?q[l.item]:l.qty})).filter(l=>l.qty>0);
 try{const j=await post("/finance/porders/api/day/send",{proposal_id:pid,lines});
  MSG={kind:j.already?"dup":"",title:j.already?L("dup"):L("saved"),lines:[esc(j.message||""),"Order #"+j.order_id+(j.sent_text?" · "+esc(j.sent_text):"")+(j.by?" · "+esc(j.by):""),(j.wa_url?L("openwa"):"")]};
  delete DQ[pid]; await load(); if(j.wa_url){window.location.href=j.wa_url;}
 }catch(e){MSG={kind:(e.j&&e.j.already)?"dup":"err",title:(e.j&&e.j.already)?L("dup"):L("err"),lines:[esc(e.message)]};render();window.scrollTo(0,0);}
 BUSY=false;
}
async function holiday(day,remove){
 if(BUSY)return;BUSY=true;
 const d=day||(el("holDay")||{}).value, note=(el("holNote")||{}).value||"";
 try{ if(!d) throw new Error(EN?"pick a date":"tareekh chuniye"); await post("/finance/porders/api/rules/holiday",{day:d,note,remove:!!remove}); await load(); }
 catch(e){MSG={kind:"err",title:L("err"),lines:[esc(e.message)]};render();window.scrollTo(0,0);}
 BUSY=false;
}''', "section 4 + 5")
    return s


# ---------------------------------------------------------------- sanjeevni_approvals.py
def build_approvals(s):
    s = rep(s, '''#  sanjeevni_approvals.py  ·  v1.9  ·  kit S408_MONTH_END_PACKS  ·  Session 283
#
''', '''#  sanjeevni_approvals.py  ·  v1.10  ·  kit S410_MEDICINE_ORDERING  ·  Session 283 (Sanjeevni)
#
#  v1.10 (S410, D626, 26-Sep-2026): Needs you gains order_rules' lines -- an order still unsent on its next order day, a supplier's
#  month running above its 90-day pace, the Kedar review (one tap), the freeze, the Sunday one-liner (fail-soft).
#  NEEDS_YOU_WITHOUT_S410=1 leaves them out -- set only by an older kit's frozen walk re-run.
#
''', "header")
    s = rep(s, '''VERSION = "1.9"
''', '''VERSION = "1.10"
''', "version")
    s = rep(s, '''    # 7 · the statement's age (a word, not a fault)
''', '''    # 13 · S410 (D626): the medicine ordering day -- a stuck order, a month above pace, the Kedar review, the freeze (fail-soft).
    #      NEEDS_YOU_WITHOUT_S410=1 is set ONLY by an older kit's frozen walk re-run; the service never sets it.
    if os.environ.get("NEEDS_YOU_WITHOUT_S410") != "1":
        try:
            import order_rules  # noqa: PLC0415
            lines.extend(order_rules.needs_you_lines(con))
        except Exception:  # noqa: BLE001
            pass
    # 7 · the statement's age (a word, not a fault)
''', "needs-you lines")
    return s


# ---------------------------------------------------------------- finance_approvals.html
def build_approvals_html(s):
    s = rep(s, '''<!doctype html>
<!-- S406_RETURNS_TWO_KINDS (Session 283, 26-Sep-2026, D622)''', '''<!doctype html>
<!-- S410_MEDICINE_ORDERING (Session 283, 26-Sep-2026, D626): the red "Out of stock both ends -- N" bar at the top (only when N > 0);
     the Purchase orders card's rules fold rewritten -- one plain line per supplier, tap to edit, the candidates lists, the per-item
     overrides, the freeze, one tap "Approve rules"; the collapsible "New items this month -- N"; the Needs-you review button. Nothing
     else on the page moves.
  -- kit S406 header below --
<!-- S406_RETURNS_TWO_KINDS (Session 283, 26-Sep-2026, D622)''', "header")
    s = rep(s, '''<div id="alertBar"></div>
''', '''<div id="alertBar"></div>
<div id="oosBar"></div>
''', "oos bar")
    s = rep(s, '''<details class="fold" id="pordersRulesCard" data-load="loadPORules"><summary>Buying rules for medicines <span class="sub">· the S225 settings and the do-not-order list, one sitting</span></summary><div>
  <div id="poRules">loading&hellip;</div>
</div></details>
''', '''<details class="fold" id="pordersRulesCard" data-load="loadPORules"><summary>Buying rules for medicines <span class="sub">· one line per supplier, tap to edit · the lists · the freeze · Approve rules (S410, D626)</span></summary><div>
  <div id="poRules">loading&hellip;</div>
</div></details>
<details class="fold" id="pordersNewCard" data-load="loadPONew"><summary>New items this month — <span id="poNewN">…</span> <span class="sub">· first-ever purchases: salt · supplier · manufacturer · MRP · rate, as the exports hold them</span></summary><div>
  <div class="row"><span class="mut">month</span><input type="month" id="poNewMonth" onchange="loadPONew()"></div>
  <div id="poNew">loading&hellip;</div>
</div></details>
''', "rules + new items folds")
    s = rep(s, '''function loadPORules(){
  fetch("/finance/porders/api/rules?_="+Date.now(),{cache:"no-store"}).then(srvJSON).then(function(x){
    var j=x.j||{}; var o=$("poRules"); if(!o)return; if(!j.ok){o.textContent="could not load";return}
    var s=j.s225||{}, L=j.lists||{};
    var h='<div class="mut">S225 engine: pace over '+s.pace_days+' days · lead '+s.lead_days+' + safety '+s.safety_days+' days · cover at most '+s.max_cover_days+' days · cadence weekly above ₹'+s.tier_weekly_rs+'/month, fortnightly above ₹'+s.tier_fortnight_rs+', else monthly · a line below ₹'+s.min_line_rs+' is dropped · '+esc(s.rounding)+'.</div>';
    ["never_reorder","on_demand","internal_use","orthotics_cycle"].forEach(function(k){h+='<div><b>'+k.replace(/_/g," ")+'</b>: '+((L[k]||[]).length?(L[k]||[]).map(esc).join(", "):'<span class="mut">empty</span>')+'</div>'});
    h+=j.approved?'<div class="ok" style="margin-top:8px">✓ approved by '+esc(j.approved.by)+' at '+esc(j.approved.at)+' — the staff screen may send medicine orders.</div>'
                 :'<div style="margin-top:8px"><button onclick="poApprove()">I approve these buying rules and the do-not-order list</button> <span class="mut">Until then the staff screen says "Doctor sahab ke rules ka intezaar".</span></div>';
    o.innerHTML=h;
  }).catch(function(){var o=$("poRules"); if(o) o.textContent="could not reach the server"});
}
function poApprove(){
  if(!confirm("Approve the medicine buying rules as they stand? The staff screen will then send medicine orders on WhatsApp.")) return;
  fetch("/finance/porders/api/rules/approve",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"}).then(srvJSON).then(function(x){var j=x.j||{}; if(!j.ok){alert(j.message||j.error||"not recorded");return} loadPORules(); loadNeeds();}).catch(function(){alert("the server could not be reached")});
}
''', '''/* ---- S410 (D626): the rules as settings -- one plain line per supplier, tap to edit; the lists; the freeze; Approve rules ---- */
var PO_R=null;
function loadPORules(){
  fetch("/finance/porders/api/rules/state?_="+Date.now(),{cache:"no-store"}).then(srvJSON).then(function(x){
    var j=x.j||{}; var o=$("poRules"); if(!o)return; if(!j.ok){o.textContent=j.message||j.error||"could not load";return}
    PO_R=j; var st=j.settings||{};
    var h='';
    if(j.frozen) h+='<div class="alert bad">⛔ Medicine ordering is FROZEN since '+esc((j.frozen.at||"").slice(0,16))+' — '+esc(j.frozen.reason||"")+' <button class="ghost" onclick="poFreeze(false)">Unfreeze</button></div>';
    else h+='<div class="row"><button class="ghost" onclick="poFreeze(true)">Freeze all medicine ordering</button> <span class="mut">one tap; the reason shows to staff; unfreeze the same way</span></div>';
    h+='<div class="mut" style="margin:6px 0">Shop-wide: lead '+esc(st["order.lead_days"])+' day · safety '+esc(st["order.safety_days"])+' · single-source extra '+esc(st["order.single_source_extra_days"])+' · caps weekly '+esc(st["order.cap_weekly"])+' / fortnightly '+esc(st["order.cap_fortnightly"])+' / monthly '+esc(st["order.cap_monthly"])+' days · min line ₹'+Math.round((st["order.min_line_p"]||0)/100)+' · min order ₹'+Math.round((st["order.min_order_p"]||0)/100)+' · blocked '+esc(st["order.blocked_days"])+' · interim orders '+(st["order.interim"]==="1"?'ON from '+esc(st["order.interim_from"]):'off')+' · notices to '+esc(j.notice_to)+' at 09:00, 12:00, 15:00, 17:00 · go-live '+esc(st["order.go_live"])+'.</div>';
    h+='<div><b>Per supplier</b> <span class="mut">(cadence from the shop\\'s own rhythm; your edits are kept for ever; the seed re-runs monthly)</span></div><div class="tblwrap"><table><tbody>';
    (j.rules||[]).forEach(function(r){
      var sn=esc(r.supplier_norm).replace(/'/g,"\\\\'");
      h+='<tr><td>'+esc(r.words)+'<div class="mut" style="font-size:12.5px">'+esc(r.cadence_how||"")+(r.owner_set&&r.owner_set.length?' · yours: '+esc(r.owner_set.join(", ")):'')+'</div></td>'+
         '<td class="num" style="white-space:nowrap"><button class="ghost" onclick="poEdit(\\''+sn+'\\')">edit</button> '+(r.paused?'<button class="ghost" onclick="poSet(\\''+sn+'\\',\\'paused\\',0)">resume</button>':'<button class="ghost" onclick="poPause(\\''+sn+'\\')">pause</button>')+(r.review_on?' <button class="ghost" onclick="poSet(\\''+sn+'\\',\\'move_to\\',\\''+esc(r.review_target||"weekly")+'\\')">move to '+esc(r.review_target||"weekly")+'</button>':'')+'</td></tr>';
    });
    h+='</tbody></table></div>';
    var c=j.candidates||{};
    h+='<details style="margin-top:8px"><summary><b>Never re-order — candidates ('+(c.never||[]).length+')</b> <span class="mut">in stock, no sale in '+c.never_days+' days · tick = never proposed</span></summary><div class="tblwrap"><table><thead><tr><th>Item</th><th class="num">Stock</th><th>Last sale</th><th></th></tr></thead><tbody>'+
       (c.never||[]).map(function(x){return '<tr><td>'+esc(x.item)+'</td><td class="num">'+x.qty+'</td><td>'+esc(x.last_sale_text)+'</td><td><button class="ghost" onclick="poItem(\\''+esc(x.item).replace(/'/g,"\\\\'")+'\\',\\'never\\',true)">never re-order</button></td></tr>'}).join("")+'</tbody></table></div></details>';
    h+='<details style="margin-top:6px"><summary><b>On demand — candidates ('+(c.on_demand||[]).length+')</b> <span class="mut">at most '+c.on_demand_max_sales+' sales in '+c.on_demand_days+' days and unit value ≥ '+esc(c.on_demand_min_rs)+'</span></summary><div class="tblwrap"><table><thead><tr><th>Item</th><th class="num">Stock</th><th class="num">Sales</th><th class="num">Unit</th><th></th></tr></thead><tbody>'+
       (c.on_demand||[]).map(function(x){return '<tr><td>'+esc(x.item)+'</td><td class="num">'+x.qty+'</td><td class="num">'+x.sales+'</td><td class="num">'+esc(x.unit_rs)+'</td><td><button class="ghost" onclick="poItem(\\''+esc(x.item).replace(/'/g,"\\\\'")+'\\',\\'on_demand\\',true)">on demand</button></td></tr>'}).join("")+'</tbody></table></div></details>';
    var ir=j.item_rules||[], L=j.lists||{};
    h+='<details style="margin-top:6px"><summary><b>Your item rules ('+ir.length+')</b> <span class="mut">never · on demand · keep-in-stock · max on shelf · internal use — and the lists as the spine reads them</span></summary>'+
       '<div class="mut">internal use: '+((L.internal_use||[]).map(esc).join(", ")||"empty")+' · never re-order: '+((L.never_reorder||[]).map(esc).join(", ")||"empty")+' · on demand: '+((L.on_demand||[]).map(esc).join(", ")||"empty")+' (orthotics cycle retired)</div>'+
       '<div class="tblwrap"><table><tbody>'+ir.map(function(x){return '<tr><td>'+esc(x.item)+'</td><td>'+esc(x.rule)+(x.value!=null?' '+x.value:'')+'</td><td class="mut">'+esc(x.set_by||"")+' '+esc((x.set_at||"").slice(0,10))+'</td><td><button class="ghost" onclick="poItem(\\''+esc(x.item).replace(/'/g,"\\\\'")+'\\',\\''+esc(x.rule)+'\\',false)">remove</button></td></tr>'}).join("")+'</tbody></table></div>'+
       '<div class="row" style="margin-top:6px"><input id="poItemName" placeholder="item as Marg prints it" style="min-width:220px"> <select id="poItemRule"><option value="keep">keep-in-stock (units)</option><option value="max_shelf">max on shelf (units)</option><option value="never">never re-order</option><option value="on_demand">on demand</option><option value="internal">internal use</option></select> <input id="poItemVal" type="number" placeholder="units" style="width:90px"> <button class="ghost" onclick="poItemAdd()">add</button></div></details>';
    h+=j.rules_ok?'<div class="ok" style="margin-top:8px">✓ Rules approved — the staff screen sends medicine orders (the day\\'s proposals at 09:00).</div>'
                 :'<div style="margin-top:8px"><button onclick="poApprove()">Approve rules</button> <span class="mut">one tap: the standing approval (D626) — the paper purchase-order sheet is retired; the system\\'s record replaces it. Until then the staff screen says "Doctor sahab ke rules ka intezaar".</span></div>';
    if(j.kedar_review) h+='<div class="alert info" style="margin-top:8px">'+esc(j.kedar_review.text)+' <button class="ghost" onclick="poSet(\\'KEDAR PHARMACEUTICAL\\',\\'move_to\\',\\''+esc(j.kedar_review.target)+'\\')">Move Kedar to '+esc(j.kedar_review.target)+'</button></div>';
    if((j.holidays||[]).length) h+='<div class="mut" style="margin-top:6px">Holidays (Shavez keeps the list): '+(j.holidays||[]).map(function(x){return esc(x.day)+(x.note?' ('+esc(x.note)+')':'')}).join(", ")+'</div>';
    if((j.audit||[]).length) h+='<details style="margin-top:6px"><summary class="mut">last changes ('+(j.audit||[]).length+')</summary><div class="tblwrap"><table><tbody>'+(j.audit||[]).map(function(a){return '<tr><td class="mut">'+esc((a.at||"").slice(0,16))+'</td><td>'+esc(a.who)+'</td><td>'+esc(a.supplier_norm||"")+'</td><td>'+esc(a.field)+'</td><td class="mut">'+esc(a.old==null?"":a.old)+' → '+esc(a.new==null?"":a.new)+'</td></tr>'}).join("")+'</tbody></table></div></details>';
    o.innerHTML=h;
    var e=$("poNewN"); if(e) e.textContent=j.new_items_n;
  }).catch(function(){var o=$("poRules"); if(o) o.textContent="could not reach the server"});
}
function poPost(u,b,then){fetch(u,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b||{})}).then(srvJSON).then(function(x){var j=x.j||{}; if(!j.ok){alert(j.message||j.error||"not saved");return} (then||function(){loadPORules(); loadNeeds();})();}).catch(function(){alert("the server could not be reached")});}
function poSet(sn,field,value){poPost("/finance/porders/api/rules/set",{supplier:sn,field:field,value:value});}
function poEdit(sn){
  var r=(PO_R&&PO_R.rules||[]).filter(function(x){return x.supplier_norm===sn})[0]; if(!r) return;
  var f=prompt("Which setting for "+r.short+"?  cadence (weekly/fortnightly/monthly/custom) · order_days (MON,FRI) · blocked_days (SUN,THU) · lead_days · safety_days · cover_cap_days · single_source_extra (0/1) · min_order_p (paise) · review_on (YYYY-MM-DD) · review_target · note","cadence");
  if(!f) return; f=f.trim();
  var v=prompt("New value for "+f+" (now: "+(r[f]==null?"":r[f])+")", r[f]==null?"":String(r[f])); if(v==null) return;
  poSet(sn,f,v.trim());
}
function poPause(sn){var why=prompt("Pause orders to this supplier — the reason staff will see:"); if(why==null) return; poPost("/finance/porders/api/rules/set",{supplier:sn,field:"pause_reason",value:why},function(){poSet(sn,"paused",1);});}
function poItem(item,rule,on){if(!on&&!confirm("Remove this rule for "+item+"?")) return; poPost("/finance/porders/api/rules/item",{item:item,rule:rule,on:on});}
function poItemAdd(){var n=($("poItemName")||{}).value||"", r=($("poItemRule")||{}).value||"keep", v=($("poItemVal")||{}).value||""; if(!n.trim()){alert("the item name");return} poPost("/finance/porders/api/rules/item",{item:n.trim(),rule:r,on:true,value:(v===""?null:v)});}
function poFreeze(on){var why=on?prompt("Freeze all medicine ordering — the reason staff will see:"):null; if(on&&why==null) return; poPost("/finance/porders/api/rules/freeze",{on:on,reason:why||""});}
function poApprove(){
  if(!confirm("Approve the medicine buying rules as they stand? The staff screen will then send the day\\'s medicine orders on WhatsApp.")) return;
  fetch("/finance/porders/api/rules/approve",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"}).then(srvJSON).then(function(x){var j=x.j||{}; if(!j.ok){alert(j.message||j.error||"not recorded");return} loadPORules(); loadNeeds();}).catch(function(){alert("the server could not be reached")});
}
function loadPOOos(){
  fetch("/finance/porders/api/oos?_="+Date.now(),{cache:"no-store"}).then(srvJSON).then(function(x){
    var j=x.j||{}; var el=$("oosBar"); if(!el)return; if(!j.ok||!j.n){el.innerHTML="";return}
    el.innerHTML='<div class="alert bad">⛔ <b>Out of stock both ends — '+j.n+'</b>: '+(j.items||[]).map(function(i){return esc(i.item)+' (shelf '+i.qty+(i.cover_days!=null?', '+i.cover_days+' d':'')+' · '+esc(i.vendor_short)+' said no '+esc(i.said_no)+')'}).join(" · ")+' <span class="sub">out or thin at the pharmacy and the supplier answered Nahi mila on the last order line; clears when a purchase lands or another supplier fills it</span></div>';
  }).catch(function(){});
}
function loadPONew(){
  var m=($("poNewMonth")||{}).value||""; var o=$("poNew"); if(!o) return;
  fetch("/finance/porders/api/new-items?_="+Date.now()+(m?"&month="+encodeURIComponent(m):""),{cache:"no-store"}).then(srvJSON).then(function(x){
    var j=x.j||{}; if(!j.ok){o.textContent=j.message||j.error||"could not load";return}
    var e=$("poNewN"); if(e) e.textContent=j.n; var mi=$("poNewMonth"); if(mi&&!mi.value) mi.value=j.month;
    if(!j.n){o.innerHTML='<div class="mut">no first-ever purchase in '+esc(j.month)+'</div>';return}
    o.innerHTML='<div class="tblwrap"><table><thead><tr><th>Item</th><th>Salt</th><th>Supplier</th><th>Manufacturer</th><th class="num">MRP</th><th class="num">Purchase rate</th><th>First bill</th></tr></thead><tbody>'+
      (j.items||[]).map(function(i){return '<tr><td>'+esc(i.item)+' <span class="mut">'+esc(i.packing||"")+'</span></td><td>'+(i.salt?esc(i.salt):'<span class="mut">—</span>')+'</td><td>'+esc(i.supplier_short)+'</td><td>'+(i.manufacturer==="not in export"?'<span class="mut">not in export</span>':esc(i.manufacturer)+' <span class="mut">'+esc(i.manufacturer_lane)+'</span>')+'</td><td class="num">'+(i.mrp==="not in export"?'<span class="mut">not in export</span>':esc(i.mrp))+'</td><td class="num">'+esc(i.rate_rs)+'</td><td>'+esc(i.first_text)+' <span class="mut">'+esc(i.bill_no||"")+'</span></td></tr>'}).join("")+'</tbody></table></div><div class="mut">manufacturer from Marg\\'s item master, MRP from the salt-wise list, as the spine holds them; never guessed.</div>';
  }).catch(function(){o.textContent="could not reach the server"});
}
''', "rules renderer")
    s = rep(s, '''  loadPOSummary();   /* S403: the count on the Purchase orders fold */
''', '''  loadPOSummary();   /* S403: the count on the Purchase orders fold */
  loadPOOos();       /* S410: the red bar at the top, only when N > 0 */
''', "loadNeeds hooks")
    s = rep(s, '''      var act=l.neft_event?' <button onclick="event.stopPropagation();neftEvent('+parseInt(l.neft_event,10)+',\\'ok\\')">OK</button> <button class="ghost" onclick="event.stopPropagation();neftEvent('+parseInt(l.neft_event,10)+',\\'reject\\')">Not this</button>':'';   /* S405 */
''', '''      var act=l.neft_event?' <button onclick="event.stopPropagation();neftEvent('+parseInt(l.neft_event,10)+',\\'ok\\')">OK</button> <button class="ghost" onclick="event.stopPropagation();neftEvent('+parseInt(l.neft_event,10)+',\\'reject\\')">Not this</button>':'';   /* S405 */
      if(l.review_supplier) act+=' <button onclick="event.stopPropagation();poSet(\\''+esc(l.review_supplier).replace(/'/g,"\\\\'")+'\\',\\'move_to\\',\\''+esc(l.review_target||"weekly")+'\\')">Move Kedar to '+esc(l.review_target||"weekly")+'</button>';   /* S410 */
''', "needs-you review button")
    return s


# ---------------------------------------------------------------- darpan_kal.py / .html
def build_kal(s):
    s = rep(s, '''def _ortho_short_safe(con):
    """S403 (D618): 'Orthotic kam hai -- N' for Darpan's card, read from porders in-process; never breaks the page."""
''', '''def _orders_today_safe(con):
    """S410 (D626): 'Aaj ke order -- N (M bheja)' for Darpan's card, read from order_rules in-process; never breaks the page."""
    try:
        import order_rules                                   # noqa: PLC0415
        return order_rules.day_summary(con)
    except Exception as e:                                   # noqa: BLE001
        return dict(ok=False, n=0, sent=0, unsent=0, text="", error=str(e)[:80])


def _ortho_short_safe(con):
    """S403 (D618): 'Orthotic kam hai -- N' for Darpan's card, read from porders in-process; never breaks the page."""
''', "kal helper")
    s = rep(s, '''                ortho_short=_ortho_short_safe(con))            # S403 (D618)
''', '''                ortho_short=_ortho_short_safe(con),            # S403 (D618)
                orders_today=_orders_today_safe(con))          # S410 (D626)
''', "kal payload")
    return s


def build_kal_html(s):
    s = rep(s, ''' h+=orthoShortSec(j.ortho_short);   /* S403 (D618): Orthotic kam hai -- N */
''', ''' h+=orthoShortSec(j.ortho_short);   /* S403 (D618): Orthotic kam hai -- N */
 h+=ordersTodaySec(j.orders_today); /* S410 (D626): Aaj ke order -- N (M bheja) */
''', "kal render")
    s = rep(s, '''/* S403 (D618): 'Orthotic kam hai -- N' -- collapsed; the list; a button that opens the Purchase orders screen */
''', '''/* S410 (D626): 'Aaj ke order -- N (M bheja)' -- the count line; opens the Purchase orders screen */
function ordersTodaySec(o){
 if(!o||!o.ok||!o.n) return "";
 return sec('<div class="row"><span class="k">Aaj ke order — <b>'+o.n+'</b> ('+o.sent+' bheja'+(o.unsent?', <span class="amber">'+o.unsent+' baaki</span>':'')+')</span></div>'+
  (o.text?'<div class="muted">'+esc(o.text)+'</div>':'')+(o.frozen?'<div class="bad">Medicine ordering band hai</div>':'')+
  '<a class="btn primary" href="'+esc(o.url||"/finance/porders")+'">Purchase orders खोलें ↗</a>');
}
/* S403 (D618): 'Orthotic kam hai -- N' -- collapsed; the list; a button that opens the Purchase orders screen */
''', "kal section")
    return s


def main():
    args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
    fin, out = args.get("--finance"), args.get("--out")
    if not (fin and out):
        sys.exit(__doc__)
    os.makedirs(out, exist_ok=True)
    built = {
        "porders.py": build_porders(load(os.path.join(fin, "porders.py"), "porders.py")),
        "porders.html": build_porders_html(load(os.path.join(fin, "porders.html"), "porders.html")),
        "sanjeevni_approvals.py": build_approvals(load(os.path.join(fin, "sanjeevni_approvals.py"), "sanjeevni_approvals.py")),
        "finance_approvals.html": build_approvals_html(load(os.path.join(fin, "finance_ui", "finance_approvals.html"), "finance_approvals.html")),
        "darpan_kal.py": build_kal(load(os.path.join(fin, "darpan_kal.py"), "darpan_kal.py")),
        "darpan_kal.html": build_kal_html(load(os.path.join(fin, "darpan_kal.html"), "darpan_kal.html")),
    }
    for name, text in built.items():
        raw = text.encode("utf-8")
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(raw)
        print("built %s  %s" % (md5(raw), name))


if __name__ == "__main__":
    main()
