#!/usr/bin/env python3
# =====================================================================
#  S193_DISC — in-place patch of the served Hub template
#  (/root/finance/finance_ui/finance_approvals.html)
#
#  Adds a Gross and Disc(ount) column to the per-day Marg bill drill.
#  Today the bill table shows only the NET ("Amount"); a discounted
#  bill therefore reconciles invisibly against the day's gap. After
#  this, each bill shows  Gross | Disc | Net.
#
#  FAIL-LOUD: every anchor must be found exactly once, or nothing is
#  written and the script exits non-zero (the installer rolls back).
#  Bytes-only edit to client-side JS; no server/Jinja region touched.
# =====================================================================
import sys

TARGET = "/root/finance/finance_ui/finance_approvals.html"

# (label, exact_old, new, expected_count)
PATCHES = [
    ("bill table header",
     '<thead><tr><th>Bill</th><th>Patient</th><th>Mode</th><th class="num">Amount</th></tr></thead>',
     '<thead><tr><th>Bill</th><th>Patient</th><th>Mode</th>'
     '<th class="num">Gross</th><th class="num">Disc</th><th class="num">Net</th></tr></thead>',
     1),
    ("bill row cells",
     '<td>\'+esc(b.mode||"")+\'</td><td class="num">\'+fmt(b.amount)+\'</td></tr>\';',
     '<td>\'+esc(b.mode||"")+\'</td>'
     '<td class="num">\'+(b.gross!=null?fmt(b.gross):"—")+\'</td>'
     '<td class="num">\'+(b.disc?fmt(b.disc):"—")+\'</td>'
     '<td class="num">\'+fmt(b.amount)+\'</td></tr>\';',
     1),
    ("items sub-row colspan",
     '<tr class="items" style="display:none"><td colspan="4"><table>',
     '<tr class="items" style="display:none"><td colspan="6"><table>',
     1),
]


def main():
    with open(TARGET, "r", encoding="utf-8") as fh:
        html = fh.read()

    # preflight: every anchor present exactly the expected number of times,
    # and not already patched (idempotence guard).
    problems = []
    for label, old, new, want in PATCHES:
        got = html.count(old)
        already = html.count(new)
        if already >= want and got == 0:
            problems.append("ALREADY PATCHED: %s" % label)
        elif got != want:
            problems.append("anchor '%s' found %d time(s), expected %d" % (label, got, want))
    if problems:
        print("*** PATCH PREFLIGHT FAILED — nothing written:")
        for p in problems:
            print("      -", p)
        sys.exit(2)

    for label, old, new, want in PATCHES:
        html = html.replace(old, new, want)

    with open(TARGET, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("      Hub bill-drill patched: Gross | Disc | Net columns added.")


if __name__ == "__main__":
    main()
