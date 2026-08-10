# D297 — CALL INTELLIGENCE CONSOLE (log · staff · referee · digest · leads · no-show · revenue) — SIGNED CONTRACT v4 (FINAL · BUILD-READY)

*Session 166 · 2026-08-10 · **D297 MINTED** (design vetted end-to-end this session; build begins S167). Supersedes v1/v2/v3. This single document carries the contract **and** every live-verified fact needed to build without re-probing (Appendix A). Nothing here is from memory — all schemas/IDs/joins were confirmed by live probe or live code this session (D160/D188).*

> **One-line intent.** Retire the GAS Callback-Tracker dashboard and rehome its proven intelligence in the VPS portal — the doctor's single evolving point — as a call log + staff-performance + referee + digest + lead-conversion + no-show + revenue console, reading the two live Sheets and the follow-up tracker's pushed outputs.

---

## §0 — SCOPE MAP (every owner directive, S166 → where it lands)

| Directive | Track |
|---|---|
| every call: incoming answered · missed · net-missed · outbound callbacks, date/time | C (spine = `Call_Durations`) |
| staff outcome not filed → highlight, never blank | C (amber NOT FILED) |
| net-missed two-way (either side, repeatable), grouped attempts | C (conversation threads) |
| call/transcript/judge times tracked (data-mining) | C (latency view) |
| AI verdict grades call quality (opening/closing/info asked+given) + digressions | J (judge rubric) |
| referee here; retire old AppScript system + its Sheet; retire `verdict_review.py`; I am sole referee | R |
| migrate daily digest to VPS, reachable via portal | G |
| transcript caught VPS-side (Sarvam → VPS → cache) | T |
| row search → cascading filter flow | C |
| recordings at VPS, 1–2 months, no lag; console.db export to Drive; no new Drive deletions | K + R-export |
| pull MyOperator missed calls, reconcile our calls | C-reconcile (port GAS) |
| staff-compliance checks baked in GAS — reuse | C-staff (port GAS) |
| unknown callers = new first-time inquiries = highest value | C (New-Leads view) |
| mark marketing/spam; block-list for MyOperator panel | M |
| send-back-to-staff (call again) + free-text reason | C-write (port GAS) |
| track new-caller conversion (unknown today → patient tomorrow) | L |
| track no-show callbacks (booked, not in day report → next day) | N |
| **daily revenue report in portal** | **V (NEW, in scope)** |

---

## §1 — ARCHITECTURE (hubbed on the portal)

```
BUILDER  portal_console.py (VPS /root/wa/, read-only over sheets + drive)
  → SQLite /root/wa/console.db  (sole writer; incremental; watermark on ended_at_ist)
  → local rec cache /root/wa/rec_cache/  (60d / 1 GB, oldest-pruned)
  → nightly export console.db → Drive  (durable backup)
PORTAL (doctor-gated)
  /portal/console          call log · staff summary · cascading filters · CSV · New-Leads · No-shows · Revenue
  /portal/console/referee  worst-first cards · one-tap disposition   (writes dispositions → console.db + Drive)
  /portal/console/action   send-back(reason) · mark-marketing        (console writes)
  /portal/digest           11:00 pulse + 21:30 digest, live
  /portal/rec/<join_key>   recording proxy (local-first, Drive fallback, in-page player)
  /portal/console-data     JSON → gist metric 5
```
Cron `*/10 9–21 IST`, incremental. Fail-loud (D236): stale/missing db is *said*, never faked. New metrics = new keys/tables in `console.db`; no portal rework (D246/D296). One writer per store (D235); the only portal writes are dispositions + send-back + marketing marks, each to its own `console.db` table (+ mirrored where a legacy tab still needs it during cutover).

---

## §2 — SPINE
`Call_Durations` = one row/call, both directions, missed included; `status=='probe'` excluded. Direction ← `category` (incoming→In, obd→Out). Answered/missed ← provider `status`+`customer_result` (never talk-seconds — D244/F-44). Bridge to verdict chain: `recording_filename → Call_Recordings.MyOperator Filename → Join Key`. **Missed-call completeness (owner):** our webhook can under-capture missed calls, so the builder reconciles against MyOperator's missed log (port `MyOperator.gs`/`Netting.gs` + `flag_investigator.py` /search) within the pull lag.

## §3 — COLUMNS (no masking — full number, doctor-gated)
Date/Time/Direction/Duration ← `Call_Durations` · Number ← `phone10` (fallback filename→`Call_Recordings`) · Patient Name ← `Call_Verdicts`/`Patient_Master` · **Diagnosis** ← `Patient_Master` via phone10 (F-70; mirrored nightly by `push_patient_mirror.py`) · Staff outcome ← `Call_Verdicts.Claimed Outcome` (blank → **NOT FILED**, amber) · AI verdict + quality grades ← `Call_Verdicts` · Recording ← proxy (local-first) · Transcript ← `console.db` cache · Referee state ← `console.db` · Staff who handled ← Out:`Outbound_Log.Agent` / In:`Call_Verdicts.Agent` (names via `Agents`).

## §4 — CONVERSATION THREADS & TWO-WAY NET-MISSED
Group calls by `phone10` into a conversation across both directions/time; each attempt expandable (direction·date·time·**agent**·status·duration·its verdict/recording/transcript). Net-missed is a **conversation** property: RESOLVED if any leg connected (either side may start/repeat); NET-MISSED (OPEN) if none has. Day headers reconcile to `Daily_Summary`. Primary action view = net-missed-open, newest first, attempt count + last staff.

## §5 — LATENCY DATA-MINING
Per call: `t_call`(`captured_at_ist`) · `t_transcript`(`Transcribed At`) · `t_judge`(`Judged At`); lags transcript−call, judge−transcript, judge−call. Pipeline-latency view (median/p90/max + backlog aging + trend) — the early-warning instrument for a silently stalling stage (F-69 lesson).

## §6 — TRACK J: JUDGE GRADES QUALITY + DIGRESSION
`call_verdict.py` prompt gains the rubric (Axis-3 CONDUCT operable — closes D166/D199). New `Call_Verdicts` cols `Q_Opening`,`Q_Info_Asked`,`Q_Info_Given`,`Q_Closing`,`Q_Digression`,`Q_Note`. Judge proposes, doctor confirms (D191). Digression=POOR + weak open/close surface on the agent row + a conduct-watch filter. **Rubric is out as `D297_Call_Quality_Rubric_for_review.docx` — Track J waits on the owner's red-pen; no other track does.**

## §7 — STAFF-PERFORMANCE SUMMARY (Agent × day + range)
Calls handled (In answered + Out attempts) · outcomes filed vs handled (+ NOT-FILED count) · verdict TRUE/FALSE/UNCLEAR · quality good-rate + digression-POOR count · flags raised · net-missed-open on watch. **Port the existing GAS compliance metrics** (`OutcomeLog.gs`/`CallConsole.gs`/`Netting.gs`). Click a staff row → filter the log to that agent.

## §8 — TRACK T: TRANSCRIPT CAUGHT VPS-SIDE
`call_transcription.py` writes Sarvam text into `console.db` (Join Key) at transcription time — no Drive re-pull, instant expand, survives link expiry. Builder back-pulls existing transcripts once (drive token) to seed the window.

## §9 — SEARCH AS CASCADING FILTER
Narrowing flow: Direction → Agent → Answered/Missed/Net-missed → Flag/Quality → Date-range, each facet showing live counts; free-text (name/number/diagnosis) is the final refiner. Every filtered view CSV-exportable (doctor-side, full data).

## §10 — TRACK R: REFEREE IN CONSOLE, FULL RETIREMENT (sole referee = owner)
Console owns the whole referee flow. **Ordering ported** (verdict_review.py red/green/blue bands + `sort_key`). Referee cards worst-first with recording/transcript/verdict inline; one-tap **Agree / Override→Final Outcome / Note** → a `dispositions` row in `console.db` (Join Key · Final Outcome · Note · **Refereed By = manoj** · Refereed-At) → derived **gap** + **self-review flag** (⚠ if the call's `Agent` == ext-10). **Durability:** nightly `console.db` → Drive export (owner-confirmed). **Retired at cutover** (one writer, F-3/D235): AppScript referee UI + its `Doctor_Verdicts`/`Verdict_Review` Sheet dependency + `verdict_review.py`. **Dependency handled:** `daily_digest.py` (the only other reader of `Verdict_Review`) is migrated to Track G (`console.db`) — that is what frees `verdict_review.py` to retire. Cutover order: (a) console referee-write live + idempotent (write twice→one row); (b) digest repointed; (c) disable AppScript referee write; (d) stop `verdict_review.py` cron.

## §11 — TRACK G: DIGEST → PORTAL
`/portal/digest` renders the 11:00 pulse + 21:30 digest live from `console.db`. `daily_digest.py` repointed off `Verdict_Review` onto `console.db`. Email push stays optional (D236 lineage); portal is the always-current view.

## §12 — TRACK K: VPS RECORDING CACHE
Builder pulls recent recordings Drive→`/root/wa/rec_cache/`; proxy serves local-first, Drive-fetch fallback for older. Cap 60 days OR 1 GB (measured ~0.30 GB for 60d — ~1% of free disk), oldest-pruned. **Drive never deleted** (owner).

## §12a — TRACK M: MARKETING/SPAM
A console mark (marketing/spam) on a call/number → a `console.db` flag + a **block-list view** (numbers to lock at the MyOperator panel — the block itself stays a panel action) + optional `Do_Not_Call` row. Marked numbers drop out of the New-Leads and net-missed-open views.

## §12b — TRACK L: NEW-CALLER CONVERSION
Unknown incoming caller today (number not in `Patient_Master`) is a high-value first-time inquiry (D243). The builder records it; after the next nightly `push_patient_mirror.py`, if that number now appears in `Patient_Master`, it **converted**. Report: new-leads/day → converted → conversion rate, by day and (where attributable) by handling agent. Reads the tracker's pushed `Patient_Master` — no tracker migration needed.

## §12c — TRACK N: NO-SHOW CALLBACKS
The local tracker's `processor.py` already joins `visit_ledger` (seen, from the consultation/day report) vs `followup_ledger` (due) and pushes the worklist to **`Followups_Today`** (the calling list) + **`Followups_Settled`**. Track N surfaces the **booked-but-not-seen** subset (due, not settled/seen for the date) as a next-day callback list, and **closes the loop**: did we call back · when · which staff · outcome · did they then show. Reads the pushed tabs — loosely coupled. Exact no-show tag = a builder join (due−settled/visit) confirmed at Stage A against the live tabs.

## §12d — TRACK V: DAILY REVENUE IN PORTAL (NEW, in scope)
The daily revenue report lives in the **local follow-up tracker** (`revenue.py`/`revenue_ingest.py`, the `/finance` routes; `revenue_ledger.csv`) and is **not** currently pushed to the VPS. Track V = a lightweight **daily revenue push** from the tracker (a summary → a `Revenue_Daily` Sheet tab or a JSON to the VPS, mirroring `push_followups_today.py`'s pattern) → a **`/portal/console` Revenue view** (day/period totals, consult vs procedure vs lab, concessions, ▲/▼ vs the ₹600 standard consult). Full line-level revenue stays in the tracker until its own VPS migration; the portal shows the summary. **Owner-confirmed in scope (S166).** *Build note: needs a small tracker-side push script + a portal read; the tracker code is on the clinic PC (PHI — never in repo/kit).*

---

## §13 — BUILD SEQUENCE + GATES
- **A · Track C builder** → `console.db` (join · threads · net-missed · reasons · latency · transcript back-pull · missed-call reconcile). `--selftest` + **dry-run counts reconciled to the sheets** before ship.
- **B · Track C page** `/portal/console` (log · groups · staff summary · cascading filters · CSV · New-Leads · No-shows) + `/portal/rec` proxy + **Track K** cache. F-63 route-hits before install. Cron `*/10 9–21`.
- **C · Gist metric 5** from `console.db` — deferred card live, no portal rework.
- **G · Digest → portal**; **M · marketing marks**; **C-write · send-back(reason)** (port GAS).
- **R · Referee-in-console** + Drive export + one-writer cutover (retire AppScript referee + `verdict_review.py`).
- **L · conversion** + **N · no-show** (read tracker pushes) + **V · revenue** (tracker push → portal view).
- **T · transcript-at-VPS** hook; **J · judge rubric** (after red-pen; propose-only). 

## §14 — STANDS ON
D235 (one writer) · D236/D246/D296 (local-artefact seam, fail-loud) · D191/D199 (propose/dispose; rubric makes conduct operable) · D243 (unknown incoming = fresh lead) · D244/F-44 (provider status) · D160/D188 (live, hash-verified) · F-70 (diagnosis live). Parent of gist metric 5.

---
---

# APPENDIX A — VERIFIED GROUND TRUTH (S166 probes/code — build from this, re-verify md5 live)

**Sheets:**
- **Clinic Callback Tracker** `1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0` — holds `Call_Durations`, `Call_Recordings`, `Call_Transcripts`, `Followup_Outcomes`, `Patient_Master`, `Followups_Today`, `Followups_Settled`, `Callbacks_Today`, `K_Strikes`, `Daily_Summary`, `Do_Not_Call`, `Agents` … (19 tabs).
- **Call Audit (Doctor Only)** `1rq9VvB5L94EmmZbiUwase9HBLsJ3htispYLd1rHjSRQ` — holds `Call_Verdicts`, `Verdict_Review`, `Doctor_Verdicts`.

**Credential (reads BOTH sheets):** service-account JSON at env `GOOGLE_SA_KEY` (legacy alias `WA_SA_KEY`), resolved from the clinic `.env` (`/root/wa/recordings-archive/.env` or `/root/wa/.env`). Drive files (recordings/transcripts) via `DRIVE_TOKEN_FILE=/root/wa/recordings-archive/drive_token.json` (owner OAuth). VPS python `/root/wa/venv/bin/python3`.

**Master join key** `Join Key = {phone10}_{call_start_unix}` (regex `^(\d{10})_(\d{9,12})$`), in `Call_Recordings`, `Call_Transcripts`, `Call_Verdicts`, `Doctor_Verdicts`. `Call_Durations`→chain via `recording_filename → Call_Recordings.MyOperator Filename → Join Key`.

**Schemas (live headers, S166):**
- `Call_Durations` (14): `client_ref_id, ref_id, session_id, category(incoming|obd), status(bridged|missed|probe), total_duration, customer_result, customer_talk_duration, customer_ring_duration, recording_filename, ended_at_ist, captured_at_ist, source_event, phone10` — **1652 rows**. (phone10 can be blank on obd → use filename fallback.)
- `Call_Verdicts` (35): `Date, Time, Direction, Patient Number, Agent, Patient Name, Clinic ID, Duration, Claimed Outcome, AI Outcome, Verdict, Match Confidence, Outcome TRUE/FALSE, AI Reason, Evidence, Spoke With, Confidence, Flag PostOp, Flag Complaint, Flag Urgent, Flag Surgery, Flag Clinical, Flag Conduct, Conduct Note, Recording Link, Transcript Link, Join Key, Status, Error, Judged At, Prompt Ver, Model, Doctor Flag, Doctor Note, Final Outcome` — **2195 rows, current to today** (pipeline ALIVE).
- `Doctor_Verdicts` — has `Agent` + `Recorded At`, **NO reviewer-identity col** (→ Track R adds `Refereed By`). **19 rows, last 29 Jun** (referee loop cold — the reason for Track R).
- `Verdict_Review` — worst-first band; read by `daily_digest.py` (repoint at retirement).
- `Outbound_Log` (7): `Date, Time, Phone10, Agent(full name), Duration_s, Status, Start_Unix` — 165 rows (outbound staff attribution).
- `Agents` (4): `Ext, Name, UserId, Active` — 6 live (Manoj ext10, Shavez 11, Shivani 12, Manoj Bhati 13, Alisha 14, Darpan 15).
- `Daily_Summary` (6): `Date, Total Calls, Incoming, Net-Missed, Resolved, Net-Missed %` — authoritative daily net-missed.
- `Followup_Outcomes` — staff's `Claimed Outcome` source (`k_coming`/`k_not_coming`/`k_call_again`).
- `Patient_Master` (8): `Mobile, Patient Name, Diagnosis, Age, Gender, Last Visit, Patient UID, Clinic_Specific_Id` — mirrored nightly.
- Recording stats: avg **~217 KB**; last-7-day rate ~27 recorded/day; **60 days ≈ 0.30 GB**, full history ≈ 0.28 GB. VPS disk 99 G / 12 G used / 88 G free.

**Live probes used (re-run to re-verify):** `/tmp/d297_probe.py` (sheets/tabs/headers/counts), `/tmp/d297_probe2.py` (staff attribution), `/tmp/d297_recsize.py` (recording sizes). All read-only.

# APPENDIX B — PORT MAP (existing code → console feature; RE-VERIFY md5 live vs repo)

Repo `manoj-clinic-automation/drmanoj-clinic-automation` (branch main):
- **Pipeline** (`recordings-archive/`, `call-hook/`): `call_hook_capture.py`→`Call_Durations` · `call_recording_archive.py`→`Call_Recordings` · `call_transcription.py`→`Call_Transcripts` (**Track T hook here**) · `call_verdict.py`→`Call_Verdicts` (**Track J prompt here**) · `verdict_review.py`→`Verdict_Review`/`Doctor_Verdicts` (**RETIRE; port ordering `sort_key`+`C_SECTION_BAND` red/green/blue**) · `flag_investigator.py`→`flag_investigator_results.json`.
- **GAS dashboard** (`dashboard/` — RETIRE the referee UI): `Netting.gs` (net-missed rule), `MyOperator.gs` (`/search` missed-call pull → **C-reconcile**), `OutcomeLog.gs`+`WebApp.gs` (`sendBackToStaff`/`SENT_BACK` free-text reason → **C-write send-back**; unknown-caller/`non_patient`; compliance metrics → **C-staff**), `CallConsole.gs` (the existing GAS console being superseded), `CallField.gs` (the DEAD `Call_Feed` writer, F-69).
- **Local follow-up tracker** (clinic PC — **PHI, NEVER in repo/kit**): `app.py` (2150L Flask; `/run`, `/finance`, `/revenue/*`, `/calls`), `processor.py` (visit↔followup join, `reconcile_calls`, `find_called_in_and_due`, "DIKHA CHUKE→RESOLVE"), `revenue.py`/`revenue_ingest.py` (**Track V** daily revenue), `push_followups_today.py`→`Followups_Today`+`Followups_Settled` (calling list; reads `Do_Not_Call`, replace-only), `push_patient_mirror.py`→`Patient_Master` (**Track L** source), `converter/docterz_to_myoperator.py` (Docterz exports→campaign CSVs). Ledgers (local CSV): `visit_ledger`(seen), `followup_ledger`(due), `revenue_ledger`, `patient_master`, `call_log`, `outbound_log`.

# APPENDIX C — RUBRIC & SECURITY
- **Rubric** `D297_Call_Quality_Rubric_for_review.docx` — editable Word doc out to the owner (opening/info-asked/info-given/closing/digression + call-script capture). Track J blocks on its return; nothing else does.
- **F-71 (S166):** the uploaded `followup_tracker.zip` carried **PHI** (`patient_master.csv`, `patient_diagnosis.csv`), **revenue ledgers**, and **secrets** (`.secret_key`, `.env`) — kin F-56. Read **code-only**, **nothing committed anywhere**, no data printed. **Action:** treat that `.secret_key`/`.env` as potentially exposed → rotation check; future uploads code-only.

---

**STATUS: D297 signed & minted (S166). Build = Stage A next session, off this document. Live code unchanged this session.**
