#!/root/wa/venv/bin/python3
# =============================================================================
#  patch_code_bundle_s347.py  ·  Session 276 (parent)  ·  S347_SPINE_BACKUP  ·  v1
#
#  THE PHARMACY SPINE WENT LIVE ON 20-Sep-2026 (S331, 07:19 IST) AND IS IN NO
#  STORE. /root/finance/spine/ holds seven Python files, two rule files the
#  owner will edit (spine_rules.json, order_rules.json) and the nightly witness
#  spine_compare_latest.txt. The 01:35 code bundle has never looked there: its
#  root/finance entries are NON-recursive by design, so a new sub-folder is
#  invisible until it is named. The Sanjeevni chat named it to the parent at
#  its S274 close; this is that line.
#
#  ONE EDIT: a new SOURCES entry for root/finance/spine -- *.py, *.json, *.txt,
#  non-recursive, so readings/ orders/ expiry/ (data, thousands of small files)
#  are NOT swept into the code bundle. spine.db can never come in here anyway:
#  "*.db*" is a HARD_EXCLUDE. The database and the readings go to the state
#  backup instead (patch_state_backup_s347.py).
#
#  A NEW entry, never an edit to an existing one, so that no file carried today
#  can stop being carried by this change (the file's own S273 precedent).
#
#  Anchored, idempotent, refuses on any anchor that is not found exactly once.
#  FROM is v1.6 (S318); the pin is checked but the anchors decide.
# =============================================================================
import hashlib
import os
import py_compile
import shutil
import sys
import tempfile
import time

TARGET = "/root/state_backup/code_bundle.py"
FROM_MD5 = "598e55a4255fef130366eb3c37d78363"
MARK = "S347, the spine"

EDITS = [
    ('    ("etc/systemd/system",           ("call-*.timer", "staff-*.service",\n'
     '                                      "assetapp.service", "attlistener.service",\n'
     '                                      "attendance-*.service"),                      False, ()),\n'
     ']\n',
     '    ("etc/systemd/system",           ("call-*.timer", "staff-*.service",\n'
     '                                      "assetapp.service", "attlistener.service",\n'
     '                                      "attendance-*.service"),                      False, ()),\n'
     '    # v1.7 (S347, the spine): the pharmacy spine, live since S331 (20-Sep-2026)\n'
     '    # under /root/finance/spine/ and in no store until now -- the root/finance\n'
     '    # entries above are non-recursive by design, so a new sub-folder is\n'
     '    # invisible until it is named. Code, the two rule files the owner edits\n'
     '    # (spine_rules.json, order_rules.json) and the nightly witness text.\n'
     '    # NON-recursive on purpose: readings/ orders/ expiry/ are data and go to\n'
     '    # the state backup; spine.db is walled off by "*.db*" below regardless.\n'
     '    ("root/finance/spine",           ("*.py", "*.json", "*.txt"),                   False, ()),\n'
     ']\n'),
]


def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def apply_to_text(text):
    if MARK in text:
        return text, ["ALREADY -- this file already carries the S347 change"]
    if "S318, the gap" not in text:
        return None, ["this file does not carry the S318 change yet -- install S318 first"]
    msgs = []
    for i, (anchor, repl) in enumerate(EDITS, 1):
        n = text.count(anchor)
        if n != 1:
            return None, ["edit %d: its anchor appears %d time(s), not once -- refusing" % (i, n)]
        text = text.replace(anchor, repl, 1)
        msgs.append("edit %d applied" % i)
    return text, msgs


def main(argv):
    mode = "--check" if "--check" in argv else ("--apply" if "--apply" in argv else "")
    target = TARGET
    for a in argv[1:]:
        if a.startswith("--file="):
            target = a.split("=", 1)[1]
    if not mode:
        print("usage: patch_code_bundle_s347.py --check|--apply [--file=PATH]")
        return 2
    if not os.path.isfile(target):
        print("RESULT REFUSED -- %s is not there" % target)
        return 3
    live = md5_file(target)
    with open(target, "r", encoding="utf-8") as fh:
        text = fh.read()
    print("file   :", target)
    print("md5    :", live, "(expected FROM %s)" % FROM_MD5 if live != FROM_MD5 and MARK not in text else "")
    new, msgs = apply_to_text(text)
    for m in msgs:
        print("       :", m)
    if new is None:
        print("RESULT REFUSED -- nothing changed")
        return 4
    if new == text:
        print("RESULT ALREADY")
        return 0
    if mode == "--check":
        print("RESULT WOULD APPLY -- %d edit(s), no write in --check" % len(EDITS))
        return 0
    if live != FROM_MD5:
        print("note   : live md5 is not the recorded FROM; the anchors matched exactly once each, so the edit is safe")
    stamp = time.strftime("%Y%m%d_%H%M%S")
    bak = "%s.bak_S347_%s" % (target, stamp)
    shutil.copy2(target, bak)
    tmpdir = tempfile.mkdtemp(prefix="s347_")
    tmp = os.path.join(tmpdir, "candidate.py")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(new)
    try:
        py_compile.compile(tmp, cfile=os.path.join(tmpdir, "c.pyc"), doraise=True)
    except py_compile.PyCompileError as ex:
        print("RESULT REFUSED -- the patched text does not compile:", ex)
        shutil.rmtree(tmpdir, ignore_errors=True)
        return 5
    shutil.copystat(target, tmp)
    shutil.move(tmp, target)
    shutil.rmtree(tmpdir, ignore_errors=True)
    print("backup :", bak)
    print("md5 now:", md5_file(target))
    print("RESULT APPLIED")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
