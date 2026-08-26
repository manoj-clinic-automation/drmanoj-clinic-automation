> ## WORKING PAPER — S203, not a reference
> Written to work something out on 26-Aug-2026. Its conclusions live in
> `MARG_MEDICAL_CURRENT.md`; its evidence and reasoning live in
> `MARG_MEDICAL_HISTORY.md`, both in `deploy_kits/MARG_MEDICAL/`.
> **Do not cite this as current.** Retained, not deleted (F-23).

# S203 — KB CENSUS, PHASES 1 AND 2

**Session 203 · 26 Aug 2026 · READ-ONLY. Nothing was deleted, moved or modified anywhere.
No git operation was run. Phase 3 (retirement) was not attempted — `S203_KB_CONSOLIDATION_PLAN.md`
§5 requires the owner's approval and it has not been given.**

**Method, stated first.** The four canon stores were pulled as FILES and hash-verified against
`CANONICAL_MANIFEST.md`'s CURRENT rows before anything was compared against them (D188 — a filename
is not provenance):

| store | md5 (transcribed from `md5sum`) | bytes | verdict |
|---|---|---|---|
| `KB_History_Archive_v1_49_S202.md` | `06c6670a8a1155959e4f0961ad58e7c5` | 897,225 | matches the manifest's CURRENT Archive pin |
| `KB_Register_v5_54_S202.md` | `8fede84d7126e13fca17418e449f9d0a` | 380,810 | matches the CURRENT Register pin |
| `Fault_Action_Register_v2_41.md` | `4883e3bdf08cba92da7597448e00f2da` | 344,065 | matches the CURRENT Fault-Register pin |
| `CANONICAL_MANIFEST.md` (repo) | `3ff86788c5da3e1d10a16d72be060bf4` | 261,311 | self-row; no pin to check against |

**A verification that had never been done before, and it passed.** The project-knowledge copies of
the Archive, the Register and the Fault Register were returned by the connector **as files**, so
they could legitimately be hashed. All three are **byte-identical to the repository copies and to
their manifest pins**. Project knowledge and git agree exactly on the three largest canonical
documents.

**And the limit on that.** A project document below roughly 261 KB is returned as **inline text**,
not as a file. This project's own rule (`S181_postclose_addendum` §3, adopted after a 206 KB retype
produced a false red) is that *a hash verdict is only ever pronounced on bytes delivered as a FILE;
re-keyed inline text may corroborate, never convict and never acquit.* **So no md5 is claimed below
for any project document under that size.** For those, content identity was tested by extracting
distinctive tokens — transcribed md5s, rupee figures, counts, file paths, backup names, D/F/AF
numbers — and searching the whole repository (1,821 files) and the four canon stores for them. That
test can prove *absence* conclusively, which is what §1 and §2 turn on.

---

## §1 · CENSUS

### 1.1 Counts

| | |
|---|---|
| Rows in the project's document list | **167** |
| Distinct paths | **163** — four paths appear **twice** (see 1.2) |
| Distinct basenames | **163** |
| Files in the repository (excluding `.git`) | **1,821** |
| Entries in `deploy_kits/KB_canon_all/` | **216** |
| Project docs with a file of the same basename **somewhere** in the repo | **87** |
| Project docs with **no file of that basename anywhere** in the repo | **76** |
| Project docs **not named anywhere in `CANONICAL_MANIFEST.md`** | **90** |
| …of which also absent from the repo | **70** |

**Classification against the plan's §2 table.** Using the plan's own vocabulary:

- **CURRENT** — the Tier-0/Tier-1 live rows (Archive, Register, Fault Register, Runbook v136,
  START_HERE_203, the manifest, the pinned specs/dossiers/contracts). All verified present in both
  stores; the three biggest verified byte-identical.
- **SUPERSEDED** — retained older versions with manifest rows (`END_OF_SESSION_PROMPT_v4/v6`,
  `HANDOFF_RUNBOOK_…v113/v115/v134`, `START_HERE_SESSION_201`, `KB_Asset_Register_v1_11_0_R_S181`,
  `Salary_System_KB_v1_S157`, `Clinic_Estate_Master_Inventory_v1`, `Attendance_System_Dossier_v1_2`,
  the incident reports…). All present in the repo.
- **SESSION RECORD** — the `S###_*.md` family, ~93 documents.
- **ORPHAN** — **90 documents in project knowledge are named nowhere in the manifest.** This is the
  plan's own "most interesting category", and it is the majority of the project's document set.

**One honest qualification on the orphan count.** The manifest carries a *collective* row —
``S193_Close_Summary_and_Pins` · `S193_*` · `S194_*` · `S195_*` · `S196_*` (session docs)`` — which
covers the S193–S196 family by wildcard rather than by individual pinned md5. Those documents are
therefore *acknowledged* but **not individually hash-pinned**, and Phase 0 cannot verify any of them.
Every other document in the list below is not referenced at all.

### 1.2 Four paths are duplicated in project knowledge

`CANONICAL_MANIFEST.md` · `WABA_Approved_Templates_v1_S137.md` ·
`Maintenance_SOP_System_Spec_v1_1.md` · `Clinic_Contact_QR_Setup_Record.docx`

Each appears twice with different `created_at` timestamps (e.g. the manifest at 2026-08-26 and at
2026-08-15). Only one of each is reachable by path, so **the older copy of each cannot be read,
hashed, or verified — and it still occupies the knowledge budget.** These four are the cheapest
possible reclamation and carry no judgement call at all.

### 1.3 THE LIST — project documents that exist in NO other store

**76 documents.** No file of that basename exists anywhere in the 1,821-file repository, and for
every one that was opened (66 of the 76), a distinctive verbatim string from it was searched across
the whole repository and the four canon stores and **found nowhere**. The cold kit
(`DrManoj_Clinic_FULL_Handoff_Session202_2026-08-26.zip`, taken at the S202 close) was opened and
enumerated: it contains `deploy_kits/` + `margpull/` + the manifest only — **it is a mirror of the
repository canon and contains none of these documents either.** So for these 76, project knowledge
is the ONLY store, and the plan's own governing rule — *nothing is retired until it is provably
recoverable from TWO independent places* — is not merely unmet; there is **one** place.

**S202 (2)**
`S202_PENDENCY_AUDIT.md` · `S202_Marg_Transport_Resilience_D350_CONTRACT.md`

**S201 (11)**
`S201_PARKED_BACKLOG.md` · `S201_Marg_Pipeline_Rebuild_Plan.md` ·
`S201_Medical_Pipeline_Completion_Audit.md` · `S201_Marg_Outbox_Never_Drained_Finding.md` ·
`S201_Part0_Rescan_Record.md` · `S201_Part1_Capture_And_Agent_Record.md` ·
`S201_Part1_xlsx_Dependency_Removed.md` · `S201_Parts2_3_4_Record.md` ·
`S201_A1FIX_Live_Pin_Record.md` · `S201_Month_vs_Marg_Explained.md` · `S201_WHATS_LEFT_FOR_YOU.md`

**S200 (9)**
`S200_Session_Notes.md` · `S200_StaffApp_Design_Candidate.md` · `S200_Register_Live_Pin_Record.md` ·
`S200_PortalPWA_Live_Pin_Record.md` · `S200_D340_Sunday_Absence_Ruling.md` ·
`S200_D341_Absence_Weight_and_Punch_Blindsight.md` · `S200_D342_Hold_Fines_Sunday_Deterrent.md` ·
`S200_D343_D344_Divisor_Darpan_GoLive.md` · `S200_D345_Absence_Fine_Ramp.md`

**S198 (4)**
`S198_G1_Live_Pin_Record.md` · `S198_H1_Live_Pin_Record.md` · `S198_P2_P3_Live_Pin_Record.md` ·
`S198_P4_P5_H2_Live_Pin_Record.md`

**S193–S195 (5)**
`S193_Close_Summary_and_Pins.md` · `S194_Triple_Feature_Live_Pins.md` ·
`S194_Addendum_S4_S5_Pins.md` · `S195_Close_Summary_FINAL.md` · `S195_FINAL_PINS.md`

**S184 (7)**
`S184_Sheet_vs_YesBank_Verification.md` · `S184_Cash_Correction_Build_State.md` ·
`S184_Float_Investigation.md` · `S184_Parking_Windows_29days.md` ·
`S184_DailyFlow_Holiday_Reserve_Design.md` · `S184_Reserve_Counter_Person_Design.md` ·
`S184_Reconciliation_Workbench_Design.md`

**S181 (9)**
`S181_UPI_Gap_Root_Cause.md` · `S181_Clinic_Lab_Source_Forensic_Analysis.md` ·
`S181_Docterz_Export_Verdict_and_Migration.md` · `S181_Docterz_Financial_Capture_Open_Issues.md` ·
`S181_Clinic_Reconciliation_and_StaffAction_Findings.md` · `S181_Clinic_Module_Build_Contract_C1.md` ·
`S181_Clinic_Module_Target_Design.md` · `S181_C1_Contract_Addendum.md` · `S181_postclose_addendum.md`

**S180 (7)**
`S180_Marg_Folder_Recon.md` · `S180_Marg_Feed_Feasibility.md` · `S180_Marg_Sample_Findings.md` ·
`S180_Marg_Feed_Transport_Design.md` · `S180_Marg_Feed_Request_and_Flow.md` ·
`S180_Marg_Daily_Sale_Button_Settings.md` · `S180_Marg_Action_Register.md`

**S179 (10)**
`S179_Finance_Revenue_Migration_Analysis_v1.md` · `S179_Sanjeevni_Medical_Module_Build_Contract_v1.md` ·
`S179_Clinic_Finance_System_Build_Contract_v2.md` · `S179_B1_Medical_Reconciliation_Report.md` ·
`S179_B1b_B2_Delivery_Note.md` · `S179_B2.1_Delivery_Note.md` · `S179_B2.2_Delivery_Note.md` ·
`S179_B3a_Delivery_Note.md` · `S179_Finance_Install_Kit.md` · `S179_Marg_Sale_Report_Analysis.md`

**Non-session-record (12)**
`AUDIT_RUN_2026-08-24_slice1.md` (the Auditor's ONLY run report) · `OWNER_TODO_LIVE.md`
(un-manifested **by design**, D-ruled — not a fault) · `S203_KB_CONSOLIDATION_PLAN.md` (this
exercise's own plan) · `Marg_Report_Requirement_Sanjeevni.md` · `F82_Fault_Register_append_S172.md` ·
`Fault_Register_append_F85_F88_S180.md` · `INCIDENT_2026-07-12_VERDICT_APPEND_OVERWRITE_F39.md` ·
`templates_snapshot.json` · `templates_snapshot_p2.json` · `Clinic_Contact_QR_Setup_Record.docx` ·
`S195_medical_kit/SETUP_CHECK.bat` · `S195_medical_kit/marg_export_macro_v2.ahk`

**Six of the 76 are named in the manifest but absent from every store**, which is the F-107
condition standing open right now: `OWNER_TODO_LIVE` (by design) · `S179_Marg_Sale_Report_Analysis` ·
`S180_Marg_Folder_Recon` · `S184_Float_Investigation` · `S193_Close_Summary_and_Pins` ·
`S203_KB_CONSOLIDATION_PLAN`. **The manifest names four of these as canonical companions and the
repository does not have them.**

---

## §2 · THE REDUNDANCY TEST

The claim under test is *"its content is in the Archive."* It was tested per document, by extracting
distinctive tokens and searching the Archive (A), the Register (R), the Fault Register (F) and the
manifest (M). A token found in none of the four is written **ABSENT** below and is quoted verbatim.

**Result: 63 session records from the §1.3 list were opened and tested. All 63 hold at least one
item that exists in no canonical store. Not one was found redundant.** The assumption the plan set
out to test does not survive contact with the documents.

### 2.1 Verdict table

| # | Document | Verdict | The unique item, quoted, and its search result |
|---|---|---|---|
| 1 | `S202_PENDENCY_AUDIT.md` | **PROMOTE** | The N1–N13 cross-store reconciliation, which exists in no other document. **N2:** *"The AF-# series has no bridge to the F-# register. `AF-1`, `AF-2`, `AF-3`, `AF-4`, `AF-6` appear **zero times** in the Fault Register … and **AF-5 is unaccounted for in any document I can reach**."* Confirmed independently here: `AF-3`, `AF-4`, `AF-5`, `AF-6` return **0 hits in all four stores**. Also **"29 findings carrying NO status marker at all"** — ABSENT — and **N13** *"The later Daily Flow v2 stages have no status anywhere"* — ABSENT. |
| 2 | `S202_Marg_Transport_Resilience_D350_CONTRACT.md` | **PROMOTE** | This is a **signed design contract for a minted decision (D350)** and it has no manifest row and no repo copy. Every comparable contract — D329, D330, D331, D332, D335, D336, D337 — is a pinned Tier-1 row. Unique text incl. *"a system with two paths and no switch has one path"* and §4 *"Neither PC could be rebuilt today from anything written down."* `S202_Marg_Transport_Resilience` and `MagicDNS`: ABSENT everywhere. |
| 3 | `S201_Marg_Pipeline_Rebuild_Plan.md` | **PROMOTE** | The A–M fault table with source line numbers, and the **hashes of the stranded files**: `633a54d3`, `fbea55de`, `1beac275`, `df20b4d2` — **all four ABSENT from all four stores.** Also the seven-failure-mode monitoring-coverage table and the Lab-PC rule *"Attaching a source must be a data edit, never a new script"* (ABSENT). |
| 4 | `S201_PARKED_BACKLOG.md` | **PROMOTE** | Findings **C1–C8**, six of which the S202 audit confirms were never minted. **C6** verbatim: *"A re-apply wipes that day's review queue (`DELETE FROM sale_item_review WHERE ingest_batch_id=?`). Any resolution must be recorded somewhere that survives a re-import… **Matters directly to the Docterz plan**."* `sale_item_review` appears in A and R; **this rule about it does not.** |
| 5 | `S201_Medical_Pipeline_Completion_Audit.md` | **PROMOTE** | *"**343 attempts between 15:28 and 18:20 — 4.1 MB of identical backups**"* — ABSENT. Manojz pin `PULL_HIDDEN.vbs 9a3ba9ba3bb7376bd166f12624d282c3` — ABSENT. The PDF proof `7617f1b4` — ABSENT. *"`index.csv`: **41 rows, 15 columns, 0 malformed**"* — ABSENT. |
| 6 | `S201_Parts2_3_4_Record.md` | **PROMOTE** | *"**`PURCHASE_BILLWISE` totals 476,393 and `PURCHASE_SUPPLIERWISE` totals 476,393 for the same July period.** Two independently generated reports agreeing to the rupee is a genuine cross-report integrity check."* Both `476393` and `476,393`: **ABSENT everywhere.** This is a live financial control that exists in one document. Also *"16 would pass, 0 would be refused"* and gate selftest `39 → 49`: ABSENT. |
| 7 | `S201_Part0_Rescan_Record.md` | **PROMOTE** | *"Index: VERIFIED 16 → 26 · UNKNOWN 5 → 1 · REFUSED 13 → 7"* — ABSENT. Backup `index.csv.before_rescan_20260825-142311` — ABSENT. The rescued reports' business dates (`2024-01-20`, `2024-10-05` ×2, `2025-06-03`) — ABSENT. The deliberate non-signature ruling on `SANJEEVNI ORTHOTIC STOCK 22 JAN 2024` — ABSENT. |
| 8 | `S201_Part1_Capture_And_Agent_Record.md` | **PROMOTE** | The 10:37 watcher-death timeline — ABSENT. The **old medical watcher pin `25126388…`** — ABSENT. Manojz pins `d63045b1`, `78ef009d`, `ca8b2af9`, `481d567b`, `d4af22f6` — **all ABSENT.** *"**`NEEDS_UPLOAD` and `FROM_CLINIC` do not exist** on the medical PC"* — ABSENT. |
| 9 | `S201_Part1_xlsx_Dependency_Removed.md` | **PROMOTE** | *"**170 cells compared, 0 mismatches**"* against openpyxl on `SALE BOOK FORMAT.xlsx` (`9bf5c008`) — both ABSENT. `PULL_FROM_MEDICAL.bat` pin `ddd9b88e` — ABSENT. This is the only proof that the stdlib `.xlsx` reader is correct. |
| 10 | `S201_A1FIX_Live_Pin_Record.md` | **PROMOTE** | The **offline-harness recovery recipe** — which deploy kit holds each live module byte-for-byte — and the differential *"570/679 → 573/682, +3 exactly, fail set byte-identical (109 rows)"*. `570/679`, `573/682`, kit id `d602ea6e`, `_marg_total_for_date`: **all ABSENT.** `S201_PARKED_BACKLOG` §B cites this recipe as the precondition for every future kit's measured projection. |
| 11 | `S201_Marg_Outbox_Never_Drained_Finding.md` | **PROMOTE** | *"SANJEEVNI MEDICOS · 24-08-2026 · 22 bills · gross 13,881.15 · discount 916.35 · NET ₹12,964.00 · cash ₹10,462.00 · non-cash ₹2,502.00"* — every figure **ABSENT**. Capture hashes `25c1ff95` / `3b456d9c` — ABSENT. *"`send_log.txt` last entry **22-08-2026 09:39**"* — ABSENT. The verbatim `marg_router.py` lines 314–318 — ABSENT. |
| 12 | `S201_Month_vs_Marg_Explained.md` | **PARTIAL → PROMOTE** | Totals `51,868` / `23,879` / `20,599` **are** in the Archive. But the day-by-day review-queue table, bill **`A003039` (₹190)** — the single bill that disproved the "no clinic ID → dropped" theory — and `days_differing`, `49,181`: **ABSENT.** The reasoning is unique; only the headline survived. |
| 13 | `S201_WHATS_LEFT_FOR_YOU.md` | **PROMOTE (weak)** | Overlaps `OWNER_TODO_LIVE` by design. Unique: the allowlist evidence — *"18 of its own database files (`.dbf .cdx .idx .fpt .xff .C18`)"* — and `MEDICAL_CENSUS.bat` (ABSENT). |
| 14 | `S200_Session_Notes.md` | **PROMOTE** | The live-session record of Surendra/Ranjeet/Sukhveer's four-tranche advance entry with the recovery matrix (Aug/Sep/Oct/Nov), and the vhost-drift discovery. `24738a34` (the `register_proxy.block` md5) and `e59f9be5` (the repo vhost mirror): **ABSENT.** |
| 15 | `S200_StaffApp_Design_Candidate.md` | **PROMOTE** | The entire Staff Console / task-board / policy-template design. `tasks.jsonl`, `Probation`, `policy template`, `MediaRecorder`: **all ABSENT.** `S202_PENDENCY_AUDIT` lists **SC0 Staff Console Phase 0** as a live builder item blocked on four owner rulings — **the rulings are enumerated only here.** |
| 16 | `S200_Register_Live_Pin_Record.md` | **PROMOTE** | The D338/D339 build record incl. *"a capability the owner cannot complete in one pass is only half built"* and the nine D339 selftest assertions. |
| 17 | `S200_PortalPWA_Live_Pin_Record.md` | **PROMOTE** | The AutoSSL diagnosis and *"AutoSSL reports 4 domains failing renewal validation incl. `drmanojagarwal.com`"* — present in the Archive; but `24738a34`, `e59f9be5` and the phase-2/phase-3 proxy recipe: ABSENT. |
| 18–22 | `S200_D340…D345` (5 docs) | **PROMOTE** | The Archive's §S200 "SUNDAY RECKONING" is a three-bullet summary. ABSENT from every store: the D340 derivation *"Shivani: 5 weekdays plus Sundays 5, 12, 19 and 26 … `5 + (4 × 0.5) = 7`"*; *"the '14 staff-days to correct' list … was built on a **contaminated comparison**"*; `Base/60`; `noout_days`; **`29 Nov 2026`** (the first 5th-Sunday); D342's totals *"collected ₹1,011.47 · held (suspended) ₹3,034.37"* and *"staff keep **₹5,834.53** more this month"*; `fines_exempt`; D343's Surendra HOLD reasoning; D345's ramp table and **`3,774.84`** (Shivani's recovery figure — which `OWNER_TODO_LIVE` now carries as **₹3,724.55**, a second, different figure, neither of them in the canon). |
| 23–26 | `S198_G1 / H1 / P2_P3 / P4_P5_H2 Live_Pin_Record` | **PROMOTE** | The pin *chains* are in the Register. ABSENT: the PWA icon hashes `5a4fef38` / `83c6ec70`; `PAYMENT_REGISTER_URL` and both Google Sheet ids; every backup path (`_backup_S198_H1_20260823_154117`, `_backup_S198_G1_20260823_164018`); the offline differentials `557/667 → 563/673`, `563/673 → 569/679`; builder selftest `21 → 27`. |
| 27 | `S195_FINAL_PINS.md` | **PROMOTE** | `SEND_TO_CLINIC.bat` pin **`e19a8a777ac22fe75a242f1eb9762185`** — ABSENT everywhere, and this is the medical-side fallback sender that **AF-1 is still armed on**. Also `AutoHotkey_2.0.26` and the AHK-version check command — ABSENT. |
| 28 | `S195_Close_Summary_FINAL.md` | **PROMOTE (weak)** | Most pins are in the canon. Unique: the GAS inventory as a single table, and the canon-debt warning that produced the S197 fold. |
| 29 | `S193_Close_Summary_and_Pins.md` | **PROMOTE** | Named in the manifest, absent from the repo. Unique: F-155…F-159 in full; *"Cash: drawer ₹65,697 … unbanked ₹2,40,895"* (`2,40,895` present in A, `65,697` present in A) but **`3141`** (the discount-bearing bill count as written) and the full kit list: ABSENT. |
| 30 | `S194_Triple_Feature_Live_Pins.md` | **PROMOTE** | *"19-Aug: day ₹44,120 = full 30-bill Marg; only 23 bills (₹41,554) linked; the 7 missing (₹2,566) = the gap"* — the figures are in the Archive, but `extract_home_medicine.py` / `apply_home_medicine_backfill.py` and the **re-load instruction for 17/18/19 Aug** are ABSENT, and that backfill is still owed. |
| 31 | `S194_Addendum_S4_S5_Pins.md` | **PROMOTE (weak)** | `96cd7b75` and `43d2b845` are in the canon. Unique: the email-agent systemd/config layout and the IMAP narrowing rationale. |
| 32 | `S184_Sheet_vs_YesBank_Verification.md` | **PROMOTE** | The §6 derivation of the −₹30,056 to the exact cell: *"Old Balance as typed **26,604** (exact) … **The ₹75,000 is deducted twice. That double-count is the entire −₹30,056.** … Counted once, the row closes at **+₹44,548**."* `26,604`, `44,548`, `13,514`, `85,258`, `1,14,351`, `99,054`, `29,093`, `13,900`, `38,554`, `18,194`: **all ABSENT.** Also §1's table of the three phantom deposits (15 Jun ₹50,000 · 18 Jul ₹42,000 · 25 Jul ₹45,000) — ABSENT. |
| 33 | `S184_Parking_Windows_29days.md` | **PROMOTE** | A 29-row data table of the parked-cash days with per-day amounts, grouped by bank trip. `20,450`, `24,393`, `70,924`, `63,388`, `58,679`, `16,542`, `4,136`: **all ABSENT.** This is the worksheet the owner was to check against Dr Bhawna's copy; it exists once. |
| 34 | `S184_Cash_Correction_Build_State.md` | **PROMOTE** | Backup tables `s184_removed_movements` / `s184_removed_adjustments` — ABSENT. The survey figures *"31 `cash_movement` out/bank rows = ₹16,59,114"* — `16,59,114` present in A once; the backup-table names, which are the only route to reversing the migration, are not. |
| 35 | `S184_Float_Investigation.md` | **PROMOTE** | Named in the manifest, absent from the repo. The float identity and its three-branch decision rule; `Sanjeevni_Float_Investigation` ABSENT. |
| 36 | `S184_DailyFlow_Holiday_Reserve_Design.md` | **PROMOTE** | `biometric_present_ids`, `60b42351`, `FINANCE_ATTENDANCE_DB` fail-soft rule: `biometric_present_ids` and `60b42351` **ABSENT**. |
| 37 | `S184_Reserve_Counter_Person_Design.md` | **PROMOTE** | The four-way reserve-day cash routing and the multi-day reserve stretch model. `manned_by` **ABSENT**; `counter_person` appears in R but the design does not. |
| 38 | `S184_Reconciliation_Workbench_Design.md` | **PROMOTE** | The workbench + correction-log design; `upi_statement` **ABSENT** from all four stores. |
| 39 | `S181_UPI_Gap_Root_Cause.md` | **PROMOTE** | F-91's entire evidential basis. *"On 9 days the ledger's `Net` matches the clinic to the rupee — nothing missing — yet ₹5,300 of UPI is absent and ₹3,800 has appeared in `Cash`."* `5,67,000`, `1,08,500` (the back-tested cumulative), the bill-size and single-line/multi-line tables: **ABSENT.** The Fault Register carries F-91's one-line summary and none of the proof. |
| 40 | `S181_Clinic_Lab_Source_Forensic_Analysis.md` | **PROMOTE** | *"**The revenue arithmetic is INVERTED between units** … the single most dangerous copy-paste in the build"* — this warning is quoted forward by `S201_PARKED_BACKLOG`, `S202_PENDENCY_AUDIT` and `OWNER_TODO_LIVE` as the reason not to replicate for the Lab PC. **Its evidence lives only here**: `18,10,809`, `1,49,163`, `10,68,584`, `0026`, `176 distinct` spellings — **all ABSENT.** |
| 41 | `S181_Docterz_Export_Verdict_and_Migration.md` | **PROMOTE** | The seven-tender Docterz footer block, and the exact ₹500/₹600 leg losses: `25,600`, `20,800`, `Patient APP`, `Net Banking`, `clinical_data_report`, `Laboratory Amount`: **all ABSENT.** |
| 42 | `S181_Docterz_Financial_Capture_Open_Issues.md` | **PROMOTE** | E1–E10 importer traps and the B1/B2/B3 receivables gap. |
| 43 | `S181_Clinic_Reconciliation_and_StaffAction_Findings.md` | **PROMOTE** | F-92's and F-93's evidence: the month-by-month discount table (`33,115` **ABSENT**) and *"On 2026-08-15 the concession section is 100% junk."* |
| 44 | `S181_Clinic_Module_Build_Contract_C1.md` | **PROMOTE** | The C1/C3 contract: the `revenue_ledger.csv` column map, the tender-attribution-by-month table (`0.3%` — ABSENT), and §1 *"Tender is stamped on the `Consultation` line only"* — the last obstacle to C5, stated here and nowhere else. `567,150`: ABSENT. |
| 45 | `S181_C1_Contract_Addendum.md` | **PROMOTE** | The six owner decisions of late S181 — the four-token clinic tender vocabulary, the `Laboratory Amount` → X-ray fixed mapping, the Razorpay and ICICI-POS feed decisions. `docterz_report.py 783fffde…` is in A and R; these rulings are not. |
| 46 | `S181_Clinic_Module_Target_Design.md` | **UNCERTAIN — not opened** | No repository copy, no manifest row. Classified by census only; no redundancy verdict is claimed for it. |
| 47 | `S181_postclose_addendum.md` | **PROMOTE — high** | **This is where the Phase 0 mechanism was designed.** *"a hash verdict is only ever pronounced on bytes delivered as a FILE … Re-keyed inline text may corroborate, **never convict and never acquit**"* — the phrase `never convict` is in A and M, but the addendum's full §3 (why `KB_canon_all` exists, what it must contain, the EOS duty to refresh it) is not; `4c8704e` and `KB_canon_all.zip`: ABSENT. **F-184 — the S202 fault where `KB_canon_all` went four sessions stale — is a failure of exactly the duty this document defines, and the document is in one store.** |
| 48 | `S180_Marg_Folder_Recon.md` | **PROMOTE — high** | Named in the manifest, absent from the repo. The **complete Marg file-format analysis**: the 16-byte prefix `19 a3 95 78 …`, the period-256 obfuscation proof, `CP437`, `marguser.csv` as the unencrypted control, `pfdapi584`, the `.c18` table inventory, `daybook.xml`. **Every one of those tokens is ABSENT from all four stores.** If this document is lost, the Marg data-layer analysis is lost with it. |
| 49 | `S180_Marg_Feed_Feasibility.md` | **PROMOTE** | The seven-route verdict table, the `up_sale`/`up_saleinfo` dormant-slot discovery (`up_sale` **ABSENT**), the `serverbackup` weekday-rotation proof (**ABSENT**). Also carries a **provenance block correcting its own session number** — the origin of F-85. |
| 50 | `S180_Marg_Sample_Findings.md` | **PROMOTE — the most consequential of all; see §2.2** | Records `C:\Users\Public\MARG\17476\` on **15 Aug 2026**. Also `e81f97fe`, `da087842`, `277,083`, `193,412`, `CN00167`, `MARG ERP 9+`, `A002660`: **all ABSENT.** |
| 51 | `S180_Marg_Feed_Transport_Design.md` | **PROMOTE** | §4A, the sale-return correlation design measured on 9 real credit notes, and the §4 invariants (Darpan as checker, "flag few things, trend everything", two attribution thresholds). `82% joinable`: ABSENT. *(Note: `S201_PARKED_BACKLOG` §F and `S202_PENDENCY_AUDIT` N7 both say **"Retire `S180_Marg_Feed_Transport_Design`"** because its route ranking is obsolete — but §4A and §4 are not obsolete and are not carried anywhere else. Retire the ranking, not the document.)* |
| 52 | `S180_Marg_Feed_Request_and_Flow.md` | **PROMOTE** | The measured facts table: *"non-cash was **36.9%** of net over 5 days"*, *"It agrees with CASH on **133 of 138** bills — but the 5 it misses are split-tender"* (both present in A), and the vendor request block (`39548`, E.BUSID) — **ABSENT.** |
| 53 | `S180_Marg_Daily_Sale_Button_Settings.md` | **PROMOTE** | The **exact Marg report-screen settings** — the operational recipe for regenerating the feed. `MARG ERP 9+`, the delimiter screen values: ABSENT. |
| 54 | `S180_Marg_Action_Register.md` | **PROMOTE** | V1–V9 · Q1–Q8 · O1–O10 · U1–U18, with **V7's silent-truncation warning** and the U11 measured ceiling *"1 corroborated, 2 unique, 2 near, 0 ambiguous, 31 none — 3 of 36 safe"*. `V7`, `up_saleinfo`, `3,634`: ABSENT/near-absent. |
| 55 | `S179_Marg_Sale_Report_Analysis.md` | **PROMOTE** | Named in the manifest, absent from the repo. *"Thirteen days, thirteen exact matches"* and the derivation `277,083 − 193,412 = 83,671 = 88,777 − 5,106` that established the money rule. `277,083` / `193,412`: **ABSENT.** |
| 56 | `S179_B1_Medical_Reconciliation_Report.md` | **PROMOTE** | The 36 carry-forward breaks itemised with dates and amounts. `26,81,566`, `1,04,403`, `9,76,713`, `2,57,894`, `medical_adjustments.csv`: **all ABSENT.** |
| 57–60 | `S179_B1b_B2` · `B2.1` · `B2.2` · `B3a` Delivery Notes | **PROMOTE (weak–medium)** | Superseded as build state, but each carries the **design reasoning** for a live invariant: the cutover endpoint and why it deliberately leaves the 36 breaks open; the per-unit role matrix; *"Revenue counts in full. Cash does not."* and `v_noncash_by_head`; the adapter-as-setting model. Their build-time md5s (`becf4122`, `16a261cb`, `4d957a6b`, `82264947`, `480aa8ad`, `557b4344`) are **ABSENT** — expected for superseded builds, and the only reason they are not a promotion argument. |
| 61 | `S179_Clinic_Finance_System_Build_Contract_v2.md` | **PROMOTE** | The three-entity hard rule with the ICICI MIDs, the accountant-pack specification, and §5's governance question. |
| 62 | `S179_Sanjeevni_Medical_Module_Build_Contract_v1.md` | **PROMOTE (weak)** | Superseded whole by v2 (which says so). Retains §7 — the ICICI merchant-statement identification with sender, subject pattern and both MIDs. |
| 63 | `S179_Finance_Revenue_Migration_Analysis_v1.md` | **PROMOTE** | FIN-1…FIN-14, the estate-wide revenue totals (`₹54,79,676`, *"roughly a ₹1.3 crore/year flow"*) and the §3.2 Interpretation A/B analysis that D313 was built on. |
| 64 | `S179_Finance_Install_Kit.md` | **PROMOTE (weak)** | The four post-install steps, incl. *"A role row keyed to a username that doesn't exist **grants nothing, silently**"* — still true of every unit. |
| 65 | `AUDIT_RUN_2026-08-24_slice1.md` | **PROMOTE — high** | The Auditor's **only** run report, holding AF-1…AF-6 in full plus the four read-only commands. `AF-3`, `AF-4`, `AF-5`, `AF-6`, `last_response.txt`, `sent_hashes.txt`: **ABSENT from all four stores.** `OWNER_TODO_LIVE` ⭐0 item 7 and `S202_PENDENCY_AUDIT` O9 both instruct the owner to run **"AF-3's duplicate-advance scan"** *before the August close* — **and the command exists only in this document.** |
| 66 | `Marg_Report_Requirement_Sanjeevni.md` | **PROMOTE** | The vendor-facing requirements document with the acceptance list and licence `LIC-14116710` (**ABSENT**). The manifest's §S182 block says only *"A vendor-facing requirement document was written."* |
| 67 | `Fault_Register_append_F85_F88_S180.md` | **REDUNDANT** | Its content (F-85…F-88 full text) **was applied** — *"assigned by anticipation"* is present in `Fault_Action_Register_v2_41` (2 hits). This is a genuine append artefact whose merge is proven. |
| 68 | `F82_Fault_Register_append_S172.md` | **REDUNDANT (likely)** | F-82 is in the Fault Register's index and carried as OPEN-VENDOR. The diagnostic ladder was not separately verified as merged verbatim — **UNCERTAIN on that one paragraph.** |
| 69 | `INCIDENT_2026-07-12_VERDICT_APPEND_OVERWRITE_F39.md` | **UNCERTAIN** | An incident report with no manifest row and no repo copy, while its two siblings (F-41, F-44) have both. The narrative is in Archive §S141; the minute-by-minute timeline was not exhaustively diffed. **Its asymmetry with F-41/F-44 is itself the finding.** |
| 70 | `templates_snapshot.json` / `_p2.json` | **UNCERTAIN** | WABA template snapshots; no repo copy, no manifest row, not opened (JSON data, not a session record). |
| 71 | `S195_medical_kit/SETUP_CHECK.bat`, `marg_export_macro_v2.ahk` | **UNCERTAIN** | Kit source files; `GUARD_AND_SEND.bat`, `guard_and_send.py`, `marg_report.py` and `SETUP_S195_MARG.md` from the same folder **do** have repo copies. These two do not. The `.ahk` macro is recorded as PARKED and is on the S201 cleanup list. |
| 72 | `Clinic_Contact_QR_Setup_Record.docx` | **UNCERTAIN** | Binary, duplicated in the project list, no repo copy, no manifest row. Not opened. |

### 2.2 The finding that changes what this exercise is for

**`S180_Marg_Sample_Findings.md` — project knowledge only, no repo copy, no manifest row — closes
with this line, written 15 Aug 2026:**

> *"Also noted: `C:\Users\Public\MARG\17476\` is a Marg user folder (`17476`) not seen in the S180
> folder survey, which found only `50018`, `61376` and `a` under `D:\MARGERP\users\`."*

**Ten days later, the S201 close recorded the same path as a new discovery**, and the manifest's
§S201 block still reads:

> *"**Marg has TWO output trees, and only one was ever known.** … `C:\Users\Public\MARG\<id>\all\REPORT.PDF` <- found 25-Aug, S201 … **Every document in this KB — including the two references rewritten earlier the same day — described only the first.**"*

That last sentence is false of project knowledge. The path and the user id were written down at
S180. `61376` and `50018` — the other two Marg user ids recorded in the same document — appear
**nowhere** in the Archive, the Register, the Fault Register or the manifest to this day.

The blind spot the S201 audit describes — *"the census, the recent-files sweep and the ignored-file
counter … all three would have answered 'nothing' with complete confidence"* — was a blind spot in
the **canon**, not in the project's knowledge. The fact was recorded; it was recorded in the one
store nothing indexes, hashes or reads. **That is what an unregistered canonical document costs,
measured in a real outage.**

### 2.3 A second concrete cost, still live

`OWNER_TODO_LIVE.md` ⭐0 item 7 requires **AF-3's duplicate-advance scan** before the August close —
the first fully enforced payroll run. The scan command exists in exactly one place,
`AUDIT_RUN_2026-08-24_slice1.md`, which has no repo copy and no manifest row. `AF-3` returns **zero
hits** in all four canonical stores. If that document were lost today, the instruction would survive
and the means of carrying it out would not.

---

## §3 · SIZE — WHERE THE FOOTPRINT IS SPENT

### 3.1 A correction to the premise of the whole exercise

The plan is founded on *"project knowledge hit **1,958,788 of 2,000,000 tokens — 98%**"*, and the
API today reports `knowledge_size: 1,404,142` of `max_knowledge_size: 2,000,000`.

**That figure cannot be a character count of the documents in project knowledge.** Three documents
were pulled from project knowledge as files and measured directly:

```
KB_History_Archive_v1_49_S202.md    897,225 bytes   md5 06c6670a8a1155959e4f0961ad58e7c5
KB_Register_v5_54_S202.md           380,810 bytes   md5 8fede84d7126e13fca17418e449f9d0a
Fault_Action_Register_v2_41.md      344,065 bytes   md5 4883e3bdf08cba92da7597448e00f2da
                                  -----------
                                  1,622,100 bytes   — three documents
```

**1,622,100 > 1,404,142.** Three documents alone exceed the reported total, before the 261,311-byte
manifest and the other 159 documents are counted. Summing the repository twins of the 87
name-matched documents gives **2,943,897 bytes**, and the remaining 76 are not counted at all.

**So the headroom number the consolidation is being driven by does not mean what it appears to
mean.** It is either measured in some other unit, deduplicated, or stale. This matters directly:
Phase 4 of the plan proposes *"report project-knowledge headroom in the close report, and warn below
15% remaining"* — **that watchdog would be built on a metric nobody has validated.** Validating it
is a cheaper and safer first move than any deletion.

### 3.2 The measured distribution

Sizes are exact for the four documents pulled as files, and are the repository twin's byte count for
the rest (a proxy — but a proxy proven exact on all three cases where both could be measured).

| # | Document | bytes | cumulative | share |
|---|---|---|---|---|
| 1 | `KB_History_Archive_v1_49_S202.md` | 897,225 | 897,225 | 30.5% |
| 2 | `KB_Register_v5_54_S202.md` | 380,810 | 1,278,035 | 43.4% |
| 3 | `Fault_Action_Register_v2_41.md` | 344,065 | 1,622,100 | **55.1%** |
| 4 | `CANONICAL_MANIFEST.md` | 261,311 | 1,883,411 | 64.0% |
| 5 | `Dr_Manoj_Clinic_Umbrella_Architecture_v1_58.md` | 99,372 | 1,982,783 | 67.3% |
| 6 | `Call_Console_Evolution_Spec_v2_4.md` | 70,524 | 2,053,307 | 69.7% |
| 7 | `Diagnostics_Surveillance_System_Spec_v2_3.md` | 57,080 | 2,110,387 | 71.7% |
| 8 | `Clinic_Callback_Tracker_AppsScript_Audit_v1_9.md` | 44,447 | 2,154,834 | 73.2% |
| 9 | `INCIDENT_2026-07-08_CALLHOOK_403_v5_CONSOLIDATED.md` | 42,301 | 2,197,135 | 74.6% |
| 10 | `S195_medical_kit/marg_report.py` | 34,987 | 2,232,122 | 75.8% |
| 11 | `MyOperator_Call_API_Master_Reference_23_june_.md` | 31,979 | 2,264,101 | 76.9% |
| 12 | `Salary_Attendance_Master_Dossier_v1_S164.md` | 30,537 | 2,294,638 | 77.9% |
| 13 | `KB_Asset_Register_v1_11_0_R_S181.md` | 29,303 | 2,323,941 | 78.9% |
| 14 | `Frontend_Dashboard_Documentation_v4_S140.md` | 25,655 | 2,349,596 | 79.8% |
| 15 | `Clinic_Estate_Master_Inventory_v1_1.md` | 23,361 | 2,372,957 | 80.6% |
| 16 | `Clinic_Estate_Master_Inventory_v1.md` (superseded) | 22,283 | 2,395,240 | 81.4% |
| 17 | `D297_Console_Portal_Build_Dossier_v1_S168.md` | 18,986 | 2,414,226 | 82.0% |
| 18 | `D297_Call_Console_Contract_v4_FINAL.md` | 18,384 | 2,432,610 | 82.6% |
| 19 | `AI_Verdict_Layer_Master_v1_S145.md` | 17,831 | 2,450,441 | 83.2% |
| 20 | `S183_Sanjeevni_Daily_Cash_Design_and_Marg_Findings.md` | 17,811 | 2,468,252 | 83.8% |

**Three documents account for the top 50%** — the Archive, the Register and the Fault Register.
**Four account for 64%.** All four are Tier-0/Tier-1 CURRENT, all four are load-bearing, and **none
of them is a candidate for anything.** The Archive alone is more than the entire session-record
population.

**The consequence for the plan.** The ~76 project-only session records the plan proposed to test for
retirement are, by the measured distribution, in the **long tail** — the largest of them
(`S181_Clinic_Lab_Source_Forensic_Analysis`, `S200_StaffApp_Design_Candidate`,
`S201_Marg_Pipeline_Rebuild_Plan`, `S202_PENDENCY_AUDIT`) are of the order of 15–25 KB each, and the
whole family is a small fraction of the footprint. **Deleting all of them would not move the number
that triggered this exercise, and every one of them tested so far holds something unique.**

The reclamation that *is* free of judgement:
1. The **four duplicated paths** (1.2) — an unreadable second copy of the manifest alone is ~261 KB.
2. The **superseded versions** that already have manifest rows AND verified repository copies — the
   plan's own "minimum viable version" in §8. That is the safe move, and it is where the bytes are.

---

## §4 · WHAT I COULD NOT VERIFY, AND WHY

1. **No md5 is claimed for any project document under ~261 KB.** The connector returns them as
   inline text, and this project forbids convicting or acquitting on re-keyed text
   (`S181_postclose_addendum` §3). For those, "exists in no other store" is proved by absence of
   distinctive verbatim strings across all 1,821 repository files and all four canon stores — which
   is conclusive for absence but does not, by itself, prove byte-identity where a same-named repo
   file does exist. **87 documents therefore carry "a same-named repository file exists" rather than
   "a byte-identical copy exists."** The three where a file *was* obtainable all matched exactly,
   which is encouraging and is not proof about the other 84.

2. **Six of the 76 project-only documents were not opened** and carry no redundancy verdict:
   `S181_Clinic_Module_Target_Design.md` · `templates_snapshot.json` · `templates_snapshot_p2.json` ·
   `Clinic_Contact_QR_Setup_Record.docx` · `S195_medical_kit/SETUP_CHECK.bat` ·
   `S195_medical_kit/marg_export_macro_v2.ahk`. They are classified by census only; their §2 verdict
   is **UNCERTAIN**, not REDUNDANT. The other **70 were opened in full.**

3. **The `knowledge_size` discrepancy is unresolved** (§3.1). I can prove the reported figure is not
   a character sum; I cannot say what it is. **Nothing in this report should be used to argue about
   headroom until that metric is understood.**

4. **The 21 session records that DO have repository copies** were tested mechanically rather than by
   reading: every md5-shaped token and every rupee figure was extracted from the repo copy and
   searched across the four stores. Results, for completeness — `S186_F113_Backfill_Silent_Shortfall`,
   `S186_Sanjeevni_Cash_FINAL_Close`, `S187_Daily_Flow_v2_Target_Design` and `_Addendum`,
   `S189_Advance_Pool_Design_D329`, `S190_Expense_Menu_Redesign_D330`, `S190_Staff_Advance_Policy_D331`,
   `S195_Medical_Watcher_LIVE_Reference`, `S198_Purchase_Portal_Design_CONTRACT`, `S199_Live_Pin_Record`,
   `S199_MonthEnd_Flow_D337_CONTRACT`, `S199_Salary_Policy_D336_CONTRACT`, `S201_UI_Health_Redesign_Record`
   returned **zero absent tokens**. Six did not: `S196_Close_Summary_FINAL` (**five live pins —
   `33f94b40`, `51e9ed7e`, `ba7127b1`, `c50986e8`, `fc99c7d1` — absent from all four stores**),
   `S186_Cash_Movement_Sheet_Analysis` (10 absent figures),
   `S183_Sanjeevni_Daily_Cash_Design_and_Marg_Findings` (8),
   `S183_Sanjeevni_Cash_Reconciliation_YesBank` (6), `S191_Darpan_Money_Model_Objective_Report` (6),
   `S179_Finance_LIVE_State` (3), `S189_70k_Gate_Verification` (1), `S191_Waiver_Capacity_Layer_D332_Design` (1).
   **This is a weaker test than reading** — it sees hashes and money, not rationale — so those
   twelve "zero absent" results should be read as *"no unique hash or figure"*, **not** as
   *"no unique content"*.

5. **The older duplicate of each of the four duplicated paths could not be read at all** (1.2), so
   nothing is known about their contents, including whether either is a stump.

6. **Google Drive was not searched.** The manifest describes Drive as a delivery surface rather than
   a canon store, and the cold kit was checked instead. If the owner believes any of the 76 was ever
   filed to Drive, that is a cheap additional check and it would change the "no other store"
   classification for those documents.

---

## §5 · WHAT PHASE 1 AND PHASE 2 ACTUALLY ESTABLISHED

The plan's §3 predicted the inversion and it is what happened:

> *"If a session record holds something unique, it is not flab — it is an unregistered canonical
> document, and it gets promoted to Tier 1 rather than retired."*

**63 of 63 session records tested hold something unique. Zero were found redundant.** The
substantive question is no longer *what can be deleted* but **what must be filed and pinned**, and
the plan's §5 approval list should be re-scoped accordingly.

**Nothing here is a recommendation to act.** Phase 3 is the owner's to authorise, and on this
evidence the first Phase-3 action is not a retirement — it is a **filing**.

---

*S203 · Phases 1 and 2 only · read-only · no file created, moved, modified or deleted in any store ·
no git operation run · every md5 quoted was transcribed from a `md5sum` run in this session (F-116).*
