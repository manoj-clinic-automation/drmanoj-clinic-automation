#!/usr/bin/env python3
"""returns_probe.py -- read-only. What does a RETURN actually look like in the data?

Before building the returns audit, measure what is there: do returns carry item
lines at all, do the items reappear on that patient's earlier purchases, and can
a rate be computed from qty_raw. Counts and MASKED shapes only -- no item name,
no patient, no number. Writes nothing.
"""
import collections, os, re, sqlite3, sys
sys.path.insert(0, "/root/finance")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
import finance_daily_gaps as G

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row

def shape(v):
    s = re.sub(r"\d", "#", str(v if v is not None else ""))
    s = re.sub(r"[A-Za-z]", "A", s)
    s = re.sub(r"A{2,}", "A+", s); s = re.sub(r"#{2,}", "#+", s)
    return s[:22]

print("=" * 72)
print("1  DOES sale_line_item HOLD RETURNS AT ALL?")
print("=" * 72)
for r in con.execute("SELECT is_return, COUNT(*) n, COUNT(DISTINCT bill_no) b "
                     "FROM sale_line_item GROUP BY 1"):
    print("   is_return=%s : %d lines across %d bills" % (r["is_return"], r["n"], r["b"]))

print("\n" + "=" * 72)
print("2  DO THE RETURN BILLS IN sale_item HAVE LINES IN sale_line_item?")
print("=" * 72)
rets = con.execute(
    "SELECT s.source_ref bill, e.business_date d, s.patient_ref_id, s.amount_p, "
    "       s.gross_p, s.disc_p FROM sale_item s "
    "JOIN day_entry e ON e.id=s.day_entry_id "
    "WHERE e.unit='medical' AND s.service LIKE '%!_return' ESCAPE '!'").fetchall()
print("   return bills in sale_item: %d" % len(rets))
withlines = 0
for r in rets:
    n = con.execute("SELECT COUNT(*) c FROM sale_line_item WHERE bill_no=?",
                    (r["bill"],)).fetchone()["c"]
    if n: withlines += 1
print("   of those, with item lines  : %d" % withlines)
print("   -> if this is 0, the audit cannot be built from sale_line_item and")
print("      the item detail must come from the Marg export instead.")

print("\n" + "=" * 72)
print("3  CAN A RATE BE COMPUTED?  qty_raw shapes")
print("=" * 72)
for r in con.execute("SELECT qty_raw, COUNT(*) n FROM sale_line_item "
                     "GROUP BY qty_raw ORDER BY n DESC LIMIT 8"):
    print("   %6d  %s" % (r["n"], shape(r["qty_raw"])))
print("   amount_p present on %d of %d lines" %
      (con.execute("SELECT COUNT(*) c FROM sale_line_item WHERE amount_p IS NOT NULL"
                   ).fetchone()["c"],
       con.execute("SELECT COUNT(*) c FROM sale_line_item").fetchone()["c"]))

print("\n" + "=" * 72)
print("4  DOES A RETURNED ITEM APPEAR ON THAT PATIENT'S EARLIER PURCHASE?")
print("=" * 72)
found = missing = nopat = 0
checked = 0
for r in rets:
    if not r["patient_ref_id"]:
        nopat += 1
        continue
    lines = con.execute("SELECT item_key FROM sale_line_item WHERE bill_no=?",
                        (r["bill"],)).fetchall()
    for ln in lines:
        checked += 1
        hit = con.execute(
            "SELECT 1 FROM sale_line_item l "
            "JOIN sale_item s2 ON s2.source_ref = l.bill_no "
            "WHERE l.item_key=? AND l.is_return=0 AND s2.patient_ref_id=? "
            "AND l.business_date <= ? LIMIT 1",
            (ln["item_key"], r["patient_ref_id"], r["d"])).fetchone()
        if hit: found += 1
        else: missing += 1
print("   return bills with no patient link : %d" % nopat)
print("   returned item lines checked       : %d" % checked)
print("      found on an earlier purchase   : %d" % found)
print("      NOT found                      : %d" % missing)
print("   -> 'not found' is the S180 signal: a return of something this patient")
print("      never bought. It is what makes a fictitious return hard.")
con.close()
