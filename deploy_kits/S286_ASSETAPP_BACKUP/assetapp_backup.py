#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assetapp_backup.py -- S286. The asset register's nightly backup, able to say
whether it worked.

WHAT IT REPLACES
    One crontab line, 02:30 daily, since before S230:
      tar -czf /root/backups/assetapp_$(date +%F).tar.gz -C /root \
          assetapp/assets.db assetapp/uploads 2>/dev/null; \
      find /root/backups -name "assetapp_*.tar.gz" -mtime +14 -delete
    It named no log and sent its errors to /dev/null, so job_pulse could only
    ever say NO TRACE. And it pruned old archives whether or not tonight's had
    worked: fourteen failed nights in a row would have left no good copy.

WHAT IT DOES -- the same archive, the same name, the same fourteen days, plus:
    1. assets.db is copied with SQLite's own backup call and checked with
       PRAGMA integrity_check before it goes in. tar read a live database file
       mid-write; this cannot.
    2. The archive is written as .part, then reopened and every member read
       back in full (which checks every gzip CRC), and the uploads counted
       against the disk. Only then does it take the real name.
    3. Old archives are pruned ONLY after a night that passed, and never
       today's. The age rule is find's -mtime +14, exactly.
    4. One line per run on stdout -- cron appends it to
       /root/backups/assetapp_backup.log -- and exit 0 or 1.

WHAT IT TOUCHES
    Reads /root/assetapp/assets.db (read-only) and /root/assetapp/uploads.
    Writes only /root/backups/assetapp_<date>.tar.gz and deletes only
    /root/backups/assetapp_*.tar.gz older than the retention. The app is not
    stopped, not written, not restarted.

    python3 assetapp_backup.py               the nightly run
    python3 assetapp_backup.py --selftest    in a temporary folder only
"""
import argparse
import datetime as dt
import glob
import hashlib
import os
import shutil
import sqlite3
import sys
import tarfile
import tempfile
import time

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_db(src, dst):
    """A consistent copy through SQLite's backup API, then integrity_check."""
    con = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    try:
        out = sqlite3.connect(dst)
        try:
            con.backup(out)
            res = out.execute("PRAGMA integrity_check").fetchone()[0]
            tables = out.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        finally:
            out.close()
    finally:
        con.close()
    return res, tables


def count_files(folder):
    n = 0
    for _, _, files in os.walk(folder):
        n += len(files)
    return n


def prune(dest, keep_days, today_name, now_ts):
    """find -name 'assetapp_*.tar.gz' -mtime +N -delete, never today's."""
    gone = []
    for p in sorted(glob.glob(os.path.join(dest, "assetapp_*.tar.gz"))):
        if os.path.basename(p) == today_name:
            continue
        age_days = int((now_ts - os.path.getmtime(p)) // 86400)
        if age_days > keep_days:
            os.remove(p)
            gone.append(os.path.basename(p))
    return gone


def run(root, dest, keep_days, now=None):
    """Returns (ok, line)."""
    now = now or dt.datetime.now(IST)
    app = os.path.join(root, "assetapp")
    db = os.path.join(app, "assets.db")
    uploads = os.path.join(app, "uploads")
    name = "assetapp_%s.tar.gz" % time.strftime("%Y-%m-%d")   # = $(date +%F)
    final = os.path.join(dest, name)
    part = final + ".part"
    stamp = now.strftime("%Y-%m-%d %H:%M:%S IST")
    problems = []
    tmpdir = tempfile.mkdtemp(prefix=".assetapp_snap_", dir=dest)
    snap = os.path.join(tmpdir, "assets.db")
    try:
        if not os.path.isfile(db):
            return False, "%s  FAIL  %s  assets.db not found at %s -- nothing written, nothing pruned" % (stamp, name, db)
        try:
            integ, tables = snapshot_db(db, snap)
        except Exception as e:
            return False, "%s  FAIL  %s  could not copy assets.db (%s) -- nothing written, nothing pruned" % (stamp, name, e)
        if integ != "ok":
            return False, "%s  FAIL  %s  assets.db integrity_check said %r -- nothing written, nothing pruned" % (stamp, name, integ[:80])

        have_uploads = os.path.isdir(uploads)
        on_disk = count_files(uploads) if have_uploads else 0
        if not have_uploads:
            problems.append("uploads folder missing")

        with tarfile.open(part, "w:gz") as tf:
            tf.add(snap, arcname="assetapp/assets.db")
            if have_uploads:
                tf.add(uploads, arcname="assetapp/uploads")

        # read it all back: every member, every byte, every CRC
        in_archive, db_seen = 0, False
        with tarfile.open(part, "r:gz") as tf:
            for m in tf:
                if m.isfile():
                    fh = tf.extractfile(m)
                    while fh.read(1 << 20):
                        pass
                    if m.name == "assetapp/assets.db":
                        db_seen = True
                    else:
                        in_archive += 1
        if not db_seen:
            problems.append("assets.db missing from the archive")
        if have_uploads and in_archive < on_disk:
            # a file added to uploads mid-run may make the disk count larger by
            # one or two; fewer in the archive than on disk before is a fault
            problems.append("uploads: %d in archive, %d on disk" % (in_archive, on_disk))

        if problems:
            # A flawed archive never replaces a good one already made today.
            # With no archive for today at all, the flawed one is kept -- a
            # database without its photos still beats nothing -- and says so.
            if os.path.exists(final):
                return False, ("%s  FAIL  %s  -- %s -- this run's archive discarded, the earlier one for today "
                               "kept (md5 %s) -- nothing pruned"
                               % (stamp, name, "; ".join(problems), md5(final)))
            os.replace(part, final)
            size, digest = os.path.getsize(final), md5(final)
            return False, ("%s  FAIL  %s  %s B  md5 %s  db ok (%d tables)  uploads %d  -- %s -- kept as the only "
                           "copy for today -- nothing pruned"
                           % (stamp, name, format(size, ","), digest, tables, in_archive, "; ".join(problems)))
        os.replace(part, final)
        size, digest = os.path.getsize(final), md5(final)
        gone = prune(dest, keep_days, name, time.time())
        kept = len(glob.glob(os.path.join(dest, "assetapp_*.tar.gz")))
        return True, ("%s  OK    %s  %s B  md5 %s  db ok (%d tables)  uploads %d  pruned %d  kept %d"
                      % (stamp, name, format(size, ","), digest, tables, in_archive, len(gone), kept))
    except Exception as e:
        return False, "%s  FAIL  %s  %s: %s -- nothing pruned" % (stamp, name, type(e).__name__, e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        if os.path.exists(part):
            try:
                os.remove(part)
            except OSError:
                pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/root")
    ap.add_argument("--dest", default="/root/backups")
    ap.add_argument("--keep-days", type=int, default=14)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not os.path.isdir(a.dest):
        print("%s  FAIL  backup folder %s does not exist"
              % (dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"), a.dest))
        return 1
    ok, line = run(a.root, a.dest, a.keep_days)
    print(line)
    sys.stdout.flush()
    return 0 if ok else 1


# ----------------------------------------------------------------- self test
def selftest():
    ok = True

    def check(name, got, want):
        nonlocal ok
        if got != want:
            ok = False
            print("FAIL %-52s got %r want %r" % (name, got, want))
        else:
            print("ok   %s" % name)

    base = tempfile.mkdtemp(prefix="s286_selftest_")
    try:
        root, dest = os.path.join(base, "root"), os.path.join(base, "backups")
        app = os.path.join(root, "assetapp")
        os.makedirs(os.path.join(app, "uploads", "2026", "09"))
        os.makedirs(dest)
        con = sqlite3.connect(os.path.join(app, "assets.db"))
        con.execute("CREATE TABLE asset (id INTEGER PRIMARY KEY, name TEXT)")
        con.executemany("INSERT INTO asset(name) VALUES (?)", [("chair",), ("x-ray viewer",)])
        con.commit(); con.close()
        for i in range(5):
            with open(os.path.join(app, "uploads", "2026", "09", "scan%d.jpg" % i), "wb") as fh:
                fh.write(os.urandom(2048))
        today = "assetapp_%s.tar.gz" % time.strftime("%Y-%m-%d")
        old15 = os.path.join(dest, "assetapp_2026-08-01.tar.gz")
        old14 = os.path.join(dest, "assetapp_2026-08-02.tar.gz")
        for p, days in ((old15, 15.2), (old14, 14.5)):
            open(p, "wb").write(b"old")
            t = time.time() - days * 86400
            os.utime(p, (t, t))

        good, line = run(root, dest, 14)
        check("a good night passes", good, True)
        check("its line says OK", "  OK    " in line, True)
        check("the archive has the same name as the old tar", os.path.isfile(os.path.join(dest, today)), True)
        check("the line counts the uploads", "uploads 5 " in line, True)
        with tarfile.open(os.path.join(dest, today), "r:gz") as tf:
            names = sorted(m.name for m in tf if m.isfile())
            tf.extract("assetapp/assets.db", os.path.join(base, "x"))
        check("members keep the old paths", names[0], "assetapp/assets.db")
        check("all five uploads are in", len([n for n in names if n.startswith("assetapp/uploads/")]), 5)
        c = sqlite3.connect(os.path.join(base, "x", "assetapp", "assets.db"))
        check("the archived database opens with its rows", c.execute("SELECT COUNT(*) FROM asset").fetchone()[0], 2)
        c.close()
        check("find -mtime +14: a 15-day archive is pruned", os.path.exists(old15), False)
        check("find -mtime +14: a 14-day archive is kept", os.path.exists(old14), True)
        check("no .part and no snapshot left behind",
              [n for n in os.listdir(dest) if n.endswith(".part") or n.startswith(".assetapp_snap_")], [])

        # a bad night must not prune
        old16 = os.path.join(dest, "assetapp_2026-07-30.tar.gz")
        open(old16, "wb").write(b"old"); t = time.time() - 16 * 86400; os.utime(old16, (t, t))
        good_md5 = md5(os.path.join(dest, today))
        shutil.move(os.path.join(app, "uploads"), os.path.join(base, "uploads_away"))
        bad, line2 = run(root, dest, 14)
        check("a flawed archive never replaces today's good one", md5(os.path.join(dest, today)), good_md5)
        check("missing uploads is a FAIL", bad, False)
        check("and says why", "uploads folder missing" in line2, True)
        check("a failed night prunes nothing", os.path.exists(old16), True)
        shutil.move(os.path.join(base, "uploads_away"), os.path.join(app, "uploads"))

        # a corrupt database is refused before anything is written
        before = md5(os.path.join(dest, today))
        with open(os.path.join(app, "assets.db"), "r+b") as fh:
            fh.seek(100); fh.write(b"\x00" * 3000)
        bad2, line3 = run(root, dest, 14)
        check("a damaged database is a FAIL", bad2, False)
        check("and today's good archive is not overwritten", md5(os.path.join(dest, today)), before)
        check("a damaged database prunes nothing", os.path.exists(old16), True)

        # with no archive yet for today, a flawed night still keeps what it has
        os.remove(os.path.join(dest, today))
        shutil.move(os.path.join(app, "uploads"), os.path.join(base, "uploads_away2"))
        con = sqlite3.connect(os.path.join(base, "fresh.db")); con.execute("CREATE TABLE t (a)"); con.commit(); con.close()
        shutil.copy(os.path.join(base, "fresh.db"), os.path.join(app, "assets.db"))
        bad4, line5 = run(root, dest, 14)
        check("with nothing for today the flawed archive is kept and labelled",
              (bad4, os.path.isfile(os.path.join(dest, today)), "only copy for today" in line5), (False, True, True))
        shutil.move(os.path.join(base, "uploads_away2"), os.path.join(app, "uploads"))

        # no database at all
        os.remove(os.path.join(app, "assets.db"))
        bad3, line4 = run(root, dest, 14)
        check("no database is a FAIL that says where it looked", (bad3, "not found" in line4), (False, True))
        check("every line is one line", all("\n" not in s for s in (line, line2, line3, line4)), True)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print("\nSELFTEST %s" % ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
