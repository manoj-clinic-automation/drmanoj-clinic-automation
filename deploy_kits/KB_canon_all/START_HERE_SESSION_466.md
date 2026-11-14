# START HERE — SESSION 466 — the Scan App chat (papers & bills)

*Written at the S464 close (14-Nov-2026, 20:4x IST, full EOS) by the Scan App chat. Session **466 is RESERVED for this project** on the board (`board/_numbers`): take it there as the FIRST act (NUMBERS_PROTOCOL_v1) with a SHORT line (under 400 characters). The project's custom instructions govern every reply.*

> **FIRST — if this close was HELD AT THE BUILD** (the board's S464 line says HELD): its parts are complete in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S464\close_parts\` (close.json built on the parent's S462 canon: Register v5.293, Archive v1.290, Fault v2.277 §7.210, Runbook v373). Run `TZ=Asia/Kolkata TMPDIR=/tmp python3 -B ~/mnt/Downloads/_kbtools/close_build.py ~/mnt/Downloads/ClaudeCowork/03_WORKING_PAPERS/S464/close_parts/close.json` from `/tmp` (a POSIX path — the Windows spelling is not found in the shell), read the table, then `--place`. If another close was placed since, re-base: every version in the parts (v5.294 / v1.291 / v2.278 §7.211 / v374) and close.json's runbook `supersedes_old` / `_new` and todo markers move with it. Then the board line READY and the owner's publish.

## A · The open (OPEN_ROUTINE_v1)

1. **Connections:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup`. The device shell; never `git` in it. `/sessions` is full (F-1326): scratch in `/tmp`, `TMPDIR=/tmp`, npm with `npm_config_cache=/tmp/...`, flask for a walk from `pip install --target /tmp/...`. The shell refuses at times ("bridge sockets") — the file tools still work; retry the shell once.
2. **The number:** 466 by a pinned write; the clock from the clock tool. Read the counters from the newest close's END line; read `_numbers` whole only to write it (F-1405). A kit number: read `kit_next`, not the last line.
3. **The board:** unread messages to `scanapp`; the packs reminder (D713).
4. **The day's checks:** `D:\Downloads\_kbtools\DAY_OPEN_LATEST.txt` — run `day_open.py` only when it is not today's or a publish / bundle came since.
5. **The pins:** this project's DECLARED-PENDING 8 — `sorting_desk.py` 2eeb8b39 · `claude_reader.py` e2338b8b · `clinic_papers.py` 91305fe0 · `xray_costs.py` 0a296116 · `procroom.py` 38c5bbaa · `reader_watch.py` 5ba95fce · `scan_checks_s441.py` 5c934bdb · `asset_register.py` 63eba920 — CONFIRMED by a bundle newer than 14-Nov 20:40 IST.

## B · The work — in this order

1. **F-1419 — a credit note scanned on the pharmacy lane.** The pharmacy reader (`claude_reader.read_pharmacy`, PHARMACY_PROMPT) has no credit-note kind, so such a paper lands as kind 'Pharmacy' and may be paired with its bill by Sanjeevni's register. Tell the Sanjeevni chat first (board message); then a kit: the pharmacy reading's credit note → kind 'Pharmacy credit note' at intake (read asset_register's pharmacy intake path live; drift 1) and the desk's credit-note box for it. Walk on the real app; cold review.
2. **What he asks.** He may switch `desk.cn` / `bar.goto` on for Shavez himself (The month's switch card).
3. **`clinic_papers.py` drift 5:** read WHOLE before any kit touches it.

## C · What this project is now (S464)

- **S835 live (20:10):** credit notes on the sorting desk — the reader's line ("a CREDIT NOTE … its no., against invoice …") with Make it a Credit note / No — leave it; the sixth kind; the box: no., date, amount back; "Against which bill?" — this dealer's clinic-lane and pharmacy (kind 'Pharmacy') bills of 90 days, each opening its scan and, for a pharmacy bill, Marg's purchase lines (`purchase_scan_link` → `purchase_bill` → `purchase_line`, item_check's one-copy rule) and the spine's purchase return; or on the dealer's account (a clinic group or Sanjeevni only). After Save: pharmacy → kind 'Pharmacy credit note' (never paired as a bill); clinic → its bill's group, The month: bought − credit notes = spent (by the credit note's own month); never live, never approved, never stock lines. Table `credit_note`: one live link per credit note. The bill's view: Bill · Credit note · Still owed. Switch `desk.cn` (absent = OFF for Shavez).
- **S838 live (20:40):** Go to ▾ on the scan app's bar — Sorting desk, The month, Bills awaited, and every page in five groups; built from the bar's own list; the desk takes the bar over at a worker's first request (asset_register untouched). Switch `bar.goto` (absent = OFF for Shavez).

## D · Lessons of S464 (into §2C's NEVER list)

- An install line on the board takes its md5s from the kit's PIN_TO files, never from a build's console (F-1416).
- A paper kind that is never spend must stay off every lane whose readers count money — check each reader of the scan app, here and in `/root/finance` (F-1417, F-1418).
- Before handing a paper to Sanjeevni, read how its registers select papers (`kind='Pharmacy'`): a paper they must not pair gets its own kind (A-D52).
