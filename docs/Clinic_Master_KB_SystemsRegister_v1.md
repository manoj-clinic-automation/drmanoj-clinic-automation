# Dr. Manoj Agarwal Clinic — Master Knowledge Base & Systems Register
**Advanced Orthopaedic Surgery Centre, Bareilly**
Version 1.0 · 28 June 2026 · Owner: Dr. Manoj Agarwal · Maintained with Claude (per session)

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
| Apps Script | dashboard web app `/exec`, gated `?k=KEY`, **build v17 · inbound** |
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
| **Dashboard** (Apps Script) | `dashboard/WebApp.gs` + `Dashboard.html`, build **v17** | The cockpit (see §7) |
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

## 7. The dashboard (build v17) — what it does

**Cockpit sections:** Awaiting callback · Resolved callbacks · **Today's follow-up calls** (v16) · **Escalations** (v16, doctor-only) · **Settled follow-ups** (v16) · Recent WhatsApp · Handled today · Clinic Team. KPI tiles: Awaiting · Incoming missed · Total calls · WhatsApp (48h) · **Follow-ups due** (v16).

**Access model (server-enforced, never trusted from the page):**
- `DASH_KEY` (master) → `full` (doctor, ext 10): everything incl. Escalations view + WhatsApp reply.
- `AKEY_<ext>` (per-agent) → `staff`: read + log outcomes + place calls; no Escalations view, no reply box.
- Active=`no` in the `Agents` tab off-boards instantly; deleting `AKEY_<ext>` is the hard kill.
- The agent is ALWAYS derived from the login key server-side.

**Click-to-call:** green Call buttons → `triggerCall(key, number, rowId)` → server derives agent from key → POSTs `/call` with secret server-side + agent's `user_id`. The `tel:` link is the manual fallback. Placed calls clear the callback row on next refresh (the dashboard reads call logs).

**Follow-up call loop (v16):** reads `Followups_Today`, overlays today's outcomes (settled rows drop off; "couldn't communicate" stays as retry), grouped by Section→priority. Outcome capture writes to `Followup_Outcomes`; escalating outcomes also persist to `Followup_Escalations`. Doctor-only Escalations view resolves with Completed treatment / Dropped out / Will follow up / Other.

**Incoming-call outcomes (v17):** every "Needs a callback now" row has a **"Log outcome ▾"** disclosure (Option A — hidden until tapped, unfolds one step at a time). Known patient → reason + resolution. Unknown number → identity first (existing-patient-new-number / new-patient / surgery-enquiry / not-a-patient) → the right sub-flow. New-patient enquiries optionally capture "how did they hear?" (channel-of-acquisition). All write to `Followup_Outcomes` (`Source=Incoming` + Identity/Reason/Channel/ForWhom/Clinic ID); clinical reasons auto-escalate. Known callers now show **Clinic ID + last visit** on the row.

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

## 12. State at v17 (28 Jun 2026)
**LIVE:** dashboard v17 (callbacks · click-to-call · per-agent server-bound identity · sheet-driven roster with instant off-boarding · WhatsApp feed/thread/reply · recordings · **follow-up call loop** · **incoming-call outcomes** · escalations · next-day email summary) · VPS relays (receiver, send, click-to-call) · wa-notifier · daily converter · follow-up ingest. WhatsApp public API enabled & working. OBD click-to-call proven end-to-end.

**OPEN (no urgency):** roll out per-agent `AKEY_` keys (until then all calls log as ext 10) · WhatsApp token rotation (HIGH risk, plan with Lokesh) · self-hosted ntfy + topic bifurcation (rollout step 4, with the D9 shared-fate revisit; keep the supervisor's dead-man's-switch OFF-VPS) · 360° patient query · document repository · revenue MIS · HR lane · de-id→NotebookLM pipeline · supervisor `doctor.py`.

---

## 13. Change log
| Version | Date | Change |
|---|---|---|
| 1.0 | 28 Jun 2026 | First Master KB / Systems Register: consolidates 11 sessions + the v16 follow-up loop + v17 incoming-call outcomes. Canonical for all infra/identity/parameters; NotebookLM-ready. |

*End. Keep one copy in Notion "Clinic HQ" and one in the handoff kit. Update §5 (tabs), §6 (components), §12 (state) as the system evolves.*
