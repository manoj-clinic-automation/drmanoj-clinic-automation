# MyOperator OBD Click-to-Call — Technical Build Reference (TOP PRIORITY)
**Dr. Manoj Agarwal Clinic · prepared 26 Jun 2026**
Goal: make the dashboard's "Call" buttons place real MyOperator calls (logged, recorded, IVR-tied) instead of native `tel:` dialer calls. Calls are FREE on the SUV plan (owner-confirmed). This is the agreed next build.

> Source: the clinic's official MyOperator Postman collection (`api/MyOperator_API_Document_postman_collection.json`). No secret values appear in this doc.

---

## 1. Why (the value, in one place)
- **IVR-logged + recorded** outbound calls → they appear in Call_Feed like inbound calls.
- **Anti-duplicate calling:** a call placed by ANY agent lands in the shared logs, so the dashboard can auto-clear that patient from everyone's "Needs callback now" list.
- **Security:** the calling secret lives only on the VPS behind a key-gated endpoint. A leaked dashboard file can place NO calls. With User Dialer, a triggered call can only ever ring a REGISTERED agent's stored mobile — it cannot be bent to an arbitrary phone.
- **Caller mapping is already done:** every agent's mobile is in their MyOperator profile; we reference the agent, MyOperator rings their stored mobile.

Dependency to note: click-to-call rings the agent's REAL mobile in the background, so that SIM must have active outgoing service (if an agent's recharge lapses, only THEIR button fails to connect).

---

## 2. Endpoint & auth
```
POST https://obd-api.myoperator.co/obd-api-v1
Header:  x-api-key: <OBD x-api-key>          # from the Calling/OBD panel area
Body (JSON): includes company_id + secret_token (see modes)
```
Two separate secrets are involved: the **`x-api-key`** (header) and the **`secret_token`** (body). Plus **`public_ivr_id`** (body). These THREE are not yet captured — they are the only gate (see §7).

## 3. Call modes (pick one)
**Recommended for this clinic: Type 1 → User Dialer** (rings the agent's MyOperator user, bridges the patient; cleanest attribution; agents auto-resolved via Get Users).

### Type 1 — User Dialer  (RECOMMENDED)
```json
{
  "company_id": "68384350414b9847",
  "secret_token": "<secret_token>",
  "type": "1",
  "number": "<patient number incl. country code, e.g. 91XXXXXXXXXX>",
  "public_ivr_id": "<public_ivr_id>",
  "user_id": "<agent uuid>",
  "reference_id": "<our tracking id, e.g. callback row id or patient number>",
  "max_call_duration": 300,
  "call_hold": true
}
```
> NOTE: the OBD example labels `user_id` as `<uuid>`. Get Users returns BOTH `user_id` and `uuid` per agent — confirm on the first live test which one OBD expects (almost certainly `uuid`). Optional: `region`, `std_code`, `caller_id`, `custom_1`, `custom_2` (voicebot).

### Type 1 — Anonymous Dialer (fallback; no user mapping, just a phone)
```json
{ "company_id":"...", "secret_token":"...", "type":"1",
  "number":"<patient>", "number_2":"<agent mobile>", "public_ivr_id":"...",
  "reference_id":"...", "max_call_duration":300, "call_hold":true }
```

### Type 2 — IVR Dialer (routes the patient into the IVR flow; not the callback use-case)
```json
{ "company_id":"...", "secret_token":"...", "type":"2",
  "number":"<patient>", "public_ivr_id":"...", "max_call_duration":300, "call_hold":true }
```

**Constraints:** `max_call_duration` INTEGER and must be ≤ 5400 (5401 → Bad Request). `call_hold` ∈ {true,false}. `type` ∈ {"1","2"}.

## 4. Success & error responses
**Success:**
```json
{ "details":"Request accepted successfully", "status":"success", "code":"200",
  "unique_id":"<request_id>", "reference_id":"<echoed back>" }
```
- `unique_id` = MyOperator's id for this call request. `reference_id` = whatever WE sent — **this is the loop-closing join key.**

**Errors (from saved examples):** Bad Request (missing `company_id`/`secret_token`/`number`/`public_ivr_id`, invalid `type`, or `max_call_duration`>5400) · 403 Forbidden (wrong key/secret or not provisioned) · 404 Not Found · 500 Internal (server-side).

## 5. Agent auto-mapping — Get Users
```
GET https://developers.myoperator.co/search/user?token=<CALLING/LOGS token (3f76…)>&_all
```
Returns `data[]` with per-agent `user_id`, `uuid`, `name`, `contact_number`, `extension`, `role_id`. Build a name→uuid map once (cache in Script Properties or a sheet tab), refresh occasionally. This removes all manual uuid upkeep and stays correct as staff change.

## 6. Loop-closing design (auto-clear the callback list)
1. When a button is tapped, send the OBD call with `reference_id` = the callback row id (or patient number+date).
2. The same `reference_id` returns (a) immediately in the OBD success body and (b) later in the **call logs** (`Search Logs`, master ref) and/or the **`call.end` / `call.summary` webhooks**.
3. A small matcher marks that patient "called/attempted" in the sheet → the dashboard drops the row from "Needs callback now" for EVERY agent.
- Optional real-time: register the new Calls webhooks (`call.initiated/answered/end/summary`) → the existing VPS receiver, matching on `reference_id`/number. Otherwise poll Search Logs on the dashboard refresh.

## 7. WHAT WE STILL NEED (the only gate) — get from panel or Lokesh
1. **`public_ivr_id`** — the IVR's public id.
2. **`secret_token`** — OBD body secret.
3. **`x-api-key`** — OBD header key.
All three sit in the panel's **Calling / OBD API** area (same family as the existing Calling/Logs `3f76…` token — nothing WhatsApp-side is touched, nothing needs regenerating). If labels are unclear, one message to Lokesh: *"Please give me the OBD click-to-call public_ivr_id, secret_token, and x-api-key for company 68384350414b9847."*

## 8. Build plan (once the 3 values are in hand)
1. **VPS:** add a gated endpoint (same pattern as `/wa-send`) — e.g. `POST /call` on a new tiny service (or extend the relay), holding the 3 OBD secrets in `/root/wa/.env`. It accepts `{ agent, patient_number, reference_id }` behind header `X-Call-Key` (mirrors a new `CALL_API_SECRET` in Script Properties), resolves agent→uuid (Get Users cache), and POSTs to the OBD endpoint. Returns `unique_id`.
2. **Apps Script (`WebApp.gs`):** `triggerCall(number)` server-side via `UrlFetchApp` → VPS `/call` with the call key (secret stays server-side, never in the browser/sheet). Logs the attempt.
3. **Dashboard (`Dashboard.html`):** change the Call buttons from `href="tel:..."` to `onclick="placeCall(number, rowId)"` → `google.script.run.triggerCall(...)`; show a "ringing your phone…" toast.
4. **Test ladder:** (a) one call to the doctor's own number from Postman/curl to confirm the 3 creds + which id field (`user_id` vs `uuid`); (b) wire VPS `/call`, curl it; (c) one button in the dashboard; (d) roll to all buttons; (e) add the reference_id matcher.

## 9. Security model (defense in depth)
- OBD secrets: VPS `.env` only (chmod 600). Never in Apps Script HTML, never in the sheet, never in chat.
- Endpoint gated by `X-Call-Key` (`CALL_API_SECRET`), mirrored in Script Properties; the dashboard calls it ONLY server-side via UrlFetchApp.
- User Dialer pins the caller to a registered agent uuid server-side → cannot dial from an arbitrary phone.
- Dashboard remains key-gated (full/staff). A leaked HTML copy has no secret and no VPS access → zero calling power.
