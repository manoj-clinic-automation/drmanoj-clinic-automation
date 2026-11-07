# START HERE — SESSION 401 — the Scan App chat (papers & bills)

*Written at the S398 close (07-Nov-2026, 08:2x IST) by the Scan App chat. Session **401 is RESERVED for this project** on the board (`board/_numbers`): take it there as the FIRST act (NUMBERS_PROTOCOL_v1). The project's custom instructions (COMMON_START_HERE_PROMPT_v1) govern every reply.*

## A · The open (OPEN_ROUTINE_v1)

1. **Connections:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup` — report by name. The device shell; never `git` in it. Build in the cloud workspace on code from the bundle and the kits.
2. **The session number:** 401 from `board/_numbers` by a pinned write; the clock from the clock tool — every minute written on the board read, never `2x` (F-510).
3. **The board:** every unread message, every note since 07-Nov 08:2x IST. The packs page reminder (D713).
4. **The day's checks once a day:** `D:\Downloads\_kbtools\DAY_OPEN_LATEST.txt` — read it; run `day_open.py` only when it is not today's or a publish or a bundle came since.
5. **The publish landed:** this close's record (papers only) — `main` = `origin/main` (read `.git/logs/HEAD` and the refs).
6. **The pins:** `/root/assetapp/sorting_desk.py` **baa7c6aa** (S739), `/root/assetapp/stationery.py` **cfb3d8b5** (S746) DECLARED-PENDING — CONFIRMED when a bundle newer than 07-Nov 08:19 IST holds them. `asset_register.py` 16a2abea is CONFIRMED (07-Nov 03:18 bundle).

## B · The work — in this order

1. **What he did since, read live (read-only sub-agent):** the Stationery page — October's statement made? sent? a bill joined in either box, paid? An NK bill joined → it sits on the NK lane and shows in NK's pack 8.1 for its month. The Admin switches *Yuvika slips on the desk* and *Recent scans by scan date*: if he switched either ON, read its screens live as him and as Shavez. Build only a gap found.
2. **B-0176** (Yuvika slip, Procedure room, no line): ask him on the board for its lines if still empty; never guessed.
3. **The next kit on `sorting_desk.py` reads it WHOLE first** (drift 5).
4. **The review notes** of §2C item 8 — only folded into a kit that touches the file.

Then the rest of §2C of the Runbook v313.

## C · What this project is now (S398)

- **The sorting desk (S739):** a listed supplier's challan on the Stationery flow (from the start day, not placed elsewhere by a person, not left) shows a card *sorted on the Stationery page* with the link; its destinations and Save are off; the server refuses such a Save (a second-scan answer alone is saved, the paper not moved). A misread supplier picked as the listed one goes to Stationery & packaging with no lines. **Yuvika (switch `desk.yuvika`, OFF):** a bill number not read as a slip → Pharmacy; no number and no item → two buttons; else → Procedure room with its lines ready; a person's place is kept.
- **The Stationery page's product box (S741, S743):** a searchable list on the sorting form (product and unit); when nothing matches, the note first and every product below, nearest first; a name not on the list is still added on Save.
- **The statement (S746):** section 5 has a box for each side it holds — *Clinic's bill* and *NK Pathology's bill*. Each joins its own paper, takes rates for its own lines, is paid on its own. NK's paper is moved to the NK lane by the join (audited `relane`; an approved paper refused; an NK-lane paper refused as the Clinic's). The statement reads *paid* when every side is paid, *part billed* between. The NK ledger and the account read each side's own state. An estimate is joined the same way and stays out of the packs (D858). Columns `stationery_stmt.nk_*`.
- **The plan:** `S398_NK_SHARE_PLAN.md` (project knowledge and `03_WORKING_PAPERS\S398\`).

## D · Kits and pins

- **S739_DESK_YUVIKA_LISTED** — live 06:26 IST 07-Nov; `sorting_desk.py` 52e959da → baa7c6aa; undo: `\cp -p /root/assetapp/sorting_desk.py.bak_S739_52e959da /root/assetapp/sorting_desk.py && systemctl restart assetapp` (the Yuvika part alone: its switch OFF).
- **S741_STATIONERY_PRODUCT_PICK** — live 07:01 IST; `stationery.py` 2abbc10a → 8f85815d; backup `.bak_S741_2abbc10a`.
- **S743_STATIONERY_PICK_ALL** — live 07:22 IST; 8f85815d → d76a808d; backup `.bak_S743_8f85815d`.
- **S746_STMT_TWO_BILLS** — live 08:19 IST; d76a808d → cfb3d8b5; undo: `\cp -p /root/assetapp/stationery.py.bak_S746_d76a808d /root/assetapp/stationery.py && systemctl restart assetapp` (the five `nk_*` columns stay, unused by the older file; the database backup beside it).
- Read-only pins unchanged: `asset_register.py` 16a2abea · `procroom.py` e51c00a1 · `clinic_papers.py` 89a3cd0a · `claude_reader.py` 1277e80d · `claude_reread.py` ed7023d2 · `batteries.py` bb082b4c · `xray_costs.py` 5823bae2 · `asset_machine.py` 7dbd5e0c · `scanner_widget.js` b936f0f3 · `/root/shared/scan_checks_s441.py` 10787cbf.
- The kits' walks run on a copy of the bundle's scan-app code in the cloud: `walk_s739_app.py`, `walk_s741_page.py`, `walk_s743_page.py`, `walk_s746_app.py`, `walk_s746_page.py` (the real app, every part, made-up rows).

## E · Lessons of S398 (carried into the NEVER list of §2C)

- A ruling with two outcomes per supplier (Yuvika: slip vs printed bill) is best built as a suggestion behind a switch; the person's Save decides (D857).
- A screen that two pages can both move must have one owner; the other shows the link and refuses the save on the server too (F-1159).
- A searchable list must still list something when the box already holds a name not on it — the reader fills most boxes (F-1169).
- A new column that changes what old rows mean needs a carry-over, run before the new file is placed (F-1170).
- Never tell him a switch's state or where a paper is from the board or a list — read it live (F-1171).
