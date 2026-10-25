#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s650.py -- kit S650_ATTCORR's walk on MADE-UP staff (D786). Nothing real is read or written.

  python3 walk_s650.py <dir holding staff_register.py + att_correction.py + salary_policy.py + salary_engine.py>
                       <dir holding att_month_report.py> [--old]

Builds a throw-away register in a temp folder (five invented staff, an invented October 2026 of punches with gaps, a
clinic holiday, a festival, a D338 correction, a day-grid leave), imports the register from the given folder with its
paths pointed there, and walks the whole flow as reception, Shavez and the owner with Flask's test client: the sheet,
the three screens and their Saves, nothing counting before approval, Approve & save writing the register's own records,
a change after approval undone and rewritten, the salary lock waiting, a locked month, an unreadable punch feed, who may
open what, and the lines' door. The last line is 'N of N green'.
--old: the control on the live register (no hook): every S650 check must be red and every older check green.
"""
import csv
import datetime
import importlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile

OLD = "--old" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]
if len(args) != 2:
    sys.exit(__doc__)
SRC, ATT = os.path.abspath(args[0]), os.path.abspath(args[1])

RES = []


def check(tag, name, ok, detail=""):
    RES.append((tag, name, bool(ok)))
    print("%s  [%s] %s%s" % ("GREEN" if ok else "RED  ", tag, name, ("  -- " + detail) if (detail and not ok) else ""))


TMP = tempfile.mkdtemp(prefix="s650walk.")
APP = os.path.join(TMP, "staff_register")
os.makedirs(APP)
for f in ("staff_register.py", "att_correction.py", "salary_policy.py", "salary_engine.py"):
    if os.path.exists(os.path.join(SRC, f)):
        shutil.copy(os.path.join(SRC, f), os.path.join(APP, f))
ATTD = os.path.join(TMP, "att")
os.makedirs(ATTD)
for f in ("att_month_report.py",):
    shutil.copy(os.path.join(ATT, f), os.path.join(ATTD, f))

PUNCH = os.path.join(TMP, "punches.csv")
MASTER = os.path.join(TMP, "staff_master.csv")
os.environ.update(SR_DB_PATH=os.path.join(TMP, "sr.db"), SR_PUNCH_CSV=PUNCH, SR_STAFF_MASTER=MASTER,
                  SR_ATT_DIR=ATTD, SR_VAULT_DIR=os.path.join(TMP, "vault"))
os.environ.pop("ATT_ROSTER_FROM", None)

# five invented people. Asha: group A, no Sunday shift (the salary reads her Sundays as OFF; the register's own
# roster would call her 1st/3rd Sundays ON -- the walk proves the salary's word is used). Bina: a Sunday shift.
STAFF = [(1, "Asha Test", "A", "09:00", "17:00", "", "", "N"),
         (2, "Bina Test", "B", "09:00", "17:00", "09:00", "13:00", "N"),
         (3, "Chetan Test", "A", "10:00", "18:00", "10:00", "14:00", "N"),
         (4, "Dev Test", "ARJ", "08:00", "16:00", "08:00", "12:00", "Y"),
         (5, "Esha Test", "B", "09:30", "17:30", "09:30", "13:30", "N")]
with open(MASTER, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["user_id", "name", "wd_start", "wd_end", "sun_start", "sun_end", "sunday_group", "minutes_exempt",
                "base_salary"])
    for sid, nm, g, ws, we, ss, se, ex in STAFF:
        w.writerow([sid, nm, ws, we, ss, se, g, ex, 10000])

YM = "2026-10"
HOLIDAY = "2026-10-02"
FEST = "2026-10-20"
GAPS = {1: {"2026-10-07", "2026-10-15", FEST}, 2: {"2026-10-03", "2026-10-10", "2026-10-18", "2026-10-24"},
        3: {"2026-10-21"}, 4: {"2026-10-22"}, 5: set()}
with open(PUNCH, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["user_id", "datetime", "status"])
    for day in range(1, 32):
        d = "%s-%02d" % (YM, day)
        if d == HOLIDAY:
            continue
        sun = datetime.date.fromisoformat(d).weekday() == 6
        for sid, nm, g, ws, we, ss, se, ex in STAFF:
            if d in GAPS[sid]:
                continue
            if sun and sid == 1:
                continue                       # Asha never comes on a Sunday (her Sundays are off)
            w.writerow([sid, "%s %s:02" % (d, ws), 0])
            w.writerow([sid, "%s %s:00" % (d, we), 1])

sys.path.insert(0, APP)
try:
    SR = importlib.import_module("staff_register")
except Exception as e:                                                  # noqa: BLE001
    print("RED   the register did not import: %s: %s" % (type(e).__name__, e))
    print("0 of 1 green")
    sys.exit(1)
SR._today = lambda: "2026-11-01"
SR.init_db()
con = SR.get_db()
for sid, nm, g, *_ in STAFF:
    con.execute("INSERT INTO staff(staff_id,name,join_date,sunday_group,minutes_exempt,active) VALUES(?,?,?,?,?,1)",
                (sid, nm, "2026-01-01", g, 1 if sid == 4 else 0))
con.execute("UPDATE staff SET username='shavez' WHERE staff_id=3")
con.execute("UPDATE staff SET username='alisha' WHERE staff_id=5")
con.execute("INSERT INTO festival_day(fest_date,name,clinic_closed) VALUES(?,?,1)", (HOLIDAY, "Gandhi Jayanti (made-up)"))
con.execute("INSERT INTO festival_day(fest_date,name,clinic_closed) VALUES(?,?,0)", (FEST, "Festival (made-up)"))
for day in range(1, 32):
    d = "%s-%02d" % (YM, day)
    con.execute("INSERT INTO day_review(reg_date,state,maker_user,maker_ts,checker_user,checker_ts,status) "
                "VALUES(?,'exceptions','alisha','x','shavez','x','approved')", (d,))
con.execute("INSERT INTO present_request(reg_date,staff_id,req_user,req_ts,reason,status,decide_user,decide_ts,"
            "decide_note) VALUES('2026-10-24',2,'manoj','2026-10-24 09:00:00','made-up','approved','manoj','x',"
            "'past-day presence correction (D338)')")
con.execute("INSERT INTO daily_register(reg_date,staff_id,absence_type,leave_kind,leave_approved_by,maker_user,maker_ts)"
            " VALUES('2026-10-10',2,'leave_sanctioned','discretionary','bhawna','alisha','x')")
con.commit()
con.close()

app = SR.app
app.testing = True
c = SR.app.test_client()


def as_user(user, role):
    with c.session_transaction() as s:
        s["sr_user"] = user
        s["sr_role"] = role


def q(sql, *a):
    k = SR.get_db()
    try:
        return [dict(r) for r in k.execute(sql, a)]
    except sqlite3.OperationalError:
        return []                                  # the control: the staging tables do not exist
    finally:
        k.close()


def x(sql, *a):
    k = SR.get_db()
    try:
        k.execute(sql, a)
        k.commit()
    except sqlite3.OperationalError:
        pass                                       # the control: the staging tables do not exist
    finally:
        k.close()


def line():
    r = c.get("/register/attcorr/api/line")
    try:
        return r.status_code, json.loads(r.get_data(as_text=True) or "{}")
    except ValueError:
        return r.status_code, {}


T = "S650"
# ---- older behaviour, untouched (green on both files) ----
r = c.get("/register/health")
check("older", "the register's health door answers 200", r.status_code == 200, str(r.status_code))
as_user("manoj", "override")
r = c.get("/register/fixabsents?ym=%s" % YM)
check("older", "the owner's fix-absents desk still opens", r.status_code == 200, str(r.status_code))
r = c.get("/register/salary/flow/verify?ym=%s" % YM)
check("older", "the owner's Step 0 sheet still opens", r.status_code == 200, str(r.status_code))

AC = sys.modules.get("att_correction")
ok_mod = AC is not None and getattr(AC, "SR", None) is SR
check(T, "att_correction is installed into the running register", ok_mod)
if not ok_mod:
    class _N:                                  # the control: nothing installed -- every S650 check must come out red
        DECIDE_NOTE = "(not installed)"

        @staticmethod
        def day_list(con, ym):
            raise RuntimeError("not installed")

        @staticmethod
        def lock_blocker(ym):
            return "ERR not installed"
    AC = _N()

# ---- the day list ----
try:
    k = SR.get_db()
    blocks, feed = AC.day_list(k, YM)
    k.close()
except Exception as e:                                                  # noqa: BLE001
    blocks, feed = [], False
got = {b["sid"]: [(r["d"], r["off"]) for r in b["rows"]] for b in blocks}
want1 = [("2026-10-04", True), ("2026-10-07", False), ("2026-10-11", True), ("2026-10-15", False),
         ("2026-10-18", True), (FEST, False), ("2026-10-25", True)]
check(T, "Asha: her three weekday gaps and ALL four Sundays, each Sunday marked off (the salary's roster, not the "
         "register's)", got.get(1) == want1, str(got.get(1)))
check(T, "Bina: 03, 10, 18 (an on-duty Sunday); 24-10 left out (already corrected on the D338 door)",
      got.get(2) == [("2026-10-03", False), ("2026-10-10", False), ("2026-10-18", False)], str(got.get(2)))
check(T, "no day of the clinic holiday is listed, and Esha (punched every day) is not listed",
      HOLIDAY not in json.dumps(got) and 5 not in got, str(got))
N = sum(len(v) for v in got.values())
check(T, "Chetan 21-10 and Dev 22-10 listed; 12 days in all", got.get(3) == [("2026-10-21", False)]
      and got.get(4) == [("2026-10-22", False)] and N == 12, "N=%d" % N)

# ---- the sheet ----
as_user("alisha", "maker")
r = c.get("/register/attcorr/sheet?ym=%s" % YM)
s = r.get_data(as_text=True)
check(T, "reception opens the A4 sheet: 'Attendance correction sheet — October 2026', every listed name, the "
         "three tick columns, a signature per person and the three at the foot",
      r.status_code == 200 and "Attendance correction sheet &mdash; October 2026" in s
      and all(n in s for n in ("Asha Test", "Bina Test", "Chetan Test", "Dev Test")) and "Esha Test" not in s
      and s.count("&#9744;") == 3 * N and "Asha Test's signature" in s and "Shavez (checked)" in s
      and "Dr Manoj:" in s, str(r.status_code))
check(T, "the sheet carries no reason column and no in-time (the owner's ruling)",
      r.status_code == 200 and not any(w in s.lower() for w in ("wajah", "reason", "aane ka", "samay")))

st0, L0 = line()
check(T, "the lines' door before any entry: print and enter open with 12 days, Shavez's and the owner's closed",
      st0 == 200 and L0.get("print_open") == 12 and L0.get("enter_open") == 12 and L0.get("check_open") == 0
      and L0.get("owner_open") == 0 and "October" in (L0.get("print_text") or ""), str(L0))

# ---- reception enters ----
r = c.get("/register/attcorr/enter?ym=%s" % YM)
s = r.get_data(as_text=True)
check(T, "reception's screen: one Present/Leave/Absent choice per listed day and a Save button",
      r.status_code == 200 and s.count('type="radio"') == 3 * N and ">Save<" in s, str(r.status_code))
before_pr = len(q("SELECT * FROM present_request"))
before_dr = q("SELECT * FROM daily_register ORDER BY id")
form = {"ym": YM, "m_1_2026-10-07": "P", "m_1_2026-10-15": "L", "m_1_%s" % FEST: "L", "m_1_2026-10-11": "L",
        "m_2_2026-10-03": "A", "m_2_2026-10-10": "L", "m_2_2026-10-18": "P", "m_3_2026-10-21": "P",
        "m_4_2026-10-22": "A", "sign_1": "1", "sign_2": "1", "sign_3": "1", "sign_4": "1"}
r = c.post("/register/attcorr/enter", data=form)
loc = r.headers.get("Location", "")
check(T, "reception's Save returns to her screen with Saved", r.status_code in (302, 303) and "ok=1" in loc, loc)
r = c.get(loc or "/register/attcorr/enter")
s = r.get_data(as_text=True)
check(T, "her screen then shows '✓ Saved — <date> · <time> · 9 din'",
      "&#10003; Saved" in s and "9 din" in s)
check(T, "NOTHING COUNTS YET: no present request and no day-grid row was written by reception's Save",
      len(q("SELECT * FROM present_request")) == before_pr and q("SELECT * FROM daily_register ORDER BY id") == before_dr)
st1, L1 = line()
check(T, "after her Save: the print line closes; the enter line stays for the 3 blank Sundays; Shavez's and the "
         "owner's lines open", L1.get("print_open") == 0 and L1.get("enter_open") == 3 and L1.get("check_open") == 12
      and L1.get("owner_open") == 1, str(L1))

# ---- Shavez checks ----
as_user("shavez", "checker")
r = c.get("/register/attcorr/check?ym=%s" % YM)
s = r.get_data(as_text=True)
check(T, "Shavez's screen: his own block read-only ('Aapke apne din Sir dekhenge'), every other day changeable",
      r.status_code == 200 and "Aapke apne din Sir dekhenge" in s and 'name="m_3_' not in s
      and s.count('type="radio"') == 3 * (N - 1), str(r.status_code))
r = c.post("/register/attcorr/check", data={"ym": YM, "m_1_2026-10-07": "P", "m_1_2026-10-15": "L",
                                             "m_1_%s" % FEST: "L", "m_1_2026-10-11": "L", "m_2_2026-10-03": "A",
                                             "m_2_2026-10-10": "A", "m_2_2026-10-18": "P", "m_3_2026-10-21": "A",
                                             "m_4_2026-10-22": "A", "sign_1": "1", "sign_2": "1", "sign_4": "1"})
loc = r.headers.get("Location", "")
s = c.get(loc).get_data(as_text=True) if loc else ""
row10 = (q("SELECT * FROM attcorr_day WHERE reg_date='2026-10-10' AND staff_id=2") or [{}])[0]
row21 = (q("SELECT * FROM attcorr_day WHERE reg_date='2026-10-21' AND staff_id=3") or [{}])[0]
check(T, "Shavez's Save: Saved on screen; Bina 10-10 Leave -> Absent kept with his name; his own 21-10 NOT changed",
      "ok=1" in loc and "&#10003; Saved" in s and row10.get("mark") == "A" and row10.get("entered_mark") == "L"
      and row10.get("checked_by") == "shavez" and row21.get("mark") == "P", "%s %s" % (row10, row21))
r = c.get("/register/attcorr/check?ym=%s" % YM)
check(T, "his change is shown: 'Shavez ne badla · reception ne Leave bhara tha'",
      "Shavez ne badla" in r.get_data(as_text=True))
st2, L2 = line()
check(T, "after Shavez's Save his line closes and the enter line closes too", L2.get("check_open") == 0
      and L2.get("enter_open") == 0 and L2.get("owner_open") == 1, str(L2))
as_user("alisha", "maker")
r = c.post("/register/attcorr/enter", data=dict(form, **{"m_1_2026-10-07": "A"}))
check(T, "reception cannot Save over Shavez's check (she is told why)",
      "err=" in r.headers.get("Location", "") and
      (q("SELECT mark FROM attcorr_day WHERE reg_date='2026-10-07' AND staff_id=1") or [{}])[0].get("mark") == "P",
      r.headers.get("Location", ""))

# ---- who may open what ----
r1 = c.get("/register/attcorr/check?ym=%s" % YM)
r2 = c.get("/register/attcorr?ym=%s" % YM)
as_user("shavez", "checker")
r3 = c.get("/register/attcorr?ym=%s" % YM)
r4 = c.get("/register/attcorr/enter?ym=%s" % YM)
check(T, "reception cannot open Shavez's or the owner's page; Shavez cannot open the owner's; Shavez CAN open the "
         "entry screen (the fallback)", r1.status_code == 403 and r2.status_code == 403 and r3.status_code == 403
      and r4.status_code == 200, "%s %s %s %s" % (r1.status_code, r2.status_code, r3.status_code, r4.status_code))
with c.session_transaction() as sess:
    sess.clear()
st, Lx = line()
check(T, "the lines' door gives nothing to a visitor who is not signed in", st == 403 and Lx == {}, "%s %s" % (st, Lx))

# ---- the lock waits ----
try:
    msg = AC.lock_blocker(YM)
except Exception as e:                                                  # noqa: BLE001
    msg = "ERR %s" % e
check(T, "before the owner approves, the salary lock waits (with the page's full address)",
      "not approved yet" in msg and "https://followup.dr-manoj.in/register/attcorr?ym=2026-10" in msg, msg)
_orig_render = SR._render_salary
SR._render_salary = lambda ym, u, m="", msg_kind="block": "LOCKDESK:" + m
as_user("manoj", "override")
r = c.post("/register/salary/lock", data={"ym": YM})
check(T, "the Lock desk's own button refuses with that sentence (the view is wrapped)",
      "LOCKDESK:" in r.get_data(as_text=True) and "attendance corrections are not approved" in r.get_data(as_text=True)
      and not q("SELECT * FROM locked_run"), r.get_data(as_text=True)[:200])
SR._render_salary = _orig_render

# ---- the owner approves ----
r = c.get("/register/attcorr?ym=%s" % YM)
s = r.get_data(as_text=True)
check(T, "the owner's page (English): every day changeable, Shavez's correction named, the lock's wait said, "
         "Approve & save", r.status_code == 200 and s.count('type="radio"') == 3 * N
      and "Shavez corrected Leave to Absent" in s and "salary lock waits" in s and "Approve &amp; save" in s,
      str(r.status_code))
r = c.post("/register/attcorr", data={"ym": YM, "m_1_2026-10-07": "P", "m_1_2026-10-15": "L", "m_1_%s" % FEST: "L",
                                      "m_1_2026-10-11": "L", "m_2_2026-10-03": "A", "m_2_2026-10-10": "A",
                                      "m_2_2026-10-18": "P", "m_3_2026-10-21": "P", "m_4_2026-10-22": "L"})
loc = r.headers.get("Location", "")
s = c.get(loc).get_data(as_text=True) if loc else ""
check(T, "Approve & save: Saved on screen, 'October's attendance is updated'",
      "ok=1" in loc and "&#10003; Saved" in s and "attendance is updated" in s, loc)
pr = {(x["reg_date"], x["staff_id"]): x for x in q("SELECT * FROM present_request")}
a7, b18, c21 = pr.get(("2026-10-07", 1)), pr.get(("2026-10-18", 2)), pr.get(("2026-10-21", 3))
check(T, "Present = an approved present request at the duty start, D786's note (Asha 09:00, Bina's Sunday 09:00, "
         "Chetan 10:00)", all(x and x["status"] == "approved" and x["decide_note"] == AC.DECIDE_NOTE
                             for x in (a7, b18, c21)) and a7["req_ts"] == "2026-10-07 09:00:00"
      and b18["req_ts"] == "2026-10-18 09:00:00" and c21["req_ts"] == "2026-10-21 10:00:00", str((a7, b18, c21)))
k = SR.get_db()
md = SR.machine_day(k, "2026-10-07") or {}
k.close()
check(T, "the register's own reader now shows Asha present on 07-10 by request, 0 minutes late",
      (md.get(1) or {}).get("via_req") is True and (md.get(1) or {}).get("late") == 0, str(md.get(1)))
dr = {(x["reg_date"], x["staff_id"]): x for x in q("SELECT * FROM daily_register")}
l15, l20, l22 = dr.get(("2026-10-15", 1)), dr.get(("%s" % FEST, 1)), dr.get(("2026-10-22", 4))
check(T, "Leave = the day grid's own sanctioned-leave row (discretionary; 'festival' on the festival; by manoj)",
      l15 and l15["leave_kind"] == "discretionary" and l15["leave_approved_by"] == "manoj"
      and l15["absence_type"] == "leave_sanctioned" and l20 and l20["leave_kind"] == "festival"
      and l22 and l22["leave_kind"] == "discretionary", str((l15, l20, l22)))
b10 = dr.get(("2026-10-10", 2))
check(T, "Absent over a grid leave: Bina's 10-10 leave becomes absent; Absent with no grid row writes nothing (03-10)",
      b10 and b10["absence_type"] == "absent" and not b10["leave_kind"] and ("2026-10-03", 2) not in dr, str(b10))
check(T, "Leave on an off-duty Sunday writes nothing (Asha 11-10): an off day is never charged",
      ("2026-10-11", 1) not in dr and ("2026-10-11", 1) not in pr)
eng_ok = True
try:
    sys.path.insert(0, APP)
    import salary_engine as E                                           # noqa: PLC0415
    agg, _staff, covered = E.load_register(YM, db_path=os.environ["SR_DB_PATH"])
    eng_ok = covered and agg[1]["leave_dates"] == {"2026-10-15", FEST} and agg[4]["leave_dates"] == {"2026-10-22"} \
        and agg[2]["leave_dates"] == set()
    eng_detail = str({k2: v["leave_dates"] for k2, v in agg.items()})
except Exception as e:                                                  # noqa: BLE001
    eng_ok, eng_detail = False, "%s: %s" % (type(e).__name__, e)
check(T, "the salary engine's own register reader sees exactly those leaves (Asha 15, 20; Dev 22; Bina none)",
      eng_ok, eng_detail)
check(T, "after approval the lock no longer waits", AC.lock_blocker(YM) == "" if ok_mod else False)
st3, L3 = line()
check(T, "after approval every line is closed", all(L3.get(x) == 0 for x in ("print_open", "enter_open", "check_open",
                                                                              "owner_open")), str(L3))
as_user("shavez", "checker")
r = c.post("/register/attcorr/check", data={"ym": YM, "m_1_2026-10-07": "A"})
check(T, "after approval Shavez's Save is refused ('Sir approve kar chuke hain')",
      "err=" in r.headers.get("Location", "") and "Sir" in r.headers.get("Location", ""), r.headers.get("Location", ""))

# ---- changing a day after approval: the old write is undone, the new one written ----
as_user("manoj", "override")
r = c.post("/register/attcorr", data={"ym": YM, "m_1_2026-10-07": "A", "m_1_2026-10-15": "P", "m_1_%s" % FEST: "L",
                                      "m_1_2026-10-11": "L", "m_2_2026-10-03": "A", "m_2_2026-10-10": "L",
                                      "m_2_2026-10-18": "P", "m_3_2026-10-21": "P", "m_4_2026-10-22": "L"})
pr = {(x["reg_date"], x["staff_id"]): x for x in q("SELECT * FROM present_request")}
dr = {(x["reg_date"], x["staff_id"]): x for x in q("SELECT * FROM daily_register")}
b10 = dr.get(("2026-10-10", 2))
check(T, "re-approval: Asha 07 Present -> Absent removes its present request; 15 Leave -> Present removes the leave row "
         "and writes the request; Bina 10 back to Leave puts her grid row back, then writes the leave as sanctioned by "
         "the approver",
      ("2026-10-07", 1) not in pr and ("2026-10-15", 1) in pr and ("2026-10-15", 1) not in dr
      and b10 and b10["leave_kind"] == "discretionary" and b10["leave_approved_by"] == "manoj", str(b10))
check(T, "the D338 correction on 24-10 is never touched", ("2026-10-24", 2) in pr
      and "D338" in pr[("2026-10-24", 2)]["decide_note"])
x("UPDATE attcorr_day SET mark='A' WHERE reg_date='2026-10-21' AND staff_id=3")
check(T, "a tick that differs from what was written makes the lock wait again ('changed after you approved')",
      "changed after you approved" in AC.lock_blocker(YM))
x("UPDATE attcorr_day SET mark='P' WHERE reg_date='2026-10-21' AND staff_id=3")

# ---- a locked month; an unreadable punch feed; a month before the flow ----
k = SR.get_db()
k.execute("INSERT INTO locked_run(ym,total_payout,report_html,locked_by,locked_ts,status) "
          "VALUES(?,0,'','manoj','2026-11-03 10:00:00','locked')", (YM,))
k.commit()
k.close()
r = c.post("/register/attcorr", data={"ym": YM, "m_1_2026-10-07": "P"})
check(T, "a locked month cannot be changed (the owner is told to unlock first)",
      "err=" in r.headers.get("Location", "") and "locked" in r.headers.get("Location", ""), r.headers.get("Location", ""))
k = SR.get_db()
k.execute("DELETE FROM locked_run")
k.commit()
k.close()
os.rename(PUNCH, PUNCH + ".away")
r = c.get("/register/attcorr?ym=%s" % YM)
s = r.get_data(as_text=True)
r2 = c.post("/register/attcorr", data={"ym": YM, "m_1_2026-10-07": "P"})
lb = AC.lock_blocker(YM) if ok_mod else ""
os.rename(PUNCH + ".away", PUNCH)
check(T, "with the punch feed unreadable: the page says so and shows no list, Approve is refused, the lock waits",
      "cannot be read" in s and 'type="radio"' not in s and "err=" in r2.headers.get("Location", "")
      and "punch feed cannot be read" in lb, lb)
check(T, "September (before the flow) never makes the lock wait", AC.lock_blocker("2026-09") == "" if ok_mod else False)

# ---- the hook is the only change to the register ----
src = open(os.path.join(APP, "staff_register.py"), encoding="utf-8").read()
check(T, "staff_register.py carries the hook exactly once, just before __main__",
      src.count("_attcorr.install(app, sys.modules[__name__])") == 1
      and src.index("_attcorr.install(") < src.index('if __name__ == "__main__":'))

shutil.rmtree(TMP, ignore_errors=True)
s650 = [x for x in RES if x[0] == T]
older = [x for x in RES if x[0] != T]
if OLD:
    print("%d S650 check(s) red · %d older red · %d green" % (sum(1 for x in s650 if not x[2]),
                                                                      sum(1 for x in older if not x[2]),
                                                                      sum(1 for x in RES if x[2])))
else:
    print("%d of %d green" % (sum(1 for x in RES if x[2]), len(RES)))
