REINSTALL -- DR MANOJ'S OWN PC, "manojz" (kit S459_MANOJZ_PC_KIT)
==================================================================

This PC runs the nightly record-keeping, the pull of the pharmacy's reports
from the Medical PC, and the follow-up tracker with its ledgers. Almost
none of that is in a kit: it is this PC's own state. Since 03-Oct-2026 the
03:10 nightly zips that state to the ClinicBackup SSD every night, and the
button on the Clinic PCs page restores from the newest of those zips.

A. WHAT ONLY A PERSON CAN DO
   Any order. The button can be pressed before any of these: it says what
   is still missing, and it is safe to press again afterwards.
   1. Windows, with your own account. The ClinicBackup SSD plugged in --
      it must show as drive F:.
   2. Python from python.org, with "Add python.exe to PATH" ticked.
   3. Git for Windows.
   4. Google Drive for desktop, signed in with the clinic account, as
      drive H:.
   5. Tailscale, signed in.
   6. The Claude desktop app.

B. THE BUTTON
   In Chrome on this PC: sign in to the clinic portal as Dr Manoj, open the
   tile "Clinic PCs", press "Set up this PC as Dr Manoj's PC", then Keep,
   then Run. The file it downloads fetches this kit from the clinic server
   and runs setup_pc.py:

      1  the kit is whole
      2  the SSD and the newest state zip (every file in it tested)
      3  the folders: the follow-up tracker with its ledgers and settings,
         the Marg pull with its settings and switches, the nightly tools,
         the Docterz archive, the Vitals tool
      4  the knowledge base (D:\Downloads\ClaudeCowork), from the newest
         nightly mirror
      5  Python's packages, the ones this PC had
      6  the scheduled tasks, exactly as Windows had exported them, made
         for your new account
      7  a list of part A with what this PC already has ticked

   IT ONLY PUTS BACK WHAT IS NOT THERE. A folder that exists is not opened,
   a task that exists is not touched, a package that is installed is not
   installed again. On the working PC it is a read-only check; that is how
   it is rehearsed.

C. AFTER THE BUTTON
   1. The repository. Sign in to GitHub once, then:
         git clone https://github.com/manoj-clinic-automation/drmanoj-clinic-automation.git "D:\dr-manoj-git\drmanoj-clinic-automation"
      (Three of the scheduled tasks run tools from inside it.)
   2. The Medical PC's share login, stored on this PC. Claude gives the one
      line; the password is yours.
   3. If the window says some tasks need an administrator: right-click the
      downloaded setup file, Run as administrator, once more.
   4. In the Claude desktop app, connect the folders again: D:\Downloads,
      D:\dr-manoj-git, F:\ClinicBackup.

D. THE CHECKS THAT PROVE IT WORKED
   1. The window says DONE.
   2. D:\Downloads\DocterzArchive\_last_pass.txt is rewritten every five
      minutes.
   3. D:\Downloads\margsync\MargPull\_last_pull.txt is rewritten every ten
      minutes.
   4. Next morning the nightly's reports in D:\Downloads\_kbtools carry
      that night's date, PC_STATE_BACKUP_LATEST.txt among them.
   5. The follow-up tracker opens (open_tracker.bat in its folder) and
      shows its patients.

E. WHAT IS, AND IS NOT, IN THE KIT
   The kit holds the installer and this page -- no data, no secret. The
   state it restores is on the SSD:
      F:\ClinicBackup\DrManojClinic_Automation\05_PC_STATE\manojz
   one zip a night, the newest seven kept. Those zips hold patient data and
   this PC's own keys; they are written to the SSD and nowhere else.

   THE LIMIT, said plainly: the SSD sits at this PC. A disk that dies is
   covered. A fire or a theft that takes the PC and the SSD together is
   not -- there is no off-site copy of this PC's state yet.

F. WHERE THE STATE COMES FROM
   D:\Downloads\_kbtools\pc_state_backup.py, run by NIGHTLY.bat at 03:10.
   What it wrote last: D:\Downloads\_kbtools\PC_STATE_BACKUP_LATEST.txt
