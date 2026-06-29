"""
waba.py — MyOperator WhatsApp Business API client for the Follow-Up Tracker.

This is the *send arm* of the existing tracker. It does ONE thing: take a
patient + a template name + variables, and send an approved WABA template via
MyOperator's public API — with strict error handling (especially wallet-empty),
phone validation, and a structured result the batch driver can log.

Nothing here reads the ledgers; send_followups.py does that and calls send_template().

Config comes from environment variables (never hard-code the token):
    MYOP_BASE_URL          https://publicapi.myoperator.co
    MYOP_COMPANY_ID        68384350414b9847
    MYOP_PHONE_NUMBER_ID   1090067637530949
    MYOP_WABA_ID           2101222617483538          (not needed to send, kept for reference)
    MYOP_AUTH_TOKEN        <the WhatsApp APIs "Authentication" Bearer value>  (SECRET)
    MYOP_COUNTRY_CODE      91                          (optional, default 91)
    WABA_TEMPLATE_BODY_FORMAT   var_n | varn | numeric | list   (default numeric — confirmed working 16 Jun 2026)

The exact JSON shape for *template body variables* is the one thing the
MyOperator collection does not show with a real example, so it is isolated in
_build_body() and switchable via WABA_TEMPLATE_BODY_FORMAT. Run waba_probe.py
once to confirm which format your account accepts, then leave it set.
"""

from __future__ import annotations
import os
import re
import json
import time
import urllib.request
import urllib.error
from pathlib import Path


def _load_dotenv() -> None:
    """Read .env from this folder so the token comes from a file (reliable),
    not a hand-typed `set` command (which can add trailing spaces/truncate).
    The file wins over shell vars; obvious placeholders are ignored."""
    p = Path(__file__).resolve().parent / ".env"
    if not p.exists():
        return
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if not v or "PASTE_" in v or "_HERE" in v:
                continue
            os.environ[k] = v
    except Exception:
        pass


_load_dotenv()


# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL        = os.environ.get("MYOP_BASE_URL", "https://publicapi.myoperator.co").rstrip("/")
COMPANY_ID      = os.environ.get("MYOP_COMPANY_ID", "")
PHONE_NUMBER_ID = os.environ.get("MYOP_PHONE_NUMBER_ID", "")
WABA_ID         = os.environ.get("MYOP_WABA_ID", "")
AUTH_TOKEN      = os.environ.get("MYOP_AUTH_TOKEN", "")
COUNTRY_CODE    = os.environ.get("MYOP_COUNTRY_CODE", "91")
BODY_FORMAT     = os.environ.get("WABA_TEMPLATE_BODY_FORMAT", "numeric")
SEND_PATH       = "/chat/messages"

# Error codes from the MyOperator collection that must STOP a whole batch.
FATAL_CODES = {
    "CHAT_4001": "Insufficient wallet balance",
    "CHAT_0302": "WABA is disabled",
    "CHAT_0303": "Phone number is disabled",
    "CHAT_0304": "Phone number is not connected",
}


# ── Exceptions ────────────────────────────────────────────────────────────────
class WabaConfigError(Exception):
    """Missing/invalid configuration."""


class WabaFatalError(Exception):
    """A condition that must halt the entire run (e.g. empty wallet)."""
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


# ── Phone helpers ─────────────────────────────────────────────────────────────
_TEN_DIGIT = re.compile(r"^[6-9]\d{9}$")


def normalize_mobile(raw: str) -> str | None:
    """Return a clean 10-digit Indian mobile, or None if not valid.

    Accepts inputs like '9837046634', '+919837046634', '0919837046634',
    '91 98370 46634' and strips to the trailing 10 digits.
    """
    if raw is None:
        return None
    digits = re.sub(r"\D", "", str(raw))
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    if len(digits) == 10 and _TEN_DIGIT.match(digits):
        return digits
    return None


# ── Payload construction ──────────────────────────────────────────────────────
def _build_body(variables: list[str]) -> dict | list:
    """Build the template 'body' parameter in the configured format.

    The MyOperator collection shows template sends but not a real variable
    example, so we keep all known shapes here and pick one via env.
    Templates are registered with numbered placeholders {{1}}, {{2}}, {{3}};
    variables[] must be in that order.
    """
    if BODY_FORMAT == "var_n":      # {"var_1": "...", "var_2": "..."}
        return {f"var_{i}": v for i, v in enumerate(variables, 1)}
    if BODY_FORMAT == "varn":       # {"var1": "...", "var2": "..."}
        return {f"var{i}": v for i, v in enumerate(variables, 1)}
    if BODY_FORMAT == "numeric":    # {"1": "...", "2": "..."}
        return {str(i): v for i, v in enumerate(variables, 1)}
    if BODY_FORMAT == "list":       # [{"type":"text","text":"..."}]
        return [{"type": "text", "text": v} for v in variables]
    raise WabaConfigError(f"Unknown WABA_TEMPLATE_BODY_FORMAT: {BODY_FORMAT}")


def build_payload(mobile10: str, template_name: str, variables: list[str],
                  language: str = "en", myop_ref_id: str | None = None) -> dict:
    """Assemble the /chat/messages request body for a template send.

    Static buttons (Call, Book Appointment) are baked into the approved
    template, so no 'buttons' field is needed here.
    """
    context = {"template_name": template_name, "language": language}
    if variables:
        context["body"] = _build_body(variables)
    # NOTE: language lives ONLY inside context — every documented body-param
    # example omits a data-level "language" key; including it triggers a 500.
    return {
        "phone_number_id": PHONE_NUMBER_ID,
        "customer_country_code": COUNTRY_CODE,
        "customer_number": mobile10,
        "reply_to": None,
        "myop_ref_id": myop_ref_id,
        "data": {"type": "template", "context": context},
    }


# ── HTTP ──────────────────────────────────────────────────────────────────────
def _headers() -> dict:
    return {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "X-MYOP-COMPANY-ID": COMPANY_ID,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def check_config() -> None:
    missing = [k for k, v in {
        "MYOP_COMPANY_ID": COMPANY_ID,
        "MYOP_PHONE_NUMBER_ID": PHONE_NUMBER_ID,
        "MYOP_AUTH_TOKEN": AUTH_TOKEN,
    }.items() if not v]
    if missing:
        raise WabaConfigError("Missing env vars: " + ", ".join(missing))


def send_template(mobile10: str, template_name: str, variables: list[str],
                  language: str = "en", myop_ref_id: str | None = None,
                  timeout: int = 20, retries: int = 1) -> dict:
    """Send one approved template. Returns a structured result dict:

        {ok, status_code, message_id, conversation_id, code, message, raw}

    Raises WabaFatalError on wallet-empty / disabled conditions so the caller
    can stop the whole batch. Per-message failures (bad template, bad number)
    return ok=False without raising.
    """
    check_config()
    payload_obj = build_payload(mobile10, template_name, variables, language, myop_ref_id)
    if os.environ.get("WABA_DEBUG"):
        print("  [debug] POST", BASE_URL + SEND_PATH)
        print("  [debug] payload:", json.dumps(payload_obj))
    payload = json.dumps(payload_obj).encode("utf-8")
    url = BASE_URL + SEND_PATH
    last_exc = None

    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=payload, headers=_headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", "replace")
                return _parse_response(resp.status, body)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            result = _parse_response(e.code, body)
            # Fatal conditions: stop the batch.
            if result.get("code") in FATAL_CODES:
                raise WabaFatalError(result["code"], FATAL_CODES[result["code"]])
            return result
        except urllib.error.URLError as e:
            last_exc = e
            if attempt < retries:
                time.sleep(3)
                continue
            return {"ok": False, "status_code": 0, "message_id": "",
                    "conversation_id": "", "code": "NETWORK",
                    "message": f"Network error: {e}", "raw": ""}
    return {"ok": False, "status_code": 0, "message_id": "", "conversation_id": "",
            "code": "NETWORK", "message": f"Network error: {last_exc}", "raw": ""}


def _parse_response(status_code: int, body: str) -> dict:
    try:
        data = json.loads(body) if body else {}
    except json.JSONDecodeError:
        data = {}
    d = data.get("data", {}) if isinstance(data, dict) else {}
    # MyOperator misspells conversation id as "conversaton_id" in some responses.
    conv = d.get("conversation_id") or d.get("conversaton_id") or ""
    code = str(data.get("code", "")) if isinstance(data, dict) else ""
    msg = data.get("message", "") if isinstance(data, dict) else ""
    ok = 200 <= status_code < 300 and (str(code) in ("200", "") and bool(d.get("message_id") or msg))
    # Treat explicit success flag if present
    if isinstance(data, dict) and str(data.get("status", "")).lower() == "success":
        ok = True
    return {
        "ok": bool(ok),
        "status_code": status_code,
        "message_id": d.get("message_id", ""),
        "conversation_id": conv,
        "code": code,
        "message": msg,
        "raw": body[:1000],
    }
