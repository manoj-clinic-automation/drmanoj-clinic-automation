#!/usr/bin/env python3
"""make_s628.py -- kit S628_ONE_NAME_LIST: builds the TO files from the FROM bytes by anchored edits (each anchor exactly once, else stop).
    python3 -B make_s628.py --finance <dir with the FROM files> --assetapp <dir> --out <dir> [--kit <this folder>]"""
import argparse, hashlib, importlib.util, os, sys

FROM = {"stock_figure.py": "8c66b6b1010b7f0942768fe04022fa27", "porders.py": "b1736494f6dc58683ccb9c0a4c3fe181",
        "order_track.py": "a8c46700c4d3e2cbbb48767b6c46fa65", "porders_s454.py": "53ef850f5c337f44f3d24e1ca83dd960"}
EDIT_FILES = {"stock_figure.py": "edits_stock_figure.py", "porders.py": "edits_porders.py", "order_track.py": "edits_order_track.py",
              "porders_s454.py": "edits_porders_s454.py"}
NEW = ("med_names.py",)


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(kit, name):
    spec = importlib.util.spec_from_file_location(name[:-3], os.path.join(kit, name))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def apply(src, edits, label):
    s = src.decode("utf-8")
    for i, (a, b) in enumerate(edits):
        n = s.count(a)
        if n != 1:
            sys.exit("STOP %s edit %d: anchor found %d times (must be 1): %r" % (label, i + 1, n, a[:120]))
        s = s.replace(a, b)
    return s.encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--kit", default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for label, ef in EDIT_FILES.items():
        if not os.path.exists(os.path.join(a.kit, ef)):
            continue
        src = open(os.path.join(a.finance, label), "rb").read()
        if md5(src) != FROM[label]:
            sys.exit("STOP %s: md5 %s is not the FROM pin %s" % (label, md5(src), FROM[label]))
        m = load(a.kit, ef)
        edits = list(m.EDITS)
        if hasattr(m, "DS_NEW"):                              # porders: detect_supplies replaced whole, between two exact anchors
            s = src.decode("utf-8")
            i, j = s.find(m.DS_OLD_HEAD), s.find(m.DS_OLD_TAIL)
            if s.count(m.DS_OLD_HEAD) != 1 or s.count(m.DS_OLD_TAIL) != 1 or not (0 <= i < j):
                sys.exit("STOP porders.py: the detect_supplies anchors")
            src = (s[:i] + m.DS_NEW + s[j + len(m.DS_OLD_TAIL):]).encode("utf-8")
        out = apply(src, edits, label)
        open(os.path.join(a.out, label), "wb").write(out)
        print("BUILT %-18s %s -> %s (%d edits)" % (label, FROM[label][:8], md5(out), len(edits)))
    for n in NEW:
        b = open(os.path.join(a.kit, n), "rb").read()
        open(os.path.join(a.out, n), "wb").write(b)
        print("BUILT %-18s NEW  -> %s" % (n, md5(b)))


if __name__ == "__main__":
    main()
