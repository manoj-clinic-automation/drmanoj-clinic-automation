# KB HISTORY ARCHIVE — v1.16 (Tier 1 · append-only · out of the session loop)

**Dr. Manoj Agarwal Clinic · Bareilly · created S147, carried VERBATIM from Clinic_Master_KB_SystemsRegister v1.72 (md5 27b72639…).**

> This file holds the project's HISTORY: every session narrative (§S…) and every full-text decision block, unaltered. Authority on *what happened*. For *what is true now*, read the **KB Register v2.5** (Tier 0). Opened on demand only. (D247)

> The v1.72 end-marker is preserved at the foot of this file as a historical truncation-proof.

---

# Clinic Master KB / Systems Register — v1.72 (CONSOLIDATED)

**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **v1.72 is a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything in v1.71 plus **§S146 (Session 146, FULL EOS — one live VPS file replaced): B1 — the 21:30 digest now READS `flag_investigator_results.json` and quotes the Flag Investigator's rolling recording-gap split (never_recorded vs missed_no_conversation) in a new "Recording health" section — ONE source of truth, no recompute; FAIL-LOUD on a missing/unreadable/stale (>20 h) results file (the numbers are withheld and said so, never a silent zero). `daily_digest.py` v1.4 → v1.5 (md5 `0a4ee35b5fb7fbc0570efe3bc0cdde88`, 83/83 selftest, +8 checks), installed WinSCP → md5 match → py_compile → selftest → live `--digest --dry-run` clean (Recording health printed "0 genuine · N missed" on real data); no cron change; ADDITIVE ONLY (the 11:00 pulse and the same-day per-call alert are untouched); read-only, writes nothing (D236); no `append_row` (D235). 🧭 THE THREE-PRODUCT LINEAGE NAMED (D246): Followup Tracker (clinic PC, offline — SOURCE) → Callback Tracker (Sheet + Console, VPS — SYSTEM OF RECORD, Product A) → Call Intelligence (`recordings-archive`, VPS — ANALYTICS, Product B); three seams, two already contracts (Callback→Intelligence; Investigator→Digest, hardened by B1), the Followup→Callback seam the one still to name (where the Docterz-export migration lives). B2 clinical windows CAPTURED + parked for the #10 build (outgoing follow-ups: LEARN the return window per diagnosis from ~5 weeks; incoming leads + missed-call callbacks: flat 3-day). Housekeeping: the v1.71 CHANGELOG entry was absent (the end-marker promised it) — backfilled here. Decision D246.**
> *(previous consolidation note)* **v1.71 is a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything in v1.70 plus **§S145 (Session 145, FULL EOS — two live VPS files replaced; the AI Verdict Layer Master written): F-44 RAISED+FIXED+PROVEN — the recording-gap detectors (`flag_investigator.py`, `daily_digest.py`) had mislabelled MISSED calls as "never recorded" by reading talk-seconds instead of MyOperator's top-level `status`; a missed call's ring/hold time was counted as a lost recording. `flag_investigator.py` v1.2 (md5 `a9baa6ca22055bb188d5c65b93c47ba1`, 51/51 selftest) and `daily_digest.py` v1.4 (`f7e05ed2a79670667fda170f3b70b9d1`, 75/75 selftest) fix it to key off `status` (D244). 🟢 THE "42 NEVER-RECORDED" COLLAPSED 42 → 0 on re-baseline; the backup proved 42/42 were `missed (status 2)`, zero genuine — so the standing "take the 42 to Lokesh" action is VOID (a false alarm), correcting §S144.2's reading of the 42 as provider-side loss. THE AI VERDICT LAYER MASTER WAS WRITTEN (`AI_Verdict_Layer_Master_v1_S145.md`, D245, which CLOSES D242) — canonical; it SUPERSEDES `AI_Review_Layer_Design_Spec_v1_1_S131.md` and RETIRES `AI_Verdict_Layer_Master_CHARTER_S143.md`. Diagnostics Spec → v2.3; Fault→Action Register unchanged. Decisions D244–D245.**
> *(previous consolidation note)* **v1.70 is a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything in v1.69 plus **§S144 (Session 144, FULL EOS — one new live VPS file + two new cron lines): BUILD 2 COMPLETE END-TO-END. `flag_investigator.py` v1.1 (D239) is LIVE and cron-armed (`*/30 9-19 * * *` + `0 20 * * *`, IST). It reads `Call_Durations`, asks MyOperator `/search` whether each lost conversation's recording exists provider-side (a call has audio ONLY when status "1" + a non-empty filename), SELF-HEALS same-day recoverables by dropping one ordinary pipeline kick, LABELS+COUNTS never-recorded calls, and writes `flag_investigator_results.json` (the file the digest will read). One-writer rule honoured — it writes only its own file, never `Call_Durations`/`Call_Recordings`. 🔴 F-42 QUANTIFIED: 42 connected calls in a rolling 7 days produced NO recording provider-side (far past the D239 3/week threshold → raise with Lokesh); plus 5 recoverable HEALED same-day (recordings landed in `Call_Recordings`, proven end-to-end) and 10 recoverable-pastdate surfaced with re-run commands (documented v1 boundary). 🔴 F-43 RAISED+FIXED same session: v1 gated the heal-kick on the outcome TRANSITION into recoverable, so a `--no-heal` run (or a failed kick) silently consumed the transition and suppressed the real kick forever; fixed to gate on the durable per-call `kicked` flag (v1.1). D160 repo==live verified for all four S143 files. D242 minted (charter Master, gated to Investigator-stable ~S145–146). D243 minted (the #10 two-pipeline conversion model). Decisions D242–D243.**
> *(previous consolidation note)* **v1.69 was a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything in v1.68 plus **§S143 (Session 143, FULL EOS — three live VPS files replaced, one one-off tool, one data file, one new cron): BUILD 1 COMPLETE END-TO-END. `verdict_review.py` v3 (D240): forced-card band — any supplied Join Key draws a FULL answer card above every section, cap-exempt, MATCH included; answered keys collapse to ✓ lines and are never asked twice; the daily 2 spot-checks are picked and MARKED by this script alone (ONE DECIDER); a 21:00 daily redraw cron is armed. `daily_digest.py` v1.3: its own spot-picker DELETED — it reads the tab's 'Today's spot-checks' line; the live dry-run proved digest pair == tab pair. F-40 CLOSED (four call_verdict 'F-21' mislabels + the verdict_review banner). `make_force_keys.py` resolved all 41 D237 referee keys after its own dry-run caught the unpadded-hour trap (v1.0: 20/41 missing, every one an hour <10) — v1.1 compares times numerically. THE GROUND-TRUTH LEDGER IS ALIVE: the owner refereed 18/41 the same afternoon; harvest round-trip proven; upsert proven idempotent (0 new / 0 updated / 18 unchanged); Doctor_Verdicts = 18 rows; raw doctor↔AI agreement 16/18 (89%); on all 5 staff-vs-AI disagreement cards the doctor sided WITH the AI. 🔴 F-42 ESCALATED: 6 lost conversations counted on 13-Jul alone (D239 threshold: 3/week). D241: the 14-point Insight Harvest Register minted; five insights designated the D223 gist tile's feeders. Repo drift closed by hash. Decisions D240–D241.**
\n> *(previous consolidation note)* **v1.68 is a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything in v1.67 plus **§S142 (Session 142, FULL EOS — one new VPS file, one emergency system fix): the D236 DIGEST LAYER BUILT AND LIVE (`daily_digest.py` v1.2.1-S142, read-only by construction, 72/72 selftest; 11:00 pulse + 21:30 digest crons armed; both emails proven on the owner's phone). 🔴 F-41 FOUND, FIXED, CANARY-PROVEN the same morning: crond had run on UTC since 16 Jun — every cron ever armed fired 5h30 late; the 08:45 write-probe had NEVER fired. Owner-directed same-day v1.2: every unjudged call now carries an automatic reason; the lost-conversation detector's FIRST run caught 🔴 F-42 (connected incoming calls with talk but no recording — open). D237 stratified 41-call referee set built and delivered; Verdict_Review redrawn to 8,845 rows / 378 cards; refereeing waits (owner: Option B) for the S143 verdict_review enhancement. Flag Investigator designed and approved (D239). Decisions D238–D239.**\n\n> *(previous consolidation note)* **v1.67 is a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything in v1.66 plus **§S141 (Session 141, FULL EOS — one VPS file changed): F-39 found and fixed the same night — Sheets append-detection was writing every v2 verdict onto row 61, erasing its predecessor; ~502 wasted AI calls; `call_verdict.py` v2.1 (explicit-row writes) installed, 5/5 supervised trial, full re-judge to 550 rows, cron re-armed. F-40 raised (stale version banners). First real 550-call analysis delivered. Digest layer designed (D236) and calibration path locked (D237). Decisions D235–D237.**\n\n> *(previous consolidation note)* **v1.66 is a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything in v1.65 plus **§S140 (Session 140, FULL EOS — one Apps Script deploy, five VPS installs, all live-verified): the owner-directed close-ALL-call-lifecycle-gaps day, three passes in one Sunday. Pass 1: K-2 incoming one-tap LIVE (Dashboard v18.28f + Callconsole v1.7) — unknown connected callers become NEW LEADS with a 7-button set and a 🌱 New-leads band (3-day TTL, D226). Pass 2: the VPS verdict layer v2 LIVE (`call_verdict.py` v2 + `verdict_review.py` v2) — K-era claim equivalence, D153 RETIRED (F-18 closed), the 03:40 nightly cron armed, 480 historical calls judged with 0 failures. Pass 3: the D200 at-hangup pipeline LIVE (`call_hook_capture.py` v3.1 kick-queue + `call-pipeline.service` worker) and the G-6/F-38 daily write-probe armed. The entire S139 gap register G-1–G-6 is CLOSED. Decisions D225–D234.**
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

## §S143 — SESSION 143 (Mon 13 Jul 2026, afternoon — FULL EOS; three live VPS files replaced, one one-off tool + one data file added, one cron armed)

### §S143.1 — D240: `verdict_review.py` v3 — the forced-card band, built and proven end-to-end the same afternoon
Full-file replacement on the hash-verified live v2 (`13e7618e563202b236659249fdacdeee`; repo==live proven
before a line was touched — D160/D188). **v3: 1,837 lines, live md5 `280eb2cef9295d89f30c7b84d4c94adb`,
selftest 144/144 on the VPS interpreter** (all 121 v2 checks preserved + 23 new D240 checks). The band: any
Join Key supplied via `/root/wa/recordings-archive/force_keys.txt` (one per line, `#` comments, FILE ORDER
kept) or `--force-keys` draws a **FULL answer card in section 0, above FLAGGED**, exempt from
`MAX_CARDS_PER_SECTION` by construction (it never passes through `by_section`), **MATCH verdicts
included** — curing the v2 gap that left 13/41 referee calls and the daily spot-checks with no answer cell.
Forced keys resolve against ALL rows, not the window (a referee key may pre-date it). **Answered keys**
(outcome present in `Doctor_Verdicts` or the current harvest) collapse to a one-line `✓ answered` entry with
the doctor's verdict shown and NO editable cell — the band shrinks as the sitting progresses and nothing is
ever asked twice. A forced key is excluded from its home section (one call, one answer cell — the harvest
token map cannot tolerate duplicates). Missing keys are NAMED — opaque tokens on the exportable tab, full
keys in the run log — never silently dropped. Scenario counts and the match rate are computed from the
unfiltered window rows, so band placement cannot move the accuracy number (the same rule that protects it
from flag placement). Harvest-before-redraw, one-writer-per-table, the token scheme, and ₹0 are unchanged.
Banner now honestly `verdict_review v3 (S143, D240)`. Live proof chain: dry-run without a force file (0+2,
answer cells 390 = 388+2), dry-run with the file (41+2, **answer cells 413 = 370+43 exactly as predicted**,
dedupe deltas reconciled per section), then the real redraw.

### §S143.2 — The daily spot-checks have ONE DECIDER (the S143 architecture choice inside D240)
`pick_spotchecks`: up to 2 clean-MATCH cards per day (`placement == match`, so flagged and suspect rows —
which already draw cards — can never double-draw; never a key already answered; never a key already forced),
date-seeded, drawn at the END of the band under a `★ TODAY'S SPOT-CHECK` banner. The script that draws the
cards is the script that picks them; it writes a summary row labelled **`Today's spot-checks`** (masked
number · date · time · outcome), and every consumer READS that row. The rejected alternative — two scripts
computing "the same" seeded pick from pools read at different times of day — diverges silently. **A
`0 21 * * *` cron now redraws daily** (harvests the day's answers, refreshes the band, picks tomorrow's
pair) so the 21:30 digest always reads a fresh tab; 21:00 was chosen because an answer typed DURING a
redraw's harvest-to-delete window would be lost — **the redraw must never run while the doctor is
mid-sitting**. Cron line verified by `crontab -l`; its first scheduled firing (tonight 21:00, log
`verdict_review_cron.log`) joins the S144 proof list.

### §S143.3 — `make_force_keys.py` (v1.1, one-off, read-only) and the unpadded-hour trap, caught by its own dry-run
The D237 xlsx carries date/time/number but NO Join Keys (keys are `phone_epochSECONDS`; the workbook has
minutes). A 193-line one-off (md5 `9b44831a0a2a2003fac5c4901f7da35c`, selftest 11/11) resolves the 41
referee triples against the live `Call_Verdicts` under an explicitly `spreadsheets.readonly` scope and
writes `force_keys.txt` — a local VPS file, no Sheet touched. Two honesty rules, both selftested: a call it
cannot find is NAMED, never guessed; two calls in one minute are AMBIGUOUS, never guessed. **v1.0's live
dry-run resolved only 21/41 — and every missing call had an hour before 10.** `Call_Verdicts` stores
UNPADDED hours (`9:06`); Excel had dressed the workbook's times as `09:06`; the text-prefix match failed on
every single-digit hour — the S142 unpadded-time lesson recurring in a new file within 24 hours. v1.1
compares times as minutes-since-midnight, never as text; **41/41 resolved**, `force_keys.txt` written,
count proven by `grep -cv '^#'` = 41 (the artefact, not the success message — F-41 discipline).

### §S143.4 — F-40 CLOSED (and the record corrected: it was four mislabels, not three)
`call_verdict.py`: the runbook said "three one-liners"; the artefact showed **four** `F-21` labels (header
L7 + comments L709/L1034/L1083). All four now read F-39. Comment-only change: 1,122 lines unchanged,
selftest 42/42 unchanged, prompt and logic byte-identical; new live md5
**`539ea68fb4ce99f0029fdbb53bbf8ebe`**. With the v3 banner (§S143.1), **F-40 is closed in the artefacts** —
every version string and finding label in the verdict layer now tells the truth.

### §S143.5 — `daily_digest.py` v1.3: the second spot-picker is DELETED, not deprecated
`pick_spot_checks` (and its `random` import) removed outright; `find_spotcheck_line` reads the tab's
labelled summary row via a `Verdict_Review!A1:B30` read inside `collect()` (now a 5-tuple; both call sites
updated). Line present → the email carries it verbatim and points at the ★ cards; line absent (the 21:00
redraw not yet run) → the email honestly points at the top band and **invents nothing** — both paths
selftested. **Live md5 `63a558d2a73dc5ec22ea8bb772869353`, selftest 74/74** (72 v1.2.1 checks − 4 picker
tests + 6 new), the two by-construction guarantees re-proven (readonly scope + zero append calls). The
install's live `--digest --dry-run` closed the loop: **the email's pair equalled the tab's pair**
(`…2932 on_medication` · `…4081 coming`) and the footer already reads "Doctor referee progress: 18 / 100
cards (D191)".

### §S143.6 — THE GROUND-TRUTH LEDGER IS ALIVE: 18 rows, 89% raw agreement, and the AI's mismatches confirmed
The owner began the referee sitting the hour the band went live. Verified from a fresh xlsx export of the
audit book (never from memory — D172): **`Doctor_Verdicts` = 18 data rows, 18 unique keys, every row
carrying an outcome, each stamped `verdict_review v3 (S143, D240)`**; the band redrew to 18 `✓ answered`
lines + 23 open referee cards + 2 spot-checks (25 open; 396 answer cells — every count reconciled exactly
against the run log). The harvest **upsert is proven idempotent**: a second run reported
`0 new, 0 updated, 18 unchanged` — the property F-39 taught this project to demand of every writer. **First
calibration numbers ever: 16/18 doctor↔AI agreement (89% raw).** The two differs are both benign classes:
the known dikha_chuke↔close_followup soft pair, and one case where the AI erred toward MORE action
(needs_callback vs no_action) — the safe direction. **On all five cards where staff and the AI disagreed,
the doctor sided with the AI** (will_come vs dikha_chuke · wrong_number vs not_interested ·
appointment_booked vs coming · cant_communicate vs coming · on_medication vs coming): the judge's mismatch
findings are signal, not noise. D191 Phase-2 gate progress: **18/100 refereed.**

### §S143.7 — 🔴 F-42 ESCALATED BY THE DATA: six lost conversations in ONE day
The v1.3 dry-run's suggestion line carried **6 connected-no-recording calls for 13-Jul alone**: the two
known pairs (8287590248 ×2 · 6392367128 ×2) plus two NEW same-afternoon events — 13:21 `…8333` (33 s) and
14:54 `1206138695` (19 s; the non-standard number shape is itself worth a look). The D239 escalation
threshold is ≥3 provider-never-recorded per WEEK; one day sits at six candidates. **Build 2 (Flag
Investigator + F-42 investigation) is Session 144's first build**, recon defined: (a) does `Call_Durations`
carry the MyOperator session_id or must it derive from `client_ref_id`; (b) the exact Call API search shape
from `MyOperator_Call_API_Master_Reference_23_june_.md`. All D239 defaults stand (self-heal ON · every
30 min 09:00–20:00 · results file the digest reads · Lokesh line at threshold).

### §S143.8 — Housekeeping and record corrections
**Repo drift CLOSED by hash** (owner committed; verified `call_verdict.py` = `9cb454e9…`, `daily_digest.py`
= `e6df21cce…`, S142 docs present) — and immediately re-owed for the three S143 versions. **A-proofs parked
to S144 morning** per owner: 21:30 digest (first cron-fired; spam-check once; suggestion line should carry
the F-42 calls), 08:45 write-probe log, 11:00 pulse — now joined by the 21:00 `verdict_review_cron.log`.
**New standing item: the VPS venv runs Python 3.9 (EOL)** — google-auth/api-core FutureWarnings on every
run; harmless today; the upgrade must be scheduled deliberately (venv rebuild = every pipeline retested);
Tier-C housekeeping. Owner confirmed F-37 window, repo naming tidy, K toggle-removal watch, and the Docterz
export migration are UNBLOCKED (Docterz decision itself still open). The Umbrella's END marker was found
stale ("v1.51" on a v1.54 file — the S131 stale-marker class) and is corrected in v1.55. The KB's own
line-count convention re-learned during this EOS: the file's last line is unterminated, so `wc -l` = 4,073
while splitlines = 4,074 — both true of the same artefact; counts below state their convention.

### DECISIONS D240–D241 — FULL TEXT
- **D240** `verdict_review.py` v3 — FORCED CARDS + ONE-DECIDER SPOT-CHECKS (parents D155/D237/D191).
  (a) A forced-key list (`force_keys.txt`, file order, `#` comments; `--force-keys` additive; `--force-file`
  explicit, error if named and absent) draws FULL answer cards in a band ABOVE all sections, cap-exempt by
  construction, MATCH included, resolved against all rows not the window. (b) Answered keys collapse to `✓`
  lines — a sitting is resumable across days and nothing is asked twice. (c) One call, one answer cell:
  forced keys are excluded from their home sections. (d) Missing keys: opaque tokens on the tab, full keys
  in the log, never silent. (e) The daily 2 spot-checks are picked, marked (★), and summarised (the
  `Today's spot-checks` row) by verdict_review ALONE; every consumer reads the tab (ONE DECIDER). (f) The
  `0 21 * * *` daily redraw cron is part of this decision — and a redraw must never run during an active
  sitting (harvest-to-delete window). (g) Clinic times are compared NUMERICALLY, never as text — the
  twice-learned unpadded-hour rule, now standing for every script. Counts and the match rate remain
  placement-independent. Implemented and live-proven S143.
- **D241** INSIGHT HARVEST REGISTER (parent D223; owner-approved list, S143). Fourteen analyses the
  accumulated call + Docterz data can already support, recorded as the roadmap that FILLS the D223 gist
  tile. **Call-data-only: (1)** best hour/day to call (answer rate by slot); **(2)** retry-value curve →
  an evidence-based stop-after-N rule; **(3)** minimum talk-duration for a real conversation; **(4)**
  per-agent accuracy/outcome profile (coach by recording, not by number — the D191 ethos); **(5)**
  repeat-caller friction map → IVR/WABA auto-answers; **(6)** K-2 new-lead conversion inside the 3-day TTL;
  **(7)** speed-to-callback vs outcome; **(8)** reputation early-warning trend (asked_not_to_call · conduct
  · complaint flags, weekly); **(9)** pipeline-health scorecard (empty transcripts · F-42-class losses ·
  wrong numbers, weekly rates). **Docterz-join-dependent (the strongest argument for closing the
  export-migration decision): (10)** said-coming vs actually-came — THE conversion number and the honest
  denominator for everything else; **(11)** diagnosis-wise return compliance; **(12)** the silent
  surgical-advice pipeline (flag/estimate then vanished — a worst-first recall list, directly revenue- and
  outcome-linked); **(13)** no-show risk profile → a day-before confirmation call; **(14)** programme ROI in
  rupees. **GIST-TILE FEEDERS (the five that fill D223): #10 conversion · #9 pipeline health · #6 lead
  conversion · #8 reputation trend · #14 ROI** — the bird's-eye answers to "is it working · is it healthy ·
  is it growing · is anyone unhappy · what is it worth". Build priority when scheduled: 10 → 1 → 2 → 12.
  Register only; nothing is scheduled by this decision.

**Next free decision number: D242. Next free finding number: F-43.**


---

## §S144 — BUILD 2 LIVE: THE FLAG INVESTIGATOR (D239); F-42 QUANTIFIED; F-43 FOUND & FIXED

Session 144 built, installed, verified and armed the D239 Flag Investigator end-to-end, and in doing so turned the open F-42 fault into a hard number. It also settled the domain model for the register's most valuable analysis (#10). One new live VPS file (`flag_investigator.py` v1.1), two new cron lines, one new results file. No existing live file was rebuilt.

### §S144.1 — `flag_investigator.py` v1.1 (LIVE)
- **Path:** `/root/wa/recordings-archive/flag_investigator.py` · **md5** `0863b854860615f5198a6101fef59fe4` · **selftest 45/45** · run with `/root/wa/venv/bin/python3`.
- **What it does, every 30 min in clinic hours:** reads `Call_Durations` for lost conversations (connected, real talk time, empty `recording_filename`, past a 25-min grace so it does not fight the D200 retry); for each, asks MyOperator `/search` whether the recording exists provider-side; then acts.
- **Diagnosis is provider ground truth, not inference:** a call has audio ONLY when the log's status is `"1"` AND `filename` is non-empty. The `/search` call is the JSON-body POST copied verbatim from the running `call_recording_archive.py` (the proven method on this account — D172), never the doc's query-string variant.
- **Three outcomes:** `recoverable` (recording exists, pipeline missed it) → self-heal; `never_recorded` (log present, filename empty) → label + count; `no_provider_log` (no matching log) → anomaly, surfaced not counted.
- **Self-heal = one ordinary pipeline kick** (today only), the exact kick shape the call-hook drops at hang-up; the worker then re-runs today's archive→transcribe→verdict idempotently. Gated on the durable per-call `kicked` flag (see F-43), so a call is kicked at most once.
- **v1 boundary (documented, not hidden):** a `recoverable` call from an EARLIER day is reported as `recoverable_pastdate` with its exact re-run command (`call_recording_archive.py --date D` then `call_verdict.py --date D`) rather than auto-run — lifting this to full auto-heal is a small v1.1 (a dated kick + one worker tweak).
- **One-writer rule (D235/F-3/F-39):** it writes ONLY `flag_investigator_results.json`; it never writes `Call_Durations` (owner: the call-hook) or `Call_Recordings` (owner: the archiver). Idempotent — running twice yields the same file and no double-kick.
- **Escalation:** `escalate_lokesh` flag flips true when never-recorded ≥ 3 in a rolling 7 days (D239 default). The results file is what the digest will read.
- **Cron armed:** `*/30 9-19 * * *` and `0 20 * * *` (together = :00 and :30 through 20:00 inclusive), IST. crond confirmed active, clock confirmed Asia/Kolkata (+0530) — the F-41 fix holds. Log-proof (an IST-stamped scheduled run in `flag_investigator.log`) is owed at the first tick (20:00 13-Jul / 09:00 14-Jul), per the F-41 discipline: the artefact proves the schedule, not the install message.

### §S144.2 — 🔴 F-42 QUANTIFIED (provider-side loss, at scale)
The first live run diagnosed the last 7 days: **42 connected calls produced NO recording on MyOperator's side** — the tool found each in MyOperator's own logs with an empty filename. This is not a pipeline bug on our side; it is the provider not recording. Against the D239 threshold of 3/week, 42 is an order of magnitude over. This is the finding the whole build existed to produce, and **the number to raise with Lokesh** (owner's action; a per-day factual note can be drafted on request — patient numbers stay on the clinic side, never in chat). Alongside: **5 recoverable calls healed same-day** (kick → worker → recordings landed in `Call_Recordings`, verified against the manifest tab, proven end-to-end) and **10 recoverable-pastdate** surfaced for later batch heal. Zero `no_provider_log` — every candidate matched a provider log, so the matcher is sound; "never-recorded" always means *found the call, filename empty*, and the matcher prefers a recorded sibling leg, so the 42 is conservative.

### §S144.3 — 🔴 F-43 (raised + fixed same session): the kick-gate bug
v1 gated the self-heal kick on the *outcome transition* into `recoverable`. During install the first real run dropped **no** kick — because an earlier `--no-heal` verification run had already recorded those calls as `recoverable`, so the transition was already "spent." The same flaw meant a *failed* kick would also permanently suppress the retry. Root cause: the anti-spam gate keyed off the wrong thing. **Fix (v1.1):** gate on the durable per-call `kicked` flag — the true "have we healed this yet?" marker. A `--no-heal` observation or a failed kick can no longer swallow the kick; a genuinely-kicked call is never re-kicked. Re-verified (md5 + 45/45), re-run → kick fired → the five recoverable calls read `kicked=True` and their recordings landed. **Lesson:** an anti-spam gate must key off the durable action-taken marker, never off a derived state that other code paths can advance.

### §S144.4 — D160 repo==live, verified by hash
The owner had committed the four S143 files. All four verified byte-identical to their recorded live hashes (`verdict_review 280eb2cef9295d89f30c7b84d4c94adb`, 1837 lines · `call_verdict 539ea68fb4ce99f0029fdbb53bbf8ebe` · `daily_digest 63a558d2a73dc5ec22ea8bb772869353` · `make_force_keys 9b44831a0a2a2003fac5c4901f7da35c`). The S143 "commits owed" backlog item is closed and PROVEN, not merely reported.

### §S144.5 — D241 insights scoped; the #10 two-pipeline model (→ D243)
Discussed register items #1 (best time to call), #2 (retry-value curve), #3 (min talk-duration) and #10 (said-coming vs came). #1/#2/#3 are buildable now from call data (aggregate out, no PHI, no new secret); #3 will retune the `min_talk` constant the Investigator now uses. The owner supplied the domain model that reshapes #10 (recorded as D243): **two pipelines, never averaged.** (1) Follow-up is *informational, no chase* — the clinic calls to inform of a due appointment and does not pursue; the honest question is "of those informed, did they return around the due date?" — a reminder-effectiveness signal, not a sales KPI (which keeps pressure off Shivani/Alisha). (2) Incoming enquiries from unknown numbers are *fresh leads* with a **3-day window** to first visit. The daily consultation-report exports (seen-patients) already provide the "actually-came" half, so **#10 is buildable now on current exports; the export MIGRATION decision is an enhancement, not a prerequisite.** Locked params: 3-day new-patient window · follow-ups no-chase · ~5-week analysis basis · slice by diagnosis. Open at build time: the follow-up "came" window around the due date; the call↔patient join key (phone vs a clinic UID); whether the export carries a mappable diagnosis field. Build order when scheduled: 10 → 1 → 2 → (3 folds in).

### DECISIONS D242–D243 — FULL TEXT
- **D242** AI_VERDICT_LAYER_MASTER — GATED WRITE (parent D223/charter S143). The consolidating `AI_Verdict_Layer_Master` document is written ONLY after the D239 Flag Investigator is live AND has run stably for a real clinic period (~S145–146), to avoid the delta-chain rewrite trap (D202) of documenting a moving target. Register-only; nothing is scheduled or built by this decision. Minted at S144 open per the charter; the Investigator went live the same session, so the stability clock now runs.
- **D243** THE #10 TWO-PIPELINE CONVERSION MODEL (parent D241 #10; owner domain input, S144). The clinic runs TWO distinct call funnels that must never be averaged into one conversion number. **(1) Follow-up — informational, no chase:** one call informs a patient a follow-up is due; the clinic does not pursue. The honest metric is *return around the due date* (reminder effectiveness), anchored on the DUE date, not the call — deliberately not a sales KPI, so it never becomes pressure on staff. #2 (retry/stop-after-N) largely does not apply here; the only nuance is a WhatsApp fallback if the single informational call does not connect. **(2) Incoming unknown-number enquiries — fresh leads:** conversion = enquiry → first visit inside a **3-day window** (owner-locked; also register #6). #10 therefore reports TWO numbers, separately. The "said-coming" half already exists in `Followup_Outcomes` (`will_come`/`confirmed`); the "actually-came" half comes from the **daily consultation-report exports** already landing — so #10 is buildable on today's exports and the export-MIGRATION decision is downgraded from blocker to enhancement. Locked: 3-day new-patient window · follow-ups no-chase · ~5-week analysis basis · slice by diagnosis (feeds #11). Open at build: the follow-up return window around the due date; the join key (phone vs clinic UID); the diagnosis field's presence/mapping.

### §S144 FINDING — F-43 (raised + FIXED)
- **F-43** FLAG-INVESTIGATOR KICK-GATE keyed off an outcome transition instead of the durable action-taken flag; a `--no-heal` run or a failed kick could consume the transition and then permanently suppress the real self-heal kick for that call. Found live during install; fixed in v1.1 by gating on the per-call `kicked` flag. Class: same family as the F-41 "prove by the artefact, not the state" lesson — a gate must depend on what was actually DONE, not on a derivable state.

**Next free decision number: D244. Next free finding number: F-44.**

## §S145 — SESSION 145 (Tue 14 Jul 2026 — FULL EOS; two live VPS files replaced; the AI Verdict Layer Master written)

Session 145 raised and fixed **F-44**, a recording-gap MISLABEL, and in doing so RETIRED the "42 → Lokesh" action as a false alarm. It also wrote the **`AI_Verdict_Layer_Master`** (D245, closing D242). Two live VPS files were replaced (`flag_investigator.py` v1.2, `daily_digest.py` v1.4); no cron changed; no data lost. The whole call chain was swept — the fault was contained to exactly two consumer files.

### §S145.1 — F-44: the mislabel, found by a full-chain sweep
The owner's 21:30 digest flagged an incoming MISSED call (09:37, "talked 40s", no recording) as a lost recording. Root cause: MyOperator counts a call's clock from the first ring (menu/hold/ring all count), so a missed call can carry tens of "talk" seconds; two Python consumers judged "a real conversation" from those seconds and the customer-leg `result`, IGNORING the top-level `status` (`bridged`/`missed`/`voicemail`) that `call_hook_capture.py` already stores truthfully. Contained to two files: `flag_investigator.py` (`is_lost_candidate()` never read `status`; `diagnose()` routed Search-Logs `status "2"` into `never_recorded`) and `daily_digest.py` (`classify_pending()` emitted "talked Xs, no recording" on duration alone). VERIFIED CLEAN, no change: the receiver stores raw truth; the archiver pulls only `status "1"`+filename (missed calls never enter `Call_Recordings`); transcription and the verdict layer only ever see recorded calls (so a missed call cannot reach them — the "no content"/`cant_communicate` verdicts are genuinely connected-but-empty calls, correctly labelled); all Apps Script already gates on `status == "bridged"`.

### §S145.2 — the fix, gated + installed + PROVEN (42 → 0)
`flag_investigator.py` v1.1 → v1.2 (md5 `a9baa6ca22055bb188d5c65b93c47ba1`, 51/51 selftest): `is_lost_candidate()` drops `missed`/`voicemail` rows; `diagnose()` adds a `missed_no_conversation` outcome for status "2" and restricts `never_recorded` to status "1"+blank filename. `daily_digest.py` v1.3 → v1.4 (md5 `f7e05ed2a79670667fda170f3b70b9d1`, 75/75 selftest): `classify_pending()` labels a `missed`/`voicemail` row "missed — no recording expected" (not an alert). Both installed via WinSCP → md5 match on the VPS → `py_compile` → selftest (→ digest dry-run clean), per D188; no cron change. RE-BASELINE PROOF: the results file was backed up (`…pre_f44.json`) and rebuilt — `never_recorded_7d` **42 → 0**; `escalate_lokesh` True → False. The backup's own `detail` text broke the old 42 down as **42/42 `missed (status 2)`, 0 genuine `status 1`**. So the entire "42 never-recorded" was 42 MISSED calls: MyOperator never lost a recording; the detector miscounted. **The "take the 42 to Lokesh" action is VOID** (false alarm) — this CORRECTS §S144.2, which read the 42 as provider-side loss.

### §S145.3 — the AI Verdict Layer Master written (D245; closes D242)
`AI_Verdict_Layer_Master_v1_S145.md` (md5 `bd4b67f6810cd2316eb58dfe6bf180cd`) — canonical. Compiled from artefacts per D172 (the S131 design spec, the S143 charter, the live code, the runbook, the API reference). It carries the invariant + asymmetry, the data-flow spine, the three axes, the D191 two-phase gate, per-script contracts with live md5s, the ground rules with their scars (now including F-44/D244), the decisions the layer stands on, a live snapshot (586 proposed · 18 disposed · 18/100 · ~89% · never_recorded_7d=0), and a "deliberately not carried" list. It SUPERSEDES `AI_Review_Layer_Design_Spec_v1_1_S131.md` and RETIRES `AI_Verdict_Layer_Master_CHARTER_S143.md` (doc count stays eleven; one Phase-0 row swaps). The owner directed the write at S145, satisfying D242's stability gate by decision now that the Investigator is live and its first correctness proof (F-44) has landed.

### §S145.4 — live file versions after S145
`flag_investigator.py` = **v1.2** (`a9baa6ca22055bb188d5c65b93c47ba1`). `daily_digest.py` = **v1.4** (`f7e05ed2a79670667fda170f3b70b9d1`). Unchanged, verified-live md5s this session: `call_verdict.py 539ea68fb4ce99f0029fdbb53bbf8ebe`, `verdict_review.py 280eb2cef9295d89f30c7b84d4c94adb`, `call_hook_capture.py b8a1a293c54dfb6528e04fdf31f8d3e6`, `call_pipeline_worker.py 3c8be7f0f6f5960103fb1ed586c48cce`, `callhook_write_probe.py 705bd4a1d82068b1ccc74a2567e2ac67`, `make_force_keys.py 9b44831a0a2a2003fac5c4901f7da35c`. Diagnostics Spec bumped to **v2.3** (F-44 + the detector's status-keying); the **Fault→Action Register is UNCHANGED** (F-44 is a fixed classifier bug, not an operational response-lane fault). Incident: `INCIDENT_2026-07-14_RECORDING_GAP_MISLABEL_F44.md`.

### DECISIONS D244–D245 — FULL TEXT
- **D244** RECORDING-GAP DETECTION KEYS OFF PROVIDER STATUS, NOT DURATION (parent D239; finding F-44, S145). A call's duration includes ring/hold, so talk-seconds alone cannot distinguish a real conversation from a long-ringing miss. Every detector that reasons about "did we talk / should a recording exist" MUST read MyOperator's connected-vs-missed truth — the top-level `status` (`bridged` = a conversation; `missed`/`voicemail` = none), the same signal the Apps Script gate already uses (`status == "bridged" && customer_result == "answered"`) and the same `status "1"` vs `"2"` on the `/search` side. A `missed`/`status 2` call is NEVER a "lost recording"; it gets its own non-alert outcome (`missed_no_conversation`). `never_recorded` is reserved for the genuine gap: the provider says CONNECTED (status 1) yet produced no recording — the only subset the Lokesh threshold counts.
- **D245** AI_VERDICT_LAYER_MASTER WRITTEN AT S145 (parent D242; owner decision). The owner directed the Master's write at S145, overriding D242's ~S145–146 timing gate: the Investigator is live (S144) and its first correctness proof (F-44) has landed, so the layer is no longer the moving target D202 feared. The Master supersedes the S131 design spec and retires the S143 charter. **D242 is CLOSED by this write.**

### §S145 FINDING — F-44 (raised + FIXED)
- **F-44** RECORDING-GAP DETECTORS MISLABELLED MISSED CALLS AS "NEVER RECORDED". `flag_investigator.py` and `daily_digest.py` judged "a real conversation" from talk-seconds / customer-leg `result` while ignoring the top-level `status` the receiver already stored, so a missed call's ring/hold seconds were counted as a lost recording. Inflated the never-recorded/7d figure to 42 (all 42 were missed calls) and raised a FALSE escalate-to-Lokesh. Found from one confusing digest line; the whole call chain was swept (contained to two consumer files); fixed by keying off `status` (D244); proven by re-baseline (42 → 0). Class: same "prove by the artefact / the signal must mean what the detector assumes" family as F-41/F-43. **Corrects §S144.2's reading of the 42 as provider-side loss.**

**Next free decision number: D246. Next free finding number: F-45.**


---

## §S146 — SESSION 146 (Tue 14 Jul 2026 — FULL EOS; one live VPS file replaced)

Session 146 was a **callback-tracker FINALISATION** session. It shipped **B1** — the 21:30 digest now reads the Flag Investigator's results file instead of recomputing the recording-gap split — and NAMED the project's product architecture as a three-link lineage (**D246**). One live VPS file replaced (`daily_digest.py` v1.5); no cron changed; no new fault; no data touched. Read-only, additive.

### §S146.1 — B1: the digest reads the Investigator (one source of truth)
`daily_digest.py` v1.4 → **v1.5** (md5 `0a4ee35b5fb7fbc0570efe3bc0cdde88`, **83/83** selftest — +8 checks). The 21:30 digest now loads `flag_investigator_results.json` and renders a new **"Recording health"** section that QUOTES the Investigator's rolling split — `never_recorded_7d`, `counts["missed_no_conversation"]`, `never_recorded_threshold`, `escalate_lokesh` — with a freshness stamp. This closes the §2B carryover: the digest no longer recomputes what the Investigator already decides (single source of truth on the Investigator→Digest seam). **Fail-loud by design:** a missing / unreadable / stale (>`FLAG_STALE_HOURS`=20 h) results file is SAID so in plain English and the numbers are withheld — never a silent zero. Two thin functions read the file (`load_flag_results`, never raises) and one PURE function (`summarise_flag_results`, fully selftested) turns it into the line. **Additive only:** the 11:00 pulse and the same-day per-call "no recording today" alert are untouched (a different, faster signal, kept deliberately). Still read-only, writes nothing (D236); no `append_row` anywhere (D235) — both re-asserted by selftest.

### §S146.2 — install proof (D188)
GitHub `recordings-archive/daily_digest.py` == live confirmed by hash BEFORE edit (`f7e05ed2…`, plus `flag_investigator.py a9baa6ca…`). After build: WinSCP → **md5 match on the VPS** (`0a4ee35b…dde88`) → `/root/wa/venv/bin/python3 -m py_compile` OK → selftest **83/83 PASS** (incl. the D235 no-append and read-only guards) → **live `--digest --dry-run`** (read-only) printed the real 21:30 email with the Recording health line reading *"…0 genuine never-recorded — every connected call's recording is present · 0 missed…"* against real data (17 calls, 9 mismatch, 0 staff-logged that day). Nothing sent, nothing written. **No cron change** — the 21:30 cron picks up the new file automatically.

### §S146.3 — D246: the three-product lineage named
The owner affirmed, and D246 mints, the project's product architecture as **one lineage of three linked products on two substrates**: **Followup Tracker** (Track 1, clinic PC, offline — the SOURCE where follow-up intent is born: diagnosis, plan, due date) → **Callback Tracker** (Product A, Sheet + Console, VPS — the SYSTEM OF RECORD that executes the intent) → **Call Intelligence** (Product B, `recordings-archive`, VPS — the ANALYTICS that measures execution: verdicts, insights, conversion). Triage rule: bad/missing operational data → Product A (clinic-urgent, manual fallback); wrong verdict / miscounted digest → Product B (calm, no clinic impact). F-44 is the proof the boundary already holds — it *looked* like provider loss (A/operational) but was a Product-B consumer misreading `status`. **Three seams; two are contracts** (Callback→Intelligence via the Sheet read; Investigator→Digest via the JSON, hardened by B1); **the Followup→Callback seam is the one still to name explicitly** — a break there ("a due patient never reaches the call list") is the highest-impact failure in the chain, and it is exactly where the parked **Docterz export MIGRATION** (D243) lives. One VPS/repo covers A+B; the clinic PC holds the Followup Tracker; the KB is the umbrella index over all three.

### §S146.4 — B2 clinical windows captured (parked for #10)
The owner supplied the conversion/behaviour windows for the D241 #10 insight, captured now and to be minted as decisions when #10 builds: **outgoing follow-ups** — read ~**5 weeks** of history and LEARN the return window PER DIAGNOSIS (no single ± number; diagnosis is a required dimension, feeding #11); **incoming fresh leads + callbacks of incoming missed calls** — a flat **3-day** conversion window after the call (consistent with D243's owner-locked 3-day new-patient window). Parked, not built this session.

### §S146.5 — live file versions after S146 + housekeeping
`daily_digest.py` = **v1.5** (`0a4ee35b5fb7fbc0570efe3bc0cdde88`, 83/83). Unchanged, verified-live md5s this session (GitHub == live, hash-matched before edit): `flag_investigator.py a9baa6ca22055bb188d5c65b93c47ba1`, `call_verdict.py 539ea68fb4ce99f0029fdbb53bbf8ebe`, `verdict_review.py 280eb2cef9295d89f30c7b84d4c94adb`, `call_hook_capture.py b8a1a293c54dfb6528e04fdf31f8d3e6`, `call_pipeline_worker.py 3c8be7f0f6f5960103fb1ed586c48cce`, `callhook_write_probe.py 705bd4a1d82068b1ccc74a2567e2ac67`, `make_force_keys.py 9b44831a0a2a2003fac5c4901f7da35c`. **Diagnostics Spec UNCHANGED (stays v2.3)** — B1 adds no fault code/check/fallback; it changes the digest's reporting line only. **Fault→Action Register UNCHANGED.** No incident this session. **Housekeeping caught + fixed:** the v1.71 CHANGELOG entry was ABSENT although the v1.71 end-marker promised it (an S145 EOS omission) — backfilled in this v1.72 bump; class = the same stale-record family the KB has caught before (§S131, §S143 Umbrella marker).

### DECISION D246 — FULL TEXT
- **D246** THE THREE-PRODUCT LINEAGE (parent D223/D236; owner affirmation, S146). The project is one lineage of three linked products on two substrates: **Followup Tracker** (clinic PC, offline — source of follow-up intent) → **Callback Tracker** (VPS, Sheet + Console — system of record / Product A) → **Call Intelligence** (VPS, `recordings-archive` — analytics / Product B). The boundary is conceptual + a code/doc/contract seam, NOT separate infrastructure: one VPS, one repo, one secret store, one EOS discipline for A+B; the Followup Tracker stands most separate (own machine, offline, frozen). The demarcation exists for triage and safe iteration: A is operational-urgent with a manual fallback and trends toward frozen; B is owner-facing, batch, next-day-tolerant, free to evolve without risking the core. Three seams; the two downstream are defined contracts (Callback→Intelligence via Sheet tabs; Investigator→Digest via `flag_investigator_results.json`, hardened by B1); the **Followup→Callback** seam is not yet a named contract — its break is the chain's highest-impact failure, and the parked Docterz export migration (D243) lives there. Register entries for verdicts/insights/analytics are tagged **Product B** from S146.

---

## §S147 — 19 Jul 2026 (Session 147, FULL EOS — one repo code push [`Main.gs`]; the knowledge base restructured)

> **Backfilled at S149** from `HANDOFF_RUNBOOK_2026-07-19_Session147_v85.md` §0 and `D247_Canonical_Data_Management_S147.md` — deliberately, from those two artefacts, not reconstructed from memory. §S148 flagged this gap; this section closes it. (Placed between §S146 and §S148 in session order.)

**Type.** Knowledge-base restructure. The problem solved: the canonical docs had grown huge and were read in full at the start and rewritten in full at the end of every session — the dominant per-session cost. One repo code push (`Main.gs`); no other live/VPS code touched, no `.env`, nothing restarted.

**D247 minted — a three-tier canonical system + the KB split.** Every canonical doc is tagged **Tier 0** (session loop — read at start, rewritten at end), **Tier 1** (reference — hash-verified at start, read only if the session's task touches it, rewritten only if changed), or **Tier 2** (frozen — hash-verified only, never read in the loop, changed only by explicit owner waiver + a version bump). This **clarifies** D202/S100 (still one consolidated file per doc, no delta chain) — it does not repeal it.

**The KB split — the one big one-time surgery.** The monolithic `Clinic_Master_KB_SystemsRegister_v1.72` (~4,300 lines, md5 `27b72639…`) became two consolidated single files, neither a delta chain:
- **`KB_Register_v2.0`** (md5 `651c254b…`, ~490 lines) — current state only: systems register, a one-line decision index, a one-line finding index, current live-file versions + md5s, and the backlog. Rides the loop. Authority on what is true NOW.
- **`KB_History_Archive_v1.0`** (md5 `44681d05…`) — every `§S###` narrative and every full D/F text, carried over VERBATIM. Out of the loop; opened on demand. Authority on what HAPPENED.
- **Proof nothing was lost:** every source line 1→4307 was assigned to exactly one file; **0 of ~3,500 content lines dropped**. Three self-checks tried to pass while wrong — a newline off-by-one that blinded its own check, plus two dedupe checks fooled by mis-computed sets — and each was caught by an artefact-level second check. A live demonstration of *"a check that cannot fail is not a check."*

**Decisions index completed.** D121→D246 indexed in the Register; the 45 previously-undefined decisions (D189–D218, D225–D239) were authored from their full text in the Archive, never from memory.

**`CANONICAL_MANIFEST.md` created** — the linchpin every Phase 0 verifies (all tiers by md5; read Tier 0 only). If a doc is not a row in it, it does not carry forward.

**`END_OF_SESSION_PROMPT_v4`** (md5 `9fa2be50…`) — the tier-aware close-out: append to the Archive, update the Register, maintain the manifest. No more whole-KB rewrites.

**Frozen-product dossiers (Tier 2) built / adopted:**
- **Attendance** (`attendance/`) — dossier `efc17e19…`, folder digest `dc12f4a0…`.
- **Nutrition / Diet write-path** (`clinic_writer/`) — dossier `3b869d0e…`, folder digest `df0b0c34…`; frozen **as-is** (a Hindi-spelling tidy would be waiver-gated).
- **Callback Tracker core** (`dashboard/`) — dossier `7e445ff0…`, live project digest `e4fd4512…`. Freeze split **confirmed**: the write-path core is frozen (`WebApp.gs` D34 + Config / MyOperator / Netting / Sheets / Main + manifest + the Sheet); the Console / Dashboard / Health / Outcome UI stays an **active Tier-1 subsystem** (`Call_Console_Evolution_Spec`, `Frontend_Dashboard_Documentation`).
- **WABA templates** — adopted (`WABA_Approved_Templates_v1_S137`, `63dd1883…`).
- **`SYSTEM_DOC_COVERAGE_MAP_S147`** — every subsystem → its authoritative doc, plus the three consolidation-candidate gaps (Follow-up Tracker · Call-hook family · WhatsApp API family).

**Consent HTML reclassified** — removed from the frozen set; it now lives inside the in-development **Surgical Estimate tool** (not yet in GitHub). Its dossier/freeze is deferred until that tool ships. Tier 2 is therefore **four** products, not five.

**Repo code push.** The live `Main.gs` (D206: `removeTriggers()` scoped to Main's own three triggers) was pushed over the stale pre-D206 repo copy. Live-vs-repo verified: all other `dashboard/` files already matched.

### DECISION D247 — FULL TEXT

- **D247 — Canonical Data Management: tiers, the Register/Archive split, and frozen-product dossiers.**
  **Why.** The KB (`Clinic_Master_KB_SystemsRegister`, v1.72, ~4,300 lines) was append-only: every session it gained a `§S###` narrative, a top-of-file consolidation note, and the full text of that session's decisions, and shed nothing. The dominant per-session cost was reading the whole project history at start and rewriting all of it at end. D202/S100 ("one consolidated file, no delta chain") stopped *fragile* delta chains but had produced one file that behaved like an ever-growing delta chain glued together.
  **Ruling.** (1) **Register / Archive split** — the KB becomes two consolidated single files: the **KB Register** (current state only — the systems register, a one-line decision index D1…D246, a one-line finding index, current live-file versions + md5s, and the backlog; authority on what is true NOW; rides the loop) and the **KB History Archive** (append-only — every `§S###` narrative and every full D/F text, carried over verbatim, nothing dropped per D172; authority on what HAPPENED; out of the loop, opened on demand). Both remain consolidated single files; neither is a delta chain. This **clarifies** D202/S100, it does not repeal it. (2) **Three tiers** — every canonical doc is tagged Tier 0/1/2 in `CANONICAL_MANIFEST.md`: Tier 0 read at start + rewritten at end; Tier 1 hash-verified at start, read only if touched, rewritten only if changed; Tier 2 hash-verified at start, never read in the loop, never rewritten, changed only by an explicit owner waiver (D34 discipline) + a version bump. (3) **Frozen products get a dossier + a ledger** — each frozen product has exactly one canonical as-built dossier (the deep-reference doc); the FROZEN ledger is a thin index, one row per product (name · dossier file · artefact location · artefact md5 · frozen-as-of S/D · waiver rule); dossier weight matches product weight. (4) **Phase 0 verifies the manifest by md5 for ALL tiers but reads only Tier 0** — integrity is proven for everything (cheap — hash compare only); context is spent only on the hot set. (5) **Authority order (unchanged in spirit)** — "the KB wins if anything disagrees" now reads: the **Register** wins on current state; the **Archive** wins on history; the two cannot conflict (the Archive is dated history and asserts nothing about *now*). **Provenance (binding):** every md5 in the manifest is computed from the live artefact at freeze/version time (D172/D188) — no hash is ever assumed; a dossier for a not-yet-documented product is built from the live artefact, never from memory. **Relates to:** clarifies D202/S100 · extends D34 (freeze-by-waiver) to the frozen-product set · parents D223/D236/D246 (the three-product lineage).

**Live file versions after S147:** unchanged from §S146.5 — no live/VPS Python was touched this session; the only code change was the repo `Main.gs` push (D206). **Next free at S147 close: D248 · F-45 · Session 148.**

---

## §S148 — 19 Jul 2026 (Session 148, FULL EOS — GitHub repo changed; canonical docs changed; NO live/VPS code touched)

**Type.** Documentation + repo-hygiene. No VPS code, no `.env`, nothing restarted. One GitHub commit (the repo trim). Canonical project-knowledge docs changed: the evergreen START-HERE template (v4→v5), `CANONICAL_MANIFEST.md`, and — at this close — this Archive and the KB Register.

**Phase 0.** Clean. Every row in `CANONICAL_MANIFEST.md` hash-verified across all tiers; all matched. The single row the manifest itself flagged unpinned (`Fault_Action_Register`, "compute at EOS") was carried in as backlog item 3 and resolved (below).

**1 · S147 install verified (backlog item 1).** By direct project-knowledge inventory: all twelve restructure files present (Register v2.0, Archive v1.0, manifest, EOS v4, four dossiers, coverage map, D247, START_HERE_148, runbook v85); the retired monolith `Clinic_Master_KB_SystemsRegister_v1.72` and `END_OF_SESSION_PROMPT_v3` both absent. The manifest's own STATUS line still self-described as "proposed / becomes canonical on install" — stale post-install; corrected in item 3.

**2 · START-HERE evergreen template rebuilt v4 → v5.** `START_HERE_PROMPT_v4.md` (also the project's custom instructions) still named `END_OF_SESSION_PROMPT_v3`, the retired `KB_SystemsRegister` with the obsolete D121→D188 index note, and spec versions `v2_0`; it had no tier model and no Phase 0. `START_HERE_PROMPT_v5.md` adds Phase 0 and the tier model, **defers to the manifest for the doc set + versions** (the durable fix — it can no longer rot on a version bump, the exact fault that retired v4), restores the last-4 patient masking, and drops the pre-manifest "check System_Health sheet" start-ritual. Owner installed it to project knowledge and to the custom instructions, replacing v4 (v4 archived in the repo trim).

**3 · CANONICAL_MANIFEST reconciled (backlog item 3).** `Fault_Action_Register_v2.1` provenance established by cross-store agreement: the project-knowledge copy and the GitHub mirror (`canonical-docs/Fault_Action_Register_v2_1.md`) are **byte-for-byte identical**, md5 `fde74c496a00826b504dc77b0c0c6cf6`. That hash pinned into the manifest; the FAR row is now inside the Phase 0 verified set. The same edit flipped the STATUS line to "canonical — installed" and marked the Install bullet done. Three targeted whole-line swaps, each anchor asserted unique; line count unchanged. Owner swapped the updated manifest into project knowledge.

**4 · Repo trim executed, pushed, externally verified (backlog item 2).** `Repo_Trim_S148.ps1` (dry-run default, `git mv`, collision-guarded, no auto-commit) moved **105** superseded documents from `canonical-docs/` into `canonical-docs/archive/`, and **rescued** the current `Maintenance_SOP_System_Spec_v1_1.md` — which the naive "archive `docs/`" instruction would have buried — up into `canonical-docs/` (its md5 verified `== 35b257ee…` before the move). Commit `0db5c01`: **106 files changed, 0 insertions, 0 deletions** (every change a pure rename → history preserved), pushed `ae2e4ff..0db5c01 main -> main`. Verified from GitHub by raw-file probe: retired KB v1.72 now 200 at `archive/`, 404 at the old path; Maintenance SOP 200 at `canonical-docs/`, 404 at `docs/`.

**5 · git-PATH permanent fix (client-side, no repo change).** The first `-Execute` run failed "git is not recognized" — the PowerShell window couldn't see GitHub Desktop's bundled git (at a version-numbered path). A one-time PowerShell-profile snippet was installed that **auto-finds the newest** `GitHubDesktop\app-*\…\git.exe` on every new window, so it survives GitHub Desktop updates. Confirmed: `git --version` works in a fresh window with no setup block.

**Findings.**
- **F-45 (raised; fix parked to S149).** `Fault_Action_Register` is titled **v2.1** but its changelog's newest row is **v2.0** — the v2.1 bump left no changelog entry. Same stale-record family the KB keeps catching (v1.71 backfill; §S131/§S143). Not a corruption (end-marker present, file complete). Fix = add the missing v2.1 row.

**Integrity gap found this session (flagged, not yet fixed):**
- **This Archive was missing §S147.** Its end-marker named §S146 as the last section and its next-free line still read D247, so the S147 restructure narrative was never appended at S147 close (it lives in HANDOFF_RUNBOOK v85 §0, START_HERE_148 §0, and `D247_Canonical_Data_Management_S147.md`). The next-free counter is corrected in this v1.1 bump; **backfilling the full §S147 block from those sources is on the S149 backlog** (done deliberately, not fabricated second-hand here).

**Repo-mirror gaps found (backlog, not faults — live/PK is canonical, D160):**
- `API_QUICK_REFERENCE_CARD.md` (current Tier-1 doc) — **absent from the GitHub repo entirely.**
- `WABA_Approved_Templates_v1_S137.md` (current Tier-2 dossier) — **absent from `canonical-docs/dossiers/`** (the other three dossiers are present).
- `README_CANONICAL_SET.md` — almost certainly still describes the pre-restructure set; needs a content refresh (left in place, not archived).

**Decisions:** none minted — the work was hygiene, not a new architectural choice. **D248 stays free.**
**No live-system change; no incident; Gmail health note skipped (no manual health check performed).**

**Next free decision number: D248. Next free finding number: F-46.**

---

## §S149 — 19 Jul 2026 (Session 149, EOS-light — documentation + repo-hygiene; NO live/VPS code touched)

**Type.** Documentation / repo-hygiene close-out. No VPS code, no `.env`, nothing restarted. All work built and verified offline; the GitHub pushes are **owed** (produce-then-push — the assistant is read-only, the owner pushes). Canonical project-knowledge docs changed at this close: `CANONICAL_MANIFEST.md`, `Fault_Action_Register_v2_1.md`, `KB_Register` (v2.1 → **v2.2**, housekeeping), this Archive, and (repo-only) `README_CANONICAL_SET.md`.

**Phase 0.** Every carried Tier-1/Tier-2 row (16 docs) hash-verified against the manifest — **zero drift**. The Tier-0 loop rows, however, had **drifted**: the manifest still named the S148-*open* set (`START_HERE_SESSION_148`, `KB_Register` v2.0, `HANDOFF_RUNBOOK` v85) because the S148-*close* update to the manifest was never made. Corrected this session.

**Backlog resolved.**
- **Items 1 & 2 (push API card / WABA dossier) — found ALREADY DONE.** Both are in the GitHub mirror and **byte-for-byte identical** to project knowledge and their manifest pins (`68c4fc34…`, `63dd1883…`). The "absent from repo" backlog was stale — the same stale-record family the project keeps catching. Struck, not re-pushed.
- **Item 4 — F-45 RESOLVED.** `Fault_Action_Register` was titled v2.1 with a changelog that stopped at v2.0. The missing v2.1 row was added, documenting §0.35 / **D204 (S132)**: the Lane-1 auto-responder does not exist and is not scheduled; D113 reclassified as intent-not-fact; the `System does` column reads "once Deliverable 2 exists" (D178). No lane, procedure or rule changed. `fde74c…` → `3bfeac72…`; re-pinned.
- **Item 6 — §S147 backfilled** into this Archive (the block above), written from `HANDOFF_RUNBOOK` v85 §0 (pulled back from the repo archive) + `D247_Canonical_Data_Management_S147.md` — deliberately, from those artefacts, not from memory; every md5 fingerprint cross-checked against the manifest. `44681d05…` → re-pinned.
- **Item 3 — README refreshed.** The repo `README_CANONICAL_SET.md` was stuck at Session 125 (KB v1.48, Umbrella v1.36, Runbook v59, referencing the retired `KB_APPEND_Session125`). Rewritten to the post-restructure tiered model; it now carries no version numbers and defers to the manifest, so it cannot rot on a bump.
- **Item 5 — Phase-2 repo tidy produced.** `Repo_Trim_Phase2_S149.ps1` (dry-run default, `git mv`, collision-guarded, no auto-commit — the S148 pattern) archives **38** unambiguously-superseded files: 3 `canonical-docs/` stragglers the S148 trim could not catch (`KB_Register_v2_0_S147`, `KB_History_Archive_v1_0_S147`, `START_HERE_SESSION_148` — their successors did not exist when that trim ran) + 35 historical `docs/` files. It **holds 12** live/uncertain clinic + reference docs (the clinic manuals — Troubleshooting Runbook, Staff/Doctor Manuals, Wall Cards, Hinglish Call-Desk Companion — plus four inventories/briefs and two context docs) for an owner ruling, rather than wildcard-sweeping them: the documented "don't bury a live file" rule (the S148 Maintenance-SOP near-miss).

**Manifest.** Regenerated to S149: Tier-0 rows corrected to the live set; FAR + this Archive re-pinned; jobs 1–2 recorded verified-already-done; a README companion note added.

**Method.** Every edit was an assert-once anchor with full collateral-change reversal verification (the FAR reverses to the byte-identical original; the Archive reverses to its pre-edit self). All hashes computed from the live artefact, never assumed (D172/D188).

**Findings.** **F-45 RESOLVED.** No new finding raised. **No decision minted** — the work was hygiene, not a new architectural choice; **D248 stays free.**

**Carried forward:**
- **GitHub pushes owed** (produce-then-push): the corrected FAR, updated Archive, refreshed README, regenerated manifest overwrite their `canonical-docs/` paths; then run the Phase-2 tidy; then commit + push.
- **The 12 held `docs/` files** need an owner ruling (current vs superseded) before they can be archived.
- ~~Register housekeeping~~ **DONE at this close:** the Register bumped **v2.1 → v2.2** — findings line advanced (F-45 RESOLVED, next free F-46) and **D247 added to its decisions index** (was in the header only). No other Register content changed.
- **Insight Harvest items · D223 doctor-portal gist tile** — carried, unchanged.
- **Live-systems Track 2** (untouched by this arc): WABA sends blocked on the MyOperator authorizer fault (D120, Lokesh); `wa_approve` still nohup-not-systemd; key rotations overdue.

**Next free decision number: D248. Next free finding number: F-46.**

---

## §S150 — 22 Jul 2026 (Session 150, FULL EOS — one Tier-2 frozen product changed under waiver; NO live/VPS code touched)

A build session on the **frozen** Nutrition/Diet write-path (`clinic_writer`, Tier 2, D247). The owner asked for a batch of doctor-approved changes to the PC-local tool; the product was **unfrozen under an explicit waiver (D248, D34 discipline)**, changed, verified, installed, and **re-frozen** with a version bump.

**Base verified first (D172/D188).** The 5 code files in the owner's `clinic_writer` zip were md5-checked against the dossier hashes before any edit — all matched (`clinic_writer.py 0ad6d9f4`, `vitals_app.py ba29a558`, `vitals_page.html 24ac9af4` = v26 base, `clinic_menu.html e5dc69df`, `open_vitals.bat 9ba27c04`). All change work was confined to **`vitals_page.html`**; the engine, Flask app and the two ledger schemas (20/14 cols) were never opened. Live patient data was never touched.

**What changed (all in `vitals_page.html`, v26 → v28):**
- **(a) Hindi spelling/grammar tidy** in the exercise/modality LIB strings (`name_hi`/`instr_hi`) — 8 sites (e.g. स्ट्रेंगदेनिंग→स्ट्रेंथनिंग; मुवमेंट→मूवमेंट; सायटिक→साइटिक; “AND”→“और”; frozen-bottle strings reworded). **This closes the dossier's sole open caveat (§5/§6).**
- **(b) Clinical content:** exercise library **126 → 128** (Frozen-Shoulder Standard **Internal-Rotation towel**; Rotator-Cuff Standard **Cross-Body**), a **PIVD knee-to-chest stop-rule**, and a **bottle-roll dose** fix (“5 min each foot”, “2–3×/day”). A web cross-check (AAOS/NHS/Mayo) confirmed the library is clinically sound.
- **(c) Diet chart ported from Excel.** The tool already ported the Excel `My_Plan` maths; the missing piece was the Excel **`Diet_Chart`** tab (“व्यक्तिगत आहार चार्ट”). Built as `dietChartBlocks()` — a **new optional printable sheet** gated by an “Include diet chart” checkbox (default ON), its own page break, bilingual per the existing `#lang` selector, feeding the existing **text-only archive seam** with **zero engine/app change**. Owner choices: **diet-aware** meal schedule (option b — eggs for Egg+Veg; soy/paneer swaps for Pure Veg; local fish + chicken for Non-Veg); **weekly shopping list dropped**; sections kept = A (daily meals), B (prioritise, condition-branched), C (avoid), and comorbidity (relabelled **D**). Two folded-out Excel columns noted to the owner (Excel “Key Nutrients” survives inside the existing Nutrition-Advice band; meal content stays Hinglish — sattu/mattha/akhrot — in every language mode).
- **(d) Screen-only comfort theme.** A warm dim `@media screen{…}` palette for eye comfort during on-screen review. **Print is fully isolated** (printing hides everything and renders a fresh white `#printDoc` under `@media print`), so printouts are **byte-identical** — verified.
- **Late label tweaks (owner):** “घरेоू व्यायाम पत्रक” → **“घर की एक्सर्साइज़”**; diet-sheet heading अनुसूची → “दैनिक भोजन”. The sibling per-condition sub-label “| घरेоू व्यायाम” was left as-is on the owner's “all other seems ok” — flagged as still-unmatched if he wants alignment later.

**Verification & install.** Edits were applied with per-edit `assert count==N` + JSON re-parse. A **functional node smoke test** (diet × condition × comorbidity) caught a **`ReferenceError`** — Section B referenced `cond`, which existed only in `planBlocks`, not in the new `dietChartBlocks` — that `node --check` had passed (syntax OK, scope not). Fixed by declaring `cond` inside `dietChartBlocks`; the four-case smoke test then passed (Pure Veg = zero eggs, Non-Veg = fish, B always 3 rows, C always 5, D only when a comorbidity is recorded). Final **`vitals_page.html` v28, md5 `fcedae303b620f3e5199f4b1e4766510`** — owner-confirmed **installed** on `D:\clinic_writer\` (saved under the original name, old file deleted, runs via `open_vitals.bat`).

**Method / invariants.** Full-file replacement only (no deltas, D202); source md5-verified before edit (D172); expected values from the artefact, never memory (D188); every edit count-asserted and JSON/smoke-re-validated; engine/app/schemas untouched; print output byte-identical; Tier-2 change is **waiver-gated with a version bump** (D34/A6). The `cond`-scope catch reinforces “`node --check` verifies syntax, not scope; the artefact-level second check is mandatory” — a lesson, not a live fault.

**Findings.** **No new finding.** The `cond`-scope slip was self-introduced during the build and fixed before delivery — not a fault. **F-46 stays free.**

**Docs.** Nutrition dossier → **v1.1** (caveat closed; v28 recorded; folder-digest recompute owed at install). Register → **v2.3** (D248 indexed; state note; changelog). This Archive → **v1.2** (this section). Manifest updated last.

### Decision minted this session

- **D248** WAIVER — `clinic_writer` unfrozen for one owner-approved batch (S150; D34 discipline). The Tier-2 frozen Nutrition/Diet write-path (`clinic_writer`, D247) was unfrozen under an explicit owner waiver for a batch of doctor-approved changes to `vitals_page.html`, then re-frozen with a version bump (dossier v1 → v1.1). All changes are in `vitals_page.html` only — the engine (`clinic_writer.py`), Flask app (`vitals_app.py`), ledger schemas (20/14 cols) and the archived-PDF/print output are untouched and byte-identical; no VPS/live code. Changes: **(a)** Hindi spelling/grammar tidy in the exercise/modality LIB strings (`name_hi`/`instr_hi`) — **closes the sole open dossier caveat** (§5/§6); **(b)** exercise library extended 126 → 128 (Frozen-Shoulder Standard Internal-Rotation towel; Rotator-Cuff Standard Cross-Body) plus a PIVD knee-to-chest stop-rule and a bottle-roll dose fix; **(c)** the Excel `Diet_Chart` tab ported into the tool as a new optional printable diet sheet gated by an “Include diet chart” checkbox (default ON) — **diet-aware** meal schedule (owner choice (b): eggs for Egg+Veg, soy/paneer swaps for Pure Veg, local fish + chicken for Non-Veg), the weekly **shopping list dropped**, sections A/B/C + comorbidity (relabelled D), feeding the existing text-only archive seam with zero engine change; **(d)** a **screen-only** reading-comfort colour theme (`@media screen`) — print is fully isolated and unchanged. `vitals_page.html` v26 → **v28**, md5 `fcedae303b620f3e5199f4b1e4766510`; owner-confirmed **installed live** on `D:\clinic_writer\`. A build-time `ReferenceError` (a Section-B `cond` scope slip) was caught by the functional node smoke test **before delivery** and fixed — reinforcing that `node --check` verifies syntax, not scope, and the artefact-level second check is mandatory (not a live fault; no F minted). *Full text: Archive §S150.*

**Carried forward (unchanged):** the S149-owed install/push jobs (install the S149 doc set to project knowledge + push to GitHub, run `Repo_Trim_Phase2_S149.ps1`; rule on the 12 held `docs/` files) — the S150 doc deltas fold into that same pending install; Insight Harvest items; D223 doctor-portal gist tile; Live-systems Track 2 (WABA sends blocked on D120/Lokesh; `wa_approve` nohup-not-systemd; key rotations overdue).

**Next free decision number: D249. Next free finding number: F-46.**

---

## §S151 — 05 Aug 2026 (FULL EOS — one new live VPS file; attendance system extended; salary policy locked)

**Theme: July salary processed; the salary layer built.** The session began as "how do I process July salary"
and ended with the salary computation automated at source, a locked staff punctuality policy, and Darpan's
entire financial complexity systematised — all at the workbook layer, nothing sensitive added to the VPS
beyond what `staff_master.csv` already carried.

**1. July salary inputs computed (twice, independently — and they agree).** First from the owner-uploaded
July register PDF by pdfplumber coordinate parse (day column = round((cx−86.7)/22.6545)+1), producing
ABSENT/LATE-MIN/EXTRA-MIN per staff with a 24/24 self-check (computed Present and Absent matched the
register's printed P/A for all 12 staff). Later, `att_month_report.py` on the VPS recomputed the month from
raw `punches.csv` — Present/Absent matched the PDF path 12/12, and every grace-band difference in late
figures reconciled by hand (Sukhveer 93→74 min, Sandip 533→497). Two independent computation paths, one
truth. Shivani's 1100 extra minutes = 4 genuine evening covers of Alisha's leave (days 9/10/13/15) → paid
as 4 × Rs 200 cover rate, not raw minutes; Alisha's absences on 14/16/17 had no Shivani out-punch → not
credited (punch-out rule born here, now notice point 7).

**2. Sandip's timing corrected (owner ruling: 09:00–21:00, was 08:00–20:00 in the workbook).** His July
lates collapsed 1853→533 min — a stale recorded shift, not chronic lateness. The pattern (every staff
member judged against their OWN timing; a wrong timing manufactures fake lateness) is now a standing check
before any fine regime.

**3. `staff_master.csv` rebuilt and live: 12 active staff, all with base salaries** (Darpan and Arjun added
by the owner in the workbook). `build_staff_master.py` proved it parses Darpan's split-shift string
("09:30-15:30 + 18:00-21:00") correctly → wd 09:30–21:00 (first start, last end — right for late/extra
judging). Live VPS md5 `f8f3a23908d2007ccdc1bd9af5e87725`. The salary workbook's permanent home is now
**`D:\clinic_salary\`** — a plain non-repo folder (F-31: one careless commit must never be able to publish
salaries); `build_staff_master.py` is run FROM that folder against the repo copy of the script. The old
OnTime-era salary folder (`08_salary_attendance_system`) is archived-then-deleted; the workbook found
inside it was verified canonical by rebuild-and-compare (identical to live VPS CSV, salaries masked in
comparison) before adoption.

**4. Staff punctuality policy designed, costed, LOCKED (D249), effective 01-08-2026.** July's data showed
lateness is systemic (10/12 staff late 15–25 of ~27 days) → policy targets frequency, not depth. Incentive
costed: worst case Rs 4,400/month (~4.2% of wage bill), realistic Rs 2,500–3,300; July baseline 0/12 would
qualify at strict thresholds → ramp built in. Bilingual 10-point notice drafted in-chat for the board.

**5. Darpan systematised (D250).** Owner rulings captured across the session: interest-bearing tranche at
flat Rs 1,000/month (≈6.3% p.a., no annual reset; figures live in the workbook only, per F-31), waterfall
interest→interest-bearing principal→interest-free tranche, 2 permitted instalment skips per FY then
recover-from-perks, unpaid months capitalise the flat interest, ST advances clear in-month (rarely 2–3),
every ad-hoc payment classified by dropdown (Perk / ST-Advance / ST-Recovery / Skip-Recovery) with date +
narration for longitudinal tracking, outstation allowance paid CASH at trip end — the Outstation Log
(start/end dates, days auto) exists to settle those punchless biometric absents and build the data record.
Deliverable: **`Darpan_Loan_System_v2_3.xlsx`** (md5 `dd6689e12bd0c2d8daa2b9903e8ded5f`; 5 sheets: Loan
Master · Schedule Card (print, signature lines) · Repayment Tracker (FY skip counter + RECOVER-FROM-PERKS
action flags; unprocessed months stay frozen — predecessor-guarded chain) · Perks & ST-Advance Ledger ·
Outstation Log). Numerically verified against hand-amortisation including skip-capitalisation and the
partial-payment case; v1 (reducing-balance, tranche-split repayments) analysed and DISCARDED as
over-engineered before the owner's flat-rate rulings. Tracker rows May/Jun-2026 pre-entered PAID; Apr-2026
and Jul-2026 are the owner's two cells. **Integration into `Salary_System_2026.xlsx` is parked as TOP JOB
next session.**

**6. Phase-1 salary automation LIVE (D251): `att_month_report.py` on the VPS** (md5
`c925198895ea146b37a0c69b0ef85b6b`), installed by the standard loop (WinSCP → md5 match → --selftest PASSED
on VPS → live July dry-run). Read-only; imports `att_core` for identical engine rules (engine and report
cannot disagree); adds the D249 policy layer (10-min grace marks, >30 = 2 marks, >60 review column,
marks//3 half-day deductions, incentive tier with Aug–Sep ramp); writes only its own dated
`salary_inputs_YYYY-MM.csv/.html` (A4-landscape print) beside itself. July run archived; its
Deduction/Incentive columns are PREVIEW ONLY (policy starts August). Additive to the frozen attendance
product — no frozen file modified; the repo `attendance/` folder gains the file (dossier v1.1 re-pins).
Roadmap locked: **Phase 2** = workbook → Google Sheet + gspread output tab (one-writer-per-tab), bundled
with the overdue key-rotation session; **Phase 3** = salary tile on the doctor PORTAL (not the staff-facing
attendance site — doctor-only by construction, attendance stays frozen), bundled with D223, decided after
Phase 2 has run.

**7. 🔴 F-46 RAISED — masking-by-detection failed twice in one session.** (a) A `diff` of staff_master CSVs
printed the base-salary column into the chat log; (b) after committing to masking, a header-keyed mask
missed because the workbook's row 1 is a title and the real headers sit in row 2 — the salary column
printed again. Same fault class as F-23/F-44's lesson: a guard that depends on detecting the sensitive
field is one format quirk away from failing open. **Rule minted: from any salary-bearing file, print only
whitelisted columns (name, timings, offs, active) — never mask-by-exclusion, never raw diffs/dumps.**
Applied for the rest of the session (all later comparisons whitelisted). Owner was informed at each breach,
immediately, in the reply that contained it.

**8. Notion not updated this session — the Notion connector was absent from the session's tool set.**
Carry: add S151 to Clinic HQ at the next session that has the connector. Drive delivery unchanged (owner
drag-drop; Drive writes still fail). No Gmail health note (no manual health check; the automated digest
system is live).

### Decisions minted this session

- **D249 — Staff punctuality & incentive policy, effective 01-08-2026.** Grace 10 min on each person's own
shift start (engine still records raw minutes; policy layer applies grace). >10 min = 1 late mark; >30 min
= 2 marks; >60 min without informing = half-day absent (script surfaces a >60 review count; informed/not is
the owner's judgment). Every 3 marks in a month = half-day salary deduction. Punctuality incentive by
salary band (~3–4% of own salary; slabs Rs 500/400/300 + fixed for the two band-X staff), paid on marks:
ramp Aug+Sep 2026 FULL ≤5 / HALF ≤8, from Oct FULL ≤2 / HALF ≤5, announced as a ladder in the same notice.
Sundays never late (engine rule stands). Evening cover duty Rs 200/evening, paid only against a punch-out.
Outstation duty informed in advance; those days are not absents. Machine record final. Deductions framed as
attendance-based half-days, never "fines" (statutory caution). July 2026 is pre-policy: its
deduction/incentive columns are preview only.
- **D250 — Darpan financial systemisation (figures in the workbook only, F-31).** Two-tranche long-term
loan: interest-bearing at FLAT Rs 1,000/month (no annual recalculation; ≈6.3% p.a. at adoption; interest
stops when the tranche clears; unpaid months capitalise the flat amount), plus an interest-free tranche.
Waterfall: recovery → interest → interest-bearing principal → interest-free. Two permitted skips per FY
(Apr–Mar); 3rd onward auto-flags recovery from perks. ST advances: recovered from the month's salary
(rarely carry 2–3 months); salary-day order = ST-recovery, then instalment, then attendance deductions —
if salary can't bear all, the instalment skips and the tracker prices it. All ad-hoc money classified
(Perk / ST-Advance / ST-Recovery / Skip-Recovery), dated + narrated, longitudinal. Outstation allowance is
CASH at trip end; the log's purpose is settling punchless biometric absents + the data record (days and
cash, lifetime, on the Loan Master). Printable signed schedule card is the standing answer to ad-hoc
demands. Position adopted as at 31-Mar-2026 from the owner's paper ledger; tracking from Apr-2026.
- **D251 — Salary-layer architecture and roadmap.** The attendance system deliberately does not compute
salary; the workbook is the money layer. Workbook home = `D:\clinic_salary\` (never inside a git working
tree). One master per concern: no per-employee CSVs — Darpan is a normal `staff_master.csv` row; his
complexity lives in workbook sheets. Phase 1 (LIVE): `att_month_report.py`, read-only, engine-importing,
policy-layered, dated CSV+A4-HTML outputs, monthly archive under `D:\clinic_salary\reports\`. Phase 2
(next): workbook+module → one Google Sheet; VPS writes ONLY its own output tab via gspread (one writer per
tab); bundled with the overdue key rotations (new service-account credential enters `.env` in the same
sitting). Phase 3 (optional, after Phase 2 has run): salary tile on the doctor portal (port 8099) bundled
with D223 — NOT on the staff-facing attendance site; portal is doctor-only by construction and the frozen
attendance product stays untouched.

**Findings: F-46 raised (see §7). Next free decision: D252. Next free finding: F-47.**

---

---

# §S152 — 06 Aug 2026 (Session 152, FULL EOS — one Tier-2-adjacent product file changed owner-side: the salary workbook gained the Darpan module; no VPS/live code; three policies locked; one system drafted)

**0. Numbering correction (D172's own field, caught at EOS, recorded here first so every reference below is unambiguous.** In-chat this session the assistant labelled the day's decisions D251–D254, but **D249–D251 were spent at S151** (Register v2.4 index; D251 = the salary-layer roadmap). The chat labels map as: chat-"D251" = **D252** (fines & grace cap) · chat-"D252" = **D253** (Sunday roster) · chat-"D253" = **D254** (leave register) · chat-"D254" = **D255** (Staff Management System, draft). The printed notices are unaffected (they carry rules, not decision numbers; the v3/v4/v5 filenames carry the wrong D-prefixes — cosmetic only, noted so a future reader is not misled by a filename: a filename is not provenance, D188).

**1. Backlog item 1 (TOP) DONE — Darpan module integrated into the salary workbook.** Owner uploaded the three current files. Hash gate first (D172/D188): `staff_master.csv` = `f8f3a23908d2007ccdc1bd9af5e87725` — matches the S151 VPS pin exactly. `Darpan_Loan_System_v2_3.xlsx` uploaded as `38ebf991b7c8400c9366a7087bd851ad` vs delivery pin `dd6689e1…` — **MISMATCH, reconciled before any work**: structure proven identical to the delivered v2.3 (5 sheets; all 1,345 formulas; every cross-sheet reference internal to the Darpan sheet-set; May/Jun-2026 pre-entered; Apr-2026 C4 and Jul-2026 C7 still EMPTY as delivered; Loan Master settings all filled) — the byte change was an Excel open-and-resave, not an edit. `Salary_System_2026.xlsx` has no pin by design (owner-edited, F-31 non-repo) — accepted as owner-current. **Merge executed in the sandbox** (openpyxl, cell-by-cell with styles, number formats, column widths, row heights, the Perks-ledger data validation, tab colours, freeze panes, and the Schedule Card's print setup): 10 sheets, the 5 salary sheets first, the 5 Darpan sheets appended; zero sheet-name collisions; zero external links in either source (the re-save-destroys-links hazard did not apply); no charts/images. **Recalc: 1,496 formulas, 0 errors — and 1,345 + 151 = 1,496 exactly.** **27/27 self-checks passed**: every cell (formula string AND recalculated value) identical to source on BOTH halves; salary-side merges, freeze pane, widths preserved; Darpan yellow entry-cell fills preserved; DV carried. Delivered md5 **`3dfe5bea7a559740fc239323ecc85319`** (as-delivered pin; the live file's hash changes with every owner edit — the pin records what was handed over, not what the file must remain). Owner installed to `D:\clinic_salary\Salary_System_2026.xlsx` after backing up the prior file (`Salary_System_2026_BACKUP_preS152.xlsx`). The standalone `Darpan_Loan_System_v2_3.xlsx` is **RETIRED** (owner to archive, not delete, until next month's entry proves the merged file in real use).

**2. The "nothing updates" report — user habit, NOT a fault; no F minted.** Owner entered 0 in C4/C7 and reported Loan Master unmoved while a Perks entry updated fine. Reproduced exactly in the sandbox on the pinned merged file: entering 0s **works** — D4/D7 flip to SKIP, May flips to PAID (chain activation), and four Loan Master live-position rows change (interest-bearing outstanding, TOTAL, Skips-this-FY → 2, interest charged). Resolution arrived from the owner: the value registers only after pressing Enter (Excel edit-mode). Recorded because the diagnostic path is the lesson: **reproduce on the pinned artefact before touching anything** — the simulation cleared the workbook in one pass and located the fault outside it. Side-note now on record: with Apr+Jul both 0, Darpan's skips-this-FY = **2, at the permitted limit** — the next skip this FY auto-raises the recover-from-perks flag (D250 discipline working as designed).

**3. Backlog items 2+3 progressed.** Item 3 (commit `att_month_report.py` to the repo) — owner reports DONE; the **attendance dossier folder-digest re-pin still rides open** (cannot be recomputed without the folder; carried). Item 2 (post the notice) evolved into the day's main work — the notice went through four revisions as policy grew (see 4–7); **posting remains owner-side, still pending** at close.

**4. D252 LOCKED (chat label "D251") — the discipline package.** Owner edits to the drafted D249 notice, then two new deterrents designed interactively:
- Point-5 consequence reworded: every 3 late marks in a month — **one day shall be marked as half day** (attendance framing, not salary-deduction framing; consistent with D249's statutory caution).
- **Sunday-never-late rule REMOVED from the notice** (owner: "there will be anarchy") and then **removed from policy entirely** — Sundays are counted normally (computation change queued; supersedes the D249 "Sundays never late" engine rule, which D253's roster makes obsolete anyway).
- The blanket outstation line removed from the general notice (Darpan-only; lives in his workbook flow).
- Machine-record point strengthened: **all salary strictly on biometric records.**
- **Grace cap (anti-exploit):** the 10-minute grace is excused at most **8 days per month**; from the 9th such day, even ≤10 min late = 1 mark. (Owner spotted the exploit — a daily 9-minute habit would never earn a mark; cap = his instinct, 8 = agreed number.)
- **Uninformed absence = ₹50 fine** — explicitly corrective, not punitive ("for improving"), on top of the normal day's salary treatment; owner reversed the assistant's proposed default so that **default = informed; the owner flags only the uninformed** (less monthly work).
- **Monthly absence cap:** more than 3 absent days in a month = additional **₹100/day from the 4th day** (owner replaced the assistant's double-counting proposal — all monetary consequences are now fines; the salary-deduction logic stays untouched; the reward-forfeiture rider was dropped with it).
- **Habitual link:** crossing the monthly cap in **3+ months within a year = annual increment reduced/withheld at owner discretion** — the report tracks and flags; the owner decides. (Replaces the assistant's employment-review ladder; owner chose increment as the deterrent.)

**5. D253 LOCKED (chat label "D252") — the Sunday roster.** Owner's own design, analysed and refined: **Group A** (Shivani · Awdhesh · Pravesh · Darpan) full duty 1st & 3rd Sundays; **Group B** (Alisha · Shavez · Ranjeet · Sukhveer) full duty 2nd & 4th; each group's other Sundays fully off. **Group C** (Sandip · Vikki · Surendra — collections; owner set C at 3, not the earlier 4) stays on the old system — every Sunday half-day — for role constraints; **Arjun (cleaner) continues as before** on the same pattern, recorded separately from collections. **5th Sunday = normal full working day for everyone** (owner overrode the assistant's half-day suggestion). Cost-neutrality proven in-session: 2 full Sundays worked = the same 2 day-equivalents as 4 half-Sundays; the 2 monthly offs are repositioned, not added — plus 2 discretionary leaves unchanged. Coverage analysis accepted: reception alternates perfectly; pathology 3-deep every Sunday; **Shavez backs up clinic on B-Sundays; pharmacy stays CLOSED on Sundays** — which makes Darpan's A-Sundays his pharmacy-housekeeping days and leaves his rotation/off pattern untouched. Swaps: mutual exchange only, with prior information. On-duty Sunday = every rule applies; off Sunday = nothing counted. **Effective 01-09-2026** (August runs as-is; roster posted early so groups can plan). Roster CSV received from owner (groups verified; salary/timing columns untouched under F-46 whitelist — only name/department/group read).

**6. D254 LOCKED (chat label "D253") — the leave register defines "informed."** Problem: staff post leave messages in the WhatsApp group without approval, sometimes on the duty day itself; reminders have failed. Owner's notebook idea adopted and hardened: **bound, page-numbered register at reception** (entry date · name · leave dates · reason · approver initials); entry by the previous working day; **approval = owner's/Dr Bhawna's initials**; **emergency channel = a phone call**, entered on return marked emergency. **The teeth: absence is "informed" ONLY via register-approval or emergency call — a WhatsApp message alone ≠ informing → the D252 ₹50 applies.** Non-compliance needs **no new fine**: the fine attaches to the absence, never to the message (no double-punishment, no chat-etiquette fines). Boundary rulings recorded: unauthorised group post + came to duty = no fine (the register makes the group officially weightless); a timely register entry the owner never initialled = informed (the staff member did the compliant act; initials decide sanctioned/unsanctioned, not the ₹50). **Transition: first two weeks = verbal warning only.** Owner-side: buy the notebook, rule the columns.

**7. The notice lineage (one print artefact, four revisions, all delivered as docx + rendered-page verified):** v2 (8 points; owner's four edits to the D249 draft) `b25308cc38d7617edf220c69921b66af` → v3 (11 points; + D252 fines/grace-cap) `eb173bea39d46670fa6a34af88a7750a` → v4 (15 points; + D253 Sunday system with named groups) `fe32fb193ae5ed89e0bc1a0c6a46b399` → **v5 FINAL (16 points; + D254 register rule) `f2de5527385800c3122cd0209d32fb67`** — one A4, bilingual (Nirmala UI Hindi + Arial English), signature/date block. v5 is the standing master. **A 3-phase soft launch was then proposed** (P1 now: continuity + reward + register-in-warning-mode, grace uncapped for August; P2 ~25 Aug effective 1 Sep: fines + grace cap + register binding + Sunday roster + tightened reward; P3 ~1 Oct: the habitual→increment clause alone) on the principles *carrot before stick* and *never announce a rule before the machinery can enforce it* — **proposed, NOT yet approved**; the owner moved to new scope. If approved, three short posters replace the dense v5 on the wall; v5 stays the internal reference.

**8. D255 DRAFTED (chat label "D254") — the Staff Management System.** Owner's requests in sequence: document occasional-money items (uniform/ID-card compliance fines, night-duty payments, ad-hoc fines) in the KB as policy; a long-term appraisal framework from monthly data + owner-only columns; staff advances auto-recovered as salary instalments; then — the owner's own leap — **a maker-checker data-entry system "as in banks"**; and finally the recognition that **attendance has evolved into a Staff Management System**, absorbing the dress/ID issuance log Shavez keeps manually in a Google Sheet. Draft design recorded (full build spec at build session): **(a)** one Monthly-Adjustments ledger — every non-base rupee is one categorised row; salary formula = base − attendance deductions + reward + payments − fines − advance instalment; **(b)** Staff Advances sheet — amount + instalment in, auto-declining balance, stops at zero; **(c)** Appraisal — auto spine (marks, grace days, absences, Sunday compliance, punch-out misses, fines, reward) + owner ratings 1–5 QUARTERLY (courtesy · quality · teamwork · uniform/hygiene · cash-handling for collections staff); year-end 50/50 → increment recommendation — exactly where D252's habitual clause plugs in; **(d)** **maker-checker on the VPS attendance dashboard** (F-31: staff money data never in Drive; HTTPS+auth+ntfy already exist): maker enters (Shavez proposed, unconfirmed) → PENDING → checker (owner; Dr Bhawna delegable) approves/rejects by phone tap; **approved rows append-only, corrections by contra entry**; maker+checker+timestamps on every row; maker's own-name entries flagged; monthly close emits one approved-adjustments file into the salary computation; **(e)** **issuance & entitlement registry** — dress/ID issues become maker categories (usually ₹0; chargeable replacements auto-deduct); entitlement flags ("last dress issue 14 months ago"); **rationale recorded: a compliance fine is defensible only when the system can prove issuance** — one chain issuance→compliance→fine→salary; one-time import of Shavez's existing Google Sheet as opening history, then the sheet freezes read-only as archive. **Pending owner inputs: the rate card** (uniform/ID fine ₹ · night-duty ₹ · ID-replacement charge ₹ · dress entitlement cycle · default advance-instalment rule) **+ maker confirmation + phase-split approval.** Build order locked: (1) phased notices + the report-script change **before 01-09**; (2) the Staff Management module + workbook v3 **before the 01-10 salary run**; (3) appraisal sheet, no deadline.

**9. Queued code change (single tested drop, deadline 01-09, before the August run):** `att_month_report.py` — count Sundays per the D253 roster (new `sunday_group` column in `staff_master.csv`: A/B/C-pattern; on-duty Sundays normal, off Sundays nothing counted; 5th Sunday normal for all); grace-cap logic (marks from the 9th grace day); absent-dates listing per person + the informed/uninformed flag loop (default informed; owner flags exceptions; checked against the register); fine lines (₹50 × uninformed + ₹100 × max(0, absent−3)); habitual tracker (months-over-cap per person per year, flag at 3). Offline build with **synthetic punch fixtures** — real punch data stays off the sandbox (F-31).

**10. Records & housekeeping.** Notion connector **absent again** — the S151 catch-up now carries two sessions (S151+S152). Drive delivery unchanged (present_files drag-drop). No Gmail health note (no manual health check; automated digest live). No GitHub commit owed (no code changed this session). **A live-state conflict noticed while re-reading the record, logged for verification, not resolved:** Register changelog v1.59 (S133) records `wa_approve` → systemd DONE ("the last bare-nohup in the clinic is gone"), yet Runbook v89 §2 carries "wa_approve nohup → systemd (overdue)" — one of the two is stale; **verify `systemctl status` on the VPS before acting either way** (manifest rule: if a pending item looks done, verify against reality first). Cold kit not rebuilt (last at S151, one session ago — not overdue per EOS §E).

### Decisions minted this session

- **D252 — Attendance discipline package, effective 01-08-2026 (amends/extends D249; chat label "D251").** Grace: ≤10 min after own shift start excused at most **8 days/month**; from the 9th such day even ≤10 min = 1 late mark. Marks scale unchanged (>10 = 1, >30 = 2); every 3 marks/month = one day marked half-day (reworded from "salary deduction"). **Sundays counted normally** (the D249 "Sundays never late" engine rule is revoked; the D253 roster governs who is on duty). **Uninformed absence = ₹50 fine**, corrective framing, atop normal absence treatment; informed/uninformed default = **informed**, owner flags exceptions. **>3 absent days/month = additional ₹100/day from day 4** (replaces double-counting; no reward forfeiture). **Habitual: monthly cap crossed in 3+ months in a year = annual increment reduced/withheld at owner discretion** — machine flags, owner decides. Fines are announced only when the computation can enforce them (effective with the September-run script).
- **D253 — Sunday duty roster, effective 01-09-2026 (chat label "D252").** Group A (Shivani, Awdhesh, Pravesh, Darpan) full duty 1st & 3rd Sundays; Group B (Alisha, Shavez, Ranjeet, Sukhveer) 2nd & 4th; other Sundays fully off. Group C (Sandip, Vikki, Surendra — collections, 3 not 4) + Arjun (as-before, non-collections) stay on every-Sunday-half-day. **5th Sunday = normal full working day for all.** Pharmacy closed Sundays (Darpan's duty Sundays = pharmacy housekeeping); Shavez backs up clinic on B-Sundays. On-duty Sunday = all rules apply; off Sunday = nothing counted. Swaps mutual + prior information only. Cost-neutral by construction (2 full Sundays ≡ 4 half-Sundays); 2 discretionary leaves unchanged. Implementation: `sunday_group` column in `staff_master.csv` + roster logic in the monthly report.
- **D254 — The leave register defines "informed" (chat label "D253").** Bound page-numbered register at reception (entry date · name · leave dates · reason · approver initials); entry by the previous working day; approval = owner/Dr-Bhawna initials; emergency = a phone call, register entry on return. **Absence is informed ONLY via register-approval or emergency call; a WhatsApp message alone ≠ informing → D252's ₹50 applies.** No separate non-compliance fine — the fine attaches to the absence, never to the message. Unauthorised group post + attended duty = no fine. Timely entry left uninitialled = informed (initials decide sanctioned, not the fine). First two weeks after posting = verbal warning only. The WhatsApp group carries zero official weight for leave.
- **D255 — Staff Management System (DRAFT — design locked in outline, build pending; chat label "D254").** Attendance is renamed/reframed as one module of a Staff Management System on the VPS dashboard. Components: Monthly-Adjustments ledger (every non-base rupee = one categorised row feeding the salary formula) · Staff Advances (auto-declining instalment recovery) · Appraisal (auto spine + quarterly owner ratings, 50/50 year-end → increment recommendation, hosting D252's habitual clause) · **maker-checker entry** (maker proposes — Shavez pending confirmation; checker approves by phone tap — owner, Dr Bhawna delegable; approved rows append-only with contra-entry corrections; full maker/checker audit stamps; own-entry flagging; monthly close emits one approved file into salary) · **issuance & entitlement registry** (dress/ID issues as maker categories; chargeable replacements auto-deduct; entitlement-due flags; a compliance fine is defensible only when issuance is provable; one-time import of the existing Google Sheet, then frozen read-only). Pending: rate card (uniform/ID fine · night duty · ID replacement · dress cycle · default instalment rule), maker confirmation, phase-split approval. Deadlines: report script 01-09; module + workbook v3 before the 01-10 run; appraisal unpressured.

**Findings: none raised (the tracker report was user habit; the wa_approve conflict is a verification task, not yet a finding). Next free decision: D256. Next free finding: F-47.**

---

**END OF KB HISTORY ARCHIVE v1.4. §S152 is the last section; §S151, §S150, §S149, §S148 and §S147 sit above it. If §S152 or this marker is absent, this file is truncated and must not be used as canonical.**

---

## §S153 — 2026-08-07 — Attendance discipline build-out: notice v6, rate card, report v2→v2.5, punch-pattern discovery

**Narrative.** Backlog TOP executed end-to-end. Owner iterated the D252/D253 attendance notice to **v6 FINAL** (bands stated per episode, Option-B slab deductions, OT at double rate, swap-in-register rule, leave-register live date; two-week-warning line ruled OFF the poster). Staff **rate card v2** produced (30-day basis, Arjun excluded). `att_month_report.py` rebuilt as an additive layer on the frozen attendance core through six tested versions in one session (v2 → v2.5), each selftested (40+ checks) and most verified against real July data. July processing surfaced a genuine finding: huge "early departure" figures were **double-punch artefacts** (accidental second morning punch + no evening punch-out) — staff essentially never punch out. Fixed by a three-tier early-departure model. July ruled **diagnostic only**; August 2026 is the first billing month. The v2.4 HTML pack (grid + policy legend + ruling sheet) verified on real data; v2.5 (owner's final legend wording + incentive/net money columns) delivered, **install pending**.

**D256 — Attendance discipline computation rules (consolidated, owner-ruled S153; amends D252/D253):**
(a) Late bands per episode: ≤10 min grace (max 8 days/month; beyond cap ≤10 min = 1 mark), 11–29 min = 1 mark, 30–59 = 2, ≥60 = 2 informed / 3 uninformed (informed-flag via review file checked against the reception register).
(b) Deductions, Option B slabs: half_days = floor(max(0, marks − half_limit)/3); half_limit 8 for Aug-2026 (ramp), 5 from Sep-2026. **Sept-strict correction:** notice v5/v6 point 6 (strict from September) overrides the S151 code's Aug+Sep ramp — the posted notice is the staff-facing law.
(c) Incentive: FULL = 1 day's salary (salary÷30), HALF = half day (salary÷60); tiers ≤5/≤8 (Aug), ≤2/≤5 (Sep+).
(d) Overtime: double the per-minute salary rate (rate = salary÷(30×weekday shift minutes)), computed by minutes; **doctor approval + machine punch-out compulsory**; report lists candidates only — nothing auto-pays.
(e) Early departure, three tiers: last punch within 30 min of first = **double-punch artefact** → duty presumed done, no deduction, no OT; gap ≤120 min before shift end = auto-deduct at 1× rate; gap >120 min = **EARLY_BIG** — printed on the ruling sheet with punch times and deductible amount, never machine-applied; owner rules against the physical register.
(f) Single punch = presumed stayed till end of duty (no deduction, no OT).
(g) Salary basis: 30-day month (owner ruling).
(h) Arjun (cleaner): minutes-exempt — presence/absents only.
(i) **Net = incentive + OT − (marks deduction + early-dep deduction + fines)**; OT included by default per owner; net shown signed, green/red.
(j) Sunday swap (amends D253): mutual consent + prior information **+ written register entry, both staff sign, doctor countersigns**.
(k) July 2026 = diagnostic only; first billing month Aug-2026. Early departures now logged in the physical register.
(l) Leave/absence register live from 06-08-2026 (notice point 16).

**F-47 — Biometric double-punch artefact.** An accidental second punch minutes after arrival (staff fearing they forgot to punch) defeats any "single punch = full duty" presumption and reads as a massive early departure (observed: 540–722 min across 6 staff, Surendra ×10 days). Detection: last−first ≤ 30 min. Lesson: punch-pair semantics must be classified before money math; a punch count is not a departure record.

**F-48 — Unobserved build-path write (shadow apply).** A create_file attempt errored "file exists" while a parallel/earlier variant of the same patch had already been written AND applied to the build artefact; a later guarded patch then failed its anchors (already consumed) while new selftest guards passed. Resolution discipline: on any unobserved edit path, halt and **diff-audit against the last verified md5 before shipping** (done; all changes in-scope). Lesson: verify by content, never by the sequence of one's own actions.

**Artefact pins (S153):**
- D252_Attendance_Notice_v6_FINAL.docx **b29dfa1317024d1d622d79d6de6f5c17** (PDF ca8216b3aec281a492eb7e7d9c25a6fe) — supersedes v5 f2de5527…
- Staff_Rate_Card_v2_S153.xlsx **8e9cf6462d63b9d229bcbf973d25f88c** (v1 d690a528… discarded; 11 staff, ÷30, day-rate/half-day/per-min/OT columns)
- staff_master.csv v2 **3b1ebcb1e339fdcdb8b47389ee206108** — +sunday_group (A: Shivani, Awdhesh, Pravesh, Darpan · B: Alisha, Shavez, Ranjeet, Sukhveer · C: Sandip, Vikki, Surendra · ARJ: Arjun) +minutes_exempt (Arjun) — **INSTALLED on VPS**
- att_month_report.py lineage: v2 d293f822 (installed) → v2.1 8fb21d69 (installed) → v2.2 6116fca0 → v2.3 6d50e7a8 → v2.4 **608f2a90bf9ff65f196ac4f2f13c00bb** (**INSTALLED; July rerun verified**) → v2.5 **e64cad19d135618dec1413553e6bdc80** (**delivered, install pending**)
- July outputs regenerated on VPS (salary_inputs_2026-07.*, deductions_extras_2026-07.csv, review_2026-07.csv with informed=Y defaults, owner-editable)

**Shift-time reality flags carried to the workbook pass:** Sandip start (S151 open item), Shivani end (OT300/318 pattern), Alisha start (near-daily L26–L81 vs her arranged timing).

*Sunday-roster note:* pre-Sep months follow sun_start/sun_end columns; roster (groups/5th-Sunday) governs from 2026-09 (ROSTER_FROM).


---

## §S154 — 2026-08-07 — v2.5 install verified · shift-times ruled as-recorded · roster columns loss-proofed · Staff Ledger maker-checker BUILT AND LIVE (D257)

**Narrative.** Phase 0 clean (20/20 manifest rows md5-verified; zero mismatches). Backlog items 1, 3 and 5 executed end-to-end; item 2 (notice v6 posting) owner-confirmed done.

**1. Item 1 CLOSED — `att_month_report.py` v2.5 verified INSTALLED.** Owner's VPS transcript: md5 `e64cad19d135618dec1413553e6bdc80` exact, `--selftest` PASSED (40+), July 2026 rerun clean (figures consistent with the S153 diagnostic: Sukhveer 31/31 no-out-punch, Shivani 1,100 OT-candidate min, Arjun FULL / Sukhveer HALF, EARLY_BIG only Pravesh 28-07 + Shavez 12-07), browser layout of the three v2.5 additions (Incentive Rs money, signed coloured Net Rs, adjacent OT columns) confirmed. Repo commit of v2.5 owed.

**2. Item 3 CLOSED — workbook shift-time reality pass, ruled with ZERO edits.** Assistant's evidence brief corrected two of its own S153 framings against the real grid: Sandip's start was already 09:00 in the v2 CSV (the S151 08:00 question had been silently resolved); Shivani's 1,100 OT minutes are 4 specific long days (10/12/16/19 Jul to ~20:00–21:18), not a wrong shift end. The one genuine recorded-vs-real divergence was Alisha (recorded 11:00, arrives ~11:30–11:50 daily). Owner ruled all four **keep as recorded** — Sandip 09:00, Shivani 08:00, Alisha 11:00, Shavez 09:00: the recorded times are the law; August billing judges behaviour against them under notice v6. Deliberate, recorded, closed.

**3. Item 3 second half — the roster columns are now loss-proof end-to-end.** (a) Assistant edited the owner's live salary workbook in the sandbox (openpyxl; pre-flight proved no charts/images/external links/macros): headers `sunday_group`/`minutes_exempt` at I2/J2 styled from the existing header row, 12 rows filled per the S153 roster, Amir Sohail (no emp code) left blank. Collateral audit: recalc 1,496 formulas 0 errors; full 10-sheet cell diff — 0 formula-string changes, 0 value changes beyond cached-float precision (LibreOffice 15-digit vs Excel 17-digit rewrite, cosmetic); exactly the 26 intended cells written. As-delivered md5 **`a8625fd810477765dd9b6dd2678e7d86`** (v4 lineage; F-31 workbook, hash drifts with owner edits by design); owner installed to `D:\clinic_salary\`. (b) **`build_staff_master.py` v2** (`9fe81d7b75cdefb387206883b20cbb1e`): carries both columns, locates them by header name, REFUSES to run (writes nothing) if either column is missing or any value invalid — the column-dropping rebuild is now impossible; prints a group/exemption eyeball summary. (c) **Round-trip proof twice**: sandbox (workbook+columns → script → CSV byte-identical to installed VPS v2 `3b1ebcb1e339fdcdb8b47389ee206108`) and then on the owner's PC (certutil = `3b1ebcb1…` exact) — nothing to upload; the pipeline reproduces live reality byte-for-byte. (d) Novice SOP shipped for future staff edits: `Staff_Master_Update_SOP_v1_S154.docx` `363522474974b03a1a5893bc0526f280` (2-page A4: golden rule, column guide A–J, rebuild, WinSCP + two-sided md5 match, never-do list incl. F-31 in plain words) — lives in `D:\clinic_salary\`.

**4. Item 5 CLOSED — the D255 maker-checker module designed, built, installed, LIVE (D257).** Owner rulings collected in-session (full decision text below): two makers with tiered access (Shavez full, Alisha limited), doctors as checkers AND direct enterers, ad-hoc fines doctor-only with mandatory narration, rate card ₹20/₹20/₹200/₹100, fines per day, advances default full-current-month recovery with per-advance instalment override, individual swappable password logins. Build: **`staff_ledger.py`** single-file Flask app + admin CLI + monthly close + selftest, offline with synthetic fixtures only (F-31). Lineage v1.0 `fce4631a40d395d2d19bd0896ede539e` (selftest 38) → v1.1 `3b44c46b…` (category-adaptive entry form: fields reshape per category, live red/green amount preview, narration visibly optional except ad-hoc/other; 41 checks) → **v1.2 `478c02984dbb30a330375e3f5899ff97` INSTALLED (42 checks)** adding a show-password toggle at login (reveals own typing only; stored passwords remain salted-PBKDF2 hashes — D176 upheld). Selftest coverage: password round-trip + wrong-pw rejection, every rate computation, role fences both directions, forced narration, self-flag, approve/reject stamps, maker-cannot-decide, no double decision, contra rules (approved-only; doctors direct; makers pend; part-recovered advance blocked), advance default + instalment declining balance, month close (auto instalment rows, per-rupee CSV math, advance payout excluded from salary summary, re-close refused), web smoke (login, 403 fences, out-of-role block, adaptive-form metadata per role, toggle present). **VPS install owner-executed stepwise, each step verified from pasted output:** md5 exact + selftest 42 PASSED on VPS · four users created (`shavez` maker_full/link Shavez · `alisha` maker_limited/link alisha (case-insensitive match) · `manoj` checker · `bhawna` checker) — one earlier `bhawna` attempt with role maker_full was DISCARDED by the password gate before saving (the fail-safe worked); `listusers` verified all four · `staff-ledger.service` (systemd, enabled, Restart=always) active, curl 200 on 127.0.0.1:8043 · web tier DISCOVERED not assumed — no nginx on the box; **OpenLiteSpeed** terminates 443; attendance vhost read (`extprocessor att8042` + context `/` proxy); guarded python edit (assert-once anchor, abort-if-present) inserted `extprocessor ledger8043` (127.0.0.1:8043) + `context /ledger` into the attendance vhost, backup **`/root/vhost.conf.BACKUP_S154`** taken first; `systemctl restart lshttpd`; verify attendance **302** (normal login redirect, untouched) + ledger **200** over HTTPS. **Phone check OK** (v1.0), owner UX feedback drove v1.1/v1.2, reinstall verified (md5+selftest 42+restart). Live URL: `https://attendance.dr-manoj.in/ledger`. NTFY_URL not set — pings off, Pending page is the truth (wiring = backlog). Frozen attendance core untouched throughout (additive, same sanction pattern as the report layer). Briefing note for the makers shipped: `Staff_Ledger_Briefing_v1_S154.docx` `cf07e468cb737c9a80e42e8096739ac0` (one A4 bilingual: URL, per-person permission table, dates-only entry, PENDING-until-approved, contra-never-edit, self-flag normal).

**5. Dress/I-card sheet PARKED by owner.** `DRESS ICARD NAME.xlsx` located in Drive (id `106jbhv…`, Shavez's manual fine/issuance log — exactly D255(e)'s Google Sheet); owner deferred: "we make our own system for logging these entries" (now live as ledger categories) and will upload the sheet later for one-time import as issuance-registry opening history, then freeze (D255(e) unchanged).

**6. F-49 raised at EOS — latent F-31 leak path.** The owner's certutil transcript shows `build_staff_master.py` (and therefore its output `staff_master.csv`) living in `D:\dr-manoj-git\drmanoj-clinic-automation\attendance\` — inside the git working tree. A routine GitHub Desktop commit could sweep live salary data into the public repo. RULE: `.gitignore` the file BEFORE the next commit (git kit ships the helper); standing rule — no salary-bearing generated file may sit un-ignored inside a git working tree.

**7. Records.** Notion tools ABSENT a fourth consecutive session — catch-up now spans S151–S154. Drive: read-only use (file discovery + workbook download); delivery via present_files as established. No incident. No Tier-1 spec changed. No Tier-2 waiver (workbook is F-31 owner-side, not a manifest row; attendance frozen core byte-untouched — ledger and builder are additive/companion files).

### Decision minted this session

- **D257 — Staff Ledger maker-checker, BUILT (implements D255(d) plus the ledger/advances slices of D255(a)(b); owner-ruled S154).** Two maker tiers: **maker_full** (Shavez — night duty, uniform fine, I-card fine, approved leave, I-card replacement, advance issue) and **maker_limited** (Alisha — approved leave, uniform fine, I-card fine; no replacement). **Doctors (Manoj, Dr Bhawna) are checkers AND may enter directly** — checker entries save as DIRECT (auto-approved, fully audit-stamped). **Ad-hoc fines are doctor-only** with mandatory free-text narration; narration optional everywhere else. **Rate card locked:** uniform ₹20/day · I-card ₹20/day · night duty ₹200/night · I-card replacement ₹100 · fines accrue per observed day. **Advances:** default = full recovery in the current month; per-advance ₹/month instalment override; auto-declining balance; recovery stops at zero; the payout is a cash event excluded from the salary summary — only recovery instalments enter salary. **Bank discipline:** approved rows append-only; corrections by contra entry only (makers' contras pend, doctors' are direct; contra of a part-recovered advance refused — adjust instalments instead); every row stamped maker/checker/both timestamps; a maker's own-name entry auto-flags red. **Access:** individual username+password per person (salted PBKDF2, min 6 chars, show-password toggle reveals own typing only); any login swappable anytime (deluser+adduser). **Monthly close** (checker-run, re-close refused): generates the month's advance-instalment rows, stamps all approved rows closed, emits `approved_adjustments_YYYY-MM.csv` (per-staff credits/debits/net/approved-leave-days + full detail) for manual entry into the salary workbook — nothing auto-pays. **Data residency:** `/root/staff_ledger/` (ledger.jsonl, users.json, secret_key, monthly CSVs) chmod 600, F-31 — never Drive, repo, or chat. **Plumbing:** additive standalone app (frozen attendance core untouched), `staff-ledger.service` systemd, OpenLiteSpeed `extprocessor ledger8043` → 127.0.0.1:8043, `context /ledger` on the attendance vhost → live at `attendance.dr-manoj.in/ledger`.

### Finding minted this session

- **F-49 — Salary-bearing build output inside the git working tree (latent F-31 leak).** `build_staff_master.py` writes `staff_master.csv` beside itself, and the owner runs it in the repo's `attendance\` folder — one unguarded GitHub Desktop commit away from publishing staff salary data. FIX (first backlog item): add `attendance/staff_master.csv` to `.gitignore` before any commit. RULE: generated files carrying salary/staff data must be git-ignored or produced outside the working tree; F-31 compliance is enforced by configuration, not by remembering.

**Artefact pins (S154):** `Salary_System_2026.xlsx` as-delivered **`a8625fd810477765dd9b6dd2678e7d86`** (v4, +2 roster cols, owner-installed) · `build_staff_master.py` v2 **`9fe81d7b75cdefb387206883b20cbb1e`** (owner PC repo folder; commit owed) · `staff_master.csv` UNCHANGED `3b1ebcb1…` (round-trip proof ×2) · `Staff_Master_Update_SOP_v1_S154.docx` **`363522474974b03a1a5893bc0526f280`** · `staff_ledger.py` **v1.2 `478c02984dbb30a330375e3f5899ff97` INSTALLED** (v1.0 `fce4631a…`, v1.1 `3b44c46b…` superseded) · `staff-ledger.service` enabled · OLS vhost edited, backup `/root/vhost.conf.BACKUP_S154` · `Staff_Ledger_Briefing_v1_S154.docx` **`cf07e468cb737c9a80e42e8096739ac0`** · `att_month_report.py` v2.5 `e64cad19…` **INSTALLED S154**.

**Next free decision: D258. Next free finding: F-50. Next session: 155.**

---

## §S155 — 2026-08-07 — D258 executed: the Staff Ledger becomes the single home for all staff money; Darpan loan migrated live; repo trim ruled + pushed; digest recipe rediscovered

**Narrative.** A FULL build session in two acts. **Act 1 (housekeeping backlog):** F-49 CLOSED by owner ruling — the repo's long-standing blanket `*.csv` gitignore line IS the enforcement (verified live: `staff_master.csv` 404 on GitHub; no explicit line added); the S154 three-file commit verified byte-exact by raw-URL md5; NTFY wiring and the dress/I-card sheet import DROPPED by owner; the **folder-digest recipe was REDISCOVERED empirically** — it had never been written down — as `md5sum <folder>/* | sort | md5sum` from the repo root, proven by exact reproduction of the S147 pin `dc12f4a0…` on the freeze-time attendance folder reconstructed from git history (`build_staff_master.py` v1 `d7e0110c…` recovered from commit `e00c30ff`); new pins computed — `attendance/` (11 files) **`c4c9c83f44fbbbb39609047671e77d60`**, `clinic_writer/` (7 files, v28 confirmed already in the repo) **`1b4f0f2299cd6c9e72b6d04f45847556`**, font TTF first-pin `f4ae6809…`; the S149 Fault-Register push carry discovered ALREADY DONE (repo byte-identical); the **Phase-2 trim ruling** delegated to the assistant and executed — KEEP the 6 staff-facing docs in `docs/`, ARCHIVE 4 to `canonical-docs/historical/`, `git rm` 2 byte-identical duplicates — via `Repo_Trim_Phase2_Ruling_S155.ps1` (md5-pinned, dry-run-default, collision-guarded; v1 broke on PowerShell 5.1 ANSI-decoding of non-ASCII dashes → v2 rebuilt pure-ASCII and byte-scanned — LESSON: Windows-PowerShell deliverables must be pure ASCII or UTF-8-BOM); a pushed-nothing mystery diagnosed as commit-without-push (LESSON: GitHub Desktop's "Push origin" ↑count is the truth); final state verified on live HEAD. Repo `canonical-docs/` mirror noted one session-set stale with ~15 superseded root strays (folds into the next doc push).

**Act 2 (owner-directed, the day's centre): D258 minted AND executed.** The post-S154 ruling — all day-to-day money events including Darpan's enter the Staff Ledger under the doctor's DIRECT login — was extended live by the owner to its logical end: **the structured loan itself moves in-app and the workbook's Darpan sheets retire**. The owner uploaded the live workbook under an explicit scoped F-31 waiver so the loan logic could be read exactly; reading it caught a REAL model error before any rupee moved — the v2.0–v2.2 engine charged interest ON TOP of the instalment, while the workbook's Repayment Tracker proves the **instalment IS the whole monthly deduction and the Rs 1,000 interest comes OUT of it**, with a true waterfall (interest → interest-bearing principal → interest-free principal) overflowing ACROSS tranches within the same month, interest stopping the moment the interest-bearing tranche clears, and a SKIP month recovering nothing while Rs 1,000 capitalises. Record corrections from the artefact: skips this FY = **1 (2026-04 only)** — the earlier "Apr+Jul both skipped" note belonged to the retired standalone workbook; perks lifetime = **Rs 19,000** after the owner ordered a Rs 1,000 test row deleted (guarded openpyxl edit, recalc 1,496 formulas 0 errors, workbook md5 → `a0e3b038f2a3fd55b64fdb8db049dadc`). Owner ruled July salary clears AFTER go-live — so the migration carries as-of-June balances and **the ledger's first close IS July**.

**`staff_ledger.py` v1.2 → v2.4** in five installed, individually md5+selftest-verified versions:
- **v2.0** — per-staff STATEMENT view (checkers any staff; makers locked to their own `staff_link`, URL override blocked); interest-bearing advances; skip machinery (2/FY Indian-FY counter, historical months recordable for migration); running salary net computed under the identical rule-set as the monthly close (proven equal in selftest — the two can never disagree).
- **v2.1** — **F-50 raised by the owner live and fixed**: `ROLE_CATS["checker"]` was `list(CATEGORIES.keys())`, so adding the v2.0 system categories silently put machine-only rows in the doctor's entry dropdown; RULE MINTED: **a role's powers are explicit lists, never derived-everything from a growable structure**; PERK category added (doctor-only, narration required, salary-EXCLUDED cash-benefit record); statement Account-summary box (perks total/count · instalments paid · interest paid · both tranche balances · FY skips with months).
- **v2.2** — `migrate-loan` guided CLI (figures typed on the VPS only, F-31-clean); IDEMPOTENT (any open advance refuses a rerun — mutation-proven).
- **v2.3** — the workbook-exact waterfall-budget engine (above); migration reshaped to ONE instalment + perks brought-forward; **an atomicity fault in migrate_loan caught by the session's own mutation-testing BEFORE install** (validation ran after the first append — in an append-only ledger a failed call left orphan state) → validate-before-append rule implemented and selftested; **v2.3.1** one-line perk parser after the owner's natural "narration / amount" input tripped the two-prompt flow (the atomicity rule protected him live — the failed run appended nothing).
- **v2.4** — live-position strip on the entry form (selected staff's tranche balances + FY skips, checker-only — maker privacy mutation-proven as two-gate defence in depth); Rs-0 advance refused with guidance to the Skip button (killing the workbook's type-0-to-skip habit); case-insensitive staff names in migration (the live `darpan` trap).
Selftest 42 → **123**; ~15 deliberate mutations across the session, each either caught by a named check or proven a non-fault by an independent second gate. **Engine proven against reality twice**: full-history replay 190,000/180,000 → skip Apr → May → Jun reproduced the workbook LIVE POSITION to the rupee (183,000 / 180,000 / interest 2,000 / skips 1 / perks 19,000); July rehearsal produced the exact go-forward numbers.

**Migration EXECUTED live (owner, VPS):** verification block exact (183,000 / 180,000 / 1 skip 2026-04 / 19,000) → **`close 2026-07`** run → Darpan July line **−5,000** (1,000 interest + 4,000 principal), loan → **179,000**; phone Statement confirmed all figures + both school-fee perks named. Post-close ledger audit (category/status listing, amounts withheld) found 8 rows = the expected 7 + one pre-migration **Shivani ad-hoc test fine (owner's 13:50 tap)** — contra instruction issued (reverse via Full-ledger form; ignore her line when entering July salary; nets in the August close). **Workbook moved to its new canonical home `/root/clinic_salary/Salary_System_2026.xlsx` on the VPS** (chmod 700/600, md5 verified) with the PC copy replaced; monthly loop = download → salary entry → upload — explicitly TEMPORARY, see the S156 mandate.

**Decisions minted this session**

- **D258 — One home per rupee: the Staff Ledger owns ALL staff money, structured loans included (owner-ruled S155; supersedes the S154 evening draft's workbook/ledger split).** Every money event for every staff member — perks, fines, advances, night duty, AND the structured Darpan-type loan (principal, flat Rs 1,000/month interest, skips, capitalisation, waterfall recovery) — lives in `staff_ledger.py` on the VPS. The doctor enters Darpan's events under his own DIRECT login; loan repayment is NEVER typed — the monthly close generates it; a skip is the Advances-page button, never a Rs 0 entry. Engine semantics are workbook-exact (proven by full-history replay): monthly deduction = min(instalment, everything owed); allocation interest → interest-bearing principal → interest-free principal with same-month overflow; interest stops at tranche clear; skip = no recovery + Rs 1,000 capitalised + max 2/Indian-FY. The salary workbook's Darpan sheets (Loan Master · Repayment Tracker · Schedule Card · Perks & ST-Advance Ledger · Outstation Log) are **RETIRED as of the verified live migration (07-08-2026)** — frozen history, never filled again; the workbook keeps only salary computation, fed one net line per staff from the close CSV. Workbook canonical home = VPS `/root/clinic_salary/` (F-31), PC copy = working copy. Migration was atomic, idempotent, and verified against the workbook LIVE POSITION to the rupee before retirement.

**Finding minted this session**

- **F-50 — Derived-everything role powers (raised by the OWNER live on v2.0; fixed v2.1).** The checker role's enterable categories were computed as `list(CATEGORIES.keys())`; when v2.0 added machine-only system categories (instalment/interest/capitalise/skip) the doctor's entry form silently inherited them — a checker could hand-type a loan-interest row. The selftest never probed the checker's dropdown for ABSENCE. RULE: **a role's powers are an explicit allow-list, never derived from a growable structure**; every power-set gets a negative selftest (what must NOT be there). Fixed with explicit lists + F-50 probes; regression mutation-proven. Kin of F-49's lesson: enforcement by construction, not by memory.

**Records & housekeeping.** Notion tools absent a FIFTH consecutive session — catch-up now spans S151–S155. Drive: read-only (uploads read; delivery via present_files). Gmail health note skipped per EOS §B (no manual check; automated digest live). GitHub commits owed: `staff_ledger/staff_ledger.py` v2.4 `74dac84eb15f5172478a97066f56c99d` + the canonical-docs mirror refresh (one session-set behind + ~15 root strays). Two additional lessons banked: PowerShell-5.1 ASCII discipline; a mutation must break the ACTUAL protective gate (a survived mutation against one gate of a two-gate defence is a weak probe, not a fault). **Owner mandate for S156 (TOP JOB): full backend salary automation — no manual Excel entry, no monthly workbook upload; the VPS computes salaries end-to-end (attendance report × ledger close × staff master) and the workbook demotes to read-only reference or retires.**

**Findings: F-50 (raised + fixed same session). Decisions: D258. Next free decision: D259. Next free finding: F-51.**

---

## §S156 — 2026-08-07 (Session 156, FULL — backend salary automation D259 minted+executed; F-51/F-52/F-53 minted; staff_ledger v2.4 → v3.1 live; salary report = vetted attendance HTML + salary layer; watchdog guards staff-ledger)

**Narrative.** The S156 top mandate delivered end-to-end in one session, plus the F-51 UI-safety batch that the session's own opening incident demanded.

**Act 0 (opened before the build — owner phone work on the live ledger).** The owner reported he had pressed the red **contra** button **four times** on the pre-migration Shivani test fine (1 fine + 4 contras) because the button fired with no confirmation, and separately worried Darpan's July showed "skipped." Both resolved from a phone screenshot: Darpan was CORRECT — the "skipped" row was the legitimate **2026-04** skip sitting at the top of the list, July applied normally (₹1,000 interest + ₹4,000 instalment, balance **₹179,000**), every figure matching the S155 close to the rupee → nothing logged. Shivani's over-reversal fixed the append-only way: the fine + first contra net to zero and stay; the **3 extra contras** each got their own reversal (narration "duplicate contra - reversed"), her line now 8 entries netting to zero — honest trail over clean-looking. The four-tap incident became **F-51** and shaped the build.

**Act 1 (design pass, owner-ruled).** Five decisions locked (D259): approval **on-screen** in the ledger (doctor login + confirmation), **master salary sheet only** (no per-staff payslips), approved salary **appears as a line in each staff's ledger statement** (completes "one home per rupee"), workbook **demoted to read-only** immediately / retires after one clean automated month, net **rounded to the nearest rupee**. The owner also handed over his meticulously-designed month-salary artefact (grid first page with formatted punch cells, bilingual legends, EARLY_BIG rule-sheet, collapsible per-staff money logs) and directed that the new salary report BE that design.

**Act 2 (build — `staff_ledger.py` v2.4 → v3.1, five internal versions, all proven).**
- **v3.0** — the salary engine + `/salary` page. The engine NEVER re-derives attendance policy: it reads `att_month_report.py`'s OWN output files (`salary_inputs_` / `deductions_extras_` / `review_` CSVs) as the interface, so report and salary can't disagree; a shared `month_adjustments()` is the single rule-set for both the close CSV and the salary engine. The page pulls the three former PAPER loops on-screen — informed-absence flags (edits the review file), EARLY_BIG genuine rulings (at the report's OWN would-be amount, fail-loud if the note format drifts — never guesses 0), OT approval (pays only what's approved, capped at the candidate, default 0), Darpan outstation-days (recomputes the excess-absent fine on absent−outstation) — folds in the ledger's closed adjustments and each base salary, and shows the full NET table. **APPROVE & LOCK** (confirmation dialog) appends one `SALARY_PAID` system row per staff (new system category — hand-entry and hand-contra both fenced, F-50 discipline) and writes `salary_final_<month>.csv`; a locked month refuses recompute (token = md5 over every input byte; drift between preview and press refuses the approval); corrections happen NEXT month by adjustment entry (accounting-honest).
- **v3.0 F-51 batch** — contra now a two-step server-side CONFIRM page showing the exact row + amount (step 1 appends nothing, proven); Skip button gains a confirm; reversed pairs (row + its contra) grey out as one visual unit; statement rows group under bold month headers (an April skip can no longer read as July).
- **v3.1** — the FULL salary REPORT: the owner's vetted attendance HTML is read VERBATIM and a FINAL SALARY section is spliced before `</body>` in the same design language — printable final table + screen-only collapsible per-staff breakdowns (every attendance line, each ruling narrated as applied, every ledger entry with narration + maker→checker trail, NET). PREVIEW banner (red) pre-lock, APPROVED & LOCKED (green, stamped) post-lock; on approval the whole report freezes to `salary_final_<month>.html`. Live via `/salary/report`, checker-only.
- Selftest **123 → 184**; ~9 mutation probes this session, all killed (SALARY_PAID out of SYSTEM_CATS, token check off, OT cap removed, contra-step-1 secret append, outstation dropped, rounding broken, splice dropped, waived-ruling-shown-as-deducted, approve-skips-HTML).

**Watchdog.** `clinic_watchdog.py` gained `staff-ledger.service` (backlog item 3, bundled). The repo-sourced copy hash-MISMATCHED the live VPS file → **F-52**: the live watchdog guarded **`gutlog.service`** (owner's separate health project) that neither the repo nor the canon knew about; installing the repo-built file would have silently dropped it. Rebuilt on the TRUE live copy (verified `096aba39…`) → md5 `01ca6591a74ec8009bf9748fb7f480c2`, 11 services, gutlog preserved, hand-run 11/11 up.

**Install drama → F-53.** v3.1 first shipped as `06bf03cb…`; it compiled and selftested on the sandbox's **Python 3.12** but died on the VPS venv (older Python) with `SyntaxError: f-string expression part cannot include a backslash`. **F-53: a compile check on a NEWER Python than the target proves nothing about the target.** Fixed (lifted the backslash out of the f-string expression; whole-file swept for siblings — none), and re-proven by compiling AND running the full 184-check selftest under **Python 3.11** (VPS-era, via `uv`). Final **`8bcf1b2d296786717437db672fb29b05`** — installed, md5-exact, 184/184 on the VPS, service restarted. The failed upload never endangered the service: a syntax-error file can't start, so the running v3.0 stayed up (and the watchdog, ironically newly guarding it, would have caught a death within 5 minutes).

**Verified live this session:** ledger v3.1 `8bcf1b2d…` (VPS md5 + 184 selftest + restart); watchdog `01ca6591…` (VPS md5 + 11/11 hand-run). July salary page rendered on the owner's phone (12 staff, total preview ₹107,447) — Darpan's ₹5,000 loan deduction folded in automatically; Shivani read ₹1 low exactly as predicted (test fine in July, its reversal in August, netting to zero). **July rupee-by-rupee reconciliation vs actually-paid: OPEN — the owner's carry item; July never gets an APPROVE press (already paid via workbook); its clean reconciliation is what officially demotes the workbook to read-only.**

**gutlog recorded:** `gutlog.service` is the owner's separate Health project, not part of this project's canon — guarded by the watchdog but not managed here.

**Decisions minted this session**

- **D259 — Full backend salary automation (owner mandate S155, delivered S156).** The VPS computes salaries end-to-end; the manual monthly Excel entry/upload is retired. The Staff Ledger's `/salary` page (checker-only) reads `att_month_report.py`'s output files as the interface (never re-deriving its policy math), pulls the three former paper loops on-screen (informed flags, EARLY_BIG genuine rulings, OT approval + outstation), folds in the ledger's closed monthly adjustments (via the shared `month_adjustments` rule-set) and each base salary, and produces the NET table (nearest rupee). **APPROVE & LOCK** appends one `SALARY_PAID` system row per staff + writes `salary_final_<month>.csv` + freezes the full report `salary_final_<month>.html`; a locked month is never silently recomputed (input-token guard) — corrections are next-month adjustment entries. The salary REPORT is the owner's vetted attendance HTML (grid/legends/collapsibles verbatim) with a spliced FINAL SALARY section. Approved salary shows as a line in each staff's ledger statement (outside the adjustments net). Workbook demoted to read-only reference on the VPS; full retirement after one clean automated month. Config decisions: on-screen approval, master sheet only (no per-staff payslips), nearest-rupee rounding.

**Findings minted this session**

- **F-51 — One-tap irreversible appends in the Staff Ledger UI (raised by the owner via the four-tap Shivani contra; fixed same session).** The red contra button (and the Skip button) appended with no confirmation, so a mis-tap or a repeated tap silently created real ledger rows. FIX (screen-only, no engine/data change): contra is now a two-step server-side confirm page showing the exact target row + amount (step 1 appends nothing); Skip carries a confirm; reversed pairs display greyed as one unit; statements group under month headers so a stale-position row (an April skip) can't be misread as a current-month event. Owner's request for a DELETE button was declined by recommendation — append-only + void-pair display gives the clean screen without making any rupee erasable (a true delete would need its own decision).

- **F-52 — Repo copy of a live operational script silently stale vs the VPS (caught by the D160/D188 hash gate).** The repo's `clinic_watchdog.py` lacked `gutlog.service` that the live file guards; the Phase-0-style md5 gate before install caught the drift, preventing a silent loss of coverage for the owner's health project. RULE (reinforces D160): for any live operational script, build from a fresh VPS copy verified by md5, never from the repo mirror assumed current; the repo mirror is a publish target, not a source of truth.

- **F-53 — A compile/selftest pass on a newer Python than the deployment target proves nothing about the target.** v3.1 compiled + passed 184 checks on the sandbox's Python 3.12 but failed to start on the VPS's older Python (`f-string expression part cannot include a backslash`, legal in 3.12, illegal earlier). RULE: every VPS-bound Python deliverable is compiled AND selftested against the VPS's Python generation (3.11 via `uv`) before delivery — a green run on the wrong interpreter is not a green run. (Kin of F-46's "a check that cannot fail is not a check": a check on the wrong platform is the same class of false assurance.)

**Records & housekeeping.** Notion tools absent a SIXTH consecutive session — catch-up now spans S151–S156. Drive read-only (delivery via present_files). Gmail health note skipped per EOS §B (no manual health check; automated digest live). GitHub commits owed: `staff_ledger/staff_ledger.py` v3.1 `8bcf1b2d296786717437db672fb29b05` + `clinic_watchdog.py` `01ca6591a74ec8009bf9748fb7f480c2` (live-verified, repo stale) + the canonical-docs mirror refresh (now two session-sets behind + root strays). Cold kit rebuilt this EOS. Small owner cleanup possibly pending: `rm /root/watchdog_live_copy.py`.

**Findings: F-51, F-52, F-53 (all minted; F-51 fixed same session). Decisions: D259 (minted + executed). Next free decision: D260. Next free finding: F-54.**

---

**END OF KB HISTORY ARCHIVE v1.8. §S156 is the last section; §S155, §S154 and earlier sit above it. If §S155 or this marker is absent, this file is truncated and must not be used as canonical.**


---

## §S157 — 2026-08-07 (Session 157, EOS-light — documentation & design only; NO live code, config, trigger or property touched; no GitHub commit; whole estate mapped + portal/SSO designed)

**Narrative.** Phase 0 hash-verified all 22 canonical rows but found **`KB_Register` v2.9 absent from project knowledge** — the S156 doc-swap had landed every other S156 file but missed the Register. Halted per D172/D188; absence proven by exhaustion (D201); owner re-uploaded; md5 matched `a5b38555f42aa4f2556ee1a1550b6c20`; verification then fully green.

The session then pivoted, at the owner's direction, from the July-reconciliation backlog to a full **estate-mapping + portal/SSO design** push. Over several turns the owner fed the entire estate: the two crude cross-project registers (`App_Service_Register_v1`, `Clinic_App_Register_v1`), all six Apps Script exports (clinic account `drmka.ortho@gmail.com`: Callback-Tracker cockpit, DailyClinicReports, Accounting, UPI-Reconciliation; personal account `drmanojkragarwal@gmail.com`: Inbox Janitor, CC_saver), both GitHub repo JSON dumps, the D-drive apps zip, and the C-drive follow-up-tracker zip. Each was grounded from source, not from the registers.

**`Clinic_Estate_Master_Inventory_v1.md` (v1.7)** was built and iterated seven times as the pieces arrived — the complete reconciled cross-project estate: VPS clinic services (attendance 8042, ledger 8043, asset 8030, wa-approve 8101, the call/WABA back-end, portal 8099) + personal (GutLog 8020, RxGuard 8031, FitLog 8040); both Google accounts; both repos; all local PC apps. Every clinic-relevant row grounded [V] from source. It supersedes the **S63-era `App_Service_Register`** for the automation core. The "asset app" the owner referred to was placed as the **Asset Register** (`assets.dr-manoj.in:8030`, `assetapp/`); **FitLog** placed at `fit.dr-manoj.in:8040`.

The auth code of the four portal apps was read from the repo: **four different schemes, no shared secret or identity** — portal (device-trust cookie + PIN), attendance (HMAC cookie), ledger (Flask session + users.json roles), asset (Flask session + users table). So true SSO needs a broker, not a shared cookie alone. The ledger's `/salary` is already **checker-only in code** — the F-31 manager line is enforced without new code.

Design docs produced: **`Clinic_Portal_SSO_Architecture_v1.md`** (an SSO broker owning login + roles, issuing one signed `.dr-manoj.in` cookie; a ~15-line shared verify-shim per app; each app keeps its own login as fallback; the Apps Script cockpit stays link-based) and **`Clinic_Portal_Build_Plan_v1_S157.md`** (doctor + manager tile rosters; a full per-app selection table; local apps as a PC-only, live-detected group that absorbs the Clinic Hub; the cockpit the only user-facing GAS tile). **`Salary_System_KB_v1_S157.md`** was created as a Tier-1 reference consolidating the Staff Ledger + backend salary automation (system only; F-31; no figures).

A sanitized cold kit **`DrManoj_Estate_ColdKit_S157.zip`** was built (all session docs + owner artifacts). Sanitization caught and removed **patient consent files** (`case_archive/`), **patient plan PDFs** (`plan_archive/`), the tracker's patient `data/` folder + a `.secret_key`, F-31 salary files, and a **live GCP service-account key** — the kit ships code and structure only. Resolutions from cross-checking the dumps: **`clinic-hub` is in neither repo** (PC-only; the Website/SEO register's "canonical GitHub clinic-hub/" claim is wrong); **`gutlog` is duplicated in both repos** (`drmanoj-health-systems` canonical per its `CLAUDE.md`). No live code was touched; no incident.

**DECISIONS (full text):**

- **D260 — The estate is ONE system across three hosts; map it once, verify from live source.** The clinic + personal apps span the VPS, two Google Apps Script accounts, and the local PC, but the "three projects" are a *documentation* boundary only — the automation repo is effectively a monorepo (it physically holds `assetapp`, `casepack`, `gutlog`, `gmail-automation`). A single reconciled master inventory (`Clinic_Estate_Master_Inventory`) is the reference. Ground every row from live source (repo tarball, app code, GAS export), never from a register/dump/filename that merely looks current — reinforces D188.

- **D261 — Portal single-sign-on = a broker + a per-app verify-shim; a shared cookie alone is not SSO.** A cookie scoped to `.dr-manoj.in` *reaches* every subdomain, but each app validates its own cookie with its own secret and identity, so it would reject a foreign cookie. SSO therefore introduces (a) a **broker** — the portal grows a clinic user+role store (roles `doctor`, `manager`) and issues one signed `.dr-manoj.in` cookie carrying `{user, role, epoch, exp}`; and (b) a **shared verify-shim** (~15 lines) each VPS app imports: if the SSO cookie is valid, treat the request as logged-in with that role; else fall back to the app's own login (kept). The Apps Script cockpit is Google-hosted and cannot take our cookie — it stays link-based (`?k=` in the tile). Rejected alternative: sharing raw Flask sessions (couples code, can't carry roles cleanly).

- **D262 — Portal app-selection (doctor vs manager), and local apps stay local.** Doctor portal = Group A web SSO apps (attendance, ledger+salary, asset, WABA-approve) + Group B cockpit (link) + Group C optional report-Sheet views + **Group D a "Clinic PC only" local-tools group that absorbs the Clinic Hub** (Follow-up Tracker, Vitals & Plan, Case Pack, CC Statements→Tally, GMB Assist — `localhost` tiles that work at the PC and hide otherwise). Manager portal = attendance + asset + ledger-**entry** (maker) only; no cockpit, no reports, no salary. Rationale: local apps are `localhost`+PHI and must never be served remotely; the cockpit is the only user-facing GAS; the personal cluster (Rx/GutLog/FitLog) is a different trust class and stays out (at most one link-out tile).

- **D263 — A dedicated Salary System KB.** The Staff Ledger + backend salary automation now has one wholesome Tier-1 reference (`Salary_System_KB`) consolidating architecture, maker-checker model, the D259 salary engine, F-51 UI safety, auth, deploy discipline, and the F-31 fence — system only, never staff figures.

**FINDINGS (full text):**

- **F-54 — A register's date/filename is not its provenance.** `App_Service_Register_v1.md` carried a 07-Aug-2026 file date but its own precedence note sourced its content from "Master KB v1.36 / Session 63" — ~93 sessions stale, missing the asset app, the staff-ledger, and the whole salary stack. It looked current and was not. RULE (reinforces D188): reconcile any provided register against the live KB/manifest and live source; a 7-Aug wrapper over S63 content is exactly the trap Phase 0 exists to catch.

- **F-55 — A repo-to-JSON dump can be silently partial.** The owner's `drmanoj-clinic-automation` JSON repo-dump (3.87M tokens, including the binary `attendance.zip`) had been truncated by its export tool and silently omitted four live folders — `staff_ledger`, `wa-diagnostics`, `revenue-reconciliation`, `plan-tool` — plus a root script. Cross-checked against the codeload tarball pulled directly from GitHub. RULE: for repo structure/content, use the live repo (codeload tarball / raw files), never a dump assumed complete; a dump is a convenience, not the source of truth.

- **F-56 — An uploaded "code" zip can still carry secrets, PHI, and F-31 data.** After the owner deleted "most data files," the follow-up-tracker zip still contained a live **Google service-account private key**, `.env`, `fu_upload.env`, and a `.secret_key`; the tracker/casepack/clinic_writer trees still held patient CSVs, patient consent HTML, and patient plan PDFs; the D-drive zip still held the F-31 `clinic_salary/` folder. A first sanitization pass by file-type missed the patient `case_archive/`/`plan_archive/`/`data/` directories — caught only by listing the resulting tree. RULE: before aggregating any local capture, strip whole `data/`/`output/`/archive directories (not just by extension) plus all key/secret files, then verify by tree-listing + a secret scan. ACTION: the service-account key that rode through an upload must be **rotated** (folds into the standing key-rotation backlog).

**Records & housekeeping.** Notion tools absent a SEVENTH consecutive session — catch-up now spans S151–S157. Drive read-only (delivery via present_files). Gmail health note skipped per EOS §B (no manual health check; this was a docs/design session). No GitHub commit this session (§C skipped, EOS-light) — the four new S157 docs are owed to `canonical-docs/` next session, and the S156 code push is to be verified. Cold kit built + sanitized this EOS. Live salary/ledger versions UNCHANGED from S156.

**Findings: F-54, F-55, F-56 (all minted; none live-system faults). Decisions: D260, D261, D262, D263 (minted); D259 backfilled into the Register index. Next free decision: D264. Next free finding: F-57.**

---

## Session 158 — 08 Aug 2026 — SSO portal built & rolled out live end-to-end (Steps 1–6); Notion catch-up (S147→S157)

**Phase 0.** All canonical rows md5-verified. `Fault_Action_Register_v2_3.md` was momentarily ABSENT from the set; the owner re-uploaded it, hash `c45d5a55…` matched, and verification closed **23/23**. No mismatch, no reconciliation debt.

**Notion catch-up (parked seven sessions) — DONE.** The cause of the "absent Notion" streak was found: the Notion connector was connected at the account level but **toggled OFF per-chat**, so past sessions silently had no tools; enabled this session. Ground truth was taken from the **live** Clinic HQ, not our own records: the live session log actually ended at **S147**, while the project's own notes claimed S150 — so the real absent span was **S148–S156 (nine sessions)**, not the runbook's "S151–S157" (→ F-57). The **S157** entry was written in house style, then **S148–S156** inserted (nine entries) anchored on the S157 heading; verified contiguous 147→148…156→157, no dupes, all F-31-clean (no figures). The **Tech & Systems Register** database was reconciled: **3 rows added** (Staff Ledger + Salary automation `staff_ledger.py` v3.1; Attendance salary-report layer `att_month_report.py` v2.5; Clinic Portal + SSO), **2 corrected** (canonical document set → v3.0/Archive v1.9/S147–S157; VPS Service Watchman → 11 services incl. staff-ledger + gutlog), plus housekeeping (Netters Atlas → Paused; Do_Not_Call enforcement → Live, flagged as a duplicate of the suppression row; the "D1–D120 gap (F-22)" row → Paused, corrected to 15 decisions restored + remainder runbook-only, stale monolith pointer removed). **Parked for owner verify (not asserted):** four VPS-state flags — wa-approve nohup-vs-systemd, Follow-up Tracker migration status, Daily Digest v1.4-vs-v1.5, callhook_watchdog scheduling — and the **D194 duplicate-row deletion**.

**Portal SSO — all six rollout steps BUILT, TESTED, INSTALLED, and PROVEN LIVE this session**, one app at a time, every app keeping its own login as a permanent fallback, and F-31 re-proven live at the end.

- **Step 1 — the broker.** `portal.py` was rewired as a **dual-mode** app: it stays on the legacy device-trust PIN until BOTH a `CLINIC_SSO_SECRET` is set AND ≥1 user exists, then switches to **broker** mode (username+password, issues one signed `clinic_sso` cookie scoped to `.dr-manoj.in`). Two new pure-stdlib modules were added beside it: **`clinic_sso.py`** (HMAC-SHA256 signed token `{u,r,e,iat,exp}` + cookie helpers; `COOKIE_NAME="clinic_sso"`, `COOKIE_DOMAIN=".dr-manoj.in"`, secret from env `CLINIC_SSO_SECRET`, fail-loud, D176) and **`clinic_users.py`** (JSON user store at `/root/portal/clinic_users.json` chmod-600, salted **PBKDF2 200k**, roles-as-data default doctor/manager, a global **epoch** for "sign out everywhere", full admin CLI). Installed to `/root/portal/`; on-VPS selftests clean; Phase A restarted in legacy mode (health `legacy/ok`), Phase B the owner set the secret into `portal_config.py` via a masked one-liner (value never shown), added `manoj/doctor`, restarted → **broker/ok**. Runtime port is **8099** (gunicorn `-b 127.0.0.1:8099`); the `:8090` in the file is only the dead `__main__` dev line. A pre-SSO backup `portal_BACKUP_S158_pre_sso.py` was reconstructed (the owner had overwritten the original without a backup) and kept for rollback.

- **Move 1 — Step 2 tiles + login niceties.** One `portal.py` delivery: a **password eye-toggle** on the broker login (reveals only what you type — D176-safe; its CSS needed `.login .eye` specificity to beat the full-width `.login button` rule, which had drawn it as a blue bar), **case-insensitive usernames** in `clinic_users.py` (kills the capital-first-letter trap that had rejected "Manoj"; selftest 24/24), and **role-driven tiles**: the doctor sees the full set (Call Tracker cockpit, Attendance, **Salary & Ledger**, Asset Register, WhatsApp Approvals — marked blocked, plus the report Sheets and held tiles); the manager sees **only** Attendance, Asset Register, and Staff Ledger — Entry (no salary — F-31). Verified on screen ("Signed in as manoj (doctor)", full doctor grid).

- **Step 3 — attendance shim.** `att_dashboard.py` `authed()` now also accepts a valid `clinic_sso` cookie; the app's own `att_session` cookie and HTTP Basic-Auth stay as fallback. Shim smoke 12/12. Live: Incognito still shows the attendance login (fallback intact); the portal-logged-in browser opens `attendance.dr-manoj.in` with no second login.

- **Step 4 — asset shim.** `asset_register.py` `current_user()` falls through to `_sso_user()`, which maps a valid SSO cookie to a **local asset user row** — doctor→**owner**, manager→**manager** (prefers a same-username local row when its role agrees; role-mismatch guarded). `owner_required` routes still refuse a manager. Shim smoke 11/11. Live A+B verified.

- **Step 5 — ledger shim (the F-31 one).** `staff_ledger.py` `create_app().user()` falls through to `_sso_user()`, built on the principle that **SSO proves WHO you are; the ledger's own `users.json` decides WHAT you may do** — the SSO username is matched to a ledger user and that user's own role (maker_full / maker_limited / checker) governs. A hard **anti-escalation guardrail** refuses to let an SSO *manager* resolve to a ledger *checker* even by name-match. The file's own **184-check selftest still passed** (shim inert without a portal secret) and a dedicated SSO smoke was **16/16** — doctor→checker reaches `/salary`; **manager→maker is 403 at `/salary` and `/salary/approve`**; stale-epoch and wrong-secret rejected; native login preserved. Installed on the real VPS Python (F-53 gate), selftest 184 re-run in a throwaway `LEDGER_DIR`, live A+B verified.

- **Step 6 — managers onboarded + LIVE F-31 proof.** `shavez` (ledger maker_full) and `alisha` (ledger maker_limited) were added as **named** portal managers. Logged in live as `shavez`: the portal showed **only the three manager tiles, no Salary & Ledger**; the ledger opened with no second login as a maker with **no Salary link**; and typing `attendance.dr-manoj.in/ledger/salary` directly returned **403** — F-31 enforced end-to-end, on the live server.

Each shim reads the portal secret directly from `/root/portal` (no per-app secret wiring) and is **inert** if it cannot — in which case the app behaves exactly as before, so none of the four edits could remove existing access. Rollback for each is a one-line copy of the `*_BACKUP_S158_pre_sso.py` file + a service restart. Operational note: a WinSCP **direct** upload produced a 0-byte file twice; the reliable path is to drag into the WinSCP local pane and copy the file out from there.

**DECISIONS (full text):**

- **D264 — SSO rolled out live, one app at a time, fallback intact throughout (execution of D261).** The broker + per-app verify-shim design was built and installed across portal → attendance → asset → ledger in a single session, but strictly **one app per step**, each verified live before the next, precisely to bound blast radius: a failure is isolated to that app, and rollback is that one app's backup. The governing invariant is **inert-on-failure** — if a shim cannot read the portal secret from `/root/portal`, it grants nothing and the app falls back to its own login, so adding a shim can never remove existing access. "All at once" was declined for exactly this reason (four live apps in one swap, ambiguous failure, four-app rollback).

- **D265 — Authentication vs authorization is the shim law: SSO proves WHO; each app's own store decides WHAT.** The `clinic_sso` cookie carries identity + a coarse role only. Each app maps it to its own model rather than trusting the cookie's role blindly: **attendance** admits any valid token (a shared page); **asset** maps doctor→owner, manager→manager onto its users table; **ledger** matches the SSO *username* to a ledger user and adopts that user's own fine-grained role (maker_full / maker_limited / checker). Enforcing this at the app's own store is what makes F-31 structural rather than cosmetic. Its hard edge is the ledger **anti-escalation guardrail**: an SSO *manager* may never resolve to a ledger *checker*, even if a same-named checker exists — the mapping is refused and the visitor is sent to the app's own login. Re-proven live (manager 403 at `/salary`).

- **D266 — Broker user model settled: one clinic login list, roles-as-data, named per-person managers.** The portal is the single clinic login list; users and roles are data (`clinic_users.json`), not code. Managers get **named** logins (`shavez`, `alisha` onboarded), not a shared "manager" account, so actions are attributable and can be deactivated individually. Future users (lab, Manoj Bhati, Sanjeevni) are added by command when their roles are decided. This settles the "shared-vs-named manager login" open portal decision from S157.

**FINDINGS (full text):**

- **F-57 — Take a catch-up's scope from the live target, not from our own records.** The project's notes said the Notion session log stood at S150; the **live** Clinic HQ actually ended at **S147**, so the true gap was S148–S156 (nine sessions), wider than the assumed "S151–S157." RULE (reinforces D188/D260): when reconciling an external system, read where *it* actually is and scope from that; our own "where we think we left it" is exactly the record that drifts. (The seven-session "Notion absent" streak had a second, mechanical cause: the connector was toggled off per-chat, not missing.)

- **F-58 — Flask's test client ignores a manually-set `Cookie` header.** A cookie-auth smoke gave a false negative — a valid SSO token passed via `headers={"Cookie": ...}` did not authenticate the request, because the Flask test client manages its own cookie jar and drops a raw `Cookie` header. The token was fine (a `test_request_context` probe verified it). RULE: to smoke-test cookie auth in Flask, use the client's `set_cookie` jar (or `test_request_context`), never a raw header — a header-based test can fail on a correct implementation and send you chasing a non-bug.

**Records & housekeeping.** Notion catch-up COMPLETED this session (connector re-enabled; S148–S157 written; Tech Register reconciled; four VPS-state flags + the D194 dup-row deletion parked for the owner). Drive read-only (delivery via present_files). **GitHub commit owed:** the six files delivered this session — `clinic_sso.py`, `clinic_users.py`, `portal.py` (→ `launcher/`), `att_dashboard.py` (→ `attendance/`), `asset_register.py` (→ `assetapp/`), `staff_ledger.py` (→ `staff_ledger/`); the data files `clinic_users.json` and `portal_config.py` stay git-ignored (F-31 family — the config holds live secret material). Cold kit + git kit built this EOS. Service-account key rotation (F-56) still open. July salary reconciliation still an owner carry.

**Decisions: D264, D265, D266 (minted). Findings: F-57, F-58 (minted). Next free decision: D267. Next free finding: F-59. This was Session 158.**

---

## §S159 — Portal Group D + personal tiles + GMB moved to the VPS (FULL EOS · one live VPS file: `portal.py`)

A build session on the doctor portal (backlog item 3). Phase 0 verified all 26 canonical rows by md5 — zero mismatches; the long-pending S150–S158 install had landed (project knowledge now holds the post-install set, `START_HERE_SESSION_159` present at its pin). Item 1 (the six-file S158 GitHub commit) was reported **done** by the owner; an external md5 re-check is still owed (needs the repo-owner path). Item 3 was built and verified live end-to-end.

**What was built (all in `portal.py`, live at `followup.dr-manoj.in/portal`, gunicorn :8099, service `clinic-portal`).** Started from the md5-verified live file (`c52ab1fd…`), delivered a full-file replacement, `py_compile` + a Jinja render smoke-test (doctor-on-PC / doctor-off-PC / manager) as the delivery gate.
- **Group C (report-Sheet views) found ALREADY wired** in the live portal — UPI Reconciliation, Monthly Accounting (= Clinic Accounting Reports sheet), Daily Collections, Vehicle Tracking — so the owner's "report sheet files" ask was effectively already satisfied; **not duplicated**.
- **Group D — 4 Clinic-PC-only tiles** (Follow-up Tracker `:5000`, Vitals & Plan `:5057`, Surgical Case Pack `:5058`, CC Statements→Tally `:5059`), doctor-only, plain links, gated by a per-device marker (D267).
- **2 personal tiles** (doctor-only) — CC Statement Saver → Drive folder, Inbox Janitor → Payment Register sheet — targets read from git-ignored `portal_config.py` (D268). CC_SAVER_URL confirmed opening Drive after install.
- **GMB Review Assist** — first built as a PC-local server (`gmb_serve.py`, localhost), then **moved to the VPS** at `/portal/gmb` behind login (D269); `gmb_serve.py` retired.

**Faults hit and diagnosed live (all correctly traced to cause, none a build defect):** Chrome's blocked SIP port 5060 (F-59); Linux case-sensitivity `GMB.html` ≠ `gmb.html` (F-60); a pasted code-fence label breaking `portal_config.py` (F-61). The CC→Tally "connection refused" the owner saw is **expected** — a Clinic-PC tile whose local app simply isn't running.

**Live file:** `portal.py` **`c52ab1fd…` → `679a00874c039ecabc533f9ddd0f5e67`** (516 → 634 lines). New but **retired same session:** `gmb_serve.py` (superseded by VPS hosting — not a live artefact). Repo commit of `portal.py` owed.

**DECISIONS (full text):**

- **D267 — Portal Group D uses a server-side per-device "clinic-PC" marker, not client-side localhost probing (Model 1).** Because Chrome 142+ fully enforces Private Network Access — an HTTPS page's `fetch`/probe to `http://localhost` is blocked or permission-gated by default — a "live reachable dot" built on probing is unreliable in this setting. Instead the four localhost tiles are plain links gated by a signed marker cookie `clinic_portal_pc` = HMAC(`PORTAL_TOKEN_SEED`, `clinic-pc-device`), set by visiting `/portal/mark-pc` **once in the clinic PC's own browser** and cleared by `/portal/unmark-pc`; the marker rides the same server seed, so "forget all devices" also clears it. The tiles show only on the marked device (hidden on the phone). Trade-off accepted: no per-app up/down dot — a stopped local app just returns connection-refused. Group C report-Sheet tiles were found already present in the live portal and were not duplicated.

- **D268 — Personal-account (and other capability) tile targets live only in git-ignored `portal_config.py`, never in committed `portal.py` or the repo.** The two personal tiles (CC Statement Saver → Drive folder; Inbox Janitor → Payment Register sheet) read `CC_SAVER_URL` / `INBOX_JANITOR_URL` via a `_cfg_get` helper; blank → the tile renders MANUAL. This keeps capability URLs (and, by the same rule, the cockpit's key-bearing `/exec?k=` URL) out of version control — an extension of the F-31 family and D176 (a human, not the assistant, places the secret-bearing value). **Scope decision (B):** only the *new* personal tiles use config this session; the pre-existing hardcoded clinic Sheet tiles (already committed) were left untouched, not refactored — optional later migration flagged.

- **D269 — GMB Review Assist is VPS-hosted at `/portal/gmb` behind SSO; it is the explicit exception to D262, and the other local apps stay PC-only.** GMB is a static, self-contained HTML page (no backend, no patient data, all client-side), so it is served by the portal (`login_required`), read per-request from `/root/portal/gmb.html` (path overridable via `GMB_HTML_PATH`), reachable on any device including the phone. It first ran as a PC-local server (`gmb_serve.py`) but that was **retired/superseded within the same session** once VPS hosting was chosen — `gmb_serve.py` is not a live artefact. VPS-hosting **CC→Tally was requested and declined**: it processes credit-card statements (owner-only finance) and feeds Tally, which runs on the clinic PC — so D262 governs (local finance/PHI apps must never be served remotely, and remote hosting would add a PC round-trip, not remove one). The three remaining local apps (Vitals 5057, Case Pack 5058, CC→Tally 5059) stay PC-only; their reliable auto-start is parked as a hands-on PC session (owner judged Task Scheduler and NSSM services both unreliable; likely a manual one-click launcher).

**FINDINGS (full text):**

- **F-59 — Chrome refuses ports 5060/5061 (SIP) as `ERR_UNSAFE_PORT`.** Chrome's restricted-port list (enforced across all contexts, hardened under v142 PNA) will not open `http://…:5060` or `:5061` from anywhere — address bar or tile — while `curl`/CLI ignore the list, so the server looks perfectly healthy (`curl` returns the page, `netstat` shows it LISTENING) while every browser fails. RULE: localhost tiles/dev apps must avoid Chrome's restricted ports; when a working server won't open in the browser but `curl` succeeds, suspect `ERR_UNSAFE_PORT` first. Resolved operationally by moving GMB to the VPS; the finding still constrains any future localhost app (e.g. the 5057/5058/5059 auto-start work).

- **F-60 — The VPS filesystem is case-sensitive: `GMB.html` ≠ `gmb.html`.** A file uploaded under a different case (or its original long name) makes a path-based read fail with the app's own "not installed" message even though the file is present — the code opened `/root/portal/gmb.html` while the file on disk was `GMB.html`. RULE (kin of D188): on the VPS the filename's *case* must exactly match what the code opens; "the file is there" is not "the file the code opens is there." Fixed with `mv` to the exact lowercase name.

- **F-61 — Pasting a fenced code block's language label into a live config file breaks the whole file.** Copying edit instructions that included a ```` ```python ```` fence put a bare `python` token on its own line in `portal_config.py`, which raised `NameError` at import, made the ENTIRE config unreadable, and dropped the portal to "Setup needed" (fail-safe to *unconfigured* — secrets were intact the whole time). RULE: when instructing a config edit, tell the owner to paste only the lines BETWEEN the fences, never the fence or its label; and diagnose a sudden "unconfigured" by importing the config (`python -c "import portal_config"`) to surface the offending line. Applied immediately — later config instructions this session called it out.

**Records & housekeeping.** No incident. Two stale doc headers corrected in passing (Archive top header lagged at v1.9; Fault Register end-marker lagged at v2.3 — same stale-record family caught before, e.g. §S131/§S143). Drive read-only (delivery via present_files). **Owed to the repo:** `portal.py` `679a0087…` → `launcher/`; `gmb_serve.py` is **retired** (commit optional, as history/fallback only — clearly marked superseded). **Item-1 external md5 re-check of the six S158 files still owed** (needs repo-owner path). `portal_config.py` + `clinic_users.json` stay git-ignored (F-31). **New backlog item:** local PC apps (Vitals 5057 · Case Pack 5058 · CC→Tally 5059) — hands-on session to confirm each runs, then a reliable launcher (NOT VPS — D262/D269). Service-account key rotation (F-56) and CALLHOOK Steps 3–4 still open; July salary reconciliation still an owner carry.

**Decisions: D267, D268, D269 (minted). Findings: F-59, F-60, F-61 (minted). Next free decision: D270. Next free finding: F-62. This was Session 159.**

---

## §S160 — Case Pack→VPS decided; Staff Daily Register subsystem designed; portal health tiles + sectioned mobile layout live (09 Aug 2026, FULL)

Phase 0 verified all 24 canonical rows by md5 (zero mismatch). Owner ran a mixed session: closed portal backlog items, then a long design run on the salary/attendance subsystem.

**Portal (live code).** `portal.py` `679a0087…` → **`81c2baef638f0d2d59d438c6370522cb`** (650→717 lines). (a) 3 doctor-only personal health link-tiles — RxGuard `rx.dr-manoj.in`, GutLog `health.dr-manoj.in`, FitLog `fit.dr-manoj.in` (each keeps its own owner-key login). (b) Sectioned mobile layout: tiles grouped Clinic / Money & Accounts / Clinic PC tools / Personal / Health / Coming soon; empty sections auto-hide per role; phone forced to a 2-column grid; role/PC filtering moved server-side into `_visible_sections`. An interim build (193b4e01→2fadafa4) shipped a `pc`-NameError (F-63): the route referenced a `pc` local that existed only as a keyword in the render call → 500 for authenticated users, while the logged-out curl (302) passed. Rolled back one line and refixed to `81c2baef`. SSO passthrough for the three health apps was **parked** at owner's direction.

**D270 — Surgical Case Pack → VPS (off-Drive).** A code audit of the uploaded live `D:\casepack tool\` (PHI excluded) established the true data flow: reads the follow-up tracker's local `patient_master.csv`/`patient_diagnosis.csv` read-only; writes a **local** `case_archive\YYYY\UID\*_bundle.json` + `*_consent.html` + `case_ledger.csv`, stated four times as off-Drive by design; no secrets, `127.0.0.1`-bound. So Case Pack is the twin of Vitals — a local PHI store, not the "Website/SEO" tile a doc had labelled it (F-62). Owner chose VPS migration but **off-Drive**: VPS-disk archive + a PC→VPS push for the patient CSVs, so **no service-account key is touched and F-56 stays parked**. Sarvam being an API (extracts from a file wherever it sits) means VPS-disk storage still delivers the future document-search vision — scanned discharge summaries, indoor-file covers, implant bills stored per case with Sarvam text alongside. This reverses D262 and re-amends D137 ("storage home = the clinic PC"). Migration wave locked: Case Pack → Vitals (under a D34 waiver) → CC→Tally, which the owner **reclassified as a full VPS move** (its output is an accountant-ready CSV/Excel; there is no desktop-Tally import to keep local; Drive/GAS earns its place only as the accountant-sharing channel, on an F-31 restricted folder). Follow-up Tracker stays local by design (D246); the Clinic-Hub launcher dissolves into the portal. Build parked behind a phase-3 strategy hard-bake (owner: "we proceed to coding only after hard baking it").

**D271 — Staff Daily Register subsystem.** What began as "fine-tune the salary ledger" became a designed subsystem after a critical evaluation of the July output surfaced eight flaws (arithmetic was clean; the defects were structural): punch-out data missing for most staff making early-exit/OT rules apply unequally and rewarding non-compliance; giant OT candidates with no sanity ceiling (Shivani ₹1,313.89 from four 4–5h entries — actually ₹200 cover duties); off-days invisible in the denominator; EARLY_BIG mis-framing brief-presence days; two divergent "Net" figures (one booking unapproved OT); a "FINAL" block that is a preview; and an incentive unreachable for 10 of 12. Owner triaged these into a maker-checker **Staff Daily Register**: a no-typing daily page (maker = receptionists Alisha + Shivani[inactive]; checker = Shavez, one-click; override = Manoj + Dr Bhawna, peers) that captures the day's exceptions so month-end is confirmation, not entry. Three stores, one writer each: Daily Register (SQLite WAL — daily items + a history-aware staff record + uniform/i-card issuance), Yearly Balances (leave counters + incentive pot), and the existing Staff Ledger (advances/loans/perks + override-only ad-hoc fines). Policy locked: dress ₹20 / i-card ₹20 (hard-gated on issuance, seeded from Shavez's sheet; nullified on leave/absent days); leave-vs-absent; ≥60-late informed/uninformed with informed-by (Bhawna/Manoj); clinic-holiday date-tick (Holi = closed); outstation ₹250/night (food/bed out of system); **Shivani-only ₹200/duty cover** (config exception); OT-with-permission default-accepted; the leave model (Sunday rota = ~2 offs via an override toggle that applies from a fresh month + 2 discretionary/month reset and encashed at 1 day each + 2 festival/year encashed at FY-close; over-quota = −1 day's pay + additional conditional fine; plain absents keep fines-only); incentive accrued into a per-staff annual pot (financial year Apr→Mar, paid on the following Diwali, bad month floors at ₹0, leaver paid pro-rated on exit); staff lifecycle history-aware with date-ranged shifts and override-only entry. The consolidated dossier `Staff_Daily_Register_Dossier_v1_0.md` (`84fe26dd39baafb4305e803e28ed8608`) is registered Tier-1 as a DRAFT pending owner sign-off; build is page-first, engine-second, with a July + partial-August dry-run before the first real APPROVE.

**WABA state correction.** The canonical record carried "WABA sends blocked pending Lokesh" (D120); the owner states WABA is **not blocked — it needs operationalising**. Recorded as a state correction (verification-first: confirm the live send path fires, then migrate `wa_approve` nohup→systemd), reworded in the backlog. Not a fault.

**Records & housekeeping.** No incident report (the portal 500 was caught, rolled, refixed live). GitHub connector OFF this chat → the item-1 external md5 re-check is still owed. Drive delivery via present_files. Owed to the repo: `portal.py` `81c2baef…` → `launcher/`; the dossier → `canonical-docs/`. `portal_config.py` (a live secrets file) entered the chat transcript this session — recommend rotating `CLINIC_SSO_SECRET` + re-running `portal_setup.py` at convenience (S128 discipline).

**Decisions: D270, D271 (minted). Findings: F-62, F-63 (minted). Next free decision: D272. Next free finding: F-64. This was Session 160.**

---

## §S161 — Session 161 (09 Aug 2026) — Staff Register onboarding features + Salary Engine Stage A; the C-model salary policy locked (D272–D282, F-64)

**Phase 0.** All canonical rows md5-verified against the manifest — zero mismatches. Entering set: KB_Register v3.3 (`89d060bf…`), KB_History_Archive v1.12 (`5c3cfd29…`), HANDOFF_RUNBOOK v98 (`8cbff4c4…`), Fault_Action_Register v2.6 (`6e90861e…`), CANONICAL_MANIFEST, START_HERE_SESSION_161, and the Tier-1 DRAFT `Staff_Daily_Register_Dossier_v1_0` (`84fe26dd…`). Next free before work: D272 · F-64.

**Shape of the session.** Two work streams, both delivered live: (1) finished the **register onboarding features** in `staff_register.py`; (2) built **`salary_engine.py`** — a standalone, read-only salary-reconciliation engine (Stage A). Driven end-to-end by the build protocol: offline build → `py_compile` on the VPS venv Python → selftest incl. a Flask test-client route hit (F-63) → owner installs with `--init` → browser-verify. The owner delegated all tech decisions ("handle the tech part for long-term stability… I will wait for your commands") and repeatedly confirmed the work is planning-stage (real physical records to be entered later via the maker-checker system). Closed with a full EOS.

### 1 — Staff Register onboarding features (all built + installed + verified)
Owner-requested refinements folded into `staff_register.py` across several builds; final installed md5 = **`406a793f96b743bccce53c5c783c1ce3`**. Each install required `--init` (safe additive `CREATE IF NOT EXISTS` + `_MIGRATIONS`); every selftest green; owner confirmed "all good."
- **Degree → many council registrations, each with its own certificate.** New table `degree_registration` (id, doc_id FK→document_vault degree row, staff_id, council, reg_no, stored_path, original_name, is_pdf, added_by, added_ts). A degree is flagged **"NOT registered"** until a registration is added; delete-degree cascades registrations + files. Routes `/registration/add | <id>/download | delete`. Degree upload now captures the sub_type only.
- **Job roles = multi-select tick-list** — [Lab technician, Lab assistant, Lab field staff, Receptionist, Clinic assistant, Pharmacy staff, Cleaner, Driver] + a custom free-text entry; stored comma-joined in `staff_profile.job_roles`.
- **Current address + Permanent address** textareas (new `staff_profile` cols `current_address`, `permanent_address` via `_MIGRATIONS`).
- **Family-member relation → dropdown** (Father, Mother, Husband, Wife, Son, Daughter, Brother, Sister, Guardian, Other).
- **Issued-assets register** — new table `asset_issue` (id, staff_id, asset_type ∈ mobile_phone|bicycle|motorcycle|other, identifier, descr, issued_date, issued_by, returned_date, returned_by, status ∈ issued|returned, note). A card on the staff record: issue asset / mark returned (with date) / delete (manoj only). Custodian-gated (caps.docs = Shavez + override).

### 2 — Salary Engine, Stage A (`salary_engine.py`, read-only)
Final installed md5 = **`a639f2b4be50b0e0d3e31fa3604ba175`** (July run: 12 staff, 0 problems; both selftests green; service active).
- **Architecture (D281).** A separate module at `/root/staff_register/salary_engine.py`, std-lib only, **READ-ONLY** — it writes nothing any live service reads. A pure `reconcile()` core takes loaded dicts (unit-testable). Loaders read the register DB + att's `salary_inputs_<ym>.csv` (the interface, so marks/fine/early math is never re-implemented) + the staff table's `base_salary`. It reuses `staff_ledger.compute_salary(month)` **read-only** for the FINAL-SALARY net and applies a **delta** for the new leave model. Imported by `staff_register.py` under a guard (the app won't crash if the engine is missing). Web route `/register/salary?ym=YYYY-MM` gated `require("check")` (checker Shavez + doctors override; makers excluded); nav tile "💰 Salary reconciliation" for caps.check. CLI `salary_engine.py YYYY-MM` writes `/root/staff_register/register_salary_<ym>.html` and prints **no rupees** (F-31); `--selftest` synthetic.
- **What `reconcile()` computes, per staff** (from artefacts, verified not memory): `genuine_absent = max(0, att_absent − |leave_dates∩absent_dates| − outstation_nights)`; **C = discretionary_used + genuine_absent**; `extra_days = max(0, C−2)`; `fest_over = max(0, fest_used − max(0, 2−fest_prior_fy))`; `deduct_days = extra_days + fest_over`; `base30_ded = deduct_days × base/30`; **encash = (2−C)×(base/30) only if deduct_days==0 else 0**; dress −20×n, i-card −20×n (minutes_exempt→0), extra-duty +200×n (Shivani), outstation +250×night (Darpan); incentive pulled to the annual pot; `prorate_delta = prorated_base − base`; ad-hoc read from ledger `FINE_ADHOC` (informational, NOT in the delta — compute_salary already deducts ledger debits); **final_net = compute_salary_net (read-only) + delta**. Register DB conventions: `daily_register.absence_type='leave_sanctioned'`, `leave_kind ∈ {festival, discretionary}`, `late_flag ∈ {informed, not_informed}`, `dress_improper/icard_missing` 0-1, `outstation_nights` int, `extra_duty` 0-1; `festival_day.clinic_closed=1` = Holi.

### 3 — Intended output format confirmed; dry-runs
The owner uploaded the **July attendance report** (att_month_report **Month Summary** grid + **FINAL SALARY — TOTAL PAYOUT ₹107,447**, PREVIEW) as the **intended output the engine now reproduces and extends**. Dry-runs (all uploaded HTMLs verified correct):
- **July 2026** (empty register — predates data entry): all 12 staff matched, incentive→pot **373.34** (only Arjun + Sukhveer earned), the C-model base/30 deduction applied to every absence (e.g. Darpan 11 absent → −6000). **July = a MECHANICS TEST ONLY, never paid.** The final rerun keeps Sundays as worked half-days automatically (D282: `ROSTER_FROM="2026-09"`, so pre-Sep months read `sun_start`/`sun_end`; the register Sunday toggle drives only the daily-grid display).
- **Partial-August** (register still empty — planning stage): 12 staff, full new-model net column live; the ledger "month not closed" note is an informational preview caveat, not an error. **Owner deleted the August preview HTML at close** (`rm -f /root/staff_register/register_salary_2026-08.html`).
- **Stage B DEFERRED** (D281): the official locked/approvable run — making the preview the real maker-checker output — waits until the register is filled with real maker/checker data.

### 4 — Finding
- **F-64.** `staff_ledger.py` **code** lives at `/root/staff_ledger.py`; its **data** dir is the separate `/root/staff_ledger/`. Reusing the ledger's `compute_salary` from the register app required adding `/root` **and** `/root/portal` to `sys.path` (guarded). Diagnosed via a `ModuleNotFoundError` surfaced by a temporary error-carrying module global (`_ADHOC_ERR`/`_NET_ERR`). *(Full text also in Fault Register v2.7 §7.)*

### 5 — Decisions minted (full text)
- **D272 — Shavez is both maker and checker; self-approval barred.** On any date Shavez entered, his own one-click approve is DISABLED → an override (Manoj/Bhawna) must approve that date.
- **D273 — the Register is the single staff-master; the workbook→CSV path is retired.** The register (SQLite) is the source of truth and regenerates the derived read-only `staff_master.csv`; seed = the current CSV; `staff_id = user_id`.
- **D274 — per-staff appointment-document vault, VPS-disk off-Drive** (F-56 parked); custodian = Shavez + override; Alisha/Shivani excluded.
- **D275 — absence classification is the biometric/attendance system's job.** The register captures only the LEAVE decision + exceptions; it never re-derives presence/absence.
- **D276 — per-staff scoping.** Arjun (`minutes_exempt=1`): leave-only — NO dress/i-card/60-min-late/OT; over-quota leave = flat pro-rata base/30 per excess (still gets the leave quota). Extra-duty = **Shivani only**. Outstation = **Darpan only**. Label renames: "Informed by"→"Approved by"; "Cover"→"Extra duty".
- **D277 — OT is approved-by-default; not a maker field.** Only the checker + override may review next-day to un-approve.
- **D278 — festival leave classified by DATE** (an advance festivals list); 2/year on top of the 2 regular monthly discretionary; Holi = a `festival_day` with `clinic_closed=1` (full closure, consumes nothing); unused festival encashed at FY-close (Diwali).
- **D279 — the C-model leave/absence salary model SUPERSEDES the dossier's §5 encashment design.** C = discretionary leaves taken + genuine (unsanctioned) absences; both eat a 2-day/month buffer (roster Sundays OFF handled upstream). Every day of `max(0, C−2)` **plus** over-quota festival days is deducted at **base÷30**. The ₹50/₹100 fines stay and stack unchanged; late-marks/early logic unchanged; incentive → the annual pot.
- **D280 — unused-leave encashment is attendance-gated.** Paid `((2−C)×base/30)` ONLY when there are zero deductible extra days; any extra absence forfeits it entirely (owner chose the gated option).
- **D281 — the salary engine is a standalone read-only module** reusing att's `salary_inputs` CSV + the ledger's `compute_salary` (read-only) — no re-implementation, no drift. **Stage A** = read-only preview (delta + complete new-model net). **Stage B** (official locked/approvable run) is DEFERRED until the register is filled with real maker/checker data.
- **D282 — (clarification) Sunday half-day for pre-Sep months is automatic.** `att_month_report.ROSTER_FROM="2026-09"`, so pre-Sep months use each staffer's `sun_start`/`sun_end` half-day columns; the register's Sunday toggle governs only the daily-grid DISPLAY, not the July salary math.

### 6 — Next-session TOP TASKS (owner-directed, recorded at head of Runbook §2)
(a) Where to **START in the portal**; (b) get the **July-style FINAL SALARY** output through the new system; (c) **build/wire the Manager (Shavez = checker) and Alisha (maker) portals** for their daily maker-checker jobs = **Stage B** (make the preview the official locked/approvable run, once the register is filled).

**Records & housekeeping.** No incident report. Both new files repo-commit-owed → `staff_register/`. `Staff_Daily_Register_Dossier` marked non-DRAFT **v1.1** (its §5 encashment design noted superseded by D279/D280). Drive delivery via present_files (git kit + cold kit). Notion catch-up now spans S151–S160 (owed).

**Decisions: D272–D282 (minted). Findings: F-64 (minted). Next free decision: D283. Next free finding: F-65. This was Session 161.**

---

**END OF KB HISTORY ARCHIVE v1.15. §S161 is the last section; §S160, §S159 and earlier sit above it. If §S161 or this marker is absent, this file is truncated and must not be used as canonical.**

---

## §S162 — Stage-B salary APPROVE & LOCK; biometric grid; portal tiles; ledger de-scoped; D288 consolidation directive (09 Aug 2026, FULL)

Backfilled at S163 (the S162 canonical fold-in was deliberately deferred at the S162 close-out and carried as OWED). Source of truth: `SESSION_162_CLOSEOUT.md`.

**What shipped and went live (owner-confirmed):**
- `staff_register.py` `9b08112209ab6a771ecf81d07946a7de` — Stage-B salary APPROVE & LOCK (`locked_run` table; `/salary/lock`, `/salary/unlock`; `approval_blockers`; every non-holiday date must have an approved `day_review` row before lock) + biometric-driven daily grid + continuous sanctioned-leave range (`leave_sanction` table, `/register/leave`) + new-tab nav.
- `salary_engine.py` `fc6fea4fb855f512a3b2c655cb4e5919` — Stage-B `total_payout()`; `reconcile()` unchanged.
- `staff_ledger.py` `92665b64f015fee9302ac3da6100f5c8` — B/C only: makers no longer enter leave/uniform/i-card here (D286).
- `portal.py` `43db2131c48a82250878bd022cb6fea5` — Staff-Register tile, new `staff` role, per-user mask/extra, salary tile split.
- `clinic_users.json` (data, off-repo) — roles alisha=staff, shivani=staff, shavez=manager, bhawna=doctor, manoj=doctor.
- Built but deliberately NOT installed (superseded by D288, do not install): ledger accordion salary layout `e799c8f8676ef3c6cee98923d8f5921e`.

**Decisions D283–D288 (verbatim intent):**
- **D283 — Register-native Stage-B salary APPROVE & LOCK.** `/register/salary` gated to salary view (`SR_SALARY_USERS = manoj, bhawna`) and lock power (`SR_LOCK_USERS = manoj` only). `locked_run` table (ym, total_payout, frozen report_html, locked_by/ts, unlock fields). Month lockable only when every calendar date (excl. clinic-closed holidays) has an approved `day_review` row; missing dates hard-block and render as tap-to-approve links; single LOCK at zero blockers; unlock-with-reason. Self-contained, no ledger coupling (reversed on purpose by D288). Acceptance anchor: July TOTAL PAYOUT ₹1,07,447. `--init` mandatory before restart (F-65).
- **D284 — Biometric-driven daily grid + continuous sanctioned-leave range.** Grid reads `/root/punches.csv` (`SR_PUNCH_CSV`; read-only, manual fallback). Leave = dropdown pre-filled from biometric absence; Outstation (Darpan) and Cover (Shivani) Yes/No; dress & i-card = maker taps → ₹20 fine. Grey-out + mutual-exclusion JS. New `leave_sanction` table + `/register/leave`: maker enters range → checker approves (can't approve own) → APPROVED range pre-fills the daily leave dropdown (overridable). `--init` creates `leave_sanction`.
- **D285 — Portal front-door tiles.** New minimal `staff` role; new Staff Register tile (→ `attendance.dr-manoj.in/register`) for doctor+manager+staff; Attendance opened to staff. Per-user `USER_TILE_MASK` (bhawna masks: GMB, Vitals & Plan, Surgical Case Pack, CC Statements→Tally, Follow-up Tracker) and `USER_TILE_EXTRA` (shavez: Asset Register); `_visible_sections(role, pc, user)`. Salary tile split into "Salary — approve & lock" (`/register/salary`) + "Staff Ledger" (`/ledger`).
- **D286 — Leave + uniform/i-card fines moved out of the ledger into the register.** Ledger `ROLE_CATS`: `maker_limited` (alisha, shivani) → [] (New-entry becomes a "moved to the Staff Register →" redirect); `maker_full` (shavez) keeps [NIGHT_DUTY, ICARD_REPLACEMENT, ADVANCE_ISSUE], loses FINE_UNIFORM/FINE_ICARD/LEAVE_APPROVED; checker (doctor) keeps the full list as backstop. Ledger 190-check selftest updated + passes.
- **D287 — Ledger salary-page layout redesign (layout-only).** Status banner + `<details>` accordion. Proven layout-only (zero change to any form/action/name/route/compute). SUPERSEDED by D288 — not installed; technique reusable inside the register salary page.
- **D288 — CONSOLIDATION: one salary system, in the register.** Retire the two-engines-on-the-same-staff arrangement. `/register/salary` becomes the single place a month is computed/approved/locked; the ledger reverts to the money-book (loans, advances, perks, night-duty, ad-hoc fines, i-card replacement) + loan machinery. Reverses D283's "no ledger coupling" on purpose: register salary now READS the ledger's approved salary-money rows. Delivered as a staged, dual-run, parity-proven migration. OT removed; flags → tap; outstation read from the register grid.

**Finding F-65 — a new SQLite table needs `--init` BEFORE the service restart, or the page 500s.** The Stage-B lock page queries `locked_run`; installing code without `--init` → table missing → 500. Standing rule: when a delivery adds/alters a table, the runbook runs the app's `--init` before `systemctl restart`, and the md5 is checked so a truncated/placeholder file is caught. (First Stage-B miss: a literal `PYBIN` placeholder in the runbook meant the venv `--init` never ran — always paste the real `/root/wa/venv/bin/python3`, never a placeholder.)

**Decisions: D283–D288 (minted). Findings: F-65 (minted). This was Session 162.**

---

## §S163 — D288 EXECUTED: standalone register salary proven to the rupee (July); register-owned EARLY-BIG rulings shipped (10 Aug 2026, FULL)

Two live files changed and were installed after a Phase-0 that verified all ~25 canonical rows clean. The whole session was money-code (payroll) under the "hard-bake before code" discipline; every step was build → sandbox py_compile → selftest → VPS-venv py_compile → owner install over a timestamped backup → md5 verify.

**Part 1 — D289: the standalone register salary engine (D288 executed).**
The live S162 engine already borrowed the ledger's net (`load_current_net` → `staff_ledger.compute_salary`) and added a register delta — which permanently coupled the two systems and could double-count uniform/i-card. The rewrite makes the register compute the WHOLE take-home itself from primitives:
`net = base − marks − early − uninformed − excess_absent(outstation-adjusted) − early_big + extra_duty + outstation − dress − i_card − C_model_deduction + encashment + ledger_money_fold + prorate`. **OT removed.** **Incentive is out of the month → the annual pot** (owner-confirmed: July incentive goes to the pot). The old ledger net is kept as a **shadow column** with a per-staff **Delta** so any gap is visible until parity is proven, then dropped.
Three technical rules make parity correct and were baked in (owner stated, not adjudicated):
- **C-model gated on coverage.** base÷30 cuts and encashment need leave-sanction data; a month with no register grid rows (July, pre-register) can't reclassify absence → no base÷30 cut, no encashment; those absences keep the attendance layer's ₹100 excess-absence treatment. This is what makes the July anchor conserve.
- **Uniform/i-card per-month source.** Grid if the month is register-covered (Aug onward, D286), else the ledger's FINE_UNIFORM/FINE_ICARD rows (July). The ledger fold ALWAYS excludes uniform/i-card.
- **Ledger fold = `month_adjustments` MINUS {FINE_UNIFORM, FINE_ICARD}** — parity-safe for every non-excluded category (incl. OTHER), not just the five §D named. `SALARY_EXCLUDED` (ADVANCE_ISSUE, LOAN_CAPITALISE, LOAN_SKIP, PERK, SALARY_PAID) hard-checked at import against the ledger's own set (fail-loud on drift). Excess-absence fine re-derived on genuine absences (covered) / rulings-outstation only (July). Incomplete run (ledger unreachable / base missing) → `final_net=None`, unlockable (D283). BASE MISMATCH (register base ≠ staff_master.csv) raised as a problem.
The engine-only drop preserved the three signatures the page calls (`build_report`, `render_html`, `total_payout`) + `_CSS`, so **staff_register.py needed no change for Part 1** (byte-identical). Signature: `build_report(ym, db_path=, att_dir=, *, ledger_rows=, rulings=, earlybig=, bases=)` — injectable for tests, defaults read the live ledger's own read-only loaders.
**PARITY PROVEN (July, owner ran on VPS, independently re-derived from the uploaded page):** old total (shadow) = **₹1,07,447.00** to the rupee; new monthly total ₹1,07,073 + incentive-to-pot ₹373.34 = ₹1,07,446.34 = the anchor to within **₹0.66** (sub-rupee rounding: whole-rupee net vs paise-level incentive on the two staff who earned it). All 12 rows reconcile: 10 with Delta 0, 2 with Delta = minus their incentive. No BASE MISMATCH, no ledger problems, all rows correctly flagged "no grid" (uncovered). Conservation is the parity proof for July.

**Part 2 — D290: register-owned EARLY-BIG rulings (so the ledger salary page can be retired).**
Early-big genuine/waived verdicts previously lived only in the ledger's `salary_rulings_<month>.json`, entered on the ledger salary page. The register now owns them: new `earlybig_ruling(ym, staff, ebdate, verdict, ruled_by, ruled_ts)` table (one writer = the register app); a doctor-only screen at `/register/salary/earlybig` lists each big early exit from the same `/root` attendance CSV (`deductions_extras_<ym>.csv`, fail-loud on note drift) and rules each genuine (deducts) / waived (default). The engine reads register verdicts and OVERLAYS them over the base per key (register wins; ledger fallback keeps July working; base-only keys survive). Un-ruled events default to waived (matches the ledger) but are COUNTED and surfaced as an "⏱ Early-big · N to rule" badge on the salary page so a month can't be locked with events silently ignored. A LOCKED month is read-only. Ruling is gated on the salary cap (Manoj + Bhawna, like ad-hoc fines); locking stays Manoj-only.
Substantive logic lives in the engine (testable): `earlybig_events`, `load_register_earlybig`, `_rulings_for` overlay, `render_earlybig_html`, `earlybig_unruled`, `EARLYBIG_SCHEMA`. The register change is thin: one table, two routes (GET/POST, POST writes with audit + locked-guard + idempotent `executescript` of the schema), a nav badge, a page shell — validated by a full F-63 authenticated Flask test-client smoke (GET 200 with form/event/amount; POST persists + audit row; salary page shows the badge; locked month rejects writes; non-salary user 403) and a core-route regression (`/`, `/salary`, `/staff`, `/leave`, `/health` all 200).

**Install md5s (live after this session):** `staff_register.py` `ded3ae8f172bcc84a48f282ee3f41993`, `salary_engine.py` `303c7059fa846b9e51c3c59cac666b76`. `--init` run (creates `earlybig_ruling`); `systemctl restart staff-register` → active. `staff_ledger.py 92665b64`, `portal.py 43db2131` unchanged.

**August observed (uncovered preview):** August currently computes as uncovered — the register holds no August grid data yet (owner has not begun daily entry for August). It conserves exactly like July (only incentive→pot differs, resid ₹0.33), refuses to lock (ledger month not closed, not month-end). The covered path (C-model, grid fines) is therefore NOT yet exercised — it needs a month actually captured in the register. This surfaced F-67 (below).

**F-66 (install-safety) and F-67 (latent coverage-detection)** minted (see Fault Register). No incident report (the register-down window during the botched upload was recovered from `.bak-S163eb` backups within the same session; the md5 gate prevented a mis-paid run).

**Not retired yet (staged, safe):** the ledger salary page still stands as the dual-run fallback; `compute_salary` stays dormant. Retire (redirect ledger salary → `/register/salary`) only after August reconciles at month-end and one real register-captured month is paid and matched; delete `compute_salary` the EOS after.

**Decisions: D289, D290 (minted). Findings: F-66, F-67 (minted). Next free decision: D291. Next free finding: F-68. This was Session 163.**

---

## §S164 — F-67 fixed (coverage keys off approved capture), pending-review board, Shivani activated, portal user admin, consolidated dossier

**Session 164, 2026-08-10. Verify-first; all five items built from md5-verified live copies, installed under F-66, verified live. Money math not re-touched beyond the coverage fix; F-31 preserved throughout.**

**1. F-67 / D291 — salary coverage fix.** Confirmed via `systemctl cat staff-register | grep SR_` and the cfg module that no coverage override existed. In `salary_engine.load_register()`, replaced `covered = (daily_register rows > 0)` with `covered = EXISTS(day_review WHERE reg_date LIKE 'YM%' AND status='approved')`, guarded for a missing `day_review` table (→ False). Chose `'approved'` over any-row precisely because the live DB holds a stray 2026-07 **draft** day_review row that must not flip July to covered (it would break the ₹1,07,447 parity). Added selftest CASE A (approved seed), CASE B (stray-July-draft guard), and new **CASE E** (captured month, zero exceptions → covered=True, base30_ded>0). Proved CASE E fails on the baseline engine (`303c7059`, covered=False, base30=0) and passes on the new one. Installed `salary_engine.py 5514918067243e3f39e7074144ee7db4`, VPS selftest OK, restarted `staff-register`. Owner uploaded July: all rows "no grid" (uncovered), TOTAL ties ₹1,07,447. **F-67 CLOSED.**

**D291 (full text):** Salary coverage detection keys off `day_review.status='approved'` (checker capture), not `daily_register` exception rowcount. `'approved'` specifically (not any row) so a stray draft cannot flip a month; a missing `day_review` table means uncovered. This is the correct signal because minimal-input entry means a genuinely captured month can carry real biometric absences with zero exception rows — the old rule mis-flagged such a month uncovered and skipped the base÷30 C-model cut, overpaying (proven ₹2,100 on a test month).

**2. D292 — pending-review board.** Added `/register/review` to `staff_register.py`: checker-pending = draft `day_review` dates (each with the maker stamp + a one-click Approve, D272-safe via `can_check_approve`); maker-pending = working dates with no `day_review` row up to today (future dates shown as a quiet "upcoming" note, not a nag); progress = approved / working days (clinic-closed holidays excluded); month nav; `/approve` gained `back=review`. All keyed off the existing `approval_blockers(con,ym)` so the board equals the lock C-rule and the two can never disagree. Added `GET /register/review/counts` → `{to_enter,to_approve,show_approve,ym,role}` with `show_approve` true only for checker/override (makers never see an approve count — one brain for the role rule). F-63 authenticated test-client hits added to selftest. `day_review` already carried maker/checker timestamps (no capture rebuild — surfacing only). The portal Staff-Register tile lands on the board and shows role-aware counts (✍️ N to enter · ✅ M to approve).

**3. F-68 — same-origin counts proxy.** The portal tile's browser `fetch` of the register counts endpoint returned nothing: OpenLiteSpeed's reverse proxy strips/omits the CORS/Origin headers a credentialed cross-origin fetch needs. Added portal `GET /portal/review-counts` that server-side calls `REGISTER_COUNTS_URL` (default `127.0.0.1:8044/register/review/counts`) over localhost, forwards the SSO cookie, 2s timeout, empty `{}` on failure; the tile JS now fetches the portal's own path. Confirmed live for manoj (doctor): "✍️ 10 to enter · ✅ 0 to approve" (10 = August working days to date with no entry — the board doing its job). Standing pattern: serve any cross-app widget from the caller's own origin via a localhost proxy, never a cross-origin browser fetch.

**4. D293 — Shivani activated.** Roles are `_cfg`-driven (env → `staff_register_config` → default; empty=unset). No env/config override existed, so the **code default** `SR_INACTIVE_MAKERS` was changed `"shivani"` → `""`. Shivani is now an active maker identical to Alisha; alisha/shavez unchanged. Verified live on the manoj-doctor portal.

**5. D294 — portal user management.** Read `/root/portal/clinic_users.py` (PBKDF2 store: add_user / set_role / set_password / set_active / del_user / list_users(no hashes) / bump_epoch; roles doctor/manager/staff; store `/root/portal/clinic_users.json` chmod 600, epoch=10). Built a **Manoj-only** `/portal/users` admin (list + add + set-role + reset-password via JS-prompt POST + activate/deactivate + delete). Tile gated by `PORTAL_USER_ADMINS=manoj` (`roles=[]` + `USER_TILE_EXTRA["manoj"]`; route `abort(403)` for non-admins); guards forbid deactivating/deleting self or the last active doctor. Portal "active" = the login master switch (blocks all apps); per-app maker/checker powers stay per-app; deactivation blocks future sign-ins only (the epoch is global). Added an Admin section to GROUP_ORDER. Verified live: Admin → 🔑 Manage Users present for manoj only.

**Install chains:** staff_register `f24664db → 7c6bae8b → cef76859`; portal `bd37157f → 5cf81346 → 4b75ee7b`; salary_engine `303c7059 → 5514918`.

**Install md5s (live after this session):** `salary_engine.py 5514918067243e3f39e7074144ee7db4`, `staff_register.py cef768594bee5360a388e66028456495`, `portal.py 4b75ee7b50b5530eaca7c347e4a432d0`. `staff_ledger.py 92665b64` and `att_month_report.py v2.5 e64cad19…` unchanged. Repo commit owed (code-only, F-31): salary_engine + staff_register → `staff_register/`; portal → `portal/`.

**EOS deliverable — consolidated sole-reference dossier.** `Salary_Attendance_Master_Dossier_v1_S164.md` (`669917fcaca3fece3a3f6caa1899edbf`) consolidates the salary + attendance + staff-daily-register machine into one authoritative reference with a full troubleshooting section (symptom → cause → fix across salary, attendance, register, portal, install). It **supersedes** `Attendance_System_Dossier_v1.2` (S153), `Salary_System_KB_v1` (S157), and `Staff_Daily_Register_Dossier_v1.1` (S161), which are retained historical.

**Decisions: D291, D292, D293, D294 (minted). Findings: F-67 (CLOSED), F-68 (minted). Next free decision: D295. Next free finding: F-69. This was Session 164.**

---

## §S165 — CANONICAL_MANIFEST regenerated (S161→S164 staleness closed); D223 gist tile DELIVERED end-to-end (portal_gist.py + portal.py); Darpan outstation ruled in-salary; F-69/F-70 raised (10 Aug 2026, FULL EOS — one NEW live VPS file + one live portal.py replaced + one cron armed)

**Session 165, 2026-08-10.** Verify-first throughout; every source binding proven against the live artefact before code was trusted (D160/D188). Two live installs (new `portal_gist.py`; `portal.py` replaced), one cron armed, the manifest regenerated.

**0. Phase 0 caught a stale linchpin.** `CANONICAL_MANIFEST.md` in project knowledge was at **S161** while the S162–S164 EOS had advanced every other Tier-0/1 doc — so Phase 0 had no current manifest to verify against. Reconciled by cross-checking the three S164 Tier-0 docs against each other (all agreed) and **regenerated the manifest to S164** (interim), then to S165 at this EOS. The 20 unchanged Tier-1/2 docs were re-hashed live and **all matched their prior pins (zero drift)** — the stale manifest's doc hashes were correct; it was only missing the S162–S164 bumps + delta blocks. Project-KB reconciliation: no canonical file missing; two superseded stragglers flagged for deletion (`START_HERE_SESSION_162`, `Staff_Daily_Register_Dossier_v1_0`).

**1. D295 — Darpan outstation +₹250/night is IN salary.** (Closes the S163-open question.) The S163 register engine already folds register-grid outstation into the register salary, so "in salary" is the existing behaviour; to be verified as not double-counted against any cash-outstation record at the next salary touch.

**2. D296 — D223 GIST TILE DELIVERED (two units + a JSON contract).** The ~40-session-deferred doctor's bird's-eye is live.
- **Unit 1 — `portal_gist.py`** (`55e111d71e95032c21234ae540a49431`, 400 lines, selftest 21/21): a read-only builder that reads the live sources and writes ONE file `/root/wa/portal_gist.json` (sole writer, D235). Metrics v1: (1) pipeline health from `/root/wa/recordings-archive/flag_investigator_results.json` (`never_recorded_7d` top-level; `missed` from the sparse `counts` dict, absent = a legitimate 0; `escalate_lokesh`); (2) call volume from `Call_Durations` (`category` incoming/obd → in/out; window on the `ended_at_ist` string; `status=='probe'` excluded); (3) unfiled = `Callbacks_Today` rows with a blank Staff Status; (4) 3rd-strikes = distinct `K_Strikes.Mobile` with `Tries≥3` in 7d (When column). Metric 5 (verdict awaiting-referee) DEFERRED — the verdict store (`Call_Verdicts`/`Doctor_Verdicts`) is NOT on this Sheet; it lives in Product B's `recordings-archive`. FAIL-LOUD (D236): a bad source → null field + note + `sources_ok:false`, never a silent zero. Cron `*/30 9-20 IST`. Live dry-run matched the probes exactly (66 in/13 out today, 256/66 7d, 8 unfiled, 0 strikes, pipeline all-clear); first real write done + cron armed; clock confirmed IST.
- **Unit 2 — `portal.py`** (`4b75ee7b50b5530eaca7c347e4a432d0` → `f0655abd3221d64daf07441270488344`, 1225 lines): a doctor-only "📊 Clinic Gist" tile (top of the Clinic group) whose face shows a live one-liner (`/portal/gist-data`), plus a `/portal/gist` bird's-eye page reading `portal_gist.json`. Both routes doctor-gated (`doctor_required`, mirroring `home()`'s trusted-device-defaults-to-doctor); both read-only; a missing/stale file is SAID on the page (stale banner past `stale_after_min`=45), never a fake zero. Built from the md5-verified S164 live copy (F-66, provenance proven; uploaded direct as `portal.py`, verified in place before restart; `portal.py.bak-S165gist` kept). F-63 test-client run PASSED (200 authed, gated unauth 302, tile on `/portal`, gist-data serves). Restarted; live `/portal/gist` unauth → 302; owner confirmed the rendered page (all five cards correct, "Updated 34 min ago", no stale banner).
- **The contract (D296 core):** `portal_gist.json` is the seam. The deferred metric 5 and the future console analytics slot in by ADDING keys — the portal tile needs no rework. Extends D236 (consume, don't recompute) + D246 (contract-seam pattern). *The D223 no-rework promise, made concrete.*

**3. F-69 — `Call_Feed` dead since 28 Apr 2026.** While binding the gist's call-volume source, `Call_Feed` (the name-free feed the Follow-Up Tracker reads; produced by `CallField`/`CallFeed.gs`) was found frozen at April (2,971 rows, newest 27–28 Apr, 0 today) — its upstream writer stopped ~3.5 months ago. Volume was rebound to the live `Call_Durations` (1,648 rows, 79 today). The Follow-Up Tracker reads `Call_Feed`, so its incoming/outgoing reconciliation is likely silently degraded since April — find and restart the writer next session.

**4. F-70 — the Callback Tracker Core Dossier lags the live Sheet.** The dossier frames diagnosis as Docterz-side, but `Patient_Master` carries a live **Diagnosis** column (present for most patients), and `Followups_Today`/`Followup_Escalations` carry it too — so the console's diagnosis column is buildable now, not Docterz-blocked. The dossier also lacks the real tab inventory (there is **no** "Escalations" tab; 3rd-strikes live in `K_Strikes.Tries`; the Sheet has 19 tabs). Owner corrected the assistant from the live Sheet — the D160/D188 rule in action (a doc is not provenance). Dossier update owed.

**5. Records.** New live artefacts: `portal_gist.py` + its cron; `portal.py f0655abd…`. Repo commit owed (code-only + canonical-docs mirror S162–S165). Manifest regenerated (S161→S164→S165). The doctor's **Call-Log & Staff-Performance console** (the big ask) is designated **D297** for next session — its own signed contract first, then build; the gist is its bird's-eye header, the console the drill-down; the AI-verdict store must be located to bind both. Notion catch-up (S151–S165) still owed (connector).

**Decisions: D295, D296 (minted). Findings: F-69, F-70 (minted). Next free decision: D297. Next free finding: F-71. This was Session 165.**

---

## §S166 — D297 CALL-INTELLIGENCE CONSOLE designed, vetted & SIGNED (verdict store located; follow-up-tracker architecture mapped; 14-track program incl. revenue); F-71 raised (10 Aug 2026, EOS-light — NO live code touched)

**Session 166, 2026-08-10.** No live code, config or trigger changed. The product is a fully-vetted, build-ready contract for **D297** — the doctor's Call-Intelligence Console — plus its verified ground truth, plus a call-quality rubric out for the owner's red-pen. Phase 0 passed clean.

**0. Phase 0.** Manifest S165 verified (self `4cdeacd9…`); 26 canonical docs md5-matched their pins; 7 unpinned all benign (closed incidents + reference/template docs — no drift). Noted for a future pass: pin `START_HERE_PROMPT_v5`.

**1. D297 designed by live probing, not memory (D160/D188).** Every data source was located and confirmed before a line of design was trusted:
- **Verdict store = two Sheets.** Clinic Callback Tracker (`1USjArkq…`) holds `Call_Durations`(spine, 1652 rows), `Call_Recordings`, `Call_Transcripts`, `Followup_Outcomes`, `Patient_Master`, `Followups_Today`/`Settled`. **Call Audit (Doctor Only)** (`1rq9VvB5…`) holds `Call_Verdicts`(2195 rows, current to today — pipeline alive), `Verdict_Review`, `Doctor_Verdicts`(19 rows, last 29 Jun — referee loop went cold). One service account (`GOOGLE_SA_KEY`/`WA_SA_KEY`) reads both.
- **Join Key = `{phone10}_{call_start_unix}`** unifies the chain; `Call_Durations` bridges via `recording_filename → Call_Recordings → Join Key`. `Call_Verdicts` is nearly a whole console row (35 cols incl. Recording/Transcript Link, Claimed vs AI outcome, flags). Diagnosis is live in `Patient_Master` (F-70). Staff: outbound `Outbound_Log.Agent`, incoming `Call_Verdicts.Agent`, names via `Agents`. Net-missed authoritative in `Daily_Summary`.
- **The follow-up tracker (clinic-PC engine) already feeds the VPS.** `push_followups_today.py`→`Followups_Today`(calling list)+`Followups_Settled`; `push_patient_mirror.py`→`Patient_Master`(nightly, incl. Diagnosis); `processor.py` joins `visit_ledger`(seen) vs `followup_ledger`(due, "DIKHA CHUKE→RESOLVE"). So conversion (Track L) and no-show (Track N) read pushed data — no tracker migration needed. Revenue lives in the tracker (`revenue.py`, `/finance`) and is brought into scope via a lightweight daily push (Track V).
- **Most of the ask is a PORT, not net-new.** The GAS dashboard (`dashboard/*.gs`) already encodes net-missed (`Netting.gs`), MyOperator missed reconciliation (`MyOperator.gs`), send-back-with-reason (`OutcomeLog.gs`/`WebApp.gs`), unknown-caller handling and compliance metrics. D297 rehomes these in the VPS portal and retires the GAS dashboard.
- **Recording sizing** (probe): ~217 KB each; 60 days ≈ 0.30 GB; full history ≈ 0.28 GB; disk 88 GB free → a 60-day/1 GB local cache is trivially safe (Track K); Drive untouched.

**2. The program (D297).** Fourteen tracks, hubbed on the portal (single evolving point): C (log·staff·two-way net-missed threads·latency·filters·CSV), K (recording cache), reconcile/compliance/leads (port GAS into C), M (marketing marks + block-list), send-back (port), G (digest→portal tile), R (referee in console + `Refereed By` + self-review flag + nightly Drive export; retire AppScript referee + `verdict_review.py`; repoint `daily_digest`), T (transcript cached VPS-side), J (judge grades opening/info/closing/digression — rubric out for red-pen), L (new-caller conversion), N (no-show callbacks), **V (daily revenue in portal)**. Sequence C→gist-5→G/M/send-back→R→L/N/V→T/J. Architecture: builder `portal_console.py`→SQLite `console.db` (one writer, fail-loud, cron `*/10 9–21`) → doctor-gated portal reads. Full spec + verified ground truth in **`D297_Call_Console_Contract_v4_FINAL.md`** (`42991579…`).

**3. Referee redesign (owner).** Sole referee = Manoj; the console becomes the entire referee system; the old AppScript UI + its Sheet flow + `verdict_review.py` retire; dispositions live in `console.db` with a nightly Drive export for durability (the one durability concern raised and resolved). `daily_digest.py` — the only other reader of `Verdict_Review` — is migrated to read `console.db`, which is precisely what frees `verdict_review.py` to retire.

**4. F-71 — an uploaded PC zip carried PHI + secrets (kin F-56).** The follow-up-tracker zip included `patient_master.csv`/`patient_diagnosis.csv` (PHI), revenue ledgers, and `.secret_key`/`.env` (secrets). Handled: **code-only** read, **nothing committed**, no data printed. Action: treat that key/.env as potentially exposed → rotation check; future uploads code-only.

**5. Records.** No live code touched. `D297` minted (signed contract). `F-71` minted. Rubric `.docx` out for the owner's red-pen (gates only Track J). Live file versions unchanged from S165. **Next session: BUILD D297 Stage A** (the `console.db` builder) off the v4 contract.

**Decisions: D297 (minted). Findings: F-71 (minted). Next free decision: D298. Next free finding: F-72. This was Session 166.**

## §S167 — D297 CALL-INTELLIGENCE CONSOLE, STAGE A BUILT (A1·A2a·A2b·A3): console.db spine live, reconciled to Daily_Summary + completeness-corrected (11 Aug 2026, FULL EOS — one new live VPS builder)

**Session 167, 2026-08-11.** Phase 0 clean (manifest current at S166; 27 canonical rows md5-matched; working memory was stale at S164/165 and reconciled to the manifest — the linchpin wins). Built **D297 Stage A** — the `console.db` builder — off the signed v4 contract, grounded throughout in live source code, not memory (D160/D188).

**0. Approach.** New builder `portal_console.py` at `/root/wa/`, read-only over the two Sheets (`spreadsheets.readonly`), MyOperator `/search`, and Drive; **sole writer** of `console.db`. **Full-rebuild-idempotent** (atomic tmp→replace) — chosen over watermark-incremental because the volume is a few thousand rows and it sidesteps any assumption about the un-pinned `ended_at_ist` timestamp format. Every column located by **header name** at runtime; a missing required column HALTs with the live header printed (D188). Offline gate `--selftest` (synthetic fixtures through the *real* transform path) + fail-loud guards; every stage then proven against live data by `--dry-run` before `--build`. Selftest ended at **35/35**.

**1. A1 core.** Joins `Call_Durations`(spine, `status='probe'` excluded → 1651 kept +1 probe = **1652**) × `Call_Recordings`(bridge `recording_filename → MyOperator Filename → Join Key`) × `Call_Verdicts`(**2195**; NOT-FILED = blank Claimed Outcome, amber) × `Patient_Master`(diagnosis, F-70) × `Outbound_Log`/`Agents`. The "61% join-match" alarmed at first read then decomposed cleanly: **641 calls are missed with no recording** (correctly no verdict), only **1** recorded call was unmatched — of the ~1010 recorded calls **99.9% matched**. `unjudged` reasons reconcile to the row (641 no-recording + 1 unmatched + 36 verdict-error + 4 judge-pending = 682). Conversation threads (group by phone10); latency (call `captured_at_ist` → transcript `Transcribed At` → judge `Judged At`).

**2. F-72 (fixed live).** The first live dry-run crashed in `build_latency`: `can't subtract offset-naive and offset-aware datetimes` — one timestamp column parses tz-aware (`+05:30`), another naive. Fixed centrally: `parse_ts` strips `tzinfo` → one naive IST wall clock; a genuine cross-zone source would surface as a ~constant offset in the latency stats, not silently (F-41 lineage). Re-proven by a targeted aware-vs-naive regression.

**3. A2a — net-missed rule ported from `Netting.gs`/`Config.gs`.** The first reconcile ran high vs `Daily_Summary`. The live rule: net-missed requires an **incoming** missed leg (outbound-miss-only is NOT a candidate) and is resolved by **any connected leg in either direction** (`CFG.RESOLUTION_MUST_BE_AFTER=false`). Ported faithfully — but on the real data it moved the numbers by **zero** (outbound-miss-only conversations barely exist here). Correct to hold, not the cause of the deltas. (My prediction that it would shrink the deltas was wrong; the artefact corrected me.)

**4. The real cause + A2b.** `MyOperator.gs` showed `Daily_Summary` is computed from the MyOperator **`/search`** log — a *different source* than our webhook-fed `Call_Durations`. Our count ran *high* (7 vs 3, 11 vs 7): we were missing the resolving *connects* MyOperator has, so reached numbers still looked open. **F-73**: the two live files disagreed on the `/search` `status` vocabulary; resolved by read-only `--myop-probe` — the API returns numeric `status {1,2}` + `event {1,2}`, so Netting's numeric reading is authoritative. A2b (`--with-myop-reconcile`, `/search` client ported verbatim from `flag_investigator.py`) then **reproduced `Daily_Summary` exactly (14/14 real days, delta 0** — same source + same rule) and corrected the over-counted open list **154 → 134** (20 conversations MyOperator shows were reached). `myop_daily` table + `resolved_by='myop'` flags persisted. The correction must ride the refresh cron or it is lost each rebuild.

**5. A3 — transcript back-pull.** Transcript text lives in Drive as `text/plain` (`call_transcription.py`). Back-pulled read-only (`get_media`) into a **persistent** `transcript_cache.db` (keyed by Join Key, survives full rebuilds, incremental — only uncached keys pulled) and merged into `console.db.transcripts.text`. Drive port verbatim; Drive never written/deleted (owner rule). PHI-safe probe (sizes only, never text) green: **1303/1447** rows need pulling; a 20-batch seed proved write+merge (a 20→22 merge exposed 2 duplicate transcript rows per Join Key — harmless; Stage-B dedupe noted); full seed resumable.

**6. Records.** `console.db` + `transcript_cache.db` hold full numbers + diagnosis + patient speech → **F-31/F-49: gitignored, never in repo/kit**. `portal_console.py 81581a6cec84b4414827dc71d35548d3` repo-commit-owed → `launcher/` (path to confirm alongside `portal.py`/`portal_gist.py`). **D298 minted** (console.db build architecture). **F-72 + F-73 minted.** No incident (both live faults caught in dry-run before any consumer existed — nothing reads `console.db` yet). **Stage A COMPLETE (A1·A2a·A2b·A3).** Live files otherwise unchanged from S166.

**Decisions: D298 (minted). Findings: F-72, F-73 (minted). Next free decision: D299. Next free finding: F-74. This was Session 167.**


## §S168 — D297 CALL-INTELLIGENCE CONSOLE, STAGE B1 BUILT (the `/portal/console` page) + STAGE 2a agent-backfill built & proven (11 Aug 2026, FULL EOS — one live VPS file `portal.py` updated; one builder change delivered)

**Session 168, 2026-08-11.** Phase 0 clean (manifest current at S167; all Tier-0 rows md5-matched, no drift). Built **D297 Stage B1** — the doctor-facing console page — and, on a live-data finding, built **Stage 2a** (the staff-agent backfill in the builder). Grounded throughout in md5-verified live files (D160/D188).

**0. Stage split.** Stage B was split: **B1** the `/portal/console` page (portal-only, ships now); **B2** recording proxy + Track-K `rec_cache` (deferred); **B3** the refresh cron (deferred). No-shows deferred to Track N (owner: "b defer"). Recordings link to Drive for now.

**1. B1 — the console page (`portal.py`).** Doctor-gated `/portal/console` + `/portal/console.csv`, reading `console.db` only (fail-loud/stale-aware, D236), added under the existing `PAGE_HEAD` shell with a "🎧 Call Console" tile in the Clinic group. Four views (Call log · Conversations · Staff · New Leads), cascading filters (Direction → Answered/Missed/Net-missed → Agent → Flag → Date + free-text), CSV export. Data helpers: read-only `_console_conn`, `_console_meta`, dedup views `_DV`/`_DP`/`_DPHONE`, `_query_log/_facets/_query_conversations/_query_staff/_query_leads`, day-grouping. Built rev1 → rev2 → **rev3**; F-63 gate met (Flask test-client route hits, 19/19). **rev2 `7a862f74…` was installed live** (after a WinSCP overwrite mishap that briefly rolled to `f0655abd…`, then re-installed correctly — the md5 gate caught it; F-66 discipline held). **rev3 `54c239a3c645860cfd2914e5262e9e08` delivered — NOT yet installed** (owner mid-review at session end): unified expandable **Call Detail** macro (number·name·diagnosis·last-visit·clinic-ID·staff·outcome·AI-verdict·your-review·flags·note·recording·transcript) used across log/threads/leads; day-grouped collapsible log; clearer New-Leads.

**2. F-74 — join fan-out (fixed).** rev1 showed impossible totals (Incoming **2276** > all-calls **1651**): `LEFT JOIN verdicts` multiplied rows (2195 verdicts / 1651 calls — re-judged calls have several) and `LEFT JOIN patients` compounded it. Fixed with dedup subqueries `_DV` (verdict `MAX(id)` per join_key = newest wins) + `_DP` (patient per phone10). Counts reconciled. Caught in the browser at build — no consumer harmed.

**3. Live-data punch-list (folded into rev2/rev3).** ISO `+05:30` timestamps split via `_split_dt`; phone10 blank on 505 outbound rows recovered from the join_key prefix + verdict number (names then resolve); the AI-verdict column shows `ai_outcome` with fail-loud semantics ("pending" only when no verdict; "error" vs "no outcome" distinguished — 919/2195 verdicts carry a blank ai_outcome, which had looked alarmingly "pending"); recording link falls back to the `recordings` table; transcripts render inline; last-visit + clinic-id + your-review (doctor_flag/note/final_outcome) surfaced everywhere.

**4. Staff-sparse root cause + Stage 2a (the real prize).** The console's staff column looked Alisha-only. Read-only `/search` probes proved the mechanism: the **handling agent is the `_source._us` entry with `vl=='received'`; its `ky` is the MyOperator UserId**, which maps **100% to `Agents.UserId`** (483/483, zero unmapped). The true 14-day spread is **Shivani 217 · Alisha 182 · Reception Mobile 54 · Shavez 28 · Manoj Bhati 1 · Dr Manoj 1** — "only Alisha" was a **verdict-attribution artefact** (many answered calls unjudged, or their verdict carried a blank agent). Incoming-missed has only `missed` entries → correctly no handler. Match to our calls is by `{phone10}_{start_time}` = the join key (exact 391/663; misses are incoming-missed + few-second start offsets → proximity fallback).

**5. Stage 2a built + proven (`portal_console.py` builder change).** Started from the exact live bytes (`81581a6c…`). Added `_recv_ky(src)` + `build_call_agent(conn, sources)`: an **additive `call_agent` table** (`join_key·agent·department·matched_how`), mapping `_us[received].ky → Agents.UserId → name`, matched by **exact join key then ≤90s proximity** (same number, nearest start) — reusing the `/search` hits already pulled in `myop_reconcile_layer` (no extra API). Coverage is printed in `_print_myop`, so **`--dry-run --with-myop-reconcile` MEASURES coverage in-memory before any install**. Builder `--selftest` **35/35** (existing paths intact); `build_call_agent` unit test **6/6** (exact · proximity · missed-skip · unmapped-skip). Delivered as `portal_console.py` **`00b2175fa11e7d046befa4531a5834b6`** — **NOT installed**; the S168-close pending step is the owner uploading it as `/root/wa/portal_console.new.py` and running the dry-run to read the coverage number (the file was not on the VPS yet at session end — `md5sum` returned "No such file", i.e. WinSCP had not placed it).

**6. Decisions + records.** **D299** (agent attribution + backfill) and **D300** (console display/dedup rule + broadened staged build order) minted. **F-74** minted (join fan-out). The broadened owner brief was captured for staging: after 2a → capture AI reason/evidence · Follow-ups tab (Settled due−seen + booked-not-visited no-show) · **Track R** your-verdict via curated dropdowns + free text → `dispositions` (one writer, AI-training feed) · **push-back** to the staff callback tracker in its OWN calling-list tab (two sections: auto "booked-not-visited" + manual "Dr Manoj list"), never clobbering `push_followups_today.py` (D235). B2/B3 deferred; no-shows → Track N. **Live now:** `portal.py` at **rev2 `7a862f74…`** (rev3 `54c239a3…` delivered-not-installed); `portal_console.py` unchanged live at `81581a6c…` (Stage-2a change `00b2175f…` delivered-not-installed). All other live files unchanged from S167.

**Decisions: D299, D300 (minted). Findings: F-74 (minted). Next free decision: D301. Next free finding: F-75. This was Session 168.**


# §S169 — Stage-2a agent attribution LIVE in `console.db`; portal rev4 BUILT + F-63-PASSED (staged, not installed); owner console review → rev5 punch-list (D301, D302)

*Session 169 · 2026-08-11 · FULL EOS. Phase 0 clean: `CANONICAL_MANIFEST.md` current at S168, all 29 rows md5-matched their pins, zero drift; `Clinic_Estate_Master_Inventory_v1.md` named "v1" but content-hashed to the v1.7 pin (provenance = hash, D188). No open incident.*

**0. The ⭐ top task (from S168): measure Stage-2a coverage, then wire it through.** Executed end-to-end on the data side this session.

**1. Builder install + `console.db` rebuild.** The delivered Stage-2a builder was uploaded to `/root/wa/portal_console.new.py` and md5-verified in place = **`00b2175fa11e7d046befa4531a5834b6`** (a few "No such file" attempts first while WinSCP finished, then the hash matched — F-66 gate held). Dry-runs (read-only, wrote nothing) measured coverage: **`--days 30` → 75%** (763/1017, all exact); **`--days 60` → 100%** (1017/1017, all exact, proximity 0), and the 60-day `/search` reconcile matched `Daily_Summary` on **52/60 days** and corrected net-missed-open **155 → 109**. A transient `APIError: [503]` on a second 60-day dry-run was a Google-side hiccup opening the sheet (crashed at `_open_clients` before any read; nothing written) — retried. **Decision D301:** build the agent backfill at **`--days 60`** — 100% vs 75%, all exact, because `/search` is time-windowed and 60 days reaches the back-catalogue while the daily cron stays incremental. Before the write I read the builder source (`cmd_build` → `myop_reconcile_layer(conn, token, days)` → `build_call_agent(conn, sources)`, which `DROP`s + `CREATE`s `call_agent`, inserts, `commit`s; `cmd_build` atomically swaps `.tmp` → `console.db`) and confirmed `--days` flows into the build and the table persists — so `--build` **needs** `--days 60` explicitly (default is 3, which would have tagged only 3 days). Promoted the builder: `cp portal_console.py portal_console.py.bak-S169` → `mv portal_console.new.py portal_console.py` → md5-verified live = `00b2175f…`. Ran **`--build --with-myop-reconcile --with-transcripts --days 60`**: Stage-2a backfill **1023 tagged (exact 1023 + proximity 0) = 100%**, net-missed-open **155 → 108**, transcripts back-pull 31/31 (0 errors), `BUILD complete … console.db written atomically`.

**2. Proof-by-artefact (F-41 discipline).** The build's "1023" is computed *before* the atomic swap, so a read-only query against the **live** `console.db` confirmed the table landed: **`call_agent` = 1001 distinct rows, `matched_how` all `exact`** — Shivani 457 · Alisha 346 · Shavez 104 · Reception 91 · Dr Manoj 2 · Bhati 1. **Reconciliation of 1023 vs 1001:** `call_agent.join_key` is PRIMARY KEY, so 22 duplicate-join_key call rows (same phone + same start-second = the same call double-logged, same agent) collapse via `INSERT OR REPLACE` — 1023 counts call *rows*, the table stores *distinct* join_keys. Not a fault (same agent on any duplicate); documented so it is never a phantom mystery. **The "staff-attribution prize" is realised on the data side: the true handler now sits on every answered call in `console.db`.**

**3. Portal rev4 — built + F-63-passed, staged, NOT installed.** Owner chose **Path B** (fold rev3's UX + the agent read into one file, one install). Built rev4 from the md5-verified rev3 base (`54c239a3…`): eleven guarded string replacements (each `assert count==1`) redefining the agent expression to **`COALESCE(NULLIF(call_agent,''), NULLIF(verdict.agent,''), NULLIF(outbound,''), '')`** and wiring it through the log display (`_LOG_COLS`/`_log_row` new `agent_res`), the agent **filter** and **facet** (`_AGENT_EXPR`, `_log_where`, `_facets`), the filter **dropdown** (`_agent_names` now also reads `call_agent`), and the **Staff tab** (all four verdict-based aggregations re-attributed from `v.agent` to the resolved expression). rev4 md5 = **`a7043849d9f77d4bc8c0f68ef3f0b1c3`**. **F-63 gate run in the sandbox** (real Flask test-client against a synthetic `console.db` engineered so call1's *verdict* says "Alisha Khan" but its *call_agent* says "Shivani Srivastava"): **22 assertions across 9 routes ALL PASS** — the decisive ones being that filtering the log by "Alisha Khan" **excludes** call1 (its true handler is Shivani, proving `call_agent` overrides the verdict), the CSV row for call1 carries Shivani not Alisha, and the verdict/outbound fallbacks still resolve. Delivered; owner uploaded it to `/root/portal/portal.py.new` (Step A) but **paused the install** to run a full console review. `call_agent` has the same build guarantee as `conversations` (both only exist after `--with-myop-reconcile`, which the page already assumes and the cron mandates), so referencing it directly is consistent — no new fragility.

**4. Owner console review → the rev5 punch-list.** Rather than install, the owner reviewed the live console and listed the gaps: recording opens in a Google-Drive tab (was to open locally); transcripts open on a next tab / grouped / collapsed (want inline); "AI verdict pending for plenty despite running constantly" + the AI's reason should be viewable alongside; transcription-time and verdict-time shown to assess lag; a **send-back-to-staff** free-text "call again" feature under a heading; **appointment-booked no-shows** identified and queued for next-day calling; patient name/clinic-ID/diagnosis/last-visit on **every row of every tab**; and a **"my review" column with curated dropdowns + free text, collected in one place for AI training/refinement**. These were mined against the code (rev4) + the D297 contract + build dossier: recording-local-proxy = **Track K/B2** (not built); inline transcript = present in rev4 but behind a collapse; "pending flood" = the **refresh cron is not armed** (`console.db` is a manual-build snapshot) **plus** the builder drops the **AI Reason/Evidence** columns; lag = the **`latency` table** exists but no view renders it; send-back = **Track C-write** (GAS port, not built); no-shows = **Track N** (not built); row-level context = present only in the expandable detail; review-write-back + training feed = **Track R `dispositions`** (not built). Produced **`Console_Rev5_Punchlist_v1_S169.md`** (Tier 1): a top-down, build-ready execution plan — each item carries its source, the exact file+function, the change, the gate, the install steps, and the acceptance test — so the next session runs it hands-off.

**5. Decisions + records.** **D301** (Stage-2a `--days 60` build; 100% coverage; PK-dedup documented) and **D302** (the rev5 punch-list is the canonical ordered console backlog, executed top-down for minimum owner involvement; supersedes the build-dossier §8 roadmap as the *execution* authority while the dossier stays the frozen build *reference*) minted. **No new finding** (F-75 stays free). **Live now:** builder `portal_console.py` **`00b2175f…`** INSTALLED; `console.db` carries live `call_agent` (1001); `portal.py` at **rev2 `7a862f74…`** (rev4 `a7043849…` staged at `/root/portal/portal.py.new`, F-63-passed, not installed); refresh cron still not armed. All other live files unchanged from S168.

**Decisions: D301, D302 (minted). Findings: none minted (F-75 stays free). Next free decision: D303. Next free finding: F-75. This was Session 169.**


## §S170 — 11 Aug 2026 (evening) — REV5 PUNCH-LIST EXECUTED: Items 1–8 + Track M ALL LIVE in one session; cron armed & proven; three build waves; F-75 caught at the gate; D303–D305

**Session shape.** Owner said START; the session executed `Console_Rev5_Punchlist_v1_S169.md` top-down as mandated (D302). Phase 0: all present rows verified byte-clean; the punch-list itself was ABSENT from project knowledge (F-23 stump pattern) — owner uploaded it and it hash-matched its pin `e8f707d7…` exactly; halt reconciled, work began. Mid-session the owner asked whether items could be clubbed → three waves adopted (D305). Every install followed §3 discipline (upload `.new` → md5 → VPS `py_compile` → bak → mv → md5 → restart), with builder selftests and F-63 test-client gates before each delivery.

**Item 1 — refresh cron ARMED & PROVEN (and it caught F-75).** TZ verified IST. The gate ran the exact scheduled command once by hand with a small `--days 3` — and the artefact diff showed `call_agent` collapse **1001 → 60** and net-missed-open regress **108 → 152**: every `--build` writes `console.db` atomically from scratch over just its window; the Stage-2a backfill and MyOperator net-missed correction have NO incremental mode (**F-75**). The db was restored with a timed full build (`--days 60` = **32 s**, `call_agent` 1031 tagged / 100 % coverage, net-missed 156→109) and the cron designed accordingly (**D303**): `*/10 9-21 * * * /usr/bin/flock -n /root/wa/console_cron.lock /root/wa/venv/bin/python3 /root/wa/portal_console.py --build --with-myop-reconcile --with-transcripts --days 60 >> /root/wa/logs/console_cron.log 2>&1`. Proven by artefact (F-41): the 18:00:01 scheduled fire completed in 33 s, `built_at 18:00:13`, `call_agent` held.

**Item 2 — portal rev4 installed.** Staged `a7043849…` promoted (backup `.bak-S170` = rev2 `7a862f74…`). Page acceptance from owner captures: Staff tab shows the TRUE handler split (Shivani 460 top / Alisha 367 / Shavez 108), agent filter lists real handlers, freshness banner tracked two consecutive cron fires.

**Wave 1 (Items 3+4) — builder rev5-i3 `da3e29d2…` + portal rev5 `a5626e11…`.** Builder: `ai_reason` + `evidence` carried from `Call_Verdicts` into `console.db` (spec + schema + INSERT + fixture; selftest 35→**37/37**). Portal: per-row AI reason + quoted evidence; transcribed/judged times + judge-lag ("+Xm after call"); precise pending states — **judge pending** (transcript exists) vs **awaiting transcript**; new **Pipeline** tab (judge-lag median/p90/max · why-unjudged counts · oldest-first backlog · the 139-vs-109 numbers labelled **calls vs threads** — both correct, different grains); patient context (diagnosis · clinic-ID · last-visit) as chips at ROW level on every tab; CSV + AI Reason/Evidence/Transcribed At/Judged At/Lag. Gate: **F-63 30/30** (incl. the Alisha-claims-vs-Shivani-handled precedence bait). Owner captures verified 241 reason rows, 299 lag lines, both pages fresh off the 19:00 fire. Install note: the upload landed directly as the live file and the stray `.new` (old bytes) was converted into the intended backup — hashes proved provenance throughout (D188).

**Wave 2 (Items 5+6+7) — builder w2 `e3e2cdb4…` + portal w2 `585e691c…`; NEW persistent store `console_reviews.db` (D304).** Design amendment: the punch-list's dispositions-in-console.db would be WIPED by every 10-min rebuild (consequence of F-75's atomic-from-scratch fact) → reviews + send-backs live in **`/root/wa/console_reviews.db`** — portal SOLE writer (dispositions upsert-on-join_key; send_backs one-open-per-call); the builder reads it read-only and is sole writer of a **`Dr_Manoj_Call_List`** tab in the Tracker sheet (full-replace per fire = idempotent; heading "Call list from Dr Manoj"). Vocabulary locked: **Coming / Came / Not coming / Call again / Wrong claim by staff / Spam-marketing / Other** + free-text note; ⚠ self-review flag on the doctor's own calls; **training export** `/portal/console/reviews.csv` = join_key + AI verdict/reason/evidence + transcript + doctor label. Item 7: builder reads the `Followups_Today` feed OPTIONALLY (never halts; honest absence in meta per D236) → `no_shows` table with close-the-loop columns (called since? · last attempt · by whom · reached?) → **No-shows** tab. Gates: builder selftest **40/40** (a real defect caught: `call_agent` absent in plain builds → tolerant lookup); **F-63 Wave-2 20/20** (write-twice→one-row idempotency; resolve flow; honest-absence branch) + Wave-1 30/30 regression. **Live proof at first fire: `feed_found=True rows=125 resolved={phone:4,name:3,due:6,status:8}`** — the no-show feed discovered itself on the live sheet. One skipped VPS-py_compile gate was closed retroactively before acceptance.

**Wave 3 (Item 8 + Track M) — builder w3 `4be52ab9…` + portal w3 `b513c67a…` (LIVE AT CLOSE).** Item 8: builder pulls the 60-day recording window Drive→**`/root/wa/rec_cache/`** (avg ~217 KB, 60 d ≈ 0.30 GB per Appendix A; 1 GB cap, oldest-pruned; **Drive never deleted**); portal route `GET /portal/rec/<join_key>` (strictly key-validated) streams local-first with Range support (seekable in-page `<audio>` player), 302-to-Drive fallback for uncached, 404 otherwise; small Drive link retained beside the player. Track M rides the vocabulary: a **"Spam / marketing"** disposition excludes that phone from New-leads AND the net-missed count/filter, and lists it in a **Block list** section (the number lock itself stays a MyOperator-panel action). Gates: builder selftest **42/42** (prune unit: oldest-first under cap); **F-63 Wave-3 10/10** + full Wave-1 30/30 + Wave-2 20/20 regression = **60 portal assertions**. Installed with full discipline (VPS compile on `.new` before promotion this time).

**Anthropic account identified (owner query).** The Claude API billing account = **drmanojkragarwal@gmail.com**, org "Manoj's Individual Org" (receipts from `invoice+statements@mail.anthropic.com`). Credits ran out 10 Aug 09:44 IST (API disabled) → recharged 11 Aug ~18:34 IST — which explains the verdict-error/judge-pending uptick the new Pipeline tab shows; tonight's 03:40 `call_verdict.py` run should clear it visibly. Recommended: enable auto-reload/billing alerts on that account. (Kin to the still-open unaccounted `ANTHROPIC_API_KEY` in `/root/wa/.env` — separate fault, still owed.)

**Backup chains at close (all on VPS).** `/root/wa/portal_console.py`: live `4be52ab9…`; `.bak-S169`=`81581a6c…`, `.bak-S170`=`00b2175f…`, `.bak-S170-w1`=`da3e29d2…`, `.bak-S170-w2`=`e3e2cdb4…`. `/root/portal/portal.py`: live `b513c67a…`; `.bak-S170`=`7a862f74…` (rev2), `.bak-S170-rev4`=`a7043849…`, `.bak-S170-w1`=`a5626e11…`, `.bak-S170-w2`=`585e691c…`.

### D303 (full text) — Console refresh cron: ALWAYS the full-window build, flock-mandatory
Every `portal_console.py --build` writes `console.db` atomically from scratch over exactly its `--days` window; `call_agent` (Stage-2a) and the MyOperator net-missed correction exist only within that window and have no incremental/upsert mode (F-75). Therefore the scheduled refresh is **always** `--build --with-myop-reconcile --with-transcripts --days 60` (measured 32 s), every 10 min 09–21 IST, wrapped in `/usr/bin/flock -n /root/wa/console_cron.lock` so a slow fire makes the next one SKIP rather than race the single writer. A "light" cron variant is prohibited until an incremental mode exists and is gate-proven. Supersedes the punch-list Item-1 wording ("small --days for the incremental daily window"). Extends D235/F-41.

### D304 (full text) — Doctor-persistent stores live OUTSIDE console.db; four-store ownership map
Because console.db is disposable-by-design (D303), anything the doctor writes must persist elsewhere. **`/root/wa/console_reviews.db`** (tables `dispositions`, `send_backs`) — sole writer: the portal (schema owner; upsert semantics; doctor-gated POST routes). **`/root/wa/rec_cache/`** — sole writer: the builder (60-day pull, 1 GB oldest-pruned cap; Drive never deleted). **`console.db`** — sole writer: the builder. **Sheet tab `Dr_Manoj_Call_List`** (Tracker sheet) — sole writer: the builder (full-replace from open send_backs each fire); the portal never touches Sheets, the builder reads the reviews db read-only. All four stores are PHI: `console_reviews.db` and `rec_cache/` join `console.db`/`transcript_cache.db` in `.gitignore` (F-31/F-49) — **this gitignore extension MUST land before any repo commit.** Amends the punch-list Items 5/6 storage design; extends D235/D236.

### D305 (full text) — Punch-list executed as three clubbed waves
Owner-approved amendment to D302's execution mode: Items 3+4 (Wave 1, display), 5+6+7 (Wave 2, doctor write-paths), 8+Track M (Wave 3, media+marks) were built and shipped as three gated waves — each wave one builder `.new` + one portal `.new`, each item separately asserted inside a cumulative F-63 suite (30 → 50 → 60 assertions with full regression re-runs), same per-file install discipline. Rationale: all changes concentrate in two files, so clubbing cut owner install cycles ~3× without weakening isolation (per-item assertions localise a failing item before install). Remaining tracks (G/L/V, gist metric 5, Track J) stay individually shippable.

**Decisions: D303, D304, D305 (minted). Findings: F-75 (minted). Next free decision: D306. Next free finding: F-76. This was Session 170.**

---

## §S171 — 12 Aug 2026 (FULL EOS — the console FINISHED: acceptance sweep signed off · nine live installs across three files · patient enrichment live · digest v2 in-portal · Console v3 FINAL design system live · Hindi staff coaching report · GAS vocabularies canonised; D306–D308; F-76 withdrawn · F-77/F-78/F-79/F-80 closed · F-81 OPEN)

**Phase 0:** all 28 manifest rows hash-matched, zero drift. One cosmetic lag noted (the manifest's own Tier-0 row still said "S169") — fixed at this EOS.

**Part 1 — W2+W3 acceptance sweep (Runbook task 0): SIGNED OFF.** ▶ in-page playback ✓ · review persisted across a full rebuild (D304 proven — the single most important check) ✓ · send-back badge + open list + Resolve ✓ · No-shows rendered its 125 ✓ · spam-mark left leads AND landed in the Block list (a section inside No-shows, not a tab — discoverability nit only) ✓ · training CSV FAILED → F-77. The sweep also surfaced the builder SA sheet-write 403 (F-76, later WITHDRAWN by D306) and the No-shows quality defects (date truncation = F-78 correctness bug; raw ISO timestamps; ambiguous header; missing patient context).

**Part 2 — seven sequential build/install cycles (segment 1), every one offline-built → py_compile → F-63/selftest → WinSCP `.new` → md5 → backup → mv → verify:**
- **No-shows polish + F-77/F-78 fixes + dead sheet-push removal** (portal + builder). F-78: the builder sliced the feed's `DD-Mon-YYYY` due date with `[:10]` — not cosmetic: the due-vs-today lexical gate and the calls-since-due SQL boundary were computed against the wrong format. Fixed: parse to ISO at build, format at display. F-77: the training CSV was Excel-hostile/empty — fixed with a UTF-8 BOM + route hardening.
- **Track G — digest→portal LIVE:** `/portal/digest` renders the daily pulse straight from `console.db`; `daily_digest.py` repointed off `Verdict_Review` (→ `0a4ee35b…` → **`8140f54310bc19c238e9cf11f34b21e7`** live).
- **P2 patient enrichment LIVE (builder):** optional taxonomy patient-master sheet (owner-shared to the SA as Viewer) enriches `patients` with Age/Sex + clean diagnosis — first install `393a92b1…` reported honestly `found=False` until the share landed; **F-80** then bit: gspread 6.x `Spreadsheet.client` returns an HTTPClient WITHOUT `open_by_key`, and the AttributeError was being silently caught → perpetual `found=False`. Fixed by opening the enrich sheet inside `_open_clients` via the existing `gc`; **`552135b53564491dfe5629b2311b2076` LIVE** — `P2 patient enrich: found=True rows=7610 updated=7548 inserted=62`.
- **Collapsed-row redesign begins** (w6 `11f1aea890d701a5ccc720e164ea9a24` installed — in-master flags, age/sex chips, honest markers on every surface).

**Part 3 — Console v3 (segment 2).** Builds w7 → w7b → w8 (universal grid on all tabs, day-grouping, hot leads, no-show banner, on-row review/send-back, custom shared player) + **digest v2** (span · named/unknown callers · answered→transcribed→judged funnel · nm 7-day split · flagged/worst/referee as full expandable rows via `ROW_SHARED`) — each F-63-gated, none installed individually (superseded). Owner screenshots → a stop-and-analyse: **G1–G9 gap analysis**. **G1 root cause (F-79):** a stale `details.callrow>summary{…flex…}` rule sat LATER in the stylesheet than the new grid rule — rows fell back to flex while headers rendered grid; string-assertion gates cannot catch a CSS cascade regression. **New loop (D307): an owner-approved HTML preview BEFORE any UI build** — preview v3.0→v3.3 iterated live (no-show morning protocol timeline · reports section · the coaching model · Hindi WhatsApp report). **GAS outcome vocabularies fetched VERBATIM from the repo** (Dashboard.html L1801/L1904/L1455/L1262/L1276/L1285 + Callconsole.gs L989 K_CODE_MAP) → new Tier-1 doc `GAS_Outcome_Vocabularies_v1_S171.md`; the doc summaries under-counted two lists (FU=11, IN_RES=6) — code wins (D172).

**Part 4 — Console v3 FINAL BUILT + INSTALLED.** One consolidated `portal.py`: the stale flex rules DELETED (G1 cured at the root), v3 design system (type tokens 15/13/12/11 · 1480px cap · one 7-column grid · SVG sprite · two-line cells · hover/open states), signals zone (l1 chips: flags/MISMATCH/NOT FILED/SENT BACK/tx; l2: AI verdict · staff outcome **in the staff's own Hindi button words** via `HI_OUTCOME`), on-row actions (review select · send-back w/ reason prompt · ☎ `tel:` — OBD wiring deferred), no-shows morning-protocol timeline + "reached on try N" + expanded Due-day efforts table (agent per try via `call_agent` join — a fixture-caught defect: `calls` has NO agent column), **staff tab rebuilt** (7-day matrix answered/total · filed% colour-coded · mismatch ⚠; date-tap opens the day; per-agent day sections of full rows), **`/portal/console/staffreport`** — the daily per-staff Hindi coaching sheet (आपने दर्ज किया ❌ → सही outcome ✅ → क्यों → मरीज़ के शब्द → 🎧 सुनें; correct = doctor review else AI verdict; per-staff Copy-WhatsApp Hindi block; CSV; Print→A4 PDF), and **`/portal/rl/<jk>/<sig>`** — HMAC-signed recording-only staff links (no transcript, no portal session; forged sig → 403, gate-proven). F-63 v3 FINAL gate: **11 routes × 200, 16/16 assertions** (incl. served-HTML absence of the stale flex rule — the F-79 hardening). **INSTALLED + owner-verified ("Console seems ok"): `portal.py` `d74aa3f9054430981e719dcc7830cad6` LIVE.**

**Install chains (backups on VPS):** `portal.py` `b513c67a…`(S170 w3) → `e6b80f0a…` → `81e9ec58…` → w6 `11f1aea8…` → **v3 FINAL `d74aa3f9054430981e719dcc7830cad6` LIVE** · `portal_console.py` `4be52ab9…`(S170 w3) → `393a92b1…` → **`552135b53564491dfe5629b2311b2076` LIVE** · `daily_digest.py` `0a4ee35b…` → **`8140f54310bc19c238e9cf11f34b21e7` LIVE**.

### D306 — The review store is VPS-canonical; the builder's Tracker-sheet push is REMOVED; Drive becomes backup-only (withdraws F-76)
`console_reviews.db` on the VPS is THE canonical store of doctor dispositions + send-backs — one writer (the portal, D235). The builder's `Dr_Manoj_Call_List` Tracker-sheet push is REMOVED as dead code; the service-account's Google scope is NOT widened to write (smaller blast radius, no PHI pushed outward). Drive's role is backup only: a nightly `console_reviews.db` → Drive upload (small task, still owed — backlog). Send-backs reach staff in-portal (badge + open list + Resolve) and via the coaching report; the sheet tab is retired.

### D307 — Console v3 design system + preview-first UI loop + served-HTML gating
(a) The v3 design system is the console's standard: type tokens 15/13/12/11px (nothing under 11), content capped 1480px, ONE universal 7-column grid row on every tab (`74·84·1.2fr·.9fr·90·1fr·230`), SVG sprite icons, two-line identity + two-line signals zones, chips, hover/open states, day-grouping with newest open. (b) **Preview-first:** any UI change of consequence ships an owner-approved standalone HTML preview BEFORE code is built (the v3.0→v3.3 loop that produced this design). (c) **Served-HTML gating (from F-79):** UI F-63 gates must assert on the SERVED page — including the ABSENCE of known-stale CSS rules — because string assertions on templates cannot catch cascade regressions.

### D308 — The staff coaching model: daily Hindi learning sheet + signed recording-only links; review rows double as bot-training data
The daily staff report is a LEARNING SHEET, not a scoreboard: per agent, each wrong filing renders आपने दर्ज किया ❌ → सही outcome ✅ (in the staff's own D214/D225 button words via the HI_OUTCOME map from `GAS_Outcome_Vocabularies_v1`) → क्यों (doctor note else AI reason) → मरीज़ के शब्द (transcript evidence) → 🎧 a recording-only link. "Correct" = the doctor's console review where present, else the AI verdict. Staff links are HMAC-signed `/portal/rl/<jk>/<sig>` — recording only, no transcript, no portal session, nothing else reachable; per-staff Hindi WhatsApp copy-blocks + CSV + print-to-A4. The same disposition rows are the accumulating training corpus for the future filing bot (extends D304).

**Findings.** **F-76 (S171, WITHDRAWN):** builder SA is read-only → `Dr_Manoj_Call_List` write 403; raised at the sweep, withdrawn by D306 (architecture change, not a scope fix). **F-77 (S171, CLOSED):** the training CSV `/portal/console/reviews.csv` downloaded empty/Excel-hostile; fixed (UTF-8 BOM + route hardening) and re-verified live. **F-78 (S171, CLOSED):** builder `build_no_shows` sliced `DD-Mon-YYYY` with `[:10]` — the due-vs-today gate and calls-since-due boundary computed on the WRONG format (unreliable columns, a correctness bug wearing a cosmetic face); fixed = parse to ISO at build, format at display. **F-79 (S171, CLOSED):** a stale flex rule LATER in the stylesheet silently overrode the new grid — headers and rows diverged; string-assertion gates cannot see the CSS cascade; cure = delete the rule + gate on served-HTML absence (D307c). **F-80 (S171, CLOSED):** gspread 6.x `Spreadsheet.client` returns an HTTPClient WITHOUT `open_by_key`; the AttributeError was swallowed → enrichment permanently `found=False`; fixed by opening via the base `gc` client; RULE: never let a version-sensitive attribute path fail silently — fail loud or probe it. **F-81 (S171, OPEN):** duplicate call rows observed in the live log (same phone/time/duration twice, e.g. 16:51:55 ×2) — suspected MyOperator reconcile double-insert; builder-side investigation owed; displayed honestly, not hidden (D236).

**Also this session:** new Tier-1 canonical `GAS_Outcome_Vocabularies_v1_S171.md` (verbatim K/FU/IN/L sets + K_CODE_MAP + the Hindi coaching map). Backlog minted: nightly reviews-db→Drive backup (D306 tail) · staff-master single-source project (owner-named, parked) · Week/Month PDF (needs a PDF lib — or the print-CSS path) · MyOperator OBD click-to-call wiring (tel: placeholder live) · outcome-options admin UI (`console_options`) · WhatsApp inline-reply panel (per-user permission) · PWA · webhooks-v2 call-pop · F-81 dedup investigation. Notion Tech & Systems catch-up still owed (since S169).

**Decisions: D306, D307, D308 (minted). Findings: F-76 (withdrawn), F-77/F-78/F-79/F-80 (closed), F-81 (OPEN). Next free decision: D309. Next free finding: F-82. This was Session 171.**




### §S172 (13 Aug 2026) — Surgical Case Pack in-portal + shared WhatsApp sender + follow-up batch, all LIVE; go-live blocked vendor-side (F-82)

**Phase 0 clean** (opener confirmed all rows hash-matched; F-81 parked at owner direction). The session built three portal subsystems and shipped them live, then hit a MyOperator account-side outage that blocks WhatsApp go-live.

**Surgical Case Pack → portal (D309).** The PC Case Pack became portal routes (`/portal/casepack*`) in a new logic module `casepack_portal.py 341404d7` — no new service, subdomain or web-server config. Patient search reads `console.db` `patients` READ-ONLY (`mode=ro`: phone10/name/age/gender/clinic_id/patient_uid); bundles, consents and the ledger write `/root/wa/casepack/` (PHI, sole-writer portal, gitignored). Guard `casepack_required` (`PORTAL_CASEPACK_USERS`=manoj; legacy trusted device allowed). Tiles: "Surgical Case Pack" (Clinic, doctor-only) + "Case Pack · PC fallback". Owner chose the teal-dark page theme; `casepack_page.html 161d3e89` (printable consent kept white). 12 existing PC cases migrated into the ledger. Installed on the console-v3 base `d74aa3f9` → `931adf6e`.

**Shared canonical WhatsApp sender (D310).** `portal_wa.py 34994b23` — one sender for the whole estate. System B MyOperator WABA: base `https://publicapi.myoperator.co`, `Authorization: Bearer <MYOP_AUTH_TOKEN>` + `X-MYOP-COMPANY-ID`, `POST /chat/messages`, phone-number-id `1090067637530949`. Template-family aware: `drmanoj_*` → numeric body keys `"1","2","3"` lang `en`; others → named keys (`var_1/var_2`) at the template's own language. Ten manually-sendable approved templates registered (four panel-automation templates excluded). DRY-RUN default ON (`PORTAL_WA_DRYRUN="1"`); one CSV log `/root/wa/wa_portal/wa_portal_sends.csv` (sole writer). Routes `/portal/wa*`; guard `wa_required` (`PORTAL_WA_USERS`=manoj). A.1 upgrade folded in: `date` fields → calendar picker rendering "DD Mon YYYY" defaulting to today; `datetime` → datetime-local defaulting to now; `number` with `auto_from` (days-overdue auto from a date); a `wa.me` fallback link; UI externalised to disk. `/portal/wa/send` shaped to also accept a shared-secret for Phase-B GAS calls. Installed `931adf6e` → `faf13f7c`.

**Follow-up batch (D311).** `portal_followups.py 98547bc4` reads the daily `Staff_Action_Today_YYYY-MM-DD.xlsx` ("Call Sheet") at `/root/wa/followups/` (override `PORTAL_FOLLOWUP_DIR`; latest by mtime) — a source-stable FILE, so it is independent of who writes it (PC push now, VPS tracker later, same path; the reader never writes). OD→template ladder: <0 tomorrow · 0–3 due · 4–10 missed · >10 dropout (var 3 = OD); values auto-built per row. The page tier-groups the follow-up section into the source-sheet tiers — Due today · Grace 1–3 · Actionable Missed 4–10 · Dropout 10+ — each a collapsible section with its own Select-all + per-row checkbox/OD-badge/template-override/result; procedure call-backs greyed (non-sendable). Reuses `portal_wa.send`. On the 13-Aug file: 120 sendable (Due 27 · Grace 29 · Missed 61 · Dropout 3), 4 procedure call-backs excluded. Installed `faf13f7c` → `2cc42372` (with the A.1 widget). All routes 302 incl. `/portal/wa/followups/data` (proves the real module, not the fallback stub).

**UI-served-from-disk + cache-bust (D312).** The four UI files (`wa_widget.js 36cb7aa3` · `wa_page.html 0f5ae827` · `followups_page.html 9c22db64` · `casepack_page.html 161d3e89`) are served from disk and edit-in-place with no restart. The follow-up tier-grouping and the widget date-defaults were UI-only drops. A reported "date default not taking" was proven to be browser cache (the file was correct) — cured permanently by loading the widget with a per-load cache-buster `/portal/wa/widget.js?t=Date.now()` written by `wa_page.html`. Install pattern standardised: kits ship files pre-named (`.new` = promote-in-place with md5 guard + auto-rollback; real names = overwrite-in-place, no restart).

**Go-live attempt → F-82 (vendor-side outage).** `PORTAL_WA_DRYRUN` flipped to `"0"`, token present, service active. A self-send to the doctor's own number returned `HTTP 500 {"message":null}`. Full diagnostic: the portal token is byte-identical to the tracker's `WA_TOKEN` (sha8 `d47a090a`); the tracker's OWN `wa_send.py` path 500s with the same token; READ calls (`/chat/templates`, `/chat/phonenumbers`) 500 too; a NO-AUTH call returns 401 (API up, account not resolving); inbound webhook healthy. Root cause = account-side / provisioning at MyOperator, not our code. DRYRUN returned to `"1"` (SAFE). Escalated to Khushi (account manager, full-detail email) + Lokesh. Go-live waits on vendor restore, then flip→"0" + self-send, no code change.

**Decisions D309–D312 (minted, full text below).** **Finding F-82 (OPEN, vendor).** New Tier-1 canonical `Portal_WhatsApp_Casepack_Dossier_v1_S172.md` (the sole reference for these three subsystems). Repo commit owed (gitignore the three new PHI paths first). No incident report (the outage is external; the diagnostic ladder is captured in F-82).

### D309 — Surgical Case Pack ported into the clinic portal (doctor-only), off-PC-primary
Case Pack becomes portal routes (`/portal/casepack`, `/search`, `/cases`, `/case/<id>`, `/save`) in `casepack_portal.py` — not a new service, subdomain or web-server config. Patient search reads `console.db` `patients` READ-ONLY (`mode=ro`); case bundles + consents + ledger WRITE to `/root/wa/casepack/`, a PHI store, portal-sole-writer, gitignored (F-31/F-49). Auth = `casepack_required` (SSO user in `PORTAL_CASEPACK_USERS`, default `manoj`; legacy trusted device allowed). The VPS is now primary; the PC Case Pack tool is an emergency fallback (D270's off-Drive intent, now realised in the portal). 12 existing PC cases migrated into the ledger.

### D310 — One canonical shared WhatsApp sender for the whole estate (`portal_wa.py`)
System B MyOperator WABA is implemented ONCE: base `https://publicapi.myoperator.co`, `Authorization: Bearer <MYOP_AUTH_TOKEN>` + `X-MYOP-COMPANY-ID 68384350414b9847`, `POST /chat/messages`, `phone_number_id 1090067637530949`. Template-family aware (`drmanoj_*` → numeric keys/`en`; others → named keys/own-lang). Ten manually-sendable approved templates registered (four panel-automation templates excluded). DRY-RUN default ON (`PORTAL_WA_DRYRUN="1"`); one CSV log (sole writer). Go-live discipline: flip DRYRUN→"0", restart, self-send to the doctor's OWN number FIRST, then any patient. The `/portal/wa/send` endpoint is shaped to also accept a shared-secret for server-to-server GAS calls (Phase B: agent free-text replies inside the 24h window). No second sender is ever written — portal and future GAS share this one.

### D311 — Follow-up batch reads a FILE at a fixed VPS path (source-stability)
The batch reads the daily `Staff_Action_Today_YYYY-MM-DD.xlsx` at `/root/wa/followups/` (override `PORTAL_FOLLOWUP_DIR`; latest by mtime), NOT a live API or sheet. When the follow-up tracker later moves to the VPS it writes the SAME path — the reader is independent of who writes it and never writes itself (extends D235's one-writer rule to a one-reader contract). Template auto-selected by overdue-days ladder (<0 tomorrow · 0–3 due · 4–10 missed · >10 dropout, var 3 = OD); values auto-built (name, formatted date, OD). Non-follow-up rows (procedure call-backs) are shown greyed and never sent. The page tier-groups by the source-sheet tiers with per-tier Select-all. Reuses `portal_wa.send` (same log, same DRY switch); `POST /portal/wa/followups/send` up to 500 items.

### D312 — Portal UI files are served from disk, editable-in-place, and the widget is cache-busted
`wa_widget.js`, `wa_page.html`, `followups_page.html` (`/root/wa/wa_portal/`) and `casepack_page.html` (`/root/wa/casepack/`) are served from disk — a UI-only change is a drag-and-drop with NO restart. The widget is loaded with a per-load cache-buster (`/portal/wa/widget.js?t=Date.now()`) so an edited widget is never served stale from the browser cache (the S172 date-default fix appeared to "not take" purely because of caching — the file was correct). The standing install pattern is folded here: kits ship files pre-named — `.new` = promote-in-place under an md5 guard with auto-rollback (`.bak-SNNN`); real names = overwrite-in-place, no restart — so an install is drag-files + paste-one-block, no renaming.

**Findings.** **F-82 (S172, OPEN — vendor-side):** the MyOperator WhatsApp Developer API returns `HTTP 500 {"message":null}` on EVERY authenticated call (reads + sends) for the clinic account, identical from the portal and the tracker's own `wa_send.py` with the same token; no-auth returns 401 (API up, account not resolving); inbound webhook healthy → account-side/provisioning at MyOperator, not our code. Diagnostic ladder captured (log tail → token fingerprint → tracker-path live-send → read call → no-auth control). Escalated to Khushi + Lokesh; go-live blocked; DRYRUN returned to "1". Lesson: run the no-auth 401 control EARLY (three wrong diagnoses were resolved only by it). Near-miss (not a fault): a first install targeted `/root/wa` instead of `/root/portal` — caught by the md5 gate. Full text: Fault Register v2.17 + this §S172.

**Decisions: D309, D310, D311, D312 (minted). Finding: F-82 (OPEN, vendor). Next free decision: D313. Next free finding: F-83. This was Session 172.**


**END OF KB HISTORY ARCHIVE v1.24. §S172 is the last section; §S171, §S170 and earlier sit above it. If §S172 or this marker is absent, this file is truncated and must not be used as canonical.**


## §S173 — 13 Aug 2026 (Asset Register sub-project build; EOS-light for clinic canon — NO clinic code touched; folded at S177 from `S173_CLOSEOUT_RECORD.md`)

**Phase 0 done:** clinic canon (S172 manifest) md5-verified; all present rows PASS. Two absences by design (Fault Register F-82 append-owed; superseded Staff Daily Register). No clinic system altered. Manoj pivoted off WABA go-live (still **BLOCKED vendor-side** — MyOperator HTTP 500, F-82) to the **Asset Register** (`assets.dr-manoj.in`, separate `assetapp/` folder in the monorepo).

**Shipped + installed + verified live, four increments (baseline v1.2.0 `636f7b05…` → v1.4.2):**
- **v1.3.0** shared config-driven scanner (`scanner_widget.js`, disk-served) — multipage PDF, JPEG→PDF, editable filename, per-page delete/retake, ID-card mode, batch mode.
- **v1.4.0** taxonomy backbone (entities × zones) + fail-loud dry-run migration; **49 assets classified** (Clinic 37 / NK Path 11 / Personal 1).
- **v1.4.1** admin: password set-&-reveal/generate; API-token mask + rotate button.
- **v1.4.2** grouped Entity→Zone→assets collapsible index.

74/74 tests. Four VPS `.bak` rollbacks. Final code md5 `asset_register.py 3e18ed30…` · `scanner_widget.js 9b1444ac…` · `smoke_test.py b9d2bc7c…`. Git kit md5 `f6f852db…`. Full redesign **signed off** (Kind→Entity→Zone→Category/Heading cascade; Asset-vs-Consumable split; contract/period engine; record-only payment+EMI; maker-checker; Sarvam OCR pipeline); details + build queue in `assetapp/NEXT_BUILD.md`.

**Asset-app decisions minted (A-series, sub-project scope — full text in the git kit / NEXT_BUILD):** **A-D1** Entity replaces location as the top axis; visibility rides on Entity (Personal = owner-only) · **A-D2** Consumables are a separate table (headings), not assets · **A-D3** Dates entered as Month+Year; renewals **computed** from contract type → period · **A-D4** Payment is **record-only** (Cash/Bank/Card + optional EMI; computed end for reference; no reminders) · **A-D5** Maker-checker: owner (manoj+bhawna)=full+checker; manager=maker scoped to entities (never Personal); audit log · **A-D6** OCR: search + read-only peek on non-sensitive docs; sensitive stay search-only · **A-D7** `asset_register.py` is the entrypoint (`asset_register:app`); `app.py` dead → git-remove.

**Provenance:** built from the md5-verified live baseline, not memory (D160/D188). No clinic Tier-0/Tier-2 file edited; clinic manifest hashes remained those pinned at S172. No PHI/secret in any output (F-31). **No clinic decision or finding minted. This was Session 173.**


## §S174 — 13 Aug 2026 (Asset Register sub-project build, full sub-project EOS — NO clinic code touched; folded at S177 from `SESSION_174_CLOSEOUT_RECORD.md`)

**Phase 0 done** (S172 manifest verified, all present rows PASS; the two by-design absences stand). WABA still vendor-blocked (F-82); the session continued the Asset Register.

**Shipped, installed live, and Fold-tested — five increments (v1.4.2 → v1.7.0):**
- **v1.5.0 (Wave A)** — cascading Kind→Entity→Zone→Category entry form; month/year date dropdowns; contract/period engine (computed warranty/renewal); managed vendor/provider/bank/card pick-lists; record-only payment + EMI block; make-N-copies. Smoke 102/0.
- **v1.5.1 (Wave A.1)** — contextual contract (None / Warranty only / AMC-CMC + PM count); contextual payment; EMI auto-compute; AMC/CMC preventive-maintenance tracking (`assets.pm_count` + `service_logs.is_pm`); vendor/provider select-or-type-new. Smoke 114/0.
- **v1.5.2 (Wave A.2)** — contextual service log by visit type (PM free / AMC-covered; Repair & Other costed); replaced part carries its OWN warranty → computed reminder "Part warranty: {part}". New cols `service_logs.svc_type, part_replaced, part_warranty`. Smoke 130/0.
- **v1.6.0 (Wave B)** — due-soon badges on the grouped index + NEW per-entity `/renewals` view (due-soon default, `?all=1`, visibility-gated). Smoke 139/0.
- **v1.7.0 (Wave A.3)** — soothing stylesheet-only redesign (class names preserved); payment expansion (Cash / Bank / Cheque no.+date / UPI ref / Credit Card / EMI / Unpaid; new `assets.pay_ref, pay_date`); Parts-replaced card; service report scans linked back (`service_logs.report_att_id`); contextual "work done" label. Smoke **161/0**; `node --check` on both rendered inline scripts OK.

Gates every wave: system-`python3` py_compile (F-53) → smoke kept green 74→161 → `node --check` on emitted JS → `.bak-S174*` → md5-verify → mv → restart → serve-check → Fold test. All additive; 49 assets intact through every migration. **Final v1.7.0 md5:** `asset_register.py 9493dfbe74fff1eaf805295a75069c3a` · `smoke_test.py f9b347dfa42ca6eb398710cfe48dbd76` · `scanner_widget.js 9b1444ac…` unchanged.

**Asset-app decisions A-D8–A-D15 minted:** A-D8 contextual contract drives computed warranty/renewal · A-D9 PM under AMC/CMC is free (svc_type drives the cost gate + PM counter) · A-D10 replaced part = own warranty + reminder + Parts-replaced card · A-D11 due-soon badges + per-entity Renewals view, visibility-gated · A-D12 payment expanded but still record-only (incl. Unpaid; `pay_ref`/`pay_date`) · A-D13 redesign is stylesheet-only (why 139→161 stayed green) · A-D14 service report scan links back via `report_att_id` · A-D15 contextual "work done" label by visit type.

**Wave A.4 punch-list raised at the Fold test** (executed S175): 1 thumbnails · 2 service-entry confirmation · 3 softer palette · 4 back-navigation · 5 faceted narrowing search. **Provenance:** md5-verified baseline, assert-once anchors, no clinic file edited, no PHI/secret out (F-31). **No clinic decision or finding minted. This was Session 174.**


## §S175 — 14 Aug 2026 (Asset Register sub-project build, full sub-project EOS — NO clinic code touched; folded at S177 from `SESSION_175_CLOSEOUT_RECORD.md`)

**Phase 0 done — all 29 pinned manifest rows PASS, zero drift** (the two by-design absences stand; canon correctly parked at S172 pending this fold). WABA still vendor-blocked (F-82).

**Shipped + offline-gated (v1.7.0 → v1.8.0), one combined install:** **A.4a** back-nav ("← Assets"/"← Staff") + `flash("Service entry saved.")` + `confirm()` on costed entries only · **palette** 3-swatch low-glare background picker in Admin (Cool blue-grey / Warm sand / Soft sage; `settings.palette` via safe `setting_or()`) · **A.4b** price-gated image thumbnails (Files card, service-log report links, Parts-replaced card; sensitive images never thumbnail without price rights) · **A.4c** cascading faceted search on `/assets` (Entity → Zone → Category/Kind/Status, options from the visible set only, submit-on-change, Fold-safe) · **Phase D** the owner-only **purchase ledger** — tables `bills` + `bill_items`, `/bills` list/new/detail/delete/file + `/purchases` analytics (rate history/drift, period consumption, Expiring-soon reusing `due_state`) · **Phase E** the shared **`sarvam_ocr.py`** + scan→extract→pre-filled-bill flow · **scanner enhancement** — `enhanceGray()` integral-image local-mean shadow-flatten in `scanner_widget.js`, proven by a numeric Node harness (90-vs-230 gradient → uniform ~182). Smoke **161 → 203/0**.

**Post-closeout live Sarvam fix (same wave):** VPS diagnostic proved DIGITISE fine but EXTRACT `400 SCHEMA_INVALID` (fields need non-empty descriptions) → `DEFAULT_BILL_SCHEMA` fixed; extract completed on the real Sanwaria bill (S0700154352, ₹58,299, 0.99+ conf); `_map_bill()` hardened with `_cln` whitespace-collapse. **Post-closeout v1.8.1 (A-D19):** assets index regrouped by **LOCATION** (the entity→zone overlay was mostly NULL on the live 49 → one "Unclassified" blob); labelled collapsible sections + counts + due badges; columns extended to Name · Category · Serial · Supplier · Purchased · Status · Contract. Smoke 203/0. **Final v1.8.1 md5:** `asset_register.py c740bfbf0a9ac57d65bb4e95e4ba084e` · `smoke_test.py 64c9be270dfd5c035c9b45cd2437aa32` · `sarvam_ocr.py b1cc567b70b5e67c8c021fa22590babf` (NEW, shared) · `scanner_widget.js 4fe8c89386a54ce90786823b53df55bc` (was `9b1444ac…`).

**Asset-app decisions A-D16–A-D19 minted:** **A-D16** Sarvam extraction is a shared VPS service — one `sarvam_ocr.py` at `/root/shared/` (`SHARED_LIB_DIR` shim), SDK-based (`sarvamai` doc_ai), no hardcoded endpoints, graceful-skip · **A-D17 (v2)** bill capture is a structured ledger (`bills`+`bill_items`; asset+consumable superset schema; owner-only/403) enabling consumption + rate-drift queries · **A-D18** scanner enhancement = local shadow-flatten, not global stretch (preserves stamps/blue handwriting) · **A-D19** assets index grouped by location with extended columns.

Deliverables: git kit `assetapp_gitkit_v1.8.1.zip` (secrets-scan clean) · `KB_Asset_Register_v1.8.1.md` (Notion swap staged, write pended on approval). **Provenance:** built from the md5-verified v1.7.0 baseline + uploaded widget; SDK surface introspected live, not guessed; the sole in-session miss (an A.4c smoke using an invalid CATEGORIES value) was a test-data bug fixed before delivery — not a fault. No clinic file edited, no PHI/secret out (the two sample vendor bills were used only to fix the extract schema). **No clinic decision or finding minted. This was Session 175.**


## §S176 — 14 Aug 2026 (Asset Register + portal wave, full sub-project EOS — one clinic-side file `portal.py` gained a tile; folded at S177 from `START_HERE_SESSION_177.md` + the S176 Notion page + `KB_Asset_Register_v1_10_3.md`)

**Asset Register shipped v1.8.1 → v1.10.3, offline-gated to 315/0, all installs uploaded & confirmed on the VPS.** Three decision waves + one portal tile:
- **A-D20 (v1.9.0)** — date-normalisation keystone (`_norm_date()` → ISO on save + idempotent `normalise_dates()` self-heal) · bill→asset **bridge** (two-way `asset.bill_id ↔ bill_item.asset_id`, seeds item-expiry renewal) · consumable expiry in owner `/renewals` · from-bill backlink. Smoke 236/0.
- **A-D21 (v1.10.0)** — **reception scan-first intake** (SSO `staff` → fail-closed `reception`; monotonic stamp slips `B-0001…`; instant draft+scan; background Sarvam fill, non-clobber) · **maker-checker bills** (Consumable → manager, Asset-kind → doctor ONLY, server-side lane guard; reject = void) · **vendor directory** (`vendors` + multi-person `vendor_contacts`; inline service contacts on the asset page). Only approved bills feed analytics/renewals/bridge. Smoke 293/0; 18 vendors auto-seeded.
- **A-D22 (v1.10.1→v1.10.2)** — intake camera fix (mixed image+PDF input suppressed the phone camera; split into a camera control + photo/PDF fallback, labelled buttons + filename confirmation). Smoke 301/0.
- **A-D23 (v1.10.3)** — **OCR no longer silent**: `ocr_status` (reading/read/empty/failed) on the draft + Purchases list · **Re-read with Sarvam** button (non-clobber; drafts + approved) · blank-bill approval needs an explicit confirm (server-enforced). Smoke 315/0.
- **Portal:** `portal.py` gained a **"Scan Purchase"** tile (staff + manager) → `assets.dr-manoj.in/intake`; new live `portal.py da4177091ba9f188be6a0ff3eaf25bd8` (from `2cc42372…`).

**Sarvam verified working live** on B-0001's real scan (vendor Shri Ram Enterprise, bill SRE/737/2025-26, ₹1,30,003, 5 items). **F-83 minted (clinic finding, asset-app located):** the intake background OCR thread is fire-and-forget — it dies on service restart and skips non-draft bills, which is why B-0001 arrived blank; mitigated by A-D23 (visible `ocr_status` + manual Re-read); durable fix (queue/worker or synchronous-with-timeout) queued for a later wave. **Live md5 (v1.10.3):** `asset_register.py b30983710238863b6d98b8e773c6923c` · `smoke_test.py 65d6cd0e06d1e4fb9947175df5054152` · `portal.py da4177091ba9f188be6a0ff3eaf25bd8` · `scanner_widget.js 4fe8c893…` · `sarvam_ocr.py b1cc567b…`. Git kit `gitkit_S176.zip` (folder-wise `assetapp/` + `portal/` + COMMIT_MSG + KIT_MANIFEST) — **owner committed it before S177 close (repo at v1.10.3)**. Consolidated doc: `KB_Asset_Register_v1_10_3.md` (`07d01e80a1d6a49884650d2e542205df`), superseding v1.8.1.

**Finding F-83 minted (next free F-84). No clinic decision minted (D313 free). This was Session 176.**


## §S177 — 14 Aug 2026 (FULL EOS — Asset Register A-D24 wave BUILT + INSTALLED LIVE v1.11.0, smoke 342/0; housekeeping item 4 closed; the owed S173–S176 clinic-canon fold executed at this EOS)

**Phase 0:** manifest (S172) verified; the owed S173–S176 folds acknowledged as this session's close-out duty per `START_HERE_SESSION_177`. WABA go-live still **BLOCKED vendor-side** (F-82 — MyOperator HTTP 500; no change). Backlog items taken: **5** (A-D24 build), **4** (housekeeping); items 1/3 parked by owner, 2 already done (S176 kit committed, repo at v1.10.3).

**A-D24 wave (v1.10.3 `b3098371…` → v1.11.0) — BUILT offline, gated, INSTALLED LIVE; VPS smoke 342/0.** Three sub-parts (the fourth, scanner-app adoption of shared sarvam, was already satisfied by the A-D16 shared import):
- **(a) Scanner-in-intake.** `/intake` now leads with the full **shadow-flatten scanner widget** (A-D18 `enhanceGray`), doc-mode locked (`allowIdCard`/`allowBatch` false), posting to a new `/intake/scan_submit` (session-stashes the bill id, returns bare 200) with `backUrl /intake/slip/last`; the plain `bill_cam`/`bill_file` upload kept inside a `<details>` fallback; shared `_create_intake_bill()` helper (DRY — one bill-creation path for both routes). The fail-closed reception guard initially 403'd the new routes (correct behaviour); `RECEPTION_OK` deliberately gained `intake_scan_submit`, `intake_slip_last`, `scanner_widget_js`.
- **(b) `/purchases` spend analytics.** Total + this-month cards, spend-by-month bars, top-vendors bars, Indian-format rupees via a new `_inr()` Jinja filter + `_ym_human()`; owner-only dashboard spend tile.
- **(d) Supplier/purchase-date backfill.** `_backfill_asset_from_bill()` + `backfill_asset_supplier()` startup sweep fills blank asset `vendor`/`purchase_date` from the linked **approved** bill — non-clobber, idempotent; hooked into `init_db`, `bill_approve`, and the asset-edit bridge.

Gates: offline py_compile + smoke (STEP 23 added — 27 checks 23a–f; 315 → 342) → single &&-chained install block (md5 gate → `.bak` → `mv` → **VPS smoke as the gate** → restart-or-auto-rollback). The VPS run used the REAL sarvam module — the authoritative green. **Live md5 (v1.11.0):** `asset_register.py 0cd8fc3bfe8d39322c6162a41124bddf` · `smoke_test.py 6e72373325f808b1d7eaeb99f51a7b14` · `scanner_widget.js 4fe8c893…` UNCHANGED · `sarvam_ocr.py b1cc567b…` UNCHANGED at `/root/shared/`. `.bak` files retained in `/root/assetapp/`.

**Housekeeping (item 4) — ALL DONE:**
- **4a** `prune_backups.py` (`9dce8ea6dd61c5583f131f40fd4fec95`) installed at `/root/`, self-test 15/0 on the VPS — dry-run default, `--apply`, keep-newest-2, 14-day age gate, live-file guard, `.backup`≠`.bak`, logs to `prune_backups.log`; first dry-run correctly pruned nothing (all 18 backups <14 d). Manual tool, no cron.
- **4b** `sarvam_ocr.py` verified already single-copy at `/root/shared/` (md5 matches the pin; imports resolve there) — the KB's "not yet relocated" ASSUMED flag is CLOSED, nothing to move.
- **4c** stray owner test assets **#51–55** (all named 'test', created 13-Aug) deleted via `delete_test_assets.py` (`24cc30d832d3497e9948bef204361692`; hard-coded IDs + name-verify refuse-all guard, WAL-checkpointed DB backup, all-or-nothing transaction, offline-gated 11/0). Result **CLEAN DELETE ✓**: assets 54 → 49, target rows 0, zero orphan expiries/service_logs/attachments; undo backup `assets.db.predelete.2026-08-14_223751` on the VPS. Read-only `inspect_assets.py` also delivered. Rows **#45–50** (duplicate manager-entered "Gaurav scientific"×3 / "Aastha medical"×4) flagged as possible practice-junk but **NOT touched** — owner's call, queued for review.

**Delivery-format rules minted this session (standing):** files for VPS install are delivered pre-named **`.new`**; the install is **ONE copy-paste &&-chained bash block** (`md5sum -c` → `.bak` → `mv` → smoke gate → restart only on green → auto-rollback from `.bak` on red) — never numbered steps. **Terminal lesson:** long heredoc pastes corrupt at the owner's terminal → DB/utility work ships as uploadable script files, never pasted heredocs.

**Clinic-canon fold executed at this EOS (the S173–S176 debt):** §S173–§S176 appended above from their md5-verified close-out records (`S173_CLOSEOUT_RECORD`, `SESSION_174_CLOSEOUT_RECORD`, `SESSION_175_CLOSEOUT_RECORD`, `START_HERE_SESSION_177` + the S176 asset KB); Register → v4.6; Estate Inventory Asset-Register row → v1.11.0 + a `/root/shared/` shared-libs row (→ v1.1); `KB_Asset_Register_v1_10_3.md` (`07d01e80…`) registered Tier-1 (retires v1.8.1); the Fault-Register append consolidated to carry **F-82 + F-83** (→ v2.17 on owner apply); manifest advanced **S172 → S177** with per-session delta blocks.

**Asset-app decision A-D24 minted (next free A-D25). No clinic decision minted (D313 free). No clinic finding minted (F-84 free — the reception-guard 403 was the fail-closed design working; the heredoc corruption is an environment lesson, not a system fault). No incident. This was Session 177.**


**END OF KB HISTORY ARCHIVE v1.25. §S177 is the last section; §S176, §S175, §S174, §S173, §S172 and earlier sit above it. If §S177 or this marker is absent, this file is truncated and must not be used as canonical.**


## §S178 — 14 Aug 2026 (Session 178, EOS-light — documentation organization; NO live code · NO change to this Archive's prior content beyond this appended section)

Owner directive: *"organize the KB docs thoroughly · cut bloat · compact without any loss of context."* Phase 0 green — all present rows md5-matched; three re-uploaded canon files (`Fault_Action_Register` v2.16, `KB_Asset_Register` v1.10.3, `Staff_Daily_Register_Dossier` v1.1) reconciled EXACT to their pins before work.

**Evaluation (both long spine docs).** The **KB Register (v4.6)** had drifted back toward a mini-monolith — session history duplicated in THREE overlapping forms: per-session "S… additions" blocks, a full prose "## CHANGELOG", and a "§S… STATE" tail (two half-migrated organisational schemes coexisting). This **KB History Archive (v1.25)** was found healthy in substance, with only cosmetic drift that is the *cost* of the append-only + prefix-byte-identical rule: five embedded "END OF KB HISTORY ARCHIVE" markers (only the last is live), a stale H1 ("v1.16") and preamble pointer ("Register v2.5"), inconsistent session heading levels (§S152/§S169 as `#`, §S172 as `###`), and §S158 with no dedicated header — none of which can be fixed without either losing history or breaking the truncation-proof.

**Decision (Claude's, per the owner's "decide yourself"):** compact the **Register** (it is in-loop Tier-0 — where the bloat both lives and costs the most per session — and cutting the duplicated history is provably zero-loss because this Archive holds every one of those narratives verbatim); **leave this Archive untouched** save this one append.

- **KB Register compacted v4.6 → v5.0** (`ee12a63d4b87b1359f2d0954945457b2`; 752 → 500 lines, 207 KB → 75 KB). The three duplicated history forms were removed; the Register keeps current-state + indexes only — one consolidated live-file table, the decisions index **completed through D312**, the findings index, a compact version-lineage table, and (new) a truncation-proof END-marker the Register had always lacked. The compaction surfaced and CLOSED two pre-existing gaps: **D264–D269** (minted at S158/S159 but never actually bulleted in the index) and **F-82** (the current #1 open blocker, skipped in the old findings blurb). **Zero-loss proven MECHANICALLY**, not asserted: every decision D121→D312, every finding index entry, every kept section, and all 56 changelog versions are present in the new file; each "dropped" D/F number was verified to have zero index bullets in the old file — pure prose mentions inside the cut narrative, whose canonical homes (this Archive · the Fault Register) are untouched.
- **KB Asset Register refreshed v1.10.3 → v1.11.0** (`1c147beb44ad4413d3b147ad70e43ea7`) — built from the hash-verified v1.10.3 base + §S177 of this Archive (NOT memory): the A-D24 wave (scanner-widget-led `/intake` + `/intake/scan_submit`/`slip/last`; `/purchases` spend analytics via `_inr()`; approved-bill → asset supplier/purchase-date backfill), the housekeeping tools, the test-row cleanup (54 → 49), and next-free A-D25.
- **De-clutter:** `Salary_System_KB` (v1, S157), `Staff_Daily_Register_Dossier` (v1.1, S161), the closed `INCIDENT_2026-07-14_…_F44`, and the two pre-refresh doc versions (Register v4.6, Asset KB v1.10.3) moved to a NEW manifest **Tier 1 — HISTORICAL** subsection: retained, still hash-verified at Phase 0, out of the active reference set.
- **Manifest advanced S177 → S178** — re-pins Register v5.0 + Asset v1.11.0; records this Archive v1.25 → v1.26; Runbook v111 → v112; START_HERE 178 → 179.

**Deliverable md5s:** Register v5.0 `ee12a63d4b87b1359f2d0954945457b2` · Asset KB v1.11.0 `1c147beb44ad4413d3b147ad70e43ea7` · Archive v1.26 (this file, pinned in the manifest) · Runbook v112 + START_HERE_179 + final manifest (pinned in the manifest).

**No live code · no clinic decision (D313 free) · no clinic finding (F-84 free) · asset next A-D25 · no incident. This was Session 178.**


**END OF KB HISTORY ARCHIVE v1.26. §S178 is the last section; §S177, §S176, §S175, §S174, §S173, §S172 and earlier sit above it. If §S178 or this marker is absent, this file is truncated and must not be used as canonical.**


## §S179 — 15 Aug 2026 (Session 179, FULL — the Sanjeevni (medical) daily-revenue system migrated off Google Forms onto the VPS, live and bank-reconciled; D313 minted; F-84 (three self-found security faults) fixed)

Owner directive: migrate the daily-revenue system from Google Forms + the Google Sheet (`1AnJWD…rZH8`) to the VPS, **starting with medical (Sanjeevni Medicos)**, then clinic, then pathology — *"ALL THREE WILL MIGRATE TO VPS."* Manual workflow stays as fallback until each unit runs clean in parallel. Phase 0 was green (manifest verified at S178; all present rows md5-matched).

**What went live this session.** A new Flask app `clinic-finance` at `/root/finance/` (system `python3`, gunicorn on `127.0.0.1:8106`, OpenLiteSpeed `context /finance` on the portal's own origin so the SSO cookie carries — F-68), live at `followup.dr-manoj.in/finance/`, routing by role. `finance.db` (SQLite) holds **121 legacy medical days imported as recorded** (Apr 1 → Aug 13 2026), reproducing the sheet's own closing to the rupee (−₹30,056), which is what proves the import faithful. Nightly verified backups (01:05, 30 daily + 12 monthly). Portal tiles: **Daily Sale** (maker `darpan` → `/finance/entry`) and **Sanjeevni Medicos** (checker `manoj` → `/finance/review`); `Sanjeevni Medicos` masked from `bhawna`, and `Attendance`/`Staff Register`/`Scan Purchase` masked from `darpan` (role `staff` is shared, shaped per user).

**The build, block by block (all installed with the S177 `.new` + &&-chained md5-gate → `.bak` → `mv` → smoke-gate → restart-or-auto-rollback discipline; smoke proven to leave `finance.db` byte-identical):**
- **B1 — legacy import.** `finance_import_medical.py` imports 121 days as recorded; 36 carry-forward breaks became open, dated, sized `cash_adjustment` rows + `recon_exception` shouts (net unexplained **−₹84,533**, corrected down from an initial −₹184,285 once a 21-May resubmission was found double-counted); 7 physically-impossible negative-cash days imported honestly, not smoothed; 14 missing days at import. Output: `S179_B1_Medical_Reconciliation_Report`. Two findings that reshape the drift: 1-Aug opening typed ₹0 against 31-Jul close ₹38,176 (a keystroke, not a policy — Apr→May and May→Jun carried correctly); and 31-Jul's close rests on a +₹45,000 morning correction after an ₹85,000 deposit on 30-Jul drove the drawer negative — one look at the 30-Jul bank statement likely resolves the largest July break.
- **B2/B2.1/B2.2 — the module.** `finance_app.py`: maker entry + checker review, computed opening (no input anywhere — the 36 breaks are structurally impossible to repeat), non-cash bills (`day_noncash_bill` — home/procedure medicines count as revenue but not cash), cash movements to/from Bank/Dr Manoj/Dr Bhawna, expenses (fixed "Salary advance" → maker-checker → `PENDING_LEDGER_WIRING` for the future Staff-Ledger post; rest free text), month close/finalise, and parked-cash: a deposit is never split — one movement, one slip, one date matching the bank; only the OLD month's share is named (`clears_ym`/`clears_amount_p`), the remainder is the new month by definition; cash parked past 21 days shouts. `/api/cutover` ("Count the drawer") sets the opening for the owner's planned August re-entry — safe to run twice by design.
- **B3a — scanner.** Reused the refined VPS scanner widget as a dedicated per-document scan host page (`/finance/scan/<date>/<doc>`, serves widget + jsPDF from disk, public assets carry no clinic data); three docs per day (day sale report · manual copy · orthotics copy). Scan-completeness is read from the `attachment` table (server truth), never the browser.
- **B4 — day browse.** Every day stays openable as a collapsed expandable line regardless of status; scans are inline links (imported days link to the ORIGINAL Drive file — copies were never held, dashed border marks those); Portal back links on both pages, Back control on the scan page.
- **B5 — UPI reconciliation, LIVE.** `finance_upi.py` parses the ICICI Merchant (MPR) `.xlsx` (sheet CD_1, 22 cols), **self-checks each file against its own Grand Total** and rejects on mismatch (`StatementRejected`), stores settled UPI per unit per day, and flags any day whose entered UPI disagrees with the bank. Bank is the arbiter; approval requires `acknowledge_upi` over an open mismatch (Darpan's habitual issue is not selecting UPI in Marg — the bank corrects it). `VPS_Push_UPI.gs` in the clinic Gmail pushes the daily MPR to `/finance/api/upi-statement` (token `X-Finance-Cron`) at 09:30, dedupes via Script Properties, emails only on failure; verified end-to-end (`{"ok":true,"pushed":8}`). Merchant IDs confirmed for **all three** units: `…312505` Sanjeevni · `…306941` clinic · `…319164` NK Pathology.

**Design invariants (D313).** Money is INTEGER PAISE end to end (no float touches a rupee). Opening/closing cash is COMPUTED via SQL views, never a stored column. Revenue counts in full; cash does not. A deposit is never split. A missing day is never silenced — not for Sunday, not for absence; on the next working day Darpan files it and the shout stays pinned until filed. Attribution (clinic-id + patient name per line) reconciles to the day total and can never change it — the patient-revenue spine reads, it does not post (same for lab; clinic will read patient-wise from the follow-up tracker, procedure entry only enriching the procedure name). The line source is a pluggable adapter (`sarvam_ocr` | `marg_export` | `labmate_export` | `tracker` | `manual`) selected by a **column map (data, not code)**. Scans are evidence, relocated not deleted (month finalisation queues them to Drive; the attachment row + Drive id kept forever). The three units stay separate for accounts. HTML is plain English.

**Auth is fail-closed (see F-84).** `clinic_sso` signed cookie is authoritative; a `before_request` allow-list gate protects every surface incl. routes added later; per-unit entitlement via `unit_role` is the sole authority (a valid clinic login with no `medical` row = 403 — the manager cannot read the pharmacy's cash; a broker role grants nothing, not even `doctor`); the epoch is read live on every request and fail-closed if unreadable, honouring "Sign out everywhere"; header auth is off unless `FINANCE_ALLOW_HEADER_AUTH=1` (documented never-set). `healthz` exposes `sso_epoch_ok`; the installer auto-rolls-back if it is false.

**Marg feed (analysis only, adapter not yet built — S179/S180).** The Sanjeevni Marg sale-report `.xls` beats Sarvam OCR decisively: **13/13 exact day-total matches** against the sheet — the pharmacy's typing is perfect, so the historical drift is NOT a revenue-recording problem. Rule for the future adapter: **cash = the CASH column; UPI = net − CASH** (never the mode field — 12 split-payment bills carry cash inside a UPI-mode bill; and on three days every bill defaulted to CASH with zero UPI, which the daily UPI reconciler catches). The description field carries a stable trailing 3–5 digit number after `<phone> <name>` — 190 distinct phones, none ever paired with a different trailing number — behaving exactly like the clinic patient ID the spine needs (owner to confirm it IS the clinic ID). Needs its own adapter (date lives in group-header rows; real BIFF `.xls`; DAY TOTAL/GRAND TOTAL trailer rows skipped; day-total self-check before accepting a line). The Marg `.jmbkh` backup is an encrypted dead end and unnecessary — keep exporting the report. Full detail: `S179_Marg_Sale_Report_Analysis`, `S180_Marg_Folder_Recon`.

---

### D313 — Clinic Finance subsystem architecture (medical live; clinic + lab to replicate)

A single VPS finance subsystem migrates all three units' daily revenue off Google Forms, **medical first, clinic and lab as largely a replication** once medical is streamlined. The architecture, locked by the medical build and to be reused verbatim:

1. **One app, per-unit isolation.** `clinic-finance` (system python3, `/root/finance/`, `/finance` on the portal origin) serves all three units; `business_unit` + `unit_role` scope every row and every permission by unit. Accounts stay separate per unit by construction.
2. **Money is INTEGER PAISE; cash position is COMPUTED, never typed.** `day_entry`/`day_line`/`day_expense`/`cash_movement`/`day_noncash_bill` feed SQL views (`v_cash_ledger`, `v_month_summary`, `v_cash_custody`, `v_month_parked`) that derive opening/closing — eliminating the class of carry-forward break that produced 36 errors in the sheet.
3. **Revenue ≠ cash.** Non-cash bills raise revenue without touching the drawer; the drawer carries across the month; a bank deposit is a single un-split movement that names only the prior month's share.
4. **Ingest is data-driven.** `ingest_source`/`ingest_column_map`/`ingest_batch` + adapters (`sarvam_ocr`/`marg_export`/`labmate_export`/`tracker`/`manual`); switching a unit's source is a column map, not a code change. Marg (pharmacy) and Labmate (pathology) are the primary sources once one real export of each is mapped; Sarvam is the fallback for the manual and orthotics pages.
5. **The patient-revenue spine reads, never posts.** Every sale carries clinic-id + patient name; `patient_ref` (clinic_id UNIQUE, WALK-IN reserved) accumulates cumulative patient revenue; attribution reconciles to the day total and can never alter it.
6. **UPI is bank-arbitrated.** ICICI MPR `.xlsx` per merchant id, self-checked against its own Grand Total; entered-vs-bank mismatch shouts until acknowledged.
7. **Missing days shout and never go silent;** scans are evidence relocated to Drive, never deleted.
8. **Auth is fail-closed** (see F-84): signed SSO cookie, before_request allow-list, per-unit `unit_role` entitlement, live epoch check, header auth opt-in only.

Reversibility: Google Forms is retired per unit only after a clean parallel run; the manual workflow is the standing fallback. Extends the portal/SSO architecture (D261/D262) and the one-writer-per-store rule (D235). Full live-state: `S179_Finance_LIVE_State` (Tier-1, sole reference).

### F-84 — Three self-found security faults: the offline-testing shortcut was the vulnerability (FIXED)

Three faults, all mine, all found on my own post-install review, all the same shape — a development/testing convenience carried into production without asking what it lets a stranger do: **(1)** reads were ungated (identity checked only on writes) → fail-closed `before_request` allow-list; **(2)** identity came from spoofable `X-Clinic-*` headers in prod (`curl -H "X-Clinic-Role: checker"` = full control, not a leak) → real SSO cookie authoritative, header auth opt-in only, and *signed-in ≠ entitled* (no `unit_role` row = 403); **(3)** the epoch was never checked (`current_epoch=None`), so "Sign out everywhere" did not revoke `/finance` → epoch read live + fail-closed on every request, `healthz` surfaces `sso_epoch_ok`, installer rolls back if false. **The lesson worth keeping:** anything that grants identity for convenience must be opt-in and the production default must be closed. A fourth, smaller lesson — a test that asserted an environment accident ("epoch unreadable here") rolled back a good install; tests must assert behaviour, not what the machine happens to look like. Full text: `Fault_Register_append_F84_S179` → merges to Fault Register v2.17 alongside the owed F-82 + F-83 append.

---

**Live md5s at S179 close (Register-pinned; NOT manifest rows — F-31 keeps the DB + CSVs out of both repo and manifest):** `finance_app.py 61e36d5522e4e99e1e65e159ef50c85e` · `finance_ingest.py 872ec33ef7c628cd474224b0c6c78ba5` · `finance_import_medical.py 7cfde93e1c18a030a031a60ff66795f6` · `finance_upi.py 3f5016f0c64f12b91ab55c18252705c1` · `finance_schema.sql bef0d8100a1d7da30d049a9cd8eaf365` · `finance_ui/finance_entry.html 8ec6ad494fd6b97e5c7c70b6c42fdfc5` · `finance_ui/finance_review.html ddd3d5f61fb2f41950b1a63aa3480650` · `finance_backup.sh efe6f1b527bffafc21062bc352a063ee` · `clinic-finance.service 59c03bfafc2cd63bc440053724b61c34` · clinic-Gmail GAS `VPS_Push_UPI.gs 955b291c99edd0f16c79836e54a1043d`. Git kit `gitkit_S179.zip` prepared (folder-structured `finance/` + `gas/`, `.gitignore.additions`, commit message) — **owner action: `.gitignore` the PHI paths in the SAME commit before `git add` (F-31/F-49).**

**Owner loose ends carried:** the 30-Jul bank-statement deposit question (gates the August cutover anchor); one test scan through Daily Sale; off-box backup destination (holds patient names — owner's call); accountant-pack patient-name toggle (`export.include_patient_names`, default off); token rotation offered; the Marg-feed adapter decision (call Marg support for a scheduled export; optional Cowork recon on the MEDICAL PC). **Not yet built:** B4b Drive archive mover · B6 salary-advance → Staff-Ledger post · B7 month export `.xlsx`/`.pdf` per entity · missing-day WhatsApp nudge cron · Marg/Labmate column maps · pathology UPI route beyond the merchant id · **clinic + lab modules (next session — a replication of medical)**.

**D313 minted (next free D314) · F-84 minted (next free F-85) · no incident. This was Session 179.**


**END OF KB HISTORY ARCHIVE v1.27. §S179 is the last section; §S178, §S177, §S176, §S175, §S174, §S173, §S172 and earlier sit above it. If §S179 or this marker is absent, this file is truncated and must not be used as canonical.**


---

## §S180 — 15 Aug 2026 (Session 180, FULL — the Marg pharmacy feed established end-to-end offline; sale returns made to reach the books; four live-code installs; D314–D316 minted; F-85–F-89 raised, two about this session's own process; four lost canonical documents recovered by hash and three closed as LOST)

**Owner directive at open:** *"Marg feed — act on today's survey."* The session then ran long and
turned into four separate installs on the live `clinic-finance` box, a vendor requirement document,
two process findings about how this session itself worked, and a recovery operation over the owner's
disk that restored four of the seven unreachable canonical documents and established that the other
three are gone.

### Phase 0

**33 of 33 reachable canonical rows verified clean by md5** — every Tier-0 row, every Tier-1 spec and
dossier, all four Tier-2 frozen dossiers, and the historical rows. No drift anywhere. The manifest
matched its own pin `8afb20b2…`.

**Seven manifest rows could not be reached at all** — not in project knowledge under any path, not in
Google Drive: `Fault_Action_Register` v2.16 (Tier-1 CURRENT, with two appends owed), `KB_Asset_Register`
v1.11.0 (Tier-1 CURRENT), `Staff_Daily_Register_Dossier` v1.1, `KB_Asset_Register` v1.10.3,
`KB_Register` v4.6 and v5.0, `KB_History_Archive` v1.26. They were absent from `MD5SUMS.txt` too, so
they were never part of the S179 close-out bundle. Drive is stale as a KB mirror — nothing there is
newer than 6 Jul 2026, i.e. the pre-S147 lineage. Archive §S178 records that three of these went
missing once before and were restored from the owner's PC cold backup, not from Drive. **Owner
decision: flag and proceed** — the session's work touched none of them. It remains owed.

### The session-number correction (F-85)

The session opened with an uploaded document headed *"Session 181"*. Derived from the artefacts
rather than the labels (D188): the last close-out was S179, which named the next session 180 and
regenerated `START_HERE_SESSION_180`; `S180_Marg_Folder_Recon` was written at 09:15 on 15-Aug,
**before** that close-out at 10:50, so it is S179 work carrying a forward-guessed label; the 14:30
feed survey inherited the wrong label and called itself 181. No close-out had run since S179, so no
number past 180 had been consumed. **This was therefore Session 180**, and the uploaded survey was
folded in as `claude/S180_Marg_Feed_Feasibility.md` with a provenance block recording the
correction, the original upload's md5 (`c2086db25b39c02e8c29bc6cf4dc634c`), and the body kept
byte-for-byte verbatim.

### What the Marg report actually is — five real exports, and three different reports under one filename

The S181-labelled survey had documented a 9-column month-to-date report. The first file the owner
supplied was **not that report**: same menu, same filename, same folder, but a **3-column**
single-day statement (`BILL NO. | DESCRIPTION | BILL VALUE`) with **no CASH column at all**. A text
export from `C:\Users\Public\MARG\17476\` proved to be the same 3-column report in another format —
checked bill by bill, same 23 bills, same total, adding nothing.

Marg's `BILL WISE STATEMENT` screen (`Daily Reports → Sale Reports → Bill Wise Statement`) turned out
to have a `Report Type` dropdown with `Detail · Column-2 · Summary-1 · Summary-2`. **`Summary-1`
collapses the report to three columns and loses the payment split entirely; `Detail` produces the
nine columns.** It was never the `80 Col` width setting, which was an early wrong guess, corrected.

**The confirmed layout:**

```
BILL NO. | DESCRIPTION | D.R. | GROSS AMT. | DISCOUNT | TAX | DR/CR | NET AMT. | CASH
```

**Verified arithmetic across every complete day parsed:** each day's bill rows sum **exactly** to its
`DAY TOTAL :` row; the days sum to `GRAND TOTAL :`; and per bill,
`GROSS − DISCOUNT + TAX + DR/CR`, rounded, reproduces `NET AMT.` The same business day exported twice
by different runs gave identical figures (01-08-2026: 37 bills, ₹28,119.00 net, ₹16,411.00 cash).

**The money rule, now proven on visible data rather than taken on trust:** `cash = the CASH column`,
`non-cash = NET − CASH`. Non-cash was **36.9%** of net across five days, and `.UPI` bills show
`CASH` as `0.00` against a full `NET`.

**The `D.R.` mode field was mischaracterised and then corrected.** It is not garbage: in the `Detail`
report it agrees with the CASH column on 133 of 138 bills. But the five it misses are **split-tender**
bills — `.UPI` with part cash (net 3000 / cash 1000; net 300 / cash 158). A single-mode label cannot
represent a split; the CASH column can. The rule stands for a better reason than first given.

**The discount channel was also mischaracterised and corrected.** An early draft built the flag
design around `DR/CR` because that is where the first large single value appeared (₹19 on a ₹319
bill, and one bill of ₹85.39 written down by ₹85.00 — 99.5%). Measured across 138 sale bills:
**`DISCOUNT` 84 bills / ₹3,634 (~3% of gross)** versus **`DR/CR` 16 bills / ₹199 (0.16%)**.
`DISCOUNT` is the real channel by a factor of eighteen; `DR/CR` is secondary.

**Credit notes** are plain negatives (`−1150.00`). In the `.xls` the positive amounts arrive as
**numeric** cells while the negatives arrive as **text** cells with leading spaces — a reader
trusting the cell type drops every refund silently.

### The truncation defect

A month-to-date range **with item detail on** does not export completely and gives no error.
Evidence from 15-08-2026: requested `FROM 01-08-2026 TO 15-08-2026`; produced 1,207 rows across 44
pages; contained **only 01-08 to 06-08**; day 06-08 had no `DAY TOTAL :`; days 07–15 were absent;
and there was **no `GRAND TOTAL :` row anywhere**. The file opened normally in Excel and looked
complete.

**That missing `GRAND TOTAL` is the reliable completeness test**, and the design already relied on it
— so the check paid for itself on real data the first time it met a real file.

**Consequence:** item detail and month-to-date cannot be combined. Owner chose **two saved buttons** —
Button A (accounts): month-to-date, item detail off, self-healing because a later file always
contains everything an earlier one did; Button B (analysis): single day, item detail on. This also
bounds the failure of an unattended sweep: a missed day costs item detail, never the accounts.

### Transport — the owner's design, and a reversal

The survey recommended a background folder watcher. The owner pointed out that staff already
generate the report every day (it was printed and used to fill the Google Form) and that Darpan
already has the Daily Sale portal tile, so the soft copy can ride an action that already happens.
The watcher was argued against on the grounds that it fails silently — the shape of F-75 and the
01-Jul follow-ups incident.

The owner then chose full automation with no human at all: report lands in a folder, swept from
there; email if Marg can be made to send it; manual generation by a morning staffer as a fallback;
Darpan last. **The objection was withdrawn on the condition that the missing-day alarm (D313) has
been seen to fire**, since that alarm is precisely the mitigation for a silent sweep.

### Sale returns — the design, and what the data supported

Owner's workflow: returns are few and accepted gracefully; patients are asked for the purchase bill
but never refused for not having one; reception will open a portal page, enter patient and drugs,
and hand a printout to Darpan with the medicines; a dropdown reason; the discount given at sale is
deducted at return; Manoj gets pre-checked data with staff and timestamp.

**Measured on the nine credit notes in the six-day sample:** all nine carry at least a name (none is
anonymous); **five of nine** carry the full name + mobile + clinic ID the standing rule requires;
**seven of nine** correlate back to a prior sale inside the six-day window. The two that do not are
**not** missing identity — `CN00154` (−₹1,700, the largest) carries a clinic ID, a mobile and a name;
its original sale simply predates the file. **So the lookup must run against the database, not the
day's file.** Drug-level corroboration proved decisive where available: `CN00158` returned six items
and all six appeared on that patient's earlier sale.

Owner added: expired or near-expiry returns are flagged and disallowed; a 30-day window from sale is
a reasonable control. Both are decidable from the data — expiry is present on **682 of 705** item
lines, and the sale date comes from the correlation itself.

**A control point was raised and then improved by the owner.** The concern: Darpan is the operator on
most days, so discount flags on his own page would be self-audit — the D272 shape. The owner's
answer was better than the objection: visibility is deliberate and deterrent, he physically explains
exceptions and *the doctor and Bhawna tick them off*. The invariant recorded is therefore
**"Darpan sees and explains; only the doctor or Bhawna clears."** A second point stands alongside it:
flag few things per bill (on size *and* proportion) and trend the daily discount rate, or alert
fatigue makes the ticking mechanical within a week.

### What was built and installed

Four separate installs on the live box, each hash-gated, backed up, smoke-gated and auto-rolled-back.

**U1 — sale returns reach the books.** `finance_ingest.adapter_csv` skipped every row with
`amount <= 0`, a junk filter that also ate every refund silently. Split into the two things it
conflated: no readable amount or exactly zero stays junk; a genuine negative is a **return**.
Proved: before, 2 rows kept and the day attributed ₹2,150.00; after, 3 rows and ₹1,750.00 — the old
code overstated the day by exactly the ₹400 refund. **Not done by allowing negative amounts**, because
`sale_item.amount_p` is declared `CHECK (amount_p >= 0)` and SQLite cannot drop a CHECK with
`ALTER TABLE`; removing it meant create-copy-drop-rename on a live table holding 121 days of patient
data, to change a *reporting* behaviour. Returns store as a **positive magnitude with
`service='<base>_return'`**, and **one view** (`v_day_attribution`) nets them. `sale_item` was first
confirmed to be summed in exactly one place. **Install-order enforced by the test:** the smoke
contains a check that fails if the view migration was not applied, verified at 49/50 exit 1 against
an un-migrated store. Installed 20:38 IST, `INGEST 50/50`, `sso_epoch_ok: true`, 121 days intact.

**U2 — `marg_report.py`.** Reads the Marg `.xls`; refuses what it cannot trust (the 3-column variant
by name and remedy, a truncated export, any day failing its own arithmetic); emits bill rows and
drug rows. Identifies the variant from the title and header before parsing — two different reports
share one filename, and a file is not identified by its name (D188). **Self-caught during the
build (F-86):** the reader was emitting **full 10-digit phone numbers**, though `patient_ref` stores
`phone_last4` and nothing more and `ingest_column_map` has no phone field at all. Corrected to
last-four; the item CSV carries no patient identity at all; outputs grepped for any 10-digit string,
none found. **Clinic-ID scoring added:** 111 of 113 real IDs are exactly four digits, so a
non-four-digit ID is neither discarded (that loses a real patient) nor trusted — it scores below
`ingest.min_confidence` 0.70 and goes to review.

**U3 — `finance_returns.py` + `sale_line_item`.** Drug lines had no home in the schema; `sale_item`
is bill-level. Additive only: one table, four indexes, three `returns.*` settings, proved to add six
objects, remove none, and be a no-op on re-run. Correlates a credit note to its sale by patient,
corroborated by the medicines returned, and grades the result — `conclusive · probable ·
patient_only · none` — because a name match is a probability and only the top grade is fit to feed
an audit. It **never refuses a return**; refusing is a decision for a person at the counter.
End-to-end on the real six days: `CN00158` conclusive 6/6, three more conclusive 1/1, three
`patient_only`, `CN00154` `none + large_and_unmatched`. **U4** (expiry + 30-day window) folded in as
settings-driven flags. Installed 21:14 IST, `RETURNS 28/28`, `selftest 38/38` on the box.
**U13:** `xlrd 2.0.2` added.

**U1-fix + U11.** A regression introduced by U1 was found before it could bite: queued returns are
stored **signed** in `sale_item_review` (which has no non-negative constraint, keeping
`in_review_p` honest), but `/finance/api/review/<id>/resolve` passed that value straight into
`sale_item`, which forbids negatives. A checker resolving a queued return would have got a 500.
Proved before/after on the same request: **HTTP 500 / no row → HTTP 200 / `('pharmacy_return', 7700)`**.
Not reachable live yet, as nothing feeds returns into the queue until the reader is wired in.
**U11 `finance_identity.py`** proposes a patient for name-only lines from the system's own
accumulated roster; grades `corroborated · unique_exact · near · ambiguous · none`; **proposes and
never assigns**, writing nothing to `sale_item` and resolving nothing. Installed 22:13 IST,
`SMOKE 179/179`, `IDENTITY 44/44`.

**U11's measured ceiling, recorded because it redirects effort.** Roster of 94 patients from six
days, against 36 name-only lines: 1 corroborated, 2 unique, 2 near, 0 ambiguous, **31 none** — 3 of
36 safe to default. Of the 31 unmatched, **29 are distinct names**; only one repeats. They are
one-off walk-ins, not clinic patients whose ID was missed. **This reframes the 82% attribution
figure: it is not a defect to engineer away but roughly the share of pharmacy business that is
clinic patients at all.** The other ~17% (₹19,979 over six days) is counter trade. Cleverer name
matching will not move it; only a roster independent of the pharmacy typing the ID — the follow-up
tracker's consultation report, which lives on the clinic PC — would, and that is a transport problem.

### Two process failures, both mine (F-87, F-88)

**F-87 — a change was shipped to a test suite that could not be run, twice.** `finance_app.py`'s
smoke suite is written against the real store (>100 filed days, approved and locked days, open
exceptions, a legacy tail leaving cash negative), so it could not run offline. That was treated as
acceptable and the change shipped on reasoning alone. It failed on the box with two broken
assertions, both caused by the added test block, and the install gate rolled it back correctly.
**This is F-84's own lesson repeated after this project had already minted it.** The remedy is an
asset rather than a resolution: `dev_seed_smoke_db.py` builds a database satisfying the suite's
preconditions. Verified differentially before the third build shipped — unmodified 163/173 versus
modified 166/176 on identical seeded data, **zero failures added**. The specific traps, now written
into the code itself: `ingest_day` **supersedes** the day's previous batch and **deletes** what it
produced, so any test that ingests destroys earlier setup (this cost two separate debugging rounds);
and resolving a queued line **adds** a `sale_item`, which an earlier check counts. The block now
inserts its queue row directly and runs last, with a comment saying it must stay last.

**F-88 — a passing `md5sum -c` proves a kit is internally consistent, not that it is the intended
kit.** Two install attempts ran an older download whose checksums matched its own files perfectly.
Kin to D188. Fixed by having the installer carry the identity of the build it belongs to and refuse
to run otherwise; the guard was tested against the old module before shipping.

Also confirmed independently: the smoke suite genuinely does not touch `finance.db` — md5 identical
before and after, repeatedly. That claim holds.

### The vendor requirement document

`Marg_Report_Requirement_Sanjeevni.md` — standalone, forwardable, no internal decision or fault
numbers. Menu path, both button settings, the export delimiter settings, the exact nine headers, a
structurally real sample with placeholder identities, and six numbered requirements each with a
pass/fail test: one click · automatic daily generation · two separate output files · **a DATE column
on every bill row** · automatic email · month-by-month history. Plus the truncation defect with its
evidence, and the question that matters more than raising a limit: **if it cannot export fully, can
it fail visibly instead of writing a partial file silently?** A §7 lists what must not change — the
nine headers, the total rows, the footer count, negative credit notes — because vendors improve
report formats helpfully.

**The DATE-column requirement is the owner's observation and it removes a permanent fragility.** The
date currently appears **only as a group heading** above each day's block; bill rows carry none. Any
reader must infer each bill's date from the last heading seen, so a change to page breaks, sorting
or heading placement silently mis-dates bills.

Also noted for the vendor: Marg's mail subsystem has **never been set up** — both mail folders
empty, nothing ever queued or sent — so email is a fresh configuration, not a repair; and the
outgoing sender is still the demo ID `MARGDEMO`.

### The seven unreachable rows — recovered four, lost three (F-89, D316)

A PowerShell recovery tool was written and run over the owner's `D:` drive. It searched **by md5, not
by filename** (D188 — these documents could be sitting under any name), opened `.zip` archives
because the cold backup is one, and re-hashed an LF-normalised copy of any near-miss in case a
Windows editor had converted the line endings. **26,745 files hashed.**

**Four recovered, each matching its pinned md5 exactly:**

| Row | Found at |
|---|---|
| `Fault_Action_Register` v2.16 (Tier-1 CURRENT) | `D:\Downloads\1 ROUGH WORKING FOLDER\DrManoj_Clinic_FULL_Handoff_Session171_2026-08-12\` |
| `Staff_Daily_Register_Dossier` v1.1 | `D:\Downloads\1 ROUGH WORKING FOLDER\cold_kit_S165_2026-08-10\` |
| `KB_Asset_Register` v1.10.3 | `D:\dr-manoj-git\drmanoj-clinic-automation\canonical-docs\` |
| `KB_Register` v4.6 (S177) | `D:\dr-manoj-git\drmanoj-clinic-automation\canonical-docs\` |

**Three not found, on D: or C:, and declared LOST by the owner:** `KB_Asset_Register` v1.11.0
(Tier-1 CURRENT), `KB_Register` v5.0 (S178), `KB_History_Archive` v1.26 (S178).

**Why those three and not the others — the pattern is the finding.** The newest full cold kit on the
machine is **`DrManoj_Clinic_FULL_Handoff_Session171`**. The three missing documents are **S177 and
S178 outputs — created nine sessions after the last cold backup was taken.** Everything up to S171 is
comfortably recoverable from disk; everything after depended on whatever happened to be downloaded
loose. `END_OF_SESSION_PROMPT_v4 §E` calls for a cold kit every three to five sessions. It lapsed,
and this is the bill.

The scan also showed the archive is in far better shape than "seven missing" implied: an almost
unbroken lineage sits on disk — `KB_Register` v2.0→v5.1, `KB_History_Archive` v1.0→v1.27 (v1.25_S177
`56361254…` and v1.27_S179 `adb85c35…` both present and matching), `Fault_Action_Register`
v1→v2.14.

**F-89 minted** — the cold-backup cadence lapsed for nine sessions and three canonical documents were
lost as a direct result. **D316 minted** — an irrecoverable canonical row is CLOSED in the manifest
as LOST with its consequence stated, never left as a permanently unverifiable row, because a Phase 0
that halts on the same three rows every session teaches the next reader to ignore the halt.

**Applying D316 to these three:** `KB_Register` v5.0 and `KB_History_Archive` v1.26 are **historical
and superseded by versions verified present on disk** (v5.1 and v1.27), so nothing current depends on
them — closed as **LOST-SUPERSEDED**, no further action. `KB_Asset_Register` v1.11.0 is **Tier-1
CURRENT** and is the one that matters; but its predecessor v1.10.3 was recovered and Archive
§S173–§S177 carries the full narrative of what changed, so it is closed as **LOST-RECONSTRUCTABLE**
with a backlog item to rebuild it from those two verified sources. It is not gone, it is unbuilt.

**Owner also committed the git kits at this close**, clearing the carry that had left the repository
two sessions behind.

### D314 — a sale return is stored as a magnitude, with its direction in the row's type

Never as a negative amount. `sale_item.amount_p` carries `CHECK (amount_p >= 0)`, a deliberate
invariant (amounts are magnitudes; direction is the row's type). Honouring it meant no table rebuild
on a live store holding real patient data — only a view changed, and nothing was read, written or
deleted. The queue table (`sale_item_review`) has no such constraint and keeps the value **signed**,
so `in_review_p` stays honest; every path that moves a row from queue to spine must convert the sign
back into a magnitude plus a `_return` service. Applies unchanged when clinic and lab replicate.

### D316 — an irrecoverable canonical row is CLOSED as LOST, never left permanently unverifiable

Phase 0 verifies what the canonical set *claims* to contain. When a row genuinely cannot be
recovered, leaving it listed-but-unverifiable makes Phase 0 halt on the same rows every session —
and a halt that always fires is a halt that gets waved through, which destroys the value of the
check for every other row. So an irrecoverable row is **closed** in the manifest, with its pinned
md5 kept for provenance and its consequence stated in one of two forms:
**LOST-SUPERSEDED** (a later version is verified present, so nothing current depends on it — no
action) or **LOST-RECONSTRUCTABLE** (it is current, but a predecessor plus the Archive narrative can
rebuild it — a backlog item, not a permanent flag). A closed row is not drift and does not halt
Phase 0. Only a row that is *listed as present* and fails its hash does that. *§S180.*

### D315 — a patient-identity match is graded, and only the top grade may feed an audit

Revenue attribution tolerates a probable match: the cost of being wrong is a rupee in the wrong
history. A discount or return audit does not: the cost is naming the wrong patient, the wrong day
and the wrong person behind the counter. The same match therefore carries two thresholds — all
grades feed revenue, only the top grade feeds the audit. Applied in `finance_identity` (five grades,
only two offered as a default click, `ambiguous` deliberately offering nothing) and in
`finance_returns` (four verdicts, only `conclusive` audit-fit).

### Live md5s at S180 close

`finance_ingest.py 2cd0f264fb1a091f3e3ec7c3f4a17438` (was `872ec33e…`) ·
`finance_app.py 7b62b7ae661914505c864d71cc6c9abc` (was `61e36d55…`) ·
`marg_report.py 28b47d447cfd966411742055717a5c56` (NEW) ·
`finance_returns.py a46a87e65d951d59baeb9d86c9d8fe59` (NEW) ·
`finance_returns.sql 9cec4e317590f845beda87881721cf69` (NEW) ·
`finance_identity.py 81092e3ca18c9a85f1de06cc8055d967` (NEW).
Database: `v_day_attribution` redefined to net `*_return`; table `sale_line_item` + 4 indexes +
3 `returns.*` settings added. VPS python: `xlrd 2.0.2`. All other clinic live files UNCHANGED.
Backups on the box: `finance.db.bak_20260815_203810` · `…_211437` · `…_221320` ·
`finance_ingest.py.bak_20260815_203810` · `finance_app.py.bak_20260815_221320`.

**Cold-backup discipline restored at this close** — `KB_S180_close.zip` was produced with all six
canonical documents plus `MD5SUMS.txt`, and the git kits were committed. **The next full cold kit is
due within three to five sessions and is now a standing backlog item, not a discretionary one.**

**Owner loose ends carried:** the whole Marg vendor request (§2 of the requirement document) ·
one export from **each** button, checked before the buttons are saved · **one complete Button A
export 01-Aug→date passing its GRAND TOTAL check, which gates the August cutover** · whether `ABL`
(seen where the phone sits) is a credit/party account, i.e. a third payment category · the flag
thresholds in rupees and per cent · the counter rule that every return bill carries name + mobile +
clinic ID (5 of 9 today) · the return-reason vocabulary and which reasons route clinically rather
than into finance · **seeing the missing-day alarm actually fire before the sweep is trusted** ·
bill `A002783` (₹85.39 gross, ₹85.00 written off, 99.5%) · and, still, the S179 git kit — the repo is
now two sessions behind, and the PHI paths must be `.gitignore`d in the same commit before the first
`git add` (F-31/F-49).

**Also owed:** rebuild `KB_Asset_Register` v1.11.0 from the recovered v1.10.3 + Archive §S173–§S177
(D316, LOST-RECONSTRUCTABLE) · re-apply the three Fault Register appends now that v2.16 is back
(F-82+F-83, F-84, F-85–F-89) → v2.17.

**Still not built:** U5 reception return page · U6 return-authorisation reference code (depends on
whether Marg's credit note has a reference field) · U7 discount deduction at return (**re-sized to
medium after reading the schema: the discount is not stored anywhere — `sale_item` holds only NET,
and `adapter_csv` reads no discount column though `ingest_column_map` permits one**) · U8 Darpan's
checker page · U9 the flag engine · U12 transport · U14 home-vs-procedure classification.

**D314, D315 and D316 minted (next free D317) · F-85 … F-89 raised (next free F-90) · no incident —
every failure this session was caught by an install gate or by self-review before reaching live use.
Four canonical documents recovered by hash, three declared lost and closed under D316. Git kits
committed. This was Session 180.**


## §S181 — 15–16 Aug 2026 (Session 181, FULL — the longest session on record: KB housekeeping cleared · clinic+lab forensics · UPI gap root-caused · the CLINIC finance module BUILT, REDESIGNED and LIVE via a NEW one-command deploy chain; D317–D319; F-90–F-95)

**Owner directives, in sequence:** housekeeping first · elaborate the consultation-report gaps · fix the UPI gap · evaluate the tracker · proceed with minimum involvement, find a way for VPS work · redesign the clinic screen · EOS with git+KB work automated.

**Phase 0.** 41 of 41 rows md5-verified clean (subagent, hash-compare only). The three D316 LOST rows correctly did not halt. No open incident.

**Housekeeping (all three items closed):**
- **`Fault_Action_Register` v2.16 → v2.17** (`7bcde8c98d62e6570f9995b7bbbd5166`) — the three owed appends applied (F-82+F-83 · F-84 · F-85–F-89); new §7.1 carries those eight findings' full text verbatim; zero-loss proven mechanically against the v2.16 pin (§0–§6 byte-identical save approved notes). Source-of-truth line corrected (had cited the retired monolithic KB). **SEVEN changelog rows reconstructed** from evidence: six versions had no row at all (the F-45 family, recurring), and the row labelled v2.9 was proven by two independent Archive §S161 statements to describe S161 — moved to v2.7, the true v2.9 (S163) reconstructed into the gap.
- **`KB_Asset_Register` v1.11.0-R** (`631a2ba7ff907b98aadee89ac97d0412`) — the D316 LOST-RECONSTRUCTABLE row rebuilt from the recovered v1.10.3 + Archive §S177, the same recipe §S178 records the lost original using. Carries a provenance block stating it is NOT the lost bytes; adds a §5A index of A-D1–A-D15 and the §11 delivery rules. Adversarially verified; five errors found in the draft and fixed before delivery (incl. an UNKNOWN ruling on the asset repo's git position — the Archive contradicts itself).
- **Cold kit `DrManoj_Clinic_FULL_Handoff_Session181`** — the first FULL kit since S171 (the F-89 gap). 46 files, 42/42 pins verified at pack time. ⚠ **The PHI scan found six unmasked full patient numbers inside the canonical set itself** (Archive v1.27/v1.28, API card; one with full name + clinic id) — pre-existing, NOT introduced; deliberately not masked (would break every pin and the Archive's prefix-proof); kit flagged PHI-bearing; owner decision pending.

**Clinic + lab forensics (read-only):** the Accounting sheet's clinic tab has NO cash spine (no opening/closing/deposit columns — nothing to migrate; "replication of medical" was optimistic); revenue arithmetic is INVERTED between units (medical gross-minus-UPI vs clinic additive); lab nets expenses into `Net`; the lab tab is silent since 30 Jul (parked, owner). Drive `modifiedTime` proven a FALSE freshness signal for form-fed sheets (read 4 Jul while two tabs took submissions the same day). The per-patient procedure log: 76% rupee-exact days but 84% capture, no tender, free-text names — attribution spine only. **Owner decisions:** typed entry posts now, built to shift to tracker-posts later (D313's `tracker` adapter slot); clinic first, lab parked; clinic/lab cash is HANDED OVER (cash_movement to persons), historical banking question open.

**The reconciliation (37 days, 1 Jul–14 Aug):** capture 95.92% but only **16/37 days rupee-exact (43%)**; Procedure worst (83.84%, four −100% days), X-ray mis-classified not lost (two days prove it: day exact, streams shuffled). **Tender: cash +0.7%, UPI −17.7% (−₹30,400).** Staff Action `Day Revenue` tab found (53 workbooks) — well made for humans, but its per-line `Mode` is the visit mode replicated (1 of 2,100 visits has two modes) — presents visit tender in a per-stream layout; build on `revenue_ledger.csv`, lift the Free/Concession classification + `vs ₹600` flag into it.

**UPI gap root-caused (my split-leg hypothesis REFUTED — ₹2,000/6.6% only):** (1) **UPI booked as Cash at Docterz entry — ₹17,900/59%** (June: 101.4% revenue capture yet −₹21,101 UPI — only mislabelling can do that; concentrated in small single-line visits ≤₹500 at 9.5% online vs 29% clinic average); (2) missing revenue's UPI share ₹9,200/30% (Procedure-heavy); (3) unattributed tender ₹3,300/11%. **₹0 unexplained.** Not repairable at visit level (the label IS the corrupted field); day-level restatement or gateway records only. **No ledger-only check can detect it — the manual daily tab is the reconciliation anchor and has been quietly right all along.** Owner-supplied raw exports then proved: **the Docterz footer carries a complete 7-tender day breakdown nothing reads**; the two ledger day-gaps (₹500, ₹600) are Wallet/Debit-Card legs the tracker's parser silently drops (it knows only cash + Online Payment tokens); ledger Cash equals Docterz's own footer Cash to the rupee — **the misclassification happens at reception's mode selection, upstream of all our code.** The two export variants use incompatible split formats. `docterz_report.py` delivered (`783fffde…`, selftest 22/22, both real files parse clean, footer-asserted, all seven tenders, refuses unknown tokens). Clinical-data-report verdict: ADD it (Diagnosis 61%, Follow Up 76% — explicit dates the tracker infers today), never replace (all stream amounts zero, receipt trail gutted); periodic diagnosis export can retire once ingested. Discount capture stopped **18 Jun** (not 1 Jul — month-total artefact corrected); Lab stream carries **₹2,71,380 with no tender at all**; the concession_log parser swallows the Docterz footer and writes **three fake patients a day** into the staff sheet (15-Aug: 100% junk).

**THE BUILD — clinic module live, via a NEW deploy chain (D317), six kits, five installs, two green:**
- Finance code taken from the GitHub repo — **13/13 files hash-matched the Register pins** (F-52 disproven by hash, not assumed); repo found **PUBLIC** (F-90). Smoke made runnable offline first (F-87): `dev_seed_smoke_db.py` + baseline 166/176→167/177 (data-conditional; failure list is the invariant).
- **Deploy chain:** kit → `push_kit.bat` (PC, one double-click; v3 finds GitHub Desktop's bundled git, refuses to claim success unless the push succeeded) → GitHub `deploy_kits/` → `vps_deploy.sh` (one pasted command: clone/pull → SUMS → KIT_ID currency → hand off to the kit's own gated installer). Owner involvement per install: two small actions.
- **S182_C1a** (labelled S182 during S181 — an F-85 recurrence by the assistant, hours after quoting the rule; recorded, labels stand): clinic six-cell entry, strays, evidence, per-unit gating; offline 227/237 differential-clean. RED: installer assumed the retired WinSCP delivery (`cd /root/finance`); md5 gate fired before anything was touched; red branch printed "restored" over no-ops. **S182_C1b**: staged from kit dir, honest red branch. RED: `sqlite3` CLI absent on the VPS. **S182_C1c**: migration via python3 + preflight. RED — **the system working**: smoke-on-live-copy hit the bank arbiter (a real clinic UPI settlement exists for D1=14 Aug; the MPR stores all three units since S179); approve correctly refused over the open mismatch; a path the synthetic db can never exercise. Roles probe (owner, read-only) proved live unit_role identical to seeds. **S182_C1d**: mismatch path made deterministic (smoke plants a statement, OR IGNOREd on live), approve tested refuse-then-acknowledge, checks made self-describing. RED with the answer in the label: got 302 — the gate's login redirect for a roleless user on a page path (F-84 behaving); the check had demanded one refusal shape of two. Reproduction attempt with planted legacy attachments did NOT reproduce — evidence over theory throughout. **S182_C1e**: invariant-shaped check (never serve, never content-redirect) + real clinic makers seeded — **shavez, alisha, shivani** (the seat had pointed at placeholder `reception`, which has no portal login; owner flagged Shavez missing). **GREEN: SMOKE 240/240 on the real store** — the 10 offline failures were synthetic-db artefacts, all pass on live. Every red was caught by a gate; nothing was ever left half-installed; the C1b red proved the restore path end-to-end.
- **Owner redesign (D318) → S182_C2a, GREEN: SMOKE 316/316.** English "Clinic Entry Form"; four typed tender totals (Cash · UPI · **Debit Card** · **Razorpay** — Docterz online bookings); per-stream split comes from the tracker panel instead of typed cells; Extra Collection with required narration; **Expenses (drawer-reducing, note required)**; Grand Total of Cash; "दो सबूत" wording removed. **Two-stage approval:** Shavez verifies (side-table fact over `submitted` — no status CHECK rebuild; self-verify barred per D272; correction clears verification), owner is final checker (`clinic.final_checker` setting; may approve unverified with recorded skip). Razorpay rides additive `clinic_line_side` (day_line's mode CHECK excludes it — routed around, NOT rebuilt); UPI reconcile compares mode='upi' only (card/razorpay are other rails: ICICI MIS + Razorpay settlement report, both via Gmail auto-forward + the proven GAS-push pattern — owner-side, pending). **Tracker panel:** `tracker_day` table + token-gated `/finance/api/tracker-feed` (privacy-refusing: any name/phone key in a payload → 400) + read-only panel on entry AND review for all three levels; `gas/VPS_Push_TrackerDay.gs` shipped, wiring pending. Offline 304/314 differential-clean, verified independently twice.
- **Live at close:** `finance_app.py` `86382f62907b65cf17fded2ee914328e` · `finance_ui/finance_entry_clinic.html` `0c64fda2005ea3cd6692aeb8fd3dc728` · migrations `migration.S182_clinic` + `migration.S182_c2` applied (markers set) · new tables `clinic_verification`, `clinic_line_side`, `tracker_day` (+ the C1 `attachment` rebuild — the one non-additive step, taken knowingly) · rollback pairs `.bak_S182` and `.bak_S182C2` on the box. Migration file md5s: S182_clinic `bd2bb0ee5c58ac694ff1f741d70fee98` · S182_c2 `22c67f25b17e39faaaf66376df10c373`. GAS (not yet wired): `4e5c5b97d945fb63f8807bef54251be1`.
- **Parallel run begins:** the Google Form continues until clinic runs clean in parallel (D313); manual workflow remains the fallback. Portal tiles NOT yet built (S182 top task).

**D317 — deploy-by-kit over GitHub, one command a side.** Kits live in `deploy_kits/<KIT>/` in the repo; the PC publishes via `push_kit.bat`; the VPS installs via `vps_deploy.sh <KIT>` which verifies SUMS + KIT_ID currency (F-88) then runs the kit's own installer (preflight → stage-from-kit-dir → backup → swap → python3 migration → smoke gate → restart on green → HONEST red that reports whether live files were touched). Rules minted by the reds: an installer is gated end-to-end through its ACTUAL invocation path; it may use only tools proven present on the target; a re-issued kit takes a NEW name; a success message is printed only by the code path that succeeded. Owner's explicit OK = running the command; nothing is automatic.

**D318 — the clinic module's owner-directed shape.** Typed tender totals post (cash/upi/card/razorpay); the per-stream truth is Docterz's, displayed read-only beside the entry (the spine reads, never posts); strays carry mandatory narration; expenses reduce the drawer only; two-stage approval (verifier → final checker, settings-named); verification is a side-table fact, never a status rebuild; UPI reconciles against the bank alone, other tenders against their own rails.

**D319 — the KB swap is the assistant's job now.** At every EOS the assistant writes the canonical documents DIRECTLY into project knowledge at their canonical paths (replace-in-place), produces MD5SUMS, and hands the owner exactly two actions: one double-click (`push_kit.bat` on the KB kit → git `deploy_kits/`) and one download (the cold kit zip). Manual project-knowledge uploads are retired. Phase 0 discipline unchanged — the next session still verifies every row by hash.

**F-90 — the GitHub repo is PUBLIC.** Proven by anonymous clone (it is how the finance code was fetched and hash-verified). Answers F-9's old "repo visibility UNKNOWN". Code-only (F-31 held: no PHI, no secrets, finance.db never committed) — but the whole automation estate incl. the WebApp.gs function names F-9 worried about is world-readable. Owner decision: make private + read-only deploy key on the VPS (keeps D317 working; the key never passes through chat).
**F-91 — UPI recorded as Cash at the point of entry (Docterz).** ₹17,900 over six weeks; proven by the accounting identity, the June month, and the footer-vs-ledger rupee match; invisible to every ledger-internal check by construction. The typed daily tab is the reconciliation anchor. Fix is behavioural (reception's mode selection) + the C1/C2 variance alarm; history repairable at day level only.
**F-92 — discount capture stopped 18 Jun 2026.** ₹1,33,720 captured Apr–18 Jun, zero after; `concession_log`'s per-stream discount columns 0.0 forever; concessions still being GIVEN (Free/Concession section, `vs ₹600` flags) — no longer VALUED. Same shape as Marg U7. Part of an 18–19 Jun regression cluster (gateway tokens stopped leaking; Lab rows stopped) — tracker-side investigation owed.
**F-93 — the concession parser swallows the Docterz footer and mints three fake patients a day** into the staff-facing workbook (one named `Cash`, one named the day's cash figure; 15-Aug: the section was 100% junk). Kin F-78/E5: a footer row that must be dropped and is not.
**F-94 — an installer's environment assumptions are part of its specification** (the C1a/C1b/C1c trilogy: delivery-path cwd · absent sqlite3 CLI · unconditional success/restore messages). Gate the installer through its actual invocation path on a target-shaped environment; preflight its tools; print only what happened.
**F-95 — a synthetic store proves logic, not life.** The C1c red (real bank statements), the C1e seat (placeholder username with no login), and the 302 (auth-mode-dependent refusal shape) were all invisible offline. Rules: smoke checks print what they saw; environment-dependent invariants are asserted as invariants, not as one environment's shape; before a first live gate, enrich the offline store with live-shaped data (statements, history, roles).

**Recorded, NOT minted (owner's numbers to spend):** Drive modifiedTime as false freshness (D188 kin) · Docterz export schema instability (21/37/39 cols; `Amount collected` type-shifts exactly on split rows) · the Lab ₹2,71,380 no-tender block · the medical broker-role guard bug (fail-closed but wrong) · the canonical set's own unmasked patient numbers (cold-kit PHI flag) · `dev_seed_smoke_db.py`'s hard-coded path.

**Assistant self-reports:** kits labelled S182 inside Session 181 (F-85's own rule, recurred); the C1a "restored" and the push_kit "pushed" messages both claimed success over failure (the F-94 family, own goals both); one wrong hypothesis (split-leg) and one wrong correction (discounts "stopped 1 Jul") — both caught by measurement before they cost anything.

**EOS mechanics this close (D319 first execution):** Register v5.2 → **v5.3** (additive) · this Archive v1.28 → **v1.29** (§S181 pure append, prefix byte-identical to `0e8b4bd6…`) · Runbook v114 → **v115** · `START_HERE_SESSION_182` · manifest re-pinned (v2.17 CURRENT, v2.16 historical; v1.11.0-R CURRENT, v1.10.3 historical) · canonical docs written to project knowledge by the assistant · KB git kit + fresh cold kit delivered. Session documents in `claude/`: forensics · target design · C1 contract + addendum · reconciliation + StaffAction findings · UPI root cause · Docterz verdict. **Next free: D320 · F-96 · A-D25 · Session 182.** ⭐ S182: portal tiles · GAS tracker-feed wiring · first parallel-run week checks · month-close family · the F-90 privacy decision. This was Session 181.


---

## §S182 — 16 Aug 2026 (FULL) — Phase 0 proved against git for the first time; the clinic PORTAL TILES live; a fail-open identity default found and closed; F-96–F-99; D320

**Two live installs on `/root/portal/portal.py`, both green, both gated before anything was touched. One driver kit placed. No incident. The `portal.py` Register pin was found STALE by two sessions — the finding that shaped the whole session.**

### 1. Phase 0 — verified independently, not accepted on report

The session opened on the owner's report that a previous session had rebuilt Phase 0 against git and passed **48 of 48** rows at commit `aabb5ea`. That claim was not taken on trust. The repository was cloned anonymously (which incidentally re-proved **F-90**: the repo is public), and two checks were run:

- `md5sum -c MD5SUMS_ALL.txt` inside `deploy_kits/KB_canon_all/` → **48 OK, 0 failed**.
- The check that actually matters: the **45 pinned rows from `CANONICAL_MANIFEST.md`** were hashed against the git bytes *independently of the kit's own SUMS file* → **45/45 OK**. The 48 = 45 canonical rows + 3 Fault-Register append artefacts, which the manifest correctly classes as provenance only. Nothing pinned was missing.

The distinction matters and is **F-88's own lesson**: a self-generated SUMS file passing against the files beside it proves internal consistency, never currency. The kit passes the stronger test too. The kit's `CANONICAL_MANIFEST.md` is byte-identical to project knowledge's (`3af7657d…`), so git and project knowledge are demonstrably one canon rather than two drifting copies.

**`README_VERIFY.md`'s rule is adopted as correct:** *a hash verdict is only ever pronounced on bytes delivered as a FILE (git clone, or project_read returning a file path); re-keyed inline text may corroborate, never convict or acquit.* Earlier the same day a Phase 0 run from project knowledge had produced a **false red** on `KB_Register` v4.6 (`b7330f5c…` against a pin of `0503f255…`); settled against the byte-exact git copy, the row was clean, and the divergence was two hunks totalling 104 bytes introduced by re-keying — one spurious blank line and one dropped clause. **Transcription error, proven rather than assumed.** The transcription hazard is now closed by method, not by care.

### 2. F-96 — the canonical set is PHI-bearing in a public repository (owner ruled: accept)

Scanning all 48 files for mobile-shaped strings: 12 hits, of which 3 are digit runs inside md5 hashes and 2 are the clinic's own helpline/WhatsApp number. That leaves **7 unmasked patient mobile numbers**, and — worse than S181 recorded — **at least two patient names and one clinic patient ID sitting directly beside them**, in the Callback-Tracker audit and in Archive v1.27/v1.28/v1.29 (14 hits in each of the three Archive copies).

S181 had flagged "six unmasked numbers, cold kit is PHI-bearing, owner ruling owed." That ruling was **overtaken by events**: the same content was pushed to a public repo at 11:34 on 16 Aug. Six of the affected files were already in the older `canonical-docs/` folder before that, so exposure is not new; the push multiplied it.

This is an **F-31 breach**, and its shape is instructive: **a passing 48/48 conceals it.** The check proves integrity and says nothing about whether the content belongs there at all — F-88 one level up.

**D320 (owner ruling): the repository stays public, knowingly.** Recorded as a deliberate decision rather than an open finding. The assistant registered one dissent and dropped it: the seven numbers and two names belong to patients rather than to the practice, so they cannot consent to the trade. Private-plus-read-only-deploy-key remains available at any time, costs nothing, and changes no workflow.

### 3. F-97 — the live-code pins are verified by nothing, and one was stale by two sessions

The S182 top task was portal tiles. Before writing a line, the obvious build path was checked and found to be a trap.

`TILES` is a hardcoded Python list inside `portal.py` with a fail-loud assert; tiles cannot come from config. `S179_Finance_LIVE_State` records two live portal tiles — **Daily Sale** → `/finance/entry` and **Sanjeevni Medicos** → `/finance/review`. **All three copies of `portal.py` in the repo (`portal/`, `portal_kit/`, `launcher/`) contain zero occurrences of `/finance`.** The Register pinned `portal.py` at `da4177091ba9f188be6a0ff3eaf25bd8` "S176", and `portal/portal.py` matched that **byte-for-byte**.

Confirmed on the box by the owner:

| | md5 | `/finance` refs |
|---|---|---|
| Register pin (S176) | `da4177091ba9f188be6a0ff3eaf25bd8` | 0 |
| repo `portal/portal.py` | `da4177091ba9f188be6a0ff3eaf25bd8` | 0 |
| **live** | **`34f038a7652024d49479569ed53bbfb9`** | **2** |

The pin and the repo agreed **with each other**, and both were two sessions behind the box. A full-file replacement built the obvious way would have **deleted the medical unit's two live finance tiles**, and every gate would have passed on the way out, because nothing asserts their presence. The matching hash would have actively reassured.

**F-97: Phase 0 verifies DOCUMENTS. Nothing verifies the live-code pins in the Register at all — and the new git-clone Phase 0 makes that gap easier to miss, not harder, because it feels total.** A filename is not provenance (D188); neither is a Register pin.

The live file was transferred and **hash-verified against the md5 the owner had read off the box himself** (`34f038a765…`) before being used. Diff against the S176 repo copy: three hunks, all S179 finance, nothing else drifted.

### 4. S182_P1a — the clinic portal tiles (LIVE, 42/42)

Built on the verified live bytes. Design decisions taken from the **seeded migration data**, not from the runbook's summary line — which proved incomplete:

- `finance_migration_S182_clinic.sql` seeds clinic **makers** shavez, alisha, shivani (+ a `reception` placeholder); `_c2.sql` adds **shavez as a clinic `checker`** — the middle approver who verifies before final approval. The runbook's one-liner ("Daily Collection for shavez/alisha/shivani, Clinic review for owner+bhawna") omitted that. **Shavez needs both tiles**, or he has no route to the screen where he verifies.
- Tile wording is already **data**: `clinic.tile.maker_title` = "Daily Collection", `clinic.tile.checker_title` = "Clinic", with Hindi subtitles, served by `/finance/clinic/api/tile-meta`.

**Owner decisions:** Shavez gets both tiles · the checker tile matches the seeded name ("Clinic") and is **wired dynamically** · the legacy Google-Sheet "Daily Collections" tile is **retired**.

Implemented as three blocks: two TILES entries with `roles: []` (grant-only via `USER_TILE_EXTRA`, because the clinic rosters are named people and a role-based tile would leak to every other staff login), the `_TILE_GROUP` rows, and the named grants. Plus client-side hydration matching the house idiom already used by the Staff Register and Clinic Gist tiles — **the portal never waits on the finance app, and a failure leaves the static text**.

**A conflict surfaced and was resolved rather than papered over:** `tile-meta` is role-collapsed and returns ONE tile per caller (checker wins), so it cannot label both of Shavez's tiles. Resolved by hydrating **on href match**, leaving any non-matching clinic tile on its static text. The limitation is documented rather than hidden: Shavez's *maker* tile keeps its static label.

**The gate (42 checks) was proven to bite before it was trusted** — run against the unmodified live file, 16 checks correctly failed; with "Sanjeevni Medicos" deliberately deleted from a copy, it caught the loss and named it. Imported against the **real** `clinic_sso.py` / `clinic_users.py` at their live pins, not stubs (F-95).

**Offline rehearsal caught a real bug that would have produced a FALSE RED on the box:** `importlib` cannot infer a loader for a file named `portal.py.new`, so the gate died with an obscure `AttributeError`. Fixed with an explicit `SourceFileLoader`. All three installer paths were then rehearsed against a fake portal — green; drift-refusal touching nothing; post-swap failure restoring to the exact original hash.

**New in this kit and adopted as practice: a LIVE-FILE CURRENCY GATE.** The installer refuses unless `/root/portal/portal.py` is exactly the file the kit was built against, and says so without touching anything. F-97 turned into a gate.

Installed green: `portal.py` `34f038a765…` → **`410388daa9cf39daba6bb2d4c187a1e6`**.

### 5. F-98 — the portal assumed "doctor" when it could not identify the caller (found, fixed, LIVE)

The owner's post-install portal page showed the **anonymous** header line and was missing the two new tiles — *and* "Manage Users", a grant-only tile untouched since S164. That control case proved the tiles were never broken: with no identity, `USER_TILE_EXTRA` has no username to match and **every** grant-only tile vanishes.

Chasing why identity was empty found this, in the code's own words:

> `_is_doctor()`: *"Mirror home(): a trusted device with no SSO user is treated as the doctor."*

`_authed()` accepts a valid SSO cookie **or** `_is_trusted()` — the legacy PIN-era device cookie kept for the SSO transition. Together: **a browser holding that old device cookie, with no SSO session at all, was authenticated and treated as the doctor** — not just tiles, but every `@doctor_required` route: the Clinic Gist, the Call Console, the per-staff coaching report. Patient-data surfaces. The likeliest browser in that state is the clinic PC, shared by reception.

**This is F-84's pattern** — *anything that grants identity for convenience must be opt-in; the production default must be closed* — minted on the finance app at S179, fixed there, and still sitting in the SSO broker that fronts everything else. Defence in depth limited it: `/portal/users` uses `@user_admin_required`, which demands a real SSO user and 403s a trusted device; the finance app has been fail-closed since F-84; downstream apps run their own verify-shims (D265).

**Fixed in S182_P2a, keyed to `_sso_ready()` rather than to the cookie:** when broker mode is available, identity must be proven; when it is not (secret unreadable, or a pre-SSO estate), the legacy device-trust path is **untouched**. That second branch is deliberate — **D264 requires a verify-shim to be inert on failure**, and a naive fail-closed edit would lock the owner out of his own front door the first time `portal_config` broke. The D264 branch is asserted as its own test.

**The gate (48 checks) adds two blocks the P1a gate lacked:** an **identity matrix** over all four combinations of (broker ready?, SSO user?), and **SERVED-HTML checks (D307c)** that render the real page for manoj, bhawna, shavez, alisha, shivani and darpan and read the tiles out of the HTML each would receive, presence **and absence**. That second block is precisely what was missing when the empty portal could not be explained.

**Two of the gate's own assertions were wrong on first run and the gate caught them:** a bare `">Clinic<"` match also hit the **section header** "Clinic" (the tile name collides with a section name — a human-readable ambiguity, flagged to the owner), and Darpan had wrongly been expected to see "Sanjeevni Medicos" (he is `staff`; that tile is `doctor`). Both were the author's errors, not the code's. Proven to bite: against the pre-fix live file it fails on exactly the two symptoms.

Installed green: `portal.py` `410388da…` → **`2784b1cb76abfb9dbe2407c38da5bd83`**.

**Confirmed in the real world, not just at the gate.** Owner's page: "Signed in as manoj (doctor)", the **Clinic** tile present, no Daily Collection, and **Manage Users restored**. Shavez's page: "Signed in as shavez (manager)" with **both** clinic tiles. Every one of the 48 served-HTML predictions held against real logins.

### 6. F-99 — a missing-day alarm anchored on the first filed day cannot see a unit that never files one

The clinic review screen showed every day 1–16 Aug as `pending`, never `missing`; "Days not filed 0"; exceptions empty. `refresh_missing_days()` anchors on `MIN(business_date)` for the unit and **returns 0 immediately when the unit has no `day_entry` rows**, so no exception is raised and the grid falls through to `pending`. There is no `clinic.start_date`; the anchor is literally "the earliest day you ever filed."

The alarm therefore **arms itself the moment the first clinic day is filed**, and every unfiled day after that shouts — but until then the system cannot distinguish *"this unit has not started"* from *"this unit has gone dark."* Medical never hit this because it was seeded with 121 imported legacy days. **Clinic is the first unit to start empty, and lab will hit it too.** No code was written: a new setting would mean another kit against a finance app freshly green at 316/316, to cover a window that closes with the first filed day.

### 7. The Marg fortnight — S182_M1a placed, and what it found

The owner supplied a Marg BILL WISE export, 1–15 Aug, and asked to ingest it. It parsed clean through the live `marg_report.py` (`28b47d44…`): **355 bills · net ₹2,85,934** (cash ₹1,89,438 / non-cash ₹96,496), all 15 days present, each summing exactly to its own DAY TOTAL, GRAND TOTAL present. Warnings all working as designed: 18 credit notes totalling −₹9,760 (D314) · 93 of 355 bills with no clinic ID heading to WALK-IN · 7 bills with non-4-digit clinic IDs scored low into review (D315).

**An anomaly the parser does not flag, and the most valuable thing in the file: 11 Aug (₹20,412, 25 bills) and 14 Aug (₹17,943, 23 bills) are 100% cash — not one UPI or card bill**, against 40–76% cash on every other working day. That is **F-91's shape appearing in the pharmacy** rather than at Docterz reception. ₹38,355 whose true tender split is unknown; no code recovers it, only asking Darpan while he remembers.

Two live behaviours shaped the driver: `ingest_day()` refuses any day not already filed (the spine **reads, never posts** — D313), and re-ingesting a day **deletes** what its previous batch produced. So `marg_backfill.py` is **dry-run by default**, surveys before it writes, and backs up `finance.db` before the first write.

**The failure it exists to prevent, found in rehearsal:** `_colmap()` returns empty when no `ingest_source` row matches, and `adapter_csv` then reads **zero rows while `ingest_day` still reports ok** — a clean-looking success that ingested nothing, on live patient data. The driver now refuses on an inactive source, refuses on a column map that does not match the header `marg_report.py` actually emits (naming each mismatched field), and **aborts the whole run** if rows read ≠ rows in the CSV. Rehearsed three ways against a throwaway database built from the real schema: inactive → refused; wrong map (the selftest's own `"Bill No"` / `"Customer"` / `"Net Amt"` names) → refused, each field named; correct map → wrote 37/37, 28/28, 36/36, 25/25, giving **99 spine lines + 27 review = 126 bills, none dropped**, batch status `partial` (correct — low-confidence lines to review, D315).

**On the live box the dry run refused immediately: `(medical, marg_export)` is seeded ACTIVE=0 and has NO column map rows at all** — absent, not wrong. Read-only survey of the live database:

- **121 medical days filed, 1 Apr 2026 → 13 Aug 2026, all `legacy_sheet`** (Apr 26 · May 27 · Jun 27 · Jul 28 · Aug 13).
- **`sale_item` = 0 and `sale_line_item` = 0.** Both stores have never been populated.

So the owner's stated goal — backfill item-wise sale data from 1 April in 15-day Marg exports, to power the sale-return pipeline — is **exactly reachable** (1 April is precisely where filed days begin) and carries **zero supersede risk** (nothing to destroy). His 15-day chunking is validated by the file itself: it carried **1,688 drug-detail lines** and still passed the completeness check, where S180 had observed a month-to-date run with item detail truncating silently at day 6 of 15.

**What the driver still lacks:** it writes only `sale_item`. The return pipeline needs `sale_line_item`, populated by `finance_returns.load_lines()` from `marg_report.write_items_csv` rows. A v2 driver doing both stores per day, plus the column-map setup, is the S183 top task.

### 8. Housekeeping and process

- **A formatting fault of the assistant's, twice:** deploy commands written inline followed by a full stop caused the owner to paste `S182_P2a.` and `S182_M1a.`, which `vps_deploy.sh` refused cleanly both times. Commands now go in their own fenced block. Harmless, and the refusals were exemplary — each named exactly what it looked for before touching anything.
- **`+ … (forced update)` on every `vps_deploy.sh` run is normal**, not history rewriting: the script fetches with `--depth 1`, and a shallow fetch always grafts a fresh root.
- **The device bridge was used as the S181 addendum intended:** Downloads and `D:\dr-manoj-git` connected at session start, and all three kits were written straight into `deploy_kits\<KIT>\` and hash-verified on the owner's disk, reducing his PC action to one double-click.
- **Still open, small:** the clinic month-close prompt says "as per the **Sanjeevni** sale register soft copy" — a string the unit-name rewrite missed on the shared review screen (also `legacy_medicine_copy` / `legacy_implant_copy` scan labels). And whether Shavez's "Awaiting your approval" KPI counts verifications or final approvals — unobservable on an empty day, to be watched on the first real one.

### 9. Close

Live now: `/root/portal/portal.py` **`2784b1cb76abfb9dbe2407c38da5bd83`** · `/root/finance/marg_backfill.py` **`e101c595619dc39a19397abb040d64c9`** (placed, not yet run to completion). Kits `S182_P1a` · `S182_P2a` · `S182_M1a` in the repo. Medical and clinic finance apps unchanged this session and proven so at every gate.

**D320 minted. F-96 · F-97 · F-98 (fixed) · F-99 raised. No incident** — every failure was caught by a gate, by a rehearsal, or by reading the code before writing it. Cold-kit count **2 of 3–5**.

⭐ **S183 top task: the Marg April→August backfill** — v2 driver (bills + drug lines), the `marg_export` column map and activation, then the fortnight chunks. Then: the clinic parallel-run checks, the tracker-feed GAS wiring, and the F-97 structural fix (something that verifies live-code pins). **Next free: D321 · F-100 · A-D25 · Session 183.** This was Session 182.


**END OF KB HISTORY ARCHIVE v1.30. §S182 is the last section; §S181, §S180, §S179, §S178, §S177, §S176, §S175, §S174, §S173, §S172 and earlier sit above it. If §S181 or this marker is absent, this file is truncated and must not be used as canonical.**


## §S183 — 16 Aug 2026 (Session 183, FULL — the F-97 structural fix SHIPPED; the Marg pharmacy feed went LIVE and backfilled five months; the Sanjeevni cash chain reconciled from bank records and found whole; D321; F-100–F-104)

*Folded into this Archive at the S185 close (17 Aug 2026), together with §S184 and §S185. The S183 append was deferred at its own close to "S184 opening housekeeping", deferred again at S184, and applied here. Sources, all hash-verified at the S185 Phase 0 — no filename taken as provenance (D188): `HANDOFF_RUNBOOK_2026-08-16_Session183close_v117.md` (md5 `cc523169dbcd0e2fb50a96ab132e215b`) · `KB_Register_v5_5_S183.md` (md5 `3cad79e6361c6e1777f3bc9db983770d`) · `CANONICAL_MANIFEST.md` §S183 block · `S183_Sanjeevni_Cash_Reconciliation_YesBank.md` (md5 `ca49c4113b3cbd658fd2986b1aa7bb89`) · `S183_Sanjeevni_Daily_Cash_Design_and_Marg_Findings.md` (md5 `de4f88b3a48e71c19e708f6a1d274f41`).*

### 1. Thread one — the F-97 structural fix is LIVE (D321)

`verify_live_pins.py` and a generated `live_pins.txt` now sit at `/root/deploy/` on the box. One command — `python3 /root/deploy/verify_live_pins.py` — hashes every pinned live file and returns **MATCH / DRIFT / MISSING / UNTRACKED**, exiting non-zero on drift or absence. Kits S183_V1a → V1c.

**Its first run found the record wrong about nine of the forty-four live rows.** Eight files were recorded one directory too high — the call-hook/verdict family lives in `/root/wa/call-hook/` and `/root/wa/recordings-archive/`, not `/root/wa/` (**F-101**) — and one pin was genuinely stale: `call_hook_capture.py`, pinned at its S126 value while the live file had been replaced on **12 Jul 2026 at 18:13** (**F-102**). Of the rows it could check, **31 of 31 matched with zero drift**, and the call-hook receiver was measured healthy in the same breath (dual-key gate ON, `current=key_ea20dd previous=key_db8972`, ROTATION IN PROGRESS, 26 accepted / 0 refused).

**F-101's lesson is about severity, not bookkeeping.** A wrong path downgrades a DRIFT to a MISSING. "Not there" reads as a filing error; "different from the record" reads as danger. The eighth row proved it — a genuine stale hash was wearing a MISSING's clothes. **F-102 is an instructive inversion of F-97:** at S182 the repo agreed with the stale pin and the box was right; here the repo was right and only the record was wrong. The record is the weak point in both directions, which is exactly why the check has to interrogate the machine.

**F-100** was raised and fixed on the publishing side the same session: `push_kit.bat` reported "pushed successfully" while git had silently dropped a kit file. The pin list was named `live_pins.tsv` and `.gitignore` carries a blanket `*.tsv` — one of the data-format guards that keep patient data out of a public repo (F-31/F-49, D320). `git add <folder>` says nothing about ignored files inside it, so the published kit was incomplete and the fault surfaced only as a SUMS refusal at the VPS console. **The publishing record claimed a file that was not there — F-97's shape one layer up the toolchain.** Fixed two ways: the file was renamed to `.txt` — **no exception was carved into `.gitignore`**, because a blanket PHI rule with holes in it is how something eventually gets through — and **`push_kit.bat` v4** now lists any excluded file with the exact rule that excluded it and REFUSES to commit.

### 2. Thread two — the Marg pharmacy feed is LIVE and backfilled (the S183 ⭐ top task)

Kit **S183_M2a**: `marg_report.py` now reads `.xlsx` as well as `.xls` (staff save exports through Excel; the `.xls` path proven byte-identical, the `.xlsx` reader proven faithful by a round-trip); migration **`S183_marg_map`** activates the `marg_export` adapter with its 7-field column map; `marg_backfill.py` **v2** writes both `sale_item` and `sale_line_item`.

**Backfilled 119 days, 1 Apr → 13 Aug: 3,044 bills, 15,574 drug lines, 982 bills attributed to 449 patients, 45 returns — and the money (`day_line`) was byte-identical before and after.** That is D313's "attribution never moves the books" proven at scale, and it is what makes the Marg feed and any future re-ingest safe. The 5 not-filed days (Marg-only) refused harmlessly. A false-abort on Marg's zero-net procedure write-offs was caught by the offline test and fixed — the F-87 lesson working as intended.

### 3. Thread three — the Sanjeevni cash chain reconciled, and no money is missing

The drawer showed an impossible **−₹30,056**. With the owner's bank statements it resolved completely: **ICICI (…312505) holds card and UPI only** — Darpan's declared UPI matches it T+1, so his discipline is confirmed good — and **all cash is swept to a Yes Bank account** as `CASH DEP-SELF-SANJEEVNI MEDICOS`. **Sixteen verified cash deposits, ₹16,45,600, between 9 Apr and 13 Aug, were unrecorded.** That was the entire "break."

Reconciled: cash collected ₹17,98,033 − deposits ₹16,45,600 − expenses ₹84,442 = **+₹67,991 drawer growth**. Derived drawer ≈ **₹75k**, after a ~₹40k correction for salary advances drawn from the drawer.

**F-103** minted (the finance system reconciles UPI against ICICI but has NO cash-deposit reconciliation against Yes Bank — which is precisely why sixteen real movements could go unrecorded for months and read as missing money). **F-104** minted (the backfill fed identity-less legacy bills through attribution, creating ~2,062 review items and 118 `line_sum_vs_day_total` exceptions; owner ruled: reclassify legacy no-ID bills to WALK-IN).

**No live finance write was made this session.** The cash reconciliation was completed as read-only analysis and the booking deliberately deferred to fresh runway — nothing was missing, so there was no urgency to justify writing to live financial books at the tail of a marathon.

### 4. Mental models this session produced

**A hash proves agreement with a record, not with reality (F-97/F-102).** The pin verifier exists because git and the Register agreed with each other and both were wrong. **A wrong path hides a wrong hash (F-101).** **A green light is only green about the thing it checked** — the Marg files' arithmetic self-checks passed and said nothing about the description column; `md5sum -c` proves integrity, never currency (F-88); 48/48 proves nothing about whether PHI belongs in the set (F-96). **A break in a ledger is often an unrecorded real movement, not a loss (F-103).** **The bank is the arbiter, and it cleared the human** — the person was never the problem; the missing reconciliation was.

### 5. Close

Live now: `marg_report.py` **`829f4344df6e086510bb0fb6112ecb77`** · `marg_backfill.py` **`fa33ec8a6dfa0ee0b6af5613160f3394`** · migration `S183_marg_map` `9340675c9105f9d5e78cc37980494999` · `/root/deploy/verify_live_pins.py` `ce36dbf10e7d5bbd5310507add41f3cb`. Register-pinned corrections: the eight call-hook/verdict paths + `call_hook_capture.py` `b8a1a293c54dfb6528e04fdf31f8d3e6`.

**D321 minted. F-100 · F-101 · F-102 (all closed same session) · F-103 · F-104 (open) raised. No incident.** Cold kit `KB_S183_close` taken — count 3 of 3–5, F-89 cadence met.

⭐ **S184 top task: book the Sanjeevni cash correction, gated.** **Next free: D322 · F-105 · A-D25 · Session 184.** This was Session 183.

---

## §S184 — 17 Aug 2026 (Session 184, FULL — the Sanjeevni cash books CORRECTED LIVE, exceptions regenerated, the D322 holiday classifier shipped, and the reserve/daily-flow model designed end to end; D322; F-105, F-106)

*Folded into this Archive at the S185 close. Source, hash-verified: `HANDOFF_RUNBOOK_2026-08-17_Session184close_v118.md` — filed to the repo at the S185 close under F-107 and pinned there; the four S184 design docs (`S184_Float_Investigation`, `S184_Reconciliation_Workbench_Design`, `S184_Reserve_Counter_Person_Design`, `S184_DailyFlow_Holiday_Reserve_Design`, plus `S184_Parking_Windows_29days`, `S184_Cash_Correction_Build_State`, `S184_Sheet_vs_YesBank_Verification`) remain in project knowledge as the detailed references.*

### 1. Thread one — the Sanjeevni (medical) cash books were CORRECTED LIVE

The −₹30,056 was diagnosed to the cell: the 13-Aug deposit was subtracted in the typed opening **and** again by the sheet formula — double-counted, on one late-filed row.

Then, **survey first**. `S184_S1a` was a read-only DB survey, and it is the only reason the correction did not do far more damage than the fault: it found that `finance.db` **already held** the sheet's 31 deposit movements (₹16,59,114) and 36 carry-forward adjustments (−₹84,533). A blind "add the 16 deposits" — which is exactly what the S183 record prescribed — **would have double-counted ₹16 lakh.** The record said the deposits were unrecorded; the box said they were already there.

- **`S184_C1a`** (gated migration, INSTALLED): the 31 sheet deposits were replaced by the **16 Yes Bank verified credits** (₹16,45,600); the 36 legacy adjustments removed and backed up in `s184_removed_*`; **₹40,000 of Darpan advances** recorded as drawer expenses (no `staff_id`, so deliberately NOT posted to the Staff Ledger — owner's choice); ₹337 of procedure-medicine as noncash. **Closing 13 Aug moved −30,056 → +27,654.** `day_line` — the sale money — was byte-identical throughout. Marker `migration.S184_cash_correction`; backup `finance.db.bak_S184C1_20260817_065446`.
- **`S184_C2a`** (gated migration, INSTALLED): `carry_forward_break` and `negative_cash` exceptions are created **only** by the one-shot importer, so C1a left them stale — the books were right and the alarms still red. C2a resolved all 36 breaks and recomputed negative_cash from `v_cash_ledger` down to the **29 real parking-window days** (4 Jun – 4 Aug), each labelled *"cash parked with Dr Bhawna ahead of a bank trip (verify from her copy)"*. Marker `migration.S184_C2a_exceptions`. Dashboard after: cash-in-hand **₹42,993**, unexplained adjustments **0**.

### 2. Thread two — the D322 missing-day classifier shipped LIVE

`finance_app.py` `86382f62…` → **`c66bec2b76…`**, kit `S184_F1b` (a reship of F1a). `refresh_missing_days` was revised per **D322**: Sundays and attendance-sourced clinic holidays (the `clinic_holiday` table plus `festival_day` with `clinic_closed=1`) become an optional kind **`clinic_holiday`** (low severity, not owed); genuine weekday gaps stay owed `missing_day`. A new `clinic_holidays()` helper reads the attendance database read-only and **fail-soft** (`FINANCE_ATTENDANCE_DB`, default `/root/staff_register/staff_register.db`).

**F1a first went RED — and that red is F-106.** Its `--selftest` asserted the *pre-S184* store state: cash negative, breaks open, marg unmapped. Our own legitimate corrections read as failures, and the gate correctly restored. F1b made those four checks **state-adaptive**, and came back **314/314** on the corrected store. This is the same family as F-88 (a checksum proves integrity, never currency) and F-97 (a pin agrees with a record, not reality): **a self-test that asserts a data state becomes a liability the instant the data is legitimately corrected.**

### 3. Thread three — the app enforced correctness, and it looked like an obstacle (F-105)

Darpan's 14/15 Aug catch-up was **BLOCKED** until the deposits were booked: the Submit guard refused because the opening carried the −₹30,056, and the guard will not accept a negative opening. The S183 record had said this catch-up "needs nothing above." **The record was wrong and the box was right** — the D313 invariant doing exactly its job.

After C1a, 14 Aug (cash ₹11,413 / UPI ₹6,530) and 15 Aug (cash ₹3,926 / UPI ₹4,925) were entered on the maker form and **saved as drafts** — the form requires three scans or a stated reason to Submit, and the owner chose that Darpan attaches the scans and submits, with Manoj approving. **16 Aug was left unclosed** (a Sunday — now optional under D322).

### 4. Thread four — the reserve / daily-flow model designed end to end (NOT built)

Four design documents, all in project knowledge, none of them code:

- **`S184_Reserve_Counter_Person_Design`** — biometric attendance as a **HINT in both directions**, never an authority; the standard Darpan-maker / Manoj-checker gate retained; **four cash destinations** (Darpan's drawer, Dr Bhawna, Dr Manoj, kept-by-reserve); multi-day cumulative stretches reconciled by Marg for sale and the bank for UPI; an extensible counter-person registry seeded with Vinay Saxena.
- **`S184_Reconciliation_Workbench_Design`** — one screen joining Marg ⋈ bank ⋈ entry, cash→UPI suggestions graded like D315 and never auto-applied, a correction log through `audit_log`. Mostly reads data that already exists, which is why it is the highest-value / lowest-risk item on the backlog and delivers the F-91 fix.
- Plus the holiday and parking-window documents.

### 5. Thread five — the opening float is OPEN, and instrumented

Proven this session: **booking the 29 negatives away is mathematically impossible at float 0.** The books come up short by roughly ₹85k — the first-week float, matching the sheet's 8-Apr ₹99,017 injection. So *"no negatives"* and *"drawer ≈ ₹43k"* are **mutually exclusive**; only a physical count decides which is real.

`Sanjeevni_Cash_Reconciliation.xlsx` (4 tabs) was delivered to fill to a float verdict from two numbers: Darpan's drawer count and Dr Bhawna's held cash. Both booking paths are prepped — float ≈ 0 → book nothing, the negatives stay labelled; float ≈ 85–99k → ship the gated **`S184_C3a`** opening-float-parked-with-Dr-Bhawna migration.

**The rule this produced: don't fabricate a schedule to make a chart look right.** A negative drawer is unrecorded movement, not loss — but you cannot book it away without the float.

### 6. Close

**D322 minted. F-105 and F-106 raised. No incident** — every failure was caught by a gate. An expert critical evaluation of the whole design was delivered (accuracy / convenience / single-place recall, with prioritised suggestions); the owner accepted #1–4 and #6, took #5 the same day, and #7 with a blank-but-flagged count field, with Hindi labels to be shown first.

**The session shipped live code and live data and did NOT fold the canon** — the Archive and Fault-Register appends, the Register bump and the manifest rebuild were all left owed, compounding S183's own deferral. That debt was carried into S185 and cleared at the S185 close.

⭐ **S185 top task: resolve the opening float, then book.** **Next free: D323 · F-107 · A-D25 · Session 185.** This was Session 184.

---

## §S185 — 17 Aug 2026 (Session 185, FULL — a verification session that became the fold-in session: Phase 0 proved the canon intact, F-107 and F-108 raised, and THREE sessions of canonical debt were cleared in one pass)

### 1. Phase 0 — green, and independently so

Documents were verified against **git bytes**, per the S182 rule that a hash verdict is pronounced only on bytes delivered as a file. The repo was cloned anonymously and `md5sum -c MD5SUMS_ALL.txt` run in `deploy_kits/KB_canon_all`: **55 of 55 OK, zero failures** (kit ID `536961e984832a38e008d9c26524b097`).

The **F-88 cross-check** was then run separately, because a passing `md5sum -c` proves a kit internally consistent rather than current. All **77** distinct md5 tokens in `CANONICAL_MANIFEST.md` were extracted and compared against the real hashes of every file in the kit: **52 matched real bytes**, and the **25** that did not are each legitimately not a document row — live VPS code pins (Register-tracked, never manifest rows), Tier-2 artefact digests, the three D316 closed-as-lost rows, and two superseded S178 versions. **No document row was left unaccounted for. Nothing halted.**

The live-code half — `verify_live_pins.py` (D321) — was **not** run: it executes on the VPS and the session had no reach to the box. The expected `finance_app.py` drift (box `c66bec2b…` vs Register `86382f62…`) was therefore reconciled from the S184 install record rather than from a live reading, and that limitation is recorded rather than glossed.

### 2. F-107 — Phase 0 is blind to a document that was never listed

The S184 close wrote two **Tier-0** documents — `HANDOFF_RUNBOOK…v118` and `START_HERE_SESSION_185` — into project knowledge **only**. They never reached the repo, never entered `MD5SUMS_ALL.txt`, and never became rows in the manifest.

**So at the S185 open, the two Tier-0 documents Phase 0 is required to read were the two documents Phase 0 could not verify.** They were read on trust, and nothing reported a problem, **because nothing looks for a missing row.** Phase 0 walks the manifest and asks of each row *do these bytes still match?* It never walks the documents in use and asks *is each of you listed?*

This is **F-97's documentary twin**: F-97 was nothing verifying the live-code pins; F-107 is nothing detecting an unlisted document. Both are **absence-blindness**, and absence is what this project has actually lost documents to (F-89, S131). Their hashes were deliberately **not invented** at the S185 close — "compute at freeze" means a real hash still owed, not a placeholder to skip (D172/D188). Both files were **filed to the repo at this close** from the project-knowledge copies, hashed as delivered, and pinned. Those bytes are canonical from here.

### 3. F-108 — findings recorded in one register were never applied to the other

Found while building the owed Fault-Register append. The Fault Register's **§7 index still ended at F-89** and stated *"Next free finding: F-90"* — while **F-90 … F-95 (S181) had never been applied to it at all**, and F-96 … F-99 (S182) existed only as §7.1 full-text blocks with no index rows. The KB Register's own findings index carried all of them, so **nothing was lost** — but the *findings register*, the document whose entire job is to be the register of findings, was four sessions behind and said so nowhere.

**This is the F-45 family recurring** — the fault this very register minted at S149 for exactly this failure, and which it has now committed six more times. The deeper point is the same as F-107's: a version bump that *adds* content is loud; content that was *never added* is silent. RULE: the next-free number and the last index row must agree, and that agreement is checked at every append.

### 4. The fold-in — three sessions of debt cleared in one pass

The owner instructed a full close-out executed end to end. Applied in one pass, in order:

- **KB History Archive v1.30 → v1.33** — §S183, §S184 and §S185 appended **in chronological order, as one contiguous append**. Appending §S185 first would have put the history permanently out of order; an append-only file cannot be repaired by a later append. Prefix proven byte-identical to the `7a673ac6…` pin.
- **Fault_Action_Register v2.18 → v2.19** — F-90 … F-95 (S181, never applied), F-100 … F-104 (S183), F-105 … F-106 (S184), F-107 … F-108 (S185) all landed; §7 index extended from F-89 to F-108. **One version bump, not three**, because the file has exactly one final state and three sequential rewrites of it would be churn, not provenance; the changelog row itemises everything that landed.
- **KB Register v5.5 → v5.6** — the `finance_app.py` pin corrected to `c66bec2b76…`; the two S184 migration markers recorded; D322 into the decisions index; F-105 … F-108 into the findings index; the stale `v5.4` H1 corrected.
- **CANONICAL_MANIFEST rebuilt**, MD5SUMS regenerated, START_HERE promoted to 186, and the whole set pushed to GitHub.

### 5. What this session is really about

Three consecutive sessions deferred this fold-in, and **every one of those deferrals was a reasonable local decision** — S183 protected live financial books from a tail-of-marathon write, S184 went straight to the cash correction the clinic actually needed, S185 opened by asking rather than assuming. Individually defensible; cumulatively, three sessions of drift between the record and reality, in a project that has already had to rebuild canonical documents from cold backups once.

**RULE: the fold-in belongs at the HEAD of a session, never the tail** — and a debt that survives two deferrals should be treated as an incident of process, not as a backlog item.

**D-numbers: none minted. F-107 and F-108 raised. No incident.** Cold kit `KB_S185_close` taken after the fold-in, so it captures the finalised set rather than freezing the debt into a backup.

⭐ **S186 top task: resolve the opening float, then book** (Darpan's drawer count + Dr Bhawna's held cash → float ≈ 0 book nothing, or float ≈ 85–99k ship the gated `S184_C3a`). **Next free: D323 · F-109 · A-D25 · Session 186.** This was Session 185.

## §S186 — 17 Aug 2026 (Session 186, FULL — the longest build session in the project: the cash chain closed by physical count, a phantom bank deposit found in the live books, and six upgrades shipped across five gated installs; D323, D324; F-109 … F-114)

**Six kits, five live installs, four Register versions, six findings.** Two kits went red and both were
caught by their own gates and restored with nothing half-applied. No incident.

### Thread 1 — Phase 0, and the pin chain repaired (F-109 · F-110 · F-111)

Documents GREEN: the repo was cloned anonymously and `md5sum -c MD5SUMS_ALL.txt` returned **63 of 63
OK** (kit `2a0834d9…`; the S185 record's 55/`536961e9…` was that session's *opening* verification, and
55 + 8 S185 outputs = 63 — arithmetic checked, not assumed). The **F-88 cross-check** then matched
**69 of 85** manifest md5 tokens to real file bytes; the other 16 are each legitimately non-document
(live-code pins, Tier-2 digests, the three D316 closed-as-lost rows, two superseded S178 versions, one
kit-ID token). The **F-107 inverse check** ran for the first time: every Tier-0 document about to be
read was confirmed to have a manifest row.

⭐ **Task 0 was answerable from git, and the record was wrong.** `deploy_kits/S184_F1b/finance_app.py.new`
hashes to **`c66bec2b9ea8c11af9c4a4244541e96f`** — its `KIT_ID.txt` and `SUMS.md5` agree, and its
installer refuses to run unless the payload matches. The owner then ran `verify_live_pins.py` on the
box, which read the live file as the same value. The record had carried `c66bec2b76…`, **wrong in
characters 9 and 10** — **F-109**. Runbook v118 and START_HERE_185 record only eight characters; the
ten-character form first appears at the S185 fold-in, in the session that wrote *"never invent a hash
to make a table look complete."*

That same run reported **three DRIFT reds of which two were false** — **F-110**. The pin list on the
box declared `source_md5: ff509b01…` for Register v5.5, but canonical v5.5 is `3cad79e6…` and **no
file in the repo hashes to `ff509b01…`**: it had been generated from an intermediate draft. Canonical
v5.5 already held the values the box was running. The tool had printed its own source md5 every run for
three sessions and nothing compared it to the manifest.

Regenerating exposed **F-111**: the generator could not read the Register that S185 wrote — two
`*(applied marker; no file md5)*` rows halt it outright, and the v5.6 `*(superseded)*` rollback row
would have been pinned as a second live pin for the same path, a red that could never go green. Kit
**`S186_V1a`** shipped both fixes: `gen_live_pins.py` **v1.1** refuses to build from a Register the
manifest does not pin as CURRENT; `verify_live_pins.py` **v1.1** refuses to *run* on a list carrying no
verified-source attestation. Live check after install: **match 40 · drift 0 · missing 0**, verdict
**AMBER by design** because v5.7 was not yet a manifest row. Untracked rose 68 → 76 — because the draft
list had no row under `/root/deploy/`, so for three sessions **the checker could not see its own
directory**.

### Thread 2 — the Sanjeevni cash chain, closed by physical count (D323 · F-112)

The owner supplied a Darpan ⇄ Dr Bhawna custody sheet (1 Apr – 15 Aug; parked ₹11,58,958, returned
₹9,25,516). **Cash parked with Dr Bhawna from 1–7 April totals exactly ₹99,017** — the figure the
legacy finance sheet injected on 8 April with no stated source, and the figure S184 identified as
matching the ≈₹85k shortfall. Two records produced independently, agreeing to the rupee.

The custody model was then established from the owner directly, and none of it had been written down
anywhere before: **Darpan's copy resets on the 1st of each month**, its closing balance sometimes taken
and sometimes carried forward **with no marker recording which**; **Dr Bhawna never banks** — every
Sanjeevni deposit is made by Darpan; the **counter person (Vinay) hands cash direct to Dr Bhawna**,
bypassing the drawer entirely. Darpan's **April copy opened at zero**, verified on the physical copy.

Two proposed mechanisms were tested and both were wrong — that Dr Bhawna banked directly, and that the
sheet's 4 Aug ₹70,000 contradicted the copy. The first died on one sentence from the owner; the second
resolved into ₹38,176 (July closing) + ₹31,824 (August sales) = ₹70,000 exactly.

**F-112 was found in the middle of this.** The Yes Bank statement for 1 Jul – 17 Aug has its last
transaction of any kind on **30 July**: the 13 Aug ₹75,000 deposit **never happened**, yet `S184_C1a`
had booked it as one of "16 verified" credits — on a row S183 had itself marked *"falls after the
statement cutoff … check when booking"*. Truth: **15 deposits, ₹15,70,600**.

**Darpan's drawer was then cleared for the first time, and the arithmetic proved itself.** Copy
₹60,198 − ₹3,926 (15 Aug Vinay → Dr Bhawna) − ₹7,309 (6 Aug Vinay → Dr Bhawna) = **₹48,963**, paid out
as ₹10,000 (advance adjusted against July salary) + ₹20,000 (advance against August salary) + **₹18,963
handed to the owner** = ₹48,963, drawer **empty**. The payout landed to the rupee and thereby proved
two counter-person handovers that no record had connected.

Kit **`S186_C1a`** then applied the close: the phantom deposit removed (backed up in
`s186_removed_movements`), **₹87,205** parked as ONE approved, reasoned `cash_adjustment` on the
earliest medical day (**D323**), the 17 Aug physical count **₹1,75,198** recorded in `cash_count`, and
`negative_cash` recomputed from `v_cash_ledger`. Precheck 4/4, **verify 14/14**, `day_line` byte-unchanged.
Closing **₹42,993 → ₹2,05,198**.

⭐ **The result that matters: open `negative_cash` exceptions 29 → 0.** S184 proved that booking those
away was *mathematically impossible at float 0* and would need roughly **₹85,000**. The float,
established five sessions later by counting the notes, is **₹87,205**. **A derivation from the books
and a count of the cash agreed to within about ₹2,200.** The exceptions did not need to be argued away;
they resolved because the missing money was found. *(The offline rehearsal had predicted 7 residual
negatives and the live store produced 0 — the difference being the seed's even daily distribution
against the real store's lumpiness. The prediction was on record before the install, not after.)*

### Thread 3 — three upgrades, then two more (F-113 · F-114)

**`S186_R1a`** (additive data layer): `bank_statement_line` + `bank_statement_period`,
`counter_person` seeded with the real roles, `cash_custody_event` + `v_cash_custody_balance` carrying
the **taken / carried** month-end marker whose absence hid a float for five months (**D323(d)**), and
the new module `finance_yesbank.py` (selftest 23/23). Verify 10/10; the app's own data proven
byte-identical before and after.

**`S186_R2a`** (the three surfaces): `/finance/workbench` — Entered · Marg · Bank on one screen with
gaps **graded** exact/likely/weak per D315 and never auto-applied; the Yes Bank upload and reconcile
routes; custody capture; and the drawer count where **blank is UNKNOWN and flagged, never zero**.
Live smoke **341/341 on the real store**.

**F-103 is closed, and was proved against the fault that motivated it.** Given the owner's real
statement and the *uncorrected* store, `finance_yesbank.py` flagged exactly the 13 Aug ₹75,000 and
nothing else — 5 matched, 1 caught, zero false positives.

Then the item-wise go-live question exposed **F-113**. Item-wise data stopped at 13 Aug, which is also
where the backfill stopped — an ambiguity that could not be resolved from the data, because "the daily
flow is broken" and "the backfill stopped early" have an identical signature. `ingest_batch` settled it
(`NO BATCH` for 14–15 Aug), and then two successive diagnoses were **both wrong** — a short export, and
a driver abort — each disproved by reading the real export with the live parser and running the live
adapter against it. The truth: the days were **not filed when the backfill ran**, so they were
correctly skipped and reported as *"not filed (refused, harmlessly)"* — a statement true at that
instant and false ever after, with nothing to make it durable.

Re-running the backfill ingested both days (23/23 and 10/10 bills, 147 drug lines), which exercised the
daily path for the first time — and revealed **F-114**: `WALK-IN 0, review 10`. Two records, the parser
warning and the ingest docstring, both described WALK-IN attribution the code did not perform. The
queue had grown to 2,072 rows, none of them answerable.

**`S186_I1a`** fixed it (a clean anonymous line from a structured export → WALK-IN; low confidence and
anonymous OCR still → review; reversible by setting) and shipped what the owner asked for in the same
kit: **Marg exports upload through the portal**, parsed, surveyed, ingested and **deleted inside the
same request** — so no export need ever live on the box again. It keeps all three of the CLI driver's
guards and adds the one it lacked: a NOT-FILED skip now writes a `data_flag` (**F-113's remedy**).
Live smoke **351/351**.

**`S186_W1a`** then cleared F-104: review queue **2,072 → 0**, days flagged **120 → 4**. Its first run
went **RED and restored** — the migration had guarded `amount_p > 0` and silently dropped all **116
credit notes**, which `sale_item_review` stores as negatives while `sale_item` carries returns as a
positive magnitude with service `pharmacy_return` (D314). The gate caught it because the outcome did
not match the projection it had printed sixty seconds earlier. Corrected to convert by type, the second
run verified **14/14** and matched the projection exactly.

**The four days that survived are the point:** 3 May (zero lines — F-113 biting, visibly), 9 May
(−₹665), 2 Jun (−₹690) and **12 Jun (OVER by ₹8,487)** — live money that had been invisible inside 120
identical shouts since June.

### D324, and how this session was worked

**D324** was adopted mid-session at the owner's instruction: kits are **written directly into the local
repo** over the device bridge, each carrying a `PUSH.bat`, so publishing is one pasted path. It removed
the zip round-trip, the folder-naming trap, the xcopy step and the `__pycache__` residue that
`push_kit.bat` v4 had caught earlier the same day — every one of which had already cost a round trip.

**Both builds on live code were made on bytes verified from the box**, recovered hash-verified from the
`S184_F1b` kit payload in git. The repo's own `finance/finance_app.py` is two builds stale and would
have deleted the clinic module. **That is F-97 avoided in practice rather than in principle**, and it is
what the morning's pin work bought.

**Three times an assistant test asserted state rather than behaviour and had to be repaired before
shipping** — twice in R2a and once in I1a (the suite rewrites the marg column map mid-run, so both
"assume the shipped map" and "read the current map" made the test a test of ordering; it now owns its
map and restores it). **F-106, caught in our own work rather than shipped**, which is the argument for
running the F-87 differential rather than trusting a green number.

**Register versions this session: v5.6 → v5.7 → v5.8 → v5.9 → v5.10 → v5.11.** Five bumps, each
recording live pins as they moved rather than at the close — deliberately, because unrecorded live pins
are the F-97 condition and this session was spent digging out of it.

**Owed and named, not silently deferred:** Darpan's ₹30,000 (blocked on scans, and the ₹10,000's
category is still an open question that could double-count in his Ledger); 14/15 Aug still `draft`;
the May export re-upload for 3 May; **12 June's ₹8,487**; the Hindi labels and the entry-screen custody
block; the CLI driver's NOT-FILED flag and its `attributed ? · review ?` display bug; the ₹70,000 of
Darpan advances resting on an unverified claim in a SQL comment.

**D-numbers: D323, D324 minted. F-109 … F-114 raised, all six appended to the Fault Register the same
session — the first close since S181 leaving no owed append. No incident.**

⭐ **S187 top task: owner's choice — the item-wise go-live decision, the 12 June ₹8,487, or the F-107/
F-108 structural checks.** **Next free: D325 · F-115 · A-D25 · Session 187.** This was Session 186.

## §S186-POST — 17 Aug 2026 (Session 186 POST-CLOSE — the close was published, the first pin run went RED, and chasing that one RED opened six more faults in the verification chain itself; F-115 … F-121; no live code touched)

**The shape of it.** S186 closed clean by every measure available at the time: six canonical files built,
cross-verified, hashed and filed. Then came publishing, and publishing is where it came apart — not
because anything was lost, but because **nothing in the chain that proves the record was itself being
proved.** Seven findings in one evening, all in the machinery: the publish step, the manifest, the
checksum file, the pin list, and a gate that had learned to cry wolf.

**1 — the publish that published nothing.** The owner pasted `PUSH.bat` as instructed. It pushed and
`HEAD` matched `origin/main`. But `PUSH.bat` stages only its own kit folder, and `KB_canon_all` is not a
kit — so the last published commit was `S186_W1a`, from the middle of the session, while the entire
close-out sat uncommitted on disk. **A true green about the wrong question** (F-115). Fixed with
`PUBLISH_CLOSE.bat`, which stages the whole tree and ends by comparing the local commit hash to the
remote one. Its own gate then refused to commit twice on the owner's screen — first over `.pyc` residue in two
S182 kits, then again after that residue was moved into a folder the narrowed scan still covered
(**F-121**). Both versions asked whether anything ignored sat *near* the staged files; proximity was
never the fault. **v3** asks the only question that matters — *does git track every name the payload's
own checksum list declares?* — and was rehearsed against a real refusal before shipping.

**2 — the RED.** With the close finally published, `verify_live_pins.py` ran against it and returned
**RED, 1 drift, 41 match**. `finance_workbench.html`: record `45cb85b3…`, box `18c71e63…`. The workbench
had shipped twice at S186 — in `S186_R2a`, then a newer build inside `S186_I1a` — and the box carried the
newer one, correctly. At the close the duplicate-path guard (built that same morning for F-111) fired
because one path was pinned twice; the conflict was resolved by deleting a row, and the row deleted was
the current one. **A guard can prove two pins disagree; it cannot say which is true — and that question
was settled from the documents instead of from the box, the exact inverse of D321(d)** (F-118).

This is worth marking. **It is the first RED in the project caused by the record rather than the box**,
and therefore the first demonstration that the pin checker works in the direction nobody designed it
for. Had a full-file replacement later been built on the stale pin, it would have overwritten the newer
workbench with the older — which is F-97, the fault the entire pin system exists to prevent. Nothing on
the box was ever wrong; nothing on the box was touched.

**3 — what the RED led to.** Verifying the pin meant verifying the chain above it, and the chain had
three more holes. The manifest's own Phase-0 footer pinned this Register at `d5ec45a5…` — a token that,
against a full md5 index of all 936 files in the repo (hashed as stored and with line endings normalised
both ways), **matches nothing anywhere**, and appears in exactly one place: that footer (F-116). The pin
list attested `manifest_md5: 04eff42c…`, which also exists nowhere; the checker printed *"VERIFIED
against the manifest … (md5 04eff42c…)"* while never comparing that md5 to a file — F-110 one level up,
inside the tool built at this same session to close F-110 (F-117). And `MD5SUMS_ALL.txt` carried a row
for `KB_Register_v5_10_S186.md`, an intermediate bump that is not on disk, so **the single command
`START_HERE_187` gives Phase 0 exits non-zero: 70 OK, one missing** (F-119). The door to the next
session was locked, and nothing said so, because nobody runs Phase 0 at the end of the session that
wrote it. Alongside it, the folder shipped **three** competing checksum files, two of them stale and
both capable of convicting a correct file (F-120).

**4 — what was done.** Record-only; the box was not touched and no live code changed. The workbench pin
was corrected **from the box**. The manifest was rebuilt from real bytes with the phantom footer gone.
`MD5SUMS_ALL.txt` was rebuilt with an inverse check — every file in the folder is now either listed or
excluded with a stated reason — and made the folder's single checksum authority. The pin list was
regenerated against the corrected manifest as kit `S186_V1c`. Everything retired was **moved to
`deploy_kits/_attic_S186/`, not deleted**: two stale checksum files, a superseded commit note, three
`_superseded_S182` documents, `.pyc` residue and a stray `.tsv`. Every byte survives, in the tree and in
history.

**What this session is really about.** S186 proper was about money — five months of Sanjeevni cash
closed by physical count. S186-POST is about something narrower and, for the long run, more useful:
**the difference between a record that is consistent and a record that is true.** Six of these seven
faults were found only because one RED was taken seriously instead of explained away. The seventh was
found while fixing the first. Every one of them was invisible to a check that passed.

⭐ **Owed at S187:** `verify_live_pins.py` must hash the manifest it names and refuse on a mismatch —
three lines, and it prevents the finding that produced F-117. **Next free: D325 · F-122 · A-D25 ·
Session 187.** This was Session 186, post-close.

## §S187 — 17–18 Aug 2026 (Session 187, FULL — EIGHT kits live in one session: the F-117/F-122 structural fix, B5 reception push, Daily Flow v2 stage D1, the portal tile chain, and the owner's Sanjeevni Hub under a new Clinic Design Language; D325–D328; F-122 … F-126)

**The session in one line: the record-keeping machinery learned to prove its own claims, reception
got a one-click sender, every seat's portal tile started speaking, and everything Sanjeevni collapsed
into one designed Hub wearing the owner's real logo — eight kits, every one landing exactly to its
stated projection, two design contracts signed, and the publish step reduced to one desktop icon.**

### Phase 0, and the morning's three record faults

Documents verified against git bytes per the standing procedure. The live-pin run read 42/0/0. But
the open itself surfaced **three faults in the S186 post-close record, found before any work began**
(recorded here, corrected at this close, none minted — each is an instance of an existing family):
(1) the manifest carried **five "(pre-…)" rows still labelled CURRENT** beside their successors —
two Registers, two runbooks, two START_HEREs among them — so a strict reader finds two CURRENT
Registers (the V1a checker selftest deliberately covers exactly this case and refuses rather than
guesses); (2) **`START_HERE_SESSION_187` contradicted itself** — its head said Register v5.12 ·
Fault Register v2.21, its "Where the truth lives" said v5.11 · v2.20 · Archive v1.34 · Runbook v120,
and its next-free line said F-115 against a Fault Register standing at F-121; (3) **Runbook v121's
end-marker read "END OF HANDOFF RUNBOOK v120"** — the F-45/F-116 family in the runbook's own footer.
All three are the same lesson F-116 taught: *a document's footer and cross-references are claims
about itself, checked like any other.*

### Thread 1 — the F-117 fix became the F-122 discovery (kit `S187_V1a`)

Runbook v121 item 0 said the fix was ~3 lines: hash the manifest the pin list names, compare, refuse.
**Executing it proved the fault was one level deeper and the fix as written was unbuildable.** The
V1c list's `manifest_md5: 78881ddd…` was checked against an md5 index of the full 157-commit history
— all 24 committed manifest states, both line-ending normalisations — and matches **nothing**; V1b's
`04eff42c…` likewise. **Every `--manifest` generation had minted a phantom**, because the manifest's
self-row is "recomputed last, each EOS": the whole-file hash at generation time describes a transient
PC-side state edited again before the push. A true hash of a state that no longer exists is
indistinguishable from an invented one. **F-122 raised.**

The durable fix uses what the box already holds: `/root/deploy/repo`, the D317 chain's clone.
`verify_live_pins.py` **v1.2** finds the file in `repo/deploy_kits/KB_canon_all/` hashing to the pin
list's `source_md5` (by hash, not filename — D188), parses the manifest beside it, and confirms its
CURRENT `KB_Register` row pins that same hash — **VERIFIED is printed only after both comparisons
pass on this machine**; anything else states its reason and caps at AMBER. Selftest 43/43.
`gen_live_pins.py` **v1.2** writes the stable `manifest_current_register_pin` and never the
whole-file md5. Selftest 22/22. Proven against the real repo clone before shipping; F-110's draft
hash `ff509b01…` correctly refuses. Installed live: **42 match · 0 drift · 0 missing**, AMBER by
design pending this close. **F-123 found en route** — the repo's second, S177-stale
`canonical-docs/CANONICAL_MANIFEST.md`, still calling itself canonical; retired at this close.
The first publish of V1a also produced **F-124** live: a stale `.git/HEAD.lock` blocked the commit,
`PUSH.bat` v1's `|| echo` swallowed the fatal, and "pushed" was printed with origin unchanged —
fixed in v2 the same hour (lock refusal · empty-vs-failed decided before committing · origin HEAD
verified after pushing).

### Thread 2 — B5: reception pushes the Marg report; the checker alone applies (kit `S187_M1a`, D325)

The owner chose "Fix F-117 + B5 together." The S186 upload lived on the checker-only workbench — the
opposite of the S183 segregation-of-duty ruling. Built after reading the S180 Marg recon docs at the
owner's direction, which corrected two design assumptions: Marg writes the report to the FIXED path
`users\<id>\report\REPORT_1.XLS`, overwritten every run; and Marg writes live, so the sender copies
first and never writes inside `D:\MARGERP`. Owner's three rulings: **double-click sender** (no silent
daemon — F-113), **survey-first with the checker's apply**, **dependency-free batch** (certutil +
Windows curl). The push stages the parsed per-day line/item CSVs in the new `marg_push_staging`
table and **the file dies inside the request**; apply (`require("checker")`) replays the staged CSVs
through the same guarded ingest; applied payloads are pruned. `FINANCE_MARG_TOKEN` is a **separate,
scoped, stage-only secret** — one path, no identity, no reads, no apply, 503 fail-closed when absent.
Selftest 359/369 offline, +24 over baseline, zero failures added (F-87 differential); three F-106-family
bugs caught in our own tests before shipping. **D325 minted.**

**The medical-PC setup was its own saga, and two token lessons came out of it.** The `.bat.txt`
extension trap; a `ren` typo; the config line losing its `TOKEN=` prefix twice in Notepad (settled by
a PowerShell in-place replace and a `findstr` proof of exactly one placeholder line). Worse: the
token was once typed into the repo-kit copy on the wrong PC (caught by masked diff, reverted by
HEAD-overwrite before any push — a public-repo leak averted), and **once pasted into chat by the
owner — declared burned on the spot and rotated on the VPS** (`openssl rand -hex 16`, unit updated,
service restarted). Standing rule restated: **a secret pasted into chat is burned, and repo-write
credentials never transit chat at all.** By evening the first genuine push from reception was
ACCEPTED-FOR-REVIEW and staged — proven end to end. The sender later got its desktop dressing:
`SendToClinic.ico` + `MAKE_DESKTOP_ICON.bat` (shortcut "SEND TO CLINIC"), committed into the M1a kit
folder; an old M1a re-deploy attempt was correctly REFUSED by its currency gate — the D317 chain
protecting against an unneeded install.

### Thread 3 — Daily Flow v2 designed, contracted, and stage D1 shipped (kit `S187_D1a`, D326)

The owner's directive — Darpan sees ICICI UPI + Marg after saving; the owner's page expands to bill
level; salary edits with instalment logic; "think of all other such features which will reduce
friction … and then build" — was taken as a full design first (`S187_Daily_Flow_v2_Target_Design.md`,
the S181 C1 pattern), then contracted by three owner rulings: **allow-but-badge** post-reveal edits
(`edited_after_reveal`); **salary bridges to the Staff Ledger, never replicated** (gated on the
backlog-6 ₹70,000 verification); **Yes Bank statements arrive in the owner's PERSONAL Gmail** (shapes
stage D5). **D326 minted** — one canonical Day Page, staged D1→D5. D1 shipped: `/finance/api/day/<date>/full`
(the whole day in one checker-only call: declared · Marg bills→drug lines · ICICI settled-vs-declared
· Yes Bank · flags · exceptions · review · attribution), `/finance/api/approvals` (every strip count
carries its rows), `/finance/approvals` (expand-in-place, approve via the existing guarded route).
Read-only except the reused approve; no schema change; 371/381 offline, +12, zero failures added.
Installed 387/387.

**The owner then stress-tested the design with edge-case questions** — export not done? same file
re-exported? multi-day file? incomplete data? unreadable? what happens to Darpan's entry when no
export exists? what authorities per seat? — and the answers are in the design docs: dup-by-file_md5
→ ALREADY-RECEIVED; NOT-FILED flags (F-113's remedy) surface on the Hub; push-survey warnings are
displayed; the seat matrix is explicit. **The returns system was then specified in full by the owner**
(reception books the return: related-sales lookup → drugs+quantities against original lines → reason
dropdown → live verification against the initial sale → eligibility legends: expired = INELIGIBLE ·
>2 months = FLAGGED · sold ≥1 month ago AND <1 month expiry left = DISQUALIFIED → print slip →
Darpan books the CN in Marg → the CN reconciles against the logged return), plus the 360-degree
lookup, refill-skipper intelligence, orthotics purchase-side via **the asset app's scanned purchase
bills** (owner's own answer, better than both offered options), and remote access (Tailscale +
RustDesk approved). All captured as the signed addendum
(`S187_Daily_Flow_v2_Design_Addendum_Returns_360.md`); **build PAUSED by the owner — the S188 open
starts on this contract.** His later ideation — per-user contextual instructions populating the
portals — was parked as stage **D6** in the same addendum.

### Thread 4 — the portal tile chain (kits `S187_P1a` → `P1b` → `P2a`; F-125)

The owner uploaded his real portal + review pages: the review page had **no navigation at all**, so
the Sanjeevni tile landed on an island. P1a: the tile lands on `/finance/approvals`, carries live
pending counts (`data-sanjeevni-counts` ← the new checker-only `/finance/api/tile-summary`,
fail-soft), and the approvals page gains a section-nav; portal gate 18/18 on served HTML with masks
proven. **Its install went RED — 388/389 — and the one failure was ours: F-125**, the M1a-era
"exactly one pending row" check broken by the morning's first real reception push. The gate restored
byte-perfect; P1b scoped the check to its own bytes and re-rehearsed against the exact failing
condition: 389/389 live. Then the owner: *"ideate and execute any similar setup done for other
users"* — P2a extended the pattern to **every seat**: Darpan's Daily Sale tile gains his own to-do
line (`/finance/api/my-day-summary`, maker-seated only, **D322-aware** — Sundays and holidays are
not owed), and the clinic tiles gain maker/checker counts server-side inside the existing
`tile-meta` subtitle (zero portal change for clinic). A doubled `</tbody>` in the live approvals
page — found in the owner's own uploaded HTML — was fixed in passing. 392/392 live; portal gate 22/22.

### Thread 5 — the Sanjeevni Hub, then the design pass, then the real logo (kits `S187_H1a` → `H1b` → `H1c`)

The owner could not find the Marg upload ("I CANT LOACTE THE MARG UPLOAD… THIS PAGE SHD BECOME THE
SOLE PLACE FOR ANY SANJEEVNI INFO AND WORK FOR ME"). **H1a rebuilt the approvals page as the Hub**:
Marg (upload + pushed-Apply moved in from the workbench, missing-export list, NOT-FILED flags,
push-survey warnings now displayed) · Approvals · Cash register (30/60/90-day ledger, cash-in-hand
headline, every date drills into the full Day Page) · Custody (**the money with Dr Bhawna**) ·
Entered·Marg·Bank month grid · Orthotics (NEW `/finance/api/orthotics` — owner-editable keyword
vocabulary as a setting, 90-day per-item rollup; **qty deliberately not summed** — `qty_raw` is
Marg's strips:loose text and a numeric sum would be a guess wearing a number) · Exceptions. One
shared Day-Page renderer serves every card; the only new server surface is orthotics. 400/400 live —
though the installer's goodbye then died on a quoting slip (**F-126**; all real work already done;
standing rule: `bash -n` the WHOLE installer, applied to H1b/H1c).

Then the design ruling: "READIBILITY IS POOR … DO A WONDERFUL PAGE DESIGN … MAKE DESIGN ELEMENT
DEFAULT THROUGHOUT OUR WORKS." Built by the dataviz skill's method: **`Clinic_Design_Language_v1.md`
— THE DEFAULT from here** — warm paper surfaces, 15px/1.6 type with uppercase kickers, tabular
right-aligned numerals with `.00` stripped, sticky branded header + always-visible section tabs,
46px floating back-to-top, bounded scrolling tables with sticky heads and zebra, stat tiles, folded
`<details>` help, status always icon+label never color alone. H1b shipped it page-only (every id and
API path byte-preserved, selftest differential clean) — **published but never installed, retired
unlived**, because the owner's two corrections arrived first: the logo had to be his REAL one, and
*"Advanced Orthopaedic Surgery Centre" is the tagline, not the clinic name*. The logo was found in
his Canva (`dr manoj logo`, design `DAHKiFFICC0`), export blocked by the sandbox proxy, saved by the
owner to `D:\dr-manoj-git\logo\`, staged over the bridge, the diamond mark auto-cropped by color
mask, embedded as a data-URI. **H1c: logo mark · "Dr. Manoj Agarwal Clinic" (owner's exact wording)
· tagline line "Advanced Orthopaedic Surgery Centre · Sanjeevni Hub"** — dual currency gate (accepts
the live H1a page or an installed H1b), installed at the session's very end: page placed, pins
43/0/0 AMBER pending this close, the branded Hub live.

### Thread 6 — publishing collapsed to one icon (D328)

The owner: *"i feel u can easily do this part, and make it default menthod."* The honest boundary was
stated and stands: the device bridge has no network (`git commit` works there, `git push` cannot),
the cloud holds no credentials, and **repo-write credentials never transit chat** — repo-write is the
D317 chain's trust anchor (anyone holding it can plant a kit `vps_deploy.sh` would install); the
day's own burned-token episode is the case study. Full publish autonomy is an explicit S188 decision
(a scoped deploy key, risks written down) if the owner wants it. What shipped instead:
**`PUBLISH_ALL.bat`** at the repo root — one desktop icon that publishes EVERYTHING pending with
every gate kept (HEAD.lock refusal · F-100 gitignore-drop gate across the tree · commit failure is
real, F-124 · push · **origin HEAD verified before success is printed**). Its first field run
published H1c and the sender dressing in one verified push. **D328 minted: PUBLISH_ALL.bat is the
default publish method; per-kit PUSH.bat files remain as fallbacks; the last click stays the
owner's until a deploy-key decision says otherwise.**

### Also this session

"Can I do the PC work from my Galaxy Fold Claude app also" — yes for everything cloud/VPS-side; the
device bridge needs the desktop app. Project knowledge hit its ~2M-token ceiling mid-close;
superseded same-session Register intermediates were deleted from PK (bytes preserved in repo kits —
nothing lost, and the manifest keeps their pins).

### Decisions minted this session — FULL TEXT

**D325 — B5: reception produces the sales record; the checker alone moves it into the books; the
file never rests anywhere.** (a) The medical PC's sender (`SEND_TO_CLINIC.bat`, dependency-free:
certutil + Windows curl) pushes the day's BILL WISE report with `FINANCE_MARG_TOKEN` — a scoped,
stage-only secret: one path, no identity, no reads, no apply, fail-closed 503 when absent, separate
from the GAS cron token so either rotates alone. (b) The push STAGES the parsed per-day line/item
CSVs (`marg_push_staging`, lazily created, DDL authoritative in code) and deletes the file inside
the same request — survey-first was the owner's ruling, and staging the replayable CSVs is what
makes it possible without a PHI spool; the rejected alternative (a spool folder) would have
reintroduced what S186 removed. (c) Apply is `require("checker")` only, one click, replaying the
staged CSVs through the SAME guarded ingest as the direct upload (expect-mismatch aborts, zero-line
load aborts, still-unfiled days reported, the F-113 flag written at push time); applied payloads are
pruned. (d) The sender is a double-click, not a daemon (F-113); it keeps dated copies because Marg
overwrites `REPORT_1.XLS` every run, tracks sent-hashes so a repeat click is harmless
(ALREADY-RECEIVED), never writes inside `D:\MARGERP`, and logs every send to a file that outlives
the run. Grounded in the S180 recon + feasibility surveys, read before build at the owner's
direction. *(Spent at kit `S187_M1a`.)*

**D326 — Daily Flow v2 is staged on ONE canonical Day Page, and three owner rulings shape it.** The
design doc `S187_Daily_Flow_v2_Target_Design.md` (+ the returns/360 addendum) is the contract.
(a) One expandable day view every surface links into — same data, same level; role decides scope,
not the page. (b) Save-then-see with allow-but-badge: Darpan's declaration stays an independent
record because the mirror reveals bank/Marg only after his save; a post-reveal edit is permitted but
stamped `edited_after_reveal` and badged to the checker (F-105's lesson: the app keeps the record
honest, it does not become an obstacle). (c) Salary bridges to the Staff Ledger, never replicated —
one authority per rupee (D202/D258); finance shows the Ledger's live view beside each advance and
posts through it; gated on the backlog-6 verification of the ₹70,000 claim. (d) Yes Bank statements
live in the owner's personal Gmail — the auto-feed lands at stage D5 by forward-rule into clinic
Gmail or a scoped personal-account script, decided at D5. Stages: D1 Day Page + approvals (SHIPPED,
kit `S187_D1a`) · D2 the maker mirror · D-R returns at reception (specified in the addendum) · D3
the Ledger bridge (gated) · D4 home/procedure medicine · D5 feeds/nudges/month-pack · D6 contextual
per-user instructions (parked). *(Spent at kit `S187_D1a` + the two signed design docs.)*

**D327 — reception gets identity: the scoped `counter` role.** Returns, orthotics and 360 lookup
require reception to have a screen with identity — the stage-only sender token cannot carry a UI. A
portal login (e.g. user `vinay`) on the medical unit with role `counter`: can look up patients, log
returns, view orthotics; CANNOT see cash position, day totals, approvals, or anything checker-side;
every action attributed by name. Extends the S179 role model deliberately (maker/checker/counter);
the S182 grant-only tile pattern applies. Owner ruled at the addendum's §8; builds with stage D-R at
S188. *(Minted at this close from the signed addendum.)*

**D328 — publishing is ONE whole-repo icon with every gate, and publish autonomy has an explicit
boundary.** `PUBLISH_ALL.bat` (repo root, desktop shortcut "PUBLISH") is THE default publish method:
`git add -A` the whole tree · refuse on `.git\HEAD.lock` (F-124) · refuse if `.gitignore` silently
drops a file under `deploy_kits/`, `logo/`, or the canon (F-100, scoped so deliberate ignores do not
cry wolf — F-121) · a failed commit is a failure, decided before committing · success is printed
only after origin HEAD equals local HEAD. Per-kit `PUSH.bat` files remain as fallbacks. **The
boundary: the assistant prepares everything; the last click stays the owner's.** The device bridge
has no network, the cloud holds no repo credentials, and repo-write credentials never transit chat —
repo-write is the D317 chain's trust anchor, and a token that transits chat is burned (proven twice
this session). Full publish autonomy (a scoped deploy key) is an explicit future owner decision with
the risks written down, not a default anyone drifts into. *(Minted at this close; the tool proved
itself on its first field run.)*

### Findings

**F-122** (phantom manifest attestation — closed structurally, v1.2 tools) · **F-123** (twin
manifests — retired at this close) · **F-124** (the publisher swallowed a fatal — v2 same hour) ·
**F-125** (state-asserting test broken by the first real push — P1b, the fourth F-106-family
firing) · **F-126** (installer tail syntax error — the whole-file `bash -n` rule). All five appended
to Fault_Action_Register **v2.22** at this close — **the second consecutive close with no owed
append.** Recorded unminted: the morning's three record faults (five duplicate-CURRENT manifest
rows · START_HERE 187's self-contradiction · the v120 footer on Runbook v121), all corrected in this
close's rebuilt documents; and the Register v5.21 end-marker still reading "v5.11 (S186)", corrected
at v5.22.

### Where things stand at the close

**Live:** `finance_app.py` `db4373a5671dc90d384166a5771e098b` (400/400) · `finance_approvals.html`
`028255054662924713e03362c3976b05` (the branded Hub) · `portal.py` `bd4ed0a3b89659676e7e193998eeb1a9`
(every seat's tile speaking) · `finance_workbench.html` `420f82c2846bc49d0d12ab5040d8c542` ·
checker/generator v1.2 · reception's sender live with icon · `PUBLISH_ALL.bat` proven. **First
pending reception push awaiting the owner's Apply on the Hub.** Cash in hand still reads ₹2,05,198
pending Darpan's ₹30,000; 14/15 Aug still draft. **S188 opens on the signed Daily Flow v2 contract:
D-R returns → D2 mirror → 360 wiring → orthotics (asset-app purchase feed) → D5 feeds → D6, plus the
gated §4a Staff Ledger check, the `counter` role build, and the Tailscale+RustDesk rollout.**
**Next free: D329 · F-127 · A-D25 · Session 188.** This was Session 187.

---

## §S188 — 18 Aug 2026 (Session 188, FULL — Daily Flow v2 stage D2 LIVE in two kits: Darpan's mirror, save-then-see enforced server-side, and the badge that reaches the checker unaided; no decision minted; F-127 … F-131)

**Two kits, both green to a projection written down before the box was touched** — `S188_D2a`
400/400 → 453/453, `S188_D2b` 453/453 → 464/464. No incident. **Five findings**, all appended to
Fault_Action_Register **v2.23** and **v2.24** the same session — the third consecutive close with no
owed append. **No new decision:** everything built here is the execution of **D326**, and inventing a
D-number for an implementation detail would cheapen the index.

### Phase 0

Green, and quiet. The repo cloned anonymously, `md5sum -c MD5SUMS_ALL.txt` → **85 of 85 OK, exit 0,
zero WARNING lines** (F-119's inverse satisfied). The **F-88 cross-check** then hashed all **1,033
files** in the clone against the manifest's 114 md5 tokens: **102 matched real bytes**, and each of
the remaining twelve was legitimately non-document — three D316 closed-as-lost rows, four Tier-2
artefact digests, three live VPS code pins quoted in the §S179 narrative, one kit ID, and two
superseded documents not carried in the canon folder. The **F-107 inverse check** confirmed all four
Tier-0 documents carried manifest rows and matched exactly; the **F-123 check** found exactly one
file named `CANONICAL_MANIFEST.md`. `verify_live_pins.py` was not run — it executes on the box and
the session had no reach to it; the owner ran it implicitly through each kit's currency gate
instead, which read the expected pins both times.

**One observation, not a halt:** three superseded intermediates sit in `KB_canon_all` with no
manifest row — `Fault_Action_Register_v2_20.md`, `KB_History_Archive_v1_34_S186.md`,
`KB_Register_v5_11_S186.md`. Harmless (all superseded), but the F-107 shape in reverse: bytes in the
canon folder the manifest pass does not know about.

### The build — stage D2, on the signed contract

The owner chose **D2 (Darpan's mirror)** out of the addendum's proposed order, and chose to ship it
as **one kit**: the mirror and the Design Language rebuild together, so Darpan learns one new page
rather than two.

**Survey first.** The design docs were read, then the live code — and the repo's `finance/` tree
turned out to be **seven builds stale** (`finance_app.py` there is the S180 build; `portal.py`
pre-S182; `finance_approvals.html` and `finance_workbench.html` absent entirely). The live bytes
exist only inside the deploy kits. Every live pin was recovered by **hash-hunt, not by filename**
(D188) and the build was made on those bytes. This is **F-97 part 2** in the flesh.

Reading the maker's existing surfaces to design his scoped view is what turned up **F-127**.

**`S188_D2a`** — `GET /finance/api/day/<date>/mirror`, the maker's scoped reveal: his declared
figures · ICICI settled UPI with a match-or-gap verdict · the Marg verdict in **three** states
(`applied` / `staged_not_applied` / `absent`, because "no comparison" has two causes needing two
different people to act) · which scans are attached · his opening carry · the days he still owes.
**Save-then-see is enforced on the server** — an unsaved day answers `409 not_saved` — so the
sequencing that keeps his declaration and the Marg export independent is a property of the system
rather than a promise the page makes to itself. A lazily-created `day_mirror_reveal` row records the
reveal with a **fingerprint of the money shown**, so tapping Scan (which silently saves a draft) is
correctly *not* an edit; a later save that moves the money writes an `EDITED_AFTER_REVEAL`
`data_flag`. **The elegant part: the checker's `/full` already renders `data_flag` rows, so the badge
reaches the approval queue with no checker-side code change at all.** The entry page was rebuilt
under **Clinic Design Language v1** — which names Darpan's D2 mirror as *born in v1* — carrying the
H1c Canva logo, in-page tabs, tabular numerals, `<details class="help">` slots (**where D6's
contextual instructions will land with no further page surgery**), empty `.hindi` slots and the 46px
back-to-top. The File button became gated on the three scans **or** a stated reason.

**F-127 closed in the same kit.** The timing question the owner settled — *"Darpan files next
morning only after 10 am"* — dissolved the Marg-timing problem entirely: ICICI pushes at 09:30 daily,
so the bank half fires every morning, and the Marg half fires as soon as the owner has pressed
**Apply**. That coupling was named explicitly rather than discovered later.

**`S188_D2b`** — **F-129**, caught *before any live use*, while writing the owner's own first-look
instructions: the safe advice would have been "open an approved day, not a draft", and the fact that
the advice needed a caveat was the signal. The reveal now arms only on a maker's look.

### Findings

**F-127** — a role gate on the surface is not a role gate on the data; `_gate` protects the unit
boundary and nothing protected the role boundary inside it, so Darpan's page pulled the whole medical
cash position on every load. **F-128** — found only because F-127's fix *is* a role refusal and would
not go green: the offline seed granted the smoke user a checker role the box does not have, so
**eight** "a maker cannot X" assertions had been passing by accident; correcting one line moved the
offline baseline **375 → 398**. **F-129** — a marker recorded that something was shown, but not to
whom. **F-130** (at the close) — a page-only kit that preserves every id is invisible to an id-based
test, so the *design* is the one thing 464 green checks cannot see; exposed when a saved copy of the
Hub could not be told from the live one by any gate we own, only by `md5sum` on the box (which
matched — the record was right). **F-131** (at the close) — `git status` is not read-only; it left an
`index.lock` the bridge could not delete, which blocked the owner's publish, and `.git/` held
**fourteen** such locks dated across S185–S188, every one a silent workaround and **not one
recorded**.

**Two things behaved exactly as designed and are worth the record.** `PUBLISH_ALL.bat` met the stale
lock, printed `git add FAILED` and committed nothing — **F-124's** fix earning its keep. And every
one of the four gates that could have caught a bad install did: the currency gate read the expected
pins twice, the differential smoke refused to swap on any new failure, and a rehearsed red restored
both files byte-perfect on a throwaway box before either kit was offered.

### Where things stand at the close

**Live:** `finance_app.py` `3a7086f851720dd161bc43c3c1fd45dd` · `finance_ui/finance_entry.html`
`2c23b461bdae5a4ed6a4c4ed4708b4f9` · smoke **464/464** · `finance_approvals.html`
`028255054662924713e03362c3976b05` (H1c, **verified on the box this session**) · `portal.py` and
`finance_workbench.html` unchanged. Cash in hand still reads ₹2,05,198 pending Darpan's ₹30,000;
14 and 15 Aug still draft and now safely openable; 16 Aug (Sunday) and **17 Aug unfiled**, with a
pushed Marg report for 17 Aug staged and awaiting the owner's Apply — which is now also what arms
Darpan's morning cross-check.

**The one thing owed to a person rather than a file:** Darpan has not yet been walked through
**Save → the check → File**. The kit changes his habit and the runbook said so before it shipped.

**Next free: D329 · F-132 · A-D25 · Session 189.** This was Session 188.

---

## §S188-POST — 18 Aug 2026 (Session 188 POST-CLOSE — the close was published, the owner opened Darpan's page as Darpan, and one look reopened the session; F-132, F-133; kit `S188_D2c` live)

**The S188 close was written, verified, published and reported.** The owner then logged into
**Darpan's own account from an incognito window on his phone**, looked at the page, and asked one
question: *"it is showing total amount also."*

**That one look found what five layers of gates could not** — because every gate was checking that
the code did what the record said, and the record itself was wrong.

### F-132 — the claim recorded as fact hours earlier

Closing F-127 that morning, three routes were gated. For `/finance/api/day/<date>` the kit, the
Register and the message to the owner all read: *"payload unchanged, because it was already
correctly scoped."* **Nobody had looked.**

`opening_p` comes from `v_cash_ledger`, whose window is `ROWS BETWEEN UNBOUNDED PRECEDING AND 1
PRECEDING` — a running total of **every day since the books began**. The maker's page labelled it
*"Opening cash · carried from the last filed day"* at **24px bold**, with "Closing cash" beneath at
**30px**. The whole unit cash position, twice, in the largest type on the screen.

**And it was not true of him.** Most of that balance is parked with Dr Bhawna (D323); ~₹87,205 is a
pre-April adjustment (S186). "Carried forward" invited him to believe his drawer held two lakh.
**That half predates F-127 and had been live since S179.**

It leaked through **three** doors — the GET, the **save response**, and the D2 mirror built the same
day. Fixing the first surfaced the second; fixing the second surfaced the third.

### F-133 — the survey was the finding

The owner then ruled on what Darpan *should* see: money parked with him and Dr Bhawna, and days
since the last bank deposit — the parked figure as **a total line that opens to the two names**,
and **not counting the previous financial year**.

Before building it, the box was surveyed:

```
cash_movement, all time, medical:  bank/out  n=15  Rs 15,70,600.00   (nothing else)
last bank deposit : 2026-07-30, Rs 85,000   -> 19 days ago (threshold 7)
cash_custody_event: 0
```

**Not one handover to either doctor has ever been recorded.** Built unsurveyed, the page would have
shown a confident `Dr Manoj ₹0 · Dr Bhawna ₹0` while roughly two lakh sat with one of them — a
worse falsehood than the one the same kit was removing.

**It also explains the ₹2,05,198.** S184/S186 recorded *"cash parked with Dr Bhawna"* as exception
text and `negative_cash` labels, never as cash movements. The money left the drawer; in the books it
never did. The entry — *"Cash out / cash back — Bank, Dr Manoj, Dr Bhawna"* — has been on that page
since S179; fifteen bank deposits went in and not one handover did. **The gap is practice, not
code**, which is why no kit closes it.

### `S188_D2c` — live, 464/464 → 478/478

Removed: the running opening/closing from the page, from `/finance/api/day` for a maker, from the
save response, and from the mirror; the checker's payloads byte-unchanged; the dead CSS with them.
Added: a **"Where the cash is"** card — the parked total expanding to Dr Manoj and Dr Bhawna
individually, scoped to the financial year (1 April), and the bank-trip clock, deliberately *not*
year-scoped because "days since" must survive an April boundary. **A zero is rendered as an
instruction, never as a fact.**

**Six existing assertions were deliberately inverted or re-pointed** (the entry page's opening-field
checks, the id-preservation list, two ledger-arithmetic reads now taken through the checker) —
changed knowingly and re-rehearsed against the state that broke them (F-125). The financial-year
boundary is proven with a real row: ₹12,345 dated before 1 April excluded, the identical movement
inside the year counted, both cleaned up. Differential CLEAN: three declared removals, **all 11
POSTed payload keys untouched**. Rehearsed green and red; the red restored byte-perfect.

**The projection held for the fourth time in a row** — 478/478 written down before the box was
touched, and 478/478 measured.

### Where things stand

**Live:** `finance_app.py` **`f06e139b7651329a72b08bbc5779077f`** · `finance_ui/finance_entry.html`
**`d3844bb96a1d496e5882cfbbb695cbf4`** · smoke **478/478**.

**Open and named, and it is about the owner's books rather than the maker's screen:** the ledger's
"cash in hand" is overstated by whatever is genuinely with the doctors, with no record to net it
down. Either the handovers are entered retrospectively, or a counted reconciliation of the kind
S186 performed for the drawer.

**Next free: D329 · F-134 · A-D25 · Session 189.** This was Session 188, after its own close.

---

## §S188-FINAL — 18 Aug 2026 (Session 188, the third close — F-134: the routine's own missing step, found by running the check the routine is supposed to end with)

With the post-close canon published, the owner ran the proper end-of-session verification —
`python3 /root/deploy/verify_live_pins.py` — and it went **RED on two files the box had exactly
right**: `finance_app.py` and `finance_ui/finance_entry.html`, the two files S188 changed.

**The drift was in the list, not the box.** `/root/deploy/live_pins.txt` was still the one generated
at the **S187 close**, from **Register v5.22** — three Register versions stale.

### F-134 — narrative is not procedure

`live_pins.txt` is generated **from the KB Register**, so a Register bump makes it stale by
definition. S187 knew this, regenerated it, and wrote so in its manifest block: *"the pin list is
regenerated from Register v5.22 against THIS manifest … and ships beside the canon."*

**But that is narrative.** `END_OF_SESSION_PROMPT_v4` §A runs A0 → A7 and ends at *"CANONICAL_MANIFEST
— the linchpin, ALWAYS updated last."* **There was no A8.** So the S188 close rebuilt the manifest,
`MD5SUMS_ALL.txt` and `KIT_ID.txt`, and never touched the pin list. The instruction existed only in a
sentence about what somebody had once done.

**The tool was flawless and it is worth recording separately.** It did not pass on a stale list. It
printed `source : ATTESTED BY THE GENERATOR -- NOT PROVED HERE`, raised `MANIFEST_MISMATCH`, and
showed the CURRENT pin it expected (`9b713355…`) beside the one the list carried (`116a0bdb…`).
**That is F-122's v1.2 fix behaving exactly as designed** — a checker structurally unable to print
VERIFIED without proof. The chain F-97 → D321 → F-110 → F-117 → F-122 caught this on its own.

**Ordering is part of the fix.** The generator refuses to run unless the Register hashes to the
manifest's CURRENT row (F-110), so the pin list cannot precede A7 — it must follow it.

### Fixed

**`END_OF_SESSION_PROMPT` v4 → v5** (Tier 1) gains **step A8 — regenerate the live-pin list, after
the manifest**, with the command, the `register_pin_verified: yes` check, and the line that matters:
*a close that rebuilds the manifest and not the pin list is not finished.* The list was regenerated
from **Register v5.26** — `register_pin_verified: yes`, 43 VPS rows, 11 BLIND — and both previously
drifting files now carry the box's own hashes.

Fault Register **v2.26** · Register **v5.26** · this Archive **v1.39** · manifest rebuilt ·
START_HERE 189 reissued a second time.

### Where Session 188 finally stands

**Three kits, three projections written before measurement, three landing on the number**
(453/453 · 464/464 · 478/478). **Eight findings, every one appended the session it was raised.**
**No decision minted** — the whole session is the execution of D326.

Five findings came from building the next thing on the last. Two came from the owner looking at his
own system **through his staff's eyes**. The eighth came from him running **the verification the
routine is supposed to end with** — which found that the routine did not, in fact, end with it.

**Still open and carried to S189:** **F-133** — the ledger's "cash in hand" is overstated by
handovers to the two doctors that were never entered as `cash_movement` rows, and no record exists to
net it down. **F-130** — the design-fingerprint gap on three remaining pages. **F-131** — 14 stale
git index locks awaiting a delete only the owner can perform.

**Next free: D329 · F-135 · A-D25 · Session 189.** This was Session 188, at its third and final close.

---

## §S189 — 18 Aug 2026 (Session 189, FULL — seven kits live, one retired unlived by its own gate; ELEVEN findings F-130…F-140 minus F-134, every one closed or fixed the session it was raised; the ₹2 lakh question closed; the ₹70,000 gate verified open; D329 minted; smoke 478 → 509)

**The session that audited the auditors.** S189 opened as housekeeping — two cheap fixes off the
S188 backlog — and became the longest build day in the project: the day the record itself was put
under the same discipline as the code, and failed it three times, and was corrected three times, in
the open.

**Phase 0 (documents): GREEN.** Repo cloned anonymously, `md5sum -c MD5SUMS_ALL.txt` → 99/99, exit
0. The F-88 cross-check: 140 manifest tokens, 126 matched real bytes, every non-matching token
legitimately non-document — including the two superseded `START_HERE_SESSION_189` intermediates that
share a filename with the final reissue. The F-107 inverse check clean both directions; exactly ONE
`CANONICAL_MANIFEST.md` (F-123); the A8 pin list confirmed genuinely built on Register v5.26 by
hashing the Register file itself. **Phase 0 (live code): the owner ran `verify_live_pins.py` after
the one manual copy — GREEN with `source : VERIFIED ON THIS MACHINE`, the FIRST proved attestation
in the project's history.** The F-97 → D321 → F-110 → F-117 → F-122 → F-134 chain closed end to end.
Four proved GREENs were recorded this session in total.

**Kit `S189_G1a` — F-130 closed, and the instruction that specified it was wrong (F-135).** The
backlog said: add the design-fingerprint assertions to `approvals`, `workbench` and `review`.
Surveyed on real bytes recovered from the kits by hash (the repo's `finance/` tree is eight builds
stale — F-97 part 2): approvals 4/4 markers, **workbench 0/4, review 0/4** — both predate
`Clinic_Design_Language_v1` entirely. Two thirds of the instruction would have gone RED at its own
gate; it had been written at the S188 close without opening the files — **F-132's shape, in the
record rather than the code — minted F-135.** The kit declares the measured state in BOTH
directions: the two v1 pages asserted positive, the two pre-v1 pages asserted NEGATIVE, so a
rebuild cannot land silently either. Offline projection 476/478 → 480/482, measured exactly; live
478/478 → **482/482**. En route: F-131 closed (the 14 `.git/index.lock.*` files moved out and
deleted by the owner), `.gitattributes` extended (`*.html`, `*.new`, `*.sql` → `eol=lf`; the
duplicated `*.py` line removed, recorded in a comment), and the offline rehearsal was discovered to
require resurrecting `dev_seed_smoke_db.py` — the F-87 tool — which stalls at the S180 schema
(noted, unminted, owner's call).

**F-136 — a hash checked by neither check.** The manifest's Tier-2 Attendance row carried
`staff_ledger.py v2.4 74dac84e…` while calling the value *Register-tracked*; the Register pins
`92665b64…` and contains `74dac84e…` nowhere. Because `gen_live_pins.py` builds the pin list FROM
the Register, a manifest-only hash never enters it; Phase 0's F-88 cross-check asks only whether a
token is a document. **Unverified since S162.** Measured on the box: `/root/staff_ledger.py` =
`92665b64…` and `staff-ledger.service` runs exactly that file — the Register was right all along;
the stray `/root/wa/staff_ledger.py` (`06bf03cb…`, nowhere in the repo) is wired to nothing. Fixed
in the manifest: the md5 stripped, the pointer kept; a sweep found exactly one such duplicate. The
duplicate-CURRENT labelling was also found recurred across four families and corrected, with the
Runbook rows re-named `(pre-…)` — theirs was the only family whose duplicates shared a bare name,
the one shape the generator's strict single-CURRENT parse would refuse.

**The ₹2 lakh question — F-137, and the record's diagnosis was the fault.** Runbook v124 ⭐0b and
this Archive's own §S188-POST said cash in hand was *overstated by unbooked handovers*. Reading the
schema before building (the assistant first repeated F-132 by claiming the box held "no evidence"
— the evidence sat in `cash_count`, exactly where the authoritative S186 doc said; owned
immediately): `v_day_cash` subtracts EVERY `cash_movement` row from cash in hand, so the record's
prescribed fix — book the handovers as movements — would have cut ₹2,05,198 to ≈₹30,000 **against
a physical count proving ₹1,75,198 genuinely held** (drawer 0 · owner ₹18,963 · Dr Bhawna
₹1,56,235; S186, notes counted). There was NO overstatement: the custody facts had been recorded
as PROSE in `cash_count.explanation`, in the same session `cash_custody_event` was built to hold
them. **Owner ruling: doctor-held cash IS cash in hand, located elsewhere. Custody is LOCATION;
movement is QUANTITY.** Kits: `S189_W1a` (the card reads `cash_custody_event`; six checks proving
a custody event moves the card and not the ledger, and a movement the reverse; 482 → 488) and
`S189_C1a` (the counted position: four rows totalling ₹1,75,198 to the paise against `cash_count`,
the ₹1,45,000 balancing entry admitting its journeys are unitemised, the empty drawer recorded by
writing nothing; the gate restores the whole database unless the ledger is byte-identical).

**F-138 — C1a's first run was refused by its own final smoke, and the gate was right.** Verify had
already printed *"cash in hand UNCHANGED, as promised"* — then three of the four new F-137 checks,
which asserted the store's ABSOLUTE state ("parked must be ₹0.00"), went red the moment the
migration legitimately recorded ₹18,963, and the installer restored the books untouched. The
aggravation that earned the number: the fourth check in the same block had already been converted
to a delta citing F-106 — the discipline applied to the line under the cursor, not the block. Fixed
in `S189_W1b`, whose installer met the count-equal problem honestly: 488 → 488, so it **reproduces
the failure** — applies the C1a migration to a throwaway copy, requires the current app RED with
every FAIL naming F-137, the new app GREEN — before any swap. On the box: 485/488 reproduced
exactly, then 488/488 twice, then C1a green end to end. **Darpan's card now reads Dr Manoj ₹18,963
· Dr Bhawna ₹1,56,235 · as at the count of 17 Aug. F-133 closed: the capability unused since S179
holds the counted position.**

**The §4a ₹70,000 gate — VERIFIED OPEN (D326(c)).** Five machine checks — the Staff Ledger read
raw (16 rows; Darpan's seven are the July close exactly: two migrated tranches ₹1,83,000 +
₹1,80,000, the 2026-04 skip, ₹19,000 perks, July's −₹5,000 split ₹1,000/₹4,000 to balance
1,79,000, **the D250 engine's first real close matching the workbook replay to the rupee**) · the
finance drawer (the ₹40,000 as three rows, 9 Apr/30 May/18 Jun) · the live workbook
(`Loan Master B27: ST-advance outstanding = 0`; the ST ledger empty of entries) · the §S155
migration record (as-of-June balances proven to the rupee, NO ST advances in the block) · July's
close (−₹5,000 only) — plus the one fact no surviving file holds, supplied by the owner: recovering
₹40,000 against a ₹20,000 base means near-zero take-home for two months, and **yes, his salary was
cut.** The Apr–Jun advances were recovered in the workbook era. No double-count exists in any book.
**The salary bridge (D3) is UNBLOCKED.** `S189_70k_Gate_Verification.md` written and FILED the same
session. The 17 Aug ₹30,000 confirmed in NEITHER book — the owner's one-click, with the ₹10,000
category decision (free text if July-salary settlement; `salary_advance` double-counts).

**The expense menu — F-139, F-140, kits `S189_E1a`/`S189_E1b`.** The owner: *"this free text entry
will become the rogue spoiler — do some dropdown selection flow."* Reading the existing control
found the deeper fault (**F-139**): the staff selector was hardcoded ids 1/2 into `staff_ref`,
empty since S179, never read or written by the app; *"Someone else"* a fake staff member. Surveyed
first: zero rows ever carried a staff_id. Owner ruling: *"Darpan draws only his salary advance from
the medical cash"* — the selector removed entirely, identity SERVER-resolved (F-84), the one real
row created lazily, client ids ignored. The menu: five categories, one authored source, the served
page held to every label, a skipped choice refused server-side, Other requiring details, the
advance writing the exact S184 string. **E1a was refused by its own gate on the box** (**F-140**):
its rehearsal-day finder walked forward from 1 April into a D322 Sunday hole 135 days back, where
the save answers `too_old` before the expense parse — the offline store was continuous: right data,
wrong SHAPE. Diagnosed by reproduction (a beyond-window gap = the exact six FAILs; a mid-window
gap = three, discriminating `too_old` from `negative_cash`), fixed (backward-from-today finder,
the D2/F-129 direction; server errors embedded in every check label), rehearsed on FOUR store
shapes, landed **488/488 → 509/509, +21 exactly**. E1a retired unlived — the second kit today
refused by a gate, and the second time the gate was right. Named, deliberately unfixed: a re-saved
draft silently drops its earlier expenses (live since S179); the D3 bridge must reconcile
`PENDING_LEDGER_WIRING` rows against manual ledger entries.

**Canon discipline this session: THREE mid-session folds**, each with pins recorded as they moved,
each bump proven zero-loss by reverse application onto the manifest's own pins, the pin list
regenerated in the A8 order each time, and four proved GREENs on the box. The owner's EOS directive
at close: **the assistant executes the KB swap, Notion, the repo commit to the PC and the cold kit
itself; the owner's residual work is ONE double-click (`PUBLISH_ALL.bat`, the D328 boundary until a
scoped deploy key is ruled on) plus the on-box pin-list copy.** A portable definition of EOS /
EOS-light was written for reuse across projects (`EOS_DEFINITION_PORTABLE.md`).

### D329 — the Advance Pool (minted S189 close; full text of the signed design in `S189_Advance_Pool_Design_D329.md`, Tier-1 CONTRACT)

**Every approved medical salary-advance joins Darpan's one Advance Pool automatically** (the B6
bridge: push-on-approval, scoped token generated on-box, idempotent by finance expense id,
provenance carried, fail-soft never fail-silent). **Recovery = min(pool, advance_instalment) at
every monthly close** — a second deduction stream beside the D250 loan, never inside its waterfall
(which recovers interest-free money LAST — a new advance folded in would queue behind ₹3.59 lakh).
`advance_instalment` is a checker-only setting, default ₹5,000, every change its own logged row.
**"Foregone on request" gets both meanings:** Advance-Skip (defer, max 2/Indian-FY, no
capitalisation — the loan's relaxation mirrored, minus the interest) and Advance-Waive (forgive,
uncapped but never silent, reasoned row). **Month-end reconciliation card** before every close:
opening pool + advances (each linked to its finance day and scans) − recovery − waived = closing;
unmatched items in either book surface for one-tap LINK — which is how the hand-entered ₹20,000
marries its finance row instead of double-posting. The pool opens at ₹20,000 — the Apr–Jun
₹40,000, verified recovered, stays out. There is deliberately NO consolidation ceremony: the pool
IS the consolidation, so the randomness of the drawing stops being an accounting problem. Builds
as `S190_SL1` (ledger: categories, setting, close integration, card, receive endpoint) +
`S190_F1` (finance: push-on-approval, LINK, truthful `ledger_posted`), token on-box, order
SL1 → token → F1, each rehearsed against a store carrying the live file's SHAPE (F-140).

**Live at this close:** `finance_app.py` `5cb73ff83b591535053c7911026ecd8b` ·
`finance_entry.html` `1c7d2dc3179f29e9de0b9fb0d77c6fe1` · migration `S189_custody` applied ·
smoke **509/509** · cash in hand ₹2,05,198 (→ ₹1,75,198 = the counted figure, once the ₹30,000 is
entered) · custody: Dr Manoj ₹18,963 · Dr Bhawna ₹1,56,235 · the ₹70,000 verified closed · pin
list `register_pin_verified: yes` at every fold.

**Next free: D330 · F-141 · A-D25 · Session 190.** This was Session 189.

---

## §S190 — Session 190 (19 Aug 2026) — FULL BUILD SESSION: D330 + D331 minted AND executed, SEVEN kits live, the ₹30,000 sitting closed end to end, the quota lane (owner ruling "A")

**The session that put the owner's money rules into the machines the same day he ruled them.**
Phase 0 green (manifest verified by md5, all tiers). The backlog's ⭐0 was the ₹30,000 sitting;
the owner's rulings while walking toward it redesigned the expense system twice over — and both
redesigns were signed, built, installed and verified before the session ended, with the sitting's
three advances not only entered but wired to recover themselves.

### The two decisions, minted and executed same-session

**D330 — the expense menu, the derived ceiling, compulsory evidence (supersedes D329 whole).**
Sanjeevni expenses become THREE categories: **salary advance · home expenses · other expenses**.
The advance is capped by a **derived** ceiling — per-staff % of base salary floored to the last
₹100 (Darpan 75% of ₹20,000 = ₹15,000/calendar month; all other staff 50%; nothing stores the
rupee figure, F-136) — shown inline with the month-to-date BEFORE he types, refused server-side
past it with both figures in the message. Over the ceiling nothing is drawn from any drawer —
the staff pipeline takes it. Home/other are free text with **compulsory per-row evidence at
FILE, no escape hatch** (the owner's own flow: photograph at payment, upload at filing — so the
bill input went INLINE in the expense row on his ruling, not behind a post-save scanner). Home
expenses total separately as the proprietor's **drawings** on tile and month grid. Petty spends
stay on the manual book (a digital petty book is **PARKED**). The clinic unit gets the two
expense categories + the same evidence rule and deliberately NO advance path. Courier COD for
personal items = home expenses (why courier is not a business head). **Applies from August.**
Full text: the signed contract `S190_Expense_Menu_Redesign_D330.md` (pinned Tier-1 CONTRACT).

**D331 — the staff advance policy, every staff member, one rule.** Inline month-to-date beside
the derived ceiling on the Staff Ledger entry form (base from `staff_master.csv`, pct from
`advance_pct.json` — default 50, Darpan 75; §5.3 answered by the installer from the box's own
CSV: base ₹20,000 → ₹15,000). Above the ceiling = **SPECIAL**: the maker may draft, the maker
uploads the written application **signed by Dr Manoj or Dr Bhawna** (the ledger's first
attachment — shared scan widget, sha in the row), the checker approves — approval REFUSES
without it, and a special advance is never direct (even a checker's own entry goes PENDING).
An advance may be attributed **against a future month** (`against_month`): it consumes THAT
month's quota and is recovered from that month's close (eligibility filter; D250 arithmetic
byte-untouched). The Sanjeevni gate counts forward-attributed salary-side advances (fail-soft
JSONL read, forward-only — double-count structurally impossible; degradation visible: "Sanjeevni
book only"). Missing base = gate stands down visibly. Applies from August. Full text: the signed
contract `S190_Staff_Advance_Policy_D331.md` (pinned Tier-1 CONTRACT). *(The application
requirement on NEW interest loans stays procedural — wiring it would break the migration path;
recorded in the contract.)*

### The seven kits, in install order — sixteen consecutive exact projections

1. **`S190_E2`** (finance 509 → 542, +33) — D330 whole: three-choice menu, derived ceiling
   inline + server refusal, `expense_uid` stable row identity closing the draft-resave wipe
   (loadDay refills expenses/movements/non-cash; the save's delete-and-reinsert survives),
   per-row evidence (`expense_attachment` lazy table, camera AND gallery), the File gate
   (`expense_evidence_required`, no escape hatch), drawings split, clinic twins. One kit instead
   of the contract's three on the owner's "minimum steps" ruling. Kit v1 was REFUSED by its own
   D317 gate — its clinic-page hash constant carried a tail fabricated from a truncated record
   prefix (F-109/F-116 shape); nothing on the box moved; v2 changed one constant, transcribed
   from the owner's own on-box md5sum. The delivery note also gave `/root/deploy` for
   `/root/deploy/repo` (F-135 shape) — the owner hit it live. Both recorded as F-141 candidates.
2. **`S190_SL2`** (ledger 190 → 212, +22) — D331 whole on the Staff Ledger.
3. **`S190_F2`** (finance 542 → 547, +5) — the cross-system plumbing: `ledger_fwd_advances_p()`
   fail-soft forward-only read, inline line + refusal include ledger-attributed advances.
4. **`S190_SL3`** (ledger 212 → 214, +2) — **the owner's first live look fixed the policy's
   blind spot**: the S155 migration rows (years of history dated Aug 2026) made Darpan's line
   read "Rs 3,63,000 of Rs 15,000" and would have refused his ordinary ₹15,000. RULING: the
   quota counts from the D331 install forward — only rows with an explicit `against_month`,
   and never interest-bearing loans (which also bypass the gate; the parallel D250 instrument).
   Advances page gains against-month · SPECIAL badge · 📄 application link.
5. **`S190_F3`** (finance 547 → 547, count-equal, proven by reproduction ON THE BOX: 545/547
   with exactly 2 fails both naming F3, then 547/547) — the bill chosen INLINE in the expense
   row, uploaded automatically on Save; File-with-pending becomes draft-save → upload → File.
   Kit v1 was REFUSED by its own harness: `tail -1` read a FAIL line printed after the smoke
   summary as the summary. v2 greps the whole output. Third gate refusal of the day, third time
   the gate was right, third F-141 candidate — all three caught the TOOLCHAIN, not the payload.
6. **`S190_F4`** (finance 547 → 549, +2) — owner-found on the real 31-July screen: "only the
   doctor can change it" shown TO THE DOCTOR. The medical locked-day gate tested the SSO broker
   role (`u["role"]`) instead of the unit roles; the clinic twin had it right since S182. One
   functional line; an audit found it the only wrong `u["role"]` use in the file. F-84 family.
7. **`S190_F5`** (finance 549 → 550, +1) — owner-found: his edited 31-July day vanished from
   the approvals queue while its ₹10,000 counted — the queue hides `legacy_sheet` days by
   design (bulk import), but an edited legacy day needs the queue. A correction now re-marks
   the day `source='app'`, both units; the revision keeps the legacy original verbatim.

### The ₹30,000 sitting — closed end to end, the proof line to the rupee

The owner's rulings: ₹10,000 = July advance, finance entry dated **31 July** (filed and approved
via `/finance/review` after F4+F5 cleared the path); ₹15,000 = August advance from medical
(exactly his 75% ceiling — the inline line read "15,000.00 of 15,000.00 max"); ₹5,000 = a
transfer-out movement to Dr Manoj, reaching Darpan through the salary pipeline **attributed
against September** — so August stays exactly at ceiling and September's drawer limit becomes
₹10,000 automatically. Cash in hand landed **₹1,75,198.00 — the counted figure (Dr Manoj
₹18,963 + Dr Bhawna ₹1,56,235), to the rupee**, verified on the live tile by Claude driving the
owner's own Chrome (tabs, screenshots, the Hub, the entry page — the first browser-verified
close in the project). All three ledger entries confirmed present in `/ledger/book` (an earlier
"done" had in fact been refused by the pre-SL3 gate — the red "NOT saved" was missed; proven
absent from the book, then re-entered on a walked path). 14 & 15 Aug approved by the owner.
17 & 18 Aug remain deliberately zero-figure drafts — Darpan owes real figures + scans next
session; the 17-Aug Marg push is already applied.

### SL4 — the quota lane (owner ruling "A")

Minutes after the three advances went in, the owner's statement look surfaced the last gap:
all three read **"(waiting for the loan to clear)"** — D250's waterfall queues every
interest-free advance behind the ₹3.59 lakh loan book. Right for legacy tranches, wrong for a
month's own salary money (D329's parallel-stream idea had been lost in the supersession).
**RULED "A": the ledger's own close recovers them** — August's close takes ₹10,000 + ₹15,000,
September's the ₹5,000; no manual workbook squaring. Kit **`S190_SL4`** (ledger 214 → 218, +4):
in `close_month()`, after the D331 eligibility filter, a QUOTA advance (explicit `against_month`
· not interest-bearing · default recover-fully instalment, `instalment == amount`) recovers IN
FULL in its own lane beside the waterfall. A deliberately partial instalment opts back into the
waterfall; a loan Skip pauses ONLY the waterfall — the quota lane always collects. Waterfall
order and arithmetic byte-untouched. Statement cards name the recovery month (first close ≥ the
against-month — the July-attributed ₹10,000 collects at the August close, July being closed).
The owner's F-132 look confirmed all five cards exactly. Live pin `3b09073a…` → `470bb113…`,
backup `staff_ledger.py.bak_S190_SL4_20260819_101237`.

### Canon discipline this session

**Six mid-session folds** (Register v5.31 → v5.36), every pin recorded AS IT MOVED (F-97), every
fold zero-loss-proven by reverse application onto its predecessor's pin; **eleven GREEN
`verify_live_pins.py` runs** on the box, `register_pin_verified: yes` throughout, the eleventh
at 43/43 after fold 6. Two project-knowledge 2MB refusals handled by deleting repo-verified
superseded Register versions from project knowledge only. A Chrome-automation lesson recorded:
clicking a native `<select>` opens an OS dropdown that wedges the extension — use form_input or
let the owner touch selects.

### Candidate findings — recorded, NOT minted (the F-141 ruling is the owner's, deferred to S191)

Six candidates: (1) the fabricated hash tail (E2 v1) · (2) the wrong install path in the
delivery note · (3) the `tail -1` harness (F3 v1) · (4) the migration-dated quota (SL2→SL3) ·
(5) the broker-role locked-day gate (F4) · (6) the hidden-legacy queue (F5). Plus one UX note:
a refusal that looks like a save (the missed red behind the "ledger entries done" belief).

### Deferred to S191 (owner's word: "WILL DO IN NEXT SESSION")

Darpan's real 17 & 18 Aug figures + scans → approval · Surendra's ₹8,000 advance PENDING
(over his ₹5,200 ceiling; grandfathered entry — approve or reject) · the F-141 ruling.

**Live at this close:** `staff_ledger.py` `470bb1133046d9076de5a2edd413f66c` (218) ·
`finance_app.py` `17e6b84ce90ca7d7a0a9ba0c668ab15f` (550) · `finance_entry.html`
`bae2dd8983c8c3b886705a4f6b6d8dba` · `finance_entry_clinic.html` `d4f7ddaa4c2151935bc81f1bf38c8945`
· `advance_pct.json` seeded `{"Darpan": 75}` · cash in hand **₹1,75,198** = the counted figure ·
the August close will recover ₹25,000 and September's the ₹5,000 automatically.

**Next free: D332 · F-141 · A-D25 · Session 191.** This was Session 190.

---

# §S191 — 19 Aug 2026 (Session 191, FULL EOS — the confirmation session: F-141…F-146 ruled at the mid-session fold; the staff advance system confirmed against the live box and the confirmation surfaced F-147…F-151; D332 minted and SIGNED; July salary corrected to the pre-policy ruling; no live code moved, no live data changed)

**0. Phase 0 and the twelfth GREEN.** Documents: fresh anonymous clone, `md5sum -c` → 124/124 OK exit 0; F-88 cross-check 183 of 198 tokens matched real bytes, the 15 others each legitimately non-document; F-123 one manifest; A8 source_md5 proven by hashing the Register. Live code: the owner ran the chained pull + pin-copy + `verify_live_pins.py` — **GREEN, match 43, drift 0, `source: VERIFIED ON THIS MACHINE`**, the twelfth consecutive GREEN, this one proving the whole mid-session fold (pin list `e07ca968…` · Register `c93139fd…` · manifest `507c0d53…` measured on the box) byte-identical end to end through PC and GitHub.

**1. The mid-session fold (recorded in the §S191 manifest block as it happened).** The six S190 candidates RULED — five numbers, one fold: F-141 (fabricated hash tail, the wrong install path folded in as its second instance) · F-142 (tail-1 harness) · F-143 (migration-dated quota) · F-144 (broker-role gate) · F-145 (hidden-legacy queue) · F-146 (a refusal that looks like a save — the only one OPEN, UI fix owed). Fault Register v2.29 → **v2.30**, Register v5.37 → **v5.38**, both reverse-application-proven; the proof harness itself produced one false False and was fixed under F-142's own rule, minutes after minting it. Surendra's ₹8,000 left PENDING by owner ruling, surveyed first, with the recovery consequence recorded so no session re-derives it.

**2. "Confirm the work done in the staff advances system" — and the confirmation was the session.** Done on the box, not the record: the S190_SL4 kit payload hashed to the live pin `470bb113…` (so the code read was the code running); the owner ran `--selftest` → **218/218**; every D331/SL3/SL4 clause read in the live bytes and checked against the contract — ceiling derivation, PENDING-counts-too, SPECIAL-never-direct, the application gate in `decide()`, `against_month` eligibility, the forward-only cross-system read, the quota lane's three conditions. **All held.** The live pages corroborated: /ledger/advances showed the five open items exactly as recorded; /ledger/book showed the three sitting advances APPROVED. One assistant error recorded, not silent: the `advance_pct.json` path was written from assumption (`/root/wa/ledger/`) instead of read from the code (`LEDGER_DIR` default `/root/staff_ledger`) — the owner's cat failed harmlessly; the F-135 shape, in the toolchain not the canon, third toolchain slip of the day's family.

**3. What the confirmation surfaced — the projection of the first real month-end.** August would recover ₹30,000 against the ₹20,000 base (quota lane ₹10,000+₹15,000, both first-close-≥-month, plus the loan's ₹5,000); `compute_salary()` has no floor; ≈₹14,000 of repayment would be recorded that no money paid. Reading D250's full text against the machine then yielded the pattern of the day: **the arithmetic was implemented faithfully (workbook-exact, proven twice) and the judgment clauses were never built** — "if salary can't bear all, the instalment skips" (→F-147), the 3rd-skip perks flag (→F-149). The drawer→ledger bridge was found honest-but-absent: `PENDING_LEDGER_WIRING`, B6 having died with D329's whole-supersession (→F-148). `S191_Darpan_Money_Model_Objective_Report.md` written and FILED — the objective statement of how his money actually runs: D250's two-tranche loan + waterfall + skips + ST-advances; D258's one-home-per-rupee migration; D331's 75% ceiling; the live position to the rupee (loan ₹1,79,000 · interest-free ₹2,10,000 · perks ₹19,000 · skips 1/2).

**4. July was already ruled and the machine had contradicted the ruling (F-150).** S151, twice: July is pre-policy, Deduction/Incentive columns "PREVIEW ONLY (policy starts August)". The live July salary applied both — **₹16,552.38 over-deducted across all twelve staff**. The owner's "JULY NO DED" was his own standing ruling, unenforced. `Salary_July_2026_for_finalisation.xlsx` built from the live table (columns transcribed, nothing re-derived): computed vs per-rules vs correction, plus the owner's waiver / advance-drawn / actual-paid / notes columns — **deliberately NOT filed to the public repo (F-31/D320: all-staff salary data); delivered to the owner and placed on the PC outside the git working tree.** The owner finalises it there as the waiver workflow's first test run.

**5. D332 MINTED AND SIGNED — the Waiver, Defer & Repayment-Defined Advance layer** (signed contract `S191_Waiver_Capacity_Layer_D332_Design.md` v3, FILED and pinned this close; the owner's agreement and his three refinements minuted in the document). The one-sentence system: *an advance is an amount plus a repayment schedule defined at approval; the close collects the schedule; the owner can DEFER any single collection with one tap and a reason; nothing recovers that the salary cannot bear; everything owed is always visible with its months remaining.* The rulings: DEFER replaces SKIP (whole instalment shifts, no capitalisation — proven costless since interest rides inside each collected instalment; 2/FY survives as a waivable ₹1,000 penalty on interest-bearing loans only, attached to the INSTRUMENT never the person) · the waiver instrument (WAIVE forgives / DEFER postpones, never one button; LINE / STAFF_MONTH / ALL_MONTH; `waiver_authority` seeded to Dr Manoj, Dr Bhawna scoped-in-but-INACTIVE; compulsory written reason, no escape hatch; amounts derived never frozen; own visible column; token-protected; contra-reversed) · the capacity rule (F-147's fix, D250's clause built) · the schedule lane (uneven distributions — "₹8,000 → ₹4,000 → ₹4,000 → ₹4,000" — set at approval; uniform instalment and SL4's recover-in-full both special cases; the lane fix is the ONLY recovery-side code) · the request-not-draw pharmacy flow (F-148 dissolved: one approval tap releases cash AND writes the ledger) · enforcement dates as settings unlocked by the notice-served date (F-150's fix; the notice is unshared, so no promise binds the ladder dates; August ruled preview-only; Sunday policy the same, off until switched) · the per-staff Perks view · the F-151 wording fix. Workflow ruled: salary detail generated → staff corrections → owner's final waivers → owner closes with actual amounts paid. **Builds: S192_SL5 (waiver + settings + wording) · S192_SL6 (defer + schedule lane + capacity + loud surfaces) · S192_SL7 (perks view) · S192_F6 (request flow).**

**6. Darpan's concrete rulings (data corrections GATED on a separate GO — none executed this session):** July closes at **₹0 payable**, fully composed: ₹20,000 sanctioned no attendance deduction − ₹10,000 drawn 31 Jul (absorbed) − ₹5,000 loan instalment (collected) − ₹5,000 offset against pre-31-July advances; one adjustment entry narrates the composition. The 17-Aug money consolidates to **ONE ₹20,000 SPECIAL advance** (₹15,000 drawer + ₹5,000 via Dr Manoj; the against-September booking dissolves into it), **owner's uneven schedule ₹8,000 (Aug) · ₹4,000 × 3 (Sept–Nov)** — August keeps headroom for the ₹5,000 loan and ₹7,000 drawable; cleared at the November close; ₹15,000 steady from December; the signed application scanned at booking (the D331 gate will refuse without it — owner obtaining it). Ceiling **50% from August** (75% exception ends; `advance_pct.json` one line). ⚠ **THE TRIPWIRE, recorded loudest:** the ₹10,000 (`fbd756fe1473`) is settled inside July — **unless it is closed out before the August close runs, the close collects it a second time.** Until SL6, the 8/4/4/4 distribution is bookable today as two rows (₹8,000 against-August recover-in-full = existing SL4 + ₹12,000 @ ₹4,000 from Sept — needing the lane fix only from its September first collection). His total owed becomes ₹3,79,000: the ₹10,000 was salary paid early, never a loan, and the books will finally say so.

**7. F-147 … F-151 appended (Fault Register v2.30 → v2.31), every one ruled by the owner the same day** (build · build-and-test · correct · build-as-setting · correct). None found by a failure: all five found because a confirmation was performed against the live system instead of the record — F-135's rule applied at scale.

**8. The close itself:** Archive v1.41 → **v1.42** (this section; pure append, prefix proven byte-identical) · Fault Register → **v2.31** · Register → **v5.39** (D332 into the decisions index; findings advanced; pointers; lineage; reverse-application-proven) · Runbook → **v127** · START_HERE → **192** · manifest rebuilt (the two S191 docs pinned as Tier-1; the July xlsx recorded as deliberately-not-filed with its reason, so the F-107 inverse check reads intent rather than absence) · pin list regenerated LAST from v5.39 (A8) · cold kit NOT due (3 of 3–5; due ~S192–S194). Owner meanwhile: obtains Darpan's signed application · introduces him to the Sanjeevni daily entry portal for his daily submissions (17/18 Aug drafts, Runbook ⭐0) · finalises the July sheet as the waiver test run.

**Next free: D333 · F-152 · A-D25 · Session 192.** This was Session 191.

---

**END OF KB HISTORY ARCHIVE v1.42. §S191 is the last section; §S190, §S189, §S188-FINAL, §S188-POST, §S188, §S187, §S186-POST, §S186, §S185, §S184, §S183, §S182, §S181, §S180, §S179, §S178, §S177 and earlier sit above it. If §S191 or this marker is absent, this file is truncated and must not be used as canonical.**

---

# §S192 — 19 Aug 2026 (Session 192, FULL EOS — the KB freed, three D332 kits live, the gated money corrections executed, and F6 stopped at its design on purpose)

**0. Phase 0 and the thirteenth GREEN.** Documents verified against a fresh anonymous clone; `CANONICAL_MANIFEST.md` measured on the box at `d670effb…`; the owner ran the chained pull + pin-copy + `verify_live_pins.py` → **GREEN, match 43, drift 0, `source: VERIFIED ON THIS MACHINE`**, built from Register v5.39 (`28a807a0…`) — the thirteenth consecutive GREEN, and the last one before this session moved the ledger pin three times. Every canonical file used in this close was taken from the git canon and **hash-verified against its manifest pin before it was touched** (Register `28a807a0…` · Archive `b59532f7…` · Fault `a9484bc4…` · manifest `d670effb…` · Runbook `8d56943c…` · START_HERE `ec0bfa31…`).

**1. THE KB CLEANUP — the owner's own S191-close ruling, executed first.** Project knowledge stood at **1,919,222 of 2,000,000 characters (96%)** and was months from refusing writes. The governing rule was the owner's: *a project doc may be deleted ONLY after its exact bytes are verified present in the git canon by md5 comparison at cleanup time; a doc whose bytes exist nowhere else is NEVER deleted — it is FILED first (the F-107 discipline), or explicitly kept; a filename match is not provenance (D188).* Method: a fresh anonymous clone, a full md5 index of 1,200 files / 1,059 unique hashes, and every candidate's manifest pin cross-checked against it — plus a round-trip control (two Registers hashed from project knowledge matched their manifest pins AND their git copies byte-for-byte, proving the read path exact before any deletion). **47 documents deleted on one approval: 9 superseded Registers · 6 Fault Registers · 11 Runbooks · 12 START_HEREs · 4 historical dossiers · 5 append artefacts, every one of the 47 proven present in git first.** Result **1,919,222 → 1,149,776 (96% → 57.5%)**, comfortably under the 60% target. **Five Category-C docs were deliberately NOT deleted** — their bytes are not pinned in the manifest, so cheap proof was unavailable and the rule says keep. Nothing current was touched.

**2. D332 — THREE KITS BUILT AND LIVE IN ONE SESSION.** All three built on the **live bytes recovered from `deploy_kits/S190_SL4/` by hash, not filename** (D188): the repo's `staff_ledger/staff_ledger.py` (`92665b64…`) is the stale mirror and was never used (F-52 / F-97 part 2).

- **`S192_SL5`** (`470bb113…` → **`0ed19495…`**, selftest **218 → 240, +22 exactly**). The **waiver instrument** (§2.8): WAIVE forgives a *derived* deduction — never a frozen rupee — at scopes LINE / STAFF_MONTH / ALL_MONTH, with a compulsory written reason and no escape hatch, append-only and contra-reversed (activeness DERIVED from the contra records, never mutated in place), its own `+waived` column on both salary tables, the per-staff breakdown and `salary_final_<month>.csv`, stored per month in `waivers_<YYYY-MM>.json`, `waiver_authority` seeded **manoj active / bhawna scoped-in-but-INACTIVE** and deliberately not a one-tap web toggle. **Owner ruling this session: a waiver may forgive ANY deduction line** — attendance (`att:<type>`) or a ledger debit (`led:<row id>`); WAIVE forgives, DEFER postpones, two verbs and never one button. The **policy-date settings** (§2.7 / F-150): `ledger_settings.json` + `/ledger/settings`, where `attendance_enforce_from` is the notice-served month — **while it is unset every month is PREVIEW-ONLY**, attendance deductions shown struck-through and not applied to NET, while ledger money always applies because it is owed rather than a penalty. The **F-151 wording fix**, owner-scoped to attendance only: rendered "fine" → "attendance deduction"; the uniform / i-card / ad-hoc ledger charges keep their names and the att-report CSV headers are untouched. The approval token now hashes the waivers and the settings, so a stale preview refuses instead of silently recomputing.
- **`S192_SL6`** (**`0279540e…`**, selftest **240 → 274**). **The SCHEDULE (§4):** an advance is an amount *plus* a repayment schedule defined at approval; a schedule that does not add to the advance exactly is refused, because a schedule with a silent gap is a promise the close cannot keep; the close collects the month's step **in its own lane beside the waterfall**, never queued behind the loan book — and **SL4's recover-in-full and a uniform instalment are both special cases of it**, one generalisation subsuming all three. Rows with no schedule behave exactly as before. **DEFER replaces SKIP (§2.1):** the instalment shifts whole and the schedule **EXTENDS**; no automatic capitalisation, since interest rides inside each collected instalment; the 2/FY discipline survives as a **waivable ₹1,000 penalty on interest-bearing loans only**, attached to the instrument and never the person; a written reason is compulsory; `LOAN_SKIP` is untouched for history. *(Recorded because it was nearly shipped: the first implementation counted elapsed months only across the listed steps, so after a defer the FINAL step could never fall due — the schedule's tail would have been silently eaten. Caught by testing the arithmetic before writing the test block, and fixed by counting elapsed months from the schedule's first step, unbounded.)* **The CAPACITY rule (F-147, D250's unbuilt judgment clause):** one budget per staff per month = base − other debits booked − a protected `min_takehome`, spent by every lane in order; what cannot be taken becomes a **`CAPACITY_HOLD`** line and **stays owed**, never silently dropped; **no base salary on file DISABLES the gate** rather than freezing recovery — the D331 fail-open design, shown and never silent.
- **`S192_SL7`** (**`44e39d6a…`**, selftest **274 → 287**). The **per-staff Perks view** (§2.9), closing **F-149**: a perk is a record of a benefit paid, not money owed — no approval chain, excluded from salary by design — and the gap was that it could be *entered and then never read*. `/ledger/perks` gives an index of every staff member's net total, a per-staff view with the lifetime figure and a year filter, and append-only honesty: a contra'd perk nets to zero with **both rows still visible**, because a contra is simply a negative PERK row and needs no special case.

**3. THE GATED DATA CORRECTIONS — executed, after a survey and a dry run.** D332 §6 items 1–4, on the owner's separate explicit GO, **before the August close** as the contract required. The survey came first and was the point: it proved all three target rows APPROVED, un-collected, `recovered: 0`, **with no children** (so the code would permit a contra), and — decisively — that **`2026-08` was NOT yet closed**, which made the ₹10,000 tripwire live and real rather than historical. A dry-run mode printed every intended write before anything was committed. Then six writes: **contra ₹10,000 `fbd756fe1473`** (`c287af8feea5`) — *the tripwire killed: August can no longer collect money settled in cash in July* · **contra ₹15,000 `540acd6b8e7c`** (`aba609b148ee`) and **contra ₹5,000 `d6162b009451`** (`9b8462f9ac2e`) · **`advance_pct` Darpan 75 → 50**, ceiling ₹15,000 → **₹10,000**, the exception ended · **ONE ₹20,000 SPECIAL** dated 17 Aug against 2026-08 with the owner's real schedule **8,000 + 4,000 × 3** (`0cc0b26b38c5`, **PENDING** — the D331 application gate has no escape hatch) · **a ₹0 record-only entry** narrating the July zero composition (`791d321b9dd4`), deliberately moving no money because July's ledger is already closed and a real movement would have landed in *August's* close. Verified afterwards by re-running the same read-only survey, not by assertion: the three originals each carry their contra, **Darpan's open advances are now only the two loan tranches**, `pct=50 ceiling=10000`, and August's quota reads **₹20,000** — correct only because each contra was stamped with its original's `against_month` (see F-153). Once the SPECIAL is approved, August takes ₹8,000 + ₹5,000 = ₹13,000, take-home ₹7,000 — exactly the signed contract's table.

**4. `S192_F6` — DESIGNED AND DELIBERATELY NOT BUILT.** The survey found F6 far narrower than the contract implies: three of §2.5's four requirements are already live, including the inline ceiling refusal that names both figures (D330 gate 1), and the approval endpoint already carries `# Approval is what posts a salary advance to the Staff Ledger. Not entry.` with the ledger call stubbed as **`PENDING_LEDGER_WIRING`** — *the codebase being honest about its own gap rather than pretending the posting happened*. What remains is the wiring. **It was not built because it could not be honestly tested here:** `finance_app.py`'s smoke suite opens with `shutil.copyfile(live_db, tmp_db)` — it runs against a copy of the real `finance.db`, which exists only on the VPS, so the 550 checks cannot run offline. Shipping into it on reasoning alone is **F-87 exactly**, whose own RULE is that making an unrunnable suite runnable is the FIRST task. The remedy asset (`finance/dev/dev_seed_smoke_db.py`) exists; the route is a seeded store carrying the live SHAPE (F-140), then **differential** verification — baseline vs modified on identical data. Design filed as `S192_F6_Design_and_Survey.md` with the mechanism, the idempotency guard, the **ordering** (ledger append FIRST, then `ledger_ref` and the finance commit, so a crash leaves a visible orphan rather than an invisible lie), and the fail-loud requirement. One open question flagged rather than assumed: whether "the drawer is not touched" is *already* true depends on whether `v_day_cash` counts expenses on unapproved days — to be read, not guessed (F-133's shape). **A cross-book money writer is the last thing that should ship on a plausible argument.**

**5. Findings.** **CLOSED by code now running: F-147** (capacity rule, SL6) · **F-149** (perks unreadable, SL7) · **F-150** (policy dates as settings, SL5) · **F-151** (the "fine" wording, SL5). **F-148 stays OPEN**, pending F6. **Three minted** — the owner having ruled at S191 that the call is the assistant's: **F-152** (`.gitattributes` pinned `*.py/.sh/.html/.new/.sql` to LF but not `*.txt`/`*.md5`; a CRLF `SUMS.md5` makes `md5sum -c` read the filename with a trailing `\r`, fail to find it, and turn a **perfectly good kit RED at gate [1/6]** — a gate firing wrongly, which D316 warns is worse than no gate; **found from a publish warning, fixed the same session** with the reasoning written into the file; kin of F-100/D164) · **F-153** (`make_contra` copies category, staff, dates and the negated amount but **not `against_month`**, so a reversed advance keeps eating that month's quota — Darpan's August would have read ₹35,000 instead of ₹20,000, and a future above-ceiling refusal could fire on money already reversed; worked around in the correction script, **the one-line gap in `make_contra` is still open**) · **F-154** (*the assistant had a live bridge to the owner's PC and did not use it*: the first kit was delivered as a chat download with hand-unzip instructions, which failed three times — including an instruction containing a literal `…/` placeholder that the owner pasted verbatim — and only then was the file written straight into the repo, after which every kit landed first time. **RULE: before instructing the owner to do manual work, check whether a connected capability already does it; and never hand over a command containing a placeholder that looks like a path.** Kin of F-135/F-141 — the toolchain, not the canon).

**6. Process, recorded because the discipline is worthless if its misses are not.** Two of three kits had a projection that missed: SL6 projected 270 and measured **274**, SL7 projected 286 and measured **287**. Neither was a behavioural surprise; both reconciled exactly against the test block (`ck(` occurrences minus the `ck(False, …)` guards that sit inside `try` blocks and never execute). **The cause was the assistant counting his own new checks by eye, and the fix adopted mid-session is procedural: count the block programmatically BEFORE running.** Both kits shipped with the **measured** figures, never a retro-fitted projection. Against that: **all three installs landed first time, each selftest hitting its stated number on the box, with no rollback and no incident.**

**7. Also this session:** the `.gitattributes` fix published (F-152), and two stray binary zips plus a `_to_delete` folder cleared from the repo root by the owner — binaries in the working tree being what truncated the S157 repo dump (F-55).

**8. The close.** Archive v1.42 → **v1.43** (this section; pure append, the 786,212 bytes before it proven byte-identical by direct comparison) · Fault Register v2.31 → **v2.32** · Register v5.39 → **v5.40** (all three live pins; D332 progress; findings; lineage; reverse-application-proven) · Runbook v127 → **v128** · START_HERE → **193** · manifest rebuilt · pin list regenerated LAST from v5.40 (A8) · **cold kit TAKEN** (was 3 of 3–5 and due). Three docs written during the session and filed: `S192_SL5_Live_Pin_Record.md` (pins recorded as they moved), `S192_Gated_Data_Corrections_Executed.md`, `S192_F6_Design_and_Survey.md`; the S192 opening note deleted, its work done.

**Still on the owner:** scan Darpan's signed application against row `0cc0b26b38c5` and approve it **before running the August close** if the ₹8,000 is to be collected this month (otherwise the schedule simply shifts) · the July salary close from the owner-side sheet, the waiver workflow's first real test · Darpan's introduction to the daily entry portal.

**Next free: D333 · F-155 · A-D25 · Session 193.** This was Session 192.

---

# §S193 — 20 Aug 2026 (Session 193, FULL build EOS — F6 live and F-148 closed, the discount column shipped forward AND backfilled, the cash-position view built over four passes, D333 minted; the monolithic canon fold deliberately deferred)

*(Folded into this Archive at the S197 fold-in — the S185 precedent. The session's own close artefacts — `S193_Close_Summary_and_Pins.md`, `HANDOFF_RUNBOOK_2026-08-20_Session193close_v129.md`, `START_HERE_SESSION_194.md` — are the sources; nothing here is from memory (D172).)*

**A long build session, entirely on the Sanjeevni (medical) finance surface.** Thirteen kits shipped (one deliberately SKIPPED and folded forward), every install GREEN.

**1. F6 (F-148) + F-153 — LIVE (`S193_F6`).** The drawer→ledger bridge, the S192 close's first task, built exactly as the S192 design ordered: **the seeded store FIRST** (F-87 — `finance_app.py`'s smoke could not run offline until this session built `seed_live_shape.py` + `migrations_concat.sql`, the harness that then served every later finance kit). Approving a Sanjeevni day that carries a salary advance now posts an `ADVANCE_ISSUE` to the Staff Ledger **through the ledger's own writer** — fail-loud, idempotent, ordered. Ledger selftest **287 → 289**; finance smoke **550 → 555**. The F-153 one-line gap (`make_contra` dropping `against_month`) was bundled into the same kit: `staff_ledger.py` `44e39d6a…` → **`acd7b538ec9476f86e243c73eec3d3fd`**. **F-148 CLOSED. F-153 CLOSED.**

**2. F-155 — the applied-status truth (`S193_F155`).** A Marg push had reported **"✓ applied" while the day carried no ingested bills** (17-Aug read applied with empty books). Now a run is "applied" ⟺ **every day it carries actually ingested**; otherwise it stays `pending` with its payload kept for replay. Smoke 555 → 557. *(F-155 was the canonical next-free number and S193 consumed it — the fork this made is reconciled in the S197 fold note under §S196.)*

**3. The discount column — LIVE + BACKFILLED (`S193_DISC`).** Per-bill **Gross · Disc · Net** in the Marg bill drill, for new pushes AND all history. Gross is **stored, never computed** — Marg rounds the net, so gross ≠ net+disc for 1,312 bills and a computed gross would be wrong. The adapter reads gross/disc **directly from the CSV row**, not via `ingest_column_map` (whose `our_field` CHECK allows `discount`/`tax` but not `gross`). Historical backfill two-pass: PASS 1 exact `source_ref==bill_no` (Marg-push days), PASS 2 by net-amount in bill order for the S186/F-104 synthetic-ref days. **3,141 bills filled across 124 days**; 16–19 Aug recovered from the medical-PC `SENT\` folder over the device bridge — *recover from what the system already kept*. Five-file chain: schema ALTER (`sale_item.gross_p`/`disc_p`, idempotent; the live `finance_schema.sql` file itself NOT swapped — repo reference `finance_schema_S193.sql` carries the CREATE for fresh installs), `marg_report.py` → **`6411a57d4517e0a06a02e1045b354138`**, `finance_ingest.py` in-place patched → **`a4e9663f9be1c138293d6dd8311577d0`** (built against the two exact live regions, verified by reconstructing live and hashing — *when the repo is behind the box, import by hash and patch in place*), `finance_app.py`, `finance_approvals.html`. Data fact recorded: **~₹70k of discounts across 1 Apr – 19 Aug previously invisible in reconciliation**; the 85→109 unmatched are net-₹0 give-away bills (never stored) + genuinely empty days.

**4. Stale not-filed flag self-heal (`S193_STALE`, F-156).** `MARG_DAY_NOT_FILED` was written at push time and never cleared — 17-Aug stayed flagged after its books filled. The Hub note now hides any such flag for a day that has a Marg batch: display-only, self-healing, no row deleted. **F-156 CLOSED.**

**5. The cash-position view — LIVE, four passes (`S193_CASHPOS` → `_2` → `_3` → `_4`), and D333 MINTED.** New `/finance/api/cash-position` (maker+checker): Darpan's **drawer** = `v_cash_ledger` closing − parked; **reserve (Dr Bhawna)** and **Dr Manoj** from `cash_custody_event`; bank deposits from `cash_movement`. New Hub "Cash position" card — loud stat tiles, every line tap-to-expand to its detail, drawer day-wise **since the last clearing**, fetch cache-busted. At close: drawer ₹65,697 (17 Aug 33,401 → 18 Aug 50,573 → 19 Aug 65,697) · reserve ₹1,56,235 · Manoj ₹18,963 · unbanked ₹2,40,895 · banked ₹15,70,600 (15 deposits; last 30 Jul). The four passes each fixed a found fault the same day: **F-157** — custody balances returned as comma-formatted strings, the client's `x.held>0` became `NaN>0`, every hand filtered out, the Cash-custody box empty **from the day it shipped** (parse to number for maths, format for display). **F-158** — day-wise drawer subtracted the *current* reserve from every historical closing, false negatives back to mid-July (the window starts at the last clearing — *a derived figure is only meaningful over its valid window*). **F-159** (assistant delivery fault, recorded not silent) — a correct endpoint fix appeared unfixed for two rounds because **Chrome served a cached API GET**; fixed `?_=<ts>` + `{cache:"no-store"}`, and the server was verified directly by reading the live API in the owner's own Chrome before shipping — *the browser is part of the system*. All three CLOSED the session they were raised.

### DECISIONS — D333 (S193; the cash-position accountability model), full text

**D333 — where the cash is, reconciled, for both Darpan and the owner.** **Drawer (Darpan) = `v_cash_ledger.closing_p` − reserve − with_manoj.** Reserve (Dr Bhawna) and with-Manoj come from `cash_custody_event` (the counted position; the daily flow records no hand-overs to them yet). Bank deposits from `cash_movement(party='bank', out)`. **Invariant: drawer + reserve + manoj = unbanked.** The old "₹33k float" is Darpan's uncounted drawer cash (owner confirmed he holds the 17th's cash) — not a mystery. Day-wise drawer is meaningful only FROM the last clearing (`MAX(cash_custody_event.event_date)`); before that the reserve did not exist. Forward direction: once hand-overs to Bhawna/Manoj are entered as `cash_movement`s, the reserve tracks live from the flow *(built at S194, kit `S194B`)*.

**6. Darpan's 18-Aug day — RESCUED, not deleted.** The owner asked to delete a "second draft"; the DB had ONE entry (id 124) holding the day's 22 Marg bills — deleting it would have cascaded ₹25,176 of sales away. It was a complete day left in `draft`; the owner was guided to fill (23,879 / 6,707 / 17,172) + reason-for-scans → File → Approve. Now `approved`. *Don't delete what holds live data — the fix was to finish it.*

**7. Daily Sale v2 — PROTOTYPED + APPROVED.** Clickable prototype delivered and OK'd; the live `POST /finance/api/day` contract mapped (transfers ride in `movements`). To be built as a NEW page at its own URL, the current page kept as fallback — built at S194. Design + contract: `S193_Daily_Page_v2_and_Backlog.md`.

**8. Findings.** **F-155 used · F-156 · F-157 · F-158 · F-159 minted — all five CLOSED the session they were raised.** F-148 and F-153 closed by kit `S193_F6`. **D333 minted.**

**9. Final live pins at the S193 close** (each recorded as it moved, F-97): `finance_app.py` **`4c0a2d19734e3860ed3d172191b2e7ff`** (chain: `17e6b84c`(S190_F5) → `9b1afe4f`(F6) → `d455e1aa`(F155) → `d86745b7`(DISC) → `51245f8b`(STALE) → `fa87fd40` → `18d2f8a7` → `4c0a2d19`(CASHPOS3); CASHPOS4 was html-only) · `finance_approvals.html` **`8ce3fabd3f712d99456d60ddbf6f4e1c`** (…→ `ea874fec` → `2e3b40cc` → `0a786f20` → `44a0401f` → `8ce3fabd`) · `marg_report.py` **`6411a57d…`** · `finance_ingest.py` **`a4e9663f…`** · `staff_ledger.py` **`acd7b538…`**. Kits: `S193_F6` · `S193_F155` · `S193_UX` · `S193_TOOLS` (dr_query) · `S193_MPC` (`SEND_TO_CLINIC.bat` v3) · `S193_DISC` · `S193_STALE` · `S193_CUST` · `S193_CUST2` (SKIP — folded into CASHPOS) · `S193_CASHPOS`…`_4`.

**10. The close, and the honest caveat.** Runbook v128 → **v129** · START_HERE **194** · `S193_Close_Summary_and_Pins.md` filed. **The monolithic Register/Archive/manifest fold was deliberately deferred** (Runbook v129 §4): canon too large to rewrite at the tail of an exhausting build session — the S193 state captured completely in the close docs, the mechanical fold flagged as owed, not skipped. *(That debt grew to four sessions and was cleared at the S197 fold-in — this append.)* Owner residual: `PUBLISH_ALL.bat` · on-box pin-list copy · delete repo-root `_to_delete/`.

**Next free: D334 · F-160 · A-D25 · Session 194.** This was Session 193.

---

# §S194 — 20–21 Aug 2026 (Session 194, FULL build EOS — all five backlog stars LIVE in one session: Daily Sale v2, home-medicine, the reclass log, live hand-overs, the email query agent; NO decision minted)

*(Folded into this Archive at the S197 fold-in. Sources: `S194_Triple_Feature_Live_Pins.md` + `S194_Addendum_S4_S5_Pins.md`; pins were recorded as they moved (F-97) and the canon fold was owed forward.)*

**All installs GREEN, first pass except `S194D` — whose gate correctly refused because `S194C` was already live (the D317 chain working; reissued as `S194E`, nothing touched).**

**1. Kit `S194` (⭐1/⭐2/⭐3).** **Daily Sale v2** — the approved S193 prototype built real at `/finance/daily` (two-stage flow: enter + save-gated submit → reconcile + transfer → final submit; transfer-only path; `/finance/entry` kept untouched as fallback). **Home-medicine auto-tag** — populated from the Marg export per the S193 ⭐2 ruling (no new manual scan for Darpan): `sale_item.home_med` (idempotent ALTER) + `/finance/api/home-medicine` + Hub card. **Cash/UPI reclassification log** — on re-import, each bill's mode is snapshotted BEFORE `ingest_day`'s delete-reinsert, compared to the incoming mode, and flips (both directions) written to the new **`mode_change_log`** table + `/finance/api/reclassifications` + Hub card — Amir's cash→UPI conversions finally visible, automatically.

**2. Kit `S194B` (⭐4) — live doctor hand-overs.** `api_cash_position` now computes **reserve/Manoj = custody baseline (`cash_custody_event`) + net `cash_movement`(dr_bhawna / dr_manoj, out−in)**, and **unbanked = drawer + reserve + manoj** (not raw closing) — a hand-over recorded on Darpan's page moves cash drawer→reserve live, without double-counting; the D333 invariant preserved. Smoke 569 → **571 (+2 exactly)**. No schema change, no data write.

**3. Kit `S194C` — the switch.** `/finance/` and Darpan's tile now open `/finance/daily`; scan back-links → `/finance/daily`; and the daily page **RELOADS a saved day on return and on date change (`loadDay`)** so a scan round-trip can't blank the form and wipe expenses — the D330 draft-wipe hazard closed on the new page too. `finance_daily.html` `e1092757` → **`7ac94934faf2d4434e4b81974526f0b0`**.

**4. Kit `S194E` — Marg auto-replay.** `_replay_pending_marg_for_day()` hooked into the day-save: **the moment a day is filed, any PENDING Marg push carrying it is ingested** (payload kept per F-155). Proven end-to-end offline; smoke 571 → **573**. This closes, going forward, the diagnosed gap (below).

**5. The Marg < Darpan's-sheet diagnosis, logged.** Darpan's sheet is NET (after discount), so the gap was real: bills that never linked because the Marg push fired **before** the day was filed (push result `ingested:[], still_not_filed`). 19-Aug: day ₹44,120 = full 30-bill Marg; only 23 bills (₹41,554) linked; the 7 missing (₹2,566) = the gap. Auto-replay prevents this class; the already-pruned 17/18/19-Aug payloads (pre-F-155) were re-loaded from the `SENT\` exports at S195.

**6. Kit `S194_EMAIL` (⭐5) — the full-auto email query agent, LIVE.** `/root/deploy/email_agent.py` → **`96cd7b75f9c7c57221f4112d5facd2b4`** + systemd `email-agent.service` (oneshot `--once`) + `email-agent.timer` (every 3 min, enabled). Config `/root/deploy/email_agent.json` (chmod 600; the Gmail app password on-box only — never in chat or repo; `email_agent.example.json` is the repo template). Behaviour: IMAP as `drmka.ortho@gmail.com`, searches **UNSEEN SUBJECT "Q:"**; for each match FROM a trusted sender (drmanojkragarwal@ / drmka.ortho@) whose subject starts `Q:`, runs **read-only `dr_query`** and replies ONLY to the matched trusted address, then marks it seen. Non-matching mail untouched. Read-only + allowlisted-sender + router allowlist all selftest-enforced. Verified live: `Q: custody` → `handled 1 command(s)`, reply in ~5s. **The recorded candidate finding:** the first cut searched all UNSEEN and fetched **1,103 full messages per poll** — safe (never touched them) but slow and a Gmail-load risk; fixed by narrowing the IMAP SEARCH server-side to the subject trigger. *"Search server-side for the thing you want; don't fetch everything and filter."* Recorded at S194 as an *"F-160 candidate (owner's call to mint)"* — **minted at the S197 fold as F-163**, because S196 independently consumed F-160 before this candidate was ruled; the collision and its resolution are recorded in Fault Register v2.33, not silently renumbered.

**7. DB migrated (S194):** `sale_item.home_med` (idempotent ALTER) + new table `mode_change_log`. Nothing else.

**8. Final live pins at the S194 close:** `finance_app.py` **`d2863c30ed0d3cc23126c7da13d9fe9b`** (chain: `4c0a2d19`(S193) → `87cf4568`(S194) → `43d2b845`(S194B) → `45845f6c`(S194C) → `d2863c30`(S194E)) · `finance_ingest.py` **`6cb83302b022ca3d46a53b32011a7ddd`** · `finance_daily.html` **`7ac94934…`** · `finance_approvals.html` **`402fa7b263b86f75bfccc122f1a0ca37`** · `email_agent.py` **`96cd7b75…`** (→ `e535c4f8…` at S195) · `staff_ledger.py` unchanged `acd7b538…`.

**9. Carried out of the session:** re-load 17/18/19 Aug from the `SENT\` exports (done S195) · the 08-18 −₹20,599 check (resolved S195: corrected & approved at 25,176) · home-medicine history backfill (toolkit built + tested: `extract_home_medicine.py` + `apply_home_medicine_backfill.py`) · benign flags left (Sunday `clinic_holiday`, genuinely-empty `missing_day` 05-04/05-27). **NO decision minted** (feature builds executing D326/D333 designs). The canon fold debt carried forward.

**Next free: D334 · F-160 · A-D25 · Session 195.** This was Session 194.

---

# §S195 — 21–23 Aug 2026 (Session 195, FULL build EOS — the longest build session to date: the correction checklist, the credit-note sign fixed, the UPI statement chain filled, the bank-statement chain end-to-end, the Marg report router, the medical-PC resident watcher, the Marg-401 token crisis survived; the Auditor seeded)

*(Folded into this Archive at the S197 fold-in. Sources: `S195_Close_Summary_FINAL.md` (the close record) + the per-topic `S195_*` docs in project knowledge, which remain the detailed references — this section is the session narrative, not their replacement.)*

**1. What went live.**
- **The correction checklist** (self-closing) + Excel/WhatsApp/email/CSV handover for Amir; **Marg-vs-books at save** (A1), **honest cash position** (A2), **cash/UPI misclass with direction** (A3), **month check** (A4). Floored at `FINANCE_CORRECTION_FROM=2026-08-01`. Design + live pins: `S195_Correction_Checklist_Design.md` / `S195_Correction_Checklist_LIVE_Pins.md`.
- **Darpan's cash/UPI accuracy** surfaced on his own portal tile + save response.
- **The email agent hardened**: folded + RFC2047-encoded `Q:` subjects now recovered (it had been silently dropping any command longer than ~75 characters). `email_agent.py` → **`e535c4f8116abd2fe60b7fda334f33ec`**.
- **`marg_net_sql()` — the credit-note sign fixed in all THREE readers** (the 18-Aug fault, below).
- **The UPI statement chain FILLED**: GAS backfill loaded **163 statements** (medical 8→56, clinic 55, lab 50, back to 06-Jun). Verdict: the cash/UPI split has been wrong on **ONE day since 1-Aug (₹30, 06-Aug)** — **Darpan is accurate.** (`S195_UPI_Statement_Gap_Finding.md`.)
- **18-Aug corrected & approved at 25,176** (his copy AND Marg agree; the entry was short ₹1,297 — he had counted right); 20-Aug approved; 21-Aug applied.
- **The bank-statement chain end-to-end**: `Bank_Statement_Relay` (personal GAS, daily 07:00) → `Bank_Statement_Filer` v3 (clinic GAS, daily 07:00) → archive + both accountants (Hemant Mourya, Shyam Agarwal) + Amir (Sanjeevni, per-attachment 1923/9819). (`S195_Bank_Statement_Chain.md`.)
- **Two inboxes janitored** (personal Inbox Janitor v2.3 fix `3be9bb77…` + the new `Clinic_Janitor`, `cjSetup()` done).
- **`Renewal_Nag`** — persistent escalating renewal reminders replacing easily-swept calendar pings (personal GAS; armed, first fire ~6-Sep). *(Became the S196 renewals health line's feed via v2.)*
- **NEFT monthly automation** (`Neft_Draft`, clinic GAS): draft on the 1st, finals to Amir on the 25th; the Aug draft + July finals already placed. Requirements doc `Accounts_Monthly_Requirements_v1_2026-08`.
- **The Marg report router**: **5 self-classifying types** (sale, closing stock, expiry, supplier-wise + bill-wise purchase), `margpull/signatures.json` **`1b21f3bf582d9f19fb8959a5336b0ba0`**; `margpull/` mirrored to the repo (it had been a single point of failure). (`S195_Marg_Report_Router_Design.md` / `S195_Club3_Router_Signatures.md`.)
- **The medical-PC resident watcher** — overwrite-proof capture of Marg exports (Marg overwrites `REPORT_1.XLS` every run), watching `D:\MARGERP\users` + `D:\MARG REPORTS`, autostart via the Startup folder, **portable bundled Python** (the medical PC has no system Python — a Store stub; standard adopted: bundled `pyportable`, full paths, never a system install). Raw mirror of `D:\MARG REPORTS` → `margsync\marg_reports_mirror`. Sole reference: **`S195_Medical_Watcher_LIVE_Reference.md`**. On manojz: scheduled task "Marg pull from medical" every 10 min (`PULL_FROM_MEDICAL.bat AUTO`) — captures + identifies every export into `margsync\MargArchive` (named by the business date INSIDE the file) + `index.csv`, mirrors the medical working folder, and offsites to Drive (`H:\My Drive\Clinic Data Archive\MargArchive`).
- **Publishers hardened** (stale-git-lock self-clear — the F-124/F-131 family closed at the tool). **The Auditor seeded** (`AUDITOR_SEED_v1.md`) — scheduled at S196.

**2. THE MARG-401 CRISIS (`S195_Marg_Push_401_Incident.md`).** The medical-PC push began answering **401**: `FINANCE_MARG_TOKEN` had lived somewhere transient, so a service restart killed the sender. Fixed durably: the token now declared in `/etc/systemd/system/clinic-finance.service`. **Both `FINANCE_MARG_TOKEN` and `FINANCE_CRON_TOKEN` transited chat during the diagnosis (21-Aug) — rotation owed and still the highest-severity open item at the S197 fold** (the cron token also lives in GAS "UPI Reconciliation" Script Properties). The crisis lesson — *a page can be red while the glance surface stays innocent* — drove the S195 health surfaces and finished landing at S196 (HLT2, the tile headline).

**3. The health surfaces (`S195_HEALTH`).** `GET /finance/health` (checker) + `/finance/api/health`; `api_tile_meta` — a red check replaces the checker's portal tile subtitle, reaching the portal home with no portal change; `FINANCE_FILING_DUE_HOUR` (default 12) — yesterday is "today's job" until then; **flags are `info`, never `warn`** — they always exist, and letting them drive the tile would turn the warning into wallpaper. Checks: Marg push freshness + pending applies · days filed (Sundays skipped) · books vs last physical count · flags · newest verified backup. *(The S195 close recorded the A4 month-vs-Marg check as done; S196 found both A4 cards had died into their `except` on every render — F-162 — and `_health_headline()` consumed by nothing — F-161. Both in §S196.)*

**4. Faults found & fixed — the session's real lessons** *(recorded unnumbered at S195; minted at the S197 fold as F-164…F-168 — see Fault Register v2.33)*:
- **The credit-note sign** counted twice in 2 of 3 readers → the 18-Aug "23,879" phantom that nearly reversed a correct correction (`S195_Credit_Note_Sign_Fault.md`). Fixed: one `marg_net_sql()` authority. **(F-164)**
- **Repeated rollbacks, one root habit**: asserting against shapes not printed — an invented fixture, guessed JSON, a self-matching search string, reserved `$args`, a mis-diagnosed encoding. Remedy adopted: `pyflakes` + `tools/check_late_locals.py` + `tools/check_row_keys.py` before packaging any kit; **never assert against an unprinted shape.** **(F-165)**
- **The 8-of-90 blind monitor** — a clean checklist meant *no bank data*, not agreement; the health page's UPI-evidence line is now the coverage witness (D166/F-99 applied again). **(F-166)**
- **The medical PC had no system Python** (Store stub) — the whole watcher-install saga; the bundled-portable standard adopted. **(F-167)**
- **manojz cannot write to the medical PC** (read-only share) — every "push to medical" feature had assumed an OS-forbidden write (`S195_ToMedical_Pipe_Broken.md`). **(F-168 — OPEN pending the owner's Drive-for-Desktop install.)**
- Two F-106-shape test lessons, fixed in place: three checks asserting the month's non-cash was EXACTLY "350.00" went red the moment Darpan filed the first real no-payment bill (now they assert the rule, and the tile check asserts tile-agrees-with-endpoint); the router selftest used a real report name as its "unknown" example and went red when that report was onboarded. **Tests must describe rules, not snapshots.**

**5. Owner decisions recorded at the close (22–23 Aug):** (1) **token rotation PARKED to next session** (both exposed tokens still live); (2) **the 17-Aug ₹20,000 → Staff Ledger only against Darpan's written, scanned application** — not yet actioned, the drawer stays off ₹175,201 until then; (3) **the medical delivery pipe**: the owner will install **Google Drive for Desktop on the medical PC**, making ToMedical a mounted-drive local copy — the medical-side puller build DROPPED.

**6. Also this session:** backups proven — cron `5 1 * * *`, verified nightly, **restore proven** (126 days, 3,141 items). `GUARD_AND_SEND.bat` — the medical PC's ONE icon (finds by content → guards → sends → parks failures in `NEEDS_UPLOAD\`); `find_sale_report.ps1` in its own file (cmd mangled the escaped pipes inside a batch if-block and it silently found nothing); `marg_export_macro_v3.ahk` PARKED pending AHK v2. Monthly-cycle discovery + pending work clubbed into `S195_Monthly_Cycle_Map_and_Backlog.md` / `S195_Pending_Work_Clubbed.md`; the Marg `.dbf` encryption finding + partial key, the Docterz/Personal-GAS evaluations, the drawer-investigation gaps, the credit-note fault, the retention policy (`Clinic_Source_Data_Retention_Policy_v1.md`) all filed as their own docs.

**7. Final live pins at the S195 close:** `finance_app.py` **`df75024392e31ae99bb3fde9fab24062`** · smoke **654/654** (chain: `d2863c30`(S194E) → `85df28fe`(ENTRY) → `f25ed489`(NCSCAN) → `fe596b29`(HEALTH) → `89ab3e8e` → `e3a4ba79` → … → `df750243`(SIGN)) · `portal.py` **`ff08980737c107c3babb78b0c5c169c2`** (Club2; portal gate 26/26) · `email_agent.py` **`e535c4f8…`** · `finance_daily.html` `20efc5caa664c9b96be23bb66866d21c` · GAS: `VPS_Push_UPI` v2 **`fac84c5b4a5a14b6345d4cce52c1ad39`** · Inbox Janitor v2.3 `3be9bb77…` · `Bank_Statement_Relay` + `Bank_Statement_Filer` v3 + `Clinic_Janitor` + `Renewal_Nag` + `Neft_Draft` live · `margpull/signatures.json` **`1b21f3bf…`** · the medical-PC watcher LIVE, resident, autostart.

**8. The close, and the fold-in debt named.** The canon stood folded to S192 with S193/S194/S195 as standalone close docs; the S195 close ruled — correctly, per D247/F-23 — that **bolting three sessions of change onto a stale canon at the tail of an exhausting build session is exactly how a stump/delta fault gets made**, and flagged a dedicated EOS-light fold-in session instead. *(Executed at S197 — this append.)* Owner-set S196 priorities: attendance/salary self-service first · the renewals health line · start the Auditor · carry-overs (token rotation ⭐ · the ₹20,000 ledger entry · Drive-for-Desktop · Labmate sample · the fold-in).

**Next free: D334 · F-160 · A-D25 · Session 196.** This was Session 195.

---

# §S196 — 23 Aug 2026 (Session 196, FULL build EOS — attendance self-service + the portal-health plan finished: six kits, six first-pass GREENs, each landing exactly on its written projection; D334 owner-ruled; the weekly Auditor scheduled)

*(Folded into this Archive at the S197 fold-in. Sources: `S196_Close_Summary_FINAL.md` · `S196_Attendance_SelfService_Build_State.md` · `S196_Health_Renewals_Build_State.md` · `HANDOFF_RUNBOOK_2026-08-23_Session196close_v130.md`.)*

**1. Kit `S196_ATT1` — staff self-service.** New portal role **`self`** mapped to staff rows (`staff.username`; `--map-usernames` printed all 12 clean); a today-only **"My biometric"** page (`/register/me`): today's date + punch times, **nothing else** (owner leakage ruling). **Mark-me-present**: same-day only · refused if a machine punch exists · one per day · reason required · **the server receipt time IS the punch time** (the phone clock is never trusted; late bands run off it — *self-policing beats policing: delaying a request costs exactly what punching late costs*) · Shavez verifies (never his own) · counts only on Dr Manoj's approval · "#N this month" visible on the board. Out-punch stays on the machine. **Machine late minutes in the day grid**: ≥60 min shows exact minutes as a loud read-only badge stored in `daily_register.late_minutes`, form-proof; sub-60 stays quiet; Sundays via the transcribed D253 roster. `att_month_report` **v2.6** folds APPROVED requests as synthetic punches (`*` in the grid), fail-soft to v2.5. Seven staff logins created by the owner (awdhesh, pravesh, ranjeet, sukhveer, sandip, vikki, surendra); **nothing for Arjun (ruling)**. `staff_register.py` `cef76859…`(S164) → `c2059ea1…` → and with ATT2 **`9087954c8a4a891e8cdd848d6a9d48b2`** (v0.4); `att_month_report.py` `e64cad19…`(v2.5) → **`9ab98313bbda7ae5555fb4b5a5a82c4b`** (v2.6).

### DECISIONS — D334 (S196, owner-ruled; minted at the S197 fold), full text

**D334 — the present-request policy.** A staff member with no machine punch may request to be marked present, under five binding rules: **(a) request-time-as-punch** — the server's receipt time IS the punch time; the phone clock is never trusted; late bands run off the server time, so delaying a request costs exactly what punching late costs and there is nothing to gain by gaming it; **(b) same-day only** — no retrospective requests; **(c) the no-punch guard** — a request is refused outright if a machine punch exists for the day; one request per day, reason compulsory; **(d) verify-then-doctor** — Shavez verifies every request (never his own; his own go straight to the doctor), and the request **counts only on Dr Manoj's approval**; **(e) month-count visibility** — "#N this month" renders on the board beside the name, so frequency is visible where approvals happen. The out-punch stays on the machine. Approved requests reach the salary layer as synthetic punches (`att_month_report` v2.6), marked `*` in the grid, fail-soft to v2.5 if the request store is unreadable.

**2. Kit `S196_ATT2` — the PWA.** The self page is installable: manifest + the real clinic-logo icons (**extracted from the live S187_H1c Hub bytes** — the Canva host is unreachable from the sandbox), linked on the self page only; **NO service worker, nothing cached**; `self` sessions ~180 days; "Add to Home screen" = the app.

**3. Kit `S196_HLT1` — the renewals line.** The personal Inbox-Janitor GAS wrapped as **`Renewal_Nag_v2.gs`** (trigger + emails identical, now ALSO pushes every daily run) → one-path token **`FINANCE_RENEWALS_TOKEN`** (its own secret, fail-closed; **wired by the owner on the box, never in chat**; end-to-end proof = `bad_payload` with the real token) → JSON state file → health card: OVERDUE bad · stale-feed warn · ≤7d warn (reaches the tile) · ≤30d info · no-feed quiet info. Days recomputed from dates at render. **LIVE — first push landed 11:01.** *A reminder system's own death must be loud: the push runs daily even when quiet, precisely so "feed stale" can fire when the pusher dies.* Smoke 654 → **665/665** on projection.

**4. Kit `S196_HLT2` — the crisis lesson's last inch (F-161 closed).** `tile-summary` now carries `health_line`; **the Sanjeevni portal tile shows the worst problem FIRST**, unchanged when all is clear. The finding it closes: S195 had built `_health_headline()` *"for the portal tile"* and **nothing ever consumed it** — page red, tile innocent; found by reading the live bytes when the owner asked "is the crisis lesson fully taken care of?" — *a capability without its wire is a claim; grep for the CONSUMER, not the definition.* `portal.py` `ff089807…` → **`ee749cd9f3ac1294aab0d13ce069efc1`**. Smoke 665 → **667/667**.

**5. Kit `S196_HLT3` — A4 revived (F-162 closed).** The owner's first real read of the live health page caught *"This month vs Marg — could not be read ('datetime.date' object is not callable)"* — the F-132 pattern, a human looking beating a green suite. Root cause in the S195 baseline: `_health_state` set a local `today = dt.date.today()` which **shadowed the module `today()`**, so **BOTH A4 cards died into their `except` on every render since S195** while the S195 close recorded the check as done. Fix: one line, plus a **class-refusing smoke check** — no health card may ever be a swallowed Python exception (*a check that displays its own exception has died, not degraded*). `finance_app.py` chain this session: `df750243…`(S195) → `cfacce27…`(HLT1, 654→665) → `6fc3becc…`(HLT2, →667) → **`388c8ac0fdfecdee6029c0033b9b0ef8`** (HLT3, →**668**). Both A4 cards alive for the first time since S195.

**6. The Auditor SCHEDULED.** Weekly unattended cloud run, Mondays ~07:05 IST, trigger `trig_01XBRt7dcsXcjtmgdmemnR3x`, seeded from `AUDITOR_SEED_v1.md` + unattended adjustments (slice rotation from `AUDIT_RUN` docs; **AF-# numbering, so the Auditor never mints bare F-numbers**; an owner-commands section instead of pause-for-paste; push + email summary). First firing 24-Aug = slice 1 (cash trail) calibration.

**7. F-160 — the kit delivered OUTSIDE the git tree.** A kit landed at `D:\dr-manoj-git\` when the real repo is one level deeper (`…\drmanoj-clinic-automation\`): the publish destination was **assumed from the connected-folder root instead of read from `PUBLISH_ALL.bat`'s own `REPO_DIR`** — PUBLISH pushed without it, the VPS pull had no kit. Remedied the same hour by `mv` + full re-hash, byte-identical. F-135/F-141 family: *the publish destination is read from the publisher's config, never assumed.*

**8. Verification discipline this session.** Every kit: hash-verified base bytes (repo == pin for ATT1; **kit-tarball hash-recovery** for HLT1/HLT2 — the repo `finance/`/`portal/` trees are S180/S182-stale) · offline pre-flight (`py_compile` · `pyflakes` · `check_late_locals` · `check_row_keys`) · **the finance smoke's first-ever OFFLINE runs** via the reconstructed S193_F6 seeded-store harness — differentials +11/+2/+1, every one exact, fail-sets byte-identical; the HLT1 differential caught a request-context fault in the session's own test code before the box could · installers rehearsed (ATT1 end-to-end including the refusal path) · six on-box installs, six first-pass GREENs (654→665→667→668 finance; att + register suites grown and green).

**9. The close.** Close summary + Runbook **v130** + START_HERE **197** + the two build-state docs written to project knowledge AND committed into the repo tree (`deploy_kits/KB_canon_S196close/`, SUMS.md5 covered). **The F-SERIES FORK flagged for the fold-in to reconcile FIRST** (canonical next-free F-155 vs S193's F-155–F-159 vs S196's F-160–F-162), with a freeze on new bare F-numbers until reconciled. Owner residual: one `PUBLISH_ALL.bat` double-click (done — the S197 Phase 0 found the commit landed 11:24 IST). Pending owner jobs carried: **token rotation (⭐ highest severity, aging since 21-Aug)** · Darpan's application scan → approve `0cc0b26b38c5` before the Aug close · the 17-Aug ₹20,000 ledger entry · file 21-Aug (auto-replay then loads its pending 37-bill Marg push — F-155 behaviour, not a fault) · the 18-Aug 8-bill attribution · the correction-checklist day + 4 UPI/bank disagreement days · the July salary sheet · staff-phone PWA installs · Drive-for-Desktop on the medical PC · the Labmate sample export.

**Next free at the S196 close: FROZEN pending the fork reconcile (D334 reserved).** This was Session 196.

### S197 FOLD NOTE (23 Aug 2026 — the fork reconciled; this append)

Executed at the S197 fold-in, owner-delegated, before any other S197 work: **the F-series fork is resolved in favour of every number already in circulation.** (a) **F-155–F-159 are S193's** (F-155 consumed the canonical next-free; all five closed the session they were raised). (b) **F-160–F-162 are S196's** as written — no S194/S195 doc had used a bare F-160+ token, verified by sweeping both the repo and project knowledge. (c) The one collision found: S194 had recorded its email-agent over-fetch as an *"F-160 candidate (owner's call to mint)"* — **minted as F-163**, keeping S196's circulated tokens intact; numbering is therefore not chronological across F-160–F-163, recorded not silent (F-108 family). (d) The five unnumbered S195 faults are **minted F-164–F-168** so the findings register carries them (leaving them doc-only would recreate the F-108 condition knowingly). **D333 (S193) and D334 (S196) minted into the decisions index. Next free: D335 · F-169 · A-D25.** Archive v1.43 → **v1.44** (§S193…§S196, this pure append) · Register v5.40 → **v5.41** · Fault Register v2.32 → **v2.33** · manifest rebuilt · `live_pins.txt` regenerated from Register v5.41 (A8 — the checker had been unprotecting since S193) · cold kit taken (due, 4 of 3–5 since S192).

---

# §S198 — 23 Aug 2026 (Session 198, FULL build EOS — the "club everything" day: EIGHT kits installed GREEN across portal, finance-health and gist; the complete offline purchase toolchain built and PROVEN on real July data; the NEFT vendor master + the Neft_Guard; D335 minted and SIGNED — the Purchase Portal is S199's flagship; F-170…F-173)

**The owner opened with eight jobs "to be clubbed, automated, to run as independently as possible":** (1) the Marg NEFT file + bank letter, (2) a portal Downloads section for printable clinic forms, (3) the accountant monthly pack, (4) Portal Health made clickable to exact fix points, (5) the WABA pending works (vendor active again), (6) every staff member's role-scoped portal as a PWA, (7) Darpan's ₹20,003 drawer surplus + the paper-application steps, (8) the portal home revamped (all tiles one screen, health as a tile). Mid-session additions: caller-details on staff mobiles (call-pop — finalised earlier, limitations accepted), the gist tile's extended functionality, and the Janitor output sheet + the Renewals sheet wired to the portal. Owner rulings: **Club 0 (the owner/Darpan money batch) moved to the END; the remainder first.** Club C (WABA works · call-pop · free-text blog replies) was surveyed into the backlog, not built.

## S198.1 — Club A: the portal wave (kits `S198_P1` → `S198_G1`, all installed GREEN, pins recorded AS THEY MOVED — F-97)

**`S198_P1` — the home revamp** (dark theme kept by owner preference; the health HERO + per-tile chips fed by the existing `tile-summary` fetch; compact tiles; a Staff group; PC-migration chips; a to-top button; call tiles seated together, GMB up, Case Pack after the WA cluster). Gate 127/127. **The v2 install went RED at the probe step — a REAL rollback on the live box — and the fault was the installer's, not the payload's (F-170):** the probe asserted HTTP 200/302 from `127.0.0.1:8090` but the box answers **301** to plain HTTP — for the old bytes and the new alike; the S196 installer had only *printed* the code, never judged it. v3 made the probes informational-only and moved the serves-proof to the app's own render path (importlib + `test_client`); installed GREEN. `portal.py` `ee749cd9…` → `dc093f1f…`.

**`S198_H1` — Portal Health becomes DOORS**: every health check now carries a link to its exact fix point (`#margCard` / `#pendCard` / `#cashPosCard` / `#stripCard` / `#monthCard` / `/finance/marg-worklist`) plus an act-line saying what to do there. Two of six new selftest checks were caught **state-dependent by the offline differential before sealing** (the month-grid/worklist links do not always render) and made conditional — the F-106 family stopped in the harness, not on the box. `finance_app.py` `388c8ac0…` → `4ae49536…` (smoke 668 → 674).

**`S198_P2` — Forms & Downloads** (`/portal/forms`; `FORMS_DIR=/root/portal/forms`; `_forms_safe` sanitizer; login-required viewing, doctor-required manage; gate 20/20). `portal.py` → `2a162ec4…`. **`S198_P3` — the Renewals tile** wired to the owner's Renewals master v2 Sheet. `portal.py` → `40b10a8b…`. **`S198_P4` — the portal is a PWA** (manifest + base64 icons on public routes; **NO service worker** — the ATT2 ruling; scope `/`). `portal.py` → `e2484429…`. **`S198_P5` — the duplicate tile removed** (Payment Register tile opened the same Sheet as Janitor; owner: remove it; config retained). `portal.py` → `43ec35b1…`.

**`S198_H2` — the owner's own live-eyes findings fixed the same day.** He found (a) the health list **claimed worst-first and had never been sorted** — the docstring said it since S195, no `sort` existed (**F-171**, the F-45 family in code); (b) the Marg-push age check was **Sunday-blind** — with everything filed to date it still said "Something is wrong" across a Sunday (**F-172**, the false-alarm class); (c) Renewals unclickable in the health tile. Fixed: `_sundays_between`, `checks.sort` genuinely worst-first, culprits named in the hero, the renewals door added. `finance_app.py` `4ae49536…` → **`2c99b2c6c719091deada5603fc295c90`** (smoke 674 → 680). *(A re-run of the H2 installer went RED expecting `4ae49536…` — that was the currency gate correctly refusing a duplicate install; the first run had succeeded. Verified from the box: md5 + SMOKE 680/680. No incident.)*

**`S198_G1` — the gist tile finally has content**: `compute_console(conn, today)` reads `console.db` (sole writer untouched) and renders three cards — funnel, staff-AI agreement, leads — into `GIST_HTML`; a live dry-run inside the installer. `portal_gist.py` `55e111d7…` → **`ef3ad196a00c2df44a7770553237a0e6`** (selftest 27); `portal.py` `43ec35b1…` → **`ab019dda3ac68e566de017c5ae536a6b`** (FINAL). *(Also this kit's delivery note first carried a hand-typed hash — caught pre-seal, note regenerated with every hash transcribed from `md5sum` output; the F-141 rule held.)*

**Final S198 pins: `portal.py ab019dda3ac68e566de017c5ae536a6b` · `finance_app.py 2c99b2c6c719091deada5603fc295c90` · `portal_gist.py ef3ad196a00c2df44a7770553237a0e6`.** Chains: portal `ee749cd9 → dc093f1f → 2a162ec4 → 40b10a8b → e2484429 → 43ec35b1 → ab019dda`; finance `388c8ac0 → 4ae49536 → 2c99b2c6`; gist `55e111d7 → ef3ad196`.

## S198.2 — Club B: the purchase/NEFT layer (offline, in `D:\dr-manoj-git\NEFT_Vendor_Master\` — OUTSIDE the git tree, vendor bank data, D320/F-31)

**B1 — the vendor master decides where money is authorised to go** (owner: "b1 decides where the money is authorised to go so its very important"). `NEFT_Vendor_Master_v1.xlsx`: **22 FY-2026-27-verified vendors** transcribed from the executed NEFT advice files via the Drive text route (18/18 per-file totals matched — transcription-safe), an **account-changes sheet** with month of change, and an **UNVERIFIED sheet** for every pre-April-2026 vendor absent from this FY's payments (owner rule: flagged for verification before any future payment). **The April-2025 advice file has its account column SHIFTED against its name column** — possible wrong-account historical payments — **F-173, OPEN**: the owner checks the April-2025 bank statement.

**The Neft_Guard** (`Neft_Guard.gs`, GAS in the "UPI Reconciliation" project; `ng_` prefix; `NG_SEED` 24 rows; pure `ng_classifyRows_` proven by a node harness on the shipped bytes, 9/9): daily 07:00 trigger reads any new NEFT advice in Drive and emails **only on problems** — an unknown vendor, an unverified vendor, or an account differing from the master. **D325 holds: the person signs and sends; the system never touches the bank.**

**B2 — the monthly toolchain, proven on the real July exports**: `make_recon.py` (parse of the Marg supplier-wise export with the fortnight h1/h2 split and a block-TOTAL refuse; NAME_MAP Marg→register; prev-carry chaining; `_regen` clobber guard) prefills the vendor reconciliation Amir signs — **July validation: 20/21 exact against the executed NEFT; the 21st was KEDAR, ₹310 — a genuine discrepancy flagged live**; AGARWAL SURGICALS (₹3,556, never NEFT-paid) surfaced. `make_billcheck.py` builds the staff-friendly bill-check workbook (vendor-grouped expandable rows, Correct/Wrong dropdowns, per-vendor subtotal + progress, a stats sheet) and **harvests corrections to `corrections_log.csv`** (vendor-context carry-down; dedupe) — every correction becomes data. Plus `RUN_RECON/RUN_BILLCHECK/LOG_CORRECTIONS.bat`, `RECON_SETUP.md`, and PROOF workbooks. **Amir's delivery pipe**: the owner installed clinic Google Drive on the medical and lab PCs; his files land via the `ToMedical` folder (the `H:\My Drive\Clinic Data Archive` grant, this session).

**A standing method lesson recorded loud:** re-emitting file bytes as base64 through model generation is **NOT viable** — twice attempted, both zips corrupted, both failures loud. The standing transfer method is the Drive **text route with per-file total verification** (it preserves exact account digits and leading zeros).

## S198.3 — D335 minted and SIGNED: the Purchase Portal (build = S199 flagship)

> **D335 — the Purchase Portal contract (S198 · 23-Aug-2026 · SIGNED · v8 final).** Full text canonical in **`S198_Purchase_Portal_Design_CONTRACT.md`** — *the 14-state workflow table IS the spec*; this index entry is a summary, not the authority. The entire monthly purchase-payment cycle becomes a portal-scoped, role-gated pipeline in stages **PP0–PP4**: PP0 report ingestion (bill-wise/supplier-wise land via the existing Marg capture pipeline); PP1 the bill-check done IN the portal by reception/Darpan (checkers); PP2 Amir's compulsory pass — corrections flagged correct/corrected, regenerate if needed, **final approval by Amir countersigned by Darpan, all online**; PP3 the payment pack — Excel with audit trail, approved by Shavez, owner's OK against physical bills attached to the final bill-wise printout; PP4 cheque + **prefilled bank letter** (only cheque number, date picker, amount prefilled) — print, sign, bank, `sanjeevni.bly@gmail.com`, Amir's Marg pack, accountant pack. **Owner rule: NO audit trail reaches the accountant or the bank.** **Phase 2 — the two-witness item layer**: scanned purchase bills (the asset-app + Sarvam intake, ~80/month) ingested into Marg's soft-copy purchase entry (₹3.5/bill) become witness one; the item-wise Marg purchase export (generated every Amir visit, ingested immediately) is witness two; granular item analytics (expiry, reorder, surplus, rotating physical stock audit) feed the Sanjeevni page and Darpan's portal. **Both trial gates are FAIL-SAFE**: if either trial fails, the manual flow stands and the data already earned keeps its value (Amir uploads scans with the physical bill in front of him; month-end sheets still come from the exports). Prerequisite owner action: the **first item-wise Marg purchase export from 01-08-2026** (expected to file under `_UNKNOWN` in MargArchive — the router has no signature for it yet; that is the Club-3 sample, NOT a fault).

## S198.4 — Findings minted this session (the mint call is the assistant's — the S191 precedent)

- **F-170 (S198 · CLOSED same session, installer v3):** an installer probe's expected HTTP code was asserted from assumption — never measured on the box, never printed by a predecessor as a *judgment* — and a healthy install was rolled back. Rule: **an installer probe's expected code is measured on the box or it is printed, never judged.** The F-106 family inside an installer.
- **F-171 (S198 · CLOSED, kit `S198_H2`):** the health page **claimed worst-first ordering it never performed** — the docstring promised a sort that did not exist, live since S195, found by the owner's eyes. The F-45 family (a claim outliving its implementation) in code.
- **F-172 (S198 · CLOSED, kit `S198_H2`):** the Marg-push age check was **Sunday-blind** and raised "Something is wrong" on a fully-filed system across a Sunday — a false alarm that teaches staff to ignore red. Age checks must count only expected-activity days (`_sundays_between`).
- **F-173 (S198 · OPEN — owner review owed):** the **April-2025 NEFT advice file carries its account-number column shifted against its names** — payments that month may have gone to wrong accounts. Surfaced by the B1 transcription pass; the owner checks the April-2025 bank statement against the vendor master.

## S198.5 — Close mechanics

Archive v1.44 → **v1.45** (this §S198, pure append). Fault Register v2.34 → **v2.35** (F-170…F-173). Register v5.42 → **v5.43** (the three final pins + chains; D335 into the decisions index; findings index; next free **D336 · F-174 · A-D25**). Runbook → **v132**; `START_HERE_SESSION_199`; manifest rebuilt; `live_pins.txt` regenerated from v5.43 (A8); the Notion page-per-session log (A9). Session docs filed to the repo (F-107): the five live-pin records, the owner cycle spec, the B1/B2 records, and the signed D335 contract. Cold kit NOT due (count 1 of 3–5 since S197).

---

## §S199 — Session 199 (23–24 Aug 2026, FULL build EOS): the salary-policy rebuild — "the system is not to punish, but to promote and reward"

**The session that turned one owner instinct — "the deduction logic seems too harsh for immediate application" — into a complete new salary system: designed clause by clause with the owner, built, installed through seven gated kits, and preview-tested on real July and August data before anything could touch pay.**

**Phase 0 (S199 open):** documents GREEN — the S198 canon kit verified 12/12 by SUMS, all five Tier-0 files hashing exactly to the manifest pins; the F-88 cross-check matched 226 of 242 manifest tokens against real repo bytes (the 16 unmatched each legitimately non-document: the three S198 live pins existing only on the box, the Club-B files outside the git tree, kit IDs, the D316 closed-as-lost rows). The live-pin run remained the owner's on the box.

**Act 1 — the scenario question.** The owner asked to see the notice-v6 deduction logic against the old ₹1/minute practice on real August data. The live bytes were recovered by hash (D188): `att_month_report.py` v2.6, `staff_register.py` v0.4, `salary_engine.py` — and a read-only scenario tool (`att_scenario.py`, kit `S199_SCEN1`) was built ON the live report's own functions so it could not drift, then wired into the portal behind the manoj/bhawna salary gate as a doored page (kit `S199_SCEN2`, `staff_register.py` → `c1fede9f…`). The first live salary-page view then tripped a three-session-old landmine: **F-174**, the ledger's `SALARY_EXCLUDED` having grown at S192 with no sweep of the engine's mirror — the D288 drift guard refusing exactly as built. Fixed same hour (kit `S199_SALFIX`, engine → `ca37c615…`).

**Act 2 — the one-time data look.** The owner shared the real figures as a ruled exception (used in-session only; nothing persisted to repo, canon or memory). The July provisional sheet decoded completely: LATE = ₹1 × raw late minutes — **matching the machine's raw-minute computation TO THE MINUTE for all ten staff**; LEAVE AMT = (leaves − 2) × base ÷ 30.5, symmetric (under-use credited — the reward instinct already alive in the owner's own practice); payable = base − advance − loan − late − leave. One row refused to reconcile: **Shivani, paid her full ₹8,600 against a computed ₹4,025 (≈₹4,575 gap) — owner check owed before the July final working.** The comparison verdict: the marks-slab system priced lateness at ₹2.5–4/minute against the old ₹1 (August: old ₹5,501 · ramp ₹7,683 · strict ₹9,392) — harsher exactly where the owner sensed it, and August marks averaging 23 marked the problem systemic, not individual.

**Act 3 — the rulings (the heart of the session).** Ideation → owner rulings, each absorbed the hour it landed: late money leaves the marks slab and reprices at each person's OWN salary minute-rate (base/(30 × shift minutes) — the flat ₹1 had been charging the lowest-paid staff ~3× their earned minute), **90 free minutes/month** over the 10-min×8 grace, bands ramping ×0.5/×1.0/×1.5, charges under ₹10 ignored; the **Improvement Hold** — 75% of any late charge held in the staff member's name and RELEASED on ≥30% improvement the next month ("it is not a fine, it is your own money kept aside"), waivable individual→all but deliberately not advertised in the staff notice; leaves stay full-day-rate symmetric with NO ladder ("don't penalise — excess day full day salary rate deduction stays"); duty times untouched, the arrival analytics an internal tool; dress/I-card ₹15/day-without as explicit Yes/No; incentive ≤5/≤8 marks — ruled at the close to the **annual Diwali pot (S163 kept)**, the notice corrected to match (v3); **every number a setting — "any resetting, we don't touch code, that's the plan"**; and above all: **"I need to be free at month end, and wrap up in 5 minutes."** The playground workbook (v1/v2, owner-side only) let the owner tune the levers on real data; the bilingual staff notice and the two-page salary-sheet print format were drafted, owner-edited (annexures out, waiver language out of the staff copy) and finalised as drafts v3.

**Act 4 — the Month-End Flow (D337) built and installed.** The owner specified the flow verbatim: machine-data Sheet 1 (attendance grid, staff viewing FIRST, remarks for review, override days visible) and Sheet 2 (advances + long-term loans + holds + all fines) printed together, both approved by him with corrections made THROUGH the system ("only for revisions I don't want to scuttle around — easy navigation should be available from here" → every fixable cell a DOOR, the S198_H1 pattern), then the final salary computed. Built as `salary_policy.py` (the D336 engine, settings-driven, PREVIEW standard) + register routes (kit `S199_FLOW1`): the flow pack, pack approvals gating the lock, the policy-settings page, `/me/month` with the remark loop and owner-set visibility windows (running month live; lock+5 days), the dress/I-card dropdown conversion and the **August migration executed live: 88/74 phantom ticks → 0, DB backed up (F-175 closed)**. The owner's first preview then caught **F-176** (the running day counted absent — all twelve staff "A" at 06:00) and drove the full design pass (kit `S199_FLOW2`): half-month grid blocks with punch times visible, month-in-words captions ("MACHINE DATA" vs "FINAL"), Darpan's separate money page with outstation, night-duty credited from the ledger, no totals rows, the min-charge floor, sticky navigation — plus the old salary page's shadow/delta columns and parity banner retired (`bedd468e…`).

**Act 5 — the Lock Desk (kit `S199_FLOW3`).** Owner rulings: the landing page becomes the lock desk ON the new engine; incentive to the Diwali pot. `/register/salary` now shows a readiness checklist (dates · Sheet 1 · Sheet 2 · enforcement · month ended) and a summary identical to Sheet 3; the **Lock refuses any month not covered by `enforce_from`** — a preview month locking deductions is now structurally impossible (the F-150 lesson made architecture); on lock it records the total, stores the FINAL sheets, and writes the hold ledger once per staff-month, re-lock-safe. Final pins: `staff_register.py` **`124c6eb2…`** (v0.7) · `salary_policy.py` **`7f86cc87…`** (v1.3) · `salary_engine.py` **`bedd468e…`** · `att_scenario.py` **`4dcd19bc…`** (v2).

**Process notes, recorded not hidden:** the first kit landed in a `deploy_kits/` folder BESIDE the repo instead of inside it (the F-160 REPO_DIR lesson relived from the cloud side; corrected, and the stale `.git/index.lock` blocking the commit — the F-131 recurrence — cleared to `_stale_git_locks_S199/` outside the tree). A whole-function replacement harness ate two route decorators during the lock-desk build — caught offline by the register selftest's route-200 assertions before anything shipped (the gates catching the toolchain again). Scenario v1's mislabeled months (**F-177**) were owner-caught and fixed in v2. Four findings, four closed same-session; **no incident** — every failure was caught by a gate, a selftest, or the owner's first look.

**Queued at close (Runbook §2):** the desk's missing Leaves/Absent columns + the fines legend · the **Arjun threshold ruling** (₹100 fine threshold flat-3 vs per-staff allowed_offs — a genuine two-threshold incoherence found by the owner) · the owner-advances entry on Sheet 2 (July worksheet + August figures + Darpan's pending ₹20,000 SPECIAL → the final working) · printable money sheets · the **selfie-punch ideation** (geotagged camera-only capture as EVIDENCE inside the D334 present-request flow; also the outstation tool) — held for a D-number. Owner items standing: **token rotation (aging since 21-Aug, highest severity)** · Shivani's July row · serving the notice · the enforce_from decision.

---

## §S200 — Session 200 (24–25 Aug 2026) — THE GO-LIVE SESSION: July locked on the new engine (₹59,163); nine decisions; twelve kits; the PWA unified

**The session in one line:** the owner's "⭐0 salary items" pick became the system's graduation — every remaining July question ruled, the D336 engine upgraded to the owner's final shape, the whole flow walked end-to-end on real data, and **July 2026 LOCKED at ₹59,163 on 2026-08-25 07:16:48** — the first month the system carried by itself. The owner's stated purpose held throughout: *"the reason for this july juggling is not money, its actually testing a system we are developing with the goals we have set."*

### 1 · Phase 0 — GREEN (all checks; F-88 254 tokens / 238 matched, 16 accounted; F-119/F-123/F-107/A8 clean)

### 2 · The morning's money work (owner taps, assistant navigation)
- **Shivani's July row ruled A SLIP** (not a waiver); recovery FULL in August; exact figure deferred to the VPS sheet (later computed exactly: see §7). Her separate **₹3,000 extra advance PARKED to August**.
- **August advances entered live** with two correct D331 gate firings: Surendra ₹10,000 in four tranches (Shavez's ₹8,000 PENDING row rejected and re-entered as dated tranches, ₹2,000/mo; the 10/8 ₹2,000 separate, full-Aug), gate refusal at ₹7,000-vs-₹5,200 fixed by future-month attribution; Ranjeet ₹6,000 split ₹5,000 Aug + ₹1,000 Sep after his ₹5,000-ceiling refusal; Sukhveer ₹6,000 Aug + ₹4,000 Sep (owner's no-paper split). Recovery map: Surendra 4k/2k/2k/2k · Ranjeet 5k/1k · Sukhveer 6k/4k.
- **Darpan's ₹20,000 SPECIAL** (0cc0b26b38c5) still PENDING on the signed application — owner action before the August close.

### 3 · D338 (kit S200_R1, GREEN first pass) — owner-approved past-day presence correction
Owner, on the real screen: month-attendance → day → absent-to-present did not save — because no such door existed (D334 is staff-side, today-only). **D338:** a doctor-only door on the day page writes an ALREADY-APPROVED present_request for a past no-punch day — in-time typed (pre-filled with the shift start), compulsory reason, audited — honoured by every existing reader through the ONE mechanism that already existed. Guards: approver-only · no future dates · staff active · feed readable · NO machine punch · one per staff-day · no holidays. `staff_register.py 124c6eb2… → e1305902…` (v0.8). Build red caught by the suite itself (test block placed after the fixture feed-restore — the guard was right both times).

### 4 · THE PORTAL-PWA UNIFICATION (owner: "as we have migrated to pwa wrapper all portals need to be like this only")
The portal PWA (followup origin, scope /) had tiles jumping to attendance.dr-manoj.in — every tap left the app; /register 404'd on followup. Confirmed from pinned bytes: the SSO cookie is domain-wide (.dr-manoj.in) and the register wholly relative → a vhost doorway alone unifies.
- **S200_R2a (GREEN):** `/register → 127.0.0.1:8044` APPENDED to the LIVE followup vhost — never replaced: **the live vhost had drifted from the repo mirror** (live carries /wa-approve S64 + /finance S179 the mirror lacks; a repo-based replace would have wiped two production paths). Backup `vhost.conf.bak_S200_R2a_20260824_151507`; probes /register/health=200, /portal & /finance intact.
  *Post-install scare, resolved NOT-A-FAULT:* owner's browser timed out on attendance.dr-manoj.in; on-box every door answered 200 while LiteSpeed's log showed Let's Encrypt's external probe timing out the same minutes — a transient external blip, self-recovered. Standing lesson: a client timeout with every local door 200 is a network fact, not a config fault. (Side observation: AutoSSL shows 4 domains failing renewal incl. drmanojagarwal.com — pre-existing.)
- **S200_R2b (GREEN):** portal tiles same-origin. **Base-pin correction caught mid-build (F-97 working):** the quoted P4 pin e2484429… was stale; the Register's chain P4→P5 43ec35b1→G1 **ab019dda** was the truth; bytes found by hash (D188). `portal.py ab019dda… → a48f4189…`.
- **S200_R8 (GREEN):** phase 2 — `/ledger → 127.0.0.1:8043` appended (Sheet-2's ledger doors had 404'd the first time one was pressed); both Staff-Ledger tiles same-origin; `portal.py a48f4189… → 24ea2c0b…`. Remaining cross-domain: bare Attendance tile + assets.dr-manoj.in (queued).

### 5 · D339/D339b — the FIX-ABSENTS desk (kits S200_R3, S200_R4, both GREEN)
Owner after real use of D338: "the flow for attendance correction is still cumbersome… sundays are not highlighted." **D339:** `/register/fixabsents?ym=` — every correctable machine-absence of a month on ONE page, grouped per staff with live absent/corrected/still-absent counters, shift-start prefills, one reason, tick-all, bulk write **through correct_present()** (the page grants nothing; it only refuses to OFFER what the write would refuse: future/holiday/rostered-off/punched/already-corrected; dead feed ⇒ empty list + warning, never a clean page). New `punch_month_index()` reads the CSV once, not 31×. Plus the **Sunday-columns regression fixed** on Sheet 1 (att_month_report had marked Sundays since v2.x; the new grid never carried it) — purple SUN header + column border, additive to existing cell classes. `staff_register e1305902…→582e1714…` (v0.9) + `salary_policy 7f86cc87…→dfe67285…`.
**D339b (R4):** owner: "i marked ticked days present… same is coming again." His saved page proved 20 corrections HAD saved; the fault was the required-but-empty Reason box at the top of a long page — the browser silently refused the submit. **Lesson minted: a required field the user cannot see when they press the button is a silent failure, not a validation.** Fix: reason pre-filled + carried; "Corrections already made" listed; **UNDO** added (approver-only, deletes ONLY desk/D338-written rows proven by decide_note, audited; staff D334 requests never deletable here). `→7d62435a…` (v0.10). Two build reds caught by the suite (a too-coarse R3 assertion; audit vs audit_log).

### 6 · THE SUNDAY RECKONING — D340 · D341 · D341b (owner rulings)
Owner: "actually the staff sent me absents calculating sunday absents as half days, caught it later." The arithmetic proved it (Shivani: 5 weekdays + 4 Sundays×0.5 = 7.0 = the sheet's figure) — machine whole-days had been compared against half-day-weighted counts: **the earlier 14-day correction list was built on mixed units**, and some saved corrections were false-present. Principle minted: **the register records FACTS; pay conventions live in the money layer.**
- **D340:** a July Sunday absence costs HALF a day.
- **D341:** the weight is **DERIVED** — that day's rostered minutes ÷ weekday minutes (override setting −1=derive / 0..1 forces; missing data ⇒ 1.0 fail-safe, bad data can never cheapen an absence). July validated it: Pravesh's true Sunday ratio is 0.56, Darpan's 0.524 — the derivation was truer than the hand-applied 0.5.
- **D341b:** the hard-coded D253 roster era (2026-09) is **GATED** behind ATT_ROSTER_FROM (default 2099-01) — groups are unassigned, rostering "only a thought", and the 5th-Sunday full-day rule would have changed 29-Nov-2026 unasked.
Owner rulings on the three contested Sundays (Shavez 19, Surendra 12, Pravesh 12): all stay ABSENT at derived weight. Undo set executed: Shavez 1 Jul, Surendra 13+14 back to absent; Shivani needed nothing (her 9 = 7.0 exactly).

### 7 · THE ENGINE RUN, THE RECONCILIATION, AND D342/D343 (owner rulings on live evidence)
`salary_policy.compute("2026-07")` run on the box; net reconciled for all 12 to the paisa: NET = Base − Leave − Collect25% − Fines, **HELD never subtracted** — exposing that the Improvement Hold had NO teeth (nothing withheld, nothing to release, nothing collected on failure).
Reconciling against the owner's ACTUAL Google-sheet payments: **divisor 30.5 matches 8 of 10 rows within ₹1 (30 matches none)** — July was paid symmetric-leave at 30.5, independently confirming the Sunday half-weighting.
- **D342a — the hold is a SUSPENDED CHARGE:** not deducted now; CANCELLED on ≥30% improvement; **COLLECTED with next month otherwise**. Chosen over a true hold for the staff's cash reality; switching later is a setting.
- **D342b — Arjun is NEVER fined** (extended by **D345b: never earns incentive either** — fully outside the loop; implemented as: minutes-exempt staff are outside fines AND incentive).
- **D342c — Sunday: HALF for pay, WHOLE for the deterrent.** Deliberate split — pay follows hours, the deterrent follows the occurrence. NOT an inconsistency to be tidied.
- **D343a — day_divisor = 30.5** (practice wins; setting follows). **D343b — Amir Sohail** is real staff OFF the biometric (₹2,500 manual) — enrol or keep a manual line.
- **Surendra ₹516.08 gap HELD** (paid −267 vs computed +249.08; likely real advance ≈₹8,746 vs 8,230 carried) — ledger check before settling.
- **D344 — Darpan FOLDED IN; August = GO-LIVE for all staff.** His exclusion from the Google sheet was only its inability to hold his loan + Sanjeevni-cash drawings; the ledger holds exactly that. July NIL is his computed result. Go-live prerequisites gathered: enforce_from · notice served · staff acceptance of interest.
- **D345 — the absence fine is a RAMP** (owner: "no pay, if more leaves then a small fine also adds up, ramps up"): k-th excess day beyond OWN allowance = k × fine_ramp_step (default ₹10; cumulative step·n(n+1)/2); flat-3 threshold DEAD (the Arjun incoherence structurally gone). July: ₹660 vs ₹1,600 flat.
**THE VERDICT (the metric the owner asked for):** old system as actually paid vs the finalised system, same July — **ALL ELEVEN staff gain, ₹5,384.37 more in staff hands** (Shavez +1,067 · Sandip +797 · Awdhesh +707 · Alisha +667 · Surendra +606 · Pravesh +569 · Ranjeet +450 · Arjun +210 · Vikki +170 · Sukhveer +93 · Shivani +50), late money ₹6,846→₹1,011 collected + ₹3,034 suspended, ₹660 ramp fines, ₹524.59 Diwali accrual. Owner-side workbook `Salary_July_2026_FINAL.xlsx` (VERDICT · CASH SETTLEMENT ₹4,519 top-ups · ATTENDANCE BASIS · AUGUST SETTLEMENT · D336 POLICY · COMPARE · METHOD) + bilingual staff PDF `Salary_New_System_July_Comparison.pdf` (Hindi-first; the suspended-75% box: "इस पैसे का मालिक आपका अपना सुधार है") — both owner-side, outside git (D320/F-31).
**Validation worth its own line:** the symmetric-leave clause independently produced Sukhveer's unused-leave credit ₹1,066.67 — the exact figure the owner had ruled by hand.

### 8 · D346 — THE GO-LIVE ENGINE (kits S200_R5 GREEN · S200_R5b GREEN)
ONE three-file kit carrying every ruling: derived Sunday weight (pay) / whole-day ramp (deterrent) / exempt-outside-the-loop / suspended-hold cancel+COLLECT limb (lock writes a COLLECT action; release adds NO money back — it never left) / divisor 30.5 / roster gate. `salary_policy 7f86cc87-chain → 4521f1a6` (v1.4) · `staff_register 7d62435a → 40efbac3` (v0.11) · `att_month_report 9ab98313 → 0184cb13` (v2.7; its selftest pins the roster era ON for its fixture so dormant code stays proven). First VPS run was a no-op — the kit had not been published (publish-then-pull ordering); second run GREEN first pass. **On-box July dump reproduced the workbook**: weighted leaves, ₹1,409.84, ramp 210/280/100/60/10, Arjun 0 — with the two derived-weight refinements (Pravesh 0.56, Darpan 0.524) truer than the hand 0.5.
**R5b:** my −1 "derive" sentinel collided with my own validator ("cannot be negative") exactly at the ENFORCE-FROM save — fixed with a key-specific rule; and the fix's first selftest draft would have LEFT 0.5 forced in the live settings file — rewritten snapshot-and-restore. **Lesson minted: a selftest that writes a live store is itself a live event.**

### 9 · S200_R6 (GREEN) — cover duty · settings-linked fines · the dark ledger
Owner's three: no cover-duty category; uniform fine ₹20 vs the ruled ₹15 (two rate cards disagreeing); the form's far-right pickers/edge-to-edge rows. **COVER_DUTY** ₹200/day credit (narration = who was covered; maker_full+checker) reaching PAY via the salary engine's duty-credit read; **uniform/I-card day-rates read LIVE from salary_policy_settings.json** (can never diverge again); the whole ledger app moved to the clinic dark family, paired-field entry card, mobile-first. `staff_ledger acd7b538 → 18052621` (v3.3-S200-SL6) · `salary_policy 260944bf → 9b14c340`. Shivani's four cover evenings identified FROM THE PUNCHES (9/10/13/15 Jul — late-outs summing to exactly the 1,100 candidate minutes) and entered: her ₹800 flowed into the compute.

### 10 · S200_R7 (GREEN) — approve WHERE you read (and the publish-guard catch)
Owner's UX list executed: approve strips ON Sheet 1/2 (return to the same page; desk shows open-&-approve doors; D337's human press intact, the page-hop gone) · FINALISED/NOT-FINAL strip + print button on the preview · Scenario renamed What-if with a sandbox explanation · FIX-ABSENTS a standout button · expandable fix-absents cards · **REAL BUG: the open-loans table's interest-only filter had hidden every non-interest tranche** (why "Darpan shows only one") — all opens now list, tagged; his page carries statement/advances/perks doors · fonts up. `salary_policy 9b14c340 → c9dd846e` (v1.5) · `staff_register 40efbac3 → f85a4b06` (v0.12).
**F-31/D320 enforcement event:** the kit initially carried `manual_advances_2026-07.json`; PUBLISH_ALL **refused** (gitignored salary data) — the guard working exactly as built. Kit re-cut without it; the data reached the box by paste. **Standing rule: kits carry code; money data goes to the box directly.**

### 11 · S200_R8 → R9 → R10 — the run-through's last catches
- **R8** (§4) also: back links became real BUTTONS; sheet cells 16px semi-bold; nav gained Lock desk + prev/next month arrows.
- **R9** (staff_ledger 18052621 → eaa305cb, v3.4-S200-SL7): advances grouped ONE EXPANDABLE CARD PER STAFF (open count · balance · interest/PENDING/perks in the summary; perks-history + statement doors inside); **the retired old salary computation DISARMED** — its live "APPROVE & LOCK" button (still armed on the pre-D336 rules, one confused press from locking August on the dead model) replaced by a banner to the register Lock desk; steps 2 (informed flags — feeds the new engine) and 5 (ledger close) marked as the living parts. *Install not explicitly confirmed on the box at close — verify the grouped advances page next session.*
- **R10** (salary_policy c9dd846e → 7c0cfb94, v1.7): **the owner-record manual advances now DEDUCT in compute** — caught at the brink: Sheet 4 was asking staff to sign for money already in their pockets as advances, and the lock total was ₹55,030 too high. After R10: Advance ded. ₹65,030 (8 manual + Darpan's 10,000), Sheet-4 amounts = the true hand-over (Alisha 2,647.37 … Shivani 4,875.45 …), verified against the workbook to the paisa.
- **Darpan's two big advances CONFIRMED REAL by the owner** (₹183,000 interest-bearing bal 175,000 + ₹180,000 interest-free, both 2026-08-07; ₹3.55L outstanding at ₹5,000/mo each) — the "unique loan and drawings" that kept him off the Google sheet, now fully in the system.
- **F-178 MINTED (open):** the mid-duty punch blindsight — the feed keeps EVERY punch but the day uses only first/last; in 09:00–out 11:00–in 15:00–out 18:00 reads as a full day, and NO page shows the sequence. Fix queued: surface the punch sequence + flag mid-duty gaps beyond a threshold. (Honest limit: only punches that happen can be seen — the selfie-GPS punch closes the rest.)

### 12 · 🔒 THE LOCK — July 2026
16 never-entered July register days closed by an owner-sanctioned audited backfill script (all-clear, in his name, replicating his 16 tap-sequences); Sheet 1 approved; Sheet 2 approved; **LOCKED: TOTAL PAYOUT ₹59,163 · by manoj · 2026-08-25 07:16:48.** Every suspended charge written to hold_ledger — August's improvement test is armed. The FINAL sheets exist on the VPS; the bilingual Sheet 4 is the signature book.

### 13 · Ideation filed (NOT built) — the next flagship: `S200_StaffApp_Design_Candidate.md`
The Staff Console (Phase 0 spine: one card per person writing through the scattered stores; joining wizard; policy TEMPLATES incl. probation quota-ramp 0%→25%→50%; the EXIT flow — live need: **Pravesh resigns 31-Aug**) · the staff Money & Attendance app (slip · Diwali pot · the WINNABLE hold-release meter · quota meter · in-app advance requests with pre-filled SPECIAL forms photographed back) · **काम, the voice-first task board** (owner records tasks; SEEN auto-stamps; reporting = two big buttons + hold-to-record voice reply; append-only store; not-WhatsApp boundaries) — all behind owner knobs, default OFF, rollout by phases 0/A/B/C/D. Four standing rulings requested before Phase 0.
Also carried live: **interest terms need staff acceptance** · a living owner to-do doc (`OWNER_TODO_LIVE.md`, project-side, deliberately UN-manifested because it edits continuously).

### 14 · Mental models (added this session)
- **A capability the owner cannot complete in one pass is only half built** (D338 made correction possible; D339 made a month practical).
- **A required field the user cannot see when pressing the button is a silent failure, not a validation** (D339b).
- **The register records facts; pay conventions live in the money layer** — and when two counts are compared, state the units first (the Sunday reckoning).
- **Practice outranks the written setting when they disagree** — reconcile against what was actually paid (D343's 30.5).
- **A selftest that writes a live store is itself a live event** — snapshot and restore (R5b).
- **Kits carry code; money data travels outside git** — and the guard that refuses is the discipline working (R7/F-31).
- **A run-through on real data is the only auditor that presses every door** — it found the armed old lock, the hidden tranches, the 404'd doors, and the signature-sheet advance gap in a single walk.

**Queued at close (Runbook v134 §2 is the live list):** owner ⭐0 (tokens · Darpan SPECIAL · Pravesh exit · July cash top-ups ₹4,519 · Surendra ₹516 · Arjun's paid figure · Shivani's two August items · 18-Aug bills · UPI days · staff comms/PWA/forms · Medical-PC Drive · Club-3/Club-4 · auditor triage) · builder ⭐1 (ledger auto-detect + old-settings retirement + cover-rate link · F-178 surfacing · Staff Console D347 candidate · task board · PWA holdouts) · ⭐2 the August close = the first fully LIVE run.

**Next free: D347 · F-179.**

---

## §S201 — 25 Aug 2026 · FULL build session · THE MARG PIPELINE MADE WHOLE
### (three kits live · the medical PC reached and supervised · D347 + D348 · F-179 … F-183)

**How it opened.** *"i made a marg sale report this morning and saw it being pushed from a cmd window
there, in few minutes, but it is not in `/finance/approvals#margCard` yet, and i cant find it in my
local margsync folder too — analyse, solve, and give report."*

One missing report. It ended as the session that closed every hole in the pipeline that carries
Sanjeevni's pharmacy revenue from the medical PC to the books.

---

### 1 · THE ROOT CAUSE — a queue with no consumer

`marg_router.py` verified every report and stamped it **"queued for upload"** into
`MargArchive\_outbox`. **Nothing read `_outbox`.** The only uploader in the whole chain was a manual
double-click on the medical PC's `SEND_TO_CLINIC.bat`, and it had not been pressed since **22 Aug**.

Eleven verified reports were sitting there — 2 purchase, 6 closing stock, 2 expiry, 1 scrap-store —
**every one of them archived, hashed and correct, and none of them on the server.** The only symptom
the owner could see was a page that stayed empty. **F-179.**

The fix is `marg_gate.py` on manojz (`f09cfe61d052d5dc8dd402d2e3a85422`, selftest 49/49): an outbox
sender with client-side delivery state, superseding by `span_key` across batches, live token
resolution from the medical PC with a local cache, and `os.replace` for state writes. It is driven by
the existing 10-minute pull, so the queue now drains itself.

**Recorded because it is the session's own worst moment:** the assistant told the owner the server
deduplicated marg-push by content. **It does not** — it answered ACCEPTED and staged a second copy of
24-Aug. The claim was made from expectation, not from reading the ingest path. Corrected in the same
hour, and the client-side state exists because of it.

---

### 2 · THE `.xlsx` TIME BOMB, REMOVED RATHER THAN MANAGED

The medical PC's Python has no spreadsheet reader, so the guard there could not verify an `.xlsx`
export **at all** — and sent anyway when it could not verify. Rather than install and then maintain
`openpyxl` on a machine nobody logs into, the dependency was **deleted**: `xlsx_stdlib.py`
(`bbe11a8953f66c27126c48e773cfbe35`) reads `.xlsx` with `zipfile` + `ElementTree` and nothing else,
validated cell-for-cell against `openpyxl` on the real exports. `marg_router.open_sheet()` routes to
it; the medical kit carries it.

**Mental model recorded:** *a dependency you cannot maintain on the machine that needs it is not a
dependency, it is a scheduled outage.*

---

### 3 · THE MEDICAL PC, REACHED AND SUPERVISED

Tailscale gave manojz a **read-only view of D: only**. Google Drive for Desktop, already installed for
the S198 accountant work, became the **bidirectional channel**: `ToMedical` down (Claude → medical),
`FromMedical` up (medical → Claude). Nothing else on that machine had to change.

`medical_agent.py` supervises `marg_watch.py` as a child process, restarts it within a minute of a
death, writes a heartbeat every five minutes into `FromMedical`, and auto-applies kit files with a
compile-check and a hash verify. It iterated **S201.1 → S201.11** in one day, and every iteration was
a fault found by watching it run:

- **S201.1 died silently under `pythonw`** — `sys.stdout` is `None` there, and `log()` wrote to the
  console before the file. File first, console guarded, plus a crash handler.
- **S201.5/.6** — a retry loop had written **343 backups / 4.1 MB in three hours.** Prove writable
  before backing up; name backups by source md5; three tries then stop; prune with `chmod`.
- **S201.7** — the PDF test found a **second Marg output tree on `C:\Users\Public\MARG\`**, which
  manojz **structurally cannot see** (the Tailscale share is D: only). Added to `WATCH_DIRS`.
- **S201.8** — an ALLOWLIST, not a denylist, after 18 Marg database files surfaced from the C: tree.
- **S201.10** — `margstart.csv` sits in every Marg user folder and never changes, pinning the IGNORED
  counter at 2 for ever. *A number that is never zero tells you nothing on the day it should have
  been 3.*
- **S201.11 — F-180, and the design ruling that answers it.** S201.10 sat on Drive from 19:30 while
  **S201.9 kept running**, and the heartbeat could not show it: it printed the running version with
  **nothing to compare it to**. The agent updates the *kit* but **deliberately never updates itself** —
  a supervisor that overwrites its own file while running can leave the PC with no watcher at all.
  That safety is kept. **So the agent does not update itself; it REPORTS on itself**: each heartbeat
  hashes the running file against `ToMedical\medical_agent.py` and prints the drift with the fix path.
  Comparison is **by md5, never by the version string a file claims about itself** (D188 applied to a
  constant). Verified offline against all three states — no file on Drive, identical, Drive newer.

**Also fixed without a single GUI step by the owner** (his standing objection: *"the method is too
cumbersome"*): the 10-minute console popup on manojz. `PULL_FROM_MEDICAL.bat` hands off to
`PULL_HIDDEN.vbs` and **repoints its own scheduled task**, verified over the 19:10 cycle.

**Recorded, because it is the same fault the assistant had criticised that morning:** installer v2
printed **"UPDATED"** without verifying, while `move` had failed with Access Denied under the running
watcher. **That is AF-1's shape exactly.** v3 stops everything first, clears the read-only attribute,
hash-compares, and prints the truth.

---

### 4 · THE MONTH ROW THAT COULD NEVER GO GREEN — and the word that was wrong

The owner: *"This month vs Marg / books 4,56,980 · Marg 4,05,112 · difference 51,868 … this is
probably a system i don't understand, some labeling as variance maybe."*

**The difference IS the parked list, to the rupee** — 49 bills, ₹51,868, confirmed day by day. The
health check compared the whole day's books against **attributed-only** Marg lines, so it could never
agree; and the differing-day list truncated at five **in silence**, which is how 24-Aug stayed hidden.
Kit **`S201_HEALTH`** compares like with like, says *"and N more"*, and gives the parked bills their
own **`info`** row that never drives the portal tile (the S195 ruling, applied at last).

Then the owner named the thing properly, and the name was the finding: **these are sale bills where
the salesman did not enter the three identifiers at the till — mobile, name, and clinic ID** (numbered
from 1, now in the 7999s). Not "variance". Not "low confidence".

**And "low confidence" was measurably wrong.** Run over **192 bills across seven days**, every Marg
bill scores **either 0.95+ (a clinic ID is present) or 0.50 (it is not)** — nothing in between, ever.
The 0.70 threshold was tuned for **OCR**, where the doubt is whether a scan was READ correctly. There
is no OCR in this path. It is a **has-ID switch**, and any value between 0.51 and 0.94 behaves
identically. **Nothing to tune; only the label was wrong.** The backlog item asking the owner to make
a business judgement on `ingest.min_confidence` is closed by measurement, not by decision.

Measured identifier capture, recorded because it is an operational number the owner can act on:

| day | bills | with ID | capture | unidentified |
|---|---|---|---|---|
| 17-Aug | 28 | 19 | 68% | ₹9,990 |
| 18-Aug | 30 | 21 | 70% | ₹4,767 |
| 19-Aug | 30 | 23 | 77% | ₹3,500 |
| 20-Aug | 20 | 16 | 80% | ₹1,331 |
| **21-Aug** | 37 | 21 | **57%** | ₹30,045 |
| 22-Aug | 25 | 23 | 92% | ₹2,489 |
| 24-Aug | 22 | 17 | 77% | ₹2,425 |
| **week** | **192** | **140** | **73%** | **₹54,547 · 28.3% of turnover** |

**21-Aug was not a formatting fault** — it was a busy day with the ID skipped more often. 26 of the 52
unidentified bills do carry a phone last-4, so the Docterz match has something to work with.

**Two latent faults found and deliberately NOT fixed in these kits (F-183, OPEN):** the `0.60` tier
parks a bill that HAS a clinic ID but no name — backwards, since the ID is the strongest identifier
there is; and the pattern `[A-Za-z]{0,3}\d{2,8}` requires two or more digits, so single-digit clinic
IDs would not match. Neither occurs in this week's data. **Mixing a behaviour change into a labelling
fix makes a rollback hard to reason about.**

---

### 5 · THE OWNER'S OWN SAVED PAGE FOUND A RENDERING FAULT — F-181

Asked to redesign the health page, the owner uploaded his saved copy of the **served** HTML. Reading
the bytes the server actually sent — not the generator — showed the **Correction checklist** row
rendering broken. The row is wrapped in `<a class=row>` and its hint carried *"Open the checklist"* as
a **second anchor inside it**. **Nested `<a>` is invalid HTML**; every browser un-nests it, orphaning
the status mark into its own clickable strip and dropping `.body` outside the row.

**It survived because the row rendered, the link worked, and the S198 tests counted rows and counted
clickable rows — both counts stayed right. Only the SHAPE was wrong, and no assertion described
shape.** Now one does, on the served bytes: no row anchor may contain another anchor.

**This is the second time in S201 that the owner's own uploaded HTML surfaced a fault invisible from
the source side** (S187 P2a found a doubled `</tbody>` the same way). **Mental model: reading what the
server actually sent is a distinct check from reading what builds it.**

Kit **`S201_UI`** also migrated `/finance/health` to **Clinic Design Language v1** — it had been
pre-v1 for fourteen sessions — and **registered it in the F-130 `_DESIGN_V1_PAGES` table** (**F-182**:
it was not in that table at all, so it was neither protected nor recorded). One flat list became three
sections — *What needs you* · *Worth knowing* · *Running normally* — so the eye lands on the job
rather than scanning eleven equal rows.

---

### 6 · THE RETRACTION — D188 broken while quoting D188

The assistant reported `vps_deploy.sh` as **broken for six kits**. It was **not**. The finding was
read off the **stale repo copy**; the live file at `/root/deploy/` had carried the correct
case-insensitive glob all along, and the owner's own `tail -3` disproved it.

**A file's location is not its provenance — committed while quoting D188 in the same document.** The
retraction was written into the session record rather than quietly dropped. The genuinely stale repo
copy of `vps_deploy.sh` remains a backlog item; it was never the fault reported.

---

### 7 · WHAT WENT LIVE

| kit | file | pin | smoke |
|---|---|---|---|
| `S201_A1FIX` | `finance_app.py` | `2c99b2c6…` → `d930b6b5bca59e7f52ce46f6b88332fd` | 680 → **683** |
| `S201_HEALTH` | `finance_app.py` | `d930b6b5…` → `024399775bfd14844f299b3dfac4bb47` | 683 → **690** |
| `S201_UI` | `finance_app.py` | `024399775b…` → `3f72e9ad16d915fe5ced45c4e28a2248` | 690 → **693** |

**Three kits, three projections written before measurement, three landing exactly** (+3, +7, +3), each
with the fail set byte-identical offline. **`S201_A1FIX` closed AF-2** — the `TOTAL_VS_MARG` check had
been dead since S195 because `days_payload` never carried `business_date`.

Manojz tooling (not VPS, not manifest rows): `marg_gate.py` · `marg_rescan.py` · `xlsx_stdlib.py` ·
`medical_inventory.py` · `medical_census.py` + the `.bat`/`.vbs` double-click set; `marg_router.py`
`bbc50f9172211925755eeaa25920d1cf` (PDF facts, `data_from`/`data_to`, xlsx routing) · `marg_watch.py`
`2076fe1d8d145524be16ae857b3d838d` · `signatures.json` `3e9cbba02ffb4e0f131738eee7a465f7` ·
`PULL_FROM_MEDICAL.bat` `d64b636b5bf2418e037e9a78893e0466`. Medical PC: `medical_agent.py`
**S201.11 `69e60d778ab61a8d50c79394e2951309`**, watcher `aa55cdb5…`.

**Cleanup, nothing deleted:** 7.6 MB parked into `_to_delete\` on manojz; cleanup scripts delivered
for the medical PC and Drive. **Census: 78 report-shaped files on the medical PC, 0 not in the
archive.**

---

### 8 · D347 · D348

**D347 — the medical-PC pipeline architecture.** Google Drive for Desktop is the **bidirectional
delivery channel** (`ToMedical` down, `FromMedical` up); Tailscale is a **read-only D:-only view** and
is not load-bearing. A resident agent supervises the watcher as a child and auto-applies kit files
with compile-check and hash verify, **but never updates itself** — a supervisor that overwrites its
own running file can leave the machine with no watcher at all. **It reports its own drift instead**,
by md5. The 10-minute pull on manojz drains the outbox, rescans quarantine when `signatures.json`
changes, and refreshes the daily picture. **The manual sender on the medical PC stays as the fallback
and is never removed** (AF-1 remains armed on it — deliberately, and recorded).

**D348 — sale bills without a clinic ID.** The salesman enters three identifiers at the till: mobile,
name, and clinic ID. A bill missing the ID **counts in sales in full** — `day_line` carries the whole
day and `finance_ingest` cannot touch it (D313) — and is **parked separately**, awaiting the Docterz
cross-match on `bill_date + patient_name + phone_last4` (last-4 only, F-86). It is reported at
**`info`**, never as a fault, and never drives the portal tile. **The words "variance" and "low
confidence" are retired**: the first was never true, and the second imported an OCR concept into a
path that has no OCR.

---

### 9 · IDEATED, PARKED FOR S202 (not decided, not built)

A **`/ops` runbook surface** — symptom-indexed, owner-only, each fault a dropdown decision tree,
linked as a **second door** from every `/finance/health` row (`HEALTH_LINKS` already maps every check
key to its fix; a parallel `HEALTH_RUNBOOK` map costs almost nothing). **Served from the repo, never
uploaded** — an uploaded copy is a second source of truth with no hash and no owner, which is F-23 and
the S131 stumps exactly. **Rule proposed: a runbook page never states a hash, version, count or path
inline; it reads them live** — the moment it hard-codes one it is a delta doc, which D202 forbids.
**Honest prerequisite: B2 first** — the three files the 60-second check opens all live on manojz, and
the VPS cannot see them, so `/ops` without B2 is a page that tells you what to do but not whether you
need to.

---

### 10 · MENTAL MODELS (added this session)

- **A queue with no consumer is not a queue, it is a hole.** Eleven correct reports sat in one for
  three days and every component reported success.
- **A dependency you cannot maintain on the machine that needs it is a scheduled outage** — delete it
  rather than install it.
- **Reading what the server SENT is a distinct check from reading what builds it.** Twice now, the
  owner's own saved HTML has caught what the source side could not.
- **When a count is right but the shape is wrong, no counting test will ever see it** — assert
  something the change did not preserve.
- **A supervisor must never update itself; it must report its own drift.** Safety and visibility are
  different problems and deserve different answers.
- **A threshold imported from another problem domain measures nothing here** — 0.70 came from OCR and
  was silently acting as a boolean.
- **A number that is never zero tells you nothing on the day it should have been three.**
- **The owner's own words are the better label** — "variance" and "low confidence" were both ours, and
  both wrong; "sale bills without a clinic ID" is what it is.
- **Mixing a behaviour change into a labelling fix makes a rollback hard to reason about** — F-183 was
  found this session and deliberately left for its own kit.

**Queued at close (Runbook v135 §2 and `OWNER_TODO_LIVE.md` are the live lists):** owner ⭐0 (tokens —
**three copies**, never hand-copy · Darpan SPECIAL · Pravesh exit 31-Aug · July cash top-ups ₹4,519 ·
Surendra ₹516 · Arjun's paid figure · Shivani's two items · UPI days · pin-list copy) · ⭐0a Marg
(agent S201.11 installed ✓ · the tidy scripts · the stale `vps_deploy.sh` sync) · ⭐1 builder (**B2
first**, then `/ops` · B3–B7 · F-183 · identifier capture on the health page · the ledger kit · F-178
surfacing · Staff Console) · ⭐2 the August close — the first fully LIVE run.

**Next free: D349 · F-184.**

---

## §S202 — 26 August 2026 · THE DAY THE FEED WENT DARK, AND SIX OF THE FAULTS WERE OURS

**Opened as canon housekeeping. Became an incident, a physical count, two design rulings, seven kits
and nine findings — six of them the assistant's own, one a correction of a claim it made and got
wrong.**

### The spine: eight hours and forty minutes of silence

At **23:08 IST on 25-Aug** the Marg pull stopped working. It was found at **07:33** the next morning,
and only because the owner asked why a report he had generated had not arrived.

**Everything was healthy.** The medical PC was on — he was in an RDP session with it. Tailscale
reported `medical  active; direct 192.168.1.37:41641`. The agent ran, the watcher captured, Drive
synced. The single thing that failed was Windows on manojz applying its default policy against
**unauthenticated guest access** to SMB shares.

Three things made it expensive, and each became a finding. **Nothing was watching that leg** — every
server-side check watches arrival at the VPS. **The error named the wrong causes** (F-193): *"Is it
switched on and Tailscale connected?"*, when both were demonstrably true. **A working alternative
route sat idle** — Drive carried the heartbeat across the entire outage without a stumble.

Fixed by authentication, not by weakening anything: `cmdkey /add:100.119.151.40 /user:MEDICAL\SET
/pass`, using the account that has a password (`MEDICAL\user` has none, and Windows refuses
passwordless network logins). The forums' remedy — re-enabling insecure guest access on a PC holding
patient records — was declined and recorded as declined. The 07:40 pull ran `-- ok` in eighteen
seconds, and the 12-June report the owner had generated came through and was ACCEPTED the same cycle.

### The Rs 20,000, settled by counting (F-187, D-none)

The owner asked why Darpan's drawer showed money that was not there. The books said **63,903**; the
drawer held **43,903**. Difference: **20,000, exactly.**

The record had known since 17-Aug — in words. `cash_count.explanation` itemises the drawer clearing
as *10,000 July advance + 20,000 August advance + 18,963 to the owner*. The 18,963 became a custody
event. The 10,000 became an expense. **The 20,000 became prose**, and prose is not in the books.

Two things about how it was settled are worth keeping. **A plausible theory was killed first**: the
owner had reasoned the gap was *20,003, with 3 written off* — and 20,003 turned out to be the 20-Aug
running balance, reconciling on every row of the table (66,994 + 7,939 − 51,930 − 3,000). It fitted
the digits and was entirely false. **And the assistant told him to press Apply on the 12-June report
and was wrong** — he pushed back, asking why he should risk disturbing financial data. Reading the
live ingest code proved him right: Apply supersedes, and would have DELETED 26 attributed rows and 26
RESOLVED review rows on a closed month, to arrive at the same number. The assistant had read that
same behaviour in the ingestion reference hours earlier and had not connected it.

### Two design rulings

**D349 — one rule in one place.** The owner's words: *"it should be the rule at one place and all data
shd follow that."* Proven twice within hours. `/ledger/statement` told him Darpan's Rs 20,000
*"recovers in full at the 2026-08 close"* when the close takes **8,000** — the quota test existed
twice, and in `close_month()` the schedule check is implicit in the ORDERING, which the display could
not copy. And `/finance/approvals` still said *"variance"* after S201 renamed it on the health page,
because nobody had realised the two surfaces showed the same rows. Both closed by a single shared
function; the exceptions card rebuilt as the inline reconciliation table he asked for, with **five
harmless rows no longer hiding four real ones** — including 12-Jun's −8,487, open since S186.

**D350 — the Marg transport, contract WRITTEN and scoped by the owner.** He read it and took the
counter-argument recorded in §8: verification, visibility, correct documents and a reinstall kit —
**no second transport.** The Drive fallback is parked, with his ruling that other channels serve. His
reasoning for a prepared-but-manual fallback was better than the contract's own proposal, and the
decisive risk was named honestly: **a standby route never exercised will not work when needed.**

### The four faults in work shipped the same day

**A gate that matched the bare word `OK`** and would have accepted 642/693 — caught an hour later by
a different kit's exact-count gate. **A preflight demanding a binary the kit never invokes**, which
refused a correct kit. **A monitor wired after the pull's early exit**, so it could report success and
nothing else — built the same morning as the never-fired witness designed to catch exactly that.
**And a check that read a dead machine's last words as proof it was alive.** All four are F-189,
F-191 and F-192, and all four were ours.

### What the owner's own questions found

Every one of the following came from him using the system, not from any test: the statement page
lying about his payroll; `REPORT_1.XLS` as the name of every report ever pushed; **56 phantom missing
days** conjured by one deliberately-loaded June report; and the eleven-month-empty `E:\auto` folder
where automatic Marg backups were configured in October 2025 and **have never once run**.

### F-185, corrected

The assistant told him that thirteen named patients and their diagnoses were exposed in his public
repository, urged action, and pressed when he was sceptical. **It was false.** `.gitignore` had
excluded them from the beginning; not one `.csv` is tracked. The scanner asked the filesystem what
existed rather than asking git what was published. The measured figure is **62 mobile-shaped numbers,
no diagnoses, ever** — F-96 was right all along at about ten times its recorded count. Corrected in
the register rather than deleted, and the scanner now refuses to run if it cannot ask git.

### Shipped

`S202_DARPAN20K` · `S202_D349B` (ledger 294 → 301) · `S202_D349A` v2 (finance 693 → 701) ·
`S202_B2A` (→ 713) · `S202_B2C` (→ 719) · `S202_B2B` (manojz sender) · `S202_PICTURE` (49 → 53).
Canon: F-184 repaired — twelve absent canonical documents filed, `MD5SUMS_ALL.txt` and `KIT_ID.txt`
rebuilt, and the folder's own verification command exiting 0 for the first time. `.gitattributes`
pinned `*.md` (F-190). Register v5.46 → v5.54 across the session, every pin recorded AS IT MOVED.

**Verdict at the close: GREEN, match 47, drift 0.** After three live installs and a data migration in
one session, nothing needed reconciling at the end — because nothing was saved up for the end.

---

**END OF KB HISTORY ARCHIVE v1.49. §S202 is the last section; §S201, §S200, §S199, §S198, §S196, §S195, §S194, §S193, §S192, §S191, §S190, §S189, §S188-FINAL, §S188-POST, §S188, §S187, §S186-POST, §S186, §S185, §S184, §S183, §S182, §S181, §S180, §S179, §S178, §S177 and earlier sit above it. If §S201 or this marker is absent, this file is truncated and must not be used as canonical.**

---

## §S203 — 26 August 2026 · THE SESSION THAT LOOKED AT THE MACHINES THEMSELVES

**A FULL build session. It opened as documentation housekeeping and became the first honest
inventory of the two Windows PCs the pharmacy revenue chain actually runs on. Three transport kits
live, one server-side gate fixed, the offsite backup built and proven unattended, sixty-nine
documents collapsed to three, D351 minted — and thirteen findings, of which five are recorded as
the assistant's own and a sixth was found at this close.**

### The three kits, and what each one fixed

**S203_R1 — `marg_router.py`** (`bbc50f9172211925755eeaa25920d1cf` → `781e5ff66d4eca6b6ed4703bf692fb46`).
An unreadable `.xls` was refused **above** the archive-and-index block. So it was never copied to
`_REFUSED`, never written to `index.csv`, and — because `seen` is rebuilt from `index.csv` on every
run — **re-refused every ten minutes for ever**, with the only message going to a console nobody
kept. Fixed by lifting the tail into `_archive_and_index()`, called by **both** paths. Selftest
**14 → 21, +7 exactly**. The seven new checks were run against the *unfixed* file first: **five go
RED**, and the two that pass were already true.

**S203_R2 — `PULL_FROM_MEDICAL.bat` + `PULL_HIDDEN.vbs`**
(`92f03999d0a14d00b7f552dbb4d44c05` → `cfb8b13d028a3bdc69a70701056392ec`;
`9a3ba9ba3bb7376bd166f12624d282c3` → `084fc4523b0e855c8d29b54c144bb60b`). The pull wrote `-- ok`
**unconditionally**, and `pipeline_status.py:122` relays that word to the clinic server as
liveness. The pull also kept **no log at all**. Now every step's exit code is checked, the word is
earned, and `_logs\pull_YYYY-MM.log` + `_logs\pull_console_YYYY-MM.log` exist.

**S203_R3 — `pipeline_status.py`** (`51cf10c9f2543fcd48a61ee7f8faf51a` →
`0b3dd968f31cdb48a910539a087206c6`). It carries the backup's age to the clinic server, and it now
reports the **stick's** age, never Marg's same-disk `serverbackup`, with a check asserting exactly
that. Selftest **15 → 21, +6 exactly**; the six run against the unpatched parser make **check 10
FAIL**. Installed by Claude directly — the owner has `D:\Downloads` connected, and after this
session that is the default (see the preference change below).

Two more live files moved on the medical PC: **`medical_agent.py` S203.3**
(`69e60d778ab61a8d50c79394e2951309` → `7b9a76f24abc5be369186507279cfaad`), which gained the
offsite backup leg; and **`medical_census.py` S203.6**
(`b53af03aaf16f011d3c15bb059637a5f` → `a7706d60965e45545e93a4eaa94fa892`), the on-machine audit
tool that reports census, drives, backup folders, Marg data size, unfiltered scheduled tasks, Marg
config, an md5 for every live file, whether Marg is running, the Windows power history, and
`D:\SendToClinic` as it really is.

**Reverse application on every file returned exactly to its live pin.** Every projection in this
session was written down before anything was measured, and every one landed.

### THE FIRST MEDICAL-PC PINS EVER TAKEN

Eight files, in `deploy_kits/S203_CENSUS_BACKUP/S203_MEDICAL_PC_PINS.md`, read from the machine by
`medical_census.py` at 13:04 — not from manojz's mirror and not from any record. Unchanged and
verified: `marg_watch.py` `aa55cdb51521c796a9167ee7d27a368f` · `xlsx_stdlib.py`
`bbe11a8953f66c27126c48e773cfbe35` · `SEND_TO_CLINIC.bat` `e19a8a777ac22fe75a242f1eb9762185` ·
`Startup\MargAgent.cmd` `edcb2f2e2ef1258d4e0d3bae9ef38460` · manojz `signatures.json`
`3e9cbba02ffb4e0f131738eee7a465f7`.

**Drift on that machine had been undetectable by construction.** `verify_live_pins.py` runs on the
VPS and cannot reach it; the Tailscale share is read-only and D:-only; and manojz's mirror is
`robocopy /E` with **no `/PURGE`**, so it never deletes and is not evidence of what is there.

### THE CHAIN — three faults, each visible only because the one before it was fixed

This is the session's spine, and it is worth reading in order, because no step could have been
taken without the one before it.

**1 · 18:38 — R2 gave the pull a log.** Until that moment there was nothing to look at. The pull
had run every ten minutes for a session and a half and left no trace of what it said.

**2 · 18:44 — its FIRST log ended `pipeline_status: post failed (HTTP Error 401)`.** That line had
printed on **every pull since S202** and been discarded every time, into a console that
`PULL_HIDDEN.vbs` threw away.

**3 · 18:51 — traced to `_gate()`.** It is a `before_request` that fails closed and exempts exactly
three literal paths: the cron token (any path), `MARG_TOKEN` for `/finance/api/marg-push`, and
`RENEWALS_TOKEN` for `/finance/api/renewals-push`. **`/finance/api/pipeline-status` was added at
S202 and never added to that list.** Every real post was therefore refused **before**
`api_pipeline_status()` ever ran, and the route's own token check was unreachable dead code.
**B2 had never once reported.** Proven in both directions, on the box: a POST from the VPS carrying
the server's own `FINANCE_MARG_TOKEN` returned **401 `not_signed_in`** before the fix, and **HTTP
200 `{"ok":true,"received_at":"2026-08-26T18:52:00"}`** after it. `finance_app.py`
`50ac4c86a3985bf82269d650d5e46f0f` → `374a0b82803068bb52e43ab9a921c1e9` at the gate fix, then
**`7948cee0e00494bbee30de1c51d03d74`** with the test.

**4 · 19:17 — proven from the REAL caller, not from a curl.** Three consecutive
`pipeline_status: 200 (token from medical PC (live))` lines in the pull's own console log,
including the **scheduled** runs at 19:10 and 19:17. A hand-run proof is a proof about the hand.

**Why it shipped broken, and this is the part that must not be lost.** The smoke suite *does* post
to that route with the `X-Finance-Marg` header — but it does so on `c`, a **signed-in** test
client. `_gate()` waved it through on the **session**, so the token clause was never exercised at
all. And the check immediately above it, *"an unauthenticated pipeline post is REFUSED"*, returned
its 401 from the **route's** check rather than from the gate. **Both checks passed for reasons
other than the ones they name.** The token substitution is also only half applied: the test sets
`os.environ["FINANCE_MARG_TOKEN"]` while `_gate()` reads the module-level `MARG_TOKEN`, bound at
import.

VPS smoke **719 → 721, +2 exactly** — and the gate fix itself added none, correctly, because there
was nothing it could honestly assert. See F-195: the +2 that were added **do not bite**, and that
is recorded as green-and-meaningless rather than left standing as coverage.

### THE BACKUP — the crown jewels, measured and then fixed

Everything below was read off the machine, not recalled.

`E:` present, **28.5 GB free of 28.9** · **177 files, 0.4 GB** · newest **22-Aug** · `E:\auto` and
`E:\MARGBCKUP\auto` **EMPTY**, `E:\MARGBCKUP` last written **09-Oct-2025** · **six non-Microsoft
scheduled tasks, all Google and OneDrive** · **115 Marg config files, and not one mentions backup**
· `margwin.exe` running (pid 7172), so `D:\MARGERP\Data` — **1,075 files, 0.9 GB** — is a set of
open FoxPro tables · the **previous financial year last backed up 17-Jul**.

**So the record was wrong.** F-191(c) said the automatic backup *"was configured and has never once
run."* **Nothing in Task Scheduler and nothing at startup runs a backup. It was never scheduled.**
The empty `auto` folders were never going to fill, and eleven months of waiting for them was
waiting for a thing that did not exist.

**Marg's own `serverbackup` is not a substitute.** The day-of-week `.mst` files land near-daily,
but the real ~2.3 MB `*_c18_d_*` pair exists only for **26, 25 and 22-Aug, then a 12-day gap back
to 10-Aug** — and it sits on **D:, the same disk as the data it is meant to survive**.

**Fixed:** the agent now copies the stick offsite automatically, bounded to 64 MB a pass, and
carries the backup's age in every heartbeat with a warning past three days. **Proven at 19:37 —
`offsite: 182 file(s), 0.41 GB … offsite copy is COMPLETE`, newest backup 0.2 days old.** The owner
took a fresh backup and it was carried offsite within the hour, unattended.

**Still open, and stated plainly: no restore has ever been tested, and the previous financial year
is 40 days stale with exactly one copy.**

### SIXTY-NINE DOCUMENTS TO THREE — the owner's ruling

His words: *"we need the current state with all other relevant kb, and retire all other to marg,
medical history … so that future reference is to the best and pointed data and sources."*

Chosen shape, **three files**, in `deploy_kits/MARG_MEDICAL/`:
**`MARG_MEDICAL_CURRENT.md`** (13 KB — the only one read) · **`MARG_MEDICAL_HISTORY.md`** (248 KB,
append-only, 58 index rows, 57 chronological entries) · **`MARG_WALL_CARD.html`** (one printed page
beside the medical PC). Plus `MARG_REPORT_EXPECTATIONS.md`.

**Preserved first, retired second.** 52 Marg/medical documents were copied into
`deploy_kits/S203_MARG_CANON/` and hash-verified; the folder holds **67 files, `md5sum -c` exit
0**. **Only then** were **18 removed from project knowledge**, and each was proven present in the
pushed commit `f94ff27a8b89f01363e62c9f800acd55ff4ff00d` before it was removed.

**Deliberately NOT retired:** `S179_Sanjeevni_Medical_Module_Build_Contract_v1` — its claimed
successor exists nowhere, so it is bannered UNCERTAIN and treated as KEEP · `S203_KB_CENSUS_PHASE12`
and `S203_PENDENCY_RECONCILIATION`, which are whole-KB and whose findings are still live.

---

**D351 — THE MARG/MEDICAL DOCUMENTATION MODEL.** *(Owner-chosen from three options presented.)*

D247 gave the knowledge base a Register plus an append-only Archive. **The Marg/medical subsystem
is the one part of this project that never received that pattern**, and it grew to sixty-nine
overlapping documents in which no reader could tell which sentence was current. D351 applies D247's
shape to it.

**The shape.** Exactly three documents, and a fourth that is a specification rather than a record:

1. **`MARG_MEDICAL_CURRENT.md` — what is true NOW.** Small enough to read in full. It is the only
   Marg/medical document opened in the ordinary loop.
2. **`MARG_MEDICAL_HISTORY.md` — append-only, everything that happened.** Indexed, chronological,
   verbatim. Opened on demand only, never in the loop.
3. **`MARG_WALL_CARD.html` — one printed page** that lives physically beside the medical PC, for
   the person standing at the machine with no session open.
4. `MARG_REPORT_EXPECTATIONS.md` — what a correct Marg report must contain.

**The three rules that stop it re-growing, and they are the whole point of the decision:**

- **New knowledge EDITS `CURRENT`, and the text it replaces moves to `HISTORY`. Never a new file.**
- **A session's output is a change to `CURRENT` or an entry in `HISTORY`. Session records are not
  canon.** This is the rule that sixty-nine documents were built by breaking.
- **Anything written to work something out is a WORKING PAPER**, stamped as one at birth, and
  folded at the close.

**Preservation is a precondition, not a consequence.** Nothing is retired until it is copied,
hash-verified, and proven present in a pushed commit. That order is part of the decision, because
the reverse order is how documents are lost.

---

### THE OWNER'S RULINGS THIS SESSION

- **12 June, +8,487 — CLOSED, do not pursue.** A sale report for that day now returns **zero
  sales**, and the only mechanism that would "fix" it re-applies the 12-June report, which
  **deletes that day's attributed and resolved review rows on a closed month**. That is the same
  ground on which it was accepted-but-not-applied at S202. **Not to be reopened without evidence
  from outside Marg.**
- **Token rotation: PARKED** for now. See F-202 — it lives in five stores, not three.
- **Documentation: three files** — current, history, wall card. D351.
- **D350 scope unchanged from S202.**

### THE OWNER'S PREFERENCE CHANGE

*"copy block please, and make it default everywhere."* A copy block is now the default delivery for
**every** machine, not only the VPS, superseding the deliver-a-`.bat`-to-double-click habit. **And
where Claude has write access, it installs directly rather than handing over work.** S203_R3 was
installed that way the same evening.

### THE ASSISTANT'S OWN FAULTS, RECORDED NOT SOFTENED

The fact sheet names five faults as the assistant's own, and a sixth was found while writing this
close (F-206). They are set down here in the same plain terms as everyone else's.

- **A verdict built on a shadowed variable** announced *"the backup target is NOT ATTACHED"* while
  the same report, a few lines up, said **"E: is present."** The report contradicted itself and the
  contradiction was published.
- **A `NameError` shipped twice**, because an insertion anchor matched in **two** places and
  `py_compile` cannot see an undefined name. **`pyflakes` can, and is now used.**
- **`trap … EXIT` was pasted into an interactive shell.** It fired where it was typed, and a
  reverted file sat on disk for a stretch while it was believed restored.
- **A test that counts +2 and proves nothing** — the smoke additions written to close the gate hole
  do not bite. Reverting the gate still gives 721/721. Recorded as green-and-meaningless rather
  than left looking like coverage (F-195).
- **Thirteen documents were produced while consolidating away sixty-nine** (F-205). D351's third
  rule exists because of this session's own behaviour, not in spite of it.

### AF-1 WAS NOT STRUCK — the strike was proposed at this close and REFUSED on measurement

The close carried an instruction to strike **AF-1** on the ground that it is armed against
`GUARD_AND_SEND.bat`, which the medical PC's own file listing proves is not on that machine, and
that the fallback D347 protects — `SEND_TO_CLINIC.bat` — is self-contained.

**The second half is true and the first half is not, and the conclusion does not follow.**
`GUARD_AND_SEND.bat` is 88 lines, calls `guard_and_send.py` and then hands off to the sender, and
**contains no `curl`, no `last_response.txt`, no `sent_hashes.txt` and no `ACCEPTED-FOR-REVIEW`
test at all** — AF-1's mechanism was never in it. AF-1 was recorded against **`SEND_TO_CLINIC.bat`,
kit `S187_M1a`**, and the live file — **`e19a8a777ac22fe75a242f1eb9762185`, which is a verified
S203 pin on the machine right now** — still carries the mechanism intact: `curl -s -m 90 -o
"%RESP%"` with **no `del` of `%RESP%` beforehand**; an `ACCEPTED-FOR-REVIEW` `findstr` on that file
that **never consults `%HTTP%`** (which is captured, and used only in the REFUSED message below);
and, on the ACCEPTED branch, `echo %HASH%>> "%HASHES%"`, which the skip test at the top of the
routine then honours for ever.

**So the fallback is self-contained and the fault is live inside it.** AF-1 stays armed, and the
reason it was nearly struck is itself a finding — **F-206**, and D188's own rule: a filename is not
provenance.

### SHIPPED

`S203_R1` · `S203_R2` · `S203_R3` · `S203_H1` · `S203_B2GATE` · `S203.3` and `S203.6` on the
medical PC. `deploy_kits/`: `MARG_MEDICAL` (5 documents) · `S203_MARG_CANON` (67) ·
`S203_CENSUS_BACKUP` · `S203_LIVE_TOOLS` (15 — five tools that existed nowhere but the two PCs) ·
and the five kit folders. Repo pushed at `f94ff27a…`, before the evening's later kits.

**Verified at this close, by hashing rather than by reading a record:** every kit pin above matches
the file on disk; `MARG_MEDICAL`, `S203_MARG_CANON`, `S203_LIVE_TOOLS`, `S203_R1`, `S203_R2`,
`S203_R3`, `S203_H1` and `S203_B2GATE` each return `md5sum -c` **exit 0**. Two things did not
check out and are recorded rather than smoothed: **`S203_CENSUS_BACKUP` carries no `SUMS.md5`**,
against §11's claim that every folder carries a verified one; and the seven files in
`S203_MARG_CANON` that its `SUMS.md5` does not list were each inspected and are **`SUMS.md5.before_*`
backups of the sums file itself**, not unlisted content — the 67 is right.

**Not yet done at the time of writing:** the manifest rows for the new folders, the Register bump,
`PUBLISH_ALL`, and the on-box pin-list copy.

---

**END OF KB HISTORY ARCHIVE v1.50. §S203 is the last section; §S202, §S201, §S200, §S199, §S198, §S196, §S195, §S194, §S193, §S192, §S191, §S190, §S189, §S188-FINAL, §S188-POST, §S188, §S187, §S186-POST, §S186, §S185, §S184, §S183, §S182, §S181, §S180, §S179, §S178, §S177 and earlier sit above it. The v1.49 end-marker immediately above §S203 is preserved in place as a historical truncation-proof, as are the earlier embedded markers — only this one is live. If §S203 or this marker is absent, this file is truncated and must not be used as canonical.**

---

### §S204 EOS (27 Aug 2026 · Session 204 · FULL build EOS — THE SESSION THAT ASKED WHETHER A PIN IS A BACKUP, AND FOUND THE AUDIT CONVICTING ON ITS OWN TRANSCRIPTION)

Opened on the owner's instruction to **work unattended wherever possible** — *"medical u can do,
manojz publish.bat also shd be able to do, only vps needs setup or claude code, so try to be
independant"* — and, later, *"do wht is best, and does not destabilize the system."* Both were
followed literally: everything below was measured or built by the assistant, and the only live
changes were two the owner executed himself with his own paste.

**1 · PHASE 0 — GREEN, and wider than before.** All 208 present manifest rows verified by md5
across every tier; the two unmatched rows are the D316 CLOSED-AS-LOST pair, which do not halt.
`md5sum -c MD5SUMS_ALL.txt` exit 0 (220/220, **F-119**). `.gitattributes` still pins
`*.md text eol=lf` (**F-190**). Project-knowledge headroom reported as a standing check:
**1,446,959 of 2,000,000 bytes — 72% used**, down from 98% at the S202 close after D351's
retirements. The manifest in project knowledge and the manifest in the repo were found
**byte-identical** (`b104474f…`) — the two stores agree on the linchpin.

**2 · F-200 ANSWERED — THE INVERSE CHECK ACROSS STORES, RUN FOR THE FIRST TIME.** Every one of the
**160 project-knowledge entries** (156 distinct paths) was hashed and looked for among all
**1,952 repo files**, by hash first and name second (D188).

- **102 byte-identical.**
- **9 same-name-different-bytes**, each then verified BY DIFF rather than by hash of a
  reconstruction — and the verdicts were not uniform: **5 real, project knowledge stale**
  (`S190_Staff_Advance_Policy_D331` — project knowledge carries the DESIGN draft *"awaiting the
  owner's OK"* while the repo carries **SIGNED AND EXECUTED** and the manifest pins the repo;
  `S179_Sanjeevni_Medical_Module_Build_Contract_v1` and `S180_Marg_Feed_Transport_Design`, each
  missing its S203 status banner; `S203_KB_CENSUS_PHASE12` and `S203_PENDENCY_RECONCILIATION`,
  each missing D351's WORKING PAPER demotion banner) · **1 real in the OTHER direction**
  (`OWNER_TODO_LIVE`: project knowledge is a full session ahead of the repo snapshot, exactly as
  designed) · **1 three-way fork** (`S196_Health_Renewals_Build_State`: the S197-fold copy silently
  DROPPED the F-155 clause the S196close copy carries while adding its own marker — **a correct
  copy exists nowhere**, F-23's shape) · **1 pair of unrelated files sharing a name**
  (`MD5SUMS.txt`, the S180 pin list against the S181 one — D188 again) · and **1 FALSE ALARM**,
  which became the session's own finding.
- **45 present in project knowledge and absent from the repo entirely.** Among them the **D340–D345
  rulings**, the S200 pin records, the S181 Docterz/UPI/lab forensics, the S184 cash designs.
  **44 were preserved to `D:\dr-manoj-git\_S204_WORK\pk_only\`** with `SUMS.md5` (`md5sum -c` exit
  0, verified on the machine) — deliberately OUTSIDE the git repo, because **F-185 is open and
  repository visibility is the owner's ruling**. The 45th, `Clinic_Contact_QR_Setup_Record.docx`,
  **could not be preserved**: the connector returns extracted text, not the .docx bytes. It remains
  single-copy.

**3 · F-208 — THE AUDIT CONVICTED ON RE-KEYED TEXT (the assistant's own).**
`Diagnostics_Surveillance_System_Spec_v2_3` was reported drifted at `be2db910…`. Re-read and
diffed, the two stores are **byte-identical** at `bdd5fa54…`, matching the manifest pin. The
reported hash was reconstructed and identified exactly: **the canonical document with one
contiguous 4-line block missing — the D114 paragraph in §M1 that names the Fault Register as the
authority.** The transcription had dropped it. No such variant exists anywhere: 15 copies on the
machine, every cold kit, and a full scan of the git object database all give `bdd5fa54…`.
`S181_postclose_addendum.md` §3 had already ruled that re-keyed inline text *"may corroborate,
never convict and never acquit"* — **and this audit convicted on it anyway.** The remedy adopted
and used for the preservation: **transcribe twice, independently, and compare — 42 of 44 converged
byte-for-byte**; the two that did not are the JSON snapshots, whose byte fidelity is therefore
recorded as NOT established.

**4 · THE OWNER'S RULING, MEASURED — DARPAN IS ON THE 50% RULE, AND ONE SYSTEM DID NOT KNOW.**
Told mid-session: *"darpan was finally in same 50% rule."* Checked against the deployed code
first, at the owner's explicit instruction — and against live bytes, not a record: `/root/staff_ledger.py`
is pinned `9e764f80…`, the pin check was GREEN 47/47, and the repo's `S202_D349B` copy hashes to
that same value, so the repo copy IS what runs.

- **Staff ledger:** `advance_pct.json` already said `{"Darpan": 50}`; `staff_master.csv` says base
  20000 — **§5.3 of the S190 document, open since S190, is answered** — so its ceiling was already
  ₹10,000.
- **Sanjeevni drawer:** **no `advance.*` settings rows existed at all**, so `advance_ceiling_p()`
  fell back to its coded default of **75** and was still allowing **₹15,000**.
- The two systems disagreed about the same man. **Corrected by the owner's own paste** —
  `advance.base_p = 2000000`, `advance.pct = 50`. `setting()` reads the DB on every call: no cache,
  **no restart needed**. **D352 minted.**

**5 · THE SIGNED DOCUMENT IS ITSELF BEHIND THE CODE.** The same check found that
`S190_Staff_Advance_Policy_D331`, even in its newer repo form, misdescribes live behaviour on two
points introduced by the same session's later refinements: §3a says month-to-date counts *all*
approved+pending advances in the calendar month, while the code counts **only rows carrying an
explicit `against_month`** (pre-D331 rows grandfathered — the reason Darpan's card once read
*"Rs 3,63,000 of Rs 15,000"*), and **interest-bearing loans bypass the quota gate entirely**, which
the document never states. **The proposed straight copy repo → project knowledge was therefore
WRONG and was not made**: it would have replaced a stale draft with a less stale one that still
misdescribes the live system. An as-built (SL3/SL4) correction block is **owed**, and the owner is
to confirm both behaviours as his rulings before they are written down as policy.

**6 · F-209 — A PIN IS NOT A BACKUP.** All 67 rows of `live_pins_S203close.txt` were checked
against all 1,952 repo files by hash. **61 recoverable. Four existed in ONE PLACE ONLY:**
`/root/finance/finance_app.py` (the clinic's money application; the newest repo copy was the
S202_B2C kit from 01:36 on 26-Aug, **before the S203 gate fix**), `/root/finance/finance_ui/finance_entry.html`
(15-Aug), `/root/deploy/email_agent.py` (21-Aug), and `/root/wa/recordings-archive/make_force_keys.py`
(**no copy, ever**). `verify_live_pins.py` is GREEN on all four, and GREEN is correct — they match
the record. **The record is a hash, not the bytes.**

**7 · KIT `S204_C1` — THE CAPTURE, WITH THE F-185 GATE BUILT IN.** Written offline, `py_compile`
+ `pyflakes` clean, and **red-proofed against a five-case fixture with the projection written
first**: 5 VPS rows / 2 eligible / 1 drift / 1 missing / 1 gated — **all five landed**, exit 1 with
faults, exit 0 clean. On the box: **47 VPS rows · 31 eligible · 0 DRIFT · 0 missing · 16 held by
the gate**, then **CAPTURED 31 of 31**, `md5sum -c` exit 0. Verified again on manojz against
`live_pins_S203close.txt` — an independent reference, not the file the script itself wrote —
**31 match, 0 mismatch.** Three of the four one-copy files are now safe.

**`make_force_keys.py` is still one copy only**: 38 mobile-shaped strings, held back correctly. It
cannot go into a public repo and needs a home that is not git. **OPEN.**

**And a fact the owner must rule on: 15 of the 16 gated files ALREADY sit in the public repo in
older versions.** The gate written this session is stricter than the standard the repository
currently meets — **F-185 in one sentence.**

**8 · F-207 — THE FILE NAMES THE FAULT, THEN COMMITS IT.** At line 9886 of `finance_app.py` the
smoke suite's own comment says *"a hardcoded `15,000.00` would go red the day the owner revises the
base or the pct"* — and sixteen lines below, twice, it hardcodes exactly that literal. The block
around it had been deliberately made state-adaptive (the S184_F1b remedy); the ceiling figure was
left behind. **The warning and the fault are in the same function.**

**Kit `S204_C2`** fixes it, built **from the live bytes captured hours earlier** — impossible
before this session, because the repo's newest copy predated the S203 gate fix and editing it would
have silently reverted B2. Five edits: the coded fallback 75 → 50 in both paths, the selftest's own
default kept in step, the docstring recording that **an exception belongs in a settings row, never
in a fallback**, and the two literals → `rupees(_want_ceil)`. **Edit 5's anchor matches twice on
purpose and the builder asserted the count** (S203's lesson inverted: where an anchor is
deliberately not unique, the count is the check). **Reverse-application returns the file to
`7948cee0…` exactly.** pyflakes reports the same two pre-existing findings as the live file and no
new one, compared list against list.

**The red-proof is recorded honestly as partial**: the failure is a LIVE-DATA failure and cannot be
reproduced offline against a fresh store — F-195's shape, named rather than papered over. What was
proven directly: at pct 50 the OLD check FAILS and the NEW one PASSES; at pct 75 both pass. **State-adaptive,
not a behaviour change.**

**Projection written before installing — and the mechanism checked rather than assumed** (`selftest()`
does `shutil.copyfile(live_db, tmp_db)`, so the throwaway carries the live settings): **720/721
before, 721/721 after, no check added or removed.** Measured: **720/721**, the failing line printing
`ceiling=10,000.00` against the hardcoded `15,000.00`; after install **721/721**, service `active`.
`/root/finance/finance_app.py`: **`7948cee0…` → `70f79997…`**, backup at
`finance_app.py.bak_S204_C2` verified at the old pin.

**9 · F-212 — TWO PUBLISHERS, ONE REPO, AND NO RULE ABOUT WHICH ONE PUBLISHES (the assistant's
own).** The VPS committed the capture locally (no credentials, by design, so the push refused and
fell back to a tarball); the same content was then published from manojz. The two histories
**diverged**, `git pull --ff-only` refused, and the delivery of `S204_C2` failed with
*"No such file or directory"* — a failure whose message named the symptom and not the cause. Fixed
by a **self-guarding block** that proved origin carried identical content before discarding the
box's local commit. **The guard fired twice on the way, correctly**: once on an untracked stray
(`deploy_kits/S195_ENTRY/126278`, an empty file from 21-Aug, moved to `/root/deploy/_stray_S204/`,
never deleted) and once on a real difference — which turned out to be **F-210**.

**10 · F-210 — THE EXECUTABLE BIT DOES NOT SURVIVE THE TRIP.** git's own words:
`mode change 100755 => 100644` on `root__deploy__email_agent.py` and
`root__finance__finance_backup.sh`. The bytes are identical; the mode is not. **`finance_backup.sh`
is a shell script: restored from the repo it will not run.** A hash cannot carry a permission, and
the pin list records neither mode nor ownership — **so a rebuild that verifies GREEN on every hash
can still produce a backup script that silently never runs.** Restore instructions carrying
`chmod +x` were written into the capture's `MANIFEST.md`.

**11 · THE ASSISTANT PUBLISHED, FOR THE FIRST TIME.** With the owner's approval, `PUBLISH_ALL.bat`
was run from the desktop by the assistant (File Explorer, click-only tier — Windows blocks typed
input to the shell, so navigation and a double-click are the whole capability). Four publishes this
session: `5c1cdd8` (kit S204_C1) · `b68507e` (the 31 captured files) · `b0a4c8c` (kit S204_C2) ·
`e2f0407` (the restore note and the pin record). **Each verified by comparing GitHub's HEAD with
the local HEAD**, never by trusting the batch file's own output. A `__pycache__` folder left by the
assistant's own compile check was moved out of the repo before the first publish, and a stale
`.git/index.lock` created by an assistant `git status` was moved to
`D:\dr-manoj-git\_stale_git_locks_S204\` — it would have blocked the owner's next publish. Both
recorded rather than quietly cleaned.

**12 · WHAT WAS DELIBERATELY NOT DONE.** The five stale project-knowledge documents were NOT
overwritten (the S190 case proved the naive rule wrong, and the owner asked for the deployed-code
check first). The S196 three-way fork was NOT merged. The 44 preserved documents were NOT put into
the public repo. `make_force_keys.py` was NOT moved. **Each waits on an owner ruling, and each is
in the owner's list.**

**Decisions: D352.** **Findings: F-207 … F-212** — three of the six are the assistant's own
(F-208, F-210 found by its own guard, F-212). **Next free: D353 · F-213 · A-D25 · Session 205.**

---

**END OF KB HISTORY ARCHIVE v1.51. §S204 is the last section; §S203, §S202, §S201, §S200, §S199, §S198, §S196, §S195, §S194, §S193, §S192, §S191, §S190, §S189, §S188-FINAL, §S188-POST, §S188, §S187, §S186-POST, §S186, §S185, §S184, §S183, §S182, §S181, §S180, §S179, §S178, §S177 and earlier sit above it. The v1.50 and v1.49 end-markers above are preserved in place as historical truncation-proofs — only this one is live. If §S204 or this marker is absent, this file is truncated and must not be used as canonical.**

---

## §S206 — 27 August 2026 · Session 206 · FULL build EOS — THE SESSION THAT RECONCILED EVERY ITEM, AND FOUND THREE OF ITS OWN FAULTS DOING IT

**Headline.** Every item Sanjeevni stocked between 1-Apr-2026 and 26-Aug-2026 was reconciled
against both stock counts. **285 items moved; 239 land exactly; the whole residue is 1,769 units —
0.98 % of the 181,232 units that passed through the shop.** Every one of the 46 unbalanced items
carries a named cause. There is no "other" bucket and no item marked UNEXPLAINED.

**And the reconciliation's first job was to convict its own reader.** Three faults were found, all
in how Marg's reports were being READ, none in the data:

1. **Whole-unit sales read as zero (F-225).** A strip line writes `0:1`; a tube, vial, syringe or
   spray writes `1.0`. The reader understood only the first form — **2,807 lines, 16.3 % of the
   year.** BRUTAFLAM GEL (367 units), DISPO SYRINGE (622), DOLONEX INJ (572), TYCOB 1500 (421),
   DEPOPRED (171) and VOLITRA SPRAY (156) had all been reported as dead stock while selling
   normally.
2. **Credit notes counted as sales (F-224).** `CN…` bills are goods coming BACK, so subtracting
   them makes the error **twice** the quantity. That doubling is what exposed it: TYRO BR was out
   by +704 against 352 CN units. **376 lines, 3,082 units.** `marg_report.py` already handled the
   MONEY side correctly and its docstring says so; the QUANTITY side had never been checked.
3. **The sale report truncates item names at 20 characters (F-223).** `HARD COLLAR ADJ L HOSPIK`
   rings up as `HARD COLLAR ADJ L HO`, which exists in no item master, so its sales attach to a
   code owning no stock while the real item shows purchases with no sales. **11 codes; the largest
   carries 574 units.** **And the obvious test for it is wrong** — the cut can land on a space,
   which is then stripped, so `DISPO SYRINGE NIPRO 3ML` arrives as NINETEEN characters. A
   `len(name) == 20` check misses exactly the biggest cases; the correct test cuts the MASTER name
   and compares.

**None of the four existing cross-checks caught any of the three** — not the bill chain, not the
four-way purchase reconciliation, not `WHOLE = MAIN + DTH + SCRAP`, not the multi-store identity.
All four kept passing throughout. **Only forcing every item to account for itself found them.**
That is the lesson of this session: a check that has never failed may be answering a question
nobody is asking (the F-195 / F-209 / F-215 shape, one layer out).

**THE TWO MISSING MOVEMENT TYPES — NAMED BY THE OWNER, AND ONE IS A HOLE IN THE AUDIT TRAIL.**
The reconciliation could isolate the residue but not explain it, and said so. The owner then named
both:

- **The in-place expiry edit (F-228).** *"I open the stock, press a keyboard command and alter the
  stock quantity and expiry as a method told by tech team."* **That writes NO VOUCHER.** Not a
  sale, not a return, not an adjustment document. So `SALE_BILLWISE` cannot show it,
  `PURCHASE_ITEMWISE` cannot show it, and `STOCK_CLOSING` shows only the result. Worse: a backdated
  "as on 31-March" export is rolled back THROUGH VOUCHERS, so an edit made in June makes the March
  figure disagree with itself and nothing records why. **Measured signature: 8 items zeroed while
  still on the list (~29 units); 11 more reduced but not zeroed (147 units).** The expiry link is
  only partly visible — 2 of the 11 held a batch dated on or before Aug-2026 (18 %) against 4 % of
  normal trading items. **A batch only ever removed appears on no line anywhere**, so the absence
  of evidence is the evidence. **Fix: raise a stock-adjustment / breakage voucher instead. Same
  three minutes, leaves a dated document.**
- **Ravi Medical has no purchase bill at all in May or August (F-229).** Apr had 2, Jun 3, Jul 3,
  then nothing. Goods arrived and are in stock; the paperwork has not. *"the goods are in my
  custody."* Two surpluses are Ravi's — `DOLOGESIC SP` +280 and `OPTIFENAC TBR` +21. **`ETOZOX 90`
  is NOT Ravi's and remains unexplained: 548 on the shelf, 102 on 31-March, zero purchases all
  year, ~₹8,800 at MRP.**

**THE OWNER'S TAXONOMY, ADOPTED THROUGHOUT.** *"tablet or capsule come in strips commonly 10 tabs
each, maybe 15 or rarely less or more."* Quantities now read as **strips + loose** for `1*N` items
and as whole units otherwise. **The class comes from the PACKING, never from Marg's unit label —
55 of 378 labels contradict their own packing** (`ARM SLING L UNISON` is labelled `TAB.`).
Internal arithmetic stays in base units because that is the only way stock, purchase and sale
reconcile; only the presentation converts.

**MARG'S OWN ARITHMETIC, DISCOVERED HERE (F-226).** On `PURCHASE_ITEMWISE`, `loose_qty` is computed
with the pack size AT THE TIME OF THE BILL, while the packing column reprints the CURRENT one.
`INTACOXIA-60`: qty 80, packing shown `1*15`, `loose_qty` 800 = 80 × 10. **`loose_qty` is
authoritative for purchases.** For stock reports, `packs:loose` converts with the packing printed
on its own row and nothing else. Two items disagree between sources and are **reported, not
resolved**: `FOLITRAX 7.5` and `INTACOXIA-60`.

**DUPLICATE ITEM CODES — 79 candidate pairs, and the detector had to be corrected mid-write.** It
compared names word by word and so missed a pure re-ordering: `DISPO SYRINGE NIPRO 3ML` and
`NIPRO 3 ML DISPO SYRINGE` tokenise differently because of `3ML` versus `3 ML`. Comparing the
letters of the squashed name catches it exactly. **That one miss was hiding the clearest split in
the file** — `NIPRO 3 ML DISPO SYRINGE` sits at **−83** with 88 sold and nothing ever purchased,
while its twin holds the whole 600-unit purchase. Seven pairs to merge, 61 empty stubs to delete
(three already carrying a `ZZ`/`ZZZ` prefix somebody added to hide them), 10 to check, 7 to leave.

**THE TWO LISTS.** The March export carries 974 lines, today's 374 — but **617 of the removed lines
were already at zero.** **Only SIX items held stock on 31-March and are gone**, and five of the six
are naming: `THI OQ AP` (254 units, renamed `THIO Q AP`), `PARI 12.5` (→ `PARI CR 12.5`), and four
`LEUKOCRAPE` misspellings (11 units).

**THE 16-CHARACTER BILL PRINT (F-230).** Marg prints 16 characters on a bill and 20 on the sale
report; **17 groups have two or more live items printing identically.** 77 renames were generated
with the identifier protected and the vendor word given up first, **every family sharing one core,
zero collisions, checked after generation rather than assumed.** Two faults were found in the
renamer itself while building it: a size sitting MID-NAME was cut from one token list and appended
from another, producing `ANKLE BINDER L L` on nineteen names; and proposing each size separately
gave `KNEE SUPP HNGD L` beside `KNEE HNGD XL` — both inside sixteen characters and together
unreadable as one product.

**DECISIONS AND OUTPUT.** Two kits published and verified (`228c40f..25d3730`, 60 files, 4,983
insertions): **`S206_SANJEEVNI_RECONCILE`** (25 modules, 47 selftest + 8 verification checks) and
**`S206_SANJEEVNI_MARG_PURCHASE`**, plus `S206_F216_DISPOSITION` and `S206_MANOJZ_AGENT`. **Both
Sanjeevni kits were renamed before their first commit** — free then, expensive after — and the
rename would have broken `ingest.py` silently, since it imports the parsers from the other kit by
path. **The `SANJEEVNI` tag is adopted for every pharmacy artefact going forward.**

**A SELF-CONTAINED SESSION KIT** was built at `D:\Downloads\S206_SANJEEVNI_SESSION_KIT\` — 190
files, 11 MB: the four canonical documents, both code kits, all data, the deliverables, and **46
raw Marg exports**. It rebuilds every figure with no project knowledge, no chat history and no
GitHub; the selftest passes from inside it.

**THE F-100 GATE EARNED ITS KEEP.** `PUBLISH_ALL.bat` refused the publish because
`live_pins_IGNORE_block.tsv` was caught by `.gitignore:40 *.tsv` — a rule sitting under the
PATIENT-DATA block. **A kit file that would have left the repo silently.** Resolved by renaming the
file to `.txt`, **not** by weakening the gate: a `!` exception would make a patient-data rule
conditional, and the file is a config block destined for `live_pins.txt`, which is already `.txt`.
The S205 ruling that the gate stays strict was honoured.

**ASSISTANT FAULTS THIS SESSION, RECORDED NOT SOFTENED.** Four live tokens were printed in chat by
a probe command that ended `grep -iE 'Environment|ExecStart'` — the values were never written to
any document, repo or memory, and all four must be rotated. A bare `git status` was handed to the
owner **after** `PUBLISH_ALL.bat` had been read in the same session — the file contains four
fallback paths for `git.exe` precisely because `where git` fails on manojz. Earlier: sale coverage
reported as 6.8 % of the year when it was 100 %; the gross purchase column summed instead of net,
6.6 % overstated; "28 items sold below cost" from reading MRP-per-pack as a line amount; "19
duplicate item codes" that were a parser fault; "31 orphans" measured at 59 and withdrawn.

**AND A GAP IN THE PREVIOUS CLOSE, FOUND BY MEASUREMENT AT THIS ONE.** **§S205 IS ABSENT FROM THIS
ARCHIVE.** The S205 close produced `HANDOFF_RUNBOOK_2026-08-27_Session205close_v139.md` (A3) but
never ran A1 or A2 — the Archive stayed at v1.51/S204 and the Register at v5.56/S204. **S205's
history is unarchived and is NOT reconstructed here**: writing another session's narrative from its
leftover working documents would be authoring history from second-hand text, which is exactly what
D172 and A0 forbid. **It is recorded as an open item for the owner to rule on.**

**Decisions: none minted.** **Findings: F-223 … F-231 (candidates — the F-series fork is still
unratified).** **Next free: D353 · F-223 · A-D25 · Session 207.**

---

**END OF KB HISTORY ARCHIVE v1.52. §S206 is the last section; §S204, §S203, §S202, §S201, §S200, §S199, §S198, §S196, §S195, §S194, §S193, §S192, §S191, §S190, §S189, §S188-FINAL, §S188-POST, §S188, §S187, §S186-POST, §S186, §S185, §S184, §S183, §S182, §S181, §S180, §S179, §S178, §S177 and earlier sit above it. §S205 IS ABSENT — the S205 close never ran A1; this is a known, recorded gap, not a truncation. The v1.51, v1.50 and v1.49 end-markers above are preserved in place as historical truncation-proofs — only this one is live. If §S206 or this marker is absent, this file is truncated and must not be used as canonical.**
