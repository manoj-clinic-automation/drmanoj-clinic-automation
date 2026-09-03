#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clinic_upi_check.py -- S223: the clinic's online money against the bank's UPI feed, as a CHECK.

THE OWNER, 04-Sep-2026, on why the bank is almost always higher than our lines:
    "The counter is marking mode wrong. A bill paid by UPI gets recorded as Cash. That would
     produce exactly this shape -- bank always higher, never lower -- agree, but checks are a
     part of system and a note in report too"

So this is the report, plus a check that files what it finds where his existing exception screens
already look: `recon_exception`, kind `docterz_vs_upi`. No new table, no new screen, no new
vocabulary -- it sits beside `upi_vs_statement`, `line_sum_vs_day_total` and `missing_day`.

WHY THE COUNTER IS THE LEADING EXPLANATION, AND HOW THAT WAS ESTABLISHED
  The other candidate was card money hiding in the feed. It was checked, not assumed. The ICICI
  MPR is an ACQUIRER file -- 22 columns including Mode of Payment, Scheme Name, Card Type, Card
  Number -- so card COULD have been in it, and `finance_upi.py` ends its mode read with `or "UPI"`,
  which would silently relabel a card row whose Mode cell was blank. Both were tested on the box:
  across all 1,115 ingested transactions every mode is UPI, and in the six newest statements read
  directly the Mode column is present and populated (`Mode of Payment: {UPI: 40}`,
  `Card Type: {'': 40}`). **The fallback is not firing, and there is no card in this feed.**
  The clinic's POS card takings settle somewhere that never reaches this box.

  That leaves the counter. A bill paid by UPI but rung as Cash makes our UPI figure too low and
  the bank's right -- bank above ours, never below, which is the shape observed on 31 of 33
  differing days. **And it means the day's declared CASH is overstated by the same amount**, which
  is the part that matters at the drawer.

WHAT IS DELIBERATELY NOT COMPARED, each named on the report rather than hidden:
  * CARD -- not in this feed at all (above). Unreconciled by nature today.
  * RAZORPAY -- portal consultations settle to Yes Bank and are notified by email; they are in
    Docterz and NOT in the MPR, so they push OURS above the bank. `bank_statement_line` is empty,
    so that channel is unreconciled too.
  * WALLET and PATIENT APP -- not cash, but not established to settle through this same report.
  * CASH -- no bank feed exists for it.

  Of the clinic's four money-in channels, ONE is reconcilable today. A check that does not say so
  turns its own blind spots into accusations.

HEALING (F-275). A day that later agrees is CLOSED, with the reason recorded. Nothing here shouts
forever: every run re-decides every day in the window.

    /root/wa/venv/bin/python3 -B clinic_upi_check.py                 report only, writes nothing
    /root/wa/venv/bin/python3 -B clinic_upi_check.py --write         file and heal exceptions
"""
import argparse
import datetime as dt
import sqlite3
import sys

ONLINE = "Online Payment"
KIND = "docterz_vs_upi"
UNIT = "clinic"
HIGH_P = 200000          # Rs 2,000
MED_P = 50000            # Rs 500


def _sev(d):
    a = abs(d)
    return "high" if a >= HIGH_P else ("medium" if a >= MED_P else "low")


def day_figures(con, d, legs_table):
    split_ids, leg_online = set(), 0
    if legs_table:
        for r in con.execute("SELECT clinic_id, tender, amount_p FROM clinic_day_tender "
                             "WHERE business_date=?", (d,)):
            split_ids.add(r["clinic_id"])
            if r["tender"] == ONLINE:
                leg_online += r["amount_p"]
    out = dict(online=leg_online, card=0, wallet=0, app=0, cash=0, unresolved=0)
    for r in con.execute("SELECT clinic_id, mode, amount_p FROM clinic_day_line "
                         "WHERE business_date=? AND section IN (?,?,?)",
                         (d, "consult", "xray", "proc")):
        m, p = (r["mode"] or "").strip(), r["amount_p"] or 0
        if r["clinic_id"] in split_ids:
            continue
        if m == ONLINE:
            out["online"] += p
        elif m in ("Debit Card", "Credit Card"):
            out["card"] += p
        elif m == "Wallet":
            out["wallet"] += p
        elif m == "Patient APP":
            out["app"] += p
        elif m == "Cash":
            out["cash"] += p
        else:
            out["unresolved"] += p
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="/root/finance/finance.db")
    ap.add_argument("--days", type=int, default=60)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    con = sqlite3.connect(a.db)
    con.row_factory = sqlite3.Row
    have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type=:t",
                                      {"t": "table"})}
    for t in ("clinic_day_line", "clinic_day_revenue", "upi_txn", "recon_exception"):
        if t not in have:
            sys.exit("REFUSING: %s is not in this database" % t)
    legs = "clinic_day_tender" in have
    bank_upto = con.execute("SELECT MAX(txn_date) m FROM upi_txn WHERE unit=?",
                            (UNIT,)).fetchone()["m"]
    if not bank_upto:
        sys.exit("REFUSING: upi_txn holds nothing for unit=%s" % UNIT)

    days = [r[0] for r in con.execute(
        "SELECT business_date FROM clinic_day_revenue ORDER BY business_date DESC LIMIT ?",
        (a.days,))]
    days.reverse()
    print("bank feed runs to %s. Days after that are NOT compared -- the statement has not "
          "arrived, which is not a discrepancy.\n" % bank_upto)
    print("%-12s %10s %10s %9s  %-8s %s" % ("day", "ours(UPI)", "bank(UPI)", "diff", "severity",
                                            "not compared"))
    print("-" * 92)
    opened = healed = skipped = agreed = 0
    tot_o = tot_b = 0
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for d in days:
        if d > bank_upto:
            skipped += 1
            print("%-12s %10s %10s %9s  %-8s statement not arrived" % (d, "-", "-", "-", "-"))
            continue
        f = day_figures(con, d, legs)
        ours = f["online"]
        bank = con.execute("SELECT COALESCE(SUM(amount_p),0) s FROM upi_txn "
                           "WHERE unit=? AND txn_date=?", (UNIT, d)).fetchone()["s"]
        diff = bank - ours                       # positive = the bank has more than our lines
        tot_o += ours
        tot_b += bank
        aside = []
        for k, lbl in (("card", "card"), ("wallet", "wallet"), ("app", "app"),
                       ("unresolved", "SPLIT LEGS MISSING")):
            if f[k]:
                aside.append("%s %d" % (lbl, f[k] // 100))
        sev = _sev(diff) if diff else "-"
        print("%-12s %10d %10d %9d  %-8s %s"
              % (d, ours // 100, bank // 100, diff // 100, sev, ", ".join(aside) or "-"))
        if not a.write:
            if diff == 0:
                agreed += 1
            continue
        if diff == 0:
            agreed += 1
            cur = con.execute(
                "UPDATE recon_exception SET status='resolved', "
                "resolution='the day now agrees with the bank feed', closed_at=? "
                "WHERE unit=? AND business_date=? AND kind=? AND status='open'",
                (now, UNIT, d, KIND))
            healed += cur.rowcount
            continue
        # The two directions mean OPPOSITE things and must never share a sentence.
        if f["unresolved"]:
            detail = ("the bank and our lines differ by Rs %d. Rs %d of this day is a SPLIT bill "
                      "whose legs were never recovered, so part of that gap is a missing INPUT, "
                      "not missing money. Re-run push_day_tenders.py on the clinic PC before "
                      "reading anything into this day." % (abs(diff) // 100, f["unresolved"] // 100))
            sev = "low"
        elif bank == 0 and ours > 0:
            # A THIRD state, and it is not the Razorpay one. The clinic plainly took online money
            # and the feed has not a single transaction for that date -- that is a statement that
            # never arrived or never ingested, not money that went missing. Measured over the
            # first 59 days: five such days, all in June and early July.
            detail = ("the bank feed has NO clinic transaction at all for this date, while our "
                      "lines show Rs %d of online money. That is a MISSING STATEMENT, not missing "
                      "money -- check whether the MPR for this date was ever received and "
                      "ingested. Nothing should be read into the amount until it is."
                      % (ours // 100))
            sev = "medium"
        elif diff > 0:
            detail = ("bank UPI is Rs %d ABOVE what the Docterz lines call online. The likely "
                      "cause is a bill paid by UPI and rung at the counter as CASH -- in which "
                      "case no money is missing and this day's declared CASH is overstated by "
                      "about the same amount, which is what to check at the drawer. Card is not "
                      "in this comparison: the ICICI feed carries none." % (diff // 100))
        else:
            detail = ("our lines are Rs %d ABOVE the bank UPI feed, which HAS transactions for "
                      "this date -- the opposite direction, and "
                      "the uncommon one. Two known causes, neither a loss: a RAZORPAY portal "
                      "consultation (it is in Docterz, settles to Yes Bank, and never appears in "
                      "the MPR), or this day's statement not yet ingested. Check the Razorpay "
                      "email for this date before treating it as anything else."
                      % (abs(diff) // 100))
        con.execute("INSERT OR IGNORE INTO recon_exception "
                    "(unit, business_date, kind, severity, status, detail, opened_at, shout_count) "
                    "VALUES (?,?,?,?, 'open', ?, ?, 0)", (UNIT, d, KIND, sev, detail, now))
        cur = con.execute(
            "UPDATE recon_exception SET severity=?, detail=?, expected_p=?, actual_p=?, diff_p=? "
            "WHERE unit=? AND business_date=? AND kind=? AND status='open'",
            (sev, detail, ours, bank, diff, UNIT, d, KIND))
        opened += 1 if cur.rowcount else 0
    if a.write:
        con.commit()
    print("-" * 92)
    print("%-12s %10d %10d %9d" % ("TOTAL", tot_o // 100, tot_b // 100, (tot_b - tot_o) // 100))
    print("\ndays compared %d · agreeing to the rupee %d · not yet settled %d"
          % (len(days) - skipped, agreed, skipped))
    if a.write:
        print("exceptions filed or refreshed: %d · closed because the day now agrees: %d"
              % (opened, healed))
    else:
        print("REPORT ONLY -- nothing was written. Add --write to file these as exceptions.")
    print("""
NOTE, and it is part of the finding, not a disclaimer:
  * The bank being ABOVE our lines is the expected shape of a bill paid by UPI and rung as CASH.
    Where that is the cause, no money is missing -- the day's CASH figure is overstated by the
    same amount, and that is what to check at the drawer.
  * CARD is not in this comparison. The ICICI MPR carries none: all 1,115 ingested transactions
    read UPI, and the six newest statements were opened directly to confirm the Mode column is
    populated rather than defaulting. The clinic's POS card money settles where this box cannot
    see it.
  * RAZORPAY portal consultations settle to Yes Bank and reach the owner by email only. They are
    in Docterz and not in the MPR, so they push OURS ABOVE the bank -- the opposite direction.
  * Of the clinic's four ways of taking money -- cash, UPI, card, Razorpay -- only UPI can be
    reconciled today.""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
