#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""report_s468.py -- S468_FINANCE_SMALLS: three small housekeeping jobs, each run by the installer. Need not be run by hand.

  report_s468.py advances   <ledger.jsonl> <finance.db>         READ-ONLY
      Names every pharmacy salary advance in the finance book that is stamped as posted, or sits on an approved day
      with no stamp (S462 counted 1 and 1): the day, the person, the amount, and the Staff Ledger row that answers
      it -- or the plain fact that none does. Changes nothing.
  report_s468.py scans      <finance_scans folder> <finance.db> <live scan folder> [--move]
      The tiny test scans --selftest left behind before S461 (under 65 bytes, *.pdf -- no scanner makes a PDF that
      small). Counted; with --move they are MOVED into a folder beside the one they are in, never deleted. A file
      that any row of the finance database names is left where it is. Refuses if the folder is the live scan folder.
  report_s468.py statements <upi_statements folder> <yesbank_statements folder>   READ-ONLY
      Counts the files there that carry the names only --selftest uses. Nothing is moved: a bank-statement store is
      not tidied by a guess.
"""
import datetime
import json
import os
import sqlite3
import sys

TINY = 65
ASIDE = "finance_scans.test_scans_set_aside_S468"


def _ro(path):
    return sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=5)


def advances(led, dbf):
    rows = []
    try:
        with open(led, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    except OSError as ex:
        print("the Staff Ledger was not read (%s)" % ex)
        return 0
    by_id = {r.get("id"): r for r in rows}
    try:
        con = _ro(dbf)
        con.row_factory = sqlite3.Row
        book = con.execute(
            "SELECT x.id, x.amount_p, x.ledger_posted, x.ledger_ref, x.ledger_posted_at, e.business_date, e.status, "
            "s.name AS staff FROM day_expense x JOIN day_entry e ON e.id=x.day_entry_id "
            "LEFT JOIN staff_ref s ON s.id=x.staff_id WHERE e.unit='medical' AND x.category_fixed='salary_advance' "
            "AND (x.ledger_posted=1 OR e.status IN ('approved','locked')) ORDER BY e.business_date, x.id").fetchall()
    except Exception as ex:                                          # noqa: BLE001
        print("the finance database was not read (%s)" % ex)
        return 0
    print("pharmacy salary advances in the finance book, stamped or on an approved day: %d" % len(book))

    def near(staff, amount, iso):
        got = []
        try:
            d0 = datetime.date.fromisoformat(iso)
        except ValueError:
            return got
        for r in rows:
            if r.get("category") != "ADVANCE_ISSUE" or r.get("contra_of"):
                continue
            try:
                dd = abs((datetime.date.fromisoformat(str(r.get("date_from"))[:10]) - d0).days)
            except ValueError:
                continue
            if (r.get("staff") or "").strip().lower() == (staff or "").strip().lower() and r.get("amount") == amount and dd <= 7:
                got.append(r)
        return got

    def say(r):
        return "ledger row %s, dated %s, %s, entered by %s%s" % (
            r.get("id"), r.get("date_from"), r.get("status"), r.get("maker") or "?",
            " -- posted by the finance app" if "(finance expense #" in (r.get("narration") or "") else " -- entered in the ledger by hand")

    for b in book:
        amount = b["amount_p"] // 100
        head = "  %s  %s  Rs %d  (day %s)" % (b["business_date"], b["staff"] or "no name", amount, b["status"])
        if b["ledger_posted"]:
            r = by_id.get(b["ledger_ref"])
            if r:
                # a REVERSAL is an approved contra of the SAME category (the ledger's own test). An instalment, a skip
                # and a deferral also point at the advance through contra_of -- they are not reversals (F-714: this
                # report said 'REVERSED' of a live advance on its first run on the box, 03-Oct, for want of this line).
                rev = [x for x in rows if x.get("contra_of") == r.get("id") and x.get("status") == "APPROVED"
                       and x.get("category") == r.get("category")]
                print(head + ": STAMPED, and its row is in the ledger -- %s%s" % (say(r), "; REVERSED there since" if rev else ""))
            else:
                n = near(b["staff"], amount, b["business_date"])
                print(head + ": STAMPED with ledger row %s, which is NOT in the ledger%s" % (
                    b["ledger_ref"] or "(none written)",
                    ("; the same person and amount within 7 days: " + "; ".join(say(x) for x in n[:3])) if n
                    else "; and no advance of that person and amount within 7 days either -- TO LOOK AT"))
        else:
            n = near(b["staff"], amount, b["business_date"])
            if n:
                print(head + ": NO STAMP, but the ledger has it -- %s. Nothing to do; it cannot post again (S462)." % "; ".join(say(x) for x in n[:3]))
            else:
                print(head + ": NO STAMP and NO advance of that person and amount within 7 days in the ledger -- "
                             "it never reached the Staff Ledger. TO LOOK AT: enter it in the Staff Ledger by hand if it was paid.")
    return 0


def _named_in_db(dbf, folder_name):
    """Base names of files in <folder_name> that any '...path...' column of the finance database names."""
    named = set()
    con = _ro(dbf)
    for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        for col in con.execute('PRAGMA table_info("%s")' % t.replace('"', '')).fetchall():
            if "path" in (col[1] or "").lower():
                try:
                    for (v,) in con.execute('SELECT "%s" FROM "%s" WHERE "%s" LIKE ?' % (col[1], t, col[1]), ("%" + folder_name + "%",)):
                        if v:
                            named.add(os.path.basename(str(v)))
                except sqlite3.Error:
                    continue
    con.close()
    return named


def scans(folder, dbf, live, move):
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        print("test scans: %s is not there -- nothing to do" % folder)
        return 0
    if os.path.realpath(folder) == os.path.realpath(live):
        print("test scans: REFUSED -- %s is the live scan folder; nothing is touched" % folder)
        return 0
    try:
        named = _named_in_db(dbf, os.path.basename(folder))
    except Exception as ex:                                          # noqa: BLE001
        print("test scans: the finance database was not read (%s) -- nothing is moved" % ex)
        return 0
    tiny, kept = [], 0
    for root, _dirs, files in os.walk(folder):
        for f in files:
            p = os.path.join(root, f)
            try:
                if f.lower().endswith(".pdf") and os.path.getsize(p) < TINY and not os.path.islink(p):
                    if f in named:
                        kept += 1
                    else:
                        tiny.append(p)
            except OSError:
                continue
    if not move:
        print("test scans: %d tiny test scan(s) in %s%s" % (len(tiny), folder, ("; %d more are named by a row of the database and stay" % kept) if kept else ""))
        return 0
    dest = os.path.join(os.path.dirname(folder), ASIDE)
    moved = 0
    for p in tiny:
        rel = os.path.relpath(p, folder)
        to = os.path.join(dest, rel)
        if os.path.exists(to):
            to = to + "." + datetime.datetime.now().strftime("%H%M%S%f")
        try:
            os.makedirs(os.path.dirname(to), exist_ok=True)
            os.rename(p, to)                                         # a move inside one disk; nothing is deleted
            moved += 1
        except OSError:
            continue
    print("test scans: %d tiny test scan(s) moved out of %s into %s (moved, not deleted)%s"
          % (moved, folder, dest, ("; %d named by a row of the database were left" % kept) if kept else ""))
    return 0


def statements(upi, yes):
    for label, folder, tail in (("upi_statements", upi, "_mpr.xlsx"), ("yesbank_statements", yes, "_yesbank.csv")):
        if not os.path.isdir(folder):
            print("test statements: %s is not there" % folder)
            continue
        names = os.listdir(folder)
        n = len([f for f in names if f.lower().endswith(tail)])
        print("test statements: %s holds %d file(s); %d carry the self-test's own name (*%s) -- counted only, nothing moved"
              % (label, len(names), n, tail))
    return 0


def main():
    a = sys.argv[1:]
    if len(a) == 3 and a[0] == "advances":
        return advances(a[1], a[2])
    if len(a) in (4, 5) and a[0] == "scans":
        return scans(a[1], a[2], a[3], len(a) == 5 and a[4] == "--move")
    if len(a) == 3 and a[0] == "statements":
        return statements(a[1], a[2])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
