#!/usr/bin/env python3
"""
wa_send_api.py - tiny send relay for the dashboard "Reply" box.
Dr. Manoj Agarwal Clinic.

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
          -- returns the guard's JSON result to the dashboard

  This service NEVER holds or prints the WhatsApp token. It only knows its own
  gate secret (SEND_API_SECRET), which authorises "ask the VPS to send a guarded
  reply" and nothing else - it cannot read patient records or call logs.

WHY A SEPARATE SERVICE (not added to wa_receiver.py)
  The inbound receiver is live and must not be touched. This runs as its own
  process on its own port (8096) with its own systemd unit, so the receiver
  stays exactly as it is.

ENDPOINTS  (all under /wa-send, because that is the path the proxy forwards)
  GET  /wa-send         -> health check (no secret): {"status":"alive"}
  GET  /wa-send/check    -> window check (needs key + number): is the 24h window
                            open for this number? (no send)
  POST /wa-send         -> guarded send (needs key; JSON body
                            {"number": "...", "message": "...", "reply_to": null})

SECURITY
  - Gate: every real call must carry the secret, as header X-Send-Key:<secret>
    (preferred - stays out of access logs) or ?key=<secret>. Wrong/absent -> 403.
    Fail-closed: if no secret is configured at all, every guarded call is refused.
  - The WhatsApp token is handled entirely inside wa_send.py; this file never
    sees it.
  - The 24-hour WhatsApp window is enforced by send_with_guard (it reads
    WA_Inbox). Out-of-window -> it refuses and says "use a template".
  - Logs go ONLY to the systemd journal (journalctl -u wa-send-api) and record
    the last-10 digits + outcome, never the message text and never any token.

CONFIG  (/root/wa/.env  - the same file the receiver already uses)
  SEND_API_SECRET   (required) the gate secret for this relay
  (WhatsApp + Sheet config is read by wa_send.py from /root/wa/.env and
   /root/wa/wa_send.env, exactly as the wa_send.py CLI already uses it.)

RUN
  Production:  gunicorn -w 1 -b 127.0.0.1:8096 --timeout 60 wa_send_api:app
               (via the wa-send-api.service systemd unit)
  Quick test:  python wa_send_api.py      (Flask's built-in server on 8096)

DEPENDENCIES  (already present in /root/wa/venv)
  Flask, plus whatever wa_send.py needs (gspread, google-auth).
"""

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


app = Flask(__name__)


@app.get("/wa-send")
def health():
    return jsonify({"service": "wa_send_api", "status": "alive"}), 200


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
    _log("send", last10(number),
         "open=%s" % result.get("window_open"),
         "sent=%s" % result.get("sent"),
         "http=%s" % result.get("http_status"))
    # HTTP is always 200 here; the JSON 'sent'/'ok'/'reason' carry the real
    # outcome so the dashboard can show a precise, friendly message.
    return jsonify(result), 200


if __name__ == "__main__":
    # Local quick test only; production uses gunicorn via systemd.
    app.run(host="127.0.0.1", port=8096)
