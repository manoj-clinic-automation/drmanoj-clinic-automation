#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proof_s749.py -- S749: the purchase check as it stands on this box's own databases, READ ONLY (both opened mode=ro; only register(),
_month_summary() and s749_month_open(), which read). The DRY run of F-1153: run it on the LIVE files and on the kit's files and read the
difference -- every bill whose state or whose-line the kit re-states (the one-rupee bills, Kedar A000211, the four clipped bills, Ravi).
    python3 -B proof_s749.py <finance dir to read with> <shared dir> <finance.db> <assets.db> [--brief]
Prints, per counted month: one line per bill (supplier · bill · date · Marg · paper · state · whose), the month's words, the lock's holds,
the bills with no item lines. One last line:
    PROOF S749: <months> counted month(s) · <bills> bills · <open> open · no item lines: <n> · <state counts>
Supplier names, bill numbers, scan stamps and amounts only -- no phone number, no patient detail."""
import os
import sqlite3
import sys
import time
import traceback


def rs(p):
    if p is None:
        return "-"
    p = int(p)
    return "%sRs %s%s" % ("-" if p < 0 else "", "{:,}".format(abs(p) // 100), (".%02d" % (abs(p) % 100)) if abs(p) % 100 else "")


def main():
    if len(sys.argv) < 5:
        print(__doc__)
        print("PROOF S749: ERROR usage")
        return 2
    code, shared, db, adb = (os.path.abspath(x) for x in sys.argv[1:5])
    brief = "--brief" in sys.argv
    sys.path.insert(0, shared)
    sys.path.insert(0, code)
    os.environ["SHARED_LIB_DIR"] = shared
    import warnings
    warnings.simplefilter("ignore")
    try:
        import purchase_app as PA
        PA._assets_db = adb
        import scan_register as SR
        con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=30)
        con.row_factory = sqlite3.Row
        months = sorted(m for m in SR.months_with_bills(con, 24) if SR.month_class(con, m) == "counted")
    except Exception:                                         # noqa: BLE001
        print(traceback.format_exc()[-1500:])
        print("PROOF S749: ERROR the register could not be read")
        return 1
    new = hasattr(SR, "s749_month_open")
    print("S749 proof · read only · %s files · counted months: %s" % ("the kit's" if new else "the LIVE", ", ".join(months) or "none"))
    tot_bills = tot_open = tot_nolines = 0
    counts = {}
    t_all = 0.0
    for m in months:
        try:
            t0 = time.time()
            r = SR.register(con, m)
            s = PA._month_summary(con, m)
            gate = PA._lock_gate(con, m, s)
            took = time.time() - t0
            t_all += took
        except Exception:                                     # noqa: BLE001
            print(traceback.format_exc()[-1200:])
            print("PROOF S749: ERROR %s could not be read" % m)
            return 1
        print("== %s · %d bill(s) · read in %.2f s" % (m, r["total"], took))
        for x in sorted(r["rows"], key=lambda z: (z["date"], z["id"])):
            a = x.get("agree") or {}
            paper = rs(a.get("scan_p")) if a.get("scan_p") else "-"
            word = SR.STATE_EN.get(x["state"], x["state"])
            if not brief or x["state"] not in ("verified", "has_scan", "accepted", "confirmed"):
                print("  %-28s %-14s %s  %-13s %-13s %-22s %s" % (x["supplier"][:28], str(x["bill_no"])[:14], x["date"], rs(x["amount_p"]), paper, word,
                                                                   (x.get("whose") or "")[:60]))
            counts[word] = counts.get(word, 0) + 1
        tot_bills += r["total"]
        if new:
            n = SR.s749_month_open(con, m, r)
            print("  the month's words: %s · %s" % (n["words"], n["neft"]))
            tot_open += n["open"]
        else:
            open_n = (r["total"] - r["settled"]) + r.get("open_scans", 0)
            print("  settled %d of %d · open %d" % (r["settled"], r["total"], open_n))
            tot_open += open_n
        nl = s.get("no_lines") or []
        tot_nolines += len(nl)
        print("  no item lines: %d%s" % (len(nl), (" -- " + ", ".join("%s %s" % (b["supplier_norm"][:20], b["bill_no"]) for b in nl[:6])) if nl else ""))
        print("  the lock: %s" % ("OPEN" if gate[0] else "holds -- " + " | ".join(gate[1])[:600]))
    print("PROOF S749: %d counted month(s) · %d bills · %d open · no item lines: %d · %s · read in %.1f s"
          % (len(months), tot_bills, tot_open, tot_nolines, ", ".join("%s %d" % (k, v) for k, v in sorted(counts.items())), t_all))
    if t_all > 20:
        print("PROOF S749: ERROR the months took %.1f s to read (more than 20 s) -- too slow for the live pages" % t_all)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
