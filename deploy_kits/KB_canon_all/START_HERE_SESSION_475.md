# START HERE — SESSION 475 — the Scan App chat (papers & bills)

*Written at the S466 close (17-Nov-2026, 11:3x IST, full EOS, HELD AT THE BUILD) by the Scan App chat. Session **475 is RESERVED for this project** on the board (`board/_numbers`): take it there as the FIRST act (NUMBERS_PROTOCOL_v1) with a SHORT line (under 400 characters). The project's custom instructions govern every reply.*

> **FIRST — place S466's held close.** Its parts are complete in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S466\close_parts\` (close.json written on top of the parent's held S471 parts: Register v5.302, Archive v1.299, Fault v2.286 §7.219, Runbook v382, Book v21). Read the board's READY lines and the manifest: if S471 has not been placed, or another close has been placed since, **re-base** — every version in the parts (v5.302 / v1.299 / v2.286 §7.219 / v382) and close.json's runbook `supersedes_old` / `supersedes_new` (they quote the current Runbook's top line), the todo markers, `brief_from` / `report_from` / `start_here_from` move with it. Then `TZ=Asia/Kolkata TMPDIR=/tmp python3 -B ~/mnt/Downloads/_kbtools/close_build.py ~/mnt/Downloads/ClaudeCowork/03_WORKING_PAPERS/S466/close_parts/close.json` from `/tmp`, read the table, then `--place`. The board line READY, then the owner's publish (one line).

## A · The open (OPEN_ROUTINE_v1)

1. **Connections:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup`. The device shell; never `git` in it. **The device VM's `/sessions` disk was replaced on 17-Nov (S472):** a chat whose link sits on the old disk cannot use the shell — the file tools still work; say so and open fresh. Scratch in `/tmp`, `TMPDIR=/tmp`; flask for a walk from `pip install --target /tmp/pydeps flask`.
2. **The number:** 475 by a pinned write; the clock from the clock tool. A kit number: read `kit_next`. Read `_numbers` whole only to write it (F-1405) — every write carries the whole `claims` array: copy it from your last read.
3. **The board:** unread messages to `scanapp`; the packs reminder (D713).
4. **The day's checks:** `D:\Downloads\_kbtools\DAY_OPEN_LATEST.txt` — run `day_open.py` only when it is not today's.
5. **The pins:** this project's DECLARED-PENDING 10 — S841's `claude_reader.py` 5b27b226 · `asset_register.py` b668771c; S464's `sorting_desk.py` 2eeb8b39 · `clinic_papers.py` 91305fe0 · `xray_costs.py` 0a296116 · `procroom.py` 38c5bbaa · `reader_watch.py` 5ba95fce · `scan_checks_s441.py` 5c934bdb — the placing's re-hold against the newest bundle says which are CONFIRMED.

## B · The work — in this order

1. **What he asks.** Nothing is waiting on a build.
2. **`clinic_papers.py` drift 5:** read WHOLE before any kit touches it.
3. **S841's known (Runbook §2C item 4):** a list of pharmacy credit notes not yet pointed at a bill would be a new staff screen — a mock-up first, only if he wants it.

## C · What this project is now (S466)

- **S841 live (21:17 IST 14-Nov):** a dealer's credit note scanned straight on the pharmacy lane is read by `read_pharmacy` with S835's credit-note kind and a pharmacy rule ("Credit Invoice / Cash-Credit / Credit Sale / Less CN" are bills); the paper is marked kind `Pharmacy credit note`, doc_kind `credit_note` before the row is filled (`_s550_claude` wrapper), healed after every POST / reading / start (doc_kind credit_note on the pharmacy lane as 'Pharmacy'; or a reading that says credit note on a never-marked row), unless a person re-laned it after the mark (`_s841_person_said` — the way back from a wrong recognition); the history rule never moves it; the bill edit page keeps the kind (F-1422). Switch `read.pharmacy_cn` (absent = ON). It opens on the desk with S835's box.
- **S835, S838 live (14-Nov):** credit notes on the sorting desk (`desk.cn` OFF for Shavez); Go to ▾ on the bar (`bar.goto` OFF for Shavez).

## D · Lessons of S466 (into §2C's NEVER list)

- Take a number on the board before writing it anywhere — a kit's README, block or installer (F-1437).
- A new paper kind goes into every kept-kind list of the app in the same kit (F-1422).
- A cold review's "way back" check: a heal that re-marks what a person undid is a trap (S841 point 2).
