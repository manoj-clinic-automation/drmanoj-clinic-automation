#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s457.py -- kit S457_DOCTERZ_SERVER_PATH. ONE anchored edit to /root/finance/finance_app.py (a92baae4, S453):
the two export doors join PUBLIC_PATHS -- the gate lets them reach reception_door.py, and reception_door.py checks a
signature on both. Refuses any file that is not exactly the FROM pin. Prints the result's md5.

    python3 apply_s457.py <path to finance_app.py>
"""
import hashlib
import sys

FROM = "a92baae43afbdd92c36930535418ad58"
OLD = '''                "/finance/api/reception/jobs/read",        # S453
'''
NEW = '''                "/finance/api/reception/jobs/read",        # S453
                "/finance/api/reception/exports/list",     # S457: the owner's PC reads the Docterz exports back; signed
                "/finance/api/reception/exports/get",      # S457
'''


def main(path):
    raw = open(path, "rb").read()
    got = hashlib.md5(raw).hexdigest()
    if got != FROM:
        print("REFUSED: %s is %s, not %s" % (path, got, FROM))
        return 1
    s = raw.decode("utf-8")
    if s.count(OLD) != 1:
        print("REFUSED: the anchor is there %d times, not once" % s.count(OLD))
        return 1
    out = s.replace(OLD, NEW).encode("utf-8")
    with open(path, "wb") as fh:
        fh.write(out)
    print("applied 1 edit -> %s" % hashlib.md5(out).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]) if len(sys.argv) == 2 else 2)
