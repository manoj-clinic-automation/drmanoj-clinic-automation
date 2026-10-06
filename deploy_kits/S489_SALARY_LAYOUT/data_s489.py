#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data_s489.py -- kit S489_SALARY_LAYOUT: the two small OWNER-RULED records Sheet 2 cannot read out
of the staff ledger, written as /root/staff_register/loan_pages.json (salary_policy.loan_pages()).

  groups   -- advances that are ONE loan handed over in parts. Today one: Surendra's advance of
              14-17 Aug 2026, entered as three advances (the owner's stated record of 10-Sep-2026,
              lines C2-C4 and C9: the group comes back in equal monthly parts from the August salary).
  history  -- a private loan's months BEFORE the staff ledger began. Today one: Darpan's loan with
              interest. Its position at 31-Mar-2026 is the loan workbook's own agreed one
              (Salary_System_2026.xlsx, Loan Master B13, "owner's ledger figure"); its Repayment
              Tracker has April 2026 skipped and May and June paid at the loan's standing terms.
              THIS RECORD CARRIES NO BALANCE AND NO INSTALMENT (F-31): it says only which months
              were skipped and which were paid. The engine works the opening balance BACK from the
              ledger's own figures -- so the page can never disagree with the ledger -- and
              "ledger_adjust" names the one adjustment the ledger must carry for those months: the
              flat Rs 1,000 the workbook added on the skipped April, which the owner ruled on
              06-Oct-2026 comes off (D682; restate_s489.py writes that row). If the ledger's
              adjustment is anything else, the page SAYS so instead of showing a wrong opening.

From now on an advance paid back over several months should be entered ONCE with its schedule;
then it is one ledger row and needs no group here. This file is data, not code: it holds no
salary, no balance and no patient detail. The kit ships no .json (the repository blocks them,
F-300/F-751), so the file is made by this script.

usage:  python3 data_s489.py --write <path>      write (or confirm) the file; prints its md5
        python3 data_s489.py --check <path>      0 if the file there holds exactly this record
"""
import os, sys, json, hashlib

RECORD = {
    "_made_by": "kit S489_SALARY_LAYOUT (data_s489.py), 06-Oct-2026 -- owner rulings D681/D682",
    "groups": [
        {"staff": "Surendra", "given": "14–17 Aug 2026",
         "ids": ["3e4033170e76", "89899f448bfd", "c5ebea2b976a"],
         "why": "one advance entered as three (stated record of 10-Sep-2026, C2-C4, C9)"},
    ],
    "history": {
        "Darpan": {
            "loan_id": "b1eb7a8e419e",
            "opening_date": "2026-03-31",
            "ledger_adjust": -1000,
            "source": "loan workbook Salary_System_2026.xlsx (7-Aug-2026): Loan Master B13; Repayment Tracker rows 4-6",
            "pre": [
                {"ym": "2026-04", "kind": "skip",
                 "note": "skipped; the flat interest the workbook added on this month comes off (owner, 06-Oct-2026)"},
                {"ym": "2026-05", "kind": "paid"},
                {"ym": "2026-06", "kind": "paid"},
            ],
        },
    },
}


def text():
    return json.dumps(RECORD, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv):
    if len(argv) != 3 or argv[1] not in ("--write", "--check"):
        print(__doc__)
        return 2
    path = argv[2]
    want = text().encode("utf-8")
    have = None
    if os.path.exists(path):
        with open(path, "rb") as f:
            have = f.read()
    if argv[1] == "--check":
        ok = have == want
        print("loan_pages.json %s" % ("holds this kit's record" if ok else "is absent or different"))
        return 0 if ok else 1
    if have == want:
        print("loan_pages.json already holds this record  md5 %s" % md5(want))
        return 0
    if have is not None:
        bak = path + ".bak_S489_" + md5(have)[:8]
        with open(bak, "wb") as f:
            f.write(have)
        os.chmod(bak, 0o600)
        print("an earlier loan_pages.json kept as %s" % bak)
    tmp = path + ".s489.tmp"
    with open(tmp, "wb") as f:
        f.write(want)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    print("loan_pages.json written  md5 %s  (%d group, %d private loan history)"
          % (md5(want), len(RECORD["groups"]), len(RECORD["history"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
