#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
medical_inventory.py  --  S201.  Read-only census of the medical PC's Marg
exports, and a recent-files sweep for anything the pipeline cannot see.

    python medical_inventory.py                 # census of the known folders
    python medical_inventory.py recent 3        # EVERY file changed in 3 days

WHY THE SWEEP EXISTS
    The first version of this census only counted .xls/.xlsx -- the same
    filter the watcher uses. That makes "0 not captured" circular: it can only
    ever find files the watcher already accepts. Marg also writes PDF, CSV and
    DBF, and it can save outside the two folders we watch. The sweep answers
    the question the census structurally cannot: "what did Marg actually write
    on this machine today, of any kind, anywhere on D:?"

Writes nothing on the medical PC.
"""

import datetime as dt
import hashlib
import io
import os
import sys

MEDICAL = r"\\100.119.151.40\DDrive"
ARCHIVE = r"D:\Downloads\margsync\MargArchive"
OUT = r"D:\Downloads\margsync\MEDICAL_INVENTORY.txt"
OUT_RECENT = r"D:\Downloads\margsync\MEDICAL_RECENT.txt"

LOOK_IN = [
    (r"MARGERP\users", "Marg's own output slots (overwritten each run)"),
    (r"MARG REPORTS", "saved by hand by Dr Manoj"),
    (r"SendToClinic\_captured", "the resident watcher's capture spool"),
    (r"SendToClinic\Sent", "dated copies kept by the sender"),
    (r"SendToClinic\NEEDS_UPLOAD", "sends that failed and were parked"),
]

# What the watcher will pick up. Everything else on this machine is invisible
# to the pipeline, which is precisely what we want flagged.
# S201: .pdf added -- the watcher now captures PDFs, so a PDF is no longer an
# invisible file and must not be reported as one. This list has to track the
# watcher's, or the census goes back to grading the pipeline's homework with
# the pipeline's own answers.
WATCHED_EXTS = (".xls", ".xlsx", ".pdf")

# Never walked: bulk that would take hours across the network and holds no
# exports. Marg's own database and encrypted backups live here.
SKIP_DIRS = {"data", "backup", "backtemp", "pyportable", "__pycache__",
             "xlrd", "temp", "usertemp", "system", "_old",
             "$recycle.bin", "system volume information"}
SKIP_EXTS = {".jmbkh", ".mbk", ".dll", ".exe", ".zip", ".log", ".tmp",
             ".dbf", ".cdx", ".fpt", ".ini", ".dat", ".bak"}
MAX_HASH_BYTES = 25 * 1024 * 1024


def md5_of(path, chunk=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def title_of(path):
    low = path.lower()
    if not low.endswith(WATCHED_EXTS):
        return None
    if low.endswith(".pdf"):
        return "(PDF - no readable report title)"
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        if low.endswith(".xlsx"):
            import xlsx_stdlib
            sh = xlsx_stdlib.open_workbook(path).sheet_by_index(0)
        else:
            import xlrd
            sh = xlrd.open_workbook(path).sheet_by_index(0)
        for r in range(min(8, sh.nrows)):
            v = str(sh.cell_value(r, 0)).strip()
            if len(v) > 12 and any(w in v.upper() for w in
                                   ("STATEMENT", "REPORT", "SALE", "PURCHASE",
                                    "STOCK", "EXPIRY", "LIST")):
                return v
        return "(no title row found)"
    except Exception as e:
        return "(unreadable: %s)" % e.__class__.__name__


def archive_md5s(archive):
    """md5 -> description, from the router's index AND from the archive's own
    files on disk.

    The index alone is not trustworthy, but NOT for the reason first recorded
    here. There is no re-filing code path at all: marg_router.py blacklists a
    file by content md5 the moment it is indexed --

        if digest in seen:
            out("  = already indexed, skipping"); return None

    -- and append_index() opens index.csv in "a" mode with no update path. So
    once a file is indexed as UNKNOWN it can never be re-examined, whatever
    the registry later learns, and its row can never be corrected.

    The two July purchase reports sitting correctly in PURCHASE_BILLWISE/ and
    PURCHASE_SUPPLIERWISE/ are hand-made copies placed out-of-band when the
    purchase signatures were added on 23-Aug -- byte-identical duplicates with
    no .txt sidecar, whose mtimes match the minute the folders were created
    rather than the copy2-preserved source mtimes. The originals are still in
    _UNKNOWN/ and the index still calls them unidentifiable.

    Same fault, other victims: 633a54d3 and fbea55de (stock-expiry) are frozen
    in _REFUSED though their title matches today's registry. Every signature
    added strands whatever it should have rescued.

    So: read the index, then hash what is actually filed, and let the disk win.
    """
    import csv
    out, from_index = {}, {}
    path = os.path.join(archive, "index.csv")
    if os.path.exists(path):
        with io.open(path, "r", encoding="utf-8", errors="replace",
                     newline="") as fh:
            rows = list(csv.reader(fh))
        if rows:
            hdr = rows[0]
            for r in rows[1:]:
                if len(r) < len(hdr):
                    continue
                d = dict(zip(hdr, r))
                m = (d.get("md5") or "").strip().lower()
                if m:
                    from_index[m] = "%s %s %s->%s" % (
                        d.get("verdict", "?"), d.get("type", "?"),
                        d.get("date_from", ""), d.get("date_to", ""))
    out.update(from_index)

    # The archive's real contents. Small enough to hash every run.
    disagreements = []
    if os.path.isdir(archive):
        for base, dirs, files in os.walk(archive):
            dirs[:] = [d for d in dirs
                       if d.lower() not in ("_spool", "_outbox", "__pycache__")]
            rel = os.path.relpath(base, archive)
            top = rel.split(os.sep)[0] if rel != "." else ""
            for f in files:
                if not f.lower().endswith(WATCHED_EXTS):
                    continue
                fp = os.path.join(base, f)
                try:
                    if os.path.getsize(fp) > MAX_HASH_BYTES:
                        continue
                    m = md5_of(fp)
                except Exception:
                    continue
                filed = "filed as %s" % (top or "(archive root)")
                if m in from_index and top and not top.startswith("_"):
                    if top.split("_")[0].upper() not in from_index[m].upper():
                        disagreements.append((m, from_index[m], top))
                out[m] = filed if top and not top.startswith("_") \
                    else out.get(m, filed)
    if disagreements:
        out["__disagreements__"] = disagreements
    return out


def walk(root, all_ext=True):
    found = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in SKIP_EXTS:
                continue
            if not all_ext and ext not in WATCHED_EXTS:
                continue
            p = os.path.join(base, f)
            try:
                st = os.stat(p)
            except Exception:
                continue
            found.append((p, st.st_size, st.st_mtime))
    return found


def _emit(lines):
    def say(s=""):
        print(s)
        lines.append(s)
    return say


def _write(lines, out):
    try:
        with io.open(out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("\n(written to %s)" % out)
    except Exception as e:
        print("\n(could not write %s: %s)" % (out, e))


def census():
    lines = []
    say = _emit(lines)
    say("MEDICAL PC -- Marg export census   %s"
        % dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    say("share: %s" % MEDICAL)
    say("counting EVERY file type, not only the .xls/.xlsx the watcher takes")
    say()
    if not os.path.isdir(MEDICAL):
        say("CANNOT REACH THE MEDICAL PC at %s" % MEDICAL)
        say("Is it switched on and is Tailscale connected?")
        _write(lines, OUT)
        return 1

    known = archive_md5s(ARCHIVE)
    disagree = known.pop("__disagreements__", [])
    say("archive holds %d known files" % len(known))
    if disagree:
        say()
        say("INDEX DISAGREES WITH THE ARCHIVE for %d file(s) -- the router's"
            % len(disagree))
        say("index.csv was never corrected when these were re-filed:")
        for m, idx, top in disagree:
            say("   %s  index says [%s]  but it is filed under %s"
                % (m[:8], idx.strip(), top))
    say()

    total, missed, invisible = 0, [], []
    for rel, why in LOOK_IN:
        root = os.path.join(MEDICAL, rel)
        say("=" * 78)
        say("%s   -- %s" % (rel, why))
        if not os.path.isdir(root):
            say("   (folder does not exist on the medical PC)")
            say()
            continue
        items = sorted(walk(root), key=lambda t: t[2], reverse=True)
        if not items:
            say("   (empty)")
            say()
            continue
        for p, size, mtime in items:
            total += 1
            when = dt.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            watched = p.lower().endswith(WATCHED_EXTS)
            try:
                m = md5_of(p) if size <= MAX_HASH_BYTES else "(too big)"
            except Exception as e:
                say("   %s  %s  COULD NOT READ (%s)"
                    % (when, os.path.relpath(p, root), e.__class__.__name__))
                continue
            state = known.get(m)
            if not watched:
                mark = "INVISIBLE to the watcher (not .xls/.xlsx)"
                invisible.append((when, p))
            elif state:
                mark = "captured"
            else:
                mark = "NOT CAPTURED"
                missed.append((when, p, m))
            say("   %s  %9d  %s  %s" % (when, size, m[:8], mark))
            say("        %s" % os.path.relpath(p, root))
            t = title_of(p)
            if t:
                say("        title: %s" % t)
            if state:
                say("        archive: %s" % state)
            say()

    say("=" * 78)
    say("files seen on the medical PC        : %d" % total)
    say("watched type but NOT in the archive : %d" % len(missed))
    say("types the watcher cannot see at all : %d" % len(invisible))
    if missed:
        say()
        say("Watched files the pull never filed:")
        for when, p, m in sorted(missed, reverse=True):
            say("   %s  %s  %s" % (when, m[:8], p))
    if invisible:
        say()
        say("These are NOT .xls/.xlsx, so the watcher ignores them entirely.")
        say("A report exported as PDF lands here and never reaches the clinic:")
        for when, p in sorted(invisible, reverse=True)[:40]:
            say("   %s  %s" % (when, p))
    if not missed and not invisible:
        say("Every file in the watched folders is a watched type and captured.")
    _write(lines, OUT)
    return 0


def recent(days):
    lines = []
    say = _emit(lines)
    cutoff = dt.datetime.now() - dt.timedelta(days=days)
    say("MEDICAL PC -- EVERYTHING written in the last %d day(s)   %s"
        % (days, dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    say("share: %s   (whole drive, any file type)" % MEDICAL)
    say("cutoff: %s" % cutoff.strftime("%Y-%m-%d %H:%M:%S"))
    say()
    if not os.path.isdir(MEDICAL):
        say("CANNOT REACH THE MEDICAL PC at %s" % MEDICAL)
        _write(lines, OUT_RECENT)
        return 1

    known = archive_md5s(ARCHIVE)
    known.pop("__disagreements__", None)
    hits = []
    for base, dirs, files in os.walk(MEDICAL):
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS]
        for f in files:
            if os.path.splitext(f)[1].lower() in SKIP_EXTS:
                continue
            p = os.path.join(base, f)
            try:
                st = os.stat(p)
            except Exception:
                continue
            if dt.datetime.fromtimestamp(st.st_mtime) >= cutoff:
                hits.append((p, st.st_size, st.st_mtime))

    hits.sort(key=lambda t: t[2], reverse=True)
    if not hits:
        say("Nothing at all was written on D: in the last %d day(s)." % days)
        say("If you generated a report in that window, Marg did not save it")
        say("to this drive -- check the save path in the Marg export dialog.")
    for p, size, mtime in hits:
        when = dt.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        watched = p.lower().endswith(WATCHED_EXTS)
        m = ""
        try:
            if size <= MAX_HASH_BYTES:
                m = md5_of(p)
        except Exception:
            m = ""
        tag = "captured" if (m and m in known) else (
            "NOT CAPTURED" if watched else "not a watched type")
        say("   %s  %9d  %-14s %s" % (when, size, tag, p.replace(MEDICAL, "D:")))
        t = title_of(p)
        if t:
            say("        title: %s" % t)
    say()
    say("=" * 78)
    say("files written in the last %d day(s): %d" % (days, len(hits)))
    _write(lines, OUT_RECENT)
    return 0


def main():
    a = sys.argv[1:]
    if a and a[0].lower() == "recent":
        return recent(int(a[1]) if len(a) > 1 else 3)
    return census()


if __name__ == "__main__":
    sys.exit(main())
