# HANDOFF RUNBOOK — Session 121 (v55) — 2026-07-07

**Canonical set (FULLY CONSOLIDATED single files — no delta chains, S100 policy):**
- **KB `Clinic_Master_KB_SystemsRegister` v1.45** (consolidated, self-contained) — WINS on any conflict.
- **Umbrella Architecture v1.33** (consolidated, self-contained).
- **This Runbook v55** (self-contained; supersedes v54 / Session 102).

Prior: Session 102 v54.

> **Documentation policy (owner directive, S100, still in force):** canonical docs are built as
> **single fully-consolidated files, not delta chains.** KB v1.45, Umbrella v1.33, and this Runbook
> v55 are all single-file masters.

---

## §0 — WHAT HAPPENED (Sessions 103–121)

This arc completed the **callback-tracker agenda Items 2 and 3**, plus a data-folder evaluation.
**FULL EOS — live PC-side code changed** (`processor.py`).

### Item 2 — auto-settle "didn't pick up but visited" → FOUND ALREADY LIVE (verified S106)
Claude owed a decision sheet and delivered it; owner approved four decisions (match on `Patient_UID`,
cutoff = raise-date strictly-after, silent staff-hide + audit tag, and — owner's change — **visit
beats amber**: a returned patient settles even if the row was reinstated). On reading `processor.py`
Claude found the settle engine **already built**: `compute_followup_status` (~line 1820) matches each
follow-up to a real Docterz visit keyed on `Patient_UID`, using `Followup_Log_Date` with
`COUNT_LOG_DATE_VISIT_AS_RETURN = False` (visit **strictly after** raise-date settles; same-day does
not). Verified on 07-Jul live data: **249 of 493 rows settled**, zero leakage to the staff sheet.
**Item 2 needed no build** — only end-to-end confirmation, now done.

### §107 data-folder / Drive-sync evaluation (S108) → VERIFIED-NORMAL (D147)
Owner asked about "multiple dated CSVs" in the tracker `data\` folder. Finding: normal by design.
`consultation_report_YYYY-MM-DD.csv` = daily raw Docterz inputs (many, dated); `visit_ledger.csv` =
single cumulative ledger (never dated, one fixed path). The `data\` folder is Drive-synced (PC writes
→ Drive mirrors); settle freshness depends on that sync. No code. **D147.**

### Item 3 — staff call-sheet cap + Hard-to-Reach split → BUILT + LIVE (S121, D148)
Owner policy (Sessions 109–114): daily cap **120**; winnable buckets first (Due Today / Grace /
Actionable) in existing order; leftover room drip-filled with **oldest Probable Dropouts**; winnable
overflow **rolls to tomorrow**; **3 no-contact strikes → Hard-to-Reach** tab (name · Clinic ID ·
mobile · diagnosis · last-visit date · attempts; reinstated exempt) for doctor keep/archive;
recording+transcript links deferred (owner choice "b"). Built into `build_staff_call_workbook`
(additive only, +155 lines, 0 removed, two `try/except`-wrapped inserts). Verified on the real
regenerated 07-Jul sheet: **follow-up section = exactly 120 rows** (110 winnable + 10 oldest-dropout
drip), **Hard-to-Reach tab present** (0 patients today — expected), audit workbook untouched/full.
`py_compile` clean on the clinic PC. New `processor.py` md5 **`171a090645da130a4f4cbb0c0b102f22`**.

---

## §1 — STATE / MENTAL MODELS

**Track 2 live systems (unchanged this arc — no VPS/dashboard code touched):**
- Duration gate LIVE + healthy (`call-hook.service` :8098 up; `Call_Durations` filling).
- Dashboard stable; `OutcomeLog.gs` at the D143 build; URL stable.
- WABA sends still BLOCKED vendor-side (D120); `wa_approve` still nohup (not systemd); watchman /
  health report / attendance / follow-up push live; key rotations overdue.

**Track 1 / PC-local:**
- **`processor.py` (follow-up tracker) CHANGED + LIVE** — now carries the D146 de-dupe AND the D148
  cap/Hard-to-Reach split. md5 `171a090645da130a4f4cbb0c0b102f22`. Backup on PC:
  `processor_BACKUP_S115_pre_Item3.py` (= S102 build `8813a27db66c91628153c55912612ceb`).
- Vitals & Plan front-end Step 5 COMPLETE; Step 7 (reconciliation) not started; Hindi spelling task
  in `vitals_page.html` still open.

**Mental models (reinforced this arc):**
- **Item 2 was already built.** The settle engine (`compute_followup_status`) pre-existed; the agenda
  item was really a verification task. Lesson: read the live code before assuming a build is needed.
- **Two builders in `processor.py`:** `build_staff_call_workbook` → staff CALL SHEET
  (`Staff_Action_Today_*.xlsx`, all de-dupe/settle-exclude/cap logic lives here); a second builder →
  doctor AUDIT workbook (`Followup_Audit_*.xlsx`, 9 tabs, deliberately left FULL). Changes to the
  staff builder never touch the audit builder.
- **Order inside `build_staff_call_workbook`:** call overlay → reinstatement merge → **D146 de-dupe**
  → **D148 3-strike split + 120-cap/drip** → write. Each new block is `try/except` fail-safe.
- **Two file-types in `data\`:** dated `consultation_report_*` (fuel, many) vs single
  `visit_ledger.csv` (tank). Everything reads the tank. Multiple dated CSVs are expected.
- **The install file-lock trap:** Windows blocks `wb.save()` if the target `.xlsx` is open in Excel
  (`PermissionError [Errno 13]`). Not a code fault — close the file, re-run.
- Docs are consolidated single files (S100 directive) — build the next canonical version as a full
  fold-in, never a delta.

---

## §2 — BACKLOG (what to pick up next)

### THE SIX-ITEM AGENDA (owner-set S94) — updated standing
- **Item 0 — DONE (S94).** **Item 1 — DONE (S102).** **Item 2 — DONE / already-live, verified (S106).**
  **Item 3 — DONE (S121, D148).**

4. **Live staff-activity summary on the doctor dashboard (NEXT candidate)** — today live + yesterday
   cross-verified/audited against archive + transcripts. Buildable; the "audited" half depends on
   Item 5.
5. **AI audit layer (Stage 3, D62)** — overnight Haiku-tier batch, ~₹200–350/month,
   transcript-vs-claimed-outcome, doctor-only flags. Designed, not built. Doctor-only "Call Audit"
   sheet exists.
6. **Historical taxonomy insights** — analysis only; BLOCKED on a de-identified export. Claude owes
   the de-identified-export spec.

### FAST FOLLOW-UP (carried from Item 3, owner choice "b")
- **Hard-to-Reach recording + transcript links.** Add last call recording + transcript link columns
  to the Hard-to-Reach tab. Those live on Drive + tracker sheet keyed on `Patient_UID` (VPS
  call-transcription job; doctor-only sheet `1rq9VvB5L94EmmZbiUwase9HBLsJ3htispYLd1rHjSRQ`). Verify
  the transcript-metadata join before wiring. Small, well-scoped.

### PRIORITY PENDING (carried)
- **Option B — per-patient "latest state" join.** On the surviving call-sheet row, assemble the
  patient's most-recent visit + most-recent call outcome + its recording + transcript + most-recent
  follow-up. Bigger; overlaps Items 4/5 + Stage-3. (Item 3 was the call-sheet trim only.)

### Track 1 backlog (unchanged)
- Hindi SPELLING corrections in `vitals_page.html` LIB strings.
- Step 7 — new-patient reconciliation (dovetails with the settle machinery; UID-blank rows stitched
  on Clinic ID + mobile).
- Living Clinic Data Map (§66.6).

### Track 2 live backlog (unchanged)
🔴 WABA authorizer/Lokesh + re-fire TEST · make `wa_approve` a systemd service · rotate
`WA_APPROVE_KEY` · 🔴 service-account key rotation (Lokesh) · AKEY_14 · arm timer-freshness checker
+ maintenance jobs · `clinic_health_report.py` UTC→IST fix · courtesy-rotate `CALLHOOK_SECRET` +
`FU_UPLOAD_SECRET` (D145, low-risk hygiene).

### Documentation backlog (housekeeping — owner pushes)
- **Commit the current canonical set to GitHub** — repo `docs/` still lacks the recent KB / Umbrella
  / Runbook versions and the S102 + S121 `processor.py` changes. A sync task, not a lost-file problem.

---

## §3 — KEY PATHS / FACTS

- **Follow-up tracker (PC-local):** `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\`.
  Generator = **`processor.py`** — builds BOTH `Staff_Action_Today_*.xlsx` (staff call sheet, via
  `build_staff_call_workbook`) and `Followup_Audit_*.xlsx` (doctor audit, 9 tabs). Owner uses
  `python` (not `python3`) to `py_compile`. Current md5 `171a090645da130a4f4cbb0c0b102f22`; backup
  `processor_BACKUP_S115_pre_Item3.py` (= `8813a27db66c91628153c55912612ceb`).
- **Item 3 tuning constants (in `build_staff_call_workbook`):** `DAILY_CALL_CAP = 120`,
  `STRIKE_LIMIT = 3`. Winnable = {Due Today, Grace Period, Actionable Missed Follow-Up}.
- **Settle engine (Item 2):** `compute_followup_status` (~line 1820); `COUNT_LOG_DATE_VISIT_AS_RETURN
  = False` (visit strictly after `Followup_Log_Date` settles); `EXPIRY_DAYS = 60`.
- **Data folder:** `data\` under the tracker; Drive-synced. `consultation_report_YYYY-MM-DD.csv` =
  daily inputs (many); `visit_ledger.csv` = single cumulative ledger (never dated).
- **Manual follow-up push:** CMD → `cd "C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker"`
  → `python push_followups_today.py --push`. No flag = preview.
- **Call-hook:** `call_hook_capture.py` as `call-hook.service`, gunicorn 127.0.0.1:8098; OLS
  `/mo-callhook` → 8098; raw logs `/root/wa/call-hook/call_hook_logs/YYYY-MM-DD.jsonl`; secret gate
  `CALLHOOK_SECRET` in `/root/wa/.env` (plain-alphanumeric, D144). Join key `client_ref_id`; connect
  = customer leg answered + talk ≥15s → `Call_Durations`.
- **Dashboard Apps Script files:** `WebApp`, `Callconsole`, `OutcomeLog`, `Dashboard.html`, plus
  config/MyOperator/Netting/Sheets/Main/Monitor/CallField/Probe/Diagnostics. Deploy rule: **edit
  existing deployment → New version** (never New deployment — changes the URL).
- **Sheet:** Clinic Callback Tracker `1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0`. Doctor-only Call
  Audit / transcript metadata `1rq9VvB5L94EmmZbiUwase9HBLsJ3htispYLd1rHjSRQ`.
- **VPS python:** always `/root/wa/venv/bin/python3`.
- **Canonical docs (single-file masters):** KB v1.45 · Umbrella v1.33 · Runbook v55.

---

## §4 — SESSION-START CHECKS (unchanged)
1. `System_Health` tab — any open incidents?
2. Call-hook healthy? (any stuck "Checking…" tiles; is today's `YYYY-MM-DD.jsonl` raw-log present?)
3. Any fault codes / banners from staff since last session?
If any incident open → address before new build. Else read KB + runbook, confirm, ask which backlog
item to start. **Default next execution item: agenda Item 4 (live staff-activity summary on the
doctor dashboard) OR the small Hard-to-Reach recording/transcript fast-follow-up — owner's pick.**
