#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s746.py -- builds S746's stationery.py from the live FROM bytes by the counted edits in edits_s746.py.

    python3 -B make_s746.py <FROM stationery.py> <OUT path> [--expect]

--expect: the result must equal the kit's own whole file (PIN_TO_stationery.txt). Refuses (exit 2, nothing written) when the FROM
file is not at its pin, when any anchor is not found exactly once, when the result does not compile, or (--expect) differs.
Standard library only.
"""
import hashlib
import os
import py_compile
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import edits_s746 as E                                               # noqa: E402


def md5(b):
    return hashlib.md5(b).hexdigest()


def pin(name):
    return open(os.path.join(HERE, name)).read().strip()


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) != 2:
        print(__doc__)
        sys.exit(2)
    src_b = open(a[0], "rb").read()
    want = pin("PIN_FROM_stationery.txt")
    if md5(src_b) != want:
        print("REFUSED: %s is %s, not the pinned FROM %s -- nothing written" % (a[0], md5(src_b), want))
        sys.exit(2)
    t = src_b.decode("utf-8")
    for name, (old, new) in E.EDITS:
        n = t.count(old)
        if n != 1:
            print("REFUSED: edit '%s' -- its anchor occurs %d times (must be once) -- nothing written" % (name, n))
            sys.exit(2)
        t = t.replace(old, new)
    out = t.encode("utf-8")
    tmp = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
    tmp.write(out)
    tmp.close()
    try:
        py_compile.compile(tmp.name, cfile=tmp.name + "c", doraise=True)
    except py_compile.PyCompileError as e:
        print("REFUSED: the result does not compile -- %s" % e)
        sys.exit(2)
    finally:
        for p in (tmp.name, tmp.name + "c"):
            if os.path.exists(p):
                os.unlink(p)
    if "--expect" in sys.argv and md5(out) != pin("PIN_TO_stationery.txt"):
        print("REFUSED: the rebuilt file is %s, the kit's TO is %s -- nothing written" % (md5(out), pin("PIN_TO_stationery.txt")))
        sys.exit(2)
    with open(a[1], "wb") as f:
        f.write(out)
    print("BUILT %s md5 %s (%d edits, from %s)" % (a[1], md5(out), len(E.EDITS), want[:8]))


if __name__ == "__main__":
    main()
