# Clinic Master KB / Systems Register — v1.68 (CONSOLIDATED)

**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **v1.68 is a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything in v1.67 plus **§S142 (Session 142, FULL EOS — one new VPS file, one emergency system fix): the D236 DIGEST LAYER BUILT AND LIVE (`daily_digest.py` v1.2.1-S142, read-only by construction, 72/72 selftest; 11:00 pulse + 21:30 digest crons armed; both emails proven on the owner's phone). 🔴 F-41 FOUND, FIXED, CANARY-PROVEN the same morning: crond had run on UTC since 16 Jun — every cron ever armed fired 5h30 late; the 08:45 write-probe had NEVER fired. Owner-directed same-day v1.2: every unjudged call now carries an automatic reason; the lost-conversation detector's FIRST run caught 🔴 F-42 (connected incoming calls with talk but no recording — open). D237 stratified 41-call referee set built and delivered; Verdict_Review redrawn to 8,845 rows / 378 cards; refereeing waits (owner: Option B) for the S143 verdict_review enhancement. Flag Investigator designed and approved (D239). Decisions D238–D239.**\n\n> *(previous consolidation note)* **v1.67 is a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything in v1.66 plus **§S141 (Session 141, FULL EOS — one VPS file changed): F-39 found and fixed the same night — Sheets append-detection was writing every v2 verdict onto row 61, erasing its predecessor; ~502 wasted AI calls; `call_verdict.py` v2.1 (explicit-row writes) installed, 5/5 supervised trial, full re-judge to 550 rows, cron re-armed. F-40 raised (stale version banners). First real 550-call analysis delivered. Digest layer designed (D236) and calibration path locked (D237). Decisions D235–D237.**\n\n> *(previous consolidation note)* **v1.66 is a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything in v1.65 plus **§S140 (Session 140, FULL EOS — one Apps Script deploy, five VPS installs, all live-verified): the owner-directed close-ALL-call-lifecycle-gaps day, three passes in one Sunday. Pass 1: K-2 incoming one-tap LIVE (Dashboard v18.28f + Callconsole v1.7) — unknown connected callers become NEW LEADS with a 7-button set and a 🌱 New-leads band (3-day TTL, D226). Pass 2: the VPS verdict layer v2 LIVE (`call_verdict.py` v2 + `verdict_review.py` v2) — K-era claim equivalence, D153 RETIRED (F-18 closed), the 03:40 nightly cron armed, 480 historical calls judged with 0 failures. Pass 3: the D200 at-hangup pipeline LIVE (`call_hook_capture.py` v3.1 kick-queue + `call-pipeline.service` worker) and the G-6/F-38 daily write-probe armed. The entire S139 gap register G-1–G-6 is CLOSED. Decisions D225–D234.**
>
> **v1.65 is a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything in v1.64 plus **§S139 (Session 139, FULL EOS — two Apps Script deploys, one VPS install, one portal hotfix): the F-10 cure DEPLOYED (Dashboard v18.26, opaque data refs, audit F-10 CLOSED) and the ENTIRE §K.6 K-1 one-tap staff UI BUILT AND LIVE in the same Sunday session (Dashboard v18.27 + Callconsole v1.6 + relay v3 `/wa-send/template`), the owner-requested call-lifecycle audit with its gap register (G-1…G-6; K-2 → A5 → Pass 5 → Pass 6 closure order), the first Block-C quota baseline (453 builds/day), and the attendance-https portal hotfix. Decisions D219–D224.**
>
> **v1.64 is a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything in v1.63 plus **§S138 (Session 138, FULL EOS — VPS code changed): the F-19 scope change EXECUTED — `call_hook_capture.py` v3.0→v3.0.1 now captures INCOMING calls into `Call_Durations` (owner decisions D217 row key, D218 phone10 column), the 13-column grid-limit 400 caught on first restart and fixed same session, and a 219-row idempotent backfill (`backfill_call_durations.py`) that recovered nine days of incoming history — all independently verified against the live tab. Decisions D217–D218; findings F-37, F-38 raised. §K Phase K-2 is UNBLOCKED.**
>
> **v1.63 is a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything in v1.62 plus **§S137 (Session 137, EOS-light — decisions and design only, NO code touched): decisions D213–D216 minted and live-verified, the §K.6 one-tap staff-UI design locked with zero open inputs (canonical home: Console Spec v2.2), the full 14-template WABA panel inventory pulled live by API, the WABA token's `.env` name recorded (`MYOP_AUTH_TOKEN`), and Umbrella v1.48 recovered from GitHub after being found absent from project knowledge.**
>
> **v1.61 is a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything in v1.60 plus **§S135 (Session 135): the shared-mobile identity incident F-34 found and CLOSED same day (D208, three files), the Session-35 review-SEND-BACK loop CLOSED (F-35/D209), ingest identity hardening + ledger cleanup (D210), and the clinical-data-report migration design. Decisions D208–D210.**
>
> **v1.48 is a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything in v1.47 plus **§124 (Session 124): the Verdict Analysis Layer BUILT (`verdict_review.py`), the duration-gate FAIL-OPEN (`Dashboard.html` v18.19), the recurrence of the call-webhook 403 outage, and two corrections to the Session-123 record. Decisions D155–D160.**
>
> **v1.47 was the prior fully-consolidated master**
>
> **v1.46 is a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything below plus **§122 (Session 122): the Stage-3 AI judge build (`call_verdict.py`), the Drive-OAuth-token incident + permanent fix, and decision D149**.
>
> **v1.44 is a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything below plus **§102 (Session 102): the staff call-sheet de-duplication build, decision D146**.
>
> **v1.42 was the prior FULLY CONSOLIDATED, self-contained master.** It folds the entire delta chain
> into one document with a single decisions index and one changelog. No earlier version file
> is needed to read this one. **KB wins on any conflict.**
>
> **What this consolidation contains, and where each piece came from:**
> - **v1.38 base** (self-contained master; itself carried v1.36's collapse of
>   v1.33 → v1.34 → v1.35 + Session 67, and folded in the **v1.37 delta = Session 73** build
>   work). §12 STATE, §65, §66, §67, §73, Surveillance Register, decisions **D121–D134**.
> - **v1.39 delta (Session 75)** — §75 PC-local write-path (`clinic_writer.py`), **D135–D138**.
> - **v1.40 delta (Session 93)** — §93 PC-local Vitals & Plan front-end (Track 1 Step 5),
>   **D139–D142**.
> - **v1.41 delta (Session 94)** — §94 call-webhook 403 outage fix + doctor-console
>   `isGenericAgent_` fix, **D143–D145**.
>
> **Note on v1.37:** no standalone `v1.37` file exists (searched Drive backup + local code
> keep; not found). Its content is not lost — it was folded into the **v1.38 base** at the
> time (per v1.38's own header: "folds in the v1.37 delta = Session 73 build work"), and is
> present in this document within §73. Nothing is reconstructed or invented here.
>
> **Consolidation method:** verbatim fold-in only. Section bodies (§12, §65–§67, §73, §75,
> §93, §94) are reproduced exactly as written in their source files; the ONLY new material is
> this header, the single unified Decisions Index, the merged Surveillance forward-notes, and
> the changelog. No wording, decision, number, hash, or fact was altered.
>
> **§12 STATE currency:** §12 below is reproduced verbatim from the v1.38 base (its own
> "unchanged since Session 64" framing is preserved for the historical record). The CURRENT
> live picture is governed by the later sections and their state-change notes — most recently
> **§94.6** (S94 close): the call-duration gate is LIVE and healthy again after the 403 outage
> was fixed; `OutcomeLog.gs` was updated (D143) and redeployed as a New version (dashboard URL
> unchanged); everything else in §12 still stands (WABA sends still BLOCKED vendor-side D120;
> `wa_approve` still nohup not systemd; key rotations still overdue). Track 1: Step 5 COMPLETE,
> Step 7 not started.

---

## §12 STATE — what is live right now (UNCHANGED since Session 64 close)

**Nothing in §12 changed at Sessions 65–67 (no live code touched in any of them).** The live picture
from v1.32 stands verbatim:

- **WABA FOLLOW-UP BRIDGE — BUILT + LIVE on VPS, but SENDS BLOCKED vendor-side (D116–D120).**
  Three components in `/root/wa/`: `plan_followups_from_xlsx.py` (dry-run planner, LIVE),
  `wa_approve.py` (approve/deselect page, 127.0.0.1:8101 via OLS `/wa-approve`, **hand-run via
  nohup — NOT yet a systemd service**), `waba.py` (template sender, copied to VPS, unchanged).
  Safety = 2 open-gates (secret key in URL + TEST-mode default) + 2 live-send gates (LIVE toggle +
  daily-cap). Config in `/root/wa/wa_approve.env`; send creds in `/root/wa/.env`.
- **🔴 WABA SENDS BLOCKED — MyOperator-side AWS API Gateway fault (D120).** Send + templates-LIST
  GET both return HTTP 500 `x-amzn-ErrorType: AuthorizerConfigurationException`. Vendor-side, not
  ours (500 not 401/403; no-payload GET fails identically). Lokesh must fix the publicapi gateway
  authorizer. Fault code `WABA_SEND_AUTHORIZER_500` (ESCALATE-ONLY, vendor). AWS request-id on file:
  `eb82db53-47b2-48f1-b744-027a754be56c`.
- **Everything else from v1.31 §12 stands verbatim** — daily health report LIVE 08:00 IST;
  timer-freshness checker built+tested but STILL NOT armed; S61 watchman LIVE; stale-list sentinel
  LIVE; follow-up push VPS-native; attendance live; Dashboard v18.18; caller-ID SOP D93; duration
  gate D82; key rotation 🔴 overdue; AKEY_14; PHI base swap deferred.

**Known open (live-systems backlog, Track 2) — unchanged, restated:**
1. **🔴 WABA authorizer fault (D120)** — Lokesh; blocks ALL WABA sends; re-fire TEST when it clears.
2. **Make `wa_approve` a systemd service** — nohup dies on SSH close.
3. **Rotate `WA_APPROVE_KEY`** + service-account key (Tier A1) + AKEY_14.
4. **Upstream watcher dup bug** (clinic-PC) — 6 true-identical rows; diagnostic `inspect_dupes.py`.
5. Arm timer-freshness checker; maintenance jobs; "Agent shows as Staff" close; GitHub commit
   (S59–S64); data pass; P1–P10.
6. `call_transcription.py` GitHub commit; Stage-3 AI verdict layer; clinic_health_report.py UTC→IST
   fix; Orthopedic_Clinic_Rehab_Nutrition_v12.xlsm audit fixes (My_Plan!B31 #NAME? etc.).

---

## §12A CURRENT LIVE STATE — call-hook family (Sessions 125–127)

**`§12` above is a historical artefact.** Its own heading says *"UNCHANGED since Session 64 close"* and it has been true to that. It is preserved verbatim, not rewritten. Where §12 and §12A disagree about the call-hook family, **§12A wins.** (D175.)

**`call-hook.service` — LIVE.** `call_hook_capture.py` **v2 (dual-key)**. File on disk replaced 08-Jul **21:55**: 31,490 bytes, 701 lines, md5 `beafccafbf7e81aa5f2736be939b2bbb`, 43/43 selftest on the installed file. **Loaded into a running worker for the first time at 08-Jul 23:38:00** (rotation step 1) — until then the worker executed the pre-21:55 bytes, imported at 14:49:13. gunicorn `-w 1`, no `--preload`, `127.0.0.1:8098`. Gate accepts `CALLHOOK_SECRET` **or** `CALLHOOK_SECRET_PREV`, constant-time; refusals written to `call_hook_rejects/YYYY-MM-DD.jsonl` **before** they are refused. Rollback: two byte-identical v2 copies, `call_hook_capture.py.bak_20260708_144241` and `.LIVE_v2_s126_20260708_212453` (both 30,749 bytes). v1 is not on the box; it lives in GitHub and the cold kit.

**`CALLHOOK_SECRET` rotation — STEPS 1 AND 2 COMPLETE. STEPS 3 AND 4 PARKED (S128, D176).**
> **PARKED means: not abandoned, not pending, and not to be raised at session start.** The dual-key gate (D162) permits the panel and the VPS to disagree indefinitely. Nothing degrades with time. See §S128 for the stated bound of the exposure. Resume only when the owner asks.
- **Step 1** ✅ 08-Jul 23:38:00. `CALLHOOK_SECRET_PREV` set equal to `CALLHOOK_SECRET`. Startup: `previous=SAME AS CURRENT (rotation not started; harmless)`. Verified across nine hours and 48 real calls, zero refusals, zero PREV-key acceptances (both variables identical, so `CALLHOOK_SECRET` matched first every time).
- **Step 2** ✅ 09-Jul 09:05:58. New key generated **on the VPS** (`openssl rand -hex 12` → 24 hex chars, no `@`, nothing that percent-encodes — the D165 encoding trap removed at source). Installed via `rotate_callhook.sh install`. Startup: `current=key_ea20dd  previous=key_db8972  -> ROTATION IN PROGRESS`. **Verified on live traffic at 09:35:** 64 calls accepted today, **12 on the previous key in 30 minutes**, `refused today: none`. This is the first production exercise of the previous-key branch (D174).
- **Step 3** ⏸️ **PARKED 09-Jul-2026 (S128).** The MyOperator panel still sends the old key `key_db8972`, and that is a stable, safe, indefinite state. When resumed it requires a clinic day with hours in front of it: update the panel, place one real call, confirm `on PREVIOUS key/30min` falls to `0` and `refused today: none` — **then re-check ≥1 hour later on the same clinic day.** An incident is closed by a successful re-test, not a successful test. **When resumed, a THIRD key must be generated** — `key_ea20dd` was exposed in a chat transcript at S128 open (D176) and must not be pasted into the panel.
- **Step 4** ⏸️ **PARKED, AND BLOCKED ON STEP 3 REGARDLESS.** Clearing `CALLHOOK_SECRET_PREV` while the panel holds the old key reconstructs the 06-Jul outage by hand. The command is deliberately absent from `rotate_callhook.sh`, from this KB, and from the runbook. See **D173**.

**BOTH keys are now live and both are exposed in chat transcripts.** `key_db8972` (12-char, `@`) since S94–S125; `key_ea20dd` (24-char hex) since S128 open, when Runbook v61 §5 instructed the owner to `grep` it to his terminal (**D176**). Neither dies before step 4. **The exposure is bounded, not urgent** — see §S128 for what the secret can and cannot do. Steps 1 and 2 bought exactly this: an exposure that is *unhurried* rather than *unfixable without an outage*.

**`rotate_callhook.sh` — NEW, on the VPS at `/root/wa/rotate_callhook.sh`.** Four subcommands: `status` (read-only), `stage` (builds `.env.candidate_s127`, eleven guards, self-deletes on any failure, never touches `.env`), `install` (re-runs guards, `cmp`-validates the rollback point *at the instant before* the atomic `mv`, swaps, clears bytecode, restarts, reads back the startup line), `rollback`. Keys appear only as `key_<md5[:6]>` labels. Built because a human reading forty exit codes is the bottleneck and the hazard. See **D171**.

**Known cosmetic defect in `rotate_callhook.sh` v1.0:** `status` looks back only two minutes for the startup line, so it prints a blank unless a restart has just happened. Harmless in `install`; misleading in `status`. Fix in the next session that touches the script — a blank that looks like a fault is the thing this project exists to eliminate.

**Rejected-at-the-door (Diagnostics Category 5) — IMPLEMENTED** in the receiver (D163), live 08-Jul 14:49. **`callhook_watchdog.py` v1.0 — BUILT**, on the VPS, manual runs only. **Two defects, both open:** (a) no coverage guard — a date the access log does not span reads as zero traffic and reports CRITICAL *"MyOperator is not delivering at all"*, a confident wrong diagnosis pointing away from the real cause; (b) `mask_key()` does not `unquote()` before hashing, so labels do not compare across sources (D165). **Not scheduled**: it exits 1 on WARN, so a naive `OnFailure` fires all day on already-fixed 403s.

**`ANTHROPIC_API_KEY len=111` sits unaccounted in `/root/wa/.env`**, loaded into the environment of a gunicorn worker that has no use for it. Added inside the outage window; recorded nowhere; nobody has identified what wrote it. Confirmed still present at S127 close. **Rotate it, find out what wrote it, and move it out of the call-hook worker's `.env`.** An unknown secret in a live process's environment is a fault whether or not it has caused one yet (D169).

---

## §65 SESSION 65 — Plan-tool multi-condition build + patient-lookup design (05 Jul 2026)

**EOS-LIGHT. No live code changed.** Decisions **D121–D124**.

### A) The standalone HTML plan-tool (Thread A) — multi-condition build, v21 → v23
- **What it is:** `rehab_nutrition_plan_vNN.html`, a single standalone file opened in Chrome. Owner
  fills a patient's details, prints/saves a personalised Rehab/Nutrition plan (Hindi-first older ortho
  patients). A **portal artifact, NOT a live system** until the owner deploys it. Owner's real Chrome
  is the FINAL print authority; headless render is a pre-check only.
- **Library:** `library_data.json` (extracted from `Orthopedic_Clinic_Rehab_Nutrition_v11.xlsm`) =
  126 exercises (English+Hindi), 111 modalities, 13 conditions. Embedded into the HTML.
- **v22** (md5 `91da5a2ad96678c184c4e38acbcf5b4f`): multi-condition selector — up to 4 conditions,
  each block's sub-pickers correct by type (joints=Pathway+Severity; spine=Pathway inc.
  radiculopathy+Severity; Ankle=Severity only; Post-TKR/THR=Phase only).
- **v23** (md5 `68cf0c9c45c3926bacc60200e561a66d`): two output buttons — **Patient Printout**
  (Nutrition + Home Exercise Sheet, per-condition sections, patient language, no machine settings) and
  **Physio Sheet (clinic)** (per condition: Modalities first, then Exercises). Headless-verified.
- **Hindi header name 16pt** — owner confirmed OK in real Chrome. **Parked item CLOSED.**

### B) Patient-lookup design — LOCKED (D121–D124)
- **D121** — Host the plan-tool as a **VPS-portal Flask app on its own private port, key-gated, behind
  OLS** (`extprocessor` + `context`) — SAME walled-off pattern as clinic-portal (:8099), attendance
  (:8042), wa-approve (:8101).
- **D122** — **Canonical CSV source rule:** read newest `patient_master.csv` + newest
  `patient_diagnosis.csv` by modified-date, from ONE fixed VPS folder the tracker syncs to — never a
  hard-coded Drive file-ID. Exact VPS folder confirmed on the box at build time.
- **D123** — **Shared Mobile → pick-list** (name+age+ID); never auto-pick. Age shown, never trusted.
- **D124** — **Two faces:** (a) owner's full version; (b) locked-down **staff BP-entry-only** version.

---

## §66 — SESSION 66: patient-data map + shared data model (Track 1)

**EOS-LIGHT — design + read-only Drive discovery. No code, no writes.** Decisions **D125–D128**.

### §66.1 — The patient-data "nerve centre" (read-only)
**Canonical live folder (CONFIRMED):** `My Laptop / data /` (Drive folder id
`1aRKh1ecJVpVmPJMMupnNKGiabrKfsF1C`; parent "My Laptop" `1SXjt7EO2MBVrqPF1gFMkm__a-JYZZDCG`). The
Drive-sync mount from the clinic-PC follow-up tracker. Live files keep a **stable file-id** as they
update (only modifiedTime moves), so the D122/L2 "newest-by-date in one fixed folder" rule resolves
cleanly to this single folder. (Exact VPS-side sync path still confirmed on the box at build time.)

**Files (all re-synced together; last stamp seen 2026-07-04):**
- `patient_master.csv` — identity. Cols: `Patient_UID, Clinic_Specific_Id, Patient_Name, Mobile_Raw,
  Mobile_Clean, Mobile_Status, First_Seen_Date, Last_Seen_Date, Mobile_Duplicate_Count,
  Identity_Status, Added_From, Last_Updated`. (id `1KmHIoJSi7cY1JvXKepwHVWlNUH79QLPl`)
- `patient_diagnosis.csv` — clinical. 7,452 data rows. Cols: `Patient_UID, Clinic_Specific_Id,
  Patient_Name, Age, Sex, Mobile_Clean, Diagnosis_Raw, Standardized_Diagnosis, Diagnosis_Category,
  Diagnosis_Priority, Diagnosis_Status, Comorbidities, Concession_Scheme, Admin_CC, Admin_PD,
  Admin_BID, Is_VIP, Source_File, Last_Updated`. (id `19duFAoKuK32vZo52miQA_OQL7qkfEycx`)
- `visit_ledger.csv` — attendance (NOT vitals). Cols: `Visit_ID, Visit_Date, Patient_UID,
  Clinic_Specific_Id, Patient_Name, Mobile_Raw, Mobile_Clean, Had_Procedure, Source_File,
  Processed_On`. (id `1tTHCcU8hhyGd-ciG87JDLbfrmF8-UzGP`)
- Plus `followup_ledger.csv`, `revenue_ledger.csv`, `outbound_log.csv`, `concession_log.csv`,
  `reinstatements.csv`, `confirmations.csv`, `diagnosis_source_meta.json`.
- Call recordings, transcripts, staff call outcomes flow to Drive + tracker sheet. All join on `Patient_UID`.

### §66.2 — Data-reality facts (verified)
- **`Patient_UID` is the spine** across every file (e.g. `ZOUEY49089`). Machine-stable, unique, never shown to staff.
- **Sex is coded `M`/`F`** — lookup maps `M→Male`, `F→Female`. 1 blank.
- **Age is dirty:** of 7,452 rows — 25 blank, 7 impossible (≤0 or >110), 389 under 15 (real children).
  Age is SHOWN for confirmation, never trusted.
- **Shared mobiles common:** `Mobile_Duplicate_Count` up to 5 on one number. Pick-list is a frequent path.
- **Diagnosis partly unclassified:** 47 categories, largest bucket "Other / Unclassified" (~1,922) +
  "No Diagnosis Recorded" (~293). Pre-fill frequently leaves the picker empty by design.
- **Comorbidities populated for only ~670 of 7,452 rows** (~9%) — blank pre-fill for ~91% is correct.
- **VITALS EXIST NOWHERE in synced data.** Height/weight/BP locked in Docterz only. Vitals tool is net-new.

### §66.3 — The shared data model (LOCKED)
**Write-path law:** Docterz = source of truth for diagnosis; tracker *derives* the CSVs; plan-tool and
vitals tool **only READ** Docterz-derived data and **NEVER write back**. Any tool that persists writes
into a file **it alone owns**. One-writer-per-file.

**Read-only inputs (tracker owns):** `patient_master`, `patient_diagnosis`, `visit_ledger`,
recordings/transcripts/call-outcomes.

**Write-side files (tool-owned):**
- `vitals_ledger.csv` — single vitals store. One write-function; **two front doors** (staff BP-only page +
  vitals section inside the plan-tool). Keyed `Patient_UID` + date. Append-only (one row per capture).
- `plan_ledger.csv` — plan-tool's OWN record of doctor's choices at a visit (conditions + comorbidities +
  sheets printed). Persists "I changed the diagnosis for this plan" WITHOUT touching `patient_diagnosis.csv`.

**ID rule:** `Clinic_Specific_Id` = human lookup handle (what staff TYPE). `Patient_UID` = backend
storage/join key (what everything SAVES ON). Lookup resolves Clinic ID → UID behind the scenes.

### §66.4 — Decisions (D125–D128)
- **D125** — Plan-tool pre-fills condition + comorbidities from `patient_diagnosis.csv`; doctor reviews
  & corrects on screen. ~26% Other/Unclassified, so pre-fill often leaves the picker empty — expected.
- **D126** — Plan-tool NEVER writes back to Docterz-derived files. Doctor's on-screen choices PERSIST in
  a plan-tool-owned `plan_ledger.csv`.
- **D127** — VITALS: one `vitals_ledger.csv`, one write-function, TWO front doors (staff BP-only page +
  vitals section inside the nutrition tool). Nutrition tool also READS vitals back. One writer, two interfaces.
- **D128** — JOIN KEY: `Patient_UID` = single backend storage/join key. `Clinic_Specific_Id` = human
  lookup handle only. Nothing stored keyed on Clinic ID.

### §66.5 — Still open (resolved/advanced in §67)
- Column schemas of `vitals_ledger` + `plan_ledger` → **RESOLVED in §67 (locked).**
- Build order: vitals format → nutrition tool's auto-read. Nutrition tool can ship first with manual weight/BP.
- VPS canonical-folder read path (D122/L2) — resolve on the box at build time. Still open.

### §66.6 — STANDING DIRECTIVE: living data-structure documentation
1. One exhaustive research/documentation pass of the ENTIRE data structure — every file live and
   in-construction (Drive `My Laptop/data/`, tracker outputs, Google-Sheet tabs, recordings/transcripts/
   call-outcomes, the new `vitals_ledger` + `plan_ledger`), and how they interconnect on `Patient_UID`.
   Produce one canonical "Clinic Data Map" document.
2. Keep it a LIVING document — updated on every file add / column change / writer change / new tool.
   Canonical alongside the KB. Surfaces in the Runbook backlog every session until done.

---

## §67 — SESSION 67: `Patient_UID` origin verified + schemas locked + v24/v25 built (05 Jul 2026)

**Full BUILD session on Track 1. No VPS / live-systems code changed — plan-tool remains offline Thread-A.**
Decisions **D129–D131**.

### §67.1 — `Patient_UID` origin VERIFIED: Docterz-generated (corrects §66 inference)
Owner exported a live 13-patient sample from Docterz (`clinical_data_export_docterz_sample.xlsx`,
55 columns). It has a **native column literally named `Patient UID`**, alongside `Clinic Specific Id`,
`Mobile`, `Gender`, `DOB`, `Age`, `Diagnosis`, and a present-but-empty `Vitals` column. Sample UIDs
(`RYIDM58643`, `GTYMR99882`, `YNTEP13051`) match the KB's 5-letter+5-digit format (`ZOUEY49089`).

- **`Patient_UID` is generated by DOCTERZ at registration — NOT by the tracker.** The tracker copies it
  through into the CSVs. Earlier "tracker generates it" reasoning was WRONG. Same-day patients are absent
  from the tracker CSVs only because the tracker ingests end-of-day / next-morning; the patient already
  holds their Docterz UID from registration.
- **BUT the UID is a BACKEND field — NOT visible at the front of Docterz.** Reception and owner see only
  **Clinic Specific ID + name + mobile** at the visit. The UID surfaces later (export/tracker layer).
- D128 join-key law stands and is reinforced: both keys are Docterz-native and authoritative at source.

### §67.2 — Other facts from the Docterz export
- **Docterz `Vitals` column EXISTS but is empty** in the sample — confirms vitals are net-new even at
  source. Revisit if Docterz vitals ever populate.
- **Docterz exports `DOB` + precise age** ("60 years 11 mons 21 days"). DOB is the authoritative age
  source; the plain-integer `Age` in `patient_diagnosis.csv` is a lossy downstream derivation (explains
  the dirty ages in §66.2). If age accuracy matters, DOB is the truth.
- The Docterz export is the **headwater** of the whole patient-data graph; feeds the tracker → CSVs.

### §67.3 — LOCKED SCHEMAS (Track 1 first build task)
**`vitals_ledger.csv`** (append-only, one row per capture; writer computes BMI/category/ratio for ALL
rows regardless of front door):
`Vitals_ID, Patient_UID, Clinic_Specific_Id, Patient_Name, Measured_On, Age_At_Visit, Sex, Height_cm,
Weight_kg, BMI, BMI_Category, Waist_cm, Waist_Height_Ratio, BP_Systolic, BP_Diastolic, Pulse_bpm,
Entered_By, Source_Face, Written_At, Note`

**`plan_ledger.csv`** (one row per plan generation; choices-only + pointers) — **14 columns, AMENDED at
S73 (D134): two PDF-path columns added. This is the CURRENT locked order:**
`Plan_ID, Patient_UID, Clinic_Specific_Id, Patient_Name, Plan_Date, Conditions_Selected,
Comorbidities_Selected, Diet_Type, Vitals_ID_Used, Sheets_Printed, Plan_PDF_Patient, Plan_PDF_Physio,
Generated_By, Written_At`

> **Schema-change note:** the original S67 plan_ledger was 12 columns (…`Sheets_Printed, Generated_By,
> Written_At`). S73 inserted `Plan_PDF_Patient` + `Plan_PDF_Physio` before `Generated_By` (D134). The
> `vitals_ledger.csv` schema above is UNCHANGED.

- `vitals_ledger` is append-only (repeat-visit trends accumulate). Derived values (BMI, category,
  waist:height) stored IN the ledger for reproducibility (owner wants historical progress reports).
- `plan_ledger` references vitals via `Vitals_ID_Used` (no duplicated weight to drift; blank if plan
  made with no vitals). Single source of truth for the measurement is `vitals_ledger`.
- `Sheets_Printed` = which sheets printed this visit (`Patient`, `Physio`, or both); blank if none yet.
- `Plan_PDF_Patient` / `Plan_PDF_Physio` = server-written archive path of each printout PDF (D132);
  blank if that sheet was not printed.

### §67.4 — v24 built: offline patient lookup (APPROVED offline)
`rehab_nutrition_plan_v24.html` (md5 `8c11be6b235578b5f3979448da8ba8b8`, 275,062 bytes). Adds to v23:
- "Load patient data" button → owner picks the two CSVs once per session (offline-safe; browsers can't
  auto-read disk files).
- Type Clinic ID or mobile → resolves to `Patient_UID` → auto-fills Name/Mobile/ID/Age/Sex.
- Pre-fills condition (mapped Standardized_Diagnosis → one editable condition block) + comorbidities
  (semicolon-split → editable tick boxes). Unmapped dx leaves picker empty (D125).
- Shared-mobile → pick-list (name+age+ID); never auto-picks (D123).
- Age shown, never trusted: blank/junk left blank + flagged; child/impossible ages flagged (L5/§66.2).
- Height/weight/BP stay manual with a reminder line.
- Headless-tested against a synthetic CSV pair (real headers, no real data) — 8 scenarios pass, zero JS errors.

### §67.5 — v25 built: embedded vitals section + new-patient path (APPROVED offline)
`rehab_nutrition_plan_v25.html` (md5 `92e3c637d0742d3ae1775ab21f871ea1`, 281,346 bytes). Adds to v24:
- **Embedded vitals-entry section (front door 2 — owner):** reuses the tool's existing `compute()` so
  BMI/category/waist:height MATCH the printed plan exactly. Shows the values live, then "Assemble vitals
  record" builds the exact `vitals_ledger.csv` row in locked column order and shows it field-by-field.
  **Offline shows the row only; the actual CSV append is a hosted-stage job (one writer, D127, decision B).**
- **New-patient toggle** (reworded from "No Clinic ID" → "New / not-yet-synced patient"): reveals a note,
  captures Clinic ID + name + mobile (NO UID field — not visible at front, §67.1). Row written with
  `Patient_UID` blank + Note "NEW — not yet in tracker; UID pending sync".
- IST timestamp stamped explicitly (TZ-independent). Missing height/weight → warning, not a broken row.
- Headless-tested: existing + new-patient + missing-measurement cases pass, zero JS errors. Print +
  lookup regression-clean.

### §67.6 — Decisions (D129–D131)
- **D129** — `Patient_UID` is **Docterz-generated** (verified from live export), copied through by the
  tracker; it is a **backend field, not shown at the front of Docterz**. Corrects the §66 inference;
  D128 reinforced.
- **D130** — New-patient (not-yet-synced) handling: the tool captures **Clinic ID + name + mobile only**
  (front-of-Docterz visible). No UID field. `Patient_UID` left blank on the row; row marked "UID pending sync".
- **D131** — **New-patient reconciliation (refines D130):** a same-day new patient's vitals/plan row
  starts UID-blank and is later STITCHED to the real Docterz `Patient_UID` once the tracker ingests them,
  matching on `Clinic_Specific_Id` + mobile. This is a light hosted-stage reconciliation job (essentially
  the earlier "option A"), needed only for the minority same-day-new path. Schema already supports it
  (UID nullable; Clinic ID + name always present). The staff BP-only page (D124/D127) shows NO calculated
  outputs on screen, but its stored rows STILL get BMI/category/ratio computed by the one writer (complete data).

### §67.7 — Track 1 status after Session 67 (historical — superseded by §73.4)
- Schemas LOCKED (§67.3). v24 lookup + v25 vitals section BUILT & owner-approved OFFLINE.
- Plan-tool artifact at end of S67: **v25** (`92e3c637d0742d3ae1775ab21f871ea1`).

---

## §73 — SESSION 73: plan_ledger row-assembly built (v26) + printout-PDF archiving locked (05 Jul 2026)

**Full BUILD session on Track 1. All offline — no VPS/live/GitHub code changed. Plan-tool remains an
offline Thread-A artifact.** Decisions **D132–D134**. (Sessions 68–72 were the design arc that settled
these decisions; folded in here.)

### §73.1 — Owner steering decision (context, not a numbered D)
Build the plan-tool + vitals tool fully, do all the backend write-path work, and **HOST BOTH TOGETHER
at one time** — the "final online version" is locked only once everything is built and the backend
actually writes ledgers + PDFs end-to-end. Offline builds (v26 onward) are **staging steps toward the
hosted product**, not deliverables in themselves. Does not change the locked Track-1 build ORDER; it
changes when a piece is "done" (hosting = done).

### §73.2 — Printout-PDF archiving (D132/D133/D134)
- The tool prints two sheets (patient + physio) but kept no copy — no record of what a patient was
  actually given. **D132** fixes it: archive **both** PDFs per visit, tagged by patient:
  `plan_archive/<year>/<Patient_UID>/<Plan_Date>_<Plan_ID>_{patient|physio}.pdf`. New patients with no
  UID yet (D130) → `plan_archive/pending/<Clinic_Id>_<mobile>/…`; the reconciliation job (D131) moves
  them to the real UID folder on tracker sync. Yearly top folder → easy archive-off later.
- **Why a frozen PDF, not re-print-on-demand:** the sheet depends on live CSV lookups + on-screen
  choices + tool version; re-generating months later may not reproduce it. A frozen PDF is the true record.
- **Storage sizing:** ~0.4 MB per visit (both text PDFs). At current load (**<10 printed plans/day**) →
  **~100 MB/year** — negligible on VPS or free Drive. Not a constraint.
- **Generated server-side** at hosting (a browser cannot silently save a PDF to disk). Offline, v26 only
  previews the exact paths.
- **Storage home (D133):** VPS canonical, Drive mirror DEFERRED (owner: "just save it reliably").
  Reliable local writes; matches one-writer-per-file + D122; the live write-path never depends on Drive
  at print time. A Drive mirror can be bolted on later (reuse the recording-archive OAuth-as-owner
  pattern, D36) if browse-anywhere is ever wanted.
- **Schema (D134):** see the amended `plan_ledger` in §67.3 (two PDF-path columns).

### §73.3 — v26 BUILT (offline, awaiting owner real-Chrome check)
`rehab_nutrition_plan_v26.html` — **md5 `6212ad8fe5072521cadb36b21f190ffa`**, from v25
(`92e3c637d0742d3ae1775ab21f871ea1`), full-file replacement, ~287 KB.
- New **"Plan record"** collapsed `<details>` panel (placed after the Doctor's-note group) — **button +
  on-demand preview only, NO live line** (owner: "it will clutter the front, skip it if possible").
- Click **Assemble plan record** → shows the exact 14-column `plan_ledger.csv` row (header + data +
  field-by-field). Nothing written offline.
- Reads REAL on-screen state: each condition block via `data-cond`/`data-path`/`data-sev`/`data-phase`
  → `Name [pathway/severity/phase]; …`; ticked comorbidities (`dm/htn/ckd/gout/thyroid` → full names);
  diet dropdown.
- **Print-flag mechanism (owner-approved):** each of the two existing print buttons sets a silent flag
  (`PLAN_PRINTED.patient` / `.physio`) — one added line each, no change to how printing works or looks —
  so `Sheets_Printed` + the two PDF-path fields truthfully reflect what was printed. Assemblable in any
  order (before or after printing).
- `Plan_ID`, `Patient_UID`, `Vitals_ID_Used` correctly blank offline (server-assigned/linked at hosting).
- **Offline PDF-path caveat (on-screen note added):** offline the path shows a `pending/` folder + a
  literal `<Plan_ID>` placeholder — expected, because the front never holds the backend UID (D129) and
  Plan_ID is server-assigned. On the hosted server both resolve to the real UID folder + a real Plan_ID.
- **Testing:** Node `--check` parse passed; 3-scenario headless logic test passed (established patient /
  new patient / nothing-printed). CSV escaping reused from v25.

### §73.4 — Track 1 status after Session 73 (CURRENT)
- Schemas LOCKED (§67.3 vitals unchanged; plan_ledger amended, D134). v24 + v25 + v26 built; v24/v25
  owner-approved offline; **v26 awaiting owner real-Chrome check** (closes Step 1 when confirmed).
- **NOT yet done:** hosting (Flask+OLS, D121/D122 — resolve VPS folder on the box); the real server-side
  write-path (vitals writer + plan_ledger writer + PDF archiving); staff BP-only page (D124/D127/D131);
  new-patient reconciliation job (D131); living Clinic Data Map (§66.6).
- **Owner plan:** host plan-tool + vitals TOGETHER once the backend write-path is built.
- Plan-tool current artifact: **v26** (`rehab_nutrition_plan_v26.html`, md5 `6212ad8fe5072521cadb36b21f190ffa`).
  Still an OFFLINE Thread-A artifact — not hosted, not committed to the live repo.

### §73.5 — Decisions (D132–D134)
- **D132** — Archive both printout PDFs, patient-tagged (`plan_archive/<year>/<Patient_UID>/…`); new-
  patient PDFs → `pending/` bucket, stitched on reconciliation; ~100 MB/yr; PDFs generated server-side.
- **D133** — Storage home: VPS canonical, Drive mirror deferred (owner: "just save it reliably").
- **D134** — `plan_ledger` schema +2 columns (`Plan_PDF_Patient`, `Plan_PDF_Physio`); new 14-col order (§67.3).

---

## §75 — SESSION 75: PC-local write-path built (Track 1, Step 4)

### §75.1 — Three pivots (context for the decisions)
1. **PC-local, not VPS.** The plan+vitals write-path tool runs on the **clinic PC**. The
   two source CSVs (`patient_master.csv`, `patient_diagnosis.csv`) already live on the
   clinic PC — the follow-up tracker writes them there and Google Drive syncs them out.
   Hosting the writer where the data already is means no patient data spreads to a
   second machine, and it honours the earlier no-VPS-hosting lean. (D136)
2. **Staff BP-only page retired.** Owner: *"I only enter the vitals in my PC; staff hand
   me a physical vitals record."* The second front door has no user. (D135)
3. **PDF/ledger storage home = clinic PC**, then Drive sync. Archive structure unchanged.
   (D137)

### §75.2 — `clinic_writer.py` — the PC-local single writer (BUILT + INSTALLED)
One self-contained Python module on the clinic PC (`C:\clinic_writer\`). Three jobs +
one read-only helper:
- **`write_vitals(...)`** — appends one row to `vitals_ledger.csv`; computes BMI /
  BMI_Category (Indian cut-offs <18.5/<23/<27.5/else) / Waist_Height_Ratio for EVERY
  row itself (mirrors the plan-tool compute() exactly); assigns next `Vitals_ID`;
  normalises Sex → M/F; stamps IST. 20-col locked schema (§67.3).
- **`write_plan(...)`** — appends one row to `plan_ledger.csv`; assigns next `Plan_ID`;
  links `Vitals_ID_Used`; stamps IST. 14-col locked schema (§67.3, D134).
- **`archive_pdf(...)`** — renders a text-faithful PDF via **reportlab** (D138) and files
  it at the D132 path (`plan_archive/<year>/<Patient_UID>/…`; new patients → `pending/`).
- **`lookup_uid_by_clinic_id(...)`** — read-only resolve of Clinic_Specific_Id →
  Patient_UID from `patient_master.csv`. NEVER writes the source CSVs.

**ID formats:** `V-YYYY-NNNNNN` / `P-YYYY-NNNNNN` — per-year running counter, 6-pad,
gap-safe (scans existing IDs for the year, takes max+1).

**Invariants obeyed:** append-only; one-writer-per-file; never writes the two read-only
source CSVs; no network / no Drive / no VPS calls (Drive sync is Drive's own job on the
folders); IST timestamps explicit.

**Verification (both machines):**
- Sandbox (Py 3.12.3): `py_compile` clean; `--selftest` 20/20 PASS; real PDF (valid
  `%PDF-`) filed correctly.
- **Clinic PC (Py 3.14.5): owner ran `--selftest` → 20/20 PASS; certutil md5 =
  `d4e20a51ead1aada8c07bead2b504100` (matches). INSTALLED + CONFIRMED 2026-07-05.**

**Status:** this is the WRITE-PATH LIBRARY. No front-end wired yet (Step 5 next). Manual
fallback (browser print, no archive) unchanged until the front-end is live.

**Repo demarcation (kit correction, same session):** `clinic_writer.py` lives in its OWN
top-level Git folder **`clinic_writer/`** — kept deliberately separate from
`followup-tracker/` because they are two distinct systems (matching `C:\clinic_writer\`
on the PC). A `README.md` in the folder documents the split. Code md5 unchanged; only the
repo location was corrected from the first S75 kit.

### §75.3 — Amendments to earlier Track-1 decisions
- **D121 (host as VPS Flask+OLS)** — AMENDED by D136: this tool is **PC-local**, not on
  the VPS. (Other portal tools on the VPS are unaffected.)
- **D122 (canonical CSV folder)** — RESOLVED by D136: canonical source is the **clinic-PC
  local `data/` folder** the tracker writes (Drive folder id
  `1aRKh1ecJVpVmPJMMupnNKGiabrKfsF1C` is its Drive mirror). Newest-by-date rule stands.
- **D124/D127 (two front doors / staff BP page)** — the STAFF-PAGE portion is RETIRED by
  D135. The single vitals writer + one-vitals-ledger design stands (one front door now:
  the doctor).
- **D133 (storage home VPS)** — AMENDED by D137: storage home is the **clinic PC**, then
  Drive sync. Archive structure (D132) and schema (D134) unchanged.

### §75.4 — Decisions (D135–D138)
- **D135** — Staff BP-only page RETIRED from Track-1 build (only the doctor enters vitals).
- **D136** — Track-1 write-path = PC-LOCAL; reads clinic-PC local `data/` CSVs; amends
  D121, resolves D122.
- **D137** — PDF + ledger storage home = clinic PC, then Drive sync; amends D133;
  archive structure unchanged.
- **D138** — PDF engine = reportlab (pure-Python, text-faithful; durable one-command
  Windows install), over HTML-render engines.

**Reserved:** D83–D92 (P1–P10). **Next free: D139.**

## §93 — Track 1 Step 5: PC-local Vitals & Plan front-end (COMPLETE)

### §93.1 What was built
The **local front-end** that turns the S75 `clinic_writer.py` engine (write-path library)
into a usable screen. Runs only on the clinic PC, doctor-only, no internet, no VPS.
Lives on **D:** so a Windows reformat can't wipe it (D140).

Package at `D:\clinic_writer\`:

| File | Role | md5 |
|---|---|---|
| `clinic_writer.py` | Engine (updated this arc — bilingual PDF) | `0ad6d9f449addd03de40b0bfbacca659` |
| `vitals_app.py` | Flask app, port 5057, 127.0.0.1 only | `ba29a558947f7ac8489626e0df39a8ef` |
| `vitals_page.html` | v25 plan-tool + Save-to-records bridge | `24ac9af4edfd00c01e4025e88800dade` |
| `open_vitals.bat` | Double-click launcher (mirrors open_tracker.bat) | — |
| `clinic_menu.html` | One-bookmark menu → Tracker + Vitals&Plan | — |
| `NotoSansDevanagari-Regular.ttf` | Hindi font for archive PDFs | `f4ae6809bd8c31573370e8da72514012` |

### §93.2 Flow
Type Clinic ID → `/lookup` reads `patient_master.csv` + `patient_diagnosis.csv`
(READ-ONLY, from the tracker's C: data folder) → resolves real `Patient_UID`
(shared-mobile pick-list, D123) → Age/Sex/condition pre-fill (editable, D125) →
enter vitals + plan choices → print as usual → **Save to records** → `/save` calls
`write_vitals` + `write_plan` + `archive_pdf` (both sheets) → two ledger rows + two PDFs.
New patients (UID blank) route to `plan_archive\pending\` for later reconciliation (Step 7).

### §93.3 Reads / writes
- **Reads (never writes):** `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\data\`
  → `patient_master.csv`, `patient_diagnosis.csv`.
- **Writes (own, on D:):** `D:\clinic_writer\vitals_ledger.csv` (20 cols), `plan_ledger.csv`
  (14 cols), `plan_archive\<year>\<UID>\<date>_<PlanID>_{patient|physio}.pdf`.

### §93.4 Decisions D139–D142
- **D139** — Front-end is its own auto-launched Flask app importing clinic_writer,
  a SEPARATE program from the live tracker (stability/safety/maintenance); shared menu
  page; double-click `.bat` launch (mirrors the tracker). Ports 5000 (tracker) / 5057
  (vitals) never clash.
- **D140** — Whole tool + engine + ledgers + archive live on **D:** (survives a Windows
  reformat). D: is an SSD PARTITION → protects vs reformat, NOT disk death; Drive sync is
  the real off-machine backup. Source CSVs stay on C:, read across drives. New tool built
  on D: from birth; migrating the live tracker to D: is a separate later task.
- **D141** — Diagnosis pre-fill mapped from `Orthopedic_Diagnosis_Taxonomy_Master.xlsx`
  (27 canonical categories). 12 auto-fill a rehab button; 15 blank-by-design (doctor picks).
  Knee Internal Derangement blank (owner A=No); Cervical*→Cervical Disc Disease,
  Lumbar*→Lumbar PIVD (owner B=Yes). Unmapped → "dx recorded — pick the exercise set",
  never a silent Knee-OA default. (Fixes the strict-label matcher that failed on the real
  full-wording data.)
- **D142** — Bilingual archive PDF via **per-run font switching**: Helvetica for English,
  NotoDev (NotoSansDevanagari) for Devanagari runs, chosen per run within each line
  (engine helper `_mixed()`). Whole-doc Devanagari font rejected — it has digits only,
  no A–Z, so it dropped all English. ALSO: empty-physio-PDF fixed — Save bridge now builds
  BOTH sheets from the tool's own `sheetBlocks()` (physio is never an on-screen box), not
  screen-scraping. Graceful font fallback → archiving never fails. reportlab stays (D138).

### §93.5 Engine change (clinic_writer.py)
Only `archive_pdf` changed since S75: base font Helvetica + `_mixed()` per-run Devanagari
wrapping + a `_DEV_RE` regex helper. Self-test still 20/20. New md5
`0ad6d9f449addd03de40b0bfbacca659` (was `d4e20a51ead1aada8c07bead2b504100`). This is the
FIRST engine change since the S75 lock — additive, fallback-safe.

### §93.6 Status
**Step 5 COMPLETE** and owner-verified on the clinic PC. **Step 7 (reconciliation)** not
started. **Plan-tool / vitals tool are still PC-LOCAL offline systems** — not hosted, not
live-VPS.

### §93.7 Open (next session, Track 1)
**Hindi SPELLING** corrections in the exercise/modality library source strings
(`name_hi` / `instr_hi`) — content + rendering are correct; only spelling to tidy. The
strings live in the embedded `LIB` in `vitals_page.html` (originally from
`Orthopedic_Clinic_Rehab_Nutrition_v11.xlsm`). Owner explicitly scoped OUT table-formatting
rework (archive content complete; run-together tables acceptable).

## §94 — Track 2: call-webhook outage + doctor-console fix (LIVE CODE CHANGED)

Session 94 was **not** a planned build session. It opened on a manual follow-up push and
turned into two live-fault repairs, then a project examination and a six-item forward agenda.

### §94.1 Incident 1 — call-webhook 403 outage (FIXED, verified end-to-end)

**Symptom:** staff dashboard follow-up tiles stuck on "⌛ Checking the call… the outcome
unlocks once it connects" even after a genuine >15-second connected call. The outcome
dropdown never unlocked. Started ~Jul 6, all tiles at once. WhatsApp feed unaffected.

**Diagnosis chain (all read-only until the fix):**
1. `call-hook.service` (:8098) was **up and healthy** — ruled out dead service.
2. Raw-log folder `/root/wa/call-hook/call_hook_logs` had **no `2026-07-07.jsonl`** — no
   call webhook had been received all day; last body landed Jul 6 ~13:41.
3. MyOperator panel → Webhooks v2: the **Call** webhook showed **status Failed**; the
   WhatsApp webhook showed **Active** (hence WhatsApp still worked).
4. Panel Failure Logs: **every** Call Ended / Call Summary delivery returned **HTTP 403**,
   consistently, on both Jul 6 and Jul 7.
5. A local `curl` to the receiver with the correct key **also returned 403** — proving the
   rejection was the receiver's own secret-gate, not an OLS/IP/WAF block.

**Root cause:** the VPS `.env` had **two secrets mashed onto one physical line** — a lost
newline had merged `CALLHOOK_SECRET` with a trailing `FU_UPLOAD_SECRET=…` fragment, so the
receiver read `CALLHOOK_SECRET` as a long run-on string that could never match the panel's
key → every incoming call webhook 403'd → nothing written to `Call_Durations` → the duration
gate could never unlock. (A **second, clean** `FU_UPLOAD_SECRET` on the next line was the one
actually in force — last-definition-wins — so the follow-up upload catcher kept working,
which is why only calls broke.)

**Fix (owner ran, one step at a time):**
- Timestamped backup of `.env` first.
- `sed -i '17s|.*|CALLHOOK_SECRET=<new clean key>|'` — rewrote **only** line 17 to a fresh
  **plain-alphanumeric** call key (Option B, chosen to remove the `@` special-char that
  complicates URL transport). The run-on `FU_UPLOAD_SECRET=…` junk on line 17 was thereby
  deleted; the real `FU_UPLOAD_SECRET` on line 18 was untouched.
- `systemctl restart call-hook.service` → verified `active`, `secret gate: ON`, `connected
  to 'Call_Durations' — 98 rows known`.
- MyOperator panel → Webhooks v2 → **Call** webhook → Edit → updated `?key=` to the new
  clean key; Call Ended + Call Summary still ticked; Authentication None; Save.

**Verified end-to-end:** Shavez placed a real follow-up call; the tile's "Checking…"
resolved; the outcome unlocked and saved. Outage closed.

**New fault code:** `CALLHOOK_SECRET_MISMATCH_403` — **ASSISTED**. Detection idea (not yet
built): if the panel's Call webhook shows Failed OR no `YYYY-MM-DD.jsonl` raw-log file has
appeared by mid-morning on a clinic day, alert. Procedure = compare `grep CALLHOOK_SECRET
/root/wa/.env` against the panel URL's `?key=`; re-sync + restart if they differ.

### §94.2 Incident 2 — doctor console "Could not load: isGenericAgent_ is not defined" (FIXED)

**Symptom:** the doctor dashboard's **Outcome Review → Today** view showed "Could not load:
isGenericAgent_ is not defined" and a count of 0. **Yesterday** view worked (13 outcomes
listed). So saved outcomes were fine; only the Today *display* was broken.

**Diagnosis (static scan of the live Apps Script JSON export, all 14 files):**
- `OutcomeLog.gs` line ~333 calls `isGenericAgent_(by)` — a helper **defined nowhere** in
  the project. When the Today build loop reaches it, JS throws → the whole Today view dies.
- The scan flagged 5 "called-but-undefined" names; 4 (`escPick_`, `fmtLV_`, `fmtWhen_`,
  `sbPick_`) are false positives — defined as `var x = function`. **Only `isGenericAgent_`
  is genuinely undefined.** It is the sole such fault in the project.
- Today vs Yesterday difference: line 333 only bites when a live matched call with an agent
  name is present, which the Today enrichment path produces and the archive-based Yesterday
  path does not — explaining why only Today failed.

**Fix (D143):** added the one missing helper to `OutcomeLog.gs`, placed among the small
helpers after `OL_col_`. It answers the question the call site needs — *is this "Handled By"
value a generic placeholder (staff / doctor / unknown / agent / system / blank) rather than
a real name?* — so line 333 can borrow the real caller's name from the call log when the
outcome was filed under a generic label.

```
function isGenericAgent_(name) {
  var n = String(name || '').trim().toLowerCase();
  if (!n) return true;
  return (n === 'staff' || n === 'doctor' || n === 'unknown' || n === 'agent' || n === 'system');
}
```

**Delivered as a full-file replacement** (per protocol), built from the live JSON export
(21,076 → 21,690 chars; only the one function + comment added). Verified: `node --check`
PASS; exactly one definition, one call site. Owner deployed via **edit existing deployment →
New version** (URL stable). Owner confirmed: Today view loads, "all good now."

### §94.3 Project examination (no code beyond the two fixes)

Full static analysis of the live project was run from the Apps Script JSON export. Findings:
- The dashboard **does not de-duplicate** the follow-up worklist — it reads `Followups_Today`
  exactly as the PC push writes it. So **duplicate patient rows originate PC-side** (the
  tracker's list generation), not in the dashboard.
- Today's real worklist was **238 rows** (20 Due Today, 34 Grace, 52 Actionable Missed,
  **124 Probable Dropout**, plus small buckets) — confirming the ">200, not humanly callable"
  problem is dominated by the Probable-Dropout bucket.
- `Call_Feed` remains the known-unreliable feed (D55); archive is authoritative.

### §94.4 Six-item forward agenda (owner-set; DESIGN captured, not built)

Logged for sequencing. My recommended order and current standing:

1. **Duplicate patient entries in a day** — real; fix is **PC-side** (de-dupe before/inside
   `push_followups_today.py`, or in the tracker's list builder). SAFE, ready to build once
   we see why a patient doubles (same section twice vs two sections). *Next execution item.*
2. **Reconcile "didn't pick up but visited"** — auto-settle a follow-up when the patient
   actually visits (proof = new Docterz visit). HIGH VALUE. Overlaps **Track-1 Step 7**
   (new-patient reconciliation) — same match machinery (Clinic ID + mobile). Needs a design
   step (which visits qualify, what outcome to write, where it runs).
3. **Trim the staff calling list (>200)** — needs an OWNER POLICY decision (what caps the
   daily list, where the 124 dropouts go — separate low-priority queue / weekly batch).
   Partly pre-designed as **D66 "Living Staff List"** (snooze, 3-tries-escalate,
   outcome-vanishes) — designed, not fully built.
4. **Live staff-activity summary on the doctor dashboard** — today live + yesterday
   cross-verified/audited against archive + transcripts. Buildable; the "audited" half
   depends on item 5.
5. **Migrate to AI audit layer** — this is **Stage 3 (D62)**: overnight Haiku-tier batch,
   ~₹200–350/month, transcript-vs-claimed-outcome, doctor-only flags. Designed, not built.
   Doctor-only "Call Audit" sheet already exists.
6. **Historical follow-up insights across taxonomy** — analysis only, no code. **Blocked on
   a de-identified data export** (patient data is deliberately not in this project). Claude
   can deliver the analysis plan now; real numbers need the export.

**Owner stance at close:** open to doing more together when it fits limited time; delegated
sequencing to Claude ("your call"). Claude's call: do the safe/ready items (Item 0 done +
Item 1 next), design-sheet the rest — do NOT bundle policy/AI-cost decisions into a rushed
build.

### §94.5 Decisions
- **D143** — `isGenericAgent_` helper added to `OutcomeLog.gs`: generic = staff / doctor /
  unknown / agent / system / blank. Purpose: let the Today outcome view borrow the real
  caller name from the matched call when the outcome was filed under a generic label.
  Full-file replacement; node-check verified; deployed as New version (URL stable).
- **D144** — Call-hook secret standard: the `?key=` gate for `/mo-callhook` (and by
  extension similar self-chosen VPS webhook gates) shall be **plain alphanumeric, no special
  characters** (no `@ # / ? & =`), because special characters corrupt under URL transport and
  caused the S94 403 outage. Applies to future key rotations of these gates.
- **D145** (hygiene note, not yet acted) — during S94 the plain-text values of
  `CALLHOOK_SECRET` (new), `FU_UPLOAD_SECRET` (line 18), and the old junk fragment were
  visible in terminal paste. These are self-chosen VPS gate keys (NOT WABA/MyOperator
  tokens), so exposure is low-risk, but a courtesy rotation of `CALLHOOK_SECRET` +
  `FU_UPLOAD_SECRET` is advisable at a convenient time (no Lokesh coordination needed).

### §94.6 State changes to §12
- **Duration gate is LIVE and healthy again.** `call-hook.service` (:8098) up; `Call_Durations`
  filling; outcome unlock working. The S94 403 outage is CLOSED.
- **Dashboard Apps Script:** `OutcomeLog.gs` updated (D143), redeployed as a New version of
  the existing deployment; dashboard URL unchanged.
- Everything else in §12 (KB v1.40) stands verbatim: WABA sends still BLOCKED vendor-side
  (D120); `wa_approve` still nohup (not systemd); key rotations still overdue; watchman /
  health report / attendance / follow-up push all live; Track 1 Step 5 COMPLETE, Step 7 not
  started.

---

---

## §102 SESSION 102 — Staff call-sheet de-duplication (07 Jul 2026)

**FULL EOS. Live PC-side code changed** (`processor.py`, the follow-up tracker's list builder).
This is the first execution item of the owner's six-item agenda ("Item 1 — duplicate patient
entries"), and it is DONE, installed, and verified on the day's real sheet.

### §102.1 The problem (root cause, verified from real data)
The daily staff call sheet `Staff_Action_Today_*.xlsx` was showing the SAME patient two or three
times. Root cause established by reading today's real workbook, NOT assumed:
- A patient carries **several OPEN follow-ups from different visit cycles** (each with its own
  `Followup_ID` / KEY). They are all still "open" because earlier cycles were never closed, so they
  all land on the same day's sheet.
- **No KEY repeats** — these are not byte-identical rows (so it is NOT the old upstream watcher
  dup bug). They are genuinely-distinct un-collapsed multi-cycle follow-ups for one person.
- On 07-Jul: **236 follow-up rows, 22 duplicate groups.** Two sub-patterns: (A) two open
  follow-ups with different dates (most groups); (B) two with the SAME date (near-simultaneous
  double-generation for one visit).
- **Confirmed the dashboard does not de-dupe** (D-note carried from §94.3) — the fix belongs
  **PC-side at generation**, exactly where the KB already said it should.

### §102.2 The fix (owner-confirmed collapse rule, D146)
Inserted a collapse step into **`build_staff_call_workbook`** in `processor.py`, applied to the
final follow-up list (`combined`) AFTER the call overlay + reinstatement merge and BEFORE the rows
are written — so it affects ONLY the FOLLOW-UP section. Procedure call-backs and the Watch/
Unreachable section are untouched.

Collapse rule (owner-confirmed, S102):
- **Group by mobile + name + diagnosis** — so a patient's two genuinely-different clinical
  problems stay as two separate rows.
- **Keep ONLY the most recent follow-up cycle = latest `Due_Date`.** Older cycles are removed
  from the sheet **entirely, with NO note** (owner decided a note would confuse staff).
- **EXCEPTION: a reinstated ("call back & complete", amber) row always wins its group**, even if
  older — that flag means the clinic owes the patient a callback and must never be dropped.
- **Blank / invalid mobile → group by name only** (those are un-callable anyway).
- The whole block is wrapped in `try/except` → on ANY error it falls back to the full,
  un-deduped list. A de-dupe hiccup can **never** break the sheet (same defensive pattern the
  file already uses for reinstatements and procedure reconciliation).

### §102.3 The audit workbook is deliberately NOT de-duped
`processor.py` has TWO builders: `build_staff_call_workbook` → the staff CALL SHEET
(`Staff_Action_Today_*.xlsx`, fixed here) and a second builder → the doctor AUDIT workbook
(`Followup_Audit_*.xlsx`, 9 tabs). The audit's own "Staff Action Today" tab still shows every
row **by design** — it is the doctor's oversight microscope; only the staff-facing call sheet is
collapsed. (Owner may revisit if he wants the audit collapsed too.)

### §102.4 Verification (on the real regenerated sheet)
- **Follow-up rows 236 → 214** (22 removed); **zero duplicate groups remain**.
- Rakesh Kumar → single row, the 29-Jun amber "call back & complete" (reinstated WON). ✅
- Chandraprabha → single row. ✅  Satwinder Kaur → single 03-Jul row (25-day-old hidden). ✅
- `python -m py_compile processor.py` clean on the clinic PC (owner-confirmed, no output).
- New `processor.py` md5 `8813a27db66c91628153c55912612ceb`; backup kept on PC as
  `processor_BACKUP_S102.py` (manual fallback = restore it).

### §102.5 Decisions
- **D146 — Staff call-sheet de-duplication rule.** In `build_staff_call_workbook`
  (`processor.py`), the follow-up list is collapsed to **one row per patient** before writing:
  group by **mobile + name + diagnosis**; keep the **latest `Due_Date`**; **older cycles hidden
  with no note**; **reinstated rows always win their group**; blank-mobile grouped by name only;
  fail-safe `try/except` falls back to the full list. Only the FOLLOW-UP section is affected; the
  Procedure and Watch sections and the separate `Followup_Audit_*.xlsx` audit workbook are
  untouched. Verified live 07-Jul (236 → 214, zero dups).

### §102.6 Carried forward (added to priority backlog)
- **Option B — per-patient "latest state" join** (bigger task, deferred by owner to the
  console/reconciliation work): put the patient's **most-recent visit + most-recent call outcome +
  its recording + transcript + most-recent follow-up** all on the single surviving row. Needs the
  Docterz visit feed + `Call_Durations` / call-transcription sources wired in; overlaps agenda
  Items 2 & 4 and the Stage-3 audit layer. **This session's fix (Option A) is the call-sheet
  de-dupe only.**
- **Agenda Item 2 confirmed as next** — reconcile "didn't pick up but visited" (auto-settle a
  follow-up when the patient actually returns; proof = a real Docterz visit after the follow-up
  was created). Claude owes the one-page DECISION SHEET before that build. The current sheet does
  NOT yet drop patients who quietly returned — that is Item 2 by design, not a regression.

### §102.7 State changes to §12
- **`processor.py` (PC-local, follow-up tracker) is CHANGED and LIVE** — carries the D146
  de-dupe. Everything else in §12 stands: WABA sends still BLOCKED vendor-side (D120);
  `wa_approve` still nohup (not systemd); duration gate live + healthy; key rotations overdue;
  Track 1 Step 5 COMPLETE, Step 7 not started.


## §107 SESSION 108 — Data-folder / Drive-sync evaluation (07 Jul 2026)

**EOS-light finding (no code) — folded into this v1.45 full EOS.** The owner asked why the
follow-up tracker's `data\` folder shows **multiple dated CSV files**, and whether that indicates
a fault in the Item 2 auto-settle engine (which reads visits). Claude evaluated the code + folder
and found it **NORMAL BY DESIGN.**

### §107.1 The two file-types (they must not be confused)
The tracker's `data\` folder holds two different kinds of CSV that look superficially similar:
- **`consultation_report_YYYY-MM-DD.csv`** — the **daily raw Docterz input**, ONE per clinic day.
  `parse_consultation_report()` (`processor.py`) reads the day's file at ingest; then it is history.
  **These are SUPPOSED to be many and dated** — one arrives each day. Seeing a pile of them is
  correct, not a fault.
- **`visit_ledger.csv`** — the **single cumulative attendance ledger**, read from ONE fixed path
  (`DATA_DIR / "visit_ledger.csv"`). The tracker appends each day's consultations into it. It is
  **SUPPOSED to be ONE file, never dated.** Every row's `Source_File` column records which dated
  `consultation_report_*` it came from (the audit trail). Verified on the live file: 749 visits,
  04-Jun → 06-Jul-2026, cumulative, single file.

Analogy for the record: the dated `consultation_report_*` files are the **fuel** (one tank-fill a
day); `visit_ledger.csv` is the **tank**. The settle engine and everything else read the tank.

### §107.2 Drive-sync direction (owner-confirmed S108)
The `data\` folder is **Google-Drive-synced** (owner confirmed). This matches the existing record
(D122 canonical-source rule; §66.1 folder `My Laptop / data /`, Drive id
`1aRKh1ecJVpVmPJMMupnNKGiabrKfsF1C`). Direction: the **clinic-PC tracker owns/writes** these files;
Drive **mirrors them out** (off-machine backup). The canonical read is *newest-by-modified-date from
the one fixed folder*, never a hard-coded Drive file-ID.

### §107.3 The one honest dependency (not a fault today)
The Item 2 settle engine can only settle a returning patient **once that patient's row exists in
`visit_ledger.csv`** — i.e. after the day's `consultation_report_*` is ingested AND Drive has synced.
So settle freshness = sync freshness. On 07-Jul this was healthy (last visit 06-Jul, processed
07-Jul — normal one-day lag). Nothing broken; recorded as a known dependency, not a defect.

### §107.4 Decision
- **D147 — Two-file-type rule + Drive-sync direction (VERIFIED-NORMAL).** In the tracker `data\`
  folder: `consultation_report_YYYY-MM-DD.csv` = daily raw Docterz inputs, *many and dated by
  design*; `visit_ledger.csv` = single cumulative ledger, *never dated*, read from one fixed path.
  Multiple dated CSVs are expected, not a fault. The `data\` folder is Drive-synced (PC writes →
  Drive mirrors); settle-engine freshness depends on that sync. No code change; documentation only.


## §121 SESSION 121 — Item 3: staff call-list cap + Hard-to-Reach split (07 Jul 2026)

**FULL EOS. Live PC-side code changed** (`processor.py`, `build_staff_call_workbook`). This is the
third execution item of the owner's six-item agenda ("Item 3 — trim the >200 staff list"), DONE,
installed, and verified on the real generated sheet.

### §121.0 Agenda context — Items 1 & 2 status confirmed this arc
- **Item 1 (duplicates) — DONE (§102, S102).**
- **Item 2 (auto-settle "didn't pick up but visited") — found ALREADY BUILT and LIVE, verified S106.**
  The settle engine already exists in `processor.py` (`compute_followup_status`, ~line 1820): every
  follow-up is matched to a real Docterz visit keyed on `Patient_UID`, using `Followup_Log_Date`
  (the raise-date) with constant `COUNT_LOG_DATE_VISIT_AS_RETURN = False` → a visit **strictly
  after** the raise-date settles it (same-day = the prescribing visit, does NOT settle). Matched
  rows flip to terminal `Returned Early / On Time / Late` with `Matched_Visit_ID` +
  `Return_Delay_Days`, are excluded from the staff sheet, and kept tagged in the audit workbook.
  Verified on 07-Jul live data: **249 of 493 rows settled**, zero leakage to the staff Call Sheet.
  Item 2 therefore needed **no build** — only end-to-end confirmation, now done. (Owner decision on
  the design sheet: visit beats amber — a returned patient settles even if the row was reinstated.)

### §121.1 The problem
The staff Call Sheet carried ~222 rows/day — not humanly callable. Volume dominated by **Probable
Dropouts** (127 on 07-Jul; 11–60 days overdue), which crowd out the winnable fresh follow-ups
(Due Today + Grace + Actionable). It is a "wrong patients at the top" problem, not "too many people".

### §121.2 The fix (owner policy, Sessions 109–114; D148)
All changes land in **`build_staff_call_workbook`**, applied to the final follow-up list AFTER the
settle-exclusion + call overlay + D146 de-dupe and BEFORE the rows are written. Two steps, both
wrapped in `try/except` (fail-safe fallback to the pre-cap list — can never blank the sheet):

- **Step A — 3-strike Hard-to-Reach split.** Any row with `Call_Attempts ≥ 3` and still no contact
  (`Call_Resolution` not RESOLVE/DECLINE) is pulled OFF the daily list into a new **Hard-to-Reach**
  tab in the staff workbook, carrying **name · Clinic ID · mobile · diagnosis · last-visit date**
  (last-visit read read-only from `visit_ledger`) **· attempts**. Reinstated (amber) rows are
  protected — never pulled. Purpose: the doctor decides per patient — keep calling or archive. NOT
  auto-archived. *(Recording + transcript links are a planned fast follow-up — owner choice "b",
  S111 — because those live on Drive/tracker-sheet keyed on `Patient_UID`, outside `processor.py`.)*
- **Step B — 120-cap + drip + roll-to-tomorrow.** Remaining rows filled to a **DAILY_CALL_CAP = 120**
  total: winnable buckets (Due Today / Grace Period / Actionable Missed) first, in the engine's
  existing freshest-first + post-op-float order; whatever room is left under 120 back-filled with the
  **OLDEST Probable Dropouts** (most days-overdue first, the drip). When winnable alone ≥ 120, take
  the top 120 and the winnable **overflow rolls to tomorrow** (not shown today; reappears next run
  because its ledger status is unchanged); dropouts get zero room that day.

Priority order within the list is **unchanged** from before (the engine's own ranking + post-op
float stay as-is). The audit workbook (`Followup_Audit_*.xlsx`) is **untouched and stays full** —
only the staff Call Sheet is capped.

### §121.3 Verification (on the real regenerated sheet, 07-Jul)
- Staff workbook tabs: Call Sheet · Vacation Notice · Settled Follow-Ups · **Hard-to-Reach** · Day
  Revenue. New tab present. ✅
- Follow-up section capped at **exactly 120 rows** (237 callable → 110 winnable + 10 oldest-dropout
  drip). ✅
- Hard-to-Reach tab present with correct title; **0 patients today** (no one has ≥3 no-contact
  attempts yet — expected; the call-log read-back is young). ✅
- Audit workbook intact (493 ledger rows, 9 tabs). ✅
- `python -m py_compile processor.py` clean on the clinic PC (owner-confirmed, blank output).
- New `processor.py` md5 **`171a090645da130a4f4cbb0c0b102f22`**; backup kept on PC as
  **`processor_BACKUP_S115_pre_Item3.py`** (= S102 build `8813a27db66c91628153c55912612ceb`, the
  manual fallback = restore it).
- One transient install hiccup: first run raised `PermissionError [Errno 13]` at `wb.save()` because
  the target `Staff_Action_Today_*.xlsx` was open in Excel (Windows file-lock) — NOT a code fault;
  closing the file and re-running succeeded. Recorded so it isn't mistaken for a regression.

### §121.4 Decision
- **D148 — Staff call-sheet cap + Hard-to-Reach split.** In `build_staff_call_workbook`
  (`processor.py`), after de-dupe and before writing: (A) rows with `Call_Attempts ≥ 3` and no
  contact (not RESOLVE/DECLINE) are moved to a **Hard-to-Reach** tab (name · Clinic ID · mobile ·
  diagnosis · last-visit date · attempts; reinstated rows exempt) for doctor keep/archive decision;
  (B) the remaining list is capped at **120** total — winnable buckets first in existing priority
  order, leftover room drip-filled with oldest Probable Dropouts, winnable overflow rolls to
  tomorrow. Fail-safe `try/except` fallback to the full list. Audit workbook untouched/full.
  **Amendment note to D146:** "reinstated always wins its group" now holds *among rows that survive
  the settle engine and the 3-strike split* — a returned or 3-strike row is removed before de-dupe
  (visit/attempts beat amber, per owner). Verified live 07-Jul (cap = 120, drip = 10, HTR = 0).

### §121.5 Recording/transcript follow-up (owner choice "b", carried)
The Hard-to-Reach tab ships now with the four LOCAL fields. Adding **last call recording +
transcript links** is the immediate next micro-task: those live on Drive + the tracker sheet keyed
on `Patient_UID` (the VPS call-transcription job, doctor-only sheet
`1rq9VvB5L94EmmZbiUwase9HBLsJ3htispYLd1rHjSRQ`). Needs the transcript-metadata join verified before
wiring — kept out of this build to keep it clean and shippable.

### §121.6 State changes to §12
- **`processor.py` (PC-local, follow-up tracker) is CHANGED and LIVE** — now carries BOTH the D146
  de-dupe AND the D148 cap/Hard-to-Reach split. md5 `171a090645da130a4f4cbb0c0b102f22`. Everything
  else in §12 stands: WABA sends still BLOCKED vendor-side (D120); `wa_approve` still nohup (not
  systemd); duration gate live + healthy; key rotations overdue; Track 1 Step 5 COMPLETE, Step 7 not
  started.

---

## SURVEILLANCE REGISTER — unchanged since Session 64

No surveillance rows changed at S65–S67 (no live component added). The v1.32 register stands verbatim,
including the WABA-send fault row (`WABA_SEND_AUTHORIZER_500`, CRITICAL·ESCALATE-ONLY) and the
wa_approve "not yet service-monitored" note.

*(Forward-looking: when the hosted plan-tool + vitals tool become live services, each gets its own
surveillance row — liveness on its port/service, plus a freshness/disk check for the `plan_archive/`
PDF store (D132) and the two ledgers. Not yet applicable; not built.)*

---

### Surveillance forward-notes folded from later sessions
*(These are forward-looking notes recorded in the deltas; no surveillance ROW is live yet for
these Track-1 tools. Kept here so the register stays complete.)*

**From v1.39 (S75):** When the Step-5 front-end goes live on the PC it becomes a local service
— at that point add a liveness/freshness row (local app up; ledgers + `plan_archive/` writable
+ syncing). *(Step 5 is now COMPLETE per §93, but as a PC-local offline app, not a monitored
live service; no VPS surveillance row applies.)*

---

## §95–100 — DOCUMENTATION-CONSOLIDATION ARC (records-cleanup; NO live code)

Sessions 95–100 were an **EOS-light documentation arc — no live system, VPS file, dashboard
script, or Track-1 tool was touched.** Its whole purpose was to turn fragmented delta chains
into clean single-file canonical masters and to recover version files that had gone missing
from project knowledge. Logged here so the KB's own history is honest and self-explaining.

### §95.1 What was done
- **KB consolidated → v1.42 (S95):** folded v1.38 base + v1.39 + v1.40 + v1.41 into one
  self-contained master (this document's immediate predecessor). Verbatim fold-in; unified
  Decisions Index D121–D145; one changelog.
- **Missing-file hunt + recovery (S96–S97):** established that **KB v1.37 has no standalone
  file** in project knowledge but its content was already absorbed into the v1.38 base (present
  in §73) — nothing lost. Found that **GitHub `docs/`** holds an older full-history archive
  including the **KB v1.37 delta** and **Umbrella v1.27 delta** (both recoverable there). The
  one true gap — the **Umbrella v1.28 consolidated base** — was **recovered by the owner from
  cold-backup kit**, along with the deep **Umbrella v1.19 delta**. Both uploaded; gap closed.
- **Umbrella consolidated → v1.31 (S99):** folded v1.28 (consolidated base) + v1.29 (S75) +
  v1.30 (S93) into one self-contained Umbrella master. Verbatim fold-in; Track-1 decisions
  note D121–D142; one changelog. Companion to this KB.
- **Runbook refreshed → v53 (S100):** the Runbook had been stale at v52 (Session 94), predating
  the arc. Reissued as a self-contained **v53** that records the arc, carries the full live
  backlog forward verbatim, and repoints the canonical set.
- **KB history-close → v1.43 (S101, this fold):** this section + changelog entry, so the KB's
  own record references its v1.42 consolidation and the Umbrella v1.31 / Runbook v53 companions.
  No live-systems content changed; §12 STATE and every prior section stand verbatim.

### §95.2 Owner directive — CANONICAL DOCS ARE SINGLE CONSOLIDATED FILES (no delta chains)
From S100 onward, each canonical document is built as **one fully-consolidated, self-contained
file with a single changelog** — never a base-plus-stacked-deltas chain. Stacked deltas over
many sessions caused the missing-file confusion this arc had to clean up. When a new canonical
version is issued, everything folds into one master; older delta files become historical only.

### §95.3 Canonical set after this arc
- **KB `Clinic_Master_KB_SystemsRegister` v1.43** (this document) — WINS on any conflict.
- **Umbrella Architecture v1.31** (consolidated, self-contained).
- **Handoff Runbook v53** (Session 100, self-contained).
- Recovered from cold kit: **Umbrella v1.28** (consolidated base) + **v1.19** delta.
- Recoverable from GitHub `docs/`: **KB v1.37** delta, **Umbrella v1.27** delta, older history.
- **Known-stale in GitHub (commit-to-repo housekeeping task, owner pushes):** repo lacks KB
  v1.38/v1.40/v1.42/v1.43, Umbrella v1.29/v1.30/v1.31, the refreshed Runbook, Call_Console v1.5,
  and the API card. Not a lost-file problem — a sync task.

### §95.4 No decisions consumed
This arc added **no new D-numbers** (it changed no system or design). Next free decision number
is unchanged at **D146**. The §95.2 documentation directive is a working-protocol standard, not
a numbered architectural decision.

---

## DECISIONS INDEX — CONSOLIDATED (D121–D175)

**Track-1 additions (D121–D134), from v1.38 base:**
- **D121** Host plan-tool as walled-off Flask+OLS VPS portal tool, key-gated. *(AMENDED by D136 — tool is PC-local, not VPS.)*
- **D122** Canonical CSV rule: newest-by-date from one fixed folder; never a Drive file-id. *(RESOLVED by D136 — clinic-PC local `data/` folder.)*
- **D123** Shared mobile → pick-list; age shown not trusted.
- **D124** Two faces: owner full version + staff BP-only version. *(Staff-page portion RETIRED by D135.)*
- **D125** Pre-fill dx/comorb; review & correct; often empty by design.
- **D126** Plan-tool never writes source; choices persist to plan_ledger.
- **D127** One vitals_ledger, one writer, two front doors; tool reads vitals back. *(Now one front door — doctor — after D135.)*
- **D128** Patient_UID = backend join/storage key; Clinic_Specific_Id = human handle.
- **D129** Patient_UID is Docterz-generated (verified); backend field, not shown at front.
- **D130** New-patient path: Clinic ID + name + mobile only; UID blank + "pending sync".
- **D131** New-patient reconciliation: stitch UID later on Clinic ID + mobile (hosted/Step-7 job).
- **D132** Archive both printout PDFs, patient-tagged (`plan_archive/<year>/<Patient_UID>/…`); new-patient PDFs → `pending/` bucket, stitched on reconciliation; ~100 MB/yr; generated server-side at hosting.
- **D133** Ledger + PDF storage home = VPS canonical; Drive mirror deferred. *(AMENDED by D137 — storage home is the clinic PC.)*
- **D134** `plan_ledger` schema +2 PDF-path columns (`Plan_PDF_Patient`, `Plan_PDF_Physio`); new 14-col order.

**Track-1 write-path (D135–D138), from v1.39 (S75):**
- **D135** Staff BP-only page retired (doctor-only vitals entry).
- **D136** Track-1 write-path PC-local; clinic-PC `data/` CSVs canonical (amends D121, resolves D122).
- **D137** PDF/ledger storage home = clinic PC → Drive sync (amends D133; structure unchanged).
- **D138** PDF engine = reportlab (pure-Python text-faithful archive).

**Track-1 front-end (D139–D142), from v1.40 (S93):**
- **D139** Front-end is its own auto-launched Flask app importing clinic_writer, separate from the live tracker; shared menu page; double-click `.bat` launch. Ports 5000 (tracker) / 5057 (vitals) never clash.
- **D140** Whole tool + engine + ledgers + archive live on **D:** (survives a Windows reformat; Drive sync is the real off-machine backup). Source CSVs stay on C:, read across drives.
- **D141** Diagnosis pre-fill mapped from `Orthopedic_Diagnosis_Taxonomy_Master.xlsx` (27 canonical categories): 12 auto-fill a rehab button, 15 blank-by-design; unmapped → "pick the exercise set", never a silent Knee-OA default.
- **D142** Bilingual archive PDF via per-run font switching (Helvetica English / NotoSansDevanagari Devanagari, engine `_mixed()`); physio PDF built from `sheetBlocks()` not screen-scraping; graceful font fallback; reportlab stays.

**Track-2 live fixes (D143–D145), from v1.41 (S94):**
- **D143** `isGenericAgent_` helper added to `OutcomeLog.gs` (generic = staff / doctor / unknown / agent / system / blank) so the Today outcome view can borrow the real caller name from the matched call when the outcome was filed under a generic label. Full-file replacement; node-check verified; deployed as New version (URL stable).
- **D144** Call-hook secret standard: the `?key=` gate for `/mo-callhook` (and similar self-chosen VPS webhook gates) shall be **plain alphanumeric, no special characters** — special chars corrupt under URL transport and caused the S94 403 outage. Applies to future rotations of these gates.
- **D145** (hygiene note) Courtesy rotation of `CALLHOOK_SECRET` + `FU_UPLOAD_SECRET` advisable at a convenient time (self-chosen VPS gate keys, NOT WABA/MyOperator tokens; low-risk; no Lokesh coordination needed).
- **D146** Staff call-sheet de-duplication in `build_staff_call_workbook` (`processor.py`): one row per patient (group mobile+name+diagnosis, keep latest `Due_Date`, older cycles hidden no-note, reinstated rows win, blank-mobile→name-only, fail-safe fallback). Staff sheet only; audit workbook untouched. Verified 07-Jul (236→214). See §102.
- **D147** Two-file-type rule + Drive-sync direction (VERIFIED-NORMAL): `consultation_report_YYYY-MM-DD.csv` = daily raw inputs, many-and-dated by design; `visit_ledger.csv` = single cumulative ledger, never dated, one fixed path. `data\` folder Drive-synced (PC writes → Drive mirrors); settle freshness depends on sync. No code. See §107.
- **D148** Staff call-sheet cap + Hard-to-Reach split in `build_staff_call_workbook` (`processor.py`): (A) `Call_Attempts ≥ 3` + no contact → Hard-to-Reach tab (name·Clinic ID·mobile·diagnosis·last-visit·attempts; reinstated exempt) for doctor keep/archive; (B) cap **120** total — winnable first, oldest-dropout drip fills leftover room, winnable overflow rolls to tomorrow; fail-safe fallback; audit untouched. Amends D146 (reinstated wins *among rows surviving settle + 3-strike*). Verified 07-Jul (cap 120, drip 10, HTR 0). See §121.
- **D149** Stage-3 AI judge (`call_verdict.py`) — the transcript-only verdict layer (parent D62). Claude Haiku, ALL calls both directions, BLIND (transcript+direction+duration only; never the staff claim or any patient/agent identifier); answers in the LIVE dashboard vocabularies (11 FU codes / incoming lists) + UNCLEAR; six mandatory-review flags (postop·complaint·urgent·surgery·clinical·conduct); evidence excerpt per verdict; three-field record (staff/AI/doctor-final) version-stamped; writes its OWN `Call_Verdicts` tab in the doctor-only Call Audit sheet; calibration-first (no auto-accept, no actions in v1); diarisation deferred (owner "a"). Built + installed + proven (md5 `bb17720d4857e3c040e8c89e7cc2e095`, selftest 24/24, first real run 15/15). Claim-match ±45-min join found too weak (§122.4) — redesign is the next task. See §122.
- **D150** Stage-3 claim-match join REDESIGNED (`call_verdict.py`, replaces the §122.4 ±45-min window). Match on patient PHONE NUMBER over a whole-day FORWARD window (`call_start − 10 min` … `call_start + 28 h`, reaching the next-morning batch); earliest-unclaimed-in-window wins; two calls to one number pair in call-time ORDER; each row stamped Match Confidence (`unique`/`ordered`/`none`). Root cause fixed: staff file outcomes in morning batches, so a claim's `When` is filing-time not call-time. See §123.
- **D151** Judge-once-fill-later (upsert) for `Call_Verdicts`: the AI judges each call ONCE; when the staff claim lands later, the row's claim/verdict cells are updated in place (no second AI call); the doctor's own columns are never touched; re-runs are idempotent (₹0 on a no-new-work run). Header-mismatch fail-safe refuses to append onto an out-of-date layout. See §123.
- **D152** `Call_Verdicts` row ENRICHED: full Patient Number (from Join Key, always present; replaces the last-4 mask in the DOCTOR-ONLY sheet — blind-judge unaffected, AI still sees transcript only), Recording Link (joined from the Stage-1 `Call_Recordings` tab by Join Key), Match Confidence, and a name/Clinic-ID fallback by number for unmatched calls. Console logs stay masked to last-4. See §123.
- ⛔ **OVERTURNED BY D190 (S130).** *The finding below is FALSE. `saveIncomingOutcome` stamps `Section='Incoming'`, never `Source=incoming`; the incoming `Log outcome` button has been dead for every `Patient_Master` match since it shipped (F-8). "Zero rows, ever" recorded an impossibility as a staff habit. Read D190 and §S130 first. Retained unaltered per D175.*
- **D153** (finding) Staff do NOT file outcomes for INCOMING calls — zero `Source=incoming` rows in `Followup_Outcomes`, ever — so "No claim logged" is CORRECT for incoming calls, not a gap. Real match rate is measured on outgoing-with-claim only (06-Jul: 16/22 Match = 73%). See §123.
- **D154** (design-locked, build pending S124) Verdict Analysis Layer: a daily-updated, read-only, ONE-PATIENT-PER-SCREEN-VERTICAL Google Sheet segregating verdicts by scenario (Mismatch · AI-logged-staff-didn't · Unclear · Matches-collapsed) for fast doctor review; built on the proven `Call_Verdicts` data; one-writer-per-table preserved. See §123.7.

**Continuation — D155–D175 (added at v1.49, Session 127).**

> **Where D155–D160 physically live.** They were written into the tail of `§123.7` at v1.48 and were never added to this index; the index heading claimed `D121–D160` while its body stopped at `D154`. They are **re-homed here by reference, not by movement** — nothing is cut and re-pasted inside a canonical document (D175). Read them in `§123.7`, immediately before the `## §124` heading.

- **D155** Verdict Analysis Layer BUILT (`verdict_review.py`). *In `§123.7`.*
- **D156** Duration gate FAILS OPEN (`Dashboard.html` v18.19; amends D77/D82). *In `§123.7`.*
- ⛔ **PARTLY OVERTURNED BY D190 (S130).** *The numbers below stand. The clause "D153's principle stands (staff do not file outcomes for incoming calls)" is FALSE — D190 destroyed that principle. Retained unaltered per D175.*
- **D157** (correction to D153) 06-Jul was 36 outgoing / 26 incoming; real match rate **16/20 = 80%**. *In `§123.7`.*
- **D158** (OPEN DEFECT) The D150 phone-keyed forward-window join can bind an outgoing claim to an earlier incoming call. Display-mitigated only; **the join is not fixed.** *In `§123.7`.*
- **D159** (incident) `CALLHOOK_SECRET_MISMATCH_403` recurrence; VPS aligned to panel; clinic left on the old secret. *In `§123.7`.*
- **D160** (governance) The live Apps Script project, not GitHub, is the canonical dashboard. *In `§123.7`.*

> **D161 does not exist.** Confirmed by direct search of `v1.48` (S127): two occurrences, both forward-looking ("next free: D161"). It was reserved and skipped, never minted. It is not a lost decision.

- **D162** Dual-key acceptance is mandatory for any shared-secret gate. *§S125.*
- **D163** A gate must write down its refusals before it refuses. *§S125.*
- **D164** `.env` is never edited by line number; its contents are validated at startup. *§S125.* *(Rationale twice retracted — see D166.)*
- **D165** Masked key labels must be encoding-normalised (`unquote()`) before comparison. *§S125.*
- **D166** The correct entry in a knowledge base is sometimes `UNKNOWN`. *§S126.*
- **D167** A control that addresses one path into a hazard is not a control on the hazard (`core.autocrlf`). *§S126.*
- **D168** Install by candidate path and atomic `mv`; never overwrite the live file to test it. *§S126.*
- **D169** Secrets are inventoried by name and value length, never by value. *§S126.*
- **D170** Empty and absent are the same state for `CALLHOOK_SECRET_PREV`. Read the source. *§S127.*
- **D171** A multi-step production rotation is executed by a guarded script, not a human reading exit codes. *§S127.*
- **D172** A check's expected value must be derived from the artefact, never predicted from memory of it. *§S127.*
- **D173** Rotation step 4 must never precede step 3; the command is withheld until it can. *§S127.*
- **D174** A selftest is not a production verification. *§S127.*
- **D175** `§12` frozen as historical; `§12A` carries current state and wins. *§S127.*
- **D176** A procedure must never instruct a human to display a secret. *§S128.*
- **D177** A check must be calibrated to the clock of the thing it checks. *§S128B.*
- **D178** A monitored label must state what the artefact contains. *§S128B.*
- **D179** Report a count with the scope that makes it actionable, or not at all. *§S128B.*
- **D180** An audit finds; it does not fix. *§S128B.*
- **D181** Incoming calls become first-class; the receiver stops discarding what it already receives. *§S129.*
- **D182** An unknown incoming number gets a tile. Identity is established by staff, not by a filter. *§S129.*
- **D183** No call ends its day unlogged; the 21:30 sweep escalates both directions to the doctor. *§S129.*
- **D184** The outcome tile appears at hangup, not at ring. *§S129.*
- **D185** Nothing real-time is built on a system whose running cost is unmeasured. *§S129.*
- **D186** Verification of a subset is not verification of the set. *§S129.*
- **D187** A fix requiring D34's suspension is blast-radius-assessed first, and made last. *§S129.*
- **D188** A filename is not provenance. *§S129.*

## §122 SESSION 122 — Stage-3 AI judge built + Drive-token incident fixed (07 Jul 2026)

**FULL EOS — new live VPS script installed (`call_verdict.py`), OAuth app status changed,
Drive token re-minted.** Decision **D149** (parent: D62). No existing code file was modified;
one new script was added and the nightly-pipeline auth was repaired.

### §122.1 — Stage-3 AI judge: design LOCKED (D149, refines D62)
The AI verdict layer (agenda Item 5) was designed in full across the session and locked:
- **Judge model = Claude Haiku** (`claude-haiku-4-5`), overnight-batch-capable. The AI call sits
  in ONE isolated function; provider/model switch = one `.env` line (`AI_JUDGE_MODEL`).
- **Scope = ALL connected calls, both directions.** Incoming outcomes also land in
  `Followup_Outcomes` (`Source='incoming'`), so a claim can exist for either direction.
- **BLIND JUDGE (the heart of D62):** the AI is shown ONLY the transcript text + direction +
  talk-seconds. NEVER the staff's claimed outcome, patient name, mobile, Clinic ID, or agent
  name. This kills anchoring bias AND doubles as privacy (no patient identifier reaches the AI).
  The Match/Mismatch comparison happens AFTERWARDS, mechanically, in Python.
- **Answer vocabulary = the LIVE dashboard lists** (verified from the deployed `Dashboard.html`
  + the Apps Script export): 11 `FU_OUTCOMES` codes for outgoing follow-ups; the union of
  `IN_RESOLUTIONS` + `IN_NEW_OUTCOMES` for incoming; plus `UNCLEAR`. The judge answers in the
  staff's own language so the comparison is apples-to-apples. If the dashboard dropdowns change,
  the `VOCAB_*` constants in `call_verdict.py` must change with them.
- **Six flags (second lane):** postop · complaint · urgent · surgery · clinical · conduct. Any
  flag true → mandatory doctor review, regardless of Match status. (Conduct flag owner-approved.)
- **Evidence excerpts:** every verdict quotes the single deciding Hindi phrase + who said it.
- **Three-field record:** staff outcome · AI outcome · doctor final adjudication — never
  overwritten. Version-stamped (prompt version + model version per row).
- **Calibration-first:** during the first weeks everything lands in the doctor console; NO
  auto-accept, NO action triggering (no WABA, no bookings, no edits to any other table). v1 is
  classify-and-flag ONLY.
- **Diarisation deferred (owner decision "a"):** the judge builds on today's undiarised
  transcripts; it infers speakers cautiously and answers UNCLEAR when it can't tell. Whether to
  upgrade Stage-2 to diarised transcription is decided later, from calibration evidence.

Two owner design files were folded in this session: **adopted** = evidence excerpts, the
three-field record, the six safety flags, version stamping, calibration framing; **deferred** =
the parallel 18-category taxonomy as the primary answer (kept as flags instead), downstream
action triggering, auto-accept confidence thresholds, and the 40-field ledger.

### §122.2 — `call_verdict.py` BUILT + INSTALLED + PROVEN
One new VPS script, sibling to Stage 2 at `/root/wa/recordings-archive/call_verdict.py`.
- Reads `Call_Transcripts` (Callback Tracker) → downloads each transcript from the restricted
  Drive folder → sends transcript-only to Haiku → parses strict JSON → fuzzy-matches the staff
  claim from `Followup_Outcomes` → computes Match / Mismatch / Partial / Unclear / No-claim →
  writes ONE row to a NEW `Call_Verdicts` tab in the **doctor-only** "Call Audit" sheet
  (`1rq9VvB5L94EmmZbiUwase9HBLsJ3htispYLd1rHjSRQ`). This script is that tab's ONLY writer.
- Modes: `--selftest` (offline logic, no key/network), `--dry-run` (judges for real, writes
  nothing), real run. No systemd timer yet (deliberate — after calibration review).
- **Verification:** `py_compile` clean; **selftest 24/24 PASS** on both sandbox and VPS; md5
  **`bb17720d4857e3c040e8c89e7cc2e095`**; 781 lines. First real run wrote **15 verdict rows**
  (`--date 2026-07-06 --limit 15`, 15 judged / 0 failed).
- **Storage/tab note:** `Call_Transcripts` actually lives in the Callback Tracker (the S23
  planned move to the doctor-only sheet never happened — confirmed by the doctor-only sheet's
  untouched-since-creation timestamp). `Call_Verdicts` is created automatically in the
  doctor-only sheet on first run.
- **Cost note:** v1 calls the API per-call (simpler, resumable) rather than the overnight batch
  API — realistic ~₹400–700/mo vs the ~₹200–350 batch estimate. Batch mode is a contained later
  upgrade if cost matters.

### §122.3 — 🔴 INCIDENT: Drive OAuth token expired (Testing-status 7-day limit) — FIXED
The Stage-3 dry-run surfaced `invalid_grant: Token has been expired or revoked` on the Drive
download step. **Root cause:** the Google OAuth app (owner-identity, D36) was left in **"Testing"
publishing status**, and Google expires Testing-status refresh tokens after **exactly 7 days**.
The token was minted ~30-Jun; 30-Jun + 7 = 07-Jul → it hit its built-in lifetime mid-day 07-Jul.
- **This token is shared by Stage 1 (recording archive, 02:00 IST) and Stage 2 (transcription,
  03:00 IST).** A dead token would have failed BOTH nightly jobs — and Stage-1 downloads today's
  recordings from MyOperator, whose links expire after ~24 h → risk of PERMANENT recording loss.
- **Damage check (Drive evidence):** last night's transcripts were uploaded at 03:05 IST 07-Jul
  → the token was alive that morning; it died later the same day. **Nothing was lost.** Caught
  within hours — the exact gap the (still-unarmed) timer-freshness checker exists for.
- **Fix Part 1 (permanent):** published the OAuth app **Testing → In production** — tokens no
  longer expire every 7 days. ("1 user / 100 user cap" and the unverified-app warning are
  expected and harmless for a single-account private app.)
- **Fix Part 2 (immediate):** re-minted `drive_token.json` on the owner's PC via the existing
  `get_drive_token.py` (manual copy-the-address-bar flow), uploaded to the VPS at
  `/root/wa/recordings-archive/drive_token.json` (726 bytes, 22:40 IST 07-Jul). Post-fix dry-run:
  **3 judged / 0 failed** — token fix AND Stage-3 both proven in one run.
- **Hygiene note (secret slip):** the owner screenshotted the OAuth `code=` redirect URL into
  chat. Harmless in this case (single-use code, consumed on token exchange, dies in ~10 min).
  Standing rule reinforced: never screenshot/paste a URL carrying a `code=` or key.

### §122.4 — FINDING: the ±45-min claim-match is too weak (next task)
The first real run judged 15 of 06-Jul's calls sensibly (good outcomes, honest UNCLEARs) but ALL
15 showed `claim=(none)`. Root-caused (read-only, no code changed): **not** a timestamp bug
(WebApp writes `When` as `yyyy-MM-dd HH:mm`, which the parser handles). The real cause is a
**workflow mismatch** — staff file outcomes in batches (e.g. ~10:00 IST clearing send-backs)
while calls happen in the 3–7 PM window, so a claim rarely falls inside the matcher's ±45-min
window around a call. The "No claim logged" result is the SAFE behaviour (never a false
Mismatch), but the join is too fragile to surface real Match/Mismatch. The AI half works; the
**claim-matching half needs redesign** (this was flagged as the weak link back in S24). Two paths
for next session: (1) widen to whole-day nearest-claim; (2) stronger join on mobile + `Agent Ext`
+ same-day. The 15 rows already written are fine as calibration data (blank claims, now
understood). **[RESOLVED S123 — path (1) whole-day join built; see §123 / D150.]**

## §123 SESSION 123 — Stage-3 claim-match join REDESIGNED + verdict row enriched + proven on real data (08 Jul 2026)

**FULL EOS — live VPS script replaced (`call_verdict.py`); no other code touched.**
Decisions **D150–D153** (parent: D149 / D62); **D154** design-locked for S124. This session turned
the Stage-3 judge from "AI works, matching doesn't" into a proven, trustworthy same-day verdict layer.

### §123.1 — Root cause of the 0/15, confirmed then fixed
The ±45-min window (§122.4) matched 0 real calls because **staff file outcomes in MORNING BATCHES —
hours after the call** (the follow-up batch runs ~09:00–13:41 IST). A claim's `When` is the FILING
time, not the call time, so a tight clock window can never catch it. Workflow truth, not a bug.

### §123.2 — The redesigned join (D150)
Match on the patient's PHONE NUMBER over a whole-day FORWARD window: an outcome filed from
`call_start − 10 min` (clock-skew) to `call_start + 28 h` (reaches the next-morning batch) is a
candidate. Calls can't leak past ~01:00 (Stage-1 downloads at 02:00), so a call and its outcome can
never be confused with the NEXT day's calls. Earliest-unclaimed-in-window wins; two calls to one
number pair in call-time ORDER. Every row gets a **Match Confidence**: `unique` (1 call + 1 candidate
→ trustworthy), `ordered` (competition, paired by order → glance), `none` (no claim → safe "No claim
logged").

### §123.3 — Enriched `Call_Verdicts` row (D152)
Added full **Patient Number** (from the Join Key, so always present — replaces the last-4 mask in this
DOCTOR-ONLY sheet; blind-judge unaffected), **Recording Link** (joined from the Stage-1
`Call_Recordings` tab by Join Key), **Match Confidence**, and a **name/Clinic-ID fallback** by number
so an unmatched call still carries an identity (training-KB completeness). Console logs stay masked.

### §123.4 — Judge-once-fill-later upsert (D151)
A call is sent to the AI only ONCE. When the staff claim lands later, the row's claim/verdict cells
are UPDATED in place (no second AI call); the doctor's own columns are never touched. Re-runs are
idempotent (proven: a second 06-Jul run = `0 judged, 0 failed, 0 claim-updated`, ₹0). A header-mismatch
fail-safe refuses to append onto an out-of-date tab layout.

### §123.5 — Proven on real data (D153)
06-Jul full re-run (62 calls, 0 failed): of the 22 OUTGOING calls with a filed claim, **16 Match /
5 Mismatch / 1 Unclear** (73%). 40 incoming calls = "No claim logged" — CORRECT: staff never file
incoming outcomes (zero `Source=incoming` rows in `Followup_Outcomes`). Three safety flags surfaced
(surgery; complaint+clinical+conduct; clinical). Owner reviewed the live tab and confirmed the AI is
judging correctly.

### §123.6 — Install / verification facts
`call_verdict.py` full-file replacement — md5 **`8c8ae1656056d8d1b2dec1b4776fe5c9`**, 1037 lines,
selftest **33/33** (was 24). Backup `call_verdict_BACKUP_S123_pre_join_redesign.py` at
`/root/wa/recordings-archive/`. Old 15-row `Call_Verdicts` tab deleted, recreated with the new layout.
No timer yet (carried). Prompt / vocabularies / flags / blind-judge unchanged from D149.

### §123.7 — Next task (D154, design-locked): Verdict Analysis Layer
Owner ask: a **daily-updated, read-only Google Sheet**, easy to read, **one patient per screen
vertically** (horizontal `Call_Verdicts` scrolling is cumbersome), **segregated by scenario**:
(1) Mismatches (staff vs AI) — training material; (2) AI-logged-but-staff-didn't; (3) Unclear — to
analyse *why*; (4) Matches — collapsed/summarised. Must stay trustworthy (built on the proven verdict
data; one-writer-per-table preserved). Top task for Session 124.

- **D155** Verdict Analysis Layer BUILT (`verdict_review.py`, parent D154/D149/D62). A read-only, rolling-7-day, ONE-PATIENT-PER-SCREEN-VERTICAL `Verdict_Review` tab in the doctor-only sheet, segregated by scenario, each card carrying the FULL TRANSCRIPT in a collapsed row-group with the AI's evidence excerpt highlighted in place. Two editable cells per card (a direction-aware dropdown mirroring the live dashboard vocabulary + a free-text note). Answers are harvested into a second tab, `Doctor_Verdicts`, keyed on Join Key — the durable ground-truth ledger that later seeds the voice-bot KB and the autonomous-judge calibration. **One writer per table preserved: `call_verdict.py` owns `Call_Verdicts` and is never written to by this script; `verdict_review.py` owns the two new tabs.** Harvest ALWAYS precedes the destroy-and-redraw, so a rebuild cannot destroy a typed answer. ₹0 — no AI calls. md5 `af6622e4edc3f454cf0bfed128c4f76b`, selftest 117/117. See §124.1.
- **D156** Duration gate FAILS OPEN (`Dashboard.html` v18.19; amends D77/D82). If a call **cannot be measured** within 3 minutes (webhook down, vendor slow, no `reference_id`), the outcome dropdown now unlocks anyway behind an "unverified" banner. A call **measured as not-connected** still blocks the outcome, exactly as D77 intended. All six gate states now persist to `localStorage`; the 3-minute timeout is measured from the CALL, not the page load; both silent `if(!ref) return;` paths now fail safe. **Standing principle: no verification mechanism may ever stand between a staff member and recording what a patient said.** See §124.2 and §124.3.
- ⛔ **PARTLY OVERTURNED BY D190 (S130).** *The numbers below stand. The clause "D153's principle stands (staff do not file outcomes for incoming calls)" is FALSE — D190 destroyed that principle. Retained unaltered per D175.*
- **D157** (correction to D153) The Session-123 figures described claim-status, not direction. 06-Jul truth: **36 outgoing / 26 incoming** (not 22/40). Of 20 outgoing calls with a filed claim: 16 Match / 4 Mismatch. **Real match rate = 16/20 = 80%**, not 73%. The "40" was the count of rows with NO claim; only 19 of them were incoming. D153's *principle* stands (staff do not file outcomes for incoming calls); its *numbers* were wrong. See §124.4.
- **D158** (finding, OPEN DEFECT in `call_verdict.py`) The phone-keyed forward-window join (D150) can bind an outgoing call's staff claim to an EARLIER INCOMING call from the same number. Proven on real data: number `…5227` rang in at 12:01 and was called back at 13:40; the claim filed for the 13:40 outgoing call was attached to the 12:01 incoming call, producing one bogus Mismatch and one bogus "No claim logged". Any patient who both calls in and is called back can trigger it. **Mitigated for display only** — `verdict_review.py` routes any incoming call bearing a claim to a `SUSPECT JOINS — DO NOT TRAIN ON THESE` section and excludes it from the match rate. **The join itself is NOT fixed.** See §124.5.
- **D159** (incident, `CALLHOOK_SECRET_MISMATCH_403` — RECURRENCE) The §94.1 outage returned. The MyOperator panel has been sending the OLD 12-character `@`-bearing key since 06-Jul 13:41; the S94 panel edit survived exactly one verification call (4 successful deliveries at 16:28–16:35 on 07-Jul) and then reverted. 1,074 rejections on 06-Jul, 2,744 on 07-Jul, 631 on 08-Jul — **every one silent.** Fixed by aligning the VPS to the panel (`CALLHOOK_SECRET` in `/root/wa/.env` set to the panel's decoded key; `call-hook.service` restarted 10:28:32; 200s from 10:29:17). **Deliberate temporary trade: the clinic is back on the old secret.** Proper rotation, both ends, verified across a full clinic day, is on the backlog. See §124.3 and the incident report.
- **D160** (governance) **The live Apps Script project is the canonical source of the dashboard, not GitHub.** The committed `Dashboard.html` was 84,427 chars; the live one is 152,984 and contains the entire duration gate. Two diagnoses this session were made against the stale copy and were WRONG. **Rule: every EOS that touches the dashboard commits the live Apps Script export.** See §124.6.

## §124 SESSION 124 — Verdict Analysis Layer BUILT · duration gate FAILS OPEN · the 403 outage recurs (08 Jul 2026)

**FULL EOS — one new VPS script, one live dashboard file replaced, one live `.env` secret realigned.**
Decisions **D155–D160**. The session began as a build (D154) and turned into a live-fault repair
that changed how the clinic's staff-facing gate works forever.

### §124.1 — Verdict Analysis Layer BUILT (D155)
`verdict_review.py` — new, at `/root/wa/recordings-archive/`. md5 **`af6622e4edc3f454cf0bfed128c4f76b`**,
1364 lines, selftest **117/117**, `py_compile` clean, **₹0 (no AI calls)**.

- **Reads** `Call_Verdicts` (header-verified; refuses to run on a changed layout) + each row's
  transcript from Drive. **Writes** two NEW tabs it alone owns: `Verdict_Review` and `Doctor_Verdicts`.
  `Call_Verdicts` is never written to — grep-verified, and asserted in the selftest.
- **`Verdict_Review`** — rolling 7 days, fully redrawn each run. Sections, in order:
  **1 FLAGGED** (clinical/safety — drawn first, whatever else the row is) · **2 MISMATCH** (includes
  Partial) · **3 AI-LOGGED-STAFF-DIDN'T** · **4 UNCLEAR** · **5 SUSPECT JOINS** (see D158) ·
  **6 MATCHES** (one line each). Each card ≈ one screen, followed by the **full transcript in a
  COLLAPSED row-group** with the AI's evidence excerpt located by fuzzy match and highlighted; when
  the excerpt cannot be located verbatim the card SAYS SO rather than highlighting the wrong line.
- **Two editable cells per card:** a dropdown chosen by call direction (the 11 outgoing / 9 incoming
  live-dashboard codes + `UNCLEAR`, `cannot_judge`, `transcript_bad`) and an optional free-text note.
- **`Doctor_Verdicts`** — append/upsert, keyed on Join Key. This is the ground-truth ledger for the
  voice-bot KB and the autonomous-judge calibration. Its de-identified export is **v1.1, deliberately
  deferred** (Stage-4's de-identify-first rule; the de-identifier is unbuilt).
- **The safety order:** HARVEST the doctor's typed answers into `Doctor_Verdicts` **first**; only then
  delete and redraw. Anything that fails in the harvest exits before the destroy. Answers already in
  `Doctor_Verdicts` are pre-filled back into the redrawn cards.
- **PHI:** the rolling window means a transcript leaves the tab as its call ages out — compliant with
  the LOCKED 90-day raw-transcript purge (Voice Bot Stage 2a) without the purge job knowing this tab
  exists. The hidden machine column stores an **opaque token**, not the Join Key, so a CSV/XLSX export
  of the tab carries no phone numbers.
- **Not protected.** Whole-sheet protection was tried and removed: Google treats expanding a row-group
  as editing the sheet, so protection made every transcript unreadable. The tab is redrawn each run,
  so a stray edit is self-healing.

**First real run (06-Jul window):** 32 cards — 6 flagged · 4 mismatch · 8 ai-only · 13 unclear ·
1 suspect join · 13 match lines · 19 incoming-no-claim excluded. 29 usable transcripts, **3 empty**.
**Owner has refereed 0 cards so far — every accuracy claim about the AI remains unverified.**

### §124.2 — Three gaps the first real run exposed (upstream, in `call_verdict.py`)
1. **`Agent` is `(not recorded)` on 21 of 27 cards.** `call_verdict.py` takes the agent from the staff
   *claim* (`Handled By`), so every call without a matched claim is anonymous — including a card
   carrying a **conduct complaint against the doctor**. The agent extension is in `Call_Feed`; it must
   come from the call record, not the claim. **OPEN.**
2. **`Clinic ID` is blank on 100% of rows.** The D152 name/Clinic-ID fallback populates the name
   (19/27) but never the Clinic ID. That is the join key into patient data — no Clinic ID, no
   "last visit", no diagnosis, therefore **no doctor console**. **OPEN, and it blocks the console.**
3. **Safety-flagged calls could hide.** Three of the six flagged rows had `Match` verdicts (collapsed
   to one line) and two were incoming (excluded entirely). Fixed in `verdict_review.py` by the FLAGGED
   section, which outranks every scenario. **A flag is a clinical signal about a patient, never a
   statement about staff accuracy, and must never be hidden by a bookkeeping rule.**

### §124.3 — 🔴 INCIDENT: the call-webhook 403 outage RECURRED (D159), and the gate FAILED CLOSED (D156)
**Symptom (owner-reported):** follow-up tiles stuck on "⌛ Checking the call…" forever, surviving a
page refresh, after genuinely connected calls.

**Diagnosis chain (all read-only until the fix):**
1. `call-hook.service` up and healthy; `.env` `CALLHOOK_SECRET` clean (24 chars, alphanumeric, one
   line, no run-on). **Not §94.1's `.env` corruption.**
2. No `2026-07-08.jsonl`. But the receiver's secret gate **returns 403 before `raw_log()` is called**,
   so a missing raw log cannot distinguish "no delivery" from "rejected at the door".
3. The **web-server access log** settled it: `13.126.78.76`, `Go-http-client/2.0`, continuous
   `POST /mo-callhook` → **403**, 33-byte body (= the receiver's own `{"ok":false,"error":"forbidden"}`).
   Proxy config intact. MyOperator was delivering; we were rejecting.
4. Counts by date: **06-Jul 111×200 then 1,074×403 · 07-Jul 4×200 and 2,744×403 · 08-Jul 631×403, 0×200.**
   The four 07-Jul successes are Shavez's S94 verification call at 16:28–16:35. **The S94 fix held for
   seven minutes.**
5. The panel's key decoded to **12 characters containing an `@`** — the OLD secret, the exact one S94
   rotated away from. The panel edit never persisted.

**Fix:** aligned the VPS to the panel rather than editing the panel again (whatever rewrites the panel
cannot rewrite `/root/wa/.env`). `.env` backed up, `CALLHOOK_SECRET` rewritten via `awk`+`ENVIRON`
(guards: exactly one matching line, only the value changed, identical line count — the §94.1 run-on
trap made impossible), `chmod 600`, `systemctl restart call-hook.service`. `ActiveEnterTimestamp
10:28:32`; last 403 `10:28:02`; first 200 `10:29:17`; `2026-07-08.jsonl` created; `Call_Durations`
rows 101–107 written with real `bridged/answered/talk=37,23,26,15`.

**The clinic is back on the old 12-char `@` secret.** Deliberate, temporary. Rotation goes on the
backlog, to be done on **both** ends and verified across a full clinic day.

**Cost of the outage: two clinic days of outcome data**, because the duration gate blocked the outcome
dropdown whenever it could not measure a call. Hence D156.

### §124.4 — The `Dashboard.html` bugs, and what actually caused "forever" (D156)
Read from the **live Apps Script export**, not the repo (see D160). Two distinct defects:

- **Bug A — result states were never persisted.** Only `fuCalled` and `fuRefId` went to
  `localStorage`; `fuTalked` / `fuMissed` / `fuTimeout` lived in page memory. Every reload therefore
  re-rendered a called tile as "Checking the call…" and restarted a fresh 3-minute timer. **For anyone
  who refreshes, the spinner was permanent.** This is the reported symptom.
- **Bug B — a call with no `reference_id` spun forever, literally.** `fuMarkCalled(rid, res.reference_id||'')`
  persisted the tile as *called with no ref*; `fuResumePolls()` then skipped it silently
  (`if(fuRefId[rid] && …)`), `fuStartPoll()` had a bare `if(!ref) return;`, nothing ever timed it out.
  No poll, no timeout, no escape across every reload until `localStorage` was cleared by hand.

**`Dashboard.html` v18.19** (md5 `034529a124c6bfab8aec2b675620dfec`, 2,738 lines, `node --check` clean
on the extracted script, 16/16 invariant checks): all six states persist; the timeout is measured from
`fuPlacedAt` (the call) not the page load; both `if(!ref)` paths call `fuSetTimeout()`; the day key is
local (IST) not UTC, which flushes the stuck entries once on first load. And the substantive change —
**the gate FAILS OPEN on couldn't-measure**, offering the dropdown behind an "unverified" banner, while
a call measured as *not connected* still blocks. `fuSave`, `triggerCall`, `getCallDuration`,
`WebApp.gs` and `CallConsole.gs` are untouched. Deployed by the owner (edit existing deployment → New
version); build stamp confirmed `v18.19 · S124`.

### §124.5 — Two corrections to the Session-123 record (D157, D158)
S123 recorded "22 outgoing with a claim / 40 incoming correctly No-claim, 16/5/1, 73%". The live
`Call_Verdicts` crosstab says otherwise: **36 outgoing, 26 incoming.** The "40" was the number of rows
with **no claim**, of which only **19** were incoming. Of 20 outgoing-with-claim: **16 Match, 4
Mismatch → 80%.** The fifth "mismatch" was an **incoming call carrying a claim**, which by D153's own
principle is impossible — it is the D158 false join. **D153's principle stands; its arithmetic did not.**

### §124.6 — Governance: the repo is not the dashboard (D160)
`dashboard/Dashboard.html` in GitHub: 84,427 chars, no duration gate, stamped v18.18. The live file:
152,984 chars, gate included. Two diagnoses this session were made against the stale copy and were
wrong — including a confident claim that the `reference_id` lived only in page memory (it is in fact
persisted). **The live Apps Script export is now committed with this EOS and must be committed with
every EOS that touches the dashboard.**

### §124.7 — What today proved about verification itself
The S94 fix was recorded as *"Verified end-to-end. Outage closed."* on the strength of **one call**.
It was dead seven minutes later. **A single successful call, taken immediately after a change, cannot
distinguish "fixed" from "fixed for one call."** New standing rule: a fix to a webhook, secret, timer
or gate is verified only after **one real call AND a re-check ≥1 hour later on the same clinic day**.

### §124.8 — Detection gap, still open
2,744 rejections passed through the server on 07-Jul and **nothing the clinic owns noticed.** The
receiver 403s before it raw-logs and before it prints to the journal. The only detector that has ever
fired for `CALLHOOK_SECRET_MISMATCH_403` is a receptionist. S94 named the fault code, wrote the
detection rule, and never built it — and it recurred in thirty-six hours. **Top diagnostics task.**

## §S125 — Dual-key acceptance, rejection visibility, and the end of the 403 blind spot
**08 July 2026 · Build session · Closes the S124 top task**

Session 124 closed with the `CALLHOOK_SECRET_MISMATCH_403` detector **specced and unbuilt**. Session 125 built it, ran it, used it to finish the forensics S124 could not, and then removed the fault's ability to cause an outage at all.

**The detector, at last.** `callhook_watchdog.py` v1.0 lives at `/root/wa/call-hook/callhook_watchdog.py`. It reads the OpenLiteSpeed access log — the only place a rejected webhook delivery is visible — and answers the question the raw log cannot: *did nobody call, or did we refuse everyone?* Read-only; it writes nothing unless `--state` is passed. Six fault codes, four severities, keys handled only as opaque `key_<md5[:6]>` labels with no unmask flag. 37/37 offline selftest on the VPS interpreter.

**What it proved in one line.** Run at 14:11 on 08 Jul: `115 accepted (200) / 635 rejected (403)`, and `keys seen : key_271f88 (115 ok / 635 rejected)`. **One key label, carrying both the rejections and the acceptances.** MyOperator sent the identical string across all 750 requests. Nothing about the sender changed at 10:28 — only the value on the VPS did. The second-webhook-subscription theory, S124's leading suspicion, is dead for 08 Jul: `CALLHOOK_MULTIPLE_KEYS` did not fire, and it would have.

**The `7e17f7` anomaly.** `/root/wa/.env.bak_20260707_162509` holds a `CALLHOOK_SECRET` value of **61 characters**, non-alphanumerics `@ _ _ =` in that order, with `strip()` changing nothing. Not a smudge, not a third key. It is the 12-character `@` key with a `FU_UPLOAD_SECRET=<32-char value>` fragment attached: `12 + 17 + 32 = 61`, to the byte. Found by a routine secrets sweep of the cold kit, matching on `FU_UPLOAD_SECRET` in a file nobody had opened in fourteen sessions.

> **[S126 CORRECTION]** S125 attributed this to a **lost newline**. That is retracted. See §S126 and **D166**. The composition above is settled; the **mechanism is UNKNOWN**.

**Therefore the outage was TWO faults, not one — and `sed` was the repair, not the cause.**

*Window 1 (06 Jul 13:41 → 07 Jul 16:28).* The corrupted line. **Dormant** — real and asleep — until a worker respawn re-read `.env` at 13:41 on 06 Jul. No restart, no reboot, no journal entry; nothing human selected that moment.

*Window 2 (07 Jul ~16:35 → 08 Jul 10:28).* S94's `sed -i '17s'` **removed** the run-on and installed a clean alphanumeric key; the panel was edited; **four deliveries returned 200 at 16:28–16:35. The fix worked.** Then the two ends came apart again within minutes. **How, is still unknown.** A second webhook subscription is disproven for 08 Jul; that the 16:28 panel edit never saved is not excluded.

> **[S126]** The journal shows **no worker respawn between `07 Jul 16:28:04` and `08 Jul 10:28:33`** — the whole of Window 2. The worker held one secret in memory throughout, so the VPS side could not have changed. This points hard at the panel. **Not proven:** `tail -3` did not rule out an unprinted respawn. See §S126 and backlog item 5.

**Retractions (S125).** Incident v1 §6 stated the fix avoided *"`sed` by line number, which is what created §94.1's run-on line"* — the causal direction is **inverted**. S124 §3.2's *"exactly one line, no run-on"* inspected `.env` **after** the repair. S124 §4's *"the VPS was correct throughout"* is false for Window 1. And a mid-session assistant claim that the encoding defect "didn't bite" was wrong: it had bitten, invisibly.

**The encoding trap.** The live `.env` value labels as `key_db8972`; the access log labels the same key as `key_271f88`. Two hypotheses were live: benign percent-encoding of the `@`, or `.env` and the running worker had **diverged again**, arming a second dormant outage. Resolved by test, not assumption — `urllib.parse.quote()` of the `.env` value reproduces the access-log label exactly. Benign. Recorded as **D165**.

**The structural fix.** `call_hook_capture.py` **v2**, live 08 Jul 14:49:12. Three changes, all inside the secret gate; an AST diff confirms `extract_record`, `record_to_row`, `upsert`, `_connect_store`, `store_handle`, `raw_log`, `to_ist_iso`, `_find_sa_key`, `_load_env` and `home` are byte-identical to v1. The gate accepts `CALLHOOK_SECRET` **or** `CALLHOOK_SECRET_PREV` in constant time (**D162**); a delivery on the previous key logs a WARN naming the masked label; a refusal is written to `call_hook_rejects/YYYY-MM-DD.jsonl` **before** it is refused (**D163**), metadata only, throttled to the first 500 per day then 1 in 100; and startup warns if the secret contains whitespace, an `=`, or exceeds 40 characters (**D164**). 43/43 offline selftest. Proven live by a keyless probe: 403, and exactly one reject-log line.

**Why the fault was dormant, which is the heart of it.** `gunicorn -w 1` with no `--preload`: the worker reads `.env` once, at import. An edit takes effect at the next respawn — hours or days later, with no restart, no reboot, no journal entry linking cause to effect. On 06 Jul that respawn came at 13:41. **This was never a careless-edit problem. It was a system that permitted a careless edit to remain invisible for 44 hours.** A perfect edit applied to only one of the two places the secret lives would have produced the same outage.

**Still open at S125 close:** rotate `CALLHOOK_SECRET` · the watchdog's two defects · 115 accepted vs 114 raw-log lines · what if anything reverted the panel in S94.

---

## §S126 — The housekeeping that broke the record five times
**08 July 2026 · Build session (code changed; no restart, no key touched) · Rotation still unstarted**

Session 126 was convened to rotate `CALLHOOK_SECRET`. **The key was not touched. `.env` was not written. Nothing was restarted.** The session ran the six data-safety measures Runbook v59 placed before the rotation, and five recorded facts failed against the disk.

**A fifth truncated document.** `KB_APPEND_Session125.md` ends mid-sentence inside its §3. The runbook (v59) and the incident report (v2) are intact. The procedure was not reconstructed from memory. **A numbering gap surfaced:** KB v1.48 carries D121–D160 and says *"next free: D161"*; the S125 append is headed *"append after D161"*. **D161 exists in neither.**

**The record was wrong by one byte, and had been for sessions.** The live `call_hook_capture.py` was **30,749** bytes, not 30,750. 690 lines, final byte `\n` (confirmed by `od -c`), so the file terminated properly and no newline was missing. Because the repo's `31,100` came from the same record, the claimed 350-byte delta was unverified in both directions. Measured, not trusted: **the true delta is 351 bytes, 5 lines.**

**The "lost newline" explanation is dead.** `/root/wa/.env.bak_20260707_162509` (1327 bytes, 29 lines, mode 600) shows `CALLHOOK_SECRET len=61` **and** `FU_UPLOAD_SECRET len=32` — the latter present, on its own intact line. **A lost newline merges two lines; it consumes the second. That line survived.** The 61 characters therefore arrived by **duplication: text inserted, nothing deleted.**

Composition remains settled — `12 (@ key) + 17 ("FU_UPLOAD_SECRET=") + 32 (alnum value) = 61`, non-alphanumerics `@ _ _ =` in that order. **Mechanism is UNKNOWN.** A `sed` overrun, a stray append, an editor, a botched heredoc paste all produce insertion-without-deletion; the evidence distinguishes none of them. This is the **third** explanation offered for these characters: `sed` (incident v1, retracted S125), lost newline (S125, retracted S126), duplication-of-unknown-origin (S126, and it is a *class*, not a mechanism). Both retracted causes were plausible, written down with confidence, and survived because nobody opened the file. **See D166. Record no third cause.**

**A prediction failed and is recorded rather than dropped.** The assistant predicted the forensic backup at ~1465 bytes, *larger* than the live 1416. It is 1327 — smaller by 89. The sign was wrong (a lost newline removes a byte; it does not add bulk), and the method was worse: it compared the sizes of two files differing in several places and attributed the difference to the one line under discussion. The `12+17+32=61` reconstruction rests on the value's length and character order, not on file size, and is unaffected.

**An unrecorded secret was found in the live `.env`.** `ANTHROPIC_API_KEY len=111`. Absent from the 07-Jul backup, therefore added between `07 Jul 16:25` and `08 Jul 10:28` — **inside the outage window** — by something nobody has identified. Mode 600, so not an emergency. But the gunicorn call-webhook worker now loads an Anthropic credential it has no use for, and no document mentions it. **Rotate it; move it out of that worker's environment; find out what wrote it.** The census that found it is now standard: **D169**.

**Six bytes are unaccounted.** `1416 − 1327 = +89`. `ANTHROPIC_API_KEY` line (+130), two blank lines (+2), `CALLHOOK_SECRET` 61→12 (−49) = **+83**. Every other key name and value length is identical across both files. Probably line termination. Logged, not waved off.

**The 115-vs-114 gap resolved into something smaller.** At 14:11: 115 accepted / 114 raw-log lines. At 21:20: **133 accepted / 132 lines.** Eighteen further deliveries, eighteen further lines, **offset still exactly one.** An ongoing defect would have widened it. **One historical event, not a mechanism that is still running.** Bounded and low-priority; benign explanations exist (a health probe; a line counted before it was flushed).

**Window 2, nearly settled, deliberately left open.** `journalctl … | grep "secret gate" | tail -3` returned three startup lines: `07 Jul 16:28:04`, `08 Jul 10:28:33`, `08 Jul 14:49:13`. Window 2 sits entirely inside the first gap. **The worker held one secret in memory across the whole of it** — `.env` could have been rewritten a hundred times and the worker would never have known. The VPS side could not have changed. The four 200s at 16:28–16:35 prove the worker's key matched the panel; the 403s from ~16:35 prove it stopped matching; the worker did not move. **This points hard at the panel.** It is **not recorded as proven**: `tail -3` did not rule out an unprinted respawn, and it is not established that v1 printed `secret gate` on every start path. One read-only command settles it, and it no longer depends on the watchdog's coverage guard or on log retention.

**The `.env` and the worker provably agree.** `cp -a` preserved the backup's mtime: `.env` was last written `08 Jul 10:28`, and the worker respawned at `10:28:33` — one deliberate act, the S124 repair, thirty-one seconds after `last 403 : 10:28:02`. Established three independent ways: the startup label (`key_db8972`, literal), the wire label (`key_271f88`, access log), and the mtime.

**Two rollback points, not zero.** Runbook v59 §7 warned the S125 `.bak` was "a copy of v2, not v1" and therefore "not a rollback point." True, and understated: it is a **valid rollback point to v2**. `cmp` proves `call_hook_capture.py.bak_20260708_144241` and `call_hook_capture.py.LIVE_v2_s126_20260708_212453` byte-identical, both 30,749. **v1 is not on the box** — GitHub and the cold kit only.

**A git trap, found armed.** The clinic PC had `core.autocrlf=true` with `.gitattributes` set to `* text=auto`: LF in the repository, **CRLF written into the working tree at every checkout**. A `git clone` followed by the Binary WinSCP upload that D164 mandates would have delivered **701 carriage returns** to the VPS, faithfully. **Binary mode prevents WinSCP from *adding* CRs; it does nothing about CRs git already wrote.** Unfired only because the working copy had arrived by some route other than a checkout. Closed at source: `core.autocrlf false` (repo-local) and `*.py text eol=lf` in `.gitattributes`, which travels with the repo and overrides any user's config. **See D167.**

**The upload was stopped because the repo's docstring was also wrong.** The repo candidate's header read *"run onto the end of it by a lost newline"* — disproven forty minutes earlier. The live header read *"the exact signature of a `sed -i` line-number edit"* — disproven in S125. Runbook v59 §2 states the rotation procedure is *"documented in the header of `call_hook_capture.py`"*; that header is a canonical document. Installing the candidate would have swapped one retracted causal story for another, in a canonical document, on the live box, on the evening the second one was disproven. **A corrected full file was written instead.**

**And the diff was read, hunk by hunk, for the first time.** Three hunks: a docstring, one `log()` string, one trailing blank line. `2→12`, `2→2`, `+1`. `690 + 11 = 701`; `30749 + 741 = 31490`. Nothing hidden. **The long-repeated claim "executing code is identical" is now verified rather than asserted.**

**Installed 21:55 IST via candidate path, never by overwriting** (**D168**): upload to a distinct filename → `diff` against running code → `py_compile` on the VPS interpreter → `--selftest` → validate the rollback point with `cmp` **immediately before** the atomic `mv` → re-verify the *installed* file. Final: **31,490 bytes, 701 lines, `CR = 0`, final byte `\n`, md5 `beafccafbf7e81aa5f2736be939b2bbb`, 43/43 selftest on the installed file.** Last section asserted by reading it.

**The running worker still executes the pre-21:55 bytes.** It imported at `14:49:13` and will not notice the swap. The new header becomes real at the next respawn — **rotation step 1**. The same dormancy that took the clinic down on 06-Jul, deliberately induced, known, with a chosen resolution time.

**Not one of these findings came from reasoning.** Every one came from looking at the disk. Five recorded facts failed; a sixth — the byte count — had been repeated across sessions unchallenged.

**Still open at close:** rotate `CALLHOOK_SECRET` (unstarted; the key is still exposed in a chat transcript) · `ANTHROPIC_API_KEY` unaccounted in `.env` · the watchdog's two defects · Window 2's cause, one read-only command away · six unexplained bytes · D161 unaccounted · 133 vs 132.

---

## §S127 — The rotation moves: steps 1 and 2 done, and the KB bump correctly refused
**08–09 July 2026 · BUILD session (`.env` written, service restarted, new VPS script) · Spans two calendar days; the 08-Jul chat froze after step 1 and was recovered from the disk on 09-Jul**

Two sessions were convened to rotate `CALLHOOK_SECRET` and both spent themselves on documentation. This one moved it. The key is not yet dead — but it is now killable at leisure, with no outage available to it.

**The KB bump was attempted, and correctly refused.** `v1.48` was placed in uploads so the shell could read it — the condition `KB_APPEND_Session126.md` §0 set for a mechanical, verifiable bump. The shell read it, and then read the *target*. `KB_APPEND_Session126.md` §4 names three lines to REPLACE in `§12`. **None of the three is in `§12`.** §12 occupies lines 48–80 and is the verbatim `v1.38` base, unchanged since Session 64. The §12 that §4 was written against exists only in an author's mental model, assembled from the runbook's §1/§2 — *the same failure the whole S125–S126 arc is about: a document described from memory of what it should contain, and nobody opened it.* Executing §4 would have required *choosing* where three lines go, which is a judgement, and per **D166** a judgement is not made silently inside a canonical document. `KB_SWAP_BLOCKER_S127.md` was written instead. It decided nothing.

**What the blocker established by measurement, not by quoting the record:** `v1.48` is 107,061 bytes / 1,327 lines / CR = 0, no evidence of truncation (the first time the repeated "107 KB" was ever verified). **`D161` never existed** — reserved and skipped, in neither v1.48 nor the S125 block. `D155`–`D160` are orphaned at lines 1132–1137, outside a DECISIONS INDEX whose heading claims to run to `D160` but which stops at `D154`. Line 1 read `v1.47` in a file that is `v1.48` throughout. An early `grep` miscounted and was about to report a duplicated `D121–D145` block; **the claim was checked before it was stated**, and it was wrong.

**Rotation step 1 — 08-Jul 23:38:00.** `CALLHOOK_SECRET_PREV` appended equal to `CALLHOOK_SECRET`, by `printf`, never `sed` (D164). Restart. Both variables identical, so no key the panel could send would be refused: **that is what made a 23:30 restart safe.** The startup line came back with a fresh timestamp — `Phase B receiver v2 (dual-key) … previous=SAME AS CURRENT (rotation not started; harmless)`. **The 21:55 bytes were finally executing.** The dormancy induced deliberately at 21:55 on 08-Jul — the same mechanism that took the clinic down on 06-Jul, this time understood and with a chosen resolution time — ended here. The chat froze immediately afterwards. Nothing was lost: it was all on the disk.

**Recovery, 09-Jul.** Service `active`, PIDs `867880/867881` — **the identical master and worker that booted at 23:38.** No respawn in nine hours. `call_hook_logs/2026-07-09.jsonl` present and growing; `call_hook_rejects/2026-07-09.jsonl` **absent**. Step 1 verified under nine hours of real clinic traffic.

**A `0` that meant nothing.** `journalctl --since "23:30 yesterday"` printed `Failed to parse timestamp` and emitted nothing; `grep -c` counted the `PREVIOUS key` lines in that nothing and returned `0`. **A check that cannot fail is not a check** — precisely the watchdog's own coverage defect, reproduced by hand in a shell. Re-run with `--since "2026-07-08 23:30"` and a `wc -l` coverage guard in front of it: **58** journal lines, **0** PREV-key acceptances, `exit=1` (grep's normal zero-count signal, which is why these are chained with `;` and never `&&`).

**`rotate_callhook.sh` was written, because the human was the bottleneck.** The owner's objection was correct and is now a design rule (D171): *"again i am doing lot of un ending cmd job."* Forty commands, each needing him to read an exit code and decide whether it was the good kind. Every one of those judgements is mechanisable, and a script that **refuses** is strictly safer than a human who **approves**. `stage` runs eleven guards and deletes its own candidate if any fails; `.env` is never touched until `install`, which re-runs them all and `cmp`-validates the rollback point at the instant before the atomic `mv`.

**Two predictions, two misses, both caught by the check.** Told to expect **12** function definitions, the file returned **11** — the pattern `^[a-z_]*(){` excludes digits, and `since2()` has a digit. Told to expect **3** startup branches, `grep` returned **4**. Neither was a fault in the file. Both were the assistant predicting a file's contents from memory of having written it, rather than deriving the expectation from the artefact. The same class as `30,750` bytes repeated across five sessions. **D172.**

**And the fourth branch mattered.** Reading twenty-six lines of `_startup_connect()` — instead of trusting the runbook's quoted phrase — answered three questions in one command. It confirmed `-> ROTATION IN PROGRESS` is the real string. It revealed a fourth branch, `current=(unset!)`, recorded nowhere. And line 545 reads **`if SECRET and SECRET_PREV:`** — an empty string is falsy in Python, so **`CALLHOOK_SECRET_PREV=` with nothing after it behaves identically to an absent line.** Step 4's open question, budgeted for a whole session, cost one `sed -n`. **D170.**

**Rotation step 2 — 09-Jul 09:05:58.** Key generated on the VPS, into the candidate by `awk`+`ENVIRON`, never through a terminal echo, never into this chat. Eleven guards green. Backup `.env.bak_s127_step2_20260709_085801` `cmp`-verified byte-identical *at the instant before* the `mv`. Startup: `current=key_ea20dd  previous=key_db8972  -> ROTATION IN PROGRESS`.

**Then the thing that had never been tested.** Until 09:05 both variables held the same value, so every delivery matched `CALLHOOK_SECRET` first and **the previous-key acceptance branch had never accepted a real webhook.** It had passed 43/43 in a selftest. That is not the same thing. At 09:35: **64 calls accepted today · 12 on the previous key in 30 minutes · `refused today: none`.** Twelve real webhooks fell through to `CALLHOOK_SECRET_PREV` and were accepted. **D174.**

**Steps 3 and 4 are open, and step 4 is deliberately withheld.** The panel was not updated — the owner parked it. Nothing is pending: both keys work, indefinitely, which is the entire purpose of the gate. The step-4 command exists nowhere, because clearing `PREV` before the panel moves would rebuild the 06-Jul outage by hand. **D173.**

**Not one finding this session came from reasoning. Every one came from looking at the disk.**

---

## DECISIONS D162–D175 — FULL TEXT (Sessions 125–127)

**D162 — Dual-key acceptance is mandatory for any shared-secret gate.**
*08 Jul 2026, S125.* A secret held in two places must be rotatable without a synchronised cutover. The call-webhook receiver accepts `CALLHOOK_SECRET` **or** `CALLHOOK_SECRET_PREV`, compared in constant time. A stale worker and a fresh worker both work; the panel and the VPS may disagree indefinitely; the disagreement surfaces as a WARN line naming the key in use, rather than as a receptionist reporting stuck tiles. **Generalises to `WA_APPROVE_KEY`, `FU_UPLOAD_SECRET`, and every future shared secret** — any secret read once at import in a single-worker process is a mine with an unknown fuse.

**D163 — A gate must write down its refusals before it refuses.**
*08 Jul 2026, S125.* The implementation of Diagnostics Category 5. `call_hook_rejects/YYYY-MM-DD.jsonl`, dir 700, files 600. Metadata only: timestamp, reason, masked key label, key length, source IP, method, path. **Never the key, never the body.** Throttled — full detail for the first 500 refusals per day, then 1 in 100 — so a refusal storm is visible without being able to fill the disk. A gate that refuses silently is indistinguishable from a world that never called.

**D164 — `.env` is never edited by line number, and its contents are validated at startup.**
*08 Jul 2026, S125.* `sed -i '<N>s|…'` is prohibited: position-dependent, unverifiable after the fact, mangles escapes. Use `awk` + `ENVIRON` or `printf` to append.
**Correction to the rationale this rule was first given.** The `sed` did **not** create the 61-character run-on; `sed -i '17s'` was S94's repair, which removed it. The rule stands on its own merits, not on that story — and the story is now on the record as an example of how a plausible causal claim survived two sessions and one incident report unchallenged. *(S126: the replacement story — a lost newline — is also retracted. See D166.)*
**WinSCP transfers of `.env` and of any `.py` must be Binary, never Text** — Text mode appends `\r` to every line. Verify after any upload: `file <path>` says `ASCII text`; `grep -c $'\r' <path>` says `0`. *(S126: necessary but insufficient — see D167.)* The receiver warns at startup if its secret contains whitespace, an `=`, or exceeds 40 characters, which would have caught the run-on the moment a worker read it, in Window 1, before any clinic day was lost.

**D165 — Masked key labels must be encoding-normalised before comparison.**
*08 Jul 2026, S125.* An md5 label of a wire-format key and of the same key in literal form are different strings. The Go client percent-encodes `@` as `%40`; Flask decodes it before the receiver compares. The same key labels as `key_271f88` in the access log and `key_db8972` in `.env`. Any tool comparing labels across sources must `urllib.parse.unquote()` first. Cost roughly an hour on 08 Jul and briefly presented as a live second outage.

---

> **Note on numbering.** KB v1.48 records D121–D160 and states *"next free: D161."* No D161 exists in v1.48 or in the S125 append block, which is headed *"append after D161."* **D161 is unaccounted for.** D162–D165 (S125) and D166–D169 (S126) are correct and unaffected. **Next free decision number for new work: D170.**

**D166 — No cause is recorded unless the evidence distinguishes it from its rivals. `UNKNOWN` is a valid, and sometimes the only honest, entry.**
*08 Jul 2026, S126.* The 61-character `.env` value has had three explanations. `sed` overrunning its delimiter (incident report v1 — retracted S125, because `sed -i '17s'` was S94's *repair*). A lost newline (S125 — retracted S126, because `FU_UPLOAD_SECRET len=32` survives on its own intact line in `.env.bak_20260707_162509`, and a lost newline consumes the line it merges). And "a duplication" — which is not a mechanism but a *class* of them: a `sed` overrun, a stray append, an editor, a botched heredoc paste all fit equally. **The evidence chooses none.** Both retracted causes were plausible, were written down with confidence, and survived because nobody opened the file. A knowledge base that cannot say `UNKNOWN` will fill the gap with the most recent guess and then defend it. **Composition may be recorded (`12 + 17 + 32 = 61`, non-alphanumerics `@ _ _ =` in that order). Mechanism may not.**

**D167 — A control that guards one path into a hazard is not a control on the hazard.**
*08 Jul 2026, S126.* D164 mandates WinSCP **Binary** transfers for `.py` and `.env`, to stop WinSCP appending `\r`. Correct, and insufficient. The clinic PC had `core.autocrlf=true` with `.gitattributes` set to `* text=auto`: LF in the repository, **CRLF written into the working tree at every checkout**. A `git clone` followed by the Binary upload the runbook prescribes would have delivered 701 carriage returns to the VPS, faithfully. **Binary mode prevents WinSCP from *adding* CRs; it does nothing about CRs git already wrote.** Fixed at source: `core.autocrlf false` (repo-local, clinic PC) and `*.py text eol=lf` in `.gitattributes`, which travels with the repo and overrides any user's config. **Generalises: when a rule names a tool, ask what else can produce the same byte.**

**D168 — Live code is never overwritten to be tested. Candidate path → diff → compile → selftest → atomic `mv`.**
*08 Jul 2026, S126.* Upload to a distinct filename beside the live file. `diff` it against the *running* code and **read every hunk** — "the difference is only a docstring" had been believed for sessions and had never once been checked; when it finally was, it was true, and it was also about to install a retracted causal claim into a canonical header. `py_compile` and `--selftest` on the VPS interpreter, not the author's. Validate the rollback point with `cmp` **immediately before** the `mv` that destroys the file it would roll back to — a backup you have not compared at the moment of use is a belief about the past. `mv` on one filesystem is atomic; there is no instant of a half-written file. Then **re-verify the installed file**: compiling a candidate and installing something are two different acts. **Verify by reading the file's last section. Never by hash alone — a hash proves two files match; it cannot prove either is complete.**

**D169 — Secrets are inventoried by name and value length, never by value.**
*08 Jul 2026, S126.* Run at every EOS, against `.env` and every `.env.bak_*`:
```
awk '/^[A-Za-z_][A-Za-z0-9_]*=/ { n=index($0,"="); printf "  %-24s len=%d\n", substr($0,1,n-1), length($0)-n }' <envfile>
```
A complete census with nothing secret on the screen, in a transcript, or in a scrollback buffer. It is how `ANTHROPIC_API_KEY len=111` was found sitting unrecorded in the call-webhook worker's environment, added during the outage window by something nobody has identified. It is how `CALLHOOK_SECRET len=61` was confirmed *alongside* an intact `FU_UPLOAD_SECRET len=32`, which is what killed the lost-newline theory. **An unknown secret in a live process's environment is a fault, whether or not it has caused one yet.** Also: every `.env.bak_*` holds a real key. `chmod 600`, never delete the forensic ones, treat all of them as secrets.

---

**D170 — For `CALLHOOK_SECRET_PREV`, empty and absent are the same state. Read from the source, not assumed.**
*09 Jul 2026, S127.* `_startup_connect()` line 545 reads `if SECRET and SECRET_PREV:`. In Python an empty string is falsy, so `CALLHOOK_SECRET_PREV=` with nothing after it falls through to `elif SECRET:` and prints `previous=(unset)`. **Rotation step 4 is therefore a one-line `.env` edit plus a restart**, not the design question a whole session had been reserved for. It cost one `sed -n '540,565p'`. The generalisation: before reserving a session to *decide* how a program behaves, spend one command *reading how it behaves.* The same read revealed a fourth startup branch — `current=(unset!)  previous=…` — that no document had recorded.

**D171 — A multi-step production rotation is executed by a guarded script, not by a human reading exit codes.**
*09 Jul 2026, S127.* `rotate_callhook.sh` (`status` · `stage` · `install` · `rollback`). The owner's objection was the design input: *"again i am doing lot of un ending cmd job."* Roughly forty commands had been issued across two sessions, each requiring him to read output and judge whether `exit=1` was the good kind — and `grep -c` exits 1 on a legitimate zero count, so it frequently was. **Every one of those judgements is mechanisable, and a script that refuses is strictly safer than a human who approves.** `stage` runs eleven guards, never touches `.env`, and deletes its own candidate on any failure. `install` re-runs all of them, `cmp`-validates the rollback point at the instant before the atomic `mv`, and reads the startup line back. Keys appear only as `key_<md5[:6]>`. **Generalises: any procedure that has been walked by hand twice should be walked by a script the third time, with the guards the human was performing written into it.**

**D172 — A check's expected value must be derived from the artefact, never predicted from memory of it.**
*09 Jul 2026, S127.* Twice in one hour: a function count predicted as `12` returned `11` (the pattern `^[a-z_]*(){` excludes digits; `since2()` has one), and a startup-branch count predicted as `3` returned `4`. Neither file was defective. Both times the expectation was asserted from memory of having authored the thing being checked. **A check whose expected value comes from memory can confirm a belief; it cannot catch an error, because a wrong file and a wrong expectation agree.** Same class as `30,750` bytes repeated across five sessions and never measured. Extends **D166**: it is not enough to write `UNKNOWN` where you do not know — you must also refuse to write a number you have not read. *Both misses were caught, because the artefact was read anyway.*

**D173 — Rotation step 4 must never precede step 3, and the command is withheld until it can.**
*09 Jul 2026, S127.* Clearing `CALLHOOK_SECRET_PREV` while the MyOperator panel still sends the old key refuses **every** delivery — the 06-Jul outage, reconstructed by hand, from a position of safety. The step-4 command is therefore **deliberately absent** from `rotate_callhook.sh`, from the KB, and from the runbook. It is issued only after two clean `status` checks, **at least an hour apart, on the same clinic day**, showing `on PREVIOUS key/30min = 0` and `refused today: none`. **An incident is closed by a successful re-test, not a successful test** (S94: the panel edit survived exactly one verification call, then reverted, and cost two clinic days). Parking step 3 parks step 4. The two are one unit.

**D174 — A selftest is not a production verification.**
*09 Jul 2026, S127.* The dual-key receiver's previous-key acceptance branch passed **43/43** offline and had, until 09-Jul 09:05:58, **never accepted a real webhook**. Before step 2 both `.env` variables held the same value, so every delivery matched `CALLHOOK_SECRET` on the first comparison and the branch was dead code in production. Step 2 armed it and 12 real deliveries exercised it within 30 minutes — `refused today: none`. **Any code path that only fires during an exceptional state is unverified until that state is entered on live traffic, however green the selftest.** Enter such states at a moment you choose, with a rollback validated, during hours when the failure would be seen.

**D175 — `§12` is frozen as a historical artefact; `§12A` carries current state and wins.**
*09 Jul 2026, S127.* Resolves judgement 1 of `KB_SWAP_BLOCKER_S127.md`. `§12`'s own heading reads *"UNCHANGED since Session 64 close"*; rewriting it would destroy the only record of that baseline and would be a deletion inside a canonical document. Instead **`§12A` is added immediately after it**, additively, and supersedes it wherever they disagree. Judgement 2 and 3: `D155`–`D160` are **re-homed by reference, not by movement** — the DECISIONS INDEX gains a continuation block pointing to where they physically sit; nothing is cut and re-pasted. Judgement 4: line 1 corrected to `v1.49`, and **an explicit end-of-file assertion is added** — the KB was the only canonical document without one, and the one that could not be verified any other way. **Every operation in the v1.48 → v1.49 bump was additive except the title line.** Byte and line counts asserted before and after, from the shell.

---

## §S128 — The rotation is PARKED, deliberately, with its exposure bounded
**09 July 2026 · EOS-LIGHT (no code changed · `.env` untouched · nothing restarted) · Rotation steps 1–2 remain complete; steps 3–4 parked**

Sessions 125, 126 and 127 were convened around one 12-character secret. Session 128 was opened to continue, and the owner stopped it:

> *"If both keys are doing their job, then I'm not interested in this ping pong of pasting commands and then pasting the output to you just for more security."*

**He is right, and the record should say so plainly.** The rotation is parked by owner decision. Not abandoned. Not pending. Not to be raised at session start.

### The one status reading taken this session

```
service               active
listening             1
CALLHOOK_SECRET       len=24   key_ea20dd
CALLHOOK_SECRET_PREV  len=12   key_db8972
accepted today        66 calls
refused today         none
on PREVIOUS key/30min 2
startup line          (blank)
```

Every line is the expected value for *"steps 1–2 done, panel not yet moved."* The blank `startup line` is the known cosmetic defect (`status` looks back only two minutes), **not** a fault. `on PREVIOUS key/30min = 2` is the dual-key gate working as designed: the panel still sends `key_db8972`, the receiver still accepts it, and the WARN lines are the instrument.

### The bound of the exposure — written down once, so it is never re-litigated from fear

`CALLHOOK_SECRET` gates **exactly one capability**: an HTTP POST to the call-webhook receiver (`127.0.0.1:8098`, behind OLS). A holder of the key can **inject or replay call rows into `Call_Feed`**.

It confers **no** read of patient data, **no** ability to place a call, **no** access to the tracker sheet, the dashboard, the recordings, the transcripts, or the MyOperator panel. It is a **data-integrity** exposure, **not a breach**. Two exposed keys are the same class as one.

**The real cost of parking, stated honestly:** injected rows would be indistinguishable from real calls at the receiver, would enter `Call_Feed`, and would be transcribed and judged by the Stage-3 AI layer. The exposure is therefore *bounded*, not *nil*. Nothing observed suggests it has been exercised: `refused today: none` across every reading since 08-Jul, and the accepted-vs-raw-log offset remains the single historical unit (§S126, item 8).

**Why parking is safe rather than merely tolerable:** the dual-key gate (**D162**) was built precisely so that the panel and the VPS may disagree **indefinitely**. Nothing is pending on the owner, on Lokesh, or on a timer. Nothing degrades. **There is no clock on this.**

### What actually caused this session's exposure

**Runbook v61 §5**, under *Session Hygiene Notes*, recorded that the key was *"read once by the owner off `grep '^CALLHOOK_SECRET=' /root/wa/.env | cut -d= -f2` for safekeeping."*

At S128 open the owner ran exactly that. The value went to a terminal, and from the terminal into a chat transcript.

**Three sessions were spent removing a secret from a transcript. One line of hygiene notes put a fresh one back.** The document written to protect the key instructed its disclosure. This is not an owner error. It is a document defect, and it is **D176**.

### The instrument that was missing all along

The deeper finding of this session is not about keys. It is that **the only way anyone could learn whether the live systems were healthy was for the owner to type commands and paste output.** Four sessions of "ping pong" were the symptom of a missing instrument, not of an impatient user. The remedy is `Health.gs` (see Runbook v62 §2, item 1): a daily self-report from the tracker itself, inside Google, requiring no terminal, no SSH, and no `.env`.

---

## DECISION D176 — FULL TEXT

**D176 — A procedure must never instruct a human to display a secret.**
*09 Jul 2026, S128.* Runbook v61 §5 contained a command whose standard output is a live credential, presented as hygiene. It was executed, as anything written in a runbook eventually is, and the key it protected was disclosed within one turn.

**Rule:** no canonical document — KB, runbook, incident report, SOP, spec — may contain a command whose output is a secret, in any form, including as a description of what was once done. Where a value must be retained, the **generating process** writes it to a mode-600 file on the box; it is never rendered to a terminal, a scrollback buffer, a chat, or a screenshot. `rotate_callhook.sh` already meets this standard for itself: it generates the key on the VPS and moves it into the candidate `.env` by `awk` + `ENVIRON` **specifically so it never crosses a terminal.** The runbook then undid that, in prose.

**Generalises: a hygiene note is executable.** A runbook is not a description of what was done — it is an instruction for what will be done next. Every command in it will be run by someone, in a hurry, with the output going somewhere neither author anticipated. Sibling of **D169** (secrets are inventoried by name and value length, never by value) — D169 governs what we *write down about* a secret; D176 governs what we *tell a human to do* with one.

**Consequence, recorded so step 3 cannot inherit the fault:** `key_ea20dd` is burned. When the rotation is resumed, `stage` must generate a **third** key. `key_ea20dd` must never be pasted into the MyOperator panel.

---

## PARKED ITEMS REGISTER (new, S128)

Items placed here are **decided, safe, and closed to session-start review.** They are not backlog. They are re-opened only when the owner asks, by name.

| Item | Parked | State | Bound / why parking is safe |
|---|---|---|---|
| `CALLHOOK_SECRET` rotation steps 3 & 4 | 09-Jul-2026, S128 | Steps 1–2 complete; dual-key gate live | Both keys accepted, `refused today: none`, no clock. Exposure is data-integrity on `Call_Feed` only — no patient-data read, no call placement, no panel access. Resume needs a clinic morning **and a third key** (D176). |
| `setDashboardKey` / `setStaffKey` closure (F-9) | 09-Jul-2026, S129 | ⚠️ **ORDERED LAST, NOT SILENCED** | Owner directive: assess blast radius before touching `WebApp.gs` (D34). **This is not a safe item and must NOT be closed to session-start review.** It is ordered last because the fix requires suspending D34, not because the risk is low. Bound: exploitation needs the `/exec` URL *and* the function name. The names are absent from the served page but present in the GitHub repo — **repo visibility is `UNKNOWN` and must be confirmed (Block A-0).** `removeTriggers` / `removeHealthTrigger`, the loudest of the group, close in Block A and need no D34 waiver. |

## §S128B — The instrument, the three defects it exposed in itself, and the audit that follows
**09 July 2026 · Same session as §S128 · BUILD (new Apps Script file `Health.gs`, live in the dashboard project) · No VPS code touched, no `.env`, no restart**

The owner's stated priority was not the rotation. It was: *"the staff facing callback tracker and the outcome logging goes on smoothly."*

**The finding underneath four sessions of command-and-paste:** the only way anyone could learn whether the live systems were healthy was for the owner to type into a terminal and paste the output. That is not a diligent process. **It is a missing instrument.**

### `Health.gs` — a heartbeat that can fail

Added to the **existing** Apps Script project bound to the Clinic Callback Tracker. Read-only: **zero write calls**, verified mechanically. `WebApp.gs` untouched (**D34**). No new OAuth scopes — `spreadsheets`, `send_mail` and `scriptapp` were already in the manifest. Zero collisions against the project's 152 existing functions. Installs by paste; disarms with `removeHealthTrigger`; rolls back to a `.bak` that also never wrote anything.

**It emails every day, green or not.** `Diagnostics.gs` (S53) speaks only on failure, so its silence means *fine*, *never installed*, or *dead* — indistinguishable. That is the shape of the 06-Jul outage. **The heartbeat's absence is now itself the signal.** It also records its own last run, so a missed day is reported the next morning rather than vanishing.

**v1 shipped at 10:23 and was wrong three times.** All three were caught the same way: the owner read a number in the email and asked about it. Not one was caught by reasoning.

### The three defects, all one defect

**(a) `today=0` on a nightly tab.** v1 asked every tab *"how many rows today?"* At 09:00 a tab rebuilt at 21:30 always answers `0` — whether the job ran or died. v1 printed **`✅ Clinic health OK`** over it, on the same day the runbook gained the line *a check that cannot fail is not a check*. → **D177.**

**(b) `Call_Durations` was not monitored at all** — the one tab the VPS receiver writes, and the exact tab that went silent for 44 hours on 06-Jul. v2 adds it. Replayed against four scenarios: v1 says OK to all four; **v2 catches the 06-Jul outage on its second morning** and a dead 21:30 trigger on day two, while staying silent on a quiet morning.

**(c) `370 outcome(s) awaiting review`** — a lump with no clock behind it. `getOutcomeLog(key, day)` serves **only `today` or `yesterday`**. The 370 was never a queue and could not be worked from the dashboard. Split, it is `3 today · 10 yesterday · 357 aged out` — and 3 + 10 + 357 = 370. **The doctor's first question of the session was spent on a number that described nothing.** → **D179.**

### The four clocks — recorded so no future session re-derives them

| Tab | Written by | Cadence | Max lag |
|---|---|---|---|
| `Followups_Today` | `push_followups_today.py` (clinic PC) | each morning | 0 |
| `Followup_Outcomes` | staff, via dashboard | through the day | 2 |
| `Call_Durations` | `call_hook_capture.py` (VPS) | real time | 1 |
| `Call_Feed` | `rebuildCallFeed()` (Apps Script) | nightly 21:30 | 1 |
| `Call_Recordings` | Stage 1 (VPS) | ~02:00, archives *yesterday* | 1 |
| `Call_Transcripts` | Stage 2 (VPS) | ~03:00, archives *yesterday* | 1 |

**`Call_Feed` and `Call_Durations` are different tables on different clocks.** `Call_Feed` is a nightly 14-day clear-and-rewrite from the MyOperator Search Logs API. `Call_Durations` is written in real time by the receiver — **and only for calls placed through the console dialler** (`category == "obd"` **and** `client_ref_id` present). Proven on 09-Jul: **66 webhooks accepted, 29 rows written.** Everything else is raw-logged on the VPS and never reaches the sheet. A label that says *"real time"* without saying *"console-dialled only"* is a false label. → **D178.**

**Consequence, deliberate and documented:** `Call_Durations` carries `maxLag: 1`, not `0`. At 09:00 there may legitimately be no call yet. `maxLag: 2` was tried and **rejected in test** — it delays outage detection to the third morning, trading away the entire purpose to buy comfort against a rare, dismissible false alarm.

### The audit begins

At the owner's direction, a full audit of the Apps Script project was opened. **Passes 1 (structure) and 2 (data flow) are complete; pass 3 is preliminary; pass 4 not started.** New canonical document: **`Clinic_Callback_Tracker_AppsScript_Audit_v1_1.md`**. **Nothing was fixed.** 12 server files, 4,231 lines, plus `Dashboard.html` at 2,738 lines, 51 browser-reachable globals, **zero duplicate definitions** after 128 sessions.

Headline findings, all documented and all untouched:

- **F-0** — `Call_Feed` **is published to the web**, confirmed from the sheet's dialog, auto-republish on, `Call_Feed` only (not `Entire document`). Deliberate: it is how the clinic-PC tracker pulls its feed. **Public: ~3,000 patient mobile numbers + call date + agent name.** `CallField.gs` line 8 claims *"PHI never leaves the clinic"* — the first clause (no names, no diagnosis) is true; **the conclusion is not.** A mobile number is an identifier. **Accepted risk, bound now written down.** The dialog's own first line reads *"This document is not published to the web"* while `Call_Feed` is published — that line describes the selector, not the state.
- **F-1** — `doGet` serves the dashboard **with no key**. Seven globals check nothing (`sendFollowupSummary`, `probeApi`, `probeRecordingField`, `probeRecordingPlayback`, `testIntradayNow`, `testMonitorNow`, `testMorningNow`). Verified: none returns patient data. **Unauthenticated write, send, and quota-burn as the deploying account. Not exfiltration.**
- **F-2** — **sixteen `catch (e) {}`** blocks that swallow the error, in the staff-facing path. Three of them inside `Diagnostics.gs`, whose docstring reads *"a silent guard is worse than none."*
- **F-3** — `Followup_Outcomes` has **three writers**, and `WebApp.gs` line 1152 comments *"one-writer tab."* Safe today only by accident of layout (column-disjoint, appends never shift indices, `fp` fingerprint guard). One `deleteRow`, ever, and review columns land on the wrong patient.
- **F-4** — `logOutcome` has **no caller anywhere**; its tab `Outcomes_Log` has never been created. A dead ledger with a live, browser-reachable writer that appends patient name and Clinic ID.

**Three of the assistant's own audit checks failed and were rebuilt** before any finding was stated — a regex that returned `withSuccessHandler`, one that returned `getElementById`, and a one-writer test that captured variable names. **And the script that folded F-0 into the audit threw before saving, while the file was copied out under the new name anyway** — for ten seconds a `v1.1` existed on disk that was byte-identical to `v1.0`. **A version number is not evidence of a version.** Caught only because the traceback was read.

**Every fault found this session was the assistant's own, and all of them were one fault: a number, a label, or a name presented without the thing that gives it meaning.**

---

## DECISIONS D177–D180 — FULL TEXT

**D177 — A check must be calibrated to the clock of the thing it checks.**
*09 Jul 2026, S128.* `Health.gs` v1 asked *"how many rows today?"* of `Call_Feed`, a tab rebuilt nightly at 21:30. At 09:00 the answer is `0` whether the rebuild ran or died, so the check printed `✅ OK` over a trigger that could have been dead for a week. **A check whose expected value does not move when the fault occurs is not a check.** Each monitored artefact must be judged against *its own* cadence: `maxLag`, derived from the schedule of its writer, never a uniform "today" test. Direct descendant of **D174** (a selftest is not a production verification) — both are the same error: a green result produced by a code path that the fault does not traverse.

**D178 — A monitored label must state what the artefact contains, not what it appears to contain.**
*09 Jul 2026, S128.* `Health.gs` v2 labelled `Call_Durations` *"VPS receiver, real time."* The receiver writes a row **only** when `category == "obd"` and `client_ref_id` is present: console-dialled calls, nothing else. On 09-Jul, 66 accepted webhooks produced 29 rows. A reader of that label would conclude the tab tracks all calls and would mis-read both its silence and its counts. **Corrected to "console-dialled calls ONLY."** Sibling of **F-0**, where `CallField.gs` labels a feed *"PHI never leaves the clinic"* while publishing 3,000 mobile numbers. **The label is part of the instrument. A wrong label is a wrong reading.**

**D179 — Report a count with the scope that makes it actionable, or do not report it.**
*09 Jul 2026, S128.* `Health.gs` v1 reported `370 outcome(s) logged and not yet reviewed`. The review UI (`getOutcomeLog(key, day)`) serves only `today` or `yesterday`; 357 of those rows had aged out and could not be reached, let alone worked. The owner's first question of the session was spent on a queue that did not exist. Split correctly: `3 today · 10 yesterday · 357 aged out`. **A total that mixes the actionable with the unreachable is not a summary; it is a wall.** Applies to every count this project surfaces to a human: state the scope, or omit the number.

**D180 — An audit finds; it does not fix.**
*09 Jul 2026, S128.* The Apps Script audit opened with five findings, two of them (F-0, F-1) touching a live web app used by staff during clinic hours. **Nothing was changed:** no file, no trigger, no tab, no publish setting. A live staff-facing system is not repaired mid-inventory, and a finding written down loses nothing by waiting a session. Each repair gets a decision sheet priced in lines changed, files touched, whether a staff path is disturbed, and whether rollback needs a redeploy. **F-2's sixteen sites must be split** — a swallowed `ntfy` error and a swallowed outcome-write error are not the same finding and must never be fixed by the same commit.

---

## §S129 — `Dashboard.html` read at last; a dead button, a key giveaway, and a document set that misled its own reader
**09 July 2026 · EOS-LIGHT — no code changed, no file written, no trigger touched, no property set · Audit pass 3 item 1 COMPLETE**

The owner's instruction was to read `Dashboard.html`, 2,738 lines, entirely unread after 128 sessions. It was read. Eight findings follow, and one of them has probably been costing the clinic data every day since it shipped.

### The session opened by getting it wrong

The assistant asserted `Dashboard.html` at **2,676 lines** against the JSON export in project knowledge, declared the five canonical documents defective for saying 2,738, and invoked *"the record is not the disk, and the record loses."*

**The record was right. The disk was the wrong disk.**

`Clinic_Callback_Tracker_AppsScript_S124.json` carries `PAGE_BUILD = 'v18.18 · S57'` and contains **no `Health.gs`**. It is a **pre-S124** export, misnamed for the session it predates. The live file, exported fresh by the owner at the assistant's mention, is **2,738 lines · 157,611 bytes · md5 `034529a124c6bfab8aec2b675620dfec`** — the exact md5 already recorded in this KB's own **v1.48 changelog** for the `v18.19` D156 fix. Two independent sources agree; the file in project knowledge disagrees with both.

The rule held. The identification of *the artefact* did not. **A filename is not provenance → D188.** The claim was withdrawn before any document was edited on the strength of it.

Twelve `.gs` files are byte-identical between the stale export and the live one. Only `Dashboard` differs; only `Health.gs` is new. Fresh export: **465,195 bytes, md5 `8bdb6d4dfdb0a331c5048b3c0fccf367`, 15 files.**

### 🔴 F-8 — the outcome button for incoming calls is dead for every patient the clinic already knows

`Dashboard.html` line 912 serialises the patient's details with `JSON.stringify`, which always emits **double quotes**, passes them through `jsq()`, which escapes `\` and `'` but **not** `"`, and line 923 pastes the result into an `onclick` attribute delimited by **double quotes**. The first quote inside the packet closes the attribute early.

Established by emitting the exact HTML and parsing it, not by reading it:

| Row | `onclick` the browser compiles | Result |
|---|---|---|
| number **not** in `Patient_Master` | `inOpen('in_98…_0','9812345678',false,'{}')` | ✅ works |
| number **in** `Patient_Master` | `inOpen('in_98…_0','9812345678',true,'{` | ❌ syntax error; handler never installs |

The button renders and looks correct. Clicking it does nothing, silently. `inOpen()` is the only route to the incoming-outcome form; `saveIncomingOutcome` is invoked from nowhere else. **For any incoming caller who is a recognised patient, staff cannot file an outcome at all.** The breaking condition is `e.patient` being truthy — i.e. the number is in `Patient_Master` — not the `known` flag.

**This collides with D153.** D153 records, from 40 incoming calls on 06-Jul returning *"No claim logged"*, that *"staff never file outcomes for incoming calls — workflow finding, not a gap."* That population is precisely the one whose button is dead. **A rendering defect may have been recorded as a staff habit, and then relied upon to justify the Stage-3 join in `call_verdict.py`.**

It is not asserted. It is falsifiable in ten seconds on the live dashboard, and **the evidence exists only until the fix lands.** Until the click is made, D153's status is **`UNKNOWN`**, not "confirmed" and not "overturned."

### 🔴 F-9 — F-1 undercounts the ungated surface by twenty functions, and two of them hand out the doctor's key

Audit v1.1's F-1 names **seven** ungated globals and concludes *"none of the seven returns patient data … unauthenticated write, send and quota-burn — **not exfiltration**."* Both halves are true **of those seven**. The conclusion was stated over all of them.

Live count, re-derived from the fresh export with a check that was made to fail first: **55 browser-reachable globals, 27 ungated.** Among the twenty never examined:

- **`setDashboardKey(k)`** and **`setStaffKey(k)`** (`WebApp.gs` L48/L52) — overwrite the stored `DASH_KEY` / `STAFF_KEY` script properties. No key argument, no role check.
- **`removeTriggers()`** (`Main.gs` L97) — deletes **every** trigger in the project.
- **`removeHealthTrigger()`** (`Health.gs` L393) — deletes the 09:00 heartbeat specifically.

Manifest confirmed from the live export: `access: ANYONE_ANONYMOUS`, `executeAs: USER_DEPLOYING`. In Apps Script **every top-level function not ending in `_` is callable from any browser that has loaded the page.** So a holder of the `/exec` URL, with no `?k=` at all, can set `DASH_KEY` to a value of their choosing, sign in with it, and be graded `full` — reaching `getOutcomeLog`, `getTranscriptText`, `getFollowups`: names, Clinic IDs, diagnoses, transcripts. The owner's own key simultaneously stops matching. **It is one anonymous call from a full PHI read, and from a lockout.**

**Two things soften it, and both must be said.**

1. **Server-side role enforcement is real and correct.** Every doctor-only function opens with `dashRole_(key) !== 'full'`. Client-side hiding of the escalation and review sections is defence-in-depth, not the gate. A staff member holding a valid `AKEY_<ext>` genuinely cannot read the doctor's console. **The role model is sound. The setters are the single hole in it.**
2. **`removeTriggers` would be caught.** `Health.gs` alerts by silence; a disarmed heartbeat surfaces the next morning. The instrument built in S128 covers the attack on itself.

**The realistic actor is not a stranger.** It is the `/exec` URL, held by six staff, resident in browser history, and unrevocable without a redeploy that changes it everywhere.

**And the collision the owner must resolve:** both setters live in `WebApp.gs`, which **D34** forbids touching. The rule written to protect a fragile file now stands in front of the only genuine privilege escalation in the project. → **D187.**

### 🟠 F-10 — two escapers, each blind where the other sees

`esc()` neutralises `& < > "` and not `'`. `jsq()` neutralises `\` and `'` and not `"`. Twelve sites put `jsq()` output inside a double-quoted attribute; twelve put `esc()` output inside a single-quoted one. Each held **only because the data happened never to exercise the other's blind spot** — phone digits, hex recording refs, row IDs.

Line 923 was the first field *guaranteed* to contain a double quote. **F-8 is not a typo. It is the first field that tested the gap.** Same shape as F-3, which is safe by accident of layout: this is safe by accident of data.

The structural cure is not a better escaper. It is to stop embedding patient data in markup at all — the button carries a row ID; the details stay in a JavaScript object and are looked up on click. Twenty-four fragile sites become none.

### 🟠 F-11 — the key is stored in the clear and there is no way to sign out

`applyAccess()` writes the key to `localStorage` as `clinicDashKey`. **Zero** occurrences of a logout, a clear, or a `removeItem` in 2,738 lines. The reception tablet holds a working key permanently. `?k=` in the URL puts it into browser history and into any screenshot of the address bar.

The existing control — `Active=no` on the roster row, which makes `dashRole_` return `none` — is real and is the right one. But it invalidates the **person**, never the **key**, and nothing prompts the edit.

### 🟡 F-12 — every open tab costs ~9 server calls a minute, over F-6's whole-tab reads

`REFRESH_SECONDS = 60`. Each cycle fires `getDashboardData`, `getFollowups`, `getFollowupLastVisits`, `getFollowupRecordings`, `getFollowupClinicIds`, `getAllCallsToday`, `getFollowupFreshness`, plus `getEscalations` and `getOutcomeLog` on the doctor's key. **F-6** counted fifteen full-tab `getDataRange().getValues()` reads, including `Call_Feed` at 3,019 rows and growing nightly. The two findings multiply.

Sharpest instance: while a call is placed, the tile polls `getCallDuration` **every 6 s for up to 3 min**, and `getCallDuration` re-reads the entire `Call_Durations` tab each time. **One three-minute call re-reads that whole tab thirty times.**

Nothing is broken today. It degrades in proportion to accumulated history, and it degrades as *"the dashboard is slow"* and *"Reconnecting…"* — which look like the clinic's internet and are not. **The project's daily Apps Script execution budget is `UNKNOWN` and must be looked up, never guessed.** Nothing currently watches it: `Health.gs` reports on tabs and freshness, not on headroom.

### 🟡 F-13 — the UTC-date bug D156 fixed still survives sixty lines away

`fuDayKey()` (L1603) was rewritten in S124 to use the **local** date, precisely because a UTC day key stranded call state. **L1800 still calls `new Date().toISOString().slice(0,10)`** — UTC — to stamp the follow-up progress line. Display-only, and the clinic is shut between 00:00 and 05:30 IST. But it is the same bug, in the same file, left behind by the commit that fixed its twin.

**And "local" is not "IST."** There are three clocks: the manifest's `Asia/Kolkata` (via `Session.getScriptTimeZone()`, 15× in `WebApp.gs`), the separate `CC_TZ` constant (18× across `Callconsole.gs` / `OutcomeLog.gs` — this is **F-5**), and the browser's device clock. A tablet with a wrong time zone can corrupt follow-up state. The remedy is one clock: the server sends `todayIST`; the client computes no dates.

### ⚪ F-14 — fourteen of seventeen client-side silent catches are correct; three are not

Swallowing a `localStorage` write, a `.focus()`, or a `revokeObjectURL` is right. **L1260** and **L1364** swallow a `JSON.parse` of the patient packet, so a malformed packet becomes an empty outcome payload rather than an error. **L1128** swallows `openThread`.

L1260 parses the very packet F-8 corrupts. **The catch that would have reported F-8 is the catch that hid it.**

### ⚪ F-15 — a production web app holds the `documents` OAuth scope for one dev file

`DocumentApp` appears exactly once in the project: `Probe.gs`, the scaffolding already flagged by F-7. The scope is granted to the whole deployment.

### The incoming-call gap, and what the receiver is throwing away

F-8 is a broken button. Underneath it is a missing capability, and the owner named it: *"the incoming doesn't open the callback tracker currently, making the outcome logging difficult."*

Outbound calls have a machine — console click, `client_ref_id`, receiver row, polling tile, unlocked form. **Incoming calls have none of it.** Per **D178** the receiver writes a row only when `category == "obd"` **and** `client_ref_id` is present. On 09-Jul, **66 webhooks accepted → 29 rows written.** The other 37 were real calls, received by the VPS, raw-logged, and dropped before the sheet.

Verified against `MyOperator_Call_API_Master_Reference` §9: the webhook suite is `call.initiated` → `call.dial_begin` → `call.answered` → `call.end` → `call.summary`. The receiver is subscribed to the last two. **Adding incoming calls is subtraction, not integration** — no Lokesh, no new credential, no token; the event list is a set of tick-boxes in the panel (§9.0 item 5, self-serve).

**`call.initiated` has never been captured on this account.** §9.0 verified only `call.end` and `call.summary` against real bodies. Whether `call.initiated` fires for incoming calls, and whether it carries the caller's number, is **`UNKNOWN`** and cannot be designed against.

### Why the tile fires at hangup, not at ring

The owner asked for a ring-time tile **and**, in the same message, for *"stability and low maintenance."* Those conflict, and the conflict was surfaced rather than silently resolved.

Apps Script cannot push. The browser only sees the world when it asks — every 60 s today, at the cost F-12 records. A tile visible during a ring (~20 s) demands asking every ~5 s: roughly a twelvefold load increase, aimed at the one limit nobody measures.

**And the human argument is stronger than the technical one. While the phone rings, the receptionist is answering the phone.** She reaches for the handset, then talks to a patient in pain. She cannot log during a ring and should not be looking at a screen. **The moment an outcome is knowable is the moment the call ends** — the patient has hung up, she still remembers, and `call.end` has already reached the VPS. → **D184.**

### Answer to the owner's quota question, recorded because it will be asked again

*"Quota is also important — if needed, what other options exist for us?"* In ascending order of disruption:

1. **Reduce demand.** Lengthen the refresh; bundle the five follow-up calls into one; read the last *N* rows instead of whole tabs; stop polling when the browser tab is hidden. Invisible to staff.
2. **Cache on the server.** `CacheService` holding the dashboard payload for 30–60 s, shared across all tabs: six agents refreshing becomes **one** sheet read, not six. Largest saving for the least change.
3. **Measure before optimising further.** The edition-specific daily budget is `UNKNOWN`. Add headroom to `Health.gs` so exhaustion is predicted, not discovered mid-clinic.
4. **Move the read path off Apps Script.** The VPS already holds a service account and `gspread`. It could serve the dashboard payload; Apps Script keeps the writes. **A trade, not a win** — a second auth surface and a new dependency.
5. **Move the dashboard off Apps Script entirely.** Large, and not recommended.

**1 and 2 are invisible to staff and are what Block C means.** 4 and 5 exist only if 1–3 prove insufficient.

### What was decided, and what was not

Owner directives this session: Block A approved · **Block B parked, ordered last, blast radius assessed first** · Block C approved *only if it does not disrupt flow* · Block D approved · `Probe.gs` deletion delegated to the assistant · escaper rework approved *if workflow is not compromised* · audit-record correction approved.

**Nothing was changed. No file, no trigger, no property, no tab, no publish setting.** The one number asserted against the wrong artefact was withdrawn before it reached a document.

---

## DECISIONS D181–D188 — FULL TEXT

**D181 — Incoming calls become first-class; the receiver stops discarding what it already receives.**
*09 Jul 2026, S129.* `call_hook_capture.py` writes a row only for `category == "obd"` with a populated `client_ref_id` (D178). Every incoming call already arrives at the VPS as `call.end` and `call.summary`, is raw-logged, and is dropped. On 09-Jul that was 37 of 66 accepted webhooks. The incoming console is therefore **subtraction, not integration**: no vendor ticket, no new credential, no token rotation, nothing from Lokesh. Incoming rows go to a **new tab, never `Call_Durations`** — that tab means *console-dialled*, and D178 exists because a label that lies is a fault. One writer per table.

**D182 — An unknown incoming number gets a tile. Identity is established by staff, not by a filter.**
*09 Jul 2026, S129.* Owner decision. A tile is created for every incoming call, recognised or not. The unknown-caller path in `inOpen()` already exists and already asks *"Who is this?"* — existing patient on a new number, new enquiry, urgent surgical, not a patient. **Filtering to known numbers would discard exactly the calls with the highest clinical value.** Sibling of D179: a queue that hides the unreachable is a wall.

**D183 — No call ends its day unlogged; the 21:30 sweep escalates both directions to the doctor.**
*09 Jul 2026, S129.* Owner decision. Every call, incoming and outgoing, that carries no outcome at the end of the clinic day is swept into a doctor-facing review band. **This is what makes the incoming console self-correcting**: a staff member may miss a tile and the system still notices. It is the same architectural move as `Health.gs` — the absence of an entry becomes a signal instead of a silence. Descendant of D179: the count must arrive with the scope that makes it actionable.

**D184 — The outcome tile appears at hangup, not at ring.**
*09 Jul 2026, S129.* The owner initially asked for a ring-time tile, and in the same message for stability and low maintenance. Apps Script cannot push; a ring-time tile requires polling roughly every 5 s against the whole-tab reads of F-6/F-12 — a twelvefold load increase aimed at an unmeasured limit. **The decisive argument is not technical.** While the phone is ringing the receptionist is answering it; she cannot log an outcome and must not be looking at a screen. The outcome becomes knowable at hangup, when `call.end` has already reached the VPS. Ring-time is **deferred, not dropped**: revisit after Block C, and only with a captured `call.initiated` body, which has never been seen on this account.

**D185 — Nothing real-time is built on a system whose running cost is unmeasured.**
*09 Jul 2026, S129.* Block C (one clock, bounded reads, bundled calls, server-side cache, quota headroom in `Health.gs`) precedes Block D (the incoming console). The dashboard makes ~9 server calls per minute per open tab over fifteen whole-tab reads, and no instrument watches the budget those consume. Adding a real-time feature to that is not a feature; it is a fault with a delay. Direct descendant of **D177** — a check calibrated to the wrong clock, and a system whose limit is invisible, fail the same way: **the green light is produced by a path the fault does not traverse.**

**D186 — Verification of a subset is not verification of the set.**
*09 Jul 2026, S129.* Audit v1.1's F-1 examined seven ungated globals, correctly verified that none returns patient data, and published the conclusion *"not exfiltration"* over a surface of twenty-seven — two of which overwrite the doctor's key. **The reassuring sentence was the wrong one, and it was wrong in the project's signature way: a true claim about a part, stated about the whole.** The basis of the original count of seven is unrecoverable; F-1 is therefore re-derived, its method stated, and the original recorded as unrecoverable rather than silently overwritten. Sibling of D174 (a selftest is not a production verification) and D172 (expected values come from the artefact).

**D187 — A fix requiring D34's suspension is blast-radius-assessed first, and made last.**
*09 Jul 2026, S129.* `setDashboardKey` and `setStaffKey` are the project's only unauthenticated privilege escalation, and both live in `WebApp.gs`, which **D34** forbids touching. Owner directive: *"check blast radius before touching it — park for last change."* **This item is ordered last; it is not silenced.** It sits in the PARKED ITEMS REGISTER with an explicit exception: unlike the rotation, it is **not** closed to session-start review, because it is ordered by dependency and not by safety. Its bound depends on the `/exec` URL *and* the function names, which are absent from the served page but present in the GitHub repo — **repo visibility is `UNKNOWN` and must be confirmed before the bound may be relied upon.** `removeTriggers` and `removeHealthTrigger` require no waiver and close in Block A.

**D188 — A filename is not provenance.**
*09 Jul 2026, S129.* `Clinic_Callback_Tracker_AppsScript_S124.json`, sitting in project knowledge, contains `PAGE_BUILD = 'v18.18 · S57'` and no `Health.gs`. It is a **pre-S124** export named for a session it predates. Reading it, the assistant asserted `Dashboard.html` at 2,676 lines, declared five canonical documents defective, and invoked *"the record is not the disk."* The record was right. **The rule held; the identification of the artefact did not.** Sibling of *a version number is not evidence of a version* (S128): both are the error of trusting a **name** attached to bytes instead of the bytes. Where an artefact's provenance is asserted by its filename alone, the correct entry is **`UNKNOWN`** (D166) until a hash, a build stamp, or a fresh export confirms it. Corollary: every canonical document naming an export must carry that export's **md5 and file count**, not its nickname.

---

## RESERVED / OPEN DECISION NUMBERS
- **D83–D92** remain RESERVED for the pending lifecycle proposals P1–P10 (KB §55), still awaiting lock.
- **Next free decision number for new work: D217.** (**D213–D216 spent in S137** — seen-today template, §K wording, third-attempt rule, 3rd-strike template + snooze; see §S137.2.) (**D211–D212 spent in S136** — see §S136.6. *Correction, S136: this header still read "D208" after S135 had spent D208–D210 — the v1.61 changelog was right, this header was not. D172's own field, a third time.*) (**D206–D207 spent in S134** — trigger ownership and sign-out-via-flag; see §S134.6.) (**D205 spent in S133** on the seen-today WABA feature — see §S133.5; **D204 spent in S132** — see §S132.7.) *(Correction, S133: this line still read "D204" after S132 had spent D204 — the changelog and §S132.7 were right, this index header was not. D172's own field, again.)* (D189/D190 spent in S130; **D191–D201 spent in S131** on the AI review-layer design — see §S131.7; **D202 spent in S131** on the record itself — see §S131.14.) **D1–D120 are NOT in the index below and never have been (F-22). Fifteen are restored: D62, D66, D68, D69, D77, D78, D80, D81, D82, D97, D98 in §S131.13, and D112–D115 in §S131.16. The rest live only in the Session 1–62 runbooks.**

---

## OPEN BACKLOG SNAPSHOT (as of S94 close — see Runbook for the live list)

**Six-item forward agenda (owner-set S94, recommended order):** (0) console `isGenericAgent_`
fix — DONE. (1) Duplicate patient entries in a day — PC-side de-dupe, SAFE, next execution item.
(2) Reconcile "didn't pick up but visited" — auto-settle on a real Docterz visit; overlaps
Track-1 Step 7. (3) Trim the >200 staff list — **DONE (S121, D148: cap 120 + Hard-to-Reach split).** (4) Live staff-activity summary on doctor dashboard — audited half
depends on item 5. (5) AI audit layer (Stage 3, D62) — **BUILT + PROVEN S122–S123 (D149–D153); next = nightly timer + Verdict Analysis Layer D154.**
(6) Historical taxonomy insights — analysis only, blocked on a de-identified export.

**Track-2 live backlog:** WABA authorizer fault (D120, Lokesh, blocks all sends) · make
`wa_approve` a systemd service · rotate `WA_APPROVE_KEY` + service-account key + AKEY_14 · arm
timer-freshness checker + maintenance jobs · `clinic_health_report.py` UTC→IST fix · courtesy
rotate `CALLHOOK_SECRET` + `FU_UPLOAD_SECRET` (D145) · consider a `CALLHOOK_SECRET_MISMATCH_403`
detector (panel Failed OR no daily raw-log by mid-morning).

**Track-1 backlog:** Hindi SPELLING corrections in `vitals_page.html` LIB strings · Step 7
new-patient reconciliation (dovetails with agenda item 2) · living Clinic Data Map (§66.6).


---

## CHANGELOG

- **v1.68 — 13 Jul 2026 (Session 142, FULL EOS — one new VPS file `daily_digest.py` v1.2.1; crond restarted; `.env` +3 `DIGEST_` lines; Verdict_Review redrawn 8,845/378):** Adds **§S142**, **D238–D239**, findings **F-41 (FIXED)** and **F-42 (open)**. 🟢 **D236 digest layer LIVE**: 11:00 all-morning-calls pulse (D238) + 21:30 full digest with 2 seeded MATCH spot-checks; read-only by construction (readonly scope + no-append, both selftested); email path proven on the owner's phone; AI lines from aggregate counts only. 🔴 **F-41**: crond ran on UTC since 16 Jun — every cron 5h30 late, the 08:45 write-probe had NEVER fired, masked by the at-hangup worker; cured by crond restart, **proven by a 2-minute canary** (never the restart message). Owner-directed same-day classifier: every unjudged call carries a reason; its first run caught 🔴 **F-42** — connected incoming calls (status=missed + result=connected) with 27–101 s of talk and no recording ever produced; hypothesis: answered on an unrecorded leg; S143 investigation. **D237 set built**: 41 calls, seed `D237-S142`, full strata coverage, xlsx delivered; 28/41 answerable today (ai-only cap; MATCH lines have no answer cell → the daily spot-checks lack a landing cell) — owner chose Option B, whole sitting waits for the S143 `verdict_review` force-card enhancement. **D239 Flag Investigator approved** (self-heal ON · 30-min clinic-hours cadence · Lokesh-escalation rule). Repo drift confirmed by hash (call_verdict still v1.0 in repo); v2.1 + daily_digest commits owed. Next free decision: **D240.** Next free finding: **F-43.**
- **v1.67 — 13 Jul 2026 (Session 141, FULL EOS — one VPS file changed: `call_verdict.py` v2.1):** Adds **§S141**, **D235–D237**, findings **F-39 (FIXED)** and **F-40 (open, cosmetic)**. 🔴 **F-39:** Sheets append "table detection" landed EVERY v2 verdict on row 61 — the S140 "480 judged / 0 failed" catch-up and every worker kick each overwrote the previous verdict; ~502 AI calls wasted in a day; the no-date-limit 03:40 cron would have repeated it nightly (disarmed before first firing, re-armed after the fix). Proven by the append API's own reply (`updatedRange: A61:AI61`); one v1 row and the last v2 survivor were collateral (the diagnostic probe shared the diseased path). **v2.1** (md5 `9cb454e9…`, selftest 42/42): explicit computed-row writes, local row counter, grid auto-grow, honest `PROMPT_VERSION`. Supervised 5/5 trial → full re-judge → **550 verdict rows, complete history**. **F-40:** stale banners (`verdict_review` still prints v1.3; v2.1 comments mislabel the finding "F-21") — the same staleness that masked F-39. First real analysis delivered (550 calls; 70% match rate on logged outgoing; batch-offset clusters; ~15-recording worst-first doctor list). **Digest layer designed (D236)** — 21:30 full + 11:00 silent-unless-actionable pulse, email pending test-receipt gate; **calibration path locked (D237)** — stratified 40-call referee set, then daily drip. Next free decision: **D238.** Next free finding: **F-41.**

- **v1.66 — 12 Jul 2026 (Session 140, FULL EOS — Dashboard v18.28f, Callconsole v1.7, four VPS files + one systemd unit installed and live-verified):** Adds **§S140**, **D225–D234**. Gap register **G-1, G-3, G-4, G-5, G-6 ALL CLOSED** (G-2 closed S139) — the life of a call now has no known gap in either direction. **F-18 CLOSED** (D153 retired; incoming calls judged for the first time). K-2 live: new-lead band, 3-day TTL, one miss-counter rule. Verdict layer v2: selftests 42/42 + 121/121; historical catch-up 480 judged / 0 failed. D200 implemented: kick-queue at-hangup pipeline (hook v3.1 selftest 61/61, worker 14/14), QUIET window 01:55–04:05 IST, 03:40 cron = floor. Write-probe (G-6/F-38 cure) armed 08:45 daily, selftest 10/10, first manual run PASS. Staff-buzz notification idea permanently DROPPED (D232). Next free decision: **D235.** Next free finding: **F-39.**
- **v1.65 — 12 Jul 2026 (Session 139, FULL EOS — Dashboard v18.26→v18.27, Callconsole v1.6, relay v3, portal hotfix):** Adds **§S139**, **D219–D224**; audit **F-10 CLOSED**; call-lifecycle gap register G-1…G-6 (G-2 closed same session); quota baseline recorded.
- **v1.64 — 12 Jul 2026 (Session 138, FULL EOS — VPS code changed):** Adds **§S138**, **D217–D218**, **F-37, F-38**.
  Backlog **A1 executed end-to-end in one session**: `call_hook_capture.py` **v3.0.1** live (827 lines, md5
  `b64aee2b7b0bcc986a72e5e4f176a86c`) — incoming calls now upsert into `Call_Durations` keyed `IN-<session_id>`
  (D217) with the caller's last-10 number in the new final `phone10` column, incoming rows only (D218). The
  v3.0 first restart hit `Range (Call_Durations!N1) exceeds grid limits` — the tab was CREATED exactly 13
  columns wide; v3.0.1 adds a guarded `add_cols(1)` before the header self-heal (offline selftest cannot see
  grid geometry; the raw log lost nothing meanwhile). New one-shot **`backfill_call_durations.py`** (131 lines,
  md5 `974ae54952dbc235e5cc6af107e83eeb`, insert-only, idempotent, aborts without the phone10 header, imports
  the receiver's own `extract_record`) replayed 9 raw-log files / 874 lines / 424 extractable calls →
  **inserted 219 rows (216 incoming + 3 OBD strays from 03-Jul)**. Independent verification from the live tab:
  424 data rows, 216 `IN-` / 208 OBD, phone10 = 10 digits on 216/216 incoming and blank on 208/208 OBD, zero
  duplicate keys, 138/216 incoming carry a recording filename. **F-19's scope change against D80 is EXECUTED;
  §K Phase K-2 is unblocked.** Selftest grew 42→**57** checks. F-37: VPS health mail's "ACTIONS TAKEN (last
  24h)" showed 04-Jul entries on 12-Jul. F-38: surveillance gap — service liveness green for the full ~9 h
  the sheet-write path was failing (raised, not fixed; D180). 12-Jul VPS health mail ALL GREEN; quota/D183/
  D212 reads remain time-gated. Next free decision number: **D219.** Next free finding number: **F-39.**
- **v1.63 — 11 Jul 2026 (Session 137, EOS-LIGHT — decisions + design only, NO code touched):** Adds **§S137**,
  **D213–D216** (all four template-dependent values live-verified against the WABA panel the same evening).
  §K.6 one-tap staff-UI design LOCKED with zero open inputs (canonical home: Console Spec v2.2). Full
  14-template WABA inventory pulled live (7 new to the API card; numeric-vs-named placeholder split recorded;
  `MYOP_AUTH_TOKEN` recorded as the token's `.env` name). `WABA_Approved_Templates_v1_S137.md` supersedes the
  historical `Final_WABA_Utility_Templates` doc. Umbrella v1.48 found absent from project knowledge, recovered
  from GitHub `canonical-docs/` md5-exact, restored. D183 digest observed twice on 11-Jul (manual + likely
  trigger; 12-Jul count is the clean test). CALLHOOK Step-3 message sent to Lokesh. Next free decision
  number: **D217.**
- **v1.62 — 11 Jul 2026 (Session 136, FULL EOS — THREE Apps Script deploys v18.24/v18.25/+Callconsole v1.5, all
  live-verified same evening; live editor byte-verified post-deploy via export `__7_`):** Adds **§S136**,
  **D211–D212**. **Block C SHIPPED** (one server clock · one bundled trip behind a 45 s per-role shared cache ·
  bounded 200-row duration poll · hidden tabs sleep · QUOTA HEADROOM in the 08:00 mail) — closes **F-5, F-6,
  F-12, F-13** and audit **§4-Q3**. **F-36 raised and CLOSED same evening** (escalation card was a seventh
  phone-keyed surface; live case Raj Rani 7362→7361; ID ⚠ verify on shared-no-match, D208). **WA tiles show
  today's call** (D212; verification parked). **F-4 CLOSED** (dead logOutcome ledger deleted). **Block E
  CLOSED** (Probe.gs deleted; `documents` scope dropped — F-15/F-7). **D183 BUILT and ARMED** (21:30
  unlogged-calls digest, both directions, read-only; first digest live-received). **F-3 CLASSIFIED** (§S136.5:
  column-disjoint-by-layout contract recorded). CALLHOOK optimism corrected (§S136.3 — a zero-traffic window
  proves nothing; Steps 3–4 remain open). Export-form hashing rule recorded (§S136.4). Stale next-free-D
  header corrected a third time (D172's field). Next free decision number: **D213.**
- **v1.61 — 11 Jul 2026 (Session 135, FULL EOS — two Apps Script deploys v18.22/v18.23, three PC files):**
  Adds **§S135**, **D208–D210**; **F-34 raised and CLOSED same session** (shared-mobile identity: mirror
  per-phone collapse + phone-keyed dashboard enrichment — Raj Rani shown with Ekta's ID and Ekta's
  last-visit date); **F-35 CLOSED** (S35 review SEND BACK now returns tiles to staff, live-verified on
  four real tiles); resolver single-match name check + UID-shape footer guard; visit ledger cleaned
  831→829 (09-Jul "Credit Card"/"0-7400" leak); clinical data report verified a strict superset and the
  migration plan enumerated (build pending, owner input on the follow-up column open). One recorded
  assistant error: a from-memory claim about F000562 disproved by the artefact (D172 restated).

- **v1.60 — 11 Jul 2026 (Session 134, FULL EOS — two Apps Script files changed, deployed v18.21):**
  Adds **§S134**, **D206**, **D207**; **withdraws F-32**; **closes F-33, F-2 (A-6), F-11 (A-4), A-3,
  A-5**. 🟢 **F-33 classified external** — the one `runMorningReport` failure (09 Jul, `Address
  unavailable: developers.myoperator.co`) sits inside the D120 outage window; no code change. ↩️
  **F-32 WITHDRAWN** — `setupTriggers()` installs one trigger per hour by design
  (`INTRADAY_HOURS`×7 + `EMAIL_HOURS`×3 + 1 + 4 subsystem = 15); owner counted 7/3/15 on the Triggers
  screen; S133's "≈8×" was a miscount of 7; third finding cleared by reading the installer. 🔧 **A-5**
  — `removeTriggers` scoped to Main's own three handlers (**D206**; it had been a project-wide sweep
  that `setupTriggers` invoked, an armed accident for the health email). 🔧 **A-3** — the
  `openThread`-after-send catch uncloaked; F-14's three wrong catches all gone; 18 trivial guards
  remain, counted with scope. 🔐 **F-11/A-4** — Sign out live: `clinicSignedOut` flag checked before
  any key source (**D207** — the sandbox cannot edit the parent URL; the flag is the sandbox-legal
  equivalent of stripping `?k=`); feature checks 3/3. 📋 **A-6/F-2 closed** — nineteen (not sixteen;
  +3 with `Health.gs`) silent server catches classified individually: 11 fail-open enrichments, 6
  alert-path guards, 1 save-protection, 1 dead code; **zero fixes needed**. 🔑 **Recorded:** the live
  full-key property is `SECRET_KEY` (WebApp L148 alias; `DASH_KEY` never set here); full property list
  `UNKNOWN`. 📦 Deploy verified from fresh export **`8bd1aeaa…`** (Main `1a85166c…`, Dashboard
  `5ff68c3d…` byte-identical to built files; WebApp/Health unchanged). 📚 **Frontend Doc v2 delivered**
  (complete re-base, every line number re-derived, §8 session/key handling new, two v1 UNKNOWNs
  closed). Rotation and AI-review layer never raised. Every KB operation additive except the title
  line, the next-free line, the end-marker, and this entry. Next free decision number: **D208.**
- **v1.59 — 11 Jul 2026 (Session 133, FULL EOS — one PC file changed, one VPS service installed, one repo commit):**
  Adds **§S133**. ✅ **D194 BUILT, TESTED, LIVE** — `Do_Not_Call` tab created (`Phone · Reason · Set By ·
  Set When · Note`, human-maintained, never written or created by code) + filter in
  `push_followups_today.py` (**19,497 b · 489 l · `7693a29a98dddbbdf01846fd139f5649`**, built from the
  triple-verified `fc0a731d…` by five guarded anchors). Safety contract: tab missing → loud warning,
  push continues; tab unreadable → **push refuses**; bad rows reported masked. **Live end-to-end test:**
  one real patient listed → push removed exactly her (122→121), row deleted → restored (0 numbers, 122).
  **F-20, `patient_deceased`, `number_invalid` CLOSED.** ✅ **Repo hygiene commit `84831b0`, verified
  from GitHub by hash:** **F-31** (placeholder-guarded `git mv` → `att_config.example.py`), **F-17**
  (deployed content was ALREADY in the repo as `WebApp_v19_D189.gs` — pure renames; `WebApp.gs` now
  `5173c3c7…`, pre-change kept as `WebApp_PRECHANGE_ROLLBACK.gs`; `.gs.gs` names fixed), **F-30** (three
  watcher files off the single disk, `watch_and_push_followups.py` `8561f3d7…`), **F-27** (deployed
  `wa_send_api.py` `bc76e5cb…`, `logged=` marker present), Health.gs newline aligned (`9461d01b…`).
  ✅ **`wa_approve` → systemd** — unit `e18048b2…`, gunicorn `127.0.0.1:8101`, `--timeout 300` (one LIVE
  batch may fire up to `WA_DAILY_CAP` sends in one POST), enabled + active, old nohup PID 696717 killed,
  page verified live; deployed `wa_approve.py` = repo (`c650f4c2…`, no drift). **The last bare-nohup in
  the clinic is gone.** ✅ **Fresh Apps Script export verified in project knowledge** (`523ddcbe…`,
  15 files, `WebApp` `5173c3c7…`, `Dashboard` `a442bab5…` = deployed v18.20) — the stale-`4.json` item
  is closed. ✅ **A-7 done** — Triggers inventory captured. 🔴 **F-32** — **15 installed triggers with
  heavy duplication**: `runIntradayDigest` ≈8×, `runSummaryEmail` 3× (quota waste; possible duplicate
  runs/emails). 🔴 **F-33** — `runMorningReport` error rate **14.29%**; every other trigger 0%. Neither
  fixed (D180). 🧭 **A-4 re-scoped:** F-11's fix (sign-out button, strip `?k=`, localStorage clear) is
  `Dashboard.html` CODE, not a manual action — moved into the next Apps Script pass; interim
  history-hygiene parked by owner. **D205** minted (seen-today WABA section: designed at session start,
  never as a late-session add-on; source = the owner's daily Docterz CSV — **exported by the owner, not
  Shavez: factual correction to the working record**). Index header corrected (said D204 after D204 was
  spent). Owner directive: **all AI-review-layer work parked** (A-00, A-0, A-1 not raised; F-18 parked
  with it). Next free decision number: **D206.**

- **v1.58 — 10 Jul 2026 (Session 132, FULL EOS — one live file changed: `Dashboard.html` → v18.20):**
  Adds **§S132**. **F-8 CLOSED** — Fix B built from the verified export, eight anchored edits,
  seventeen lines, `node --check` clean, the broken handler reproduced in node before deploy and
  verified live on two known-patient tiles. **F-14's two `JSON.parse` catches removed** (L1260, L1364);
  `catch(e){}` 16 → 14; L1128 is A-3's whole remainder. **Block E's *stop embedding patient data in
  button markup* delivered.** **MyOperator cleared** — both endpoints 200, template delivered to the
  handset, outage window documented (05 Jul 01:19 → 09 Jul 16:53, service unrestarted since 26 Jun).
  **Tracker reconciled against the repo**: 38/40 identical; `push_followups_today.py` identical across
  three sources. Decision **D204** (D113 is intent, not fact). Findings **F-27, F-29, F-30, F-31**;
  **F-26 and F-28 WITHDRAWN**. Four assertions made from unread artefacts, all four wrong (§S132.6).
  Next free decision number: **D205**.

- **v1.57 — 09 Jul 2026 (Session 131, consolidation pass 3 — still NO live code touched):** Adds **§S131.15–.17**, **D203**, **F-24**, **F-25**, and the backfill of **D112–D115**. 🛑 **The Register was NOT retired, and §S131.12's recommendation to retire it was WRONG.** Diagnostics §M1 states: *"The single brain = `Fault_Action_Register` (**D114**)."* Folding it away would have overturned a decision the assistant had not read — because **D112–D115 all sit in the D1–D120 hole (F-22)** and §M1 is their only definition. **That would have been the fourth lineage error of this session.** It was caught only because the document was read before it was retired. 🔴 **F-24 — the Register describes an auto-responder that does not exist.** Nine faults are marked `AUTO→ESC` with *"System does: `systemctl restart call-api`"* — but the live watchman is, in Diagnostics §L2's own words, *"**Read-only** — reports only; **never starts/stops/changes a service**."* It *names* the restart command in an alert; it has never run one. **D113 — *"the watchman IS the Lane-1 responder"* — states intent as fact.** §4 of the same Register lists that responder as **Deliverable 2, unbuilt. Not one row of the Register is live-and-acting.** *During an outage, a session reading §2.1 would wait for a restart that never comes.* 🔴 **F-25 — six `CALLHOOK_*` codes have been detecting since S125 with no lane and no procedure**, violating the Register's own rule 4 (*"every alert names its procedure"*). All six laned in Register **v2.0 §2.5**, every one ESCALATE-ONLY or ASSISTED. ✅ **D203 — detection and response are separate documents with a stated boundary:** Diagnostics *defines and detects* a fault code; the Register *lanes* it; **neither restates the other.** This preserves D114 and ends the "two writers, one table" appearance. 🧱 **`Fault_Action_Register_v2_0.md`** — self-contained; §1, §2.1–§2.4, §3, §4, §5 verbatim, **0 lines lost**; the twenty-five-version-dead source-of-truth line corrected; the front page that said *"nothing here is built"* over a body marking three detectors LIVE replaced by a **per-row status column**; §5's Q1 and Q2 **closed by what shipped** (09:00 IST; ntfy + Gmail) — the document was never told. **No rule, lane or procedure was altered.** 📚 **D112–D115 restored** (§S131.16) — with §S131.13's eleven, **fifteen of the missing D1–D120 are now in this document.** 🗄️ **Historical archive:** seven superseded documents and eight non-system files removed from the working set, **archived to the cold kit under `historical/` and to the repo.** Nothing deleted. **Kept deliberately:** `4.json`, the `Verdict_Review` CSV (the only evidence behind the calibration argument), and `MyOperator_Call_API_Master_Reference` — which held the answer to D200 when nothing else did. ⚠️ Recorded, not fixed: the Register's `WA_TOKEN_AGING` procedure points at `SOP_WhatsApp_Token.md`, **which has never been written. A procedure that points at a document nobody wrote is not a procedure.** Next free decision number: **D204.**

- **v1.56 — 09 Jul 2026 (Session 131, EOS-light consolidation pass 2 — still NO live code touched):** Adds **§S131.12–.14**, **D202**, **F-21, F-22, F-23**, overturn markers on **D153** and **D157**, and the recovery of **eleven decisions this KB has never held**. 📚 **Two of the seven documents `START_HERE` calls canonical were stumps.** `Call_Console_Evolution_Spec_v1_6` held §J and §K alone and opened by cross-referencing a `§G` that existed nowhere; `Diagnostics_..._v1_7` began at `§NEW-D`. Both broke the **S100 policy stated in this document's own header** — applied to the KB in S100 and never to the specs. **Git had v1.1 and v1.6 only; across 62 commits, v1.2–v1.5 were never committed. Drive had v1.5.** All were recovered intact from the owner's cold-backup zips; three independent copies of v1.5 agree byte-for-byte. **Nothing was lost, and the four-month backup discipline is the only reason.** 🔴 **F-22 — this document has never carried D1–D120.** The index of every KB ever written runs **D121→D188**. **D68, D78, D80, D81 have zero mentions in 246 KB of canonical text**; D77 and D82 appear only inside D156's phrase *"amends D77/D82"*. **The KB amends decisions it does not contain.** 💸 **What the hole cost, measured: four designs made in S131 had already been made in Sessions 25–54** — D200 (per-call recording + processing-lag retry, Call Console v1.1 §12, S25); **Axis 1 CONTACT, the AI judge's entire purpose** (D62/D77 — *"dead-air lies … caught post-hoc by the AI-verdict layer"*); the **three-attempt cap** (D78 — and it **conflicts** with D195: D78 fires a WABA template and snoozes, D195 goes to the doctor; **neither is built**); and **`wrong_number` → doctor** (D68, verbatim). ↩️ **F-19 WITHDRAWN.** `call_hook_capture.py` L385 skipping non-OBD calls is **D80, as built, Session 54** — *"Skips incoming / non-OBD calls"* — not a defect. Reclassified as a **scope change** against D80. **Third lineage error of S131**, same cause as F-8's and D200's: a decision characterised without reading the document that made it, because that document was a fragment. **F-20 survives** — D68 *escalates* `asked_not_to_call`; nothing ever *suppressed* it. Escalation is not suppression, and `Do_Not_Call` (D194) is the suppression D68 implied. 🔴 **F-21** — the S25 backlog item reached no backlog. 🔴 **F-23** — `Diagnostics_v1_7` swore *"carries forward v1.6 unchanged"* and **abridged §NEW-D/F/G, dropping sixteen lines**, including the Session-94 evidence behind the verification standard (*"the fix was dead seven minutes later; the panel had reverted"*). **It kept the rule and deleted the reason.** 🧱 **Three consolidations, each asserted line-by-line to lose nothing:** `Call_Console_Evolution_Spec_v2_0.md` (v1.1–v1.6, **0 lines lost**), `Diagnostics_Surveillance_System_Spec_v2_0.md` (v1.1–v1.7, **0 lines lost**; three sections all named `§NEW` renamed §L1/§L2/§L3 per D178; v1.6's full originals restored as §M2–§M4), and `INCIDENT_2026-07-08_CALLHOOK_403_v5_CONSOLIDATED.md` (v2+v3+v4 → §1–§16, **0 lines lost**; **v4's false status line — "MITIGATED, rotation in progress" — corrected; the rotation has been PARKED since S128**). ⛔ **D153 and D157 now carry overturn markers** — the false principle had survived inside this document, unmarked, in three places. ✅ **D202 minted: a decision lives in the KB index, or it does not live.** *One writer per table*, applied to the record. Corollaries: carry the md5 of what you name (D188, D201); **no canonical document may be a delta** (F-23). Next free decision number: **D203.**

- **v1.55 — 09 Jul 2026 (Session 131, EOS-light consolidation — still NO live code touched):** Adds **§S131.11** and re-bases the callback-tracker document set. **The session's own lineage error, recorded:** Runbook v66 §0.2 and Design Spec v1.0 §1.1 called F-8's blast radius *"wider than the audit's headline"* — **it was not.** Audit v1.2 stated it in **S129**, in its title and its body. S131 re-derived an existing finding and mistook the re-derivation for an extension. **D190 and D201 were written in this session and violated in it, against the document that taught the lesson.** Fact unchanged; lineage wrong. Corrected in Runbook **v67**, Design Spec **v1.1**, and Audit **v1.3**'s F-8 lineage note. **No decision minted — D190 already covers it.** 📚 **Audit re-based to v1.3 (not re-audited):** its §0 had declared the **pre-fix** export (`8bdb6d4d…`, 465,195 B) while marking **F-9 🔴 open** (closed by D189, v64, verified) and **D153 `UNKNOWN`** (overturned by D190) — §S129's *"document set that misled its own reader"*, in the audit itself. §0 now carries both artefacts side by side and records that **`Dashboard.html` is byte-identical across them** (`034529a1…`), so **F-8, F-10, F-11, F-13, F-14 stand unre-derived**; only `WebApp.gs` differs, and F-9's reasoning is preserved as the record of *why*. F-8 re-priced (Fix A one line · **Fix B six lines, recommended**). §4's questions **2** (repo public — yes) and **4** (D153 — F-8) answered. **F-2's sixteen `catch (e) {}` untouched and still unclassified — A-6 (D180).** ✅ **Frontend Doc verified current and correct** — post-fix md5 in its header, `Staff Status` already attributed to staff, the `IN_` day key and `sendBackToStaff` already documented. **The healthiest document in the set.** Its own open question #4 was answered this session (nothing in the project writes `Staff Status`); that and the `SENT_BACK` → `getFollowups` L938 re-surface go into its v2, at the build session. 🗄️ **`F9_Decision_Sheet_D189_Session130.md` retired from project knowledge and archived** — a decision sheet's job ends when its decision is executed; it had also been omitted from the first cold kit, a gap in the close-out. **D188 and D201 are hereby read as applying to the document set, not only to code exports:** every canonical document naming an artefact carries that artefact's md5, and when the artefact moves the document is re-based or it lies. Next free decision number: **D202.**

- **v1.54 — 09 Jul 2026 (Session 131, EOS-light — NO live code touched):** Adds **§S131** and the companion **AI Review Layer Design Specification v1**. **Not one line of live code, config, trigger or property was changed; no GitHub commit.** The session's product is a finished design and eleven decisions. ✅ **Export verified from the artefact:** `4.json` (a filename carrying no information) asserted by hash — 465,074 bytes, md5 `449f3fe6981c2b75dfac0437126ece59`, **15 files**, `WebApp.gs` 1,647 lines / md5 `5173c3c7…`, `function setDashboardKey(`=0, `function setStaffKey(`=0 (counted by definition, not substring), `Dashboard.html` `034529a1…` / 2,738 lines, CR=0 throughout. **F-9 is closed in the artefact, not merely in the record.** 🔬 **F-8 anatomised:** `esc()` (L685) escapes `& < > "` but not `'`; `jsq()` (L729) escapes `\ '` but not `"` — F-10's two blind escapers. L912 passes `JSON.stringify` output (always double-quoted) through `jsq`; L923 pastes it into a `"`-delimited `onclick`; the attribute closes at the first `"` and **the handler is never installed**. Blast radius is **any `Patient_Master` match**, not just `known` (a bare UID breaks it too). Fix A = one line `esc(jsq(…))`; **Fix B = six lines, recommended** — hold the packet in a page-level map, which also kills the L1260 `catch(e){}` (A-3's first item) and delivers Block E's *stop embedding patient data in button markup*. `Dashboard.html` only; no D34 question. 🧩 **The two tile mechanisms, proven:** an incoming tile leaves only at WebApp **L247** on `Callbacks_Today.Staff Status` — and **nothing in all fifteen files has ever written that column** (every `setValue`/`setValues` searched; `Sheets.gs` preserves it, `STAFF_COL_COUNT: 2`). The only thing that has ever cleared an incoming tile is a human typing into the sheet by hand. Meanwhile **WebApp L1252–55 already computes `settle`/`escalate`/`retry` for incoming**, already writes it, and the client already renders it (L1382) — **the machine is built and nobody consumes its output.** 🔁 **The doctor→staff loop was built in Session 52:** `sendBackToStaff` (L1502) writes `SENT_BACK`; `getFollowups` (**L938**) re-surfaces the row as a staff tile under *"Sent back by doctor"* with the note, and auto-clears when staff file a newer outcome. `getEscalations` (L1387–1401) already attaches recording + transcript. **The owner's AI-review proposal is a second row source into an existing loop, not a new mechanism.** 🤖 **AI REVIEW LAYER DESIGNED AND LOCKED (D191–D201):** the judge **proposes**, the doctor **disposes**, the staff **act**. New **Axis 1 CONTACT** (18 codes, five groups; Group A is metadata-derived and costs no AI); Axis 2 OUTCOME unchanged and meaningful only under `spoke_patient`/`spoke_family_proxy`; **Axis 3 CONDUCT** split objective (auto-recorded) vs interpretive (doctor confirms before it becomes record), **no composite score**, per-flag exclusions, coach by recording not by number, **play-don't-export**, denominator honesty. Two-phase gate: **Phase 1 no machine-initiated tile movement at all**; Phase 2 unlocks auto-bounce for Groups A+B only at **100 refereed cards · ≥95% agreement · zero false-settles in the last 50** — *a false bounce costs one phone call; a false settle is invisible.* `patient_deceased` and `wrong_number` gaps closed; **`Do_Not_Call` tab** becomes the single enforcement point because the dashboard performs **zero writes** on `PATIENT_SHEET_ID` and `Followups_Today` is read-only to it. Dashboard becomes **sole writer of `Doctor_Verdicts`** (D193, parent D155); new property `AUDIT_SHEET_ID`; three spreadsheets now. **Blind judge preserved as a rule, not a convention (D198).** ⏱️ **The recording lag was never unknown (D200):** `recording_filename` arrives in the `call.end` webhook and `call_hook_capture.py` **already writes it to `Call_Durations` in real time**; recordings persist indefinitely, only links expire (24 h). Batch at 02:00/03:00 is a **choice, not a constraint**. 🔴 **Four findings raised, none fixed (D180):** **F-17** the public repo's `WebApp.gs` is the **pre-fix** file (`276dc197…`, both setters still defined) wearing the live file's name; **F-18** `verdict_review.py` prints overturned **D153** as a design justification and excused 19 incoming calls from scrutiny; **F-19** `call_hook_capture.py` **L385** discards every incoming call — `recording_filename` and all; **F-20** `asked_not_to_call` is a live outcome code with no enforcement anywhere. 📏 **Record defects:** Runbook v65 §3 and the S131 opener state the KB is **1,907 lines; the artefact is 1,906** (bytes 207,959 ✅, CR 0 ✅) — every other stated count in the project reproduces exactly, this one did not, and it slipped through in the very field D172 exists to protect. The KB's own **end-marker was stale** (claimed the CHANGELOG was the last section while §S130 sat after it) — corrected here. `Health.gs` differs live-vs-repo by **one trailing newline**, content identical. **`Source` is already taken** in `FU_OUTCOME_HEADERS` (source-on-medication) — a new provenance column must not reuse it. **`script_not_followed` and `no_closing` are specified and INOPERABLE (D199, status `UNKNOWN` per D166)** until the owner supplies the call script and the definition of a complete closing; a decision workbook was issued to collect both. **The D34 question is raised exactly once (§S131.10) and is the owner's to answer.** Every KB operation additive except the title line, the next-free-decision line, the stale end-marker, and this changelog entry; four anchors asserted unique before edit; byte/line/CR counts asserted before and after from the shell. Next free decision number: **D202.**

- **v1.53 — 09 Jul 2026 (Session 130, FULL EOS — one live Apps Script file changed: `WebApp.gs`):** Adds **§S130** and the companion **Frontend/Dashboard Documentation v1**. 🟢 **F-9 CLOSED (D189).** `setDashboardKey` and `setStaffKey` — two ungated top-level functions in `WebApp.gs`, callable by any anonymous browser via `google.script.run`, each overwriting a master access key — were **deleted** (8 lines out, a 4-line comment in). **A-0 first established the repo is PUBLIC** (control-tested: nonexistent repo→404, this repo→200+`Public`, anonymous `raw.githubusercontent.com` fetch succeeded) and that the **live `/exec` deployment ID is in it** (`sops/`, `launcher/portal.py`, `portal/portal.py`) — so **D187's bound was void**: function names and URL were public together. `DASH_KEY` value was NOT in the repo (all `?k=` hits are placeholders). Owner confirmed the chain by observation: incognito, no `?k=`, `/exec` served the login card → `doGet` serves the page to strangers; the page fires `getAccess(k)` unauthenticated → the `google.script.run` channel is open before any key. Rung 4 (calling the setter) was **proven by code, never executed** — executing it *is* the exploit. Blast radius measured from the artefact (transitive, depth-3): **55 browser-reachable functions, 28 ungated; not one of the 28 is called by the page** — the entire ungated surface is dead weight. The two setters are referenced exactly once each project-wide (their own definition): **deletion breaks nothing.** Fix built offline, `node --check` OK, CR=0; deployed as **version 64** on the single existing deployment (URL unchanged). Verified against a fresh export (md5 `449f3fe6981c2b75dfac0437126ece59`): `WebApp.gs` **1,647 lines / 79,666 bytes / md5 `5173c3c7…`**, `function setDashboardKey(`=0, `function setStaffKey(`=0, **other 14 files byte-identical**, `Dashboard.html` md5 `034529a1…` unchanged. Staff smoke tests: owner-key full, staff-key read-only, recordings play — all pass. **No exploitation:** `setDashboardKey` cannot read the old key back, so a still-valid `DASH_KEY` (owner logged in post-fix) proves it was never called; `STAFF_KEY` also unchanged (owner-confirmed in Script Properties). 🔴 **F-8 CONFIRMED, D153 OVERTURNED (D190).** The entire frontend was read and documented for the first time. `saveIncomingOutcome` writes to `Followup_Outcomes` stamping the `Section` column `'Incoming'`. **The live tab holds 400+ rows; exactly TWO carry Section=`Incoming` — 29 June and 1 July, both name-blank, both Identity=`non_patient`.** These are precisely the two cases the F-8 defect *permits* (no `Patient_Master` match → L912 emits `'{}'` → valid `onclick`). **Zero named callers, zero known patients, ever.** So **D153 ("staff never file incoming outcomes — workflow finding") was wrong: not a habit but an impossibility** — the `Log outcome ▾` button has been dead for every known patient since v18.19 shipped, and the record mistook the symptom for a staff choice, then relied on it for the Stage-3 join. **F-8's fix is NOT drafted this session** — §5 of the Frontend Doc shows the incoming tile clears on `Callbacks_Today.Staff Status`, not on outcome, so a working button alone won't make it behave like a follow-up tile; F-8 needs its own decision sheet (S131). 🧭 **New: F-16** — `PAGE_BUILD` is a page-file stamp, not a server-version stamp; the served page cannot report which `WebApp.gs` version `/exec` runs (owner saw `v18.19·S124` after deploying WebApp v64 and reasonably asked). Cosmetic-but-misleading (D178 pattern); logged, not fixed. **Structural findings recorded in the Frontend Doc:** two spreadsheets not one (`SHEET_ID` operational + `PATIENT_SHEET_ID` patient DB); `Followup_Outcomes` has two writers (incoming+follow-up, told apart only by the `IN_`/`Section` marker — bears on the D158 join); incoming vs follow-up tiles remove differently (status-driven vs outcome-driven). Every KB operation additive except the title line, the next-free-decision line, and this changelog entry; three anchors asserted unique before edit; byte/line/CR counts asserted before and after from the shell. Next free decision number: **D191.**


- **v1.52 — 09 Jul 2026 (Session 129, EOS-LIGHT — no code changed, no file written, no trigger touched, no property set):** Adds **§S129**. 📖 **Audit pass 3, item 1 COMPLETE: `Dashboard.html` read in full** — 2,738 lines, 157,611 bytes, md5 `034529a124c6bfab8aec2b675620dfec`, against a **fresh export** supplied by the owner (465,195 bytes, md5 `8bdb6d4dfdb0a331c5048b3c0fccf367`, 15 files). 🔴 **F-8 — the incoming-call "Log outcome" button is DEAD for every patient in `Patient_Master`**: `JSON.stringify` emits double quotes, `jsq()` does not escape them, and the `onclick` attribute is double-quoted, so the handler never compiles. Established by emitting and parsing the HTML, not by reading it. **This collides with D153** ("staff never file outcomes for incoming calls — workflow finding, not a gap"), whose population is exactly the one whose button is dead; **D153 is now `UNKNOWN`** pending one click on the live dashboard, and that evidence expires the moment F-8 is fixed. 🔴 **F-9 — F-1 is wrong**: not seven ungated globals but **twenty-seven of fifty-five**, and two of them (`setDashboardKey`, `setStaffKey`) overwrite the doctor's key — **unauthenticated privilege escalation to a full PHI read, plus owner lockout**, not the "not exfiltration" F-1 published (**D186**). Server-side role enforcement is otherwise **sound**; `removeTriggers` / `removeHealthTrigger` are anonymous trigger-killers but `Health.gs`'s silence catches them. Both setters sit in `WebApp.gs`, which **D34** forbids touching → **D187**, parked *last but not silenced*. Also: **F-10** two half-escapers (`esc()` misses `'`, `jsq()` misses `"`) — F-8 is the first field that tested the gap; **F-11** the key lives in `localStorage` in cleartext with **no sign-out anywhere in 2,738 lines**; **F-12** ~9 server calls/min/tab over F-6's fifteen whole-tab reads, one 3-minute call re-reading `Call_Durations` thirty times, **daily budget `UNKNOWN` and unwatched**; **F-13** the UTC-date bug D156 fixed still survives at L1800, and *"local" is not "IST"*; **F-14** three of seventeen client catches are wrong, and the one at L1260 is what hid F-8; **F-15** the `documents` OAuth scope is held for `Probe.gs` alone. 🧭 **The incoming-call console designed** (D181–D184): the receiver already receives every incoming call and discards it (37 of 66 webhooks on 09-Jul), so this is **subtraction, not integration** — no Lokesh, no credential, no token. Unknown numbers get tiles (**D182**); nothing ends the day unlogged, both directions sweep to the doctor at 21:30 (**D183**); the tile fires at **hangup, not ring** (**D184**) — because Apps Script cannot push, and because *while the phone is ringing the receptionist is answering the phone*. **D185**: Block C (one clock · bounded reads · bundled calls · `CacheService` · quota headroom) precedes Block D. Owner's quota question answered and recorded in §S129. ⚠️ **D188 — a filename is not provenance:** the export in project knowledge named `…_S124.json` carries `PAGE_BUILD v18.18 · S57` and no `Health.gs`; reading it, the assistant asserted 2,676 lines and declared five canonical documents defective. **The record was right; the disk was the wrong disk.** The claim was withdrawn before any document was edited on it. Every operation in the v1.51 → v1.52 bump was additive except the title line, the next-free-decision number, and the end-of-file assertion; seven anchors asserted unique before edit; byte/line/CR counts asserted before and after, from the shell; the pre-edit md5 re-verified after the guard threw once. Next free decision number: **D189.**
- **v1.51 — 09 Jul 2026 (Session 128, FULL EOS — new live Apps Script file `Health.gs`; no VPS code, no `.env`, no restart):** Adds **§S128B**. 🟢 **`Health.gs` v2.2 LIVE** in the Clinic Callback Tracker Apps Script project — a daily heartbeat that emails every morning, green or not, so that its **absence** is the signal. Read-only (zero write calls, verified), `WebApp.gs` untouched (D34), no new OAuth scopes, zero collisions against 152 existing functions. v1 shipped at 10:23 and was **wrong three times**, each caught by the owner reading a number: `today=0` on a nightly tab (**D177**), `Call_Durations` unmonitored (**D178**), and `370 awaiting review` — a lump with no clock, actually `3 today · 10 yesterday · 357 aged out` (**D179**). **The four clocks are now recorded** (`Followups_Today` · `Followup_Outcomes` · `Call_Durations` · `Call_Feed` · `Call_Recordings` · `Call_Transcripts`), with `Call_Feed` (nightly 21:30, 14-day clear-and-rewrite) and `Call_Durations` (VPS receiver, **console-dialled OBD calls only** — 66 webhooks → 29 rows on 09-Jul) established as different tables on different clocks. 📋 **Apps Script AUDIT opened** (`Clinic_Callback_Tracker_AppsScript_Audit_v1_1.md`), passes 1–2 complete, **nothing fixed (D180)**: F-0 `Call_Feed` **is published to the web** (deliberate; ~3,000 patient mobiles + agent names public; `CallField.gs`'s "PHI never leaves the clinic" is false as written; accepted risk, bound recorded) · F-1 `doGet` has no key, seven ungated globals, **no exfiltration** · F-2 sixteen silent `catch (e) {}` · F-3 `Followup_Outcomes` has three writers under a "one-writer tab" comment · F-4 `logOutcome` dead, `Outcomes_Log` never created. Rotation remains **PARKED** (§S128). Next free decision number: **D181.**
- **v1.50 — 09 Jul 2026 (Session 128, EOS-LIGHT — no code changed, `.env` untouched, nothing restarted):** Adds **§S128**. ⏸️ **`CALLHOOK_SECRET` rotation steps 3 and 4 are PARKED by owner decision** — not abandoned, not pending, and removed from session-start review. Steps 1 and 2 remain complete; the dual-key gate (D162) permits the panel and the VPS to disagree indefinitely, so **nothing degrades and there is no clock.** New **PARKED ITEMS REGISTER** created to hold such items out of the backlog. New **D176 — a procedure must never instruct a human to display a secret**: Runbook v61 §5 recorded a `grep` of the live key "for safekeeping"; it was executed at S128 open and `key_ea20dd` entered a chat transcript. **Both keys are now exposed; the exposure's bound is stated in §S128** (POST to the call-webhook receiver only — injects rows into `Call_Feed`; confers no patient-data read, no call placement, no panel or dashboard access; data-integrity, not breach). **When the rotation resumes, a third key must be generated — `key_ea20dd` must never be pasted into the panel.** Single status reading taken: service active, 66 accepted, `refused today: none`, `on PREVIOUS key/30min = 2`, blank startup line (known cosmetic defect, not a fault). Session's deeper finding: four sessions of command-and-paste were the symptom of a **missing instrument** — tracker health was unobservable without the owner's terminal. Remedy: `Health.gs` (Runbook v62 §2 item 1). Every operation in the v1.49 → v1.50 bump was additive except the title line, four `§12A` state lines, the end-of-file assertion, and the next-free-decision number; ten anchors asserted unique before edit; byte/line/CR counts asserted before and after, from the shell. Next free decision number: **D177.**
- **v1.49 — 09 Jul 2026 (Sessions 125–127, FULL EOS — `.env` written, service restarted, new VPS script):** Folds in **§S125** (dual-key receiver + reject logging + `callhook_watchdog.py`; D162–D165), **§S126** (housekeeping that broke the record five times; D166–D169), and **§S127** (rotation steps 1 and 2; D170–D175). 🟢 **`CALLHOOK_SECRET` rotation STEPS 1 AND 2 COMPLETE** — step 1 08-Jul 23:38:00 (dual-key gate armed; the 21:55 v2 bytes finally loaded), step 2 09-Jul 09:05:58 (`current=key_ea20dd  previous=key_db8972  -> ROTATION IN PROGRESS`), verified on live traffic: 64 calls accepted, 12 on the previous key in 30 min, **0 refused**. 🔴 **Steps 3 (MyOperator panel) and 4 (clear `PREV`) remain OPEN; the step-4 command is deliberately withheld until step 3 lands (D173).** The old 12-char `@` key `key_db8972` is still live and still exposed. New: `rotate_callhook.sh` on the VPS (D171) — eleven guards, self-deleting candidate, `cmp`-validated rollback, keys masked. **§12 frozen as a historical artefact; new §12A carries current state and wins (D175)** — resolves all four judgements of `KB_SWAP_BLOCKER_S127.md`. **`D161` confirmed never minted.** `D155`–`D160` re-homed into the DECISIONS INDEX **by reference, not by movement**. Line-1 title corrected (it read `v1.47` in a `v1.48` file) and an **end-of-file assertion added** — the KB was the only canonical doc without one. Every operation additive except the title. Open: panel step 3 · `ANTHROPIC_API_KEY len=111` unaccounted in `.env` · watchdog's two defects · `rotate_callhook.sh status` startup-line window · D158 join defect · 0 cards refereed. Next free decision number: **D176.**
- **v1.48 — 08 Jul 2026 (Session 124, FULL EOS — new VPS script + live dashboard file + live secret realigned):** Added §124. **Verdict Analysis Layer BUILT** (`verdict_review.py`, D155; md5 `af6622e4edc3f454cf0bfed128c4f76b`, selftest 117/117, ₹0): rolling-7-day one-patient-per-screen `Verdict_Review` + `Doctor_Verdicts` ground-truth ledger, full transcripts in collapsed row-groups with the AI's evidence highlighted, harvest-before-redraw, opaque export-safe tokens, one-writer-per-table preserved. **Duration gate now FAILS OPEN** (`Dashboard.html` v18.19, D156; md5 `034529a124c6bfab8aec2b675620dfec`) — two bugs found in the LIVE export (result states never persisted; a ref-less tile spun forever), and no verification mechanism may block a staff member from recording what a patient said. 🔴 **`CALLHOOK_SECRET_MISMATCH_403` RECURRED** (D159): the MyOperator panel had been sending the old 12-char `@` key since 06-Jul 13:41 — the S94 fix survived exactly one verification call; 4,449 silent 403s across three days; fixed by aligning the VPS to the panel (10:28:32). Corrections: **D157** (06-Jul was 36 outgoing / 26 incoming; real match rate **16/20 = 80%**, not 73%) and **D158** (the D150 join can bind an outgoing claim to an earlier incoming call — proven on `…5227`; display-mitigated only, **join still defective**). **D160**: the live Apps Script export, not GitHub, is the canonical dashboard. Open: agent + Clinic ID missing from `Call_Verdicts`; the 403 detector; 0 cards refereed. Next free decision number: **D161**.
- **v1.47 — 08 Jul 2026 (Session 123, FULL EOS — live VPS script replaced):** Added §123. Stage-3 claim-match join REDESIGNED in `call_verdict.py` (D150): the §122.4 ±45-min window (0/15) replaced by a whole-day, phone-keyed FORWARD window (−10 min … +28 h) with in-order pairing and a Match Confidence stamp — root cause was staff morning-batch filing (claim `When` = filing-time, not call-time). Row ENRICHED (D152: full Patient Number, Recording Link joined from Stage-1 `Call_Recordings`, Match Confidence, name/Clinic-ID fallback). Judge-once-fill-later upsert + header fail-safe (D151); re-runs idempotent. Proven on 06-Jul (62 judged, 0 failed; 16/22 outgoing Match = 73%; 40 incoming correctly "No claim logged" — D153: staff never file incoming outcomes). md5 `8c8ae1656056d8d1b2dec1b4776fe5c9`, selftest 33/33, backup `call_verdict_BACKUP_S123_pre_join_redesign.py`. Verdict Analysis Layer design-locked for S124 (D154). Prompt/flags/blind-judge unchanged. Next free decision number: **D155**.
- **v1.46 — 07 Jul 2026 (Session 122, FULL EOS — new live VPS script + auth fix):** Added §122. Stage-3 AI judge (`call_verdict.py`) DESIGNED, BUILT, INSTALLED, and PROVEN — Claude Haiku, blind transcript-only judge, live-dashboard vocabularies, six safety flags, evidence excerpts, three-field version-stamped record, its own `Call_Verdicts` tab in the doctor-only sheet, calibration-first with no actions in v1 (D149; parent D62). md5 `bb17720d4857e3c040e8c89e7cc2e095`, selftest 24/24, first real run 15/15. 🔴 Drive-OAuth-token incident fixed: app was in Testing status (7-day token expiry) → published to In production (permanent) + token re-minted (immediate); nightly pipeline confirmed unharmed. Finding: the ±45-min claim-match join is too weak for real staff batch-filing — redesign is next (§122.4). Two owner design files folded in (adopted evidence/flags/versioning; deferred 18-cat taxonomy, action-triggering, auto-accept). Next free decision number: **D150**.
- **v1.45 — 07 Jul 2026 (Sessions 103–121, FULL EOS — live PC-side code changed):** Added §107 (S108 data-folder / Drive-sync evaluation — VERIFIED-NORMAL, D147) and §121 (Item 3 staff call-sheet cap + Hard-to-Reach split, D148). §121.0 records that Item 2 (auto-settle on return) was found ALREADY BUILT and LIVE (verified S106, 249/493 settled). `processor.py` changed and live — now carries D146 de-dupe + D148 cap/split; new md5 `171a090645da130a4f4cbb0c0b102f22`; backup `processor_BACKUP_S115_pre_Item3.py`. Decisions **D147, D148**. Next free decision number: **D149**.
- **v1.43 — 07 Jul 2026 (Session 101, EOS-light):** Added §95–100 recording the S95–S100
  documentation-consolidation arc (KB→v1.42, Umbrella→v1.31, Runbook→v53, cold-kit recovery
  of Umbrella v1.28+v1.19, GitHub-archive findings). Recorded the owner directive that
  canonical docs are single consolidated files, not delta chains (§95.2). NO live-systems
  content changed — every prior section stands verbatim. No new decisions; next free D146.
- **v1.42 — 07 Jul 2026 (Session 95, EOS-light):** FULL CONSOLIDATION. Folded v1.38 base +
  v1.39 (S75) + v1.40 (S93) + v1.41 (S94) into one self-contained master. Single unified
  Decisions Index (D121–D145) with amendment cross-references; merged Surveillance
  forward-notes; added Open Backlog Snapshot; one changelog. No content altered — verbatim
  fold-in only. Recorded that no standalone v1.37 file exists (its content lives in the v1.38
  base, present in §73). Next free decision number: D147 (D146 used at §102).
- **v1.44 — 07 Jul 2026 (Session 102):** Added §102. **FULL EOS — live PC-side code changed.** Staff call-sheet de-duplication built into `processor.py` (`build_staff_call_workbook`): one row per patient (mobile+name+diagnosis), latest `Due_Date` kept, older cycles hidden with no note, reinstated rows win, fail-safe fallback. Verified live 07-Jul (236 → 214 follow-up rows, zero duplicates). Decision **D146**. Audit workbook left un-deduped by design. Option B (per-patient latest-state join) added to priority backlog. Next free decision number: **D147**.
- **v1.41 — 07 Jul 2026 (Session 94):** Added §94. Two live fixes: call-webhook 403 outage
  (`.env` run-on-line corruption → clean key rotation + panel re-sync, D144) and doctor
  console `isGenericAgent_` undefined-function bug (D143). New fault code
  `CALLHOOK_SECRET_MISMATCH_403`. Six-item forward agenda captured (design only). Hygiene
  note D145. Decisions index → D145.
- **v1.40 — 06 Jul 2026 (Session 93):** Added §93. Track 1 Step 5 — PC-local Vitals & Plan
  front-end COMPLETE (Flask app port 5057, bilingual archive PDFs, diagnosis pre-fill from
  taxonomy master). Decisions D139–D142. Engine `clinic_writer.py` bilingual-PDF change.
- **v1.39 — 05 Jul 2026 (Session 75):** Added §75. Track 1 Step 4 — PC-local write-path
  `clinic_writer.py` BUILT + INSTALLED (20/20 selftest). Three architecture pivots
  (PC-local not VPS; staff BP page retired; storage home = clinic PC). Decisions D135–D138.
- **v1.38 — 05 Jul 2026 (Session 74, consolidation):** Consolidated master. Carried the
  v1.36 collapse (v1.33 → v1.34 → v1.35 + S67) and folded in the v1.37 delta (S73 build:
  plan_ledger row-assembly v26 + printout-PDF archiving). Decisions D132–D134.

---


## §S130 — F-9 closed, the frontend mapped, and a decision that had been backwards for months
**09 July 2026 · Session 130 · FULL EOS · one live Apps Script file changed (`WebApp.gs` → version 64); no VPS code, no `.env`, no trigger, no property**

The session opened on Block A-0 and did not leave Block A. It closed the one finding in this project where a stranger with a public URL could take the clinic away from its owner, then read the front end end-to-end for the first time in 130 sessions and found a recorded decision standing exactly backwards.

### The repo is public, and that voided the reason F-9 was parked
A-0 asked one question: is the GitHub repo private? It is **public** — established with a control (a nonexistent repo returns 404; this one returns 200, shows the `Public` label, and serves `README.md` over anonymous `raw.githubusercontent.com`, which carries no credentials). The **live `/exec` deployment ID is in the public repo** (`sops/SOP_Dashboard_AppScript.md`, `launcher/portal.py`, `portal/portal.py`). D187 had parked F-9 last on the belief that *"the function names are only in the private repo, so the URL alone is not enough."* Both halves — URL and names — are public, together. **The bound was void.** The one mercy: the `DASH_KEY` value is not in the repo; every `?k=` there is a placeholder (`?k=KEY`, `?k=DASHKEY`).

Making the repo private was considered and **rejected**: git history keeps the leak, anyone who cloned or indexed it already has it, and the assistant needs public read for this very session. Obscurity was never the control. **The gate is the control.**

### The chain, observed not assumed
Owner opened `/exec` in incognito with no `?k=`. The login card rendered → `doGet(e)` never reads `e`; it serves the page to anyone. The served page fires `google.script.run…getAccess(k)` on load with `k` empty → the invocation channel is open before any key is entered. `setDashboardKey(k)` is a top-level, non-underscore, gateless function that does `setProperty('DASH_KEY', k)`. A stranger calls it, then loads `?k=<their value>`, and `dashRole_` returns `'full'`: every patient row, every mobile, the WhatsApp Reply box — and the owner locked out at the same instant. **Rung 4 (the actual call) was proven by three lines of gateless code and deliberately never executed — the call *is* the exploit.**

### Blast radius, from the artefact
Every top-level function in every `.gs`, effects resolved transitively to depth 3 (a function that calls a helper that writes, writes): **55 browser-reachable, 28 ungated.** The load-bearing fact: **the page calls 24 server functions and every one of them is gated; not one of the 28 ungated functions is called by the page.** The ungated surface has no legitimate browser use at all. `setDashboardKey`/`setStaffKey` occur exactly once each in the whole 15-file project — their own definition. Deleting them cannot break anything, and that was proven, not asserted.

### The fix (D189)
Eight lines deleted from `WebApp.gs`, replaced by a 4-line comment recording why. Built offline, `node --check` clean, CR=0. **D34 was suspended for this one deletion (D189) and resumed immediately** — the edit *removes* code, adds no function, no dependency. Deployed as **version 64** on the single existing deployment; the `/exec` URL is unchanged (never a new deployment — that moves the URL). Verified against a fresh export: `WebApp.gs` 1,647 lines / 79,666 bytes / md5 `5173c3c7…`; both setters gone; the other 14 files byte-identical; `Dashboard.html` untouched. Smoke tests green (owner full, staff read-only, recordings play). **No exploitation could have occurred silently:** the setters cannot read the old key back, so a `DASH_KEY` that still works (owner logged in after the fix) is proof it was never overwritten; `STAFF_KEY` was also owner-confirmed unchanged.

*One process note, recorded honestly:* the deployed-version md5 matched the offline build byte-for-byte, and the verification checker itself first mis-fired — it counted the substring `setDashboardKey` (which now appears in the explanatory comment) rather than the definition `function setDashboardKey(`. The assertion caught the assistant, the assistant looked, and the fault was in the instrument, not the file. **A count without its scope is a wall (D179) — broken in the very check built to catch a bad paste, and caught.**

### The frontend, and the decision that was backwards
The whole page was read and documented (companion: **Frontend/Dashboard Documentation v1**). The map settled a puzzle the owner raised directly: *tiles vanish when staff fill outcomes, so how can the outcome button be dead?* The answer is that **these are two unrelated mechanisms.** A tile leaves the pending list when the **`Staff Status`** column of `Callbacks_Today` reads a "done" word — read by `isDoneStatus_`. The outcome card writes to a **different tab** (`Followup_Outcomes`) and **never touches `Staff Status`**; `inSave` on success only clears the card, not the tile. Vanishing tiles and a dead button coexist perfectly.

Then the evidence. `saveIncomingOutcome` stamps `Section='Incoming'`. The live `Followup_Outcomes` holds 400+ rows; **exactly two are `Incoming` — 29 June and 1 July, both name-blank, both `non_patient`** — the only two cases the defect allows. **F-8 confirmed: the incoming `Log outcome ▾` button has never once worked for a patient the clinic knows.** And so **D153 is overturned (D190):** it recorded *"staff never file outcomes for incoming calls — workflow finding, not a gap,"* but the tab proves it was **not a choice, an impossibility.** A rendering defect was written into the record as a staff habit and then relied upon for the Stage-3 join. **The inverted record, not the button, is the finding.**

F-8's *fix* is not drafted here: because incoming tiles clear on status, not outcome, repairing the button alone would leave it logging without clearing — its own confusion. F-8 gets a decision sheet in S131, together with the tile-behaviour question.

### Decisions minted
- **D189 — Delete, don't guard, an ungated function that nothing calls; and suspend D34 by name for exactly one removal.** F-9's setters had no caller, no trigger, no page use. A guard would add code to the file D34 protects, to defend a function no one uses. Deletion, with D34 named-suspended for that single edit and resumed on verification, is the minimal correct move. Blast radius is assessed from the artefact's own call graph, not from an audit's summary of it (parent D186).
- **D190 — A recorded workflow finding must be verified against the artefact before it is relied upon; absence of data is not evidence of a habit.** D153 read "no incoming outcomes" as "staff choose not to file them" and built the Stage-3 join on it. The tab showed the write path was broken. When the record explains a gap by human behaviour, check that the machine *could* have produced the data at all. Sibling of D188 (a filename is not provenance) and D166 (`UNKNOWN` is a valid entry).
- **F-16 (finding, not a decision) — `PAGE_BUILD` is a page stamp mistaken for a server stamp.** The served page cannot report which `WebApp.gs` version `/exec` runs. Logged; a one-line server-version echo would close it (D178 pattern).



---

## §S131 — The AI review layer, designed and not built; F-8 anatomised; four findings

**Session type: EOS-light. Not one line of live code was touched.** No Apps Script deploy, no VPS
file, no `.env`, no trigger, no property, no GitHub commit. The session's product is a design that
is finished and a set of decisions that are made. This section is the dedicated record of that
design, written so that the build session that follows it needs no further conversation.

### S131.0 — The export was verified, and the record was checked against two disks

The opener instructed: *assert the md5, not the filename* (D188). The Apps Script export arrived
named `4.json` — a filename that carries no information at all.

- **Whole blob:** 465,074 bytes · md5 **`449f3fe6981c2b75dfac0437126ece59`** — exact match to the
  value Runbook v65 §0.2 records for the post-fix export. **15 files.**
- `WebApp.gs` **1,647 lines**, md5 `5173c3c7…`, `function setDashboardKey(` **= 0**,
  `function setStaffKey(` **= 0** (counted by definition, not substring — D179).
- `Dashboard.html` md5 `034529a1…`, 2,738 lines. `Health.gs` 401 lines. **CR = 0 across all 15.**

**F-9 is closed in the artefact, not merely in the record.**

Two process facts belong here, both uncomfortable and both instructive.

1. The assistant reported the export **absent from project knowledge**, on the strength of a
   directory listing. The listing was true of the disk at that moment. **The file manifest supplied
   in the assistant's own opening context already named `4.json`.** The absence claim was made from
   one disk while the record described another. → **D201.**
2. The **repo** was then used as a substitute source and md5-matched against the Runbook's recorded
   hashes: `Dashboard.html` `034529a1…` ✅, `WebApp_v19_D189.gs` `5173c3c7…` ✅, `WebApp.gs`
   `276dc197…` = the **pre-fix rollback point**. Three independent matches. That check is what
   surfaced **F-17**.

### S131.1 — F-8, anatomised from the artefact

There are **two escapers in `Dashboard.html`, each blind exactly where the other sees** (F-10):

- `esc()` (**L685**) escapes `&` `<` `>` `"` — **not** `'`
- `jsq()` (**L729**) escapes `\` `'` — **not** `"`

**L912** — `var pj = e.patient ? jsq(JSON.stringify({name,uid,last,dx})) : '{}';`
`JSON.stringify` always emits `"`. `jsq` does not touch `"`. The packet leaves L912 carrying raw
double quotes.

**L923** pastes it into a button whose `onclick` attribute is **delimited by `"`**. The browser stops
the attribute at the first `"` inside the packet and tries to compile
`inOpen('in_98…_0','9812345678',true,'{` — an unterminated string. **The handler is never
installed.** The button renders perfectly and does nothing, silently, and no error appears at click
time because the failure happened when the page was drawn.

**The blast radius is wider than "known patients."** The breaking condition is `e.patient` being
*truthy* — **any number matching `Patient_Master` at all**, including a bare UID with no name.
`known` (which requires a name or a diagnosis) is a strictly narrower set.

**Fix A** — one line, and exactly what F-10 prescribes: `esc(jsq(JSON.stringify({…})))`. Order is not
arbitrary: the browser decodes HTML entities *first*, then compiles the JavaScript, so the value must
be JS-escaped on the inside and HTML-escaped on the outside.

**Fix B** — six lines: hold the packet in a page-level map keyed by slot id and pass only the id.
This closes F-8, **removes the `catch(e){}` at L1260** (A-3's first item, the one that hid F-8 —
there is no `JSON.parse` left to fail), delivers the **Block E** item *"stop embedding patient data
in button markup"*, and takes patient name / UID / diagnosis out of the page's HTML source
altogether. Both fixes touch `Dashboard.html` only. **No server file. No D34 question. Rollback =
redeploy the previous version.** → **Fix B is the recommendation.**

### S131.2 — The two tile mechanisms, and the line that has never been written

A **follow-up** tile leaves because `saveFollowupOutcome` classifies the code `settle`/`escalate`/
`retry` (**WebApp L1140–41**), settling rows land in `Followups_Settled`, the reader excludes them,
and the client hides the row immediately with an undo window (`fuPending`). **The same system both
decides and clears.**

An **incoming** tile leaves at **WebApp L247**, one line:

```js
if (isDoneStatus_(st)) handled.push(item); else pending.push(item);
```

…where `st` is the **`Staff Status`** cell of `Callbacks_Today`.

**Every `setValue` and `setValues` in all fifteen files was searched. Nothing in this project has ever
written `Staff Status`.** `Sheets.gs` deliberately preserves it (`STAFF_COL_COUNT: 2` — the last two
columns are staff-owned) and writes only `Auto-Status`. **The only thing that has ever cleared an
incoming tile is a human typing a word into the Google Sheet by hand.** The dashboard cannot clear
its own tile, and a repaired button would not have cleared it either.

And the machine to fix it already exists, unused. **WebApp L1252–55:**

```js
settle = escalate ? 'escalate' : (IN_NONSETTLING[resolution] ? 'retry' : 'settle');
```

`IN_NONSETTLING` already holds `needs_callback` and `cant_communicate`. The verdict is already
written into `Followup_Outcomes`. The client at **L1382** already renders *"saved — stays for
callback"* on `retry`. **The whole machine is built and nobody consumes its output.**

### S131.3 — The doctor→staff return loop was built in Session 52 and nobody said so

`sendBackToStaff` (**WebApp L1502**) writes `SENT_BACK` plus the doctor's free-text note into
`Followup_Escalations`. `getFollowups` (**L938**) reads it back and rebuilds it as a staff tile in a
section literally named **"Sent back by doctor"** — carrying the note, the original outcome reason,
who filed it, when, and the matched call. It **auto-clears** the moment staff file a newer outcome
(`lastOut[key] >= sentBackWhen`).

`getEscalations` (**L1387–1401**, v18.6/v18.8) already attaches the **recording and the transcript**
to each escalated row via `OL_todayCallsAndMissed_`, `OL_transcriptsByKey_`, and `escPick_` — which
deliberately selects the call **at or just before** the outcome was saved, never one logged hours
later.

**The owner's proposal — "the AI verdict lands in my dashboard, in a section where I verify it and
send the tile back to staff" — is therefore not a new mechanism. It is a second row source into a
loop that has been live for eighty sessions.**

### S131.4 — Where the verdict lives, and the writer question it forces

**D149** and **D155**: `call_verdict.py` writes `Call_Verdicts` into the **doctor-only "Call Audit"
sheet** — *a third spreadsheet.* `verdict_review.py` owns `Verdict_Review` and `Doctor_Verdicts` in
that same file, the latter described as *"the durable ground-truth ledger."*

**The Apps Script has no handle on it.** Its entire property list is `SHEET_ID · PATIENT_SHEET_ID ·
DASH_KEY · STAFF_KEY · AKEY_* · MYOP_TOKEN · NTFY_TOPIC · SUMMARY_EMAIL · SUMMARY_NTFY ·
CALL_API_SECRET · SEND_API_SECRET · SECRET_KEY`. Zero references to the Call Audit sheet. A new
property **`AUDIT_SHEET_ID`** is required, and the dashboard will read **three** spreadsheets.

Three options were put and one was chosen. → **D193.**

### S131.5 — The recording lag was never unknown

The assistant asked for a measurement. The owner replied that it had already been studied. **He was
right, and the artefacts say so:**

- `MyOperator_Call_API_Master_Reference` **§9.1** — *"both `call.end` and `call.summary` carry
  `recording_filename` in `payload`."*
- **§6** — `/recordings/link?file=…` returns a fresh link valid 24 h, while *"recordings themselves
  persist on MyOperator's cloud indefinitely; only the link expires."*
- `call_hook_capture.py` **L183–186** — `HEADER` for `Call_Durations` **already contains
  `recording_filename`**; **L408** reads it out of the `call.end` payload; it is written to the sheet
  **in real time, at hangup.**

**There is no lag to measure.** The 02:00 archive and the 03:00 transcription are **batch by choice,
not by necessity.** → **D200.**

But **L385** of the same receiver:

```python
if category != "obd" or not client_ref_id:
    return None
```

**Every incoming call, and every outgoing call not dialled from the console, is discarded at the
door — recording filename and all.** → **F-19**, and Block D's first line depends on it.

### S131.6 — THE AI REVIEW LAYER — design, locked

> **The judge proposes. The doctor disposes. The staff act.**
> Nothing about that sentence is a slogan; each clause is a writer of a different table.

#### Axis 1 — CONTACT. Exactly one per call. *"Did a usable conversation happen, and with whom?"*

**Group A — never connected. No recording exists, so the AI never sees these. Metadata only, zero AI cost.**
Source: `Call_Durations.customer_result`, `status`, `total_duration`, and `recording_filename` empty.

| Code | Disposition |
|---|---|
| `no_answer` | to staff · 3-attempt cap · then `exhausted` → doctor |
| `busy` | to staff · 3-attempt cap |
| `unreachable` | to staff · 3-attempt cap |
| `call_failed` | to staff · 3-attempt cap |
| `number_invalid` | **never to staff.** Definitive action → `Do_Not_Call` (D194) |

**Group B — connected, no usable human conversation.** To staff with the reason and the recording,
**and in parallel a flagged card on the doctor's tab.** 3-attempt cap. `voicemail` ×3 routes to the
**doctor**, not to `exhausted`.

`voicemail` · `ivr_or_bot` · `answered_silent` · `audio_unusable` · `call_dropped`
— and **`language_barrier` → doctor only** (it needs a different agent, not another attempt).

**Group C — a human answered, but not the right one. All escalate to the doctor with a flag.**

| Code | Disposition |
|---|---|
| `wrong_number` | **settles the case AND flags the doctor** so the number can be corrected. Not a queue item. The 3-attempt cap is meaningless on a number that was never the patient's |
| `spoke_other_person` | flagged card → doctor |
| `callback_requested` | **to staff with the stated time**; informational on the doctor's tab |

**Group D — the right person.**

| Code | Disposition |
|---|---|
| `spoke_patient` | outcome stands |
| `spoke_family_proxy` | outcome stands. *The commonest case in this practice and today entirely invisible to the record* |
| `patient_deceased` | **settles permanently.** Number → `Do_Not_Call`. **Only the doctor may set this flag.** Never re-dialled |

**Group E** — `unclear`: no default. It waits on the doctor's tab.

#### Axis 2 — OUTCOME. **Unchanged.**
The existing 11 follow-up codes and the incoming lists. **Meaningful only when Axis 1 is
`spoke_patient` or `spoke_family_proxy`.** Every other contact code makes the outcome field moot —
which is precisely the invisible failure this layer closes: today a staff member can file `coming`
on a call that was a voicemail, and nothing in the system objects.

#### Axis 3 — CONDUCT. Zero or more. **Never moves a tile.**

**Objective — verifiable from a transcript. Recorded and reported automatically.**
`no_identification` · `no_closing` · `script_not_followed` · `unauthorised_promise`

**Interpretive — a machine inferring tone from Hindi, sometimes over poor audio.**
`rude_or_curt` · `talked_over_patient`
**Brusque telephone Hindi is not rudeness.** These are raised as a card; the doctor listens; **his
confirmation writes the record.** Never counted as fact until then.

**No composite score. Six binary checks. Nothing is averaged into a number.** → **D197.**

**Per-flag applicability, hard-coded.** You cannot follow a script at a voicemail. No conduct
assessment on `no_answer`, `busy`, `unreachable`, `call_failed`, `voicemail`, `ivr_or_bot`,
`answered_silent`, `call_dropped`, `audio_unusable`, `language_barrier`, `patient_deceased`.
Applicability is **per flag, not per call**: on a `wrong_number`, *did you say which clinic was
calling* still applies; *did you follow the follow-up script* does not.

**The default report names nobody:** *"This week the clinic identified itself on 46 of 52 calls; the
next step was confirmed on 31 of 52."* That is standardization. It creates no league table. The
per-agent view exists and is **doctor-only**, behind the same `dashRole_ === 'full'` gate as the
escalations.

**Coaching is by recording, not by number.** The evidence excerpt and the audio are already attached
(D152, D155). **Play, don't export**: the training pack renders on screen; it does not become a file
carrying patients' voices out of the clinic. **Denominator honesty**: *21 of 52*, never a bare *21*
(D179).

#### The owner's standing impression, recorded as a hypothesis and not as a fact

> *"conduct is good · script is strictly not followed · closing is weakest"*

Both stated problems sit in the **objective** column, which a machine can verify without judging
tone. The **interpretive** column — the risky half — is the one the owner says is already fine.

**This is an impression, not a measurement, and it is exactly the shape of D190**: a human
explanation of a gap, relied upon before the artefact was checked. *"Staff never file incoming
outcomes"* felt true for months. **The training pack's first job is to test these three sentences,
not to assume them.** If conduct proves not to be uniformly good, that finding outranks everything
else in the pack.

#### The blocker that is honest rather than fatal

The judge can report `script_not_followed` **only if it has been told the script**, and `no_closing`
**only if a closing has been defined.** Neither exists anywhere in this project. Both are the owner's
to write, and nobody else's. **Status: `UNKNOWN` (D166).** The two flags are specified in full and
are **not operable** until the script and the closing definition are supplied. → **D199.**
*If there is no written script — which "strictly not followed" makes a live possibility — then that
absence is the finding, and the first fix is a script, not a judge.*

### S131.7 — DECISIONS D191–D201 — FULL TEXT

- **D191 — The AI judge proposes; the doctor disposes. Two-phase gate.**
  **Phase 1:** no machine-initiated tile movement of any kind. A verdict places a card on the
  doctor's tab; **his click** sends the tile back to staff, and that click *is* the referee decision
  that fills `Doctor_Verdicts`. **Phase 2** unlocks machine auto-bounce for Groups A and B only, and
  only on: **100 refereed cards · ≥95% agreement on the bounce / no-bounce call · zero cases in the
  last 50 where the judge said the conversation was fine and the doctor disagreed.** The asymmetry is
  deliberate: **a false bounce costs one phone call; a false settle closes a case that never
  connected, and is invisible.** Groups C, D and `unclear` never auto-move. Parent **D149**
  ("calibration-first, no actions in v1") and **D190**.

- **D192 — A third axis: CONTACT.** The judge answers *"did a usable conversation happen, and with
  whom?"* separately from *"what was said."* Eighteen codes in five groups (§S131.6). **Group A is
  derived from call metadata and costs no AI at all** — a no-answer produces no recording, therefore
  no transcript, therefore the judge never sees it. Axis 2 is meaningful only under `spoke_patient`
  or `spoke_family_proxy`. Every code is decidable from **transcript + direction + duration** alone:
  the blind judge of D149 is preserved unchanged.

- **D193 — The doctor's dashboard becomes the sole writer of `Doctor_Verdicts`.** `verdict_review.py`
  retires its harvest and its sheet-based dropdowns. One writer per table, one ledger, one place the
  doctor works. The spreadsheet review card was a stopgap for a dashboard section that did not exist.
  Requires a new script property **`AUDIT_SHEET_ID`**; the dashboard will read three spreadsheets.
  Parent **D155**.

- **D194 — `Do_Not_Call` is the single enforcement point, because the dashboard structurally cannot
  act.** Established from the artefact: the Apps Script performs **zero writes** against
  `PATIENT_SHEET_ID`, and `Followups_Today` is **read-only** to it — that tab is rewritten every
  morning by `push_followups_today.py` on the clinic PC. A flag that lives anywhere else is
  overwritten before breakfast. **One new tab in the tracker, read by the morning generator before it
  writes.** It serves `number_invalid`, `patient_deceased`, and **`asked_not_to_call`** — a live
  outcome code that has never been enforced anywhere (**F-20**). **Only the doctor may set
  `patient_deceased`;** staff may file the outcome, his confirmation writes the row.

- **D195 — The tile-return contract.** Incoming-tile removal moves **off `Callbacks_Today.Staff
  Status` and onto the outcome**, mirroring `Followups_Settled`: the pending builder excludes numbers
  with a same-day `Incoming` row whose `settle` is `settle` or `escalate`; `retry` rows deliberately
  keep their tile; the client hides on save with an undo window (`fuPending`'s shape).
  **`Staff Status` is never written by the dashboard** — the removal is driven by *reading*
  `Followup_Outcomes`, so `Callbacks_Today` keeps exactly one writer. Cap: **3 attempts** on Groups A
  and B. `voicemail ×3` → doctor, not `exhausted`.

- **D196 — Incoming calls need a stable case identity.** `saveIncomingOutcome` keys everything
  `IN_<phone>_<yyyymmdd>` — a **day** key, not a **case** key. The send-back loop clears a tile by
  `lastOut[key] >= sentBackWhen`; cross midnight and the fresh outcome takes a *different key*, so a
  sent-back incoming tile **can never clear itself**. Adopt the judge's own identity —
  **`<phone>_<call_epoch>`**, a call id, stable forever. This sits directly on **D158's join defect**
  and would close it.

- **D197 — Conduct is scored per call against a checklist, never as a number about a person.** Six
  binary checks, split **objective** (transcript-verifiable, auto-recorded) and **interpretive** (tone
  — proposed only, entering the record solely on the doctor's confirmation). Per-flag applicability
  exclusions. Doctor-only visibility; a per-agent view exists and is opened for a reason, not
  displayed as a scoreboard. **Coaching is by recording, not by number.** Conduct calibration is
  **separate** from contact calibration and requires **40 calls the doctor has listened to himself**;
  until then the flags are collected silently. Not in the daily summary email — an email is a document
  that can be forwarded. Storage: proposals as columns in `Call_Verdicts` (owned by `call_verdict.py`);
  doctor confirmations in `Doctor_Verdicts` (owned by the dashboard, D193). **No new writer.**

- **D198 — The judge stays blind to agent identity, as a rule and not a convention.** D149 gives it
  transcript, direction and duration; the agent's name is attached *afterwards*, by the join. It
  therefore cannot hold a grudge against one member of staff or favour another. **This is a fairness
  guarantee, it is load-bearing, and it dies the moment somebody adds the agent name to the prompt
  "for context."** It is written down here so that nobody does.

- **D199 — `script_not_followed` and `no_closing` are specified and inoperable until the clinic's call
  script and closing definition exist.** Status **`UNKNOWN`** (D166), not "pending," not "to be
  inferred." The judge will check exactly what is written and nothing else. The absence of a written
  script is itself a finding, and its first fix is a script, not a judge.

- **D200 — Recording lag is not a blocker and will not be measured as a gate.** `recording_filename`
  arrives in the `call.end` webhook and is already written to `Call_Durations` in real time
  (`call_hook_capture.py` L183–186, L408). Recordings persist on MyOperator indefinitely; only the
  *link* expires (24 h). **A fetch-with-backoff makes the file-availability delay irrelevant to
  correctness.** The 02:00 / 03:00 batch clocks are a choice, not a constraint. The delay is worth
  *recording* for `Health.gs` lag budgets; it is not worth *waiting* for.

- **D201 — The record is a manifest and a disk. Check both before declaring an absence.** The S131
  opener asserted an export by md5 against a file the disk did not yet carry, while the assistant's
  own context manifest already named it. **The assertion (bytes + md5) held; the absence claim did
  not.** An assertion of presence is verified by hashing. **An assertion of absence is verified by
  exhausting every place the thing could be** — and the manifest is one of those places. Sibling of
  **D188** (a filename is not provenance) and **D186** (verification of a subset is not verification
  of the set).

### S131.8 — FINDINGS RAISED (none fixed — D180)

- **F-17 — the public repo's `WebApp.gs` is the pre-fix file wearing the live file's name.**
  `dashboard/WebApp.gs` is md5 `276dc197…` — the rollback point — and `function setDashboardKey(`
  and `function setStaffKey(` are **both still defined in it**. The deployed code sits beside it as
  `WebApp_v19_D189.gs` (`5173c3c7…`). Nothing is exploitable: repo code does not execute, and the
  live deployment (v64) has the setters deleted. **But anyone who opens `dashboard/WebApp.gs`
  believing the filename reads the vulnerable version — including the next assistant.** F-9's fix is
  not represented in the repo under the name that matters. Cheap correction at the next git session.
  *(Same folder, minor: `CallField.gs.gs` and `Probe.gs.gs` carry a doubled extension.)*

- **F-18 — `verdict_review.py` prints the overturned decision as a design justification.** The banked
  first run (`Verdict_Review_first_run_06Jul_S124.csv`, row 10) reads: *"Incoming calls, no claim —
  19 — Correct by design — staff do not log incoming…"* **That is D153, and D190 destroyed it.**
  Nineteen incoming calls were excused from scrutiny on a false premise. The review layer must stop
  excusing incoming calls before any of its counts can be trusted.

- ⛔ **F-19 IS WITHDRAWN (§S131.12).** *`call_hook_capture.py` L385 is not a defect: Call Console Spec v2.0 §G.1 records it as **D80, as built, Session 54** — "Skips incoming / non-OBD calls." Reclassified as a scope change against D80. The entry below is retained unaltered per D175, as the record of the error.*
- **F-19 — the webhook receiver throws away every incoming call at the door.**
  `call_hook_capture.py` **L385**: `if category != "obd" or not client_ref_id: return None`. The
  `call.end` payload — **including `recording_filename`** — is discarded for every incoming call and
  every outgoing call not dialled from the console. Block D's first line ("receiver stops discarding
  incoming calls") is a prerequisite for any live incoming verdict.

- **F-20 — `asked_not_to_call` is a live outcome code with no enforcement anywhere.** A patient who
  asks not to be called is re-listed by the next morning's generator. Same class as the deceased gap;
  both are closed by **D194**.

### S131.9 — RECORD DEFECTS (statements, not systems)

- **Runbook v65 §3 and the S131 opener both state the KB is 1,907 lines. The artefact is 1,906**
  (`\n`-count and `splitlines()` agree; **bytes 207,959 ✅, CR 0 ✅**, end-marker present). The file is
  the right file, whole and untruncated; only the statement about it was wrong. Every other stated
  count in the project reproduces exactly under `splitlines()` — `Dashboard.html` 2,738,
  `WebApp.gs` 1,652 / 1,647, `Health.gs` 401. **This one did not, and it slipped through in the very
  field D172 exists to protect.**

- **The KB's own end-marker was stale.** It read *"the CHANGELOG is the last section"* while §S130 sat
  after it. Corrected in v1.54 to describe reality. *A marker that misdescribes the file it guards
  cannot detect a truncation of it — D178, applied to the instrument.*

- **`Health.gs`: 19,040 bytes live, 19,041 in the repo.** Diffed: the sole difference is a trailing
  newline. Content identical, 401 lines both. **Not a finding — a footnote, recorded so that nobody
  later mistakes it for drift.**

- **`Source` is already taken.** `FU_OUTCOME_HEADERS` carries a `Source` column, used for
  *source-on-medication*. Any new provenance column (`staff` vs `machine`) **must not reuse the
  name** — that would be D178 in a single word.

### S131.10 — WHAT THIS SESSION DID NOT DO

Nothing was built. Nothing was fixed. **F-8 remains live; the incoming `Log outcome ▾` button is still
dead for every known patient.** The `Do_Not_Call` tab does not exist; a bereaved family can still be
called tomorrow. F-17 through F-20 are recorded and untouched (**D180**).

**The two artefacts the owner must supply before the build session can specify Axis 3 fully** are the
**call script** (Hindi, as staff are meant to speak it) and the **definition of a complete closing**
(two to four checkable things). Both are collected by the S131 decision workbook.

**The D34 question is raised exactly once, here, and it is the hardest question in the build:**
`saveIncomingOutcome` (L1233), the pending builder (L247), `getFollowups` (L925+), `sendBackToStaff`
(L1502) and `getEscalations` (L1373) **all live in `WebApp.gs`** — the file D34 says never to touch.
D189 established the pattern: **suspend D34 by name, for a bounded edit, resume on verification.**
This design cannot be built without doing that once more, and it is the owner's call, not the
assistant's.
### S131.11 — THE SESSION'S OWN LINEAGE ERROR, AND THE CONSOLIDATION IT FORCED

**Written after §S131.10, in the same session, because the owner asked one more question.**

Asked whether three callback-tracker documents needed consolidating, the assistant read them properly
and found that **Audit v1.2 had already established F-8's blast radius in Session 129** — in its own
title (*"dead for every patient in `Patient_Master`"*) and in its body (*"the breaking condition is
`e.patient` being truthy … not the `known` flag, so a patient row with only a UID also breaks"*).

**Runbook v66 §0.2 and Design Spec v1.0 §1.1 both called this "wider than the audit's headline."**
It was not. The session re-derived an existing finding from the artefact and mistook its own
re-derivation for an extension of it. **The fact is unchanged. The lineage was wrong.**

**D190 and D201 were both written in this session, and both were violated in it** — against the very
document that taught the lesson. *An artefact is read before it is characterised, and a document is an
artefact.* Corrected in Runbook **v67**, Design Spec **v1.1**, and the F-8 lineage note of Audit
**v1.3**. **No decision number is minted: this is a correction, not a new rule.** D190 already covers it.

#### What the consolidation found in the three documents

- **`Clinic_Callback_Tracker_AppsScript_Audit_v1_2.md` — stale in the way S129 itself named.** Its §0
  source table declared **`8bdb6d4dfdb0a331c5048b3c0fccf367` / 465,195 bytes** — the **pre-fix** export.
  Every finding in it rests on a snapshot of a project that no longer exists. It still marked **F-9 as
  🔴 open** (closed by D189, deployed v64, verified) and still recorded **D153 as `UNKNOWN`** (overturned
  by D190). *A reader who opened the audit before the KB would have been misled about which project it
  describes* — precisely §S129's "document set that misled its own reader."
  → **Re-based to v1.3.** `Dashboard.html` is **byte-identical across both exports** (`034529a1…`), so
  **F-8, F-10, F-11, F-13 and F-14 stand unre-derived.** Only `WebApp.gs` differs; F-9's reasoning is
  preserved as the record of *why*, its status set to **CLOSED**. F-8 re-priced with both options. §4's
  open questions **2** (repo public — yes) and **4** (D153 — F-8) answered. **F-2's sixteen
  `catch (e) {}` untouched and still unclassified — A-6 (D180).**
  *Credit where it is owed: the audit warned that F-8's evidence would "expire the moment F-8 is fixed."
  F-8 was never fixed, and D190 obtained the evidence another way, in time. **The warning was sound.***

- **`Frontend_Dashboard_Documentation_v1_S130.md` — current, correct, and needs nothing.** Verified, not
  assumed. Its provenance header already names the **post-fix** md5. Its §5 already states *"Filing an
  outcome does NOT remove it."* Its writer table already names **staff** — not code — as the writer of
  `Staff Status`. It already carries the `IN_<phone>_<day>` key and `sendBackToStaff`. **It is the
  healthiest document in the set.** Two additions are owed at v2, when the frontend actually changes:
  its **own open question #4** (*"is `Staff Status` typed by hand?"* — answered this session by
  exhaustive `setValue`/`setValues` search: **yes, nothing in the project writes it**), and the
  `SENT_BACK` → `getFollowups` **L938** re-surface into the *"Sent back by doctor"* section, which the
  doc does not carry.

- **`F9_Decision_Sheet_D189_Session130.md` — retired from project knowledge.** Its decision was made,
  executed as version 64, and verified against the artefact. **A decision sheet's job ends when its
  decision is executed;** keeping it in the working set costs a read at every session open and invites a
  closed question to be reopened. **Archived in the cold kit** — from which the first kit built this
  session had omitted it, a gap in the close-out itself.

#### The rule this leaves behind, already written

**D188** (a filename is not provenance) and **D201** (presence is verified by hashing, absence by
exhaustion) were both aimed at *code exports*. **They apply to the document set with equal force.**
Every canonical document that names an artefact must carry that artefact's md5 — and when the artefact
moves, the document is re-based or it lies.

### S131.12 — THE RECOVERY, AND THE HOLE IT EXPOSED IN THIS DOCUMENT

**Written after §S131.11, in the same session, because the owner asked whether three incident files
and a fault register needed consolidating.** They did. Answering the question properly required
reading the two "canonical" specs, and reading them properly exposed something larger than either.

#### The stumps

`START_HERE_PROMPT_v3.md` names seven canonical documents. **Two of them were fragments.**

- **`Call_Console_Evolution_Spec_v1_6.md`** — 8,025 bytes, containing **§J and §K and nothing else**.
  Its header claimed *"Carries forward v1.5 unchanged."* v1.5 was not in project knowledge. Its very
  first sentence reads *"The gate (§G, D77/D82) is a synchronous blocker…"* — pointing the reader at
  a section that existed nowhere anybody could reach.
- **`Diagnostics_Surveillance_System_Spec_v1_7.md`** — began at `§NEW-D`. Same shape.

Both broke the **S100 policy** stated in this document's own header — *"single file, no delta chain"* —
a policy applied to the KB in Session 100 and never applied to the specs, which went on stacking
deltas for thirty sessions while the KB was kept honest.

#### The recovery

Git holds **v1.1 and v1.6 only**; across sixty-two commits and every branch, **v1.2, v1.3, v1.4 and
v1.5 were never committed at all.** Drive held v1.5 and nothing else. Every one of them was then
recovered, intact, from the owner's cold-backup zips:

| File | Recovered from | md5 |
|---|---|---|
| Call Console v1.2 (§A §B §C) | `DrManoj_Clinic_FULL_Handoff_Session51_2026-07-03.zip` | `3bb27fe1…` |
| Call Console v1.3 (§D §E §F) | `DrManoj_Clinic_ColdKit_Session53_2026-07-03.zip` | `4c063486…` |
| Call Console v1.4 (§G) | `S54-55_cold_kit.zip` | `bae684ed…` |
| Call Console v1.5 (§H §I) | `Session57_ColdBackup_Docs.zip` + `COLD_KIT_Session67` + Drive | `9ef6ac27…` |
| Diagnostics v1.2 · v1.3 · v1.4 | Session-53 · Session-61 · Session-62 kits | `e7da5ddf…` `9748ca2d…` `9b2693ee…` |

**Three independent copies of Call Console v1.5 — two zips and Drive — agree byte-for-byte.**

**Nothing was lost. The cold-backup discipline, run after every session for four months, is the only
reason.** It has now been tested, and it held.

#### F-22 — this document has never carried D1–D120

The decisions index of **every KB that has ever existed** was checked: `v1.31`, `v1.43`, `v1.48`,
`v1.53`, `v1.55`.

| | |
|---|---|
| Index range, every version | **D121 → D188.** Ninety-eight entries. |
| Absent from the index | **D1 – D120**, plus D161 |
| **D68 · D78 · D80 · D81** | **zero mentions in 246 KB of canonical text.** Not indexed, not referenced, not defined. |
| **D77 · D82** | appear **only** inside D156's phrase *"amends D77/D82"* |
| **D62** | 9 mentions, **0 definitions** |

**This document amends decisions it does not contain.** For thirty sessions it has been the
authority that *wins on any conflict*, about decisions whose text it has never held. They existed
only in the spec chain — and four fifths of that chain existed only in a zip folder on a Windows PC.

#### What the hole cost, measured

**Four things designed in Session 131 had been designed already, in Sessions 25 to 54, and were
re-derived because the documents holding them could not be read.**

1. **D200** (recording lag is not a blocker; per-call download; fetch-with-backoff) — written in
   Call Console **v1.1 §12, Session 25**: *"migrate Stage 1 recording archiver from nightly batch to
   per-call download … requiring a MyOperator processing-lag/retry check and a webhook trigger."*
2. **Axis 1 CONTACT — the AI judge's whole purpose** — scoped in v1.3 §E and v1.4 §G.5, **D62/D77**:
   *"Determined dead-air lies … are out of scope for the gate — caught post-hoc by the AI-verdict
   layer (D62)."*
3. **The three-attempt cap** in D195 — **D78**, v1.3 §F, Session 53: *"sticky-on-staff 3-strike …
   the miss count accumulates across days."* Designed, *"build after the gate,"* never built.
   **And it disagrees with D195:** D78 sends the third strike to a WABA template and a snooze; D195
   sends it to the doctor. **Neither is built. They must be reconciled before either is.**
4. **`wrong_number` → doctor escalation**, also in D195 — **D68**, v1.2 §A, Session 51, verbatim:
   *"'Wrong number' and 'Asked not to call' are connected-call outcomes … routed to the doctor as
   escalations."*

#### F-19 is WITHDRAWN

`call_hook_capture.py` **L385** — `if category != "obd" or not client_ref_id: return None` — was
recorded in §S131.8 as a finding: *"the webhook receiver throws away every incoming call at the
door."* **It is not a defect.** Call Console v1.4 **§G.1**, describing the receiver **as built** in
Session 54 under **D80**, states it plainly:

> *"**Skips incoming / non-OBD calls.**"*

Deliberate. Documented. **F-19 is withdrawn as a finding and reclassified as a scope change against
D80** — the boundary D80 drew must now move, because the AI review layer needs incoming recordings.
That is a decision to take, not a bug to fix.

**This was the third lineage error of Session 131** — after F-8's blast radius (§S131.11) and D200's
provenance — and all three have one cause: **a decision was characterised without reading the
document that made it, because that document had been reduced to a fragment that could not be read.**

**F-20 survives.** D68 routes `asked_not_to_call` to a doctor *escalation*. Nothing has ever
*suppressed* the number from the next morning's regenerated list. **Escalation is not suppression**,
and `Do_Not_Call` (D194) is exactly the suppression D68 implied and nobody built.

#### F-21 — a backlog item that never lived

The Session-25 item above reached **no backlog**. It was written into a spec's changelog, the spec
became a stump, and 106 sessions later it was re-derived from the webhook payload and presented as
a finding. **It is in neither the KB nor any runbook.**

#### F-23 — a delta that abridged what it swore it carried

`Diagnostics_Surveillance_System_Spec_v1_7.md` declares *"Carries forward v1.6 unchanged."* **It does
not.** Its `§NEW-D`, `§NEW-F` and `§NEW-G` are compressions of v1.6's text, and **sixteen lines were
dropped** — including, from the verification standard, its entire evidential basis:

> *"Session 94 recorded the 403 outage as 'Verified end-to-end. Outage closed.' on the strength of one
> call placed immediately after the fix. **The fix was dead seven minutes later; the panel had
> reverted.**"*

v1.7 kept the rule and deleted the reason. **A rule without its reason is the first thing a future
session argues away.** v1.6's full originals are restored in Diagnostics Spec **v2.0** as §M2/§M3/§M4.

> **This is the case against delta chains, made by the chain itself.** A delta that claims verbatim
> carry-forward and abridges is undetectable without both files — and one of those files was nowhere
> in project knowledge.

#### The consolidation performed (Session 131)

| Document | Was | Now | Loss check |
|---|---|---|---|
| Call Console Evolution Spec | v1.1 … v1.6, six files, four missing | **v2.0** — single, self-contained | **0 lines lost** |
| Diagnostics & Surveillance Spec | v1.1 … v1.7, seven files, three missing | **v2.0** — single, self-contained | **0 lines lost** |
| CALLHOOK 403 incident | v1 (`_SUPERSEDED`) + v2 + v3 + v4 | **v5** — single, self-contained | **0 lines lost** |

Every consolidation transplanted section **bodies verbatim** and asserted, programmatically, that
every content line of every source section survives in the output. Three deliberate removals, each
named in the file that made them: the delta-chain scaffolding (*"append this to that"*), v1.7's
abridgements (superseded by v1.6's originals), and the incident's **false status line** — v4 read
*"MITIGATED, rotation in progress"* while the rotation had been **PARKED since Session 128**.

Diagnostics v1.2, v1.3 and v1.4 each named their single section **`§NEW`** — three unrelated check
families under one label. Renamed **§L1, §L2, §L3**; every original heading string preserved in a
provenance line beneath its new heading (**D178**).

### S131.13 — DECISIONS RECOVERED FROM THE SPEC CHAIN (D62–D98)

**These eleven decisions govern live, shipped behaviour and have never appeared in this document.**
They are recorded here by their source, verbatim in substance, so that the index is no longer a lie.
**Their full text lives in `Call_Console_Evolution_Spec_v2_0.md`**, which is now their canonical home.

- **D62** — *Determined dead-air lies (a line held open with no real conversation) are out of scope
  for any duration gate. They are caught post-hoc by the AI-verdict layer.* → the founding scope of
  the AI review layer. *(v2.0 §E, §G.5)*
- **D66** — *Vanish-on-file: on save of a completing or escalating outcome the tile is removed
  immediately, the write is held ten seconds, and a bottom UNDO toast counts down. If the page closes
  inside the window the write never fires and the patient re-surfaces — the safe failure, never a
  fake "done."* *(v2.0 §D, built v18.15)*
- **D68** — *Missed-call binding. 1–2 no-answers inside 60 minutes snooze the tile; the 3rd removes
  it from the staff list. **"Wrong number" and "Asked not to call" are connected-call outcomes,
  routed to the doctor as escalations** — they cannot be known until a call connects, so they are
  never actions on a missed tile.* *(v2.0 §A, built v18.4)*
- **D69** — *The doctor's Escalations card is a live read, not a filing snapshot: identity, diagnosis
  and last-visit fill from the current patient record; the matched call attaches time, duration,
  recording (MyOperator same-day → Drive archive later) and transcript; every card carries an explicit
  call-status line.* *(v2.0 §B, built v18.5→v18.8)*
- **D77** — *The duration gate, design. Outcome availability is driven by the call's real measured
  duration from the `call.end` webhook, not by a self-declared "Talked" tap. Exact-call binding via
  `reference_id`, never fuzzy number+time matching.* *(v2.0 §E; superseded as built by D82; amended
  by D156)*
- **D78** — *Sticky-on-staff 3-strike. A patient at three misses does not leave the staff worklist;
  it drops to a distinct bottom band with cross-day context, and the miss count accumulates across
  days. The third strike fires the WABA template and snoozes X days.* **DESIGNED, NEVER BUILT.
  Conflicts with D195 — reconcile before building either.** *(v2.0 §F)*
- **D80** — *The `call-hook` receiver: a walled-off VPS service, secret-gated, upserting one row per
  call into the one-writer `Call_Durations` tab keyed on `client_ref_id`. **Skips incoming / non-OBD
  calls.** No phone number is written.* → **the boundary that F-19 mistook for a defect.** *(v2.0 §G.1)*
- **D81** — *Corrected field mechanics from real captured bodies: the join key is
  `payload.client_ref_id` (the webhook's `ref_id` is MyOperator's own UUID, not ours); the gate signal
  is the **customer leg's** `talk_duration` and `result`, never the top-level `duration`, which
  includes agent pickup and ring time.* *(v2.0 §G.2)*
- **D82** — *The duration gate, as built. `allowOutcome = (status=="bridged") AND
  (customer_result=="answered") AND (customer_talk_duration >= CC_GATE_MIN_TALK)`, `CC_GATE_MIN_TALK
  = 15`s, which doubles as the opening-line script-adherence check. Any ambiguity or missing field →
  `allowOutcome:false` (fail-safe). Manual fallbacks preserved throughout.* *(v2.0 §G; amended by
  D156 — the gate now fails **open** when it cannot measure)*
- **D97** — *WhatsApp tap-to-call, on inbound rows only, through the same dialer and the same gate.
  **Corollary, standing: never use native `confirm`/`alert`/`prompt` in the dashboard — always an
  in-page dialog.** The Apps Script sandbox force-prepends "An embedded page at …googleusercontent.com
  says" to every native dialog, and no page can remove it.* *(v2.0 §H, built v18.17b)*
- **D98** — *The stale-list top-bar guard: a live on-screen twin of the 2 PM email sentinel, sharing
  `Diagnostics.gs::checkFollowupListFresh`'s exact rule so the bar and the email can never disagree.
  Read-only, no PHI, fail-safe (any error reports not-stale and never blocks the board).*
  *(v2.0 §I, built v18.18)*

> **D1–D61, D63–D65, D67, D70–D76, D79, D83–D96, D99–D120 remain unrecovered.** Their text is in the
> handoff runbooks of Sessions 1–62, which sit in the same cold-backup folder. **That is a trawl for
> another session, and it is worth doing.**

### S131.14 — DECISION D202

- **D202 — A decision lives in the KB decisions index, or it does not live.** A decision recorded only
  in a spec, a changelog, an incident report or a chat transcript is not part of the record: it cannot
  be found by the next reader, and it will be re-derived — expensively, and sometimes wrongly. **The
  same rule holds for the backlog: an item recorded in a document's changelog is not a backlog item
  (F-21).** This is *one writer per table*, the invariant already enforced on every sheet in this
  system, applied at last to the record itself.
  **Corollary:** every canonical document that names an artefact carries that artefact's md5, and when
  the artefact moves the document is re-based — or it lies (§S131.11, D188, D201).
  **Corollary:** no canonical document may be a delta. A delta that claims verbatim carry-forward and
  abridges is undetectable without both files (**F-23**), and the file you need will be the one nobody
  kept.
### S131.15 — THE FAULT REGISTER KEPT, NOT RETIRED — AND THE FOURTH LINEAGE ERROR, CAUGHT IN TIME

The owner asked for the two remaining loose threads closed: the **Fault → Action Register**, and the
**historical document set**.

#### The recommendation that was wrong

§S131.12 recommended folding the Register into the Diagnostics Spec and retiring it — *"two writers,
one table."* **That recommendation was wrong, and it was wrong in the way this whole session has been
wrong.**

Diagnostics Spec v2.0 **§M1**, locked in Session 63, says:

> **The single brain = `Fault_Action_Register_v1_Session63.md` (D114)** — every fault mapped to lane +
> exact procedure. Reference it in every maintenance/incident session.

**D114 designates the Register as the authority.** Retiring it would have overturned a decision the
assistant had not read — because **D112, D113, D114 and D115 all sit in the D1–D120 hole (F-22)**, and
§M1 is the only place any of them is defined.

**This would have been the fourth lineage error of Session 131.** It was caught only because the
document being retired was read before it was retired. *The lesson has now been learned four times in
one day, and it is the same lesson each time.*

#### The two documents are not duplicates

| | Answers |
|---|---|
| `Diagnostics_Surveillance_System_Spec` | *"How do we detect it?"* — check families, models, detection architecture |
| `Fault_Action_Register` | *"What happens when it fires?"* — lane, system action, exact human procedure |

They overlap on the fault-code **list** and nowhere else. The Register's actual job — code → lane →
procedure — exists in no other document. → **D203** states the boundary.

#### F-24 — the register describes a responder that does not exist

Nine faults in the Register's §2.1 are marked **AUTO→ESC**, with *"System does: `systemctl restart
call-api`; re-check; alert."*

The live watchman, in Diagnostics **§L2**'s own words:

> *"**Read-only** — reports only; **never starts/stops/changes a service.**"*

It **names** the restart command inside an alert. **It has never run one.** And §M1's **D113** —
*"The S61 watchman **IS** the Lane-1 service responder"* — states a design intent as a fact, while §4
of the Register lists that responder as **Deliverable 2, unbuilt.**

**Not one row of that register is live-and-acting.** Everything that works is detect-and-alert.

> **This is not academic. During an outage, a session reading §2.1 would wait for a restart that never
> comes**, and would not read the journal, because the document told it the system had already
> restarted the service.

**D113 must be re-stated as intent or scheduled as a build.** It cannot stand as a statement of fact.

#### F-25 — six fault codes detected since Session 125, never laned

The `CALLHOOK_*` family — `CALLHOOK_SECRET_MISMATCH_403`, `CALLHOOK_MULTIPLE_KEYS`,
`CALLHOOK_403_EARLIER_TODAY`, `CALLHOOK_NO_ACCEPTED_TODAY`, `CALLHOOK_SILENT`,
`CALLHOOK_RAWLOG_MISSING` — has been **detecting for six sessions with no lane and no procedure.**
An alert that names a fault code which maps to nothing violates the Register's own **rule 4**:
*"Every alert names its procedure."* All six are laned in Register **v2.0 §2.5**, every one
**ESCALATE-ONLY or ASSISTED** — a key, a panel, or a vendor sits behind each, and §3's rule 3 forbids
the responder from touching any of the three.

*(Related, and deliberately not "fixed": Diagnostics §L2 registers `VPS_SERVICE_DOWN` /
`WATCHDOG_SELF_FAIL`; the Register lanes nine per-service codes. **Both are correct** — the detector
emits one code with the service name attached; the Register lanes the response per service. Recorded
so that nobody harmonises one into the other and destroys the distinction.)*

#### Two of Session 63's three open questions were answered by what shipped, and nobody told the document

| | Question | Answer |
|---|---|---|
| Q1 | Daily report timing? | **09:00 IST** — `Health.gs`. *(v1 suggested ~8 AM.)* |
| Q2 | Channel? | **Both** — ntfy one-liner + Gmail detail (`clinic_health_report.py`, D115). |
| Q3 | Log-prune policy? | **STILL OPEN.** It decides whether `LOG_ROTATION_OVERDUE` can ever be promoted to Lane 1. |

#### The consolidation performed

`Fault_Action_Register_v2_0.md` — self-contained; §1, §2.1–§2.4, §3, §4 and §5 reproduced **verbatim**,
loss-checked line by line, **zero lines lost**. What changed is only what was false: the twenty-five-
version-dead source-of-truth line; the front page that declared *"nothing here is built"* over a body
marking three detectors LIVE; and the absent status column. **No rule, lane or procedure was altered.**

### S131.16 — DECISIONS RECOVERED FROM DIAGNOSTICS §M1 (D112–D115)

**Four more decisions this document has never held.** Their only definition is Diagnostics Spec v2.0
§M1. With §S131.13's eleven, **fifteen of the missing D1–D120 are now recorded here.**

- **D112 — Two lanes.** **LANE 1 — NARROW-AUTO:** the system runs a proven-safe, idempotent fix
  itself, re-checks, and reports. Started deliberately tiny — only *restart a dead always-on service*
  and *re-run the follow-up push.* **Nothing else is Lane 1 until deliberately promoted, and promotion
  is a logged decision.** **LANE 2 — ASSISTED (Option 2a):** for everything else the background program
  only *detects and escalates*; the stepwise fixer is Claude in a confirmation-gated session, scripted
  by the Register. **No consequential action runs without an explicit confirmation.** **AUTO→ESC:** the
  Lane-1 fix is tried once; if the service does not recover it escalates with the manual procedure.
  **ESCALATE-ONLY:** never auto-acted — token rotation, disk-full, backup-missing, anything destructive,
  anything touching PHI or the MyOperator panel.
- **D113 — The S61 watchman is the Lane-1 service responder; no second restarter is built.**
  ⚠️ **STATED AS FACT, TRUE ONLY AS INTENT (F-24).** The watchman that exists is **read-only** and
  never restarts anything. Re-state or schedule.
- **D114 — The Fault → Action Register is the single brain.** Every fault mapped to lane + exact
  procedure; referenced in every maintenance and incident session. **This is why the Register was kept
  in Session 131 rather than folded away.**
- **D115 — The daily health report (Category 3 — positive confirmation).**
  `clinic_health_report.py`, read-only, takes no action: nine services, three timer heartbeats, disk
  usage, and the watchman's last 24 h, in **one digest — ntfy one-liner + Gmail detail**, ✅ ALL GREEN
  or ⚠️ ATTENTION NEEDED. **Health is positively confirmed each morning rather than assumed from
  silence.** Its **absence** is the fault.

### S131.17 — DECISION D203, AND THE HISTORICAL ARCHIVE

- **D203 — Detection and response are separate documents with a stated boundary.**
  **`Diagnostics_Surveillance_System_Spec` defines a fault code and how it is detected. The
  `Fault_Action_Register` assigns that code a lane and a procedure. A code is defined once and laned
  once; neither document restates the other.** This preserves **D114** while ending the "two writers,
  one table" appearance that nearly caused the Register to be retired unread. **Corollary:** a fault
  code that is detected but never laned is a broken alert — it violates the Register's own rule 4,
  *"every alert names its procedure"* (**F-25**).

#### The historical archive

Seven documents were carried in project knowledge, read at every session open, and superseded by the
KB. **They are archived to the cold kit and the repo, and removed from the working set.** None is
wrong; all are finished.

| Document | Why it leaves |
|---|---|
| `FINAL_Execution_Plan_v3_OperatingModel_Session50.md` | Subtitled *"THE single reference for the coding sessions ahead."* **Eighty-one sessions behind.** |
| `Call_Pipeline_Audit_Evidence_and_Future_Plan_02Jul2026.md` | Sessions 37–45. Folded into the KB. |
| `Followup_Taxonomy_and_Lifecycle_Design_v1_Session56.md` | Session 56. The vocabulary it designed is now in the live code and in `Call_Console_Evolution_Spec_v2_0`. |
| `INCIDENT_2026-07-01_FOLLOWUPS_WATCHER_NOT_RUNNING.md` | Session 24. Closed and recovered the same morning. |
| `Google_Workspace_Inventory_v1_0_30Jun2026.md` · `Voice_Bot_Pipeline_Plan_v1_1.md` | 30 June. Forward-looking; neither is a current gap. |
| `Orthopedic_Clinic_Rehab_Nutrition_v11.xlsm` · `Ayushman_Ortho_Finder.html` · the four MyOperator template files · `Surgical_Estimate_System` · `Orthopedic_Diagnosis_Taxonomy_Master` · `GoDaddy_Short_URL_Master` · two `.docx` | Not documents of this system. Superseded by `clinic_writer` and `rehab_nutrition_plan_v26.html`, or simply unrelated. |

**Kept, deliberately:** `4.json` (the artefact), `Verdict_Review_first_run_06Jul_S124.csv` (the **only**
evidence behind the calibration argument), `API_QUICK_REFERENCE_CARD`, `MyOperator_Call_API_Master_Reference`
(which held the answer to D200 when nothing else did), `Maintenance_SOP_System_Spec` (forward-looking,
and the Register's `WA_TOKEN_AGING` procedure points at an SOP inside it that **has never been
written** — recorded, not fixed), `Frontend_Dashboard_Documentation`, and `END_OF_SESSION_PROMPT_v3`.

> **Nothing archived is deleted.** Every file is in the Session-131 cold kit under `historical/`, and
> in the repo. **Seven of the thirteen spec files recovered earlier today existed nowhere but a zip on
> a Windows desktop.** That is not a mistake this project will make twice.




## §S132 — F-8 KILLED; MyOperator CLEARED; and four absences asserted from unread artefacts

**Session type: FULL EOS — one live file changed.** `Dashboard.html` → **v18.20**, deployed as a new
version of the existing deployment (`/exec` unchanged). No server `.gs` file. No D34 waiver spent.
No VPS service edited. Three read-only diagnostic scripts were added to `/root/wa`.

### S132.0 — The record was verified, and the mirror was not the project

Phase 0 hashed all ten canonical artefacts against the opener's table. **Nine matched exactly.** The
Runbook was absent from the assistant's file mirror and was uploaded. Then the Umbrella disappeared
from the mirror entirely, while the **project-knowledge search index returned its contents on demand.**

**The assistant's file mirror is a snapshot taken at conversation start; the search index is live.** An
absence asserted from the mirror is an absence asserted from a stale disk. **D201 already says this —
"an assertion of absence is verified by exhausting every place the thing could be" — and the mirror is
one place, not every place.** The Umbrella was verified instead against the repo copy
(`b1c6c414…`, byte-identical to the table). *Recorded so that no future session mistakes a mirror lag
for a lost file.*

Repo `dashboard/WebApp.gs` re-hashed: **`276dc197…`**, both setters present. **F-17 confirmed open.**

### S132.1 — A-000 answered. D204.

The owner delegated the technical call and it was answered **(a) — re-state D113 as intent.**
Fault Register **v2.0 had already defused most of F-24** at the top of §2 (the 🟡 banner and §0.4's
status table). What remained is that **D113 is still stated as fact in Diagnostics §M1 — its only
definition.** Corrected in Diagnostics **v2.1**; the Register's "System does" column re-labelled per
**D178** in **v2.1**. **Lane 1 remains empty. Deliverable 2 is not scheduled** (D112: promotion is a
logged decision, and no fault has earned one).

### S132.2 — F-8 IS DEAD

Built from the verified export (`Dashboard.html` md5 `034529a1…`), eight anchored edits, every anchor
asserted unique, **seventeen lines changed and nothing else.**

- `IN_PAT` — a page-level map keyed by slot id, rebuilt on every render.
- **L912** stashes the packet in the map instead of stringifying it into markup.
- **L923** the button now carries `(slotId, digits, boolean)` and **nothing else**.
- **L1260** the dead `JSON.parse` and its `catch(e){}` — *the catch that would have reported F-8 is the
  catch that hid it* — **deleted.** `pat` was parsed there and never used.
- **L1262** `slot.dataset.pat` — **deleted.** No packet reaches the DOM.
- **L1364** `inSave` reads `IN_PAT[slotId]`. **The second `JSON.parse` catch dies with it.**

`catch(e){}` in `Dashboard.html`: **16 → 14.** L1128 (`openThread`) survives — **that is A-3's whole
remainder now.**

**Proved before deploy, not asserted.** The live escapers were re-implemented in node against a patient
named `Ram D'Souza`. The old attribute closes at the first `"` and the browser receives
`inOpen('in_9812345678_0','9812345678',true,'{` — **which does not compile**, exactly as Audit v1.2
predicted in S129. The new one compiles. `node --check` clean on the embedded script.

**Verified live, on two tiles.** `8218401104` (Neeta Agarwal, ID ZROVL43590) and `9411222492` both
opened straight to **Reason → Resolution**, skipping *"Who is this?"*. **That skip is the proof:** it
only happens when `known === true` reaches `inOpen` — the code path that had never once executed. A
third tile (`1409801539`, *"Not in patient list"*) opened the identify-caller card, confirming the
unknown path is undisturbed. Nothing was saved. **D190's two `non_patient` rows are undisturbed.**

**Closed by this fix:** F-8 · F-14's two JSON catches · Block E's *"stop embedding patient data in
button markup"* · the first of F-10's twenty-four fragile sites — **structurally, by removing the data,
not by improving the escaper.**

**Still true, and expected:** the tile does not clear. **Nothing in this project has ever written
`Callbacks_Today.Staff Status`.** That is D195, and it waits on A-1.

### S132.3 — MyOperator: cleared, with a defensible timeline

Ticket 653584 had run five days on a request for *"a screenshot of the error"* — of a server-to-server
API call, which has no screen.

Three probes were built (all read-only or dry-run-by-default, all token-guarded: the token is read from
`.env`, used, and never printed; each output is scanned for the token and destroyed if found):
`waba_probe.sh` · `waba_template_test.py` · `waba_recovery_window.sh`.

| Fact | Evidence |
|---|---|
| `GET /chat/templates` → **200** | 10 Jul 18:46 IST. 14 templates returned |
| `POST /chat/messages` → **200 Accepted** | 10 Jul 19:04 IST. `message_id c9130529-…` |
| Template **delivered to the handset** | 19:06 IST, rendered correctly with both buttons |
| Outage began | 05 Jul 01:19 IST — `AuthorizerConfigurationException`, request id `eb82db53…` |
| Next attempt after the failure | **09 Jul 16:53:05** — `sent=True http=200` |
| `wa-send-api.service` `ActiveEnterTimestamp` | **26 Jun 20:56 IST — unrestarted throughout** |

**Nothing on the clinic's side changed. It cannot have.** The journal holds 9,115 lines from 05 Jul
alone, so the silence between 05 and 09 Jul is an **absence verified by exhaustion**, not lost evidence:
**no send was attempted.** The relay logs failures as loudly as successes (`_log()` is unconditional).

`wa_approve.py` started **05 Jul 01:05:10**. The owner emailed support **fourteen minutes later.** He was
approving follow-up templates when they began failing. **`waba.py` is the tracker's send arm and it does
call the public API** — so the outage did reach the patient-facing path, and the ticket's impact claim
stands. **D120 is, on today's evidence, not a live fault.** A fault that heals without explanation
returns without warning: the recovery window is the question to put to the vendor.

### S132.4 — The tracker reconciled against the repo, file by file

`C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker` vs `followup-tracker/` in the repo.

- **38 of 40 code files byte-identical.** **0 files in the repo that are not on the PC.**
- Differ: `patient_mirror_log.txt` (a log) and `python test_send.py` (a stray file whose name contains a
  space). Neither is code that runs.
- **`push_followups_today.py` is identical across three sources** — PC manifest, owner's upload, and repo:
  **16,600 bytes · 428 lines · md5 `fc0a731d38482eb90b7d2def135c92b6`.** `Do_Not_Call` may be built on it.

**The repo is an honest mirror of the tracker.** It is *not* an honest mirror of `dashboard/` (F-17) or
`wa-send/` (F-27).

### S132.5 — FINDINGS

- **F-27 — the repo's `wa-send/wa_send_api.py` is not the deployed file.** The live journal prints
  `send <n> open=… sent=… logged=True http=200`. **`logged=` appears nowhere in the repo file**
  (`19253232…`). A later version runs and was never committed. **Same class as F-17**, different folder.

- **F-29 — Runbook v69 §3 was never re-based when v67–v69 folded in.** It names *"KB v1.54 · 239,175
  bytes / 2,311 lines"* (artefact: v1.57, 277,634 / 2,727), *"Runbook → this file, **v66**"*,
  *"Umbrella → **v1_41**"*, and *"Next free: **D202**"* (D202 and D203 were both minted). §0 and §2 were
  correct. **Only the section whose job is to say where we stopped was wrong** — D172's own field.

- **F-30 — `watch_and_push_followups.py` exists on one Windows desktop and nowhere else.** 8,439 bytes.
  It is the auto-push watcher under Task Scheduler, and it has a live incident to its name
  (`INCIDENT_2026-07-01_FOLLOWUPS_WATCHER_NOT_RUNNING`). Uncommitted, with
  `start_followup_watcher.bat` and `SETUP_followup_watcher_autostart.txt`. **The script that pushes the
  morning worklist is backed up nowhere but that disk.** Precisely the shape of the S131 spec recovery.

- **F-31 — `.gitignore` cannot untrack what git already tracks.** `attendance/att_config.py` is in the
  **public** repo. The repo's own `.gitignore` names it twice: *"holds the attendance dashboard password
  + SECRET_KEY — NEVER commit."* Git ignores that rule for tracked files.
  **Nothing is exposed today** — established by comparing credential *values* by hash, never printing one:

  | | live (VPS) | public repo |
  |---|---|---|
  | `DASHBOARD_PASSWORD` | 12 chars, `db8972d2…` | 20 chars, `1f502ef8…` — **the shipped placeholder, `# <-- CHANGE THIS`** |
  | `SMTP_PASS` | 16 chars (real) | **empty** |
  | `SECRET_KEY` | 64 chars | **absent** |

  **The danger is prospective.** The day anyone copies the live file into that folder, `git add` will
  take it **without complaint**. The warning is written and it will not fire. Cure:
  `git rm --cached attendance/att_config.py`, commit, rename the template `att_config.example.py`.
  **The rest of the rule held:** no `.env`, no `*.csv`, no service-account key anywhere in 326 repo
  entries — verified against the published tarball, not against the rule that claims to protect it.

- ⛔ **F-26 WITHDRAWN.** *"`wa_send_api.py` logs no send outcome."* It logs every outcome. The claim came
  from a `grep` for `" 200` and `status.*200` against a file that writes `http=200`. **A check
  miscalibrated to its artefact reports the artefact's absence (D177).**
- ⛔ **F-28 WITHDRAWN.** *"The template send path is unlogged."* `wa_approve.py` writes a CSV
  (`Timestamp, Mode, Kind, Key, Name, Mobile, Template…`) and its stdout and stderr both go to
  `/root/wa/wa_approve.out`. Asserted from a `grep` for the wrong words.

*(Both entries are retained above per D175, as the record of the error.)*

### S132.6 — THE SESSION'S OWN FAILURE MODE, COUNTED

**Four assertions were made from artefacts that had not been read, and all four were wrong:**

1. **F-26** — the relay's log format, guessed instead of read.
2. **F-28** — the approval path's logging, guessed instead of read.
3. **`/root/wa/wa-send/wa_send.py`** — a **repo folder name** used as a **disk path**. It does not exist.
4. **F-31, first draft** — the *tracker folder's* two-line `.gitignore` was read, and a conclusion drawn
   about the *repo's* eighty-two-line one. Two folders. Two files. One characterised as the other.

**S131 recorded three lineage errors and wrote D190, D201 and D202 about them. S132 committed four more
of the same species, in a session that opened by reciting the rule.** The rule is not the defect. **The
defect is that a grep, a path, and a filename all feel like evidence and none of them is.**

> **An artefact is read before it is characterised. A mirror is not the project. A repo path is not a
> disk path. A `grep` that cannot match is not a search.** No new decision is minted: **D190 and D201
> already cover every one of these.** They were violated, not absent.

### S132.7 — DECISION D204 — FULL TEXT

- **D204 — D113 is an intent, not a fact. No auto-responder exists, and none is scheduled.**
  The S61 watchman **detects and alerts**. It prints `systemctl restart <svc>` inside the alert text and
  **has never executed one.** D113's *"the S61 watchman **IS** the Lane-1 service responder"* describes
  **Deliverable 2, which is unbuilt.** Every `AUTO→ESC` row in the Fault Register means, today: *you are
  told; a human restarts.* **Lane 1 stays empty.** Per **D112**, promotion into Lane 1 is a logged
  decision and **no fault has earned one** — no service in this clinic has been observed dying
  unattended. Deliverable 2 will be scheduled the day a journal shows one that does.
  **During an outage, do not wait for a restart.** Parents: **D112, D113, D114.** Raised as **F-24**.

### S132.8 — WHAT THIS SESSION DID NOT DO

`Do_Not_Call` was not built, though its input file is now verified. **A bereaved family can still be
called tomorrow.** F-18 untouched. A-3's remainder (L1128) untouched. A-5 untouched. F-2's sixteen
server catches untouched and still unclassified (**A-6**). The rotation stayed parked and was not raised.

**A-00, A-0 and A-1 remain unanswered, and every server-side item is behind A-1.**



## §S133 — D194 LIVE; REPO HONEST; THE LAST NOHUP DIES; TWO TRIGGER FINDINGS

**Session type: FULL EOS.** One PC file changed (`push_followups_today.py`). One VPS service installed
(`wa-approve.service`). One repo commit (`84831b0`, 11 files), pushed and hash-verified from GitHub.
No `.gs` file, no `Dashboard.html`, no D34 waiver. Owner directive at open: **do the callback-tracker
backlog in minimum steps; park everything linked to the AI worksheet/verdict layer** — A-00, A-0 and
A-1 were therefore not raised, and **F-18 is parked with the layer** (nothing consumes its report while
the layer sleeps).

### S133.0 — Phase 0/1: nine hashes matched; the fresh export closed the stale-4.json item
All nine canonical documents matched the S133 opener's table exactly; CR 0; stale versions absent;
end-markers present. Mid-session the owner replaced `4.json` in project knowledge: the new export is
`Clinic_Callback_Tracker__4_.json`, **overall md5 `523ddcbecc34cfe2c9a7ed6c7b3179ed`, 15 files**, with
`WebApp` = **`5173c3c7a9d58e091fa8a49ee97522c9`** (the deployed hash, Runbook v70 §3) and `Dashboard` =
**`a442bab52eab7898d1b2e692403f987b`, 157,703 b** (the deployed v18.20). Every dashboard file in the
repo was byte-compared against this export: **14 of 15 identical**, `Health.gs` = export + one trailing
newline (fixed this session, below).

### S133.1 — D194 BUILT, TESTED, LIVE. F-20 / patient_deceased / number_invalid CLOSED.
- The **`Do_Not_Call` tab** exists in the Callback Tracker sheet: `Phone · Reason · Set By · Set When ·
  Note`. **Human-maintained. Code never writes or creates it** — a renamed tab must fail loudly, not be
  papered over by auto-creation.
- `push_followups_today.py` rebuilt from the triple-verified source (`fc0a731d…`, 16,600 b, 428 l) by
  **five guarded anchor edits** (62 lines added, 1 comment line replaced): new `TAB_DNC` config; new
  `fetch_dnc_set(sh)`; filter applied to `Followups_Today` only (Settled is history, no calls placed
  from it); preview mode unchanged and credential-free; every console mention of a number masked.
- **Safety contract:** tab MISSING → loud warning every run, push continues (a renamed tab cannot brick
  the morning list, but is seen immediately). Tab present but UNREADABLE → **the push refuses** — never
  push a worklist that skipped the do-not-call check. A `Phone` cell that will not normalize is
  reported (masked) and skipped, never silently ignored.
- **Installed:** `python -m py_compile` clean on the clinic PC; placed at the tracker folder;
  **19,497 b · 489 l · md5 `7693a29a98dddbbdf01846fd139f5649` · CR 0**, verified by `certutil` on the
  PC. Rollback beside it: `push_followups_today_OLD_S133.py`.
- **Proven end-to-end on live data:** with one real Due-Today patient in the tab, `--push` printed
  `Do-not-call list loaded : 1 number(s)`, removed exactly that row (masked), and wrote **121** of 122;
  the test row was deleted and a second push restored **122** with `0 number(s)`. The standing staff
  rule from today: **deceased / wrong number / asked-not-to-call → one row in `Do_Not_Call`; gone from
  the next morning's push onward.**

### S133.2 — REPO HYGIENE: commit `84831b0`, four findings closed, verified from GitHub by hash
Executed on the owner's PC by a **guarded one-shot batch** (`update_repo_S133.bat`): every input's
existence checked; `att_config.py` renamed **only after** `findstr` proved the `CHANGE THIS`
placeholder present (a real secret aborts the run); `push_followups_today.py` staged only after
`certutil` matched `7693a29a…`; the fetched `wa_send_api.py` accepted only after the live-only
`logged=` marker was found in it (a check calibrated to F-27's own evidence); review pause before
commit. Git ran from **GitHub Desktop's bundled binary** (no system git on the PC) —
`%LOCALAPPDATA%\GitHubDesktop\app-3.6.2\resources\app\git\cmd`, PATH-set for one window.

Verified afterwards **from the published GitHub tarball, not from the PC**:
- **F-31 CLOSED** — `attendance/att_config.py` untracked; `att_config.example.py` tracked, placeholder
  intact; `.gitignore`'s existing rule (L81–82) now actually protects the future.
- **F-17 CLOSED** — the deployed `WebApp.gs` content **was already in the repo** under the name
  `WebApp_v19_D189.gs` (byte-identical to the export) — the fix was pure renames: `WebApp.gs` is now
  `5173c3c7…`; the pre-change file (`276dc197…`) is kept as `WebApp_PRECHANGE_ROLLBACK.gs`;
  `CallField.gs.gs` → `CallField.gs`, `Probe.gs.gs` → `Probe.gs`.
- **F-30 CLOSED** — `watch_and_push_followups.py` (**`8561f3d75f986daf2fae1002e0e16856`**),
  `start_followup_watcher.bat`, `SETUP_followup_watcher_autostart.txt` committed. The morning push is
  no longer backed up nowhere but one Windows disk.
- **F-27 CLOSED** — deployed `wa_send_api.py` committed (**`bc76e5cbb6d362e32ada3f90ed3a0c2f`**),
  `logged=` marker present ×2.
- `dashboard/Health.gs` aligned to the export byte-for-byte (**`9461d01b…`**) — the recurring one-byte
  false finding is retired.
- `followup-tracker/push_followups_today.py` in the repo = the installed D194 build (`7693a29a…`).

### S133.3 — `wa_approve` IS A SERVICE. The last bare nohup is gone.
Facts taken from the VPS before design: running as `/root/wa/venv/bin/python3 wa_approve.py` (Flask dev
server) since 05 Jul 01:05, PID 696717; `WA_APPROVE_PORT=8101`, `WA_APPROVE_HOST=127.0.0.1` (extracted
by targeted `grep` — never the whole env file, which holds `WA_APPROVE_KEY`); deployed
`/root/wa/wa_approve.py` md5 **`c650f4c28ed576549fa661fcf65a49f5` = the repo copy — no drift.**
`wa-approve.service` (672 b, **`e18048b2b4901c2e182063b2f8f7d649`**) modelled on the proven
`wa-send-api` unit: gunicorn `-w 1 -b 127.0.0.1:8101 --timeout 300` — **the 300 is load-bearing**: one
LIVE batch can fire up to `WA_DAILY_CAP` (default 100) sends inside a single POST at 1–2 s each, and a
default 30 s worker timeout would kill it mid-batch. The app self-loads `wa_approve.env` from its own
folder, so the unit needs no `EnvironmentFile=`. Installed: `daemon-reload` → `kill 696717` →
`enable --now` → **`active (running)`, enabled, gunicorn holding 8101** (`ss` verified) → the approve
page **verified loading in the browser through the OLS proxy** with the day's file and sections.
Along the way two operator notes proved out: `…/wa-approve/send` answers *Method Not Allowed* to a
typed URL — correct, POST-only, nobody fires sends by visiting a link; and the page's own address with
`?k=` lives in browser history — retrieved from there, never pasted into chat.
**Queued:** commit `wa-approve.service` itself into `wa-approve/` (it is currently the only unit file
of the set not in the repo).

### S133.4 — A-7 DONE: the trigger inventory, and what it showed (F-32, F-33)
The Triggers screenshot (11 Jul 00:36 IST): **15 installed triggers**, all time-based, all Head, all
owned by the owner. Functions seen: `runIntradayDigest` (**≈8 instances**), `runSummaryEmail` (**3**),
`rebuildCallFeed`, `sendFollowupSummary`, `checkFollowupListFresh`, `runMorningReport`,
`dailyHealthReport` (1 each).
- **F-32 — trigger duplication.** One function installed ≈8× and another 3× means repeated runs per
  period: quota burned (Block C's exact currency) and possible duplicate digest emails. Cause unknown
  (likely repeated installer runs without a matching remove). **Dedupe belongs in the next Apps Script
  pass, alongside A-5** — `removeTriggers`/`removeHealthTrigger` are the very functions involved.
- **F-33 — `runMorningReport` error rate 14.29%**; every other trigger reads 0%. Uninvestigated;
  the executions log will name the exception at the next Apps Script session.
Neither fixed this session — **an audit finds; it does not fix (D180).**

### S133.5 — DECISION D205 — FULL TEXT
- **D205 — Patient-facing WABA features are designed at session start, never built as late-session
  add-ons. The "seen-today" section of `wa_approve` is recorded as designed backlog, not built.**
  *11 Jul 2026, S133.* The owner asked why patients seen in clinic today do not appear on the approve
  page. Read from the deployed code (= repo, `c650f4c2…`): the page reads **only the Call Sheet** of
  `Staff_Action_Today_*.xlsx` and shows **only** the five bucket statuses mapped in `STATUS_TEMPLATE`
  (Due Today · Grace Period · Actionable Missed Follow-Up · Probable Dropout · Procedure call-back).
  Patients seen today are by definition not on the follow-up call sheet — **nothing is broken; the
  feature never existed.** Building it means: a new data source on the VPS (**the owner's daily Docterz
  CSV export — exported by the owner, NOT Shavez; this corrects the working record**), a template
  decision, opt-out + dedupe + send-log + TEST-mode wiring equal to the existing sections. Parents:
  D194 (enforcement point), the wa_approve safety model (S64). **Scheduled for a session-start design,
  half-session scope.**

### S133.6 — RECORD CORRECTIONS AND RE-SCOPES
- The decisions-index header still read *"Next free: D204"* after S132 had spent D204 — the changelog
  and §S132.7 were right; the header was not. Corrected to **D206**. D172's own field, once again.
- **A-4 re-scoped.** F-11's fix (sign-out button; strip `?k=` after reading; clear `clinicDashKey`) is
  **client code in `Dashboard.html`**, per the audit's own F-11 text — not a ten-second manual action.
  It moves into the next Apps Script pass with A-3 (L1128) and A-5. The interim hygiene step (clearing
  `script.google.com` entries from shared-device browser history) was **parked by the owner to next
  session** — it removes the stored `?k=` from history and autocomplete on the reception tablet.

### S133.7 — WHAT THIS SESSION DID NOT DO
Group 2 untouched: A-3's L1128 catch, A-5's two trigger-killers, the F-11 code fix — all queued for one
Apps Script pass built from the fresh export. A-6 (the sixteen server catches) unclassified. F-18
parked with the AI layer by owner directive, with A-00, A-0, A-1 — none raised. F-32/F-33 recorded, not
fixed. Block C/D untouched (D185 ordering stands). The rotation stayed parked and was not raised.



## §S134 — ONE APPS SCRIPT PASS: F-32 WITHDRAWN, FOUR CLOSURES, SIGN-OUT LIVE (v18.21)

### S134.0 — Summary
**Session type: FULL EOS — two Apps Script files changed (`Main.gs`, `Dashboard.html`), deployed as
`v18.21 · S134` on the single existing deployment (URL unchanged).** No VPS file, no PC file, no
`.env`, **no trigger deleted**, `WebApp.gs` untouched (D34 intact), rotation and the AI review layer
never raised (owner's S133 parking honoured). Every claim below verified from an artefact.

### S134.1 — Phase 0/1: nine matches
All nine canonical docs matched the S134 opener's hash table exactly; CR 0 everywhere; end-markers
present; stale versions absent; secret scan clean; export `523ddcbe…` confirmed current and used as
the sole build source.

### S134.2 — F-33 CLOSED: classified external (D120 window), no code change
The executions log read before anything was edited (per plan): **one failure in seven days** — 09 Jul
07:36, duration 1.556 s against a 4–14 s normal, error `Exception: Address unavailable:
https://developers.myoperator.co/search at fetchCallsBetween_(MyOperator:109) at
runMorningReport(Main:53)`. That timestamp sits squarely inside the **D120 MyOperator outage window**
(cleared 10 Jul; ticket 653584 open). Not quota, not a code bug; every run since completed. The
"14.29%" was 1/7 of a rolling window. **Optional hardening recorded, not built:** let the morning
report survive a fetch failure with a "call data unavailable" note — backlog, low priority; the
failure is a useful visible symptom of a MyOperator outage.

### S134.3 — F-32 WITHDRAWN: the "duplicates" were the design
**The installer was read before anything was deleted.** An Apps Script daily trigger fires once at one
hour, so `setupTriggers()` deliberately installs one trigger per clinic hour:
`CFG.INTRADAY_HOURS: [8,10,12,14,16,18,20]` → **7 × runIntradayDigest**, `CFG.EMAIL_HOURS: [11,15,19]`
→ **3 × runSummaryEmail**, + 1 morning + 4 subsystem (rebuildCallFeed, sendFollowupSummary,
checkFollowupListFresh, dailyHealthReport) = **15 exactly**. The owner then counted the Triggers
screen: **7 / 3 / 15 — zero duplication.** S133's "≈8×" was a screenshot miscount of 7 (the total of
15 was arithmetically incompatible with 8 all along: 8+3+5=16). **Third finding cleared by reading the
code that installs the thing** (the F-19 pattern). No quota was ever leaking; Block C loses nothing.

### S134.4 — The build: A-5 + A-3 remainder + F-11/A-4, one deploy, artefact-verified
- **A-5 CLOSED.** `removeTriggers()` (`Main.gs`) was a bulldozer: it deleted **every** project trigger
  — including `dailyHealthReport`, `rebuildCallFeed`, `sendFollowupSummary`,
  `checkFollowupListFresh`, none of which it owns — and `setupTriggers()` calls it first, so any re-run
  of setup would have silently killed the 09:00 health email and three other subsystems. **Now scoped
  to Main's own three handlers** and reports its count (`removeHealthTrigger` was always the model;
  unchanged). `Main.gs` → **4,817 b · 107 l · `1a85166c72c624c3fa5533a3cf02c4c9`**.
- **A-3 CLOSED.** The `openThread`-after-send catch now logs to console (the reply is already sent at
  that point; console is the right level). **F-14's three wrong client catches are all gone** — two
  removed with Fix B (S132), this one uncloaked (S134). **18 trivial guards remain**
  (localStorage/DOM; 7 of them added by S134's own key-hygiene code, correctly) — counted with scope
  (D179).
- **F-11 / A-4 CLOSED.** **Sign out** button in the header; `doSignOut` removes `clinicDashKey`, sets
  a `clinicSignedOut` flag, zeroes `DASH_KEY`/`DASH_ROLE`, stops the refresh timer, shows the login
  card. **Boot checks the flag before any key source** — after sign-out, both a `?k=` in the URL and
  the stored key are ignored; explicit login clears the flag and re-arms auto-login. Keyed URLs in
  shared-device browser history remain the owner's manual hygiene step. `Dashboard.html` →
  **158,612 b · 2,753 l · `5ff68c3d66a8b8d85eb31b70399a13c1`**, `PAGE_BUILD v18.21 · S134`.
- **Build discipline:** seven guarded anchor edits (each asserted count=1), `node --check` clean on
  `Main.gs` and on the page's extracted JS, CR 0. **Deploy:** existing deployment → New version.
  **Feature checks 3/3** (stamp + button visible; sign-out then the old `?k=` bookmark → login card,
  not auto-login; key login → auto-login re-armed). **Fresh export
  `Clinic_Callback_Tracker__5_.json` — 466,953 b · md5 `8bd1aeaa19459286566ce20abe72e4a2` · 15
  files: `Main` and `Dashboard` byte-identical to the built files; `WebApp` `5173c3c7…` and `Health`
  `9461d01b…` unchanged.** Closed in the artefact, not just the record.

### S134.5 — A-6 / F-2 CLOSED: nineteen catches classified individually; zero fixes needed
**Count corrected with scope (D179): F-2 said sixteen; the artefact has nineteen** — the original 16
plus 3 that arrived with `Health.gs` (S128); the arithmetic reconciles exactly. Classification:
- **11 deliberate fail-open enrichments** (`getFollowups` L968; `getEscalations` L1391–93;
  `Callconsole` ×4; `OutcomeLog` ×3): a *lookup* failure (patient name, agent name, today-calls badge,
  transcript) blanks a field and never blocks staff — the D156 family. Residual noted: a wrong
  `PATIENT_SHEET_ID` degrades silently to missing names; staff eyes are the detector; bounded.
- **6 alert-path guards** (`Diagnostics` L114/128/143; `Health` L205/360/373): email and ntfy each
  guarded so one channel's failure doesn't kill the other; one broken tab doesn't kill the health
  report; and the alerter's own death is covered by the 09:00 dead-man design.
- **1 save-protection** (`WebApp` L1309): a failed urgent-incoming *notification* must never fail the
  outcome *save*.
- **1 dead code** (`Probe.gs` L67): dies with the file (Block D/E, F-15).
**Verdict: the audit's instinct was right to flag them and right not to touch them (D180).**

### S134.6 — Decisions minted, and the SECRET_KEY fact
- **D206 — trigger ownership: each file removes only its own triggers.** A cleanup function names its
  handler functions explicitly; a project-wide `deleteTrigger` sweep is forbidden.
  `removeHealthTrigger` was always the model; `removeTriggers` now conforms.
- **D207 — sign-out via flag, not URL surgery.** The Apps Script sandbox **cannot modify the parent
  address bar**, so "strip `?k=` after reading" (A-4's original wording) is impossible as written. The
  sandbox-legal equivalent: a device-local `clinicSignedOut` flag checked **before any key source** and
  cleared only by explicit login. Same protection, honest mechanism.
- **Recorded fact (S134):** this project's live full-access Script Property is **`SECRET_KEY`** —
  `WebApp.gs` L148 accepts `DASH_KEY` **or** `SECRET_KEY`, and `DASH_KEY` was never set on this
  deployment. The owner's property list as reported: `MYOP_TOKEN`, `SECRET_KEY`. **Whether that list
  was exhaustive (STAFF_KEY, AKEY_*, SHEET_ID, PATIENT_SHEET_ID rows) is `UNKNOWN` (D166)** — the
  owner reported two names and moved on; confirm the full name list before building any per-agent
  feature.

### S134.7 — Document state after S134
| Document | Version |
|---|---|
| `Clinic_Master_KB_SystemsRegister_v1_60.md` | **v1.60** (this file) |
| `HANDOFF_RUNBOOK_2026-07-11_Session134_v72.md` | **v72** |
| `Dr_Manoj_Clinic_Umbrella_Architecture_v1_46.md` | **v1.46** |
| `Clinic_Callback_Tracker_AppsScript_Audit_v1_5.md` | **v1.5** (re-based: F-2/F-11/F-14 closed) |
| `Frontend_Dashboard_Documentation_v2_S134.md` | **v2** (complete re-base; F-29's debt paid) |
| Fault Register v2.1 · Diagnostics v2.1 · Call Console v2.0 · AI Review v1.1 · Incident v5 | unchanged |

**Live artefacts:** Apps Script export `Clinic_Callback_Tracker__5_.json`
**`8bd1aeaa19459286566ce20abe72e4a2`**, 15 files (`Main` `1a85166c…` · `Dashboard` `5ff68c3d…` ·
`WebApp` `5173c3c7…` · `Health` `9461d01b…`), deployed `v18.21 · S134`. PC and VPS artefacts unchanged
from v71 §3.

## §S135 — SESSION 135 (11 Jul 2026): the shared-mobile identity incident, the S35 loop closed, and the ingest hardened

### S135.1 — F-34: one root cause, two symptoms, found by the owner on one tile
The owner reported Raj Rani's follow-up tile showing a different patient's Clinic ID; later, that its
"last visit" was her FIRST visit. Both were the SAME defect. The Docterz record was never wrong: three
consultation exports (05-Jun, 16-Jun procedure, 04-Jul) all say Raj Rani = **7361**, mobile shared with
**Ekta = 7362** (family mobile). The corruption was display-side, two layers deep: **(a)**
`push_patient_mirror.py` collapsed the Patient_Master upload to **one row per PHONE** ("keep last
occurrence per phone"), so only Ekta travelled up; **(b)** `Callconsole.gs`'s D52 enrichment
(`cc_patientMap_`, "first wins") painted that one row's ID **and last-visit date** onto every relative
on the mobile. The "first visit" the owner saw was **Ekta's last visit**. A second live collision
existed the same day: J P Singh / Manjeet Kaur share a mobile; one displayed the other's ID.

### S135.2 — F-34 CLOSED (D208): three files, simulated on the real cases, then live-verified
- `push_patient_mirror.py` → keyed by **Patient UID** (one row per patient): `d3105f6901700bad5300ea61b014a102` (was `815e5132…`).
- `Callconsole.gs` **v1.3** → name-aware enrichment: new `cc_patientMultiMap_` (all patients per phone),
  `cc_fuEnrich_` matches each Followups_Today row to its OWN patient by token-overlap ≥ 0.7 (the PC
  resolver's rule); unique mobiles keep the legacy plain key so a stale open page degrades to blank,
  never to a wrong ID: `44330498575dc5b46f6ed623445d05c2` (was `f32550bb…`).
- `Dashboard.html` **v18.22** → six lookups made name-aware via `fuLookup`; a shared mobile with no
  confident match shows **"ID ⚠ verify"**, never a guess: `a45d7da8f103fe03cc332cda94854230` (was `5ff68c3d…`).
Offline simulation passed on the day's real cases (Raj Rani→7361, Ekta→7362, J P Singh→7342,
Manjeet Kaur→7614, Satendra Kaur→6986 unique, partial-name→verify marker). **Live-verified same day**:
Raj Rani's tile = **ID 7361 · Last visit 04-Jul**; mirror re-push wrote **7,407 patients one-per-UID**
("Last Visit" correctly wired to `Last_Seen_Date`). Incoming-call tiles stay phone-keyed **by design**
(caller-ID is all a ringing phone can offer). Diagnosis/Age/Gender columns in the mirror are blank —
the master file lacks them; filling them is item 5 of the S135.6 migration plan.

### S135.3 — F-35 CLOSED (D209): the review console's SEND BACK finally reaches staff
The Session-35 gap ("recorded now; drives list suppression when the loop-closing build lands") had let
four owner SEND BACKs (Shashi Sahu, Rajni Saxena, J P Singh, Raj Rani, 09:20–09:27) vanish for staff.
Built: `getReviewSendbacks` in **OutcomeLog.gs** (READ-ONLY on `Followup_Outcomes`; one-writer rule
intact — S135b adds a reader, F-3's writer count unchanged): latest 'SEND BACK' verdict per Key becomes
a Session-52-shaped tile carrying the doctor's note; it retires when staff log ANY newer outcome or the
verdict is re-reviewed to APPROVED. `Dashboard.html` **v18.23** merges tiles idempotently into the
'Sent back by doctor' band (`_sbBase` guards the open-count against re-render drift). Simulated on the
day's REAL 13 outcome rows (4 tiles, correct notes; retire-on-action and retire-on-APPROVED both pass).
**Live-verified**: all four tiles appeared on the reception-mobile login with notes. Hashes:
OutcomeLog `9fc4c941bc067a40ce43eb40e8e81376` (was `7ba7d212…`), Dashboard `132d62579702b5c651347af97dea2c03`.

### S135.4 — D210: identity evidence hardened at ingest, and the ledger cleaned
`processor.py` (base gate-checked `171a090645da130a4f4cbb0c0b102f22` → installed `0e7c129f57b53fca2cb21ba6dcd4d381`):
**(a)** `resolve_identity` single-mobile matches are now name-checked; a disagreement keeps the match
but demotes to **"Medium"** with Identity_Issue "Name differs from registered owner (…) — verify" —
"Medium" passes every issuance filter (no patient drops off the call sheets) and deliberately loses
only the mobile-keyed diagnosis fallback, which is exactly what is unsafe when names disagree.
**(b)** Footer guard: only UID-shaped rows (`[A-Z0-9]{8,14}`) enter `parse_consultation_report`.
**(c)** `clean_visit_ledger_junk.py` (`535af72132149cd76bfd750417c7e8eb`, preview-by-default, backup-on-apply) removed the
09-Jul footer leak — V000819 "Credit Card" and V000820 "0/7400" from `consultation_report_2026-07-09.csv`
— ledger 831 → **829**, backup `visit_ledger_BACKUP_<stamp>.csv` beside it. Verified clean (re-run: 0 junk).

### S135.5 — Two non-incidents, and a correction on the record
Tiles "disappearing" mid-day was the **settle model working** (D13: logged outcomes leave the worklist;
the Excel is a morning snapshot). And this file records a session error: the assistant asserted from
memory that Manjeet Kaur (F000562) "should still be on the list" — the morning workbook proved she was
**never issued** (119 keys, F000562 absent). D172 restated: expected values come from the artefact.

### S135.6 — Clinical data report: evaluated, superset-verified, migration designed (build pending)
Docterz's new "clinical data report" export was verified **header-by-header against the code**: every
column `parse_consultation_report` and `revenue.py` read exists under the identical name; the datetime
format is the one `parse_date` was written for; the banner row is identical; the footer is a single
blank-UID "Total" row (cleaner than the old report that caused S135.4c). New riches: same-day
Diagnosis, named Procedures, prescriptions/dosage, Tests, Instructions, **Follow Up date (no
Appointment ID)**, DOB/Age/Gender/Address, invoice, collector, full revenue split. Migration plan
(enumerated, approved in principle, **no decision number until built**): accept both filenames; ingest
new columns additively; same-day diagnosis write-through; procedure detection via the named column
(catches ₹0 cashless; may retire the manual marker); **follow-up log stays the source of truth** (its
Appointment-ID dedupe is load-bearing) with the report's Follow-Up column as a reconciliation
cross-check — owner yes/no pending; mirror keeps its 8 columns (**clinical fields never travel to the
Sheet**); optional Day-Revenue enrichment later.

### S135.7 — Decisions minted, document state, and artefacts
- **D208 — identity displays are name-aware on shared mobiles; a blank + "verify" beats a wrong ID.**
  Phone-only lookups are lawful only where the phone is the only evidence (incoming caller-ID).
- **D209 — a review SEND BACK drives the worklist.** The verdict re-surfaces the tile (with the note)
  until staff act or the verdict flips to APPROVED. Readers may span files; writers may not.
- **D210 — identity evidence rules at ingest:** a single-mobile match is never "High" without a name
  check; only UID-shaped rows enter the pipeline; demotion must never remove a patient from calling.

| Document | Version |
|---|---|
| `Clinic_Master_KB_SystemsRegister_v1_61.md` | **v1.61** (this file) |
| `HANDOFF_RUNBOOK_2026-07-11_Session135_v73.md` | **v73** |
| `Dr_Manoj_Clinic_Umbrella_Architecture_v1_47.md` | **v1.47** |
| `Clinic_Callback_Tracker_AppsScript_Audit_v1_6.md` | **v1.6** (F-34, F-35 recorded CLOSED; F-3 reader note) |
| Frontend Doc v2 · Fault Register v2.1 · Diagnostics v2.1 · Call Console v2.0 · AI Review v1.1 | unchanged |

**Live artefacts after S135:** Apps Script sources `Dashboard.html` **v18.23** `132d62579702b5c651347af97dea2c03` ·
`Callconsole.gs` v1.3 `44330498575dc5b46f6ed623445d05c2` · `OutcomeLog.gs` `9fc4c941bc067a40ce43eb40e8e81376` (owner to export fresh
`Clinic_Callback_Tracker__6_.json` next session; `Main/WebApp/Health` unchanged: `1a85166c…` /
`5173c3c7…` / `9461d01b…`). PC: `processor.py` `0e7c129f57b53fca2cb21ba6dcd4d381` · `push_patient_mirror.py` `d3105f6901700bad5300ea61b014a102` ·
`clean_visit_ledger_junk.py` `535af72132149cd76bfd750417c7e8eb` · visit_ledger 829 rows. VPS unchanged.

**Next free decision number: D211. Next free finding number: F-36.**

---

## §S136 SESSION 136 — three deploys, all live-verified same day (11 Jul 2026, evening)

### S136.1 — WHAT SHIPPED (Apps Script, three "New version" deploys on the one existing deployment)
- **Deploy 1 — Block C (D185 order honoured):** `Dashboard.html` v18.24, `Callconsole.gs` v1.4, `Health.gs` v2.3.
  ONE CLOCK: `cc_todayIST_()` rides in every refresh; the page computes no dates; `fuDayKey()` prefers the
  server date; the last UTC line (F-13, L1857-class) retired. ONE TRIP: `getDashboardBundle(key,{force,olDay})`
  replaces ~9 calls/min/device, cached 45 s per ROLE in `CacheService` (staff cache ≠ doctor cache; force
  bypasses AND refills, so a post-save refresh is what every device sees next). Bounded poll:
  `getCallDurationFast` reads the LAST 200 rows of `Call_Durations`, not the whole tab (a 3-min call used to
  re-read it ~30×). Hidden tabs stop refreshing and catch up instantly on return. `cc_qcBump_` counts full
  builds/day into Script Property `QC_BUNDLE_BUILDS`; `Health.gs` §4b prints QUOTA HEADROOM (advisory problem
  above 2,000 builds/day) — audit §4-Q3 closed. Closes **F-5, F-6, F-12, F-13**.
- **Deploy 2 — F-36 + WhatsApp call line:** `Dashboard.html` v18.25. **F-36 raised and CLOSED the same
  evening:** the ESCALATION card was a seventh phone-keyed surface F-34 never counted — its ID/last-visit are
  baked at save time or filled by WebApp's phone-keyed map, painting a relative onto shared mobiles
  (live case: Raj Rani shown as 7362 · 30-May = Ekta). Cure = the S135 pattern applied client-side:
  name-aware `fuLookup` wins; shared-no-match shows **ID ⚠ verify** (D208); mirror-unknown mobiles keep the
  stored value. Live-verified: Raj Rani card → **7361 · 04-Jul**. *Deliberately untouched:* the card's
  diagnosis (maps don't carry it; evidence absent) and the outcome-log/history chips (a log shows what was
  logged). WA tiles now carry today's outgoing call — who called · when · duration/not-connected · 🎧 — built
  client-side from the bundle's `allCalls` (phone10 recovered from the call `id` prefix; zero extra reads).
  Today-only by design; per-call history is Block D. Verification parked (no WA call occurred after deploy).
- **Deploy 3 — F-4 + Block E + D183:** `Callconsole.gs` v1.5 + `appsscript.json` manifest + **Probe.gs
  DELETED**. F-4 closed: dead `logOutcome` + `cc_ensureOutcomesTab_` + `Outcomes_Log` constants removed
  (public writer, called by nothing, tab never created). Block E closed: Probe.gs deleted and the
  `documents` OAuth scope dropped from the manifest (F-15/F-7). **D183 built:** `sweepUnloggedCalls` — 21:30
  IST digest to the doctor of every call, BOTH directions, whose number has no outcome row today; read-only
  mirror, moves nothing; shared family mobiles are NOT named (D208 — "(shared family mobile)").
  `installSweepTrigger` run once by the owner (D206); trigger armed and visible. Manual run live-verified:
  digest of ~34 numbers received; its content already demonstrates the Block D gap (incoming connected calls
  produce nothing).

### S136.2 — LIVE-EDITOR VERIFICATION (post-deploy export `Clinic_Callback_Tracker__7_.json`)
All 13 files byte-match the delivered work (export-form md5 = file md5 computed after stripping ONE trailing
newline — the Apps Script editor strips it; proven this session on OutcomeLog, S136.4). `Probe` absent ✅;
manifest carries NO `documents` scope ✅. `Callconsole` v1.5 `4c15e7a5…` · `Dashboard` v18.25 `f38aa92e…` ·
`Health` v2.3 `83ebfc51…` · `appsscript` `7ad6f2fe…` · all ten untouched files match their S135 hashes.

### S136.3 — CALLHOOK ROTATION: the optimistic reading, corrected
Two status checks were clean (0 on PREV/30 min) — but "accepted today" sat at 108 in BOTH, i.e. **zero calls
flowed between them; the clean window was vacuous.** Step 3 (Lokesh updates the panel) remains UNCONFIRMED;
the KB's 09-Jul record (12 calls/30 min on PREV) stands as the last traffic evidence. Step 4 stays locked
(D173 — its command is deliberately withheld). The decisive test is a status check during weekday traffic.
The assistant asserted "Step 3 appears done" before checking the counter's denominator — withdrawn in-session;
D172's lesson, again: a zero is only evidence when something flowed.

### S136.4 — VERIFICATION FACTS LEARNED
- **The editor strips the file's final newline.** OutcomeLog "drifted" by md5 at session start; byte-diff vs
  the S135 GitHub copy proved equality except one trailing `\n`. Rule: **expected hashes for editor exports
  are computed on `rstrip('\n')` content** ("export-form"). START_HERE_137's table is export-form throughout.
- Two build-script failures were caught by the anchor/content guards before any file was written (a cutter
  that stopped at a `}` inside a docstring example; a placeholder line left in a heredoc). The guards, not
  luck, kept the delivered files clean — the practice stands.

### S136.5 — F-3 BOOKKEEPING (closed as CLASSIFIED, no code)
Three functions write `Followup_Outcomes`: `WebApp.saveFollowupOutcome`, `WebApp.saveIncomingOutcome`,
`OutcomeLog.reviewOutcome` (review columns only). Safe today because their column sets are **disjoint by
layout, not by contract**. Standing note recorded here as the contract: any new writer to that tab, or any
column-set change in an existing one, must re-derive the disjointness before deploy. One-writer-per-table
(D-series) remains the rule for every OTHER table.

### S136.6 — DECISIONS MINTED
- **D211 — The dashboard read model is ONE bundled trip behind a per-role shared cache.** `getDashboardBundle`
  is the page's sole per-cycle read path; 45 s `CacheService` TTL per role; `force` bypasses and refills;
  reviewing a non-today outcome day is never cached; a cache failure degrades to a plain build, never to an
  error. Old per-function endpoints remain answering so stale open pages survive a deploy. *(11 Jul 2026, S136.)*
- **D212 — WhatsApp tiles show TODAY's outgoing call only, from data already in the bundle.** No new reads,
  no new tabs; the permanent per-call history belongs to Block D and must not be half-built here.
  *(11 Jul 2026, S136.)*

### S136.7 — OPEN AT CLOSE (feeds Runbook v74 §2)
Block D remainder: (a) VPS `call_hook_capture.py` stops discarding incoming (F-19) — its own careful pass;
(b) §K one-tap staff buttons — blocked on OWNER wording + the D78-vs-D195 third-attempt conflict;
(c) D205 seen-today WABA — session-start design per its own text, owner template decision pending.
F-10 markup cure — own commit per the audit. Frontend Doc v2 is stale in its read-path section (bundle
architecture) — v3 scheduled. Docterz clinical-report migration decision. CALLHOOK Steps 3–4 (Lokesh).
Service-account key rotation (overdue, highest-standing risk) · AKEY_14 · Hindi spellings in vitals LIB ·
Notion orphaned pages. Three owner questions issued in-session (D205 template · §K wording · D78 vs D195).

---

## §S137 SESSION 137 — decisions + design, NO code (11 Jul 2026, late evening; EOS-light)

### S137.1 — WHAT HAPPENED
A decisions-and-design session immediately after S136's three deploys. **No live system, VPS file, or
Apps Script line was touched.** Phase 0: KB/Runbook/Audit/Console Spec md5-exact; **Umbrella v1.48 was
ABSENT from project knowledge** — recovered from GitHub `canonical-docs/` (md5 `7fa7ae2251996bdc4c5f38ac1606903b`,
exact match to the Runbook v74 companion table) and restored by the owner. Phase 0b: all 14 files inside
export `__7_` match export-form hashes; `Probe` absent. Phase 1 (read via Gmail connector): the **D183
digest arrived TWICE on 11-Jul** (21:15 and 21:24 IST, identical "34 numbers, 53 calls") — one was the
in-session manual run, the other very likely the armed trigger; **12-Jul night's arrival count is the clean
test: exactly one = trigger healthy, two = duplicate trigger to remove.** The **QUOTA HEADROOM first read
moves to the 12-Jul morning mail** — 11-Jul's morning mail was generated before the evening Block C deploy.
CALLHOOK: owner sent the Step-3 message to Lokesh in-session; next act = ONE weekday-traffic status check,
then Step 4 (D173 discipline unchanged).

### S137.2 — DECISIONS (D213–D216, all template names live-verified against the panel same evening)
- **D213 — Seen-today patients get the approved `drmanoj_post_visit` template** ({{1}} = name). Closes the
  open input on D205 (the feature decision, S133). The D205 build remains pending (session-start design,
  half-session, VPS `wa_approve` scope). *(11 Jul 2026, S137.)*
- **D214 — §K one-tap button wording locked verbatim:** मरीज़ आ रहे हैं · नहीं आएँगे · बात हुई — फिर call
  करना · बात नहीं हो पाई · डॉक्टर को दिखाना है. *(11 Jul 2026, S137.)*
- **D215 — Third attempt = auto-WABA + snooze + doctor NOTIFIED in the panel (read-only band; not an
  action queue).** Supersedes the D78-vs-D195 either/or: D78's WABA+snooze mechanics stand; D195's
  send-to-doctor becomes notify-the-doctor. The band rides inside `getDashboardBundle` (D211) as a filter —
  zero extra reads. *(11 Jul 2026, S137.)*
- **D216 — 3rd-strike message = the existing approved `drmanoj_followup_due`** ({{1}} name, {{2}} due date —
  the API card's confirmed-200 send body already uses it); **snooze = 3 days**; the F-34-family residue
  (escalation-card diagnosis + incoming-tile names, both name-aware) **rides in the same K-1 build**.
  *(11 Jul 2026, S137.)*

### S137.3 — §K.6 DESIGN LOCKED (canonical home: Call Console Evolution Spec v2.2, §K.6)
Full design written and closed with **zero open inputs**: five buttons at gate-resolve (D214 wording; codes
`K_COMING / K_NOT_COMING / K_CALL_AGAIN / K_NO_CONTACT / K_TO_DOCTOR`); one row per tap into the one-writer
`Followup_Outcomes` with a `ui=K` marker; measured-not-connected shows the one honest choice pre-highlighted
but never auto-files; fail-open per §J; cross-day miss counter (any of the four reached-codes zeroes it);
3rd strike per D215/D216; Phase K-1 = outgoing only (+F-34 residue), Phase K-2 = incoming after F-19;
parallel run with per-agent completion counter in the bundle; old flow retires only after completion beats
42 % for five consecutive clinic days. The build (backlog A2) can start cold from the spec section alone.

### S137.4 — WABA TEMPLATE INVENTORY, PULLED LIVE (System B `GET /chat/templates`, both pages)
- **14 approved templates** (panel `count:14`; pagination `limit/offset`, page size 10 — a single-page read
  silently misses four). All 7 the API card listed are confirmed live, **+7 the card did not know**:
  `appointment_confirmation_ortho` · `appointment_reminder_1day_ortho` · `reschedule_confirmation` ·
  `welcome_template` · `decline_acknowledgement_manoj` · `missedaftercall` · `daily_account_summary`.
- **Placeholder split (send-blocking fact):** the five `drmanoj_*` templates use NUMERIC keys
  (`body:{"1":…}` — the card's existing rule); the other seven use NAMED keys (`var_1`, `date`, …).
  The numeric rule is true for the drmanoj set, **not universal**.
- **`missedaftercall` (hi) duplicates `eng_missedaftercall` (en)** — same body; which one the panel
  automation fires is unconfirmed (Khushi/Lokesh someday, no urgency). **`daily_account_summary`** is a
  stray non-clinic template (vehicle/collections) — do not use; panel-tidy candidate.
- **Token name recorded:** the WABA Bearer token in `/root/wa/.env` is **`MYOP_AUTH_TOKEN`** (a first pull
  attempt with `WA_SEND_TOKEN`/`WA_TOKEN` — the names `wa_send.py` documents for its own env — found no
  line, sent an empty Bearer, and drew the anonymous AWS explicit-deny). D176 held throughout: the token
  was read into a shell variable and never printed; `.env` inspected by key names only (`cut -d= -f1`).
- **New readable canonical: `WABA_Approved_Templates_v1_S137.md`** (all 14 bodies, grouped, decision flags
  inline). **Supersedes `Final_WABA_Utility_Templates_Branded_Links.docx`, which is HISTORICAL** — it
  carries pre-rename names (`FU_Reminder_v2` era) and misled this session's first template recommendation
  until the API card and the live panel corrected it. Template-name truth = the API card + the panel;
  raw JSON snapshots (`templates_snapshot.json`, `templates_snapshot_p2.json`) preserved in project knowledge.

### S137.5 — OPEN AT CLOSE (feeds Runbook v75 §2)
The three S136 owner questions are ANSWERED — nothing in the backlog is owner-blocked. Ready builds, any
order: **A1** (F-19 VPS incoming capture — needs its two session-start design decisions: row key, PHI rule) ·
**A2** (§K K-1 build — design complete, zero open inputs, includes F-34 residue) · **D205/D213 seen-today
WABA** (session-start design, `wa_approve` scope). Then: F-10 markup cure (own commit) · Frontend Doc v3 ·
Docterz clinical-report migration decision · CALLHOOK weekday check → Step 4 · service-account key rotation
(overdue, highest-standing risk) · AKEY_14 · Hindi spellings in vitals LIB · Notion orphaned pages.
Watch items for 12-Jul: QUOTA HEADROOM first read · D183 single-vs-double arrival · first natural WA-tile
call verifies D212.

---

## §S138 SESSION 138 — F-19 EXECUTED: incoming calls become first-class (12 Jul 2026, morning; FULL EOS)

### S138.1 — WHAT HAPPENED
Phase 0: all 7 canonical docs md5-exact; Phase 0b: all 14 export-`__7_` files match export-form hashes,
`Probe` absent. Phase 1 could not run at open (the three watch items are tied to 12-Jul mails that had not
yet arrived; 11-Jul evening session start). Owner picked **backlog A1**. The two required session-start
design decisions were put to the owner in plain language and decided (D217, D218 below). Build → deploy →
a live failure caught within seconds → fix → backfill → independent verification, all inside one session.

### S138.2 — DECISIONS
- **D217 — Incoming rows in `Call_Durations` are keyed `IN-<session_id>`** (webhook `payload.id`, identical
  in `call.end` and `call.summary`, so the pair collapses to one row; the `IN-` prefix cannot collide with an
  OBD `client_ref_id`, which is always phone-timestamp shaped). An incoming event with no session id is
  raw-logged and skipped, never guessed. Owner delegated the key choice explicitly. *(12 Jul 2026, S138.)*
- **D218 — New final column `phone10`: the caller's last-10-digit number, INCOMING rows only; OBD rows
  blank** (their ref already embeds the number our own dialer stamps). Identity is resolved at VIEWING time
  against `Patient_Master`, never at capture — so a caller who becomes a patient later links retroactively
  with zero rework; no caller NAME is ever written. Owner confirmed after the known-vs-future-patient
  question was answered. Amends the receiver's "tab holds no phone number" rule for incoming rows.
  *(12 Jul 2026, S138.)*

### S138.3 — THE BUILD (v3.0 → v3.0.1, one live lesson)
`call_hook_capture.py` v3.0: `extract_record` accepts `category == "incoming"` alongside OBD; header gains
`phone10` (col 14); the receiver self-heals the live header (sole writer of the tab); phone falls back
`payload.customer_number` → top-level `customer_identifier` → customer-leg `phone_number`; everything else
(oneway/callback/webcall/otp) stays raw-log-only; gate/rotation/reject logging untouched. Selftest 42→57.
**First restart, 23:34 IST 11-Jul: `Range (Call_Durations!N1) exceeds grid limits ... max columns: 13`.**
The tab was *created* exactly 13 columns wide; writing N1 needs the grid widened first — offline selftests
cannot see grid geometry. Side effect until fixed: EVERY sheet write (incoming and OBD) deferred; the raw
`.jsonl` log held everything, as designed. **v3.0.1** adds a guarded `ws.add_cols(1)` before the header
write. Restart 08:25 IST 12-Jul: `grid widened to 14 columns` → `header self-heal: added 'phone10' at
column N` → `connected ... 205 rows known`. Live: 827 lines, md5 `b64aee2b7b0bcc986a72e5e4f176a86c`.

### S138.4 — THE BACKFILL (insert-only, idempotent, verified)
New `backfill_call_durations.py` (131 lines, md5 `974ae54952dbc235e5cc6af107e83eeb`): reads every raw log,
runs each body through the receiver's own imported `extract_record` (no copied logic), `call.summary` beats
`call.end` per key, inserts ONLY keys absent from the tab, hard-aborts if the `phone10` header is missing
(wrong-order protection), `--dry-run` first. Dry-run: 9 files / 874 lines / 0 unparsable / 424 extractable /
219 to insert. Real run: **inserted 219 rows** (216 incoming since 03-Jul + 3 OBD strays that predate the
receiver's first stable window). **Independent verification, read from the live tab, not the script's own
report:** 424 data rows (205+219 exact); 216 `IN-` rows all `category=incoming`, all phone10 exactly 10
digits; 208 OBD rows all phone10 blank; zero duplicate keys; 138/216 incoming carry `recording_filename`
(bridged calls — missed calls have none). The newest incoming row's phone10 ends `…2497` — the top pending
callback of 11-Jul, i.e. the new data joins reality immediately.

### S138.5 — FINDINGS (raised, not fixed — D180)
- **F-37 — the VPS health mail's "ACTIONS TAKEN BY WATCHMAN (last 24h)" section showed 04-Jul entries on
  the 12-Jul mail.** Window filter or label is wrong (it appears to print the last N entries regardless of
  age). Cosmetic; `clinic_health_report` script; a future maintenance pass.
- **F-38 — liveness is not write-success.** For ~9 hours (23:34 → 08:25) `call-hook.service` was green in
  every check while 100 % of its sheet writes failed. Nothing surveils the write path (e.g. reading the
  receiver's own "deferred" log lines, or a freshness probe on `Call_Durations`). Surveillance-scope
  candidate for the Diagnostics Spec when it next opens; raised here, deliberately not designed here.

### S138.6 — LIVE READS (Phase 1, executed at close)
12-Jul VPS health mail (08:00): **ALL GREEN** — 9/9 services, 3/3 timers, disk 10 %. Time-gated and carried
to S139: QUOTA HEADROOM first read (the ~09:43 Apps Script mail had not arrived at close) · D183 arrival
count (digest ~21:30 tonight; exactly ONE = healthy) · first natural WA-tile call verifies D212 · CALLHOOK
weekday-traffic status check (Monday; the 11-Jul evening WARN lines prove the panel was still on the
previous key — Lokesh's Step 3 remains genuinely open).

### S138.7 — OPEN AT CLOSE (feeds Runbook v76 §2)
**A1 is DONE and off the backlog. §K Phase K-2 is unblocked** (A2's K-1 can now be planned with K-2 in
sight). Ready builds: **A2** (§K K-1, design complete) · **A3** (D205/D213 seen-today WABA) · **A4** (F-10
markup cure). Standing items unchanged: CALLHOOK Steps 3–4 (Monday check) · service-account key rotation
(overdue, highest-standing risk) · AKEY_14 · Docterz clinical-report migration decision · Frontend Doc v3 ·
Hindi spellings · Notion orphaned pages · panel-tidy candidates. New watch: F-37/F-38 sit in the findings
ledger for a future Diagnostics/maintenance pass.

---


---

## §S139 SESSION 139 — F-10 CURED + K-1 BUILT AND LIVE, THE CALL-LIFECYCLE AUDIT, AND THE FIRST QUOTA BASELINE (12 Jul 2026, Sunday; FULL EOS — two Apps Script deploys, one VPS install, one portal hotfix)

### S139.1 — WHAT HAPPENED
Phase 0 clean: all 9 canonical docs + Frontend Doc v2 md5-exact; export-`__7_` files match export-form
hashes, `Probe` absent. Session opened on the owner's ask: *"complete all pending corrections and upgrades
in the callback tracker, minimum steps"* — answered with a two-pass plan (F-10 then K-1), then, at the
owner's direction, BOTH passes were executed in this one session (Sunday: zero traffic, parallel-run
fallback intact, Monday becomes the single live-verification morning). A full **call-lifecycle audit**
(both directions, capture → verdict) was performed at the owner's request — see S139.5. The owner also
registered a standing product goal: a **consolidated bird's-eye "gist" tile on the portal** (Pass 6, D223).

### S139.2 — BUILD 1: THE F-10 CURE (Dashboard.html v18.25 → v18.26, DEPLOYED + stamp-verified)
The audit's ~24 fragile sites (patient data interpolated into `onclick` markup through two half-blind
escapers) plus 8 same-pattern incoming-form `slotId` handler sites were ALL converted to **opaque data
refs (D219)**: `dref(value)` stores the value in a page-level dedupe-bounded map and returns a key like
`d17` ([a-z0-9] only — safe in every quoting context); handlers receive `dget('d17')`. **No data value
ever enters element markup again.** Handler signatures untouched; 34 guarded edits, every anchor asserted
at its exact count; zero `esc()/jsq()` residue in any handler attribute; `node --check` clean; hostile-value
proof (`D'Souza "x" <b>&</b> \`) round-trips exactly. v18.26 md5 `446d95aed9616423cea2821b37570af5`.
**Audit F-10 is CLOSED (Audit v1.8).** Live verification of the incoming-form tap is PARKED to the first
weekday incoming call (deployed Sunday).

### S139.3 — BUILD 2: K-1 ONE-TAP STAFF UI, END TO END (three artefacts, all live)
Pre-build checklist (Console Spec §K.6.7) executed from the artefacts first, and it mattered: the spec's
"counter lives in worklist assembly" collided with D34 (worklist assembly IS `WebApp.gs`). Resolution =
**D220**: the cross-day miss counter is computed in `Callconsole.gs` inside `getDashboardBundle`
(`missTotals`); WebApp's per-day logic stays byte-identical — which the §K.6.6 parallel run requires anyway.
Reset rule verified against the artefact: a miss = outcome `no_answer` (either flow); ANY other outcome row
for that key zeroes the count (old-flow settle/retry rows included, because both surfaces share one table).

**Artefacts, all verified then installed:**
- **`Dashboard.html` v18.27** (2,988 lines, md5 `4e73682242a34d167c86e8a72a941854`): five Hindi buttons
  verbatim (D214) wired into the three gate states (§K.6.2 — connected → all five; measured-not-connected →
  बात नहीं हो पाई pre-highlighted + ↻ फिर call करें; couldn't-measure → fail-open, all five); 10-second
  ↩︎ बदलें undo, no dialogs (D97); per-device **⚡ One-tap** toggle (localStorage `K_UI`; old dropdown flow
  fully intact); 3-day snooze band (visible, wake button); doctor's read-only "3rd-strike WhatsApp sent
  today" band; per-agent आज: logged/made completion chip. Deployed same deployment, New version;
  stamp + toggle live-verified by the owner at 09:36 IST.
- **`Callconsole.gs` v1.6** (1,128 lines, md5 `eb91034961a20545b5316b144f86075a`): ADDS ONLY + one guarded
  bundle edit. `cc_missTotals_()`, `cc_kLoggedToday_()`, `cc_kStrikesToday_()`, `cc_fireStrikeWaba_()`,
  `saveKOutcome()`. **Write mapping = D221**: buttons 1–3 write `k_coming`/`k_not_coming`/`k_call_again`
  with the settle column set explicitly (`settle`/`settle`/`retry`); button 4 writes **`no_answer`** so ALL
  existing snooze/3-strike/verdict machinery keeps working; button 5 **delegates to `saveFollowupOutcome`**
  (`problem`, detail-prefixed) so the Escalations tab keeps its existing writer. `source='K'` is the ui
  marker on every K row (§K.6.3's ui=K, carried in an existing column — no grid widening, the S138 lesson).
  New tab `K_Strikes` (Callconsole its only writer). `node --check` clean.
- **`wa_send_api.py` v3** (relay): new guarded `POST /wa-send/template` — allow-list
  {`drmanoj_followup_due`, `drmanoj_post_visit`}, numeric-key confirmed-200 body shape (S137), caps = one
  per number+template per day + 50/day global (counter file `/root/wa/wa_template_relay_counter.json`),
  token resolution `MYOP_AUTH_TOKEN` first. v2 free-text path byte-logic unchanged. `py_compile` clean,
  **selftest 10/10**, md5 `a3ed37080aaec940226c98bf0d2c7e04`; installed, service restarted, health answered
  `version:3`, and the endpoint proven to REFUSE without the secret (behaviour, not just liveness — the
  F-38 lesson applied to a deploy check).

**D222 — the 3rd-strike safety rule:** the WABA fires ONLY when a new K_NO_CONTACT save transitions the
cross-day count to EXACTLY 3 — never on historical ≥3 — so a deploy can never mass-fire. Relay missing or
erroring never blocks the save (fail-open, §J.4). Retirement metric unchanged: completion >42 % for five
consecutive clinic days retires the old dropdown (§K.6.6).

### S139.4 — PORTAL HOTFIX (D224) + THE STALE-REPO PROOF
Attendance moved to **`https://attendance.dr-manoj.in`**. The portal tile still pointed at the raw
`http://93.127.195.49:8042`. Found by reading the LIVE `/root/portal/portal.py` (the GitHub copy does not
even contain the tile — **the repo's portal folder is stale against live**; D160's "live is canonical"
proven again, and the S139 git kit must carry the live portal.py). Guarded sed (count==1 asserted), backup
`portal_BACKUP_S139_pre_https.py`, `py_compile`, restart, owner verified the padlock. Watchdog/health-report
reference only the service NAME — unaffected.

### S139.5 — THE CALL-LIFECYCLE AUDIT (owner-requested; an audit finds, it does not fix — D180)
Both directions traced capture → outcome → recording → transcript → verdict → doctor. OUTGOING: healthy
end-to-end except the outcome stage (42 % unfiled / 19 % disagreement — K-1 is now the live cure) and the
verdict stage (no nightly timer). INCOMING: capture ✅ (S138) · missed-call tiles ✅ · **answered incoming
calls still produce no outcome anywhere — the single largest lifecycle hole; cure = K-2, now next in the
build queue** · recordings/transcripts ✅ (Stages 1–2 cover both directions, proven by the 06-Jul verdicts)
· verdict layer still EXCUSES incoming (F-18, now stale).

**THE GAP REGISTER (carried until each closes):**
| Gap | What | Cure | Status |
|---|---|---|---|
| G-1 | Answered incoming calls → no outcome, ever (D183's dominant line) | **K-2** incoming one-tap | next build (Pass 3) |
| G-2 | Cross-day miss counter never built | K-1 D220 | **CLOSED S139** |
| G-3 | Stage-3 verdict has no nightly timer (manual runs only) | arm timer in the A5 pass | open |
| G-4 | D158 claim↔call join can bind an outgoing claim to an earlier incoming call; more exposed now `IN-` rows flow | fix inside A5 | open |
| G-5 | Recording-loss window: Stage 1 nightly vs ~24 h MyOperator link expiry; one bad night = permanent loss (F-21/D200, designed twice, never built) | per-call download, VPS maintenance pass (Pass 5) | open |
| G-6 | F-38 liveness ≠ write-success: nothing surveils the receiver's write path | write-probe, same Pass 5 (pairs with F-37) | open |
Smaller, already on record: F-37 · §G.6 PHI in `client_ref_id` · hand-dialled calls invisible to the gate
(D178, accepted) · F-0 (accepted risk, documented).

**The build order to close everything:** Pass 3 = **K-2** → Pass 4 = **A5** (incoming verdicts + D158 join
+ nightly timer) → Pass 5 = **D200 + F-38 (+F-37)** → Pass 6 = **portal gist tile (D223)**. A3 (seen-today
WABA) slots anywhere — its relay side shipped this session (post_visit already on the allow-list).

### S139.6 — LIVE READS
**QUOTA HEADROOM first real read (09:44 mail): 453 full builds yesterday ≈ 4,983 sheet reads, all devices —
comfortable; the baseline is now recorded.** Cadence (~1 build/2 min overnight) is the open-tab signature
the cache absorbs by design. Noted, honestly: K-1 adds two small per-build reads of the outcomes tab
(counter + completion as separate reads); negligible at 420 rows, logged as a merge-into-one-read
micro-optimisation for a future Block-C pass. Same mail: **Call_Durations today=222** = the 219 backfill
rows + 3 natural post-restart rows — v3.0.1 visibly ingesting; Monday's first weekday incoming call remains
the clean proof. All tabs on schedule. Carried to tonight: **D183 digest count — exactly ONE**.

### S139.7 — DECISIONS MINTED
- **D219** — F-10 cure pattern: opaque data refs (`dref`/`dget`, dedupe-bounded map, [a-z0-9] keys); no
  data value may ever be interpolated into element markup; handler signatures unchanged.
- **D220** — Cross-day miss counter lives in the Callconsole bundle (`missTotals`); WebApp's per-day logic
  untouched (D34). Miss = `no_answer` from either surface; ANY other outcome row for the key resets it.
- **D221** — K-code write mapping: 1–3 write k-codes with explicit settle column; button 4 writes
  `no_answer`; button 5 delegates to `saveFollowupOutcome('problem')`; `source='K'` = the ui marker;
  no new writer to Escalations; no grid widening.
- **D222** — 3rd-strike WABA fires only on the transition to exactly 3, via the EXISTING relay's new
  allow-listed, capped `/wa-send/template`; fail-open toward the save.
- **D223** — Portal "gist" tile registered as Pass 6: one clickable tile on `/portal` opening the doctor's
  consolidated bird's-eye (both-direction calls, unfiled outcomes, verdict disagreements, 3rd strikes,
  pipeline health). Every remaining pass must produce data the tile can read without rework.
- **D224** — Attendance system canonical address is `https://attendance.dr-manoj.in`; portal tile updated.

### S139.8 — OPEN AT CLOSE (feeds Runbook v77 §2)
**A2 (K-1) and A4 (F-10) are DONE and off the backlog.** Monday morning carries the verification load:
F-10 incoming tap · K-1 five buttons on the first real staff call · CALLHOOK weekday status check → Step 4
if clean · first weekday incoming `IN-` row. Ready builds: **K-2** (incoming one-tap — G-1) · **A3**
(seen-today WABA; relay half already live) · **A5** (incoming verdicts + D158 + timer). Standing items
unchanged: CALLHOOK Steps 3–4 · service-account key rotation (highest-standing risk) · AKEY_14 · Docterz
migration decision · Hindi spellings (Track 1) · Notion orphans · panel-tidy · F-37/F-38 (→ Pass 5) ·
Block-C read-merge micro-optimisation (new). Tonight: D183 count.

---

## §S140 SESSION 140 — ALL CALL-LIFECYCLE GAPS CLOSED IN ONE DAY: K-2 LIVE, VERDICT LAYER v2 LIVE, D200 AT-HANGUP PIPELINE LIVE (12 Jul 2026, Sunday; FULL EOS — one Apps Script deploy, five VPS installs)

### S140.1 — WHAT HAPPENED
Phase 0 clean (all 10 canonical docs md5-exact against START_HERE_SESSION_140). Owner's directive: close
ALL remaining call-lifecycle gaps (the S139 register G-1…G-6) **today**, in three passes. AKEY_14 parked
again. The staff-buzz/ntfy notification idea was permanently **DROPPED** (D232) — owner: phones would buzz
all day; "the plan is to make the incoming calls to tracker app, that shd be enough" — **the tracker IS the
surface.** All three passes shipped and were live-verified the same day; Pass-3 install verified live by
the owner before close. The build chat compacted twice; EOS ran in a fresh chat from
`SESSION_140_NOTES_for_EOS.md`.

### S140.2 — PASS 1: K-2 INCOMING ONE-TAP, DEPLOYED AND OWNER-VERIFIED ("all good")
**Design locks (owner decisions):** unknown connected callers are **high-value NEW LEADS**, not skipped —
they get a **7-button** lead set (D225). Button 1 wording: **"Appointment booked"**. Button 7:
**पुराने मरीज़ — नया नंबर** → opens the existing v17 link-patient form via `inIdentity('existing_new_number')`.
**ONE miss-counter rule for both call directions** (D227). **Lead TTL = 3 days** (owner chose 3 over the
proposed 7; D226). जानकारी दे दी (`enquiry_only`) is **NOT terminal** — the lead stays alive in the band.
A lead dies on: `Patient_Master` conversion, a terminal outcome, or 3-day expiry; escalated leads live in
the escalation queue, not the band. 🚨 `surgery_enquiry` = instant doctor push. ⚡ **one-tap defaults ON**
(D228); the toggle is kept only as an escape hatch and is REMOVED once usage >42 % for 5 consecutive clinic
days (watch item).

**Shipped:**
- **`Callconsole.gs` v1.7** — 1,224 lines, md5 `b1d49c6227ba16d0e7a57340a03d1a31`. `cc_outcomeScan_()`:
  **ONE `Followup_Outcomes` read per bundle** → `missTotals` + `kLogged` + `newLeads` — the S139 Block-C
  read-merge micro-optimisation is DONE here (no new tabs, writers, or reads). `cc_patientMap_` memoised
  (`CC_PMAP_MEMO`). `LEAD_TTL_DAYS=3`. Bundle emits `newLeads` (cap 30).
- **`Dashboard.html` v18.28f** — md5 `d528e666b258d1faf958e890e691d68a`, deployed (New version on the
  existing deployment; `PAGE_BUILD` stamp verified live). K-1 buttons on known-patient connected-incoming
  tiles; **7 lead buttons (`L_LABELS`/`L_ORDER`) for unknowns**; `KIN_PAT` map uses the F-10 `dref` pattern
  (no PHI in onclick markup — D219 held); `kIn*` machinery with 10-s undo; **K-path → `saveKOutcome`
  (Callconsole.gs), L-path → the frozen WebApp `saveIncomingOutcome` — D34 respected**; 🌱 **New-leads band
  (`secNewLeads`)** above Today's calls. Iterations b–f: dark-theme colours, `kInSlotR` on Resolved tiles,
  one-tap default ON, unknown callers show a dialable number, `.ac-name` link CSS.
- Missed incoming calls keep the old "Log outcome ▾" flow (F-10 verify Monday).

### S140.3 — PASS 2: VPS VERDICT LAYER v2 (A5 / G-3 / G-4 / F-18), INSTALLED AND LIVE-PROVEN
Base live==repo verified (D188) before edits; backups `.bak_s139` on the VPS.
- **`call_verdict.py` v2** — 1,102 lines, md5 `b7dc12613ae24afee41fdc8bd6910480`, installed.
  `normalise_claim` strips the `in_` prefix, aliases `k_coming`→`coming`. **CLAIM_EQUIV** (D229):
  `k_not_coming` ≡ {`not_interested`,`treatment_elsewhere`,`close_followup`,`no_action`};
  `k_call_again` ≡ {`on_medication`,`out_of_town`,`needs_callback`}; `no_answer` ≡ {`cant_communicate`};
  `problem` ≡ {`escalated`}. **CLAIM_PARTIAL**: `k_call_again` ~ {`coming`,`will_come`}.
  `compare_outcomes` order: normalise → exact → equiv → PARTIAL_PAIRS → CLAIM_PARTIAL. Selftest **42/42**.
- **`verdict_review.py` v2** — 1,550 lines, md5 `13e7618e563202b236659249fdacdeee`, installed.
  **D153 RETIRED (F-18 CLOSED, D230):** an incoming call with no claim but an AI outcome → `SEC_AI_ONLY`
  (a real gap now, not excused); no AI → `SEC_UNCLEAR`; DRAWN kept. **SUSPECT fires only when the claim
  ∈ LEGACY_OUTGOING_SUSPECT** {`coming`,`out_of_town`,`on_medication`,`dikha_chuke`,`close_followup`,
  `not_interested`,`treatment_elsewhere`,`wrong_number`,`asked_not_to_call`} **appears on an incoming
  call.** Review's `normalise_claim` deliberately does NOT alias `k_coming` — aliasing made legitimate K-2
  taps look legacy; caught by selftest. Match rate = all judged claims, both directions. Suspect banner
  reworded (D158 lineage). Selftest **121/121**.
- **Historical catch-up run by the owner: 480 judged, 0 failed.** K-equivalence proven live
  (`coming`↔`coming` Match; `dikha_chuke`↔`close_followup` Partial); **incoming calls judged for the first
  time**; the last row was an incoming `appointment_booked` with `urgent,clinical` flags and no claim —
  exactly the case D153 used to excuse.
- **Cron armed** (G-3 CLOSED): `40 3 * * * /root/wa/venv/bin/python3
  /root/wa/recordings-archive/call_verdict.py >> /root/wa/recordings-archive/verdict_cron.log 2>&1`.
  The owner's paste showed the append command ran TWICE — the dedupe check (`crontab -l | sort | uniq`)
  was folded into the Pass-3 install block and executed there.
- Owner challenged the 03:40 batch vs D200; resolved and accepted (D231): **03:40 = the guaranteed
  floor/sweep; Pass 3 = the fast path.** "Populate my dashboard" = Pass 6 (D223 gist tile), next session.
  D185 read-budget gate satisfied (S139 baseline: 453 builds ≈ 4,983 reads/day).

### S140.4 — PASS 3: D200 AT-HANGUP PIPELINE + G-6 WRITE-PROBE, INSTALLED AND VERIFIED LIVE
Base verification by the owner on the VPS before edits — all three == repo (D188 ✓):
`call_hook_capture.py` `b64aee2b7b0bcc986a72e5e4f176a86c` (v3.0.1, 827 lines) ·
`call_recording_archive.py` `d6b35e0a93863aac0c9869c57bb4dabd` · `call_transcription.py`
`ee8d3e4134ff78d0c01f4e2ecd34a215`. **Key architecture fact:** Stage 1 pulls from the MyOperator
`/search` API directly with `--date` (NOT the nightly `Call_Feed`) → intraday runs see today's calls.
All three stages are `--date`-scoped and idempotent.

- **`call_hook_capture.py` v3.1** — 894 lines, md5 `b8a1a293c54dfb6528e04fdf31f8d3e6`, installed
  (CRITICAL-service protocol: backup → WinSCP → md5 → py_compile → `--selftest` → restart → status →
  `rotate_callhook.sh status`; crontab dedupe check run here). **ONE change:** `pipeline_kick(event_type)`
  right after `raw_log`; kicks only on `call.end`/`call.summary`; writes `<YmdHMSf>_<hex>.kick` json
  `{ts,event,due:0}` to `QUEUE_DIR` (env `CALLHOOK_QUEUE_DIR`, default
  `/root/wa/recordings-archive/pipeline_queue`); wholly try/except **degrade-safe** (proven by the
  selftest's unmakeable-dir check); gate/capture/upsert **byte-identical to v3.0.1**. Selftest **61/61**
  (57 old + 4 new kick checks). Uses `datetime`, not `time` (the hook has no `time` import).
- **`call_pipeline_worker.py`** — 313 lines, md5 `3c8be7f0f6f5960103fb1ed586c48cce`, installed. Systemd-run
  poller (15 s) on `QUEUE_DIR`; **coalesces ALL due kicks under a non-blocking flock** on
  `/root/wa/recordings-archive/pipeline.lock` (kicks consumed only after the lock); runs the three
  **UNCHANGED** stage scripts via subprocess `--date <today IST>`, timeout 1,800 s each, chain stops on a
  stage failure; after any fresh-kick run it schedules **exactly ONE** `retry_*.kick` at +600 s (D200
  backoff; **retries never spawn retries**; dedupe = one retry outstanding max) — D234. **QUIET window
  01:55–04:05 IST** (kicks wait; the nightly batches own that slot) — D233. `--once` and `--selftest`
  flags; logs to stdout/journald. Selftest **14/14**.
- **`call-pipeline.service`** — md5 `273c578cf5ce4b2988d62e47cd0ddeec`. Type=simple,
  WorkingDirectory=`/root/wa/recordings-archive`, ExecStart=`/root/wa/venv/bin/python3
  …/call_pipeline_worker.py`, Restart=always, RestartSec=10, WantedBy=multi-user.target. Enabled `--now`.
- **`callhook_write_probe.py` (G-6/F-38 cure)** — 258 lines, md5 `705bd4a1d82068b1ccc74a2567e2ac67`,
  installed; first manual run **PASS**; daily cron armed: `45 8 * * * /root/wa/venv/bin/python3
  /root/wa/call-hook/callhook_write_probe.py >> /root/wa/call-hook/write_probe.log 2>&1`.
  Reads `CALLHOOK_SECRET` from `/root/wa/.env` (**D176: never printed; URL masked**). POSTs a signed
  synthetic `call.end` (category obd, `client_ref_id PROBE-WRITEPATH`, **NO PHI**) through the PUBLIC url
  `https://followup.dr-manoj.in/mo-callhook` — traversing OLS→gunicorn→gate→gspread. **FAILs** on non-200,
  on the F-38 case (HTTP 200 but the sheet result not in inserted/updated, e.g. "deferred"), and on stale
  read-back (verifies the PROBE row's `captured_at_ist` in `Call_Durations` is <180 s old via gspread;
  `_find_sa_key` pattern copied). One self-overwriting row, invisible to dashboards. Selftest **10/10**.
- **Live proof executed:** console call → kick consumed → the three stages ran → the verdict landed in
  minutes. **Owner confirmation at EOS: "Pass-3 install verified live."**

### S140.5 — GAP REGISTER: ALL CLOSED
| Gap | What it was | Cure | Status |
|---|---|---|---|
| G-1 | Answered incoming calls produced NO outcome anywhere | K-2 (S140 Pass 1) | **CLOSED S140** |
| G-2 | Cross-day miss counter never built | K-1 D220 | CLOSED S139 |
| G-3 | Stage-3 verdict had no nightly timer | 03:40 cron (S140 Pass 2) | **CLOSED S140** |
| G-4 | D158 join defect, exposed as `IN-` rows flow | verdict layer v2 (S140 Pass 2) | **CLOSED S140** |
| G-5 | Recording-loss window (nightly Stage-1 vs 24 h links; F-21/D200 never built) | at-hangup pipeline (S140 Pass 3) | **CLOSED S140** |
| G-6 | F-38 write-path surveillance gap | daily write-probe (S140 Pass 3) | **CLOSED S140** |

**The life of a call now has no known gap in either direction.** F-18 CLOSED (D153 retired, incoming calls
judged). F-21's 106-session loop (per-call download, first written S25) is finally CLOSED by D200's
implementation. **F-37 (health-mail stale watchman window) remains OPEN** — Pass 3 did not touch it.

### S140.6 — DECISIONS MINTED (D225–D234)
- **D225 — New-lead band:** an unknown caller on a CONNECTED incoming call is a high-value **new lead**,
  not a skip; it gets the 7-button lead set (`L_LABELS`/`L_ORDER`; button 7 = पुराने मरीज़ — नया नंबर →
  existing link-patient form). The 🌱 band is derived inside the existing bundle from the **single**
  `Followup_Outcomes` read — no new tabs, writers, or reads. *(12 Jul 2026, S140.)*
- **D226 — Lead lifetime = 3 days.** A lead dies on `Patient_Master` conversion, a terminal outcome, or
  3-day expiry; `enquiry_only` (जानकारी दे दी) is NOT terminal; escalated leads live in the escalation
  queue, not the band. *(12 Jul 2026, S140.)*
- **D227 — ONE miss-counter rule, both call directions.** The D220 counter applies uniformly to incoming
  and outgoing. *(12 Jul 2026, S140.)*
- **D228 — One-tap defaults ON.** The ⚡ toggle is an escape hatch only; REMOVE it once one-tap usage
  >42 % for 5 consecutive clinic days. *(12 Jul 2026, S140.)*
- **D229 — K-era claim tables** (canonical in `call_verdict.py` v2): CLAIM_EQUIV — `k_not_coming` ≡
  {not_interested, treatment_elsewhere, close_followup, no_action}; `k_call_again` ≡ {on_medication,
  out_of_town, needs_callback}; `no_answer` ≡ {cant_communicate}; `problem` ≡ {escalated}. CLAIM_PARTIAL —
  `k_call_again` ~ {coming, will_come}. Compare order: normalise → exact → equiv → PARTIAL_PAIRS →
  CLAIM_PARTIAL. *(12 Jul 2026, S140.)*
- **D230 — D153 RETIRED.** Incoming no-claim + AI outcome = `SEC_AI_ONLY` (a real gap, no longer excused).
  SUSPECT fires only for a legacy-outgoing code on an incoming call; `verdict_review.py` deliberately does
  NOT alias `k_coming` (aliasing made legitimate K-2 taps look legacy — caught by selftest). *(12 Jul 2026,
  S140.)*
- **D231 — The 03:40 verdict cron is the guaranteed floor/sweep; the at-hangup worker is the D200 fast
  path.** Both run; neither replaces the other. *(12 Jul 2026, S140.)*
- **D232 — Staff-buzz/ntfy notification idea DROPPED permanently.** The tracker is the surface. *(12 Jul
  2026, S140.)*
- **D233 — Pipeline QUIET window 01:55–04:05 IST.** Kicks arriving in the window wait; the nightly batches
  own that slot. *(12 Jul 2026, S140.)*
- **D234 — The kick-queue pattern:** the hook writes kicks best-effort (wholly degrade-safe); the worker
  coalesces all due kicks under a non-blocking flock; after any fresh burst it schedules exactly ONE
  +600 s retry; **retries never spawn retries** (one retry outstanding max). *(12 Jul 2026, S140.)*

### S140.7 — LIVE READS / VERIFICATION FACTS
Selftests: hook v3.1 **61/61** · worker **14/14** · probe **10/10** · verdict **42/42** · review
**121/121**. Historical verdict catch-up: **480 judged / 0 failed**. Probe first manual run: **PASS**.
Live pipeline proof: one console call → verdict in minutes. Dashboard stamp v18.28f verified live;
Callconsole v1.7 deployed as a New version on the existing deployment. Crontab dedupe checked (the 03:40
line's double-append caught and corrected in the Pass-3 block).

### S140.8 — OPEN AT CLOSE (feeds Runbook v78 §2)
**Monday 13-Jul is the first live morning — the verification load:** K-1 first real staff tap · F-10
incoming tap on missed calls · first natural `IN-` row through v3.1 (**kick visible in journalctl**) ·
D212 WA tile · D183 digest count tonight = exactly ONE · pipeline live proof on a natural call (call →
verdict in minutes) · write-probe first scheduled PASS line ~08:45 · CALLHOOK rotation Steps 3–4 with
Lokesh (panel update, then clear PREV) · K-1/K-2 usage counter toward the 42 %×5-day toggle-removal rule
(D228). **Ready next: Pass 6 = D223 doctor-portal gist tile (the data now flows).** Carried: Hindi
spellings in `vitals_page.html` · Docterz clinical-data export migration (owner decision pending) ·
AKEY_14 + service-account key rotation (Tier A1, parked) · F-37 · ClickUp parked (D17). Standing rules
touched and in force: D34 (WebApp frozen — the L-path calls the existing frozen endpoint), D160, D172,
D176, D185, D188, D200 (now implemented), D223 (Pass 6 next).


## §S141 SESSION 141 — F-39: EVERY v2 VERDICT WAS LANDING ON ONE ROW; ~500 JUDGED CALLS LOST, RE-JUDGED SAME NIGHT; call_verdict.py v2.1 LIVE; FIRST REAL 550-CALL ANALYSIS DELIVERED; DIGEST LAYER DESIGNED (12–13 Jul 2026, FULL EOS — one VPS file changed)

### §S141.1 F-39 — the append that erased itself (FOUND AND FIXED, evidence chain)
The owner asked for the promised analysis of "the 480 we judged yesterday." The doctor-only sheet held
**63 rows — header + the 62 old v1 verdicts, newest 06-Jul**; the Callback Tracker held nothing either.
Shell history line 956 proved the S140 catch-up was a **real run, no --dry-run** (480 paid Haiku calls);
the pipeline worker's journal showed the same calls re-judged on every kick (8 → 7 → 7 → 7), meaning the
dedupe never saw its own output. `get_all_values()` confirmed no hidden rows (no blank-col-A cloak). The
smoking gun was the append API's own reply during an instrumented probe:
**`updatedRange: 'Call_Verdicts!A61:AI61'`** — Google Sheets' append "table detection" had chosen **row 61,
inside the data**, and every single v2 verdict (catch-up + every worker kick) was written onto that one
range, **each write erasing the previous one**. Collateral: the FIRST v2 overwrite destroyed one original
v1 row that lived at row 61; the diagnostic probe itself (same `append_row` path — that was the point)
overwrote the last surviving v2 row before deleting itself, leaving 61 v1 rows + header. Cost of the bug:
~502 wasted AI calls in one day, and the re-armed 03:40 cron would have re-judged the ENTIRE history every
night forever (no date limit) — caught the same evening, cron disarmed before its first firing.
Why it hid: v2 never bumped `PROMPT_VERSION`, so the lone surviving v2 row wore the v1 label (`v1.0-S128`)
— see F-40. Transcripts/recordings were never at risk (Stage-1/2 persistence is correct).

### §S141.2 The fix — call_verdict.py v2.1 (five surgical edits, proven live)
`call_verdict.py` **v2.1** (1,122 lines, md5 `9cb454e9ec0b9c6609367a3c337d6119`, selftest **42/42**),
built offline with count-asserted string edits on the hash-verified live copy (repo == live confirmed,
`b7dc1261…`): (1) new-verdict writes go to an **explicitly computed row** (`update(range_name=f"A{n}")`),
never append-detection; (2) `next_row` computed ONCE per run from `get_all_values()` then advanced
locally (one extra read per run — D185 respected); (3) grid auto-grows (`add_rows`) before a big
catch-up; (4) the tab-creation header write made explicit too; (5) `PROMPT_VERSION` → `v2.1-S141`.
Install gate passed (md5 + py_compile + selftest). Supervised trial `--limit 5` with the **worker paused**
(one-writer-in-time, D235): 5/5 landed, stamped v2.1-S141, <10 min. Full catch-up: **550 verdict rows**
now on paper — the complete judged history. Worker restarted; **03:40 cron re-armed** (verbatim line).
Idempotence now real: settled calls are skipped, quiet nights cost ₹0.

### §S141.3 F-40 (OPEN, cosmetic) — stale version banners masked F-39
`verdict_review.py` v2 still prints **`verdict_review v1.3 (S124, D155)`** (`BUILD_VERSION` never bumped;
behaviour verified v2 — the D230 incoming-no-claim bucket counted 0 as designed). `call_verdict.py` v2 had
the same defect (`PROMPT_VERSION` stale) — that mislabel is precisely what hid F-39's lone survivor. And
v2.1's in-code comments call the finding "F-21", a number already taken since S131 — the canonical number
is **F-39**; the comment is wrong. Three one-line label fixes, queued for the next VPS-touching session.

### §S141.4 The first real analysis — 550 calls (275 in / 275 out), delivered to the owner
All-time: Verdicts = 289 No-claim-logged · 118 Unclear · 83 Match · 58 Mismatch · 2 Partial. AI outcomes
led by coming 103 · **appointment_booked 92** · info_given 43 · on_medication 37 · will_come 32. 78 rows
carry safety flags (Clinical 61 · Surgery 20 · Complaint 12 · PostOp 11 · Urgent 7 · Conduct 5).
7-day window (206 calls): review drew 180 cards — 26 flagged · 11 mismatch · 108 ai-only · 35 unclear;
match rate on logged outgoing **26/37 = 70%**. Structural insight: the entire 289-row no-claim mass is the
pre-K logging hole (incoming had NO logging mechanism until K-2 shipped in S140) — it should collapse this
week and is the live proof of the K build. Mismatch anatomy: (a) **batch-entry offset clusters** (30-Jun
13:24–13:48 = eight mismatches in 24 min; again 3-Jul midday) — one coaching point; (b) **optimistic
"coming"** (~19 cases where transcript says out_of_town/on_medication); (c) a few serious (7-Jul 8:41
claimed no_answer, patient spoke and is coming). **First K-era mismatch**: 12-Jul 12:29,
in_appointment_booked tapped vs AI enquiry_only — day-one learning curve, catch early. A worst-first
~15-recording doctor list was delivered (safety first: 8-Jul 11:18 …8651 post-op callback; 4-Jul 11:54
…0311 postop+urgent+surgery; 1-Jul 14:18 …2210 "problem"; 7-Jul 16:33 & 11-Jul 8:15 urgent bookings;
conduct ×5 incl …1506 twice on 6-Jul; repeat unlogged callers …6800 ×5, …3486 ×5, …0537 ×4, …6422 ×4).
Filter performance: 550 calls → ~15 recordings needing the doctor. The owner SKIPPED (not dropped) the
in-tracker incoming-ring idea raised this session; it is NOT on the backlog.

### §S141.5 Decisions
- **D235 — Explicit-row writes only; one writer in time.** No clinic script may rely on Sheets append
  "table detection" (`append_row`) for data rows: every data write targets an explicitly computed
  row/range. And no two processes may write the same tab concurrently — the pipeline worker is paused
  for the duration of any manual verdict run. Root cause: F-39.
- **D236 — Digest layer design LOCKED (build next session, BEFORE A8; the D223 tile consumes its
  numbers).** New `daily_digest.py` on the VPS, reader of everything and writer of nothing shared.
  Delivery: EMAIL to the owner's personal Gmail — the address is hardcoded only after the owner confirms
  receipt of the S141 test draft (Gmail draft `r-7726188132642677352`, sent from the clinic account).
  **21:30 IST full digest**: day-in-one-line · worst-first review list with recording links · **2 random
  MATCH spot-checks** (owner-referee answers land in Doctor_Verdicts and count toward the D191 gate) ·
  at most one data-backed improvement suggestion (tech or human). **11:00 IST morning pulse**: ≤5 lines,
  only still-actionable items from the morning follow-up rush; **SILENT when clean**. AI-written summary
  lines for month one (₹1–2/day), then owner re-decides. Weekly digest (Sunday): lead-conversion funnel
  (unknown number → lead → Patient_Master appearance, riding the D226 expiry detector), follow-up visit
  behaviour (said-coming vs actually-visited within 7 days, by agent and by code), staff logging+truth
  scoreboard, judge-health, top-3 suggestions — tables in a sheet tab + email ping.
- **D237 — Judge-calibration path.** One-time **stratified referee set (~40 calls)** spanning every
  outcome code × direction × confidence, drawn from the 550, refereed by the doctor in Verdict_Review;
  THEN the daily 2-random-match drip as maintenance. AI may analyse its own verdicts for internal
  consistency only — machine self-agreement NEVER counts toward the D191 100-card/≥95% gate; only the
  doctor's answers do.

**Next free decision number: D238. Next free finding number: F-41.**

---

## §S142 — SESSION 142 (Mon 13 Jul 2026, clinic morning — FULL EOS; one new VPS file `daily_digest.py`, crond restarted, `.env` +3 lines, Verdict_Review redrawn)

### §S142.1 — D236 DIGEST LAYER: BUILT, INSTALLED, LIVE, DOUBLY VERIFIED
`daily_digest.py` (new, `/root/wa/recordings-archive/`), final **v1.2.1-S142** — 1,045 lines local build,
live md5 **`e6df21cce507bd2d4e60dd9c5644b008`** (byte-identical to the delivered copy), selftest **72/72**
on the VPS interpreter. **Reader of everything, writer of nothing shared**: requests the
`spreadsheets.readonly` scope and contains no Sheets-append call — both are selftested assertions, so the
file physically cannot write a tab (D235 by construction). Reads `Call_Verdicts` + `Doctor_Verdicts`
(audit book) and `Call_Durations` + `Followup_Outcomes` + `Call_Transcripts` (tracker). **Delivery:**
clinic Gmail → owner's personal Gmail via SMTP:587; three `DIGEST_` lines appended to `/root/wa/.env`,
the 16-char app password copied **silently** from `/root/att_config.py` (value never displayed — D176).
**Crons armed:** `0 11 * * *` pulse · `30 21 * * *` digest, both `>> digest_cron.log`. **Proof chain:**
`--test` mail received on the owner's phone → live `--pulse --dry-run` on real data → cron-line grep = 2
→ live pulse received. The dry-run earned its keep: v1.0's first run against live data exposed three
defects (broken judged↔pending join — verdict `Join Key` is `mobile10_epochSECONDS` while
`client_ref_id` is `mobile10-epoch+hex`; text-sorted unpadded times putting 10:00 before 8:58; duplicate
duration rows) → **v1.1** fixed all three (phone+epoch ≤300 s join, IN- fallback phone+≤6 min window,
dedupe keep-last, `pad_time`). **Owner amendment (D238): the 11:00 pulse ALWAYS sends and opens with ALL
of the morning's calls** — judged first (time · dir · patient · duration · staff tap · AI outcome ·
verdict), then pending; then ≤5 Needs-Attention lines. The 21:30 digest: AI-written day-in-one-line +
one suggestion from **aggregate counts only** (no names/numbers/transcripts leave the sheet; Haiku;
computed fallback if the key is absent or the call fails), the day's numbers, worst-first listen list
with recording links, **2 seeded-random MATCH spot-checks** (deterministic per day), D191 progress
footer. Weekly Sunday section: designed, NOT built (rides D226 — later VPS touch).

### §S142.2 — 🔴 F-41 FOUND, FIXED, CANARY-PROVEN: crond ran on UTC since 16 Jun
The 11:00 pulse did not arrive; `digest_cron.log` did not exist. Diagnosis chain: OS timezone correct
(`timedatectl` = Asia/Kolkata) but `crond` `ActiveEnterTimestamp` = **16 Jun** — a daemon keeps the
timezone it was born with, and it was born before the box was set to IST. Proof from artefacts: the
"03:40" verdict sweep's log file is stamped **09:10 IST** (= 03:40 UTC); the S140 08:45 write-probe's
log **did not exist** — the probe NEVER fired on schedule (its recorded PASS was the manual run);
`/var/log/cron`'s own timestamps were UTC wearing local dress (the F-40 camouflage species, at OS
level). The at-hangup worker masked everything: verdicts kept landing in minutes, so a nightly sweep
running mid-morning went unnoticed for weeks. **Cure:** `systemctl restart crond` (+rsyslog); **proof by
canary, not by the restart message** (D235 discipline): a temporary `* * * * *` job wrote three
IST-minute-boundary lines (11:17/11:18/11:19), then was removed; crond reborn 11:16:58 IST. The pulse
was fired manually the same minute so the owner's first pulse still arrived in the morning.
**Consequences:** tonight 21:30 = the first correctly-clocked cron digest; tomorrow 08:45 = the
write-probe's first real scheduled run; the 03:40 sweep returns to actual night.

### §S142.3 — Unjudged-call reason classifier (owner-directed, built same day → v1.2/v1.2.1)
Owner: *"make a system to automatically analyse such calls and assign a reason for not being judged."*
Designed from the live tab, not guesses: `customer_result` (connected/answered/not_answered) +
`customer_talk_duration` are the truth columns. Every pending call in the pulse now carries one of:
**not answered** · **too short to judge (Ns talk)** · **in pipeline** (≤30 min old) · **transcribed —
verdict due** (transcript join found: phone+epoch ≤300 s, or phone+≤6 min for IN- rows) ·
**⚠ talked Ns, no recording** (connected, ≥15 s talk, >30 min, no transcript) — the last is a
**lost-conversation detector** that escalates into Needs Attention and, when any exist, prefixes the
21:30 digest's suggestion line. v1.2.1 (live md5 above): ⚠ alerts sort FIRST in Needs Attention so the
5-line cap can never cut them (the cap had cut one on the first live send); attention-line times padded.
Constants: `MIN_TALK_S=15`, `PIPELINE_GRACE_MIN=30`. Flag cells verified as **"YES"** (not "TRUE") —
`truthy_flag` already accepted YES; only the session's ad-hoc analysis had guessed and was corrected.

### §S142.4 — 🔴 F-42 (OPEN): connected incoming calls with real talk and NO recording
The classifier's **first production run** caught it: **8287590248** (09:37 + 09:38; 40 s + 27 s talk)
and **6392367128** (11:07 + 11:09; 39 s + 101 s talk) — all four rows `status=missed` **+**
`customer_result=connected`, and no recording or transcript ever appeared (verified in
`Call_Recordings`/`Call_Transcripts`, hours later). The incoming calls that DID get judged that morning
lack this status/result combination. **Working hypothesis:** answered on a leg MyOperator does not
record (e.g., picked up directly on the reception mobile rather than through the recorded route) — if
true, no retry will ever find a recording and the fix is panel-side. Investigation = S143 (hook logs,
MyOperator Call API by session_id, possibly Lokesh). Until then these calls are *visible and labelled*
in every pulse instead of silently unjudged.

### §S142.5 — D237 REFEREE SET BUILT; refereeing parked on Option B (owner)
From the (now) 566 verdict rows — S141's 550 + the morning's 16, buckets reconciled against the S141
record — a **seeded, reproducible stratified set of 41 calls** (seed `D237-S142`): one seat per
non-empty (direction × AI-outcome × verdict) cell (38) + 2 confidence/verdict balance seats + flag
seats; covers **all 18 outcome codes, both directions, all 3 confidence levels (19 high / 17 med /
4 low), all 6 safety-flag types, 12 mismatches**, 29-Jun → 13-Jul. Delivered as
`D237_Referee_Set_S142.xlsx` (41 rows, listen links, red = mismatch, amber = flagged). Enabling redraw:
`verdict_review.py --days 21` → **8,845 rows / 378 cards** — sheet row-count verified equal to the
script's claim (the F-39 lesson, honoured; an earlier check against a mid-write export was correctly
distrusted and re-run). **Gap found:** only 28/41 picks are answerable today — the ai-only section caps
at 120 cards (6 picks dropped) and **MATCH calls render as lines with no answer cell** (D155-era
design), which also means **the D236 daily 2-spot-checks currently have no landing cell**. Owner chose
**Option B**: the whole 41-card sitting waits for the S143 `verdict_review.py` enhancement (force-draw
full cards for a supplied key list). The xlsx and seed stay valid.

### §S142.6 — Also this session
Live-verification items from the Monday list, proven incidentally by the pulse data: **K-1/K-2 staff
taps live in production** (a morning full of `k_coming`/`k_not_coming` claims, first K-era incoming
mismatches visible); **verdict-in-minutes on natural calls proven twice** (9557703250 judged between
two pulse snapshots). `verdict_review` live banner seen printing "v1.3 (S124, D155)" — **F-40 confirmed
live, still unfixed** (the day filled; rides S143). **Repo drift confirmed by hash:** the repo's
`call_verdict.py` is still **v1.0-S128** (md5 `b7dc12613ae24afee41fdc8bd6910480`) — the S141 v2.1 commit
was never pushed; `daily_digest.py` has no repo copy yet. Both commits owed.

### §S142.7 — Decisions
- **D238 — The 11:00 pulse always sends and opens with the complete list of the morning's calls**
  (owner amendment to D236's silent-when-clean design; the actionable section stays capped at 5 lines
  with ⚠ lost-conversation alerts always first).
- **D239 — Flag Investigator approved (S143 build, paired with the F-42 investigation).** For every
  ⚠ lost-conversation flag: (1) ask MyOperator's Call API by session_id whether a recording exists —
  if YES, self-heal by re-triggering the existing download→transcribe→judge chain; if NO, label the
  reason ("answered outside the recorded route") and count the pattern; (2) check the hook logs for
  whether the kick fired; (3) write findings to a VPS results file that the digest READS (digest stays
  a pure reader; the investigator is sole writer of its own file; no new tabs; ₹0). Owner-approved
  defaults: self-heal ON · every 30 min 09:00–20:00 · ≥3 provider-never-recorded in a week → the digest
  tells the owner to raise it with Lokesh.

**Next free decision number: D240. Next free finding number: F-43.**

---

**END OF MASTER KB v1.68. §S142 is the last section, and §S142.7 is its last subsection. §S141 sits immediately above it. The CHANGELOG's newest entry is `v1.68`. If any of these is absent, this file is truncated and must not be used as canonical.**