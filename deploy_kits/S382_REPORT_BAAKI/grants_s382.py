#!/usr/bin/env python3
"""grants_s382.py -- kit S382_REPORT_BAAKI. A DATA edit of /root/portal/tile_grants.json: the tile 'Report baaki' is
granted by name to sukhveer, alisha, shivani and shavez (the owner, 24-Sep-2026); the version moves up by one.
Nothing else in the file changes; a name already there is left alone.
  python3 grants_s382.py <tile_grants.json> [--out FILE]"""
import json, sys
TILE, WHO = "Report baaki", ("sukhveer", "alisha", "shivani", "shavez")
src = sys.argv[1]
out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else src
raw = open(src, encoding="utf-8").read()
d = json.loads(raw)
added = []
for u in WHO:
    e = d["users"].setdefault(u, {})
    ex = e.setdefault("extra", [])
    if TILE not in ex:
        ex.append(TILE); added.append(u)
    if TILE in (e.get("mask") or []):
        e["mask"] = [m for m in e["mask"] if m != TILE]
if added:
    d["version"] = int(d.get("version") or 0) + 1
    ind = 2 if raw.lstrip().startswith("{\n  ") else (1 if "\n " in raw[:20] else 2)
    open(out, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=ind) + ("\n" if raw.endswith("\n") else ""))
print("GRANTS_S382 OK: version %s, granted to %s" % (d.get("version"), ", ".join(added) or "nobody new (already there)"))
