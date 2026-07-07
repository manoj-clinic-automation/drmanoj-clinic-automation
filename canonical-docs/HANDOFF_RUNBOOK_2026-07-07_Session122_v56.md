# HANDOFF RUNBOOK — Session 122 (v56) — 2026-07-07

**Canonical set (FULLY CONSOLIDATED single files — no delta chains, S100 policy):**
- **KB `Clinic_Master_KB_SystemsRegister` v1.46** (consolidated, self-contained) — WINS on any conflict.
- **Umbrella Architecture v1.34** (consolidated, self-contained).
- **This Runbook v56** (self-contained; supersedes v55 / Session 121).

Prior: Session 121 v55.

> **Documentation policy (owner directive, S100, still in force):** canonical docs are built as
> **single fully-consolidated files, not delta chains.** KB v1.46, Umbrella v1.34, and this Runbook
> v56 are all single-file masters.

---

## §0 — WHAT HAPPENED (Session 122)

This session built **agenda Item 5 — the Stage-3 AI judge** — and, in the middle of proving it,
uncovered and fixed a **live Drive-OAuth-token incident**. **FULL EOS — a new live VPS script was
installed and the nightly-pipeline auth was repaired.** No existing code file was modified.

### Stage-3 AI judge — DESIGNED, BUILT, INSTALLED, PROVEN (D149; parent D62)
`call_verdict.py`, sibling to Stage 2 at `/root/wa/recordings-archive/`. It reads `Call_Transcripts`,
downloads each transcript from the restricted Drive folder, sends **transcript + direction +
duration ONLY** to Claude Haiku (blind judge — never the staff claim or any patient/agent
identifier), parses a strict JSON verdict (outcome in the LIVE dashboard vocabulary + six safety
flags + an evidence excerpt), then in Python fuzzy-matches the staff's claim from
`Followup_Outcomes` and computes Match / Mismatch / Partial / Unclear / No-claim. Each result is one
row in a NEW `Call_Verdicts` tab it creates in the **doctor-only** Call Audit sheet — with blank
`Doctor Flag · Doctor Note · Final Outcome` columns reserved for the doctor.
- **Verified:** `py_compile` clean; **selftest 24/24 PASS** (sandbox + VPS); md5
  **`bb17720d4857e3c040e8c89e7cc2e095`**; 781 lines. First real run: **15 judged / 0 failed**.
- **Not yet done:** no systemd timer (deliberate — run on demand until calibration review is done);
  the claim-match redesign (see below); staff silent-flag + doctor-console surfacing (Item 4).

### 🔴 INCIDENT — Drive OAuth token expired, fixed permanently + immediately
The dry-run hit `invalid_grant: Token has been expired or revoked`. Root cause: the OAuth app was
in **Testing** publishing status → Google expires those refresh tokens after **exactly 7 days**
(minted ~30-Jun → died 07-Jul). This token is shared by **Stage 1 (02:00 IST)** and **Stage 2
(03:00 IST)**; a dead token would have failed tonight's runs, and Stage-1's MyOperator links expire
in ~24 h → risk of permanent recording loss. **Drive evidence confirmed last night's 03:05 IST run
succeeded — nothing was lost.** Fix: **(1) permanent** — published the app **Testing → In
production** (tokens no longer expire every 7 days); **(2) immediate** — re-minted `drive_token.json`
on the PC (`get_drive_token.py`, manual address-bar flow), uploaded to
`/root/wa/recordings-archive/drive_token.json` (726 bytes, 22:40 IST). Post-fix dry-run: 3/0.

### FINDING — the ±45-min claim-match is too weak (Item 5 part 2, NEXT)
The 15 real verdicts were sensible but ALL showed `claim=(none)`. Root-caused (read-only): **not** a
timestamp bug — staff file outcomes in **batches** (e.g. ~10:00 clearing send-backs) while calls are
in the **3–7 PM** window, so claims rarely fall inside the matcher's ±45-min window. "No claim
logged" is the SAFE result (never a false Mismatch), but the join can't surface real
Match/Mismatch as-is. **The AI half works; the claim-matching half needs redesign.**

---

## §1 — STATE / MENTAL MODELS

**Track 2 live systems:**
- **NEW: `call_verdict.py` (Stage-3 AI judge) INSTALLED + LIVE-CAPABLE**, run on demand (no timer).
  md5 `bb17720d4857e3c040e8c89e7cc2e095`. `Call_Verdicts` tab now exists in the doctor-only sheet
  (header + 15 real rows from 06-Jul).
- **Drive OAuth token: FRESH + PERMANENT.** App is **In production**; token re-minted 07-Jul 22:40
  (726 bytes). Stages 1 + 2 + 3 all use `/root/wa/recordings-archive/drive_token.json`.
- Stage 1 (recording archive, 02:00) + Stage 2 (transcription, 03:00) LIVE + healthy (token fixed).
- Duration gate / dashboard / `OutcomeLog.gs` at the D143 build; URL stable.
- WABA sends still BLOCKED vendor-side (D120); `wa_approve` still nohup (not systemd); watchman /
  health report / attendance / follow-up push live; key rotations still overdue.

**Track 1 / PC-local:** `processor.py` at the D148 build (md5 `171a090645da130a4f4cbb0c0b102f22`);
Vitals & Plan front-end Step 5 complete; Step 7 not started; Hindi spelling task open.

**Mental models (reinforced this session):**
- **The AI judge works; the claim-join is the weak half.** The S24 warning ("fuzzy, not a clean
  key") came true on real data. Redesign the join before trusting Match/Mismatch.
- **The blind-judge rule is load-bearing.** The AI never sees the staff claim or any identifier —
  that's both the anti-anchoring mechanism (D62) and the privacy mechanism. Do not "help" it by
  sending the claim.
- **Answer vocabulary must mirror the LIVE dashboard.** Match/Mismatch only works because the judge
  answers in the staff's own codes. If a dashboard dropdown changes, `VOCAB_*` in `call_verdict.py`
  must change too.
- **OAuth "Testing" status = a 7-day time bomb.** Any owner-OAuth token minted under Testing dies in
  7 days. The app is now In production, so this specific bomb is defused — but it's the reason the
  timer-freshness checker should finally be armed.
- **Three stages, one token.** Stages 1/2/3 all depend on `drive_token.json`. If it dies, all three
  die together — and Stage 1's loss is permanent (24-h MyOperator links). Highest-consequence
  single point of failure in the recordings pipeline.
- **`--dry-run` still creates the tab header.** Tab creation (needed for the already-judged check)
  happens even in dry-run; only DATA rows are withheld. Harmless, but know it.

---

## §2 — BACKLOG (what to pick up next)

### THE SIX-ITEM AGENDA (owner-set S94) — updated standing
- **Items 0,1,2,3 — DONE.** **Item 5 (AI judge) — v1 BUILT + PROVEN (S122, D149)**, but see the
  claim-join redesign below before it's trustworthy end-to-end.

### STAGE-3 FOLLOW-THROUGH (the live thread — do these next, in order)
1. **Redesign the claim-match join (§122.4)** — the ±45-min window is too weak for batch filing.
   Options: (1) whole-day nearest-claim on mobile; (2) stronger join on mobile + `Agent Ext` +
   same-day. Then re-run a recent day and referee real Match/Mismatch. **This is the top next task.**
2. **Calibration review** — with a working join, run a full recent day, open `Call_Verdicts`, and
   referee: is the AI outcome right? are the flags right? Fill the `Doctor Final` column. Measure how
   often undiarised transcripts caused UNCLEAR (this decides whether Stage-2 diarisation is worth it).
3. **Systemd timer** for `call_verdict.py` (~03:30 IST, after Stage 2's 03:00) — ONLY after
   calibration is satisfactory.
4. **Item 4 — live staff-activity summary on the doctor dashboard** — its "audited" half consumes
   `Call_Verdicts`, so it naturally follows a working Stage 3.
5. **Cost check / batch mode** — if per-call cost (~₹400–700/mo) matters, switch to the overnight
   batch API (contained change; `AI_JUDGE_MODEL` isolation already in place).

### FAST FOLLOW-UP (carried from Item 3, owner choice "b")
- **Hard-to-Reach recording + transcript links** on the HTR tab (Drive + tracker sheet, keyed on
  `Patient_UID`). Verify the transcript-metadata join first. Small.

### Track 1 backlog (unchanged)
- Hindi SPELLING corrections in `vitals_page.html` LIB strings · Step 7 new-patient reconciliation ·
  Living Clinic Data Map (§66.6).

### Track 2 live backlog (unchanged)
🔴 WABA authorizer/Lokesh + re-fire TEST · make `wa_approve` a systemd service · rotate
`WA_APPROVE_KEY` · 🔴 service-account key rotation (Lokesh) · AKEY_14 · **arm the timer-freshness
checker (now doubly justified — it would have caught the token death)** · maintenance jobs ·
`clinic_health_report.py` UTC→IST fix · courtesy-rotate `CALLHOOK_SECRET` + `FU_UPLOAD_SECRET` (D145).

### Documentation backlog (housekeeping)
- **Commit the current canonical set + `call_verdict.py` to GitHub** — commit message + zip provided
  in this EOS. Repo `docs/` + `recordings-archive/` need the S122 additions.

---

## §3 — KEY PATHS / FACTS (Stage-3 additions in **bold**)

- **Stage-3 judge:** **`/root/wa/recordings-archive/call_verdict.py`** (md5
  `bb17720d4857e3c040e8c89e7cc2e095`). Modes: `--selftest` (offline), `--dry-run` (judges, writes
  nothing), real (`--date YYYY-MM-DD [--limit N]`). VPS python `/root/wa/venv/bin/python3`.
- **Stage-3 env (in `/root/wa/.env`):** **`ANTHROPIC_API_KEY`** (line 31), `GOOGLE_SA_KEY`,
  `DRIVE_TOKEN_FILE=/root/wa/recordings-archive/drive_token.json`; optional `TRACKER_SHEET_ID`,
  `AUDIT_SHEET_ID`, `AI_JUDGE_MODEL` (default `claude-haiku-4-5`).
- **Drive OAuth app:** Google Cloud project (drmka.ortho@gmail.com), OAuth consent screen now
  **Publishing status: In production** (was Testing). Token minted via `get_drive_token.py` on the
  PC folder `D:\Oouth config\` (holds `get_drive_token.py` + `client_secret.json`).
- **Reads:** `Call_Transcripts` + `Followup_Outcomes` → **Clinic Callback Tracker**
  `1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0`. **Writes:** `Call_Verdicts` → **doctor-only Call
  Audit sheet** `1rq9VvB5L94EmmZbiUwase9HBLsJ3htispYLd1rHjSRQ` (single-writer = this script).
- **Answer vocabularies (live dashboard):** outgoing `FU_OUTCOMES` = coming · out_of_town ·
  on_medication · cant_communicate · dikha_chuke · problem · close_followup · not_interested ·
  treatment_elsewhere · wrong_number · asked_not_to_call. Incoming = resolved_on_call ·
  appointment_booked · info_given_will_act · needs_callback · escalated · cant_communicate ·
  will_come · enquiry_only · no_action. Plus `UNCLEAR`.
- **`Followup_Outcomes` `When` format** = `yyyy-MM-dd HH:mm` (IST wall time); `Mobile` = last-10
  digits. Written only by `WebApp.gs`.
- Stage 1/2 unchanged: `Call_Recordings` / `Call_Transcripts` tabs; transcripts as `.txt` in the
  restricted Drive "Call Transcripts" folder (`14W26mbdT97FTrXexGoQadO5KnQQGOg_k`).
- Follow-up tracker (PC): `processor.py` md5 `171a090645da130a4f4cbb0c0b102f22`; backup
  `processor_BACKUP_S115_pre_Item3.py`. Dashboard deploy rule: edit existing deployment → New version.

---

## §4 — SESSION-START CHECKS (unchanged)
1. `System_Health` tab — any open incidents?
2. Call-hook healthy? (stuck "Checking…" tiles; today's `YYYY-MM-DD.jsonl` raw-log present?)
3. Any fault codes / banners from staff since last session?
4. **NEW: is `drive_token.json` still valid?** (Stage 1/2/3 all depend on it. A quick tell: did last
   night's transcripts appear in the Drive "Call Transcripts" folder? If not, suspect the token.)
If any incident open → address before new build. Else read KB + runbook, confirm, and pick up the
**Stage-3 claim-match redesign (§2 item 1)** as the default next task.
