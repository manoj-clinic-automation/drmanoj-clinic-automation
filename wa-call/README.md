# wa-call — click-to-call relay (OBD)

A small, self-contained Flask service that lets the dashboard's **Call** buttons
place a real outbound (OBD) call through MyOperator, dialed-as the logged-in agent.
Walled off from WhatsApp — its own service, own port.

## Files
- `call_api.py` — the relay. Gated by header `X-Call-Key` (must equal `CALL_API_SECRET`
  in `/root/wa/.env`; fail-closed). Accepts an agent ext/name OR a panel `user_id`
  (the dashboard sends the user_id from the Agents roster). Forces the number to
  `+91XXXXXXXXXX`, generates a unique `reference_id` per call, sends `max_call_duration`
  as the integer 300, `call_hold: true`. Reads all OBD secrets fresh from `.env`.
  Logs only: agent + patient last-4 + outcome (never the full number, never a secret).
- `call-api.service` — systemd unit; gunicorn -w 1 -b 127.0.0.1:8097.
- `call_api_proxy_block.txt` — the OpenLiteSpeed context block that exposes it at
  `https://followup.dr-manoj.in/call`.
- `insert_call_proxy.py` — one-off helper that inserts that block into the live
  vhost.conf safely (idempotent; writes a .new file for review before swapping).

## Secrets (NOT in this repo)
`CALL_API_SECRET`, `MYOP_OBD_SECRET`, `MYOP_OBD_XAPIKEY`, `MYOP_PUBLIC_IVR_ID`
live only in `/root/wa/.env` on the VPS (chmod 600).

## Port / endpoint
- Local: `127.0.0.1:8097`
- Public (via OpenLiteSpeed): `POST https://followup.dr-manoj.in/call`
- Health: `GET /call` → `{"ok": true, ...}`
