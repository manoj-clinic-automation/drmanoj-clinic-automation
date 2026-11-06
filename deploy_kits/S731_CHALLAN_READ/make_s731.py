#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s731.py -- builds S731's asset_register.py and sorting_desk.py from the live FROM bytes by the counted edits in edits_s731.py.

    python3 -B make_s731.py <FROM folder> <OUT folder> [--expect]

--expect: each result must equal the kit's own whole file (PIN_TO_<name>.txt). Refuses (exit 2, nothing written) when a FROM file is
not at its pin, when any anchor is not found exactly once, when a result does not compile, or (--expect) differs from its TO pin.
Standard library only.
"""
import hashlib
import os
import py_compile
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import edits_s731 as E                                               # noqa: E402


def md5(b):
    return hashlib.md5(b).hexdigest()


def pin(name):
    return open(os.path.join(HERE, name)).read().strip()


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) != 2:
        print(__doc__)
        sys.exit(2)
    src, out = a
    built = {}
    for f, edits in E.EDITS.items():
        b = open(os.path.join(src, f), "rb").read()
        want = pin("PIN_FROM_%s.txt" % f[:-3])
        if md5(b) != want:
            print("REFUSED: %s is %s, not the pinned FROM %s -- nothing written" % (f, md5(b), want))
            sys.exit(2)
        t = b.decode("utf-8")
        for name, old, new in edits:
            n = t.count(old)
            if n != 1:
                print("REFUSED: %s edit '%s' -- its anchor occurs %d times (must be once) -- nothing written" % (f, name, n))
                sys.exit(2)
            t = t.replace(old, new)
        o = t.encode("utf-8")
        tmp = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
        tmp.write(o)
        tmp.close()
        try:
            py_compile.compile(tmp.name, cfile=tmp.name + "c", doraise=True)
        except py_compile.PyCompileError as e:
            print("REFUSED: %s does not compile -- %s" % (f, e))
            sys.exit(2)
        finally:
            for p in (tmp.name, tmp.name + "c"):
                if os.path.exists(p):
                    os.unlink(p)
        if "--expect" in sys.argv and md5(o) != pin("PIN_TO_%s.txt" % f[:-3]):
            print("REFUSED: the rebuilt %s is %s, the kit's TO is %s -- nothing written" % (f, md5(o), pin("PIN_TO_%s.txt" % f[:-3])))
            sys.exit(2)
        built[f] = o
    for f, o in built.items():
        with open(os.path.join(out, f), "wb") as fh:
            fh.write(o)
        print("BUILT %s md5 %s (%d edits, from %s)" % (f, md5(o), len(E.EDITS[f]), pin("PIN_FROM_%s.txt" % f[:-3])[:8]))


if __name__ == "__main__":
    main()
