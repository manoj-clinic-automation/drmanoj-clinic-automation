REINSTALL -- THE RECEPTION PC AGENT (kit S448_RECEPTION_AGENT)
==============================================================

One kit rebuilds everything the clinic's system needs on the reception PC.
The agent's own part is ONE line. What is listed first is what only a person
can do, because each step is a sign-in or a Windows prompt.

A. WHAT ONLY A PERSON CAN DO -- in this order
   1. Windows, logged in as the reception user. (The agent starts at logon;
      nothing runs at the Windows login screen.)
   1a. THE CLINIC WI-FI -- only if this PC is to use Wi-Fi (no working LAN
      cable). The clinic's network "Airtel_Airtrl_mano_8080" is a Wi-Fi 6
      network. A fresh Windows 10 gives this PC's card (Intel Dual Band
      Wireless-AC 3160) Intel's driver of 2016 (18.33.0.2), and with that
      driver the clinic's network is NOT IN THE LIST AT ALL, while other
      networks are. It is not a password fault and not a router fault.
      Cure: put the PC on any other internet for ten minutes (a phone
      hotspot will do), then
         Settings > Update & Security > Windows Update >
         View optional updates > Driver updates
      tick  Intel - net - 4/29/2019 - 18.33.17.1  , press Download and
      install, and restart. The clinic's network is then in the list: join
      it, TICK "Connect automatically", and type the Wi-Fi password (the
      owner's; it is in no kit).
      Check, in a Command Prompt:
         netsh wlan show drivers      (Version reads 18.33.17.1)
         netsh wlan show interfaces   (SSID reads the clinic's network)
      (The fault of 02/03-Oct-2026 and its cure, F-693. The cabled port
      showed no link on those days: a cable or socket matter, not this.)
   2. Google Drive for desktop, signed in with the CLINIC Google account.
      "My Drive" must show Clinic Records and Clinic Data Archive.
      If Drive will not start with a permission error on
         C:\Users\<user>\AppData\Local\Google\DriveFS
      quit Drive, rename that folder (DriveFS_old_<date>), start Drive, sign
      in again. (The fault of 01-Oct-2026 and its cure.)
   3. Chrome, opened once, and Docterz signed in for the staff.
   4. The Claude desktop app is NOT put back on this PC. It was removed on
      03-Oct-2026 at the owner's word: Claude works here through signed jobs
      (the Drive door and the server door). The kit's config.json says
      "keep_claude_running": false, so the agent does not look for it.
   5. Tailscale (so the owner can view this PC from his own devices):
      install it from https://tailscale.com/download and sign in with the
      owner's account. The PC appears on his tailnet as "receptionpc".
   6. The read-only share for the owner, AFTER step B and after Tailscale:
      in this kit's folder, right-click share_setup.cmd, choose "Run as
      administrator", click Yes, and type the viewing password twice when
      the window asks.
      (It makes the account "clinicview", shares C:\ read-only as
      ReceptionC to Tailscale addresses only, switches Guest off and removes
      the old open shares. Its log: C:\ClinicAgent\share_setup_log.txt.)
   7. The firewall and the sharing rules, AFTER step 6: right-click
      C:\ClinicAgent\secure_setup.cmd (the installer puts it there; it is in
      this kit's folder too), choose "Run as administrator", click Yes.
      (Windows Firewall on for all three profiles; file sharing reachable
      from Tailscale addresses only; the licence server's ports left open to
      the clinic's own network; the old open shares removed. It starts no
      scan and changes no Windows Security exclusion. Safe to run again.
      Its log: C:\ClinicAgent\secure_setup_log.txt. Without this step a
      reinstalled PC has its firewall as Windows left it.)

B. THE AGENT -- THE SIMPLE WAY (since S450): in Chrome on this PC sign in to
   the clinic portal as Dr Manoj, open the tile "Clinic PCs", press
   "Set up this PC as the Reception PC", then Keep, then Run. The file it
   downloads fetches this kit from the clinic server, installs it, opens the
   direct road to the server, and offers step A.6 at its end. Nothing below
   in B is needed then.

   THE OLDER WAY, kept as the fallback (it needs Google Drive signed in
   first) -- press Windows key + R, paste, Enter
   (use the folder this kit is in; from the clinic Drive it is the line below)

   cmd /k "G:\My Drive\Clinic Data Archive\ToReception\S448_RECEPTION_AGENT_kit\INSTALL_RECEPTION_AGENT.bat"

   It ends with DONE or with STOP and a reason, and saves everything it
   printed beside itself as install_log.txt (no patient data in it).

   What it does: makes C:\ClinicAgent, unpacks its own Python 3.11.9 there,
   copies the agent and its guard and compares them byte for byte, compiles
   them, runs a read-only self-test, brings config.json and the Drive-door
   public keys from the kit if the PC has none, points Chrome's download
   folder at Clinic Records\Docterz exports (only if Chrome is closed --
   otherwise the agent does it itself the next time Chrome is closed), sets
   the start at logon, starts the agent and shows its first heartbeat.
   It also puts share_setup.cmd and secure_setup.cmd beside the agent in
   C:\ClinicAgent, for steps A.6 and A.7. Safe to run again at any time.

C. THE CHECKS THAT PROVE IT WORKED
   1. The window says DONE and shows a heartbeat with "ATTENTION: nothing".
   2. C:\ClinicAgent\heartbeat.txt is rewritten every 5 minutes.
   3. The same heartbeat appears in the clinic Drive:
         My Drive\Clinic Data Archive\FromReception\heartbeat.txt
   4. Log out and log in again: the heartbeat's "up since" is after the logon.
   5. From a Claude chat: a job dropped into C:\ClinicAgent\jobs\in comes
      back in C:\ClinicAgent\jobs\out (local door), or a signed job put into
      My Drive\Clinic Data Archive\ToReception\jobs comes back in
      FromReception\results (Drive door).
   6. THE DIRECT ROAD TO THE SERVER (S449). The heartbeat's SERVER line reads
      "direct upload on | last accepted <a time>". After a REINSTALL the PC
      makes a NEW upload key, so the server refuses it until that key is
      enrolled: the heartbeat then shows "public_key" (heartbeat.json) and an
      attention line. Claude enrolls it on the server (reception_keys.txt,
      kit S449_RECEPTION_UPLOAD) -- nothing for a person to do at the desk.
   7. HOW CURRENT WINDOWS IS (S456). The heartbeat's WINDOWS line names the
      build, the date of the system files and the day the last cumulative
      update went in; the clinic's health page says the same in its
      Reception PC row. Nothing for a person to do at the desk.

D. WHAT THE KIT HOLDS
   INSTALL_RECEPTION_AGENT.bat   the installer (this is all a person runs)
   reception_agent.py            the agent
   agent_guard.py                keeps the agent alive, undoes a bad update
   pyportable.zip                CPython 3.11.9, standard library only
   config.json                   this PC's settings (no Claude app kept running)
   authorized_keys.txt           PUBLIC keys allowed to send jobs through Drive
                                 (may be absent: then the Drive door is shut)
   reception_sign.py             for a Claude session: make a key, sign a job
   share_setup.cmd               the owner's read-only view of this PC (A.6)
   secure_setup.cmd              the firewall and the sharing rules (A.7)
   tests\test_kit.py             the offline walk
   MD5SUMS.txt                   the md5 of every file above

   Before a reinstall, compare the kit with MD5SUMS.txt and with the pins in
   the Register: the repository's copy (deploy_kits\S448_RECEPTION_AGENT) is
   the authoritative one, the Drive copy is the convenient one.

E. WHAT THE KIT DELIBERATELY DOES NOT HOLD
   Any password, token or signing secret. The signing secret for Drive jobs
   lives on the owner's PC only. The secret that signs this PC's uploads to
   the server is made ON this PC (C:\ClinicAgent\upload_key.txt) and is in
   no kit, no Drive folder and no backup -- a reinstall simply makes a new
   one. No patient data.

F. THE SWITCH
   C:\ClinicAgent\_off\ALL_OFF.txt   -- no jobs, no repairs, no updates;
   the heartbeat goes on and says OFF. Delete the file (or put the single
   word ON in it) to switch back on.
