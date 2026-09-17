#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_s282.py -- offline proof for S282_LINE_OWNER. Nothing live is touched.

    python3 -B selftest_s282.py --live /path/to/a/copy/of/purchase_app.py

Part 1 runs the rule over a fixture database shaped like the F-494 case plus the
cases that must NOT be touched. Part 2 applies the patcher to a COPY of the given
live file and proves: anchor once, parses, helper present, idempotent, wrong pin
refused, and the helper inside the patched file gives the same answers as the
one-off repair script on the same fixture.
"""
import argparse
import ast
import hashlib
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
import repair_f494_s282 as rep  # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("ok " if ok else "FAIL", name, ("  -- " + str(detail)) if detail else ""))
    if not ok:
        FAILS.append(name)


def fixture(path):
    con = sqlite3.connect(path)
    con.executescript("""
    CREATE TABLE purchase_bill (id INTEGER PRIMARY KEY, supplier_norm TEXT, bill_no TEXT,
                                bill_date TEXT, amount_p INTEGER);
    CREATE TABLE purchase_line (id INTEGER PRIMARY KEY, supplier_norm TEXT, bill_no TEXT,
                                bill_date TEXT, month TEXT, item TEXT, amount_p INTEGER,
                                net_amount_p INTEGER, line_type TEXT);
    """)
    bills = [("A_PHARMA", "160", "2026-09-01", 537700), ("K_PHARMA", "160", "2026-09-01", 1240000),
             ("A_PHARMA", "77", "2026-09-03", 100), ("K_PHARMA", "77", "2026-09-03", 200),
             ("A_PHARMA", "78", "2026-09-04", 100), ("K_PHARMA", "78", "2026-09-04", 200),
             ("A_PHARMA", "79", "2026-09-05", 100), ("K_PHARMA", "79", "2026-09-05", 200),
             ("A_PHARMA", "80", "2026-09-06", 100), ("K_PHARMA", "80", "2026-09-06", 300),
             ("SOLO", "500", "2026-09-07", 900)]
    con.executemany("INSERT INTO purchase_bill (supplier_norm,bill_no,bill_date,amount_p) VALUES (?,?,?,?)", bills)
    lines = [
        # case 1: the F-494 shape -- ITEMWISE witnesses, then the unowned BILLITEMWISE lines
        ("A_PHARMA", "160", "2026-09-01", "DENGEN PLUS", 640080, 537668, "ITEMWISE"),
        ("K_PHARMA", "160", "2026-09-01", "MEG QCS", 240000, 240000, "ITEMWISE"),
        ("K_PHARMA", "160", "2026-09-01", "ASTOFEN SP", 88000, 88000, "ITEMWISE"),
        ("K_PHARMA", "160", "2026-09-01", "PATOPAN DSR", 320000, 320000, "ITEMWISE"),
        ("K_PHARMA", "160", "2026-09-01", "TYRO BR", 592000, 592000, "ITEMWISE"),
        ("A_PHARMA", "160", "2026-09-01", "DENGEN PLUS", 640080, 537668, "ITEMWISE"),  # a superseded copy
        (None, "160", "2026-09-01", "DENGEN PLUS", 640080, 537668, "BILLITEMWISE"),      # 7
        (None, "160", "2026-09-01", "MEG QCS", 240000, 240000, "BILLITEMWISE"),          # 8
        (None, "160", "2026-09-01", "ASTOFEN SP", 88000, 88000, "BILLITEMWISE"),         # 9
        (None, "160", "2026-09-01", "PATOPAN DSR", 320000, 320000, "BILLITEMWISE"),      # 10
        (None, "160", "2026-09-01", "TYRO BR", 592000, 592000, "BILLITEMWISE"),          # 11
        # case 2: collision, no ITEMWISE witness at all -> stays
        (None, "77", "2026-09-03", "X", 100, 100, "BILLITEMWISE"),                       # 12
        # case 3: collision, ITEMWISE names BOTH suppliers for the same line -> stays
        ("A_PHARMA", "78", "2026-09-04", "Y", 100, 100, "ITEMWISE"),
        ("K_PHARMA", "78", "2026-09-04", "Y", 100, 100, "ITEMWISE"),
        (None, "78", "2026-09-04", "Y", 100, 100, "BILLITEMWISE"),                       # 15
        # case 4: collision, the only witness is a stranger -> stays
        ("STRANGER", "79", "2026-09-05", "Z", 100, 100, "ITEMWISE"),
        (None, "79", "2026-09-05", "Z", 100, 100, "BILLITEMWISE"),                       # 17
        # case 5: a unique bill with an unowned line is rev 2's job, not ours -> untouched here
        (None, "500", "2026-09-07", "W", 900, 900, "BILLITEMWISE"),                      # 18
        # case 6: amount NULL on both sides still matches (IS, not =)
        ("K_PHARMA", "80", "2026-09-06", "V", None, None, "ITEMWISE"),
        (None, "80", "2026-09-06", "V", None, None, "BILLITEMWISE"),                     # 20
        # case 7: same item, DIFFERENT amount -> not a witness
        ("A_PHARMA", "80", "2026-09-06", "U", 100, 100, "ITEMWISE"),
        (None, "80", "2026-09-06", "U", 150, 150, "BILLITEMWISE"),                       # 22
    ]
    con.executemany("INSERT INTO purchase_line (supplier_norm,bill_no,bill_date,item,amount_p,"
                    "net_amount_p,line_type) VALUES (?,?,?,?,?,?,?)", lines)
    con.commit()
    return con


def owners(con):
    return dict(con.execute("SELECT id, supplier_norm FROM purchase_line WHERE line_type='BILLITEMWISE'"))


EXPECT = {7: "A_PHARMA", 8: "K_PHARMA", 9: "K_PHARMA", 10: "K_PHARMA", 11: "K_PHARMA",
          12: None, 15: None, 17: None, 18: None, 20: "K_PHARMA", 22: None}


def part1(tmp):
    print("part 1 -- the rule on the fixture (repair script)")
    con = fixture(os.path.join(tmp, "f1.db"))
    n0, p0 = rep.orphans(con)
    check("fixture starts with 11 unowned lines", n0 == 11, n0)
    placed, left = rep.place(con, rep.by_no_map(con))
    con.commit()
    got = owners(con)
    check("every line lands where the fixture says", got == EXPECT, got)
    check("six placed, five left", (len(placed), len(left)) == (6, 5), (len(placed), len(left)))
    placed2, _ = rep.place(con, rep.by_no_map(con))
    check("second pass places nothing (idempotent)", len(placed2) == 0, len(placed2))
    con.close()
    # dry run writes nothing
    con = fixture(os.path.join(tmp, "f1dry.db"))
    rep.place(con, rep.by_no_map(con), write=False)
    con.commit()
    check("write=False leaves all 11 unowned", rep.orphans(con)[0] == 11)
    con.close()


def helper_from(path):
    src = io.open(path, "r", encoding="utf-8").read()
    tree = ast.parse(src)
    fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_line_owner_s282"]
    if len(fn) != 1:
        return None
    mod = ast.Module(body=fn, type_ignores=[])
    ns = {}
    exec(compile(mod, path, "exec"), ns)
    return ns["_line_owner_s282"]


def md5(p):
    return hashlib.md5(io.open(p, "rb").read()).hexdigest()


def part2(tmp, live):
    print("part 2 -- the patcher on a COPY of %s" % live)
    py = sys.executable
    patcher = os.path.join(HERE, "patch_line_owner_s282.py")
    work = os.path.join(tmp, "purchase_app.py")
    shutil.copy2(live, work)
    before = md5(work)
    src = io.open(work, "r", encoding="utf-8").read()
    import patch_line_owner_s282 as pm
    check("anchor present exactly once in the live bytes", src.count(pm.A_OLD) == 1, src.count(pm.A_OLD))
    check("helper not already present", pm.MARK not in src)
    r = subprocess.run([py, "-B", patcher, "--file", work, "--from", "0" * 32], capture_output=True, text=True)
    check("wrong --from is refused", r.returncode != 0 and "REFUSING" in (r.stdout + r.stderr))
    check("...and nothing was written", md5(work) == before)
    r = subprocess.run([py, "-B", patcher, "--file", work, "--from", before, "--check"], capture_output=True, text=True)
    check("--check reports and writes nothing", r.returncode == 0 and md5(work) == before, r.stdout.strip())
    r = subprocess.run([py, "-B", patcher, "--file", work, "--from", before], capture_output=True, text=True)
    check("patch applies", r.returncode == 0, r.stdout.strip() + r.stderr.strip())
    after = md5(work)
    check("bytes changed", after != before)
    check("backup written beside it", os.path.exists("%s.bak_S282_%s" % (work, before[:8])))
    try:
        py_compile.compile(work, doraise=True)
        check("patched file compiles", True)
    except Exception as e:  # noqa: BLE001
        check("patched file compiles", False, e)
    src2 = io.open(work, "r", encoding="utf-8").read()
    check("the call sits inside _redate_lines, before the month refresh",
          "    _line_owner_s282(con, by_no)\n    con.execute(\"UPDATE purchase_line SET month=" in src2)
    check("helper defined once", src2.count("def _line_owner_s282(") == 1)
    r = subprocess.run([py, "-B", patcher, "--file", work, "--from", after], capture_output=True, text=True)
    check("second run says ALREADY PATCHED and leaves the pin", r.returncode == 0 and "ALREADY" in r.stdout and md5(work) == after)
    print("  pin of the patched copy: %s  (the installer reads its own off the disk)" % after)
    fn = helper_from(work)
    check("helper can be lifted out of the patched file", fn is not None)
    if fn:
        con = fixture(os.path.join(tmp, "f2.db"))
        n = fn(con, rep.by_no_map(con))
        con.commit()
        check("the helper in purchase_app.py gives the fixture's answers", owners(con) == EXPECT, owners(con))
        check("...and reports six placed", n == 6, n)
        check("...and is idempotent", fn(con, rep.by_no_map(con)) == 0)
        con.close()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", required=True, help="a COPY of the live purchase_app.py bytes")
    a = ap.parse_args(argv)
    tmp = tempfile.mkdtemp(prefix="s282_")
    try:
        part1(tmp)
        part2(tmp, a.live)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n = len(FAILS)
    print("S282 selftest: %d check(s) failed%s" % (n, (": " + ", ".join(FAILS)) if n else ""))
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
