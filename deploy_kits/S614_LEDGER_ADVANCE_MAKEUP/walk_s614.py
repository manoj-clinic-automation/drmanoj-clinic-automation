#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s614.py -- kit S614 (S336, D753): what "advance remaining" is made of, on the statement's top section and on
New entry -- on top of all of S612's walk (the statement month by month, an advance against a later month says so).

    python3 walk_s614.py --code DIR --scratch DIR [--live-ledger DIR --live-register FILE --staff-csv FILE]

Part A -- a made-up "Walk Staff" in Surendra's exact shape (Aug: 10th 2000, 14-17th 8000 loan at 2000/month, 25th
3000; Sep: 3rd 1500, 18th 5000; Oct: 1st 980, 8th 5000) and made-up LOCKED salary runs (Aug paid 3260, Sep -980):
the page must read Aug cut 7000 / remaining 6000 / paid Rs 3,260; Sep cut 8500 / remaining 4000 / paid Rs 0 short
by Rs 980; Oct running: to be cut 7980, remaining after 2000; every advance listed; the old lines kept, closed.
Part B -- (on the box) scratch COPIES of the live ledger and staff register: every staff member's page answers; the
running month's "remaining after" equals the top box; each month's remaining follows from the one before
(previous + taken - cut); and every locked month's paid figures add up to that month's locked total payout.
S614 adds -- Part A: Surendra's own Rs 3,000 of 21 Oct against next month's salary; a loan; an agreed schedule; an
advance the salary cannot bear (part held). The top section lists one line per advance left after the close, saying
when it is cut, and the lines add up to "Advance remaining after"; New entry carries, for the chosen person, every
open advance, the close's cut, what is booked against each month and the ceiling; a maker's page script parses
(F-973).  Part B (on the box, scratch copies): for EVERY staff member the lines add up to the top box, and New entry
answers with one line per open advance.
Exit 0 = GREEN; the S612 file goes RED (no make-up).
"""
import subprocess
import tempfile
import argparse
import datetime
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--code", required=True)
ap.add_argument("--scratch", required=True)
ap.add_argument("--live-ledger", default="")
ap.add_argument("--live-register", default="")
ap.add_argument("--staff-csv", default="")
a = ap.parse_args()
S = os.path.abspath(a.scratch)
if S.startswith("/root/staff_ledger") or S.startswith("/root/staff_register"):
    print("RED: refusing to walk in a live folder")
    sys.exit(1)
os.environ["NTFY_URL"] = ""
passed, failed = [], []


def check(cond, label):
    (passed if cond else failed).append(label)
    print(("  ok   " if cond else "  FAIL ") + label)
    return cond


def load(ledger_dir, staff_csv, regdb, tag):
    os.environ.update(LEDGER_DIR=ledger_dir, STAFF_CSV=staff_csv, ATT_BASE=os.path.join(S, "att"),
                      STAFF_REGISTER_DB=regdb)
    spec = importlib.util.spec_from_file_location("sl_" + tag, os.path.join(a.code, "staff_ledger.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def text(html):
    t = re.sub(r"<[^>]+>", " ", html)
    for k, v in (("&mdash;", "-"), ("&middot;", "."), ("&rarr;", "->"), ("&amp;", "&"), ("&nbsp;", " "), ("&minus;", "-")):
        t = t.replace(k, v)
    return re.sub(r"\s+", " ", t)


# ------------------------------------------------------------------ Part A
os.makedirs(os.path.join(S, "att"), exist_ok=True)
today = datetime.date.today()
M = today.strftime("%Y-%m")
NXT = (today.replace(day=28) + datetime.timedelta(days=5)).strftime("%Y-%m")   # the month after (Nov)                        # the running month (Oct in Surendra's case)
first = today.replace(day=1)
M1 = (first - datetime.timedelta(days=1)).strftime("%Y-%m")                 # Sep
M2 = (first - datetime.timedelta(days=1)).replace(day=1)
M2 = (M2 - datetime.timedelta(days=1)).strftime("%Y-%m")                    # Aug
LA = os.path.join(S, "A_ledger")
shutil.rmtree(LA, ignore_errors=True)
os.makedirs(LA)
CSV = os.path.join(S, "A_sm.csv")
with open(CSV, "w") as fh:
    fh.write("user_id,name,department,base_salary,allowed_offs,wd_start,wd_end,sun_start,sun_end,active,timing_note,"
             "sunday_group,minutes_exempt\n9001,Walk Staff,Pathology,10500,2,09:00,21:00,09:00,15:00,Y,,C,N\n"
             "9002,Walk Other,Clinic,9000,2,09:00,21:00,09:00,15:00,Y,,A,N\n"
             "9003,Walk Loan,Clinic,30000,2,09:00,21:00,09:00,15:00,Y,,A,N\n"
             "9004,Walk Sched,Clinic,30000,2,09:00,21:00,09:00,15:00,Y,,A,N\n"
             "9005,Walk Small,Clinic,2000,2,09:00,21:00,09:00,15:00,Y,,A,N\n")
TS = "2099-01-01T00:00:00"


def row(i, cat, amount, date, **kw):
    r = {"id": i, "ts_entry": TS, "maker": kw.pop("maker", "walk"), "staff": kw.pop("staff", "Walk Staff"),
         "category": cat, "date_from": date, "date_to": date, "days": 0, "amount": amount,
         "instalment": kw.pop("instalment", None), "narration": kw.pop("narration", ""), "self_flag": False,
         "direct": True, "status": kw.pop("status", "APPROVED"), "checker": "walk", "ts_decision": TS,
         "contra_of": kw.pop("contra_of", None), "closed_month": kw.pop("closed_month", ""), "interest": False}
    r.update(kw)
    return r


rows = [
    row("a10", "ADVANCE_ISSUE", 2000, M2 + "-10", closed_month=M1),
    row("a14", "ADVANCE_ISSUE", 2000, M2 + "-14", instalment=2000, closed_month=M1),
    row("a15", "ADVANCE_ISSUE", 3000, M2 + "-15", instalment=2000, closed_month=M1),
    row("a17", "ADVANCE_ISSUE", 3000, M2 + "-17", instalment=2000, closed_month=M1),
    row("a25", "ADVANCE_ISSUE", 3000, M2 + "-25", closed_month=M1),
    row("a25d", "ADVANCE_ISSUE", 3000, M2 + "-25", closed_month=M1),               # a duplicate ...
    row("a25x", "ADVANCE_ISSUE", -3000, M2 + "-25", contra_of="a25d", closed_month=M1),   # ... reversed
    row("rej", "ADVANCE_ISSUE", 8000, M2 + "-14", status="REJECTED"),
    row("r1", "ADVANCE_INSTALMENT", -2000, M2, contra_of="a10", closed_month=M2, maker="RECONCILE",
        narration="C1 - clears in full. Balance after: 0"),
    row("r5", "ADVANCE_INSTALMENT", -3000, M2, contra_of="a25", closed_month=M2, maker="RECONCILE",
        narration="C5 - clears in full. Balance after: 0"),
    row("r9", "ADVANCE_INSTALMENT", -2000, M2, contra_of="a14", closed_month=M2, maker="RECONCILE",
        narration="C9 - part 1. Balance after: 0"),
    row("s3", "ADVANCE_ISSUE", 1500, M1 + "-03", against_month=M1, instalment=1500, closed_month=M1),
    row("s18", "ADVANCE_ISSUE", 5000, M1 + "-18", against_month=M1, instalment=5000, closed_month=M1),
    row("i1", "ADVANCE_INSTALMENT", -1500, M1, contra_of="s3", closed_month=M1, maker="SYSTEM",
        narration="quota advance recovered in full (balance after: 0)"),
    row("i2", "ADVANCE_INSTALMENT", -5000, M1, contra_of="s18", closed_month=M1, maker="SYSTEM",
        narration="quota advance recovered in full (balance after: 0)"),
    row("i3", "ADVANCE_INSTALMENT", -2000, M1, contra_of="a15", closed_month=M1, maker="SYSTEM",
        narration="auto instalment for advance a15 (balance after: 1000)"),
    row("o1", "ADVANCE_ISSUE", 980, M + "-01", against_month=M, instalment=980, narration="SHORT OF LAST SALARY"),
    row("o8", "ADVANCE_ISSUE", 5000, M + "-08", against_month=M, instalment=5000),
    row("x1", "NIGHT_DUTY", 400, M1 + "-12", staff="Walk Other", closed_month=M1),
    # a loan with interest, whose first cut was booked in a month BEFORE its date (Darpan's live shape)
    row("l1", "ADVANCE_ISSUE", 20000, M1 + "-05", staff="Walk Loan", instalment=5000, interest=True, closed_month=M1),
    row("lr", "ADVANCE_INSTALMENT", -4000, M2, staff="Walk Loan", contra_of="l1", closed_month=M2, maker="SYSTEM",
        narration="auto instalment for loan l1 (balance after: 16000)"),
    row("li", "LOAN_INTEREST", -1000, M2, staff="Walk Loan", contra_of="l1", closed_month=M2, maker="SYSTEM",
        narration="flat monthly interest on loan l1"),
    row("lc", "LOAN_CAPITALISE", -1000, M2, staff="Walk Loan", contra_of="l1", closed_month=M2, maker="SYSTEM",
        narration="correction"),                                   # Darpan's July correction (S612)
    row("n1", "ADVANCE_ISSUE", 3000, M + "-21", staff="Walk Loan", instalment=3000, against_month=NXT),   # S612
    row("n2", "ADVANCE_ISSUE", 3000, M + "-21", instalment=3000, against_month=NXT, narration="OK"),     # S614: Surendra's
    row("sc", "ADVANCE_ISSUE", 12000, M1 + "-10", staff="Walk Sched", closed_month=M1,
        schedule=[{"month": M, "amount": 4000}, {"month": NXT, "amount": 4000},
                  {"month": (datetime.date(int(NXT[:4]), int(NXT[5:]), 28) + datetime.timedelta(days=5)).strftime("%Y-%m"),
                   "amount": 4000}]),
    row("sm", "ADVANCE_ISSUE", 3000, M + "-05", staff="Walk Small", instalment=3000, against_month=M),
    row("pd", "ADVANCE_ISSUE", 1500, M + "-20", status="PENDING", against_month=NXT, instalment=1500),
]
with open(os.path.join(LA, "ledger.jsonl"), "w") as fh:
    fh.writelines(json.dumps(r) + "\n" for r in rows)

REG = os.path.join(S, "A_register.db")
if os.path.exists(REG):
    os.remove(REG)
con = sqlite3.connect(REG)
con.execute("CREATE TABLE locked_run (ym TEXT PRIMARY KEY, total_payout INTEGER NOT NULL, report_html TEXT NOT NULL, "
            "locked_by TEXT NOT NULL, locked_ts TEXT NOT NULL, unlocked_by TEXT, unlocked_ts TEXT, unlock_reason TEXT, "
            "status TEXT NOT NULL DEFAULT 'locked')")


def s3(people):
    trs = "<tr><th>Name</th></tr>"
    for nm, base, adv, net in people:
        vals = [base, adv] + [0] * 16 + [net]
        trs += "<tr><td><b>%s</b></td>%s</tr>" % (nm, "".join("<td class='n'>%s</td>" % "{:,}".format(v) for v in vals))
    return "<html><table class='s3t'>%s</table></html>" % trs


con.execute("INSERT INTO locked_run(ym,total_payout,report_html,locked_by,locked_ts) VALUES(?,?,?,?,?)",
            (M2, 3260 + 8000, s3([("Walk Staff", 10500, 7000, 3260), ("Walk Other", 9000, 0, 8000)]), "walk", TS))
con.execute("INSERT INTO locked_run(ym,total_payout,report_html,locked_by,locked_ts) VALUES(?,?,?,?,?)",
            (M1, -980 + 8400, s3([("Walk Staff", 10500, 8500, -980), ("Walk Other", 9000, 0, 8400)]), "walk", TS))
con.commit()
con.close()

L = load(LA, CSV, REG, "A")
print("[A] Surendra's shape, made up")
if not check(hasattr(L, "month_book"), "the ledger has the month-by-month statement"):
    print("RED: no month blocks (the S609 file)")
    sys.exit(1)
book = {b["ym"]: b for b in L.month_book("Walk Staff")}
check(sorted(book) == sorted([M2, M1, M]), "three months: %s" % sorted(book))
b2, b1, b0 = book.get(M2, {}), book.get(M1, {}), book.get(M, {})
check(b2.get("cut_total") == 7000 and b2.get("remaining") == 6000, "%s: cut 7000, remaining 6000" % M2)
check([t["rs"] for t in b2.get("taken", [])] == [2000, 2000, 3000, 3000, 3000],
      "%s: the five advances taken (the reversed duplicate and the rejected one are not)" % M2)
check(b1.get("cut_total") == 8500 and b1.get("remaining") == 4000, "%s: cut 8500, remaining 4000" % M1)
check(b0.get("state") == "running" and b0.get("cut_total") == 7980 and b0.get("remaining") == 5000,
      "%s (running): to be cut 7980, remaining after 5000 (2000 + the 21st's 3000)" % M)
check(b2.get("salary", {}).get("net") == 3260 and b1.get("salary", {}).get("net") == -980,
      "salary from the locked runs: paid 3260, then -980")
app = L.create_app()
L.save_users({"walk": {"role": "checker", "salt": "00", "pw": "x", "active": True}})
C = app.test_client()
with C.session_transaction() as s:
    s["u"] = "walk"
page = C.get("/ledger/statement?staff=Walk+Staff").data.decode()
t = text(page)
check("Advance remaining now: Rs 12,980" in t, "top box: Advance remaining now Rs 12,980")
check("Advance remaining after" in t and "Total advance outstanding" not in t, "the owner's word: 'Advance remaining'")
check("Base Rs 10,500 - advances Rs 7,000 - leave, late & fines Rs 240 = paid Rs 3,260" in t,
      "%s salary adds up: 10,500 - 7,000 - 240 = paid 3,260" % M2)
check("Base Rs 10,500 - advances Rs 8,500 - leave, late & fines Rs 2,980 = paid Rs 0 - short by Rs 980" in t,
      "%s salary adds up: 10,500 - 8,500 - 2,980 = Rs 0, short by Rs 980" % M1)
check("To be cut at month end Rs 7,980" in t and "Advance remaining after the close Rs 5,000" in t,
      "running month: Rs 7,980 to be cut, Rs 5,000 after")
check("cleared" in t and "Rs 1,000 left on it" in t, "each cut says what it did to its advance")
check("will clear it" in t, "the running month says 'will clear it', not 'cleared'")
check("see the advance of 01" in t and "the same amount" in t, "the short salary points to the same-amount advance")
check("contra entry" not in t and "reversing entry" in t, "the footer in plain words")
check("cut from ONE monthly amount" in t and "to be cut in" in t, "the one-monthly-amount rule is said; future cuts say 'to be cut'")
check("Every advance" in t and "settled " in t, "every advance, one line each, with when it settled")
check("<details" in page and "Technical entries" in t and "Running net counts APPROVED" in t,
      "the old ledger lines are kept, closed, under Technical entries")
pos = [page.find("<b style='font-size:16px'>" + L._month_words(m)) for m in (M2, M1, M)]
check(all(p >= 0 for p in pos) and pos == sorted(pos), "months run oldest first")
lb = L.month_book("Walk Loan")
prev, okc = 0, True
for b in lb:
    okc = okc and b["remaining"] == prev + sum(x["rs"] for x in b["taken"]) + b["cap_total"] - b["rec_total"]
    prev = b["remaining"]
check(okc and lb and lb[0]["ym"] == M2 and lb[0]["remaining"] == 15000,
      "a loan cut before its date: shown from its first cut, remaining 15,000 (%s)" % [(b["ym"], b["remaining"]) for b in lb])
mineL = L.plan_for_staff("Walk Loan", L.month_plan())
outL = sum(x["balance"] for x in L.open_advances() if x["issue"]["staff"] == "Walk Loan")
pL = text(C.get("/ledger/statement?staff=Walk+Loan").data.decode())
check(mineL.get("interest") == 1000 and lb[-1]["remaining"] == outL - (mineL["take"] - 1000)
      and ("Advance remaining after %s: %s" % (L._month_words(M), L._rs(lb[-1]["remaining"]))) in pL,
      "interest is not advance: the top box and the running month agree (%s)" % lb[-1]["remaining"])
nx = L._month_words(NXT)
check(("from %s salary" % nx) in pL and ("to be cut in %s %s" % (nx[:3], NXT[:4])) in pL,
      "an advance against %s salary says so, and 'to be cut in %s'" % (nx, nx[:3]))
check("Rs 1,000 taken off the loan" in pL and "Rs -1000" not in pL.split("Technical entries")[0], "a negative correction reads 'taken off the loan'")
check("from %s salary" % L._month_words(M1) in t, "a quota advance says which month's salary it comes from")
one = text(C.get("/ledger/statement?staff=Walk+Staff&m=%s" % M1).data.decode())
check(L._month_words(M1) in one and ("%s (running)" % L._month_words(M)) not in one, "a chosen month shows that month")


# ------------------------------------------------------------------ S614 (D753): what the remaining is made of
print("[A2] S614: the top section's make-up and New entry's position box")
if not check(hasattr(L, "advance_makeup") and hasattr(L, "entry_position"), "the ledger names what the remaining is made of"):
    print("RED: no make-up (the S612 file)")
    sys.exit(1)
MW, NW = L._month_words(M), L._month_words(NXT)


def topbox(tt):
    i = tt.find("Advance remaining after %s:" % MW)
    j = tt.find("what the month-end close will take", i)
    return tt[i:j] if i >= 0 and j > i else ""


def adds_up(m, nm):
    """the make-up lines (what is left after the close) add to the top box's 'Advance remaining after'."""
    pl = m.month_plan()
    mine = m.plan_for_staff(nm, pl)
    outst = sum(x["balance"] for x in m.open_advances() if x["issue"]["staff"] == nm)
    want = max(0, outst - (mine["take"] - mine.get("interest", 0)))
    got = sum(x["left"] for x in m.advance_makeup(nm, pl))
    return got == want, got, want


tb = topbox(t)
check(("Rs 3,000 - advance of 21 %s - from %s salary" % (L._dmy(M + "-21")[3:], NW)) in tb,
      "Surendra's shape: 'Rs 3,000 - advance of 21 %s - from %s salary' under 'remaining after'" % (L._dmy(M + "-21")[3:], NW))
check(("Rs 2,000 - left on the advance of %s (Rs 3,000) - from the monthly amount of Rs 2,000, oldest first - next at the %s close"
       % (L._dmy(M2 + "-17"), NW)) in tb,
      "'Rs 2,000 - left on the advance of 17 ... - from the monthly amount of Rs 2,000, oldest first - next at the %s close'" % NW)
check("The lines under 'To be cut' are what the month-end close will take" in t, "the note says it is about the 'To be cut' lines")
check("Advance remaining after %s: Rs 5,000" % MW in tb and tb.count(" - ") >= 4 and "980" not in tb.split("Rs 5,000", 1)[1],
      "the list names only what is left after the close (cleared ones are not in it)")
for nm in ("Walk Staff", "Walk Loan", "Walk Sched", "Walk Small", "Walk Other"):
    ok_, got_, want_ = adds_up(L, nm)
    check(ok_, "%s: the lines add up to 'remaining after' (%s = %s)" % (nm, got_, want_))
tl = topbox(pL)
check("left on the loan of" in tl and "a loan: Rs 5,000 a month, of which Rs 1,000 is interest" in tl
      and "Rs 1,000 of the cut is interest, so what is owed falls by Rs 4,000" in tl
      and ("from %s salary" % NW) in tl, "a loan names its interest apart; its later advance says '%s salary'" % NW)
tsc = topbox(text(C.get("/ledger/statement?staff=Walk+Sched").data.decode()))
check(("Rs 8,000 - left on the advance of %s (Rs 12,000) - by the agreed schedule - next Rs 4,000 in %s" % (L._dmy(M1 + "-10"), NW)) in tsc,
      "an agreed schedule says its next step (Rs 4,000 in %s)" % NW)
tsm = topbox(text(C.get("/ledger/statement?staff=Walk+Small").data.decode()))
check("Rs 1,000 - left on the advance of" in tsm and "part held at the %s close" % MW in tsm,
      "an advance the salary cannot bear says what is held")
check(topbox(text(C.get("/ledger/statement?staff=Walk+Other").data.decode())).count("<li") == 0,
      "a person with nothing open has no list")
ep = C.get("/ledger/").data.decode()
mP = re.search(r"var P = (\{.*?\});\n", ep)
mA = re.search(r"var A = (\{.*?\});\n", ep)
P = json.loads(mP.group(1).replace("<\\/", "</")) if mP else {}
A = json.loads(mA.group(1)) if mA else {}
ws = P.get("Walk Staff", {})
op = [text(x) for x in ws.get("open", [])]
check(len(op) == 5, "New entry: Walk Staff's five open advances, one line each (%d)" % len(op))
check(any(("21 %s . Rs 3,000 . Rs 3,000 left . from %s salary" % (L._dmy(M + "-21")[3:], NW)) in x for x in op),
      "New entry: '21 ... . Rs 3,000 . Rs 3,000 left . from %s salary'" % NW)
check(any(("Rs 1,000 at the %s close, then Rs 2,000 left - from the monthly amount of Rs 2,000, oldest first" % MW) in x for x in op),
      "New entry: the 17th's 'Rs 1,000 at the %s close, then Rs 2,000 left'" % MW)
check(any("cut in full at the %s close" % MW in x for x in op), "New entry: an advance cleared at this close says so")
check(any("Rs 1,000 left . the last Rs 1,000 cut at the %s close" % MW in x for x in op),
      "New entry: a part-paid advance cleared now says 'the last Rs 1,000 cut'")
check(ws.get("pendm", {}).get(NXT) == 1500 and "waiting for approval)" in ep and "over the ceiling by" in ep,
      "New entry: the booking says what of it is waiting, and a booking over the ceiling says by how much")
check(text(ws.get("cut", "")).strip() == "Rs 7,980" and ws.get("cut_month") == MW, "New entry: 'The %s close will cut: Rs 7,980'" % MW)
check([text(x) for x in ws.get("pend", [])] == ["%s . Rs 1,500" % L._dmy(M + "-20")], "New entry: the advance waiting for approval")
aw = A.get("Walk Staff", {})
check(aw.get("taken", {}).get(NXT) == 4500 and aw.get("ceiling") == 5200,
      "New entry: booked against %s Rs 4,500 (3,000 + 1,500 waiting) of a Rs 5,200 ceiling" % NXT)
wl = [text(x) for x in P.get("Walk Loan", {}).get("open", [])]
check(any("off the loan at the %s close (+ Rs 1,000 interest)" % MW in x for x in wl), "New entry: the loan's interest is named apart")
check("Walk Other" in P and P["Walk Other"].get("open") == [], "New entry: a person with nothing open is 'No open advance'")
check("Already booked against" in ep and "room under the ceiling" in ep and 'addEventListener("change", staffpos)' in ep,
      "New entry: the box says the month's booking and the room, and follows the chosen month")


def js_ok(html_page):
    """every inline script parses (node --check), when node is on this machine; None = no node."""
    node = shutil.which("node")
    if not node:
        return None
    for sc in re.findall(r"<script>(.*?)</script>", html_page, re.S):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
            fh.write(sc)
        r_ = subprocess.run([node, "--check", fh.name], capture_output=True, text=True)
        os.remove(fh.name)
        if r_.returncode != 0:
            return False
    return True


L.save_users({"walk": {"role": "checker", "salt": "00", "pw": "x", "active": True},
              "walkm": {"role": "maker_full", "salt": "00", "pw": "x", "active": True}})
CM = app.test_client()
with CM.session_transaction() as s_:
    s_["u"] = "walkm"
mp = CM.get("/ledger/").data.decode()
check("var P = {};" in mp and '"loan"' not in mp.split("var P =")[1].split(";")[0],
      "F-973: a maker's page carries 'var P = {};' and no balances")
jc, jm = js_ok(ep), js_ok(mp)
if jc is None:
    print("  --   the page scripts: no node on this machine (checked in the rehearsal)")
else:
    check(jc and jm, "the doctor's and the maker's New entry scripts both parse")

# ------------------------------------------------------------------ Part B
if a.live_ledger:
    print("[B] scratch copies of the live ledger and staff register")
    LB = os.path.join(S, "B_ledger")
    shutil.rmtree(LB, ignore_errors=True)
    shutil.copytree(a.live_ledger, LB)
    RB = os.path.join(S, "B_register.db")
    src = sqlite3.connect("file:%s?mode=ro" % a.live_register, uri=True)
    dst = sqlite3.connect(RB)
    src.backup(dst)
    dst.close()
    src.close()
    LBm = load(LB, a.staff_csv, RB, "B")
    sal = LBm.locked_salaries()
    con = sqlite3.connect(RB)
    locked = dict(con.execute("SELECT ym,total_payout FROM locked_run WHERE status='locked'").fetchall())
    con.close()
    check(all(int(round(sum(v["net"] for v in sal[ym].values()))) == int(locked[ym]) for ym in sal),
          "every locked month read (%d of %d) adds up to its locked payout" % (len(sal), len(locked)))
    appB = LBm.create_app()
    LBm.save_users({"walkb": {"role": "checker", "salt": "00", "pw": "x", "active": True}})
    CB = appB.test_client()
    with CB.session_transaction() as s:
        s["u"] = "walkb"
    bad, chain_bad, top_bad, n = [], [], [], 0
    for nm in LBm.staff_names():
        n += 1
        r = CB.get("/ledger/statement?staff=" + nm)
        if r.status_code != 200 or "advances and salary" not in r.data.decode():
            bad.append(nm)
            continue
        bk = LBm.month_book(nm)
        prev = 0
        for b in bk:
            exp = prev + sum(x["rs"] for x in b["taken"]) + b["cap_total"] - b["rec_total"]
            if b["remaining"] != exp:
                chain_bad.append("%s %s: %s vs %s" % (nm, b["ym"], b["remaining"], exp))
                for x in LBm.load_ledger():           # explain it on screen: the rows of that month (no names but staff)
                    if x["staff"] == nm and ((x.get("closed_month") or "") == b["ym"] or (x.get("date_from") or "")[:7] == b["ym"]):
                        print("      row %s %s %s date %s closed %s of %s" % (x["id"][-6:], x["category"], x["amount"],
                              x.get("date_from"), x.get("closed_month"), (x.get("contra_of") or "")[-6:]))
            prev = b["remaining"]
        if bk and bk[-1]["state"] == "running":
            pl = LBm.month_plan()
            mine = LBm.plan_for_staff(nm, pl)
            outst = sum(x["balance"] for x in LBm.open_advances() if x["issue"]["staff"] == nm)
            want = max(0, outst - (mine["take"] - mine.get("interest", 0)))
            if bk[-1]["remaining"] != want:
                top_bad.append("%s: %s vs %s" % (nm, bk[-1]["remaining"], want))
    mk_bad, ep_bad = [], []
    for nm in LBm.staff_names():
        ok_, got_, want_ = adds_up(LBm, nm)
        if not ok_:
            mk_bad.append("%s: %s vs %s" % (nm, got_, want_))
    epB = CB.get("/ledger/").data.decode()
    mPB = re.search(r"var P = (\{.*?\});\n", epB)
    PB = json.loads(mPB.group(1).replace("<\\/", "</")) if mPB else None
    if PB is None:
        ep_bad.append("no position data on the page")
    else:
        vw = LBm.loans_view(LBm.load_ledger(), LBm.month_plan()["month"])
        nopen = {d["staff"]: sum(1 for x in d["tranches"] if x["open"]) for d in vw["staff"]}
        for nm in LBm.staff_names():
            if len((PB.get(nm) or {}).get("open", [])) != nopen.get(nm, 0):
                ep_bad.append("%s: %s lines vs %s open" % (nm, len((PB.get(nm) or {}).get("open", [])), nopen.get(nm, 0)))
    check(not mk_bad, "every person's make-up lines add up to the top box's 'remaining after'%s" % ((": " + "; ".join(mk_bad[:4])) if mk_bad else ""))
    check(not ep_bad and CB.get("/ledger/").status_code == 200,
          "New entry answers, one line per open advance for every person%s" % ((": " + "; ".join(ep_bad[:4])) if ep_bad else ""))
    jB = js_ok(epB)
    if jB is not None:
        check(jB, "New entry's script parses on the live shape")
    check(not bad, "every staff member's page answers (%d people)%s" % (n, (": " + ", ".join(bad)) if bad else ""))
    check(not chain_bad, "each month's remaining = previous + taken + added - recovered%s" % ((": " + "; ".join(chain_bad[:4])) if chain_bad else ""))
    check(not top_bad, "the running month's remaining = the top box%s" % ((": " + "; ".join(top_bad[:4])) if top_bad else ""))
    shutil.rmtree(LB, ignore_errors=True)
    os.remove(RB)

print("")
print("WALK S614: %d passed, %d failed" % (len(passed), len(failed)))
print("GREEN" if not failed else "RED")
sys.exit(0 if not failed else 1)
