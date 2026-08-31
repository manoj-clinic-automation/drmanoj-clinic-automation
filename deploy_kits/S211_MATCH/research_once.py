#!/usr/bin/env python3
"""research_once.py -- read-only. Everything still open, answered in ONE run.

The assistant cannot reach this box (egress is blocked at the proxy), so this
replaces a series of one-line requests. It writes nothing and prints counts,
dates and rupees only -- never a name, a number, or a bill's text.
"""
import collections, os, sqlite3, sys
sys.path.insert(0, "/root/finance")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
import finance_daily_gaps as G

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 90
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
days = sorted(r[0] for r in con.execute(
    "SELECT business_date FROM day_entry WHERE unit='medical' "
    "ORDER BY business_date DESC LIMIT ?", (N,)).fetchall())
post = [d for d in days if d >= G.IDENTITY_ERA_START]

def linked(pid):
    if not pid: return "no link"
    p = con.execute("SELECT clinic_id, patient_uid FROM patient_ref WHERE id=?",
                    (pid,)).fetchone()
    if p is None: return "dangling"
    if (p["clinic_id"] or "").upper().startswith("WALK"): return "WALK-IN"
    return "master patient" if (p["patient_uid"] or "") else "stub, no uid"

print("=" * 74)
print("Q1  WHICH PATH DECIDED EACH VERDICT, and does the text path explain the 154?")
print("=" * 74)
ct = collections.Counter(); withtext = 0
for d in post:
    rows = con.execute(
        "SELECT s.id, s.description, s.patient_ref_id, s.service FROM sale_item s "
        "JOIN day_entry dd ON dd.id=s.day_entry_id "
        "WHERE dd.unit='medical' AND dd.business_date=?", (d,)).fetchall()
    gaps, _ = G.identity_gaps(con, d, "medical", None, exclude_returns=True)
    gm = {g["sale_item_id"]: g["verdict"] for g in gaps}
    for r in rows:
        if (r["service"] or "").endswith("_return"): continue
        path = "text" if (r["description"] or "").strip() else "ingest link"
        if path == "text": withtext += 1
        ct[(path, gm.get(r["id"], "matched"), linked(r["patient_ref_id"]))] += 1
print("post-era sales carrying description text: %d\n" % withtext)
print("%-12s %-18s %-16s %6s" % ("path", "verdict", "linked to", "count"))
for k in sorted(ct):
    print("%-12s %-18s %-16s %6d" % (k[0], k[1], k[2], ct[k]))
print("\n  If every 'matched / WALK-IN' row came through the TEXT path, the join is")
print("  RECOVERING identities the original ingest could not -- a gain, not a hole.")
print("  If any came through the INGEST LINK path, that is a real bug in my code.")

print("\n" + "=" * 74)
print("Q2  DID SOMETHING CHANGE MID-AUGUST, or did the counter genuinely improve?")
print("=" * 74)
print("%-12s %6s %8s %9s %9s   %s" %
      ("date", "sales", "withtext", "WALK-IN", "unmatched", "note"))
for d in post[-25:]:
    rows = con.execute(
        "SELECT s.description, s.patient_ref_id, s.service FROM sale_item s "
        "JOIN day_entry dd ON dd.id=s.day_entry_id "
        "WHERE dd.unit='medical' AND dd.business_date=?", (d,)).fetchall()
    sales = [r for r in rows if not (r["service"] or "").endswith("_return")]
    wt = sum(1 for r in sales if (r["description"] or "").strip())
    wi = sum(1 for r in sales if linked(r["patient_ref_id"]) == "WALK-IN")
    _, t = G.identity_gaps(con, d, "medical", None, exclude_returns=True)
    print("%-12s %6d %8d %9d %9d" % (d, len(sales), wt, wi, t["unmatched"]))
print("\n  A drop in WALK-IN means the counter improved.")
print("  A drop in 'withtext' at the same time means the PIPELINE changed instead.")

print("\n" + "=" * 74)
print("Q3  THE PAYMENT HALF, over the whole period -- is -304 typical or singular?")
print("=" * 74)
print("%-12s %10s %10s %10s" % ("date", "digital", "bank", "difference"))
diffs = []
for d in post:
    p = G.payment_gaps(con, d, "medical")
    if p["bank_settled_p"] is None: continue
    diffs.append((d, p["entered_digital_p"], p["bank_settled_p"], p["difference_p"]))
for d, e, b, x in diffs[-12:]:
    print("%-12s %10.2f %10.2f %10.2f" % (d, e/100.0, b/100.0, x/100.0))
if diffs:
    agree = sum(1 for _, _, _, x in diffs if x == 0)
    tot = sum(abs(x) for _, _, _, x in diffs)
    print("\n  days with a bank statement: %d | days that agree exactly: %d"
          % (len(diffs), agree))
    print("  total absolute difference across them: %.2f" % (tot/100.0))
else:
    print("  no bank statements stored for this unit in the period.")

print("\n" + "=" * 74)
print("Q4  THE SANCTIONED PHARMACY DISCOUNTS -- are they being applied?")
print("=" * 74)
rows = con.execute(
    "SELECT s.gross_p, s.disc_p, p.admin_pd_pct FROM sale_item s "
    "JOIN day_entry dd ON dd.id=s.day_entry_id "
    "LEFT JOIN patient_ref p ON p.id=s.patient_ref_id "
    "WHERE dd.unit='medical' AND dd.business_date >= ? "
    "AND s.service NOT LIKE '%_return'", (G.IDENTITY_ERA_START,)).fetchall()
have_pd = [r for r in rows if r["admin_pd_pct"]]
print("post-era sales: %d | to a patient holding a sanctioned discount: %d"
      % (len(rows), len(have_pd)))
if have_pd:
    ok = under = over = nodisc = 0
    for r in have_pd:
        g = r["gross_p"] or 0; dsc = r["disc_p"] or 0
        if not g: continue
        want = round(g * r["admin_pd_pct"] / 100.0)
        if dsc == 0: nodisc += 1
        elif abs(dsc - want) <= max(100, want * 0.02): ok += 1
        elif dsc < want: under += 1
        else: over += 1
    print("   discount matches the sanction : %d" % ok)
    print("   NO discount applied at all    : %d" % nodisc)
    print("   less than sanctioned          : %d" % under)
    print("   more than sanctioned          : %d" % over)
print("\n   gross_p populated on %d of %d rows"
      % (sum(1 for r in rows if r["gross_p"]), len(rows)))
print("   disc_p  populated on %d of %d rows"
      % (sum(1 for r in rows if r["disc_p"]), len(rows)))
con.close()
