# START HERE — SESSION 410 — the Scan App chat (papers & bills)

*Written at the S409 close (08-Nov-2026, 20:1x IST, full EOS) by the Scan App chat. Session **410 is RESERVED for this project** on the board (`board/_numbers`): take it there as the FIRST act (NUMBERS_PROTOCOL_v1). The project's custom instructions (COMMON_START_HERE_PROMPT_v1) govern every reply.*

## A · The open (OPEN_ROUTINE_v1)

1. **Connections:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup` — report by name. The device shell; never `git` in it. Build in the cloud workspace on code from the bundle and the kits. The device VM's clock is UTC — convert every time it prints.
2. **The session number:** 410 from `board/_numbers` by a pinned write; the clock from the clock tool (F-510).
3. **The board:** every unread message, every note since 08-Nov 20:1x IST. The packs page reminder (D713).
4. **The day's checks once a day:** `D:\Downloads\_kbtools\DAY_OPEN_LATEST.txt` — read it; run `day_open.py` only when it is not today's or a publish or a bundle came since. The cold kit is DUE from 09-Nov (7 days).
5. **The publish landed:** this close's record (papers only) — `main` = `origin/main` (read `.git/logs/HEAD` and the refs).
6. **The pins:** `/root/assetapp/asset_register.py` **74043cdb**, `/root/assetapp/claude_reader.py` **ce3868ed**, `/root/shared/scan_checks_s441.py` **59d5cb1c** (S754, 20:03 IST 08-Nov) DECLARED-PENDING — CONFIRMED when a bundle newer than 08-Nov 20:03 IST holds them. S750's dfa0955c / 8e1ae6bf were superseded before any bundle.

## B · The work — in this order

1. **S754 read live (a read-only sub-agent), the first full day of recognition:** All papers, Kind *all*, the pharmacy lane — the eight papers of 08-Nov (B-0291, 0292, 0293, 0296, 0297, 0298, 0299, 0303) Kind *Summary* under October; B-0295 one page; any new untick summary carries the audit `summary` via "recognised (S754)"; any single bill still *Pharmacy*. A gap found is built; nothing else.
2. **F-1194:** at the scan app's start `clinic_papers.heal_auto` runs before S754's `auto_home` guard (`asset_register.py` mounts `clinic_papers` around line 4717; the guard is installed at the file's end). Put the summary exclusion inside `clinic_papers.auto_home` itself (`clinic_papers.py` drift 3, read it whole first) or install the guard before the mount. Walk on a made-up root that restarts the app.
3. **F-1174:** the bill reader has no credit-note kind — on the same reader (`claude_reader.py` ce3868ed; read whole at S409).
4. **What he did since, read live** (only a gap found is built): October's stationery statement; the two switches; B-0176's lines.

Then the rest of §2C of the Runbook v322.

## C · What this project is now (S409)

- **Kit S754_SUMMARY_RECOGNISE (D871), live 20:03 IST (code) / 20:07 IST (data).** A pharmacy-lane paper scanned without a tick is read by `claude_reader.read_pharmacy` — the bill prompt plus a paragraph that decides first whether the paper is a dealer's statement (one call). A statement lands as a ticked one does (S750): kind Summary, doc_kind summary, audited `summary` via "recognised (S754)", the row lent the dealer, the period's last day and the figure. The tick still wins; the clinic lane untouched. The summary reader (ticked too): the dealer is the seller, never Sanjeevni Medicos (S439's buyer rule, copied in) — null when none is printed; the period from the bills' majority month when missing / one day / the "as on" date; a printed period kept. Keys added to `claude_reading.data`: continued, as_on, period_by, period_from_as_read, period_to_as_read, dealer_was_buyer, recognised.
- **The kind kept:** a summary on the pharmacy lane is kind Summary whichever road put it there (healed after every POST, after every reading, at start; also from a recognised reading whose row was never flipped) — except a recognised paper a person moved after the recognition (the way back from a wrong recognition). Approve refuses doc_kind summary. `clinic_papers.auto_home` never moves a summary (except at start-up — F-1194). Switch: settings `read.summary_recognise` = off (absent = on).
- **S441 check 1:** a complete statement (a Summary, or two or more numbered bill lines and a total) is never joined to the scan before it; a continued page joins a Summary head only.
- **The data (08-Nov 20:07, backup `/root/assetapp/assets.db.bak_S754_20261108_200708`):** the eight summaries all Summary, pharmacy, Filed, October; B-0296 unjoined (L.K. Drug House, no seller printed, 01–15 Oct); B-0295's own file back; B-0303 DAANSHI PHARMA.
- **The switches (read live 08-Nov, unchanged):** Smart scanner ON · Reception buttons ON · Sorting desk for Shavez ON · Machine pages OFF · Stationery diya ON · Batteries ON · Yuvika slips on the desk OFF (the front page's Switches row, not Admin) · Recent scans by scan date OFF (Admin).

## D · Kits and pins

- **S754_SUMMARY_RECOGNISE** (live): `asset_register.py` dfa0955c → 74043cdb, `claude_reader.py` 8e1ae6bf → ce3868ed, `/root/shared/scan_checks_s441.py` 10787cbf → 59d5cb1c; backups `*.bak_S754_<old md5>`; the undo line in its README.
- Read-only pins: `sorting_desk.py` baa7c6aa · `stationery.py` cfb3d8b5 · `procroom.py` e51c00a1 · `clinic_papers.py` 89a3cd0a · `claude_reread.py` ed7023d2 · `batteries.py` bb082b4c · `xray_costs.py` 5823bae2 · `asset_machine.py` 7dbd5e0c · `scanner_widget.js` b936f0f3.
- Drift: `sorting_desk.py` 5 (read whole before its next kit) · `asset_register.py` 0 · `claude_reader.py` 0.

## E · Lessons of S409 (carried into the NEVER list of §2C)

- `bill_audit.who` is the logged-in user for every server step inside a request — judge a person's decision by the action and its time (F-1193).
- A start-up heal in a mounted module runs before a later section's guard (F-1194).
- A data step's refusal must not block the code: split the gates (built into S754's installer).
- A kit on live data reads the live rows first and DRYs on the box — both of S754's refusals were caught before a byte was written.
