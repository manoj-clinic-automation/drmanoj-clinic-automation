import importlib.util, sys, random, datetime
def load(p, n):
    spec = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
random.seed(7)
import os
names = ["Darpan","Surendra","Shivani","Ranjeet","Sukhveer","Shavez","Amir","Alisha","Parvesh"] + (["Extra%d" % i for i in range(int(os.environ.get("EXTRA","0")))])
ym = "2026-08"; staff = []
for i, n in enumerate(names):
    g = {}; leave = set()
    for d in range(1, 32):
        wd = datetime.date(2026, 8, d).weekday()
        r = random.random()
        if r < .06: g[d] = {"st": "AB"}; 
        elif r < .09: g[d] = {"st": "AB"}; leave.add("2026-08-%02d" % d)
        elif wd == 6 and r < .5: g[d] = {"st": "OFF"}
        else:
            late = random.choice([0,0,0,0,5,12,25,70])
            g[d] = {"st": "P", "in": "%02d:%02d" % (10 + late // 60, late % 60), "out": "19:05", "late": late, "req": r > .97}
    staff.append({"uid": i, "name": n, "grid": g, "leave_dates": leave, "present": 25, "absent_excl": 2,
                  "leave_in_absent": len(leave), "marks": 3, "late_min": 140})
res = {"ym": ym, "staff": staff, "notes": ["A note line from the engine, as the live page carries."], "enforced": True}
for tag, path in (("old", "/mnt/user-data/uploads/dr-manoj-git/drmanoj-clinic-automation/deploy_kits/S200_R10/salary_policy.py"),
                  ("new", "/home/claude/S238_SHEET1_PRINT/kit/salary_policy.py")):
    P = load(path, "sp_" + tag)
    open("/tmp/s1_%s.html" % tag, "w").write(P.sheet1_html(res, doors=False, prefix="/register", print_=True))
    open("/tmp/s1_%s_screen.html" % tag, "w").write(P.sheet1_html(res, doors=True, prefix="/register", back="/x", approve_html="<div class='apvbar'>approve</div>"))
print("ok")
