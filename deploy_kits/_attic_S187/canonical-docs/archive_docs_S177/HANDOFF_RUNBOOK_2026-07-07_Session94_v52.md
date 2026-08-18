# HANDOFF RUNBOOK — Session 94 (v52) — 2026-07-07

**Canonical set:** KB v1.38 + v1.39 + v1.40 + **v1.41 delta** · Umbrella v1.28 + v1.29 +
**v1.30 delta** (unchanged this session) · this Runbook **v52**.
Prior: Session 93 v51.

---

## §0 — WHAT HAPPENED (Session 94)

A **live-systems incident session on Track 2.** Opened on a routine manual follow-up push,
became two fault repairs, then a full project examination and a six-item forward agenda.

### 1. Manual follow-up push (routine, resolved a confusion)
Owner was late generating the staff action sheet and pushed it by hand. Clarified the
long-standing preview-vs-push confusion: **running the script with no flag = PREVIEW
(writes nothing); adding `--push` = LIVE write.** Same script, only the flag differs.
Double-clicking the script runs it in preview by default — which is why "nothing happened"
was confusing. Always push via CMD in the tracker folder with `--push` on the end.
Today's push: 238 worklist rows / 150 settled, pushed live and confirmed.

### 2. Incident 1 — call-webhook 403 outage (FIXED, verified end-to-end)
Staff tiles stuck on "⌛ Checking the call…" even after real >15s connected calls; outcome
never unlocked. Root cause: the VPS `/root/wa/.env` had **two secrets merged onto one line**
(a lost newline joined `CALLHOOK_SECRET` with a trailing `FU_UPLOAD_SECRET=…` fragment), so
the receiver read `CALLHOOK_SECRET` as junk → every MyOperator call webhook 403'd → nothing
reached `Call_Durations` → the duration gate could never unlock. WhatsApp was unaffected
because its webhook key has no special chars and a clean `FU_UPLOAD_SECRET` on line 18 kept
the upload catcher alive.
**Fixed:** backed up `.env`, rewrote line 17 to a fresh **plain-alphanumeric** call key
(removing the `@`), restarted `call-hook.service` (verified healthy), updated the panel's
Call webhook `?key=`. **Confirmed working:** Shavez called, tile resolved, outcome saved.
New fault code `CALLHOOK_SECRET_MISMATCH_403`. Standard set: webhook gate keys must be
plain-alphanumeric (D144).

### 3. Incident 2 — doctor console "isGenericAgent_ is not defined" (FIXED)
Doctor **Outcome Review → Today** view threw "Could not load: isGenericAgent_ is not
defined" (Yesterday worked). Static scan of the live Apps Script export: `OutcomeLog.gs`
line ~333 calls a helper **defined nowhere**; it is the project's ONLY genuine
undefined-function fault (4 other flags were false positives).
**Fixed (D143):** added the one missing helper (generic = staff/doctor/unknown/agent/system/
blank), delivered as a **full-file replacement** built from the live export, `node --check`
PASS, deployed as a **New version** of the existing deployment (URL stable). Owner confirmed
"all good now."

### 4. Project examination + six-item agenda (design only, no further code)
Full static analysis run from the JSON export. Key facts: dashboard does **not** de-dupe the
worklist (duplicates are **PC-side**); today's list was **238 rows dominated by 124 Probable
Dropouts**. Owner set six enhancement items; Claude assessed each against the real code and
recommended: do the safe/ready ones now, decision-sheet the design-heavy ones. See §2.

---

## §1 — STATE / MENTAL MODELS

**Track 2 live systems:**
- **Duration gate LIVE and healthy again** — `call-hook.service` (:8098) up, `Call_Durations`
  filling, outcome unlock working. S94 403 outage CLOSED.
- **Dashboard** — `OutcomeLog.gs` updated (D143) and redeployed as a New version; URL stable;
  Today outcome view works.
- Everything else unchanged from S93: WABA sends still BLOCKED vendor-side (D120); `wa_approve`
  still nohup (not systemd); watchman / health report / attendance / follow-up push live;
  key rotations overdue.

**Track 1:** unchanged this session. Step 5 COMPLETE; Step 7 (reconciliation) not started;
Hindi spelling task still open.

**Mental models reinforced this session:**
- **The duration gate depends on a fragile chain:** MyOperator Call webhook → OLS `/mo-callhook`
  → `call-hook` receiver → secret gate → `Call_Durations` tab → dashboard poll. A break
  *anywhere* shows up to staff as a permanent "Checking…". First diagnostic when tiles stick:
  check for today's `YYYY-MM-DD.jsonl` raw-log file and the panel webhook status.
- **`.env` is edited by hand and can silently merge lines** — always `grep` to verify a repair
  landed on separate lines before restarting; keep a timestamped backup first.
- **Duplicates are PC-side, not dashboard-side** — fix at generation, not display.

---

## §2 — BACKLOG (what to pick up next)

### THE SIX-ITEM AGENDA (owner-set S94) — recommended order
**Item 0 — DONE this session** (isGenericAgent_ fix; Today console works).

1. **Duplicate patient entries (NEXT, SAFE).** PC-side de-dupe. Before building, see today's
   `Staff_Action_Today_*.xlsx` (or two duplicate rows) to learn *why* a patient doubles —
   same section twice, or two different sections. That decides the collapse rule.
2. **Reconcile "didn't pick up but visited"** — auto-settle on a real Docterz visit. Design
   together with **Track-1 Step 7** (shared Clinic-ID + mobile match). Needs design decisions.
3. **Trim the >200 staff list** — needs an OWNER POLICY call (caps; where the 124 dropouts
   go). Partly pre-designed as D66 "Living Staff List."
4. **Live staff-activity summary on doctor dashboard** — today live + yesterday audited.
   Audited half depends on item 5.
5. **AI audit layer (Stage 3, D62)** — overnight Haiku batch, ~₹200–350/mo, doctor-only flags.
6. **Historical taxonomy insights** — analysis only; BLOCKED on a de-identified export.

**Claude to prepare next session:** a one-page DECISION SHEET for items 2 and 3 (the exact
choices needed), and the de-identified export spec for item 6, so the next session is pure
execution.

### Track 1 backlog (unchanged, when owner returns to it)
- Hindi SPELLING corrections in `vitals_page.html` LIB strings.
- Step 7 — new-patient reconciliation (dovetails with agenda item 2).
- Living Clinic Data Map (§66.6).

### Track 2 live backlog (unchanged)
🔴 WABA authorizer/Lokesh + re-fire TEST · make `wa_approve` a systemd service · rotate
`WA_APPROVE_KEY` · 🔴 service-account key rotation (Lokesh) · AKEY_14 · arm timer-freshness
checker + maintenance jobs · clinic_health_report UTC→IST fix · **NEW: courtesy-rotate
`CALLHOOK_SECRET` + `FU_UPLOAD_SECRET`** (D145, low-risk hygiene) · **NEW: consider a
`CALLHOOK_SECRET_MISMATCH_403` detector** (panel Failed OR no daily raw-log by mid-morning).

---

## §3 — KEY PATHS / FACTS

- **Manual follow-up push:** CMD → `cd "C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker"`
  → `python push_followups_today.py --push`. No flag = preview.
- **Call-hook:** `call_hook_capture.py` as `call-hook.service`, gunicorn 127.0.0.1:8098; OLS
  `/mo-callhook` → 8098; raw logs `/root/wa/call-hook/call_hook_logs/YYYY-MM-DD.jsonl`; secret
  gate = `CALLHOOK_SECRET` in `/root/wa/.env` (now plain-alphanumeric, D144); panel Call
  webhook `?key=` must match it. Join key `client_ref_id`; connect = customer leg answered +
  talk ≥15s → `Call_Durations`.
- **Dashboard Apps Script files:** `WebApp`, `Callconsole`, `OutcomeLog`, `Dashboard.html`,
  plus config/MyOperator/Netting/Sheets/Main/Monitor/CallField/Probe/Diagnostics. Deploy rule:
  **edit existing deployment → New version** (never New deployment — that changes the URL).
- **Sheet:** Clinic Callback Tracker `1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0`;
  tabs used this session: `Followups_Today`, `Followups_Settled`, `Followup_Outcomes`,
  `Call_Durations`.

---

## §4 — SESSION-START CHECKS (unchanged)
1. `System_Health` tab — any open incidents?
2. `Diagnostics.gs` live yet? If yes, was the 7 AM check clean today?
3. Any fault codes / banners from staff since last session?
If any incident open → address before new build. Else read KB + runbook, confirm, ask which
backlog item to start.
