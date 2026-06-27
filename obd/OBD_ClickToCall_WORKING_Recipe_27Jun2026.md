# OBD Click-to-Call — WORKING RECIPE (proven 27 Jun 2026)

**Status: ✅ LIVE & PROVEN.** A real User-Dialer call rang BOTH legs (agent mobile
…4044, then patient 9389559274) from the VPS. This was the project's top blocker
for weeks. Recipe below is locked — the `/call` endpoint must reproduce it exactly.

---

## 1. Endpoint & headers
```
POST https://obd-api.myoperator.co/obd-api-v1
Header:  x-api-key: <MYOP_OBD_XAPIKEY>      # the oomf… key (shared client key, public, harmless)
Header:  Content-Type: application/json
Header:  Accept: application/json
```

## 2. Working body (User Dialer = the production mode)
```json
{
  "company_id": "68384350414b9847",
  "secret_token": "<MYOP_OBD_SECRET>",
  "type": "1",
  "number": "+919389559274",
  "public_ivr_id": "<MYOP_PUBLIC_IVR_ID>",
  "user_id": "6838435041f29988",
  "reference_id": "obdtest-<unique>",
  "max_call_duration": 300,
  "call_hold": true
}
```
Response on success: `HTTP 200 {"details":"Request accepted successfully","status":"success","code":"200","unique_id":"…","reference_id":"…"}`

## 3. THE FIVE HARD-WON RULES (each was a separate 400/403 we debugged)
1. **`number` MUST be E.164:** `+91` + 10 digits, e.g. `+919389559274`. Bare `9389559274`
   AND bare `919389559274` both fail with `Provide valid Number in string format`.
   The `+` and country code are required.
2. **`max_call_duration` MUST be a real integer** `300` — NOT the string `"300"`.
   Quoting it triggers: `instance type (string) does not match … (allowed: ["integer"])`.
   (≤ 5400.)
3. **`user_id` = the panel "User id" hex works** (e.g. Dr Manoj `6838435041f29988`).
   No uuid needed. Get-Users API was NOT required.
4. **`reference_id` must be UNIQUE per call.** A repeat returns
   `403 … reference ID … already taken … remaining_ttl ~171777 seconds` (locked ~2 days).
   Use callback-row id, or patient+timestamp.
5. **Calls are QUEUED, not instant.** "Request accepted" (200) ≠ ringing. The dialer
   places the agent leg, waits for answer, then bridges the patient — expect a delay
   of seconds up to a minute+, longer right after a campaign is created. Early "dead"
   calls were just slow / the new campaign still propagating.

## 4. Account facts confirmed this session
- **Public IVR ID** lives in the OBD campaign **"Clinic API Calling"** (shown next to the
  campaign name in Manage → Call → Outgoing → Campaign). Saved in `.env` as `MYOP_PUBLIC_IVR_ID` (6a3f…).
- **Anonymous Dialer (number_2 = agent mobile) is DISABLED** on this plan
  → `403 "Your annonymous feature is not enabled"`. Do not use it; User Dialer is correct.
- **Get Users API** (`GET developers.myoperator.co/search/user?token=…`) returns
  `404 "Unknown method."` on this plan — looks unprovisioned. **Not needed**, because the
  panel hex `user_id` works directly. If ever needed, ask Lokesh to enable the User API.

## 5. Agent user_id map (panel hex — these are the `user_id` values to send)
| Agent | ext | user_id (hex) | mobile (last4) |
|---|---|---|---|
| Dr Manoj Agarwal | 10 | 6838435041f29988 | 4044 |
| Shavez Ahmed | 11 | 686cf49a692bb162 | 4926 |
| Shivani Srivastava | 12 | 686cf557c4f09495 | 9246 |
| Manoj Bhati | 13 | 686cf5a29a97d527 | 4408 |
| Alisha Khan | 14 | 69cfa941359e1649 | 3474 |
| Darpan Robert | 15 | 6a2017dd50280597 | 5546 |
| Reception Mobile | 16 | 6a2018cda8975829 | 4080 |

## 6. .env keys now present on the VPS (/root/wa/.env, chmod 600)
```
MYOP_OBD_XAPIKEY   = oomf…(public client key)
MYOP_OBD_SECRET    = 26eb…(secret_token, real secret)
MYOP_PUBLIC_IVR_ID = 6a3f…(campaign Public IVR ID)
MYOP_LOGS_TOKEN    = 3f76…(Calling/Logs Authentication token)
```
(Plus the WhatsApp/sheet keys already there: WA_SA_KEY, WA_WEBHOOK_SECRET, SEND_API_SECRET, WA_SHEET_ID, etc.)

## 7. Test tool (inert, kept on VPS for debugging)
`/root/wa/obd_test.py` — `python obd_test.py <patient10>` places one User-Dialer call.
Reads all creds from `.env`. Prints no secrets. Handy to re-verify the recipe anytime.

## 8. Next build (the /call endpoint) — reproduces this recipe server-side
See the v9 runbook §"NEXT BUILD". Gated `/call` on the VPS → Apps Script `triggerCall`
→ dashboard buttons → `reference_id` auto-clears the callback list.
