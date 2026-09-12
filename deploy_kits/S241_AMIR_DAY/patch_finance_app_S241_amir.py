"""
patch_finance_app_S241_amir.py -- mount amir_day on the finance app.

One block, anchored after the LAST '# --- S###_NAME end ---' line that occurs
before the __main__ block, exactly as S240_MARG_DOOR does.  The anchor is
discovered, never named, because the kit that is last on the box changes.

It refuses rather than guesses.  Every refusal leaves the file byte-identical.

Offline:  FA_PATH=./finance_app_copy.py /root/wa/venv/bin/python3 patch_finance_app_S241_amir.py
"""

import hashlib
import io
import os
import re
import shutil
import sys
import time

TARGET = os.environ.get("FA_PATH", "/root/finance/finance_app.py")
MARK = "S241_AMIR_DAY begin"

BLOCK = (
    "\n"
    "# --- S241_AMIR_DAY begin -- Amir's day as seven steps on a phone (D472) ---\n"
    "import amir_day                                               # noqa: E402\n"
    "amir_day.init(app, db, require, unit=os.environ.get(\"AMIR_UNIT\", UNIT))\n"
    "# --- S241_AMIR_DAY end ---\n"
)

END_RE = re.compile(r"^# --- S\d{3}_[A-Z0-9_]+ end ---$", re.M)
MAIN = '\nif __name__ == "__main__":'


def md5_8(b):
    return hashlib.md5(b).hexdigest()[:8]


def refuse(msg):
    print("REFUSING: %s" % msg)
    print("   Nothing was changed.")
    return 2


def main():
    if not os.path.isfile(TARGET):
        return refuse("%s does not exist" % TARGET)

    raw = io.open(TARGET, "rb").read()
    if b"\r\n" in raw:
        return refuse("%s has CRLF line endings; this box's file is LF (F-294)" % TARGET)

    src = raw.decode("utf-8")
    before = md5_8(raw)

    if MARK in src:
        print("ALREADY MOUNTED (%s); pin %s -- nothing to do" % (MARK, before))
        return 0

    m_main = src.find(MAIN)
    if m_main < 0:
        return refuse("no __main__ block found; this is not the app file I expect")

    # The names the mount line uses must exist, exactly once, before the mount.
    for name in ('\ndef require(', '\ndef db('):
        n = src.count(name)
        if n != 1:
            return refuse("%r occurs %d times, expected exactly 1" % (name.strip(), n))
        if src.find(name) > m_main:
            return refuse("%r is defined after __main__; the mount would NameError" % name.strip())
    if not re.search(r"^app\s*=\s*Flask\(", src, re.M):
        return refuse("no 'app = Flask(' line; wrong file")
    if not re.search(r"^UNIT\s*=", src, re.M):
        return refuse("no module-level UNIT; the mount would NameError")
    if not re.search(r"^import os$|^import os\b", src, re.M):
        return refuse("os is not imported at module level; the mount would NameError")

    anchors = [m for m in END_RE.finditer(src) if m.end() < m_main]
    if not anchors:
        return refuse("no '# --- S###_NAME end ---' anchor before __main__")
    a = anchors[-1]
    anchor_line = src[a.start():a.end()]

    for name in ('\ndef require(', '\ndef db('):
        if src.find(name) > a.start():
            return refuse("%r is defined after the anchor; the mount would NameError" % name.strip())

    new = src[:a.end()] + BLOCK + src[a.end():]

    bak = "%s.bak_S241amir_%s" % (TARGET, time.strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(TARGET, bak)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(new)

    try:
        compile(new, TARGET, "exec")
    except SyntaxError as e:
        shutil.copy2(bak, TARGET)
        return refuse("the edit did not compile (%s); the file was put back" % e)

    after = md5_8(io.open(TARGET, "rb").read())
    print("   anchored after : %s" % anchor_line)
    print("   finance_app.py : %s -> %s" % (before, after))
    print("   backup         : %s" % bak)
    return 0


if __name__ == "__main__":
    sys.exit(main())
