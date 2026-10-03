#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s468.py -- S468_FINANCE_SMALLS (session 292, 03-Oct-2026): three exact insertions, ALL inside selftest().

Built from the real bytes: /root/finance/finance_app.py at 72d25382 (49f52391 with S467 applied).
--selftest uploads made-up bank statements through the real routes, and those routes store the raw file in UPI_DIR /
YESBANK_DIR -- the LIVE upi_statements / yesbank_statements folders. S461 sandboxed the scan folder only. This gives
the run a throwaway folder for each, removed at exit by S461's own cleanup, and puts the two names back at the end.
Nothing outside selftest() changes; no route, no page, no setting. Every anchor must be found exactly once.
   usage: apply_s468.py <finance_app.py>
"""
import hashlib
import sys

FROM = "72d2538222a8fbd6a12d5ac2434c5a4e"

EDITS = [
    ('''    global DB_PATH, ALLOW_HEADER_AUTH, LEDGER_JSONL, SCAN_DIR     # S461: + SCAN_DIR\n''',
     '''    global DB_PATH, ALLOW_HEADER_AUTH, LEDGER_JSONL, SCAN_DIR     # S461: + SCAN_DIR
    global UPI_DIR, YESBANK_DIR                                   # S468\n'''),
    ('''    atexit.register(_s461_selftest_cleanup, _s461_made)\n''',
     '''    atexit.register(_s461_selftest_cleanup, _s461_made)
    # S468: the made-up bank statements this run uploads were stored in the LIVE upi_statements and
    # yesbank_statements folders (S461 sandboxed the scans only). Both stores are throwaway folders for the run.
    _s468_dirs_prev = (UPI_DIR, YESBANK_DIR)
    UPI_DIR = tempfile.mkdtemp(prefix="smoke_upi_")
    YESBANK_DIR = tempfile.mkdtemp(prefix="smoke_yesbank_")
    _s461_made.extend([UPI_DIR, YESBANK_DIR])\n'''),
    ('''    SCAN_DIR = _s461_scan_prev                                    # S461\n''',
     '''    SCAN_DIR = _s461_scan_prev                                    # S461
    UPI_DIR, YESBANK_DIR = _s468_dirs_prev                        # S468\n'''),
]


def apply(src):
    for n, (old, new) in enumerate(EDITS, 1):
        got = src.count(old)
        if got != 1:
            raise SystemExit("!! anchor %d was found %d time(s), expected 1 - nothing written" % (n, got))
        src = src.replace(old, new)
    return src


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_s468.py <path to finance_app.py>")
    path = sys.argv[1]
    raw = open(path, "rb").read()
    have = hashlib.md5(raw).hexdigest()
    if have != FROM:
        raise SystemExit("!! %s is %s, not %s - nothing written" % (path, have, FROM))
    out = apply(raw.decode("utf-8")).encode("utf-8")
    compile(out, path, "exec")
    with open(path, "wb") as fh:
        fh.write(out)
    print("finance_app.py %s -> %s (%d insertions; %+d bytes)" % (have[:8], hashlib.md5(out).hexdigest()[:8], len(EDITS), len(out) - len(raw)))


if __name__ == "__main__":
    main()
