#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s674.py -- S674_VARIETY_FLOW: checks the live stationery.py and sorting_desk.py are at their FROM pins, applies the kit's counted
edits (edits_s674.py, with s674_block.py) to those live bytes, and refuses unless each result is byte-for-byte the kit's whole file
(its TO pin). The kit changes no other file.

    python3 -B make_s674.py <FROM folder> <TO folder>
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import edits_s674                                                    # noqa: E402


def md5f(p):
    with open(p, "rb") as h:
        return hashlib.md5(h.read()).hexdigest()


def pin(name):
    with open(os.path.join(HERE, name)) as h:
        return h.read().strip()


def build(src, dst, out=print):
    os.makedirs(dst, exist_ok=True)
    if pin("PIN_FROM_stationery.txt") != edits_s674.FROM_PIN or pin("PIN_FROM_sorting_desk.txt") != edits_s674.FROM_PIN_DESK:
        out("the kit's FROM pins and its edits disagree -- STOP")
        return 1
    rc = edits_s674.build(os.path.join(src, "stationery.py"), os.path.join(dst, "stationery.py"), out=out)
    if rc:
        return rc
    rc = edits_s674.build_desk(os.path.join(src, "sorting_desk.py"), os.path.join(dst, "sorting_desk.py"), out=out)
    if rc:
        return rc
    for f in ("stationery.py", "sorting_desk.py"):
        m = md5f(os.path.join(dst, f))
        if m != pin("PIN_TO_%s.txt" % f[:-3]) or m != md5f(os.path.join(HERE, f)):
            out("the rebuilt %s is %s, not the kit's TO %s -- STOP" % (f, m[:8], pin("PIN_TO_%s.txt" % f[:-3])[:8]))
            return 1
        out("%s: rebuilt on the live FROM bytes = the kit's whole file %s" % (f, m))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(build(sys.argv[1], sys.argv[2]))
