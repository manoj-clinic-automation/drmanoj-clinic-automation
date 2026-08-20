#!/usr/bin/env python3
# S193_CASHPOS3 - Cash position: every line clickable-to-expand (drawer day-wise,
# reserve movements, Manoj movements, bank deposits list) + cache-busted fetch
# so a stale response can never mask fresh data. In-place html patch, fail-loud, idempotent.
import sys
TARGET="/root/finance/finance_ui/finance_approvals.html"
OLD=r"""function loadCashPos(){
  fetch("/finance/api/cash-position").then(function(r){return r.json()}).then(function(j){
    if(!j.ok){$("cashPos").textContent="could not load";return}
    var days=(j.days||[]);
    var h='<div class="stat" style="margin-bottom:2px"><span class="lbl">In Darpan’s drawer'+(j.as_of?' · as of '+esc(j.as_of):'')+'</span><span class="val">'+fmt(j.drawer)+'</span></div>'+
      '<div class="stat"><span class="lbl">Parked · Dr Bhawna (reserve)</span><span class="val">'+fmt(j.reserve)+'</span></div>'+
      '<div class="stat"><span class="lbl">Parked · Dr Manoj</span><span class="val">'+fmt(j.with_manoj)+'</span></div>'+
      '<div class="stat"><span class="lbl">Unbanked total (drawer + parked)</span><span class="val">'+fmt(j.unbanked)+'</span></div>'+
      '<div class="stat"><span class="lbl">Banked to date ('+esc(j.bank_count)+')'+(j.last_bank_date?' · last '+esc(j.last_bank_date):'')+'</span><span class="val">'+fmt(j.bank_deposited)+'</span></div>';
    h+='<div class="custPerson" style="border-top:1px solid #eee"><div onclick="tog(this)" style="cursor:pointer;padding:9px 2px"><span class="mut" style="font-size:12px">› drawer day by day</span></div>'+
      '<div style="display:none"><div class="tblwrap" style="margin:2px 0 6px"><table><thead><tr><th>Date</th><th class="num">In drawer</th><th class="num">Unbanked</th></tr></thead><tbody>'+
      days.map(function(d){return '<tr><td>'+esc(d.date)+'</td><td class="num">'+fmt(d.drawer)+'</td><td class="num">'+fmt(d.unbanked)+'</td></tr>'}).join("")+
      '</tbody></table></div></div></div>';
    $("cashPos").innerHTML=h;
  }).catch(function(){$("cashPos").textContent="could not load"});
}"""
NEW=r"""function loadCashPos(){
  fetch("/finance/api/cash-position?_="+(new Date()).getTime(),{cache:"no-store"}).then(function(r){return r.json()}).then(function(j){
    if(!j.ok){$("cashPos").textContent="could not load";return}
    var NM={dr_bhawna:"Dr Bhawna",drawer:"Drawer (Darpan)",counter:"Counter (Vinay)",dr_manoj:"Dr Manoj",bank:"Bank"};
    function row(label,val,detailHtml){
      return '<div class="custPerson" style="border-top:1px solid #eee">'+
        '<div onclick="tog(this)" style="display:flex;justify-content:space-between;align-items:center;cursor:pointer;padding:10px 2px">'+
        '<span><span class="mut" style="color:#999">▸</span> '+label+'</span><span class="val" style="font-size:18px">'+fmt(val)+'</span></div>'+
        '<div style="display:none;padding-left:6px">'+detailHtml+'</div></div>';
    }
    function evTable(list){
      if(!list||!list.length)return '<div class="mut" style="padding:6px 2px">no recorded movements yet</div>';
      return '<div class="tblwrap" style="margin:2px 0 6px"><table><thead><tr><th>Date</th><th>From</th><th>To</th><th class="num">Amount</th><th>Note</th></tr></thead><tbody>'+
        list.map(function(e){return '<tr><td>'+esc(e.date)+'</td><td>'+esc(NM[e.frm]||e.frm)+'</td><td>'+esc(NM[e.to]||e.to)+'</td><td class="num">'+fmt(e.amount)+'</td><td class="mut">'+esc((e.note||"").slice(0,80))+'</td></tr>'}).join("")+'</tbody></table></div>';
    }
    var days=(j.days||[]);
    var drawerDetail='<div class="tblwrap" style="margin:2px 0 6px"><table><thead><tr><th>Date</th><th class="num">In drawer</th><th class="num">Unbanked</th></tr></thead><tbody>'+
      days.map(function(d){return '<tr><td>'+esc(d.date)+'</td><td class="num">'+fmt(d.drawer)+'</td><td class="num">'+fmt(d.unbanked)+'</td></tr>'}).join("")+'</tbody></table></div>';
    var deps=(j.bank_deposits||[]);
    var depDetail=deps.length?('<div class="tblwrap" style="margin:2px 0 6px"><table><thead><tr><th>Date</th><th class="num">Amount</th><th>Ref</th></tr></thead><tbody>'+
      deps.map(function(d){return '<tr><td>'+esc(d.date)+'</td><td class="num">'+fmt(d.amount)+'</td><td class="mut">'+esc(d.ref)+'</td></tr>'}).join("")+'</tbody></table></div>'):'<div class="mut" style="padding:6px 2px">no deposits recorded</div>';
    $("cashPos").innerHTML=
      '<div class="stat" style="margin-bottom:4px"><span class="lbl">Unbanked total'+(j.as_of?' · as of '+esc(j.as_of):'')+'</span><span class="val">'+fmt(j.unbanked)+'</span></div>'+
      row("In Darpan’s drawer", j.drawer, drawerDetail)+
      row("Parked · Dr Bhawna (reserve)", j.reserve, evTable(j.reserve_detail))+
      row("Parked · Dr Manoj", j.with_manoj, evTable(j.manoj_detail))+
      row("Banked to date ("+esc(j.bank_count)+")", j.bank_deposited, depDetail)+
      '<div class="mut" style="font-size:12px;margin-top:6px">Tap any line to expand its detail.</div>';
  }).catch(function(){$("cashPos").textContent="could not load"});
}"""
def main():
    h=open(TARGET,encoding="utf-8").read()
    if h.count(NEW)==1 and h.count(OLD)==0: print("      ALREADY PATCHED."); return
    if h.count(OLD)!=1: print("*** PREFLIGHT FAILED: anchor found %d time(s), expected 1."%h.count(OLD)); sys.exit(2)
    open(TARGET,"w",encoding="utf-8").write(h.replace(OLD,NEW,1))
    print("      Cash position rows now expandable + cache-busted.")
if __name__=="__main__": main()
