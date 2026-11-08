# START HERE — SESSION 409 — the Scan App chat (papers & bills)

*Written at the S401 close (08-Nov-2026, 18:5x IST, EOS-light) by the Scan App chat. Session **409 is RESERVED for this project** on the board (`board/_numbers`): take it there as the FIRST act (NUMBERS_PROTOCOL_v1). The project's custom instructions (COMMON_START_HERE_PROMPT_v1) govern every reply.*

## A · The open (OPEN_ROUTINE_v1)

1. **Connections:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup` — report by name. The device shell; never `git` in it. Build in the cloud workspace on code from the bundle and the kits. The device VM's clock is UTC — convert every time it prints.
2. **The session number:** 409 from `board/_numbers` by a pinned write; the clock from the clock tool (F-510).
3. **The board:** every unread message, every note since 08-Nov 18:5x IST. The packs page reminder (D713).
4. **The day's checks once a day:** `D:\Downloads\_kbtools\DAY_OPEN_LATEST.txt` — read it; run `day_open.py` only when it is not today's or a publish or a bundle came since. The cold kit is DUE from 09-Nov (7 days).
5. **The publish landed:** this close's record (papers only) — `main` = `origin/main` (read `.git/logs/HEAD` and the refs).
6. **The pins:** `/root/assetapp/asset_register.py` **dfa0955c** and `/root/assetapp/claude_reader.py` **8e1ae6bf** (the Sanjeevni chat's S750, 11:39 IST 08-Nov, on this project's files) DECLARED-PENDING — CONFIRMED when a bundle newer than 08-Nov 11:39 IST holds them. `sorting_desk.py` baa7c6aa and `stationery.py` cfb3d8b5 CONFIRMED (08-Nov 03:15 bundle).

## B · The work — in this order

1. **The summary read — F-1190's reader half (the owner's word 17:27 IST 08-Nov: staff scan a dealer's month summary on the pharmacy lane like any bill, tick or no tick; the system recognises it).** Read the specification WHOLE first: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S408\S408_SCANAPP_PROMPT_SUMMARY_READ.md` (md5 `3d35a8a26493a6d8aa37ebcbd62b0fde`). He need not paste it — it is this chat's to read. Then:
   - **`asset_register.py` is at drift 5 — read it WHOLE** (dfa0955c, from the newest bundle, or the box's live bytes if the bundle predates 11:39 IST 08-Nov — then hash the live file through his one line, never predict it, F-472). Read S750's own section of it and of `claude_reader.py` (`read_summary`, `clean_summary`, `summary_to_bill`) before anchoring a single edit; `deploy_kits\S750_MONTH_END\make_s750.py` and `walk_s750_app.py` are the Sanjeevni chat's.
   - The shape: on the pharmacy lane, a statement-shaped paper (several bill lines, a month total, no single bill number) lands as kind Summary (doc_kind 'summary'), read by `read_summary`; the dealer never Sanjeevni Medicos — null when no seller is printed; the period from the bills listed; a complete statement is never joined as "page 2" (S441 check 1); the `claude_reading` keys that `scan_register.s750_summary_scans` reads kept as they are.
   - S750's question folded in: a desk re-lane keeps kind 'Summary'.
   - The one-off on the day's eight papers (B-0291/0292/0293 clinic-lane drafts; B-0297/0298/0299 filed as bills; B-0296 L.K. set aside as Janta's page 2; B-0303 Daanshi read as the buyer under November): read each live first (a read-only sub-agent), guarded, DRY before real (F-1153), a backup of `assets.db` first.
   - A PLANNED line on `board/_numbers` naming the files before the build (D646 — both files carry the Sanjeevni chat's last TOs); a kit number from the board before the scratch folder is named (F-831). The Sanjeevni chat's S753 is its own half in `/root/finance` only — read its line on the board; nothing of its files is touched here.
2. **F-1174:** the bill reader has no credit-note kind — next, on the same reader, when item 1 is live.
3. **What he did since, read live** (only a gap found is built): October's stationery statement; the two switches.
4. **B-0176:** its lines on the board for him or Shavez; never guessed.

Then the rest of §2C of the Runbook v321.

## C · What this project is now (S401)

- Unchanged by S401 (EOS-light). S398's state stands: the sorting desk sends a listed supplier's challan to the Stationery page (S739); Yuvika's suggestion behind `desk.yuvika` (OFF); the Stationery page's product box (S741, S743); the statement's two bills (S746).
- **The switches (read live 08-Nov):** the owner's Switches row on the front page `https://followup.dr-manoj.in/scanapp/` and on The month `https://followup.dr-manoj.in/scanapp/desk/month` — Smart scanner ON · Reception buttons ON · Sorting desk for Shavez ON · Machine pages OFF · Stationery diya ON · Batteries ON · **Yuvika slips on the desk OFF**. Admin `https://followup.dr-manoj.in/scanapp/admin` carries *Recent scans by scan date* (OFF) and the reading cards (Claude ON, Sarvam OFF). **The Yuvika switch is NOT on Admin (F-1192).**
- **The intake since S750 (the Sanjeevni chat's):** a second button *DEALER KA MAHINE KA HISAAB (SUMMARY) HAI?* on the pharmacy lane; a ticked summary lands as kind 'Summary', read by Claude's `read_summary`, never by Sarvam; the clinic lane ignores the tick. A Summary row shows on All papers, the staff list and the home card like a Challan; the desk never opens it.
- **The data since S751:** sixteen mis-kinded summary scans (B-0274 .. B-0289) removed as `bill_delete` does; bills 288 → 272; backup `/root/assetapp/assets.db.bak_S751_20261108_140815`.

## D · Kits and pins

- No kit at S401.
- **S750_MONTH_END** (the Sanjeevni chat's, live 11:39 IST 08-Nov): `asset_register.py` 16a2abea → dfa0955c, `claude_reader.py` 1277e80d → 8e1ae6bf; backups `*.bak_S750_16a2abea` / `*.bak_S750_1277e80d`; its README carries the undo.
- Read-only pins: `sorting_desk.py` baa7c6aa · `stationery.py` cfb3d8b5 · `procroom.py` e51c00a1 · `clinic_papers.py` 89a3cd0a · `claude_reread.py` ed7023d2 · `batteries.py` bb082b4c · `xray_costs.py` 5823bae2 · `asset_machine.py` 7dbd5e0c · `scanner_widget.js` b936f0f3 · `/root/shared/scan_checks_s441.py` 10787cbf.
- Drift: `asset_register.py` 5 · `sorting_desk.py` 5 — each read whole before its next kit.

## E · Lessons of S401 (carried into the NEVER list of §2C)

- Where a switch sits is read from the page's code, never from a kit's README wording (F-1192).
- The device VM prints UTC; `day_open.py`'s "not from today" on the SSD mirror at an early-morning open is that clock — the mirror's own date names the night.
- Another chat's PLANNED change to this project's files arrives as a board message: read every `to: scanapp` message at the close too, not only at the open.
