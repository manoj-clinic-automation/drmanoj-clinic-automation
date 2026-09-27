# S284 BUILD BRIEF — the parent · for session 286 · written at the S284 close, 27-Sep-2026

## §0 · The mandate
The Callback Tracker moves to the clinic server (D634), on the owner's delegation: *keep the flow and the display identical.* The plan is `CALLBACK_TRACKER_VPS_PLAN_v1.md` (project knowledge; `03_WORKING_PAPERS\S284\`). This brief says how to start it.

## §1 · What the tracker is, in files
`deploy_kits/GAS_CURRENT/ClinicCallbackTracker/` holds the live Apps Script, byte-identical to the editor at version 83 (27-Sep): `WebApp.gs` (the web app's doGet and every `google.script.run` target), `Dashboard.html` (the one page staff use), `Callconsole.gs`, `Main.gs`, `MyOperator.gs`, `OutcomeLog.gs` and the rest; `SUMS.md5` 29/29. Project id `148sj-FT…` under drmka.ortho (u/1); deployment `AKfycbyoQ5R3yv…` — **every change is a new version of the existing deployment, never a new deployment, with GAS_CURRENT updated in the same breath (D577, D583).**

The sheet's tabs the page reads and writes include `Followups_Today`, `Followup_Outcomes` (18 headers; key `IN_<phone>_<yyyyMMdd>`), `Followup_Escalations` (13), `WA_Inbox` (9 incl. *sent by*), `Agents`, `Patient_Master`. The server already writes `Followup_Outcomes` in the tracker's own shape (S419 `ring_outcome.py`) and already reads the sheet through the venv's gspread (key found by content in `/root/wa`, sheet id from `push_followups_vps.py`).

## §2 · Stage 0 — ground truth (no change anywhere)
1. From `WebApp.gs`: list every function the page calls (`grep -o "google.script.run[^;]*"` over `Dashboard.html` gives the names), each with its arguments, its return shape, and the tabs it touches. Write it as a table in `03_WORKING_PAPERS\S286\`.
2. List the project's Google triggers (the editor's Triggers page, read by a sub-agent — screens never enter the main thread).
3. The box: CPU, memory, disk (from the bundle's info or one read-only line); the portal's gunicorn workers.

## §3 · Stage 1 — the read-only twin
`/portal/tracker` serves `Dashboard.html` (the GAS_CURRENT bytes) with a small shim script injected that defines `google.script.run` and forwards each call to `/portal/tracker/api/<function>`; the server functions read the same sheet and answer in the same shape. Writes answer *read-only* in stage 1. A daily comparison (server answer vs Google's for the same list) writes one health row. Doctor-only until stage 4.

**Also before stage 1:** confirm `ring_outcomes.db` has a second store — read `sheets_pull.py`'s tab list; if `Followup_Outcomes` is not pulled, add the db to `SRC_FILES` of the state backup (F-647's rule; a new kit, S429's bytes as FROM if it is installed).

## §4 · The rest of the plan
Stages 2–6 as in the plan. Nothing switched off before stage 5; the owner's preview beside Google's, then his one yes.

## §5 · Also open
S429's line (after the publish) · the July Vitals sheets through `/portal/vitals/archive` when his Chrome is reachable (D635) · the 1-Oct monthly copy (a check is scheduled in the S284 chat for 09:30 IST) · the 4-Oct Apps Script row.

## §6 · First acts
Phase 0 → the board claim (286) → the pin check against the 28-Sep bundle → stage 0.
