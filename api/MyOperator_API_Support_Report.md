# MyOperator Support — Public WhatsApp API returns HTTP 500 on Bearer auth

**Account:** Dr. Manoj Agarwal Clinic
**Date:** 13 June 2026
**Severity:** Blocking — cannot send any WhatsApp message via the public API

---

## 1. Summary

Every authenticated call to the public WhatsApp API (`https://publicapi.myoperator.co`)
fails. A request with `Authorization: Bearer` returns **HTTP 500** with body
`{"message":null}` — a server error, not an auth rejection. The identical request
with an `x-api-key` header returns a clean **HTTP 401 `{"message":"Unauthorized"}`**.
This happens on a simple no-body GET as well as on the send endpoint, and is
identical across every credential in our panel. Our message templates are
approved. We believe the public WhatsApp API is not enabled/provisioned on our
WABA and need it activated.

---

## 2. Account identifiers

| Item | Value |
|---|---|
| Company ID | 68384350414b9847 |
| WABA ID | 2101222617483538 |
| Phone Number ID | 1090067637530949 |
| WABA number | 9358008080 |
| Base URL | https://publicapi.myoperator.co |
| Token used | The "Authentication" value from panel → APIs & Webhooks → Developer API → WhatsApp APIs |
| Auth scheme | Per your Postman collection: `Authorization: Bearer <token>` + `X-MYOP-COMPANY-ID` |

---

## 3. Exact requests and responses (reproducible)

### 3a. No-body GET (templates list) with Bearer → HTTP 500
```
curl -i -X GET "https://publicapi.myoperator.co/chat/templates?waba_id=2101222617483538&waba_template_status=approved&limit=5&offset=0" \
  -H "Authorization: Bearer <OUR_WHATSAPP_APIS_AUTH_TOKEN>" \
  -H "X-MYOP-COMPANY-ID: 68384350414b9847" \
  -H "Accept: application/json"
```
Response: **HTTP 500**, body `{"message":null}`

### 3b. Same GET with x-api-key instead of Bearer → HTTP 401
```
curl -i -X GET "https://publicapi.myoperator.co/chat/templates?waba_id=2101222617483538&waba_template_status=approved&limit=5&offset=0" \
  -H "x-api-key: <OUR_WHATSAPP_APIS_AUTH_TOKEN>" \
  -H "X-MYOP-COMPANY-ID: 68384350414b9847" \
  -H "Accept: application/json"
```
Response: **HTTP 401**, body `{"message":"Unauthorized"}`

### 3c. Send a template (POST) with Bearer → HTTP 500
```
curl -i -X POST "https://publicapi.myoperator.co/chat/messages" \
  -H "Authorization: Bearer <OUR_WHATSAPP_APIS_AUTH_TOKEN>" \
  -H "X-MYOP-COMPANY-ID: 68384350414b9847" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"phone_number_id":"1090067637530949","customer_country_code":"91","customer_number":"9837114044","reply_to":null,"myop_ref_id":null,"trail":{"name":null},"data":{"type":"template","context":{"template_name":"drmanoj_followup_due","language":"en","body":{"var_1":"Test Patient","var_2":"14 Jun 2026"}}}}'
```
Response: **HTTP 500**, body `{"message":null}`

GET `/chat/phonenumbers` behaves the same as 3a (500 on Bearer).

---

## 4. What we have already ruled out

- **Variable/body format** — tried `var_1`, numeric `1`, `var1`, and list forms; all 500. A **no-variable** template also 500s, so it is not the body.
- **Header names / scheme** — match your Postman collection exactly (`Authorization: Bearer` + `X-MYOP-COMPANY-ID`, `Content-Type`, `Accept`).
- **Token paste/truncation** — token loaded clean from a file; same result.
- **Company ID** — sent identically in 3a and 3b; only the auth header differs, yet results differ (500 vs 401), so the company ID is not the issue.
- **The credential itself** — tried all four panel keys (WhatsApp APIs Authentication, Calling APIs x-api-key, Calling APIs Authentication, Secret Key) as both Bearer and x-api-key. Every one: Bearer → 500, x-api-key → 401.

A 500 (server crash) rather than a 401 (clean reject) on the Bearer path, for **every** credential, indicates the Bearer handler cannot resolve our account context — consistent with the public WhatsApp API not being enabled/provisioned on our WABA.

---

## 5. Our questions / requests

1. Please **enable/provision public WhatsApp Business API access** (`publicapi.myoperator.co`) for the company/WABA above, or tell us the exact activation step in the panel.
2. Is public WhatsApp / Developer API access **included and enabled on our current plan**? If it is a paid add-on, how do we activate it?
3. Please **confirm the correct credential and auth header** for `POST /chat/messages`. We are using the WhatsApp APIs page "Authentication" value as `Authorization: Bearer`, with `X-MYOP-COMPANY-ID`, per your Postman collection.
4. **Will clicking "Regenerate" on the WhatsApp APIs "Authentication" token affect our existing automated post-call / missed-call WhatsApp templates** (`new_post_call_message`, `eng_missedaftercall`) that currently fire from the panel's call automation? We do not want to regenerate if it risks breaking those live messages.

Please route this to the API/technical team. Everything on our side is ready — we only need API access confirmed/enabled.

Thank you,
Dr. Manoj Agarwal Clinic
