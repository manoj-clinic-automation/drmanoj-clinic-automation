# HANDOFF RUNBOOK — Session 124 (v58) — 2026-07-08

**Canonical set (FULLY CONSOLIDATED single files — no delta chains, S100 policy):**
- **KB `Clinic_Master_KB_SystemsRegister` v1.48** (consolidated, self-contained) — WINS on any conflict.
- **Umbrella Architecture v1.36** (consolidated, self-contained).
- **This Runbook v58** (self-contained; supersedes v57 / Session 123).
- Specs changed this session: **Call_Console_Evolution_Spec v1.6**, **Diagnostics_Surveillance_Spec v1.6**.
- Unchanged this session: API_QUICK_REFERENCE_CARD, Maintenance_SOP_Spec.

Prior: Session 123 v57. Canonical docs live in the repo folder **`canonical-docs/`**.

---

## §0 — WHAT HAPPENED (Session 124)

**FULL EOS.** One new VPS script, one live dashboard file replaced, one live `.env` secret realigned.
Decisions **D155–D160**. The session opened as a build and became a live-fault repair that
permanently changed how the staff-facing gate behaves.

### 1. Verdict Analysis Layer — BUILT (D155)
`verdict_review.py`, new, at `/root/wa/recordings-archive/`. md5 **`af6622e4edc3f454cf0bfed128c4f76b`**,
1364 lines, selftest **117/117**, **₹0 — no AI calls**.

Reads `Call_Verdicts` (header-verified) + transcripts from Drive. Writes two new tabs it alone owns:

- **`Verdict_Review`** — rolling 7 days, redrawn each run. Six sections: FLAGGED (first, whatever else
  the row is) · MISMATCH · AI-LOGGED-STAFF-DIDN'T · UNCLEAR · SUSPECT JOINS · MATCHES (one line each).
  One patient per screen; the **full transcript sits beneath each card in a collapsed row-group** with
  the AI's evidence excerpt highlighted in place. Two editable cells: a direction-aware dropdown
  (live-dashboard vocabulary) + a free-text note.
- **`Doctor_Verdicts`** — append/upsert on Join Key. The ground-truth ledger for the voice-bot KB and
  the autonomous-judge calibration.

`Call_Verdicts` is never written to. **Harvest always precedes destroy-and-redraw**, so a rebuild
cannot lose a typed answer. Hidden machine column carries an opaque token, not the phone number.

**First real run:** 32 cards — 6 flagged · 4 mismatch · 8 ai-only · 13 unclear · 1 suspect join ·
13 match lines · 19 incoming-no-claim excluded. 29 usable transcripts, 3 empty.

### 2. 🔴 The call-webhook 403 outage RECURRED (D159)
Tiles stuck on "Checking the call…" forever. **Not** the `.env`. The **MyOperator panel has been
sending the old 12-character `@` key since 06-Jul 13:41.** The Session-94 fix survived exactly one
verification call (4 successes, 16:28–16:35 on 07-Jul) and reverted. **1,074 + 2,744 + 631 = 4,449
silent 403s across three days.** Found in the web-server access log; the receiver 403s *before* it
raw-logs, so nothing else could see it.

Fixed by aligning the VPS to the panel (not the panel to the VPS — whatever rewrites the panel cannot
rewrite `/root/wa/.env`). Restart at 10:28:32; last 403 10:28:02; first 200 10:29:17; `Call_Durations`
rows 101–107 landing with real `bridged/answered/talk` values.

**The clinic is back on the OLD 12-char `@` secret. Rotation is on the backlog — both ends, verified
across a full clinic day.**

### 3. The duration gate now FAILS OPEN (D156) — `Dashboard.html` v18.19
Two bugs, found in the **live Apps Script export** (the repo copy has no gate at all):
- **Bug A:** only `fuCalled`/`fuRefId` were persisted; the three result states lived in page memory, so
  every reload re-rendered "Checking…" and restarted a fresh 3-minute timer. For anyone who refreshes,
  the spinner was permanent. **This was the reported symptom.**
- **Bug B:** a call returning without a `reference_id` was persisted as *called with no ref*;
  `fuResumePolls` skipped it silently and `fuStartPoll` had a bare `if(!ref) return;`. No poll, no
  timeout, no escape — forever, across every reload.

v18.19 (md5 `034529a124c6bfab8aec2b675620dfec`, `node --check` clean, 16/16 invariants): all six states
persist; the timeout is measured from the CALL (`fuPlacedAt`), not the page load; both `if(!ref)` paths
fail safe; the day key is local (IST) not UTC, which flushes the stuck entries once. **And when a call
cannot be MEASURED, the outcome dropdown unlocks behind an "unverified" banner.** A call measured as
*not connected* still blocks, exactly as D77 intended. Deployed; build stamp `v18.19 · S124` confirmed.

### 4. Two corrections to the Session-123 record (D157, D158)
- **D157.** 06-Jul was **36 outgoing / 26 incoming**, not 22/40. The "40" was rows with *no claim*; only
  19 were incoming. Of 20 outgoing-with-claim: 16 Match, 4 Mismatch → **80%, not 73%.**
- **D158.** The phone-keyed forward-window join can bind an **outgoing** call's claim to an **earlier
  incoming** call from the same number. Proven: `…5227` rang in at 12:01, was called back at 13:40; the
  13:40 claim attached to the 12:01 incoming call → one bogus Mismatch + one bogus "No claim logged".
  **`verdict_review.py` isolates these into a SUSPECT JOINS section and excludes them from the match
  rate. The join in `call_verdict.py` is NOT fixed.**

### 5. Governance (D160)
The committed `Dashboard.html` is 84,427 chars with no gate; the live one is 152,984. **Half the
running dashboard has never been committed.** Two of this session's diagnoses were made against the
stale copy and were wrong. The live export is committed with this EOS and must be committed with every
EOS that touches the dashboard.

### New fault-code / surveillance changes
- `CALLHOOK_SECRET_MISMATCH_403` — **recurred; detection still NOT BUILT.** Now the top diagnostics task.
- New verification standard (§124.7): a fix to a webhook, secret, timer or gate is verified only after
  **one real call AND a re-check ≥1 hour later on the same clinic day.** One immediate call proves nothing.

---

## §1 — STATE / MENTAL MODELS

**Track 2 live systems:**
- **`verdict_review.py` (Stage 3b) — LIVE, run on demand.** md5 `af6622e4edc3f454cf0bfed128c4f76b`.
  Owns `Verdict_Review` + `Doctor_Verdicts` in the doctor-only sheet. No timer.
- **`call_verdict.py` (Stage 3 judge) — LIVE, unchanged this session.** md5 `8c8ae1656056d8d1b2dec1b4776fe5c9`
  (GitHub copy verified identical). **Carries the D158 join defect and the D157-corrected numbers.**
- **`Dashboard.html` v18.19 — LIVE (D156).** Gate fails open on couldn't-measure.
- **`call-hook.service` — LIVE again** since 10:28:32 on 08-Jul, on the OLD 12-char `@` secret (D159).
- Stage 1 (02:00) + Stage 2 (03:00) LIVE + healthy; Drive OAuth token fresh/permanent.
- WABA sends still BLOCKED vendor-side (D120); `wa_approve` still nohup; key rotations still overdue.

**Track 1 / PC-local:** `processor.py` at D148 (md5 `171a090645da130a4f4cbb0c0b102f22`); Vitals & Plan
Step 5 complete; Step 7 not started; Hindi spelling task open.

**Mental models (new or reinforced this session):**
- **No verification mechanism may stand between a staff member and recording what a patient said.**
  Two clinic days of outcome data were lost to a gate waiting on a webhook. Filing is the staff's job;
  verifying is the system's job; they must not share a critical path.
- **One successful call does not verify a fix.** S94 was closed on one call and was dead in seven minutes.
- **A 403 is invisible.** The receiver rejects before it raw-logs and before it journals. Absence of a
  `YYYY-MM-DD.jsonl` cannot distinguish "no delivery" from "rejected". Only the web-server access log can.
- **The panel can revert.** Align the VPS to the panel, not the reverse — `.env` is ours, the panel isn't.
- **A safety flag is a clinical signal about a patient, never a statement about staff accuracy.** It must
  never be hidden by a bookkeeping rule (three flagged rows were collapsed into the Matches list; two
  flagged incoming calls were dropped from the tab entirely).
- **The runbook is not evidence.** Two S123 figures and one S94 verification claim did not survive
  contact with the live data today. Re-derive from the data before building on a recorded number.
- **0 cards refereed.** Every statement about the AI's accuracy — including "80%" — is agreement, not
  accuracy, until the owner fills `Doctor_Verdicts`.

---

## §2 — BACKLOG (what to pick up next)

### 🔴 TOP — the detection gap the last two incidents both exposed
1. **Build the `CALLHOOK_SECRET_MISMATCH_403` detector.** Two parts, both small: (a) the receiver counts
   and logs its 403s (it currently rejects in total silence); (b) the watchdog alerts if no
   `YYYY-MM-DD.jsonl` exists by mid-morning on a clinic day. Specced in S94, never built, recurred in 36h.
2. **Re-check the webhook ≥1 hour after the 08-Jul fix** and again on 09-Jul morning. If the panel
   reverts again, find what is rewriting it (a second webhook entry is the leading suspicion).

### OWNER TASK (no build, ~20 min) — everything downstream depends on it
3. **Referee the 32 cards in `Verdict_Review`.** Zero are done. This is the only thing that converts
   "the AI agrees with staff 80% of the time" into "the AI is right N% of the time", and it is the
   ground truth for the autonomous judge and the voice-bot KB.

### STAGE-3 FOLLOW-THROUGH
4. **Fix `call_verdict.py`: agent + Clinic ID from the CALL record, not the claim.** 21/27 cards say
   "(not recorded)" — including a conduct complaint against the doctor. Clinic ID is blank on 100% of
   rows, which **blocks the doctor console entirely** (no Clinic ID → no last visit, no diagnosis).
5. **Fix the D158 join defect** — an incoming call must never absorb a later outgoing call's claim.
6. **Systemd timer** for `call_verdict.py` (~03:30 IST) + `verdict_review.py` (~03:45 IST).
7. **`verdict_review.py` v1.1** — the de-identified `Verdict_Training_KB` export that seeds the voice-bot
   KB. Needs the Stage-4 de-identifier (unbuilt) and refereed rows (item 3).

### THE STAFF-FACING PROGRAMME (designed this session, not built)
8. **Reduce the staff vocabulary to 4–5 "what next" choices**; the AI supplies the 11-code "what happened"
   from the transcript. Staff answer what they know at hang-up; the machine answers what it can hear.
   Owner to supply the wording (Hindi where it helps).
9. **Ask at hang-up, one tap, optional note.** Batch filing exists because filing is expensive and deferred.
10. **Never show staff the AI.** Corrective action reaches them from the doctor, about the patient.
11. **Measure staff on completion, never on accuracy.** (Today: 15 of 36 outgoing calls — 42% — got no
    outcome at all.)
12. **Background reconciler** (claim → call, the reverse join). Must read `Call_Feed`, NOT `Call_Recordings`:
    an attempted call that rang out has no recording. Three verdicts that must never be collapsed —
    *no attempt* (never called) · *attempt, not connected* (**blameless**) · *connected but nothing asked*
    (only the AI judge can see this).
13. **Doctor-only review console.** Blocked on item 4 (Clinic ID). Doctor's actions land in a
    `Doctor_Actions` tab he owns; the staff dashboard reads it. `WebApp.gs` stays sealed.
14. **Diarisation (Stage 2).** Transcripts are one wall of text with no speakers; Sarvam includes
    diarisation at ₹30/hour. Cheapest high-leverage change; prerequisite for speaker-aware judging and
    for the voice bot's listening half.
15. **Voicemail outcome code** — a three-place change (live dashboard dropdown, `call_verdict.py`
    `VOCAB_*`, `verdict_review.py`). Dissolves if item 8 lands first ("couldn't reach").

### Track 2 live backlog (carried)
🔴 **Rotate `CALLHOOK_SECRET` properly** (both ends; the clinic is on the old `@` key) · 🔴 WABA
authorizer/Lokesh + re-fire TEST · make `wa_approve` a systemd service · rotate `WA_APPROVE_KEY` ·
🔴 service-account key rotation (Lokesh) · AKEY_14 · **arm the timer-freshness checker** · maintenance
jobs · `clinic_health_report.py` UTC→IST fix · courtesy-rotate `FU_UPLOAD_SECRET` (D145) ·
**empty-transcript guard** (3 empty on 06-Jul; they land in Unclear looking like AI failures) ·
**VPS Python 3.9 is past EOL** (google-auth warns on every run).

### Track 1 backlog (unchanged)
Hindi SPELLING corrections in `vitals_page.html` LIB strings · Step 7 new-patient reconciliation ·
Living Clinic Data Map (§66.6).

### Documentation backlog
- **DONE this EOS:** KB v1.48 · Umbrella v1.36 · Runbook v58 · Call_Console_Evolution_Spec v1.6 ·
  Diagnostics_Surveillance_Spec v1.6 · incident report · **the LIVE Apps Script export committed (D160)**.
- **Notion was NOT updated** — the connector was unauthenticated all session. `NOTION_UPDATE_S124.md`
  is in the handoff kit, ready to paste.

---

## §3 — KEY PATHS / FACTS (Session-124 additions in **bold**)

- **Stage-3b analysis layer:** **`/root/wa/recordings-archive/verdict_review.py`** (md5
  **`af6622e4edc3f454cf0bfed128c4f76b`**, 1364 lines). Modes: `--selftest` (offline, 117/117),
  `--dry-run` (reads everything, writes nothing — not even a missing tab), real run,
  `--days N` (1–90, default 7), `--no-transcripts`. VPS python `/root/wa/venv/bin/python3`.
- **Reads:** `Call_Verdicts` (doctor-only sheet `1rq9VvB5L94EmmZbiUwase9HBLsJ3htispYLd1rHjSRQ`) +
  transcripts from Drive. **Writes:** **`Verdict_Review`** + **`Doctor_Verdicts`** in the same sheet.
  Env: `GOOGLE_SA_KEY` **or `WA_SA_KEY`** (the clinic `.env` uses the latter), `DRIVE_TOKEN_FILE`.
- **Stage-3 judge:** `/root/wa/recordings-archive/call_verdict.py` (md5 `8c8ae1656056d8d1b2dec1b4776fe5c9`,
  1037 lines) — **unchanged this session, GitHub copy verified byte-identical to the VPS copy.**
- **Dashboard:** `Dashboard.html` **v18.19** (md5 `034529a124c6bfab8aec2b675620dfec`, 2738 lines).
  Gate constants: `FU_MIN_TALK=15`, `FU_POLL_EVERY_MS=6000`, `FU_POLL_TIMEOUT_MS=180000`.
  `localStorage` key `dashFuCalled` now holds `{date, ids, refs, placed, talked, missed, timeout}`
  with a **local (IST)** date key. Deploy rule unchanged: edit existing deployment → New version.
- **Call webhook:** receiver `/root/wa/call-hook/call_hook_capture.py`, gunicorn on `127.0.0.1:8098`,
  route **`POST /mo-callhook?key=…`**, proxied by `followup.dr-manoj.in`.
  **A row reaches `Call_Durations` only when `category == "obd"` AND `client_ref_id` is present** —
  i.e. only for calls placed through the dashboard dialer. A hand-dialled call can never unlock the gate.
  **The secret gate returns 403 BEFORE `raw_log()`** — a rejected delivery leaves no trace anywhere
  except the web-server access log.
- **Access-log forensics (the only place a 403 storm is visible):**
  `grep -h "mo-callhook" /home/*/logs/*access* | sed -E 's/key=[^& ]+/key=<masked>/g' | tail -20`
  Count by date+status: pipe through `sed -E 's/.*\[([0-9]{2}\/[A-Za-z]{3}\/[0-9]{4}).*" ([0-9]{3}) .*/\1 \2/' | sort | uniq -c`
- **`.env` edits — the §94.1-proof recipe:** back up first; rewrite with
  `awk '/^KEY=/{print "KEY=" ENVIRON["NEWVAL"]; next} {print}'` (never `awk -v`, never `sed` by line
  number); then assert **exactly one matching line**, **only the value changed** (`diff` of key names),
  and **identical line counts**, before `\cp -f`.
- **`Call_Verdicts` layout (35 cols, S123/D152):** Date · Time · Direction · Patient Number · Agent ·
  Patient Name · Clinic ID · Duration · Claimed Outcome · AI Outcome · Verdict · Match Confidence ·
  Outcome TRUE/FALSE · AI Reason · Evidence · Spoke With · Confidence · 6× Flag · Conduct Note ·
  Recording Link · Transcript Link · Join Key · Status · Error · Judged At · Prompt Ver · Model ·
  Doctor Flag · Doctor Note · Final Outcome. **Both scripts refuse to run on a changed header.**
- **`Doctor_Verdicts` layout (17 cols):** Join Key · Date · Time · Direction · Patient Number ·
  Patient Name · Clinic ID · Agent · Claimed Outcome · AI Outcome · Verdict · Match Confidence ·
  **Doctor Final Outcome** · **Doctor Note** · Section · Recorded At · Build.
- Answer vocabularies unchanged (11 outgoing / 9 incoming + `UNCLEAR`). `verdict_review.py` adds two
  **doctor-only** escapes to the dropdown: `cannot_judge`, `transcript_bad`.
- Follow-up tracker (PC): `processor.py` md5 `171a090645da130a4f4cbb0c0b102f22`.

---

## §4 — SESSION-START CHECKS (revised)
1. `System_Health` tab — any open incidents?
2. **Call-hook healthy?** `ls -lt /root/wa/call-hook/call_hook_logs/ | head -3` — is *today's*
   `YYYY-MM-DD.jsonl` present and growing? **If not, go straight to the access log** (see §3) — the raw
   log cannot tell you whether deliveries are absent or being rejected.
3. Any fault codes / banners from staff since last session? Stuck "Checking…" tiles?
4. Is `drive_token.json` still valid? (Stage 1/2/3 all share it. Tell: did last night's transcripts
   appear in the Drive "Call Transcripts" folder?)
5. **Has the owner refereed any `Verdict_Review` cards?** (`Doctor_Verdicts` row count.)

If any incident is open → address before new build. Else read KB + runbook, confirm, and pick up
**§2 item 1 (the 403 detector)**.

---

## §5 — START-HERE PROMPT — Session 125 (paste at next session's start)

Hi Claude. Continuing my clinic-automation project (**Session 125 — use the next number**).
I'm Dr. Manoj Agarwal, Dr. Manoj Agarwal Clinic, orthopaedic surgeon, Bareilly. Solo practice,
older Hindi-first semi-urban patients.

**Working protocol (follow strictly):** plain language, no assumed coding knowledge · ONE step at a
time, wait for my explicit confirmation · full-file replacements only, never diffs · ALL-CAPS from
me = urgent · mask all secrets/tokens · nothing live rebuilt without my OK, manual workflow always
stays fallback · build/test offline → py_compile (I use `python`) → then I install · VPS python
`/root/wa/venv/bin/python3`. Ending a session: **EOS** (code changed) or **EOS-light** (docs only).

**Canonical docs are in THIS PROJECT'S KNOWLEDGE (single consolidated files):**
KB `Clinic_Master_KB_SystemsRegister` **v1.48** — WINS on any conflict · **HANDOFF_RUNBOOK Session
124 v58** (§0 what happened, §2 backlog) · **Umbrella Architecture v1.36** · API_QUICK_REFERENCE_CARD ·
**Call_Console_Evolution_Spec v1.6** · **Diagnostics_Surveillance_Spec v1.6** · Maintenance_SOP_Spec.
Code lives in GitHub (`drmanoj-clinic-automation`; canonical docs in `canonical-docs/`). **The LIVE
Apps Script export is the canonical dashboard, not the repo copy (D160)** — `Clinic_Callback_Tracker_AppsScript_S124.json`
is in project knowledge. Patient data is NOT in this project.

**WHERE WE STOPPED (Session 124, FULL EOS — one new script, one live dashboard file, one live secret):**
(1) **Verdict Analysis Layer BUILT** — `verdict_review.py` (md5 `af6622e4edc3f454cf0bfed128c4f76b`,
selftest 117/117, ₹0): a rolling-7-day, one-patient-per-screen `Verdict_Review` tab with full
transcripts in collapsed row-groups and the AI's evidence highlighted, plus a `Doctor_Verdicts`
ground-truth ledger. First run: 32 cards. **I have refereed 0 of them.**
(2) 🔴 **The call-webhook 403 outage recurred** — the MyOperator panel had been sending the OLD 12-char
`@` key since 06-Jul; the Session-94 fix survived exactly one call. 4,449 silent 403s over three days.
Fixed by aligning the VPS to the panel at 10:28:32. **We are back on the old secret.**
(3) **The duration gate now FAILS OPEN** — `Dashboard.html` v18.19 (md5 `034529a124c6bfab8aec2b675620dfec`),
deployed and confirmed. Two clinic days of outcome data were lost to a gate waiting on a webhook.
(4) **Corrections:** 06-Jul was 36 outgoing / 26 incoming, match rate **16/20 = 80%** (not 22/40, 73%);
and the claim-join can bind an outgoing call's claim to an earlier incoming call from the same number
(**defect still open in `call_verdict.py`**).

**START HERE — Session 125, in this order:**
1. 🔴 **Build the `CALLHOOK_SECRET_MISMATCH_403` detector** (specced in S94, never built, recurred in
   36 hours): the receiver counts + logs its 403s, and the watchdog alerts if no `YYYY-MM-DD.jsonl`
   exists by mid-morning on a clinic day. **A 403 is currently invisible to every system I own.**
2. Confirm the webhook is still healthy (it must be re-checked ≥1 hour after a fix, not once).
3. Then either: **fix `call_verdict.py`** so Agent and Clinic ID come from the CALL record, not the
   staff claim (21/27 cards say "(not recorded)"; Clinic ID is blank on 100% of rows and **blocks the
   doctor console**) — or **the staff-UI programme** (§2 items 8–12: 4–5 "what next" choices for staff,
   the AI supplies the 11-code "what happened", one tap at hang-up, and the background claim→call
   reconciler that must read `Call_Feed`, not `Call_Recordings`).

**Session-start checks:** System_Health open incidents? · **is TODAY's `call_hook_logs/YYYY-MM-DD.jsonl`
present and growing?** (if not, go straight to the web-server access log — the raw log cannot see a 403) ·
staff banners / stuck "Checking…" tiles? · did last night's transcripts appear in the Drive "Call
Transcripts" folder? · has anything landed in `Doctor_Verdicts`?

**Standing rule added this session:** a fix to a webhook, secret, timer or gate is verified only after
**one real call AND a re-check ≥1 hour later on the same clinic day.** One immediate call proves nothing —
that is exactly how Session 94 recorded a dead fix as "verified end-to-end".

**Connected sources:** Google Drive (drmka.ortho@gmail.com) · Gmail · Notion (Clinic HQ — **needed
re-authorisation last session; the S124 Notion update is still unposted**) · GitHub
(drmanoj-clinic-automation) · ClickUp parked (D17, do not use). Read the KB + runbook, confirm, then
tell me which item you recommend and start.
