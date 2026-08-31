#!/usr/bin/env python3
"""why_unmatched.py -- read-only. WHY did each of the 145 fail, rung by rung?

The owner: the pre-June work matched the majority by PATIENT NAME on the sale
bill, and resolved duplicate names against the Docterz VISIT records. This asks
whether the current matcher is using the visit ledger anything like that hard.

Counts and masked shapes only -- digits become #, letters A. No name, no number,
no bill text is ever printed. Writes nothing.
"""
import collections, os, re, sqlite3, sys
sys.path.insert(0, "/root/finance")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
import finance_daily_gaps as G
import finance_patient_match as M

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
days = sorted(r[0] for r in con.execute(
    "SELECT business_date FROM day_entry WHERE unit='medical' "
    "AND business_date >= ? ORDER BY business_date", (G.IDENTITY_ERA_START,)).fetchall())

def shape(v):
    s = re.sub(r"\d", "#", str(v or "")); s = re.sub(r"[A-Za-z]", "A", s)
    s = re.sub(r"A{2,}", "A+", s); s = re.sub(r"#{2,}", "#+", s)
    return s[:34]

what = collections.Counter(); shapes = collections.Counter()
rungs = collections.Counter(); visitday = collections.Counter()
namehits = collections.Counter()
for d in days:
    rows = con.execute(
        "SELECT s.id, s.description, s.service FROM sale_item s "
        "JOIN day_entry dd ON dd.id=s.day_entry_id "
        "WHERE dd.unit='medical' AND dd.business_date=? "
        "AND COALESCE(s.description,'') <> ''", (d,)).fetchall()
    nvis = con.execute("SELECT COUNT(*) c FROM patient_visit WHERE visit_date=?",
                       (d,)).fetchone()["c"]
    for r in rows:
        if (r["service"] or "").endswith("_return"): continue
        res = M.match_bill(con, r["description"], d)
        if res["verdict"] != "unmatched": continue
        ident = M.read_bill_identity(r["description"])
        key = ("id" if ident["clinic_id"] else "-", 
               "mob" if ident["mobile"] else "-",
               "name" if ident["name"] else "-")
        what["+".join(x for x in key if x != "-") or "nothing at all"] += 1
        shapes[shape(r["description"])] += 1
        for st in res["steps"]:
            rungs[(st["step"], str(st["detail"])[:44])] += 1
        visitday[("visits that day: %d" % (0 if nvis == 0 else 1 if nvis < 5 else 2))] += 1
        # would a NAME-ONLY search of the whole visit ledger find exactly one?
        if ident["name"]:
            cand = con.execute(
                "SELECT DISTINCT p.clinic_id FROM patient_visit v "
                "JOIN patient_ref p ON p.clinic_id=v.clinic_id").fetchall()
            hits = [c["clinic_id"] for c in cand
                    if M.names_agree(ident["name"],
                                     con.execute("SELECT name FROM patient_ref "
                                                 "WHERE clinic_id=?", (c["clinic_id"],)
                                                 ).fetchone()["name"])]
            namehits["exactly one" if len(hits) == 1 else
                     "none" if not hits else "several (%d)" % min(len(hits), 9)] += 1

print("UNMATCHED post-era sales examined: %d\n" % sum(what.values()))
print("what the bill actually carried:")
for k, v in what.most_common(): print("   %-22s %5d" % (k, v))
print("\nthe most common text shapes (digits masked, letters folded):")
for k, v in shapes.most_common(12): print("   %5d  %s" % (v, k or "(empty)"))
print("\nwhere the chain stopped:")
for k, v in rungs.most_common(14): print("   %5d  %-16s %s" % (v, k[0], k[1]))
print("\nvisits recorded on the bill's own day:")
for k, v in visitday.most_common(): print("   %-22s %5d" % (k, v))
print("\nIF WE SEARCHED THE WHOLE VISIT LEDGER BY NAME ALONE:")
for k, v in namehits.most_common(): print("   %-22s %5d" % (k, v))
print("\n   'exactly one' is the population the owner's pre-June method recovered.")
con.close()
