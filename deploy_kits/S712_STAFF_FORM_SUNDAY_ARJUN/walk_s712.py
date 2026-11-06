# walk_s712.py -- kit S712_STAFF_FORM_SUNDAY_ARJUN (session 389, the parent, 06-Nov-2026)
# Walks the Add staff form's server code on a MADE-UP root (temp registers, temp staff_master.csv,
# temp punches) -- never the live files. The attendance side is read through the REAL
# att_core / att_month_report, with att_config replaced by a stub pointing at the temp files.
#
#   python walk_s712.py <dir with staff_easy.py + staff_easy.html> <dir with joiner_app.py> <dir with att_core.py>
#   last line: "N of N green"  (or "X S712 check(s) red . Y green")
import csv, datetime, io, json, os, shutil, sqlite3, sys, tempfile, types

KDIR, FINLIB, ATTLIB = [os.path.abspath(a) for a in sys.argv[1:4]]
T = tempfile.mkdtemp(prefix="s712walk_")
SM = os.path.join(T, "staff_master.csv")
PU = os.path.join(T, "punches.csv")
SR = os.path.join(T, "staff_register.db")
FIN = os.path.join(T, "finance.db")
HEAD = ["user_id", "name", "department", "base_salary", "allowed_offs", "wd_start", "wd_end",
        "sun_start", "sun_end", "active", "timing_note", "sunday_group", "minutes_exempt"]
with io.open(SM, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, lineterminator="\n"); w.writerow(HEAD)
    w.writerow([5, "Madeup Old", "Clinic", 9000, 2, "09:00", "21:00", "09:00", "21:00", "Y", "", "A", "N"])
with io.open(PU, "w", encoding="utf-8", newline="") as f:
    f.write("user_id,datetime\n")
os.environ["STAFF_EASY_SR_DB"] = SR
os.environ["ATT_STAFF_MASTER"] = SM
os.environ["ATT_PUNCH_CSV"] = PU
os.environ["ATT_ROSTER_FROM"] = "2099-01"
cfg = types.ModuleType("att_config")
cfg.STAFF_MASTER, cfg.PUNCH_CSV, cfg.EXCLUDE_IDS = SM, PU, set()
cfg.GRACE_MIN, cfg.FLAG_LATE_ON_SUNDAY = 10, False
sys.modules["att_config"] = cfg

# the kit's (or the live) staff_easy first on the path; joiner_app and att_* from their own dirs
STAGE = os.path.join(T, "code"); os.makedirs(STAGE)
for fn in ("staff_easy.py", "staff_easy.html"):
    shutil.copy(os.path.join(KDIR, fn), STAGE)
for fn in ("joiner_app.py", "joiner_schema.sql"):
    shutil.copy(os.path.join(FINLIB, fn), STAGE)
for fn in ("att_core.py", "att_month_report.py"):
    shutil.copy(os.path.join(ATTLIB, fn), STAGE)
sys.path.insert(0, STAGE)
sys.dont_write_bytecode = True

from flask import Flask
import joiner_app as J
import staff_easy as E
import att_core, att_month_report as AMR


def fin_db():
    c = sqlite3.connect(FIN, timeout=15); c.row_factory = sqlite3.Row; return c


J._db = fin_db
app = Flask("s712walk")
E.init(app, lambda role: ({"user": "manoj", "role": "checker"}, None))
cl = app.test_client()
OK, RED = [], []


def check(label, cond, why=""):
    (OK if cond else RED).append(label)
    print(("GREEN " if cond else "RED   ") + label + ("" if cond else "  -- " + str(why)[:200]))


def save(name, grp, ss="", se=""):
    b = {"person": name, "handover": "none", "employment": "PARTTIME", "job": "Cleaner",
         "join_date": "2026-11-01", "wd_start": "09:00", "wd_end": "10:30", "sunday_group": grp,
         "sun_start": ss, "sun_end": se, "base_salary": "3500", "allowed_offs": "4",
         "minutes_exempt": "1"}
    r = cl.post("/finance/staff/easy/api/save", data=json.dumps(b), content_type="application/json")
    return r.status_code, (r.get_json(silent=True) or {})


def pending(name):
    c = sqlite3.connect(SR); c.row_factory = sqlite3.Row
    r = c.execute("SELECT * FROM joiner_pending WHERE person=?", (name,)).fetchone()
    c.close(); return r


def link_row(p, code):
    """the dict api_link writes into staff_master.csv, field for field"""
    return {"user_id": code, "name": p["person"], "department": p["department"] or "",
            "base_salary": p["base_salary"], "allowed_offs": p["allowed_offs"],
            "wd_start": p["wd_start"], "wd_end": p["wd_end"],
            "sun_start": p["sun_start"] or "", "sun_end": p["sun_end"] or "",
            "active": "Y", "timing_note": "", "sunday_group": p["sunday_group"],
            "minutes_exempt": "Y" if p["minutes_exempt"] else "N"}


SUN, MON = datetime.date(2026, 11, 8), datetime.date(2026, 11, 9)

# 1 the choices the page is given
r = cl.get("/finance/staff/easy/api/list"); j = r.get_json(silent=True) or {}
check("1 the form offers exactly: Works every Sunday / Sunday off",
      j.get("sunday") == {"C": "Works every Sunday", "OFF": "Sunday off"}, j.get("sunday"))
# 2-3 the never-adopted rota choices are refused
s, j = save("Madeup Rota A", "A"); check("2 '1st and 3rd' (A) is refused", s == 400, (s, j))
s, j = save("Madeup Rota B", "B"); check("3 '2nd and 4th' (B) is refused", s == 400, (s, j))
# 4 Sunday off: saved as no Sunday group and no Sunday hours
s, j = save("Madeup Off", "OFF", "09:00", "15:00")
p = pending("Madeup Off")
check("4 Sunday off saves group '' and no Sunday hours",
      s == 200 and p is not None and (p["sunday_group"] or "") == "" and not p["sun_start"] and not p["sun_end"],
      (s, j, dict(p) if p else None))
# 5 works Sundays without hours is refused
s, j = save("Madeup NoHours", "C"); check("5 'Works every Sunday' without hours is refused", s == 400, (s, j))
# 6 works Sundays with hours
s, j = save("Madeup Sun", "C", "09:00", "10:30")
q = pending("Madeup Sun")
check("6 'Works every Sunday' saves C with his Sunday hours",
      s == 200 and q is not None and q["sunday_group"] == "C" and q["sun_start"] == "09:00" and q["sun_end"] == "10:30",
      (s, j, dict(q) if q else None))
# 7-8 what the attendance and salary then read (the real readers, on the temp list)
try:
    if p is not None:
        E._append_master(link_row(p, 91))
    if q is not None:
        E._append_master(link_row(q, 92))
    pol = AMR.load_staff_policy(); staff = att_core.load_staff()
    def shift(uid, d):
        return AMR.duty_shift(d, d.strftime("%Y-%m"), staff[uid], pol[uid])
    check("7 Sunday off: the salary reads his Sunday as OFF, his Monday as a duty day",
          91 in staff and shift(91, SUN) == (None, None) and shift(91, MON)[0] is not None,
          (shift(91, SUN), shift(91, MON)) if 91 in staff else "not in the list")
    check("8 works Sundays: the salary reads his Sunday as a duty day 09:00-10:30",
          92 in staff and tuple(x.strftime("%H:%M") for x in shift(92, SUN)) == ("09:00", "10:30"),
          shift(92, SUN) if 92 in staff else "not in the list")
except SystemExit as ex:
    check("7 the attendance report accepts what the form wrote", False, ex)
    check("8 (not reached)", False, "")
except Exception as ex:
    check("7 the attendance report accepts what the form wrote", False, repr(ex))
    check("8 (not reached)", False, "")
# 9 the page's words
h = io.open(os.path.join(STAGE, "staff_easy.html"), encoding="utf-8").read()
check("9 the page no longer says a 5th Sunday is a full day", "5th Sunday" not in h)
check("10 the page says a missed Sunday counts as one of his offs",
      "A Sunday he does not come counts as one of his offs." in h)
check("11 the page's detail line says Sunday 'off' or 'every Sunday (hours)'",
      "'every Sunday ('" in h and ":'off')" in h)
r = cl.get("/finance/staff/easy/api/health"); j = r.get_json(silent=True) or {}
check("12 the module says it is S712", j.get("kit") == "S712", j)

shutil.rmtree(T, ignore_errors=True)
n = len(OK) + len(RED)
print("%d of %d green" % (n, n) if not RED else "%d S712 check(s) red . %d green" % (len(RED), len(OK)))
