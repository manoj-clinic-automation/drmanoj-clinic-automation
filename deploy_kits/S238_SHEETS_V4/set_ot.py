#!/usr/bin/env python3
"""set_ot.py -- kit S238_SHEETS_V4. The owner's ruling of 11-Sep-2026: overtime is the
incentive for staff not to rush home when the clinic runs late -- it is PAID. Writes
ot_pay = 1 through salary_policy.save_settings() (the settings page's own validated,
audited door) and prints the value before and after. The daily threshold stays OFF.
   usage: set_ot.py <dir holding the installed salary_policy.py>"""
import sys, os, json, importlib.util
d = sys.argv[1]
spec = importlib.util.spec_from_file_location("salary_policy_set", os.path.join(d, "salary_policy.py"))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
try:
    stored = json.load(open(M.SETTINGS_PATH, encoding="utf-8")).get("ot_pay")
except Exception:
    stored = None
if stored == 1:
    print("ot_pay already 1 -- nothing written"); sys.exit(0)
ok, err = M.save_settings({"ot_pay": 1}, by="manoj (owner ruling 11-Sep-2026, kit S238_SHEETS_V4)")
after = M.load_settings().get("ot_pay")
print("ot_pay: %s -> %s  (overtime now enters the net)" % ("not stored" if stored is None else stored, after))
sys.exit(0 if ok and after == 1 else 1)
