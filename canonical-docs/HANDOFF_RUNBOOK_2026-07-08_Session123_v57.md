# HANDOFF RUNBOOK — Session 123 (v57) — 2026-07-08

**Canonical set (FULLY CONSOLIDATED single files — no delta chains, S100 policy):**
- **KB `Clinic_Master_KB_SystemsRegister` v1.47** (consolidated, self-contained) — WINS on any conflict.
- **Umbrella Architecture v1.35** (consolidated, self-contained).
- **This Runbook v57** (self-contained; supersedes v56 / Session 122).

Prior: Session 122 v56.

> **Documentation policy (owner directive, S100, still in force):** canonical docs are built as
> **single fully-consolidated files, not delta chains.** KB v1.47, Umbrella v1.35, and this Runbook
> v57 are all single-file masters. Canonical docs live in the repo folder **`canonical-docs/`**.

---

## §0 — WHAT HAPPENED (Session 123)

**FULL EOS — the live Stage-3 script `call_verdict.py` was replaced; no other code touched.**
This session fixed the one thing standing between the Stage-3 AI judge and real use: the
claim-match join. It went from **0/15** to a proven **16/22 (73%)** on real data, and the owner
confirmed on the live sheet that the AI is judging correctly.

### The claim-match join — REDESIGNED (D150; the top S122 task, now DONE)
Root cause of the 0/15 (§122.4) confirmed: **staff file outcomes in MORNING BATCHES, hours after
the call**, so a claim's `When` is filing-time, not call-time — a ±45-min window could never catch
it. New join: match on the patient's **phone number** over a whole-day **forward window**
(`call_start − 10 min` … `call_start + 28 h`, which reaches the next-morning batch). Earliest-
unclaimed-in-window wins; two calls to one number pair in **call-time order**; every row is stamped
**Match Confidence** = `unique` / `ordered` / `none`.

### The `Call_Verdicts` row — ENRICHED (D152) + JUDGE-ONCE-FILL-LATER (D151)
Added: full **Patient Number**, a **Recording Link** (joined from the Stage-1 `Call_Recordings` tab
by Join Key), **Match Confidence**, and a **name/Clinic-ID fallback** by number for unmatched calls.
The AI now judges each call **once**; when the staff claim lands later, the row's claim/verdict cells
are **updated in place** (no second AI call), and the doctor's own columns are never touched. Re-runs
are idempotent (a 2nd 06-Jul run = `0 judged, 0 failed, 0 claim-updated`, ₹0). A **header fail-safe**
refuses to append onto an out-of-date tab layout.

### Proven on real data (D153)
06-Jul full re-run — **62 judged, 0 failed.** Of 22 outgoing calls with a filed claim:
**16 Match / 5 Mismatch / 1 Unclear** (73%). 40 incoming calls = "No claim logged", which is
**correct**: staff never file outcomes for incoming calls (zero `Source=incoming` rows in
`Followup_Outcomes`, ever). Three safety flags surfaced (surgery; complaint+clinical+conduct;
clinical). The 5 mismatches + 3 flags are sitting in the sheet for calibration review.

### Install facts
`call_verdict.py` full-file replacement — md5 **`8c8ae1656056d8d1b2dec1b4776fe5c9`**, 1037 lines,
selftest **33/33** (was 24). Backup `call_verdict_BACKUP_S123_pre_join_redesign.py` at
`/root/wa/recordings-archive/`. Old 15-row `Call_Verdicts` tab deleted; recreated with the new
layout. **No systemd timer yet** (carried). Prompt / vocabularies / flags / blind-judge unchanged
from D149.

---

## §1 — STATE / MENTAL MODELS

**Track 2 live systems:**
- **`call_verdict.py` (Stage-3 AI judge) — join REDESIGN LIVE + PROVEN.** md5
  `8c8ae1656056d8d1b2dec1b4776fe5c9`. Run on demand (no timer). `Call_Verdicts` tab in the
  doctor-only sheet now carries the new enriched layout (recreated fresh; 62 real 06-Jul rows).
- **Drive OAuth token: FRESH + PERMANENT** (app In production since S122). Stages 1 + 2 + 3 all use
  `/root/wa/recordings-archive/drive_token.json`. Session-start check #4 passed this session
  (last night's transcripts present in Drive).
- Stage 1 (recording archive, 02:00) + Stage 2 (transcription, 03:00) LIVE + healthy.
- Duration gate / dashboard / `OutcomeLog.gs` at the D143 build; URL stable.
- WABA sends still BLOCKED vendor-side (D120); `wa_approve` still nohup (not systemd); watchdog /
  health report / attendance / follow-up push live; key rotations still overdue.

**Track 1 / PC-local:** `processor.py` at the D148 build (md5 `171a090645da130a4f4cbb0c0b102f22`);
Vitals & Plan front-end Step 5 complete; Step 7 not started; Hindi spelling task open.

**Mental models (reinforced this session):**
- **A claim's timestamp is FILING-time, not call-time.** The whole redesign rests on this. Never
  re-introduce a tight clock window around the call — staff batch-file hours (or a morning) later.
- **Incoming calls have no staff claim by workflow.** "No claim logged" on an incoming call is the
  correct, expected result — not a bug and not a gap. Match rate is measured on outgoing-with-claim.
- **Judge once, re-match cheaply.** The costly step (AI) runs once per call; claim-filling later is a
  free cell update. This is what makes a through-the-day cadence affordable.
- **The blind-judge rule is still load-bearing.** The AI sees transcript + direction + duration only
  — never the claim or any identifier. The enriched row (full number etc.) is written to the
  doctor-only OUTPUT; it does NOT reach the AI. Do not "help" the judge by sending the claim.
- **Answer vocabulary must mirror the LIVE dashboard.** Unchanged rule: if a dashboard dropdown
  changes, `VOCAB_*` in `call_verdict.py` must change too.
- **Same-day is a CADENCE change, not a code change now.** The code already supports write-on-
  transcription + fill-claim-later. What's missing is running Stages 1→2→3 through the day (the
  nightly run is retained as the safety net). Right now it is still nightly, so verdicts are ~a day
  stale until the timer/cadence work is done.

---

## §2 — BACKLOG (what to pick up next)

### STAGE-3 FOLLOW-THROUGH (the live thread — recommended order)
1. **Verdict Analysis Layer (D154) — TOP TASK, owner-requested this session.** A daily-updated,
   read-only Google Sheet, easy to read, **one patient per screen vertically** (horizontal
   `Call_Verdicts` scrolling is cumbersome), **segregated by scenario**: (1) Mismatches (staff vs AI)
   — training material; (2) AI-logged-but-staff-didn't; (3) Unclear — analyse *why*; (4) Matches —
   collapsed/summarised. Must stay trustworthy (built on the proven `Call_Verdicts` data; one-writer-
   per-table preserved). **Design first, then build.**
2. **Calibration review (owner task, ~10 min, no build)** — open `Call_Verdicts`, referee the 5
   mismatches + 3 flagged rows, fill the `Final Outcome` column. This seeds the staff-training record.
3. **Systemd timer** for `call_verdict.py` (~03:30 IST, after Stage 2's 03:00) — makes verdicts
   appear each morning without a manual run. (Later: through-the-day cadence for true same-day.)
4. **Item 4 — live staff-activity summary on the doctor dashboard** — its "audited" half consumes
   `Call_Verdicts`, so it follows a working Stage 3 and the analysis layer.
5. **Cost check / batch mode** — if per-call cost matters, switch to the overnight batch API
   (contained change; `AI_JUDGE_MODEL` isolation already in place).

### FAST FOLLOW-UP (carried from Item 3, owner choice "b")
- **Hard-to-Reach recording + transcript links** on the HTR tab (Drive + tracker sheet, keyed on
  `Patient_UID`). Verify the transcript-metadata join first. Small. (Note: the recording-link join by
  Join Key is now proven in `call_verdict.py` — reuse that pattern.)

### Track 1 backlog (unchanged)
- Hindi SPELLING corrections in `vitals_page.html` LIB strings · Step 7 new-patient reconciliation ·
  Living Clinic Data Map (§66.6).

### Track 2 live backlog (unchanged)
🔴 WABA authorizer/Lokesh + re-fire TEST · make `wa_approve` a systemd service · rotate
`WA_APPROVE_KEY` · 🔴 service-account key rotation (Lokesh) · AKEY_14 · **arm the timer-freshness
checker** · maintenance jobs · `clinic_health_report.py` UTC→IST fix · courtesy-rotate
`CALLHOOK_SECRET` + `FU_UPLOAD_SECRET` (D145).

### Documentation backlog (housekeeping)
- **DONE this EOS:** canonical set updated (KB v1.47 · Umbrella v1.35 · Runbook v57) + the new
  `call_verdict.py` committed to GitHub via the provided git kit (canonical docs → `canonical-docs/`,
  script → `recordings-archive/`).

---

## §3 — KEY PATHS / FACTS (Stage-3 additions in **bold**)

- **Stage-3 judge:** **`/root/wa/recordings-archive/call_verdict.py`** (md5
  **`8c8ae1656056d8d1b2dec1b4776fe5c9`**, 1037 lines). Backup
  **`call_verdict_BACKUP_S123_pre_join_redesign.py`** (pre-redesign, md5
  `bb17720d4857e3c040e8c89e7cc2e095`). Modes: `--selftest` (offline, 33/33), `--dry-run` (judges,
  writes nothing), real (`--date YYYY-MM-DD [--limit N]`). VPS python `/root/wa/venv/bin/python3`.
- **Redesigned join constants (in the script):** `CLAIM_SKEW_BEFORE_S = 600` (10 min),
  `CLAIM_MAX_FORWARD_S = 100800` (28 h). Match on phone number; confidence `unique`/`ordered`/`none`.
- **`Call_Verdicts` new columns:** Patient Number (full) · Match Confidence · Recording Link —
  in addition to the S122 set. Recording Link joins the Stage-1 **`Call_Recordings`** tab by
  **Join Key** (`Drive File ID` → `https://drive.google.com/file/d/<id>/view`).
- **Judge-once-fill-later:** existing rows are matched by Join Key; a landed claim updates only the
  claim/verdict/confidence/identity cells via `update_cells`; doctor columns untouched. Idempotent.
- **Stage-3 env (in `/root/wa/.env`):** **`ANTHROPIC_API_KEY`**, `GOOGLE_SA_KEY`,
  `DRIVE_TOKEN_FILE=/root/wa/recordings-archive/drive_token.json`; optional `TRACKER_SHEET_ID`,
  `AUDIT_SHEET_ID`, `AI_JUDGE_MODEL` (default `claude-haiku-4-5`).
- **Reads:** `Call_Transcripts` + `Followup_Outcomes` + **`Call_Recordings`** → **Clinic Callback
  Tracker** `1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0`. **Writes:** `Call_Verdicts` →
  **doctor-only Call Audit sheet** `1rq9VvB5L94EmmZbiUwase9HBLsJ3htispYLd1rHjSRQ` (single writer).
- **Answer vocabularies (live dashboard):** outgoing `FU_OUTCOMES` = coming · out_of_town ·
  on_medication · cant_communicate · dikha_chuke · problem · close_followup · not_interested ·
  treatment_elsewhere · wrong_number · asked_not_to_call. Incoming = resolved_on_call ·
  appointment_booked · info_given_will_act · needs_callback · escalated · cant_communicate ·
  will_come · enquiry_only · no_action. Plus `UNCLEAR`.
- **`Followup_Outcomes`:** `When` = `yyyy-MM-dd HH:mm` (IST); `Mobile` = last-10; `Source` blank on
  outgoing follow-ups, `Incoming` on incoming (which staff do NOT log outcomes for). Written only by
  `WebApp.gs`.
- Stage 1/2 unchanged: `Call_Recordings` / `Call_Transcripts` tabs; transcripts as `.txt` in the
  restricted Drive "Call Transcripts" folder (`14W26mbdT97FTrXexGoQadO5KnQQGOg_k`).
- Follow-up tracker (PC): `processor.py` md5 `171a090645da130a4f4cbb0c0b102f22`; backup
  `processor_BACKUP_S115_pre_Item3.py`. Dashboard deploy rule: edit existing deployment → New version.

---

## §4 — SESSION-START CHECKS (unchanged)
1. `System_Health` tab — any open incidents?
2. Call-hook healthy? (stuck "Checking…" tiles; today's `YYYY-MM-DD.jsonl` raw-log present?)
3. Any fault codes / banners from staff since last session?
4. Is `drive_token.json` still valid? (Stage 1/2/3 all depend on it. Quick tell: did last night's
   transcripts appear in the Drive "Call Transcripts" folder? If not, suspect the token.)
If any incident open → address before new build. Else read KB + runbook, confirm, and pick up the
**Verdict Analysis Layer (§2 item 1, D154)** as the default next task.

---

## §5 — START-HERE PROMPT — Session 124 (paste at next session's start)

Hi Claude. Continuing my clinic-automation project (**Session 124 — use the next number**).
I'm Dr. Manoj Agarwal, Dr. Manoj Agarwal Clinic, orthopaedic surgeon, Bareilly. Solo practice,
older Hindi-first semi-urban patients.

**Working protocol (follow strictly):** plain language, no assumed coding knowledge · ONE step at a
time, wait for my explicit confirmation · full-file replacements only, never diffs · ALL-CAPS from
me = urgent · mask all secrets/tokens · nothing live rebuilt without my OK, manual workflow always
stays fallback · build/test offline → py_compile (I use `python`) → then I install · VPS python
`/root/wa/venv/bin/python3`. Ending a session: **EOS** (code changed) or **EOS-light** (docs only).

**Canonical docs are in THIS PROJECT'S KNOWLEDGE (single consolidated files):**
KB `Clinic_Master_KB_SystemsRegister` **v1.47** — WINS on any conflict · **HANDOFF_RUNBOOK Session
123 v57** (§0 what happened, §2 backlog) · **Umbrella Architecture v1.35** · API_QUICK_REFERENCE_CARD
· Call_Console_Evolution_Spec · Diagnostics_Surveillance_Spec · Maintenance_SOP_Spec (latest each).
Code lives in GitHub (`drmanoj-clinic-automation`; canonical docs in `canonical-docs/`). Patient
data is NOT in this project.

**WHERE WE STOPPED (Session 123, FULL EOS — Stage-3 join redesign LIVE + PROVEN):** `call_verdict.py`
redesigned and installed (md5 `8c8ae1656056d8d1b2dec1b4776fe5c9`, selftest 33/33). The claim-match
join now matches on phone number over a whole-day forward window (fixed the batch-filing 0/15 →
16/22 = 73% on 06-Jul). Row enriched (full number, recording link, match confidence, name/Clinic-ID
fallback); judge-once-fill-later upsert; re-runs idempotent. 40 incoming calls correctly "No claim
logged" (staff don't log incoming). Owner confirmed the AI judges correctly. Backup
`call_verdict_BACKUP_S123_pre_join_redesign.py`. No timer yet.

**START HERE — Session 124 = the Verdict Analysis Layer (top task, D154):** a daily-updated,
read-only Google Sheet, easy to read, ONE PATIENT PER SCREEN VERTICALLY (horizontal `Call_Verdicts`
scrolling is cumbersome), segregated by scenario — (1) Mismatches (staff vs AI), (2) AI-logged-but-
staff-didn't, (3) Unclear (analyse why), (4) Matches (collapsed). Must stay trustworthy, built on the
proven verdict data, one-writer-per-table preserved. **Design it first, then build.** OR pick another
Stage-3 follow-through: calibration review · systemd timer (~03:30 IST) · Item 4 (live staff-activity
summary).

**Session-start checks:** System_Health open incidents? · call-hook healthy (stuck "Checking…" tiles /
today's raw-log present)? · staff banners? · did last night's transcripts appear in the Drive "Call
Transcripts" folder? (if NOT, suspect the shared Drive token — Stages 1/2/3 share it).

**Connected sources:** Google Drive (drmka.ortho@gmail.com) · Gmail · Notion (Clinic HQ) · GitHub
(drmanoj-clinic-automation) · ClickUp parked (D17, do not use). Read the KB + runbook, confirm, then
tell me which item you recommend and start.
