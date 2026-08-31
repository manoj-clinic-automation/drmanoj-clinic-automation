#!/usr/bin/env python3
"""diagnose_identity_text.py -- where does the counter's identity text actually live?

READ-ONLY. Prints COUNTS and MASKED SHAPES only: every digit becomes # and every
letter becomes A, so the format is visible and the content never is. No name, no
number, no bill text is printed.
"""
import os, re, sqlite3, sys

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 7
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
days = [r[0] for r in con.execute(
    "SELECT business_date FROM day_entry WHERE unit='medical' "
    "ORDER BY business_date DESC LIMIT ?", (N,)).fetchall()]
q = ",".join("?" * len(days))

rows = con.execute(
    "SELECT s.* FROM sale_item s JOIN day_entry d ON d.id=s.day_entry_id "
    "WHERE d.unit='medical' AND d.business_date IN (%s)" % q, days).fetchall()
print("sale_item rows over the last %d filed days: %d\n" % (len(days), len(rows)))

cols = rows[0].keys() if rows else []
print("columns present:", ", ".join(cols), "\n")

def shape(v):
    s = re.sub(r"\d", "#", str(v or ""))
    s = re.sub(r"[A-Za-z]", "A", s)
    s = re.sub(r"A{2,}", "A+", s); s = re.sub(r"#{2,}", "#+", s)
    return s[:40]

for col in ("description", "source_ref", "service"):
    if col not in cols: continue
    vals = [r[col] for r in rows]
    nn = sum(1 for v in vals if (v or "").strip())
    print("%-12s non-empty %d/%d" % (col, nn, len(vals)))
    import collections
    for sh, k in collections.Counter(shape(v) for v in vals).most_common(6):
        print("     %5d  %s" % (k, sh if sh else "(empty)"))
    print()

print("is identity ALREADY resolved by the existing code?")
print("   patient_ref_id set on %d of %d rows"
      % (sum(1 for r in rows if r["patient_ref_id"]), len(rows)))
if "confidence" in cols:
    import collections
    print("   confidence values:",
          dict(collections.Counter(r["confidence"] for r in rows).most_common(6)))

print("\nwhere else could the typed text be?")
for t, c in (("sale_item_review", "raw_text"), ("sale_line_item", "item_name")):
    try:
        n = con.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
        print("   %-18s rows: %d" % (t, n))
        r = con.execute("SELECT %s v FROM %s LIMIT 3" % (c, t)).fetchall()
        for x in r: print("        shape: %s" % shape(x["v"]))
    except sqlite3.Error as e:
        print("   %-18s not readable: %s" % (t, str(e)[:50]))
con.close()
