#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_S655_finance_app.py -- kit S655_LAB_PC_AGENT. TWO anchored edits to the parent's /root/finance/finance_app.py
(FROM f2e86ca7919abc9e660b1bd5e811eebf, the 25-Oct-2026 bundle), built from the LIVE bytes at install time:

  1. PUBLIC_PATHS: the lab doors added after the S457 reception export door -- the login gate lets them reach
     lab_door.py, which authenticates each request itself (an Ed25519 signature), exactly as the reception doors.
  2. The mount: lab_door.init(app, db) in a guarded block after the S449 reception mount (the S209/S425 shape).

    python3 -B make_S655_finance_app.py <live finance_app.py> <output>
Each anchor must occur exactly once, else nothing is written and the exit code is 1.
"""
import hashlib
import io
import sys

FROM = "f2e86ca7919abc9e660b1bd5e811eebf"
src, dst = sys.argv[1], sys.argv[2]
text = io.open(src, "r", encoding="utf-8", newline="").read()
if hashlib.md5(text.encode("utf-8")).hexdigest() != FROM:
    sys.stderr.write("finance_app.py is not at its pin %s -- nothing written\n" % FROM[:8])
    sys.exit(1)

EDITS = [
    ('                "/finance/api/reception/exports/get",      # S457\n',
     '                "/finance/api/reception/exports/get",      # S457\n'
     '                "/finance/api/lab/heartbeat",              # S655: the NK Pathology lab PC\'s doors; lab_door.py verifies the signature on each\n'
     '                "/finance/api/lab/snap/status",            # S655\n'
     '                "/finance/api/lab/snap/part",              # S655\n'
     '                "/finance/api/lab/snap/finish",            # S655\n'
     '                "/finance/api/lab/snap/list",              # S655\n'
     '                "/finance/api/lab/jobs/submit",            # S655: the lab PC\'s job relay, the S453 shape\n'
     '                "/finance/api/lab/jobs/next",              # S655\n'
     '                "/finance/api/lab/jobs/ack",               # S655\n'
     '                "/finance/api/lab/jobs/result",            # S655\n'
     '                "/finance/api/lab/jobs/read",              # S655\n'),
    ('# --- S449_RECEPTION_UPLOAD end ---\n',
     '# --- S449_RECEPTION_UPLOAD end ---\n'
     '# --- S655_LAB_PC_AGENT begin -- the NK Pathology lab PC posts its heartbeat and its Labmate snapshot straight here (D784) ---\n'
     '# The owner, 25-Oct-2026: "plan a direct upload to the server from this PC also". lab_door.py is the NK Pathology\n'
     '# project\'s file, derived from reception_door.py; it keeps /root/labdata/ and touches no table of this app.\n'
     'try:                                                          # guarded, as every later mount (S209)\n'
     '    import lab_door                                               # noqa: E402\n'
     '    lab_door.init(app, db)\n'
     'except Exception as _ex_m:                                    # noqa: BLE001\n'
     '    _MOUNT_FAILED.append((\'lab_door\', repr(_ex_m)[:200]))\n'
     '    print("lab_door NOT mounted: %s" % _ex_m, file=sys.stderr)\n'
     '# --- S655_LAB_PC_AGENT end ---\n'),
]
for old, new in EDITS:
    n = text.count(old)
    if n != 1:
        sys.stderr.write("anchor occurs %d time(s), expected 1:\n%s\n" % (n, old[:120]))
        sys.exit(1)
    text = text.replace(old, new)
io.open(dst, "w", encoding="utf-8", newline="").write(text)
print("finance_app.py: 2 edits, md5 %s" % hashlib.md5(text.encode("utf-8")).hexdigest())
