#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_fixture.py — writes the walk's test ledger.

The kit deliberately ships NO .json or .jsonl file: the repository's .gitignore
blocks them (F-300, and this kit was its fourth recurrence — the publish refused
a fixture on 10-Sep-2026). So the fixture is GENERATED here instead of stored.

It is built to be as awkward as the real ledger: an advance keyed wrong, contra'd
and re-entered; an advance already cleared; an interest-bearing loan with a
skipped month and capitalised interest; a pending request; and a rejected row.
The names are staff names used throughout this project; every amount is invented.

  python3 _proof/make_fixture.py /tmp/fixture_ledger.jsonl
"""
import json, sys

def build():
    rows = []
    def add(**k):
        rows.append({
            "id": k["id"], "ts_entry": "2026-08-01T10:00", "maker": "shavez",
            "staff": k["staff"], "category": k["cat"],
            "date_from": k.get("df", "2026-08-01"), "date_to": k.get("df", "2026-08-01"),
            "days": 0, "amount": k["amt"], "instalment": k.get("inst"),
            "narration": k.get("n", ""), "self_flag": False, "direct": True,
            "status": k.get("st", "APPROVED"), "checker": "drmanoj",
            "ts_decision": "2026-08-01T10:05", "contra_of": k.get("co", ""),
            "closed_month": k.get("cm", ""), "interest": k.get("intr", False)})
    add(id='d001', staff='Darpan', cat='ADVANCE_ISSUE', amt=25000, inst=5000, df='2026-08-17', n='advance application 17 aug')
    add(id='d002', staff='Darpan', cat='ADVANCE_ISSUE', amt=-25000, co='d001', df='2026-08-01', n='CONTRA of d001: amount keyed wrong')
    add(id='d003', staff='Darpan', cat='ADVANCE_ISSUE', amt=15000, inst=3000, df='2026-08-17', n='advance application 17 aug (corrected)')
    add(id='d100', staff='Darpan', cat='ADVANCE_INSTALMENT', amt=-3000, co='d003', df='2026-08', cm='2026-08')
    add(id='d900', staff='Darpan', cat='ADVANCE_ISSUE', amt=4000, inst=2000, df='2026-06-05', n='june advance')
    add(id='d901', staff='Darpan', cat='ADVANCE_INSTALMENT', amt=-2000, co='d900', df='2026-06', cm='2026-06')
    add(id='d902', staff='Darpan', cat='ADVANCE_INSTALMENT', amt=-2000, co='d900', df='2026-07', cm='2026-07')
    add(id='d910', staff='Darpan', cat='NIGHT_DUTY', amt=1200, df='2026-08-10', cm='2026-08')
    add(id='s001', staff='Surendra', cat='ADVANCE_ISSUE', amt=13000, inst=2000, df='2026-06-01', intr=True, n='loan with schedule')
    add(id='s101', staff='Surendra', cat='ADVANCE_INSTALMENT', amt=-2000, co='s001', df='2026-06', cm='2026-06')
    add(id='s102', staff='Surendra', cat='LOAN_INTEREST', amt=-1000, co='s001', df='2026-06', cm='2026-06')
    add(id='s103', staff='Surendra', cat='LOAN_SKIP', amt=0, co='s001', df='2026-07')
    add(id='s104', staff='Surendra', cat='LOAN_CAPITALISE', amt=1000, co='s001', df='2026-07')
    add(id='s105', staff='Surendra', cat='ADVANCE_INSTALMENT', amt=-2000, co='s001', df='2026-08', cm='2026-08')
    add(id='s106', staff='Surendra', cat='LOAN_INTEREST', amt=-1000, co='s001', df='2026-08', cm='2026-08')
    add(id='s900', staff='Surendra', cat='FINE_UNIFORM', amt=-20, df='2026-08-04', cm='2026-08')
    add(id='s901', staff='Surendra', cat='ADVANCE_ISSUE', amt=6000, inst=2000, df='2026-08-28', st='PENDING', n='asked for another')
    add(id='a001', staff='Amir', cat='NIGHT_DUTY', amt=800, df='2026-08-12', cm='2026-08')
    add(id='z001', staff='Amir', cat='OTHER', amt=-500, df='2026-08-01', st='REJECTED', n='keyed twice')
    return rows

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fixture_ledger.jsonl"
    rows = build()
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print("wrote %d rows to %s" % (len(rows), out))
