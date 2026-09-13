#!/usr/bin/env python3
"""LIVE-SHAPE walk of S245_AMIR_BILLTAP -- amir_day.py, step 5 (the bill list).

A real Flask app, a real sqlite database with the real column shapes, driven over WSGI
the way Amir's phone drives it.  Proves three things at once:

  * the screen got simpler -- one tap per bill, the reasons folded away;
  * the list holds what the owner ruled on 13-Sep -- bills from BILLS_FROM onwards
    only, and a flagged bill stays until he marks it Theek hai;
  * nothing the server relies on changed.

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


def dayof(d):
    return d.strftime("%Y-%m-%d")


TODAY = dayof(now())
FIRST = TODAY[:8] + "01"
D2 = dayof(now() - timedelta(days=2))
SETTLED_DAY = (datetime.strptime(amir_day.BILLS_FROM, "%Y-%m-%d")
               - timedelta(days=3)).strftime("%Y-%m-%d")

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


def put_export(kind, when=None):
    when = when or now()
    key = "%s-%s" % (kind, ms(when))
    cx.execute("INSERT OR REPLACE INTO purchase_export VALUES(?,?,?,?,?,?,?,?,NULL)",
               (key, kind, FIRST, dayof(when), ms(when), 137, 4455600, st(when)))
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
        "SELECT bill_no, reason, state, settled_outcome, settled_by FROM amir_claim "
        "ORDER BY id").fetchall()]


def keys_on(h):
    """The exact form fields the screen offers, as the browser would send them."""
    return {"k": re.findall(r"name='k_(\d+)' value='([^']*)'", h),
            "r": re.findall(r"name='r_(\d+)' value='([a-z]+)'", h),
            "n": re.findall(r"name=n value='(\d+)'", h)}


def answer(h, **by_norm):
    """Fill the form the screen is actually offering, the way a browser would."""
    k = keys_on(h)
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
print("\n== S245 walk -- amir_day.py %s" % TARGET)
print("   settlement line BILLS_FROM = %s" % amir_day.BILLS_FROM)

tick(1); tick(2); tick(3)
bw_2 = put_export("BILLWISE", now() - timedelta(days=2))     # the cumulative exports of
bw_1 = put_export("BILLWISE", now() - timedelta(days=1))     # the two previous days
bw_0 = put_export("BILLWISE")                                # and today's
put_export("ITEMWISE")

# PB-1 first arrived two days ago and rides in every export since -- one bill, three rows
for bw in (bw_2, bw_1, bw_0):
    add_bill(bw, "PURANA MEDICAL STORE", "puranamedicalstore", "PB-1", D2, 700000)
add_bill(bw_0, "SHREE BALAJI MEDICAL AGENCY", "shreebalajimedicalagency", "B-7781", TODAY, 1234500)
add_bill(bw_0, "AYUSH PHARMA DISTRIBUTORS", "ayushpharmadistributors", "AP-2214", TODAY, 876500)
add_bill(bw_0, "<script>alert(1)</script> TRADERS", "scripttraders", "X-9", TODAY, 45000)
add_bill(bw_0, "SETTLED SUPPLIER", "settledsupplier", "OLD-AUG", SETTLED_DAY, 999900)

print("\n-- A. what the screen looks like now")
# --------------------------------------------------------------------------
h = scan(get("/finance/amir/step/5")[2])
check("A1 every bill offers one plain 'Theek hai' tap",
      h.count("class=tap") == 4, str(h.count("class=tap")))
check("A2 the reasons are inside a <details> that is SHUT by default",
      h.count("<details class=notok>") == 4 and "<details class=notok open" not in h)
check("A3 the second tap says 'Theek nahi'", h.count("<summary>Theek nahi</summary>") == 4)
check("A4 no 'required' anywhere -- a required control inside a shut <details> "
      "silently blocks the whole submit", "required" not in h)
check("A5 the four reasons are present but folded away",
      all(("value='%s'" % c) in h for c in ("short", "nodeal", "discount", "other")))
check("A6 'Theek hai' comes before the reasons, not among them",
      h.index("Theek hai") < h.index("Kam maal aaya"))

k = keys_on(h)
check("A7 one hidden key per bill, exactly as the server reads it", len(k["k"]) == 4, str(k["k"]))
check("A8 five choices per bill, all one radio group",
      len(k["r"]) == 20 and sorted({i for i, _v in k["r"]}) == ["0", "1", "2", "3"], str(len(k["r"])))
check("A9 the count the server will loop over is on the form", k["n"] == ["4"], str(k["n"]))
check("A10 he types no bill number -- the key travels hidden",
      "value='shreebalajimedicalagency|B-7781|%s'" % TODAY in h)
check("A11 the bill count is said in plain words up top", "4 bill." in h)
check("A12 the save button is always reachable", "class=savebar" in h)
check("A13 a hostile supplier name is escaped",
      "<script>alert(1)" not in h and "&lt;script&gt;" in h)
check("A14 rupees are readable", "12,345" in h)
check("A15 he is told when to open the second tap, in one line", "Kuch gadbad ho to hi" in h)

print("\n-- B. what the list holds (owner ruling, 13-Sep)")
# --------------------------------------------------------------------------
check("B1 a bill dated before the settlement line is NOT shown",
      "OLD-AUG" not in h and "SETTLED SUPPLIER" not in h)
_pb = h.count("value='puranamedicalstore|PB-1|%s'" % D2)
check("B2 a bill riding in three exports is listed ONCE", _pb == 1, str(_pb))
check("B3 and it is pichhla baaki -- judged by the export that FIRST carried it",
      "Pichhla baaki" in h and "1 bill." in h[:h.index("<form")])
w = amir_day._work(cx, TODAY)
check("B4 the day counts it once, not three times",
      len(w["today_bills"]) + len(w["carry_bills"]) == 4,
      "%d + %d" % (len(w["today_bills"]), len(w["carry_bills"])))

print("\n-- C. answering, and what happens to a flag")
# --------------------------------------------------------------------------
post("/finance/amir/step/5", answer(h, shreebalajimedicalagency="ok",
                                    ayushpharmadistributors="short",
                                    puranamedicalstore="ok"))
d = dispositions()
check("C1 'theek hai' is written", d.get("B-7781") == "ok" and d.get("PB-1") == "ok")
check("C2 a reason is written", d.get("AP-2214") == "short")
check("C3 the bill he left alone is NOT written", "X-9" not in d, str(d))
check("C4 'theek hai' raises no claim",
      not [c for c in claims() if c["bill_no"] in ("B-7781", "PB-1")], str(claims()))
check("C5 a deficiency raises exactly one claim",
      len([c for c in claims() if c["bill_no"] == "AP-2214"]) == 1, str(claims()))

h = scan(get("/finance/amir/step/5")[2])
check("C6 the bills he okayed are gone", "B-7781" not in h and "PB-1" not in h)
check("C7 the untapped bill is still there", "X-9" in h)
check("C8 THE FLAGGED BILL STAYS, in its own band", "AP-2214" in h and "Flag kiye hue bill" in h)
check("C9 and it shows what he wrote, and when",
      "Aapne likha tha" in h and "Kam maal aaya" in h[h.index("Flag kiye hue bill"):])
check("C10 the untapped bill is counted in the subtitle, the flagged one is not", "1 bill." in h)

w = amir_day._work(cx, TODAY)
check("C11 a flag does NOT hold the day open -- step 5 is open on the untapped bill only",
      len(w["flagged_bills"]) == 1 and not w["done"].get(5))

post("/finance/amir/step/5", answer(h, scripttraders="nodeal"))
w = amir_day._work(cx, TODAY)
check("C12 with every bill tapped, step 5 is DONE even with two flags open",
      w["done"].get(5) and len(w["flagged_bills"]) == 2, str(len(w["flagged_bills"])))
h = scan(get("/finance/amir/step/5")[2])
check("C13 the screen then says so and offers the way forward",
      "Aaj ke sab bill ho gaye" in h and "Aage badhiye" in h)

print("\n-- D. the flag clears only on Theek hai, and closes the chase")
# --------------------------------------------------------------------------
check("D1 two claims are open for Darpan",
      len([c for c in claims() if c["state"] != "settled"]) == 2, str(claims()))
post("/finance/amir/step/5", answer(h, ayushpharmadistributors="ok"))
check("D2 marking it Theek hai clears the flag", dispositions().get("AP-2214") == "ok")
c = [x for x in claims() if x["bill_no"] == "AP-2214"][0]
check("D3 and settles the claim Darpan was chasing, named and attributed",
      c["state"] == "settled" and c["settled_outcome"] == "amir_ok" and c["settled_by"] == "amir",
      str(c))
h = scan(get("/finance/amir/step/5")[2])
check("D4 that bill is gone from the list", "AP-2214" not in h)
check("D5 the other flag is still there", "X-9" in h)
check("D6 the other claim was NOT touched",
      [x for x in claims() if x["bill_no"] == "X-9"][0]["state"] != "settled")

post("/finance/amir/step/5", answer(h, scripttraders="discount"))
check("D7 changing the reason on a flagged bill raises no second claim",
      len([x for x in claims() if x["bill_no"] == "X-9"]) == 1, str(claims()))
check("D8 and the new reason is what is stored", dispositions().get("X-9") == "discount")

h = scan(get("/finance/amir/step/5")[2])
post("/finance/amir/step/5", answer(h, scripttraders="ok"))
h = scan(get("/finance/amir/step/5")[2])
check("D9 with nothing left the screen says so", "Koi bill baaki nahi hai" in h)

print("\n-- E. the close, and refusals")
# --------------------------------------------------------------------------
tick(6)
w = amir_day._work(cx, TODAY)
check("E1 the day is ready to close", amir_day._ready_to_close(w))
post("/finance/amir/step/7", {"go": "7"})
check("E2 and it closes", closed_at() is not None)

add_bill(bw_0, "NAYA SUPPLIER", "nayasupplier", "NS-1", TODAY, 100000)
h = scan(get("/finance/amir/step/5")[2])
k2 = keys_on(h)
f2 = {"n": k2["n"][0], "go": "5"}
for i, v in k2["k"]:
    f2["k_%s" % i] = v
    f2["r_%s" % i] = "zzz-not-a-reason"
post("/finance/amir/step/5", f2)
check("E3 a value that is not one of the five is refused, not stored",
      "NS-1" not in dispositions(), str(dispositions()))
check("E4 and the bill comes straight back", "NS-1" in get("/finance/amir/step/5")[2])

print("\n-- F. the standing properties")
# --------------------------------------------------------------------------
check("F1 GATE_STEPS unchanged", amir_day.GATE_STEPS == (2, 4, 5, 6))
check("F2 the five answers are unchanged",
      [c for c, _l in amir_day.REASONS] == ["ok", "short", "nodeal", "discount", "other"])
check("F3 the claim-raising set is unchanged",
      amir_day.CLAIM_REASONS == ("short", "nodeal", "discount", "other"))
check("F4 the settlement line is a real date and tunable",
      re.match(r"^\d{4}-\d{2}-\d{2}$", amir_day.BILLS_FROM) is not None)
bad = [i for i, p in enumerate(PAGES) if PHONE.search(re.sub(r"<[^>]+>", " ", p))]
check("F5 no ten-digit phone-shaped number on any screen walked (F-185)", not bad, str(bad))
check("F6 no onclick/onchange handler was introduced",
      not any(re.search(r"\son(click|change|input|submit)=", p) for p in PAGES))
check("F7 no <script> tag was introduced", not any(re.search(r"<script[ >]", p) for p in PAGES))

cx.execute("UPDATE purchase_export SET superseded_by='x' WHERE type='ITEMWISE'")
cx.commit()
tick(3, mins=amir_day.EXPORT_GRACE_MIN + 3)
h = scan(get("/finance/amir/step/5")[2])
check("F8 the report reminder band still rides above the bills",
      "Ek report dobara banani hai" in h)

print("\n== %d checks, %d ok, %d failed" % (OK[0] + len(BAD), OK[0], len(BAD)))
if BAD:
    for b in BAD:
        print("   FAILED: %s" % b)
    sys.exit(1)
print("== WALK GREEN")
sys.exit(0)
