#!/usr/bin/env python3
"""patch_finance_app_s290.py -- two anchored, additive edits to /root/finance/finance_app.py (S290).
Patched ON THE BOX from its exact live bytes (F-185). Refuses unless md5 == FROM.
  1. PUBLIC_PATHS gains "/finance/api/bank-sms": the front gate lets the phone's one door through;
     bank_sms.py checks the key itself (the renewals/marg pattern: the handler re-checks).
  2. the guarded mount of bank_sms, just above the __main__ block.
Usage: patch_finance_app_s290.py --file PATH --from MD5 [--out PATH]
"""
import hashlib
import sys

A1 = '''PUBLIC_PATHS = ("/finance/healthz",
'''
A1_NEW = '''PUBLIC_PATHS = ("/finance/healthz",
                "/finance/api/bank-sms",                   # S290: the phone's door; bank_sms.py checks its key
'''
A2 = '''if __name__ == "__main__":
    if "--selftest" in sys.argv:
'''
A2_NEW = '''# --- S290_BANK_SMS begin -- the bank's morning settlement SMS from the owner's phone (17-Sep-2026) ---
# One door (/finance/api/bank-sms, key-checked in the module), one table (bank_sms_settlement), one page
# (/finance/bank-sms, the doctors). Only an ICICI POS settlement credit is ever stored.
# GUARDED (S209): a fault inside the module is printed and every other page keeps serving.
try:
    import bank_sms                                            # noqa: E402
    bank_sms.init(app, db, require, audit)
except Exception as _ex_bs:                                    # noqa: BLE001
    print("bank_sms NOT mounted: %s" % _ex_bs, file=sys.stderr)
# --- S290_BANK_SMS end ---


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
    if "S290_BANK_SMS" in s:
        print("REFUSED: already carries S290")
        return 1
    for anchor in (A1, A2):
        if s.count(anchor) != 1:
            print("REFUSED: anchor found %d times: %r" % (s.count(anchor), anchor[:50]))
            return 1
    data = s.replace(A1, A1_NEW).replace(A2, A2_NEW).encode("utf-8")
    open(out, "wb").write(data)
    print("patched: %s -> %s" % (have, hashlib.md5(data).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
