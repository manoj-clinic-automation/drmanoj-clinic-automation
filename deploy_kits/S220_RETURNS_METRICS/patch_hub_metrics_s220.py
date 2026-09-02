#!/usr/bin/env python3
"""
patch_hub_metrics_s220.py -- S220 item 2, part 2 of 2: the gist line on the card.

finance_ui/finance_approvals.html (pin 8b2a8348, the large-gate bytes). ONE anchored
change: directly under the returns header, one English line --

  Aug 2026: Rs 18,611 returned . 2.9% of sales (up; Jul 2.3%) . examinable 75% . flagged 29% . 3 to look at

The rate reads amber above 2.0% or when it rose on the previous month; examinable
reads green at 98%+ (the target), amber below; flagged is watched, not coloured.
Every number expands, in place, into the rows below it -- the same card, the same
place (the owner's ruling, 02-Sep).

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_hub_metrics_s220.py
Offline: HUB_PATH=/path/to/finance_approvals.html.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('HUB_PATH', '/root/finance/finance_ui/finance_approvals.html')
MARK = 'S220 METRICS'

H_OLD = '''    var h='<div style="font-size:14px">'+head+'</div>';\n    /* S220 LARGE-RETURN GATE'''
H_NEW = '''    var h='<div style="font-size:14px">'+head+'</div>';
    /* S220 METRICS: the gist. Rate = returns / sales on the bill spine, this month and
       last (one source, one rule); examinable and flagged = shares of this month's
       return rupees by the audit's own verdicts. Target: examinable >= 98%. */
    (function(){
      var M=j.metrics; if(!M) return;
      var MON=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
      var lab=function(m){return m?(MON[parseInt(m.slice(5,7),10)-1]+" "+m.slice(0,4)):""};
      var pc=function(v){return v==null?"—":(v.toFixed(1)+"%")};
      var rate=M.rate_pct, prev=M.prev_rate_pct;
      var arrow= (rate!=null&&prev!=null) ? (rate>prev?" ↑":(rate<prev?" ↓":" →")) : "";
      var rateBad=(rate!=null)&&(rate>2.0||(prev!=null&&rate>prev));
      var rateHtml=rate==null?'<span class="mut">rate —</span>'
        :'<span class="'+(rateBad?'badge b-warn':'ok')+'">'+pc(rate)+' of sales'+arrow+'</span>'+
         (prev!=null?' <span class="mut">('+lab(M.prev_month)+' '+pc(prev)+')</span>':'');
      var ex=M.examinable_pct;
      var exHtml=ex==null?'<span class="mut">examinable —</span>'
        :'examinable <span class="'+(ex>=98?'ok':'badge b-warn')+'">'+pc(ex)+'</span>';
      var flHtml='flagged <b>'+pc(M.flagged_pct)+'</b>'+(M.flagged_p?' <span class="mut">('+gapRs(M.flagged_p)+')</span>':'');
      var look=j.pending_approval||0;
      h+='<div style="margin:4px 0"><b>'+esc(lab(j.month))+':</b> '+gapRs(j.total_p)+' returned · '+rateHtml+' · '+exHtml+' · '+flHtml+
         ' · '+(look?'<span class="badge b-warn">'+look+' to look at</span>':'<span class="ok">nothing to look at</span>')+'</div>';
    })();
    /* S220 LARGE-RETURN GATE'''

PAIRS = [("H", H_OLD, H_NEW)]


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
    bak = TARGET + ".bak_S220_metrics_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    if len(out) <= len(src) or out.count(MARK) != 1:
        raise SystemExit("REFUSED: the result is not the expected shape. NOTHING was changed.")
    open(TARGET, "w", encoding="utf-8").write(out)
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("restart  systemctl restart clinic-finance.service")
    return 0


if __name__ == "__main__":
    sys.exit(main())
