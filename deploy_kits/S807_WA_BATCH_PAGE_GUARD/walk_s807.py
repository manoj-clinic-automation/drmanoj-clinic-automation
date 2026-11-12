#!/usr/bin/python3
# walk_s807.py -- kit S807_WA_BATCH_PAGE_GUARD. Usage: walk_s807.py <dir holding portal/portal_followups.py> [--control]
# Everything is MADE UP: the list files (made-up names, mobiles built from a counter -- F-185), the page file and the sender
# are built at run time in a temp folder removed at the end. No live file is opened and NOTHING is sent: the sender is a
# recorder. The last line is "WALK OK n/n" or "WALK RED k of n"; with --control, "CONTROL: red ..." when it is red as it must be.
import datetime as dt, importlib, os, shutil, sys, tempfile, time
K = os.path.abspath(sys.argv[1])
CONTROL = "--control" in sys.argv
T = tempfile.mkdtemp(prefix="s807w.")
FUD, WAD = os.path.join(T, "followups"), os.path.join(T, "wa_portal")
os.makedirs(FUD); os.makedirs(WAD)
os.environ.update({"PORTAL_FOLLOWUP_DIR": FUD, "PORTAL_WA_DIR": WAD})
os.environ.pop("PORTAL_FOLLOWUP_GLOB", None); os.environ.pop("MYOP_AUTH_TOKEN", None)
sys.path.insert(0, os.path.join(K, "portal"))
sys.dont_write_bytecode = True
RES = []
def ck(name, ok, why=""):
    RES.append(bool(ok)); print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)) if (why and not ok) else ""))
def t(name, fn):
    try:
        r = fn()
        if isinstance(r, tuple):
            ck(name, r[0], r[1])
        else:
            ck(name, r)
    except Exception as e:  # noqa: BLE001
        ck(name, False, repr(e)[:170])

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
D = dt.datetime.now(IST).date()
day = lambda n: (D + dt.timedelta(days=n))                             # noqa: E731
M = lambda n: "9" + "%09d" % (80700 + n)                               # noqa: E731 -- made-up mobiles
PAGE = "<!doctype html><html><head><title>walk</title></head><body>\n<div class=\"wrap\"><h1>Follow-up WhatsApps</h1></div>\n<script>var X=1;</script></body></html>"
with open(os.path.join(WAD, "followups_page.html"), "w", encoding="utf-8") as fh:
    fh.write(PAGE)

import openpyxl
def make_list(name, fu_rows, proc_rows=(), age=0):
    """A made-up Staff_Action list in the tracker's shape. fu_rows: (name, mobile, od). age: seconds older than now."""
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Call Sheet"
    ws.append(["STAFF ACTION LIST %d" % D.year])
    ws.append(["1. FOLLOW-UP CALLS — made up"])
    ws.append(["S.N", "ID", "Name", "Mobile", "Diagnosis", "Due", "OD", "Status"])
    for i, (nm, mob, od) in enumerate(fu_rows, 1):
        ws.append([i, "W%d" % i, nm, mob, "made-up dx", "12-Nov", od, "to call"])
    ws.append(["2. PROCEDURE CALL-BACKS — made up"])
    ws.append(["S.N", "ID", "Name", "Mobile", "Diagnosis", "Due", "OD", "Status"])
    for i, (nm, mob, od) in enumerate(proc_rows, 1):
        ws.append([i, "P%d" % i, nm, mob, "made-up proc", "12-Nov", od, "call back"])
    p = os.path.join(FUD, name); wb.save(p)
    ts = time.time() - age; os.utime(p, (ts, ts))
    return p
def clear():
    for f in os.listdir(FUD):
        os.remove(os.path.join(FUD, f))
NAME = lambda d: "Staff_Action_Today_%s.xlsx" % d.isoformat()          # noqa: E731
FU = [("Walk Chand", M(1), -1), ("Walk Devi", M(2), 2), ("Walk Lal", M(3), 6), ("Walk Rani", M(4), 15), ("No Mobile", "", 1)]
PROC = [("Proc Singh", M(9), 0)]

m = importlib.import_module("portal_followups")

from flask import Flask, redirect
app = Flask("s807walk")
WHO = {"v": "manoj"}; CFG = {"PORTAL_WA_DRYRUN": "0", "MYOP_AUTH_TOKEN": "made-up-token"}; SENT = []
def guard(fn):
    import functools
    @functools.wraps(fn)
    def w(*a, **k):
        if not WHO["v"]:
            return redirect("/login")
        return fn(*a, **k)
    return w
FAIL = {"on": None, "how": ""}                                        # the made-up sender can be told to fail on one number
def wa_send(phone, template, values, who, tok, dry_run=True):
    SENT.append({"phone": phone, "template": template, "values": dict(values), "who": who, "dry": dry_run})
    if FAIL["on"] == phone:
        if FAIL["how"] == "none":
            return None
        raise RuntimeError("made-up sender failure")
    return {"ok": True, "mode": "DRY" if dry_run else "LIVE"}
try:
    m.register(app, guard, lambda: WHO["v"], lambda k, d="": CFG.get(k, d), wa_send)
except Exception as e:  # noqa: BLE001
    ck("R the module registers its three doors", False, repr(e)[:170])
cl = app.test_client()
U, UD, US = "/portal/wa/followups", "/portal/wa/followups/data", "/portal/wa/followups/send"
item = lambda nm, mob, tpl="drmanoj_followup_due", sn=1: {"sn": sn, "name": nm, "phone": mob, "template": tpl, "values": {"1": "REQUEST " + nm, "2": "a date from the request"}}  # noqa: E731
HD = lambda d=None: {"X-List-Date": (d or day(0)).isoformat()}       # noqa: E731 -- what the strip's script adds to the page's send request
def post(items, hd=None):
    return cl.post(US, json={"items": items}, headers=HD() if hd is None else hd)
DUE = "12 Nov %d" % D.year                                           # the list's own date text for every made-up row

# ---- A: the rule itself
t("A1 a list's day is the date in its own name", lambda: m.list_date("/x/" + NAME(day(0))) == day(0) and m.list_date("/x/Staff_Action_Today_2026-08-13.xlsx") == dt.date(2026, 8, 13))
t("A2 no date in the name, or a date that is not a date -> no day (the write time is not used)", lambda: m.list_date("/x/Staff_Action_Today.xlsx") is None and m.list_date("/x/Staff_Action_Today_2026-13-45.xlsx") is None and m.list_date("") is None)
def a2b():
    d = day(0).isoformat()
    bad = ["Staff_Action_Today_%s (1).xlsx" % d, "Staff_Action_Today_%s_old.xlsx" % d, "Staff_Action_Today_%s_from_2026-08-13.xlsx" % d, "Staff_Action_Today_1%s.xlsx" % d,
           "Staff_Action_Today_%s3.xlsx" % d, "Staff_Action_Today_2026-08-13_copy_%s.xlsx" % d, "staff_action_today_%s.xlsx" % d, "Staff_Action_Today_%s.XLSX" % d, "~$Staff_Action_Today_%s.xlsx" % d]
    got = [n for n in bad if m.list_date("/x/" + n) is not None]
    return got == [], got
t("A2b only the exact name Staff_Action_Today_YYYY-MM-DD.xlsx has a day: a copy, an '_old', two dates, extra digits -> no day", a2b)
t("A2c the day comes from the file's NAME, never from its folder", lambda: m.list_date("/x/%s/Staff_Action_Today_2026-08-13.xlsx" % day(0).isoformat()) == dt.date(2026, 8, 13) and m.list_date("/x/Staff_Action_Today_%s.xlsx/list.xlsx" % day(0).isoformat()) is None)
def a3():
    clear(); p = make_list(NAME(day(0)), FU); s = m.list_state(p)
    return s["fresh"] is True and s["why"] == "" and s["file_date"] == day(0).isoformat() and s["today"] == day(0).isoformat(), s
t("A3 today's list is fresh", a3)
def a4():
    clear(); p = make_list(NAME(day(-1)), FU); s = m.list_state(p)
    y = day(-1); n = day(0)
    return (s["fresh"] is False and "%d %s %d" % (y.day, y.strftime("%b"), y.year) in s["why"] and "%d %s %d" % (n.day, n.strftime("%b"), n.year) in s["why"] and "not today's" in s["why"]), s
t("A4 yesterday's list is NOT fresh, and the reason names both dates", a4)
def a5():
    clear(); p = make_list(NAME(day(1)), FU); s = m.list_state(p)
    return s["fresh"] is False and "not today's" in s["why"], s
t("A5 a list dated tomorrow is NOT fresh either", a5)
def a6():
    clear(); p = make_list("Staff_Action_Today.xlsx", FU); s = m.list_state(p); s0 = m.list_state(None)
    return s["fresh"] is False and "not named for a day" in s["why"] and s0["fresh"] is False and "No follow-up list" in s0["why"], (s, s0)
t("A6 a list with no date in its name, and no list at all: NOT fresh, each with its own reason", a6)
def a7():
    clear(); p = make_list(NAME(day(0)), FU); real = m.today_ist
    try:
        m.today_ist = lambda: day(1)
        s = m.list_state(p)
    finally:
        m.today_ist = real
    return s["fresh"] is False and m.list_state(p)["fresh"] is True, s
t("A7 the day turns (IST): today's list stops being fresh the moment the date changes", a7)
def a8():
    want = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=5, minutes=30); old = os.environ.get("TZ"); got = []
    try:
        for z in ("Pacific/Kiritimati", "Pacific/Pago_Pago", "UTC"):     # +14 and -11: one of the two is always on another date than IST
            os.environ["TZ"] = z; time.tzset(); got.append(m.today_ist())
    finally:
        if old is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = old
        time.tzset()
    return got == [want.date()] * 3, (got, want.date())
t("A8 the day is read in IST whatever the server's own zone (tried at +14, -11 and UTC)", a8)

# ---- B: the data door
def b1():
    clear(); make_list(NAME(day(0)), FU, PROC); CFG["PORTAL_WA_DRYRUN"] = "0"
    j = cl.get(UD).get_json(); rows = j["sections"][0]["rows"]
    return (j["ok"] and j["mode"] == "LIVE" and j["dry"] is False and j["list"]["fresh"] and len(j["sections"]) == 2 and len(rows) == 5
            and [r["sendable"] for r in rows] == [True, True, True, True, False] and j["sections"][1]["rows"][0]["sendable"] is False), j
t("B1 today's list: the rows as before (4 sendable, 1 without a mobile, the procedure row not sendable), LIVE named", b1)
def b2():
    CFG["PORTAL_WA_DRYRUN"] = "1"; j = cl.get(UD).get_json(); CFG["PORTAL_WA_DRYRUN"] = "0"
    return j["ok"] and j["mode"] == "TEST" and j["dry"] is True, j
t("B2 with the test switch on the data says TEST", b2)
def b3():
    rows = cl.get(UD).get_json()["sections"][0]["rows"]
    return ([r["template"] for r in rows[:4]] == ["drmanoj_followup_tomorrow", "drmanoj_followup_due", "drmanoj_followup_missed", "drmanoj_followup_dropout"]
            and m.values_for("drmanoj_followup_dropout", rows[3]) == {"1": "Walk Rani", "2": rows[3]["date_fmt"], "3": "15"} and rows[0]["phone"] == M(1) and rows[0]["phone_mask"].endswith(M(1)[-4:])
            and rows[0]["date_fmt"] == DUE), rows
t("B3 the template ladder and the values are unchanged", b3)
def b4():
    clear(); make_list("Staff_Action_Today_2026-08-13.xlsx", FU, PROC)
    r = cl.get(UD); j = r.get_json()
    return (r.status_code == 200 and j["ok"] is False and j["stale"] is True and "13 Aug 2026" in j["error"] and "sections" not in j and M(1) not in r.get_data(as_text=True)
            and "Walk Chand" not in r.get_data(as_text=True)), j
t("B4 the list of 13-Aug: refused in plain words, and NOT ONE row of it is given to the page", b4)
def b5():
    clear(); r = cl.get(UD); j = r.get_json()
    return r.status_code == 200 and j["ok"] is False and "No follow-up list" in j["error"], j
t("B5 no list on the server: refused in plain words", b5)
def b6():
    clear(); make_list(NAME(day(0)), FU, age=600); make_list(NAME(day(-3)), FU, age=0)
    j = cl.get(UD).get_json()
    return j["ok"] is False and j["stale"] is True, j
t("B6 an older list written LAST wins the pick as before -- and is refused (the safe direction)", b6)
def b7():
    clear(); make_list("Staff_Action_Today_%s_old.xlsx" % day(0).isoformat(), FU); SENT.clear()
    j = cl.get(UD).get_json(); r = post([item("Walk Chand", M(1))])
    return j["ok"] is False and j["stale"] is True and "not named for a day" in j["error"] and r.status_code == 409 and SENT == [], (j, r.status_code)
t("B7 a file named '..._<today>_old.xlsx': refused by the data door and by the send door", b7)

# ---- C: the send door
def c1():
    clear(); make_list("Staff_Action_Today_2026-08-13.xlsx", FU, PROC); SENT.clear()
    r = post([item("Walk Chand", M(1)), item("Walk Devi", M(2), sn=2)], HD(dt.date(2026, 8, 13))); j = r.get_json()
    return r.status_code == 409 and j["ok"] is False and j["stale"] is True and "13 Aug 2026" in j["error"] and SENT == [], (r.status_code, j, SENT)
t("C1 the list of 13-Aug: Send selected is refused (409) and the sender is NEVER called", c1)
def c2():
    clear(); SENT.clear(); r = post([item("Walk Chand", M(1))])
    return r.status_code == 409 and r.get_json()["ok"] is False and SENT == [], r.status_code
t("C2 no list on the server: refused, the sender never called", c2)
def c3():
    clear(); make_list(NAME(day(0)), FU, PROC); SENT.clear(); CFG["PORTAL_WA_DRYRUN"] = "0"
    r = post([item("Walk Chand", M(1), "drmanoj_followup_tomorrow"), item("Walk Devi", M(2), sn=2)]); j = r.get_json()
    return (r.status_code == 200 and j["ok"] and j["sent"] == 2 and j["total"] == 2 and j["dry"] is False and len(SENT) == 2
            and SENT[0] == {"phone": M(1), "template": "drmanoj_followup_tomorrow", "values": {"1": "Walk Chand", "2": DUE}, "who": "manoj", "dry": False}
            and SENT[1] == {"phone": M(2), "template": "drmanoj_followup_due", "values": {"1": "Walk Devi", "2": DUE}, "who": "manoj", "dry": False}
            and sorted(j["results"][0]) == ["error", "mode", "name", "ok", "sn"]), (j, SENT)
t("C3 today's list: two ticked rows go to the one sender -- the number, the name and the date are the LIST's (what the request says about them is not used)", c3)
def c3b():
    SENT.clear(); j = post([item("Walk Rani", M(4), "drmanoj_followup_dropout", sn=4), item("Walk Lal", M(3), "drmanoj_post_visit", sn=3)]).get_json()
    return j["sent"] == 2 and SENT[0]["values"] == {"1": "Walk Rani", "2": DUE, "3": "15"} and SENT[1]["values"] == {"1": "Walk Lal"}, SENT
t("C3b the template he picks for a row is kept (the page's choice box); its words are built from the list's row", c3b)
def c4():
    SENT.clear()
    r = post([item("Stranger", M(50)), item("Proc Singh", M(9), sn=1), item("Walk Lal", M(3), sn=3), item("No Mobile", "", sn=5)]); j = r.get_json()
    res = j["results"]
    return (r.status_code == 200 and j["sent"] == 1 and j["total"] == 4 and [s["phone"] for s in SENT] == [M(3)] and res[0]["ok"] is False and res[0]["mode"] == "REFUSED"
            and "not on today's list" in res[0]["error"] and res[1]["ok"] is False and res[3]["ok"] is False and res[2]["ok"] is True), (j, SENT)
t("C4 a row that is not a sendable row of today's list (a stranger, the procedure row, a blank) is refused; the good row beside it goes", c4)
def c5():
    SENT.clear()
    bad = [item("Walk Chand", M(2)), item("Walk Devi", M(1), sn=2), item("Somebody Else", M(1)), item("Walk Chand", M(1), sn=2), item("walk chand", M(1)), item("Walk Chand ", M(1))]
    j = post(bad).get_json()
    return j["sent"] == 0 and SENT == [] and all(x["mode"] == "REFUSED" for x in j["results"]), (j, SENT)
t("C5 the S.N, the name and the number must ALL be the list's row: a list number under another name or another S.N is refused", c5)
def c6():
    SENT.clear(); n = M(1)
    forms = ["+91 " + n[:5] + " " + n[5:], "91" + n, "0" + n, n[:5] + " " + n[5:], n[:5] + "-" + n[5:], " " + n, n + "\n", "+" + n, n + "x", int(n), float(n), [n], {"n": n}, list(n), None, True, "x" * 5000 + n]
    j = post([dict(item("Walk Chand", M(1)), phone=f) for f in forms]).get_json()
    return j["sent"] == 0 and SENT == [] and j["total"] == len(forms), (j["sent"], SENT[:2])
t("C6 the number must be the list's own ten digits as text: spaces, dashes, +91, a number type, a list, a long string -- all refused, none handed to the sender", c6)
def c6b():
    SENT.clear(); j = post([dict(item("Walk Chand", M(1)), sn=s) for s in ("1", 1.0, True, None, [1])]).get_json()
    j2 = post([item("Walk Chand", M(1), tpl) for tpl in ("welcome_template", "appointment_reminder_1day_ortho", "any_template_at_all", "", None, ["drmanoj_followup_due"], 7)]).get_json()
    return j["sent"] == 0 and j2["sent"] == 0 and SENT == [] and all("not a follow-up message" in x["error"] for x in j2["results"]), (j, j2)
t("C6b the S.N must be the list's number; a template outside the five follow-up messages is refused", c6b)
def c7():
    SENT.clear(); r = post([]); r2 = cl.post(US, json={}, headers=HD())
    return r.status_code == 400 and r2.status_code == 400 and r.get_json()["error"] == "no rows selected" and SENT == [], (r.status_code, r2.status_code)
t("C7 nothing ticked: 400 'no rows selected' as before", c7)
def c8():
    clear(); p = os.path.join(FUD, NAME(day(0)))
    with open(p, "wb") as fh:
        fh.write(b"this is not a spreadsheet")
    SENT.clear(); r = post([item("Walk Chand", M(1))]); j = r.get_json()
    r2 = cl.get(UD)
    return r.status_code == 409 and j["ok"] is False and "nothing was sent" in j["error"] and SENT == [] and r2.status_code == 500 and r2.get_json()["ok"] is False, (r.status_code, j)
t("C8 today's list unreadable: nothing is sent (409, said plainly); the data door fails as before", c8)
def c9():
    clear(); make_list(NAME(day(0)), FU); SENT.clear(); CFG["PORTAL_WA_DRYRUN"] = "1"
    j = post([item("Walk Chand", M(1))]).get_json(); CFG["PORTAL_WA_DRYRUN"] = "0"
    return j["sent"] == 1 and j["dry"] is True and SENT[0]["dry"] is True, (j, SENT)
t("C9 with the test switch on, the sender is told it is a test (as before)", c9)
def c10():
    SENT.clear(); r = post(["not a row", None, 7, item("Walk Devi", M(2), sn=2)]); j = r.get_json()
    return r.status_code == 200 and j["sent"] == 1 and [s["phone"] for s in SENT] == [M(2)], (r.status_code, j)
t("C10 a broken item in the request does not break the door; the good row goes", c10)
def c11():
    real = m.today_ist; SENT.clear()
    try:
        m.today_ist = lambda: day(1)
        r = post([item("Walk Chand", M(1))])
    finally:
        m.today_ist = real
    return r.status_code == 409 and SENT == [], r.status_code
t("C11 past midnight (IST) the page's list is yesterday's: Send selected is refused", c11)
def c12():
    SENT.clear(); a = cl.post(US, json={"items": [item("Walk Chand", M(1))]}); b = post([item("Walk Chand", M(1))], HD(day(-1))); c = post([item("Walk Chand", M(1))], {"X-List-Date": ""})
    return (a.status_code, b.status_code, c.status_code) == (409, 409, 409) and "Reload the page" in a.get_json()["error"] and a.get_json()["ok"] is False and SENT == [], (a.status_code, b.status_code, c.status_code, SENT)
t("C12 a page that was NOT opened on today's list (no list date in its request, or yesterday's) is told to reload; nothing is sent", c12)
def c13():
    clear(); make_list(NAME(day(-1)), FU, age=60); make_list(NAME(day(0)), [("Walk Chand", M(1), 0), ("Walk Naya", M(7), 1)]); SENT.clear()
    r = post([item("Walk Chand", M(1), "drmanoj_followup_tomorrow"), item("Walk Devi", M(2), sn=2)], HD(day(-1)))
    return r.status_code == 409 and SENT == [], (r.status_code, SENT)
t("C13 a page left open since yesterday, a patient still on today's list: refused whole (its old words cannot go)", c13)
def c14():
    clear(); make_list(NAME(day(0)), FU); SENT.clear(); FAIL["on"] = M(2); FAIL["how"] = "raise"
    try:
        r = post([item("Walk Chand", M(1)), item("Walk Devi", M(2), sn=2), item("Walk Lal", M(3), sn=3), item("Walk Rani", M(4), sn=4)]); j = r.get_json()
    finally:
        FAIL["on"] = None
    res = j["results"]
    return (r.status_code == 200 and j["ok"] is True and j["sent"] == 1 and j["total"] == 4 and [s["phone"] for s in SENT] == [M(1), M(2)] and res[0]["ok"] is True
            and res[1]["mode"] == "FAILED" and "not tried again" in res[1]["error"] and res[2]["mode"] == "NOT SENT" and res[3]["mode"] == "NOT SENT"), (r.status_code, j, SENT)
t("C14 the sender fails on row 2 of 4: row 1 stays sent, row 2 is NOT tried again, rows 3 and 4 are not sent, and the page is told row by row", c14)
def c15():
    SENT.clear(); FAIL["on"] = M(1); FAIL["how"] = "none"
    try:
        r = post([item("Walk Chand", M(1)), item("Walk Devi", M(2), sn=2)]); j = r.get_json()
    finally:
        FAIL["on"] = None
    return r.status_code == 200 and j["sent"] == 0 and len(SENT) == 1 and j["results"][0]["mode"] == "FAILED" and j["results"][1]["mode"] == "NOT SENT", (r.status_code, j)
t("C15 the sender gives no answer: treated as a failure, the batch stops", c15)
def c16():
    clear(); make_list(NAME(day(0)), [("Walk Pita", M(5), 1), ("Walk Putra", M(5), 1), ("Walk Twin", M(6), 1), ("Walk Twin", M(6), 4)]); SENT.clear()
    j = post([item("Walk Pita", M(5)), item("Walk Putra", M(5), sn=2), item("Walk Twin", M(6), sn=3), item("Walk Twin", M(6), sn=4)]).get_json()
    return j["sent"] == 4 and [s["values"]["1"] for s in SENT] == ["Walk Pita", "Walk Putra", "Walk Twin", "Walk Twin"], (j, SENT)
t("C16 two patients on one mobile each get their own message, as before", c16)
def c17():
    rows = m.sendable_rows({"sections": [{"rows": [{"sn": 1, "name": "A", "phone": M(1), "sendable": True, "od": 1}, {"sn": 1, "name": "A", "phone": M(1), "sendable": True, "od": 9}]},
                                         {"rows": [{"sn": 2, "name": "B", "phone": M(2), "sendable": True, "od": 1}, {"sn": 2, "name": "B", "phone": M(2), "sendable": True, "od": 1}, {"sn": 3, "name": "C", "phone": M(3), "sendable": False}]}]})
    return rows[(1, "A", M(1))] is None and rows[(2, "B", M(2))]["od"] == 1 and (3, "C", M(3)) not in rows and m.match_row({"sn": 1, "name": "A", "phone": M(1)}, rows) is None, rows
t("C17 two different rows with the same S.N, name and number cannot be told apart: refused", c17)

# ---- D: the page says LIVE or TEST on its face
def strip(html):
    a = html.index("<!--s807-->"); b = html.index("<!--/s807-->", a) + len("<!--/s807-->")
    return html[a:b], html[:a] + html[b:]
def d1():
    clear(); make_list(NAME(day(0)), FU); CFG["PORTAL_WA_DRYRUN"] = "0"
    r = cl.get(U); h = r.get_data(as_text=True); ban, rest = strip(h)
    n = day(0)
    return (r.status_code == 200 and rest == PAGE and h.index("<body>") + len("<body>") == h.index("<!--s807-->") and 'data-mode="LIVE"' in ban and ">LIVE<" in ban
            and "Today's list (%d %s %d)" % (n.day, n.strftime("%b"), n.year) in ban.replace("&#x27;", "'") and "A message sent from this page goes to the patient" in ban and r.headers.get("Cache-Control") == "no-store"
            and '"X-List-Date"' in ban and '"%s"' % n.isoformat() in ban), ban
t("D1 today's list, live: a strip straight after <body> says LIVE and the list's date, and gives the page the list's date; the page file's own text is untouched", d1)
def d2():
    CFG["PORTAL_WA_DRYRUN"] = "1"; ban, rest = strip(cl.get(U).get_data(as_text=True)); CFG["PORTAL_WA_DRYRUN"] = "0"
    return 'data-mode="TEST"' in ban and ">TEST<" in ban and "nothing goes to any patient" in ban and ">LIVE<" not in ban and rest == PAGE, ban
t("D2 with the test switch on the strip says TEST", d2)
def d3():
    clear(); make_list("Staff_Action_Today_2026-08-13.xlsx", FU)
    ban, rest = strip(cl.get(U).get_data(as_text=True))
    return ('data-fresh="0"' in ban and "13 Aug 2026" in ban and "not today" in ban and ">LIVE<" in ban and rest == PAGE and "/portal/messages" in ban and "goes to the patient" not in ban
            and "<script" not in ban and "X-List-Date" not in ban), ban
t("D3 the list of 13-Aug: the strip says it is not today's and that nothing can be sent (and does not also say a message goes); it gives the page no list date", d3)
def d4():
    clear(); ban, rest = strip(cl.get(U).get_data(as_text=True))
    return 'data-fresh="0"' in ban and "No follow-up list" in ban and rest == PAGE and "<script" not in ban, ban
t("D4 no list on the server: the strip says so", d4)
def d5():
    return m.with_banner("<p>no body tag</p>", m.list_state(None), True).startswith('<!--s807--><div id="s807-banner"') and m.with_banner('<html><BODY class="x">hi</BODY>', m.list_state(None), True).startswith('<html><BODY class="x"><!--s807--><div id="s807-banner"')
t("D5 a page file with no <body> tag gets the strip in front; a <BODY class=..> tag is found", d5)
def d6():
    b = m.banner_html({"fresh": False, "why": "<script>alert(1)</script> & \"co\""}, False)
    return "<script>" not in b and "&lt;script&gt;" in b and "&amp; &quot;co&quot;" in b, b
t("D6 the strip's words are escaped", d6)
def d7():
    os.remove(os.path.join(WAD, "followups_page.html")); r = cl.get(U)
    with open(os.path.join(WAD, "followups_page.html"), "w", encoding="utf-8") as fh:
        fh.write(PAGE)
    return r.status_code == 500 and "not installed" in r.get_data(as_text=True), r.status_code
t("D7 the page file missing: 500 'not installed' as before", d7)

# ---- E: the doors stay closed without a login
def e1():
    clear(); make_list(NAME(day(0)), FU); SENT.clear(); WHO["v"] = ""
    try:
        a = (cl.get(U).status_code, cl.get(UD).status_code, post([item("Walk Chand", M(1))]).status_code)
    finally:
        WHO["v"] = "manoj"
    return a == (302, 302, 302) and SENT == [], (a, SENT)
t("E1 without a login all three doors answer 302 and nothing is sent", e1)
t("E2 the version reads S807", lambda: (m.VERSION.startswith("S807"), getattr(m, "VERSION", None)))
def e3():
    src = open(os.path.join(K, "portal", "portal_followups.py"), encoding="utf-8").read()
    return ("urllib" not in src and "http.client" not in src and "requests" not in src and "socket" not in src and src.count("wa_send(") == 1
            and "open(" in src and '"w"' not in src and "'w'" not in src and ".write(" not in src and "os.remove" not in src and "getmtime" in src), ""
t("E3 the file still holds no network code of its own, ONE call of the one sender, and writes no file", e3)

clear()
ck("F1 the walk left only its own folders", sorted(os.listdir(T)) == ["followups", "wa_portal"] and os.listdir(FUD) == [] and os.listdir(WAD) == ["followups_page.html"], sorted(os.listdir(T)))
shutil.rmtree(T, ignore_errors=True)
bad = RES.count(False)
if CONTROL:
    print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
else:
    print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))
