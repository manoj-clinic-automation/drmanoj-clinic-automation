#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s819.py -- kit S819 (S453, F-1367): no interest on a loan in a month unless principal comes off it that month.

    python3 walk_s819.py --code DIR --old DIR --scratch DIR [--live-ledger DIR --staff-csv FILE]

--code is the folder holding the staff_ledger.py under test; --old the folder holding the S614 file it was built on
(85e2ab51).  Every ledger here is MADE UP, in a scratch folder: made-up people ("Walk ..."), made-up figures, months
of 2031.  Nothing real is opened.  Each case is closed with BOTH files and the rows the close writes are compared.

 a  the salary carries the whole instalment ................ the same rows as before
 b  short of the instalment, but not of the interest ....... before: interest alone, or interest and a part;
                                                             now: nothing taken, one hold row (THE CONTROL)
 c  nothing left in the salary .............................. the whole instalment held, no interest
 d  the loan's last month (less owed than the instalment) ... carried: closes as before; not carried: held whole
 e  the owner's skip, and his defer (free / penalty / waived)  the same rows as before, short salary or not
 f  interest-free advances only, short salary ............... the same rows as before (a part is still taken)
 g  a schedule and a month's own advance eat the capacity ... their rows as before; the loan held whole;
                                                             what the waterfall asked of the capacity is given back
 h  two months, the first held .............................. the loan ends exactly one month later; interest once
                                                             in every month principal came off, and in no other
 i  the dry run (S609) ...................................... the same rows the close then writes; writes nothing
 j  every surface that forecasts or states the month ........ a held month: nothing cut, no interest shown, the
                                                             loan standing -- and it equals what the close then does
 k  kept as before, on purpose (noted in the README) ........ an instalment equal to the flat interest
 L  (on the box) a scratch COPY of the live ledger ......... the next close, by both files: the same rows for
                                                             everyone except a person whose loan instalment is
                                                             now held whole; nobody pays interest beside a hold;
                                                             every page answers.  Counts only -- no name, no figure.
Exit 0 = GREEN.  Pointed at the S614 file (--code = --old) it goes RED: that is the control.
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--code", required=True)
ap.add_argument("--old", required=True)
ap.add_argument("--scratch", required=True)
ap.add_argument("--live-ledger", default="")
ap.add_argument("--staff-csv", default="")
a = ap.parse_args()
S = os.path.abspath(a.scratch)
if S.startswith("/root/staff_ledger") or S.startswith("/root/staff_register"):
    print("RED: refusing to walk in a live folder")
    sys.exit(1)
os.makedirs(os.path.join(S, "att"), exist_ok=True)
os.environ.update(NTFY_URL="", LEDGER_DIR=os.path.join(S, "boot"), STAFF_CSV=os.path.join(S, "boot.csv"),
                  ATT_BASE=os.path.join(S, "att"), STAFF_REGISTER_DB=os.path.join(S, "no_register.db"))
passed, failed = [], []


def check(cond, label):
    """cond: a value, or a function (an error inside it is a FAIL, so the control can be counted on the old file)."""
    try:
        ok = bool(cond() if callable(cond) else cond)
    except Exception as ex:                                       # noqa: BLE001
        ok = False
        label += "   [%s: %s]" % (type(ex).__name__, str(ex)[:70])
    (passed if ok else failed).append(label)
    print(("  ok   " if ok else "  FAIL ") + label)
    return ok


def load(folder, tag):
    spec = importlib.util.spec_from_file_location("sl_" + tag, os.path.join(folder, "staff_ledger.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


N = load(a.code, "new")            # the file under test
O = load(a.old, "old")             # the S614 file
print("under test: v%s   ·   built on: v%s" % (N.APP_VERSION, O.APP_VERSION))

PREV, M1, M2, M3, M4, M5 = "2031-03", "2031-04", "2031-05", "2031-06", "2031-07", "2031-08"
TS = "2099-01-01T00:00:00"
USERS = {"walk": {"role": "checker", "salt": "00", "pw": "x", "active": True}}
INT = 1000


def row(i, cat, amount, date, **kw):
    r = {"id": i, "ts_entry": TS, "maker": kw.pop("maker", "walk"), "staff": kw.pop("staff", "Walk Loan"),
         "category": cat, "date_from": date, "date_to": date, "days": 0, "amount": amount,
         "instalment": kw.pop("instalment", None), "narration": kw.pop("narration", ""), "self_flag": False,
         "direct": True, "status": kw.pop("status", "APPROVED"), "checker": "walk", "ts_decision": TS,
         "contra_of": kw.pop("contra_of", None), "closed_month": kw.pop("closed_month", ""), "interest": False}
    r.update(kw)
    return r


def anchor():                       # one row stamped to March 2031, so the next close is April 2031 on any day
    return row("z0", "NIGHT_DUTY", 200, PREV + "-12", staff="Walk Other", closed_month=PREV)


def loan(i, staff, amount=20000, inst=5000):
    return row(i, "ADVANCE_ISSUE", amount, PREV + "-05", staff=staff, instalment=inst, interest=True,
               closed_month=PREV, narration="made-up loan")


def free(i, staff, amount, inst, day="06"):
    return row(i, "ADVANCE_ISSUE", amount, PREV + "-" + day, staff=staff, instalment=inst, closed_month=PREV,
               narration="made-up advance")


def fine(i, staff, rs, month):      # a made-up deduction: it is what leaves the salary short
    return row(i, "FINE_ADHOC", -rs, month + "-10", staff=staff, narration="made-up deduction")


def fresh(m, tag, rows, people):
    d = os.path.join(S, tag)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    with open(os.path.join(d, "ledger.jsonl"), "w") as fh:
        fh.writelines(json.dumps(r) + "\n" for r in rows)
    csvp = os.path.join(d, "sm.csv")
    with open(csvp, "w") as fh:
        fh.write("user_id,name,department,base_salary,allowed_offs,wd_start,wd_end,sun_start,sun_end,active,"
                 "timing_note,sunday_group,minutes_exempt\n")
        for k, (nm, base) in enumerate(people):
            fh.write("%d,%s,Clinic,%s,2,09:00,21:00,09:00,15:00,Y,,A,N\n" % (9001 + k, nm, base))
    m.LEDGER_DIR, m.STAFF_CSV = d, csvp
    return d


def norm(rows):
    return [(r["staff"], r["category"], int(r["amount"]), r.get("contra_of") or "", r.get("date_from"),
             r.get("closed_month"), r.get("narration") or "") for r in rows]


def run(m, tag, rows, people, months):
    """A fresh made-up ledger; for each (month, rows to add first): the dry run, then the close. What each wrote."""
    d = fresh(m, tag, rows, people)
    led = os.path.join(d, "ledger.jsonl")
    out = []
    for month, extra in months:
        for r in extra:
            m.append_ledger(dict(r))
        n0 = len(m.load_ledger())
        raw = open(led, "rb").read()
        dry = m.close_month({}, "preview", month, dry=True) or []
        quiet = open(led, "rb").read() == raw and not os.path.exists(os.path.join(d, "approved_adjustments_%s.csv" % month))
        m.close_month(USERS, "walk", month)
        out.append({"month": month, "dry": norm(dry), "real": norm(m.load_ledger()[n0:]), "quiet": quiet})
    return out


def both(tag, rows, people, months):
    return run(N, tag + "_new", rows, people, months), run(O, tag + "_old", rows, people, months)


def amts(rows, cat, ref=None):
    return [-r[2] for r in rows if r[1] == cat and (ref is None or r[3] == ref)]


def holds(rows):
    return [r for r in rows if r[1] == "CAPACITY_HOLD"]


def whole(rows):
    return [r for r in rows if r[1] == "CAPACITY_HOLD" and "WHOLE instalment HELD" in r[6]]


def bal(m, iid):
    return next((x["balance"] for x in m.open_advances() if x["issue"]["id"] == iid), 0)


def cap_left(m, month, staff):
    """What the close's own capacity store holds for `staff` when the close ends (read off a dry run)."""
    got = {}

    def prof(frame, event, arg):
        if event == "return" and frame.f_code.co_name == "close_month":
            got["cap"] = dict(frame.f_locals.get("_cap") or {})
    sys.setprofile(prof)
    try:
        m.close_month({}, "preview", month, dry=True)
    finally:
        sys.setprofile(None)
    return got.get("cap", {}).get(staff)


def text(html):
    t = re.sub(r"<[^>]+>", " ", html)
    for k, v in (("&mdash;", "-"), ("&middot;", "."), ("&rarr;", "->"), ("&amp;", "&"), ("&nbsp;", " "), ("&minus;", "-")):
        t = t.replace(k, v)
    return re.sub(r"\s+", " ", t)


ALL = []                            # every close of this walk, for (i)
P1 = [("Walk Loan", 30000), ("Walk Other", 9000)]

# ------------------------------------------------------------------ a
print("[a] the salary carries the whole instalment")
n, o = both("a1", [anchor(), loan("L1", "Walk Loan")], P1, [(M1, [])])
ALL += n
check(n[0]["real"] == o[0]["real"], "plenty left: the close writes the same rows as before")
check(amts(n[0]["real"], "LOAN_INTEREST") == [INT] and amts(n[0]["real"], "ADVANCE_INSTALMENT") == [4000]
      and not holds(n[0]["real"]), "... Rs 1,000 interest and Rs 4,000 off the loan, nothing held")
n, o = both("a2", [anchor(), loan("L1", "Walk Loan"), fine("f1", "Walk Loan", 25000, M1)], P1, [(M1, [])])
ALL += n
check(n[0]["real"] == o[0]["real"] and amts(n[0]["real"], "ADVANCE_INSTALMENT") == [4000] and not holds(n[0]["real"]),
      "exactly the instalment left (Rs 5,000): carried, the same rows as before")
n, o = both("a3", [anchor(), loan("L1", "Walk Nobase")], [("Walk Other", 9000)], [(M1, [])])
ALL += n
check(n[0]["real"] == o[0]["real"] and amts(n[0]["real"], "LOAN_INTEREST") == [INT],
      "no base salary on file (the capacity gate is off): the same rows as before")

# ------------------------------------------------------------------ b  (THE CONTROL)
print("[b] short of the instalment, but not of the interest")
for tag, left, was in (("b1", 3000, "interest and a part"), ("b2", 1000, "interest alone"), ("b3", 400, "a part of the interest")):
    n, o = both(tag, [anchor(), loan("L1", "Walk Loan"), fine("f1", "Walk Loan", 30000 - left, M1)], P1, [(M1, [])])
    ALL += n
    check(sum(amts(o[0]["real"], "LOAN_INTEREST")) == min(INT, left)
          and sum(amts(o[0]["real"], "ADVANCE_INSTALMENT")) == max(0, left - INT),
          "Rs %s left -- before: %s was taken (the fault, shown on the S614 file)" % ("{:,}".format(left), was))
    check(not amts(n[0]["real"], "LOAN_INTEREST"), "Rs %s left -- now: NO interest is taken" % "{:,}".format(left))
    check(not amts(n[0]["real"], "ADVANCE_INSTALMENT") and not [r for r in n[0]["real"] if r[1] == "LOAN_CAPITALISE"],
          "Rs %s left -- now: nothing is cut and nothing is added to the loan" % "{:,}".format(left))
    check(len(n[0]["real"]) == 1 and len(whole(n[0]["real"])) == 1 and n[0]["real"][0][3] == "L1"
          and n[0]["real"][0][2] == 0 and n[0]["real"][0][6].startswith("Rs 5000 "),
          "Rs %s left -- now: ONE hold row, against the loan, for the whole Rs 5,000" % "{:,}".format(left))
    check(bal(N, "L1") == 20000, "Rs %s left -- now: the loan stands at Rs 20,000" % "{:,}".format(left))
check(lambda: all(w in whole(n[0]["real"])[0][6] for w in ("No interest", "nothing is cut", "one month longer")),
      "the hold row says it in plain words: no interest, nothing cut, one month longer")

# ------------------------------------------------------------------ c
print("[c] nothing left in the salary")
n, o = both("c1", [anchor(), loan("L1", "Walk Loan"), fine("f1", "Walk Loan", 30000, M1)], P1, [(M1, [])])
ALL += n
check(not amts(n[0]["real"], "LOAN_INTEREST") and not amts(n[0]["real"], "ADVANCE_INSTALMENT")
      and not amts(o[0]["real"], "LOAN_INTEREST") and not amts(o[0]["real"], "ADVANCE_INSTALMENT"),
      "nothing left: nothing taken, before and now")
check(len(n[0]["real"]) == 1 and len(whole(n[0]["real"])) == 1 and bal(N, "L1") == 20000,
      "nothing left: one hold row for the whole instalment, the loan standing")

# ------------------------------------------------------------------ d
print("[d] the loan's last month")
last = [anchor(), loan("L1", "Walk Loan"),
        row("p1", "ADVANCE_INSTALMENT", -17500, PREV, contra_of="L1", closed_month=PREV, maker="SYSTEM",
            narration="made-up earlier instalments (balance after: 2500)")]
n, o = both("d1", last, P1, [(M1, [])])
ALL += n
check(n[0]["real"] == o[0]["real"] and amts(n[0]["real"], "LOAN_INTEREST") == [INT]
      and amts(n[0]["real"], "ADVANCE_INSTALMENT") == [2500] and bal(N, "L1") == 0,
      "Rs 3,500 owed, carried: Rs 1,000 interest + Rs 2,500, the loan closed -- the same rows as before")
n, o = both("d2", last + [fine("f1", "Walk Loan", 27000, M1)], P1, [(M1, [])])
ALL += n
check(len(n[0]["real"]) == 1 and len(whole(n[0]["real"])) == 1 and n[0]["real"][0][6].startswith("Rs 3500 ")
      and bal(N, "L1") == 2500, "Rs 3,500 owed, Rs 3,000 left: held whole (Rs 3,500), no interest, Rs 2,500 standing")
check(amts(o[0]["real"], "LOAN_INTEREST") == [INT], "... before, the S614 file took Rs 1,000 interest there")
lastf = last + [free("A1", "Walk Loan", 3000, 5000)]
n, o = both("d3", lastf, P1, [(M1, [])])
ALL += n
check(n[0]["real"] == o[0]["real"] and amts(n[0]["real"], "ADVANCE_INSTALMENT", "A1") == [1500] and bal(N, "L1") == 0,
      "last month with an interest-free advance behind, carried: the rest flows on to it -- the same rows as before")
n, o = both("d4", lastf + [fine("f1", "Walk Loan", 26000, M1)], P1, [(M1, [])])
ALL += n
check(len(n[0]["real"]) == 1 and len(whole(n[0]["real"])) == 1 and bal(N, "L1") == 2500 and bal(N, "A1") == 3000,
      "... not carried (Rs 4,000 left of Rs 5,000): held whole, nothing off the loan or the advance behind it")

# ------------------------------------------------------------------ e
print("[e] the owner's skip and defer")
skip = row("s1", "LOAN_SKIP", 0, M1, contra_of="L1", narration="made-up skip")


def defer(pen, waived):
    return row("d1", "ADVANCE_DEFER", 0, M1, contra_of="L1", narration="made-up defer", defer_penalty=pen,
               penalty_waived=waived, skip_month=False)


for tag, extra, what in (("e1", [skip], "a skipped month (Rs 1,000 added, D250)"),
                         ("e2", [defer(False, False)], "a deferred month, free"),
                         ("e3", [defer(True, False)], "a deferred month, the third of the year (Rs 1,000 penalty)"),
                         ("e4", [defer(True, True)], "a deferred month, the penalty waived")):
    for short in (False, True):
        rows_ = [anchor(), loan("L1", "Walk Loan"), free("A1", "Walk Loan", 6000, 3000)] + extra
        if short:
            rows_.append(fine("f1", "Walk Loan", 28000, M1))
        n, o = both(tag + ("s" if short else "f"), rows_, P1, [(M1, [])])
        ALL += n
        check(n[0]["real"] == o[0]["real"] and not amts(n[0]["real"], "LOAN_INTEREST") and not whole(n[0]["real"]),
              "%s, %s: the same rows as before" % (what, "salary short" if short else "salary full"))
check(lambda: [r[2] for r in n[0]["real"] if r[1] == "LOAN_CAPITALISE"] == [], "... a waived penalty adds nothing")

# ------------------------------------------------------------------ f
print("[f] interest-free advances only, short salary")
n, o = both("f1", [anchor(), free("A1", "Walk Loan", 9000, 3000), free("A2", "Walk Loan", 4000, 2000, "09"),
                   fine("f1", "Walk Loan", 28000, M1)], P1, [(M1, [])])
ALL += n
check(n[0]["real"] == o[0]["real"], "Rs 2,000 left of a Rs 3,000 instalment: the same rows as before")
check(amts(n[0]["real"], "ADVANCE_INSTALMENT", "A1") == [2000] and len(holds(n[0]["real"])) == 1
      and not whole(n[0]["real"]), "... a part (Rs 2,000) is still taken, the rest held the old way")

# ------------------------------------------------------------------ g
print("[g] a schedule and the month's own advance ahead of the loan")
sched = row("C1", "ADVANCE_ISSUE", 8000, PREV + "-07", staff="Walk Loan", closed_month=PREV,
            schedule=[{"month": M1, "amount": 4000}, {"month": M2, "amount": 4000}])
quota = row("Q1", "ADVANCE_ISSUE", 3000, M1 + "-03", staff="Walk Loan", instalment=3000, against_month=M1)
grow = [anchor(), loan("L1", "Walk Loan"), sched, quota, fine("f1", "Walk Loan", 20000, M1)]
n, o = both("g1", grow, P1, [(M1, [])])
ALL += n
check([r for r in n[0]["real"] if r[3] in ("C1", "Q1")] == [r for r in o[0]["real"] if r[3] in ("C1", "Q1")]
      and amts(n[0]["real"], "ADVANCE_INSTALMENT", "C1") == [4000] and amts(n[0]["real"], "ADVANCE_INSTALMENT", "Q1") == [3000],
      "the schedule's Rs 4,000 and the month's own Rs 3,000: the same rows as before")
check([r for r in n[0]["real"] if r[3] == "L1"] == whole(n[0]["real"]) and len(whole(n[0]["real"])) == 1
      and bal(N, "L1") == 20000, "Rs 3,000 left for a Rs 5,000 instalment: the loan held whole, no interest")
check(amts(o[0]["real"], "LOAN_INTEREST", "L1") == [INT], "... before, the S614 file took Rs 1,000 interest there")
fresh(N, "g2_new", grow, P1)
check(lambda: cap_left(N, M1, "Walk Loan") == 3000,
      "what the waterfall asked of the capacity is given back (Rs 3,000 stands in the close's store)")
fresh(N, "g3_new", [anchor(), loan("L1", "Walk Loan"), fine("f1", "Walk Loan", 20000, M1)], P1)
check(lambda: cap_left(N, M1, "Walk Loan") == 5000, "a carried month still spends it (Rs 10,000 less the Rs 5,000 instalment)")

# ------------------------------------------------------------------ h
print("[h] two months, the first held")
hl = [anchor(), loan("L1", "Walk Loan", 9000, 5000)]
ha = run(N, "h_carried", hl, P1, [(M1, []), (M2, []), (M3, []), (M4, []), (M5, [])])
hb = run(N, "h_held", hl + [fine("f1", "Walk Loan", 29000, M1)], P1, [(M1, []), (M2, []), (M3, []), (M4, []), (M5, [])])
bal_b = bal(N, "L1")
ALL += ha + hb


def months_with(res, cat):
    return [x["month"] for x in res if amts(x["real"], cat, "L1")]


def tot(res, cat):
    return sum(sum(amts(x["real"], cat, "L1")) for x in res)


check(months_with(ha, "ADVANCE_INSTALMENT") == [M1, M2, M3], "both carried: principal comes off in April, May, June 2031")
check(hb[0]["real"] == whole(hb[0]["real"]) and len(hb[0]["real"]) == 1, "April held: one hold row and nothing else")
check(months_with(hb, "ADVANCE_INSTALMENT") == [M2, M3, M4] and bal_b == 0,
      "April held: the loan ends in July 2031 -- exactly one month later than June")
check(months_with(hb, "LOAN_INTEREST") == months_with(hb, "ADVANCE_INSTALMENT"),
      "interest is taken in exactly the months principal comes off, and in no other")
check(all(amts(x["real"], "LOAN_INTEREST", "L1") in ([], [INT]) for x in hb)
      and tot(hb, "LOAN_INTEREST") == INT * len(months_with(hb, "ADVANCE_INSTALMENT")),
      "interest once a month: total interest Rs 3,000 = 3 months of principal x Rs 1,000")
check(tot(hb, "LOAN_INTEREST") == tot(ha, "LOAN_INTEREST") and tot(hb, "ADVANCE_INSTALMENT") == tot(ha, "ADVANCE_INSTALMENT") == 9000,
      "the held month costs nothing: the same interest and the same Rs 9,000 principal as the carried run")
check(not [r for x in hb for r in x["real"] if r[1] == "LOAN_CAPITALISE"], "nothing is ever added to the loan for a held month")

# ------------------------------------------------------------------ j  (before i: it needs its own ledger)
print("[j] every surface that forecasts or states the month")
PJ = [("Walk Held", 30000), ("Walk Carried", 30000), ("Walk Part", 30000), ("Walk Other", 9000)]
jrows = [anchor(),
         loan("LH", "Walk Held"), fine("fh", "Walk Held", 27000, M1),
         loan("LC", "Walk Carried"),
         free("AP", "Walk Part", 9000, 3000), fine("fp", "Walk Part", 28000, M1)]
MW, SH = "April 2031", "Apr 2031"


def surfaces(m, tag):
    """What every forecasting function says of April 2031 BEFORE the close -- for the three made-up people."""
    fresh(m, tag, jrows, PJ)
    rows = m.load_ledger()
    plan = m.month_plan()
    g = {"plan": plan, "rows": rows}
    for nm in ("Walk Held", "Walk Carried", "Walk Part"):
        view = m.loans_view(rows, plan["month"], nm)
        trs = [dict((k, v) for k, v in t.items() if k != "held_now") for t in view["staff"][0]["tranches"]]
        g[nm] = {"mine": m.plan_for_staff(nm, plan, rows), "book": m.month_book(nm, rows, {}),
                 "makeup": m.advance_makeup(nm, plan, rows), "makeup_html": m.makeup_html(nm, plan, rows),
                 "entry": m.entry_position(nm, plan, rows), "view": view, "tranches": trs,
                 "due": view["staff"][0]["due"], "loans_html": m.loans_html(view, "checker", nm, [x for x, _ in PJ])}
    app = m.create_app()
    m.save_users(USERS)
    c = app.test_client()
    with c.session_transaction() as s_:
        s_["u"] = "walk"
    ver = "v" + m.APP_VERSION
    for nm in ("Walk Held", "Walk Carried", "Walk Part"):
        q = nm.replace(" ", "+")
        g[nm]["statement"] = c.get("/ledger/statement?staff=" + q).data.decode().replace(ver, "v")
        g[nm]["loans_page"] = c.get("/ledger/loans?m=%s&staff=%s" % (M1, q)).data.decode().replace(ver, "v")
    ep = c.get("/ledger/").data.decode()
    mP = re.search(r"var P = (\{.*?\});\n", ep)
    g["P"] = json.loads(mP.group(1).replace("<\\/", "</")) if mP else {}
    g["client"], g["m"] = c, m
    return g


gn = surfaces(N, "j_new")
go = surfaces(O, "j_old")
check(gn["plan"]["month"] == M1 and not gn["plan"]["closed"] and not gn["plan"]["error"], "the next close is April 2031 (made-up)")
for nm, what in (("Walk Carried", "a carried loan"), ("Walk Part", "an interest-free advance, part held")):
    check(all(gn[nm][k] == go[nm][k] for k in ("mine", "book", "makeup", "makeup_html", "entry", "tranches", "due", "loans_html")),
          "%s: the plan, the month blocks, the make-up, New entry's box and the Loans view read as before" % what)
    check(gn[nm]["statement"] == go[nm]["statement"] and gn[nm]["loans_page"] == go[nm]["loans_page"],
          "%s: the Statement page and the Loans page are the same, byte for byte" % what)
check(lambda: gn["P"]["Walk Carried"] == go["P"]["Walk Carried"] and gn["P"]["Walk Part"] == go["P"]["Walk Part"],
      "New entry's page data for both is the same as before")
h = gn["Walk Held"]
hrows = [r for r in gn["plan"]["rows"] if r["staff"] == "Walk Held"]
check(len(hrows) == 1 and hrows[0]["category"] == "CAPACITY_HOLD" and "WHOLE instalment HELD" in hrows[0]["narration"],
      "held month, the close's own dry run: one hold row, no interest row, no instalment row")
check(h["mine"]["take"] == 0 and h["mine"]["interest"] == 0 and h["mine"]["held"] == 5000,
      "the plan: to be cut Rs 0, interest Rs 0, held Rs 5,000")
check(lambda: len(h["mine"]["lines"]) == 1 and "whole loan instalment is held" in h["mine"]["lines"][0]["what"]
      and "no interest" in h["mine"]["lines"][0]["what"] and "one month longer" in h["mine"]["lines"][0]["what"],
      "the plan's line: 'the whole loan instalment is held this month ... no interest ... one month longer'")
bk = h["book"][-1]
check(bk["ym"] == M1 and bk["state"] == "running" and bk["cut_total"] == 0 and bk["rec_total"] == 0
      and bk["cap_total"] == 0 and bk["remaining"] == 20000,
      "the month block: to be cut Rs 0, nothing added, Rs 20,000 remaining after the close")
check(lambda: len(bk["cuts"]) == 1 and bk["cuts"][0]["kind"] == "hold" and "whole loan instalment of Rs 5,000 is held" in bk["cuts"][0]["what"]
      and "no interest" in bk["cuts"][0]["what"] and not any("interest on the loan" in c_["what"] for c_ in bk["cuts"]),
      "the month block's line: the whole Rs 5,000 is held, no interest -- never 'interest on the loan'")
mk = h["makeup"]
check(lambda: len(mk) == 1 and mk[0]["cut"] == 0 and mk[0]["interest"] == 0 and mk[0]["left"] == mk[0]["left_now"] == 20000,
      "what the remaining is made of: Rs 0 cut, Rs 0 interest, Rs 20,000 left")
check(lambda: "the whole instalment is held at the %s close" % MW in mk[0]["when"] and "no interest this month" in mk[0]["when"]
      and "part held" not in mk[0]["when"], "... and it says the whole instalment is held, not 'part held'")
check("of the cut is interest" not in h["makeup_html"] and "whole instalment is held" in h["makeup_html"],
      "the statement's list: no 'of the cut is interest' line; the loan's line says held")
check(lambda: "Rs&nbsp;0" in h["entry"]["cut"] and "interest" not in h["entry"]["cut"] and len(h["entry"]["open"]) == 1
      and "whole instalment is held" in h["entry"]["open"][0] and "interest)" not in h["entry"]["open"][0],
      "New entry's box: the April close will cut Rs 0; the loan's line says held, no '(+ interest)'")
tr = h["view"]["staff"][0]["tranches"][0]
check(lambda: tr["held_now"] is True and tr["due_this_month"] == 0 and tr["balance"] == 20000 and h["due"] == 0,
      "the Loans view: falling due Rs 0, held this month, balance Rs 20,000")
check("held this month" in h["loans_html"] and "nothing cut, no interest" in text(h["loans_html"])
      and "Rs 0</b> in" not in h["loans_html"], "the Loans page says 'held this month - nothing cut, no interest', not 'Rs 0 in 2031-04'")
st = text(h["statement"])
i0 = st.find("Advances - Walk Held")
top = st[i0:st.find("what the month-end close will take", i0)]
check("Advance remaining now: Rs 20,000" in top and ("To be cut from %s salary: Rs 0" % MW) in top
      and ("Advance remaining after %s: Rs 20,000" % MW) in top,
      "the Statement's top box: remaining now Rs 20,000, to be cut Rs 0, remaining after Rs 20,000")
check("whole loan instalment is held this month" in top and "interest on the loan" not in top and "of the cut is interest" not in top,
      "the Statement's top box says the whole instalment is held -- and shows no interest as taken")
blocks = st[st.find("what the month-end close will take"):st.find("Technical entries")]
check("To be cut at month end Rs 0" in blocks and "Advance remaining after the close Rs 20,000" in blocks
      and "interest on the loan" not in blocks and ("held in %s - nothing cut, no interest" % SH) in blocks,
      "the Statement's April block and 'Every advance': Rs 0 to be cut, Rs 20,000 after, 'held in Apr 2031'")
check("held this month" in h["loans_page"], "the Loans page (as served) says 'held this month'")
check(lambda: "whole instalment is held" in gn["P"]["Walk Held"]["open"][0] and "Rs&nbsp;0" in gn["P"]["Walk Held"]["cut"],
      "New entry (as served): the loan's line says held; the close will cut Rs 0")
# ... and then the close does exactly that
fresh(N, "j_new", jrows, PJ)
N.save_users(USERS)
n0 = len(N.load_ledger())
N.close_month(USERS, "walk", M1)
N.close_report(M1)
wrote = [r for r in N.load_ledger()[n0:] if r["staff"] == "Walk Held"]
check(norm(wrote) == norm(hrows), "the close then writes exactly the row the forecast showed")
check(-sum(r["amount"] for r in wrote if r["category"] in ("ADVANCE_INSTALMENT", "LOAN_INTEREST")) == h["mine"]["take"] == 0
      and bal(N, "LH") == bk["remaining"] == 20000,
      "forecast = close: Rs 0 cut; the loan stands at Rs 20,000, as the forecast said")
rep = N.load_close_report(M1) or ""
check("Walk Held: Rs 5000 — the WHOLE loan instalment HELD" in rep and "No interest was taken" in rep,
      "the close report names it: the whole loan instalment held, no interest taken")
bc = [b for b in N.month_book("Walk Held", None, {}) if b["ym"] == M1]
check(lambda: bc[0]["state"] == "closed" and bc[0]["cut_total"] == 0 and bc[0]["remaining"] == 20000
      and "Rs 5,000 was held" in bc[0]["cuts"][0]["what"] and "no interest" in bc[0]["cuts"][0]["what"],
      "after the close the April block reads: cut Rs 0, the whole Rs 5,000 was held, no interest, Rs 20,000 at month end")
nx = N.plan_for_staff("Walk Held", N.month_plan())
check(N.month_plan()["month"] == M2 and nx["take"] == 5000 and nx["interest"] == INT,
      "May 2031's forecast: the full Rs 5,000 (Rs 1,000 of it interest) -- the loan simply runs one month longer")
cv = N.loans_view(N.load_ledger(), M1, "Walk Held")["staff"][0]["tranches"][0]
check(lambda: cv["held_now"] is True and cv["balance"] == 20000, "the Loans view of closed April still says it was held")
before = {r["id"]: r for r in jrows}
after = {r["id"]: r for r in N.load_ledger() if r["id"] in before}
check(all({k: v for k, v in after[i].items() if k != "closed_month"} == {k: v for k, v in before[i].items() if k != "closed_month"}
          for i in before), "every row that was already in the ledger is untouched (the close only stamps the month)")

# ------------------------------------------------------------------ k
print("[k] kept as before, on purpose")
n, o = both("k1", [anchor(), loan("L1", "Walk Loan", 20000, 1000)], P1, [(M1, [])])
ALL += n
check(n[0]["real"] == o[0]["real"] and amts(n[0]["real"], "LOAN_INTEREST") == [INT] and not amts(n[0]["real"], "ADVANCE_INSTALMENT"),
      "an instalment equal to the flat interest (Rs 1,000), carried: the same rows as before -- NOTED in the README, not changed")

# ------------------------------------------------------------------ i
print("[i] the dry run (S609)")
check(lambda: ALL[0]["dry"] == ALL[0]["real"] and len(ALL[0]["real"]) == 2, "a carried month: the dry run's rows are the rows the close writes")
check(lambda: ALL[3]["dry"] == ALL[3]["real"] and len(whole(ALL[3]["real"])) == 1, "a held month: the dry run's rows are the rows the close writes")
check(all(x["dry"] == x["real"] for x in ALL), "every close of this walk (%d): dry run = close" % len(ALL))
check(all(x["quiet"] for x in ALL), "the dry run writes nothing: no row, no stamp, no file")

# ------------------------------------------------------------------ L  (on the box only)
if a.live_ledger:
    print("[L] live shape: a scratch COPY of the live ledger (the live one is only read)")
    LB = os.path.join(S, "L_ledger")
    shutil.rmtree(LB, ignore_errors=True)
    shutil.copytree(a.live_ledger, LB)
    for m_ in (N, O):
        m_.LEDGER_DIR, m_.STAFF_CSV = LB, a.staff_csv
    raw_l = open(os.path.join(LB, "ledger.jsonl"), "rb").read()
    pn, po = N.month_plan(), O.month_plan()
    check(pn["month"] == po["month"] and pn["error"] == po["error"] and pn["closed"] == po["closed"],
          "both files plan the same next close%s" % ((" (the plan says: %s)" % pn["error"][:60]) if pn["error"] else ""))
    names = sorted({r["staff"] for r in pn["rows"]} | {r["staff"] for r in po["rows"]})
    heldw, differ, beside = 0, 0, 0
    for nm in names:
        rn = norm([r for r in pn["rows"] if r["staff"] == nm])
        ro = norm([r for r in po["rows"] if r["staff"] == nm])
        wn = whole(rn)
        if wn:
            heldw += 1
            rest = [r for r in rn if r not in wn]
            gone = [r for r in ro if r not in rest]
            if (len(wn) != 1 or any(r not in ro for r in rest)
                    or any(not (r[1] == "LOAN_INTEREST" or (r[1] == "ADVANCE_INSTALMENT" and "auto instalment" in r[6])
                                or (r[1] == "CAPACITY_HOLD" and "waterfall instalment HELD" in r[6])) for r in gone)):
                differ += 1
        elif rn != ro:
            differ += 1
        hold_refs = {r[3] for r in rn if r[1] == "CAPACITY_HOLD"}
        if any(r[1] == "LOAN_INTEREST" and r[3] in hold_refs for r in rn):
            beside += 1
    check(differ == 0, "the next close: the same rows as before for everyone, except a loan instalment now held whole "
                       "(%d people in the plan, %d held whole, %d differ otherwise)" % (len(names), heldw, differ))
    check(beside == 0, "nobody pays interest on a loan whose instalment is held (%d)" % beside)
    # S819 second reader: this kit's rule is for the month that CANNOT carry the instalment. A carried month still
    # takes the flat interest with no principal off that loan when a person has two loans with interest in the
    # waterfall, or a head instalment not above the flat interest. Counted here; names and figures never printed.
    wf_ = {}
    for a_ in N.open_advances():                      # the close's own snapshot, in waterfall order
        if N.advance_lane(a_) in ("loan", "waterfall"):
            wf_.setdefault(a_["issue"]["staff"], []).append(a_)
    odd = 0
    for advs_ in wf_.values():
        k_ = sum(1 for a_ in advs_ if a_["interest"])
        if k_ >= 2 or (k_ == 1 and int(advs_[0]["instalment"]) <= N.INTEREST_RS):
            odd += 1
    check(odd == 0, "no loan shape where a carried month would take interest without principal "
                    "(%d people with a loan in the waterfall, %d of that shape)" % (len(wf_), odd))
    appL = N.create_app()
    N.save_users({"walkl": {"role": "checker", "salt": "00", "pw": "x", "active": True}})
    cl_ = appL.test_client()
    with cl_.session_transaction() as s_:
        s_["u"] = "walkl"
    bad = 0
    people = N.staff_names()
    for nm in people:
        r_ = cl_.get("/ledger/statement", query_string={"staff": nm})
        if r_.status_code != 200 or "advances and salary" not in r_.data.decode():
            bad += 1
    check(bad == 0 and people, "every person's Statement page answers (%d people, %d did not)" % (len(people), bad))
    check(cl_.get("/ledger/loans").status_code == 200 and cl_.get("/ledger/").status_code == 200
          and cl_.get("/ledger/loans", query_string={"m": pn["month"]}).status_code == 200,
          "the Loans page and New entry answer")
    check(open(os.path.join(LB, "ledger.jsonl"), "rb").read() == raw_l, "nothing was written to the copy's ledger")
    shutil.rmtree(LB, ignore_errors=True)

print("")
print("WALK S819: %d passed, %d failed" % (len(passed), len(failed)))
print("GREEN" if not failed else "RED")
sys.exit(0 if not failed else 1)
