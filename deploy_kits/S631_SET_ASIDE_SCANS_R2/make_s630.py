#!/usr/bin/env python3
"""make_s630.py -- kit S630_SET_ASIDE_SCANS: builds the TO files from the FROM bytes by anchored edits (each anchor exactly once, else stop).
    python3 -B make_s630.py --finance <dir with the FROM files> --out <dir>"""
import argparse, hashlib, os, sys

FROM = {"order_track.py": "4edfef6b21b0734b79028d0bf6e3930e", "porders_s454.py": "0ce8352597a0c2a45ba977c7ebf510ed"}
EDITS = {"order_track.py": [
    ('''KIT = "S628_ONE_NAME_LIST"                                    # v1.1 S628 (D761)''',
     '''KIT = "S630_SET_ASIDE_SCANS"                                  # v1.2 S630: a set-aside scan is never offered Send back nor named twice; v1.1 S628 (D761)'''),
    ('''VERSION = "1.1"''', '''VERSION = "1.2"'''),
    ('''            x["head_stamp"] = (ctx.scans.get(h) or {}).get("stamp_no") or "#%d" % h      # S628: the clearer scan's own number''',
     '''            x["head_stamp"] = (ctx.scans.get(h) or {}).get("stamp_no") or "#%d" % h      # S628: the clearer scan's own number
            x["set_aside"] = _aside(ctx.scans.get(int(x["scan"])))                         # S630: set aside by the scan app (a copy / rejected)
            x["head_set_aside"] = _aside(ctx.scans.get(h))'''),
    ('''def same_paper(con, ctx):''', '''def _aside(s):
    """S630: a scan the scan app set aside (rejected -- a duplicate or refused) or marked a copy (dup_of): never sent back, never named twice."""
    s = s or {}
    return str(s.get("status") or "") == "rejected" or bool(s.get("dup_of"))


def same_paper(con, ctx):'''),
    ('''        if str(s.get("created_at") or "")[:10] < since(con) or not ctx.usable(sid):
            continue
        rd = ctx.read.get(int(sid)) or {}''', '''        if str(s.get("created_at") or "")[:10] < since(con) or not ctx.usable(sid) or _aside(s):
            continue                                          # S630: a set-aside scan is already handled -- never named as a second copy
        rd = ctx.read.get(int(sid)) or {}'''),
], "porders_s454.py": [
    ('''    out, seen = [], set()
    for x in s.get("scans") or []:
        sid = int(x.get("head") or x["scan"])
        if sid in seen or x.get("other"):
            continue''', '''    out, seen = [], set()
    for x in s.get("scans") or []:
        sid = int(x.get("head") or x["scan"])
        if x.get("head_set_aside"):                           # S630: the clearer copy is set aside -- offer the tied scan itself, if it is not
            sid = int(x["scan"])
            if x.get("set_aside"):
                continue                                      # both set aside: nothing to send back (the scan app refuses it)
        if sid in seen or x.get("other"):
            continue'''),
    ('''        st = x.get("stamp") if int(x["scan"]) == sid else (x.get("head_stamp") or "#%d" % sid)''',
     '''        st = x.get("stamp") if int(x["scan"]) == sid else (x.get("head_stamp") or "#%d" % sid)   # S630: never a set-aside scan here'''),
]}


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for label, edits in EDITS.items():
        src = open(os.path.join(a.finance, label), "rb").read()
        if md5(src) != FROM[label]:
            sys.exit("STOP %s: md5 %s is not the FROM pin %s" % (label, md5(src), FROM[label]))
        s = src.decode("utf-8")
        for i, (x, y) in enumerate(edits):
            n = s.count(x)
            if n != 1:
                sys.exit("STOP %s edit %d: anchor found %d times (must be 1): %r" % (label, i + 1, n, x[:100]))
            s = s.replace(x, y)
        out = s.encode("utf-8")
        open(os.path.join(a.out, label), "wb").write(out)
        print("BUILT %-16s %s -> %s (%d edits)" % (label, FROM[label][:8], md5(out), len(edits)))


if __name__ == "__main__":
    main()
