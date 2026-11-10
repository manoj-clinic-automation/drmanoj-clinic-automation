#!/usr/bin/env python3
"""proof_s768.py FILES_DIR SHARED_DIR FINANCE_DIR PROOF_DB LABEL
On ONE COPY of finance.db (never the live file): the seed, the guard and a start of an Orthotics count by the kit's
section_count.py with this box's real section_map / scan_register. Prints what the owner's first count would hold; writes only
to the copy. Last line: 'PROOF S768 LABEL: ...'."""
import os
import sqlite3
import sys
import types

FILES, SHARED, FIN, PDB, LABEL = sys.argv[1:6]
if os.path.abspath(PDB).startswith("/root/finance/"):
    print("REFUSED: the proof runs on a copy, never in /root/finance")
    sys.exit(2)
sys.path[:0] = [FILES, FIN, SHARED]
try:
    import flask  # noqa: F401
except ImportError:                                            # the device VM has no flask: the module needs only the names
    f = types.ModuleType("flask")
    f.Blueprint = lambda *a, **k: types.SimpleNamespace(route=lambda *a, **k: (lambda fn: fn))
    f.jsonify = f.request = f.send_file = None
    sys.modules["flask"] = f
import section_count as SC  # noqa: E402

con = sqlite3.connect(PDB, timeout=30)
con.row_factory = sqlite3.Row
nd, nf = SC.seed_from(con, os.path.join(FILES, "section_count_seed_S768.txt"), who="proof")
g = SC.guard(con, "Orthotics")
dealers = sorted(SC.section_dealers(con, "Orthotics"))
ok, res, code = SC.start(con, "Orthotics", "proof", override=True, is_owner=True)
if not ok:
    print("start refused:", res, code)
    print("PROOF S768 %s: start refused (%s)" % (LABEL, code))
    sys.exit(1)
cid = res["count"]
rows = con.execute("SELECT * FROM section_count_line WHERE count_id=? ORDER BY n", (cid,)).fetchall()
disp = {r[0] for r in con.execute("SELECT item_key FROM section_item_display")}
new = [r["item"] for r in rows if r["item_key"] not in disp]
s1 = [r for r in rows if r["flag"] == 1]
s2 = [r for r in rows if r["flag"] == 2]
names = [r["item"] for r in rows]
ren = [(n, SC.rename_for(n, names)) for n in names if SC.loses_size(n)]
print("seed: display %d, marks %d" % (nd, nf))
print("dealers of the section: %d (%s)" % (len(dealers), ", ".join(dealers[:8])))
print("guard: checked %s, blocked %s" % (g["checked"], g["blocked"]) + ("" if g["checked"] else " -- " + g["why"]))
for l in g["lines"][:10]:
    print("   " + l["text"])
print("the count's lines: %d (snapshot %s) · new names not in the paper: %s" % (len(rows), con.execute("SELECT snap_as_on FROM section_count WHERE id=?", (cid,)).fetchone()[0],
                                                                                ", ".join(new) or "none"))
print("two stars: " + ", ".join("#%d %s" % (r["n"], r["item"]) for r in s2))
print("one star : %d -- %s" % (len(s1), ", ".join("#%d" % r["n"] for r in s1)))
for n, newn in ren:
    print("rename   : %s -> %s" % (n, newn))
cols = {r[1] for r in con.execute("PRAGMA table_info(amir_job)")}
uniq = any(r[2] and [x[2] for x in con.execute("PRAGMA index_info('%s')" % r[1])] == ["key"] for r in con.execute("PRAGMA index_list(amir_job)"))
aj = "ok" if ({"key", "kind", "subject", "text_hi", "sub_hi", "created_at", "created_by", "show_from"} <= cols and uniq) else "BAD"
for w in g.get("warns") or []:
    print("   to look at: " + w["text"])
print("PROOF S768 %s: lines %d · one-star %d · two-star %d · new %d · guard %s (%d waiting) · renames %d · amir_job %s" %
      (LABEL, len(rows), len(s1), len(s2), len(new), ("blocked" if g["blocked"] else "clear") if g["checked"] else "unchecked", len(g["lines"]), len(ren), aj))
