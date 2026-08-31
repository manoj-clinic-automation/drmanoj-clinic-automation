#!/usr/bin/env python3
"""
anomaly_baseline.py -- S214: the anomaly card's memory.

WHY THIS EXISTS (S212's instruction to S214, verbatim)
    "Fix the anomaly baseline BEFORE that card goes near a page -- across five
     runs today RATE OFF moved 2 -> 156 -> 345 -> 0 on identical data."

    The number moved because the DEFINITION moved -- five variants of the rate
    test were tried in one day (median yardstick, rate-divided-by-quantity,
    fixed tolerance, ...). Each variant is recorded, with the reason it was
    wrong, inside finance_item_anomaly.py itself. S214 proved the surviving
    definition on the real archive:

      * two full scans of 133 days produced BYTE-IDENTICAL flag sets;
      * the owner's known June case (20 tubes on bill A001988, 30-Jun) IS
        flagged: FAR BEYOND ANYTHING SEEN;
      * RATE OFF = 0 on the archive is an HONEST zero, not blindness --
        a synthetic tenfold-off rate flags, a synthetic 50%-off flags, and
        a 25% discount (real orthotic territory) rightly does not.

THE REMAINING PROBLEM THIS FILE SOLVES
    A stable definition still yields ~344 standing flags over five months --
    mostly common tablets leaving at twice their usual ceiling, which is what
    a two-month course looks like. A card that shows 344 rows is a card nobody
    reads. The fix is the same one the daily sweep uses (S210_SWEEP, baseline
    78): FREEZE the standing findings once, and alert only on what is NEW.

USAGE
    python3 anomaly_baseline.py --db /root/finance/finance.db --rebuild
        Full deterministic scan; writes the baseline file; prints the count
        and the set md5. Run once at adoption, and again only when the owner
        accepts a new standing set.

    python3 anomaly_baseline.py --db /root/finance/finance.db
        Scans, diffs against the baseline, lists ONLY NEW flags (and counts
        flags that have left). Exit 0 = nothing new; exit 1 = new flags;
        exit 2 = no baseline yet.

READ-ONLY against the database. Writes nothing but its own baseline file.
Patient identity: prints bill numbers and items, never patient numbers.
"""
import argparse
import collections
import hashlib
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import finance_item_anomaly as A   # the S211_MATCH definition, unchanged

BASELINE_DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "anomaly_baseline.txt")


def scan_all(db):
    """Every flag in the whole archive, one sorted line per flag.

    The line is the flag's IDENTITY (date|bill|seq|verdict|item), not its
    prose: detail text may be reworded without inventing 'new' findings.
    """
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    con.row_factory = sqlite3.Row
    dates = [r[0] for r in con.execute(
        "SELECT DISTINCT business_date FROM sale_line_item "
        "WHERE is_return=0 ORDER BY 1")]
    lines, tally = [], collections.Counter()
    for d in dates:
        out, t = A.scan_day(con, d)
        tally.update(t)
        for o in out:
            lines.append("%s|%s|%s|%s|%s" % (
                d, o["bill"], o["seq"], o["verdict"], o["item"]))
    con.close()
    return sorted(lines), tally


def set_md5(lines):
    return hashlib.md5("\n".join(lines).encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--baseline", default=BASELINE_DEFAULT)
    ap.add_argument("--rebuild", action="store_true",
                    help="accept the current flag set as the standing baseline")
    args = ap.parse_args()

    lines, tally = scan_all(args.db)
    md5 = set_md5(lines)
    counts = collections.Counter(l.split("|")[3] for l in lines)

    if args.rebuild:
        tmp = args.baseline + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("# anomaly_baseline -- one line per accepted standing flag\n")
            f.write("# set_md5 %s  flags %d\n" % (md5, len(lines)))
            for l in lines:
                f.write(l + "\n")
        os.replace(tmp, args.baseline)
        print("BASELINE WRITTEN: %d flags, set md5 %s" % (len(lines), md5))
        print("  by verdict: %s" % dict(counts))
        print("  scan tally: %s" % dict(tally))
        return 0

    if not os.path.exists(args.baseline):
        print("NO BASELINE at %s -- run with --rebuild first" % args.baseline)
        return 2
    with open(args.baseline, encoding="utf-8") as f:
        base = set(l.strip() for l in f if l.strip() and not l.startswith("#"))
    cur = set(lines)
    new, gone = sorted(cur - base), sorted(base - cur)
    print("flags now %d | baseline %d | NEW %d | resolved %d | set md5 %s"
          % (len(cur), len(base), len(new), len(gone), md5))
    for l in new:
        print("NEW  " + l)
    if gone:
        print("(%d baseline flags no longer present -- rebuild when accepted)"
              % len(gone))
    return 1 if new else 0


if __name__ == "__main__":
    sys.exit(main())
