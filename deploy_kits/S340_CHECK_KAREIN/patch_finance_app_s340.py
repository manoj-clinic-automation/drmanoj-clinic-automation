#!/usr/bin/env python3
"""patch_finance_app_s340.py -- one anchored, additive edit to /root/finance/finance_app.py (S340).
Built from the exact live bytes (S332 pin 3a871f53 = the 01:35 bundle's 41e0ffb4 + S332's patch, recomputed).
  _unit_for_path(): /finance/checks/... belongs to the new unit 'checks' (reception's "Check karein" queue),
  so the front gate refuses a login with no row there before any route runs. The routes live in records.py,
  already mounted by S332 -- no new mount.
Usage: patch_finance_app_s340.py --file PATH --from MD5 [--out PATH]
"""
import hashlib
import sys

A1 = '''    if path == "/finance/records" or path.startswith("/finance/records/"):
        return "records"     # S332: the 360-degree patient record, the doctors only (owner, 20-Sep-2026).
'''
A1_NEW = A1 + '''    if path == "/finance/checks" or path.startswith("/finance/checks/"):
        return "checks"      # S340: reception's "Check karein" queue for patient records (owner, 20-Sep-2026).
'''


def main(argv):
    args = dict(zip(argv[1::2], argv[2::2]))
    path, want = args.get("--file"), args.get("--from")
    out = args.get("--out", path)
    if not path or not want:
        print(__doc__)
        return 2
    raw = open(path, "rb").read()
    have = hashlib.md5(raw).hexdigest()
    if have != want:
        print("REFUSED: %s is %s, expected %s" % (path, have, want))
        return 1
    s = raw.decode("utf-8")
    if '"/finance/checks"' in s:
        print("REFUSED: already carries S340")
        return 1
    if s.count(A1) != 1:
        print("REFUSED: anchor found %d times (need exactly 1)" % s.count(A1))
        return 1
    data = s.replace(A1, A1_NEW).encode("utf-8")
    open(out, "wb").write(data)
    print("patched: %s -> %s" % (have, hashlib.md5(data).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
