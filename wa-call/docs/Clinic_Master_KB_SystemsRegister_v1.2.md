# Dr. Manoj Agarwal Clinic — Master Knowledge Base & Systems Register
**Advanced Orthopaedic Surgery Centre, Bareilly**
Version 1.2 · 28 June 2026 (Session 14) · Owner: Dr. Manoj Agarwal · Maintained with Claude (per session)

> **What this is.** The single canonical reference for the whole clinic-automation system — every component, every parameter, every data contract, every hard-won rule. This is the "Clinic Systems Register" the Umbrella Architecture (delta #2) requires: all infra/identity facts live HERE once, and other docs reference this instead of restating them, so nothing drifts.
>
> **NotebookLM-ready.** This file is structured, self-contained, and contains NO patient data and NO real secrets (only masked hints). It can be uploaded to NotebookLM as a reasoning source as-is.
>
> **Precedence.** Where any older note disagrees with this file, THIS file wins. Companion living doc: the *Umbrella Architecture* (the "why/shape"); this is the "what/where/how".

---

## 0. Security charter (read first)

- **Secrets never appear in this file, Git, or Notion.** Only masked hints (e.g. `lHCx…`). Real values live ONLY in: VPS `/root/wa/.env` (chmod 600), the follow-up `.env`, Apps Script Script Properties, and Apple Notes.
- **PHI never goes to the cloud un-de-identified.** Patient data lives in the Google Sheet / Drive / local device under access control. NotebookLM gets only de-identified data.
- **Two MyOperator tokens, never mixed** (different systems — see §3).
- **Masking discipline in tooling:** `sed -E 's/(=.{5}).*/\1…(hidden)/'` — never `cat` a secret file, never print a full patient number (mask to last-4).

---

## 1. What the system is

Clinic automation for a solo orthopaedic surgeon serving an older, Hindi-first, semi-urban base in Bareilly. It unifies **IVR calls + WhatsApp Business API (WABA) + a Google Apps Script dashboard + a Hostinger VPS (Flask relays) + Google Sheets (data spine)** into one operations hub that **cares** (timely follow-up), **holds accountable** (verified outcomes), and **learns** (dropout/channel patterns). The EMR (**Docterz**) is closed — CSV export only, no API, no webhooks.

**Architecture in one line:** modules talk through DATA (the Sheet), never to each other; one universal join key (**Clinic ID**); one writer per table; every module degrades to a fallback, never a crash.

---

## 2. Infrastructure constants (identifiers — NOT secrets)

### MyOperator
| Item | Value |
|---|---|
| Company ID | `68384350414b9847` |
| WABA ID | `2101222617483538` |
| Phone Number ID | `1090067637530949` |
| WABA number | `9358008080` |
| IVR incoming (published) | `8065293652` |
| Internal routing DID (in logs `_did`) | `+918047947130` |

### VPS (shared)
| Item | Value |
|---|---|
| Host / domain | `followup.dr-manoj.in` |
| IP | `93.127.195.49` · server `srv1746119.hstgr.cloud` |
| OS / stack | AlmaLinux 9 · CyberPanel + OpenLiteSpeed + gunicorn |
| Work dir / venv | `/root/wa` · `/root/wa/venv` (Flask, gspread, google-auth, gunicorn) |
| Timezone | Asia/Kolkata |
| vhost.conf | `/usr/local/lsws/conf/vhosts/followup.dr-manoj.in/vhost.conf` (owner nobody:nobody, 750). After edit: `systemctl restart lsws` |
| Gotcha | `cp` is aliased to `cp -i` → use `\cp -f` to overwrite |
| Public site | `https://drmanojagarwal.com` (canonical; `.in` 301s to it) — **shares this VPS** (D9 accepted-risk; revisit at brain-migration) |

### Google
| Item | Value |
|---|---|
| Sheet "Clinic Callback Tracker" | ID `1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0` |
| Service account | `patient-mirror@sincere-octane-500413-v8.iam.gserviceaccount.com` |
| Apps Script | dashboard web app `/exec`, gated `?k=KEY`, **build v17.1 · inbound** |
| GA4 LIVE (.com) | property `540951406` · `G-XV7PPY194Q` (**keeper, never archive**) |
| GA4 legacy (.in) | property `513765081` · likely `G-SFBCM4KEKR` |
| GTM | keep `GTM-PQG6VNXZ`; delete `GTM-P9HNQ3NH` |
| Meta Pixel | `1184741477099159` |
| Docterz clinic id | `1823` |

### Code / knowledge homes
| Item | Value |
|---|---|
| GitHub | `drmanoj-clinic-automation`, branch `main`, local `D:\dr-manoj-git\drmanoj-clinic-automation`. Folders: `dashboard/`, `wa-receiver/`, `wa-send/`, `wa-call/`, `notifier/`, `converter/`. Committed via GitHub Desktop |
| Notion | "Clinic HQ" main page `38618b9d-8f91-813e-9773-c20f567fd32f`; Tech & Systems Register `collection://e2e5e030-efc6-41a3-8f8a-70e808aaa5cb` |

---

## 3. The three MyOperator systems (never mix)

| System | Does | Host | Token (masked) | Auth style |
|---|---|---|---|---|
| **A — Call/Logs + Recordings** | read call logs, fetch recording links | `developers.myoperator.co` | Calling/Logs `3f76…` (32 ch) | `token` as a **parameter** (body/query) — no Authorization header |
| **B — WhatsApp send** | send template + free-text messages | `publicapi.myoperator.co` | WhatsApp "Authentication" `lHCx…` | `Authorization: Bearer` (**capital B**) + `X-MYOP-COMPANY-ID` |
| **C — Inbound webhooks** | receive incoming WhatsApp (push) | MyOperator → your URL | your self-chosen `?key=` gate (not a MyOperator token) | MyOperator POSTs JSON to you |
| **OBD — click-to-call** | place 2-leg agent→patient calls | `obd-api.myoperator.co` | `x-api-key` (`oomf…`, public) + `secret_token` (`26eb…`, real secret) | header `x-api-key` + secret in body |

### Token regeneration risk
- **WhatsApp "Authentication" (`lHCx…`) = HIGH risk.** Regenerating breaks live panel-native call automations (`new_post_call_message`, `eng_missedaftercall`) within ~24h (a grace window). Plan with MyOperator (Lokesh) before doing it; not needed for normal operation.
- **Calling/Logs (`3f76…`) = LOW risk.**

---

## 4. API recipes (proven on this account)

### B — WhatsApp send  `POST publicapi.myoperator.co/chat/messages`
- Headers: `Authorization: Bearer <lHCx…>` (**capital B** — lowercase = AWS IAM explicit-deny 401), `X-MYOP-COMPANY-ID: 68384350414b9847`, `Content-Type` + `Accept` json.
- Template vars = **numeric string keys** `"1"`, `"2"` inside `body` (NOT `var_1`, NOT a list).
- Success returns `message_id` (unique per message) + `conversation_id` (per recipient). Webhooks join on **`message_id`** (`myop_ref_id` is null for API sends; also parse the misspelled `conversaton_id`).
- List templates: `GET /chat/templates?waba_id=<id>&waba_template_status=approved`.

### A — Call logs  `POST developers.myoperator.co/search`
- Params in a **raw JSON body**; `token` (`3f76…`) is a parameter, no Authorization header.
- Use **bare paths** (ignore the Postman `/search/` prefix — it 404s here).
- Recording link: `GET /recordings/link?token=…&file=…` (24h link).
- Nanosecond timestamps: trim to ≤6 fractional digits before Python 3.9 `fromisoformat()`.

### OBD — click-to-call  `POST obd-api.myoperator.co/obd-api-v1`  (LIVE, proven 27 Jun)
Body (User Dialer = production mode):
```json
{ "company_id":"68384350414b9847", "secret_token":"<26eb…>", "type":"1",
  "number":"+91XXXXXXXXXX", "public_ivr_id":"<6a3f…>", "user_id":"<panel-hex>",
  "reference_id":"<unique>", "max_call_duration":300, "call_hold":true }
```
**Five locked rules** (each was a debugged failure):
1. `number` MUST be E.164: `+91`+10 digits. Bare 10- or 12-digit both fail.
2. `max_call_duration` MUST be a real integer `300` (not `"300"`). ≤5400.
3. `user_id` = the panel "User id" hex works directly (no UUID, no Get-Users API).
4. `reference_id` MUST be unique per call (a repeat → 403, locked ~2 days).
5. Calls are **queued, not instant** — "accepted" (200) ≠ ringing. It's a **2-leg** call: agent's phone rings first, then the patient bridges (a test "patient" must be a different handset from the agent's).
- Anonymous Dialer is **disabled** on this plan (403) — use User Dialer. Get-Users API returns 404 (unprovisioned, not needed).

---

## 5. Data spine — the Google Sheet tabs (one writer each)

| Tab | Writer | Reader(s) | Holds |
|---|---|---|---|
| `Call_Feed` | call-log poll | dashboard | raw call events |
| `Callbacks_Today` | staff/dashboard | dashboard | missed-caller callback status |
| `Patient_Master` | `push_patient_mirror.py` (one-way from local CSV) | dashboard | patient context (name, Clinic ID, dx, age, sex, last visit) — **read-only mirror** |
| `WA_Inbox` | VPS receiver + send relay | dashboard | WhatsApp messages (in/out) |
| `Agents` | human (sheet) | dashboard | roster: `Ext | Name | UserId | Active` |
| `Followups_Today` | `push_followups_today.py` (one-way) | dashboard | the daily follow-up worklist |
| `Followups_Settled` | `push_followups_today.py` | dashboard | returned/dropout history |
| `Followup_Outcomes` | **dashboard only** (v16/v17) | summary | one row per logged outcome (follow-up + incoming). Morning re-push never touches it |
| `Followup_Escalations` | **dashboard only** (v16/v17) | doctor view + summary | items needing the doctor; persist until resolved |

### Tab contracts (column headers)
- **`Followups_Today`:** `Key, Section, PR, Patient Name, Mobile, Diagnosis, Due Date, OD, Status`
- **`Followups_Settled`:** `Due, Patient, Mobile, Clinic ID, Outcome, Handled By, When`
- **`Followup_Outcomes`:** `When, Key, Patient, Mobile, Section, Outcome, Source, Days, Expected Date, Detail, Handled By, Agent Ext, Settle, Identity, Reason, Channel, For Whom, Clinic ID`
- **`Followup_Escalations`:** `Raised, Key, Patient, Clinic ID, Diagnosis, Mobile, Last Visit, Reason, Detail, Raised By, Status, Resolution, Resolved When`

---

## 6. Live components — DO NOT REBUILD

| Component | Where | Role |
|---|---|---|
| **Dashboard** (Apps Script) | `dashboard/WebApp.gs` + `Dashboard.html`, build **v17.1** | The cockpit (see §7) |
| **Inbound WA receiver** | VPS `wa_receiver.py`, port 8095, path `/wa-webhook?key=` | inbound WhatsApp → `WA_Inbox` (+ media links) |
| **WhatsApp send relay** | VPS `wa_send_api.py`/`wa_send.py`, port 8096, path `/wa-send`, gate `SEND_API_SECRET` (X-Send-Key) | outbound replies (`direction=out`), 24h-window guarded |
| **Click-to-call relay** | VPS `call_api.py`, port 8097, path `/call`, gate `CALL_API_SECRET` (X-Call-Key) | 2-leg OBD calls dialed-as the logged-in agent |
| **wa-notifier** | VPS service | WhatsApp→ntfy name-only alerts (topic `drmka-yfv80gjcixa643` on ntfy.sh) |
| **Daily converter** | `converter/docterz_to_myoperator.py` | Docterz CSV → MyOperator campaign CSVs |
| **Follow-up ingest** | `push_followups_today.py` (staff PC, daily) | Staff_Action_Today.xlsx → `Followups_Today`/`Followups_Settled` |

### Ports (all behind OpenLiteSpeed on followup.dr-manoj.in)
| Service | Local | Public path | Gate |
|---|---|---|---|
| Inbound WA receiver | 127.0.0.1:8095 | `/wa-webhook?key=` | `WA_WEBHOOK_SECRET` |
| WhatsApp send relay | 127.0.0.1:8096 | `/wa-send` | `SEND_API_SECRET` |
| Click-to-call relay | 127.0.0.1:8097 | `/call` | `CALL_API_SECRET` |

---

## 7. The dashboard (build v17.1) — what it does

**Cockpit sections:** Awaiting callback · Resolved callbacks · **Today's follow-up calls** (v16) · **Escalations** (v16, doctor-only) · **Settled follow-ups** (v16) · Recent WhatsApp · Handled today · Clinic Team. KPI tiles: Awaiting · Incoming missed · Total calls · WhatsApp (48h) · **Follow-ups due** (v16).

**Access model (server-enforced, never trusted from the page):**
- `DASH_KEY` (master) → `full` (doctor, ext 10): everything incl. Escalations view + WhatsApp reply.
- `AKEY_<ext>` (per-agent) → `staff`: read + log outcomes + place calls; no Escalations view, no reply box.
- Active=`no` in the `Agents` tab off-boards instantly; deleting `AKEY_<ext>` is the hard kill.
- The agent is ALWAYS derived from the login key server-side.

**Click-to-call:** green Call buttons → `triggerCall(key, number, rowId)` → server derives agent from key → POSTs `/call` with secret server-side + agent's `user_id`. The `tel:` link is the manual fallback. Placed calls clear the callback row on next refresh (the dashboard reads call logs).

**Follow-up call loop (v16):** reads `Followups_Today`, overlays today's outcomes (settled rows drop off; "couldn't communicate" stays as retry), grouped by Section→priority. Outcome capture writes to `Followup_Outcomes`; escalating outcomes also persist to `Followup_Escalations`. Doctor-only Escalations view resolves with Completed treatment / Dropped out / Will follow up / Other.

**Incoming-call outcomes (v17):** every "Needs a callback now" row has a **"Log outcome ▾"** disclosure (Option A — hidden until tapped, unfolds one step at a time). Known patient → reason + resolution. Unknown number → identity first (existing-patient-new-number / new-patient / **Doctor-urgent** / not-a-patient) → the right sub-flow. New-patient enquiries optionally capture "how did they hear?" (channel-of-acquisition). All write to `Followup_Outcomes` (`Source=Incoming` + Identity/Reason/Channel/ForWhom/Clinic ID); clinical reasons auto-escalate. Known callers now show **Clinic ID + last visit** on the row.

**Doctor/urgent path (v17.1):** the former "surgery enquiry" identity was broadened into a single calm **"🚨 Doctor/urgent — surgery, fracture, accident, severe pain"** choice (internal value still `surgery_enquiry`). Rationale: reception does **not** triage clinically — one high-intent button beats a clinical taxonomy that creates hesitation. Behaviour: it **always escalates** to the doctor's queue (`IN_ESCALATE_IDENTITY = { surgery_enquiry:1 }`) **and still captures the outcome** (appointment booked / will come / etc.). Staff are trained to tap it **and call the doctor immediately** (human-first). On save it fires an instant **high-priority ntfy push** via `notifyUrgentIncoming_()` to the existing `NTFY_TOPIC` (Option A — reuses the live topic so it never trips the ntfy.sh free-tier 429; title `🚨 URGENT incoming call`, priority `urgent`). Push body is **graduated**: known patient = name + status tag, unknown = "new patient"; it **includes the patient phone number** for one-tap call-back (owner decision 28 Jun 2026 — a documented privacy tradeoff: name + number traverse ntfy.sh; **no clinical free-text** ever goes in the push). On-screen the urgent branch shows a red **"Call Doctor urgently"** banner and a lean form (optional name → outcome). Terminology is **patient**, never "lead", throughout the UI and docs.

**Next-day summary:** daily Apps Script trigger on `sendFollowupSummary` → reads yesterday's `Followup_Outcomes` → staff-wise × outcome-wise HTML table → email (`SUMMARY_EMAIL`) + optional ntfy nudge (`SUMMARY_NTFY` toggle, default OFF; topic `NTFY_TOPIC`).

### Refined outcome model (the truth model)
- **Settling** (row leaves worklist): Coming/will visit · Out of town · On medication (source here/outside + days).
- **Non-settling** (stays for retry): Connected but couldn't communicate.
- **Escalating** (→ Escalations, persist until doctor resolves): Already visited (dikha chuke) · Problem/attention · Close follow-up (treatment complete) · Not interested · Treatment elsewhere.
- **Auto-settled from evidence** (not staff-entered): patient appears in consultation CSV → Returned/Done; medicine verified via Sanjeevni.

---

## 8. Agent roster (ext → panel user_id hex → mobile last-4)
| Ext | Name | user_id (hex) | last4 |
|---|---|---|---|
| 10 | Dr Manoj Agarwal | `6838435041f29988` | 4044 |
| 11 | Shavez Ahmed | `686cf49a692bb162` | 4926 |
| 12 | Shivani Srivastava | `686cf557c4f09495` | 9246 |
| 13 | Manoj Bhati | `686cf5a29a97d527` | 4408 |
| 14 | Alisha Khan | `69cfa941359e1649` | 3474 |
| 15 | Darpan Robert | `6a2017dd50280597` | 5546 |
| 16 | Reception Mobile | `6a2018cda8975829` | 4080 |
(Plan = 10 seats; 7 used; 3 spare. Add: one `Agents` row + one `AKEY_<ext>` property — no code/VPS edit.)
**Per-agent `AKEY_` keys ARE LIVE (verified Session 14):** `AKEY_11`–`AKEY_16` are set as Script Properties. Calls/outcomes now log under the **real agent**, not all-as-ext-10. (Confirm the `Agents` tab still carries Ext 11–16 with `Active=yes`.)

---

## 9. WABA templates (approved on the WABA)
| Panel name | Vars | Role |
|---|---|---|
| `drmanoj_post_visit` | {{1}} name | post-visit same-day |
| `drmanoj_followup_tomorrow` | name, due date | reminder, due tomorrow |
| `drmanoj_followup_due` | name, due date | due today / grace 0–3d |
| `drmanoj_followup_missed` | name, due date | missed 4–10d |
| `drmanoj_followup_dropout` | name, due date, days overdue | dropout >10d |
| `new_post_call_message` | — | after-call (LIVE, panel-native automation) |
| `eng_missedaftercall` | — | missed-call (LIVE, panel-native automation) |

Branded short links (GoDaddy `dr-manoj.in`): book · map · app · ios · whatsapp · review · contact. QR standee encodes `https://contact.dr-manoj.in` only.

---

## 10. Secrets inventory (values ONLY in `/root/wa/.env` chmod 600 + Apple Notes)
`CALL_API_SECRET` (relay gate) · `SEND_API_SECRET` (send gate) · `WA_WEBHOOK_SECRET` (inbound gate) · `MYOP_OBD_XAPIKEY` (`oomf…`, public) · `MYOP_OBD_SECRET` (`26eb…`, real) · `MYOP_PUBLIC_IVR_ID` (`6a3f…`) · `MYOP_LOGS_TOKEN` (`3f76…`) · WhatsApp Bearer "Authentication" (`lHCx…`) · service-account JSON.
**Apps Script Script Properties:** `DASH_KEY` (master) · `AKEY_<ext>` (per agent) · `SHEET_ID` · `STAFF_KEY` (legacy) · `SUMMARY_EMAIL` · `NTFY_TOPIC` · `SUMMARY_NTFY` · the call/send secrets mirrored for relay calls · `MYOP_TOKEN` (logs, for recordings).

---

## 11. Working protocol (how the build is run)
Plain language · one step at a time (wait for confirmation) · **full-file replacements only** · ALL-CAPS = urgency · mask all secrets/PHI · nothing live rebuilt without confirmation · manual workflow always stays as fallback. Build/test offline → **md5sum + py_compile / node --check** gate → restart. Apps Script: **edit existing deployment → New version** (never new deployment; reusing a version number silently ships nothing). VPS installs: **WinSCP → md5 verify → py_compile → restart** (terminal mangles large pastes). `\cp -f` for overwrites. Deliver every artifact as a download. Session closes with GitHub commit + Notion refresh + handoff.

---

## 12. State at v17.1 (28 Jun 2026)
**LIVE:** dashboard v17 (callbacks · click-to-call · per-agent server-bound identity · sheet-driven roster with instant off-boarding · WhatsApp feed/thread/reply · recordings · **follow-up call loop** · **incoming-call outcomes** · escalations · next-day email summary) · VPS relays (receiver, send, click-to-call) · wa-notifier · daily converter · follow-up ingest. WhatsApp public API enabled & working. OBD click-to-call proven end-to-end.

**v17.1 (deployed 28 Jun 2026):** incoming **Doctor/urgent** path — always-escalate + outcome still captured + instant ntfy push (name + tag + number). Deployed and confirmed working (header `v17.1 · inbound`).

**Staff/clinic documents (28 Jun 2026, in `docs/`):** Troubleshooting Runbook (EN) · Staff Manual — Call Console (EN, manager) · Doctor Manual (EN) · A4 Wall Card — Call Flows (Hinglish, single page, PDF+DOCX; both flowcharts + combined high-contrast legend) · Call Desk Companion (Hinglish, what-each-option-means). Committed to GitHub `docs/`.

**OPEN (no urgency):** WhatsApp token rotation (HIGH risk, plan with Lokesh) · self-hosted ntfy + topic bifurcation (rollout step 4, with the D9 shared-fate revisit; keep the supervisor's dead-man's-switch OFF-VPS) · 360° patient query (**spec'd + server fn built this session — see §14**) · revenue reconciliation (**in progress — see §14**) · document repository · revenue MIS · HR lane · de-id→NotebookLM pipeline · supervisor `doctor.py`.

---

## 14. Session 14 additions (28 Jun 2026) — patient lookup + revenue reconciliation

### 14a. VERIFIED CORRECTIONS to earlier assumptions
- **Per-agent `AKEY_` keys are LIVE** (see §8). Accountability is on; not an open item.
- **The dashboard Apps Script project is MULTI-FILE.** `WebApp.gs` references helpers (`last10_`, `hhmmssToSeconds_`, `fetchCallsBetween_`) and a `CFG` config object that live in **other project files** (at least `MyOperator.gs` + a config file). **The handoff `dashboard/` folder is INCOMPLETE** — it only carries `WebApp.gs` + `Dashboard.html`. **Action: export `MyOperator.gs` + the CFG-defining file into the repo** so Git holds the whole project. Until then, treat `WebApp.gs` full-file replacements as safe (they are self-contained and only *reference* the other files) but know the project is bigger.
- **`Patient_Master` live columns (verified from `push_patient_mirror.py`):** `Mobile · Patient Name · Diagnosis · Age · Gender · Last Visit · Patient UID`. The **Diagnosis is the sanitised, taxonomical** one produced by the Follow-Up Tracker (refreshed each ingest) — NOT a raw Docterz `purpose of visit`.
- **Identity column reality (verified, 7,420 rows):** `Clinic_Specific_Id` = **4-digit, 100% filled** (the Clinic ID on the patient file). `Patient_UID` = 10-char opaque alphanumeric (Docterz internal). The mirror currently pushes only **one** of these into the Sheet's `Patient UID` column. **Recommended one-line fix:** add both `Clinic ID` (4-digit) and `UID` as separate `OUT_HEADERS` so Clinic-ID search is exact.

### 14b. "Who is this?" 360 patient lookup — server function BUILT (not yet deployed)
- **`lookupPatient360(key, mode, query)`** appended to `dashboard/WebApp.gs` (new md5 `312de4b3…`). Phone-first, read-only, tier-aware, freshness-stamped. Modes: `mobile` (exact), `clinicid` (exact, tolerant of Clinic-ID-or-UID), `name` (partial → pick-list, cap 25, most-recent-first). Plus helpers `agoFromMs_()` and `pendingByMobile_()` (reads `Followups_Today`).
- **Verified safe:** first 1,411 lines byte-identical to live v17.1 (md5 `42b8762d…`) — pure append, nothing live changed. Passed `node --check`.
- **STILL TODO:** the `Dashboard.html` card UI (3 search boxes + stacked result + one-tap Call), then deploy BOTH files together (edit existing deployment → New version). The server fn is inert until the page calls it.
- **Decisions locked:** Doctor sees financials, Shavez sees clinicals. Mobile-first stacked cards. Card carries a "data as of __" freshness stamp (it's downstream of the nightly mirror — last-night-fresh). Migration-proof (reads Sheet tabs that survive the VPS/SQLite move).

### 14c. REVENUE DATA REALITY (verified from the tracker + real export files)
The tracker's revenue engine (`revenue.py`) and finance web UI **already exist** but are **trapped on the clinic C: drive**. Live Flask routes confirmed in `app.py`: **`/finance`, `/finance/patient`, `/finance/period`, `/finance/lines`, `/lab`, `/lab/add`, `/procedure`, `/concessions`.** The per-patient + period + per-source + lifetime-value views the doctor wants are **already built** — the real task is making them **reachable from the phone** (this is the migration lane).

Revenue sources, by readiness:
| Source | In tracker revenue ledger? | Clinic-ID era |
|---|---|---|
| **Consultation / X-ray / Procedure** | ✅ Auto from Docterz nightly (`Source` = these 3 only; X-ray = Laboratory+Radiology cols, the clinic's Fuji DR) | n/a |
| **Lab (NK Pathology / Labmate)** | ⚠️ Manual `/lab` form, **Source="Lab"**, currently EMPTY in data | suffix **live now** (going forward) |
| **Pharmacy (Marg)** | ❌ NOT revenue — only a *corroboration* signal (MED HERE → match vs Marg upload). `/finance` page literally says "Pharmacy (Marg) not yet connected." | suffix **from 20 Jun 2026** |
| **Sanjeevni** | (separate sale files; relationship to Marg TBC — possibly 2nd pharmacy or different report) | TBC |

**The 20-June feature (owner-engineered):** pharmacy software can't carry a clean join, so the owner embedded **triple-redundant identity** — mobile in its own field + **Clinic ID as a name suffix**. Verified on the Marg 20-Jun file (36 bills): 80% carry a 10-digit mobile, ~52% carry both mobile + 4-digit Clinic ID. **Pathology (Labmate) now prints the Clinic-ID suffix too — but only going forward.**

**Two eras, two match strategies:**
- **From 20 Jun (Marg) / suffix-era (Labmate):** Clinic ID is the **clean primary key**.
- **1 Apr – pre-suffix (all historical):** **no** Clinic ID/mobile → must use **name + bill-date↔visit-date** cross-match against the consultation/visit ledger (the proven fuzzy method).

**Verified name-format mismatch (critical for fuzzy matching):** Labmate names are prefixed + 3-token (`Mr. First Last`); `Patient_Master` names are mostly no-prefix, 1–2 token. ⇒ matcher MUST strip honorifics (`Mr/Mrs/Smt/Sri/Shri/Km/Master/B-o/W-o/S-o/D-o`), lowercase, and match on the **token SET**, not exact string.

**Verified revenue at stake:** the single Labmate file (1 Apr–18 Jun) holds **₹3,50,130** of pathology revenue (clean `Date` + `Net` columns), currently invisible to `/finance`.

### 14d. The revenue reconciler — SPEC LOCKED (next build)
A durable Python reconciler `reconcile_revenue.py` (offline, dry-run first). **North star: map maximum CORRECT revenue from 1 April; never drop a rupee; doubtful rows → per-patient review list; truly unmatchable → `Unclassified` (revenue still counted).**

**Matching ladder (per bill, in order):** (1) Clinic ID → (2) mobile exact → (3) name + bill-date within visit window → (4) name unambiguous → (5) **ambiguous → review list** / **no match → Unclassified**. Every row keeps its rupee value; only *attribution* varies. Never force-assign to the wrong patient.

**Output:** one durable ledger (Source-tagged Pharmacy/Lab/Unclassified, with `Match_Status`, `Match_By`, confidence) that feeds the existing `/finance` views, plus a `revenue_review.csv` of doubtful per-patient candidate lines. Date rule: **bill-date ↔ patient visit-date cross-match**; doubtful → review (owner's call).

**Build order agreed:** fuzzy engine first (covers the 1-Apr historical backlog where the money is), then the clean Clinic-ID engine (Marg 20-Jun-on, suffix-era Labmate). Build & prove on the **Labmate file first** (cleanest: real Date + Net). Source samples are in `revenue_reconciliation/source_samples/`.

### 14e. Migration lane (C: drive → structured homes) — captured
Everything currently lives on the **clinic-PC C: drive** (single point of failure; violates the 3-2-1 rule). Structured migration to-do:
| # | Component | To | Note |
|---|---|---|---|
| M1 | Follow-Up Tracker ("brain") | VPS (rollout step 4) | clinic-PC double-click kept as fallback |
| M2 | WABA send arm | VPS | already BUILT, wire on migration |
| M3 | Call recorder / `pull_recordings` | VPS or Drive archive | recordings auto-archive to Drive |
| M4 | IVR KB kit | structured repo (Git docs / Notion) | knowledge, not code |
| M5 | Clinic salary engine (HR lane) | separate trust class | kept apart from patient data |
| M6 | **SQLite-era mirror widening** | new Sheet tabs (diagnosis/visit/revenue) | the 360° card widens **free** with no UI change |
**SQLite is NOT made redundant by the dashboard:** the Apps Script cockpit always reads the **Sheet**; after migration the VPS+SQLite becomes the *writer* that fills those tabs. The 360° card and join key (Clinic ID + Mobile_Clean) survive untouched.

---


| Version | Date | Change |
|---|---|---|
| 1.0 | 28 Jun 2026 | First Master KB / Systems Register: consolidates 11 sessions + the v16 follow-up loop + v17 incoming-call outcomes. Canonical for all infra/identity/parameters; NotebookLM-ready. |
| 1.1 | 28 Jun 2026 | v17.1 dashboard: incoming **Doctor/urgent** path (surgery/fracture/accident/severe-pain — always-escalate, outcome still captured, instant ntfy push incl. patient number — see §7). Added the staff/clinic document set (runbook, manuals, A4 wall card, companion). "Patient" not "lead" everywhere. |
| 1.2 | 28 Jun 2026 (Session 14) | Added §14: verified corrections (AKEY live; dashboard is multi-file & repo incomplete; Patient_Master columns; identity-shape findings); the **"Who is this?" 360 lookup** server fn `lookupPatient360` built into `WebApp.gs` (card UI still TODO); the **revenue-data reality** (Consultation/X-ray/Procedure live; Lab manual+empty; Marg=corroboration-only, not yet revenue; 20-Jun Clinic-ID-suffix feature; ₹3.5L Labmate revenue invisible to /finance); the **revenue reconciler spec** (two-era matching, Unclassified fallback); the **C-drive→structured migration lane M1–M6**. |

*End. Keep one copy in Notion "Clinic HQ" and one in the handoff kit. Update §5 (tabs), §6 (components), §12 (state) as the system evolves.*
