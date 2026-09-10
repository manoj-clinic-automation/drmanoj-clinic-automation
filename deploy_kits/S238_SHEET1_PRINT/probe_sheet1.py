#!/usr/bin/env python3
"""probe_sheet1.py -- S238_SHEET1_PRINT. Renders Sheet 1 from the NEW salary_policy.py
with a synthetic 31-day month (invented names and times, no staff data) on the box's
own python, BEFORE install. Proves the print blocks are present and nothing raises."""
import importlib.util, sys, datetime
spec = importlib.util.spec_from_file_location("sp_new", sys.argv[1])
P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
staff = []
for i in range(9):
    g = {d: ({"st": "AB"} if d % 11 == 0 else {"st": "P", "in": "10:%02d" % (d % 40), "out": "19:00",
              "late": d % 40, "req": d == 7}) for d in range(1, 32)}
    staff.append({"uid": i, "name": "Staff%d" % i, "grid": g, "leave_dates": {"2026-08-22"}, "present": 28,
                  "absent_excl": 2, "leave_in_absent": 1, "marks": 2, "late_min": 90})
res = {"ym": "2026-08", "staff": staff, "notes": [], "enforced": True}
fails = []
h = P.sheet1_html(res, doors=False, prefix="/register", print_=True)
for need in ('class="s1grid"', 'class="s1sum"', "@page{size:A4 portrait", "break-after:page",
             "MONTH SUMMARY", ">31<", "min-width:140px"):
    if need not in h: fails.append("print page lacks " + need)
h2 = P.sheet1_html(res, doors=True, prefix="/register", back="/x", approve_html="<b>ap</b>")
if "FIX ABSENTS" not in h2 or ">31<" not in h2: fails.append("screen page lost its content")
h3 = P.sheet1_html(res, only_uid=3)
if "Staff3" not in h3 or "Staff4" in h3: fails.append("a staff member's own view shows someone else")
for f in fails: print("  FAIL: " + f)
print("sheet1 probe: %d failures" % len(fails))
sys.exit(1 if fails else 0)
