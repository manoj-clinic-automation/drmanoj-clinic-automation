#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
make_s520.py -- the builder of kit S520_AMIR_PROOF_ANY_CLOSING (10-Oct-2026, F-830).

    python3 -B make_s520.py --finance /root/finance --out DIR

Reads ONE live file, stock_app.py, refuses anything but its FROM pin (bfc2a40b, S500's TO), replaces ONE span inside
_s446_proof (the block S500's line opened, down to the `res = dict(state=("done" ...` line inclusive; each end of the span
must occur exactly once), compiles the result and refuses anything but its TO pin.  Nothing else in the file moves.

THE RULE (F-830, the owner's decision of 10-Oct): an item's voucher is PROVEN when the FIRST closing after the vouchers, or
the NEWEST one, shows it moved by exactly its vouchers -- never a middle closing alone (a sale the PC's figure misses could
cancel a real error there by coincidence, and a pass is recorded once).  Right on the first = keyed right, a later move is a
sale or a purchase; right on the newest = corrected in Marg after a wrong check (S500's F-801 case).  A still-wrong row reads
from the newest closing, as before.  The same function checks the stage-C medicine lots; the rule applies there on purpose.

Run with -B.  Never import this file.  It writes only inside --out.
"""
import argparse
import hashlib
import os
import sys

PINS = {"stock_app.py": ("bfc2a40bff0d8f0050078ea49f990eda", "1f43f47ea288c8bba3750b78ba4cef9b")}


def md5(b):
    return hashlib.md5(b).hexdigest()


class Stop(Exception):
    pass


START = "        R, L = before[-1], after[-1]                              # S500 (F-801): the NEWEST closing after the vouchers -- a correction made in Marg after a wrong check is seen\n"
END = "    if res.get(\"state\") == \"export\":                           # S488 (B.1): since when and for what -- keys added, nothing else\n"
NEW = r'''        R = before[-1]                                            # S520 (F-830): proven on the first or the newest closing after the vouchers
        _bR = _proof_basis(feeds[(R, "expected")]["source"])
        cands = [x for x in after if _proof_basis(feeds[(x, "expected")]["source"]) == _bR]   # the closings on R's basis; a re-based one is skipped
        if not cands:
            res = dict(state="export", rows=[], last_at=last_at, text="re-based between %s and %s" % (R, after[-1]))
        else:
            L = cands[-1]                                         # the newest on R's basis: as_after, and the numbers of a still-wrong row
            mR, eR, mL, eL = feeds[(R, "marg")]["items"], feeds[(R, "expected")]["items"], feeds[(L, "marg")]["items"], feeds[(L, "expected")]["items"]
            tries = []                                            # ONLY the first closing after the vouchers (when it is on R's basis) and the newest
            for x in (after[0], L):
                if x in cands and x not in tries:
                    tries.append(x)
            rows, proven_on = [], {}
            for item in sorted(need):
                for x in tries:
                    mX, eX = feeds[(x, "marg")]["items"], feeds[(x, "expected")]["items"]
                    if item in mR and item in eR and item in mX and item in eX and (mX[item] - eX[item]) - (mR[item] - eR[item]) == need[item]:
                        proven_on[item] = x
                        break
                if item in proven_on:
                    rows.append(dict(item=item, need=need[item], moved=need[item], marg=mL.get(item), should=mL.get(item), ok=True, keys=[_s446_key(k) for k in vno[item]]))
                    continue
                if item not in mR or item not in eR or item not in mL or item not in eL:
                    rows.append(dict(item=item, need=need[item], moved=None, marg=mL.get(item), should=None, ok=False, keys=[_s446_key(k) for k in vno[item]]))
                    continue
                moved = (mL[item] - eL[item]) - (mR[item] - eR[item])
                rows.append(dict(item=item, need=need[item], moved=moved, marg=mL[item], should=mL[item] + (need[item] - moved), ok=False,
                                 keys=[_s446_key(k) for k in vno[item]]))
            wrong = [r for r in rows if not r["ok"]]
            res = dict(state=("done" if not wrong else "wrong"), rows=wrong, as_before=R, as_after=L, last_at=last_at, items=len(rows), proven_on=proven_on)
'''


def build(t):
    if t.count(START) != 1 or t.count(END) != 1:
        raise Stop("the span's start occurs %d times, its end %d times (each must be exactly 1)" % (t.count(START), t.count(END)))
    i, j = t.index(START), t.index(END)
    if not i < j:
        raise Stop("the span's end is not after its start")
    old = t[i:j]
    if "res = dict(state=(\"done\" if not wrong else \"wrong\"), rows=wrong, as_before=R, as_after=L, last_at=last_at, items=len(rows))\n" not in old:
        raise Stop("the span does not end on the res = dict(...) line this builder was written on")
    if old.count("\n") != 16:
        raise Stop("the span is %d lines, not the 16 this builder was written on" % old.count("\n"))
    return t[:i] + NEW + t[j:]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--print-to", action="store_true", help="print the built md5 and accept it (packing the kit)")
    a = ap.parse_args(argv)
    name = "stock_app.py"
    frm, to = PINS[name]
    try:
        raw = open(os.path.join(a.finance, name), "rb").read()
        if md5(raw) != frm:
            raise Stop("%s is %s, not the FROM pin %s -- someone changed it since the brief" % (name, md5(raw), frm))
        if b"\r" in raw:
            raise Stop("%s carries carriage returns" % name)
        new = build(raw.decode("utf-8")).encode("utf-8")
        compile(new, name, "exec")
        if md5(new) != to and not a.print_to:
            raise Stop("%s built to %s, not the TO pin %s" % (name, md5(new), to))
    except Stop as e:
        print("STOP: %s" % e)
        return 2
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, name), "wb") as fh:
        fh.write(new)
    print("%s  %s -> %s  (%+d lines)" % (name, frm[:8], md5(new)[:8], new.count(b"\n") - raw.count(b"\n")))
    if a.print_to:
        print("   TO %s = %s" % (name, md5(new)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
