#!/usr/bin/env python3
"""
get_users.py - one-shot, READ-ONLY agent lookup for OBD click-to-call.
Dr. Manoj Agarwal Clinic.

WHAT IT DOES
  Calls MyOperator "Get Users" and prints a clean table of:
        name | user_id | uuid
  It PRINTS NO PHONE NUMBERS and NO TOKEN, so the output is safe to share.
  Purpose: get the agent uuid (and user_id) needed for an OBD User-Dialer call,
  and confirm which id field OBD wants.

TOKEN
  Reads the Calling/Logs token (the 32-char 3f76... one) from the environment
  variable MYOP_LOGS_TOKEN. It is never printed and never written to disk.

RUN (on the VPS)
  export MYOP_LOGS_TOKEN="<paste the 3f76... token here>"
  /root/wa/venv/bin/python /root/wa/get_users.py
  unset MYOP_LOGS_TOKEN          # clear it from this shell when done
"""

import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error

HOST = "https://developers.myoperator.co"
PATH = "/search/user"


def _load_env(path):
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except OSError:
        pass


_load_env(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


def main():
    token = os.environ.get("MYOP_LOGS_TOKEN", "").strip()
    if not token:
        print('ERROR: set the token first ->  '
              'export MYOP_LOGS_TOKEN="<the 3f76... Calling/Logs token>"',
              file=sys.stderr)
        sys.exit(2)

    # The token travels in the URL only to MyOperator over HTTPS; never printed.
    url = "%s%s?token=%s&_all=1" % (HOST, PATH, urllib.parse.quote(token, safe=""))
    req = urllib.request.Request(url, headers={"Accept": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", "replace")
            http = resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        print("HTTP %s from Get Users." % e.code, file=sys.stderr)
        try:
            j = json.loads(body)
            print("message:", j.get("message") or j.get("status") or body[:200],
                  file=sys.stderr)
        except Exception:
            print(body[:200], file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print("Network/other error:", repr(e), file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(raw)
    except Exception:
        print("Could not parse JSON. First 200 chars (no token in it):",
              file=sys.stderr)
        print(raw[:200], file=sys.stderr)
        sys.exit(1)

    # The user list is usually under "data"; be tolerant of the exact shape.
    rows = data.get("data") if isinstance(data, dict) else data
    if isinstance(rows, dict):
        rows = rows.get("users") or rows.get("data") or list(rows.values())
    if not isinstance(rows, list):
        print("Unexpected response shape. Top-level keys:",
              list(data.keys()) if isinstance(data, dict) else type(data),
              file=sys.stderr)
        sys.exit(1)

    print("HTTP %s  -  %d user(s) found" % (http, len(rows)))
    print("-" * 72)
    print("%-26s | %-14s | %s" % ("name", "user_id", "uuid"))
    print("-" * 72)
    for u in rows:
        if not isinstance(u, dict):
            continue
        name = str(u.get("name") or u.get("user_name") or "").strip()[:26]
        uid = str(u.get("user_id") or u.get("id") or "")
        uuid = str(u.get("uuid") or "")
        print("%-26s | %-14s | %s" % (name, uid, uuid))
    print("-" * 72)
    print("(phone numbers intentionally omitted - safe to paste back)")


if __name__ == "__main__":
    main()
