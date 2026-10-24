#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
near_expiry.py -- S638_EXPIRY_WATCH (Sanjeevni, session 348, 24-Oct-2026).  Replaces S343_NEAR_EXPIRY's file whole (F-1009, D771).

The nightly line of S343 stays exactly as it is (crontab unchanged, 23:57):
    57 23 * * * cd /root/finance/spine && /root/wa/venv/bin/python3 -B near_expiry.py >> /root/finance/spine/near_expiry.log 2>&1

What it runs now is the EXPIRY WATCH (/root/finance/expiry_watch.py): Marg's Batch Stock (the one report with stock by batch, monthly,
filed by the door as BATCH_STOCK) lowered by the spine's own sale lines, made every night into the owner's list -- expired, near expiry
(counted to the day Marg stops selling the batch, F-1009: S343 counted three months on the expiry month itself and read the 'Stock
expiry' export, whose window Marg cuts at the operator's date), dump, wrong batch, new products, out of stock -- in finance.db's
stock_expiry_run / stock_expiry_line.  The screens read those tables.  S343's expiry/ folder is left as it was (nothing reads it).

    /root/wa/venv/bin/python3 -B /root/finance/spine/near_expiry.py [--date YYYY-MM-DD]
OFF: /root/finance/spine/OFF and /root/finance/_off/ALL_OFF (checked by expiry_watch.run).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIN = os.path.dirname(HERE)
if FIN not in sys.path:
    sys.path.insert(0, FIN)

import expiry_watch  # noqa: E402

KIT = "S638_EXPIRY_WATCH"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    return expiry_watch.main(["run"] + argv)


if __name__ == "__main__":
    sys.exit(main())
