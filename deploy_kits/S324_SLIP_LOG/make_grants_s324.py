#!/usr/bin/env python3
"""make_grants_s324.py -- tile_grants.json v19 -> v20 (S324). One tile granted by name, nothing withdrawn:
'OPD & X-ray/Proc Slips' to shavez, alisha, shivani, bhati (the chamber) and awdhesh (the room).
Written with the same json.dump shape the file already uses (indent 2, ensure_ascii False).
Usage: make_grants_s324.py IN OUT"""
import json
import sys

TILE = "OPD & X-ray/Proc Slips"
WHO = ["shavez", "alisha", "shivani", "bhati", "awdhesh"]
d = json.load(open(sys.argv[1], encoding="utf-8"))
assert d.get("version") == 19, "expected v19, found %r" % d.get("version")
for u in WHO:
    e = d["users"].setdefault(u, {})
    ex = e.setdefault("extra", [])
    if TILE not in ex:
        ex.append(TILE)
d["version"] = 20
d["_note"] += (" | v20 (S324, 19-Sep-2026): the NEW tile 'OPD & X-ray/Proc Slips' (/finance/slips) to shavez, "
               "alisha, shivani and bhati (the chamber assistants who log the slip number and clinic ID) and to "
               "awdhesh (the X-ray/procedure room, who ticks Paid and Done); the doctor holds it by role. Its gate "
               "is a NEW server unit 'slips'; nothing else in this file moves.")
open(sys.argv[2], "w", encoding="utf-8").write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
print("v20 written")
