#!/usr/bin/env python3
"""LIVE-SHAPE walk of S244_AMIR_PROCESSING -- amir_day.py, step 3 and step 4.

Not a mock of the logic: a real Flask app, a real sqlite database with the real
column shapes of purchase_export / purchase_bill / amir_step / mi_file, driven over
WSGI the way Amir's phone drives it -- GETs, POSTs, 303s followed by hand.

Run:  python3 walk_amir_processing_s244.py [path/to/amir_day.py]
Exit 0 only if every check is ok.
"""
import os
import re
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "amir_day.py")
sys.path.insert(0, os.path.dirname(TARGET))
os.environ.setdefault("SALTS_REFRESH_STATE", os.path.join(tempfile.gettempdir(), "no_such_salts_state.json"))

import amir_day                                                     # noqa: E402
from flask import Flask                                             # noqa: E402

assert os.path.samefile(amir_day.__file__.replace(".pyc", ".py"), TARGET), \
    "imported the wrong amir_day.py: %s" % amir_day.__file__

IST = timezone(timedelta(hours=5, minutes=30))
OK = [0]
BAD = []


def check(name, cond, detail=""):
    if cond:
        OK[0] += 1
        print("  ok    %s" % name)
    else:
        BAD.append(name)
        print("  FAIL  %s %s" % (name, ("-- " + detail) if detail else ""))


def now():
    return datetime.now(IST)


def stamp(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def marg_stamp(dt):
    """Marg's own export stamp shape, as the purchase door writes it (F-455)."""
    return dt.strftime("%Y%m%d-%H%M%S")


TODAY = now().strftime("%Y-%m-%d")
FIRST = TODAY[:8] + "01"


# --------------------------------------------------------------------------
# the live shapes
# --------------------------------------------------------------------------
DB = os.path.join(tempfile.mkdtemp(prefix="s244_"), "finance.db")
_cx = sqlite3.connect(DB, check_same_thread=False)
_cx.row_factory = sqlite3.Row
_cx.executescript("""
CREATE TABLE purchase_export(
  md5 TEXT PRIMARY KEY, type TEXT, period_from TEXT, period_to TEXT,
  export_stamp TEXT, n_rows INTEGER, grand_amount_p INTEGER, received_at TEXT,
  superseded_by TEXT, filename TEXT, bytes INTEGER);
CREATE TABLE purchase_bill(
  bw_md5 TEXT, supplier TEXT, supplier_norm TEXT, bill_no TEXT,
  bill_date TEXT, amount_p INTEGER);
CREATE TABLE mi_file(
  id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, stamp TEXT,
  received_at TEXT, verdict TEXT, filename TEXT);
CREATE TABLE purchase_salt_task(
  id INTEGER PRIMARY KEY AUTOINCREMENT, section TEXT, done INTEGER,
  done_at TEXT, done_by TEXT);
CREATE TABLE amir_salt_upload(
  id INTEGER PRIMARY KEY AUTOINCREMENT, uploaded_at TEXT, ticked INTEGER);
""")
_cx.commit()

USER = {"username": "amir", "role": "maker"}
DENY = [False]


def db():
    return _cx


def require(*roles, **kw):
    if DENY[0]:
        return None, "no"
    return USER, None


app = Flask(__name__)
app.config["PROPAGATE_EXCEPTIONS"] = True
amir_day.init(app, db, require, unit="medical")
C = app.test_client()


# --------------------------------------------------------------------------
# helpers that talk to the screens
# --------------------------------------------------------------------------
def get(path):
    r = C.get(path)
    return r.status_code, r.headers.get("Location", ""), r.get_data(as_text=True)


def post(path, **form):
    r = C.post(path, data=form)
    return r.status_code, r.headers.get("Location", ""), r.get_data(as_text=True)


def step4():
    return get("/finance/amir/step/4")[2]


def clear_exports():
    _cx.execute("DELETE FROM purchase_export")
    _cx.execute("DELETE FROM purchase_bill")
    _cx.commit()


def put_export(kind, when, pfrom=FIRST, pto=TODAY, rows=120, md5=None):
    _cx.execute(
        "INSERT OR REPLACE INTO purchase_export"
        "(md5, type, period_from, period_to, export_stamp, n_rows, grand_amount_p,"
        " received_at, superseded_by) VALUES(?,?,?,?,?,?,?,?,NULL)",
        (md5 or ("%s-%s" % (kind, marg_stamp(when))), kind, pfrom, pto,
         marg_stamp(when), rows, 4455600, stamp(when)))
    _cx.commit()
    return md5 or ("%s-%s" % (kind, marg_stamp(when)))


def set_tick3(minutes_ago):
    _cx.execute("INSERT OR REPLACE INTO amir_step(day, step, done_at, by_user) VALUES(?,3,?,?)",
                (TODAY, stamp(now() - timedelta(minutes=minutes_ago)), "amir"))
    _cx.commit()


def tick3_at():
    r = _cx.execute("SELECT done_at FROM amir_step WHERE day=? AND step=3", (TODAY,)).fetchone()
    return r["done_at"] if r else None


PHONE = re.compile(r"(?<!\d)\d{10}(?!\d)")
PAGES = []


def scan(html_text):
    PAGES.append(html_text)
    return html_text


# ==========================================================================
print("\n== S244 walk -- amir_day.py %s" % TARGET)
print("\n-- A. nothing exported yet")
# --------------------------------------------------------------------------
s, loc, _ = get("/finance/amir")
check("A1 home lands on step 1 on a fresh day", "/finance/amir/step/1" in loc, loc)

h = scan(step4())
check("A2 step 4 says 'abhi nikaali nahi gayi', not 'aaj ki nahi aayi'",
      "Abhi nikaali nahi gayi" in h and "aaj ki nahi aayi" not in h)
check("A3 step 4 offers the way back to step 3", "/finance/amir/step/3" in h)
check("A4 no auto-refresh while nothing is expected", "http-equiv=refresh" not in h)

h = scan(get("/finance/amir/step/3")[2])
check("A5 step 3 prints the FROM date he must type",
      amir_day._ddmmyyyy(FIRST) in h, amir_day._ddmmyyyy(FIRST))
check("A6 step 3 prints TODAY as the TO date",
      amir_day._ddmmyyyy(TODAY) in h, amir_day._ddmmyyyy(TODAY))
check("A7 step 3 says the TO date must be today's", "TO ki tareekh aaj ki honi chahiye" in h)


print("\n-- B. he says he has exported: PROCESSING")
# --------------------------------------------------------------------------
post("/finance/amir/step/1", tick="1", go="1")          # he punches
post("/finance/amir/step/2", tick="2", go="2")          # bills are in Marg
s, loc, _ = post("/finance/amir/step/3", tick="3", go="3")
check("B1 the export tick lands him on step 4, never past it", s == 303 and loc.endswith("/step/4"),
      "%s %s" % (s, loc))

h = scan(step4())
check("B2 step 4 says the report is being made", "Report ban rahi hai" in h)
check("B3 step 4 says the file is on its way to the server",
      "server tak pahunch rahi hai" in h)
check("B4 step 4 does NOT say 'aaj ki nahi aayi' while it is in transit",
      "aaj ki nahi aayi" not in h)
check("B5 step 4 does NOT tell him to make it again while it is in transit",
      "Dobara banaiye" not in h)
check("B6 step 4 re-checks itself", "http-equiv=refresh" in h)
check("B7 step 4 offers to let him start the next task", "Aage ka kaam shuru kijiye" in h)

s, loc, _ = get("/finance/amir")
check("B8 'where did I leave off' does NOT park him on step 4 while processing",
      (not loc.endswith("/step/4")) and loc.rstrip("/")[-1] in "567", loc)

h = scan(get("/finance/amir/step/5")[2])
check("B9 step 5 carries the amber band, not a block", "Report abhi ban rahi hai" in h)
check("B10 the banner shows step 4 amber while processing", "class='wait'" in h)

s, loc, _ = post("/finance/amir/step/4", skip="1", go="4")
check("B11 'aage ka kaam' moves him on to step 5", s == 303 and loc.endswith("/step/5"),
      "%s %s" % (s, loc))
check("B12 step 4 is never ticked by him",
      _cx.execute("SELECT 1 FROM amir_step WHERE day=? AND step=4", (TODAY,)).fetchone() is None)


print("\n-- C. one report lands, the other is still coming")
# --------------------------------------------------------------------------
put_export("BILLWISE", now())
h = scan(step4())
check("C1 the report that arrived is green", "Bill-wise purchase report &#10003;" in h)
check("C2 the other is still processing", "Report ban rahi hai" in h)
check("C3 still not asked to remake anything", "Dobara banaiye" not in h)
_hl = get("/finance/amir")[1]
check("C4 home still lets him work while one report is in transit",
      not _hl.endswith("/step/4"), _hl)


print("\n-- D. both in: PROCESSING DONE")
# --------------------------------------------------------------------------
bw = _cx.execute("SELECT md5 FROM purchase_export WHERE type='BILLWISE'").fetchone()["md5"]
put_export("ITEMWISE", now())
h = scan(step4())
check("D1 step 4 says the check is finished", "Jaanch poori ho gayi" in h)
check("D2 both reports read verified", h.count("&#10003;") >= 2)
check("D3 nothing says processing any more", "Report ban rahi hai" not in h)
check("D4 the page stops re-checking itself", "http-equiv=refresh" not in h)
check("D5 the only button is forward", "Aage badhiye" in h and "Dobara banai" not in h)
check("D6 Marg's own YYYYMMDD-HHMMSS stamp verifies (F-455 stays fixed)",
      "rows" in h and "baje" in h)
w = amir_day._work(_cx, TODAY)
check("D7 step 4 counts as done, proven not ticked", w["done"][4] is True)
check("D8 nothing is left of the pair on the owner's line",
      not [x for x in amir_day._left(w) if "report" in x.lower()])


print("\n-- E. the grace runs out: only NOW is he asked to make it again")
# --------------------------------------------------------------------------
clear_exports()
set_tick3(amir_day.EXPORT_GRACE_MIN + 2)
h = scan(step4())
check("E1 step 4 now names it missing", "aaj ki nahi aayi" in h)
check("E2 step 4 asks for it again, by name",
      "Dobara banaiye:" in h and "Item-detail purchase report" in h)
check("E3 the Excel warning is still there", "khuli Excel band kijiye" in h)
check("E4 the dates he must type are printed with the ask",
      amir_day._ddmmyyyy(TODAY) in h and amir_day._ddmmyyyy(FIRST) in h)
check("E5 the page no longer re-checks itself", "http-equiv=refresh" not in h)
check("E6 he can still go on to his next task", "Aage ka kaam shuru kijiye" in h)
s, loc, _ = get("/finance/amir")
check("E7 home brings him back to step 4 once it needs him", loc.endswith("/step/4"), loc)
h = scan(get("/finance/amir/step/6")[2])
check("E8 step 6 carries the red-ish reminder band", "Ek report dobara banani hai" in h)


print("\n-- F. 'dobara banai' restarts the clock, and never claims a report arrived")
# --------------------------------------------------------------------------
before = tick3_at()
s, loc, _ = post("/finance/amir/step/4", again="1", go="4")
check("F1 it stays on step 4", s == 303 and loc.endswith("/step/4"), "%s %s" % (s, loc))
check("F2 the transit clock was restarted", tick3_at() > before, "%s -> %s" % (before, tick3_at()))
h = scan(step4())
check("F3 the screen goes back to processing", "Report ban rahi hai" in h)
check("F4 it does not say the report arrived", "Jaanch poori ho gayi" not in h)
check("F5 still no step 4 tick anywhere",
      _cx.execute("SELECT 1 FROM amir_step WHERE day=? AND step=4", (TODAY,)).fetchone() is None)
s, loc, _ = post("/finance/amir/step/4", go="4")
check("F6 a plain look changes nothing and stays put", s == 303 and loc.endswith("/step/4"))


print("\n-- G. the 13-Sep bug itself: a file that DID arrive, with the wrong TO date")
# --------------------------------------------------------------------------
clear_exports()
set_tick3(1)
yday = (datetime.strptime(TODAY, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
put_export("ITEMWISE", now(), pto=yday)                 # his fresh export, TO = yesterday
put_export("BILLWISE", now(), pto=yday)
h = scan(step4())
check("G1 a wrong-period file that just arrived is reported AT ONCE, not waited on",
      "tareekh galat hai" in h and "Report ban rahi hai" not in h)
check("G2 and he is told to make it again with today's date printed",
      "Dobara banaiye:" in h and amir_day._ddmmyyyy(TODAY) in h)

clear_exports()
put_export("ITEMWISE", now() - timedelta(minutes=90), pto=yday)   # yesterday's leftover
put_export("BILLWISE", now() - timedelta(minutes=90), pto=yday)
set_tick3(1)                                                      # he exported a minute ago
h = scan(step4())
check("G3 a STALE wrong file does not mask the fresh one still in transit",
      "Report ban rahi hai" in h and "tareekh galat hai" not in h)


print("\n-- H. the gate, the close, and the owner's words")
# --------------------------------------------------------------------------
check("H1 GATE_STEPS unchanged", amir_day.GATE_STEPS == (2, 4, 5, 6))
h = scan(get("/finance/amir/step/7")[2])
check("H2 the close is refused while the pair is not verified", "Abhi kuch baaki hai" in h)
check("H3 the close wrote nothing",
      _cx.execute("SELECT closed_at FROM amir_day WHERE day=?", (TODAY,)).fetchone()["closed_at"] is None)
s, loc, _ = post("/finance/amir/step/7", go="7")
check("H4 posting the close while unfinished still writes nothing",
      _cx.execute("SELECT closed_at FROM amir_day WHERE day=?", (TODAY,)).fetchone()["closed_at"] is None)

w = amir_day._work(_cx, TODAY)
check("H5 the owner is told a report is still arriving, in English",
      any("still arriving" in x for x in amir_day._left(w)), str(amir_day._left(w)))
clear_exports()
set_tick3(amir_day.EXPORT_GRACE_MIN + 5)
w = amir_day._work(_cx, TODAY)
check("H6 and told 'not verified' once it is genuinely late",
      any("not verified" in x for x in amir_day._left(w)), str(amir_day._left(w)))

h = scan(get("/finance/amir/day")[2])
check("H7 the owner's page carries no Hinglish from this change",
      "ban rahi hai" not in h and "Dobara banaiye" not in h)


print("\n-- I. the standing properties, re-proven on the changed screens")
# --------------------------------------------------------------------------
clear_exports()
set_tick3(1)
bwmd5 = put_export("BILLWISE", now())
_cx.execute("INSERT INTO purchase_bill(bw_md5, supplier, supplier_norm, bill_no, bill_date, amount_p)"
            " VALUES(?,?,?,?,?,?)",
            (bwmd5, "<script>alert(1)</script> AGENCY", "scriptagency", "B-7781",
             TODAY, 1234500))
_cx.commit()
h = scan(get("/finance/amir/step/5")[2])
check("I1 a hostile supplier name is escaped", "<script>alert(1)" not in h and "&lt;script&gt;" in h)
check("I2 the bill list still fills itself -- he types no bill number", "B-7781" in h)

bad_pages = [i for i, p in enumerate(PAGES) if PHONE.search(re.sub(r"<[^>]+>", " ", p))]
check("I3 no ten-digit phone-shaped number on any screen walked (F-185)",
      not bad_pages, str(bad_pages))

DENY[0] = True
s, _l, h = get("/finance/amir/step/4")
check("I4 a user without the role gets a readable refusal", s == 403 and "Yeh page aapke liye nahin" in h)
DENY[0] = False

amir_day._ensure(_cx)
amir_day._ensure(_cx)
check("I5 schema creation stays idempotent (F-303)", True)

_cx.execute("ALTER TABLE purchase_export RENAME TO purchase_export_x")
_cx.commit()
h = scan(step4())
check("I6 a missing purchase_export table does not crash the screen",
      "purchase_export table not present yet" in h)
_cx.execute("ALTER TABLE purchase_export_x RENAME TO purchase_export")
_cx.commit()

check("I7 the grace window is the documented one, and tunable",
      1 <= amir_day.EXPORT_GRACE_MIN <= 60)


# ==========================================================================
print("\n== %d checks, %d ok, %d failed" % (OK[0] + len(BAD), OK[0], len(BAD)))
if BAD:
    for b in BAD:
        print("   FAILED: %s" % b)
    sys.exit(1)
print("== WALK GREEN")
sys.exit(0)
