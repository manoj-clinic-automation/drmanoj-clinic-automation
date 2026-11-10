#!/usr/bin/env python3
"""proof_s769.py FILES_DIR SHARED_DIR FINANCE_DIR PROOF_DB LABEL -- on ONE COPY of finance.db: the hub's list by the kit's
section_count.py with this box's real section_map / scan_register, and the shape of unit_role the switch writes. Writes nothing
the live file would see. Last line: 'PROOF S769 LABEL: ...'."""
import os
import sqlite3
import sys

FILES, SHARED, FIN, PDB, LABEL = sys.argv[1:6]
if os.path.abspath(PDB).startswith("/root/finance/"):
    print("REFUSED: the proof runs on a copy, never in /root/finance")
    sys.exit(2)
sys.path[:0] = [FILES, FIN, SHARED]
try:
    import flask  # noqa: F401
except ImportError:                                            # the device VM has no flask: the module needs only the names
    import types
    f = types.ModuleType("flask")
    f.Blueprint = lambda *a, **k: types.SimpleNamespace(route=lambda *a, **k: (lambda fn: fn))
    f.jsonify = f.request = f.send_file = None
    sys.modules["flask"] = f
import section_count as SC  # noqa: E402

con = sqlite3.connect(PDB, timeout=30)
con.row_factory = sqlite3.Row
SC.ensure_schema(con)
H = SC.hub(con)
cols = {r[1] for r in con.execute("PRAGMA table_info(unit_role)")}
ur = "ok" if {"unit", "username", "role", "active", "note"} <= cols else "BAD"
t = H["templates"][0]
print("template: %s · %d items · guard %s · open count %s" % (t["section"], t["items"], ("blocked" if t["guard"]["blocked"] else "clear") if t["guard"]["checked"] else "unchecked", t["open"]))
print("counts: " + "; ".join("#%d %s %s" % (c["id"], c["section"], c["status"]) for c in H["counts"]) if H["counts"] else "counts: none")
print("who may count: " + ", ".join("%s %s" % (s["user"], "on" if s["on"] else "off") for s in H["staff"]))
print("whole shop: %d items · plan %s" % (H["whole"]["items"], H["whole"]["plan"]))
con.rollback()
print("PROOF S769 %s: template %s %d items · counts %d · staff %d · unit_role %s" % (LABEL, t["section"], t["items"], len(H["counts"]), len(H["staff"]), ur))
