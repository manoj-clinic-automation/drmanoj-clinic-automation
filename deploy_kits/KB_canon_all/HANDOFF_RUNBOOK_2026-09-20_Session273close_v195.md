# HANDOFF RUNBOOK — v195 — S273 CLOSE (the parent), 20-Sep-2026

*Supersedes v194 (S274 close, the Sanjeevni project) for the parent's thread; v194's Sanjeevni sections remain its own record.*

## §0 · WHAT HAPPENED
The 360° patient record went live in one morning, 08:00–10:30 IST. There were seven installed kits (S332, S333, S335, S339, S342, S344, S346) and two frozen kits that refused themselves (S340, S345; F-581). The doctors' record page is on the portal; *Check karein* is at reception; blood reports, WhatsApp media and added papers flow into the clinic Drive through the mailbox script, which the assistant placed itself in the owner's signed-in browser (D577). New fault codes: F-579 … F-584. Decisions: D573 … D577. No SOP change for staff beyond *Check karein* and the X-ray test folder.

## §1 · MENTAL MODELS
- **Drive holds the files; the server holds the index** (D573). Reads go through `records_drive.py` under the venv, because the finance app's python has no Google libraries (F-579).
- **The mailbox script is the only Drive writer** (D574). The server asks and records; the script saves.
- **Nothing is filed by a guess** (D576). Reception confirms.
- **Walks on live data assert only about their own rows** (F-581).

## §2 · THE LIVE BACKLOG
See `S273_BUILD_BRIEF.md §2` and `OWNER_TODO_LIVE.md`. Next: live X-ray filing after 2–3 days of test files.

## §3 · INSTALL DISCIPLINE
Every kit carried its own walk on a scratch copy of the live database, backups beside each file, and a restore on red. Two refusals (S340, S345) installed nothing; their successors carried the same payload byte-identical with the walk corrected. The frozen folders stay in the repository as record.

## §4 · THE BOUNDARY
The VPS needs the owner (one line each). The Apps Script now needs only his sign-in, and the built-in browser holds drmka.ortho as account `/u/1/`. manojz: the shell works again this session (`device_bash`), with python + flask installed in its VM for walks.
