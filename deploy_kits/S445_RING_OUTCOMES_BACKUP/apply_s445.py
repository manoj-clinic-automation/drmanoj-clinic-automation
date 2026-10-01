#!/usr/bin/env python3
"""apply_s445.py -- kit S445_RING_OUTCOMES_BACKUP (session 287, 01-Oct-2026). F-677: /root/portal/ring_outcomes.db
(S419, live since 27-Sep: every ring, who answered, the outcome tapped, the reminder state, the mirror queue) was in
NO store -- not the encrypted nightly (SRC_FILES / SRC_DIRS / SRC_TREES never name /root/portal), not the code bundle
(root/portal takes *.py *.html *.json *.js only), not sheets_pull (only the outcomes that reached the tracker's
Followup_Outcomes tab). D654: it joins the encrypted nightly as a NAMED file, beside console.db -- through the same
sqlite online-backup and integrity check. ONE anchored edit on EXACT bytes: FROM 0e841f35 (S429, live).
usage: apply_s445.py <clinic_state_backup.py>"""
import hashlib
import sys

FROM = "0e841f3569f6e00f92fdc99031ed1242"
TAG = "S445 (F-677)"
OLD = '''    "/root/finance/spine/spine.db",
]
'''
NEW = '''    "/root/finance/spine/spine.db",
    # S445 (F-677), 01-Oct-2026: the ring card's own store (S419, live 27-Sep) -- every ring, who answered,
    # the outcome tapped, the 10-minute reminder state and the tracker-mirror queue. It was in no store at all.
    "/root/portal/ring_outcomes.db",
]
'''


def apply(path):
    raw = open(path, "rb").read()
    s = raw.decode("utf-8")
    if TAG in s:
        return "already"
    if hashlib.md5(raw).hexdigest() != FROM:
        raise SystemExit("REFUSED: clinic_state_backup.py is %s, not the S429 bytes %s" % (hashlib.md5(raw).hexdigest(), FROM))
    if s.count(OLD) != 1:
        raise SystemExit("REFUSED: anchor not found exactly once")
    open(path, "wb").write(s.replace(OLD, NEW).encode("utf-8"))
    return "patched"


if __name__ == "__main__":
    print("clinic_state_backup.py :", apply(sys.argv[1]))
