# Dr. Manoj Agarwal Clinic — Dashboard Capability Map, Requirements & Asset Inventory
**Prepared 26 Jun 2026 · companion to HANDOFF_RUNBOOK v7**
Scope: everything the MyOperator (IVR + WABA) + VPS + Apps Script dashboard + Docterz-CSV stack can be made to do.
Status key: **LIVE** (running now) · **BUILT** (coded/tested, not wired) · **PLANNED** (agreed, not built) · **POSSIBLE** (feasible, not yet scoped).
Context anchors: orthopaedics; older, Hindi-first, semi-urban patients; calls are FREE on the SUV plan; EMR (Docterz) is closed (CSV export only, no webhooks); diagnosis taxonomy tags exist for targeting.

---

## PART 1 — CAPABILITY MAP (what the dashboard can become)

### A. Inbound call handling & callback management
| # | Capability | Status | Needs |
|---|---|---|---|
| A1 | Missed-call → "Needs callback now" worklist | LIVE | — |
| A2 | Resolved/handled callbacks, per-agent "Clinic Team" cards + recording playback | LIVE | — |
| A3 | Auto-clear a callback when ANY agent calls the patient back (shared log) | POSSIBLE | OBD click-to-call + `reference_id` matching |
| A4 | Repeat missed-caller → auto-priority flag (same number, multiple misses) | POSSIBLE | logic over Call_Feed |
| A5 | After-hours call queue → tomorrow-morning callback list | POSSIBLE | time-window logic (after-hours flag already exists) |
| A6 | First-response-time / SLA tracking (miss → callback latency) | POSSIBLE | join inbound miss ↔ outbound callback on number |
| A7 | Known-patient vs unknown-number tagging on every call | POSSIBLE | match Call_Feed ↔ Patient_Master |
| A8 | Channel/source attribution (which IVR keypress / number drove the call) | POSSIBLE | call.* webhook fields / log fields |

### B. Outbound calling (click-to-call via OBD)
| # | Capability | Status | Needs |
|---|---|---|---|
| B1 | Dashboard "Call" button places a logged, recorded IVR call (User Dialer, rings agent's stored mobile, bridges patient) | POSSIBLE | OBD creds (Part 2) |
| B2 | Auto-map agents → user_id via "Get Users" (no manual uuid upkeep) | POSSIBLE | calling key + Get Users |
| B3 | One-tap "Call this patient" from inside a WhatsApp thread | POSSIBLE | B1 done |
| B4 | `reference_id` loop-closing → outbound call returns in logs → list self-clears for everyone (anti-duplicate-calling) | POSSIBLE | B1 + matching |
| B5 | Call-through worklist (tap down a list of pending callbacks) | POSSIBLE | B1 done |
| B6 | Security: calling power lives only on the VPS behind a key; a leaked dashboard file can place NO calls, and User Dialer can only ring registered agents | POSSIBLE (by design) | B1 architecture |

### C. WhatsApp messaging & engagement
| # | Capability | Status | Needs |
|---|---|---|---|
| C1 | Inbound WhatsApp feed + chat-thread view + media (images/PDF/voice) | LIVE | — |
| C2 | Reply to patients from the dashboard (24h window aware) | LIVE | — |
| C3 | Follow-up reminder ladder (due/tomorrow/missed/dropout) | BUILT | wire sender to ledger |
| C4 | Post-visit message + app-install nudge (from day's EMR export) | BUILT (converter) | confirm template names, run |
| C5 | Appointment confirmation / day-before reminder (cut no-shows) | POSSIBLE | template + reminder feed |
| C6 | Dropout detection & re-engagement (overdue follow-ups) | PLANNED | ledger logic |
| C7 | Surgery-estimate follow-up; post-op recovery follow-up | BUILT (templates) | sheets + sender |
| C8 | Operated-patients periodic reach-out | PLANNED | dedicated sheet + template |
| C9 | Diagnosis-tag broadcasts (e.g. knee-OA → PRP/visco info; osteoporosis → bone-density camp; post-fracture → physio) | POSSIBLE | tagged contacts + approved marketing/utility templates |
| C10 | STOP / opt-out auto-handling | POSSIBLE | message.received webhook → opt-out list |
| C11 | Link-click tracking (who tapped app/booking/map link = warm lead) | POSSIBLE | link_tracking webhook + branded short URLs (have) |
| C12 | Template analytics (sent/delivered/read/failed per template) | POSSIBLE | message status webhooks → sheet |
| C13 | Festival / birthday goodwill touch (opt-in, light cadence) | POSSIBLE | DOB from EMR + template |

### D. Patient identification & context
| # | Capability | Status | Needs |
|---|---|---|---|
| D1 | Auto-match inbound call/WhatsApp → name, last visit, last diagnosis, tags shown inline | POSSIBLE | Patient_Master match (mirror exists) |
| D2 | One-view patient timeline (calls + WhatsApp + visits together) | POSSIBLE | join Call_Feed + WA_Inbox + EMR export per number |
| D3 | Family / shared-number handling (IDENTITY: tag) | POSSIBLE | tag logic |
| D4 | "Unknown caller → quick add to contacts" | POSSIBLE | Contacts API |

### E. Analytics / MIS
| # | Capability | Status | Needs |
|---|---|---|---|
| E1 | Daily answer rate / missed rate / callback-completion rate | POSSIBLE | views over Call_Feed |
| E2 | Call volume by hour & weekday → staffing insight | POSSIBLE | Call_Feed timestamps |
| E3 | Campaign funnel: sent → delivered → read → clicked → booked | POSSIBLE | status + link webhooks |
| E4 | Agent performance (calls handled, avg response, recordings) | PARTLY LIVE | extend Clinic Team cards |
| E5 | Enquiry → appointment → visit → surgery funnel, by diagnosis | POSSIBLE | EMR export cross-ref |
| E6 | Accounting cross-check (day report) | LIVE (manual export) | optional auto-ingest |

### F. Operational automation
| # | Capability | Status | Needs |
|---|---|---|---|
| F1 | Nightly EMR export → auto-build follow-up + post-visit worklists | BUILT (converter) | scheduler |
| F2 | Auto-tag patients from diagnosis taxonomy on ingestion | POSSIBLE | taxonomy map (exists) |
| F3 | Call recordings auto-archived to Google Drive | PLANNED | pull_recordings.py + cron |
| F4 | Daily "good-morning" summary to doctor (calls, misses, WA, follow-ups due) | POSSIBLE | summary job → WhatsApp/sheet |
| F5 | Escalation alert: missed call unhandled > N hours | POSSIBLE | watchdog over Call_Feed |

### G. Advanced / future
| # | Capability | Status | Needs |
|---|---|---|---|
| G1 | Voicebot reminders/confirmations (OBD `custom_1/2`) — automated call that speaks a reminder | POSSIBLE | voicebot enablement on plan |
| G2 | IVR keypress → auto-WhatsApp (e.g. press for location → auto-send map link) | POSSIBLE | call webhook + send |
| G3 | Smart callback prioritisation (post-op, elderly, surgery-estimate-pending rank higher) | POSSIBLE | tags + rules |
| G4 | Surgical-estimate Google Sheet folded into the same dashboard | PLANNED | sheet + view |
| G5 | AI-assisted Hinglish reply drafting in the WhatsApp thread (staff edits before send) | POSSIBLE | careful scope (review-request flow stays manual by design) |
| G6 | Call-summary/disposition capture (call.summary webhook) into patient timeline | POSSIBLE | webhook → sheet |

---

## PART 2 — REQUIREMENTS (what unlocks each cluster)

**R1. OBD click-to-call (unlocks B1–B6, A3, A6, B-loop):** three values from the panel —
`public_ivr_id`, `secret_token`, `x-api-key` — plus a VPS `/call` endpoint (same pattern as `/wa-send`) and a one-line dashboard button rewire. Agents auto-resolved via **Get Users**.

**R2. Real-time call events (unlocks A4/A5/A6/A8, E1–E2, F5, G2, G6):** register the **new Calls webhooks**
(`call.initiated/dial_begin/answered/end/summary/disposition`) → point at a VPS receiver (extend the existing one). Gives live call state instead of polled logs.

**R3. WhatsApp status & opt-out (unlocks C10–C12, E3):** register the **WABA webhooks**
(`message.delivered/read/failed/link_tracking`, plus `message.received` already in use) → VPS → sheet/opt-out list.

**R4. Tagged contacts (unlocks C9, D-context, G3):** finish the bulk contact upload (~6,419) with diagnosis tags, after the 2-row merge test. IVR import format is the master.

**R5. Patient context inline (unlocks D1–D2):** matching layer Call_Feed/WA_Inbox ↔ Patient_Master (mirror already syncs nightly).

**R6. Templates (unlocks C-series):** keep approving Meta utility/marketing templates as needed; respect 24h-window rule for free-text and category rules for broadcasts.

**R7. Schedulers (unlocks F-series):** VPS cron for nightly ingest, recordings archive, daily summary, watchdog.

**R8. Analytics views (unlocks E-series):** mostly build-on-existing-data (no new API), just dashboard/sheet views.

**Cross-cutting guardrails:** EMR is closed → anything needing live clinical data is nightly-batch only (no-show/report-ready depend on whichever fields the export carries). Meta rules govern template categories, the 24h free-text window, and opt-outs. Patient base is older/Hindi-first → conservative cadence, honour STOP, never spammy. Secrets stay on the VPS / Script Properties, never in the dashboard file or sheet.

---

## PART 3 — ASSET INVENTORY (what we already hold)

### 3a. MyOperator API surface available to us (from the official Postman collection)
- **WhatsApp:** Send Message; Templates (Create/List/Fetch by id/Fetch by name/Delete); Campaigns (List/Fetch); List Phone Numbers; Upload Media.
- **Contacts:** Create / Create-with-custom-fields / Search / Fetch / Fetch-by-id / Filter-by-phone / Update-by-phone / Update-by-id / Delete.
- **Calling:** Search Logs; Log Filters List; **Get Recording Link**.
- **Outbound (OBD):** **POST Call** at `https://obd-api.myoperator.co/obd-api-v1` — modes: Type 1 User Dialer (`user_id`), Type 1 Anonymous Dialer (`number_2`), Type 2 IVR Dialer.
- **Users:** Get Users (returns agent `user_id`s) / Create / Update.
- **Webhooks (New):** Calls — `call.initiated`, `call.dial_begin`, `call.answered`, `call.end`, `call.summary`, `disposition`; WABA — `message.received/sent/read/delivered/failed`, `message.link_tracking`, `conversation.assign/close`.

### 3b. Keys & secrets we hold (LOCATIONS ONLY — values never written here)
| Credential | Lives at (panel/where) | Used for | Status |
|---|---|---|---|
| WhatsApp "Authentication" Bearer (`lHCx…`) | Panel → APIs & Webhooks → Developer API → WhatsApp APIs; stored in VPS `.env` | Send/list WABA via `publicapi.myoperator.co` | HAVE (live) |
| Calling / Logs token (`3f76…`, 32-char) | Panel → Calling APIs page; stored in Apps Script `MYOP_TOKEN` | Call logs + recording links via `developers.myoperator.co` | HAVE (live) |
| OBD `x-api-key` | Panel → Calling/OBD API area | Header for OBD click-to-call | **NOT YET CAPTURED** |
| OBD `secret_token` | Panel → Calling/OBD API area | Body secret for OBD call | **NOT YET CAPTURED** |
| `public_ivr_id` | Panel (IVR settings / OBD) | Identifies the IVR for OBD calls | **NOT YET CAPTURED** |
| `WA_WEBHOOK_SECRET` | VPS `.env`; in the webhook URL `?key=` | Gate inbound webhook | HAVE |
| `SEND_API_SECRET` | VPS `.env` + Apps Script `SEND_API_SECRET` | Gate the send relay | HAVE |
| Dashboard `SECRET_KEY` (full) / `STAFF_KEY` | Apps Script Script Properties | Dashboard login (full / staff read-only) | HAVE |
| Service-account JSON (`patient-mirror`) | VPS `/root/wa/patient-mirror-key.json` | Sheet read/write | HAVE |

### 3c. Identifiers we hold
Company ID `68384350414b9847` · WABA ID `2101222617483538` · Phone Number ID `1090067637530949` · WABA number `9358008080` · IVR incoming `8065293652` · Sheet id `1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0`. **Missing: `public_ivr_id`** (needed for OBD).

### 3d. Data & infra assets
- Google Sheet hub (tabs: Call_Feed, WA_Inbox, Patient_Master, Daily_Monitor) + live Apps Script dashboard (`/exec`, v12 media + tap-jump).
- VPS (Hostinger, `followup.dr-manoj.in`): receiver (`/wa-webhook`, media-capturing) + send relay (`/wa-send`, v2), Python/Flask/cron capable.
- Patient master ~6,419 with diagnosis taxonomy; Docterz CSV exports (consultation/day report, follow-up logs); patient Android/iOS apps (record view, appointments, handout links).
- Branded short URLs (`dr-manoj.in`: book/map/app/ios/whatsapp/review/contact), QR standee, vCard.
- Panel-native automations LIVE: after-call `new_post_call_message`, missed-call `eng_missedaftercall`.

---

## PART 4 — EXPERT PRIORITY SEQUENCE (suggested)
1. **OBD click-to-call (B1–B6)** — highest leverage now: free calls, IVR-logged, anti-duplicate, hijack-resistant. Gate = 3 OBD values.
2. **`reference_id` loop-closing + auto-clear (A3/B4)** — immediately follows B1; makes the worklist self-maintaining.
3. **First live WhatsApp campaigns (C3/C4)** — the patient-facing payoff; converter already built.
4. **Patient context inline (D1)** — small, high daily value for every agent.
5. **WABA + Calls webhooks (R2/R3)** — unlocks analytics, opt-out, link-tracking, escalation as a batch.
6. **Tagged bulk contacts (R4) → diagnosis broadcasts (C9)** — once merge behaviour is verified.
7. **Automation/analytics (F/E)** and **advanced (G)** as steady follow-ons.

*This document is a living catalogue — add rows as ideas land. Nothing here changes anything live; it is planning only.*
