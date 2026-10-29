#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s679.py -- the server side of kit S679_SALE_BILLED_TO_PARTY (reports_tile.py).

    python3 -B walk_s679.py --new <root> --lib <root> --db <copy> --scratch <dir> [--old-root <root>]
    python3 -B walk_s679.py --old <root> --lib <root> --db <copy> --scratch <dir>          (the control: the live file must go red)

<root>/finance/reports_tile.py is the file under test.  --db is a COPY of finance.db, read only here.  The reason under test is the one the
medical PC's S679 watcher sends -- made up (bill A999901), never a real row.  With --old-root, old = new: hindi_reason of every distinct
(reason, verdict) the door has ever stored is the same under the old and the new file.
Last line: "N of N green" (new) or "K S679 check(s) red . M older red . G green" (old).
"""
import argparse
import importlib.util
import os
import shutil
import sqlite3
import sys

R = "the medical PC refused it: the reader refused it: bill A999901 is billed to a party account, not cash or UPI"
STOP = "the medical PC refused it: the reader refused it (line 12)"
GLOB = "the medical PC refused it: the reader refused it (line [0-9]*)"


def load(root, lib, scratch, tag):
    d = os.path.join(scratch, "mod_" + tag)
    os.makedirs(d, exist_ok=True)
    shutil.copyfile(os.path.join(root, "finance", "reports_tile.py"), os.path.join(d, "reports_tile.py"))
    for p in (os.path.join(lib, "finance", "spine"), os.path.join(lib, "finance")):
        if p not in sys.path:
            sys.path.append(p)
    sys.path.insert(0, d)
    spec = importlib.util.spec_from_file_location("reports_tile_" + tag, os.path.join(d, "reports_tile.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    sys.path.remove(d)
    return m


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--new")
    g.add_argument("--old")
    ap.add_argument("--lib")
    ap.add_argument("--db", required=True)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--old-root")
    a = ap.parse_args()
    root = a.new or a.old
    lib = a.lib or root
    os.makedirs(a.scratch, exist_ok=True)
    m = load(root, lib, a.scratch, "test")
    res = []

    def ck(name, fn, s679):
        try:
            ok = bool(fn())
        except Exception as e:                                         # noqa: BLE001
            ok, name = False, name + " (raised %s: %s)" % (type(e).__name__, str(e)[:100])
        res.append((name, ok, s679))

    hi = m.hindi_reason(R, "REFUSED")
    ck("T1 the party reason in Hindi names the bill and says to correct it in Marg, then export again",
       lambda: hi.startswith("Bill A999901 party ke khaate mein bana hai") and "Cash ya UPI" in hi and "dobara nikaaliye" in hi, True)
    ck("T2 it is NOT a reader stop (the staff must act; S556's held row is not used)", lambda: not m.reader_stop(R), False)
    ck("T3 nor does the duty map's reader-stop GLOB match it (shavez.sale_report stays due)",
       lambda: sqlite3.connect(":memory:").execute("SELECT ? GLOB ?", (R, GLOB)).fetchone()[0] == 0, False)
    row = {"md5": "walk679" + "0" * 25, "type": "SALE_BILLWISE", "verdict": "REFUSED", "reason": R, "pc_verdict": "",
           "received_at": "2099-01-15T09:57:09+05:30", "stamp": "20990115-095709", "date_from": "", "date_to": ""}
    ck("T4 the due day's sale file is judged 'wrong', its Hindi line naming bill A999901",
       lambda: (lambda f: f["j"] == "wrong" and "A999901" in f["why_hi"])(m._s500_sale_file(dict(row))), True)
    ck("T5 a true reader stop still reads 'Medical PC is file ko padh nahi paya -- aapko kuch nahi karna' (unchanged)",
       lambda: m.reader_stop(STOP) and "padh nahi paya" in m.hindi_reason(STOP), False)
    ck("T6 an ordinary medical-PC refusal keeps its words (unchanged)",
       lambda: m.hindi_reason("the medical PC refused it: the reader refused it", "REFUSED").startswith("Medical PC ne file manzoor nahi ki"), False)
    if a.new and a.old_root:
        old = load(a.old_root, lib, a.scratch, "old")
        cx = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
        pairs = cx.execute("SELECT DISTINCT reason, verdict FROM mi_file").fetchall()
        diff = [(r, v) for r, v in pairs if m.hindi_reason(r, v) != old.hindi_reason(r, v)]
        print("  --  old = new: %d distinct (reason, verdict) pairs at the door, %d differ" % (len(pairs), len(diff)))
        for r, v in diff[:10]:
            print("      RED %r / %s" % (str(r)[:100], v))
        ck("T7 old = new on every reason the door has ever stored", lambda: not diff and pairs, False)
    for name, ok, _s in res:
        print("  %s  %s" % ("ok " if ok else "RED", name))
    if a.new:
        n = sum(1 for r in res if r[1])
        print("%d of %d green" % (n, len(res)))
        sys.exit(0 if n == len(res) else 1)
    print("%d S679 check(s) red · %d older red · %d green" % (sum(1 for r in res if not r[1] and r[2]),
                                                          sum(1 for r in res if not r[1] and not r[2]), sum(1 for r in res if r[1])))


if __name__ == "__main__":
    main()
