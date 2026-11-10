#!/usr/bin/env python3
"""proof_s771.py FILES_DIR SHARED_DIR FINANCE_DIR PROOF_DB LABEL -- on ONE COPY of finance.db (and the box's assets.db, READ ONLY):
the Orthotic bills card by the kit's section_count.py with this box's real section_map. Prints each bill (masked of nothing -- dealer
bills carry no patient), never writes the live file. Last line: 'PROOF S771 LABEL: ...'."""
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
SC.ensure_s771(con)
C = SC.bills_card(con, "Orthotics")
for grp in ("now", "open"):
    for x in C[grp]:
        print("%-4s bill %-14s %s %-13s %d lines%s" % (grp, x["no"], x["date"], x["state"], len(x["lines"]), " (number spilled, read)" if x["overflow"] else ""))
        for l in x["lines"]:
            if l["kind"]:
                print("        %s" % l["why"])
print("settled: " + ", ".join("%s (%s)" % (s["no"], s["date"]) for s in C["settled"]))
con.rollback()
diff = sum(1 for x in C["now"] + C["open"] if x["state"] == "differs")
print("PROOF S771 %s: dealers %s · this month %d · earlier still open %d · settled %d · differing bills %d · scans %s"
      % (LABEL, "+".join(C["dealers"]) or "none", len(C["now"]), len(C["open"]), len(C["settled"]), diff, "read" if C["scans_ok"] else "NOT read"))
