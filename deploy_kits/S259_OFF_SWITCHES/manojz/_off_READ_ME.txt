THE OFF SWITCH  --  D:\Downloads\margsync\_off\        (S259, 14-Sep-2026)
==========================================================================

THE SWITCH IS A FILE. If a file with one of these names is sitting in this
folder, the job it names does not run. Delete the file and it runs again.

Nothing has to be restarted, stopped, re-registered or re-installed. Each
job looks in this folder when it next comes round -- within 15 minutes for
the watchdog, at its next run for the stock push -- and does what it finds.

    ALL_OFF.txt              stops EVERYTHING on this PC that talks to
                             the clinic server
    PULL_WATCHDOG_OFF.txt    stops only the 15-minute "is the Marg pull
                             asleep?" check
    PUSH_STOCK_OFF.txt       stops only the stock push -- both the daily
                             one and the 22:30 nightly one

YOU DO NOT HAVE TO MAKE THESE FILES BY HAND. Two double-clicks do it:

    D:\Downloads\margsync\TURN_OFF_ALL.bat      switch everything off
    D:\Downloads\margsync\TURN_ON_ALL.bat       switch everything back on

WHAT IS SWITCHED OFF IS NOT LOST. Nothing is deleted and nothing is
skipped for ever: the archive keeps filling, and when the switch goes back
on the next run sends what it finds, including what it missed.

WHAT DOES *NOT* STOP. The 10-minute Marg pull from the medical PC still
runs, and the medical PC still captures every Marg export. That is on
purpose: an export that is not captured is gone for ever, because Marg
overwrites REPORT_1.XLS the moment the next report is made.

The contents of these files do not matter. An empty file is enough.
