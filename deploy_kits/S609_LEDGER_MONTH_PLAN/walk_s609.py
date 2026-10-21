#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s609.py -- kit S609 (S331): the month plan on the statement and the Loans page.

    python3 walk_s609.py --code DIR --scratch DIR [--live-ledger DIR --staff-csv FILE]

Part A, made-up person "Walk Staff" (Surendra's shape): two old advances of Rs 3000 (Rs 2000 instalment each, Rs 2000
already back on the first) and a new Rs 5000 against this month. The statement must say: outstanding Rs 9000, to be
cut Rs 7000 (5000 + 1000 + 1000), left after Rs 2000; the Loans page "falling due" Rs 7000; and the REAL close of the
month must then write exactly the rows the plan showed.
Part B (with --live-ledger, on the box): on a scratch COPY of the live ledger, the dry run equals the real close row
for row, and the OLD file's real close writes the same rows as the NEW file's -- the close itself is unchanged.
Exit 0 = GREEN. On the old file Part A goes RED (no plan: the negative control).
"""
import argparse
import datetime
import importlib.util
import json
import os
import shutil
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--code", required=True, help="folder holding the staff_ledger.py under test")
ap.add_argument("--scratch", required=True)
ap.add_argument("--live-ledger", default="")
ap.add_argument("--staff-csv", default="")
ap.add_argument("--old-code", default="", help="folder holding the OLD staff_ledger.py (Part B's close comparison)")
a = ap.parse_args()
S = os.path.abspath(a.scratch)
if S.startswith("/root/staff_ledger"):
    print("RED: refusing to walk in the live ledger folder")
    sys.exit(1)
os.environ["NTFY_URL"] = ""
passed, failed = [], []


def check(cond, label):
    (passed if cond else failed).append(label)
    print(("  ok   " if cond else "  FAIL ") + label)
    return cond


def load(code_dir, ledger_dir, staff_csv, tag):
    os.environ["LEDGER_DIR"] = ledger_dir
    os.environ["STAFF_CSV"] = staff_csv
    os.environ["ATT_BASE"] = os.path.join(S, "att")
    spec = importlib.util.spec_from_file_location("staff_ledger_" + tag, os.path.join(code_dir, "staff_ledger.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def strip(rows):
    keep = ("staff", "category", "date_from", "amount", "contra_of", "narration", "closed_month")
    return sorted([tuple(str(r.get(k)) for k in keep) for r in rows])


today = datetime.date.today()
M = today.strftime("%Y-%m")
first = today.replace(day=1)
P = (first - datetime.timedelta(days=1)).strftime("%Y-%m")
TS = "2099-01-01T00:00:00"


def row(i, cat, amount, date, **kw):
    r = {"id": i, "ts_entry": TS, "maker": kw.pop("maker", "walk"), "staff": "Walk Staff", "category": cat,
         "date_from": date, "date_to": date, "days": 0, "amount": amount, "instalment": kw.pop("instalment", None),
         "narration": kw.pop("narration", "walk"), "self_flag": False, "direct": True, "status": "APPROVED",
         "checker": "walk", "ts_decision": TS, "contra_of": kw.pop("contra_of", None),
         "closed_month": kw.pop("closed_month", ""), "interest": False}
    r.update(kw)
    return r


# ------------------------------------------------------------------ Part A
LA = os.path.join(S, "A_ledger")
shutil.rmtree(LA, ignore_errors=True)
os.makedirs(LA)
os.makedirs(os.path.join(S, "att"), exist_ok=True)
CSVA = os.path.join(S, "A_staff_master.csv")
with open(CSVA, "w") as fh:
    fh.write("user_id,name,department,base_salary,allowed_offs,wd_start,wd_end,sun_start,sun_end,active,timing_note,"
             "sunday_group,minutes_exempt\n9001,Walk Staff,Pathology,20000,2,09:00,21:00,09:00,15:00,Y,,C,N\n")
rows = [
    row("wA", "ADVANCE_ISSUE", 3000, P + "-15", instalment=2000, closed_month=P),
    row("wAr", "ADVANCE_INSTALMENT", -2000, P, contra_of="wA", closed_month=P, maker="SYSTEM",
        narration="auto instalment for advance wA (balance after: 1000)"),
    row("wB", "ADVANCE_ISSUE", 3000, P + "-17", instalment=2000, closed_month=P),
    row("wC", "ADVANCE_ISSUE", 5000, M + "-08", instalment=5000, against_month=M),
]
with open(os.path.join(LA, "ledger.jsonl"), "w") as fh:
    for r in rows:
        fh.write(json.dumps(r) + "\n")
L = load(a.code, LA, CSVA, "newA")
L.save_users({"walk": {"role": "checker", "salt": "00", "pw": "x", "active": True, "staff_link": ""}})

print("[A] the month plan -- Surendra's shape, made up")
if not check(hasattr(L, "month_plan"), "the ledger has a month plan"):
    print("RED: no month plan (the old file)")
    sys.exit(1)
pl = L.month_plan()
check(pl["month"] == M and not pl["closed"] and not pl["error"], "the next close is %s (open)" % M)
mine = L.plan_for_staff("Walk Staff", pl)
check(mine["take"] == 7000, "to be cut this month: Rs %d (5000 + 1000 + 1000), not 9000" % mine["take"])
amts = sorted(l["rs"] for l in mine["lines"])
check(amts == [1000, 1000, 5000], "three lines: %s" % amts)
check(any("clears it" in l["what"] for l in mine["lines"]) and any("Rs 2000 left" in l["what"] for l in mine["lines"]),
      "each line says what it does to its advance")
app = L.create_app()
C = app.test_client()
with C.session_transaction() as s:
    s["u"] = "walk"
html = C.get("/ledger/statement?staff=Walk+Staff").data.decode()
check("Total advance outstanding now: <b>Rs 9000</b>" in html, "statement: total outstanding Rs 9000")
check("To be cut from %s salary: <b>Rs 7000</b>" % L._month_words(M) in html, "statement: to be cut Rs 7000")
check("Left after %s: <b>Rs 2000</b>" % L._month_words(M) in html, "statement: left after Rs 2000")
loans = C.get("/ledger/loans?staff=Walk+Staff").data.decode()
check("falling due in %s: <b>Rs 7000</b>" % M in loans, "Loans page: falling due Rs 7000 (was 8000)")
n0 = len(L.load_ledger())
L.close_month({}, "preview", M, dry=True)
check(len(L.load_ledger()) == n0 and not os.path.exists(L._p("approved_adjustments_%s.csv" % M)),
      "the dry run writes nothing (no row, no CSV)")
got = L.close_month(L.load_users(), "walk", M)
real = [r for r in L.load_ledger() if r.get("closed_month") == M and r.get("maker") == "SYSTEM"]
check(strip(real) == strip(pl["rows"]), "the REAL close wrote exactly the rows the plan showed")
check(sum(-r["amount"] for r in real if r["category"] == "ADVANCE_INSTALMENT") == 7000, "and took Rs 7000")
pl2 = L.month_plan(M)
check(pl2["closed"] and L.plan_for_staff("Walk Staff", pl2)["take"] == 7000, "after the close the page shows what was taken")

# ------------------------------------------------------------------ Part B
if a.live_ledger:
    print("[B] the close itself is unchanged -- scratch copies of the live ledger")
    for tag in ("B_new", "B_old", "B_dry"):
        d = os.path.join(S, tag)
        shutil.rmtree(d, ignore_errors=True)
        shutil.copytree(a.live_ledger, d)
    Ln = load(a.code, os.path.join(S, "B_dry"), a.staff_csv, "dry")
    mon = Ln.next_close_month()
    pl = Ln.month_plan(mon)
    check(not pl["error"], "dry run of %s on the live ledger copy: %d rows" % (mon, len(pl["rows"])))
    Ln2 = load(a.code, os.path.join(S, "B_new"), a.staff_csv, "new")
    u = {"walk": {"role": "checker"}}
    try:
        Ln2.close_month(u, "walk", mon)
        new_rows = [r for r in Ln2.load_ledger() if r.get("closed_month") == mon and r.get("maker") == "SYSTEM"]
        check(strip(new_rows) == strip(pl["rows"]), "the NEW real close = its dry run, row for row (%d)" % len(new_rows))
        if a.old_code:
            Lo = load(a.old_code, os.path.join(S, "B_old"), a.staff_csv, "old")
            Lo.close_month(u, "walk", mon)
            old_rows = [r for r in Lo.load_ledger() if r.get("closed_month") == mon and r.get("maker") == "SYSTEM"]
            check(strip(old_rows) == strip(new_rows), "the OLD close and the NEW close write the same rows (%d)" % len(old_rows))
            on = open(os.path.join(S, "B_old", "approved_adjustments_%s.csv" % mon)).read().split("\n", 1)[1]
            nn = open(os.path.join(S, "B_new", "approved_adjustments_%s.csv" % mon)).read().split("\n", 1)[1]
            check(on == nn, "and the same month CSV")
    except Exception as ex:                                       # noqa: BLE001
        check(False, "the close on the copy raised %r" % ex)
    for tag in ("B_new", "B_old", "B_dry"):
        shutil.rmtree(os.path.join(S, tag), ignore_errors=True)

print("")
print("WALK S609: %d passed, %d failed" % (len(passed), len(failed)))
print("GREEN" if not failed else "RED")
sys.exit(0 if not failed else 1)
