#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_take.py -- kit S897 (the parent, S493, 20-Nov-2026): the box half of the seed (plan S492 FINAL s1, s6.2).

Takes the sealed seed seed_pack.py wrote on the PC (TRACKER_SEED_<stamp>.zip + .sha256, synced by Drive into the clinic
folder docterz_ingest already reads) and puts the Follow-up Tracker's live state into /root/followup_tracker/:

  1. FETCH: the newest TRACKER_SEED_*.zip in the Drive folder and its .sha256, with the box's own read-only credential
     (docterz_ingest's), or a local pair given with --zip. The sha256 must agree or nothing is unpacked.
  2. REFUSE while anything is live: /root/followup_tracker/SWITCHED_AT present (the server's ledgers are the live ones --
     a seed never overwrites them); the OFF file absent (the runner may be mid-pass); a ledger already there unless --again
     (then the old data/, uploads/, archive/ go whole into _seed_before_<stamp>/, never deleted).
  3. TRANSLATE the PC's paths in _pickup_state.json (seen[].archived, days[].input) and index.csv (archived_path) to the
     box's: ...\\DocterzArchive\\X -> <root>/archive/X, ...\\followup_tracker\\uploads\\Y -> <root>/uploads/Y. Every
     translated path must exist in the unpacked seed, or nothing is placed (followup_alone and pick_followup read them).
  4. PLACE: data/ 700 and its files 600 (they carry patients), uploads/, archive/, feed_url.txt, replay/; SEEDED_AT written
     with the seed's stamp and counts. The runner stays OFF; the switch evening is session 3's.
NEVER prints a patient detail: counts, dates, the zip's name.

    /root/wa/venv/bin/python3 -B seed_take.py [--root /root/followup_tracker] [--zip <path>] [--again] [--dry-run] [--check]
"""
import argparse
import datetime as dt
import glob
import hashlib
import io
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import zipfile

VERSION = "S897.1"
ROOT_DEFAULT = os.environ.get("FUT_ROOT", "/root/followup_tracker")
FIN = os.environ.get("FIN_DIR", "/root/finance")
NAME_RE = re.compile(r"^TRACKER_SEED_(\d{8}-\d{6})\.zip$")
SNAP_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_(\d{6})_daily$")
MOVED = ("data", "uploads", "archive", "replay", "feed_url.txt")


def say(msg):
    print(msg, flush=True)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ── 1 fetch ────────────────────────────────────────────────────────────────────────────────────────
def drive_newest(scratch):
    """(zip path, sha path) of the newest seed in the Drive folder, downloaded into scratch; None when none."""
    if FIN not in sys.path:
        sys.path.insert(0, FIN)
    import docterz_ingest as DI                                 # noqa: PLC0415 -- the box's own credential and folder
    cred, requests = DI._drive()
    q = "'%s' in parents and trashed=false and name contains 'TRACKER_SEED_'" % DI.FOLDER_ID
    files, token = [], None
    while True:
        p = {"q": q, "fields": "nextPageToken,files(id,name,modifiedTime,size)", "pageSize": 200}
        if token:
            p["pageToken"] = token
        r = requests.get("https://www.googleapis.com/drive/v3/files", params=p,
                         headers={"Authorization": "Bearer " + cred.token}, timeout=60)
        r.raise_for_status()
        j = r.json()
        files += j.get("files", [])
        token = j.get("nextPageToken")
        if not token:
            break
    zips = sorted([f for f in files if NAME_RE.match(f["name"])], key=lambda f: f["name"])
    if not zips:
        return None, None, len(files)
    z = zips[-1]
    s = next((f for f in files if f["name"] == z["name"] + ".sha256"), None)
    if s is None:
        raise SystemExit("REFUSING: %s is in Drive but its .sha256 is not (sync still on its way?)" % z["name"])
    zp, sp = os.path.join(scratch, z["name"]), os.path.join(scratch, s["name"])
    for f, dest in ((z, zp), (s, sp)):
        raw = DI.fetch_bytes(f["id"])
        with open(dest, "wb") as fh:
            fh.write(raw)
        os.chmod(dest, 0o600)
    return zp, sp, len(files)


def verify(zp, sp):
    with open(sp, encoding="utf-8") as fh:
        line = fh.readline().split()
    if not line or len(line[0]) != 64:
        raise SystemExit("REFUSING: the .sha256 file is not of the expected shape")
    got = sha256_of(zp)
    if got != line[0]:
        raise SystemExit("REFUSING: sha256 of %s does not agree with its .sha256 -- not unpacked" % os.path.basename(zp))
    return True


# ── 3 translate ────────────────────────────────────────────────────────────────────────────────────
def translate(path, root):
    """a PC path -> the box path, by the last folder the seed keeps; '' when it is not one of the seed's"""
    s = str(path or "").replace("\\", "/")
    low = s.lower()
    best = None                                                  # the innermost key wins, whatever its order
    for key, sub in (("/docterzarchive/", "archive"), ("/followup_tracker/uploads/", "uploads"),
                     ("/followup_tracker/data/", "data"), ("/followup_tracker/outputs/", "outputs")):
        i = low.rfind(key)
        if i >= 0 and (best is None or i > best[0]):
            best = (i, key, sub)
    if best is None:
        return ""
    i, key, sub = best
    return os.path.join(root, sub, s[i + len(key):])


def translate_state(unpacked, root):
    p = os.path.join(unpacked, "archive", "_pickup_state.json")
    with open(p, encoding="utf-8") as fh:
        st = json.load(fh)
    stats = {"seen": 0, "seen_missing": 0, "days": 0, "days_missing": 0}
    for v in st.get("seen", {}).values():
        if v.get("archived"):
            t = translate(v["archived"], root)
            v["archived"] = t
            stats["seen"] += 1
            if not t or not os.path.exists(os.path.join(unpacked, os.path.relpath(t, root))):
                stats["seen_missing"] += 1
    for v in st.get("days", {}).values():
        if v.get("input"):
            t = translate(v["input"], root)
            v["input"] = t
            stats["days"] += 1
            if not t or not os.path.exists(os.path.join(unpacked, os.path.relpath(t, root))):
                stats["days_missing"] += 1
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=1, sort_keys=True)
    ip = os.path.join(unpacked, "archive", "index.csv")
    if os.path.exists(ip):
        import csv                                              # noqa: PLC0415
        with open(ip, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.reader(fh))
        if rows and "archived_path" in rows[0]:
            k = rows[0].index("archived_path")
            for r in rows[1:]:
                if len(r) > k and r[k]:
                    r[k] = translate(r[k], root) or r[k]
            with open(ip, "w", encoding="utf-8", newline="") as fh:
                csv.writer(fh).writerows(rows)
    return stats


# ── 4 place ────────────────────────────────────────────────────────────────────────────────────────
def harden(top):
    for r, ds, fs in os.walk(top):
        os.chmod(r, 0o700)
        for f in fs:
            os.chmod(os.path.join(r, f), 0o600)


def place(unpacked, root, stamp, again, dry):
    moved_aside = ""
    if again:
        moved_aside = os.path.join(root, "_seed_before_%s" % dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
        if not dry:
            os.makedirs(moved_aside, mode=0o700)
            for n in MOVED:
                p = os.path.join(root, n)
                if os.path.exists(p):
                    shutil.move(p, os.path.join(moved_aside, n))
    if not dry:
        for n in MOVED:
            src = os.path.join(unpacked, n)
            if os.path.exists(src):
                dest = os.path.join(root, n)
                if os.path.isdir(dest):
                    shutil.rmtree(dest)                           # only an EMPTY folder the installer made (checked by caller)
                shutil.move(src, dest)
        for n in ("data", "uploads", "archive", "replay"):
            if os.path.isdir(os.path.join(root, n)):
                harden(os.path.join(root, n))
        if os.path.exists(os.path.join(root, "feed_url.txt")):
            os.chmod(os.path.join(root, "feed_url.txt"), 0o600)
    return moved_aside


def counts_of(root):
    data = os.path.join(root, "data")
    ledgers = len([f for f in glob.glob(os.path.join(data, "*.csv"))])
    snaps = len([d for d in glob.glob(os.path.join(data, "backups", "*_daily")) if SNAP_RE.match(os.path.basename(d))])
    ups = len(glob.glob(os.path.join(root, "uploads", "*.csv")))
    arch = sum(len(fs) for _, _, fs in os.walk(os.path.join(root, "archive")))
    return ledgers, snaps, ups, arch


def check(root):
    """--check: what the folder holds, and whether the state resolves (counts only)"""
    if not os.path.exists(os.path.join(root, "SEEDED_AT")):
        say("not seeded: %s has no SEEDED_AT" % root)
        return 1
    with open(os.path.join(root, "SEEDED_AT"), encoding="utf-8") as fh:
        say("seeded: " + fh.read().strip().splitlines()[0])
    sp = os.path.join(root, "archive", "_pickup_state.json")
    with open(sp, encoding="utf-8") as fh:
        st = json.load(fh)
    sm = sum(1 for v in st.get("seen", {}).values() if v.get("archived") and not os.path.exists(v["archived"]))
    dm = sum(1 for v in st.get("days", {}).values() if v.get("input") and not os.path.exists(v["input"]))
    l, s, u, a = counts_of(root)
    say("ledgers %d, snapshots %d, uploads %d, archive files %d; state seen %d (%d unresolved), days %d (%d unresolved)"
        % (l, s, u, a, len(st.get("seen", {})), sm, len(st.get("days", {})), dm))
    return 0 if not (sm or dm) else 2


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=ROOT_DEFAULT)
    ap.add_argument("--zip", default="", help="a local seed zip (its .sha256 beside it); default: the newest in Drive")
    ap.add_argument("--again", action="store_true", help="re-seed: the present data/uploads/archive go into _seed_before_<stamp>/")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    root = a.root
    if a.check:
        return check(root)
    if not os.path.exists(os.path.join(root, "processor.py")):
        raise SystemExit("REFUSING: %s holds no processor.py (S895 not installed)" % root)
    if os.path.exists(os.path.join(root, "SWITCHED_AT")):
        raise SystemExit("REFUSING: %s/SWITCHED_AT is present -- the server's ledgers are live; a seed never overwrites them" % root)
    if not os.path.exists(os.path.join(root, "OFF")):
        raise SystemExit("REFUSING: %s/OFF is absent -- the runner may be running; put the OFF file first" % root)
    have = glob.glob(os.path.join(root, "data", "*.csv"))
    if have and not a.again:
        raise SystemExit("REFUSING: %s/data already holds %d ledger(s) -- say --again to set them aside and seed afresh" % (root, len(have)))
    scratch = tempfile.mkdtemp(prefix="s897seed.", dir="/tmp")
    os.chmod(scratch, 0o700)
    try:
        if a.zip:
            zp, sp = a.zip, a.zip + ".sha256"
            if not os.path.exists(sp):
                raise SystemExit("REFUSING: %s has no .sha256 beside it" % os.path.basename(zp))
            say("seed: %s (local)" % os.path.basename(zp))
        else:
            zp, sp, n = drive_newest(scratch)
            if not zp:
                raise SystemExit("no TRACKER_SEED_*.zip in the Drive folder (%d file(s) seen) -- has the PC's outputs folder synced?" % n)
            say("seed: %s (Drive)" % os.path.basename(zp))
        verify(zp, sp)
        stamp = NAME_RE.match(os.path.basename(zp)).group(1)
        unpacked = os.path.join(scratch, "unpacked")
        os.makedirs(unpacked, mode=0o700)
        with zipfile.ZipFile(zp) as zf:
            for m in zf.infolist():
                if m.filename.startswith(("/", "..")) or "/../" in m.filename:
                    raise SystemExit("REFUSING: the zip carries an unsafe path")
            zf.extractall(unpacked)
        man_p = os.path.join(unpacked, "SEED_MANIFEST.json")
        if not os.path.exists(man_p):
            raise SystemExit("REFUSING: the seed carries no SEED_MANIFEST.json")
        with open(man_p, encoding="utf-8") as fh:
            man = json.load(fh)
        bad = 0
        for rel, want in man.get("files", {}).items():
            p = os.path.join(unpacked, rel)
            if not os.path.exists(p):
                bad += 1
                continue
            h = hashlib.md5(open(p, "rb").read()).hexdigest()
            if h != want:
                bad += 1
        if bad:
            raise SystemExit("REFUSING: %d file(s) in the zip do not agree with its manifest" % bad)
        say("sha256 agrees; manifest %d files, all agree (seed stamp %s, since %s)" % (len(man.get("files", {})), stamp, man.get("since", "?")))
        for need in ("archive/_pickup_state.json", "data"):
            if not os.path.exists(os.path.join(unpacked, need)):
                raise SystemExit("REFUSING: the seed has no %s" % need)
        stt = translate_state(unpacked, root)
        say("paths translated: seen %d (%d unresolved), days %d (%d unresolved)" % (stt["seen"], stt["seen_missing"], stt["days"], stt["days_missing"]))
        if stt["seen_missing"] or stt["days_missing"]:
            raise SystemExit("REFUSING: the state names files the seed does not carry -- nothing placed")
        if a.dry_run:
            say("dry run -- nothing placed")
            return 0
        for n in ("data", "uploads", "archive", "replay"):        # S895's installer made them empty; anything else is --again's
            p = os.path.join(root, n)
            if os.path.isdir(p) and os.listdir(p) and not a.again:
                raise SystemExit("REFUSING: %s is not empty -- say --again" % p)
        aside = place(unpacked, root, stamp, a.again, a.dry_run)
        l, s, u, ar = counts_of(root)
        with open(os.path.join(root, "SEEDED_AT"), "w", encoding="utf-8") as fh:
            fh.write("%s seed %s (since %s): ledgers %d, snapshots %d, uploads %d, archive files %d%s\n"
                     % (dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), stamp, man.get("since", "?"), l, s, u, ar,
                        ("; the earlier seed set aside in " + os.path.basename(aside)) if aside else ""))
        os.chmod(os.path.join(root, "SEEDED_AT"), 0o600)
        say("PLACED: ledgers %d, snapshots %d, uploads %d, archive files %d%s; runner still OFF"
            % (l, s, u, ar, ("; earlier seed in " + os.path.basename(aside)) if aside else ""))
        return check(root)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    os.environ.setdefault("TZ", "Asia/Kolkata")
    sys.exit(main())
