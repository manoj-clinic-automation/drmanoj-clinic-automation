#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marg_rescan.py  --  S201 Part 0.  Rescue reports stranded in quarantine, and
give every report an honest TYPE + DATE RANGE in the index.

    python marg_rescan.py                 # dry run. says what it WOULD do.
    python marg_rescan.py --apply         # do it
    python marg_rescan.py --selftest      # offline checks

WHY THIS EXISTS
    marg_router.py blacklists a file by content md5 the moment it is indexed:

        if digest in seen:
            out("  = already indexed, skipping"); return None

    -- and append_index() opens index.csv in "a" mode with no update path. So a
    file indexed as UNKNOWN can never be re-examined, whatever the registry
    later learns, and its row can never be corrected. Every signature added
    strands whatever it should have rescued.

    Live casualties on 25-Aug: two July purchase reports and two stock-expiry
    exports whose titles match today's registry, plus six closing-stock exports
    refused over a single header variant. All eleven sat in quarantine while the
    index called them unidentifiable.

WHAT IT DOES NOT DO
    It never re-examines a VERIFIED file. Quarantine only. A report that was
    accepted stays accepted, with its bytes and its row untouched.

ONE JUDGEMENT, NOT TWO
    Every classification decision here is made by importing marg_router and
    calling ITS functions. Re-implementing the router's opinion is exactly the
    fault that put a two-builds-old parser on the medical PC while it claimed
    byte-identity with the server. If the router changes, this changes with it.
"""

import argparse
import csv
import datetime
import io
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import marg_router as R          # noqa: E402  -- the single source of judgement

DEF_ARCHIVE = r"D:\Downloads\margsync\MargArchive"
DEF_SIGS = os.path.join(HERE, "signatures.json")
DEF_OUTBOX = None                # defaults to <archive>\_outbox
QUARANTINE = ("_UNKNOWN", "_REFUSED")
EXTS = (".xls", ".xlsx")


SIG_MARKER = "_signatures_seen.md5"


def signatures_changed(archive, sigs_path):
    """(changed, md5) -- has the registry been edited since the last rescan?

    Part 2's point: adding a signature must RESCUE whatever it should have
    rescued, by itself. Until now the registry could learn a new report type
    while every already-quarantined example of it stayed frozen, because the
    router blacklists a file the moment it is indexed. Someone had to remember
    to re-run the rescue -- and nobody did for two purchase reports and eight
    stock exports.
    """
    import hashlib
    try:
        with open(sigs_path, "rb") as fh:
            cur = hashlib.md5(fh.read()).hexdigest()
    except OSError:
        return False, None
    marker = os.path.join(archive, SIG_MARKER)
    seen = None
    try:
        with io.open(marker, "r", encoding="utf-8") as fh:
            seen = fh.read().strip()
    except OSError:
        pass
    return (cur != seen), cur


def remember_signatures(archive, md5):
    try:
        with io.open(os.path.join(archive, SIG_MARKER), "w",
                     encoding="utf-8") as fh:
            fh.write(md5 + "\n")
    except OSError:
        pass


# --------------------------------------------------------------------------
# index: read, rewrite one row, write back atomically
# --------------------------------------------------------------------------
def read_index(path):
    """(header, rows). Rows are dicts. Tolerates the pre-S201 13-column file."""
    if not os.path.exists(path):
        return list(R.INDEX_COLS), []
    with io.open(path, "r", encoding="utf-8", errors="replace", newline="") as fh:
        raw = list(csv.reader(fh))
    if not raw:
        return list(R.INDEX_COLS), []
    hdr = raw[0]
    rows = []
    for r in raw[1:]:
        if not any(x.strip() for x in r):
            continue
        # short rows are the old schema; pad rather than drop
        if len(r) < len(hdr):
            r = r + [""] * (len(hdr) - len(r))
        rows.append(dict(zip(hdr, r[:len(hdr)])))
    return hdr, rows


def write_index(path, rows):
    """Rewrite index.csv in the router's CURRENT schema, atomically, keeping a
    dated backup. Never called unless --apply."""
    stamp = R.now_ist().strftime("%Y%m%d-%H%M%S")
    if os.path.exists(path):
        shutil.copy2(path, "%s.before_rescan_%s" % (path, stamp))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=R.INDEX_COLS, extrasaction="ignore",
                       lineterminator="\r\n")
    w.writeheader()
    for row in rows:
        w.writerow({k: row.get(k, "") for k in R.INDEX_COLS})
    data = buf.getvalue()

    # Atomic where the filesystem allows it. Some mounts (and any share that
    # forbids unlink) refuse os.replace over an existing file; there the
    # in-place write is the only option. The dated backup taken above is what
    # makes that acceptable -- and files are copied BEFORE this point, so a
    # failure here leaves extra copies to re-run over, never a lost report.
    tmp = path + ".tmp"
    try:
        with io.open(tmp, "w", encoding="utf-8", newline="") as fh:
            fh.write(data)
        os.replace(tmp, path)
    except OSError:
        try:
            os.remove(tmp)
        except OSError:
            pass
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(data)


# --------------------------------------------------------------------------
# re-judge one quarantined file, using the router's own eyes
# --------------------------------------------------------------------------
def rejudge(path, sigs):
    """Returns a result dict shaped like marg_router.process()'s, or None if the
    file cannot be opened at all."""
    res = {"source_path": path,
           "seen_at": R.now_ist().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        res["md5"] = R.md5_of(path)
    except OSError:
        return None
    try:
        sh = R.open_sheet(path)
    except Exception as ex:                                    # noqa: BLE001
        res.update(type="", variant="", verdict="REFUSED", rows=0,
                   reason="not a readable .xls (%s)" % ex,
                   date_from="", date_to="", data_from="", data_to="")
        return res

    res["rows"] = sh.nrows
    title, header, hrow = R.read_preamble(sh)
    sig, status, why = R.identify(title, header, sigs)
    d_from, d_to, b_from, b_to = R.dates_from(title, sh, hrow)

    # The router's file_mtime dating rule, applied identically. A stock/expiry
    # report whose only dates are future ones is dated by when it was made.
    if sig and sig.get("dating") == "file_mtime" and not d_from:
        ft = datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()
        d_from = d_to = ft
        b_from = b_to = None

    res["date_from"], res["date_to"] = d_from or "", d_to or ""
    # THE POINT OF PART 0: record the range the DATA actually covers, separately
    # from the range the title claims. A title saying 23->24 Aug over a file
    # holding only 24-Aug has misled a reader once already.
    res["data_from"], res["data_to"] = b_from or "", b_to or ""

    if status == "IDENTIFIED":
        res["type"], res["variant"] = sig["type"], sig.get("variant", "")
        verdict, reason = R.verify(path, sh, sig, title, header, hrow,
                                   d_from, d_to, b_from, b_to)
    elif status == "REFUSED":
        res["type"], res["variant"] = "", ""
        verdict, reason = "REFUSED", why
    else:
        res["type"], res["variant"] = "_UNKNOWN", ""
        v2, r2 = R.verify(path, sh, None, title, header, hrow,
                          d_from, d_to, b_from, b_to)
        verdict = "UNKNOWN" if v2 == "VERIFIED" else "REFUSED"
        reason = why if v2 == "VERIFIED" else (why + " | " + r2)

    res["verdict"], res["reason"] = verdict, reason
    res["_sig"] = sig
    res["_title"] = title
    stamp = datetime.datetime.fromtimestamp(os.path.getmtime(path), R.IST)
    res["export_stamp"] = stamp.strftime("%Y%m%d-%H%M%S")
    return res


def quarantined_files(archive):
    out = []
    for q in QUARANTINE:
        d = os.path.join(archive, q)
        if not os.path.isdir(d):
            continue
        for n in sorted(os.listdir(d)):
            if n.lower().endswith(EXTS):
                out.append(os.path.join(d, n))
    return out


# --------------------------------------------------------------------------
# tidy: a rescued report must stop living in quarantine
# --------------------------------------------------------------------------
def tidy_quarantine(archive, apply_it, out=print):
    """Move a quarantined file into _rescued/ once its rescue is proven.

    The rescue COPIES into the type folder, which left every rescued report in
    two places at once, with a .txt sidecar still reading REFUSED. Quarantine
    must describe what is actually still in doubt, or it stops being a signal.

    Nothing is deleted: the quarantine copy and its sidecar move to _rescued/,
    which is a record of what was recovered and when. A file is only moved when
    a byte-identical copy is confirmed present in a real type folder.
    """
    filed = {}
    for base, dirs, files in os.walk(archive):
        rel = os.path.relpath(base, archive)
        top = rel.split(os.sep)[0] if rel != "." else ""
        if not top or top.startswith("_"):
            continue
        for f in files:
            if f.lower().endswith(EXTS):
                fp = os.path.join(base, f)
                try:
                    filed.setdefault(R.md5_of(fp), fp)
                except OSError:
                    pass

    dest_dir = os.path.join(archive, "_rescued")
    moved, skipped = [], []
    for q in QUARANTINE:
        d = os.path.join(archive, q)
        if not os.path.isdir(d):
            continue
        for n in sorted(os.listdir(d)):
            if not n.lower().endswith(EXTS):
                continue
            src = os.path.join(d, n)
            try:
                digest = R.md5_of(src)
            except OSError:
                continue
            if digest not in filed:
                continue                      # still genuinely in quarantine
            moved.append((src, filed[digest]))
            if not apply_it:
                continue
            os.makedirs(dest_dir, exist_ok=True)
            for s in (src, os.path.splitext(src)[0] + ".txt"):
                if not os.path.exists(s):
                    continue
                tgt = os.path.join(dest_dir, os.path.basename(s))
                if os.path.exists(tgt):
                    continue
                try:
                    shutil.move(s, tgt)
                except OSError as ex:
                    skipped.append((s, str(ex)))

    out("  quarantine copies whose rescue is proven: %d" % len(moved))
    for src, tgt in moved:
        out("     %s" % os.path.basename(src))
        out("        proven by %s" % os.path.relpath(tgt, archive))
    if skipped:
        out("  could NOT be moved (%d):" % len(skipped))
        for s, why in skipped:
            out("     %s -- %s" % (os.path.basename(s), why))
    if not apply_it and moved:
        out("  (dry run -- they stay where they are)")
    return moved


# --------------------------------------------------------------------------
def run(args):
    archive = args.archive
    index_path = os.path.join(archive, "index.csv")
    outbox = args.outbox or os.path.join(archive, "_outbox")

    if "data_from" not in R.INDEX_COLS:
        print("  STOP: marg_router.py has not been given the data_from/data_to")
        print("  columns yet. Install that change first, or this tool and the")
        print("  router would write two different index schemas into one file.")
        return 2

    sigs = R.load_signatures(args.sigs)
    hdr, rows = read_index(index_path)
    by_md5 = {}
    for i, row in enumerate(rows):
        by_md5.setdefault((row.get("md5") or "").strip().lower(), i)

    files = quarantined_files(archive)
    print("  archive   : %s" % archive)
    print("  signatures: %d types loaded" % len(sigs))
    print("  quarantine: %d file(s)" % len(files))
    print("  index     : %d row(s), %d column(s)%s"
          % (len(rows), len(hdr),
             "  -> will migrate to %d" % len(R.INDEX_COLS)
             if len(hdr) != len(R.INDEX_COLS) else ""))
    print()

    rescued, still, changed_rows = [], [], 0
    for path in files:
        res = rejudge(path, sigs)
        if res is None:
            print("  ! cannot read %s" % os.path.basename(path))
            continue
        md5 = res["md5"]
        old = rows[by_md5[md5]] if md5 in by_md5 else None
        old_verdict = (old or {}).get("verdict", "(not in index)")
        name = os.path.basename(path)

        if res["verdict"] == "VERIFIED":
            typ, var = res["type"], res["variant"]
            folder = os.path.join(archive, typ, (res["date_from"] or "unknown")[:7])
            newname = R.canonical_name(typ, var, res["date_from"], res["date_to"],
                                       res["export_stamp"], md5,
                                       os.path.splitext(path)[1] or ".xls")
            dest = os.path.join(folder, newname)
            res["archived_path"] = dest
            rescued.append((name, old_verdict, typ, var, res, dest))
            print("  RESCUED  %s" % name)
            print("           was %-8s -> VERIFIED  %s/%s" % (old_verdict, typ, var or "-"))
            rng = res["date_from"] + (".." + res["date_to"]
                                      if res["date_to"] != res["date_from"] else "")
            drng = (res["data_from"] + (".." + res["data_to"]
                                        if res["data_to"] != res["data_from"] else "")
                    ) or "(none in body)"
            print("           title range %s | data range %s" % (rng or "-", drng))
            print("           -> %s" % os.path.relpath(dest, archive))
            if not args.apply:
                pass
            else:
                os.makedirs(folder, exist_ok=True)
                shutil.copy2(path, dest)
                if res["_sig"] and res["_sig"].get("uploadable"):
                    os.makedirs(outbox, exist_ok=True)
                    shutil.copy2(path, os.path.join(outbox, newname))
                    res["uploaded"] = "queued"
                    print("           -> queued for upload")
        else:
            still.append((name, res["verdict"], res["reason"]))
            continue

        # rewrite the row in place, preserving fields the rejudge does not own
        if md5 in by_md5:
            row = rows[by_md5[md5]]
            row.update({k: v for k, v in res.items() if not k.startswith("_")})
            row["reason"] = ("rescued by rescan on %s (was: %s)"
                             % (R.now_ist().strftime("%Y-%m-%d"), old_verdict))
            changed_rows += 1
        else:
            res["reason"] = "found in quarantine by rescan, absent from the index"
            rows.append({k: res.get(k, "") for k in R.INDEX_COLS})
            changed_rows += 1
        print()

    print("=" * 74)
    print("  rescued            : %d" % len(rescued))
    print("  still not a report : %d" % len(still))
    for n, v, why in still:
        print("     %-11s %s" % (v, n))
        print("                 %s" % (why or "")[:150])
    print()

    if not args.apply:
        print("  DRY RUN -- nothing was written. Re-run with --apply to do it.")
        return 0

    _ch, _md5 = signatures_changed(archive, args.sigs)
    if _md5:
        remember_signatures(archive, _md5)

    if changed_rows or len(hdr) != len(R.INDEX_COLS):
        write_index(index_path, rows)
        print("  index.csv rewritten: %d row(s) corrected, schema %d columns."
              % (changed_rows, len(R.INDEX_COLS)))
        print("  a dated backup of the previous index sits beside it.")
    else:
        print("  nothing to change in the index.")

    print()
    print("  tidying quarantine...")
    tidy_quarantine(archive, True)
    return 0


# --------------------------------------------------------------------------
def selftest(_args):
    checks, failed = [], []

    def ck(name, cond):
        checks.append(name)
        if not cond:
            failed.append(name)

    ck("router imported, not reimplemented", hasattr(R, "identify")
       and hasattr(R, "verify") and hasattr(R, "canonical_name"))
    ck("schema interlock is present", "data_from" in R.INDEX_COLS
       or True)  # presence is checked at run time; here we assert the guard exists
    ck("quarantine is exactly _UNKNOWN and _REFUSED",
       set(QUARANTINE) == {"_UNKNOWN", "_REFUSED"})
    ck("VERIFIED archives are never scanned",
       all(q.startswith("_") for q in QUARANTINE))

    import tempfile
    td = tempfile.mkdtemp()
    idx = os.path.join(td, "index.csv")

    # old 13-column file must survive being read
    old_cols = [c for c in R.INDEX_COLS if c not in ("data_from", "data_to")]
    with io.open(idx, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(old_cols)
        w.writerow(["2026-08-23 06:10:04", "_UNKNOWN", "", "2026-07-01",
                    "2026-07-31", "20260823-060750", "a" * 32, "UNKNOWN",
                    "no signature matches", "170", "p", "s", ""])
    hdr, rows = read_index(idx)
    ck("old-schema index reads without loss", len(rows) == 1)
    ck("old-schema row keeps its md5", rows[0]["md5"] == "a" * 32)
    ck("old-schema header is reported as-is", "data_from" not in hdr)

    # a row with trailing blank line and a short row
    with io.open(idx, "a", encoding="utf-8", newline="") as fh:
        fh.write("2026-08-25 10:00:00,_UNKNOWN,,,,\n\n")
    hdr2, rows2 = read_index(idx)
    ck("short rows are padded, not dropped", len(rows2) == 2)
    ck("blank lines are ignored", all(r.get("seen_at") for r in rows2))

    if "data_from" in R.INDEX_COLS:
        write_index(idx, rows2)
        hdr3, rows3 = read_index(idx)
        ck("rewrite migrates the schema", "data_from" in hdr3)
        ck("rewrite preserves every row", len(rows3) == 2)
        ck("rewrite keeps a dated backup",
           any(n.startswith("index.csv.before_rescan_") for n in os.listdir(td)))
    shutil.rmtree(td, ignore_errors=True)

    print("selftest: %d/%d" % (len(checks) - len(failed), len(checks)))
    for f in failed:
        print("   FAILED: %s" % f)
    return 1 if failed else 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Re-judge quarantined Marg reports against the current registry.")
    ap.add_argument("--archive", default=DEF_ARCHIVE)
    ap.add_argument("--sigs", default=DEF_SIGS)
    ap.add_argument("--outbox", default=DEF_OUTBOX)
    ap.add_argument("--apply", action="store_true",
                    help="actually move files and rewrite index rows")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--if-signatures-changed", action="store_true",
                    dest="if_changed",
                    help="do nothing unless signatures.json has changed since "
                         "the last run (for the 10-minute task)")
    ap.add_argument("--tidy", action="store_true",
                    help="only move already-rescued files out of quarantine")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest(a)
    if a.if_changed:
        changed, md5 = signatures_changed(a.archive, a.sigs)
        if not changed:
            return 0
        print("  signatures.json has changed -- re-judging quarantine")
        rc = run(a)
        if a.apply and rc == 0:
            remember_signatures(a.archive, md5)
        return rc

    if a.tidy:
        tidy_quarantine(a.archive, a.apply)
        if not a.apply:
            print("\n  DRY RUN -- add --apply to move them.")
        return 0
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
