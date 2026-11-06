# START HERE — SESSION 398 — the Scan App chat (papers & bills)

*Written at the S395 close (06-Nov-2026, evening) by the Scan App chat. Session **398 is RESERVED for this project** on the board (`board/_numbers`): take it there as the FIRST act (NUMBERS_PROTOCOL_v1). The project's custom instructions (COMMON_START_HERE_PROMPT_v1) govern every reply.*

## A · The open (OPEN_ROUTINE_v1)

1. **Connections:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup` — report by name. The device shell; never `git` in it. **The device VM's disk is full (0 free):** build in the cloud workspace on code from the bundle and the kits; nothing is unpacked in the VM.
2. **The session number:** 398 from `board/_numbers` by a pinned write; the clock from the clock tool — and every minute written on the board read, never `2x` (F-510).
3. **The board:** every unread message, every note since 06-Nov 21:2x IST. The packs page reminder (D713).
4. **The day's checks once a day:** `D:\Downloads\_kbtools\DAY_OPEN_LATEST.txt` — read it; run `day_open.py` only when it is not today's or a publish or a bundle came since (the parent's S394 closed F-1151: follow the day page's own line for the device shell).
5. **The publish landed:** this close's record (papers only) — `main` = `origin/main`.
6. **The pins:** `/root/assetapp/asset_register.py` **16a2abea** (S737), `/root/assetapp/stationery.py` **2abbc10a** (S735), `/root/assetapp/sorting_desk.py` **52e959da** (S732) DECLARED-PENDING — CONFIRMED when a bundle holds them (none since 04-Nov 21:44, F-1124, the parent's).

## B · The work — in this order

1. **What he did since:** read the Stationery page live (read-only sub-agent): October's statement made? sent? Variety's bill joined, paid? Build only a gap found. Read the Recent-scans switch on /admin: if he switched it ON, read the home page and All papers live as him and as Shavez (no Personal paper for Shavez).
2. **F-1159 + D845 (3) — one kit on `sorting_desk.py`, read WHOLE first (drift 4):** a listed supplier's challan opened on the desk says *sort it on the Stationery page* with the link, and its destination buttons do not move it; and Yuvika's goods to the Procedure room panel on D797's pattern (Variety → Stationery). The panel shown to him (a mock-up) before install; a new staff screen installs switched off.
3. **F-1160 — the product box on the Stationery page:** a searchable list (S715's supplier-box pattern) in place of the datalist, in the next kit on `stationery.py`.
4. **D845 (4) — the NK share into NK Pathology's accounts:** a written plan (the NK ledger of S674 — its first line is B-0235, NK AYUSHMAN PAD — into NK's own accounts), for the parent (`finance_app.py`) and the NK Pathology chat; PLANNED lines first; the scan app's part after they agree.

Then the rest of §2C of the Runbook v310.

## C · What this project is now (S395)

- **The Stationery page's statements (S735):** while no statement stands for the month just ended (nor this month) and it has unbilled lines, section 5 offers *Make <last month>'s statement* first; once it stands, the page is as before. The start day `stationery.suppliers_from` = **2026-10-26** (moved from 28-Oct by his line, F-1158). October: 16 lines on 7 papers (B-0235 NK), his to make.
- **Recent scans by scan date (S737), SWITCHED OFF** (`recent.on`; Admin → *Recent scans by scan date*): ON = the home page's three counts and *Recent scans* (owner and manager; IST scan day; 7/14/30; All · Needs someone · Clinic · NK · Dr MK · Pharmacy; *where it sits* from the desk's own list first) and All papers newest scan first with Scanned and Where it sits (`?order=bill` today's order). OFF = both pages byte-identical to before.
- **The reading, the desk, X-ray films:** as S392 left them (Book §21).

## D · Kits and pins

- **S735_STMT_LAST_MONTH** — live 19:59 IST 06-Nov; `stationery.py` 3a22c6bb → 2abbc10a; undo: `\cp -p /root/assetapp/stationery.py.bak_S735_3a22c6bb /root/assetapp/stationery.py && systemctl restart assetapp`.
- **S737_RECENT_SCANS** — live 20:40 IST 06-Nov, switched OFF; `asset_register.py` 5f44f65e → 16a2abea; undo: `\cp -p /root/assetapp/asset_register.py.bak_S737_5f44f65e /root/assetapp/asset_register.py && systemctl restart assetapp` (or the switch OFF).
- **The data line of 21:07 IST:** `stationery.suppliers_from` 2026-10-28 → 2026-10-26; undo: the same guarded line with the two dates swapped (Archive §S395).
- Read-only pins unchanged: `procroom.py` e51c00a1 · `clinic_papers.py` 89a3cd0a · `claude_reader.py` 1277e80d · `claude_reread.py` ed7023d2 · `batteries.py` bb082b4c · `xray_costs.py` 5823bae2 · `asset_machine.py` 7dbd5e0c · `scanner_widget.js` b936f0f3 · `/root/shared/scan_checks_s441.py` 10787cbf.
- The kits' walks run on a copy of the bundle's scan-app code in the cloud: `walk_s735_app.py`, `walk_s737_app.py` (the real app, every part, made-up rows; a made-up clock — `stationery.TODAY`, `asset_register.S737_NOW`, the desk's `_today`).

## E · Lessons of S395 (carried into the NEVER list of §2C)

- A flow that waits on a month end must be able to make the month just ended — read the page's own month rule before calling it done (F-1157).
- A start day hides what came just before it: compare All papers with the account for the listed supplier (F-1158).
- A save that a screen refuses can still move the paper by another door — replay his exact save on the real app before guessing (F-1159).
- A kit that changes the home page: prove OFF byte-identical, and get a cold review; it found a real mislabel.
- Every board minute is read from the clock, never estimated (F-510).
