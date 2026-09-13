#!/usr/bin/env python3
"""LIVE-SHAPE walk of S246_AMIR_LIST_REOPEN -- getting back into the flow.

A real Flask app, a real sqlite database with the real column shapes, driven over WSGI.
The thing being proven: DIN BAND is no longer a dead end -- the banner is links, the
closed screen names the ways back, and the day can be opened again, recorded.

Run:  python3 walk_amir_reopen_s246.py [path/to/amir_day.py]
Exit 0 only if every check is ok.
"""
import json
import os
import re
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "amir_day.py")
sys.path.insert(0, os.path.dirname(TARGET))
os.environ.setdefault("SALTS_REFRESH_STATE", os.path.join(tempfile.gettempdir(), "no_salts.json"))

import amir_day                                                     # noqa: E402
from flask import Flask                                             # noqa: E402

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


def st(d):
    return d.strftime("%Y-%m-%d %H:%M:%S")


def ms(d):
    return d.strftime("%Y%m%d-%H%M%S")


TODAY = now().strftime("%Y-%m-%d")
FIRST = TODAY[:8] + "01"

DB = os.path.join(tempfile.mkdtemp(prefix="s246_"), "finance.db")
cx = sqlite3.connect(DB, check_same_thread=False)
cx.row_factory = sqlite3.Row
cx.executescript("""
CREATE TABLE purchase_export(md5 TEXT PRIMARY KEY, type TEXT, period_from TEXT, period_to TEXT,
  export_stamp TEXT, n_rows INTEGER, grand_amount_p INTEGER, received_at TEXT, superseded_by TEXT);
CREATE TABLE purchase_bill(bw_md5 TEXT, supplier TEXT, supplier_norm TEXT, bill_no TEXT,
  bill_date TEXT, amount_p INTEGER);
""")
# the amir_day table EXACTLY as it exists live, before this kit -- four columns
cx.execute("""CREATE TABLE amir_day(day TEXT PRIMARY KEY, opened_at TEXT,
                                    closed_at TEXT, closed_by TEXT)""")
cx.execute("INSERT INTO amir_day(day, opened_at) VALUES('2026-09-01','2026-09-01 09:00:00')")
cx.commit()

app = Flask(__name__)
app.config["PROPAGATE_EXCEPTIONS"] = True
amir_day.init(app, lambda: cx, lambda *a, **k: ({"username": "amir"}, None), unit="medical")
C = app.test_client()


def get(p):
    r = C.get(p)
    return r.status_code, r.headers.get("Location", ""), r.get_data(as_text=True)


def post(p, data):
    r = C.post(p, data=data)
    return r.status_code, r.headers.get("Location", ""), r.get_data(as_text=True)


def tick(step):
    cx.execute("INSERT OR REPLACE INTO amir_step(day, step, done_at, by_user) VALUES(?,?,?,'amir')",
               (TODAY, step, st(now())))
    cx.commit()


def put_export(kind):
    key = "%s-%s" % (kind, ms(now()))
    cx.execute("INSERT OR REPLACE INTO purchase_export VALUES(?,?,?,?,?,?,?,?,NULL)",
               (key, kind, FIRST, TODAY, ms(now()), 137, 4455600, st(now())))
    cx.commit()
    return key


def add_bill(bw, supplier, norm, no, paise):
    cx.execute("INSERT INTO purchase_bill VALUES(?,?,?,?,?,?)",
               (bw, supplier, norm, no, TODAY, paise))
    cx.commit()


def day_row():
    r = cx.execute("SELECT * FROM amir_day WHERE day=?", (TODAY,)).fetchone()
    return dict(r) if r else {}


def answer(h, **by_norm):
    k = {"k": re.findall(r"name='k_(\d+)' value='([^']*)'", h),
         "n": re.findall(r"name=n value='(\d+)'", h)}
    form = {"n": k["n"][0], "go": "5"}
    for i, v in k["k"]:
        form["k_%s" % i] = v
        norm = v.split("|")[0]
        if by_norm.get(norm):
            form["r_%s" % i] = by_norm[norm]
    return form


PHONE = re.compile(r"(?<!\d)\d{10}(?!\d)")
PAGES = []


def scan(h):
    PAGES.append(h)
    return h


# ==========================================================================
print("\n== S246 walk -- amir_day.py %s" % TARGET)

print("\n-- A. the schema grows under a table that is already there")
# --------------------------------------------------------------------------
before = {r[1] for r in cx.execute("PRAGMA table_info(amir_day)").fetchall()}
check("A1 the live table starts with four columns", before == {"day", "opened_at", "closed_at", "closed_by"},
      str(sorted(before)))
amir_day._ensure(cx)
after = {r[1] for r in cx.execute("PRAGMA table_info(amir_day)").fetchall()}
check("A2 the two new columns are added in place", {"reopened_at", "reopened_by"} <= after)
amir_day._ensure(cx)
amir_day._ensure(cx)
check("A3 running it again changes nothing (F-303)",
      {r[1] for r in cx.execute("PRAGMA table_info(amir_day)").fetchall()} == after)
old = cx.execute("SELECT opened_at FROM amir_day WHERE day='2026-09-01'").fetchone()
check("A4 an existing row keeps its data", old and old["opened_at"] == "2026-09-01 09:00:00")

print("\n-- B. every step is a link, on every screen")
# --------------------------------------------------------------------------
tick(1); tick(2); tick(3)
bw = put_export("BILLWISE")
put_export("ITEMWISE")
add_bill(bw, "SHREE BALAJI MEDICAL AGENCY", "shreebalajimedicalagency", "B-7781", 1234500)
add_bill(bw, "AYUSH PHARMA DISTRIBUTORS", "ayushpharmadistributors", "AP-2214", 876500)

h = scan(get("/finance/amir/step/1")[2])
links = re.findall(r"<a class='[a-z]*' href='/finance/amir/step/(\d)'>", h)
check("B1 all seven steps are links in the banner", links == list("1234567"), str(links))
check("B2 the banner no longer has dead <span> steps", "<span class='on'>" not in h)
check("B3 the link text is still the step name", "Punch" in h and "Band" in h)

print("\n-- C. close the day, then find the way back in")
# --------------------------------------------------------------------------
h = scan(get("/finance/amir/step/5")[2])
post("/finance/amir/step/5", answer(h, shreebalajimedicalagency="ok",
                                    ayushpharmadistributors="short"))
tick(6)
w = amir_day._work(cx, TODAY)
check("C1 the day is ready to close", amir_day._ready_to_close(w))
post("/finance/amir/step/7", {"go": "7"})
check("C2 it closed", day_row().get("closed_at") is not None)

h = scan(get("/finance/amir/step/7")[2])
check("C3 the closed screen says DIN BAND", "DIN BAND" in h)
check("C4 it offers the bill list by name", "Bill dekhiye" in h and "/finance/amir/step/5" in h)
check("C5 it names how many flags are waiting there", "1 flag" in h, "flag count on the link")
check("C6 it offers salt and the report check", "Salt aur naam" in h and "Report ki jaanch" in h)
check("C7 it offers to open the day again", "Din phir se kholiye" in h)
check("C8 and the banner is still all links",
      re.findall(r"<a class='[a-z]*' href='/finance/amir/step/(\d)'>", h) == list("1234567"))

s, loc, _ = get("/finance/amir")
check("C9 'where did I leave off' lands on the closed screen, not nowhere",
      loc.endswith("/step/7"), loc)
s, _l, h2 = get("/finance/amir/step/5")
check("C10 a step opened directly on a closed day still renders",
      s == 200 and "Flag kiye hue bill" in h2)

print("\n-- D. a new bill after the close is not silently lost")
# --------------------------------------------------------------------------
add_bill(bw, "RAAT KA SUPPLIER", "raatkasupplier", "RK-1", 250000)
h = scan(get("/finance/amir/step/7")[2])
check("D1 the closed screen says a new bill has arrived", "naya bill aa gaya hai" in h)
s, loc, _ = get("/finance/amir")
check("D2 and the jump takes him to the bills", loc.endswith("/step/5"), loc)

print("\n-- E. opening the day again")
# --------------------------------------------------------------------------
s, loc, _ = post("/finance/amir/step/7", {"go": "7"})
check("E1 a plain post on a closed day does NOT reopen it",
      day_row().get("closed_at") is not None)

s, loc, _ = post("/finance/amir/step/7", {"reopen": "1", "go": "7"})
r = day_row()
check("E2 reopening clears the close", r.get("closed_at") is None and r.get("closed_by") is None)
check("E3 and records when, and by whom",
      r.get("reopened_at") and r.get("reopened_by") == "amir", str(r))
check("E4 the step 7 tick is gone, so the day reads OPEN",
      cx.execute("SELECT 1 FROM amir_step WHERE day=? AND step=7", (TODAY,)).fetchone() is None)
check("E5 it drops him where the work actually is", loc.endswith("/step/5"), loc)

w = amir_day._work(cx, TODAY)
check("E6 everything else already done stays done",
      w["done"].get(1) and w["done"].get(2) and w["done"].get(4) and w["done"].get(6))
check("E7 his answers were not touched",
      cx.execute("SELECT COUNT(*) c FROM amir_bill_disposition").fetchone()["c"] == 2)
check("E8 and the flag is still standing", len(w["flagged_bills"]) == 1)

h = scan(get("/finance/amir/step/7")[2])
check("E9 the close screen is back to asking, not announcing",
      "Abhi kuch baaki hai" in h or "Din band karein?" in h)

print("\n-- F. re-closing, and what the owner sees")
# --------------------------------------------------------------------------
h = scan(get("/finance/amir/step/5")[2])
post("/finance/amir/step/5", answer(h, raatkasupplier="ok"))
post("/finance/amir/step/7", {"go": "7"})
check("F1 the day closes again", day_row().get("closed_at") is not None)
h = scan(get("/finance/amir/step/7")[2])
check("F2 and the screen says it had been opened again", "dobara khola gaya tha" in h)

h = scan(get("/finance/amir/day")[2])
check("F3 the owner's page says so too, in English", "reopened" in h)
check("F4 and names who", "amir" in h)
check("F5 the owner's page carries no Hinglish from this change",
      "phir se kholiye" not in h and "dobara khola" not in h)

s, _l, body = get("/finance/amir/day/api/visit-summary")
try:
    v = json.loads(body)
except ValueError:
    v = {}
check("F6 the visit summary carries the reopen, for the record",
      bool(v.get("reopened_at")) and v.get("reopened_by") == "amir", body[:120])

print("\n-- G. the standing properties")
# --------------------------------------------------------------------------
check("G1 GATE_STEPS unchanged", amir_day.GATE_STEPS == (2, 4, 5, 6))
check("G2 the five answers are unchanged",
      [c for c, _l in amir_day.REASONS] == ["ok", "short", "nodeal", "discount", "other"])
check("G3 the settlement line is a real date", re.match(r"^\d{4}-\d{2}-\d{2}$", amir_day.BILLS_FROM))
s, _l, hz = get("/finance/amir/api/healthz")
check("G4 healthz names this kit", "S246_AMIR_LIST_REOPEN" in hz, hz[:80])
bad = [i for i, p in enumerate(PAGES) if PHONE.search(re.sub(r"<[^>]+>", " ", p))]
check("G5 no ten-digit phone-shaped number on any screen walked (F-185)", not bad, str(bad))
check("G6 no onclick/onchange handler was introduced",
      not any(re.search(r"\son(click|change|input|submit)=", p) for p in PAGES))
check("G7 no <script> tag was introduced", not any(re.search(r"<script[ >]", p) for p in PAGES))

print("\n== %d checks, %d ok, %d failed" % (OK[0] + len(BAD), OK[0], len(BAD)))
if BAD:
    for b in BAD:
        print("   FAILED: %s" % b)
    sys.exit(1)
print("== WALK GREEN")
sys.exit(0)
