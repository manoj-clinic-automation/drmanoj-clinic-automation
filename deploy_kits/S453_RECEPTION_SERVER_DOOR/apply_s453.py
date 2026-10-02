#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s453.py -- kit S453_RECEPTION_SERVER_DOOR. ONE anchored edit to /root/finance/finance_app.py (e8dbf77e, S450):
the five paths of the job relay join PUBLIC_PATHS -- the gate lets them reach reception_door.py, and reception_door.py
checks a signature on every one of them. Refuses any file that is not exactly the FROM pin. Prints the result's md5.

    python3 apply_s453.py <path to finance_app.py>
"""
import hashlib
import sys

FROM = "e8dbf77e8a4dbd3dd83486ed6ebf68a5"
OLD = '''                "/finance/api/reception/report",           # S449
'''
NEW = '''                "/finance/api/reception/report",           # S449
                "/finance/api/reception/jobs/submit",      # S453: the job relay; reception_door.py checks a signature on each
                "/finance/api/reception/jobs/next",        # S453
                "/finance/api/reception/jobs/ack",         # S453
                "/finance/api/reception/jobs/result",      # S453
                "/finance/api/reception/jobs/read",        # S453
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
