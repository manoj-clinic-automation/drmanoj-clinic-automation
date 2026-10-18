#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lines_s582.py -- a frozen earlier walk, re-run on the S582 files, with exactly the line S582 forces in its new form.

    python3 lines_s582.py s571 <the frozen walk_s571.py> <out: a copy in /tmp (or the PC's _scratch)>

The earlier kits are never edited (a published kit is frozen); the copy is written elsewhere. The line must be found exactly once, or
this refuses (exit 1). It is an INTENDED change (S582_BRIEF_R1 B1):
  s571 I1 -- S571's walk line 354 requires Renewals IMMEDIATELY after Batteries in the owner's menu. S582 puts "X-ray costs" between
             them for the owner (only when xray_costs.py is mounted). The line now accepts Batteries . Renewals (xray_costs not
             mounted -- S571's walk copies its own MODS, which do not name xray_costs.py) or Batteries . X-ray costs . Renewals. The
             manager's line (586: Machines . Batteries) is untouched. S582's own walk (X7) checks the owner's and the manager's order
             strictly with xray_costs mounted. No other line of any earlier walk changes."""
import sys

LINES = {
    "s571": (
        ('and n_fit_btn >= 15 and "+ Add a battery place" in p1 and after(m_own, "Machines", "Batteries") and after(m_own, "Batteries", "Renewals")\n',
         'and n_fit_btn >= 15 and "+ Add a battery place" in p1 and after(m_own, "Machines", "Batteries") and (after(m_own, "Batteries", "Renewals")'
         ' or (after(m_own, "Batteries", "X-ray costs") and after(m_own, "X-ray costs", "Renewals")))\n', 1),
    ),
}


def main():
    which, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
    s = open(src, encoding="utf-8").read()
    for old, new, cnt in LINES[which]:
        n = s.count(old)
        if n != cnt:
            sys.exit("REFUSED: the %s walk line %r was found %d times, not %d" % (which, old[:60], n, cnt))
        s = s.replace(old, new)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(s)
    print("%s walk copied to %s with its %d line%s in S582's form" % (which.upper(), out, len(LINES[which]), "" if len(LINES[which]) == 1 else "s"))


if __name__ == "__main__":
    main()
