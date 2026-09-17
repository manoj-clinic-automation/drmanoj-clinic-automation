#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_s285.py -- offline proof for S285_SUPPLIER_CHECK. Nothing live is touched.

    python3 -B selftest_s285.py --live /path/to/a/copy/of/amir_day.py

Applies the patcher to a COPY of the live file, then imports BOTH the untouched
copy and the patched copy as modules (flask must be importable) and drives their
own _bills() and _bill_block() over one fixture database:

  bill 1  KEDAR, 3 items KEDAR has always supplied            -> no warning
  bill 2  DAANSHI, one item KEDAR supplied on 3 earlier bills  -> ONE warning naming KEDAR, 3
  bill 3  DAANSHI, an item never bought before                 -> no warning
  bill 4  SOLO, an item another supplier bought ONCE           -> no warning (below two)
  bill 5  a bill that exists only in a SUPERSEDED export       -> gone from the list (was shown before)
  bill 6  a bill first seen in a superseded export and still in the live one -> stays, seen_day = the earlier day
  bill 7  a flagged bill (reason short)                        -> stays in flagged, carries no warning
"""
import argparse
import hashlib
import importlib.util
import io
import os
import py_compile
import shutil
import sqlite3
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("ok " if ok else "FAIL", name, ("  -- " + str(detail)) if detail else ""))
    if not ok:
        FAILS.append(name)


def md5(p):
    return hashlib.md5(io.open(p, "rb").read()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def fixture(path, mod):
    cx = sqlite3.connect(path)
    cx.row_factory = sqlite3.Row
    cx.executescript("""
    CREATE TABLE purchase_export (md5 TEXT PRIMARY KEY, type TEXT, file TEXT, period_from TEXT,
        period_to TEXT, export_stamp TEXT, received_at TEXT, n_rows INTEGER, grand_amount_p INTEGER,
        superseded_by TEXT);
    CREATE TABLE purchase_bill (id INTEGER PRIMARY KEY, supplier_norm TEXT, supplier TEXT, bill_no TEXT,
        bill_date TEXT, month TEXT, cash_p INTEGER, credit_p INTEGER, amount_p INTEGER, source_md5 TEXT,
        bw_md5 TEXT);
    CREATE TABLE purchase_line (id INTEGER PRIMARY KEY, supplier_norm TEXT, bill_no TEXT, bill_date TEXT,
        item TEXT, amount_p INTEGER, source_md5 TEXT, line_type TEXT);
    """)
    mod._ensure(cx)
    # exports: E1 (bill-wise, 1-10 Sep, exported 10-Sep, SUPERSEDED by E2), E2 (bill-wise, 1-17 Sep,
    # exported 17-Sep, live), L1 (item-wise, April-Aug history, live), L2 (item-wise, Sep, live)
    cx.executemany("INSERT INTO purchase_export VALUES (?,?,?,?,?,?,?,?,?,?)", [
        ("E1", "BILLWISE", "e1", "2026-09-01", "2026-09-10", "20260910-180000", "2026-09-10T18:00:00", 0, 0, "E2"),
        ("E2", "BILLWISE", "e2", "2026-09-01", "2026-09-17", "20260917-090000", "2026-09-17T09:00:00", 0, 0, None),
        ("L1", "ITEMWISE", "l1", "2026-04-01", "2026-08-31", "20260901-100000", "2026-09-01T10:00:00", 0, 0, None),
        ("L2", "ITEMWISE", "l2", "2026-09-01", "2026-09-17", "20260917-090100", "2026-09-17T09:01:00", 0, 0, None),
    ])
    bills = [
        # in E1 only: bill 5 (the wrong-supplier bill Amir has since corrected in Marg)
        ("WRONGCO", "WRONGCO", "500", "2026-09-05", 1000, "E1"),
        # in E1 AND E2: bill 6 (first seen 10-Sep, still live)
        ("KEDAR", "KEDAR PHARMACEUTICAL", "600", "2026-09-05", 2000, "E1"),
        ("KEDAR", "KEDAR PHARMACEUTICAL", "600", "2026-09-05", 2000, "E2"),
        # today's bills, in E2
        ("KEDAR", "KEDAR PHARMACEUTICAL", "1", "2026-09-17", 3000, "E2"),
        ("DAANSHI", "DAANSHI PHARMA", "2", "2026-09-17", 4000, "E2"),
        ("DAANSHI", "DAANSHI PHARMA", "3", "2026-09-17", 500, "E2"),
        ("SOLO", "SOLO TRADERS", "4", "2026-09-17", 600, "E2"),
        ("KEDAR", "KEDAR PHARMACEUTICAL", "7", "2026-09-17", 700, "E2"),
    ]
    cx.executemany("INSERT INTO purchase_bill (supplier_norm,supplier,bill_no,bill_date,month,cash_p,credit_p,"
                   "amount_p,source_md5,bw_md5) VALUES (?,?,?,?,'2026-09',0,?,?,?,?)",
                   [(a, b, c, d, e, e, f, f) for a, b, c, d, e, f in bills])
    lines = [
        # history: KEDAR supplied TYRO BR on 3 bills, MEG QCS on 2, ASTOFEN on 2; ONCE supplied by OTHER on 1
        ("KEDAR", "h1", "2026-05-02", "TYRO BR", 100, "L1", "ITEMWISE"),
        ("KEDAR", "h2", "2026-06-02", "TYRO BR", 100, "L1", "ITEMWISE"),
        ("KEDAR", "h3", "2026-07-02", "TYRO BR", 100, "L1", "ITEMWISE"),
        ("KEDAR", "h3", "2026-07-02", "TYRO BR", 100, "L1", "BILLITEMWISE"),  # same bill twice, two line types
        ("KEDAR", "h1", "2026-05-02", "MEG QCS", 100, "L1", "ITEMWISE"),
        ("KEDAR", "h2", "2026-06-02", "MEG QCS", 100, "L1", "ITEMWISE"),
        ("KEDAR", "h1", "2026-05-02", "ASTOFEN SP", 100, "L1", "ITEMWISE"),
        ("KEDAR", "h4", "2026-08-02", "ASTOFEN SP", 100, "L1", "ITEMWISE"),
        ("OTHER", "o1", "2026-08-09", "RARE ITEM", 100, "L1", "ITEMWISE"),
        # a superseded history line must not count: WRONGCO "supplied" TYRO BR only in a dead export
        ("WRONGCO", "z1", "2026-08-20", "TYRO BR", 100, "DEAD", "ITEMWISE"),
        # today
        ("KEDAR", "1", "2026-09-17", "TYRO BR", 100, "L2", "ITEMWISE"),
        ("KEDAR", "1", "2026-09-17", "MEG QCS", 100, "L2", "ITEMWISE"),
        ("KEDAR", "1", "2026-09-17", "ASTOFEN SP", 100, "L2", "ITEMWISE"),
        ("DAANSHI", "2", "2026-09-17", "TYRO BR", 100, "L2", "ITEMWISE"),
        ("DAANSHI", "2", "2026-09-17", "DENGEN PLUS", 100, "L2", "ITEMWISE"),
        ("DAANSHI", "3", "2026-09-17", "NEW THING", 100, "L2", "ITEMWISE"),
        ("SOLO", "4", "2026-09-17", "RARE ITEM", 100, "L2", "ITEMWISE"),
    ]
    cx.executemany("INSERT INTO purchase_line (supplier_norm,bill_no,bill_date,item,amount_p,source_md5,line_type) "
                   "VALUES (?,?,?,?,?,?,?)", lines)
    cx.execute("INSERT INTO amir_bill_disposition (supplier_norm,bill_no,bill_date,day,reason,by_user,at) "
               "VALUES ('KEDAR','7','2026-09-17','2026-09-17','short','amir','2026-09-17T09:30:00')")
    cx.commit()
    return cx


def keyset(rows):
    return {(r["supplier_norm"], r["bill_no"]) for r in rows}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", required=True)
    a = ap.parse_args(argv)
    py = sys.executable
    tmp = tempfile.mkdtemp(prefix="s285_")
    try:
        print("part 1 -- the patcher on a COPY of %s" % a.live)
        old = os.path.join(tmp, "amir_day_before.py")
        work = os.path.join(tmp, "amir_day.py")
        shutil.copy2(a.live, old)
        shutil.copy2(a.live, work)
        before = md5(work)
        import patch_supplier_check_s285 as pm
        src = io.open(work, "r", encoding="utf-8").read()
        for i, (o, _n) in enumerate(pm.EDITS):
            check("anchor %s present exactly once" % "ABCDE"[i], src.count(o) == 1, src.count(o))
        patcher = os.path.join(HERE, "patch_supplier_check_s285.py")
        r = subprocess.run([py, "-B", patcher, "--file", work, "--from", "0" * 32], capture_output=True, text=True)
        check("wrong --from refused, nothing written", r.returncode != 0 and md5(work) == before)
        r = subprocess.run([py, "-B", patcher, "--file", work, "--from", before], capture_output=True, text=True)
        check("patch applies", r.returncode == 0, (r.stdout + r.stderr).strip()[-100:])
        after = md5(work)
        print("  pin: %s -> %s" % (before, after))
        try:
            py_compile.compile(work, doraise=True)
            check("patched file compiles", True)
        except Exception as e:  # noqa: BLE001
            check("patched file compiles", False, e)
        r = subprocess.run([py, "-B", patcher, "--file", work, "--from", after], capture_output=True, text=True)
        check("second run ALREADY PATCHED, pin unchanged", "ALREADY" in r.stdout and md5(work) == after)

        print("part 2 -- both modules over the fixture")
        m0 = load(old, "amir_day_before")
        m1 = load(work, "amir_day_after")
        check("the new reason is there and is NOT a claim",
              m1.REASON_MAP.get("supplier") == "Supplier galat likha" and "supplier" not in m1.CLAIM_REASONS)
        check("the other reasons are unchanged", [c for c, _l in m1.REASONS if c != "supplier"] == [c for c, _l in m0.REASONS])
        cx0 = fixture(os.path.join(tmp, "f0.db"), m0)
        cx1 = fixture(os.path.join(tmp, "f1.db"), m1)
        t0, c0, f0 = m0._bills(cx0, "2026-09-17")
        t1, c1, f1 = m1._bills(cx1, "2026-09-17")
        check("BEFORE: the corrected-away bill 500 still haunted the list", ("WRONGCO", "500") in keyset(c0))
        check("AFTER: bill 500 (only in a superseded export) is gone", ("WRONGCO", "500") not in keyset(t1 + c1 + f1))
        check("AFTER: bill 600 (superseded AND live) stays as carry", ("KEDAR", "600") in keyset(c1))
        check("AFTER: bill 600 keeps its EARLIER seen_day (10-Sep, not 17-Sep)",
              [d for d in c1 if d["bill_no"] == "600"][0]["seen_day"] == "2026-09-10")
        check("AFTER: today's four unanswered bills are today's", keyset(t1) == {("KEDAR", "1"), ("DAANSHI", "2"), ("DAANSHI", "3"), ("SOLO", "4")}, keyset(t1))
        check("AFTER: the flagged bill 7 stays flagged", keyset(f1) == {("KEDAR", "7")})
        check("the lists agree with BEFORE except for the vanished bill",
              keyset(t0) == keyset(t1) and keyset(c0) - {("WRONGCO", "500")} == keyset(c1) and keyset(f0) == keyset(f1))
        w = {d["bill_no"]: d.get("warn") for d in t1 + c1}
        check("bill 1 (KEDAR, its own items): no warning", w["1"] == [], w["1"])
        check("bill 2 (DAANSHI with TYRO BR): ONE warning naming KEDAR on 3 bills", w["2"] == [("TYRO BR", "KEDAR", 3)], w["2"])
        check("...and the superseded WRONGCO history did not count", all(x[1] != "WRONGCO" for x in w["2"]))
        check("bill 3 (never-bought item): no warning", w["3"] == [], w["3"])
        check("bill 4 (item bought once elsewhere): no warning, below two", w["4"] == [], w["4"])
        check("bill 600 (carry): computed too, and quiet", w["600"] == [])
        check("flagged bills carry no warn key", all("warn" not in d for d in f1))
        html2 = m1._bill_block(0, [d for d in t1 if d["bill_no"] == "2"][0])
        check("the warning renders on bill 2, above Theek hai, naming both suppliers",
              "swarn" in html2 and "TYRO BR" in html2 and "KEDAR" in html2 and "DAANSHI PHARMA" in html2
              and html2.index("swarn") < html2.index("Theek hai"))
        html1 = m1._bill_block(1, [d for d in t1 if d["bill_no"] == "1"][0])
        check("no warning box on bill 1", "swarn" not in html1)
        check("the new reason is offered under Theek nahi", "value='supplier'" in html1 and "Supplier galat likha" in html1)
        check("a bill with no warn key renders as before", "swarn" not in m1._bill_block(2, {"supplier_norm": "X", "bill_no": "9", "bill_date": "2026-09-17"}))
        # robustness: no purchase_line table at all -> no warning, no crash
        cx2 = sqlite3.connect(os.path.join(tmp, "f2.db")); cx2.row_factory = sqlite3.Row
        check("no purchase_line table: empty warning, no crash", m1._supplier_warn_s285(cx2, {"supplier_norm": "A", "bill_no": "1", "bill_date": "2026-09-17"}) == [])
        check("the stylesheet carries the one new rule once", io.open(work, encoding="utf-8").read().count(".bill .swarn{") == 1)
        # _save_bills accepts the new reason and raises no claim for it
        m1._save_bills(cx1, "2026-09-17", "amir", {"n": "1", "k_0": "DAANSHI|2|2026-09-17", "r_0": "supplier"})
        row = cx1.execute("SELECT reason FROM amir_bill_disposition WHERE supplier_norm='DAANSHI' AND bill_no='2'").fetchone()
        check("Supplier galat likha is saved as the bill's answer", row and row["reason"] == "supplier")
        n_claims = cx1.execute("SELECT COUNT(*) FROM amir_claim WHERE bill_no='2'").fetchone()[0] if m1._table_exists(cx1, "amir_claim") else 0
        check("...and raises no claim for Darpan", n_claims == 0, n_claims)
        t3, c3, f3 = m1._bills(cx1, "2026-09-17")
        check("...and the bill moves to flagged until he marks Theek hai", ("DAANSHI", "2") in keyset(f3) and ("DAANSHI", "2") not in keyset(t3))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n = len(FAILS)
    print("S285 selftest: %d check(s) failed%s" % (n, (": " + ", ".join(FAILS)) if n else ""))
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
