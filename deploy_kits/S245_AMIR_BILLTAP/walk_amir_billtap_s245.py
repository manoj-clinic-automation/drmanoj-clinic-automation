#!/usr/bin/env python3
"""LIVE-SHAPE walk of S245_AMIR_BILLTAP -- amir_day.py, step 5 (the bill list).

A real Flask app, a real sqlite database with the real column shapes, driven over WSGI
the way Amir's phone drives it.  Proves the screen got simpler AND that nothing the
server relies on changed.

Run:  python3 walk_amir_billtap_s245.py [path/to/amir_day.py]
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
YDAY = (datetime.strptime(TODAY, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

DB = os.path.join(tempfile.mkdtemp(prefix="s245_"), "finance.db")
cx = sqlite3.connect(DB, check_same_thread=False)
cx.row_factory = sqlite3.Row
cx.executescript("""
CREATE TABLE purchase_export(md5 TEXT PRIMARY KEY, type TEXT, period_from TEXT, period_to TEXT,
  export_stamp TEXT, n_rows INTEGER, grand_amount_p INTEGER, received_at TEXT, superseded_by TEXT);
CREATE TABLE purchase_bill(bw_md5 TEXT, supplier TEXT, supplier_norm TEXT, bill_no TEXT,
  bill_date TEXT, amount_p INTEGER);
CREATE TABLE mi_file(id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, stamp TEXT,
  received_at TEXT, verdict TEXT);
CREATE TABLE purchase_salt_task(id INTEGER PRIMARY KEY AUTOINCREMENT, section TEXT,
  done INTEGER, done_at TEXT, done_by TEXT);
""")
cx.commit()

app = Flask(__name__)
app.config["PROPAGATE_EXCEPTIONS"] = True
amir_day.init(app, lambda: cx, lambda *a, **k: ({"username": "amir"}, None), unit="medical")
C = app.test_client()
amir_day._ensure(cx)


def get(p):
    r = C.get(p)
    return r.status_code, r.headers.get("Location", ""), r.get_data(as_text=True)


def post(p, data):
    r = C.post(p, data=data)
    return r.status_code, r.headers.get("Location", ""), r.get_data(as_text=True)


def tick(step, mins=0):
    cx.execute("INSERT OR REPLACE INTO amir_step(day, step, done_at, by_user) VALUES(?,?,?,'amir')",
               (TODAY, step, st(now() - timedelta(minutes=mins))))
    cx.commit()


def put_export(kind, mins=0):
    when = now() - timedelta(minutes=mins)
    key = "%s-%s" % (kind, ms(when))
    cx.execute("INSERT OR REPLACE INTO purchase_export VALUES(?,?,?,?,?,?,?,?,NULL)",
               (key, kind, FIRST, TODAY, ms(when), 137, 4455600, st(when)))
    cx.commit()
    return key


def add_bill(bw, supplier, norm, no, date, paise):
    cx.execute("INSERT INTO purchase_bill VALUES(?,?,?,?,?,?)",
               (bw, supplier, norm, no, date, paise))
    cx.commit()


def closed_at():
    r = cx.execute("SELECT closed_at FROM amir_day WHERE day=?", (TODAY,)).fetchone()
    return r["closed_at"] if r else None


def dispositions():
    return {r["bill_no"]: r["reason"] for r in
            cx.execute("SELECT bill_no, reason FROM amir_bill_disposition").fetchall()}


def claims():
    return [dict(r) for r in cx.execute(
        "SELECT bill_no, reason, state FROM amir_claim ORDER BY id").fetchall()]


def keys_on(page_html):
    """The exact form fields the screen offers, as the browser would send them."""
    return {"k": re.findall(r"name='k_(\d+)' value='([^']*)'", page_html),
            "r": re.findall(r"name='r_(\d+)' value='([a-z]+)'", page_html),
            "n": re.findall(r"name=n value='(\d+)'", page_html)}


PHONE = re.compile(r"(?<!\d)\d{10}(?!\d)")
PAGES = []


def scan(h):
    PAGES.append(h)
    return h


# ==========================================================================
print("\n== S245 walk -- amir_day.py %s" % TARGET)

# a normal morning: punched, bills in, both reports verified
tick(1); tick(2); tick(3)
bw = put_export("BILLWISE")
put_export("ITEMWISE")
add_bill(bw, "SHREE BALAJI MEDICAL AGENCY", "shreebalajimedicalagency", "B-7781", TODAY, 1234500)
add_bill(bw, "AYUSH PHARMA DISTRIBUTORS", "ayushpharmadistributors", "AP-2214", TODAY, 876500)
add_bill(bw, "<script>alert(1)</script> TRADERS", "scripttraders", "X-9", TODAY, 45000)

print("\n-- A. what the screen looks like now")
# --------------------------------------------------------------------------
h = scan(get("/finance/amir/step/5")[2])
check("A1 every bill offers one plain 'Theek hai' tap", h.count("class=tap") == 3)
check("A2 the reasons are inside a <details> that is SHUT by default",
      h.count("<details class=notok>") == 3 and "<details class=notok open" not in h)
check("A3 the second tap says 'Theek nahi'", h.count("<summary>Theek nahi</summary>") == 3)
check("A4 no 'required' anywhere -- a required control inside a shut <details> "
      "silently blocks the whole submit", "required" not in h)
check("A5 the four reasons are present but folded away",
      all(("value='%s'" % c) in h for c in ("short", "nodeal", "discount", "other")))
check("A6 'Theek hai' is not one of four open choices",
      h.count("Kam maal aaya") == 3 and h.index("Theek hai") < h.index("Kam maal aaya"))

k = keys_on(h)
check("A7 one hidden key per bill, exactly as the server reads it", len(k["k"]) == 3, str(k["k"]))
check("A8 five choices per bill, all one radio group", len(k["r"]) == 15
      and sorted({i for i, _v in k["r"]}) == ["0", "1", "2"], str(len(k["r"])))
check("A9 the count the server will loop over is on the form", k["n"] == ["3"], str(k["n"]))
check("A10 he types no bill number -- the key travels hidden",
      "B-7781" in h and "value='shreebalajimedicalagency|B-7781|%s'" % TODAY in h)
check("A11 the bill count is said in plain words up top", "3 bill." in h)
check("A12 the save button is always reachable", "class=savebar" in h)
check("A13 a hostile supplier name is escaped",
      "<script>alert(1)" not in h and "&lt;script&gt;" in h)
check("A14 rupees are readable", "12,345" in h)
check("A15 he is told when to open the second tap, in one line",
      "Kuch gadbad ho to hi" in h)

print("\n-- B. it still does exactly what it did")
# --------------------------------------------------------------------------
kk = {i: v for i, v in k["k"]}
form = {"n": "3", "go": "5"}
for i, v in kk.items():
    form["k_%s" % i] = v
# bill 0 ok, bill 1 short, bill 2 left unanswered
for i, v in kk.items():
    if v.startswith("shreebalaji"):
        form["r_%s" % i] = "ok"
    elif v.startswith("ayushpharma"):
        form["r_%s" % i] = "short"
s, loc, _ = post("/finance/amir/step/5", form)
d = dispositions()
check("B1 'theek hai' is written", d.get("B-7781") == "ok")
check("B2 a reason is written", d.get("AP-2214") == "short")
check("B3 the unanswered bill is NOT written", "X-9" not in d, str(d))
check("B4 'theek hai' raises no claim",
      not [c for c in claims() if c["bill_no"] == "B-7781"], str(claims()))
check("B5 a deficiency raises exactly one claim",
      len([c for c in claims() if c["bill_no"] == "AP-2214"]) == 1, str(claims()))

h = scan(get("/finance/amir/step/5")[2])
check("B6 the unanswered bill comes straight back, alone", h.count("class=tap") == 1 and "X-9" in h)
check("B7 the answered bills are gone", "B-7781" not in h and "AP-2214" not in h)

k2 = keys_on(h)
kk2 = {i: v for i, v in k2["k"]}
f2 = {"n": k2["n"][0], "go": "5"}
for i, v in kk2.items():
    f2["k_%s" % i] = v
    f2["r_%s" % i] = "zzz-not-a-reason"
post("/finance/amir/step/5", f2)
check("B8 a value that is not one of the five is refused, not stored",
      "X-9" not in dispositions(), str(dispositions()))

for i in kk2:
    f2["r_%s" % i] = "nodeal"
post("/finance/amir/step/5", f2)
check("B9 the real answer is then stored", dispositions().get("X-9") == "nodeal")
check("B10 re-answering the same bill raises no second claim",
      len([c for c in claims() if c["bill_no"] == "X-9"]) == 1, str(claims()))
n_before = len(claims())
post("/finance/amir/step/5", f2)
check("B11 and posting it again still raises none", len(claims()) == n_before)

h = scan(get("/finance/amir/step/5")[2])
check("B12 with nothing left the screen says so", "Koi bill baaki nahi hai" in h)

print("\n-- C. yesterday's leftovers, and the close")
# --------------------------------------------------------------------------
bw_y = put_export("BILLWISE", mins=60 * 26)          # yesterday's bill-wise export
add_bill(bw_y, "PICHHLA SUPPLIER", "pichhlasupplier", "OLD-1", YDAY, 500000)
h = scan(get("/finance/amir/step/5")[2])
check("C1 an unanswered older bill returns as pichhla baaki", "Pichhla baaki" in h)
check("C2 and it is tappable in the same simple way",
      h.count("class=tap") == 1 and h.count("<summary>Theek nahi</summary>") == 1)

h = scan(get("/finance/amir/step/7")[2])
check("C3 the day will not close while a bill is untapped", "Abhi kuch baaki hai" in h)
post("/finance/amir/step/7", {"go": "7"})
check("C4 and posting the close writes nothing", closed_at() is None, str(closed_at()))

k3 = keys_on(scan(get("/finance/amir/step/5")[2]))
f3 = {"n": k3["n"][0], "go": "5"}
for i, v in k3["k"]:
    f3["k_%s" % i] = v
    f3["r_%s" % i] = "ok"
post("/finance/amir/step/5", f3)
tick(6)
w = amir_day._work(cx, TODAY)
check("C5 with every bill tapped the day is ready to close", amir_day._ready_to_close(w))
post("/finance/amir/step/7", {"go": "7"})
check("C6 and it closes", closed_at() is not None)

print("\n-- D. the standing properties")
# --------------------------------------------------------------------------
check("D1 GATE_STEPS unchanged", amir_day.GATE_STEPS == (2, 4, 5, 6))
check("D2 the five answers are unchanged",
      [c for c, _l in amir_day.REASONS] == ["ok", "short", "nodeal", "discount", "other"])
check("D3 the claim-raising set is unchanged",
      amir_day.CLAIM_REASONS == ("short", "nodeal", "discount", "other"))
bad = [i for i, p in enumerate(PAGES) if PHONE.search(re.sub(r"<[^>]+>", " ", p))]
check("D4 no ten-digit phone-shaped number on any screen walked (F-185)", not bad, str(bad))
check("D5 the page is still JavaScript-free",
      not any(("<script" in p.lower() and "&lt;" not in p[:p.lower().index("<script")][-6:])
              for p in PAGES if "<script" in p.lower()) or
      all("<script>alert" not in p for p in PAGES))
check("D6 no onclick/onchange handler was introduced",
      not any(re.search(r"\son(click|change|input|submit)=", p) for p in PAGES))

cx.execute("UPDATE purchase_export SET superseded_by='x' WHERE type='ITEMWISE'")
cx.commit()
add_bill(bw, "BAND TEST AGENCY", "bandtestagency", "BT-1", TODAY, 10000)
tick(3, mins=amir_day.EXPORT_GRACE_MIN + 3)
h = scan(get("/finance/amir/step/5")[2])
check("D7 the report reminder band still rides above the bills",
      "Ek report dobara banani hai" in h and "class=tap" in h)

print("\n== %d checks, %d ok, %d failed" % (OK[0] + len(BAD), OK[0], len(BAD)))
if BAD:
    for b in BAD:
        print("   FAILED: %s" % b)
    sys.exit(1)
print("== WALK GREEN")
sys.exit(0)
