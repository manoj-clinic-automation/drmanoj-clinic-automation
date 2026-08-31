#!/usr/bin/env python3
"""selftest for S214_ANOMALY_BASELINE -- invariants on a SYNTHETIC db.

No frozen real snapshot (the S212 rule): every check is an invariant that
must hold on data this file builds itself, so archive growth never reddens it.
"""
import os
import sqlite3
import subprocess  # every child runs with -B: bytecode inside a kit folder
                   # is an ignored file the publish gate then refuses (S214)
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import finance_item_anomaly as A
import anomaly_baseline as B

PASS = FAIL = 0


def check(name, ok):
    global PASS, FAIL
    print("%s  %s" % ("PASS" if ok else "FAIL", name))
    PASS, FAIL = PASS + ok, FAIL + (not ok)


def build_db(path):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE sale_line_item (business_date TEXT, bill_no TEXT,"
                " seq INT, item_name TEXT, item_key TEXT, qty_raw TEXT,"
                " pack TEXT, amount_p INT, is_return INT DEFAULT 0)")
    con.execute("CREATE TABLE sale_item (source_ref TEXT, patient_ref_id INT)")
    con.execute("CREATE TABLE patient_ref (id INT, name TEXT, clinic_id TEXT)")
    rows = []
    # STEADY: sold daily for 30 days, qty 1-2, rate always 10000
    for i in range(30):
        d = "2026-05-%02d" % (i + 1)
        rows.append((d, "B%03d" % i, 1, "STEADY TAB", "steady", "0:%d" % (1 + i % 2),
                     "1*10", 10000, 0))
    # RARE: ONE prior sale of 1 unit -- then 20 on judgement day (the June shape)
    rows.append(("2026-05-10", "B900", 1, "RARE OINT", "rare", "0:1", "", 5000, 0))
    # judgement day 2026-06-01
    rows.append(("2026-06-01", "J001", 1, "STEADY TAB", "steady", "0:1", "1*10", 10000, 0))
    rows.append(("2026-06-01", "J002", 1, "RARE OINT", "rare", "0:20", "", 5000, 0))
    con.executemany("INSERT INTO sale_line_item VALUES (?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()


def scan(db, day="2026-06-01"):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    out, tally = A.scan_day(con, day)
    con.close()
    return out, tally


def main():
    tmp = tempfile.mkdtemp(prefix="anom_selftest_")
    db = os.path.join(tmp, "t.db")
    build_db(db)

    out1, t1 = scan(db)
    out2, t2 = scan(db)
    check("determinism: two scans identical", out1 == out2 and t1 == t2)

    v = {(o["bill"], o["seq"]): o["verdict"] for o in out1}
    check("thin-history 20x line flags FAR BEYOND",
          v.get(("J002", 1)) == "FAR BEYOND ANYTHING SEEN")
    check("normal line does not flag", ("J001", 1) not in v)

    con = sqlite3.connect(db)
    n = con.execute("SELECT COUNT(*) FROM sale_line_item "
                    "WHERE business_date='2026-06-01'").fetchone()[0]
    buckets = sum(c for k, c in t1.items() if not k.startswith("_"))
    check("verdict buckets are disjoint and sum to the day's lines", buckets == n)

    # rate injections on the steady item
    for mult, should in ((0.10, True), (0.50, True), (0.75, False)):
        con.execute("UPDATE sale_line_item SET amount_p=? "
                    "WHERE bill_no='J001'", (int(10000 * mult),))
        con.commit()
        o, _ = scan(db)
        got = any(x["bill"] == "J001" and "RATE OFF" in x["verdict"] for x in o)
        check("rate at %d%% of normal %s" %
              (mult * 100, "flags" if should else "stays quiet"), got == should)
    con.execute("UPDATE sale_line_item SET amount_p=10000 WHERE bill_no='J001'")
    con.commit()
    con.close()

    # the baseline flow, end to end, via the CLI
    base = os.path.join(tmp, "base.txt")
    py = sys.executable
    tool = os.path.join(HERE, "anomaly_baseline.py")
    r = subprocess.run([py, "-B", tool, "--db", db, "--baseline", base],
                       capture_output=True, text=True)
    check("no baseline yet -> exit 2", r.returncode == 2)
    r = subprocess.run([py, "-B", tool, "--db", db, "--baseline", base, "--rebuild"],
                       capture_output=True, text=True)
    check("rebuild exits 0 and writes the file",
          r.returncode == 0 and os.path.exists(base))
    r = subprocess.run([py, "-B", tool, "--db", db, "--baseline", base],
                       capture_output=True, text=True)
    check("unchanged data -> quiet, exit 0",
          r.returncode == 0 and "NEW 0" in r.stdout)
    con = sqlite3.connect(db)
    con.execute("INSERT INTO sale_line_item VALUES "
                "('2026-06-02','N001',1,'STEADY TAB','steady','0:30','1*10',10000,0)")
    con.commit()
    con.close()
    r = subprocess.run([py, "-B", tool, "--db", db, "--baseline", base],
                       capture_output=True, text=True)
    check("new outlier line -> exit 1 and a NEW row",
          r.returncode == 1 and "NEW " in r.stdout)
    check("NEW row names the bill, not a patient number", "N001" in r.stdout)

    print("\n%d passed, %d failed" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
