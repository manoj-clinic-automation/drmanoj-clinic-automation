#!/usr/bin/env python3
"""apply_s447.py -- kit S447_RATE_GROUPS (session 288, 02-Oct-2026). F-681, the owner: 'cast slab is coming at
three places'. The rate page (/finance/clinic/sheets) built its procedure groups by ADJACENCY, while services()
hands the rows over sorted by name -- so 'Cast / slab' broke wherever Dressing and the ILI lines sort in between
(live, 02-Oct: Cast / slab 11 . Dressing 1 . Cast / slab 2 . Injection (ILI) 5 . Cast / slab 8 . Other 1).
Now every group is ONE block wherever its rows sort: Cast / slab, then Injection (ILI), then Dressing, then any
other group by name, 'Other' last; inside a block a line waiting for his call comes first, then by name -- so each
site's cast sits directly above its slab. Nothing else changes: no row, no price, no status, no route, the X-ray
section untouched, the staff parchi's own list (slip_log, by id) untouched.
ONE anchored edit on EXACT bytes: FROM 6a04071d (S441, live). usage: apply_s447.py <owner_sheets.py>"""
import hashlib
import sys

FROM = "6a04071db4667a129dbd0446686bf749"
TAG = "S447 (F-681)"
OLD = '''        groups = []
        for r in rows:
            g = r["grp"] or "Other"
            if not groups or groups[-1][0] != g:
                groups.append((g, []))
            groups[-1][1].append(r)
'''
NEW = '''        by = {}                                      # S447 (F-681): one block per group, wherever its rows sort
        for r in rows:
            by.setdefault(r["grp"] or "Other", []).append(r)
        first = ("Cast / slab", "Injection (ILI)", "Dressing")
        order = sorted(by, key=lambda g: (first.index(g) if g in first else len(first), g == "Other", g.lower()))
        groups = [(g, sorted(by[g], key=lambda r: (r["status"] != "pending", r["name"].lower()))) for g in order]
'''


def apply(path):
    raw = open(path, "rb").read()
    s = raw.decode("utf-8")
    if TAG in s:
        return "already"
    if hashlib.md5(raw).hexdigest() != FROM:
        raise SystemExit("REFUSED: owner_sheets.py is %s, not the S441 bytes %s" % (hashlib.md5(raw).hexdigest(), FROM))
    if s.count(OLD) != 1:
        raise SystemExit("REFUSED: anchor not found exactly once")
    open(path, "wb").write(s.replace(OLD, NEW).encode("utf-8"))
    return "patched"


if __name__ == "__main__":
    print("owner_sheets.py :", apply(sys.argv[1]))
