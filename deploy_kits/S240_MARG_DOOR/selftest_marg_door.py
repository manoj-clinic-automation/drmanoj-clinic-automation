#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_marg_door.py -- S240. Proves the one door, against REAL Marg exports, into a TEMP
database and a TEMP archive. It touches nothing live: not finance.db, not /root/marg_ingest/archive.

    /root/wa/venv/bin/python3 -B selftest_marg_door.py [--from DIR]

--from defaults to /root/marg_ingest/archive, so on the box it exercises whatever that box
actually holds. Cases it cannot exercise there (a sale report leaves no file on this box, by
policy) are reported as NOT EXERCISED rather than silently passed.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ING = os.environ.get("MARG_INGEST_DIR", "/root/marg_ingest")
# the INSTALLED marg_take is what must be proved, so its folder goes first
for p in (HERE, ING):
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

OK = [0]
BAD = [0]
SKIP = [0]


def ck(name, cond, extra=""):
    if cond:
        OK[0] += 1
        print("  ok    %s" % name)
    else:
        BAD[0] += 1
        print("  FAIL  %s %s" % (name, extra))


def skip(name, why):
    SKIP[0] += 1
    print("  --    %s  (NOT EXERCISED: %s)" % (name, why))


def find(root, needle, n=1):
    out = []
    for base, _d, files in os.walk(root):
        for f in sorted(files):
            if needle in f.upper() and f.lower().endswith((".xls", ".xlsx")):
                out.append(os.path.join(base, f))
                if len(out) >= n:
                    return out
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", default="/root/marg_ingest/archive")
    a = ap.parse_args()
    import marg_take as MT

    tmp = tempfile.mkdtemp(prefix="doorselftest_")
    db = os.path.join(tmp, "t.db")
    arch = os.path.join(tmp, "archive")
    os.makedirs(arch)
    print("selftest_marg_door -- temp db %s" % db)
    print("  reading real exports from: %s" % a.src)

    # ---- what it must refuse -------------------------------------------------------------
    ck("an empty file is refused",
       MT.take(b"", name="x.xls", db=db, archive=arch)["status"] == "REFUSED")
    ck("a .txt is refused",
       MT.take(b"hello", name="notes.txt", db=db, archive=arch)["status"] == "REFUSED")
    r = MT.take(b"this is not a spreadsheet at all", name="report.xls", db=db, archive=arch)
    ck("bytes that are not a spreadsheet are refused", r["status"] == "REFUSED", r["reason"])
    ck("an oversized file is refused",
       MT.take(b"\xd0\xcf\x11\xe0" + b"0" * (MT.MAX_BYTES + 1), name="big.xls",
               db=db, archive=arch)["status"] == "REFUSED")
    ck("a name cannot carry a folder", MT.safe_name(r"..\..\windows\system32\evil.xls") == "evil.xls")
    ck("a name cannot carry odd characters", MT.safe_name("a b;c&d.XLS") == "a_b_c_d.xls")

    # ---- what it must take ---------------------------------------------------------------
    stock = find(a.src, "STOCK_CLOSING")
    if not stock:
        skip("a stock export is taken and kept", "no STOCK_CLOSING file in %s" % a.src)
    else:
        raw = open(stock[0], "rb").read()
        r1 = MT.take(raw, name=os.path.basename(stock[0]), source="test", db=db, archive=arch)
        ck("a stock export is taken", r1["status"] == "TAKEN", r1["reason"])
        ck("  ...and verified", r1["verdict"] == "VERIFIED", r1["verdict"])
        ck("  ...and the file is kept (no patient data in it)", r1["kept"] == 1)
        ck("  ...and the capture moment comes from the name, not from now",
           r1["stamp"] == os.path.basename(stock[0]).split("__")[-2], r1["stamp"])
        r2 = MT.take(raw, name=os.path.basename(stock[0]), source="test", db=db, archive=arch)
        ck("the same bytes again are ALREADY, not a second copy", r2["status"] == "ALREADY", r2["status"])
        r3 = MT.take(raw, name="COMPLETELY_DIFFERENT_NAME.xls", source="manual", db=db, archive=arch)
        ck("the same bytes under another name are still ALREADY", r3["status"] == "ALREADY", r3["status"])
        ck("  ...so one file is held, not three", MT.counts(db=db)["total"] == 1,
           MT.counts(db=db)["total"])

    pur = find(a.src, "PURCHASE")
    if not pur:
        skip("a purchase export is taken", "no PURCHASE file in %s" % a.src)
    else:
        rp = MT.take(open(pur[0], "rb").read(), name=os.path.basename(pur[0]), source="test",
                     db=db, archive=arch)
        ck("a purchase export is taken and verified",
           rp["status"] == "TAKEN" and rp["verdict"] == "VERIFIED", "%s/%s" % (rp["status"], rp["verdict"]))

    sale = find(a.src, "SALE_BILLWISE")
    if not sale:
        skip("a sale report leaves no file behind", "this box keeps none, by policy (S186)")
    else:
        before = set()
        for b, _d, fs in os.walk(arch):
            before |= {os.path.join(b, f) for f in fs}
        rs = MT.take(open(sale[0], "rb").read(), name=os.path.basename(sale[0]), source="test",
                     db=db, archive=arch)
        ck("a sale report is taken", rs["status"] == "TAKEN", rs["reason"])
        ck("  ...and its item lines are kept", rs["lines"] > 0, rs["lines"])
        ck("  ...and the file itself is NOT kept", rs["kept"] == 0)
        after = set()
        for b, _d, fs in os.walk(arch):
            after |= {os.path.join(b, f) for f in fs}
        left = [p for p in (after - before) if p.lower().endswith((".xls", ".xlsx", ".pdf"))]
        ck("  ...and no export file is left anywhere in the archive", not left, left[:2])
        import sqlite3
        con = sqlite3.connect(db)
        vals = " ".join(str(x) for row in con.execute(
            "SELECT item_name, pack, qty_raw, batch, expiry_ym FROM mi_sale_line") for x in row)
        con.close()
        import re as _re
        ck("  ...and nothing phone-shaped is in the lines kept",
           not _re.search(r"\b[6-9]\d{9}\b", vals))

    # ---- the lock ------------------------------------------------------------------------
    sample = (stock or pur or [None])[0]
    if not sample:
        skip("while the collector holds the lock, the door says BUSY", "no real export to send")
    else:
        db2 = os.path.join(tmp, "lock.db")               # a db that has never seen this file,
        arch2 = os.path.join(tmp, "archive2")            # so ALREADY cannot mask BUSY
        os.makedirs(arch2)
        holder = subprocess.Popen([sys.executable, "-c",
                                   "import fcntl,time;f=open(%r,'a+');fcntl.flock(f.fileno(),fcntl.LOCK_EX);"
                                   "time.sleep(8)" % MT.LOCK_PATH])
        try:
            import time as _t
            _t.sleep(1.0)
            MT.LOCK_WAIT_S = 2
            r = MT.take(open(sample, "rb").read(), name=os.path.basename(sample),
                        source="test", db=db2, archive=arch2)
            ck("while the collector holds the lock, the door says BUSY and takes nothing",
               r["status"] == "BUSY", r["status"])
            ck("  ...and nothing was recorded in that attempt", MT.counts(db=db2)["total"] == 0)
        finally:
            MT.LOCK_WAIT_S = 25
            holder.terminate()
            holder.wait()

    ck("recent() answers", isinstance(MT.recent(5, db=db), list))
    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d ok, %d failed, %d not exercised" % (OK[0], BAD[0], SKIP[0]))
    return 1 if BAD[0] else 0


if __name__ == "__main__":
    sys.exit(main())
