#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s767.py — one CSS edit on the LIVE casepack_page.html (333f7825, S764's TO): the nowrap rule meant for the two
box titles (DTH rates · Build an estimate) also reached the fold labels INSIDE the Build box, so a long fold label ran
into its figure (the live read of S764, 18:0x IST 09-Nov). The selector is narrowed to the box's own summary.
  python make_s767.py <from_dir> <to_dir>"""
import os, sys, hashlib
def md5(b): return hashlib.md5(b).hexdigest()
src, dst = sys.argv[1], sys.argv[2]; os.makedirs(dst, exist_ok=True)
b = open(os.path.join(src, "casepack_page.html"), "rb").read(); t = b.decode("utf-8")
old = ".s764box summary .k{white-space:nowrap}"; new = ".s764box > summary > .k{white-space:nowrap}"
if t.count(old) != 1: raise SystemExit("anchor occurs %d time(s)" % t.count(old))
t = t.replace(old, new); out = t.encode("utf-8")
open(os.path.join(dst, "casepack_page.html"), "wb").write(out)
print("FROM %s TO %s %d bytes" % (md5(b)[:8], md5(out), len(out)))
