# START-HERE prompt — Session 13
**Dr. Manoj Agarwal Clinic · paste this at the top of the next chat**

Continuing Dr. Manoj's clinic automation. **Read the Master KB first** (`Clinic_Master_KB_SystemsRegister_v1.md`) — it is the canonical Systems Register: every component, parameter, tab contract, and API recipe through build **v17**. Then this prompt.

## Standing protocol (unchanged — carry forward)
Plain language; one step at a time, wait for my confirmation; **full-file replacements only** (never diffs); ALL-CAPS = urgency; **mask all secrets/PHI**, never print; nothing live is rebuilt without explicit confirmation; manual workflow always stays as fallback. Build/test offline → **md5sum + py_compile / node --check** gate → restart. Apps Script: **edit existing deployment → New version** (never new deployment). VPS installs: **WinSCP → md5 verify → py_compile → restart** (terminal mangles large pastes); `\cp -f` to overwrite. Deliver every artifact as a **download** + present_files.

## Where we are (one line)
Dashboard **v17 LIVE & deployed**: callbacks + click-to-call + per-agent server-bound identity + sheet-driven roster + WhatsApp feed/thread/reply + recordings + **follow-up call loop (v16)** + **incoming-call outcomes (v17)** + doctor-only escalations + next-day email summary. The Master KB v1 was just written and is current.

## What I confirmed done at the end of Session 12
- v16 (follow-up loop) and v17 (incoming-call outcomes) both pasted and **deployed** (New version). Header reads `v17 · inbound`.
- Script Properties set: `SUMMARY_EMAIL` (works — test email received), `NTFY_TOPIC`. `SUMMARY_NTFY` left OFF (ntfy.sh free quota reserved for the live notifier; 429 confirmed — self-hosted ntfy deferred to rollout step 4).
- Daily trigger on `sendFollowupSummary` set.

## OPENING TASKS for this session (do in this order)

### 1. Package & commit (do first — closes Session 12 properly)
- **GitHub:** I'll commit via GitHub Desktop. Give me the exact files to stage and a commit message. Files changed/added in Session 12: `dashboard/WebApp.gs` (v17), `dashboard/Dashboard.html` (v17). Also fold in the session's docs under a `docs/` folder: `Clinic_Master_KB_SystemsRegister_v1.md`. Suggested message: "Session 12: follow-up call loop (v16) + incoming-call outcomes (v17) + Master KB v1".
- **Notion "Clinic HQ":** append the **Master KB v1** as a page (or replace the prior Systems Register content with it, since it's now canonical). Main page id `38618b9d-8f91-813e-9773-c20f567fd32f`. (Notion was appended at the end of Session 12 with the KB; confirm it's current, update the build to v17 and the "state" section.)

### 2. The remaining operational docs (write these — they were sequenced after the KB)
Produce each as its own reviewable download, one at a time:
- **Troubleshooting runbook** — symptom → cause → fix. Pull the hard-won gotchas from the KB §3–§4 and §11 (lowercase-bearer 401, OLS proxy needs extprocessor+context not `[P]`, nanosecond-timestamp trim, deploy-version-discipline silent no-op, OBD's five rules, the ntfy 429, `\cp -f`, WinSCP-not-paste).
- **Staff manual / call-console training script** — plain "what to tap when" for reception: how to log a follow-up outcome, how to log an incoming-call outcome (the identity → reason → resolution flow), what each outcome means, that clinical reasons auto-reach the doctor. English (no Hindi needed, per owner). Short, screenshot-friendly.
- **Doctor manual** — the daily/weekly rhythm: reading the morning summary email, clearing the Escalations tab (Completed treatment / Dropped out / Will follow up / Other), the "close follow-up · treatment complete" authority, when to escalate to Lokesh.

### 3. Then resume the build backlog (pick a lane when ready)
- Roll out per-agent `AKEY_` keys (until then all calls log as ext 10).
- 360° patient query box (build on current data; Clinic-ID join).
- Supervisor `doctor.py` (hybrid: health-in-each-module + thin central collector for the daily digest + dead-man's-switch — keep the switch OFF-VPS).
- De-identification pipeline → NotebookLM (D18).
- Revenue MIS (D19, data-ready) · HR lane (D20, data-ready).
- Website cheap wins (Lane 3): close R1 (which property `GT-MJB2DPLN` routes to), GA4 internal-traffic filter. (Schema phone typo already fixed.)
- At rollout step 4 (brain migration to VPS): self-hosted ntfy + topic bifurcation + the D9 shared-fate revisit.

## Files to have on hand
From the Session 12 outputs: `WebApp.gs` (v17), `Dashboard.html` (v17), `Clinic_Master_KB_SystemsRegister_v1.md`, this prompt. From the prior FULL handoff zip: the `api/` references, `obd/` recipe, `prev_runbooks/`, the VPS service files, `push_followups_today.py`, `converter/`.

Confirm Task 1 first (commit + Notion), then proceed to Task 2 docs one at a time.
