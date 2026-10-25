#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s649.py -- S649_READER_PHOTO_SIZE (F-1003: a large phone photo shrunk for the reader by the venv python): checks the live claude_reader.py is at its FROM pin and places the kit's
whole claude_reader.py beside it. The kit changes no other file.

    python3 -B make_s649.py <FROM folder> <TO folder>
"""
import hashlib
import os
import shutil
import sys

FROM_PIN = {"claude_reader.py": "101189093f8d0f9921fbb3e41b66226e"}
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
    shutil.copyfile(os.path.join(HERE, "claude_reader.py"), os.path.join(dst, "claude_reader.py"))
    out("claude_reader.py: FROM %s = the pin; the kit's whole file %s" % (FROM_PIN["claude_reader.py"][:8], md5f(os.path.join(dst, "claude_reader.py"))))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(build(sys.argv[1], sys.argv[2]))
