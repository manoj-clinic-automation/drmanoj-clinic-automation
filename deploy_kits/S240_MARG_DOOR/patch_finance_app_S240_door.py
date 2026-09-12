#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_finance_app_S240_door.py -- S240: mount marg_door inside the finance app.

ONE EDIT, and it refuses rather than guesses.

  * If the mark is already there it changes nothing and says so (so a re-run is safe).
  * The anchor is not hard-coded to a kit that may since have been superseded: it is the LAST
    "# --- S###_<NAME> end ---" line in the mount region, found in the file itself. That is the
    end of the last module mounted, wherever the app has got to. If there is none, it refuses.
  * The names the mount uses -- app, db, require -- must each be defined exactly where expected,
    and BEFORE the anchor, or it refuses: a mount that NameErrors takes the whole app down.
  * CRLF refused (F-294). Backup taken. Compiled after writing; restored on a syntax error.

  /root/wa/venv/bin/python3 -B patch_finance_app_S240_door.py            (on the box)
  FA_PATH=./copy.py python3 -B patch_finance_app_S240_door.py            (offline, for the walk)
"""
import datetime as dt
import hashlib
import io
import os
import re
import shutil
import sys

TARGET = os.environ.get("FA_PATH", "/root/finance/finance_app.py")
MARK = "S240_MARG_DOOR begin"
END_RE = re.compile(r"^# --- S\d{3}_[A-Z0-9_]+ end ---$", re.M)
MAIN = '\nif __name__ == "__main__":'
REQUIRED = ("\ndef require(", "\ndef db(")

BLOCK = '''

# --- S240_MARG_DOOR begin -- hand a Marg export to the server from any browser (D467 phase 2a) ---
# The worst-case route the owner asked for: no medical PC, no Drive, no Tailscale -- a person
# opens /finance/clinic/marg/upload and sends the file. It goes through marg_take.take(), the
# same one door the five-minute collector uses, so it is classified by the same router and
# de-duplicated by the file's own md5. A sale report is read into PHI-free lines and deleted.
import marg_door                                              # noqa: E402
marg_door.init(app, db, require)
# --- S240_MARG_DOOR end ---'''


def main():
    if not os.path.exists(TARGET):
        sys.exit("REFUSING: %s not found" % TARGET)
    raw = io.open(TARGET, "rb").read()
    src = raw.decode("utf-8")
    cur = hashlib.md5(raw).hexdigest()
    if MARK in src:
        print("ALREADY MOUNTED (%s); pin %s -- nothing to do" % (MARK, cur))
        return 0
    if b"\r\n" in raw:
        sys.exit("REFUSING: %s has CRLF line endings; this box's file is LF (F-294)" % TARGET)
    if MAIN not in src:
        sys.exit("REFUSING: no __main__ block -- this does not look like finance_app.py")
    cut = src.index(MAIN)
    for name in REQUIRED:
        if src.count(name) != 1:
            sys.exit("REFUSING: %r occurs %d times, expected exactly 1" % (name.strip(), src.count(name)))
        if src.index(name) > cut:
            sys.exit("REFUSING: %r is defined after __main__" % name.strip())
    if not re.search(r"^app\s*=\s*Flask\(", src, re.M):
        sys.exit("REFUSING: no 'app = Flask(' line -- the mount would have nothing to attach to")
    ends = [m for m in END_RE.finditer(src) if m.end() < cut]
    if not ends:
        sys.exit("REFUSING: no '# --- S###_<NAME> end ---' line before __main__ to chain after. "
                 "Nothing was changed.")
    last = ends[-1]
    anchor = last.group(0)
    for name in ("\ndef require(", "\ndef db("):
        if src.index(name) > last.start():
            sys.exit("REFUSING: %r is defined after the anchor %r; the mount would NameError"
                     % (name.strip(), anchor))
    new = src[:last.end()] + BLOCK + src[last.end():]
    bak = TARGET + ".bak_S240door_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(TARGET, bak)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(new)
    try:
        compile(new, TARGET, "exec")
    except SyntaxError as e:
        shutil.copy2(bak, TARGET)
        sys.exit("REFUSING: syntax error after the edit (%s); %s restored" % (e, TARGET))
    got = hashlib.md5(io.open(TARGET, "rb").read()).hexdigest()
    print("   anchored after : %s" % anchor)
    print("   finance_app.py : %s -> %s" % (cur[:8], got[:8]))
    print("   backup         : %s" % bak)
    return 0


if __name__ == "__main__":
    sys.exit(main())
