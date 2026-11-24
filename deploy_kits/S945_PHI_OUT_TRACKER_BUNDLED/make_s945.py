#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s945.py -- kit S945 (the parent, S511, 24-Nov-2026): builds state_backup/code_bundle.py (TO) from the live bytes (FROM
aa8f985f) by ONE exact anchor -- the server tracker's code (/root/followup_tracker, top level only: *.py and *.sh; never data/,
uploads/, archive/, venv/, logs/, outputs/, intake/, which are folders and a non-recursive source never enters them) joins the
nightly code bundle (roadmap S510 A4, F-1613). Nothing else moves.
    python3 make_s945.py <code_bundle.py FROM> <code_bundle.py TO>
"""
import ast
import hashlib
import sys

FROM_MD5 = "aa8f985f197289992e502b0cf997a25d"
A1 = '''    ("root/assetapp/static",         ("*.js",),                                      False, ()),
'''
N1 = A1 + '''    # --- v1.9 (S945, 24-Nov-2026, F-1613): the follow-up tracker runs on the box since S895 (the switch 23-Nov); its code was in
    # no bundle. Top level only -- data/, uploads/, archive/, venv/, logs/, outputs/, intake/ are folders a non-recursive source never
    # enters; OFF, SWITCHED_AT, *.txt and *.json (state, seeds) stay out by the patterns; token/secret/users by name.
    ("root/followup_tracker",        ("*.py", "*.sh"),                               False, ("token", "secret", "users")),
'''


def main():
    src_p, dst_p = sys.argv[1], sys.argv[2]
    raw = open(src_p, "rb").read()
    got = hashlib.md5(raw).hexdigest()
    if got != FROM_MD5:
        sys.exit("FROM is %s, not %s -- read the live bytes first (F-472)" % (got[:8], FROM_MD5[:8]))
    t = raw.decode("utf-8")
    if t.count(A1) != 1:
        sys.exit("anchor not found exactly once")
    if "root/followup_tracker" in t:
        sys.exit("already carries the tracker")
    t = t.replace(A1, N1)
    ast.parse(t)
    out = t.encode("utf-8")
    open(dst_p, "wb").write(out)
    print("TO %s (%d bytes)" % (hashlib.md5(out).hexdigest(), len(out)))


if __name__ == "__main__":
    main()
