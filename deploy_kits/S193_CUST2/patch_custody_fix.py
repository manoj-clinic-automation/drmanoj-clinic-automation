#!/usr/bin/env python3
# S193_CUST2 - fix: custody balances arrive as comma-formatted STRINGS
# ("1,56,235.00"), so numeric compares were NaN and every hand vanished
# while the total sat at 0. Parse to number for math + Indian-group the
# total. In-place patch, fail-loud, idempotent.
import sys
TARGET="/root/finance/finance_ui/finance_approvals.html"
OLD=r"""function loadCustody(){
  fetch("/finance/api/custody").then(function(r){return r.json()}).then(function(j){
    if(!j.ok){$("custHeld").textContent="could not load";return}
    var held=j.held||[], events=j.events||[];
    var NAMES={dr_bhawna:"Dr Bhawna",drawer:"Drawer (Darpan)",counter:"Counter (Vinay)",dr_manoj:"Dr Manoj",bank:"In transit to bank"};
    var holders=held.filter(function(x){return x.held>0}).sort(function(a,b){return b.held-a.held});
    var passed=held.filter(function(x){return x.held<=0}).sort(function(a,b){return a.held-b.held});
    var total=holders.reduce(function(a,x){return a+(x.held||0)},0);
    function evFor(p){return events.filter(function(e){return e.frm===p||e.to===p})}
    function detailTable(p){
      var evs=evFor(p);
      if(!evs.length)return '<div class="mut" style="padding:6px 2px">no recorded movements</div>';
      return '<div class="tblwrap" style="margin:4px 0 6px"><table><thead><tr><th>Date</th><th>From</th><th>To</th><th class="num">Amount</th><th>Note</th></tr></thead><tbody>'+
        evs.map(function(e){var inTo=(e.to===p);
          return '<tr><td>'+esc(e.date)+'</td><td>'+esc(NAMES[e.frm]||e.frm)+'</td><td>'+esc(NAMES[e.to]||e.to)+
          '</td><td class="num">'+(inTo?'+ ':'− ')+fmt(e.amount)+'</td><td class="mut">'+esc((e.note||"").slice(0,90))+'</td></tr>'}).join("")+
        '</tbody></table></div>';
    }
    function personRow(x){
      var name=esc(NAMES[x.party]||x.party);
      var right=x.held>0
        ? '<span class="val" style="font-size:18px">'+fmt(x.held)+'</span>'
        : '<span class="mut" style="font-size:14px">holds nothing now'+(x.held<0?' · passed on '+fmt(-x.held):'')+'</span>';
      return '<div class="custPerson" style="border-top:1px solid #eee">'+
        '<div onclick="tog(this)" style="display:flex;justify-content:space-between;align-items:center;cursor:pointer;padding:9px 2px">'+
          '<span>'+name+' <span class="mut" style="font-size:12px">› movements</span></span>'+right+'</div>'+
        '<div style="display:none;padding-left:12px">'+detailTable(x.party)+'</div></div>';
    }
    var all=holders.concat(passed);
    $("custHeld").innerHTML=held.length?(
      '<div class="stat" style="margin-bottom:4px"><span class="lbl">Held now · total (cash in hands right now)</span><span class="val">'+fmt(total)+'</span></div>'+
      all.map(personRow).join("")+
      '<div class="mut" style="font-size:12px;margin-top:6px">Tap a name to see every note that passed through that hand.</div>'
    ):'<span class="mut">no custody balances recorded yet</span>';
    var ev=(j.events||[]).slice(0,8);
    $("custEv").innerHTML=ev.length?('<div class="mut" style="margin:10px 0 2px">Recent movements (all hands)</div><div class="tblwrap"><table><thead><tr><th>Date</th><th>From</th><th>To</th><th class="num">Amount</th><th>Note</th></tr></thead><tbody>'+
      ev.map(function(e){return '<tr><td>'+esc(e.date)+'</td><td>'+esc(NAMES[e.frm]||e.frm)+'</td><td>'+esc(NAMES[e.to]||e.to)+'</td><td class="num">'+fmt(e.amount)+
        (e.month_end?' <span class="badge b-warn">'+esc(e.month_end)+'</span>':'')+'</td><td class="mut">'+esc(e.note||"")+'</td></tr>'}).join("")+
      '</tbody></table></div>'):"";
  }).catch(function(){$("custHeld").textContent="could not load"});
}"""
NEW=r"""function loadCustody(){
  fetch("/finance/api/custody").then(function(r){return r.json()}).then(function(j){
    if(!j.ok){$("custHeld").textContent="could not load";return}
    var held=j.held||[], events=j.events||[];
    var NAMES={dr_bhawna:"Dr Bhawna",drawer:"Drawer (Darpan)",counter:"Counter (Vinay)",dr_manoj:"Dr Manoj",bank:"In transit to bank"};
    function num(v){return parseFloat(String(v==null?0:v).replace(/,/g,""))||0}
    function inr(n){n=Math.round(n);var neg=n<0,s=String(Math.abs(n)),last3=s.slice(-3),rest=s.slice(0,-3);var g=rest?rest.replace(/\B(?=(\d\d)+(?!\d))/g,",")+","+last3:last3;return (neg?"-":"")+g}
    var holders=held.filter(function(x){return num(x.held)>0}).sort(function(a,b){return num(b.held)-num(a.held)});
    var passed=held.filter(function(x){return num(x.held)<=0}).sort(function(a,b){return num(a.held)-num(b.held)});
    var total=holders.reduce(function(a,x){return a+num(x.held)},0);
    function evFor(p){return events.filter(function(e){return e.frm===p||e.to===p})}
    function detailTable(p){
      var evs=evFor(p);
      if(!evs.length)return '<div class="mut" style="padding:6px 2px">no recorded movements</div>';
      return '<div class="tblwrap" style="margin:4px 0 6px"><table><thead><tr><th>Date</th><th>From</th><th>To</th><th class="num">Amount</th><th>Note</th></tr></thead><tbody>'+
        evs.map(function(e){var inTo=(e.to===p);
          return '<tr><td>'+esc(e.date)+'</td><td>'+esc(NAMES[e.frm]||e.frm)+'</td><td>'+esc(NAMES[e.to]||e.to)+
          '</td><td class="num">'+(inTo?'+ ':'− ')+fmt(e.amount)+'</td><td class="mut">'+esc((e.note||"").slice(0,90))+'</td></tr>'}).join("")+
        '</tbody></table></div>';
    }
    function personRow(x){
      var name=esc(NAMES[x.party]||x.party), v=num(x.held);
      var right=v>0
        ? '<span class="val" style="font-size:18px">'+fmt(x.held)+'</span>'
        : '<span class="mut" style="font-size:14px">holds nothing now'+(v<0?' · passed on '+inr(-v):'')+'</span>';
      return '<div class="custPerson" style="border-top:1px solid #eee">'+
        '<div onclick="tog(this)" style="display:flex;justify-content:space-between;align-items:center;cursor:pointer;padding:9px 2px">'+
          '<span>'+name+' <span class="mut" style="font-size:12px">› movements</span></span>'+right+'</div>'+
        '<div style="display:none;padding-left:12px">'+detailTable(x.party)+'</div></div>';
    }
    var all=holders.concat(passed);
    $("custHeld").innerHTML=held.length?(
      '<div class="stat" style="margin-bottom:4px"><span class="lbl">Held now · total (cash in hands right now)</span><span class="val">'+inr(total)+'</span></div>'+
      all.map(personRow).join("")+
      '<div class="mut" style="font-size:12px;margin-top:6px">Tap a name to see every note that passed through that hand.</div>'
    ):'<span class="mut">no custody balances recorded yet</span>';
    var ev=(j.events||[]).slice(0,8);
    $("custEv").innerHTML=ev.length?('<div class="mut" style="margin:10px 0 2px">Recent movements (all hands)</div><div class="tblwrap"><table><thead><tr><th>Date</th><th>From</th><th>To</th><th class="num">Amount</th><th>Note</th></tr></thead><tbody>'+
      ev.map(function(e){return '<tr><td>'+esc(e.date)+'</td><td>'+esc(NAMES[e.frm]||e.frm)+'</td><td>'+esc(NAMES[e.to]||e.to)+'</td><td class="num">'+fmt(e.amount)+
        (e.month_end?' <span class="badge b-warn">'+esc(e.month_end)+'</span>':'')+'</td><td class="mut">'+esc(e.note||"")+'</td></tr>'}).join("")+
      '</tbody></table></div>'):"";
  }).catch(function(){$("custHeld").textContent="could not load"});
}"""
def main():
    h=open(TARGET,encoding="utf-8").read()
    if h.count(NEW)==1 and h.count(OLD)==0:
        print("      ALREADY PATCHED."); return
    if h.count(OLD)!=1:
        print("*** PREFLIGHT FAILED: anchor found %d time(s), expected 1."%h.count(OLD)); sys.exit(2)
    open(TARGET,"w",encoding="utf-8").write(h.replace(OLD,NEW,1))
    print("      custody balances now parse correctly; total + per-hand figures show.")
if __name__=="__main__": main()
