# Dr. Manoj Clinic — Umbrella Architecture · v1.27 (DELTA over v1.26)

**Session 73 · 05 Jul 2026 · Track 1 (hosted plan-tool + vitals). Offline build; no live code.**

Base: v1.26 (Session 67). This delta adds the printout-archiving layer and the "host both together"
operating decision. Everything in v1.26 stands.

---

## 1. Operating decision — host plan-tool + vitals TOGETHER, once the backend works

The Track-1 target is now stated plainly: **build the whole thing (plan-tool + vitals + the backend
write-path) and host it at ONE time.** Offline artifacts (v24 lookup, v25 vitals, v26 plan-record) are
staging steps — the "final online version" is locked only after the backend actually writes ledgers +
PDFs end-to-end. This tightens the definition of "done" (hosting = done) without changing the locked
build order. It fits the hub-and-spoke law: the hosted tool becomes a single spoke that owns its own
write files (`vitals_ledger`, `plan_ledger`, `plan_archive/`) and only READS the Docterz-derived CSVs.

## 2. New layer — printout PDF archive (D132/D133/D134)

A third tool-owned write target joins the two ledgers: **`plan_archive/`** — a patient-tagged store of the
actual PDFs handed to the patient.

- **Both sheets archived** (patient + physio) per visit — the frozen record of what was given.
- **Tagged on the same spine as everything else** — `Patient_UID` (D128), with year + `Plan_Date` +
  `Plan_ID` so it joins cleanly to `plan_ledger` (which now carries `Plan_PDF_Patient` /
  `Plan_PDF_Physio` pointers, D134). New patients → `pending/` bucket, stitched on reconciliation (D131).
- **VPS is home (D133)** — reliable local writes, one-writer-per-file, no dependency on Drive at print
  time. Drive mirror deferred (owner: browse-in-Drive not essential). If ever wanted, the mirror reuses
  the recording-archive OAuth-as-owner pattern (D36).
- **Server-side generation** — PDFs are produced by the hosted server, not the browser (a web page can't
  silently file a PDF to disk). This is why archiving is a hosting-stage capability; offline the tool only
  previews the paths.
- **Cost is a non-issue** — ~100 MB/year at current load (<10 printed plans/day). Yearly folders make any
  future archive-off a one-move operation.

## 3. Single-writer principle extended

`plan_archive/` is written by the same hosted tool that owns `plan_ledger` — the plan-tool is the sole
writer of its own three artifacts (plan_ledger, plan_archive, and — via the one shared vitals writer —
vitals_ledger rows it captures through its embedded vitals door). The measurement still lives once
(vitals_ledger); the plan points at it (`Vitals_ID_Used`); the PDF is the frozen output, pointed at from
plan_ledger. No data duplicated to drift.

## 4. Decisions this session
- **D132** — archive both printout PDFs, patient-tagged, pending bucket, ~100 MB/yr, server-side generated.
- **D133** — storage home VPS canonical, Drive mirror deferred.
- **D134** — plan_ledger +2 PDF-path columns (new 14-col order; KB §67.3-AMENDED).

## 5. Growth path (unchanged order, tighter "done")
Owner real-Chrome check of v26 → **next session: vitals tool** → build the server-side write-path (vitals
writer + plan_ledger writer + PDF archiving) → **host plan-tool + vitals together** (D121/D122) → staff
BP-only page → new-patient reconciliation job. Standing: living Clinic Data Map (§66.6), now including
`plan_archive/`.
