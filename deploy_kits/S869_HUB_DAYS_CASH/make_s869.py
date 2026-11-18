"""make_s869.py <code dir holding the FROM files (finance/)> <out dir> -- kit S869_HUB_DAYS_CASH: the Hub's Days and Cash (D1005).
   finance_ui/finance_approvals.html  nine anchored patches (the day panel, the Days rows + band, the Cash card, the Returns card's decide hook, the S869 script)
   day_resync.py                      five anchored patches (pass 1 on approved days too, F-1459)
   sanjeevni_cash.py, sanjeevni_day.py: WHOLE files from the kit (read whole this session; their FROM pins checked here)
   hub_cash.py                        NEW (taken from the kit by the installer)
Every FROM file is checked against its pin first; every anchor must match exactly once."""
import hashlib, os, sys
SRC, OUT = sys.argv[1], sys.argv[2]
KD = os.path.dirname(os.path.abspath(__file__))
FROM = {"finance_ui/finance_approvals.html": "17f13acc3b9f18ef2be71eefcc811c07", "day_resync.py": "00b45a150df15123106fbcc641f913ab",
        "sanjeevni_cash.py": "8e58691bac16fceb00602e7f8eabdaf8", "sanjeevni_day.py": "22a38006a4e3be59b47ea091ea1f971f"}


def patch(text, pairs):
    for old, new in pairs:
        assert text.count(old) == 1, "anchor not found once: %r" % old[:80]
        text = text.replace(old, new)
    return text


# ----------------------------------------------------------------------------------------------------------------------- the Hub page
H1_OLD = '''    function billList(list){
      if(!list||!list.length)return '<span class="mut">none</span>';
      return list.map(function(b){
        var its=(b.items||[]).map(function(i){return '<tr><td>'+esc(i.item)+'</td><td class="mut">'+esc(i.pack||"")+'</td><td class="mut">'+esc(i.qty||"")+'</td><td class="num">₹'+esc(i.amount)+'</td><td class="mut">'+esc(i.batch||"")+' '+esc(i.expiry||"")+'</td></tr>'}).join("");
        return '<div style="border-bottom:1px dotted #eee;padding:2px 0">'+
          '<div onclick="var n=this.nextElementSibling;if(n)n.style.display=n.style.display===\\'none\\'?\\'\\':\\'none\\'" style="cursor:pointer;display:flex;gap:8px">'+
          '<span style="flex:1">'+esc(b.bill)+' <span class="mut">'+esc(b.name||"no patient name")+'</span>'+(its?' <span class="tog">▸</span>':'')+'</span>'+
          '<span class="num">₹'+esc(b.amount)+'</span></div>'+
          (its?'<div style="display:none"><table>'+its+'</table></div>':'')+'</div>';
      }).join("");
    }
    var h='<div class="sec" style="max-width:640px">';
    h+=line("","Sale (Marg)",v.sale.total,v.sale.bills+" bill(s)",billList(v.sale.list));
    h+=line("−","Sale returns",v.returns.total,v.returns.count?v.returns.count+" credit note(s)":"none",v.returns.count?billList(v.returns.list):null);
'''
H1_NEW = '''    /* S869 (D1005): every bill opens to its medicines WITH each line's value; a without-cash bill names who it was typed to
       (exactly as Darpan typed it in Marg); a sale return names the patient, the ID and the mobile, and carries the Returns
       card's own verdict with the same Approve / Reject (one check, one action, two places). */
    function itemTable(its){
      if(!its||!its.length) return '';
      return '<table><thead><tr><th>medicine</th><th>pack</th><th>qty</th><th class="num">rate</th><th class="num">value</th><th>batch · expiry</th></tr></thead><tbody>'+
        its.map(function(i){return '<tr><td>'+esc(i.item)+'</td><td class="mut">'+esc(i.pack||"")+'</td><td class="mut">'+esc(i.qty||"")+'</td><td class="num mut">₹'+esc(i.amount)+'</td><td class="num">'+(i.value!=null?'₹'+esc(i.value):'—')+'</td><td class="mut">'+esc(i.batch||"")+' '+esc(i.expiry||"")+'</td></tr>'}).join("")+'</tbody></table>';
    }
    function billList(list){
      if(!list||!list.length)return '<span class="mut">none</span>';
      return list.map(function(b){
        var its=itemTable(b.items);
        var who=b.typed?('<b>'+esc(b.typed)+'</b> <span class="mut">as typed in Marg</span>'+((b.name&&b.name!==b.typed)?' <span class="mut">· '+esc(b.name)+'</span>':'')):('<span class="mut">'+esc(b.name||"no patient name")+'</span>');
        return '<div style="border-bottom:1px dotted #eee;padding:2px 0">'+
          '<div onclick="var n=this.nextElementSibling;if(n)n.style.display=n.style.display===\\'none\\'?\\'\\':\\'none\\'" style="cursor:pointer;display:flex;gap:8px">'+
          '<span style="flex:1">'+esc(b.bill)+' '+who+(its?' <span class="tog">▸</span>':'')+'</span>'+
          '<span class="num">₹'+esc(b.amount)+'</span></div>'+
          (its?'<div style="display:none">'+its+'</div>':'')+'</div>';
      }).join("");
    }
    function retList(list){
      if(!list||!list.length)return '<span class="mut">none</span>';
      var ask=false;
      var out=list.map(function(b){
        var its=itemTable(b.items);
        var who=[b.patient?('<b>'+esc(b.patient)+'</b>'):'<span class="mut">no patient name</span>', b.clinic_id?('#'+esc(b.clinic_id)):'', b.mobile?esc(b.mobile):''].filter(Boolean).join(' · ');
        var r=(typeof rhFind==="function")?rhFind(b.key):null, verdict;
        if(r){
          verdict='<span class="badge '+(r.tone==="ok"?"b-ok":(r.tone==="bad"?"b-bad":(r.tone==="mut"?"":"b-warn")))+'">'+rhEsc(r.word||r.verdict||"")+'</span>';
          if(r.pending_ok&&RH&&RH.owner) verdict+=' <button data-k="'+rhEsc(r.key)+'" onclick="event.stopPropagation();rhDecide(rhAt(this,\\'data-k\\'),\\'approved\\',this)">Approve</button> '+
            '<button class="ghost" data-k="'+rhEsc(r.key)+'" onclick="event.stopPropagation();rhDecide(rhAt(this,\\'data-k\\'),\\'rejected\\',this)">Reject</button>';
        } else if(RH===null){ ask=true; verdict='<span class="mut">the Returns card is loading…</span>'; }
        else verdict='<span class="mut">not on the Returns card</span>';
        return '<div style="border-bottom:1px dotted #eee;padding:2px 0">'+
          '<div onclick="var n=this.nextElementSibling;if(n)n.style.display=n.style.display===\\'none\\'?\\'\\':\\'none\\'" style="cursor:pointer;display:flex;gap:8px;flex-wrap:wrap">'+
          '<span style="flex:1">'+esc(b.bill)+' '+who+(its?' <span class="tog">▸</span>':'')+'</span><span>'+verdict+'</span>'+
          '<span class="num">₹'+esc(b.amount)+'</span></div>'+
          (its?'<div style="display:none">'+its+'</div>':'')+'</div>';
      }).join("");
      if(ask&&!window.S869_CN_ASKED){ window.S869_CN_ASKED=1; if(typeof loadCN==="function") loadCN(); setTimeout(function(){ if($(elId)) dayDetail(d,elId); },3000); }
      return out;
    }
    var h='<div class="sec" style="max-width:640px">';
    h+=line("","Sale (Marg)",v.sale.total,v.sale.bills+" bill(s)",billList(v.sale.list));
    h+=line("−","Sale returns",v.returns.total,v.returns.count?v.returns.count+" credit note(s)":"none",v.returns.count?retList(v.returns.list):null);
'''
H2_OLD = '''    if(v.without_cash.list.length) h+=line("−","Without cash",v.without_cash.total,v.without_cash.list.map(function(x){return x.head}).join(", "),
            v.without_cash.list.map(function(x){return '<div style="display:flex;gap:8px"><span style="flex:1">'+esc(x.bill)+' '+esc(x.head)+(x.note?' <span class="mut">'+esc(x.note)+'</span>':'')+'</span><span class="num">₹'+esc(x.amount)+'</span></div>'}).join(""));
    h+=line("=","Cash received",v.cash_received,"",null,true);
'''
H2_NEW = '''    if(v.without_cash.list.length) h+=line("−","Without cash",v.without_cash.total,v.without_cash.list.map(function(x){return x.head}).join(", "),
            v.without_cash.list.map(function(x){ var its=itemTable(x.items);
              return '<div style="border-bottom:1px dotted #eee;padding:2px 0"><div onclick="var n=this.nextElementSibling;if(n)n.style.display=n.style.display===\\'none\\'?\\'\\':\\'none\\'" style="cursor:pointer;display:flex;gap:8px"><span style="flex:1">'+esc(x.bill)+' '+esc(x.head)+(x.typed?' · <b>'+esc(x.typed)+'</b> <span class="mut">as typed in Marg</span>':'')+(x.note?' <span class="mut">'+esc(x.note)+'</span>':'')+(its?' <span class="tog">▸</span>':'')+'</span><span class="num">₹'+esc(x.amount)+'</span></div>'+(its?'<div style="display:none">'+its+'</div>':'')+'</div>'}).join(""));
    h+=line("=","Cash received",v.cash_received,"",null,true);
    if(v.other_account) h+=line("−","Paid into another account",v.other_account,"never reached the drawer (your entry)",null);
'''
H3_OLD = '''    if(v.went) h+='<div style="margin:6px 0"><b>Where the cash went:</b> '+esc(v.went)+'</div>';
'''
H3_NEW = '''    if(v.went) h+='<div style="margin:6px 0"><b>Where the cash went:</b> '+esc(v.went)+'</div>';
    h+=s869Entries(v,d,elId);                                                      /* S869: your entries on this day, + Add an entry */
'''
H4_OLD = '''      else if(d.log) st='<span class="pill ok">'+esc(d.log.amount)+' to '+esc(d.log.to)+(d.log.received?'':' · not yet received')+'</span>';
'''
H4_NEW = '''      else if(d.log) st='<span class="pill ok">'+esc(d.log.amount)+' to '+esc(d.log.to)+(d.log.received?'':' · not yet received')+'</span>'+
         ((!d.log.received&&d.log.to==="Dr Bhawna")?' <button class="ghost" onclick="event.stopPropagation();s869Received(\\''+d.date+'\\')">Received ✓ for Dr Bhawna</button>':'');   /* S869 */
'''
H5_OLD = '''  var MON=["January","February","March","April","May","June","July","August","September","October","November","December"];
  var h="";
  order.forEach(function(ym,ix){
    var rows=months[ym]; var pend=rows.filter(function(d){return !d.approved}).length;
'''
H5_NEW = '''  var MON=["January","February","March","April","May","June","July","August","September","October","November","December"];
  var h=s869Band();                                                                   /* S869: Dr Bhawna's handovers not marked received */
  order.forEach(function(ym,ix){
    var rows=months[ym]; var pend=rows.filter(function(d){return !d.approved}).length;
'''
H6_OLD = '''    try{ $("cashPos").innerHTML=s761CashHTML(j,BX,gapTxt,gapCls); return; }catch(e761){ /* S761: the S210 drawing below stands */ }
'''
H6_NEW = '''    s869Why();                                                                        /* S869: why the drawer reads what it reads */
    try{ $("cashPos").innerHTML=s761CashHTML(j,BX,gapTxt,gapCls); return; }catch(e761){ /* S761: the S210 drawing below stands */ }
'''
H7_OLD = '''  <div id="cashPos" class="held"><span class="mut">loading…</span></div>
'''
H7_NEW = '''  <div id="cashPos" class="held"><span class="mut">loading…</span></div>
  <div id="drawerWhy"></div><!-- S869: why Darpan's drawer reads what it reads -->
'''
H8_OLD = '''     loadCN(); if(typeof loadNeeds==="function") loadNeeds(); })
   .catch(function(){ btn.disabled=false; alert("nothing was saved — the server could not be reached"); });
'''
H8_NEW = '''     loadCN(); if(typeof loadNeeds==="function") loadNeeds(); if(typeof s869AfterDecide==="function") setTimeout(s869AfterDecide,2500); })
   .catch(function(){ btn.disabled=false; alert("nothing was saved — the server could not be reached"); });
'''
H9_OLD = '''/* ---- Days: one line per day, grouped by month; tap = the day panel (S365/S367) ---- */
'''
H9_NEW = '''/* ==== KIT_S869_HUB_DAYS_CASH (18-Nov-2026, Sanjeevni session 482; D1005, the owner's OK on mock-up v3 at 11:59) ====================
   Dr Bhawna does not use the app: the owner stamps her handovers received (one row, or all at once -- hub_cash's door).
   His own entries on a day (money into another account; cash taken out on a doctor's word) are added and removed here,
   owner only. The Cash card says why the drawer reads what it reads: each short day, its cause, Add an entry / Accept. */
function s869Post(u,b){ return fetch(u,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b||{})}).then(srvJSON).then(function(x){ var j=x.j||{}; if(!j.ok) throw new Error(j.message||j.error||("HTTP "+x.s)); return j; }); }
function s869Refresh(){ if(typeof loadDays==="function") loadDays(); if(typeof loadCashPos==="function") loadCashPos(); if(typeof loadNeeds==="function") loadNeeds(); }
function s869AfterDecide(){ Object.keys(dayOpen||{}).forEach(function(d){ if(dayOpen[d]&&$("dd-"+d)) dayDetail(d,"dd-"+d); }); }
function s869Received(d){
  s869Post("/finance/darpan/kal/api/received",{date:d}).then(function(){ s869Refresh(); }).catch(function(e){ alert("not marked — "+e.message); });
}
function s869ReceivedAll(n){
  if(!window.confirm("Mark all "+n+" handover(s) to Dr Bhawna as received?")) return;
  s869Post("/finance/sanjeevni/api/received-all",{party:"dr_bhawna"}).then(function(j){ s869Refresh(); alert((j.n||0)+" handover(s) marked received for Dr Bhawna"); }).catch(function(e){ alert("not marked — "+e.message); });
}
function s869Band(){
  if(!DAYS||!DAYS.days) return "";
  var U=DAYS.days.filter(function(d){ return d.log&&!d.log.received&&d.log.to==="Dr Bhawna"; });
  if(!U.length) return "";
  var sum=0; U.forEach(function(d){ sum+=parseInt(String(d.log.amount||"0").replace(/,/g,""),10)||0; });
  var first=U[0].date<U[U.length-1].date?U[0]:U[U.length-1], last=U[0].date<U[U.length-1].date?U[U.length-1]:U[0];
  return '<div class="cb-line warn" style="margin-bottom:8px">'+U.length+' handover'+(U.length===1?'':'s')+' to Dr Bhawna ('+esc(first.day||first.date)+' to '+esc(last.day||last.date)+') '+(U.length===1?'is':'are')+' not marked received · ₹'+sum.toLocaleString("en-IN")+
    ' <button onclick="s869ReceivedAll('+U.length+')">Mark all '+U.length+' received</button> <span class="mut">· she does not use the app; your tap stands for her</span></div>';
}
function s869Entries(v,d,elId){
  var E=v.entries||[], h='<div style="margin:6px 0">';
  if(E.length) h+='<b>Your entries:</b> '+E.map(function(e){ return esc(e.words)+' <a href="#" onclick="s869Remove('+e.id+',\\''+d+'\\',\\''+elId+'\\');return false" class="mut">remove</a>'; }).join(' · ');
  h+=(E.length?' · ':'')+'<a href="#" onclick="s869Toggle(\\''+d+'\\');return false">+ Add an entry</a>'+
    '<div class="logbox" id="s869add-'+d+'" style="display:none"><select id="s869k-'+d+'" onchange="s869Kind(\\''+d+'\\')"><option value="other_account">Paid into another account</option><option value="taken_out">Cash taken out</option></select>'+
    ' ₹<input type="number" id="s869a-'+d+'" style="width:90px" placeholder="amount">'+
    '<span id="s869p1-'+d+'"> account <input id="s869acc-'+d+'" placeholder="e.g. NK Pathology UPI" style="width:170px"></span>'+
    '<span id="s869p2-'+d+'" style="display:none"> with <select id="s869w-'+d+'"><option value="dr_bhawna">Dr Bhawna</option><option value="dr_manoj">me</option><option value="pool">the pool</option></select>'+
    ' for <select id="s869f-'+d+'"><option value="personal">personal</option><option value="clinic_expense">clinic expense</option><option value="other">other</option></select></span>'+
    ' note <input id="s869n-'+d+'" placeholder="two words" style="width:200px"> <button onclick="s869Save(\\''+d+'\\')">Save</button> <button class="ghost" onclick="s869Toggle(\\''+d+'\\')">cancel</button>'+
    '<span class="mut" style="width:100%">Paid into another account: the money never reached the drawer. Cash taken out: it left the drawer on a doctor\\'s word and counts with the doctors. Only you see these.</span></div></div>';
  return h;
}
function s869Toggle(d){ var b=$("s869add-"+d); if(b) b.style.display=b.style.display==="none"?"":"none"; }
function s869Kind(d){ var k=$("s869k-"+d).value; $("s869p1-"+d).style.display=k==="other_account"?"":"none"; $("s869p2-"+d).style.display=k==="taken_out"?"":"none"; }
function s869Save(d){
  var k=$("s869k-"+d).value, a=parseFloat($("s869a-"+d).value);
  if(isNaN(a)||a<=0){ alert("type the amount"); return; }
  var b={date:d,kind:k,amount_p:Math.round(a*100),note:$("s869n-"+d).value};
  if(k==="other_account") b.party=$("s869acc-"+d).value; else { b.party=$("s869w-"+d).value; b.purpose=$("s869f-"+d).value; }
  s869Post("/finance/sanjeevni/api/day-entry",b).then(function(){ s869Refresh(); if($("dd-"+d)) dayDetail(d,"dd-"+d); }).catch(function(e){ alert("not saved — "+e.message); });
}
function s869Remove(id,d,elId){
  if(!window.confirm("Remove this entry?")) return;
  s869Post("/finance/sanjeevni/api/day-entry/remove",{id:id}).then(function(){ s869Refresh(); if($(elId)) dayDetail(d,elId); }).catch(function(e){ alert("not removed — "+e.message); });
}
function s869Accept(d){
  if(!window.confirm("Accept the short of "+d+" -- written off, out of the drawer?")) return;
  s869Post("/finance/darpan/kal/api/owner/decide",{date:d,decision:"accept",note:"accepted on the Hub's Cash card"}).then(function(){ s869Refresh(); }).catch(function(e){ alert("not accepted — "+e.message); });
}
function s869OpenDay(d){ dayOpen[d]=true; if(typeof renderDays==="function") renderDays(); if(typeof goCard==="function") goCard("daysCard"); setTimeout(function(){ var b=$("s869add-"+d); if(b) b.style.display=""; },1500); }
function s869Why(){
  var el=$("drawerWhy"); if(!el) return;
  fetch("/finance/sanjeevni/api/drawer-why?_="+Date.now(),{cache:"no-store"}).then(srvJSON).then(function(x){
    var j=x.j||{}; if(!j.ok){ el.innerHTML=""; return; }
    var ny=(j.not_yet||[]).length?(' · '+j.not_yet.length+' day'+(j.not_yet.length===1?'':'s')+' not yet handed over ₹'+esc(j.waiting)+' ('+j.not_yet.map(function(x){return esc(x.day)}).join(', ')+')'):'';
    var restTxt=j.rest_is_roundoffs?(' · the rest ₹'+esc(j.rest)+' is round-offs'):(' · the rest ₹'+esc(j.rest)+' is not explained by these');
    if(!j.days||!j.days.length){ el.innerHTML='<div class="mut" style="font-size:12px;margin-top:6px">Darpan\\'s drawer ₹'+esc(j.drawer)+ny+(j.rest_is_roundoffs?' — nothing beyond round-offs is unexplained ✓':restTxt)+'</div>'; return; }
    var h='<details class="fold" open style="margin-top:8px"><summary><b>Why the drawer reads ₹'+esc(j.drawer)+'</b> <span class="mut">· '+j.days.length+' day'+(j.days.length===1?'':'s')+' handed over short by ₹'+esc(j.short_total)+ny+restTxt+'</span></summary>'+
      '<div class="tblwrap" style="margin-top:6px"><table><thead><tr><th>day</th><th class="num">cash</th><th class="num">handed</th><th class="num">short</th><th>why</th><th class="act"></th></tr></thead><tbody>';
    j.days.forEach(function(r){
      h+='<tr><td><b>'+esc(r.day)+'</b></td><td class="num">₹'+esc(r.cash)+'</td><td class="num">₹'+esc(r.left)+'</td><td class="num"><b>₹'+esc(r.short)+'</b></td><td>'+(r.cause||[]).map(esc).join('<br>')+'</td>'+
        '<td class="act" style="white-space:nowrap"><button class="ghost" onclick="s869OpenDay(\\''+r.date+'\\')">Add an entry</button>'+(r.actions.indexOf("accept")>=0?' <button class="ghost" onclick="s869Accept(\\''+r.date+'\\')">Accept (write off)</button>':'')+'</td></tr>';
    });
    el.innerHTML=h+'</tbody></table></div></details>';
  }).catch(function(){ el.innerHTML=""; });
}
/* ==== end KIT_S869 ==== */

/* ---- Days: one line per day, grouped by month; tap = the day panel (S365/S367) ---- */
'''

# ----------------------------------------------------------------------------------------------------------------------- day_resync.py
R_PAIRS = [
('''"""day_resync.py -- S399_DAY_TRUTH_5 (S355 -> S356 -> S357 -> S367 -> this): an unapproved pharmacy day follows
Marg's latest bills and the bank, and carries its home / procedure medicine bills and their credit notes.
''', '''"""day_resync.py -- S399_DAY_TRUTH_5 (S355 -> S356 -> S357 -> S367 -> S672 -> S869): an unapproved pharmacy day follows
Marg's latest bills and the bank, and carries its home / procedure medicine bills and their credit notes.

S869 (F-1459, the owner 18-Nov-2026, D1005: "make the necessary changes one time to correct the records")
    PASS 1 (the bank's UPI) ran only on UNAPPROVED days. 9-Oct and 14-Oct were approved before the bank's statement
    came, so they stayed UPI 0 and the Hub's cash read Rs 10,163 / 11,985 high, while Darpan's Kal ka hisaab (which
    reads the bank directly) said 13,258 / 21,063 -- the two pages disagreed for five weeks. Pass 1 now runs on
    EVERY autofiled, never-person-corrected pharmacy day, approved or not: UPI is the bank's, cash = net - UPI, one
    audit_log row 'resync_upi' as before (the after_json names the day's status). Pass 0 (Marg) and pass 2 are
    unchanged: an approved day that differs from Marg is still only named.
'''),
('''def candidates(con, since):
    """Unapproved, autofiled, never corrected by a person, statement in."""
    rows = con.execute(
        "SELECT e.id, e.business_date, e.status, e.source "
        "FROM day_entry e WHERE e.unit=? AND e.status IN ('submitted','draft') "
        "AND e.source='app' AND e.business_date>=? "''', '''def candidates(con, since, any_status=False):
    """Unapproved (S869: approved too when any_status -- never a locked day), autofiled, never corrected by a person."""
    rows = con.execute(
        "SELECT e.id, e.business_date, e.status, e.source "
        "FROM day_entry e WHERE e.unit=? AND (e.status IN ('submitted','draft') OR (? AND e.status='approved')) "
        "AND e.source='app' AND e.business_date>=? "'''),
('''        "ORDER BY e.business_date", (UNIT, since)).fetchall()
    return rows
''', '''        "ORDER BY e.business_date", (UNIT, 1 if any_status else 0, since)).fetchall()
    return rows
'''),
('''    before = dict(date=iso, cash_p=cash_p, upi_p=upi_p, net_p=net_p)
    after = dict(date=iso, cash_p=new_cash, upi_p=bank_p, net_p=net_p,
                 bank_txns=n_txn, rule="D354 marg+bank, re-read from the statement", kit=KIT)''', '''    before = dict(date=iso, cash_p=cash_p, upi_p=upi_p, net_p=net_p, status=e["status"])
    after = dict(date=iso, cash_p=new_cash, upi_p=bank_p, net_p=net_p, status=e["status"],
                 bank_txns=n_txn, rule="D354 marg+bank, re-read from the statement" +
                 ("; S869: the statement came after the day was approved (F-1459)" if e["status"] not in ("submitted", "draft") else ""),
                 kit=KIT)'''),
('''    # ---- pass 1: UPI from the bank
    rows = candidates(con, a.since)
    counts = {}
    print("%s %s -- UPI: %d unapproved autofiled day(s) since %s in %s" % (KIT, mode, len(rows), a.since, a.db))''', '''    # ---- pass 1: UPI from the bank (S869: approved days too -- the bank's statement often lands after the approval)
    rows = candidates(con, a.since, any_status=True)
    counts = {}
    print("%s %s -- UPI: %d autofiled day(s) since %s in %s (S869: approved days included)" % (KIT, mode, len(rows), a.since, a.db))'''),
]


def main():
    os.makedirs(os.path.join(OUT, "finance_ui"), exist_ok=True)
    for f in FROM:
        b = open(os.path.join(SRC, f), "rb").read()
        assert hashlib.md5(b).hexdigest() == FROM[f], "%s is not at its FROM pin (%s)" % (f, hashlib.md5(b).hexdigest())
        if f == "finance_ui/finance_approvals.html":
            t = patch(b.decode("utf-8"), [(H1_OLD, H1_NEW), (H2_OLD, H2_NEW), (H3_OLD, H3_NEW), (H4_OLD, H4_NEW), (H5_OLD, H5_NEW),
                                          (H6_OLD, H6_NEW), (H7_OLD, H7_NEW), (H8_OLD, H8_NEW), (H9_OLD, H9_NEW)]).encode("utf-8")
        elif f == "day_resync.py":
            t = patch(b.decode("utf-8"), R_PAIRS).encode("utf-8")
        else:
            t = open(os.path.join(KD, f), "rb").read()                      # the whole file from the kit
        open(os.path.join(OUT, f), "wb").write(t)
        print(f, hashlib.md5(t).hexdigest())


if __name__ == "__main__":
    main()
