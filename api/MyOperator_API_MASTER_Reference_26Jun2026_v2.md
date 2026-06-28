# MyOperator API — MASTER Reference (Exhaustive, Authoritative)

**Dr. Manoj Agarwal Clinic, Bareilly**
**Compiled:** 26 June 2026
**Updated:** 26 June 2026 (session 5) — added the **free-text / session send** (System B), confirmed working on this account.
**Status:** ✅ This file SUPERSEDES every earlier MyOperator API note. Where any older
document disagrees with this one, THIS file wins. It records only methods **proven
working on this specific account**, reconciled against the official API PDF, the
official Postman collection, the live Apps Script dashboard poller, the live
follow-up send layer, and the live inbound receiver (`wa_receiver.py`).

> Earlier docs now demoted to history (do not follow if they conflict):
> `MyOperator_API_Support_Report.md` (the pre-fix "500 / not provisioned" symptom —
> RESOLVED), and any note showing `var_1` variable format, `x-api-key` for WhatsApp,
> or the Postman `/search/recordings/link` prefix. All three were wrong for this account.

---

## 0. THE BIG PICTURE — three independent systems

MyOperator exposes **three** things this clinic uses. They are separate: different
hosts, different tokens, different auth styles. Never mix them.

| System | What it does | Host | Token | Auth style |
|---|---|---|---|---|
| **A — Call/Logs + Recordings** | read call logs, fetch recording links | `developers.myoperator.co` | Calling/Logs `3f76…` (32 ch) | `token` as a parameter (body/query) |
| **B — WhatsApp send** | send template messages out | `publicapi.myoperator.co` | WhatsApp `lHCx…` | `Authorization: Bearer` (capital B) + `X-MYOP-COMPANY-ID` |
| **C — Inbound webhooks** | receive incoming WhatsApp (push) | MyOperator pushes → **your** URL | none on MyOperator side; **your** `?key=` gate | MyOperator POSTs JSON to you |

---

## 0a. Security — read first

- **Two tokens, never mixed:**

| Token | Masked | Length | Panel location | For | Mechanism | Regen risk |
|---|---|---|---|---|---|---|
| Calling / Logs | `3f76…` | 32 ch | **Calling APIs** page | System A | `token` parameter | **LOW** |
| WhatsApp "Authentication" | `lHCx…` | — | APIs & Webhooks → Developer API → **WhatsApp APIs** | System B | `Authorization: Bearer` | **HIGH** |

- **HIGH regen risk (WhatsApp token):** regenerating it breaks the live panel-native
  call automations (`new_post_call_message`, `eng_missedaftercall`) within ~24h.
  There is a ~24h grace window. Plan with MyOperator (Lokesh) before regenerating;
  not needed for normal operation.
- Real tokens live ONLY in: VPS `/root/wa/.env`, the follow-up `.env`, Apps Script
  Script Properties, and Apple Notes. Never in chat, screenshots, shared docs, or git.
- **System C gate** (`WA_WEBHOOK_SECRET`) is a self-chosen URL key, not a MyOperator
  token. If it ever leaks, rotate it (change `.env` + the MyOperator webhook URL).
  It only allows posting fake inbound rows — it exposes no patient data.

---

## 1. Account identifiers

| Item | Value |
|---|---|
| Company ID | `68384350414b9847` |
| WABA ID | `2101222617483538` |
| Phone Number ID | `1090067637530949` |
| WhatsApp (WABA) number | `9358008080` |
| IVR incoming (published) number | `8065293652` |
| Internal routing DID (seen in logs `_did`) | `+918047947130` |
| Call/Logs host | `https://developers.myoperator.co` |
| WhatsApp host | `https://publicapi.myoperator.co` |
| Inbound receiver URL (System C) | `https://followup.dr-manoj.in/wa-webhook?key=<WA_WEBHOOK_SECRET>` |

---

# SYSTEM A — Call / Logs + Recordings  (`developers.myoperator.co`)

Authenticated by the **Calling/Logs token** (`3f76…`). **No `Authorization` header** —
the token is a parameter.

## A1. Endpoints

| Purpose | Method | URL | Status |
|---|---|---|---|
| Search / list call logs | `POST` | `/search` | ✅ Live (dashboard poller) |
| Get recording link (24h) | `GET` | `/recordings/link` | ✅ Confirmed |
| List log filter IDs | `GET` | `/filters` | Documented |
| List users | `GET` | `/user` | Documented |

> **Use the BARE paths.** Ignore the Postman `/search/` prefix (e.g.
> `/search/recordings/link`) — that is a collection-authoring error and 404s here.

## A2. Search logs — `POST /search`  ✅ proven

On THIS account the parameters go in a **raw JSON BODY** (query-string is a fallback only).

```
POST https://developers.myoperator.co/search
Content-Type: application/json
```
```json
{ "token": "<LOGS_TOKEN>", "from": "1781568000", "to": "1781654399",
  "log_from": "0", "page_size": "100" }
```

| Param | Req | Type | Notes |
|---|---|---|---|
| `token` | Yes | string | Calling/Logs token (full 32 chars). |
| `from` / `to` | No | string | Window, **UTC unix seconds**. |
| `log_from` | No | string | Pagination offset (default `0`). |
| `page_size` | No | string | Per page (default `20`, **max `100`**). |
| `search_key` | No | string | Free text (name/email/phone/comments/uid). |
| `filters` | No | string | Filter IDs joined `AND`/`OR` (poller does NOT use; classifies in code). |

**Response (Elasticsearch-style):** records at `data.hits[]`, real fields under `_source`.

### `_source` field dictionary
| Field | Meaning |
|---|---|
| `caller_number_raw` | Caller number, no country code (**last 10 digits** = patient join key). |
| `caller_number` | E.164, e.g. `+919837211131`. |
| `start_time` / `end_time` | **UTC unix seconds** (convert to Asia/Kolkata to display). |
| `duration` | Total call `"HH:MM:SS"` (includes ring time). |
| `event` | `1` = incoming, `2` = outgoing. |
| `status` | `1` = answered, `2` = missed. |
| `filename` | Recording file name. **Only present when `status==1`.** |
| `fileurl` | Panel **player page** (needs a logged-in session). Do NOT use to download — use A3. |
| `log_details[]` | Per-leg: `received_by[].name` (agent), `action`, leg `duration`, leg `start_time`. |

**Recording rule:** audio exists only when `status==1` AND `filename != ""`.
Missed (`status==2`) → no `filename`, no audio.

## A3. Get recording link — `GET /recordings/link`  ✅ confirmed

```
GET https://developers.myoperator.co/recordings/link?token=<LOGS_TOKEN>&file=<FILENAME_FROM_LOG>
```
- `file` = the exact `filename` from the log (`…-v2.mp3`), **not** `fileurl`.
- Returned link is valid **24h** — fetch the audio immediately, don't store the link.
- Recordings persist on MyOperator indefinitely; only the *link* expires → re-request anytime.

## A4. Recipe — import a day's recordings
1. `POST /search` (JSON body), `page_size:"100"`, paginate `log_from` until a page < 100.
2. For each record with `status==1` and `filename!=""`:
   a. `GET /recordings/link?...&file=<filename>` → read returned link.
   b. Fetch link → save `.mp3` (name by `caller_number_raw` last-10 + `start_time`).
3. Skip every `status==2`.

## A5. Filters / Users (optional, not used by dashboard)
`GET /filters?token=…` → per-account filter IDs (fetch, don't hardcode).
`GET /user?token=…&_all=1` → users; roles 1=SuperAdmin 2=Admin 4=Manager 8=Basic.

---

# SYSTEM B — WhatsApp send  (`publicapi.myoperator.co`)

Authenticated by the **WhatsApp token** (`lHCx…`) as a **Bearer** header.
✅ Confirmed working (16 June engineer call + clinic PC + live follow-up sends).

## B1. Authentication (both headers required)
| Header | Value | Notes |
|---|---|---|
| `Authorization` | `Bearer <WA_TOKEN>` | **Capital `Bearer`.** Lowercase `bearer` → AWS "explicit deny". |
| `X-MYOP-COMPANY-ID` | `68384350414b9847` | Always sent. |
| `Content-Type` | `application/json` | For POST. |
| `Accept` | `application/json` | |

## B2. Endpoints
| Method | Path | Use |
|---|---|---|
| `POST` | `/chat/messages` | Send a template message |
| `GET` | `/chat/templates?waba_id=<id>&waba_template_status=approved` | List approved templates |
| `GET` | `/chat/phonenumbers?...&waba_id=<id>` | List phone numbers |

## B3. Send a template — `POST /chat/messages`  ✅ working body
```json
{
  "phone_number_id": "1090067637530949",
  "customer_country_code": "91",
  "customer_number": "9837114044",
  "data": {
    "type": "template",
    "context": {
      "template_name": "drmanoj_followup_due",
      "language": "en",
      "body": { "1": "John Doe", "2": "12" }
    }
  },
  "reply_to": null,
  "myop_ref_id": null
}
```
- **Variable format = numeric STRING keys** `"1"`, `"2"`, `"3"` inside `body`.
  **Not** `var_1`, not a list. (`WABA_TEMPLATE_BODY_FORMAT = numeric`.)
- `language = "en"`.

## B3b. Send a FREE-TEXT (session) message — `POST /chat/messages`  ✅ confirmed 26 Jun (session 5)

Same endpoint, same auth as B3. The ONLY difference is the `data` block: `type` is
`"text"` and `context` carries a plain `body` (no template name, no variables).

```json
{
  "phone_number_id": "1090067637530949",
  "customer_country_code": "91",
  "customer_number": "9837114044",
  "data": {
    "type": "text",
    "context": { "body": "Namaskar, yeh ek reply hai.", "preview_url": false }
  },
  "reply_to": null,
  "myop_ref_id": null
}
```

- Source: MyOperator's own Postman collection (`Whatsapp Business APIs → Send Message`),
  then **proven live on this account** (HTTP 200 / `status:success` / `Accepted`, real
  WhatsApp delivered). **Lokesh not required for the format.**
- `preview_url`: `false` unless you want WhatsApp to render a link preview.
- `reply_to`: optional `message_id` to quote/thread onto a specific inbound message.
- Success response shape is identical to B4 (`conversation_id` + `message_id`).

### ⚠️ The 24-HOUR SESSION WINDOW (a WhatsApp/Meta rule, not a MyOperator quirk)
A free-text (`type:text`) message only **delivers** if the customer messaged the clinic
within the **last 24 hours**. Outside that window WhatsApp allows **only approved
templates** (which is why the follow-up ladder uses templates). The API will still
*accept* an out-of-window text in some cases, but it will not be delivered — so callers
must check the window first.

**How we respect it:** the live inbound receiver writes every incoming message to
**WA_Inbox** with an IST timestamp. The sender module `wa_send.py` reads WA_Inbox,
finds the number's most recent **incoming** message, and only sends free text if it was
≤24h ago; otherwise it refuses and tells the operator to use a template. This guard is
what makes free-text safe to put behind a dashboard button.

## B4. Success response + webhook join key
```json
{ "status":"success","code":"200","message":"Accepted",
  "data": { "conversation_id":"…", "message_id":"…" } }
```
- `conversation_id` = stable per recipient (one thread per number).
- `message_id` = unique per message.
- For API-sent messages `myop_ref_id` returns `null` → **join delivery/read/failed/STOP
  webhooks on `message_id`** (parse both `conversation_id` and the misspelled
  `conversaton_id` if present).

## B5. Approved templates (panel)
| Name | Vars | Role |
|---|---|---|
| `drmanoj_post_visit` | {{1}} | post-visit (same day) |
| `drmanoj_followup_tomorrow` | {{1}},{{2}} | due tomorrow |
| `drmanoj_followup_due` | {{1}},{{2}} | due today / grace 0–3d |
| `drmanoj_followup_missed` | {{1}},{{2}} | missed 4–10d |
| `drmanoj_followup_dropout` | {{1}},{{2}},{{3}} | dropout >10d |
| `new_post_call_message` | — | after-call — **panel-native, NOT via API** |
| `eng_missedaftercall` | — | missed-call — **panel-native, NOT via API** |

---

# SYSTEM C — Inbound webhooks (Webhooks v2)  ✅ LIVE 26 Jun 2026

MyOperator **pushes** each incoming WhatsApp message to a URL you own. There is no
"fetch past messages" API — inbound only arrives by push, so a receiver is required.

## C1. Panel setup (one-time, DONE)
- Panel → **APIs & Webhooks → Webhooks v2 → Add New Webhook**.
- **Webhook URL:** `https://followup.dr-manoj.in/wa-webhook?key=<WA_WEBHOOK_SECRET>`
- **Authentication:** None (our security is the `?key=` in the URL).
- **Method:** POST, HTTPS only (panel enforces this).
- **Events:** WhatsApp events → tick **Message Received** ONLY. (Leave Sent / Delivered /
  Read / Failed / Track-URL / Conversation events unticked — they would flood the sheet.)
- Current state: ONE active entry (Message Received). The old `webhook.site/…` entry is
  Inactive (can be deleted).

## C2. Confirmed inbound payload (from the live test) — AUTHORITATIVE
A real "Message Received" push looks like this (field names verified against the row it produced):
```json
{
  "event_type": "message.received",
  "timestamp": "2026-06-26T02:10:56.956814767Z",
  "customer_identifier": "919837114044",
  "direction": "incoming",
  "session_id": "dd60b513-711d-…",
  "payload": {
    "id": "9fcb92ab-1469-…",
    "status": "received",
    "data": {
      "type": "text",
      "context": { "body": "Test 1" }
    }
  }
}
```

## C3. Field map → WA_Inbox columns (what the receiver writes)
| WA_Inbox column | Source path in payload | Notes |
|---|---|---|
| Timestamp | `timestamp` | **UTC, ISO-8601, may carry NANOseconds + `Z`** → convert to IST (see C5). |
| Phone | `customer_identifier` | CC+10 digits; receiver strips to digits only. |
| Direction | `direction` | `incoming`. |
| Type | `payload.data.type` | e.g. `text`. |
| Message | `payload.data.context.body` | the message text. |
| Message ID | `payload.id` | unique; also the **de-dupe key**. |
| Conversation ID | `session_id` | stable per patient thread (same value family as B4 `conversation_id`). |
| Status | `payload.status` | `received`. |

The receiver also tries several fallback paths per field (defensive), but the paths
above are the ones confirmed live. Only inbound messages are written: it requires
direction not "out" AND (event mentions "received" OR a body exists OR a real type) —
delivery/read/status pushes are ignored even if the panel were mis-ticked.

## C4. Receiver behaviour (the contract)
- `GET /` → `wa_receiver alive` (health check).
- `POST /wa-webhook?key=…` → validates the key, logs the raw push to
  `/root/wa/wa_logs/<YYYY-MM-DD>.jsonl`, de-dupes on `payload.id`, appends one row to
  the **WA_Inbox** tab in the tab's existing column order.
- Always returns `200` quickly (so MyOperator doesn't retry-storm), even on a duplicate.

## C5. ⚠️ TIMESTAMP GOTCHA (fixed 26 Jun) — keep this fix
- MyOperator's `timestamp` can be **nanosecond** precision with a `Z`, e.g.
  `2026-06-26T02:10:56.956814767Z` (9 fractional digits).
- **Python 3.9's `datetime.fromisoformat()` rejects 7–9 fractional digits** (it accepts
  only 3 or 6). The old code's safety net then stored the raw UTC string → the sheet
  showed UTC with a `Z`, 5h30 behind IST.
- **Fix (in the shipped `wa_receiver.py`):** before parsing, replace `Z`→`+00:00` and
  trim fractional seconds to ≤6 digits, then `fromisoformat`, then `.astimezone(IST)`.
  Verified: `…56.956814767Z` → `2026-06-26T07:40:56+05:30`. Also handles unix seconds,
  unix millis, and already-IST strings.

---

## 9. Error → meaning quick reference
| What you saw | System | Meaning / fix |
|---|---|---|
| `400 "...not an authorized request"` | A | Truncated token (need 32 ch) OR params in wrong place — use **JSON body** for `/search`. |
| `404` on recording link | A | You used the `/search/recordings/link` prefix — use the **bare** `/recordings/link`. |
| `500 {"message":null}` on Bearer | B | API not provisioned (old pre-16-June symptom — now fixed). |
| `401 {"message":"Unauthorized"}` on `x-api-key` | B | Wrong scheme — wants `Authorization: Bearer`, not `x-api-key`. |
| `403` / "explicit deny" | B | Lowercase `bearer` (must be capital) or not provisioned. |
| `200 OK status:success Accepted` | B | Working — a real WhatsApp went out. |
| `500` on the public site after a rewrite | C | OpenLiteSpeed rejects Apache `[P]` flag in the rewrite box — use the **extprocessor + context proxy** in vHost Conf instead (see runbook). |
| sheet timestamp shows `…Z` (UTC) | C | The nanosecond/Py-3.9 bug — ensure the C5 fix is in `wa_receiver.py`. |

---

## 10. One-screen cheat sheet
```
A  CALL/LOGS (developers.myoperator.co)  token=3f76… (32ch)  NO Authorization header
   POST /search        JSON body { token, from, to (UTC unix s), log_from, page_size:"100" }
   GET  /recordings/link   ?token=…&file=<filename .mp3>     (link 24h)
   audio only when status==1 && filename!="";  event 1=in 2=out;  status 1=ans 2=miss
   bare paths only (ignore Postman /search/ prefix)

B  WHATSAPP SEND (publicapi.myoperator.co)  token=lHCx…  (HIGH regen risk)
   POST /chat/messages  Authorization: Bearer <token> (CAPITAL B) + X-MYOP-COMPANY-ID
   TEMPLATE : data.type "template"; body vars = numeric string keys "1","2"; language "en"
   FREE TEXT: data.type "text"; context {body, preview_url:false}  ← only inside 24h window
              (patient must have messaged in last 24h; else template only)
              wa_send.py enforces this by reading WA_Inbox before sending
   reply: status success / Accepted; join future webhooks on data.message_id

C  INBOUND (MyOperator pushes to you)   gate = ?key=<WA_WEBHOOK_SECRET>
   Webhooks v2 → Message Received → https://followup.dr-manoj.in/wa-webhook?key=…
   timestamp is UTC (maybe nanoseconds+Z) → convert to IST (trim frac to 6 digits on Py3.9)
   de-dupe on payload.id;  phone=customer_identifier;  body=payload.data.context.body
```

*No real tokens in this document. This MASTER supersedes: the 25-Jun consolidated ref,
the 23-Jun call master, the CallLogs/Recordings ref, the 16-Jun working KB, and the
13-Jun support report. Keep the official `MyOperator_API.pdf` and the Postman
collection as raw vendor sources.*
