> ## WORKING PAPER — S203, not a reference
> Written to work something out on 26-Aug-2026. Its conclusions live in
> `MARG_MEDICAL_CURRENT.md`; its evidence and reasoning live in
> `MARG_MEDICAL_HISTORY.md`, both in `deploy_kits/MARG_MEDICAL/`.
> **Do not cite this as current.** Retained, not deleted (F-23).

# S203 — MARG / MEDICAL PC: RETIREMENT LIST

**Session 203 · 26-Aug-2026 · READ-ONLY.** No document was removed, edited or moved by this pass.
No `git` command was run (F-131). No token value was read or printed.

**Authority for the exercise:** the owner has authorised retiring superseded Marg documentation
from project knowledge ("remove any which need to go or retire, we do all now and here for once").

**The gate, and it is not negotiable:** *a document may be retired only if it is provably
recoverable, by md5, from a store other than project knowledge.* F-89 lost three canonical
documents permanently; two more at S131 survived only because a cold backup had them.

---

## 0 · VERIFICATION DONE BEFORE CLASSIFYING — and one blocker

### 0.1 The second store is real. I checked it myself.

`deploy_kits/S203_MARG_CANON/` on manojz, verified this session:

```
md5sum -c SUMS.md5   ->  exit 0, every row OK
SUMS.md5 itself      ->  4642b0227c49c52957637e65e3eb94c9
rows in SUMS.md5     ->  52
files under the dir  ->  54
```

**Precisely what those 52 rows are:** 51 copied documents **+ the folder's own
`README_S203_MARG_CANON.md`.** The 54th file is
`MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v1.md` — **which is present in the folder but is NOT listed
in `SUMS.md5` and therefore is not covered by the folder's own integrity check.** I hashed it
directly: `57d12c8c46dd633a318f096344d02709`, 26,732 bytes — matching the value I was given.
**Fix owed: add the master to `SUMS.md5`.**

### 0.2 An independent content check, not a hash echo

A matching md5 in `SUMS.md5` proves the repo copy is internally consistent. It does **not** prove
the repo copy carries the same content as the Project copy — that is F-88's exact lesson, and
`S203_KB_CENSUS_PHASE12` §4.1 already warns that a same-named file is not a byte-identical copy.

So I ran a **second, independent test**: for each candidate I grepped the repo copy for distinctive
verbatim strings **taken from my own full reading of the Project copies earlier today**. Those
readings came from `project_read`, not from the repo, so the two sources are genuinely independent.

**Result: every document tested carries its distinctive content.** Two apparent misses were both my
grep terms, not the files, and are resolved in §0.3. Copies are **verbatim — no provenance header
was prepended**, confirmed by `head` on three files.

### 0.3 A misattribution corrected, in my own earlier report and in the census

Chasing one of the two misses found a real error:

**§4A — the sale-return correlation design measured on nine real credit notes — lives in
`S180_Marg_Feed_Request_and_Flow.md`, NOT in `S180_Marg_Feed_Transport_Design.md`.** Proven:
`grep -l 'CN00154'` returns `S180_Marg_Action_Register.md` and `S180_Marg_Feed_Request_and_Flow.md`
only; the heading list of `Transport_Design` runs §0–§6 with no §4A.

**Both `S203_KB_CENSUS_PHASE12` row 51 and my own `S203_MARG_DOC_INVENTORY` §3 attribute §4A to
`Transport_Design`, and both use it as the reason not to retire that document.** The reason was
attached to the wrong file. `Transport_Design`'s genuinely unique content is §1 (the
watcher-vs-upload trade table), §3.4 (the idempotent per-day upsert that makes the feed
self-healing), §3.5 (the self-checks), §3.6 (PHI handling) and §3.7 (the parallel-run
recommendation). It is still KEEP — but for the right sections.

### 0.4 THE BLOCKER — this file could not be written to the Project

**The `Projects` tool was disabled part-way through this task** (`No such tool available: Projects.
Projects is disabled for this session, in subagents as well as here`). `ToolSearch` finds no
replacement.

Two consequences, stated plainly rather than worked around:

1. **This document could not be written to `claude/S203_MARG_RETIREMENT_LIST.md`.** It is staged at
   `/home/claude/S203_MARG_RETIREMENT_LIST.md` and must be published by hand or by a session that
   has the tool.
2. **I could not re-read any Project document after the tool was withdrawn.** Everything below rests
   on readings taken earlier in this same session, plus the repo bytes. Where a document was never
   read from the Project at all, it is **CANNOT DECIDE**, not RETIRE.

### 0.5 The sequencing condition — read this before removing anything

`README_S203_MARG_CANON.md` says so itself:

> *"**Not manifest-pinned.** These rows are not (yet) in `CANONICAL_MANIFEST.md`. Filing and pinning
> is the owner's, at a close. **Until then Phase 0 does not verify them** — `SUMS.md5` here is the
> only check."*

**An unpinned repo folder is the F-107 / F-184 condition exactly.** `KB_canon_all` went four
sessions stale with twelve pinned documents missing and nothing noticed, because no numbered step
maintained it. `S203_MARG_CANON` has no numbered step either.

> **RECOMMENDATION: pin first, retire second.** Give `S203_MARG_CANON` a manifest row — or pin the
> individual files — at this close, *then* remove the Project copies. Removing first moves a
> document from "one store, unindexed" to "one store, unindexed **and unwatched**", which is not an
> improvement. The whole cost of waiting is one close.

---

## 1 · RETIRE — 13 documents

Superseded as a statement of current state; content carried by the master, by a newer document, or
by the repo copy; **not** named in the master's own §10 "must be preserved" list; not a manifest
row; not the sole home of an unexecuted instruction or an operational recipe.

All repo paths are relative to `drmanoj-clinic-automation/deploy_kits/S203_MARG_CANON/`.
All md5s verified by `md5sum -c SUMS.md5` (exit 0) this session.

| # | Project path | Repo proof (md5) | Superseded by — where its content now lives |
|---|---|---|---|
| 1 | `claude/S195_FINAL_PINS.md` | `S195_FINAL_PINS.md` · `c368c43fedb41786fcade130f0ea0931` | Every VPS pin superseded many times. Its one durable item — `SEND_TO_CLINIC.bat` = `e19a8a777ac22fe75a242f1eb9762185` — is now **independently re-measured on the machine** and carried in **master §3.2**, so it has two sources for the first time. |
| 2 | `claude/S195_Close_Summary_FINAL.md` | `S195_Close_Summary_FINAL.md` · `b1bcdceec46223c08783782c56092824` | The S195 narrative was folded into **Archive §S195** at the S197 fold (manifest, Archive v1.44, "pure append, prefix proven byte-identical"). Its canon-debt warning is spent — the fold happened. |
| 3 | `claude/S195_Marg_dbf_Encryption_Finding.md` | `S195_Marg_dbf_Encryption_Finding.md` · `c3f7d453f576218b104d069ea4e04b68` | **Superseded by its own successor**: `S195_Marg_decrypt_partial_key.md` states *"it supersedes the earlier optimistic 'crackable via crib-drag' note."* That successor is repo-preserved at `deploy_kits/KB_canon_S197fold/filed/` · `3f83f1594fcb22e29b6aba0458e6574b` (hashed by me today). **Retiring the optimistic note removes a live wrong answer from the store sessions actually read.** |
| 4 | `claude/S195_Email_Hardening_and_Marg_Guard_BuildState.md` | `S195_Email_Hardening_and_Marg_Guard_BuildState.md` · `4456995fcb9db746978722de1e0441df` | Build state for kits long installed. The guard chain it describes is **not on the medical PC at all** (master §3.1). The email half belongs to a different subsystem and is in Archive §S195. |
| 5 | `claude/S201_A1FIX_Live_Pin_Record.md` | `S201_A1FIX_Live_Pin_Record.md` · `c069cd4b36a604618cd5d2a4e47c0844` | Its pin (`d930b6b5…`) has moved four times since; live is `50ac4c86…`. The durable item — the offline-harness recovery recipe — is intact in the repo copy and cited by `S201_PARKED_BACKLOG` §B, which stays. |
| 6 | `claude/S201_Part0_Rescan_Record.md` | `S201_Part0_Rescan_Record.md` · `4247b6153f649f7607e8cace84bae7e0` | The rescan is live and documented as procedure in **`MARG_PIPELINE_REFERENCE_v1` §7** and **`..._MAINTENANCE_FLOW_v1` §3**. The 11 rescued business dates and the `index.csv.before_rescan_20260825-142311` backup name are history, preserved in the repo copy. |
| 7 | `claude/S201_Part1_Capture_And_Agent_Record.md` | `S201_Part1_Capture_And_Agent_Record.md` · `8be4f6c758b2054e14861189c49c5b35` | The agent is described current in **master §3.3/§3.4**, and its live pin is now measured (`7b9a76f2…`, S203.3). Every manojz pin in this document is superseded. The 10:37 watcher-death timeline is history, repo-preserved. |
| 8 | `claude/S201_Marg_Outbox_Never_Drained_Finding.md` | `S201_Marg_Outbox_Never_Drained_Finding.md` · `d0adbd36217ad4922ef0474b2bdd5774` | **F-179 is CLOSED**; its full text is in the **Fault Register v2.41** and **Archive §S201**, and the symptom row is in **master §7**. |
| 9 | `claude/S201_Medical_Pipeline_Completion_Audit.md` | `S201_Medical_Pipeline_Completion_Audit.md` · `a0452bbb7491ac2adc909945df254ca1` | **Superseded by measurement.** Its §2 pins were read from manojz's mirror; `S203_MEDICAL_PC_PINS` read the machine and master §3.1 lists what the mirror wrongly implies. Its §4 "found 25-Aug" claim is **the error corrected at master §9 #8**. Keeping it in the read-store keeps that error in circulation. |
| 10 | `claude/S201_WHATS_LEFT_FOR_YOU.md` | `S201_WHATS_LEFT_FOR_YOU.md` · `907ff59bb8d41c64117cac4d239a932a` | A point-in-time owner list from 25-Aug, wholly superseded by **`OWNER_TODO_LIVE.md`** (26-Aug, and the A10 numbered step keeps it current) and by **master §6**. Its unique item (18 Marg database files on the health surface) is in the repo copy. |
| 11 | `claude/S180_Marg_Feed_Feasibility.md` | `S180_Marg_Feed_Feasibility.md` · `6db52a89106e17e17769f2d31be6f24d` | A route survey whose verdicts are spent — the route was chosen and built. Its live evidence (`up_sale`/`up_saleinfo` dormant, `MARGDEMO`, the `serverbackup` weekday rotation) survives as **vendor asks** in `S180_Marg_Action_Register` V8/Q5 and `Marg_Report_Requirement_Sanjeevni`, both KEEP. |
| 12 | `claude/S179_Sanjeevni_Medical_Module_Build_Contract_v1.md` | `S179_Sanjeevni_Medical_Module_Build_Contract_v1.md` · `f6de1a5eaa59f1c685caca988ad1a3b8` | **Superseded whole by v2, which says so.** *(Caveat: I did not read this from the Project — see §4 #1. Its §7 ICICI merchant-statement identification should be confirmed present in v2 before removal.)* |
| 13 | `claude/S203_MARG_MEDICAL_SYSTEM_MAP.md` | `S203_MARG_MEDICAL_SYSTEM_MAP.md` · `5221196a9e531416cc61aa77f5bc9f5b` | **Superseded whole by the master, which corrects three of its errors** — AF-1 "still armed" (master §3.1), the backup "configured Oct-2025 and never once run" (master §4.2), and the "four-copy `marg_report.py` problem" (master §9 #2). It was written from the record; the master was written from the machine. Its D350 §5 gap tables are preserved in the repo copy. |

---

## 2 · KEEP + PROMOTE — 8 documents

Unique canonical content; should gain a manifest row at the close.

| Project path | Repo proof | The unique item |
|---|---|---|
| `claude/MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v1.md` | in the folder, `57d12c8c46dd633a318f096344d02709`, **but ABSENT from `SUMS.md5`** | The consolidation itself. **It is the one document this whole exercise produced and it is the one file in the folder its own checksum file does not cover.** Pin it, and add it to `SUMS.md5`. |
| `claude/S203_MARG_DOC_VERIFICATION.md` | `f9eb31693da2319430dea6b34a419bfa` | **82 claims tested against live code and the machine: 42 VERIFIED, 17 WRONG, 12 STALE, 11 UNVERIFIABLE**, each with file+line. It is the evidence base for the master's §9 and the only audit of the reference set that exists. |
| *(repo-only)* `deploy_kits/S203_CENSUS_BACKUP/S203_MEDICAL_PC_PINS.md` | `976a6f0ccc22318a603d055f81541f71` (hashed by me today) | **The first medical-PC live pins ever taken**, read from the machine; the `MargAgent.cmd` text verbatim; the six things the never-purging mirror gets wrong; the proof that no scheduled backup was ever configured. **Not in project knowledge, not in `S203_MARG_CANON`, in no manifest row.** |
| `claude/S202_Marg_Transport_Resilience_D350_CONTRACT.md` | `64dfdd17d085642a1174fd034f92b93f` | A **signed-contract-class document with no manifest row**, when D329/D330/D331/D332/D335/D336/D337 all have one. §8's counter-argument is what the owner actually ruled on. |
| `claude/S180_Marg_Folder_Recon.md` | `f3393979354411105a253e2715fabe7b` | **The entire Marg data-layer analysis** — the 16-byte prefix, the period-256 proof, `codepage=437`, `marguser.csv` as the unencrypted control, the `.c18` inventory. **The master carries none of it** (§3 below). |
| `claude/S180_Marg_Daily_Sale_Button_Settings.md` | `3f46935784261a18f50da552d6fd31ee` | **The exact Marg report-screen and Excel-delimiter settings — the only recipe for regenerating the feed after a Marg reinstall.** The master names it as must-preserve and does not carry it. |
| `claude/Marg_Report_Requirement_Sanjeevni.md` | `ee3cd2549948d6437ef75480d9dadec0` | Licence **`LIC-14116710`**, E-Business ID `39548`, R1–R6, the §8 acceptance list, and the truncation defect written up for the vendor. **The vendor asks have never been answered**, so this is an open instruction, not history. |
| `claude/AUDIT_RUN_2026-08-24_slice1.md` | `17746ec35727c14e2c5b173c9235fce7` | AF-1…AF-6 in full **and the AF-3 duplicate-advance scan command**, which `OWNER_TODO_LIVE` ⭐0 #7 orders run *before the August close*. The instruction lives in two backlogs; the means lives here. |

---

## 3 · KEEP — current, manifest-pinned, or content nowhere else

| Project path | Why KEEP |
|---|---|
| `claude/MARG_PIPELINE_REFERENCE_v1.md` | **Manifest Tier-1 CURRENT.** Master §0 defers to it for detail. Needs the §9 corrections applied, not retirement. |
| `claude/MARG_PIPELINE_MAINTENANCE_FLOW_v1.md` | **Manifest Tier-1 CURRENT.** The 60-second check and the guest-access decision tree. |
| `claude/MARG_INGESTION_REFERENCE_v1.md` | **Manifest Tier-1 CURRENT**, and **the master carries none of the ingestion half** — D313, `marg_net_sql`, the confidence tiers, the Docterz match key are all absent from it (§4 below). |
| `claude/S195_Medical_Watcher_LIVE_Reference.md` | **Manifest Tier-1 CURRENT**, still labelled *"SOLE reference"*. Retiring a pinned canonical row from the Project before the manifest row is changed would break Phase 0. Change the label first. |
| `claude/Clinic_Source_Data_Retention_Policy_v1.md` | **Manifest Tier-1 CURRENT** and **still a draft awaiting the owner's approval**, with the CA question open. |
| `claude/S180_Marg_Sample_Findings.md` | Master §10 names it must-preserve. The C: tree on 15-Aug, the column variants, and **the text-cell credit-note trap the master does not carry**. |
| `claude/S180_Marg_Action_Register.md` | **V7's silent-truncation warning is absent from the master** (§4). Plus U11's measured attribution ceiling and U7's DISCOUNT-vs-DR/CR correction. Unanswered vendor asks V1–V9 / Q1–Q8. |
| `claude/S180_Marg_Feed_Request_and_Flow.md` | **§4A, the sale-return correlation design measured on nine real credit notes** (see §0.3 — this is where it actually is), plus §4's four design invariants. |
| `claude/S180_Marg_Feed_Transport_Design.md` | §3.4 the idempotent per-day upsert (why the feed is self-healing), §3.5 the self-checks, §3.6 PHI handling, §3.7. **Retire the §2 route ranking, not the document.** |
| `claude/S179_Marg_Sale_Report_Analysis.md` | **Manifest-NAMED in §S179 companions.** The money rule's derivation (`277,083 − 193,412 = 83,671 = 88,777 − 5,106`) — **and the master carries no money rule at all.** |
| `claude/S201_Marg_Pipeline_Rebuild_Plan.md` | `S203_PENDENCY_RECONCILIATION` Thread 2 records it as one of only two homes of **AF-5's substance** (row K). Parts 6–8 are unbuilt. |
| `claude/S201_Parts2_3_4_Record.md` | Master §10 must-preserve: the per-type `end_marker` derivations and the ₹476,393 cross-report control. |
| `claude/S201_Part1_xlsx_Dependency_Removed.md` | Master §10 must-preserve: **the only proof `xlsx_stdlib.py` is correct** (170 cells vs openpyxl, 0 mismatches), for a file master §8 lists as existing nowhere but two PCs. |
| `claude/S201_Month_vs_Marg_Explained.md` | **`MARG_PIPELINE_MAINTENANCE_FLOW_v1` §2 points readers at it by name.** A current canonical document cites it as the full explanation. |
| `claude/S201_PARKED_BACKLOG.md` | C1–C8 and the E-section AF items; four of C3–C8 are recommended for F-numbers and none is minted yet. |
| `claude/S202_PENDENCY_AUDIT.md` | N1–N13. **Its repo filing is OWED at the S203 close** per `OWNER_TODO_LIVE`; the Project copy stays until the pinning happens. |
| `claude/S203_MARG_CODE_TRUTH_MAP.md` | The only reading of the code: §3.1 the pull produces no log, `marg_router.py:349-354`, the state-file table, §5's backup-hook analysis with §5.4's honest caveat. |
| `claude/S203_MARG_DOC_INVENTORY.md` | This exercise's own evidence base — **with §0.3's correction applied.** |
| `claude/S203_KB_CENSUS_PHASE12.md` · `S203_PENDENCY_RECONCILIATION.md` · `S203_KB_CONSOLIDATION_PLAN.md` | In active use; the consolidation plan's §5 approval gate is not yet exercised. |
| `claude/OWNER_TODO_LIVE.md` | **Un-manifested by design** (A10). The living list. |
| `claude/START_HERE_SESSION_203.md` · `claude/AUDITOR_SEED_v1.md` | Manifest rows, live. |
| `claude/S183_Sanjeevni_Daily_Cash_Design_and_Marg_Findings.md` · `claude/S186_F113_Backfill_Silent_Shortfall.md` | Manifest-pinned; F-113's struck-through wrong diagnoses are kept deliberately (F-23). |
| `claude/S195_medical_kit/*` (6 files) | The macro coordinates and the guard sources. Manifest names the kit; two of the six are absent from `deploy_kits/S195_MARG/` and exist only in `S203_MARG_CANON` now. |

---

## 4 · CANNOT DECIDE

| # | Document | What I could not verify |
|---|---|---|
| 1 | `claude/S179_Sanjeevni_Medical_Module_Build_Contract_v1.md` · `claude/S179_B1_Medical_Reconciliation_Report.md` | **I never read either from the Project.** The repo copies exist and are hash-verified, and I confirmed they contain `ICICI` and `carry-forward` respectively — but I cannot compare them against the Project copies, and the Projects tool is now gone. #1 is listed RETIRE on the strength of v2 declaring it superseded; **if that cannot be confirmed, treat it as KEEP.** |
| 2 | Six repo-only `S195_*` documents — `Monthly_Cycle_Discovery` · `Monthly_Cycle_Map_and_Backlog` · `Correction_Checklist_Design` · `Close_State_and_Next` · `Drawer_Investigation_Gaps_and_Checks` · `Credit_Note_Sign_Fault` | Located in `deploy_kits/KB_canon_S197fold/filed/` and Marg-touching (6–15 hits each), **not opened**. They are not in project knowledge, so they are not retirement candidates — but no redundancy verdict is claimed for them either. |
| 3 | Whether any Project copy is **byte-identical** to its repo copy | Impossible in principle for documents under ~261 KB (`S181_postclose_addendum` §3 — inline text may corroborate, never convict *or acquit*), and impossible in practice now that the tool is withdrawn. **What I do claim: distinctive verbatim content survives in every copy tested.** |
| 4 | Google Drive as a third store | `mnt/Clinic Data Archive` **failed to mount** in this shell. If any of these was ever filed to Drive it would strengthen the case; absence there proves nothing. |
| 5 | Whether the repo working tree is published | `git status` was not run (F-131). `OWNER_TODO_LIVE` ⭐0 #3 says the S202 close is committed locally only until `PUBLISH_ALL.bat` runs. **If the preservation pass is unpublished, the "second store" is one disk, not two.** This is the sharpest open question on the whole exercise. |

---

## 5 · WHAT THE MASTER REFERENCE GETS WRONG OR LOSES

**This matters more than the list.** The master is strong — it is measured rather than
carried-forward, and §3, §4 and §5 are better than anything they replace. The findings below are
narrow and specific.

### 5.1 Two factual errors

**1 · §8 blind spot 5 — the token count is wrong in both directions.**

> *"The token has at least five copies, not the three on record — the systemd unit, the medical PC's
> `token.txt`, the manojz cache, **plus `D:\Downloads\MARG_TOKEN_S187.txt` and
> `D:\Downloads\margsync\SendToClinic\token.txt`**."*

**"The manojz cache" and `D:\Downloads\margsync\SendToClinic\token.txt` are the same file** —
`MARG_PIPELINE_REFERENCE_v1` §4 item 3 and `marg_gate.py:56-57` both name that path as the cache.
So the list double-counts. And it **omits one I can evidence**: a filename listing of the mounted
`Downloads` folder (names only; **no file contents read, no value printed**) returns
`margsync/_to_delete/S201_20260825/loose/finance marg token.txt`, which
`S203_MARG_CODE_TRUTH_MAP` §7 also records.

**Corrected: five distinct stores** — the systemd unit *(unverifiable this session)* · the medical
PC's `token.txt` · the manojz cache · `MARG_TOKEN_S187.txt` · the `_to_delete` loose copy — **plus
`pipeline_status.py` as a fourth consumer** (`S203_MARG_DOC_VERIFICATION` claim #33). On the
project's oldest and highest-severity open item, a rotation list that is wrong about which files
exist is the failure mode itself.

*(Separately, and not a Marg token: the same listing shows
`Downloads/Projects/In-Development/MyOperator-Call-API/image_CONTAINS_TOKEN.png`. Different
subsystem; named here only so the rotation sweep does not miss it.)*

**2 · §10's headline numbers are already stale, and they are the decision-relevant ones.**

> *"**39 are orphans** with no row of any kind; and **30 exist in exactly one store** — project
> knowledge — with no repo and no cold-kit copy."*

**The second clause is no longer true.** The preservation pass this session put 51 of them into
`deploy_kits/S203_MARG_CANON/`. The master's §10 describes the world as it was before the folder it
was written alongside. A reader deciding retirement from §10 would conclude no document can be
retired at all.

### 5.2 What the consolidation loses — three whole subjects

The master's §0 is honest that it does not repeat everything. But three subjects are absent from it
*and* absent from the documents it defers to, so a reader of the master plus the four references
would not learn them. Verified by grep of the master:

**1 · Marg's tables are ENCRYPTED, and remote decryption is retired on a thorough negative.**
`encrypt`, `decrypt`, `19 a3 95 78`, `codepage` — **all ABSENT from the master.** §4.1 says *"`mdis.c18`
is the bill header table, `dis.c18` the drug lines"* and stops. A reader could reasonably conclude
those are readable files. They are not: Marg wraps them via bsVault→Chilkat32, and
`S195_Marg_decrypt_partial_key` concluded *"Remote decryption from the files alone is not
tractable"* after four independent attacks. **Without that, someone re-opens a closed dead end.**
Carried only by `S180_Marg_Folder_Recon` + `S195_Marg_decrypt_partial_key`.

**2 · The money rule, and V7 the silent truncation.** `CASH column`, `D.R.`, `Disc.Bill`,
`GRAND TOTAL`, `credit note` — **all ABSENT from the master.** These are the two facts that decide
whether a report is *usable*:
- `cash = the CASH column` · `UPI = NET − CASH` · **never the `D.R.` mode field** (it agrees on 133
  of 138 bills and the five it misses are split-tender);
- a month-to-date export **with item detail truncates silently at ~44 pages** — the file opens, the
  rows are there, only `GRAND TOTAL` is missing.
Carried only by `S179_Marg_Sale_Report_Analysis`, `S180_Marg_Feed_Request_and_Flow`,
`S180_Marg_Action_Register` V7 and `Marg_Report_Requirement_Sanjeevni` §6 — **all four KEEP.**

**3 · The whole ingestion half.** `D313`, `marg_net_sql`, `phone_last4`, `clinic id` — **all ABSENT
from the master.** §2 stops at *"Dr Manoj alone applies it."* That is a deliberate deferral to
`MARG_INGESTION_REFERENCE_v1`, and it is the strongest possible argument that that reference
**cannot be retired** — including its §9 item 5, which D348 retired and which therefore needs
correcting in place, not removing.

### 5.3 One omission worth a line in §5

**§5.3 "If the medical PC dies tomorrow"** lists what you would need. It does not say that
`D:\MARGERP\users\<id>\report\` is a *fixed overwritten slot* and that **the report-screen settings
required to regenerate an export are in `S180_Marg_Daily_Sale_Button_Settings`, not in Marg's
defaults.** After a vendor reinstall the buttons are gone. §10 names the document; §5.3 — the
section someone reads in an emergency — does not point at it.

### 5.4 What the master gets right that nothing else did

Recorded because it is the reason the exercise was worth doing: §3.1's list of what is **not** on
the medical PC and the striking of AF-1 · §3.3's warning that the S195 restart recipe kills the
supervisor · §4.2's settling of the backup question by measurement · §5, which **did not exist
anywhere before** · §2's warning that `_last_pull.txt`'s `ok` means almost nothing · and §9 #8
crediting the C: tree to `S180_Marg_Sample_Findings` on 15-Aug.

---

## 6 · RECOMMENDED ORDER

1. **Add the master to `SUMS.md5`** — it is the only file in the folder the checksum does not cover.
2. **Publish the repo** (`PUBLISH_ALL.bat`) — until then the second store is one disk (§4 #5).
3. **Pin `S203_MARG_CANON` in the manifest** at this close (§0.5).
4. **Then** remove the 13 §1 documents from project knowledge.
5. Correct the master's §8 token list and §10 counts; add §5.3's pointer.
6. Promote the eight §2 documents to manifest rows; strike the *"SOLE reference"* label on
   `S195_Medical_Watcher_LIVE_Reference` as Row 2 of the coverage map lands.

---

*S203 · read-only · every md5 quoted was computed by `md5sum` in this session or transcribed from
the file that carries it · absences stated with what was searched · no document removed, moved or
edited · no git command run · no token value read or printed · no patient identifier reproduced.*
