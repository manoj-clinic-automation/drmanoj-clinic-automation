#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proof_s824.py -- S824_REVISED_BILL_SETASIDE (F-1378): the purchase returns read by one copy of the finance code, on this box's own
databases, READ ONLY (both opened mode=ro; only scan_register.s740_model, which reads).
    python3 -B proof_s824.py read <finance code dir> <shared dir> <finance.db> <assets.db> <out.json>
    python3 -B proof_s824.py compare <old.json> <new.json>
'compare' says PROVEN only when: Janta 21965 of 02-Oct is SETTLED by the new code on the road 'revised' by scan B-0271; every other
return reads exactly as with the old code; and no return is settled by B-0264 (the true double). Its last line:
    PROOF S824: PROVEN | NOT PROVEN <why>
Supplier names, bill numbers, scan stamps and amounts only -- no phone number, no patient detail."""
import json
import os
import sqlite3
import sys
import traceback

JANTA = ("JANTA PHARMACEUTICALS", "21965", "2026-10-02")
REVISED, DOUBLE = "B-0271", "B-0264"


def read(code, shared, db, adb, out):
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
        m = SR.s740_model(con)
        jb = con.execute("SELECT id FROM purchase_bill WHERE supplier_norm=? AND lower(trim(bill_no))=? AND bill_date=?",
                         (PA.supplier_key(JANTA[0]), JANTA[1], JANTA[2])).fetchone()
    except Exception:                                         # noqa: BLE001
        print(traceback.format_exc()[-1500:])
        print("PROOF S824: ERROR the returns could not be read")
        return 1
    rows = {r["key"]: dict(kind=r["kind"], supplier=str(r.get("supplier") or ""), bill_no=str(r.get("bill_no") or ""), bill_id=r.get("bill_id"),
                           stage=r.get("stage"), resolved=bool(r.get("resolved")), road=r.get("road"), ref=r.get("ref"), amount_p=r.get("amount_p"))
            for r in m["returns"]}
    json.dump(dict(janta_bill=int(jb[0]) if jb else None, returns=rows), open(out, "w"), indent=1, sort_keys=True)
    print("read: %d returns (%d settled) by %s" % (len(rows), sum(1 for v in rows.values() if v["resolved"]), code))
    return 0


def compare(old_p, new_p):
    old, new = json.load(open(old_p)), json.load(open(new_p))
    jb = new.get("janta_bill")
    jk = [k for k, v in new["returns"].items() if v["kind"] == "on_bill" and v["bill_id"] == jb]
    why = []
    if jb is None or len(jk) != 1:
        why.append("Janta 21965 is not one return here")
    else:
        o, n = old["returns"].get(jk[0]) or {}, new["returns"][jk[0]]
        print("Janta 21965 (02-Oct): before -- %s%s ; after -- %s%s" % (o.get("stage"), (" by " + str(o.get("ref"))) if o.get("resolved") else "",
                                                                   n["stage"], (" by %s (%s)" % (n["ref"], n["road"])) if n["resolved"] else ""))
        if not (n["resolved"] and n["road"] == "revised" and n["ref"] == REVISED):
            why.append("Janta 21965 is not settled by %s" % REVISED)
    diff = [k for k in set(old["returns"]) | set(new["returns"]) if k not in jk and old["returns"].get(k) != new["returns"].get(k)]
    for k in sorted(diff)[:20]:
        print("  CHANGED: %s  %s -> %s" % (k, old["returns"].get(k), new["returns"].get(k)))
    if diff:
        why.append("%d other return(s) read differently" % len(diff))
    dbl = [k for k, v in new["returns"].items() if v.get("ref") == DOUBLE]
    if dbl:
        why.append("%s settles %d return(s)" % (DOUBLE, len(dbl)))
    print("other returns compared: %d, all the same: %s" % (len(set(old["returns"]) - set(jk)), "yes" if not diff else "NO"))
    print("PROOF S824: " + ("PROVEN" if not why else "NOT PROVEN -- " + "; ".join(why)))
    return 0 if not why else 1


if __name__ == "__main__":
    if len(sys.argv) >= 7 and sys.argv[1] == "read":
        sys.exit(read(*(os.path.abspath(x) for x in sys.argv[2:7])))
    if len(sys.argv) >= 4 and sys.argv[1] == "compare":
        sys.exit(compare(sys.argv[2], sys.argv[3]))
    print(__doc__)
    sys.exit(2)
