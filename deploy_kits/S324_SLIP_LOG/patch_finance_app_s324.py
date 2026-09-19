#!/usr/bin/env python3
"""patch_finance_app_s324.py -- two anchored, additive edits to /root/finance/finance_app.py (S324).

finance_app.py stays out of the repository (F-185), so it is patched ON THE BOX from its exact live
bytes. Refuses unless the file's md5 is FROM and each anchor occurs exactly once; writes the result
to --out; prints the new md5.
  1. _unit_for_path(): /finance/slips/... belongs to the new unit 'slips' (the front gate refuses a
     login with no row there before any route runs).
  2. the guarded mount of slip_log (S209 pattern), placed just above the __main__ block.
Usage: patch_finance_app_s324.py --file PATH --from MD5 [--out PATH]
"""
import hashlib
import sys

A1 = '''    if path == "/finance/petty" or path.startswith("/finance/petty/"):
        return "petty"       # S289: Manoj Bhati's petty book, its own unit (owner, 17-Sep-2026).
'''
A1_NEW = A1 + '''    if path == "/finance/slips" or path.startswith("/finance/slips/"):
        return "slips"       # S324: the OPD & X-ray/Proc slip tile, its own unit (owner, 19-Sep-2026).
'''
A2 = '''if __name__ == "__main__":
    if "--selftest" in sys.argv:
'''
A2_NEW = '''# --- S324_SLIP_LOG begin -- the OPD & X-ray/Proc slip tile and its night report (owner, 19-Sep-2026) ---
# Its own unit 'slips' (makers = the chamber assistants and the room; checkers = the doctors); its own
# slip_* tables, created on first request (F-303). Reads Docterz lines, the patient master and the
# owner's rate page READ-ONLY. GUARDED (S209): a fault inside it is printed, every other page serves.
try:
    import slip_log                                            # noqa: E402
    slip_log.init(app, db, require, audit, unit="slips")
except Exception as _ex_sl:                                    # noqa: BLE001
    print("slip_log NOT mounted: %s" % _ex_sl, file=sys.stderr)
# --- S324_SLIP_LOG end ---


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
    if "S324_SLIP_LOG" in s:
        print("REFUSED: already carries S324")
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
