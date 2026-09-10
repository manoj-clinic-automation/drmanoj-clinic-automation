#!/usr/bin/env python3
"""set_improve.py -- kit S238_SHEET2_REVIEW. The owner's ruling of 10-Sep-2026:
"the 30 % is too high a benchmark, so a 20% improvement releases hold". Writes
improve_pct = 20 through salary_policy.save_settings() -- the same validated,
audited door the settings page uses -- and prints the value before and after.
   usage: set_improve.py <dir holding the installed salary_policy.py>"""
import sys, importlib.util, os
d = sys.argv[1]
spec = importlib.util.spec_from_file_location("salary_policy_set", os.path.join(d, "salary_policy.py"))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
before = M.load_settings().get("improve_pct")
if before == 20:
    print("improve_pct already 20 -- nothing written"); sys.exit(0)
ok, err = M.save_settings({"improve_pct": 20}, by="manoj (owner ruling 10-Sep-2026, kit S238_SHEET2_REVIEW)")
after = M.load_settings().get("improve_pct")
print("improve_pct: %s -> %s" % (before, after))
sys.exit(0 if ok and after == 20 else 1)
