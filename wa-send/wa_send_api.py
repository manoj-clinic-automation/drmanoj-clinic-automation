#!/usr/bin/env python3
"""
wa_send_api.py - tiny send relay for the dashboard "Reply" box.
Dr. Manoj Agarwal Clinic.

VERSION: v2 (26 Jun 2026) - now LOGS each sent reply back into WA_Inbox as a
         direction="out" row, so the dashboard can show the conversation thread.
         Everything else is unchanged from the proven v1.

WHAT IT DOES
  A small always-on web service that lets the Google dashboard send a WhatsApp
  free-text reply WITHOUT the WhatsApp token ever leaving this VPS.

  Flow:
    Dashboard (Apps Script)  --HTTPS POST, header X-Send-Key: SEND_API_SECRET-->
      https://followup.dr-manoj.in/wa-send
        -- OpenLiteSpeed proxy --> 127.0.0.1:8096 (this service)
          -- calls send_with_guard() from the already-proven wa_send.py
             (which reads the WhatsApp token from wa_send.env, checks the
              24-hour window against WA_Inbox, and only then sends)
          -- on success, appends an "out" row to WA_Inbox (best-effort)
          -- returns the guard's JSON result to the dashboard

  This service NEVER holds or prints the WhatsApp token. It only knows its own
  gate secret (SEND_API_SECRET).

WHY LOG OUTBOUND (v2)
  WA_Inbox was inbound-only, so a reply we sent vanished from view. Logging the
  sent text as a direction="out" row lets the dashboard render a real two-sided
  thread per number. The 24h-window guard in wa_send.py only ever looks at
  INCOMING rows (it skips direction startswith "out"), so these rows can never
  fool the window check. If the sheet write fails, the SEND still succeeded - we
  just report logged=false; the message already went out.

ENDPOINTS  (all under /wa-send)
  GET  /wa-send         -> health check (no secret): {"status":"alive"}
  GET  /wa-send/check    -> window check (needs key + number)
  POST /wa-send         -> guarded send (needs key; JSON {"number","message"})

SECURITY
  - Gate: header X-Send-Key:<secret> (preferred) or ?key=<secret>. Else 403.
    Fail-closed: no secret configured -> refuse every guarded call.
  - The WhatsApp token is handled entirely inside wa_send.py.
  - Logs go ONLY to the systemd journal; last-10 digits + outcome, never text/token.

RUN
  Production:  gunicorn -w 1 -b 127.0.0.1:8096 --timeout 60 wa_send_api:app
  Quick test:  python wa_send_api.py
"""

import datetime
import re
import sys
from flask import Flask, request, jsonify

# Reuse the proven sender. wa_send.py sits next to this file in /root/wa.
from wa_send import (
    load_config,
    send_with_guard,
    window_state,
    read_env_file,
    last10,
)

ENV_PATH = "/root/wa/.env"
MAX_MESSAGE_CHARS = 4000          # WhatsApp text cap is ~4096; stay safely under
NUMBER_RE = re.compile(r"^\d{10,13}$")
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def _secret():
    """Read the relay gate secret fresh from /root/wa/.env on each call."""
    try:
        return read_env_file(ENV_PATH).get("SEND_API_SECRET")
    except Exception:
        return None


def _key_ok():
    want = _secret()
    if not want:
        return False  # fail closed: no secret configured -> refuse everything
    got = request.headers.get("X-Send-Key") or request.args.get("key")
    return got == want


def _log(*parts):
    # systemd journal only (journalctl -u wa-send-api). Local + root-only.
    print("[wa_send_api]", *parts, file=sys.stderr, flush=True)


def log_outbound(cfg, number, message, message_id):
    """Append a direction='out' row to WA_Inbox so the dashboard thread shows the
    reply we just sent. Best-effort: any failure is logged and swallowed - the
    WhatsApp message has already been sent, so we must NOT fail the request.
    Returns True if the row was written, else False.

    The row is written in the tab's existing column order, matching the receiver:
      timestamp | phone | direction | type | message | message id | conversation id | status
    The 24h guard ignores 'out' rows, so this never affects window checks.
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(cfg["sa_key"], scopes=scopes)
        gc = gspread.authorize(creds)
        ws = gc.open_by_key(cfg["sheet_id"]).worksheet(cfg.get("tab", "WA_Inbox"))
        header = ws.row_values(1)
        now_iso = datetime.datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S") + "+05:30"
        fields = {
            "timestamp":       now_iso,
            "phone":           re.sub(r"\D", "", str(number)),
            "direction":       "out",
            "type":            "text",
            "message":         str(message or ""),
            "message id":      str(message_id or ""),
            "conversation id": "",
            "status":          "sent",
        }
        row = [fields.get(h.strip().lower(), "") for h in header]
        ws.append_row(row, value_input_option="RAW")
        return True
    except Exception as e:        # noqa: BLE001
        _log("outbound-log failed (send still ok):", repr(e))
        return False


app = Flask(__name__)


@app.get("/wa-send")
def health():
    return jsonify({"service": "wa_send_api", "status": "alive", "version": 2}), 200


@app.get("/wa-send/check")
def check():
    if not _key_ok():
        return jsonify({"ok": False, "reason": "forbidden"}), 403
    number = (request.args.get("number") or "").strip()
    if not NUMBER_RE.match(re.sub(r"\D", "", number)):
        return jsonify({"ok": False, "reason": "bad number"}), 400
    cfg = load_config()
    is_open, last_dt, age = window_state(cfg, number)
    return jsonify({
        "ok": True,
        "number": last10(number),
        "window_open": is_open,
        "last_inbound": last_dt.isoformat() if last_dt else None,
        "hours_since": round(age.total_seconds() / 3600, 1) if age else None,
    }), 200


@app.post("/wa-send")
def send():
    if not _key_ok():
        return jsonify({"ok": False, "reason": "forbidden"}), 403

    data = request.get_json(silent=True) or request.form or {}
    number = str(data.get("number") or "").strip()
    message = str(data.get("message") or "").strip()
    reply_to = data.get("reply_to") or None

    digits = re.sub(r"\D", "", number)
    if not NUMBER_RE.match(digits):
        return jsonify({"ok": False, "sent": False,
                        "reason": "Invalid number."}), 400
    if not message:
        return jsonify({"ok": False, "sent": False,
                        "reason": "Empty message."}), 400
    if len(message) > MAX_MESSAGE_CHARS:
        return jsonify({"ok": False, "sent": False,
                        "reason": "Message too long (max %d chars)." % MAX_MESSAGE_CHARS}), 400

    cfg = load_config()
    result = send_with_guard(cfg, number, message, reply_to=reply_to)

    # v2: if the send went out, log it as an outbound row so the thread shows it.
    if result.get("sent"):
        result["logged"] = log_outbound(cfg, digits, message, result.get("message_id"))

    _log("send", last10(number),
         "open=%s" % result.get("window_open"),
         "sent=%s" % result.get("sent"),
         "logged=%s" % result.get("logged"),
         "http=%s" % result.get("http_status"))
    # HTTP is always 200 here; the JSON 'sent'/'ok'/'reason' carry the real outcome.
    return jsonify(result), 200


if __name__ == "__main__":
    # Local quick test only; production uses gunicorn via systemd.
    app.run(host="127.0.0.1", port=8096)
