#!/usr/bin/env python3
"""
wa_send_api.py - tiny send relay for the dashboard "Reply" box.
Dr. Manoj Agarwal Clinic.

VERSION: v3 (12 Jul 2026, Session 139) - adds POST /wa-send/template: a guarded,
         allow-listed APPROVED-TEMPLATE send for the K-1 3rd-strike message
         (D215/D216) and the seen-today message (D213). v2 behaviour unchanged.

WHAT IT DOES
  A small always-on web service that lets the Google dashboard send WhatsApp
  WITHOUT the WhatsApp token ever leaving this VPS.

  v2 (unchanged): free-text reply, 24h-window guarded by wa_send.py.
  v3 (new):       template send, OUTSIDE the window, but:
                    - template name must be on the ALLOW-LIST below
                    - per number+template: max ONE per day
                    - global across this endpoint: max 50 per day
                  Counters persist in /root/wa/wa_template_relay_counter.json.

ENDPOINTS  (all under /wa-send)
  GET  /wa-send           -> health check (no secret): {"status":"alive"}
  GET  /wa-send/check     -> window check (needs key + number)
  POST /wa-send           -> guarded free-text send (needs key)
  POST /wa-send/template  -> guarded template send   (needs key)   [v3]

SECURITY
  - Gate: header X-Send-Key:<secret> (preferred) or ?key=<secret>. Else 403.
    Fail-closed: no secret configured -> refuse every guarded call.
  - The WhatsApp Bearer token is read fresh per call; NEVER logged or returned.
    Resolution order (S137, API card): MYOP_AUTH_TOKEN in /root/wa/.env first,
    then wa_send.py's own load_config() chain.
  - Logs go ONLY to the systemd journal; last-10 digits + outcome, never text/token.

RUN
  Production:  gunicorn -w 1 -b 127.0.0.1:8096 --timeout 60 wa_send_api:app
  Quick test:  python wa_send_api.py
  Selftest  :  python wa_send_api.py --selftest   (offline; no key, no network)
"""

import datetime
import http.client
import json
import os
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

# ---------------------------- v3: template mode ------------------------------
API_HOST = "publicapi.myoperator.co"
API_PATH = "/chat/messages"
# Allow-list: template name -> tuple of REQUIRED numeric body keys (S137: the
# drmanoj_* family uses numeric string keys "1","2"; language "en").
TEMPLATE_ALLOW = {
    "drmanoj_followup_due": ("1", "2"),   # D216: the 3rd-strike message
    "drmanoj_post_visit":   ("1",),       # D213: seen-today (future A3 pass)
}
TPL_COUNTER_PATH = "/root/wa/wa_template_relay_counter.json"
TPL_GLOBAL_DAILY_CAP = 50                 # hard ceiling across this endpoint
# -----------------------------------------------------------------------------


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


def _waba_token(cfg):
    """S137: the live Bearer lives as MYOP_AUTH_TOKEN in /root/wa/.env.
    Fall back to wa_send.py's own chain so free-text and template can never
    disagree about which token exists."""
    try:
        tok = read_env_file(ENV_PATH).get("MYOP_AUTH_TOKEN")
        if tok:
            return tok
    except Exception:
        pass
    return cfg.get("token")


def _tpl_counter_load(today):
    try:
        with open(TPL_COUNTER_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
        if d.get("date") == today:
            return d
    except Exception:
        pass
    return {"date": today, "total": 0, "keys": {}}


def _tpl_counter_save(d):
    try:
        tmp = TPL_COUNTER_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f)
        os.replace(tmp, TPL_COUNTER_PATH)
    except Exception as e:  # noqa: BLE001
        _log("counter save failed:", repr(e))


def build_template_payload(cfg, number, template, body_vars):
    """Exact confirmed-200 shape (API card S137): numeric string keys, en."""
    return {
        "phone_number_id": cfg["phone_number_id"],
        "customer_country_code": cfg["country_code"],
        "customer_number": last10(number),
        "data": {
            "type": "template",
            "context": {
                "template_name": template,
                "language": "en",
                "body": body_vars,
            },
        },
        "reply_to": None,
        "myop_ref_id": None,
    }


def validate_template_request(number, template, raw_vars):
    """Pure validation (selftest-able). Returns (ok, reason, body_vars)."""
    digits = re.sub(r"\D", "", str(number or ""))
    if not NUMBER_RE.match(digits):
        return False, "Invalid number.", None
    if template not in TEMPLATE_ALLOW:
        return False, "Template not on the allow-list.", None
    need = TEMPLATE_ALLOW[template]
    raw_vars = raw_vars or {}
    body = {}
    for k in need:
        v = str(raw_vars.get(k, "") or "").strip()
        if not v:
            return False, "Missing template variable {{%s}}." % k, None
        if len(v) > 120:
            v = v[:120]
        body[k] = v
    return True, None, body


def check_caps(counter, digits, template):
    """Pure cap logic (selftest-able). Returns (ok, reason, dedupe_key)."""
    key = "%s|%s" % (digits[-10:], template)
    if counter["keys"].get(key):
        return False, "Already sent this template to this number today.", key
    if counter["total"] >= TPL_GLOBAL_DAILY_CAP:
        return False, "Daily template cap reached (%d)." % TPL_GLOBAL_DAILY_CAP, key
    return True, None, key


def send_template(cfg, number, template, body_vars):
    """POST the template message. Returns dict {sent, ok, message_id, http_status, reason}."""
    out = {"sent": False, "ok": False, "message_id": None,
           "http_status": None, "reason": None}
    token = _waba_token(cfg)
    if not token:
        out["reason"] = "No WhatsApp token configured."
        return out
    payload = build_template_payload(cfg, number, template, body_vars)
    headers = {
        "Authorization": "Bearer " + token,          # capital B required (S137)
        "X-MYOP-COMPANY-ID": cfg["company_id"],
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    conn = http.client.HTTPSConnection(API_HOST, timeout=30)
    try:
        conn.request("POST", API_PATH, json.dumps(payload), headers)
        res = conn.getresponse()
        status = res.status
        text = res.read().decode("utf-8", errors="replace")
    finally:
        try:
            conn.close()
        except Exception:
            pass
    out["http_status"] = status
    try:
        body = json.loads(text)
    except Exception:
        body = None
    if status == 200 and isinstance(body, dict) \
            and str(body.get("status", "")).lower() == "success":
        out["sent"] = True
        out["ok"] = True
        out["message_id"] = (body.get("data") or {}).get("message_id")
        out["reason"] = "Accepted."
    else:
        out["reason"] = "Send failed (HTTP %s)." % status
    return out


def log_outbound(cfg, number, message, message_id, msg_type="text"):
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
            "type":            msg_type,
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
    return jsonify({"service": "wa_send_api", "status": "alive", "version": 3}), 200


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


@app.post("/wa-send/template")
def send_template_route():
    """v3: guarded, allow-listed, capped APPROVED-TEMPLATE send (D216)."""
    if not _key_ok():
        return jsonify({"ok": False, "sent": False, "reason": "forbidden"}), 403

    data = request.get_json(silent=True) or request.form or {}
    number = str(data.get("number") or "").strip()
    template = str(data.get("template") or "").strip()
    raw_vars = data.get("vars") or {}

    ok, reason, body_vars = validate_template_request(number, template, raw_vars)
    if not ok:
        return jsonify({"ok": False, "sent": False, "reason": reason}), 400

    digits = re.sub(r"\D", "", number)
    today = datetime.datetime.now(IST).strftime("%Y-%m-%d")
    counter = _tpl_counter_load(today)
    ok, reason, dkey = check_caps(counter, digits, template)
    if not ok:
        _log("template REFUSED", last10(number), template, reason)
        return jsonify({"ok": False, "sent": False, "reason": reason}), 200

    cfg = load_config()
    result = send_template(cfg, number, template, body_vars)

    if result.get("sent"):
        counter["keys"][dkey] = 1
        counter["total"] += 1
        _tpl_counter_save(counter)
        result["logged"] = log_outbound(
            cfg, digits, "[template] " + template, result.get("message_id"),
            msg_type="template")

    _log("template", last10(number), template,
         "sent=%s" % result.get("sent"),
         "http=%s" % result.get("http_status"),
         "total_today=%s" % counter["total"])
    return jsonify(result), 200


def _selftest():
    """Offline logic checks: no key, no network, no sheet."""
    t = {"pass": 0, "fail": 0}

    def chk(name, cond):
        t["pass" if cond else "fail"] += 1
        print(("PASS" if cond else "FAIL"), name)

    ok, r, b = validate_template_request("9812345678", "drmanoj_followup_due",
                                         {"1": "Ram Kumar", "2": "12 Jul 2026"})
    chk("valid due request", ok and b == {"1": "Ram Kumar", "2": "12 Jul 2026"})
    ok, r, _ = validate_template_request("9812345678", "not_allowed", {"1": "x"})
    chk("allow-list refuses unknown", (not ok) and "allow-list" in r)
    ok, r, _ = validate_template_request("12345", "drmanoj_followup_due", {"1": "x", "2": "y"})
    chk("bad number refused", not ok)
    ok, r, _ = validate_template_request("9812345678", "drmanoj_followup_due", {"1": "x"})
    chk("missing var refused", (not ok) and "{{2}}" in r)
    ok, r, b = validate_template_request("919812345678", "drmanoj_post_visit", {"1": "Sita"})
    chk("post_visit single var ok", ok and b == {"1": "Sita"})

    c = {"date": "2026-07-12", "total": 0, "keys": {}}
    ok, r, k = check_caps(c, "9812345678", "drmanoj_followup_due")
    chk("fresh number passes caps", ok and k == "9812345678|drmanoj_followup_due")
    c["keys"][k] = 1
    ok, r, _ = check_caps(c, "919812345678", "drmanoj_followup_due")
    chk("same number+template same day refused", (not ok) and "Already" in r)
    ok, r, _ = check_caps(c, "9812345678", "drmanoj_post_visit")
    chk("other template same number allowed", ok)
    c2 = {"date": "2026-07-12", "total": TPL_GLOBAL_DAILY_CAP, "keys": {}}
    ok, r, _ = check_caps(c2, "9000000000", "drmanoj_followup_due")
    chk("global cap enforced", (not ok) and "cap" in r)

    cfg = {"phone_number_id": "1090067637530949", "country_code": "91",
           "company_id": "x", "token": "t"}
    p = build_template_payload(cfg, "919812345678", "drmanoj_followup_due",
                               {"1": "Ram", "2": "12"})
    chk("payload shape = confirmed-200 body",
        p["customer_number"] == "9812345678"
        and p["data"]["type"] == "template"
        and p["data"]["context"]["template_name"] == "drmanoj_followup_due"
        and p["data"]["context"]["language"] == "en"
        and p["data"]["context"]["body"] == {"1": "Ram", "2": "12"}
        and p["myop_ref_id"] is None and p["reply_to"] is None)

    print("SELFTEST: %d pass / %d fail" % (t["pass"], t["fail"]))
    return t["fail"] == 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if _selftest() else 1)
    # Local quick test only; production uses gunicorn via systemd.
    app.run(host="127.0.0.1", port=8096)
