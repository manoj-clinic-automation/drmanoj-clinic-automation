#!/usr/bin/env python3
"""tally_recent.py -- read-only. What is really in the day, and does 100% mean anything?

Counts only. No name, no number, no bill text. Writes nothing.

S211: the first version reported 126 bills at 100% matched, which is too clean to
trust. Two things were wrong with the question it asked:
  * SALES RETURNS were counted as bills. A return is not a sale.
  * "matched" only ever meant "linked to a patient_ref row that has a uid". If
    resolve_patient links every bill to something, and every clinic id in the
    period happens to be in the master, nothing can ever fail -- a measure that
    cannot fail is not a measure.
So this splits sales from returns, and shows WHERE the gap could hide: bills on
WALK-IN, bills linked to a stub, and whether sale_item holds one row per bill.
"""
import collections, os, sqlite3, sys
sys.path.insert(0, "/root/finance")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
import finance_daily_gaps as G

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 7
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
days = [r[0] for r in con.execute(
    "SELECT business_date FROM day_entry WHERE unit='medical' "
    "ORDER BY business_date DESC LIMIT ?", (N,)).fetchall()]
days = sorted(days)
q = ",".join("?" * len(days))

rows = con.execute(
    "SELECT s.*, d.business_date bd FROM sale_item s "
    "JOIN day_entry d ON d.id=s.day_entry_id "
    "WHERE d.unit='medical' AND d.business_date IN (%s)" % q, days).fetchall()

print("=== WHAT IS ACTUALLY IN THESE %d DAYS ===" % len(days))
print("sale_item rows                    : %d" % len(rows))
print("by service                        :",
      dict(collections.Counter(r["service"] for r in rows)))
print("distinct bill numbers (source_ref): %d" % len({r["source_ref"] for r in rows}))
print("   -> if that is far below the row count, a bill spans several rows")
print()

sales = [r for r in rows if not (r["service"] or "").endswith("_return")]
rets = [r for r in rows if (r["service"] or "").endswith("_return")]
print("SALES   %d      RETURNS %d" % (len(sales), len(rets)))
print()

print("=== WHERE COULD A GAP HIDE? ===")
walkin = con.execute("SELECT id FROM patient_ref WHERE UPPER(clinic_id)='WALK-IN'").fetchone()
wid = walkin["id"] if walkin else None
n_walk = sum(1 for r in rows if wid and r["patient_ref_id"] == wid)
n_nolink = sum(1 for r in rows if not r["patient_ref_id"])
stub = 0
for r in rows:
    if r["patient_ref_id"]:
        p = con.execute("SELECT patient_uid FROM patient_ref WHERE id=?",
                        (r["patient_ref_id"],)).fetchone()
        if p is not None and not (p["patient_uid"] or ""):
            stub += 1
ERA = G.IDENTITY_ERA_START
def era(r): return "before" if r["bd"] < ERA else "after "
cnt = collections.Counter()
for r in rows:
    kind = "return" if (r["service"] or "").endswith("_return") else "sale  "
    if not r["patient_ref_id"]: cnt[(era(r), kind, "no link")] += 1
    elif wid and r["patient_ref_id"] == wid: cnt[(era(r), kind, "WALK-IN")] += 1
    else:
        p = con.execute("SELECT patient_uid FROM patient_ref WHERE id=?",
                        (r["patient_ref_id"],)).fetchone()
        if p is not None and not (p["patient_uid"] or ""):
            cnt[(era(r), kind, "stub, no uid")] += 1
        else:
            cnt[(era(r), kind, "master patient")] += 1
print("%-7s %-7s %-16s %6s" % ("era", "kind", "linked to", "count"))
for k in sorted(cnt):
    print("%-7s %-7s %-16s %6d" % (k[0], k[1], k[2], cnt[k]))
print()
print("   the counter gap is the AFTER rows that are not a master patient.")
print("   BEFORE %s the three identifiers were not being captured, so those" % ERA)
print("   rows say nothing about the counter and are not counted anywhere.")
print()

print("=== THE DAY, SALES ONLY ===")
print("%-12s %6s %8s %10s %10s   %12s" %
      ("date", "sales", "matched", "ambiguous", "unmatched", "sales total"))
tot = collections.Counter()
tot["pre_sales"] = 0; tot["post_sales"] = 0
for d in days:
    r = G.day_report(con, d, "medical", exclude_returns=True)
    t = r["totals"]
    day_sales = [x for x in sales if x["bd"] == d]
    amt = sum(x["amount_p"] or 0 for x in day_sales)
    tot["sales"] += len(day_sales); tot["amt"] += amt
    for k in ("matched", "ambiguous", "unmatched"): tot[k] += t[k]
    if r.get("before_identity_era"):
        print("%-12s %6d %8s %10s %10s   %12.2f   (before 18-Jun: not counted)" %
              (d, len(day_sales), "-", "-", "-", amt / 100.0))
        tot["pre_sales"] += len(day_sales)
    else:
        print("%-12s %6d %8d %10d %10d   %12.2f" %
              (d, len(day_sales), t["matched"], t["ambiguous"], t["unmatched"],
               amt / 100.0))
        tot["post_sales"] += len(day_sales)
print("-" * 70)
print("%-12s %6d %8d %10d %10d   %12.2f" %
      ("TOTAL", tot["sales"], tot["matched"], tot["ambiguous"], tot["unmatched"],
       tot["amt"] / 100.0))
print("   of which %d sales are before 18-Jun and NOT counted; %d are after."
      % (tot["pre_sales"], tot["post_sales"]))
chk = tot["matched"] + tot["ambiguous"] + tot["unmatched"]
print("   check: matched+ambiguous+unmatched = %d, counted sales = %d %s"
      % (chk, tot["post_sales"], "OK" if chk == tot["post_sales"] else "<-- MISMATCH"))
print()
print("=== PAYMENT, LATEST DAY -- units sanity-checked ===")
p = G.payment_gaps(con, days[-1], "medical")
for m, v in sorted(p["modes"].items()):
    print("   mode %-8s %8.2f  over %d row(s)" % (m, v["paise"] / 100.0, v["bills"]))
print("   bank settled      %s" %
      ("%8.2f" % (p["bank_settled_p"] / 100.0) if p["bank_settled_p"] is not None else "none"))
print("   difference        %s" %
      ("%8.2f" % (p["difference_p"] / 100.0) if p["difference_p"] is not None else "n/a"))
print("   ->", p["note"])
con.close()
