#!/usr/bin/env python3
"""F-155 display: the pushed-reports badge tells the truth (reads ingested_count).
Fail-loud: the anchor must occur exactly once. Usage: patch_f155.py <finance_approvals.html>"""
import sys
OLD='''        var st=p.status==="pending"?'<span class="badge b-warn">⏳ PENDING</span>'
              :p.status==="applied"?'<span class="badge b-ok">✓ applied '+esc((p.applied_at||"").slice(0,16))+"</span>"
              :'<span class="badge b-bad">'+esc(p.status)+"</span>";'''
NEW='''        var _loaded=(p.ingested_count||0)>0;
        var st=(p.status==="pending"&&p.applied_at)?'<span class="badge b-warn">⏳ waiting — day not filed yet; re-apply once filed</span>'
              :p.status==="pending"?'<span class="badge b-warn">⏳ PENDING</span>'
              :(p.status==="applied"&&_loaded)?'<span class="badge b-ok">✓ loaded '+esc((p.applied_at||"").slice(0,16))+"</span>"
              :p.status==="applied"?'<span class="badge b-bad">⚠ loaded nothing — re-load from Marg</span>'
              :'<span class="badge b-bad">'+esc(p.status)+"</span>";'''
p=sys.argv[1]; s=open(p,encoding="utf-8").read()
if s.count(OLD)!=1:
    sys.stderr.write("REFUSED: badge anchor found %d times (need 1)\n"%s.count(OLD)); sys.exit(3)
open(p,"w",encoding="utf-8").write(s.replace(OLD,NEW)); print("  F-155 badge patched:",p)
