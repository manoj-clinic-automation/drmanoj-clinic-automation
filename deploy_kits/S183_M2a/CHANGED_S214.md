# CHANGED AT S214 -- F-185 fixture scrub

The selftest/docstring fixtures in `marg_report.py` carried three real-shaped
phone numbers with name-shaped strings beside them. Replaced with
obviously-fake 90000000xx numbers and fictional names by the
deterministic fixer (deploy_kits/S214_F185_FIX/fix_f185_fixtures.py);
selftest 38/38 before and after. SUMS.md5 row regenerated same day.
