#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s651.py -- S651_CLEARER_DUPLICATE (D761: the clearer scan of a duplicate kept): checks each live file is at its FROM pin and
places the kit's whole files beside them. The kit changes no other file.

    python3 -B make_s651.py <FROM folder> <TO folder>
"""
import hashlib
import os
import shutil
import sys

FROM_PIN = {"scan_checks_s441.py": "b9ba6839ec7979cb709909214d6a0b69",
            "asset_register.py": "068440f7106b6e78b78c1ca3266b9a47",
            "sorting_desk.py": "ca9fda745914c2875c8056a0091b0c1a"}
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
    for f in FROM_PIN:
        shutil.copyfile(os.path.join(HERE, f), os.path.join(dst, f))
        out("%s: FROM %s = the pin; the kit's whole file %s" % (f, FROM_PIN[f][:8], md5f(os.path.join(dst, f))))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(build(sys.argv[1], sys.argv[2]))
