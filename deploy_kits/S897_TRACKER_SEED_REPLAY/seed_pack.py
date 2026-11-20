#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_pack.py -- kit S897 (the parent, S493, 20-Nov-2026): the PC half of the seed (plan S492 FINAL s1, s6.2).

Runs in the assistant's device VM with the owner's PC folders mounted (no step of his). It packs the Follow-up Tracker's
live state into ONE sealed zip, written into the tracker's own outputs\\ folder -- which Drive for Desktop syncs to the
clinic Drive folder the box already reads (docterz_ingest's folder). seed_take.py on the box fetches it from there.

WHAT GOES IN (byte for byte, every file hashed into SEED_MANIFEST.json):
  data/        the ledgers (visit, follow-up, revenue, call, patient master ...), their meta files, .secret_key, and
               data/backups/<date>_<time>_daily snapshots from --since on (Replay 2 needs them; older ones stay on the PC)
  uploads/     every input the state file or the console log names (the days' consultation reports, the follow-up logs,
               the S892 header-only files) -- the state's days[].input must resolve on the box or followup_alone goes blind
  archive/     D:\\Downloads\\DocterzArchive: _pickup_state.json, index.csv, _console.log, _pickup_log.txt, the KIND folders
               (CONSULTATION / FOLLOWUP_LOG / CLINICAL), _QUARANTINE, DOCTERZ_SHOUTS.txt -- not the PC-only fetch/send logs,
               not _outputs_before_run (the box's inbox holds the uploaded workbooks)
  feed_url.txt the Call_Feed URL (the runner fetches the feed itself from the switch evening on)
  replay/      processor.py.bak_S777_0e7c129f -- the engine before 10-Nov, for Replay 2 only
NEVER: a path, a name or a number printed. Counts and file names of the zip only.

    python3 seed_pack.py --live <tracker folder> --archive <DocterzArchive> [--out <folder>] [--since 2026-10-19] [--dry-run]
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import zipfile

VERSION = "S897.1"
SINCE_DEFAULT = "2026-10-19"
SNAP_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_(\d{6})_daily$")
ARCHIVE_TOP = ("_pickup_state.json", "index.csv", "_console.log", "_pickup_log.txt", "DOCTERZ_SHOUTS.txt")
ARCHIVE_DIRS = ("CONSULTATION", "FOLLOWUP_LOG", "CLINICAL", "_QUARANTINE")
OLD_ENGINE = "processor.py.bak_S777_0e7c129f"


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def walk_files(top):
    for root, dirs, files in os.walk(top):
        dirs.sort()
        for f in sorted(files):
            yield os.path.join(root, f)


def collect(live, archive, since):
    """[(zip name, source path)] -- the plan's list, nothing more."""
    out = []
    data = os.path.join(live, "data")
    if not os.path.isdir(data):
        raise SystemExit("REFUSING: %s has no data folder" % live)
    for p in walk_files(data):
        rel = os.path.relpath(p, data).replace(os.sep, "/")
        if rel.startswith("backups/"):
            top = rel.split("/", 1)[1].split("/", 1)[0]
            m = SNAP_RE.match(top)
            if not m or m.group(1) < since:
                continue
        if rel.endswith((".tmp", ".part", ".lock")) or "__pycache__" in rel:
            continue
        out.append(("data/" + rel, p))
    uploads = os.path.join(live, "uploads")
    if os.path.isdir(uploads):
        for p in walk_files(uploads):
            rel = os.path.relpath(p, uploads).replace(os.sep, "/")
            if rel.lower().endswith(".csv"):
                out.append(("uploads/" + rel, p))
    for name in ARCHIVE_TOP:
        p = os.path.join(archive, name)
        if os.path.exists(p):
            out.append(("archive/" + name, p))
    for d in ARCHIVE_DIRS:
        top = os.path.join(archive, d)
        if os.path.isdir(top):
            for p in walk_files(top):
                out.append(("archive/" + d + "/" + os.path.relpath(p, top).replace(os.sep, "/"), p))
    for name in ("feed_url.txt",):
        p = os.path.join(live, name)
        if os.path.exists(p):
            out.append((name, p))
    p = os.path.join(live, OLD_ENGINE)
    if os.path.exists(p):
        out.append(("replay/" + OLD_ENGINE, p))
    return out


def check_state(live, archive, entries):
    """every path the state names must be in the zip: counts of resolved / missing"""
    st_path = os.path.join(archive, "_pickup_state.json")
    with open(st_path, encoding="utf-8") as fh:
        st = json.load(fh)
    names = {os.path.basename(z).lower() for z, _ in entries}
    missing_arch = sum(1 for v in st.get("seen", {}).values()
                       if v.get("archived") and os.path.basename(str(v["archived"]).replace("\\", "/")).lower() not in names)
    missing_in = sum(1 for v in st.get("days", {}).values()
                     if v.get("input") and os.path.basename(str(v["input"]).replace("\\", "/")).lower() not in names)
    return len(st.get("seen", {})), len(st.get("days", {})), missing_arch, missing_in


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", required=True, help="the PC's tracker folder (processor.py beside data/)")
    ap.add_argument("--archive", required=True, help="the PC's DocterzArchive folder")
    ap.add_argument("--out", default="", help="where the zip goes (default: <live>/outputs)")
    ap.add_argument("--since", default=SINCE_DEFAULT, help="snapshots from this day on (Replay 2's month)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    live, archive = os.path.abspath(a.live), os.path.abspath(a.archive)
    if not os.path.exists(os.path.join(live, "processor.py")):
        raise SystemExit("REFUSING: %s holds no processor.py" % live)
    if not os.path.exists(os.path.join(archive, "_pickup_state.json")):
        raise SystemExit("REFUSING: %s holds no _pickup_state.json" % archive)
    out_dir = a.out or os.path.join(live, "outputs")
    entries = collect(live, archive, a.since)
    seen, days, miss_a, miss_i = check_state(live, archive, entries)
    counts = {"data": sum(1 for z, _ in entries if z.startswith("data/") and not z.startswith("data/backups/")),
              "snapshots": len({z.split("/")[2] for z, _ in entries if z.startswith("data/backups/")}),
              "uploads": sum(1 for z, _ in entries if z.startswith("uploads/")),
              "archive": sum(1 for z, _ in entries if z.startswith("archive/")),
              "other": sum(1 for z, _ in entries if not z.startswith(("data/", "uploads/", "archive/")))}
    print("seed_pack %s: %d files (%d ledgers/meta, %d snapshots since %s, %d uploads, %d archive, %d other); state seen %d, days %d"
          % (VERSION, len(entries), counts["data"], counts["snapshots"], a.since, counts["uploads"], counts["archive"], counts["other"], seen, days))
    if miss_a or miss_i:
        print("REFUSING: the state names %d archived file(s) and %d input(s) that are not in the pack" % (miss_a, miss_i))
        return 2
    print("state: every archived file and every day's input is in the pack")
    if a.dry_run:
        print("dry run -- nothing written")
        return 0
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    name = "TRACKER_SEED_%s.zip" % stamp
    os.makedirs(out_dir, exist_ok=True)
    tmp = os.path.join(out_dir, name + ".part")
    manifest = {"version": VERSION, "stamp": stamp, "since": a.since, "counts": counts,
                "pc_tracker_prefix": live, "pc_archive_prefix": archive, "files": {}}
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        for z, p in entries:
            zf.write(p, z)
            manifest["files"][z] = md5_of(p)
        zf.writestr("SEED_MANIFEST.json", json.dumps(manifest, indent=1, sort_keys=True))
    final = os.path.join(out_dir, name)
    os.replace(tmp, final)
    digest = sha256_of(final)
    with open(final + ".sha256", "w", encoding="utf-8") as fh:
        fh.write("%s  %s\n" % (digest, name))
    print("written: %s (%s bytes) + .sha256" % (name, "{:,}".format(os.path.getsize(final))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
