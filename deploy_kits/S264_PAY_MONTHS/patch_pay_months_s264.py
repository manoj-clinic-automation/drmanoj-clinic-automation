#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_pay_months_s264.py -- S264: the payment sheet gets its months back.

WHAT WAS WRONG. The tile opens /page/pay, which lands on the newest month, and
the sheet had NO way to reach any other month. The only route to August was the
hub, and the hub's month link goes to /page/month/<m> -- the PURCHASE AUDIT page
(bill by bill, PROVISIONAL, FINALISE), which is a different job entirely. So the
owner asked for August's payment sheet and got August's purchase audit.

THREE CHANGES, each anchored exactly once:
  A  the payment sheet gains a month strip -- every month with purchases, one tap.
  B  the purchase audit page gains one line pointing at that month's PAYMENT SHEET,
     so the two screens name each other instead of being mistaken for each other.
  C  the helper that builds the strip is appended at the end of the file.

    python3 -B patch_pay_months_s264.py --file /root/finance/purchase_app.py [--from <md5>]
"""
import argparse
import hashlib
import io
import os
import shutil
import sys

MARK = "_pay_months_nav_s264"

A_OLD = r"""            'this month is paid from. <a href="%s/page/month/%s">the same month, bill by bill</a>'
            '</div>%s%s%s%s%s'
            % (_esc(_month_name(month)), prefix, month, strip, sheet_card, verify_card,
               cheque_card, nextcard))"""
A_NEW = r"""            'this month is paid from. To check the bills themselves, open '
            '<a href="%s/page/month/%s">the purchase audit for this month</a>.'
            '</div>%s%s%s%s%s%s'
            % (_esc(_month_name(month)), prefix, month,
               _pay_months_nav_s264(con, month, prefix),
               strip, sheet_card, verify_card, cheque_card, nextcard))"""

# NOTE: the file writes the em dash as an escape sequence in its source. A raw
# string literal is NOT safe to match it with, so the backslash is built by hand.
_BS = chr(92)

B_OLD = ('purchases</h1><div class="muted">One row per Marg bill. '
         'The amount is Marg' + _BS + "'s '")
B_NEW = ('purchases</h1><div class="muted">This is the purchase audit ' + _BS + 'u2014 one row per '
         'Marg bill. To pay the month, open '
         '<b><a href="%s/page/pay/%s">the payment sheet for %s</a></b>. '
         'The amount is Marg' + _BS + "'s '")

C_OLD = r"""            % (_esc(_month_name(month)), recon, st, "".join(out) or"""
C_NEW = (r"""            % (_esc(_month_name(month)), request.script_root + _url_prefix, month,"""
         "\n" + r"""               _esc(_month_name(month)), recon, st, "".join(out) or""")

HELPER = '''

# ---------------------------------------------------------------------------
# S264 -- the months, on the sheet itself.
#
# /page/pay lands on the newest month and had no way out of it. This is that way
# out: every month the purchase book actually holds, as one tap each, with the
# month being read marked and not a link. Styled inline on purpose -- the page's
# stylesheet is not touched by this kit.
# ---------------------------------------------------------------------------

_NAV_ON_S264 = ("display:inline-block;padding:4px 11px;border-radius:999px;"
                "background:var(--ink);color:#fff;font-weight:600;font-size:13px")
_NAV_OFF_S264 = ("display:inline-block;padding:4px 11px;border-radius:999px;"
                 "border:1px solid var(--line);text-decoration:none;font-size:13px")


def _short_month_s264(m):
    """Aug 26 -- the strip has to fit a phone, so the long name is not used here."""
    try:
        y, mm = m.split("-")
        return "%s %s" % (("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
                           "Sep", "Oct", "Nov", "Dec")[int(mm) - 1], y[2:])
    except Exception:
        return m


def _pay_months_nav_s264(con, month, prefix):
    try:
        months = _months(con)
    except Exception:
        return ""
    if not months:
        return ""
    if month not in months:
        months = sorted(set(months) | {month}, reverse=True)
    out = []
    for m in months:
        label = _esc(_short_month_s264(m))
        if m == month:
            out.append('<span style="%s">%s</span>' % (_NAV_ON_S264, label))
        else:
            out.append('<a href="%s/page/pay/%s" style="%s">%s</a>'
                       % (prefix, m, _NAV_OFF_S264, label))
    return ('<div class="card" data-s264="months" style="padding:9px 12px"><div '
            'style="display:flex;flex-wrap:wrap;gap:7px;align-items:center">%s</div></div>'
            % "".join(out))
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--from", dest="from_md5", default=None)
    a = ap.parse_args()
    if not os.path.exists(a.file):
        sys.exit("REFUSING: %s not found" % a.file)
    raw = io.open(a.file, "rb").read()
    cur = hashlib.md5(raw).hexdigest()
    src = raw.decode("utf-8")
    if MARK in src:
        print("ALREADY PATCHED (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if a.from_md5 and cur != a.from_md5.lower():
        sys.exit("REFUSING: %s is %s, you said %s" % (a.file, cur, a.from_md5))
    for label, old in (("the payment sheet's body", A_OLD),
                       ("the audit page's first line", B_OLD),
                       ("the audit page's arguments", C_OLD)):
        if src.count(old) != 1:
            sys.exit("REFUSING: anchor %r matched %d times, expected exactly 1"
                     % (label, src.count(old)))
    new = src.replace(A_OLD, A_NEW, 1).replace(B_OLD, B_NEW, 1).replace(C_OLD, C_NEW, 1)
    new = new.rstrip("\n") + "\n" + HELPER.strip("\n") + "\n"
    bak = a.file + ".bak_S264_" + cur[:8]
    shutil.copy2(a.file, bak)
    io.open(a.file, "w", encoding="utf-8", newline="\n").write(new)
    got = hashlib.md5(io.open(a.file, "rb").read()).hexdigest()
    print("patched %s" % a.file)
    print("   was  %s" % cur)
    print("   now  %s" % got)
    print("   backup %s" % bak)


if __name__ == "__main__":
    main()
