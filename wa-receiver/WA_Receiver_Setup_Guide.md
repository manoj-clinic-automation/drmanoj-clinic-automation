# WhatsApp Inbox Receiver — Setup Guide
**Dr. Manoj Agarwal Clinic · fills the dashboard's WhatsApp panels**
Last updated: 25 June 2026

> Read this as the map. **Don't start the VPS steps yet** — do **Step 0** first; it decides whether the rest is even possible right now. We'll go through the steps together, one at a time.

---

## What this does (one line)
A tiny always-on service on your VPS catches each incoming WhatsApp message MyOperator pushes, and writes it into the **WA_Inbox** tab of the Clinic Callback Tracker sheet. The dashboard already reads that tab, so the "Recent WhatsApp" panel and the per-caller WhatsApp line fill in by themselves.

## Files in this bundle
- `wa_receiver.py` — the receiver (Flask). Reuses the **patient-mirror** service account.
- `requirements.txt` — the three libraries it needs.
- `wa_receiver.env.example` — settings template (copy to `.env`, fill in).

---

## Step 0 — THE GATING CHECK (do this first, 2 minutes)
Before building anything on the VPS, confirm MyOperator will actually push inbound WhatsApp messages on your plan. (The *sending* API needed enabling earlier — inbound could be the same.)

- In the MyOperator panel: **APIs & Webhooks → Webhooks v2**. Look for the ability to add a webhook with an event like **"message received" / inbound message**.
- If you can add that event → we're clear.
- If you can't tell, or it's not there → one line to **Lokesh**: *"Does our plan push inbound WhatsApp 'message received' webhooks via Webhooks v2? We want to receive patient replies at our own endpoint."*

**Tell me what you find.** If it's available, we proceed to Step 1. If not, we get it enabled first instead of building blind.

---

## Step 1 — Make a folder + put files on the VPS
On the VPS (CyberPanel), create a working folder, e.g. `/home/<your-user>/wa/`, and upload into it:
`wa_receiver.py`, `requirements.txt`. (We'll make `.env` in Step 3.)

## Step 2 — Bring the service-account key over (reuse the same one)
The receiver signs in to Google with the **same `patient-mirror` JSON key** your local mirror uses.
- Copy that one JSON file from the local PC into the VPS `wa/` folder, e.g. as `patient-mirror-key.json`.
- Lock it down: `chmod 600 patient-mirror-key.json`
- (No new Google setup — that service account already has write access to the sheet.)
> The key is a secret. Keep it only on the VPS and the local PC. Don't paste it anywhere.

## Step 3 — Settings file
- Copy `wa_receiver.env.example` to `.env` in the same folder.
- Fill in: `WA_SA_KEY` (full path to the JSON), and invent a long random `WA_WEBHOOK_SECRET`.
- `WA_SHEET_ID` is already correct. Set `WA_RAW_LOG_DIR` to e.g. `/home/<your-user>/wa/wa_logs`.

## Step 4 — Install the libraries (in its own clean environment)
```
cd /home/<your-user>/wa
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 5 — Test run (prove it connects)
```
python wa_receiver.py
```
Expect a line like: `connected to 'WA_Inbox' - 8 columns, N ids known` and `listening on http://127.0.0.1:8095`.
In a second terminal: `curl http://127.0.0.1:8095/` → should print `wa_receiver alive`.
Stop it with Ctrl+C once that works.

## Step 6 — Keep it always-on (systemd service)
We'll create a small service so it runs 24/7 and restarts on reboot. (Exact unit file we'll write together — it runs gunicorn: `gunicorn -w 2 -b 127.0.0.1:8095 wa_receiver:app`.)

## Step 7 — Expose it at your domain
Make `https://followup.dr-manoj.in/wa-webhook` reach the service on `127.0.0.1:8095`, via the existing CyberPanel/OpenLiteSpeed site for `followup.dr-manoj.in` (reverse proxy). We'll do this in the panel together; the SSL is already there.
- Test from your phone's browser: open `https://followup.dr-manoj.in/` → `wa_receiver alive`.

## Step 8 — Point MyOperator at it
In **Webhooks v2**, add:
- URL: `https://followup.dr-manoj.in/wa-webhook?key=<your WA_WEBHOOK_SECRET>`
- Event: **message received** (inbound).
- Save.

## Step 9 — Live test + confirm the field map
- Send a WhatsApp from your own phone to the clinic number (9358008080).
- Within a few seconds, a new row should appear in **WA_Inbox**, and the dashboard's **Recent WhatsApp** panel should show it after the next refresh.
- Also check `wa_logs/<today>.jsonl` — it has the raw message. If any column came out blank, send me **one raw line with the phone digits masked** and I'll adjust the field map (the exact MyOperator field names are confirmed against a real message at this step).

---

## Good to know
- **Nothing is lost:** every push is written to the raw log first, even if the sheet write hiccups.
- **No duplicates:** re-delivered pushes are skipped by message id.
- **Private:** the raw logs hold patient numbers/messages — keep the `wa/` folder owner-only.
- **Manual stays intact:** this only adds an inbox feed; it sends nothing and changes no existing workflow.
- **Sending replies is a separate, later step** (and we agreed to build/test that but hold deployment).
