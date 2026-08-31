#!/usr/bin/env python3
"""validate_visit_rung.py -- read-only. Is the visit fallback evidence, or luck?

THE TEST, and it needs no ground truth:
  Take the bills that resolved on LAST-4 + NAME -- the strong rung, two
  independent signals. For each, hide the last four and ask the VISIT rung
  alone. If the visit rung is evidence, it agrees with the strong rung most of
  the time. If it is luck, it disagrees or fires on the wrong patient.

  A rung that cannot be checked against anything is a rung nobody should trust
  with a patient's name.

Counts only. No name, no number, no bill text. Writes nothing.
"""
import collections, json, os, sqlite3, sys
sys.path.insert(0, "/root/finance")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
import finance_daily_gaps as G
import finance_patient_match as M

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
days = sorted(r[0] for r in con.execute(
    "SELECT business_date FROM day_entry WHERE unit='medical' AND business_date >= ? "
    "ORDER BY business_date", (G.IDENTITY_ERA_START,)).fetchall())

agree = disagree = visit_silent = 0
nvisits = collections.Counter()
strict_would = collections.Counter()
for d in days:
    rows = con.execute(
        "SELECT s.description, s.service FROM sale_item s "
        "JOIN day_entry dd ON dd.id=s.day_entry_id "
        "WHERE dd.unit='medical' AND dd.business_date=? "
        "AND COALESCE(s.description,'') <> ''", (d,)).fetchall()
    for r in rows:
        if (r["service"] or "").endswith("_return"): continue
        ident = M.read_bill_identity_json(r["description"])
        if not ident or not ident.get("last4") or not ident.get("name"): continue
        strong = M.match_bill(con, r["description"], d)
        if strong["verdict"] != "matched_partial" or not strong["patient"]: continue
        # now hide the last four and ask the visit rung alone
        blob = json.loads(r["description"])
        blob["phone_last4"] = ""
        weak = M.match_bill(con, json.dumps(blob), d)
        if weak["verdict"] == "matched_visit" and weak["patient"]:
            if weak["patient"]["clinic_id"] == strong["patient"]["clinic_id"]:
                agree += 1
            else:
                disagree += 1
        else:
            visit_silent += 1
        n = con.execute("SELECT COUNT(*) c FROM patient_visit WHERE visit_date=?",
                        (d,)).fetchone()["c"]
        nvisits[0 if n == 0 else 1 if n < 10 else 2 if n < 25 else 3] += 1

tested = agree + disagree + visit_silent
print("=" * 70)
print("CROSS-VALIDATION OF THE VISIT RUNG")
print("=" * 70)
print("bills resolved by the STRONG rung (last-4 + name) : %d" % tested)
print()
print("  with the last four hidden, the visit rung alone:")
print("     agreed with the strong rung   : %d" % agree)
print("     picked a DIFFERENT patient    : %d   <-- these would be WRONG" % disagree)
print("     said nothing (no unique fit)  : %d" % visit_silent)
if agree + disagree:
    acc = 100.0 * agree / (agree + disagree)
    print("\n  when the visit rung DID fire, it was right %.1f%% of the time"
          " (%d of %d)" % (acc, agree, agree + disagree))
    print("  -> below about 95%% this rung should not name a patient at all;")
    print("     it should offer candidates and let a person choose.")
else:
    print("\n  the visit rung never fired on a checkable bill -- it cannot be")
    print("  validated from this data, which is itself a reason not to trust it.")
print("\n  busyness of the days these bills fell on:")
for k, lbl in ((0, "no visits"), (1, "under 10"), (2, "10-24"), (3, "25 or more")):
    if nvisits[k]: print("     %-12s %d" % (lbl, nvisits[k]))
print("  -> the busier the day, the more names there are to collide with.")
con.close()
