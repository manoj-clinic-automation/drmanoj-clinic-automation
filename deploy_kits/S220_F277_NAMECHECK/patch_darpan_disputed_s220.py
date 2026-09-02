#!/usr/bin/env python3
"""
patch_darpan_disputed_s220.py -- S220 F-277, part 3 of 4: Darpan's count.

darpan_app.py (pin f4161c7d) keeps a small list of verdicts that say THE
AUDIT COULD NOT RUN -- "no patient attributed", "not examinable", "identity
needed". They stay in `needs`, so the row reaches Darpan's desk as a
question, but they are NOT counted in `flagged`, the number the owner is
meant to act on. "identity disputed" joins that list, for the same reason
and by the owner's ruling (S220): amber, routed to Darpan, never a money
verdict. ONE anchored change, sliced verbatim from the live bytes.

Run on the box:
  /root/wa/venv/bin/python3 -B /root/finance/patch_darpan_disputed_s220.py
Offline: DARPAN_PATH=/path/to/darpan_app.py.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('DARPAN_PATH', '/root/finance/darpan_app.py')
MARK = 'S220 F-277'

A_OLD = ('            if not _hist and r["verdict"] not in (\n'
         '                    "ok", "no patient attributed", "not examinable",\n'
         '                    "identity needed"):\n'
         '                flagged += 1')

A_NEW = ('            # S220 F-277: "identity disputed" -- two names on one clinic ID --\n'
         '            # is a question for a person, not a finding about money. It\n'
         '            # joins the three above: on the desk, not in the count.\n'
         '            if not _hist and r["verdict"] not in (\n'
         '                    "ok", "no patient attributed", "not examinable",\n'
         '                    "identity needed", "identity disputed"):\n'
         '                flagged += 1')

PAIRS = [("A", A_OLD, A_NEW)]


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
    bak = TARGET + ".bak_S220_f277_" + stamp
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
