#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s715.py -- builds S715's sorting_desk.py from the live FROM bytes by the counted edits in edits_s715.py.

    python3 -B make_s715.py <FROM sorting_desk.py> <OUT path> [--expect <md5 of the kit's TO>]

Refuses (exit 2, nothing written) when the FROM file's md5 is not the pinned one, when any anchor is not found exactly once, when
the result does not compile, or (--expect) when the result differs from the kit's TO. Standard library only.
"""
import hashlib
import os
import py_compile
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import edits_s715 as E                                               # noqa: E402

FROM_MD5 = "35fdd6c53d04d0b5740aa0e56816d422"


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(src):
    t = src
    for name, (start, end, new) in E.BETWEEN:
        if t.count(start) != 1 or t.count(end) != 1:
            raise SystemExit("REFUSED: %s -- its markers occur %d / %d times (each must be once)" % (name, t.count(start), t.count(end)))
        a = t.index(start)
        b = t.index(end)
        if b <= a:
            raise SystemExit("REFUSED: %s -- the end marker is before the start" % name)
        t = t[:a] + new + t[b:]
    for name, (old, new) in E.EDITS:
        n = t.count(old)
        if n != 1:
            raise SystemExit("REFUSED: edit '%s' -- its anchor occurs %d times (must be once)" % (name, n))
        t = t.replace(old, new)
    return t


def main():
    a, skip = [], False
    for x in sys.argv[1:]:
        if skip:
            skip = False
        elif x == "--expect":
            skip = True
        elif not x.startswith("--"):
            a.append(x)
    if len(a) != 2:
        print(__doc__)
        sys.exit(2)
    src_b = open(a[0], "rb").read()
    if md5(src_b) != FROM_MD5:
        print("REFUSED: %s is %s, not the pinned FROM %s -- nothing written" % (a[0], md5(src_b), FROM_MD5))
        sys.exit(2)
    try:
        out = build(src_b.decode("utf-8")).encode("utf-8")
    except SystemExit as e:
        print(str(e) + " -- nothing written")
        sys.exit(2)
    tmp = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
    tmp.write(out)
    tmp.close()
    try:
        py_compile.compile(tmp.name, doraise=True)
    except py_compile.PyCompileError as e:
        print("REFUSED: the result does not compile -- %s" % e)
        sys.exit(2)
    finally:
        os.unlink(tmp.name)
        c = tmp.name + "c"
        if os.path.exists(c):
            os.unlink(c)
    if "--expect" in sys.argv:
        want = sys.argv[sys.argv.index("--expect") + 1]
        if md5(out) != want:
            print("REFUSED: the rebuilt file is %s, the kit's TO is %s -- nothing written" % (md5(out), want))
            sys.exit(2)
    with open(a[1], "wb") as f:
        f.write(out)
    print("BUILT %s md5 %s (%d edits + %d whole functions, from %s)" % (a[1], md5(out), len(E.EDITS), len(E.BETWEEN), FROM_MD5[:8]))


if __name__ == "__main__":
    main()
