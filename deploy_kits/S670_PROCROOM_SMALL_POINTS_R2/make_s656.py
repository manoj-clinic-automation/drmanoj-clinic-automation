#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s656.py -- S656_PROCROOM_SMALL_POINTS: checks the live procroom.py is at its FROM pin (S648's TO), applies the kit's counted
edits (edits_s656.py) to those live bytes, and refuses unless the result is byte-for-byte the kit's whole procroom.py (its TO pin).
The kit changes no other file.

    python3 -B make_s656.py <FROM folder> <TO folder>
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import edits_s656                                                    # noqa: E402


def md5f(p):
    with open(p, "rb") as h:
        return hashlib.md5(h.read()).hexdigest()


def pin(name):
    with open(os.path.join(HERE, name)) as h:
        return h.read().strip()


def build(src, dst, out=print):
    os.makedirs(dst, exist_ok=True)
    if pin("PIN_FROM_procroom.txt") != edits_s656.FROM_PIN:
        out("the kit's FROM pin and its edits disagree -- STOP")
        return 1
    rc = edits_s656.build(os.path.join(src, "procroom.py"), os.path.join(dst, "procroom.py"), out=out)
    if rc:
        return rc
    m = md5f(os.path.join(dst, "procroom.py"))
    if m != pin("PIN_TO_procroom.txt") or m != md5f(os.path.join(HERE, "procroom.py")):
        out("the rebuilt procroom.py is %s, not the kit's TO %s -- STOP" % (m[:8], pin("PIN_TO_procroom.txt")[:8]))
        return 1
    out("procroom.py: rebuilt on the live FROM bytes = the kit's whole file %s" % m)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(build(sys.argv[1], sys.argv[2]))
