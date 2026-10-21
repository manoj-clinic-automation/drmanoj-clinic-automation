#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s610.py -- kit S610 (S331): a double press on arrival is not an OUT punch on the attendance page.

    python3 walk_s610.py --code DIR --base DIR --scratch DIR
--code: the folder with the att_dashboard.py under test.  --base: the folder with att_config.py, att_core.py and
att_month_report.py (on the box: /root, only read).  Made-up person 9901 "Walk One" and made-up punches in a scratch
folder; the live punches.csv and staff master are never opened.  Exit 0 = GREEN; the old file goes RED.
"""
import argparse
import datetime
import os
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--code", required=True)
ap.add_argument("--base", required=True)
ap.add_argument("--scratch", required=True)
a = ap.parse_args()
S = os.path.abspath(a.scratch)
os.makedirs(S, exist_ok=True)
sys.path.insert(0, os.path.abspath(a.base))
sys.path.insert(0, os.path.abspath(a.code))
sys.dont_write_bytecode = True
import att_config as cfg  # noqa: E402

today = datetime.date.today()
d0 = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=10)
while d0.weekday() == 6:
    d0 += datetime.timedelta(days=1)
d1 = d0 + datetime.timedelta(days=1)
if d1.weekday() == 6:
    d1 += datetime.timedelta(days=1)
SM = os.path.join(S, "staff_master.csv")
PC = os.path.join(S, "punches.csv")
with open(SM, "w") as fh:
    fh.write("user_id,name,department,base_salary,allowed_offs,wd_start,wd_end,sun_start,sun_end,active,timing_note,"
             "sunday_group,minutes_exempt\n9901,Walk One,Pathology,9000,2,09:00,21:00,09:00,15:00,Y,,C,N\n"
             "9902,Walk Two,Clinic,9000,2,09:00,21:00,,,Y,,,N\n")
with open(PC, "w") as fh:
    fh.write("user_id,datetime,io_mode,verify_mode,received_at\n")
    fh.write("9901,%s 09:22:05,0,1,x\n9901,%s 09:22:40,0,1,x\n" % (d0, d0))       # a double press, no out
    fh.write("9901,%s 09:00:10,0,1,x\n9901,%s 18:30:00,0,1,x\n" % (d1, d1))       # a real out
cfg.STAFF_MASTER = SM
cfg.PUNCH_CSV = PC
cfg.EXCLUDE_IDS = set()
import att_core as core  # noqa: E402
if getattr(core, "STAFF_MASTER", None) is not None:
    core.STAFF_MASTER = SM
if getattr(core, "PUNCH_CSV", None) is not None:
    core.PUNCH_CSV = PC
import att_dashboard as D  # noqa: E402
D.authed = lambda: True
C = D.app.test_client()
passed, failed = [], []


def check(cond, label):
    (passed if cond else failed).append(label)
    print(("  ok   " if cond else "  FAIL ") + label)
    return cond


staff = core.load_staff()
check(9901 in staff or "9901" in staff, "the made-up person is read from the scratch staff master")
print("[a] the month grid")
html = C.get("/month?ym=%s" % d0.strftime("%Y-%m")).data.decode()
check("09:22<br><span class=\"out\">09:22</span>" not in html, "the double press is NOT shown as an out time")
check("18:30" in html, "a real out punch still shows (18:30)")
check('"o": "09:22"' not in html.replace("'", '"'), "nor in the phone view's data")
import re  # noqa: E402
sun0 = d0.replace(day=1)
while sun0.weekday() != 6:
    sun0 += datetime.timedelta(days=1)
rows_html = {m.group(1): m.group(0) for m in re.finditer(r'<tr><td class="nm">(Walk (?:One|Two))</td>.*?</tr>', html, re.S)}
r1 = rows_html.get("Walk One", "")
r2 = rows_html.get("Walk Two", "")
cells1 = re.findall(r"<td class=\"([^\"]*)\">(.*?)</td>", r1)[:]
day_cells1 = [c for c in cells1 if "tot" not in c[0] and c[0] != "nm"]
day_cells2 = [c for c in re.findall(r"<td class=\"([^\"]*)\">(.*?)</td>", r2) if "tot" not in c[0] and c[0] != "nm"]
check(len(day_cells1) >= sun0.day and day_cells1[sun0.day - 1][1] == "A",
      "a Sunday-duty person's missed Sunday reads A (%s)" % sun0)
check(len(day_cells2) >= sun0.day and day_cells2[sun0.day - 1][1] == "off", "a person with no Sunday duty reads off")
tot1 = re.findall(r'<td class="tot abs2">(\d+)</td>', r1)
abs_days = sum(1 for c in day_cells1 if c[1] == "A")
check(tot1 and int(tot1[0]) == abs_days and abs_days >= 1, "the A total counts every A on the row (%s)" % (tot1[0] if tot1 else "-"))
check('"duty"' in html and ('"%d": 1' % sun0.day) in html, "the phone view knows the duty Sunday too")

print("[b] the day view")
dv = C.get("/?date=%s" % d0.isoformat()).data.decode()
check("left early" not in dv, "the double press is not 'left early'")
check("no out punch" in dv, "it says: pressed twice on arrival, no out punch")
dv2 = C.get("/?date=%s" % d1.isoformat()).data.decode()
check("09:00 – 18:30" in dv2 or "09:00 &ndash; 18:30" in dv2, "a real day still shows 09:00 – 18:30")
print("")
print("WALK S610: %d passed, %d failed" % (len(passed), len(failed)))
print("GREEN" if not failed else "RED")
sys.exit(0 if not failed else 1)
