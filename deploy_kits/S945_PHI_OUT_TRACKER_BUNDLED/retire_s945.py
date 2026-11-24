#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""retire_s945.py -- kit S945 (roadmap S510 A3, F-1631): the three leftovers of the 2026-07 referee work leave the live code folder
/root/wa/recordings-archive/ for /root/_retired/S510/ (a folder the nightly code bundle never enters, EXCLUDE_DIRS '_retired'):
  make_force_keys.py                            moved; its TRIPLES list (41 patient numbers) REPLACED by '# removed S510 (F-1631)'
  force_keys.txt                                moved as it is (its output: join keys), if present
  call_verdict_BACKUP_S123_pre_join_redesign.py moved as it is (dead code; its figures are selftest fixtures)
Nothing imports them: verdict_review.py reads force_keys.txt only when the file exists (then prints 'Force file: ...'); the
night's verdict stage does not read it. Runs on the box by the installer:  --check (counts only) | --apply | --undo
Nothing printed ever carries a number: counts only.
"""
import os
import re
import shutil
import sys

RA = os.environ.get("RA", "/root/wa/recordings-archive")
RET = os.environ.get("RET", "/root/_retired/S510")
FILES = ["make_force_keys.py", "force_keys.txt", "call_verdict_BACKUP_S123_pre_join_redesign.py"]
TEN = re.compile(r"(?<!\d)[6-9]\d{9}(?!\d)")        # an Indian mobile's shape; a unix stamp is not counted
TRIPLES_RE = re.compile(r"^TRIPLES = \[\n.*?^\][ \t]*(?:#[^\n]*)?(?:\n|\Z)", re.M | re.S)


def runs(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return len(TEN.findall(fh.read()))
    except OSError:
        return 0


def folder_runs(folder):
    n = 0
    for name in sorted(os.listdir(folder)):
        p = os.path.join(folder, name)
        if os.path.isfile(p) and name.endswith((".py", ".txt", ".sh", ".json")):
            n += runs(p)
    return n


def check():
    present = [f for f in FILES if os.path.exists(os.path.join(RA, f))]
    retired = [f for f in FILES if os.path.exists(os.path.join(RET, f))]
    print("CHECK live-folder ten-digit runs %d; leftovers in the live folder %d of 3; retired %d of 3"
          % (folder_runs(RA), len(present), len(retired)))
    return 0


def apply():
    os.makedirs(RET, mode=0o700, exist_ok=True)
    os.chmod(RET, 0o700)
    # validate everything first -- nothing moves until every move is known to be possible
    plan = []
    for f in FILES:
        src, dst = os.path.join(RA, f), os.path.join(RET, f)
        if not os.path.exists(src):
            continue
        if os.path.exists(dst):
            print("APPLY STOP: %s already in the retired folder (nothing moved)" % f)
            return 1
        new = None
        if f == "make_force_keys.py":
            text = open(src, encoding="utf-8").read()
            new, n = TRIPLES_RE.subn("TRIPLES = []   # removed S510 (F-1631): the 41 referee numbers left this file at S945\n", text)
            if n != 1:
                print("APPLY STOP: the TRIPLES list was not found exactly once in make_force_keys.py (nothing moved)")
                return 1
        plan.append((src, dst, new))
    moved = 0
    for src, dst, new in plan:
        if new is not None:
            with open(dst, "w", encoding="utf-8") as fh:
                fh.write(new)
            os.chmod(dst, 0o600)
            os.remove(src)
        else:
            shutil.move(src, dst)
            os.chmod(dst, 0o600)
        moved += 1
    left = folder_runs(RA)
    print("APPLY moved %d; live-folder ten-digit runs now %d; the retired make_force_keys.py carries %d"
          % (moved, left, runs(os.path.join(RET, "make_force_keys.py"))))
    return 0


def undo():
    back = 0
    for f in FILES:
        src, dst = os.path.join(RET, f), os.path.join(RA, f)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.move(src, dst)
            back += 1
    print("UNDO moved back %d (make_force_keys.py comes back WITHOUT its 41 numbers -- they are not recoverable from the box, by design)" % back)
    return 0


def selftest():
    import tempfile
    d = tempfile.mkdtemp(prefix="s945_")
    ra, ret = os.path.join(d, "ra"), os.path.join(d, "ret")
    os.makedirs(ra)
    G = 10 ** 9
    body = ('#!/usr/bin/env python3\nX = 1\nTRIPLES = [\n    ("%d", "2026-07-01", "10:00"),\n    ("%d", "2026-07-02", "11:00"),\n]\n'
            'def f():\n    return TRIPLES\n' % (9 * G + 1234, 9 * G + 5678))
    open(os.path.join(ra, "make_force_keys.py"), "w").write(body)
    open(os.path.join(ra, "force_keys.txt"), "w").write("%d_%d\n" % (9 * G + 1234, 175 * 10 ** 7 + 1871234))
    open(os.path.join(ra, "call_verdict_BACKUP_S123_pre_join_redesign.py"), "w").write("y = 2\n")
    open(os.path.join(ra, "call_verdict.py"), "w").write("z = 3\n")
    global RA, RET
    RA, RET = ra, ret
    n = f = 0

    def ok(name, cond):
        nonlocal n, f
        n += 1
        print(("  ok   " if cond else "  FAIL ") + name)
        if not cond:
            f += 1
    ok("before: 3 ten-digit runs in the live folder", folder_runs(ra) == 3)
    ok("apply returns 0", apply() == 0)
    ok("after: 0 runs in the live folder; the 3 files gone; call_verdict.py untouched",
       folder_runs(ra) == 0 and not any(os.path.exists(os.path.join(ra, x)) for x in FILES) and os.path.exists(os.path.join(ra, "call_verdict.py")))
    kept = open(os.path.join(ret, "make_force_keys.py")).read()
    ok("the retired make_force_keys.py has an empty TRIPLES and no number, still compiles",
       "TRIPLES = []" in kept and runs(os.path.join(ret, "make_force_keys.py")) == 0 and "def f():" in kept and compile(kept, "x", "exec"))
    ok("the retired folder is 0700, files 0600", (os.stat(ret).st_mode & 0o777) == 0o700 and (os.stat(os.path.join(ret, "force_keys.txt")).st_mode & 0o777) == 0o600)
    ok("apply again: nothing to move, 0", apply() == 0)
    open(os.path.join(ra, "force_keys.txt"), "w").write("x\n")
    open(os.path.join(ra, "make_force_keys.py"), "w").write(body.replace("]\n", "]  # end\n"))
    ok("a file both live and retired: STOP, and the other live file NOT moved", apply() == 1 and os.path.exists(os.path.join(ra, "make_force_keys.py")))
    os.remove(os.path.join(ra, "force_keys.txt"))
    os.remove(os.path.join(ra, "make_force_keys.py"))
    ok("a ']' with a trailing comment still matches", TRIPLES_RE.subn("T", body.replace("]\n", "]  # end\n"))[1] == 1)
    ok("a ']' at the end of the file with no newline still matches", TRIPLES_RE.subn("T", body.split("def f")[0].rstrip("\n"))[1] == 1)
    ok("undo brings the 3 back, numbers gone from the script", undo() == 0 and all(os.path.exists(os.path.join(ra, x)) for x in FILES) and folder_runs(ra) == 1)
    shutil.rmtree(d, ignore_errors=True)
    print("SELFTEST %d/%d" % (n - f, n))
    return 1 if f else 0


if __name__ == "__main__":
    a = sys.argv[1:2]
    sys.exit({"--check": check, "--apply": apply, "--undo": undo, "--selftest": selftest}.get(a[0] if a else "", lambda: print(__doc__) or 2)())
