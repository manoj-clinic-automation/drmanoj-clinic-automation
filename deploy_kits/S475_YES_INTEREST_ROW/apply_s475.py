#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s475.py -- S475_YES_INTEREST_ROW (session 293, 04-Oct-2026, F-720). Exact-anchor edits on the two Yes Bank
readers, built from the real bytes of the 04-Oct 01:35 bundle: yes_branch.py 378539d9 · finance_yesbank.py 5a088cd9.
Every anchor must be found exactly once; both files are verified before either is written.

WHAT. On 04-Oct the shelf refused two true September statements (Dr Manoj's and Dr Bhawna's Yes Bank savings, the
branch's unlocked copies): 'a row dated 2026-10-01 falls outside the printed period 2026-09-01 to 2026-09-30'. Read in
the statement itself: the row is the bank's own quarter-end interest -- 'CREDIT INTEREST CAPITALISED ON SB A/C',
TXN DATE 01-OCT-2026, VALUE DATE 30-SEP-2026 -- which the bank counts inside September's totals (every arithmetic proof
had already passed; only the date check, which looked at the txn date alone, refused). Both readers (the branch layout
and the e-statement PDF) have the same check at the same place.

THE RULE NOW: a row is inside the printed period when EITHER its value date or its txn date is -- so nothing that was
accepted before is refused now, and the bank's next-working-day posting of a value-dated row is accepted. A row whose
both dates fall outside is refused as before, and the message now prints both dates.
   usage: apply_s475.py <yes_branch.py> <finance_yesbank.py>
"""
import hashlib
import sys

FROM = {"yes_branch.py": "378539d930b8fc3caa5b0ce9d6664c5e", "finance_yesbank.py": "5a088cd91bc1b8d873cc779f3fa9b0a8"}

BRANCH_EDITS = [
    ('''def _iso(s):
    return dt.datetime.strptime(s.title(), "%d-%b-%Y").date().isoformat()
''',
     '''def _iso(s):
    return dt.datetime.strptime(s.title(), "%d-%b-%Y").date().isoformat()


def in_period(ln, pfrom, pto):
    """S475 (F-720): a row belongs to the printed period when its VALUE date OR its txn date is inside it. The bank posts
    the quarter's savings interest on the first day of the next month with the value date of the last ('CREDIT INTEREST
    CAPITALISED ON SB A/C', TXN DATE 01-OCT, VALUE DATE 30-SEP) and counts it in that month's totals; the txn date alone
    refused a true statement. Nothing accepted before this rule is refused by it."""
    v = ln.get("value_date") or ln["txn_date"]
    return (pfrom <= ln["txn_date"] <= pto) or (pfrom <= v <= pto)
'''),
    ('''    for i, ln in enumerate(lines, 1):
        if ln["txn_date"] < pfrom or ln["txn_date"] > pto:
            raise StatementRejected("a row dated %s falls outside the printed period %s to %s -- refusing" % (ln["txn_date"], pfrom, pto))
''',
     '''    for i, ln in enumerate(lines, 1):
        if not in_period(ln, pfrom, pto):                                              # S475 (F-720)
            raise StatementRejected("a row dated %s (value date %s) falls outside the printed period %s to %s -- refusing"
                                    % (ln["txn_date"], ln.get("value_date") or ln["txn_date"], pfrom, pto))
'''),
]

ESTMT_EDITS = [
    ('''def _iso(v):
    """The bank writes ISO already; accept dd/mm/yyyy and dd-Mon-yyyy too.
''',
     '''def in_period(ln, pfrom, pto):
    """S475 (F-720): a row belongs to the printed period when its VALUE date OR its txn date is inside it. The bank posts
    the quarter's savings interest on the first day of the next month with the value date of the last ('CREDIT INTEREST
    CAPITALISED', TXN DATE 01-OCT, VALUE DATE 30-SEP) and counts it in that month's totals; the txn date alone refused a
    true statement. A row with no value date is judged by its txn date, as before."""
    v = ln.get("value_date") or ln["txn_date"]
    return (pfrom <= ln["txn_date"] <= pto) or (pfrom <= v <= pto)


def _iso(v):
    """The bank writes ISO already; accept dd/mm/yyyy and dd-Mon-yyyy too.
'''),
    ('''    for ln in lines:
        if ln["txn_date"] < pfrom or ln["txn_date"] > pto:
            raise StatementRejected("a row dated %s falls outside the printed period %s to %s "
                                    "-- refusing" % (ln["txn_date"], pfrom, pto))
''',
     '''    for ln in lines:
        if not in_period(ln, pfrom, pto):                                  # S475 (F-720)
            raise StatementRejected("a row dated %s (value date %s) falls outside the printed period %s to %s "
                                    "-- refusing" % (ln["txn_date"], ln.get("value_date") or ln["txn_date"], pfrom, pto))
'''),
]


def apply(src, edits, what):
    for n, (old, new) in enumerate(edits, 1):
        got = src.count(old)
        if got != 1:
            raise SystemExit("!! %s anchor %d was found %d time(s), expected 1 - nothing written" % (what, n, got))
        src = src.replace(old, new)
    return src


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_s475.py <yes_branch.py> <finance_yesbank.py>")
    plan = [("yes_branch.py", sys.argv[1], BRANCH_EDITS), ("finance_yesbank.py", sys.argv[2], ESTMT_EDITS)]
    outs = []
    for name, path, edits in plan:
        raw = open(path, "rb").read()
        have = hashlib.md5(raw).hexdigest()
        if have != FROM[name]:
            raise SystemExit("!! %s is %s, not %s - nothing written" % (path, have, FROM[name]))
        out = apply(raw.decode("utf-8"), edits, name).encode("utf-8")
        compile(out, path, "exec")
        outs.append((name, path, raw, out, len(edits)))
    for name, path, raw, out, n in outs:                   # both verified before either is written
        with open(path, "wb") as fh:
            fh.write(out)
        print("%s %s -> %s (%d edits; %+d bytes)" % (name, hashlib.md5(raw).hexdigest()[:8], hashlib.md5(out).hexdigest()[:8], n, len(out) - len(raw)))


if __name__ == "__main__":
    main()
