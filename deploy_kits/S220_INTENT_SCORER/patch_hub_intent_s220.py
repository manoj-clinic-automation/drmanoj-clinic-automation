#!/usr/bin/env python3
"""
patch_hub_intent_s220.py -- S220 item 4, part 2 of 2: the Intent signals block on the card.

finance_ui/finance_approvals.html (pin dac5a86d, the metrics bytes). TWO anchored changes:
  H1  a collapsed block under the returns list -- "Intent signals (nightly) . N to look at"
      -- LOOK rows first, each with its plain-English detail, historical rows greyed and
      never counted. Owner-only content (the API answers others with nothing).
  H2  loadIntent() called beside loadCN() at page load.
English only. The check is that the file grew and carries the mark once.

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_hub_intent_s220.py
Offline: HUB_PATH=/path/to/finance_approvals.html.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('HUB_PATH', '/root/finance/finance_ui/finance_approvals.html')
MARK = 'S220 INTENT'

H1_OLD = '''  <div id="cnBox" class="note" style="margin-top:8px">loading&hellip;</div>\n</div>\n'''
H1_NEW = '''  <div id="cnBox" class="note" style="margin-top:8px">loading&hellip;</div>
  <!-- S220 INTENT: the nightly scorer's signals -- patterns against their own baselines,
       rows to look at, never findings. Owner-only. -->
  <div id="intentBox" style="margin-top:8px"></div>
</div>
'''
H2_OLD = '''    loadCN(); loadIDs();\n'''
H2_NEW = '''    loadCN(); loadIDs(); loadIntent();\n'''
H3_OLD = '''function cnDecide(bill,decision){\n'''
H3_NEW = '''function loadIntent(){
  /* S220 INTENT: signals from finance_intent.py (nightly). A signal is a pattern measured
     against its own baseline; LOOK means worth a minute, WATCH means on the record. */
  var box=document.getElementById("intentBox"); if(!box) return;
  fetch("/finance/darpan/api/intent").then(function(r){return r.json()}).then(function(j){
    if(!j.ok||!(j.signals||[]).length){box.innerHTML=j.note?'<div class="mut">Intent signals: '+esc(j.note)+'</div>':'';return}
    var look=j.look||0;
    var h='<details'+(look?' open':'')+'><summary><b>Intent signals</b> <span class="mut">(nightly, as of '+esc(j.as_of||"")+')</span>'+
      (look?' · <span class="badge b-warn">'+look+' to look at</span>':' · <span class="ok">nothing to look at</span>')+'</summary>';
    h+='<div class="tblwrap"><table><thead><tr><th></th><th>signal</th><th>where</th><th class="num">n</th><th class="num">now</th><th class="num">baseline</th><th class="num">×</th><th>what it saw</th></tr></thead><tbody>';
    j.signals.forEach(function(s){
      var lv= s.historical ? '<span class="mut">past</span>' : (s.level==="look" ? '<span class="badge b-warn">LOOK</span>' : '<span class="mut">watch</span>');
      var st= s.historical ? ' style="color:var(--text-3)"' : '';
      h+='<tr'+st+'><td>'+lv+'</td><td>'+esc(s.signal)+'</td><td>'+esc(s.scope)+' '+esc(s.key)+'</td>'+
         '<td class="num">'+(s.n==null?"—":s.n)+'</td><td class="num">'+(s.value==null?"—":s.value)+'</td>'+
         '<td class="num">'+(s.baseline==null?"—":s.baseline)+'</td><td class="num">'+(s.ratio==null?"—":s.ratio)+'</td>'+
         '<td>'+esc(s.detail||"")+(s.worth_p?' <span class="mut">('+gapRs(s.worth_p)+')</span>':'')+'</td></tr>';
    });
    h+='</tbody></table></div><div class="mut">A signal proposes; you dispose. Baselines are the counter\\'s own previous weeks. Rows marked past are before 02-Sep and raise nothing (D361).</div></details>';
    box.innerHTML=h;
  }).catch(function(e){box.innerHTML='<span class="mut">intent signals unavailable ('+e+')</span>'});
}
function cnDecide(bill,decision){
'''
PAIRS = [("H1", H1_OLD, H1_NEW), ("H2", H2_OLD, H2_NEW), ("H3", H3_OLD, H3_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S220_intent_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    if len(out) <= len(src) or out.count("function loadIntent(") != 1:
        raise SystemExit("REFUSED: the result is not the expected shape. NOTHING was changed.")
    open(TARGET, "w", encoding="utf-8").write(out)
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("restart  systemctl restart clinic-finance.service")
    return 0


if __name__ == "__main__":
    sys.exit(main())
