#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s945.py -- kit S945 on a MADE-UP root. No live file, no network, nothing written outside a temp folder.
    python3 walk_s945.py <code_bundle.py (the kit's)> <scratch dir> [--control]
  1. retire_s945.py --selftest (the three leftovers moved, the numbers gone, 0700/0600, again, undo)
  2. the kit's code_bundle.py gather() on a made-up ROOT: /root/followup_tracker/{server_runner.py, processor.py, undo.sh,
     OFF, SWITCHED_AT, state.json, seed.txt, token_x.py} + data/ uploads/ archive/ venv/ logs/ outputs/ intake/ with files inside,
     plus /root/_retired/S510/make_force_keys.py and /root/finance/finance_app.py: the two .py + the .sh are carried; nothing
     from the folders; OFF/SWITCHED_AT/json/txt/token out; _retired out; finance_app.py still in.
  --control: the FROM code_bundle.py (CB_FROM env) -> the tracker absent -> red.   Last line: WALK n/n
"""
import importlib.util
import os
import subprocess
import sys

CB = os.path.abspath(sys.argv[1])
SCR = os.path.abspath(sys.argv[2])
HERE = os.path.dirname(os.path.abspath(__file__))
if "--control" in sys.argv:
    CB = os.environ.get("CB_FROM", CB)
n = f = 0


def ok(name, cond):
    global n, f
    n += 1
    print(("  ok   " if cond else "  FAIL ") + name)
    if not cond:
        f += 1


r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "retire_s945.py"), "--selftest"], capture_output=True, text=True, env=dict(os.environ, TMPDIR=SCR))
ok("retire_s945.py --selftest %s" % (r.stdout.strip().splitlines() or ["?"])[-1], r.returncode == 0 and r.stdout.strip().endswith("SELFTEST 10/10"))

root = os.path.join(SCR, "root")
os.makedirs(root, exist_ok=True)
def put(rel, body="x = 1\n"):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(body)
for rel in ("root/followup_tracker/server_runner.py", "root/followup_tracker/processor.py", "root/followup_tracker/undo_s895.sh",
            "root/followup_tracker/OFF", "root/followup_tracker/SWITCHED_AT", "root/followup_tracker/state.json", "root/followup_tracker/seed.txt",
            "root/followup_tracker/token_helper.py", "root/followup_tracker/data/ledger.csv", "root/followup_tracker/uploads/u.xlsx",
            "root/followup_tracker/archive/a.csv", "root/followup_tracker/venv/bin/python3", "root/followup_tracker/logs/runner.log",
            "root/followup_tracker/outputs/o.xlsx", "root/followup_tracker/intake/i.csv", "root/followup_tracker/data/helper.py",
            "root/_retired/S510/make_force_keys.py", "root/finance/finance_app.py", "root/state_backup/code_bundle.py"):
    put(rel)
os.environ["ROOT"] = root
spec = importlib.util.spec_from_file_location("cb_s945", CB)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
files, skipped, hits = mod.gather()
rels = {rel for rel, _ in files}
ok("the tracker's two .py and the .sh carried", {"root/followup_tracker/server_runner.py", "root/followup_tracker/processor.py", "root/followup_tracker/undo_s895.sh"} <= rels)
ok("nothing from data/ uploads/ archive/ venv/ logs/ outputs/ intake/ (a .py inside data/ too)", not any(rel.startswith("root/followup_tracker/") and rel.count("/") > 2 for rel in rels))
ok("OFF, SWITCHED_AT, state.json, seed.txt out", not any(rel.endswith(("/OFF", "/SWITCHED_AT", "state.json", "seed.txt")) for rel in rels))
ok("a token-named file out", "root/followup_tracker/token_helper.py" not in rels)
ok("_retired never entered", not any("_retired" in rel for rel in rels))
ok("finance_app.py still carried", "root/finance/finance_app.py" in rels)
ok("the SOURCES line is non-recursive and names only *.py and *.sh", any(d == "root/followup_tracker" and tuple(p) == ("*.py", "*.sh") and rec is False for d, p, rec, _ in mod.SOURCES))
print("WALK %d/%d" % (n - f, n))
sys.exit(1 if f else 0)
