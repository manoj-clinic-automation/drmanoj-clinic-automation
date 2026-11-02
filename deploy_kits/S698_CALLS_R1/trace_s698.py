#!/usr/bin/env python3
"""
trace_s698.py -- S698 (F-1083): READ-ONLY trace of the doubled call rows, on console.db (mode=ro).
Counts only; no number, no name. It need not be run by hand: the installer prints it once before the repair.

For every day since --since it groups the calls by the fold keys (portal_console.fold_keys: MyOperator's uuid,
the recording file, the session id, the exact end-second) and says:
  rows . calls after the fold . pairs folded . of those: SAME client_ref_id (the receiver's row drift, one key
  written twice) / DIFFERENT client_ref_id (the two events carried different session ids) . by which key they met.
"""
import argparse
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="/root/wa/console.db")
    ap.add_argument("--since", default="2026-10-20")
    ap.add_argument("--builder", default="/root/wa/portal_console.py", help="the builder whose fold_calls is used")
    a = ap.parse_args()
    bdir = os.path.dirname(os.path.abspath(a.builder))
    sys.path.insert(0, bdir)
    import importlib.util
    spec = importlib.util.spec_from_file_location("pc_s698", a.builder)
    pc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pc)
    if not hasattr(pc, "fold_calls"):
        print("TRACE: the builder at %s has no fold_calls (not the S698 builder) -- nothing traced" % a.builder)
        return 1
    if not os.path.exists(a.db):
        print("TRACE: %s is missing -- nothing traced" % a.db)
        return 1
    conn = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
    conn.row_factory = sqlite3.Row
    cols = ("client_ref_id", "ref_id", "session_id", "category", "status", "total_duration", "recording_filename",
            "ended_at_ist", "source_event", "phone10")
    days = {}
    for r in conn.execute("SELECT %s FROM calls WHERE substr(ended_at_ist,1,10)>=? ORDER BY ended_at_ist, id" % ",".join(cols), (a.since,)):
        d = dict(r)
        days.setdefault((d["ended_at_ist"] or "")[:10], []).append(d)
    print("TRACE S698 (read-only, counts only) -- console.db built %s" %
          (conn.execute("SELECT v FROM meta WHERE k='built_at'").fetchone() or ["?"])[0])
    print("  %-11s %5s %6s %6s %6s %6s   %s" % ("day", "rows", "calls", "pairs", "same", "diff", "met by"))
    tot = {"rows": 0, "calls": 0, "pairs": 0, "same": 0, "diff": 0}
    for day in sorted(days):
        kept, st = pc.fold_calls(days[day])
        by = " ".join("%s=%d" % (k, v) for k, v in st["by"].items() if v)
        print("  %-11s %5d %6d %6d %6d %6d   %s" % (day, st["rows_in"], st["rows_out"], st["folded"],
                                                  st["same_key_pairs"], st["diff_key_pairs"], by or "-"))
        tot["rows"] += st["rows_in"]; tot["calls"] += st["rows_out"]; tot["pairs"] += st["folded"]
        tot["same"] += st["same_key_pairs"]; tot["diff"] += st["diff_key_pairs"]
    print("  %-11s %5d %6d %6d %6d %6d" % ("total", tot["rows"], tot["calls"], tot["pairs"], tot["same"], tot["diff"]))
    if tot["pairs"] == 0:
        print("  no doubled rows since %s" % a.since)
    elif tot["same"] >= tot["diff"]:
        print("  the pairs carry the SAME key: the receiver's row arithmetic drifted (one key written twice) -- the v3.2 receiver mends it")
    else:
        print("  the pairs carry DIFFERENT keys: the two events of one call came with different session ids -- the uuid is the second key now")
    return 0


if __name__ == "__main__":
    sys.exit(main())
