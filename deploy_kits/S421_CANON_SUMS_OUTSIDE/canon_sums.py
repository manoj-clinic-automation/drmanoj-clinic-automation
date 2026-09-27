#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
canon_sums.py  (S275)  --  keep MD5SUMS_ALL.txt covering every file in KB_canon_all.

WHY THIS EXISTS
  Twice on 15-Sep-2026 a document was published into
  `deploy_kits\\KB_canon_all\\` and MD5SUMS_ALL.txt gained no row for it. The
  gate then passes -- `md5sum -c` verifies 535 of 535 -- while not checking the
  new file at all. A gate that quietly stops covering a file still exits 0.
  That is F-369's shape, and this was its third instance in three days (the pin
  list missed its row at the S256 and S257 closes as well).

  The repair is not a third manual edit. It is a step that owns the sums file.

WHAT IT DOES
  --check    (default) name every file in canon with no row, and every row with
             no file, and verify every row that has both. Writes nothing.
             Exit 0 = the sums file covers the folder exactly and every hash
             matches. Exit 4 = coverage gap. Exit 3 = a hash mismatch.
  --fix      rewrite MD5SUMS_ALL.txt so it covers the folder exactly.
             EXISTING ROWS THAT STILL MATCH THEIR FILE ARE COPIED THROUGH BYTE
             FOR BYTE, in their existing order. Only missing rows are added and
             only rows whose file is gone are dropped.

WHAT IT REFUSES
  * A hash MISMATCH is never rewritten by --fix. A row whose file has changed
    is a fact that needs a person, not a silent update: --fix stops, names it,
    and writes nothing. (--force-changed rewrites those rows and says so in the
    report; it exists so the refusal can be overridden deliberately, never by
    accident.)
  * A rewrite that would drop more than 10% of the rows is REFUSED.
  * An unreadable file is a FAIL, not a footnote, and exits 3.

  The old file is copied to <backup-dir>\MD5SUMS_ALL.txt.bak_<stamp> before any rewrite, and
  the new one is hashed back before it is put in place.

  S421 (F-596, 27-Sep-2026): the backup lives OUTSIDE canon (default
  D:\Downloads\_kbtools\canon_sums_backups), so it is never a canon file and never gets
  a row; and --fix writes NOTHING when the sums file already covers canon exactly.
  Before this, every night's run backed the sums file up INSIDE canon, rowed the
  backup, and so changed canon itself -- the nightly could never report "nothing to do",
  and 41 backups had piled up by S277.

stdlib only. Rows are `<md5>` + two spaces + the path with forward slashes,
sorted under a byte ordering -- byte-identical to what `md5sum` produces.
"""

import argparse
import hashlib
import os
import shutil
import sys
from datetime import datetime

VERSION = "S275 v1.2 (+ S320, the CURRENT-row check; + S421, F-596: backups OUTSIDE canon, no rewrite when nothing changed)"
SUMS = "MD5SUMS_ALL.txt"
RC_OK, RC_FAIL, RC_GAP = 0, 3, 4


def md5_of(path, chunk=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def read_rows(path):
    """[(md5, relpath, raw_line)] in file order. A malformed line is kept and flagged."""
    rows, bad = [], []
    if not os.path.isfile(path):
        return rows, bad
    with open(path, "r", encoding="utf-8", newline="") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            if len(line) > 34 and line[32:34] == "  ":
                rows.append((line[:32], line[34:].replace("\\", "/"), line))
            else:
                bad.append(line)
    return rows, bad


def walk(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for fn in sorted(filenames):
            if fn == SUMS:          # a file cannot carry its own hash
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            out.append((rel, full))
    return sorted(out)


# --------------------------------------------------------------- S320 (F-384) --
#  EXACTLY ONE ROW PER FAMILY MAY CLAIM TO BE CURRENT.
#
#  CANONICAL_MANIFEST.md is the linchpin, and gen_live_pins.py keys on the bare
#  word CURRENT. A superseded row that still carries it is therefore not a
#  cosmetic blemish: the pin list can be generated from the wrong version of the
#  Register. That is F-384 (S236) and F-449 (S243) -- the same fault twice, both
#  times found by hand, months apart.
#
#  Convention this reads, and it is the manifest's own: a superseded row writes
#  "was **CURRENT**" or carries the word superseded / SUPERSEDED / formerly /
#  retained in its notes. A row with a bare CURRENT is claiming the title.
#
#  READ-ONLY. It parses the manifest and never edits it; a finding here is
#  reported and named in the VERDICT line, and never changes the exit code,
#  because the sums repair must not be blocked by a manifest blemish.
MANIFEST_NAME = "CANONICAL_MANIFEST.md"
#  Families that may legitimately hold more than one CURRENT row, with the most
#  there may be. START_HERE_SESSION: one entry point per project since the
#  Sanjeevni project split (the parent's and Sanjeevni's), and each row is
#  expected to name its project.
CURRENT_ALLOW_MULTI = {"START_HERE_SESSION": 2}


def _family(name):
    n = name.strip().strip("`*").strip()
    for ext in (".md", ".txt", ".py", ".json"):
        if n.endswith(ext):
            n = n[:-len(ext)]
    out, i = [], 0
    parts = n.replace("-", "_").split("_")
    for p in parts:
        if p.startswith("v") and p[1:].replace(".", "").isdigit():
            break
        if p.startswith("S") and p[1:].split("close")[0].isdigit():
            break
        if p.isdigit():
            break
        out.append(p)
        i += 1
    return "_".join(out) or n


def _claims_current(notes):
    low = notes.lower()
    for word in ("superseded", "formerly", "retained"):
        if word in low:
            return False
    at = 0
    while True:
        k = notes.find("CURRENT", at)
        if k < 0:
            return False
        before = notes[max(0, k - 14):k].rstrip("* ").rstrip()
        if not (before.endswith("was") or before.endswith("not")):
            return True
        at = k + 7


def current_row_report(root, say):
    """(duplicate families, note for the VERDICT line). Never raises, never writes."""
    path = os.path.join(root, MANIFEST_NAME)
    say("")
    say("CURRENT-ROW CHECK (F-384) -- read-only, on %s" % MANIFEST_NAME)
    if not os.path.isfile(path):
        say("  the manifest is not in this folder -- nothing checked")
        return {}, "manifest absent"
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        say("  could not be read: %s" % exc)
        return {}, "manifest unreadable"
    fam = {}
    rows = 0
    for i, line in enumerate(text.split("\n"), 1):
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() in ("doc", "document", "file"):
            continue
        rows += 1
        notes = " ".join(cells[3:]) if len(cells) > 3 else cells[-1]
        if _claims_current(notes):
            fam.setdefault(_family(cells[0]), []).append((i, cells[0].strip("`* ")))
    dups = {}
    for k, v in fam.items():
        if len(v) > int(CURRENT_ALLOW_MULTI.get(k, 1)):
            dups[k] = v
    say("  rows parsed : %d · families claiming CURRENT : %d" % (rows, len(fam)))
    if not dups:
        say("  OK -- no family claims CURRENT more than once (allowing %s)"
            % ", ".join("%s x%d" % (k, n) for k, n in sorted(CURRENT_ALLOW_MULTI.items())))
        return {}, ""
    say("  F-384 AGAIN -- %d family(ies) claim CURRENT more than once:" % len(dups))
    for k in sorted(dups):
        say("    %s" % k)
        for ln, name in dups[k]:
            say("        line %-6d %s" % (ln, name))
    say("  A superseded row that still reads CURRENT can generate the pin list from")
    say("  the wrong version. Correct the stale cells VISIBLY at the next close.")
    return dups, "F-384: %d family(ies) with more than one CURRENT row (%s)" % (
        len(dups), ", ".join(sorted(dups)))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--canon", default=r"D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\KB_canon_all")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--force-changed", action="store_true")
    ap.add_argument("--report", default=None)
    ap.add_argument("--backup-dir", default=r"D:\Downloads\_kbtools\canon_sums_backups")   # S421, F-596
    a = ap.parse_args(argv)

    root = a.canon
    lines = ["CANON SUMS -- %s" % VERSION,
             "when   : %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             "canon  : %s" % root, ""]

    def say(s=""):
        lines.append(s)
        print(s)

    if not os.path.isdir(root):
        say("FAIL -- the canon folder does not exist.")
        return RC_FAIL

    sums_path = os.path.join(root, SUMS)
    rows, malformed = read_rows(sums_path)
    files = walk(root)
    on_disk = dict(files)
    rowed = {}
    for h, rel, raw in rows:
        rowed.setdefault(rel, (h, raw))

    say("files in canon : %d" % len(files))
    say("rows in %s : %d" % (SUMS, len(rows)))
    if malformed:
        say("MALFORMED lines: %d -- a FAIL, never a footnote" % len(malformed))
        for m in malformed[:10]:
            say("    %s" % m[:100])
        return RC_FAIL

    missing_row = [rel for rel, _ in files if rel not in rowed]
    missing_file = [rel for rel in rowed if rel not in on_disk]

    changed, unreadable, verified = [], [], 0
    for rel, full in files:
        if rel not in rowed:
            continue
        try:
            got = md5_of(full)
        except OSError as exc:
            unreadable.append("%s (%s)" % (rel, exc))
            continue
        if got != rowed[rel][0]:
            changed.append((rel, rowed[rel][0], got))
        else:
            verified += 1

    say("")
    say("verified       : %d" % verified)
    say("IN CANON, NO ROW (the gate is not checking these) : %d" % len(missing_row))
    for r in missing_row:
        say("    %s" % r)
    say("ROW, NO FILE   : %d" % len(missing_file))
    for r in sorted(missing_file):
        say("    %s" % r)
    say("HASH MISMATCH  : %d" % len(changed))
    for rel, was, now in changed:
        say("    %s\n        row %s\n        now %s" % (rel, was, now))
    say("UNREADABLE     : %d" % len(unreadable))
    for u in unreadable:
        say("    %s" % u)

    _dups, _dupnote = current_row_report(root, say)       # S320 (F-384), read-only

    rc = RC_OK
    if unreadable:
        rc = RC_FAIL
    elif changed:
        rc = RC_FAIL
    elif missing_row or missing_file:
        rc = RC_GAP

    if not a.fix:
        say("")
        say("VERDICT : %s%s" % ({RC_OK: "OK -- the sums file covers the folder exactly",
                                 RC_FAIL: "FAIL",
                                 RC_GAP: "GAP -- run with --fix"}[rc],
                                (" · " + _dupnote) if _dupnote else ""))
        return finish(lines, a, rc)

    # ---------------------------------------------------------------- --fix
    if rc == RC_OK:                                   # S421 (F-596): nothing to change -> write nothing
        say("")
        say("NOTHING TO REWRITE -- the sums file already covers canon exactly (no backup taken)")
        say("VERDICT : OK%s" % ((" \u00b7 " + _dupnote) if _dupnote else ""))
        return finish(lines, a, RC_OK)
    if unreadable:
        say("")
        say("REFUSING to rewrite: a file could not be read.")
        return finish(lines, a, RC_FAIL)
    if changed and not a.force_changed:
        say("")
        say("REFUSING to rewrite: %d row(s) disagree with their file." % len(changed))
        say("A changed file is a fact that needs a person, not a silent update.")
        say("Re-run with --force-changed only if you mean to accept the new bytes.")
        return finish(lines, a, RC_FAIL)

    keep = {rel for rel, _ in files}
    if rows and len(missing_file) > max(1, len(rows) // 10):
        say("")
        say("REFUSING to rewrite: it would drop %d of %d rows (>10%%)."
            % (len(missing_file), len(rows)))
        return finish(lines, a, RC_FAIL)

    forced = {rel for rel, _, _ in changed} if a.force_changed else set()
    new_lines = []
    for h, rel, raw in rows:                      # existing rows, in order, byte for byte
        if rel not in keep:
            continue
        if rel in forced:
            new_lines.append("%s  %s" % (md5_of(on_disk[rel]), rel))
        else:
            new_lines.append(raw)
    for rel in missing_row:
        new_lines.append("%s  %s" % (md5_of(on_disk[rel]), rel))

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if os.path.abspath(a.backup_dir).lower().startswith(os.path.abspath(root).lower()):   # S421 (F-596)
        say("REFUSING -- the backup folder is inside canon (F-596).")
        return finish(lines, a, RC_FAIL)
    try:
        os.makedirs(a.backup_dir, exist_ok=True)
    except OSError as exc:
        say("FAIL -- could not make the backup folder %s: %s" % (a.backup_dir, exc))
        return finish(lines, a, RC_FAIL)
    bak = os.path.join(a.backup_dir, SUMS + ".bak_" + stamp)
    # NOT ".new": a file of that exact name already lives in this canon folder,
    # rowed by the gate, and os.replace() would have destroyed it. The kit's own
    # test caught that. The temp name is unique per run and refuses a collision.
    tmp = "%s.tmp_%s_%d" % (sums_path, stamp, os.getpid())
    if os.path.exists(tmp):
        say("REFUSING -- the temporary name %s already exists." % os.path.basename(tmp))
        return finish(lines, a, RC_FAIL)
    try:
        if os.path.isfile(sums_path):
            shutil.copyfile(sums_path, bak)       # S421: outside canon, so no row
        new_lines.sort(key=lambda s: s[34:].encode("utf-8"))
        body = "\n".join(new_lines) + "\n"
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        if md5_of(tmp) != hashlib.md5(body.encode("utf-8")).hexdigest():
            os.remove(tmp)
            say("REFUSING -- the new file did not read back identical.")
            return finish(lines, a, RC_FAIL)
        os.replace(tmp, sums_path)
    except OSError as exc:
        say("FAIL -- could not write: %s" % exc)
        return finish(lines, a, RC_FAIL)

    say("")
    say("REWRITTEN : %d rows (was %d)" % (len(new_lines), len(rows)))
    say("  added   : %d" % len(missing_row))
    say("  dropped : %d" % len(missing_file))
    say("  forced  : %d" % len(forced))
    say("  backup  : %s" % bak)
    say("VERDICT : FIXED%s" % ((" \u00b7 " + _dupnote) if _dupnote else ""))
    return finish(lines, a, RC_OK)


def finish(lines, a, rc):
    target = a.report
    if target:
        try:
            d = os.path.dirname(target)
            if d and not os.path.isdir(d):
                os.makedirs(d)
            with open(target, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(lines) + "\n")
        except OSError as exc:
            sys.stderr.write("could not write the report: %s\n" % exc)
    return rc


if __name__ == "__main__":
    sys.exit(main())
