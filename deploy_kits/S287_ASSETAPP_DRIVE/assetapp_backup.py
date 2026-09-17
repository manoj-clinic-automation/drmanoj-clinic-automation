#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assetapp_backup.py -- S286, v2 by S287. The asset register's nightly backup: verified on
the box, shipped off the box, and able to say whether it worked.

WHAT IT REPLACES
    One crontab line, 02:30 daily:
      tar -czf /root/backups/assetapp_$(date +%F).tar.gz -C /root \
          assetapp/assets.db assetapp/uploads 2>/dev/null; \
      find /root/backups -name "assetapp_*.tar.gz" -mtime +14 -delete
    No log, errors thrown away, pruning whether or not the night worked, a live
    database tarred mid-write -- and fourteen copies that all sat on the same
    disk as the app. The uploaded photos had no copy anywhere else.

THE LOCAL LEG
    1. assets.db copied through SQLite's backup call; PRAGMA integrity_check.
    2. The archive written as .part, reopened, every member read back in full
       (every gzip CRC), uploads counted against the disk -- then renamed.
    3. A flawed archive never replaces a good one already made today.

THE OFF-BOX LEG -- Google Drive, the same folder and the same proven route as
finance_drive_backup.py (S213), whose Drive calls and config this imports.
    * The service account has NO storage of its own. It can only write new
      content into files the OWNER already owns. Two such slot files exist in
      the FinanceDB_Backups folder, created from the owner's account at S263:
          assetapp_nightly.tar.gz    replaced whenever the register changed
          assetapp_monthly.tar.gz    first verified run of each month, that
                                     revision PINNED (kept forever) while the
                                     archive is under PIN_MAX_BYTES
    * A night whose content matches what Drive already holds -- same database
      rows, same uploads by name, size and time -- uploads nothing: the Drive
      copy is already current, and Drive's revision history is not spent on
      identical bytes. The match is proven, not assumed: the fingerprint and
      the md5 are both recorded on the Drive file and the md5 is Drive's own.
    * Every upload is read back: Drive's md5 must equal the local md5.

PRUNING, AND WHY IT DEPENDS ON THE OFF-BOX LEG
    Only after a verified local archive, never today's, age rule = find -mtime.
    With a verified Drive copy for tonight, the box keeps 3 days; without one
    it keeps the old 14, so a Drive outage never thins the only copies.

ONE LINE PER NIGHT, and the exit code:
    OK    local verified and Drive current           exit 0
    PART  local verified, Drive leg failed (why)     exit 1
    FAIL  no verified local archive tonight (why)    exit 1

    python3 assetapp_backup.py               the nightly run
    python3 assetapp_backup.py --no-offsite  local leg only
    python3 assetapp_backup.py --selftest    temporary folder and a fake Drive
"""
import argparse
import datetime as dt
import glob
import hashlib
import importlib.util
import os
import shutil
import sqlite3
import sys
import tarfile
import tempfile
import time

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
DRIVE_MODULE = "/root/finance/finance_drive_backup.py"
NIGHTLY_SLOT = "assetapp_nightly.tar.gz"
MONTHLY_SLOT = "assetapp_monthly.tar.gz"
KEEP_DAYS_NO_OFFSITE = 14
KEEP_DAYS_WITH_OFFSITE = 3
MAX_OFFSITE_BYTES = 2 * 1024 ** 3        # refuse to ship more than 2 GB in one night
PIN_MAX_BYTES = 500 * 1024 ** 2          # pin a monthly forever only below 500 MB


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_db(src, dst):
    """A consistent copy through SQLite's backup API, integrity_check, and a
    fingerprint of the rows themselves (not the file's bytes)."""
    con = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    try:
        out = sqlite3.connect(dst)
        try:
            con.backup(out)
            res = out.execute("PRAGMA integrity_check").fetchone()[0]
            tables = out.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
            h = hashlib.sha1()
            if res == "ok":
                for stmt in out.iterdump():
                    h.update(stmt.encode("utf-8", "replace"))
                    h.update(b"\n")
        finally:
            out.close()
    finally:
        con.close()
    return res, tables, h.hexdigest()


def uploads_fingerprint(folder):
    """(file count, sha1 of every relative path, size and whole-second mtime)."""
    h, n = hashlib.sha1(), 0
    if not os.path.isdir(folder):
        return 0, h.hexdigest()
    rows = []
    for base, _, files in os.walk(folder):
        for f in files:
            p = os.path.join(base, f)
            try:
                st = os.stat(p)
            except OSError:
                continue
            rows.append("%s\t%d\t%d" % (os.path.relpath(p, folder), st.st_size, int(st.st_mtime)))
    for r in sorted(rows):
        h.update(r.encode("utf-8", "replace"))
        h.update(b"\n")
        n += 1
    return n, h.hexdigest()


def prune(dest, keep_days, today_name, now_ts):
    """find -name 'assetapp_*.tar.gz' -mtime +N -delete, never today's."""
    gone = []
    for p in sorted(glob.glob(os.path.join(dest, "assetapp_*.tar.gz"))):
        if os.path.basename(p) == today_name:
            continue
        if int((now_ts - os.path.getmtime(p)) // 86400) > keep_days:
            os.remove(p)
            gone.append(os.path.basename(p))
    return gone


# ------------------------------------------------------------------ local leg
def local_leg(root, dest, now):
    """Returns dict: ok, name, path, size, md5, tables, uploads, fp, why."""
    app = os.path.join(root, "assetapp")
    db = os.path.join(app, "assets.db")
    uploads = os.path.join(app, "uploads")
    name = "assetapp_%s.tar.gz" % time.strftime("%Y-%m-%d")   # = $(date +%F)
    final = os.path.join(dest, name)
    part = final + ".part"
    r = {"ok": False, "name": name, "path": final, "why": ""}
    tmpdir = tempfile.mkdtemp(prefix=".assetapp_snap_", dir=dest)
    snap = os.path.join(tmpdir, "assets.db")
    try:
        if not os.path.isfile(db):
            r["why"] = "assets.db not found at %s -- nothing written" % db
            return r
        try:
            integ, tables, db_fp = snapshot_db(db, snap)
        except Exception as e:
            r["why"] = "could not copy assets.db (%s) -- nothing written" % e
            return r
        if integ != "ok":
            r["why"] = "assets.db integrity_check said %r -- nothing written" % integ[:80]
            return r
        have_uploads = os.path.isdir(uploads)
        on_disk, up_fp = uploads_fingerprint(uploads)
        problems = [] if have_uploads else ["uploads folder missing"]

        with tarfile.open(part, "w:gz") as tf:
            tf.add(snap, arcname="assetapp/assets.db")
            if have_uploads:
                tf.add(uploads, arcname="assetapp/uploads")
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
            problems.append("uploads: %d in archive, %d on disk" % (in_archive, on_disk))

        r.update(tables=tables, uploads=in_archive,
                 fp=hashlib.sha1(("%s|%s" % (db_fp, up_fp)).encode()).hexdigest()[:20])
        if problems:
            if os.path.exists(final):
                r["why"] = ("%s -- this run's archive discarded, the earlier one for today kept (md5 %s)"
                            % ("; ".join(problems), md5(final)))
                return r
            os.replace(part, final)
            r.update(size=os.path.getsize(final), md5=md5(final))
            r["why"] = "%s -- kept as the only copy for today" % "; ".join(problems)
            return r
        os.replace(part, final)
        r.update(ok=True, size=os.path.getsize(final), md5=md5(final))
        return r
    except Exception as e:
        r["why"] = "%s: %s" % (type(e).__name__, e)
        return r
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        if os.path.exists(part):
            try:
                os.remove(part)
            except OSError:
                pass


# --------------------------------------------------------------- off-box leg
def real_drive():
    """(drive, folder_id) through finance_drive_backup.py's own calls and conf."""
    spec = importlib.util.spec_from_file_location("finance_drive_backup", DRIVE_MODULE)
    fdb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fdb)
    conf = fdb.load_conf()
    sa = fdb.find_sa_json(conf)
    fid = conf.get("FOLDER_ID")
    if not sa or not fid:
        raise RuntimeError("Drive not configured (%s)" % ("no service account json" if not sa else
                                                          "FOLDER_ID blank in drive_backup.conf"))
    return fdb.Drive(fdb.make_session(sa)), fid


def _desc_field(desc, key):
    for part in (desc or "").split(" · "):
        if part.startswith(key + "="):
            return part[len(key) + 1:]
    return None


def offsite_leg(loc, now, drive_factory):
    """Returns (ok, text)."""
    try:
        d, fid = drive_factory()
        files = {f["name"]: f for f in d.list(fid)}
        missing = [n for n in (NIGHTLY_SLOT, MONTHLY_SLOT) if n not in files]
        if missing:
            return False, ("slot file(s) missing in the Drive folder: %s -- they must be owned by the "
                           "owner's account; the service account cannot create them" % ", ".join(missing))
        nightly, monthly = files[NIGHTLY_SLOT], files[MONTHLY_SLOT]
        stamp = now.strftime("%Y-%m-%d %H:%M IST")
        ndesc = nightly.get("description") or ""
        texts = []
        if (_desc_field(ndesc, "fp") == loc["fp"] and nightly.get("md5Checksum")
                and _desc_field(ndesc, "md5") == nightly.get("md5Checksum")):
            texts.append("drive unchanged (current since %s)" % (_desc_field(ndesc, "shipped") or "?"))
            shipped_md5 = nightly.get("md5Checksum")
        else:
            if loc["size"] > MAX_OFFSITE_BYTES:
                return False, ("archive is %s B, over the %s B nightly limit -- not shipped"
                               % (format(loc["size"], ","), format(MAX_OFFSITE_BYTES, ",")))
            d.update_content(nightly["id"], loc["path"])
            got = d.get(nightly["id"])
            if got.get("md5Checksum") != loc["md5"] or int(got.get("size", -1)) != loc["size"]:
                return False, ("nightly upload DID NOT VERIFY (drive md5 %s, local %s) -- the previous "
                               "good version is still in the file's revision history"
                               % (got.get("md5Checksum"), loc["md5"]))
            d.patch_meta(nightly["id"], {"description": " · ".join([
                "assetapp backup", "fp=%s" % loc["fp"], "md5=%s" % loc["md5"],
                "bytes=%d" % loc["size"], "uploads=%d" % loc["uploads"], "shipped=%s" % stamp])})
            texts.append("drive shipped %s B, md5 verified" % format(loc["size"], ","))
            shipped_md5 = loc["md5"]

        # monthly -- first verified night of the month; a failure here warns only
        mtag = now.strftime("%Y-%m")
        if _desc_field(monthly.get("description"), "month") != mtag:
            try:
                d.update_content(monthly["id"], loc["path"])
                mg = d.get(monthly["id"])
                if mg.get("md5Checksum") != loc["md5"]:
                    texts.append("monthly WARN did not verify")
                else:
                    pinned = "not pinned (over %d MB)" % (PIN_MAX_BYTES // 1024 ** 2)
                    if loc["size"] <= PIN_MAX_BYTES:
                        revs = d.revisions(monthly["id"])
                        if revs:
                            d.pin_revision(monthly["id"], revs[-1]["id"])
                            pinned = "pinned forever"
                    d.patch_meta(monthly["id"], {"description": " · ".join([
                        "month=%s" % mtag, "assetapp backup", "fp=%s" % loc["fp"],
                        "md5=%s" % loc["md5"], "bytes=%d" % loc["size"], "shipped=%s" % stamp])})
                    texts.append("monthly %s %s" % (mtag, pinned))
            except Exception as e:
                texts.append("monthly WARN %s" % str(e)[:120])
        return True, "; ".join(texts)
    except Exception as e:
        return False, ("%s: %s" % (type(e).__name__, str(e)[:200])).replace("\n", " ")


def run(root, dest, offsite=True, now=None, drive_factory=real_drive):
    """Returns (exit_code, line)."""
    now = now or dt.datetime.now(IST)
    stamp = now.strftime("%Y-%m-%d %H:%M:%S IST")
    loc = local_leg(root, dest, now)
    if not loc["ok"]:
        return 1, "%s  FAIL  %s  local: %s -- nothing shipped, nothing pruned" % (stamp, loc["name"], loc["why"])
    head = ("%s  {V}  %s  local ok %s B md5 %s, db ok (%d tables), uploads %d"
            % (stamp, loc["name"], format(loc["size"], ","), loc["md5"], loc["tables"], loc["uploads"]))
    if offsite:
        off_ok, off_txt = offsite_leg(loc, now, drive_factory)
    else:
        off_ok, off_txt = False, "drive skipped (--no-offsite)"
    keep = KEEP_DAYS_WITH_OFFSITE if off_ok else KEEP_DAYS_NO_OFFSITE
    gone = prune(dest, keep, loc["name"], time.time())
    kept = len(glob.glob(os.path.join(dest, "assetapp_*.tar.gz")))
    verdict = "OK  " if off_ok else "PART"
    line = "%s | %s | pruned %d, kept %d (keep %d days)" % (
        head.replace("{V}", verdict), off_txt if off_ok else "DRIVE FAILED: " + off_txt, len(gone), kept, keep)
    return (0 if off_ok else 1), line


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/root")
    ap.add_argument("--dest", default="/root/backups")
    ap.add_argument("--no-offsite", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not os.path.isdir(a.dest):
        print("%s  FAIL  backup folder %s does not exist"
              % (dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"), a.dest))
        return 1
    code, line = run(a.root, a.dest, offsite=not a.no_offsite)
    print(line)
    sys.stdout.flush()
    return code


# ----------------------------------------------------------------- self test
class FakeDrive(object):
    """Behaves like the six Drive calls: slot files, md5 on read-back, revisions."""

    def __init__(self, slots=(NIGHTLY_SLOT, MONTHLY_SLOT)):
        self.files = {}
        for i, n in enumerate(slots):
            self.files["id%d" % i] = {"id": "id%d" % i, "name": n, "size": "86",
                                      "md5Checksum": "placeholder", "description": "", "revs": []}
        self.uploads = 0
        self.corrupt = False
        self.fail_list = False

    def list(self, fid):
        if self.fail_list:
            raise RuntimeError("list -> HTTP 503: backend error")
        return [dict((k, v) for k, v in f.items() if k != "revs") for f in self.files.values()]

    def update_content(self, fid, path):
        f = self.files[fid]
        f["md5Checksum"] = "0" * 32 if self.corrupt else md5(path)
        f["size"] = str(os.path.getsize(path))
        f["revs"].append({"id": "r%d" % (len(f["revs"]) + 1), "keepForever": False})
        self.uploads += 1

    def get(self, fid):
        return dict((k, v) for k, v in self.files[fid].items() if k != "revs")

    def patch_meta(self, fid, body):
        self.files[fid].update(body)

    def revisions(self, fid):
        return list(self.files[fid]["revs"])

    def pin_revision(self, fid, rid):
        for r in self.files[fid]["revs"]:
            if r["id"] == rid:
                r["keepForever"] = True


def selftest():
    ok = True

    def check(name, got, want):
        nonlocal ok
        if got != want:
            ok = False
            print("FAIL %-58s got %r want %r" % (name, got, want))
        else:
            print("ok   %s" % name)

    base = tempfile.mkdtemp(prefix="s286_selftest_")
    try:
        root, dest = os.path.join(base, "root"), os.path.join(base, "backups")
        app = os.path.join(root, "assetapp")
        up = os.path.join(app, "uploads", "2026", "09")
        os.makedirs(up)
        os.makedirs(dest)
        con = sqlite3.connect(os.path.join(app, "assets.db"))
        con.execute("CREATE TABLE asset (id INTEGER PRIMARY KEY, name TEXT)")
        con.executemany("INSERT INTO asset(name) VALUES (?)", [("chair",), ("x-ray viewer",)])
        con.commit(); con.close()
        for i in range(5):
            with open(os.path.join(up, "scan%d.jpg" % i), "wb") as fh:
                fh.write(os.urandom(2048))
        today = "assetapp_%s.tar.gz" % time.strftime("%Y-%m-%d")

        def aged(name, days):
            p = os.path.join(dest, name)
            open(p, "wb").write(b"old")
            t = time.time() - days * 86400
            os.utime(p, (t, t))
            return p

        now = dt.datetime(2026, 9, 17, 2, 30, tzinfo=IST)
        fake = FakeDrive()
        fac = lambda: (fake, "folder")

        # --- night 1: ships, verifies, pins the month, keeps 3 days locally
        a4, a2 = aged("assetapp_2026-09-13.tar.gz", 4.2), aged("assetapp_2026-09-15.tar.gz", 2.2)
        code, line = run(root, dest, True, now, fac)
        print("     " + line)
        check("night 1 is OK and exits 0", (code, "  OK    " in line), (0, True))
        check("the archive keeps the old name", os.path.isfile(os.path.join(dest, today)), True)
        with tarfile.open(os.path.join(dest, today), "r:gz") as tf:
            names = sorted(m.name for m in tf if m.isfile())
            tf.extract("assetapp/assets.db", os.path.join(base, "x"))
        check("members keep the old paths", (names[0], len(names)), ("assetapp/assets.db", 6))
        c = sqlite3.connect(os.path.join(base, "x", "assetapp", "assets.db"))
        check("the archived database opens with its rows", c.execute("SELECT COUNT(*) FROM asset").fetchone()[0], 2)
        c.close()
        check("Drive holds tonight's bytes, by md5", fake.files["id0"]["md5Checksum"], md5(os.path.join(dest, today)))
        check("the Drive file records fingerprint and md5", ("fp=" in fake.files["id0"]["description"],
              "md5=%s" % md5(os.path.join(dest, today)) in fake.files["id0"]["description"]), (True, True))
        check("the month is shipped and pinned", ("month=2026-09" in fake.files["id1"]["description"],
              fake.files["id1"]["revs"][-1]["keepForever"]), (True, True))
        check("with a verified Drive copy the box keeps 3 days (4-day gone)", os.path.exists(a4), False)
        check("and the 2-day archive stays", os.path.exists(a2), True)
        check("no .part and no snapshot left", [n for n in os.listdir(dest)
              if n.endswith(".part") or n.startswith(".assetapp_snap_")], [])

        # --- night 2: nothing changed -> no upload, still OK
        n_up = fake.uploads
        code2, line2 = run(root, dest, True, now + dt.timedelta(days=1), fac)
        check("an unchanged night uploads nothing", fake.uploads, n_up)
        check("and is still OK, saying Drive is current", (code2, "drive unchanged" in line2), (0, True))
        check("the month is not shipped twice", len(fake.files["id1"]["revs"]), 1)

        # --- night 3: a new photo -> ships again
        with open(os.path.join(up, "scan9.jpg"), "wb") as fh:
            fh.write(os.urandom(1024))
        code3, line3 = run(root, dest, True, now + dt.timedelta(days=2), fac)
        check("a new upload makes the night ship again", (code3, fake.uploads, "drive shipped" in line3),
              (0, n_up + 1, True))

        # --- a new month pins a new revision
        run(root, dest, True, dt.datetime(2026, 10, 1, 2, 30, tzinfo=IST), fac)
        check("a new month ships and pins again", ("month=2026-10" in fake.files["id1"]["description"],
              sum(1 for r in fake.files["id1"]["revs"] if r["keepForever"])), (True, 2))

        # --- Drive read-back mismatch -> PART, local keeps 14
        a5 = aged("assetapp_2026-09-12.tar.gz", 5.2)
        with open(os.path.join(up, "scan10.jpg"), "wb") as fh:
            fh.write(os.urandom(1024))
        fake.corrupt = True
        code4, line4 = run(root, dest, True, now, fac)
        check("a Drive copy that does not verify is PART, exit 1", (code4, "  PART  " in line4), (1, True))
        check("and says it did not verify", "DID NOT VERIFY" in line4, True)
        check("without a verified Drive copy the box keeps 14 days", os.path.exists(a5), True)
        fake.corrupt = False

        # --- Drive unreachable / slot missing / not configured
        fake.fail_list = True
        code5, line5 = run(root, dest, True, now, fac)
        check("Drive unreachable is PART with the reason", (code5, "HTTP 503" in line5), (1, True))
        fake.fail_list = False
        lonely = FakeDrive(slots=(NIGHTLY_SLOT,))
        code6, line6 = run(root, dest, True, now, lambda: (lonely, "folder"))
        check("a missing slot file is PART and names it", (code6, MONTHLY_SLOT in line6), (1, True))

        def unconfigured():
            raise RuntimeError("Drive not configured (FOLDER_ID blank in drive_backup.conf)")
        code7, line7 = run(root, dest, True, now, unconfigured)
        check("no Drive config is PART, not a crash", (code7, "not configured" in line7), (1, True))
        code8, line8 = run(root, dest, False, now, fac)
        check("--no-offsite runs the local leg and keeps 14", (code8, "keep 14 days" in line8), (1, True))

        # --- oversize archive is refused before upload
        global MAX_OFFSITE_BYTES
        saved, MAX_OFFSITE_BYTES = MAX_OFFSITE_BYTES, 10
        with open(os.path.join(up, "scan11.jpg"), "wb") as fh:
            fh.write(os.urandom(1024))
        before = fake.uploads
        code9, line9 = run(root, dest, True, now, fac)
        MAX_OFFSITE_BYTES = saved
        check("an archive over the limit is not shipped", (code9, fake.uploads, "nightly limit" in line9),
              (1, before, True))

        # --- local failures: nothing shipped, nothing pruned
        good_md5 = md5(os.path.join(dest, today))
        a16 = aged("assetapp_2026-09-01.tar.gz", 16.2)
        shutil.move(os.path.join(app, "uploads"), os.path.join(base, "away"))
        before = fake.uploads
        c10, l10 = run(root, dest, True, now, fac)
        check("missing uploads is a FAIL, nothing shipped", (c10, "  FAIL  " in l10, fake.uploads), (1, True, before))
        check("a flawed archive never replaces today's good one", md5(os.path.join(dest, today)), good_md5)
        check("a failed night prunes nothing", os.path.exists(a16), True)
        shutil.move(os.path.join(base, "away"), os.path.join(app, "uploads"))
        with open(os.path.join(app, "assets.db"), "r+b") as fh:
            fh.seek(100); fh.write(b"\x00" * 3000)
        c11, l11 = run(root, dest, True, now, fac)
        check("a damaged database is a FAIL before anything is written",
              (c11, md5(os.path.join(dest, today)), fake.uploads), (1, good_md5, before))
        os.remove(os.path.join(app, "assets.db"))
        c12, l12 = run(root, dest, True, now, fac)
        check("no database says where it looked", (c12, "not found" in l12), (1, True))
        check("every line is one line", all("\n" not in s for s in
              (line, line2, line3, line4, line5, line6, line7, line8, line9, l10, l11, l12)), True)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print("\nSELFTEST %s" % ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
