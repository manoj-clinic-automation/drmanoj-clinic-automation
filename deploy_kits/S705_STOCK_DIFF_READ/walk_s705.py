#!/usr/bin/env python3
"""Walk for S705 on a MADE-UP spine (no real data). Builds the spine's own schema from spine_build.py's DDL,
runs the reader, checks each line; the CONTROL (the same spine with no OPEN finding) must list 0 items."""
import os, re, sqlite3, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = sys.argv[1]           # path to spine_build.py (for the DDL)
src = open(BUILD).read()
i = src.index("CREATE TABLE sp_meta"); ddl = src[i:src.index('"""', i)]
def make(path, open_note="OPEN at the latest closing"):
    con = sqlite3.connect(path); con.executescript(ddl)
    con.executemany("INSERT INTO sp_meta VALUES (?,?)", [("built", "2026-11-04T23:50:48"), ("checkable", "2026-10-30,2026-10-31,2026-11-02"), ("pending", "2026-11-04")])
    con.executemany("INSERT INTO sp_item (k20, name, packing) VALUES (?,?,?)", [("ALPHA", "ALPHA TAB", "10"), ("BETA", "BETA SYP", ""), ("GAMMA", "GAMMA GEL", ""), ("DELTA", "DELTA CAP", "")])
    con.executemany("INSERT INTO sp_check VALUES (?,?,?,?,?)", [
        ("2026-10-30", "ALPHA", 10, 10, 0), ("2026-10-31", "ALPHA", 15, 10, 5), ("2026-11-02", "ALPHA", 13, 8, 5),
        ("2026-10-30", "BETA", 4, 4, 0), ("2026-10-31", "BETA", 4, 4, 0), ("2026-11-02", "BETA", 3, 3, 0),
        ("2026-10-30", "GAMMA", 2, 4, -2), ("2026-10-31", "GAMMA", 2, 4, -2), ("2026-11-02", "GAMMA", 2, 4, -2),
        ("2026-10-30", "DELTA", 9, 9, 0), ("2026-10-31", "DELTA", 9, 9, 0), ("2026-11-02", "DELTA", 6, 9, -3)])
    con.executemany("INSERT INTO sp_finding VALUES (?,?,?,?)", [
        ("2026-10-31", "ALPHA", 5, "TIMING: keyed after the export"), ("2026-11-02", "ALPHA", 5, open_note),
        ("2026-11-02", "GAMMA", -2, open_note), ("2026-11-02", "DELTA", -3, "VOUCHER: Amir's stock voucher filed in Marg (-3)")])
    con.executemany("INSERT INTO sp_move VALUES (?,?,?,?,?)", [
        ("ALPHA", "2026-10-01", "OPENING", 10, "op"), ("ALPHA", "2026-11-01", "SALE", -2, "A0001"),
        ("BETA", "2026-10-01", "OPENING", 4, "op"), ("BETA", "2026-11-02", "SALE", -1, "A0002"),
        ("GAMMA", "2026-10-01", "OPENING", 4, "op"), ("DELTA", "2026-10-01", "OPENING", 9, "op"),
        ("ALPHA", "2026-11-03", "PURCHASE", 20, "SUPP X/77")])
    con.executemany("INSERT INTO sp_close VALUES (?,?,?,?)", [("2026-11-04", "ALPHA", 33, "m"), ("2026-11-04", "GAMMA", 2, "m")])
    con.commit(); con.close()
def run(db):
    before = open(db, "rb").read()
    out = subprocess.run([sys.executable, "-B", os.path.join(HERE, "s705_stock_diffs.py"), db], capture_output=True, text=True).stdout
    return out, open(db, "rb").read() == before
ok = 0; bad = 0
def check(name, cond):
    global ok, bad
    print(("  ok   " if cond else "  RED  ") + name); ok += bool(cond); bad += (not cond)
with tempfile.TemporaryDirectory() as t:
    db = os.path.join(t, "spine.db"); make(db)
    out, same = run(db)
    print(out)
    check("the spine file is byte-identical after the read (nothing written)", same)
    check("two OPEN items listed (ALPHA, GAMMA), the VOUCHER and TIMING ones not", "OPEN at 2026-11-02: 2 item(s)" in out and "DELTA" not in out.split("OPEN at")[1])
    check("ALPHA diff +5 began after 10-30: Marg 10->15, spine 10->10, nothing moved", re.search(r"ALPHA TAB \[10\]  diff \+5 .*\n    began after 2026-10-30 \(diff was 0\): Marg 10->15, spine 10->10; moved in the spine: nothing", out) is not None)
    check("ALPHA at the pending closing: Marg 33, spine 28; the purchase after the latest closing named", "at 2026-11-04 (pending) Marg 33, spine 28" in out and "11-03 +20 SUPP X/77" in out)
    check("GAMMA -2 present since the first checkable closing", re.search(r"GAMMA GEL  diff -2 .*\n    present since the first checkable closing 2026-10-30", out) is not None)
    check("the END line says nothing was written", "S705 END -- 2 item(s); nothing was written" in out)
    check("no ten-digit run in the output", re.search(r"\d{10}", out) is None)
    db2 = os.path.join(t, "control.db"); make(db2, open_note="TIMING: closed by a later closing")
    out2, _ = run(db2)
    check("CONTROL: the same spine with no OPEN finding lists 0 items (a reader that ignored the note would go red here)", "OPEN at 2026-11-02: 0 item(s)" in out2)
print("WALK S705: %d ok, %d red" % (ok, bad)); sys.exit(1 if bad else 0)
