' ===========================================================================
'  RUN_HIDDEN.vbs  --  S236, 09-Sep-2026.
'
'  A GENERIC hidden launcher.  Give it a batch file (and any arguments that
'  batch expects) and it runs it with NO CONSOLE WINDOW.
'
'  WHY THIS EXISTS
'      PULL_HIDDEN.vbs (S201) did this for ONE job, hard-coded.  Three more
'      scheduled jobs arrived at S224 and S225 -- PULL_WATCHDOG,
'      EXPECTED_ON_CAPTURE and SNAPSHOT_ON_CAPTURE -- and every one of them
'      was registered to run its .bat DIRECTLY.  Windows opens a console for
'      each, so the owner got a window flashing on his screen every fifteen
'      minutes, three at a time.  The fix that had already been found at S201
'      was simply never applied to the jobs that came after it.
'
'      This file is generic so that the NEXT scheduled job cannot repeat it:
'      point the task at this, pass it the batch, and there is no window.
'
'  IT ADDS NO REDIRECTION.  Each of those batches already writes its own
'  console log.  Wrapping them in a second redirect would silently detach the
'  log they already keep, and a log that moves is worse than a log that is
'  ugly.
'
'  Window style 0 = hidden.  False = do not wait.
' ===========================================================================
Option Explicit
Dim sh, q, cmd, i

If WScript.Arguments.Count < 1 Then
    WScript.Quit 2          ' nothing to run; fail quietly, this is a launcher
End If

Set sh = CreateObject("WScript.Shell")
q = Chr(34)

' Rebuild the command line, quoting every part, so a path with a space in it
' cannot break the run.  cmd /c "" ... "" is the doubled-quote form cmd needs
' when the whole command is itself quoted.
cmd = q & WScript.Arguments(0) & q
For i = 1 To WScript.Arguments.Count - 1
    cmd = cmd & " " & q & WScript.Arguments(i) & q
Next

sh.Run "cmd /c " & q & cmd & q, 0, False
