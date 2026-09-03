#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clinic_upi_report.py -- S223: does the clinic's online money agree with the bank's UPI feed?

REPORT ONLY. It reads. It writes nothing, anywhere -- no table, no row, no file. Its whole job is
to answer, on real days, whether a comparison is worth building a screen around. Measure before you
design (S221); a screen built on an unmeasured comparison shouts at the owner every day and is
wrong every day.

WHAT IT COMPARES, AND WHY ONLY THIS

  ours   = the clinic's ONLINE PAYMENT money for a day, from the Docterz lines, with split bills
           resolved into their legs (that is what S223_SPLIT_LEGS recovered)
  bank   = SUM(upi_txn.amount_p) for unit='clinic' on the same date

THREE THINGS ARE DELIBERATELY NOT COMPARED, and each is named on the report rather than hidden:

  * CARD. Measured at the S223 open: every one of the 1,115 rows in upi_txn carries mode='UPI'.
    The merchant feed the clinic receives is a UPI settlement report; card settles on another rail
    and is not in it. So clinic card takings have NOTHING in this feed to match against -- and by
    the owner's own ruling ("third tender column ONLY IF the MPR names the rail") there is no third
    column, because the rail is not named.
  * WALLET and PATIENT APP. They are not cash, but neither is it established that they settle
    through this same UPI report. Until that is measured they are listed apart, not assumed in.
  * CASH. It is not in a bank feed at all.

THE DATE. `upi_txn.txn_date` is the day the money moved; the Docterz business date is the day the
patient was seen. They are the same day for a counter payment, and this report assumes nothing
else -- where they disagree, the difference shows up as a difference, which is the point.

    /root/wa/venv/bin/python3 -B clinic_upi_report.py [--days 45] [--db PATH]
"""
import argparse
import sqlite3
import sys

ONLINE = "Online Payment"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="/root/finance/finance.db")
    ap.add_argument("--days", type=int, default=45)
    a = ap.parse_args()
    con = sqlite3.connect(a.db)
    con.row_factory = sqlite3.Row

    have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type=:t",
                                      {"t": "table"})}
    for t in ("clinic_day_line", "upi_txn"):
        if t not in have:
            sys.exit("REFUSING: %s is not in this database" % t)
    legs = "clinic_day_tender" in have
    if not legs:
        print("NOTE: clinic_day_tender is absent -- split bills cannot be resolved into legs, so "
              "their online portion is unknown and every split day will read as a difference. "
              "That is a missing input, not a finding.\n")

    days = [r[0] for r in con.execute(
        "SELECT business_date FROM clinic_day_revenue ORDER BY business_date DESC LIMIT ?",
        (a.days,))]
    days.reverse()
    if not days:
        sys.exit("REFUSING: no days stored")

    print("%-12s %10s %10s %9s   %s" % ("day", "ours(UPI)", "bank(UPI)", "diff", "not compared"))
    print("-" * 78)
    agree = differ = 0
    tot_ours = tot_bank = 0
    rows_out = []
    for d in days:
        split_ids = set()
        leg_online = 0
        if legs:
            for r in con.execute("SELECT clinic_id, tender, amount_p FROM clinic_day_tender "
                                 "WHERE business_date=?", (d,)):
                split_ids.add(r["clinic_id"])
                if r["tender"] == ONLINE:
                    leg_online += r["amount_p"]
        line_online = card = wallet = app = cash = other = 0
        for r in con.execute("SELECT clinic_id, mode, amount_p FROM clinic_day_line "
                             "WHERE business_date=? AND section IN (?,?,?)",
                             (d, "consult", "xray", "proc")):
            m, p = (r["mode"] or "").strip(), r["amount_p"] or 0
            if r["clinic_id"] in split_ids:
                continue                       # its legs are authoritative; do not double count
            if m == ONLINE:
                line_online += p
            elif m in ("Debit Card", "Credit Card"):
                card += p
            elif m == "Wallet":
                wallet += p
            elif m == "Patient APP":
                app += p
            elif m == "Cash":
                cash += p
            elif m == "Split Payment":
                other += p                     # a split with no legs recovered
            else:
                other += p
        ours = leg_online + line_online
        bank = con.execute("SELECT COALESCE(SUM(amount_p),0) s FROM upi_txn "
                           "WHERE unit=:u AND txn_date=:d", {"u": "clinic", "d": d}).fetchone()["s"]
        diff = ours - bank
        tot_ours += ours
        tot_bank += bank
        if diff == 0:
            agree += 1
        else:
            differ += 1
        aside = []
        if card:
            aside.append("card %d" % (card // 100))
        if wallet:
            aside.append("wallet %d" % (wallet // 100))
        if app:
            aside.append("app %d" % (app // 100))
        if other:
            aside.append("UNRESOLVED SPLIT %d" % (other // 100))
        print("%-12s %10d %10d %9d   %s"
              % (d, ours // 100, bank // 100, diff // 100, ", ".join(aside) or "-"))
        rows_out.append((d, ours, bank, diff))

    print("-" * 78)
    print("%-12s %10d %10d %9d" % ("TOTAL", tot_ours // 100, tot_bank // 100,
                                   (tot_ours - tot_bank) // 100))
    print()
    print("days compared: %d   agreeing to the rupee: %d   differing: %d" % (len(days), agree, differ))
    worst = sorted(rows_out, key=lambda r: -abs(r[3]))[:8]
    if differ:
        print("\nlargest differences (ours minus bank, in rupees):")
        for d, o, b, x in worst:
            if x:
                print("   %s   ours %6d   bank %6d   diff %+7d" % (d, o // 100, b // 100, x // 100))
    print("\nCARD IS NOT IN THIS COMPARISON. Every row of upi_txn carries mode='UPI'; the clinic's "
          "card takings settle on a rail this feed does not carry, so there is nothing here to "
          "match them against.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
