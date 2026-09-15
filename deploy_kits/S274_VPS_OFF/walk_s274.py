#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s274.py -- the LIVE-SHAPE walk for S274, the VPS off switches.

It works on COPIES of the four live files, patches them with the kit's own
patcher, and then asserts what the kit CLAIMS -- that each job stops when its
marker is there and runs when it is not. It creates markers under
/root/finance/_off and removes exactly the ones it created; it opens no
database and runs no job to completion.

A check that cannot run says SKIPPED and is never counted as a pass (F-443).

  python3 walk_s274.py --src /root/finance --patcher patch_off_switches_s274.py
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

FILES = {
    "spine_cadence.py":    ("SPINE_OFF", "spine_cadence", ["--db", "/nonexistent.db"]),
    "sale_attribution.py": ("ATTRIBUTION_OFF", "sale_attribution", ["--db", "/nonexistent.db", "--report"]),
    "export_watch.py":     ("EXPORT_WATCH_OFF", "export_watch", ["--day", "today", "--db", "/nonexistent.db"]),
    "salts_refresh.py":    ("SALTS_REFRESH_OFF", "salts_refresh", ["--dry-run"]),
}
OFF_DIR = "/root/finance/_off"

PASS, FAIL, SKIP = [], [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name if cond else "%s  %s" % (name, detail))
    print(("  ok    " if cond else "  FAIL  ") + name + ("" if cond else "   " + detail))


def skip(name, why):
    SKIP.append("%s (%s)" % (name, why))
    print("  skip  %s  -- %s  [NOT a pass]" % (name, why))


def run(path, args, cwd):
    p = subprocess.run([sys.executable, path] + args, capture_output=True,
                       text=True, cwd=cwd, timeout=120)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def marker(name):
    if not os.path.isdir(OFF_DIR):
        os.makedirs(OFF_DIR)
    p = os.path.join(OFF_DIR, name)
    with open(p, "w") as fh:
        fh.write("walk_s274\n")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="folder holding the four LIVE files")
    ap.add_argument("--patcher", required=True)
    a = ap.parse_args()

    box = tempfile.mkdtemp(prefix="s274_walk_")
    made = []
    try:
        # copy the whole source folder so imports beside the files still resolve
        work = os.path.join(box, "finance")
        shutil.copytree(a.src, work, symlinks=True,
                        ignore=shutil.ignore_patterns("*.db", "*.db-*", "_off", "logs",
                                                      "*.log", "__pycache__", "*.bak_*"))

        print("\n--- 0 · the selftests BEFORE the patch ---")
        before = {}
        for name in ("sale_attribution.py", "export_watch.py", "spine_cadence.py"):
            rc, out = run(os.path.join(work, name), ["--selftest"], work)
            before[name] = out.strip().splitlines()[-1] if out.strip() else ""
            if "selftest:" in before[name]:
                print("      %-22s %s" % (name, before[name]))
            else:
                print("      %-22s (could not run here)" % name)

        print("\n--- 1 · the patcher ---")
        rc, out = run(a.patcher, ["--dir", work], box)
        print("".join("      %s\n" % l for l in out.strip().splitlines()))
        check("the patcher reports success", rc == 0, "rc=%d" % rc)

        print("\n--- 2 · every patched file still compiles ---")
        for name in FILES:
            rc, out = run("-", [], work) if False else (0, "")
            p = subprocess.run([sys.executable, "-m", "py_compile", os.path.join(work, name)],
                               capture_output=True, text=True)
            check("compiles: %s" % name, p.returncode == 0, p.stderr.strip()[:120])

        print("\n--- 3 · the selftests AFTER the patch say exactly what they said before ---")
        for name in ("sale_attribution.py", "export_watch.py", "spine_cadence.py"):
            rc, out = run(os.path.join(work, name), ["--selftest"], work)
            now = out.strip().splitlines()[-1] if out.strip() else ""
            if "selftest:" not in before.get(name, ""):
                skip("%s selftest unchanged" % name,
                     "its selftest cannot run outside the box (missing import)")
                continue
            check("%s selftest unchanged: %s" % (name, now), now == before[name],
                  "was %r now %r" % (before[name], now))
            check("%s selftest still reports 0 failures" % name, "0 failures" in now, now)

        print("\n--- 4 · its OWN marker stops each job ---")
        for name, (own, label, args) in sorted(FILES.items()):
            made.append(marker(own))
            rc, out = run(os.path.join(work, name), args, work)
            check("%s stops on %s" % (name, own),
                  rc == 0 and ("%s: switched off" % label) in out,
                  "rc=%d out=%r" % (rc, out.strip()[:160]))
            os.remove(made.pop())

        print("\n--- 5 · a .txt marker is honoured too ---")
        for name, (own, label, args) in sorted(FILES.items()):
            made.append(marker(own + ".txt"))
            rc, out = run(os.path.join(work, name), args, work)
            check("%s stops on %s.txt" % (name, own),
                  rc == 0 and ("%s: switched off" % label) in out,
                  "rc=%d" % rc)
            os.remove(made.pop())

        print("\n--- 6 · ALL_OFF stops all four ---")
        made.append(marker("ALL_OFF"))
        for name, (own, label, args) in sorted(FILES.items()):
            rc, out = run(os.path.join(work, name), args, work)
            check("%s stops on ALL_OFF" % name,
                  rc == 0 and ("%s: switched off" % label) in out, "rc=%d" % rc)
        os.remove(made.pop())

        print("\n--- 7 · with no marker, the guard does NOT stop the job ---")
        for name, (own, label, args) in sorted(FILES.items()):
            rc, out = run(os.path.join(work, name), args, work)
            check("%s runs past the guard when no marker is there" % name,
                  ("%s: switched off" % label) not in out,
                  "out=%r" % out.strip()[:160])

        print("\n--- 8 · one job's marker does not stop another ---")
        made.append(marker("SPINE_OFF"))
        rc, out = run(os.path.join(work, "export_watch.py"), FILES["export_watch.py"][2], work)
        check("SPINE_OFF does not stop export_watch",
              "export_watch: switched off" not in out, out.strip()[:120])
        os.remove(made.pop())

        print("\n--- 9 · nothing else in the four files changed ---")
        for name in FILES:
            src = os.path.join(a.src, name)
            cur = os.path.join(work, name)
            import difflib, io
            o = io.open(src, encoding="utf-8").read().splitlines()
            n = io.open(cur, encoding="utf-8").read().splitlines()
            added = [l for l in difflib.unified_diff(o, n, lineterm="", n=0)
                     if l.startswith("+") and not l.startswith("+++")]
            removed = [l for l in difflib.unified_diff(o, n, lineterm="", n=0)
                       if l.startswith("-") and not l.startswith("---")]
            check("%s: no line removed or altered, only added" % name, not removed,
                  "removed %d: %s" % (len(removed), removed[:3]))
            print("        (+%d lines)" % len(added))

    finally:
        for p in made:
            try:
                os.remove(p)
            except OSError:
                pass
        try:
            if os.path.isdir(OFF_DIR) and not os.listdir(OFF_DIR):
                os.rmdir(OFF_DIR)
        except OSError:
            pass
        shutil.rmtree(box, ignore_errors=True)

    print("\n" + "-" * 66)
    print("  passed %d   failed %d   skipped %d" % (len(PASS), len(FAIL), len(SKIP)))
    for s in SKIP:
        print("  SKIPPED (not a pass): %s" % s)
    for f in FAIL:
        print("  FAILED: %s" % f)
    print("-" * 66)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
