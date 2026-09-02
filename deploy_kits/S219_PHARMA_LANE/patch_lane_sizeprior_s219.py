#!/usr/bin/env python3
"""
patch_lane_sizeprior_s219.py -- S219, a DELTA on top of the pharmacy lane.

The lane went live at 16:17 today (asset_register.py e7a68a13...). This adds the
one thing learned afterwards, from the owner scanning a real bill: >95% of
pharmacy purchase bills are HALF A4, so the lane now TELLS the scanner which
page it is looking for. Without that the detector can outline the PRINTING
instead of the paper, and look entirely convincing doing it.

A separate patcher rather than a re-run, because the main kit refuses on its own
MARK once installed -- and a patcher that quietly re-applies itself is how a file
ends up patched twice.

ONE anchored change, sliced verbatim from the installed bytes.
SAFETY: exact-once assert, timestamped backup, compile-with-restore, idempotent.
USAGE: python3 -B /root/assetapp/patch_lane_sizeprior_s219.py
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get("AR_PATH", "/root/assetapp/asset_register.py")
MARK = "expectAspect=0.7048"

OLD = '<select id=intake_lane style="max-width:300px"\n onchange="if(window.SCANNER_CONFIG){window.SCANNER_CONFIG.uploadFields.lane=this.value;}\n           var h=document.getElementById(\'lane_basic\'); if(h){h.value=this.value;}">'

NEW = '<select id=intake_lane style="max-width:300px"\n onchange="if(window.SCANNER_CONFIG){window.SCANNER_CONFIG.uploadFields.lane=this.value;\n             /* S219: >95% of pharmacy purchase bills are half A4 (owner, measured).\n                Telling the scanner the page it is looking for is what stops it\n                outlining the PRINTING instead of the paper. Cleared for clinic\n                bills, which are any shape at all. */\n             if(this.value===\'pharmacy\'){window.SCANNER_CONFIG.expectAspect=0.7048;\n               window.SCANNER_CONFIG.expectLabel=\'half-A4 bill\';}\n             else{delete window.SCANNER_CONFIG.expectAspect;\n               delete window.SCANNER_CONFIG.expectLabel;}}\n           var h=document.getElementById(\'lane_basic\'); if(h){h.value=this.value;}">'


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already carries the size prior -- nothing to do")
        return 0
    n = src.count(OLD)
    if n != 1:
        raise SystemExit("REFUSED: the lane block matches %d times (need exactly 1). "
                         "Is S219_PHARMA_LANE installed? Nothing has been changed." % n)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S219_sizeprior_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src.replace(OLD, NEW, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: compile failed (%s); restored from %s" % (ex, bak))
    print("patched %s (size prior: half A4)" % TARGET)
    print("backup  %s" % bak)
    print("restart: systemctl restart assetapp.service")
    return 0


if __name__ == "__main__":
    sys.exit(main())
