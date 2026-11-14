#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proof_s825.py -- S825_ARRIVALS_BY_THE_BILL (F-1220, D883): the scan-tied open order lines as one copy of the finance code reads them, on this
box's own databases, READ ONLY (finance.db opened mode=ro; assets.db read-only by purchase_app._assets_con; the spine read-only).
    python3 -B proof_s825.py read <finance code dir> <shared dir> <finance.db> <assets.db> <out.json>
    python3 -B proof_s825.py compare <old.json> <new.json>
'compare' prints every scan-tied open line -- the item, the dealer, the ordered packs, whether the old and the new file count it as arrived,
the tracker's own note (on bill B-xxxx / not seen) -- and says PROVEN only when the new file reached the scan store, every line it no longer
counts is one the bill does not carry AND is on order on the count basis, it counts no line the old file did not, and no other line moved.
Its last line:  PROOF S825: PROVEN (N lines: K carried, D not on their bill and on the way, U not judged) | NOT PROVEN <why>
Item and dealer names and pack counts only -- no phone number, no patient detail."""
import datetime as dt
import json
import os
import sqlite3
import sys
import time
import traceback


def read(code, shared, db, adb, out):
    sys.path.insert(0, shared)
    sys.path.insert(0, code)
    os.environ["SHARED_LIB_DIR"] = shared
    os.environ["ASSETS_DB"] = adb
    import warnings
    warnings.simplefilter("ignore")
    try:
        import purchase_app as PA
        PA._assets_db = adb
        import stock_figure as SF
        import order_rules as ORR
        con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=30)
        lines = SF.scan_lines(con, None, None, "", SF.Ctx(con, None, read_only=True))
        judged = SF.s825_bill_judged(con, SF.Ctx(con, None, read_only=True)) if hasattr(SF, "s825_bill_judged") else "old"
        con.row_factory = sqlite3.Row
        t0 = time.time()
        oc = ORR._on_order_units(con, dt.date.today(), "count")   # S459: timed on the box (the review: a fresh tracker context per call)
        t_ms = int((time.time() - t0) * 1000)
        con.row_factory = None
        pa = PA
        meta = {}
        for r in con.execute("SELECT l.id, l.item, l.packs, o.vendor FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                             "WHERE l.order_id IN (SELECT order_id FROM order_scan_tie WHERE arrived=1) AND l.supplied IS NULL AND l.billed_qty IS NULL "
                             "AND COALESCE(l.missing,0)=0"):
            meta[str(int(r[0]))] = [r[1], int(r[2] or 0), r[3], pa.norm(r[1]) in oc]
    except Exception:                                         # noqa: BLE001
        print(traceback.format_exc()[-1500:])
        print("PROOF S825: ERROR the lines could not be read")
        return 1
    d = dict(reached=(judged is not None and judged != "old"), old=(judged == "old"),
             judged={} if judged in (None, "old") else {str(k): bool(v) for k, v in judged.items()},
             lines={str(int(x["line_id"])): float(x["units"]) for x in lines}, meta=meta, t_ms=t_ms)
    json.dump(d, open(out, "w"), indent=1, sort_keys=True)
    print("read: %d scan-tied open line(s) count as arrived by %s%s" % (len(d["lines"]), code,
                                                                          "" if d["old"] else "; %d judged by their bill" % len(d["judged"])) + "; the on-order read %d ms" % t_ms)
    return 0


def compare(old_p, new_p):
    old, new = json.load(open(old_p)), json.load(open(new_p))
    meta, j = new["meta"], new["judged"]
    ids = sorted(set(old["lines"]) | set(new["lines"]) | set(meta), key=lambda k: (str((meta.get(k) or ["", 0, ""])[2]), str((meta.get(k) or [""])[0])))
    print("  %-34s %-24s %4s %-5s %-5s %s" % ("item", "dealer", "ord", "old", "new", "the bill"))
    carried = gone = unj = 0
    bad = []
    for k in ids:
        it, pk, v, onord = (meta.get(k) or ["?", 0, "?", False])[:4]
        o, n = k in old["lines"], k in new["lines"]
        jj = j.get(k)
        word = "carries it" if jj is True else ("NOT on it" if jj is False else "not judged (no read scan)")
        if jj is True:
            carried += 1
        elif jj is False:
            gone += 1
        else:
            unj += 1
        if n and not o:
            bad.append("%s counted now, not before" % it)
        if o and not n and not (jj is False and onord):
            bad.append("%s left out but %s" % (it, "not judged off its bill" if jj is not False else "not on order"))
        if o and n and old["lines"][k] != new["lines"][k]:
            bad.append("%s units moved" % it)
        if jj is False and n:
            bad.append("%s judged off its bill yet counted" % it)
        print("  %-34s %-24s %4s %-5s %-5s %s%s" % (str(it)[:34], str(v)[:24], pk, "yes" if o else "-", "yes" if n else "-", word,
                                                  " · on order" if (jj is False and onord) else ""))
    why = []
    if not new.get("reached"):
        why.append("the scan store was not reached -- the new file kept the old reading")
    why += bad[:6]
    print("PROOF S825: " + ("PROVEN (%d lines: %d carried, %d not on their bill and on the way, %d not judged; the on-order read %s ms, was %s ms)" % (len(ids), carried, gone, unj, new.get("t_ms", "?"), old.get("t_ms", "?"))
                           if not why else "NOT PROVEN -- " + "; ".join(why)))
    return 0 if not why else 1


if __name__ == "__main__":
    if len(sys.argv) >= 7 and sys.argv[1] == "read":
        sys.exit(read(*(os.path.abspath(x) for x in sys.argv[2:7])))
    if len(sys.argv) >= 4 and sys.argv[1] == "compare":
        sys.exit(compare(sys.argv[2], sys.argv[3]))
    print(__doc__)
    sys.exit(2)
