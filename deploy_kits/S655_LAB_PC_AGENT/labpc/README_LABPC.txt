THE LAB PC AGENT (kit S655) -- what is on this PC and what a person does
==========================================================================

INSTALL (once): double-click INSTALL_LAB_AGENT.bat in this folder, as the
user Labmate runs under. It puts everything in C:\ClinicLabAgent, starts the
agent, shows its first heartbeat, and prints this PC's PUBLIC KEY (also
copied to the clinic Drive, Clinic Data Archive\FromLab\lab_public_key.txt).
Tell the owner the window said DONE. Nothing else to do on this PC.

WHAT IT DOES BY ITSELF
  - starts at every logon (Startup folder: ClinicLabAgent.cmd)
  - every 5 minutes: a heartbeat (counts and dates, never a name) to the
    clinic Drive (FromLab\heartbeat.txt) and to the clinic server
  - ~5 minutes after switch-on and every 3 hours: copies lab.mdb and
    Captdata.mdb from E:\Labmate982, zips them, sends the zip to the clinic
    server in signed parts. Labmate is never opened, never stopped, never
    changed. The staff's own backup (Backupdata) is untouched.
  - runs a job the owner sends it (signed; through Drive ToLab\jobs or the
    server), writes the output back

WHAT A PERSON NEVER HAS TO DO
  - nothing daily. The PC is switched off in the evening and on at ~08:30 as
    always; the agent catches up at switch-on.

SWITCHES (files, for the owner)
  C:\ClinicLabAgent\_off\ALL_OFF.txt   -- stops repairs and jobs (heartbeat continues)
  C:\ClinicLabAgent\_off\JOBS_OFF.txt  -- stops jobs only
  config.json "snapshot_enabled": false  -- stops the Labmate snapshot

REMOVING THE CLAUDE APP (the owner's word, after the server side is in):
  double-click REMOVE_CLAUDE_APP.bat. It refuses until the agent's heartbeat
  says the server accepted it. Then Chrome > profile picture > Sign out.

IF SOMETHING LOOKS WRONG: read C:\ClinicLabAgent\heartbeat.txt (plain words)
and agent.log. Nothing in either is a patient record.
