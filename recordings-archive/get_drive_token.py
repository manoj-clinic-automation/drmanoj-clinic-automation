#!/usr/bin/env python3
"""
get_drive_token.py — ONE-TIME setup. Run this on YOUR OWN PC, not the VPS.

WHAT THIS DOES
  Asks you to sign in as drmka.ortho@gmail.com in your browser and click
  Allow, then saves a small credential file ("drive_token.json") that lets
  the clinic's automated VPS script upload recordings to YOUR Drive (using
  your own 5TB storage) without ever asking you to log in again. You run
  this exactly once. The resulting file refreshes itself forever after.

  This version does NOT rely on your PC auto-catching the browser's
  response (some antivirus/firewall setups block that local step). Instead
  YOU copy the final browser address bar back into this terminal — a
  manual step, but one that works regardless of any firewall.

BEFORE RUNNING
  1. Put the file you downloaded from Google Cloud Console - the long
     name starting "client_secret_259882152447..." - in the SAME FOLDER
     as this script, renamed to exactly:  client_secret.json
  2. Install the one extra library this needs (one time, on your PC only):
         pip install google-auth-oauthlib

RUN
  python get_drive_token.py

WHAT WILL HAPPEN
  1. This terminal prints a long link.
  2. Copy that ENTIRE link, paste it into your browser's address bar,
     press Enter.
  3. Sign in as drmka.ortho@gmail.com.
  4. It will warn "Google hasn't verified this app" - EXPECTED, this app
     is private to just you. Click Advanced -> Go to Clinic Drive
     Archiver (unsafe) -> Allow.
  5. The browser will land on a page that LIKELY SHOWS AN ERROR
     ("localhost refused to connect" or similar) - this is FINE and
     EXPECTED. The important part isn't the page loading; it's the
     address bar, which will contain a long URL with "code=" in it.
  6. Click into that address bar, select the ENTIRE URL (Ctrl+A while
     the address bar is focused, then Ctrl+C), and come back to this
     terminal.
  7. This terminal will be waiting with a prompt: "Paste the full URL
     from your browser's address bar here:" - paste it (right-click ->
     Paste, or Ctrl+V) and press Enter.
  8. Terminal prints "Saved: drive_token.json". Done.

AFTER IT SUCCEEDS
  Upload the new drive_token.json to the VPS (same WinSCP process you've
  used for every other file this session) into:
      /root/wa/recordings-archive/
  Tell Claude once it's uploaded.

THIS FILE IS SENSITIVE
  drive_token.json effectively grants Drive access to your account.
  Treat it like a password: don't share it, don't paste its contents
  into chat. It only ever needs to exist in two places - briefly here,
  and permanently on the VPS in the same protected folder as the other
  secrets (.env, the service-account key).
"""

import os
import sys
from pathlib import Path

# Allow the http://localhost redirect step. This is the standard, official
# workaround for oauthlib's generic "must be https" guard, which doesn't
# special-case loopback addresses. The actual sensitive step — exchanging
# the code for a token — always goes to Google over https regardless of
# this setting; only the local redirect itself is http, which is normal
# and safe for "localhost" specifically (RFC 8252).
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

try:
    from google_auth_oauthlib.flow import Flow
except ImportError:
    print("Missing library. Run this first, then re-run this script:")
    print("    pip install google-auth-oauthlib")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/drive"]
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_OUT_FILE = "drive_token.json"
REDIRECT_URI = "http://localhost"


def main():
    here = Path(__file__).resolve().parent
    client_secret_path = here / CLIENT_SECRET_FILE

    if not client_secret_path.exists():
        print("Could not find '%s' in this folder: %s" % (CLIENT_SECRET_FILE, here))
        print("Put the downloaded Google Cloud client-secret JSON here and "
              "rename it to exactly '%s', then re-run this script." % CLIENT_SECRET_FILE)
        sys.exit(1)

    flow = Flow.from_client_secrets_file(
        str(client_secret_path), scopes=SCOPES, redirect_uri=REDIRECT_URI
    )
    auth_url, _state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )

    print()
    print("STEP 1 — open this link in your browser:")
    print()
    print(auth_url)
    print()
    print("STEP 2 — sign in as drmka.ortho@gmail.com, click through the")
    print("'unverified app' warning (Advanced -> Go to Clinic Drive Archiver")
    print("(unsafe) -> Allow). The page that loads next may show an error —")
    print("that's fine. What matters is the browser's ADDRESS BAR.")
    print()
    print("STEP 3 — copy the ENTIRE address bar contents (click it, Ctrl+A,")
    print("Ctrl+V) and paste it below, then press Enter.")
    print()

    pasted = input("Paste the full URL from your browser's address bar here: ").strip()

    if "code=" not in pasted:
        print("That doesn't look like it contains an authorization code "
              "('code=' was not found). Make sure you copied the FULL "
              "address bar text after clicking Allow, then try again.")
        sys.exit(1)

    try:
        flow.fetch_token(authorization_response=pasted)
    except Exception as e:  # noqa: BLE001
        print("Could not complete the exchange:", repr(e))
        print("This usually means the link was used already, expired, or "
              "got cut off when pasting. Run this script again for a fresh link.")
        sys.exit(1)

    creds = flow.credentials
    out_path = here / TOKEN_OUT_FILE
    out_path.write_text(creds.to_json(), encoding="utf-8")

    print()
    print("Saved: %s" % out_path)
    print("Done. Upload this file to the VPS now (/root/wa/recordings-archive/), "
          "then let Claude know.")


if __name__ == "__main__":
    main()
