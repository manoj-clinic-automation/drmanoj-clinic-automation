#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_s286.py -- S286_ASSETAPP_BACKUP

Gives the asset register's 02:30 backup a log and a verdict. Two changes, both
reversible in one line:
  1. puts assetapp_backup.py in /root/state_backup/ (the nightly code bundle
     already carries that folder, so tomorrow's bundle proves the pin);
  2. replaces ONE crontab line -- the bare tar -- with a line that runs it and
     appends to /root/backups/assetapp_backup.log. No other line is touched.

ORDER, AND WHAT STOPS IT
  gate: the old line is in the crontab exactly once, and the script is absent
        or already the kit's bytes -> selftest on this box -> script in place
        -> ONE REAL RUN NOW: must end OK, or the script is removed and the
        crontab is never opened -> crontab backed up, the one line swapped,
        read back and compared whole -> any mismatch restores the backup.

One line on the VPS:
    cd /root/deploy/repo && git pull --ff-only && /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S286_ASSETAPP_BACKUP/install_s286.py
Undo (both halves):
    crontab /root/finance/crontab.bak_S286

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
BAK = os.path.join(ROOT, "finance", "crontab.bak_S286")
SCRIPT_MD5 = "9fdc66a3d7d0bfe94541b2eb228302e9"

OLD_LINE = ('30 2 * * * tar -czf /root/backups/assetapp_$(date +\\%F).tar.gz -C /root '
            'assetapp/assets.db assetapp/uploads 2>/dev/null; find /root/backups -name '
            '"assetapp_*.tar.gz" -mtime +14 -delete')
NEW_LINE = ('30 2 * * * /root/wa/venv/bin/python3 -B /root/state_backup/assetapp_backup.py '
            '>> /root/backups/assetapp_backup.log 2>&1  # S286_ASSETAPP_BACKUP')


def md5(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def fail(m):
    print("REFUSED: %s" % m)
    sys.exit(1)


def crontab_read():
    r = subprocess.run([CRONTAB, "-l"], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        fail("crontab -l failed: %s" % (r.stderr.strip() or r.returncode))
    return r.stdout


def crontab_write(path):
    r = subprocess.run([CRONTAB, path], capture_output=True, text=True, timeout=30)
    return r.returncode == 0, r.stderr.strip()


def main():
    print("== S286_ASSETAPP_BACKUP -- the asset register's backup gets a log ==")
    if not os.path.isfile(SRC) or md5(SRC) != SCRIPT_MD5:
        fail("the kit's assetapp_backup.py is missing or not %s -- the kit is damaged" % SCRIPT_MD5)
    if not os.path.isfile(os.path.join(ROOT, "assetapp", "assets.db")):
        fail("%s/assetapp/assets.db is not there" % ROOT)
    if not os.path.isdir(os.path.join(ROOT, "backups")):
        fail("%s/backups is not there" % ROOT)

    cron = crontab_read()
    lines = cron.split("\n")
    n_old = sum(1 for l in lines if l.rstrip() == OLD_LINE)
    n_new = sum(1 for l in lines if l.rstrip() == NEW_LINE)
    if n_new == 1 and n_old == 0 and os.path.isfile(DEST) and md5(DEST) == SCRIPT_MD5:
        print("Already installed -- the new line is in the crontab and the script matches. Nothing changed.")
        return 0
    if n_old != 1 or n_new != 0:
        fail("expected the old tar line exactly once and the new line not at all; found old %d, new %d. "
             "The crontab has moved on; rebuild against it." % (n_old, n_new))
    if os.path.exists(DEST) and md5(DEST) != SCRIPT_MD5:
        fail("%s already exists with different bytes (%s)" % (DEST, md5(DEST)))
    print("gate     : old line found once; script slot %s" % ("free" if not os.path.exists(DEST) else "already the kit's bytes"))

    r = subprocess.run([PY, "-B", SRC, "--selftest"], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(r.stdout[-2500:]); print(r.stderr[-1500:])
        fail("the script did not pass its selftest on this machine; nothing was changed")
    print("selftest : passed on this box (%d checks)" % r.stdout.count("ok   "))

    placed = not os.path.exists(DEST)
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    shutil.copy2(SRC, DEST)
    os.chmod(DEST, 0o755)
    print("script   : %s (%s)" % (DEST, md5(DEST)))

    r = subprocess.run([PY, "-B", DEST, "--root", ROOT, "--dest", os.path.join(ROOT, "backups")],
                       capture_output=True, text=True, timeout=1800)
    line = (r.stdout or "").strip()
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write((line or "(no output) rc=%d %s" % (r.returncode, (r.stderr or "").strip()[-300:])) + "\n")
    print("first run: %s" % (line or r.stderr.strip()[-500:]))
    if r.returncode != 0 or "  OK    " not in line:
        if placed:
            os.remove(DEST)
        fail("the first real run did not end OK. The script is removed, the crontab was never opened, "
             "the old 02:30 tar line still runs tonight. The line above says why.")

    with open(BAK, "w", encoding="utf-8") as fh:
        fh.write(cron)
    with open(BAK, encoding="utf-8") as fh:
        if fh.read() != cron:
            fail("the crontab backup did not read back exactly; the crontab was not changed")
    new_text = "\n".join(NEW_LINE if l.rstrip() == OLD_LINE else l for l in lines)
    tmp = BAK + ".new"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(new_text)
    ok, err = crontab_write(tmp)
    after = crontab_read() if ok else None
    if not ok or after != new_text:
        crontab_write(BAK)
        back = crontab_read()
        fail("the crontab did not read back as written (%s); restored from the backup -- %s"
             % (err or "content differs", "identical again" if back == cron else "CHECK BY HAND: crontab -l"))
    os.remove(tmp)
    print("crontab  : 1 line swapped, %d lines before and after, read back whole" % len(lines))
    print("backup   : %s" % BAK)
    print("")
    print("  was : %s" % OLD_LINE)
    print("  now : %s" % NEW_LINE)
    print("")
    print("DONE. Tonight's 02:30 run writes its own line to %s," % LOG)
    print("and the hourly job pulse will read it instead of NO TRACE.")
    print("To undo:  crontab %s" % BAK)
    return 0


if __name__ == "__main__":
    sys.exit(main())
