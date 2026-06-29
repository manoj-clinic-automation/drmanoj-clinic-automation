#!/usr/bin/env python3
"""
waba_probe.py — one-shot WhatsApp test sender.

Sends ONE approved template to a single number you choose, using the same
waba.py send path the real batches use. Use it to confirm end-to-end sending
works (capital Bearer + numeric variables) WITHOUT needing any ledger data.

Usage:
    python waba_probe.py 9837114044
    python waba_probe.py 9837114044 --template drmanoj_followup_due --var "Test Patient" --var "14 Jun 2026"

Defaults: template "drmanoj_followup_due", variables ["Test Patient", "14 Jun 2026"].
Reads all config (token, IDs, body format) from .env via waba.py.
"""

import sys
import argparse
import waba


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("number", help="10-digit Indian mobile to send the test to")
    ap.add_argument("--template", default="drmanoj_followup_due",
                    help="approved template name (default: drmanoj_followup_due)")
    ap.add_argument("--var", action="append", default=[],
                    help="a template variable; repeat in order, e.g. --var Name --var Date")
    args = ap.parse_args()

    mobile = waba.normalize_mobile(args.number)
    if not mobile:
        print(f"Not a valid 10-digit Indian mobile: {args.number}")
        sys.exit(1)

    variables = args.var if args.var else ["Test Patient", "14 Jun 2026"]

    try:
        waba.check_config()
    except waba.WabaConfigError as e:
        print(f"Config problem: {e}")
        print("Open your .env and make sure MYOP_AUTH_TOKEN is set (and the other IDs).")
        sys.exit(1)

    print(f"Sending '{args.template}' to {mobile} with variables {variables} ...\n")
    res = waba.send_template(mobile, args.template, variables)

    if res.get("ok"):
        print("SUCCESS — WhatsApp accepted.")
        print(f"  message_id      : {res.get('message_id', '')}")
        print(f"  conversation_id : {res.get('conversation_id', '')}")
        print("\nA real WhatsApp should arrive on that number shortly.")
    else:
        print("NOT SENT.")
        print(f"  HTTP status : {res.get('status_code')}")
        print(f"  code        : {res.get('code')}")
        print(f"  message     : {res.get('message')}")
        print(f"  raw         : {res.get('raw', '')[:300]}")
        print("\nPaste this output back and I'll tell you the one thing to fix.")


if __name__ == "__main__":
    main()
