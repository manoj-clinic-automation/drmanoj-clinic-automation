# Dr. Manoj Agarwal Clinic — Automation Handoff Runbook v9
**Session 9 close · 27 Jun 2026 (late evening IST) · for Session 10**

Read this first, then `obd/OBD_ClickToCall_WORKING_Recipe_27Jun2026.md`, then
`CARRYOVER_Session9_to_10_27Jun2026.md`. Older runbooks are in `prev_runbooks/`.

---

## 0. HOW TO WORK WITH THE DOCTOR (strict — do not drift)
- **Plain language.** No assumed coding knowledge. Terminal = "black window";
  a command = "a line of text you type and press Enter."
- **Full-file replacements**, never diffs/partial edits.
- **One step at a time**, wait for confirmation before the next.
- **ALL-CAPS from the doctor = urgent.**
- **Never print real tokens, secrets, or patient phone numbers** — always mask
  (`sed -E 's/(=.{5}).*/\1…(hidden)/'`, never `cat` a secret file).
- **Never rebuild live components.** Manual workflow always stays as fallback.
- **Large files: deliver as downloads** (present_files), not inline blobs.
- **VPS terminal MANGLES large pastes** (drops/merges lines — proven twice this
  session, on a heredoc AND on short-line base64). ⇒ **Install files via WinSCP
  upload**, then verify with `md5sum` + `py_compile`. Only short single-line
  commands are paste-safe. The doctor's WinSCP is configured (id_ed25519 → .ppk).

## 1. WHAT THIS PROJECT IS
Clinic automation for an orthopedic surgeon (Bareilly; older, Hindi-first,
semi-urban patients). Stack: **MyOperator IVR + WhatsApp Business API (WABA)** +
**Google Apps Script callback dashboard** + **Hostinger VPS** + **Google Sheets**
data layer. EMR is **Docterz** (closed, CSV-only, no webhooks).

## 2. INFRASTRUCTURE CONSTANTS
- MyOperator Company ID `68384350414b9847` · WABA ID `2101222617483538` ·
  Phone Number ID `1090067637530949` · IVR DID `8065293652` (Bangalore) ·
  WABA number `9358008080`.
- VPS `followup.dr-manoj.in`, IP `93.127.195.49`, server `srv1746119`, **root** login.
  Stack: Hostinger + CyberPanel + OpenLiteSpeed + gunicorn. Work dir `/root/wa`,
  venv `/root/wa/venv` (Flask, gspread, google-auth, gunicorn). TZ Asia/Kolkata.
  `cp` is aliased to `cp -i` → use `\cp -f` to overwrite.
- Google Sheet "Clinic Callback Tracker" ID `1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0`.
  Service account `patient-mirror@sincere-octane-500413-v8.iam.gserviceaccount.com`.
- Dashboard live `/exec` (v12: media render + WhatsApp tap-to-jump), gated `?k=KEY`
  (DASH_KEY). **Keep URL stable: edit existing deployment → New version. Never new deployment.**
- GitHub repo `drmanoj-clinic-automation` (branch `main`, local `D:\dr-manoj-git\drmanoj-clinic-automation`).
- Notion "Clinic HQ": main page `38618b9d-8f91-813e-9773-c20f567fd32f`;
  Tech & Systems Register `collection://e2e5e030-efc6-41a3-8f8a-70e808aaa5cb`.

## 3. LIVE COMPONENTS — DO NOT REBUILD
- Dashboard v12 (Apps Script).
- VPS receiver `wa_receiver.py` (inbound WA → `WA_Inbox` tab; captures media S3 links).
- VPS send relay `wa_send_api.py` / `wa_send.py` (outbound replies, `direction=out` rows;
  gated by `SEND_API_SECRET`).
- Daily Docterz→MyOperator campaign converter (`converter/docterz_to_myoperator.py`).
- **NEW this session — `wa-notifier` service** (see §4).

## 4. NEW & LIVE THIS SESSION (Session 9)
### 4a. WhatsApp → ntfy notifier  ✅ LIVE
- `wa-notifier.service` running on VPS (`active` + `enabled`, auto-restart, survives reboot).
- `notifier/notifier_wa.py` — read-only watcher: polls `WA_Inbox` every 30s, resolves
  patient NAME from `Patient_Master` (last-10-digit key, same as dashboard), pushes a
  **NAME-ONLY** alert to ntfy. Privacy: no number, no message text, no diagnosis.
  Skips outbound (`direction=out`) rows. Baselines on first run (never floods).
- ntfy topic `drmka-yfv80gjcixa643` on `https://ntfy.sh`. Phone (Android ✓) and the
  Shavez/reception PC (Chrome PWA at ntfy.sh/app, subscribed + Allowed) both fire.
- **Proven:** test WhatsApp → Android buzzed + PC toast popped.
- **Privacy follow-up (later):** self-host ntfy on the VPS for full privacy (needs Web
  Push/VAPID for the PWA). For now public ntfy.sh with name-only payloads is the agreed start.

### 4b. OBD Click-to-Call  ✅ PROVEN (recipe locked)
See `obd/OBD_ClickToCall_WORKING_Recipe_27Jun2026.md`. Both legs rang. The 4 OBD
credentials are in `/root/wa/.env` (chmod 600). Test tool `/root/wa/obd_test.py` kept.

## 5. NEXT BUILD (Session 10 priority) — the /call endpoint
Goal: dashboard "Call" buttons place real MyOperator OBD calls (logged, recorded,
IVR-tied) instead of `tel:` dialer calls, and auto-clear the callback list.
1. **VPS:** add a gated `POST /call` (mirror the `/wa-send` relay pattern; can extend
   `wa_send_api.py` or a tiny new service). Holds OBD secrets in `.env`. Accepts
   `{agent, patient_number, reference_id}` behind header `X-Call-Key` (new
   `CALL_API_SECRET`, mirrored in Apps Script Script Properties). Builds the body per
   the locked recipe (E.164 number, integer max_call_duration, panel-hex user_id from
   the agent map, unique reference_id) and POSTs to obd-api-v1. Returns `unique_id`.
   Install via WinSCP; verify md5 + py_compile; keep a `.bak` of any edited live file.
2. **Apps Script (`dashboard/WebApp.gs`):** `triggerCall(agent, number, rowId)` →
   `UrlFetchApp` to VPS `/call` with the call key (secret server-side only). Log attempt.
   Deploy via **New version of the existing deployment** (URL must stay stable).
3. **Dashboard (`dashboard/Dashboard.html`):** change Call buttons from `tel:` to
   `onclick=placeCall(...)` → `google.script.run.triggerCall(...)`; show "ringing your
   phone…" toast; note the queued delay.
4. **Loop close:** match the `reference_id` back from Call_Feed/logs to mark the patient
   "called" → dashboard drops the row from everyone's "Needs callback now."
5. **Test ladder:** curl `/call` for the doctor → one dashboard button → all buttons.

## 6. NOTIFICATION ROADMAP (after Trigger 1, which is done)
- Reception PC ntfy PWA setup if it's a separate machine (4 taps: ntfy.sh/app →
  subscribe `drmka-yfv80gjcixa643` → Allow → Windows notifications on / Focus off).
- **Trigger 2 — overdue-callback nudge:** needs the pending-callback count. Best as a
  tiny read-only counts action on the Apps Script dashboard (single source of truth;
  deploy via New version), then a second watcher/branch pushes "N callbacks pending."
- Desktop always-on-top counter widget (install-once app on staff PCs).

## 7. OTHER PENDING (carried, not started)
- **GitHub sync:** commit Session 8 + 9 files (see CARRYOVER for the exact file→folder map).
- **Notion Clinic HQ:** mark OBD = WORKING, notifier = LIVE (being done at handoff).
- **WhatsApp token rotation:** the `Bearer` "Authentication" token has had on-screen
  exposure; rotation needs coordinated timing with Lokesh (regenerating breaks live
  panel call automations within ~24h). Plan, don't do impromptu. See `token_rotation/`.
- **MyOperator contacts upload merge behavior:** verify with a 2-row test before any
  bulk upload (update vs duplicate; tags additive vs replaced).

## 8. KEY API FACTS (full refs in api/)
- **WhatsApp send:** `POST https://publicapi.myoperator.co/chat/messages`,
  header **capital** `Authorization: Bearer <token>` + `X-MYOP-COMPANY-ID`. Lowercase
  `bearer` → AWS IAM explicit-deny 401. Vars are numeric string keys `"1"`,`"2"`. Token
  = WhatsApp APIs "Authentication" (lHCx…), VPS `.env` only.
- **OBD calling:** see the WORKING recipe (the authoritative doc now).
- **Call/Logs:** `POST https://developers.myoperator.co/search` with `token` (3f76…).
  Recordings via the recordings ref. Nanosecond timestamps need trimming to ≤6 frac
  digits for Python 3.9 `fromisoformat()`.
- **No inbound pull endpoint** — inbound WA only via Webhooks v2 push → the VPS receiver.

## 9. CURRENT STATE — ONE LINE
Notifier LIVE (phone+PC). OBD calling PROVEN & recipe locked. VPS clean & secured
(.env chmod 600). Next: build the gated `/call` endpoint + wire dashboard Call buttons.
