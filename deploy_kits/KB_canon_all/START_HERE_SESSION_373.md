# START HERE — SESSION 373 — written at the S372 close (the parent), 31-Oct-2026

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open in a fresh chat in this project, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (read it from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). The project's custom instructions are `COMMON_START_HERE_PROMPT_v1`.
2. **The first work: the open with its six checks (§0 A); then D812, the procedures list, at his word (§0 B); then IPD kit 4 once he has answered the mock-up (§0 C).** If he names something else, take it.
   - The Runbook is v285 (§2A). The Register §S372 holds D810 (Darpan's month jobs), D811 (the film log), D812 (the procedures list); §S371 D809; §S370 D806–D808.
   - The newest live modules: `/root/finance/xray_film.py` c08a1016 and `/root/finance/month_jobs.py` 33fa557f, mounted by `finance_app.py` 2f604fee. Kits: `deploy_kits/S686_INGEST_SELFTEST_F1051/`, `S687_DARPAN_MONTH_JOBS/`, `S688_XRAY_FILM_LOG/` (copies in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S372\`).

*FIRST ACT: take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **373 is RESERVED for the parent.** 369 (Sanjeevni) was open at this close; 363 (Scan App) and 365 (NK Pathology) reserved.
- At this close (board v828): **D813 · F-1065 · A-D25 · kit S689 · session 374 next.** **Kit S682 is already taken** for IPD kit 4 and PLANNED on `surgery_cases.py` 89a668a9 (30-Oct 15:05); the line goes stale on 6-Nov — after that, write a fresh PLANNED line on the newest bundle's bytes.

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* The standing rules of `START_HERE_SESSION_357.md`'s connection list stand whole: never `git` in the device shell; every commit to the PC read back by hash; a published kit folder never changes.

***Every time you write is read first: the clock tool, a commit stamp, a file's time or a program's own line (F-510).***

**Learned this session (S372):**
- **Run `day_open.py` in the device VM with its path overrides, always.** Its Windows defaults fail there: `python3 $HOME/mnt/Downloads/_kbtools/day_open.py --read --tools $HOME/mnt/Downloads/_kbtools --repo $HOME/mnt/dr-manoj-git/drmanoj-clinic-automation --kb $HOME/mnt/Downloads/ClaudeCowork --ssd $HOME/mnt/ClinicBackup/DrManojClinic_Automation --roots $HOME/mnt/Downloads $HOME/mnt/dr-manoj-git $HOME/mnt/ClinicBackup`. Its page prints UTC; convert to IST.
- **A background sub-agent's result survives a container restart in its transcript.** Twice this session a restart lost the result in flight; it was recovered by reading the sub-agent's transcript and extracting its last assistant text. Do that before re-running any agent.
- **Cold reviews kept finding real blockers.** S688 took five rounds: R2, R3 and R4 each found a real fault (F-1061, F-1062, F-1063) in a counter fed by people. Review again after every design change; stop only at SAFE.
- **The owner's screen-level corrections can simplify a design.** His "the screen shows FILMS LEFT" (20:23) replaced a morning count, a reset rule and a weekly tick with one typed number. Ask what the machine or paper actually shows before designing a count.
- **A test's clean-up goes in a `finally`; a made-up ID is checked unused on live data (F-1059).** 4471 and 5120 were real clinic IDs.
- **Delete every database copy you made in the VM before the session ends (F-1064).** Other sessions' copies cannot be deleted from a new sandbox user.

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN (`OPEN_ROUTINE_v1`).**
1. **The board:** every note, every message with `read:false`. **Remind him of the packs page (D713).**
2. **The day's checks:** run `day_open.py` with the overrides above (if the page is not today's); `UNREAD_LISTS_LATEST.txt`.
3. **The 01-Nov bundle against `live_pins_S372close.txt`** — seven pins must now match: `finance_ingest.py` 029f5c20 · `finance_app.py` 2f604fee · `aaj_duties.json` c5c80c37 · `aaj_seed.py` dc7050d5 · `month_jobs.py` 33fa557f · `xray_film.py` c08a1016 · `casepack_page.html` f95d186d. Then the parent's DECLARED-PENDING 9 becomes 2. Any other change is a halt; re-read the file whole (F-472). `purchase_app.py` 2e1e9023 vs the pin list's da04d546 is the Sanjeevni chat's record lag, not drift.
4. **The finance restore drill:** its first scheduled run was Sunday 1-Nov 02:10 (S661); the stale leg should be clear. If not, it is the first work.
5. **F-1064:** confirm `/tmp/s680root`, `/tmp/s370`, `/tmp/s369`, `/tmp/s683` are gone from the device VM; then close it.
6. **The film log's first day,** read as manoj by a read-only sub-agent: `https://followup.dr-manoj.in/finance/slips/film/log` — the first counts on 1-Nov (reception, or Shavez after 11:00); and **the 16 film bills read vs 12 listed** — find the four and say why.
7. **On Monday 2-Nov:** the newest `claude/AUDIT_RUN_*` (slice 5) and its *For the builder* lines; the close answers each.
8. **The rest (first open of the day only):** project knowledge measured once, never-cited %, what no store holds, the cold kit when DUE.

**B · D812 — THE PROCEDURES LIST (Runbook v285 §2A item 2), at his word.**
- **Read first, whole:** `xray_film.py` c08a1016 from the newest bundle — its X-ray list, the slips it reads, the Excel download (padwriter) — and `topics/procedure-conventions` (casts and slabs, ILI, dressings).
- **What it is:** from 1-Oct-2026, month by month, grouped by day with counts by kind (casts and slabs, ILI, dressings, other); each row date, slip, clinic ID, patient, procedure, side, cash/UPI; a date range box; an Excel download. Seen by him, Shavez and reception; **amounts on his page only.**
- **A mock-up first** (made-up patients), then a kit number from the board; every S688 gate: walk with mutants, control on the live file, a cold review until SAFE, rehearsal (DRY · install · ALREADY · red restores), the publish and one server line, a live read as manoj.
- **No phone number, name or clinic ID in the repository (F-185); no patient file in the cloud workspace (D656).**

**C · IPD KIT 4: THE IMPLANT BILLS DESK, THE CHEQUE, THE VENDORS' LEDGER (D807; §2A item 3; kit S682).**
- **His three answers first** (asked 30-Oct 15:10, on the mock-up's last board `https://claude.ai/artifact/D4BQUWfNKqoXHt5uZBJmcw`): the five steps' words · does Shavez write the cheque from the desk (number, date, amount) · old cases settled only by him on the vendor's page.
- **Read first, whole:** `surgery_cases.py` 89a668a9 from the newest bundle: the vendors' pages, the vendor ledger, the hospital payments, `IMPL_PAY` and `_follow_implants` (S681), the old-case exclusion, and `surg_bill`'s credit line (`COALESCE(payable, bill)`, owner-only).
- **What it is for (D804, D807):** Shavez enters or scans each vendor's bill against its case's implant; the hospital's cheque is recorded; the vendor is paid and confirms. A vendor's page shows its ledger. The old cases' implants are settled there, one by one. **Who sees what:** Shavez everything except the implant's actual cost; the actual cost and the amounts paid to vendors are Dr Manoj's.
- **Every S681 gate:** carry walk_s681's 254 checks and add a section; the control; the probe as manoj, shavez, bhawna, darpan; mutants; a cold review (two rounds at least); the real screens before placing; the rehearsal (red after placing restores 89a668a9).

**D · THEN, in order (Runbook v285 §2A):** S688's three wording notes in the next kit on `xray_film.py` · the Hostinger kernel update when its fix is out · kit 5 when the hospital has explained the credit heads (D808) · kit 6 · watch Darpan's month jobs and the film log's first month · his three board items of 27-Oct · F-1031 · D786's first month from 1-Nov · the rest.

**Owner-side, on his board:** the publish · the home medicines list and each vehicle paper's dates (`https://followup.dr-manoj.in/finance/monthjobs/owner`) · the opening spare boxes and the 16 unsized studies (`https://followup.dr-manoj.in/finance/slips/film/log`, Settings) · IPD kit 4's three answers · the packs page (shops and passwords) · Y106 · the glucometer line · his IPD share % · the hospital's word on the credit heads (Y181) · from 1-Nov *Approve & save* · the Marg engineer's restore test · the SBI downloads · Raghav's Zerodha papers · Ranjeet's login · the reception PC's Windows · the Docterz report export · the arms licence in November · D812 when he says.

**Standing owner rulings:** rules 1–51 of `START_HERE_SESSION_360.md`, 52–53 of `START_HERE_SESSION_368.md`, 54–56 of `START_HERE_SESSION_370.md`, 57–59 of `START_HERE_SESSION_371.md` and 60 of `START_HERE_SESSION_372.md` stand whole. Added:

61. **Darpan's monthly jobs (D810):** home medicines from the owner's own list in settings (needed per month), counted in the last 7 days of the month by him or Darpan, to order = needed − left; the vehicle check at month end is Darpan's (five vehicles; stepney and jack-paana on Wagon R and Vento); paper reminders pollution 7 days, insurance 1 month, RC 45 days; the expiry clear-out at month end. Stock check, Marg reports and the procedure room are NOT month jobs.
62. **The X-ray film log (D811):** reception types the FILMS LEFT the machine shows, per size, each morning (Shavez from 11:00); boxes of 150; no spare box — order at 10 days' supply, both sizes, from Jugnu Medicos (Nigam, Fuji), by Shavez or him; the gap vs paid slips shown to all, no reason asked; no weekly film-stock tick; contacts his to edit, staff to see, numbers in the database only.
63. **The procedures list (D812):** like the X-ray list, from 1-Oct, month by month, grouped by day with counts by kind; amounts on his page only; seen by him, Shavez and reception.

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_205_S372close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_202_S372close.md` (§S372) |
| Fault → Action Register | `Fault_Action_Register_v2_189.md` (§7.123) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-31_Session372close_v285.md` (**§2A the order**) |
| open / close / prompt | `OPEN_ROUTINE_v1.md` · `CLOSE_ROUTINE_v1.md` · `COMMON_START_HERE_PROMPT_v1.md` |
| live pins | `live_pins_S372close.txt` |
| build brief | `S372_BUILD_BRIEF.md` |
| numbers | System Board `board/_numbers`. At this close: **D813 · F-1065 · A-D25 · kit S689 · session 374 next; 373 RESERVED for the parent** |

*Written at the S372 close, 31-Oct-2026.*

---

## THE OTHER CHATS — a pointer, not a carried section

- **Sanjeevni (369 open):** record the S683 `purchase_app.py` pin (2e1e9023) at its close; its spine gate is still theirs (`parent_S371_1`). S687's `month_jobs.py` reads their `stock_expiry_*` read-only.
- **The Scan App (363 reserved):** S688's `xray_film.py` reads `/root/assetapp/assets.db` read-only (`bills.subgroup`, `status`, `dup_of`, `bill_items`, `xray_film_line`); a schema change there must tell the parent. **NK Pathology (365 reserved):** unchanged.
- **For all:** `/root/finance/finance_app.py` moved twice this session (2f604fee), `aaj_duties.json` (c5c80c37) and `aaj_seed.py` (dc7050d5) likewise. A chat touching them builds on these bytes.
