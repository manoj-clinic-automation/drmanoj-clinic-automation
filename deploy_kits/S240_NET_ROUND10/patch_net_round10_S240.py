#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_net_round10_S240.py -- NET PAYABLE is cut to the last Rs.10.

THE OWNER, 12-Sep-2026: "ROUND OFF NET PAYABLE TO LAST 10 RUPEES."

Money is handed over in notes, so the paise and the last digit are not paid. The cut is made at
the ONE place the net is computed, so every page that shows a net -- sheet 3, sheet 4, the own
sheets, the slip, the totals, and whatever the lock stores -- shows the same rounded rupee. The
totals row adds the rounded nets, so the sheet still adds up.

DIRECTION: always TOWARDS ZERO. A payable of 8,651.33 is paid 8,650. A month that ends negative
(-1,949.07) carries 1,940 forward, not 1,950. The rounding never runs against the person.

The exact figure is kept as net_exact, and the difference as net_round_off, so a page that shows
a working can show the round-off line and still add up. Two such lines are added -- one on the
owner's SHEET 5, one on the salary slip -- and they appear only when there is something to round.

NO COLUMN IS ADDED to sheets 3 or 4 (the owner, 12-Sep: "dont add any columns now"). Sheet 3's
footnote gains one sentence saying the net is cut to the last Rs.10.

It refuses rather than guesses: each anchor must occur EXACTLY ONCE, and it must compile after the
edit or the backup is restored.

    /root/wa/venv/bin/python3 -B patch_net_round10_S240.py            (on the box)
    SP_PATH=./copy.py python3 -B patch_net_round10_S240.py            (offline)
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

TARGET = os.environ.get("SP_PATH", "/root/staff_register/salary_policy.py")
MARK = "net_round_off"

A_OLD = ("        net = round(base - deductions - adv_ded + duty_credits + ot_paid, 2)"
         " if base else 0.0\n")
A_NEW = ('''        net_exact = round(base - deductions - adv_ded + duty_credits + ot_paid, 2) \\
            if base else 0.0
        # D477 (the owner, 12-Sep-2026): "round off net payable to last 10 rupees". Money is
        # handed over in notes, so the paise and the last digit are not paid. The cut is always
        # TOWARDS ZERO -- a payable of 8,651.33 is paid 8,650, and a month that ends negative
        # carries 1,940 forward, not 1,950 -- so the rounding never runs against the person.
        net = float(int(abs(net_exact) / 10) * 10) * (-1.0 if net_exact < 0 else 1.0)
        net_round_off = round(net_exact - net, 2)
''')

B_OLD = '            "leave_dates": leave_dates, "net": net,\n'
B_NEW = ('            "leave_dates": leave_dates, "net": net,\n'
         '            "net_exact": net_exact, "net_round_off": net_round_off,\n')

C_OLD = '''    o.append("<tr class='net'><td><b>NET PAYABLE</b></td><td class='n'><b>%s</b></td></tr>"'''
C_NEW = ('''    if st.get("net_round_off"):
        o.append(row("Round off — to the last Rs.10", "", st["net_round_off"]))
''' + C_OLD)

D_OLD = '''    o.append("<tr class='net'><td><b>Is mahine mila</b></td><td class='n'><b>%s</b></td></tr>"'''
D_NEW = ('''    if st.get("net_round_off"):
        o.append(row("Round off — poore 10 rupaye", "", st["net_round_off"]))
''' + D_OLD)

E_OLD = "each without.</div>'"
E_NEW = ("each without. NET PAYABLE is cut to the last Rs.10 — the paise and the "
         "last digit are not paid out.</div>'")


def main():
    if not os.path.exists(TARGET):
        sys.exit("REFUSING: %s not found" % TARGET)
    raw = io.open(TARGET, "rb").read()
    src = raw.decode("utf-8")
    cur = hashlib.md5(raw).hexdigest()
    if MARK in src:
        print("ALREADY DONE; pin %s -- nothing to do" % cur)
        return 0
    if b"\r\n" in raw:
        sys.exit("REFUSING: CRLF line endings (F-294)")
    for name, anchor in (("the net line", A_OLD), ("the staff record", B_OLD),
                         ("the owner page NET row", C_OLD), ("the slip NET row", D_OLD),
                         ("the sheet 3 footnote", E_OLD)):
        n = src.count(anchor)
        if n != 1:
            sys.exit("REFUSING: %s occurs %d times, expected exactly 1. Nothing was changed."
                     % (name, n))

    new = (src.replace(A_OLD, A_NEW, 1).replace(B_OLD, B_NEW, 1)
              .replace(C_OLD, C_NEW, 1).replace(D_OLD, D_NEW, 1)
              .replace(E_OLD, E_NEW, 1))

    bak = TARGET + ".bak_S240round10_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(TARGET, bak)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(new)
    try:
        compile(new, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copy2(bak, TARGET)
        sys.exit("REFUSING: syntax error after the edit (%s); %s restored" % (ex, TARGET))
    got = hashlib.md5(io.open(TARGET, "rb").read()).hexdigest()
    print("   net is now cut to the last Rs.10, towards zero, at the one place it is computed")
    print("   %s : %s -> %s" % (os.path.basename(TARGET), cur[:8], got[:8]))
    print("   backup    : %s" % bak)
    return 0


if __name__ == "__main__":
    sys.exit(main())
