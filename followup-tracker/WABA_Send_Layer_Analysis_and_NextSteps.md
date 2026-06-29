# WABA Send Layer — Analysis & Next Steps

**Connecting your existing Follow-Up Tracker to MyOperator WABA · 12 June 2026**

---

## 1. What I found in your kit (the important part)

Your local tracker is **most of the system already built**. It resolves patient identity to UID, cleans and validates mobiles, runs the exact follow-up state machine the templates were designed for, computes days-overdue, tracks visits, carries the diagnosis taxonomy, skips vacation windows, and deliberately refuses to act on ambiguous/invalid identities. Your `processor.py` even contains comments written *for this step* ("when WABA goes live…").

So there is **nothing to rebuild**. The only missing piece was the **send arm** — the part that takes the tracker's output and actually calls the WhatsApp API. That's what these four files are.

## 2. How your tracker's status maps to the approved templates

| `Followup_Status` (your processor) | Days overdue | Template (approved) |
|---|---|---|
| Not Due *(only when due = tomorrow)* | −1 | `drmanoj_followup_tomorrow` (B2) |
| Due Today | 0 | `drmanoj_followup_due` (B3) |
| Grace Period | 1–3 | `drmanoj_followup_due` (B3) |
| Actionable Missed Follow-Up | 4–10 | `drmanoj_followup_missed` (B4) |
| Probable Dropout | 11–60 | `drmanoj_followup_dropout` (B5) → uses `Days_Overdue` |
| *(visit today, from visit ledger)* | — | `drmanoj_post_visit` (B1) |
| Returned / Identity / Invalid / Expired | — | **never sent** |

Because only those five statuses are sendable, your identity-unresolved and invalid-mobile patients are **automatically protected** — they can't be messaged.

*Proof it works:* run against your real `followup_ledger.csv` (dated 11 Jun), the driver built a plan of **56 messages** — 15 B4, 18 B3, 12 B2, 11 B1 — with dates formatted ("06 Jun 2026") and the test-allowlist correctly clamping it to 2.

## 3. The four new files (drop into the `followup_tracker/` folder)

| File | What it does |
|---|---|
| `waba.py` | The API client: Bearer auth + your IDs, sends one approved template, handles errors (halts the batch on `CHAT_4001` wallet-empty / WABA-disabled), validates mobiles. |
| `send_followups.py` | The batch driver: reads your ledgers, maps status→template, applies **dedupe / opt-out / test-allowlist / daily-cap**, dry-run by default, logs every send to `data/messages_log.csv`. |
| `waba_probe.py` | One-shot tester — sends a single template to *your own* number to confirm auth and the variable format before any batch. |
| `.env.example` | Config template. Copy to `.env`, paste the token, keep the test allowlist set until go-live. |

These **only add** to your tracker; they never modify its files. The only new files they create are `data/messages_log.csv` (the send log) and, when you start handling opt-outs, `data/opt_outs.csv` (columns: `Mobile,Date,Source`).

## 4. The one thing to confirm on the very first send

The MyOperator collection shows template sends but **not** a real example of how variable values are passed. So `waba.py` keeps all known formats in one switch (`WABA_TEMPLATE_BODY_FORMAT`, default `var_n`). `waba_probe.py` settles it in one message: if the variables don't fill in correctly, re-run with `numeric` / `varn` / `list` until one renders right on your phone, then lock that value in `.env`. This is the only API unknown left.

## 5. Local test sequence (do this on the clinic PC)

1. Put the four files in `followup_tracker/`. Create `.env` from `.env.example`, paste your **WhatsApp APIs → Authentication** token (the one in Apple Notes), keep `WABA_TEST_ALLOWLIST` set to your 5 numbers.
2. `pip install -r requirements.txt` already covers it (no new dependencies — `waba.py` uses only the standard library).
3. **Probe** (confirms auth + format + rendering to your phone):
   `python waba_probe.py 9837046634` — try each template name; if a template uses variables, watch they fill correctly. Fix the format in `.env` if needed.
4. **Dry-run the batch** (sends nothing): `python send_followups.py` — read the plan it prints.
5. **First real batch, tiny + safe:** temporarily set `WABA_TEST_ALLOWLIST` to **2–3 real patients you trust** who appear in today's ledger, then `python send_followups.py --send`. Verify they receive the right template. (Your 5 test numbers aren't patients, so the *batch* won't target them — that's what the probe in step 3 is for.)
6. When confident, clear `WABA_TEST_ALLOWLIST` to send to all eligible patients (the cap of 100 still pauses runaway runs).

This is exactly your **semi-automatic** model: you run the day's process, read the dry-run, then choose to `--send`. Later that becomes a button.

## 6. What still has to be built (the VPS phase)

Sending works from anywhere, but three things need the server at `followup.dr-manoj.in`:

1. **Webhook receiver** — a `/webhook` route to catch delivered / read / failed / **STOP** events and update `messages_log.csv`, joined on `message_id`. Sending is testable now; delivery/read confirmation needs this.
2. **Auto opt-out** — the webhook writes "STOP" repliers into `opt_outs.csv` so the driver permanently skips them. Until then, opt-outs can be added by hand.
3. **"Review & Send" button** in the Flask UI — the same `send_followups` logic behind a button, so staff (you → Shavez → reception) can run it without the command line.

None of these block the local send test. They come once the tracker is moved onto the VPS (your app is already VPS-ready — password env vars + waitress are in place).

## 7. Where we are

- Templates: **approved** ✓ · Tracker: **built & running** ✓ · Send layer: **written, dry-run-verified against your real ledger** ✓
- Immediate: run the **probe** to lock the body-variable format, then a **tiny allowlisted live batch**.
- Then: deploy the tracker to `followup.dr-manoj.in`, add the **webhook receiver** + **opt-out** + **send button**, and run the pilot.

Tell me the probe result (which `WABA_TEMPLATE_BODY_FORMAT` rendered correctly) and I'll wire the webhook receiver + the Flask send button next.
