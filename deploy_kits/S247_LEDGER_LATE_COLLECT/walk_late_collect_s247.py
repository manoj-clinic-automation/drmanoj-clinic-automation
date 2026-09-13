#!/usr/bin/env python3
"""LIVE-SHAPE walk of S247_LEDGER_LATE_COLLECT -- staff_ledger.py.

A real ledger directory, real users.json and ledger.jsonl, the real Flask app driven
over WSGI the way the owner's browser drives it. The situation is rebuilt exactly as
it happened: a month is CLOSED first, and the advance arrives afterwards.

Run:  python3 walk_late_collect_s247.py [path/to/staff_ledger.py]
Exit 0 only if every check is ok.
"""
import csv
import json
import os
import secrets
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "staff_ledger.py")
sys.path.insert(0, os.path.dirname(TARGET))

TMP = tempfile.mkdtemp(prefix="s247_")
os.environ["LEDGER_DIR"] = TMP
os.environ["STAFF_CSV"] = os.path.join(TMP, "staff.csv")

import staff_ledger as L                                          # noqa: E402

L.LEDGER_DIR = TMP
L.STAFF_CSV = os.path.join(TMP, "staff.csv")

OK = [0]
BAD = []


def check(name, cond, detail=""):
    if cond:
        OK[0] += 1
        print("  ok    %s" % name)
    else:
        BAD.append(name)
        print("  FAIL  %s %s" % (name, ("-- " + detail) if detail else ""))


def ledger_bytes():
    p = os.path.join(TMP, "ledger.jsonl")
    return open(p, "rb").read() if os.path.exists(p) else b""


def rows():
    return L.load_ledger()


def instalments(issue_id, month=None):
    return [r for r in rows()
            if r["category"] == "ADVANCE_INSTALMENT" and r["contra_of"] == issue_id
            and r["status"] == "APPROVED"
            and (month is None or r.get("closed_month") == month)]


# ---------------------------------------------------------------- the fixture
with open(L.STAFF_CSV, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["user_id", "name", "active", "base_salary"])
    for i, n in enumerate(["Meera", "Nadia"]):
        w.writerow([i + 1, n, "Y", "10000"])

for name, role in (("doc", "checker"), ("mk", "maker_full")):
    salt = secrets.token_hex(16)
    u = L.load_users()
    u[name] = {"pw": L.hash_pw("pw", salt), "salt": salt, "role": role,
               "staff_link": "", "active": True}
    L.save_users(u)
users = L.load_users()

app = L.create_app()
app.config["PROPAGATE_EXCEPTIONS"] = True
C = app.test_client()
C.post(L.URL_PREFIX + "/login", data={"u": "doc", "p": "pw"})
MK = app.test_client()
MK.post(L.URL_PREFIX + "/login", data={"u": "mk", "p": "pw"})


def get(p):
    r = C.get(p)
    return r.status_code, r.get_data(as_text=True)


def post(p, data, cl=None):
    r = (cl or C).post(p, data=data)
    return r.status_code, r.headers.get("Location", ""), r.get_data(as_text=True)


print("\n== S247 walk -- staff_ledger.py %s" % TARGET)
print("   app version %s" % L.APP_VERSION)

# ---- the month that was closed EARLY, exactly as August was ----------------
# An advance that existed before the close, so the close has something to do.
early = L.make_entry(users, "doc", "Nadia", "ADVANCE_ISSUE", "2026-08-05", "", 0,
                     "2000", "before the close", against_month="2026-08")
L.close_month(users, "doc", "2026-08")

# ...and then, five days after the close was pressed, the advance arrives.
adv = L.make_entry(users, "doc", "Meera", "ADVANCE_ISSUE", "2026-08-25", "", 0,
                   "5000", "cash given", against_month="2026-08")
AID = adv["id"]

# and one booked against a LATER month, to prove the ordering guard
later = L.make_entry(users, "doc", "Nadia", "ADVANCE_ISSUE", "2026-08-26", "", 0,
                     "1000", "against next month", against_month="2026-09")
LID = later["id"]

print("\n-- A. the situation, before anything is fixed")
# --------------------------------------------------------------------------
check("A1 the advance is approved and open",
      adv["status"] == "APPROVED" and any(a["issue"]["id"] == AID for a in L.open_advances()))
check("A2 it counts against the August salary", L.advance_against_month(adv) == "2026-08")
check("A3 August is closed", "2026-08" in L.closed_months())
check("A4 August collected nothing from it", instalments(AID, "2026-08") == [])
try:
    L.close_month(users, "doc", "2026-08")
    check("A5 August cannot be closed again", False, "the re-close was allowed")
except ValueError as e:
    check("A5 August cannot be closed again -- unchanged", "already closed" in str(e))

print("\n-- B. the control the page now offers")
# --------------------------------------------------------------------------
s, h = get(L.URL_PREFIX + "/advances")
check("B1 the advances page renders", s == 200 and AID in h)
check("B2 it offers the new control", "/ledger/late-collect" in h)
check("B3 with August among the months", "<option value='2026-08'>" in h)
check("B4 the amount is prefilled with the whole balance", "value='5000'" in h
      or 'value="5000"' in h)
check("B5 a reason is demanded by the form itself", "reason (required)" in h)
check("B6 it says in one line why this exists",
      "already closed" in h and "never repeated" in h)
check("B7 Defer is still there, untouched", "/ledger/defer" in h)

print("\n-- C. what it refuses, and writes nothing while refusing")
# --------------------------------------------------------------------------
for name, form, why in (
    ("C1 a month that is not closed",
     {"id": AID, "month": "2026-09", "reason": "x"}, "not closed yet"),
    ("C2 a month before the one it counts against",
     {"id": LID, "month": "2026-08", "reason": "x"}, "counts against"),
    ("C3 no reason",
     {"id": AID, "month": "2026-08", "reason": "   "}, "needs a written reason"),
    ("C4 more than the balance",
     {"id": AID, "month": "2026-08", "reason": "x", "amount": "5001"}, "between Rs 1"),
    ("C5 nothing, or a negative",
     {"id": AID, "month": "2026-08", "reason": "x", "amount": "0"}, "between Rs 1"),
    ("C6 an amount that is not a number",
     {"id": AID, "month": "2026-08", "reason": "x", "amount": "five"}, "number of rupees"),
    ("C7 an advance that does not exist",
     {"id": "deadbeefdead", "month": "2026-08", "reason": "x"}, "no such approved advance"),
):
    before = ledger_bytes()
    s, _l, body = post(L.URL_PREFIX + "/late-collect", form)
    check(name + " is refused, by reason", why in body, body[:200])
    check(name + " -- and the ledger is byte-identical", ledger_bytes() == before)

s, _l, body = post(L.URL_PREFIX + "/late-collect",
                   {"id": AID, "month": "2026-08", "reason": "x"}, cl=MK)
check("C8 a maker cannot do this at all", s == 403)

print("\n-- D. the correction itself")
# --------------------------------------------------------------------------
before = ledger_bytes()
n_before = len(rows())
s, loc, _b = post(L.URL_PREFIX + "/late-collect",
                  {"id": AID, "month": "2026-08", "reason": "owner ruling 13-Sep"})
check("D1 it returns to the advances page", s == 302 and loc.endswith("/advances"))
check("D2 exactly one row was written", len(rows()) == n_before + 1)
check("D3 the ledger is append-only -- nothing before it moved",
      ledger_bytes().startswith(before))

got = instalments(AID, "2026-08")
check("D4 August now has the collection", len(got) == 1)
r = got[0]
check("D5 it is the same row the close writes",
      r["category"] == "ADVANCE_INSTALMENT" and r["amount"] == -5000
      and r["closed_month"] == "2026-08" and r["contra_of"] == AID
      and r["status"] == "APPROVED" and r["staff"] == "Meera", json.dumps(r)[:200])
check("D6 it carries the name of the person who decided it",
      r["maker"] == "doc" and r["checker"] == "doc")
check("D7 and the reason, in the row itself",
      "owner ruling 13-Sep" in r["narration"] and "already been closed" in r["narration"])
check("D8 and it is marked as a late collection for anyone reading later",
      r.get("late_collection") is True)
check("D9 the balance is now nil", L.advance_recovered(AID) == 5000)
check("D10 the advance has left the open list",
      not any(a["issue"]["id"] == AID for a in L.open_advances()))

print("\n-- E. it cannot be done twice, and the next close does not repeat it")
# --------------------------------------------------------------------------
before = ledger_bytes()
s, _l, body = post(L.URL_PREFIX + "/late-collect",
                   {"id": AID, "month": "2026-08", "reason": "again"})
check("E1 a second collection for the same month is refused",
      "already has a collection" in body)
check("E2 -- and wrote nothing", ledger_bytes() == before)

s, h = get(L.URL_PREFIX + "/advances")
check("E3 the settled advance is gone from the page", AID not in h)

L.close_month(users, "doc", "2026-09")
check("E4 September's close collects nothing more on it",
      instalments(AID, "2026-09") == [])
check("E5 and the August collection still stands, alone", len(instalments(AID)) == 1)

print("\n-- F. the rest of the ledger is untouched")
# --------------------------------------------------------------------------
check("F1 the advance that WAS caught by August's close is unaffected",
      L.advance_recovered(early["id"]) == 2000)
s, h = get(L.URL_PREFIX + "/statement?staff=Meera")
check("F2 the statement shows the collection to the owner",
      s == 200 and "2026-08" in h)
s, h = get(L.URL_PREFIX + "/")
check("F3 the entry form still refuses to offer a system category by hand",
      s == 200 and '"ADVANCE_INSTALMENT"' not in h)
try:
    L.make_entry(users, "doc", "Meera", "ADVANCE_INSTALMENT", "2026-08-25", "", 0,
                 "5000", "sneaky")
    check("F4 a hand-typed instalment is still impossible", False, "it was allowed")
except (PermissionError, ValueError, KeyError):
    check("F4 a hand-typed instalment is still impossible", True)

print("\n-- G. a partial collection")
# --------------------------------------------------------------------------
adv2 = L.make_entry(users, "doc", "Nadia", "ADVANCE_ISSUE", "2026-08-28", "", 0,
                    "2000", "second cash", against_month="2026-08")
A2 = adv2["id"]
s, _l, _b = post(L.URL_PREFIX + "/late-collect",
                 {"id": A2, "month": "2026-08", "reason": "half now", "amount": "1500"})
check("G1 a part amount is taken as given", L.advance_recovered(A2) == 1500)
check("G2 the advance stays open for the rest",
      any(a["issue"]["id"] == A2 and a["balance"] == 500 for a in L.open_advances()))
check("G3 August is no longer offered for that advance",
      L.late_collect_blocked(adv2, "2026-08", rows()).startswith("2026-08 already has"))
check("G4 but September is, now that it is closed",
      L.late_collect_blocked(adv2, "2026-09", rows()) == "")
s, h = get(L.URL_PREFIX + "/advances")
check("G5 and the page offers exactly that", "<option value='2026-09'>" in h)

print("\n-- H. the standing properties")
# --------------------------------------------------------------------------
check("H1 the version says what is live", L.APP_VERSION == "3.8-S247-LATE-COLLECT")
try:
    L.close_month(users, "doc", "2026-09")
    check("H2 close_month still refuses a re-close", False, "allowed")
except ValueError:
    check("H2 close_month still refuses a re-close", True)
check("H3 closed_months reads back what was closed",
      set(L.closed_months()) >= {"2026-08", "2026-09"})
check("H4 the helper and the writer agree on what is blocked",
      L.late_collect_blocked(adv, "2026-08", rows()).startswith("2026-08 already has"))

print("\n== %d checks, %d ok, %d failed" % (OK[0] + len(BAD), OK[0], len(BAD)))
if BAD:
    for b in BAD:
        print("   FAILED: %s" % b)
    sys.exit(1)
print("== WALK GREEN")
sys.exit(0)
