' ===========================================================================
'  PULL_HIDDEN.vbs  --  S201.  Runs the 10-minute Marg pull with NO window.
'
'  Called two ways, and both must end up here:
'    * by the scheduled task, once it has been repointed at this file;
'    * by PULL_FROM_MEDICAL.bat itself, which hands off to this the moment it
'      notices it was started with a console.
'
'  The "HIDDEN" second argument is what stops that hand-off looping: the batch
'  only re-launches when it is NOT already the hidden copy.
'
'  Window style 0 = hidden. False = do not wait for it to finish.
' ===========================================================================
'  S203_R2: the pull now keeps its console output.
'
'  Until now this line discarded it. The batch prints what every step did --
'  what was captured, what was routed, what was sent, why a send failed -- and
'  all of it went nowhere, every ten minutes, because nothing was redirected.
'  On 26-Aug the feed was dark for 8h40m and there was no record to read.
'
'  One file per month, so it rotates itself and can be sent as one attachment.
'  Chr(34) is used for the quote character instead of doubled quotes: the
'  nesting a redirect needs inside cmd /c is exactly where this kind of line
'  goes wrong, and a name is easier to check than a run of quotation marks.
Dim sh, fso, here, logdir, logfile, q
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
here = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
logdir = here & "_logs"
If Not fso.FolderExists(logdir) Then fso.CreateFolder(logdir)
logfile = logdir & "\pull_console_" & Year(Now) & "-" & Right("0" & Month(Now), 2) & ".log"
q = Chr(34)
sh.Run "cmd /c " & q & q & here & "PULL_FROM_MEDICAL.bat" & q & _
       " AUTO HIDDEN >>" & q & logfile & q & " 2>&1" & q, 0, False
