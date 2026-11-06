#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proof_s736.py -- S736: what the server would ask reception for, on this box's own databases, READ ONLY (both opened mode=ro; the plan
only reads -- porders_s454.s736_plan; nothing is asked, withdrawn or written).

    python3 -B proof_s736.py <new finance dir> <shared dir> <finance.db> <assets.db>

Prints every scan the server would send to reception now (stamp, month, reason, try), every scan it would put before the owner and Shavez
(two rescans behind), every server ask it would withdraw, the open asks already standing, and one last line:
    PROOF S736: N ask(s) (Oct a, Nov b, ...) · E for the owner and Shavez · W withdrawn · O open asks already
or "PROOF S736: REFUSED ..." (an ask outside a counted month -- September raises nothing, D848) / "PROOF S736: ERROR ...".
No phone number or patient detail is printed: supplier names, bill numbers and scan stamps only."""
import os
import sqlite3
import sys
import traceback


def main():
    if len(sys.argv) < 5:
        print(__doc__)
        print("PROOF S736: ERROR usage")
        return 2
    new, shared, db, adb = (os.path.abspath(x) for x in sys.argv[1:5])
    sys.path.insert(0, shared)
    sys.path.insert(0, new)
    os.environ["SHARED_LIB_DIR"] = shared
    import warnings
    warnings.simplefilter("ignore")
    try:
        import purchase_app as PA
        PA._assets_db = adb
        import porders_s454 as P4
        con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=30)
        con.row_factory = sqlite3.Row
        p = P4.s736_plan(con)
    except Exception:                                         # noqa: BLE001
        print(traceback.format_exc()[-1500:])
        print("PROOF S736: ERROR the plan could not be read")
        return 1
    if not p.get("ok"):
        print("PROOF S736: ERROR the asset app's database or scan_quality is not reachable -- nothing would be asked")
        return 1
    f = p["facts"]
    words = P4.S736_REASON_EN
    bad = [x for x in p["ask"] + p["escalated"] if P4.month_class(con, x["month"]) != "counted"]
    print("S736 proof · %s · read only" % P4.OS.now_iso())
    print("the server would ASK reception for a rescan (%d):" % len(p["ask"]))
    for x in p["ask"]:
        print("  %-8s %s · %-28s %-10s %-22s try %d" % (x["stamp"], x["month"], (x["vendor"] or "")[:28], x["bill_no"][:10], words.get(x["reason"], x["reason"]),
                                                       x["tries"] + 1))
    print("for the OWNER and SHAVEZ -- rescanned twice, still in trouble (%d):" % len(p["escalated"]))
    for x in p["escalated"]:
        print("  %-8s %s · %-28s %-10s %s" % (x["stamp"], x["month"], (x["vendor"] or "")[:28], x["bill_no"][:10], words.get(x["reason"], x["reason"])))
    print("server asks it would WITHDRAW (the scan is fine now) (%d): %s" % (len(p["withdraw"]), ", ".join(str(i) for i in p["withdraw"]) or "none"))
    op = [a for a in f["asks"] if not a.get("done_at") and not a.get("withdrawn_at")]
    by = {}
    for a in op:
        by[str(a.get("asked_by") or "")] = by.get(str(a.get("asked_by") or ""), 0) + 1
    print("open asks already standing (%d): %s" % (len(op), " · ".join("%s %d" % (k, v) for k, v in sorted(by.items())) or "none"))
    per = {}
    for x in p["ask"]:
        per[x["month"]] = per.get(x["month"], 0) + 1
    months = ", ".join("%s %d" % (m, n) for m, n in sorted(per.items())) or "none"
    if bad:
        print("PROOF S736: REFUSED %d ask(s) outside a counted month: %s" % (len(bad), ", ".join(x["stamp"] for x in bad[:8])))
        return 1
    print("PROOF S736: %d ask(s) (%s) · %d for the owner and Shavez · %d withdrawn · %d open asks already" % (len(p["ask"]), months, len(p["escalated"]),
                                                                                                     len(p["withdraw"]), len(op)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
