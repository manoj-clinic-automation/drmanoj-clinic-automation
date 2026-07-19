# HANDOFF RUNBOOK — Session 73 · v48 · 2026-07-05

**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · with: Claude**
**FULL EOS — plan-tool v26 built offline; NO live/VPS code touched.** Baseline in:
KB v1.36, Umbrella v1.26, Runbook v47 (S67). Baseline out: **KB v1.37 (delta over v1.36),
Umbrella v1.27, Runbook v48 (S73).** **KB wins on any conflict.**

---

## §0 — WHAT HAPPENED THIS SESSION (S73)

Full BUILD session on **Track 1** (hosted plan-tool + vitals). All offline; no VPS.

1. **Owner steering decision:** build plan-tool + vitals fully, do the backend work, and **host BOTH
   TOGETHER at one time** — the "final online version" is locked only once everything is built and the
   backend works end-to-end. Offline builds are staging steps, not finish lines. (Does not change the
   Track-1 build ORDER; changes when a piece is "done" = hosting.)
2. **Locked PDF archiving of printouts** — D132 (archive both patient + physio PDFs, tagged
   `plan_archive/<year>/<Patient_UID>/<Plan_Date>_<Plan_ID>_{patient|physio}.pdf`; new patients →
   `pending/` bucket, stitched on reconciliation; ~100 MB/yr, negligible). D133 (storage home = VPS
   canonical, Drive mirror deferred — owner "just save it reliably"). D134 (`plan_ledger` +2 columns).
3. **Amended the `plan_ledger` schema** — added `Plan_PDF_Patient` + `Plan_PDF_Physio`; new 14-column
   order (KB §67.3-AMENDED). vitals_ledger schema unchanged.
4. **Built v26** — `rehab_nutrition_plan_v26.html` (md5 `6212ad8fe5072521cadb36b21f190ffa`, from v25
   `92e3c637d0742d3ae1775ab21f871ea1`). New collapsed "Plan record" panel (button + on-demand preview
   only, no live line — owner wanted the front uncluttered). Reads real multi-condition blocks +
   comorbidities + diet → exact 14-col plan_ledger row incl. both PDF-path fields. Two print buttons set
   a silent print-flag → truthful `Sheets_Printed` + PDF paths. Node parse OK; 3-scenario headless test
   passed. **Delivered offline — awaiting owner's real-Chrome check.**

**Decisions:** D132, D133, D134 (KB §73.5).

---

## §1 — STATE (unchanged; no live code touched)

Identical to S64/S65/S66/S67 close — see KB v1.36 §12 verbatim. WABA bridge BUILT+LIVE, sends BLOCKED
vendor-side (D120); `wa_approve` still nohup (not systemd); key rotation overdue; health report /
watchman / attendance / follow-up push all live as before.

**The plan-tool is NOT live** — v26 is an offline Thread-A artifact (not hosted, not committed).

---

## §2 — BACKLOG (what to pick up next)

### Track 1 — hosted plan-tool + vitals (this session's track)
Schemas LOCKED; v24 + v25 + v26 built (v24/v25 approved, v26 awaiting real-Chrome check). Next in order:

1. **Owner real-Chrome check of v26** — expand "Plan record" → Assemble plan record; confirm the row
   reads conditions/comorbidities/diet correctly and `Sheets_Printed` + PDF paths match what was printed.
   (Offline the PDF path shows `pending/` + `<Plan_ID>` — expected; on-screen note explains.) This CLOSES
   Track-1 Step 1.
2. **NEXT SESSION START — the vitals tool**, toward **hosting plan-tool + vitals TOGETHER** (owner's
   decision). Confirm the vitals section (v25) is complete/aligned; design the server-side write-path so
   both tools host at once.
3. **Host the tool(s)** (Flask + OLS, own private port, key-gated — D121). FIRST confirm on the VPS the
   exact folder the tracker syncs `patient_master.csv` + `patient_diagnosis.csv` to (D122); if not yet
   synced, add that one sync step. OLS forwards the FULL path → Flask answers at its context path.
4. **Real server-side write path** — the single vitals writer (appends to `vitals_ledger.csv`, computes
   BMI/category/ratio for every row per D131, assigns `Vitals_ID`) + the plan_ledger writer (assigns
   `Plan_ID`, links `Vitals_ID_Used`) + **PDF archiving** (generates + saves both sheet PDFs to the D132
   paths, resolves real UID folder + Plan_ID).
5. **Staff BP-only page** (D124/D127/D131) — measurement fields ONLY, NO calc on screen; writes through
   the same one vitals writer.
6. **New-patient reconciliation job** (D131) — stitch UID-blank rows + `pending/` PDFs to the real Docterz
   UID once the tracker ingests them (match on Clinic ID + mobile).

Plan-tool current artifact: **v26** (`rehab_nutrition_plan_v26.html`, md5 `6212ad8fe5072521cadb36b21f190ffa`).

### STANDING (surfaces every session until done)
- **📘 Living "Clinic Data Map"** (KB §66.6) — one exhaustive research/doc pass of the ENTIRE data
  structure incl. the verified Docterz headwater (§67.1) + the new plan_archive PDF store, kept updated
  on every file/column/writer change. Canonical alongside the KB.

### Track 2 — live-systems backlog (unchanged, carried from v47)
1. **🔴 WABA authorizer fault (D120)** — Lokesh must fix MyOperator publicapi AWS gateway; blocks ALL
   WABA sends; re-fire TEST when it clears. AWS request-id `eb82db53-47b2-48f1-b744-027a754be56c`.
2. **Make `wa_approve` a systemd service** (`wa-approver.service`) — nohup dies on SSH close; add to watchman.
3. **Rotate `WA_APPROVE_KEY`** + service-account key (Tier A1) + AKEY_14.
4. **Upstream watcher dup bug** — true-identical rows; `inspect_dupes.py`; sender unchanged (D119).
5. Arm timer-freshness checker + maintenance jobs (disk → token-age → log-prune → backup); verify & close
   "Agent shows as Staff"; `call_transcription.py` GitHub commit; Stage-3 AI verdict layer;
   clinic_health_report.py UTC→IST fix; Orthopedic_Clinic_Rehab_Nutrition_v12.xlsm audit fixes
   (My_Plan!B31 #NAME? etc.); GitHub commit S59–S64; data pass; P1–P10 lock; D78 sticky counter.

---

## §3 — DECISIONS THIS SESSION
D132 (archive both printout PDFs, tagged by UID/date/Plan_ID, pending bucket, ~100 MB/yr, server-side) ·
D133 (storage home VPS canonical, Drive mirror deferred) · D134 (plan_ledger +2 PDF-path columns; new
14-col order). Full text KB §73.5 + §67.3-AMENDED.

---

## §4 — FILES
- **Delivered offline:** `rehab_nutrition_plan_v26.html` (md5 `6212ad8fe5072521cadb36b21f190ffa`).
- **Docs (this EOS):** KB v1.37 delta, Umbrella v1.27 delta, this Runbook v48. Notion decisions log
  updated (D132–D134). No GitHub commit — nothing live changed (v26 is an offline artifact; commit if/when
  the owner wants it versioned, but it is not live code).
