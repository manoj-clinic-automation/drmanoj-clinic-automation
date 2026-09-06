#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
snapshot_on_capture.py -- S225 §8 item 7: push the stock snapshot WHEN IT IS CAPTURED, not only at 22:30.

The owner (04-Sep): "latest stock report doesn't seem to be applied" -- the Marg closing-stock export reached
the archive at 03:10 and the drift page waited for the nightly. This runs on manojz every 15 minutes (a
scheduled task, registered ALLOWED ON BATTERY -- F-314): it reads MargArchive\index.csv, finds the newest
VERIFIED STOCK_CLOSING export that is a whole-store set (variant TOTALS or DEFAULT -- never ORTHOTICS or
SUBSET), and if that export has not been pushed by this tool before, runs the S208 kit's push_snapshot.py
exactly as the nightly does. push_snapshot decides what to send (it holds the F-235 rules); this only decides
WHEN. A marker file remembers the last export pushed; a refusal is logged and retried next time.
Nothing here writes to Marg or the archive. Logs: D:\Downloads\margsync\_analysis\snapshot_on_capture_log.txt
"""
import csv, datetime as dt, io, os, subprocess, sys

ARCHIVE = os.environ.get("MARG_ARCHIVE", r"D:\Downloads\margsync\MargArchive")
KIT = os.environ.get("STOCK_KIT", r"D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S208_STOCK_LEDGER")
OUT = os.environ.get("MARG_ANALYSIS", r"D:\Downloads\margsync\_analysis")
PY = os.environ.get("PYTHON", sys.executable or "python")
WHOLE = ("TOTALS", "DEFAULT")
MARK = os.path.join(OUT, "snapshot_on_capture_last.txt")
LOG = os.path.join(OUT, "snapshot_on_capture_log.txt")


def log(msg):
    os.makedirs(OUT, exist_ok=True)
    line = "%s  %s" % (dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line)
    with io.open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def newest_whole_closing():
    idx = os.path.join(ARCHIVE, "index.csv")
    if not os.path.exists(idx):
        return None
    with io.open(idx, encoding="utf-8", errors="replace", newline="") as fh:
        rows = [r for r in csv.DictReader(fh)
                if r.get("type") == "STOCK_CLOSING" and r.get("verdict") == "VERIFIED"
                and (r.get("variant") or "").upper() in WHOLE]
    if not rows:
        return None
    rows.sort(key=lambda r: (r.get("date_to") or "", r.get("seen_at") or ""))
    return rows[-1]


def main(argv=None):
    dry = "--dry-run" in (argv or sys.argv[1:])
    r = newest_whole_closing()
    if r is None:
        log("no VERIFIED whole-store STOCK_CLOSING in the archive -- nothing to do")
        return 0
    last = io.open(MARK, encoding="utf-8").read().strip() if os.path.exists(MARK) else ""
    if r["md5"] == last:
        return 0                                  # quiet: the newest export is already pushed
    log("NEW closing-stock export: as-on %s, seen %s, %s rows, md5 %s -- pushing now"
        % (r.get("date_to"), r.get("seen_at"), r.get("rows"), r["md5"][:8]))
    if dry:
        log("dry run -- push_snapshot NOT run, marker NOT written")
        return 0
    script = os.path.join(KIT, "push_snapshot.py")
    if not os.path.exists(script):
        log("REFUSING: %s not found" % script)
        return 2
    p = subprocess.run([PY, "-B", script], cwd=KIT, capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    for ln in out.strip().splitlines()[-12:]:
        log("  | " + ln)
    if p.returncode != 0 or "REFUSING" in out:
        log("push_snapshot exit %d -- NOT marked done; will retry in 15 min" % p.returncode)
        return 1
    os.makedirs(OUT, exist_ok=True)
    io.open(MARK, "w", encoding="utf-8").write(r["md5"] + "\n")
    log("pushed and marked (md5 %s)" % r["md5"][:8])
    return 0


if __name__ == "__main__":
    sys.exit(main())
