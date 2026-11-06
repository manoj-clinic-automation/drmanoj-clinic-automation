# START HERE — SESSION 392 — the Scan App chat (papers & bills)

*Written at the S363 close (06-Nov-2026, midday) by the Scan App chat. Session **392 is RESERVED for this project** on the board (`board/_numbers`): take it there as the FIRST act (NUMBERS_PROTOCOL_v1). The project's custom instructions (COMMON_START_HERE_PROMPT_v1) govern every reply.*

## A · The open (OPEN_ROUTINE_v1)

1. **Connections:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup` — report by name. The device shell; never `git` in it.
2. **The session number:** 392 from `board/_numbers` by a pinned write; the clock from the clock tool.
3. **The board:** every unread message, every note since 06-Nov 12:5x IST. The packs page reminder (D713).
4. **The day's checks once a day:** `python D:\Downloads\_kbtools\day_open.py --read` (run it only when the page is not today's).
5. **The publish landed:** this close's record (papers only) — `main` = `origin/main`.
6. **The pins:** `/root/assetapp/sorting_desk.py` **4990350b** (S715) DECLARED-PENDING until the 07-Nov bundle — CONFIRMED when the bundle holds it.

## B · The work, in order

1. **F-1136 — why B-0250 (a Variety Stationers challan, scanned 05-Nov 15:10 IST) was never read.** The screens say only *read failed*. The cause is in the box's own record: `bills.ocr_status`, `claude_reading` (ok, model, error, at) and `bill_audit` (read_retry, filled) for B-0250 and the week's other unread papers. Read it from the 07-Nov database copy in the device VM (never the cloud workspace, D656; delete the copy after) — or, if the copy lacks it, one read-only server line for the owner. Say the cause in one line; build only the fix it needs. Do not hand him diagnostics.
2. **S715 in use:** read the desk live after the first papers are sorted on it — a supplier picked from the list, a new item added from a line (its unit and rate on the owner's Stationery page), a Variety challan's Clinic / NK lines and their day (= the challan's date) on the Stationery page's account. A fault found is fixed in a small kit on 4990350b.
3. **D838's second kit, only on his word:** X-ray film lines and Others lines on the desk (new storage; the X-ray films are read by the parent's `xray_film.py` — a PLANNED line, the parent told).
4. **The rest of §2C of the Runbook** (v304): the Variety flow's first month, Yuvika's goods flow, recent scans by date, the NK share, the review notes of S715 (the desk's move of a mixed Variety challan voids its NK lines; rates in a manager's JSON), the small points.

## C · What this project is now (S363)

- **The sorting desk** (`/scanapp/desk`, S551 … S715): the supplier picked from `/desk/api/suppliers` (sorted papers only, a listed supplier always, never a person's papers or the pharmacy lane, the owner's expense lane to him only); `f_date` a calendar; the stationery lines with *+ Add a line*, ×, the item search, *+ Add <name> to the list* (unit, rate — the rate the owner's alone); a listed (Variety) challan's lines Clinic or NK, dated by the challan; the procedure room product search; *Read it again* through `/bills/<id>/reread`.
- **The Stationery page** (S674) sorts a listed supplier's read challans as before; the desk now sorts them too.
- **The battery places** (`/scanapp/batteries`): *Old battery ₹* on a fitting is the scrap money; the cost shows price − old battery.

## D · Kits and pins

- **S715_DESK_ITEM_LINES** — live 11:07 IST 06-Nov; `sorting_desk.py` 35fdd6c5 → 4990350b; undo: `\cp -p /root/assetapp/sorting_desk.py.bak_S715_35fdd6c5 /root/assetapp/sorting_desk.py && systemctl restart assetapp`.
- Read-only pins unchanged: `procroom.py` e51c00a1 · `stationery.py` 3a22c6bb · `asset_register.py` 63a8b15b · `clinic_papers.py` 89a3cd0a · `claude_reader.py` 1277e80d · `claude_reread.py` ed7023d2 · `batteries.py` bb082b4c · `xray_costs.py` 5823bae2 · `asset_machine.py` 7dbd5e0c · `scanner_widget.js` b936f0f3 · `/root/shared/scan_checks_s441.py` 10787cbf.

## E · Lessons of S363 (carried into the NEVER list of §2C)

- When manojz is off the link, a kit can be built in the cloud from the live bytes the repository already holds whole (a kit folder whose file = the pin) — the walk of the real app and the rehearsal still wait for the PC (F-1136's lesson is the other way: a read the owner's paste dropped is re-read, never assumed).
- A kit's own build step runs with the installer's exact arguments before review (F-1138).
- A cached panel redraws when anything its fields depend on changes — the paper type, the supplier (F-1139).
- A fresh rehearsal database lacks columns the live one has (`page_of`, `mixed`): add them in the walk, as S674's does.
