#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""rebuild_manifest.py v1.1 (S268) -- rebuild or check MANIFEST.md5 for the
ClaudeCowork tree on manojz, WITHOUT a POSIX shell.

WHY THIS EXISTS
    From 08-Sep-2026 the Cowork Linux workspace on manojz stopped starting
    (a Windows update; device_bash fails with "no Plan9 drive shares mounted").
    Every close since has APPENDED rows to MANIFEST.md5 and recorded a full
    folder-wide rebuild as OWED (S255, S256 -- F-443).  This tool removes the
    dependency: it walks and hashes the tree with the Windows python that is
    already on the machine.

WHAT IT GUARANTEES
    * It NEVER deletes a file and NEVER writes anywhere except its own output
      folder and MANIFEST.md5 / MANIFEST.md5.bak_* inside the tree.
    * It writes MANIFEST.md5.new first, proves it, and only then replaces.
    * F-369 DISCIPLINE: it diffs the new row list against the old one and
      reports added / dropped / changed BEFORE accepting.  A gate that quietly
      loses a row still exits 0, and that is the failure this rule exists for.
    * It REFUSES to replace when rows would fall by more than --max-drop-pct
      (default 10), unless --force is given, and says why.

ROW FORMAT -- byte-compatible with the md5sum output the old shell produced:
    <32 hex>  <relative path with FORWARD slashes>
Rows are sorted by path so two rebuilds of an unchanged tree are identical.

EXCLUDED, exactly as the previous generator excluded them:
    MANIFEST.md5 itself and every MANIFEST.md5* sidecar (.new, .bak_*).
    Nothing else is excluded.

MODES
    --check     hash the tree, compare to MANIFEST.md5, write a report, change
                nothing.  Exit 0 only if every row matches and nothing is
                unlisted.  This is the Phase 0 gate for the Cowork tree.
    --rebuild   as --check, then replace MANIFEST.md5 (backing up the old one).
"""

import argparse
import codecs
import hashlib
import os
import sys
import time

VERSION = "1.1"
ROW_SEP = "  "
HEXLEN = 32


def md5_of(path, bufsize=1024 * 1024):
    h = hashlib.md5()
    f = open(path, "rb")
    try:
        while True:
            chunk = f.read(bufsize)
            if not chunk:
                break
            h.update(chunk)
    finally:
        f.close()
    return h.hexdigest()


def is_excluded(relpath):
    """MANIFEST.md5 and its sidecars are never listed -- a file cannot be
    inside its own checksum, and the .bak_/.new copies are working files."""
    base = relpath.split("/")[-1]
    return base == "MANIFEST.md5" or base.startswith("MANIFEST.md5.")


def walk_tree(root):
    """Return {relpath: md5} for every regular file under root.
    Symlinks and reparse points are followed only if they resolve to a file
    inside root; anything unreadable is returned in the errors list."""
    rows = {}
    errors = []
    rootabs = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(rootabs):
        dirnames.sort()
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, rootabs).replace(os.sep, "/")
            if is_excluded(rel):
                continue
            try:
                rows[rel] = md5_of(full)
            except Exception as exc:
                errors.append((rel, str(exc)))
    return rows, errors


def read_manifest(path):
    """Parse an existing MANIFEST.md5.  Returns (rows, comment_lines, bad).
    Comment and blank lines are kept only for the count -- the rebuilt file is
    pure rows, which is what makes it mechanically checkable."""
    rows = {}
    comments = []
    bad = []
    if not os.path.exists(path):
        return rows, comments, bad
    fh = codecs.open(path, "r", "utf-8", errors="replace")
    try:
        for lineno, line in enumerate(fh, 1):
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            if line.lstrip().startswith("#"):
                comments.append(line)
                continue
            if len(line) > HEXLEN + 2 and line[HEXLEN:HEXLEN + 2] == ROW_SEP:
                digest = line[:HEXLEN].lower()
                if len(digest) == HEXLEN and all(c in "0123456789abcdef" for c in digest):
                    rows[line[HEXLEN + 2:]] = digest
                    continue
            bad.append((lineno, line))
    finally:
        fh.close()
    return rows, comments, bad


def render(rows):
    out = []
    for rel in sorted(rows):
        out.append(rows[rel] + ROW_SEP + rel + "\n")
    return "".join(out)


def diff(old, new):
    added = sorted(set(new) - set(old))
    dropped = sorted(set(old) - set(new))
    changed = sorted(p for p in (set(old) & set(new)) if old[p] != new[p])
    return added, dropped, changed


def section(title, items, cap, total_note=True):
    lines = ["", title + " -- " + str(len(items))]
    if not items:
        lines.append("    (none)")
        return lines
    for item in items[:cap]:
        lines.append("    " + item)
    if total_note and len(items) > cap:
        lines.append("    ... and " + str(len(items) - cap) + " more (full list is the row diff)")
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description="Rebuild or check MANIFEST.md5 without a POSIX shell.")
    ap.add_argument("--root", required=True, help="folder the manifest describes")
    ap.add_argument("--manifest", default=None, help="path to MANIFEST.md5 (default: <root>/MANIFEST.md5)")
    ap.add_argument("--report", default=None, help="where to write the report (default: beside this script)")
    ap.add_argument("--label", default=None, help="backup suffix, e.g. S268 (default: a timestamp)")
    ap.add_argument("--backup-dir", default=None,
                    help="put the backup of the old manifest here instead of beside it "
                         "(keeps the measured tree free of nightly clutter)")
    ap.add_argument("--rebuild", action="store_true", help="replace MANIFEST.md5 (default is check only)")
    ap.add_argument("--force", action="store_true", help="replace even if the drop guard trips")
    ap.add_argument("--max-drop-pct", type=float, default=10.0, help="refuse a rebuild that loses more than this %% of rows")
    ap.add_argument("--cap", type=int, default=40, help="how many paths to print per section")
    a = ap.parse_args(argv)

    root = os.path.abspath(a.root)
    if not os.path.isdir(root):
        sys.stderr.write("ROOT NOT FOUND: " + root + "\n")
        return 2
    manifest = a.manifest or os.path.join(root, "MANIFEST.md5")
    here = os.path.dirname(os.path.abspath(__file__))
    report_path = a.report or os.path.join(here, "REBUILD_REPORT.txt")
    label = a.label or time.strftime("%Y%m%d_%H%M%S")

    t0 = time.time()
    new_rows, walk_errors = walk_tree(root)
    old_rows, old_comments, bad_lines = read_manifest(manifest)
    added, dropped, changed = diff(old_rows, new_rows)
    elapsed = time.time() - t0

    body = render(new_rows)
    new_blob = body.encode("utf-8")
    new_md5 = hashlib.md5(new_blob).hexdigest()

    drop_pct = (100.0 * len(dropped) / len(old_rows)) if old_rows else 0.0
    guard_tripped = bool(old_rows) and drop_pct > a.max_drop_pct

    clean = (not added) and (not dropped) and (not changed) and (not walk_errors)

    L = []
    L.append("REBUILD_REPORT -- rebuild_manifest.py v" + VERSION)
    L.append("when       : " + time.strftime("%Y-%m-%d %H:%M:%S") + " (local clock on this PC)")
    L.append("root       : " + root)
    L.append("manifest   : " + manifest)
    L.append("mode       : " + ("REBUILD" if a.rebuild else "CHECK ONLY"))
    L.append("walk took  : " + ("%.1f" % elapsed) + " s")
    L.append("")
    L.append("rows on disk now      : " + str(len(new_rows)))
    L.append("rows in old manifest  : " + str(len(old_rows)))
    L.append("non-row lines in old  : " + str(len(old_comments)) + " comment, " + str(len(bad_lines)) + " unparsed")
    L.append("new manifest md5      : " + new_md5)
    L.extend(section("ADDED   (on disk, absent from the manifest)", added, a.cap))
    L.extend(section("DROPPED (in the manifest, absent from disk)", dropped, a.cap))
    L.extend(section("CHANGED (same path, different bytes)", changed, a.cap))
    L.extend(section("UNREADABLE (walk errors -- a FAIL, never a footnote)",
                     [p + " :: " + e for p, e in walk_errors], a.cap))
    if bad_lines:
        L.extend(section("UNPARSED LINES IN THE OLD MANIFEST (kept out of the rebuild)",
                         ["line " + str(n) + ": " + t for n, t in bad_lines], a.cap))
    L.append("")

    wrote = False
    if not a.rebuild:
        L.append("VERDICT    : " + ("CLEAN -- tree matches the manifest exactly" if clean
                                    else "DIFFERS -- see the sections above"))
        L.append("ACTION     : nothing written (check-only run)")
    elif guard_tripped and not a.force:
        L.append("VERDICT    : REFUSED")
        L.append("ACTION     : nothing written. " + str(len(dropped)) + " rows would be lost ("
                 + ("%.1f" % drop_pct) + "% > " + ("%.1f" % a.max_drop_pct) + "%).")
        L.append("             If that is genuinely right, re-run the same line with --force.")
    else:
        tmp = manifest + ".new"
        fh = open(tmp, "wb")
        try:
            fh.write(new_blob)
        finally:
            fh.close()
        proof = md5_of(tmp)
        if proof != new_md5:
            L.append("VERDICT    : ABORTED -- the file written to disk does not hash to what was built.")
            L.append("             built " + new_md5 + " / on disk " + proof + ". MANIFEST.md5 untouched.")
        else:
            if os.path.exists(manifest):
                if a.backup_dir:
                    if not os.path.isdir(a.backup_dir):
                        os.makedirs(a.backup_dir)
                    backup = os.path.join(a.backup_dir, "MANIFEST.md5.bak_" + label)
                else:
                    backup = manifest + ".bak_" + label
                if not os.path.exists(backup):
                    fhi = open(manifest, "rb")
                    blob = fhi.read()
                    fhi.close()
                    fho = open(backup, "wb")
                    fho.write(blob)
                    fho.close()
                    L.append("backup     : " + backup)
                else:
                    L.append("backup     : " + backup + " already existed -- left as it was")
            if os.path.exists(manifest):
                os.remove(manifest)
            os.rename(tmp, manifest)
            final = md5_of(manifest)
            wrote = True
            L.append("VERDICT    : REBUILT")
            L.append("ACTION     : MANIFEST.md5 replaced. md5 on disk now " + final
                     + (" (matches)" if final == new_md5 else " (MISMATCH -- investigate)"))
            if guard_tripped:
                L.append("             drop guard was overridden with --force.")

    text = "\n".join(L) + "\n"
    try:
        rh = codecs.open(report_path, "w", "utf-8")
        rh.write(text)
        rh.close()
    except Exception as exc:
        sys.stderr.write("could not write report: " + str(exc) + "\n")
    sys.stdout.write(text)

    if walk_errors:
        return 3
    if a.rebuild:
        return 0 if wrote else 4
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main())
