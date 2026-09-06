#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
expected_on_capture.py -- S225 (06-Sep-2026): push OUR computed stock figure WHEN THE SALE REPORT LANDS, not only at 22:30.

Why: the drift page compares Marg's closing stock with the figure the books compute (baseline + purchases - sales).
Marg's side has pushed on capture since S225 (snapshot_on_capture.py). Our side still waited for the nightly at 22:30 --
and on 05-Sep the PC was asleep at 22:30 (watchdog: asleep ~21:38 to 01:04), while the catch-up run of 08:46 had hung at
its first step with no output. So the first comparable day never reached the page: "Our computed figure: never received".

This runs on manojz every 15 minutes (scheduled, ALLOWED ON BATTERY, 10-minute time limit -- F-314). It reads
MargArchive\index.csv and watches TWO things: the newest VERIFIED SALE_BILLWISE export and the newest VERIFIED
PURCHASE_* export. When either is new (rev 2, the owner 06-Sep 02:00: "Amir adds a few purchases and exports the
purchase reports, and then the server should apply immediately"):
    1  if a purchase export is new -> push_purchases.py (the S224 kit, the nightly's step 3) sends every purchase export
       not yet on the server, so the purchase books are current FIRST;
    2  PUSH_STOCK_DAILY.bat recomputes and sends our figure -- that .bat holds the pinned baseline and the refusal
       check in ONE place (D349); this only decides WHEN.
Marker = the pair of md5s last handled. Exit 0 = sent (marked) · 3 = the .bat refused (marked, said once, waits for a
newer export) · anything else = not marked, retried in 15 min. Nothing here writes to Marg or the archive. The 22:30
nightly stays as the sweep.
Logs: D:\Downloads\margsync\_analysis\expected_on_capture_log.txt
"""
import csv, datetime as dt, io, os, subprocess, sys

ARCHIVE = os.environ.get("MARG_ARCHIVE", r"D:\Downloads\margsync\MargArchive")
DAILY = os.environ.get("STOCK_DAILY_BAT", r"D:\Downloads\margsync\PUSH_STOCK_DAILY.bat")
PKIT = os.environ.get("PURCHASE_KIT", r"D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S224_MARG_PURCHASES")
PY = os.environ.get("PYTHON", sys.executable or "python")
OUT = os.environ.get("MARG_ANALYSIS", r"D:\Downloads\margsync\_analysis")
MARK = os.path.join(OUT, "expected_on_capture_last.txt")
LOG = os.path.join(OUT, "expected_on_capture_log.txt")


def log(msg):
    os.makedirs(OUT, exist_ok=True)
    line = "%s  %s" % (dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line)
    with io.open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def newest_sale():
    idx = os.path.join(ARCHIVE, "index.csv")
    if not os.path.exists(idx):
        return None
    with io.open(idx, encoding="utf-8", errors="replace", newline="") as fh:
        rows = [r for r in csv.DictReader(fh)
                if r.get("type") == "SALE_BILLWISE" and r.get("verdict") == "VERIFIED" and r.get("md5")]
    if not rows:
        return None
    rows.sort(key=lambda r: (r.get("date_to") or "", r.get("seen_at") or ""))
    return rows[-1]


def newest_purchase():
    idx = os.path.join(ARCHIVE, "index.csv")
    if not os.path.exists(idx):
        return None
    with io.open(idx, encoding="utf-8", errors="replace", newline="") as fh:
        rows = [r for r in csv.DictReader(fh)
                if (r.get("type") or "").startswith("PURCHASE_") and r.get("verdict") == "VERIFIED" and r.get("md5")]
    if not rows:
        return None
    rows.sort(key=lambda r: (r.get("seen_at") or ""))
    return rows[-1]


def runner():
    """The command that computes and sends. Overridable so the selftest can stand in a stub."""
    cmd = os.environ.get("STOCK_DAILY_CMD")
    if cmd:
        return cmd.split("|")
    return ["cmd", "/c", DAILY]


def purchase_runner():
    """The command that sends the purchase books (push_purchases.py in its kit). Overridable for the selftest."""
    cmd = os.environ.get("PURCHASE_CMD")
    if cmd:
        return cmd.split("|"), None
    return [PY, "-B", os.path.join(PKIT, "push_purchases.py")], PKIT


def main(argv=None):
    dry = "--dry-run" in (argv or sys.argv[1:])
    sale, purch = newest_sale(), newest_purchase()
    if sale is None:
        log("no VERIFIED SALE_BILLWISE in the archive -- nothing to do")
        return 0
    key = "%s %s" % (sale["md5"], purch["md5"] if purch else "-")
    last = io.open(MARK, encoding="utf-8").read().strip() if os.path.exists(MARK) else ""
    last_key = " ".join(last.split()[1:3]) if last else ""
    if last_key == key:
        return 0                                  # quiet: nothing new since the last run (sent, or refused and said once)
    purchase_new = bool(purch) and (purch["md5"] not in last.split())
    if purchase_new:
        log("NEW purchase export: %s %s..%s, seen %s, %s rows, md5 %s"
            % (purch.get("type"), purch.get("date_from"), purch.get("date_to"), purch.get("seen_at"), purch.get("rows"), purch["md5"][:8]))
    if sale["md5"] not in last.split():
        log("NEW sale export: for %s, seen %s, %s rows, md5 %s"
            % (sale.get("date_to"), sale.get("seen_at"), sale.get("rows"), sale["md5"][:8]))
    log("-- computing our figure now%s" % (" (purchase books first)" if purchase_new else ""))
    if dry:
        log("dry run -- nothing run, marker NOT written")
        return 0
    if not os.environ.get("STOCK_DAILY_CMD") and not os.path.exists(DAILY):
        log("REFUSING: %s not found" % DAILY)
        return 2
    os.makedirs(OUT, exist_ok=True)
    if purchase_new:
        cmd, cwd = purchase_runner()
        if cwd and not os.path.exists(os.path.join(cwd, "push_purchases.py")):
            log("REFUSING: push_purchases.py not found in %s" % cwd)
            return 2
        try:
            pp = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired:
            log("push_purchases did not finish in 5 minutes -- NOT marked; will retry in 15 min")
            return 1
        pout = (pp.stdout or "") + (pp.stderr or "")
        for ln in [x for x in pout.strip().splitlines() if x.strip()][-6:]:
            log("  |p " + ln)
        # 0 = sent · 2 without REFUSING = nothing left to send (the nightly got there first) · else not now
        if not (pp.returncode == 0 or (pp.returncode == 2 and "REFUSING" not in pout)):
            log("push_purchases exit %d -- purchase books NOT current; NOT marked; will retry in 15 min" % pp.returncode)
            return 1
        log("purchase books current on the server")
    try:
        p = subprocess.run(runner(), capture_output=True, text=True, timeout=540)
    except subprocess.TimeoutExpired:
        log("PUSH_STOCK_DAILY did not finish in 9 minutes -- NOT marked; will retry in 15 min")
        return 1
    out = (p.stdout or "") + (p.stderr or "")
    for ln in [x for x in out.strip().splitlines() if x.strip()][-8:]:
        log("  | " + ln)
    if p.returncode == 0:
        io.open(MARK, "w", encoding="utf-8").write("SENT %s\n" % key)
        log("our figure for %s sent and marked (sale %s, purchases %s)" % (sale.get("date_to"), sale["md5"][:8], purch["md5"][:8] if purch else "-"))
        return 0
    if p.returncode == 3:
        io.open(MARK, "w", encoding="utf-8").write("REFUSED %s\n" % key)
        log("PUSH_STOCK_DAILY REFUSED for %s (see _analysis\\push_stock_lastrun.txt) -- said once; waits for a newer export" % sale.get("date_to"))
        return 3
    log("PUSH_STOCK_DAILY exit %d -- NOT marked; will retry in 15 min" % p.returncode)
    return 1


if __name__ == "__main__":
    sys.exit(main())
