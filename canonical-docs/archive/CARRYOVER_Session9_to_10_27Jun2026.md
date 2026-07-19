# Carryover — Session 9 → Session 10 (27 Jun 2026)

## What Session 9 accomplished
1. **WhatsApp → ntfy notifier built, installed, and PROVEN live** (phone + PC).
   Service `wa-notifier` is `active`+`enabled` on the VPS. Read-only, name-only, private.
2. **OBD Click-to-Call PROVEN end-to-end** — both legs rang. The recipe is locked in
   `obd/OBD_ClickToCall_WORKING_Recipe_27Jun2026.md`. This cleared the project's
   #1 long-standing blocker.
3. Created the OBD campaign **"Clinic API Calling"**; captured its **Public IVR ID**
   into `/root/wa/.env`. Added all 4 OBD credentials to `.env` and set it `chmod 600`.
4. VPS tidied and secured.

## The debugging trail (so it's never re-fought)
OBD threw six different errors before success, each fixed:
- paste corruption on install → switched to **WinSCP** (terminal mangles big pastes).
- `Provide valid Number` → number must be **E.164 `+91…`** (not bare 10 or 12 digits).
- `reference ID already taken` → make `reference_id` **unique** per call.
- `instance type (string) … allowed integer` → `max_call_duration` must be **integer**.
- `Your annonymous feature is not enabled` → Anonymous Dialer disabled → use **User Dialer**.
- `Get Users 404 Unknown method` → User API unprovisioned → **panel-hex `user_id` works**, no uuid needed.
- final cause of "accepted but silent": calls are **queued** → ring after a delay.

## Files changed/created this session
- `notifier/notifier_wa.py`  (md5 feeea7efca7bbe3c02baa4ffd120de27)
- `notifier/wa-notifier.service`  (md5 9118efca8176043f771fa0aeb5cb9c16) → /etc/systemd/system/
- `obd/obd_test.py`  (final md5 036e1d942dfa425ac1edf5e9b47086a1) → /root/wa/
- `obd/get_users.py`  (md5 8aa05229a9464e1dfa54c6cc8f51c8a6, but User API is 404 on this plan — kept for reference only)
- `.env` gained: MYOP_OBD_XAPIKEY, MYOP_OBD_SECRET, MYOP_PUBLIC_IVR_ID, MYOP_LOGS_TOKEN

## GitHub commit map (Sessions 8 + 9 — pending)
Copy into the local repo `D:\dr-manoj-git\drmanoj-clinic-automation`, then commit.
Secrets/patient data stay gitignored — these files contain none.
| Repo folder | Files |
|---|---|
| `notifier/` (new) | notifier_wa.py, wa-notifier.service |
| `obd/` (new) | obd_test.py, get_users.py, OBD_ClickToCall_WORKING_Recipe_27Jun2026.md |
| `wa-receiver/` | wa_receiver.py, peek_media.py, check_link.py (Session 8) |
| `dashboard/` | WebApp.gs (v12), Dashboard.html (v12) (Session 8) |
| repo root `docs/` | HANDOFF_RUNBOOK_2026-06-27_v9.md, this carryover |

## Immediate next step in Session 10
Build the gated **`/call`** endpoint (runbook §5) using the locked recipe, then wire
the dashboard Call buttons. WinSCP for any file install; keep `.bak` of edited live files.
