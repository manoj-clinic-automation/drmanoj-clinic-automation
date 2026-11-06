# START HERE — SESSION 395 — the Scan App chat (papers & bills)

*Written at the S392 close (06-Nov-2026, evening) by the Scan App chat. Session **395 is RESERVED for this project** on the board (`board/_numbers`): take it there as the FIRST act (NUMBERS_PROTOCOL_v1). The project's custom instructions (COMMON_START_HERE_PROMPT_v1) govern every reply.*

## A · The open (OPEN_ROUTINE_v1)

1. **Connections:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup` — report by name. The device shell; never `git` in it.
2. **The session number:** 395 from `board/_numbers` by a pinned write; the clock from the clock tool.
3. **The board:** every unread message, every note since 06-Nov 18:0x IST. The packs page reminder (D713).
4. **The day's checks once a day.** In the device shell `day_open.py` needs the VM roots (F-1151):
   `cd $HOME/mnt/Downloads/_kbtools && python3 day_open.py --tools $HOME/mnt/Downloads/_kbtools --repo $HOME/mnt/dr-manoj-git/drmanoj-clinic-automation --kb $HOME/mnt/Downloads/ClaudeCowork --ssd $HOME/mnt/ClinicBackup/DrManojClinic_Automation --roots $HOME/mnt/Downloads $HOME/mnt/dr-manoj-git $HOME/mnt/ClinicBackup --read`
   (without `--read` when the page is not today's, or a publish or a bundle came since).
5. **The publish landed:** this close's record (papers only) — `main` = `origin/main`.
6. **The pins:** `/root/assetapp/asset_register.py` **5f44f65e** (S731) and `/root/assetapp/sorting_desk.py` **52e959da** (S732) DECLARED-PENDING — CONFIRMED when a bundle holds them (none since 04-Nov 21:44, F-1124, the parent's).

## B · The work — D845, in this order (the owner's "eos, build in fresh session then", 17:58 IST 06-Nov)

1. **The Variety flow's first month, checked end to end on the live page** (read-only sub-agents; screenshots never in the main thread): October's statement on the Stationery page challan by challan (Clinic / NK, B-0250's three Clinic lines of 05-Nov among them), the WhatsApp send (needs Variety's phone on Vendors — his), their bill joined to the challans and paid once. Build only a gap found, in a small kit.
2. **Recent scans by scan date** — for him and Shavez: a mock-up first (a Design canvas), built only on his "final". A new staff screen installs switched off.
3. **Yuvika's goods to the Procedure room panel** — her challans and slips land on the Procedure room lines by themselves, on D797's pattern (Variety → Stationery). A kit; the panel shown to him before install. **`sorting_desk.py` is at drift 4 — read it whole before this kit.**
4. **The NK share into NK Pathology's accounts** — a written plan (the NK ledger of S674 → NK's own accounts), for the parent (`finance_app.py`) and the NK Pathology chat; PLANNED lines first; the scan app's part after they agree.

Then the rest of §2C of the Runbook v307.

## C · What this project is now (S392)

- **The reading:** Claude reads every new scan on the clinic, NK and Dr MK lanes and every challan on any lane — never a person's paper (Personal, Resumes, a patient's paper) nor a letter or form on Other document (S731). A paper that was never put to Claude and says *read failed* is read once by itself after its desk Save or a lane move (`read_after_move` in its audit); a paper Claude already tried is not (*Read it again* stays).
- **The sorting desk** (`/scanapp/desk`): S715's supplier list, calendar, stationery lines, Variety's Clinic / NK, the procedure room search, *Read it again*; **S732's Other lines** for a paper in Others — what it is, quantity, unit, rate, + Add a line, ×, the amounts and the total — written as the paper's `bill_items` only when the panel was changed (`desk_lines` audit).
- **X-ray films:** no desk lines needed (D844) — the film bills are read with their size and boxes; the parent's film log and `xray_costs.py` read them.

## D · Kits and pins

- **S731_CHALLAN_READ** — live 17:1x IST 06-Nov; `asset_register.py` 63a8b15b → 5f44f65e, `sorting_desk.py` 4990350b → d2742ded; undo: `\cp -p /root/assetapp/asset_register.py.bak_S731_63a8b15b /root/assetapp/asset_register.py && \cp -p /root/assetapp/sorting_desk.py.bak_S731_4990350b /root/assetapp/sorting_desk.py && systemctl restart assetapp`.
- **S732_DESK_OTHER_LINES** — live 17:5x IST 06-Nov; `sorting_desk.py` d2742ded → 52e959da; undo: `\cp -p /root/assetapp/sorting_desk.py.bak_S732_d2742ded /root/assetapp/sorting_desk.py && systemctl restart assetapp`.
- Read-only pins unchanged: `procroom.py` e51c00a1 · `stationery.py` 3a22c6bb · `clinic_papers.py` 89a3cd0a · `claude_reader.py` 1277e80d · `claude_reread.py` ed7023d2 · `batteries.py` bb082b4c · `xray_costs.py` 5823bae2 · `asset_machine.py` 7dbd5e0c · `scanner_widget.js` b936f0f3 · `/root/shared/scan_checks_s441.py` 10787cbf.

## E · Lessons of S392 (carried into the NEVER list of §2C)

- A paper with no reading and no retry was never put to Claude: read `_s601_asked`'s exclusions before suspecting the reader (F-1136).
- Before building what he asked, check live whether it is needed — the X-ray film lines were not (D844).
- The device VM's disk can be full: a database copy cannot be unpacked there — one rehearsed read-only server line instead, short enough that his paste carries it whole.
- A control walk must report red, never crash: every check that reads a new element is null-safe.
