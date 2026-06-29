#!/usr/bin/env python3
"""
call_tester.py  —  MyOperator WhatsApp API auth / provisioning checker
Dr. Manoj Agarwal Clinic · for use DURING the engineer call.

WHEN TO USE THIS:
  Only if the engineer hands you a NEW token or tells you to try a different
  header. It lets you test it instantly WITHOUT editing .env live.
  For the plain baseline test, your existing  waba_check.py  is fine.

WHAT IT DOES:
  One no-body GET to /chat/templates, tried BOTH ways (Authorization: Bearer
  and x-api-key), printing the HTTP status + a short bit of the body.
  That status is the whole diagnosis:
     Bearer -> 200  = AUTH GREEN (provisioning fixed). Next: run waba_probe.py.
     Bearer -> 500  = server still can't resolve the account = API still NOT enabled.
     Bearer -> 401  = clean rejection = the token is wrong (ask for the right one).

  The token is typed HIDDEN — never shown, never saved to a file, never sent
  anywhere. Safe to run while screen-sharing.

HOW TO RUN (in the same folder as your other waba files):
     python call_tester.py
"""
import ssl
import sys
import getpass
import urllib.request
import urllib.error

# These are account IDs, NOT secrets. Edit only if the engineer tells you to.
COMPANY_ID = "68384350414b9847"
WABA_ID    = "2101222617483538"
BASE_URL   = "https://publicapi.myoperator.co"

URL = (f"{BASE_URL}/chat/templates"
       f"?waba_id={WABA_ID}&waba_template_status=approved&limit=5&offset=0")


def call(style, token):
    """style is 'bearer' or 'x-api-key'."""
    req = urllib.request.Request(URL, method="GET")
    if style == "x-api-key":
        req.add_header("x-api-key", token)
    else:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-MYOP-COMPANY-ID", COMPANY_ID)
    req.add_header("Accept", "application/json")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            return r.getcode(), r.read(400).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(400).decode("utf-8", "replace")
    except Exception as e:                       # noqa: BLE001
        return 0, f"(no response: {e})"


def verdict(bearer_status):
    if bearer_status == 200:
        return ("AUTH GREEN  ->  provisioning is fixed.\n"
                "   Next: run   python waba_probe.py 9837114044 --auto")
    if bearer_status == 500:
        return ("Still HTTP 500  ->  the server cannot resolve the account =\n"
                "   the public API is still NOT enabled. Tell the engineer this.")
    if bearer_status == 401:
        return ("Now HTTP 401 (a clean rejection)  ->  the API is reachable but\n"
                "   this token is wrong. Ask the engineer for the correct credential.")
    return "Unexpected status — copy the two lines above and paste them to Claude."


def main():
    print("\nMyOperator auth tester")
    print("Paste the token the engineer gave you. Typing is hidden —")
    print("it is never shown, saved, or sent anywhere.\n")
    token = getpass.getpass("Token: ").strip()
    if not token:
        print("No token entered. Run it again.")
        sys.exit(1)

    print("\nTesting the same request two ways...\n")
    b_status, b_body = call("bearer", token)
    print(f"  [Bearer   ]  HTTP {b_status}   {b_body[:160]}")
    x_status, x_body = call("x-api-key", token)
    print(f"  [x-api-key]  HTTP {x_status}   {x_body[:160]}")

    print("\n=> " + verdict(b_status) + "\n")


if __name__ == "__main__":
    main()
