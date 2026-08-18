# MyOperator API — Quick Reference Card (all systems)
**Dr. Manoj Agarwal Clinic** · masked hints only · full tokens live ONLY in VPS `.env` + Apple Notes

> THREE SEPARATE SYSTEMS + OBD. Tokens are NOT interchangeable. Mixing them is the #1 historical bug.
> **System letters match the Master Reference + Master KB §3:** A = Call/Logs · B = WhatsApp send · C = Inbound webhooks (**C-wa** WhatsApp inbound + **C-call** call events) · OBD = click-to-call. *(This card was re-lettered 29 Jun 2026 — earlier copies had A/B swapped. Call webhooks added to System C 03 Jul 2026, Session 54.)*
> **Session 16 note:** the full Callback Dashboard Apps Script project (all 11 files) is in `dashboard/`; the live dashboard reads the **Call/Logs API (System A)** directly on each page load (not via triggers).

---

## System A — Call / Logs API (IVR call history) ✅ LIVE
- **Endpoint:** `POST https://developers.myoperator.co/search` (live docs/test: `https://signup.myoperator.com/api/`).
- **Auth:** token in the **request body** as the `token` param — **no `Authorization` header.** Different token from WhatsApp. Panel → **Calling APIs** page. Masked hint `3f76…` (32 ch).
- **Params:** `token` (req), `from`/`to` (UTC unix seconds), `log_from` (offset, dflt 0), `page_size` (dflt 20, **max 100**). Params go in a **raw JSON body** (query-string is a fallback only).
- **Use bare paths** — ignore the Postman `/search/` prefix (e.g. `/search/recordings/link`), it 404s here.
- **Recording link:** `GET /recordings/link?token=…&file=<filename .mp3>` — link valid **24h**. Audio exists only when `status==1` AND `filename!=""`. `event` 1=incoming/2=outgoing; `status` 1=answered/2=missed.
- **Use:** call logs for IVR / missed-call / callback work + the live dashboard poller. NOT for sending WhatsApp.
- **Timestamp note:** MyOperator sends 9-digit nanosecond timestamps + `Z`; Python 3.9 `fromisoformat()` rejects → trim to ≤6 digits before parsing.
- **Regen risk: LOW.**

---

## System B — WhatsApp Business API (sending) ✅ WORKING
- **Base:** `https://publicapi.myoperator.co`
- **Auth:** `Authorization: Bearer <token>` — **CAPITAL B REQUIRED** (lowercase `bearer` → AWS IAM explicit-deny). Plus `X-MYOP-COMPANY-ID: 68384350414b9847`.
- **Token source:** Panel → APIs & Webhooks → Developer API → **WhatsApp APIs → "Authentication"**. Masked hint `lHCx…`. NOT the Calling key. **VPS `.env` variable name: `MYOP_AUTH_TOKEN`** (proven S137 — `WA_SEND_TOKEN`/`WA_TOKEN` do not exist in `/root/wa/.env`; an empty Bearer draws the same AWS explicit-deny as a bad one).
- **Send:** `POST /chat/messages`
- **List templates:** `GET /chat/templates?waba_id=2101222617483538&waba_template_status=approved` — **paginated, page size 10 (`limit`/`offset`); panel holds 14, so one page silently misses four** (proven S137, full two-page pull captured in `WABA_Approved_Templates_v1_S137.md` + raw JSON snapshots).
- **List numbers:** `GET /chat/phonenumbers?...&waba_id=2101222617483538`
- **Body variables — SPLIT BY TEMPLATE FAMILY (S137):** the five `drmanoj_*` templates use **numeric** string keys `"1"`,`"2"`,`"3"` inside `body` (NOT `var_1`, NOT a list; `language="en"`; → `WABA_TEMPLATE_BODY_FORMAT=numeric`). The other seven approved templates use **NAMED** keys exactly as defined (`var_1`, `var_2`; `daily_account_summary` uses `date`/`vehiclesummary`/`collectionsumma`/`totalamount`). **The numeric rule is NOT universal — sending named-key templates with numeric keys will fail.**
- **Free-text (session) send:** same endpoint, `data.type="text"`, `context:{body, preview_url:false}` — **only delivers inside the 24h session window** (patient must have messaged in last 24h; else template only). `wa_send.py` enforces this by reading WA_Inbox first.
- **Success:** `200` `{status:success, code:200, message:Accepted, data:{conversation_id, message_id}}`. `conversation_id` = one per recipient; `message_id` = unique per message.
- **Webhook join key:** API-sent → `myop_ref_id` is null → match delivery/read/failed/STOP on **`message_id`** (parse both `conversation_id` and the misspelled `conversaton_id`).
- **Regen risk: HIGH** (see caveat below).

### Working send body (confirmed 200):
```json
{ "phone_number_id":"1090067637530949","customer_country_code":"91",
  "customer_number":"9837114044",
  "data":{"type":"template","context":{
    "template_name":"drmanoj_followup_due","language":"en",
    "body":{"1":"John Doe","2":"12"}}},
  "reply_to":null,"myop_ref_id":null }
```

### Approved templates (panel names — FULL live inventory, 14/14, pulled S137; bodies in `WABA_Approved_Templates_v1_S137.md`):
| Name | Vars (format) | Role |
|---|---|---|
| `drmanoj_post_visit` | {{1}} name (numeric) | post-visit same-day — **D213: the seen-today message** |
| `drmanoj_followup_tomorrow` | {{1}} name, {{2}} date (numeric) | due tomorrow |
| `drmanoj_followup_due` | {{1}} name, {{2}} date (numeric) | due today / grace 0–3d — **D216: the 3rd-strike message** |
| `drmanoj_followup_missed` | {{1}} name, {{2}} date (numeric) | missed 4–10d |
| `drmanoj_followup_dropout` | {{1}} name, {{2}} date, {{3}} days overdue (numeric) | dropout >10d |
| `new_post_call_message` | — | after-call (LIVE, panel-native automation) |
| `eng_missedaftercall` | — (lang en) | missed-call (LIVE, panel-native automation) |
| `missedaftercall` | — (lang hi) | **duplicate body of `eng_missedaftercall`** — which one the automation fires: unconfirmed |
| `appointment_confirmation_ortho` | var_1 name, var_2 date-time (named) | booking confirmed |
| `appointment_reminder_1day_ortho` | var_1 name, var_2 date-time (named) | appointment tomorrow |
| `reschedule_confirmation` | var_1 name, var_2 new time (named, lang hi) | appointment moved |
| `welcome_template` | var_1 name (named, lang hi) | enquiry acknowledgement |
| `decline_acknowledgement_manoj` | var_1 name (named) | opt-out acknowledgement |
| `daily_account_summary` | named (date/vehicle/collections/total) | **STRAY non-clinic template — do not use; panel-tidy candidate** |

---

## System C — Inbound webhooks (Webhooks v2) ✅ LIVE

### C-wa — WhatsApp inbound ("Message Received")
- Panel → APIs & Webhooks → **Webhooks v2** (HTTPS only) → tick **Message Received** ONLY (other WhatsApp events would flood the sheet).
- **Webhook URL:** `https://followup.dr-manoj.in/wa-webhook?key=<WA_WEBHOOK_SECRET>` — the `?key=` is YOUR self-chosen gate, not a MyOperator token.
- **Receiver:** `wa_receiver.py`, running as **`wa-receiver.service`** (gunicorn, 127.0.0.1:8095). It receives each MyOperator push, de-dupes on `payload.id`, and writes one row to the **WA_Inbox** sheet tab. Inbound media arrives in TWO pushes (blank link, then link-filled ~2–7s later, same id) — the receiver lets the later push fill a blank media cell (Session 16 fix).
- **⚠️ Do NOT confuse with `wa-notifier.service`** — that is the SEPARATE ntfy watcher (`notifier_wa.py`) which polls WA_Inbox every ~30s and pushes name-only alerts to the private ntfy topic. Two different services on the VPS.
- **Timestamp gotcha:** push timestamp is UTC, may carry nanoseconds + `Z` → convert to IST (trim fractional to ≤6 digits on Py3.9).

### C-call — Call webhooks (Webhooks v2 → call events) ✅ LIVE (Session 54)
- Panel → APIs & Webhooks → **Webhooks v2 → Add New Webhook** → tick **Call Ended** (`call.end`) + **Call Summary** (`call.summary`) ONLY. This is a **SEPARATE** webhook entry from the "Message Received" one above — do not edit that one. Additive; **no WABA-token rotation, no Lokesh coordination.**
- **Webhook URL:** `https://followup.dr-manoj.in/mo-callhook?key=<CALLHOOK_SECRET>` — Authentication: **None** (the `?key=` is YOUR self-chosen gate). Path deliberately shares no prefix with `/call` (the dialer) so OLS can't mis-route.
- **Receiver:** `call_hook_capture.py`, running as **`call-hook.service`** (gunicorn, 127.0.0.1:**8098**; OLS context `/mo-callhook` → 8098). Walled off from WhatsApp/dialer. Raw-logs every body, then **upserts one PHI-clean row** into the **`Call_Durations`** sheet tab (**no phone number written**). Degrade-safe (raw-log + 200 even if Sheets is down; never retry-storms); skips incoming/non-OBD calls.
- **Join key = `payload.client_ref_id`** (our OBD `reference_id`) — **NOT `ref_id`** (that's MyOperator's own UUID). Only OBD calls carry it; incoming (`category:"incoming"`, empty `client_ref_id`) are skipped.
- **"Reached the patient?" = the customer leg** (`legs[]` where `type=="customer"`): `talk_duration` + `result` (`"answered"` = real pickup; `"connected"` w/ `answered_at:null` = reached only). Top-level `duration` includes agent-pickup + ring — **don't** use it as the connect signal.
- Feeds the **duration gate** (dashboard v18.16 · `CallConsole.gs::getCallDuration`, threshold **15s**). Full field detail: `api/MyOperator_Call_API_Master_Reference` **§9.0**.
- Helper: `call-hook/peek_callhook.py` prints a captured body with the patient number auto-masked.

---

## OBD — click-to-call (outbound dialer) ✅ WORKING
- **Endpoint:** `POST https://obd-api.myoperator.co/obd-api-v1`
- **Auth:** header **`x-api-key`** (a SEPARATE OBD key, `oomf…`, public/harmless) + `secret_token` (`26eb…`, real secret) in the body. All four OBD creds live in VPS `/root/wa/.env` (chmod 600).
- **Locked recipe (five hard-won rules):** (1) `number` in **E.164** (`+91`+10 digits — bare 10-digit and 12-digit-without-`+` both FAIL); (2) `max_call_duration` a real **integer** (not a string), ≤5400; (3) `call_hold:true`; (4) **unique `reference_id` per call** (reuse within ~2 days → 403); (5) `user_id` = panel hex (no UUID; Get-Users API returns 404, not needed). Calls are **queued, not instant** — 2-leg: agent's phone rings first, then patient bridges.
- **Anonymous Dialer:** disabled on this plan (403) — use User Dialer.
- Local service: `call_api.py` on VPS port **8097**, systemd, OLS proxy. Full proven recipe: `obd/OBD_ClickToCall_WORKING_Recipe_27Jun2026.md`.

---

## Token regeneration caveat (CONFIRMED by engineer)
Clicking **Regenerate** on the WhatsApp "Authentication" token (System B, `lHCx…`) **breaks the live after-call/missed-call automations (~24h grace)**. Safe sequence: regenerate → within 24h update the token everywhere it's used. **Do NOT regenerate impromptu** — plan it, coordinate with **Lokesh Kumar VB** (MyOperator engineer). Three things to confirm with the vendor before doing it: (1) do the panel automations pick up the new token automatically or must it be pasted somewhere; (2) does the new token work immediately for `publicapi` send; (3) confirm the regenerate→update-within-24h order. Helper: `token_rotation/rotate_wa_token.py` + plan doc.

---

## Error → meaning
| Saw | System | Means |
|---|---|---|
| `400 "...not an authorized request"` | A | Truncated token (need 32 ch) OR params in wrong place — use JSON body for `/search`. |
| `404` on recording link | A | Used the `/search/recordings/link` prefix — use the bare `/recordings/link`. |
| `500` + `{"message":null}` on Bearer | B | API not provisioned / can't resolve account (pre-16-Jun symptom; now fixed). |
| `401` `{"message":"Unauthorized"}` on x-api-key | B | Wrong scheme for that endpoint (chat/* wants Bearer). |
| `403` "explicit deny in an identity-based policy" | B | Not provisioned OR lowercase `bearer` (must be capital). |
| `403` on OBD | OBD | Reused `reference_id` within ~2 days, or Anonymous Dialer (disabled on plan). |
| `200` + `Accepted` | B / OBD | Working — a real WhatsApp went out / call request accepted. |
