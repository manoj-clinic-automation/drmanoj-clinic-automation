# HANDOFF RUNBOOK — Session 102 (v54) — 2026-07-07

**Canonical set (FULLY CONSOLIDATED single files — no delta chains, S100 policy):**
- **KB `Clinic_Master_KB_SystemsRegister` v1.44** (consolidated, self-contained) — WINS on any conflict.
- **Umbrella Architecture v1.32** (consolidated, self-contained).
- **This Runbook v54** (self-contained; supersedes v53 / Session 100).

Prior: Session 100 v53.

> **Documentation policy (owner directive, S100, still in force):** canonical docs are built as
> **single fully-consolidated files, not delta chains.** Each new canonical version folds
> everything into one self-contained master with one changelog. KB v1.44, Umbrella v1.32, and this
> Runbook v54 are all single-file masters.

---

## §0 — WHAT HAPPENED (Session 102)

**FULL EOS. Live PC-side code changed** (`processor.py`). This session executed **Item 1** of the
owner's six-item agenda — **duplicate patient entries on the daily staff call sheet** — end to end,
and it is DONE and VERIFIED on the day's real sheet.

### The problem (root cause, verified from real data — not assumed)
The daily staff call sheet `Staff_Action_Today_*.xlsx` showed the same patient two or three times.
Cause found by reading today's actual workbook: a patient carries **several OPEN follow-ups from
different visit cycles** (each its own `Followup_ID`/KEY), because earlier cycles were never closed,
so they all land on one day's sheet. **No KEY repeats** — so this is NOT the old byte-identical
watcher bug; it is un-collapsed multi-cycle follow-ups. On 07-Jul: 236 follow-up rows, 22 duplicate
groups (some same-date near-simultaneous double-generations, most different-date open cycles).

### The fix (D146)
A single collapse step was inserted into **`build_staff_call_workbook`** in `processor.py` (the
follow-up tracker's list builder, at `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\`).
It runs on the final follow-up list AFTER the call overlay + reinstatement merge, BEFORE rows are
written — so only the FOLLOW-UP section is affected. Rule (owner-confirmed):
- Group by **mobile + name + diagnosis** (two different clinical problems stay separate rows).
- Keep only the **most recent follow-up cycle** = latest `Due_Date`. **Older cycles hidden, NO note.**
- **EXCEPTION: a reinstated ("call back & complete", amber) row always wins its group.**
- Blank/invalid mobile → group by name only.
- Wrapped in `try/except` → any error falls back to the full list; can never break the sheet.

### Verified live
- 236 → 214 follow-up rows; zero duplicate groups remain.
- Rakesh Kumar → 1 row (29-Jun amber reinstated WON). Chandraprabha → 1. Satwinder Kaur → 1 (03-Jul).
- `python -m py_compile processor.py` clean on the clinic PC (owner-confirmed).
- New `processor.py` md5 `8813a27db66c91628153c55912612ceb`. Backup on PC: `processor_BACKUP_S102.py`.

### Deliberately NOT done (by design, recorded so it isn't mistaken for a regression)
- The **audit workbook** (`Followup_Audit_*.xlsx`) is **left un-deduped** — it is the doctor's
  oversight microscope; only the staff call sheet is collapsed.
- The sheet does **not** yet drop patients who quietly returned after a follow-up was raised — that
  is **agenda Item 2** (auto-settle on a real Docterz visit), the next task.

---

## §1 — STATE / MENTAL MODELS

**Track 2 live systems (unchanged this session — no VPS/dashboard code touched):**
- Duration gate LIVE and healthy (`call-hook.service` :8098 up, `Call_Durations` filling).
- Dashboard stable; `OutcomeLog.gs` at the D143 build; URL stable.
- WABA sends still BLOCKED vendor-side (D120); `wa_approve` still nohup (not systemd); watchman /
  health report / attendance / follow-up push live; key rotations overdue.

**Track 1 / PC-local:**
- **`processor.py` (follow-up tracker) CHANGED + LIVE** — carries the D146 de-dupe.
- Vitals & Plan front-end Step 5 COMPLETE; Step 7 (reconciliation) not started; Hindi spelling
  task in `vitals_page.html` still open.

**Mental models (reinforced S102):**
- **Duplicates are PC-side, fixed at GENERATION, not display.** Confirmed again this session.
- **Two builders live in `processor.py`:** `build_staff_call_workbook` → the staff CALL SHEET
  (`Staff_Action_Today_*.xlsx`); a second builder → the doctor AUDIT workbook
  (`Followup_Audit_*.xlsx`, 9 tabs). They are separate paths — a change to one does not touch the
  other. The de-dupe went into the call-sheet builder only.
- **The de-dupe is fail-safe** — try/except fallback to the full list; a bug can never blank the sheet.
- Docs are consolidated single files (S100 directive) — build the next canonical version as a full
  fold-in, never a delta.

---

## §2 — BACKLOG (what to pick up next)

### THE SIX-ITEM AGENDA (owner-set S94) — updated standing
- **Item 0 — DONE (S94).** **Item 1 — DONE (S102, this session).**

2. **Reconcile "didn't pick up but visited" (NEXT).** Auto-settle a follow-up when the patient
   actually returns (proof = a new Docterz visit after the follow-up was raised). Overlaps
   **Track-1 Step 7**. **Claude owes a one-page DECISION SHEET** before this build (which visits
   qualify, what outcome to write, where it runs). HIGH VALUE.
3. **Trim the >200 staff list** — needs an OWNER POLICY call (caps; where the 124 Probable-Dropouts
   go). Partly pre-designed as D66 "Living Staff List." **Claude owes a one-page DECISION SHEET.**
4. **Live staff-activity summary on doctor dashboard** — today live + yesterday audited (audited
   half depends on Item 5).
5. **AI audit layer (Stage 3, D62)** — overnight Haiku batch, ~₹200–350/mo, doctor-only flags.
6. **Historical taxonomy insights** — analysis only; BLOCKED on a de-identified export. **Claude
   owes the de-identified-export spec.**

### NEW — priority pending added S102
- **Option B — per-patient "latest state" join.** On the surviving call-sheet row, assemble the
  patient's **most-recent visit + most-recent call outcome + its recording + transcript +
  most-recent follow-up.** Bigger task — needs the Docterz visit feed + `Call_Durations` /
  call-transcription sources wired in; overlaps Items 2 & 4 and the Stage-3 audit layer. S102's fix
  was the call-sheet de-dupe only (Option A).

### Track 1 backlog (unchanged)
- Hindi SPELLING corrections in `vitals_page.html` LIB strings.
- Step 7 — new-patient reconciliation (dovetails with agenda Item 2).
- Living Clinic Data Map (§66.6).

### Track 2 live backlog (unchanged)
🔴 WABA authorizer/Lokesh + re-fire TEST · make `wa_approve` a systemd service · rotate
`WA_APPROVE_KEY` · 🔴 service-account key rotation (Lokesh) · AKEY_14 · arm timer-freshness checker
+ maintenance jobs · `clinic_health_report.py` UTC→IST fix · courtesy-rotate `CALLHOOK_SECRET` +
`FU_UPLOAD_SECRET` (D145, low-risk hygiene).

### Documentation backlog (housekeeping, low priority — owner pushes)
- **Commit the current canonical set to GitHub** — repo `docs/` lacks KB v1.38/v1.40/v1.42/v1.43/
  **v1.44**, Umbrella v1.29/v1.30/v1.31/**v1.32**, Runbook v53/**v54**, Call_Console v1.5, the API
  card, and this session's `processor.py` change. Not a lost-file problem — a sync task.

---

## §3 — KEY PATHS / FACTS

- **Follow-up tracker (PC-local):** `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\`.
  Generator = **`processor.py`** — builds BOTH `Staff_Action_Today_*.xlsx` (staff call sheet, via
  `build_staff_call_workbook`) and `Followup_Audit_*.xlsx` (doctor audit, 9 tabs). Owner uses
  `python` (not `python3`) to `py_compile`. S102 backup: `processor_BACKUP_S102.py`.
- **Manual follow-up push:** CMD → `cd "C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker"`
  → `python push_followups_today.py --push`. No flag = preview.
- **Call-hook:** `call_hook_capture.py` as `call-hook.service`, gunicorn 127.0.0.1:8098; OLS
  `/mo-callhook` → 8098; raw logs `/root/wa/call-hook/call_hook_logs/YYYY-MM-DD.jsonl`; secret gate
  = `CALLHOOK_SECRET` in `/root/wa/.env` (plain-alphanumeric, D144); panel Call webhook `?key=`
  must match. Join key `client_ref_id`; connect = customer leg answered + talk ≥15s → `Call_Durations`.
- **Dashboard Apps Script files:** `WebApp`, `Callconsole`, `OutcomeLog`, `Dashboard.html`, plus
  config/MyOperator/Netting/Sheets/Main/Monitor/CallField/Probe/Diagnostics. Deploy rule: **edit
  existing deployment → New version** (never New deployment — that changes the URL).
- **Sheet:** Clinic Callback Tracker `1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0`.
- **VPS python:** always `/root/wa/venv/bin/python3`.
- **Canonical docs (single-file masters):** KB v1.44 · Umbrella v1.32 · Runbook v54. Recovered from
  cold kit: Umbrella v1.28 base + v1.19 delta. Recoverable from GitHub `docs/`: KB v1.37 delta,
  Umbrella v1.27 delta, older history.

---

## §4 — SESSION-START CHECKS (unchanged)
1. `System_Health` tab — any open incidents?
2. Call-hook healthy? (any stuck "Checking…" tiles; is today's `YYYY-MM-DD.jsonl` raw-log present?)
3. Any fault codes / banners from staff since last session?
If any incident open → address before new build. Else read KB + runbook, confirm, ask which backlog
item to start. **Default next execution item: agenda Item 2 (reconcile "didn't pick up but visited")
— Claude to bring the one-page DECISION SHEET first.**
