#!/usr/bin/env python3
# =============================================================================
# waba_template_test.py — Session 132
# Send ONE approved WhatsApp template to a chosen number, as a live proof
# that POST /chat/messages works. No 24h window needed.
#
# SAFETY
#   - DRY RUN BY DEFAULT. It sends nothing unless you pass --send.
#   - The bearer token is read from /root/wa/.env, used, and never printed.
#   - The destination number is masked in all output.
#   - Before anything is printed, the output is scanned for the token.
#     If any fragment is present, the output is destroyed and we abort.
#
# Payload shape is copied verbatim from API_QUICK_REFERENCE_CARD.md
# ("Working send body (confirmed 200)"), not from memory.
#
# Usage:
#   /root/wa/venv/bin/python3 /root/wa/waba_template_test.py            # dry run
#   /root/wa/venv/bin/python3 /root/wa/waba_template_test.py --send     # LIVE
# =============================================================================

import datetime
import http.client
import json
import os
import re
import sys

ENVFILE = "/root/wa/.env"
API_HOST = "publicapi.myoperator.co"
API_PATH = "/chat/messages"

DEST_NUMBER = "9837114044"          # the owner's own phone
TEMPLATE = "drmanoj_followup_due"   # {{1}} name, {{2}} date
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def read_env(path):
    vals = {}
    if not os.path.exists(path):
        return vals
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            vals[k.strip()] = v
    return vals


def mask_number(n):
    n = re.sub(r"\D", "", n)[-10:]
    return "91-%sxxxxx%s" % (n[:2], n[-3:])


def die(msg, code=2):
    print("ABORT: " + msg)
    sys.exit(code)


def main():
    live = "--send" in sys.argv

    print("=" * 67)
    print(" WABA TEMPLATE SEND TEST")
    print(" Host     : https://%s%s" % (API_HOST, API_PATH))
    print(" Template : %s" % TEMPLATE)
    print(" To       : %s   (masked)" % mask_number(DEST_NUMBER))
    print(" Mode     : %s" % ("LIVE SEND" if live else "DRY RUN — nothing is sent"))
    print(" When     : %s" % datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S %Z"))
    print("=" * 67)
    print()

    env = read_env(ENVFILE)
    if not env:
        die("cannot read %s" % ENVFILE)

    token = env.get("MYOP_AUTH_TOKEN", "")
    company_id = env.get("MYOP_COMPANY_ID", "")
    phone_number_id = env.get("MYOP_PHONE_NUMBER_ID", "")

    # An empty value and an absent value behave identically (D170) — check both.
    if not token:
        die("MYOP_AUTH_TOKEN is absent or empty in %s" % ENVFILE, 3)
    if not company_id:
        die("MYOP_COMPANY_ID is absent or empty in %s" % ENVFILE, 3)
    if not phone_number_id:
        die("MYOP_PHONE_NUMBER_ID is absent or empty in %s" % ENVFILE, 3)

    print("Token    : %d characters, from $MYOP_AUTH_TOKEN (never displayed)" % len(token))
    print("Company  : %s" % company_id)
    print("Phone id : %s" % phone_number_id)
    print()

    today = datetime.datetime.now(IST).strftime("%d-%b-%Y")
    payload = {
        "phone_number_id": phone_number_id,
        "customer_country_code": "91",
        "customer_number": DEST_NUMBER,
        "data": {
            "type": "template",
            "context": {
                "template_name": TEMPLATE,
                "language": "en",
                "body": {"1": "SYSTEM TEST", "2": today},
            },
        },
        "reply_to": None,
        "myop_ref_id": None,
    }

    shown = json.loads(json.dumps(payload))
    shown["customer_number"] = mask_number(DEST_NUMBER)
    print("PAYLOAD (number masked; no token in the body):")
    print(json.dumps(shown, indent=2))
    print()

    if not live:
        print("=" * 67)
        print(" DRY RUN. Nothing was sent.")
        print(" Re-run with  --send  to deliver this template.")
        print("=" * 67)
        return

    headers = {
        "Authorization": "Bearer " + token,   # capital B required
        "X-MYOP-COMPANY-ID": company_id,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    conn = http.client.HTTPSConnection(API_HOST, timeout=30)
    try:
        conn.request("POST", API_PATH, json.dumps(payload), headers)
        res = conn.getresponse()
        status = res.status
        raw = res.read().decode("utf-8", errors="replace")
        resp_headers = dict(res.getheaders())
    except Exception as exc:
        print("=" * 67)
        print(" RESULT: the request did not complete.")
        print(" %s: %s" % (type(exc).__name__, exc))
        print("=" * 67)
        sys.exit(1)
    finally:
        try:
            conn.close()
        except Exception:
            pass

    # GUARD — the token must appear nowhere in anything we are about to print.
    blob = raw + json.dumps(resp_headers)
    if token in blob:
        die("the token appeared in the server's response. "
            "Nothing printed. Do NOT screenshot anything.", 5)

    print("-" * 67)
    print(" HTTP STATUS : %s" % status)
    print("-" * 67)
    print()

    req_id = resp_headers.get("x-amzn-RequestId") or resp_headers.get("x-amzn-requestid") or ""
    err_type = resp_headers.get("x-amzn-ErrorType") or resp_headers.get("x-amzn-errortype") or ""

    try:
        body = json.loads(raw)
    except Exception:
        body = None

    print("RESPONSE BODY:")
    print(raw[:600] if raw else "  (empty)")
    print()

    print("=" * 67)
    if status == 200 and isinstance(body, dict) and str(body.get("status", "")).lower() == "success":
        data = body.get("data") or {}
        print(" RESULT: 200 ACCEPTED — MyOperator took the message.")
        print("         message_id      : %s" % data.get("message_id"))
        print("         conversation_id : %s" % data.get("conversation_id"))
        print()
        print(" POST /chat/messages WORKS. Check your phone for the template.")
        print(" NOTE: 'Accepted' means MyOperator queued it. Delivery to the")
        print("       handset is confirmed by the phone, not by this number.")
    elif status == 500:
        print(" RESULT: 500 — STILL BROKEN.")
        if err_type:
            print("         x-amzn-ErrorType : %s" % err_type)
        if req_id:
            print("         FRESH AWS request id (send this to MyOperator):")
            print("         %s" % req_id)
    elif status in (401, 403):
        print(" RESULT: %s — the authorizer REACHED us and rejected the token." % status)
        print("         That is a credential fault on our side, not theirs.")
    else:
        print(" RESULT: HTTP %s — unexpected. Show this output to Claude." % status)
        if req_id:
            print("         AWS request id: %s" % req_id)
    print("=" * 67)
    print()
    print("This whole screen is safe to photograph.")


if __name__ == "__main__":
    main()
