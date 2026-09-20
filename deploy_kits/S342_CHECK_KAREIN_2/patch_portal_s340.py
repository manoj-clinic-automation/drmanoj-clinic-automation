#!/usr/bin/env python3
"""patch_portal_s340.py -- builds the kit's portal.py from the live one (S340). Two anchored, additive edits:
  1. the NEW tile 'Check karein' (/finance/checks), roles ['doctor'], granted by name to alisha, shivani,
     shavez in tile_grants.json v23; the server's unit 'checks' refuses every other login;
  2. its section: 'Clinic'.
Built from the live bytes (S339 pin b7b0e43c = the bundle's 4085b767 + S339's patch, recomputed).
Usage: patch_portal_s340.py --file PATH --from MD5 --out PATH
"""
import hashlib
import sys

A1 = '''    {"icon": "\\U0001F9D1\\u200D\\u2695\\uFE0F", "name": "Bhati aaj",'''
A1_NEW = '''    {"icon": "\\u2705", "name": "Check karein",
     # S340 NEW (owner, 20-Sep-2026). Reception's one queue for patient records: a blood test with no report,
     # a lab report for an unknown ID, a lab e-mail with no PDF (X-ray and WhatsApp items join later).
     # Its own server unit ('checks'). Granted by name in tile_grants.json v23 to alisha, shivani, shavez.
     "desc": "Records ke sawaal \\u00b7 ek tap",
     "live": True,
     "url": "/finance/checks",
     "roles": ["doctor"]},
''' + A1
A2 = '''    "Patient records": "Clinic",'''
A2_NEW = A2 + '''
    "Check karein": "Clinic",'''


def main(argv):
    a = dict(zip(argv[1::2], argv[2::2]))
    raw = open(a["--file"], "rb").read()
    have = hashlib.md5(raw).hexdigest()
    if have != a["--from"]:
        print("REFUSED: portal.py is %s, expected %s" % (have, a["--from"]))
        return 1
    s = raw.decode("utf-8")
    if '"Check karein"' in s:
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
