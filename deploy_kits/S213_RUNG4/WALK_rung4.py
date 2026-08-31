#!/usr/bin/env python3
# =============================================================================
#  WALK_rung4.py · S213 · the live-shape walk for the rung-4 rework
#
#  Proves, on a real database built from the real schema:
#   1  THE DEFECT, REPRODUCED: the old rule matches a bill because its RATES
#      happen to sum to the money -- the reworked rule refuses it
#   2  the reworked rule recovers a bill the old one missed (rates != money,
#      but the VALUED lines == the bill)
#   3  two candidates that both fit -> neither rule guesses
#   4  a candidate with an unreadable line never identifies a bill
#   5  v2 differs from the installed S212 module ONLY in the docstring and
#      the rung-4 block -- everything else byte-identical
#   6  regression: returns_for_day still reconciles to the paisa
#
#  Run:  python -B WALK_rung4.py     (from inside the kit folder)
# =============================================================================
import difflib, os, sqlite3, sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
KITS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.append(os.path.join(KITS, "S212_SUMP"))   # finance_money, when run in-repo

CHECKS = []
def check(name, cond):
    CHECKS.append((name, bool(cond)))
    print("  [%s] %s" % ("ok " if cond else "FAIL", name))

import finance_returns_audit as A
from finance_returns_audit import find_return_lines, returns_for_day

def make_con():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    con.execute("CREATE TABLE day_entry (id INTEGER PRIMARY KEY, unit TEXT,"
                " business_date TEXT, status TEXT)")
    sql = os.path.join(os.path.dirname(KITS), "finance", "finance_returns.sql")
    if not os.path.exists(sql):
        sql = os.path.join(HERE, "finance_returns.sql")
    con.executescript(open(sql).read().replace("BEGIN;", "").replace("COMMIT;", ""))
    con.executescript("""
    CREATE TABLE sale_item (id INTEGER PRIMARY KEY, day_entry_id INTEGER, unit TEXT,
      service TEXT, source_ref TEXT, amount_p INTEGER, patient_ref_id INTEGER);
    CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT,
      phone_last4 TEXT);
    INSERT INTO day_entry VALUES (1,'medical','2026-08-20','locked');
    """)
    return con

def line(con, bno, seq, qty, rate_p, pack="1*10", item="ITEM X"):
    con.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date,"
                " bill_no, is_return, seq, item_name, item_key, pack, qty_raw,"
                " amount_p, expiry_ym, batch) VALUES "
                "(1,'medical','2026-08-20',?,1,?,?,?,?,?,?, '2027-01','B1')",
                (bno, seq, item, item.lower().replace(" ", ""), pack, qty, rate_p))

def old_rule(con, d, amount_p):
    cand = con.execute(
        "SELECT bill_no, SUM(COALESCE(amount_p,0)) t FROM sale_line_item "
        "WHERE is_return=1 AND business_date=? GROUP BY bill_no", (d,)).fetchall()
    f = [c["bill_no"] for c in cand if abs((c["t"] or 0) - amount_p) <= 100]
    return f[0] if len(f) == 1 else None

D = "2026-08-20"

print("— 1 · the defect, reproduced: rates coincide, money does not")
con = make_con()
# 2 packs at rate 100.00 each: RATE-SUM = 200.00, MONEY = 2 x 100 = 200? no --
# make it distinct: qty '2:0' rate 100.00 -> rate-sum 100.00, money 200.00.
line(con, "X1", 1, "2:0", 10000)
# the bill claims Rs 100.00 -- the OLD rule (rate-sum 100.00) matches it;
# the money (Rs 200.00) says it is NOT this bill.
check("old rule matches on the rate coincidence", old_rule(con, D, 10000) == "X1")
r, how = find_return_lines(con, "NOBILL", D, 10000)
check("reworked rule refuses it", r == [] and how == "")

print("— 2 · the reworked rule recovers what the old one missed")
r, how = find_return_lines(con, "NOBILL", D, 20000)   # the real money
check("money finds the bill", [x["bill_no"] for x in r] == ["X1"]
      and how == "same day and the money agrees (bill X1)")
check("the old rule could not (rate-sum is 100.00, not 200.00)",
      old_rule(con, D, 20000) is None)

print("— 3 · two fits -> no guess")
line(con, "X2", 1, "2:0", 10000)                       # identical twin
r, how = find_return_lines(con, "NOBILL", D, 20000)
check("ambiguous day refused by the rework", r == [] and how == "")

print("— 4 · an unreadable line disqualifies its bill")
con2 = make_con()
line(con2, "Y1", 1, "1:0", 15000)
line(con2, "Y1", 2, "??", 5000)                        # unreadable quantity
r, how = find_return_lines(con2, "NOBILL", D, 15000)
check("partial totals never identify a bill", r == [] and how == "")

print("— 5 · v2 changes ONLY the docstring and the rung-4 block")
v1p = os.path.join(KITS, "S212_SUMP", "finance_returns_audit.py")
if not os.path.exists(v1p):
    v1p = os.path.join(HERE, "finance_returns_audit_S212.py")
if os.path.exists(v1p):
    v1 = open(v1p, encoding="utf-8").read().splitlines()
    v2 = open(os.path.join(HERE, "finance_returns_audit.py"),
              encoding="utf-8").read().splitlines()
    hunks = [g for g in difflib.SequenceMatcher(None, v1, v2).get_opcodes()
             if g[0] != "equal"]
    lo = next(i for i, l in enumerate(v2) if l.startswith("def find_return_lines"))
    hi = next(i for i, l in enumerate(v2) if l.startswith("def audit_return"))
    check("every changed line is in the docstring head or inside find_return_lines",
          all(g[3] < 60 or (lo < g[3] and g[4] <= hi) for g in hunks))
    changed = "\n".join("\n".join(v2[g[3]:g[4]]) for g in hunks)
    check("both regions are the declared ones",
          "v2 · S213" in changed and "bill_gross_p(lns)" in changed)
else:
    check("S212 baseline present to diff against", False)

print("— 6 · regression: returns_for_day still reconciles to the paisa")
con3 = make_con()
con3.execute("INSERT INTO patient_ref VALUES (1,'842','N','4321')")
con3.execute("INSERT INTO sale_item (day_entry_id,unit,service,source_ref,"
             "amount_p,patient_ref_id) VALUES (1,'medical','pharmacy_return',"
             "'CN9',15000,1)")
line(con3, "CN9", 1, "1:0", 15000)
rows, summ = returns_for_day(con3, D, "medical")
check("one return, Rs 150.00, population audited",
      summ["count"] == 1 and summ["value_p"] == 15000 and summ["audited"] == 1)

fails = [n for n, ok in CHECKS if not ok]
print()
if fails:
    print("WALK FAILED:", ", ".join(fails)); sys.exit(1)
print("ALL WALK CHECKS PASS (%d)" % len(CHECKS))
