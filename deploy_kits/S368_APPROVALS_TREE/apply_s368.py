#!/usr/bin/env python3
"""apply_s368.py -- kit S368_APPROVALS_TREE. Anchored edit on darpan_kal.py 19b9c0e8 (S365/S367 bytes):
init() also mounts sanjeevni_approvals (the tree's read door), exactly as it mounts sanjeevni_day.
  python3 apply_s368.py --dir /root/finance [--out DIR]     (in place when --out is omitted)
"""
import argparse, hashlib, os, sys
ap = argparse.ArgumentParser(); ap.add_argument("--dir", required=True); ap.add_argument("--out")
a = ap.parse_args()
p = os.path.join(a.dir, "darpan_kal.py"); s = open(p, encoding="utf-8").read()
assert hashlib.md5(s.encode("utf-8")).hexdigest() == "19b9c0e85bf73340df3dd006b1f5c9ce", "darpan_kal.py is not 19b9c0e8"
old = '''    except Exception as ex:                        # noqa: BLE001 -- the page falls back to the old panel
        print("sanjeevni_day not mounted: %s" % ex)
'''
new = old + '''    try:                                           # S368: the approvals tree's read door (sanjeevni_approvals.py)
        import sanjeevni_approvals
        sanjeevni_approvals.init(app, db_getter, require_fn, unit)
    except Exception as ex:                        # noqa: BLE001 -- the page then says what it could not read
        print("sanjeevni_approvals not mounted: %s" % ex)
'''
assert s.count(old) == 1
s = s.replace(old, new)
s = s.replace("#  darpan_kal.py", "#  darpan_kal.py", 1)
out = os.path.join(a.out or a.dir, "darpan_kal.py")
open(out, "w", encoding="utf-8").write(s)
print("darpan_kal.py ->", hashlib.md5(s.encode("utf-8")).hexdigest())
