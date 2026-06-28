# MyOperator Call / Logs + Recordings API — Reference

**Dr. Manoj Agarwal Clinic, Bareilly**
**System:** Call telephony / IVR (NOT WhatsApp — that is a separate API)
**Base host:** `https://developers.myoperator.co`
**Status:** `/search` confirmed live in production (GS poller). `/recordings/link` and `/filters` documented; verify on first call.
**Last reconciled:** 23 June 2026, against the official API PDF + Postman collection + the live GS response shape.

---

## 0. Security — read first

- This is the **Call/Logs token**, NOT the WhatsApp `Bearer` token. They are different keys for different systems.
- Token lives on the panel: **Calling APIs** page. Masked hint begins `3f76…`. Full value stays only in `.env` / Apple Notes.
- **Never** paste the real token into chat, a screenshot, a shared doc, or a committed file. Use the placeholder `<LOGS_TOKEN>` everywhere and inject it from environment at runtime.

---

## 1. Auth model

| | Call/Logs API (this doc) | WhatsApp API (separate) |
|---|---|---|
| Host | `https://developers.myoperator.co` | `https://publicapi.myoperator.co` |
| Auth | `token` parameter (the `3f76…` key) | `Authorization: Bearer` + `X-MYOP-COMPANY-ID` |
| Token source | Panel → Calling APIs | Panel → APIs & Webhooks → Developer API → WhatsApp APIs |

There is **no** `Authorization` header on the Call/Logs API. Authentication is the `token` value.

---

## 2. Endpoint summary

| Purpose | Method | URL |
|---|---|---|
| Search / list call logs | `POST` | `https://developers.myoperator.co/search` |
| List log filter IDs | `GET` | `https://developers.myoperator.co/filters` |
| **Get recording link** | `GET` | `https://developers.myoperator.co/recordings/link` |
| List users | `GET` | `https://developers.myoperator.co/user` |
| Add / update user | `POST` / `PUT` | `https://developers.myoperator.co/user` |

> **Discrepancy note:** the Postman collection prefixes these with an extra `/search/` (e.g. `/search/recordings/link`). That is a collection authoring error. Use the bare paths above — they match the PDF docs and the live, working GS app.

---

## 3. Search Logs — `POST /search`

Returns call records (incoming + outgoing), paginated.

### 3.1 Parameters — sent in a **raw JSON BODY** (not the query string)

> The written docs say "query string." That is **wrong** — the JSON body is what authenticates. This was the cause of an earlier `400 "not an authorized request"`. Confirmed against the live GS app.

| Name | Required | Type | Notes |
|---|---|---|---|
| `token` | Yes | string | The `3f76…` Calling/Logs token. |
| `from` | No | string | Start time, **UTC unix seconds**. |
| `to` | No | string | End time, **UTC unix seconds**. |
| `log_from` | No | string | Pagination offset. Defaults to `0`. |
| `page_size` | No | string | Logs per page. Default `20`, **max `100`**. |
| `search_key` | No | string | Free text: Name, Email, Phone, Comments, Unique id, Caller name. |
| `filters` | No | string | Filter IDs joined with `AND` / `OR` (see §4). |

### 3.2 Request

```
POST https://developers.myoperator.co/search
Content-Type: application/json
```
```json
{
  "token": "<LOGS_TOKEN>",
  "from": "1781568000",
  "to": "1781654399",
  "log_from": "0",
  "page_size": "100"
}
```

### 3.3 Response shape (Elasticsearch-style)

Records live at `data.hits[]`; each call's real fields are under `_source`.

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "total": 6740,
    "hits": [
      {
        "_source": {
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
              "received_by": [
                { "name": "Alisha Khan", "extension": "14" }
              ]
            }
          ]
        }
      }
    ]
  }
}
```

### 3.4 `_source` field dictionary (the ones that matter)

| Field | Meaning |
|---|---|
| `caller_number_raw` | Caller number, no country code (use last 10 digits as the join key). |
| `caller_number` | E.164 form, e.g. `+919837211131`. |
| `start_time` / `end_time` | UTC unix **seconds**. |
| `duration` | Total call as `"HH:MM:SS"` string (includes ring time). |
| `event` | `1` = incoming, `2` = outgoing. |
| `status` | `1` = answered (connected), `2` = missed (no one answered). |
| `filename` | Recording file name. **Populated only when `status == 1`.** Empty `""` for missed. |
| `fileurl` | Panel audio URL (player; may need a logged-in session — prefer §5). |
| `log_details[]` | Per-leg detail: which agent (`received_by[].name`), `action` (`received` / `missed`), leg `duration`, leg `start_time`. |

**Recording rule:** a call has audio only when `status == 1` and `filename` is non-empty. Missed calls (`status == 2`) have `filename: ""` and `fileurl: ""`.

---

## 4. Log Filters — `GET /filters`

Returns the filter IDs to use in `/search`'s `filters` param. IDs can vary per account, so **fetch them; don't hardcode**.

```
GET https://developers.myoperator.co/filters?token=<LOGS_TOKEN>
```

Usage pattern (from the docs):
- Example IDs: incoming = `5`, missed = `13`, call = `8` (verify against your own `/filters` output).
- Same parent → join with `OR` (e.g. incoming OR outgoing).
- Different parent → join with `AND`.
- All incoming missed calls → `filters = "5 AND 13 AND 8"`.

> Note: the live GS app does **not** use `filters` — it pulls every call and classifies in code (more robust than trusting filter IDs). Filters are optional.

---

## 5. Get Recording Link — `GET /recordings/link`  ← the recordings endpoint

Returns a **fresh download link, valid for only 24 hours**, for one recording file.

### 5.1 Parameters — query string

| Name | Required | Type | Notes |
|---|---|---|---|
| `token` | Yes | string | The `3f76…` Calling/Logs token. |
| `file` | Yes | string | The exact `filename` from the log record, e.g. `80f0…-v2.mp3`. |

### 5.2 Request

```
GET https://developers.myoperator.co/recordings/link?token=<LOGS_TOKEN>&file=<FILENAME_FROM_LOG>
```

Example:
```
GET https://developers.myoperator.co/recordings/link?token=<LOGS_TOKEN>&file=80f0d78156f508d518d9070eccf45d0a4041f2448d8fd18968e2d014486e17e973263513b5fd6ab8e843bea00693867f-v2.mp3
```

### 5.3 Behaviour / rules

- The returned link is downloadable but **expires in 24 hours** — fetch the audio immediately, do not store the link for later.
- Recordings themselves persist on MyOperator's cloud indefinitely; only the *link* expires. So there is no data-loss urgency — re-request a fresh link any time within retention.
- Pass the `filename` value (the `.mp3` one), not the `fileurl`.

---

## 6. Standard recipe — import recordings for a day

1. `POST /search` with `from`/`to` for the window, `page_size: "100"`, paginate via `log_from` until a page returns `< 100` rows.
2. For each record where `status == 1` and `filename != ""`:
   a. `GET /recordings/link?token=…&file=<filename>` → read the returned link.
   b. Fetch that link → save the `.mp3`.
   c. Name the file on `caller_number_raw` (last 10) + `start_time` so it joins to the patient record locally.
3. Skip every `status == 2` record — no audio exists.

Because recordings stay on MyOperator's side, this can run on any cadence (the existing 2-hourly poll, or a nightly sweep). The 24-hour expiry only constrains how long a *fetched link* stays valid, not when you must run.

---

## 7. Gotchas (all confirmed)

- **Two different tokens.** Logs/recordings = `3f76…` (this doc). WhatsApp sending = `lHCx…` Bearer. Do not mix.
- **`/search` params go in the JSON body**, not the query string, despite the docs.
- **Ignore the Postman `/search/` prefix.** Real paths are bare: `/search`, `/filters`, `/recordings/link`, `/user`.
- **Only answered calls have recordings.** `status == 2` → no `filename`, no audio.
- **`fileurl` ≠ download link.** It points at the panel app and may need a session. For programmatic download, use `/recordings/link` with the `filename`.
- **Times are UTC unix seconds.** Convert to Asia/Kolkata for display.

---

## 8. Webhooks v2 (alternative to polling — payload not yet captured)

The Postman collection lists real-time call events under `WebHooks(New) / Calls`: `call.initiated`, `call.dial_begin`, `call.answered`, `call.end`, `call.summary`, `disposition`. `call.summary` likely carries the recording reference, but the example payloads are empty in the collection, so the exact field name is **unconfirmed**. If you switch recordings to a webhook trigger, capture one real `call.end` / `call.summary` body first and confirm whether it includes `filename`/`fileurl` before wiring it.

---

*Reference only. No real tokens stored. Companion: live GS project "Clinic Callback Tracker" (already pulls `/search`; currently discards `filename`/`fileurl`).*
