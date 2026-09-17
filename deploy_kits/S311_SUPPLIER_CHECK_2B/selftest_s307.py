#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_s307.py -- offline proof for S307_SUPPLIER_CHECK_2. Nothing live is touched.

    python3 -B selftest_s307.py --live /path/to/a/copy/of/amir_day.py      (S285, b3c20319)

The S285 fixture, plus: bill 502 under MANNAT and DEEPAM with the same amount; bill 252 under YUVIKA and DEEPAM
with different amounts; a GHOST 600 only in a superseded export beside KEDAR 600; a return R9 under SOLO of an
item KEDAR has always supplied; a return R8 under KEDAR of KEDAR's own item. Both modules (before / after) run
their own _bills() and _bill_block().
"""
import argparse, hashlib, importlib.util, io, os, py_compile, shutil, sqlite3, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
FAILS = []
PIN = "b3c20319c4808ebc64bec197c951468c"


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("ok " if ok else "FAIL", name, ("  -- " + str(detail)) if (detail and not ok) else ""))
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
        # S307: the same number and date under two suppliers
        ("MANNAT", "MANNAT PHARMA", "502", "2026-09-17", 900, "E2"),
        ("DEEPAM", "DEEPAM PHARMA", "502", "2026-09-17", 900, "E2"),
        ("YUVIKA", "YUVIKA SURGICALS", "252", "2026-09-17", 380, "E2"),
        ("DEEPAM", "DEEPAM PHARMA", "252", "2026-09-17", 190, "E2"),
        ("GHOST", "GHOST TRADERS", "600", "2026-09-05", 2000, "E1"),   # same number as KEDAR 600, only in a dead export
        # S307: a purchase RETURN under a supplier who never supplied the item
        ("SOLO", "SOLO TRADERS", "R9", "2026-09-17", -100, "E2"),
        ("KEDAR", "KEDAR PHARMACEUTICAL", "R8", "2026-09-17", -100, "E2"),
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
        ("SOLO", "R9", "2026-09-17", "TYRO BR", 100, "L2", "ITEMWISE"),
        ("KEDAR", "R8", "2026-09-17", "MEG QCS", 100, "L2", "ITEMWISE"),
    ]
    cx.executemany("INSERT INTO purchase_line (supplier_norm,bill_no,bill_date,item,amount_p,source_md5,line_type) "
                   "VALUES (?,?,?,?,?,?,?)", lines)
    cx.execute("INSERT INTO amir_bill_disposition (supplier_norm,bill_no,bill_date,day,reason,by_user,at) "
               "VALUES ('KEDAR','7','2026-09-17','2026-09-17','short','amir','2026-09-17T09:30:00')")
    cx.commit()
    return cx




def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", required=True)
    a = ap.parse_args(argv)
    py = sys.executable
    tmp = tempfile.mkdtemp(prefix="s307_")
    print("part 1 -- the patcher on a COPY")
    check("the live copy is S285's pin", md5(a.live) == PIN, md5(a.live))
    old, work = os.path.join(tmp, "amir_day_before.py"), os.path.join(tmp, "amir_day.py")
    shutil.copy2(a.live, old); shutil.copy2(a.live, work)
    import patch_supplier_check2_s307 as pm
    s = io.open(work, encoding="utf-8").read()
    for i, (o, _n) in enumerate(pm.EDITS):
        check("anchor %d present exactly once" % (i + 1), s.count(o) == 1, s.count(o))
    patcher = os.path.join(HERE, "patch_supplier_check2_s307.py")
    r = subprocess.run([py, "-B", patcher, "--file", work, "--from", "0" * 32], capture_output=True, text=True)
    check("wrong --from refused, nothing written", r.returncode != 0 and md5(work) == PIN)
    r = subprocess.run([py, "-B", patcher, "--file", work, "--from", PIN], capture_output=True, text=True)
    check("patch applies", r.returncode == 0, r.stdout + r.stderr)
    after = md5(work)
    print("  pin: %s -> %s" % (PIN, after))
    try:
        py_compile.compile(work, cfile=os.path.join(tmp, "x.pyc"), doraise=True); check("patched file compiles", True)
    except Exception as e:  # noqa: BLE001
        check("patched file compiles", False, e)
    r = subprocess.run([py, "-B", patcher, "--file", work, "--from", after], capture_output=True, text=True)
    check("second run ALREADY PATCHED, pin unchanged", "ALREADY" in r.stdout and md5(work) == after)
    check("backup is the S285 bytes", md5(work + ".bak_S307_" + PIN[:8]) == PIN)

    print("part 2 -- both modules over the fixture")
    m0, m1 = load(old, "amir_before"), load(work, "amir_after")
    cx0 = fixture(os.path.join(tmp, "f0.db"), m0)
    cx1 = fixture(os.path.join(tmp, "f1.db"), m1)
    t0, c0, f0 = m0._bills(cx0, "2026-09-17")
    t1, c1, f1 = m1._bills(cx1, "2026-09-17")
    k = lambda rows: sorted((r["supplier_norm"], r["bill_no"]) for r in rows)   # noqa: E731
    check("the lists are exactly S285's lists", (k(t0), k(c0), k(f0)) == (k(t1), k(c1), k(f1)))
    check("S285's warnings are unchanged", {(d["supplier_norm"], d["bill_no"]): d["warn"] for d in t0 + c0} == {(d["supplier_norm"], d["bill_no"]): d["warn"] for d in t1 + c1})
    by = {(d["supplier_norm"], d["bill_no"]): d for d in t1 + c1}
    check("502 under MANNAT names DEEPAM, same amount", by[("MANNAT", "502")]["twin"] == [("DEEPAM PHARMA", 900, True)], by[("MANNAT", "502")]["twin"])
    check("502 under DEEPAM names MANNAT, same amount", by[("DEEPAM", "502")]["twin"] == [("MANNAT PHARMA", 900, True)], by[("DEEPAM", "502")]["twin"])
    check("252 under YUVIKA names DEEPAM, different amount", by[("YUVIKA", "252")]["twin"] == [("DEEPAM PHARMA", 190, False)], by[("YUVIKA", "252")]["twin"])
    check("a bill alone on its number has no twin", by[("KEDAR", "1")]["twin"] == [] and by[("DAANSHI", "2")]["twin"] == [])
    check("KEDAR 600: a same-number bill only in a superseded export is not a twin", by[("KEDAR", "600")]["twin"] == [], by[("KEDAR", "600")]["twin"])
    check("return R9 under SOLO of KEDAR's item: S285 warns", by[("SOLO", "R9")]["warn"] == [("TYRO BR", "KEDAR", 3)], by[("SOLO", "R9")]["warn"])
    check("return R8 under KEDAR of KEDAR's own item: quiet", by[("KEDAR", "R8")]["warn"] == [])
    h502 = m1._bill_block(0, by[("MANNAT", "502")])
    check("502 renders: two supplier ke naam, the other name, the amount, above Theek hai",
          "Ek hi bill do supplier ke naam" in h502 and "DEEPAM PHARMA" in h502 and h502.index("swarn") < h502.index("Theek hai"))
    h252 = m1._bill_block(1, by[("YUVIKA", "252")])
    check("252 renders the softer look", "Do alag supplier ho sakte hain" in h252 and "Ek hi bill" not in h252)
    hr9 = m1._bill_block(2, by[("SOLO", "R9")])
    check("return R9 renders as a wapsi to the wrong supplier", "wapsi" in hr9 and "kabhi <b>SOLO TRADERS</b> se nahi aaya" in hr9 and "KEDAR" in hr9)
    h2 = m1._bill_block(3, by[("DAANSHI", "2")])
    h2_old = m0._bill_block(3, [d for d in t0 + c0 if (d["supplier_norm"], d["bill_no"]) == ("DAANSHI", "2")][0])
    check("an ordinary S285 warning renders exactly as before", h2 == h2_old)
    h1_old = m0._bill_block(4, [d for d in t0 + c0 if (d["supplier_norm"], d["bill_no"]) == ("KEDAR", "1")][0])
    check("a quiet bill renders exactly as before", m1._bill_block(4, by[("KEDAR", "1")]) == h1_old)
    cx2 = sqlite3.connect(os.path.join(tmp, "f2.db"))
    check("no tables: no twin, no crash", m1._twin_bills_s307(cx2, {"supplier_norm": "A", "bill_no": "1", "bill_date": "2026-09-17"}) == [])
    check("flagged bills carry no twin key", all("twin" not in d for d in f1))
    print("\n%d failed" % len(FAILS))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
