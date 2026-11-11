#!/usr/bin/python3
# make_s789.py -- kit S789_LAB_TILE_COUNT (S428, 11-Nov-2026, the parent; the owner 09:29 IST: "for the lab reports, it is still showing
# the same number 42"). Usage: make_s789.py <live check_screens.py> <out dir>. Exact replacements on check_screens.py e86f16e1 (S788).
import hashlib, os, sys
src, out = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
assert hashlib.md5(b).hexdigest().startswith("e86f16e1"), "not the live check_screens.py (e86f16e1)"
C = b.decode("utf-8")
def rp(t, a, b):
    assert t.count(a) == 1, "anchor not once: " + a[:80]
    return t.replace(a, b)
C = rp(C, 'VERSION = "S788 1"', 'VERSION = "S789 1"')
# his console line and the tile count: only the reports that need an answer (a likely wrong ID)
C = rp(C, '"lab": len(lab_items(con)),', '"lab": len([i for i in lab_items(con) if i["wrong"]]),   # S789: only what needs an answer')
# his page: the asking ones first in the list
C = rp(C, '"lab": lab_items(con),', '"lab": sorted(lab_items(con), key=lambda i: not i["wrong"]),   # S789: the asking ones first')
C = rp(C, """<span class="n" style="color:'+t[3]+'">'+B[t[0]].length+'</span>""",
          """<span class="n" style="color:'+t[3]+'">'+(t[0]==='lab'?B.lab.filter(function(i){return i.wrong;}).length:B[t[0]].length)+'</span>""")
C = rp(C, """['lab','Lab report filed, no blood slip','in the record already · for your information','#1D4ED8']""",
          """['lab','Lab report — wrong ID?','needs an answer · '+B.lab.filter(function(i){return !i.wrong;}).length+' more filed with no blood slip, for information only','#1D4ED8']""")
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "check_screens.py"), "wb").write(C.encode("utf-8"))
print("written check_screens.py", hashlib.md5(C.encode("utf-8")).hexdigest()[:8])
