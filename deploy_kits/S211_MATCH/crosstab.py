#!/usr/bin/env python3
"""crosstab.py -- read-only. Cross every verdict against what the bill is linked to.

S211: the tally reported 1,321 matched while only 1,167 post-era sales are linked
to a master patient, and 361 are linked to WALK-IN. Those cannot both be true.
This crosses the two directly, so the disagreeing cell names itself instead of
being reasoned about. Counts only; writes nothing.
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

# how many day_entry rows per date? a duplicate would double-count silently
dups = con.execute(
    "SELECT business_date, COUNT(*) c FROM day_entry WHERE unit='medical' "
    "GROUP BY 1 HAVING c > 1").fetchall()
print("dates with MORE THAN ONE day_entry row: %d %s" %
      (len(dups), [d["business_date"] for d in dups][:5]))

# every patient_ref row that looks like a walk-in, however it is spelled
walk = con.execute("SELECT id, clinic_id, patient_uid FROM patient_ref "
                   "WHERE clinic_id LIKE '%WALK%' OR clinic_id LIKE '%walk%'").fetchall()
print("\npatient_ref rows that look like WALK-IN: %d" % len(walk))
for w in walk:
    print("   id=%s clinic_id=%r has_uid=%s" % (w["id"], w["clinic_id"], bool(w["patient_uid"])))

def linked_to(pid):
    if not pid: return "no link"
    p = con.execute("SELECT clinic_id, patient_uid FROM patient_ref WHERE id=?",
                    (pid,)).fetchone()
    if p is None: return "dangling id"
    if (p["clinic_id"] or "").upper().startswith("WALK"): return "WALK-IN"
    return "master patient" if (p["patient_uid"] or "") else "stub, no uid"

ct = collections.Counter()
for d in days:
    if d < G.IDENTITY_ERA_START:
        continue
    gaps, tally = G.identity_gaps(con, d, "medical", None, exclude_returns=True)
    gapmap = {g["sale_item_id"]: g["verdict"] for g in gaps}
    rows = con.execute(
        "SELECT s.id, s.patient_ref_id, s.service FROM sale_item s "
        "JOIN day_entry dd ON dd.id=s.day_entry_id "
        "WHERE dd.unit='medical' AND dd.business_date=?", (d,)).fetchall()
    for r in rows:
        if (r["service"] or "").endswith("_return"):
            continue
        v = gapmap.get(r["id"], "matched")
        ct[(v, linked_to(r["patient_ref_id"]))] += 1

print("\n%-18s %-16s %6s" % ("verdict", "linked to", "count"))
for k in sorted(ct):
    flag = ""
    if k[0] == "matched" and k[1] != "master patient":
        flag = "   <-- CANNOT BE RIGHT"
    print("%-18s %-16s %6d%s" % (k[0], k[1], ct[k], flag))
print("\ntotal post-era sales counted: %d" % sum(ct.values()))
con.close()
