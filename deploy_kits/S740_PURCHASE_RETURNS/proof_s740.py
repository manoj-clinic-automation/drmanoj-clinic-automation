#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proof_s740.py -- S740: the purchase returns as they stand now, on this box's own databases, READ ONLY (both opened mode=ro; only
scan_register.s740_model, which reads).
    python3 -B proof_s740.py <new finance dir> <shared dir> <finance.db> <assets.db>
Prints reception's questions, every return (kind, stage, whose), the count shortages for the owner, any dealer's return line no return
matches, and whether Janta 21965 (D839) is on the question list now (so the seed applies). One last line:
    PROOF S740: Q question(s) · R return(s) pending (D for Amir to enter) · S resolved · F count line(s) · Janta 21965: <state>
Supplier names, bill numbers, scan stamps, item names and amounts only -- no phone number, no patient detail."""
import os
import sqlite3
import sys
import traceback

JANTA = ("JANTA PHARMACEUTICALS", "21965", "2026-10-02")


def rs(p):
    if p is None:
        return "-"
    p = int(p)
    return "%sRs %s%s" % ("-" if p < 0 else "", "{:,}".format(abs(p) // 100), (".%02d" % (abs(p) % 100)) if abs(p) % 100 else "")


def main():
    if len(sys.argv) < 5:
        print(__doc__)
        print("PROOF S740: ERROR usage")
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
        import scan_register as SR
        con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=30)
        con.row_factory = sqlite3.Row
        import time
        t0 = time.time()
        m = SR.s740_model(con)
        took = time.time() - t0
        flags = SR._s740_flags(con)
        jb = con.execute("SELECT id FROM purchase_bill WHERE supplier_norm=? AND lower(trim(bill_no))=? AND bill_date=?", JANTA).fetchone()
    except Exception:                                         # noqa: BLE001
        print(traceback.format_exc()[-1500:])
        print("PROOF S740: ERROR the returns could not be read")
        return 1
    print("S740 proof · read only · the returns read in %.2f s" % took)
    print("Reception's question (the paper reads more than Marg):")
    for q in m["questions"]:
        print("  %-30s %-12s %s  %-8s paper %s · Marg %s · more %s" % (q["supplier"][:30], q["bill_no"][:12], q["date"], q.get("stamp") or "-",
                                                                      rs(q["paper_p"]), rs(q["marg_p"]), rs(q["diff_p"])))
    print("Returns:")
    pend = [r for r in m["returns"] if not r["resolved"]]
    for r in m["returns"]:
        what = r.get("item") or ("bill %s" % r["bill_no"])
        print("  %-8s %-30s %-24s %s  %s  %-10s %s" % (r["kind"], r["supplier"][:30], what[:24], r["date"], rs(r["amount_p"]), r.get("stage"),
                                                      ("resolved: " + r["road"] + " " + r["ref"]) if r["resolved"] else (r.get("whose") or "")))
    print("Count shortages for the owner (possibly returned, no paper):")
    for f in flags:
        print("  %s · %s %s · from %s only" % (f["item"], f["qty"], f["unit"], f["supplier"]))
    print("A dealer's return line no return matches:")
    for o in m["adjusted"]:
        print("  %s · scan %s · %s" % (o.get("supplier") or o["vendor"], o["stamp"], rs(o["amount_p"])))
    if jb is None:
        js = "not in Marg"
    elif any(int(q["bill_id"]) == int(jb[0]) for q in m["questions"]):
        js = "on the question list -- the seed applies"
    elif any(r["kind"] == "on_bill" and r.get("bill_id") == int(jb[0]) for r in m["returns"]):
        js = "already a return"
    else:
        js = "not a question now -- the seed writes nothing"
    n_do = sum(1 for r in pend if r.get("stage") in ("do_revised", "do_full", "do_return", "do_own", "do_amount", "do_goods"))
    print("PROOF S740: %d question(s) · %d return(s) pending (%d for Amir to enter) · %d resolved · %d count line(s) · Janta 21965: %s"
          % (len(m["questions"]), len(pend), n_do, len(m["returns"]) - len(pend), len(flags), js))
    if took > 5:
        print("PROOF S740: ERROR the returns took %.1f s to read (more than 5 s) -- too slow for the live pages" % took)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
