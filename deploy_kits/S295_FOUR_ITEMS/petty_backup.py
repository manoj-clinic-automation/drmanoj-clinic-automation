#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
petty_backup.py -- S295 (17-Sep-2026). The petty book's photos, verified on the box and shipped to
Google Drive every night.

WHY. S289 put Manoj Bhati's bill and diary-page photos in /root/finance/petty_uploads. The entries
themselves live in finance.db, which already reaches Drive at 01:40; the photos reached nothing --
named at S265 as "what no store holds".

HOW -- NO NEW DRIVE CODE. The asset register's backup (S286/S287, /root/state_backup/assetapp_backup.py,
proven live on 17-Sep) already does the hard part: owner-owned slot files, fingerprint skip, md5
read-back, a monthly revision pinned forever, pruning that depends on a verified off-box copy. This
file imports that module read-only and reuses its off-box leg unchanged, pointed at two slot files of
its own that the owner's account (drmka.ortho) created in FinanceDB_Backups at S265:
    petty_uploads_nightly.tar.gz      petty_uploads_monthly.tar.gz
The local leg is this file's own, because there is no database here -- only photos.

ONE LINE PER NIGHT, and the exit code:
    OK    local verified and Drive current           exit 0
    PART  local verified, Drive leg failed (why)     exit 1
    FAIL  no verified local archive tonight (why)    exit 1

    python3 petty_backup.py               the nightly run
    python3 petty_backup.py --no-offsite  local leg only
    python3 petty_backup.py --selftest    temporary folders and the asset module's fake Drive
"""
import argparse
import datetime as dt
import glob
import importlib.util
import os
import sys
import tarfile
import tempfile
import time

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
ASSET_MODULE = os.environ.get("PETTY_ASSET_MODULE", "/root/state_backup/assetapp_backup.py")
NIGHTLY_SLOT = "petty_uploads_nightly.tar.gz"
MONTHLY_SLOT = "petty_uploads_monthly.tar.gz"
PREFIX = "petty_uploads_"


def asset_module(path=None):
    spec = importlib.util.spec_from_file_location("assetapp_backup_s295", path or ASSET_MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.NIGHTLY_SLOT, mod.MONTHLY_SLOT = NIGHTLY_SLOT, MONTHLY_SLOT   # its off-box leg reads these by name
    return mod


def local_leg(ab, uploads, dest):
    name = "%s%s.tar.gz" % (PREFIX, time.strftime("%Y-%m-%d"))
    final = os.path.join(dest, name)
    part = final + ".part"
    r = {"ok": False, "name": name, "path": final, "why": "", "tables": 0}
    try:
        on_disk, fp = ab.uploads_fingerprint(uploads)
        with tarfile.open(part, "w:gz") as tf:
            if os.path.isdir(uploads):
                tf.add(uploads, arcname="petty_uploads")
        seen = 0
        with tarfile.open(part, "r:gz") as tf:
            for m in tf:
                if m.isfile():
                    fh = tf.extractfile(m)
                    while fh.read(1 << 20):
                        pass
                    seen += 1
        if seen < on_disk:
            r["why"] = "photos: %d in archive, %d on disk -- this run's archive discarded" % (seen, on_disk)
            return r
        os.replace(part, final)
        r.update(ok=True, size=os.path.getsize(final), md5=ab.md5(final), uploads=seen, fp=fp[:20])
        return r
    except Exception as e:                       # noqa: BLE001
        r["why"] = "%s: %s" % (type(e).__name__, e)
        return r
    finally:
        if os.path.exists(part):
            try:
                os.remove(part)
            except OSError:
                pass


def prune(dest, keep_days, today_name, now_ts):
    gone = []
    for p in sorted(glob.glob(os.path.join(dest, PREFIX + "*.tar.gz"))):
        if os.path.basename(p) == today_name:
            continue
        if int((now_ts - os.path.getmtime(p)) // 86400) > keep_days:
            os.remove(p)
            gone.append(os.path.basename(p))
    return gone


def run(ab, uploads, dest, offsite=True, now=None, drive_factory=None):
    now = now or dt.datetime.now(IST)
    stamp = now.strftime("%Y-%m-%d %H:%M:%S IST")
    loc = local_leg(ab, uploads, dest)
    if not loc["ok"]:
        return 1, "%s  FAIL  %s  local: %s -- nothing shipped, nothing pruned" % (stamp, loc["name"], loc["why"])
    head = "%s  {V}  %s  local ok %s B md5 %s, photos %d" % (
        stamp, loc["name"], format(loc["size"], ","), loc["md5"], loc["uploads"])
    if offsite:
        off_ok, off_txt = ab.offsite_leg(loc, now, drive_factory or ab.real_drive)
    else:
        off_ok, off_txt = False, "drive skipped (--no-offsite)"
    keep = ab.KEEP_DAYS_WITH_OFFSITE if off_ok else ab.KEEP_DAYS_NO_OFFSITE
    gone = prune(dest, keep, loc["name"], time.time())
    kept = len(glob.glob(os.path.join(dest, PREFIX + "*.tar.gz")))
    line = "%s | %s | pruned %d, kept %d (keep %d days)" % (
        head.replace("{V}", "OK  " if off_ok else "PART"), off_txt if off_ok else "DRIVE FAILED: " + off_txt,
        len(gone), kept, keep)
    return (0 if off_ok else 1), line


def selftest(asset_path=None):
    ab = asset_module(asset_path)
    n = [0]

    def check(name, got, want):
        n[0] += 1
        if got != want:
            print("FAIL %d %s: got %r want %r" % (n[0], name, got, want))
            sys.exit(1)
    tmp = tempfile.mkdtemp(prefix="petty_bk_")
    up, dest = os.path.join(tmp, "petty_uploads"), os.path.join(tmp, "backups")
    os.makedirs(os.path.join(up, "2026-09"))
    os.makedirs(dest)
    for i in range(3):
        with open(os.path.join(up, "2026-09", "p%d.jpg" % i), "wb") as fh:
            fh.write(os.urandom(2048))
    fake = ab.FakeDrive(slots=(NIGHTLY_SLOT, MONTHLY_SLOT))
    now = dt.datetime(2026, 9, 17, 2, 40, tzinfo=IST)
    code, line = run(ab, up, dest, now=now, drive_factory=lambda: (fake, "F"))
    check("first night OK", (code, " OK " in line, "photos 3" in line, "drive shipped" in line), (0, True, True, True))
    code, line = run(ab, up, dest, now=now, drive_factory=lambda: (fake, "F"))
    check("same photos -> drive unchanged", (code, "drive unchanged" in line), (0, True))
    with open(os.path.join(up, "2026-09", "p9.jpg"), "wb") as fh:
        fh.write(os.urandom(1024))
    code, line = run(ab, up, dest, now=now, drive_factory=lambda: (fake, "F"))
    check("a new photo ships again", (code, "photos 4" in line, "drive shipped" in line), (0, True, True))
    lonely = ab.FakeDrive(slots=(NIGHTLY_SLOT,))
    code, line = run(ab, up, dest, now=now, drive_factory=lambda: (lonely, "F"))
    check("missing monthly slot is PART and named", (code, MONTHLY_SLOT in line), (1, True))
    empty = os.path.join(tmp, "none")
    code, line = run(ab, empty, dest, now=now, drive_factory=lambda: (ab.FakeDrive(slots=(NIGHTLY_SLOT, MONTHLY_SLOT)), "F"))
    check("no photos yet is still a verified night", (code, "photos 0" in line), (0, True))
    check("slot names are this file's, not the asset register's", (ab.NIGHTLY_SLOT, ab.MONTHLY_SLOT), (NIGHTLY_SLOT, MONTHLY_SLOT))
    print("SELFTEST OK -- %d checks (petty photos: verified archive, Drive ship, unchanged skip, new photo, missing slot, empty folder)" % n[0])
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uploads", default="/root/finance/petty_uploads")
    ap.add_argument("--dest", default="/root/backups")
    ap.add_argument("--no-offsite", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--asset-module", default=None)
    a = ap.parse_args()
    if a.selftest:
        return selftest(a.asset_module)
    if not os.path.isdir(a.dest):
        print("%s  FAIL  backup folder %s does not exist" % (dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"), a.dest))
        return 1
    code, line = run(asset_module(a.asset_module), a.uploads, a.dest, offsite=not a.no_offsite)
    print(line)
    sys.stdout.flush()
    return code


if __name__ == "__main__":
    sys.exit(main())
