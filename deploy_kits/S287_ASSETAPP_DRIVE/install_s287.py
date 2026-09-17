#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_s287.py -- S287_ASSETAPP_DRIVE

Upgrades /root/state_backup/assetapp_backup.py from S286 (verified, on the box
only) to v2 (verified on the box AND shipped to Google Drive). The crontab line
S286 installed is only READ, never written: same 02:30 line, same log.

WHY
    The owner, 17-Sep-2026: the asset register's backups were multiple copies on
    the VPS itself; set it right and add an off-site copy -- the off-site place
    is the connected Google Drive. S286's first run proved the size: one archive
    204 MB, and fifteen of them on the server's own disk.

WHAT v2 ADDS
    * the verified archive goes to Drive's FinanceDB_Backups folder, into two
      slot files the owner's account created at S263 (assetapp_nightly.tar.gz,
      assetapp_monthly.tar.gz) -- through finance_drive_backup.py's own calls
      and config, nothing new to configure;
    * a night identical to what Drive holds uploads nothing;
    * every upload is read back by Drive's own md5;
    * with a verified Drive copy the server keeps 3 days, without one the old 14.

SAFETY
    refuses unless S286's script 9fdc66a3... is installed and its crontab line
    is present once * selftest on this box * backup beside the file * the
    first real run must make a verified server archive (OK, or PART when only
    Drive failed) or the S286 script is put back byte-identically.

One line on the VPS:
    cd /root/deploy/repo && git pull --ff-only && /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S287_ASSETAPP_DRIVE/install_s287.py
Undo:
    \\cp /root/state_backup/assetapp_backup.py.bak_S287_9fdc66a3 /root/state_backup/assetapp_backup.py

Env (rehearsal only): ROOT=/dir  PY=/path/python3  CRONTAB=/path/fake-crontab
"""
import hashlib, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("ROOT", "/root")
PY = os.environ.get("PY", "/root/wa/venv/bin/python3")
CRONTAB = os.environ.get("CRONTAB", "crontab")
SRC = os.path.join(HERE, "assetapp_backup.py")
DEST = os.path.join(ROOT, "state_backup", "assetapp_backup.py")
LOG = os.path.join(ROOT, "backups", "assetapp_backup.log")
FROM = "9fdc66a3d7d0bfe94541b2eb228302e9"
TO = "b816504c89fa127b7519d29a77e54658"
CRON_LINE = ('30 2 * * * /root/wa/venv/bin/python3 -B /root/state_backup/assetapp_backup.py '
             '>> /root/backups/assetapp_backup.log 2>&1  # S286_ASSETAPP_BACKUP')


def md5(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def fail(m):
    print("REFUSED: %s" % m)
    sys.exit(1)


def main():
    print("== S287_ASSETAPP_DRIVE -- the asset register's backup goes to Google Drive ==")
    if not os.path.isfile(SRC) or md5(SRC) != TO:
        fail("the kit's assetapp_backup.py is missing or not %s -- the kit is damaged" % TO)
    if not os.path.isfile(DEST):
        fail("%s is not there -- install S286 first" % DEST)
    cur = md5(DEST)
    if cur == TO:
        print("Already installed -- v2 is in place. Nothing changed.")
        return 0
    if cur != FROM:
        fail("assetapp_backup.py is %s, expected S286's %s. It has moved on; rebuild against it." % (cur, FROM))
    r = subprocess.run([CRONTAB, "-l"], capture_output=True, text=True, timeout=30)
    n = sum(1 for l in (r.stdout or "").split("\n") if l.rstrip() == CRON_LINE)
    if r.returncode != 0 or n != 1:
        fail("S286's crontab line should be present exactly once; found %d. Nothing was changed." % n)
    print("gate     : S286 script %s installed; its crontab line present once (read only)" % FROM[:8])

    r = subprocess.run([PY, "-B", SRC, "--selftest"], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(r.stdout[-2500:]); print(r.stderr[-1500:])
        fail("v2 did not pass its selftest on this machine; nothing was changed")
    print("selftest : passed on this box (%d checks)" % r.stdout.count("ok   "))

    bak = "%s.bak_S287_%s" % (DEST, FROM[:8])
    shutil.copy2(DEST, bak)
    if md5(bak) != FROM:
        fail("the backup did not copy exactly; nothing was changed")
    shutil.copy2(SRC, DEST)
    os.chmod(DEST, 0o755)
    print("script   : %s -> %s  (backup %s)" % (FROM[:8], md5(DEST)[:8], bak))

    print("first run: backing up now and sending to Google Drive -- a few minutes for ~200 MB")
    sys.stdout.flush()
    r = subprocess.run([PY, "-B", DEST, "--root", ROOT, "--dest", os.path.join(ROOT, "backups")],
                       capture_output=True, text=True, timeout=3600)
    line = (r.stdout or "").strip()
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write((line or "(no output) rc=%d %s" % (r.returncode, (r.stderr or "").strip()[-300:])) + "\n")
    print("first run: %s" % (line or (r.stderr or "").strip()[-500:]))
    verdict = line.split("  ")[1].strip() if line.count("  ") >= 2 else ""
    if verdict not in ("OK", "PART"):
        shutil.copy2(bak, DEST)
        print("restored : %s" % md5(DEST))
        fail("the first run made no verified archive; S286's script is back, byte-identical. "
             "The line above says why.")
    print("")
    if verdict == "OK":
        print("DRIVE    : verified -- the archive is on Google Drive, checked by Drive's own md5.")
        print("SERVER   : now keeps 3 days of archives instead of 14.")
    else:
        print("DRIVE    : FAILED on this first run (reason in the line above). The verified server")
        print("           copy is in place and still keeps 14 days; Drive is retried every night.")
    print("DONE. Same 02:30 line, same log: %s" % LOG)
    print("To undo:  \\cp %s %s" % (bak, DEST))
    return 0


if __name__ == "__main__":
    sys.exit(main())
