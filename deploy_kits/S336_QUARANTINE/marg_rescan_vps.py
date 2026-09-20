#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marg_rescan_vps.py -- S274 / kit S336_QUARANTINE (Sanjeevni).  The server-side rescan (Book s11.4 3d).

    /root/wa/venv/bin/python3 -B /root/marg_ingest/marg_rescan_vps.py --if-signatures-changed --apply
    /root/wa/venv/bin/python3 -B /root/marg_ingest/marg_rescan_vps.py --status
    /root/wa/venv/bin/python3 -B /root/marg_ingest/marg_rescan_vps.py --apply          (re-judge now, whatever changed)

WHAT IT DOES, in order, under the collector's own lock (marg_take._Lock, so it never runs beside a take
or the five-minute collection):
  1. marg_rescan.py -- manojz's tool, vendored byte-identical -- re-judges every .xls/.xlsx still in
     archive/_REFUSED and archive/_UNKNOWN with the CURRENT signatures.json, through the router's own
     functions; a file that now verifies is copied into its type folder, its index.csv row rewritten,
     and the quarantine copy + sidecar moved to archive/_rescued/ (nothing deleted by that tool).
  2. every rescued md5 is then RE-TAKEN THROUGH THE ONE DOOR (marg_take.take, source 'rescan'): its
     mi_file row (REFUSED / UNKNOWN) and any mi_sale_line rows are removed first so the door judges it
     afresh -- a sale report becomes PHI-free lines and its raw copy is deleted (S186); every other type
     stays kept in its type folder.  What the door decided is printed per file.
  3. archive/_rescued/ keeps SIDECARS ONLY on this box: the raw copies marg_rescan parks there are
     removed (they exist now in the type folder, or as lines, or were never fit to rest here).
It writes: index.csv (via marg_rescan), mi_file / mi_sale_line (via the door), the quarantine folders.
It never touches a VERIFIED file.  Its OFF switch is the collector's: /root/marg_ingest/OFF.
"""
import argparse
import datetime as dt
import glob
import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import marg_ingest as MI          # noqa: E402
import marg_rescan as RS          # noqa: E402  (manojz's tool, vendored)
import marg_take as MT            # noqa: E402

OFF = os.path.join(HERE, "OFF")
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def now():
    return dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def _index_verdicts(archive):
    try:
        _hdr, rows = RS.read_index(os.path.join(archive, "index.csv"))
    except Exception:                                            # noqa: BLE001
        return {}
    return {(r.get("md5") or "").strip().lower(): r for r in rows}


def quarantine_status(archive, db):
    """One dict for --status and for a health line."""
    files = RS.quarantined_files(archive)
    side = [p for q in RS.QUARANTINE for p in glob.glob(os.path.join(archive, q, "*.txt"))]
    resc = glob.glob(os.path.join(archive, "_rescued", "*"))
    marker = ""
    try:
        with io.open(os.path.join(archive, RS.SIG_MARKER), "r", encoding="utf-8") as fh:
            marker = fh.read().strip()
    except OSError:
        pass
    cur = ""
    try:
        with open(os.path.join(HERE, "signatures.json"), "rb") as fh:
            cur = hashlib.md5(fh.read()).hexdigest()
    except OSError:
        pass
    return dict(kept=len(files), sidecars=len(side), rescued_records=len(resc),
                signatures=cur[:8], last_judged=marker[:8], changed=(cur != marker))


def _retake(md5, path, db, log):
    """Remove the door's old opinion of these bytes and take them again.  The old mi_file row is held in
    memory and put back if the door does not answer TAKEN (busy, refused) -- a record is never lost."""
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as e:
        log("   ! cannot read %s: %s" % (os.path.basename(path), e))
        return None
    if hashlib.md5(raw).hexdigest() != md5:
        log("   ! %s is not the bytes the index names (%s)" % (os.path.basename(path), md5[:8]))
        return None
    con = MT._connect(db)
    try:
        cur = con.execute("SELECT * FROM mi_file WHERE md5=?", (md5,))
        cols = [d[0] for d in cur.description]
        old = cur.fetchone()
        lines = con.execute("SELECT * FROM mi_sale_line WHERE md5=?", (md5,)).fetchall()
        con.execute("DELETE FROM mi_sale_line WHERE md5=?", (md5,))
        con.execute("DELETE FROM mi_file WHERE md5=?", (md5,))
        con.commit()
    finally:
        con.close()
    res = MT.take(raw, name=os.path.basename(path), source="rescan", db=db)
    if res.get("status") != "TAKEN" and old is not None:
        con = MT._connect(db)
        try:
            con.execute("INSERT OR REPLACE INTO mi_file (%s) VALUES (%s)" % (",".join(cols), ",".join("?" * len(cols))), tuple(old))
            if lines:
                n = len(lines[0])
                con.executemany("INSERT INTO mi_sale_line VALUES (%s)" % ",".join("?" * n), [tuple(l) for l in lines])
            con.commit()
        finally:
            con.close()
        log("   ! the door answered %s for %s -- its old row was put back" % (res.get("status"), os.path.basename(path)[:60]))
    return res


def run(args, log=print):
    archive = args.archive
    db = args.db
    if os.path.exists(OFF):
        log("marg_rescan_vps %s: OFF flag present (%s) -- nothing done" % (now(), OFF))
        return 0
    if args.status:
        s = quarantine_status(archive, db)
        log("quarantine: %d file(s) kept · %d sidecar(s) · %d rescued record(s) · signatures %s · last judged with %s%s"
            % (s["kept"], s["sidecars"], s["rescued_records"], s["signatures"] or "?", s["last_judged"] or "never",
               " · CHANGED, rescan due" if s["changed"] else ""))
        return 0
    if args.if_changed:
        changed, _md5 = RS.signatures_changed(archive, args.sigs)
        if not changed:
            log("marg_rescan_vps %s: signatures unchanged -- nothing to re-judge" % now())
            return 0
    try:
        lock = MT._Lock().__enter__()
    except RuntimeError:
        log("marg_rescan_vps %s: the archive is busy (collector lock) -- try again shortly" % now())
        return 3
    try:
        MI._readers()                    # the router's own .xlsx opener into marg_report, as the door does
        before = _index_verdicts(archive)
        argv = ["--archive", archive, "--sigs", args.sigs]
        if args.apply:
            argv.append("--apply")
        log("marg_rescan_vps %s: re-judging quarantine%s" % (now(), "" if args.apply else " (DRY RUN)"))
        rc = RS.main(argv)
        if rc not in (0, None):
            log("   marg_rescan returned %s -- stopping here, nothing re-taken" % rc)
            return int(rc)
        if not args.apply:
            return 0
        after = _index_verdicts(archive)
    finally:
        lock.__exit__()                  # the door locks itself per take; holding on would make it BUSY
    rescued = [m for m, r in after.items()
               if (r.get("verdict") or "").upper() == "VERIFIED"
               and (before.get(m, {}).get("verdict") or "").upper() != "VERIFIED"]
    n_ok = 0
    for md5 in sorted(rescued):
        row = after[md5]
        path = RS.R._local_path(archive, row.get("archived_path")) if hasattr(RS.R, "_local_path") else row.get("archived_path")
        if not path or not os.path.exists(path):
            log("   ! rescued %s but its file is not at %s" % (md5[:8], row.get("archived_path")))
            continue
        res = _retake(md5, path, db, log)
        if res is None or res.get("status") != "TAKEN":
            continue
        n_ok += 1
        log("   RE-TAKEN %-8s %-22s %s kept=%s lines=%s  %s" % (res.get("status"), (res.get("type") or "?") + "/" + (res.get("variant") or "-"),
                                                              res.get("verdict"), res.get("kept"), res.get("lines"), os.path.basename(path)[:70]))
    # 3. sidecars only in _rescued/
    removed = 0
    for p in glob.glob(os.path.join(archive, "_rescued", "*")):
        if p.lower().endswith((".xls", ".xlsx", ".pdf")):
            try:
                os.remove(p)
                removed += 1
            except OSError:
                pass
    log("marg_rescan_vps %s: rescued %d, re-taken through the door %d, raw copies removed from _rescued/ %d"
        % (now(), len(rescued), n_ok, removed))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Re-judge the VPS quarantine against the current signatures, and re-take what is rescued.")
    ap.add_argument("--archive", default=MI.ARCHIVE)
    ap.add_argument("--sigs", default=os.path.join(HERE, "signatures.json"))
    ap.add_argument("--db", default=MI.DB_DEFAULT)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--if-signatures-changed", dest="if_changed", action="store_true")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args(argv)
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
