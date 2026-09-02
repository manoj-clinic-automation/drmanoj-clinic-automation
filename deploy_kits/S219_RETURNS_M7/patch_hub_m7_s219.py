#!/usr/bin/env python3
"""
patch_hub_m7_s219.py -- S219 M7, part 3 of 4.

THE SCREEN, READ FIRST (the S209 rule). Before writing a line of this, the
hub's own code was read, and it held the defect the rest of M7 would otherwise
have shipped into: the verdict badge is a two-branch ladder whose FINAL ELSE
IS RED. Any verdict it has not been told about -- "identity needed" included --
arrives on the owner's screen in the exact colour this whole change exists to
take away.

TWO anchored changes to finance_ui/finance_approvals.html:
  H  "identity needed" reads AMBER, beside the two verdicts that already do
  I  the patient's full mobile when the box has it, the last four when it does
     not (D356). Never a half-number dressed as a whole one.

This file is HTML, so there is no compile check to run -- the patcher instead
asserts each anchor exactly once and keeps a timestamped backup beside it.
No service restart is needed: it is a static file.

USAGE (one line):
  /root/wa/venv/bin/python3 -B /root/finance/patch_hub_m7_s219.py
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('HUB_PATH', '/root/finance/finance_ui/finance_approvals.html')
MARK = 'S219 M7:'

H_OLD = '      var vb = n.verdict==="ok" ? \'<span class="ok">ok</span>\'\n             : (n.verdict==="no patient attributed"||n.verdict==="not examinable")\n               ? \'<span class="badge b-warn">\'+esc(n.verdict)+\'</span>\'\n               : \'<span class="badge b-bad">\'+esc(n.verdict)+\'</span>\';'

H_NEW = '      /* S219 M7: three verdicts mean THE AUDIT COULD NOT RUN, and they are\n         amber, not red. Red is reserved for a finding about money. Before\n         this, an unknown verdict fell through to red by default -- which is\n         how "identity needed" would have arrived on the screen wearing the\n         exact colour the change exists to remove. */\n      var vb = n.verdict==="ok" ? \'<span class="ok">ok</span>\'\n             : (n.verdict==="no patient attributed"||n.verdict==="not examinable"\n                ||n.verdict==="identity needed")\n               ? \'<span class="badge b-warn">\'+esc(n.verdict)+\'</span>\'\n               : \'<span class="badge b-bad">\'+esc(n.verdict)+\'</span>\';'

I_OLD = '      h+= n.name\n        ? \'<div style="margin:2px 0">patient: <b>\'+esc(n.name)+\'</b>\'+(n.clinic_id?\' · ID \'+esc(n.clinic_id):\'\')+(n.mobile_last4?\' · …\'+esc(n.mobile_last4):\'\')+\'</div>\''

I_NEW = '      h+= n.name\n        ? \'<div style="margin:2px 0">patient: <b>\'+esc(n.name)+\'</b>\'+(n.clinic_id?\' · ID \'+esc(n.clinic_id):\'\')+(n.mobile?\' · \'+esc(n.mobile):(n.mobile_last4?\' · …\'+esc(n.mobile_last4):\'\'))+\'</div>\''

PAIRS = [("H", H_OLD, H_NEW), ("I", I_OLD, I_NEW)]


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
    bak = TARGET + ".bak_S219_m7_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    return 0


if __name__ == "__main__":
    sys.exit(main())
