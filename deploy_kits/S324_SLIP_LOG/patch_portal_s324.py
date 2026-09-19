#!/usr/bin/env python3
"""patch_portal_s324.py -- builds the kit's portal.py from the live one (S324). Two anchored edits:
  1. the NEW tile 'OPD & X-ray/Proc Slips' (/finance/slips), roles ['doctor'] -- granted to staff by
     name in tile_grants.json v20, so a lost grants file leaves it with the owner alone;
  2. its section: 'Clinic'.
Usage: patch_portal_s324.py --file PATH --from MD5 --out PATH
"""
import hashlib
import sys

A1 = '''    {"icon": "\\U0001F9D1\\u200D\\u2695\\uFE0F", "name": "Bhati aaj",'''
A1_NEW = '''    {"icon": "\\U0001F9FE", "name": "OPD & X-ray/Proc Slips",
     # S324 NEW (owner, 19-Sep-2026). The chamber logs every slip's number + clinic ID as it arrives;
     # the room ticks Paid / Done; the night report matches the slips against Docterz, slip order,
     # OPD and X-ray/Proc apart. Its own server unit ('slips'). Granted by name in v20.
     "desc": "Parchi number + clinic ID \\u00b7 room tick",
     "live": True,
     "url": "/finance/slips",
     "roles": ["doctor"]},
''' + A1
A2 = '''    "Petty book": "Money & Accounts", "Bhati aaj": "Clinic",'''
A2_NEW = A2 + '''
    "OPD & X-ray/Proc Slips": "Clinic",'''


def main(argv):
    a = dict(zip(argv[1::2], argv[2::2]))
    raw = open(a["--file"], "rb").read()
    have = hashlib.md5(raw).hexdigest()
    if have != a["--from"]:
        print("REFUSED: portal.py is %s, expected %s" % (have, a["--from"]))
        return 1
    s = raw.decode("utf-8")
    if "OPD & X-ray/Proc Slips" in s:
        print("REFUSED: already carries the tile")
        return 1
    for anc in (A1, A2):
        if s.count(anc) != 1:
            print("REFUSED: anchor x%d: %r" % (s.count(anc), anc[:50]))
            return 1
    s = s.replace(A1, A1_NEW).replace(A2, A2_NEW)
    d = s.encode("utf-8")
    open(a["--out"], "wb").write(d)
    print("patched: %s -> %s" % (have, hashlib.md5(d).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
