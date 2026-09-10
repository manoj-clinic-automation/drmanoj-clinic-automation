#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ledger_statement.py  —  the staff ledger, with the noise taken out
Dr. Manoj Agarwal Clinic · Session 237 · built for the August 2026 salary close

WHY THIS EXISTS
  The ledger is append-only: nothing is ever edited, and a correction is made by
  posting a CONTRA that reverses the original. That is right, and it is also why
  the raw ledger is hard to read -- a corrected entry appears three times over
  (the original, the contra, and the replacement) and the running total means
  nothing until you have paired them up by hand.

⭐ AND THERE IS A SECOND, WORSE REASON, WHICH IS NOT OBVIOUS

  The field `contra_of` carries TWO completely different meanings:

    1. on a CONTRA row          -> "this REVERSES row X"
    2. on a system row          -> "this BELONGS TO advance X"
       (ADVANCE_INSTALMENT, LOAN_INTEREST, LOAN_CAPITALISE, LOAN_SKIP)

  So every monthly instalment, every interest charge and every skip carries a
  `contra_of` and LOOKS like a contra when you read the file or the page. On a
  loan running eight months that is eight rows that appear to be reversals and
  are nothing of the kind.

  **This tool separates the two.** A row is only treated as a reversal if it
  actually reverses something: same staff, same category, opposite amount, and
  approved -- which is the same test `open_advances()` uses in staff_ledger.py.

WHAT IT DOES
  Reads the ledger, removes the reversed pairs, keeps the system rows attached
  to the advance they belong to, and prints a plain statement per person:
  what was issued, what has been recovered month by month, what interest was
  capitalised, and what is still owed.

  The arithmetic is NOT reinvented. It is the ledger's own:
      balance = amount + capitalised - recovered          (open_advances)
      recovered = sum of -amount over APPROVED ADVANCE_INSTALMENT rows
                  whose contra_of is this advance         (advance_recovered)

IT WRITES NOTHING. It opens the ledger read-only and prints. There is no
--write, no --fix, and no option that changes a byte.

RUN
  Everyone:                python3 ledger_statement.py
  One person:              python3 ledger_statement.py --staff Darpan
  For a month's close:     python3 ledger_statement.py --month 2026-08
  To a spreadsheet:        python3 ledger_statement.py --csv /root/ledger_2026-08.csv
  Prove it, no files:      python3 ledger_statement.py --selftest
"""

import argparse
import csv
import json
import os
import sys

LEDGER = os.environ.get("LEDGER_DIR", "/root/staff_ledger")
LEDGER_FILE = os.path.join(LEDGER, "ledger.jsonl")

# Straight from staff_ledger.py -- kept identical on purpose.
SYSTEM_CATS = {"ADVANCE_INSTALMENT", "LOAN_INTEREST", "LOAN_CAPITALISE", "LOAN_SKIP", "SALARY_PAID"}
SALARY_EXCLUDED = {"ADVANCE_ISSUE", "LOAN_CAPITALISE", "LOAN_SKIP", "PERK", "SALARY_PAID"}
LABEL = {
    "NIGHT_DUTY": "Night duty", "FINE_UNIFORM": "Uniform fine", "FINE_ICARD": "I-card fine",
    "LEAVE_APPROVED": "Approved leave", "ICARD_REPLACEMENT": "I-card replacement",
    "ADVANCE_ISSUE": "ADVANCE ISSUED", "FINE_ADHOC": "Ad-hoc fine", "PERK": "Perk",
    "OTHER": "Other adjustment", "ADVANCE_INSTALMENT": "instalment recovered",
    "LOAN_INTEREST": "loan interest", "LOAN_CAPITALISE": "interest added on skip",
    "LOAN_SKIP": "instalment SKIPPED", "SALARY_PAID": "salary paid",
}


def load(path=None):
    """Read the append-only ledger. Read-only, and it never dies on one bad line."""
    path = path or LEDGER_FILE
    rows, bad = [], 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                bad += 1
    return rows, bad


# ---------------------------------------------------------------------------
# The pure half -- no files. Everything here is selftested.
# ---------------------------------------------------------------------------
def is_reversal(row, rows_by_id):
    """Is this row a genuine CONTRA -- i.e. does it actually reverse its target?

    The test is the one staff_ledger.open_advances() uses: it points at a row,
    that row exists, same category, and the amounts cancel. A system row
    (instalment/interest/skip) points at its PARENT advance and is never a
    reversal, whatever its contra_of says."""
    tgt = row.get("contra_of") or ""
    if not tgt:
        return False
    if row.get("category") in SYSTEM_CATS:
        return False                       # a child of an advance, not a reversal
    o = rows_by_id.get(tgt)
    if o is None:
        return False
    return (o.get("category") == row.get("category")
            and (o.get("amount") or 0) == -(row.get("amount") or 0))


def classify(rows):
    """Split the ledger into what it really is.

    live      -- rows that still count
    reversed_ -- originals that a contra cancelled
    contras   -- the cancelling rows themselves
    rejected  -- never approved, never counted
    pending   -- awaiting a checker
    children  -- system rows attached to an advance (NOT contras)"""
    by_id = {r.get("id"): r for r in rows}
    contras = [r for r in rows if r.get("status") == "APPROVED" and is_reversal(r, by_id)]
    reversed_ids = {r["contra_of"] for r in contras}
    out = {"live": [], "reversed_": [], "contras": contras, "rejected": [], "pending": [],
           "children": []}
    for r in rows:
        st = r.get("status")
        if st == "REJECTED":
            out["rejected"].append(r); continue
        if st == "PENDING":
            out["pending"].append(r); continue
        if r in contras:
            continue
        if r.get("id") in reversed_ids:
            out["reversed_"].append(r); continue
        if r.get("category") in SYSTEM_CATS and (r.get("contra_of") or ""):
            out["children"].append(r)
        out["live"].append(r)
    return out


def recovered(issue_id, live):
    """Exactly staff_ledger.advance_recovered()."""
    return sum(-(r.get("amount") or 0) for r in live
               if r.get("category") == "ADVANCE_INSTALMENT" and r.get("contra_of") == issue_id)


def capitalised(issue_id, live):
    """Exactly staff_ledger.advance_capitalised()."""
    return sum((r.get("amount") or 0) for r in live
               if r.get("category") == "LOAN_CAPITALISE" and r.get("contra_of") == issue_id)


def advances_for(staff, live):
    """Every advance this person still has, with the ledger's own balance."""
    out = []
    for r in live:
        if r.get("category") != "ADVANCE_ISSUE":
            continue
        if staff and (r.get("staff") or "").strip().lower() != staff.strip().lower():
            continue
        rec = recovered(r["id"], live)
        cap = capitalised(r["id"], live)
        bal = (r.get("amount") or 0) + cap - rec
        out.append({
            "id": r["id"], "staff": r.get("staff"), "issued_on": r.get("date_from"),
            "amount": r.get("amount") or 0, "instalment": r.get("instalment") or r.get("amount") or 0,
            "interest": bool(r.get("interest")),
            "recovered": rec, "capitalised": cap, "balance": bal,
            "narration": r.get("narration") or "",
            "children": sorted([c for c in live if c.get("contra_of") == r["id"]
                                and c.get("category") in SYSTEM_CATS],
                               key=lambda c: (c.get("date_from") or "", c.get("ts_entry") or "")),
        })
    out.sort(key=lambda a: (not a["interest"], a["issued_on"] or "", a["id"]))
    return out


def staff_list(live):
    return sorted({(r.get("staff") or "").strip() for r in live if (r.get("staff") or "").strip()})


def month_lines(staff, live, month):
    """What this month's close actually took off the salary, by the ledger's own
    rule: APPROVED rows stamped closed_month == month, minus the categories that
    are not salary money. Same rule set as staff_ledger.month_adjustments()."""
    out = []
    for r in live:
        if r.get("closed_month") != month:
            continue
        if staff and (r.get("staff") or "").strip().lower() != staff.strip().lower():
            continue
        out.append(r)
    return sorted(out, key=lambda r: (r.get("staff") or "", r.get("category") or ""))


def rs(p):
    """The ledger keeps whole rupees, not paise."""
    return "{:,}".format(int(p or 0))


# ---------------------------------------------------------------------------
# Printing -- plain language, no jargon, nothing hidden.
# ---------------------------------------------------------------------------
def print_person(staff, live, month=None, show_cleared=False):
    advs = advances_for(staff, live)
    cleared = [a for a in advs if a["balance"] <= 0]
    if not show_cleared:
        advs = [a for a in advs if a["balance"] > 0]
    print("\n" + "=" * 78)
    print("  %s" % staff.upper())
    print("=" * 78)
    if not advs:
        print("  nothing owed")
    if cleared and not show_cleared:
        print("  (%d advance(s) fully cleared and not shown — add --all to see them)" % len(cleared))
    for a in advs:
        kind = "interest-bearing loan" if a["interest"] else "advance"
        print("\n  %s of Rs %s issued %s   (instalment Rs %s)"
              % (kind, rs(a["amount"]), a["issued_on"] or "?", rs(a["instalment"])))
        if a["narration"]:
            print("     \"%s\"" % a["narration"][:70])
        if not a["children"]:
            print("     nothing recovered yet")
        for c in a["children"]:
            amt = c.get("amount") or 0
            when = c.get("date_from") or c.get("closed_month") or ""
            tag = LABEL.get(c.get("category"), c.get("category"))
            if c.get("category") == "LOAN_SKIP":
                print("     %-10s %-26s        -" % (when, tag))
            else:
                print("     %-10s %-26s  Rs %9s" % (when, tag, rs(abs(amt))))
        print("     %-37s  Rs %9s" % ("recovered so far", rs(a["recovered"])))
        if a["capitalised"]:
            print("     %-37s  Rs %9s" % ("interest added on skipped months", rs(a["capitalised"])))
        print("     %-37s  Rs %9s   <<<" % ("STILL OWED", rs(a["balance"])))
    tot = sum(a["balance"] for a in advs if a["balance"] > 0)
    if len(advs) > 1:
        print("\n  TOTAL STILL OWED BY %s: Rs %s" % (staff.upper(), rs(tot)))
    if month:
        ml = month_lines(staff, live, month)
        print("\n  --- what %s's close took from this person's salary ---" % month)
        if not ml:
            print("      nothing")
        for r in ml:
            amt = r.get("amount") or 0
            mark = "" if r.get("category") not in SALARY_EXCLUDED else "   (not salary money)"
            print("      %-28s  Rs %9s%s" % (LABEL.get(r.get("category"), r.get("category")),
                                             rs(amt), mark))
    return tot


def print_noise(cl, bad):
    print("\n" + "-" * 78)
    print("  WHAT WAS TAKEN OUT SO THIS COULD BE READ")
    print("-" * 78)
    print("  %4d reversed entries hidden, with the %d contra rows that cancelled them"
          % (len(cl["reversed_"]), len(cl["contras"])))
    print("  %4d rows still awaiting a checker  (NOT counted anywhere below)" % len(cl["pending"]))
    print("  %4d rejected rows                  (never counted)" % len(cl["rejected"]))
    print("  %4d instalment / interest / skip rows that carry a `contra_of` and are"
          % len(cl["children"]))
    print("       NOT contras at all -- they belong to an advance. This is the thing")
    print("       that makes the raw ledger look like a mess.")
    if bad:
        print("  %4d unreadable line(s) in the file -- reported, not skipped silently" % bad)
    print("  %4d rows counted as live" % len(cl["live"]))
    if cl["pending"]:
        print("\n  ! the pending rows, because they will change these numbers when decided:")
        for r in cl["pending"][:10]:
            print("      %-12s %-22s Rs %-9s  %s" % (r.get("staff"), LABEL.get(r.get("category"), r.get("category")),
                                                     rs(r.get("amount")), (r.get("narration") or "")[:28]))


def write_csv(path, live, month):
    """One row per open advance, for pasting into the salary sheet."""
    advs = advances_for(None, live)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["staff", "issued_on", "advance_rs", "instalment_rs", "interest_bearing",
                    "recovered_rs", "capitalised_rs", "still_owed_rs", "narration"])
        n = 0
        for a in advs:
            if a["balance"] <= 0:
                continue
            w.writerow([a["staff"], a["issued_on"], a["amount"], a["instalment"],
                        "yes" if a["interest"] else "no", a["recovered"], a["capitalised"],
                        a["balance"], a["narration"]])
            n += 1
    return n


# ---------------------------------------------------------------------------
# selftest -- no files, no ledger.
# ---------------------------------------------------------------------------
def _row(**kw):
    r = {"id": kw.get("id", "x"), "staff": kw.get("staff", "Darpan"),
         "category": kw.get("category", "ADVANCE_ISSUE"), "amount": kw.get("amount", 0),
         "instalment": kw.get("instalment"), "status": kw.get("status", "APPROVED"),
         "contra_of": kw.get("contra_of", ""), "date_from": kw.get("date_from", "2026-08-01"),
         "closed_month": kw.get("closed_month", ""), "interest": kw.get("interest", False),
         "narration": kw.get("narration", ""), "ts_entry": kw.get("ts_entry", "2026-08-01T00:00")}
    return r


def selftest():
    checks = []

    def ck(name, got, want):
        checks.append((got == want, name, got, want))

    # --- the heart of it: an instalment is NOT a contra ---------------------
    issue = _row(id="A1", amount=15000, instalment=3000)
    inst = _row(id="I1", category="ADVANCE_INSTALMENT", amount=-3000, contra_of="A1",
                closed_month="2026-08", date_from="2026-08")
    by = {r["id"]: r for r in [issue, inst]}
    ck("an instalment is not a reversal", is_reversal(inst, by), False)
    ck("an advance with no contra is not reversed", is_reversal(issue, by), False)

    contra = _row(id="C1", category="ADVANCE_ISSUE", amount=-15000, contra_of="A1")
    ck("a real contra IS a reversal", is_reversal(contra, {r["id"]: r for r in [issue, contra]}), True)
    half = _row(id="C2", category="ADVANCE_ISSUE", amount=-5000, contra_of="A1")
    ck("a row that does not cancel is not a reversal",
       is_reversal(half, {r["id"]: r for r in [issue, half]}), False)
    ck("a contra pointing at nothing is not a reversal",
       is_reversal(_row(id="C3", amount=-1, contra_of="GONE"), {}), False)
    ck("a different category is not a reversal",
       is_reversal(_row(id="C4", category="OTHER", amount=-15000, contra_of="A1"),
                   {r["id"]: r for r in [issue]}), False)
    ck("interest is not a reversal",
       is_reversal(_row(id="X", category="LOAN_INTEREST", amount=-1000, contra_of="A1"), by), False)
    ck("a skip is not a reversal",
       is_reversal(_row(id="X", category="LOAN_SKIP", amount=0, contra_of="A1"), by), False)
    ck("capitalised interest is not a reversal",
       is_reversal(_row(id="X", category="LOAN_CAPITALISE", amount=1000, contra_of="A1"), by), False)

    # --- classify -----------------------------------------------------------
    rows = [issue, inst, contra]
    cl = classify(rows)
    ck("the contra is caught", len(cl["contras"]), 1)
    ck("the reversed original is set aside", [r["id"] for r in cl["reversed_"]], ["A1"])
    ck("the instalment is a child, not a contra", [r["id"] for r in cl["children"]], ["I1"])
    ck("a reversed advance is not live", [r["id"] for r in cl["live"]], ["I1"])

    clean = classify([issue, inst])
    ck("without a contra the advance stays live", sorted(r["id"] for r in clean["live"]), ["A1", "I1"])
    ck("nothing is reversed", clean["reversed_"], [])

    pend = _row(id="P1", status="PENDING", amount=5000)
    rej = _row(id="R1", status="REJECTED", amount=5000)
    c2 = classify([issue, inst, pend, rej])
    ck("pending is held apart", [r["id"] for r in c2["pending"]], ["P1"])
    ck("rejected is held apart", [r["id"] for r in c2["rejected"]], ["R1"])
    ck("neither is live", sorted(r["id"] for r in c2["live"]), ["A1", "I1"])

    # --- the arithmetic, and it must equal the ledger's own -----------------
    live = classify([issue, inst]) ["live"]
    ck("recovered counts the instalment", recovered("A1", live), 3000)
    ck("capitalised is zero without a skip", capitalised("A1", live), 0)
    a = advances_for("Darpan", live)[0]
    ck("balance = amount + capitalised - recovered", a["balance"], 12000)
    ck("the instalment is carried", a["instalment"], 3000)

    cap = _row(id="K1", category="LOAN_CAPITALISE", amount=1000, contra_of="A1", date_from="2026-07")
    live2 = classify([issue, inst, cap])["live"]
    ck("a skipped month's interest raises the balance",
       advances_for("Darpan", live2)[0]["balance"], 13000)
    ck("and is reported separately", advances_for("Darpan", live2)[0]["capitalised"], 1000)

    # a second, unrelated instalment must not be counted against this advance
    other = _row(id="A2", staff="Surendra", amount=13000, instalment=2000)
    oinst = _row(id="I2", staff="Surendra", category="ADVANCE_INSTALMENT", amount=-2000,
                 contra_of="A2", closed_month="2026-08")
    live3 = classify([issue, inst, other, oinst])["live"]
    ck("one person's instalment never touches another's", recovered("A1", live3), 3000)
    ck("Surendra's own balance", advances_for("Surendra", live3)[0]["balance"], 11000)
    ck("staff filter is case-insensitive", len(advances_for("darpan", live3)), 1)
    ck("no filter returns everybody's", len(advances_for(None, live3)), 2)
    ck("the staff list is found", staff_list(live3), ["Darpan", "Surendra"])

    # --- ordering: interest-bearing first, then oldest ----------------------
    old = _row(id="A0", amount=5000, date_from="2026-01-01")
    loan = _row(id="A3", amount=9000, date_from="2026-09-01", interest=True)
    order = [x["id"] for x in advances_for("Darpan", classify([old, loan, issue])["live"])]
    ck("an interest-bearing loan is recovered first", order[0], "A3")
    ck("then the oldest advance", order[1], "A0")

    # --- the month's close ---------------------------------------------------
    ml = month_lines("Darpan", classify([issue, inst])["live"], "2026-08")
    ck("the month shows the instalment", [r["id"] for r in ml], ["I1"])
    ck("a different month shows nothing", month_lines("Darpan", live, "2026-07"), [])
    ck("ADVANCE_ISSUE is not salary money", "ADVANCE_ISSUE" in SALARY_EXCLUDED, True)
    ck("an instalment IS salary money", "ADVANCE_INSTALMENT" in SALARY_EXCLUDED, False)

    # --- the categories match staff_ledger.py --------------------------------
    ck("system categories are the ledger's five", sorted(SYSTEM_CATS),
       ["ADVANCE_INSTALMENT", "LOAN_CAPITALISE", "LOAN_INTEREST", "LOAN_SKIP", "SALARY_PAID"])
    ck("rupee formatting", rs(1234567), "1,234,567")
    ck("a zero prints as 0", rs(0), "0")
    ck("None prints as 0", rs(None), "0")

    cleared_only = classify([_row(id="Z1", amount=1000, instalment=1000),
                             _row(id="Z2", category="ADVANCE_INSTALMENT", amount=-1000, contra_of="Z1")])["live"]
    ck("a cleared advance has a zero balance", advances_for("Darpan", cleared_only)[0]["balance"], 0)
    ck("advances_for still returns it (the filter is at print time)",
       len(advances_for("Darpan", cleared_only)), 1)

    fails = [c for c in checks if not c[0]]
    for ok, name, got, want in checks:
        if not ok:
            print("  FAIL  %-52s got %r want %r" % (name, got, want))
    print("selftest: %d checks, %d failures" % (len(checks), len(fails)))
    return 1 if fails else 0


def main():
    p = argparse.ArgumentParser(description="The staff ledger with the contra noise removed. Reads only.")
    p.add_argument("--staff", help="just this person (case-insensitive)")
    p.add_argument("--month", help="also show what this month's close took, e.g. 2026-08")
    p.add_argument("--csv", metavar="PATH", help="write the open advances to a spreadsheet file")
    p.add_argument("--file", default=LEDGER_FILE, help="the ledger (default %s)" % LEDGER_FILE)
    p.add_argument("--all", action="store_true", help="also show advances that are fully cleared")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        return selftest()
    if not os.path.exists(a.file):
        print("!! no ledger at %s" % a.file)
        print("   name it with --file, or set LEDGER_DIR.")
        return 1
    rows, bad = load(a.file)
    cl = classify(rows)
    live = cl["live"]
    print("STAFF LEDGER — read %d rows from %s" % (len(rows), a.file))
    print_noise(cl, bad)
    names = [a.staff] if a.staff else staff_list(live)
    grand = 0
    for n in names:
        grand += print_person(n, live, a.month, a.all)
    print("\n" + "=" * 78)
    print("  TOTAL STILL OWED, ALL STAFF: Rs %s" % rs(grand))
    print("=" * 78)
    if a.csv:
        n = write_csv(a.csv, live, a.month)
        print("\n  %d open advance(s) written to %s" % (n, a.csv))
    print("\n  (nothing was changed — this only reads)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
