# MyOperator API — Working Configuration & Knowledge Base

**Dr. Manoj Agarwal Clinic, Bareilly**
**Source:** Live troubleshooting call with MyOperator engineer, 16 June 2026
**Status:** ✅ RESOLVED — WhatsApp public API now working and permanently enabled

> Purpose: single reference for everything confirmed on the 16 June call. Covers the WhatsApp Business API (sending), the Postman setup it was tested in, and the separate Call/Logs API. Drop the WhatsApp + Postman sections into the Follow-Up Tracker thread; the Call/Logs section belongs with the IVR work.

---

## 0. Security note — read first

- **No real tokens are written in this document.** Only where they live and a short masked hint. The full values stay only in your `.env` (VPS) and Apple Notes.
- The WhatsApp Authentication token was **visible on screen throughout this session** → it should be regenerated later, carefully (see §6).
- Never paste any token into a chat, screenshot, WhatsApp group, or shared document.

---

## 1. Headline outcome

- The WhatsApp public API (`publicapi.myoperator.co`) now **works** and is **permanently enabled and included in the plan** (vendor confirmed it was a **provisioning/setup issue on their side**, now fixed).
- Sending was confirmed **twice in the engineer's Postman** and then **from the clinic PC** — all `200 OK / Accepted`.
- There were **two separate problems**, fixed separately:
  1. **Account side:** the public API was not provisioned → fixed by the MyOperator engineer during the call.
  2. **Local side:** the word `bearer` was lowercase in the local script → must be capital **`Bearer`**.

---

## 2. Account identifiers

| Item | Value |
|---|---|
| Company ID | `68384350414b9847` |
| WABA ID | `2101222617483538` |
| Phone Number ID | `1090067637530949` |
| WhatsApp (WABA) number | `9358008080` |
| IVR incoming number | `8065293652` |
| Base URL (WhatsApp API) | `https://publicapi.myoperator.co` |

---

## 3. WhatsApp Business API — `publicapi.myoperator.co`

### 3.1 Authentication (the two must-haves)

| Header | Value | Notes |
|---|---|---|
| `Authorization` | `Bearer <token>` | **Capital `Bearer` is required.** Lowercase `bearer` caused an "explicit deny" rejection. |
| `X-MYOP-COMPANY-ID` | `68384350414b9847` | Always sent alongside. |
| `Content-Type` | `application/json` | For POST. |
| `Accept` | `application/json` | |

- **Token used:** the **"Authentication"** value from panel → **APIs & Webhooks → Developer API → WhatsApp APIs**.
- **Masked hint:** begins `lHCx…` (full value redacted — kept in `.env` / Apple Notes only).
- This is **NOT** the same as the Calling/Logs token (see §5) — that is a different key for a different system.

### 3.2 Endpoints

| Method | Path | Use |
|---|---|---|
| `POST` | `/chat/messages` | Send a template message |
| `GET` | `/chat/templates?waba_id=<id>&waba_template_status=approved` | List approved templates |
| `GET` | `/chat/phonenumbers?...&waba_id=<id>` | List phone numbers |

### 3.3 Working send request (confirmed `200 OK`)

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
      "body": {
        "1": "John Doe",
        "2": "12"
      }
    }
  },
  "reply_to": null,
  "myop_ref_id": null
}
```

### 3.4 Variable format (confirmed working)

- Template variables are sent as **numeric string keys**: `"1"`, `"2"`, `"3"` … inside `body`.
- **Not** `var_1`, not a list. (This is the value to set as `WABA_TEMPLATE_BODY_FORMAT = numeric` in the tracker.)
- `language` = `"en"`.

### 3.5 Success response shape

```json
{
  "status": "success",
  "code": "200",
  "message": "Accepted",
  "data": {
    "conversation_id": "dd60b513-711d-4d93-996a-8ffecb8b24f2",
    "message_id": "6d7b237a-08c3-4902-9cdb-d6bd9c2071bc"
  }
}
```

- `conversation_id` stays the **same per recipient** (one thread per number).
- `message_id` is **unique per message**.
- **Webhook join key:** for API-sent messages, `myop_ref_id` comes back `null`, so delivery/read/failed/STOP webhooks must be matched on **`message_id`** (parse both `conversation_id` and the misspelled `conversaton_id` if present).

---

## 4. Postman reference (how it was tested)

- **Collection:** MyOperator's official **"MyOperator API Document"** (the engineer drove this from the workspace `public-apis · Prasanna`).
- **Path inside the collection:** `Whatsapp Business APIs → Send Message (POST)`.
  - Other items present: `Templates` (Create / List / Fetch by ID / Fetch by Name / Delete), `Campaigns`, `List Phone Numbers`, `Upload Media`, `Whatsapp Webhook Responses`, `Contact APIs`, `WebHooks (New / Deprecated)`, `OBD APIs`, `User APIs`.
- **Request setup:** method `POST`, URL `https://publicapi.myoperator.co/chat/messages`, **Body = raw / JSON**, ~13 headers (Authorization Bearer + X-MYOP-COMPANY-ID + Content-Type + Accept).
- **Code snippet:** Postman's **"Python – http.client"** generator produced the exact `test_send.py` script used on the clinic PC. (To regenerate it for any request: open the request → `</>` Code snippet → choose **Python – http.client**.)

---

## 5. Call / Logs API — `developers.myoperator.co` (SEPARATE system)

> This is a **different API** from WhatsApp. It is for **phone-call / IVR logs**, not for sending WhatsApp messages. Not needed for the follow-up messaging. Useful later for IVR work (e.g. missed-call detection / callbacks).

- **Live docs / testing page:** `https://signup.myoperator.com/api/`
- **Endpoint (Logs — "Access or search logs"):** `POST https://developers.myoperator.co/search`
- **Purpose:** get the list of your call logs; query, search & filter.
- **Token:** a **different** token — the "Unique MyOperator API token issued to the user accessing the API." Found on the panel's **Calling APIs** page. **Masked hint:** begins `3f76…` (full value redacted).
- **On error:** the response carries an error `code` and `message` in the status parameter.

### Parameters

| Name | Required | Type | Notes |
|---|---|---|---|
| `token` | **Yes** | string | The Calling/Logs API token (the `3f76…` one). |
| `from` | No | string | Start date, **UTC unix timestamp**. |
| `to` | No | string | End date, **UTC unix timestamp**. |
| `log_from` | No | string | Pagination offset; defaults to `0`. |
| `page_size` | No | string | Number of logs; defaults to `20`, **max `100`**. |

---

## 6. Token inventory & regeneration

### The different tokens (this was the main source of earlier confusion)

| Token | Where it lives | What it's for | Auth header |
|---|---|---|---|
| **WhatsApp "Authentication"** (`lHCx…`) | APIs & Webhooks → Developer API → **WhatsApp APIs** | Sending WhatsApp via `publicapi.myoperator.co/chat/*` | `Authorization: Bearer` |
| **Calling / Logs token** (`3f76…`) | Panel → **Calling APIs** page | Call logs / IVR via `developers.myoperator.co/search` | `token` parameter in body |

### Regeneration caveat (confirmed by the engineer)

- Clicking **Regenerate** on the WhatsApp Authentication token **will break the live after-call / missed-call automation** (`new_post_call_message`, `eng_missedaftercall`) **after ~24 hours**.
- So there is a **24-hour grace window**. The safe sequence is: regenerate → within 24 hours make sure the new token is in place **everywhere it is used**.
- **Decision: do NOT regenerate impromptu.** Plan it as a deliberate step.
- **Still to confirm with the vendor before regenerating:**
  1. Do the after-call / missed-call automations pick up the new token **automatically**, or must it be pasted in somewhere manually — and where?
  2. Does the new token work **immediately** for the `publicapi` send?
  3. Confirm the safe order: regenerate, then update everywhere within 24h.

---

## 7. Error → meaning quick reference

| What you saw | Meaning |
|---|---|
| `HTTP 500` + `{"message":null}` on Bearer | API not provisioned / server can't resolve the account (the pre-fix symptom). |
| `HTTP 401` + `{"message":"Unauthorized"}` on `x-api-key` | Wrong auth scheme/key for this endpoint (this endpoint wants Bearer, not x-api-key). |
| `403 Forbidden` / `"...explicit deny in an identity-based policy"` | Either the account isn't provisioned for the resource **or** the header used lowercase `bearer`. |
| `200 OK` + `status: success` + `Accepted` | Working. A real WhatsApp went out. |

---

## 8. What happened on the call (timeline)

1. **Before the call:** every authenticated call failed — Bearer → `HTTP 500 {"message":null}`; same call with `x-api-key` → `401 Unauthorized`; even read-only calls; across all keys.
2. **Local PC, lowercase `bearer`:** returned `"...explicit deny in an identity-based policy"`.
3. **Engineer's Postman, capital `Bearer`:** first `403 Forbidden` → engineer **enabled/provisioned the API** → then `200 OK / success / Accepted` (template `drmanoj_followup_due`).
4. **Second Postman test:** `200 OK` again (template `drmanoj_followup_missed`).
5. **Local PC still failed** with the explicit-deny message → cause isolated to **lowercase `bearer`**.
6. **Changed `bearer` → `Bearer`** in `test_send.py` → `200 OK / success / Accepted` from the clinic PC. ✅
7. **Engineer confirmed:** it was a setup issue, now solved; access is permanent and included in the plan.

---

## 9. Open items / next steps

- [ ] **Strip the token out of `test_send.py`** after testing (leave a placeholder); keep the real value only in `.env`.
- [ ] **Wire the follow-up tracker** to this working recipe — capital `Bearer`, variables as `"1"`/`"2"` (`WABA_TEMPLATE_BODY_FORMAT = numeric`).
- [ ] **Plan the token regeneration** inside the 24-hour window, after confirming the three vendor questions in §6.
- [ ] **Call/Logs API** — take up separately for the IVR / missed-call workstream (not part of follow-up messaging).

---

## Appendix — working `test_send.py` shape (token redacted)

```python
import http.client
import json

conn = http.client.HTTPSConnection("publicapi.myoperator.co")
payload = json.dumps({
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
  "reply_to": None,
  "myop_ref_id": None
})
headers = {
  'X-MYOP-COMPANY-ID': '68384350414b9847',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'Authorization': 'Bearer <TOKEN_FROM_ENV>'   # capital "Bearer" — REQUIRED
}
conn.request("POST", "/chat/messages", payload, headers)
res = conn.getresponse()
print(res.read().decode("utf-8"))
```

*End of KB — 16 June 2026 live call. Companion docs: `FollowupTracker_WABA_Context_Consolidated.md`, `MyOperator_API_Support_Report.md`.*
