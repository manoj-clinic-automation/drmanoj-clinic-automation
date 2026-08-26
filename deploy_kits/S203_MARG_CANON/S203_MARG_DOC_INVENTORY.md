> ## WORKING PAPER — S203, not a reference
> Written to work something out on 26-Aug-2026. Its conclusions live in
> `MARG_MEDICAL_CURRENT.md`; its evidence and reasoning live in
> `MARG_MEDICAL_HISTORY.md`, both in `deploy_kits/MARG_MEDICAL/`.
> **Do not cite this as current.** Retained, not deleted (F-23).

# S203 — MARG + MEDICAL PC: DOCUMENT INVENTORY AND SUPERSESSION MAP

**Session 203 · 26-Aug-2026 · READ-ONLY.** No canonical document was edited, no git command was
run, no F-number minted. This file is the only write.

**Purpose.** A single MASTER reference for Marg and the medical PC is being written. This document
is its *bill of materials*: every document anywhere that says anything about Marg or the medical
PC, what each uniquely holds, whether it is current or superseded, and what the master must carry
so that every superseded document can be retired without losing a fact.

**Governing rule, from F-89 (three canonical documents permanently lost) and the S131 stumps:**
**nothing below is called redundant unless the other place its content lives is named.** Where a
document's content was tested and found unique, the unique item is quoted. Where a document was
not opened, it says so.

---

## 0 · METHOD, AND WHAT THIS PASS COULD NOT SEE

**Two stores were swept end to end:**

1. **The attached claude.ai Project** — all 167 rows of the document list enumerated via
   `project_info`; every Marg/medical-relevant document read in full via `project_read`.
2. **The git working tree** on manojz at `~/mnt/dr-manoj-git/drmanoj-clinic-automation` — **1,823
   files** enumerated (`find`, excluding `.git`), then filtered two ways: by **filename**
   (`*marg*`, `*medical*`, `*sanjeevni*`, `*watcher*`, `*retention*`) and by **content**
   (case-insensitive `marg|medical pc|manojz` across every `.md` outside the Archive, the Fault
   Register and the manifest, with hit counts). `CANONICAL_MANIFEST.md` was read in full and is
   the authority for what is canonical and at which tier.

**Hashes.** Every md5 in this document was either computed by `md5sum` in this session and is
labelled as such, or transcribed from the file that carries it. **No hash is invented.** Where a
value could not be established it says **not established** and says where it was looked for
(F-116, D172/D188).

**What this pass could NOT see, stated so it is not mistaken for coverage:**

- **Google Drive was not searched.** `S203_KB_CENSUS_PHASE12` §4.6 records the same gap. The
  `Clinic Data Archive` mount failed in this shell (`mnt/Clinic Data Archive failed to mount`), so
  `ToMedical\`, `FromMedical\` and the offsite `MargArchive` were not enumerated. If any
  project-only document was ever filed to Drive, that would change its "one store" classification.
- **No live box was reached.** Nothing here confirms the VPS, the medical PC or manojz. Every
  "live" statement is *the bytes the pin list says are live*, or a figure another document
  measured and labelled.
- **`git status` was not run** (F-131: `git status` is not read-only and left index locks across
  S185–S188). The working tree may hold unpublished commits; it is at least as new as origin.
- **Six repo-only `S195_*` documents were located and hash-listed but not read in full** — they
  are marked *(not opened)* in Group B and carry no redundancy verdict.
- **Under-261 KB project documents cannot be hash-verified.** The connector returns them as inline
  text and this project forbids convicting or acquitting on re-keyed text
  (`S181_postclose_addendum` §3). For those, "exists in no other store" is proved by **absence of
  distinctive verbatim strings**, which is conclusive for absence and is not proof of
  byte-identity where a same-named repo file exists.

---

## 1 · THE INVENTORY

**69 documents.** Grouped by *provenance status*, because that is what decides whether a document
can be retired at all.

### Group A — individually pinned in `CANONICAL_MANIFEST.md`, present in BOTH stores (8)

Every md5 below was computed this session in
`deploy_kits/KB_canon_all/` and matched its manifest row.

| # | Document | Lives | Manifest row | Date | md5 (computed this session) | Covers |
|---|---|---|---|---|---|---|
| A1 | `MARG_PIPELINE_REFERENCE_v1.md` | project KB + repo | **Tier 1 CURRENT** | S201, CORRECTED S202 | `97b3cf73f7f83c0860bde2d911596ff7` | capture → route → archive → send, end to end; the upload contract; the three token copies; the runbook "a day did not arrive"; folders; adding a report type; launching Marg from a script |
| A2 | `MARG_PIPELINE_MAINTENANCE_FLOW_v1.md` | project KB + repo | **Tier 1 CURRENT** | S201, CORRECTED S202 | `c2b5251f55762490ad219b8855a18dd8` | the 60-second health check (three files, all on manojz, none needs a login); fault flow **by symptom**; routine maintenance; what every folder is; what to send Claude; the six things that will bite |
| A3 | `MARG_INGESTION_REFERENCE_v1.md` | project KB + repo | **Tier 1 CURRENT** | S201 | `4d603b727a91a7c782992f092fc949e3` | the server half: push → stage → apply → `ingest_day` → the confidence gate → `marg_net_sql()`; D313; batch status; the review queue and the Docterz plan |
| A4 | `S195_Medical_Watcher_LIVE_Reference.md` | project KB + repo ×2 | **Tier 1 CURRENT** (labelled *"SOLE reference for the Marg capture pipeline"*) | S195, filed S197 | `885090ab946b61e7b5a990a14a190a15` | the resident watcher, the Store-stub Python discovery, the `MargWatcher.cmd` autostart text verbatim, the PowerShell restart recipe |
| A5 | `Clinic_Source_Data_Retention_Policy_v1.md` | project KB + repo ×2 | **Tier 1 CURRENT** (*draft for owner approval*) | S195, filed S197 | `90831162f985359b69725b1dc874e679` | export retention: measured sizing, the three-copy model, 8-year rule, purge rules, the §6 "what this does NOT cover" paragraph |
| A6 | `S186_F113_Backfill_Silent_Shortfall.md` | project KB + repo | **Tier 1** | S186, filed S187 | `0fc78c1fe326f16e1a907a47805e8267` | F-113 in full **including two wrong diagnoses struck through, not deleted** |
| A7 | `S183_Sanjeevni_Daily_Cash_Design_and_Marg_Findings.md` | project KB + repo | manifest **§S183 footer**, not a Tier-1 table row | S183 | `de4f88b3a48e71c19e708f6a1d274f41` | the S183 Marg findings folded into the cash design |
| A8 | `MARG_PIPELINE_MAINTENANCE_FLOW_v1.md` **(S201 pre-correction bytes)** | repo `KB_canon_S201close/` only | pinned in manifest **§S201 block** | S201 | `f02cd8bdbb9078ae51837534675e69cb` | the version **before** the S202 Tailscale correction — retained lineage |

> **A note on A1's lineage that matters for the master.** `MARG_PIPELINE_REFERENCE_v1` was filed at
> the S202 **open** at `d34d06169285a47a9180d71b65898e1f` (manifest §S202-OPEN block) and
> **CORRECTED at the S202 close** to `97b3cf73…`. **The `d34d0616…` bytes exist nowhere in the
> repository today** — `find` returns exactly one `MARG_PIPELINE_REFERENCE_v1.md`, and it hashes to
> `97b3cf73…`. A pinned version was overwritten rather than retained. Recorded, not softened.

### Group B — repo-only, covered by the manifest's WILDCARD row, no individual md5 (17)

The manifest's row reads: ``S193_Close_Summary_and_Pins` · `S193_*` · `S194_*` · `S195_*` ·
`S196_*` (session docs)` … *(each hashed in `KB_canon_S197fold/filed/SUMS.md5`)*``. These are
therefore **acknowledged but not individually hash-pinned, and Phase 0 cannot verify any of them.**
All were "re-compacted out of project knowledge after byte-proof against git" at the S197 fold — so
for these, **git is the only store**, the mirror image of Group D.

md5s below were computed this session in `deploy_kits/KB_canon_S197fold/filed/`.

| # | Document | md5 | Date | Covers |
|---|---|---|---|---|
| B1 | `S195_Marg_Report_Router_Design.md` | `163f3aef3f93e1483986ad276154a039` | 21-Aug | the router's **design rationale**: two-signal identification, refuse-on-partial-match, the `index.csv` column list, the versions-of-a-day monthly compare |
| B2 | `S195_Club3_Router_Signatures.md` | `85fe790e6b067d39449563947a7b7313` | 23-Aug | the STOCK/EXPIRY/PURCHASE signature derivations; `dating: file_mtime`; the **overwrite hole closed**; the three Docterz export shapes |
| B3 | `S195_Marg_Push_401_Incident.md` | `2cd5a8554c290177fbe4c57a64a8d13b` | 21-Aug | the 401 crisis root cause + **the token-comparison diagnostic that never exposes the secret** |
| B4 | `S195_Marg_decrypt_partial_key.md` | `3f83f1594fcb22e29b6aba0458e6574b` | 21-Aug | **THE THOROUGH NEGATIVE** — remote decryption retired, with the four attacks and the falsifying evidence |
| B5 | `S195_ToMedical_Pipe_Broken.md` | `f3b16d4c7f86f8fc57b50617cfc058ef` | 23-Aug | ERROR 5 verbatim; **F-168's evidence**; the consequence for Amir's statements |
| B6 | `S195_Medical_PC_Macro_Guard_Runbook.md` | `633bc0a790e226d6501937df3ce30349` | 21-Aug | the medical-PC file inventory with md5s; **the AHK macro's five calibrated screen coordinates**; the portable-Python + vendored-xlrd build |
| B7 | `S195_Medical_PC_Continuation_AHK.md` | `1c4d472962511a0d4a4bb2b373d3a35d` | 21-Aug | **the recorded Marg export click-flow**, captured by `psr.exe` on the box |
| B8 | `S195_Medical_PC_Close_Analysis.md` | `56f5dabbc30de90c88c822efb979e65e` | 21-Aug | **the REPORT_1 vs REPORT_2 / which-login money question** — the two logins carry different versions of the truth |
| B9 | `S195_Medical_PC_Close_Summary.md` | `87508823274b4782e3747d05c331a665` | 21-Aug | the EOS record of the one-off medical-PC leg; the same file record; the pending list |
| B10 | `S195_Marg_dbf_Encryption_Finding.md` | *(also in project KB)* | 21-Aug | the *optimistic* encryption note — **superseded by B4** |
| B11 | `S195_Email_Hardening_and_Marg_Guard_BuildState.md` | *(also in project KB)* | 21-Aug | the guard's build state; `guard_and_send.py` md5; the Z:-drive access facts |
| B12–B17 | `S195_Monthly_Cycle_Discovery` · `S195_Monthly_Cycle_Map_and_Backlog` · `S195_Correction_Checklist_Design` · `S195_Close_State_and_Next` · `S195_Drawer_Investigation_Gaps_and_Checks` · `S195_Credit_Note_Sign_Fault` | not computed | S195 | **(not opened this pass)** — each returned 6–15 hits on `marg\|medical pc\|manojz`. No redundancy verdict is claimed for them. |

### Group C — repo-only, NO manifest row of any kind — **ORPHANS** (9)

| # | Document | md5 (computed this session) | Date | Covers |
|---|---|---|---|---|
| **C1** | `deploy_kits/S203_CENSUS_BACKUP/S203_MEDICAL_PC_PINS.md` | `976a6f0ccc22318a603d055f81541f71` | **26-Aug 08:11 — the newest Marg document anywhere** | **THE FIRST-EVER MEDICAL-PC LIVE PINS**, read from the machine by `medical_census.py` S203.6 |
| **C2** | `deploy_kits/S203_CENSUS_BACKUP/S203_medical_census_S203.1_Pin_Record.md` | `58c232fb43e4c49fadd1c8097c3da5f8` | 26-Aug 07:08 | the census pin chain S203.1→S203.5, three assistant faults, **the `pyflakes` protocol proposal** |
| C3 | `margpull/README_PULL.md` | not computed | S195 | the pull's original install instructions — **STALE, see §4** |
| C4 | `deploy_kits/S202_PICTURE/README_PICTURE.md` | not computed | 26-Aug 02:33 | the two `marg_gate.py` faults: `REPORT_1.XLS` filename, the 56-phantom-missing-days alarm, `_coverage_from.txt` |
| C5 | `deploy_kits/S202_B2B/README_B2B.md` | not computed | 26-Aug | `pipeline_status.py`'s rules, the outbox-counting bug caught by real data, **the success-path-only wiring fault (F-191a)**, the mixed line endings note |
| C6 | `deploy_kits/S195_MARG/SETUP_S195_MARG.md` | not computed | S195 | the guard's original setup — **its install steps are explicitly superseded by B6** |
| C7 | `deploy_kits/S183_M2a/DELIVERY_NOTE.md` | not computed | S183 | the `.xlsx` reader + `S183_marg_map` migration delivery |
| C8 | `deploy_kits/S182_M1a/DELIVERY_NOTE.md` | not computed | S182 | `marg_backfill.py` placement |
| C9 | `deploy_kits/S187_M1a/DELIVERY_NOTE.md` | not computed | S187 | the B5 reception-push (D325) delivery |

### Group D — project-knowledge-only: NO repo copy, NO cold-kit copy (35)

`S203_KB_CENSUS_PHASE12` §1.3 established the cold kit
(`DrManoj_Clinic_FULL_Handoff_Session202_2026-08-26.zip`) contains `deploy_kits/` + `margpull/` +
the manifest only, so **for these documents project knowledge is the ONLY store.** I re-verified
by filename against the 1,823-file tree: none of the basenames below matches any repo file.

| # | Document | Manifest? | Date | Covers |
|---|---|---|---|---|
| **D1** | `S179_Marg_Sale_Report_Analysis.md` | **NAMED as a companion in §S179 · absent from the repo → F-107 OPEN** | 15-Aug | the thirteen-day exactness proof; the cash/UPI derivation; the patient-ID discovery |
| **D2** | `S180_Marg_Folder_Recon.md` | **NAMED in §S179 companions · absent from the repo → F-107 OPEN** | 15-Aug | **the complete Marg file-format analysis** |
| D3 | `S180_Marg_Feed_Feasibility.md` | ORPHAN | 15-Aug | the seven-route verdict table; `up_sale`/`up_saleinfo`; the `serverbackup` scheduler proof; the session-number correction that became F-85 |
| D4 | `S180_Marg_Sample_Findings.md` | ORPHAN | 15-Aug | **the FIRST record of `C:\Users\Public\MARG\17476\`**; the 3-column vs 9-column variant; the text-cell credit-note trap |
| D5 | `S180_Marg_Feed_Transport_Design.md` | ORPHAN | 15-Aug | §4A the sale-return correlation design; §3.6 PHI handling; the watcher-vs-upload trade table **(its route ranking is obsolete — see §3)** |
| D6 | `S180_Marg_Feed_Request_and_Flow.md` | ORPHAN | 15-Aug | the measured-facts table; **the four design invariants**; §4A measured on 9 real credit notes; the target flow diagram |
| D7 | `S180_Marg_Daily_Sale_Button_Settings.md` | ORPHAN | 15-Aug | **the exact Marg report-screen settings, field by field** |
| D8 | `S180_Marg_Action_Register.md` | ORPHAN | 15-Aug | V1–V9 · Q1–Q8 · O1–O10 · U1–U18; **V7's silent-truncation warning**; U11's measured attribution ceiling; U7's DISCOUNT-vs-DR/CR correction |
| D9 | `Marg_Report_Requirement_Sanjeevni.md` | ORPHAN | 15-Aug | **the vendor-facing requirements document** with licence `LIC-14116710`, R1–R6, the §8 acceptance list, the truncation defect written up for Marg |
| D10 | `S179_Sanjeevni_Medical_Module_Build_Contract_v1.md` | ORPHAN | 14-Aug | superseded by v2; retains §7 the ICICI merchant-statement identification *(not opened this pass)* |
| D11 | `S179_B1_Medical_Reconciliation_Report.md` | ORPHAN | 14-Aug | the 36 carry-forward breaks itemised *(not opened this pass)* |
| D12 | `S195_FINAL_PINS.md` | ORPHAN | 22-Aug | **`SEND_TO_CLINIC.bat` = `e19a8a777ac22fe75a242f1eb9762185`**; the AHK-version check; the S195 owner-action list |
| D13 | `S195_Close_Summary_FINAL.md` | ORPHAN | 23-Aug | the S195 pin table; the five faults-and-lessons; the three owner decisions of 22–23 Aug; the canon-debt warning that produced the S197 fold |
| D14 | `S201_Marg_Pipeline_Rebuild_Plan.md` | ORPHAN | 25-Aug | **the A–M fault table with source line numbers**; the seven-failure-mode coverage table; the eight-part rebuild; Part 8 (Lab PC) |
| D15 | `S201_Marg_Outbox_Never_Drained_Finding.md` | ORPHAN | 25-Aug | F-179's evidence: the hour-by-hour timeline, the two file names, the verbatim `marg_router.py` lines 314–318, *"the word `queued` is a lie"* |
| D16 | `S201_Part0_Rescan_Record.md` | ORPHAN | 25-Aug | the rescan design rule; the 11 rescued reports by business date; `data_from`/`data_to`; the deliberate non-signature ruling |
| D17 | `S201_Part1_Capture_And_Agent_Record.md` | ORPHAN | 25-Aug | **the 10:37 watcher-death timeline**; the Drive delivery channel proof; the agent's heartbeat contents; installer v2's false "UPDATED" |
| D18 | `S201_Part1_xlsx_Dependency_Removed.md` | ORPHAN | 25-Aug | **the only proof `xlsx_stdlib.py` is correct** — 170 cells vs openpyxl, 0 mismatches |
| D19 | `S201_Parts2_3_4_Record.md` | ORPHAN | 25-Aug | **the end_marker derivation table per type**; the ₹476,393 cross-report agreement; `covered_days()`/`span_key()`; the always-route fix |
| D20 | `S201_Medical_Pipeline_Completion_Audit.md` | ORPHAN | 25-Aug | the two output trees; the 343-attempt runaway; the popup fix; the three-place cleanup; §8 what is still unfixed |
| D21 | `S201_Month_vs_Marg_Explained.md` | ORPHAN | 25-Aug | the day-by-day review-queue table to the rupee; **bill A003039 (₹190), the bill that disproved the wrong theory**; F-a/F-b/F-c |
| D22 | `S201_A1FIX_Live_Pin_Record.md` | ORPHAN | 25-Aug | **the offline-harness recovery recipe** (which kit holds each live module); the retracted `vps_deploy.sh` claim |
| D23 | `S201_PARKED_BACKLOG.md` | ORPHAN | 25-Aug | A1–A5 · B1–B6 · **C1–C8** · D1–D3 · E (AF-3/4/6) · F (KB hygiene owed) |
| D24 | `S201_WHATS_LEFT_FOR_YOU.md` | ORPHAN | 25-Aug | the owner-facing three-item list; the allowlist evidence (18 Marg database files on the health surface) |
| **D25** | `S202_Marg_Transport_Resilience_D350_CONTRACT.md` | **ORPHAN — a SIGNED-CONTRACT-class document with no manifest row and no repo copy** | 26-Aug | D350 in full: §0 the outage anatomy, §1 the two transports, §2 verification at both ends, §3 the B2 states, §4 the reinstall kits, §5 the document corrections, §7 the build order, §8 the counter-argument the owner ruled on |
| D26 | `S202_PENDENCY_AUDIT.md` | ORPHAN | 25-Aug | O1–O22 · the builder queue · **N1–N13, the cross-store reconciliation** · the 19 open findings parsed by status |
| **D27** | `AUDIT_RUN_2026-08-24_slice1.md` | ORPHAN | 24-Aug | **the Auditor's ONLY run report — AF-1…AF-6 in full, and the four read-only commands, including AF-3's duplicate-advance scan** |
| D28 | `S195_medical_kit/SETUP_CHECK.bat` | manifest names the kit; **absent from repo** | 21-Aug | the one-click guard self-test *(not opened)* |
| D29 | `S195_medical_kit/marg_export_macro_v2.ahk` | manifest names the kit; **absent from repo** | 21-Aug | **the calibrated AutoHotkey export macro** *(not opened)* |
| D30 | `S195_medical_kit/marg_report.py` · `guard_and_send.py` · `SETUP_S195_MARG.md` · `GUARD_AND_SEND.bat` | in repo as `deploy_kits/S195_MARG/` | 21-Aug | the guard chain sources |
| D31 | `S203_MARG_MEDICAL_SYSTEM_MAP.md` | ORPHAN | **26-Aug 06:32** | the documentary map: machines, the chain in 12 stages, every known failure mode, 18 blind spots, D350 as scoped, §6 the backup position, §7 eleven conflicts |
| D32 | `S203_MARG_CODE_TRUTH_MAP.md` | ORPHAN | **26-Aug 06:33** | **what the code actually does**: the component table with line numbers, the schedules, every swallow site, the state-file table, §5 where a backup job could hook in, §6 nine code-vs-doc contradictions |
| D33 | `S203_KB_CENSUS_PHASE12.md` | ORPHAN | 26-Aug 04:35 | the 76-document one-store list; the 63-of-63 redundancy result; §2.2 the C:-tree finding; §3.1 the `knowledge_size` correction |
| D34 | `S203_PENDENCY_RECONCILIATION.md` | ORPHAN | 26-Aug 04:27 | C3–C8 worked to verdicts against live bytes; the complete AF-1…AF-6 table; the missing AF↔F bridge; five draft coverage-map rows; Thread 4 |
| D35 | `OWNER_TODO_LIVE.md` | **un-manifested BY DESIGN** (A10 of `END_OF_SESSION_PROMPT_v7`) | 26-Aug | ⭐0a the backup; ⭐1 the owner's stated build order; ⭐0b the 60-second check |

### Group A/B/C/D — the totals

| | count |
|---|---|
| **Documents inventoried** | **69** |
| Individually pinned in the manifest (Group A) | **8** |
| Covered only by a **wildcard** manifest row, no md5 (Group B) | **17** |
| Manifest-**named** but absent from the repo (D1, D2, D28, D29) + un-manifested by design (D35) | **5** |
| **ORPHANS — in no manifest row of any kind** | **39** (9 repo-side, 30 project-side) |

---

## 2 · WHAT EACH DOCUMENT UNIQUELY HOLDS

This is the section that protects against loss. `S203_KB_CENSUS_PHASE12` §2 already ran a token
search of 63 session records across all four canon stores; where it established a token as ABSENT
I cite that. Everything additional below was established in this pass.

### 2.1 The three current references (A1–A3) — what only they carry

**A1 `MARG_PIPELINE_REFERENCE_v1`:**
- The **upload contract**, which existed in no spec anywhere before it: the URL, the
  `X-Finance-Marg` header, the multipart field name, and every response code with its meaning —
  including *"`401` … **The token was wrong or absent** … This is what a stale token looks like;
  it does not say 'bad token'."*
- **§4, the only place all three token copies are listed together**: the systemd unit, medical
  `D:\SendToClinic\token.txt` (*"plain text by design (scoped, stage-only). Deliberately excluded
  from the manojz mirror (`/XF token.txt`)"*), and the manojz cache — *"Before S201 this was a
  hand-copy from 20-Aug and had been answering **401 for five days** while medical's own copy
  worked."*
- **§8a**, the Marg working-directory rule: *"Launched from anywhere else it refuses with 'Few
  important files not found in SYSTEM / Please RE-INSTALL software!' — which is badly misleading
  and would panic anyone reading it on a live pharmacy system."* And: *"Marg **does** accept a
  command-line argument and resolves it as a path (`/?` returns 'Invalid path or file name'), but
  there is no evidence it can be told to RUN A REPORT."*
- **§2's disagreement table** — the five things previously believed and not true.

**A2 `MARG_PIPELINE_MAINTENANCE_FLOW_v1`:**
- **The 60-second check** — the only three-file health test that needs no login.
- **§2's guest-access decision tree in full**, including the ruling recorded as a ruling:
  *"DO NOT re-enable insecure guest access to 'fix' this. Forums recommend it. It switches off a
  protection that exists to stop a machine on the network reading shares without proving who it is
  — on the PC holding patient records."*
- **`cmdkey /add:100.119.151.40 /user:MEDICAL\SET /pass`**, with the reason `MEDICAL\SET` and not
  `MEDICAL\user`: *"Windows refuses network logins for accounts without one, and `MEDICAL\user` has
  none."*
- **Credentials are stored PER WINDOWS USER**, with the `schtasks … findstr /i "Run As User"` check.
- §4's folder table with the **safe-to-empty column** — the only place that judgement is written.

**A3 `MARG_INGESTION_REFERENCE_v1`:**
- **§0, D313 stated as the one rule**: *"`finance_ingest.py` **contains no reference to `day_line`
  at all.** It cannot change a rupee of recorded revenue."*
- **The confidence-tier table** (0.99 / 0.95 / 0.60 / 0.50 / 0.99-WALK-IN) and the two consequences
  that "surprise everyone".
- **`marg_net_sql()`'s origin story with both figures**: 18-08-2026, true net **20,599**, second
  reader **23,879**, *"out by exactly 2 × 1,640."*
- **§8, what a parked row preserves**: the `raw_text` JSON column list, and *"The match key will be
  `bill_date + patient_name + phone_last4`. The phone is stored as **last 4 digits only** (F-86)."*

### 2.2 The single-store documents — quoted unique items

**D2 `S180_Marg_Folder_Recon` — the highest-value single loss risk in this inventory.**
It is the **entire Marg data-layer analysis** and exists in one place:
- The universal 16-byte prefix: `19 a3 95 78 <63|53> 44 f1 98 55 93 67 a1 be c0 2d da`.
- The proof of layout: *"`[16-byte Marg prefix][encrypted standard VFP DBF: 32-byte header + 32-byte
  field descriptors + 0x0D + fixed-length records]`"*, with the constant/varying offset map.
- **`codepage=437`** from `CONFIG.FPW`, quoted in full.
- **`marguser.csv` is a plain unencrypted DBF** — *"useful as a control when testing any parser."*
- The `.c18` table inventory with sizes and mtimes; `dis.c18` / `mdis.c18` / `subdis.c18` roles.
- The `pfdapi*.dll` build ladder (`pfapi443 → … → pfdapi584`).
- **The naming convention**: *"A `.ini` file paired with a same-named `.fpt` … is a **table, not a
  config file**. Do not assume `.ini` means text."*
- `serverlog.fpt` at **768 MB** — a live disk-hygiene item nothing else records.
- `S203_KB_CENSUS_PHASE12` §2 row 48: *"**Every one of those tokens is ABSENT from all four
  stores.** If this document is lost, the Marg data-layer analysis is lost with it."*

**D4 `S180_Marg_Sample_Findings` — the most consequential, and §4 of this document is about it.**
- Written **15-Aug-2026**: *"Also noted: `C:\Users\Public\MARG\17476\` is a Marg user folder
  (`17476`) not seen in the S180 folder survey, which found only `50018`, `61376` and `a` under
  `D:\MARGERP\users\`."*
- The two variants under one filename: *"Same menu, same filename, same folder — two different
  reports."* `AS ON` = 3 columns, no CASH; `FROM` = 9 columns.
- **The parsing trap**: *"the positive rows are **numeric** cells (type 2) but the two negative rows
  are **text** cells (type 1) carrying leading spaces … A parser that trusts the cell type … would
  **silently drop every credit note** and overstate the day."*
- The mode-field disproof from a second file: *"All **23 of 23** rows … carry the mode `.CASH`."*

**D7 `S180_Marg_Daily_Sale_Button_Settings` + D6 §2 + D9 §2 — the operational recipe.**
The exact `BILL WISE STATEMENT` screen values, field by field, and the Excel export screen
(`Header` · heading `No`/`1` · data start line `5` · ends `0` · `Formated`). Without this, the feed
cannot be regenerated after a Marg reinstall. **`S203_KB_CENSUS_PHASE12` records the delimiter
values as ABSENT from all four canon stores.**

**D8 `S180_Marg_Action_Register` — V7, the warning that must never be lost:**
> *"A month-to-date range **with item detail** was tested on 15-08-2026. It ran past 44 pages and
> **the export truncated at day 6 of 15 — silently.** The file opened, the rows were there, only the
> `GRAND TOTAL` was missing. … **One file per calendar month, each ending in its own `GRAND TOTAL`
> row.**"*
Also U11's measured ceiling — *"1 corroborated, 2 unique, 2 near, 0 ambiguous, 31 none — 3 of 36
safe to offer as a default"* — and the reframing it produces: *"it is not a defect to engineer
away, it is roughly the share of pharmacy business that is clinic patients at all."*
And U7's correction: `DISCOUNT` ₹3,634 over 84 bills vs `DR/CR` ₹199 over 16 — *"`DISCOUNT` is the
real channel by a factor of eighteen."*

**D9 `Marg_Report_Requirement_Sanjeevni` — the vendor-facing document.**
Licence **`LIC-14116710`**, E-Business ID **`39548`**, the R1–R6 requirements, **R4 (a DATE column
on every bill row — the fragility fix nothing else asks for)**, §6 the truncation defect written up
as a defect with evidence, §7 "what must not change", §8 the acceptance list. The manifest's §S182
block records only *"A vendor-facing requirement document was written."*

**D14 `S201_Marg_Pipeline_Rebuild_Plan`** — the A–M fault table with **`marg_router.py` line
numbers**, the four stranded-file hashes `633a54d3`, `fbea55de`, `1beac275`, `df20b4d2` (census: all
four ABSENT from all four stores), and the seven-failure-mode coverage table.

**D19 `S201_Parts2_3_4_Record`** — the per-type `end_marker` derivation table, and the live financial
control: *"`PURCHASE_BILLWISE` totals **476,393** and `PURCHASE_SUPPLIERWISE` totals **476,393** for
the same July period."* Census: both `476393` and `476,393` **ABSENT everywhere**.

**D18 `S201_Part1_xlsx_Dependency_Removed`** — *"**170 cells compared, 0 mismatches**"* against
openpyxl. This is the **only** proof that the stdlib `.xlsx` reader is correct, and the reader
replaced a deleted dependency in the live path.

**D22 `S201_A1FIX_Live_Pin_Record`** — the offline-harness recovery recipe naming which deploy kit
holds each live module by hash. `S201_PARKED_BACKLOG` §B cites it as the precondition for every
future kit's *measured* projection.

**D25 `S202_Marg_Transport_Resilience_D350_CONTRACT`** — a signed-contract-class document with no
row anywhere. Unique: *"a system with two paths and no switch has one path"*; §3's rule *"A fallback
nobody notices becomes the new normal … Working by the reserve route is a degraded state, and it
must read as one"*; §4 *"**Neither PC could be rebuilt today from anything written down.**"*; the
MagicDNS fix for the hardcoded `100.119.151.40`; §8's counter-argument, which is the thing the owner
actually ruled on.

**D27 `AUDIT_RUN_2026-08-24_slice1`** — AF-1…AF-6 in full **and the AF-3 duplicate-advance scan
command**. `OWNER_TODO_LIVE` ⭐0 item 7 requires that scan before the August close and **the command
exists in one document, in one store, with no manifest row.**

**D12 `S195_FINAL_PINS`** — `SEND_TO_CLINIC.bat` = **`e19a8a777ac22fe75a242f1eb9762185`**. Census:
ABSENT everywhere. **C1 independently re-measured the same value from the machine on 26-Aug** — so
this pin now has two sources for the first time, and both are outside the canon.

**C1 `S203_MEDICAL_PC_PINS` — the newest and, for the master, the most important orphan.**
- **The first medical-PC live pins ever taken**, seven files with path, bytes, md5 and mtime,
  measured on the machine by `md5_of()`.
- `Startup\MargAgent.cmd` **verbatim**, and the consequence: *"So the agent starts **at logon
  only**. There is no scheduled task for it. No logon, nothing runs — including … the offsite
  backup."*
- **Six things the mirror said that the machine denies**, because *"The manojz mirror never purges."*
  Among them: *"`GUARD_AND_SEND.bat`, `guard_and_send.py` and `marg_report.py`"* are **NOT on the
  medical PC.**
- *"**Scheduled tasks: six, all Google and OneDrive.** The S195 logon task 'Marg export watcher'
  does **not** exist."* and *"**Nothing in Task Scheduler or at startup runs a backup.** The
  automatic backup was never failing — it was never there."*
- `medical_agent.py` pin moved **`69e60d778ab61a8d50c79394e2951309` → `7b9a76f24abc5be369186507279cfaad`**
  (S201.11 → S203.3), zero-loss proven by reverse application, and the offsite leg's first run:
  *"`offsite: 38 file(s), 0.07 GB in F:\My Drive\Clinic Data Archive\MargBackups · 145 file(s) still
  to copy`. **The Marg backups have left the machine that holds them for the first time.**"*
- **The false-green rule**: *"the age that triggers the warning is measured on the copy that would
  actually be used in a disaster, never on the nearest file that looks like a backup."*
- `D:\SendToClinic\_old\COPY_MARG_DATA.bat` — *"records the fact that **Marg partitions its FoxPro
  tables by financial year in the file extension** (`.c18` = FY 2026-27)"* — corroborating D2.

**D32 `S203_MARG_CODE_TRUTH_MAP`** — the only document that reads the code rather than the record:
- **§3.1**: *"since S201 the pull produces no log at all"* — `PULL_HIDDEN.vbs:17` runs the batch
  hidden (`vbHide`), nothing redirects stdout, *"every line printed by `marg_watch.py`,
  `marg_router.py`, `marg_rescan.py`, `marg_gate.py send` and `pipeline_status.py` is written to a
  console nobody can see and is then destroyed."*
- **The most serious single defect in the Python**, `marg_router.py:349-354`: an unreadable
  spreadsheet returns before line 406, so *"The file is never copied to `_REFUSED\`, never gets a
  `.txt` sidecar, and **is never appended to `index.csv`** … for ever, invisibly."*
- **§3.3**: `END … -- ok` is stamped on a path requiring only a Python and a reachable share —
  *"Capture, routing, rescue, send and the picture can all have failed and the stamp still reads
  `ok`."* And `pipeline_status.py` reports that stamp verbatim to the server.
- **§4's state-file table** with *what happens if missing / if stale* for every state file, and the
  discovery of a **second, contradictory `MARG_PICTURE.txt`** at `MargPull\MARG_PICTURE.txt` — *"an
  orphan from an older build and … a trap for anyone opening the wrong one."*
- **§5, the backup hook analysis**: five candidate hooks ranked, the `BACKUP.txt` measurements
  (`D:\MARGERP\Data` 1075 files 0.9 GB; `serverbackup` 65 files 0.1 GB newest `2026-08-26
  00:01:14`), and **§5.4's honest caveat**: *"Nothing in this codebase can produce a *consistent*
  copy of `D:\MARGERP\Data` while Marg is running … Copying it live and calling it a backup would be
  the same class of error as the AF-1 false ACCEPTED."*
- **§7**: a second copy of the upload token at
  `D:\Downloads\margsync\_to_delete\S201_20260825\loose\finance marg token.txt` — *"a second copy to
  remember when it happens."*

---

## 3 · SUPERSESSION MAP

| Document | Status |
|---|---|
| A1 `MARG_PIPELINE_REFERENCE_v1` | **CURRENT** — with four stale passages: §1 "BOTH folders" (three), §3 the multipart filename, §3 "does NOT dedupe" (contradicted by the code), §9 "`xlsx_stdlib.py` is not yet on the medical PC" (it is). §5 and §8a are current and load-bearing. |
| A2 `MARG_PIPELINE_MAINTENANCE_FLOW_v1` | **CURRENT** — the strongest document in the set. §2a's Tailscale correction is authoritative. |
| A3 `MARG_INGESTION_REFERENCE_v1` | **CURRENT except §9 item 5**, which is **SUPERSEDED-BY-D348** and flagged as such in the manifest. |
| A4 `S195_Medical_Watcher_LIVE_Reference` | **SUPERSEDED-BY-A1**, by A1's own opening line — but the manifest row still says *"SOLE reference for the Marg capture pipeline."* **Two Tier-1 CURRENT rows contradict each other** (= `S202_PENDENCY_AUDIT` N3, still unresolved). **Retain**: the Store-stub discovery, the `MargWatcher.cmd` text, the PowerShell restart recipe, the `$args`-is-reserved note. |
| A5 `Clinic_Source_Data_Retention_Policy_v1` | **PARTLY SUPERSEDED** on three factual points (§4 below) and **still labelled a draft awaiting owner approval**. Its retention *rules* and §6 are current. |
| A6, A7 | CURRENT for their scope. |
| A8 (`f02cd8bd…`) | **SUPERSEDED-BY-A2** — retained lineage, correct. |
| B1 `S195_Marg_Report_Router_Design` | **PARTLY SUPERSEDED** — the router now runs on manojz, not "on the medical PC"; the archive path is `D:\Downloads\margsync\MargArchive`. **Its §1 evidence, §2.1 two-signal rule, §2.5 index columns, §4 versions-of-a-day design and §7 risks are CURRENT and carried nowhere else.** |
| B4 `S195_Marg_decrypt_partial_key` | **CURRENT and it supersedes B10.** Its own words: *"it supersedes the earlier optimistic 'crackable via crib-drag' note."* |
| B10 `S195_Marg_dbf_Encryption_Finding` | **SUPERSEDED-BY-B4** — but is still cited as live by B7 and sits in project knowledge with no supersession marker. |
| B6 `S195_Medical_PC_Macro_Guard_Runbook` | **PARTLY SUPERSEDED by C1** — C1 proves `GUARD_AND_SEND.bat`, `guard_and_send.py`, `marg_report.py`, `AutoHotkey64.exe`, the export macros and `xlrd\` are **not on the machine**. The **calibrated coordinates and the recorded flow remain the only record of how to drive Marg by macro.** |
| B8 `S195_Medical_PC_Close_Analysis` | **PARTLY SUPERSEDED** — the macro path is gone. **§"THE ONE REAL BLOCKER" is NOT superseded**: which login carries the UPI reclassification is *"a money question, not just a filename question"* and is unanswered. |
| C1 `S203_MEDICAL_PC_PINS` | **CURRENT — and it is the newest word on the medical PC.** It supersedes AF-1's "still armed" status and F-191(c)'s "configured and never once run" wording. **ORPHAN.** |
| C2 `S203_medical_census_S203.1_Pin_Record` | **CURRENT.** ORPHAN. |
| C3 `margpull/README_PULL.md` | **SUPERSEDED-BY-A1/A2 and factually wrong** — see §4. |
| C6 `SETUP_S195_MARG.md` | **SUPERSEDED-BY-B6** by B6's own statement; and further by C1 (the files it installs are not on the machine). |
| D1 `S179_Marg_Sale_Report_Analysis` | **CURRENT on the money rule and the identifier**; superseded on "make `marg_export` primary", which happened. **Manifest-named, repo-absent — F-107 OPEN.** |
| D2 `S180_Marg_Folder_Recon` | **CURRENT as the sole data-layer analysis**; its §2 SQL-sync speculation is corrected by D3 §2; its decryption recommendation is superseded by B4. **Manifest-named, repo-absent — F-107 OPEN.** |
| D3 `S180_Marg_Feed_Feasibility` | **CURRENT as evidence** (the `up_sale` slots, the scheduler proof); its route ranking is history. ORPHAN. |
| D4 `S180_Marg_Sample_Findings` | **CURRENT** — its C:-tree line is unretracted and correct. ORPHAN. |
| D5 `S180_Marg_Feed_Transport_Design` | **PARTLY SUPERSEDED.** `S201_PARKED_BACKLOG` §F and `S202_PENDENCY_AUDIT` N7 both say *"Retire it"*; `S203_KB_CENSUS_PHASE12` corrects that to **"Retire the ranking, not the document"** — §4A and the §4 invariants are carried nowhere else. |
| D6, D7, D8, D9 | **CURRENT as the vendor/operational recipe.** Nothing supersedes them; the vendor requests they contain have never been answered. |
| D14–D24 (the S201 family) | **CURRENT as evidence records.** D21's closing "min_confidence is an owner decision" is **SUPERSEDED-BY-D348**. D23's C5 is **SUPERSEDED** (fixed at S201; see D34) and its C8 is a **DUPLICATE of AF-1** (D34). |
| D25 `D350 CONTRACT` | **CURRENT and SCOPED by the owner** — §1 PARKED, §2/§3/§4/§5 live. **ORPHAN.** |
| D26 `S202_PENDENCY_AUDIT` | **CURRENT except N1 and N2**, both corrected by D34. **ORPHAN; its repo filing is OWED at the S203 close** (`OWNER_TODO_LIVE` HOUSEKEEPING). |
| D31 `S203_MARG_MEDICAL_SYSTEM_MAP` | **CURRENT except where C1 (2 hours later) measured the machine** — its AF-1 row, its §6 backup framing and its §4.4 "four-copy problem" are superseded by C1. |
| D32 `S203_MARG_CODE_TRUTH_MAP` | **CURRENT.** Its §1 method note already flags the mirror-never-purges limit that C1 then measured. |
| D34 `S203_PENDENCY_RECONCILIATION` | **CURRENT** on C3/C4/C6/C7 (verified against live-pinned bytes) and on the AF series. Its C5 verdict is **further superseded by C1** — the guard is not merely unable to run, it is not present. |

---

## 4 · CONTRADICTIONS BETWEEN DOCUMENTS

Both sides quoted; the newer named.

**1 · The C: output tree — a documented fact lost and re-discovered as new.**
> `S180_Marg_Sample_Findings` (project KB, **15-Aug-2026**): *"`C:\Users\Public\MARG\17476\` is a
> Marg user folder (`17476`) not seen in the S180 folder survey."*
>
> `S201_Medical_Pipeline_Completion_Audit` §4 (**25-Aug**) and `CANONICAL_MANIFEST.md` §S201:
> *"`C:\Users\Public\MARG\<id>\all\REPORT.PDF` <- **found 25-Aug, S201** … **Every document in this
> KB — including the two references rewritten earlier the same day — described only the first.**"*
>
> And `S203_MARG_MEDICAL_SYSTEM_MAP` §1.1 (**26-Aug 06:32**) repeats it: *"found 25-Aug-2026, S201"*.

**The newer claim is FALSE and is still in the canon.** The S180 document is right. First
identified by `S203_KB_CENSUS_PHASE12` §2.2; confirmed here. `61376` and `50018`, the other two
Marg user ids, appear nowhere in the Archive, Register, Fault Register or manifest to this day.

**2 · Tailscale: load-bearing or not.**
> **D347** (S201, in `KB_Register_v5_54_S202` decisions index and `CANONICAL_MANIFEST.md` §S201):
> *"Tailscale is a **read-only D:-only view and NOT load-bearing**."*
>
> `MARG_PIPELINE_REFERENCE_v1` §1 and `MARG_PIPELINE_MAINTENANCE_FLOW_v1` §2a (**S202, newer**):
> *"**AND IT IS LOAD-BEARING. D347 calls Tailscale 'NOT load-bearing'; that is WRONG and
> 26-Aug-2026 proved it** — the whole pull leg runs over this share, and when it closed the feed
> stopped for 8h40m."*

**The S202 references are newer and correct. The decision record is still wrong** — D350 §5 lists
the correction as owed *"in the decision record"* and `S203_MARG_MEDICAL_SYSTEM_MAP` §5.4 records
it as **NOT DONE**.

**3 · Which document is the reference for Marg capture.**
> `MARG_PIPELINE_REFERENCE_v1` opening: *"**Supersedes `S195_Medical_Watcher_LIVE_Reference.md`** as
> the authoritative description."*
>
> `CANONICAL_MANIFEST.md` Tier-1 row for `S195_Medical_Watcher_LIVE_Reference`: *"**SOLE reference
> for the Marg capture pipeline**."*

Both rows are Tier-1 CURRENT. The reference is newer. Raised as `S202_PENDENCY_AUDIT` **N3**;
verified still unresolved in the manifest this session.

**4 · `ingest.min_confidence`.**
> `MARG_INGESTION_REFERENCE_v1` §9 item 5: *"Whether 0.70 is right here is an **owner decision**,
> not a code one."* — repeated in `S201_PARKED_BACKLOG` A3 and `S201_Month_vs_Marg_Explained`.
>
> **D348** (S201, minted hours later the same session): closed by **MEASUREMENT** — 192 bills over
> seven days, every one 0.95+ or 0.50, *"a has-ID switch imported from OCR into a path with no OCR."*

**D348 is newer and wins.** The manifest flags the discrepancy (F-23: filed as delivered rather
than silently edited) and leaves the ruling to the owner. **Three documents still carry the retired
question.**

**5 · How many folders the watcher watches.**
> `MARG_PIPELINE_REFERENCE_v1` §1: *"captures .xls/.xlsx/.pdf from **BOTH** folders"*.
>
> `S203_MARG_CODE_TRUTH_MAP` §6.3, from the code: *"`medical_agent.py:51-52` `WATCH_DIRS = [r"D:\MARGERP\users",
> r"D:\MARG REPORTS", r"C:\Users\Public\MARG"]` — **three**, confirmed by the live heartbeat line."*

**Three is correct.** A reader of the canonical reference alone would not know a whole output tree
is being captured.

**6 · Does the server dedupe by content? — code vs doc, unresolved.**
> `marg_gate.py:31-32` (live on manojz): *"A false 'sent' is the expensive failure. **A repeat send
> is free — the server dedupes by content.**"*
>
> `MARG_PIPELINE_REFERENCE_v1` §3 and `MARG_INGESTION_REFERENCE_v1` §2: *"**The endpoint does NOT
> dedupe by content.** Sending the same bytes twice stages twice."*

The references are newer and were written against the live ingest path; `marg_gate`'s comment is
the older belief. **`S203_MARG_CODE_TRUTH_MAP` §6.1: *"If the reference is right, `marg_gate`'s
stated safety margin does not exist, and every path that loses `_outbox_state.json` stages 12
duplicate reports into the approvals queue. Resolve this against the server before anything else."***
Not established from the record which is true of the running server.

**7 · The multipart filename.**
> `MARG_PIPELINE_REFERENCE_v1` §3: *"Body: multipart/form-data, field name `"file"`, filename
> `"REPORT_1.XLS"`."*
>
> `S202_PICTURE/README_PICTURE.md` and `marg_gate.py:506` (**26-Aug, newer**): the upload now
> carries the **archived** filename. The doc's contract section is stale.

**8 · AF-1 — armed on a file that is not there.**
> `MARG_PIPELINE_REFERENCE_v1` L99, `CANONICAL_MANIFEST.md` §S201, Archive §S201 inside D347's own
> text, `HANDOFF_RUNBOOK` v135/v136, `OWNER_TODO_LIVE` ⭐3, `S201_PARKED_BACKLOG` C8,
> `S201_Medical_Pipeline_Completion_Audit` §8, `S203_MARG_MEDICAL_SYSTEM_MAP` §3: **AF-1 still
> ARMED** on `GUARD_AND_SEND.bat`.
>
> `S203_MEDICAL_PC_PINS` (**26-Aug 08:11, newest**): *"AF-1 is recorded against `GUARD_AND_SEND.bat`
> lines 119-123 … **That file is not on the machine.** AF-1 has been carried as 'still armed' in
> five places against a file that no longer exists. The fallback D347 preserves is
> `SEND_TO_CLINIC.bat`, which was read and is self-contained — it posts the report directly and
> never calls the guard or the parser. **The fallback works; the fault it is said to carry cannot
> fire.**"*

**The newest document read the machine. Seven places in the canon and the working docs are wrong.**

**9 · The Marg automatic backup — "configured and never ran" vs "never configured".**
> **F-191(c)** in `Fault_Action_Register_v2_41`, `OWNER_TODO_LIVE` ⭐0a and
> `S203_MARG_MEDICAL_SYSTEM_MAP` §6: *"automatic Marg backups were **configured** around
> 02-Oct-2025 and have never once run"*; *"**a facility that is configured but never confirmed
> producing output is not configured — it is decoration**."*
>
> `S203_MEDICAL_PC_PINS` (**newest, measured on the machine**): *"**Scheduled tasks: six, all Google
> and OneDrive** … **Nothing in Task Scheduler or at startup runs a backup. The automatic backup was
> never failing — it was never there.**"*

**The newest wins.** F-191(c)'s *finding* stands (there is no working automatic backup); its
*wording* is wrong, and the wording is what a future session would act on. Also contradicted:
`medical_census.py`'s own `BACKUP.txt` §7, quoted by `S203_MARG_CODE_TRUTH_MAP` §5.1: *"The backup
target is NOT ATTACHED … every automatic run has been writing to a drive letter that is not there"*
— which C2 records as **the S203.1 variable-shadowing fault, already fixed in S203.2.**

**10 · The medical guard — "cannot run" vs "is not there".**
> `S201_PARKED_BACKLOG` C5, `S202_PENDENCY_AUDIT` N1, `S203_MARG_MEDICAL_SYSTEM_MAP` §3: *"The
> medical guard cannot run at all — its bundled Python (3.11.9) has neither `xlrd` nor `openpyxl`."*
>
> `S203_PENDENCY_RECONCILIATION` Thread 1: *"C5 should be marked SUPERSEDED … the fix shipped in the
> session that raised it"* — `xlsx_stdlib.py` was installed on the medical PC on 25-Aug 19:28:17.
>
> `S203_MEDICAL_PC_PINS` (**newest**): `GUARD_AND_SEND.bat`, `guard_and_send.py` and
> `marg_report.py` are **not on the medical PC at all.**

**Three states, three documents, all live.** The newest is measured; the other two are inferred.

**11 · AF-5 / B4 — the "four-copy problem" that may be a three-copy problem.**
> `S203_MARG_MEDICAL_SYSTEM_MAP` §4.4 (26-Aug 06:32): *"**AF-5 is a FOUR-copy problem, not three** …
> Plus the medical PC's copy."*
>
> `S203_MEDICAL_PC_PINS` (26-Aug 08:11): `marg_report.py` is not among the 77 files in
> `D:\SendToClinic`.

**If the newer measurement is right, AF-5 and backlog item B4 ("one parser, not three") are
substantially MOOT** — there is no divergent PC parser to converge. This is unresolved and matters,
because B4 sits in two live backlogs.

**12 · `PULL_FROM_MEDICAL.bat` — record vs box.**
> `KB_Register_v5_54_S202` live-file table: **`3c5389d54241f234e94dc62b82d046e1`**.
>
> `S203_MARG_MEDICAL_SYSTEM_MAP` §1.2, measured on manojz 26-Aug: **`92f03999d0a14d00b7f552dbb4d44c05`**.

**The box wins** (D321(d), F-169 precedent). A live, unrecorded F-186 instance; **cause not
established** — a `PULL_FROM_MEDICAL.bat.bak_before_diag` sits beside it.

**13 · The repo `margpull/` mirror is stale, and one file is the *wrong version*.**
> Repo: `marg_router.py` `e5418830134f9c354fd40da4acf25d79` · `marg_watch.py`
> `25126388e6841ab38202811d2b940d6a` · `PULL_FROM_MEDICAL.bat` `15da9d27a0827bc3b806417e3d74c629`.
>
> Live manojz: `bbc50f91…` · `2076fe1d…` · `92f03999…`.
>
> `S201_Part1_Capture_And_Agent_Record` §5 names `25126388…` explicitly as *"the OLD watcher"* —
> `EXTS = (".xls", ".xlsx")`, **the version that cannot see PDFs.** Both repo copies are that version.

**14 · `xlsx_stdlib.py` — which machine.**
> `HANDOFF_RUNBOOK … v135` L55: *"replaced `openpyxl` **on the medical PC**"*.
> `KB_History_Archive_v1_49_S202` L7255: files it under *"**Manojz** tooling"*.
> `MARG_PIPELINE_REFERENCE_v1` §9: *"**not yet on the medical PC**"*.
> `S203_MEDICAL_PC_PINS`: on the medical PC, `bbe11a8953f66c27126c48e773cfbe35`.
> `S203_MARG_MEDICAL_SYSTEM_MAP` §1.2: also on manojz, same hash.

**It is on both. All three canonical statements are wrong in some part.** Raised as
`S203_PENDENCY_RECONCILIATION` recommendation 12.

**15 · AF-5 "unaccounted for".**
> `S202_PENDENCY_AUDIT` N2, quoted forward into `OWNER_TODO_LIVE` ⭐3: *"**AF-5 is unaccounted for in
> any document I can reach.**"*
>
> `S203_PENDENCY_RECONCILIATION` Thread 2 (newer): *"That is resolved. AF-5 is written out in full
> in `AUDIT_RUN_2026-08-24_slice1.md` … `S201_PARKED_BACKLOG` §E … **lists AF-3, AF-4 and AF-6 and
> silently skips AF-5.**"*

**16 · The retention policy vs the built system — three ways.**
> `Clinic_Source_Data_Retention_Policy_v1` §2: working copy at **`D:\MargArchive\`**.
> Live: `D:\Downloads\margsync\MargArchive\`.
>
> §3: *"Put `D:\MargArchive` **inside** a Google Drive for Desktop synced folder … no monthly upload
> job to remember, no extra script to maintain. **This is the single highest-value step.**"*
> Built instead: `robocopy /E` from the 10-minute pull — **which excludes `_spool` and `_outbox`**,
> as a synced folder would not have. So *"the pending-send queue has no offsite copy"* is a
> consequence of not doing what the policy recommended.
>
> §2: medical origin copy at `D:\SendToClinic\Sent\`. Live medical spool: `_captured\`. **Whether
> `Sent\` exists today is not established** — it is not in `S203_MEDICAL_PC_PINS`'s six-item
> denial list either way, and this pass did not read the medical PC.

**The pipeline references are newer. The policy is still labelled a draft and has never been
reconciled.**

**17 · `margpull/README_PULL.md` is wrong twice.**
> *"reads **three** folders on the medical PC"* — the batch reads **four** (`…\SendToClinic\_captured`
> was added). *"files it under `D:\MargArchive\<TYPE>\<YYYY-MM>\`"* and *"e.g. `D:\MargPull`"* — the
> live paths are `D:\Downloads\margsync\MargArchive` and `D:\Downloads\margsync\MargPull`.
> `S203_MARG_CODE_TRUTH_MAP` §6.5 adds the consequence: *"running `marg_router.py` by hand with no
> arguments on manojz writes to two folders that are not the live ones."*

**18 · `marg_router.py` is not a step in the pull.**
> `MARG_PIPELINE_REFERENCE_v1` §1 draws it as a numbered step in `PULL_FROM_MEDICAL.bat`.
> `S203_MARG_CODE_TRUTH_MAP` §1: *"It is called in-process by `marg_watch.route()`
> (`marg_watch.py:265-272`). **If it raises, it takes the watcher process down with it, and the
> batch does not notice.**"*

**19 · The pull's step order.**
> Reference §1 lists send before the mirrors and the offsite. The batch runs mirrors and the Drive
> offsite **first** (`:103`, `:114`, `:127`), then rescan, then send, then status
> (`S203_MARG_CODE_TRUTH_MAP` §6.4).

**20 · `S180_Marg_Feed_Transport_Design`'s route ranking is inverted against reality.**
> D5 §2: *"**3 — do not build**: Folder watcher on `users\*\report\REPORT_1.XLS`."*
> What was built: exactly that watcher, resident on the medical PC.
> `S201_PARKED_BACKLOG` §F / `S202_PENDENCY_AUDIT` N7: *"Retire it."*
> `S203_KB_CENSUS_PHASE12` row 51: *"**Retire the ranking, not the document.**"*

**21 · Marg decryption — "crackable" vs "thorough negative".**
> `S195_Marg_dbf_Encryption_Finding`: *"**CONFIRMED XOR** … So it is genuinely breakable."*
> `S195_Marg_decrypt_partial_key` (newer): *"**All 7 files share an identical 19-byte header prefix
> despite sizes 809 B … 13 MB.** Under simple XOR of a standard DBF the prefixes would differ …
> Identical prefixes falsify 'XOR-of-standard-DBF'. … **Remote decryption from the files alone is
> not tractable.**"*

**The negative is newer and correct.** The optimistic note carries no supersession marker in
project knowledge and is still cited as live by `S195_Medical_PC_Continuation_AHK`.

---

## 5 · THE CARRY-FORWARD LIST

Everything the master reference must contain so that every superseded document can be retired
without losing a fact. Grouped by what it is, not by which document it came from. **A document may
only be retired once every line naming it below is in the master.**

### 5.1 · The machines, exactly

1. **Medical PC** — hostname `MEDICAL`, Tailscale `100.119.151.40`, Windows 10 Pro. Accounts
   `MEDICAL\SET` (**has** a password) and `MEDICAL\user` (**none** — Windows refuses passwordless
   network logins). *(A1 §1, A2 §2)*
2. **The seven measured medical-PC pins** — the first ever taken — with paths, bytes, md5s and
   mtimes, and `token.txt` recorded as *present, 32 bytes, deliberately never hashed or mirrored*.
   *(C1)*
3. **`Startup\MargAgent.cmd` verbatim**, and the rule it implies: **the agent starts at LOGON only;
   there is no scheduled task; no logon means nothing runs, including the offsite backup.** *(C1)*
4. **The six things the manojz mirror shows that the machine denies** — the mirror is
   `robocopy /E` with **no `/PURGE`**, so it keeps every file ever deleted and **is not evidence of
   what is on the machine.** *(C1, D32 §1 method note, D32 §7)*
5. **Scheduled tasks on the medical PC: six, all Google and OneDrive.** The S195 logon task *"Marg
   export watcher"* does not exist. *(C1)*
6. **manojz** — the concentration: *"publisher + puller + mirror + offsite in one box"*; every live
   path; the drive-letter split (**Drive is `H:` on manojz and `F:` on medical**). *(D31 §1.2)*
7. **The Tailscale share is `DDrive` — D: only, read-only.** manojz cannot see `C:` and cannot
   write to medical (**ERROR 5 — F-168**). *(B5, A1 §1)*
8. **`PULL_FROM_MEDICAL.bat` hardcodes `100.119.151.40`; the durable fix is the MagicDNS name.**
   *(D25 §2)*
9. **The medical PC's `E:\` backup stick is not reachable from manojz at all** — which is why the
   backup survey had to run on the machine. *(C2)*

### 5.2 · The two Marg output trees, and the report itself

10. **Both trees, with the date each was first written down**: `D:\MARGERP\users\<uid>\report\REPORT_n.XLS`
    (S180) **and `C:\Users\Public\MARG\<id>\all\REPORT.PDF` — first recorded 15-Aug-2026 in
    `S180_Marg_Sample_Findings`, not 25-Aug.** Both are **fixed slots, overwritten on every export.**
    *(D4, D20 §4)*
11. **The three watch roots** — `D:\MARGERP\users` · `D:\MARG REPORTS` · `C:\Users\Public\MARG`.
    *(D32 §6.3)*
12. The Marg user ids seen: **`50018`, `61376`, `a`, `17476`.** *(D2, D4)*
13. **The two report variants under one filename** — `AS ON` (3 columns, no CASH, unusable for
    accounting) vs `FROM` (9 columns). **The adapter must identify the variant before parsing and
    refuse an unrecognised layout.** *(D4 §5)*
14. **The nine column headers, in order**, and the `DAY TOTAL :` / `GRAND TOTAL :` /
    `Total No. of Bills:` structure. *(D9 §3)*
15. **The exact Marg report-screen settings and the Excel delimiter-screen settings** — the recipe
    for regenerating the feed after any reinstall. *(D7, D6 §2, D9 §2)*
16. **`Report Type` must be `Detail`** — `Summary-1` loses the CASH column entirely. *(D7, D9)*
17. **V7 — the silent truncation**: month-to-date **with item detail** truncated at day 6 of 15,
    44 pages, no error, file opened normally. **One file per calendar month, each ending in its own
    `GRAND TOTAL`.** *(D8, D9 §6)*
18. **The money rule**: `cash = the CASH column` · `non-cash = NET − CASH`. **Never the `D.R.` mode
    field** — it agrees on 133 of 138 bills and the 5 it misses are split-tender. *(D1 §3, D6 §1)*
19. **The credit-note text-cell trap** — negatives arrive as text cells with leading spaces;
    reading only numeric cells silently drops every refund. *(D4)*
20. **The patient identifier**: `<phone> <NAME> <clinic id>` — **ID LAST**, and
    `split_clinic_id()` expects it first. 190 distinct phones, none ever paired with a different
    trailing number. **The field truncates at 33 characters.** *(D1 §4, D6 §1)*
21. **Attribution coverage is a ceiling, not a defect**: ~82% joinable, and the remainder is counter
    trade — *"Do not spend effort on cleverer name matching."* *(D8 U11)*
22. **`DISCOUNT` is the discount channel, not `DR/CR`** — ₹3,634 over 84 bills vs ₹199 over 16.
    *(D8 U7)*
23. **Marg version = `MARG ERP 9+`**, established from the export sheet name, not from file
    properties (`margwin.exe` has no VERSIONINFO). *(D3, D2 §7.4)*
24. **Launching Marg from a script requires `cd /d D:\MARGERP` first**; otherwise it says *"Please
    RE-INSTALL software!"* Marg accepts a path argument but **there is no evidence it can be told to
    run a report** — open with Marg support. *(A1 §8a, A2)*

### 5.3 · Marg's own data, and the backup position

25. **The data layer in full**: the 16-byte prefix bytes; the `[prefix][encrypted VFP DBF]` layout
    proof; **`codepage=437`**; `marguser.csv` as the unencrypted control; the `.c18` table inventory
    and roles (`dis` header · `mdis` lines · `subdis` sub-detail); the `pfdapi*` ladder; the
    `.ini`-means-table naming rule; `serverlog.fpt` at 768 MB. *(D2 — one store)*
26. **Marg partitions its FoxPro tables by financial year in the file extension** (`.c18` = FY
    2026-27) — independently recorded on the machine in `_old\COPY_MARG_DATA.bat`. *(D2, C1)*
27. **Decryption is RETIRED on a thorough negative**, with the falsifying evidence (identical
    19-byte prefixes across 809 B–13 MB files). The only remaining route is a runtime debugger dump.
    **Carry the negative, and mark the optimistic S195 note superseded.** *(B4 supersedes B10)*
28. **The backup position, corrected**: manual copies to `E:\` every 2–4 days; the old FY last
    backed up 17-July; **all ~308 MB on one stick attached to the machine it protects**; no restore
    ever tested — **and there is no configured automatic backup at all** (C1 supersedes F-191(c)'s
    "configured but never ran").
29. **`D:\MARGERP\Data` cannot be copied consistently while Marg runs** — open FoxPro tables,
    `margwin.exe` observed live. *"A backup that cannot be restored is not a backup."* **The only
    Marg artefact safely copyable unattended is `serverbackup\`** (Marg writes and closes it,
    newest `2026-08-26 00:01:14`), plus whatever `.mbk` a human makes on `E:`. *(D32 §5.3/§5.4, C1)*
30. **The offsite backup leg now exists** — `medical_agent.py` S203.3
    (`7b9a76f24abc5be369186507279cfaad`), first run *"38 file(s), 0.07 GB … 145 file(s) still to
    copy"*. **The Marg backups have left the machine for the first time.** *(C1)*
31. **The false-green rule**: *"the age that triggers the warning is measured on the copy that would
    actually be used in a disaster, never on the nearest file that looks like a backup."* *(C1)*
32. **The delivery channel exists; the execution channel does not.** Drive `ToMedical\_kit` →
    `medical_agent.install_kit()` is allowlisted, compile-checked and hash-verified. **Nothing on
    manojz can start a process on the medical PC.** *(C2, D32 §5.5)*

### 5.4 · The pipeline as it runs, and where it lies

33. **The 60-second check** — the three files, all on manojz, none needs a login, with what healthy
    looks like for each. *(A2 §1)*
34. **The real component table**: what starts each component, what it reads, what it writes, and
    **how that was established** — `marg_router.py` is called **in-process** by `marg_watch.route()`,
    not as a batch step; the medical watcher runs **without `--route`**. *(D32 §1)*
35. **Every interval, measured from the code**: pull 10 min (comment only — the trigger is not
    determinable from code) · heartbeat 300 s · watcher liveness 30 s · safety poll 5.0 s · settle
    60 ms · POST timeout 90 s, **no retry in the send** · coverage window 45 days. *(D32 §2)*
36. **THE PULL PRODUCES NO LOG.** `PULL_HIDDEN.vbs` runs the batch with `vbHide`; nothing redirects
    stdout; every diagnostic line from five programs is destroyed. `_NEEDS_ATTENTION.txt` is the one
    exception. *(D32 §3.1)*
37. **`END … -- ok` does not mean the work succeeded** — it requires only a Python and a reachable
    share. `pipeline_status.py` then reports that stamp verbatim to the server. *(D32 §3.3)*
38. **`marg_router.py:349-354`** — an unreadable spreadsheet returns before archiving, before the
    sidecar, **before `index.csv`**, and is re-refused every cycle for ever with no row anywhere
    saying so. *(D32 §3.2)*
39. **The state-file table** — for every state file: who writes it, who reads it, **what happens if
    it is missing and what if it is stale.** Including: losing `_outbox_state.json` re-sends
    everything; losing `_coverage_from.txt` re-arms the 56-false-alarm condition. *(D32 §4)*
40. **The second, contradictory `MARG_PICTURE.txt`** at `MargPull\MARG_PICTURE.txt` — an orphan from
    an older build, and a trap. *(D32 §4)*
41. **The signature schema and the `--learn` procedure**, with the rule *"Derive a marker from a
    real sample; **never guess one**"*, and the per-type `end_marker` derivation table with the
    evidence (16 pass, 0 refused, then all 26 re-verified). **`SALE_BILLWISE/SUMMARY1` deliberately
    has no marker and says so.** *(A1 §7, D19)*
42. **`data_from`/`data_to` vs `date_from`/`date_to`** — what the rows carry vs what the title
    claims, **the DATA range wins**; `covered_days()` / `span_key()`; a range covers every day in it.
    *(D16, D19)*
43. **Adding a signature now rescues what it should have rescued** —
    `marg_rescan.py --if-signatures-changed`, and the reason it must import the router rather than
    re-implement it. *(D16, D19)*
44. **Never hand-copy a report into a type folder** — that is how the index came to disagree with
    the disk. *(A2 §3, D14 §0)*
45. **The upload contract in full**, every response code with its meaning, and the two rules:
    **the endpoint does not dedupe by content**, and **never decide success from a response file a
    failed request leaves untouched (AF-1)**. **Flag the unresolved `marg_gate.py:31-32`
    contradiction until the server settles it.** *(A1 §3, A3 §2, D32 §6.1)*
46. **The three token copies**, the `/XF token.txt` exclusion, the 401-reads-as-`not_signed_in`
    signature, **the token-comparison diagnostic that never exposes the secret**, and **the fourth
    copy** at `_to_delete\S201_20260825\loose\finance marg token.txt`. *(A1 §4, B3, D32 §7)*
47. **The `_spool` is the dedupe memory** — emptying it re-imports everything, and it has **no
    offsite copy** because `robocopy` excludes `_spool` and `_outbox`. *(A1 §6, A2 §4)*
48. **The mirror never purges** — 363 stale `marg_watch.py.before_*` files on manojz for files
    already deleted on the medical PC. *(D32 §7)*

### 5.5 · Ingestion — the server half

49. **D313 as the one rule**: money is `day_line`, attribution is `sale_item`, and `finance_ingest`
    cannot touch a rupee. **Therefore a books-vs-Marg difference is never missing money.** *(A3 §0)*
50. **The confidence-tier table**, and **F-183's two latent faults**: the `0.60` tier parks a bill
    that HAS a clinic ID (backwards), and single-digit clinic IDs would not match. *(A3 §4, D31 §3)*
51. **`marg_net_sql()` and its origin** — 18-Aug, 20,599 vs 23,879, *"never write a second way of
    summing Marg rows."* *(A3 §6)*
52. **The month-vs-Marg check compares incomparable things** and the day-by-day proof to the rupee
    (49 lines, ₹51,868), **plus bill `A003039` (₹190), the single bill that disproved the wrong
    theory.** *(D21, A3 §7)*
53. **Apply supersedes and DELETES** — *"a re-apply wipes that day's review queue"* (C6), and the
    owner's 12-June ruling: re-applying an old day *"would have DELETED 26 attributed rows and 26
    RESOLVED review rows on a closed month, to arrive at the same number."* *(D23 C6, D31 §2)*
54. **`rows_read != expect` → rollback; a half-loaded day is never left behind.** *(A3 §3)*
55. **The Docterz match key `bill_date + patient_name + phone_last4`, last-4 only (F-86)** — and
    that resolutions need somewhere that survives a re-import. *(A3 §8)*
56. **The sale-return correlation design** measured on 9 real credit notes (5 of 9 compliant, 7 of 9
    correlated, one conclusive at 6 of 6 items) and the flag rule: *"not 'a return happened' — large,
    and still unmatched after the database has been searched."* *(D5 §4A)*
57. **The four design invariants** — Darpan explains but cannot clear (D272 kin) · flag few things,
    trend everything · two attribution thresholds · **the missing-day alarm must be SEEN to fire.**
    *(D6 §4)*

### 5.6 · Faults, their evidence, and their true status

58. **F-179** with its evidence: the timeline, the two file names, `marg_router.py` lines 314–318
    verbatim, and *"the word `queued` is a lie"*. **RULE: assert the DRAIN, not the enqueue.** *(D15)*
59. **The watcher death of 10:37 and how it was found** — by accident, 4 hours later; *"That day's
    report survived on redundancy, not on design."* *(D17)*
60. **The 343-attempt runaway** and its three fixes (prove writable before backing up · name the
    backup by source md5 · 3 tries then stop). *(D20 §5)*
61. **The A–M fault table with source line numbers**, and the four stranded-file hashes. *(D14)*
62. **The seven-failure-mode coverage table**, and which of them B2 closed. *(D14, D31 §4.1)*
63. **AF-1's mechanism in full** — and **C1's correction that the file it names is not on the
    machine.** Carry both, with the newer marked newer. *(D27, A1 §3, C1)*
64. **AF-2 born dead**, and the deeper lesson: *"the push-path test stub **fabricated the reader's
    key shape** — the fixture mirrored the reader, not the writer."* *(D22)*
65. **AF-3's duplicate-advance scan command** — *the instruction survives in two backlogs and the
    means of carrying it out exists in one orphan document.* *(D27)*
66. **AF-4, AF-5, AF-6 in full**, and **the AF↔F bridge that does not exist**: `AUDITOR_SEED_v1`
    still instructs the Auditor to continue the F-series while S196 overrode that to AF-#, *"and no
    sentence replaced it"* — an F-23 situation for the owner's ruling. *(D27, D34 Thread 2)*
67. **C3/C4/C6/C7 worked to verdicts against live-pinned bytes** (line 516, line 416,
    `split_clinic_id` in both live modules, 20 BLIND rows of which **none names a medical-PC file**),
    **C5 corrected as fixed**, **C8 corrected as a duplicate of AF-1**. *(D34 Thread 1)*
68. **F-191(a)** — `pipeline_status.py` wired below the pull's early exit, *"a monitor that could
    report success and nothing else"*; and the unguarded `pause` found beside it. *(C5)*
69. **F-192(b)** — the 56 phantom missing days, and the two-step fix ending in a **declared**
    coverage start. *"A false alarm is worse than no alarm."* *(C4)*
70. **The `.xlsx` time bomb and how it was defused by DELETING the dependency**, with the proof
    (170 cells vs openpyxl, 0 mismatches) and the reasoning: *"A dependency that must be installed on
    every machine is a dependency that will be missing on one of them."* *(D18)*
71. **The 401 crisis** — the token was never in the unit file; *"a restart is not a no-op when a
    service's environment has drifted from its unit file."* *(B3)*
72. **F-168 / ERROR 5** with the verbatim robocopy output. *(B5)*
73. **The REPORT_1 vs REPORT_2 / which-login question, unanswered**: the two logins carry different
    versions of the truth (19-Aug ₹44,120: 50018 all-cash vs 61376 cash 18,790 / non-cash 25,330).
    *"This is a money question, not just a filename question."* *(B8, B11)*
74. **The `pyflakes` protocol proposal** — `py_compile` proves a file parses and cannot see an
    undefined name; proven both ways. And **"an anchor that is not unique is not an anchor."**
    *(C2)*
75. **"A survey that only exists if every part of it succeeds is not a survey"** — write as you go;
    a failing section reports itself in place. *(C2)*
76. **"A verdict may only read variables it can name and nothing else has touched."** *(C2)*

### 5.7 · Scope, blind spots and open decisions the master must carry

77. **D347 in full, WITH the Tailscale clause marked corrected**, and the correction still owed in
    the decision record. *(§4 item 2)*
78. **D348 in full**, and the three documents that still carry the retired min_confidence question.
    *(§4 item 4)*
79. **D350 as the owner scoped it** — §2/§3/§4/§5 live, **§1 the Drive fallback PARKED**, and his
    reasoning recorded as better than the contract's own proposal, with the named risk: *"a standby
    route never exercised will not work when needed."* *(D25, D31 §5)*
80. **The reinstall kits (§4), item by item, with what exists and what does not** — including **five
    live PC-side files with no copy in the repository**: `marg_rescan.py`, `xlsx_stdlib.py`,
    `medical_inventory.py`, `medical_census.py`, `medical_agent.py`. *(D25 §4, D31 §5.3, D34 Thread 1)*
81. **The repo `margpull/` mirror is stale and one file is the PDF-blind old watcher.** *(§4 item 13)*
82. **`.gitattributes` / `core.autocrlf` — F-190**: the reinstall kits must be tested on a machine
    with git's Windows defaults, not on manojz. *(D31 §5.3)*
83. **The Lab PC / Labmate**: nothing documented; survey first; **S181's warning that the revenue
    arithmetic is INVERTED between medical and clinic/lab — "the single most dangerous copy-paste in
    the build"**; attach a source as a **profile + signatures, never a copied script**; and **ask
    where Labmate writes — Marg turned out to have two output trees on two drives.** *(A1 §8, D14
    Part 8, D23 D2)*
84. **The vendor asks that have never been answered** — the two saved buttons, auto-generation into
    `report\auto\`, two separate output files, the DATE column (R4), auto-email, `up_sale` /
    `up_saleinfo` (E.BUSID `39548`), the operator column, the export page/line cap, and the
    month-by-month history request. Licence `LIC-14116710`. *(D6 §2, D8, D9)*
85. **The retention policy's three factual corrections**, and that it is **still a draft awaiting
    owner approval** with the CA question open. *(§4 item 16, A5)*
86. **The eighteen remaining blind spots**, ordered, with what closed and what did not. *(D31 §4.2)*
87. **The concentration risk stated plainly**: *"manojz is still publisher+puller+mirror+offsite in
    one box"* — audit slice 4, never run. *(D27, D34 Thread 3 Row 4)*
88. **`SYSTEM_DOC_COVERAGE_MAP_S147` has no row for the medical PC, manojz, Marg capture,
    clinic-finance or the Lab PC** — and the five draft rows already written for it. *(D26 N6, D34
    Thread 3)*

### 5.8 · Filing actions the master's adoption should trigger

*(Recommendations only. Minting and filing are the owner's, at a close.)*

89. **File to the repo and pin — the F-107 condition standing open right now** (four of these are
    **named in the manifest** and the repository does not have them): `S179_Marg_Sale_Report_Analysis`
    · `S180_Marg_Folder_Recon` · `S195_medical_kit/SETUP_CHECK.bat` ·
    `S195_medical_kit/marg_export_macro_v2.ahk`.
90. **File and pin the two S203 orphans that already live in the repo but in no manifest row**:
    `deploy_kits/S203_CENSUS_BACKUP/S203_MEDICAL_PC_PINS.md` (`976a6f0ccc22318a603d055f81541f71`) and
    `S203_medical_census_S203.1_Pin_Record.md` (`58c232fb43e4c49fadd1c8097c3da5f8`). **The first is
    the only record of the medical PC's true state and it is unpinned.**
91. **File and pin `S202_Marg_Transport_Resilience_D350_CONTRACT`** — every comparable signed
    contract (D329, D330, D331, D332, D335, D336, D337) is a pinned Tier-1 row; this one is in one
    store with no row. Already OWED at the S203 close per `OWNER_TODO_LIVE`.
92. **File `AUDIT_RUN_2026-08-24_slice1`** — it holds the AF-3 command that two live backlogs
    instruct the owner to run before the August close.
93. **File the 20 remaining project-only Marg/medical session records** (the S180 family, the S201
    family, `Marg_Report_Requirement_Sanjeevni`, `S195_FINAL_PINS`, `S195_Close_Summary_FINAL`,
    `S202_PENDENCY_AUDIT`, the S203 family) — **or fold their unique content into the master before
    anything is retired.** `S203_KB_CENSUS_PHASE12` tested 63 session records and found **zero
    redundant**.
94. **Strike the *"SOLE reference"* label** on `S195_Medical_Watcher_LIVE_Reference`'s manifest row
    when the master lands (= N3).
95. **Correct A1 §1 (three watch roots), §3 (the multipart filename), §9 (`xlsx_stdlib.py` is
    installed), and add `C:\Users\Public\MARG\` to the reference** — the manifest's own row already
    claims the reference covers *"the two Marg output trees (D: and **C:**)"* and **the string
    appears in it zero times.**
96. **Correct D347's Tailscale clause in the KB Register decisions index** — the one place a future
    session reads the ruling from.
97. **Mark superseded, do not delete**: `S195_Marg_dbf_Encryption_Finding` (→ B4) ·
    `SETUP_S195_MARG.md` (→ B6) · `margpull/README_PULL.md` (→ A1/A2) ·
    `S180_Marg_Feed_Transport_Design`'s §2 route ranking only.
98. **Resolve `marg_gate.py:31-32` against the running server** before anything else in the code
    list — it is the only contradiction here where being wrong stages duplicates into the approvals
    queue.
99. **Search Google Drive** (`ToMedical\`, `FromMedical\`, the offsite `MargArchive`) before any
    document in Group D is retired. This pass could not reach it; the mount failed.

---

*S203 · read-only · every md5 quoted was computed by `md5sum` in this session or transcribed from
the file that carries it · absences stated with what was searched · no patient identifiers
reproduced; no token value read or printed · nothing created, moved, modified or deleted in any
store, and no git command was run.*
