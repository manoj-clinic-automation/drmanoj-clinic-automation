#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""edits_s620.py -- kit S620 (session S336, 22-Oct-2026): one exact edit on the live /root/finance/setup_notes.py (S617,
290722df).     python3 edits_s620.py LIVE OUT [KIT]

FOUND ON THE LIVE PAGE at 08:00 IST, the morning S617 went in: the Hostinger card's jobs line said "The nightly check has
not reported for over three hours" -- false. The freshness check runs at 08:05 and then hourly 09:35 ... 23:35, so from
23:35 to 08:05 its last run is up to 8 h 30 m old by design. Now the age it is held to follows that schedule: before
08:30 IST up to 9 h 30 m is normal; from 08:30 on, 2 h 30 m (the hourly runs plus a margin).
"""
import hashlib
import sys

EDITS = [
    ('        old = (now - ran).total_seconds() > 3 * 3600\n',
     '        # S620: the check runs 08:05, then hourly 09:35 .. 23:35 -- its night gap (23:35 -> 08:05) is not late\n'
     '        allowed_h = 9.5 if (now.hour, now.minute) < (8, 30) else 2.5\n'
     '        old = (now - ran).total_seconds() > allowed_h * 3600\n'),
]


def main():
    live, out = sys.argv[1], sys.argv[2]
    kit = sys.argv[3] if len(sys.argv) > 3 else None
    s = open(live, encoding="utf-8").read()
    for i, (old, new) in enumerate(EDITS, 1):
        n = s.count(old)
        if n != 1:
            print("  REFUSED: edit %d's anchor occurs %d times (expected 1)" % (i, n))
            return 1
        s = s.replace(old, new)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    a = hashlib.md5(open(out, "rb").read()).hexdigest()
    print("  %d edit applied · rebuilt %s" % (len(EDITS), a[:8]))
    if kit:
        b = hashlib.md5(open(kit, "rb").read()).hexdigest()
        print("  kit %s  %s" % (b[:8], "same" if a == b else "DIFFERENT"))
        return 0 if a == b else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
