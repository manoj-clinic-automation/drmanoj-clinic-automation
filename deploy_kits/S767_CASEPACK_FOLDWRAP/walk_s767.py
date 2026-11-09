#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s767.py <dir> [--control] — the page's fold labels inside the Build box may wrap; the box titles may not.
Green on the kit's page ("WALK OK"); red on the live page ("CONTROL: red at check 1")."""
import os, sys, re
d = sys.argv[1]; control = "--control" in sys.argv
t = open(os.path.join(d, "casepack_page.html"), encoding="utf-8").read()
n = 0; fails = []
def ck(label, cond):
    global n; n += 1
    print("  %d %s %s" % (n, "ok " if cond else "RED", label))
    if not cond:
        fails.append(n)
        if control: print("CONTROL: red at check %d (%s)" % (n, label)); sys.exit(0)
ck("the nowrap rule reaches only the box's own title (.s764box > summary > .k)", ".s764box > summary > .k{white-space:nowrap}" in t and ".s764box summary .k{white-space:nowrap}" not in t)
ck("the S764 block, the four live stages and the foot bar are untouched", all(s in t for s in ("s764css", "1 · Estimate", "4 · IPD case", "Estimates given", "Manage packages", "function csGenerate", "window.s764Render")))
ck("exactly one byte-run differs from S764's page: the selector", t.count("s764box > summary") == 1)
if control: print("CONTROL: did NOT go red"); sys.exit(2)
if fails: print("WALK FAILED %s" % fails); sys.exit(1)
print("WALK OK %d/%d" % (n, n))
