#!/usr/bin/env python3
"""patch_finance_app_s289.py -- two anchored, additive edits to /root/finance/finance_app.py (S289).

finance_app.py stays out of the repository (F-185), so it is patched ON THE BOX from its exact live
bytes. Refuses unless the file's md5 is FROM; writes the result beside it; prints the new md5.
  1. _unit_for_path(): /finance/petty/... belongs to the new unit 'petty' (the front gate refuses a
     login with no row there before any route runs).
  2. the guarded mount of petty_book (S209 pattern: a fault inside the module is printed and every
     other page keeps serving), placed just above the __main__ block.
Usage: patch_finance_app_s289.py --file PATH --from MD5 [--out PATH]
"""
import hashlib
import sys

A1 = '''    if path == "/finance/physio" or path.startswith("/finance/physio/"):
        return "physio"      # S249: the physiotherapy unit. A login with no row there is refused here.
'''
A1_NEW = A1 + '''    if path == "/finance/petty" or path.startswith("/finance/petty/"):
        return "petty"       # S289: Manoj Bhati's petty book, its own unit (owner, 17-Sep-2026).
'''
A2 = '''if __name__ == "__main__":
    if "--selftest" in sys.argv:
'''
A2_NEW = '''# --- S289_PWA_EXIT_AND_PETTY begin -- Manoj Bhati's petty book (owner, 17-Sep-2026) ---
# Its own unit 'petty' (maker = bhati, checker = the doctors, viewer = reception); its own petty_*
# tables, created on first request (F-303); nothing here reads or writes Sanjeevni or clinic money.
# GUARDED (S209): a fault inside the module is printed and every other page keeps serving.
try:
    import petty_book                                          # noqa: E402
    petty_book.init(app, db, require, audit, unit="petty")
except Exception as _ex_pb:                                    # noqa: BLE001
    print("petty_book NOT mounted: %s" % _ex_pb, file=sys.stderr)
# --- S289_PWA_EXIT_AND_PETTY end ---


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
    for anchor in (A1, A2):
        n = s.count(anchor)
        if n != 1:
            print("REFUSED: anchor found %d times (need exactly 1): %r" % (n, anchor[:60]))
            return 1
    if "S289_PWA_EXIT_AND_PETTY" in s:
        print("REFUSED: already carries S289")
        return 1
    s = s.replace(A1, A1_NEW).replace(A2, A2_NEW)
    data = s.encode("utf-8")
    open(out, "wb").write(data)
    print("patched: %s -> %s" % (have, hashlib.md5(data).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
