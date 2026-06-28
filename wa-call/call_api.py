#!/usr/bin/env python3
"""
call_api.py — gated VPS relay that places a MyOperator OBD "click-to-call".
Dr. Manoj Agarwal Clinic.

VERSION: v1 (28 Jun 2026)

WHAT IT DOES (in plain words)
  A small always-on web service. When an agent taps "Call" on the Google
  dashboard, the dashboard sends one HTTPS request here. This service then asks
  MyOperator to ring THAT AGENT'S OWN MOBILE first; when the agent picks up,
  MyOperator dials the patient and bridges the two. The call is logged by
  MyOperator AS THAT AGENT'S CALL (because we send the agent's panel user_id).

  This is the "User Dialer" flow — the exact recipe that was proven working on
  27 Jun 2026 (obd_test.py). This file just reproduces that recipe server-side,
  behind a secret gate, so the dashboard can trigger it without ever holding any
  MyOperator secret.

  Flow:
    Dashboard (Apps Script)
      --HTTPS POST, header X-Call-Key: CALL_API_SECRET-->
        https://followup.dr-manoj.in/call
          -- OpenLiteSpeed proxy --> 127.0.0.1:8097 (this service)
            -- builds the locked OBD body (E.164 number, integer duration,
               agent's panel-hex user_id, a UNIQUE reference_id)
            -- POSTs to https://obd-api.myoperator.co/obd-api-v1
            -- returns {ok, accepted, unique_id, reference_id} to the dashboard

  WALLED OFF FROM WHATSAPP: this is its own service on its own port (8097). It
  does NOT import or touch the live WhatsApp send relay / receiver. A bug here
  can never take WhatsApp messaging down.

SECRETS (read fresh from /root/wa/.env on each call; never printed)
  CALL_API_SECRET     — this service's own gate secret (the dashboard's key)
  MYOP_OBD_SECRET     — OBD secret_token (real secret)
  MYOP_OBD_XAPIKEY    — OBD x-api-key (shared client key; harmless but kept in env)
  MYOP_PUBLIC_IVR_ID  — the "Clinic API Calling" campaign Public IVR ID
  (COMPANY_ID is a non-secret constant, embedded below.)

ENDPOINTS (all under /call)
  GET  /call            -> health check (no secret): {"status":"alive"}
  POST /call            -> place a call (needs key; JSON {agent, patient_number, reference_id})

SECURITY
  - Gate: header X-Call-Key:<secret> (preferred) or ?key=<secret>. Else 403.
    Fail-closed: if no secret is configured in .env, every call is refused.
  - Dialed-as identity comes from EITHER a known agent ext/name (resolved
    against the built-in map) OR an explicit user_id. The dashboard derives
    that user_id SERVER-SIDE from the Agents roster + the logged-in agent's
    key (never from the page), so a newly-added agent works with no edit
    here. A user_id is accepted only past the gate and only if it matches
    the panel-hex shape (alnum 8-40).
  - Logs go ONLY to the systemd journal: agent + patient last-4 + outcome.
    Never the full number, never any secret.

RUN
  Production:  gunicorn -w 1 -b 127.0.0.1:8097 --timeout 60 call_api:app
  Quick test:  python call_api.py
"""

import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

from flask import Flask, jsonify, request

# ---------------------------------------------------------------------------
# Constants (non-secret)
# ---------------------------------------------------------------------------
ENV_PATH = os.environ.get("CALL_ENV_PATH", "/root/wa/.env")
COMPANY_ID = "68384350414b9847"
OBD_URL = "https://obd-api.myoperator.co/obd-api-v1"
MAX_CALL_DURATION = 300          # integer, per the locked recipe (must NOT be a string)
VALID_USER_ID = re.compile(r"^[A-Za-z0-9]{8,40}$")   # panel hex id shape
CALL_HOLD = True
HTTP_TIMEOUT = 30                # seconds; OBD returns "accepted" quickly (call is queued)
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# Agent map (panel hex user_id — NOT secret; it is in the OBD recipe doc).
# Keyed for resolution by BOTH extension and name, so the dashboard can send
# whichever it already knows.
#   ext : (display_name, user_id_hex, mobile_last4)
AGENTS = {
    "10": ("Dr Manoj Agarwal",   "6838435041f29988", "4044"),
    "11": ("Shavez Ahmed",       "686cf49a692bb162", "4926"),
    "12": ("Shivani Srivastava", "686cf557c4f09495", "9246"),
    "13": ("Manoj Bhati",        "686cf5a29a97d527", "4408"),
    "14": ("Alisha Khan",        "69cfa941359e1649", "3474"),
    "15": ("Darpan Robert",      "6a2017dd50280597", "5546"),
    "16": ("Reception Mobile",   "6a2018cda8975829", "4080"),
}


# ---------------------------------------------------------------------------
# .env loader (tiny, local — keeps this service self-contained / walled off)
# ---------------------------------------------------------------------------
def read_env(path=ENV_PATH):
    """Return a dict of KEY=value pairs from the .env file. Missing file -> {}."""
    out = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _norm_name(s):
    """Lowercase, collapse spaces — for tolerant name matching."""
    return re.sub(r"\s+", " ", str(s or "").strip().lower())


# Build a name-> ext lookup once (normalized).
_NAME_TO_EXT = {_norm_name(v[0]): ext for ext, v in AGENTS.items()}


def resolve_agent(agent):
    """Accept an extension ('10'..'16') OR an agent name. Return
    (ext, name, user_id) or None if it doesn't match a known clinic agent."""
    if agent is None:
        return None
    a = str(agent).strip()
    # Try extension first (exact, allowing a stray '+' or 'ext' prefix to be ignored)
    ext_digits = re.sub(r"\D", "", a)
    if ext_digits in AGENTS:
        name, uid, _ = AGENTS[ext_digits]
        return ext_digits, name, uid
    # Then try name (tolerant)
    ext = _NAME_TO_EXT.get(_norm_name(a))
    if ext:
        name, uid, _ = AGENTS[ext]
        return ext, name, uid
    return None


def e164_in(number):
    """Force an Indian number to E.164 (+91 + last 10 digits).
    Returns (e164_str, ten_digits). ten_digits is '' if not exactly 10."""
    ten = re.sub(r"\D", "", str(number or ""))[-10:]
    if len(ten) != 10:
        return None, ""
    return "+91" + ten, ten


def make_reference_id(base):
    """A reference_id that is GUARANTEED unique per call (the OBD API locks a
    repeated reference_id for ~2 days). We keep the dashboard's row id as the
    readable prefix, then append epoch seconds + 4 random hex chars.
    The dashboard stores the FULL value we return, to match it back from the
    call logs later (auto-clear the callback row)."""
    safe = re.sub(r"[^A-Za-z0-9_-]", "", str(base or ""))[:32] or "cb"
    suffix = "%d%s" % (int(time.time()), os.urandom(2).hex())
    return "%s-%s" % (safe, suffix)


def build_body(user_id, patient_e164, reference_id, secret, ivr_id):
    """Construct the EXACT locked OBD body (User Dialer, type '1').
    Pure function — no network — so it is easy to unit-test."""
    return {
        "company_id": COMPANY_ID,
        "secret_token": secret,
        "type": "1",                       # User Dialer
        "number": patient_e164,            # E.164, e.g. +919389559274
        "public_ivr_id": ivr_id,
        "user_id": user_id,                # agent's panel hex -> logged as that agent
        "reference_id": reference_id,      # unique per call
        "max_call_duration": MAX_CALL_DURATION,   # INTEGER 300, not a string
        "call_hold": CALL_HOLD,
    }


def place_obd_call(body, xapikey):
    """POST the body to the OBD API. Returns (http_status, parsed_json_or_text).
    Network call kept separate so the endpoint flow can be tested with it mocked."""
    req = urllib.request.Request(
        OBD_URL, data=json.dumps(body).encode("utf-8"), method="POST")
    req.add_header("x-api-key", xapikey)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            raw = r.read().decode("utf-8")
            status = r.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        status = e.code
    try:
        return status, json.loads(raw)
    except Exception:  # noqa: BLE001
        return status, {"raw": raw}


def _log(*parts):
    """systemd journal only (journalctl -u call-api). No numbers in full, no secrets."""
    print("[call_api]", *parts, file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__)


def _key_ok():
    want = read_env().get("CALL_API_SECRET")
    if not want:
        return False  # fail closed: no secret configured -> refuse everything
    got = request.headers.get("X-Call-Key") or request.args.get("key")
    return got == want


@app.get("/call")
def health():
    return jsonify({"service": "call_api", "status": "alive", "version": 1}), 200


@app.post("/call")
def call():
    if not _key_ok():
        return jsonify({"ok": False, "reason": "forbidden"}), 403

    data = request.get_json(silent=True) or request.form or {}
    agent_in = data.get("agent")
    user_id_in = str(data.get("user_id") or "").strip()
    number_in = data.get("patient_number") or data.get("number")
    ref_in = data.get("reference_id") or data.get("rowId") or ""

    # Identity (both forms only reachable past the X-Call-Key gate):
    #   1) explicit user_id from the dashboard (derived server-side from the
    #      Agents roster + the agent's login key) -> lets new agents work
    #      with no change here; accepted only if it is panel-hex shaped; or
    #   2) an agent extension / name resolved against the built-in map.
    resolved = resolve_agent(agent_in)
    if user_id_in and VALID_USER_ID.match(user_id_in):
        user_id = user_id_in
        if resolved:
            ext, agent_name, _ = resolved          # enrich label if ext known
        else:
            ext = re.sub(r"\D", "", str(agent_in or ""))[:4] or "?"
            agent_name = "agent"
    elif resolved:
        ext, agent_name, user_id = resolved
    else:
        return jsonify({"ok": False, "reason": "Unknown agent. Send the agent's "
                        "extension (10-16), exact name, or a valid user_id."}), 400

    # Patient number -> E.164.
    patient_e164, ten = e164_in(number_in)
    if not ten:
        return jsonify({"ok": False, "reason": "Patient number must be 10 digits."}), 400

    # Secrets / config (fail clearly if the VPS isn't configured, without leaking which).
    env = read_env()
    secret = env.get("MYOP_OBD_SECRET", "").strip()
    xapikey = env.get("MYOP_OBD_XAPIKEY", "").strip()
    ivr_id = env.get("MYOP_PUBLIC_IVR_ID", "").strip()
    if not (secret and xapikey and ivr_id):
        _log("config-missing: one of MYOP_OBD_SECRET/XAPIKEY/PUBLIC_IVR_ID absent")
        return jsonify({"ok": False, "reason": "Calling not configured on server."}), 500

    reference_id = make_reference_id(ref_in)
    body = build_body(user_id, patient_e164, reference_id, secret, ivr_id)

    status, resp = place_obd_call(body, xapikey)
    accepted = (status == 200 and str(resp.get("status", "")).lower() == "success")
    unique_id = resp.get("unique_id")

    _log("call", "ext=%s" % ext, "agent=%s" % agent_name,
         "patient=...%s" % ten[-4:], "http=%s" % status,
         "accepted=%s" % accepted, "ref=%s" % reference_id)

    out = {
        "ok": accepted,
        "accepted": accepted,
        "http_status": status,
        "agent": agent_name,
        "agent_ext": ext,
        "reference_id": reference_id,
        "unique_id": unique_id,
    }
    if not accepted:
        # Surface MyOperator's own message so we can see why (no secret is in it).
        out["reason"] = resp.get("details") or resp.get("message") or resp.get("raw") \
            or "OBD request not accepted."
    # HTTP is always 200 from us; the JSON 'ok'/'accepted'/'reason' carry the outcome.
    return jsonify(out), 200


if __name__ == "__main__":
    # Local quick test only; production uses gunicorn via systemd.
    app.run(host="127.0.0.1", port=8097)
