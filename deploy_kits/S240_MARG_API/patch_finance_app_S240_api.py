#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_finance_app_S240_api.py -- S240 phase 2b: let the medical PC's key open ONE more path.

The app's front gate (S187_M1a) lets the pharmacy key through for a named handful of paths and
nothing else:

    if MARG_TOKEN and p in ("/finance/api/marg-push",
                            "/finance/api/pipeline-status") \\
            and request.headers.get("X-Finance-Marg") == MARG_TOKEN:
        return None

This adds "/finance/api/marg-file" to that tuple -- ONE line, inserted straight after the first
entry, indented to the same column as the entries already there (read from the file, not assumed).
Nothing else changes: no new secret, no new gate, no role, no other route. The handler re-checks
the key itself, as the others do.

It refuses rather than guesses: the opening line must occur EXACTLY ONCE, the path must not
already be there, the file must be LF, and it must still compile after the edit or the backup is
restored.

    /root/wa/venv/bin/python3 -B patch_finance_app_S240_api.py          (on the box)
    FA_PATH=./copy.py python3 -B patch_finance_app_S240_api.py          (offline, for the walk)
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

TARGET = os.environ.get("FA_PATH", "/root/finance/finance_app.py")
OPEN_LINE = 'if MARG_TOKEN and p in ("/finance/api/marg-push",'
NEW_PATH = '"/finance/api/marg-file",'


def main():
    if not os.path.exists(TARGET):
        sys.exit("REFUSING: %s not found" % TARGET)
    raw = io.open(TARGET, "rb").read()
    src = raw.decode("utf-8")
    cur = hashlib.md5(raw).hexdigest()
    if NEW_PATH in src:
        print("ALREADY OPEN (%s is in the gate); pin %s -- nothing to do" % (NEW_PATH, cur))
        return 0
    if b"\r\n" in raw:
        sys.exit("REFUSING: %s has CRLF line endings; this box's file is LF (F-294)" % TARGET)
    if src.count(OPEN_LINE) != 1:
        sys.exit("REFUSING: %r occurs %d times, expected exactly 1 -- the gate is not the shape "
                 "this patch knows. Nothing was changed." % (OPEN_LINE, src.count(OPEN_LINE)))
    i = src.index(OPEN_LINE)
    line_start = src.rfind("\n", 0, i) + 1
    eol = src.index("\n", i)
    col = i - line_start + OPEN_LINE.index("(") + 1          # line up under the first entry
    new = src[:eol + 1] + (" " * col) + NEW_PATH + "\n" + src[eol + 1:]
    bak = TARGET + ".bak_S240api_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(TARGET, bak)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(new)
    try:
        compile(new, TARGET, "exec")
    except SyntaxError as e:
        shutil.copy2(bak, TARGET)
        sys.exit("REFUSING: syntax error after the edit (%s); %s restored" % (e, TARGET))
    got = hashlib.md5(io.open(TARGET, "rb").read()).hexdigest()
    print("   the gate now also opens for: %s" % NEW_PATH.strip('",'))
    print("   finance_app.py : %s -> %s" % (cur[:8], got[:8]))
    print("   backup         : %s" % bak)
    return 0


if __name__ == "__main__":
    sys.exit(main())
