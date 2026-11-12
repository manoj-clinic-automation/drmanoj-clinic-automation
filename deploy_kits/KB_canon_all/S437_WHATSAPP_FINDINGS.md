# S437 — WHATSAPP FINDINGS — the parent, 12-Nov-2026 (Claude Fable) — counts only; no patient name or number

*Every figure, read and decision of S437. The running notes with the kits' details: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S437\S437_NOTES_FOR_CLOSE.md`.*

## 1 · F-1031 — why the Inbox's sends were refused, shown

**The proof table** (S802's installer, on the server, 15:35 IST; every request a FRESH made-up key used once, nothing sent; 500A = HTTP 500 with `x-amzn-ErrorType: AuthorizerConfigurationException`, body `{"message":null}`; 401/403 = the proper answer to a wrong key):

| way | answers |
|---|---|
| 1 urllib — the Inbox's road until today | 500A 500A |
| 2 `http.client`, header names exactly as written | 403 403 |
| 3 `http.client`, the company header named as urllib sends it | 500A 500A |
| 4 `http.client` as written, with `Connection: close` | 403 403 |
| 5 the changed Inbox sender, made-up keys | 403 403 |
| 6 the changed Inbox sender, the real key, an empty number | 400 (let through) |

Rows 2 and 3 differ in one thing: `X-MYOP-COMPANY-ID` against `X-Myop-Company-Id`. Python's urllib writes every header name as `Xxx-Yyy`; `http.client` writes it as given. MyOperator's gateway keeps an authorisation per key for a while: in S799's run urllib was refused until an `http.client` request with the same key had been let through, then accepted. That is why the Inbox worked in clusters and failed for days.

**The month before the fix** (the Inbox's send log, 30 days to 12-Nov): first tries 10 ok / 27 refused, none ok in November; retries 5 ok of 667. The tracker's relay (`wa_send.py`, `http.client`): 2 sent, 0 refused since 1-Nov.

**After** (to 17:16 IST): the test template 15:36:39 ok; a reply at its 30th try 15:42:01 ok; 0 refused.

**Who sends how** (the 12-Nov bundle): `http.client` — `wa/wa_send.py`, `wa/wa_send_api.py` (the tracker's relay), the probes; now also `portal/portal_inbox.py` (`myop_send`) and `portal/portal_wa.py` (`send`). **Still urllib — F-1294:** `wa/waba.py` (behind `wa_approve.py`), `wa/swap_key_s701.py`.

**For MyOperator's ticket 691386 (D938 — not sent; the owner decides the text after 1–2 days):** HTTP header names are case-insensitive by the standard; their authorizer treats the company header's name as case-sensitive and answers 500 instead of 401/403.

## 2 · The show-only list (S798, S801) — `/portal/messages`

Six lists in the owner's order: follow-up tomorrow (6 p.m. the day before) · after today's visit · appointment reminder (online bookings; this template carries no number) · date passed, next morning · date passed, day 5 · long overdue (two weeks; only on his tick). Rules in the code: never to a patient who came back; one message a number a day; not to those who bought medicines meanwhile (D919); the stop list; a missing mobile or several mobiles → held and said.

**12-Nov on the box:** tomorrow 9 · date passed yesterday 2 · day five 4 · long overdue 12 · rows without a mobile 0 of 27 (27 of 27 before S801). From the PC's copy: seen 11-Nov 18; visits a clinic day 17 on average (up to 31); follow-up dates given in 30 days 347, not back 194; standing past their date 4–10 days 42, 11–45 days 218 (left alone). About 40 messages a day, 1,000 a month.

**STOP:** before S798 nothing on the server read an incoming STOP (the older approve page honours a hand-kept file). In the 200 newest chats: 0 STOP. The listener runs every 5 minutes; the stop list is empty.

**The mobile:** `finance.db` `patient_ref` keeps the last four digits and a fingerprint only; the full mobile is in `/root/wa/console.db` `patients`.

## 3 · His MyOperator plan, as read in the panel (read-only)

Plan "SUV", Rs 15,000 a month, 15 months, renewal 03-Aug-2027. Users 10 (8 used); channels 10 pairs; departments 10 (2 used: Appointments — simultaneous, 25 s; Emergency). **One number** — the helpline — carries incoming and outgoing; there is no second IVR number. Calls lost for want of a channel: **14 ever** (11 of them in seven minutes on 14-Aug). Last 7 days: incoming 118, connected 78, missed 40. **When all lines are busy the flow ends** — no voicemail, queue or overflow. The internal transfer is in use (his word); the panel shows no setting for it. After-call WhatsApp: a webhook to an approved template, active since 17-Aug.

**Cost:** utility template 13 paise (19 this cycle = Rs 2.47); prepaid wallet about Rs 29,000; about 1,000 a month ≈ Rs 130.

**Audio library:** 29 items; three "get back to you" recordings, MyOperator's stock English (9–12 s), none in the active flow; the welcome is bilingual, 7.8 s.

## 4 · The Google profile and the contact page

Read 11:35 IST as a visitor: both show only the old number. His word (D937): leave them to change by themselves; check at every open.

## 5 · Decisions

D937 — the show-only list, its order and wording ok; ONE test template to his own number (done 15:36); the profile and contact page left; the costs ok; the internal transfer is operational. D938 — nothing to MyOperator until 1–2 days are observed and he decides the text. D939 — next: the WhatsApp items, then the analytics page.

## 6 · Kits

S798_WA_MESSAGES_SHOWONLY (live 12:05) · S801_WA_LIST_MOBILES (live 12:35) · S802_WA_SEND_HEADERS (live 15:35) · S799_WA_SEND_ROAD and S800_WA_SEND_KNOCK (ran, changed nothing — two wrong readings, F-1292).
