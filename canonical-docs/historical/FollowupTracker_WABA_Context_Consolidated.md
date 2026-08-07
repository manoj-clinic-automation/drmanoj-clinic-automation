# Follow-Up Tracker × WABA — Consolidated Project Context

**Dr. Manoj Agarwal Clinic, Bareilly · WhatsApp automation via MyOperator API**
Handoff/context document · last updated 12 June 2026

> Purpose: drop this into the follow-up tracker chat so any session has the full, integrated picture — what's built, what's decided, where the one blocker is, and exactly how to resume.

---

## 1. Goal in one paragraph

Send the clinic's WhatsApp follow-up ladder automatically from the existing **Follow-Up Tracker** (a Python/Flask app), using the **MyOperator WhatsApp Business API**. The tracker already computes *who needs which message*; we are adding the *send arm* plus delivery/STOP tracking. Deployment target is the **Hostinger VPS** (CyberPanel) under the private domain **followup.dr-manoj.in**. Patient base is older, Hindi-first, semi-urban — messaging is conservative and semi-automatic at first.

---

## 2. Confirmed MyOperator config

| Item | Value |
|---|---|
| Base URL | `https://publicapi.myoperator.co` |
| Company ID | `68384350414b9847` |
| WABA ID | `2101222617483538` |
| Phone Number ID | `1090067637530949` |
| WABA number | 9358008080 |
| Auth scheme (per Postman collection) | `Authorization: Bearer <token>` **+** `X-MYOP-COMPANY-ID: <company id>` |
| Bearer token location | Panel → **APIs & Webhooks → Developer API → WhatsApp APIs → "Authentication"** (eye → copy). **Not** the Calling-APIs x-api-key. |
| Send endpoint | `POST /chat/messages` |
| List templates | `GET /chat/templates?waba_id=<id>&waba_template_status=approved` |
| List phone numbers | `GET /chat/phonenumbers?...&waba_id=<id>` |
| Webhooks | Panel → APIs & Webhooks → **Webhooks v2** (currently empty; HTTPS only) |

Secrets (the Authentication token) live only in the VPS/`.env`, never in docs or chat.

---

## 3. Templates — all APPROVED in the panel

Exact registered names (no prefix on the B-set; A-set carries prefixes):

| Doc | Panel name | Vars | Role |
|---|---|---|---|
| B1 | `drmanoj_post_visit` | {{1}} name | post-visit (same-day) |
| B2 | `drmanoj_followup_tomorrow` | {{1}} name, {{2}} due date | reminder, due tomorrow |
| B3 | `drmanoj_followup_due` | {{1}} name, {{2}} due date | due today / grace 0–3d |
| B4 | `drmanoj_followup_missed` | {{1}} name, {{2}} due date | missed 4–10d |
| B5 | `drmanoj_followup_dropout` | {{1}} name, {{2}} due date, {{3}} days overdue | dropout >10d |
| A4 | `new_post_call_message` | — | after-call (LIVE, panel-native) |
| A3 | `eng_missedaftercall` | — | missed-call (LIVE, panel-native) |
| — | `daily_account_summary` | — | separate (accounting), out of tracker scope |

A4/A3 fire through MyOperator's **native call automation**, not the API — out of the tracker build's scope.
Variables registered as numbered placeholders `{{1}}`,`{{2}}`,`{{3}}`; API sends them positionally (`var_1`, `var_2`, …).
B5 body was fixed to actually use `{{3}}` (Meta rejects declared-but-unused variables).

---

## 4. How the tracker maps to templates (the integration)

The existing tracker (`processor.py`) already produces a `followup_ledger` with `Followup_Status`, `Days_Overdue`, resolved patient identity, and clean mobiles. The send arm just reads that:

| `Followup_Status` | Days overdue | Template |
|---|---|---|
| Not Due *(due == tomorrow)* | −1 | `drmanoj_followup_tomorrow` (B2) |
| Due Today | 0 | `drmanoj_followup_due` (B3) |
| Grace Period | 1–3 | `drmanoj_followup_due` (B3) |
| Actionable Missed Follow-Up | 4–10 | `drmanoj_followup_missed` (B4) |
| Probable Dropout | 11–60 | `drmanoj_followup_dropout` (B5) |
| visit today (visit ledger) | — | `drmanoj_post_visit` (B1) |
| Returned / Identity / Invalid / Expired | — | **never sent** (structurally excluded) |

Because only the five ladder statuses are sendable, identity-unresolved and invalid-mobile patients can never be messaged — safety is structural.

---

## 5. The send layer (built, drop-in to the `followup_tracker/` folder)

Standard-library only; no new dependencies. Reads config from `.env` (a tiny loader is built into `waba.py`).

| File | Role |
|---|---|
| `waba.py` | API client: Bearer auth + IDs, `send_template()`, phone normalize, error handling (halts batch on `CHAT_4001` wallet-empty / WABA-disabled), `.env` loader. Body-variable format is a switch (`WABA_TEMPLATE_BODY_FORMAT`: var_n / numeric / varn / list). |
| `send_followups.py` | Batch driver: reads ledgers, maps status→template, applies **dedupe** (`messages_log.csv`), **opt-out** (`opt_outs.csv`), **test allowlist**, **daily cap (pause+confirm at 100)**. Dry-run by default; `--send` to send. |
| `waba_probe.py` | One-shot tester to your own number; `--auto` tries all body formats and a no-variable isolation send. |
| `waba_check.py` | Auth isolation: no-body GET with Bearer and x-api-key across up to 4 candidate keys. |
| `.env.example` | Config template (no secret). |

Verified: the driver was dry-run against the real 11-Jun ledger → built a correct 56-message plan (15 B4 / 18 B3 / 12 B2 / 11 B1), dates formatted, allowlist/cap/dedupe all firing.

---

## 6. CURRENT BLOCKER (the one open item)

**Symptom:** every authenticated call to `publicapi.myoperator.co` fails the same way, on a no-body GET as well as on sends:
- `Authorization: Bearer <token>` → **HTTP 500, body `{"message":null}`**
- same request with `x-api-key` header → **HTTP 401 `{"message":"Unauthorized"}`**

**Ruled out (rigorously):** variable format (all 4), message body (no-variable template also 500), paste/truncation (token loaded clean from `.env`), header names/scheme (match the collection), company ID (sent in both; only auth header differs), and the key itself — **all four panel credentials** (WhatsApp Authentication, Calling x-api-key, Calling Authentication, Secret Key) fail identically under both schemes.

**Diagnosis:** a 500 (server crash) rather than a 401 (clean reject) on Bearer, for *every* credential, means the Bearer handler can't resolve the account context — i.e. the **public WhatsApp API is not enabled/provisioned on this WABA**, despite the panel showing keys. This is account-side, not the code.

**Escalation:** ticket prepared for MyOperator asking them to (1) enable/provision public API access, (2) confirm the correct credential + auth header for `POST /chat/messages`, (3) confirm whether API access is included/enabled on the current plan, and (4) **confirm whether regenerating the WhatsApp APIs "Authentication" token would break the live panel-native after-call/missed-call templates** — owner does NOT want to regenerate until this is confirmed.

---

## 7. Decisions log

- Runtime: **Python**. Database: **SQLite (WAL)** for v1 (migrate to CyberPanel MariaDB later if needed).
- Deployment: **Hostinger VPS / CyberPanel**, webhook host **followup.dr-manoj.in** (real DNS A-record + Let's Encrypt; kept off the public drmanojagarwal.in WordPress site, per the clinic's vendor trust boundary). VPS timezone **Asia/Kolkata**.
- Sending model: **semi-automatic** first (operator reviews then sends), operated by doctor → assistant (Shavez) → reception in stages. Then fully scheduled.
- Daily cap: **pause + confirm if eligible > 100** (no artificial throttle below natural ~40–50/day volume).
- B1 timing: kept with "aaj"/same-evening wording for now (revisit later).
- Data flow: closed EMR (Docterz, CSV only). Doctor exports follow-up logs + consultation report nightly (~9–11 PM), later delegated; CSV lands on the VPS. Completion of a follow-up is inferred from the next export (patient reappears) since the EMR gives no completion signal.
- Marketing vendor never gets EMR / patient data / tracker / VPS access (separate trust class).

---

## 8. Owner-side status

Done: VPS + followup.dr-manoj.in live with SSL ✓ · timezone IST ✓ · all B templates approved ✓ · token copied to Apple Notes ✓ · 5 test numbers provided ✓ · wallet self-managed ✓.
Pending: MyOperator API enablement (the blocker) · then resume testing.

---

## 9. Resume sequence (the moment API access is enabled)

1. `python waba_check.py` → expect HTTP 200 (auth green).
2. `python waba_probe.py 9837114044 --auto` → confirms the working `WABA_TEMPLATE_BODY_FORMAT`; a real WhatsApp lands on the phone. Lock that format in `.env`.
3. Tiny **allowlisted** live batch (2–3 trusted real patients in today's ledger) → verify rendering.
4. Clear `WABA_TEST_ALLOWLIST` → send to all eligible (cap still pauses runaway runs).
5. **Still to build (VPS phase):** webhook receiver at `followup.dr-manoj.in/webhook` (delivered/read/failed/STOP → auto opt-out, joined on `message_id`), and a **"Review & Send" button** in the Flask UI for non-technical operators.

**Correlation note for the webhook:** for API-sent messages the webhook `source = api` and `myop_ref_id` may return null — join on the **`message_id`** returned by the send call, parsing both `conversation_id` and the misspelled `conversaton_id`.

---

## 10. Housekeeping (before go-live)

- Regenerate the WhatsApp APIs "Authentication" token (only after MyOperator confirms it won't break live call templates), since it has been on screen during testing.
- Remove the `MYOP_ALT_TOKEN*` lines from `.env` (they were only for auth isolation).
- Re-add `WABA_TEMPLATE_BODY_FORMAT`, `WABA_TEST_ALLOWLIST`, `WABA_DAILY_CAP` to `.env` if the short version is in use.

---

*End of consolidated context. Companion files: `waba.py`, `send_followups.py`, `waba_probe.py`, `waba_check.py`, `.env.example` (the send layer) and the rollout/plan docs.*
