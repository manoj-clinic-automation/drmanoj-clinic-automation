# S459_MANOJZ_PC_KIT — session 292, 03-Oct-2026

**What a whole reading of this PC found (F-705).** Much of the clinic's work that lives only on Dr Manoj's PC was in **no backup**: the follow-up tracker's code, its settings and key files, `margsync\_config` (the machine settings and this PC's signing key for the Reception PC's jobs and for the Docterz fetch), the Docterz archive, and the definitions of the scheduled tasks that run everything. The nightly mirrored the knowledge base and the server's code only. *What WAS covered, and stays as it is:* the tracker's twelve ledger files have a nightly Drive copy (F-261 records it; the owner corrected the assistant on exactly this at S230), and the patient master is mirrored to its Google Sheet every morning. **A first draft of this page said the ledgers were in no backup; that was asserted from one source and was wrong — corrected before it was published.**

**Two parts.**

1. **`pc_state_backup.py` — step 2b of the 03:10 nightly** (`NIGHTLY.bat`, one block). One dated zip to `F:\ClinicBackup\DrManojClinic_Automation\05_PC_STATE\manojz\`: the tracker folder, `margsync\_config`, `MargPull` (not its logs), `_off`, `SendToClinic`, `_analysis`, the loose files of `margsync`, `DocterzArchive`, `_kbtools` (not `vps_code`), `D:\clinic_writer`, every scheduled task of Task Scheduler's top folder as Windows exports it, and `MACHINE_FACTS.txt` (Python and its packages, git, drives, start-up entries). Reopened, every CRC tested; newest 7 kept, older moved aside; report `D:\Downloads\_kbtools\PC_STATE_BACKUP_LATEST.txt` (counts and sizes only). **The zip holds patient data and this PC's secrets; it goes to the SSD and nowhere else.**
2. **`setup_pc.py` — the Clinic PCs kit for this PC.** Restores from the newest of those zips, and **only puts back what is not there**: a folder only if it does not exist, a task only if Task Scheduler has none of that name (made for the new account — the old account's id is replaced), a Python package only if missing; the knowledge base from the newest nightly mirror if absent. On the working PC it is a read-only check.

**Placed on manojz by the assistant (the nightly is the assistant's own):** `D:\Downloads\_kbtools\pc_state_backup.py`, `NIGHTLY.bat` (the old one kept as `.bak_S459_d0a555b6`), `S459_SUMS.md5`, `S459_README.md`.

**Proved offline:** `test_setup_manojz.py <this folder>` — 29 checks, the backup and the restore end to end on stand-ins.

**The limit, said plainly:** the SSD sits at this PC. A dead disk is covered; a fire or theft that takes both is not. An off-site, encrypted copy is the next step, not built.

**Owed:** the first real night (the task export and the machine facts run only on Windows); then the button pressed once on this PC, where it must report every folder *already here* and no task made.
