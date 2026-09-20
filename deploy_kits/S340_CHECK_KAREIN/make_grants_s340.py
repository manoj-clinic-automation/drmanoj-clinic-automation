#!/usr/bin/env python3
"""make_grants_s340.py -- tile_grants.json v22 -> v23 (S340). One tile granted by name, nothing withdrawn:
'Check karein' to alisha, shivani (reception) and shavez (the checker). The doctors hold it by role.
Written with the same json.dumps shape the file already uses (indent 2, ensure_ascii False).
Usage: make_grants_s340.py IN OUT"""
import json
import sys

TILE = "Check karein"
WHO = ["alisha", "shivani", "shavez"]
d = json.load(open(sys.argv[1], encoding="utf-8"))
assert d.get("version") == 22, "expected v22, found %r" % d.get("version")
for u in WHO:
    e = d["users"].setdefault(u, {})
    ex = e.setdefault("extra", [])
    if TILE not in ex:
        ex.append(TILE)
d["version"] = 23
d["_note"] += (" | v23 (S340, 20-Sep-2026): the NEW tile 'Check karein' (/finance/checks) to alisha and shivani "
               "(reception, who answer the patient-records queue) and shavez (the checker); the doctors hold it by "
               "role. Its gate is a NEW server unit 'checks'; nothing else in this file moves.")
open(sys.argv[2], "w", encoding="utf-8").write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
print("v23 written")
