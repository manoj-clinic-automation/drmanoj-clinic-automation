#!/usr/bin/env python3
# =============================================================================
#  MEASURE_rung4.py · S213 · READ-ONLY measurement: old rung 4 vs reworked
#
#  The S212 rung 4 compared SUM(rate-per-pack) against a bill's MONEY and
#  still recovered 18 bills. That number is load-bearing, so the rework is
#  not installed on faith -- this script runs BOTH rules over every return
#  bill on the live database and prints what actually changes.
#
#  Prints NO patient data. Bill numbers, dates and amounts only.
#
#  Run (VPS):
#    python3 /root/deploy/repo/deploy_kits/S213_RUNG4/MEASURE_rung4.py /root/finance/finance.db
# =============================================================================
import collections
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KITS = os.path.dirname(HERE)
for p in (HERE, "/root/finance", os.path.join(KITS, "S212_SUMP")):
    if os.path.isdir(p):
        sys.path.append(p)
from finance_money import bill_gross_p          # the one rate->money authority

TOL = 100                                       # Rs 1, both rules

def main(db):
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    con.row_factory = sqlite3.Row

    # the rung-4 population: return BILLS whose lines rungs 1-3 cannot find
    bills = con.execute(
        "SELECT e.business_date d, s.source_ref bill, s.amount_p "
        "FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id "
        "WHERE e.unit='medical' AND s.service LIKE '%!_return' ESCAPE '!' "
        "ORDER BY e.business_date, s.source_ref").fetchall()

    import re
    def rung123(bill_no):
        b = str(bill_no or "").strip()
        if not b:
            return False
        if con.execute("SELECT 1 FROM sale_line_item WHERE bill_no=? LIMIT 1",
                       (b,)).fetchone():
            return True
        digits = re.sub(r"\D", "", b)
        if len(digits) >= 3:
            r = con.execute(
                "SELECT DISTINCT bill_no FROM sale_line_item WHERE is_return=1 "
                "AND REPLACE(REPLACE(bill_no,'CN',''),'-','') LIKE ?",
                ("%" + digits,)).fetchall()
            if len(r) == 1:
                return True
        return False

    def day_candidates(d):
        by = collections.defaultdict(list)
        for c in con.execute(
                "SELECT bill_no, qty_raw, pack, amount_p FROM sale_line_item "
                "WHERE is_return=1 AND business_date=?", (d,)):
            by[c["bill_no"]].append(dict(qty_raw=c["qty_raw"], pack=c["pack"],
                                         amount_p=c["amount_p"]))
        return by

    def old_fit(d, amount_p):
        cand = con.execute(
            "SELECT bill_no, SUM(COALESCE(amount_p,0)) t FROM sale_line_item "
            "WHERE is_return=1 AND business_date=? GROUP BY bill_no", (d,)).fetchall()
        f = [c["bill_no"] for c in cand if abs((c["t"] or 0) - amount_p) <= TOL]
        return f[0] if len(f) == 1 else None

    def new_fit(d, amount_p):
        f = []
        for bno, lns in day_candidates(d).items():
            gross, bad = bill_gross_p(lns)
            if bad:
                continue
            if abs(gross - abs(amount_p)) <= TOL:
                f.append(bno)
        return f[0] if len(f) == 1 else None

    pop = [b for b in bills if not rung123(b["bill"])]
    print("return bills total: %d · reaching rung 4 (rungs 1-3 blank): %d"
          % (len(bills), len(pop)))

    same = gained = lost = moved = 0
    detail = []
    for b in pop:
        o = old_fit(b["d"], b["amount_p"])
        n = new_fit(b["d"], b["amount_p"])
        if o == n:
            same += 1 if o else 0
            continue
        if o and not n:
            lost += 1;  detail.append(("LOST", b, o, n))
        elif n and not o:
            gained += 1; detail.append(("GAINED", b, o, n))
        else:
            moved += 1;  detail.append(("MOVED", b, o, n))

    print("recovered by BOTH rules identically: %d" % same)
    print("recovered ONLY by the old (rates) rule -- the suspect matches: %d" % lost)
    print("recovered ONLY by the reworked (money) rule: %d" % gained)
    print("matched to a DIFFERENT bill by each rule: %d" % moved)
    for kind, b, o, n in detail:
        print("  %-6s %s  %-12s Rs %10.2f   old->%s  new->%s"
              % (kind, b["d"], b["bill"], abs(b["amount_p"] or 0) / 100.0,
                 o or "-", n or "-"))
    print("done. READ-ONLY -- nothing was written.")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/root/finance/finance.db")
