#!/usr/bin/env python3
"""
patch_darpan_english_s220.py -- S220 item 3: the owner's console speaks English.

THE OWNER'S RULING (02-Sep): converse with him in English always; every
owner-facing console and page in English; staff-facing pages stay Hindi.

A sub-agent read the live code for Hindi on owner-only surfaces. The hub page
itself is 100% English. Three checker-only API responses were not:
  1  /finance/darpan/api/coverage -- five romanised-Hindi explanations, in a
     field literally named `hindi`, RENDERED on the owner's hub in the Marg
     coverage table ("sab aa gaya", "din bhara hai par Marg report nahin"...).
     -> English. The field keeps its name so the page needs no change.
  2  /finance/darpan/api/corrections -- "Marg: bill X ka payment mode CASH se
     UPI kijiye". The endpoint is checker-only, so the OWNER reads it and
     relays it to Darpan, who acts in Marg. -> English first, the Hindi kept
     in brackets for the relay: the owner reads his language, Darpan hears his.
  3  joiner /api/reset_password -- "<name> ka password reset ho gaya hai" is
     the text the owner reads OUT to the staff member ("Set the portal
     password to this, then read it out"). It is a message TO staff, shown on
     the owner's screen: staff-facing by purpose. LEFT AS IT IS, on the
     owner's own rule -- recorded here so nobody hunts for it again.

TWO anchored changes to darpan_app.py (pin 94bffba2, the metrics bytes).
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_darpan_english_s220.py
Offline: DARPAN_PATH=/path/to/darpan_app.py.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('DARPAN_PATH', '/root/finance/darpan_app.py')
MARK = 'S220 OWNER ENGLISH'

A_OLD = '''        if f and export == "applied":
            verdict, hindi = "OK", "sab aa gaya"
        elif f and export == "staged":
            verdict, hindi = "REPORT WAITING", "report aayi hai, workbench se lagani hai"
        elif f:
            verdict, hindi = "EXPORT MISSING", "din bhara hai par Marg report nahin"
        elif export in ("applied", "staged"):
            verdict, hindi = "DAY NOT FILED", "report hai par din nahin bhara"
        else:
            verdict, hindi = "DAY NOT FILED", "na din bhara na report"
'''
A_NEW = '''        # S220 OWNER ENGLISH: these lines are rendered on the owner's hub (the
        # Marg coverage table). The field keeps its old name so the page needs
        # no change; the words are the owner's language now.
        if f and export == "applied":
            verdict, hindi = "OK", "filed, report in, applied"
        elif f and export == "staged":
            verdict, hindi = "REPORT WAITING", "the report is in; apply it from the workbench"
        elif f:
            verdict, hindi = "EXPORT MISSING", "the day is filed, but there is no Marg report"
        elif export in ("applied", "staged"):
            verdict, hindi = "DAY NOT FILED", "the report is in, but the day is not filed"
        else:
            verdict, hindi = "DAY NOT FILED", "neither filed nor reported"
'''
B_OLD = '''            instruction="Marg: bill %s ka payment mode CASH se UPI kijiye"
                        % (r["bill_no"] or "?")))
'''
B_NEW = '''            # S220 OWNER ENGLISH: the owner reads this and relays it to Darpan,
            # who acts in Marg -- so English first, the Hindi kept for the relay.
            instruction="Marg: change bill %s payment mode CASH \\u2192 UPI "
                        "(bill %s ka payment mode CASH se UPI kijiye)"
                        % (r["bill_no"] or "?", r["bill_no"] or "?")))
'''
PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S220_english_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: the result does not compile (%s). "
                         "RESTORED from %s -- the live file is unchanged." % (ex, bak))
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("restart  systemctl restart clinic-finance.service")
    return 0


if __name__ == "__main__":
    sys.exit(main())
