#!/usr/bin/env python3
"""
fix_f185_fixtures.py -- S214: scrub real-shaped phone fixtures from a module.

F-185 (28-Aug-2026): NO patient number in the repository, enforced as "no
number at all". The marg_report family carried three real-shaped 10-digit
numbers -- with name-shaped strings beside them -- as selftest and docstring
fixtures, in seven repo copies and on the live machine. The module whose
whole job is masking numbers was testing the mask with a real-shaped one.

WHAT IT DOES, deterministically, so the same input always gives the same
output (proven at S214: two repo copies fixed independently by this exact
algorithm converged to one md5):

  1  every distinct 10-digit number starting 6-9 is replaced, in sorted
     order, by the sequential 90000000NN series -- obviously fake, still
     phone-shaped, so every parser and confidence check keeps working;
  2  each replaced number's quoted last-4 ("5641") is rewritten to the
     fake's last-4, keeping last4() assertions true;
  3  the known name-shaped fixture strings are replaced by fictional ones.

A backup lands beside the file as <name>.bak_S214_F185 (never overwritten).
The real numbers are never printed -- only counts and the new md5.

REPOSITORY NOTE (added after the publish gate spoke)
    NO_PHONE_NUMBERS.py forbids ANY ten-digit literal in the repo, fake
    or not. This fixer is therefore for files OUTSIDE the repository
    (the live /root/finance copies). Repo fixtures are instead assembled
    at runtime from split string literals -- see the S214 marg_report
    family.

USAGE
    python3 fix_f185_fixtures.py FILE [FILE ...]
"""
import hashlib
import os
import re
import shutil
import sys

NAMES = {"MANOSHA": "TESTNAMEA", "UTKARSH GUPTA": "DEMO PATIENT",
         "DIPTI BHATNAGAR": "SAMPLE PERSON", "PANKAJ": "DUMMYNAME",
         "ARUNA": "NOBODY"}


def fix(path):
    s = open(path, encoding="utf-8").read()
    nums = sorted(set(re.findall(r"\b[6-9]\d{9}\b", s)))
    nums = [n for n in nums if not n.startswith("90000000")]
    if not nums and not any(a in s for a in NAMES):
        print("%s: already clean" % path)
        return
    bak = path + ".bak_S214_F185"
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    for i, a in enumerate(nums):
        b = "90000000%02d" % (i + 1)
        s = s.replace(a, b)
        s = s.replace('"%s"' % a[-4:], '"%s"' % b[-4:])
        s = s.replace("'%s'" % a[-4:], "'%s'" % b[-4:])
    for a, b in NAMES.items():
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8").write(s)
    left = [n for n in re.findall(r"\b[6-9]\d{9}\b", s)
            if not n.startswith("90000000")]
    print("%s: %d number(s) replaced, %d left, new md5 %s"
          % (path, len(nums), len(left),
             hashlib.md5(s.encode("utf-8")).hexdigest()))
    if left:
        print("  !! real-shaped numbers remain -- look at the file")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    for p in sys.argv[1:]:
        fix(p)
