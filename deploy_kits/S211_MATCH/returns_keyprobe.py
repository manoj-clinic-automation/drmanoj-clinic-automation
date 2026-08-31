#!/usr/bin/env python3
"""returns_keyprobe.py -- read-only. Why do only 63 of 179 returns join?

The owner confirms all sale data, bill-wise and item-wise, is uploaded to
29-Aug-2026. So 116 return bills without item lines is almost certainly a
JOIN-KEY MISMATCH, not absent data: sale_line_item holds 186 return-flagged
bills, sale_item holds 179, and only 63 share a bill number.

Prints MASKED shapes and counts only -- never an item name or a patient.
Writes nothing.
"""
import collections, os, re, sqlite3, sys
sys.path.insert(0, "/root/finance")

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row

def shape(v):
    s = re.sub(r"\d", "#", str(v if v is not None else ""))
    s = re.sub(r"[A-Za-z]", "A", s)
    s = re.sub(r"A{2,}", "A+", s); s = re.sub(r"#{2,}", "#+", s)
    return s[:20]

si = [r["bill"] for r in con.execute(
    "SELECT DISTINCT s.source_ref bill FROM sale_item s "
    "WHERE s.service LIKE '%!_return' ESCAPE '!' AND s.source_ref IS NOT NULL")]
sli = [r["bill_no"] for r in con.execute(
    "SELECT DISTINCT bill_no FROM sale_line_item WHERE is_return=1")]
sli_all = [r["bill_no"] for r in con.execute(
    "SELECT DISTINCT bill_no FROM sale_line_item")]

print("return bill numbers in sale_item        : %d" % len(si))
print("return bill numbers in sale_line_item   : %d" % len(sli))
print("shared exactly                          : %d" % len(set(si) & set(sli)))
print("in sale_item but NOT in line items      : %d" % len(set(si) - set(sli_all)))
print()
print("SHAPE of the return bill number, each side:")
print("  sale_item      :", dict(collections.Counter(shape(x) for x in si).most_common(5)))
print("  sale_line_item :", dict(collections.Counter(shape(x) for x in sli).most_common(5)))
print()
orphan = sorted(set(si) - set(sli_all))
print("orphans (a return bill with no line under that number): %d" % len(orphan))
if orphan:
    print("  their shapes:", dict(collections.Counter(shape(x) for x in orphan).most_common(5)))
    # do the digits appear inside a DIFFERENT bill number on the line side?
    hit = 0
    for b in orphan[:60]:
        digits = re.sub(r"\D", "", str(b))
        if not digits: continue
        if con.execute("SELECT 1 FROM sale_line_item WHERE bill_no LIKE ? LIMIT 1",
                       ("%" + digits + "%",)).fetchone():
            hit += 1
    print("  of the first %d, how many have their DIGITS inside some line-item "
          "bill number: %d" % (min(60, len(orphan)), hit))
    print("  -> a high number means the same bill under a different prefix,")
    print("     which is a key-normalisation fix, not lost data.")
print()
print("AND THE OTHER DIRECTION -- line-item returns with no sale_item bill:")
rev = sorted(set(sli) - set(si))
print("  %d of them; shapes: %s" % (len(rev),
      dict(collections.Counter(shape(x) for x in rev).most_common(5))))
con.close()
