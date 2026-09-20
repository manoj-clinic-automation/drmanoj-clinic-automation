#!/usr/bin/env python3
"""patch_finance_app_s332.py -- two anchored, additive edits to /root/finance/finance_app.py (S332).

finance_app.py stays out of the repository (F-185), so it is patched ON THE BOX from its exact live
bytes (the S324 pin 41e0ffb4, read whole from the 20-Sep 01:35 code bundle -- no inferred anchor).
Refuses unless the md5 is FROM and each anchor occurs exactly once; writes --out; prints the new md5.
  1. _unit_for_path(): /finance/records/... belongs to the new unit 'records' (doctors only), so the
     front gate refuses every other login before any route runs.
  2. the guarded mount of records (S209 pattern), just above the __main__ block.
Usage: patch_finance_app_s332.py --file PATH --from MD5 [--out PATH]
"""
import hashlib
import sys

A1 = '''    if path == "/finance/slips" or path.startswith("/finance/slips/"):
        return "slips"       # S324: the OPD & X-ray/Proc slip tile, its own unit (owner, 19-Sep-2026).
'''
A1_NEW = A1 + '''    if path == "/finance/records" or path.startswith("/finance/records/"):
        return "records"     # S332: the 360-degree patient record, the doctors only (owner, 20-Sep-2026).
'''
A2 = '''if __name__ == "__main__":
    if "--selftest" in sys.argv:
'''
A2_NEW = '''# --- S332_RECORDS begin -- the 360-degree patient record, step 1: blood reports (owner, 20-Sep-2026) ---
# Its own unit 'records' (checkers = the doctors, nobody else); its own record_* tables, created on first
# request (F-303). Reads the patient master, Docterz lines, the slip tile and Sanjeevni READ-ONLY; files
# stay in the clinic's Google Drive and are fetched through the box's read-only service account.
# GUARDED (S209): a fault inside it is printed, every other page serves.
try:
    import records                                             # noqa: E402
    records.init(app, db, require, audit, unit="records")
except Exception as _ex_rc:                                    # noqa: BLE001
    print("records NOT mounted: %s" % _ex_rc, file=sys.stderr)
# --- S332_RECORDS end ---


''' + A2


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
    if "S332_RECORDS" in s:
        print("REFUSED: already carries S332")
        return 1
    for anchor in (A1, A2):
        n = s.count(anchor)
        if n != 1:
            print("REFUSED: anchor found %d times (need exactly 1): %r" % (n, anchor[:60]))
            return 1
    s = s.replace(A1, A1_NEW).replace(A2, A2_NEW)
    data = s.encode("utf-8")
    open(out, "wb").write(data)
    print("patched: %s -> %s" % (have, hashlib.md5(data).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
