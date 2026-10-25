#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s648.py -- S648_PROCROOM_OPEN_DOOR (the count door for the parent's Aaj ka kaam line, and Baaki din back to 01-10-2026): checks the live procroom.py is at its FROM pin (S643's TO) and places the kit's
whole procroom.py beside it. The kit changes no other file.

    python3 -B make_s648.py <FROM folder> <TO folder>
"""
import hashlib
import os
import shutil
import sys

FROM_PIN = {"procroom.py": "7b936d6f05240f17423b93b223d73a36"}
HERE = os.path.dirname(os.path.abspath(__file__))


def md5f(p):
    with open(p, "rb") as h:
        return hashlib.md5(h.read()).hexdigest()


def build(src, dst, out=print):
    os.makedirs(dst, exist_ok=True)
    for f, pin in FROM_PIN.items():
        m = md5f(os.path.join(src, f))
        if m != pin:
            out("%s: FROM is %s, not the pin %s -- STOP" % (f, m[:8], pin[:8]))
            return 1
    shutil.copyfile(os.path.join(HERE, "procroom.py"), os.path.join(dst, "procroom.py"))
    out("procroom.py: FROM %s = the pin; the kit's whole file %s" % (FROM_PIN["procroom.py"][:8], md5f(os.path.join(dst, "procroom.py"))))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(build(sys.argv[1], sys.argv[2]))
