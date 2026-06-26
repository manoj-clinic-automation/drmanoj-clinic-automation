#!/usr/bin/env python3
# =============================================================================
# waba_text_probe.py  —  Dr Manoj Agarwal Clinic
# ONE-OFF TESTER for the WhatsApp FREE-TEXT (session) send format.
# Not part of any live app. Safe to run, safe to delete afterwards.
#
# WHAT IT DOES
#   Sends a single free-text (type:"text") WhatsApp message to ONE number you
#   name on the command line, and prints the full reply so we can confirm the
#   format works on this account.
#
# THE 24-HOUR RULE (read before running)
#   A free-text message only DELIVERS if that number messaged the clinic within
#   the last 24 hours. So the test is:
#     1) From the phone you will target, send any WhatsApp to the clinic number
#        9358008080  (this opens the 24h window).
#     2) Within a few minutes, run this script targeting that same number.
#   Outside an open window WhatsApp blocks free text (only templates are allowed)
#   — that is expected and not a code fault.
#
# SECRETS
#   The WhatsApp token is read from the environment or a small key=value file.
#   It is NEVER printed and NEVER hard-coded here. Do not paste the token into
#   chat. Company id / phone-number id are public identifiers (safe defaults).
#
# USAGE
#   Provide the token one of these ways (first found wins):
#     - env var:        set WA_TOKEN=...   (Windows)   /   export WA_TOKEN=...  (Linux)
#     - a file:         --env waba_text_probe.env      (KEY=VALUE lines)
#     - auto:           a file named waba_text_probe.env in the current folder
#   Then:
#     python waba_text_probe.py <10-digit-number> "your message text"
#   Optional:
#     --reply-to <message_id>   quote/thread onto a specific inbound message
#     --country 91              override country code (default 91)
#
# EXAMPLE (target your own number — replace the X's)
#   python waba_text_probe.py 9XXXXXXXXX "Namaskar, yeh ek test reply hai."
# =============================================================================

import argparse
import http.client
import json
import os
import re
import sys

# ---- Public, non-secret identifiers for THIS account (safe to keep here) -----
DEFAULT_COMPANY_ID      = "68384350414b9847"
DEFAULT_PHONE_NUMBER_ID = "1090067637530949"
DEFAULT_COUNTRY_CODE    = "91"
API_HOST                = "publicapi.myoperator.co"
API_PATH                = "/chat/messages"


def load_env_file(path):
    """Tiny KEY=VALUE reader. Ignores blank lines and # comments. No deps."""
    vals = {}
    if not path or not os.path.exists(path):
        return vals
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


def get_config(env_path):
    """Resolve config from: real env vars, then the env file, then defaults."""
    fromfile = load_env_file(env_path)

    def pick(key, default=None):
        return os.environ.get(key) or fromfile.get(key) or default

    token = pick("WA_TOKEN")
    cfg = {
        "token":           token,
        "company_id":      pick("WA_COMPANY_ID", DEFAULT_COMPANY_ID),
        "phone_number_id": pick("WA_PHONE_NUMBER_ID", DEFAULT_PHONE_NUMBER_ID),
    }
    return cfg


def normalize_number(raw):
    """Keep digits only; if it carries 91 + 10 digits, drop the country code."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    return digits


def mask(tok):
    if not tok:
        return "(missing)"
    return (tok[:4] + "…") if len(tok) > 4 else "…"


def main():
    ap = argparse.ArgumentParser(description="WhatsApp free-text (session) send tester")
    ap.add_argument("number", help="10-digit destination (your own number for the test)")
    ap.add_argument("message", help="message text (quote it)")
    ap.add_argument("--env", default="waba_text_probe.env",
                    help="path to a KEY=VALUE file holding WA_TOKEN (default: ./waba_text_probe.env)")
    ap.add_argument("--country", default=DEFAULT_COUNTRY_CODE, help="country code (default 91)")
    ap.add_argument("--reply-to", default=None, help="optional message_id to quote/thread")
    args = ap.parse_args()

    cfg = get_config(args.env)
    if not cfg["token"]:
        print("✗ No WA_TOKEN found.")
        print("  Set it as an environment variable, or put a line  WA_TOKEN=...  in")
        print(f"  a file named {args.env} in this folder, then run again.")
        sys.exit(2)

    number = normalize_number(args.number)
    if len(number) != 10:
        print(f"✗ '{args.number}' is not a 10-digit number after cleaning (got '{number}').")
        sys.exit(2)

    body = {
        "phone_number_id": cfg["phone_number_id"],
        "customer_country_code": args.country,
        "customer_number": number,
        "data": {
            "type": "text",
            "context": {
                "body": args.message,
                "preview_url": False,
            },
        },
        "reply_to": args.reply_to,   # None -> JSON null
        "myop_ref_id": None,
    }

    headers = {
        "Authorization": "Bearer " + cfg["token"],   # capital B — required
        "X-MYOP-COMPANY-ID": cfg["company_id"],
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    print("— Sending free-text test —")
    print(f"  to            : 91-{number[:2]}xxxxx{number[-3:]}   (masked)")
    print(f"  company id    : {cfg['company_id']}")
    print(f"  phone_no_id   : {cfg['phone_number_id']}")
    print(f"  token         : {mask(cfg['token'])}  (masked, never shown in full)")
    print(f"  message       : {args.message!r}")
    if args.reply_to:
        print(f"  reply_to      : {args.reply_to}")
    print()

    try:
        conn = http.client.HTTPSConnection(API_HOST, timeout=30)
        conn.request("POST", API_PATH, json.dumps(body), headers)
        res = conn.getresponse()
        status = res.status
        text = res.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"✗ Network/connection error: {e}")
        sys.exit(1)
    finally:
        try:
            conn.close()
        except Exception:
            pass

    print(f"HTTP {status}")
    # pretty-print JSON if possible
    try:
        parsed = json.loads(text)
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
    except Exception:
        parsed = None
        print(text)

    print()
    low = text.lower()
    if status == 200 and parsed and str(parsed.get("status", "")).lower() == "success":
        mid = (parsed.get("data") or {}).get("message_id", "?")
        print("✅ FREE-TEXT FORMAT CONFIRMED — a real WhatsApp was accepted.")
        print(f"   message_id = {mid}")
        print("   If it does NOT arrive on the phone, the 24h window was likely closed:")
        print("   message the clinic number 9358008080 first, then re-run within minutes.")
    elif any(w in low for w in ["session", "re-engage", "reengage", "24", "window",
                                "template", "outside", "not open", "expired"]):
        print("⚠ Looks like the 24-HOUR WINDOW was closed (not a format problem).")
        print("  Send a WhatsApp from the target phone to 9358008080, then re-run within minutes.")
    elif "explicit deny" in low or status == 403:
        print("⚠ Auth rejected. Check the token is the WhatsApp 'Authentication' token")
        print("  (lHCx…) and that 'Bearer' is capitalised (it is, in this script).")
    else:
        print("⚠ Unexpected reply. Copy the JSON above (it has NO token in it) so we can read it.")


if __name__ == "__main__":
    main()
