THE OFF SWITCH  --  D:\SendToClinic\_off\              (S259, 14-Sep-2026)
==========================================================================

THE SWITCH IS A FILE. If a file with one of these names is sitting in this
folder, the job it names does not run. Delete the file and it runs again.
Nothing has to be restarted -- each job looks in this folder as it comes
round, and the pusher comes round every 60 seconds.

    ALL_OFF.txt              stops the SENDING of captured exports to the
                             clinic server. CAPTURE KEEPS RUNNING.
    MARG_PUSH_OFF.txt        the same thing, for the sending alone

    MARG_WATCH_OFF.txt       *** STOPS CAPTURE ITSELF ***

WHY CAPTURE HAS ITS OWN, SEPARATE SWITCH -- AND WHY ALL_OFF DOES NOT TOUCH IT

Marg reuses the same file name for every report it exports. The moment a
new report is made, the previous export is overwritten and gone. Capture
exists to copy it out of the way in that instant. Everything else in this
system can be paused and caught up later; an export that was never
captured cannot be recovered from anywhere.

So ALL_OFF.txt stops the sending and leaves capture alone. Stopping capture
takes its own file, named for it, put there on purpose.

    D:\SendToClinic\TURN_OFF_ALL.bat      switch the sending off
    D:\SendToClinic\TURN_ON_ALL.bat       switch everything back on

Nothing switched off is lost: captured exports wait in _captured and are
sent when the switch goes back on.

The contents of these files do not matter. An empty file is enough.
