#!/usr/bin/env python3
"""json_keys.py -- read-only. What is inside that description blob?

Prints the JSON KEY NAMES (Marg column names -- not patient data) and, for each,
a MASKED shape of its value: digits become #, letters A. No name, no number, no
free text is printed. Writes nothing.

S211: description on WALK-IN rows turned out to hold a JSON dump of the raw Marg
row, not the counter's typed text. My matcher was parsing it as prose and finding
digit-runs inside it. This finds the field that actually holds the identity.
"""
import collections, json, os, re, sqlite3, sys
sys.path.insert(0, "/root/finance")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
import finance_daily_gaps as G

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row

def shape(v):
    s = re.sub(r"\d", "#", str(v if v is not None else ""))
    s = re.sub(r"[A-Za-z]", "A", s)
    s = re.sub(r"A{2,}", "A+", s); s = re.sub(r"#{2,}", "#+", s)
    return s[:30]

rows = con.execute(
    "SELECT s.description FROM sale_item s JOIN day_entry d ON d.id=s.day_entry_id "
    "WHERE d.unit='medical' AND d.business_date >= ? "
    "AND COALESCE(s.description,'') <> '' LIMIT 400", (G.IDENTITY_ERA_START,)).fetchall()
print("rows with a description: %d (sampled)\n" % len(rows))

keys = collections.Counter(); shapes = collections.defaultdict(collections.Counter)
notjson = 0
for r in rows:
    try:
        d = json.loads(r["description"])
    except Exception:
        notjson += 1
        continue
    if not isinstance(d, dict):
        notjson += 1
        continue
    for k, v in d.items():
        keys[k] += 1
        shapes[k][shape(v)] += 1
print("rows that would NOT parse as a JSON object: %d" % notjson)
print("\n%-28s %6s   %s" % ("key", "seen", "most common value shapes"))
for k, n in keys.most_common(40):
    top = ", ".join("%s x%d" % (s or "(empty)", c)
                    for s, c in shapes[k].most_common(3))
    print("%-28s %6d   %s" % (k[:28], n, top[:70]))

print("\nWHICH KEY LOOKS LIKE THE COUNTER'S IDENTITY TEXT?")
print("  -- one whose shape mixes #+ and A+ , e.g. '#+ A+ #+' (phone name id)")
print("  -- NOT a pure '#+' (an amount) or a pure date '#+-#+-#+'")
con.close()
