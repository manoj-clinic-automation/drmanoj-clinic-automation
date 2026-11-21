"""walk_s913.py -- kit S913_PROCROOM_NEXT_DAY: the morning screen's day choice and its after-Save step, on made-up days.
usage: python walk_s913.py <dir holding procroom.py>      (no database: the screen's readers are replaced by made-up ones)
Prints one line per check and last 'WALK n/N'. Run on the live file it must go red (the control)."""
import importlib.util, os, sys, types

SRC = sys.argv[1]
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.abspath(os.path.dirname(__file__))]   # F-1441
spec = importlib.util.spec_from_file_location("procroom_w", os.path.join(SRC, "procroom.py"))
PR = importlib.util.module_from_spec(spec); spec.loader.exec_module(PR)
from flask import Flask, get_flashed_messages  # noqa: E402

app = Flask("w"); app.secret_key = "walk"
app.add_url_rule("/procroom/morning", "s637_morning", lambda: "")
app.add_url_rule("/bills", "bills_list", lambda: "")
SEEN = {}
class FakeDB:
    def commit(self): SEEN["commit"] = SEEN.get("commit", 0) + 1
    def rollback(self): SEEN["rollback"] = SEEN.get("rollback", 0) + 1
AR = types.SimpleNamespace(get_db=lambda: FakeDB(), page=lambda tpl, **kw: kw["v"]["day"], _flow=lambda *a: "",
                           app=types.SimpleNamespace(view_functions={}))
PR.AR = AR
PR._staff_gate = lambda: None
PR._today = lambda: __import__("datetime").date(2026, 11, 21)
PR.morning_from = lambda db: "2026-10-01"
PR.morning_view = lambda db, day: {"day": day}
OPEN = {"v": []}
PR.open_days = lambda db: OPEN["v"]
SAVE = {"raise": None}
def fake_save(db, day, form, who=None):
    if SAVE["raise"]:
        raise ValueError(SAVE["raise"])
    if OPEN["v"] is not None and SAVE.get("clears", True):
        OPEN["v"] = [o for o in OPEN["v"] if o["day"] != day]
    return "Save ho gaya — 1 slip, 4 cheezein."
PR.save_morning = fake_save
R = []
def check(name, ok, why=""):
    R.append(bool(ok)); print(("ok   " if ok else "FAIL ") + name + ((" -- " + str(why)) if (why and not ok) else ""))
def page(q=""):
    with app.test_request_context("/procroom/morning" + q):
        return PR.morning_page()
def save(day):
    with app.test_request_context("/procroom/morning/save", method="POST", data={"day": day}):
        r = PR.morning_save()
        return r.headers.get("Location", ""), list(get_flashed_messages())

OPEN["v"] = [{"day": "2026-11-13", "n": 6}, {"day": "2026-11-20", "n": 1}]
check("P1 opened with no day: the oldest waiting day (13-11)", page() == "2026-11-13", page())
check("P2 a day asked for is the day shown", page("?day=2026-11-20") == "2026-11-20")
OPEN["v"] = []
check("P3 nothing waiting: yesterday, as before", page() == "2026-11-20", page())
OPEN["v"] = None
check("P4 the list unreadable: yesterday, as before", page() == "2026-11-20", page())

OPEN["v"] = [{"day": "2026-11-13", "n": 6}, {"day": "2026-11-20", "n": 1}]
loc, fl = save("2026-11-20")
check("S1 Save finishes 20-11: goes on to 13-11", "day=2026-11-13" in loc, loc)
check("S2 ... and says so", fl and "Ab 13-11" in fl[0] and "Save ho gaya" in fl[0], fl)
loc, fl = save("2026-11-13")
check("S3 the last day done: stays, 'sab din poore'", "day=2026-11-13" in loc and fl and "sab din poore" in fl[0], (loc, fl))
OPEN["v"] = [{"day": "2026-11-13", "n": 6}]; SAVE["clears"] = False
loc, fl = save("2026-11-13")
check("S4 a day still waiting after Save: the same day", "day=2026-11-13" in loc and fl and "Ab " not in fl[0], (loc, fl))
SAVE["raise"] = "Slip 1529: Fibrecast — size chunein."
loc, fl = save("2026-11-13")
check("S5 a refused Save: the same day, the reason, nothing saved", "day=2026-11-13" in loc and fl and "Kuch save nahi hua" in fl[0]
      and SEEN.get("rollback"), (loc, fl))
SAVE["raise"] = None; SAVE["clears"] = True; OPEN["v"] = None
loc, fl = save("2026-11-20")
check("S6 the list unreadable after Save: the same day, the Save's own words", "day=2026-11-20" in loc and fl == ["Save ho gaya — 1 slip, 4 cheezein."], (loc, fl))
print("WALK %d/%d" % (sum(R), len(R)))
