#!/root/wa/venv/bin/python3
# =============================================================================
#  patch_state_backup_s347.py  ·  Session 276 (parent)  ·  S347_SPINE_BACKUP  ·  v1
#
#  THE SPINE'S DATA INTO THE 01:50 ENCRYPTED STATE BUNDLE. Two rows, and no
#  change to the mechanism (the owner's S233 instruction: put new sources
#  inside the mechanism that already works and invent no second one):
#
#    SRC_FILES  += /root/finance/spine/spine.db      the spine itself -- goes
#                  through the sqlite ONLINE BACKUP api like every other
#                  database here, integrity-checked first (a failing check is
#                  FATAL 40, the file's own standing rule for every database)
#    SRC_DIRS   += /root/finance/spine/readings      the PHI-free readings the
#                  spine is rebuilt from -- one <md5>.json per Marg export,
#                  append-only (a reading is never removed), which is exactly
#                  what the "vanished source is FATAL 41" rule needs
#
#  WHY readings/ AND NOT the whole spine folder: the store walk takes every
#  data file one level down, and orders/ and expiry/ are nightly OUTPUTS that a
#  later kit may legitimately prune -- a pruned file would read as a vanished
#  source and refuse the whole night's backup. Named narrowly, on purpose.
#  The code and the two rule files ride the 01:35 code bundle (the sister patch).
#
#  Anchored, idempotent, refuses on any anchor that is not found exactly once.
#  FROM is v3 (S233); the pin is checked but the anchors decide.
# =============================================================================
import hashlib
import os
import py_compile
import shutil
import sys
import tempfile
import time

TARGET = "/root/state_backup/clinic_state_backup.py"
FROM_MD5 = "fba579857e731cef2a122d554a232ed6"
MARK = "S347, the spine"

EDITS = [
    # 1 · the database, as a named file
    ('    "/root/staff_master.csv",\n'
     ']\n',
     '    "/root/staff_master.csv",\n'
     '    # v4 (S347, the spine), 20-Sep-2026: the pharmacy spine (S331), rebuilt\n'
     '    # every ten minutes from the readings below and swapped in atomically.\n'
     '    # A database, so it goes through the sqlite online-backup api and the\n'
     '    # integrity check like every other one here. spine.db.tmp / .failed are\n'
     '    # not named and are never taken.\n'
     '    "/root/finance/spine/spine.db",\n'
     ']\n'),
    # 2 · the readings, as a store
    ('    "/root/state_backup/sheets",\n'
     ']\n',
     '    "/root/state_backup/sheets",\n'
     '    # v4 (S347, the spine), 20-Sep-2026: the readings the spine is built\n'
     '    # from -- one PHI-free <md5>.json per Marg export, append-only. Named\n'
     '    # narrowly (not the whole spine folder): orders/ and expiry/ beside it\n'
     '    # are nightly outputs a later kit may prune, and a pruned file would\n'
     '    # read as a vanished source (FATAL 41) and refuse the whole night.\n'
     '    "/root/finance/spine/readings",\n'
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
    if '"/root/state_backup/sheets",' not in text:
        return None, ["this file does not carry the S233 v3 source list -- refusing"]
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
        print("usage: patch_state_backup_s347.py --check|--apply [--file=PATH]")
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
