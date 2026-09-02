#!/usr/bin/env python3
"""
patch_hub_largegate_s220.py -- S220 item 1, part 3 of 3: the owner's card.

finance_ui/finance_approvals.html (pin 9f579dc6, the S220 F-277 bytes). Inside the
returns card that already exists -- no new card, no new tile (the owner's ruling
of 02-Sep: extend the card's drill-down; all English):
  H1  one line under the header: how many returns are Rs 1,000+ this month and
      how many still need his OK.
  H2  the row badge "Rs 1,000+ - your OK" on a large return.
  H3  the SPOT-COUNT LIST at the foot of the card: item, batch, why, the
      credit note, and a "counted" action that records the quantity (window
      .prompt, the pattern cnDecide already uses) or "skip".
  H4  the function behind that action.
Four anchored changes, sliced verbatim from the live bytes; the check is that
the file grew and carries the mark exactly once.

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_hub_largegate_s220.py
Offline: HUB_PATH=/path/to/finance_approvals.html.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('HUB_PATH', '/root/finance/finance_ui/finance_approvals.html')
MARK = 'S220 LARGE-RETURN GATE'

H1_OLD = '''    var h='<div style="font-size:14px">'+head+'</div>';\n    h+='<div class="mut" style="margin:4px 0">'+j.audited+' audited (lines + bill) · '+\n'''
H1_NEW = '''    var h='<div style="font-size:14px">'+head+'</div>';
    /* S220 LARGE-RETURN GATE: the line above which a return needs the owner's OK
       (returns.large_p). Size is where the money moved: 0 -> 6 such returns, May -> Aug. */
    (function(){
      var big=(j.notes||[]).filter(function(n){return n.large});
      var open=big.filter(function(n){return !n.approval||n.approval.status==="pending"});
      if(big.length){
        var rs=big.reduce(function(a,n){return a+(n.amount_p||0)},0);
        h+='<div style="margin:4px 0">₹'+((j.large_p||100000)/100).toFixed(0)+'+ returns this month: <b>'+big.length+'</b> · '+gapRs(rs)+
           (open.length?' · <span class="badge b-warn">'+open.length+' need your OK</span>':' · <span class="ok">all decided ✓</span>')+'</div>';
      }
    })();
    h+='<div class="mut" style="margin:4px 0">'+j.audited+' audited (lines + bill) · '+
'''

H2_OLD = '''         (n.refund_shortfall_p?' · <span class="badge b-warn">₹'+(n.refund_shortfall_p/100).toFixed(2)+' withheld on the refund</span>':'')+\n         '</summary>';\n'''
H2_NEW = '''         (n.refund_shortfall_p?' · <span class="badge b-warn">₹'+(n.refund_shortfall_p/100).toFixed(2)+' withheld on the refund</span>':'')+
         (n.large?' · <span class="badge b-warn">₹'+((j.large_p||100000)/100).toFixed(0)+'+ — your OK</span>':'')+
         '</summary>';
'''

H3_OLD = '''    h+='<div class="mut">A return is a second transaction that points at a first one; this card shows the chain that found it — or says honestly that none could be found. The detector proposes; you dispose.</div>';\n    box.innerHTML=h;\n'''
H3_NEW = '''    h+='<div class="mut">A return is a second transaction that points at a first one; this card shows the chain that found it — or says honestly that none could be found. The detector proposes; you dispose.</div>';
    /* S220 SPOT-COUNT LIST: the items the system flagged (a large return, or a money
       verdict), for a physical count. The deterrent the owner asked for while routine
       stock checking is suspended. Written after Apply and hourly; never on page load. */
    var sc=j.spot_checks||[];
    if(sc.length){
      var due=sc.filter(function(s){return s.status==="due"}).length;
      h+='<details style="margin:10px 0 4px 0"'+(due?' open':'')+'><summary><b>Spot-count list</b> · '+sc.length+' item(s)'+
         (due?' · <span class="badge b-warn">'+due+' to count</span>':' · <span class="ok">all counted ✓</span>')+'</summary>';
      h+='<div class="tblwrap"><table><thead><tr><th>item</th><th>batch</th><th>why</th><th>credit note</th><th>date</th><th>count</th></tr></thead><tbody>';
      sc.forEach(function(s){
        var act= s.status==="due"
          ? '<button class="ghost" onclick="spotCount('+s.id+',\\'done\\')">counted</button> <button class="ghost" onclick="spotCount('+s.id+',\\'skipped\\')">skip</button>'
          : (s.status==="done"?'<span class="ok">✓ '+esc(s.counted_qty||"")+'</span>':'<span class="mut">skipped</span>')+
            '<span class="mut"> · '+esc(s.counted_by||"")+' '+esc((s.counted_at||"").slice(0,16))+(s.note?' · '+esc(s.note):'')+'</span>';
        h+='<tr><td>'+esc(s.item_name||s.item_key)+'</td><td>'+esc(s.batch||"")+'</td><td>'+esc(s.reason)+'</td><td>'+esc(s.bill_no)+'</td><td>'+esc(s.business_date)+'</td><td>'+act+'</td></tr>';
      });
      h+='</tbody></table></div><div class="mut">Count the shelf, type what is there. The difference against Marg is read later; this only records the count, by name and time.</div></details>';
    }
    box.innerHTML=h;
'''

H4_OLD = '''function cnDecide(bill,decision){\n'''
H4_NEW = '''function spotCount(id,status){
  /* S220 SPOT-COUNT: record what was physically counted (or that it was skipped). */
  var qty="", note="";
  if(status==="done"){qty=window.prompt("Counted quantity on the shelf (as on the pack, e.g. 2:5):","")||"";
    if(!qty.trim())return;}
  else{note=window.prompt("Skip this count — why? (optional)","")||"";}
  fetch("/finance/darpan/api/spot-check",{method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({id:id,status:status,counted_qty:qty,note:note})})
   .then(function(r){return r.json()}).then(function(j){
     if(!j.ok){alert(j.message||j.error);return}
     loadCN();
   });
}
function cnDecide(bill,decision){
'''

PAIRS = [("H1", H1_OLD, H1_NEW), ("H2", H2_OLD, H2_NEW), ("H3", H3_OLD, H3_NEW), ("H4", H4_OLD, H4_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S220_large_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    if len(out) <= len(src) or out.count(MARK) != 1 or out.count("function spotCount(") != 1:
        raise SystemExit("REFUSED: the result is not the expected shape. NOTHING was changed.")
    open(TARGET, "w", encoding="utf-8").write(out)
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("restart  systemctl restart clinic-finance.service")
    return 0


if __name__ == "__main__":
    sys.exit(main())
