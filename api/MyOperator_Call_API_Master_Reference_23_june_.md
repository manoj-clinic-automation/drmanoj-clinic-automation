# MyOperator Call APIs — Master Verified Reference

**Dr. Manoj Agarwal Clinic, Bareilly**
**Scope:** Everything call/IVR-related in one place — Search Logs, Filters, Recording Links, Users, click-to-call (OBD), and the new call webhooks. **WhatsApp sending is a separate system and is intentionally out of scope here** (different host, different token).
**Sources reconciled:** official API PDF + official Postman collection ("MyOperator API Document") + the live, in-production Google Apps Script project (the missed-call digest poller) + your two prior KB notes + **real production `call.end` / `call.summary` bodies captured from OUR OWN account (Session 54, 03 Jul 2026)**.
**Last reconciled:** 03 July 2026 (Session 54 — call-webhook fields verified in production; see §9.0).

> **One-line summary:** The Call/Logs system is hosted at `developers.myoperator.co`, authenticated by a single `token` (the `3f76…`, 32-char Calling/Logs key — *not* the WhatsApp Bearer key). The method that is actually running and confirmed in your GS poller is **`POST /search` with all parameters in the query string and no request body.**

---

## 0. Security — read first

- This document contains **no real tokens**. Only where they live and a masked hint. Full values stay only in `.env` (VPS) and Apple Notes.
- **Two different tokens exist. Do not mix them:**

| Token | Masked hint | Lives on panel at | Used for | Auth mechanism |
|---|---|---|---|---|
| **Calling / Logs token** | `3f76…` (32 chars) | **Calling APIs** page | All endpoints in this document (`developers.myoperator.co/*`) | `token` value (query string) |
| WhatsApp "Authentication" | `lHCx…` | APIs & Webhooks → Developer API → WhatsApp APIs | WhatsApp sending (`publicapi.myoperator.co`) — **separate, not in this doc** | `Authorization: Bearer` |

- A **truncated** Calling/Logs token returns `400 {"status":"error","message":"This not an authorized request","code":400}`. The full value is **32 characters**. Trim stray spaces/newlines on paste.

---

## 1. Account identifiers

| Item | Value |
|---|---|
| Company ID | `68384350414b9847` |
| IVR incoming (published) number | `8065293652` |
| Internal routing DID seen in logs (`_did`) | `+918047947130` |
| Base host (all call APIs) | `https://developers.myoperator.co` |
| OBD (click-to-call) host | `https://obd-api.myoperator.co` |
| Webhook channel | `call` (events POSTed *to* your endpoint) |

---

## 2. Endpoint master table (all call-related)

| # | Purpose | Method | URL | Status |
|---|---|---|---|---|
| 1 | **Search / list call logs** | `POST` | `https://developers.myoperator.co/search` | ✅ Live in GS poller |
| 2 | List log filter IDs | `GET` | `https://developers.myoperator.co/filters` | Documented; verify on first call |
| 3 | **Get recording link (24h)** | `GET` | `https://developers.myoperator.co/recordings/link` | Documented; verify on first call |
| 4 | List users | `GET` | `https://developers.myoperator.co/user` | Documented |
| 5 | Add user | `POST` | `https://developers.myoperator.co/user` | Documented |
| 6 | Update user | `PUT` | `https://developers.myoperator.co/user` | Documented |
| 7 | Click-to-call (OBD) | `POST` | `https://obd-api.myoperator.co/obd-api-v1` | Documented (separate host) |
| 8 | Call webhooks (real-time) | `POST` (inbound to you) | your receiver URL | New webhook suite; see §10 |

> **Ignore the Postman `/search/` prefix.** The collection prefixes paths with an extra `search/` (e.g. `/search/search`, `/search/filters`, `/search/recordings/link`, `/search/user`). That is a collection-authoring quirk. The **real, working paths are bare**: `/search`, `/filters`, `/recordings/link`, `/user` — these match the PDF and the running GS code.

---

## 3. ⭐ Search Logs — the verified working method (as in the GS project)

This is the one you asked for: exactly what the live Apps Script poller does.

### 3.1 The request the GS code actually makes

**`POST` to `/search` with every parameter in the QUERY STRING and an empty body.**

```
POST https://developers.myoperator.co/search?token=<LOGS_TOKEN>&from=<UNIX>&to=<UNIX>&log_from=0&page_size=100
(no request body)
```

The exact construction in `MyOperator.gs` → `fetchCallsBetween_()`:

```javascript
var query = 'token='     + encodeURIComponent(token) +
            '&from='     + encodeURIComponent(String(fromUnix)) +
            '&to='       + encodeURIComponent(String(toUnix)) +
            '&log_from=' + encodeURIComponent(String(offset)) +
            '&page_size='+ encodeURIComponent(String(CFG.PAGE_SIZE));   // 100
var url = CFG.ENDPOINT + '?' + query;                 // ENDPOINT = .../search
var resp = UrlFetchApp.fetch(url, { method: 'post', muteHttpExceptions: true });
// NO payload — the API reads params from the query string above.
```

### 3.2 Parameters

| Name | Required | Type | Notes |
|---|---|---|---|
| `token` | **Yes** | string | The `3f76…` Calling/Logs token (full 32 chars). |
| `from` | No | string | Start time, **UTC unix seconds**. |
| `to` | No | string | End time, **UTC unix seconds**. |
| `log_from` | No | string | Pagination offset. Defaults to `0`. |
| `page_size` | No | string | Logs per page. Default `20`, **max `100`**. |
| `search_key` | No | string | Free text: Name, Email, Phone, Comments, Unique id, Caller name. |
| `filters` | No | string | Filter IDs joined with `AND`/`OR` (see §5). |

> The GS poller deliberately sends **no `filters` / `search_key`** — it pulls every call and classifies in code (more robust than trusting filter IDs).

### 3.3 ⚠️ Query-string vs JSON-body — the one discrepancy to know

Your notes disagree with each other on this point. Resolving it cleanly:

- **The running GS code (3 versions, all identical on this) sends params in the QUERY STRING, POST, no body** — and its header comment says *"Confirmed working."* The official PDF also says query string: *"API token must be provided as part of the query string for all requests."*
- **One of your KB notes (`MyOperator_CallLogs_Recordings_API_Reference.md` §3.1) and a stale comment in `Config.gs` claim the opposite** — that params must go in a *raw JSON body* and that "the docs are wrong." That claim is **contradicted by the code that is actually running in production.**

**Authoritative position:** use the **query-string + POST + no body** method (what the GS poller runs). Treat the "JSON body" note as superseded. If you ever hit a `400 "not an authorized request"` that the token length doesn't explain, run `probeAuthMethods()` (already in the project, §9) — it tries POST/GET × query-only/with-dates and tells you which combination the account accepts, without throwing.

### 3.4 Response shape (Elasticsearch-style)

Records live at `data.hits[]`; each call's real fields are under `_source`. The GS client unwraps `_source` and adds clean derived fields.

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "total": 6740,
    "hits": [
      {
        "user_id": "bcdd743fe1a72faf9689dcbc06f3364d",
        "_source": {
          "company_id": "68384350414b9847",
          "caller_number_raw": "9837211131",
          "caller_number": "+919837211131",
          "start_time": 1781618966,
          "end_time": 1781619032,
          "duration": "00:01:06",
          "event": 1,
          "status": 1,
          "filename": "80f0…-v2.mp3",
          "fileurl": "https://app.myoperator.com/audio/80f0…-v2",
          "department_name": "Appointments",
          "log_details": [
            {
              "_ds": "ANSWER",
              "action": "received",
              "duration": "00:00:43",
              "start_time": 1781618989,
              "received_by": [{ "name": "Alisha Khan", "extension": "14" }]
            }
          ]
        }
      }
    ]
  }
}
```

### 3.5 `_source` field dictionary (the fields that matter)

| Field | Meaning |
|---|---|
| `caller_number_raw` | Caller number, no country code → use **last 10 digits** as the local join key. |
| `caller_number` | E.164 form, e.g. `+919837211131`. |
| `start_time` / `end_time` | UTC unix **seconds**. |
| `duration` | Total call `"HH:MM:SS"` string (**includes ring time**). |
| `event` | `1` = incoming, `2` = outgoing. |
| `status` | `1` = answered (connected), `2` = missed (no one answered). |
| `filename` | Recording file name. **Populated only when `status == 1`.** Empty `""` for missed. |
| `fileurl` | Panel audio URL (player; may need a logged-in session — prefer the link endpoint, §6). |
| `log_details[].received_by[].name` | The **agent** who took the leg (Alisha Khan, etc.) — **not** the caller's name. |
| `log_details[].action` | `received` / `missed`. |
| `log_details[]._ds` | `ANSWER` / `NOANSWER` / `CANCEL`. |

**Recording rule:** a call has audio only when `status == 1` **and** `filename` is non-empty. Missed calls (`status == 2`) carry `filename: ""` and `fileurl: ""`.

**Caller name is never in the call record** — the API only carries the *agent* name in `received_by[]`. The caller's identity is resolved later on the VPS/tracker side (PHI-clean by design).

### 3.6 What the GS client adds (enrichment) — `enrichRecord_()`

After unwrapping `_source`, each record gets these clean derived fields so the rest of the pipeline sees flat data:

| Derived field | How it's computed |
|---|---|
| `phone10` | last 10 digits of `caller_number_raw` / `caller_number` |
| `duration_seconds` | `"HH:MM:SS"` parsed to integer seconds |
| `direction` | `'outgoing'` if `event == 2`, else `'incoming'` |
| `is_missed` | `true` if `status == 2` |
| `_hit_user_id` | the hit's `user_id` (or `allcaller_id`) |

### 3.7 Pagination

Loop with `log_from` += page count, `page_size = 100`, stop when a page returns `< 100` rows. Safety cap `MAX_PAGES = 50`.

---

## 4. Net-missed callback logic (the business rules in `Netting.gs`)

These are the rules the poller applies to turn raw records into the callback list. **Upgraded 19-Jun-2026** to use the accurate `status` signal (supersedes the old "duration < 30s" proxy).

- **Missed candidate:** an **incoming** call that **no one answered** (`status == 2` → `is_missed`). Duration is *not* used to guess misses, because `duration` includes ring time — a genuine short connected call is not a miss, and a long-ringing abandon is.
- **Resolved (dropped from list):** the number had **any connected call** (`status == 1`) that day, in **either direction** — i.e. the patient got through, or the front desk called back and connected. (`CFG.RESOLUTION_MUST_BE_AFTER = false` → a connect resolves anytime that day; set `true` to require it *after* the missed attempt.)
- **Repeat callers** collapse to one row with an attempt count; `attempts >= HIGH_INTENT_ATTEMPTS` (default `3`) flags **priority**.
- **Sort order:** priority first, then most attempts, then most recent.
- **After-hours flag:** call outside `08:00–21:00` local (`WORKDAY_START_HOUR`/`WORKDAY_END_HOUR`).

---

## 5. Log Filters — `GET /filters`

Returns the filter IDs used in `/search`'s `filters` param. **Fetch them; don't hardcode** (IDs can vary per account). The full live list from the Postman collection:

```
GET https://developers.myoperator.co/filters?token=<LOGS_TOKEN>
```

| ID | Name | parent_id | Group |
|---|---|---|---|
| 1 | Source of logs | 0 | *(category header)* |
| 2 | Myoperator IVR | 1 | Source |
| 3 | Mobile | 1 | Source |
| 4 | Event of logs | 0 | *(category header)* |
| **5** | **Incoming** | 4 | Event |
| 6 | Outgoing | 4 | Event |
| 7 | Type of logs | 0 | *(category header)* |
| **8** | **Call** | 7 | Type |
| 9 | SMS | 7 | Type |
| 11 | Status of logs | 0 | *(category header)* |
| 12 | Connected | 11 | Status |
| **13** | **Missed** | 11 | Status |
| 14 | Voicemail | 11 | Status |
| 15 | Tags | 0 | *(category header)* |
| 21 | Call property | 0 | *(category header)* |
| 22 | Noted | 21 | Call property |
| 23 | Archived | 21 | Call property |
| 24 | Star Marked | 21 | Call property |
| 25 | Two word filters | 0 | *(category header)* |

**Rules for combining (`AND` / `OR` only):**
- `parent_id = 0` is a **category header** — never pass it as a filter itself; only use IDs whose `parent_id != 0`.
- **Same parent → join with `OR`** (e.g. Incoming `5` OR Outgoing `6`).
- **Different parent → join with `AND`** (e.g. Mobile `3` AND Incoming `5`).
- Example — *all incoming missed calls*: `filters = "5 AND 13 AND 8"` (Incoming AND Missed AND Call).

> The GS poller does **not** use filters — it pulls everything and classifies in code. Filters are optional and only worth adding if you want the server to pre-narrow large pulls.

---

## 6. Get Recording Link — `GET /recordings/link`

Returns a **fresh download link, valid for only 24 hours**, for one recording file.

```
GET https://developers.myoperator.co/recordings/link?token=<LOGS_TOKEN>&file=<FILENAME_FROM_LOG>
```

| Param | Required | Notes |
|---|---|---|
| `token` | Yes | The `3f76…` Calling/Logs token. |
| `file` | Yes | The exact `filename` from the log record (the `.mp3` value), **not** the `fileurl`. |

Rules:
- The returned link **expires in 24 hours** — fetch the audio immediately; don't store the link for later.
- **Recordings themselves persist on MyOperator's cloud** indefinitely; only the *link* expires. So there's no data-loss urgency — re-request a fresh link any time within retention.
- Pass the log record's `filename` (Search Logs) **or** the webhook's `recording_filename` (§10) — they are the same kind of value.

### Standard recipe — import a day's recordings
1. `POST /search` for the window, `page_size = 100`, paginate via `log_from` until a page returns `< 100`.
2. For each record where `status == 1` and `filename != ""`:
   a. `GET /recordings/link?token=…&file=<filename>` → read the returned link.
   b. Fetch that link → save the `.mp3`.
   c. Name the file on `caller_number_raw` (last 10) + `start_time` so it joins to the patient record locally.
3. Skip every `status == 2` record — no audio exists.

Because recordings stay on MyOperator's side, this can run on any cadence (your 2-hourly poll, or a nightly sweep).

---

## 7. Users API — `GET / POST / PUT /user`

| Action | Method | Key params |
|---|---|---|
| Fetch users | `GET` | `token` (req), `keyword`, `page`, `page-size` (max 100), `_all=1` for everyone |
| Add user | `POST` | `token`, `name`, `contact_number` (no country code), `country_code`, `extension` (11–99, unique) — required; plus `email`, `alternate_contact_number`+`alternate_cc`, `panel_access`, `receive_calls`, `contact_type` (mobile/sip/landline) |
| Update user | `PUT` | `token`, `uuid` (req) + any field above to change |

**User role IDs:** `1` SuperAdmin · `2` Admin · `4` Manager · `8` Basic.
Notes: extension must be a unique integer; contact number must be unique in the company (can be an alternate on another user, triggers a verification); `alternate_cc` is required only when `alternate_contact_number` is set.

---

## 8. Click-to-call (OBD) — `POST https://obd-api.myoperator.co/obd-api-v1`

Outbound dial / voicebot trigger. **Different host and a different auth field** (`secret_token`, not the logs `token`).

```json
{
  "company_id": "68384350414b9847",
  "secret_token": "<SECRET_TOKEN>",
  "type": "2",
  "number": "<customer_number>",
  "public_ivr_id": "<public_ivr_id>",
  "region": "<optional>",
  "std_code": "<optional>",
  "caller_id": "<optional>",
  "reference_id": "<optional custom tracking id>",
  "max_call_duration": "<optional integer seconds>",
  "call_hold": true,
  "custom_1": "value",
  "custom_2": "value"
}
```

Use this only if you ever want programmatic outbound calls / callbacks from code. Not needed for the missed-call digest.

---

## 9. Call Webhooks (New) — real-time alternative to polling

The vendor's new webhook suite POSTs call-lifecycle events **to a receiver URL you host**. All share a standard **envelope + `payload`** structure. Events: `call.initiated` → `call.dial_begin` → `call.answered` → `call.end` → `call.summary`, plus `disposition`.

### 9.0 ⭐ PRODUCTION-VERIFIED on OUR account (Session 54, 03 Jul 2026) — READ FIRST

We captured real `call.end` + `call.summary` bodies from our OWN company (`68384350414b9847`) at a receiver on `/mo-callhook`. The vendor examples below (§9.2–§9.3) are from a **sample** company and an **incoming** call; ours are **outbound OBD**. These account-verified facts override any conflicting assumption elsewhere in this doc:

1. **Join key for OUR OBD calls = `payload.client_ref_id`, NOT `ref_id`.** The value our dialer stamps (`call_api.py` → `make_reference_id`) comes back as **`client_ref_id`**. The webhook's **`ref_id` is MyOperator's OWN UUID** (e.g. `3b4014a4-76cd-11f1-…`) — do **not** match on it. `session_id` (= `payload.id`, shaped like `cb9.<epoch>.<n>`) is a stable backup key.
2. **"Did we reach the patient?" comes from the CUSTOMER LEG, not top-level `duration`.** In `payload.legs[]`, the entry with `type == "customer"` carries `talk_duration` (real seconds talking) and `result`. Top-level `payload.duration` **includes agent-pickup + ring time** — a real call showed top-level `49` while the patient leg talked `32`. **Require `result == "answered"`**: a real incoming call showed `result:"connected"` with `answered_at: null` at `11` talk-seconds, i.e. *reached, not answered*. `"connected"` alone is **not** a genuine pickup.
3. **Tell OBD (outbound) apart from incoming:** OBD → `payload.category == "obd"` **and** a populated `client_ref_id`; incoming → `category == "incoming"` **and** empty `client_ref_id` / `ref_id`. Our receiver ignores anything that isn't OBD.
4. **Full per-account envelope** (fields the vendor sample omitted): top-level `event_id`, `event_version`, `system_identifier`; `payload.did`, `payload.obd_campaign { id, job_id }`; per-leg `dial_status`, `pickup_device`, `answered_at`, `ring_duration`. `recording_filename` is present and complete in `call.end`.
5. **Setup is SELF-SERVE — no vendor ticket, no token rotation.** Panel → **APIs & Webhooks → Webhooks v2 → Add New Webhook** → paste your receiver URL (Authentication: **None** — the `?key=` in the URL is your own gate) → tick **Call Ended** (`call.end`) + **Call Summary** (`call.summary`). This is a **separate** webhook entry from the WhatsApp "Message Received" one and does not disturb it. Both `call.end` and `call.summary` fire per call, in real time.

**Where this is used:** the live duration gate — the VPS `call-hook` receiver writes a PHI-clean `Call_Durations` tab keyed on `client_ref_id`; `CallConsole.gs::getCallDuration` unlocks an outcome only when `status == "bridged"` AND customer `result == "answered"` AND `talk_duration ≥ 15s` (dashboard v18.16). See Master KB v1.23 §54 and Call Console Spec v1.4 §G.

### 9.1 ✅ Recording field — now confirmed

The earlier open question ("does the webhook carry the recording reference, and under what name?") is **resolved**: both `call.end` and `call.summary` carry **`recording_filename`** in `payload`. This is the *same value* you'd pass to `/recordings/link?file=…` (§6).

> **Field-name watch:** Search Logs calls it **`filename`**; the webhook calls it **`recording_filename`**. Same content, different key. Handle both.

### 9.2 `call.summary` — the richest event (best for CRM/analytics)

Final, enriched call log: top-level call fields + full `legs[]` (never empty) + `comments[]` + agent/department metadata.

**Payload schema (key fields):**

| Field | Type | Description |
|---|---|---|
| `id` | string | System call UID (= `session_id`) |
| `category` | string | `incoming`, `oneway`, `callback`, `webcall`, `obd`, `otp` |
| `direction` | string | `incoming` / `outgoing` |
| `customer_number` | string | Customer phone (E.164 in examples) |
| `status` | string | **`bridged`** (connected), **`missed`**, **`voicemail`** |
| `started_at` / `ended_at` | time | ISO-8601 (never blank for `started_at`) |
| `duration` | int | Total seconds |
| `location` | string | "State, Country" (may be empty/approximate) |
| `recording_filename` | string | Recording file name (→ feed to `/recordings/link`) |
| `billable` | bool | |
| `ref_id` / `client_ref_id` | string | OBD reference IDs |
| `obd_campaign` | object | OBD only (`job_id`, `id`) |
| `legs[]` | array | Per-participant detail (below) |
| `comments[]` | array | Comments added during the call |

**Each `legs[]` entry:**

| Field | Type | Description |
|---|---|---|
| `leg_index` | int | Order of the leg |
| `type` | string | `customer` / `agent` |
| `result` | string | `connected` / `answered` / `not_answered` |
| `dial_status` | string | `ANSWER` / `BUSY` / `NOANSWER` / `""` |
| `phone_number` | string | Leg's number |
| `talk_duration` | int/null | Seconds actually talking (null if not answered) |
| `ring_duration` | int/null | Seconds ringing |
| `started_at` / `ended_at` / `answered_at` | time | ISO-8601 (`answered_at` null if unanswered) |
| `pickup_device` | string | e.g. `phone` |
| `agent` | object/null | `{ uuid, name, email, contact, extension }` |
| `department` | object/null | `{ id, name }` |

### 9.3 Example — `call.summary`, incoming bridged call (abridged)

```json
{
  "company_id": "6836cad944e39380",
  "event_type": "call.summary",
  "event_sequence": 1,
  "timestamp": "2026-04-14T05:29:28.838Z",
  "channel": "call",
  "direction": "incoming",
  "session_id": "15.1776144484.2922",
  "customer_identifier": "+919876543210",
  "payload": {
    "id": "15.1776144484.2922",
    "direction": "incoming",
    "customer_number": "+919876543210",
    "status": "bridged",
    "started_at": "2026-04-14T05:28:04+00:00",
    "ended_at": "2026-04-14T05:29:26+00:00",
    "category": "incoming",
    "location": "KO, IN",
    "duration": 82,
    "recording_filename": "7b8aff…-v2.mp3",
    "obd_campaign": null,
    "legs": [
      { "leg_index": 1, "type": "customer", "result": "connected", "talk_duration": 82, "phone_number": "+919876543210" },
      { "leg_index": 2, "type": "agent", "result": "not_answered", "dial_status": "BUSY", "ring_duration": 22,
        "agent": { "name": "Agent1 Name", "extension": "10" } },
      { "leg_index": 3, "type": "agent", "result": "answered", "dial_status": "ANSWER", "talk_duration": 26,
        "answered_at": "2026-04-14T05:28:59+00:00",
        "agent": { "name": "Agent2 Name", "extension": "15" } }
    ],
    "billable": true,
    "comments": []
  }
}
```

### 9.4 `call.end` vs `call.summary`

`call.end` carries the complete call summary (top-level fields + final `legs[]`, also with `recording_filename`). `call.summary` is the **most comprehensive** — adds agent/department metadata per leg and `comments[]`. For CRM/analytics, prefer `call.summary`.

### 9.5 `disposition` webhook

Fires when a disposition is submitted for a call — use it to push call+disposition data into your datastore or to create/update a lead. Single event.

### 9.6 If you switch missed-call detection to webhooks
You'd no longer poll. Map the webhook's modern status to your existing logic: `status == "missed"` (or all agent legs `result == "not_answered"`) = a missed candidate; `status == "bridged"` = resolved. **We DID capture real bodies from our own account (Session 54) — see §9.0 for what they actually showed** (join key `client_ref_id`; the patient answer read from the customer leg's `talk_duration` / `result`; extra per-account fields). Where §9.2–§9.3 (vendor sample + incoming call) differ from §9.0, **trust §9.0.**

---

## 10. Cross-reference: Search Logs vs Webhook (same concepts, different names)

| Concept | Search Logs (`_source`) | Webhook (`payload`) |
|---|---|---|
| Direction | `event` (`1`/`2`) | `direction` (`"incoming"`/`"outgoing"`) |
| Connected vs missed | `status` (`1`/`2`) | `status` (`"bridged"`/`"missed"`/`"voicemail"`) |
| **OUR OBD call id** (join key) | — (not carried) | **`client_ref_id`** ⭐ (our `reference_id`; **`ref_id` = MyOperator's own UUID**, do not use) · backup `session_id`/`id` |
| Caller number | `caller_number` / `caller_number_raw` | `customer_number` / `customer_identifier` |
| Recording file | **`filename`** | **`recording_filename`** |
| Total duration (incl. ring) | `duration` (`"HH:MM:SS"`, incl. ring) | `duration` (int seconds, incl. agent-pickup + ring) |
| **Patient talk time** (real) | — (use `log_details[]`) | **`legs[](type=="customer").talk_duration`** ⭐ + `.result` (`"answered"` = genuine pickup; `"connected"` w/ `answered_at:null` = reached only) |
| Times | unix seconds | ISO-8601 strings |
| Agent | `log_details[].received_by[].name` | `legs[].agent.name` |

> **⭐ = production-verified on our account (Session 54, §9.0).** For the duration gate, match on `client_ref_id` and read the **customer leg's** `talk_duration` + `result` — never the top-level `duration` (which includes the agent leg + ring).

---

## 11. Error → meaning quick reference

| What you see | Meaning |
|---|---|
| `400 {"message":"This not an authorized request"}` | Token wrong or **truncated** (must be full 32 chars), or the param method the account expects differs — run `probeAuthMethods()`. |
| `200 {"status":"success","code":200,"data":{...}}` | Working. Records at `data.hits[]`. |
| `{"status":"error", ...}` with HTTP 200 | App-level error — the GS client throws on this; check `code`/`message`. |
| Non-JSON body | Server/edge error — GS client surfaces the first 300 chars. |
| Empty `filename`/`fileurl` on a record | Call was missed (`status == 2`) — no audio exists. |

---

## 12. The GS project — file roles & the working client

The live missed-call digest project (Apps Script, timezone `Asia/Kolkata`):

| File | Role |
|---|---|
| `Config.gs` | All tunables + `FIELD_MAP`. Token read from Script Property `MYOP_TOKEN` (never in code). **Note:** its header comment says "JSON body" — that comment is stale; the code in `MyOperator.gs` sends query string (see §3.3). |
| `MyOperator.gs` | The Search Logs client: `getToken_`, `fetchCallsBetween_`, `enrichRecord_`, `probeApi`. **This is the source of truth for the working method.** |
| `MyOperator_1.gs` / `MyOperator_2.gs` | Progressive versions of the same client. `_2` is newest: adds a safe token-length diagnostic, `probeAuthMethods()` (method/param probe) and `probeAuthHeaders()` (header probe). Keep **one** copy in the live project to avoid duplicate-function clashes. |
| `Netting.gs` | Net-missed engine: `normalizeCall_`, `computeNetMissed_` and the resolution/priority rules in §4. |

### 12.1 Canonical working client (trimmed to the call that matters)

```javascript
// Token from Script Properties (Project Settings → Script Properties → MYOP_TOKEN)
function getToken_() {
  var raw = PropertiesService.getScriptProperties().getProperty('MYOP_TOKEN');
  if (!raw) throw new Error('Set Script Property MYOP_TOKEN to the FULL 32-char Calling/Logs token.');
  return String(raw).trim();   // defend against a pasted space/newline
}

function hhmmssToSeconds_(v) {
  if (v == null) return 0;
  if (typeof v === 'number') return Math.round(v);
  var p = String(v).split(':');
  if (p.length === 3) return (+p[0])*3600 + (+p[1])*60 + (+p[2]);
  if (p.length === 2) return (+p[0])*60 + (+p[1]);
  var n = Number(v); return isNaN(n) ? 0 : Math.round(n);
}
function last10_(v){ var d=String(v||'').replace(/\D/g,''); return d.length>10?d.slice(-10):d; }

function enrichRecord_(hit) {
  var s = (hit && hit._source) ? hit._source : (hit || {});
  s.duration_seconds = hhmmssToSeconds_(s.duration);
  s.direction = (String(s.event) === '2') ? 'outgoing' : 'incoming'; // event 1=in, 2=out
  s.is_missed = (String(s.status) === '2');                          // status 2 = no answer
  s.phone10   = last10_(s.caller_number_raw || s.caller_number || '');
  return s;
}

// POST to /search with params in the QUERY STRING, no body. Paginated.
function fetchCallsBetween_(startDate, endDate) {
  var token = getToken_();
  var fromUnix = Math.floor(startDate.getTime()/1000);
  var toUnix   = Math.floor(endDate.getTime()/1000);
  var all = [], offset = 0, PAGE = 100, MAX = 50;

  for (var page = 0; page < MAX; page++) {
    var url = 'https://developers.myoperator.co/search'
            + '?token='     + encodeURIComponent(token)
            + '&from='      + fromUnix
            + '&to='        + toUnix
            + '&log_from='  + offset
            + '&page_size=' + PAGE;
    var resp = UrlFetchApp.fetch(url, { method: 'post', muteHttpExceptions: true });
    if (resp.getResponseCode() !== 200)
      throw new Error('HTTP ' + resp.getResponseCode() + ' : ' + resp.getContentText().slice(0,300));
    var json = JSON.parse(resp.getContentText());
    if (String(json.status).toLowerCase() === 'error')
      throw new Error('API error: ' + JSON.stringify(json).slice(0,300));
    var batch = (json.data && json.data.hits) || [];
    for (var i = 0; i < batch.length; i++) all.push(enrichRecord_(batch[i]));
    if (batch.length < PAGE) break;       // last page
    offset += batch.length;
  }
  return all;
}
```

### 12.2 First-run / troubleshooting order
1. `probeApi()` — pulls a 5-record sample, logs field names + the normalized result. Confirms token + shape.
2. If `400 "not an authorized request"` despite a 32-char token: `probeAuthMethods()` (POST/GET × with/without dates), then `probeAuthHeaders()` (company-id / bearer / header-token). Any `HTTP 200 / "status":"success"` line is the combination to lock in. If all four stay `400`, it's an account-side switch → contact support.

---

## 13. Gotchas (all confirmed)

- **Two tokens, never mixed.** Logs/recordings = `3f76…` (this doc, query-string `token`). WhatsApp = `lHCx…` Bearer (separate system).
- **`/search` params go in the query string** (POST, no body) — this is what the live GS poller runs, and what the PDF states. The "JSON body" note in two of your docs is contradicted by the running code.
- **Token must be the full 32 chars.** Truncated → `400 "This not an authorized request"`.
- **Ignore the Postman `/search/` prefix.** Real paths are bare.
- **Only answered calls (`status == 1`) have recordings.** `status == 2` → empty `filename`.
- **`fileurl` ≠ download link.** Use `/recordings/link` with the `filename`.
- **Times in Search Logs are UTC unix seconds; webhooks are ISO-8601.** Convert to Asia/Kolkata for display.
- **Recording field name differs by source:** `filename` (logs) vs `recording_filename` (webhooks).
- **Caller name is never in the call record** — only the agent name is. Resolve patient identity downstream.
- **[Prod, S54] OBD join key is `client_ref_id`, not `ref_id`.** `ref_id` is MyOperator's own UUID; our stamped `reference_id` returns as `client_ref_id`.
- **[Prod, S54] Top-level webhook `duration` includes agent-pickup + ring.** For real patient talk-time use the customer leg's `talk_duration`; for a genuine pickup require `result == "answered"` (not just `"connected"`).
- **[Prod, S54] Call webhooks are self-serve** in Webhooks v2 (Add New Webhook → Call Ended + Call Summary), a separate entry from the WhatsApp webhook — no vendor ticket, no token rotation.

---

*Reference only. No real tokens stored. Companion: live GS project (Search Logs poller) + `MyOperator_WhatsApp_Postman_CallLogs_API_Working_KB_16Jun2026.md` (WhatsApp side).*

## Changelog
- **03 Jul 2026 (Session 54):** Added **§9.0 — production-verified account facts** (join key `client_ref_id`; patient signal from the customer leg's `talk_duration`/`result`; OBD-vs-incoming filter; full per-account envelope; self-serve Webhooks-v2 setup). Corrected §9.6, the §10 cross-reference table, and §13 gotchas to match real captured bodies. Header source list + "Last reconciled" bumped.
- **23 Jun 2026:** Initial master reference (PDF + Postman + live GS poller + prior KB notes).
