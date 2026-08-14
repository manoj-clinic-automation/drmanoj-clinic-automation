#!/usr/bin/env python3
"""prune_backups.py — tidy accumulated backup files on the VPS.

Clinic-automation housekeeping tool (S177, item 4). It sweeps the *backup*
copies that pile up next to live files during installs -- names ending in
`.bak`, `.bak.<timestamp>`, `.new`, or `.old` -- and removes the stale ones,
while ALWAYS keeping a few recent rollback points.

SAFE BY CONSTRUCTION
--------------------
1. Dry-run is the DEFAULT. Nothing is deleted unless you pass --apply.
2. It only ever considers files whose name matches a backup marker
   (`.bak` / `.bak.<...>` / `.new` / `.old`). A live source file such as
   `asset_register.py` never matches, so it can never be selected. `.backup`
   is deliberately NOT matched (only exact `.bak`).
3. It never recurses (top level of each directory only), never follows
   symlinks, and never touches anything that is not a regular file.
4. Per live file it KEEPS the newest N backups (default 2), and among the
   rest only deletes those older than the age gate (default 14 days). A fresh
   rollback point is therefore safe even if you already have N of them.

USAGE
-----
  python3 prune_backups.py                      # dry-run on the current dir
  python3 prune_backups.py /root/assetapp /root/portal /root/wa
  python3 prune_backups.py /root/assetapp --apply         # actually delete
  python3 prune_backups.py /root/assetapp --keep 3 --age-days 30 --apply
  python3 prune_backups.py --selftest           # prove the logic (no real files)

On --apply, every deletion is appended to `<dir>/prune_backups.log`.
"""
import argparse
import os
import re
import sys
import time

BAK_MARK = re.compile(r"\.bak(\.|$)", re.I)   # matches .bak  and  .bak.<timestamp>
LOG_NAME = "prune_backups.log"


def backup_stem(name):
    """Return the live-file stem a backup name belongs to, or None if `name`
    is not a backup file. e.g. 'asset_register.py.bak.2026-08-14_1030' ->
    'asset_register.py'; 'smoke_test.py.new' -> 'smoke_test.py'."""
    m = BAK_MARK.search(name)
    if m:
        return name[:m.start()]
    low = name.lower()
    if low.endswith(".new"):
        return name[:-4]
    if low.endswith(".old"):
        return name[:-4]
    return None


def scan_dir(d):
    """Yield (path, stem, mtime, size) for every backup file directly in `d`.
    Skips symlinks, directories, and the tool's own log."""
    try:
        entries = list(os.scandir(d))
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        return
    for e in entries:
        if e.name == LOG_NAME:
            continue
        if e.is_symlink() or not e.is_file():
            continue
        stem = backup_stem(e.name)
        if stem is None:
            continue
        try:
            st = e.stat()
        except OSError:
            continue
        yield (e.path, stem, st.st_mtime, st.st_size)


def plan_dir(d, keep, age_days, now):
    """Decide, for one directory, which backups to delete vs keep. Returns
    (to_delete, kept) lists of (path, mtime, size). Pure -- no filesystem
    writes -- so the self-test can assert on it."""
    groups = {}
    for path, stem, mtime, size in scan_dir(d):
        groups.setdefault(stem, []).append((path, mtime, size))
    to_delete, kept = [], []
    age_cut = age_days * 86400
    for stem, members in groups.items():
        members.sort(key=lambda t: t[1], reverse=True)   # newest first
        for i, (path, mtime, size) in enumerate(members):
            recent_enough = i < keep                     # among the newest N
            young = (now - mtime) < age_cut              # newer than age gate
            if recent_enough or young:
                kept.append((path, mtime, size))
            else:
                to_delete.append((path, mtime, size))
    to_delete.sort(key=lambda t: t[0])
    kept.sort(key=lambda t: t[0])
    return to_delete, kept


def _fmt_age(secs):
    days = secs / 86400.0
    if days >= 1:
        return "%.0fd" % days
    return "%.0fh" % (secs / 3600.0)


def _fmt_size(n):
    for unit in ("B", "K", "M", "G"):
        if n < 1024 or unit == "G":
            return "%.0f%s" % (n, unit)
        n /= 1024.0


def run(dirs, keep, age_days, apply, quiet, now=None):
    now = now if now is not None else time.time()
    total_del = total_bytes = 0
    for d in dirs:
        to_delete, kept = plan_dir(d, keep, age_days, now)
        if not quiet:
            print("\n%s  (keep newest %d, delete older than %dd)" % (d, keep, age_days))
            if not to_delete and not kept:
                print("  no backup files here.")
            elif not to_delete:
                print("  %d backup(s) present; nothing old enough to prune." % len(kept))
        logf = None
        for path, mtime, size in to_delete:
            total_del += 1
            total_bytes += size
            line = "%s  %6s  age %-5s  %s" % (
                "DELETE" if apply else "would delete",
                _fmt_size(size), _fmt_age(now - mtime), path)
            if not quiet:
                print("  " + line)
            if apply:
                try:
                    os.remove(path)
                    if logf is None:
                        logf = open(os.path.join(d, LOG_NAME), "a")
                    logf.write("%s  removed  %s  (%s, age %s)\n" % (
                        time.strftime("%Y-%m-%d %H:%M:%S"), path,
                        _fmt_size(size), _fmt_age(now - mtime)))
                except OSError as ex:
                    print("  !! could not delete %s: %s" % (path, ex))
        if logf:
            logf.close()
    verb = "Deleted" if apply else "Would delete"
    print("\n%s %d backup file(s), freeing ~%s.%s" % (
        verb, total_del, _fmt_size(total_bytes),
        "" if apply else "  (dry-run -- re-run with --apply to remove them.)"))
    return total_del


# ----------------------------------------------------------------- self-test
def selftest():
    import tempfile, shutil
    ok = bad = 0

    def chk(name, cond):
        nonlocal ok, bad
        if cond:
            ok += 1; print("  PASS  " + name)
        else:
            bad += 1; print("  FAIL  " + name)

    tmp = tempfile.mkdtemp(prefix="prune_selftest_")
    try:
        now = time.time()
        DAY = 86400

        def mk(name, age_days):
            p = os.path.join(tmp, name)
            open(p, "w").write("x")
            t = now - age_days * DAY
            os.utime(p, (t, t))
            return p

        # a live source file (must NEVER be selected) + a real .backup (not .bak)
        live = mk("asset_register.py", 40)
        realbackup = mk("data.backup", 40)          # .backup != .bak
        # four backups of asset_register.py at increasing age
        b_new0 = mk("asset_register.py.bak.2026-08-14_1030", 0)   # fresh
        b_new1 = mk("asset_register.py.new", 1)                   # newish
        b_old1 = mk("asset_register.py.bak", 20)                  # old
        b_old2 = mk("asset_register.py.bak.2026-01-01_0000", 60)  # very old
        # a lone .old backup of another file: old, but the ONLY rollback point
        lone = mk("portal.py.old", 90)

        dele, kept = plan_dir(tmp, keep=2, age_days=14, now=now)
        dset = {p for p, _, _ in dele}
        kset = {p for p, _, _ in kept}

        chk("live source file never selected", live not in dset and live not in kset)
        chk("'.backup' is not treated as a backup", realbackup not in dset and realbackup not in kset)
        chk("backup_stem groups the 4 asset_register copies under one stem",
            {backup_stem(os.path.basename(p)) for p in (b_new0, b_new1, b_old1, b_old2)}
            == {"asset_register.py"})
        chk("keeps the two newest backups (keep=2)", b_new0 in kset and b_new1 in kset)
        chk("deletes older-than-gate beyond the newest N", b_old1 in dset and b_old2 in dset)
        chk("a lone backup is kept (only rollback point, within keep=2)", lone in kset and lone not in dset)

        # keep=1 => only the single newest survives; the 1d copy is still kept by the age gate
        d2set = {p for p, _, _ in plan_dir(tmp, keep=1, age_days=14, now=now)[0]}
        chk("keep=1 still keeps the newest backup", b_new0 not in d2set)
        chk("keep=1 keeps a young (1d) copy via the age gate", b_new1 not in d2set)
        chk("keep=1 deletes the old copies", b_old1 in d2set and b_old2 in d2set)

        # age gate protects a fresh 3rd copy even beyond keep-N
        b_fresh_extra = mk("asset_register.py.bak.fresh", 2)   # 3rd-newest, but only 2d old
        k3set = {p for p, _, _ in plan_dir(tmp, keep=2, age_days=14, now=now)[1]}
        chk("age gate keeps a fresh 3rd copy (<14d) despite keep=2", b_fresh_extra in k3set)
        # ...but with a 1-day age gate that same 3rd copy (2d) is now prunable
        d4set = {p for p, _, _ in plan_dir(tmp, keep=2, age_days=1, now=now)[0]}
        chk("tighter age gate (1d) now prunes the 2d-old 3rd copy", b_fresh_extra in d4set)

        # apply actually deletes and writes a log
        run([tmp], keep=2, age_days=14, apply=True, quiet=True, now=now)
        chk("apply removed the old backups", not os.path.exists(b_old1) and not os.path.exists(b_old2))
        chk("apply left the live file", os.path.exists(live))
        chk("apply left the newest backups", os.path.exists(b_new0) and os.path.exists(b_new1))
        chk("apply wrote a prune log", os.path.exists(os.path.join(tmp, LOG_NAME)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\nself-test: %d passed, %d failed" % (ok, bad))
    return 0 if bad == 0 else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Prune stale .bak/.new/.old backup files (dry-run by default).")
    ap.add_argument("dirs", nargs="*", help="directories to scan (default: current dir)")
    ap.add_argument("--apply", action="store_true", help="actually delete (default is dry-run)")
    ap.add_argument("--keep", type=int, default=2, help="backups to keep per live file (default 2)")
    ap.add_argument("--age-days", type=int, default=14, help="only delete backups older than this (default 14)")
    ap.add_argument("--quiet", action="store_true", help="print only the final summary")
    ap.add_argument("--selftest", action="store_true", help="run the built-in self-test and exit")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    dirs = a.dirs or ["."]
    dirs = [d for d in dirs if os.path.isdir(d) or print("skip (not a dir): %s" % d)]
    if not dirs:
        print("no valid directories given."); return 2
    run(dirs, a.keep, a.age_days, a.apply, a.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
