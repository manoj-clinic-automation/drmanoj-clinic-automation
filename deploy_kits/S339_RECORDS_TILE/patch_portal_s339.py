#!/usr/bin/env python3
"""patch_portal_s339.py -- builds the kit's portal.py from the live one (S339). Two anchored, additive edits:
  1. the NEW tile 'Patient records' (/finance/records), roles ['doctor'] -- the owner and Dr Bhawna by role;
     granted to nobody by name, and the server's own unit 'records' refuses every other login anyway;
  2. its section: 'Clinic'.
Built from the live bytes (S329 pin 4085b767, read whole from the 20-Sep 01:35 code bundle).
Usage: patch_portal_s339.py --file PATH --from MD5 --out PATH
"""
import hashlib
import sys

A1 = '''    {"icon": "\\U0001F9D1\\u200D\\u2695\\uFE0F", "name": "Bhati aaj",'''
A1_NEW = '''    {"icon": "\\U0001F4C2", "name": "Patient records",
     # S339 NEW (owner, 20-Sep-2026). The 360-degree patient record (S332): patients of the day on top,
     # one click to a patient's visits, X-rays, blood reports from the clinic Drive, Sanjeevni bills,
     # procedures. The doctors only -- its own server unit ('records'); no grant by name.
     "desc": "One patient's whole history \\u00b7 reports from Drive",
     "live": True,
     "url": "/finance/records",
     "roles": ["doctor"]},
''' + A1
A2 = '''    "OPD & X-ray/Proc Slips": "Clinic",'''
A2_NEW = A2 + '''
    "Patient records": "Clinic",'''


def main(argv):
    a = dict(zip(argv[1::2], argv[2::2]))
    raw = open(a["--file"], "rb").read()
    have = hashlib.md5(raw).hexdigest()
    if have != a["--from"]:
        print("REFUSED: portal.py is %s, expected %s" % (have, a["--from"]))
        return 1
    s = raw.decode("utf-8")
    if '"Patient records"' in s:
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
