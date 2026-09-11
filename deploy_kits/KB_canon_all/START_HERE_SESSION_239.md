# START HERE: SESSION 239
**Written at the S238 close, 11-Sep-2026 (IST).** This is a new chat in the same project. **Read this
whole file first.** It carries the full context for Docterz, Sanjeevni, the Marg vendor, Amir and the
August lock, so you should not need ten papers. Open `S238_BUILD_BRIEF.md` only for build detail.

---

## §0 · THE STANDING OWNER RULINGS (restate these every session)

1. **Publishing is his double-click.** Name one file, with its full path:
   `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`
2. **Always give full paths, including URLs**, each in its own copy block. Never write a bare `/finance/...`.
3. **One line per command.** Multi-line pastes have been cut in transit. Use `\cp`. **Never glue two
   commands together**: at S238 the paste `S238_STEP0_V2bash` failed.
4. **Work token-lean, but never skip verification.**
5. **Plain language. One step at a time. Full-file replacements. ALL-CAPS from him means urgent.**
6. **Mask patient numbers to the last 4 digits and never print secrets or tokens.** Under F-185 the
   repository is PUBLIC, so it holds no number at all.
7. **Nothing live is rebuilt without his OK, and the manual path stays as the fallback.**
8. **Sub-agents read screens.** Screenshots never enter the main conversation.
9. **Do not hand him diagnostics to run.** Ask only for the one action nobody else can do.
10. **When a screen is wrong, read the screen's code first.** The server is the last suspect.
11. **Do not put technical choices to him.** Make the call and state it. *(Standing since S238.)*
12. **IST times only** in anything he reads. The container clock is UTC, so convert.

**Rulings that carry forward:**

- **D442:** his stated record is the authority. Where the ledger disagrees, correct the ledger.
- **F-411:** hash a file against `CANONICAL_MANIFEST.md` before reasoning from it.
- **F-414 (new):** a probe copy of a module that uses `BASE = dirname(__file__)` reads **no settings and
  no holds**. Re-point every BASE-derived path at the live folder, or the probe lies.

---

## §1 · PHASE 0: connections, then verification, then work

1. **Check the connections and report them by name.**
   - `D:\Downloads`: Marg archive, `_config`, ClaudeCowork, and **the Docterz exports**
   - `D:\dr-manoj-git`: repo, kits, publish
   - `F:\ClinicBackup`: SSD
   - the assistant's browser: still in the F-242 login loop

   All three folders were connected at S238. ⚠ **The device shell mounts nothing.** A Windows update of
   8-Sep blocks it. Work is stage → container → commit → **verify md5 after staging back**. This works
   perfectly and was the method for all of S238.
2. Open `CANONICAL_MANIFEST.md` and verify rows by md5 from inside `deploy_kits\KB_canon_all\`. Halt on a
   hash mismatch, never on a missing file.
3. Read Tier 0 only, then `OWNER_TODO_LIVE.md`.
4. **Canon at this close:** Archive **v1.85** · Register **v5.88** · Fault Register **v2.70** (F-0 … F-419) ·
   Runbook **v169** · this file · `S238_BUILD_BRIEF` · manifest.
5. **Next free: D455 · F-420 · Session 239.**

---

## §2 · WHAT TO START ON (he chose this at the S238 close)

**This new chat is for Docterz (§3).** The Sanjeevni and Marg work (§4–§5) follows. Two checks come first
because they have a clock on them:

### §2a · ⏰ FIRST CHECK: has August been locked?

He said he will lock August **later today (11-Sep)**, after the staff fill Step 0 and he updates the
system. **Do not lock it for him.** At the open, find out where it stands and help him finish if it is
not done.

- **Step 0 verify sheet** (one A4 page per print; staff mark P/L/A against the physical register):
  ```
  https://attendance.dr-manoj.in/register/salary/flow/verify?ym=2026-08
  ```
- **Month-end flow** (Step 0 → Fix-absents desk → approve Sheet 1 and Sheet 2 → Sheets 3 and 4 → Lock):
  ```
  https://attendance.dr-manoj.in/register/salary/flow?ym=2026-08
  ```
- **What should happen:**
  - Darpan's net reads **−4,443.82 until his missed punches are fixed** on the Fix-absents desk. His
    ruling is that the punch corrections will resolve it.
  - The August advances for Ranjeet (₹6,000), Shivani (₹1,100) and Sukhveer (₹14,000) come off
    **August's** salary. The reconciler has already written this to the ledger (6 rows, S238).
- **August nets before the Step 0 corrections**, for comparison only:

  | Staff | Net (₹) |
  |---|---:|
  | Alisha | 8,651.33 |
  | Amir Sohail | 2,295.08 |
  | Arjun | 2,780.33 |
  | Awdhesh | 10,115.61 |
  | Darpan | −4,443.82 |
  | Pravesh | 2,823.33 |
  | Ranjeet | 3,674.93 |
  | Sandip | 6,556.61 |
  | Shavez | 12,095.42 |
  | Shivani | 6,501.09 |
  | Sukhveer | 3,248.85 |
  | Surendra | 3,263.64 |
  | Vikki | 4,692.49 |
- **The lock requires** the month to be over, the ledger closed for the month, and zero blockers. The
  `lock` permission is Manoj-only. **This will be the first salary month ever locked (F-407).** Treat it
  as a first run: read the lock's output back.
- Live pins:
  - `salary_policy.py` v1.12 `bc7b7ffc…`
  - `staff_register.py` v0.18 `b9a72d1a…`
  - `/root/staff_ledger.py` v3.7 `49b13f42…`

### §2b · FIRST CHECK: did Amir export his Marg reports?

**Measured at the S238 close (11-Sep, 07:30 IST pull, `MargArchive\index.csv`): he did NOT.**

- **The newest purchase exports** are 06-Sep: BILLWISE and BILLITEMWISE, 01-Sep to 06-Sep. **None landed
  on 08, 09 or 10-Sep.** The 07-Sep file is the one-off April–June backfill.
- **Last sale export (SALE_BILLWISE):** business date 09-Sep, delivered. **10-Sep has not arrived**, but it
  is not late until noon today.
- **Last stock closing (STOCK_CLOSING):** 08-Sep.
- **Only two captures on 10-Sep:** two invoice PDFs, at 12:17 and 18:49.
- **Nothing was refused or unknown.** `_REFUSED\` has nothing new since 05-Sep, and `_UNKNOWN\` is empty.

**What Amir owes (D405, every day he attends; he punched on 10-Sep):** all three purchase reports, each
**from the 1st of the month to date**: `PURCHASE_BILLWISE`, `PURCHASE_BILLITEMWISE`,
`PURCHASE_SUPPLIERWISE`. Also due: the daily SALE BILL WISE (item detail) and the two-day morning
STOCK_CLOSING (D376).

**How to re-check at the open, with no shell:**

1. Stage these two files. `_last_pull.txt` should read `END … -- ok` within about 15 minutes.
   ```
   D:\Downloads\margsync\MargArchive\index.csv
   ```
   ```
   D:\Downloads\margsync\MargPull\_last_pull.txt
   ```
2. Look for `PURCHASE_*` rows with a `seen_at` of 11-Sep or later.

**If they are still missing, he said "or I will do it".** Tell him in one line which reports and which
date range. **One export covers all the missing days**, because each report runs from 01-Sep to date.

### §2c · Then check the Docterz 09:30 proof

The new schedule's first run was due at **09:30 IST on 11-Sep**. Two things to confirm on the Day
Revenue screen:

- 11-Sep's sheet (which carries 10-Sep) loaded.
- `/root/finance/logs/docterz_ingest.log` has cron entries.

Two questions are still open with him:

- **07-Sep shows ₹0 with 0 lines.** Is that true, or was the sheet empty?
- **08-Sep has no row at all.**

---

## §3 · DOCTERZ: full context

### §3.1 · What is live (VPS)

- **Reader:** `/root/finance/docterz_ingest.py`
  - Kit `S223_SPLIT_LEGS`, md5 `80bf760d…`.
  - It reads `Staff_Action_Today_*.xlsx`, sheet **Day Revenue**, from Drive folder
    `1Tls3EsrsJRqjWUY2ZtMcSlObOLP1BgQE` (the tracker's `outputs\` folder, synced to Drive from his PC).
  - It writes three `finance.db` tables: `clinic_day_revenue`, `clinic_day_line`, `clinic_day_tender`.
  - Date convention: an export for day D produces `Staff_Action_Today_` dated D+1.
- **Schedule (IST, D453).** First run 09:30, because the bank MPR never arrives before then. Every 10
  minutes until 12:00, then 13:40 and 19:40. Crontab lines:
  - `30-50/10 9`
  - `*/10 10-11`
  - `0 12`
  - `40 13,19`

  Each line runs under `flock -n` and appends to `/root/finance/logs/docterz_ingest.log`.
  - Backup: `/root/finance/logs/crontab.bak_S238_DOCTERZ_SCHEDULE_20260911_070504`
- **Root cause of the outage from 3 to 10 September (F-415):** the S223 cron redirected into
  `/root/finance/logs/`, which did not exist. The shell cannot open the redirect target, so **the command
  never ran and nothing was logged anywhere.** The directory now exists.
  - The catch-up filled the Day Revenue screen to 10-Sep: 73 days.
  - Backups: `/root/finance/finance.db.bak_S238_DOCTERZ_LIVE_20260911_065202` and `…_065430`.
- **The bank MPR** comes separately, through the hourly Apps Script push. The day page reads it live.
- **Kits:** `deploy_kits\S238_DOCTERZ_LIVE\` (rev 2, KIT_ID `ea3e3ef9…`) and
  `deploy_kits\S238_DOCTERZ_SCHEDULE\` (`77fbaf36…`).
  - **F-416:** rev 1 refused to schedule because June workbooks have no Day Revenue sheet and made the
    run exit 1. Rev 2 accepts only that reason.

### §3.2 · Ask 1: automatic pickup from `D:\Downloads` (NOT BUILT)

**His words:** *"automatic pickup of the reports — consultation report and follow-up logs — from my
Downloads folder, and process them; then the manual system either retires or becomes a fallback. The
tracker continues at my PC only."*

- **Files seen in `D:\Downloads` on 11-Sep:**
  - `consultation_report_2026-09-10.csv`
  - `consultation_report_2026-09-10 (1).csv` (a second, larger export of the same day)
  - `consultation_report_2026-09-11.csv`
  - `followup_logs.csv` and `followup_logs (1).csv` (**no date in the name**)
  - `clinical_data_report_2026-09-10.csv`
  - `Followup_Audit_*.xlsx` (probably tracker output)

  Browser duplicates arrive as "(1)".
- **The tracker lives only on his PC:** `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\`,
  with data under `...\data\`. **It is NOT a connected folder.** Ask him once for access, using the folder
  access request.
- **Build a watcher on his PC** that:
  - picks up new exports;
  - names each by business date;
  - runs the tracker's existing daily job (what the browser `/run` does today with two CSVs);
  - files the outputs into an archive folder;
  - **never deletes anything**;
  - runs as a scheduled task, the way the Marg watcher and margsync already run
    (`D:\Downloads\Marg_Watcher_medical`, `D:\Downloads\margsync`).
- **Follow the S223 capture spec** (`claude/S223_DOCTERZ_CAPTURE_AT_RECEPTION_SPEC.md`):
  - a day is **replaced, never appended**;
  - the **newest export wins**;
  - a newer file with **fewer rows is quarantined** and shouted about.
- **Keep the Drive feed alive.** The watcher must keep producing `Staff_Action_Today_*.xlsx` with the same
  name and the same sheet, or the VPS reader goes dark.
- **Fold in the split-payment gap.**
  - `push_day_tenders.py` (kit `S223_SPLIT_LEGS`, `30244990…`) must run after each consultation export.
    It ran once, on 04-Sep, and was never scheduled, so **the cash/online/card split stops at 03-Sep.**
  - **Fold in the uninstalled `revenue.py` parser fix** from S223
    (`03_WORKING_PAPERS\S223\parser_fix_offline\tenders.py`):
    - `split_payment()` reads only 2 of the 7 payment types, so Wallet, Debit Card and Patient APP are
      dropped.
    - `read_export()` must stop at the `Total` row (F-93).
    - Install gate: the live `revenue.py` must hash `a15d776e…` (`S225_FOLLOWUP_TRACKER_STUDY` §5 step 0).
- **The manual `/run` page stays as the fallback.** Reception's upload step retires only after the
  watcher has run clean for several days.

### §3.3 · Ask 2: the Clinical Data Report (NOT BUILT; measure first)

**His words:** *"analyse the clinical data report exported by Docterz, to be incorporated in the
follow-up tracker, as it feeds diagnosis, medications, investigations, advice and many other things
which can be integrated, such as the medicines with the pharmacy and the follow-up updated from
there."*

- **Measure the real export first:** `D:\Downloads\clinical_data_report_2026-09-10.csv`. **Patient data
  stays in the session workspace.** Put aggregates only in any document.
- **Prior measurement:** `S211_CLINICAL_DATA_REPORT_PARKED` (31-Aug sample, 278 rows × 55 columns).
  - Fill rates: Drugs + Dosage 186, Diagnosis 164, Instructions 180, Follow Up date 179, Tests 54,
    Procedures 30.
  - Per-visit money is fully broken out, each with Amount and Discount and an Invoice No: Consultation,
    Procedure, Drugs, Vaccination, Package, Lab, Radiology.
  - 15 columns are always empty.
  - `Amount collected` is free text, so never parse it.
  - `Mode Of Payment` is "-" on 98 rows.
  - The report is a **strict superset of the consultation report**.
- **Decide whether to augment or replace.** His S211 ruling: *"add it to the tracker for processing, and
  decide whether to add to consultation report and follow-up logs or replace it."* Answer with
  evidence:
  - Can this report alone drive the daily job?
  - Does the follow-up log's Appointment-ID spine still need the follow-up logs export?
- **Diagnosis:**
  - Feed it into `diagnosis_normalizer.py`, grounded in `Orthopedic_Diagnosis_Taxonomy_Master.xlsx`
    (27 diagnoses plus 12 gap-fillers).
  - This gives a daily **priority A–D** to order the calls. Today that layer runs by hand and goes stale.
- **Medicines to the pharmacy:**
  - Match Drugs Prescribed and Dosage against Sanjeevni `sale_line_item` (VPS `finance.db`), by patient
    and date.
  - The result is **prescribed versus bought at our pharmacy**. It gives capture rate, lost scripts, and
    "medicine finished → follow-up due".
  - It needs a drug-name to Marg-item map; the item spine (§4) is where that map lives.
- **Investigations and procedures:** link to the X-ray/lab entry (`/lab`) and to NK Pathology/Labmate,
  to compare what was ordered with what was done.
- **Follow-up date and instructions:**
  - The Follow Up date is the tracker's own subject, taken at the source. Compare it with the follow-up
    logs.
  - Instructions feed patient education and the WhatsApp templates.
- **Money:** this could replace the Day Revenue sheet reader. "Two readers of the same money" was ruled
  against, so retire `S211_DAYREVENUE` only after this reader ingests reliably. Check it against
  `docterz_ingest.py` first.
- **Deliverable:** short findings in chat, the full working paper to the project, then a build plan in
  the order he approves. **Ask 2 rides on Ask 1:** the watcher picks this report up too.

### §3.4 · Other open Docterz items

- Tighten the freshness leg for Day Revenue from **200 h to 26 h**.
- Rotate `docterz_ingest.log`.
- Check the 07-Sep and 08-Sep questions.
- **Pointers:**
  - `claude/NEXT_CHAT_DOCTERZ_AUTOPICKUP_AND_CLINICAL_REPORT.md` (the 15-item list)
  - `claude/S225_FOLLOWUP_TRACKER_STUDY.md`
  - `claude/S223_DOCTERZ_CAPTURE_AT_RECEPTION_SPEC.md`
  - `claude/S223_DOCTERZ_STAGE1_COMPLETE.md`
  - `claude/S238_DOCTERZ_LIVE_BUILT.md`
  - `claude/S238_DOCTERZ_SCHEDULE_BUILT.md`

---

## §4 · SANJEEVNI (pharmacy and Marg sync): full context

### §4.1 · The architecture: three machines, and data only flows inward

The VPS cannot reach either PC.

- **Medical PC** (pharmacy counter, Windows 10, user `SET`).
  - Marg runs here and nowhere else. Staff export by hand to `D:\MARGERP\users\<id>\report\REPORT_n.XLS`.
  - `marg_watch.py` catches each export (md5-deduplicated) into `D:\SendToClinic\_captured\`.
  - `medical_agent.py` (S205.1) supervises it:
    - heartbeat every 300 s;
    - hourly Marg database backup to Drive `MargBackups`;
    - starts at logon.
- **manojz** (his PC), `D:\Downloads\margsync\MargPull\`.
  - `PULL_FROM_MEDICAL.bat` runs every 10 minutes over Tailscale SMB, read-only.
  - `marg_router.py` identifies each report **by content** (`signatures.json`, 17 signatures) into
    `MargArchive\<TYPE>\<YYYY-MM>\`, with `index.csv`, mirrored to Drive `Clinic Data Archive`.
  - `marg_gate.py` POSTs sale reports to:
    ```
    https://followup.dr-manoj.in/finance/api/marg-push
    ```
  - `snapshot_on_capture`, `expected_on_capture` and `push_purchases` feed stock and purchases.
  - `pull_watchdog.py` runs every 15 minutes; there is a nightly push at 22:30.
- **VPS**, `/root/finance/`: `finance_app.py`, `finance_ingest.py`, `marg_report.py`, `marg_backfill.py`,
  `stock_app.py`, `sale_bill.py`, and `finance.db` (about 128 tables).
  - **The push is parsed and the file is deleted inside the same request, so the VPS keeps no export
    files.**
- **Pages:**
  ```
  https://followup.dr-manoj.in/finance/approvals
  ```
  ```
  https://followup.dr-manoj.in/finance/darpan
  ```
  ```
  https://followup.dr-manoj.in/finance/purchase/page/salts
  ```
  ```
  https://followup.dr-manoj.in/finance/stock/page/desk
  ```
  ```
  https://followup.dr-manoj.in/finance/returns/desk
  ```
- **Key tables:**
  - `sale_line_item`: about 17.8k lines, 3.5k bills.
  - The item spine:
    - `marg_item` 374
    - `marg_item_name` 423
    - `marg_item_fact` 1,127
    - `marg_task` 41 open
    - `marg_name_unresolved` 10
    - `marg_spine_run`: **one run only, 07-Sep**
  - `marg_figure`: 422 figures.
  - `sale_bill`: new at S237.
  - `marg_item_discount`: **absent, because T1 is not installed**.
- **Pins:**
  - `marg_spine.py` `9a08b2c4…` is installed. A newer `b5956f59…` (the VINTAZ merge) is installed
    nowhere, so do not confuse the two.
  - T1: `marg_discount.py` `a49c733f…`.
  - ⚠ **F-395:** the live `marg_report.py` (`f9370dde…`) and `finance_ingest.py` (`747b4a50…`) match no
    repo copy. **Never edit either from the repo.**

### §4.2 · What is DONE

| Session | Done |
|---|---|
| S212 | System of record measured |
| S213 | Stock count and diffs screens live |
| S229 | **Item spine installed** (7 tables). D401–D404 ruled |
| S235 | **Derivation pass installed**: 227 of 373 priced, shelf value at MRP ₹5,12,147. Orthotic discount register settled: 93 products |
| S236 | **T1 (`marg_item_discount`) built and published, NOT installed.** F-385: the bill-level discount is dropped by our ingest |
| S237 | **Rung 1 installed** (`sale_bill`: gross, discount, tax, dr/cr, net, cash, credit-note). The walk found **₹27,375.33 of discount across 524 bills in 21 days**. Rung plan written |

### §4.3 · The full plan (`SANJEEVNI_RUNG_PLAN_v1_S237`)

The five safety rules of `SANJEEVNI_CONSOLIDATION_WORK_PLAN_v1_S235` stand:

- build beside, never over;
- nothing visible changes in Phase A;
- every URL keeps working;
- old and new run side by side before any switch;
- every step is reversible in one move.

| Rung | Work | Status |
|---|---|---|
| 1 | Bill header retained, **backfilled from the whole archive** | table live; **backfill NOT run** |
| 2 | Attribution: split each bill's discount across its lines with T1 | **NEXT**; needs T1 installed |
| 3 | Gross becomes net, side by side for a full cycle | later; needs his "say the word" |
| 4 | Spine cadence plus a drift report | later |
| 5 | Coverage as data | partly in `marg_figure` |
| 6 | The five lanes (sale, purchase, ordering, stock check, returns/expiry) read the spine | later |
| 7 | Side by side, then switch one screen at a time | later |

- **Rung 1 is done when** every archived bill has a header and gross − discount + dr/cr = net within
  `round_p` (up to ₹1), or the exception is named.
- **Rung 2 is done when** the six S236 single-appliance bills reproduce to the paisa. The fixture is
  **A003495**: ₹3,170 gross, ₹870 discount, ₹2,300 net.
- **Phases after the rungs:**
  - **B · Doors:** day-one fixes (orphaned and dead tiles, six money-tile names), then B1 stock check,
    B2 purchase, B3 sale and returns, B4 ordering.
  - **C · Roles:** six role maps and the PWA on staff phones. The PWA waits. Dr Bhawna's `unit_role`
    seed is missing.
  - **D · New screens:** start a count, adjustment vouchers (D388/D397), return at the counter,
    near-expiry (D409), a new-report tile (D407), a staff advance form (D371).
  - **E · Junk:** quarantine first; deleting is his call.
- **Orthotic track, T1–T9:**
  - T1 ruling table: built.
  - T2 `stock_count.section`.
  - T3 blind count.
  - T4 A4 print.
  - T5 match.
  - T6 loss statement.
  - T7 vouchers batched to Marg's 6-line print limit (F-382).
  - T8 consumption register.
  - T9 cadence: orthotics monthly, the whole shop quarterly.
- **Detectors** (designed, not built): suspect bills are kept out of rate-setting; a single-line price
  is refused; an MRP that disagrees with sales becomes a `marg_task` question.

### §4.4 · Scheduled next, in order

1. **Finish Rung 1's backfill.**
   - **Blocker:** the archive exists only on manojz (`D:\Downloads\margsync\MargArchive\SALE_BILLWISE\`)
     and in Drive, never on the VPS.
   - **Decision for the session (make it, do not ask him):** ship the archived sale exports to the VPS
     through the existing `marg-push` door, or run the backfill against a copy of `finance.db` and ship
     the rows.
   - The first real run also shows whether the 27-Aug `.xlsx` parses.
2. **Install T1**, one line from `deploy_kits\S236_DISCOUNT\`, then **build Rung 2**. Build offline
   against the nightly backup, do a live-shape walk, then one install line.
3. **If the vendor's per-line columns ever reach the Excel export** (§5), teach the importer. This
   simplifies Rung 2; it does not block it.
4. Then Rung 4 (spine cadence) and the four orthotic screens.

**His open items on this track:**

- Rung 3 sign-off.
- The provisional gross-up reads low (1.45× observed against 1.25×/1.43× assumed).
- One tap: VINTAZ P 4500 INJ write-off.
  ```
  https://followup.dr-manoj.in/finance/stock/page/desk?count=1
  ```
- Finalise the August and September Marg Purchases.

---

## §5 · THE MARG VENDOR: pending (bill-wise sale report, item name and discount)

**Vendor:** Ram Singh (Marg dealer), licence LIC-14116710, reached over AnyDesk.

- **The problem, measured 10-Sep (S237_MARG_NEW_EXPORT_MEASURED):**
  - **The BILL WISE SALES STATEMENT Excel export has not changed.** It has 9 columns:
    `BILL NO. | DESCRIPTION | D.R. | GROSS AMT. | DISCOUNT | TAX | DR/CR | NET AMT. | CASH`.
    **The discount is one figure per bill; there is no per-line rate, discount or net** (F-385). That is
    why Rung 2 has to *attribute* the discount.
  - **The item name is cut at 20 characters in the sale export** (e.g. `KNEE SUPPORT HINGED XXL` becomes
    `KNEE SUPPORT HINGED`, losing the size). It is cut at **29 in the stock export**, so the
    `L S BELT CONT GRAY UNISON XXL` and `…XXX` lines cannot be told apart (F-380).
  - **What the vendor changed on 09-Sep (11:44–18:11 IST) was only the PRINTED GST invoice:**
    - a wider name;
    - a new `DIS` column, which prints a **percentage** rather than rupees;
    - an unheaded third money column, which is the gross.
  - **The vendor's test bill used live number A003493, which collides with a real sale.**
  - S236's claims that the "F-385 cause was removed" and the "renames are no longer urgent" were
    **wrong**. S237 corrected them.
- **The ask** (drafted 10-Sep as a numbered Hinglish message, **not recorded as sent**):
  1. Per-line RATE, DISCOUNT and AMOUNT in the **Excel** export. This is the priority.
  2. Wider names in the sale export (20 characters) and the stock export (29).
  3. DIS in rupees, and a heading on the last column.
  4. No test bills on live numbers.

  **Also unanswered since 28-Aug:** batch-wise closing stock, the item ledger by voucher type, and why
  the expired and near-expiry exports come out identical. The 15-Aug requirement document
  (`Marg_Report_Requirement_Sanjeevni`: two saved reports, separate filenames, a date on every bill
  row, auto email, monthly history) has no recorded resolution either.
- **At the open:** ask him in one line whether the message went to Ram Singh and what came back.
- **How to tell if the fix has landed:** read the header row of any sale export stamped after 09-Sep
  18:11. It should have more than 9 columns, or item lines carrying rate, discount and amount, and names
  longer than 20 characters. The newest such export is `…20260909-221733`, and it is **unchanged**. A
  changed shape will probably land in `MargArchive\_REFUSED\`, because the signature will no longer
  match. Watch that folder.
- **Amir's 22 renames** (naming rule D439, the sixth section of his page) are **urgent again**, because
  the Excel still clips. `OWNER_TODO_LIVE` said "no longer urgent" until this close and is now
  corrected. His 12 orthotic rows stay parked until Ram Singh answers.

---

## §6 · EVERYTHING ELSE OPEN (full list in `OWNER_TODO_LIVE.md`)

- **The staff-money work still to build** (he said to proceed):
  - the statement page rewrite (he wants to see the screen first);
  - the loan-restatement row;
  - actual-paid on the salary lock;
  - the register's advance deduction must read only the ledger's own rows for the month (D349,
    `S238_SALARY_PAGES_FINDING`).
- **His terms and documents:**
  - Darpan's loan workbook: ₹175,000 in the ledger against ₹174,000 on his record, the ₹1,000 split,
    and April's wrong SKIP;
  - tranche B's terms (₹180,000 with no schedule);
  - Surendra's advances in later months, flagged.
- **F-413** (a ruling): real numbers in the inherited Archive. Mask in place, or freeze v1.84 and mask a
  v2.0.
- **UptimeRobot** is watching `drmanojagarwal.in`, **not the `.com`** that expired, and has been silent
  since 04-Sep. The `S237_CERT_WATCH` rev 2 install and its first mail are still to be confirmed.
- **The arms licence renews on 27-Sep-2026.** It is inside its nag window and no mail has been seen.
- **The unattended nightly Q5 finding F-384 recurred.** It was fixed at this close; see the close report.
- The MyOperator token overlap (Ms Khushi Jain) · the ICICI ·9012 expiry · four Bitwarden values ·
  the call-recordings backup · Parvesh's exit date · the delete lists.

---

## §7 · THE FIVE STORES, AND THE ONE RULE

- **project knowledge** = canon.
- **GitHub** = code plus `deploy_kits/KB_canon_all/`. It is PUBLIC, so no numbers.
- **`D:\Downloads\ClaudeCowork\`** = everything canon excludes.
- **`F:\ClinicBackup\`** = mirrors and cold kits.
- **Drive** = not set up.

**No document may be live and editable in two stores.** The manifest decides what is current.

---
*START_HERE_SESSION_239 · written at the S238 close, 11-Sep-2026.*
