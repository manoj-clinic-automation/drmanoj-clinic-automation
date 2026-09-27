#!/usr/bin/env python3
"""apply_s429.py -- kit S429_MONTHLY_PIN_GUARD (session 284, 27-Sep-2026). F-649: the monthly slot's description
'month=YYYY-MM' was written even when the keep-forever pin failed (or no revision was listed), so the month counted
as DONE and the next night never retried -- a month could pass with no pinned copy. Now the description is written
ONLY when the pin is confirmed; otherwise the log says the month stays open and the next night tries again.
ONE anchored edit on EXACT bytes: FROM ede26d98 (S424, live). usage: apply_s429.py <clinic_state_backup.py>"""
import hashlib
import sys

FROM = "ede26d98a6aaf36188a797d732f4a4d7"
TAG = "S429 (F-649)"
OLD = '''                d.patch_meta(monthly["id"],
                             {"description": "month=%s · %s" % (mtag, desc)})
'''
NEW = '''                if monthly_done:                                  # S429 (F-649): only a CONFIRMED pin closes the month
                    d.patch_meta(monthly["id"],
                                 {"description": "month=%s · %s" % (mtag, desc)})
                else:
                    log("WARNING: monthly copy for", mtag, "NOT pinned -- the month stays open;"
                        " the next night ships and pins it again")
'''


def apply(path):
    raw = open(path, "rb").read()
    s = raw.decode("utf-8")
    if TAG in s:
        return "already"
    if hashlib.md5(raw).hexdigest() != FROM:
        raise SystemExit("REFUSED: clinic_state_backup.py is %s, not the S424 bytes %s" % (hashlib.md5(raw).hexdigest(), FROM))
    if s.count(OLD) != 1:
        raise SystemExit("REFUSED: anchor not found exactly once")
    open(path, "wb").write(s.replace(OLD, NEW).encode("utf-8"))
    return "patched"


if __name__ == "__main__":
    print("clinic_state_backup.py :", apply(sys.argv[1]))
