#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s868.py -- kit S868_DOCTOR_OFF_DAY (the parent, S480, 18-Nov-2026). A walk on a MADE-UP root (an empty sqlite built by
the code's own ensure(), made-up CSVs with no real patient): the empty consultation report on a not-sitting day; the owner's
not-sitting page through Flask for every role (F-1445); the readers' own queries; the Clinic PCs page's two words.
    python3 walk_s868.py <code_dir> <work_dir>        last line "WALK n/m"."""
import datetime as dt
import json
import os
import shutil
import sqlite3
import sys

CODE, WORK = sys.argv[1:3]
try:
    _ME = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _ME = None
sys.path[:] = [p for p in sys.path if not _ME or os.path.abspath(p or ".") != _ME]     # F-1441
sys.path[:0] = [CODE]
if os.path.isdir(WORK):
    shutil.rmtree(WORK)
os.makedirs(WORK)
RES = []


def ok(name, cond, extra=""):
    RES.append(bool(cond))
    print("%s  %s%s" % ("PASS" if cond else "FAIL", name, ("  -- " + str(extra)[:240]) if extra else ""))


DB = os.path.join(WORK, "finance.db")
os.environ.update(FINANCE_DB=DB, DOCTERZ_EXPORT_STORE=os.path.join(WORK, "store"), LAB_BEAT=os.path.join(WORK, "beat.json"),
                  LAB_SNAP_INDEX=os.path.join(WORK, "snaps.json"), PC_KITS_ROOT=os.path.join(WORK, "kits"),
                  PC_KIT_CODES=os.path.join(WORK, "codes.json"), PC_KIT_LOG=os.path.join(WORK, "log.txt"))
os.makedirs(os.path.join(WORK, "kits"))
try:
    import docterz_pickup as DP                                          # noqa: E402
    import off_days as OD                                                # noqa: E402
except Exception as ex:                                                  # noqa: BLE001 -- the control (no off_days.py) is red
    print("FAIL  import: %s" % ex)
    print("WALK 0/34")
    sys.exit(1)
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
DP.ensure(con)
con.execute("CREATE TABLE IF NOT EXISTS slip (id INTEGER PRIMARY KEY, series TEXT, day TEXT, state TEXT)")
con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT)")
for i in range(3):
    con.execute("INSERT INTO slip (series, day, state) VALUES ('opd','2031-03-19','ok')")       # a day he worked (made-up)
con.execute("INSERT INTO slip (series, day, state) VALUES ('xp','2031-03-18','ok')")           # an X-ray slip only
con.commit()
HEAD = "Consultation Date,Patient Name,Mode Of Payment,Amount\n"
EMPTY = (HEAD + "Walk Clinic (made up),,,\n").encode()
REAL = (HEAD + "18-03-2031,Made Up One,Cash,500\n18-03-2031,Made Up Two,UPI,500\n").encode()
N = [0]


def f(ist, name="consultation_report.csv"):
    """A made-up Drive file: its modifiedTime is the IST moment given, in UTC as Drive writes it."""
    N[0] += 1
    t = (ist - dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S.000Z") if ist else ""
    return {"id": "walk-file-%d" % N[0], "name": name, "modifiedTime": t}


def row(day, kind="consultation"):
    return con.execute("SELECT * FROM docterz_export WHERE kind=? AND business_date=? AND status='current' ORDER BY id DESC LIMIT 1",
                       (kind, day)).fetchone()


def off(day):
    try:
        return bool(con.execute("SELECT 1 FROM clinic_off_day WHERE day=?", (day,)).fetchone())
    except sqlite3.Error:
        return False


# ---- the pickup: an empty consultation report
k, d, n, st, note = DP.take(con, f(dt.datetime(2031, 3, 18, 20, 30)), EMPTY)          # Tuesday 18-Mar-2031, evening
r = row("2031-03-18")
ok("P1 an empty report on a day with no OPD slip: that day's CURRENT report, 0 rows", st == "current" and d == "2031-03-18" and r is not None and r["rows"] == 0, (st, d, note))
ok("P2 ... nothing kept on disk (reception's PC never gets an empty file back)", r is not None and r["stored"] == "" and not os.path.isdir(os.path.join(WORK, "store", "consultation")))
ok("P3 ... and the day is marked not sitting by the server", off("2031-03-18") and "not sitting" in (note or ""))
k, d, n, st, note = DP.take(con, f(dt.datetime(2031, 3, 19, 20, 30)), EMPTY)          # Wednesday 19-Mar: 3 OPD slips
ok("P4 an empty report on a day WITH OPD slips: set aside and said", st == "quarantined" and d == "2031-03-19" and "EMPTY" in note and row("2031-03-19") is None, (st, note))
ok("P5 ... the day not marked", not off("2031-03-19"))
k, d, n, st, note = DP.take(con, f(dt.datetime(2031, 3, 18, 21, 10)), REAL)           # he did sit on the 18th after all
r = row("2031-03-18")
ok("P6 a real report of that day replaces the empty one", st == "current" and r is not None and r["rows"] == 2, (st, note))
ok("P7 ... and clears the not-sitting mark", not off("2031-03-18"))
k, d, n, st, note = DP.take(con, f(dt.datetime(2031, 3, 18, 21, 40)), EMPTY.replace(b"made up", b"made up again"))
ok("P8 an empty report after a real one never replaces it, and is not shouted (review 5)", st == "superseded" and row("2031-03-18")["rows"] == 2, (st, note))
k, d, n, st, note = DP.take(con, f(dt.datetime(2031, 3, 21, 10, 20)), EMPTY.replace(b"made up", b"made up morning"))
ok("P9 an empty report exported before 13:00 belongs to the working day before (Thu 20-Mar)", d == "2031-03-20" and st == "current", (st, d))
k, d, n, st, note = DP.take(con, f(None), EMPTY.replace(b"made up", b"no time"))
ok("P10 an empty report with no export time: set aside, as before", st == "quarantined" and note == "no date in the file", (st, note))
# owner_lines: the morning after a not-sitting day says nothing; the old 'no date' empties are not shouted
lines = DP.owner_lines(con, dt.datetime(2031, 3, 21, 11, 0))
ok("P11 his money page: no 'No Docterz export' line for a not-sitting day", not any("No Docterz export" in x for x in lines), lines)
ok("P12 ... and the old empty 'no date in the file' reports are not shouted", not any("no date in the file" in x for x in lines), lines)
con.execute("INSERT INTO docterz_export (drive_id, drive_mtime, md5, kind, business_date, rows, status, note, taken_at) VALUES "
            "('walk-q','x','q1','followup','2031-03-20',5,'quarantined','FEWER ROWS (5) than export #1 (9) -- not taken; check the export',?)",
            (dt.datetime(2031, 3, 20, 21, 0).isoformat(sep=" "),))
con.commit()
lines = DP.owner_lines(con, dt.datetime(2031, 3, 21, 11, 0))
ok("P13 ... a real set-aside export is still shouted", any("FEWER ROWS" in x for x in lines), lines)
lines = DP.owner_lines(con, dt.datetime(2031, 3, 20, 11, 0))
ok("P14 a working day with no report at all: the red line stays", any("No Docterz export for Wed 19-Mar" in x for x in lines), lines)

# ---- the owner's marks
OD.now_ist = lambda: dt.datetime(2031, 3, 24, 9, 0)                      # Monday 24-Mar-2031
okm, why = OD.mark(con, "2031-03-24", "walkowner")
r = row("2031-03-24")
ok("O1 'not sitting today': a CURRENT consultation row of the day, 0 rows, nothing stored", okm and r is not None and r["rows"] == 0 and r["stored"] == "" and r["drive_id"] == "offday:walkowner", why)
q1 = con.execute("SELECT 1 FROM docterz_export WHERE kind='consultation' AND business_date=? AND status='current' ORDER BY id DESC LIMIT 1", ("2031-03-24",)).fetchone()
ok("O2 the readers' own query (missing-export alert, Aaj ka kaam, the console) finds it", q1 is not None)
okm2, why2 = OD.mark(con, "2031-03-18", "walkowner")
ok("O3 a day whose report has patients cannot be marked", not okm2 and "patients" in why2, why2)
ok("O4 Sunday and out of range refused", not OD.mark(con, "2031-03-23", "w")[0] and not OD.mark(con, "2031-07-01", "w")[0] and not OD.mark(con, "2031-03-10", "w")[0])
okm3, _ = OD.mark(con, "2031-03-26", "walkowner")                         # a day ahead
k, d, n, st, note = DP.take(con, f(dt.datetime(2031, 3, 26, 20, 0)), REAL.replace(b"18-03-2031", b"26-03-2031"))
ok("O5 a marked day ahead, then he sits: the real report wins, the mark goes", okm3 and st == "current" and row("2031-03-26")["rows"] == 2 and not off("2031-03-26"), (st, note))
OD.mark(con, "2031-03-25", "walkowner")
okm4, _ = OD.unmark(con, "2031-03-25", "walkowner")
ok("O6 taken back: the mark and its row go", okm4 and not off("2031-03-25") and row("2031-03-25") is None)
OD.unmark(con, "2031-03-26", "walkowner")
ok("O7 taking back never deletes a real report's row", row("2031-03-26") is not None and row("2031-03-26")["rows"] == 2)
for i in range(3):
    con.execute("INSERT INTO slip (series, day, state) VALUES ('opd','2031-03-27','ok')")
con.commit()
OD.mark(con, "2031-03-27", "walkowner")
k, d, n, st, note = DP.take(con, f(dt.datetime(2031, 3, 27, 20, 0)), EMPTY.replace(b"made up", b"marked day"))
ok("P15 a day HE marked takes the empty report even with OPD slips (his word wins)", st == "current" and row("2031-03-27")["rows"] == 0, (st, note))

# ---- the page, for every role (F-1445)
from flask import Flask, jsonify, request                                # noqa: E402
app = Flask("walk868")


def require(*roles, unit=None):
    r = request.headers.get("X-Walk-Role", "")
    if r == "owner" and "checker" in roles:
        return dict(user="walkowner", role="checker"), None
    return None, (jsonify(ok=False, error="not_permitted"), 403)


OD.init(app, lambda: con, require)
cl = app.test_client()
g = cl.get(OD.PAGE_URL, headers={"X-Walk-Role": "owner"})
body = g.get_data(as_text=True)
ok("F1 his page opens for him, says today is marked (Mon 24-Mar)", g.status_code == 200 and "Today (Mon 24-Mar) is marked" in body, g.status_code)
ok("F2 the page lists the days with 'Take back'", "Take back" in body and "Thu 27-Mar-2031" in body)
for role in ("", "maker", "viewer"):
    ok("F3 refused for role '%s'" % (role or "none"), cl.get(OD.PAGE_URL, headers={"X-Walk-Role": role}).status_code == 403)
p = cl.post(OD.PAGE_URL, json={"action": "mark", "day": "2031-03-28"}, headers={"X-Walk-Role": "owner"})
ok("F4 a mark through the page", p.status_code == 200 and p.get_json()["ok"] and off("2031-03-28"), p.get_data(as_text=True)[:120])
p = cl.post(OD.PAGE_URL, json={"action": "mark", "day": "2031-03-28"}, headers={"X-Walk-Role": "maker"})
ok("F5 a mark by another login refused", p.status_code == 403)
p = cl.post(OD.PAGE_URL, json={"action": "drop", "day": "2031-03-28"}, headers={"X-Walk-Role": "owner"})
ok("F6 an unknown action does nothing", p.get_json()["ok"] is False and off("2031-03-28"))
OD.now_ist = lambda: dt.datetime(2031, 3, 25, 9, 0)
g = cl.get(OD.PAGE_URL, headers={"X-Walk-Role": "owner"})
ok("F7 an unmarked today offers the button", "I am not sitting today (Tue 25-Mar)" in g.get_data(as_text=True))

# ---- the Clinic PCs page: the two words
try:
    import pc_kits as pk                                                 # noqa: E402
    ok("K1 the reception PC heard 2 minutes ago is Working",
       pk._s868_state("reception", "info", "heard 2 minute(s) ago · Google Drive running") == "ok")
    ok("K2 heard 45 minutes ago stays 'Off or not heard'; other PCs untouched",
       pk._s868_state("reception", "info", "heard 45 minute(s) ago") == "info" and pk._WORD["info"] == "Off or not heard"
       and pk._s868_state("medical", "info", "heard 1 minute(s) ago") == "info")
    w = pk._s868_att_words(["Google Drive is NOT running", "walk text that must not show", "disk space is low: 2.0 GB free"])
    ok("K3 the lab PC's items in OUR words, never its text", "Google Drive is not running" in w and "one other thing" in w
       and "its disk is nearly full" in w and "must not show" not in w and "2.0" not in w, w)
except Exception as ex:                                                  # noqa: BLE001
    ok("K pc_kits: %s" % ex, False)
print("WALK %d/%d" % (sum(RES), len(RES)))
