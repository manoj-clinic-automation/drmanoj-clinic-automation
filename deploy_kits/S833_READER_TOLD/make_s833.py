#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s833.py -- S833_READER_TOLD: checks the live claude_reader.py and clinic_papers.py are at their FROM pins, applies the kit's
counted edits (edits_s833.py) to those live bytes, copies the NEW reader_watch.py, and refuses unless each result is byte-for-byte the
kit's whole file (its TO pin).

    python3 -B make_s833.py <FROM folder> <TO folder>
"""
import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import edits_s833                                                    # noqa: E402


def md5f(p):
    with open(p, "rb") as h:
        return hashlib.md5(h.read()).hexdigest()


def pin(name):
    with open(os.path.join(HERE, name)) as h:
        return h.read().strip()


def build(src, dst, out=print):
    os.makedirs(dst, exist_ok=True)
    for f in ("claude_reader.py", "clinic_papers.py"):
        if pin("PIN_FROM_%s.txt" % f[:-3]) != edits_s833.FROM[f]:
            out("the kit's FROM pin of %s and its edits disagree -- STOP" % f)
            return 1
        rc = edits_s833.build(f, os.path.join(src, f), os.path.join(dst, f), out=out)
        if rc:
            return rc
    shutil.copyfile(os.path.join(HERE, "reader_watch.py"), os.path.join(dst, "reader_watch.py"))
    for f in ("claude_reader.py", "clinic_papers.py", "reader_watch.py"):
        m = md5f(os.path.join(dst, f))
        if m != pin("PIN_TO_%s.txt" % f[:-3]) or m != md5f(os.path.join(HERE, f)):
            out("the rebuilt %s is %s, not the kit's TO %s -- STOP" % (f, m[:8], pin("PIN_TO_%s.txt" % f[:-3])[:8]))
            return 1
        out("%s: = the kit's whole file %s" % (f, m))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(build(sys.argv[1], sys.argv[2]))
