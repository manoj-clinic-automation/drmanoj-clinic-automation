# Dr. Manoj Agarwal Clinic — Master Knowledge Base & Systems Register
**Advanced Orthopaedic Surgery Centre, Bareilly**
Version 1.7 · 30 June 2026 (Session 19 close-out — follow-up auto-push made automatic (folder watcher + Windows Startup); "2001" due-date bug fixed at the push source; unified launcher portal BUILT (not yet deployed); Excel tools inspected; TPA tariff verification brief produced) · Owner: Dr. Manoj Agarwal · Maintained with Claude (per session)

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
| GitHub | `drmanoj-clinic-automation`, branch `main`, local `D:\dr-manoj-git\drmanoj-clinic-automation`. Folders: `dashboard/`, `wa-receiver/`, `wa-send/`, `wa-call/`, `notifier/`, `converter/`, `api/`, `token-rotation/`, `revenue-reconciliation/`, `followups-ingest/`, **`followup-tracker/`** (added Session 18 — 42 files, all core tracker Python) + root `README.md`. **`dashboard/` holds ALL 4 Apps Script files** (`WebApp.gs` v17.1+`lookupPatient360`, `Dashboard.html`, `MyOperator.gs`, `Config.gs`). Committed via GitHub Desktop. No PHI/secrets committed. `.gitignore` hardened Session 18: explicit `data/`, `outputs/`, `Archive/` folder blocks added. |
| Notion | "Clinic HQ" main page `38618b9d-8f91-813e-9773-c20f567fd32f`; Tech & Systems Register `collection://e2e5e030-efc6-41a3-8f8a-70e808aaa5cb`. **Refreshed at Session 14 close-out:** Master KB page → v1.2 (§14 added); HQ Key-Links pointer → v1.2; Tech & Systems Register → Dashboard row (v17.1 + AKEY live, v18 360° note appended) and the old "Marg ERP Revenue Integration" row widened to **"Revenue Reconciliation (Marg + Lab → ledger)"** with the full D11 spec; Active Projects board → 2 new cards: "360° Patient Lookup card — finish & deploy" (Medium), "Revenue Reconciliation" (High) |

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

**OPEN (no urgency):** WhatsApp token rotation (HIGH risk, plan with Lokesh) · self-hosted ntfy + topic bifurcation (rollout step 4, with the D9 shared-fate revisit; keep the supervisor's dead-man's-switch OFF-VPS) · 360° patient query (**spec'd + server fn built — see §14/§16**) · document repository · revenue MIS · HR lane · de-id→NotebookLM pipeline · supervisor `doctor.py`.

**Now LIVE (Session 16):** Revenue Reconciler — `/finance` shows whole-period **₹14,14,380** / 729 patients / 1874 lines; held bills (~₹91,570) queued at `/revenue/review`. Callback Dashboard dropdowns bug fixed; full 11-file Apps Script project captured. WhatsApp inbound images fixed (`wa-receiver.service`).

**Session 17 (housekeeping, no code):** 3-tier carryover model adopted; project-knowledge PHI removed (now 13 clean files); GitHub connected read-only; two-project split decided (this = code/VPS/APIs; sibling = Clinic & Growth). See §17.

**Session 18 (design sprint, no live code):** three specs written (Call Console, Diagnostics & Surveillance, Maintenance & SOP); Follow-Up Tracker core → GitHub (single point of failure eliminated); tracker `data/`+`outputs/` syncing to Drive; full Google Workspace audit (8 Apps Script projects, 4 sheets, financial ops stack discovered). See §18.

**Session 19 (auto-push live + date fix + launcher built):**
- **Follow-up auto-push is now AUTOMATIC.** `push_followups_today.py` is deployed on the clinic PC; a folder watcher (`watch_and_push_followups.py`) detects each new `Staff_Action_Today_*.xlsx` in `outputs/` and pushes it; a `start_followup_watcher.bat` launcher (auto-restart loop) runs from the Windows **Startup** folder, so the watcher starts on every login. No daily command needed; manual fallback remains `python push_followups_today.py --push`. **Day-1 worklist confirmed live on the dashboard (178 follow-ups).** See §19.1.
- **"2001" due-date bug fixed at the source.** The tracker wrote yearless per-row dates (`30-Jun`); the dashboard's `fmtDateCell_` then defaulted the year to 2001. Fixed in `push_followups_today.py` with a defensive `to_full_date()` normaliser that always writes full `DD-Mon-YYYY` (handles real Excel dates, yearless text, full text, and junk; never crashes). 17/17 unit cases + a full reader run against a workbook mimicking the real file all pass. **Delivered for the owner to replace + re-run — preview/push confirmation pending at session close.** Live dashboard untouched (lower-risk fix at the data producer, not the consumer). See §19.2.
- **Unified launcher portal BUILT (not deployed).** Phase-1 doctor-only portal (`portal.py`, Flask, port 8090) at `followup.dr-manoj.in/portal` — 11 tiles (6 live links + 5 manual/held labels, flippable via one config line). PIN + indefinite device-trust cookie (NOT biometric — survives device repair/reset), "forget all devices" button, sealed recovery reference. Remaining: PIN-setup script, systemd unit, reverse-proxy snippet, actual deploy. Staff RBAC = Phase 2. See §19.3.
- **Excel tools inspected** (future rebuilds, not Phase 1): Surgical Estimate, Nutrition/Physio, Ayushman packages KB. Ayushman HTML finder = current working system, **do not modify, link only**.
- **TPA tariff verification brief produced** (`TPA_Verification_Ingestion_Brief_v1_0.md`) — for a separate background chat to visually verify 10 scanned TPA tariff PDFs against a suspect Gemini transcription. See §19.4.
- **PENDING (security):** rotate the service-account key accidentally pasted into chat (see §19.5).

---

## 14. Session 14 additions (28 Jun 2026) — patient lookup + revenue reconciliation

### 14a. VERIFIED CORRECTIONS to earlier assumptions
- **Per-agent `AKEY_` keys are LIVE** (see §8). Accountability is on; not an open item.
- **The dashboard Apps Script project is MULTI-FILE.** `WebApp.gs` references helpers (`last10_`, `hhmmssToSeconds_`, `fetchCallsBetween_`) and a `CFG` config object that live in **other project files** (`MyOperator.gs` + a config file, now `Config.gs`). ~~The handoff `dashboard/` folder is INCOMPLETE — it only carries `WebApp.gs` + `Dashboard.html`.~~ **✅ RESOLVED (Session 14 close-out):** all 4 Apps Script files (`WebApp.gs`, `Dashboard.html`, `MyOperator.gs`, `Config.gs`) are now committed to the repo `dashboard/` folder — Git holds the whole project. `WebApp.gs` full-file replacements remain safe (self-contained; they only *reference* the other files).
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
| 1.3 | 28 Jun 2026 (Session 14 close-out) | GitHub + Notion close-out folded in. **Repo gap CLOSED:** `dashboard/` now holds all 4 Apps Script files (`WebApp.gs`, `Dashboard.html`, `MyOperator.gs`, `Config.gs`); new repo folders `api/ converter/ token-rotation/ revenue-reconciliation/ followups-ingest/` + root `README.md`; 22-file commit pushed to `main` (no PHI/secrets). **Notion refreshed:** Master KB page → v1.2, Tech & Systems Register Dashboard + Revenue-Reconciliation rows updated, 2 new Active-Projects cards (360° card · Revenue Reconciliation). §14a "export MyOperator.gs" action marked resolved. |
| 1.4 | 29 Jun 2026 (Session 16 close-out) | Brings the KB current to Session-16 close. Added **§15** (Session 15 — Revenue Reconciler **Lane B**: external Marg/Labmate Excel ingest, matching ladder, held-bills review) and **§16** (Session 16 — Revenue Reconciler **GO-LIVE** ₹14,14,380 / 729 patients / 1874 lines; Callback Dashboard empty-dropdowns bugfix (`function(e,i)` + New-version publish) + full **11-file** Apps Script project captured; WhatsApp **inbound-images** two-push de-dupe fix in `wa_receiver.py` + `backfill_wa_media.py`). **Cross-surface numbering note:** this file is canonical — Session-16 content is **§16** here; the Notion KB page labels the same content **§15** (a Notion-side label only; relabel §15→§16 on next Notion touch to match this file). |
| 1.6 | 30 Jun 2026 (Session 18 close-out) | Design sprint + infrastructure. Added **§18**: (1) Three new spec docs — Call Console Evolution v1.0, Diagnostics & Surveillance v1.0, Maintenance & SOP v1.0; (2) START_HERE v2 + END_OF_SESSION v2 + Connector Automation Opportunities v1.0; (3) Follow-Up Tracker core code → GitHub (42 files, `.gitignore` hardened, single-point-of-failure eliminated); (4) Tracker `data/` + `outputs/` → Google Drive continuous sync confirmed; (5) Parallel build+diagnostics discipline adopted; (6) Google Workspace full audit — 8 Apps Script projects (all 0% errors), 4 sheets confirmed, undocumented financial ops stack discovered (UPI recon + vehicle tracking + monthly accounting ₹12,57,275 net May 2026); (7) D15–D18 decisions locked. No live code changed. | Key changes: (1) **3-tier carryover model** adopted — CORE docs in project knowledge, code/docs in GitHub+Notion, full zip = cold backup only (stop carrying the big zip per chat); (2) **project-knowledge PHI cleanup** — 8 patient databases removed, down to 13 clean files; (3) **GitHub connected** to the project as read-only knowledge; superseded KB copies purged from repo `docs/` + `wa-call/docs/`; (4) **two-project split** decided — this project = code/VPS/APIs; sibling "Clinic & Growth" = website/GMB/staff/salary; (5) **END_OF_SESSION_PROMPT.md** added (Notion deliberately handled live, not in the prompt); (6) two companion KBs (Biometric Attendance v2, Follow-Up Tracker v2) refined & verified against repo — they live in the Clinic & Growth project. Canonical/API/infra facts UNCHANGED — API Quick-Ref Card and Umbrella unchanged this session. |

*End. Keep one copy in Notion "Clinic HQ" and one in the handoff kit. Update §5 (tabs), §6 (components), §12 (state) as the system evolves.*


---

## 15. SESSION 15 ADDITIONS — Revenue Reconciler (Lane B) [NEW]

**What shipped.** A tracker-native module + admin screen that ingests **external pharmacy (Marg)** and **pathology (Labmate)** revenue Excel files, matches each bill to a patient, and feeds confident matches into `/finance` — holding doubtful/unmatched money for the doctor to approve. Live-installed on the clinic PC; compiles clean.

### 15.1 New files (in the tracker folder)
| File | Role | Git-safe |
|---|---|---|
| `revenue_ingest.py` | Reads Marg/Labmate Excel, matches bills→patients, writes matched→`revenue_ledger.csv`, held→`revenue_pending_review.csv`. Imports the tracker's own `processor` + `revenue` (identical behaviour). | ✅ |
| `app.py` (patched) | Real 1808-line live file + **add-only** patch → 2138 lines. 6 routes + 3 HTML screens + menu link, all `@admin_required`. Byte-preserving on the original. | live file (no secrets) |
| `reconcile_revenue.py` | Standalone CLI version (proving ground, same logic). | ✅ |

### 15.2 Routes (all admin-only)
`GET /revenue/upload` · `POST /revenue/preview` · `POST /revenue/commit` · `GET /revenue/review` · `POST /revenue/promote` · `GET /revenue/lookup`. Home menu link: **📊 Revenue Upload**.

### 15.3 New data files (PHI — local only, never Git)
- `data/revenue_pending_review.csv` — held bills (doubtful/unmatched).
- `data/revenue_source_meta.json` — freshness banner data (amber if >45 days old).
- Matched rows append into existing `data/revenue_ledger.csv` (the 20-col contract from §ledger).

### 15.4 Matching ladder (first hit wins, per bill)
1. Clinic ID exact (4-digit suffix) 2. Mobile exact (10-digit) 3. Name-set + visit within **±3 days**, unique 4. Name unambiguous in master 5. 2+ candidates → **HELD/review** (never auto-pick) 6. No match → **HELD/Unclassified**. Name normaliser strips honorifics → lowercases → order-independent token set. **Invariant in code:** ₹in == ₹matched + ₹held (no rupee dropped).

### 15.5 Proven numbers (sandbox, real samples)
- **Labmate** 200 bills/₹3,50,130 → **matched 148/₹2,58,560**, held 52/₹91,570 (review 17 distinct bills/₹70,010 + unclassified 13/₹21,560).
- **Marg** 32 bills/₹32,822 → matched 23/₹24,794, held 9/₹8,028. (Marg proves the Clinic-ID-suffix discipline → ~100% auto-match.)

### 15.6 Locked decisions (D-series continuation)
- Max correct external revenue from **1 April**; doubtful→review (doctor decides); unmatchable→Unclassified (counted); never force-assign.
- Date window **±3 days** (config constant). Ambiguous name → always review.
- Labmate revenue = **Net** (after discount); carry Gross+Discount.
- **Only MATCHED bills enter the live ledger now**; review+unclassified held separately, enter ledger only after manual **promote** (because `/finance` counts every ledger row regardless of Source).
- Upload/promote = **Admin only**. `app.py` delivered as **add-only patch on the real file**, byte-verified.

### 15.7 Bug found & fixed at session end
`detect_kind()` had `suffix==".xls" → pharmacy` BEFORE the filename check, so a file named `LABMATE_..._.XLS` was misrouted to the Marg reader → 0 rows → preview showed "pharmacy · 0 bills · ₹0".
**Fixed:** filename keywords now win first (LABMATE/patho→lab, MARG/sanjeevni→pharmacy), then content sniff, then extension last. Added `_read_any_excel()` (openpyxl → xlrd → pandas-auto → `read_html`) so true `.xlsx`, true old `.xls`, and `.xls`-named HTML all open. Proven: real filename → `lab`; sandbox flow still exactly ₹2,58,560/52 held (no regression). **Open:** byte-verify the real `.XLS` next session.

### 15.8 Verified file fingerprints (this kit)
- `revenue_ingest.py` md5 `aa59ac198e19f6a59ae54107e1ecc926`
- `app.py` (patched, tested) md5 `5e2fbd41b5af8c972f16b50642eadd3a`

### 15.9 Backlog delta
Lane A (360° patient card in `Dashboard.html`; server fn `lookupPatient360` already in `WebApp.gs` md5 `312de4b3`, undeployed) remains parked. WA token rotation still pending (coordinate Lokesh Kumar VB).

---

# 16. SESSION 16 — 29 June 2026 (Revenue go-live + Callback Dashboard bugfix + full project capture)

## 16.1 Revenue Reconciler — LIVE
The Session-15 `.XLS` detector fix is proven on the REAL Labmate file (`lab · 200 bills · ₹3,50,130`). `/finance` Lab line is populated (was ₹0). Whole-period (1 Apr→29 Jun): **₹14,14,380** / 729 patients / 1874 lines (Consultation ₹6,97,200 · X-ray ₹2,93,850 · Procedure ₹1,51,950 · **Lab ₹2,71,380**). Notion row → Live. `revenue_ingest.py` unchanged (md5 `aa59ac198e19f6a59ae54107e1ecc926`). Held queue at `data/revenue_pending_review.csv`, reviewed at `/revenue/review`. Apr–Jun visit-spine file must stay in `…/followup_tracker/uploads/`.

## 16.2 Callback Dashboard — empty-dropdowns bug FIXED (Incident #1)
**Symptom:** KPI tiles correct, every expandable dropdown empty, no on-screen error.
**Root cause:** `Dashboard.html` pending renderer was `p.map(function(e){` while using `i` inside (`var inId='in_'+esc(...)+'_'+i`). `ReferenceError: i is not defined` thrown inside `Array.map` aborted the ENTIRE client render; KPI tiles survived because they draw first. Sibling renderers were already `function(e,i)` / `function(m,i)`, so only the pending list's bug took everything down.
**Fix:** one char → `p.map(function(e,i){` (line 689). **Then** a separate step: editing the HTML does NOT change what `/exec` serves — must publish a **New version** (Manage deployments → Edit → Version → New version). Both done; live page fully populated, console clean.
**Diagnostic order banked:** `probeApi` (data in?) → `probeDashboardData_` via a plain-named wrapper, because the Run dropdown hides `_`-suffixed functions (server returning it?) → both pass ⇒ render bug ⇒ F12 Console. Triggers irrelevant (live dashboard fetches API per-load).

## 16.3 FULL Apps Script project now captured (major fix)
The handoff kit previously carried only **2** of the project's files (`WebApp.gs` + `Dashboard.html`), which caused hours of half-blind debugging. The kit now carries all **11**: `appsscript.json, config.gs, MyOperator.gs, Netting.gs, Sheets.gs, Main.gs, Monitor.gs, CallField.gs.gs, WebApp.gs, Dashboard.html, Probe.gs.gs`. Two filenames keep doubled `.gs` (`CallField.gs.gs`, `Probe.gs.gs`) to match the live project exactly. New reference docs in `docs/`: `Callback_Dashboard_KB_v1.md` (v1.1), `Callback_Dashboard_TROUBLESHOOTER_v1.md` (v1.1), `Callback_Dashboard_TROUBLESHOOT_LOG.md` (running incident diary).

## 16.4 Architecture rule promoted to canonical
**The live dashboard and the email/Sheet triggers are two independent data paths in one project.** Classify any future problem as dashboard (Path B, live API per-load) vs emails/tabs (Path A, triggers) BEFORE attempting any fix. This is now the first branch in the Troubleshooter.

## 16.5 Backlog delta
Held-bills review (recover from ₹91,570) is the live next-step. 360° patient card (Lane A) still parked — `lookupPatient360` in `WebApp.gs`, undeployed; needs Dashboard.html card UI + New-version deploy. WA token rotation still pending (coordinate Lokesh Kumar VB). Per-agent AKEY_11–16 now LIVE.

## 16.6 WhatsApp inbound IMAGES fix (Session 16, 29 Jun 2026)
**Problem:** incoming photos rendered as placeholder only. **Cause:** MyOperator pushes each image TWICE with the same message id — 1st push `context.link=null` (S3 not ready), 2nd push ~2–7s later carries the real link. `wa_receiver.py` wrote the blank 1st push, remembered its id, then dropped the link-bearing 2nd push as a duplicate.
**Fix:** in `wa_receiver.py`, when a duplicate id arrives whose new push has a media link and the existing row's message cell is blank, UPDATE that cell (helpers `looks_like_media_link`, `update_message_for_id`). True re-deliveries still skipped. Verified live: log shows `appended … 97a58545` then `filled late media link for 97a58545`; image rendered.
**Backfill:** `backfill_wa_media.py` repairs already-missed images from raw logs (`/root/wa/wa_logs/*.jsonl`); idempotent, never overwrites/appends. Run with venv python.
**Canonical operational facts (banked):**
- Inbound receiver service = **`wa-receiver.service`** (gunicorn, 127.0.0.1:8095, runs `wa_receiver.py`). The separate **`wa-notifier.service`** runs `notifier_wa.py` (ntfy). Don't confuse them.
- All VPS python scripts in `/root/wa` must run with **`/root/wa/venv/bin/python3`** (only the venv has gspread/google-auth).
- MyOperator media = two pushes (blank-link then link-filled, same id); any media consumer must allow a later push to fill the link.
- The real `wa_receiver.py` is now in Git/kit `vps_core/` (md5 `9f46279ebc080262102ab13ad200d6a9`), replacing the long-standing 0-byte placeholder.

---

# 17. SESSION 17 — 29 June 2026 (Housekeeping: carryover model + project structure)

> **No code was built or changed this session.** Nothing live was touched. This section records structural/organisational decisions only. All infra, identity, API, and parameter facts elsewhere in this KB are UNCHANGED.

## 17.1 The 3-tier carryover model (now the law)
The old habit of carrying a ~109-file handoff zip into every new chat is retired. Carryover is now three tiers:
- **CORE** — 5 canonical docs live in **project knowledge** and persist across all chats: this KB, the latest Runbook, the Umbrella Architecture, the API Quick-Ref Card, and START_HERE. No per-chat upload.
- **ARCHIVE** — **GitHub** holds code (now connected to the project, read-only & searchable in-chat); **Notion** holds the doc surface.
- **COLD BACKUP** — the full zip, saved to the PC and refreshed only periodically. It is a safety net, not a working file.

To "update" a project-knowledge file there is no in-place edit: delete the old → add the new. After a delete+re-upload, the retrieval index can briefly serve the old copy — start a fresh chat if a stale version appears.

## 17.2 Project-knowledge PHI cleanup
Project knowledge began at 35 files / ~14 MB, ~93% identifiable PHI (8 patient databases including a 9.66 MB Docterz export and a 6,275-patient WABA master). **All 8 PHI databases were removed from the cloud project.** Final project knowledge = **13 files**: the 5 CORE docs + 7 reference files (diagnosis taxonomy, GoDaddy short-URL master, MyOperator upload formats, 2 blank template CSVs, QR-setup doc, WABA utility-templates doc) + `END_OF_SESSION_PROMPT.md`. Principle reaffirmed: **PHI never lives in cloud project knowledge** — patient data stays in the Google Sheet / Drive / local device under access control.

## 17.3 GitHub connected to the project (read-only)
The repo `drmanoj-clinic-automation` is now a project knowledge source — I can READ any repo file in-chat (I cannot write/commit/push). Superseded KB copies were purged from the repo: `docs/Clinic_Master_KB_SystemsRegister_v1.md` + `v1.2.md` and the duplicate copies under `wa-call/docs/`. Repo search now returns only the current KB. **Loop unchanged:** I hand a file as a download → you save to `D:\dr-manoj-git\…` → commit in GitHub Desktop → push → Sync the connector.

## 17.4 Two-project split (decided)
The original single project had outgrown its name. Going forward:
- **This project → `Dr Manoj Clinic — Systems & Automation`** = everything involving code: IVR/WABA/MyOperator, callback dashboard, VPS relays, revenue reconciler, follow-up tracker, attendance, patient spine, physiotherapy pipeline. **GitHub lives here.**
- **Sibling project → `Dr Manoj Clinic — Clinic & Growth`** = non-code: website/GMB/SEO/satellite city pages, staff/salary/HR, vehicle tracking, vCard, QR/Canva, strategy.
- Each project's custom instructions carries a one-line cross-pointer to the other. **Do not over-split** — the automation is legitimately interlinked, so it stays in one project. The HR/salary lane should eventually be its own project (separate trust class for staff financial data).

## 17.5 End-of-session prompt
`END_OF_SESSION_PROMPT.md` now lives in project knowledge — an 8-step close-out (summarise → KB → Runbook → Umbrella → API card → GitHub commit message → project-knowledge swaps → cold-backup zip). **Notion is deliberately NOT in the prompt** — Notion is updated live with Claude during each session, by owner preference.

## 17.6 Companion KBs refined (for the Clinic & Growth project)
Two operational KBs were verified against the GitHub `attendance/` code + Notion and reissued as v2 (all "VERIFY" gaps filled). They describe systems whose code lives in THIS project's repo but whose operational ownership sits with the broader clinic, so the KBs live in the Clinic & Growth project knowledge:
- **Biometric Attendance v2** — standalone Secureye→VPS capture (`attlistener_v2.py`, systemd `attlistener`, port 8041) + engine/dashboard/mailer/watchdog (`att_core/att_dashboard/att_mailer/att_doctor`, dashboard port 8042); 6 watchdog categories; cron 11:30/21:00/14:00; de-dup 790→141; tests 23/23 + 27/27; emergency revert device IP `054.186.015.016`; OPEN: rewire Daily Clinic Reports off the ONtime ABSENT CSV.
- **Follow-Up Tracker v2** — core code is LOCAL only (`C:\followup_tracker_local_test_kit\…`); only integration bridges (`followups-ingest/push_followups_today.py`, `revenue_ingest.py`) are in the repo; `1111111111`=No-Mobile rule; Patient UID = key / Clinic Specific Id = display; MAX_FOLLOWUP_SPAN_DAYS=3 guard; tests 56/2; VPS migration to `followup.dr-manoj.in` pending.

## 17.7 Backlog delta
No backlog item was started. The follow-up tracker was named next target for Session 18: version-control its core code into GitHub (after confirming `.env`, `*.json`, and `data/` are gitignored). **This was completed in Session 18 — see §18.**

---

# 18. SESSION 18 — 30 June 2026 (Design sprint + Follow-Up Tracker to GitHub + Google Workspace audit)

> **No code deployed to live systems this session.** This was a design, infrastructure, and audit session. All live systems untouched. New spec documents written and committed to GitHub. Follow-Up Tracker core code version-controlled for the first time.

## 18.1 Three new specification documents written

All three are now in `docs/` in GitHub and in `06 · Claude Workspace / Generated Documents` in Google Drive.

**Call Console Evolution Spec v1.0** — Full specification for evolving the dashboard (v17.1) into the clinic's primary call console replacing MyOperator dialer + Excel outcome log + Staff Action sheet. Key decisions locked (C1–C10): 30-second polling, visual-only new-call notification, Follow-up write-back to sheet + dashboard hide, WA call button fires OBD, agent badge top-right, pending outcomes tray, number pad in Callbacks section, global dropdown contrast fix, `Outcomes_Log` tab as Excel replacement, "Clinic ID" label everywhere (underlying field unchanged).

**Diagnostics & Surveillance System Spec v1.0** — Complete specification for continuous self-monitoring: dual detection paths (client-side 30s poll + server-side 30min watchdog + 7AM deep check), 5 check categories (API health, sheet integrity, Script Properties, VPS services, data freshness), `System_Health` sheet tab as incident record, three-layer banner (plain description + fallback protocol + fix steps), automatic on-demand diagnostics triggered by fault detection, 15-minute escalation to doctor with pre-packaged context, auto-resolution when fault clears. Full fallback protocol text written for every known fault type.

**Maintenance & SOP System Spec v1.0** — Blueprint for the third Claude project (Maintenance & SOP). To be created after `Diagnostics.gs` is live. Drive folder structure: `Clinic Automation / Specs & Architecture /`, `SOPs /`, `Incident Reports /`, `Code Exports /`, `Handoff Kits /`. Seven SOPs planned (Dashboard, VPS Services, WA Token, Follow-Up Tracker, Revenue Reconciler, Biometric Attendance, MyOperator IVR). Surveillance register covering all live modules.

## 18.2 Supporting documents written

- **START_HERE Prompt v2** — adds session-start health check (read `System_Health` tab before build work), lists three new spec docs as canonical references, lists connected sources
- **END_OF_SESSION Prompt v2** — adds Section B (live connector actions: Drive doc saves, Notion updates, ClickUp backlog sync, Gmail digest draft), Section F (Maintenance project sync once it exists)
- **Connector Automation Opportunities v1.0** — full map of Drive, Gmail, Notion, ClickUp, GitHub, Chrome, Claude Code automation potential; four-tier priority hierarchy; single most impactful immediate action = Drive folder structure
- **Google Workspace Inventory v1.0** — complete audit of all 8 Apps Script projects, 4 linked Google Sheets, Drive structure, Computers sync status, trigger health. See §18.5.

## 18.3 Follow-Up Tracker → GitHub (Backlog Item 1 CLOSED)

**Single point of failure eliminated.** The tracker core code — previously existing only on the clinic PC — is now in GitHub under `followup-tracker/`.

- **Files committed:** 26 Python files (app.py 99KB, processor.py 155KB, revenue.py, seed_diagnosis.py, diagnosis_normalizer.py, build_insight.py, concessions.py, backfill_revenue.py, backfill_call_log.py, send_followups.py, waba.py + 15 more) + 4 bat launchers + 5 txt guides + 2 md docs + `.env.example` + `requirements.txt` = **42 files total**
- **`.gitignore` hardened:** explicit `data/`, `outputs/`, `Archive/`, `data_backup_09_jun/` folder blocks added. `*.json`, `*.csv`, `*.xlsx`, `.env`, `*secret*` all blocked. `patient_mirror_log.txt` excluded (log file with patient mirror run details)
- **Service account JSON** (`sincere-octane-500413-v8-ba8a4836aa68.json`) confirmed blocked by `*.json` rule — never committed
- **PHI confirmed absent** — `data/`, `outputs/`, `uploads/`, `Archive/` all excluded

**Google Drive data sync confirmed:** `followup_tracker/data/` and `followup_tracker/outputs/` now syncing automatically to `drmka.ortho@gmail.com` (5TB, Koo promo until May 2027) via Google Drive desktop client on clinic PC + laptop. Verified in Drive Computers section.

**New files discovered in audit (not in Jun 20 inventory):**
- `push_patient_mirror.py` (24 Jun) — mirrors patient data to Google Sheet
- `run_patient_mirror.bat` (24 Jun) — launcher
- `backfill_call_log.py` (29 Jun) — call log backfill utility
- `test_call_readback.py` (23 Jun) — call readback test
- `test_ivr_reconcile.py` (23 Jun) — IVR reconcile test
- `processor.py` grew 88KB → 155KB between Jun 20 inventory and session

## 18.4 Parallel build+diagnostics discipline adopted

From Session 18 onwards, every new or significantly changed file receives a **failure map comment block** at the top documenting external dependencies, fault codes, and fallback behaviours inline. This means `Diagnostics.gs` Step 3 is ~80% written by the time Steps 1+2 (Call Console build) are complete. Decision locked: build-first-monitor-later is retired.

## 18.5 Google Workspace audit — complete inventory

**8 Apps Script projects, all healthy (0% error rates):**

| Project | Triggers | Status | Notes |
|---|---|---|---|
| Clinic Callback Tracker | 13 | 🟢 LIVE | Primary dashboard. 13 triggers may have duplicates from past setupTriggers — run setupTriggers once to clean. Low urgency. |
| UPI Reconciliation | 1 | 🟢 LIVE | Daily UPI logged vs ICICI settled — 3 entities. 15 open exceptions as of Jun 29. |
| DailyClinicReports ⭐ | 1 | 🟢 LIVE | Track360 vehicle data + ICICI bank statements → Daily Clinic Reports sheet |
| Clinic Accounting Reports | 1 | 🟢 LIVE | Monthly revenue summaries → Monthly Accounting Reports sheet |
| Untitled (Jun 16) | 0 | 🔴 Dormant | Open and identify |
| DailyClinicReports (Jun 7) | 0 | 🔴 Dormant | Old version — confirm superseded then delete |
| Untitled (Jun 7) | 0 | 🔴 Dormant | Open and identify |
| Daily Clinic Reports (Jun 7) | 0 | 🔴 Dormant | Old version — confirm superseded then delete |

**4 Google Sheets confirmed:**

| Sheet | ID | Purpose |
|---|---|---|
| Clinic Callback Tracker | `1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0` | Dashboard spine. Agents (7, all active) + WA_Inbox (live) + all operational tabs. 225KB. |
| Accounting details | `1AnJWDJsAwtgkfFCQNwLzi6lqPPAfGwd-4TUZkuzrZH8` | Staff daily collection log via Google Form. Owner: `drmanojkragarwal@gmail.com` — shared to hub account. |
| Daily Clinic Reports | `1rwxrqAiLh9xBLezZLe7VqBWeCn3FRf_GZqOAEZi-oWc` | Vehicle_Log + ICICI ledgers + UPI_Reconciliation + Open_Exceptions. |
| Monthly Accounting Reports | `13eJo58J7G8n846mGlyv-pHpDILQnCrK-8ZZekyi1Hrg` | Auto-generated monthly summaries. May 2026: ₹12,57,275 net. |

**Undocumented financial operations stack discovered:**
Three live systems (UPI Reconciliation + DailyClinicReports + Clinic Accounting Reports) form a complete daily financial control system — comparing Google Form collections against ICICI bank settlements, tracking vehicle movements, generating monthly department-wise revenue reports. Running since July 2024. Currently undocumented in the KB and not in GitHub. Belongs in Clinic & Growth project knowledge. **Do not rename "Daily Clinic Reports" sheet** — Clinic Accounting Reports finds it by name not ID.

**Critical dependency:** Accounting details sheet owned by `drmanojkragarwal@gmail.com` (personal account) shared to the clinic hub account. If sharing is accidentally revoked, UPI reconciliation breaks.

**WA_Inbox observation:** some outgoing messages stored with bare 10-digit numbers instead of `91XXXXXXXXXX`. Cosmetic inconsistency in the sheet — not a functional issue. Fix in wa-send relay in a future session.

**Drive Computers:** My Computer + My Laptop + My Laptop (1) all syncing. OLD FILES archived.

## 18.6 Storage decision
Google account `drmka.ortho@gmail.com` has **5TB via Koo promo until ~13 May 2027**. This is the data backup home for all clinic data (tracker data/, outputs/, recordings). OneDrive connector not needed. **Reminder: review Google storage plan by 1 April 2027** before the promo expires.

## 18.7 Backlog delta (Session 18)
- **CLOSED:** Follow-Up Tracker → GitHub (Backlog Item 1 from Session 17)
- **NEW — Call Console build (Step 1):** `WebApp.gs` additions (allCallsToday_, getAgentIdentity_, logOutcome_, Outcomes_Log tab writer) — ready to build Session 19
- **NEW — Call Console build (Step 2):** `Dashboard.html` full rebuild — after Step 1
- **NEW — Diagnostics.gs (Step 3):** after Steps 1+2
- **CARRIED:** Follow-Up Tracker VPS migration · Held-bills review · 360° patient card · WhatsApp token rotation (Lokesh) · ntfy self-hosting · Maintenance project creation (after Diagnostics.gs live)
- **NEW AUDIT ITEMS:** Document financial ops stack in Clinic & Growth KB · fix Clinic Accounting Reports to use openById · clean up 4 dormant Apps Script projects · identify Untitled spreadsheet in Drive root · fix outgoing WA phone number format in wa-send relay · run setupTriggers() to clean trigger duplicates
- **DEFERRED — Claude Code VPS connection:** one-time setup waiting for Maintenance project. Guide written: `Claude_Code_VPS_Connection_Setup_v1_0_30Jun2026.md` in Drive + outputs. Steps documented. Key caveat: WinSCP `.ppk` key must be exported as OpenSSH format first.

---

## 19. Session 19 additions (30 June 2026) — auto-push live, date fix, launcher built

### 19.1 Follow-up auto-push made AUTOMATIC (was manual)

**The gap closed.** From day-1 of the follow-up call loop, the dashboard's `Followups_Today` was empty because `push_followups_today.py` lived only in the GitHub `followups-ingest/` folder and had never been deployed to the clinic PC — and even once deployed, nothing ran it automatically. The owner expected the push to be automatic; it was not built.

**Now live, end to end (clinic PC):**
| Piece | File | Role |
|---|---|---|
| Push script | `push_followups_today.py` | Reads newest `Staff_Action_Today_*.xlsx` (read-only) → writes `Followups_Today` + `Followups_Settled` (replace-only; never touches `Followup_Outcomes`). |
| Folder watcher | `watch_and_push_followups.py` | Polls `outputs\` every 5s; on a new/changed workbook (signature = name\|size\|mtime in `watch_pushed.seen`), waits 10s to settle, then calls the push with `--push --file`. Dedup means an already-pushed file stays silent; a genuine regeneration re-pushes. |
| Launcher | `start_followup_watcher.bat` | Auto-restart loop around the watcher. |
| Auto-start | Shortcut in Windows **Startup** folder (`…\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`) — confirmed in place. Watcher starts on every login. |

All four live in `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\`. Folder watcher uses polling (not OS file events) deliberately — Google Drive sync churn would otherwise trigger false events. **Day-1 LIVE push confirmed:** 178 worklist rows / 144 settled written; dashboard showed "TODAY'S FOLLOW-UP CALLS 178" with Call buttons. **Manual fallback** (unchanged): `python push_followups_today.py --push`.

Files are in GitHub under `followups-ingest/` (watcher + launcher + setup note added this session).

### 19.2 The "2001" due-date bug — fixed at the source

**Symptom:** every follow-up showed "Due 30 Jun 2001". **Cause:** the tracker writes the per-row DATE column as **yearless text** (`30-Jun`) — only the sheet's header row carries `Date: 30-Jun-2026`. The dashboard's `fmtDateCell_` helper parses a yearless string and Apps Script's date parser defaults the year to **2001**.

**Decision — fix at the data producer, not the live consumer** (lower risk; the live dashboard is the clinic's primary tool). Added a defensive `to_full_date(raw, default_year=None)` normaliser to `push_followups_today.py` plus a `_MONTHS` map. It always outputs full `DD-Mon-YYYY`:
- real `datetime`/`date` object → formatted directly (year already correct)
- yearless text `30-Jun`, `30/06`, `30-6`, `30 Jun` → current year attached
- full text `30-Jun-2026`, `30/06/2026`, `2026-06-30`, `30 Jun 2026` → parsed + reformatted
- anything unparseable → returned unchanged (never raises); blank stays blank

A `raw_cell()` accessor was added so the date column is read **raw** (not stringified) — otherwise a real date object would be flattened to `2026-06-30 00:00:00` before `to_full_date` ever sees it. Applied to the Call Sheet `Due Date` and the Settled `Due` + `When` columns. **Verified:** 17/17 unit cases pass; a full `read_call_sheet`/`read_settled` run against a workbook built to mirror the real file produced `30-Jun-2026` everywhere; `py_compile` clean; everything else byte-equivalent in behaviour (phone masking, dedup, section detection, empty-sheet stop, replace-only writes). New file md5 `9e4bd2070079dc0d8542738c99aa76f6`. **Delivered to the owner to replace + re-run; preview/push confirmation was still pending at session close.**

> **Note for whoever resumes:** if the owner reports the dashboard still shows 2001 after re-running, confirm they (a) saved the new `push_followups_today.py` over the old one in the tracker folder, (b) ran `--push` (not just preview), and (c) hard-refreshed the dashboard (Ctrl+Shift+R). The fix is at the push; no dashboard change was made.

### 19.3 Unified launcher portal — BUILT, not deployed

**Goal:** unify ~8–9 scattered tools (Apps Script dashboard, attendance, four finance Sheets, revenue reconciler, Ayushman finder, WABA send, surgical estimate, nutrition) behind one phone- and laptop-friendly door. The full multi-staff biometric RBAC portal is a 3–6 month project — **deferred**. **Phase 1 = doctor-only launcher, now.**

- **`portal.py`** — Flask, port **8090** (free), built + `py_compiled` + all 7 auth/render flows tested. Config in `portal_config.py` (VPS-only, chmod 600): `PORTAL_PIN_HASH`, `PIN_SALT`, `TOKEN_SEED`. 11 tiles in an editable `TILES` list — 6 live links (Call Tracker `/exec`, Attendance `:8042`, UPI Reconciliation, Vehicle Tracking, Monthly Accounting, Daily Collections) + 5 manual/held labels (Revenue Reconciler, Ayushman Finder, WABA Send, Surgical Estimate, Nutrition/Physio), each flippable to live by editing one line.
- **Login = medium PIN + indefinite device-trust cookie (NOT biometric).** Rationale: device repair/factory-reset wipes WebAuthn passkeys and would lock the owner out; a PIN survives. Includes salted PIN hash (never plaintext), "forget all devices" button (rotates the server seed to kill a lost/stolen device), sealed recovery reference (Apple Notes).
- **URL:** `followup.dr-manoj.in/portal`.
- **PENDING to go live:** (1) one-time PIN-setup script to create `portal_config.py` on the VPS; (2) systemd unit; (3) OLS reverse-proxy snippet mapping `/portal` → `127.0.0.1:8090`; (4) deploy. Then resume **Call Console Step 1** (per Session 18 sequencing — launcher first, console after).

### 19.4 Excel tools inspected + TPA verification brief

- **Surgical_Estimate_System_v2_1_2.xlsx** — 30 pre-priced procedures (Package_Master), full formula chain, Ayushman SB-code cross-ref, room rates, diabetes add-ons. Sophisticated; faithful web rebuild = a future careful session.
- **Orthopedic_Clinic_Rehab_Nutrition_v11.xlsm** — intake → auto BMI/BMR/body-fat/WHR → condition-driven exercise pathway → multi-comorbidity safety gating (DM/HTN/CKD/gout/thyroid vs supplements + diet), up to 3 stacked conditions, bilingual. Safety-critical; biggest future rebuild.
- **Ayushman_Ortho_Packages_KB.xlsx** — source-of-truth + multi-package billing cascade (highest core 100% / 2nd 50% / rest 25%, implants at full). The live HTML finder lacks this cascade (noted; no action).
- **Ayushman_Ortho_Finder.html** — current working system (80 procedures SB001–SB080, self-contained, mobile-ready). **DO NOT MODIFY — link only.**
- **TPA verification brief** — `TPA_Verification_Ingestion_Brief_v1_0.md` (md5 `236ffe14…`) produced for a **separate background chat** to visually verify 10 scanned TPA tariff PDFs against a suspect Gemini transcription (red flags: IFFCO TOKIO TKR ₹12,000 implausibly low; RELIANCE identical to BAJAJ). Output will be `TPA_Tariff_Master_Verified_v1.json` + a discrepancy log, written to Drive + a Notion Tech Register row. Feeds the future Surgical Estimate rebuild.

### 19.5 PENDING — rotate the leaked service-account key (security hygiene)

During Session 19 the live `sincere-octane-500413-v8-ba8a4836aa68.json` (full private key, key id `ba8a4836da2d2d85a4e04de40b91c486c324`) was accidentally pasted into chat (the owner meant to paste only the path). **Not an emergency** — the key only grants access to the owner's own Sheet, and chat history is private — but correct hygiene is to rotate it. **Action:** Google Cloud Console → project `sincere-octane-500413-v8` → service account `patient-mirror` → Keys → **create new JSON key** → replace the file on the clinic PC (same folder, same filename pattern; the push/mirror scripts auto-find any one service-account `.json`) → **delete the old key id** `ba8a4836…`. (The two `_source_meta.json` files also pasted are NOT secrets — just run stats.)

### 19.6 Backlog delta (Session 19)
- **CLOSED:** Follow-up auto-push automation (push script deployed · folder watcher live · Startup auto-start confirmed). Day-1 worklist live (178).
- **CLOSED (pending owner confirm):** "2001" due-date bug — fix delivered; owner to replace + re-run.
- **NEW — launcher deploy:** PIN-setup script · systemd unit · reverse-proxy `/portal` → :8090 · deploy. Then resume Call Console Step 1.
- **NEW — security:** rotate the leaked service-account key (§19.5).
- **CARRIED:** Call Console Step 1 (`WebApp.gs`) → Step 2 (`Dashboard.html`) → Diagnostics.gs Step 3 · Follow-Up Tracker VPS migration · Held-bills review (₹91,570) · 360° patient card · WhatsApp token rotation (Lokesh) · ntfy self-hosting · Maintenance project creation · the 6 Session-18 audit items (financial-stack doc, openById fix, 4 dormant Apps Script cleanup, Untitled sheet, WA phone format, setupTriggers dedupe) · Claude Code VPS connection · Google storage review (1 Apr 2027) · future rebuilds (Surgical Estimate, Nutrition/Physio web tools; unified costing tool combining Ayushman + Surgical Estimate + TPA).
