REINSTALL -- THE MEDICAL PC (kit S458_MEDICAL_PC_KIT)
=====================================================

The pharmacy counter PC. Marg runs here and every pharmacy report is born
here: Marg writes each report into a fixed file name and overwrites it at the
next export, so the clinic's watcher ON THIS PC must copy it within seconds.
That watcher, the agent that keeps it alive, and the tools around them are
what this kit puts back.

A. WHAT ONLY A PERSON CAN DO -- in this order, BEFORE the button
   1. Windows, with its two accounts: SET (WITH a password -- an account
      without one cannot serve the share) and the staff account "user".
      The PC signs itself in as SET at power-on (netplwiz), so the agent
      starts without anyone at the desk.
   2. Marg ERP and its data at D:\MARGERP. The Marg engineer restores it
      from the newest backup: the pen drive (E:), or the clinic Drive,
      Clinic Data Archive\MargBackups. He also sets Marg's own scheduled
      backup again.
   3. D: shared as DDrive for the owner's PC (it pulls the captures every
      ten minutes), and Tailscale signed in with the owner's account -- this
      PC is "medical" on his tailnet.
   4. Google Drive for desktop, signed in with the CLINIC Google account.
      The agent finds My Drive by itself. Its heartbeat goes to
      Clinic Data Archive\FromMedical; newer tools come to it from
      Clinic Data Archive\ToMedical\_kit.

B. THE BUTTON
   In Chrome on this PC, signed in to Windows as SET: sign in to the clinic
   portal as Dr Manoj, open the tile "Clinic PCs", press "Set up this PC as
   the Medical PC", then Keep, then Run. The file it downloads fetches this
   kit from the clinic server, checks every file, and runs setup_pc.py:

      1  the kit is whole
      2  D:\SendToClinic (made if it is not there)
      3  its own Python 3.11.9 in D:\SendToClinic\pyportable
      4  the tools -- ONLY WHAT IS MISSING is placed
      5  this account starts the agent at every sign-in
      6  the agent is started; its first heartbeat is read back

   IT NEVER REPLACES A FILE THAT IS ALREADY THERE. Run on the working PC it
   changes nothing; that is also how it is rehearsed. A tool that was
   updated after this kit was packed is left as it is, and after a
   reinstall the agent brings the current tools from the clinic Drive by
   itself (step A.4).

   It ends with DONE, or with STOP and a reason. Safe to run again.

C. AFTER THE BUTTON
   1. token.txt. The capture works without it; the SEND to the clinic
      server does not. It is in no kit. Tell Claude the PC is back: Claude
      gives the one line that puts it in D:\SendToClinic.
   2. The staff account: sign in as "user" once and double-click
         D:\SendToClinic\ENABLE_AGENT_THIS_ACCOUNT.bat
      so the agent also starts when that account signs in.

D. THE CHECKS THAT PROVE IT WORKED
   1. The window says DONE.
   2. D:\SendToClinic\heartbeat.txt is rewritten every five minutes and
      says  WATCHER : ALIVE .
   3. The same heartbeat appears in the clinic Drive:
         My Drive\Clinic Data Archive\FromMedical
   4. Export any report in Marg: within seconds a new file is in
         D:\SendToClinic\_captured
   5. On the clinic's health page the rows "Medical PC capture" and
      "Medical PC reachable" read normal.

E. WHAT THE KIT HOLDS
   setup_pc.py                   the installer the button runs
   README_REINSTALL_MEDICAL.txt  this file
   MD5SUMS.txt                   the md5 of every file in the kit
   payload\                      the tools, exactly as the working PC had
                                 them on the day the kit was packed (the
                                 agent and its guard, the starter, the
                                 watcher, the text reader, the sender, the
                                 switches, the two small libraries)
   Its Python comes separately from the clinic server (the same 3.11.9 the
   Reception PC uses).

   NOT IN THE KIT, on purpose: token.txt; Marg; anything captured; any log;
   the old manual "guard and send" trio of August (GUARD_AND_SEND.bat,
   guard_and_send.py, marg_report.py) -- retired since the agent sends by
   itself.
   AutoHotkey64.exe (the old export macro's program) is not in it either --
   its installer is on the owner's SSD, F:\ClinicBackup\Tools-Installers,
   and is needed only if the macro is ever used again.

F. THE SWITCHES
   D:\SendToClinic\TURN_OFF_ALL.bat and TURN_ON_ALL.bat (they write and
   remove files in D:\SendToClinic\_off). ALL OFF stops the sending, never
   the capture: an export not captured in that instant is gone for ever.
